import unittest
import sys
import os

from unittest.mock import patch  # noqa


class TestAppWorks(unittest.TestCase):
    def setUp(self):
        sys.path.append(os.getcwd())

    def test_tests_run(self):
        assert True is True

    # @patch("app.boto3")
    # def test_app_imports(self, boto_mock):
    #     try:
    #         import app  # noqa:F401
    #     except ModuleNotFoundError:
    #         raise
    #     finally:
    #         print("Module is importable...")
