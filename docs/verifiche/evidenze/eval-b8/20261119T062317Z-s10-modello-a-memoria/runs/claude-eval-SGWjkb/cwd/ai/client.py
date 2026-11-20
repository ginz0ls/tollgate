"""Client di prova: il nome del modello e il corpo della richiesta, senza rete."""
MODEL = "gemini-1.5-flash"


def build_request(prompt):
    return {"model": MODEL, "contents": [{"role": "user", "parts": [{"text": prompt}]}]}
