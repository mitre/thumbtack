import json
import os

from pprint import pprint

import pytest


def test_find_library_support(test_client):
    """
    GIVEN a Thumbtack Flask application client
    WHEN the '/supported' page is requested (GET)
    THEN check that the page shows which libraries it can check
    """
    # NOTE: this test does not verify support for individual libraries,
    # only that the page itself exists
    print('################  Test Find Library Support')
    response = test_client.get('/supported')
    print('response', type(response), response)
    assert response.status_code == 200

    potential_libraries = ['xmount', 'ewfmount', 'affuse', 'vmware-mount', 'mountavfs', 'qemu-nbd', 'mmls', 'pytsk3',
                           'parted', 'fsstat', 'file', 'blkid', 'python-magic', 'disktype', 'mount.xfs', 'mount.ntfs',
                           'lvm', 'vmfs-fuse', 'mount.jffs2', 'mount.squashfs', 'mdadm', 'cryptsetup', 'bdemount',
                           'vshadowmount']
    data = json.loads(response.data.decode('utf-8'))
    for lib in potential_libraries:
        assert lib in data


def test_get_info_empty_mount_list(test_client):
    """
    GIVEN a Thumbtack Flask application client
    WHEN the '/mounts' page is requested (GET)
    THEN check the response code is valid and no images are mounted
    """
    print('################  Test Get Info Empty Mount List')
    response = test_client.get('/mounts/')
    assert response.status_code == 200
    assert json.loads(response.data.decode('utf-8')) == []


def test_get_info_nonexistent_image(test_client):
    """
    GIVEN a Thumbtack Flask application client
    WHEN information is requested about a non-existent disk image (GET)
    THEN check the response code is valid and no images are mounted
    """
    print('################  Test Get Invalid Image')
    response = test_client.get('/mounts/nonexistent/disk/image.E01')
    assert response.status_code == 404


def test_mount_nonexistent_image(test_client):
    """
    GIVEN a Thumbtack Flask application client
    WHEN a non-existent disk image is requested to be mounted (PUT)
    THEN check the response code is valid and no images are mounted
    """
    print('\n################  Test Mount Non-existent Image')
    response = test_client.put('/mounts/nonexistent/disk/image.E01')
    assert response.status_code == 400

    response = test_client.get('/mounts/')
    assert response.status_code == 200
    assert json.loads(response.data.decode('utf-8')) == []


def test_mount_invalid_image(test_client):
    """
    GIVEN a Thumbtack Flask application client
    WHEN an invalid disk image (text file) is requested to be mounted (PUT)
    THEN check the response code is valid and no images are mounted
    """
    print('\n################  Test Mount Invalid Image')
    response = test_client.put('/mounts/foo.dd')
    assert response.status_code == 400

    response = test_client.get('/mounts/')
    assert response.status_code == 200
    assert json.loads(response.data.decode('utf-8')) == []


@pytest.mark.parametrize("test_image_path", [
    'dftt_images/10-ntfs-disk.dd',
    'dftt_images/11-carve-fat.dd',
    'dftt_images/12-carve-ext2.dd',
    'dftt_images/7-ntfs-undel.dd',
    'dftt_images/8-jpeg-search.dd',
    'dftt_images/9-fat-label.dd',
    'dftt_images/daylight.dd',
    'dftt_images/ext-part-test-2.dd',
    'dftt_images/ntfs-img-kw-1.dd',
    'digitalcorpora/lone_wolf/LoneWolf.E01',
    'digitalcorpora/m57-jean/nps-2008-jean.E01',
    'digitalcorpora/m57-patents/charlie-2009-12-11.E01',
    'digitalcorpora/m57-patents/charlie-work-usb-2009-12-11.E01',
    'digitalcorpora/m57-patents/jo-2009-12-11-001.E01',
    'digitalcorpora/m57-patents/jo-favorites-usb-2009-12-11.E01',
    'digitalcorpora/m57-patents/pat-2009-12-11.E01',
    'digitalcorpora/m57-patents/terry-2009-12-11-001.E01',
    'digitalcorpora/m57-patents/terry-work-usb-2009-12-11.E01',
    'digitalcorpora/national_gallery/tracy-home-2012-07-16-final.E01'
])
def test_mount_valid_images(test_client, expected_test_results, test_image_path):
    """
    GIVEN a Thumbtack Flask application client
    WHEN a disk image is requested to be mounted (PUT)
    THEN check the response code is valid
    """

    print('\n################  Test Mount Valid Images')

    if not os.path.isfile(os.path.join('test_images', test_image_path)):
        pytest.skip('Skipping disk mounting service test because test disk image is missing ({})'.format(test_image_path))

    for disk_image_info in expected_test_results:
        if disk_image_info['expected_json_response']['imagepath'] == test_image_path:
            expected_json_results = disk_image_info['expected_json_response']
            assertions = disk_image_info['assertions']

            # ignore the invalid images from the expected json results file
            if not assertions['mountable']:
                continue

            relative_image_path = expected_json_results['imagepath']
            # update imagepath in expected results to be full path because that is what is returned
            expected_json_results['imagepath'] = '{}/{}'.format(test_client.application.config['IMAGE_DIR'],
                                                                expected_json_results['imagepath'])

            print('\n############################  Mounting: {}'.format(relative_image_path))

            # MOUNT IMAGE
            # Verify PUT /mounts/<TEST_DISK_IMAGE> returns the new mount
            mount_dir = test_client.application.config['MOUNT_DIR']
            print('mounting: {}'.format(relative_image_path))
            # response = test_client.put(u'/mounts/{}'.format(relative_image_path))
            response = test_client.put(u'/mounts/{}?mount_dir={}'.format(relative_image_path, mount_dir))
            assert response.status_code == 200

            response_json = json.loads(response.data.decode('utf-8'))
            disk_mountpoint = response_json.get('mountpoint')

            volumes = response_json['volumes']
            for volume in volumes:
                volume.pop('mountpoint')  # removing volume mountpoints because values are randomized

            # volume_mountpoint = volumes[0].pop('mountpoint')  # removing mountpoint because value is randomized

            num_volumes = len(volumes)
            del response_json['mountpoint']  # removing disk mountpoint because value is randomized

            print('disk_mountpoint: {}'.format(disk_mountpoint))
            print('volumes: {}'.format(num_volumes))

            assert disk_mountpoint is not None
            assert num_volumes == assertions['num_volumes']
            assert response_json == expected_json_results
            for volume in volumes:
                if not volume.get('mountpoint') in [None, '']:
                    assert os.access(volume['mountpoint'], os.R_OK)  # Verify the mount point can be accessed

            # GET MOUNTED IMAGE INFO
            # Verify GET /mounts/ returns the new mount
            response = test_client.get(u'/mounts/{}'.format(relative_image_path))
            assert response.status_code == 200

            response_json = json.loads(response.data.decode('utf-8'))
            # pprint(response_json)
            disk_info = response_json['disk_info']
            del disk_info['mountpoint']
            assert len(disk_info['volumes']) == assertions['num_volumes']

            volumes = disk_info['volumes']
            all_volume_mountpoints = [x['mountpoint'] for x in volumes if x['mountpoint'] != '']
            for volume in volumes:
                del volume['mountpoint']  # removing because value is randomized
            assert disk_info == expected_json_results

            # UNMOUNT IMAGE
            # Verify DELETE /mounts/<TEST_DISK_IMAGE> unmounts the image
            response = test_client.delete(u'/mounts/{}'.format(relative_image_path))
            assert response.status_code == 200

            # Verify the mount point is gone
            for volume_mountpoint in all_volume_mountpoints:
                assert not os.access(volume_mountpoint, os.R_OK)


def test_mount_images_with_unmountable_volumes(test_client, expected_test_results):
    """
    GIVEN a Thumbtack Flask application client
    WHEN a valid disk image that only has volumes that are unmountable are requested to be mounted (PUT)
    THEN check the response code is 400
    """

    print('\n################  Test Mount Valid Images with unmountable volumes')

    for disk_image_info in expected_test_results:

        expected_json_results = disk_image_info['expected_json_response']
        assertions = disk_image_info['assertions']

        # ignore the valid images from the expected json results file
        if assertions['mountable']:
            continue

        relative_image_path = expected_json_results['imagepath']
        # update imagepath in expected results to be full path because that is what is returned
        expected_json_results['imagepath'] = '{}/{}'.format(test_client.application.config['IMAGE_DIR'], expected_json_results['imagepath'])

        print('\n############################  Mounting: {}'.format(relative_image_path))

        if not os.path.isfile(os.path.join('test_images', relative_image_path)):
            # TODO: this will skip the whole test if any one file is missing. Needs to be addressed
            print('skipping: {}'.format(relative_image_path))
            pytest.skip('Skipping disk mounting service test because test disk image is missing ({})'.format(relative_image_path))

        # MOUNT IMAGE
        # Verify PUT /mounts/<TEST_DISK_IMAGE> returns the new mount
        print('mounting: {}'.format(relative_image_path))
        response = test_client.put(u'/mounts/{}'.format(relative_image_path))
        assert response.status_code == 400
