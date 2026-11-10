# Ri-revisione giro 1 del Task 4 (1423a9d..05c450c)

Letti: regole, brief, revisione, decisioni 3 e 15, report, diff. Eseguito solo `python3 -B -m unittest tests.test_rules_backend` (41 test, OK).

### Verdetti sui rilievi

1. **Rinvio non diceva il vero sulla decisione 15 (I-1)**: INDIRIZZATO. `docs/profili/backend.md` (voce «Rinvio»): su `main` solo esclusione per frammento, scritture di Wrangler, script nei monorepo; regole, pagina e frammento restano su `b5-profilo-backend`, il profilo non è proposto. Coperto da `test_page_rinvio_says_what_stays_on_the_branch` (needle su `main`, ramo, le tre parti, «non vanno su `main`»).
2. **Ultima frase di «Quando si accende» contraddittoria (I-2)**: INDIRIZZATO. La nuova frase coincide con la decisione 3 (percorso esatto per il file trovato; gli altri file della cartella al generico; task misto a `backend`) e dice che un file senza righe e fuori dalle cartelle non entra mai da solo e va aggiunto a mano nel `tollgate.toml`. La contraddizione con `--update` non c'è più.
3. **«Regole tolte» descriveva male le differenze (I-3)**: INDIRIZZATO. L'elenco ora ha: due fonti tolte (regole 1 e 9), regola 12 con «scelta nostra» (5 e 9 già l'avevano), regola 7 riscritta, regola 8 con una fonte in più, `export function POST(` uscito. Coincide con il diff del commit precedente e con la revisione; nessun id `R-BACKEND-` nella sezione.
4. **Affermazione falsa sulle fonti ufficiali (I-4)**: INDIRIZZATO. Ora: pagina ufficiale per le righe di codice, `api/` e `functions/` (righe 46 e 49 del rapporto); catalogo e progetto di B per `server/`, `backend/`, `routes/`, `handlers/` (righe 47-48 e la nota sui due pattern larghi).
5. **Termini non spiegati (M-1)**: INDIRIZZATO. Spiegati: edge function, `tollgate.toml`, gestore (nel glossario); namespace e bucket (nella frase su KV e R2); lanciatore; orchestratore di monorepo. Test `test_page_explains_the_terms`.
6. **Intestazione del rapporto sulle citazioni (M-2)**: INDIRIZZATO. `docs/profili/verifiche/backend-fonti.md` riga 3: «nella skill e nella pagina per l'utente se ne prendono solo i fatti… Le citazioni di questo rapporto sono al più di una riga per fonte».

Pagina ancora vera rispetto a skill e frammento (nessun file di skill o frammento nel diff); parole semplici, frasi brevi.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- Il test del Rinvio normalizza gli spazi su tutta la sezione, quindi la regex `\*\*Rinvio\.\*\*[^\n]*` prende anche l'ultimo paragrafo oltre la voce: i needle potrebbero passare per testo fuori dalla voce. Debolezza minore, non un difetto della pagina.
- M-3, M-4, M-5 (test sui dati privati, `sources_main` morto, regex deboli) non toccati dal giro e non richiesti dal dispatch.
- Resta da ricordare al Task 9 che `docs/profili/infra.md` dice «scoperte» le scritture remote di Wrangler (già nella revisione).

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
