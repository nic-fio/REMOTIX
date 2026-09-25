#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f029 — F-029 VOCI PERICOLOSE ASSENTI

    python3 15-f029-voci-pericolose-assenti.py --scatola kde --browser chrome [--guasto]

ATTESO (`DECISIONI.md` §4.7 e §4.1-ter): nel menu d'uscita del desktop NON ci
sono blocco, sospensione (e ibernazione, sonno ibrido), riavvio, spegnimento
— ne' «Cambia utente» (decisione dell'utente del 21 set 2026: «l'unica voce
che deve rimanere è logout»); «Esci» (Log Out) C'E'.

COME SI GUARDA — il menu si APRE DAVVERO dal browser (clic veri sulla tela),
come fa l'utente:
    gnome  menu di sistema in alto a destra → pulsante d'accensione
    kde    lanciatore (Kickoff) in basso a sinistra → «Leave»
    xfce   pulsante d'azione del pannello (il nome dell'utente, in alto a destra)
    lxqt   menu principale in basso a sinistra → «Leave»
Ogni livello si fotografa (evidenza per l'utente).

⭐ CHI GIUDICA — L'OCR DELLA FOTOGRAFIA (tesseract 5.5, estratto senza root
   in /media/REMOTIX/strumenti/tesseract: vedi `15-g1b-comune.py`).  Il menu
   si ritaglia come la macchia che cambia fra la foto prima e quella dopo il
   clic, e si legge; le voci vietate si cercano nelle RIGHE lette.
   ⚠ Su GNOME il sottomenu ha il TITOLO «Power Off» (e' l'intestazione, non
     una voce): si scarta la riga piu' in alto che dice solo «Power Off».
   ⚠ Su GNOME il blocco e' un'ICONA senza testo, che l'OCR non legge: per
     quella sola voce giudica il CAMPO — la voce compare solo se c'e' GDM sul
     bus di sistema (`loginManager.js` canLock) e `disable-lock-screen` e'
     falso; letti DENTRO la sessione dell'inquilino.
   ⭐ E per tutti, i campi della cintura 1 (`remotix-niente-spegnimento.rules`):
     logind CanPowerOff/CanReboot/CanSuspend/CanHibernate/CanHybridSleep
     chiesti COME L'INQUILINO devono dire «no» (o «na») — sono le risposte
     da cui GNOME e Plasma decidono se mostrare le voci.
   PASS = OCR pulito + «Esci» letto + campi giusti.  Il menu che non si apre
   (nessuna macchia) = BLOCKED; «Esci» non letto in un menu aperto = FAIL.

GUASTO (due, tutt'e due devono dare rosso):
   A) l'elenco delle voci vietate che include «Log Out/Esci»: lo stesso testo
      letto dal menu vero deve dare ROSSO;
   B) la lettura del campo fatta dal posto sbagliato: logind chiesto da ROOT
      (che ha CAP_SYS_BOOT e si sente dire «yes», vedi la regola polkit) —
      il giudice dei campi deve dare ROSSO.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._carica("g1b", os.path.join(S.QUI, "15-g1b-comune.py"))
FUNZIONI = ("F-029",)

VIETATE = [
    ("blocco", r"\block\b|lock\s*screen|screen\s*lock|\bblocca"),
    ("sospensione", r"suspend|sospendi|sospensione|\bsleep\b|standby"),
    ("ibernazione", r"hibernat|iberna"),
    ("riavvio", r"restart|reboot|riavvia"),
    ("spegnimento", r"shut\s*down|power\s*off|spegni|arresta"),
    ("cambia utente", r"switch\s*user|cambia\s*utente"),
]
ESCI = r"log\s*-?\s*out|esci|disconnetti"
VIETATE_COL_GUASTO = VIETATE + [("esci (GUASTO)", ESCI)]

# logind: le risposte giuste, chiesta come l'inquilino
LOGIND = ("CanPowerOff", "CanReboot", "CanSuspend", "CanHibernate", "CanHybridSleep")
# ⚠ «negato»: `[M]` 24 set 2026, CanPowerOff e CanReboot chiesti dall'inquilino
#   rispondono «Call failed: Access denied» (la regola polkit dice NO), mentre
#   da root dicono «yes».  GNOME e Plasma trattano l'errore come «non si puo'».
LOGIND_BUONE = ("no", "na", "negato")


# ═══════════════════════════════════════════════════════════════════════════
#  IL GIUDICE (funzioni pure)
# ═══════════════════════════════════════════════════════════════════════════
def giudica_righe(righe, desktop, vietate=VIETATE):
    """righe = [(frase, x, y)].  Torna (trovate [(famiglia, frase)], esci_letto,
    righe_scartate)."""
    scartate = []
    righe = list(righe)
    if desktop == "gnome":
        titoli = [r for r in righe if re.fullmatch(r"\W*\w?\W*power\s*off\W*", r[0], re.I)]
        if titoli:
            y0 = min(r[2] for r in titoli)
            scartate = [r for r in titoli if abs(r[2] - y0) < 15]
            righe = [r for r in righe if r not in scartate]
    trovate = []
    for frase, _x, _y in righe:
        for fam, rx in vietate:
            if re.search(rx, frase, re.I):
                trovate.append((fam, frase))
    esci = any(re.search(ESCI, f, re.I) for f, _x, _y in righe)
    return trovate, esci, scartate


def giudica_campi(campi, desktop):
    """campi = {nome: valore letto}.  Torna [difetti]."""
    guai = []
    for k in LOGIND:
        v = campi.get(k)
        if v is None:
            guai.append("%s non letto" % k)
        elif v not in LOGIND_BUONE:
            guai.append("%s=%s (atteso no/na)" % (k, v))
    if desktop == "gnome":
        gdm, dis = campi.get("gdm_sul_bus"), campi.get("disable-lock-screen")
        if gdm is None:
            guai.append("GDM sul bus: non letto")
        elif gdm and dis != "true":
            guai.append("GDM c'e' e disable-lock-screen=%s: l'icona del blocco c'e'" % dis)
    return guai


def certifica():
    guai = []

    def prova(cosa, vero):
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
        if not vero:
            guai.append(cosa)

    menu_gnome = [("(Power Off", 3500, 140), ("Log Out...", 3490, 212)]
    t, e, sc = giudica_righe(menu_gnome, "gnome")
    prova("gnome: il titolo «Power Off» si scarta, «Log Out» c'e'", not t and e and sc)
    t, e, _ = giudica_righe(menu_gnome + [("Power Off...", 3490, 180)], "gnome")
    prova("gnome: la VOCE «Power Off…» sotto il titolo e' rossa", bool(t) and e)
    t, e, _ = giudica_righe(menu_gnome, "kde")
    prova("kde: «Power Off» non e' un titolo, e' rossa", bool(t))
    for voce in ("Lock Screen", "Suspend", "Sleep", "Hibernate", "Restart", "Shut Down",
                 "Switch User", "Blocca schermo", "Riavvia"):
        t, e, _ = giudica_righe([(voce, 10, 10), ("Logout", 10, 40)], "lxqt")
        prova("«%s» e' vietata" % voce, bool(t) and e)
    t, e, _ = giudica_righe([("Accessories", 1, 1), ("Leave", 1, 30), ("Logout", 80, 30)],
                            "lxqt")
    prova("il menu di LXQt pulito e' verde", not t and e)
    t, e, _ = giudica_righe([("Workspace 1", 1, 1)], "xfce")
    prova("senza «Log Out» ⇒ esci non letto", not e)
    t, e, _ = giudica_righe([("Log Out...", 1, 1)], "xfce", VIETATE_COL_GUASTO)
    prova("GUASTO A: con «Esci» nell'elenco il menu giusto e' rosso", bool(t))
    buoni = {k: "no" for k in LOGIND}
    prova("campi: tutti «no» ⇒ niente difetti", not giudica_campi(buoni, "xfce"))
    prova("GUASTO B: CanPowerOff=yes ⇒ difetto",
          bool(giudica_campi(dict(buoni, CanPowerOff="yes"), "kde")))
    prova("gnome: GDM presente senza disable-lock-screen ⇒ difetto",
          bool(giudica_campi(dict(buoni, gdm_sul_bus=True,
                                  **{"disable-lock-screen": "false"}), "gnome")))
    prova("gnome: niente GDM ⇒ niente icona", not giudica_campi(
        dict(buoni, gdm_sul_bus=False, **{"disable-lock-screen": "false"}), "gnome"))
    print("⛔ %d guai" % len(guai) if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  I CAMPI, dentro la scatola
# ═══════════════════════════════════════════════════════════════════════════
def leggi_logind(s, come_root=False):
    """{CanX: "no"|...} chiesto come l'inquilino (o come root, per il guasto)."""
    chi = "" if come_root else "runuser -u %s -- " % s.chi
    riga = "; ".join(
        "printf '%s=' ; %sbusctl call org.freedesktop.login1 /org/freedesktop/login1 "
        "org.freedesktop.login1.Manager %s 2>&1 | tail -1" % (k, chi, k) for k in LOGIND)
    _c, t = s.sc.dentro(riga, 60)
    campi = {}
    for r in t.splitlines():
        m = re.match(r'(Can\w+)=(?:s "(\w+)"|(Call failed: Access denied))', r.strip())
        if m:
            campi[m.group(1)] = m.group(2) or "negato"
    return campi, t


def leggi_blocco_gnome(s):
    c, t = s.sc.dentro("busctl --system list 2>/dev/null | grep -c '^org.gnome.DisplayManager '",
                       30)
    gdm = None
    try:
        gdm = int(t.strip().split()[-1]) > 0
    except (ValueError, IndexError):
        pass
    _c, t2 = G1B.nella_sessione(s, "gsettings get org.gnome.desktop.lockdown "
                                   "disable-lock-screen")
    return gdm, (t2.strip().splitlines() or [""])[-1], t + "\n" + t2


# ═══════════════════════════════════════════════════════════════════════════
#  I GESTI, per desktop (coordinate del desktop: W, H = misura della tela)
# ═══════════════════════════════════════════════════════════════════════════
def primo_clic(desktop, W, H):
    return {"gnome": (W - 30, 14), "kde": (28, H - 27),
            "xfce": (W - 64, 10), "lxqt": (12, H - 18)}[desktop]


def secondo_clic(desktop, W, H, parole):
    """Il secondo livello: (X, Y, come) o None se il menu e' di un livello.
    `parole` = [(testo, x, y, w, h, fiducia)] del primo livello."""
    if desktop == "gnome":
        return W - 45, 75, "l'icona d'accensione del menu di sistema (posizione fissa)"
    if desktop == "xfce":
        return None
    for testo, x, y, w, h, _f in sorted(parole, key=lambda p: -p[5]):
        if re.fullmatch(r"\W*(leave|esci)\W*", testo, re.I):
            return x + w / 2, y + h / 2, "«%s» letto dall'OCR" % testo
    return ({"kde": (600, H - 80), "lxqt": (52, H - 43)}[desktop] +
            ("«Leave» non letto: posizione di ripiego",))


def corpo(o, E):
    d = o.scatola
    with S.Sessione(o, "029", E) as s:
        G1B.passo("inquilino e browser pronti")
        ok, m = s.entra()
        G1B.passo("dentro: %s" % m[:80])
        if not ok:
            raise S.Bloccata(m)
        if not G1B.ocr_disponibile():
            raise S.Bloccata("tesseract non c'e' (%s): senza OCR il menu non si legge"
                             % G1B.TESSERACT)
        time.sleep(6 if d != "kde" else 10)      # il pannello finisce di nascere
        geo = s.geometria()
        W, H = geo["tl"], geo["ta"]
        ev = []
        png0, p0 = G1B.foto(s, "prima-del-menu")
        if not png0:
            raise S.Bloccata("nessuna foto prima del menu: " + p0)
        ev.append(p0)

        X, Y = primo_clic(d, W, H)
        G1B.clic_desktop(s, geo, X, Y)
        png1, p1, r1 = G1B.aspetta_apertura(s, png0, "menu-livello-1", (X, Y, 1300))
        if not png1:
            raise S.Bloccata("nessuna foto del menu: " + p1)
        ev.append(p1)
        if not r1:
            raise S.Bloccata("il clic in (%d, %d) non ha aperto niente: la foto non "
                             "cambia" % (X, Y))
        G1B.azzera_parole()
        righe, _testo1 = G1B.leggi_riquadro(png1, r1)
        print("   livello 1 %s: %s" % (r1, [f for f, _x, _y in righe]), flush=True)

        tutte = list(righe)
        sec = secondo_clic(d, W, H, G1B.parole_lette())
        r2 = None
        if sec:
            X2, Y2, come = sec
            print("   secondo clic in (%d, %d): %s" % (X2, Y2, come), flush=True)
            G1B.clic_desktop(s, geo, X2, Y2)
            png2, p2, r2 = G1B.aspetta_apertura(s, png1, "menu-livello-2", (X2, Y2, 1300),
                                                lato_min=40)
            if png2:
                ev.append(p2)
                if r2:
                    righe2, _t2 = G1B.leggi_riquadro(png2, r2)
                    print("   livello 2 %s: %s" % (r2, [f for f, _x, _y in righe2]),
                          flush=True)
                    tutte += righe2
        # il menu si chiude (due ESC), per lasciare il desktop come l'ha trovato
        for _ in range(2):
            G1B.combinazione(s.g, ["Escape"])
            time.sleep(0.4)

        trovate, esci, scartate = giudica_righe(tutte, d)
        campi, grezzo = leggi_logind(s)
        testo_campi = "logind come %s: %s" % (s.chi, ", ".join(
            "%s=%s" % (k, campi.get(k, "?")) for k in LOGIND))
        if d == "gnome":
            gdm, dis, g_grezzo = leggi_blocco_gnome(s)
            campi["gdm_sul_bus"], campi["disable-lock-screen"] = gdm, dis
            testo_campi += " · GDM sul bus di sistema=%s · disable-lock-screen=%s" % (gdm, dis)
            grezzo += "\n" + g_grezzo
        guai_campi = giudica_campi(campi, d)
        ev.append(s.salva_testo("f029-letto.txt",
                                ["righe lette dall'OCR:"] + ["  %s  (x=%d y=%d)" % r
                                                             for r in tutte]
                                + ["scartate (titolo GNOME): %s" % scartate,
                                   "campi: " + testo_campi, "", grezzo]))
        letto = " | ".join(f for f, _x, _y in tutte)
        oss = "OCR: «%s» · %s" % (letto[:300], testo_campi)
        atteso = ("nel menu d'uscita solo «Esci» (Log Out): niente blocco, sospensione, "
                  "ibernazione, riavvio, spegnimento, cambia utente; logind «no» per "
                  "l'inquilino")
        if trovate:
            E.metti("F-029", S.FAIL, "voci vietate nel menu: %s" % "; ".join(
                "%s («%s»)" % t for t in trovate), atteso=atteso, osservato=oss, evidenze=ev)
        elif not esci:
            E.metti("F-029", S.FAIL, "il menu si e' aperto ma «Esci/Log Out» NON si legge",
                    atteso=atteso, osservato=oss, evidenze=ev)
        elif guai_campi:
            E.metti("F-029", S.FAIL, "il menu e' pulito ma i campi no: %s"
                    % "; ".join(guai_campi), atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-029", S.PASS, "nel menu solo «Esci» (OCR), e logind dice no",
                    atteso=atteso, osservato=oss, evidenze=ev)

        if o.guasto:
            ta, _e, _s = giudica_righe(tutte, d, VIETATE_COL_GUASTO)
            visto_a = bool(ta)
            root, _g = leggi_logind(s, come_root=True)
            if d == "gnome":
                root["gdm_sul_bus"] = campi.get("gdm_sul_bus")
                root["disable-lock-screen"] = campi.get("disable-lock-screen")
            gb = giudica_campi(root, d)
            visto_b = bool(gb)
            E.guasto("F-029", visto_a and visto_b,
                     "A) «Esci» fra le vietate ⇒ %s · B) logind chiesto da root (%s) ⇒ %s"
                     % ("ROSSO" if visto_a else "verde (NON visto)",
                        ", ".join("%s=%s" % (k, root.get(k, "?")) for k in LOGIND),
                        "ROSSO" if visto_b else "verde (NON visto)"),
                     evidenze=ev)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
