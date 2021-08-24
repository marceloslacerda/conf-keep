from confkeep.settings import REMOTE
from confkeep.confkeep import bootstrap_repository, config_host, track_dir, watchdog
import pathlib
import unittest
import subprocess


class MyTestCase(unittest.TestCase):
    def test_something(self):
        subprocess.run(["rm", "-rf", str(REMOTE)])
        REMOTE.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=REMOTE)
        bootstrap_repository()
        config_host()
        track_dir(pathlib.Path("/etc"))
        watchdog()


if __name__ == "__main__":
    unittest.main()
