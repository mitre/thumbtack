import os
import shutil
import sys

from urllib.parse import urlparse
from zipfile import ZipFile

import requests


def download(url: str, filename: str = None):

    if not filename:
        parsed = urlparse(url)
        print('Downloading: {} --> {}'.format(url, os.path.basename(parsed.path)))
        filename = os.path.basename(parsed.path)

    r = requests.get(url)

    with open(filename, 'wb') as f:
        f.write(r.content)


def unzip(filename):
    with ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall()


# https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def download_dftt_images():
    print('Downloading DFTT images (http://dftt.sourceforge.net)')
    if not query_yes_no('[695 MB] Download DFTT images?', 'no'):
        return

    dftt_urls = [
        'http://prdownloads.sourceforge.net/dftt/1-extend-part.zip?download',
        'http://prdownloads.sourceforge.net/dftt/2-kwsrch-fat.zip?download',
        'http://prdownloads.sourceforge.net/dftt/3-kwsrch-ntfs.zip?download',
        'http://prdownloads.sourceforge.net/dftt/4-kwsrch-ext3.zip?download',
        'http://prdownloads.sourceforge.net/dftt/5-fat-daylight.zip?download',
        'http://prdownloads.sourceforge.net/dftt/6-undel-fat.zip?download',
        'http://prdownloads.sourceforge.net/dftt/7-undel-ntfs.zip?download',
        'http://prdownloads.sourceforge.net/dftt/8-jpeg-search.zip?download',
        'http://prdownloads.sourceforge.net/dftt/9-fat-label.zip?download',
        'http://prdownloads.sourceforge.net/dftt/10b-ntfs-autodetect.zip?download',
        'http://prdownloads.sourceforge.net/dftt/11-carve-fat.zip?download',
        'http://prdownloads.sourceforge.net/dftt/12-carve-ext2.zip?download',
    ]

    dl_dir = 'tmp_dl'
    os.makedirs(dl_dir, exist_ok=True)
    os.chdir(dl_dir)     # cd <dl_dir>

    test_image_dir = '../test_images'
    dftt_dir = '{}/dftt_images'.format(test_image_dir)
    os.makedirs(dftt_dir, exist_ok=True)

    for url in dftt_urls:
        download(url)

    for filename in os.listdir('.'):
        _, ext = os.path.splitext(filename)
        if ext == '.zip':
            print('unzipping: {}'.format(filename))
            unzip(filename)

    for root, dirs, files in os.walk('.'):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext == '.dd':
                old_filepath = os.path.join(root, filename)
                new_filepath = os.path.join(dftt_dir, filename)
                print('moving {} --> {}'.format(old_filepath, new_filepath))
                os.rename(old_filepath, new_filepath)

    os.chdir('..')       # cd ..
    shutil.rmtree(dl_dir)


def download_digitalcorpora_images():
    print('Downloading Digital Corpora images (https://digitalcorpora.org)')

    dl_dir = 'tmp_dl'
    os.makedirs(dl_dir, exist_ok=True)
    os.chdir(dl_dir)     # cd <dl_dir>

    test_image_dir = '../test_images'
    digitalcorpora_dir = '{}/digitalcorpora'.format(test_image_dir)
    os.makedirs(os.path.join(digitalcorpora_dir, 'm57-patents'), exist_ok=True)
    os.makedirs(os.path.join(digitalcorpora_dir, 'm57-jean'), exist_ok=True)
    os.makedirs(os.path.join(digitalcorpora_dir, 'lone_wolf'), exist_ok=True)
    os.makedirs(os.path.join(digitalcorpora_dir, 'national_gallery'), exist_ok=True)

    if query_yes_no('[250 MB] Download M57 Patents USB images?', 'no'):
        urls = [
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/charlie-work-usb-2009-12-11.E01',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/jo-favorites-usb-2009-12-11.E01',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/terry-work-usb-2009-12-11.E01',
        ]
        for url in urls:
            download(url)
        for filename in os.listdir('.'):
            new_filepath = os.path.join(digitalcorpora_dir, 'm57-patents', filename)
            print('moving {} --> {}'.format(filename, new_filepath))
            os.rename(filename, new_filepath)

    if query_yes_no('[3 GB] Download M57 Jean images?', 'no'):
        urls = [
            'http://downloads.digitalcorpora.org/corpora/drives/nps-2008-m57-jean/nps-2008-jean.E01',
            'http://downloads.digitalcorpora.org/corpora/drives/nps-2008-m57-jean/nps-2008-jean.E02'
        ]
        for url in urls:
            download(url)
        for filename in os.listdir('.'):
            new_filepath = os.path.join(digitalcorpora_dir, 'm57-jean', filename)
            print('moving {} --> {}'.format(filename, new_filepath))
            os.rename(filename, new_filepath)

    if query_yes_no('[5.4 GB] Download National Gallery images?', 'no'):
        urls = [
            'http://downloads.digitalcorpora.org/corpora/scenarios/2012-ngdc/tracy-home/tracy-home-2012-07-16-final.E01',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2012-ngdc/tracy-home/tracy-home-2012-07-16-final.E02'
        ]
        for url in urls:
            download(url)
        for filename in os.listdir('.'):
            new_filepath = os.path.join(digitalcorpora_dir, 'national_gallery', filename)
            print('moving {} --> {}'.format(filename, new_filepath))
            os.rename(filename, new_filepath)

    if query_yes_no('[15 GB] Download Lone Wolf images?', 'no'):
        urls = [
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E01',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E02',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E03',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E04',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E05',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E06',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E07',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E08',
            'http://downloads.digitalcorpora.org/corpora/scenarios/2018-lonewolf/LoneWolf_Image_Files/LoneWolf.E09'
        ]
        for url in urls:
            download(url)
        for filename in os.listdir('.'):
            new_filepath = os.path.join(digitalcorpora_dir, 'lone_wolf', filename)
            print('moving {} --> {}'.format(filename, new_filepath))
            os.rename(filename, new_filepath)

    if query_yes_no('[24.7 GB] Download M57 Patents HDD images?', 'no'):
        urls = [
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/drives-redacted/charlie-2009-12-11.E01',   # 3.6 GB
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/drives-redacted/jo-2009-12-11-001.E01',    # 5.5 GB
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/drives-redacted/pat-2009-12-11.E01',       # 5.7 GB
            'http://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/drives-redacted/terry-2009-12-11-001.E01', # 9.9 GB
        ]
        for url in urls:
            download(url)
        for filename in os.listdir('.'):
            new_filepath = os.path.join(digitalcorpora_dir, 'm57-patents', filename)
            print('moving {} --> {}'.format(filename, new_filepath))
            os.rename(filename, new_filepath)

    os.chdir('..')       # cd ..
    shutil.rmtree(dl_dir)


def main():
    download_dftt_images()
    download_digitalcorpora_images()


if __name__ == "__main__":
    main()
