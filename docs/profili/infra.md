# Regole del profilo infra di tollgate

Questa pagina è per te: dice quali sono le regole per la configurazione e il deploy su Vercel, Cloudflare e Docker e cosa hai deciso su sette punti dubbi. Le regole sono approvate e il profilo si può accendere.

Approvata dall'utente il 2026-11-07.

## Cosa sono

Sono dodici regole in più rispetto a quelle di base. Valgono solo per i file che decidono come un progetto viene messo online: la configurazione di Vercel, quella di Cloudflare e i file di Docker. Dicono, per esempio, di non scrivere mai una chiave segreta in un file del repo, di non lanciare un deploy vero durante un task e di controllare la sintassi di un comando sulla pagina ufficiale invece che a memoria.

Qualche parola, la prima volta che serve:

- **Deploy**: mettere online una nuova versione del progetto.
- **Vercel**: un servizio che ospita siti e applicazioni web. Il suo file di configurazione si chiama `vercel.json` (oppure `vercel.toml` o `vercel.ts`).
- **Cloudflare e Wrangler**: Cloudflare ospita codice che gira in rete (i «Worker»). Wrangler è il suo programma da riga di comando; la sua configurazione è `wrangler.jsonc` (oppure `wrangler.json` o `wrangler.toml`).
- **Docker**: impacchetta un programma in una «immagine» che gira uguale su qualunque macchina. Il `Dockerfile` è la ricetta dell'immagine; i file compose (`compose.yaml` e simili) descrivono più immagini che girano insieme.
- **`vars`, `ENV`, `ARG`**: i punti dove si scrivono le variabili. `vars` sta nella configurazione di Wrangler; `ENV` e `ARG` stanno in un Dockerfile (`ENV` resta dentro l'immagine, `ARG` è un valore passato alla build).
- **`npx`**: un programma di Node che scarica ed esegue al volo un altro programma. `pnpm`, `yarn`, `bun` e `npm exec` fanno lo stesso: li chiamo «lanciatori».
- **CI**: i controlli che GitHub fa in automatico a ogni modifica, descritti nei file di `.github/workflows/`.
- **Terraform, nginx, systemd**: Terraform descrive un'infrastruttura in file `.tf`; nginx è un server web e systemd gestisce i programmi di un server Linux, ognuno con i suoi file di configurazione.
- **`backend`**: il profilo, ancora da scrivere, per il codice che gira sul server.
- **Segreto**: una chiave, un token o una password. Non deve stare in un file che finisce nel repo, perché chiunque legga il repo la vedrebbe.
- **Modalità di prova (dry-run)**: un comando che fa tutto il lavoro tranne l'ultimo passo, la pubblicazione. Serve a controllare che il deploy funzionerebbe, senza farlo.
- **`compatibility_date`**: la data che dice a Cloudflare con quale versione delle sue regole deve girare il Worker.
- **Tag e digest**: il tag è il nome di una versione di un'immagine (può essere spostato dal suo autore); il digest è un'impronta che indica quell'immagine precisa.
- **Build a stadi**: un Dockerfile che compila in uno stadio e copia nell'immagine finale solo il risultato, così l'immagine resta piccola.

Valgono per chi scrive il codice e per chi lo rivede. Chi scrive può essere un agente a cui è affidato un task, cioè un pezzo del lavoro. Può essere anche Claude Code che lavora direttamente con te.

Chi rivede guarda tre cose. Il «diff» è l'elenco delle righe cambiate. Il «report» è il resoconto che l'agente scrive alla fine. La «nota di ricerca» è l'elenco di cosa ha letto prima di scrivere. Per ogni regola chi rivede risponde sì o no. La colonna «Si giudica su» dice su quale delle tre guarda: la regola 4, per esempio, si giudica sul solo diff.

## Quando si accende

Il profilo non si accende da solo. Si accende solo in un progetto dove il comando `/tollgate:init` lo propone e tu copi il blocco proposto nel `tollgate.toml` del progetto. Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate la riceve con `/tollgate:init --update`. In tutti e due i casi la copia nel `tollgate.toml` la fai tu. Vale a partire dal livello L1, cioè dai lavori medi: i lavori piccoli (L0) non lo usano.

`init` lo propone se nel progetto trova uno di questi file, a qualunque profondità, o la cartella `infra/` alla radice:

- Vercel: `vercel.json`, `vercel.toml`, `vercel.ts`.
- Cloudflare: `wrangler.toml`, `wrangler.json`, `wrangler.jsonc`.
- Docker: `Dockerfile` (anche con un suffisso dopo il nome), `.dockerignore`, `compose.yaml`, `compose.yml`, `compose.override.yaml`, `docker-compose.yaml`, `docker-compose.yml`.
- La cartella `infra/` alla radice del progetto, con tutto ciò che contiene.

Cosa non lo accende, e perché:

- I workflow di GitHub: i file in `.github/workflows/` non accendono nessun profilo, `infra` compreso. Restano del controllo di tollgate sulla CI. Le regole di `infra` chiedono comunque di leggerli prima di parlare di deploy (regola 1). Un task che cambia solo un workflow di deploy va all'agente generico.
- Il codice dei Worker: è codice dell'applicazione, non configurazione, e spetta al profilo `backend` quando ci sarà.
- Un `Dockerfile` con il nome nella forma che usa la documentazione di Docker, `<qualcosa>.Dockerfile` (per esempio `app.Dockerfile`), non accende `infra`: il pattern copre `Dockerfile` e i nomi che cominciano con `Dockerfile`, non quelli che finiscono così. Anche `<nome del Dockerfile>.dockerignore`, il file da ignorare scritto accanto a quel Dockerfile, non accende il profilo; `.dockerignore` nella radice sì. `compose.override.yaml`, invece, lo accende.
- Terraform (`*.tf`) e i file di un server tuo (nginx, systemd): per ora nessuna regola li copre.
- `.vercel/`: non è un file del repo (lo crea il collegamento del progetto a Vercel e contiene dati del tuo account), quindi non si legge e non si committa. La regola 1 parla dei file versionati.

Un file che cambia quando il profilo è già acceso lo prende l'agente di `infra`. Un file nuovo, anche nella stessa cartella, non è coperto finché non applichi la riga che `/tollgate:init --update` ti propone.

## Le regole

| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |
|---|---|---|---|---|
| 1 (R-INFRA-01) | Prima di scrivere sul deploy, il report nomina i file di deploy versionati che ha letto (configurazione di Vercel e di Wrangler, Dockerfile, file compose, workflow in `.github/workflows/`) e dice dove gira oggi il progetto. | sì | il report | Una proposta del progetto di B che hai rivisto (sezioni 3.4 e 11). La parte «dice dove gira oggi» è una scelta nostra. |
| 2 (R-INFRA-02) | Un comando o un'opzione di `vercel`, `wrangler`, `docker` o `docker compose` che il lavoro scrive ha nel report l'indirizzo della pagina ufficiale che lo descrive. Vale anche per un comando dato come fatto nel report. | sì | il report | La proposta del progetto di B che hai rivisto, per Wrangler e Vercel, la skill `wrangler` di Cloudflare e le pagine dei comandi. Per Docker è una scelta nostra. |
| 3 (R-INFRA-03) | Una proprietà scritta in `vercel.json`, `vercel.toml`, `vercel.ts` o in un file di Wrangler ha nel report l'indirizzo della pagina ufficiale che la descrive. | sì | il report | Le pagine di configurazione di Vercel e di Cloudflare e la skill `wrangler`. |
| 4 (R-INFRA-04) | Un progetto Vercel ha un solo file di configurazione. Il lavoro non aggiunge un secondo file di Vercel in una cartella che ne ha già uno. | sì | il diff | Le pagine di configurazione di Vercel (`vercel.json` e `vercel.ts`). |
| 5 (R-INFRA-05) | Nessun segreto nei file versionati: non in `vars` di Wrangler, non in `env` o `build.env` di Vercel, non in `ENV` o `ARG` di un Dockerfile. I segreti passano dalle impostazioni dei servizi o, per la build di Docker, dall'opzione `secret` letta da un `RUN`; li imposta l'utente. Un valore come `"@nome"` in `env` di Vercel è il riferimento a un segreto già salvato su Vercel, non un segreto: non conta come difetto. | sì | il diff | Le pagine di Cloudflare, di Vercel e di Docker sui segreti. |
| 6 (R-INFRA-06) | I file dei segreti locali (`.dev.vars*`, `.env`, `.env.*`) non entrano nel diff, salvo quelli che finiscono in `.example`, `.sample` o `.template`, che sono modelli senza valori veri. Se il lavoro aggiunge codice che li usa, `.gitignore` li esclude. | sì | il diff | La pagina dei segreti di Cloudflare. L'eccezione dei modelli è una scelta nostra. |
| 7 (R-INFRA-07) | Una configurazione di Wrangler nuova usa `wrangler.jsonc` e, in `compatibility_date`, la data del giorno in cui nasce. | no | il diff | Le pagine di configurazione e delle date di compatibilità di Cloudflare. |
| 8 (R-INFRA-08) | Se il lavoro cambia una `compatibility_date` già presente, il report dice di aver letto la pagina che spiega cosa cambia con la data nuova. | no | il report | La pagina delle date di compatibilità di Cloudflare. |
| 9 (R-INFRA-09) | L'immagine di base di un Dockerfile ha una versione fissata (un tag preciso o un digest), non `latest` né il solo nome. | no | il diff | La pagina di Docker sulle buone pratiche. |
| 10 (R-INFRA-10) | Un Dockerfile nuovo per un servizio che non ha bisogno di privilegi passa a un utente non amministratore con `USER`, e ha un `.dockerignore` nella radice del contesto di build (la cartella da cui Docker prende i file), oppure un file `<nome del Dockerfile>.dockerignore` accanto al Dockerfile. | no | il diff | Le pagine di Docker sulle buone pratiche e sul contesto di build. |
| 11 (R-INFRA-11) | Un Dockerfile che compila separa la build dall'immagine finale con una build a stadi. | no | il diff | La pagina di Docker sulle buone pratiche. |
| 12 (R-INFRA-12) | Il lavoro non pubblica e non cambia un servizio. Il report dice quale prova senza pubblicazione ha eseguito (per esempio un deploy di Wrangler in modalità di prova, o `vercel build` in un progetto collegato), dopo l'approvazione che tollgate ti chiede, oppure perché non l'ha fatta. Non riporta comandi che pubblicano o cambiano un servizio (deploy, pubblicazione in produzione, `secret`, `env add`) lanciati da lui. | sì | il report | La spec di tollgate (gli effetti esterni sono negati finché non li approvi) e le pagine dei comandi di Cloudflare e di Vercel. |

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. Le altre sono segnalate ma non lo fermano. Un difetto viene segnalato una sola volta.

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/infra-fonti.md`. La verifica ha anche controllato, su una pagina ufficiale, ogni nome di file che accende il profilo.

## Cosa cambia per i comandi

Tre cose da sapere, perché toccano il tuo modo di lavorare.

**Un comando di prova del deploy lo aggiungi tu, a mano.** Il profilo parte senza un comando nella definizione di «fatto» (la lista `dod` del profilo, cioè i controlli che devono essere verdi a fine lavoro). Un comando scritto da tollgate fallirebbe in ogni progetto dove Wrangler non è installato o Vercel non è collegato. Se vuoi un controllo del deploy, lo scrivi nel `tollgate.toml`, per esempio così, per un Worker con Wrangler installato:

```
[profiles.infra]
commands = { deploy-check = "npx wrangler deploy --dry-run" }
dod = ["deploy-check"]
```

Attenzione: i comandi di `dod` li lancia tollgate stesso a fine lavoro, senza chiedere e senza nessun controllo sugli effetti, e con le credenziali che hai salvato sul computer con `wrangler login` o `vercel login`. Un `deploy` scritto lì senza `--dry-run` pubblicherebbe davvero a ogni controllo di fine lavoro, senza che nulla lo fermi. La regola 12 riguarda i comandi lanciati dall'agente, non questi. Un comando aggiunto a mano in `dod` che non produce un report dei test conta verde solo se nel `tollgate.toml` c'è `[project] allow_no_tests = true`, oppure se approvi con `/tollgate:approve unverified-tests`.

**I comandi dei servizi chiedono la tua approvazione, anche con `npx`.** Da questa versione tollgate riconosce `vercel`, `wrangler`, `docker push` e simili anche quando sono scritti dietro `npx`, `pnpm`, `yarn`, `bun` o `npm exec`, e chiede la tua approvazione come per il comando nudo. Dentro il controllo ricadono anche alcuni comandi che lavorano solo in locale:

- di Supabase: `npx supabase migration new`, `functions new`, `functions serve`, `db reset`, `db lint`. Il profilo del database (B7) restringerà l'elenco ai soli comandi che toccano davvero un servizio;
- di Vercel: `npx vercel dev`, `build`, `pull`, `--version`, come già succedeva senza `npx` (ogni `vercel` chiede);
- un argomento che è soltanto il nome di un servizio: `npx vitest run vercel` chiede l'approvazione anche se non lancia Vercel; lo stesso vale per `npm docs vercel`, `npm help vercel` e `npm config vercel`.

Costo: qualche conferma in più nei progetti con questi nomi. Il vantaggio è che un deploy non parte per un giro di parole.

**Restano scoperti alcuni giri rari**, che un controllo sul testo non chiude: opzioni scritte prima del sottocomando (`wrangler --env prod deploy`), `docker build` con `--push` e le scritture remote di `wrangler kv`, `d1`, `r2`. Per questi la difesa vera è che il progetto di lavoro non abbia credenziali dei servizi.

## Cosa hai deciso

Su sette punti la fonte non diceva proprio quello che la regola chiede, o la scelta era tua. Hai tenuto la proposta in tutti e sette.

1. **Regola 1 (R-INFRA-01), «dice dove gira oggi il progetto».** Le due sezioni del progetto di B chiedono solo di leggere i file di deploy prima di parlare di deploy. Dire dove gira il progetto è una nostra aggiunta, perché chi rivede possa controllare che l'agente abbia capito il contesto. Hai deciso di tenerla.
2. **Regola 2 (R-INFRA-02), Docker.** La proposta del progetto di B che avevi rivisto nomina Wrangler e Vercel, non Docker. La regola vale anche per `docker` e `docker compose`, perché Docker è in `infra`. Hai deciso di tenere l'estensione.
3. **Regola 5 (R-INFRA-05), i file compose.** La regola non parla dei segreti nei file compose, perché nessuna delle pagine raccolte ne dice qualcosa. Hai deciso di lasciarla così.
4. **Regola 6 (R-INFRA-06), i file modello.** L'eccezione per `.example`, `.sample` e `.template` è una scelta nostra: un modello senza valori veri non va protetto. Hai deciso di tenerla, quindi un `.env.example` non viene fermato.
5. **Le cartelle di GitHub.** Le cartelle `.github/workflows/` e `.github/actions/` non accendono nessun profilo: un `Dockerfile` dentro un'azione di GitHub non propone `infra`. Hai deciso di tenere così.
6. **Un cambio per il profilo `ai`.** Un file `.md` o `.txt` (e simili: `mdx`, `markdown`, `rst`, `adoc`) non accende più un profilo dalla cartella in cui sta. Una cartella `prompts/` con soli modelli di prompt in `.md` o `.txt` non riceve più la proposta `ai`; la pagina già approvata di `ai` non cambia. Hai deciso di lasciare così, e `txt` resta tra i documenti.
7. **Regola 5 (R-INFRA-05), «li imposta l'utente».** Che i segreti li imposti tu e non l'agente non viene da una pagina: è una scelta nostra, coerente con la regola di tollgate che nega all'agente gli effetti sui servizi. Hai deciso di tenerla.

## Regole tolte dalla verifica

Nessuna regola è uscita: ciascuna ha almeno una fonte che regge, e ogni nome di file che accende il profilo è stato ritrovato su una pagina ufficiale. Quattro fonti non reggevano del tutto e sono state corrette nel testo delle regole: un riferimento al progetto di B che non conteneva ciò che la regola chiede, l'estensione a Docker presa dal progetto di B, un'altra sezione dello stesso progetto che non parla delle proprietà dei file di configurazione, e un fatto sui segreti di Wrangler attribuito alla pagina sbagliata. Nei primi due casi la parte in più è ora dichiarata come scelta nostra, nel terzo la sezione è stata tolta dalle fonti, nel quarto il fatto è stato spostato sulla pagina giusta.

## Se vuoi cambiare qualcosa

Per ogni regola puoi dirmi una di queste tre cose.

- **Va bene così.** La regola resta com'è.
- **Cambiala.** Dimmi cosa cambiare. Una regola cambiata nel senso o con una fonte nuova passa di nuovo dal controllo delle fonti.
- **Toglila.** La regola esce e il suo numero non si riusa: le altre tengono il loro.

I numeri delle regole, ora che sono approvate, non cambiano più. Se vorrai cambiare, aggiungere o togliere una regola, me lo dici e la sistemo.
