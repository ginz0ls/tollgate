import unittest

import app
from app import main


class SmokeTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(app.__version__, "0.0.1")

    def test_saluta(self):
        self.assertEqual(main.saluta("prova"), "Ciao, prova")


if __name__ == "__main__":
    unittest.main()
