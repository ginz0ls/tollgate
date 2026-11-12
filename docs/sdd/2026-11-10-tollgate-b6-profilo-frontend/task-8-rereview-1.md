# Ri-revisione giro 1, Task 8

### Verdetti sui rilievi
1. **Letture del revisore (Important)**: INDIRIZZATO. `docs/verifiche/2026-11-10-b6-prova-flusso.md:62` (riga del revisore, righe 288/297/300 e 463/472/475, `tool_uses: 3` a 316 e 491) controllato nello stream del passo 2: sono tre `Read` ciascuno (review, task, diff), nessuna è il piano. Conclusione rafforzata («possono venire solo dalla skill precaricata»); la voce è tolta dai «Limiti».
2. **Uscita di `prepara` tra le evidenze (Important)**: INDIRIZZATO. `docs/verifiche/evidenze/b6/flusso/prepara/uscita.txt:1-9` (backend/ai/infra «nessun file corrisponde», `plan-check: ok []`), citata nella tabella, nella sezione «Proposta di `init`» e nell'elenco delle evidenze. Nessun nome utente né host (grep per valore: 0), nessun `/home/`, solo `/tmp/tollgate-b1`.
3. **`tollgate plan-check` fallito (Important)**: INDIRIZZATO. Passo 1 riga 193 (comando) e 204 («invalid choice: 'plan-check'», `exit=2`) verificati; detto in «Comandi del modello» e in «Scostamenti», tolto dall'elenco dei comandi validi.
4. **Righe dello stream (Minor)**: INDIRIZZATO. Controllate: 128 (Read di `tollgate.toml`), 135 (risultato), 156-164 (Skill `rules-frontend`), 182 (Write del piano), 294, 351, 469, 193, 204: tutte esatte.
5. **`SaveButton.tsx:22` (Minor)**: INDIRIZZATO. Ora «riga 22 del diff `review-2.diff`, relativa a `src/components/SaveButton.tsx`».
6. **Task 1 non testimone pulito (Minor)**: INDIRIZZATO. Frase aggiunta (`lookups.txt` n. 5 verificato: lettura del piano; nello stream del passo 2 è la riga 147, un `Read` del piano).
7. **`isMeta: no` (⚠️)**: INDIRIZZATO. Ridotta a ipotesi non provata dalle evidenze.

### Danni nuovi nel diff della correzione
Nessuno. Nota Minor non bloccante: nel punto sul task 1 «stream, riga 147» non dice che è lo stream del passo 2 (nella sezione le righe precedenti citano il passo 1); la riga è comunque esatta.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
