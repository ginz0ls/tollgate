import unittest

import ai
from ai import summary


class _Contenuto:
    text = "riassunto"


class _Risposta:
    content = [_Contenuto()]


class _Messaggi:
    def __init__(self):
        self.chiamate = []

    def create(self, **kwargs):
        self.chiamate.append(kwargs)
        return _Risposta()


class _Client:
    def __init__(self):
        self.messages = _Messaggi()


class SmokeTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(ai.__version__, "0.0.1")

    def test_riassumi_passa_il_modello_scelto_dal_chiamante(self):
        client = _Client()
        self.assertEqual(summary.riassumi(client, "un testo", "modello-di-prova"), "riassunto")
        self.assertEqual(client.messages.chiamate[0]["model"], "modello-di-prova")


if __name__ == "__main__":
    unittest.main()
