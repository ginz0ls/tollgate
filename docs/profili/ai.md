# Regole del profilo ai di tollgate

Questa pagina è per te: dice quali sono le regole per il codice che usa modelli di intelligenza artificiale e cosa hai deciso su quattro punti dubbi. Le regole sono approvate e il profilo si può accendere.

Approvata dall'utente il 2026-11-02.

## Cosa sono

Sono undici regole in più rispetto a quelle di base. Valgono solo per il codice che chiama un modello (Claude, Gemini, OpenAI, OpenRouter, Agno). Dicono, per esempio, dove scrivere il nome del modello, quale modello scegliere e da dove prendere i limiti e i prezzi.

Qualche parola, la prima volta che serve:

- **API**: il modo in cui un programma parla con un servizio, qui con il modello.
- **ID del modello**: il nome tecnico che si scrive nel codice per scegliere un modello.
- **Alias**: un nome comodo che punta a un modello e può passare da solo a un altro più nuovo.
- **Prompt injection**: un testo nascosto in un contenuto (una pagina web, un'email) che prova a dare ordini al modello al posto di chi lo usa.
- **`tool_result`**: il blocco dei messaggi dell'API di Anthropic dove va il risultato di uno strumento o un contenuto di altri, tenuto separato dalle istruzioni.

Valgono per chi scrive il codice e per chi lo rivede. Chi scrive può essere un agente a cui è affidato un task, cioè un pezzo del lavoro. Può essere anche Claude Code che lavora direttamente con te.

Chi rivede guarda tre cose. Il «diff» è l'elenco delle righe cambiate. Il «report» è il resoconto che l'agente scrive alla fine. La «nota di ricerca» è l'elenco di cosa ha letto prima di scrivere. Per ogni regola chi rivede risponde sì o no. Per ogni regola la tabella dice su quale delle tre guarda, nella colonna «Si giudica su»: la regola R-AI-01, per esempio, si giudica sul solo diff. Le regole 9 e 10 si appoggiano solo a pagine di Anthropic: la 9 vale con l'API di Anthropic, la 10 con Claude.

## Quando si accende

Il profilo non si accende da solo. Si accende solo in un progetto dove il comando `/tollgate:init` lo propone e tu copi il blocco proposto nel `tollgate.toml` del progetto. Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate la riceve con `/tollgate:init --update`. In tutti e due i casi la copia nel `tollgate.toml` la fai tu. Vale a partire dal livello L1, cioè dai lavori medi: i lavori piccoli (L0) non lo usano.

`init` lo propone se nel progetto trova una di queste due cose:

- cartelle con questi nomi: `llm/`, `prompts/`, `agents/`, `ai/`. Le cartelle di tollgate stesso e quelle degli agenti di Claude Code non contano;
- file di codice fuori da quelle cartelle che importano uno di questi pacchetti o chiamano una di queste API: anthropic, `@google/genai` e `google.golang.org/genai` (cioè Gemini), openai, openrouter, agno. I file di test non contano.

Chi l'ha già copiato lo tiene finché non lo toglie.

Una nota sulle parole: nella regola 3 «il più recente» vuol dire l'ultimo modello stabile della famiglia, non l'ultimo in assoluto. Un modello in anteprima non conta, a meno che il report spieghi perché lo usa.

## Le regole

| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |
|---|---|---|---|---|
|  1 (R-AI-01) | Il nome del modello sta in un solo punto del codice. Il resto, test compresi, legge quel punto. Si guarda solo il diff. | sì | il diff | La tua scelta nel progetto di B, e la pagina di Anthropic sugli ID dei modelli  |
|  2 (R-AI-02) | Accanto al nome del modello c'è l'indirizzo della pagina ufficiale dei modelli e la data in cui è stato controllato. | sì | il diff | La tua scelta nel progetto di B  |
|  3 (R-AI-03) | Se il lavoro scrive o cambia il nome di un modello, il report dice quale è l'ultimo modello stabile della famiglia, letto sulla pagina ufficiale. Si usa quello, oppure si spiega perché no. | sì | il report | La tua scelta nel progetto di B, e le pagine dei modelli di Anthropic, Google, OpenAI e OpenRouter  |
|  4 (R-AI-04) | Un modello in anteprima o sperimentale si usa solo se il report lo dice e spiega il motivo. | sì | il report | La tua scelta nel progetto di B, e le pagine di Google e OpenAI sulle anteprime  |
|  5 (R-AI-05) | Se il lavoro cambia il modello, il report cita la guida alla migrazione del modello nuovo e dice cosa ha cambiato per seguirla. Un modello nuovo può rifiutare impostazioni che il vecchio accettava. | sì | il report | La tua scelta nel progetto di B, e le guide di Anthropic, Google e OpenAI  |
|  6 (R-AI-06) | Ogni valore presentato come fatto del modello (limite di contesto o di uscita, prezzo, parametro accettato o rifiutato, valore predefinito) ha nel report l'indirizzo della pagina ufficiale da cui viene. Le scelte di configurazione del progetto (quanti token chiedere, quale temperatura impostare) restano fuori. Vedi «Cosa hai deciso». | sì | il report | Il progetto di B (limiti e parametri dalla documentazione) e le pagine dei modelli e dei prezzi dei fornitori  |
|  7 (R-AI-07) | Il codice nuovo che chiama un modello dà un errore chiaro se il modello non c'è più. L'errore dice quale modello e dove cambiarlo. | no | il diff | La tua scelta nel progetto di B, e le pagine sui ritiri di Anthropic, Google e OpenAI  |
|  8 (R-AI-08) | Un alias che si sposta da solo sul modello più nuovo (i nomi con `-latest` di Gemini, quelli con `~` e `-latest` di OpenRouter, i nomi senza data dei modelli Claude precedenti alla generazione 4.6) si usa solo se il report lo dice e spiega il motivo. | no | il report | La tua scelta nel progetto di B, e le pagine di Google, OpenRouter e Anthropic sugli alias  |
|  9 (R-AI-09) | Con l'API di Anthropic, il contenuto di altri (pagine web, email, documenti) va nei blocchi `tool_result`. Non va nel prompt di sistema né nel testo dell'utente. | no | il diff | La guida di Anthropic sulla prompt injection  |
|  10 (R-AI-10) | Con Claude, il lavoro non dà al modello segreti che non servono né strumenti con più permessi del necessario. | no | il diff | La guida di Anthropic sulla prompt injection  |
|  11 (R-AI-11) | Con Agno, l'ID del modello si scrive sempre in modo esplicito e non ci si affida al valore predefinito. Vedi «Cosa hai deciso». | no | il diff | Le pagine di Agno e la pagina dei ritiri di Anthropic  |

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. Le altre sono segnalate ma non lo fermano. Un difetto viene segnalato una sola volta.

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/ai-fonti.md`.

## Cosa hai deciso

Su quattro punti la fonte non diceva proprio quello che la regola chiede. Hai tenuto la proposta in tutti e quattro.

1. **Regola 6 (R-AI-06), l'indirizzo nel report.** Nessuna pagina chiede di scrivere l'indirizzo nel report: l'obbligo è una scelta nostra, perché chi rivede possa controllare il valore. Hai deciso di tenerlo.
2. **Regola 11 (R-AI-11), Agno.** L'obbligo di scrivere l'ID del modello viene dai fatti: Agno, se non glielo dici, usa un modello predefinito, e oggi quel modello è in ritiro (Anthropic lo spegne il 30 novembre 2026). Hai deciso di tenere la regola.
3. **Cosa vuol dire «stabile» per OpenAI e OpenRouter.** Hai approvato la lettura scelta: per OpenAI un modello senza «preview» nel nome e non in via di ritiro; per OpenRouter si guarda il fornitore originale, e un modello con la data di ritiro già scritta non si sceglie.
4. **Un marcatore in più, deciso da te.** I marcatori sono le righe di codice con cui `init` riconosce un progetto che usa un modello. Nessuna pagina mostra `from "openai"` con le virgolette doppie, ma è la stessa riga di import di `from 'openai'` scritta in un altro modo, ed è la forma più comune nei progetti TypeScript. Il 2 novembre 2026 hai deciso di tenerla, insieme a `from 'openai'` (virgolette singole), `import openai` e `npm:openai`.

## Regole tolte dalla verifica

Nessuna delle undici regole è uscita: ciascuna ha almeno una fonte che regge. Una regola della bozza, invece, non aveva una fonte che la reggesse, ed è rimasta fuori.

- **Il testo prodotto dal modello come dato non fidato.** La bozza chiedeva di trattare ciò che il modello risponde come non fidato, per esempio di non eseguirlo e di non metterlo in una pagina web senza controlli. La pagina di Anthropic sulla prompt injection parla di un'altra cosa: del contenuto di altri che entra nel modello, non di ciò che ne esce. Senza una fonte che regga, la regola è fuori. Se la rivuoi, dimmelo e cerchiamo una pagina che parli dell'uscita del modello.

## Se vuoi cambiare qualcosa

Per ogni regola puoi dirmi una di queste tre cose.

- **Va bene così.** La regola resta com'è.
- **Cambiala.** Dimmi cosa cambiare. Una regola cambiata nel senso o con una fonte nuova passa di nuovo dal controllo delle fonti.
- **Toglila.** La regola esce e il suo numero non si riusa: le altre tengono il loro.

I numeri delle regole, ora che sono approvate, non cambiano più. Se vorrai cambiare, aggiungere o togliere una regola, me lo dici e la sistemo.
