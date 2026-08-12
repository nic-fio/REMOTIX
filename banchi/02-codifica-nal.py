#!/usr/bin/env python3
"""02-codifica-nal.py — la FORMA del flusso HEVC, letta sui byte.

    python3 02-codifica-nal.py --elenca   <file.hevc>
    python3 02-codifica-nal.py --verifica <file.hevc> [--idr-attesi N]
    python3 02-codifica-nal.py --storpia  <file.hevc> <modo> <uscita>
                               modi: senza-parametri | byte-girato | troncato

===========================================================================
⛔ PERCHE' ESISTE — la forma del flusso e' una DECISIONE, non un dettaglio

`VideoDecoder` del browser accetta **due formati alternativi ed esclusivi**, e
non sono intercambiabili (`web/rapporti/S2-decodifica.md` §3.5, `[S]` dalla
registrazione HEVC del W3C):

  **hevc**   — con una `description` (un `HEVCDecoderConfigurationRecord`,
               l'`hvcC`), e i NAL preceduti da un prefisso di **lunghezza**;
  **annexb** — senza `description`, e i NAL separati da **codici di inizio**
               `00 00 01`.  Qui il chunk `key` deve portare **anche tutti i
               parameter set** necessari a decodificarlo.

⭐ **F2.3 sceglie Annex-B senza `description`.**  Le ragioni stanno nel
rapporto (`fasi/rapporti/F2-3-codifica.md` §3); quel che riguarda questo file e'
la **conseguenza verificabile**: se si spedisce Annex-B, allora il primo chunk
deve contenere, in quest'ordine e prima di qualunque dato di figura,
**VPS (32), SPS (33), PPS (34)** e poi una figura **IDR (19 o 20)**.

⛔ E questo si controlla sui BYTE, non sull'etichetta che ci mettiamo noi.
Chromium fa esattamente la stessa cosa e non si fida della nostra etichetta:
`video_decoder.cc:206-214` chiama `media::mp4::HEVC::AnalyzeAnnexB()` dopo ogni
`configure()`/`flush()`, e se il chunk marcato `key` non contiene un IDR con i
suoi parameter set **rifiuta**, con un messaggio che nomina il nostro esatto
errore possibile: *«A key frame is required after configure() or flush(). If
you're using HEVC formatted H.265 you must fill out the description field»*
(`S2-decodifica.md` §3.6, `[R]`).

⇒ ⭐ Questo file e' **il pezzo di Chromium che possiamo eseguire a casa nostra**.
   Se sbagliamo forma, lo scopre qui invece che in fase 2.5, dove il sintomo
   sarebbe «la pagina resta nera» e la ricerca comincerebbe dal posto sbagliato.

===========================================================================
⛔ E LA META' CHE SI DIMENTICA: I PARAMETER SET DAVANTI A **OGNI** IDR

Un fotogramma solo li ha per forza.  Il guaio arriva quando gli IDR sono tanti
(fase 3) e i parameter set stanno **solo** in testa al flusso: un client che si
collega dopo, o che riparte da un `flush()`, riceve un IDR **nudo** e non
decodifica niente.  Il sintomo e' schermo nero **con i fotogrammi che
arrivano** — lo stesso sintomo che `codificatore.c` di v1 aveva gia' comprato
una volta, e per questo v1 vieta `AV_CODEC_FLAG_GLOBAL_HEADER` con un commento
a `src/codificatore.c:268-272`.

⇒ `--verifica --idr-attesi N` pretende **N gruppi VPS+SPS+PPS**, non uno.

===========================================================================
⛔ E `--storpia`: UN BANCO CHE NON HA MAI VISTO UN RIFIUTO NON SA VEDERLO

`REVIEWER.md` §1 punto 5 e `CODER.md` §3.10.  Un giro in cui tutto passa non
dimostra che il banco sappia bocciare: dimostra solo che non ha bocciato.  I
tre modi qui sotto sono i tre modi in cui un flusso puo' essere rotto **senza
smettere di sembrare un flusso**:

  `senza-parametri` — VPS/SPS/PPS tolti, l'IDR lasciato.  ⭐ E' il modo che
      corrisponde all'errore vero che stiamo cercando di non fare: e' cosa
      succede se un giorno qualcuno accendesse `GLOBAL_HEADER`.  Il
      decodificatore indipendente **deve** produrre **zero** fotogrammi;
  `byte-girato` — un byte del primo slice invertito.  Il decodificatore deve
      **protestare**, o consegnare pixel diversi dal sorgente;
  `troncato` — il flusso tagliato al 60 %.  Meno fotogrammi, o un errore.

⚠ Nessuno dei tre rompe la sintassi dei codici di inizio: se li rompesse, si
  starebbe provando che ffmpeg sa riconoscere un file che non e' un file, che
  non e' la stessa cosa e non serve a nessuno.
"""

import argparse
import json
import os
import sys

# I tipi di NAL che ci interessano (H.265, ISO/IEC 23008-2 tabella 7-1).
NOMI = {
    19: "IDR_W_RADL", 20: "IDR_N_LP", 21: "CRA_NUT",
    32: "VPS", 33: "SPS", 34: "PPS", 35: "AUD", 36: "EOS", 37: "EOB",
    38: "FD", 39: "PREFIX_SEI", 40: "SUFFIX_SEI",
    0: "TRAIL_N", 1: "TRAIL_R",
}
PARAMETRI = (32, 33, 34)
IDR = (19, 20)
VCL_MASSIMO = 31          # i tipi 0..31 sono dati di figura (VCL)


def trova_inizi(dati):
    """Gli offset dei codici di inizio Annex-B, e la loro lunghezza (3 o 4).

    ⛔ Si distingue `00 00 01` da `00 00 00 01`: sono tutti e due leciti, e un
       parser che ne conoscesse uno solo salterebbe meta' dei NAL **senza
       lamentarsi** — cioe' direbbe «questo flusso non ha il PPS» di un flusso
       che ce l'ha.  Un falso rosso costa quanto un falso verde.
    """
    inizi = []
    i, n = 0, len(dati)
    while i + 2 < n:
        if dati[i] == 0 and dati[i + 1] == 0 and dati[i + 2] == 1:
            if i >= 1 and dati[i - 1] == 0:
                inizi.append((i - 1, 4))   # 00 00 00 01
            else:
                inizi.append((i, 3))       # 00 00 01
            i += 3
        else:
            i += 1
    return inizi


def elenca(percorso):
    dati = open(percorso, "rb").read()
    if not dati:
        raise SystemExit(f"⛔ {percorso} e' vuoto: zero byte non e' un flusso")
    inizi = trova_inizi(dati)
    nal = []
    for k, (off, lungo) in enumerate(inizi):
        corpo = off + lungo
        fine = inizi[k + 1][0] if k + 1 < len(inizi) else len(dati)
        if corpo >= len(dati):
            continue
        tipo = (dati[corpo] >> 1) & 0x3F
        nal.append({"indice": k, "offset": off, "prefisso": lungo,
                    "tipo": tipo, "nome": NOMI.get(tipo, f"tipo{tipo}"),
                    "byte": fine - corpo})
    return {"file": os.path.basename(percorso), "byte_totali": len(dati),
            "nal": nal}


def verifica(percorso, idr_attesi):
    """⛔ La forma pretesa, e ogni pretesa dice PERCHE'."""
    e = elenca(percorso)
    nal = e["nal"]
    tipi = [n["tipo"] for n in nal]
    guasti = []

    if not nal:
        guasti.append("⛔ nessun NAL trovato: non e' un flusso Annex-B")

    # 1 — il primo NAL che non sia un delimitatore dev'essere il VPS
    utili = [t for t in tipi if t not in (35, 38)]      # senza AUD e riempimento
    if not utili or utili[0] != 32:
        guasti.append(f"⛔ il flusso non comincia con il VPS (32): comincia con {utili[:4]}")

    # 2 — prima del primo dato di figura devono esserci VPS, SPS, PPS
    prima = []
    for t in tipi:
        if t <= VCL_MASSIMO:
            break
        prima.append(t)
    for atteso in PARAMETRI:
        if atteso not in prima:
            guasti.append(f"⛔ manca il {NOMI[atteso]} ({atteso}) PRIMA del primo "
                          f"dato di figura: un chunk `key` in Annex-B deve portare "
                          f"tutti i parameter set (S2-decodifica.md §3.5)")

    # 3 — il primo dato di figura dev'essere un IDR
    vcl = [t for t in tipi if t <= VCL_MASSIMO]
    if not vcl:
        guasti.append("⛔ nessun dato di figura: il flusso non porta pixel")
    elif vcl[0] not in IDR:
        guasti.append(f"⛔ il PRIMO fotogramma non e' un fotogramma chiave: "
                      f"il primo NAL di figura e' {NOMI.get(vcl[0], vcl[0])}.  "
                      f"`VideoDecoder` dopo `configure()` pretende un chunk `key` "
                      f"o solleva DataError (S2-decodifica.md §3.6)")

    # 4 — i parameter set ripetuti davanti a OGNI IDR
    gruppi = 0
    visti = set()
    for t in tipi:
        if t in PARAMETRI:
            visti.add(t)
        elif t in IDR:
            if visti >= set(PARAMETRI):
                gruppi += 1
            visti = set()
    if gruppi < idr_attesi:
        guasti.append(f"⛔ i parameter set precedono {gruppi} IDR e ne dovevano "
                      f"precedere {idr_attesi}: un client che si collega dopo "
                      f"riceverebbe un IDR nudo (v1 src/codificatore.c:268-272)")

    # 5 — nessuna traccia di prefisso di lunghezza al posto del codice di inizio
    if len(dati_len := open(percorso, "rb").read(4)) == 4 and dati_len[:3] not in (
            b"\x00\x00\x00", b"\x00\x00\x01"):
        guasti.append("⛔ i primi byte non sono un codice di inizio: sembra un "
                      "flusso a prefisso di lunghezza (formato `hevc`/hvcC), non Annex-B")

    esito = {
        "file": e["file"], "byte_totali": e["byte_totali"],
        "nal_totali": len(nal),
        "sequenza": [n["nome"] for n in nal[:12]],
        "gruppi_parametri_prima_di_un_IDR": gruppi,
        "idr_attesi": idr_attesi,
        "primo_fotogramma_e_chiave": bool(vcl) and vcl[0] in IDR,
        "annexb": True,
        "va_bene": not guasti,
        "guasti": guasti,
    }
    print(json.dumps(esito, ensure_ascii=False, indent=2))
    return 0 if not guasti else 1


def confessione(percorso):
    """⭐ CHE COSA HA FATTO DAVVERO IL CODIFICATORE — chiesto a LUI, non dedotto.

    `CODER.md` §3.7: *non si deduce il mittente, lo si chiede.*  §3.9: *quando un
    componente puo' decidere da se', digli cosa fare — e VERIFICA CHE ABBIA
    OBBEDITO.*  E' la forma d'errore **E2** di `REVIEWER.md` §2, e in un
    codificatore e' quella di casa: *«il codificatore che ripiega in CPU senza
    dirlo»*.

    ⭐ Qui non serve dedurre niente, perche' **x265 scrive la propria confessione
       dentro il flusso**: un PREFIX_SEI di tipo 5 (user data unregistered) con
       la versione, la profondita' di bit e l'elenco COMPLETO delle opzioni che
       ha davvero usato — comprese quelle che nessuno ha chiesto.

    Le voci che questo banco legge, e perche':

      `bitdepth=10`     ⛔ la profondita' VERA con cui ha lavorato, detta da lui.
                           `ffprobe` la ricava dall'SPS, che e' un secondo
                           testimone: due testimoni indipendenti, non uno;
      `annexb`          ⭐ la FORMA del flusso, confermata dal produttore;
      `repeat-headers`  ⛔ i parameter set davanti a ogni IDR (la meta' che si
                           dimentica, e che morde in fase 3, non qui);
      `bframes=N`       ⚠ quel che NESSUNO ha chiesto e lui fa lo stesso.

    ⚠ E la dipendenza va dichiarata: questa confessione esiste perche' x265 ha
      `info=1` acceso di suo.  ⛔ Il banco lo tiene acceso **di proposito** — e'
      il suo strumento.  Se un giorno il prodotto lo spegnesse per risparmiare
      byte, questo controllo sparirebbe **in silenzio**: allora resterebbe il
      solo `ffprobe`, e va saputo prima invece che scoperto dopo.
    """
    dati = open(percorso, "rb").read()
    i = dati.find(b"x265 (build")
    if i < 0:
        return {"confessione": False,
                "perche": "nessun SEI di x265 nel flusso: o non l'ha fatto x265, "
                          "o `info=0`.  ⛔ Resta il solo ffprobe come testimone"}
    fine = dati.find(b"\x00", i)
    testo = dati[i:fine if fine > i else i + 4000].decode("ascii", "replace")
    voci = testo.split()
    def dammi(chiave):
        for v in voci:
            if v.startswith(chiave + "="):
                return v.split("=", 1)[1]
        return None
    return {
        "confessione": True,
        "versione": testo.split(" - ")[0],
        "banner_bit": "10bit" if "10bit" in testo.split("options:")[0] else "8bit",
        "bitdepth": dammi("bitdepth"),
        "input_csp": dammi("input-csp"),
        "annexb": " annexb" in testo,
        "repeat_headers": " repeat-headers" in testo,
        "bframes": dammi("bframes"),
        "keyint": dammi("keyint"),
        "lossless": " lossless" in testo,
        "byte_del_sei": (fine - i) if fine > i else None,
    }


def storpia(percorso, modo, uscita):
    dati = bytearray(open(percorso, "rb").read())
    e = elenca(percorso)
    nal = e["nal"]
    if not nal:
        raise SystemExit("⛔ non si storpia un flusso che non si e' saputo leggere")

    if modo == "senza-parametri":
        tenuti = bytearray()
        for k, n in enumerate(nal):
            if n["tipo"] in PARAMETRI:
                continue
            fine = nal[k + 1]["offset"] if k + 1 < len(nal) else len(dati)
            tenuti += dati[n["offset"]:fine]
        fuori = tenuti
        nota = "VPS/SPS/PPS tolti, i dati di figura lasciati"
    elif modo == "byte-girato":
        primo = next((n for n in nal if n["tipo"] <= VCL_MASSIMO), None)
        if primo is None:
            raise SystemExit("⛔ nessun dato di figura da storpiare")
        # ⛔ DOVE si gira il byte NON e' un dettaglio — misurato il 12 agosto 2026.
        #
        #    La prima stesura girava il byte 24 del NAL.  Su un fotogramma
        #    1920x1080 quel byte cade ancora dentro l'INTESTAZIONE dello slice, e
        #    ⛔ **il fotogramma decodificato e' tornato IDENTICO al sorgente, bit
        #    per bit**, con ffmpeg uscito 0.  Il controllo negativo non innestava
        #    nessun guasto: e' la trappola n.2 di `01-b12-guasti.py` — *«il guasto
        #    che non e' stato innestato lascia il codice sano, il banco resta
        #    verde, e chi legge conclude che il banco non vede il guasto»*.
        #
        #    ⭐ Girando lo stesso byte al **2 % del corpo** — cioe' nei dati
        #    entropici veri — i campioni diversi sono passati da **0 a 4 710 663
        #    su 6 220 800** `[M]`.  ⛔ E ffmpeg e' uscito **0 in tutti e due i
        #    casi**: lo stato d'uscita non distingueva le due cose.
        #
        #    ⇒ Si salta l'intestazione del NAL (2 byte) e si entra nel corpo per
        #      il 2 %, con un fondo di 64 byte per gli slice piccoli.
        corpo = primo["offset"] + primo["prefisso"] + 2
        dentro = max(64, primo["byte"] // 50)
        dove = min(corpo + dentro, primo["offset"] + primo["prefisso"] + primo["byte"] - 1)
        dati[dove] ^= 0xFF
        fuori = dati
        nota = (f"un byte invertito all'offset {dove}, al {100 * dentro / max(1, primo['byte']):.1f} % "
                f"del corpo del primo slice (lungo {primo['byte']} byte)")
    elif modo == "troncato":
        taglio = int(len(dati) * 0.60)
        fuori = dati[:taglio]
        nota = f"tagliato a {taglio} byte su {len(dati)} (60 %)"
    else:
        raise SystemExit(f"⛔ modo sconosciuto: {modo}")

    with open(uscita, "wb") as f:
        f.write(bytes(fuori))
    print(json.dumps({"modo": modo, "nota": nota, "uscita": uscita,
                      "byte": len(fuori)}, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--elenca")
    p.add_argument("--verifica")
    p.add_argument("--confessione")
    p.add_argument("--idr-attesi", type=int, default=1)
    p.add_argument("--storpia", nargs=3, metavar=("FILE", "MODO", "USCITA"))
    a = p.parse_args()
    if a.elenca:
        print(json.dumps(elenca(a.elenca), ensure_ascii=False, indent=2))
        return 0
    if a.confessione:
        c = confessione(a.confessione)
        print(json.dumps(c, ensure_ascii=False))
        return 0 if c.get("confessione") else 1
    if a.verifica:
        return verifica(a.verifica, a.idr_attesi)
    if a.storpia:
        return storpia(*a.storpia)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
