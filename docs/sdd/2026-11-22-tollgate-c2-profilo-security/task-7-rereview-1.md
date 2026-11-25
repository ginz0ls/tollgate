# Task 7: ri-revisione del giro di correzione 1 (commit `348bfec`, pacchetto `review-2485d3d..348bfec.diff`)

Ri-revisore in sola lettura. Pacchetto letto una volta. Nessuna suite rilanciata, nessuna copia creata, niente scritto nel worktree fuori da questo file. Un solo controllo mio, in sola lettura: il testo di `agents/implementer-security.md` al commit `348bfec` (`git show`, passato a `python3 -B` da stdin) con la stessa estrazione della sezione che fa il test, togliendo un programma alla volta.

### Verdetti sui rilievi

**m1 (rilievo 1): la frase «Un rischio che nessuna regola copre…» di `final-security` era ambigua per i temi delle regole sul report, e nessun test la fissava.** INDIRIZZATO.
- `agents/final-security.md:36`: la frase è ora «Un rischio che nessuna regola di `rules-security` copre, nemmeno una di quelle che spettano al revisore del task, si segnala lo stesso, con il passo del piano che tocca e la gravità del suo effetto», parola per parola quella decisa dal controller in `task-7-fix-1.md`.
- Coerenza con il resto dell'agente: il paragrafo dopo (`:38`) dice «Le altre regole di `rules-security` sono del revisore del task […]: tu non apri rilievi su di esse», e «Standard del revisore» ripete lo stesso per le regole sul report di ogni area. La frase nuova chiude l'unica via rimasta per portare in revisione finale un tema di una regola sul report (per esempio il limite dei tentativi di R-SECURITY-15) come «rischio senza regola». Nessun id di regola sul report compare nel file: resta vero.
- `tests/test_manifest.py:420-421` (`test_final_security_reviews_by_risk`): `assertIn` sulla frase intera fino a «si segnala lo stesso», che contiene «nemmeno una di quelle». Il report dichiara il RED (test cambiato prima dell'agente: `FAILED (failures=1)`); è credibile dal diff, perché la frase vecchia non contiene la stringa cercata.

**m3 (rilievo 3): `reviewer-security` diceva «nello stesso task», la skill «nello stesso lavoro».** INDIRIZZATO.
- `agents/reviewer-security.md:53`: «Se nello stesso lavoro è attiva un'altra area…». La skill ha la stessa parola (`skills/rules-security/SKILL.md:19`). Nel diff la riga cambia solo in quella parola.

**m5 (rilievo 5): il test cercava i nomi dei programmi come sottostringhe (`bun` dentro `bunx`, `npm` dentro `pnpm`).** INDIRIZZATO.
- `tests/test_manifest.py:402-404` (`test_real_security_agent_names_forbidden_tools`): i 14 programmi si cercano con `` f"`{prog}`" ``; le altre quattro parole restano sottostringhe (`:405-406`), come deciso.
- Controllo mio sul testo dell'agente a `348bfec`: ognuno dei 14 nomi compare tra accenti gravi una volta sola nella sezione; togliendo `` `bun` `` la ricerca nuova fallisce su `bun` e la vecchia no; lo stesso per `npm` e per `supabase` (che la ricerca vecchia trovava in un altro punto della sezione). Per tutti i 14 il test nuovo diventa rosso. Coincide con l'evidenza del report (copia temporanea: nuovo rosso, vecchio verde).

Vincoli del giro:
- **Nessun altro testo degli agenti cambiato**: nel diff, `final-security.md` e `reviewer-security.md` hanno una riga ciascuno, e in ciascuna cambia solo la frase del rilievo.
- **Paragrafi derivati dai generici identici**: le due righe cambiate stanno dentro la sezione «Area `security`», che non deriva dai generici; `test_area_agents_derive_from_generic` è nel file rilanciato verde dal report.
- **Solo tre file nel commit**: `agents/final-security.md`, `agents/reviewer-security.md`, `tests/test_manifest.py` (elenco del pacchetto: 10 righe aggiunte, 5 tolte).
- **Evidenze del report**: nomina i test e mostra gli esiti (`tests.test_manifest tests.test_b1_scripts`, 227 test, OK; `claude plugin validate --strict .` passato; suite 4516 verdi sui due interpreti, `exit 0`). Lo scostamento dall'ordine dei commit chiesto (ritocchi dopo il Task 8 invece che prima) è dichiarato e motivato, senza riscrivere la storia: accettabile.

### Danni nuovi nel diff della correzione

Nessuno.

### Osservazioni fuori ambito

- `tests/test_manifest.py:388-390`, il test gemello dell'implementatore di `database`, cerca ancora i programmi come sottostringhe (stessa debolezza di m5: `npm` dentro `pnpm`). Non toccato dal giro e non chiesto: da valutare tra i rinvii.
- I rilievi 2, 4 e 6 della revisione restano note per il controller, come deciso in `task-7-fix-1.md`.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
