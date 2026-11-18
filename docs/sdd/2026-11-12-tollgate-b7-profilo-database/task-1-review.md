# Revisione Task 1 (B7): effetti esterni di Supabase, Prisma, Drizzle

Pacchetto: `349bb5b..ca09c16` (`bin/tollgate_analysis/bash.py`, `tests/test_bash.py`). Sola lettura; sonde con `bash.parse` + `bash.effect_reason` su testo (nessun programma vero, nessuna rete). Le righe citate sono quelle di `ca09c16`.

### Aderenza (✅ / ❌ con riferimenti; ⚠️ non verificabile)

- ✅ Liste della decisione 6, voce per voce, contro il codice (`bash.py` ~1020-1060 e `_supabase_reason` 1284-1307): `SUPABASE_LOCAL` (14 voci, senza `login`/`logout`, D6), `with_remote` (13 voci), `unless_local` (6 voci), letture (6 + `snippets list`), tutto il resto chiede. `branches get`, `snippets download`, `storage ls`, `unlink`, `bootstrap`, `config pull|diff`, `whoami`, `login`, `logout` chiedono (sondati). `REMOTE_FLAGS`, `SUPABASE_VALUE_OPTIONS`, `SUPABASE_GLOBAL_OPTIONS` uguali alla decisione 6 e ai fatti.
- ✅ Ordine di valutazione: globali saltate, poi `SUPABASE_LOCAL`, `FLAG_EFFECTS`, letture, il resto chiede. Un'opzione sconosciuta prima del sottocomando chiede (`--sconosciuta`, `-ojson`, `--debug=true`).
- ✅ D1 (`--help`/`-h`/`--version` solo fuori dai valori delle opzioni globali e prima del primo `--`): i tre test che chiedono ci sono (`test_bash.py` `test_supabase_help_only_outside_option_values`).
- ✅ D2 (`npx eslint supabase --fix` chiede, `launcher_candidates` invariato), D3 (i tre test mancanti di B5, gli altri dichiarati guardie), D4 (`docs/uso/comandi.md` non toccato), D5, D6, D7 (ripiego a parte, regex vecchia tolta, i tre casi di testo), D13 (`push:pg|mysql|sqlite`, anche dietro `npx`), Prisma 8 (`db init|update|migrate|sign`).
- ✅ Prisma 7 e Drizzle contro `task-1-fatti.md`: chiedono tutto l'elenco; `db pull`, `migrate status|diff`, `generate|format|validate|init|version|debug`, `drizzle-kit pull|introspect|generate|check|up|export` passano.
- ✅ Dietro lanciatori: `npx`, `npx -y x@latest`, `pnpm dlx`, `pnpm exec`, `pnpm x`, `yarn x`, `yarn dlx`, `bunx --bun`, `npm exec -- x`, `env`, `sudo`, `bash -c`, percorso `./node_modules/.bin/x`: scritture chiedono, locali passano (sondati).
- ✅ Rimozione di `_SUPABASE_WRITE`/`_SUPABASE_READ` e rinomina `_flag_data_reason`: nessun altro chiamante (grep nel repo, restano solo nei documenti di piano/spec storici).
- ✅ Test: la RED è in `task-1-red.log` (209 fallimenti, 1 errore), la suite è `exit 0` in `suite-task-1.log`, nessun avviso. Righe nuove entro 100 caratteri.
- ❌ Una scrittura sul progetto vero passa senza permesso (I1, I2 sotto).
- ⚠️ Non rieseguita la suite (come da regole). I default della CLI 2 non sono nei fatti: `carry.md:28,40` li manda alla spec 8.5, quindi non è un difetto del task.

### Punti di forza

- La regola è chiusa verso il sicuro davvero: un gruppo sconosciuto, `--` iniziale, `-ojson`, `--workdir db push` (valore che mangia il sottocomando) chiedono. Nessun gruppo sconosciuto ne passa (sondati `seed`, `db remote`, `db schema declarative`, `functions invoke|logs`, `gen`, `db` nudi).
- `_flag_data_reason` generico e `REMOTE_FLAGS` sono la modifica minima: Wrangler resta com'è (`wrangler kv key put K V --remote --local` chiede ancora).
- Il ripiego testuale è costruito dalle stesse liste e sbaglia dalla parte sicura (`--local` e `--remote=false` chiedono, `supabase -h` chiede).
- Test con dati finti, `subTest`, prefissi `""`/`npx`/`pnpm exec`/`bunx` sulle liste locali; i test dei locali dietro lanciatore sono separati e il vecchio test riscritto tiene `vercel`/`vitest`.

### Rilievi

#### Critical
Nessuno.

#### Important

**I1. `--local` nascosto come valore di un'opzione globale: `supabase db push --network-id --local` passa senza permesso** (`bash.py:1229-1248` `_flag_data_reason`, riga `_flag_present(rest, "--local")`; `_supabase_reason` 1296-1298).
Sonda: `supabase db push --network-id --local`, `... --profile --local`, `... --output-format --local`, `... -o --local`, `supabase db pull|migration up|migration repair --network-id --local ...` danno tutte `None`. Con pflag `--network-id` prende come valore il token successivo, quindi `--local` non è mai impostato e `db push` va sul progetto collegato (`--network-id` serve solo al Docker locale, non fa fallire il comando). Il codice salta i valori delle opzioni globali per `--help` (`_supabase_asks_help`) e per le opzioni iniziali (`_supabase_args`), ma non quando cerca `--local` nel resto del comando: stessa famiglia del `--help` usato come valore che il brief chiede di guardare. Costo: una scrittura sul progetto vero (`db push`, `db pull`, `migration up|down|repair|fetch`) senza permesso con un solo token in più.
Correzione: in `_supabase_reason`, prima di `_flag_data_reason(norm)`, togliere da `words` ogni opzione di `SUPABASE_VALUE_OPTIONS` con il suo valore (e la forma `--x=v`), come già fa `_supabase_asks_help`, tenendo una sola funzione per «salta le opzioni a valore» (oggi sono due cicli quasi uguali). Test: i casi sopra devono chiedere; `supabase db push --network-id=x --local` e `supabase db push --network-id n --local` devono passare. Nota: il caso opposto (`--linked` come valore) oggi chiede, quindi è un falso positivo accettabile.

**I2. `--remote false` / `--linked false` contano come assenti per Supabase, e il test lo fissa: `supabase db reset --linked false` passa** (`bash.py:1206-1217` `_flag_present`, usato da `_flag_data_reason`; `tests/test_bash.py` in `test_supabase_remote_flag_asks`, le due righe `supabase db reset --remote=false` e `supabase db reset --remote false` in `check_effects(..., False)`).
Sonda: `supabase db reset --linked false`, `... --remote false`, `supabase db dump --linked false` danno `None`. `_flag_present` considera assente `--x` seguito dal token `false` perché per Wrangler (yargs) il booleano consuma `false`. Con cobra/pflag no: `--linked` e `--remote` (valore facoltativo) non consumano il token successivo, quindi `false` è un argomento posizionale e il comando va sul progetto collegato (cobra accetta argomenti posizionali di troppo se il comando non ha `Args`; non verificabile senza lanciare la CLI, ⚠️). Prima di questo commit `supabase db reset --linked false` chiedeva (il gruppo `db` era in scrittura): è una regressione verso il permissivo, e l'asserzione in `test_supabase_remote_flag_asks` la scrive come voluta. Il testo del piano dice «lo stesso `_flag_present`», ma parla di `--local=0` (D9 di B5), non di `--remote false`; la riga di test è dell'implementatore.
Correzione: per le opzioni remote di Supabase, presenti se compaiono (`--x` o `--x=<qualunque>`), senza il caso `false` (il costo è un falso positivo su `--remote=false`, che nessuno scrive); togliere le due righe dal test e aggiungere `supabase db reset --linked false` tra quelle che chiedono. In alternativa un parametro di `_flag_present` per programma; da scegliere col controller se si vuole toccare Wrangler (no: B5 resta com'è).

#### Minor

- **M1. `--local=0`, `--local=False`, `--local=f`, `--local=F` contano come locali** (`bash.py:1215`): pflag legge tutti come falso e `db push` va sul progetto collegato; sonda: `supabase db push --local=0|False|f` passano. `--local=0` e `FALSE` sono il costo già scritto dalla decisione 6 e da D9 di B5 («imposto dal piano»). Una riga nella pagina (Task 9) o la stessa correzione di I2 (qualunque `--local=<v>` con `v` fuori da `true|1|t|T|TRUE|True` chiede) lo chiude a costo zero; nessun test lo fissa.
- **M2. `--help`/`-h` come valore di un'opzione non globale passa** (`bash.py:1165-1175`): `supabase db push --linked --password --help`, `supabase functions deploy f --import-map --help`, `... --project-ref --help` passano. D1 lo limita alle sole opzioni globali, quindi è conforme al carry; in pratica il valore `--help` fa quasi sempre fallire il comando (password, file, ref non validi), perciò non lo alzo. Se il controller vuole la chiusura completa: `--help` vale solo se il token precedente non è un'opzione fuori da una lista di booleani noti (`--linked`, `--local`, `--remote`, `--debug`, `--yes`).
- **M3. Falsi positivi su comandi locali dietro un separatore o un `--package`** (via `launcher_candidates`, invariato per D2): `npx --package supabase supabase start`, `npx -p supabase supabase migration new x`, `npm exec supabase -- start`, `npm exec supabase -- db reset`, `npm run supabase -- start` ora chiedono (prima passavano). Il candidato è `["supabase", "--", ...]` o `["supabase", "supabase", ...]`. Sono forme meno comuni di `npx supabase …`; scriverli nella spec 8.5 con il costo (decisione 6, «un sottocomando nuovo… chiede»), oppure saltare un `--` iniziale in `_supabase_args` (ma `supabase -- db push` resta da far chiedere).
- **M4. Il ripiego testuale non vede `npx supabase@2 db push` né `/usr/bin/supabase db push`** (`bash.py` `_B`/`_SUPABASE_TEXT`: `supabase` deve seguire uno spazio e avere solo spazi dopo). Già così prima del commit (stessa `_B` della vecchia regex) e lo stesso vale per Wrangler; solo per testi che shlex non legge. Da annotare nel piano principale tra i buchi del ripiego.
- **M5. Prisma/Drizzle con un'opzione prima del sottocomando passano** (`prisma --schema x.prisma migrate dev`, `drizzle-kit --config x.ts push` danno `None`): le voci sono a prefisso (decisione 7, regola aperta, stesso limite di Wrangler già scritto tra i buchi). Non è un difetto del task; da elencare nei buchi del piano principale (non verificato se le due CLI accettano davvero l'opzione prima del comando).
- **M6. Test deboli o tautologici**: `test_supabase_tables` (`tests/test_bash.py`, ultime asserzioni su `SUPABASE_VALUE_OPTIONS`, `REMOTE_FLAGS`) ripete le costanti e fallirebbe solo a cambiare la tabella, non il comportamento; in `test_wrangler_new_entries_in_config` la prima asserzione (`wrangler kv key put K V --local` con `allow`) passerebbe anche senza `allow` (con `--local` il comando è già locale): vuota. Le altre tre del blocco `allow` e la `commands` sono utili. Togliere la prima o usare un comando che senza `allow` chiede (`kv key put K V`).
- **M7. Motivo del veto poco leggibile** in `_supabase_reason` (riga con `words[:2]`): `npx --package supabase supabase db push` dà «supabase supabase db»; `supabase --` dà «supabase » con spazio finale. Cosmetico.
- **M8. Doppio scorrimento di `FLAG_EFFECTS`** (`_supabase_reason` 1293-1298 e poi `_flag_data_reason`, e `_supabase_text_effect` 1459 la terza volta): tre ricerche della stessa voce. Una funzione `_supabase_flag_entry(words)` condivisa le unirebbe; non urgente.

### Valutazione

**Qualità del task:** Da correggere

**Motivo:** Le liste, i carry e i test richiesti ci sono e la regola chiusa regge sui gruppi sconosciuti, sulle opzioni globali iniziali e dietro i lanciatori; ma restano due vie per scrivere sul progetto vero senza permesso, `db push --network-id --local` (I1, valore di un'opzione globale scambiato per `--local`) e `db reset --linked false` (I2, semantica di Wrangler applicata a pflag, con un test che la fissa). Entrambe si chiudono con poche righe e con test mirati.
