#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f031b — F-031B LE IMPOSTAZIONI DELL'UTENTE NON SI TOCCANO (D-015, D-017,
           D-018), tranne blocco, riavvio, sospensione e stand-by

    python3 15-f031b-impostazioni-intatte.py --scatola xfce [--guasto]

⭐ LA REGOLA — decisione dell'utente del 25 set 2026, testuale: «Le
   impostazioni dell'utente non si toccano TRANNE quelle che riguardano
   blocco-schermo, riavvio sistema, sospensione e stand-by: queste sono
   impostazioni pericolose per altri utenti presenti sulla macchina».

⭐ COME: un inquilino nuovo; PRIMA dell'accesso si leggono DAL DISCO, come
   l'utente, i suoi file di impostazione — il dconf (con un profilo che ha
   SOLO `user-db:user`, cioe' `~/.config/dconf/user`), i canali xfconf
   (`~/.config/xfce4/xfconf/xfce-perchannel-xml/`), `~/.config/lxqt/*.conf`,
   le voci `lxqt-*.desktop` di `~/.local/share/applications`, `~/.config/kxkbrc`
   e `~/.cache/sessions` (dove il banco lascia una SENTINELLA: un file che
   REMOTIX non deve portare via).  Poi si entra dal browser, si aspetta che la
   sessione sia in piedi, si esce con «Esci» (il gesto di F-021), e si rilegge.

⭐ IL GIUDIZIO, chiave per chiave, in tre classi:
   · PERMESSE (`PERMESSE`) — blocco, riavvio, sospensione, stand-by: possono
     cambiare, e si dice come;
   · SORVEGLIATE (`SORVEGLIATE`) — tutto quel che REMOTIX ha mai scritto e
     che NON e' di quelle quattro specie (l'inventario del codice, 25 set
     2026: la disposizione, Ctrl+Alt+F*, «Esci…», «Cambia utente» (GNOME e dialogo di XFCE), la cintura
     del logout di XFCE, la sessione salvata,
     il pannello e le voci del menu di LXQt, kxkbrc): devono restare quelle
     di PRIMA, o FAIL;
   · ALTRE — il resto di quei file: le scrive anche il DESKTOP da se' al
     primo accesso (xfce4-panel copia la sua configurazione, LXQt crea i suoi
     file sparsi), e non sono distinguibili da qui.  ⚠ Si ELENCANO nelle
     evidenze e nella riga, ma non decidono: e' il limite dichiarato di
     questa prova.  Una chiave nuova che REMOTIX cominciasse a scrivere va
     aggiunta a `SORVEGLIATE` (o a `PERMESSE`).
   PASS = nessuna sorvegliata cambiata.  BLOCKED = non letto, o «Esci» non
   ha chiuso la sessione.

GUASTO (--guasto, dopo la passata sana, sessione chiusa): una SCRITTURA
   PERSISTENTE simulata di una chiave sorvegliata — la sentinella di
   `~/.cache/sessions` portata via (il vecchio `rm -rf`), e una chiave del
   desktop: GNOME `always-show-log-out` nel dconf dell'utente, XFCE
   `ShowSwitchUser` nel canale dell'utente, LXQt una voce `lxqt-leave.desktop`
   nascosta nella cartella dell'utente, KDE un gruppo in kxkbrc ⇒ lo stesso
   giudice deve dare rosso.
"""
import base64
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

F21 = S._carica("f021", os.path.join(S.QUI, "15-f021-esci.py"))

FUNZIONI = ("F-031B",)
PER_BROWSER = False

SENTINELLA = "xfce4-session-c15-sentinella:0"
ATTESA_IN_PIEDI_S = 20.0

# ── che cosa si legge ────────────────────────────────────────────────────────
DCONF = (
    # sorvegliate
    ["org.gnome.mutter.wayland switch-to-session-%d" % i for i in range(1, 13)]
    + ["org.gnome.shell always-show-log-out", "org.gnome.desktop.lockdown disable-user-switching"]
    + ["org.gnome.desktop.input-sources %s" % k
       for k in ("sources", "current", "mru-sources", "xkb-options")]
    # permesse
    + ["org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type",
       "org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type",
       "org.gnome.desktop.session idle-delay", "org.gnome.desktop.screensaver lock-enabled"])
FILE = (
    ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml",
    ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml",
    ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
    ".config/lxqt/panel.conf", ".config/lxqt/lxqt.conf", ".config/lxqt/session.conf",
    ".config/lxqt/lxqt-powermanagement.conf", ".config/kxkbrc")
VOCI_LXQT = ("lxqt-leave", "lxqt-lockscreen", "lxqt-suspend", "lxqt-hibernate",
             "lxqt-shutdown", "lxqt-reboot")

# ── le classi ────────────────────────────────────────────────────────────────
PERMESSE = [re.compile(x) for x in (
    r"^dconf:org\.gnome\.settings-daemon\.plugins\.power sleep-inactive-(ac|battery)-type$",
    r"^dconf:org\.gnome\.desktop\.session idle-delay$",
    r"^dconf:org\.gnome\.desktop\.screensaver lock-enabled$",
    r"^xfconf:xfce4-power-manager:/xfce4-power-manager/"
    r"(dpms-enabled|inactivity-on-ac|inactivity-on-battery)$",
    r"^xfconf:xfce4-session:/general/LockCommand$",
    # Sospendi, Iberna, Sonno ibrido nel dialogo di «Esci»: sospensione
    r"^xfconf:xfce4-session:/shutdown/Show(Suspend|Hibernate|HybridSleep)$",
    # i pulsanti d'azione del pannello: blocco, sospensione, riavvio, spegnimento
    r"^xfconf:xfce4-panel:/plugins/plugin-\d+/items$",
    r"^lxqt:lxqt-powermanagement\.conf:\[General\](enableIdlenessWatcher|runCheckLevel)$",
    r"^lxqt:lxqt\.conf:\[Screensaver\]lock_command_wayland$",
    r"^lxqt:session\.conf:\[General\]lock_command_wayland$",
)]
SORVEGLIATE = [re.compile(x) for x in (
    r"^dconf:",                                      # quelle lette e non permesse
    r"^xfconf:xfce4-session:/general/(WaylandLogoutCommand|SessionName|SaveOnExit)$",
    r"^xfconf:xfce4-session:/shutdown/ShowSwitchUser$",
    r"^lxqt:panel\.conf:\[[^\]]*\]type$",
    r"^app:",
    r"^kxkbrc:",
    r"^cache:",
)]


def classe(chiave):
    if any(p.search(chiave) for p in PERMESSE):
        return "permessa"
    if any(p.search(chiave) for p in SORVEGLIATE):
        return "sorvegliata"
    return "altra"


# ═══════════════════════════════════════════════════════════════════════════
#  LA LETTURA: una riga di shell come l'utente, il resto qui
# ═══════════════════════════════════════════════════════════════════════════
def riga_lettura(chi):
    casa = "/home/%s" % chi
    r = ["export HOME=%s; p=$(mktemp); echo user-db:user > \"$p\"" % casa,
         "if command -v gsettings >/dev/null 2>&1; then for sk in %s; do "
         "s=${sk%%%%@*}; k=${sk#*@}; v=$(DCONF_PROFILE=\"$p\" gsettings get \"$s\" \"$k\" "
         "2>/dev/null) || continue; echo \"@@dconf $s $k=$v\"; done; fi; rm -f \"$p\""
         % " ".join(x.replace(" ", "@") for x in DCONF)]
    for f in FILE:
        r.append("f=\"$HOME/%s\"; if [ -f \"$f\" ]; then echo \"@@file %s $(base64 -w0 < \"$f\")\";"
                 " fi" % (f, f))
    for v in VOCI_LXQT:
        r.append("f=\"$HOME/.local/share/applications/%s.desktop\"; if [ -f \"$f\" ]; then "
                 "echo \"@@app %s $(base64 -w0 < \"$f\")\"; fi" % (v, v))
    r.append("ls -1 \"$HOME/.cache/sessions\" 2>/dev/null | sed 's/^/@@cache /'")
    r.append("echo @@fine")
    return "; ".join(r)


def ini(testo):
    """{"[gruppo]chiave": valore} da un file QSettings/KConfig (le chiavi di
    primo livello vanno in [General], come le legge QSettings)."""
    d, g = {}, "General"
    for riga in testo.splitlines():
        riga = riga.strip()
        if not riga or riga[0] in "#;":
            continue
        m = re.match(r"^\[(.*)\]$", riga)
        if m:
            g = m.group(1)
            continue
        if "=" in riga:
            k, v = riga.split("=", 1)
            d["[%s]%s" % (g, k.strip())] = v.strip()
    return d


def xfconf(testo):
    """{"/percorso": valore} da un canale xfconf."""
    d = {}

    def giu(el, base):
        for p in el.findall("property"):
            via = base + "/" + p.get("name", "?")
            if p.get("type") == "array":
                d[via] = ",".join(v.get("value", "") for v in p.findall("value"))
            elif p.get("type") != "empty":
                d[via] = p.get("value", "")
            giu(p, via)
    giu(ET.fromstring(testo), "")
    return d


def interpreta(uscita):
    """{chiave: valore} da quel che ha stampato `riga_lettura`; None se la
    lettura non e' arrivata in fondo."""
    if "@@fine" not in (uscita or ""):
        return None
    d = {}
    for riga in uscita.splitlines():
        if riga.startswith("@@dconf "):
            k, _, v = riga[8:].partition("=")
            d["dconf:" + k.strip()] = v.strip()
        elif riga.startswith("@@file ") or riga.startswith("@@app "):
            tipo, nome, b64 = (riga.split(" ", 2) + [""])[:3]
            testo = base64.b64decode(b64).decode("utf-8", "replace") if b64 else ""
            if tipo == "@@app":
                h = ini(testo).get("[Desktop Entry]Hidden", "(senza Hidden)")
                d["app:%s:Hidden" % nome] = h
            elif "/xfconf/" in nome:
                canale = os.path.basename(nome)[:-4]
                try:
                    for k, v in xfconf(testo).items():
                        d["xfconf:%s:%s" % (canale, k)] = v
                except ET.ParseError as e:
                    d["xfconf:%s:(illeggibile)" % canale] = str(e)
            elif nome.endswith("kxkbrc"):
                for k, v in ini(testo).items():
                    d["kxkbrc:" + k] = v
            else:
                for k, v in ini(testo).items():
                    d["lxqt:%s:%s" % (os.path.basename(nome), k)] = v
        elif riga.startswith("@@cache "):
            d["cache:" + riga[8:].strip()] = "c'e'"
    return d


def leggi(s):
    for _ in range(3):
        c, t = s.come_utente("sh -c %s" % S._q(riga_lettura(s.chi)), 90)
        d = interpreta(t) if c == 0 else None
        if d is not None:
            return d, t
        time.sleep(2)
    return None, t


def giudica(prima, dopo):
    """(esito, frase, dettaglio)."""
    if prima is None or dopo is None:
        return S.BLOCKED, "le impostazioni dell'utente non si sono potute leggere (%s)" % (
            "prima" if prima is None else "dopo"), {}
    if not any(k.startswith("cache:" + SENTINELLA) for k in prima):
        return S.BLOCKED, "la sentinella di ~/.cache/sessions non c'era prima", {}
    per = {"permessa": [], "sorvegliata": [], "altra": []}
    for k in sorted(set(prima) | set(dopo)):
        a, b = prima.get(k, "(assente)"), dopo.get(k, "(assente)")
        if a != b:
            c = classe(k)
            m = re.match(r"^lxqt:panel\.conf:\[([^\]]*)\]type$", k)
            if c == "sorvegliata" and m and a == "(assente)" and b == m.group(1):
                # ⚠ [M] 25 set 2026: lxqt-panel all'avvio RISCRIVE nel file
                #   dell'utente tutta la configurazione che vede, coi tipi di
                #   serie (il gruppo si chiama come il suo tipo): e' il
                #   desktop, non noi.  Un tipo DIVERSO (mainmenu) resta rosso.
                c = "altra"
            per[c].append("%s: %s → %s" % (k, a[:80], b[:80]))
    coda = " · permesse cambiate: %s · altre cambiate (del desktop o nostre, non decidono): %d" % (
        "; ".join(per["permessa"]) or "nessuna", len(per["altra"]))
    if per["sorvegliata"]:
        return (S.FAIL, "⛔ IMPOSTAZIONI DELL'UTENTE TOCCATE: %s" % "; ".join(per["sorvegliata"])
                + coda, per)
    return S.PASS, "nessuna sorvegliata cambiata (%d lette)%s" % (
        sum(1 for k in prima if classe(k) == "sorvegliata"), coda), per


# ═══════════════════════════════════════════════════════════════════════════
#  IL GUASTO
# ═══════════════════════════════════════════════════════════════════════════
def riga_guasto(chi, desktop):
    casa = "/home/%s" % chi
    r = ["export HOME=%s" % casa,
         # il vecchio `rm -rf ~/.cache/sessions`
         "rm -f \"$HOME/.cache/sessions/%s\"" % SENTINELLA]
    if desktop == "gnome":
        r.append("p=$(mktemp); echo user-db:user > \"$p\"; "
                 "DCONF_PROFILE=\"$p\" gsettings set org.gnome.shell always-show-log-out true "
                 "2>&1 | head -2; rm -f \"$p\"")
    elif desktop == "xfce":
        r.append("d=\"$HOME/.config/xfce4/xfconf/xfce-perchannel-xml\"; mkdir -p \"$d\"; "
                 "f=\"$d/xfce4-session.xml\"; [ -f \"$f\" ] || printf '<?xml version=\"1.0\" "
                 "encoding=\"UTF-8\"?>\\n<channel name=\"xfce4-session\" version=\"1.0\">\\n"
                 "</channel>\\n' > \"$f\"; sed -i 's|</channel>|  <property name=\"shutdown\" "
                 "type=\"empty\"><property name=\"ShowSwitchUser\" type=\"bool\" "
                 "value=\"false\"/></property>\\n</channel>|' \"$f\"")
    elif desktop == "lxqt":
        r.append("d=\"$HOME/.local/share/applications\"; mkdir -p \"$d\"; printf "
                 "'[Desktop Entry]\\nType=Application\\nName=lxqt-leave\\nHidden=true\\n' > "
                 "\"$d/lxqt-leave.desktop\"")
    elif desktop == "kde":
        r.append("mkdir -p \"$HOME/.config\"; printf '\\n[Remotix15Guasto]\\nscritta=1\\n' >> "
                 "\"$HOME/.config/kxkbrc\"")
    r.append("echo scritto")
    return "; ".join(r)


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)

    b = lambda t: base64.b64encode(t.encode()).decode()             # noqa: E731
    xml = ('<?xml version="1.0"?><channel name="xfce4-session" version="1.0">'
           '<property name="general" type="empty">'
           '<property name="LockCommand" type="string" value="/bin/false"/></property>'
           '</channel>')
    uscita = "\n".join([
        "@@dconf org.gnome.shell always-show-log-out=false",
        "@@dconf org.gnome.desktop.session idle-delay=uint32 300",
        "@@file .config/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml " + b(xml),
        "@@file .config/lxqt/panel.conf " + b("panels=panel1\n[fancymenu]\ntype=fancymenu\n"),
        "@@cache " + SENTINELLA, "@@fine"])
    p = interpreta(uscita)
    prova("lettura", p and p.get("xfconf:xfce4-session:/general/LockCommand") == "/bin/false"
          and p.get("lxqt:panel.conf:[fancymenu]type") == "fancymenu"
          and p.get("lxqt:panel.conf:[General]panels") == "panel1"
          and ("cache:" + SENTINELLA) in p, repr(p))
    prova("lettura monca ⇒ None", interpreta("@@dconf a b=c") is None)
    prova("uguali ⇒ PASS", giudica(p, dict(p))[0] == S.PASS)
    prova("idle-delay 0 (permessa) ⇒ PASS",
          giudica(p, dict(p, **{"dconf:org.gnome.desktop.session idle-delay": "uint32 0"}))[0]
          == S.PASS)
    prova("LockCommand (permessa) ⇒ PASS",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/general/LockCommand": "/bin/true"}))[0]
          == S.PASS)
    prova("ShowSuspend (permessa) ⇒ PASS",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/shutdown/ShowSuspend": "false"}))[0]
          == S.PASS)
    prova("pulsanti del pannello (permessa) ⇒ PASS",
          giudica(p, dict(p, **{"xfconf:xfce4-panel:/plugins/plugin-14/items": "-lock"}))[0]
          == S.PASS)
    prova("always-show-log-out nell'utente ⇒ FAIL",
          giudica(p, dict(p, **{"dconf:org.gnome.shell always-show-log-out": "true"}))[0]
          == S.FAIL)
    prova("ShowSwitchUser nell'utente ⇒ FAIL",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/shutdown/ShowSwitchUser": "false"}))[0]
          == S.FAIL)
    prova("WaylandLogoutCommand nell'utente ⇒ FAIL",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/general/WaylandLogoutCommand":
                                "/bin/true"}))[0] == S.FAIL)
    prova("fancymenu→mainmenu nell'utente ⇒ FAIL",
          giudica(p, dict(p, **{"lxqt:panel.conf:[fancymenu]type": "mainmenu"}))[0] == S.FAIL)
    prova("il pannello riscritto dal desktop coi tipi di serie ⇒ PASS",
          giudica(p, dict(p, **{"lxqt:panel.conf:[taskbar]type": "taskbar"}))[0] == S.PASS)
    prova("fancymenu→mainmenu scritto da zero nell'utente ⇒ FAIL",
          giudica({k: v for k, v in p.items() if "fancymenu" not in k},
                  dict(p, **{"lxqt:panel.conf:[fancymenu]type": "mainmenu"}))[0] == S.FAIL)
    prova("voce Hidden nell'utente ⇒ FAIL",
          giudica(p, dict(p, **{"app:lxqt-leave:Hidden": "true"}))[0] == S.FAIL)
    prova("kxkbrc toccato ⇒ FAIL",
          giudica(p, dict(p, **{"kxkbrc:[Layout]LayoutList": "it"}))[0] == S.FAIL)
    senza = dict(p)
    senza.pop("cache:" + SENTINELLA)
    prova("sentinella portata via ⇒ FAIL", giudica(p, senza)[0] == S.FAIL)
    prova("un file del desktop in piu' (altra) ⇒ PASS",
          giudica(p, dict(p, **{"lxqt:lxqt.conf:[General]__userfile__": "true"}))[0] == S.PASS)
    prova("non letto ⇒ BLOCKED", giudica(None, p)[0] == S.BLOCKED)
    prova("riga di lettura: shell valida",
          os.system("sh -n -c %s" % S._q(riga_lettura("x"))) == 0)
    for d in S.DESKTOP:
        prova("riga del guasto %s: shell valida" % d,
              os.system("sh -n -c %s" % S._q(riga_guasto("x", d))) == 0)
    print("⛔ CERTIFICAZIONE FALLITA" if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    with S.Sessione(o, "031", E) as s:
        desktop, gesto = s.sc.gesto_esci()
        if not gesto:
            raise S.Bloccata("non so come si dice «Esci» in %s" % s.sc.contenitore)
        c, t = s.come_utente("sh -c %s" % S._q(
            "mkdir -p /home/%s/.cache/sessions && echo sentinella del banco 15-f031b > "
            "'/home/%s/.cache/sessions/%s'" % (s.chi, s.chi, SENTINELLA)), 30)
        prima, tp = leggi(s)
        ev = [x for x in (s.salva_testo("impostazioni-prima.txt", tp or ""),) if x]
        print("   prima: %s chiavi" % (None if prima is None else len(prima)), flush=True)
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        time.sleep(ATTESA_IN_PIEDI_S)        # la sessione nasce, il pannello pure
        d, ev2 = F21.esci_e_guarda(s, gesto, nome="esci")
        ev += [x for x in ev2 if x]
        if not d.get("finita"):
            raise S.Bloccata("«Esci» (%s) non ha chiuso la sessione: il «dopo» non sarebbe "
                             "il dopo" % gesto)
        dopo, td = leggi(s)
        e, frase, per = giudica(prima, dopo)
        p = s.salva_testo("impostazioni-dopo.txt", td or "")
        q = s.salva_testo("impostazioni-giudizio.txt", "\n".join(
            "%s:\n  %s" % (k, "\n  ".join(v) or "-") for k, v in per.items()))
        ev += [x for x in (p, q) if x]
        E.metti("F-031B", e, frase,
                atteso="dopo «Esci» le impostazioni dell'utente sono quelle di prima, "
                       "salvo blocco, riavvio, sospensione e stand-by",
                osservato=frase, evidenze=ev)
        if not o.guasto:
            return
        _c, tg = s.come_utente("sh -c %s" % S._q(riga_guasto(s.chi, o.scatola)), 60)
        dopo_g, tdg = leggi(s)
        eg, fg, _per = giudica(prima, dopo_g)
        print("   GUASTO (%s): %s" % ((tg or "").strip().replace("\n", " | ")[-120:], fg[:300]),
              flush=True)
        E.guasto("F-031B", None if eg == S.BLOCKED else eg == S.FAIL,
                 "scrittura persistente simulata (sentinella via + una chiave di %s): %s"
                 % (o.scatola, fg),
                 atteso="rosso: una sorvegliata cambiata", osservato=fg,
                 evidenze=[x for x in (s.salva_testo("impostazioni-guasto.txt", tdg or ""),)
                           if x])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
