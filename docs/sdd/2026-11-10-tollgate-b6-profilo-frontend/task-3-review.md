# Revisione Task 3 (c4fff87, base 4f203da)

## Aderenza

- ✅ Frontmatter, titolo, sezioni, 12 regole consecutive, 9 `[blocca]` (01-09, 11), 10 e 12 no; tutte con «Si giudica su» e `Fonte:`; nessun `approved` (`skills/rules-frontend/SKILL.md:1-5`); 75 righe.
- ✅ Riga «Un componente è …» sola, prima di `## Prima di scrivere` (SKILL.md:9).
- ✅ Frammento: nove pattern nell'ordine della decisione 3 (`frontend.toml:14-34`), `exclude` della decisione 7 (riga 56), otto marcatori nell'ordine della decisione 5 (righe 58-68; coincide con `MARKERS` del test), `skills`/`reviewer_skills`/`commands`/`dod` vuoti, agenti e `kind`/`min_level` giusti, nessun `cross`. Fonte `**/*.svelte` = pagina «.svelte files» (riga 27), come da carry.
- ✅ «Using ARIA» citata con «(bozza sospesa)» (SKILL.md:36) e R-05 con 2.1.1 e 4.1.2; il test `test_using_aria_is_cited_with_its_status` lo fissa.
- ✅ R-10: la parte su Esc ha come sostegno la voce «Keyboard Navigation» della lista di controllo ("Escape to close", riga 19 della copia; "Modals ... return focus on close", riga 21): verificato.
- ✅ Nomi e livelli WCAG corretti (1.1.1 A, 1.3.1 A, 2.1.1 A, 2.1.2 A, 2.4.3 A, 2.4.7 AA, 3.3.2 A, 4.1.2 A, 4.1.3 AA).
- ✅ Tabella delle precedenze: ho controllato P1-P38 riga per riga contro le colonne «Proposta» e «Runtime». `check()` (`tests/test_init.py:1253-1262`) confronta l'intero dizionario dei blocchi proposti (quindi un profilo «non proposto» deve essere assente: P2, P5, P7, P9, P14, P19, P21-23, ecc.) e, se `runtime` è dato, `vertical_for` file per file. Nessuna colonna divergente. `detected` coerente con le note (P5/P6 `ai`; P8 `backend`; P9/P10/P19/P23/P25/P26/P32-P34 `frontend`; P22 con `server/entry.ts` anche in `frontend`; P37 in tutti e due). P16/P17 senza runtime = «—»; P18 `None`. P37 e P38 come da carry. `test_real_frontend_exclude_several_prefixes` come da brief.
- ✅ `_real_fragments_root(test, areas=None)` estratta, `test_real_trees_light_no_profile` invariato nelle asserzioni (`tests/test_init.py:1230`); `test_real_fragments_load` legge `frontend`.
- ✅ `docs/uso/comandi.md`: sezione `rules-frontend` (bozza non approvata), «quattro forme», frase sui pattern per estensione che nomina `frontend`, `exclude` con `frontend`.
- ✅ Intoccati i file vietati (diff solo sui 6 file attesi); `vertical_for`, `task_routing`, `globs`, I-1 non toccati.
- ✅ Suite: `suite-task-3.log`, 3847 test, OK con 3.11.16 e 3.13.5, `exit 0`, nessun avviso.

Scostamenti dichiarati contro il piano:
- 2 (tolto «un segnaposto non basta»): giustificato, nessuna copia lo dice; la regola resta sostanzialmente uguale. Accettato.
- 3 (tolti `outline-0`, `focus:outline-none`): giustificato (la copia ACL, riga 158, dice solo «Removing focus outlines»); resta «per esempio `outline: none`». Accettato.
- 5 (regex del criterio): corretta; la regex del brief sarebbe stata soddisfatta da «0.6.9». Accettato, anzi migliora il piano.
- 6 (tabella `USER_CHOICES` con insieme uguale): coerente con la correzione della decisione 16.
- Anche 1, 7, 8, 9: coerenti; i tre «scelta nostra» sono fissati da un test e vanno al Task 4.

## Punti di forza

- Tabella P1-P38 fedele e con asserzione doppia; i P di assenza verificano davvero l'assenza.
- Test sulla `Fonte:` stretti (criterio + livello + insieme verificato, stato di «Using ARIA», `ui-ux-pro-max` non ammessa, «scelta nostra» obbligatoria per 01, 02, 11).
- `test_real_exclude_matches_root_folders_of_other_fragments` e `test_real_markers_not_in_tollgate_bin` chiudono due derive reali.
- Regole scritte con parole proprie, citazioni assenti, ogni regola dice cosa guardare.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor
1. `SKILL.md` R-FRONTEND-12 (riga ~55): gli esempi «gradiente viola su bianco» e «carattere di sistema scelto per default» non stanno nelle fonti citate. FUE «Avoid the AI Aesthetic» ha «Purple/indigo everything» ed «Excessive gradients» come righe separate, e nessuna dei due testi parla di carattere di sistema (frontend-design dice solo di non usare le famiglie «che sceglieresti per qualunque progetto»). Ereditato dalla bozza del piano, ma la regola dice una cosa che la `Fonte:` non sostiene. Correggere gli esempi con quelli presenti (viola/indaco ovunque, gradienti in eccesso, schede identiche) o dichiararli «scelta nostra» e portarli in «Da decidere tu».
2. `tests/test_rules_frontend.py:~170` (`test_a11y_rules_name_a_wcag_criterion`): il nome del criterio non è verificato, solo numero e livello; un nome sbagliato (es. «2.4.7 Focus Order (AA)») passerebbe. Aggiungere un dizionario numero→nome nella tabella `WCAG`. Rafforzamento, non difetto.
3. `SKILL.md` R-FRONTEND-07: ammette `aria-label` come etichetta; la lista di controllo (sezione «Forms») chiede un'etichetta visibile, e la voce «Screen Readers» ammette `aria-label`. La regola è coerente con la seconda, ma la `Fonte:` non dice che la prima è più severa: da citare nel rapporto (Task 4) come scelta.
4. `SKILL.md` R-FRONTEND-11: la `Fonte:` cita «Component Architecture» (test accanto al componente), corretto; la bozza citava «Verification», che non parla di test dei componenti. Nessuna azione, solo conferma dello scostamento.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** requisiti, carry e tabella delle precedenze rispettati e verificati riga per riga, suite verde su due interpreti, nessuno scostamento problematico. Restano solo rifiniture minori (soprattutto gli esempi di R-FRONTEND-12 non sostenuti dalle fonti).
