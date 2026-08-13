#!/usr/bin/env python3
"""03-b18b-cura.py — ⛔ LA PROVA DELLA CURA B-18, e non e' `03-b18-credito.py`.

  python3 03-b18b-cura.py --porta 7610 --parola-file … --registro …

===========================================================================
⛔⭐ PERCHE' QUESTO FILE ESISTE — `03-b18-credito.py` NON ARRIVA AL SUO CASO

`[M]` 13 agosto 2026, sera, primo giro DAL VIVO di `03-b18-credito.py` (quel
banco aveva 6 controlli certificati a tre giri e **zero** giri sul prodotto):

    --credito 6  →  333 stream video aperti in 30 s, credito MAI esaurito
    --credito 4  →  264 stream video aperti in 25 s, credito MAI esaurito
    ⇒ C2, C3, C4, C5 e C6 tutti NON PROVATO.  Solo C1 (la premessa) e' VERDE.

⛔ La ragione sta in `aioquic/quic/connection.py:_write_connection_limits`:

       if limit.used * 2 > limit.value:
           limit.value *= 2

   cioe' il pari **raddoppia** il limite appena se ne consuma meta'.  Su
   loopback il giro di rete e' di un decimo di millisecondo e il codificatore
   fa ~11 fotogrammi al secondo: il credito torna sempre prima che serva, e il
   caso di §2.3 non si presenta MAI.  ⚠ Non e' un difetto del prodotto: e' una
   scena che il banco non riesce a costruire.

⛔ E NON SI RIMEDIA COME FA `03-b15-movimento.py`, che abbassa
   `_local_max_streams_uni.value` **dopo** la stretta di mano: quello e' un
   credito RINNEGATO, RFC 9000 §4.6 lo vieta, e `[M]` in questo stesso giro il
   registro del server lo dice parola per parola — «stream uni 15 aperto; ngtcp2
   dice che ne restano 124», cioe' sul filo erano andati **128** mentre il banco
   credeva di averne annunciati 6.  ⇒ La sessione muore con «Too many streams
   open» e il rosso finisce sull'imputato sbagliato.

⭐ QUI SI FA IN TRE MOSSE, E TUTTE E TRE PRIMA CHE UN BYTE PARTA:

  1. il credito si fissa **nel costruttore** (come `03-b18-credito.py`, che su
     questo ha ragione) — cosi' finisce nel ClientHello e non e' un rinnegamento;
  2. ⭐ si **blocca il raddoppio**: finche' la pinza e' chiusa,
     `_write_connection_limits` gira su una copia del limite con `used = 0` e
     `sent = value`, quindi non alza niente e non manda nessun `MAX_STREAMS`.
     ⇒ Il credito si esaurisce **davvero**, e resta esaurito;
  3. ⭐⭐ e poi **SI RILASCIA**.  E' questa la mossa che prova la cura invece di
     limitarsi ad armarla: `03-b18-credito.py`, anche se ci arrivasse, guarda una
     RIGA DI REGISTRO («la cura e' armata»).  ⛔ Ma B-18 non e' «il flag si
     accende»: e' «al decodificatore manca un delta e non gliene tornera' mai
     uno buono».  ⇒ La domanda vera e' **che cosa arriva sul filo quando il
     posto torna**, e ha due sole risposte:

         CHIAVE 0x0301  →  l'immagine si ricuce, la cura c'e'
         delta  0x0302  →  l'immagine resta sfasciata per sempre — B-18

===========================================================================
⛔ IL VERDETTO, E COME SI LEGGE

  V1  il credito e' stato annunciato COM'E' SCRITTO (la spia sul ClientHello:
      la premessa si misura, non si crede — e' la prima regola di 03-b18)
  V2  il credito si e' esaurito DAVVERO e almeno un DELTA e' stato saltato per
      mancanza di posto (la riga di §2.3 nel registro del server)
  V3  ⭐ la CURA e' ARMATA: il registro dice «§5.2 vuole una CHIAVE (un delta e'
      stato saltato per mancanza di posto)» — e' quel che C6 di 03-b18 guarda
  V4  ⛔⭐ LA CURA FUNZIONA: il PRIMO fotogramma arrivato dopo il rilascio e'
      una CHIAVE 0x0301.  ⚠ Questo e' l'unico controllo che B-18 lo prova; gli
      altri tre lo preparano.
"""
import argparse
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
INTESTAZIONE, CHIAVE, DELTA, WT_UNI = 28, 0x0301, 0x0302, 0x54
VERDE, ROSSO, NON_PROVATO = "VERDE", "ROSSO", "NON PROVATO"


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Flusso:
    """Uno stream video come e' arrivato — la stessa forma di 03-b15."""

    def __init__(self, sid, quando):
        self.sid, self.quando = sid, quando
        self.grezzo = bytearray()
        self.letta = False
        self.tipo = self.numero = None
        self.byte = 0
        self.fine = None

    def arrivano(self, d):
        if not self.letta:
            self.grezzo += d
            if len(self.grezzo) >= INTESTAZIONE:
                g = bytes(self.grezzo[:INTESTAZIONE])
                self.tipo, _, _, _, self.numero, _, _ = struct.unpack("!HHIIIQI", g)
                self.byte = len(self.grezzo) - INTESTAZIONE
                self.letta = True
                self.grezzo = bytearray()
        else:
            self.byte += len(d)


def costruisci_cliente(a, b3):
    from aioquic.quic.connection import Limit

    class Pinza(b3.Cliente):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self.video, self.visti, self.finiti = {}, set(), []
            self.t0 = time.monotonic()
            self.caduta = None
            self.annunciato = None
            self.rilasciato_a = None
            q = self._quic

            # 1. Il credito, PRIMA della stretta di mano.
            q._local_max_streams_uni.value = a.credito
            q._local_max_streams_uni.sent = a.credito

            # ⭐ La spia: che cosa e' finito DAVVERO nel ClientHello.  Senza,
            #   ogni rosso di questo file potrebbe essere il rosso di una scena
            #   mai esistita — la lezione che 03-b18 ha pagato per tutti.
            vero_tp = getattr(q, "_serialize_transport_parameters", None)
            if vero_tp is not None:
                def spia():
                    self.annunciato = q._local_max_streams_uni.value
                    return vero_tp()
                q._serialize_transport_parameters = spia

            # 2. La PINZA sul raddoppio.  ⛔ Non si tocca il valore annunciato
            #    (sarebbe un rinnegamento): si impedisce solo che CRESCA.
            self.pinza_chiusa = True
            vero_wcl = q._write_connection_limits

            def mio_wcl(builder, space):
                if not self.pinza_chiusa:
                    return vero_wcl(builder, space)
                salvo = q._local_max_streams_uni
                finto = Limit(frame_type=salvo.frame_type, name=salvo.name,
                              value=salvo.value)
                finto.sent = salvo.value   # ⇒ niente MAX_STREAMS da mandare
                finto.used = 0             # ⇒ niente raddoppio
                q._local_max_streams_uni = finto
                try:
                    return vero_wcl(builder, space)
                finally:
                    q._local_max_streams_uni = salvo

            q._write_connection_limits = mio_wcl

        # 3. Il rilascio.
        def rilascia(self, quanto=500):
            self.pinza_chiusa = False
            self._quic._local_max_streams_uni.value = quanto
            self.rilasciato_a = time.monotonic() - self.t0
            self.transmit()

        @staticmethod
        def _vint(b, i):
            if i >= len(b):
                return None, i
            n = 1 << (b[i] >> 6)
            if i + n > len(b):
                return None, i
            v = b[i] & 0x3F
            for k in range(1, n):
                v = (v << 8) | b[i + k]
            return v, i + n

        def _arrivano(self, sid, dati, fine):
            f = self.video.get(sid)
            if f is None:
                return
            f.arrivano(dati)
            if fine:
                f.fine = "fin"
                f.finito_a = time.monotonic() - self.t0
                self.finiti.append(f)
                del self.video[sid]

        def _smista(self, event):
            sid = event.stream_id
            if sid in self.visti:
                self._arrivano(sid, event.data, event.end_stream)
                return True
            if (sid & 0x03) != 0x03 or sid == self.sessione:
                return False
            d = event.data
            if len(d) < 2 or d[0] != 0x40 or d[1] != WT_UNI:
                return False
            tipo, i = self._vint(d, 0)
            ses, i = self._vint(d, i)
            if tipo != WT_UNI or ses is None:
                return False
            self.visti.add(sid)
            self.video[sid] = Flusso(sid, time.monotonic() - self.t0)
            self._arrivano(sid, bytes(d[i:]), event.end_stream)
            return True

        def quic_event_received(self, event):
            nome = type(event).__name__
            if nome == "ConnectionTerminated":
                self.caduta = (f"codice 0x{event.error_code:02x} — "
                               f"{event.reason_phrase!r}")
            elif nome == "StreamDataReceived" and self._smista(event):
                return
            elif nome == "StreamReset" and event.stream_id in self.visti:
                f = self.video.pop(event.stream_id, None)
                if f is not None:
                    f.fine = "reset"
                    f.finito_a = time.monotonic() - self.t0
                    self.finiti.append(f)
                return
            super().quic_event_received(event)

    return Pinza


async def giro(a):
    import asyncio
    b3 = _porta("b3", "01-b3-cliente.py")
    from aioquic.asyncio import connect
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    Cliente = costruisci_cliente(a, b3)
    v = {"annunciato": None, "caduta": None, "flussi": [], "rilasciato_a": None}

    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        try:
            await asyncio.wait_for(cli.wait_connected(), timeout=10)
            v["annunciato"] = cli.annunciato
            cli.apri_sessione(autorita, a.percorso)
            stato = await asyncio.wait_for(cli.accettata, timeout=10)
            if stato != "200":
                v["caduta"] = f"la CONNECT estesa ha risposto {stato}"
                return v
            cli.apri_controllo()
            cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
            await b3.attendi(cli, "ECCOMI")
            cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                  b3.s(a.utente) + b3.s(a.parola)))
            await b3.attendi(cli, "AMMESSO", attesa=25)
            cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                  struct.pack("!IIII", a.larghezza, a.altezza,
                                              a.larghezza, a.altezza)
                                  + b3.s(a.disposizione)))
            await b3.attendi(cli, "SESSIONE", attesa=15)

            # ⛔ LA PINZA CHIUSA: si aspetta che il credito finisca e che il
            #    server abbia il tempo di saltare piu' di un delta.
            fine = time.monotonic() + a.stringi
            while time.monotonic() < fine and not cli.caduta:
                await asyncio.sleep(0.05)
            v["prima_del_rilascio"] = len(cli.finiti)

            # ⭐⭐ IL RILASCIO — la mossa che prova la cura.
            if not cli.caduta:
                cli.rilascia()
            fine = time.monotonic() + a.dopo
            while time.monotonic() < fine and not cli.caduta:
                await asyncio.sleep(0.05)
        except Exception as e:                          # noqa: BLE001
            if v["caduta"] is None:
                v["caduta"] = f"{type(e).__name__}: {e}"
        if cli.caduta:
            v["caduta"] = cli.caduta
        v["rilasciato_a"] = cli.rilasciato_a
        v["flussi"] = [{"sid": f.sid, "tipo": f.tipo, "numero": f.numero,
                        "byte": f.byte, "fine": f.fine, "quando": f.quando,
                        "letta": f.letta} for f in cli.finiti]
    return v


def leggi_registro(percorso, da):
    if not percorso:
        return []
    try:
        with open(percorso) as f:
            return f.read().splitlines()[da:]
    except OSError as e:
        print(f"   ⛔ il registro non si legge: {e}")
        return []


def conta_righe(percorso):
    try:
        with open(percorso) as f:
            return len(f.read().splitlines())
    except OSError:
        return 0


def verdetto(v, reg, credito):
    fuori = []

    # V1 — la premessa.
    if v["annunciato"] is None:
        fuori.append(("V1-annuncio", NON_PROVATO,
                      "la spia sul ClientHello non ha catturato niente: senza, "
                      "ogni rosso qui sotto non varrebbe niente"))
    elif v["annunciato"] != credito:
        fuori.append(("V1-annuncio", ROSSO,
                      f"⛔ IL BANCO MENTE: credeva di annunciare {credito} e sul "
                      f"filo ne sono andati {v['annunciato']}"))
    else:
        fuori.append(("V1-annuncio", VERDE,
                      f"sul filo e' andato initial_max_streams_uni = "
                      f"{v['annunciato']}, cioe' quel che questo banco crede"))

    saltati = [r for r in reg if "§2.3" in r and "stream unidirezionale" in r
               and "delta" in r]
    # ⛔⭐ I TRE MODI IN CUI IL PRODOTTO DICE «LA CURA E' ARMATA», e il primo
    #     giro dal vivo ha dimostrato che il marcatore scelto a tavolino era il
    #     piu' raro dei tre — anzi, quello che su un prodotto SANO non compare.
    #
    #     `[M]` 13 agosto 2026, sera, questo stesso file: V3 ha dato ROSSO — «il
    #     server non ha MAI acceso il debito di chiave» — nello stesso giro in
    #     cui V4 diceva VERDE, cioe' in cui la CHIAVE era arrivata sul filo.
    #     ⇒ Due controlli dello stesso file che si contraddicono: uno dei due
    #     mentiva, ed era V3.
    #
    # ⛔ La ragione e' strutturale: «⛔ FOTOGRAMMA NON SPEDITO: e' un delta e
    #    §5.2 vuole una CHIAVE» la scrive `rcp_video_apri()` quando CHI CHIAMA
    #    offre un delta col debito gia' acceso — cioe' solo quando il chiamante
    #    NON ha chiesto `rcp_video_serve_chiave()` prima di codificare.  Su un
    #    prodotto che si comporta bene quella riga non compare, e il debito si
    #    vede invece dalle due righe qui sotto (`[M]` 155 e 28 righe nello
    #    stesso giro).  ⚠ Un marcatore che si accende SOLO sul comportamento
    #    sbagliato del chiamante non e' la prova del comportamento giusto del
    #    server: e' il suo contrario.
    CURA_ARMATA = ("richiesta girata al palco",     # il debito e' arrivato al codificatore
                   "il debito resta acceso",        # il server sta offrendo una CHIAVE
                   "FOTOGRAMMA NON SPEDITO")        # la forma rara
    armate = [r for r in reg if any(m in r for m in CURA_ARMATA)]

    # V2 — il credito si e' esaurito DAVVERO.
    if not saltati:
        fuori.append(("V2-esaurito", NON_PROVATO,
                      "nessun delta e' stato saltato per mancanza di posto: la "
                      "scena non si e' costruita, e senza rifiuto non c'e' "
                      "niente da curare"))
    else:
        fuori.append(("V2-esaurito", VERDE,
                      f"{len(saltati)} delta saltati per mancanza di posto "
                      f"(§2.3): il rifiuto c'e' stato"))

    # V3 — la cura e' ARMATA (quel che C6 di 03-b18 guarda).
    if not saltati:
        fuori.append(("V3-armata", NON_PROVATO, "niente da armare"))
    elif not armate:
        fuori.append(("V3-armata", ROSSO,
                      f"⛔ {len(saltati)} delta saltati e il server non ha MAI "
                      f"acceso il debito di chiave: e' B-18 in piedi"))
    else:
        quali = sorted({m for m in CURA_ARMATA if any(m in r for r in armate)})
        fuori.append(("V3-armata", VERDE,
                      f"il debito di chiave e' acceso: {len(armate)} righe, "
                      f"marcatori «{'», «'.join(quali)}»"))

    # V4 — ⭐ LA CURA FUNZIONA.
    r = v.get("rilasciato_a")
    dopo = [f for f in v["flussi"]
            if r is not None and f["quando"] > r and f["letta"]]
    if not saltati:
        fuori.append(("V4-CURATO", NON_PROVATO,
                      "nessun delta e' stato saltato: non c'e' nessuna cura da "
                      "provare"))
    elif r is None:
        fuori.append(("V4-CURATO", NON_PROVATO,
                      "il credito non e' mai stato rilasciato"))
    elif not dopo:
        fuori.append(("V4-CURATO", NON_PROVATO,
                      "dopo il rilascio non e' arrivato NESSUN fotogramma con "
                      "l'intestazione leggibile: non ho niente da giudicare"))
    else:
        primo = dopo[0]
        if primo["tipo"] == CHIAVE:
            fuori.append(("V4-CURATO", VERDE,
                          f"⭐ il PRIMO fotogramma dopo il rilascio e' una "
                          f"CHIAVE 0x0301 (numero {primo['numero']}, "
                          f"{primo['byte']} byte): dopo un delta saltato per "
                          f"mancanza di posto arriva una chiave — B-18 e' CURATA "
                          f"sul filo, non solo nel registro"))
        else:
            fuori.append(("V4-CURATO", ROSSO,
                          f"⛔ il PRIMO fotogramma dopo il rilascio e' un delta "
                          f"0x{primo['tipo']:04X} (numero {primo['numero']}): al "
                          f"decodificatore manca un delta e gliene arriva un "
                          f"altro — l'immagine resta sfasciata per sempre e in "
                          f"silenzio.  E' B-18, viva"))
    return fuori


def principale():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=7610)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--credito", type=int, default=8,
                   help="⛔ HTTP/3 se ne prende TRE: 8 ⇒ 5 fotogrammi e poi buio")
    p.add_argument("--stringi", type=float, default=10.0,
                   help="secondi con la pinza CHIUSA")
    p.add_argument("--dopo", type=float, default=8.0,
                   help="secondi di osservazione DOPO il rilascio")
    p.add_argument("--registro", default="")
    p.add_argument("--uscita", default="")
    p.add_argument("--nota", default="",
                   help="⛔ che cos'era il PRODOTTO in questo giro (sano o con "
                        "quale ago): finisce nella riga di `--uscita`.  ⚠ Un "
                        "file di esiti che mescola i due senza dirlo mette due "
                        "cose diverse sotto la stessa etichetta")
    a = p.parse_args()

    if a.parola_file:
        with open(a.parola_file) as f:
            a.parola = f.read().strip()

    import asyncio
    da = conta_righe(a.registro) if a.registro else 0
    v = asyncio.run(giro(a))
    reg = leggi_registro(a.registro, da)

    print(f"\n\033[1m== Che cosa e' arrivato sul filo\033[0m")
    print(f"    --  credito annunciato: {v['annunciato']} "
          f"({(v['annunciato'] or 0) - 3} a RCP, HTTP/3 ne prende 3)")
    print(f"    --  fotogrammi prima del rilascio: "
          f"{v.get('prima_del_rilascio', '?')}")
    print(f"    --  rilascio al secondo {v['rilasciato_a']}")
    print(f"    --  fotogrammi in tutto: {len(v['flussi'])}")
    for f in v["flussi"]:
        marca = "CHIAVE" if f["tipo"] == CHIAVE else (
            f"0x{f['tipo']:04X}" if f["tipo"] else "?")
        dopo = "  ⭐ DOPO IL RILASCIO" if (v["rilasciato_a"] is not None
                                          and f["quando"] > v["rilasciato_a"]) else ""
        print(f"        n.{f['numero']} {marca:<7} {f['byte']:>7} byte  "
              f"{f['fine']}  a {f['quando']:.2f} s{dopo}")
    if v["caduta"]:
        print(f"    --  la sessione e' caduta: {v['caduta']}")
    print(f"    --  righe nuove nel registro del server: {len(reg)}")

    print(f"\n\033[1m== Il verdetto\033[0m")
    rossi = 0
    esiti = verdetto(v, reg, a.credito)
    for nome, esito, dice in esiti:
        colore = {"VERDE": "\033[1;32m", "ROSSO": "\033[1;31m"}.get(
            esito, "\033[1;33m")
        print(f"  {colore}{esito:<11}\033[0m {nome:<12} {dice}")
        if esito == ROSSO:
            rossi += 1
    if a.uscita:
        with open(a.uscita, "a") as f:
            f.write(json.dumps({"quando": time.strftime("%FT%T"),
                                "banco": "03-b18b-cura", "porta": a.porta,
                                "credito": a.credito,
                                "prodotto": a.nota or "⚠ NON DICHIARATO",
                                "verbale": v,
                                "esiti": [{"controllo": n, "esito": e,
                                           "dice": d} for n, e, d in esiti]},
                               ensure_ascii=False) + "\n")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(principale())
