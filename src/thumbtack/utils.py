import os
import json
import pickle
import re
import sqlite3
import subprocess
import sys

from pathlib import Path

from flask import current_app, g

import imagemounter_mitre

from .exceptions import (
    NoMountableVolumesError,
    UnexpectedDiskError,
    ImageNotInDatabaseError,
    DuplicateMountAttemptError,
    EncryptedImageError,
    DuplicateVolumeGroupError,
)

def get_supported_libraries():
    virtualenv_bin_directory = Path(sys.argv[0]).parent
    imount_cmd = str(virtualenv_bin_directory / "imount")

    run_args = [imount_cmd, "--check"]

    current_app.logger.info(run_args)
    output = subprocess.check_output(run_args).decode().split("\n")
    outputjson = {}

    for line in output:
        line_split = line.split()
        if len(line_split) > 0 and (
            "MISSING" in line_split or "INSTALLED" in line_split
        ):
            if line_split[0] == "INSTALLED":
                outputjson[str(line_split[1])] = True
            else:
                outputjson[str(line_split[1])] = False

    return outputjson


def get_mount_info(image_path):

    if not image_path:
        response = []

        images = get_images(mounted=True)
        for image_info in images:
            rel_path = image_info["rel_path"]

            ref_count = get_ref_count(rel_path)
            parser = image_info["parser"]

            response.append({"disk_info": parser.disks[0], "ref_count": ref_count})
        return response

    image_info = get_image_info(image_path)

    if not image_info:
        return None
    parser = image_info["parser"]

    disk_info = None
    if not parser:
        return None
    else:
        disk_info = parser.disks[0]

    ref_count = get_ref_count(image_path)

    response = {"disk_info": disk_info, "ref_count": ref_count}

    return response


def get_ref_count(rel_path):
    ref_count = 0
    result = query_db(
        "SELECT ref_count FROM disk_images WHERE rel_path = ?", [rel_path], one=True
    )
    if result:
        ref_count = result["ref_count"]
    return ref_count


def decrement_ref_count(rel_path):
    sql = "UPDATE disk_images SET ref_count = ref_count - 1 WHERE rel_path = ?"
    update_or_insert_db(sql, [rel_path])
    new_ref_count = get_ref_count(rel_path)
    current_app.logger.info(
        f"* Decreased ref count for {rel_path}. Now: {new_ref_count}"
    )


def increment_ref_count(rel_path):
    sql = "UPDATE disk_images SET ref_count = ref_count + 1 WHERE rel_path = ?"
    update_or_insert_db(sql, [rel_path])
    new_ref_count = get_ref_count(rel_path)
    current_app.logger.info(
        f"* Increased ref count for {rel_path}. Now: {new_ref_count}"
    )



def process_image_parser(image_parser, relative_image_path):
    # Volumes won't be mounted unless this generator is iterated
    try:
        for _ in image_parser.init():
            pass
    except Exception:
        current_app.logger.info(f"* Error mounting volume in {relative_image_path}")
        pass

    # thumbtack can only handle images that have one disk
    num_disks = len(image_parser.disks)
    if num_disks != 1:
        current_app.logger.error(
            f"Error: Unexpected number of disks (expected 1, got {num_disks:d})"
        )
        image_parser.clean(allow_lazy=True)
        raise UnexpectedDiskError(
            f"Unexpected number of disks (expected 1, got {num_disks:d})"
        )

    """
    Mountpoints for LVM volumes are not stored in the main mountpoint variable that we check and display in thumbtack.
    This loop identifies the LVM volumes and add them to the main volumes list.
    """
    duplicate_vg = False
    vgname = ""

    num_volumes = len(image_parser.disks[0].volumes.volumes)
    for v in image_parser.disks[0].volumes:
        if v.duplicate_volume_group:
            duplicate_vg = True
            vgname = v.vgname
        if hasattr(v, 'volumes') and v.mountpoint:
            for vol in v.volumes:
                vol.index = str(num_volumes)
                num_volumes += 1
                image_parser.disks[0].volumes.volumes.append(vol)
        elif hasattr(v, 'volumes') and v.mountpoint is None:
            current_app.logger.info(f"Volume: {str(v)}")
            for vol in v.volumes:
                if vol.duplicate_volume_group:
                    duplicate_vg = True
                    vgname = vol.vgname
                current_app.logger.info(f"Mountpoint: {str(vol.mountpoint)}")
                if vol.mountpoint is not None:
                    vol.index = str(num_volumes)
                    num_volumes += 1
                    image_parser.disks[0].volumes.volumes.append(vol)
                if hasattr(vol, 'volumes'):
                    for sub_vol in vol.volumes:
                        if sub_vol.duplicate_volume_group:
                            duplicate_vg = True
                            vgname = sub_vol.vgname
                        current_app.logger.info(f"Mountpoint: {str(sub_vol.mountpoint)}")
                        if sub_vol.mountpoint is not None:
                            sub_vol.index = str(num_volumes)
                            num_volumes += 1
                            image_parser.disks[0].volumes.volumes.append(sub_vol)

    if duplicate_vg or [v for v in image_parser.disks[0].volumes if v.duplicate_volume_group]:
        msg = "* Duplicate Volume groups detected."
        if vgname:
            msg += f" VG: {vgname}"
        current_app.logger.error(msg)
        raise DuplicateVolumeGroupError(vgname)

    # Fail if we couldn't mount any of the volumes
    if not [v for v in image_parser.disks[0].volumes if v.mountpoint]:
        image_parser.clean(allow_lazy=True)
        msg = f"* No mountable volumes in image {relative_image_path}"
        current_app.logger.error(msg)
        raise NoMountableVolumesError(msg)
    return image_parser

def mount_image(relative_image_path, creds=None):
    mount_dir = current_app.config["MOUNT_DIR"]
    if not mount_dir:
        msg = "Mount directory is not properly set by thumbtack server"
        current_app.logger.error(msg)
        raise NotADirectoryError(msg)

    full_image_path = f"{current_app.config['IMAGE_DIR']}/{relative_image_path}"

    image_info = get_image_info(relative_image_path)

    if not image_info:
        raise ImageNotInDatabaseError

    # Verify we have a valid file path
    if not os.access(full_image_path, os.R_OK):
        msg = f"* {relative_image_path} is not a valid file or is not accessible for reading"
        current_app.logger.error(msg)
        raise PermissionError(msg)

    # Check if the image is currently mounted
    if image_info["status"] == "Mounted" or image_info["status"] == "Manual mount":
        increment_ref_count(relative_image_path)
        current_app.logger.info(f"* {relative_image_path} is already mounted")
        return image_info["parser"].disks[0]
    elif get_ref_count(relative_image_path) == 1:
        msg = f"* Mount attempt in progress for {relative_image_path}"
        current_app.logger.info(f"{msg}")
        raise DuplicateMountAttemptError(msg)

    # Mount it
    current_app.logger.info(f'* Mounting image_path "{relative_image_path}"')

    # Set reference count to 1 to indicate we currently attempting to mount the image.
    sql = """UPDATE disk_images
                 SET ref_count = 1
                 WHERE rel_path = ?
          """
    update_or_insert_db(sql, [relative_image_path])

    no_mountable_volumes = False
    duplicate_vg = None
    try:
        image_parser = imagemounter_mitre.ImageParser(
            [full_image_path], pretty=True, mountdir=mount_dir, keys=creds
        )
        image_parser = process_image_parser(image_parser, relative_image_path)
    except DuplicateVolumeGroupError as e:
        duplicate_vg = e

    except NoMountableVolumesError as e:
        current_app.logger.error(f"fstypes: {image_parser.fstypes}.")
        no_mountable_volumes = True
        current_app.logger.error(f"* No mountable volumes in image {relative_image_path}. Attempting to mount with qemu-nbd")
    if no_mountable_volumes:
        try:
            image_parser = imagemounter_mitre.ImageParser(
                [full_image_path], pretty=True, mountdir=mount_dir, disk_mounter='qemu-nbd', keys=creds
            )
            image_parser = process_image_parser(image_parser, relative_image_path)
        except NoMountableVolumesError as e:
            current_app.logger.error(f"fstypes: {image_parser.fstypes}.")
            no_mountable_volumes = True
            msg = f"* No mountable volumes in image {relative_image_path}"

            # Set ref count to 0 to indicate the mount attempt failed and is no longer in progress
            sql = """UPDATE disk_images
                         SET ref_count = 0
                         WHERE rel_path = ?
                  """
            update_or_insert_db(sql, [relative_image_path])

            for v in image_parser.disks[0].volumes:
                if "LUKS encrypted file" in str(v):
                    if not creds:
                        raise EncryptedImageError("Encrypted LUKS volume detected. Try mounting with a decryption key.")
                    else:
                        raise EncryptedImageError("Encrypted LUKS volume detected. Incorrect decryption key provided.")
            raise NoMountableVolumesError(msg)

    mount_codes = get_mount_codes()
    disk_mount_status_id = (
        mount_codes["Mounted"]
        if image_parser.disks[0].mountpoint
        else mount_codes["Unable to mount"]
    )
    img_parser_pickle = pickle.dumps(image_parser)

    # log our success
    current_app.logger.info(f"* Disk Mounted: {image_parser.disks[0].mountpoint}")
    sql = """UPDATE disk_images
                 SET ref_count = 1, mountpoint = ?, mount_status_id = ?, parser = ?
                 WHERE rel_path = ?
          """
    update_or_insert_db(
        sql,
        [
            image_parser.disks[0].mountpoint,
            disk_mount_status_id,
            sqlite3.Binary(img_parser_pickle),
            relative_image_path,
        ],
    )

    disk_image_id = image_info["id"]
    for volume in image_parser.disks[0].volumes:
        v_mountpoint = volume.mountpoint if volume.mountpoint else None
        # these mount codes come from the init_db() function
        mount_status_id = (
            mount_codes["Mounted"] if v_mountpoint else mount_codes["Unable to mount"]
        )
        v_index = volume.index

        current_app.logger.info(f"  * Volume description: {volume.get_description()}")
        current_app.logger.info(f"  * Volume mountpoint: {v_mountpoint}")
        sql = "SELECT * FROM volumes WHERE disk_id = ? AND partition_index = ?"
        row = query_db(sql, [disk_image_id, v_index], one=True)

        if row:
            # UPDATE
            sql = "UPDATE volumes SET mountpoint = ?, mount_status_id = ? WHERE disk_id = ? AND partition_index = ?"
            update_or_insert_db(
                sql, [v_mountpoint, mount_status_id, disk_image_id, v_index]
            )
        else:
            sql = "INSERT INTO volumes (disk_id, mount_status_id, partition_index, mountpoint) VALUES (?, ?, ?, ?)"
            update_or_insert_db(
                sql, [disk_image_id, mount_status_id, v_index, v_mountpoint]
            )

    if e := duplicate_vg:
        current_app.logger.info(str(e))
        raise e

    return image_parser.disks[0]

def add_mountpoint(relative_image_path, mountpoint_path):
    # Get image information and mount codes
    image_info = get_image_info(relative_image_path)
    mount_codes = get_mount_codes()
    disk_mount_status_id = (mount_codes["Manual mount"])

    full_image_path = f"{current_app.config['IMAGE_DIR']}/{relative_image_path}"
    mount_dir = mountpoint_path

    # Update disk_images table
    sql = """UPDATE disk_images
                 SET ref_count = 1, mountpoint = ?, mount_status_id = ?, parser = ?
                 WHERE rel_path = ?
          """

    image_parser = imagemounter_mitre.ImageParser(
        [full_image_path], pretty=True, mountdir=mount_dir
    )



    disk = image_parser.disks[0]

    volume = imagemounter_mitre.volume.Volume(disk)
    filesystem = imagemounter_mitre.filesystems.UnknownFileSystem(volume)
    filesystem.mountpoint = mountpoint_path
    volume.filesystem = filesystem

    disk.volumes = [volume]
    image_parser.disks[0].volumes = volume

    #image_parser.disks.append(disk)

    img_parser_pickle = pickle.dumps(image_parser)

    update_or_insert_db(
        sql,
        [
            mountpoint_path,
            disk_mount_status_id,
            sqlite3.Binary(img_parser_pickle),
            relative_image_path,
        ],
    )

    # Update volumes
    disk_image_id = image_info["id"]
    mount_status_id = (mount_codes["Manual mount"])
    v_index = 0
    sql = "INSERT INTO volumes (disk_id, mount_status_id, partition_index, mountpoint) VALUES (?, ?, ?, ?)"
    update_or_insert_db(sql, [disk_image_id, mount_status_id, v_index, mountpoint_path])
    return mountpoint_path


def unmount_image(relative_image_path, force=False):
    image_info = get_image_info(relative_image_path)
    mount_codes = get_mount_codes()
    ref_count = image_info["ref_count"]

    if ref_count == 1 or force:
        current_app.logger.info(f"* Unmounting {relative_image_path}")
        if image_info["status"] == "Mounted":
            image_parser = image_info["parser"]

            image_parser.clean(allow_lazy=True)
            current_app.logger.info(f"* Unmounted {relative_image_path} successfully")

        sql = """UPDATE disk_images
                     SET ref_count = 0, mountpoint = NULL, mount_status_id = ?, parser = NULL
                     WHERE rel_path = ?
                 """
        update_or_insert_db(sql, [mount_codes["Unmounted"], relative_image_path])

        if image_info["status"] == "Mounted":
            sql = """UPDATE volumes
                     SET mountpoint = NULL, mount_status_id = ?
                     WHERE disk_id = ?
                 """
            update_or_insert_db(sql, [mount_codes["Unmounted"], image_info["id"]])
        elif image_info["status"] == "Manual mount":
            sql = """DELETE FROM volumes
                     WHERE disk_id = ?
                 """
            update_or_insert_db(sql, [image_info["id"]])
        return True
    # ref_count should only ever be 0 or greater, but anything less than 1 means it is not mounted
    elif ref_count < 1:
        current_app.logger.info(f"Image path {relative_image_path} is not mounted")
        return True
    elif ref_count > 1:
        decrement_ref_count(relative_image_path)
        return False


def unmount_all(force=False):
    current_app.logger.info("Unmounting all mounted images")
    images = get_images(mounted=True)

    for image in images:
        msg = f"{image['rel_path']} is being forcefully unmounted with {image['ref_count']:d} outstanding references."
        current_app.logger.warning(msg)
        unmount_image(image["rel_path"], force=force)


def get_mount_codes():
    mount_codes = {}
    rows = query_db("SELECT * FROM mount_status_codes")
    for row in rows:
        mount_codes[row["status"]] = row["id"]
    return mount_codes


def get_mount_status_by_id(mount_status_id):
    status = None
    result = query_db(
        "SELECT status FROM mount_status_codes WHERE id = ?",
        [mount_status_id],
        one=True,
    )
    if result:
        status = result["status"]
    return status


def get_image_info(relative_image_path):

    disk_image = query_db(
        "SELECT * FROM disk_images WHERE rel_path = ?", [relative_image_path], one=True
    )

    if not disk_image:
        return None

    id_ = disk_image["id"]
    rel_path = disk_image["rel_path"]
    full_path = disk_image["full_path"]
    filename = disk_image["filename"]

    status = get_mount_status_by_id(disk_image["mount_status_id"])

    disk_mountpoint = disk_image["mountpoint"]

    volume_info = []
    if status == "Mounted" or status == "Manual mount":
        for volume in query_db(
            "SELECT * FROM volumes WHERE disk_id = ? ORDER BY partition_index",
            [disk_image["id"]],
        ):
            idx = volume["partition_index"]

            # uid is utilized by index.html as an HTML id, so no invalid characters accepted here
            sanitized_rel_file = (
                rel_path.replace("/", "_").replace(":", "-").replace(".", "-")
            )
            uid = f"{sanitized_rel_file}_{volume['partition_index']}"

            volume_info.append(
                {
                    "index": idx,
                    "mountpoint": volume["mountpoint"],
                    "uid": uid,
                    "status": get_mount_status_by_id(volume["mount_status_id"]),
                }
            )

    ref_count = disk_image["ref_count"]

    parser = None
    if disk_image["parser"]:
        parser_bytes = disk_image["parser"]
        parser = pickle.loads(parser_bytes)

    image_info = {
        "id": id_,
        "rel_path": rel_path,
        "full_path": full_path,
        "filename": filename,
        "status": status,
        "disk_mountpoint": disk_mountpoint,
        "volume_info": volume_info,
        "ref_count": ref_count,
        "parser": parser,
    }
    return image_info


def get_images(mounted=False):
    images = []

    if mounted:
        sql = "SELECT * FROM disk_images WHERE ref_count > 0"
    else:
        sql = "SELECT * FROM disk_images"

    for disk_image in query_db(sql):
        # current_app.logger.info(f"(id: {disk_image['id']}) {disk_image['rel_path']}")
        rel_path = disk_image["rel_path"]

        images.append(get_image_info(rel_path))

    return images


def insert_image(full_path):
    mount_codes = get_mount_codes()
    mount_status = mount_codes["Unmounted"]

    rel_path_str = str(full_path.relative_to(current_app.config["IMAGE_DIR"]))
    full_path_str = str(full_path)
    filename = str(full_path.name)
    disk_image = query_db(
        "SELECT * FROM disk_images WHERE full_path = ?", [full_path_str], one=True
    )
    if not disk_image:
        current_app.logger.debug(f"Inserting disk image into DB: {full_path}")
        sql = "INSERT INTO disk_images (full_path, rel_path, filename, mount_status_id) VALUES (?, ?, ?, ?)"
        update_or_insert_db(sql, [full_path_str, rel_path_str, filename, mount_status])
    # else:
    #     current_app.logger.debug(f"({disk_image['id']}) already in DB: {full_path}")


def insert_images():
    skip_subdirs = None
    try:
        skip_subdirs = list(current_app.config["SKIP_SUBDIRECTORY"])
    except (KeyError, TypeError):
        pass

    for root, dirs, files in os.walk(current_app.config["IMAGE_DIR"]):
        if skip_subdirs:
            dirs[:] = [d for d in dirs if d not in skip_subdirs]

        for filename in files:

            full_path = Path(root, filename)

            if check_ignored(full_path):
                remove_image(full_path)
                continue

            if not filename.startswith(".") and full_path.is_file():
                insert_image(full_path)


def remove_image(full_path):
    full_path_str = str(full_path)
    disk_image = query_db(
        "SELECT * FROM disk_images WHERE full_path = ?", [full_path_str], one=True
    )

    if disk_image:
        current_app.logger.debug(f"Removing disk image from DB: {full_path}")
        sql = "DELETE from disk_images WHERE (full_path) = (?)"
        update_or_insert_db(sql, [full_path_str])


def remove_images():
    images_in_db = get_images()
    full_path_filenames = []

    skip_subdirs = None
    try:
        skip_subdirs = list(current_app.config["SKIP_SUBDIRECTORY"])
    except (KeyError, TypeError):
        pass

    for root, dirs, files in os.walk(current_app.config["IMAGE_DIR"]):
        if skip_subdirs:
            dirs[:] = [d for d in dirs if d not in skip_subdirs]

        for filename in files:
            full_path = Path(root, filename)
            full_path_filenames.append(full_path)

    # If image in DB is not on disk, remove it from DB
    [
        remove_image(image["full_path"])
        for image in images_in_db
        if Path(image["full_path"]) not in full_path_filenames
    ]


# More efficent than calling insert_images then remove_images which will scan all files twice _and_ hit disk
def monitor_image_dir():
    full_path_filenames = []

    skip_subdirs = None
    try:
        skip_subdirs = list(current_app.config["SKIP_SUBDIRECTORY"])
    except (KeyError, TypeError):
        pass

    for root, dirs, files in os.walk(current_app.config["IMAGE_DIR"]):
        if skip_subdirs:
            dirs[:] = [d for d in dirs if d not in skip_subdirs]

        for filename in files:

            full_path = Path(root, filename)
            full_path_filenames.append(full_path)

            if check_ignored(full_path):
                remove_image(full_path)
                continue

            if not filename.startswith(".") and full_path.is_file():
                insert_image(full_path)

    images_in_db = get_images()
    # If image in DB is not on disk, remove it from DB
    [
        remove_image(image["full_path"])
        for image in images_in_db
        if Path(image["full_path"]) not in full_path_filenames
    ]

def startup_remove_dirs():
    for item in os.listdir(current_app.config["MOUNT_DIR"]):
        path = Path(current_app.config["MOUNT_DIR"], item)
        current_app.logger.info(path)
        try:
            current_app.logger.info(f"Unmounting: {path}")
            subprocess.run(["umount", path])
        except Exception as e:
            current_app.logger.error(e)

        if os.path.isdir(path):
            current_app.logger.info(path)
            try:
                current_app.logger.info(f"Removing: {path}")
                os.rmdir(path)
            except Exception as e:
                current_app.logger.error(e)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        database_file = current_app.config["DATABASE"]
        db = g._database = sqlite3.connect(database_file)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    with current_app.app_context():
        db = get_db()

        sql = """
        CREATE TABLE mount_status_codes (
            id INTEGER PRIMARY KEY,
            status TEXT NOT NULL
            )"""
        db.cursor().execute(sql)
        db.commit()

        sql = """
        CREATE TABLE disk_images (
            id INTEGER PRIMARY KEY,
            mount_status_id INTEGER NOT NULL,
            full_path TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            mountpoint TEXT,
            ref_count INTEGER DEFAULT 0,
            parser BLOB,
            FOREIGN KEY(mount_status_id) REFERENCES mount_status_codes(id)
            )"""
        db.cursor().execute(sql)
        db.commit()

        sql = """
        CREATE TABLE volumes (
            id INTEGER PRIMARY KEY,
            disk_id INTEGER NOT NULL,
            mount_status_id INTEGER NOT NULL,
            partition_index INTEGER,
            mountpoint TEXT,
            FOREIGN KEY(disk_id) REFERENCES disk_images(id),
            FOREIGN KEY(mount_status_id) REFERENCES mount_status_codes(id)
            )"""
        db.cursor().execute(sql)
        db.commit()

        # insert status codes
        sql = "INSERT INTO mount_status_codes (status) VALUES (?)"
        status_codes = ["Mounted", "Unable to mount", "Unmounted", "Manual mount"]
        for code in status_codes:
            update_or_insert_db(sql, [code])

        insert_images()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    return_value = cur.fetchall()
    cur.close()
    return (return_value[0] if return_value else None) if one else return_value


def update_or_insert_db(sql, args=()):
    get_db().execute(sql, args)
    get_db().commit()


# @current_app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def check_ignored(full_path):
    full_path_str = str(full_path)

    if os.path.isdir(full_path_str):
        return True

    # Ignore .EXX.txt files
    # Ignore .EXX.adcf files
    # Ignore .EXX.log and .EXX.packed_log files
    if re.match(r".*\.[EL]X?\w\w\.(txt|adcf|(packed_)?log)$", full_path_str, flags=re.I):
        return True

    # Ignore files: .txt, .packed_log, .log
    exclude = [".txt", ".log", ".packed_log"]
    for ign in exclude:
        if full_path_str.lower().endswith(ign):
            return True

    # Include .raw files
    if (
        re.match(r".*raw$", full_path_str, flags=re.I)
    ):
        return False

    # Include .img files
    if (
        re.match(r".*img$", full_path_str, flags=re.I)
    ):
        file_basename = os.path.basename(full_path_str).split('.')[0].lower()

        check_files = [f'{file_basename}.{ext}'.lower() for ext in ['e01', 'imf']]
        image_files = [file.lower() for file in os.listdir(os.path.dirname(full_path_str))]

        # Return true if both .e01 and .imf files exist to ignore a multipart ewf file.
        return all(file in image_files for file in check_files)


    # Ignore *.db since the sqlite DB could be in this directory
    if re.match(r".*\.db$", full_path_str, flags=re.I):
        return True

    # Ignore *.E02, *.E03, ..., *.EAA, *.EAB, ..., *.FAA, ..., *.GAA, ..., *.HAA, ... but not *.E01
    if (
        not full_path_str.lower().endswith("log")
        and (re.match(r".*\.[EFGHIJKLMNOPQRSTUWXYZ]X?\w\w$", full_path_str, flags=re.I) or re.match(r".*\.[EFGHIJKLMNOPQRSTUWXYZ]X?\d\d+$", full_path_str, flags=re.I))
        and not re.match(r".*\.[EL]X?01$", full_path_str, flags=re.I)
    ):
        return True

    # Ignore *.002, *.003, ..., but not *.001
    if re.match(r".*\.\d\d\d$", full_path_str) and not re.match(
        r".*\.001$", full_path_str
    ):
        return True

    # Ignore *-sXXX.vmdk, but not *.vmdk
    if re.match(r".*\-s\w\w\w\.vmdk$", full_path_str, flags=re.I):
        return True

    # Ignore  *-1.vhd, *-2.vhd, ...,  *-N.vhd, but not *-0.vhd
    if re.match(r".*\-\d+\.vhd$", full_path_str, flags=re.I) and not re.match(
        r".*\-0\.vhd$", full_path_str, flags=re.I
    ):
        return True

    # Ignore file not matching path_contains if specified
    path_contains = None
    try:
        path_contains = current_app.config["PATH_CONTAINS"]
    except KeyError:
        pass

    # Ignore file paths not containing specified string if applicable
    if path_contains is not None and path_contains not in full_path_str:
        return True

    return False

def create_key(method, key):
    if method is None or key is None:
        return None

    method_short = ""

    if method == "bitlocker password":
        method_short = "p"
    elif method == "bitlocker recovery key":
        method_short = "r"
    elif method == "bitlocker full volume encryption and tweak key":
        method_short = "k"
    elif method == "luks passphrase":
        method_short = "p"
    else:
        return None

    key_full = {"key": f"{method_short}:{key}"}
    return key_full
