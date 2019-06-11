import os
import pickle
import re
import sqlite3
import subprocess
import sys

from pathlib import Path

from flask import current_app, g, abort

import imagemounter

from .exceptions import NoMountableVolumesError, UnexpectedDiskError, ImageNotInDatabaseError


def get_supported_libraries():
    virtualenv_bin_directory = Path(sys.argv[0]).parent
    imount_cmd = str(virtualenv_bin_directory / 'imount')

    run_args = [imount_cmd, '--check']

    current_app.logger.info(run_args)
    output = subprocess.check_output(run_args).decode().split('\n')
    outputjson = {}

    for line in output:
        line_split = line.split()
        if len(line_split) > 0 and ('MISSING' in line_split or 'INSTALLED' in line_split):
            if line_split[0] == 'INSTALLED':
                outputjson[str(line_split[1])] = True
            else:
                outputjson[str(line_split[1])] = False

    return outputjson


def get_mount_info(image_path):

    if not image_path:
        response = []

        images = get_images(mounted=True)
        for image_info in images:
            rel_path = image_info['rel_path']

            ref_count = get_ref_count(rel_path)
            parser = image_info['parser']

            response.append({
                'disk_info': parser.disks[0],
                'ref_count': ref_count
            })
        return response

    image_info = get_image_info(image_path)
    if not image_info:
        return None
    parser = image_info['parser']

    disk_info = None
    if not parser:
        abort(404, message='Image path {} is not mounted'.format(image_path))
    else:
        disk_info = parser.disks[0]

    ref_count = get_ref_count(image_path)

    response = {
        'disk_info': disk_info,
        'ref_count': ref_count
    }

    return response


def get_ref_count(rel_path):
    ref_count = 0
    result = query_db("SELECT ref_count FROM disk_images WHERE rel_path = ?", [rel_path], one=True)
    if result:
        ref_count = result['ref_count']
    return ref_count


def decrement_ref_count(rel_path):
    sql = "UPDATE disk_images SET ref_count = ref_count - 1 WHERE rel_path = ?"
    update_or_insert_db(sql, [rel_path])
    new_ref_count = get_ref_count(rel_path)
    current_app.logger.info('* Decreased ref count for {}. Now: {}'.format(rel_path, new_ref_count))


def increment_ref_count(rel_path):
    sql = "UPDATE disk_images SET ref_count = ref_count + 1 WHERE rel_path = ?"
    update_or_insert_db(sql, [rel_path])
    new_ref_count = get_ref_count(rel_path)
    current_app.logger.info('* Increased ref count for {}. Now: {}'.format(rel_path, new_ref_count))


def mount_image(relative_image_path, mount_dir='/mnt/thumbtack'):
    full_image_path = '{}/{}'.format(current_app.config['IMAGE_DIR'], relative_image_path)

    image_info = get_image_info(relative_image_path)

    if not image_info:
        raise ImageNotInDatabaseError

    if image_info['status'] == 'Mounted':
        increment_ref_count(relative_image_path)
        return image_info

    # Verify we have a valid file path
    if not os.access(full_image_path, os.R_OK):
        msg = '* {} is not a valid file or is not accessible for reading'.format(relative_image_path)
        current_app.logger.error(msg)
        raise PermissionError(msg)

    # Mount it
    current_app.logger.info('* Mounting image_path "{}"'.format(relative_image_path))
    image_parser = imagemounter.ImageParser([full_image_path], pretty=True, mountdir=mount_dir)

    # Volumes won't be mounted unless this generator is iterated
    for _ in image_parser.init():
        pass

    # thumbtack can only handle images that have one disk
    num_disks = len(image_parser.disks)
    if num_disks != 1:
        current_app.logger.error('Error: Unexpected number of disks (expected 1, got {:d})'.format(num_disks))
        image_parser.clean(allow_lazy=True)
        raise UnexpectedDiskError('Unexpected number of disks (expected 1, got {:d})'.format(num_disks))

    # Fail if we couldn't mount any of the volumes
    if not [v for v in image_parser.disks[0].volumes if v.mountpoint]:
        image_parser.clean(allow_lazy=True)
        msg = '* No mountable volumes in image {}'.format(relative_image_path)
        current_app.logger.error(msg)
        raise NoMountableVolumesError(msg)

    mount_codes = get_mount_codes()
    disk_mount_status_id = mount_codes['Mounted'] if image_parser.disks[0].mountpoint else mount_codes['Unable to mount']
    img_parser_pickle = pickle.dumps(image_parser)

    # log our success
    current_app.logger.info("* Disk Mounted: {}".format(image_parser.disks[0].mountpoint))
    sql = """UPDATE disk_images
                 SET ref_count = 1, mountpoint = ?, mount_status_id = ?, parser = ?
                 WHERE rel_path = ?
          """
    update_or_insert_db(sql, [image_parser.disks[0].mountpoint,
                              disk_mount_status_id,
                              sqlite3.Binary(img_parser_pickle),
                              relative_image_path])

    disk_image_id = image_info['id']
    for volume in image_parser.disks[0].volumes:
        v_mountpoint = volume.mountpoint if volume.mountpoint else None
        # these mount codes come from the init_db() function
        mount_status_id = mount_codes['Mounted'] if v_mountpoint else mount_codes['Unable to mount']
        v_index = volume.index

        current_app.logger.info("  * Volume description: {}".format(volume.get_description()))
        current_app.logger.info("  * Volume mountpoint: {}".format(v_mountpoint))
        sql = "SELECT * FROM volumes WHERE disk_id = ? AND partition_index = ?"
        row = query_db(sql, [disk_image_id, v_index], one=True)

        if row:
            # UPDATE
            sql = "UPDATE volumes SET mountpoint = ?, mount_status_id = ? WHERE disk_id = ? AND partition_index = ?"
            update_or_insert_db(sql, [v_mountpoint, mount_status_id, disk_image_id, v_index])
        else:
            sql = "INSERT INTO volumes (disk_id, mount_status_id, partition_index, mountpoint) VALUES (?, ?, ?, ?)"
            update_or_insert_db(sql, [disk_image_id, mount_status_id, v_index, v_mountpoint])

    return image_parser.disks[0]


def unmount_image(relative_image_path, force=False):
    image_info = get_image_info(relative_image_path)
    mount_codes = get_mount_codes()
    ref_count = image_info['ref_count']

    if ref_count == 1 or force:
        current_app.logger.info('* Unmounting {}'.format(relative_image_path))
        image_parser = image_info['parser']

        image_parser.clean(allow_lazy=True)
        current_app.logger.info('* Unmounted {} successfully'.format(relative_image_path))

        sql = """UPDATE disk_images
                     SET ref_count = 0, mountpoint = NULL, mount_status_id = ?, parser = NULL
                     WHERE rel_path = ?
                 """
        update_or_insert_db(sql, [mount_codes['Unmounted'],
                                  relative_image_path])

        sql = """UPDATE volumes
                     SET mountpoint = NULL, mount_status_id = ?
                     WHERE disk_id = ?
                 """
        update_or_insert_db(sql, [mount_codes['Unmounted'],
                                  image_info['id']])
        return True
    # ref_count should only ever be 0 or greater, but anything less than 1 means it is not mounted
    elif ref_count < 1:
        abort(404, message='Image path {} is not mounted'.format(relative_image_path))
    elif ref_count > 1:
        decrement_ref_count(relative_image_path)
        return False


def unmount_all(force=False):
    current_app.logger.info('Unmounting all mounted images')
    images = get_images(mounted=True)

    for image in images:
        msg = '{} is being forcefully unmounted with {:d} outstanding references.'.format(image['rel_path'],
                                                                                          image['ref_count'])
        current_app.logger.warning(msg)
        unmount_image(image['rel_path'], force=force)


def get_mount_codes():
    mount_codes = {}
    rows = query_db("SELECT * FROM mount_status_codes")
    for row in rows:
        mount_codes[row['status']] = row['id']
    return mount_codes


def get_mount_status_by_id(mount_status_id):
    status = None
    result = query_db("SELECT status FROM mount_status_codes WHERE id = ?", [mount_status_id], one=True)
    if result:
        status = result['status']
    return status


def get_image_info(relative_image_path):

    disk_image = query_db("SELECT * FROM disk_images WHERE rel_path = ?", [relative_image_path], one=True)

    if not disk_image:
        return None

    id_ = disk_image['id']
    rel_path = disk_image['rel_path']
    full_path = disk_image['full_path']
    filename = disk_image['filename']

    status = get_mount_status_by_id(disk_image['mount_status_id'])

    disk_mountpoint = disk_image['mountpoint']

    volume_info = []
    if status == 'Mounted':
        for volume in query_db("SELECT * FROM volumes WHERE disk_id = ? ORDER BY partition_index", [disk_image['id']]):
            idx = volume['partition_index']

            # uid is utilized by index.html as an HTML id, so no invalid characters accepted here
            sanitized_rel_file = rel_path.replace('/', '_').replace(':', '-').replace('.', '-')
            uid = '{}_{}'.format(sanitized_rel_file, volume['partition_index'])

            volume_info.append({
                'index': idx,
                'mountpoint': volume['mountpoint'],
                'uid': uid,
                'status': get_mount_status_by_id(volume['mount_status_id'])
            })

    ref_count = disk_image['ref_count']

    parser = None
    if disk_image['parser']:
        parser_bytes = disk_image['parser']
        parser = pickle.loads(parser_bytes)

    image_info = {
        'id': id_,
        'rel_path': rel_path,
        'full_path': full_path,
        'filename': filename,
        'status': status,
        'disk_mountpoint': disk_mountpoint,
        'volume_info': volume_info,
        'ref_count': ref_count,
        'parser': parser
    }
    return image_info


def get_images(mounted=False):
    images = []

    if mounted:
        sql = "SELECT * FROM disk_images WHERE ref_count > 0"
    else:
        sql = "SELECT * FROM disk_images"

    for disk_image in query_db(sql):
        current_app.logger.info('(id: {}) {}'.format(disk_image['id'], disk_image['rel_path']))
        rel_path = disk_image['rel_path']

        images.append(get_image_info(rel_path))

    return images


def insert_image(full_path):
    mount_codes = get_mount_codes()
    mount_status = mount_codes['Unmounted']

    rel_path_str = str(full_path.relative_to(current_app.config['IMAGE_DIR']))
    full_path_str = str(full_path)
    filename = str(full_path.name)
    disk_image = query_db("SELECT * FROM disk_images WHERE full_path = ?", [full_path_str], one=True)
    if not disk_image:
        current_app.logger.debug('Inserting disk image into DB: {}'.format(full_path))
        sql = "INSERT INTO disk_images (full_path, rel_path, filename, mount_status_id) VALUES (?, ?, ?, ?)"
        update_or_insert_db(sql, [full_path_str, rel_path_str, filename, mount_status])
    else:
        current_app.logger.debug('({}) already in DB: {}'.format(disk_image['id'], full_path))


def insert_images():
    for root, dirs, files in os.walk(current_app.config['IMAGE_DIR']):
        for filename in files:

            full_path = Path(root, filename)

            if check_ignored(full_path):
                continue

            if not filename.startswith('.') and full_path.is_file():
                insert_image(full_path)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        database_file = current_app.config['DATABASE']
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
        status_codes = ['Mounted',
                        'Unable to mount',
                        'Unmounted']
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
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def check_ignored(full_path):
    full_path_str = str(full_path)

    # Ignore *.db since the sqlite DB could be in this directory
    if re.match(r'.*\.db$', full_path_str, flags=re.I):
        return True

    # Ignore *.E02, *.E03, ..., *.EAA, *.EAB, ..., but not *.E01
    if (not full_path_str.lower().endswith('log') and
            re.match(r'.*\.[EL]X?\w\w$', full_path_str, flags=re.I) and
            not re.match(r'.*\.[EL]X?01$', full_path_str, flags=re.I)):
        return True

    # Ignore *.002, *.003, ..., but not *.001
    if (re.match(r'.*\.\d\d\d$', full_path_str) and
            not re.match(r'.*\.001$', full_path_str)):
        return True

    # Ignore *-sXXX.vmdk, but not *.vmdk
    if re.match(r'.*\-s\w\w\w\.vmdk$', full_path_str, flags=re.I):
        return True

    # Ignore  *-1.vhd, *-2.vhd, ...,  *-N.vhd, but not *-0.vhd
    if (re.match(r'.*\-\w+\.vhd$', full_path_str, flags=re.I) and
            not re.match(r'.*\-0\.vhd$', full_path_str, flags=re.I)):
        return True

    return False
