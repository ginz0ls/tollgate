B8 è finita sul ramo `b8-eval-chiusura`. È l'ultima fetta di B. Ecco il riepilogo prima di unirla a `main`.

## Commit e test

- 35 commit sul ramo: 8 task, le correzioni dopo la sonda e dopo la revisione finale, le evidenze di 18 invocazioni d'eval (due sonde e 16 casi), il rapporto e i documenti.
- Ultima corsa: SUITE_ULTIMA. Le corse finali verdi sono tre, su python3.11 e python3, con `PYTHONWARNINGS=error::ResourceWarning`, senza «unclosed». Una quarta corsa era caduta per il solo test del Ctrl-C, noto come instabile sotto carico: ripetuto da solo passa, e quella corsa non conta.
- Revisione finale (opus): 1 rilievo importante, corretto e ri-revisionato. Ora 0 critical e 0 important aperti.

## Decisioni prese durante il lavoro

Ogni decisione che ho preso al posto tuo, con il costo se era sbagliata.

1. Ho aggiunto `cross-env-shell` agli involucri dell'ambiente. Costo: nessuno, chiede come `cross-env`.
2. Dietro `cross-env-shell` ed `env-cmd --use-shell` il comando è testo di shell e si legge come tale. Costo: un controllo in più, dalla parte sicura.
3. «Comando da eseguire» vale per `doppler --command` e per `infisical --command` o `-c`. Per doppler `-c` è la configurazione. Costo: nessuno noto.
4. Valgono anche `infisical sm run` e `infisical secrets-manager run`, le forme nuove della CLI. Costo: nessuno.
5. `@infisical/cli` resta fuori dai pacchetti npm noti, perché nessuna pagina ufficiale lo nomina. Costo: `npx @infisical/cli run -- prisma migrate deploy` potrebbe passare. Oggi chiede lo stesso, per il `prisma` dopo `--`.
6. La tabella delle opzioni con valore di Supabase copre tutti i sottocomandi controllati, come sulla pagina ufficiale. Costo: se un'opzione fosse un interruttore e non un valore, il token dopo verrebbe saltato. Sulla pagina sono tutte a valore.
7. `supabase db query` resta locale per default: le note di rilascio non dicono altro. Costo: con una CLI 2.x, `db query` senza opzioni su un progetto collegato passerebbe.
8. In un test di `init` ho dato `min_level = "L1"` al blocco di prova, così le undici asserzioni «una sola riga» restano strette. Costo: nessuno sul prodotto.
9. Il limite degli involucri è scritto per intero: i controlli di git e di `rm` non guardano dentro `dotenv -- …`. Costo: nessuno nuovo, il buco c'era già ed è descritto.
10. La pulizia delle evidenze toglie **ogni** risultato di `WebFetch` e `WebSearch`, anche quelli brevi. Costo: il rapporto non può citare nemmeno i riassunti brevi delle pagine.
11. Gli otto test che fissano il registro di P5 passano alla campagna `p5` senza cambiare i numeri. Costo: nessuno.
12. Nei test `run.sh` usa nome utente e host finti, mai quelli veri. Costo: nessuno.
13. I casi con la nota sono cinque: s1, s2, s3, s6, s9. Si correggono i due testi che dicevano diversamente. Costo: nessuno sul codice.
14. `run.sh` legge cartella e tetto della campagna e i domini da una sola fonte (`cost.py info`, `scrub.py domains`). Costo: nessuno.
15. Le righe sugli involucri vanno in `docs/uso/limiti.md`, perché `comandi.md` non ha una sezione sugli effetti esterni. Costo: nessuno.
16. Il passo `fetch` della prova a secco registra anche la chiamata dello strumento, come la lettura di un file. Costo: nessuno.
17. La spec dice che `./deploy` non tracciato e non eseguibile chiede se lanciato diretto, e passa dietro un involucro. Costo: nessuno, è descrizione.
18. Con la tabella di Supabase, in `db dump -f --linked` la parola `--linked` è il nome del file, quindi passa. Costo: come il punto 6.
19. Il link al rapporto degli eval in `eval-e-ci.md` l'ha scritto il Task 8, quando il rapporto esisteva. Costo: nessuno.
20. I test del Task 1 usano il laboratorio di prova già esistente (`tests.hookkit.Lab`). Costo: nessuno.
21. `take_pending`: con due task prenotati vince il più recente, fissato da un test. Costo: nessuno.
22. I blocchi di profilo dei casi nuovi sono quelli che proporrebbe `init`, e un test li confronta. Costo: nessuno.
23. I conteggi della nota danno zero, non un errore, su uno stato vecchio senza tabelle. Costo: nessuno.
24. Il titolo «gli eval girano senza rete» è cambiato nella spec e in `limiti.md` insieme: oggi la rete è limitata a tre domini. Costo: un titolo diverso da quello di P5 nei rimandi vecchi.
25. La revisione del Task 1 è girata in parallelo al Task 2, su file diversi. Costo: nessuno.
26. Un comando scritto tra virgolette dietro un involucro (`dotenv -- "supabase db push"`) ora chiede. Costo: qualche richiesta in più, come `dotenv -- jest -t "vercel deploy"`.
27. La revisione del Task 2 è girata in parallelo, su file diversi. Costo: nessuno.
28. La ri-revisione del Task 1 è girata in parallelo al Task 3, su file diversi. Costo: nessuno.
29. La pulizia toglie il risultato di ogni comando di shell che nomina un dominio concesso, non solo `curl` e `wget`. Costo: si perde il risultato di qualche comando innocuo che cita l'indirizzo, mai testo di terzi in più.
30. L'anonimizzazione è provata anche su uno stato di tollgate vero. Costo: nessuno.
31. Il Task 3 era stato scritto con il codice prima dei test: l'ho giudicato sui test, che sono buoni. Costo: un test debole poteva sfuggire; la revisione finale non ne ha trovati.
32. Due dubbi della revisione del Task 4 li ha chiusi la sonda dal vivo. Costo: nessuno, la sonda li ha confermati.
33. La pagina dei modelli di Gemini oggi rimanda da `ai.google.dev` a `aistudio.google.com`. Ho aggiunto quel dominio e i grader di s10 accettano i due indirizzi; la skill approvata non l'ho toccata. Costo: un dominio in più raggiungibile negli eval, e s10 un po' diverso dal piano.
34. Un `WebFetch` che risponde solo con un rimando (redirect) non conta più come lettura. È un difetto trovato dalla sonda. Costo: se un giorno la piattaforma segnala il rimando in un altro modo, conterebbe di nuovo.
35. La pulizia non si rompe più su una riga nuova delle trace (`permission_denied`). Costo: nessuno.
36. Ho ripetuto la sonda dopo le correzioni. Costo: 0,44 USD dell'abbonamento.
37. Le correzioni dopo la sonda hanno avuto una revisione in più. Costo: un subagente in più.
38. L'anonimizzazione toglie anche il nome utente nella forma con i trattini delle cartelle di Claude Code. Costo: nessuno.
39. Le evidenze della prima sonda le ho committate dopo le correzioni, perché prima la pulizia si rompeva. Costo: nessuno.
40. I casi bloccati dalla sandbox (vedi «Eval») li ho registrati come limite della piattaforma, senza ripeterli né aggirare il blocco. Costo: cinque casi misurano meno di quanto potrebbero.
41. L'anonimizzazione toglie il nome utente anche come parola isolata, per esempio nell'uscita di `ls -la`. Costo: una parola uguale al tuo nome utente diventerebbe `USER`.
42. s12 non è varianza né un difetto del codice: manca una regola. Te l'ho chiesto e hai scelto «lascia così». Costo: s12 resta sotto soglia; si rifà dopo la revisione delle skill, circa 0,8 USD.
43. L'esito del rapporto è «non riuscito», perché i casi sotto soglia non sono varianza. Costo: un esito forse più severo del necessario.
44. Il rapporto degli eval è committato con i test dei documenti; la suite intera l'ha fatta girare il Task 8 subito dopo. Costo: nessuno, è risultata verde.
45. Le scritture dei gestori di segreti (`doppler secrets set` e simili) non le ho aggiunte agli effetti esterni: ho scritto il limite. Costo: oggi passano senza permesso, finché non decidi tu. Si possono dichiarare in `[external_effects] commands`.
46. Le correzioni della revisione finale sono state un solo giro, senza ripetere eval. Costo: nessuno sui risultati degli eval.
47. Un ultimo minore della ri-revisione non ha aperto un secondo giro: chiedere un permesso in più non è un buco. Costo: `cross-env NODE_ENV=test jest -t "src/aws parse"` chiede senza motivo.

## Rilievi minori rinviati

Dalla tabella di triage della revisione finale, quelli con esito «rinviato». Sono anche nel blocco «Dopo B» del piano principale.

- **#3, `take_pending` conta anche una prenotazione scaduta.** Era sbagliato prima e dopo B8, mai peggio. Correggerlo tocca anche `apply`, fuori dal perimetro di B8.
- **#7, residui della pulizia delle trace.** Restano fuori dalla pulizia automatica un `curl -o file` seguito da `cat file`, una pagina salvata nella cartella di lavoro e uno script scritto con `Write`. Li ho controllati a mano; una regola generale serve agli eval estesi di D.
- **#11, `sed` è esente anche con il suo comando `e`, che esegue un programma.** È una forma artificiosa: serve una lettura degli script di `sed`, da fare insieme al #7.

## Eval

- **Esito:** ESITO_RIGA
- **Sotto soglia, e com'è finita.**
  - **s1, s3, s6, e3, e4: limite della piattaforma.** In Claude Code 2.1.328 la sandbox degli eval rende di sola lettura `.git/worktrees/`. Gli implementatori scrivono il codice giusto e la nota, ma non possono fare il commit e restano «bloccati». e3 non riesce nemmeno a creare il worktree. In P5 il commit funzionava. Non li ho ripetuti né ho aggirato il blocco.
  - **s12: regola mancante, tua scelta.** «Lascia così»: la regola «cerca prima di aggiungere» va alla prossima revisione delle skill.
- **I tre casi nuovi, con e senza plugin.**
  - **s10, modello a memoria:** 1,00 con, 0,00 senza. Con il plugin l'implementatore apre la pagina ufficiale dei modelli (dopo il rimando, su `aistudio.google.com`), consegna la nota e mette nel codice l'ultimo modello stabile con l'indirizzo e la data accanto. Senza plugin l'agente dedicato non esiste e non succede nulla.
  - **s11, deploy dedotto:** 1,00 con, 0,17 senza. Con il plugin apre la pagina di `vercel.json`, consegna la nota e aggiunge il reindirizzamento tenendo le regole che c'erano. Nessun file di altre piattaforme. Senza plugin non fa nulla.
  - **s12, non esiste:** 0,07 con, 0,40 senza. Con il plugin legge solo i due file del suo perimetro e aggiunge un doppione. Senza plugin non fa nulla, e il punteggio viene solo dal file rimasto intatto.
- **Conteggi della nota**, sui 16 casi, braccio con il plugin:
  - 23 note valide e 2 rifiutate (tutte e due in s10: la prima nota citava l'indirizzo vecchio, non aperto);
  - 3 promemoria di L0 (s5), 0 cambi illeggibili, 0 rifiuti della nota da parte del gate;
  - letture registrate: 100 file letti, 10 letture da comandi di shell, 12 pagine web aperte.
- **Costo:** 11,59 USD stimati, sonde comprese, sul tetto di 20. Restano 8,41. Sono dollari equivalenti dell'abbonamento, nessun addebito.
- **Risultati di `WebFetch` rimasti nelle evidenze:** 30 risultati in tutto, **tutti** sostituiti da un segnaposto con l'indirizzo. Quindi **nessun** risultato sotto i 5000 caratteri con testo di pagine. Le note di ricerca riportano i fatti delle pagine (nomi dei modelli, date, opzioni di `vercel.json`) con parole del modello, non testo copiato. Nessun nome utente, host o token nelle evidenze: controllato anche dentro i database.

## Cosa cambia nei progetti

- I comandi dietro `dotenv`, `dotenvx`, `cross-env`, `cross-env-shell`, `env-cmd`, `doppler run`, `infisical run` e `op run` chiedono il permesso come quelli diretti. Vale anche dietro `npx` o `pnpm exec`, anche con un comando scritto tra virgolette, e fino a due involucri uno dentro l'altro.
- `supabase db push -p --local`, `db pull --schema --local` e `db push -p --help` chiedono: prima la password o lo schema presi per `--local` o per `--help` facevano partire la scrittura. `db reset --linked --version …` chiede.
- `npm exec prisma -- -- migrate deploy` chiede.
- `init --update` propone `min_level` e `checklist` a un blocco di profilo scritto a mano che non li ha.
- Due task dello stesso tipo: tollgate lega quello prenotato dal lancio, non quello con il numero più basso.
- Una pagina web che risponde solo con un rimando non vale più come lettura nella nota di ricerca.
- Chiedono anche alcuni comandi innocui il cui argomento ha il nome di un servizio, dalla parte sicura: `cross-env NODE_ENV=test jest aws`, `doppler run --project supabase -- npm run dev`, `dotenv -- jest -t "vercel deploy"`.
- Limiti scritti, che non cambiano: `dotenv -- git push --force` e `dotenv -- rm -rf …` non sono visti dai controlli di git e di `rm`. Le scritture dei gestori di segreti (`doppler secrets set` e simili) passano: si dichiarano in `[external_effects] commands`.

## Pagine approvate che invecchiano

L'elenco unico del blocco «Dopo B». Non le ho toccate: le porta la prossima revisione delle skill con te.

- `docs/profili/backend.md`: dice che una cartella `routes/` va **sempre** a `backend`. Non è più vero per i moduli che importano una libreria di rotte d'interfaccia.
- `docs/profili/backend.md`: dice di «riprendere il caso in B7» per `supabase/` dentro un pacchetto di monorepo. B7 l'ha ripreso.
- `docs/profili/frontend.md`: un `.tsx` sotto `supabase/` va a `frontend` «finché non arriva il profilo del database». Oggi va a `database`.
- `docs/profili/infra.md`: dice che le scritture remote di `wrangler kv`, `d1` e `r2` non sono coperte. Dalla revisione 32 lo sono.
- `docs/profili/infra.md`: l'elenco dei comandi di Supabase dietro un lanciatore che chiedono il permesso. Ora alcuni passano: `migration new`, `functions new`, `functions serve`, `db reset`, `db lint`.
- `docs/profili/ai.md`: una cartella `prompts/` con soli modelli di testo non propone più il profilo `ai`.
- `docs/profili/verifiche/frontend-fonti.md`: dice P1-P38, mentre la tabella arriva a P39.
- `skills/rules-ai/SKILL.md`: cita `https://ai.google.dev/gemini-api/docs/models` e le pagine vicine, che oggi rimandano ad `aistudio.google.com`. Anche `templates/models.toml` punta lì.
- `docs/profili/verifiche/ai-fonti.md`, riga 20: cita la stessa pagina spostata.
- `docs/profili/database.md`: dice che `init --update` non propone niente a un blocco `database` scritto a mano. Ora propone `min_level` e `checklist`.

Posso unire su `main`?
