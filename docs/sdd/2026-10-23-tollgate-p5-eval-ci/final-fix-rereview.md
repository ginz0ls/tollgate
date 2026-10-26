### Verdetti sui rilievi
1. F1/T1 `with open` in test_p5_scripts.py:951-952: INDIRIZZATO.
2. F2+F4/T5 «Prima di ogni pubblicazione» + nota PATH sulle evidenze delle sonde (piano, riga 483): INDIRIZZATO.
3. F3 `*.lock` esclusi in evals/run.sh:244; test in test_eval_run.py (crea migrate.lock e stato.txt, verifica copia/assenza); evidenze non toccate: INDIRIZZATO.
4. F5 riga in sezione 7 del piano (riga 466, rinvia a reviews.py:358-361, finish check/open-pr ricalcolano): INDIRIZZATO.
5. T2 matrice s5 (riga 384) ed e3 (riga 391) con «sotto soglia al primo giro, difetto, sopra soglia all'ultima»: INDIRIZZATO. eval.md:21 spiega già la convenzione «sotto soglia: difetto corretto» e le righe 29/35 la usano: basta.
6. T3 spec riga 1381: testo «spec riaperto (<motivo>): fase spec_audit» coincide con l2acts.py:286: INDIRIZZATO.
7. T4 limiti.md:109 e spec riga 110: sostituita la frase, titolo invariato, coerente con spec ~577: INDIRIZZATO.

### Danni nuovi nel diff della correzione
Nessuno. Test mirati (test_eval_run, test_docs, test_p5_scripts): 135 OK.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
