#!/usr/bin/env python3
"""06-b34-cliente.py — ⛔ IL CLIENT CHE BATTE UN TASTO, e che sa staccarsi
**con un tasto ancora giu'**.  Sottofase 6.2 — *la tastiera che rinasce*.

    python3 06-b34-cliente.py --porta 7721 --utente provat6 \\
            --parola-file /tmp/06-t/parola --disposizione it \\
            --copione 'L:z L:y L:@ P:28:1 P:28:0' --etichetta g1 \\
            --scena 'sessione it, testimone acceso'

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.

===========================================================================
⛔ PERCHE' UN CLIENT E NON IL BROWSER — e non e' una comodita'
===========================================================================

Il documento di fase (trappola 4) dice che **il pilota del browser non sa
tenere premuto** un tasto: manda sempre giu'-e-su.  E la trappola 3 dice che
**la pagina rilascia da sola** su `blur`/`visibilitychange`/`pagehide`
(`cl_rilascia_tutto`), ⇒ dal browser il server non ha quasi mai niente da
rilasciare, e **si certifica la pagina credendo di certificare il server**.

⛔ Il caso 4 di questa sottofase — `RCP.md` §11, *«la regola col rapporto
   danno/costo piu' alto del documento»* — vuole esattamente il contrario: una
   connessione che finisce **mentre un tasto e' premuto davvero**.  Qui il
   tasto si preme e non si rilascia, e poi si stacca.  ⭐ E' l'unico modo di
   misurare il SERVER invece della pagina.

⚠ E il prezzo si dichiara: questo client **non e' la pagina**, quindi non prova
  quel che la pagina fa.  Prova quel che il server fa quando la pagina non lo
  protegge — che e' la meta' che nessuno aveva mai guardato.

===========================================================================
⛔ IL CANALE DI INPUT — `RCP.md` §2.5 e §7.3
===========================================================================

Uno stream **unidirezionale**, aperto dal client, ⛔ **dopo aver ricevuto
`SESSIONE`**, e tenuto aperto.  Il canale si riconosce dal byte alto di `tipo`
(`0x01`), non dal numero dello stream.

    ├── u32 id             crescente, comincia da 1.  ⛔ 0 e' riservato
    └── u64 istante        microsecondi dell'orologio monotono del CLIENT

    LETTERA          (0x0104) + u32 carattere
    POSIZIONE_TASTO  (0x0105) + u16 codice · u8 premuto

⛔ L'`id` cresce su **tutto il canale**, non uno per tipo (§7.3).

⚠ E l'`istante` si scrive **coi microsecondi veri** (§7.3, rilievo R1.27): qui
  e' `time.monotonic()` in µs, e non un millisecondo moltiplicato per mille.

===========================================================================
⛔ I CODICI D'USCITA
===========================================================================

    0  il giro e' finito come chiesto
    2  la stretta di mano NON e' arrivata a SESSIONE — ⚠ e per i casi 5 e 3
       QUESTO E' L'ESITO ATTESO: il motivo del congedo sta nel JSON
    4  la connessione e' caduta prima della fine
"""
import argparse
import asyncio
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

RCP_LETTERA = 0x0104
RCP_POSIZIONE = 0x0105
RCP_DISPOSIZIONE = 0x0009


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ SI EREDITA, NON SI RISCRIVE: la stretta di mano e lo smistamento degli
#    stream di WebTransport hanno gia' pagato due difetti dal vivo (il
#    preambolo `40 54` e il contesto posto troppo tardi).
fc = _porta("fc", "02-filo-cliente.py")


def dimmi(*a):
    print(*a, flush=True)


class Fermati(Exception):
    """⛔ «Mi fermo qui», e NON e' un errore.

    Per i casi 3 e 5 il congedo del server **e' il risultato atteso**, non un
    incidente.  Un `return` da dentro il `async with` saltava la scrittura del
    JSON, e il lanciatore leggeva «nessun esito» — cioe' accusava il banco di
    un difetto mentre la misura era riuscita.  ⇒ Ci si ferma sollevando questa,
    che l'ultimo blocco riconosce e distingue da un guasto vero.
    """

    def __init__(self, codice):
        super().__init__(f"fermato con codice {codice}")
        self.codice = codice


class Copione:
    """⛔ Il copione si DICHIARA, e si scrive quel che e' stato SPEDITO.

    ⚠ «Ho mandato una `z`» e «e' arrivata una `z`» sono due misure diverse
      (`CODER.md` §3.8): questa classe registra solo la prima, e la seconda la
      dice il **testimone dentro la sessione**.  Tenerle separate e' il punto:
      se coincidessero in un solo numero, la sottofase non misurerebbe niente.
    """

    def __init__(self, cli, stream):
        self.cli = cli
        self.stream = stream
        self.id = 0
        self.t0 = time.monotonic()
        self.spediti = []

    def _testa(self):
        self.id += 1
        # ⛔ Microsecondi VERI (§7.3, R1.27): non millisecondi per mille.
        us = int((time.monotonic() - self.t0) * 1_000_000)
        return struct.pack("!IQ", self.id, us), us

    def _manda(self, tipo, corpo_extra, nota):
        testa, us = self._testa()
        corpo = testa + corpo_extra
        dati = struct.pack("!HI", tipo, len(corpo)) + corpo
        self.cli._quic.send_stream_data(self.stream, dati, end_stream=False)
        self.cli.transmit()
        self.spediti.append({"id": self.id, "tipo": tipo, "istante_us": us,
                             "nota": nota,
                             "orologio_ns": time.time_ns()})
        return self.id

    def lettera(self, carattere):
        cp = ord(carattere) if isinstance(carattere, str) else int(carattere)
        return self._manda(RCP_LETTERA, struct.pack("!I", cp),
                           f"LETTERA U+{cp:04X} «{chr(cp)}»")

    def posizione(self, codice, premuto):
        return self._manda(RCP_POSIZIONE, struct.pack("!HB", codice, premuto),
                           f"POSIZIONE_TASTO {codice} "
                           f"{'giu' if premuto else 'su'}")


def leggi_copione(testo):
    """`L:z` una lettera · `P:28:1` una posizione · `A:0.5` un'attesa.

    ⛔ La forma e' esplicita apposta: un copione che dicesse «scrivi ciao»
       nasconderebbe la differenza fra LETTERA e POSIZIONE_TASTO, che e'
       precisamente la distinzione che `SPECIFICHE.md` §7.3 fissa.
    """
    passi = []
    for pezzo in testo.split():
        if pezzo.startswith("L:"):
            passi.append(("L", pezzo[2:]))
        elif pezzo.startswith("U:"):          # una lettera per punto di codice
            passi.append(("L", chr(int(pezzo[2:], 16))))
        elif pezzo.startswith("P:"):
            _, c, g = pezzo.split(":")
            passi.append(("P", (int(c), int(g))))
        elif pezzo.startswith("A:"):
            passi.append(("A", float(pezzo[2:])))
        else:
            raise ValueError(f"passo non riconosciuto nel copione: {pezzo}")
    return passi


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = fc.carica_b3()
    Cliente = fc.fabbrica_cliente()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    os.makedirs(a.lavoro, exist_ok=True)

    esito = {"banco": "06-b34", "etichetta": a.etichetta,
             "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "orologio_ns": time.time_ns(),
             "porta": a.porta, "utente": a.utente, "scena": a.scena,
             "disposizione_dichiarata": a.disposizione,
             "tela": [a.larghezza, a.altezza],
             "copione": a.copione,
             "lascia_premuto": a.lascia_premuto,
             "stacca": a.stacca,
             "manda_disposizione": a.manda_disposizione,
             "sessione": None, "congedo": None, "errore": None,
             "spediti": []}

    dimmi(f"== 06-b34 «{a.etichetta}» — il client che batte un tasto")
    dimmi(f"   bersaglio: https://{autorita}{a.percorso}")
    dimmi(f"   disposizione DICHIARATA in ATTACCA: «{a.disposizione}»")
    dimmi(f"   scena: {a.scena}")
    if a.lascia_premuto:
        dimmi(f"   {GIALLO}⛔ e ci si stacca con il tasto {a.lascia_premuto} "
              f"ANCORA PREMUTO (RCP.md §11){GRIGIO}")

    codice = 0
    try:
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Cliente) as cli:
            await asyncio.wait_for(cli.wait_connected(), timeout=8)
            cli.apri_sessione(autorita, a.percorso)
            stato = await asyncio.wait_for(cli.accettata, timeout=8)
            if stato != "200":
                esito["errore"] = f"CONNECT estesa: :status = {stato}"
                dimmi(f"   {ROSSO}⛔ {esito['errore']}{GRIGIO}")
                raise Fermati(2)
            cli.apri_controllo()
            cli.codec_atteso = a.codec

            try:
                cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
                await b3.attendi(cli, "ECCOMI")
                cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                      b3.s(a.utente) + b3.s(a.parola)))
                await b3.attendi(cli, "AMMESSO", attesa=25)
                cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                      struct.pack("!IIII", a.larghezza,
                                                  a.altezza, a.larghezza,
                                                  a.altezza)
                                      + b3.s(a.disposizione)))
                _, corpo, _ = await b3.attendi(cli, "SESSIONE")
            except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
                # ⛔ E PER I CASI 5 e 3 QUESTO E' L'ESITO ATTESO, non un
                #    incidente: il motivo del congedo E' la misura.
                esito["errore"] = f"{type(e).__name__}: {e}"
                esito["congedo"] = str(e)
                dimmi(f"   {GIALLO}⇒ la stretta di mano si e' fermata: "
                      f"{e}{GRIGIO}")
                raise Fermati(2)

            lar, alt = struct.unpack("!II", corpo[1:9])
            stato_s = corpo[0]
            esito["sessione"] = {"stato": stato_s, "tela": [lar, alt]}
            dimmi(f"   {VERDE}SESSIONE{GRIGIO} stato={stato_s} "
                  f"(1=NUOVA 2=RIPRESA) tela concessa {lar}x{alt}")

            # ⛔ Il canale di input si apre DOPO `SESSIONE` (§2.5), e si tiene
            #    aperto.  Unidirezionale, del client.
            stream = cli._http.create_webtransport_stream(
                cli.sessione, is_unidirectional=True)
            cop = Copione(cli, stream)
            dimmi(f"   canale di input aperto (stream {stream})")

            # ⚠ Un respiro perche' il figlio agganci i dispositivi di `libei`:
            #   senza, i primi tasti finiscono in un `tastiera_dev` che non
            #   c'e' ancora e il banco misurerebbe l'avvio, non il regime
            #   (`CODER.md` §3.5).
            await asyncio.sleep(a.respiro)

            if a.manda_disposizione:
                # ⛔ CASO 3: `DISPOSIZIONE` (0x0009) **durante** la sessione.
                #    L'atteso si dichiara PRIMA, e sta nel lanciatore.
                dimmi(f"   ⇒ mando DISPOSIZIONE(0x0009) «"
                      f"{a.manda_disposizione}» a sessione aperta")
                cli.manda(b3.inquadra(RCP_DISPOSIZIONE,
                                      b3.s(a.manda_disposizione)))
                esito["disposizione_mandata"] = a.manda_disposizione
                await asyncio.sleep(1.5)
                if cli.caduta is not None:
                    esito["congedo"] = f"caduto: {cli.caduta}"
                    dimmi(f"   {GIALLO}⇒ la connessione e' caduta: "
                          f"{cli.caduta}{GRIGIO}")
                else:
                    # ⚠ Se il canale e' ancora vivo, si guarda se e' arrivato
                    #   un messaggio: il silenzio e' una misura anche lui.
                    try:
                        n, c, _ = await asyncio.wait_for(
                            b3.attendi(cli, None, attesa=1.0), timeout=1.5)
                        esito["dopo_disposizione"] = f"{n}: {c.hex()}"
                        dimmi(f"   ⇒ dopo DISPOSIZIONE e' arrivato {n}")
                    except Exception:      # noqa: BLE001
                        esito["dopo_disposizione"] = "nessun messaggio, "\
                            "connessione viva"
                        dimmi("   ⇒ dopo DISPOSIZIONE: nessun messaggio, "
                              "connessione viva")

            # ---- il copione ------------------------------------------------
            for tipo, arg in leggi_copione(a.copione):
                if cli.caduta is not None:
                    esito["congedo"] = f"caduto: {cli.caduta}"
                    dimmi(f"   {ROSSO}⛔ caduto a meta' copione: "
                          f"{cli.caduta}{GRIGIO}")
                    codice = 4
                    break
                if tipo == "L":
                    i = cop.lettera(arg)
                    dimmi(f"      #{i} LETTERA U+{ord(arg):04X} «{arg}»")
                elif tipo == "P":
                    i = cop.posizione(arg[0], arg[1])
                    dimmi(f"      #{i} POSIZIONE_TASTO {arg[0]} "
                          f"{'giu' if arg[1] else 'su'}")
                else:
                    await asyncio.sleep(arg)
                    continue
                await asyncio.sleep(a.passo)

            # ---- ⛔ IL TASTO CHE RESTA GIU' — `RCP.md` §11 -----------------
            if a.lascia_premuto and cli.caduta is None:
                i = cop.posizione(a.lascia_premuto, 1)
                dimmi(f"      #{i} {GIALLO}POSIZIONE_TASTO "
                      f"{a.lascia_premuto} GIU' — e NON lo rilascio{GRIGIO}")
                # ⚠ Il tempo minimo perche' il tasto arrivi davvero al
                #   compositore prima che la connessione cada: se si staccasse
                #   nello stesso millisecondo, «non era premuto» e «e' stato
                #   rilasciato» avrebbero lo stesso aspetto.
                await asyncio.sleep(a.prima_del_distacco)

            esito["spediti"] = cop.spediti

            if a.stacca == "congedo":
                # §8.2 motivo 0x01: l'utente se ne va.  ⛔ Il rilascio deve
                #    avvenire lo stesso (§7.3: «per congedo, per silenzio, per
                #    errore»).
                dimmi("   ⇒ mi stacco con CONGEDO")
                cli.manda(b3.inquadra(b3.T["CONGEDO"],
                                      struct.pack("!B", 0x01) + b3.s("banco 06-b34")))
                await asyncio.sleep(0.5)
            else:
                dimmi("   ⇒ mi stacco chiudendo la connessione")
            if cli.caduta is not None:
                esito["congedo"] = f"caduto: {cli.caduta}"

    except Fermati as f:
        # ⛔ NON e' un errore: e' la misura dei casi 3 e 5.  Si passa oltre e
        #    si scrive il JSON, che e' quel che il lanciatore legge.
        codice = f.codice
    except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
        esito["errore"] = f"{type(e).__name__}: {e}"
        dimmi(f"\n   {ROSSO}⛔ {type(e).__name__}: {e}{GRIGIO}")
        codice = codice or 2

    esito["staccato_ns"] = time.time_ns()
    percorso = os.path.join(a.lavoro, f"{a.etichetta}-cliente.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    dimmi(f"   esito: {percorso}")
    return codice


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="06-b34 — il client che batte un tasto e sa staccarsi "
                    "con un tasto giu'")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7721,
                   help="⛔ la 7721, di questa sottofase")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="provat6")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (D12)")
    p.add_argument("--larghezza", type=int, default=1280)
    p.add_argument("--altezza", type=int, default=800)
    p.add_argument("--disposizione", default="it",
                   help="quel che si DICHIARA in ATTACCA (RCP.md §4.5)")
    p.add_argument("--manda-disposizione", default="",
                   help="⛔ caso 3: manda DISPOSIZIONE(0x0009) a sessione "
                        "aperta, con questo nome")
    p.add_argument("--copione", default="",
                   help="«L:z L:y P:28:1 P:28:0 A:0.5»")
    p.add_argument("--lascia-premuto", type=int, default=0,
                   help="⛔ RCP.md §11: si stacca con QUESTO codice evdev "
                        "ancora premuto (42 = Maiusc sinistro, 29 = Ctrl)")
    p.add_argument("--stacca", choices=["brusco", "congedo"], default="brusco")
    p.add_argument("--codec", type=int, default=1)
    p.add_argument("--respiro", type=float, default=3.0,
                   help="quanto si aspetta dopo SESSIONE prima di battere")
    p.add_argument("--passo", type=float, default=0.35,
                   help="fra un tasto e l'altro")
    p.add_argument("--prima-del-distacco", type=float, default=1.0)
    p.add_argument("--lavoro", default="/tmp/06-t")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)",
                   help="⛔ CODER.md §3.2: la scena si DICHIARA")
    a = p.parse_args()
    a.parola = fc.parola_dagli_argomenti(a)
    if a.scena == "(non dichiarata)":
        dimmi("⛔ serve --scena: una misura senza scena dichiarata misura la "
              "scena, non il prodotto (`CODER.md` §3.2)")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        dimmi(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
