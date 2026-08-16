#!/usr/bin/env python3
"""06-b35-tela.py — ⛔ IL CLIENT CHE CHIEDE LA TELA, e conta quel che torna.

    python3 06-b35-tela.py --porta 7731 --utente provap6 \\
            --parola-file /tmp/parola --lavoro /media/REMOTIX/tmp/06-p \\
            --giro dieci --etichetta g1 --scena "terminale a 50 ms"

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.

===========================================================================
⛔ PERCHE' ESISTE — quel che nessun banco manda
===========================================================================

`FASI.md` §04-si-comanda lo dichiara aperto: *«i banchi RCP/1 non esercitano la
strada nuova: `01-b3-cliente.py` e `01-b4-validatore.py` restano verdi perche'
il filo non e' cambiato, ⛔ ma **nessuno dei due manda un `ADATTA_TELA`**»*.
⭐ E `banchi/04-b31-tela.c` ne manda quanti se ne vuole — ma a un `rcp.c` **nudo**
con un palco **finto**.  ⇒ Qui l'`ADATTA_TELA` esce dal filo vero e arriva a un
compositore vero, e quel che si conta e' quel che il **client** riceve.

===========================================================================
⛔ CHE COSA SI CONTA, E PERCHE' OGNUNA
===========================================================================

  · **un `TELA` per ogni `ADATTA_TELA`** — `RCP.md` §7.1: *«a ogni `ADATTA_TELA`
    il server DEVE rispondere con un `TELA`, riuscito o no»*, e §6.2 aggiunge
    che *«l'n-esimo `TELA` risponde all'n-esima `ADATTA_TELA`»*.  ⛔ Il conto si
    tiene qui perche' e' il conto che un client conforme tiene davvero: da lui
    dipende se trattenere un fotogramma o **chiudere la sessione**;
  · **la misura di ogni fotogramma** — §6.2 vuole che valga la tela in vigore, e
    un fotogramma di misura diversa e' `ERRORE_PROTOCOLLO` per un client vero.
    ⇒ Qui non si chiude: si **conta e si dichiara**, perche' un banco che
    chiude smette di misurare proprio dove comincia l'interessante;
  · ⭐ **il primo fotogramma dopo ogni `TELA(ADATTATA)` dev'essere una CHIAVE**
    (§5.2), o il decodificatore continua a emettere alla misura VECCHIA;
  · **quanto ci mette**, dall'`ADATTA_TELA` spedito al `TELA` ricevuto, e dal
    `TELA` al primo fotogramma della misura nuova.

⛔ E NON si giudicano i pixel: quello e' un altro programma, e un cronometro che
   giudicasse anche il contenuto potrebbe assolversi da solo (`04-b31-cliente`).

===========================================================================
⛔⛔ IL LIMITE DI QUESTO BANCO, SCRITTO IN TESTA
===========================================================================

**Qui non c'e' nessun browser, e i ridimensionamenti si provocano DAL FILO.**

⛔ E non e' una comodita': `LEZIONI.md` §1.15, `[M]` 13 agosto 2026 — **su Xvfb
   `requestAnimationFrame` non gira MAI** (0 quadri in 3 s, con GPU e senza,
   `visibilityState` a «visible»), e in **Blink** l'evento `resize` si consegna
   **dentro il giro di rendering** ⇒ senza quadri **non arriva mai**.  ⇒ Una
   pagina pilotata sotto `xvfb-run` **non chiederebbe mai** la ritela che segue
   la finestra, e un banco costruito cosi' sarebbe **verde per costruzione**:
   misurerebbe un prodotto a cui nessuno ha chiesto niente.

⇒ Quel che questo banco prova e' la catena **dal messaggio `ADATTA_TELA` in
  giu'**: `rcp.c` → `main.c` → `figli_ritela()` → `cattura_ridimensiona()` →
  compositore → fotogramma → `MSG_TELA` → `TELA`.
⛔ Quel che NON prova, dichiarato: che la **pagina** mandi l'`ADATTA_TELA`
  giusto al momento giusto — quello e' della sottofase 6.5, con un browser vero
  su uno schermo vero.

===========================================================================
⛔⛔ E SI GIUDICA PRIMA IL PALCO — se non consegna, il banco NON misura
===========================================================================

Una spia conta quel che e' ARRIVATO.  ⛔ Se dal palco non arriva un fotogramma,
tutto quel che segue e' un'assenza che non dimostra niente (`CODER.md` §3.10):
un `TELA` che non arriva perche' il compositore non consegna e un `TELA` che non
arriva perche' il prodotto ha un difetto **hanno la stessa faccia**.  ⇒ Il banco
lo dice — *«IL PALCO, NON IL PRODOTTO»* — e **si ferma** con uscita 5.

===========================================================================
⛔ I CODICI D'USCITA
===========================================================================

    0  il giro e' finito (⚠ «finito» non e' «verde»: il verdetto e' nel JSON)
    2  la stretta di mano NON e' arrivata a SESSIONE — non si e' misurato niente
    4  la connessione e' caduta prima della fine del giro
    5  ⛔ IL PALCO, NON IL PRODOTTO: il compositore non ha consegnato un
       fotogramma, quindi non si e' misurato il prodotto e il banco si e' fermato
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
INTESTAZIONE = 28              # §6.2, «28 byte esatti, senza riempimento»
CHIAVE, DELTA = 0x0301, 0x0302

# ⛔ I due tipi che `01-b3-cliente.py` NON ha: la sua tabella si ferma a
#    `CONGEDO`, ed e' esattamente il buco che questo banco esiste per riempire.
#    ⚠ I numeri vengono da `RCP.md` §7.1, non da `rcp.c`: un banco che leggesse
#      i valori dal prodotto non potrebbe mai accusarlo di sbagliarli.
T_ADATTA_TELA = 0x000B
T_TELA = 0x000E
T_CONGEDO = 0x000C

# `TELA` (§7.1): u8 esito, u8 motivo, u32 larghezza, u32 altezza
ESITO = {1: "ADATTATA", 2: "RIFIUTATA"}
MOTIVO = {0: "-", 1: "COMPOSITORE_INCAPACE", 2: "MISURA_FUORI_LIMITI",
          3: "NON_ORA"}

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ SI EREDITA, NON SI RISCRIVE: la stretta di mano e lo smistamento degli
#    stream unidirezionali hanno gia' pagato due difetti dal vivo.
fc = _porta("fc", "02-filo-cliente.py")


def dimmi(*a):
    print(*a, flush=True)


# ===========================================================================
#  I GIRI — ogni giro dichiara il suo ATTESO **prima**, e sta qui accanto alla
#  sequenza che lo produce: un atteso scritto dopo la misura non e' un atteso.
# ===========================================================================
#
# ⚠ Le misure sono tutte PARI e dentro 320x240..7680x4320 (§4.5) tranne dove il
#   giro dichiara di volerne una fuori: e' il caso `limiti`.
GIRI = {
    "dieci": {
        "che_cosa": "dieci ridimensionamenti di fila, misure diverse, "
                    "avanti e indietro",
        "atteso": [
            "10 ADATTA_TELA ⇒ 10 TELA, uno per ciascuna (§7.1)",
            "10 TELA(ADATTATA), 0 RIFIUTATA",
            "la tela in vigore dichiarata da ogni TELA e' quella concessa",
            "0 fotogrammi di misura diversa dalla tela in vigore (§6.2)",
            "il primo fotogramma dopo ogni TELA(ADATTATA) e' una CHIAVE (§5.2)",
            "la sessione non cade",
        ],
        "misure": [(1280, 800), (1024, 640), (1600, 900), (800, 600),
                   (1920, 1080), (1024, 640), (1280, 800), (960, 540),
                   (1440, 900), (1280, 800)],
    },
    "limiti": {
        "che_cosa": "i limiti di RCP.md §4.5 contro il palco VERO",
        "atteso": [
            "320x240 (il minimo) ⇒ ADATTATA 320x240",
            "318x240 (sotto il minimo) ⇒ RIFIUTATA MISURA_FUORI_LIMITI, "
            "e la tela NON cambia",
            "1281x801 (lati dispari) ⇒ ADATTATA 1280x800 (troncati in giu')",
            "7682x4320 (sopra il massimo) ⇒ RIFIUTATA MISURA_FUORI_LIMITI",
            "3840x2160 ⇒ ADATTATA (e' il video.misura_massima dichiarato in CIAO)",
            "3842x2160 (oltre il video.misura_massima) ⇒ ridotta in proporzione, "
            "lati pari — e la riga del RIPIEGO DICHIARATO sta nel registro",
            "in nessun caso la sessione cade (§3, eccezione 4)",
        ],
        "misure": [(320, 240), (318, 240), (1281, 801), (7682, 4320),
                   (3840, 2160), (3842, 2160), (1280, 800)],
    },
    "incatenate": {
        "che_cosa": "⛔ DUE `ADATTA_TELA` a distanza di --intervallo ms — «chi "
                    "trascina un bordo ne manda proprio due di fila»",
        "atteso": [
            "2 ADATTA_TELA ⇒ 2 TELA (§7.1: uno per ciascuna)",
            "il PRIMO TELA e' RIFIUTATA/NON_ORA (rcp.c risponde alla prima "
            "prima di girare la seconda)",
            "⭐ il SECONDO TELA e' ADATTATA con la misura della SECONDA "
            "richiesta — ⛔ e' questa la riga che si sta cercando di smentire",
            "la tela in vigore alla fine del giro e' quella della SECONDA",
            "0 fotogrammi di misura diversa dalla tela in vigore",
        ],
        "misure": [(1600, 900), (1024, 640)],
    },
    "singola": {
        "che_cosa": "UNA richiesta sola, la misura di --misura — serve al "
                    "SECONDO client delle scene «il palco cambia da se'»",
        "atteso": [
            "1 ADATTA_TELA ⇒ 1 TELA(ADATTATA) alla misura chiesta",
            "⛔ e il palco si muove SOTTO l'altra sessione, che non ha chiesto "
            "niente: e' quella che si sta misurando, non questa",
        ],
        "misure": [],   # ⚠ la mette `--misura`: vedi in fondo
    },
    "guarda": {
        "che_cosa": "si attacca e GUARDA: nessun ADATTA_TELA dopo l'attacco — "
                    "serve alle scene in cui il palco cambia DA SE'",
        "atteso": [
            "0 ADATTA_TELA dopo l'attacco ⇒ 0 TELA (§7.1: un TELA non "
            "sollecitato farebbe chiudere una sessione sana, §6.2)",
            "la sessione non cade",
        ],
        "misure": [],
    },
}


def fabbrica():
    class Tela(fc.fabbrica_cliente()):

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.t_zero = None
            self.raccolta = {}
            self.completi = []      # i fotogrammi COMPLETI, in ordine
            self.azzerati = 0
            # ⭐ i messaggi di controllo che arrivano DOPO `SESSIONE`, timbrati
            self.controllo_dopo = []

        def _ora(self):
            if self.t_zero is None:
                return None
            return round(time.monotonic() - self.t_zero, 6)

        def _arrivano(self, sid, dati, fine):
            r = self.raccolta.get(sid)
            if r is None:
                r = self.raccolta[sid] = {"t_primo": self._ora(),
                                          "dati": bytearray()}
            r["dati"] += dati
            super()._arrivano(sid, dati, fine)
            if fine:
                self._completo(sid, r)

        def _azzerato(self, sid):
            r = self.raccolta.get(sid)
            super()._azzerato(sid)
            self.azzerati += 1
            if r is not None:
                self.raccolta.pop(sid, None)

        def _completo(self, sid, r):
            d = bytes(r["dati"])
            self.raccolta.pop(sid, None)
            if len(d) <= INTESTAZIONE:
                return
            tipo, codec, lar, alt, num, ist, inp = struct.unpack(
                "!HHIIIQI", d[:INTESTAZIONE])
            self.completi.append({
                "n": len(self.completi) + 1,
                # ⛔ Il timbro e' l'istante del FIN: un fotogramma a meta' non e'
                #    un pixel, e' un fotogramma che sta arrivando.
                "t": self._ora(),
                "tipo": "chiave" if tipo == CHIAVE else (
                    "delta" if tipo == DELTA else f"0x{tipo:04x}"),
                "larghezza": lar, "altezza": alt,
                "numero": num, "byte": len(d) - INTESTAZIONE,
            })

    return Tela


async def orecchio(cli, fine_evento):
    """⭐ Drena il canale di controllo e TIMBRA ogni messaggio.

    ⛔ E si accende PRIMA di mandare il primo `ADATTA_TELA`: un `TELA` che
       arrivasse mentre nessuno legge resterebbe nella coda e il suo istante
       sarebbe quello in cui qualcuno si e' degnato di guardarla — cioe' una
       misura di quando ho chiamato `get()`, non di quando il server ha
       risposto.  ⚠ E' la stessa forma per cui il timbro del fotogramma si
       prende al FIN e non alla lettura.
    """
    while not fine_evento.is_set():
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=0.05)
        except asyncio.TimeoutError:
            continue
        if m is None:
            cli.controllo_dopo.append({"t": cli._ora(), "tipo": "canale-chiuso"})
            return
        tipo, corpo, _ = m
        voce = {"t": cli._ora(), "tipo_num": tipo}
        if tipo == T_TELA and len(corpo) >= 10:
            esito, motivo = corpo[0], corpo[1]
            lar, alt = struct.unpack("!II", corpo[2:10])
            voce.update({"tipo": "TELA", "esito": ESITO.get(esito, esito),
                         "motivo": MOTIVO.get(motivo, motivo),
                         "tela_l": lar, "tela_a": alt})
        elif tipo == T_CONGEDO:
            voce.update({"tipo": "CONGEDO",
                         "motivo_num": corpo[0] if corpo else None})
        else:
            voce["tipo"] = f"0x{tipo:04x}"
        cli.controllo_dopo.append(voce)


def chiedi_tela(cli, lar, alt):
    """⛔ La parte del client che nessun banco RCP/1 aveva: `ADATTA_TELA`."""
    cli.manda(struct.pack("!HIII", T_ADATTA_TELA, 8, lar, alt))
    return {"t": cli._ora(), "chiesta_l": lar, "chiesta_a": alt}


async def aspetta_tela(cli, quanti_prima, attesa):
    """Aspetta che arrivi un `TELA` in piu' di `quanti_prima`.

    ⛔ Si conta sui TELA, non si dorme un tempo fisso: un banco che dormisse
       misurerebbe il proprio `sleep`.  ⚠ E `None` = **non e' arrivato**, che
       NON e' «e' arrivato vuoto» (`CODER.md` §3.10): il chiamante lo scrive
       come assenza, e l'assenza di un `TELA` e' la violazione di §7.1 che
       questo banco cerca per prima.
    """
    fine = time.monotonic() + attesa
    while time.monotonic() < fine:
        tele = [v for v in cli.controllo_dopo if v["tipo"] == "TELA"]
        if len(tele) > quanti_prima:
            return tele[quanti_prima]
        if cli.caduta is not None:
            return None
        await asyncio.sleep(0.002)
    return None


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = fc.carica_b3()
    Cliente = fabbrica()
    giro = GIRI[a.giro]

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    os.makedirs(a.lavoro, exist_ok=True)

    dimmi(f"== 06-b35 — «{a.giro}»: {giro['che_cosa']}")
    dimmi(f"   bersaglio: https://{autorita}{a.percorso}  utente {a.utente}")
    dimmi(f"   scena: {a.scena}")
    dimmi(f"   ⛔ L'ATTESO, dichiarato PRIMA:")
    for r in giro["atteso"]:
        dimmi(f"      · {r}")
    dimmi("")

    caduta = None
    tentativi = []
    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            dimmi(f"   ⛔ CONNECT estesa: :status = {stato}")
            return 2
        cli.apri_controllo()
        cli.codec_atteso = a.codec
        try:
            cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
            await b3.attendi(cli, "ECCOMI")
            cli.t_zero = time.monotonic()
            cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                  b3.s(a.utente) + b3.s(a.parola)))
            await b3.attendi(cli, "AMMESSO", attesa=25)
            t_ammesso = round(time.monotonic() - cli.t_zero, 6)
            cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                  struct.pack("!IIII", a.larghezza, a.altezza,
                                              a.larghezza, a.altezza)
                                  + b3.s(a.disposizione)))
            _, corpo, _ = await b3.attendi(cli, "SESSIONE")
            t_sessione = round(time.monotonic() - cli.t_zero, 6)
        except Exception as e:      # noqa: BLE001 — il tipo dell'errore E' la misura
            dimmi(f"   ⛔ la stretta di mano non e' arrivata a SESSIONE: "
                  f"{type(e).__name__}: {e}")
            dimmi("      ⚠ Questo NON e' «la tela non funziona»: non si e' "
                  "misurato niente")
            return 2

        lar, alt = struct.unpack("!II", corpo[1:9])
        dimmi(f"   ⭐ AMMESSO a t={t_ammesso:.3f} s · SESSIONE a "
              f"t={t_sessione:.3f} s · tela concessa {lar}x{alt}")
        if cli.contesto is None:
            cli.contesto = fc.f24.Contesto(tela=(lar, alt),
                                           codec_negoziato=a.codec,
                                           sessione_aperta=True)

        # ⭐ L'orecchio si accende PRIMA del primo `ADATTA_TELA`.
        fine_evento = asyncio.Event()
        ascolto = asyncio.create_task(orecchio(cli, fine_evento))

        # ⛔ Si aspetta il PRIMO fotogramma prima di cominciare a chiedere: un
        #    ridimensionamento chiesto a palco non ancora montato misura il
        #    montaggio, non il ridimensionamento — ed e' un'altra scena
        #    (`RCP.md` §7.1, il ramo «ATTENDI»).  ⚠ Se non arriva si va avanti
        #    LO STESSO e lo si dichiara: e' un fatto, non un motivo per fermarsi.
        t0 = time.monotonic()
        while time.monotonic() - t0 < a.attesa_primo and not cli.completi:
            await asyncio.sleep(0.01)
        t_primo = cli.completi[0]["t"] if cli.completi else None
        if t_primo is None:
            # ⛔⭐ SI GIUDICA PRIMA IL PALCO, e ci si FERMA.  ⚠ Andare avanti
            #     produrrebbe una tabella di `TELA` mancanti che accusa il
            #     prodotto di una colpa del compositore — la forma peggiore,
            #     perche' e' un rosso all'imputato sbagliato.
            dimmi(f"   {ROSSO}⛔⛔ IL PALCO, NON IL PRODOTTO: nessun fotogramma "
                  f"entro {a.attesa_primo} s.{GRIGIO}")
            dimmi("      ⚠ Il compositore non consegna, quindi non si misura "
                  "niente: un `TELA` che manca perche' il palco tace e uno che "
                  "manca per un difetto hanno la STESSA faccia (`CODER.md` "
                  "§3.10).  Il banco si ferma.")
            # ⛔⭐ MA LA MISURA SI SCRIVE LO STESSO — difetto del banco trovato
            #     misurando il guasto G5, 16 agosto 2026: uscendo di qui con un
            #     `return` secco non si scriveva nessun JSON, e il
            #     certificatore trovava «SENZA-JSON».  ⚠ «Non ho misurato il
            #     PRODOTTO» non vuol dire «non ho misurato niente»: zero
            #     fotogrammi, i `TELA` arrivati e l'ora sono fatti, e sono
            #     esattamente i fatti che servono a capire perche'.
            #     ⛔ Buttarli e' la forma peggiore di §3.10: si perde anche
            #     l'informazione che dice **quale** dei due casi era.
            palco_muto = True
        else:
            palco_muto = False
            dimmi(f"   ⭐ primo fotogramma a t={t_primo:.3f} s "
                  f"({cli.completi[0]['larghezza']}x{cli.completi[0]['altezza']}, "
                  f"{cli.completi[0]['tipo']})")
            dimmi(f"   ⭐ dal SESSIONE al primo fotogramma: "
                  f"{(t_primo - t_sessione) * 1000:.0f} ms")
        dimmi("")

        # ⚠ Il ritardo iniziale serve alle scene a DUE client: il secondo deve
        #   entrare quando il primo e' gia' assestato, o si misurerebbero due
        #   attacchi sovrapposti invece di un palco che cambia sotto una
        #   sessione ferma.
        if a.ritarda > 0 and not palco_muto:
            dimmi(f"   ⏳ aspetto {a.ritarda} s prima di chiedere (scena a due "
                  f"client)")
            await asyncio.sleep(a.ritarda)

        # ---- il giro -------------------------------------------------------
        # ⛔ Col palco muto NON si prova a chiedere niente: si va dritti alla
        #    scrittura della misura, e l'uscita sara' 5.
        if palco_muto:
            pass
        elif a.giro == "incatenate":
            # ⛔⭐ LA TELA DI PARTENZA SI FISSA, o la scena non e' la stessa due
            #     volte.  ⚠ Il palco sopravvive al client (I4) e `SESSIONE`
            #     concede la misura che il palco HA (§4.5): senza questa
            #     richiesta preliminare, ogni giro parte dalla misura in cui
            #     l'ha lasciato il giro precedente — e due giri con la stessa
            #     etichetta misurerebbero due scene diverse.
            if a.base:
                bl, ba = (int(x) for x in a.base.split("x"))
                prima = len([v for v in cli.controllo_dopo if v["tipo"] == "TELA"])
                t = chiedi_tela(cli, bl, ba)
                r = await aspetta_tela(cli, prima, a.attesa_tela)
                t["risposta"] = r
                t["base"] = True
                tentativi.append(t)
                if r is None:
                    dimmi(f"   {ROSSO}⛔ la tela di PARTENZA {bl}x{ba} non e' "
                          f"stata concessa: quel che segue non e' la scena che "
                          f"dico{GRIGIO}")
                else:
                    dimmi(f"   partenza: {bl}x{ba} → TELA({r['esito']}) "
                          f"{r['tela_l']}x{r['tela_a']}")
                # ⚠ E si aspetta che il palco si sia assestato: una richiesta
                #   girata mentre il palco e' ancora in movimento sarebbe una
                #   TERZA richiesta incatenata, e la scena ne dichiara due.
                await asyncio.sleep(a.pausa)
            # ⛔ LE DUE RICHIESTE NON SI ASPETTANO A VICENDA: e' proprio il non
            #    aspettare che fa la scena.  ⚠ L'intervallo si dichiara, perche'
            #    la finestra che conta e' quella della rinegoziazione del
            #    compositore — `[M]` 41,6 ms su Mutter.
            for (l, al) in giro["misure"][:1]:
                tentativi.append(chiedi_tela(cli, l, al))
            await asyncio.sleep(a.intervallo / 1000.0)
            for (l, al) in giro["misure"][1:]:
                tentativi.append(chiedi_tela(cli, l, al))
            dimmi(f"   ⛔ due ADATTA_TELA a {a.intervallo} ms di distanza: "
                  f"{giro['misure'][0]} poi {giro['misure'][1]}")
            # e adesso si sta a guardare, per il tempo dichiarato
            fine = time.monotonic() + a.coda
            while time.monotonic() < fine and cli.caduta is None:
                await asyncio.sleep(0.01)
        elif a.giro == "guarda":
            fine = time.monotonic() + a.coda
            t_giro = time.monotonic()
            ultimo_ping = time.monotonic()
            while time.monotonic() < fine and cli.caduta is None:
                # ⚠ §5.3: trenta secondi di silenzio e la sessione si stacca —
                #   e si misurerebbe lo stacco invece della scena.  ⛔ Il passo
                #   non scende sotto 0,3 s: §5.2 vieta due RICHIEDI_CHIAVE a
                #   meno di 200 ms.
                # ⛔⭐ E OGNI `RICHIEDI_CHIAVE` RIPRENDE IL POSTO (§8.2 `0x0F`):
                #     `torna_a_parlare()` gira in cima a `rcp_ricevi()`.  ⚠ Non
                #     e' un dettaglio del banco — e' la leva che decide se
                #     questa sessione COMANDA il palco o lo GUARDA (I2), ed e'
                #     quel che fa la differenza fra le due scene.
                # ⚠ E `--ping-da` esiste per una scena sola, che senza non si
                #   puo' fare: §5.3 stacca per silenzio a 30 s e la sessione
                #   **lascia il posto restando viva**.  ⛔ Finche' il posto ce
                #   l'ha, un secondo client dello stesso utente viene congedato
                #   con `GIA_ATTIVA_REMOTA` (§8.2 `0x0F`) e la scena «due
                #   sessioni si contendono il palco» non si presenta affatto.
                if (time.monotonic() - t_giro < a.ping_da):
                    await asyncio.sleep(0.01)
                    continue
                if a.ping_ogni > 0 and time.monotonic() - ultimo_ping > a.ping_ogni:
                    cli.chiedi_chiave(len(cli.completi))
                    ultimo_ping = time.monotonic()
                await asyncio.sleep(0.01)
        else:
            for i, (l, al) in enumerate(giro["misure"]):
                prima = len([v for v in cli.controllo_dopo if v["tipo"] == "TELA"])
                n_prima = len(cli.completi)
                t = chiedi_tela(cli, l, al)
                r = await aspetta_tela(cli, prima, a.attesa_tela)
                t["risposta"] = r
                if r is None:
                    t["ms"] = None
                    dimmi(f"   {ROSSO}⛔ {i+1:2d}. ADATTA_TELA {l}x{al} → "
                          f"NESSUN TELA in {a.attesa_tela} s (§7.1 lo vieta)"
                          f"{GRIGIO}")
                else:
                    t["ms"] = round((r["t"] - t["t"]) * 1000, 1)
                    col = VERDE if r["esito"] == "ADATTATA" else GIALLO
                    dimmi(f"   {col}   {i+1:2d}. ADATTA_TELA {l}x{al} → "
                          f"TELA({r['esito']}, {r['motivo']}) "
                          f"{r['tela_l']}x{r['tela_a']} in {t['ms']:.0f} ms"
                          f"{GRIGIO}")
                # ⭐⭐ IL PRIMO FOTOGRAMMA ALLA MISURA NUOVA — e §5.2 parla di
                #     QUELLO, non del primo che capita dopo aver chiesto.
                #
                # ⛔⛔ DIFETTO DEL BANCO, trovato misurando il 16 agosto 2026 e
                #     scritto qui perche' e' la forma di `CODER.md` §2.3 — «una
                #     prova che boccia il codice giusto costa quanto una che
                #     promuove quello sbagliato».  La prima stesura prendeva
                #     `cli.completi[n_prima]`, cioe' il primo fotogramma
                #     arrivato dopo che l'`ADATTA_TELA` era **partito**: fra la
                #     partenza e il `TELA` passano decine di millisecondi, e in
                #     mezzo arrivano fotogrammi della misura VECCHIA — che sono
                #     giusti e attesi.  ⇒ Il banco contava 4 chiavi su 10 e
                #     accusava il prodotto di violare §5.2, mentre il conto
                #     giusto e' **9 su 9** (il decimo non e' un cambio: la
                #     misura era gia' quella).
                #
                # ⇒ Due domande, e sono due: *«che cosa e' arrivato dopo la
                #   risposta?»* e *«qual e' il primo alla misura che la risposta
                #   dichiara in vigore?»*.  La seconda e' quella di §5.2.
                t0 = time.monotonic()
                atteso = ((r["tela_l"], r["tela_a"]) if r else None)
                while time.monotonic() - t0 < a.attesa_fotogramma:
                    if r is not None and any(
                            f["t"] > r["t"]
                            and (f["larghezza"], f["altezza"]) == atteso
                            for f in cli.completi[n_prima:]):
                        break
                    await asyncio.sleep(0.005)
                if r is not None:
                    dopo = [f for f in cli.completi if f["t"] > r["t"]]
                    nuovi = [f for f in dopo
                             if (f["larghezza"], f["altezza"]) == atteso]
                    # ⛔ «Non e' arrivato» si scrive, e non e' «ne e' arrivato uno
                    #    a zero» (`CODER.md` §3.10).
                    t["primo_dopo"] = ({k: dopo[0][k] for k in
                                        ("n", "t", "tipo", "larghezza", "altezza")}
                                       if dopo else None)
                    t["primo_misura_nuova"] = ({k: nuovi[0][k] for k in
                                                ("n", "t", "tipo", "larghezza",
                                                 "altezza")} if nuovi else None)
                    if nuovi:
                        # ⭐ I due tempi, e sono due cose diverse: quanto ci
                        #    mette il SERVER a rispondere, e quanto ci mette il
                        #    PALCO a consegnare pixel della misura nuova.
                        t["ms_al_fotogramma"] = round(
                            (nuovi[0]["t"] - t["t"]) * 1000, 1)
                        t["ms_tela_fotogramma"] = round(
                            (nuovi[0]["t"] - r["t"]) * 1000, 1)
                else:
                    t["primo_dopo"] = t["primo_misura_nuova"] = None
                tentativi.append(t)
                await asyncio.sleep(a.pausa)
            # la coda: si guarda ancora un po', per vedere se il palco «torna»
            fine = time.monotonic() + a.coda
            while time.monotonic() < fine and cli.caduta is None:
                await asyncio.sleep(0.01)

        fine_evento.set()
        await ascolto
        caduta = cli.caduta

    # ---- quel che si consegna -------------------------------------------
    tele = [v for v in cli.controllo_dopo if v["tipo"] == "TELA"]
    # ⭐ La tela IN VIGORE, ricostruita come la ricostruirebbe un client vero:
    #    quella di `SESSIONE`, poi quella dichiarata da ogni `TELA`.
    #    ⛔ Anche da un `TELA(RIFIUTATA)`: §7.1 dice che i due campi sono «la
    #       tela in vigore DOPO questo messaggio», e su un rifiuto valgono
    #       quella di prima.  Chi li buttasse riscriverebbe il difetto minore
    #       «i due campi di TELA(RIFIUTATA) buttati» dei dieci del 15 agosto.
    vigore = (lar, alt)
    fuori_misura = []
    idx_tela = 0
    for f in cli.completi:
        while (idx_tela < len(tele)
               and tele[idx_tela]["t"] is not None
               and f["t"] is not None
               and tele[idx_tela]["t"] <= f["t"]):
            vigore = (tele[idx_tela]["tela_l"], tele[idx_tela]["tela_a"])
            idx_tela += 1
        f["vigore_l"], f["vigore_a"] = vigore
        if (f["larghezza"], f["altezza"]) != vigore:
            fuori_misura.append(f["n"])

    misura = {
        "banco": "06-b35", "giro": a.giro, "etichetta": a.etichetta,
        "che_cosa": giro["che_cosa"], "atteso": giro["atteso"],
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "porta": a.porta, "utente": a.utente, "scena": a.scena,
        "intervallo_ms": a.intervallo,
        "tela_chiesta_attacco": [a.larghezza, a.altezza],
        "tela_concessa_attacco": [lar, alt],
        "t_ammesso": t_ammesso, "t_sessione": t_sessione,
        "t_primo_fotogramma": t_primo,
        "ms_sessione_primo_fotogramma": (
            round((t_primo - t_sessione) * 1000, 1) if t_primo else None),
        "adatta_tela_spediti": len(tentativi),
        "tela_ricevuti": len(tele),
        "tentativi": tentativi,
        "controllo_dopo_sessione": cli.controllo_dopo,
        "fotogrammi": cli.completi,
        "fotogrammi_totali": len(cli.completi),
        "fotogrammi_fuori_misura": fuori_misura,
        "azzerati": cli.azzerati,
        "caduta": caduta,
    }

    # ⭐⭐ IL VERDETTO, contato qui e non a occhio nella tabella — e ogni conto
    #     porta accanto la regola che lo pretende.
    cambi = 0
    chiavi_ok = 0
    senza_risposta = 0
    prec = (lar, alt)
    for t in tentativi:
        r = t.get("risposta")
        if r is None:
            senza_risposta += 1
            continue
        adesso = (r["tela_l"], r["tela_a"])
        # ⛔ §5.2 vale sul CAMBIO: chiedere la misura che c'e' gia' non apre
        #    nessun debito di chiave, e pretenderla sarebbe il rosso
        #    all'imputato sbagliato (`rcp.c` lo dichiara: «§5.2 NON apre il
        #    debito della chiave»).
        if adesso != prec:
            cambi += 1
            p_n = t.get("primo_misura_nuova")
            if p_n and p_n["tipo"] == "chiave":
                chiavi_ok += 1
        prec = adesso
    verdetto = {
        "adatta_tela_spediti": len(tentativi),
        "tela_ricevuti": len(tele),
        "senza_risposta": senza_risposta,
        "cambi_di_misura": cambi,
        "primo_alla_misura_nuova_e_chiave": chiavi_ok,
        "fotogrammi_fuori_misura": len(fuori_misura),
        "caduta": caduta,
        "palco_muto": palco_muto,
    }
    misura["verdetto"] = verdetto

    dimmi("")
    dimmi(f"   §7.1 — un TELA per ogni ADATTA_TELA: "
          f"{len(tele)}/{len(tentativi)}"
          + (f"  {ROSSO}⛔ {senza_risposta} senza risposta{GRIGIO}"
             if senza_risposta else f"  {VERDE}✓{GRIGIO}"))
    dimmi(f"   §5.2 — il primo alla misura NUOVA e' una chiave: "
          f"{chiavi_ok}/{cambi} cambi"
          + (f"  {VERDE}✓{GRIGIO}" if chiavi_ok == cambi
             else f"  {ROSSO}⛔{GRIGIO}"))
    dimmi(f"   ADATTA_TELA spediti: {len(tentativi)} · TELA ricevuti: {len(tele)}")
    dimmi(f"   fotogrammi completi: {len(cli.completi)} "
          f"({sum(1 for x in cli.completi if x['tipo'] == 'chiave')} chiavi, "
          f"{cli.azzerati} azzerati)")
    if fuori_misura:
        dimmi(f"   {ROSSO}⛔ fotogrammi di misura DIVERSA dalla tela in vigore: "
              f"{len(fuori_misura)}{GRIGIO}")
    else:
        dimmi(f"   {VERDE}0 fotogrammi di misura diversa dalla tela in vigore"
              f"{GRIGIO}")
    percorso = os.path.join(a.lavoro, f"06-b35-{a.etichetta}.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(misura, f, ensure_ascii=False, indent=1)
    dimmi(f"   misura: {percorso}")
    if palco_muto:
        return 5
    if caduta:
        dimmi(f"   {ROSSO}⛔ {caduta}{GRIGIO}")
        return 4
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="06-b35 — la tela sul palco vero")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, help="⛔ la 7731, di questa sottofase")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="provap6")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (D12)")
    p.add_argument("--larghezza", type=int, default=1280)
    p.add_argument("--altezza", type=int, default=800)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--giro", default="dieci", choices=sorted(GIRI))
    p.add_argument("--intervallo", type=float, default=25.0,
                   help="ms fra le due ADATTA_TELA del giro «incatenate»")
    p.add_argument("--base", default="1280x800",
                   help="⭐ la tela di PARTENZA del giro «incatenate», fissata "
                        "con una richiesta preliminare ASPETTATA: senza, ogni "
                        "giro parte dove l'ha lasciato il precedente (I4)")
    p.add_argument("--attesa-primo", type=float, default=8.0)
    p.add_argument("--attesa-tela", type=float, default=5.0,
                   help="⚠ piu' del fondo di §7.1 (3000 ms), o si misurerebbe "
                        "questo tetto invece di quello del prodotto")
    p.add_argument("--attesa-fotogramma", type=float, default=2.0)
    p.add_argument("--pausa", type=float, default=0.4,
                   help="fra un ridimensionamento e il successivo")
    p.add_argument("--coda", type=float, default=4.0,
                   help="quanto si sta a guardare dopo l'ultima richiesta")
    p.add_argument("--lavoro", default="/media/REMOTIX/tmp/06-p")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)",
                   help="⛔ CODER.md §3.2: la scena si DICHIARA")
    p.add_argument("--ping-ogni", type=float, default=5.0,
                   help="⭐ RICHIEDI_CHIAVE ogni N s nel giro «guarda» — e ogni "
                        "messaggio RIPRENDE IL POSTO (I2).  0 = mai, e allora "
                        "questa sessione GUARDA senza comandare")
    p.add_argument("--ping-da", type=float, default=0.0,
                   help="secondi di SILENZIO prima di cominciare a pingare: "
                        "oltre i 30 di §5.3 la sessione lascia il posto "
                        "restando viva, ed e' l'unico modo di far entrare un "
                        "secondo client dello stesso utente")
    p.add_argument("--misura", default="1600x900",
                   help="la misura del giro «singola»")
    p.add_argument("--ritarda", type=float, default=0.0,
                   help="secondi da aspettare dopo il primo fotogramma prima "
                        "di cominciare a chiedere (scene a due client)")
    a = p.parse_args()
    if a.giro == "singola":
        GIRI["singola"]["misure"] = [tuple(int(x) for x in a.misura.split("x"))]
    a.parola = fc.parola_dagli_argomenti(a)
    if not a.porta:
        dimmi("⛔ serve --porta.  Per 06-b35 e' la 7731.")
        sys.exit(2)
    if a.scena == "(non dichiarata)":
        dimmi("⛔ serve --scena: una misura senza scena dichiarata misura la "
              "scena, non il prodotto (`CODER.md` §3.2)")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        dimmi(f"\n   ⛔ {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
