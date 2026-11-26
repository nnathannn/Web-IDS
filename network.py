# from http.server import BaseHTTPRequestHandler, HTTPServer
# import ssl
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.nodelib import NAT
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.moduledeps import pathCheck
import random

class IDSTopo(Topo):    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        server = self.addHost('server', ip='10.0.0.1/24')
        ids = self.addHost('ids', ip='10.0.0.2/24')
        device = self.addHost('device', ip='10.0.0.3/24')
        switch = self.addSwitch('s1')
        router = self.addHost('gateway', ip='10.0.0.254/24')

        root = self.addNode('root', inNamespace=False, ip='10.0.2.1/24')
        test = self.addHost('test', ip='10.0.1.1/24')
        # nat = self.addHost('nat0', cls=NAT, ip='10.0.2.1/24')
        
        self.addLink(server, switch)
        self.addLink(ids, switch)
        self.addLink(device, switch)
        self.addLink(switch, router)
        self.addLink(router, test)
        # self.addLink(router, nat)
        self.addLink(router, root)


topo = IDSTopo()
net = Mininet(topo=topo, controller=Controller)
net.start()

gw, server, ids, device, test, switch, root = net.get('gateway', 'server', 'ids', 'device', 'test', 's1', 'root')

gw.cmd('sysctl -w net.ipv4.ip_forward=1')
gw.cmd('ip addr add 10.0.1.254/24 dev gateway-eth1')
gw.cmd('ip addr add 10.0.2.254/24 dev gateway-eth2')
# root.cmd('ip addr add 10.0.2.1/24 dev root-eth0')

server.cmd('ip route add default via 10.0.0.254')
ids.cmd('ip route add default via 10.0.0.254')
device.cmd('ip route add default via 10.0.0.254')
test.cmd('ip route add default via 10.0.1.254')
# nat.cmd('ip route add default via 10.0.2.254')
# nat.configDefault()
root.cmd('ip route add default via 10.0.2.254')

switch.cmd('ovs-ofctl del-flows s1')
switch.cmd('ovs-ofctl add-flow s1 "priority=0,actions=normal"')
switch.cmd('ovs-ofctl add-flow s1 "priority=0,actions=output:2,normal"')

CLI(net)
net.stop()
