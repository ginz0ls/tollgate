import unittest

from tollgate_analysis import size
from tollgate_core.git import Change


def ch(path, added, removed):
    return Change("M", path, None, added, removed, False)


class TaskLinesTest(unittest.TestCase):
    def test_sums_added_and_removed(self):
        self.assertEqual(size.task_lines([ch("a.py", 10, 5), ch("b.py", 3, 0)], set()), 18)

    def test_lockfiles_and_generated_excluded(self):
        changes = [ch("a.py", 10, 0), ch("web/package-lock.json", 900, 100),
                   ch("web/dist/app.js", 500, 0), ch("x/a.min.js", 50, 0),
                   ch("x/__snapshots__/a.snap", 70, 0), ch("x/api.generated.ts", 20, 0)]
        self.assertEqual(size.task_lines(changes, {"package-lock.json"}), 10)

    def test_generated_patterns(self):
        self.assertEqual(len(size.GENERATED), 4)


if __name__ == "__main__":
    unittest.main()
