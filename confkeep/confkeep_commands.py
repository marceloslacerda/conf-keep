import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

from confkeep import settings

SCRIPT_TEMPLATE = """#!/bin/sh
export REPO_PATH='{repo_path}'
{ignore_sync_errors}
cd {project_path}
{python_interpreter} -m conf-keep sync > /var/log/conf-keep-sync.log 2>&1
"""

SERVICE_NAME = "conf-keep"
ADD_WATCH_COMMAND = "watch"
ADD_HOST_COMMAND = "add-host"
BOOTSTRAP_COMMAND = "bootstrap"
SYNC_COMMAND = "sync"
INSTALL_CRON_COMMAND = "install-cron"
CRON_FILE_PATH = pathlib.Path("/etc/cron.d/conf-keep")


class ConfKeepError(Exception):
    pass


def with_test_repo(func):
    def wrapper(*args, **kwargs):
        if "self" in kwargs:
            obj = kwargs["self"]
        else:
            obj = args[0]
        lock_file_path = obj.repo_path / "conf-keep.lock"
        if obj.is_ip_changed():
            raise ConfKeepError()  # Notifications already printed
        elif lock_file_path.is_file():
            print("Another command is running in this repository.")
            raise ConfKeepError()
        else:
            lock_file_path.touch()
            try:
                func(*args, **kwargs)
            finally:
                os.remove(lock_file_path)

    return wrapper


class CKWrapper:
    def __init__(self):
        self._host_name = None

    @property
    def repo_path(self):
        if not settings.REPO_PATH:
            settings.REPO_PATH = pathlib.Path(
                input("Please type the local repository path (absolute): ")
            )
        return settings.REPO_PATH

    @property
    def original_ip_path(self):
        return self.repo_path / "original-ip.txt"

    @property
    def new_ip_path(self):
        return self.repo_path / "new-ip.txt"

    @property
    def hostname_path(self):
        return self.repo_path / "hostname.txt"

    @property
    def hostname(self):
        if not self._host_name:
            if self.hostname_path.is_file():
                self._host_name = self.hostname_path.read_text()
            else:
                raise ConfKeepError("hostname.txt does not exist. Host not configured.")
        return self._host_name

    def initial_hostname_setup(self):
        if settings.ASSUME_YES:
            self._host_name = settings.HOST_NAME
        else:
            self._host_name = input(
                f"Please input the host, hostname. Press enter for {settings.HOST_NAME}: "
            )
            if not self._host_name:
                self._host_name = settings.HOST_NAME
        self.hostname_path.write_text(self._host_name)

    @property
    def work_path(self):
        if self.hostname_path.is_file():
            return self.repo_path / self.hostname_path.read_text()
        else:
            raise ConfKeepError("hostname.txt does not exist. Host not configured.")

    @property
    def tracked_file_path(self):
        return self.work_path / "tracked.txt"

    @property
    def remote(self):
        if not settings.REMOTE:
            settings.REMOTE = input("Please type the remote repository url: ")
        return settings.REMOTE

    def is_ip_changed(self):
        original_ip_out = json.loads(self.original_ip_path.read_text())
        new_ip_out = get_ip_interfaces()
        if not self.original_ip_path.is_file():
            print("Original was removed. Adding a new one")
            self.original_ip_path.write_text(json.dumps(new_ip_out))
            return False
        else:
            if original_ip_out == new_ip_out:
                print("ip output haven't changed.")
                return False
            else:
                print(
                    f"ip output changed! Please ensure that {self.work_path} is the name of this host, change"
                    f" {self.hostname_path} accordingly and remove {self.original_ip_path} once you are done."
                )
                self.new_ip_path.write_text(json.dumps(new_ip_out))
                subprocess.run(
                    [
                        "diff",
                        self.original_ip_path.absolute(),
                        self.new_ip_path.absolute(),
                    ]
                )
                return True

    def config_host(self):
        """To add another host to the repository"""
        print("Configuring host")
        repo_path = self.repo_path
        if not repo_path.is_dir():
            remote_url = self.remote
            print(f"Cloning repository {remote_url}.")
            subprocess.run(["git", "clone", remote_url, repo_path], check=True)
        else:
            pass  # No need to pull until we know the branch
        self.initial_hostname_setup()
        print(self.work_path)
        if self.work_path.is_dir():
            if is_yes(
                f"Theres already a configuration directory for the host {self.hostname}. Do you want to delete it"
            ):
                shutil.rmtree(self.work_path)
                print("Removed.")
            else:
                raise ConfKeepError("Aborted by user.")

        print("Creating a configuration directory for the host.")
        try:
            self.git_command("checkout", "-b", self.hostname)
        except subprocess.CalledProcessError:
            if is_yes(
                "Error encountered while creating and changing branches. Do you wish to continue anyway?"
            ):
                self.git_command("checkout", self.hostname)
            else:
                raise ConfKeepError("Aborting.")
        self.work_path.mkdir()
        tracked_path = self.tracked_file_path
        tracked_path.touch()
        with self.original_ip_path.open("w") as original_ip:
            original_ip.write(json.dumps(get_ip_interfaces()))
        self.git_add(tracked_path.absolute())
        self.git_add(self.original_ip_path.absolute())
        self.git_commit_am(f"Host {self.hostname} added to the repo")
        self.git_push(self.hostname)
        print(
            f"The host {self.hostname} has been setup for tracking configuration "
            f"changes. Add new files or directories to track with the command "
            f"{ADD_WATCH_COMMAND}."
        )

    def bootstrap_repository(self):
        """To create the repository"""
        print("Bootstrapping repository")
        if (self.repo_path / ".git").is_dir():
            raise ConfKeepError(
                "Repository already exists. Aborting bootstrap.\n"
                f"You can avoid this error by running the following at your own peril.\n"
                f"rm -rf {self.repo_path / '.git*'} {self.repo_path / '*'}"
            )
        self.repo_path.mkdir(exist_ok=True, parents=True)
        self.git_command("init")
        gitignore_path = self.repo_path / ".gitignore"
        gitignore_path.write_text(get_gitignore())
        self.git_add(gitignore_path)
        remote_url = self.remote
        self.git_command("remote", "add", "origin", remote_url)
        self.git_commit_am("Initial commit")
        self.git_push("master")
        print(
            f"Repository bootstrapped. You can now add new hosts to the repository with {ADD_HOST_COMMAND}."
        )
        print(
            "For your convenience you can run the following commands to avoid some prompts:"
        )
        print()
        print(f"export REPO_PATH={self.repo_path}")
        print(f"export REMOTE={self.remote}")

    @with_test_repo
    def track_dir(self):
        if not settings.MONITORED_PATH:
            directory = pathlib.Path(input("What do you want to start tracking? "))
        else:
            directory = settings.MONITORED_PATH
        if not directory.is_absolute():
            raise AttributeError(f"The directory {directory} must be an absolute path.")
        if any(
            str(directory.absolute()) == path
            for path in self.tracked_file_path.read_text().splitlines()
        ):
            print(f"The directory {directory} is already being tracked. Nothing to do.")
            return
        with self.tracked_file_path.open("at") as tracked:
            tracked.write(str(directory) + "\n")
        self.git_add(self.tracked_file_path.absolute())
        self.git_commit_am(f"New directory {directory} being tracked.")
        self.git_push(self.work_path.name)

    @with_test_repo
    def watchdog(self):
        to_sync = self.tracked_file_path.read_text().splitlines()
        if not to_sync:
            raise ConfKeepError(
                f"No files being monitored yet, use the command {ADD_WATCH_COMMAND} before calling"
                f" {SYNC_COMMAND}."
            )
        for path in to_sync:
            subprocess.run(
                ["rsync", "-avz", path, pathlib.Path(path).parent.name],
                check=not settings.IGNORE_SYNC_ERRORS,
                cwd=self.work_path,
            )
        status = self.git_command("status", "-s", get_stdout=True).splitlines()
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
            commit_message_body += f"\nThere are more {len(status) - 5} changes..."
        if some_added and some_changed:
            commit_message_head = "Some files were added and changed"
        elif some_added:
            commit_message_head = "Some file(s) were added"
        elif some_changed:
            commit_message_head = "Some file(s) were changed"
        else:
            print("Nothing changed")
            return
        self.git_add(".")
        self.git_command("commit", "-m", commit_message_head, "-m", commit_message_body)
        self.git_push(self.work_path.name)
        print(f"{len(status)} changes commited")

    def git_command(self, *args, get_stdout=False):
        ls = ["git"]
        ls.extend(args)
        if not get_stdout:
            subprocess.run([str(x) for x in ls], check=True, cwd=self.repo_path)
        else:
            cp = subprocess.run(
                [str(x) for x in ls],
                check=True,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
            )
            return cp.stdout

    def git_commit_am(self, message):
        self.git_command("commit", "-m", message)

    def git_push(self, branch):
        self.git_command("push", "origin", branch)

    def git_add(self, file):
        self.git_command("add", file)

    def install_cron(self):
        print("Installing cron file")
        script_path = pathlib.Path("/usr/local/bin/conf-keep-sync")
        if settings.IGNORE_SYNC_ERRORS:
            ignore_sync_errors = "export IGNORE_SYNC_ERRORS=TRUE"
        else:
            ignore_sync_errors = ""
        script_path.write_text(
            SCRIPT_TEMPLATE.format(
                repo_path=self.repo_path,
                python_interpreter=sys.executable,
                project_path=pathlib.Path(__file__).parent.parent,
                ignore_sync_errors=ignore_sync_errors,
            )
        )
        script_path.chmod(0o755)
        CRON_FILE_PATH.write_text(
            f"{settings.CRON_SCHEDULE} {settings.CK_USER} {script_path}\n"
        )
        if settings.CK_USER not in pathlib.Path("/etc/passwd").read_text():
            print(
                f"""Warning! No user "{settings.CK_USER}" detected!
Please add one with: useradd -m -s /bin/bash {settings.CK_USER}
Or change the generated cronfile."""
            )
        print(f"Cronfile installed at {CRON_FILE_PATH}")


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


def get_gitignore():
    return """new-ip.txt
hostname.txt
conf-keep.lock
"""


def is_yes(message):
    if settings.ASSUME_YES:
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
