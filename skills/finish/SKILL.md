---
name: finish
description: Chiude il lavoro: controllo locale della Definition of Done, revisione finale (L1, L2) e apertura della PR. Il coordinatore non scrive codice.
---

Sei il coordinatore della chiusura: lanci i comandi, lanci i revisori, leggi i verdetti. Il codice dei rilievi lo correggono gli implementatori di `/tollgate:execute`, non tu.

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.
Lancia i comandi dal **worktree del lavoro**.

L'atto `finish` lo registra il hook solo quando l'utente ha digitato `/tollgate:finish`. Se questa skill parte da un'altra strada e un comando rifiuta per mancanza dell'atto, di' all'utente di digitare `/tollgate:finish` e fermati.

**Regola ferma:** mai `git push` né `gh pr create` da Bash: la PR la apre soltanto `finish open-pr`, che spinge lo SHA giusto e la descrive dal DB.

**Codici d'uscita, per ogni comando:** riporta il messaggio così com'è (le righe `rifiuto:`, `avviso:`, `needs_you:`) e, salvo dove sotto è scritto altro, con un codice diverso da 0 fermati: non riprovare in cerca di un esito diverso.

## 1. Worktree pulito, poi il controllo

Il controllo e la revisione rifiutano un albero con modifiche non committate. Controlla `git status`: se ci sono file del coordinatore non committati (piano, spec, note), committa prima quelli, poi prosegui. Non modificare codice dei task.

Lancia `<programma> finish check`: esegue il gate e le verifiche dei profili e stampa la Definition of Done voce per voce.

- **Uscita 1, rosso**: mostra all'utente tutte le voci `[no]` con il loro dettaglio e fermati. Le voci `[dopo la revisione]` non sono errori. Non correggere da solo: indica la riga «prossimo passo», che dice di correggere e rilanciare.
- **Uscita 2, rifiuto** (nessun lavoro attivo, fase sbagliata, PR già unita o chiusa senza merge): riporta le righe `rifiuto:` e fermati. Per una PR chiusa senza merge le due strade sono nel messaggio.
- **Uscita 0, verde**: la fase è `review`. Leggi la riga «prossimo passo»: in L0 è `finish open-pr` (vai al passo 3); in L1 e L2 è `review prepare` (passo 2).

## 2. Revisione finale (L1 e L2)

Ripeti fino a quando la riga «prossimo passo» è `finish open-pr`:

1. Lancia `<programma> review prepare`. Se esce con 1 il messaggio è su stderr (`tollgate: …`): riportalo. Un tetto di cicli raggiunto («… cicli di revisione già fatti») si scioglie solo con l'utente: indica `/tollgate:approve rounds <n>` o `/tollgate:approve unverified-review`; per un messaggio su fase o SHA («rilancia /tollgate:finish») di' all'utente di digitare di nuovo `/tollgate:finish`.
2. L'output ha una o più righe `agente: <tipo> brief: "<percorso>"` con, a volte, ` model: <m>`. Lancia **in primo piano** (mai `run_in_background`) un `Agent` per ogni riga: `subagent_type` = `<tipo>`, `prompt` = il `<percorso>` del brief, `model` solo se la riga lo indica. Le righe dello stesso stadio le lanci insieme, nello stesso messaggio. I revisori sono in sola lettura: aspetta che abbiano finito tutti.
3. Rilancia `<programma> review prepare`: passa allo stadio successivo (dal revisore al verificatore dei rilievi) oppure chiude il ciclo con `ciclo N chiuso: <esito>` e la riga «prossimo passo».

Come leggere la chiusura del ciclo:

- **`ok`**: «prossimo passo» è `finish open-pr`; esci dal ciclo.
- **`needs_fix`**: la fase torna `execution`. Lancia `<programma> task start --from-findings <N>` con `N` il numero del ciclo (stampa il brief del task di correzione), poi esegui il ciclo di `/tollgate:execute` su quel task (implementatore, revisione, `task done`). Quando il task è chiuso, chiedi all'utente di digitare di nuovo `/tollgate:finish`: serve un nuovo atto per la nuova versione.
- **`needs_you`** o un blocco aperto: fermati e di' all'utente cosa può fare. `/tollgate:resolve <id del blocco> <nota>` chiude il blocco; `/tollgate:approve finding <id> <gravità|dismiss> <motivo>` declassa o scarta un rilievo che ritiene sbagliato (poi rilanci `review prepare`); `/tollgate:approve rounds <n>` concede altri cicli o giri di correzione; `/tollgate:approve unverified-review` dichiara la revisione non verificata. Non decidere tu al posto dell'utente.

I verdetti dei revisori e dei verificatori li registra il hook: non riscriverli e non discuterli.

## 3. Apertura della PR

Lancia `<programma> finish open-pr` (con `--update` se il lavoro ha già una PR aperta e va solo aggiornata). Riporta l'URL stampato (`PR #N … : <url>`). Se rifiuta (uscita 1) stampa tutte le condizioni insieme come righe `rifiuto: …`: riportale così come sono e fermati; non aggirarle con `git push` o `gh`.

## Dopo la PR

La fusione della PR spetta all'utente, su GitHub. Se la base del ramo cambia nel frattempo, il riallineamento è `/tollgate:sync`; a fusione avvenuta, `/tollgate:cleanup` toglie ramo e worktree.
