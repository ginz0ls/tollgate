"""Riassunto di un testo con un modello Claude."""

PROMPT = "Riassumi in una frase il testo seguente.\n\n{testo}"


def riassumi(client, testo, model):
    """Chiede al modello `model` un riassunto di `testo` e restituisce il testo della risposta.

    `client` è un client dell'SDK di Anthropic già costruito dal chiamante."""
    risposta = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": PROMPT.format(testo=testo)}],
    )
    return risposta.content[0].text
