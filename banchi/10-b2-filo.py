#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b2-filo — ⭐ IL TESTIMONE SUL FILO, pacchetto per pacchetto.

Gira **da root sulla macchina di prova** e guarda `enp7s0` con un socket
`AF_PACKET`: per ogni datagramma UDP fra il pari dichiarato e la porta
dichiarata scrive **quando** e' passato e **in che verso**.

⛔ PERCHE' NON BASTANO I CONTATORI `nft` DI `10-b90-filo.py`: quelli danno
   quanti byte e quanti pacchetti, non **ogni quanto**.  E la domanda di questo
   banco — *«chi tiene viva la linea, e con che cadenza»* — e' una domanda di
   CADENZA: un browser che manda un `PING` QUIC ogni due secondi e un server
   che manda un fotogramma ogni 33 ms fanno lo stesso numero di byte in due
   letture lontane, e sono due fatti opposti.

⛔ E NON C'E' `tcpdump` SU QUESTA MACCHINA (verificato il 24 agosto 2026, anche
   da root): questo file esiste per quello.

⚠⚠ CHE COSA QUESTO METRO **NON** SA DIRE, detto prima e non dopo:
   1. ⛔ **Non legge dentro QUIC**: i datagrammi sono cifrati.  Sa dire CHI ha
      mandato e QUANDO e QUANTO, non *«era un `PING`»*.  ⇒ «il browser si tiene
      vivo da se'» si DEDUCE da «il server non manda niente e il cliente manda
      lo stesso», e la deduzione va scritta come tale.
   2. ⛔ Vede solo il traffico che passa da `enp7s0`: niente `lo`.
   3. ⚠ Conta la **lunghezza IP** (come `10-b90-filo.py`), non la cornice
      ethernet: sul rame ci sono ~2,6 % di byte in piu'.
   4. ⚠ Un pacchetto perso **fra il punto di cattura e il pari** e' contato
      come passato: questo e' il filo *del server*, non quello del browser.

Uso, sulla macchina di prova, da root:

    python3 10-b2-filo.py --porta 8120 --pari 192.168.0.3 \
                           --secondi 130 --fuori /media/REMOTIX/tmp/10b2/filo.jsonl

    python3 10-b2-filo.py --certifica        # senza rete: i guasti innestati
    python3 10-b2-filo.py --tara --porta 8120 --pari 192.168.0.3   # il metro
"""
import argparse
import json
import os
import socket
import struct
import sys
import time

ETH_P_ALL = 3


# ═══════════════════════════════════════════════════════════════════════════
# IL PARSER — una funzione pura, cosi' si puo' certificare senza rete
# ═══════════════════════════════════════════════════════════════════════════
def leggi_quadro(b, porta, pari_bin):
    """Torna `(verso, lung_ip, sorgente, destinazione)` oppure `None`.

    ⛔ `None` vuol dire **«non e' roba mia»**, e non «zero byte»: chi chiama
       non deve poterli confondere.  ⚠ E ogni caso storto — quadro troncato,
       protocollo che non e' IPv4, IP con opzioni, UDP tagliato — torna `None`
       invece di indovinare.
    """
    if len(b) < 14:
        return None
    etype = struct.unpack("!H", b[12:14])[0]
    off = 14
    if etype == 0x8100:                      # VLAN: si salta il tag
        if len(b) < 18:
            return None
        etype = struct.unpack("!H", b[16:18])[0]
        off = 18
    if etype != 0x0800:                      # non IPv4
        return None
    if len(b) < off + 20:
        return None
    vihl = b[off]
    if (vihl >> 4) != 4:
        return None
    ihl = (vihl & 0x0F) * 4
    if ihl < 20 or len(b) < off + ihl + 8:
        return None
    lung_ip = struct.unpack("!H", b[off + 2:off + 4])[0]
    proto = b[off + 9]
    if proto != 17:                          # non UDP
        return None
    src = b[off + 12:off + 16]
    dst = b[off + 16:off + 20]
    u = off + ihl
    sport, dport = struct.unpack("!HH", b[u:u + 4])
    if sport == porta and src != pari_bin and dst == pari_bin:
        return ("s2c", lung_ip, sport, dport)
    if dport == porta and src == pari_bin and dst != pari_bin:
        return ("c2s", lung_ip, sport, dport)
    return None


def sniffa(iface, porta, pari, secondi, fuori):
    pari_bin = socket.inet_aton(pari)
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
    s.bind((iface, 0))
    s.settimeout(0.5)
    t0 = time.time()
    n = {"c2s": 0, "s2c": 0}
    byte = {"c2s": 0, "s2c": 0}
    # ⛔⭐ RIGA PER RIGA, E NON A BLOCCHI — `[M]` 24 agosto 2026, e il banco ha
    #     perso un giro intero per impararlo.  Con la bufferizzazione normale i
    #     pacchetti restano in memoria finche' il blocco non e' pieno; il banco
    #     spegne il testimone con un segnale a fine giro, il blocco non arriva
    #     mai su disco, e il file contiene **solo la riga d'inizio**.  ⚠ Il
    #     sintomo era la forma peggiore: «il filo non ha visto passare NIENTE»
    #     su una linea che aveva portato la sessione per due minuti.
    f = open(fuori, "w", buffering=1)
    f.write(json.dumps({"tipo": "inizio", "t": t0, "iface": iface,
                        "porta": porta, "pari": pari,
                        "secondi": secondi}) + "\n")
    f.flush()
    try:
        while time.time() - t0 < secondi:
            try:
                b = s.recv(65535)
            except socket.timeout:
                continue
            t = time.time()
            r = leggi_quadro(b, porta, pari_bin)
            if r is None:
                continue
            verso, lung, sp, dp = r
            n[verso] += 1
            byte[verso] += lung
            f.write(json.dumps({"t": round(t, 6), "v": verso, "l": lung}) + "\n")
    finally:
        f.write(json.dumps({"tipo": "fine", "t": time.time(),
                            "n": n, "byte": byte}) + "\n")
        f.close()
        s.close()
    return n, byte


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA TARATURA — si inietta un numero NOTO e si guarda se il metro lo ritrova
# ═══════════════════════════════════════════════════════════════════════════
def tara(iface, porta, pari, quanti_s2c=25, carico=100):
    """Manda `quanti_s2c` datagrammi verso il pari **mentre si guarda**.

    ⭐ Il conto e' ASIMMETRICO apposta rispetto a quello che il portatile manda
       in senso opposto: un metro che scambiasse i due versi darebbe due numeri
       che si somigliano, e due numeri che si somigliano non smascherano
       niente.
    """
    import threading
    ris = {}

    def guarda():
        ris["n"], ris["byte"] = sniffa(iface, porta, pari, 6.0, "/tmp/10b2-tara.jsonl")

    th = threading.Thread(target=guarda)
    th.start()
    time.sleep(1.0)
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    u.bind(("", porta))
    for _ in range(quanti_s2c):
        u.sendto(b"T" * carico, (pari, 39999))
        time.sleep(0.01)
    u.close()
    th.join()
    atteso_byte = quanti_s2c * (carico + 28)
    print("taratura: mandati %d datagrammi da %d B di carico verso %s"
          % (quanti_s2c, carico, pari))
    print("          il metro ha visto s2c = %d pacchetti, %d byte (attesi %d, %d)"
          % (ris["n"]["s2c"], ris["byte"]["s2c"], quanti_s2c, atteso_byte))
    print("          e c2s = %d pacchetti (dal portatile, non da me)"
          % ris["n"]["c2s"])
    bene = (ris["n"]["s2c"] == quanti_s2c and ris["byte"]["s2c"] == atteso_byte)
    print("⭐ METRO TARATO" if bene else "⛔ METRO NON TARATO: non misuro")
    return 0 if bene else 3


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I GUASTI INNESTATI — sul parser, senza rete e senza macchina
# ═══════════════════════════════════════════════════════════════════════════
def _quadro(src, dst, sport, dport, carico=100, etype=0x0800, proto=17,
            ihl=5, tronca=0, ver=4):
    ip = bytearray(ihl * 4)
    ip[0] = (ver << 4) | ihl
    lung = ihl * 4 + 8 + carico
    ip[2:4] = struct.pack("!H", lung)
    ip[9] = proto
    ip[12:16] = socket.inet_aton(src)
    ip[16:20] = socket.inet_aton(dst)
    udp = struct.pack("!HHHH", sport, dport, 8 + carico, 0)
    eth = b"\x00" * 12 + struct.pack("!H", etype)
    q = eth + bytes(ip) + udp + b"\x00" * carico
    return q[:len(q) - tronca] if tronca else q


def certifica():
    P, PARI = 8120, "192.168.0.3"
    pb = socket.inet_aton(PARI)
    casi = []

    def caso(nome, quadro, atteso):
        r = leggi_quadro(quadro, P, pb)
        avuto = None if r is None else r[0]
        casi.append((nome, atteso, avuto, avuto == atteso))

    # ── sano ──────────────────────────────────────────────────────────────
    caso("sano · dal cliente verso la mia porta",
         _quadro(PARI, "192.168.0.2", 55555, P), "c2s")
    caso("sano · dal server verso il cliente",
         _quadro("192.168.0.2", PARI, P, 55555), "s2c")
    # ── i guasti ──────────────────────────────────────────────────────────
    caso("⛔ un'ALTRA porta (8030, il banco del vicino) ⇒ non e' mia",
         _quadro(PARI, "192.168.0.2", 55555, 8030), None)
    caso("⛔ un TERZO indirizzo sulla mia porta ⇒ non e' il mio pari",
         _quadro("192.168.0.9", "192.168.0.2", 55555, P), None)
    caso("⛔ TCP invece di UDP sulla stessa porta",
         _quadro(PARI, "192.168.0.2", 55555, P, proto=6), None)
    caso("⛔ non IPv4 (IPv6 sul filo)",
         _quadro(PARI, "192.168.0.2", 55555, P, etype=0x86DD), None)
    caso("⛔ ARP",
         _quadro(PARI, "192.168.0.2", 55555, P, etype=0x0806), None)
    caso("⛔ quadro TRONCATO a meta' intestazione UDP",
         _quadro(PARI, "192.168.0.2", 55555, P, tronca=104), None)
    caso("⛔ quadro vuoto", b"", None)
    caso("⛔ solo l'ethernet", b"\x00" * 14, None)
    caso("⛔ versione IP = 6 dentro un ethertype IPv4",
         _quadro(PARI, "192.168.0.2", 55555, P, ver=6), None)
    caso("⛔ IHL fuori scala (3)",
         _quadro(PARI, "192.168.0.2", 55555, P, ihl=3), None)
    caso("⭐ IP con OPZIONI (IHL=6): si legge lo stesso",
         _quadro(PARI, "192.168.0.2", 55555, P, ihl=6), "c2s")
    caso("⭐ dentro una VLAN: si legge lo stesso",
         _quadro(PARI, "192.168.0.2", 55555, P, etype=0x8100)[:12]
         + struct.pack("!H", 0x8100) + b"\x00\x64" + struct.pack("!H", 0x0800)
         + _quadro(PARI, "192.168.0.2", 55555, P)[14:], "c2s"),
    caso("⛔ il cliente che parla a se stesso sulla mia porta (src=dst=pari)",
         _quadro(PARI, PARI, 55555, P), None)

    # ── la lunghezza IP, che e' la grandezza che si riferisce ────────────
    r = leggi_quadro(_quadro(PARI, "192.168.0.2", 55555, P, carico=1000), P, pb)
    lung_ok = (r is not None and r[1] == 1028)
    casi.append(("⭐ 1000 B di carico ⇒ 1028 B di lunghezza IP",
                 1028, None if r is None else r[1], lung_ok))

    # ── ⛔ il verso SCAMBIATO: il guasto che nessun conteggio smaschera ──
    r1 = leggi_quadro(_quadro(PARI, "192.168.0.2", 55555, P), P, pb)
    r2 = leggi_quadro(_quadro("192.168.0.2", PARI, P, 55555), P, pb)
    casi.append(("⛔ i due versi NON si confondono", "c2s/s2c",
                 "%s/%s" % (r1[0], r2[0]), r1[0] != r2[0]))

    buoni = sum(1 for c in casi if c[3])
    for nome, atteso, avuto, bene in casi:
        print("    %s %-58s atteso %-6s avuto %s"
              % ("\033[1;32mOK\033[0m" if bene else "\033[1;31mNO\033[0m",
                 nome, atteso, avuto))
    print("\n  %d su %d" % (buoni, len(casi)))
    return 0 if buoni == len(casi) else 3


def principale():
    a = argparse.ArgumentParser()
    a.add_argument("--iface", default="enp7s0")
    a.add_argument("--porta", type=int, default=8120)
    a.add_argument("--pari", default="192.168.0.3")
    a.add_argument("--secondi", type=float, default=120.0)
    a.add_argument("--fuori", default="/media/REMOTIX/tmp/10b2/filo.jsonl")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--tara", action="store_true")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if os.geteuid() != 0:
        print("⛔ serve root: AF_PACKET non si apre da utente")
        return 2
    if o.tara:
        return tara(o.iface, o.porta, o.pari)
    n, b = sniffa(o.iface, o.porta, o.pari, o.secondi, o.fuori)
    print(json.dumps({"n": n, "byte": b}))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
