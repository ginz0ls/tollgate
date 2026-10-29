import unittest

import src


class SmokeTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(src.__version__, "0.0.1")


if __name__ == "__main__":
    unittest.main()
