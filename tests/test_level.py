import unittest

from tollgate_analysis.level import FileChange, diff_level, labels_level, max_level, next_level

KW = dict(sensitive_paths=["**/migrations/**", "**/auth/**"], l0_max_files=2,
          l0_max_lines=50, l0_max_bytes=4000)


class LevelTest(unittest.TestCase):
    def test_small_diff_is_l0(self):
        ch = [FileChange("src/a.py", 10, 2)]
        self.assertEqual(diff_level(ch, diff_bytes=500, **KW), "L0")
        self.assertEqual(diff_level([], diff_bytes=0, **KW), "L0")

    def test_thresholds(self):
        self.assertEqual(diff_level([FileChange(f"f{i}", 1, 0) for i in range(3)],
                                    diff_bytes=10, **KW), "L1")
        self.assertEqual(diff_level([FileChange("a", 40, 11)], diff_bytes=10, **KW), "L1")
        self.assertEqual(diff_level([FileChange("a", 1, 0)], diff_bytes=4001, **KW), "L1")

    def test_binary_is_not_l0(self):
        self.assertEqual(diff_level([FileChange("img.png", 0, 0, binary=True)],
                                    diff_bytes=10, **KW), "L1")

    def test_sensitive_is_l2(self):
        self.assertEqual(diff_level([FileChange("db/migrations/1.sql", 1, 0)],
                                    diff_bytes=10, **KW), "L2")

    def test_labels_and_max(self):
        self.assertEqual(labels_level(["bug", "security"], ["security"]), "L2")
        self.assertEqual(labels_level(["bug"], ["security"]), "L0")
        self.assertEqual(max_level("L0", "L2", "L1"), "L2")

    def test_cap_holds_until_new_sensitive_path(self):
        self.assertEqual(next_level(current="L1", computed="L2", cap="L1",
                                    cap_paths=["src/auth/a.py"], sensitive_now=["src/auth/a.py"]),
                         "L1")
        self.assertEqual(next_level(current="L1", computed="L2", cap="L1",
                                    cap_paths=["src/auth/a.py"],
                                    sensitive_now=["src/auth/a.py", "src/auth/b.py"]), "L2")
        self.assertEqual(next_level(current="L2", computed="L0", cap=None, cap_paths=[],
                                    sensitive_now=[]), "L2")


if __name__ == "__main__":
    unittest.main()
