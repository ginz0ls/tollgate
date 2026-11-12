# Revisione Task 4 (c4fff87..980432e)

### Aderenza
- ✅ Correzioni del controller: R-FRONTEND-04 perde «e caratteri» e «gerarchia dei caratteri» dalla `Fonte:` (`skills/rules-frontend/SKILL.md`, diff righe 28-30); R-FRONTEND-12 perde «carattere di sistema scelto per default» (riga 60). Nessuna regola esce, numeri invariati, nessuna fonte nuova, `approved` assente, `templates/profiles/frontend.toml` intatto.
- ✅ Rapporto delle fonti: una riga `ok` per ogni voce di ogni `Fonte:` (29 righe, verificate a mano contro le `Fonte:` della skill; le voci «scelta nostra» sono tolte e finiscono nella sezione «Parti dichiarate «scelta nostra»»). Quattro tabelle nelle sezioni giuste, prima di «Regole tolte dalla verifica»; 9 pattern, 4 marcatori (valgono per le 8 forme), 6 prefissi, tutti uguali a `frontend.toml`. Fonte di `infra/` = catalogo riga `infra`, di `supabase/` = progetto di B sezioni 2 e 12: come richiesto.
- ✅ Fedeltà all'esito del verificatore (`task-4-fonti.md`): tutte le 29 `ok` coincidono; le due `no` sono dichiarate in testa e in «Regole tolte», con la parte tolta, e le due righe corrette sono `ok` con la correzione nella citazione. Nessuna citazione supera una riga, nessuna frase copiata. La nota su R-FRONTEND-07 (`aria-label` in «Screen Readers», etichetta visibile in «Forms») c'è nel rapporto e nella pagina. «Using ARIA» riportata come bozza sospesa.
- ✅ Pagina: tutti i costi «costo» della decisione 4 sono presenti e comprensibili (P2, P3, P6, P7, P8, P10, P13, P14, P15, P20, P23, P24, P26, P27, P28, P29, P31, P32, P33, P34, P35, P36); P37 (punto 18), P38 e `handlers/` (punto 8), `web/routes/` (17), `.css` di un sito di documentazione (22), `+types` e rotte di sole risorse (12), `aria-label` (6), le tre «scelta nostra» (3, 4, 5), L1/L2 e `dod` a mano, «lo accendono N file» (verificato: `bin/tollgate_flow/init.py:417`, `lit` conta i candidati che combaciano con `paths`, anche escluse). Conteggi: «dodici», «dieci bloccano» (R-01..09 e 11), «ventidue punti» = 22 voci con 22 «Proposta:». Il report segnala giustamente che il brief diceva 9.
- ✅ Vincoli: nessun nome utente/host/token nei tre file nuovi (grep), nessun `if any(...)`, nessun metodo d'aiuto inutilizzato, `test_page_has_no_private_data` con `assertFalse(re.search(...), messaggio fisso)` per nome utente e host; `approved` assente.
- ⚠️ Non verificabile dal diff: l'esito reale di `tests/run` (il log non è nel pacchetto); il report dice 3867 test verdi su 3.11 e 3.13.

### Punti di forza
Pagina ordinata, ogni punto di «Da decidere tu» ha costo e proposta; il glossario è puntuale; il rapporto è generato dalle `Fonte:` così le celle coincidono con le voci; il conteggio del dizionario dei numeri fallisce con messaggio esplicito; la tabella delle regole è controllata riga per riga contro la skill.

### Rilievi

**Important**
1. `tests/test_rules_frontend.py:632` `self.assertNotIn("/home/", text)`: se fallisce, unittest stampa l'intero testo della pagina, cioè proprio il percorso con il nome utente che il test deve proteggere (stessa famiglia dell'incidente descritto dalla decisione 16). Correzione: `self.assertFalse("/home/" in text, "un percorso della home compare nel testo")`.
2. `docs/profili/frontend.md`, requisito «parole tecniche spiegate la prima volta» non rispettato per alcuni termini che l'utente deve capire per decidere: **«percorso esatto»** (usato a riga 62 «Il file entra nel profilo con il suo percorso esatto» e al punto 11 «un percorso esatto vince su ogni cartella»: il glossario spiega solo «percorso per estensione»); **«loader»** (punto 12); **«CDN»** (punto 3); **«profilo»** mai definito; «client delle API» (punto 1). Correzione: una voce di glossario «Percorso esatto: il nome completo di un singolo file scritto nel `tollgate.toml`; vince su ogni cartella» (e idem per «Profilo»), e una mezza frase per loader e CDN. `test_page_explains_the_terms` andrebbe esteso con `**Percorso esatto**`.

**Minor**
3. `docs/profili/frontend.md` punto 10 (e riga «Sono del profilo `backend`, `infra` e `database`» in «Cosa non lo accende»): dice che `supabase/` va «al profilo del database», ma il profilo non c'è ancora e il punto 19 dice che un `.tsx` lì va a `frontend` fino a B7. Aggiungere «(da B7; fino ad allora vedi il punto 19)».
4. Punto 12: non dice in una riga il costo (codice lato server che segue le regole d'interfaccia) né perché «dalla parte sicura»; il primo periodo ("dentro `app/routes/`...") è ambiguo. Riscrivere con costo esplicito.
5. `test_page_brings_the_open_choices_to_the_user`: alcuni needle (`` `web/` ``, `` `supabase/` ``, `` `components/` ``) compaiono anche in punti non pertinenti (17, 10, 7), quindi P14 e P35 non sarebbero fissati se i punti 19 e 21 sparissero; i fogli di stile/test in `routes/` (P32, P33) sono fissati solo in `test_page_explains_what_changes`. Aggiungere needle specifici (es. «finché non arriva il profilo del database», «`web/api/`», `.module.css`).
6. `test_removed_sources_are_not_in_the_skill`: il ciclo sulle righe `no` è vuoto (nessuna riga `no` nel rapporto, per scelta); resta valido solo per i quattro `assertNotIn`. Accettabile, ma il docstring promette di più.
7. Pagina: «l'utente» indica sia chi usa il sito (glossario «Interfaccia») sia chi legge («tu»): si potrebbe scrivere «chi usa il sito».

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** requisiti e correzioni del controller rispettati e rapporto fedele, ma il test `assertNotIn("/home/", text)` può stampare il percorso privato in caso di errore (regola esplicita della decisione 16) e la pagina lascia senza spiegazione alcuni termini che servono per decidere. Correzioni piccole.
