import os
import pathlib


def get_path_environ(variable, default):
    return (
        pathlib.Path(os.environ[variable]).absolute()
        if variable in os.environ
        else default
    )
