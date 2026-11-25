"""Sonda dello scan pre-flight di C2: due profili attivi con uno specialista finale ciascuno
(`database` e `security`). Si lancia DALLA COPIA `git archive` (mai dal repo vivo):

    cd <copia> && python3 -B -m unittest -v <percorso>/sonda_specialisti.py   (o: python3 -B <file>)

Usa `tests.test_finalreview.FinalCase` (FlowLab, stato temporaneo)."""
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path.cwd()))
from tests.hookkit import DEFAULT_TOML  # noqa: E402
from tests.test_finalreview import REVIEWER, FinalCase  # noqa: E402

TWO = DEFAULT_TOML + """
[profiles.database]
paths = ["/supabase/**"]
min_level = "L2"
final_specialist = "tollgate:final-database"
checklist = "CL-DATABASE"

[profiles.security]
paths = ["app/auth/**"]
min_level = "L2"
final_specialist = "tollgate:final-security"
checklist = "CL-SECURITY"
"""
FILES = {"supabase/migrations/1.sql": "create table t (id int);\n", "app/auth/x.py": "X = 1\n"}


class TwoSpecialists(FinalCase):
    def test_both_start_with_own_brief_and_checklist(self):
        self.lab(toml=TWO, level="L2", extra=FILES)
        r = self.prepare()
        db, sec = "tollgate:final-database", "tollgate:final-security"
        self.assertEqual([x.agent_type for x in r.launches], [REVIEWER, db, sec])
        self.assertEqual(json.loads(self.cycle()["reviewers"]), [REVIEWER, db, sec])
        names = [x.brief.name for x in r.launches]
        self.assertEqual(names, ["final-1.md", "final-1-database.md", "final-1-security.md"])
        general, bdb, bsec = (x.brief.read_text() for x in r.launches)
        self.assertIn("CL-DATABASE", general)
        self.assertIn("CL-SECURITY", general)
        self.assertIn("CL-DATABASE", bdb)
        self.assertNotIn("CL-SECURITY", bdb)
        self.assertIn("CL-SECURITY", bsec)
        self.assertNotIn("CL-DATABASE", bsec)

    def test_only_touched_profile_starts(self):
        self.lab(toml=TWO, level="L2", extra={"app/auth/x.py": "X = 1\n"})
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [REVIEWER, "tollgate:final-security"])

    def test_l1_none(self):
        self.lab(toml=TWO, extra=FILES)
        self.assertEqual([x.agent_type for x in self.prepare().launches], [REVIEWER])


if __name__ == "__main__":
    unittest.main(verbosity=2)
