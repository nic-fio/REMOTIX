#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c8 — ⭐⭐⭐ «IL SECONDO UTENTE APRE IL BROWSER»
===========================================================================

    python3 11-c8-il-secondo-apre-il-browser.py
    python3 11-c8-il-secondo-apre-il-browser.py --senza-cura
    python3 11-c8-il-secondo-apre-il-browser.py --certifica

⛔ E' il COLLAUDO B della fase 11.  ⭐ E' anche, secondo tutt'e due i revisori
   esterni, **la prova piu' importante della lista** — e nella prima stesura era
   anche la piu' difficile da eseguire.  ⇒ L'utente ha sciolto il nodo il 26
   agosto 2026 (`DECISIONI.md` §4.6-terdecies):

       *«Per quanto mi riguarda un container puo' anche avere 10 utenti,
         e' un dato gia' misurato con GNOME.»*

   ⇒ ⭐ **C8 sta in una scatola, con DUE inquilini.**  Non dieci: la domanda e'
     la CORRETTEZZA a piu' utenti, non la capienza — quella e' gia' misurata e
     non si rifa'.

---------------------------------------------------------------------------
⛔⛔ IL GUASTO CHE QUESTA MAGLIA DEVE PRENDERE — e di chi e' la colpa
---------------------------------------------------------------------------

`DECISIONI.md` §4.6-undecies, e la correzione dell'utente che ne cambia il
bersaglio:

  · `/etc/skel/.cache` di quella macchina e' un COLLEGAMENTO a `/tmp`.
    ⭐⭐ E **NON E' UN GUASTO**: e' una **scelta voluta** del proprietario su
    come deve funzionare il suo sistema operativo.  ⛔ Non c'e' niente da
    riparare, e questa prova non lo ripara.
  · ⛔ **Il difetto e' NOSTRO**: e' il prodotto che crea gli inquilini con
    `useradd -m`, che copia lo scheletro ⇒ nascono TUTTI a scrivere nello
    stesso posto.  Firefox tiene il profilo locale sotto `$HOME/.cache/mozilla`
    = `/tmp/mozilla`, e ⛔ **il primo che apre il browser se lo prende a modo
    0700**: dal secondo in poi il profilo non nasce, e la finestra che si apre
    dice *«Your Firefox profile cannot be loaded»*.

⇒ ⭐ **Il bersaglio della prova non e' il collegamento**: e' *«il secondo utente
  apre il browser, si' o no?»*, su una macchina configurata come la vuole il
  suo proprietario.  ⛔ Guardare il collegamento sarebbe guardare la CAUSA che
  crediamo di conoscere invece dell'EFFETTO che ci interessa — e la cura
  potrebbe cambiare senza che la prova se ne accorga.

---------------------------------------------------------------------------
⭐ COME GIUDICA — nel PIXEL, e senza sapere che aspetto abbia un desktop
---------------------------------------------------------------------------

⛔ Il conto dei processi non serve: `[M]` diceva «1» con la finestra e senza.
⛔ «Firefox e' vivo» non serve: nel guasto Firefox **e' vivo**, e mostra un
   dialogo d'errore.

⇒ La prova apre nel browser una pagina di **colore `#FF00FF`** (`11-c8-pagina.html`)
  e guarda **quanto schermo e' diventato di quel colore**, con una **tolleranza
  dichiarata** — perche' i compositori applicano profili e riscalamenti, e un
  `#FF00FF` torna indietro leggermente diverso (§4.3, rilievo di Gemini).

E si guarda **PRIMA e DOPO**, non solo dopo:

    prima : la sessione e' viva e il desktop e' DISEGNATO (giudice di 10-f1)
    dopo  : una fetta larga di schermo e' del colore della pagina

⛔ Il «prima» non e' cerimonia: senza, un desktop che non nasce nemmeno darebbe
   lo stesso identico esito di un browser che non parte — ⚠ due guasti diversi
   con la stessa faccia, che e' il modo in cui questo progetto ha gia' perso
   due diagnosi.

---------------------------------------------------------------------------
⛔ COME SO CHE SA DARE ROSSO — `--senza-cura`
---------------------------------------------------------------------------

`fasi/11…` §4.1, colonna «come so che sa dare rosso»: *«si disfa la cura della
provvista ⇒ rosso»*.

  senza `--senza-cura`  gli inquilini ricevono la cura di `src/provisiona.sh`:
                        una `~/.cache` VERA, cartella loro, modo 0700
  con `--senza-cura`    ⛔ la cura NON si applica: i due nascono come li faceva
                        il codice del 25 agosto 2026 ⇒ **il secondo deve dare
                        ROSSO**, o questa maglia non serve a niente

⚠ E il terreno se lo prepara da se': la scatola parte con uno `/etc/skel`
  pulito, e questa prova ci mette il collegamento a `/tmp` — ⛔ cioe'
  **riproduce la configurazione della macchina vera**, che e' l'unica sulla
  quale la domanda ha senso.  ⇒ Provare su uno scheletro pulito vorrebbe dire
  rispondere a una domanda piu' facile di quella vera (§3.5).

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: TUTT'E DUE gli inquilini hanno aperto il browser
  1  ho guardato: almeno uno NON ce l'ha fatta            ⇒ rosso
  3  ⛔ non ho potuto guardare (il server non c'era, il giudice non c'era,
     nessun fotogramma e' arrivato) — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 E' LA CASA DEI DUE PASSI COMUNI A TUTTE E NOVE LE MAGLIE — §1.47
#
# ⛔ Non e' comodita': una riga ripetuta in nove file e' **nove posti da cui
#    divergere**, ed erano gia' divergiti.  Da `11-c1-nasce-e-si-vede.py`:
#
#   · `e_stato_ammesso(coda)`   — «il cliente e' stato AMMESSO?», che ⛔ non e'
#        la parola dentro un testo: il cliente la stampa anche nei DUE messaggi
#        di rifiuto, e sullo stdout (`01-b3-cliente.py:1315`, `:1322`, `:2560`).
#   · `garantisci_i_gruppi(chi)` — i gruppi dei nodi `/dev/dri`, ⛔ senza i
#        quali `[M]` la sessione nasce CIECA (0 su 4, zero fotogrammi,
#        `fasi/10-…` §7.4) e questa maglia misurerebbe il buio.
#
# ⛔ Se C1 non si carica si esce **3** e lo si dice: ⛔ non si ripiega in
#    silenzio su un giudizio piu' povero.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_C1 = ("e_stato_ammesso", "certifica_ammissione",
                "garantisci_i_gruppi", "verdetto_gruppi", "certifica_gruppi")
_C1 = None


def _carica_c1():
    """⛔ E' un CARICATORE, non un giudice: trova il file, non decide niente.

    ⚠ Si cerca accanto a me (nella scatola tutto sta in `/opt/remotix`) e un
      piano piu' su, perche' nel deposito questa maglia sta in
      `banchi/11-scatole/`.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "11-c1-nasce-e-si-vede.py")
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location("c1_comune", perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ Si VERIFICA che ci sia quel che serve, non ci si fida del nome del
        #    file (`CODER.md` §3.9).
        for mestiere in _MESTIERI_C1:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   vengono il predicato dell'ammissione e la garanzia dei")
        print("   gruppi della scheda — che stanno in un posto solo (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama dice «non ho potuto guardare» (**3**).
    """
    return casa_di_c1().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — `(esito, perche)`; `0` = si puo' misurare.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica — E1, «scritto non e' in
       vigore».  ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid
       dai NODI e rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui.
    """
    return casa_di_c1().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ IL COLORE DEL BERSAGLIO E LA SUA TOLLERANZA — dichiarati qui e stampati in
#    ogni esito, perche' «il browser ha disegnato» e' un verdetto, e un
#    verdetto senza il suo metro e' un'opinione.
#
# ⚠ La tolleranza NON e' prudenza generica: `fasi/11…` §4.3 accoglie il rilievo
#   di Gemini — i compositori applicano profili di colore, la catena passa per
#   una codifica H.264 in 4:2:0 (che sottocampiona proprio il croma, cioe' il
#   canale dove sta tutta la differenza fra magenta e non-magenta), e pretendere
#   il colore esatto vorrebbe dire una prova gia' morta.
# ⛔ E la tolleranza si TARA, non si sceglie: `--certifica` contiene il caso
#   «colore spostato di quanto la tolleranza ammette ⇒ deve restare VERDE» — che
#   e' la stessa guardia che C1 ha sulla soglia dell'immagine.
# ---------------------------------------------------------------------------
COLORE = (0xFF, 0x00, 0xFF)
TOLLERANZA = 48          # per canale, in livelli 0..255
FRAZIONE_MINIMA = 0.25   # quanto schermo dev'essere di quel colore

# ⚠ 0,25 e non 0,90: fra il bordo della finestra, la barra di GNOME e le
#   decorazioni, il browser a schermo intero non copre mai tutto.  ⛔ E una
#   soglia troppo alta si romperebbe al primo desktop con una barra piu' larga,
#   cioe' proprio alla fase 12 — che e' quel che questa fase esiste per evitare.


def giudice_immagini():
    """⭐ Il giudice dei pixel si IMPORTA, non si riscrive.

    ⛔ `10-f1-testimone.py` e' gia' tarato sul vero (25 agosto 2026: desktop
       nero misurato, soglia del «quasi-nero» messa in mezzo al vuoto fra i due
       mondi).  Riscriverne qui una copia vorrebbe dire avere due giudici che
       possono divergere in silenzio — e il giorno che divergono, il rosso lo
       darebbe quello sbagliato.
    ⇒ Se non c'e', questa prova esce **3**: «non ho potuto guardare».  ⛔ Non si
      ripiega su un giudizio piu' povero senza dirlo.
    """
    perc = os.path.join(QUI, "10-f1-testimone.py")
    if not os.path.exists(perc):
        return None
    spec = importlib.util.spec_from_file_location("testimone10f1", perc)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception:
        return None
    return m


def frazione_del_colore(percorso, colore=COLORE, tolleranza=TOLLERANZA):
    """Quanta parte dell'immagine e' del colore cercato, entro la tolleranza.

    ⛔ Torna **`None`** se non ha potuto guardare — file che non c'e', file
       vuoto, `numpy`/`Pillow` che mancano, PNG troncato.  ⚠ `None` non e'
       «zero»: «non ho guardato» e «ho guardato e non c'era» sono due cose
       diverse, e questo progetto ha gia' pagato per averle confuse.
    """
    if not percorso or not os.path.exists(percorso) \
            or os.path.getsize(percorso) == 0:
        return None
    try:
        import numpy as np
        from PIL import Image
        img = np.asarray(Image.open(percorso).convert("RGB")).astype("int16")
    except Exception:
        return None
    if img.ndim != 3 or img.shape[2] != 3 or img.size == 0:
        return None
    # ⚠ La distanza si prende **canale per canale** (norma del massimo) e non
    #   come somma: una somma lascerebbe passare un colore molto sbagliato su un
    #   canale solo, purche' azzeccato sugli altri due.
    scarto = np.abs(img - np.array(colore, dtype="int16")).max(axis=2)
    return float((scarto <= tolleranza).mean())


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE DEL GIUDICE — si dimostra che SA dare rosso, e verde
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ E si dichiara che cosa copre e che cosa no.

    COPRE: il lettore dei pixel — che il colore si ritrovi quando c'e', che NON
    si ritrovi quando non c'e', ⭐ che una immagine **spostata di quanto la
    tolleranza ammette** resti VERDE (o la soglia e' troppo stretta e la maglia
    si butta fra due settimane), e che «non ho guardato» torni `None`.
    ⛔ NON COPRE: che il browser sia davvero partito.  Quello lo dice
    `--senza-cura` sul vero, ed e' l'altra meta' del collaudo.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("⛔ mancano numpy o Pillow: non posso nemmeno certificarmi")
        print("   ⇒ non ho potuto guardare")
        return 3
    import tempfile

    lav = tempfile.mkdtemp(prefix="c8cert-")

    def dipingi(nome, riempi, macchia=None):
        a = np.zeros((216, 384, 3), dtype="uint8")
        a[:, :] = riempi
        if macchia is not None:
            a[80:136, 100:284] = macchia
        p = os.path.join(lav, nome + ".png")
        Image.fromarray(a).save(p)
        return p

    # ⭐ I casi, e ognuno c'e' per una ragione che si puo' dire in una riga.
    casi = []
    # 1. la pagina c'e' tutta: il browser ha disegnato
    casi.append(("pagina intera",
                 dipingi("a", COLORE, (0, 0, 0)), True))
    # 2. il desktop senza browser: nessun magenta
    casi.append(("desktop senza browser",
                 dipingi("b", (58, 62, 70), (200, 200, 200)), False))
    # 3. ⭐ IL CASO CHE TARA LA SOGLIA: il colore torna indietro SPOSTATO —
    #    profili di colore, 4:2:0, riscalamenti.  Deve restare VERDE.
    spostato = tuple(min(255, max(0, c + s))
                     for c, s in zip(COLORE, (-30, +30, -30)))
    casi.append(("colore spostato di %s (dev'essere VERDE)" % (spostato,),
                 dipingi("c", spostato, (0, 0, 0)), True))
    # 4. e uno spostato TROPPO non deve passare, o la tolleranza non separa piu'
    troppo = (0xFF, 0x90, 0xFF)
    casi.append(("colore spostato TROPPO %s (dev'essere ROSSO)" % (troppo,),
                 dipingi("d", troppo, (0, 0, 0)), False))
    # 5. lo schermo nero: e' un rosso, non un «non lo so»
    casi.append(("schermo nero", dipingi("e", (0, 0, 0)), False))
    # 6. ⛔ la finestra c'e' ma copre poco: sotto la frazione minima
    piccola = np.zeros((216, 384, 3), dtype="uint8")
    piccola[:, :] = (58, 62, 70)
    piccola[10:40, 10:80] = COLORE          # ~2,7 % dello schermo
    pp = os.path.join(lav, "f.png")
    Image.fromarray(piccola).save(pp)
    casi.append(("una macchia piccola non e' una pagina", pp, False))

    print("== certificazione del giudice di C8 ==")
    print("   colore %s · tolleranza ±%d per canale · frazione minima %.2f"
          % (COLORE, TOLLERANZA, FRAZIONE_MINIMA))
    guai = 0
    for nome, png, atteso in casi:
        fr = frazione_del_colore(png)
        visto = (fr is not None and fr >= FRAZIONE_MINIMA)
        ok = (visto == atteso)
        print("  %s  %-52s  frazione=%s  ⇒ %s (atteso %s)"
              % ("OK " if ok else "NO ", nome,
                 "non lo so" if fr is None else "%.3f" % fr,
                 "pagina" if visto else "niente",
                 "pagina" if atteso else "niente"))
        if not ok:
            guai += 1

    # 7. ⛔ E il caso che vale piu' di tutti: «non ho potuto guardare» dev'essere
    #    `None`, non zero.  Un file che non c'e' NON e' uno schermo senza pagina.
    for nome, perc in (("il file non c'e'", os.path.join(lav, "manca.png")),
                       ("il file e' vuoto", os.path.join(lav, "vuoto.png"))):
        if "vuoto" in nome:
            open(perc, "wb").close()
        fr = frazione_del_colore(perc)
        ok = fr is None
        print("  %s  %-52s  frazione=%s  ⇒ %s (atteso «non lo so»)"
              % ("OK " if ok else "NO ", nome,
                 "non lo so" if fr is None else "%.3f" % fr,
                 "non lo so" if fr is None else "un numero"))
        if not ok:
            guai += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ il caso che oggi non c'era.
    #
    # ⛔ Un inquilino fuori dai gruppi dei nodi `/dev/dri` fa nascere una
    #    sessione CIECA (`[M]` 0 su 4, zero fotogrammi, `fasi/10-…` §7.4) ⇒
    #    questa maglia misurerebbe il buio.  ⭐ Si pretende che dica «non ho
    #    potuto guardare», ⛔ e MAI rosso: e' un guasto del BANCO (§1.51).
    # ⚠ I casi vivono in C1, col passo che certificano: ⛔ una copia qui
    #   sarebbe un secondo posto da cui divergere (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    guai_gr, _quanti_gr = casa_di_c1().certifica_gruppi("C8")
    guai += guai_gr

    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice vede la pagina quando c'e', non la vede quando non c'e',")
    print("   ⭐ regge uno spostamento di colore, e dice «non lo so» invece di zero")
    print("   ⭐ e i GRUPPI DELLA SCHEDA: un inquilino che non vede fa dire "
          "«non ho potuto guardare», ⛔ mai rosso")
    print("⚠ e questa certificazione copre IL LETTORE, non il browser (vedi in testa)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# IL TERRENO — si prepara, e ⛔ si VERIFICA che sia in vigore (E1)
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=120):
    return subprocess.run(["/bin/sh", "-c", comando],
                          capture_output=True, text=True, timeout=secondi)


def sgombra_il_posto_condiviso(base):
    """⛔ «Da zero» vuol dire anche: **quel che ha lasciato il giro di prima**.

    `[M]` Il difetto vive in `/tmp/mozilla`, che il primo inquilino si prende a
    modo 0700.  ⇒ Se restasse li' dal giro precedente, il PRIMO inquilino del
    giro nuovo fallirebbe come il secondo — cioe' la prova direbbe rosso per la
    ragione sbagliata, e chi legge concluderebbe una cosa falsa.

    ⚠⚠ E si toglie SOLO quel che e' di un inquilino di QUESTA prova.  ⛔ Un
       `rm -rf /tmp/mozilla` secco cancellerebbe il profilo di chiunque altro —
       ed e' esattamente la regola che `src/provisiona.sh` si e' data
       («non si tocca `/tmp/mozilla` di chi ce l ha gia: non e nostro e non si
       sa chi lo usa»).  Qui vale uguale: fuori dalla scatola questa riga
       sarebbe un danno.
    """
    p = "/tmp/mozilla"
    chi = sh("stat -c %%U %s 2>/dev/null" % p).stdout.strip()
    if not chi:
        return None
    if not chi.startswith(base):
        return "⚠ %s e' di «%s», che non e' un inquilino di questa prova: NON lo tocco" % (p, chi)
    sh("rm -rf %s" % p)
    return "sgombrato %s, che era rimasto a «%s» dal giro prima" % (p, chi)


def prepara_lo_scheletro():
    """⭐ Riproduce la configurazione della MACCHINA VERA: `/etc/skel/.cache`
    come collegamento a `/tmp`.

    ⛔ E non e' «introdurre un guasto»: e' una **scelta del proprietario della
       macchina**, e la prova che gira su uno scheletro pulito risponde a una
       domanda piu' facile di quella vera.
    """
    sh("rm -rf /etc/skel/.cache && ln -s /tmp /etc/skel/.cache")
    r = sh("readlink /etc/skel/.cache")
    return r.stdout.strip()


def crea(chi, parola):
    """Crea l'inquilino **come lo crea il prodotto**: `useradd -m`.

    ⛔ `-m` copia lo scheletro, ed e' precisamente il passo da cui nasce il
       difetto.  Usare una via piu' pulita qui vorrebbe dire provare un
       prodotto diverso da quello consegnato.
    """
    sh("loginctl terminate-user %s 2>/dev/null; pkill -KILL -u %s 2>/dev/null; "
       "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi, chi, chi))
    # ⛔⛔ I GRUPPI DELLA SCHEDA NON STANNO PIU' DENTRO IL `useradd`.
    #     `usermod -aG video,render` inchiodava due nomi — che sono di UNA
    #     distribuzione — e ⛔ **non rileggeva**: `usermod` riuscito non vuol
    #     dire «ci sta dentro» (E1, «scritto non e' in vigore»).
    # ⭐ Li da' `attrezzi-gruppi-scheda.sh`, che li LEGGE dai nodi `/dev/dri` e
    #   poi VERIFICA confrontando i numeri.  ⇒ Qui non c'e' piu' nessun nome di
    #   gruppo e nessun numero.
    # ⛔ E senza, `[M]` la sessione nasce CIECA (0 su 4, zero fotogrammi,
    #   `fasi/10-…` §7.4): questa maglia misurerebbe il buio e lo chiamerebbe
    #   difetto del prodotto.  ⇒ Non si misura: chi chiama esce **3**.
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
    if r.returncode != 0:
        return False, (r.stderr or "").strip()[:120]
    e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="      ")
    if e_gr != 0:
        return False, perche_gr
    return True, ""


def applica_la_cura(chi):
    """⭐ Le stesse righe di `src/provisiona.sh`, e non una loro parafrasi.

    ⚠ Non si tocca `/etc/skel` e non si tocca `/tmp/mozilla` di chi ce l'ha
      gia': si da' una `~/.cache` vera SOLTANTO agli utenti che creiamo noi.
    """
    c = "/home/%s/.cache" % chi
    sh("[ -L %s ] && rm -f %s; mkdir -p %s; chown %s:%s %s; chmod 700 %s"
       % (c, c, c, chi, chi, c, c))


def sa_scrivere_nella_cache(chi):
    """⛔ «scritto non e' in vigore» (E1): non si guarda il collegamento, si
       PROVA A SCRIVERE.

    ⚠⚠ E SI SCRIVE IN `~/.cache/**mozilla**`, non in `~/.cache` — ed e' una
       correzione, non un dettaglio.  `[M]` 26 agosto 2026: la prima stesura
       provava a scrivere in `~/.cache`, che col collegamento e' `/tmp`, ⛔ e
       `/tmp` e' scrivibile da chiunque (modo 1777).  ⇒ Il predicato diceva
       **si'** anche al secondo inquilino, cioe' **non vedeva mai il difetto**.
    ⭐ Il posto che morde e' `/tmp/mozilla`, che il PRIMO si prende a modo 0700
      — ed e' esattamente la misura di `src/provisiona.sh`: *«da `provanic3`,
      `mkdir -p ~/.cache/mozilla` → Permission denied»*.
    """
    r = sh("su -s /bin/sh -c 'mkdir -p ~/.cache/mozilla/.prova-c8 && "
           "rmdir ~/.cache/mozilla/.prova-c8' %s" % chi)
    return r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════
# LA PRESA — attaccarsi alla sessione e tirarne fuori un PNG, ⛔ QUI DENTRO
# ═══════════════════════════════════════════════════════════════════════════
def scatta(chi, parola, fuori, a, resta):
    """Torna (png|None, quanti_fotogrammi|None, perche').

    ⛔ Tre esiti e non due: «il PNG c'e'», «non e' arrivato nessun fotogramma»,
       «i fotogrammi sono arrivati ma non se n'e' fatta un'immagine» — e i due
       ultimi sono *«non ho guardato»*, non «lo schermo era vuoto».
    """
    flusso = fuori + ".264"
    for f in (flusso, fuori):
        if os.path.exists(f):
            os.unlink(f)
    r = subprocess.run(
        ["python3", "-u", a.cliente,
         "--indirizzo", a.indirizzo, "--porta", str(a.porta),
         "--utente", chi, "--parola", parola,
         "--video-scrivi", flusso, "--resta", str(resta)],
        capture_output=True, text=True, timeout=int(resta) + 120)
    coda = (r.stdout or "") + (r.stderr or "")
    quanti = None
    for riga in coda.splitlines():
        if "[vid]" in riga and "nessun fotogramma" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    # ⛔⛔ PRIMA DI DAR LA COLPA AL FILO, SI GUARDA SE IL CLIENTE E' ENTRATO.
    #
    # ⚠ Fino al 27 agosto 2026 questa maglia non lo chiedeva affatto: ⇒ un
    #   RIFIUTO di credenziali usciva come *«nessun fotogramma e' arrivato dal
    #   filo»* — un'accusa al filo per un cliente che non era nemmeno entrato.
    #   ⛔ L'esito era gia' giusto (**3**, non un rosso), ⭐ ma la parola no, e
    #   una diagnosi sbagliata costa quanto un verdetto sbagliato: chi legge va
    #   a cercare il guasto nel posto che il banco gli ha indicato.
    # ⛔ E il predicato NON e' `"AMMESSO" in coda`: il cliente stampa quella
    #    parola anche nei due messaggi di rifiuto (`e_stato_ammesso()` in testa).
    ammesso = e_stato_ammesso(coda)
    if ammesso is not True:
        return None, None, (
            "il cliente e' stato RESPINTO dal server" if ammesso is False
            else "il cliente di prova non ha detto niente: non so se sia "
                 "entrato")
    if not quanti:
        return None, None, ("nessun fotogramma e' arrivato dal filo "
                            "(sessione non aperta, o palco che non consegna)")
    # ⛔ `-update 1` tiene l'ULTIMO fotogramma: e' quel che il desktop mostra
    #    adesso.  Il primo sarebbe la chiave d'apertura, cioe' un secondo fa.
    d = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
           % (flusso, fuori), secondi=180)
    if d.returncode != 0 or not os.path.exists(fuori) \
            or os.path.getsize(fuori) == 0:
        return None, quanti, ("%d fotogrammi sono arrivati ma ffmpeg non ne ha "
                              "fatto un'immagine" % quanti)
    return fuori, quanti, None


def rende_la_pagina_da_solo(chi, a, fuori):
    """⭐⭐ PROVA A — *«il browser rende la pagina»*, ⛔ **senza il palco di mezzo**.

    Firefox si fa una fotografia da se' (`--screenshot`), da utente, sulla
    macchina com'e' configurata.  ⇒ Il giudizio resta **nel pixel** — la pagina
    c'e' o non c'e' — e ⭐ **prende esattamente il difetto di §4.6-undecies**:
    per fotografare, Firefox deve prima **fare il suo profilo**, e con la
    `~/.cache` condivisa il secondo inquilino non ci riesce.

    ⛔⛔ E PERCHE' ESISTE, che e' la parte che va scritta invece che nascosta.
    La forma piena di C8 vuole la pagina vista **attraverso il prodotto**, cioe'
    dentro la sessione remota (`rende_la_pagina_nella_sessione`, prova B).
    ⚠ Quella oggi **non si puo' misurare**: `[M]` 26 agosto 2026, dentro la
    scatola **nessuna** sessione GNOME nuova nasce con un monitor — e' il
    difetto APERTO della fase 10 §7.4 («la sessione che nasce cieca»), che sta
    **a monte** di C8 e che C1 esiste apposta per prendere.
    ⇒ ⭐ Un desktop nero non testimonia sul browser: chiamare quello «rosso di
      C8» vorrebbe dire dare la colpa al browser di una cosa successa **prima
      che il browser esistesse**.

    ⛔ E il limite si dichiara, per non spacciare questa prova per l'altra:
      qui il browser disegna **nella sua finestra**, non **nella sessione
      remota**.  ⇒ Quel che questa prova NON puo' vedere e' un difetto che
      nascesse fra il browser e il palco.  ⚠ Non la sostituisce: **la precede**.
    """
    if os.path.exists(fuori):
        os.unlink(fuori)
    # ⚠ `HOME` esplicito e non ereditato: il difetto vive dentro `$HOME/.cache`,
    #   e una prova che guardasse la home sbagliata direbbe verde per sempre.
    # ⛔⛔ E IL TETTO E' SUO, non quello della prova B — `[M]` 26 agosto 2026,
    #    e ci e' costato un rosso falso.  La prima stesura riusava
    #    `--attesa-browser` (25 s): ⛔ il PRIMO avvio di Firefox in una scatola
    #    fredda non ci sta dentro, e la prova dava **ROSSO A TUTT'E DUE** gli
    #    inquilini, con la cura e senza.
    #    ⚠ Cioe' il banco dava rosso per la ragione sbagliata — e con un rosso
    #      cosi' il collaudo del guasto innestato non vale niente, perche' non
    #      distingue piu' il guasto dal banco.  ⇒ `LEZIONI.md` §1.41.
    #
    # ⚠⚠ E IL TETTO GOVERNA UNA COSA DIVERSA DA QUELLA CHE SEMBRA — correzione
    #    del 26 agosto 2026, trovata dal banco di C14 e non da questo.
    #    `[M]` Con `timeout 1`, Firefox esce con **124** (ucciso) ⛔ **e il PNG
    #    c'e' lo stesso, 30 135 byte**: scrive l'immagine e poi indugia a
    #    chiudersi.  ⇒ Questo tetto non limita **lo scatto**: limita **l'uscita
    #    del browser**.
    #    ⭐ Il giudizio resta giusto, e per una ragione che va detta: si guarda
    #      il **file**, non il codice d'uscita — un browser che ha disegnato ha
    #      disegnato, anche se poi e' stato ucciso mentre si accomiatava.
    #    ⛔ Ma il tetto resta largo lo stesso: il primo avvio in una scatola
    #      fredda deve poter arrivare fino al disegno, e su quello il tetto
    #      MORDE per davvero.
    #
    # ⛔⛔ E L'IMMAGINE SI FA SCRIVERE NELLA SUA CARTELLA, non nella nostra.
    #    `[M]` 26 agosto 2026, e ci e' costato un secondo rosso falso: la
    #    cartella di lavoro del banco e' di `root` a modo 0755, e Firefox gira
    #    da UTENTE ⇒ ⛔ non poteva scriverci, e non produceva nessuna immagine.
    #    ⚠ Il banco lo leggeva come «il browser non ha disegnato» — cioe' ⛔ **il
    #      banco dava rosso a se stesso e lo attribuiva al prodotto**.
    #    ⇒ Scatta in casa sua, e a portarla fuori ci pensa root dopo.
    suo = "/home/%s/.c8-scatto.png" % chi
    sh("rm -f %s" % suo)
    r = sh("runuser -u %s -- env HOME=/home/%s MOZ_HEADLESS=1 "
           "timeout %d %s --headless --screenshot %s file://%s"
           % (chi, chi, int(a.attesa_scatto), a.browser, suo, a.pagina),
           secondi=int(a.attesa_scatto) + 30)
    coda = ((r.stdout or "") + (r.stderr or "")).strip()
    if os.path.exists(suo) and os.path.getsize(suo):
        sh("cp -f %s %s" % (suo, fuori))
    return fuori if os.path.exists(fuori) and os.path.getsize(fuori) else None, coda[-200:]


def apri_il_browser(chi, a):
    """Accende il browser DENTRO la sessione dell'inquilino.

    ⛔ Il socket di Wayland si CERCA, non si indovina: il nome dipende da come
       il compositore e' nato, e inchiodare `wayland-0` qui vorrebbe dire una
       prova che funziona su un desktop e tace sugli altri — cioe' esattamente
       il difetto che questa fase esiste per non introdurre.
    """
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, "non so l'uid di %s" % chi
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    display = soc.stdout.strip()
    if not display:
        return None, ("in %s non c'e' nessun socket wayland: la sessione non ha "
                      "un compositore a cui il browser possa parlare" % rtd)
    comando = (
        "runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
        "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
        "%s --kiosk file://%s > /tmp/c8-%s.log 2>&1 &"
        % (chi, rtd, display, chi, a.browser, a.pagina, chi))
    sh(comando, secondi=30)
    return display, None


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente-base", default="c8u")
    p.add_argument("--quanti", type=int, default=2,
                   help="⛔ DUE, e non dieci: la domanda e' la correttezza a "
                        "piu' inquilini, non la capienza (D2 corretta)")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--pagina", default="/opt/remotix/11-c8-pagina.html")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--lavoro", default="/var/lib/rete11/c8")
    p.add_argument("--resta-prima", type=float, default=25.0,
                   help="quanto si sta attaccati al primo scatto: il palco "
                        "nasce in ~13 s, e una scadenza corta darebbe «non lo so»")
    p.add_argument("--resta-dopo", type=float, default=10.0)
    p.add_argument("--attesa-browser", type=float, default=25.0,
                   help="quanto si da' al browser per disegnare la pagina")
    p.add_argument("--senza-cura", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: non si applica la cura della "
                        "provvista. Il secondo inquilino DEVE dare rosso")
    p.add_argument("--attesa-scatto", type=float, default=120.0,
                   help="quanto si da' alla prova A. ⛔ Largo apposta: il PRIMO "
                        "avvio di Firefox in una scatola fredda passa i 25 s, e "
                        "un tetto stretto da un rosso che non e' del prodotto")
    p.add_argument("--senza-sessione", action="store_true",
                   help="salta la prova B (la pagina vista DAL CLIENTE). ⚠ Da "
                        "usare quando si sa gia' che le sessioni nascono cieche: "
                        "risparmia due minuti e non cambia nessun giudizio")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: deve creare due inquilini")
        sys.exit(2)

    # ── il terreno, e le tre cose senza le quali non si giudica ────────────
    giudice = giudice_immagini()
    if giudice is None:
        print("⛔ non trovo il giudice delle immagini (10-f1-testimone.py) accanto a me")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if not os.path.exists(a.pagina):
        print("⛔ non trovo la pagina bersaglio: %s" % a.pagina)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    # ⚠ Il cliente di prova serve SOLO alla prova B.  ⭐ E questo e' il motivo
    #   per cui la prova A gira in QUALUNQUE scatola, anche in una dove il
    #   prodotto non c'e' nemmeno: non guarda attraverso il prodotto.
    if not a.senza_sessione and not os.path.exists(a.cliente):
        print("⛔ non trovo il cliente di prova: %s" % a.cliente)
        print("   ⇒ non ho potuto guardare (⚠ con --senza-sessione non servirebbe)")
        sys.exit(3)
    if sh("command -v %s" % a.browser).returncode != 0:
        print("⛔ nella scatola non c'e' %s: non posso chiedere a nessuno di "
              "aprire una pagina" % a.browser)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if sh("command -v ffmpeg").returncode != 0:
        print("⛔ nella scatola non c'e' ffmpeg: i fotogrammi non diventano "
              "un'immagine")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)
    dove = prepara_lo_scheletro()
    resto = sgombra_il_posto_condiviso(a.utente_base)

    print("== C8 — il secondo utente apre il browser ==")
    print("   %d inquilini · porta %d · pagina %s"
          % (a.quanti, a.porta, os.path.basename(a.pagina)))
    print("   terreno: /etc/skel/.cache -> %s  (la configurazione della "
          "macchina vera)" % (dove or "⛔ NON SONO RIUSCITO A METTERLO"))
    print("   cura della provvista: %s"
          % ("⛔ NON APPLICATA (guasto innestato: il secondo DEVE dare rosso)"
             if a.senza_cura else "applicata, come src/provisiona.sh"))
    print("   metro: colore %s ±%d, almeno il %.0f%% dello schermo"
          % (COLORE, TOLLERANZA, FRAZIONE_MINIMA * 100))
    if resto:
        print("   %s" % resto)
    print()
    if not dove:
        print("⛔ non sono riuscito a preparare lo scheletro: il terreno non regge")
        sys.exit(2)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ DUE PROVE, E NON UNA — e la ragione va letta prima dei numeri
    #
    #   A · «il browser rende la pagina»            ⭐ si misura OGGI
    #       Firefox si fotografa da se', da utente, sulla macchina com'e'
    #       configurata.  Prende il difetto di §4.6-undecies per intero: per
    #       fotografare deve prima farsi il profilo.
    #
    #   B · «e la pagina si vede DAL CLIENTE»       ⚠ oggi non si misura
    #       la stessa pagina, guardata attraverso il prodotto.  ⛔ `[M]` 26
    #       agosto 2026: dentro la scatola NESSUNA sessione GNOME nuova nasce
    #       con un monitor — e' il difetto APERTO della fase 10 §7.4, che sta
    #       A MONTE di C8.  ⇒ La prova B dice «non ho potuto guardare» e
    #       NOMINA il perche'; ⛔ non diventa un rosso di C8, perche' un
    #       desktop nero non testimonia sul browser.
    #
    # ⭐ E l'esito della maglia lo decide **A**.  ⚠ B lo puo' peggiorare — se
    #   arriva a un giudizio e quel giudizio e' rosso — ⛔ mai migliorarlo.
    # ═══════════════════════════════════════════════════════════════════════
    esiti = []
    for n in range(1, a.quanti + 1):
        chi = "%s%d" % (a.utente_base, n)
        fatto, perche = crea(chi, a.parola)
        if not fatto:
            print("  %-6s  ?   non sono riuscito a crearlo: %s" % (chi, perche))
            esiti.append({"chi": chi, "a": None, "b": None})
            continue
        if not a.senza_cura:
            applica_la_cura(chi)
        scrive = sa_scrivere_nella_cache(chi)

        # ── PROVA A ────────────────────────────────────────────────────────
        pa = os.path.join(a.lavoro, "%s-A.png" % chi)
        png_a, detto = rende_la_pagina_da_solo(chi, a, pa)
        fra = frazione_del_colore(png_a) if png_a else None
        # ⛔ «il profilo c e» non basta: col collegamento a `/tmp` quella
        #    cartella e' CONDIVISA, e il secondo inquilino ci vedrebbe dentro il
        #    profilo del PRIMO.  ⇒ Si guarda di CHI e'.
        prof = sh("ls -d /home/%s/.cache/mozilla/firefox/*/ 2>/dev/null | head -1"
                  % chi).stdout.strip()
        padrone = sh("stat -c %%U /home/%s/.cache/mozilla 2>/dev/null" % chi).stdout.strip()
        if not prof:
            profilo = "⛔ MAI NATO"
        elif padrone and padrone != chi:
            profilo = "⛔ e' di «%s»" % padrone
        else:
            profilo = "suo"
        if fra is None:
            vista_a = False
            comeche = ("⛔ il browser non ha nemmeno prodotto un'immagine"
                       if png_a is None else "⛔ l'immagine non si e' lasciata leggere")
        else:
            vista_a = fra >= FRAZIONE_MINIMA
            comeche = "la pagina copre il %.1f%% dell'immagine" % (fra * 100)
        print("  %-6s  A  %-3s  %-42s  (profilo: %s · sa scrivere in "
              "~/.cache/mozilla: %s)"
              % (chi, "SI" if vista_a else "NO", comeche, profilo,
                 "si'" if scrive else "⛔ NO"))
        if not vista_a and detto:
            # ⭐ Il motivo accanto al sintomo: «non ha disegnato» da solo
            #   nasconde tre guasti diversi, e il browser il suo lo dice.
            print("            ⛔ dice: %s" % detto.replace("\n", " ")[:160])

        # ── PROVA B ────────────────────────────────────────────────────────
        vista_b = None
        motivo_b = ""
        if a.senza_sessione:
            motivo_b = "non chiesta (--senza-sessione)"
        else:
            png1 = os.path.join(a.lavoro, "%s-B-prima.png" % chi)
            p1, f1, err1 = scatta(chi, a.parola, png1, a, a.resta_prima)
            g1 = giudice.giudica(p1) if p1 else None
            if g1 is None:
                motivo_b = ("⛔ non ho potuto guardare il desktop PRIMA: %s"
                            % (err1 or "immagine illeggibile"))
            elif g1["verdetto"] in ("nero", "quasi-nero"):
                motivo_b = ("⛔ il desktop e' «%s» PRIMA del browser: e' il "
                            "difetto della fase 10 §7.4, non C8" % g1["verdetto"])
            else:
                display, err = apri_il_browser(chi, a)
                if display is None:
                    motivo_b = "⛔ non ho potuto accendere il browser: %s" % err
                else:
                    time.sleep(a.attesa_browser)
                    png2 = os.path.join(a.lavoro, "%s-B-dopo.png" % chi)
                    p2, f2, err2 = scatta(chi, a.parola, png2, a, a.resta_dopo)
                    frb = frazione_del_colore(p2) if p2 else None
                    if frb is None:
                        motivo_b = ("⛔ non ho potuto guardare il desktop DOPO: %s"
                                    % (err2 or "immagine illeggibile"))
                    else:
                        vista_b = frb >= FRAZIONE_MINIMA
                        motivo_b = ("la pagina copre il %.1f%% dello schermo "
                                    "(desktop prima: %s · fotogrammi %s/%s)"
                                    % (frb * 100, g1["verdetto"], f1, f2))
        print("  %-6s  B  %-3s  %s"
              % (chi, "SI" if vista_b else ("NO" if vista_b is False else "?"),
                 motivo_b))

        esiti.append({"chi": chi, "a": vista_a, "b": vista_b})
        sh("pkill -KILL -u %s 2>/dev/null; loginctl terminate-user %s 2>/dev/null"
           % (chi, chi))
        time.sleep(1.5)

    # ═══════════════════════════════════════════════════════════════════════
    print()
    ra = sum(1 for e in esiti if e["a"] is True)
    fa = sum(1 for e in esiti if e["a"] is False)
    ia = sum(1 for e in esiti if e["a"] is None)
    rb = sum(1 for e in esiti if e["b"] is True)
    fb = sum(1 for e in esiti if e["b"] is False)
    ib = sum(1 for e in esiti if e["b"] is None)
    print("  A · il browser rende la pagina    : %d si' · ⛔ %d no · %d non giudicati"
          % (ra, fa, ia))
    print("  B · e la pagina si vede DAL CLIENTE: %d si' · ⛔ %d no · %d non giudicati"
          % (rb, fb, ib))

    if a.senza_cura:
        # ⛔ Col guasto innestato l'esito si LEGGE AL CONTRARIO: qui il verde e'
        #    un rosso.  ⭐ Una rete che non riesce piu' a dare rosso ha
        #    esattamente l'aspetto di una rete che non trova niente (C13).
        print()
        if fa + fb >= 1:
            print("⭐ IL GUASTO INNESTATO E' STATO VISTO: %d inquilini su %d non hanno "
                  "aperto il browser.  ⇒ questa maglia SA dare rosso" % (fa, len(esiti)))
            # ⛔ E si dice anche CHI: se avesse dato rosso il PRIMO, la prova
            #    starebbe misurando un'altra cosa (per esempio un residuo del
            #    giro precedente), e il collaudo non varrebbe.
            primi = [e["chi"] for e in esiti if e["a"] is False]
            print("   ⇒ non ce l'hanno fatta: %s" % ", ".join(primi))
            if esiti and esiti[0]["a"] is False:
                print("   ⚠ ⛔ MA HA FALLITO ANCHE IL PRIMO: il guasto atteso morde dal "
                      "SECONDO in poi.  ⇒ o il posto condiviso era gia' sporco, o "
                      "quel che si sta misurando non e' il difetto di §4.6-undecies")
                return 1
            return 0
        if ia + (ib if not a.senza_sessione else 0) and not (ra or rb):
            print("⛔ non ho potuto giudicare: non posso dire se il guasto si "
                  "sarebbe visto")
            return 3
        print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: tutti hanno aperto il "
              "browser anche senza la cura.")
        print("    ⇒ o la cura non serviva, o questa maglia non guarda nel posto "
              "giusto — e in tutt'e due i casi non ci si puo' fidare di lei.")
        return 1

    if fa or fb:
        print("⛔ ROSSO: %d inquilini su %d non hanno aperto il browser"
              % (fa + fb, len(esiti)))
        return 1
    if ia:
        print("⛔ non ho potuto guardare %d inquilini su %d nella prova A" % (ia, len(esiti)))
        return 3
    print("⭐ tutt'e %d gli inquilini hanno aperto il browser e la pagina si vede"
          % len(esiti))
    if ib:
        print("⚠ e la prova B (la pagina vista DAL CLIENTE) non ha potuto "
              "giudicarne %d: e' scritto sopra il perche', e ⛔ non e' un verde"
              % ib)
    return 0

if __name__ == "__main__":
    sys.exit(main())
