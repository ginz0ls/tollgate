# Ri-revisione giro 1, Task 5 (0635303..21d8285)

### Verdetti sui rilievi
1. **(Important) R-AI-06 `[blocca]` non decidibile con sì/no**: INDIRIZZATO. `skills/rules-ai/SKILL.md` (R-AI-06) ora vale per «ogni valore che il diff o il report presentano come fatto del modello o del servizio» (limite di contesto o uscita, prezzo, parametro accettato o rifiutato, valore predefinito) e esclude le scelte di configurazione (token richiesti, temperatura). Resta `Si giudica su: report`, con l'indirizzo come obbligo. Fonte dell'obbligo aggiunta: spec di B, riga `ai` (`docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md:96`, «Parametri e limiti delle API vengono dalla documentazione, non dalla memoria»), oltre a R-BASE-04. Un `max_tokens=1024` non blocca più.
2. **(Minor) R-AI-08 si vede nel diff, dichiarazione nel report**: INDIRIZZATO. Testo: «Se il diff usa un alias ... il report lo dichiara e ne dà il motivo».
3. **(Minor) commenti di `templates/profiles/ai.toml`**: INDIRIZZATO. `grep` su «decision|Task [0-9]» senza esiti; i commenti si capiscono da soli.
4. **Limiti `require('openai')` ed `esm.sh`**: INDIRIZZATO. Elencati in «Fix round 1» del report (`task-5-report.md`, ultimo punto).

Controllo obblighi senza fonte né `approved`: il giro non aggiunge obblighi (R-AI-06 si restringe, R-AI-08 si riformula con la stessa fonte); `approved` assente in `skills/rules-ai/SKILL.md`. La riga della fonte di R-AI-06 è reale (spec riga 96).

### Danni nuovi nel diff della correzione
Nessuno. Nota minore: la fonte cita «sezione 3.4» del progetto di B; non ho verificato il numero di sezione (la riga `ai` esiste a riga 96 della spec), non blocca.

### Osservazioni fuori ambito
Nessuna. (Il report non mostra una nuova corsa dei test dopo il giro; il diff tocca solo testo di skill e commenti, ma i test strutturali di `tests/test_rules_ai.py` leggono la skill: conviene che il controller li lanci mirati.)

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
