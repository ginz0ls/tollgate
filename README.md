# tollgate

tollgate è un plugin per Claude Code che porta un lavoro da un'issue GitHub a una PR verificata. Il merge lo fa sempre una persona, su GitHub.

Lavora su due livelli.

- I guardrail locali sono hook di Claude Code. Fermano subito le scorciatoie dell'agente: test modificati per farli passare, "fatto" dichiarato senza prove, file fuori dallo scope del piano, effetti esterni non approvati, codice scritto dal coordinatore.
- Il gate su GitHub sono cinque workflow che ricalcolano da zero i fatti della PR e pubblicano gli stati `tollgate/guard` e `tollgate/verdict`.

I guardrail locali non fermano un agente che lavora apposta per aggirarli. Il gate sì, nei limiti descritti in [limiti.md](docs/uso/limiti.md): leggili prima di fidarti del verde.

## Cosa serve

- Claude Code e il plugin Superpowers (tollgate lo richiede come dipendenza, versione da 6.4.1 a 7.x).
- Python 3.11 o più recente e `git`.
- `gh` autenticato e un repo con remote GitHub.
- Per il gate: un repo su cui puoi aggiungere workflow e, se vuoi la modalità `protected`, una protezione del ramo (non esiste su un repo privato con GitHub Free: lì tollgate usa la modalità `detect`).

## Avvio rapido

1. Installa il plugin e avvia Claude Code nel repo ([installazione](docs/uso/installazione.md)).
2. Scrivi `/tollgate:setup` una volta, per alimentare la guardia del contesto.
3. Scrivi `/tollgate:init`. Misura la modalità del gate e prepara una proposta in `docs/superpowers/tollgate-init/`. I file li copi e li committi tu.
4. Apri un'issue e scrivi `/tollgate:start #N`. tollgate crea il worktree, sceglie il livello (L0, L1 o L2) e ti porta al passo giusto.
5. Alla fine scrivi `/tollgate:finish`: controllo locale, revisione finale, PR. Il merge lo fai tu.

## Documentazione

- [Installazione](docs/uso/installazione.md): dipendenze, marketplace, `/tollgate:setup`, `/tollgate:init`, token separato.
- [Comandi](docs/uso/comandi.md): ogni skill con i suoi argomenti, e la CLI.
- [Modalità del gate](docs/uso/modalita.md): `protected` e `detect`.
- [Limiti della garanzia](docs/uso/limiti.md): cosa tollgate non copre.
- [Emergenze e aggiornamenti](docs/uso/emergenze-e-aggiornamenti.md): aggiornare tollgate e le azioni fissate, gate guasto, hotfix.
- [Eval e CI](docs/uso/eval-e-ci.md): come si lanciano gli eval e cosa prova la CI del plugin.

La specifica completa è in `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`.

## Licenza

MIT. Le parti derivate da Superpowers sono citate in `LICENSES/`.
