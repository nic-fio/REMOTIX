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
   (che ha letto solo `RCP.md`) e **GTK** (`appunti-gtk.py`), che non e' nostro
   e non ha mai sentito parlare di RCP.
⭐⭐ E L'ARBITRO E' LO STESSO SUI DUE DESKTOP — 20 set 2026.  Prima erano
   `wl-copy`/`wl-paste`, che parlano `zwlr_data_control_manager_v1`: KWin ce
   l'ha, ⛔ Mutter no, e su GNOME la maglia usciva 3 («non ho potuto
   guardare»).  ⇒ Adesso si fa come fa una PERSONA: si apre una finestra vera,
   ⭐ **le si da' il fuoco con un clic mandato attraverso il prodotto**
   (`01-b3-cliente.py --clic`), e da li' in poi gli appunti si toccano — su
   GNOME come su KDE.  ⚠ E se il clic non arrivasse, il rosso sarebbe del
   prodotto che non consegna l'input: e' la stessa strada di C4.

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
# ⭐ L'arbitro esterno: GTK, cioe' `wl_data_device` — la clipboard delle
#    applicazioni vere.  ⛔ Vuole il FUOCO, e il fuoco lo da' il clic del
#    cliente (`--clic`).  Sta accanto a questa maglia dentro la scatola.
# ⚠ Dove l'arbitro racconta la sua copia: il banco lo LEGGE invece di dormire
#   un tempo fisso — con GTK la copia parte quando arriva il fuoco, e il fuoco
#   arriva col clic del cliente (ogni 4 s), non a un'ora decisa da noi.
#
# ⛔⛔ E IL FILE E' DELL'INQUILINO, non uno per tutti — 21 set 2026.
#   Qui c'era `PROVA_COPIA = "/tmp/remotix-arbitro-copia.log"`: UN nome fisso,
#   scritto e cancellato DALL'INQUILINO (il copione gira con `runuser -u chi`),
#   e ⛔ mai tolto alla fine.  `[R]` dal codice, e la stessa forma di
#   `/tmp/mozilla` (C2): il primo `c17uNNN` lo crea, `userdel` lo lascia a un
#   uid senza nome, e `/tmp` ha il bit «sticky» ⇒ un inquilino con un ALTRO uid
#   non puo' ne' toglierlo (`rm -f` fallisce in silenzio) ne' riscriverlo
#   (`>` rifiutato) ⇒ il guscio non esegue il comando della copia ⇒ ⛔ **B e R
#   rossi, cioe' «il server non annuncia la copia fatta nel desktop»**, mentre
#   nessuno aveva copiato niente.
#   ⚠ E morde SOLO in una scatola vecchia: finche' gli utenti restano gli stessi
#     `useradd` ridà a ogni `c17u` lo stesso uid (4012) e il file resta suo;
#     ⛔ basta un inquilino rimasto da un giro morto (`[M]` 21 set: in kde
#     `user@4024` e `user@4025` falliti, cioe' uid ben oltre 4012) e l'uid di
#     C17 si sposta.  `[?]` il nesso diretto non e' stato misurato dentro la
#     scatola vecchia: e' la sola scrittura condivisa fra inquilini diversi
#     che C17 fa, e combacia con la bisezione (scatola nuova ⇒ verde 2 su 2).
# ⭐ Ora il nome porta l'inquilino, come `esito_a` ed `esito_r`, e si toglie
#   alla fine: nessun giro lascia niente al giro dopo.
def prova_copia(chi):
    return "/tmp/%s-arbitro-copia.log" % chi


ARBITRO_GTK = ("env GDK_BACKEND=wayland python3 " +
               os.path.join(QUI, "appunti-gtk.py"))


def arbitro(chi):
    """⭐ L'arbitro che QUESTO desktop permette — e si CHIEDE, non si indovina.

    ⛔ `[M]` 20 set 2026, misurato su tutt'e due le scatole:
      · dove c'e' `zwlr_data_control_manager_v1` (KWin) `wl-clipboard` legge e
        scrive senza bisogno del fuoco, ed e' la strada piu' corta;
      · dove non c'e' (Mutter) `wl-copy` e `wl-paste` restano APPESI, e l'unica
        strada e' quella delle applicazioni vere: GTK piu' il fuoco, che arriva
        col clic mandato dal cliente (`--clic`).
    ⚠ La differenza e' del BANCO, non del prodotto: il prodotto su tutt'e due i
      desktop fa la stessa cosa, e le due strade portano allo stesso giudizio.
    """
    elenco = nella_sessione(chi, "wayland-info 2>/dev/null | grep -c -E "
                                 "'zwlr_data_control_manager_v1|"
                                 "ext_data_control_manager_v1'") or "0"
    if elenco.strip().lstrip("0"):
        return {"nome": "wl-clipboard",
                "incolla": "timeout 8 wl-paste -n 2>/dev/null",
                "copia": "pkill -x wl-copy; printf %%s '%s' | timeout 90 wl-copy "
                         ">" + prova_copia(chi) + " 2>&1 &",
                "attesa_copia": 3, "dice": ""}
    return {"nome": "GTK col fuoco (il clic del cliente)",
            "incolla": ARBITRO_GTK + " incolla 2>/dev/null",
            "copia": ARBITRO_GTK + " copia '%s' 60 >" + prova_copia(chi) + " 2>&1 &",
            "attesa_copia": 30, "dice": "copiato A FUOCO"}


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


def socket_wayland(chi):
    """Il socket del compositore dell'inquilino, o `None` se non c'e' ancora."""
    r = corri(["id", "-u", chi], 5)
    run = "/run/user/%s" % (r.stdout.strip() if r else "")
    if not os.path.isdir(run):
        return None
    nomi = sorted(f for f in os.listdir(run)
                  if f.startswith("wayland-") and f[8:].isdigit())
    return nomi[0] if nomi else None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ UN ATTREZZO CHE MANCA NON E' UN ROSSO — 21 set 2026, fase 13.
#
# `[R]` Qui si prendeva lo `stdout` del copione senza guardare il codice
#   d'uscita.  ⇒ Nella scatola xfce (e lxqt), dove `wl-clipboard` non c'era,
#   `wl-paste: command not found` diventava `""`, la guardia di A (che guarda
#   `None`) non scattava, e la maglia stampava **ROSSO**: un difetto del BANCO
#   con la faccia di un difetto del prodotto (§1.51).
# ⛔ E col guasto innestato era peggio: A, B e R tutti «NO» per mancanza
#   d'attrezzi ⇒ «IL GUASTO INNESTATO E' STATO VISTO», esito 0 ⇒ una
#   certificazione per C13 che non aveva guardato niente.
# ⇒ Due reti, una sotto l'altra:
#   1. ⭐ un controllo POSITIVO prima di cominciare (`attrezzo_che_manca`):
#      ogni pezzo che l'arbitro scelto userà si CHIEDE alla sessione;
#   2. e qui, per quel che sfugge: il guscio che esce 126/127 (comando non
#      trovato / non eseguibile) non da' uno stdout, da' `AttrezzoMancante`.
# ⚠ E il resto NON cambia: un attrezzo presente che risponde `""` (appunti
#   vuoti) resta un «NO», come prima — e' il caso che la maglia deve vedere.
# ═══════════════════════════════════════════════════════════════════════════
class AttrezzoMancante(Exception):
    """Nella sessione manca un pezzo del BANCO ⇒ esito 3, mai 1 e mai 0."""


# `[R]` POSIX, «Command Search and Execution»: 127 = non trovato, 126 =
#   trovato ma non eseguibile.  `timeout` e `env` li ripassano uguali.
NON_TROVATO = (126, 127)


def nella_sessione_rc(chi, copione, tempo=15):
    """Come `nella_sessione`, ma torna `(codice, stdout)`.  `None` = non c'e'."""
    uid = corri(["id", "-u", chi], 5).stdout.strip()
    run = "/run/user/%s" % uid
    socket = sorted(f for f in os.listdir(run)
                    if f.startswith("wayland-") and f[8:].isdigit()) if os.path.isdir(run) else []
    if not socket:
        return None
    r = corri(["runuser", "-u", chi, "--", "env", "XDG_RUNTIME_DIR=" + run,
               "WAYLAND_DISPLAY=" + socket[0], "sh", "-c", copione], tempo)
    return None if r is None else (r.returncode, r.stdout)


def nella_sessione(chi, copione, tempo=15):
    """Un copione dentro la sessione Wayland dell'inquilino.  `None` = non c'e'.

    ⛔ Se il guscio dice «comando non trovato» (126/127) solleva
       `AttrezzoMancante` invece di tornare uno stdout vuoto (vedi sopra).
    """
    r = nella_sessione_rc(chi, copione, tempo)
    if r is None:
        return None
    codice, uscita = r
    if codice in NON_TROVATO:
        raise AttrezzoMancante("«%s» esce %d (comando non trovato o non eseguibile)"
                               % (copione, codice))
    return uscita


# ⭐ I pezzi che ciascun arbitro usa — e come si CHIEDE se ci sono.
#   ⚠ `wayland-info` sta in tutti e due: e' lui che SCEGLIE l'arbitro, e se
#     mancasse la scelta cadrebbe su GTK in silenzio (`grep -c` risponde «0»).
#   ⚠ Per GTK non basta `command -v`: `python3` c'e' sempre, e' `import gi`
#     con GTK 4 che manca ⇒ lo si importa davvero, come fa `appunti-gtk.py`.
ATTREZZI_COMUNI = [
    ("wayland-info (wayland-utils)", "command -v wayland-info"),
]
ATTREZZI = {
    "wl-clipboard": [
        ("wl-paste (wl-clipboard)", "command -v wl-paste"),
        ("wl-copy (wl-clipboard)", "command -v wl-copy"),
    ],
    "GTK": [
        ("appunti-gtk.py", "test -r " + os.path.join(QUI, "appunti-gtk.py")),
        ("python3-gi + gir1.2-gtk-4.0",
         "python3 -c 'import gi; gi.require_version(\"Gtk\", \"4.0\"); "
         "gi.require_version(\"Gdk\", \"4.0\"); "
         "from gi.repository import Gdk, Gtk'"),
    ],
}


def attrezzo_che_manca(chi, elenco):
    """⭐ Il controllo POSITIVO: torna il nome del primo pezzo che manca, o `None`.

    ⛔ Un pezzo di cui la sessione non risponde (niente socket, tempo scaduto)
       conta come mancante: non so se c'e', e allora non guardo.
    """
    for nome, prova in elenco:
        r = nella_sessione_rc(chi, prova + " >/dev/null 2>&1", 30)
        if r is None or r[0] != 0:
            return nome
    return None


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
    for f in (esito_a, esito_r, segnale, prova_copia(chi)):
        if os.path.exists(f):
            os.unlink(f)

    primo = None
    try:
        # ── il primo cliente: annuncia A, resta, e ascolta gli annunci ─────
        # ⭐ `--clic`: il fuoco alle finestre dell'arbitro, e si RIFA' ogni 4 s
        #    perche' le finestre sono due, una dopo l'altra (leggere, copiare).
        argv = cliente(chi, a.porta, "--segnale", segnale, "--resta", "75",
                       "--clic", "960,540", "--clic-dopo", "3", "--clic-ogni", "4",
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

        # ⭐ IL CLIC LO MANDA IL CLIENTE (`--clic`): qui si aspetta solo che
        #    la finestra dell'arbitro sia in piedi e col fuoco.
        # A — dispositivo → sessione
        # ⚠ Una chiamata sola e generosa, non un giro di chiamate: l'arbitro
        #   apre la sua finestra e ASPETTA il fuoco (che arriva col clic del
        #   cliente, ogni 4 s), poi legge.  Chiamarlo dieci volte vorrebbe dire
        #   dieci finestre che si rubano il fuoco a vicenda.
        t0 = time.time()
        # ⛔ Prima il SOCKET: il segnale del cliente dice «sono attaccato», non
        #    «la sessione grafica c'e'».  Chiedere l'arbitro prima del
        #    compositore darebbe «None» e un rosso che non e' del prodotto.
        while time.time() - t0 < 90 and socket_wayland(chi) is None:
            time.sleep(1)
        if socket_wayland(chi) is None:
            print("   ⚠ nessun socket Wayland in 90 s: la sessione non c'e'"
                  " ⇒ non ho potuto guardare")
            return 3
        # ⚠ Qualche tentativo, uno alla volta: l'offerta del prodotto alla
        #   sessione arriva quando gli appunti si aprono, che e' dopo il palco.
        #   ⛔ Non in parallelo: due finestre si ruberebbero il fuoco.
        # ⛔ PRIMA si chiede se gli attrezzi ci sono (vedi `AttrezzoMancante`):
        #    uno che manca e' «non ho potuto guardare», ⛔ mai un rosso.
        manca = attrezzo_che_manca(chi, ATTREZZI_COMUNI)
        arb = arbitro(chi) if manca is None else None
        if arb is not None:
            print("   l'arbitro di questo desktop: %s" % arb["nome"])
            chiave = "wl-clipboard" if arb["nome"] == "wl-clipboard" else "GTK"
            manca = attrezzo_che_manca(chi, ATTREZZI[chiave])
        if manca is not None:
            print("   ⛔ nella sessione manca «%s»: e' un attrezzo del BANCO, non del"
                  " prodotto ⇒ non ho potuto guardare" % manca)
            if primo.poll() is None:
                primo.kill()
            return 3
        visto = None
        for _ in range(5):
            visto = nella_sessione(chi, arb["incolla"], 60)
            if visto == testo_a:
                break
            time.sleep(4)
        ok_a = visto == testo_a
        print("   A  dispositivo → sessione : %s  (atteso «%s», la sessione incolla «%s», %.0f s)"
              % ("⭐ SI" if ok_a else "⛔ NO", testo_a, visto, time.time() - t0))
        if visto is None:
            print("   ⚠ nessun socket Wayland: la sessione non c'e' ⇒ non ho potuto guardare")
            return 3

        # B — sessione → dispositivo, a cliente attaccato
        if not a.senza_copia:
            nella_sessione(chi, "rm -f " + prova_copia(chi))
            nella_sessione(chi, arb["copia"] % testo_b)
            # ⚠ Si aspetta che la copia sia AVVENUTA, non un tempo fisso: con GTK
            #   parte quando arriva il fuoco, e il fuoco arriva col clic del
            #   cliente.  ⛔ Un'attesa a orologio dava un rosso intermittente
            #   (`[M]` 20 set 2026, la rete: B e R rossi, gli stessi giri verdi
            #   a mano un minuto prima).
            t1 = time.time()
            while time.time() - t1 < arb["attesa_copia"]:
                time.sleep(1)
                if not arb["dice"]:
                    break
                detto = nella_sessione(chi, "cat " + prova_copia(chi) + " 2>/dev/null") or ""
                if arb["dice"] in detto:
                    print("   la copia nella sessione e' avvenuta dopo %.0f s"
                          % (time.time() - t1))
                    break
            else:
                if arb["dice"]:
                    print("   ⚠ in %d s l'arbitro non ha detto «%s»: la copia "
                          "nella sessione non e' partita"
                          % (arb["attesa_copia"], arb["dice"]))
            time.sleep(2)
        # ⚠ Il tetto e' piu' largo di `--resta` del cliente (75 s), o si
        #   scadrebbe aspettando un cliente che sta facendo il suo mestiere.
        uscita = primo.communicate(timeout=150)[0]
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
    except AttrezzoMancante as e:
        # ⛔ La seconda rete: un attrezzo sfuggito al controllo di prima.
        #    ⇒ 3, anche col guasto innestato (dove altrimenti sarebbe stato 0).
        print("   ⛔ un attrezzo del BANCO manca nella sessione: %s"
              " ⇒ non ho potuto guardare" % e)
        if primo is not None and primo.poll() is None:
            primo.kill()
        return 3
    finally:
        sgombera(chi)
        for f in (esito_a, esito_r, segnale, prova_copia(chi)):
            if os.path.exists(f):
                os.unlink(f)


if __name__ == "__main__":
    sys.exit(main())
