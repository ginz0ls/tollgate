# Task 7 (Step 2-4): ri-revisione del giro di correzione 1

Diff: 75084c1..6dda678. Verificato anche `bash -n` (ok) e `python3 -B -m unittest tests.test_b3bis_script` (Ran 13, OK; nessuna cartella `/tmp/tollgate-b3bis*` rimasta).

### Verdetti sui rilievi

1. **(Important) Link simbolici su `B3BIS_DIR` o su una cartella padre sotto `/tmp`: errore prima di ogni scrittura.** INDIRIZZATO.
   `spikes/b3bis/models-prova.sh:46-66`: `verifica_dir` ricava `top` (`/tmp/tollgate-b3bis` o `/tmp/tollgate-b3bis-test-<nome>`), poi per `top` e `DIR` rifiuta `-L` e, se esiste, `pwd -P` diverso dal percorso dato (cattura anche un `/tmp` alias). Gira prima di ogni modo (`:190`) e quindi prima di `mkdir -p` (`:125`, `:178`). Messaggio con prefisso `B3BIS_DIR`.
   Test `tests/test_b3bis_script.py:138-157` (`test_dir_rejects_symlinks_and_deep_paths`): link dentro la cartella del test che punta a un'altra cartella (`lnk`->`altro`), link di primo livello in `/tmp` (`toplink/w`), alias interno (`alias`->`w`); per tutti e tre i modi errore con `B3BIS_DIR` e asserzione che `altro` e `top/w` restano vuote. Nota: `lnk/x` e `a/b` sono rifiutati per profondità, non per link, ma `lnk` da solo e `toplink/w` coprono i due rami del controllo link.

2. **(Minor) Un solo livello sotto `/tmp/tollgate-b3bis-test-<nome>`.** INDIRIZZATO.
   `models-prova.sh:51-57`: `rest` con `/` iniziale, `//` o due `/` -> errore. Test: `self.dir/"a"/"b"` rifiutato per tutti e tre i modi, e `assertFalse((self.dir/"a").exists())` (`tests:155-157`).

3. **(Minor) `umask 077` prima di creare `out/` e `state/`.** INDIRIZZATO.
   `models-prova.sh:17` (prima di ogni `mkdir`/redirect). Test `tests:159-166` (`test_out_and_state_are_private`): `state` e `out` e ogni file in `out` con `mode & 0o077 == 0`. Con umask 022 tipico dell'ambiente sarebbe rosso senza la riga.

4. **(Minor) Il test della chiave asserisce frase esatta e assenza del valore in stdout, stderr e file sotto `B3BIS_DIR`.** INDIRIZZATO, con una riserva sull'esclusione.
   `tests:200-215`: frase esatta dello script, `FAKE_KEY` non in `stdout+stderr`, scansione di ogni file con `rglob` sotto `work`. Sull'esclusione di `repo/.git`: non è giustificata né necessaria. Lo script non scrive mai il valore lì (il finto scrive il segnale in `self.dir`, fuori da `work`), e gli oggetti git sono compressi, quindi la ricerca di byte grezzi non vi troverebbe nulla comunque; ma i file di testo in `.git` (config, hook, log, ref) restano non coperti e l'origin nudo `work/origin` NON è escluso, quindi la regola è incoerente. Non nasconde un caso oggi esistente; è una lacuna di copertura minore, non un difetto che impedisca di dare per indirizzato il rilievo (la frase e le tre uscite sono asserite).

### Danni nuovi nel diff della correzione
Nessuno. (Minor trascurabile: l'esclusione di `.git` sopra.)

### Osservazioni fuori ambito
- Nessun controllo del proprietario su un `/tmp/tollgate-b3bis` preesistente (cartella reale creata da altri in `/tmp` condiviso): non è un link, passa `verifica_dir`; con `umask 077` le scritture altrui falliscono e non c'è fuga, ma la cartella potrebbe essere usata da un altro utente per sostituire `repo`. Rischio basso per un'utenza singola.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
