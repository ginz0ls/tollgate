---
name: off
description: Spegne tollgate su questa macchina, per sempre o per un numero di ore. Solo l'utente.
disable-model-invocation: true
argument-hint: "[ore]"
---

Il wrapper degli hook ha già spento tollgate quando hai digitato il comando, senza Python né DB.
Riferisci all'utente il messaggio dell'hook («tollgate spento…»). Ricordagli che con tollgate
spento non gira nessun guardrail locale, che il gate su GitHub resta attivo, e che si riaccende
con /tollgate:on. Non eseguire comandi.
