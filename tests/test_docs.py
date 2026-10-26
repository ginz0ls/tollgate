"""La documentazione d'uso resta allineata al codice e alla spec (decisione 19 di P5)."""
import re
import unittest

from tests.helpers import ROOT

SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-10-08-tollgate-nucleo-design.md"
USO = ROOT / "docs" / "uso"
DOCS = [ROOT / "README.md", *sorted(USO.glob("*.md"))]
FRONTMATTER_KEY = re.compile(r'^(?P<key>[a-z-]+):\s*(?P<value>.*)$')
BOLD_ITEM = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\*\*(?P<title>.+?)\*\*")
LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)\)")


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    out = {}
    if lines and lines[0] == "---":
        for line in lines[1:]:
            if line == "---":
                break
            m = FRONTMATTER_KEY.match(line)
            if m:
                out[m["key"]] = m["value"].strip().strip('"')
    return out


def section(text, heading_prefix):
    """Le righe dal titolo che comincia per `heading_prefix` al titolo successivo (di qualunque livello)."""
    lines, out, inside = text.splitlines(), [], False
    for line in lines:
        if line.startswith("#"):
            if inside:
                break
            inside = line.startswith(heading_prefix)
            continue
        if inside:
            out.append(line)
    return out


def normalize(title):
    """Confronto dei titoli dei limiti: senza backtick, spazi compressi, senza punteggiatura finale
    (. ; :), senza distinzione di maiuscole (le voci di 17 cominciano con la minuscola)."""
    title = title.replace("`", "")
    title = re.sub(r"\s+", " ", title).strip().rstrip(".;:").strip()
    return title.casefold()


def spec_limit_titles():
    """Le voci in grassetto di tutti gli elenchi di 1.2 (dalla rev 26 comprendono anche le due voci di 17)."""
    text = SPEC.read_text(encoding="utf-8")
    titles = set()
    for line in section(text, "### 1.2"):
        m = BOLD_ITEM.match(line)
        if m:
            titles.add(normalize(m["title"]))
    return titles


def heading_slugs(path):
    """Gli ancoraggi che GitHub dà ai titoli: minuscole, senza punteggiatura, spazi in trattini."""
    slugs = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if m:
            slug = re.sub(r"[^\w\s-]", "", m[1].replace("`", "").lower())
            slugs.add(re.sub(r"\s", "-", slug))
    return slugs


class DocsTest(unittest.TestCase):
    def test_docs_exist(self):
        names = {"installazione", "comandi", "modalita", "limiti", "emergenze-e-aggiornamenti", "eval-e-ci"}
        self.assertEqual({p.stem for p in USO.glob("*.md")}, names)
        self.assertTrue((ROOT / "README.md").is_file())

    def test_every_skill_documented(self):
        comandi = (USO / "comandi.md").read_text(encoding="utf-8")
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertTrue(skills)
        for path in skills:
            name, meta = path.parent.name, frontmatter(path)
            with self.subTest(skill=name):
                heading = f"### `/tollgate:{name}`"
                self.assertIn(heading, comandi)
                body = "\n".join(section(comandi[comandi.index(heading):], "### `/tollgate:"))
                hint = meta.get("argument-hint")
                if hint:
                    self.assertIn(f"`{hint}`", body, "argument-hint mancante o diverso")
                else:
                    self.assertNotIn("Argomenti:", body, "la skill non ha argument-hint")
                if meta.get("disable-model-invocation") == "true":
                    self.assertIn("solo l'utente", body.casefold())
                else:
                    self.assertNotIn("solo l'utente", body.casefold(),
                                     "la skill può essere lanciata dal modello")

    def test_limits_match_spec_1_2(self):
        in_spec = spec_limit_titles()
        self.assertGreater(len(in_spec), 20, "la lettura della spec non trova le voci di 1.2")
        limiti = (USO / "limiti.md").read_text(encoding="utf-8")
        in_doc = {normalize(line[4:]) for line in limiti.splitlines() if line.startswith("### ")}
        self.assertEqual(in_doc - in_spec, set(), "voci di limiti.md che la spec non ha")
        self.assertEqual(in_spec - in_doc, set(), "voci della spec assenti da limiti.md")

    def test_no_local_paths(self):
        for path in DOCS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotIn("/home/", text)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("MEGA", text)

    def test_relative_links_exist(self):
        checked = 0
        for path in DOCS:
            for m in LINK.finditer(path.read_text(encoding="utf-8")):
                target = m["target"]
                if re.match(r"[a-z]+:", target):
                    continue
                checked += 1
                name, _, anchor = target.partition("#")
                linked = path.parent / name if name else path
                with self.subTest(file=path.name, link=target):
                    self.assertTrue(linked.exists())
                    if anchor and linked.suffix == ".md":
                        self.assertIn(anchor, heading_slugs(linked))
        self.assertGreater(checked, 5)

    def test_update_pins_documented(self):
        text = (USO / "emergenze-e-aggiornamenti.md").read_text(encoding="utf-8")
        self.assertIn("gate/workflows/PINS", text)
        self.assertIn("init --update", text)
        self.assertTrue((ROOT / "gate" / "workflows" / "PINS").is_file())


if __name__ == "__main__":
    unittest.main()
