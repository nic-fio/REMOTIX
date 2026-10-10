#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f012 — F-012 AUDIO: a real application plays, the BROWSER hears sound and not silence

    python3 15-f012-audio.py --scatola kde --browser chrome [--guasto]

THE SCENE.  Inside the tenant's session runs a real application that
plays: `pw-play` (a PipeWire client like any player) of a pure tone at
440 Hz, amplitude 0.5, on the DEFAULT sink — ⛔ without `--target`: a real
program does not know the sink is called «remotix», and if the default were not
the product's the user would hear nothing.

THE JUDGMENT — a field measured IN THE BROWSER, not a packet counter.
  The ear of `15-g4-comune.py`: an `AnalyserNode` placed as a pass-through between
  the blocks the page schedules and the `AudioDestinationNode` (that is, what goes
  to the loudspeaker).  RMS level and peak frequency every 100 ms.
  ⭐ The gesture: the page's context is born `suspended` without a user
  gesture; the bench makes a REAL CLICK on the canvas (trusted event), like
  the user.  It is written whether the context was suspended and whether the click woke it.

F-012  expected: over 6 s, audible >= 80 % of the samples (RMS > −40 dBFS with the context
       running), peak at 440 ± 12 Hz for >= 80 % of the audible ones;
       and I5 (SPECIFICHE §10, `src/suono.c` `alza()` called at EVERY
       connection, `figlio.c`): at connection the default sink is «remotix»
       at volume 1.00 and not muted; if the user in the session takes it to 0.10 and
       muted, the browser hears SILENCE (the slider governs: `monitor.channel-
       volumes`), and at REATTACH the volume is 1.00 again, not muted, and the tone
       is heard again.

FAULT (same session, after the healthy pass):
  g1  the application goes SILENT (pw-play killed) ⇒ the same reading must say
      silence (FAIL);
  g2  the real samples of the healthy pass judged against a WRONG EXPECTATION
      (660 Hz) ⇒ it must say FAIL.
  Seen = both red.
"""
import base64
import importlib.util as _iu
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g4", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "15-g4-comune.py"))
G4 = _iu.module_from_spec(_s)
_s.loader.exec_module(G4)

FUNZIONI = ("F-012",)
TONO_HZ = 440
FINESTRA_S = 6.0
WAV = "c15-tono-440.wav"


def certifica():
    return G4.certifica_comune()


def prepara_tono(s):
    b = base64.b64encode(G4.onda_wav(TONO_HZ, 20.0)).decode()
    # ⚠ the file is ~3.8 MB: in base64 ~5 MB, too much for a command line.
    #   ⇒ it is written inside the box in pieces.
    h = "/home/%s/%s" % (s.chi, WAV)
    s.sc.dentro("rm -f %s.b64" % h, 30)
    pezzo = 60000
    for i in range(0, len(b), pezzo):
        c, t = s.sc.dentro("printf '%%s' '%s' >> %s.b64" % (b[i:i + pezzo], h), 30)
        if c != 0:
            return False, "the tone cannot be written: %s" % t[-200:]
    c, t = s.sc.dentro("base64 -d %s.b64 > %s && rm -f %s.b64 && chown %s: %s && ls -l %s"
                       % (h, h, h, s.chi, h, h), 30)
    return c == 0, t.strip()[-200:]


def prepara_tono_ffmpeg(s):
    """⭐ Faster: the tone is written by ffmpeg INSIDE the box, with an exact
    amplitude (`aevalsrc`, not `sine` which attenuates by itself — the lesson of C5)."""
    h = "/home/%s/%s" % (s.chi, WAV)
    c, t = s.sc.dentro(
        "ffmpeg -loglevel error -y -f lavfi -i "
        "\"aevalsrc=0.5*sin(2*PI*%d*t)|0.5*sin(2*PI*%d*t):s=48000:d=20\" "
        "-c:a pcm_s16le %s && chown %s: %s && ls -l %s" % (TONO_HZ, TONO_HZ, h, s.chi, h, h), 60)
    return c == 0, t.strip()[-200:]


def suona(s):
    return s.nella_sessione("while true; do pw-play /home/%s/%s || sleep 1; done # c15tono"
                            % (s.chi, WAV))


def zittisci(s):
    s.sc.dentro("pkill -u %s -f '[c]15tono'; pkill -u %s -x pw-play; sleep 0.3; "
                "pgrep -u %s -x pw-play || echo zitto" % (s.chi, s.chi, s.chi), 30)


def wpctl(s, cosa):
    c, t = s.come_utente("wpctl %s" % cosa, 30)
    return t.strip()


def volume(s):
    """(name of the default sink, volume float | None, muted bool, text)."""
    t = wpctl(s, "get-volume @DEFAULT_AUDIO_SINK@")
    ins = wpctl(s, "inspect @DEFAULT_AUDIO_SINK@")
    m = re.search(r'node\.name = "([^"]+)"', ins)
    v = re.search(r"Volume:\s*([0-9.]+)", t)
    riga = next((r.strip() for r in t.splitlines() if "Volume:" in r), "(no Volume line: %s)"
                % t.replace("\n", " ")[-120:])
    return (m.group(1) if m else None, float(v.group(1)) if v else None, "MUTED" in t, riga)


def ascolta(s, secondi, attesa_hz=TONO_HZ, **k):
    t0 = G4.ora_pagina(s.g)
    time.sleep(secondi)
    r = G4.leggi_orecchio(s.g, t0) or {}
    camp = r.get("campioni") or []
    e, d, num = G4.giudica_suono(camp, attesa_hz, **k)
    return e, d, num, r


def sveglia(s, note):
    """Waits for the page's audio context and makes the real click."""
    stato, conti = G4.aspetta_contesto(s.g, 30)
    if stato is None:
        note.append("the page did not create an AudioContext in 30 s (counts %s)" % (conti,))
        return False
    note.append("context born «%s»" % stato)
    note.append(G4.clic_vero(s, 0.62, 0.55))
    time.sleep(1.5)
    stato2, _ = G4.aspetta_contesto(s.g, 5)
    note.append("after the click «%s»" % stato2)
    return True


def entra_con_orecchio(s):
    """The page, the ear BEFORE the login (the audio context can be born
    right after admission, if the session is already playing), then the login."""
    ok, m = s.pr.apri()
    if not ok:
        return False, "the page does not open: " + m
    ok, m = G4.metti_orecchio(s.g)
    if not ok:
        return False, m
    ok, m = s.entra(apri=False)
    if not ok:
        return False, "without a session there is no audio to look at: " + m
    return True, m


def corpo(o, E):
    sess = S.Sessione(o, "012", E)
    G4.robusta(sess.sc)
    with sess as s:
        ok, m = entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata(m)
        ok, m = prepara_tono_ffmpeg(s)
        if not ok:
            print("   ⚠ the tone with ffmpeg: %s — the bench writes it" % m, flush=True)
            ok, m = prepara_tono(s)
        if not ok:
            raise S.Bloccata("the tone does not get ready in the box: " + m)
        segno = s.segno_registro()
        c, t = suona(s)
        if c != 0:
            raise S.Bloccata("pw-play does not start in the session: " + t[-200:])
        note = []
        if not sveglia(s, note):
            r = G4.leggi_orecchio(s.g) or {}
            conti = r.get("conti")
            nome, vol, muto, tv = volume(s)
            ev = [s.salva_testo("server-f012.txt", s.registro_da(segno) if segno else []),
                  s.salva_console()]
            if conti and (conti.get("ricevuti") or 0) > 0:
                raise S.Bloccata("the page receives audio (%s) but the ear does not see the context"
                                 % conti)
            E.metti("F-012", S.FAIL, "the application plays and no audio reaches the page: "
                    "no AudioContext in 30 s (default sink %s, %s)" % (nome, tv),
                    atteso="440 Hz tone in the browser", osservato="; ".join(note), evidenze=ev)
            return
        time.sleep(1.0)
        e1, d1, num1, r1 = ascolta(s, FINESTRA_S)
        campioni_sani = r1.get("campioni") or []
        ev = [G4.salva_json(o, "f012-orecchio-sano.json", r1)]
        nome, vol, muto, tv = volume(s)
        i5 = ["at connection: default sink «%s», %s" % (nome, tv)]
        male = []
        if e1 != "PASS":
            male.append("the tone: " + d1)
        if nome != "remotix":
            male.append("I5: the default sink is «%s», not «remotix»" % nome)
        if vol is None or abs(vol - 1.0) > 0.005 or muto:
            male.append("I5: at connection the volume is not at maximum: %s" % tv)

        # I5, second half: the user lowers and mutes ⇒ silence; reattach ⇒ maximum
        wpctl(s, "set-volume @DEFAULT_AUDIO_SINK@ 0.10")
        wpctl(s, "set-mute @DEFAULT_AUDIO_SINK@ 1")
        time.sleep(1.5)
        _n, vb, mb, tvb = volume(s)
        e2, d2, num2, r2 = ascolta(s, 3.0)
        ev.append(G4.salva_json(o, "f012-orecchio-muto.json", r2))
        i5.append("lowered and muted in the session (%s) ⇒ %s" % (tvb, d2))
        if e2 == "PASS" or (num2.get("udibili") or 0) > 0.2:
            male.append("I5: with the sink muted at 0.10 the browser STILL HEARS (the session's "
                        "slider does not govern): %s" % d2)
        # the reattach: the page again, user and password, same session
        ok, m = entra_con_orecchio(s)
        if not ok:
            male.append("I5: the reattach does not succeed: %s" % m)
        else:
            note2 = []
            if ok and sveglia(s, note2):
                time.sleep(1.0)
                _n, vr, mr, tvr = volume(s)
                e3, d3, num3, r3 = ascolta(s, 4.0)
                ev.append(G4.salva_json(o, "f012-orecchio-riattacco.json", r3))
                i5.append("at reattach: %s ⇒ %s" % (tvr, d3))
                if vr is None or abs(vr - 1.0) > 0.005 or mr:
                    male.append("I5: at reattach the volume does NOT go back to maximum: %s" % tvr)
                if e3 != "PASS":
                    male.append("I5: at reattach the tone is not heard again: %s" % d3)
            else:
                male.append("I5: after the reattach the page does not play (%s %s)" % (m, note2))
        # server evidence
        ev.append(s.salva_testo("server-f012.txt", s.registro_da(segno) if segno else []))
        ev.append(s.salva_console())
        foto, dove = s.foto("f012-fine")
        if dove:
            ev.append(dove)
        oss = "%s · %s · %s" % ("; ".join(note), d1, " | ".join(i5))
        atteso = ("440 Hz tone audible in the browser (>=80%% of the samples, peak 440±12 Hz); "
                  "I5: sink «remotix» at 1.00 not muted at connection, muted ⇒ silence, "
                  "reattach ⇒ 1.00 again and tone")
        if male:
            E.metti("F-012", S.FAIL, " · ".join(male), atteso=atteso, osservato=oss, evidenze=ev,
                    numeri=num1)
        else:
            E.metti("F-012", S.PASS, "tone heard in the browser: %s; I5 holds" % d1,
                    atteso=atteso, osservato=oss, evidenze=ev, numeri=num1)

        if o.guasto:
            # g2 first (it does not touch the scene): the wrong expectation on the real samples
            eg2, dg2, _ = G4.giudica_suono(campioni_sani, 660)
            # g1: the application goes silent
            zittisci(s)
            time.sleep(1.5)
            eg1, dg1, _n1, rg1 = ascolta(s, 4.0)
            evg = [G4.salva_json(o, "f012-orecchio-guasto.json", rg1)]
            if not campioni_sani:
                E.guasto("F-012", None, "no healthy sample on which to judge the wrong expectation")
            else:
                visto = eg1 == "FAIL" and eg2 == "FAIL"
                E.guasto("F-012", visto,
                         "application silenced ⇒ %s «%s» · 660 Hz expectation on the real samples ⇒ %s «%s»"
                         % (eg1, dg1, eg2, dg2), evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
