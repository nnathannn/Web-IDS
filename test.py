# from http.server import BaseHTTPRequestHandler, HTTPServer
# import ssl
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.moduledeps import pathCheck
import random

class IDSTopo(Topo):    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        server1 = self.addHost('alice', ip='10.0.0.1/24')
        server2 = self.addHost('alex', ip='10.0.0.2/24')
        server3 = self.addHost('mallory', ip='10.0.0.3/24')
        server4 = self.addHost('bob', ip='10.0.0.4/24')
        router = self.addSwitch( 'sw0')
        
        self.addLink(server1, router)
        self.addLink(server2, router)
        self.addLink(server3, router)
        self.addLink(server4, router)

tls12 = [
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "AES128-GCM-SHA256",
    "AES256-SHA256",
]

tls13 = [
    "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256"
]

def random_cipher(host):
    random12 = ":".join(random.sample(tls12, k=random.randint(1,3)))
    random13 = ":".join(random.sample(tls13, k=random.randint(1,2)))
    conf = f"""openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = {random12}
Ciphersuites = {random13}
    """

    host.cmd(f"cat << EOF > /tmp/openssl_{host.name}.cnf\n{conf}\nEOF")
    host.cmd(f"export OPENSSL_CONF=/tmp/openssl_{host.name}.cnf")

topo = IDSTopo()
net = Mininet(topo=topo, controller=Controller)
net.start()

for host in net.hosts:
    random_cipher(host)

CLI(net)
net.stop()

# class Server(BaseHTTPRequestHandler):
#     def do_GET(self):
#         self.send_response(200)
#         self.end_headers()
#         return

# class LogServer(HTTPServer):
#     def get_request(self):
#         newsocket, fromaddr = super().get_request()
#         methods = [
#             attr for attr in dir(newsocket)
#             if callable(getattr(newsocket,attr)) and not attr.startswith("__")
#         ]
#         print(type(newsocket))
#         print(methods)
#         print(fromaddr)
#         print(newsocket.version())
#         print(newsocket.cipher())
#         print(newsocket.selected_alpn_protocol())
#         return newsocket, fromaddr

# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

# server = LogServer(('', 8080), Server)
# server.socket = context.wrap_socket(server.socket, server_side=True)
# server.serve_forever()