import re
import unittest
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent.parent / "supabase" / "migrations"
CREATE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?(\w+)", re.IGNORECASE)


def migrations_text():
    """Il testo di tutte le migrazioni, in ordine di nome: i file `.sql` sono solo testo, non si eseguono."""
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(MIGRATIONS.glob("*.sql")))


class MigrationsTest(unittest.TestCase):
    def test_every_table_has_row_level_security(self):
        text = migrations_text()
        tables = CREATE.findall(text)
        self.assertIn("notes", tables)
        for table in tables:
            with self.subTest(table=table):
                enable = rf"alter\s+table\s+(?:public\.)?{table}\s+enable\s+row\s+level\s+security"
                self.assertRegex(text, re.compile(enable, re.IGNORECASE))


if __name__ == "__main__":
    unittest.main()
