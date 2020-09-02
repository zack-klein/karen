import unittest

from unittest.mock import patch  # noqa


class TestAppWorks(unittest.TestCase):
    def setUp(self):
        pass

    def test_tests_run(self):
        assert True is True

    # @patch("app.utils")
    # def test_app_imports(self, utils_mock):
    #     try:
    #         import app  # noqa:F401
    #         print(utils_mock)
    #     except ModuleNotFoundError:
    #         raise
    #     finally:
    #         print("Module is importable...")
