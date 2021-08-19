import pathlib
import shutil
import subprocess

from settings import (
    REPO_PATH,
    HOST_NAME,
    SERVICE_NAME,
    OLD_IP_PATH,
    NEW_IP_PATH,
    HOSTNAME_PATH,
    ADD_WATCH_CMD,
    ADD_HOST_COMMAND,
    ASSUME_YES,
    DEFAULT_REMOTE,
)

from git_commands import git_command, git_push, git_commit_am, git_add


def test_host_dir():
    print("Deciding host dir")
    with NEW_IP_PATH.open("w") as new_ip_file:
        subprocess.run(["ip", "a"], stdout=new_ip_file, encoding="utf-8")
    if not OLD_IP_PATH.exists():
        print(f"{SERVICE_NAME} is being run for the first time with {REPO_PATH}")
        NEW_IP_PATH.rename(OLD_IP_PATH)
        host_name = input(
            f"{SERVICE_NAME} guessed host name as {HOST_NAME}.\nPress enter to"
            f"accept it or type a different hostname: "
        )
        if not host_name:
            host_name = HOST_NAME
        HOSTNAME_PATH.write_text(host_name)
    else:
        if NEW_IP_PATH.read_text() == OLD_IP_PATH.read_text():
            print(
                "Device interfaces have not changed. Assuming that the host"
                "isn't a clone"
            )
            host_name = HOSTNAME_PATH.read_text()
        else:
            host_name = HOSTNAME_PATH.read_text()
            new_host_name = input(
                f"Host interfaces changed! Please type the new hostname. "
                f"Press enter for {host_name}"
            )
            if new_host_name:
                host_name = new_host_name
            HOSTNAME_PATH.write_text(host_name)
            NEW_IP_PATH.rename(OLD_IP_PATH)


def config_host():
    """To add another host to the repository"""
    print("Configuring host")
    if not REPO_PATH.is_dir():
        remote_url = get_remote()
        print(f"Cloning repository {remote_url}")
        subprocess.run(["git", "clone", remote_url, REPO_PATH], check=True)
    else:
        pass  # No need to pull until we know the branch
    host_name = input(f"Please input the host, hostname. Press enter for {HOST_NAME}: ")
    if not host_name:
        host_name = HOST_NAME
    print(f"Continuing with hostname = {host_name}")
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

    print("Creating a configuration directory for the host")
    git_command("checkout", "-b", host_name)
    work_path.mkdir()
    tracked_path = get_tracked_file_path(work_path)
    tracked_path.touch()
    git_add(tracked_path.absolute())
    git_commit_am(f"Host {host_name} added to the repo")
    git_push(host_name)
    print(
        f"The host {host_name} has been setup for tracking configuration "
        f"changes. Add new files or directories to track with the command "
        f"{ADD_WATCH_CMD}"
    )


def get_gitignore():
    return """new-ip
old-ip
hostname.txt
"""


def bootstrap_repository():
    """To create the repository"""
    print("Bootstrapping repository")
    if (REPO_PATH / ".git").is_dir():
        if is_yes("Repository already exists do you want to delete it"):
            shutil.rmtree(REPO_PATH)
        else:
            raise FileExistsError("Aborting bootstrap")
    REPO_PATH.mkdir(exist_ok=True, parents=True)
    git_command("init")
    (REPO_PATH / ".gitignore").write_text(get_gitignore())
    git_add(".gitignore")
    remote_url = get_remote()
    git_command("remote", "add", "origin", remote_url)
    git_commit_am("Initial commit")
    git_push("master")
    print(
        f"Repository bootstrapped. You can now add new hosts to the repository with {ADD_HOST_COMMAND}."
    )


def is_yes(message):
    if ASSUME_YES:
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
        raise AttributeError("Host not configured")


def get_tracked_file_path(work_path):
    return work_path / "tracked.txt"


def track_dir(directory):
    work_path = get_work_path()
    tracked_path = get_tracked_file_path(work_path)
    with tracked_path.open("at") as tracked:
        tracked.write(str(directory) + "\n")
    git_add(tracked_path.absolute())
    git_commit_am(f"New directory {directory} being tracked")
    git_push(work_path.name)


if __name__ == "__main__":
    bootstrap_repository()
    config_host()
    track_dir(pathlib.Path("/etc"))
