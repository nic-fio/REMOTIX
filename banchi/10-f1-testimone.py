#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
10-f1-testimone — ⭐⭐ IL TESTIMONE CHE FA VEDERE IL DESKTOP REMOTO.
                     Un'IMMAGINE, non un contatore.
===========================================================================

    python3 banchi/10-f1-testimone.py scatta --utente provanic1 \\
            --fuori /tmp/desktop.png
    python3 banchi/10-f1-testimone.py scatta --utente provanic1 \\
            --fuori /tmp/desktop.png --marca f1-taratura
    python3 banchi/10-f1-testimone.py --certifica

Esce **0** se ha guardato e il giudizio chiesto regge · **1** se ha guardato e
il giudizio NON regge (rosso) · ⛔ **3** se **non ha potuto guardare** — e il
terzo esito non e' un rosso: e' *«non ho guardato»*, che in questo progetto e'
una cosa diversa e va detta con parole diverse (`LEZIONI.md` §1.9, e la regola
5 del preambolo: **`None` non e' zero**).

===========================================================================
⛔⛔ PERCHE' ESISTE — quattro strade provate, e nessun quadro
===========================================================================

Fino al 25 agosto 2026 la fase 10 non si chiudeva per una ragione sola: ⛔ **non
si riusciva a GUARDARE il desktop remoto.**  Il coordinamento aveva provato:

  1. lo **scatto del figlio** — `SIGUSR1` al figlio col `--rilievo` acceso:
     `cattura.bgrx` restava **a zero byte**;
  2. la **fotografia dello schermo** del portatile — `grim` risponde
     *«compositor doesn't support wlr-screencopy-unstable-v1»*: GNOME non lo da';
  3. la **tela letta dalla pagina** (`canvas.toDataURL`) via Marionette — ⛔ ogni
     riattacco faceva scadere la sessione WebDriver, e la riapertura **buttava
     giu' la sessione RCP**: il server registrava *«non lo guarda piu' nessuno»*
     pochi istanti dopo;
  4. il **conteggio dei fotogrammi** — dice **quanti**, ⛔ non **che cosa**.

===========================================================================
⭐ LA STRADA SCELTA, E PERCHE' — «il cliente che decodifica»
===========================================================================

Questo testimone prende la **terza via del quadro dell'incarico**: si attacca
alla sessione col **cliente di prova** (`banchi/01-b3-cliente.py`), si fa dare i
fotogrammi **dal filo** con `--video-scrivi`, e li da' a **`ffmpeg`**, che sulla
macchina di prova c'e'.  ⇒ Ne esce un **PNG**.

⭐ Le tre ragioni per cui questa e' la strada, e non le altre:

  · ⛔ **Non ha un browser dentro.**  La strada della tela e' morta sulla
    fragilita' di WebDriver, non sui pixel: ogni riattacco riapriva la sessione
    e staccava il cliente.  Qui non c'e' niente da riattaccare — **un processo
    solo, che apre, guarda e chiude**.
  · ⭐⭐ **Non rompe la sessione che sta guardando**, ed e' `[M]` sul registro del
    server, non creduto — ⚠ **ma non nel modo che avevo scritto qui la prima
    volta, e la correzione vale piu' della frase**.  Credevo che due clienti
    dello stesso utente convivessero (I4, «occupati adesso: N»).  ⛔ **Non
    convivono**: `[M]` 25 agosto 2026, 15:31 — con uno spettatore gia' attaccato
    a `provanic1`, il testimone e' stato **RESPINTO**:
        `posto NEGATO a provanic1 …: lo occupa un altro client di questo stesso
         utente (occupati: 1) — quell'occupante ha dato un segno di vita 916 ms
         fa, e lo sfratto NON e' scattato` · `congedo motivo=0x0f`
    ⇒ ⭐ **E questo e' l'esito giusto**: il prodotto **non sfratta chi guarda per
      far posto a chi arriva**, e il testimone — invece di inventarsi
      un'immagine — dice **«NON HO GUARDATO»** e esce **3**.  `[M]` Lo
      spettatore e' rimasto attaccato: nel registro, in quel tratto, **nessuna**
      riga «l'ultima sessione se ne va» e **nessuna** «non lo guarda piu'
      nessuno».
    ⛔ **E il limite si dichiara**: finche' qualcuno guarda quella sessione, il
      testimone **non puo' guardarla**.  ⚠ Non e' un ripiego da aggiungere: lo
      sfratto esiste gia' e scatta sul cliente **muto** (soglia 15 000 ms) —
      forzarlo qui vorrebbe dire staccare l'utente per fotografarlo.
  · ⭐ **Gira da solo**, senza terminale e senza nessuno che guardi: e' la
    condizione posta dall'incarico.

⭐ E una cosa che il prodotto fa gia' bene, e che questo testimone sfrutta:
   all'attacco su desktop **fermo** il figlio si costringe a consegnare —
   `[M]` *«una CHIAVE e' dovuta e la scena e' ferma da 400 ms: riavvio il flusso
   per farmi consegnare un fotogramma»*.  ⇒ Un solo fotogramma basta, e su un
   desktop immobile il testimone vede lo stesso.  ⚠ Senza quella riga servirebbe
   `--sveglia`, che invece resta l'ultima risorsa.

⚠ **E si dichiara dove guarda**, perche' non e' l'ultimo anello: il testimone
vede i pixel **DOPO il filo e PRIMA del decodificatore del browser** — cioe'
esattamente i byte che Firefox riceverebbe.  ⛔ Quel che questo testimone **non**
puo' vedere e' un difetto che nascesse **dentro** la tela della pagina (uno
`drawImage` sbagliato, un `bitmaprenderer` storto).  ⇒ Per quelli serve la tela,
e questo strumento non la sostituisce: **la precede**.

===========================================================================
⛔⛔ COME SI PROVA CHE IL TESTIMONE VEDE — ed e' la meta' che vale
===========================================================================

Un testimone che restituisce un PNG **nero** e uno che restituisce il desktop
**hanno la stessa faccia** dal lato del codice.  ⇒ Si tara, come ogni metro di
questa fase (`LEZIONI.md` §1.33):

  1. ⭐ **il controllo positivo**: si dipinge nel desktop remoto una marca
     **leggibile a macchina** (`04-b30-scena --movimento marca --giro NOME`) e si
     verifica che il testimone la **ritrovi** — col **lettore certificato**
     `banchi/03-marca.py`, che non e' di questo banco e non si tocca.  ⭐ La marca
     porta dentro i pixel il **nome del giro**: non basta che ci sia *una* marca,
     dev'essere **la mia**.  Un testimone che guardasse il desktop di un altro
     inquilino qui darebbe **rosso**.
  2. ⛔ **il controllo negativo**: col desktop **nero** il testimone deve dirlo,
     non restituire un'immagine qualunque spacciandola per il desktop.  ⭐ Un PNG
     che c'e' **non e'** un PNG che mostra qualcosa.
     `[M]` Fatto sul vero, 25 agosto 2026: fondo di `provanic3` messo a
     `#000000` ⇒ **QUASI-NERO**, media **0,28**, accesi **0,00121**.  ⭐ E sotto
     la barra di GNOME il fotogramma e' nero **byte per byte** (accesi
     0,00000000, luma massima 1): il metro non e' cieco, e' **sensibile a un
     pixel su ottocento**.  ⛔ Un desktop GNOME non e' mai «tutto nero» —
     l'orologio in alto non si spegne — ed e' per questo che c'e' «quasi-nero».
  3. ⛔ **e se non ha potuto guardare torna `None`**: zero fotogrammi presi dal
     filo, `ffmpeg` che non decodifica, la sessione che non si apre — sono
     tutti *«non ho guardato»*, e **nessuno di loro e' «e' nero»**.

===========================================================================
⛔⛔ LA TRAPPOLA DELL'ESC — chi usa questo testimone la incontrera'
===========================================================================

Per vedere le finestre come finestre bisogna **uscire dalla vista d'insieme** di
GNOME, e si fa mandando **ESC** (`banchi/09-b72-tasto.py --tasti 1`, fase 9).
⛔ **Ma ESC e' anche il tasto che chiude un dialogo modale.**

`[M]` 25 agosto 2026: Firefox nella sessione remota si ferma sul dialogo
*«Profile Missing — Your Firefox profile cannot be loaded»*.  Mandando ESC prima
di scattare, il dialogo **spariva** e lo scatto mostrava un desktop **vuoto** —
cioe' esattamente il sintomo su cui la fase si era arenata: *«il processo e'
vivo e qualcosa disegna, ma nessuno ha mai visto la sua finestra»*.
⇒ ⭐ **Si scatta PRIMA senza ESC, e solo dopo, se serve, si manda ESC e si
  riscatta.**  Due scatti, non uno — e la differenza fra i due e' un dato, non
  un fastidio.

===========================================================================
⚠ DOVE GIRA CHE COSA, e perche' e' spezzato in due
===========================================================================

  · la **presa** (cliente + `ffmpeg`) gira **sulla macchina di prova, dentro il
    contenitore**: li' c'e' `aioquic`, e sull'host no;
  · la **lettura dei pixel** gira **qui**, sul portatile: `numpy` e `Pillow`
    stanno qui e nel contenitore non ci sono.  ⚠ E' lo stesso confine che
    `03-marca.py` dichiara da solo in `np_o_muori()`.

⇒ Il PNG viaggia indietro con `scp`.  ⛔ E se `numpy` non c'e' nemmeno qui, il
  testimone **non finge**: torna «non ho potuto giudicare», che e' `None`.
"""

import argparse
import base64
import glob
import importlib.util
import json
import os
import shlex
import struct
import subprocess
import sys
import tempfile
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ── i predefiniti della macchina di prova (tutti scavalcabili da riga di
#    comando: ⛔ `CODER.md` §2-bis, una strada sola e nessuna variabile
#    d'ambiente che cambi la grandezza misurata) ─────────────────────────────
MACCHINA = "nicfio@192.168.0.2"
PAROLA_SUDO = "nicfio"
ENTRA = "/media/REMOTIX/enter.sh"
INDIRIZZO = "192.168.0.2"
PORTA = 8400
ALBERO = "/media/REMOTIX/src/10fin-src"
LAV = "/media/REMOTIX/tmp/10f1"
PAROLA_FILE = "/media/REMOTIX/tmp/10nic/parola"

# ⚠ Dentro il contenitore i due innesti si vedono con altri nomi (`enter.sh`).
def _dentro(percorso):
    if percorso.startswith("/media/REMOTIX/src/"):
        return "/srv/src/" + percorso[len("/media/REMOTIX/src/"):]
    if percorso.startswith("/media/REMOTIX/"):
        return "/srv/remotix/" + percorso[len("/media/REMOTIX/"):]
    return percorso


# ═══════════════════════════════════════════════════════════════════════════
# LE SOGLIE DEL GIUDIZIO — ⛔ dichiarate qui e stampate in ogni esito, perche'
# «nero» e «disegnato» sono un verdetto, e un verdetto senza il suo metro e'
# un'opinione.
# ═══════════════════════════════════════════════════════════════════════════
LUMA_NERO = 16.0       # sotto questa luma un pixel e' «spento»
FRAZIONE_NERO = 0.001  # meno dell'0,1 % di pixel accesi ⇒ lo schermo e' NERO
# ⛔ «TINTA UNITA» SI MISURA SU QUANTO SCHERMO E' DEL COLORE PIU' COMUNE, non sul
#    numero di colori distinti — e la prima stesura sbagliava proprio qui.
#    `[M]` 25 agosto 2026, guasto G8 di `--certifica`: uno schermo **nero con
#    sopra la marca** ha **due** colori soli (nero e bianco) e veniva
#    dichiarato «tinta unita».  ⚠ Cioe' il testimone buttava via l'unica prova
#    che aveva guardato davvero, e lo faceva con un verdetto plausibile.
#    ⇒ Il criterio giusto e' **quanta parte dello schermo NON e' il fondo**.
FRAZIONE_PIATTO = 0.001
# ⭐⭐ «QUASI NERO» — e la soglia e' MISURATA, non scelta.  `[M]` 25 agosto 2026,
#    il controllo negativo sul vero: desktop di `provanic3` col fondo messo a
#    `#000000`, catturato dal filo.  Sotto la barra di GNOME (y ≥ 40) il
#    fotogramma e' **nero byte per byte**: accesi 0,00000000, luma massima **1**.
#    ⛔ Ma la barra in alto — 40 righe su 1080 — porta l'orologio e le icone, e
#    con quelle lo schermo intero fa accesi **0,00121**: appena SOPRA la soglia
#    del nero, cioe' un desktop GNOME non e' MAI «tutto nero».
#    ⚠ Un testimone che si fermasse a «disegnato» direbbe il vero e non
#      servirebbe a niente: quello schermo non ha niente sopra.
#    ⇒ La media dei pixel separa i due mondi con un fattore cento:
#         desktop nero + barra   media **0,28**
#         desktop vero           media **34,3** (vuoto) … **106,9** (con la scena)
#      La soglia si mette a **2,0**, cioe' in mezzo al vuoto fra i due.
MEDIA_QUASI_NERO = 2.0

# BT.709, la stessa matrice che dichiara `03-marca.py`: qui serve solo a fare
# UN numero da tre canali.
PESI_LUMA = (0.2126, 0.7152, 0.0722)


def _marca_modulo():
    """⭐ Il lettore certificato si IMPORTA, non si riscrive.

    ⛔ `03-marca.py` e' l'unica cosa della catena che non si tocca: e' lui che
       decide se la marca c'e'.  Riscriverne la geometria qui vorrebbe dire
       avere due lettori che possono divergere in silenzio — e il giorno che
       divergono, il rosso lo darebbe quello sbagliato.
    """
    perc = os.path.join(QUI, "03-marca.py")
    if not os.path.exists(perc):
        return None
    spec = importlib.util.spec_from_file_location("marca03", perc)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _numpy_o_niente():
    """⛔ Torna `None` se non c'e', e chi chiama deve dire «non ho giudicato».

    ⚠ La tentazione era un ripiego in Python puro che «piu' o meno» dice se e'
      nero.  Sarebbe un metro diverso da quello con cui si e' tarato, cioe' la
      forma d'errore che l'incarico chiede di non fare: un numero al posto di
      una misura.
    """
    try:
        import numpy
        return numpy
    except ImportError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDIZIO SUI PIXEL — «c'e' un PNG» non e' «il PNG mostra qualcosa»
# ═══════════════════════════════════════════════════════════════════════════
def giudica(percorso):
    """Dato un PNG, dice **che cosa c'e' dentro**.

    Torna un dizionario, oppure ⛔ **`None`** se non ha potuto guardare (file
    che non c'e', file illeggibile, `numpy`/`Pillow` che mancano).

    Le chiavi:
      verdetto   «nero» · «tinta-unita» · «disegnato»
      larghezza, altezza, media, dev, minimo, massimo
      colori     quanti colori distinti
      accesi     frazione di pixel con luma > LUMA_NERO
      diversi    frazione di pixel che si scostano dal colore piu' comune
    """
    if not percorso or not os.path.exists(percorso):
        return None
    if os.path.getsize(percorso) == 0:
        return None
    np = _numpy_o_niente()
    if np is None:
        return None
    try:
        from PIL import Image
        img = np.asarray(Image.open(percorso).convert("RGB"))
    except Exception:
        # ⛔ Un PNG troncato o non-PNG e' «non ho guardato», non «e' nero»:
        #    e' esattamente la ferita che il preambolo chiama regola 5.
        return None
    if img.ndim != 3 or img.shape[2] != 3 or img.size == 0:
        return None

    h, w = img.shape[0], img.shape[1]
    f = img.astype("float32")
    luma = (f[:, :, 0] * PESI_LUMA[0] + f[:, :, 1] * PESI_LUMA[1]
            + f[:, :, 2] * PESI_LUMA[2])
    accesi = float((luma > LUMA_NERO).mean())

    piatto = img.reshape(-1, 3)
    # ⚠ Su 1920x1080 `np.unique` sulle righe costa; si campiona 1 pixel su 4 in
    #   ciascuna direzione.  ⛔ E si DICE, perche' «colori distinti» qui vuol
    #   dire «distinti nel campione», e su un'immagine con pochissimi colori —
    #   che e' il caso che decide «tinta unita» — il campione li vede tutti.
    campione = img[::4, ::4].reshape(-1, 3)
    colori = int(len(np.unique(campione, axis=0)))
    # il colore piu' comune, e quanta parte dello schermo NON e' quello
    vista = np.ascontiguousarray(campione).view(
        np.dtype((np.void, campione.dtype.itemsize * 3)))
    _u, conti = np.unique(vista, return_counts=True)
    diversi = float(1.0 - conti.max() / float(len(campione)))

    media = float(f.mean())
    if accesi < FRAZIONE_NERO:
        verdetto = "nero"
    elif media < MEDIA_QUASI_NERO:
        # ⭐ «c'e' uno schermo, e sopra non c'e' niente» — e va detto con parole
        #    sue, perche' e' l'esito che il controllo negativo deve produrre su
        #    un desktop GNOME, dove la barra in alto non si spegne mai.
        verdetto = "quasi-nero"
    elif diversi < FRAZIONE_PIATTO:
        verdetto = "tinta-unita"
    else:
        verdetto = "disegnato"

    return {
        "verdetto": verdetto,
        "larghezza": w, "altezza": h,
        "media": round(media, 3),
        "dev": round(float(f.std()), 3),
        "minimo": int(img.min()), "massimo": int(img.max()),
        "colori": colori,
        "accesi": round(accesi, 6),
        "diversi": round(diversi, 6),
        "soglie": {"luma_nero": LUMA_NERO, "frazione_nero": FRAZIONE_NERO,
                   "media_quasi_nero": MEDIA_QUASI_NERO,
                   "frazione_piatto": FRAZIONE_PIATTO},
    }


def leggi_la_marca(percorso, giri):
    """⭐ Il controllo positivo: la marca c'e', ed e' **la mia**?

    `giri` e' l'elenco dei nomi di giro che ho fatto girare io.  ⛔ L'inversione
    e' un ELENCO e non un'indovinata: la marca porta 32 bit di FNV-1a, che non
    si invertono (e' la regola che `03-marca.py` scrive da se').

    Torna:
      `None`                          ⛔ non ho potuto guardare (niente numpy,
                                      niente lettore, fotogramma troppo piccolo
                                      perche' la marca ci stia)
      {"c_e": False, "perche": …}     la marca NON c'e' — ed e' un rosso, non un
                                      «non lo so»
      {"c_e": True, "giro": …, "mio": bool, "disegno": …, "istante_us": …}
    """
    np = _numpy_o_niente()
    m = _marca_modulo()
    if np is None or m is None:
        return None
    if not percorso or not os.path.exists(percorso) \
            or os.path.getsize(percorso) == 0:
        return None
    try:
        img = m.carica(percorso)
    except Exception:
        return None
    r = m.leggi_marca(img)
    if not r.get("c_e"):
        # ⛔ LA DISTINZIONE CHE COSTA CARO SE SI PERDE: «la marca non ci
        #    starebbe» (fotogramma troppo piccolo) e' **non ho guardato**;
        #    «la marca non c'e'» e' un rosso.  `03-marca.py` le tiene gia'
        #    separate mettendo la chiave `serve` solo nella prima.
        if "serve" in r:
            return None
        return {"c_e": False, "perche": r.get("perche"),
                "contrasto": r.get("contrasto")}
    numero = r.get("giro")
    nomi = {m.fnv1a32(g): g for g in giri}
    return {"c_e": True,
            "giro_numero": numero,
            "giro": nomi.get(numero),
            "mio": numero in nomi,
            "disegno": r.get("disegno"),
            "istante_us": r.get("istante_us"),
            "contrasto": r.get("contrasto")}


# ═══════════════════════════════════════════════════════════════════════════
# LA PRESA — sulla macchina di prova, dentro il contenitore
# ═══════════════════════════════════════════════════════════════════════════
def _ssh(comando, secondi=180, macchina=MACCHINA):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o",
                        "ConnectTimeout=15", macchina, comando],
                       capture_output=True, timeout=secondi)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def _nel_contenitore(script, secondi=180, macchina=MACCHINA,
                     parola_sudo=PAROLA_SUDO, lav=LAV):
    """Fa girare uno script bash **dentro** il contenitore, da amministratore.

    ⛔ Lo script viaggia in **base64** e non dentro le virgolette: due livelli
       di shell (ssh e `enter.sh -lc`) si mangiano gli apici, e un comando
       storto qui darebbe un «zero fotogrammi» che somiglia in tutto a un
       server muto.  ⚠ E' la forma d'errore E2 del catalogo dei banchi.
    ⛔ E la parola di sudo passa da `printf`, che e' un builtin: non compare in
       `argv` di nessun processo (`FASE10-PREAMBOLO` §«la macchina di prova»).
    """
    b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
    riga = ("printf '%%s' '%s' | base64 -d > %s/passo.sh && "
            "printf '%%s\\n' %s | bash %s --root "
            "\"bash %s/passo.sh\""
            % (b64, lav, parola_sudo, ENTRA, _dentro(lav)))
    return _ssh(riga, secondi=secondi, macchina=macchina)


def _leggi_esito_cliente(testo):
    """Dal registro del cliente: **quanti fotogrammi sono ARRIVATI**.

    ⛔ Torna `None` quando non e' arrivato niente — e non zero.  `LEZIONI.md`
       §1.30 dice di contare quanta sollecitazione e' ARRIVATA prima di
       giudicare: qui la sollecitazione **e'** il fotogramma, e un banco che
       decodificasse un file vuoto direbbe «schermo nero» su un server che non
       ha mai avuto occasione di mandare niente.
    """
    fotogrammi = None
    chiavi = None
    misura = None
    sessione = None
    for r in testo.splitlines():
        if "SESSIONE:" in r:
            sessione = r.strip()
        if "[vid]" not in r:
            continue
        if "nessun fotogramma" in r:
            continue
        # «   [vid]  12 fotogrammi (2 chiavi), 1920x1080, scritti in …»
        pezzi = r.split("[vid]", 1)[1].strip().split()
        try:
            fotogrammi = int(pezzi[0])
            chiavi = int(pezzi[2].lstrip("("))
            misura = pezzi[4].rstrip(",")
        except Exception:
            continue
    if not fotogrammi:
        return None
    return {"fotogrammi": fotogrammi, "chiavi": chiavi, "misura": misura,
            "sessione": sessione}


SCRIPT_PRESA = r"""
set -u
LAV=%(lav_dentro)s
CLIENTE=%(cliente)s
TUTTI=%(tutti)s
rm -f "$LAV/flusso.264" "$LAV/scatto.png" "$LAV/cliente.log"
rm -f "$LAV"/scatto-[0-9][0-9][0-9].png
timeout %(tetto)d python3 -u "$CLIENTE" \
    --indirizzo %(indirizzo)s --porta %(porta)d \
    --utente %(utente)s --parola-file %(parola)s \
    --video-scrivi "$LAV/flusso.264" --resta %(resta).1f %(altro)s \
    > "$LAV/cliente.log" 2>&1
echo "=== CLIENTE rc=$? ==="
cat "$LAV/cliente.log"
echo "=== FFMPEG ==="
if [ -s "$LAV/flusso.264" ]; then
    # ⛔ `-update 1` riscrive SEMPRE lo stesso file: vince l'ULTIMO fotogramma
    #    decodificato, che e' quello che il desktop mostra adesso.  Prendere il
    #    primo darebbe la chiave d'apertura, cioe' lo schermo di un secondo fa.
    ffmpeg -hide_banner -loglevel error -i "$LAV/flusso.264" \
           -vsync 0 -update 1 -y "$LAV/scatto.png"
    echo "rc=$?"
    ls -l "$LAV/scatto.png" 2>/dev/null || echo "⛔ nessuno scatto"
    # ⭐⭐ E LA SEQUENZA, quando la si chiede (`--tutti`) — 25 agosto 2026.
    #
    # ⛔ Non e' un lusso: **l'ultimo fotogramma da solo mente per omissione.**
    #    `[M]` Il dialogo «Profile Missing» di Firefox e' stato trovato cosi' —
    #    compariva a meta' della presa e spariva prima della fine, e sull'ultimo
    #    scatto non c'era.  ⇒ Un desktop che ATTRAVERSA uno stato non lo mostra
    #    nell'istante finale, e chi guarda solo quello conclude «non c'e'
    #    niente» — che e' un `[?]` spacciato per un `[M]`.
    if [ -n "$TUTTI" ] && [ -s "$LAV/flusso.264" ]; then
        echo "=== FFMPEG TUTTI ==="
        ffmpeg -hide_banner -loglevel error -i "$LAV/flusso.264" \
               -vsync 0 -y "$LAV/scatto-%%03d.png"
        echo "rc=$?"
        ls "$LAV"/scatto-*.png 2>/dev/null | wc -l
    fi
else
    echo "⛔ il flusso e' vuoto o non c'e': niente da decodificare"
fi
"""


def scatta(utente, fuori, resta=6.0, porta=PORTA, indirizzo=INDIRIZZO,
           albero=ALBERO, lav=LAV, parola_file=PAROLA_FILE,
           macchina=MACCHINA, parola_sudo=PAROLA_SUDO, sveglia=None,
           loquace=False, tutti=False):
    """⭐ Tira giu' un PNG del desktop remoto di `utente`, e lo scrive in `fuori`.

    Torna un dizionario con `png` e i conti della presa, oppure ⛔ **`None`** se
    **non ha potuto guardare**.  ⚠ `None` non e' «lo schermo era nero».
    """
    altro = ""
    if sveglia:
        # ⭐ LA SVEGLIA, e serve per un motivo misurato: `[M]` il registro del
        #    figlio dice «attese a vuoto (scena ferma: Mutter consegna solo
        #    quando qualcosa cambia)».  Su un desktop **immobile** il palco puo'
        #    non consegnare niente dopo la chiave d'apertura.  ⇒ Un cambio di
        #    tela obbliga la catena a rifare un fotogramma intero.
        # ⚠ Ma cambia quel che il desktop VEDE (si ridimensiona), quindi e'
        #   SPENTA per predefinito e chi l'accende lo dichiara.
        altro = "--adatta %s@1.0 --adatta %dx%d@2.0" % (
            sveglia, 1920, 1080)

    script = SCRIPT_PRESA % {
        "lav_dentro": _dentro(lav),
        "cliente": _dentro(albero) + "/banchi/01-b3-cliente.py",
        "tetto": int(resta) + 60,
        "indirizzo": indirizzo, "porta": porta, "utente": utente,
        "parola": _dentro(parola_file), "resta": resta, "altro": altro,
        "tutti": "1" if tutti else "",
    }
    rc, out, err = _nel_contenitore(script, secondi=int(resta) + 120,
                                    macchina=macchina,
                                    parola_sudo=parola_sudo, lav=lav)
    if loquace:
        sys.stderr.write(out + err)
    conti = _leggi_esito_cliente(out)
    if conti is None:
        return {"png": None, "conti": None,
                "perche": ("⛔ NON HO GUARDATO: nessun fotogramma e' arrivato "
                           "dal filo.  ⚠ Non e' «lo schermo era nero»: e' che "
                           "il palco non ha consegnato niente, o la sessione "
                           "non si e' aperta"),
                "registro": (out + err)[-1500:]}
    if "⛔ nessuno scatto" in out or "rc=0" not in out.split("=== FFMPEG ===")[-1]:
        return {"png": None, "conti": conti,
                "perche": ("⛔ NON HO GUARDATO: %d fotogrammi sono arrivati ma "
                           "`ffmpeg` non ha prodotto lo scatto"
                           % conti["fotogrammi"]),
                "registro": (out + err)[-1500:]}

    os.makedirs(os.path.dirname(os.path.abspath(fuori)) or ".", exist_ok=True)
    if os.path.exists(fuori):
        os.unlink(fuori)          # ⛔ mai giudicare il file di un giro prima
    p = subprocess.run(["scp", "-o", "BatchMode=yes", "-q",
                        "%s:%s/scatto.png" % (macchina, lav), fuori],
                       capture_output=True, timeout=120)
    if p.returncode != 0 or not os.path.exists(fuori):
        return {"png": None, "conti": conti,
                "perche": "⛔ NON HO GUARDATO: lo scatto non e' arrivato qui (%s)"
                          % p.stderr.decode("utf-8", "replace").strip()[:200],
                "registro": (out + err)[-1500:]}
    sequenza = []
    if tutti:
        # ⭐ La sequenza sta ACCANTO allo scatto, con lo stesso nome piu' il
        #   numero: chi guarda una cartella capisce da se' che sono lo stesso
        #   giro.  ⚠ E se non arriva, NON si sporca l'esito dello scatto: lo
        #   scatto e' arrivato, e questo e' un di piu' dichiarato.
        radice = os.path.splitext(os.path.abspath(fuori))[0]
        for vecchio in glob.glob(radice + "-[0-9][0-9][0-9].png"):
            os.unlink(vecchio)
        q = subprocess.run(["bash", "-c",
                            "scp -o BatchMode=yes -q '%s:%s/scatto-[0-9][0-9][0-9].png' %s"
                            % (macchina, lav, shlex.quote(
                                os.path.dirname(radice) or "."))],
                           capture_output=True, timeout=300)
        if q.returncode == 0:
            for f in sorted(glob.glob(os.path.join(
                    os.path.dirname(radice) or ".", "scatto-[0-9][0-9][0-9].png"))):
                nuovo = radice + "-" + os.path.basename(f).split("-")[1]
                os.replace(f, nuovo)
                sequenza.append(nuovo)
    return {"png": fuori, "conti": conti, "perche": None,
            "sequenza": sequenza, "registro": (out + err)[-1500:]}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL CONTROLLO CHE NON SI PUO' SALTARE: il testimone DISTURBA la sessione?
# ═══════════════════════════════════════════════════════════════════════════
def guarda_il_registro(righe_prima, macchina=MACCHINA,
                       parola_sudo=PAROLA_SUDO,
                       registro="/media/REMOTIX/tmp/10nic/registro.log"):
    """⭐ Le righe del server scritte DA `righe_prima` IN POI, filtrate su quel
       che direbbe un distacco altrui.

    ⛔ Serve al predicato *«il testimone non rompe la sessione che sta
       osservando»*: il server lo scrive da se' — *«l'ULTIMA sessione di X se ne
       va»*, *«non lo guarda piu' nessuno»*.  ⇒ Se quelle righe compaiono
       mentre un altro cliente e' ancora attaccato, il testimone ha fatto danno.
    """
    rc, out, _ = _ssh("printf '%%s\\n' %s | sudo -S -p '' tail -n +%d %s"
                      % (parola_sudo, righe_prima + 1, registro),
                      macchina=macchina)
    if rc != 0:
        return None
    return out


def quante_righe(macchina=MACCHINA, parola_sudo=PAROLA_SUDO,
                 registro="/media/REMOTIX/tmp/10nic/registro.log"):
    # ⛔ NON `wc -l < file`: la ridirezione RUBA lo standard input a `sudo -S`,
    #    che allora chiede la parola a un terminale che non c'e' e — dopo tre
    #    tentativi — ⚠ **fa scattare il conto dei fallimenti di sudo**.
    #    `[M]` 25 agosto 2026, imparato sbagliandolo.
    rc, out, _ = _ssh("printf '%%s\\n' %s | sudo -S -p '' wc -l %s"
                      % (parola_sudo, registro), macchina=macchina)
    try:
        return int(out.strip().split()[0])
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CERTIFICAZIONE — sano → guasto → risanato, e i guasti si FANNO GIRARE
# ═══════════════════════════════════════════════════════════════════════════
def _dipingi(dove, larghezza, altezza, fondo, giro=None, disegno=7,
             istante_us=123456):
    """Costruisce un fotogramma finto, col lettore certificato.

    ⚠ E' l'unico posto dove questo banco DIPINGE: la marca la dipinge
      `03-marca.py`, cioe' lo stesso file che poi la legge — che e' come si
      certifica un lettore senza dover accendere la macchina.
    """
    np = _numpy_o_niente()
    m = _marca_modulo()
    if np is None or m is None:
        return False
    from PIL import Image
    if fondo == "nero":
        img = np.zeros((altezza, larghezza, 3), np.uint8)
    elif fondo == "grigio-pieno":
        img = np.full((altezza, larghezza, 3), 128, np.uint8)
    elif fondo == "rumore":
        img = np.random.RandomState(7).randint(
            0, 256, (altezza, larghezza, 3), dtype=np.uint8)
    else:                                   # «desktop»: una sfumatura
        yy = np.linspace(0, 1, altezza)[:, None]
        xx = np.linspace(0, 1, larghezza)[None, :]
        g = ((yy + xx) / 2 * 200 + 30).astype(np.uint8)
        img = np.repeat(g[:, :, None], 3, axis=2)
    if giro is not None:
        img = img.copy()
        m.dipingi_marca(img, disegno, istante_us, m.fnv1a32(giro))
    Image.fromarray(img).save(dove)
    return True


def certifica():
    """⛔ Un banco non e' finito finche' non lo si e' visto dare ROSSO.

    Ogni predicato di questo testimone ha qui il suo guasto, e il guasto **gira**:
    sano → guasto → risanato, contati e stampati.
    """
    np = _numpy_o_niente()
    if np is None or _marca_modulo() is None:
        print("⛔ NON HO POTUTO CERTIFICARE: senza `numpy`/`Pillow` e senza "
              "`03-marca.py` accanto, la lettura dei pixel non si fa.\n"
              "   ⚠ E questo NON e' un verde: e' il terzo esito.")
        return 3

    tmp = tempfile.mkdtemp(prefix="10-f1-certifica-")
    buoni = rossi = risanati = 0
    guasti = []

    def prova(nome, che, atteso, ottenuto):
        ok = (atteso == ottenuto)
        print("   %s %-42s atteso %-28s ottenuto %s"
              % ("✅" if ok else "⛔", nome + " · " + che,
                 repr(atteso), repr(ottenuto)))
        return ok

    print("═══ 10-f1-testimone --certifica ═══")
    print("  ⭐ SANO → ⛔ GUASTO → ⭐ RISANATO, su ciascun predicato\n")

    # ── P1 · «zero fotogrammi» e' NON HO GUARDATO, non «nero» ───────────────
    print("  P1 · il registro del cliente: quanti fotogrammi sono ARRIVATI")
    sano = ("   ⭐ SESSIONE: stato=1 tela=1920x1080\n"
            "   [vid]  12 fotogrammi (2 chiavi), 1920x1080, scritti in /x.264\n")
    g1 = "   ⭐ SESSIONE: stato=1\n   [vid]  ⛔ nessun fotogramma preso dal filo\n"
    g2 = "   ⛔ il cliente e' morto prima di aprire la sessione\n"
    a = _leggi_esito_cliente(sano)
    ok0 = prova("P1", "sano: 12 fotogrammi", 12, (a or {}).get("fotogrammi"))
    ok1 = prova("P1", "guasto G1 «nessun fotogramma» ⇒ None",
                None, _leggi_esito_cliente(g1))
    ok2 = prova("P1", "guasto G2 «cliente morto» ⇒ None",
                None, _leggi_esito_cliente(g2))
    ok3 = prova("P1", "risanato: 12 fotogrammi", 12,
                (_leggi_esito_cliente(sano) or {}).get("fotogrammi"))
    buoni += ok0; rossi += (ok1 + ok2); risanati += ok3
    if not (ok0 and ok1 and ok2 and ok3): guasti.append("P1")

    # ── P2 · il PNG che non c'e', o che non si legge, e' NON HO GUARDATO ────
    print("\n  P2 · lo scatto: «non l'ho letto» non e' «e' nero»")
    vero = os.path.join(tmp, "vero.png")
    _dipingi(vero, 640, 480, "desktop")
    ok0 = prova("P2", "sano: un PNG vero si giudica", "disegnato",
                (giudica(vero) or {}).get("verdetto"))
    ok1 = prova("P2", "guasto G3 file che non esiste ⇒ None",
                None, giudica(os.path.join(tmp, "non-c-e.png")))
    vuoto = os.path.join(tmp, "vuoto.png")
    open(vuoto, "wb").close()
    ok2 = prova("P2", "guasto G4 file di 0 byte ⇒ None", None, giudica(vuoto))
    rotto = os.path.join(tmp, "rotto.png")
    with open(rotto, "wb") as f:
        f.write(open(vero, "rb").read()[:400])   # ⛔ PNG troncato a meta'
    ok3 = prova("P2", "guasto G5 PNG troncato ⇒ None", None, giudica(rotto))
    ok4 = prova("P2", "risanato", "disegnato", (giudica(vero) or {}).get("verdetto"))
    buoni += ok0; rossi += (ok1 + ok2 + ok3); risanati += ok4
    if not (ok0 and ok1 and ok2 and ok3 and ok4): guasti.append("P2")

    # ── P3 · il verdetto sui pixel: nero, tinta unita, disegnato ────────────
    print("\n  P3 · il verdetto: ⛔ «un PNG che c'e'» non e' «un PNG che mostra»")
    nero = os.path.join(tmp, "nero.png"); _dipingi(nero, 640, 480, "nero")
    grigio = os.path.join(tmp, "grigio.png"); _dipingi(grigio, 640, 480, "grigio-pieno")
    ok0 = prova("P3", "sano: la sfumatura e' «disegnato»", "disegnato",
                (giudica(vero) or {}).get("verdetto"))
    ok1 = prova("P3", "guasto G6 schermo nero ⇒ «nero»", "nero",
                (giudica(nero) or {}).get("verdetto"))
    ok2 = prova("P3", "guasto G7 tinta unita ⇒ «tinta-unita»", "tinta-unita",
                (giudica(grigio) or {}).get("verdetto"))
    # ⭐ G8 e' il caso che separa i due sbagli opposti: uno schermo NERO con
    #    sopra la marca NON e' nero — e un testimone che dicesse «nero» qui
    #    butterebbe via l'unica prova che ha guardato davvero.
    nero_marca = os.path.join(tmp, "nero-marca.png")
    _dipingi(nero_marca, 640, 480, "nero", giro="f1-t")
    ok3 = prova("P3", "guasto G8 nero + marca ⇒ «disegnato»", "disegnato",
                (giudica(nero_marca) or {}).get("verdetto"))
    # ⭐ G12 — IL CONTROLLO NEGATIVO DEL VERO, rifatto qui in miniatura: uno
    #    schermo nero con sopra SOLO una barra chiara in alto (che e' quel che
    #    GNOME non spegne mai).  ⛔ Non e' «nero» — nessun desktop GNOME lo e' —
    #    ma non e' nemmeno «disegnato»: sopra non c'e' niente.
    quasi = os.path.join(tmp, "quasi-nero.png")
    # ⚠ E la barra finta e' TARATA SU QUELLA VERA, non disegnata a occhio: `[M]`
    #   nella barra di GNOME (40 righe) e' acceso il **3,3 %** dei pixel, e sullo
    #   schermo intero fanno una media di **0,279**.  Qui: 16x160 px bianchi =
    #   2 560 px = media 0,315.  ⛔ Una barra finta piu' grossa del vero farebbe
    #   passare il guasto per il motivo sbagliato — ed e' successo alla prima
    #   stesura, con un blocco da 500x40 che dava media 2,46.
    _img = np.zeros((1080, 1920, 3), np.uint8)
    _img[8:24, 860:1020] = 255          # ⇐ l'orologio della barra
    from PIL import Image as _Immagine
    _Immagine.fromarray(_img).save(quasi)
    ok5 = prova("P3", "guasto G12 nero + barra in alto ⇒ «quasi-nero»",
                "quasi-nero", (giudica(quasi) or {}).get("verdetto"))
    ok4 = prova("P3", "risanato", "nero", (giudica(nero) or {}).get("verdetto"))
    buoni += ok0; rossi += (ok1 + ok2 + ok3 + ok5); risanati += ok4
    if not ok5: guasti.append("P3")
    if not (ok0 and ok1 and ok2 and ok3 and ok4): guasti.append("P3")

    # ── P4 · la marca: c'e', e soprattutto e' LA MIA ────────────────────────
    print("\n  P4 · la taratura: la marca c'e', ed e' del MIO giro")
    con = os.path.join(tmp, "con-marca.png")
    _dipingi(con, 1280, 720, "desktop", giro="f1-taratura", disegno=41)
    r = leggi_la_marca(con, ["f1-taratura"])
    ok0 = prova("P4", "sano: marca trovata, ed e' mia",
                (True, True, 41),
                ((r or {}).get("c_e"), (r or {}).get("mio"), (r or {}).get("disegno")))
    senza = os.path.join(tmp, "senza-marca.png")
    _dipingi(senza, 1280, 720, "desktop")
    r1 = leggi_la_marca(senza, ["f1-taratura"])
    ok1 = prova("P4", "guasto G9 nessuna marca ⇒ rosso (non None)",
                (True, False), (r1 is not None, (r1 or {}).get("c_e")))
    # ⛔ G10: la marca c'e' ma e' di un ALTRO giro — cioe' sto guardando il
    #    desktop di qualcun altro.  E' il guasto che nessun conteggio di
    #    fotogrammi potrebbe mai dare.
    altrui = os.path.join(tmp, "altrui.png")
    _dipingi(altrui, 1280, 720, "desktop", giro="di-un-altro")
    r2 = leggi_la_marca(altrui, ["f1-taratura"])
    ok2 = prova("P4", "guasto G10 marca di un ALTRO giro ⇒ «non e' mia»",
                (True, False), ((r2 or {}).get("c_e"), (r2 or {}).get("mio")))
    # ⛔ G11: il fotogramma e' troppo piccolo perche' la marca ci stia.  Qui
    #    «la marca non c'e'» sarebbe FALSO: non ho potuto guardare.
    minuscolo = os.path.join(tmp, "minuscolo.png")
    _dipingi(minuscolo, 200, 100, "desktop")
    ok3 = prova("P4", "guasto G11 fotogramma troppo piccolo ⇒ None",
                None, leggi_la_marca(minuscolo, ["f1-taratura"]))
    r3 = leggi_la_marca(con, ["f1-taratura"])
    ok4 = prova("P4", "risanato", (True, True),
                ((r3 or {}).get("c_e"), (r3 or {}).get("mio")))
    buoni += ok0; rossi += (ok1 + ok2 + ok3); risanati += ok4
    if not (ok0 and ok1 and ok2 and ok3 and ok4): guasti.append("P4")

    print("\n───────────────────────────────────────────────────────────────")
    print("  sano %d · guasto %d · risanato %d" % (buoni, rossi, risanati))
    if guasti:
        print("  ⛔ NON CERTIFICATO: %s" % ", ".join(guasti))
        return 1
    print("  ✅ certificato: 4 predicati, 12 guasti innestati, tutti hanno morso")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="il testimone che fa vedere il desktop remoto")
    p.add_argument("che", nargs="?", default="scatta", choices=("scatta",))
    p.add_argument("--utente", default="provanic1")
    p.add_argument("--fuori", default="", help="dove scrivere il PNG, QUI")
    p.add_argument("--resta", type=float, default=6.0,
                   help="quanti secondi restare attaccati a guardare")
    p.add_argument("--porta", type=int, default=PORTA)
    p.add_argument("--indirizzo", default=INDIRIZZO)
    p.add_argument("--albero", default=ALBERO)
    p.add_argument("--lav", default=LAV)
    p.add_argument("--parola-file", default=PAROLA_FILE)
    p.add_argument("--macchina", default=MACCHINA)
    p.add_argument("--parola-sudo", default=PAROLA_SUDO)
    p.add_argument("--marca", default="",
                   help="⭐ il nome del giro che mi aspetto DENTRO i pixel: "
                        "senza, il testimone dice solo che cosa vede; con, "
                        "dice anche se sta guardando il desktop GIUSTO")
    p.add_argument("--sveglia", default="",
                   help="⚠ LxH — cambia la tela per obbligare il palco a "
                        "rifare un fotogramma su un desktop immobile.  "
                        "⛔ Cambia quel che il desktop vede: spento per "
                        "predefinito, e chi lo accende lo dichiara")
    p.add_argument("--tutti", action="store_true",
                   help="⭐ tira giu' anche TUTTI i fotogrammi della presa, "
                        "accanto allo scatto e con lo stesso nome piu' il "
                        "numero.  ⛔ Serve quando il desktop ATTRAVERSA uno "
                        "stato invece di restarci: `[M]` il dialogo «Profile "
                        "Missing» di Firefox compariva a meta' della presa e "
                        "sull'ultimo fotogramma non c'era piu'")
    p.add_argument("--json", default="", help="dove scrivere l'esito in JSON")
    p.add_argument("--loquace", action="store_true")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    if not a.fuori:
        print("⛔ senza `--fuori` non so dove mettere l'immagine")
        return 2

    t0 = time.time()
    e = scatta(a.utente, a.fuori, resta=a.resta, porta=a.porta,
               indirizzo=a.indirizzo, albero=a.albero, lav=a.lav,
               parola_file=a.parola_file, macchina=a.macchina,
               parola_sudo=a.parola_sudo, sveglia=a.sveglia or None,
               loquace=a.loquace, tutti=a.tutti)
    fuori = {"utente": a.utente, "porta": a.porta, "resta": a.resta,
             "durata_s": round(time.time() - t0, 1),
             "sveglia": a.sveglia or None}

    if e["png"] is None:
        # ⛔ IL TERZO ESITO.  Non e' un rosso e non e' un verde.
        print("⛔ NON HO GUARDATO — e questo non e' «lo schermo era nero».")
        print("   %s" % e["perche"])
        if a.loquace:
            print(e.get("registro", ""))
        fuori.update({"guardato": False, "perche": e["perche"],
                      "conti": e["conti"], "giudizio": None, "marca": None})
        if a.json:
            open(a.json, "w").write(json.dumps(fuori, ensure_ascii=False, indent=1))
        return 3

    g = giudica(e["png"])
    if g is None:
        print("⛔ NON HO GIUDICATO: lo scatto c'e' (%s) ma non ho potuto "
              "leggerne i pixel (manca `numpy`/`Pillow` qui?)." % e["png"])
        fuori.update({"guardato": True, "png": e["png"], "conti": e["conti"],
                      "giudizio": None, "marca": None})
        if a.json:
            open(a.json, "w").write(json.dumps(fuori, ensure_ascii=False, indent=1))
        return 3

    c = e["conti"]
    print("⭐ HO GUARDATO «%s» sulla porta %d" % (a.utente, a.porta))
    print("   dal filo   %d fotogrammi (%d chiavi), %s"
          % (c["fotogrammi"], c["chiavi"], c["misura"]))
    print("   lo scatto  %s  (%dx%d)" % (e["png"], g["larghezza"], g["altezza"]))
    print("   il quadro  ⇒ %s   media %.1f · dev %.1f · colori %d · "
          "accesi %.4f · diversi dal fondo %.4f"
          % (g["verdetto"].upper(), g["media"], g["dev"], g["colori"],
             g["accesi"], g["diversi"]))
    print("   le soglie  luma nero %.0f · nero sotto %.4f di accesi · quasi "
          "nero sotto media %.1f · tinta unita sotto %.4f di diversi"
          % (LUMA_NERO, FRAZIONE_NERO, MEDIA_QUASI_NERO, FRAZIONE_PIATTO))
    fuori.update({"guardato": True, "png": e["png"], "conti": c, "giudizio": g})

    esito = 0
    if a.marca:
        giri = [x for x in a.marca.split(",") if x]
        m = leggi_la_marca(e["png"], giri)
        fuori["marca"] = m
        if m is None:
            print("   ⛔ LA MARCA: non ho potuto leggerla (fotogramma troppo "
                  "piccolo, o manca il lettore).  ⚠ Non e' «non c'e'»")
            esito = 3
        elif not m["c_e"]:
            print("   ⛔ LA MARCA NON C'E' — %s" % m["perche"])
            esito = 1
        elif not m["mio"]:
            print("   ⛔ LA MARCA C'E' MA NON E' MIA: giro 0x%08x, e i miei "
                  "erano %s.  ⚠ Sto guardando il desktop di qualcun altro"
                  % (m["giro_numero"], giri))
            esito = 1
        else:
            print("   ⭐ LA MARCA C'E' ED E' MIA: giro «%s», disegno %d, "
                  "contrasto %.3f  ⇒ **il testimone sta guardando QUEL desktop**"
                  % (m["giro"], m["disegno"], m["contrasto"] or 0.0))
    else:
        fuori["marca"] = None

    if a.json:
        open(a.json, "w").write(json.dumps(fuori, ensure_ascii=False, indent=1))
    return esito


if __name__ == "__main__":
    sys.exit(main())
