# Ri-revisione giro di correzione 2 (Task 6)

### Verdetti sui rilievi
**`anonymize` lasciava il nome utente come parola intera (proprietario e gruppo di `ls -la`)**: INDIRIZZATO.
- `evals/scrub.py` `_patterns`: nuova regex `person = \b<utente>\b` (escape con `re.escape`), applicata in `clean` per ultima: `person.sub("USER", folder.sub("-home-USER-", home.sub("/home/USER", text)))`.
- Ordine: `/home/<utente>` diventa `/home/USER`, poi `-home-<utente>-` diventa `-home-USER-`, poi la parola intera. Dopo le prime due passate il nome reale non compare più in quelle forme, quindi `person` non può produrre doppioni né forme tipo `/home/USER/USER`. `USER` non coincide col valore reale (valori riservati/corti rifiutati).
- Confini: `\b` con nome `utente-prova`: `utente-provax` non corrisponde (a|x senza confine), `xutente-prova` idem; `-home-utente-prova` senza trattino finale (fine riga) corrisponde come parola intera. Il trattino interno è letterale grazie a `re.escape`.
- Controllo valori corti/riservati: `anonymize` chiama `_check_values` per primo, invariato; nessuna stampa dei valori; docstring aggiornato (`-home-<user>-` e `user` parola intera).
- Test: `tests/test_eval_run.py` `test_anonymize_user_name_as_a_whole_word` (riga `ls -la` in file di testo e colonna `.db`, `utente-provax` e `xutente-prova` invariati, il `.db` non contiene più i byte del nome, `ValueError` con `abc`); `test_anonymize_project_folder_names_with_dashes` aggiornato coerentemente (3 file, `altro.txt` ora `-home-USER`). Il report mostra RED/GREEN della suite (4175 OK su entrambi gli interpreti, exit 0); verificato sul diff, non rilanciata.

### Danni nuovi nel diff della correzione
Nessuno. Minor (non bloccante): con nomi che iniziano o finiscono con `-` o `.` il `\b` non coglie il bordo (stessa limitazione del pattern dell'host); e `utente-prova-extra` o `x-utente-prova` vengono comunque sostituiti (`-` è confine di parola). Comportamento accettabile e coerente con l'host.

### Osservazioni fuori ambito
Un nome utente comune (es. una parola da dizionario di 4+ lettere non in `RESERVED`) verrebbe sostituito ovunque nelle evidenze, anche in testo non legato all'utente: rischio di falsi positivi, non di fuga di dati.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
