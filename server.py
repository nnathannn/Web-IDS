from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<html><body><h1>test</h1></body></html>".encode("utf-8"))
        return

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

server = LogServer(('', 8080), Server)
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()