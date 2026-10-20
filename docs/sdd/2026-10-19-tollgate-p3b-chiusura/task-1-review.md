# Revisione Task 1 (P3b): verifiche dell'interfaccia di gh

Controllato sul pacchetto `review-cf4fe90..b5a3630.diff` e rileggendo il testo d'aiuto in `/tmp/tollgate-p3b/help/`.

### Aderenza
- ✅ Script scrive in `/tmp/tollgate-p3b/help/` solo `gh --version` e `gh <cmd> --help` (6 file presenti). Nessuna rete, nessun `gh auth`/`api`/`pr create` reale.
- ✅ Tabella `Id | Voce | Esito | Evidenza | Conseguenza` con G1-G5 (docs/verifiche/2026-10-19-p3b-verifiche.md:8-14).
- ✅ G1: citazione esatta in api.txt:26-27. «Non provato con insteadOf» dichiarato.
- ✅ G2: `-H/-B/-t/-F` presenti in pr-create.txt:32-48; l'aiuto non dice cosa stampa su stdout (grep verificato), coerente con la decisione 10.
- ✅ G3: `pr edit [<number>|<url>|<branch>]` e `-F, --body-file` (pr-edit.txt:11,20).
- ✅ G4: esito «in parte» corretto. Verificato: `--state {open|closed|merged|all}`, `--head`, `--json`, `--jq`, `--limit` default 30; nessuna sezione JSON FIELDS; `headRefOid`/`mergedAt` assenti (grep sui file vuoto); `comments` esiste solo come flag `-c`. Non scritto come riuscito.
- ✅ G5: `--paginate` e `--jq` presenti; `--slurp` assente (0 occorrenze in api.txt); il formato per riga è dichiarato non provato.
- ✅ carry.md Task 1: annotati `--state all`, `headRefOid`/`mergedAt`, `--paginate/--jq/--slurp`.
- ✅ `claude --version` annotato (2.1.304), solo annotato.
- ✅ Conseguenze per il piano coerenti con gli esiti (fakegh non deve dipendere da stdout di create; uscita non zero = errore).

### Punti di forza
Onestà sugli esiti: i tre punti non provabili (insteadOf, nomi dei campi JSON, formato per riga) sono marcati come tali e con l'azione a valle (revisori finali / fakegh). Il rapporto cita virgolette dall'aiuto, non memoria.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `spikes/run-p3b-experiments.sh`: modo 644, mentre il modello `run-p3a-experiments.sh` è 755. Il rapporto dice `bash spikes/...`, quindi funziona, ma conviene `chmod +x` per coerenza.
2. `spikes/run-p3b-experiments.sh:12`: lo script non cattura `claude --version` (richiesto dal brief come annotazione); il valore 2.1.304 nel rapporto non è riproducibile dallo script. Aggiungere `claude --version > "$H/claude-version.txt" 2>&1`.
3. verifiche.md:14 (G4): «Il limite 30 vale anche con `--head`» è un'inferenza (l'aiuto dà solo il default 30 di `--limit`), non un fatto provato; riformulare come «il default 30 non è legato a `--head`, quindi vale» o togliere.
4. Rapporto G4: i nomi dei campi restano non verificati; l'implementatore ha giustamente evitato `gh pr list --json` senza valore (non è `--help`). Nessuna azione, ma la conseguenza «primo uso col gh vero» deve restare tracciata fino al Task finale.

Nota: il report dell'implementatore cita «997 test OK»; non verificato (task senza codice, non rilanciato).

### Valutazione
**Qualità del task:** Approvato. **Motivo:** esiti fedeli al testo d'aiuto, nessun esito non provato spacciato per riuscito, vincoli di rete rispettati; restano solo rifiniture minori (permessi dello script, `claude --version` nello script, una frase inferita).
