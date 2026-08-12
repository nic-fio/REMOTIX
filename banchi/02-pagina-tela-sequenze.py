#!/usr/bin/env python3
"""02-pagina-tela-sequenze.py — i flussi che CAMBIANO MISURA a meta' sessione.

    python3 banchi/02-pagina-tela-sequenze.py            costruisce
    python3 banchi/02-pagina-tela-sequenze.py --elenca   dice che cosa c'e'

===========================================================================
⛔ PERCHE' ESISTE — il buco che nessuna riga di `RCP.md` copre

`RCP.md` §6.2 e' stato corretto oggi (12 agosto 2026): `largh.` e `altezza` di
un fotogramma **DEVONO valere la tela IN VIGORE** — quella di `SESSIONE`
*oppure* l'ultima concessa da `TELA(ADATTATA…)` se nel frattempo §7.1 l'ha
adattata.  ⇒ **La misura dei fotogrammi puo' cambiare a meta' sessione**, ed e'
un cambiamento legale, chiesto dall'utente che trascina una finestra.

⛔ E qui si apre il buco: §5.2 impone che **il primo fotogramma dopo `SESSIONE`
   sia una chiave** — ma dopo un `TELA(ADATTATA)` il decodificatore del client
   **riparte da zero una seconda volta**, e *nessuna riga dice che il primo
   fotogramma alla misura nuova debba essere una chiave*.

⚠ E la riga NON si scrive per prudenza.  §5.2 esiste perche' *«senza questa
  riga un delta in apertura e' conforme, e il client non ha modo di
  accorgersene: non c'e' nessun buco nella successione dei `numero`, e il
  decodificatore non solleva errori»*.  ⛔ Quella frase e' un `[S]`: e' quel che
  ci si aspetta, non quel che si e' visto.  Se sul cambio di misura il
  decodificatore **solleva** un errore, il buco e' molto meno grave di come
  sembra e la riga costa piu' di quel che rende; se invece **dipinge spazzatura
  in silenzio**, e' la stessa forma di P6 di F2.5 — «zero» e «sono fallito» con
  lo stesso aspetto — e la riga va scritta.

⇒ Questo programma costruisce i flussi che permettono di **misurarlo**.

===========================================================================
⛔ CHE COSA COSTRUISCE, E PERCHE' PROPRIO QUESTI PEZZI

Due flussi per codec, a **due misure diverse e con due pattern diversi**:

    grande   640x480   pattern **A**    (la tela di `SESSIONE`)
    piccola  320x240   pattern **B**    (la tela dopo `ADATTA_TELA`)

⛔ I pattern sono DIVERSI di proposito.  Se i due flussi portassero le stesse
   tinte, «ha dipinto il fotogramma nuovo» e «ha continuato a mostrare il
   vecchio» avrebbero lo stesso aspetto — la forma **E2**, due comportamenti
   sotto la stessa etichetta.  Con due pattern, la pagina puo' classificare i
   pixel contro **tutt'e due** e dire quale dei due sta guardando.

⛔ E 320x240 non e' un numero a caso: e' la **tela minima** di `RCP.md` §4.5, e
   il verso grande->piccola e' quello dell'utente che stringe la finestra —
   cioe' la scena che §7.1 protegge con la sua eccezione 4.

Da ciascun flusso escono **tre elenchi di pezzi**, e le differenze sono la
misura:

  `pezzi`                tutte le unita' d'accesso, com'escono dal codificatore
                         (la prima porta VPS/SPS/PPS, o la sequence header OBU)
  `pezzi_senza_ps`       le stesse unita' **senza i parameter set**
                         ⇒ il decodificatore resta con l'SPS VECCHIO attivo, e
                           legge fette di 320x240 credendole di 640x480.
                           ⛔ E' QUESTA la condizione che il mandato nomina:
                           «la risoluzione cambia senza che arrivi una SPS
                           nuova»
  `pezzi_delta`          i soli fotogrammi **delta** (dal secondo in poi)
                         ⇒ e' il buco alla lettera: un delta alla misura nuova,
                           che oggi nessuna riga vieta

===========================================================================
⛔ IL CONTROLLO POSITIVO DI QUESTO PROGRAMMA, e non e' in coda

Tre cose si verificano **prima** di scrivere un solo JSON, perche' se cadono i
numeri della pagina misurerebbero un difetto di questo script:

 1. **lo spezzettatore e' reversibile**: rimettendo insieme le NALU (o le OBU)
    senza togliere niente si riottengono **gli stessi byte** del flusso.  ⛔ Un
    offset sbagliato non da' un errore: da' un flusso che il browser rifiuta,
    cioe' un `[M]` falso contro il browser (e' la stessa ragione per cui
    `spoglia_ivf()` di F2.5 esiste una volta sola);
 2. **togliere i parameter set cambia davvero qualcosa**: `pezzi_senza_ps[0]`
    DEVE essere piu' corto di `pezzi[0]`.  Un guasto che non si innesta e un
    guasto inefficace hanno lo stesso aspetto (F2.5, riquadro del 12 agosto);
 3. **sui delta non c'e' niente da togliere**: `pezzi_delta` non cambia se gli
    si tolgono i parameter set.  ⇒ Il caso «delta alla misura nuova» e per
    costruzione **gia'** un caso «senza parameter set», e va detto invece che
    dedotto.

===========================================================================
⚠ CHE COSA QUESTO PROGRAMMA NON PRETENDE DI ESSERE

Non e' la catena vera.  In fase 2 il flusso lo produrra' il codificatore del
server dopo un `ADATTA_TELA`, e un codificatore vero riparte con un IDR e con i
suoi parameter set — cioe' il **caso (c)**.  I casi (b) sono **casi di banco**,
fatti apposta per porre al decodificatore la domanda che la catena onesta non
pone: *e se il server NON lo facesse?*  ⛔ Perche' e' esattamente quel che oggi
`RCP.md` **non gli vieta**.

⚠ Le funzioni di lettura del flusso (NALU, unita' d'accesso, `profile_tier_level`,
stringa di codec) sono **importate** da `02-pagina-sequenze.py`, non ricopiate:
quel lettore ha gia' pagato in proprio la trappola dei byte di prevenzione
dell'emulazione, e una seconda copia sarebbe un secondo posto dove ricascarci.
"""
import base64
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
DOVE = QUI / "02-pagina-tela-sequenze"

# ⛔ Import da un file il cui nome comincia per cifra e porta trattini: non e'
#    importabile con `import`, e la strada e' `importlib`.  Il modulo non fa
#    niente all'import (tutto sta sotto `if __name__ == "__main__"`).
_spec = importlib.util.spec_from_file_location(
    "f25_sequenze", QUI / "02-pagina-sequenze.py")
F25 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F25)

RITMO = 30
QUANTI = 6            # 1 chiave + 5 delta, la stessa forma di F2.5

# Le due tele, e i due pattern.  ⛔ Vedi l'intestazione: pattern diversi o
# «dipinge il nuovo» e «tiene il vecchio» non si distinguono.
TELE = {
    "grande":  {"l": 640, "a": 480, "pattern": "A"},
    "piccola": {"l": 320, "a": 240, "pattern": "B"},
}

ALTEZZA_SFUMATURA_FRAZIONE = 8      # 1/8 dell'altezza, la striscia per l'occhio
COLONNE, RIGHE = 4, 2


def errore(testo, dettaglio=None):
    print(f"\n\033[1;31mNO\033[0m  {testo}", file=sys.stderr)
    if dettaglio:
        for r in str(dettaglio).splitlines():
            print(f"        {r}", file=sys.stderr)
    sys.exit(2)


def esegui(comando, entrata=None):
    """⛔ Nessun `2>/dev/null`, nessuno stato d'uscita buttato."""
    p = subprocess.run(comando, input=entrata, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return p.returncode, p.stdout, p.stderr


# ---------------------------------------------------------------------------
def disegna(larghezza, altezza, nome_pattern):
    """Le otto tinte in una griglia 4x2, a una misura qualunque.

    ⚠ Le tinte sono **le stesse** di F2.5 (importate, non ricopiate): il
      classificatore della pagina e' lo stesso, e due tabelle di tinte sarebbero
      due verita' sullo stesso banco."""
    ordine = F25.PATTERN[nome_pattern]
    dati = bytearray(larghezza * altezza * 3)
    sfumatura = altezza // ALTEZZA_SFUMATURA_FRAZIONE
    utile = altezza - sfumatura
    lc = larghezza // COLONNE
    ac = utile // RIGHE
    celle = []
    for indice, tinta in enumerate(ordine):
        nome, (r, g, b) = F25.TINTE[tinta]
        cx = (indice % COLONNE) * lc
        cy = (indice // COLONNE) * ac
        for y in range(cy, cy + ac):
            base = (y * larghezza + cx) * 3
            for x in range(lc):
                dati[base + x * 3] = r
                dati[base + x * 3 + 1] = g
                dati[base + x * 3 + 2] = b
        celle.append({"indice": indice, "tinta": nome, "rgb": [r, g, b],
                      "x": cx, "y": cy, "l": lc, "a": ac})
    for y in range(utile, altezza):
        base = y * larghezza * 3
        for x in range(larghezza):
            v = 16 + (x * 219) // (larghezza - 1)
            dati[base + x * 3] = v
            dati[base + x * 3 + 1] = v
            dati[base + x * 3 + 2] = v
    return bytes(dati), celle, utile


# ---------------------------------------------------------------------------
def codifica_hevc(grezzo, larghezza, altezza):
    """Main10, `keyint=6`, `bframes=0`, `repeat-headers=1`.

    ⛔ Le stesse opzioni di F2.5, e per le stesse ragioni gia' pagate: in
       tutto-intra x265 emette **Rext** invece di Main10, e un fotogramma B
       uscirebbe in un ordine diverso da quello di presentazione."""
    parametri = (f"keyint={QUANTI}:min-keyint={QUANTI}:scenecut=0"
                 ":repeat-headers=1:no-open-gop=1:bframes=0"
                 ":log-level=error:crf=16")
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{larghezza}x{altezza}", "-framerate", str(RITMO), "-i", "pipe:0",
        "-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-profile:v", "main10",
        "-x265-params", parametri,
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-f", "hevc", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=grezzo)
    if codice != 0 or not uscita:
        errore(f"libx265 non ha prodotto il flusso {larghezza}x{altezza}",
               errori.decode("utf-8", "replace"))
    return uscita


def codifica_av1(grezzo, larghezza, altezza):
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{larghezza}x{altezza}", "-framerate", str(RITMO), "-i", "pipe:0",
        "-c:v", "libaom-av1", "-pix_fmt", "yuv420p",
        "-g", str(QUANTI), "-keyint_min", str(QUANTI),
        "-crf", "20", "-b:v", "0", "-cpu-used", "8",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-f", "ivf", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=grezzo)
    if codice != 0 or len(uscita) < 32:
        errore(f"libaom-av1 non ha prodotto il flusso {larghezza}x{altezza}",
               errori.decode("utf-8", "replace"))
    return uscita


# ---------------------------------------------------------------------------
# ⛔ LE OBU DI AV1 — lo spezzettatore, e il suo controllo positivo.
#
# Un'OBU: primo byte = forbidden(1) tipo(4) extension_flag(1) has_size_field(1)
# reserved(1).  Se `extension_flag` c'e' un secondo byte; se `has_size_field`
# segue la lunghezza in leb128.  libaom in IVF scrive la forma «low overhead»,
# cioe' con la lunghezza.
#
# ⛔ E il tipo che conta qui e' **1 = OBU_SEQUENCE_HEADER**: e' il posto in cui
#    AV1 tiene la misura del fotogramma, cioe' l'equivalente esatto dell'SPS.
#    Toglierlo mette il decodificatore nella stessa condizione: misura nuova,
#    nessuna dichiarazione nuova.
OBU_SEQUENCE_HEADER = 1
OBU_TEMPORAL_DELIMITER = 2


def leggi_leb128(dati, i):
    valore, spostamento, letti = 0, 0, 0
    while i + letti < len(dati):
        b = dati[i + letti]
        valore |= (b & 0x7F) << spostamento
        letti += 1
        if not (b & 0x80):
            return valore, letti
        spostamento += 7
        if letti > 8:
            break
    errore("leb128 non terminato: lo spezzettatore delle OBU sbaglia offset")


def spezza_obu(dati):
    """→ elenco di (tipo, byte completi dell'OBU, intestazione compresa)."""
    fuori = []
    i = 0
    while i < len(dati):
        primo = dati[i]
        if primo & 0x80:
            errore("bit «forbidden» acceso in un'OBU: non e' un flusso AV1 "
                   "low-overhead, e lo spezzettatore starebbe leggendo rumore")
        tipo = (primo >> 3) & 0x0F
        estensione = (primo >> 2) & 1
        con_misura = (primo >> 1) & 1
        testa = 1 + (1 if estensione else 0)
        if not con_misura:
            errore("un'OBU senza `has_size_field`: in questa forma la lunghezza "
                   "e' implicita fino a fine flusso, e non si puo' spezzare")
        misura, letti = leggi_leb128(dati, i + testa)
        fine = i + testa + letti + misura
        if fine > len(dati):
            errore("un'OBU dichiara piu' byte di quanti ne restano: flusso "
                   "troncato o offset sbagliato")
        fuori.append((tipo, bytes(dati[i:fine])))
        i = fine
    return fuori


def spezza_ivf(uscita):
    """IVF → elenco di unita' temporali (i byte di un fotogramma)."""
    if uscita[:4] != b"DKIF":
        errore("il flusso non comincia con DKIF: non e' un IVF")
    tu = []
    i = 32
    while i + 12 <= len(uscita):
        lung = int.from_bytes(uscita[i:i + 4], "little")
        corpo = uscita[i + 12:i + 12 + lung]
        if len(corpo) != lung:
            errore("un fotogramma IVF e' troncato")
        tu.append(corpo)
        i += 12 + lung
    return tu


# ---------------------------------------------------------------------------
def pezzi_hevc(unita, senza_ps):
    """Le unita' d'accesso → pezzi Annex-B, con o senza i parameter set."""
    fuori = []
    for i, u in enumerate(unita):
        nalu = [x for x in u if F25.tipo_nalu(x) not in (32, 33, 34)] if senza_ps else u
        corpo = b"".join(b"\x00\x00\x00\x01" + x for x in nalu)
        fuori.append({
            "tipo": "key" if F25.e_chiave(u) else "delta",
            "istante": round(i * 1e6 / RITMO),
            "indice": i,
            "nalu": [F25.tipo_nalu(x) for x in nalu],
            "byte": len(corpo),
            "dati": base64.b64encode(corpo).decode(),
        })
    return fuori


def pezzi_av1(tu, senza_ps):
    fuori = []
    for i, corpo in enumerate(tu):
        obu = spezza_obu(corpo)
        if senza_ps:
            obu = [(t, b) for (t, b) in obu if t != OBU_SEQUENCE_HEADER]
        byte = b"".join(b for (_, b) in obu)
        fuori.append({
            "tipo": "key" if i == 0 else "delta",
            "istante": round(i * 1e6 / RITMO),
            "indice": i,
            "obu": [t for (t, _) in obu],
            "byte": len(byte),
            "dati": base64.b64encode(byte).decode(),
        })
    return fuori


# ---------------------------------------------------------------------------
def costruisci(famiglia, nome_tela):
    t = TELE[nome_tela]
    larghezza, altezza, pattern = t["l"], t["a"], t["pattern"]
    grezzo, celle, da_riga = disegna(larghezza, altezza, pattern)
    unico = grezzo * QUANTI

    if famiglia == "hevc":
        flusso = codifica_hevc(unico, larghezza, altezza)
        info = F25.sonda(flusso)
        nalu = F25.spezza_nalu(flusso)
        unita = F25.unita_daccesso(nalu)
        if len(unita) != QUANTI:
            errore(f"{famiglia}/{nome_tela}: {len(unita)} unita' d'accesso "
                   f"invece di {QUANTI}")
        # ⛔ CONTROLLO 1 — lo spezzettatore e' reversibile.
        rimesso = b"".join(b"\x00\x00\x00\x01" + x for u in unita for x in u)
        rifatto = F25.unita_daccesso(F25.spezza_nalu(rimesso))
        if [[bytes(x) for x in u] for u in rifatto] != [[bytes(x) for x in u] for u in unita]:
            errore("lo spezzettatore delle NALU non e' reversibile: un offset "
                   "sbagliato non da' un errore, da' un flusso che il browser "
                   "rifiuta — cioe' un [M] falso contro il browser")
        parametri = [u for u in unita[0] if F25.tipo_nalu(u) in (32, 33, 34)]
        if not parametri:
            errore("la prima unita' non porta VPS/SPS/PPS")
        if not F25.e_chiave(unita[0]):
            errore("la prima unita' non e' una chiave")
        sps = next(u for u in parametri if F25.tipo_nalu(u) == 33)
        ptl = F25.leggi_ptl(sps)
        codec, dettagli = F25.stringa_codec(info, ptl)
        pezzi = pezzi_hevc(unita, False)
        senza = pezzi_hevc(unita, True)
        pix = info.get("pix_fmt")
        profilo, livello = info.get("profile"), info.get("level")
        byte_flusso = len(flusso)
    elif famiglia == "av1":
        flusso = codifica_av1(unico, larghezza, altezza)
        info = F25.sonda_ivf(flusso)
        tu = spezza_ivf(flusso)
        if len(tu) != QUANTI:
            errore(f"{famiglia}/{nome_tela}: {len(tu)} unita' temporali "
                   f"invece di {QUANTI}")
        # ⛔ CONTROLLO 1 — reversibile anche qui.
        for corpo in tu:
            if b"".join(b for (_, b) in spezza_obu(corpo)) != corpo:
                errore("lo spezzettatore delle OBU non e' reversibile")
        tipi0 = [t for (t, _) in spezza_obu(tu[0])]
        if OBU_SEQUENCE_HEADER not in tipi0:
            errore(f"la prima unita' temporale non porta la sequence header "
                   f"(OBU trovate: {tipi0}): senza, non c'e' niente da togliere "
                   "e il caso «senza parameter set» non si costruisce")
        profili = {"Main": 0, "High": 1, "Professional": 2}
        p = profili.get(info.get("profile"), 0)
        lv = int(info.get("level") or 4)
        codec = f"av01.{p}.{lv:02d}M.08"
        dettagli = {"profilo": info.get("profile"), "seq_level_idx": lv}
        pezzi = pezzi_av1(tu, False)
        senza = pezzi_av1(tu, True)
        pix = info.get("pix_fmt")
        profilo, livello = info.get("profile"), info.get("level")
        byte_flusso = len(flusso)
    else:
        errore(f"famiglia sconosciuta: {famiglia}")

    # ⛔ CONTROLLO 2 — togliere i parameter set cambia DAVVERO qualcosa.
    if senza[0]["byte"] >= pezzi[0]["byte"]:
        errore(f"{famiglia}/{nome_tela}: togliendo i parameter set il primo "
               f"pezzo non si accorcia ({pezzi[0]['byte']} → "
               f"{senza[0]['byte']} byte).  Il guasto non si e' innestato, e un "
               "guasto non innestato e uno inefficace hanno lo stesso aspetto")

    # ⛔ CONTROLLO 3 — sui delta non c'e' niente da togliere, e si DICE.
    delta_uguali = all(pezzi[i]["dati"] == senza[i]["dati"]
                       for i in range(1, len(pezzi)))
    if not delta_uguali:
        errore(f"{famiglia}/{nome_tela}: un fotogramma DELTA portava dei "
               "parameter set.  Allora «delta alla misura nuova» e «senza "
               "parameter set» sono due casi diversi, e il banco ne misura uno "
               "solo credendo di misurarne due")

    return {
        "nome": f"tela-{famiglia}-{nome_tela}",
        "famiglia": famiglia,
        "tela": nome_tela,
        "pattern": pattern,
        "larghezza": larghezza,
        "altezza": altezza,
        "ritmo": RITMO,
        "fotogrammi": QUANTI,
        "codec": codec,
        "codec_dettagli": dettagli,
        "pix_fmt": pix,
        "profilo_ffprobe": profilo,
        "livello_ffprobe": livello,
        "byte_flusso": byte_flusso,
        "celle": celle,
        "tinte": [{"nome": n, "rgb": list(c)} for n, c in F25.TINTE],
        "sfumatura_da_y": da_riga,
        "pezzi": pezzi,
        "pezzi_senza_ps": senza,
        # ⛔ I soli delta: e' il buco alla lettera — un fotogramma delta alla
        #    misura nuova, che oggi `RCP.md` non vieta.  Che siano gia' «senza
        #    parameter set» e' il CONTROLLO 3, verificato qui sopra.
        "pezzi_delta": pezzi[1:],
        "delta_gia_senza_ps": delta_uguali,
        # I 28 byte di `RCP.md` §6.2, con la misura di QUESTA tela dentro:
        # servono a mostrare che il protocollo il cambio di misura lo DICE —
        # ed e' proprio per questo che il buco riguarda il **tipo**, non la
        # misura.  ⚠ Non entrano in nessun verdetto di questo banco.
        "intestazioni_rcp": [
            base64.b64encode(F25.intestazione_rcp(
                p["tipo"] == "key", p["indice"] + 1, p["istante"],
                larghezza, altezza)).decode() for p in pezzi
        ],
    }


# ---------------------------------------------------------------------------
def principale():
    if "--elenca" in sys.argv:
        if not DOVE.is_dir():
            print(f"⛔ {DOVE} non esiste: le sequenze non sono mai state costruite")
            return 1
        trovate = sorted(DOVE.glob("*.json"))
        print(f"-- {len(trovate)} sequenze in {DOVE}")
        for f in trovate:
            d = json.loads(f.read_text())
            print(f"   {d['nome']:26s} {d['larghezza']}x{d['altezza']:<5d} "
                  f"pattern {d['pattern']}  {d['codec']:20s} "
                  f"{len(d['pezzi'])} pezzi · "
                  f"primo {d['pezzi'][0]['byte']} byte → senza ps "
                  f"{d['pezzi_senza_ps'][0]['byte']}")
        return 0 if len(trovate) == 4 else 1

    for attrezzo in ("ffmpeg", "ffprobe"):
        if not shutil.which(attrezzo):
            errore(f"{attrezzo} non c'e': senza, non si costruisce niente")
    codice, uscita, errori = esegui(["ffmpeg", "-hide_banner", "-encoders"])
    if codice != 0:
        errore("`ffmpeg -encoders` e' fallito", errori.decode("utf-8", "replace"))
    for nome in (b"libx265", b"libaom-av1"):
        if nome not in uscita:
            errore(f"questo ffmpeg non ha {nome.decode()}: e i due codec vanno "
                   "misurati TUTT'E DUE — se si comportassero diversamente, "
                   "quella e' la scoperta")

    DOVE.mkdir(exist_ok=True)
    fatte = []
    for famiglia in ("hevc", "av1"):
        for nome_tela in ("grande", "piccola"):
            d = costruisci(famiglia, nome_tela)
            (DOVE / f"{d['nome']}.json").write_text(
                json.dumps(d, ensure_ascii=False), encoding="utf-8")
            fatte.append(d)
            print(f"   \033[1;32mOK\033[0m  {d['nome']:26s} "
                  f"{d['larghezza']}x{d['altezza']:<5d} pattern {d['pattern']}  "
                  f"{d['codec']:20s} {d['byte_flusso']:7d} byte  "
                  f"primo pezzo {d['pezzi'][0]['byte']:6d} → senza ps "
                  f"{d['pezzi_senza_ps'][0]['byte']:6d}")

    # ⛔ Il controllo positivo in coda: le due tele DEVONO avere misure diverse
    #    e pattern diversi, o tutte le prove di questo banco misurerebbero un
    #    cambio di misura che non c'e' stato.
    print()
    for famiglia in ("hevc", "av1"):
        g = next(d for d in fatte if d["famiglia"] == famiglia and d["tela"] == "grande")
        p = next(d for d in fatte if d["famiglia"] == famiglia and d["tela"] == "piccola")
        if (g["larghezza"], g["altezza"]) == (p["larghezza"], p["altezza"]):
            errore(f"{famiglia}: le due tele hanno la stessa misura")
        if g["pattern"] == p["pattern"]:
            errore(f"{famiglia}: le due tele hanno lo stesso pattern, e «ha "
                   "dipinto il nuovo» non si distinguerebbe da «tiene il vecchio»")
        print(f"    \033[1;32mOK\033[0m  {famiglia}: "
              f"{g['larghezza']}x{g['altezza']} pattern {g['pattern']}  →  "
              f"{p['larghezza']}x{p['altezza']} pattern {p['pattern']}  "
              f"· codec «{g['codec']}» → «{p['codec']}»")
    print(f"    -- {len(fatte)} sequenze in {DOVE}")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
