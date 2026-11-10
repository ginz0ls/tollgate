import unittest

from server import app


class SmokeTest(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(app.dispatch("GET", "/hello"), (200, "text/plain; charset=utf-8", "ciao"))

    def test_unknown_route(self):
        self.assertEqual(app.dispatch("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
