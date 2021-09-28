import os

import confkeep.confkeep_commands
from confkeep.confkeep_commands import CKWrapper, settings
import pathlib
import unittest
import subprocess
import shutil

module_dir = pathlib.Path(__file__).parent


class MyTestCase(unittest.TestCase):
    test_dir_parent = pathlib.Path("test-dir").absolute()
    test_single_file = pathlib.Path("single-file").absolute()
    test_child = (test_dir_parent / "child").absolute()

    @classmethod
    def setUpClass(cls):
        settings.REMOTE = pathlib.Path("repo-origin").absolute()
        settings.REPO_PATH = pathlib.Path("repo-path").absolute()
        settings.ASSUME_YES = True
        settings.IGNORE_SYNC_ERRORS = True
        cls.tearDownClass()

    def tearDown(self):
        shutil.rmtree(settings.REMOTE, ignore_errors=True)
        shutil.rmtree(settings.REPO_PATH, ignore_errors=True)
        shutil.rmtree(self.test_dir_parent, ignore_errors=True)
        try:
            os.remove(self.test_single_file)
        except FileNotFoundError:
            pass

    def setUp(self):
        settings.ASSUME_YES = True
        settings.ASSUME_NO = False
        self.tearDown()
        settings.REMOTE.mkdir()
        subprocess.run(["git", "init", "--bare"], cwd=settings.REMOTE)
        self.ckwrapper = CKWrapper()
        settings.MONITORED_PATH = self.test_dir_parent
        self.test_dir_parent.mkdir()
        self.test_child.write_text('first text child')
        self.test_single_file.write_text('first text single')

    def test_bootstrap(self):
        self.ckwrapper.bootstrap_repository()
        self.assertTrue(settings.REPO_PATH.is_dir())
        self.assertTrue((settings.REMOTE / 'HEAD').is_file())
        #todo test push

    def test_bootstrap_repo_already_exists(self):
        """"Error when bootstrapping twice"""
        self.ckwrapper.bootstrap_repository()
        with self.assertRaises(confkeep.confkeep_commands.ConfKeepError):
            self.ckwrapper.bootstrap_repository()

    def test_config_host(self):
        self.ckwrapper.config_host()
        self.assertTrue(self.ckwrapper.work_path.is_dir())
        self.assertTrue(self.ckwrapper.hostname_path.is_file())
        self.assertEqual(settings.HOST_NAME, self.ckwrapper.hostname_path.read_text())
        # todo test push

    def test_config_host_error_on_configuration_exists(self):
        """Error when configuration already exists and assume yes is not set"""
        self.ckwrapper.config_host()
        with self.assertRaises(confkeep.confkeep_commands.ConfKeepError):
            settings.ASSUME_YES = False
            settings.ASSUME_NO = True
            self.ckwrapper.config_host()

    def test_track_dir(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()
        self.assertIn(str(self.test_dir_parent), self.ckwrapper.tracked_file_path.read_text())
        settings.MONITORED_PATH = self.test_single_file
        self.ckwrapper.track_dir()
        self.assertIn(str(self.test_single_file), self.ckwrapper.tracked_file_path.read_text())

    def test_track_dir_no_absolute(self):
        """Error when tracked dir is not absolute"""
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        settings.MONITORED_PATH = self.test_child.relative_to(self.test_dir_parent)
        with self.assertRaises(AttributeError):
            self.ckwrapper.track_dir()

    def test_track_dir_no_duplicate(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()
        self.ckwrapper.track_dir()
        tracked = self.ckwrapper.tracked_file_path.read_text().split('\n')
        count = 0
        for path in tracked:
            if str(self.test_dir_parent) in path:
                count += 1
        self.assertEqual(count, 1)

    def test_watchdog_no_track(self):
        """Error when there's nothing to track"""
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        with self.assertRaises(confkeep.confkeep_commands.ConfKeepError):
            self.ckwrapper.watchdog()

    def test_watchdog_sync_dir(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()
        parent = self.ckwrapper.work_path / self.test_dir_parent.name
        child = self.ckwrapper.work_path / parent.name / self.test_child.name
        self.assertFalse(parent.is_dir())
        self.ckwrapper.watchdog()
        self.assertTrue(parent.is_dir())
        self.assertTrue(child.is_file())
        self.assertEqual(self.test_child.read_text(), child.read_text())
        self.test_child.write_text('second text child')
        self.ckwrapper.watchdog()
        self.assertEqual(self.test_child.read_text(), child.read_text())

    def test_watchdog_single_file(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        settings.MONITORED_PATH = self.test_single_file
        self.ckwrapper.track_dir()
        single = self.ckwrapper.work_path / self.test_single_file.name
        self.assertFalse(single.is_file())
        self.ckwrapper.watchdog()
        self.assertTrue(single.is_file())
        self.assertEqual(self.test_single_file.read_text(), single.read_text())
        self.test_single_file.write_text('second text single')
        self.ckwrapper.watchdog()
        self.assertEqual(self.test_single_file.read_text(), single.read_text())

    def test_multiple_tracked(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()
        parent = self.ckwrapper.work_path / self.test_dir_parent.name
        child = self.ckwrapper.work_path / parent.name / self.test_child.name
        single = self.ckwrapper.work_path / self.test_single_file.name
        settings.MONITORED_PATH = self.test_single_file
        self.ckwrapper.track_dir()
        self.ckwrapper.watchdog()
        self.assertTrue(single.is_file())
        self.assertEqual(self.test_single_file.read_text(), single.read_text())
        self.assertEqual(self.test_child.read_text(), child.read_text())
        self.test_child.write_text('second text child')
        self.test_single_file.write_text('second text single')
        self.ckwrapper.watchdog()
        self.assertEqual(self.test_single_file.read_text(), single.read_text())
        self.assertEqual(self.test_child.read_text(), child.read_text())

    def test_watchdog_delete(self):
        self.ckwrapper.bootstrap_repository()
        self.ckwrapper.config_host()
        self.ckwrapper.track_dir()
        parent = self.ckwrapper.work_path / self.test_dir_parent.name
        child = self.ckwrapper.work_path / parent.name / self.test_child.name
        single = self.ckwrapper.work_path / self.test_single_file.name
        settings.MONITORED_PATH = self.test_single_file
        self.ckwrapper.track_dir()
        self.ckwrapper.watchdog()
        self.assertTrue(parent.is_dir())
        self.assertTrue(child.is_file())
        self.assertTrue(single.is_file())
        shutil.rmtree(self.test_dir_parent)
        os.remove(self.test_single_file)
        self.ckwrapper.watchdog()
        self.assertFalse(parent.is_dir())
        self.assertFalse(child.is_file())
        self.assertFalse(single.is_file())

    def test_install_cron(self):
        self.ckwrapper.install_cron()



if __name__ == "__main__":
    unittest.main()
