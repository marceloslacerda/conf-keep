import pathlib
import shutil
import subprocess
import platform

REPO_PATH = pathlib.Path('repo-path')
MONITORED_PATH = pathlib.Path('monitored-dir')
HOST_NAME = platform.node()
SERVICE_NAME = 'conf-keep'
OLD_IP_PATH = REPO_PATH / 'old-ip'
NEW_IP_PATH = REPO_PATH / 'new-ip'
HOSTNAME_PATH = REPO_PATH / 'hostname.txt'
ADD_WATCH_CMD = 'watch'
ADD_HOST_COMMAND = "add-host"
ASSUME_YES = True
DEFAULT_REMOTE = 'git@github.com:marceloslacerda/test-conf-keep.git'


def test_host_dir():
    print('Deciding host dir')
    with NEW_IP_PATH.open('w') as new_ip_file:
        subprocess.run(['ip', 'a'], stdout=new_ip_file, encoding='utf-8')
    if not OLD_IP_PATH.exists():
        print(
            f'{SERVICE_NAME} is being run for the first time with {REPO_PATH}')
        NEW_IP_PATH.rename(OLD_IP_PATH)
        host_name = input(
            f"{SERVICE_NAME} guessed host name as {HOST_NAME}.\nPress enter to"
            f"accept it or type a different hostname: ")
        if not host_name:
            host_name = HOST_NAME
        HOSTNAME_PATH.write_text(host_name)
    else:
        if NEW_IP_PATH.read_text() == OLD_IP_PATH.read_text():
            print("Device interfaces have not changed. Assuming that the host"
                  "isn't a clone")
            host_name = HOSTNAME_PATH.read_text()
        else:
            host_name = HOSTNAME_PATH.read_text()
            new_host_name = input(
                f"Host interfaces changed! Please type the new hostname. "
                f"Press enter for {host_name}")
            if new_host_name:
                host_name = new_host_name
            HOSTNAME_PATH.write_text(host_name)
            NEW_IP_PATH.rename(OLD_IP_PATH)


def config_host():
    """To add another host to the repository"""
    print("Configuring host")
    if not REPO_PATH.is_dir():
        remote_url = get_remote()
        print(f'Cloning repository {remote_url}')
        subprocess.run(['git', 'clone', remote_url, REPO_PATH], check=True)
    else:
        pass  # No need to pull until we know the branch
    host_name = input(
        f"Please input the host, hostname. Press enter for {HOST_NAME}: ")
    if not host_name:
        host_name = HOST_NAME
    print(f"Continuing with hostname = {host_name}")
    HOSTNAME_PATH.write_text(host_name)
    work_path = REPO_PATH / host_name
    if work_path.is_dir():
        if is_yes("Theres already a configuration directory for the host {host_name}. Do you want to delete it"):
            shutil.rmtree(work_path)
            print("Removed.")
        else:
            print(f"Nothing to do. Exiting.")
            exit(0)

    print("Creating a configuration directory for the host")
    subprocess.run(['git', 'checkout', '-b', host_name], check=True, cwd=REPO_PATH)
    work_path.mkdir()
    blank_path = (work_path / 'blank.txt')
    blank_path.touch()
    subprocess.run(['git', 'add', blank_path.absolute()], check=True, cwd=REPO_PATH)
    subprocess.run(
        ['git', 'commit', '-m', f'Host {host_name} added to the repo'],
        check=True, cwd=REPO_PATH)
    subprocess.run(['git', 'push', 'origin', host_name], check=True, cwd=REPO_PATH)
    print(
        f"The host {host_name} has been setup for tracking configuration "
        f"changes. Add new files or directories to track with the command "
        f"{ADD_WATCH_CMD}")
    exit(0)


def get_gitignore():
    return """new-ip
old-ip
hostname.txt
"""


def bootstrap_repository():
    """To create the repository"""
    print("Bootstrapping repository")
    if (REPO_PATH / '.git').is_dir():
        if is_yes('Repository already exists do you want to delete it'):
            shutil.rmtree(REPO_PATH)
        else:
            print("Aborting bootstrap")
            exit(1)
    REPO_PATH.mkdir(exist_ok=True, parents=True)
    subprocess.run(['git', 'init'], check=True, cwd=REPO_PATH)
    (REPO_PATH / '.gitignore').write_text(get_gitignore())
    subprocess.run(['git', 'add', '.gitignore'], check=True, cwd=REPO_PATH)
    remote_url = get_remote()
    subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True, cwd=REPO_PATH)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True,
                   cwd=REPO_PATH)
    subprocess.run(['git', 'push', 'origin', 'master'],
                   check=True,
                   cwd=REPO_PATH)
    print(f"Repository bootstrapped. You can now add new hosts to the repository with {ADD_HOST_COMMAND}.")


def is_yes(message):
    if ASSUME_YES:
        return True
    if not message.endswith('?'):
        message = message + ' (y/n)? '
    while True:
        res = input(message) == 'y'
        if res == 'y' or res == 'yes':
            return True
        elif res == 'n' or 'no':
            return False
        else:
            print(f'"{res}" is not "y" or "n"')


def get_remote():
    if not DEFAULT_REMOTE:
        return input("Please type the remote repository url (ssh): ")
    else:
        return DEFAULT_REMOTE


if __name__ == '__main__':
    # bootstrap_repository()
    config_host()
