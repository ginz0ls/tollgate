import unittest
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "web" / "index.html"


class PageParser(HTMLParser):
    """Raccoglie i moduli, i campi e i pulsanti della pagina."""

    def __init__(self):
        super().__init__()
        self.forms = []
        self.fields = []
        self.buttons = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.forms.append(attrs)
        elif tag == "input":
            self.fields.append(attrs)
        elif tag == "button":
            self.buttons.append(attrs)


def parse_page():
    parser = PageParser()
    parser.feed(PAGE.read_text(encoding="utf-8"))
    return parser


class PageTest(unittest.TestCase):
    def test_form_has_one_field_and_a_submit_button(self):
        page = parse_page()
        self.assertEqual(len(page.forms), 1)
        self.assertEqual([f.get("name") for f in page.fields], ["titolo"])
        self.assertIn("submit", [b.get("type") for b in page.buttons])


if __name__ == "__main__":
    unittest.main()
