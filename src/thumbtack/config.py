import os

bind = "0.0.0.0:8208"
workers = 4
# env = None
# max-requests = None
# user = user
# group = group
logfile = "/var/log/thumbtack/thumbtack.log"
# loglevel = debug
THUMBTACK_IMAGE_DIR = os.getcwd()
# THUMBTACK_IMAGE_DIR = '/vagrant/tests/test_images'
THUMBTACK_MOUNT_DIR = "/mnt/thumbtack"
THUMBTACK_DATABASE = "database.db"

THUMBTACK_APPLICATION_ROOT = "/"
