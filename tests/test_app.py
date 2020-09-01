import unittest
import sys
import os


class TestAppWorks(unittest.TestCase):
    def setUp(self):
        pass

    def test_tests_run(self):
        assert True is True

    def test_app_imports(self):
        sys.path.append(os.getcwd())
        import app  # noqa:F401
