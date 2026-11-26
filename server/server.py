import ssl, json, secrets, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

PORT=8080
NONCE_TTL=60

USERS = {"alice": "alice", "alex": "alex"}
SESSIONS = {}

GATE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <p>Checking your browser…</p>
  <script>window.__NONCE__ = "{nonce}";</script>
  <script src="/collector.js"></script>
</body>
</html>
"""

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

    def session(self):
        return SESSIONS.get(self.get_session_id())

    def is_authenticated(self):
        return self.session() is not None

    def is_verified(self):
        s = self.session()
        return bool(s and s["verified"])

    def send_json(self, obj, status=200):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def serve_gate(self):
        if not self.is_authenticated():
            return self.redirect("/login")
        if self.is_verified():
            return self.send_html(SECURE_HTML)
        s = self.session()
        s["nonce"] = secrets.token_hex(16)
        s["nonce_exp"] = time.time() + NONCE_TTL
        self.send_html(GATE_HTML.replace("{nonce}", s["nonce"]))

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
        elif self.path == "/collector.js":
            with open("collector.js", "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/logout":
            SESSIONS.pop(self.get_session_id(), None)
            self.redirect("/login", "session_id=; Max-Age=0; Path=/; HttpOnly; Secure")
        elif self.path in ("/", "/secure", "/home"):
            self.serve_gate()
        else:
            self.send_html("<h1>404 Not Found</h1>", status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        if self.path == "/login":
            params = parse_qs(raw.decode("utf-8"))
            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]
            print(f"login attempt: username={username}, password={password}")
            if USERS.get(username) == password:
                token = secrets.token_hex(16)
                SESSIONS[token] = {"user": username, "verified": False,
                                   "nonce": None, "nonce_exp": 0, "fp": None}
                cookie = f"session_id={token}; Path=/; HttpOnly; Secure; SameSite=Lax"
                self.redirect("/secure", cookie)
            else:
                self.send_html("<p>Invalid credentials. <a href='/login'>Try again</a></p>", status=401)

        elif self.path == "/fp":
            s = self.session()
            if not s:
                return self.send_json({"verdict": "NO_SESSION"}, 401)
            try:
                payload = json.loads(raw)
            except ValueError:
                return self.send_json({"verdict": "BAD_REQUEST"}, 400)

            expected, exp = s["nonce"], s["nonce_exp"]
            s["nonce"], s["nonce_exp"] = None, 0

            sent = str(payload.get("nonce", ""))
            if not expected or time.time() > exp \
               or not secrets.compare_digest(sent, expected):
                return self.send_json({"verdict": "BAD_NONCE"}, 403)

            verdict = self.evaluate(payload)
            if verdict == "ALLOW":
                s["verified"] = True
                s["fp"] = payload
            self.send_json({"verdict": verdict})

    def evaluate(self, p):
        if p.get("webdriver") is True:
            return "AUTOMATION"
        if p.get("ua") != self.headers.get("User-Agent"):
            return "UA_MISMATCH"
        return "ALLOW"

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
        # print(newsocket.shared_ciphers())
        return newsocket, fromaddr


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

server = LogServer(('', PORT), Server)
print(f"Serving on port {PORT}")
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()