---
name: finish
description: Chiude il lavoro: controllo locale della Definition of Done, revisione finale (L1, L2) e apertura della PR. Il coordinatore non scrive codice.
---

Sei il coordinatore della chiusura: lanci i comandi, lanci i revisori, leggi i verdetti. Il codice dei rilievi lo correggono gli implementatori di `/tollgate:execute`, non tu.

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.
Lancia i comandi dal **worktree del lavoro**.

L'atto `finish` lo registra il hook solo quando l'utente ha digitato `/tollgate:finish`. Se questa skill parte da un'altra strada e un comando rifiuta per mancanza dell'atto, di' all'utente di digitare `/tollgate:finish` e fermati.
Se il hook ha risposto «atto non registrato … vale solo in una sessione legata a un lavoro», la sessione non è legata (per esempio aperta dalla radice del checkout): di' all'utente di riprendere il lavoro con `/tollgate:start #<N>` (lega questa sessione) oppure di aprire Claude Code nel worktree del lavoro, poi di digitare di nuovo `/tollgate:finish`, e fermati. Ridigitarlo nella stessa sessione non cambia nulla.

**Regola ferma:** mai `git push` né `gh pr create` da Bash: la PR la apre soltanto `finish open-pr`, che spinge lo SHA giusto e la descrive dal DB.

**Codici d'uscita, per ogni comando:** riporta il messaggio così com'è (le righe `rifiuto:`, `avviso:`, `needs_you:`) e, salvo dove sotto è scritto altro, con un codice diverso da 0 fermati: non riprovare in cerca di un esito diverso.

## 1. Worktree pulito, poi il controllo

Il controllo rifiuta un albero con modifiche non committate. Come primo passo controlla `git status`:

- **Worktree non pulito** (file del coordinatore non committati: piano, spec, note): committa quei file, poi di' all'utente di digitare di nuovo `/tollgate:finish` e **fermati**. Un commit dopo l'atto lo fa decadere: l'atto nuovo è legato al nuovo HEAD, e senza di esso `finish open-pr` rifiuta alla fine, dopo tutto il lavoro di controllo e revisione. Non modificare codice dei task.
- **Worktree pulito**: prosegui con il controllo.

Lancia `<programma> finish check`: esegue il gate e le verifiche dei profili e stampa la Definition of Done voce per voce.

Il controllo usa lo stesso calcolo del gate su GitHub, in locale, e stampa tre tipi di riga, da non confondere:

- **Voci della DoD, `[sì]` o `[no]`**: sono le condizioni da soddisfare. `guard_scope`, `must_have` e `approvals` vengono dal calcolo del gate; le altre sono i comandi del gate, i profili e le ricevute.
- **Righe `rosso:`**: voci rosse del gate che non hanno una voce della DoD (per esempio il livello sotto il minimo, o file di tollgate modificati). Fermano il lavoro come un `[no]`: il codice d'uscita è 1.
- **Righe di `attenzione`**, in due gruppi: `da leggere:` (cambiano cosa garantisce la PR: deroghe, revisione non verificata, `approve unverified-tests`, must-have con test manuale, merge non verificati segnalati da `sentinel`, periodi con tollgate spento) e `informative:` (deroghe `scope` entro il secondo, `allow_no_tests`, task oltre la soglia, skill assenti, PR non `tg/*`). Non sono voci `[no]` e non cambiano il codice d'uscita: sul gate di GitHub `tollgate/attention` diventa rosso solo con una voce «da leggere». Riportale tutte, le `da leggere:` per prime e lascia all'utente la lettura. Non correggerle da solo e non trattarle come errori.

Ripetuto sullo stesso SHA in fase `review`, il comando non riesegue il gate: stampa l'esito salvato e le voci di `attenzione` come elenco di chiavi (`da leggere (voci del gate): …`, `informative (voci del gate): …`).

- **1, rosso**: mostra all'utente tutte le voci `[no]` con il loro dettaglio e fermati. Le voci `[dopo la revisione]` non sono errori. Le righe `rosso:` si riportano con le `[no]`; le righe di `attenzione` no, vedi sopra. Non correggere da solo: indica la riga «prossimo passo», che dice di correggere e rilanciare. In L2 la voce `approvals` `[no]` (spec e piano approvati, report dell'audit presenti) dice quale file di approvazione o quale report manca o non è più quello attuale: se la spec o il piano sono cambiati dopo l'approvazione, la via è `/tollgate:reopen spec` o `/tollgate:reopen plan` e un nuovo audit; un file di approvazione o un report non committato lo committi tu (il coordinatore) con `git add` e `git commit`, poi l'utente digita di nuovo `/tollgate:finish`; i file non si scrivono con Edit o Write.
- **2, rifiuto** (nessun lavoro attivo, fase sbagliata, PR già unita o chiusa senza merge): riporta le righe `rifiuto:` e fermati. Per una PR chiusa senza merge le due strade sono nel messaggio.
- **0, verde**: la fase è `review`. Leggi la riga «prossimo passo»: in L0 è `finish open-pr` (vai al passo 3); in L1 e L2 è `review prepare` (passo 2).

## 2. Revisione finale (L1 e L2)

Ripeti fino a quando la riga «prossimo passo» è `finish open-pr`:

1. Lancia `<programma> review prepare`. Se esce con 1 il messaggio è su stderr (`tollgate: …`): riportalo. Il tetto assoluto («8 cicli di revisione già fatti») si scioglie solo con l'utente e con una strada sola: `/tollgate:approve unverified-review` (`approve rounds` a quel punto rifiuta sempre); per un messaggio su fase o SHA («rilancia /tollgate:finish») di' all'utente di digitare di nuovo `/tollgate:finish`.
2. L'output ha una o più righe `agente: <tipo> brief: "<percorso>"` con, a volte, ` model: <m>`. Lancia **in primo piano** (mai `run_in_background`) un `Agent` per ogni riga: `subagent_type` = `<tipo>`, `prompt` = il `<percorso>` del brief, `model` solo se la riga lo indica. Le righe dello stesso stadio le lanci insieme, nello stesso messaggio. I revisori sono in sola lettura: aspetta che abbiano finito tutti.
3. Rilancia `<programma> review prepare`: passa allo stadio successivo (dal revisore al verificatore dei rilievi) oppure chiude il ciclo con `ciclo N chiuso: <esito>` e la riga «prossimo passo».

Come leggere la chiusura del ciclo:

- **`ok`**: «prossimo passo» è `finish open-pr`; esci dal ciclo.
- **`needs_fix`**: la fase torna `execution`. Se però l'output o `status` mostrano aperto il blocco «cicli di revisione esauriti» (tetto dei 4 cicli contati), la fase è `blocked` e `task start` rifiuta: **non lanciarlo**, fermati e indica all'utente `/tollgate:resolve <id del blocco>` (concede un ciclo) o `/tollgate:approve rounds <n>`; sbloccato, riprendi da qui. Altrimenti lancia `<programma> task start --from-findings <N>` con `N` il numero del ciclo (stampa il brief del task di correzione), poi esegui il ciclo di `/tollgate:execute` su quel task (implementatore, revisione, `task done`). Quando il task è chiuso, chiedi all'utente di digitare di nuovo `/tollgate:finish`: serve un nuovo atto per la nuova versione.
- **`needs_you`** o un blocco aperto: fermati e di' all'utente cosa può fare. `/tollgate:resolve <id del blocco> <nota>` chiude il blocco; `/tollgate:approve finding <id> <gravità|dismiss> <motivo>` declassa o scarta un rilievo che ritiene sbagliato (poi rilanci `review prepare`); `/tollgate:approve rounds <n>` concede altri cicli (solo per il blocco «cicli di revisione esauriti», tetto dei 4 cicli contati, entro il totale di 8) o giri di correzione di un task fermo; `/tollgate:approve unverified-review` dichiara la revisione non verificata e vale solo dopo 8 cicli. Non decidere tu al posto dell'utente.

I verdetti dei revisori e dei verificatori li registra il hook: non riscriverli e non discuterli.

## 3. Apertura della PR

Lancia `<programma> finish open-pr` (`--update` è facoltativo: richiede solo che la PR esista già; in fase `review` il comando aggiorna comunque una PR aperta). Se la fase è `pr_open` il comando rifiuta: prima il lavoro deve tornare in `execution` (con `/tollgate:sync` o con `start --reopen-execution`) e passare di nuovo da `finish check`. Riporta l'URL stampato (`PR #N … : <url>`). Se rifiuta (uscita 1) stampa tutte le condizioni insieme come righe `rifiuto: …`: riportale così come sono e fermati; non aggirarle con `git push` o `gh`.

## Dopo la PR

La fusione della PR spetta all'utente, su GitHub. Se la base del ramo cambia nel frattempo, il riallineamento è `/tollgate:sync`; a fusione avvenuta, `/tollgate:cleanup` toglie ramo e worktree.
