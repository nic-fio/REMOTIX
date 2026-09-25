#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g3-comune — l'aiuto comune delle tre prove del gruppo G3 (F-005, F-006,
F-008): le maglie C21, C22, C23 della fase 14 dentro la suite.

⛔ Le maglie si IMPORTANO, non si copiano: le loro funzioni di osservazione e
   di giudizio (`C21.osserva`, `C22.prova_browser`, `C22.scansiona`,
   `C23.manda`, `C23.fotografa_e_leggi`, …) girano cosi' come sono.  Una sola
   cosa va cambiata: `osserva` e `prova_browser` accendono DA SE' il browser
   (`VERI.accendi_guida`) e lo chiudono alla fine; nella suite il browser e
   l'inquilino li tiene `suite.Sessione`.  ⇒ `guida_prestata()` presta alla
   maglia il browser della sessione, con un `chiudi()` che non chiude: la
   sessione resta viva per la passata col guasto e per le osservazioni in piu'.
"""
import contextlib
import glob
import importlib.util as _iu
import os
import random
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _parola_sudo():
    """La parola di sudo del server: da REMOTIX_PAROLA_SUDO, o dalla riga «pass:» di
    ~/SERVER.ssh (lo stesso file di fondamenta/strumenti/sshpw.py). ⛔ Mai scritta
    nei banchi: sono nel deposito."""
    p = os.environ.get("REMOTIX_PAROLA_SUDO")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"
sys.path.insert(0, QUI)
import suite as S                                                     # noqa: E402

SCATOLE = os.path.join(S.BANCHI, "11-scatole")


def pazienza_ssh(scatola_cls):
    """⚠ `[M]` 24 set 2026, 10 agenti sul server: `Scatola.dentro` passa per un
    ssh del server verso se' stesso, e sshd (MaxStartups 10:30:100) chiude a
    caso le connessioni non ancora autenticate («Connection closed by … port
    22»).  Il comando in quel caso NON e' partito (si chiude prima
    dell'accesso) ⇒ si puo' ripetere.  Si riprova fino a 12 volte (circa due minuti)."""
    if getattr(scatola_cls, "_g3_pazienza", False):
        return
    originale = scatola_cls.dentro

    def dentro(self, riga, secondi=90):
        for i in range(12):
            c, t = originale(self, riga, secondi)
            if c is not None or "Connection closed by" not in (t or "") \
                    and "Connection reset" not in (t or ""):
                return c, t
            time.sleep(1 + 2 * min(i, 8) + 2 * random.random())
        return c, t
    scatola_cls.dentro = dentro
    scatola_cls._g3_pazienza = True


pazienza_ssh(S.C20V.Scatola)


def carica_maglia(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(SCATOLE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    pazienza_ssh(m.C20V.Scatola)
    return m


class Prestito:
    """Il browser della sessione, prestato a una maglia: tutto passa, tranne
    `chiudi()` (lo chiude la Sessione, all'uscita)."""

    def __init__(self, g):
        self.__dict__["_g"] = g

    def chiudi(self):
        return None

    def __getattr__(self, nome):
        return getattr(self.__dict__["_g"], nome)


@contextlib.contextmanager
def guida_prestata(veri, g):
    """Dentro il blocco `veri.accendi_guida(...)` torna il browser `g` della
    sessione (in prestito).  ⚠ `veri` e' il modulo `12-client-veri` CHE LA
    MAGLIA USA: ogni maglia caricata porta il suo."""
    vecchia = veri.accendi_guida
    veri.accendi_guida = lambda nome, o: Prestito(g)
    try:
        yield
    finally:
        veri.accendi_guida = vecchia


def cura_della_cache(sc, chi):
    """⭐ La `~/.cache` VERA all'inquilino — la cura di `src/provisiona.sh`, con
    le righe di `11-c8….applica_la_cura` (che gira DENTRO la scatola: qui si
    manda con `sc.dentro`), e la prova di scrittura di `sa_scrivere_nella_cache`.

    `[M]` 24 set 2026, rete11-gnome: `/etc/skel/.cache -> /tmp` (la scelta
    dell'utente, `DECISIONI.md` §4.6-undecies, riprodotta nella scatola) ⇒ il
    primo inquilino che apre `firefox-esr` si prende `/tmp/mozilla` a modo 0700
    e tutti gli altri vedono «Your Firefox profile cannot be loaded».  C21-C23
    non la facevano: nella fase 14 giravano da sole.  Con dieci agenti sulla
    stessa scatola la finestra di prova non nasce piu' ⇒ BLOCKED di banco."""
    c = "/home/%s/.cache" % chi
    cod, t = sc.dentro(
        "[ -L %s ] && rm -f %s; mkdir -p %s; chown %s:%s %s; chmod 700 %s; "
        "su -s /bin/sh -c 'mkdir -p ~/.cache/mozilla/.prova-g3 && "
        "rmdir ~/.cache/mozilla/.prova-g3' %s && echo scrive"
        % (c, c, c, chi, chi, c, c, chi), 60)
    return cod == 0 and "scrive" in (t or ""), (t or "")[-200:]


def prepara_o(o, s):
    """I campi che le maglie leggono da `o` e che `suite.argomenti` non mette;
    ⚠ la `~/.cache` vera all'inquilino la da' ora `suite.Sessione` (25 set):
    `cura_della_cache` resta solo come diagnosi, non si chiama piu'."""
    o.parola = s.parola
    o.utente = s.chi
    o.salva = o.evidenze or ""
    if not hasattr(o, "attesa_finestra"):
        o.attesa_finestra = 60


def evidenze_nuove(o, prima):
    """I file comparsi nelle evidenze dopo `prima` (un insieme di percorsi)."""
    if not o.evidenze:
        return []
    return sorted(set(glob.glob(os.path.join(o.evidenze, "*"))) - set(prima))


def evidenze_ora(o):
    return set(glob.glob(os.path.join(o.evidenze, "*"))) if o.evidenze else set()


DA_ESITO_GUASTO = {S.VERDE: True, S.ROSSO: False, S.CIECO: None}


def argomenti_g3(a):
    # ⚠ `[M]` 25 set: con Chrome una foto a scala 1 in 4K (+ la ricerca del
    #   ciano) costa 10-20 s sotto carico: in 60 s due foto FERME di fila non
    #   sempre ci stanno ⇒ BLOCKED «la finestra non si vede» con la finestra li'.
    a.add_argument("--attesa-finestra", type=int, default=150,
                   help="quanto si aspetta che la finestra di prova compaia ferma")


# ─────────────────────────────────────────────────────────────────────────────
#  LA SCENA E' ANCORA VIVA?  (per non dare al prodotto la colpa del server)
# ─────────────────────────────────────────────────────────────────────────────
# `[M]` 24 set 2026, sera: dieci agenti sul server, 31 GB, niente swap ⇒
#   l'OOM-killer del server ha ucciso processi; nello stesso minuto sono
#   sparite le finestre `firefox-esr` di due scene (F-006 e F-008, gnome).  Un
#   caso rosso con la scena morta NON e' un rosso del prodotto: e' BLOCKED.
def scena_viva(sc, chi):
    c, t = sc.dentro("pgrep -u %s -f '[f]irefox-esr' >/dev/null && echo viva || echo morta"
                     % chi, 30)
    return "viva" in (t or "")


def uccisi_dal_server():
    """Le righe «Killed process» del registro del kernel del server (dove gira
    la prova): si confrontano prima e dopo.  [] se non si leggono."""
    import subprocess
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "dmesg"], input=_parola_sudo(),
                           capture_output=True, text=True, timeout=20)
        return [x for x in r.stdout.splitlines() if "Killed process" in x]
    except Exception:                            # noqa: BLE001
        return []


def nuovi_uccisi(prima):
    dopo = uccisi_dal_server()
    return dopo[len(prima):] if len(dopo) >= len(prima) else dopo


def spiega_cieco(prima_oom):
    """Una frase in piu' per un BLOCKED: l'OOM-killer ha lavorato nel frattempo?"""
    n = nuovi_uccisi(prima_oom)
    if not n:
        return ""
    return (" — ⚠ durante la prova l'OOM-killer del SERVER ha ucciso %d processi (%s)"
            % (len(n), "; ".join(x.split("Killed process")[-1].split(" total-vm")[0].strip()
                                 for x in n[-3:])))


def traccia_la_ricerca(c21):
    """Diagnosi: ogni esito di `trova_finestra` stampato (rettangolo del ciano e
    bordo destro), per capire perche' due foto di fila non tornano ferme."""
    if getattr(c21, "_g3_traccia", False):
        return
    orig = c21.trova_finestra

    def trova(*a, **k):
        t0 = time.time()
        f, perche = orig(*a, **k)
        print("      [ricerca %.1fs] %s" % (time.time() - t0, ("ciano %s destro %s" % (
            f["ciano"], f["destro"])) if f else perche), flush=True)
        return f, perche
    c21.trova_finestra = trova
    c21._g3_traccia = True
