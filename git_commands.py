import subprocess

from settings import REPO_PATH


def git_command(*args):
    ls = ["git"]
    ls.extend(args)
    subprocess.run([str(x) for x in ls], check=True, cwd=REPO_PATH)


def git_commit_am(message):
    git_command("commit", "-m", message)


def git_push(branch):
    git_command("push", "origin", branch)


def git_add(file):
    git_command("add", file)
