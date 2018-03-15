import os
import re

import requests

from flask import Blueprint, current_app, redirect, render_template, request, url_for

main = Blueprint('', __name__)

BASE_URL = 'http://localhost:5000'

STATUS_CODES = {
    200: 'Mounted',
    400: 'Unable to mount',
    404: 'Unmounted',
    500: 'Server error'
}


@main.route('/', methods=['GET'])
@main.route('/index', methods=['GET'])
def index():
    app = current_app._get_current_object()
    image_dir = app.config['IMAGE_DIR']
    supported_mount_types = []
    unsupported_mount_types = []

    url = '{}/supported'.format(BASE_URL)
    response = requests.get(url)
    if response.status_code == 200:
        json_response = response.json()
        for mount_type, supported in json_response.items():
            if supported:
                supported_mount_types.append(mount_type)
            else:
                unsupported_mount_types.append(mount_type)

    images = {}
    for root, dirs, files in os.walk(image_dir):
        for filename in files:

            rel_dir = os.path.relpath(root, image_dir)
            if rel_dir == '.':
                rel_file = os.path.join(rel_dir, filename)[2:]
            else:
                rel_file = os.path.join(rel_dir, filename)
            url = "{}/mounts/{}".format(BASE_URL, rel_file)

            full_path = os.path.join(root, filename)
            # Ignore *.E02, *.E03, ..., *.EAA, *.EAB, ..., but not *.E01
            if (not full_path.lower().endswith('log') and
                    re.match('.*\.[EL]X?\w\w$', full_path, flags=re.I) and
                    not re.match('.*\.[EL]X?01$', full_path, flags=re.I)):
                continue

            # Ignore *.002, *.003, ..., but not *.001
            if (re.match('.*\.\d\d\d$', full_path) and
                    not re.match('.*\.001$', full_path)):
                continue

            # Ignore *-sXXX.vmdk, but not *.vmdk
            if re.match('.*\-s\w\w\w\.vmdk$', full_path, flags=re.I):
                continue

            # Ignore  *-1.vhd, *-2.vhd, ...,  *-N.vhd, but not *-0.vhd
            if (re.match('.*\-\w+\.vhd$', full_path, flags=re.I) and
                    not re.match('.*\-0\.vhd$', full_path, flags=re.I)):
                continue

            if not filename.startswith('.') and os.path.isfile(full_path):
                response = requests.get(url)
                # response.raise_for_status()
                status = STATUS_CODES[response.status_code]

                json_response = response.json()
                # print(json_response)

                disk_mountpoint = ''
                ref_count = 0
                vol_mountpoints = {}
                if status == 'Mounted':
                    if 'mountpoint' in json_response['disk_info']:
                        disk_mountpoint = json_response['disk_info']['mountpoint']

                        for volume in json_response['disk_info']['volumes']:
                            sanitized_rel_file = rel_file.replace('/', '_').replace(':', '-').replace('.', '-')
                            uid = '{}_{}'.format(sanitized_rel_file, volume['index'])
                            vol_mountpoints[volume['index']] = [volume['mountpoint'], uid]

                    ref_count = json_response['ref_count']

                images[rel_file] = [full_path, status, disk_mountpoint, vol_mountpoints, ref_count]

    return render_template('index.html',
                           supported_mount_types=supported_mount_types,
                           unsupported_mount_types=unsupported_mount_types,
                           image_dir=image_dir,
                           images=images)


@main.route('/mount_form', methods=['POST'])
def mount_form():
    img_to_mount = request.form['img_to_mount']
    operation = request.form['operation']
    url = "{}/mounts/{}".format(BASE_URL, img_to_mount)
    status = None

    if operation == 'mount':
        response = requests.put(url)
        if response.status_code == 200:
            status = 'Mounted successfully'
    elif operation == 'unmount':
        response = requests.delete(url)
        if response.status_code == 200:
            status = 'Unmounted successfully'
    else:
        print('Unknown operation! How did you even get here!?')
        return redirect('/')

    if not status:
        status = 'Unable to complete operation'

    return render_template('form_complete.html',
                           status=status)

