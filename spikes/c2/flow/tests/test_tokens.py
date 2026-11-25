import os
import unittest
from unittest import mock

from app.auth import tokens


class TokensTest(unittest.TestCase):
    def setUp(self):
        # la chiave di firma si legge dalla variabile d'ambiente: nei test vale un valore finto
        patcher = mock.patch.dict(os.environ, {"C2_PROVA_SECRET": "PROVA-123"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.secret = os.environ["C2_PROVA_SECRET"].encode()

    def test_valid_token_returns_user(self):
        token = tokens.sign("anna", 2000, self.secret)
        self.assertEqual(tokens.verify(token, self.secret, now=1000), "anna")

    def test_altered_token_is_rejected(self):
        token = tokens.sign("anna", 2000, self.secret)
        user, expires_at, signature = token.split(".")
        self.assertIsNone(tokens.verify(f"bruno.{expires_at}.{signature}", self.secret, now=1000))
        self.assertIsNone(tokens.verify(f"{user}.9999.{signature}", self.secret, now=1000))
        self.assertIsNone(tokens.verify("non-un-token", self.secret, now=1000))


if __name__ == "__main__":
    unittest.main()
