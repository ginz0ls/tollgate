# Revisione Task 6 (commit 37f4519)

### Aderenza
- ✅ Fonti: la riga `Fonte:` di R-AI-06 non rimanda più a R-BASE-04 e dice che l'obbligo dell'indirizzo nel report è proprio della regola (SKILL.md:38). Il marcatore `from "openai"` è tolto (ai.toml, 19 marcatori). 11 regole, nessuna rinumerazione, nessun `approved`.
- ✅ Rapporto: righe e citazioni coincidono con `task-6-fonti.md` e `task-6-fonti-r-ai-06.md`; nessuna riga inventata, citazioni di una riga. Marcatori 19, uguali al frammento.
- ✅ Pagina: ogni regola presente, «N.» uguale all'id, «Blocca?» uguale a `[blocca]` (1-6 sì, 7-11 no); "Da decidere tu" ha i quattro punti decisi; bozza sul testo del modello sotto «Regole tolte»; niente «Approvata dall'utente». Cartelle, pacchetti, L1 e «stabile» coincidono con `ai.toml` e con R-AI-03.
- ✅ Repo pubblico: nessun `/home/`, nome utente o host nei file nuovi; nessun testo copiato dalle pagine fuori dalle citazioni del rapporto.
- ✅ `test_real_markers_not_in_tollgate_bin` controlla tutti i file di `bin/` con subTest per file e marcatore.
- ⚠️ Non rilanciati i test (evidenza nel report: 3359 OK su due interpreti).

### Punti di forza
Test su id e nomi, non su frasi; `test_detect_markers_verified` è bidirezionale (nessun marcatore senza `ok`, nessun `ok` per un marcatore sparito). Il report segnala onestamente lo scostamento e il dubbio su R-AI-09/10.

### Rilievi

**Important**
1. `docs/profili/ai.md` (sezione «Cosa sono», ultimo capoverso): dice «Per ogni regola ho scritto su quale delle tre guarda», ma la tabella non ha la colonna «Si giudica su»: solo R-AI-01 lo dice («Si guarda solo il diff»). Affermazione falsa verso l'utente; la «nota di ricerca» è spiegata e poi non compare più. Correggere: o si aggiunge a ogni riga (la skill ha «Si giudica su» per ognuna, e il test può confrontarlo come per Blocca?), o si toglie la frase. Aggiungere la colonna è la via più fedele a ciò che la skill chiede.
2. `tests/test_rules_ai.py:315` `test_page_is_a_proposal` e `:318-ss` `test_page_brings_the_open_choices_to_the_user`: asseriscono cose che smettono di valere con il Task 7 (la pagina riceverà «Approvata dall'utente» e la sezione «Da decidere tu» sarà chiusa o cambiata). Il test dice di essere in "proposta" solo nel nome, senza avvisare che il Task 7 deve cambiarlo. Correggere: docstring esplicita «valido finché il Task 7 non approva; il Task 7 lo sostituisce con la verifica della data di approvazione», oppure legarli a `approved` assente nel frontmatter della skill (così scadono da soli e in modo coerente).
3. `docs/profili/verifiche/ai-fonti.md:9-12` e `:70-73`: intestazione di tabella duplicata in entrambe le tabelle (riga «| Regola | Fonte (URL, sezione)…» e «| Marcatore | Pagina…» ripetute, con un secondo filetto). In Markdown la seconda intestazione e il secondo filetto diventano due righe di dati false. `table_rows` scarta solo la prima riga, quindi i test non se ne accorgono. Togliere le righe 11-12 e 72-73 (e un test che vieta intestazioni ripetute, oppure confrontare `cells[0]` con "Regola"/"Marcatore" solo alla prima riga).

**Minor**
4. `tests/test_rules_ai.py` `test_removed_sources_are_not_in_the_skill`: `assertTrue(no_rows)` impone che il rapporto abbia almeno una riga `no`. Oggi regge e non scade con il Task 7 (le righe `no` sono storia della verifica), ma vincola il rapporto a un esito, non a un comportamento: una futura verifica pulita lo romperebbe. La parte utile è `assertNotIn("R-BASE-04", …)`; toglierei l'altra o la dichiarerei. Inoltre l'esito della riga R-BASE-04 è scritto `**no**` in grassetto (ai-fonti.md, riga di R-AI-06 con "fonte tolta dalla regola"): il test `== "no"` la vede diversa dalle altre due righe `no`; uniformare.
5. `docs/profili/ai.md`, riga R-AI-06 e R-AI-08: la sintesi perde due cose che la regola dice. R-AI-06 omette che le scelte di configurazione (token richiesti, temperatura) restano fuori; R-AI-08 cita solo `-latest` e non gli alias senza data dei modelli Claude precedenti alla 4.6 né quelli con `~` di OpenRouter. «Ciò che la regola chiede detto senza cambiarlo»: aggiungere mezza frase a ciascuna.
6. `docs/profili/ai.md`, «Quando si accende»: «Il profilo si propone solo dopo che hai approvato le regole. Dopo l'approvazione, i progetti che l'hanno già copiato lo tengono…» si contraddice (come si copia un profilo non ancora proposto?). Riscrivere: «Prima dell'approvazione `init` non lo propone. Chi lo ha già copiato a mano lo tiene finché non lo toglie.» (se è questo che si intende; altrimenti togliere la seconda frase).
7. Parole non spiegate per un utente non tecnico: «prompt injection» (sotto "Da dove viene" di R-AI-09/10 e nella bozza tolta), `tool_result`, «prompt di sistema», «alias», «ID», «API», «preview», «famiglia», «anteprima». Il resto (diff, report, nota, task, L1, marcatori) è spiegato. Per R-AI-09/10, non bloccanti, una riga di spiegazione basta («istruzioni nascoste in una pagina o in una email che il modello legge»).
8. Test `test_page_explains_what_changes`: gli ago `diff` e `L1` compaiono ovunque nella pagina e non provano che si dica che R-AI-01 guarda il solo diff; `R-AI-01` idem. Meglio verificare che la riga di R-AI-01 contenga "diff" e che la frase su L1 sia in «Quando si accende».
9. `ai-fonti.md` («Regole tolte»): rimanda a «la sua motivazione nel rapporto di quel task», che non è nel repo; il lettore pubblico non può seguirlo. Togliere il rimando o ripetere in una frase la motivazione (c'è già).

### Domanda dell'implementatore: «R-AI-09 e R-AI-10 valgono solo per Anthropic» sotto «Regole tolte dalla verifica»
Non va lì. Non è una regola tolta ma un limite di ambito, e dice «per loro non c'è la regola» come se fosse uscita dalla verifica; inoltre l'affermazione «non ho trovato una pagina sullo stesso tema» per Gemini, OpenAI, OpenRouter e Agno non è nell'esito della verifica del controller (⚠️ non verificabile). Spostarla in «Cosa sono» (una riga: «le regole 9 e 10 valgono per Claude») e togliere l'affermazione sulla ricerca, oppure farla verificare. (Nel rapporto delle fonti non c'è, correttamente.)

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Il contenuto di fonti, regole e frammento è coerente e fedele alla verifica, ma la pagina dichiara una colonna di «Si giudica su» che non c'è, due test scadranno col Task 7 senza dirlo, e le tabelle del rapporto hanno un'intestazione duplicata che le rompe. Correzioni piccole e locali.
