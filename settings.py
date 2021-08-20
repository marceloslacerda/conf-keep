import pathlib
import platform

REPO_PATH = pathlib.Path("repo-path")
MONITORED_PATH = pathlib.Path("monitored-dir")
HOST_NAME = platform.node()
SERVICE_NAME = "conf-keep"
ORIGINAL_IP_PATH = REPO_PATH / "original-ip.txt"
NEW_IP_PATH = REPO_PATH / "new-ip.txt"
HOSTNAME_PATH = REPO_PATH / "hostname.txt"
ADD_WATCH_CMD = "watch"
ADD_HOST_COMMAND = "add-host"
ASSUME_YES = True
DEFAULT_REMOTE = pathlib.Path("./repo-origin/").absolute()
IGNORE_SYNC_ERRORS = True
