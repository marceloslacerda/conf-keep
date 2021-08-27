from confkeep.confkeep_commands import CKWrapper, settings
import pathlib
import unittest
import subprocess
import shutil

module_dir = pathlib.Path(__file__).parent


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings.REMOTE = pathlib.Path("repo-origin").absolute()
        settings.REPO_PATH = pathlib.Path("repo-path").absolute()
        settings.ASSUME_YES = True
        settings.IGNORE_SYNC_ERRORS = True
        settings.MONITORED_PATH = pathlib.Path("/etc")

    def tearDown(self):
        shutil.rmtree(settings.REMOTE, ignore_errors=True)
        shutil.rmtree(settings.REPO_PATH, ignore_errors=True)

    def setUp(self):
        shutil.rmtree(settings.REMOTE, ignore_errors=True)
        settings.REMOTE.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=settings.REMOTE)
        self.ckwrapper = CKWrapper()

    def test_bootstrap(self):
        self.ckwrapper.bootstrap_repository()

    def test_config_host(self):
        self.ckwrapper.config_host()

    def test_track_dir(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()

    def test_watchdog(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()
        self.ckwrapper.watchdog()

    def test_install_cron(self):
        self.ckwrapper.install_cron()


if __name__ == "__main__":
    unittest.main()
