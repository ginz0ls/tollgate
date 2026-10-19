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


class RoutingTest(unittest.TestCase):
    PROF = {
        "web": {"kind": "vertical", "paths": ["web/**"], "skills": ["ui-ux-pro-max"],
                "agent": "probe:implementer-frontend", "reviewer": "probe:reviewer-frontend",
                "cross": ["a11y"]},
        "api": {"kind": "vertical", "paths": ["api/**"], "skills": ["c"],
                "agent": "probe:implementer-backend", "reviewer": "probe:reviewer-backend"},
        "lib": {"kind": "vertical", "paths": ["lib/**"], "skills": ["l1", "l2", "l3", "l4"]},
        "a11y": {"kind": "cross", "paths": ["web/**"], "reviewer_skills": ["axe"]},
    }

    def test_single_vertical_uses_its_agents(self):
        r = profiles.task_routing(["web/a.tsx"], self.PROF)
        self.assertEqual((r.implementer, r.reviewer), ("probe:implementer-frontend",
                                                      "probe:reviewer-frontend"))
        self.assertEqual(r.skills, ["ui-ux-pro-max"])
        self.assertFalse(r.split_candidate)

    def test_different_agents_fall_back_and_split(self):
        r = profiles.task_routing(["web/a.tsx", "api/b.py"], self.PROF)
        self.assertEqual((r.implementer, r.reviewer),
                         (profiles.DEFAULT_IMPLEMENTER, profiles.DEFAULT_REVIEWER))
        self.assertEqual(r.skills, ["ui-ux-pro-max", "c"])
        self.assertTrue(r.split_candidate)

    def test_cross_reviewer_skills(self):
        r = profiles.task_routing(["web/a.tsx"], self.PROF)
        self.assertIn("axe", r.reviewer_skills)

    def test_skill_cap(self):
        r = profiles.task_routing(["lib/a.py"], self.PROF)
        self.assertEqual(r.skills, ["l1", "l2", "l3"])
        self.assertTrue(r.split_candidate)

    def test_no_profile_is_generic(self):
        r = profiles.task_routing(["x/a.py"], self.PROF)
        self.assertEqual((r.implementer, r.reviewer, r.skills, r.reviewer_skills,
                          r.split_candidate),
                         (profiles.DEFAULT_IMPLEMENTER, profiles.DEFAULT_REVIEWER, [], [], False))
        self.assertEqual(profiles.task_routing([], {}).implementer, profiles.DEFAULT_IMPLEMENTER)

    def test_single_declared_agent_among_verticals(self):
        prof = {"a": {"paths": ["a/**"], "agent": "p:x"}, "b": {"paths": ["b/**"]}}
        r = profiles.task_routing(["a/1", "b/2"], prof)
        self.assertEqual(r.implementer, "p:x")
        self.assertEqual(r.reviewer, profiles.DEFAULT_REVIEWER)
        self.assertFalse(r.split_candidate)


if __name__ == "__main__":
    unittest.main()


class RulesTest(unittest.TestCase):
    PROF = {
        "web": {"rules": ["R-WEB-1", "R-WEB-2"], "blocking_rules": ["R-WEB-1"],
                "final_specialist": "p:final-web"},
        "api": {"rules": ["R-API-1"], "blocking_rules": [], "final_specialist": "p:final-web"},
        "lib": {"final_specialist": ""},
    }

    def test_rules(self):
        names = ["web", "api", "lib", "ghost"]
        self.assertEqual(profiles.blocking_rules(names, self.PROF), {"R-WEB-1"})
        self.assertEqual(profiles.known_rules(names, self.PROF),
                         {"R-WEB-1", "R-WEB-2", "R-API-1"})
        self.assertEqual(profiles.known_rules([], self.PROF), set())

    def test_final_specialists_ordered_unique(self):
        self.assertEqual(profiles.final_specialists(["lib", "web", "api"], self.PROF),
                         ["p:final-web"])
        self.assertEqual(profiles.final_specialists([], self.PROF), [])
