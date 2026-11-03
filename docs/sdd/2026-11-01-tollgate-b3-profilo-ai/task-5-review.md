# Revisione Task 5 (4cdb378..0635303)

### Aderenza
- ✅ Frontmatter, titolo, sezioni, id consecutivi (R-AI-01..11), `approved` assente, 83 righe (`skills/rules-ai/SKILL.md`; test in `tests/test_rules_ai.py:100-155`).
- ✅ Ogni regola ha `Si giudica su:` e `Fonte:`; le sei `[blocca]` (01-06) si giudicano su diff o report, nessuna sulla nota (`test_blocking_rules_judged_on_diff_or_report`, `tests/test_rules_ai.py:147`).
- ✅ Scelte dell'utente della sezione 9 del progetto di B tutte coperte per id (`USER_CHOICES`, `tests/test_rules_ai.py:21-30`): nome in un punto (01), URL+data (02), ultimo stabile (03), anteprima (04), migrazione (05), errore chiaro (07), alias (08). Il test cerca per id, non per frasi (rinvio 182 rispettato).
- ✅ Frammento `templates/profiles/ai.toml` conforme a decisioni 2, 6, 9, 14: `kind`, `min_level`, 4 pattern, `skills`/`reviewer_skills`/`dod` vuoti, agenti `-ai`, niente `rules`/`blocking_rules`/`approved`, `[detect] content` di 20 voci.
- ✅ D11: nessun marcatore è pezzo di `@anthropic-ai/claude-code` (test con `assertNotIn(marker, CLAUDE_CODE_PACKAGE)`, direzione giusta); Anthropic JS/TS è `@anthropic-ai/sdk`; nessuna voce è il solo nome di un fornitore (`test_markers_are_pieces_of_lines_not_vendor_names`). Nessun marcatore compare in `bin/` (controllato: `grep` su `api.anthropic.com` e `@anthropic-ai/sdk` in `bin` senza esiti).
- ✅ D16: la sezione di `docs/uso/comandi.md` non contiene «solo l'utente»; nella skill nessun `P<cifra>` (grep vuoto) né `tollgate <sottocomando>` nudo.
- ✅ Testo non copiato: controllo a campione su `fonti/ai/` (Gemini «at least 2 weeks notice» per le anteprime; Anthropic `tool_result` primo punto; OpenAI Astra/Sol/Terra/Luna) coerente con i fatti riportati, in parole proprie; le virgolette «…» sono titoli di sezione, `test_no_long_quotations` (≤12 parole).
- ✅ Scostamenti dichiarati (R-AI-08 della bozza scartata per mancanza di fonte; R-AI-03 diviso; R-AI-09/10 al suo posto) sono coerenti con «nessun obbligo senza fonte»: scelta corretta.
- ⚠️ La verifica riga per riga delle fonti è del Task 6; non fatta qui.

### Punti di forza
- Rifiuto onesto di R-AI-08 della bozza (la pagina parla dell'ingresso, non dell'uscita del modello).
- «Famiglia» e «stabile» definiti per fornitore con la pagina e la sezione; dove la pagina non etichetta (OpenAI, OpenRouter) lo dice invece di inventare.
- Test strutturali per id, riuso di `research.area_rules`, `rules()` a 5 elementi utilizzabile dai Task 6-7; `RealFragmentsTest` legge il frammento vero.

### Rilievi
**Important**
1. `skills/rules-ai/SKILL.md` R-AI-06 `[blocca]`: «i parametri del modello, i limiti … e i prezzi che il diff o il report scrivono» è troppo largo per un sì/no. Un `max_tokens=1024` o `temperature=0` nel diff sono «parametri del modello» e, letta alla lettera, bloccano il task finché il report non cita un URL; il revisore o blocca tutto o decide a caso. Inoltre nessuna pagina dice l'obbligo (il report stesso lo ammette: segue da R-BASE-04). Correggere restringendo ai valori che dipendono dal modello e che il diff o il report **dichiarano come fatto** (limite di contesto/uscita, prezzo, parametro che il modello accetta o rifiuta), per esempio «un limite, un prezzo o un parametro attribuito al modello come fatto», e lasciando fuori le scelte di configurazione dell'utente; oppure farla non bloccante.

**Minor**
2. `skills/rules-ai/SKILL.md` R-AI-11: obbligo derivato (ID esplicito per Agno) senza pagina che lo dica; le due fonti danno solo fatti (ID predefinito, stato deprecato). È non bloccante e dichiarato nel report, ma «da confermare» con l'utente prima del Task 7.
3. R-AI-03 per OpenAI/OpenRouter: «stabile = ID senza `preview` e non deprecato» e «`expiration_date` valorizzata = non si sceglie» sono inferenze del redattore, non frasi delle pagine. Tenerle marcate per il Task 6.
4. R-AI-08 si giudica su `report` ma la violazione (alias nel codice) si vede nel diff: il revisore deve incrociare i due; accettabile perché non bloccante, ma conviene dirlo nel testo («il diff usa un alias e il report non lo dichiara»).
5. `templates/profiles/ai.toml:1,14-21`: i commenti citano «decisioni del piano» e «rapporto del Task 5», riferimenti interni inutili in un repo pubblico dopo la fusione.
6. Marcatori: nessuna forma `esm.sh` (giustificato: nessuna pagina la mostra); `require('openai')` e `require("@anthropic-ai/sdk")` CommonJS: il secondo è coperto, il primo no. Da annotare tra i limiti noti (Task 11).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Impianto, test e frammento sono solidi e conformi a decisioni e D11/D16; resta un solo Important: R-AI-06 `[blocca]` non è decidibile con un sì o no e rischia di bloccare per qualunque parametro. Il resto sono rifiniture.
