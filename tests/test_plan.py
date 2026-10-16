import unittest

from tollgate_analysis import plan

SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope",
            "Punti di arresto", "Rischi"]


def make(must_have="M1. Somma corretta — test: tests.test_a::test_sum", files=None,
         extra="", drop=None):
    files = files or ["- Create: `src/a.py`", "- Test: `tests/test_a.py:10-20`"]
    out = ["# Piano", ""]
    for s in SECTIONS:
        if s == drop:
            continue
        out.append(f"## {s}")
        if s == "Must-have":
            out.append(must_have)
        out.append("")
    out += ["### Task 1: Somma", "", "**Files:**", *files, "Must-have: M1", "",
            "```markdown", "## Finta sezione in un blocco di codice", "- Create: `x/finto.py`",
            "```", extra]
    return "\n".join(out)


def check(text, level="L1", profiles=None, max_scope=30):
    return plan.check_plan(text, required_sections=SECTIONS, max_scope_files=max_scope,
                           must_have_tests=True, level=level, profiles=profiles or {},
                           active_always=[])


class PlanCheckTest(unittest.TestCase):
    def test_complete_plan(self):
        r = check(make())
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.scope, ["src/a.py", "tests/test_a.py"])
        self.assertEqual(r.must_haves[0].tests, ["tests.test_a::test_sum"])
        self.assertEqual([t.number for t in r.tasks], [1])

    def test_missing_section(self):
        r = check(make(drop="Rischi"))
        self.assertFalse(r.ok)
        self.assertIn("## Rischi", " ".join(r.problems))

    def test_pattern_or_dir_rejected(self):
        for bad in ["- Modify: `src/*.py`", "- Create: `src/nuova/`"]:
            with self.subTest(bad=bad):
                self.assertFalse(check(make(files=[bad])).ok)

    def test_must_have_without_test(self):
        self.assertFalse(check(make(must_have="M1. Somma corretta")).ok)
        self.assertTrue(check(make(must_have="M1. Somma corretta"), level="L0").ok)

    def test_manual_test_allowed(self):
        self.assertTrue(check(make(must_have="M1. Colore giusto — test: manuale")).ok)

    def test_brackets_in_scope_are_literal_names(self):
        r = check(make(files=["- Create: `app/[id]/page.tsx`"]))
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.scope, ["app/[id]/page.tsx"])

    def test_question_mark_in_scope_rejected(self):
        self.assertFalse(check(make(files=["- Create: `src/a?.py`"])).ok)

    def test_too_many_files(self):
        files = [f"- Create: `src/f{i}.py`" for i in range(4)]
        self.assertFalse(check(make(files=files), max_scope=3).ok)

    def test_unknown_must_have_reference(self):
        text = make().replace("Must-have: M1", "Must-have: M1, M9")
        self.assertFalse(check(text).ok)

    def test_more_than_three_skills_is_warning(self):
        prof = {"api": {"kind": "vertical", "paths": ["src/**"], "skills": ["a", "b", "c", "d"],
                        "plan_sections": []}}
        r = check(make(), profiles=prof)
        self.assertTrue(r.ok)
        self.assertTrue(any("4 skill" in w for w in r.warnings))

    def test_profile_sections_required(self):
        prof = {"api": {"kind": "vertical", "paths": ["src/**"], "skills": [],
                        "plan_sections": ["Contratti"]}}
        self.assertFalse(check(make(), profiles=prof).ok)

    def test_no_tasks(self):
        self.assertFalse(check("\n".join(f"## {s}" for s in SECTIONS)).ok)


PLAN = """# Piano

## Must-have
M1. Uno — test: a::b

### Task 1: Primo

- Create: `a.py`
```markdown
### Task 9: finto
```
riga dopo il recinto

### Task 2: Secondo

- Modify: `b.py`

## Scope
fine
"""


class TaskTextTest(unittest.TestCase):
    def test_task_text_stops_at_next_task(self):
        t = plan.task_text(PLAN, 1)
        self.assertTrue(t.startswith("### Task 1: Primo"))
        self.assertIn("riga dopo il recinto", t)
        self.assertNotIn("### Task 2", t)
        t2 = plan.task_text(PLAN, 2)
        self.assertIn("Modify: `b.py`", t2)
        self.assertNotIn("## Scope", t2)
        self.assertIsNone(plan.task_text(PLAN, 3))

    def test_task_text_ignores_headings_in_fences(self):
        t = plan.task_text(PLAN, 1)
        self.assertIn("### Task 9: finto", t)
        self.assertIsNone(plan.task_text(PLAN, 9))

    def test_multiple_files_on_one_line(self):
        for line in ["- Create: a.py, b.py", "- Modify: `a.py`, `b.py`",
                     "- Create: a.py (nuovo, da scrivere), b.py"]:
            with self.subTest(line=line):
                r = check(make(files=[line, "- Test: `tests/test_a.py`"]))
                self.assertEqual(r.scope, ["a.py", "b.py", "tests/test_a.py"])

    def test_tilde_and_long_fences(self):
        for opener, closer in [("~~~", "~~~"), ("````", "````"), ("~~~~", "~~~~~")]:
            with self.subTest(opener=opener):
                text = make(extra=f"{opener}\n- Create: `x/finto2.py`\n```\n- Create: `x/finto3.py`"
                                  f"\n{closer}\n### Task 5: finto\n")
                r = check(text)
                self.assertEqual(r.scope, ["src/a.py", "tests/test_a.py"])
                self.assertEqual([t.number for t in r.tasks], [1, 5])

    def test_bold_must_have(self):
        r = check(make(must_have="**M1.** Somma corretta — test: tests.test_a::test_sum"))
        self.assertTrue(r.ok, r.problems)
        self.assertEqual([m.id for m in r.must_haves], ["M1"])
        self.assertEqual(r.must_haves[0].tests, ["tests.test_a::test_sum"])

    def test_duplicate_must_have_and_task_ids(self):
        r = check(make(must_have="M1. Uno — test: manuale\nM1. Due — test: manuale"))
        self.assertIn("M1 duplicato", r.problems)
        r = check(make(extra="### Task 1: Ancora\n- Create: `z.py`"))
        self.assertTrue(any("task 1 duplicato" in p for p in r.problems), r.problems)

    def test_existing_cases_unchanged(self):
        self.assertTrue(check(make()).ok)


if __name__ == "__main__":
    unittest.main()
