"""Token firmati del progetto di prova, nella forma `<utente>.<scadenza>.<firma>`: la firma è l'HMAC-SHA256 di
`<utente>.<scadenza>` con la chiave di firma, in base64 per URL senza `=` finali. La scadenza è in secondi."""
import base64
import hashlib
import hmac


def _signature(payload: str, secret: bytes) -> str:
    digest = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def sign(user: str, expires_at: int, secret: bytes) -> str:
    payload = f"{user}.{expires_at}"
    return f"{payload}.{_signature(payload, secret)}"


def verify(token: str, secret: bytes, *, now: int) -> str | None:
    """L'utente del token se la firma torna, altrimenti None. La scadenza non è ancora controllata."""
    parts = token.rsplit(".", 2)
    if len(parts) != 3:
        return None
    user, expires_at, signature = parts
    if signature != _signature(f"{user}.{expires_at}", secret):
        return None
    return user
