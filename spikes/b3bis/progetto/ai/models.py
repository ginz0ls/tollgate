# Modelli della prova vera di B3-bis, scelti apposta non aggiornati.
# Ogni modello ha accanto la pagina ufficiale e la data in cui il controller l'ha letta.

# Anthropic, https://platform.claude.com/docs/en/about-claude/model-deprecations (letta il 2026-11-05):
# attivo, ma della stessa linea esiste claude-sonnet-5-5.
ANTHROPIC_MODEL = "claude-sonnet-5"
# Anthropic, stessa pagina (2026-11-05): deprecato, ritiro previsto il 2026-11-30.
ANTHROPIC_OLD_MODEL = "claude-sonnet-4-5-20250929"

# Gemini, https://aistudio.google.com/docs/models (letta il 2026-11-05):
# stabile, ma della stessa variante esiste gemini-3.5-flash-lite.
GEMINI_MODEL = "gemini-3.1-flash-lite"

# OpenAI, https://developers.openai.com/api/docs/deprecations (letta il 2026-11-05):
# ritiro previsto il 2027-01-14.
OPENAI_MODEL = "gpt-4.1-2025-04-14"

# OpenRouter: nessun modello, perché senza chiave non si è potuto verificare un ID
# con una data di ritiro sulla pagina ufficiale.
