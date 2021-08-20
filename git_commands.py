import subprocess

from settings import REPO_PATH


def git_command(*args, get_stdout=False):
    ls = ["git"]
    ls.extend(args)
    if not get_stdout:
        subprocess.run([str(x) for x in ls], check=True, cwd=REPO_PATH)
    else:
        cp = subprocess.run([str(x) for x in ls], check=True, cwd=REPO_PATH, stdout=subprocess.PIPE)
        return cp.stdout


def git_commit_am(message):
    git_command("commit", "-m", message)


def git_push(branch):
    git_command("push", "origin", branch)


def git_add(file):
    git_command("add", file)
