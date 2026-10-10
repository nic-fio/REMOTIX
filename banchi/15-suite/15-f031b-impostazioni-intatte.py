#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f031b — F-031B THE USER'S SETTINGS ARE NOT TOUCHED (D-015, D-017,
           D-018), except lock, restart, suspend and stand-by

    python3 15-f031b-impostazioni-intatte.py --scatola xfce [--guasto]

⭐ THE RULE — the user's decision of 25 Sep 2026, verbatim: «The
   user's settings are not touched EXCEPT those concerning
   screen lock, system restart, suspend and stand-by: these are
   settings dangerous for other users present on the machine».

⭐ HOW: a new tenant; BEFORE the login their settings files are read FROM DISK, like
   the user — the dconf (with a profile that has
   ONLY `user-db:user`, that is `~/.config/dconf/user`), the xfconf channels
   (`~/.config/xfce4/xfconf/xfce-perchannel-xml/`), `~/.config/lxqt/*.conf`,
   the `lxqt-*.desktop` entries of `~/.local/share/applications`, `~/.config/kxkbrc`
   and `~/.cache/sessions` (where the bench leaves a SENTINEL: a file that
   REMOTIX must not take away).  Then we log in from the browser, wait for the
   session to be up, exit with «Exit» (F-021's gesture), and read again.
   ⭐ And the USER MANAGER (R1/R2, clean-up review): with linger
   on it survives the session, and the user who logs in at the monitor
   inherits its environment and drop-ins.  After «Exit» nothing of
   REMOTIX must remain there: no variable with our mark (`systemctl --user
   show-environment`: `DCONF_PROFILE`, values with «remotix»), no drop-in
   with our name (`$XDG_RUNTIME_DIR/systemd/user.control`,
   `~/.config/systemd/user`), and `xfconf-query` on the user's real bus must not
   see XFCE's session keys (locked by us).

⭐ THE JUDGMENT, key by key, in three classes:
   · ALLOWED (`PERMESSE`) — lock, restart, suspend, stand-by: they may
     change, and how is said;
   · WATCHED (`SORVEGLIATE`) — everything REMOTIX has ever written and
     that is NOT of those four kinds (the inventory of the code, 25 Sep
     2026: the layout, Ctrl+Alt+F*, «Log out…», «Switch user» (GNOME and XFCE's dialog), XFCE's logout
     belt, the saved session,
     LXQt's panel and menu entries, kxkbrc): they must stay the ones
     from BEFORE, or FAIL;
   · OTHERS — the rest of those files: the DESKTOP also writes them by itself at the
     first login (xfce4-panel copies its configuration, LXQt creates its
     scattered files), and they cannot be told apart from here.  ⚠ They are LISTED in the
     evidence and in the line, but they do not decide: it is the declared limit of
     this test.  A new key that REMOTIX started writing must be
     added to `SORVEGLIATE` (or to `PERMESSE`).
   PASS = no watched key changed.  BLOCKED = not read, or «Exit» did not
   close the session.

FAULT (--guasto, after the healthy pass, session closed): a simulated PERSISTENT
   WRITE of a watched key — the sentinel of
   `~/.cache/sessions` taken away (the old `rm -rf`), and a key of the
   desktop: GNOME `always-show-log-out` in the user's dconf, XFCE
   `ShowSwitchUser` in the user's channel, LXQt a hidden `lxqt-leave.desktop`
   entry in the user's folder, KDE a group in kxkbrc, and a drop-in
   `zz-remotix-finto.conf` forgotten in the user manager ⇒ the same
   judge must give red.
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

# ── what is read ─────────────────────────────────────────────────────────────
DCONF = (
    # watched
    ["org.gnome.mutter.wayland switch-to-session-%d" % i for i in range(1, 13)]
    + ["org.gnome.shell always-show-log-out", "org.gnome.desktop.lockdown disable-user-switching"]
    + ["org.gnome.desktop.input-sources %s" % k
       for k in ("sources", "current", "mru-sources", "xkb-options")]
    # allowed
    + ["org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type",
       "org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type",
       "org.gnome.desktop.session idle-delay", "org.gnome.desktop.screensaver lock-enabled"])
FILE = (
    ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-session.xml",
    ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml",
    ".config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
    ".config/lxqt/panel.conf", ".config/lxqt/lxqt.conf", ".config/lxqt/session.conf",
    ".config/lxqt/lxqt-powermanagement.conf", ".config/kxkbrc")
XFCONF_SESSIONE = ("/general/WaylandLogoutCommand", "/general/SessionName",
                   "/general/SaveOnExit", "/shutdown/ShowSwitchUser")
VOCI_LXQT = ("lxqt-leave", "lxqt-lockscreen", "lxqt-suspend", "lxqt-hibernate",
             "lxqt-shutdown", "lxqt-reboot")

# ── the classes ──────────────────────────────────────────────────────────────
PERMESSE = [re.compile(x) for x in (
    r"^dconf:org\.gnome\.settings-daemon\.plugins\.power sleep-inactive-(ac|battery)-type$",
    r"^dconf:org\.gnome\.desktop\.session idle-delay$",
    r"^dconf:org\.gnome\.desktop\.screensaver lock-enabled$",
    r"^xfconf:xfce4-power-manager:/xfce4-power-manager/"
    r"(dpms-enabled|inactivity-on-ac|inactivity-on-battery)$",
    r"^xfconf:xfce4-session:/general/LockCommand$",
    # Suspend, Hibernate, Hybrid sleep in the «Exit» dialog: suspend
    r"^xfconf:xfce4-session:/shutdown/Show(Suspend|Hibernate|HybridSleep)$",
    # the panel's action buttons: lock, suspend, restart, shut down
    r"^xfconf:xfce4-panel:/plugins/plugin-\d+/items$",
    r"^lxqt:lxqt-powermanagement\.conf:\[General\](enableIdlenessWatcher|runCheckLevel)$",
    r"^lxqt:lxqt\.conf:\[Screensaver\]lock_command_wayland$",
    r"^lxqt:session\.conf:\[General\]lock_command_wayland$",
)]
SORVEGLIATE = [re.compile(x) for x in (
    r"^dconf:",                                      # those read and not allowed
    r"^xfconf:xfce4-session:/general/(WaylandLogoutCommand|SessionName|SaveOnExit)$",
    r"^xfconf:xfce4-session:/shutdown/ShowSwitchUser$",
    r"^lxqt:panel\.conf:\[[^\]]*\]type$",
    r"^app:",
    r"^kxkbrc:",
    r"^cache:",
    r"^gestore:",                                    # R1/R2: nothing of ours remains
)]


def classe(chiave):
    if any(p.search(chiave) for p in PERMESSE):
        return "permessa"
    if any(p.search(chiave) for p in SORVEGLIATE):
        return "sorvegliata"
    return "altra"


# ═══════════════════════════════════════════════════════════════════════════
#  THE READING: a shell line as the user, the rest here
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
    # ⭐ R1/R2 — the USER MANAGER: the variables with our mark, the drop-ins
    #   with our name, and what xfconfd says today about XFCE's session keys,
    #   on the user's REAL bus (the one a login at the
    #   monitor would use)
    r.append("u=$(id -u); if [ -S /run/user/$u/bus ]; then "
             "systemctl --user show-environment 2>/dev/null | while IFS= read -r l; do "
             "case \"$l\" in DCONF_PROFILE=*|*remotix*) echo \"@@env $l\";; esac; done; "
             "if command -v xfconf-query >/dev/null 2>&1; then for k in %s; do "
             "v=$(xfconf-query -c xfce4-session -p $k 2>/dev/null) && echo \"@@xfq $k=$v\"; "
             "done; fi; fi" % " ".join(XFCONF_SESSIONE))
    r.append("for f in /run/user/$u/systemd/user.control/*/*remotix* "
             "\"$HOME\"/.config/systemd/user/*.d/*remotix*; do [ -e \"$f\" ] && "
             "echo \"@@drop $f\"; done")
    r.append("echo @@fine")
    return "; ".join(r)


def ini(testo):
    """{"[group]key": value} from a QSettings/KConfig file (the top-level
    keys go into [General], as QSettings reads them)."""
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
    """{"/path": value} from an xfconf channel."""
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
    """{key: value} from what `riga_lettura` printed; None if the
    reading did not get to the end."""
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
                h = ini(testo).get("[Desktop Entry]Hidden", "(no Hidden)")
                d["app:%s:Hidden" % nome] = h
            elif "/xfconf/" in nome:
                canale = os.path.basename(nome)[:-4]
                try:
                    for k, v in xfconf(testo).items():
                        d["xfconf:%s:%s" % (canale, k)] = v
                except ET.ParseError as e:
                    d["xfconf:%s:(unreadable)" % canale] = str(e)
            elif nome.endswith("kxkbrc"):
                for k, v in ini(testo).items():
                    d["kxkbrc:" + k] = v
            else:
                for k, v in ini(testo).items():
                    d["lxqt:%s:%s" % (os.path.basename(nome), k)] = v
        elif riga.startswith("@@cache "):
            d["cache:" + riga[8:].strip()] = "c'e'"
        elif riga.startswith("@@env "):
            k, _, v = riga[6:].partition("=")
            d["gestore:env:" + k.strip()] = v
        elif riga.startswith("@@xfq "):
            k, _, v = riga[6:].partition("=")
            d["gestore:xfconf:" + k.strip()] = v.strip()
        elif riga.startswith("@@drop "):
            d["gestore:dropin:" + riga[7:].strip()] = "c'e'"
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
    """(outcome, sentence, detail)."""
    if prima is None or dopo is None:
        return S.BLOCKED, "the user's settings could not be read (%s)" % (
            "prima" if prima is None else "dopo"), {}
    if not any(k.startswith("cache:" + SENTINELLA) for k in prima):
        return S.BLOCKED, "the sentinel of ~/.cache/sessions was not there before", {}
    per = {"permessa": [], "sorvegliata": [], "altra": []}
    for k in sorted(set(prima) | set(dopo)):
        a, b = prima.get(k, "(assente)"), dopo.get(k, "(assente)")
        if a != b:
            c = classe(k)
            m = re.match(r"^lxqt:panel\.conf:\[([^\]]*)\]type$", k)
            if c == "sorvegliata" and m and a == "(assente)" and b == m.group(1):
                # ⚠ [M] 25 Sep 2026: lxqt-panel at startup REWRITES in the user's
                #   file all the configuration it sees, with the standard
                #   types (the group is named like its type): it is the
                #   desktop, not us.  A DIFFERENT type (mainmenu) stays red.
                c = "altra"
            per[c].append("%s: %s → %s" % (k, a[:80], b[:80]))
    coda = " · allowed changed: %s · others changed (the desktop's or ours, they do not decide): %d" % (
        "; ".join(per["permessa"]) or "none", len(per["altra"]))
    if per["sorvegliata"]:
        return (S.FAIL, "⛔ USER'S SETTINGS TOUCHED: %s" % "; ".join(per["sorvegliata"])
                + coda, per)
    return S.PASS, "no watched key changed (%d read)%s" % (
        sum(1 for k in prima if classe(k) == "sorvegliata"), coda), per


# ═══════════════════════════════════════════════════════════════════════════
#  THE FAULT
# ═══════════════════════════════════════════════════════════════════════════
def riga_guasto(chi, desktop):
    casa = "/home/%s" % chi
    r = ["export HOME=%s" % casa,
         # the old `rm -rf ~/.cache/sessions`
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
    # R1/R2: a REMOTIX drop-in forgotten in the user manager
    r.append("d=\"$HOME/.config/systemd/user/xfconfd.service.d\"; mkdir -p \"$d\"; printf "
             "'[Service]\\n# 15-f031b guasto\\n' > \"$d/zz-remotix-finto.conf\"")
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
    prova("reading", p and p.get("xfconf:xfce4-session:/general/LockCommand") == "/bin/false"
          and p.get("lxqt:panel.conf:[fancymenu]type") == "fancymenu"
          and p.get("lxqt:panel.conf:[General]panels") == "panel1"
          and ("cache:" + SENTINELLA) in p, repr(p))
    prova("truncated reading ⇒ None", interpreta("@@dconf a b=c") is None)
    prova("equal ⇒ PASS", giudica(p, dict(p))[0] == S.PASS)
    prova("idle-delay 0 (allowed) ⇒ PASS",
          giudica(p, dict(p, **{"dconf:org.gnome.desktop.session idle-delay": "uint32 0"}))[0]
          == S.PASS)
    prova("LockCommand (allowed) ⇒ PASS",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/general/LockCommand": "/bin/true"}))[0]
          == S.PASS)
    prova("ShowSuspend (allowed) ⇒ PASS",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/shutdown/ShowSuspend": "false"}))[0]
          == S.PASS)
    prova("panel buttons (allowed) ⇒ PASS",
          giudica(p, dict(p, **{"xfconf:xfce4-panel:/plugins/plugin-14/items": "-lock"}))[0]
          == S.PASS)
    prova("always-show-log-out in the user ⇒ FAIL",
          giudica(p, dict(p, **{"dconf:org.gnome.shell always-show-log-out": "true"}))[0]
          == S.FAIL)
    prova("ShowSwitchUser in the user ⇒ FAIL",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/shutdown/ShowSwitchUser": "false"}))[0]
          == S.FAIL)
    prova("WaylandLogoutCommand in the user ⇒ FAIL",
          giudica(p, dict(p, **{"xfconf:xfce4-session:/general/WaylandLogoutCommand":
                                "/bin/true"}))[0] == S.FAIL)
    prova("fancymenu→mainmenu in the user ⇒ FAIL",
          giudica(p, dict(p, **{"lxqt:panel.conf:[fancymenu]type": "mainmenu"}))[0] == S.FAIL)
    prova("the panel rewritten by the desktop with the standard types ⇒ PASS",
          giudica(p, dict(p, **{"lxqt:panel.conf:[taskbar]type": "taskbar"}))[0] == S.PASS)
    prova("fancymenu→mainmenu written from scratch in the user ⇒ FAIL",
          giudica({k: v for k, v in p.items() if "fancymenu" not in k},
                  dict(p, **{"lxqt:panel.conf:[fancymenu]type": "mainmenu"}))[0] == S.FAIL)
    prova("Hidden entry in the user ⇒ FAIL",
          giudica(p, dict(p, **{"app:lxqt-leave:Hidden": "true"}))[0] == S.FAIL)
    prova("kxkbrc touched ⇒ FAIL",
          giudica(p, dict(p, **{"kxkbrc:[Layout]LayoutList": "it"}))[0] == S.FAIL)
    senza = dict(p)
    senza.pop("cache:" + SENTINELLA)
    prova("sentinel taken away ⇒ FAIL", giudica(p, senza)[0] == S.FAIL)
    prova("one more desktop file (other) ⇒ PASS",
          giudica(p, dict(p, **{"lxqt:lxqt.conf:[General]__userfile__": "true"}))[0] == S.PASS)
    g = interpreta("@@env DCONF_PROFILE=/run/user/5/remotix/dconf/profilo\n"
                   "@@xfq /general/SessionName=REMOTIX\n"
                   "@@drop /run/user/5/systemd/user.control/xfconfd.service.d/"
                   "zz-remotix-sessione.conf\n@@fine")
    prova("reading the manager", g == {
        "gestore:env:DCONF_PROFILE": "/run/user/5/remotix/dconf/profilo",
        "gestore:xfconf:/general/SessionName": "REMOTIX",
        "gestore:dropin:/run/user/5/systemd/user.control/xfconfd.service.d/"
        "zz-remotix-sessione.conf": "c'e'"}, repr(g))
    for k, v in g.items():
        prova("manager: %s left ⇒ FAIL" % k.split(":")[1],
              giudica(p, dict(p, **{k: v}))[0] == S.FAIL)
    prova("not read ⇒ BLOCKED", giudica(None, p)[0] == S.BLOCKED)
    prova("reading line: valid shell",
          os.system("sh -n -c %s" % S._q(riga_lettura("x"))) == 0)
    for d in S.DESKTOP:
        prova("fault line %s: valid shell" % d,
              os.system("sh -n -c %s" % S._q(riga_guasto("x", d))) == 0)
    print("⛔ CERTIFICATION FAILED" if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    with S.Sessione(o, "031", E) as s:
        desktop, gesto = s.sc.gesto_esci()
        if not gesto:
            raise S.Bloccata("I do not know how to say «Exit» in %s" % s.sc.contenitore)
        c, t = s.come_utente("sh -c %s" % S._q(
            "mkdir -p /home/%s/.cache/sessions && echo bench sentinel 15-f031b > "
            "'/home/%s/.cache/sessions/%s'" % (s.chi, s.chi, SENTINELLA)), 30)
        prima, tp = leggi(s)
        ev = [x for x in (s.salva_testo("impostazioni-prima.txt", tp or ""),) if x]
        print("   before: %s keys" % (None if prima is None else len(prima)), flush=True)
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        time.sleep(ATTESA_IN_PIEDI_S)        # the session is born, the panel too
        d, ev2 = F21.esci_e_guarda(s, gesto, nome="esci")
        ev += [x for x in ev2 if x]
        if not d.get("finita"):
            raise S.Bloccata("«Exit» (%s) did not close the session: the «after» would not be "
                             "the after" % gesto)
        dopo, td = leggi(s)
        e, frase, per = giudica(prima, dopo)
        p = s.salva_testo("impostazioni-dopo.txt", td or "")
        q = s.salva_testo("impostazioni-giudizio.txt", "\n".join(
            "%s:\n  %s" % (k, "\n  ".join(v) or "-") for k, v in per.items()))
        ev += [x for x in (p, q) if x]
        E.metti("F-031B", e, frase,
                atteso="after «Exit» the user's settings are the ones from before, "
                       "except lock, restart, suspend and stand-by",
                osservato=frase, evidenze=ev)
        if not o.guasto:
            return
        _c, tg = s.come_utente("sh -c %s" % S._q(riga_guasto(s.chi, o.scatola)), 60)
        dopo_g, tdg = leggi(s)
        eg, fg, _per = giudica(prima, dopo_g)
        print("   FAULT (%s): %s" % ((tg or "").strip().replace("\n", " | ")[-120:], fg[:300]),
              flush=True)
        E.guasto("F-031B", None if eg == S.BLOCKED else eg == S.FAIL,
                 "simulated persistent write (sentinel gone + a key of %s): %s"
                 % (o.scatola, fg),
                 atteso="red: a watched key changed", osservato=fg,
                 evidenze=[x for x in (s.salva_testo("impostazioni-guasto.txt", tdg or ""),)
                           if x])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
