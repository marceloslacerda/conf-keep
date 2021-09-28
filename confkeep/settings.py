import os
import pathlib
import platform
from confkeep.util import get_path_environ
from os import environ

# Customizable settings

# You can change these by setting the environment variables before calling conf-keep.

# * Settings with sane defaults
# These can be kept as they are if you don't want to change them.

# Trying to guess the hostname correctly is extremely important for conf-keep as it avoid multiple hosts mixing their
# histories.
HOST_NAME = environ.get("HOST_NAME", platform.node())
# You must set this one if you want to configure conf-keep non-interactively.
ASSUME_YES = environ.get("ASSUME_YES", False)
# Conserviative version of the above variable. Mostly used for debugging.
ASSUME_NO = environ.get("ASSUME_YES", False)
# By default conf-keep runs every minute. Change this to however you like.
CRON_SCHEDULE = environ.get("CRON_SCHEDULE", "* * * * *")
# This is the user that will run the sync under cron.
CK_USER = environ.get("CONFKEEP_USER", "conf-keep")
# If set rsync will ignore errors. Useful for testing or when you only want to commit "world-readable" files
IGNORE_SYNC_ERRORS = environ.get("IGNORE_SYNC_ERRORS", False)
# Currently conf-keep relies on the ip address of a host to tell whether it's the same host or not, a clone of a
# machine would have the same hostname but a different ip address, if both machines tried to commit to the same branch
# of the REMOTE the history would be *soiled* and that would be a pain to clean up.
#
# Setting this variable to True disables that checking. That's useful for machines that don't have fixed ips like, one
# that uses DNS or wifi.
IGNORE_IP_CHANGES = environ.get("IGNORE_IP_CHANGES", False)

# * Settings without sane defaults
# These must be changed either interactively or through environment variables.

# The path to the local copy of your changes. Always use absolute paths to avoid errors.
REPO_PATH = get_path_environ("REPO_PATH", None)
# The remote repository where you will be storing your history.
REMOTE = os.environ.get("REMOTE", None)
# The local file/directory that you want to track
MONITORED_PATH = get_path_environ("MONITORED_PATH", None)
