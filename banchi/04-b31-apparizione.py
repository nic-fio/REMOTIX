#!/usr/bin/env python3
"""04-b31-apparizione.py — ⛔ IL BANCO DI O1: quanto aspetta l'utente fra il
LOGIN e il primo pixel **VERO**?

    python3 04-b31-apparizione.py --certifica --lavoro DIR
    python3 04-b31-apparizione.py --misura DIR/prima-misura.json \\
            --lavoro DIR --esiti 04-b31-esiti.jsonl

⚠ Gira DENTRO il contenitore: ci vuole `ffmpeg`, che sta li'.  ⛔ E NON ci
  vogliono ne' `numpy` ne' `PIL`, che li' non ci sono.

===========================================================================
⛔⛔ LA DOMANDA, E NON E' «QUANDO ARRIVA IL PRIMO FOTOGRAMMA»
===========================================================================

Il mandato dell'utente, 14 agosto 2026: *«il tempo fra il login e la comparsa
del desktop e' troppo lungo»*.  ⇒ ⛔ **Uno schermo vuoto spedito subito non e'
una cura**: farebbe comparire prima un vuoto e quattro secondi dopo il desktop,
che *sembra un difetto* invece di un'attesa — cioe' e' **peggio**.

⇒ Questo banco misura **due istanti diversi**, e li tiene separati apposta:

    t_primo_fotogramma   il primo fotogramma completo, qualunque cosa contenga
    ⭐ t_primo_pixel_vero il primo fotogramma in cui c'e' **il desktop**

⛔ Il verdetto lo da' il **secondo**.  Un prodotto che facesse scendere il primo
   e lasciasse il secondo dov'e' passerebbe un banco che guardasse solo l'inizio
   della catena, e peggiorerebbe quel che l'utente vede.

===========================================================================
⛔ IL GIUDICE DEI PIXEL E' QUELLO DI A1, E NON UN SECONDO
===========================================================================

*«C'e' lo sfondo» non e' «c'e' il desktop»* — l'errore che ha nascosto il
difetto per due fasi.  A1 ha gia' costruito, **calibrato su immagini vere** e
**certificato** i due indicatori che distinguono le due cose:

    B  il salto di luminanza al bordo basso della barra   (11,8 shell / 0,07 sfondo)
    T  i fronti del testo dell'orologio                   (565 shell / 0 sfondo)

⇒ Qui si importa `04-b20-desktop-vero.py` e si prendono **le sue soglie e la sua
  regola di verdetto**.  ⛔ Riscriverle darebbe due giudici che possono
  divergere, e allora nessuno dei due e' l'arbitro.

⚠ **Quel che questo file scrive di suo, e perche'**: A1 giudica UN fotogramma,
  reso in PNG; qui ne servono centinaia, e renderli tutti in PNG a 1080p e'
  qualche giga di disco.  ⇒ Il ritaglio della fascia alta si fa **in una passata
  sola** su tutto il flusso, e il conto di B e T si rifa' riga per riga.
  ⛔ E la certificazione LO CONTROLLA: sulle **stesse due immagini fabbricate**
  da A1, i miei B e T devono uscire **identici** ai suoi.  Senza quel controllo
  questa sarebbe la seconda lettura che si voleva evitare.

⛔ E l'indicatore **D** (la dock) non c'e': A1 l'ha misurato e **non
   distingueva** (0,069 shell contro 0,082 sfondo), e non entrava nel suo
   verdetto.  Portarselo dietro qui costerebbe 130 000 pixel per fotogramma per
   un numero che non decide niente.  *Dichiarato, non nascosto.*

===========================================================================
⛔ LE SOGLIE, SCRITTE PRIMA DEL GIRO
===========================================================================

`SOGLIA_S = 2,0 s` fra `CREDENZIALI` e il primo pixel vero, e il conto e'
questo:

  · `RCP.md` §4.4-bis impone al server **un secondo fisso** prima di rispondere
    a `CREDENZIALI`.  E' nostro, l'utente lo aspetta, e sta DENTRO la misura:
    ⇒ il pavimento non e' zero, e' **~1,0 s**;
  · `[M]` 14 agosto 2026, registro della sessione vera dell'utente: il figlio
    nasce a +59 ms, ha un fotogramma **codificato** a +325 ms e il palco montato
    a +379 ms.  ⇒ Quando il canale video si accende, i pixel ci sono gia';
  · ⇒ fra `SESSIONE` e il primo pixel vero non ci deve stare piu' di **~0,9 s**.

⚠ E la soglia si scrive qui, in cima, e non dentro il conto: una soglia che si
  trova solo leggendo il codice e' una soglia che si puo' spostare dopo aver
  visto il risultato.

===========================================================================
⛔ I CODICI D'USCITA — «zero» e «guasto» non hanno la stessa faccia
===========================================================================

    0  ⭐ VERDE            il primo pixel VERO e' arrivato entro la soglia
    1  ⛔ ROSSO TARDI      e' arrivato, ma oltre la soglia
    2  ⛔ NON GIUDICABILE  lo STRUMENTO non ha potuto guardare (decodifica,
                           conti che non combaciano).  ⚠ Non e' un rosso del
                           prodotto, ed e' l'unico codice che non lo accusa
    3  ⛔ ROSSO MAI        fotogrammi ne sono arrivati, e il desktop NON c'e'
                           in nessuno: la faccia peggiore
    4     USO SBAGLIATO
    5  ⛔ ROSSO ZERO       nessun fotogramma completo e' arrivato
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ IL GIUDICE DI A1, IMPORTATO — non ricopiato.  Da qui vengono le soglie
#    (`SALTO`, `FRONTE`, `FRONTI_MINIMI`, `FASCIA_ALTA`, `ALTEZZA_BARRA`,
#    `BORDO_DA`, `BORDO_A`), la regola di verdetto e la lettura della luminanza.
a1 = _porta("a1", "04-b20-desktop-vero.py")

# --- la soglia del banco, SCRITTA PRIMA DEL GIRO ---------------------------
SOGLIA_S = 2.0        # `CREDENZIALI` → primo pixel VERO — vedi il riquadro
PASSO_COLONNE = 8     # ⚠ lo stesso di A1: entra nei numeri, e va dichiarato

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def dimmi(*a):
    print(*a, flush=True)


def ffmpeg(argomenti, dove):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
                       + argomenti, capture_output=True)
    if r.returncode != 0:
        dimmi(f"   ⛔ ffmpeg({dove}) e' uscito {r.returncode}: "
              f"{r.stderr.decode(errors='replace')[:400]}")
        return False
    return True


# ===========================================================================
def bt_di_una_fascia(d, base, L):
    """B e T di UNA fascia alta, letti dal grezzo `rgb24`.

    ⛔ Gli stessi conti di `a1.indicatori`, con le SUE soglie: qui cambia solo
       da dove arrivano i byte (una fascia dentro un file che ne contiene
       molte, invece di un file per fascia).  ⚠ Che i due diano lo stesso
       numero non si spera: lo verifica `--certifica`.
    """
    prof = []
    colonne = list(range(0, L, PASSO_COLONNE))
    for y in range(a1.FASCIA_ALTA):
        riga = base + y * L * 3
        prof.append(sum(a1.luma(d, riga + x * 3) for x in colonne) / len(colonne))

    salto, dove = 0.0, -1
    for y in range(a1.BORDO_DA, min(a1.BORDO_A, a1.FASCIA_ALTA - 1)):
        v = abs(prof[y + 1] - prof[y])
        if v > salto:
            salto, dove = v, y + 1

    x0, x1 = L // 3, 2 * L // 3
    fronti = 0
    for y in range(4, a1.ALTEZZA_BARRA - 4):
        riga = base + y * L * 3
        prec = a1.luma(d, riga + x0 * 3)
        for x in range(x0 + 1, x1):
            v = a1.luma(d, riga + x * 3)
            if abs(v - prec) > a1.FRONTE:
                fronti += 1
            prec = v

    return {"salto_bordo": round(salto, 2), "riga_del_bordo": dove,
            "barra_luminanza": round(sum(prof[:a1.ALTEZZA_BARRA])
                                     / a1.ALTEZZA_BARRA, 2),
            "fronti_nella_barra": fronti,
            "B": bool(salto > a1.SALTO),
            "T": bool(fronti >= a1.FRONTI_MINIMI)}


def giudica_flusso(flusso, codec, L, A, lavoro, etichetta, quanti):
    """Decodifica il flusso e giudica OGNI fotogramma, in ordine.

    Restituisce `(lista, None)` o `(None, perche)`.
    """
    demux = "hevc" if codec == 1 else ("av1" if codec == 2 else None)
    if demux is None:
        return None, f"codec {codec} sconosciuto a questo banco"
    fascia = os.path.join(lavoro, f"{etichetta}-fasce.rgb")
    if not ffmpeg(["-f", demux, "-i", flusso, "-frames:v", str(quanti),
                   "-vf", f"crop=iw:{a1.FASCIA_ALTA}:0:0",
                   "-pix_fmt", "rgb24", "-f", "rawvideo", fascia], "fasce"):
        return None, "il decodificatore non ha reso nessuna fascia"
    per_fascia = L * a1.FASCIA_ALTA * 3
    byte = os.path.getsize(fascia)
    if byte == 0:
        return None, "il decodificatore ha reso ZERO fotogrammi da byte che c'erano"
    if byte % per_fascia:
        return None, (f"{byte} byte di fasce non sono un multiplo di "
                      f"{per_fascia}: la misura non e' quella che credo")
    n = byte // per_fascia
    with open(fascia, "rb") as f:
        d = f.read()
    fuori = []
    for i in range(n):
        m = bt_di_una_fascia(d, i * per_fascia, L)
        cod, parola = a1.verdetto(m)
        m["verdetto"] = parola
        fuori.append(m)
    os.remove(fascia)
    return fuori, None


def png_del_fotogramma(flusso, codec, indice, lavoro, nome):
    """⭐ L'immagine, perche' qualcuno la GUARDI (I8 — il metro e' quel che
    l'utente vede).  ⚠ Non entra nel verdetto."""
    demux = "hevc" if codec == 1 else "av1"
    png = os.path.join(lavoro, f"{nome}.png")
    if ffmpeg(["-f", demux, "-i", flusso, "-vf", f"select=eq(n\\,{indice})",
               "-vsync", "0", "-frames:v", "1", png], "png"):
        return png
    return None


# ===========================================================================
def principale(a):
    os.makedirs(a.lavoro, exist_ok=True)
    if a.certifica:
        return certifica(a.lavoro)
    if not a.misura:
        dimmi("⛔ serve --misura DIR/<etichetta>-misura.json, o --certifica")
        return 4

    try:
        with open(a.misura, encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError) as e:
        dimmi(f"   ⛔ NON GIUDICABILE: la misura non si legge ({e})")
        return 2

    et = m["etichetta"]
    fot = m["fotogrammi"]
    flusso = os.path.join(os.path.dirname(os.path.abspath(a.misura)), m["flusso"])
    dimmi(f"== O1 · 04-b31 — «{et}»")
    dimmi(f"   scena: {m['scena']}")
    dimmi(f"   AMMESSO a t={m['t_ammesso']:.3f} s · SESSIONE a "
          f"t={m['t_sessione']:.3f} s  ⚠ (dentro c'e' il secondo fisso di §4.4-bis)")
    dimmi(f"   fotogrammi completi: {len(fot)}  ·  azzerati e non contati: "
          f"{m['azzerati']}  ·  caduta: {m['caduta']}")

    riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "banco": "04-b31-apparizione", "etichetta": et,
            "scena": m["scena"], "porta": m.get("porta"),
            "soglia_s": SOGLIA_S,
            "t_ammesso": m["t_ammesso"], "t_sessione": m["t_sessione"],
            "fotogrammi": len(fot), "azzerati": m["azzerati"],
            "caduta": m["caduta"]}

    # ---- 5: ZERO.  ⛔ E non e' «non ho potuto guardare» ------------------
    if not fot:
        dimmi(f"\n   {ROSSO}⇒ ZERO FOTOGRAMMI{GRIGIO}")
        dimmi("      ⛔ Al client non e' arrivato NIENTE in tutta l'attesa.")
        dimmi("      ⚠ E' un rosso del PRODOTTO, non dello strumento: la "
              "stretta di mano")
        dimmi("        e' arrivata a SESSIONE, quindi il canale c'era.")
        riga.update(verdetto="ZERO FOTOGRAMMI", uscita=5)
        scrivi(a, riga)
        return 5

    t_primo = fot[0]["t_completo"]
    L, A = fot[0]["larghezza"], fot[0]["altezza"]
    codec = m["codec"]

    atteso = min(len(fot), a.quanti)
    giudizi, perche = giudica_flusso(flusso, codec, L, A, a.lavoro, et, a.quanti)
    if giudizi is None:
        dimmi(f"\n   {GIALLO}⇒ NON GIUDICABILE: {perche}{GRIGIO}")
        riga.update(verdetto="NON GIUDICABILE", uscita=2, perche=perche)
        scrivi(a, riga)
        return 2
    # ⛔⛔ E QUI SI RIFIUTA DI INDOVINARE: se i fotogrammi decodificati non sono
    #     tanti quanti quelli arrivati, l'indice del decodificatore non e'
    #     l'indice dell'arrivo — e allineare a occhio due liste di lunghezza
    #     diversa vuol dire attribuire a un fotogramma l'ora di un altro.
    if len(giudizi) != atteso:
        perche = (f"il decodificatore ha reso {len(giudizi)} fotogrammi e ne "
                  f"sono arrivati {atteso}: gli istanti non si possono "
                  f"attribuire, e NON li indovino")
        dimmi(f"\n   {GIALLO}⇒ NON GIUDICABILE: {perche}{GRIGIO}")
        riga.update(verdetto="NON GIUDICABILE", uscita=2, perche=perche,
                    decodificati=len(giudizi), arrivati=atteso)
        scrivi(a, riga)
        return 2

    primo_vero = None
    for i, g in enumerate(giudizi):
        if g["verdetto"] == "SHELL":
            primo_vero = i
            break

    dimmi(f"\n   i primi fotogrammi, giudicati uno per uno:")
    for i in range(min(len(giudizi), 8)):
        g, x = giudizi[i], fot[i]
        col = VERDE if g["verdetto"] == "SHELL" else (
            GIALLO if g["verdetto"] == "MEZZO" else ROSSO)
        dimmi(f"     {i + 1:3d}  t={x['t_completo']:8.3f} s  {x['tipo']:6s} "
              f"{x['byte']:7d} B   salto {g['salto_bordo']:7.2f}  fronti "
              f"{g['fronti_nella_barra']:5d}   {col}{g['verdetto']}{GRIGIO}")
    if primo_vero is not None and primo_vero >= 8:
        g, x = giudizi[primo_vero], fot[primo_vero]
        dimmi(f"     ...")
        dimmi(f"     {primo_vero + 1:3d}  t={x['t_completo']:8.3f} s  "
              f"{x['tipo']:6s} {x['byte']:7d} B   salto {g['salto_bordo']:7.2f}"
              f"  fronti {g['fronti_nella_barra']:5d}   {VERDE}SHELL{GRIGIO}")

    riga.update(t_primo_fotogramma=t_primo,
                byte_primo_fotogramma=fot[0]["byte"],
                verdetto_primo_fotogramma=giudizi[0]["verdetto"],
                giudicati=len(giudizi))

    png = png_del_fotogramma(flusso, codec, 0, a.lavoro, f"{et}-primo")
    dimmi(f"\n   ⚠ il PRIMO fotogramma: t={t_primo:.3f} s, {fot[0]['byte']} "
          f"byte, giudicato {giudizi[0]['verdetto']}"
          + (f" — {png}" if png else ""))

    # ---- 3: fotogrammi si', desktop no ----------------------------------
    if primo_vero is None:
        dimmi(f"\n   {ROSSO}⇒ IL DESKTOP NON COMPARE MAI{GRIGIO}")
        dimmi(f"      ⛔ {len(giudizi)} fotogrammi giudicati, e in NESSUNO c'e' "
              f"la shell.")
        dimmi("      ⚠ «arrivano fotogrammi» non e' «l'utente vede il suo "
              "desktop».")
        riga.update(verdetto="MAI", uscita=3, t_primo_pixel_vero=None)
        scrivi(a, riga)
        return 3

    t_vero = fot[primo_vero]["t_completo"]
    nostro = round(t_vero - m["t_sessione"], 3)
    png_v = png_del_fotogramma(flusso, codec, primo_vero, a.lavoro,
                               f"{et}-primo-vero")
    riga.update(t_primo_pixel_vero=t_vero, indice_primo_vero=primo_vero + 1,
                dopo_sessione_s=nostro,
                buttati_prima=primo_vero,
                byte_buttati_prima=sum(x["byte"] for x in fot[:primo_vero]))

    dimmi(f"\n   ⭐ IL PRIMO PIXEL VERO: fotogramma n. {primo_vero + 1}, "
          f"t={t_vero:.3f} s dal login" + (f" — {png_v}" if png_v else ""))
    dimmi(f"      di cui {m['t_sessione']:.3f} s fino a SESSIONE (dentro c'e' "
          f"il secondo fisso) e {nostro:.3f} s dopo")
    if primo_vero:
        dimmi(f"      ⚠ e prima di lui l'utente ha ricevuto {primo_vero} "
              f"fotogrammi che NON erano il desktop")

    if t_vero > SOGLIA_S:
        dimmi(f"\n   {ROSSO}⇒ ROSSO: {t_vero:.3f} s, e la soglia e' "
              f"{SOGLIA_S:.1f} s{GRIGIO}")
        riga.update(verdetto="TARDI", uscita=1)
        scrivi(a, riga)
        return 1
    dimmi(f"\n   {VERDE}⇒ VERDE: {t_vero:.3f} s, sotto la soglia di "
          f"{SOGLIA_S:.1f} s{GRIGIO}")
    riga.update(verdetto="IN TEMPO", uscita=0)
    scrivi(a, riga)
    return 0


def scrivi(a, riga):
    if a.esiti:
        with open(a.esiti, "a") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")


# ===========================================================================
def finta_misura(lavoro, etichetta, vuoti, pieni, t0, passo):
    """Fabbrica un giro finto: `vuoti` fotogrammi senza shell, poi `pieni` con.

    ⛔ E' il controllo positivo del CRONOMETRO, non del giudice: si sa in
       partenza quale fotogramma e' il primo vero e a che ora e' arrivato, e il
       banco deve dire quel numero.  ⚠ Senza, «il banco non trova mai il primo
       pixel vero» e «il banco trova sempre il primo» sarebbero indistinguibili
       da un giro solo.
    """
    vuota = os.path.join(lavoro, "finta-vuota.png")
    shell = os.path.join(lavoro, "finta-shell.png")
    lista = os.path.join(lavoro, f"{etichetta}-lista.txt")
    flusso = os.path.join(lavoro, f"{etichetta}-flusso.265")
    with open(lista, "w", encoding="utf-8") as f:
        for _ in range(vuoti):
            f.write(f"file '{vuota}'\nduration 0.033\n")
        for _ in range(pieni):
            f.write(f"file '{shell}'\nduration 0.033\n")
        f.write(f"file '{shell}'\n")
    # ⚠ In software e senza B-frame: l'ordine di uscita del decodificatore deve
    #   essere quello d'ingresso, o l'indice non vale l'indice.
    # ⛔ E `-frames:v` NON e' un dettaglio: senza, il demuxer `concat` produce
    #    **un fotogramma in piu'** (l'ultimo file ripetuto per dare la durata al
    #    penultimo), e la certificazione falliva su tutt'e quattro i casi
    #    accusando il giudice di un difetto del fabbricatore.  `[M]` 14 agosto
    #    2026, primo giro di questo banco — ⭐ e l'ha accusato **il controllo
    #    che rifiuta di indovinare**, che quindi funziona.
    if not ffmpeg(["-f", "concat", "-safe", "0", "-i", lista,
                   "-frames:v", str(vuoti + pieni),
                   "-c:v", "libx265", "-x265-params", "bframes=0:log-level=none",
                   "-pix_fmt", "yuv420p", "-f", "hevc", flusso], "finto-flusso"):
        return None
    fot = []
    for i in range(vuoti + pieni):
        fot.append({"n": i + 1, "stream": 3 + 4 * i,
                    "t_primo_byte": round(t0 + i * passo - 0.002, 6),
                    "t_completo": round(t0 + i * passo, 6),
                    "tipo": "chiave" if i == 0 else "delta", "codec": 1,
                    "larghezza": 1920, "altezza": 1080, "numero": i + 1,
                    "istante_server_us": 0, "input": 0, "byte": 1000})
    m = {"banco": "04-b31-apparizione", "etichetta": etichetta,
         "quando": "finto", "porta": 0, "utente": "finto",
         "scena": "FINTA: fabbricata da --certifica, senza il prodotto",
         "tela_chiesta": [1920, 1080], "tela_concessa": [1920, 1080],
         "codec": 1, "t_ammesso": 1.01, "t_sessione": 1.05, "attesa": 10.0,
         "caduta": None, "azzerati": 0,
         "flusso": os.path.basename(flusso), "fotogrammi": fot}
    percorso = os.path.join(lavoro, f"{etichetta}-misura.json")
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False)
    return percorso


class FintiArgomenti:
    def __init__(self, misura, lavoro):
        self.misura, self.lavoro = misura, lavoro
        self.esiti, self.certifica, self.quanti = "", False, 400


def certifica(lavoro):
    """⭐ LA CERTIFICAZIONE DELLO STRUMENTO — quattro cose, e tutte e quattro
    senza il prodotto, senza GNOME e senza rete (`CODER.md` §3.3).

      1. il GIUDICE di A1 sa dire tutt'e due le cose (il suo `--certifica`);
      2. ⛔ i MIEI B e T sono IDENTICI ai suoi sulle stesse due immagini —
         senza questo controllo qui ci sarebbe un secondo giudice;
      3. ⭐ il CRONOMETRO trova il primo pixel vero dove sappiamo che sta, e
         dice il ROSSO quando quel pixel arriva tardi o non arriva mai;
      4. ⛔ lo ZERO ha un codice suo e non si traveste da «il desktop non c'e'».
    """
    os.makedirs(lavoro, exist_ok=True)
    dimmi("== O1 · 04-b31 — la certificazione dello STRUMENTO (senza il prodotto)")
    esito = 0

    dimmi("\n-- 1. il giudice dei pixel e' quello di A1, e sa dire di si' e di no")
    if a1.certifica(lavoro) != 0:
        dimmi(f"   {ROSSO}⛔ il giudice di A1 non si certifica: qui non si "
              f"giudica niente{GRIGIO}")
        return 2

    dimmi("\n-- 2. ⛔ i MIEI conti contro i SUOI, sulle stesse due immagini")
    for nome, atteso in (("finta-vuota", "VUOTO"), ("finta-shell", "SHELL")):
        png = os.path.join(lavoro, f"{nome}.png")
        suo = a1.giudica_immagine(png, lavoro, nome, 1920, 1080)
        barra = os.path.join(lavoro, f"{nome}-barra.rgb")
        with open(barra, "rb") as f:
            d = f.read()
        mio = bt_di_una_fascia(d, 0, 1920)
        pari = (suo["B"] == mio["B"] and suo["T"] == mio["T"]
                and abs(suo["salto_bordo"] - mio["salto_bordo"]) < 0.01
                and suo["fronti_nella_barra"] == mio["fronti_nella_barra"])
        segno = VERDE + "OK" + GRIGIO if pari else ROSSO + "NO" + GRIGIO
        dimmi(f"   {segno}  {nome}: A1 salto {suo['salto_bordo']} fronti "
              f"{suo['fronti_nella_barra']} · io salto {mio['salto_bordo']} "
              f"fronti {mio['fronti_nella_barra']}")
        if not pari:
            dimmi(f"        ⛔ i due conti DIVERGONO: allora questo file e' un "
                  f"secondo giudice, e non deve esserlo")
            esito = 2
        if a1.verdetto(mio)[1] != atteso:
            dimmi(f"        ⛔ e il mio verdetto e' {a1.verdetto(mio)[1]}, "
                  f"atteso {atteso}")
            esito = 2
    if esito:
        return esito

    dimmi("\n-- 3. ⭐ il CRONOMETRO, su un giro FABBRICATO di cui si sa la "
          "risposta")
    # ⚠ Tre casi, e i tre codici d'uscita che devono uscire.  ⛔ Un banco che
    #   sapesse dire solo «verde» non saprebbe dire niente.
    casi = [
        # (etichetta, vuoti, pieni, t0, passo, uscita attesa, che cosa prova)
        ("cert-presto", 0, 6, 1.20, 0.02, 0,
         "il primo fotogramma E' gia' il desktop, a 1,20 s ⇒ VERDE"),
        ("cert-tardi", 0, 6, 5.20, 0.02, 1,
         "il desktop c'e' subito ma a 5,20 s ⇒ ROSSO TARDI (il difetto vivo)"),
        ("cert-vuoti-prima", 4, 4, 1.20, 1.00, 1,
         "⛔ quattro fotogrammi VUOTI a 1,20 s e il desktop solo a 5,20 s: "
         "⇒ ROSSO — un vuoto spedito subito NON e' una cura"),
        ("cert-mai", 6, 0, 1.20, 0.02, 3,
         "fotogrammi si', desktop mai ⇒ ROSSO MAI"),
    ]
    for et, vuoti, pieni, t0, passo, atteso, dice in casi:
        p = finta_misura(lavoro, et, vuoti, pieni, t0, passo)
        if p is None:
            dimmi(f"   {ROSSO}NO{GRIGIO}  {et}: non ho potuto fabbricare il giro")
            return 2
        u = principale(FintiArgomenti(p, lavoro))
        segno = VERDE + "OK" + GRIGIO if u == atteso else ROSSO + "NO" + GRIGIO
        dimmi(f"   {segno}  {et}: uscita {u}, attesa {atteso} — {dice}\n")
        if u != atteso:
            esito = 2

    dimmi("-- 4. ⛔ e il banco RIFIUTA DI INDOVINARE quando i conti non tornano")
    # ⛔ Il guasto innestato e' nella MISURA, non nel flusso: si toglie un
    #    fotogramma dalla lista degli arrivi e si lascia il flusso intero.
    #    ⚠ Senza questo caso, il controllo che rifiuta di allineare due liste di
    #      lunghezza diversa non sarebbe mai stato esercitato apposta — e quel
    #      controllo e' l'unica cosa che impedisce di attribuire a un
    #      fotogramma l'ora di un altro.
    p = finta_misura(lavoro, "cert-conti", 2, 4, 1.20, 0.02)
    with open(p, encoding="utf-8") as f:
        m = json.load(f)
    m["fotogrammi"] = m["fotogrammi"][:-1]
    with open(p, "w", encoding="utf-8") as f:
        json.dump(m, f)
    u = principale(FintiArgomenti(p, lavoro))
    segno = VERDE + "OK" + GRIGIO if u == 2 else ROSSO + "NO" + GRIGIO
    dimmi(f"   {segno}  cert-conti: uscita {u}, attesa 2 — 6 fotogrammi "
          f"decodificati e 5 arrivati ⇒ NON GIUDICABILE\n")
    if u != 2:
        esito = 2

    dimmi("-- 5. ⛔ lo ZERO ha un codice suo, e non e' «il desktop non c'e'»")
    p = finta_misura(lavoro, "cert-zero", 0, 3, 1.2, 0.02)
    with open(p, encoding="utf-8") as f:
        m = json.load(f)
    m["fotogrammi"] = []
    with open(p, "w", encoding="utf-8") as f:
        json.dump(m, f)
    u = principale(FintiArgomenti(p, lavoro))
    segno = VERDE + "OK" + GRIGIO if u == 5 else ROSSO + "NO" + GRIGIO
    dimmi(f"   {segno}  cert-zero: uscita {u}, attesa 5")
    if u != 5:
        esito = 2

    dimmi("")
    if esito == 0:
        dimmi(f"   {VERDE}⭐ lo strumento sa dire VERDE, TARDI, MAI e ZERO, e "
              f"i suoi conti sono quelli di A1{GRIGIO}")
    else:
        dimmi(f"   {ROSSO}⛔ lo strumento NON e' certificato: non giudica "
              f"niente{GRIGIO}")
    return esito


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="O1 — LOGIN → primo pixel VERO")
    p.add_argument("--misura", help="il <etichetta>-misura.json di 04-b31-cliente.py")
    p.add_argument("--lavoro", default="/tmp/04-b31")
    p.add_argument("--quanti", type=int, default=400,
                   help="quanti fotogrammi al massimo si decodificano")
    p.add_argument("--esiti", default="")
    p.add_argument("--certifica", action="store_true")
    sys.exit(principale(p.parse_args()))
