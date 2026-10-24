# Modalità del gate

Il gate gira in una di due modalità. Si scrive in `[gate] mode` di `tollgate.toml` e `init` la sceglie misurando il repo. Per cambiarla si passa da una PR `tollgate-config/*` ([emergenze e aggiornamenti](emergenze-e-aggiornamenti.md)).

## `protected`

Il ramo predefinito ha una protezione che richiede `tollgate/guard` e `tollgate/verdict` verdi, la PR obbligatoria, `strict` e regole valide anche per gli amministratori. La sorgente dei due controlli è fissata su GitHub Actions: uno stato pubblicato con un altro token, per esempio quello dell'utente o dell'agente, non conta e la PR resta bloccata.

Garanzia: una PR non entra nel ramo predefinito senza i due stati verdi e senza il tuo merge.

Il comando che attiva la protezione lo propone `init` (`protect.sh`) e lo lanci tu, con le tue credenziali, dopo che `tollgate-base` è girato sul commit d'installazione: lo script legge da lì l'identificativo della sorgente.

## `detect`

Gli stessi workflow, più `tollgate-sentinel` come unico controllo dopo il merge. Su un repo privato con GitHub Free la protezione del ramo non esiste, e nemmeno i rulesets: entrambe le API rispondono 403. Quindi il merge non è impedito, solo rilevato.

Garanzia: ogni commit che entra nel ramo predefinito senza `tollgate/guard` e `tollgate/verdict` verdi viene segnalato dopo, con uno stato `tollgate/sentinel` rosso sul commit e un'issue "tollgate: merge non verificato". Dopo ogni push controllato la sentinella scrive anche uno stato verde "controllato fino a qui", così un push saltato per errore (per esempio con `[skip ci]`) si controlla al push successivo.

Le issue le leggi e le chiudi tu su GitHub. `/tollgate:start` le mostra a ogni avvio, insieme a "modalità rilevazione: il merge non è impedito", e `/tollgate:status` ricorda che in `detect` il merge non è impedito, solo rilevato. In locale restano negati, come guardrail, il push sul ramo predefinito e `gh pr merge`.

## Come `init` sceglie

La lettura della protezione richiede il permesso di amministrazione, che il token consigliato per l'agente non ha, quindi la misura solo `init`, con le tue credenziali:

- 403 con il messaggio "Upgrade to GitHub Pro or make this repository public": `detect`.
- 200: `protected`. Se la protezione c'è già, `init` segnala i campi mancanti.
- 404 "Branch not protected": `protected`. Il ramo non è ancora protetto e `init` propone il comando.
- Qualunque altra risposta, rete assente compresa: "non determinata". `init` lo dice, rifiuta di scrivere e ti chiede di rilanciarlo con le tue credenziali. Non sceglie mai `protected` per esclusione.

Il piano dell'account non si usa: senza lo scope `user` GitHub non lo restituisce. Se il piano cambia, rilancia `init --update`.

## Cosa controlla il gate, in breve

`tollgate/guard` verifica che i file di tollgate siano uguali a quelli del ramo predefinito e che i workflow del progetto aggiunti nella PR non possano pubblicare stati. `tollgate/verdict` ricalcola da zero: comandi del gate, identificativi dei test della base (un test sparito o rotto è rosso), test-guard, scope contro il piano, coerenza con l'issue, approvazioni e report di L2. `tollgate/attention` raccoglie le voci da leggere: deroghe, tetti, componenti spenti. Se è rosso, vai a leggere il commento del gate sulla PR.
