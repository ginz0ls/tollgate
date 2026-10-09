import unittest

from tollgate_analysis import profiles

PROFILES = {
    "web": {"kind": "vertical", "paths": ["web/**"], "skills": ["ui-ux-pro-max"],
            "min_level": "L0", "plan_sections": []},
    "admin": {"kind": "vertical", "paths": ["web/admin/**"], "skills": ["a", "b"],
              "min_level": "L1", "plan_sections": []},
    "api": {"kind": "vertical", "paths": ["api/**"], "skills": ["c", "d"],
            "min_level": "L2", "plan_sections": ["Contratti"]},
    "a11y": {"kind": "cross", "paths": ["web/**"], "skills": ["x"], "min_level": "L0",
             "plan_sections": []},
}


class ProfilesTest(unittest.TestCase):
    def test_most_specific_wins(self):
        self.assertEqual(profiles.vertical_for("web/admin/x.ts", PROFILES), "admin")
        self.assertEqual(profiles.vertical_for("web/x.ts", PROFILES), "web")
        self.assertIsNone(profiles.vertical_for("lib/x.ts", PROFILES))

    def test_tie_first_declared(self):
        p = {"uno": {"kind": "vertical", "paths": ["src/**"]},
             "due": {"kind": "vertical", "paths": ["src/**"]}}
        self.assertEqual(profiles.vertical_for("src/a", p), "uno")

    def test_active_and_skills(self):
        self.assertEqual(profiles.active_profiles(["web/a.ts"], PROFILES, ["api"]),
                         ["web", "api", "a11y"])
        self.assertEqual(profiles.task_skills(["web/admin/a.ts", "api/b.py"], PROFILES),
                         ["a", "b", "c", "d"])
        self.assertEqual(profiles.min_level(["web", "admin"], PROFILES), "L1")


if __name__ == "__main__":
    unittest.main()
