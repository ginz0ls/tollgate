import unittest

from tollgate_analysis import specdoc

SPEC = """# Spec

## Fette previste

1. Prima fetta: il nucleo
2. Seconda fetta
3. Terza fetta

## Tane di coniglio

Niente.
"""


class SlicesTest(unittest.TestCase):
    def test_slices_counts_numbered_items(self):
        self.assertEqual(specdoc.slices(SPEC), 3)

    def test_no_section_is_one(self):
        self.assertEqual(specdoc.slices("# Spec\n\n## Altro\n\n1. a\n2. b\n"), 1)

    def test_section_without_items_is_one(self):
        self.assertEqual(specdoc.slices("## Fette previste\n\nSolo prosa.\n\n## Altro\n1. a\n"), 1)

    def test_items_inside_fence_ignored(self):
        text = "## Fette previste\n1. Vera\n```\n2. finta\n3. finta\n```\n\n## Altro\n4. fuori\n"
        self.assertEqual(specdoc.slices(text), 1)
        self.assertEqual(specdoc.slice_titles(text), ["Vera"])

    def test_heading_in_fence_does_not_end_section(self):
        text = "## Fette previste\n1. a\n```\n## Finta\n```\n2. b\n"
        self.assertEqual(specdoc.slices(text), 2)

    def test_slice_titles(self):
        self.assertEqual(specdoc.slice_titles(SPEC),
                         ["Prima fetta: il nucleo", "Seconda fetta", "Terza fetta"])
        self.assertEqual(specdoc.slice_titles("# Spec\n"), [])


class PitchTest(unittest.TestCase):
    def test_pitch_problems(self):
        both = "## Tane di coniglio\nx\n\n## Cosa non fare\ny\n"
        self.assertEqual(specdoc.pitch_problems(both), [])
        only_rabbit = specdoc.pitch_problems("## Tane di coniglio\nx\n")
        self.assertEqual(only_rabbit, ["manca la sezione «## Cosa non fare» (spec L2, 6.2)"])
        self.assertEqual(len(specdoc.pitch_problems("# Spec\n")), 2)

    def test_section_in_fence_does_not_count(self):
        text = "## Tane di coniglio\n```\n## Cosa non fare\n```\n"
        self.assertEqual(len(specdoc.pitch_problems(text)), 1)


if __name__ == "__main__":
    unittest.main()
