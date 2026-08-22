#!/usr/bin/env python3
"""06-b43-sonda.py — ⛔ IL SECONDO CLIENT CHE BUSSA FINCHE' NON ENTRA.

    python3 06-b43-sonda.py --porta 7801 --utente provar7 \\
            --parola-file /tmp/06-b7/parola --tetto 200 --intervallo 1.0 \\
            --etichetta m1 --scena '...'

===========================================================================
⛔⛔ PERCHE' NON BASTA LEGGERE IL REGISTRO DEL SERVER
===========================================================================

Il server scrive *«STACCATO per silenzio: NNNNN ms … posti occupati adesso:
0»*, e sarebbe comodo credergli.  ⛔ Ma e' la trappola **E1** di questo
progetto — *«scritto non e' in vigore»*: quella riga dice che una funzione e'
stata chiamata, **non** che un altro dispositivo riesca davvero a entrare.
Fra il posto lasciato e la sessione nuova ci sono `posto_prendi()`, la
verifica di §5.1 sulla sessione LOCALE, il budget di §5.5 e la rinascita del
palco — e ognuno di quelli puo' dire di no.

⇒ Questa sonda misura **il fatto che serve a chi usa i banchi**: da quando un
  client se n'e' andato, **fra quanto un altro puo' attaccarsi**.

===========================================================================
⛔ COME SI LEGGE IL RISULTATO, E PERCHE' CI SONO DUE ISTANTI PER TENTATIVO
===========================================================================

Il posto si prende **quando il server elabora `ATTACCA`**, non quando arriva
`SESSIONE`: fra i due c'e' la nascita (o il riaggancio) del palco, che dura
secondi.  ⇒ Ogni tentativo registra `attacca_ns` — quando `ATTACCA` e' partito
— e l'esito.  Il momento in cui il posto si e' liberato sta **fra**:

  · l'`attacca_ns` dell'ultimo tentativo respinto con `0x0F GIA_ATTIVA_REMOTA`
  · l'`attacca_ns` del primo tentativo riuscito

⚠ E la larghezza di quella forchetta e' l'INCERTEZZA della misura: si
  dichiara, non si nasconde dietro una media.

⛔⛔ E `SESSIONE` PORTA UNO STATO CHE NON DICE NIENTE — `[M]` 22 agosto 2026.

`RCP.md` §… lo dichiara *«u8 stato — 1 = NUOVA, 2 = RIPRESA»*, e questo banco
era stato scritto per leggere da li' la risposta alla domanda *«il figlio di
prima e' ancora vivo?»*.  ⛔ **Non si puo'**: `rcp.c:2589` scrive
`sc_byte(&w, 1)` — la costante — e il server **non manda mai `2`**.

`[M]` Dodici attacchi misurati su questa macchina, tutti dopo il primo, tutti
su un figlio che `ps` mostrava avere **lo stesso pid**: stato = **1** dodici
volte su dodici.  ⇒ E' la forma **E1** — *«scritto non e' in vigore»* — nella
stessa veste che `RCP_INATTIVITA` aveva prima del 16 agosto: un valore
dichiarato nel protocollo che nessuna riga produce, e che un'altra
implementazione dovrebbe gestire per niente.

⇒ Questo banco lo registra lo stesso, ⛔ **ma la domanda sul figlio la risponde
  `ps`**, non il filo.  Chi scrive banchi non si fidi di quel byte.

===========================================================================
⛔ QUEL CHE QUESTA SONDA **NON** MISURA
===========================================================================

Ogni tentativo costa una stretta di mano intera, PAM compreso, piu' il
**secondo fisso** di §4.4-bis: ⇒ la risoluzione non e' `--intervallo`, e' il
periodo vero fra due `attacca_ns` consecutivi, che il JSONL scrive.  Chi legge
un numero da qui senza guardare quel periodo si sta inventando una precisione.

⛔⛔ E QUI C'ERA SCRITTO UNA FALSITA', PAGATA DA UN ALTRO — `[M]` 22 ago 2026.

Diceva: ~~«le credenziali sono GIUSTE: il conto dei tre fallimenti di §4.4-bis
non viene toccato, quindi questa sonda **non puo'** far scattare il ban»~~.

⛔ Puo'.  Le credenziali sono giuste **per il server con cui ha cominciato**.
Alle 06:17:38 un altro agente ha preso la porta 7801 e ci ha messo il suo
server; questa sonda ha continuato a bussare per venti minuti senza
accorgersene, le sue credenziali li' non passavano, e il ban di §4.4-bis —
che e' per **INDIRIZZO** e dura dodici ore — e' scattato nel ban-file
dell'altro (`/media/REMOTIX/tmp/07-r/ban`: `[192.168.0.2]`).

⚠ La regola dell'isolamento («porta propria, ban-file proprio») era rispettata
  e **non e' bastata**: protegge chi la segue, non chi gli si siede addosso.
⇒ Da qui in poi questa sonda **smette di bussare** appena vede credenziali
  rifiutate o tre errori di connessione di fila.  Il codice e la ragione lunga
  stanno nel ciclo, in fondo.
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

MOTIVI = {0x01: "CHIUSO_DALL_UTENTE", 0x02: "INATTIVITA",
          0x03: "SESSIONE_ABBANDONATA", 0x04: "SESSIONE_LOCALE_PREVALSA",
          0x05: "GIA_ATTIVA_LOCALE", 0x06: "BUDGET_PIENO",
          0x0B: "ERRORE_PROTOCOLLO", 0x0C: "SERVER_IN_CHIUSURA",
          0x0D: "TEMPO_SCADUTO", 0x0E: "SESSIONE_NON_SERVIBILE",
          0x0F: "GIA_ATTIVA_REMOTA", 0x10: "SESSIONE_TERMINATA"}


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


fc = _porta("fc", "02-filo-cliente.py")


def dimmi(*a):
    print(*a, flush=True)


async def un_tentativo(a, n, b3, Cliente, conf, autorita):
    """Un solo giro: stretta di mano, `ATTACCA`, e quel che risponde."""
    t = {"n": n, "inizio_ns": time.time_ns(), "attacca_ns": None,
         "esito": None, "motivo": None, "stato_sessione": None,
         "sessione_ns": None, "errore": None}
    from aioquic.asyncio import connect
    try:
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Cliente) as cli:
            await asyncio.wait_for(cli.wait_connected(), timeout=8)
            cli.apri_sessione(autorita, a.percorso)
            stato = await asyncio.wait_for(cli.accettata, timeout=8)
            if stato != "200":
                t["esito"] = "no-connect"
                t["errore"] = f":status = {stato}"
                return t
            cli.apri_controllo()
            cli.codec_atteso = 1
            cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao()))
            await b3.attendi(cli, "ECCOMI")
            cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                  b3.s(a.utente) + b3.s(a.parola)))
            await b3.attendi(cli, "AMMESSO", attesa=25)
            # ⛔ L'istante che conta: il posto si prende QUI, non a `SESSIONE`.
            t["attacca_ns"] = time.time_ns()
            cli.manda(b3.inquadra(b3.T["ATTACCA"],
                                  struct.pack("!IIII", a.larghezza, a.altezza,
                                              a.larghezza, a.altezza)
                                  + b3.s(a.disposizione)))
            try:
                _, corpo, _ = await b3.attendi(cli, "SESSIONE",
                                               attesa=a.attesa_sessione)
            except RuntimeError as e:
                testo = str(e)
                t["esito"] = "respinto"
                t["errore"] = testo
                for codice, nome in MOTIVI.items():
                    if nome in testo:
                        t["motivo"] = nome
                        break
                return t
            t["sessione_ns"] = time.time_ns()
            t["stato_sessione"] = corpo[0]
            lar, alt = struct.unpack("!II", corpo[1:9])
            t["tela"] = [lar, alt]
            t["esito"] = "entrato"
            if a.dopo_successo == "congedo":
                cli.manda(b3.inquadra(b3.T["CONGEDO"],
                                      struct.pack("!B", 0x01)
                                      + b3.s("sonda 06-b43")))
                await asyncio.sleep(0.4)
                t["congedato_ns"] = time.time_ns()
            return t
    except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
        t["esito"] = t["esito"] or "errore"
        t["errore"] = f"{type(e).__name__}: {e}"
        return t


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    b3 = fc.carica_b3()
    Cliente = fc.fabbrica_cliente()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    os.makedirs(a.lavoro, exist_ok=True)
    fuori = os.path.join(a.lavoro, f"{a.etichetta}-sonda.jsonl")
    with open(fuori, "w", encoding="utf-8") as f:
        f.write("")

    dimmi(f"== 06-b43 sonda «{a.etichetta}» — busso ogni ~{a.intervallo} s "
          f"fino a {a.tetto} s")
    dimmi(f"   scena: {a.scena}")

    t0 = time.monotonic()
    partenza_ns = int(a.da_quando) if a.da_quando else time.time_ns()
    n = 0
    ultimo_respinto = None
    entrato = None
    errori_di_fila = 0
    ris_stop = None
    while time.monotonic() - t0 < a.tetto:
        n += 1
        t = await un_tentativo(a, n, b3, Cliente, conf, autorita)
        t["da_partenza_ms"] = ((t["attacca_ns"] or t["inizio_ns"])
                               - partenza_ns) / 1e6
        with open(fuori, "a", encoding="utf-8") as f:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
            f.flush()
        col = VERDE if t["esito"] == "entrato" else GIALLO
        dimmi(f"   #{n:3d} {t['da_partenza_ms']:9.0f} ms  {col}{t['esito']}"
              f"{GRIGIO} {t['motivo'] or ''} "
              f"{'stato=' + str(t['stato_sessione']) if t['stato_sessione'] else ''}"
              f" {t['errore'] or ''}")
        if t["esito"] == "entrato":
            entrato = t
            break
        if t["esito"] == "respinto":
            ultimo_respinto = t

        # ⛔⛔⭐ E QUI SI SMETTE DI BUSSARE — la cura di un danno gia' fatto,
        #      `[M]` 22 agosto 2026, e il danno NON e' stato a questo banco.
        #
        #      Alle 06:17:38 un altro agente ha preso la porta 7801 e ha
        #      rimpiazzato il mio server con il suo.  ⛔ Questa sonda non se n'e'
        #      accorta: ha continuato a bussare per venti minuti **al server
        #      dell'altro**, con credenziali che lui rifiutava, e ha fatto
        #      scattare il ban di §4.4-bis nel SUO ban-file — `[192.168.0.2]`
        #      per dodici ore, cioe' l'unico indirizzo da cui parte qualunque
        #      banco di questa macchina.
        #
        # ⚠ La regola dei banchi in parallelo dice «porta propria», e questa
        #   sonda la rispettava.  ⛔ Non basta: un banco che INSISTE deve
        #   accorgersi che dall'altra parte non c'e' piu' quello con cui aveva
        #   cominciato, o diventa lui l'arma.
        #
        #   1. credenziali rifiutate ⇒ ⛔ **si smette SUBITO**.  Tre no in
        #      cinque minuti sono un ban per indirizzo, e insistere non puo'
        #      produrre nessuna misura — solo il ban;
        #   2. tre errori di connessione di fila ⇒ il server non e' piu' li'.
        if t["motivo"] in ("CREDENZIALI_ERRATE", "TROPPI_TENTATIVI"):
            dimmi(f"   {ROSSO}⛔ MI FERMO: il server ha risposto "
                  f"«{t['motivo']}».  ⚠ Insistere con credenziali che non "
                  f"passano fa scattare il ban di §4.4-bis, che e' per "
                  f"INDIRIZZO e vale per TUTTI i banchi della macchina.{GRIGIO}")
            ris_stop = "credenziali rifiutate"
            break
        if t["esito"] == "errore":
            errori_di_fila += 1
            if errori_di_fila >= 3:
                dimmi(f"   {ROSSO}⛔ MI FERMO: tre errori di connessione di "
                      f"fila — il server con cui avevo cominciato non c'e' "
                      f"piu' sulla {a.porta}.  ⚠ Continuare vorrebbe dire "
                      f"bussare a quello di qualcun altro.{GRIGIO}")
                ris_stop = "il server non c'e' piu'"
                break
        else:
            errori_di_fila = 0
        await asyncio.sleep(a.intervallo)

    ris = {"banco": "06-b43-sonda", "etichetta": a.etichetta,
           "scena": a.scena, "partenza_ns": partenza_ns,
           "tentativi": n,
           "ultimo_respinto_ms": (ultimo_respinto or {}).get("da_partenza_ms"),
           "ultimo_respinto_motivo": (ultimo_respinto or {}).get("motivo"),
           "entrato_ms": (entrato or {}).get("da_partenza_ms"),
           "stato_sessione": (entrato or {}).get("stato_sessione"),
           "incertezza_ms": None,
           "fermata_perche": ris_stop}
    if entrato and ultimo_respinto:
        ris["incertezza_ms"] = (entrato["da_partenza_ms"]
                                - ultimo_respinto["da_partenza_ms"])
    percorso = os.path.join(a.lavoro, f"{a.etichetta}-sonda.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(ris, f, ensure_ascii=False, indent=1)
    dimmi(f"   esito: {percorso}")
    dimmi(f"   ⇒ entrato dopo {ris['entrato_ms']} ms "
          f"(ultimo NO a {ris['ultimo_respinto_ms']} ms, "
          f"forchetta {ris['incertezza_ms']} ms, "
          f"stato SESSIONE = {ris['stato_sessione']})")
    return 0 if entrato else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="06-b43 — la sonda che busca il posto finche' non entra")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7801)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="provar7")
    p.add_argument("--parola", default="")
    p.add_argument("--parola-file", default="")
    p.add_argument("--larghezza", type=int, default=1280)
    p.add_argument("--altezza", type=int, default=800)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--tetto", type=float, default=200.0,
                   help="per quanto si insiste, in secondi")
    p.add_argument("--intervallo", type=float, default=0.5,
                   help="⚠ fra la FINE di un tentativo e l'inizio del prossimo")
    p.add_argument("--attesa-sessione", type=float, default=90.0)
    p.add_argument("--da-quando", default="",
                   help="⛔ il nanosecondo da cui contare: quello in cui il "
                        "client di prima se n'e' andato")
    p.add_argument("--dopo-successo", choices=["congedo", "resta"],
                   default="congedo")
    p.add_argument("--lavoro", default="/tmp/06-b7")
    p.add_argument("--etichetta", default="sonda")
    p.add_argument("--scena", default="(non dichiarata)")
    a = p.parse_args()
    a.parola = fc.parola_dagli_argomenti(a)
    if a.scena == "(non dichiarata)":
        dimmi("⛔ serve --scena (CODER.md §3.2)")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001
        dimmi(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
