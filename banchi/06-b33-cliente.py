#!/usr/bin/env python3
"""06-b33-cliente.py — ⛔⛔ IL RIATTACCO CHE COMANDA: si stacca, si riattacca a
misura DIVERSA, e **solo allora** si batte un tasto, si muove il puntatore e si
clicca.

    python3 06-b33-cliente.py --porta 7781 --utente provai6 \\
            --parola-file /tmp/p --lavoro /media/REMOTIX/tmp/06-i \\
            --tela-a 1264x800 --tela-b 1000x640 --etichetta giro1 \\
            --scena "testimone Wayland aperto PRIMA dello stacco"

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.

===========================================================================
⛔ PERCHE' QUESTO BANCO ESISTE — `PIANO.md`, fase 6
===========================================================================

*«il banco del riattacco DEVE battere un tasto e muovere il puntatore dopo, non
solo verificare che la sessione ci sia: e' la forma "una prova verde col difetto
vivo" esattamente dove si presenta»*.

`[M]` Il 15 agosto 2026 si e' visto **nel registro** che al cambio di geometria
`libei` ricrea i dispositivi assoluti e che `input.c` li riaggancia.  ⛔ Ma
nessuno ha mai battuto un tasto dopo — e il registro di chi manda dice che ha
chiamato una funzione, non che il desktop ha ricevuto (`CODER.md` §3.8).  ⇒ Il
verdetto lo da' il **testimone dentro la sessione**, non questo programma.

===========================================================================
⛔ LA CATENA VERA DEL RIATTACCO, E NON QUELLA CHE SI CREDEREBBE
===========================================================================

`[R]` `rcp.c:2177-2205`: al riattacco `SESSIONE` **NON** concede la misura
chiesta — concede quella che il palco HA GIA' (I4: il palco sopravvive al
distacco), perche' cosi' i pixel arrivano da subito invece che mai.  ⇒ Il cambio
di misura arriva dopo, con `ADATTA_TELA`, ed e' **quello** che fa ricreare i
dispositivi a `libei`.

    1. ATTACCA(tela B)  →  SESSIONE(tela A)     ⚠ concessa quella del palco
    2. ADATTA_TELA(tela B)  →  TELA(tela B)     ⭐ e QUI i dispositivi muoiono
    3. e SOLO ADESSO si batte, si punta, si clicca

⛔ Un banco che saltasse il passo 2 misurerebbe un riattacco **senza ricambio di
   dispositivi**, cioe' resterebbe verde senza aver mai visto il difetto che
   cerca.  E' il modo piu' rapido di scrivere una prova inutile.

===========================================================================
⛔ I CODICI D'USCITA
===========================================================================

    0  il giro e' finito (verde o rosso lo dice il giudice, non questo)
    2  la stretta di mano NON e' arrivata a SESSIONE: non si e' misurato niente
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
INTESTAZIONE = 28              # §6.2, «28 byte esatti, senza riempimento»
CHIAVE, DELTA = 0x0301, 0x0302

# ⛔ §7.3 — e i codici sono quelli di evdev, non una convenzione nostra.
T_VISTA, T_ADATTA_TELA, T_TELA = 0x0008, 0x000B, 0x000E
T_PUNTATORE, T_PULSANTE, T_ROTELLA = 0x0101, 0x0102, 0x0103
T_LETTERA, T_POSIZIONE = 0x0104, 0x0105
KEY_ENTER, KEY_A, KEY_LEFTCTRL = 28, 30, 29
BTN_LEFT = 0x110

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ SI EREDITA, NON SI RISCRIVE: la stretta di mano e lo smistamento degli
#    stream di WebTransport hanno gia' pagato due difetti dal vivo.
fc = _porta("fc", "02-filo-cliente.py")


def dimmi(*a):
    print(*a, flush=True)


def misura(t):
    l, a = t.lower().split("x")
    return int(l), int(a)


def fabbrica():
    class Testimone(fc.fabbrica_cliente()):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.t_zero = time.monotonic()
            self.raccolta = {}
            self.completi = []
            self.azzerati = 0
            self.input_stream = None

        def apri_input(self):
            """⛔ §2.5: l'input vive su UNO stream UNIDIREZIONALE del CLIENT,
            aperto **dopo aver ricevuto `SESSIONE`** e tenuto aperto.

            ⛔⛔ E NON sul canale di controllo — `[M]` 16 agosto 2026, primo
            giro di questo banco: mandandolo li' il server congeda con
            `0x0b ERRORE_PROTOCOLLO`, dettaglio *«byte alto del tipo non e'
            controllo»* (`rcp.c:4735`).  ⭐ Era un difetto del BANCO, non del
            prodotto, e il registro l'ha detto in una riga — `CODER.md` §3.11:
            quando codice letto e misura si contraddicono, il sospetto va
            prima sulla misura.

            ⚠ `aioquic` scrive da se' il preambolo di WebTransport (il tipo
            `0x54` e il numero della sessione): i «primi due byte» di §2.5 sono
            i primi del CARICO, non dello stream (rilievo P18).
            """
            self.input_stream = self._http.create_webtransport_stream(
                self.sessione, is_unidirectional=True)
            return self.input_stream

        def manda_input(self, dati):
            # ⛔ E lo stream NON si chiude: §2.5 dice «uno solo, tenuto
            #    aperto».  Un FIN qui sarebbe «il client non comanda piu'».
            self._quic.send_stream_data(self.input_stream, dati,
                                        end_stream=False)
            self.transmit()

        def _ora(self):
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
            # ⛔ §6.2: uno stream azzerato e' un fotogramma ABBANDONATO dal
            #    server — «fotogrammi scartati per misura» e' precisamente
            #    questo numero, ed e' una delle quattro righe da rimisurare.
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
                "t": self._ora(),
                "tipo": "chiave" if tipo == CHIAVE else (
                    "delta" if tipo == DELTA else f"0x{tipo:04x}"),
                "larghezza": lar, "altezza": alt, "numero": num,
                # ⛔ `input` e' l'`id` dell'ultimo input che il COMPOSITORE HA
                #    PRESO (§6.2): e' il solo modo di sapere, dal filo, che
                #    l'iniezione e' avvenuta — e NON che sia arrivata a una
                #    finestra, che lo dice solo il testimone.
                "input": inp,
                "byte": len(d) - INTESTAZIONE,
            })

    return Testimone


async def stretta(a, tela, conf, autorita, b3, etichetta):
    """Una connessione intera, fino a `SESSIONE`.  Torna (cli, gestore, misure).

    ⛔ La connessione si tiene aperta dal chiamante: e' lui che decide quando
       staccare, ed e' lo stacco la cosa che questo banco misura.
    """
    from aioquic.asyncio import connect
    Cliente = fabbrica()
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, a.percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    if stato != "200":
        raise RuntimeError(f"CONNECT estesa: :status = {stato}")
    cli.apri_controllo()
    cli.codec_atteso = a.codec
    t0 = time.monotonic()
    cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
    await b3.attendi(cli, "ECCOMI")
    cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                          b3.s(a.utente) + b3.s(a.parola)))
    await b3.attendi(cli, "AMMESSO", attesa=25)
    cli.manda(b3.inquadra(b3.T["ATTACCA"],
                          struct.pack("!IIII", tela[0], tela[1],
                                      tela[0], tela[1]) + b3.s(a.disposizione)))
    _, corpo, _ = await b3.attendi(cli, "SESSIONE", attesa=25)
    lar, alt = struct.unpack("!II", corpo[1:9])
    t_ses = round(time.monotonic() - t0, 6)
    if cli.contesto is None:
        cli.contesto = fc.f24.Contesto(tela=(lar, alt),
                                       codec_negoziato=a.codec,
                                       sessione_aperta=True)
    dimmi(f"   [{etichetta}] chiesta {tela[0]}x{tela[1]} · "
          f"SESSIONE concede {ROSSO if (lar, alt) != tela else VERDE}"
          f"{lar}x{alt}{GRIGIO} in {t_ses * 1000:.0f} ms")
    return cli, gestore, {"chiesta": list(tela), "concessa": [lar, alt],
                          "t_sessione_ms": round(t_ses * 1000, 1)}


async def raccogli(cli, secondi, quanti_almeno=0):
    """Ascolta, e dice quanti fotogrammi COMPLETI sono arrivati."""
    fine = asyncio.get_event_loop().time() + secondi
    while asyncio.get_event_loop().time() < fine:
        if cli.caduta is not None:
            return f"caduto: {cli.caduta}"
        if quanti_almeno and len(cli.completi) >= quanti_almeno:
            return None
        await asyncio.sleep(0.01)
    return None


async def porta_a_tela(cli, b3, tela, attesa=12.0):
    """Manda `ADATTA_TELA` e aspetta il `TELA` che §7.1 impone come risposta.

    ⛔ Serve in DUE posti, e per due ragioni diverse:

      · al riattacco, ed e' **la misura**: e' il momento in cui `libei`
        distrugge e ricrea i dispositivi assoluti;
      · all'attacco, ed e' **la preparazione della scena**: il palco sopravvive
        al giro precedente (I4) e porta la tela con cui quello era finito.  ⛔ Un
        giro che partisse dalla tela sbagliata misurerebbe un ridimensionamento
        A→A, cioe' **nessun ricambio di dispositivi**, e resterebbe verde senza
        aver mai visto il difetto che cerca (`CODER.md` §3.4).
    """
    t0 = time.monotonic()
    cli.manda(b3.inquadra(T_ADATTA_TELA, struct.pack("!II", *tela)))
    fine = asyncio.get_event_loop().time() + attesa
    while asyncio.get_event_loop().time() < fine:
        m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
        if m is None:
            raise RuntimeError(f"il canale si e' chiuso: {cli.caduta}")
        tipo, corpo, _ = m
        if tipo == T_TELA:
            # ⛔ §7.1: u8 esito · u8 MOTIVO · u32 larghezza · u32 altezza.  Il
            #    motivo c'e' anche quando e' 0, e chi lo saltasse leggerebbe la
            #    larghezza spostata di un byte — cioe' un numero enorme che si
            #    legge come una diagnosi vera.
            return {"esito": corpo[0], "motivo": corpo[1],
                    "larghezza": struct.unpack("!I", corpo[2:6])[0],
                    "altezza": struct.unpack("!I", corpo[6:10])[0],
                    "ms": round((time.monotonic() - t0) * 1000, 1)}
        dimmi(f"   ⚠ messaggio {tipo:#06x} mentre aspettavo TELA")
    return {"errore": f"nessun TELA in {attesa} s — §7.1 ne impone uno"}


class Contatore:
    """L'`id` dell'input — ⛔ cresce su TUTTO il canale, non uno per tipo.

    §7.3: *«e' quello che torna nel campo `input` dei fotogrammi (§6.2), e con
    contatori separati non tornerebbe niente»*.
    """

    def __init__(self):
        self.n = 0

    def testa(self):
        self.n += 1
        return struct.pack("!IQ", self.n, int(time.monotonic() * 1_000_000))


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    b3 = fc.carica_b3()
    tela_a, tela_b = misura(a.tela_a), misura(a.tela_b)

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    os.makedirs(a.lavoro, exist_ok=True)

    dimmi("== 06-b33 — IL RIATTACCO CHE COMANDA")
    dimmi(f"   bersaglio: https://{autorita}{a.percorso}  utente {a.utente}")
    dimmi(f"   scena: {a.scena}")
    dimmi(f"   tela all'attacco: {tela_a[0]}x{tela_a[1]} · "
          f"al riattacco: {tela_b[0]}x{tela_b[1]}")
    dimmi("")

    esito = {"banco": "06-b33-riattacco", "etichetta": a.etichetta,
             "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "scena": a.scena, "porta": a.porta, "utente": a.utente,
             "tela_a": list(tela_a), "tela_b": list(tela_b)}

    # ---- 1. l'attacco -----------------------------------------------------
    dimmi("-- 1. l'attacco, alla tela A")
    cli, gestore, m1 = await stretta(a, tela_a, conf, autorita, b3, "attacco")
    esito["attacco"] = m1
    await raccogli(cli, a.prima, quanti_almeno=a.fotogrammi_prima)
    esito["attacco"]["fotogrammi"] = len(cli.completi)
    esito["attacco"]["azzerati"] = cli.azzerati
    esito["attacco"]["misure_viste"] = sorted(
        {f"{x['larghezza']}x{x['altezza']}" for x in cli.completi})
    dimmi(f"   fotogrammi completi: {len(cli.completi)} "
          f"(azzerati {cli.azzerati}) · misure viste: "
          f"{esito['attacco']['misure_viste']}")

    # ⛔⭐ E QUI CI SI PUO' FERMARE, ED E' L'UNICO MODO DI COSTRUIRE LA SCENA.
    #
    # L'applicazione «aperta prima» ha bisogno di un monitor per aprirsi, e il
    # monitor nasce **col palco**, cioe' al primo attacco.  ⇒ Un giro
    # `--solo attacco` fa nascere il palco e se ne va; il palco sopravvive al
    # distacco (I4) e il lanciatore apre l'applicazione **su un desktop che
    # esiste e con nessun client attaccato**.  ⚠ Il giro vero viene dopo.
    if a.solo == "attacco":
        # ⛔ E la scena si NORMALIZZA: il palco sopravvive al giro precedente
        #    (I4) e porta la tela con cui quello era finito.  Senza questa riga
        #    il giro vero partirebbe gia' alla tela B e il suo `ADATTA_TELA`
        #    sarebbe un B→B, cioe' zero ricambi di dispositivi.
        if tuple(m1["concessa"]) != tela_a:
            dimmi(f"   ⚠ il palco portava {m1['concessa']}: lo riporto a "
                  f"{tela_a[0]}x{tela_a[1]} con un ADATTA_TELA")
            esito["normalizza"] = await porta_a_tela(cli, b3, tela_a)
            dimmi(f"   TELA: {esito['normalizza']}")
            await raccogli(cli, 3.0)
        dimmi("\n-- ⭐ --solo attacco: il palco e' nato, mi stacco e me ne vado")
        await gestore.__aexit__(None, None, None)
        p = os.path.join(a.lavoro, f"{a.etichetta}-esito.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(esito, f, ensure_ascii=False, indent=1)
        dimmi(f"   esito: {p}")
        return 0

    # ---- 2. lo stacco -----------------------------------------------------
    # ⛔ E si stacca DAVVERO: si chiude la connessione QUIC, che e' quel che fa
    #    l'utente chiudendo la scheda.  ⚠ NON si manda `TERMINA_SESSIONE`
    #    (0x0011): quello CHIUDE la sessione grafica, e con la sessione se ne
    #    andrebbe l'applicazione aperta prima — cioe' la scena che questo banco
    #    esiste per costruire.
    dimmi("\n-- 2. lo stacco (la connessione si chiude, la SESSIONE resta: I4)")
    t_stacco = time.monotonic()
    await gestore.__aexit__(None, None, None)
    dimmi(f"   staccato.  ⚠ pausa {a.pausa} s — ⛔ sotto i 30 s di §5.3, o la "
          f"sessione avrebbe gia' rilasciato tutto")
    await asyncio.sleep(a.pausa)

    # ---- 3. il riattacco a misura DIVERSA ---------------------------------
    dimmi("\n-- 3. il riattacco, alla tela B")
    cli, gestore, m2 = await stretta(a, tela_b, conf, autorita, b3, "riattacco")
    esito["riattacco"] = m2
    esito["riattacco"]["t_dallo_stacco_ms"] = round(
        (time.monotonic() - t_stacco) * 1000, 1)
    await raccogli(cli, a.prima, quanti_almeno=a.fotogrammi_prima)
    esito["riattacco"]["fotogrammi"] = len(cli.completi)
    esito["riattacco"]["azzerati"] = cli.azzerati
    esito["riattacco"]["misure_viste"] = sorted(
        {f"{x['larghezza']}x{x['altezza']}" for x in cli.completi})
    dimmi(f"   fotogrammi completi: {len(cli.completi)} "
          f"(azzerati {cli.azzerati}) · misure viste: "
          f"{esito['riattacco']['misure_viste']}")

    # ---- 4-bis. ⛔⛔ LA SCENA CATTIVA: si tiene GIU' mentre i dispositivi muoiono
    #
    # ⭐ L'ipotesi, dichiarata PRIMA e letta nel codice di Mutter:
    #
    #   `[R]` `meta-eis-client.c:197-206` — `remove_viewport_devices()` chiama
    #         `eis_device_remove()` e NON passa da `drop_device()`, che e'
    #         l'unico posto dove Mutter rilascia quel che era premuto;
    #   `[R]` `meta-eis-client.c:612-621` — `handle_button()` ingoia **in
    #         silenzio** un rilascio per un pulsante che non risulta premuto sul
    #         dispositivo che lo riceve (*«Duplicate press/release»*), e dopo il
    #         ricambio il dispositivo e' un ALTRO.
    #
    # ⇒ `input.c` manda il rilascio sul dispositivo NUOVO (`dispositivo_tolto`
    #   tiene apposta le mappe di bit), `input_rilascia_tutto()` lo conta come
    #   partito — e il desktop resta col pulsante giu'.  ⛔ Sarebbe «il conto
    #   torna, l'evento no»: un desktop che non prende piu' i clic dopo un
    #   ridimensionamento, senza un errore da nessuna parte.
    #
    # ⚠ E il TASTO invece dovrebbe arrivare: la tastiera non e' un dispositivo di
    #   viewport (`remove_viewport_devices` guarda TOUCH e POINTER_ABSOLUTE), e
    #   al cambio di geometria non ricambia.  ⭐ E' un controllo interno alla
    #   scena: se non arrivasse nemmeno quello, la causa sarebbe un'altra.
    if a.modo in ("tenuto", "cura"):
        dimmi("\n-- 4-bis. ⛔ SI TIENE GIU' MENTRE I DISPOSITIVI MUOIONO"
              + ("  (⭐ ma con la CURA)" if a.modo == "cura" else ""))
        cli.apri_input()
        c0 = Contatore()
        # ⛔ Le coordinate sono sulla tela IN VIGORE ADESSO — cioe' quella che
        #    `SESSIONE` ha concesso al riattacco (§7.3: fuori intervallo e'
        #    `ERRORE_PROTOCOLLO`).  ⚠ Non e' `tela_b`: quella arriva DOPO.
        bl0, ba0 = m2["concessa"]
        atti0 = []

        def giu(nome, tipo, corpo, pausa=0.4):
            cli.manda_input(b3.inquadra(tipo, c0.testa() + corpo))
            atti0.append({"atto": nome, "id": c0.n})
            dimmi(f"   → {nome} (id {c0.n})")
            return pausa

        # ⛔ Prima il puntatore DENTRO la finestra, o il pulsante non avrebbe un
        #    destinatario e il rosso accuserebbe la cosa sbagliata.
        await asyncio.sleep(giu(f"PUNTATORE {bl0 // 2},{ba0 // 2}", T_PUNTATORE,
                                struct.pack("!II", bl0 // 2, ba0 // 2)))
        await asyncio.sleep(giu("PULSANTE BTN_LEFT GIU' (e li' resta)",
                                T_PULSANTE, struct.pack("!HB", BTN_LEFT, 1)))
        await asyncio.sleep(giu("POSIZIONE KEY_LEFTCTRL GIU' (e li' resta)",
                                T_POSIZIONE, struct.pack("!HB", KEY_LEFTCTRL, 1)))
        esito["tenuti_prima"] = atti0

        # ⭐⭐ LA CURA, SIMULATA DAL FILO — ed e' fedele, perche' passa dalla
        #     STESSA strada che prenderebbe il prodotto: `input_pulsante(…, 0)`
        #     → `manda_bottone()` sul dispositivo ANCORA VIVO.
        #
        # ⛔ La cura vera e' UNA RIGA in `figlio.c`, e non c'e' niente da
        #    scrivere in `input.c`: `input_rilascia_tutto(palco_input)` **prima**
        #    di `cattura_ridimensiona()`.  Dopo il ricambio non si recupera piu'
        #    — `[M]` misurato, e `[R]` `meta-seat-impl.c:899-908` dice perche'.
        if a.modo == "cura":
            await asyncio.sleep(giu("⭐ PULSANTE BTN_LEFT SU — PRIMA del ricambio",
                                    T_PULSANTE, struct.pack("!HB", BTN_LEFT, 0)))
            await asyncio.sleep(giu("⭐ POSIZIONE KEY_LEFTCTRL SU — PRIMA del ricambio",
                                    T_POSIZIONE,
                                    struct.pack("!HB", KEY_LEFTCTRL, 0)))
            esito["curati_prima"] = atti0[-2:]

    # ---- 4. ADATTA_TELA: ed e' QUI che i dispositivi muoiono ---------------
    dimmi("\n-- 4. ADATTA_TELA — ⭐ il momento in cui `libei` ricrea i dispositivi")
    n_prima = len(cli.completi)
    try:
        tela_esito = await porta_a_tela(cli, b3, tela_b)
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        tela_esito = {"errore": f"{type(e).__name__}: {e}"}
    esito["adatta_tela"] = tela_esito
    dimmi(f"   TELA: {tela_esito}")
    # ⛔ E si aspetta un fotogramma della misura NUOVA prima di battere: senza,
    #    si batterebbe mentre il palco e' ancora a mezza strada, e un rosso
    #    accuserebbe l'input di una cosa che non e' sua.
    fine = asyncio.get_event_loop().time() + 12
    vista_nuova = False
    while asyncio.get_event_loop().time() < fine:
        for x in cli.completi[n_prima:]:
            if (x["larghezza"], x["altezza"]) == tela_b:
                vista_nuova = True
        if vista_nuova:
            break
        await asyncio.sleep(0.02)
    esito["fotogramma_alla_misura_nuova"] = vista_nuova
    esito["azzerati_al_ritela"] = cli.azzerati - esito["riattacco"]["azzerati"]
    dimmi(f"   fotogramma alla misura nuova: "
          f"{VERDE + 'SI' if vista_nuova else ROSSO + 'NO'}{GRIGIO} · "
          f"fotogrammi scartati al ritela: {esito['azzerati_al_ritela']}")

    # ---- 5. ⭐⭐ E SOLO ADESSO SI COMANDA ---------------------------------
    dimmi("\n-- 5. ⭐⭐ SI BATTE UN TASTO, SI MUOVE IL PUNTATORE, SI CLICCA")
    c = Contatore()
    bl, ba = tela_b
    # ⛔ Due punti DIVERSI e lontani: Wayland non emette `motion` se la
    #    posizione non cambia, e «stessa posizione» e «non consegnato» hanno lo
    #    stesso aspetto (`CODER.md` §3.10 — B24 ci e' cascato il 14 agosto).
    punti = [(bl // 4, ba // 4), (bl * 3 // 4, ba * 3 // 4)]
    atti = []

    if cli.input_stream is None:
        cli.apri_input()
    dimmi(f"   stream di input aperto: {cli.input_stream} "
          f"(unidirezionale, §2.5)")

    # ⛔⛔ E IL RILASCIO DI QUEL CHE ERA GIU' VIENE PRIMA DI TUTTO IL RESTO.
    #     E' la misura di questa scena: il pulsante e il tasto premuti PRIMA del
    #     ricambio si rilasciano DOPO, e il verdetto lo da' il testimone.
    if a.modo in ("tenuto", "cura"):
        c.n = max(c.n, 5)   # gli id crescono su TUTTO il canale (§7.3)
        for nome, tipo, corpo in (
                ("PULSANTE BTN_LEFT SU — dopo il ricambio", T_PULSANTE,
                 struct.pack("!HB", BTN_LEFT, 0)),
                ("POSIZIONE KEY_LEFTCTRL SU — dopo il ricambio", T_POSIZIONE,
                 struct.pack("!HB", KEY_LEFTCTRL, 0))):
            cli.manda_input(b3.inquadra(tipo, c.testa() + corpo))
            dimmi(f"   → {nome} (id {c.n})")
            await asyncio.sleep(0.5)

    def batti(nome, tipo, corpo, pausa=0.35):
        cli.manda_input(b3.inquadra(tipo, c.testa() + corpo))
        atti.append({"atto": nome, "id": c.n,
                     "t": round(time.monotonic() - cli.t_zero, 6)})
        dimmi(f"   → {nome} (id {c.n})")
        return pausa

    for x, y in punti:
        await asyncio.sleep(batti(f"PUNTATORE {x},{y}", T_PUNTATORE,
                                  struct.pack("!II", x, y)))
    await asyncio.sleep(batti("POSIZIONE KEY_ENTER giu'", T_POSIZIONE,
                              struct.pack("!HB", KEY_ENTER, 1)))
    await asyncio.sleep(batti("POSIZIONE KEY_ENTER su", T_POSIZIONE,
                              struct.pack("!HB", KEY_ENTER, 0)))
    await asyncio.sleep(batti("LETTERA «a»", T_LETTERA,
                              struct.pack("!I", ord("a"))))
    await asyncio.sleep(batti("PULSANTE BTN_LEFT giu'", T_PULSANTE,
                              struct.pack("!HB", BTN_LEFT, 1)))
    await asyncio.sleep(batti("PULSANTE BTN_LEFT su", T_PULSANTE,
                              struct.pack("!HB", BTN_LEFT, 0)))
    # e un secondo Invio, per il terminale che conta le righe
    await asyncio.sleep(batti("POSIZIONE KEY_ENTER giu' (2)", T_POSIZIONE,
                              struct.pack("!HB", KEY_ENTER, 1)))
    await asyncio.sleep(batti("POSIZIONE KEY_ENTER su (2)", T_POSIZIONE,
                              struct.pack("!HB", KEY_ENTER, 0)))
    esito["atti"] = atti
    esito["id_spediti"] = c.n

    # ⛔ E si aspetta un po': l'`id` torna indietro nel campo `input` dei
    #    fotogrammi, ma solo quando ne parte uno — e su un desktop fermo puo'
    #    volerci.  ⚠ Questo dice che il COMPOSITORE l'ha preso, non che una
    #    finestra l'ha ricevuto: quello lo dice il testimone.
    await raccogli(cli, a.dopo)
    inp = [x["input"] for x in cli.completi if x["input"]]
    esito["input_tornato_max"] = max(inp) if inp else 0
    esito["fotogrammi_totali"] = len(cli.completi)
    esito["azzerati_totali"] = cli.azzerati
    esito["misure_viste_totali"] = sorted(
        {f"{x['larghezza']}x{x['altezza']}" for x in cli.completi})
    dimmi(f"\n   id spediti: {c.n} · id massimo TORNATO nei fotogrammi: "
          f"{esito['input_tornato_max']}")
    dimmi(f"   ⚠ e questo dice che il COMPOSITORE ha preso l'input, "
          f"NON che una finestra l'ha ricevuto — quello lo dice il testimone")

    await gestore.__aexit__(None, None, None)

    p = os.path.join(a.lavoro, f"{a.etichetta}-esito.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    dimmi(f"\n   esito: {p}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="06-b33 — il riattacco che comanda")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7781)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="provai6")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (D12)")
    p.add_argument("--tela-a", default="1264x800")
    p.add_argument("--tela-b", default="1000x640")
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1)
    p.add_argument("--prima", type=float, default=6.0,
                   help="secondi di ascolto dopo ogni SESSIONE")
    p.add_argument("--fotogrammi-prima", type=int, default=3)
    p.add_argument("--pausa", type=float, default=3.0,
                   help="⛔ sotto i 30 s di §5.3, o la sessione ha gia' "
                        "rilasciato tutto e si misura un'altra cosa")
    p.add_argument("--dopo", type=float, default=4.0)
    p.add_argument("--lavoro", default="/media/REMOTIX/tmp/06-i")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)")
    p.add_argument("--modo", choices=["comanda", "tenuto", "cura"],
                   default="comanda",
                   help="«tenuto» tiene GIU' un pulsante e un tasto MENTRE i "
                        "dispositivi muoiono, e li rilascia dopo: e' la scena "
                        "cattiva, quella in cui il conto torna e l'evento no")
    p.add_argument("--solo", choices=["tutto", "attacco"], default="tutto",
                   help="«attacco» fa nascere il palco e si stacca: serve ad "
                        "avere un monitor su cui APRIRE l'applicazione prima")
    a = p.parse_args()
    a.parola = fc.parola_dagli_argomenti(a)
    if a.scena == "(non dichiarata)":
        dimmi("⛔ serve --scena: una misura senza scena dichiarata misura la "
              "scena, non il prodotto (`CODER.md` §3.2)")
        sys.exit(2)
    if a.pausa >= 28:
        dimmi("⛔ --pausa a 28 s o piu': §5.3 stacca per silenzio a 30 s e il "
              "banco misurerebbe il rilascio, non il riattacco")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        dimmi(f"\n   {ROSSO}⛔ {type(e).__name__}: {e}{GRIGIO}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
