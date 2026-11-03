---
name: rules-ai
description: Regole di tollgate per il codice che usa modelli AI: le caricano in automatico gli agenti dell'area ai, non serve invocarla.
version: 1
approved: 2026-11-02
---
# Regole ai (versione 1)

Sono le regole per il codice che chiama modelli AI (Claude, Gemini, OpenAI, OpenRouter, Agno), in aggiunta a quelle di base. Chi scrive codice le segue prima di toccare un file. Chi rivede le applica guardando ciò che ha davanti, e per ognuna risponde sì o no: sotto ogni regola la riga «Si giudica su» dice se la risposta sta nel diff, nel report o nella nota di ricerca. Le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è. Un difetto si segnala una volta sola, con la regola che viola.

## Prima di scrivere

R-AI-01 [blocca] Il nome di un modello sta in un solo punto del codice, una costante o una voce di configurazione. Il resto del codice, test compresi, legge quel punto e non ripete il nome.
Si giudica su: diff
Fonte: progetto di B, sezione 9 (scelta dell'utente: il nome del modello in un solo punto); https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions (fine della sezione «Dateless IDs are pinned snapshots»: ogni ID di modello ha un suo calendario di deprecazione e ritiro, quindi cambiarlo deve costare una modifica sola)

R-AI-02 [blocca] Accanto al nome del modello il diff scrive l'indirizzo della pagina ufficiale dei modelli del fornitore e la data in cui l'ha verificato: in un commento oppure, in un file che non ammette commenti (come JSON), in una chiave vicina.
Si giudica su: diff
Fonte: progetto di B, sezione 9 (scelta dell'utente: indirizzo ufficiale e data della verifica); le pagine dei modelli elencate in «Dove informarsi»; R-BASE-04 della skill `rules-base` (stesso indirizzo, che qui va anche nel codice)

R-AI-03 [blocca] Se il diff scrive o cambia il nome di un modello, il report riporta, dalla pagina ufficiale dei modelli aperta nel task, l'ultimo modello stabile della famiglia (la nota lo riporta pure, se c'è). Il diff usa quel modello, oppure il report dice perché ne usa un altro.
Si giudica su: report
Fonte: progetto di B, sezione 9 (scelte dell'utente: l'ultimo modello subito, ma solo se stabile); per «famiglia» e «stabile» le pagine elencate qui sotto
- Anthropic: la famiglia è la linea del modello (campo `line` dell'elenco dei modelli, che non si deduce dall'ID); è stabile un modello `active` (stato «Active» nella tabella dello stato dei modelli); i modelli correnti li elenca la panoramica, mentre quelli più vecchi ma ancora disponibili stanno in una lista a parte («Legacy models»). Pagine: https://platform.claude.com/docs/en/api/models/list (campi `line` e `lifecycle`), https://platform.claude.com/docs/en/models/overview (sezione «Compare models»), https://platform.claude.com/docs/en/about-claude/model-deprecations (sezioni «Overview» e «Model status»)
- Gemini: la famiglia è la variante (per esempio Flash, Flash-Lite, Pro); è stabile un modello con l'etichetta «Stable» nella pagina dei modelli, mentre gli ID Preview, Latest ed Experimental sono tipi diversi, descritti nella sezione «Model version name patterns». Pagina: https://ai.google.dev/gemini-api/docs/models
- OpenAI: la pagina dei modelli li raggruppa per linea (Astra, Sol, Terra, Luna) e dà l'ID di ciascuno, ma non li etichetta come stabili o in anteprima; qui è stabile un modello il cui ID non contiene `preview` (la pagina delle deprecazioni dice che le anteprime lo portano nel nome) e che nelle due pagine non risulta deprecato. Pagine: https://developers.openai.com/api/docs/models, https://developers.openai.com/api/docs/deprecations (sezione «Model deprecation notice periods»)
- OpenRouter: l'ID ha la forma `autore/nome`; la famiglia e la stabilità si leggono nella pagina del fornitore originale quando è uno di quelli sopra, perché la pagina di OpenRouter non le distingue. Un modello con `expiration_date` valorizzata nel catalogo è in via di ritiro e non si sceglie. Pagina: https://openrouter.ai/docs/guides/overview/models.md (sezione «Model Object Schema»: forma dell'ID e campo `expiration_date`)

R-AI-04 [blocca] Un modello in anteprima o sperimentale compare nel diff solo se il report lo dichiara e ne dà il motivo.
Si giudica su: report
Fonte: progetto di B, sezione 9 (scelta dell'utente: solo modelli stabili); https://ai.google.dev/gemini-api/docs/models (sezione «Model version name patterns»: le anteprime hanno limiti più stretti e preavviso di almeno due settimane per la deprecazione, quelle sperimentali non sono adatte alla produzione); https://developers.openai.com/api/docs/deprecations (sezione «Model deprecation notice periods»: le anteprime si possono ritirare con preavviso breve e non sono consigliate per carichi critici)

R-AI-05 [blocca] Se il diff cambia il modello usato, il report cita la guida alla migrazione o le note di versione ufficiali del modello nuovo e dice che cosa ha cambiato per seguirle. Un modello nuovo può rifiutare parametri che il precedente accettava.
Si giudica su: report
Fonte: progetto di B, sezione 9 (scelta dell'utente: leggere le note di migrazione prima di cambiare); https://platform.claude.com/docs/en/about-claude/models/migration-guide (indice delle guide, una per modello) e https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide (sezione «Send a request to Claude Sonnet 5.5»: elenca impostazioni che con quel modello fanno rispondere con errore 400); https://platform.claude.com/docs/en/release-notes/overview; https://ai.google.dev/gemini-api/docs/changelog e https://ai.google.dev/gemini-api/docs/deprecations (colonna del sostituto consigliato); https://developers.openai.com/api/docs/deprecations (sostituti consigliati)

R-AI-06 [blocca] Ogni valore che il diff o il report presentano come fatto del modello o del servizio ha nel report l'indirizzo della pagina ufficiale da cui viene. Sono fatti di questo tipo il limite di contesto o di uscita, il prezzo, un parametro che il modello accetta o rifiuta e un valore predefinito. Le scelte di configurazione del progetto (quanti token chiedere, quale temperatura impostare) restano fuori.
Si giudica su: report
Fonte: progetto di B, sezione 3.4, riga `ai` (parametri e limiti delle API vengono dalla documentazione, non dalla memoria); i valori cambiano da modello a modello e le pagine li danno per ciascuno: https://platform.claude.com/docs/en/models/overview (sezione «Compare models»: contesto, uscita massima, prezzo) e https://platform.claude.com/docs/en/about-claude/pricing (sezione «Model pricing»); https://ai.google.dev/api/models (campi di limite dei token di un modello) e https://ai.google.dev/gemini-api/docs/pricing; https://developers.openai.com/api/docs/models (ID, prezzi e contesto di ogni modello); https://openrouter.ai/docs/guides/overview/models.md (campi `context_length` e `pricing`); https://docs.agno.com/models/overview.md (le capacità variano per fornitore, API e ID); l'obbligo di scrivere l'indirizzo nel report è proprio di questa regola, per renderla controllabile dal revisore, e non viene da una fonte (R-BASE-03 e R-BASE-06 della skill `rules-base` chiedono lo stesso indirizzo solo in «Documentazione» della nota)

## Mentre lavori

R-AI-07 Il codice nuovo o modificato che chiama un modello gestisce il caso del modello non più disponibile o ritirato con un messaggio d'errore che nomina il modello e il punto della configurazione da cambiare.
Si giudica su: diff
Fonte: progetto di B, sezione 9 (scelta dell'utente: errore chiaro per un modello non più disponibile); le richieste a un modello ritirato falliscono: https://platform.claude.com/docs/en/about-claude/model-deprecations (sezione «Migrating to replacements»), https://platform.claude.com/docs/en/api/models/list (stato `retired`), https://ai.google.dev/gemini-api/docs/deprecations (introduzione: dopo lo spegnimento l'endpoint non esiste più), https://developers.openai.com/api/docs/deprecations (sezione «Deprecation vs. legacy»: dopo lo spegnimento il modello non è più raggiungibile)

R-AI-08 Se il diff usa un alias che si sposta da solo sul modello più nuovo, il report lo dichiara e ne dà il motivo. Sono alias di questo tipo i `*-latest` di Gemini, quelli con `~` e `-latest` di OpenRouter e gli alias senza data dei modelli Claude precedenti alla generazione 4.6.
Si giudica su: report
Fonte: progetto di B, sezione 9 (scelta dell'utente: alias che cambiano da soli solo se dichiarati); https://ai.google.dev/gemini-api/docs/models (sezione «Model version name patterns», voce Latest: l'alias passa al rilascio nuovo e l'avviso è di due settimane per i cambi che rompono); https://openrouter.ai/docs/quickstart.md (nota sugli alias latest: si risolvono sul modello più recente della famiglia); https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions (sezione «Before the 4.6 generation»: l'alias punta all'ultimo snapshot datato)

R-AI-09 Con l'API di Anthropic, il contenuto di terzi che il diff passa al modello (pagine web, email, documenti, risultati di strumenti) va nei blocchi `tool_result`, mai nel prompt di sistema né in un blocco di testo dell'utente.
Si giudica su: diff
Fonte: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks (sezione «Indirect prompt injection», primo punto dell'elenco)

R-AI-10 Con Claude, il diff non dà al modello segreti che il compito non richiede né strumenti con permessi più ampi del necessario.
Si giudica su: diff
Fonte: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks (sezione «Indirect prompt injection», punto sul limitare l'accesso a dati e azioni sensibili)

R-AI-11 Con Agno il diff passa l'ID del modello in modo esplicito (`id=` oppure la forma `fornitore:id`) e non si affida al valore predefinito della classe, che può essere un modello già in ritiro.
Si giudica su: diff
Fonte: https://docs.agno.com/models/overview.md (sezione «Configure a Model»: le due forme); https://docs.agno.com/models/providers/native/anthropic/overview.md (sezione «Model Selection»: l'ID predefinito di `Claude`) letto insieme a https://platform.claude.com/docs/en/about-claude/model-deprecations (sezione «Model status»: lo stato di quell'ID)

## Dove informarsi

Prima di scrivere il nome di un modello si apre la pagina del suo fornitore, non un esempio di un framework né un riassunto. Per il codice che usa l'SDK di Anthropic c'è anche la skill `claude-api`.

- Anthropic: modelli https://platform.claude.com/docs/en/models/overview, deprecazioni https://platform.claude.com/docs/en/about-claude/model-deprecations, migrazione https://platform.claude.com/docs/en/about-claude/models/migration-guide, elenco dei modelli https://platform.claude.com/docs/en/api/models/list, prezzi https://platform.claude.com/docs/en/about-claude/pricing
- Google (Gemini): modelli https://ai.google.dev/gemini-api/docs/models, deprecazioni https://ai.google.dev/gemini-api/docs/deprecations, elenco dei modelli https://ai.google.dev/api/models, novità https://ai.google.dev/gemini-api/docs/changelog, prezzi https://ai.google.dev/gemini-api/docs/pricing
- OpenAI: modelli https://developers.openai.com/api/docs/models, deprecazioni https://developers.openai.com/api/docs/deprecations, librerie https://developers.openai.com/api/docs/libraries
- OpenRouter: modelli https://openrouter.ai/docs/guides/overview/models.md, API https://openrouter.ai/docs/api_reference/overview.md
- Agno: modelli https://docs.agno.com/models/overview.md (i modelli di esempio di Agno possono essere indietro rispetto al fornitore)

## Fonti

Le regole sono scritte con parole nostre a partire dalle pagine ufficiali dei fornitori e dei framework, consultate il 2026-11-01, e dalle scelte dell'utente raccolte nel progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md, sezione 9). Delle pagine riportano i fatti, senza testo copiato: ogni regola dice da quale pagina e da quale sezione viene.

- Anthropic: https://platform.claude.com/docs/ (modelli, deprecazioni, migrazione, elenco dei modelli, prezzi, guida alla prompt injection, SDK)
- Google (Gemini): https://ai.google.dev/ (modelli, deprecazioni, riferimento dei modelli, novità, prezzi, librerie)
- OpenAI: https://developers.openai.com/ (modelli, deprecazioni, librerie) e i file README dei repository degli SDK Python e Node
- OpenRouter: https://openrouter.ai/docs/ (modelli, API, avvio rapido)
- Agno: https://docs.agno.com/ (modelli e import dei fornitori)
- Supabase: https://supabase.com/docs/ (import `npm:` delle funzioni edge, per i marcatori di `init`)

I marcatori con cui `init` riconosce il codice AI fuori dalle cartelle tipiche (`templates/profiles/ai.toml`) vengono dalle righe di import e dagli indirizzi delle API che quelle pagine mostrano.
