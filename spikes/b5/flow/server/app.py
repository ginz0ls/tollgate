"""Server di prova: una tabella di rotte e una funzione pura per ogni rotta, in sola libreria standard."""
from http.server import BaseHTTPRequestHandler


def hello():
    return 200, "text/plain; charset=utf-8", "ciao"


ROUTES = {("GET", "/hello"): hello}


def dispatch(method, path):
    """Restituisce (stato, tipo, corpo) della rotta, o un 404 se non esiste."""
    route = ROUTES.get((method, path))
    if route is None:
        return 404, "text/plain; charset=utf-8", "non trovato"
    return route()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, content_type, body = dispatch("GET", self.path)
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
