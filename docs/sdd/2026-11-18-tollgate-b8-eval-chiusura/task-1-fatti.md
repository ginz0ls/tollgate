# Task 1, Step 0: fatti dalle pagine ufficiali (controller, WebFetch, 2026-11-18)

Elenco vincolante per il Task 1. Nessun testo delle pagine: solo fatti con parole nostre.

## Programmi che caricano l'ambiente prima di un comando
| Programma (eseguibile) | Pacchetto npm | Forma | Opzione con il comando come testo | Fonte |
|---|---|---|---|---|
| `dotenv` | `dotenv-cli` | `dotenv [opzioni] [--] <comando>`; `--` facoltativo se il comando non ha argomenti | nessuna (`-c` è una cascata d'ambiente con valore facoltativo, NON un comando) | README del repository ufficiale di dotenv-cli |
| `dotenvx` | `@dotenvx/dotenvx` | `dotenvx run [opzioni] -- <comando>` | nessuna | dotenvx.com/docs, README del repository ufficiale |
| `cross-env` | `cross-env` | `cross-env NOME=valore … <comando>`; nessuna opzione | nessuna | README del repository ufficiale |
| `cross-env-shell` | `cross-env` | come `cross-env`, ma il comando passa da una shell (`&&`, `$VAR`): di solito una sola stringa | il comando stesso è testo di shell | README del repository ufficiale |
| `env-cmd` | `env-cmd` | `env-cmd [opzioni] -- <comando>` | con `--use-shell` il comando dopo `--` è testo di shell (`env-cmd -f x --use-shell -- "a && b"`) | README del repository ufficiale |
| `doppler` | nessuno (Homebrew, apt, script) | `doppler run [opzioni] -- <comando>` | `--command <testo>` (anche `--command=…`); `-c` è `--config`, NON un comando | docs.doppler.com |
| `infisical` | nessuno nella documentazione | `infisical run [opzioni] -- <comando>`, oggi anche `infisical secrets-manager run` e l'alias `infisical sm run` | `--command` **e `-c`** (per Infisical `-c` è il comando) | infisical.com/docs (riferimento della CLI) |
| `op` | nessuno | `op run [opzioni] -- <comando>` | nessuna | 1password.dev (riferimento della CLI) |

Opzioni con valore (solo informative, la scansione non le usa): dotenv `-e`, `-v`, `-p`, `-c` (facoltativo); dotenvx run `-f`/`--file`, `--env-file`, `--env`, `--convention`, `--log-level`, `--ignore`, `-fk`, `--token`; env-cmd `-e`/`--environments`, `-f`/`--file`; doppler run `-p`/`--project`, `-c`/`--config`, `--command`, globali `--token`/`-t`, `--scope`, …; infisical run `-c`/`--command`, `-e`/`--env`, `--path`, `--projectId`, `-t`/`--tags`, `--token`, `--project-config-dir`, `--watch-interval`; op run `--env-file`, `--environment`.

## Supabase CLI 3: opzioni con valore dei sottocomandi di `FLAG_EFFECTS`
(`--remote[=…]` prende un valore solo nella forma con `=`: non entra mai nella tabella.)
- `db push`: `-p`, `--password`
- `db pull`: `-p`, `--password`, `-s`, `--schema`, `--diff-engine`
- `db reset`: `--last`, `--version`, `--sql-paths`
- `db lint`: `--fail-on`, `--level`, `-s`, `--schema`
- `db query`: `-f`, `--file`, `-o`, `--output`
- `db advisors`: `--fail-on`, `--level`, `--type`
- `db diff`: `-f`, `--file`, `--from`, `-o`, `--output`, `-s`, `--schema`, `--to`
- `db dump`: `-f`, `--file`, `-x`, `--exclude`, `-p`, `--password`, `-s`, `--schema`
- `migration up`: nessuna; `migration down`: `--last`; `migration repair`: `-p`, `--password`, `--status`; `migration fetch`: nessuna
- `migration list`: `-p`, `--password`; `migration squash`: `-p`, `--password`, `--version`
- `gen types`: `--lang`, `--query-timeout`, `-s`, `--schema`, `--swift-access-control`
- `test db`: nessuna; `inspect db` (e i suoi sottocomandi): nessuna; `inspect report`: `--output-dir`; `seed buckets`: nessuna
- Globali con valore (già in `SUPABASE_VALUE_OPTIONS`): `--agent`, `--dns-resolver`, `--network-id`, `-o`/`--output`, `--output-format`, `--profile`, `--workdir` (riconfermati).

## CLI 2 e `db query`
Le note di rilascio di github.com/supabase/cli: `db query` nasce in v2.79.0; v2.85.0, v2.108.0, v2.112.0 lo citano senza dire il bersaglio predefinito; v3.0.0 aggiunge il consenso (`--yes`) contro un bersaglio ospitato. Nessuna nota dice che in 2.x `db query` senza opzioni leggesse o scrivesse sul progetto collegato. `db query` resta `with_remote`.
