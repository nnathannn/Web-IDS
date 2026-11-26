from scapy.all import sniff

def pkt(pkt):
    print(pkt.summary())

sniff(prn=pkt, store=False)