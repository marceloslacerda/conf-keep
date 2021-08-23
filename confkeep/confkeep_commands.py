import json
import os
import pathlib
import re
import shutil
import subprocess

from settings import (
    REPO_PATH,
    HOST_NAME,
    NEW_IP_PATH,
    HOSTNAME_PATH,
    ADD_WATCH_COMMAND,
    ADD_HOST_COMMAND,
    ASSUME_YES,
    DEFAULT_REMOTE,
    ORIGINAL_IP_PATH,
    IGNORE_SYNC_ERRORS,
    CRON_FILE_PATH,
    CK_USER,
    SYNC_COMMAND,
    CRON_SCHEDULE,
)

from git_commands import git_command, git_push, git_commit_am, git_add


def is_ip_changed():
    original_ip_out = json.loads(ORIGINAL_IP_PATH.read_text())
    new_ip_out = get_ip_interfaces()
    if not ORIGINAL_IP_PATH.is_file():
        print("Original was removed. Adding a new one")
        ORIGINAL_IP_PATH.write_text(new_ip_out)
        return False
    else:
        if original_ip_out == new_ip_out:
            print("ip output haven't changed.")
            return False
        else:
            print(
                f"ip output changed! Please ensure that {get_work_path().name} is the name of this host, change"
                f" {HOSTNAME_PATH} accordingly and remove {ORIGINAL_IP_PATH} once you are done."
            )
            NEW_IP_PATH.write_text(json.dumps(new_ip_out))
            subprocess.run(
                ["diff", ORIGINAL_IP_PATH.absolute(), NEW_IP_PATH.absolute()]
            )
            return True


def get_ip_interfaces():
    out = subprocess.run(["ip", "a"], stdout=subprocess.PIPE, encoding="utf-8").stdout
    interfaces = {}
    ips = None
    for line in out.splitlines():
        line = line.strip()
        match = re.match(r"\d+: (\w+): ", line)
        if match:
            ips = []
            interfaces[match.group(1)] = ips
        else:
            if line.startswith("inet"):
                ips.append(line.split(maxsplit=2)[1])
    return interfaces


def config_host():
    """To add another host to the repository"""
    print("Configuring host")
    if not REPO_PATH.is_dir():
        remote_url = get_remote()
        print(f"Cloning repository {remote_url}.")
        subprocess.run(["git", "clone", remote_url, REPO_PATH], check=True)
    else:
        pass  # No need to pull until we know the branch
    if ASSUME_YES:
        host_name = None
    else:
        host_name = input(
            f"Please input the host, hostname. Press enter for {HOST_NAME}: "
        )
    if not host_name:
        host_name = HOST_NAME
    print(f"Continuing with hostname = {host_name}.")
    HOSTNAME_PATH.write_text(host_name)
    work_path = REPO_PATH / host_name
    if work_path.is_dir():
        if is_yes(
            "Theres already a configuration directory for the host {host_name}. Do you want to delete it"
        ):
            shutil.rmtree(work_path)
            print("Removed.")
        else:
            print(f"Nothing to do. Exiting.")

    print("Creating a configuration directory for the host.")
    try:
        git_command("checkout", "-b", host_name)
    except subprocess.CalledProcessError:
        if is_yes(
            "Error encountered while creating and changing branches. Do you wish to continue anyway?"
        ):
            git_command("checkout", host_name)
        else:
            raise
    work_path.mkdir()
    tracked_path = get_tracked_file_path(work_path)
    tracked_path.touch()
    with ORIGINAL_IP_PATH.open("w") as original_ip:
        original_ip.write(json.dumps(get_ip_interfaces()))
    git_add(tracked_path.absolute())
    git_add(ORIGINAL_IP_PATH.absolute())
    git_commit_am(f"Host {host_name} added to the repo")
    git_push(host_name)
    print(
        f"The host {host_name} has been setup for tracking configuration "
        f"changes. Add new files or directories to track with the command "
        f"{ADD_WATCH_COMMAND}."
    )


def get_gitignore():
    return """new-ip.txt
hostname.txt
conf-keep.lock
"""


def bootstrap_repository():
    """To create the repository"""
    print("Bootstrapping repository")
    if (REPO_PATH / ".git").is_dir():
        if is_yes("Repository already exists do you want to delete it"):
            shutil.rmtree(REPO_PATH)
        else:
            raise FileExistsError("Aborting bootstrap.")
    REPO_PATH.mkdir(exist_ok=True, parents=True)
    git_command("init")
    (REPO_PATH / ".gitignore").write_text(get_gitignore())
    git_add("../.gitignore")
    remote_url = get_remote()
    git_command("remote", "add", "origin", remote_url)
    git_commit_am("Initial commit")
    git_push("master")
    print(
        f"Repository bootstrapped. You can now add new hosts to the repository with {ADD_HOST_COMMAND}."
    )


def is_yes(message):
    if ASSUME_YES:
        print(message + "?")
        return True
    if not message.endswith("?"):
        message = message + " (y/n)? "
    while True:
        res = input(message) == "y"
        if res == "y" or res == "yes":
            return True
        elif res == "n" or "no":
            return False
        else:
            print(f'"{res}" is not "y" or "n"')


def get_remote():
    if not DEFAULT_REMOTE:
        return input("Please type the remote repository url (ssh): ")
    else:
        return DEFAULT_REMOTE


def get_work_path():
    if HOSTNAME_PATH.is_file():
        return REPO_PATH / HOSTNAME_PATH.read_text()
    else:
        raise AttributeError("Host not configured.")


def get_tracked_file_path(work_path):
    return work_path / "tracked.txt"


def with_test_repo(func):
    def wrapper(*args, **kwargs):
        lock_file_path = get_work_path() / "conf-keep.lock"
        if is_ip_changed():
            pass  # Notifications already printed
        elif lock_file_path.is_file():
            print("Another command is running in this repository.")
        else:
            lock_file_path.touch()
            func(*args, **kwargs)
            os.remove(lock_file_path)

    return wrapper


@with_test_repo
def track_dir(directory):
    work_path = get_work_path()
    tracked_path = get_tracked_file_path(work_path)
    if str(directory.absolute()) != str(directory):
        raise AttributeError(f"The directory {directory} must be an absolute path.")
    if any(
        str(directory.absolute()) == path
        for path in tracked_path.read_text().splitlines()
    ):
        print(f"The directory {directory} is already being tracked. Nothing to do.")
        return
    with tracked_path.open("at") as tracked:
        tracked.write(str(directory) + "\n")
    git_add(tracked_path.absolute())
    git_commit_am(f"New directory {directory} being tracked.")
    git_push(work_path.name)


@with_test_repo
def watchdog():
    work_path = get_work_path()
    tracked_path = get_tracked_file_path(work_path)
    to_sync = tracked_path.read_text().splitlines()
    for path in to_sync:
        subprocess.run(
            ["rsync", "-avz", path, pathlib.Path(path).name],
            check=not IGNORE_SYNC_ERRORS,
            cwd=work_path,
        )
    status = git_command("status", "-s", get_stdout=True).splitlines()
    commit_message_body = ""
    some_added = False
    some_changed = False
    for change in status[:5]:
        change = str(change.strip(), "utf-8").split(maxsplit=1)
        if change[0] == "??":
            some_added = True
            commit_message_body += f"\nFile {change[1]} added to the repository"
        elif change[0] == "M":
            some_changed = True
            commit_message_body += f"\nFile {change[1]} was changed"
    if len(status) > 5:
        commit_message_body += f"\nThere are more {len(status)-5} changes..."
    if some_added and some_changed:
        commit_message_head = "Some files were added and changed"
    elif some_added:
        commit_message_head = "Some file(s) were added"
    elif some_changed:
        commit_message_head = "Some file(s) were changed"
    else:
        print("Nothing changed")
        return
    git_add("..")
    git_command("commit", "-m", commit_message_head, "-m", commit_message_body)
    git_push(work_path.name)
    print(f"{len(status)} changes commited")


def install_cron():
    print("Installing cron file")
    CRON_FILE_PATH.write_text(f"{CRON_SCHEDULE} {CK_USER} conf-keep {SYNC_COMMAND}\n")
    print(f"Cronfile installed at {CRON_FILE_PATH}")
