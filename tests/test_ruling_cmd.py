"""Comando `ruling add` (C1, Task 5): una decisione presa al posto dell'utente, nello stato locale."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.flowkit import FlowLab
from tollgate_flow import ruling_cmd

TEXT = "cosa: usa la copia\nperché: l'utente non c'è\ncosto: nessuno"


class ParseTextTest(unittest.TestCase):
    def test_parse_text(self):
        fields, problems = ruling_cmd.parse_text(TEXT)
        self.assertEqual(problems, [])
        self.assertEqual(fields, {"what": "usa la copia", "why": "l'utente non c'è",
                                  "cost": "nessuno"})

    def test_field_on_two_lines_is_joined(self):
        fields, _ = ruling_cmd.parse_text("cosa: usa\nla copia\nperché: p\ncosto: c")
        self.assertEqual(fields["what"], "usa la copia")

    def test_perche_without_accent_and_any_case(self):
        fields, problems = ruling_cmd.parse_text("Cosa: a\nPERCHE: b\nCosto: c")
        self.assertEqual((fields, problems), ({"what": "a", "why": "b", "cost": "c"}, []))
        fields, _ = ruling_cmd.parse_text("COSA: a\nPERCHÉ: b\ncosto: c")
        self.assertEqual(fields["why"], "b")

    def test_perche_with_grave_accent_or_decomposed_e(self):
        """F2 e riga 17: `perchè:` (grafia comune) e una «é» in forma NFD valgono `perché:`."""
        for label in ("perchè", "Perchè", "PERCHÈ", "perche\u0301", "Perche\u0301", "perche\u0300"):
            with self.subTest(label=label):
                fields, problems = ruling_cmd.parse_text(f"cosa: a\n{label}: b\ncosto: c")
                self.assertEqual((fields, problems),
                                 ({"what": "a", "why": "b", "cost": "c"}, []))

    def test_other_label_stays_inside_the_open_field(self):
        fields, problems = ruling_cmd.parse_text("cosa: usa la copia\nNota: vedi sopra\n"
                                                 "perché: p\ncosto: c")
        self.assertEqual(problems, [])
        self.assertEqual(fields["what"], "usa la copia Nota: vedi sopra")

    def test_missing_repeated_or_leading_text_are_problems(self):
        for text in ("intro\naltra riga\ncosa: a\nperché: p\ncosto: c",
                     "cosa: a\nperché: b",
                     "cosa: a\ncosa: b\nperché: p\ncosto: c",
                     "chi: x\ncosa: a\nperché: p\ncosto: c", "cosa: a\nperché:\ncosto: c"):
            with self.subTest(text=text):
                fields, problems = ruling_cmd.parse_text(text)
                self.assertIsNone(fields)
                self.assertTrue(problems)


class RulingCase(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab(issue=7, phase="plan")
        self.addCleanup(self.fl.close)
        self.fl.register_plan(2)

    def add(self, text=TEXT, cwd=None, **kw):
        kw.setdefault("task", None)
        kw.setdefault("by", "agent")
        return ruling_cmd.add(self.fl.ts.state, cwd or self.fl.wt, text, **kw)

    def rulings(self):
        return [(r["work"], json.loads(r["data"])) for r in self.fl.conn.execute(
            "SELECT work, data FROM events WHERE type = 'ruling' ORDER BY seq")]


class AddTest(RulingCase):
    def test_add_records_event(self):
        r = self.add()
        self.assertEqual(r.code, ruling_cmd.OK)
        seq = self.fl.conn.execute("SELECT MAX(seq) FROM events WHERE type = 'ruling'"
                                   ).fetchone()[0]
        self.assertEqual(r.lines, [f"ruling registrata (evento {seq})"])
        self.assertEqual(self.rulings(),
                         [(self.fl.work, {"what": "usa la copia", "why": "l'utente non c'è",
                                          "cost": "nessuno", "by": "agent", "task": None})])

    def test_add_with_task(self):
        self.assertEqual(self.add(task=2, by="user").code, ruling_cmd.OK)
        data = self.rulings()[0][1]
        self.assertEqual((data["task"], data["by"]), (2, "user"))
        r = self.add(task=9)
        self.assertEqual(r.code, ruling_cmd.REFUSED)
        self.assertIn("task 9 inesistente", r.lines[0])
        self.assertEqual(len(self.rulings()), 1)

    def test_add_without_work_refused(self):
        outside = Path(tempfile.mkdtemp(prefix="tollgate-ruling-"))
        self.addCleanup(outside.rmdir)
        r = self.add(cwd=outside)
        self.assertEqual(r.code, ruling_cmd.REFUSED)
        self.assertIn("nessun lavoro attivo per questa cartella", r.lines[0])
        self.assertEqual(self.rulings(), [])

    def test_add_rejects_empty_and_long_text(self):
        for text in ("cosa: a\nperché:   \ncosto: c", "cosa: a\nperché: b"):
            with self.subTest(text=text):
                self.assertEqual(self.add(text).code, ruling_cmd.REFUSED)
        long = f"cosa: {'x' * (ruling_cmd.RULING_TEXT_MAX + 1)}\nperché: p\ncosto: c"
        r = self.add(long)
        self.assertEqual(r.code, ruling_cmd.REFUSED)
        self.assertIn(str(ruling_cmd.RULING_TEXT_MAX), "\n".join(r.lines))
        ok = f"cosa: {'x' * ruling_cmd.RULING_TEXT_MAX}\nperché: p\ncosto: c"
        self.assertEqual(self.add(ok).code, ruling_cmd.OK)
        self.assertEqual(len(self.rulings()), 1)

    def test_add_rejects_unknown_by(self):
        self.assertEqual(self.add(by="modello").code, ruling_cmd.REFUSED)
        self.assertEqual(self.rulings(), [])


class CommandTest(unittest.TestCase):
    def test_command_heredoc(self):
        out = ruling_cmd.command("python3 '/p/bin/tollgate'", 3)
        lines = out.splitlines()
        self.assertEqual(lines[0], f"python3 '/p/bin/tollgate' ruling add --task 3 "
                                   f"<<'{ruling_cmd.HEREDOC_END}'")
        self.assertEqual(lines[-1], ruling_cmd.HEREDOC_END)
        self.assertEqual(ruling_cmd.command("p", None).splitlines()[0],
                         f"p ruling add <<'{ruling_cmd.HEREDOC_END}'")
        fields, problems = ruling_cmd.parse_text("\n".join(lines[1:-1]))
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
