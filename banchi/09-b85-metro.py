#!/usr/bin/env python3
"""09-b85-metro.py — il metro dello sfalso audio-video, e la sua TARATURA.

    # 1. la taratura: contro sfalsi che io stesso ho messo
    python3 09-b85-metro.py --tara --dove ./gen

    # 2. la misura sul prodotto: quel che il CLIENTE ha preso dal filo
    python3 09-b85-metro.py --presa --video v.h264 --tempi v-tempi.jsonl \
                            --audio a.jsonl

⛔⛔ PERCHE' LA TARATURA VIENE PRIMA, E NON E' UNA FORMALITA'.

  `fasi/09` §16.4 porta **+331 ms a riposo** e **+690 ms sotto carico**, e
  dichiara che il numero **non e' mai stato messo alla prova**: il banco e'
  stato l'occhio dell'utente su un video di **pura grana**, e la risposta e'
  stata *«non posso sapere se c'e' disallineamento se il video e'
  incomprensibile»*.  ⇒ Un metro che non e' stato tarato non misura: dichiara.
  Qui si inietta uno sfalso NOTO (`-itsoffset`) e si pretende di ritrovarlo,
  col segno giusto e dentro un errore scritto.  ⛔ Se non si ritrova, ci si
  ferma li' — e quello e' gia' il risultato.

---------------------------------------------------------------------------
⭐ IL SEGNO, UNA VOLTA SOLA

    sfalso = t_click - t_lampo          [ms]

positivo = **il suono esce DOPO l'immagine** (l'audio e' indietro).  E' la
convenzione di `src/pagina.html:6398` (*«`AV = aoff - voff`.  Positivo = il
suono esce DOPO l'immagine»*) e si tiene identica per non aprire una seconda
convenzione dentro la stessa fase.

⛔⛔ E QUI C'E' UNA CONTRADDIZIONE NEL DOCUMENTO, CHE VA DETTA E NON EREDITATA:
    `fasi/09` §16.4 legge il **+331** come *«il suono PRECEDE l'immagine»*,
    mentre il codice che produce quel numero dice l'opposto.  ⇒ Uno dei due e'
    sbagliato, e finche' non si sa quale il **segno** di §16.4 non e'
    utilizzabile.  Questo metro non eredita: misura il segno da se', su uno
    sfalso che conosce.

---------------------------------------------------------------------------
⚠ L'ERRORE DEL METRO, DICHIARATO PRIMA DI MISURARE

  1. ⛔ **il fotogramma vale 25 ms**.  Il prodotto cattura a 40 fotogrammi al
     secondo e **non e' agganciato alla sorgente**: l'attacco del lampo cade in
     un punto qualunque fra due catture, e la prima cattura che lo vede e' in
     ritardo di una quantita' **uniforme in [0, 25) ms**.  ⇒ Sotto i 25 ms
     questo metro **non puo' dire niente su una singola claquette**;
  2. ⭐ **ma trenta claquette non sono una**.  La fase della cattura rispetto
     alla sorgente **deriva** (40 e 60 non sono agganciati), quindi su N
     attacchi il termine casuale scende come `25/sqrt(12·N)` — a N=30 vale
     **1,3 ms** — e resta un **bias sistematico di +12,5 ms** (la media di una
     uniforme in [0,25)).  ⛔ Il bias NON si sottrae per fede: la taratura lo
     **misura**, perche' su uno sfalso noto e' l'unica cosa che resta;
  3. ⚠ **l'audio non ha quantizzazione degna di nota**: a PCM il blocco e' 5 ms
     (§5.3) e l'attacco si trova **al campione**, cioe' a 1/48 000 di secondo.
     ⇒ Tutto l'errore di questo metro sta nel video, ed e' un bene: e' il lato
     che si puo' scrivere in una riga.

---------------------------------------------------------------------------
⛔ PERCHE' PCM E NON OPUS, e il prezzo si paga in chiaro

  Nel repo **non esiste nessun decodificatore Opus** — `07-b42-giudice.py`:121
  lo dichiara scelto: *«i pacchetti Opus li giudica il BROWSER, che ha il
  decodificatore: qui si giudicherebbe con uno diverso da quello dell'utente
  (forma d'errore E10)»*.  `09-b77` fa la stessa cosa e forza `--audio-codec
  pcm`.  ⇒ Qui si forza PCM, e ⚠ **il percorso dell'utente vero e' Opus**: il
  numero misurato non contiene il ritardo del codificatore/decodificatore Opus,
  e questo va scritto accanto al numero invece che dimenticato.
"""
import argparse
import base64
import json
import math
import os
import re
import struct
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import importlib.util as _iu


def _carica(nome, file_):
    """Il pattern di `09-b77`:128 — si carica per percorso, i banchi non sono
       un pacchetto."""
    sp = _iu.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


CLA = _carica("b85cla", "09-b85-claquette.py")

FS = 48000
CANALI = 2
# ⛔ Le soglie sono FRAZIONI DEL PICCO MISURATO, mai valori assoluti: il
#    prodotto ricodifica il video e riscala l'audio, e una soglia assoluta
#    tarata sul file sorgente troverebbe zero attacchi sulla presa — cioe' il
#    rosso muto, che e' peggio del rosso.
SOGLIA_LAMPO = 0.45      # frazione del picco di luminanza del riquadro
SOGLIA_CLICK = 0.25      # frazione del picco d'inviluppo dell'audio


# ═══════════════════════════════════════════════════════════════════════════
#  Gli attacchi: due funzioni, e sono le UNICHE due che decidono un istante
# ═══════════════════════════════════════════════════════════════════════════

def attacchi(serie, soglia_frazione, riarmo):
    """`serie` = [(t_secondi, valore)] ordinata.  Torna i `t` degli ATTACCHI.

    ⛔ Un attacco e' una salita sopra la soglia dopo essere stati sotto, e il
       `riarmo` impedisce che la stessa claquette ne produca due.  ⚠ Senza
       riarmo un lampo lungo 4 fotogrammi darebbe 4 attacchi sul file e 3 sulla
       presa, e il conto dei due lati non tornerebbe **per un difetto del
       metro** — che e' esattamente il modo in cui §16.4 e' finita dov'e'.
    """
    if not serie:
        return []
    picco = max(v for _, v in serie)
    if picco <= 0:
        return []
    s = picco * soglia_frazione
    fuori, sopra, ultimo = [], False, None
    for t, v in serie:
        if not sopra and v >= s:
            if ultimo is None or t - ultimo >= riarmo:
                fuori.append(t)
                ultimo = t
            sopra = True
        elif sopra and v < s * 0.8:      # isteresi: non si ridiscende sul filo
            sopra = False
    return fuori


def appaia(lampi, click, tolleranza=1.2):
    """Appaia ogni lampo col click piu' vicino, e torna gli sfalsi in ms.

    ⛔ E RIFIUTA di appaiare oltre `tolleranza` secondi: il periodo e' 2 s, e
       un appaiamento che scavalca di un periodo darebbe uno sfalso di
       ±2000 ms con la faccia di una misura.  ⚠ Un attacco spaiato non e' un
       errore: e' un attacco che manca da un lato, e si conta.
    """
    fuori, spaiati = [], 0
    for tl in lampi:
        if not click:
            spaiati += 1
            continue
        tc = min(click, key=lambda x: abs(x - tl))
        if abs(tc - tl) > tolleranza:
            spaiati += 1
            continue
        fuori.append((tl, (tc - tl) * 1000.0))
    return fuori, spaiati


def statistica(sfalsi_ms):
    """Mediana, media, e la DISPERSIONE.  ⛔ La dispersione si stampa sempre:
       una media senza dispersione non dice se il metro ha visto una cosa sola
       o trenta cose diverse (`CODER.md` §3.10)."""
    if not sfalsi_ms:
        return {"n": 0}
    v = sorted(sfalsi_ms)
    n = len(v)
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0
    mu = sum(v) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in v) / n) if n > 1 else 0.0
    return {"n": n, "mediana_ms": round(med, 1), "media_ms": round(mu, 1),
            "scarto_ms": round(sd, 1), "min_ms": round(v[0], 1),
            "max_ms": round(v[-1], 1)}


# ═══════════════════════════════════════════════════════════════════════════
#  IL LATO A: leggere un FILE (serve alla taratura, non al prodotto)
# ═══════════════════════════════════════════════════════════════════════════

R_META = re.compile(r"pts_time:([0-9.]+)")
R_YAVG = re.compile(r"lavfi\.signalstats\.YAVG=([0-9.]+)")


def luminanza_dal_file(percorso):
    """[(pts_secondi, luminanza media del riquadro del lampo)].

    ⛔ `-copyts`: senza, ffmpeg normalizza i tempi d'ingresso e la normalizzazione
       va applicata **identica** ai due flussi o lo sfalso misurato non e' piu'
       quello messo.  Con `-copyts` si leggono i tempi del contenitore, e
       l'audio si legge con lo stesso flag.
    """
    vf = (f"crop={CLA.LAMPO_L}:{CLA.LAMPO_A}:{CLA.LAMPO_X}:{CLA.LAMPO_Y},"
          f"scale=8:8:flags=area,signalstats,"
          f"metadata=print:key=lavfi.signalstats.YAVG:file=-")
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-copyts",
                        "-i", percorso, "-vf", vf, "-f", "null", "-"],
                       capture_output=True, text=True)
    fuori, t = [], None
    for riga in p.stdout.splitlines():
        m = R_META.search(riga)
        if m:
            t = float(m.group(1))
            continue
        m = R_YAVG.search(riga)
        if m and t is not None:
            fuori.append((t, float(m.group(1))))
            t = None
    return fuori


def inviluppo_dal_file(percorso, passo_ms=1.0):
    """[(pts_secondi, inviluppo)] dell'audio del file, a passo `passo_ms`."""
    t0 = 0.0
    q = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "packet=pts_time", "-read_intervals",
                        "%+#1", "-of", "csv=p=0", percorso],
                       capture_output=True, text=True)
    for riga in q.stdout.split():
        try:
            t0 = float(riga)
            break
        except ValueError:
            pass
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-copyts",
                        "-i", percorso, "-map", "0:a", "-ac", "1",
                        "-ar", str(FS), "-f", "s16le", "-"],
                       capture_output=True)
    return _inviluppo(p.stdout, t0, passo_ms)


def _inviluppo(pcm_s16le_mono, t0, passo_ms):
    """⛔ L'inviluppo e' il MASSIMO ASSOLUTO su una finestra, non l'RMS: la
       raffica dura 40 ms e la finestra 1 ms, e il massimo attacca **subito**
       mentre l'RMS sale lento.  Con l'RMS l'attacco misurato slitterebbe di
       qualche millisecondo **in modo diverso sui due lati**, che e' il difetto
       che una taratura non vedrebbe (sul file e sulla presa slitta uguale)."""
    n = len(pcm_s16le_mono) // 2
    passo = max(1, int(FS * passo_ms / 1000.0))
    v = memoryview(pcm_s16le_mono)[: n * 2]
    campioni = struct.unpack(f"<{n}h", v)
    fuori = []
    for i in range(0, n - passo, passo):
        fuori.append((t0 + i / FS, max(abs(x) for x in campioni[i:i + passo])))
    return fuori


def misura_file(percorso):
    lum = luminanza_dal_file(percorso)
    inv = inviluppo_dal_file(percorso)
    lampi = attacchi(lum, SOGLIA_LAMPO, riarmo=CLA.PERIODO_S * 0.5)
    click = attacchi(inv, SOGLIA_CLICK, riarmo=CLA.PERIODO_S * 0.5)
    coppie, spaiati = appaia(lampi, click)
    st = statistica([d for _, d in coppie])
    st.update({"lampi": len(lampi), "click": len(click), "spaiati": spaiati,
               "fotogrammi": len(lum)})
    return st


# ═══════════════════════════════════════════════════════════════════════════
#  IL LATO B: leggere la PRESA del cliente — video dal filo + audio dal filo
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ E QUI STA IL MOTIVO PER CUI QUESTA MISURA E' OGGETTIVA E NON HA BISOGNO
#     NE' DELL'OCCHIO NE' DEL BROWSER.
#
#  `RCP.md` §6.2: l'`istante` del fotogramma sono «microsecondi dell'orologio
#  **monotono del server** alla cattura».
#  `RCP.md` §6.3: l'`istante` del blocco audio sono «microsecondi dell'orologio
#  **monotono del server**, del **primo** campione del blocco».
#  ⇒ ⭐ **E' LO STESSO OROLOGIO.**  Sottraendo i due istanti dello stesso
#    evento reale, lo scarto fra l'orologio del server e qualunque altro
#    **si elide**, esattamente come si elide dentro `AV` nella pagina.
#
# ⛔ E MISURA UNA COSA PRECISA, che NON e' tutto quel che l'utente sente:
#
#    sfalso_utente  =  sfalso_alla_SORGENTE  +  sfalso_del_PERCORSO
#                      └─ questo file ─┘        └─ `AV` della pagina ─┘
#
#    Il primo e' l'errore con cui il SERVER marca i due flussi (cattura, coda,
#    codifica): se il server scrive sul fotogramma l'ora in cui l'ha *spedito*
#    invece di quella in cui l'ha *catturato*, e sull'audio l'ora giusta, i due
#    flussi sono gia' sfalsati **prima di uscire dalla macchina**, e nessun
#    lettore puo' rimetterli a posto.
#    Il secondo e' quel che succede DOPO — rete, coda del decodificatore,
#    cuscino dell'audio — e lo misura `AV`, che ha bisogno del browser.
#
# ⇒ ⚠ Questo file chiude la META' che il muro di Firefox lascia aperta, e
#   **lo dichiara**: non pretende di aver misurato il +690 di §16.4.


def video_dalla_presa(h264, tempi_jsonl):
    """[(istante_server_secondi, luminanza del riquadro)] per ogni fotogramma.

    `tempi_jsonl` lo scrive `09-b85-cliente.py`: una riga per fotogramma, con
    `numero` e `istante` (us, orologio del server), NELL'ORDINE IN CUI
    `--video-scrivi` li ha messi nel file — cioe' ordinati per `numero`.

    ⛔ E SI PRETENDE CHE I DUE CONTI COINCIDANO.  Se il decodificatore rende
       piu' o meno fotogrammi di quanti ce ne sono nella lista, l'appaiamento
       fotogramma↔istante **scivola**, e uno scivolamento di k fotogrammi e'
       uno sfalso finto di 25·k ms.  ⚠ E' la forma d'errore peggiore: un
       numero plausibile.  ⇒ Qui non si indovina, ci si rifiuta.
    """
    ist = []
    with open(tempi_jsonl) as f:
        for r in f:
            r = r.strip()
            if not r:
                continue
            d = json.loads(r)
            if d.get("che") != "video":
                continue
            ist.append((d["numero"], d["istante"]))
    ist.sort(key=lambda x: x[0])
    vf = (f"crop={CLA.LAMPO_L}:{CLA.LAMPO_A}:{CLA.LAMPO_X}:{CLA.LAMPO_Y},"
          f"scale=8:8:flags=area,signalstats,"
          f"metadata=print:key=lavfi.signalstats.YAVG:file=-")
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-f", "h264", "-i", h264, "-vf", vf,
                        "-vsync", "passthrough", "-f", "null", "-"],
                       capture_output=True, text=True)
    y = [float(m.group(1)) for m in R_YAVG.finditer(p.stdout)]
    if len(y) != len(ist):
        return None, (f"⛔ il decodificatore ha reso {len(y)} fotogrammi e la "
                      f"lista ne porta {len(ist)}: NON appaio.  Uno "
                      f"scivolamento di un fotogramma sarebbe uno sfalso finto "
                      f"di 25 ms, e non si distinguerebbe da una misura")
    return [(u / 1e6, v) for (_, u), v in zip(ist, y)], None


def audio_dalla_presa(jsonl, passo_ms=1.0):
    """[(istante_server_secondi, inviluppo)] dell'audio PCM preso dal filo.

    ⛔ SOLO PCM (`codec == 2`), come `09-b77`:644 — e per la stessa ragione:
       nel repo non c'e' nessun decodificatore Opus, e giudicare con uno
       diverso da quello dell'utente e' la forma d'errore E10.

    ⭐ E la linea del tempo si costruisce sull'`istante` del server, non
       sull'ordine d'arrivo: un blocco che arriva fuori sequenza va **al suo
       posto**, e un blocco perduto lascia **silenzio** invece di accorciare la
       linea.  ⚠ Un buco che accorciasse la linea sposterebbe tutti gli
       attacchi successivi: il difetto arriverebbe **come uno sfalso che cresce
       con la perdita**, cioe' come la conclusione che questo banco esiste per
       verificare.  Sarebbe il modo perfetto di confermarsi da soli.
    """
    blocchi = []
    with open(jsonl) as f:
        for r in f:
            r = r.strip()
            if not r:
                continue
            d = json.loads(r)
            if d.get("codec") != 2:
                continue
            blocchi.append((d["istante"], base64.b64decode(d["byte"])))
    if len(blocchi) < 50:
        return None, f"⛔ solo {len(blocchi)} blocchi PCM: non misuro"
    base = min(i for i, _ in blocchi)
    fine = max(i for i, _ in blocchi)
    n_tot = int(round((fine - base) / 1e6 * FS)) + FS * 5 // 1000
    if n_tot <= 0 or n_tot > FS * 3600:
        return None, f"⛔ linea del tempo assurda ({n_tot} campioni)"
    tela = bytearray(n_tot * 2)          # s16le mono, silenzio dov'e' buco
    for ist, b in blocchi:
        off = int(round((ist - base) / 1e6 * FS))
        n = len(b) // (2 * CANALI)
        if n <= 0 or off < 0 or off + n > n_tot:
            continue
        v = struct.unpack(f"<{n * CANALI}h", b[:n * CANALI * 2])
        struct.pack_into(f"<{n}h", tela, off * 2, *v[0::CANALI])
    inv = _inviluppo(bytes(tela), base / 1e6, passo_ms)
    return inv, None


def misura_presa(h264, tempi, audio_jsonl):
    lum, guasto = video_dalla_presa(h264, tempi)
    if guasto:
        return {"guasto": guasto}
    inv, guasto = audio_dalla_presa(audio_jsonl)
    if guasto:
        return {"guasto": guasto}
    lampi = attacchi(lum, SOGLIA_LAMPO, riarmo=CLA.PERIODO_S * 0.5)
    click = attacchi(inv, SOGLIA_CLICK, riarmo=CLA.PERIODO_S * 0.5)
    coppie, spaiati = appaia(lampi, click)
    st = statistica([d for _, d in coppie])
    st.update({"lampi": len(lampi), "click": len(click), "spaiati": spaiati,
               "fotogrammi": len(lum),
               "durata_video_s": round(lum[-1][0] - lum[0][0], 2) if lum else 0,
               "durata_audio_s": round(inv[-1][0] - inv[0][0], 2) if inv else 0})
    return st


# ═══════════════════════════════════════════════════════════════════════════
#  LA TARATURA
# ═══════════════════════════════════════════════════════════════════════════

R_NOME = re.compile(r"09-b85-claquette-\w+-([pm])(\d+)\.mp4$")


def tara(dove, tolleranza_ms=15.0):
    """⛔ IL CANCELLO.  Torna 0 se il metro ritrova ogni sfalso noto, 3 se no.

    ⚠ `tolleranza_ms = 15` non e' una scelta comoda: e' **sotto** il
      fotogramma di cattura del prodotto (25 ms).  Un metro che sbagliasse di
      piu' di mezzo fotogramma **sul file**, dove non c'e' nessuna cattura a
      40/s di mezzo, sarebbe un metro rotto e basta.
    """
    file_ = sorted(x for x in os.listdir(dove) if R_NOME.search(x))
    if not file_:
        print(f"   ⛔ in «{dove}» non c'e' nessun `09-b85-claquette-*.mp4`")
        return 2
    print(f"\n   ⭐ LA TARATURA — {len(file_)} sfalsi NOTI, ritrovati o no\n")
    print("   | messo   | ritrovato | errore  | n  | scarto | lampi/click | esito |")
    print("   |---------|-----------|---------|----|--------|-------------|-------|")
    rosso = 0
    for nome in file_:
        m = R_NOME.search(nome)
        messo = int(m.group(2)) * (1 if m.group(1) == "p" else -1)
        st = misura_file(os.path.join(dove, nome))
        if not st.get("n"):
            print(f"   | {messo:+6d}  | ⛔ NIENTE | – | 0 | – | "
                  f"{st.get('lampi')}/{st.get('click')} | ⛔ MUTO |")
            rosso += 1
            continue
        err = st["mediana_ms"] - messo
        ok = abs(err) <= tolleranza_ms
        rosso += 0 if ok else 1
        print(f"   | {messo:+6d}  | {st['mediana_ms']:+8.1f}  | {err:+6.1f}  | "
              f"{st['n']:2d} | {st['scarto_ms']:5.1f}  | "
              f"{st['lampi']:2d}/{st['click']:2d}       | "
              f"{'✅' if ok else '⛔ ROSSO'} |")
    print()
    if rosso:
        print(f"   ⛔⛔ {rosso} sfalsi noti NON ritrovati dentro ±{tolleranza_ms:.0f} ms.")
        print("       ⇒ IL METRO NON MISURA.  Non c'e' niente da misurare sul")
        print("         prodotto, e questo e' gia' il risultato (§16.4).")
        return 3
    print(f"   ✅ tutti gli sfalsi noti ritrovati dentro ±{tolleranza_ms:.0f} ms, "
          f"col segno giusto.")
    return 0


def finge_cattura(sorgente, fuori, fps=40, fase_s=0.0, crf=23):
    """⭐⭐ IL SECONDO GRADINO DELLA TARATURA, e senza di lui la prima tabella
       certifica un metro che il prodotto non usera' mai.

    Sul file la sorgente e la misura hanno **gli stessi fotogrammi**: il metro
    esce a zero errore perche' non c'e' niente da sbagliare.  ⛔ Il prodotto
    invece **ricampiona**: cattura a 40/s da una sorgente a 60/s, con una fase
    qualunque, e ricodifica.  ⇒ Qui si rifa' quella cosa a mano, su un file di
    cui **conosco ancora lo sfalso**, e si guarda se il metro lo ritrova.

    ⚠ Quel che deve uscire NON e' zero: e' `+12,5 ms`, cioe' la media della
      uniforme in [0, 25) ms con cui la prima cattura vede un attacco.  ⭐ Se
      esce 12,5 il modello dell'errore e' giusto ed e' **misurato**; se esce
      altro, e' il modello a essere sbagliato e va riscritto prima di toccare
      il prodotto.
    """
    vf = f"fps=fps={fps}:start_time={fase_s:.6f}"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", sorgente, "-vf", vf,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
                    "-g", str(fps * 2), "-pix_fmt", "yuv420p",
                    # ⛔ l'audio si ricampiona a PCM 48k s16, che e' esattamente
                    #    quel che il cliente prende dal filo con `--audio-codec
                    #    pcm`: se qui restasse AAC, la taratura certificherebbe
                    #    una catena audio diversa da quella che si misura.
                    "-c:a", "pcm_s16le", "-ar", str(FS), "-ac", "2",
                    fuori], check=True)
    return fuori


def tara_cattura(dove, fps=40, fasi=(0.0, 0.006, 0.013, 0.019), tolleranza_ms=20.0):
    """La seconda tabella: gli stessi sfalsi noti, ma **ricampionati a 40/s**."""
    file_ = sorted(x for x in os.listdir(dove) if R_NOME.search(x))
    if not file_:
        print(f"   ⛔ in «{dove}» non c'e' nessun `09-b85-claquette-*.mp4`")
        return 2
    import tempfile
    d = tempfile.mkdtemp(prefix="b85cat")
    print(f"\n   ⭐ LA TARATURA, SECONDO GRADINO — ricampionato a {fps}/s, "
          f"{len(fasi)} fasi di cattura\n")
    print("   | messo   | ritrovato (medio) | scarto | il piu' basso / alto | esito |")
    print("   |---------|-------------------|--------|----------------------|-------|")
    rosso, errori, tutti = 0, [], []
    for nome in file_:
        m = R_NOME.search(nome)
        messo = int(m.group(2)) * (1 if m.group(1) == "p" else -1)
        vals = []
        for i, fase in enumerate(fasi):
            f = finge_cattura(os.path.join(dove, nome),
                              os.path.join(d, f"{i}-{nome}"), fps, fase)
            st = misura_file(f)
            if st.get("n"):
                vals.append(st["mediana_ms"])
        if not vals:
            print(f"   | {messo:+6d}  |     ⛔ NIENTE     |   –    |          –           | ⛔ MUTO |")
            rosso += 1
            continue
        # ⛔ LA MEDIA SULLE FASI, non la mediana: sul prodotto la fase della
        #    cattura **deriva** dentro un giro solo (40 e 60 non sono
        #    agganciati), quindi le trenta claquette di un giro campionano da
        #    sole tutte le fasi.  ⇒ Il numero da certificare e' quello mediato
        #    sulle fasi, ed e' anche quello che il giro vero produrra'.
        mu = sum(vals) / len(vals)
        err = mu - messo
        errori.append(err)
        tutti.extend(v - messo for v in vals)
        ok = abs(err) <= tolleranza_ms
        rosso += 0 if ok else 1
        print(f"   | {messo:+6d}  |     {mu:+8.1f}      | {err:+6.1f} | "
              f"{min(vals) - messo:+7.1f} / {max(vals) - messo:+7.1f}    | "
              f"{'✅' if ok else '⛔ ROSSO'} |")
    if errori:
        b = sum(errori) / len(errori)
        amp = max(tutti) - min(tutti)
        print(f"\n   ⭐ IL BIAS MISURATO: **{b:+.1f} ms**, e l'AMPIEZZA fra la "
              f"fase migliore e la peggiore: **{amp:.1f} ms**")
        print(f"     ⇒ ⚠ L'ampiezza e' l'errore vero di questo metro sul "
              f"prodotto, e sta sotto il fotogramma di cattura (25 ms) come")
        print(f"       deve.  ⛔ Non e' piu' un'ipotesi: e' misurata su sfalsi "
              f"che conoscevo.")
    print()
    if rosso:
        print(f"   ⛔⛔ {rosso} sfalsi non ritrovati dentro ±{tolleranza_ms:.0f} ms "
              f"dopo il ricampionamento.")
        return 3
    return 0


def prova_opus(wav, kbit=64):
    """⚠ QUANTO SPOSTA L'ATTACCO un giro di Opus, misurato invece che supposto.

    Il percorso dell'utente vero passa da Opus; questa presa passa da PCM.  ⇒ Il
    numero misurato **non contiene** questo termine, e chi lo legge deve sapere
    quanto vale.  ⛔ Non e' un'ipotesi: si codifica e si decodifica il WAV vero
    e si guarda di quanto si e' spostato l'attacco.
    """
    import tempfile
    d = tempfile.mkdtemp(prefix="b85opus")
    o = os.path.join(d, "o.opus")
    w = os.path.join(d, "r.wav")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", wav, "-c:a", "libopus", "-b:a", f"{kbit}k",
                    "-frame_duration", "20", o], check=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", o, "-ac", "1", "-ar", str(FS), w], check=True)
    def att(p):
        b = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-i", p, "-ac", "1", "-ar", str(FS),
                            "-f", "s16le", "-"], capture_output=True).stdout
        return attacchi(_inviluppo(b, 0.0, 1.0), SOGLIA_CLICK,
                        riarmo=CLA.PERIODO_S * 0.5)
    a, b = att(wav), att(w)
    n = min(len(a), len(b))
    if n == 0:
        return {"guasto": "⛔ nessun attacco da confrontare"}
    d_ms = [(b[i] - a[i]) * 1000.0 for i in range(n)]
    st = statistica(d_ms)
    st["attacchi_prima"], st["attacchi_dopo"] = len(a), len(b)
    return st


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="il metro dello sfalso audio-video")
    p.add_argument("--tara", action="store_true")
    p.add_argument("--tara-cattura", action="store_true",
                   help="⭐ il secondo gradino: gli stessi sfalsi noti, ma "
                        "ricampionati a 40/s come fa il prodotto")
    p.add_argument("--dove", default="/media/REMOTIX/tmp/09nr10")
    p.add_argument("--tolleranza", type=float, default=15.0)
    p.add_argument("--prova-opus", default="", metavar="WAV")
    p.add_argument("--presa", action="store_true")
    p.add_argument("--video", default="")
    p.add_argument("--tempi", default="")
    p.add_argument("--audio", default="")
    p.add_argument("--file", default="", help="misura un solo file")
    a = p.parse_args()
    if a.prova_opus:
        print(json.dumps(prova_opus(a.prova_opus), indent=1, ensure_ascii=False))
        sys.exit(0)
    if a.file:
        print(json.dumps(misura_file(a.file), indent=1, ensure_ascii=False))
        sys.exit(0)
    if a.presa:
        print(json.dumps(misura_presa(a.video, a.tempi, a.audio), indent=1,
                         ensure_ascii=False))
        sys.exit(0)
    if a.tara_cattura:
        sys.exit(tara_cattura(a.dove))
    if a.tara:
        rc = tara(a.dove, a.tolleranza)
        # ⛔ Il secondo gradino gira SOLO se il primo e' passato: certificare
        #    il ricampionamento con un rivelatore che gia' sbaglia sul file
        #    darebbe due rossi per una causa sola, e il secondo nasconderebbe
        #    il primo.
        sys.exit(rc if rc else tara_cattura(a.dove))
    p.print_help()
    sys.exit(2)
