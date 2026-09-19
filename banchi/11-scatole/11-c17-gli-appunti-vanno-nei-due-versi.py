#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c17 — ⭐ «GLI APPUNTI VANNO NEI DUE VERSI»
===========================================================================

    python3 11-c17-gli-appunti-vanno-nei-due-versi.py --porta 8512
    python3 11-c17-gli-appunti-vanno-nei-due-versi.py --porta 8512 --senza-copia

    che cosa deve essere vero : un testo copiato sul dispositivo si incolla nel
                                desktop, e uno copiato nel desktop arriva al
                                dispositivo — anche a chi si RIATTACCA
    da dove parte             : una sessione nuova, un inquilino nuovo
    che cosa guarda           : tre fatti, ciascuno col suo nome
      A  dispositivo → sessione   `wl-paste` nella sessione legge il testo
                                  che il cliente ha annunciato
      B  sessione → dispositivo   `wl-copy` nella sessione, e il server lo
                                  ANNUNCIA al cliente attaccato (§7.4)
      R  chi si riattacca         un cliente nuovo sullo stesso figlio lo
                                  riceve intero, senza che nessuno ricopi
    come so che sa dare rosso : `--senza-copia` — nessuno copia niente, da
                                nessuna delle due parti ⇒ tre rossi

⭐ Nata in fase 12 (19 set 2026): gli appunti di KDE erano provati solo a mano
   (`07-b54`), e questa maglia li mette nella rete.  E al primo giro ha
   trovato un difetto VERO, di tutti i desktop: il testo copiato nella sessione
   prima che la sessione RCP fosse aperta si teneva e non si annunciava mai
   (`src/rcp.c`, `annuncia_il_tenuto`) ⇒ il fatto R.

⛔ Due implementazioni ai due lati, e nessuna e' il server: `01-b3-cliente.py`
   (che ha letto solo `RCP.md`) e `wl-clipboard` (un client Wayland che non ha
   mai sentito parlare di RCP).
⚠ `wl-clipboard` parla `zwlr_data_control_manager_v1`: KWin ce l'ha, Mutter
   no, e su GNOME `wl-copy` ripiega sul trucco della finestra col fuoco.  Se
   su GNOME l'arbitro non regge, e' l'arbitro — e lo si dice (esito 3), non si
   chiama rosso il prodotto.

Esiti: 0 verde · 1 rosso · 3 non ho potuto guardare (⛔ NON e' un rosso).
⛔ Con `--senza-copia` si legge al contrario: 0 = il guasto e' stato VISTO.
"""
import argparse
import importlib.util
import json
import os
import random
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")
PAROLA = "provanic2026"


def carica_c1():
    """Da C1 vengono l'ammissione e i gruppi della scheda: un posto solo (§1.47)."""
    for p in (os.path.join(QUI, "11-c1-nasce-e-si-vede.py"),):
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("c1", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if callable(getattr(m, "e_stato_ammesso", None)) and \
               callable(getattr(m, "garantisci_i_gruppi", None)):
                return m
    print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me ⇒ non ho potuto guardare")
    sys.exit(3)


def corri(argv, tempo=30, **kw):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=tempo, **kw)
    except subprocess.TimeoutExpired:
        return None


def sgombera(chi):
    corri(["loginctl", "terminate-user", chi], 15)
    for _ in range(40):
        r = corri(["pgrep", "-u", chi], 5)
        if r is None or r.returncode != 0:
            break
        time.sleep(0.25)
    corri(["pkill", "-KILL", "-u", chi], 5)
    corri(["userdel", "-r", chi], 15)


def nella_sessione(chi, copione, tempo=15):
    """Un copione dentro la sessione Wayland dell'inquilino.  `None` = non c'e'."""
    uid = corri(["id", "-u", chi], 5).stdout.strip()
    run = "/run/user/%s" % uid
    socket = sorted(f for f in os.listdir(run)
                    if f.startswith("wayland-") and f[8:].isdigit()) if os.path.isdir(run) else []
    if not socket:
        return None
    r = corri(["runuser", "-u", chi, "--", "env", "XDG_RUNTIME_DIR=" + run,
               "WAYLAND_DISPLAY=" + socket[0], "sh", "-c", copione], tempo)
    return None if r is None else r.stdout


def cliente(chi, porta, *altro):
    return ["python3", "-u", CLIENTE, "--indirizzo", "127.0.0.1", "--porta", str(porta),
            "--utente", chi, "--parola", PAROLA] + list(altro)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--senza-copia", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: nessuno copia niente ⇒ tre rossi")
    p.add_argument("--attesa", type=float, default=20.0)
    a = p.parse_args()
    c1 = carica_c1()

    chi = "c17u%d" % random.randint(100, 999)
    marca = random.randint(10000, 99999)
    testo_a = "C17-A-àèìòù-%d" % marca
    testo_b = "C17-B-€ß→%d" % marca
    esito_a = "/tmp/%s-a.json" % chi
    esito_r = "/tmp/%s-r.json" % chi
    segnale = "/tmp/%s-segnale" % chi
    print("== C17 — gli appunti vanno nei due versi (%s, porta %d)%s"
          % (chi, a.porta, "  ⛔ GUASTO INNESTATO: --senza-copia" if a.senza_copia else ""))

    sgombera(chi)
    if corri(["useradd", "-m", "-s", "/bin/bash", chi]).returncode != 0:
        print("⛔ non ho potuto creare l'inquilino ⇒ non ho potuto guardare")
        return 3
    corri(["chpasswd"], input="%s:%s\n" % (chi, PAROLA))
    e_gr, perche = c1.garantisci_i_gruppi(chi)
    if e_gr != 0:
        print("⛔ %s ⇒ non ho potuto guardare" % perche)
        sgombera(chi)
        return 3
    for f in (esito_a, esito_r, segnale):
        if os.path.exists(f):
            os.unlink(f)

    try:
        # ── il primo cliente: annuncia A, resta, e ascolta gli annunci ─────
        argv = cliente(chi, a.porta, "--segnale", segnale, "--resta", "25",
                       "--appunti-scrivi", esito_a)
        if not a.senza_copia:
            argv += ["--appunti-copia", testo_a]
        primo = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True)
        fine = time.time() + 60
        while not os.path.exists(segnale) and time.time() < fine and primo.poll() is None:
            time.sleep(0.25)
        if not os.path.exists(segnale):
            uscita = primo.communicate(timeout=30)[0] if primo.poll() is None else primo.stdout.read()
            amm = c1.e_stato_ammesso(uscita)
            print("⛔ il cliente non si e' attaccato (ammesso: %s) ⇒ non ho potuto guardare" % amm)
            return 3

        # ⛔ L'ARBITRO C'E'?  `[M]` 19 set 2026, scatola `gnome`: senza il
        #    protocollo `wl-paste` e `wl-copy` restano APPESI fino al `timeout`
        #    (uscita 124) — aspettano un fuoco che una sessione senza schermo
        #    non da' mai — mentre il registro del server dice «22 byte
        #    consegnati alla sessione».  ⇒ Non e' il prodotto: si esce 3.
        # ⚠ E si decide solo quando il compositore RISPONDE (`wl_compositor`
        #   nell'elenco): un `wayland-info` fallito a compositore non pronto
        #   darebbe un elenco vuoto, e un 3 su una sessione sana.
        protocolli = None
        for _ in range(30):
            elenco = nella_sessione(chi, "wayland-info 2>/dev/null | grep -o -E "
                                         "'wl_compositor|zwlr_data_control_manager_v1|"
                                         "ext_data_control_manager_v1' | sort -u")
            if elenco and "wl_compositor" in elenco:
                protocolli = elenco.replace("wl_compositor", "")
                break
            time.sleep(1)
        if protocolli is None:
            print("   ⚠ il compositore non risponde a `wayland-info` in 30 s ⇒ non ho potuto guardare")
            return 3
        if not protocolli or not protocolli.strip():
            print("   ⚠ il compositore non offre ne' `zwlr_data_control_manager_v1` ne'")
            print("     `ext_data_control_manager_v1`: `wl-clipboard` qui NON e' un arbitro")
            print("     ⇒ non ho potuto guardare — ⛔ e NON e' un rosso del prodotto")
            return 3
        print("   l'arbitro c'e': %s" % " ".join(protocolli.split()))

        # A — dispositivo → sessione
        visto, t0 = None, time.time()
        while time.time() - t0 < a.attesa:
            visto = nella_sessione(chi, "timeout 5 wl-paste -n 2>/dev/null")
            if visto == testo_a:
                break
            time.sleep(1)
        ok_a = visto == testo_a
        print("   A  dispositivo → sessione : %s  (atteso «%s», la sessione incolla «%s», %.0f s)"
              % ("⭐ SI" if ok_a else "⛔ NO", testo_a, visto, time.time() - t0))
        if visto is None:
            print("   ⚠ nessun socket Wayland: la sessione non c'e' ⇒ non ho potuto guardare")
            return 3

        # B — sessione → dispositivo, a cliente attaccato
        if not a.senza_copia:
            nella_sessione(chi, "pkill -x wl-copy; printf %%s '%s' | timeout 90 wl-copy "
                                ">/dev/null 2>&1 &" % testo_b)
        uscita = primo.communicate(timeout=60)[0]
        # ⚠ Dall'uscita del cliente e non dal suo file: il file lo scrive PRIMA
        #   di restare attaccato (`scrivi_appunti` sta prima di `--resta`), e
        #   l'annuncio di B arriva dopo.
        annunci = [(int(m.group(1)), int(m.group(2))) for m in re.finditer(
            r"il server annuncia il trasferimento (\d+), (\d+) byte", uscita)]
        lungo_b = len(testo_b.encode("utf-8"))
        ok_b = any(n == lungo_b for _, n in annunci)
        print("   B  sessione → dispositivo  : %s  (annunci del server: %s, atteso uno da %d byte)"
              % ("⭐ SI" if ok_b else "⛔ NO", annunci, lungo_b))

        # R — chi si riattacca riceve il testo della sessione
        r = corri(cliente(chi, a.porta, "--appunti-attendi", "15", "--appunti-scrivi", esito_r), 60)
        try:
            ricevuto = json.load(open(esito_r))["ricevuto"]
        except (OSError, ValueError, KeyError):
            ricevuto = None
        ok_r = ricevuto == testo_b
        print("   R  chi si riattacca       : %s  (atteso «%s», ricevuto «%s»)"
              % ("⭐ SI" if ok_r else "⛔ NO", testo_b, ricevuto))
        if r is not None and c1.e_stato_ammesso(r.stdout) is False:
            print("   ⛔ il secondo cliente e' stato RESPINTO ⇒ non ho potuto guardare")
            return 3

        # ⛔ Col guasto innestato l'esito si legge AL CONTRARIO, come in tutta la
        #    rete (C8 `--senza-cura`): 0 = il guasto e' stato VISTO.  `[M]` 19
        #    set 2026, il primo giro nella rete: usciva 1 su tre rossi, e il
        #    gancio ha detto «guasto non visto» — aveva ragione lui.
        if a.senza_copia:
            if not (ok_a or ok_b or ok_r):
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO: A, B e R tutti rossi")
                return 0
            print("⛔⛔ il guasto innestato NON e' stato visto: qualcosa e' verde senza copie")
            return 1
        if ok_a and ok_b and ok_r:
            print("⭐ VERDE — i due versi, e anche chi si riattacca")
            return 0
        print("⛔⛔ ROSSO — %s" % ", ".join(n for n, v in (("A", ok_a), ("B", ok_b), ("R", ok_r)) if not v))
        return 1
    finally:
        sgombera(chi)
        for f in (esito_a, esito_r, segnale):
            if os.path.exists(f):
                os.unlink(f)


if __name__ == "__main__":
    sys.exit(main())
