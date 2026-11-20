import unittest

from ai.client import MODEL, build_request


class ClientTest(unittest.TestCase):
    def test_request_names_the_model(self):
        self.assertEqual(build_request("ciao")["model"], MODEL)


if __name__ == "__main__":
    unittest.main()
