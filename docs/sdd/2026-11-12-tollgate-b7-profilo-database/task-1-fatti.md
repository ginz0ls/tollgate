# Fatti dello Step 0 del Task 1 (controller, 12/11/2026; elenco con parole nostre, nessun testo delle pagine)

## CLI di Supabase 3 (supabase.com/docs/reference/cli)
- Opzioni globali con valore: `--agent`, `--dns-resolver`, `--network-id`, `-o`/`--output`, `--output-format`, `--profile`, `--workdir` (anche `--x=v`). Senza valore: `--debug`, `--experimental`, `--yes`, `-h`/`--help`. Confermata la decisione 6.
- `--remote` accetta un valore facoltativo (`--remote`, `--remote=<ref|branch|url>`); `--linked`, `--project-ref`, `--db-url`, `--local` e `--project-id` (di `gen`) sono deprecate nella 3 e spariscono nella 4.
- Locali per default (con `--remote` per il progetto collegato): `db push`, `db pull`, `db reset`, `db dump`, `db diff`, `db lint`, `db query`, `db advisors`, `migration list`, `migration repair`, `migration squash`, `gen types`, `test db`, `inspect db …`, `inspect report`. Senza default dichiarato ma con solo `--remote`: `migration up`, `migration down` (`--last <n>`), `migration fetch`, `seed buckets`.
- Progetto collegato per default: `config pull` (scrive il `config.toml` locale), `config diff` (legge), `functions deploy|delete|download|list`, `secrets set|unset|list`, `config push`.
- `snippets list` (letture: elenca gli snippet SQL della piattaforma) → entra nelle letture. `snippets download` → chiede (regola chiusa).
- `branches get` mostra i dati di connessione di un ramo → chiede sempre (decisione 6).
- Gruppi esistenti non nominati dalla decisione 6 e quindi chiedono per la regola chiusa: `whoami`, `bootstrap`, `pull`, `db schema declarative …`, `config pull`, `config diff`, `backups list`, `backups restore`, `notebooks …`, `telemetry …`, `feedback …`, `issue …`, `storage …`, `sso …`, `domains …`, `vanity-subdomains …`, `encryption …`, `network-bans …`, `network-restrictions …`, `ssl-enforcement …`, `postgres-config …`.
- Le liste della decisione 6 valgono come scritte, più `snippets list` tra le letture.

## Prisma
- Prisma 7 (riferimento della CLI): chiedono `migrate dev`, `migrate deploy`, `migrate reset`, `migrate resolve`, `db push`, `db execute`, `db seed`, `studio`. Passano (letture o nessun accesso): `db pull`, `migrate status`, `migrate diff`, `init`, `generate`, `validate`, `format`, `version`, `debug`.
- Prisma 8 (release candidate, comandi nuovi): chiedono `db init`, `db update`, `db migrate`, `db sign`. Passano (regola aperta): `db verify`, `contract …`, `migration …` (status, log, list, graph, check, plan), `init`, i comandi di piattaforma.

## Drizzle (drizzle-kit)
- Chiedono: `push`, `migrate`, `studio`. Passano: `pull`, `introspect`, `generate`, `check`, `up`, `export`.
