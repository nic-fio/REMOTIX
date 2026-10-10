#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f012b — F-012B AUDIO AFTER «EXIT»: you exit, you come back in at once, and a PulseAudio
           program is still heard in the browser

    python3 15-f012b-audio-dopo-esci.py --scatola gnome --browser firefox [--guasto]

THE DEFECT IT LOOKS AT (the user's report, 2 Oct 2026, GNOME on the Radeon,
Firefox).  After «Exit» and a new login — the systemd USER MANAGER is
still alive (it stays as long as the logind session of the `remotix` child exists) — the
previous session stops pipewire, wireplumber and filter-chain but NOT
`pipewire-pulse`; the new session starts a new pipewire, and the old
`pipewire-pulse` stays attached to nothing ⇒ the programs that speak
PulseAudio (firefox-esr inside the session) are mute, and our sink captures
only digital silence.  The cure is in `src/sessione.c` («THE `pipewire-pulse`
LEFT OVER FROM THE PREVIOUS SESSION»).

⛔ WHY NOT `pw-play` (F-012's): it is a NATIVE PipeWire client, it talks
   to the new pipewire and is heard even with the defect.  Here a REAL
   PulseAudio client plays: `libpulse-simple` (the same library the
   PulseAudio programs use) called from python3 with ctypes — in the four
   boxes there is no `paplay` (pulseaudio-utils is not installed) and ffmpeg is
   compiled without the pulse output.  The tone is F-012's (440 Hz,
   amplitude 0.5, DEFAULT sink, no target).

THE SCENE (one tenant, c15912u<n>):
  1  login with F-012's ear (`15-g4-comune.py`), the pulse client
     plays ⇒ the tone MUST arrive (if not, the test has no base: BLOCKED);
  2  «Exit» with F-021's gesture (the method the menu entry reaches):
     the product declares the end, the page goes back to the form;
  3  AT ONCE a new login (page reloaded, ear put back): the
     log says «I AM MAKING IT BE BORN» (new session) and the user manager
     is the SAME as before (same pid of `systemd --user`) — otherwise the
     scene of the defect is not there and I have looked at nothing (BLOCKED);
  4  the pulse client plays again ⇒ the tone MUST reach the browser.

F-012B  expected: at point 4, F-012's judge (>= 80 % of the samples
        audible, peak at 440 ± 12 Hz over 6 s) says PASS, AND `pipewire-pulse`
        is not older than `pipewire` (start read from /proc/<pid>/stat,
        tolerance 2 s; pid and start time of pipewire, pipewire-pulse,
        wireplumber and of the user manager are written in the evidence at the
        four moments: plays, after «Exit», after the re-entry, plays again).

FAULT (same session, after the healthy pass): at point 4 NOTHING plays
  g1  the pulse client killed ⇒ the same reading of the ear MUST say FAIL;
  g2  the real samples of point 4 against a WRONG EXPECTATION (660 Hz) ⇒ FAIL;
  g3  the pid rule on a FAKE photo of the defect (pulse born before
      pipewire) ⇒ FAIL.
  Seen = all three red.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

F12 = S._carica("f012", os.path.join(S.QUI, "15-f012-audio.py"))
F21 = S._carica("f021", os.path.join(S.QUI, "15-f021-esci.py"))
G4 = F12.G4

FUNZIONI = ("F-012B",)
CLIENT = "c15pulse.py"
SEGNO_CLIENT = "c15pulse"
TOLL_INIZIO_S = 2.0
# the units of the user manager that are photographed; `systemd` in the init.scope
# is the manager itself
UNITA = ("pipewire.service", "pipewire-pulse.service", "wireplumber.service",
         "filter-chain.service")

# ⭐ The PulseAudio client: libpulse-simple, the tone in a loop until it is
#   killed.  If the pulse server does not answer (or the write falls over) it says so and
#   retries, like a real player.
CLIENT_PY = r'''
import ctypes, sys, time, wave
pa = ctypes.CDLL("libpulse-simple.so.0")
class Spec(ctypes.Structure):
    _fields_ = [("format", ctypes.c_int), ("rate", ctypes.c_uint32), ("channels", ctypes.c_uint8)]
pa.pa_simple_new.restype = ctypes.c_void_p
pa.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                             ctypes.c_char_p, ctypes.POINTER(Spec), ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
pa.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t,
                               ctypes.POINTER(ctypes.c_int)]
pa.pa_simple_free.argtypes = [ctypes.c_void_p]
w = wave.open(sys.argv[1])
assert w.getsampwidth() == 2
spec = Spec(3, w.getframerate(), w.getnchannels())          # PA_SAMPLE_S16LE
dati = w.readframes(w.getnframes())
pezzo = w.getframerate() * w.getnchannels() * 2 // 10       # 100 ms
while True:
    err = ctypes.c_int(0)
    h = pa.pa_simple_new(None, b"c15pulse", 1, None, b"tono 440", ctypes.byref(spec),
                         None, None, ctypes.byref(err))      # 1 = PA_STREAM_PLAYBACK
    if not h:
        print("pa_simple_new: error %d" % err.value, flush=True)
        time.sleep(1)
        continue
    print("connected to the pulse server", flush=True)
    vivo = True
    while vivo:
        for i in range(0, len(dati), pezzo):
            b = dati[i:i + pezzo]
            if pa.pa_simple_write(h, b, len(b), ctypes.byref(err)) < 0:
                print("pa_simple_write: error %d" % err.value, flush=True)
                vivo = False
                break
    pa.pa_simple_free(h)
    time.sleep(1)
'''


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def leggi_foto(testo):
    """The lines `@@p <comm> <pid> <start_tick> <unit>` and `@@hz <n>` ⇒
    {"hz": n, "proc": [{"comm", "pid", "inizio_s", "unita"}]} — pure."""
    hz, proc = None, []
    for r in (testo or "").splitlines():
        p = r.split()
        if len(p) == 2 and p[0] == "@@hz" and p[1].isdigit():
            hz = int(p[1])
        elif len(p) >= 4 and p[0] == "@@p" and p[2].isdigit() and p[3].isdigit():
            proc.append({"comm": p[1], "pid": int(p[2]), "tick": int(p[3]),
                         "unita": p[4] if len(p) > 4 else ""})
    for x in proc:
        x["inizio_s"] = round(x.pop("tick") / float(hz or 100), 2)
    return {"hz": hz, "proc": proc}


def di(foto, unita):
    """The unit's process (or the manager, `unita="init.scope"`), or None.
    If there is more than one: the OLDEST (it is the one left over)."""
    v = [x for x in (foto or {}).get("proc", []) if x["unita"] == unita
         and (unita != "init.scope" or x["comm"] == "systemd")]
    return min(v, key=lambda x: x["inizio_s"]) if v else None


def riassunto(foto):
    pezzi = []
    for u in ("init.scope",) + UNITA:
        x = di(foto, u)
        if x:
            pezzi.append("%s pid %d since %.1f s" % (u.replace(".service", "").replace(
                "init.scope", "manager"), x["pid"], x["inizio_s"]))
    return ", ".join(pezzi) or "(none)"


def giudica_pid(prima, dopo):
    """(outcome, reason) of the rule: pipewire-pulse not older than
    pipewire in the new session, with the user manager survived.
    `prima` = photo of session 1, `dopo` = photo of session 2 that plays."""
    g1, g2 = di(prima, "init.scope"), di(dopo, "init.scope")
    if not g1 or not g2:
        return S.BLOCKED, "I do not see the user manager (before %s, after %s)" % (g1, g2)
    if g1["pid"] != g2["pid"]:
        return S.BLOCKED, ("the user manager did NOT survive the exit (pid %d ⇒ %d): "
                           "the scene of the defect is not there" % (g1["pid"], g2["pid"]))
    pw, pp = di(dopo, "pipewire.service"), di(dopo, "pipewire-pulse.service")
    if not pw:
        return S.FAIL, "in the new session there is no pipewire"
    if not pp:
        return S.FAIL, "in the new session, with the pulse client playing, there is no pipewire-pulse"
    if pp["inizio_s"] < pw["inizio_s"] - TOLL_INIZIO_S:
        vecchio = di(prima, "pipewire-pulse.service")
        return S.FAIL, ("pipewire-pulse (pid %d, since %.1f s) is OLDER than pipewire "
                        "(pid %d, since %.1f s)%s" % (
                            pp["pid"], pp["inizio_s"], pw["pid"],
                            pw["inizio_s"], " — it is the one from the previous session"
                            if vecchio and vecchio["pid"] == pp["pid"] else ""))
    return S.PASS, ("manager alive (pid %d); pipewire-pulse pid %d since %.1f s, pipewire pid %d "
                    "since %.1f s" % (g2["pid"], pp["pid"], pp["inizio_s"], pw["pid"],
                                   pw["inizio_s"]))


def giudica(e_tono, d_tono, e_pid, d_pid):
    """The outcome of F-012B: the tone at point 4 and the pid rule."""
    if e_pid == S.BLOCKED:
        return S.BLOCKED, d_pid
    guai = []
    if e_tono != "PASS":
        guai.append("after «Exit» and the re-entry the PulseAudio program is NOT heard in the "
                    "browser: %s" % d_tono)
    if e_pid != S.PASS:
        guai.append(d_pid)
    if guai:
        if e_tono == "BLOCKED" and e_pid == S.PASS:
            return S.BLOCKED, " · ".join(guai)
        return S.FAIL, " · ".join(guai)
    return S.PASS, "after «Exit» and the re-entry the tone is heard: %s · %s" % (d_tono, d_pid)


def certifica():
    guai = 0

    def p(nome, ottenuto, atteso):
        nonlocal guai
        ok = ottenuto == atteso
        guai += not ok
        print("  %s %-62s %s (expected %s)" % ("OK " if ok else "NO ", nome, ottenuto, atteso))

    U = "user@4013.service"
    t1 = ("@@hz 100\n@@p systemd 700 1000 init.scope\n@@p pipewire 710 1100 pipewire.service\n"
          "@@p pipewire 711 1100 filter-chain.service\n"
          "@@p pipewire-pulse 712 1110 pipewire-pulse.service\n")
    prima = leggi_foto(t1)
    p("⭐ the photo reads (4 processes, hz 100)", (prima["hz"], len(prima["proc"])), (100, 4))
    p("⭐ the pipewire is pipewire.service's, not filter-chain",
      di(prima, "pipewire.service")["pid"], 710)
    sana = leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                      "@@p pipewire 810 9000 pipewire.service\n"
                      "@@p pipewire-pulse 812 9050 pipewire-pulse.service\n")
    p("⭐ new session, pulse born after pipewire ⇒ PASS", giudica_pid(prima, sana)[0], S.PASS)
    difetto = leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                         "@@p pipewire 810 9000 pipewire.service\n"
                         "@@p pipewire-pulse 712 1110 pipewire-pulse.service\n")
    p("⛔ the pulse of the previous session stays ⇒ FAIL", giudica_pid(prima, difetto)[0], S.FAIL)
    p("⛔ ⇒ and it says so", "previous session" in giudica_pid(prima, difetto)[1], True)
    p("⭐ pulse born 1 s earlier (socket activation) ⇒ PASS, tolerance",
      giudica_pid(prima, leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"
                                    "@@p pipewire-pulse 812 8900 pipewire-pulse.service\n"))[0],
      S.PASS)
    p("⚠ manager reborn ⇒ BLOCKED (the scene is not there)",
      giudica_pid(prima, leggi_foto("@@hz 100\n@@p systemd 900 8000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"
                                    "@@p pipewire-pulse 812 9050 pipewire-pulse.service\n"))[0],
      S.BLOCKED)
    p("⚠ photo not read ⇒ BLOCKED, never PASS", giudica_pid(prima, leggi_foto(""))[0], S.BLOCKED)
    p("⛔ pulse absent with the client playing ⇒ FAIL",
      giudica_pid(prima, leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"))[0], S.FAIL)
    p("⛔ a systemd not in the init.scope is not the manager",
      di(leggi_foto("@@p systemd 5 1 %s\n" % U), "init.scope"), None)
    p("⭐ tone PASS and pid PASS ⇒ PASS", giudica("PASS", "x", S.PASS, "y")[0], S.PASS)
    p("⛔ tone FAIL (silence) ⇒ FAIL", giudica("FAIL", "x", S.PASS, "y")[0], S.FAIL)
    p("⛔ tone PASS but old pulse ⇒ FAIL", giudica("PASS", "x", S.FAIL, "y")[0], S.FAIL)
    p("⚠ manager reborn ⇒ BLOCKED even with the tone", giudica("PASS", "x", S.BLOCKED, "y")[0],
      S.BLOCKED)
    p("⚠ few samples and pids in order ⇒ BLOCKED", giudica("BLOCKED", "x", S.PASS, "y")[0],
      S.BLOCKED)
    print("⛔ %d wrong cases" % guai if guai else "⭐ the judges say what they must")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def fotografa(s):
    """Pid, start and unit of the tenant's processes that matter (pipewire,
    pipewire-pulse, wireplumber, the manager) ⇒ (photo, raw text)."""
    def una():
        c, t = s.sc.dentro(
            "echo \"@@hz $(getconf CLK_TCK)\"; for p in $(pgrep -u %s); do "
            "n=$(cat /proc/$p/comm 2>/dev/null); case \"$n\" in systemd|pipewire*|wireplumber) "
            "st=$(awk '{print $22}' /proc/$p/stat 2>/dev/null); "
            "u=$(head -1 /proc/$p/cgroup 2>/dev/null | awk -F/ '{print $NF}'); "
            "echo \"@@p $n $p $st $u\";; esac; done; echo @@fine; "
            "echo \"@@ora_s $(cut -d' ' -f1 /proc/uptime)\"; "
            "ps -o pid,lstart,etimes,args -u %s | grep -E 'systemd --user|pipewire|wireplumber' "
            "| grep -v grep" % (s.chi, s.chi), 40)
        return t if "@@fine" in (t or "") else None
    t = F21._ritenta(una) or ""
    return leggi_foto(t), t


def prepara_client(s):
    h = "/home/%s/%s" % (s.chi, CLIENT)
    c, t = s.sc.dentro("cat > %s <<'@@FINE@@'\n%s\n@@FINE@@\nchown %s: %s && ls -l %s"
                       % (h, CLIENT_PY, s.chi, h, h), 30)
    return c == 0, (t or "").strip()[-200:]


def suona_pulse(s):
    return s.nella_sessione("exec python3 /home/%s/%s /home/%s/%s # %s"
                            % (s.chi, CLIENT, s.chi, F12.WAV, SEGNO_CLIENT))


def zittisci_pulse(s):
    s.sc.dentro("pkill -u %s -f '[c]15pulse'; sleep 0.3; pgrep -u %s -f '[c]15pulse' || "
                "echo zitto" % (s.chi, s.chi), 30)


def diario_client(s):
    _c, t = s.sc.dentro("tail -n 20 /home/%s/.c15-exec.log 2>/dev/null" % s.chi, 30)
    return (t or "").strip()


def client_visto(s):
    """Is the pulse client seen by the session's pipewire? (diagnosis)"""
    _c, t = s.come_utente("pw-cli ls Client 2>&1 | grep -c c15pulse", 30)
    return (t or "").strip()


def entra_e_ascolta(s, nome, ev, note):
    """The client plays and the ear listens for FINESTRA_S ⇒ (outcome, descr, numbers, r)."""
    c, t = suona_pulse(s)
    if c != 0:
        raise S.Bloccata("the pulse client does not start in the session: " + (t or "")[-200:])
    if not F12.sveglia(s, note):
        return "FAIL", "no AudioContext in the page in 30 s", {}, {}
    time.sleep(1.0)
    e, d, num, r = F12.ascolta(s, F12.FINESTRA_S)
    ev.append(G4.salva_json(s.o, "f012b-orecchio-%s.json" % nome, r))
    note.append("%s: client «%s», seen by pipewire: %s" % (
        nome, diario_client(s).replace("\n", " | ")[-160:], client_visto(s)))
    return e, d, num, r


def corpo(o, E):
    sess = S.Sessione(o, "912", E)
    G4.robusta(sess.sc)
    with sess as s:
        desktop, gesto = s.sc.gesto_esci()
        if not gesto:
            raise S.Bloccata("I do not know how to say «Exit» in %s" % s.sc.contenitore)
        print("   «Exit» (%s): %s" % (desktop, gesto), flush=True)
        ok, m = F12.entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata(m)
        ok, m = F12.prepara_tono_ffmpeg(s)
        if not ok:
            print("   ⚠ the tone with ffmpeg: %s — the bench writes it" % m, flush=True)
            ok, m = F12.prepara_tono(s)
        if not ok:
            raise S.Bloccata("the tone does not get ready in the box: " + m)
        ok, m = prepara_client(s)
        if not ok:
            raise S.Bloccata("the pulse client cannot be written in the box: " + m)
        segno = s.segno_registro()
        ev, note, foto = [], [], {}

        def scatta(nome):
            f, t = fotografa(s)
            foto[nome] = f
            ev.append(s.salva_testo("f012b-processi-%s.txt" % nome, t))
            print("      [%s] %s" % (nome, riassunto(f)), flush=True)
            return f

        # 1 ── the first session plays ──────────────────────────────────────
        e1, d1, _n1, _r1 = entra_e_ascolta(s, "1-prima", ev, note)
        scatta("1-suona")
        print("   1 before «Exit»: %s — %s" % (e1, d1), flush=True)
        if e1 != "PASS":
            ev.append(s.salva_testo("server-f012b.txt", s.registro_da(segno) if segno else []))
            raise S.Bloccata("already BEFORE «Exit» the pulse client is not heard (%s): it is not "
                             "the scene of this test (see F-012)" % d1)
        zittisci_pulse(s)

        # 2 ── «Exit» like the user ──────────────────────────────────────────
        segno_esci = F21._ritenta(s.segno_registro)
        c, t = F21.fai_il_gesto(s, gesto)
        if c != 0:
            raise S.Bloccata("the «Exit» gesture did not answer (code %s): %s" % (c, t[-200:]))
        t0 = time.time()
        finita, _r = F21.aspetta_finita(s, segno_esci, F21.TETTO_FINITA)
        if not finita:
            raise S.Bloccata("after «Exit» the product does not declare the session ended in %.0f s"
                             % F21.TETTO_FINITA)
        modulo, frase, _letta = F21.leggi_pagina(s, 30)
        esci = "ended («%s») after %.1f s, page at the form=%s «%s»" % (
            finita, time.time() - t0, modulo, frase[:60])
        print("   2 %s" % esci, flush=True)
        scatta("2-dopo-esci")

        # 3 ── inside again AT ONCE ─────────────────────────────────────────
        segno_rientro = F21._ritenta(s.segno_registro)
        t1 = time.time()
        ok, m = F12.entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata("the re-entry after «Exit» does not succeed: %s" % m)
        fetta = F21.registro(s, segno_rientro) or []
        nuova = any("I AM MAKING IT BE BORN" in r and F21.e_di(r, s.chi) for r in fetta)
        rientro = "re-entry %.1f s after the form, session %s" % (
            t1 - t0, "NEW («I AM MAKING IT BE BORN»)" if nuova else "NOT new (resumed?)")
        print("   3 %s" % rientro, flush=True)
        scatta("3-dopo-rientro")
        if not nuova:
            ev.append(s.salva_testo("server-f012b.txt", s.registro_da(segno) if segno else []))
            raise S.Bloccata("the re-entry did not make a new session be born: the scene "
                             "of the defect is not there (%s)" % rientro)

        # 4 ── the pulse client plays again ─────────────────────────────────
        e4, d4, num4, r4 = entra_e_ascolta(s, "4-dopo-esci", ev, note)
        campioni4 = r4.get("campioni") or []
        dopo = scatta("4-risuona")
        e_pid, d_pid = giudica_pid(foto["1-suona"], dopo)
        nome, _v, _m, tv = F12.volume(s)
        esito, perche = giudica(e4, d4, e_pid, d_pid)
        ev.append(s.salva_testo("server-f012b.txt", s.registro_da(segno) if segno else []))
        ev.append(s.salva_console())
        _png, dove = s.foto("f012b-fine")
        if dove:
            ev.append(dove)
        oss = " · ".join([
            "1: %s" % d1, "2: %s" % esci, "3: %s" % rientro, "4: %s" % d4,
            "default sink «%s», %s" % (nome, tv),
            "pid 1: %s" % riassunto(foto["1-suona"]),
            "pid 2: %s" % riassunto(foto["2-dopo-esci"]),
            "pid 3: %s" % riassunto(foto["3-dopo-rientro"]),
            "pid 4: %s" % riassunto(dopo), "; ".join(note)])
        print("   4 %s — %s" % (esito, perche), flush=True)
        E.metti("F-012B", esito, perche,
                atteso="after «Exit» and an immediate re-entry (user manager alive) a PulseAudio "
                       "client plays and the browser hears the 440 Hz tone (>=80%% audible, "
                       "peak 440±12 Hz); pipewire-pulse not older than pipewire "
                       "(tolerance %.0f s)" % TOLL_INIZIO_S,
                osservato=oss, evidenze=ev, numeri=num4, gesto=gesto)

        if not o.guasto:
            return
        # ── the fault: at point 4 nothing plays ────────────────────────────
        zittisci_pulse(s)
        time.sleep(1.5)
        eg1, dg1, _x, rg1 = F12.ascolta(s, 4.0)
        evg = [G4.salva_json(o, "f012b-orecchio-guasto.json", rg1)]
        if not campioni4:
            E.guasto("F-012B", None, "no healthy sample at point 4 for the wrong expectation")
            return
        eg2, dg2, _y = G4.giudica_suono(campioni4, 660)
        finto = leggi_foto("@@hz 100\n@@p systemd 1 10 init.scope\n"
                           "@@p pipewire 3 900 pipewire.service\n"
                           "@@p pipewire-pulse 2 20 pipewire-pulse.service\n")
        eg3, dg3 = giudica_pid(leggi_foto("@@hz 100\n@@p systemd 1 10 init.scope\n"
                                          "@@p pipewire-pulse 2 20 pipewire-pulse.service\n"),
                               finto)
        visto = eg1 == "FAIL" and eg2 == "FAIL" and eg3 == S.FAIL
        E.guasto("F-012B", visto,
                 "at point 4 no sound ⇒ %s «%s» · 660 Hz expectation on the real samples ⇒ %s "
                 "«%s» · pulse older than pipewire (fake photo) ⇒ %s «%s»"
                 % (eg1, dg1, eg2, dg2, eg3, dg3), evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
