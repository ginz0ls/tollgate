# Task 10: report
Commit: vedi git log (tollgate B1: prove, spec rev 27, piano principale di B). Solo documentazione.
Suite: tests/run 3121 test verdi su Python 3.11.16 (skipped=2) e 3.13.5; `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` 3121 OK; nessun «unclosed database».
Fatto: spec rev 27 (intestazione, 0, 3, 3.1, 3.2, 7.1, 7.2, 8.1, 8.5, 8.6, 11.3, 11.4, 12.2 con migrazione 6, 12.4, 16, 18.4, 20); piano principale (stato, riga B1, sezione 3 con nomi reali, nuove sezioni 8 «Prove di B1» e 9 «Rinvii»); riga di avanzamento nel progetto di B.
Dubbi/scostamenti:
- La «3.3» della rev 27: la spec non ha una 3.3 (3.2 è «Principi di design»); i criteri di validità della nota (con «non tutte e due» e il tetto di 8.000) stanno in 8.1, marcata come controllo 3.3 del progetto.
- Ruling D8 («rifiuto dal task successivo»): dal codice (`research_gate._verdict`) il rifiuto vale dalla prima modifica senza nota valida, anche nel task in corso se ha già ricevuto l'avviso. Scritto così in 12.2 e nella sezione 9.
- In L0 conta solo Edit/Write della sessione principale; Bash non è gated (test_l0_bash_not_gated): descritto così in 7.2.
- Sezione 9 del piano contiene solo i rinvii per B2/B3-B7/B8; gli altri minor (deferred) restano al triage del controller.
- «Revisione finale senza critical/important» non è ancora avvenuta: lo stato del piano dice solo «chiusa sul ramo, merge in attesa dell'OK».
- Punti senza prova in B1 (dichiarati nella tabella): obiettivi 3 e 5, regole mai lette, 3.4, nomi dei modelli, profili, rules-base agli agenti, eval; pertinenza del revisore e giro --fix solo in parte/non col modello; L2 senza test dedicato.

## Giro 1
Corretti I-1 (12.2 e sezione 9: il rifiuto vale dalla prima modifica senza nota valida in qualunque task in corso), I-2 (piano committato dal modello, registrato da tollgate), M-1 (limiti della prova reale in sezione 16 e nella sezione 8 del piano, su più voci), M-2 (250 ms limite inferiore, avvio di Python come deduzione), M-3 (stato «implementata sul ramo, merge in attesa»), M-4 (legame (a)-(e) con il 3.3), M-5 (niente «terna»), M-6 (order 25 di research_gate), M-7 (due rinvii in sezione 9 per B3-B7). Solo documentazione.
Suite: tests/run 3121 OK su 3.11.16 (skipped=2) e 3.13.5. Commit nuovo, senza amend.
