# Emergenze e aggiornamenti

## Aggiornare tollgate

Quando aggiorni il plugin, la copia della CLI e i workflow nel tuo repo restano alla vecchia versione. `/tollgate:start` lo nota (versione di `.github/tollgate/VERSION` diversa da quella del plugin) e consiglia `init --update`.

1. Lancia `/tollgate:init --update` dal checkout principale. Propone solo i file che differiscono dal ramo predefinito, e dice cosa cancellare. Se non c'è niente di diverso scrive "nulla da aggiornare".
2. Crea tu il ramo `tollgate-config/<versione>` dal ramo predefinito, copia i file della proposta, cancella quelli elencati in "Da cancellare", committa e apri tu la PR. L'agente non scrive i file di tollgate.
3. La PR deve venire dallo stesso repo (non da un fork) e contenere solo file di tollgate e file sotto `.tollgate/waivers/`. Con qualunque altro file `guard` è rosso.

Per questa corsia `guard` passa, test-guard e scope non si applicano e `attenzione` è sempre rosso, come previsto. Il riepilogo mostra le chiavi di `tollgate.toml` cambiate e l'impronta della CLI (`.github/tollgate/FINGERPRINT`, lo `sha256` di `bin/`) di testa e base: è il punto da leggere prima del merge.

## Aggiornare le azioni fissate

Ogni `uses:` dei cinque workflow del gate è fissato per SHA, nella forma `<azione>@<SHA di 40 caratteri> # <tag>`. La fonte unica è `gate/workflows/PINS`, una riga per azione: `<azione> <tag> <sha>`. Lo SHA è quello del commit del tag, con i tag annotati già dereferenziati. Le azioni sono `actions/checkout`, `actions/cache` (`restore` e `save`), `actions/upload-artifact`, `actions/download-artifact` e `actions/setup-python`. Lo stesso vale per `.github/workflows/ci.yml` del plugin.

Per portare un'azione a un tag nuovo:

1. Trova lo SHA del commit del tag sul repo pubblico dell'azione, per esempio con `git ls-remote` sul tag (per un tag annotato prendi la riga `^{}`, cioè il commit, non l'oggetto tag).
2. Aggiorna la riga in `gate/workflows/PINS`.
3. Aggiorna lo SHA e il commento nei workflow di `gate/workflows/` che usano l'azione, e in `.github/workflows/ci.yml` se la usa.
4. Lancia la suite: `tests/test_gate_workflows.py` controlla che ogni `uses:` sia fissato, che il commento coincida con `PINS` e che non resti nessun `@v`.
5. Porta la modifica nei progetti con `init --update`, come sopra.

Chi vuole che GitHub rifiuti le azioni non fissate può attivare l'impostazione `sha_pinning_required` del repo.

## Il gate è guasto

Se un bug del gate o di un workflow blocca ogni PR (stati `error`, un workflow che non parte), solo tu puoi risolvere, con questi tre passi nell'ordine:

1. Disattivi i controlli obbligatori della protezione del ramo.
2. Fai il merge della PR di riparazione.
3. Riattivi i controlli.

In `detect` non c'è niente da disattivare. Il merge di riparazione fa scattare `tollgate-sentinel`: l'issue "tollgate: merge non verificato" è attesa, e la chiudi tu dopo averla letta. Se il gate non può proprio girare, `start` lo segnala (per esempio "GitHub Actions spente: il gate non gira").

Una PR in volo durante il merge che cambia `tollgate.toml` riceve `error` "configurazione del gate cambiata dopo il run: rilancia i controlli". Un merge che non tocca `tollgate.toml` non la disturba.

## Hotfix urgente

Una PR fatta a mano da un ramo che non è `tg/*` ottiene i controlli sui test e `attenzione` rosso: è la corsia d'emergenza dichiarata, senza scope e senza revisione di tollgate. Falla fuori da Claude Code, o da una sessione non legata a un lavoro: in una sessione legata a un lavoro il push di altri rami è negato.

## Il DB locale è guasto

Se `tollgate status` risponde che il database non è integro, ripristina l'ultima copia da un terminale: `python3 <percorso>/bin/tollgate db restore`. Chiede conferma e rifiuta se il DB è sano.

Per spegnere tollgate su una macchina senza toccare il gate: `/tollgate:off [ore]`, poi `/tollgate:on`.
