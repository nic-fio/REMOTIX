#!/usr/bin/env python3
"""04-b31-cliente.py — ⛔ IL CRONOMETRO DELL'APPARIZIONE: dal LOGIN al primo
pixel, **dal lato che riceve**.

    python3 04-b31-cliente.py --porta 7711 --utente provao1 \\
            --parola-file /tmp/parola --lavoro /tmp/04-b31 --etichetta prima \\
            --attesa 25

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.

===========================================================================
⛔ CHE COSA MISURA, E DA DOVE PARTE IL CRONOMETRO
===========================================================================

Il mandato dell'utente e' *«il tempo fra il login e la comparsa del desktop»*.
⇒ Lo zero del cronometro e' **l'istante in cui i byte di `CREDENZIALI` escono
dal socket**, letto qui, dal client, con `time.monotonic()`.

⛔ E NON e' «quando il server dice AMMESSO»: fra i due c'e' il secondo fisso di
   `RCP.md` §4.4-bis, che e' **nostro** e che l'utente aspetta.  Metterlo fuori
   dalla misura vorrebbe dire spostare il confine nella direzione comoda —
   `CODER.md` §1-bis dice l'opposto.

⛔⛔ E OGNI FOTOGRAMMA E' TIMBRATO QUANDO E' **COMPLETO**, non al primo byte.
     Un fotogramma a meta' non e' un pixel: e' un fotogramma che sta arrivando.
     ⇒ Il timbro e' l'istante del FIN del suo stream (§6.2), che e' anche il
     primo istante in cui un client vero potrebbe darlo al decodificatore.

===========================================================================
⛔ QUESTO PROGRAMMA NON GIUDICA I PIXEL — E NON DEVE
===========================================================================

Qui si raccolgono **due cose e basta**: i byte, in ordine di arrivo, e l'istante
di ciascuno.  Il verdetto *«in questo fotogramma c'e' il desktop o uno schermo
vuoto?»* lo da' `04-b31-apparizione.py`, che riusa il giudice **gia' calibrato e
gia' certificato** di A1 (`04-b20-desktop-vero.py`).

⚠ Sono due programmi e non uno perche' cosi' il giudizio si puo' rifare, sugli
  stessi byte, senza rifare il giro — e perche' un cronometro che giudicasse
  anche il contenuto sarebbe un cronometro che puo' assolversi da solo.

===========================================================================
⛔ IL FLUSSO SI CONCATENA, E NON SI GIUDICA UN FOTOGRAMMA PER VOLTA
===========================================================================

Un delta HEVC **non si decodifica da solo**: senza la chiave e senza i delta che
lo precedono, il decodificatore non ha niente su cui predire.  ⇒ I carichi si
scrivono di seguito in un unico `.265`/`.obu`, in ordine di arrivo, e il giudice
decodifica **tutti** i fotogrammi e li giudica uno per uno.

⛔ E l'indice del fotogramma decodificato vale come indice dell'arrivo **solo se
   i due conti combaciano**.  Se non combaciano il giudice lo dichiara e si
   ferma: allineare a occhio due liste di lunghezza diversa e' il modo piu'
   rapido di attribuire a un fotogramma l'ora di un altro.
   ⚠ Per questo un fotogramma il cui stream e' finito con `RESET_STREAM` (§6.2,
     abbandonato) **non entra nel flusso concatenato e non entra nella lista**:
     i suoi byte sono incompleti, e infilarli spezzerebbe la decodifica di tutti
     quelli dopo.

===========================================================================
⛔ I CODICI D'USCITA
===========================================================================

    0  la stretta di mano e' arrivata a SESSIONE e il giro e' finito
    2  la stretta di mano NON e' arrivata a SESSIONE (non si e' misurato niente)
    4  la connessione e' caduta prima della fine dell'attesa
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
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ SI EREDITA, NON SI RISCRIVE.  La stretta di mano e lo smistamento degli
#    stream unidirezionali di WebTransport sono gia' il secondo lettore di
#    `RCP.md`, e hanno gia' pagato due difetti dal vivo (il preambolo `40 54` e
#    il contesto posto troppo tardi).  Riscriverli qui vorrebbe dire ripagarli.
fc = _porta("fc", "02-filo-cliente.py")


def dimmi(*a):
    print(*a, flush=True)


def fabbrica():
    class Cronometro(fc.fabbrica_cliente()):

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            # ⛔ Lo zero: lo pone il guidatore quando scrive `CREDENZIALI`.
            self.t_zero = None
            # sid -> {"t_primo": ..., "dati": bytearray}
            self.raccolta = {}
            # i fotogrammi COMPLETI, in ordine di completamento
            self.completi = []
            self.azzerati = 0

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
                self._completo(sid, r, "fin")

        def _azzerato(self, sid):
            r = self.raccolta.get(sid)
            super()._azzerato(sid)
            self.azzerati += 1
            if r is not None:
                # ⛔ Non entra nella lista: i suoi byte sono incompleti, e
                #    infilarli spezzerebbe la decodifica di tutti quelli dopo.
                self.raccolta.pop(sid, None)

        def _completo(self, sid, r, come):
            d = bytes(r["dati"])
            self.raccolta.pop(sid, None)
            if len(d) <= INTESTAZIONE:
                return
            tipo, codec, lar, alt, num, ist, inp = struct.unpack(
                "!HHIIIQI", d[:INTESTAZIONE])
            self.completi.append({
                "n": len(self.completi) + 1,
                "stream": sid,
                "t_primo_byte": r["t_primo"],
                # ⛔ Il timbro e' QUESTO: il fotogramma e' completo adesso.
                "t_completo": self._ora(),
                "tipo": "chiave" if tipo == CHIAVE else (
                    "delta" if tipo == DELTA else f"0x{tipo:04x}"),
                "codec": codec,
                "larghezza": lar, "altezza": alt,
                "numero": num, "istante_server_us": ist, "input": inp,
                "byte": len(d) - INTESTAZIONE,
                "carico": d[INTESTAZIONE:],
            })

    return Cronometro


async def guarda(cli, attesa, chiedi_ogni=0.0):
    """Resta ad ascoltare **con gli occhi aperti**, e dice quando cade.

    ⭐ `chiedi_ogni` > 0: si manda un `RICHIEDI_CHIAVE` ogni tanto, come fa un
    client vero che non vede arrivare niente (§5.2 lo IMPONE al client).
    ⛔ E non e' un artificio del banco: `[M]` 14 agosto 2026, A1 ha visto un
       client chiedere **dodici volte** una chiave che non arrivava.  ⚠ Serve
       alla scena del primo gemello, perche' e' l'unica cosa che fa scrivere il
       PADRE sul socket del figlio — e senza, il figlio resta fermo in
       `recvmsg` e il ciclo a vuoto **non compare affatto**.
    ⚠ Il passo non scende sotto i 300 ms: §5.2 vieta due richieste a meno di
      200 ms, e un banco che violasse la specifica misurerebbe il congedo.
    """
    fine = asyncio.get_event_loop().time() + attesa
    visti = 0
    prossima = asyncio.get_event_loop().time() + chiedi_ogni
    while asyncio.get_event_loop().time() < fine:
        if cli.caduta is not None:
            return f"caduto: {cli.caduta}"
        if chiedi_ogni > 0 and asyncio.get_event_loop().time() >= prossima:
            cli.chiedi_chiave(len(cli.completi))
            prossima = asyncio.get_event_loop().time() + chiedi_ogni
        while len(cli.completi) > visti:
            f = cli.completi[visti]
            visti += 1
            if visti <= 6 or f["tipo"] == "chiave":
                dimmi(f"   fotogramma {f['n']:4d}  t={f['t_completo']:8.3f} s  "
                      f"{f['tipo']:6s}  {f['byte']:7d} byte  "
                      f"{f['larghezza']}x{f['altezza']}")
        await asyncio.sleep(0.01)
    return None


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = fc.carica_b3()
    Cliente = fabbrica()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"

    os.makedirs(a.lavoro, exist_ok=True)
    dimmi("== O1 — il cronometro dell'apparizione: LOGIN → primo pixel")
    dimmi(f"   bersaglio: https://{autorita}{a.percorso}")
    dimmi(f"   ⛔ lo zero del cronometro e' l'istante di `CREDENZIALI`, "
          f"e il secondo fisso di §4.4-bis sta DENTRO la misura")
    dimmi(f"   scena: {a.scena}")
    dimmi(f"   attesa: {a.attesa} s\n")

    caduta = None
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

            # ⛔⭐ LO ZERO DEL CRONOMETRO — e si pone PRIMA di scrivere, non
            #     dopo: fra le due righe c'e' la serializzazione, ed e' tempo
            #     che l'utente aspetta.
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
            dimmi("      ⚠ Questo NON e' «il desktop non compare»: non si e' "
                  "misurato niente")
            return 2

        lar, alt = struct.unpack("!II", corpo[1:9])
        dimmi(f"   ⭐ AMMESSO a t={t_ammesso:.3f} s · SESSIONE a "
              f"t={t_sessione:.3f} s · tela concessa {lar}x{alt}\n")
        if cli.contesto is None:
            cli.contesto = fc.f24.Contesto(tela=(lar, alt),
                                           codec_negoziato=a.codec,
                                           sessione_aperta=True)
        caduta = await guarda(cli, a.attesa, a.chiedi_chiave_ogni)

    # ---- quel che si consegna al giudice ---------------------------------
    # ⛔ Un flusso solo, concatenato in ordine di arrivo: vedi il riquadro in
    #    testa.  ⚠ E il nome dice il codec, perche' il demuxer si sceglie da
    #    quello e non si indovina.
    codec = cli.completi[0]["codec"] if cli.completi else a.codec
    est = "265" if codec == 1 else ("obu" if codec == 2 else "bin")
    flusso = os.path.join(a.lavoro, f"{a.etichetta}-flusso.{est}")
    with open(flusso, "wb") as f:
        for x in cli.completi:
            f.write(x["carico"])

    misura = {
        "banco": "04-b31-apparizione", "etichetta": a.etichetta,
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "porta": a.porta, "utente": a.utente, "scena": a.scena,
        "tela_chiesta": [a.larghezza, a.altezza],
        "tela_concessa": [lar, alt],
        "codec": codec,
        "t_ammesso": t_ammesso, "t_sessione": t_sessione,
        "attesa": a.attesa, "caduta": caduta,
        "azzerati": cli.azzerati,
        "flusso": os.path.basename(flusso),
        # ⛔ Senza il carico: i byte stanno nel flusso, e qui ci sono gli
        #    ISTANTI.  Due copie degli stessi byte in due file sono due verita'.
        "fotogrammi": [{k: v for k, v in x.items() if k != "carico"}
                       for x in cli.completi],
    }
    percorso = os.path.join(a.lavoro, f"{a.etichetta}-misura.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(misura, f, ensure_ascii=False, indent=1)

    n = len(cli.completi)
    chiavi = sum(1 for x in cli.completi if x["tipo"] == "chiave")
    dimmi(f"\n   fotogrammi COMPLETI: {n} ({chiavi} chiavi, "
          f"{cli.azzerati} azzerati e non contati)")
    if n:
        dimmi(f"   il PRIMO e' arrivato a t={cli.completi[0]['t_completo']:.3f} s"
              f" — ⚠ e «arrivato» NON e' «e' il desktop»: lo dice il giudice")
    else:
        dimmi(f"   {ROSSO}⛔ ZERO fotogrammi completi in {a.attesa} s{GRIGIO}")
    dimmi(f"   flusso: {flusso}")
    dimmi(f"   misura: {percorso}")
    if caduta:
        dimmi(f"\n   {ROSSO}⛔ {caduta}{GRIGIO}")
        return 4
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="O1 — il cronometro LOGIN → primo pixel")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, help="⛔ la 7711, di questo anello")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="provao1")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (D12)")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--attesa", type=float, default=22.0,
                   help="⛔ sotto i 30 s: §5.3 stacca per silenzio, e questo "
                        "client non manda niente apposta")
    p.add_argument("--chiedi-chiave-ogni", type=float, default=0.0,
                   help="⭐ manda un RICHIEDI_CHIAVE ogni N secondi, come un "
                        "client vero che non vede niente (0 = mai; minimo 0,3 "
                        "per §5.2)")
    p.add_argument("--lavoro", default="/tmp/04-b31")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)",
                   help="⛔ CODER.md §3.2: la scena si DICHIARA")
    a = p.parse_args()
    a.parola = fc.parola_dagli_argomenti(a)
    if not a.porta:
        dimmi("⛔ serve --porta.  Per O1 e' la 7711.")
        sys.exit(2)
    if 0 < a.chiedi_chiave_ogni < 0.3:
        dimmi("⛔ --chiedi-chiave-ogni sotto 0,3 s: §5.2 vieta due "
              "RICHIEDI_CHIAVE a meno di 200 ms, e il banco misurerebbe il "
              "congedo invece del difetto")
        sys.exit(2)
    if a.scena == "(non dichiarata)":
        dimmi("⛔ serve --scena: una misura senza scena dichiarata misura la "
              "scena, non il prodotto (`CODER.md` §3.2)")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        dimmi(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
