# Ri-revisione giro 1, Task 3 (8e5574c..1dcc9c2)

Controlli: diff letto una volta; report («Fix round 1») letto; `python3 -B -m unittest tests.test_rules_backend` rilanciato per un controllo mirato (23 test OK); `grep "scelta nostra"` sulla skill.

### Verdetti sui rilievi

1. **R-BACKEND-09 `[blocca]`: obbligo del caso d'errore per ogni input validato e risorsa che può mancare, senza fonte.** INDIRIZZATO. `skills/rules-backend/SKILL.md:50`: la `Fonte:` ora aggiunge «il caso d'errore per ogni input validato e per ogni risorsa che può mancare è una scelta nostra». Per la decisione del controller (ruling nel ledger) la regola resta invariata e la dichiarazione basta; il vincolo «nessun obbligo senza fonte se non dichiarato scelta nostra» è rispettato.
2. **R-BACKEND-05 `[blocca]`: «e che il task lo chiede» senza fonte.** INDIRIZZATO. `SKILL.md:34`: la `Fonte:` ora dice «che il task chieda il cambiamento è una scelta nostra», con la parte coperta dalla fonte («cambiare ciò che è pubblico rompe chi lo usa») separata. Regola invariata, come da ruling.

Il test nuovo `test_extensions_of_the_sources_are_declared_as_our_choice` (`tests/test_rules_backend.py`, righe aggiunte) verifica «scelta nostra» in R-BACKEND-02, 05, 09; passa. Nessun test indebolito.

### Danni nuovi nel diff della correzione
Nessuno. Il diff tocca solo due righe `Fonte:` e aggiunge un test. Le `Fonte:` restano riconosciute da `test_every_rule_names_a_source_of_the_allowed_kinds` (le forme ammesse sono intatte). Il test nuovo è un po' debole, perché controlla solo la presenza della stringa nella riga e non che riguardi la parte giusta, ma è sufficiente al suo scopo (Minor, non blocca).

### Osservazioni fuori ambito
- I rilievi Minor 3-6 della revisione (R-BACKEND-12 con due obblighi e «o un database»; `Fonte:` di R-BACKEND-08 senza `code-reviewer`; `USER_CHOICES` che copre solo R-BACKEND-01; `if any(...)` tautologico) non erano nel dispatch e non risultano toccati dal diff: restano aperti come Minor, non bloccanti.
- Conferma all'utente delle due parti «scelta nostra» in «Da decidere tu»/Task 5: resta da fare nei task successivi, se il controller la vuole.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
