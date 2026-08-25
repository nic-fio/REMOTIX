#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-lucchetto — IL `netem` SU `lo` E' UNO SOLO, E VA POSSEDUTO A TURNO.

⛔⭐ PERCHE' ESISTE.  La disciplina di `lo` si mette con
    `tc qdisc replace dev lo root ...` e si toglie con `tc qdisc del dev lo
    root`: sono comandi che agiscono sulla **radice**, cioe' su TUTTA
    l'interfaccia.  Due banchi che guastano la rete insieme non si dividono il
    lavoro: **il secondo cancella la radice del primo**, e il primo continua a
    misurare credendo di avere un guasto che non c'e' piu'.
    ⚠ E non da' rosso: da' un numero plausibile.  E' esattamente la ferita di
    `LEZIONI.md` §1.26.

⭐ Quindi: chi vuole guastare `lo` prende il possesso, e chi non ce la fa
   **aspetta o si ferma**, non procede lo stesso.

⛔ IL POSSESSO SI PRENDE CON `mkdir`, non con un file.  `mkdir` e' atomico
   anche su ssh: o riesce (e sono io) o fallisce (e non sono io).  Un file
   scritto con `>` riesce sempre, anche a due mani, e non e' un lucchetto.

⭐ E OGNI POSSESSO HA UNA SCADENZA scritta dentro.  Un banco che muore col
   lucchetto in mano bloccherebbe tutti gli altri fino a domani; con la
   scadenza, il prossimo che arriva la legge, vede che e' passata, e **scassina
   dichiarandolo**.  ⚠ Scassinare in silenzio sarebbe peggio del blocco.

Uso (da Python):
    import importlib.util, os
    luc = ...            # carica questo file
    luc.prendi("09-b76", secondi=900)     # alza se non ce la fa
    try:  ...misura...
    finally: luc.molla("09-b76")

Uso (da riga di comando, per guardare):
    python3 banchi/09-lucchetto.py stato
    python3 banchi/09-lucchetto.py scassina     # ⛔ solo a mano, e si vede
"""
import os, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
POSTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-netem.d")


class NonMio(Exception):
    """Il lucchetto e' di un altro, e non e' scaduto."""


def _rem(comando, tetto=60):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def _root(comando, tetto=60):
    return _rem("printf '%%s\\n' '%s' | sudo -S -p '' %s"
                % (PAROLA_SUDO, comando), tetto)


def stato():
    """(chi, scadenza_epoch) oppure (None, None) se libero."""
    rc, out, _ = _root("cat %s/chi 2>/dev/null || true" % POSTO)
    riga = out.strip()
    if not riga:
        return (None, None)
    pezzi = riga.split(" ", 1)
    try:
        return (pezzi[1] if len(pezzi) > 1 else "?", float(pezzi[0]))
    except ValueError:
        return (riga, 0.0)


def prendi(chi, secondi=900, attesa=0, dillo=True):
    """⛔ `attesa` = quanti secondi sono disposto ad aspettare il mio turno.
       Zero vuol dire «o adesso o mi fermo», che e' il predefinito: un banco
       che aspetta in silenzio sembra un banco piantato."""
    fine_attesa = time.time() + attesa
    while True:
        # ⭐ L'atto atomico.  `mkdir` senza `-p`: se c'e' gia', fallisce.
        rc, _, _ = _root("mkdir %s 2>/dev/null" % POSTO)
        if rc == 0:
            scad = time.time() + secondi
            _root("bash -c \"printf '%%s %%s\\n' %d '%s' > %s/chi\""
                  % (int(scad), chi, POSTO))
            if dillo:
                print("   OK  lucchetto del netem preso da «%s» per %d s"
                      % (chi, secondi))
            return True

        altro, scad = stato()
        if scad is not None and scad > 0 and time.time() > scad:
            # ⛔⛔ LO SCASSINO E' UNA CORSA, E VA FATTO CONFRONTANDO — 25 ago 2026.
            #
            #   Fra il `cat chi` di `stato()` e questo `rm -rf` passano centinaia
            #   di millisecondi di rete.  In quella finestra **un altro
            #   corridore puo' aver gia' scassinato e preso**, e allora questo
            #   `rm -rf` cancellerebbe un lucchetto **valido e fresco**, non
            #   quello scaduto che avevamo visto.
            #
            #   `[M]` 25 agosto: un banco ha stampato «SCASSINO «10-e2», scaduto
            #   da 1 s» quaranta secondi dopo che uno `stato` diceva «10-e4,
            #   scade fra 1802 s».  ⛔ Nessuno se n'e' accorto sul momento: due
            #   banchi avrebbero potuto misurare insieme, e i due numeri
            #   sarebbero stati **plausibili tutt'e due**.
            #
            # ⇒ Si rilegge il file e si cancella **solo se e' ancora lo stesso**
            #   byte per byte.  E' un confronto-e-cancella: la finestra non si
            #   chiude del tutto (non e' atomico nel nucleo), ma passa da
            #   «centinaia di ms» a «il tempo di un comando».
            print("   ⚠   il lucchetto era di «%s», scaduto da %d s: SCASSINO"
                  % (altro, int(time.time() - scad)))
            atteso = "%d %s" % (int(scad), altro)
            # ⚠ Il confronto lo fa la macchina, in un comando solo: portarlo
            #   qui vorrebbe dire riaprire la finestra che stiamo chiudendo.
            cmd = (r"""bash -c 'letto=$(cat "POSTO/chi" 2>/dev/null); """
                   r"""if [ "$letto" = "ATTESO" ]; then rm -rf "POSTO"; exit 0; """
                   r"""else exit 4; fi'""")
            cmd = cmd.replace("POSTO", POSTO).replace("ATTESO", atteso)
            rc, _, _ = _root(cmd)
            if rc == 4:
                print("   ⭐  NON scassino: nel frattempo il lucchetto e'"
                      " CAMBIATO — era di un altro, fresco.")
            continue

        if time.time() >= fine_attesa:
            raise NonMio("il netem su `lo` e' di «%s» ancora per %d s: "
                         "NON misuro, perche' un guasto che non e' mio "
                         "darebbe un numero plausibile e falso"
                         % (altro, int((scad or 0) - time.time())))
        if dillo:
            print("   --  aspetto il mio turno (e' di «%s»)..." % altro,
                  flush=True)
        time.sleep(5)


def molla(chi, dillo=True):
    altro, _ = stato()
    if altro not in (None, chi):
        print("   ⚠   NON mollo: il lucchetto adesso e' di «%s», non mio "
              "(mi hanno scassinato)" % altro)
        return False
    _root("rm -rf %s" % POSTO)
    if dillo:
        print("   OK  lucchetto mollato da «%s»" % chi)
    return True


if __name__ == "__main__":
    passo = sys.argv[1] if len(sys.argv) > 1 else "stato"
    if passo == "stato":
        chi, scad = stato()
        if chi is None:
            print("libero")
        else:
            print("di «%s», scade fra %d s" % (chi, int(scad - time.time())))
    elif passo == "scassina":
        _root("rm -rf %s" % POSTO)
        print("scassinato a mano")
    else:
        print(__doc__)
