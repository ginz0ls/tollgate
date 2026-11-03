# Giro di correzione finale del ramo `b3-profilo-ai`

Sei l'implementatore del giro di correzione unico dopo la revisione finale. Correggi **tutti** i punti sotto, ciascuno con un test che fallisce prima dove si può (RED, poi GREEN). La revisione completa, con file:riga, è in `W/final-review.md`: leggila. Regole del ruolo: `W/implementer-rules.md`; regole di cautela: `W/cautele.md` (vincolanti).

## I-1 (Important): testo delle pagine dei fornitori nelle evidenze pubbliche
Negli stream-json della prova reale ci sono i `tool_result` di `WebFetch` con il testo intero delle pagine di Anthropic: `docs/verifiche/evidenze/b3/flusso/passo1/tentativo-1/claude.jsonl:120`, `docs/verifiche/evidenze/b3/flusso/passo2/tentativo-1/claude.jsonl:119`, `:128`, `:256` (verifica i numeri di riga: cerca i risultati di `WebFetch`). Sostituisci il contenuto di quei risultati con un segnaposto che dica URL e lunghezza (per esempio `[pagina di terzi tolta dalle evidenze: <URL>, <N> caratteri]`), lasciando valido il JSON di ogni riga. Cerca anche in tutti gli altri file di `docs/verifiche/evidenze/b3/` testo di pagine scaricate (risultati di `WebFetch` o `WebSearch` lunghi) e trattalo allo stesso modo. Aggiungi un test (in `tests/test_b1_scripts.py` o un file vicino) che scorre i `.jsonl` di `docs/verifiche/evidenze/` e fallisce se un risultato di `WebFetch` supera un tetto ragionevole (per esempio 2.000 caratteri), e fai sì che `registra` (o lo script che copia le evidenze) applichi lo stesso segnaposto in automatico per le prove future, con un test. Nel rapporto `docs/verifiche/2026-11-01-b3-prova-flusso.md`, sezione dell'anonimizzazione, una riga che lo dice.

## M-5: frasi della pagina `docs/profili/ai.md` e marcatore rimesso
- `:77` «le altre si rinumerano» contro `:79` «i numeri non cambiano più»: dopo l'approvazione un numero non si riusa (catalogo 2.3): correggi la frase.
- `:25`: il profilo arriva con `/tollgate:init --propose` per un progetto nuovo e con `--update` per uno che ha già tollgate; dillo esatto.
- **Decisione dell'utente del 2026-11-02:** il marcatore `from "openai"` (virgolette doppie) **torna** in `templates/profiles/ai.toml`. Nel rapporto delle fonti `docs/profili/verifiche/ai-fonti.md` la sua riga dice che è la stessa riga di import che la pagina dell'SDK di Node (`openai-sdk-node-readme.md`, `import OpenAI from 'openai';`) mostra con le virgolette singole, scritta con le virgolette doppie, e che nessuna pagina mostra la forma con le doppie: esito `ok` per decisione dell'utente del 2026-11-02 (non per una citazione). La pagina, sezione «Cosa hai deciso», punto 4, dice la decisione nuova in parole semplici (prima era tolto; ora c'è, perché la forma con le virgolette doppie è la più comune nei progetti TypeScript). Togli la frase «coprono quasi tutti i casi». Aggiorna i test che contano i marcatori o che vogliono `from "openai"` assente; `test_real_markers_not_in_tollgate_bin` deve restare verde.

## M-6
`agents/implementer-ai.md:51` «ciò che servono» → «ciò che serve».

## M-7
Nel rapporto della prova, una riga: `reviewer-ai` ha usato `WebFetch` dal vivo (verifica nello stream-json del passo 2 con `grep` mirato: è la prima prova reale della decisione 11).

## Minori del triage, da correggere prima del merge (piano principale `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`)
- I conteggi delle fonti: dopo il punto M-5 ricontali sulle tabelle di `docs/profili/verifiche/ai-fonti.md` e scrivi i numeri veri.
- `test_page_lists_every_rule` sta in `tests/test_rules_ai.py`, non in `test_fragments.py`.
- Nel blocco dei rinvii «A B4-B7» la riga sui test esistenti che girano sulla radice vera del plugin (frammenti, skill approvata, marcatori veri) — è anche il Minor M-4 della revisione finale; e il Minor M-1 (le cartelle `agents/` e `prompts/` accendono `ai` anche per file non di codice, per esempio `.github/agents/` di Copilot o `docs/ai/`).

## A basso costo, insieme
- **M-2:** il test di deriva degli agenti per area confronta anche l'insieme delle chiavi del frontmatter (le sole differenze ammesse sono quelle della decisione 10).
- **M-3:** un frammento con un valore di tipo sbagliato (per esempio `paths = "x"` o `min_level = 1`) dà una `FragmentError` col nome del file, non un `TypeError` che fa uscire `init`; con un test.

## Come chiudere
- Mai `approved` cambiato; nessuna regola cambia testo o numero.
- Test mirati dei file toccati con python3.11 e python3, poi `claude plugin validate --strict .` (uscita 0) e `PYTHONWARNINGS=error::ResourceWarning tests/run` una volta, in background, con l'uscita in `W/final-fix-suite.out`; controlla tu stesso il file fino all'esito e committa subito, senza aspettare notifiche. Commit con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (uno o più, mai amend). Prima del commit delle evidenze: `grep -rI` del nome utente e dell'host (trovali con `whoami` e `hostname`, mai scriverli in un file) e delle forme di token su `docs/verifiche/evidenze/b3/`: zero.
- Report in `W/final-fix-report.md`, con RED e GREEN per ogni punto.
