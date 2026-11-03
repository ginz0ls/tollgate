import tomllib
import unittest

from tollgate_analysis import tomlout


class TomlOutTest(unittest.TestCase):
    def test_round_trip(self):
        d = {
            "agent": 'a "citato" \\ barra\na capo\ttab \x7f del è à',
            "flag": True,
            "off": False,
            "empty": [],
            "paths": ["src/ai/**", 'x"y'],
            "commands": {"lint:fix": "ruff --fix", "test": "pytest"},
            "none_commands": {},
            "ctl": "\x00\x01\x1f",
        }
        out = tomlout.table("profiles.ai", d)
        self.assertEqual(tomllib.loads(out)["profiles"]["ai"], d)

    def test_header_quotes_non_bare_name_parts(self):
        out = tomlout.table("profiles.a b", {"k": "v"})
        self.assertEqual(tomllib.loads(out), {"profiles": {"a b": {"k": "v"}}})

    def test_rejects_other_types(self):
        for bad in (1, 1.5, None, [1, 2], {"a": 1}, ["a", None], (1,)):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                tomlout.table("t", {"k": bad})
        with self.assertRaises(TypeError):
            tomlout.table("t", {1: "x"})


if __name__ == "__main__":
    unittest.main()
