---
name: rules-base
description: Regole di base di tollgate per ogni implementatore e revisore: le caricano in automatico gli agenti di tollgate, non serve invocarla.
version: 1
approved: 2026-11-01
---
# Regole di base (versione 1)

Sono le regole del passo «informati prima», comuni a ogni lavoro e a ogni area. Chi scrive codice le segue prima di toccare un file. Chi rivede le applica guardando il diff, la nota di ricerca o il report, e per ognuna risponde sì o no. Le regole segnate `[blocca]` sono quelle per cui un no è un rilievo che ferma il task. Un difetto si segnala una volta sola, con la regola che viola.

## Prima di scrivere

R-BASE-01 [blocca] Ogni file già esistente che il diff modifica compare in «Letto nel progetto» della nota. Un file nuovo non c'è ancora quando la nota si consegna: per lui vale R-BASE-07.
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/context-engineering/SKILL.md, «Level 3: Relevant Source Files»; progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezione 3.4 (riga base)

R-BASE-02 [blocca] Se il diff usa una libreria esterna, la nota riporta la sua versione e il file delle dipendenze da cui la prende. Se quel file non la dice, la nota lo scrive invece di indovinarla.
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/source-driven-development/SKILL.md, «Step 1: Detect Stack and Versions»

R-BASE-03 [blocca] Se il diff usa una libreria o un servizio esterno, «Documentazione» ha per ciascuno almeno una pagina ufficiale, cioè la documentazione o il changelog del progetto o del fornitore. Un blog, un forum o un riassunto non bastano.
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/source-driven-development/SKILL.md, «Step 2: Fetch Official Documentation» (gerarchia delle fonti)

R-BASE-04 [blocca] Ogni nome di modello AI che il diff scrive, di Gemini, di Claude o di altri, ha in «Documentazione» l'indirizzo della pagina ufficiale dei modelli del fornitore.
Fonte: progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezioni 1 e 3.6

R-BASE-05 [blocca] Un'affermazione del tipo «non esiste» o «non è supportato», nel report, nei commenti o nei messaggi, dice dove si è cercato: un file o un indirizzo.
Fonte: progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezione 1 (schema 2)

R-BASE-06 [blocca] Ogni indirizzo che il diff (commenti, documentazione) o il report cita come fonte compare in «Documentazione» della nota. Gli indirizzi che fanno parte del codice (endpoint, fixture, configurazione, esempi) restano fuori.
Fonte: progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezione 1 (schema 3)

R-BASE-07 Una funzione o un componente nuovo segue lo schema di uno simile già presente nel progetto, se esiste, e il report dice quale.
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/context-engineering/SKILL.md, «Level 3: Relevant Source Files» (punto 3)

R-BASE-08 Se il diff cambia la build, il rilascio o la CI, «Letto nel progetto» elenca i file di configurazione già presenti che li riguardano.
Fonte: progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezione 1 (esempio del deploy)

R-BASE-09 [blocca] «Nessuna fonte esterna» vale solo se il diff non usa librerie o servizi esterni, e la nota ne dice il motivo.
Fonte: progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezioni 2 (anti-obiettivo «passo troppo pesante») e 3.2

## Mentre lavori

R-BASE-10 [blocca] La correzione di un difetto porta un test che lo riproduce: il report mostra che il test fallisce senza la correzione e passa con la correzione.
Fonte: superpowers 7.0.0 (Jesse Vincent, MIT), skills/verification-before-completion/SKILL.md, «Key Patterns» («Regression tests (TDD Red-Green)»)

R-BASE-11 Il report dichiara funzionante solo ciò che un comando eseguito nel task prova, e riporta il comando con il suo esito.
Fonte: superpowers 7.0.0 (Jesse Vincent, MIT), skills/verification-before-completion/SKILL.md, «The Iron Law»

## Fonti

Le regole sono scritte con parole nostre a partire da due raccolte di metodo con licenza MIT e dalle correzioni dell'utente raccolte nel progetto di B. Le licenze sono in `LICENSES/agent-skills-MIT.txt` (agent-skills, Addy Osmani) e in `LICENSES/superpowers-MIT.txt` (Superpowers, Jesse Vincent). Le regole sono state approvate dall'utente il 2026-11-01.
