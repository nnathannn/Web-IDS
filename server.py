from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
import secrets

PORT=8080

USERS = {"alice": "alice", "alex": "alex"}
SESSIONS = set()

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<body>
  <h2>Login</h2>
  <form method="POST" action="/login">
    <input name="username" placeholder="Username" required /><br><br>
    <input name="password" type="password" placeholder="Password" required /><br><br>
    <button type="submit">Log In</button>
  </form>
</body>
</html>
"""

SECURE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <h2>Secure Area</h2>
  <p>Welcome! You are viewing a protected page over HTTPS.</p>
  <a href="/logout">Log Out</a>
</body>
</html>
"""

class Server(BaseHTTPRequestHandler):
    def get_session_id(self):
        if "Cookie" in self.headers:
            cookie = SimpleCookie()
            cookie.load(self.headers["Cookie"])
            if "session_id" in cookie:
                return cookie["session_id"].value
        return None

    def is_authenticated(self):
        return self.get_session_id() in SESSIONS

    def redirect(self, location, cookie_header=None):
        self.send_response(302)
        self.send_header("Location", location)
        if cookie_header:
            self.send_header("Set-Cookie", cookie_header)
        self.end_headers()

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_GET(self):
        if self.path == "/login":
            self.send_html(LOGIN_HTML)
        elif self.path == "/logout":
            SESSIONS.discard(self.get_session_id())
            self.redirect("/login", "session_id=; Max-Age=0; Path=/; HttpOnly; Secure")
        elif self.path in ("/", "/secure"):
            if self.is_authenticated():
                self.send_html(SECURE_HTML)
            else:
                self.redirect("/login")
        else:
            self.send_html("<h1>404 Not Found</h1>", status=404)

    def do_POST(self):
        if self.path == "/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            
            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]

            if USERS.get(username) == password:
                token = secrets.token_hex(16)
                SESSIONS.add(token)
                cookie = f"session_id={token}; Path=/; HttpOnly; Secure; SameSite=Lax"
                self.redirect("/secure", cookie)
            else:
                self.send_html("<p>Invalid credentials. <a href='/login'>Try again</a></p>", status=401)

class LogServer(HTTPServer):
    def get_request(self):
        newsocket, fromaddr = super().get_request()
        methods = [
            attr for attr in dir(newsocket)
            if callable(getattr(newsocket,attr)) and not attr.startswith("__")
        ]
        # print(type(newsocket))
        # print(methods)
        # print(fromaddr)
        # print(newsocket.version())
        # print(newsocket.cipher())
        print(newsocket.shared_ciphers())
        return newsocket, fromaddr


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

server = LogServer(('', PORT), Server)
print(f"Serving on port {PORT}")
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()