#!/usr/bin/env python3
"""09-b85-claquette.py — il filmato con l'ATTACCO NETTO, e i suoi gemelli sfalsati.

    python3 09-b85-claquette.py --dove /media/REMOTIX/tmp/09nr10 \
            --secondi 62 --scena calma --sfalsi 0,+100,-100,+300,-300,+700,-700

⭐ A che cosa serve, ed e' il difetto dichiarato di `fasi/09` §16.4 che lo
   chiede: la prova del 23 agosto 2026 ha chiesto all'utente un giudizio sul
   sincronismo guardando **grana pura**, cioe' l'immagine in cui l'occhio ha
   MENO appigli.  La risposta e' stata *«non posso sapere se c'e'
   disallineamento se il video e' incomprensibile»*.  ⇒ Il filmato giusto non
   si cerca: si genera, e deve avere un istante in cui **si vede** quel che
   **si sente**.

⛔ E DEVE ESSERE MISURABILE IN AUTOMATICO, non solo guardabile.  L'occhio
   dell'utente serve al giudizio finale; il numero lo deve dare una macchina, o
   §16.4 si ripete identica.  ⇒ Tre scelte, e ognuna esiste per questo:

   1. ⭐ **la finestra nera fissa**.  Il lampo NON si disegna sul fondo: si
      disegna dentro un riquadro **nero** ridipinto a ogni fotogramma, sempre
      nello stesso posto.  Cosi' il metro guarda una regione che vale ZERO
      tranne quando c'e' il lampo — ⛔ e questo vale **anche sulla scena dura**,
      dove il fondo e' grana e un lampo disegnato sopra non si distinguerebbe
      dal rumore.  Senza questo riquadro il banco misurerebbe bene sul caso
      facile e male sul caso che conta;
   2. ⭐ **il lampo dura piu' di un fotogramma di cattura**.  Il prodotto
      cattura a 40 fotogrammi al secondo, cioe' **25 ms**, e non e' agganciato
      alla sorgente: un lampo lungo un solo fotogramma **puo' cadere fra due
      catture e sparire**.  ⇒ 4 fotogrammi (~66 ms a 60/s), che nessuna cattura
      a 40/s puo' saltare.  ⚠ Il prezzo e' che si misura l'ATTACCO, non il
      centro, e l'attacco visto dal ricevente e' in ritardo di mezzo periodo di
      cattura in media: e' il termine `+12,5 ms` che `09-b85-metro.py` dichiara
      e che la certificazione contro gli sfalsi noti **misura** invece di
      supporlo;
   3. ⭐ **il click e' una raffica, non un impulso**.  Un impulso di un
      campione lo Opus lo spalma: a 48 kHz e 20 ms di blocco l'energia esce
      prima e dopo, e l'attacco misurato si sposta di quanto non si sa.  ⇒ Una
      raffica di 1 kHz lunga 40 ms con attacco **ripido** (0,3 ms di rampa):
      la soglia si attraversa in un punto ben definito anche dopo un giro di
      Opus, e `09-b85-metro.py --prova-opus` misura **quanto** si sposta.

⚠ E IL FONDO DEVE COSTARE, o non si riproduce il caso «sotto carico».
   `fasi/09` §16 misura il caso duro a **21,5-23,1 Mbit/s**: un fondo nero non
   ci arriva nemmeno da lontano, e un banco che misurasse la sincronia su una
   scena da 0,2 Mbit/s direbbe di aver misurato il caso che non ha misurato.
   ⇒ `--scena dura` mette grana in movimento su tutto il resto dello schermo.

⛔ E GLI SFALSI SONO IL MOTIVO PER CUI QUESTO FILE ESISTE PRIMA DEGLI ALTRI.
   `-itsoffset` sposta l'audio di un tempo **che io conosco**.  Se il metro non
   ritrova quel tempo, col segno giusto, non c'e' niente da misurare sul
   prodotto — e quello e' gia' il risultato (`fasi/09` §16.4: *«prima di
   misurarlo va certificato lo strumento»*).

⭐ IL SEGNO, e si sceglie quello della pagina per non aprire una seconda
   convenzione: `src/pagina.html:6398` — *«`AV = aoff - voff`.  Positivo = il
   suono esce DOPO l'immagine (l'audio e' indietro)»*.  ⇒ Qui
   **`sfalso = t_click - t_lampo`**, e `-itsoffset +0,300` sull'ingresso audio
   ritarda l'audio di 300 ms, cioe' deve uscire **+300**.
"""
import argparse
import math
import os
import struct
import subprocess
import sys

# ⛔ I numeri della claquette stanno QUI e in un posto solo: il metro li
#    importa da questo file invece di riscriverli.  Due copie di «ogni due
#    secondi» che divergono darebbero un banco che misura un filmato diverso da
#    quello che ha generato, e il rosso non sarebbe distinguibile da un difetto
#    del prodotto.
PERIODO_S = 2.0          # un attacco ogni due secondi
FS = 48000               # frequenza dei campioni audio
CLICK_HZ = 1000.0        # il tono della raffica
CLICK_MS = 40.0          # quanto dura la raffica
CLICK_RAMPA_MS = 0.3     # l'attacco: ripido, ma non un gradino (Opus)
CLICK_AMPIEZZA = 0.72    # ⚠ non 1.0: un tono al fondo scala fa clipping dopo Opus
VIDEO_FPS = 60           # ⭐ 60, non 40 — vedi il riquadro qui sotto
LAMPO_FOTOGRAMMI = 4     # 4/60 = 66,7 ms: nessuna cattura a 40/s lo salta
# La finestra nera e il lampo dentro: coordinate FISSE, e il metro le rilegge.
RIQ_X, RIQ_Y, RIQ_L, RIQ_A = 96, 96, 480, 480      # il riquadro nero
LAMPO_X, LAMPO_Y, LAMPO_L, LAMPO_A = 176, 176, 320, 320   # il lampo bianco

# ⭐ PERCHE' 60 FOTOGRAMMI AL SECONDO E NON 40, che e' il ritmo del prodotto.
#
#    Chi riproduce (`mpv`) presenta i fotogrammi sui rinfreschi dello schermo.
#    Con una sorgente a 40/s su uno schermo a 60 Hz il lettore **duplica e
#    salta**, e l'istante in cui il lampo compare davvero sul vetro si sposta
#    di un rinfresco in modo che non e' dichiarabile.  ⛔ A 60/s su 60 Hz ogni
#    fotogramma sorgente cade su un rinfresco e uno solo: l'attacco resta dove
#    lo abbiamo messo, e l'unica quantizzazione che resta e' quella della
#    CATTURA — che e' del prodotto, si dichiara, e si misura.
#    ⚠ Se lo schermo della sessione non fosse a 60 Hz questa riga va rifatta:
#      `--fps` esiste apposta, e chi lo cambia lo scrive nel rapporto.


def _campioni_click(secondi, fps_video):
    """La traccia audio, campione per campione.  ⛔ Senza numpy: la macchina di
       prova non ce l'ha, e il filmato si genera DOVE gira il prodotto.

    ⭐ Gli attacchi cadono a `t = k * PERIODO_S` esatti, cioe' al campione
       `k * PERIODO_S * FS` — un intero, perche' 2 s a 48 kHz fa 96 000.  Non
       c'e' nessun arrotondamento da dichiarare: e' la meta' del metro che vale
       zero errore, e l'altra meta' (il video) vale 25 ms.
    """
    n_tot = int(round(secondi * FS))
    dati = bytearray(n_tot * 2 * 2)          # stereo, s16le
    n_click = int(CLICK_MS * FS / 1000.0)
    n_rampa = max(1, int(CLICK_RAMPA_MS * FS / 1000.0))
    quando = []
    k = 1                                    # ⭐ si parte da t=2 s: un preludio
    while k * PERIODO_S < secondi - CLICK_MS / 1000.0:
        base = int(round(k * PERIODO_S * FS))
        quando.append(base / FS)
        for i in range(n_click):
            # attacco ripido, coda in dissolvenza: l'attacco e' quel che si
            # misura, la coda serve solo a non lasciare un gradino a Opus
            if i < n_rampa:
                inv = i / n_rampa
            elif i > n_click - n_rampa * 20:
                inv = max(0.0, (n_click - i) / (n_rampa * 20))
            else:
                inv = 1.0
            v = CLICK_AMPIEZZA * inv * math.sin(2 * math.pi * CLICK_HZ * i / FS)
            c = int(max(-32767, min(32767, v * 32767)))
            off = (base + i) * 4
            if off + 4 > len(dati):
                break
            struct.pack_into("<hh", dati, off, c, c)
        k += 1
    return bytes(dati), quando


def scrivi_wav(percorso, dati):
    """Un WAV a 48 kHz stereo, scritto a mano.  ⚠ `wave` andrebbe bene: e'
       scritto a mano perche' cosi' il file e' UN blocco e non c'e' nessuna
       differenza fra quel che si crede di aver scritto e quel che c'e'."""
    n = len(dati)
    with open(percorso, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, 2, FS, FS * 4, 4, 16))
        f.write(b"data" + struct.pack("<I", n) + dati)


def filtro_video(scena, fps):
    """La catena `-vf`.  ⛔ L'ORDINE CONTA, e sbagliarlo si vede solo misurando:
       il riquadro nero va disegnato DOPO il fondo e PRIMA del lampo, o il
       fondo lo copre e il metro guarda grana."""
    periodo_f = int(round(PERIODO_S * fps))
    # ⛔ `gte(n,periodo_f)`: NIENTE lampo al fotogramma 0.  Il primo click e' a
    #    t = 2 s (c'e' un preludio), e un lampo a t = 0 senza il suo click
    #    resterebbe spaiato — cioe' un attacco in piu' da un lato solo, che e'
    #    il sintomo con cui si presenta anche un difetto VERO (un lampo perso
    #    dalla cattura).  Due cause per lo stesso sintomo, e una e' mia.
    lampo = (f"lt(mod(n\\,{periodo_f})\\,{LAMPO_FOTOGRAMMI})"
             f"*gte(n\\,{periodo_f})")
    return (
        # 1. il riquadro nero, sempre, sopra qualunque fondo
        f"drawbox=x={RIQ_X}:y={RIQ_Y}:w={RIQ_L}:h={RIQ_A}:color=black@1:t=fill,"
        # 2. il lampo bianco, dentro, per `LAMPO_FOTOGRAMMI` fotogrammi
        f"drawbox=x={LAMPO_X}:y={LAMPO_Y}:w={LAMPO_L}:h={LAMPO_A}:"
        f"color=white@1:t=fill:enable='{lampo}',"
        # 3. ⭐ e una barra che si muove SEMPRE, anche sulla scena calma: un
        #    fondo del tutto fermo non fa spedire niente al prodotto (§8.3
        #    cala i fotogrammi quando non cambia niente), e un banco che
        #    misurasse la sincronia su una scena senza video misurerebbe due
        #    lampi al minuto invece di trenta.
        f"drawbox=x='mod(t*380\\,1820)':y=700:w=100:h=260:color=yellow@1:t=fill"
    )


def sorgente_video(scena, larghezza, altezza, fps, secondi):
    """Il fondo.  ⚠ E il fondo E' il caso: `calma` e `dura` non sono due gusti,
       sono i due bracci di §16 (a riposo / sotto carico)."""
    if scena == "calma":
        # ⭐ un gradiente lento: si muove abbastanza da far spedire, costa poco
        return (f"gradients=s={larghezza}x{altezza}:r={fps}:d={secondi}:"
                f"c0=0x101018:c1=0x203050:speed=0.02")
    if scena == "dura":
        # ⛔ grana vera, che e' quel che §16 ha misurato a 21-23 Mbit/s: un
        #    fondo «complicato ma comprimibile» darebbe un caso «sotto carico»
        #    che non carica, e il numero uscirebbe uguale a quello a riposo per
        #    il motivo sbagliato.
        # ⚠ `noise` e non `geq=random(1)`: a 1920x1080x60x70 il secondo fa
        #   otto MILIARDI di valutazioni per pixel e non finisce in un'ora.
        #   ⭐ `allf=t` rifa' il rumore a ogni fotogramma, che e' quel che lo
        #   rende incomprimibile — `allf=u` da solo lo lascia FERMO, e un fondo
        #   fermo costa quasi zero: sarebbe una scena «dura» che non carica.
        # ⚠⛔ E LA GRANA SI FA A META' MISURA E POI SI INGRANDISCE, e la prima
        #    stesura non lo faceva: `noise` a 1920x1080 con `allf=t` e' rumore
        #    NUOVO su ogni pixel di ogni fotogramma, cioe' il caso peggiore che
        #    esista per un codificatore.  `[M]` 24 agosto 2026: a CRF 18 sono
        #    usciti **3 999 MB** per 70 s — 457 Mbit/s da decodificare.
        #    ⛔ Non e' «una scena dura»: e' una scena che mette in ginocchio il
        #    LETTORE, e allora quel che si misura non e' piu' il prodotto, e'
        #    `mpv` che non ce la fa.  ⇒ La grana si genera a meta' risoluzione
        #    e si ingrandisce a blocchi (`neighbor`): per l'occhio e per il
        #    codificatore del PRODOTTO resta grana, per il lettore costa un
        #    quarto.
        mez_l, mez_a = larghezza // 2, altezza // 2
        return (f"testsrc2=s={mez_l}x{mez_a}:r={fps}:d={secondi},"
                f"noise=alls=48:allf=t,"
                f"scale={larghezza}:{altezza}:flags=neighbor")
    raise SystemExit(f"   ⛔ scena «{scena}»: solo `calma` o `dura`")


def genera(dove, secondi, scena, larghezza, altezza, fps, sfalsi, crf):
    os.makedirs(dove, exist_ok=True)
    wav = os.path.join(dove, "09-b85-claquette.wav")
    muto = os.path.join(dove, f"09-b85-muto-{scena}.mp4")
    dati, quando = _campioni_click(secondi, fps)
    scrivi_wav(wav, dati)
    print(f"   [gen]  audio: {len(quando)} attacchi, il primo a {quando[0]:.3f} s, "
          f"l'ultimo a {quando[-1]:.3f} s → {wav}")

    # ⛔ Il video si genera UNA volta e si riusa per tutti gli sfalsi: se ogni
    #    sfalso avesse un video suo, due misure diverse potrebbero venire da
    #    due codifiche diverse invece che dallo sfalso — e la certificazione
    #    misurerebbe il rumore del generatore.
    if not os.path.exists(muto):
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-f", "lavfi", "-i", sorgente_video(scena, larghezza, altezza, fps, secondi),
               "-vf", filtro_video(scena, fps),
               "-t", str(secondi),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf),
               "-g", str(fps * 2), "-pix_fmt", "yuv420p", "-an", muto]
        print(f"   [gen]  video {scena} {larghezza}x{altezza}@{fps} …")
        subprocess.run(cmd, check=True)
    print(f"   [gen]  video: {muto} ({os.path.getsize(muto)/1e6:.1f} MB)")

    usciti = []
    for ms in sfalsi:
        # ⭐ `-itsoffset` sull'ingresso AUDIO: positivo = i tempi dell'audio
        #    salgono, cioe' il suono esce DOPO.  ⇒ deve uscire `+ms`.
        nome = f"09-b85-claquette-{scena}-{'p' if ms >= 0 else 'm'}{abs(ms):03d}.mp4"
        fuori = os.path.join(dove, nome)
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-i", muto,
               "-itsoffset", f"{ms/1000.0:.6f}", "-i", wav,
               "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
               # ⛔ senza questo l'audio spostato IN ANTICIPO viene tagliato
               #    all'inizio invece che spostato, e lo sfalso negativo si
               #    misurerebbe piu' piccolo di quel che e'.
               "-avoid_negative_ts", "make_zero",
               "-t", str(secondi), fuori]
        subprocess.run(cmd, check=True)
        usciti.append((ms, fuori))
        print(f"   [gen]  sfalso {ms:+5d} ms → {fuori} "
              f"({os.path.getsize(fuori)/1e6:.1f} MB)")
    return wav, muto, usciti


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="il filmato con l'attacco netto")
    p.add_argument("--dove", default="/media/REMOTIX/tmp/09nr10")
    p.add_argument("--secondi", type=float, default=62.0)
    p.add_argument("--scena", default="calma", choices=("calma", "dura"))
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--fps", type=int, default=VIDEO_FPS)
    p.add_argument("--crf", type=int, default=20)
    p.add_argument("--sfalsi", default="0",
                   help="millisecondi separati da virgola: `0,+100,-300,…`.  "
                        "⭐ Positivo = l'audio ESCE DOPO (la convenzione di "
                        "`pagina.html:6398`)")
    a = p.parse_args()
    sf = [int(x) for x in a.sfalsi.replace(" ", "").split(",") if x]
    genera(a.dove, a.secondi, a.scena, a.larghezza, a.altezza, a.fps, sf, a.crf)
    print("   [gen]  ⭐ fatto.")
