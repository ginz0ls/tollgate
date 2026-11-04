# Brief per la sessione che scrive il piano di B3-bis (sentinella dei modelli)

Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa scrivere
Tre file, con la data di oggi nel nome, sul modello di quelli di B3 (`docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md`, `-esecuzione.md`, `-brief-sessione.md`):
- il piano di B3-bis, con «Decisioni di questo piano», «Review Focus», «Copertura» e i task con firme e test;
- le istruzioni d'esecuzione;
- il brief della sessione che lo eseguirà.

Solo documenti: nessun codice, nessun `claude -p`. Rete solo per leggere con `WebFetch` le pagine ufficiali dei fornitori, per verificare gli endpoint. Lavora su `main`, un commit per ogni giro di revisione, niente push.

## Da leggere
1. Il progetto di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, sezione 9 compresa: è l'autorità.
2. Il piano principale `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3, 9 e le prove di B3.
3. La spec del nucleo rev 29: 3.2 (rete negli hook), 11.2, 11.4, 18.4.
4. Il registro di B3 `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/`: `README.md`, `progress.md`, `final-review.md`.
5. `skills/rules-ai/SKILL.md` e `docs/profili/ai.md`.
6. I fatti in `.superpowers/plan-b3/fatti-sentinella.md` e `fatti-modelli-web.md` della radice: da verificare, non sono un'autorità.
7. La memoria del progetto.

## Scelte dell'utente, da non riaprire
- La sentinella gira sul computer dell'utente all'avvio di un lavoro, con la chiave API già nell'ambiente. Niente segreti su GitHub, niente job programmati, gli hook restano senza rete.
- Fornitori: Anthropic (`GET /v1/models`) e Gemini (`models.list`); OpenAI e OpenRouter se le loro pagine ufficiali danno un elenco dei modelli.
- Avvisa se esiste un modello stabile più nuovo della stessa famiglia, o se uno in uso sta per essere ritirato.

## Da decidere nel piano
- La forma del «punto unico» del nome del modello (rinvio di B3, decisione 15) e come adattare `test_real_markers_not_in_tollgate_bin`.
- Se includere la pulizia delle cartelle temporanee che i test lasciano in `/tmp` e la ripulitura delle evidenze di B2 e gh-p4 dal testo di skill esterne, oppure perché restano fuori.

## Come lavorare
- Le scelte vere (compromessi, costi) si chiedono all'utente in parole semplici, con il costo esplicito. Il resto si decide con una `Ruling:` scritta nel piano.
- Revisione del piano da opus a contesto pulito, in sola lettura, a giri, finché un giro dice «pronto» con 0 critical e 0 important. La tabella dei giri va in fondo al piano.

## Finito quando
- I tre file esistono su `main`, committati.
- L'ultima riga della tabella dei giri dice «pronto», 0 critical, 0 important.
- `plugin-workflow-decisioni.md` nella memoria ha una voce sul piano di B3-bis.
- L'utente ha ricevuto, in italiano semplice: cosa fa B3-bis, le scelte che gli sono state chieste, quanto costerà eseguirlo, il prossimo passo.
