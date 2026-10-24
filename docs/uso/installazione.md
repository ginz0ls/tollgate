# Installazione

## Prima di cominciare

- Claude Code, Python 3.11 o più recente, `git` e `gh` autenticato.
- Superpowers, da 6.4.1 a 7.x compreso. tollgate lo dichiara come dipendenza in `plugin.json`, ma `/tollgate:start` controlla comunque la versione installata (la legge da `~/.claude/plugins/installed_plugins.json`) e rifiuta se manca o è fuori intervallo. Superpowers 8 richiede prima un aggiornamento di tollgate.
- Un repo con un remote GitHub e un ramo predefinito che ha almeno un commit.

## Il plugin

tollgate si distribuisce da un marketplace. Il file `.claude-plugin/marketplace.json` di questo repo definisce il marketplace `sainapse` con il plugin `tollgate`, e permette la dipendenza da `claude-plugins-official` (dove sta Superpowers). Aggiungi il marketplace a Claude Code, poi installa `tollgate@sainapse`, con i comandi `/plugin` di Claude Code o con `claude plugin`. Il passaggio esatto dipende da dove pubblichi il marketplace, quindi qui non c'è un indirizzo.

Per controllare il plugin prima di installarlo: `claude plugin validate` sulla cartella del repo.

## `/tollgate:setup`

La guardia del contesto (avviso e stop quando la sessione si riempie) legge la percentuale di contesto usata da un file che scrive la statusline. Un plugin non può impostare la statusline principale, quindi `/tollgate:setup` ti mostra la riga da mettere in `~/.claude/settings.json`, chiave `statusLine`:

- se hai già una statusline, la avvolge: `statusline/ctx` scrive la percentuale e poi esegue il tuo comando con lo stesso input;
- se non ne hai, usa `statusline/statusline.sh`.

Il file lo modifichi tu: la skill non scrive mai in `~/.claude/`. Il percorso del plugin contiene la versione, quindi la riga va rivista a ogni aggiornamento del plugin. Senza questo passo la guardia semplicemente non interviene.

## `/tollgate:init`

Prepara l'installazione del gate nel repo. Lo lanci dal checkout principale, e prima ti chiede due cose:

- i servizi che servono ai test (per esempio un database): nome, immagine ed eventuale porta;
- quanti merge al mese fai, per stimare i minuti di GitHub Actions (se non lo dici, assume 20).

Poi scrive la proposta in `docs/superpowers/tollgate-init/`:

- `README.md` con i passi, la modalità misurata, la stima dei minuti e il token separato;
- `files/` con l'albero da copiare: `tollgate.toml`, i cinque workflow `tollgate-{guard,run,verdict,base,sentinel}.yml` e `.github/tollgate/` (la copia della CLI, `VERSION`, `FINGERPRINT`);
- in modalità `protected` con la protezione da attivare, `protection.json` e `protect.sh`.

`init` non scrive mai su GitHub e l'agente non copia i file al posto tuo: i file di tollgate sono protetti dagli hook. I passi sono tuoi.

1. Copia `files/` nella radice del repo, per esempio `cp -R docs/superpowers/tollgate-init/files/. .`. Se `tollgate.toml` viene dal modello, compila prima `[commands]` (`setup`, `verify`, `report`).
2. Committa sul ramo predefinito e spingi, prima di attivare la protezione. Il push fa partire `tollgate-base`.
3. Solo in `protected` con protezione da attivare: quando `tollgate-base` è finito su quel commit, lancia `bash docs/superpowers/tollgate-init/protect.sh` dalla radice del repo, con le tue credenziali. Se il commit non è la punta di `origin/<ramo>`, passa lo SHA come primo argomento. Lo script legge da solo l'identificativo della sorgente degli stati e si ferma se non lo trova.
4. In `detect` non c'è niente da attivare.

Se `init` risponde "modalità non determinata", la protezione non si legge con le credenziali in uso (di solito il token dell'agente non ha l'amministrazione). Non sceglie `protected` per esclusione: rilancialo con le tue credenziali, per esempio digitando `!` seguito dal comando completo nel prompt di Claude Code. Come sceglie la modalità: [modalità](modalita.md).

## Il token dell'agente

Dai all'agente un token GitHub separato dal tuo, con permessi solo su contenuti, pull request e issue. Niente amministrazione e niente `project`. Con il tuo token l'agente potrebbe cambiare la protezione del ramo, e a quel punto i limiti di [limiti.md](limiti.md) sulle credenziali dell'utente diventano il caso normale.

Se usi jest, il `README.md` della proposta spiega anche la configurazione di jest-junit che mette il file nell'identificativo del test: con quella predefinita due test omonimi in file diversi si confondono.

## Dopo l'installazione

Apri un'issue e lancia `/tollgate:start #N` ([comandi](comandi.md)). Per spegnere tollgate su questa macchina c'è `/tollgate:off`, per riaccenderlo `/tollgate:on`. Il gate su GitHub resta attivo anche da spento.
