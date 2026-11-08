# Revisione Task 5 (bdd75d4..1f41852)

### Aderenza (✅ / ❌ ; ⚠️ non verificabile)
- ✅ Le quattro fonti `no` del verificatore (`task-5-fonti.md`) sono applicate come deciso dal controller: R-INFRA-01 e R-INFRA-02 con la parte in più dichiarata «scelta nostra» in `skills/rules-infra/SKILL.md:14` e `:18`; R-INFRA-03 senza la 3.4 (`:22`); R-INFRA-12 con `secret put` sulla pagina dei segreti (`:60`). Nessuna fonte `no` resta senza correzione. Docker aggiunto a «Dove informarsi» (`:69`).
- ✅ Nessuna regola esce, rinumerazione non necessaria (01-12 consecutive); il rapporto lo dice e la pagina ha «Regole tolte dalla verifica» senza id (`docs/profili/infra.md:104`).
- ✅ Rapporto: due tabelle con l'intestazione richiesta; 14 pattern `ok` su 14; citazioni di una riga, in inglese solo lì; niente testo lungo copiato nella skill né nella pagina.
- ✅ Pagina: tabella a cinque colonne, 12 righe, «dodici» e «sei punti» coincidono con la skill e con l'elenco; «Blocca?» e «Si giudica su» combaciano (verificato da `test_page_blocca_matches_skill` e `test_page_judged_on_matches_skill`; riletto a mano: 01,02,03,04,05,06,12 sì; 07-11 no; diff/report come nella skill).
- ✅ Carry: R-INFRA-12 usato per la regola «non pubblicare» (`infra.md:61`); D1 `allow_no_tests` e `/tollgate:approve unverified-tests` (`:79`; `config.py:30`, `verify.py:116` confermano); D16 `.vercel/` (`:42`); `app.Dockerfile` e `<nome del Dockerfile>.dockerignore` (`:40`); `compose.override.yaml` acceso (`:40`); decisione 17 con Supabase/B7, Vercel come già senza `npx`, `npx vitest run vercel`, `npm docs` (`:81-89`). Ho controllato `bin/tollgate_analysis/bash.py:984-1042`: `npm docs|help|config vercel` non sono in `PACKAGE_COMMANDS`, quindi il candidato `vercel` scatta e chiede: la frase della pagina è vera. I buchi elencati (`wrangler --env prod deploy`, `docker build --push`, `kv/d1/r2`) sono quelli veri.
- ✅ `approved` assente; nessun file di `ai` o `base` toccato (stat del diff: 4 file); nessun nome utente, host o progetto privato (grep).
- ❌ `"@nome"` in `env` di Vercel: vedi Important 1.
- ⚠️ Suite: non rilanciata (regola del revisore); l'evidenza è `task-5-suite.log` dichiarata verde, 3640 test su due interpreti, +1 skip spiegato.

### Punti di forza
- La pagina è davvero in parole semplici: glossario con le parole tecniche alla prima volta, costo esplicito per le conferme in più, avviso chiaro che il `dod` gira senza controllo e con le credenziali salvate, esempio TOML concreto. «Da decidere tu» porta all'utente le scelte nostre (01, 02, 06, `.github/actions/`, cambio per `ai`) e non nasconde i buchi rimasti della decisione 17.
- I test hanno guardie utili: `test_removed_sources_are_not_in_the_skill` verifica che ogni riga `no` abbia una `ok` della stessa regola e che le correzioni siano davvero nella `Fonte:`; `test_page_number_matches_id`; test dei pattern contro il frammento in entrambe le direzioni.
- Il rapporto non nasconde le righe `no` e spiega perché restano.

### Rilievi

**Important**

1. `docs/profili/infra.md:54` (regola 5): la pagina dice che un valore `"@nome"` in `env` di Vercel «non conta come difetto», ma `skills/rules-infra/SKILL.md:30-32` (R-INFRA-05) non lo dice: la skill è ciò che leggono `implementer-infra` e `reviewer-infra`, la pagina è ciò che l'utente approva. Oggi la regola approvata dall'utente e la regola applicata dal revisore divergono: un `env` con `"@my-secret"` può essere segnato come segreto nel diff. In più l'eccezione non ha una voce nel rapporto (`infra-fonti.md`: R-INFRA-05 non cita il passaggio di `vercel-json` sulla risoluzione dinamica di un secret, che esiste nella copia a `fonti/infra/vercel-json.md` sezioni `env` e `build.env`), non è dichiarata né fonte né «scelta nostra», e non è in «Da decidere tu». Il test (`tests/test_rules_infra.py:357-358`) si limita a cercare la stringa nella pagina, quindi non vede la divergenza. Correzione: aggiungere l'eccezione al testo di R-INFRA-05 in skill con la fonte (pagina `vercel-json`, sezioni `env` e `build.env`) e nel rapporto (riga con citazione di una riga), oppure togliere la frase dalla pagina; poi un test che confronti pagina e skill sul punto (es. «`"@nome"`» o «riferimento a un segreto» in entrambe).

**Minor**

2. `infra-fonti.md` («Parti dichiarate scelta nostra») dice che «e li imposta l'utente» di R-INFRA-05 e la 3.4 come proposta dell'autore «vanno alla pagina, in Da decidere tu», ma la pagina non li porta: il punto 3 di «Da decidere tu» riguarda i file compose. In più `infra.md:50-51` scrive «La tua scelta nel progetto di B» per la 3.4, che è una proposta dell'autore rivista dall'utente (`progress.md:71`). Dire «proposta che hai rivisto» e aggiungere una riga alla regola 5, oppure correggere il rapporto.
3. `infra-fonti.md` riga R-INFRA-12 / pagina dei comandi di Workers segnata `no` con una citazione che invece regge (`--dry-run`): chi legge la tabella senza la nota sotto la capisce al contrario. Spostare nella citazione la frase sbagliata («secret ... cambiano subito») o la nota nella cella.
4. `infra.md`: parole non spiegate per un utente non tecnico: `npx`, `backend` (profilo), `vars`/`ENV`/`ARG`, Terraform, nginx, systemd, «CI»; `skills/.../SKILL.md:60`: i comandi `project create/delete` di `pages` non hanno una riga `ok` propria nel rapporto (il verificatore ha confermato `pages deploy` e `pages secret put`).
5. I numeri «dodici», «sei punti» e «quattro fonti» della pagina non sono coperti da un test; un cambio alle regole li renderebbe falsi in silenzio.
6. `test_page_has_no_private_data` controlla solo `/home/`; l'unico controllo vero su nomi utente è la mia grep. Aggiungere i nomi che la regola di cautela vieta.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Tutte le correzioni del controller e i requisiti di `carry.md` sono presenti e coerenti con il codice, ma la pagina promette un'eccezione (`"@nome"` in `env`) che la regola applicata dal revisore non contiene, e che non ha fonte nel rapporto né voce in «Da decidere tu»: l'utente approverebbe una regola diversa da quella eseguita.
