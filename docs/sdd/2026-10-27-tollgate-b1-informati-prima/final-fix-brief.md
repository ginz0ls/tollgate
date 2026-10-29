# Giro unico di correzione della revisione finale di B1

Requisiti: `final-review.md`, in questa cartella. Correggi le voci elencate qui sotto, nell'ordine in cui le trovi in quel file e con la correzione che propone. Le ruling del controller sono in fondo a `progress.md` e prevalgono su `final-review.md`.

## Da correggere
- **I1**: i brief di revisione e di `--fix` devono dare l'esito della nota e i suoi problemi.
  - Una nota non valida va trattata come mancante: con l'interruttore acceso `major` più `missing`, con l'interruttore spento `moderate`.
  - Nel brief di `--fix`, se la nota non è valida, scrivi «la nota non è valida: correggila e consegnala di nuovo prima di modificare».
  - Esito e problemi vanno in un recinto, come il testo della nota.
  - Aggiorna `agents/task-reviewer.md` se serve, per dire come trattare l'esito.
- **I2**: `skills/setup/SKILL.md`.
  - Proponi per prime le regole per dominio, nel `.claude/settings.json` del progetto.
  - Scrivi in una frase il rischio di un `WebFetch` libero.
  - Il `"WebFetch"` globale resta una scelta dell'utente, con il rischio scritto.
  - Allinea la spec del nucleo 11.3 (rev 27, `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`) e stringi la regex di `test_setup_proposes_web_permissions` (deferred 22).
- **Minor nuove 1-8** di `final-review.md`. Per la minor 2 (uscita anticipata di `hooks/run` per i subagenti di sola lettura):
  - esci prima solo per i tipi di sola lettura di tollgate, con un elenco fisso che un test confronta con `config` e `agents/`;
  - non escludere per prefisso: un tipo sconosciuto deve continuare a passare da Python.
- **Minor 6** (una sola funzione per l'interruttore, usata da gate e `taskcmd`): unifica la funzione, ma lascia il comportamento su `OSError` com'è oggi. La correzione di `OSError` è rinviata a B2 (deferred 31).
- **Deferred «da correggere ora»** del triage: 9, 10, 16, 18, 19 (solo la parte «lavoro dalla cartella», insieme alla minor 1), 20, 21, 22, 24, 26, 27, 28, 29, 30, 32 (insieme alla minor 3), 33, 34, 35.
- **Piano principale di B**, sezione 9 (`docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`): aggiungi le deferred 13 e 31 come obbligatorie nel task di B2 che crea `rules-base`.
- **Spec rev 27**: aggiorna le frasi che descrivono un comportamento cambiato da queste correzioni. Per esempio:
  - l'uscita anticipata di `hooks/run` (7.1);
  - l'esito della nota nel brief del revisore (8.1, 8.5 o la sezione giusta);
  - l'avviso dopo una riconsegna non valida.

## Come
- Prima i test che falliscono, poi la correzione: TDD, come in `implementer-rules.md`.
- Per ogni Important e per ogni minor di comportamento (minor 1, 2, 3, 4, 5, 7; deferred 24 e 35), un test che fallisce prima della correzione.
- `spikes/run-b1-flow.sh` (deferred 35): eseguilo solo con `bash -n` e nel modo `controlla`, più `tests/test_b1_scripts.py`.
