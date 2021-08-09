import pathlib
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
    print("Setting up host")
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
        print(
            f"Theres already a configuration directory for the host "
            f"{host_name}. Nothing to do.")
        exit(0)
    else:
        print("Creating a configuration directory for the host")
        subprocess.run(['git', 'checkout', '-b', host_name], check=True, cwd=REPO_PATH)
        work_path.mkdir()
    blank_path = (work_path / 'blank.txt')
    blank_path.touch()
    subprocess.run(['git', 'add', blank_path], check=True, cwd=REPO_PATH)
    subprocess.run(
        ['git', 'commit', '-m', f'Host {host_name} added to the repo'],
        check=True)
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
    if REPO_PATH.is_dir():
        yes = input('Repository already exists do you want to delete it(y/n)? ')
        if yes == 'y':
            REPO_PATH.rmdir()
        else:
            print("Aborting bootstrap")
            exit(1)
    subprocess.run(['git', 'init'], check=True, cwd=REPO_PATH)
    path = (REPO_PATH / '.gitignore')
    path.write_text(get_gitignore())
    subprocess.run(['git', 'add', path], check=True, cwd=REPO_PATH)
    remote_url = get_remote()
    subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True, cwd=REPO_PATH)
    subprocess.run(['git', 'commit', '-m', 'Initial commit', remote_url], check=True,
                   cwd=REPO_PATH)
    subprocess.run(['git', 'push', 'origin', 'master'],
                   check=True,
                   cwd=REPO_PATH)
    print(f"Repository bootstrapped. You can now add new hosts to the repository with {ADD_HOST_COMMAND}.")


def get_remote():
    return input("Please type the remote repository url (ssh): ")


if __name__ == '__main__':
    config_host()
