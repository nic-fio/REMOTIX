#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f013 — F-013 VIDEO: a video in an application of the session, CONTINUOUS IMAGE and SOUND

    python3 15-f013-video.py --scatola gnome --browser firefox [--guasto] [--ascolto-s 40] [--video-s 60]

THE SCENE.  In the box, ffmpeg generates a real file (H.264 + AAC, 1280x720,
30 frames/s, 150 s): a UNIFORM-COLOUR background that rotates (47°/s) with a white
TARGET that moves, and a continuous tone at 660 Hz.  `ffplay` plays it
(a real player: it decodes the file, Wayland window, audio to the default
sink) inside the tenant's session.

THE JUDGMENT — from the PHOTO of the canvas and from the page's EAR, in two
  windows in a row on the same video running:
  A sound   `--ascolto-s` (40 s) WITHOUT photographing: the pass-through `AnalyserNode` of
            `15-g4-comune.py`, audible >= 95 % of the samples, peak 660 ± 12 Hz,
            no silence gap longer than 1 s.
            ⛔ Without photos because `[M]` 24 Sep, KDE/Firefox: Firefox's 4K photo
            stops the page's main thread (up to 7 s), which is
            the same one that schedules the audio ⇒ during the photos 84 % audible, without
            photos 96.5 %.  The gaps were made by the bench's camera.
            The sound DURING the photos is recorded anyway, as a diagnostic.
  B image   `--video-s` (60 s), one photo per second: the video window is
            found by difference (it is the only thing that always changes); every frame
            must have the saturated uniform background with the target (no mosaic:
            tiles of another colour beyond the target ⇒ red; no black/grey),
            two consecutive photos DIFFERENT (>= 90 %), no freeze beyond 4 s.
  The browser is at 4K (Sessione).  The audio context wakes up with a REAL
  CLICK on the canvas, outside the video window.

FAULT (same session): the player STOPS (SIGSTOP to ffplay: image
  still and sound mute, like a pause) ⇒ for 20 s the image must turn out
  STILL (FAIL) and the sound SILENCE (FAIL).  Seen = both red.
"""
import importlib.util as _iu
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g4", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "15-g4-comune.py"))
G4 = _iu.module_from_spec(_s)
_s.loader.exec_module(G4)

FUNZIONI = ("F-013",)
TONO_HZ = 660
FILE = "c15-video.mp4"
GUASTO_S = 20.0


def certifica():
    return G4.certifica_comune()


def extra(a):
    a.add_argument("--video-s", type=float, default=60.0,
                   help="how long the video is photographed in the healthy pass")
    a.add_argument("--ascolto-s", type=float, default=40.0,
                   help="how long it listens, without photos, before photographing")


def prepara_video(s):
    h = "/home/%s/%s" % (s.chi, FILE)
    grafo = ("color=c=red:s=1280x720:r=30,hue=h=t*47[bg];color=c=white:s=144x144:r=30[m];"
             "[bg][m]overlay=x='abs(mod(t*400,2*(W-w))-(W-w))':y='(H-h)/2+(H/3)*sin(t*1.3)'[out0]")
    c, t = s.sc.dentro(
        "ffmpeg -loglevel error -y -f lavfi -i \"%s\" -f lavfi -i "
        "\"aevalsrc=0.5*sin(2*PI*%d*t)|0.5*sin(2*PI*%d*t):s=48000\" -t 150 "
        "-c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -b:a 160k %s "
        "&& chown %s: %s && ls -l %s" % (grafo, TONO_HZ, TONO_HZ, h, s.chi, h, h), 120)
    return c == 0, t.strip()[-300:]


def accendi_video(s):
    return s.nella_sessione(
        "SDL_VIDEODRIVER=wayland ffplay -loglevel warning -loop 0 -window_title c15video "
        "-x 1280 -y 720 /home/%s/%s" % (s.chi, FILE))


def segnale(s, sig):
    return s.sc.dentro("pkill -%s -u %s -x ffplay; pgrep -u %s -x ffplay >/dev/null "
                       "&& echo vivo || echo morto" % (sig, s.chi, s.chi), 30)


def fuori_dal_video(box, im):
    """A point of the canvas (fractions) outside the video window, far from the edges."""
    w, h = im.size
    x0, y0, x1, y1 = box[0] / w, box[1] / h, box[2] / w, box[3] / h
    for fx, fy in ((0.86, 0.5), (0.14, 0.5), (0.5, 0.82), (0.5, 0.2), (0.86, 0.25), (0.14, 0.75)):
        if not (x0 - 0.04 <= fx <= x1 + 0.04 and y0 - 0.04 <= fy <= y1 + 0.04):
            return fx, fy
    return 0.97, 0.5


def guarda(s, o, box, secondi, nome, salva_ogni=6, minimo=6, tetto=90.0):
    """Photos for `secondi` (and at least `minimo` photos, within `tetto` s):
    [(t, crop)], [saved paths].
    ⚠ `[M]` 24 Sep: with the page STILL Chrome photographs in ~8 s each ⇒ a
    frozen video (the fault, or a real defect) would give 3 photos and a BLOCKED
    instead of a red: it continues until `minimo` photos."""
    quadri, salvate = [], []
    t0 = time.time()
    k = 0
    while (time.time() - t0 < secondi or len(quadri) < minimo) and time.time() - t0 < tetto:
        # ⚠ one photo per second at most: Chrome photographs every 0.15 s, and at
        #   that pace two equal photos mean «no new frame in
        #   150 ms», not «still image» (`[M]` 24 Sep, GNOME/Chrome: 87 %)
        prossima = t0 + k * 1.0
        if time.time() < prossima:
            time.sleep(prossima - time.time())
        im, _png, perche = G4.foto_ridotta(s.g, 0.5)
        t = time.time() - t0
        if im is None:
            print("   ⚠ photo %d: %s" % (k, perche), flush=True)
            time.sleep(0.5)
            continue
        quadri.append((t, G4.ritaglia(im, box)))
        if o.evidenze and (k % salva_ogni == 0):
            p = os.path.join(o.evidenze, "f013-%s-%03d.jpg" % (nome, k))
            im.save(p, quality=70)
            salvate.append(p)
        k += 1
    if o.evidenze and quadri:
        # all the crops, in a strip: you can see by eye whether it moves
        from PIL import Image
        col = 10
        righe = (len(quadri) + col - 1) // col
        st = Image.new("RGB", (160 * col, 90 * righe), (0, 0, 0))
        for i, (_t, c) in enumerate(quadri):
            st.paste(c, ((i % col) * 160, (i // col) * 90))
        p = os.path.join(o.evidenze, "f013-%s-ritagli.png" % nome)
        st.save(p)
        salvate.append(p)
    return quadri, salvate


def corpo(o, E):
    sess = S.Sessione(o, "013", E)
    G4.robusta(sess.sc)
    with sess as s:
        ok, m = G4.entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata(m)
        ok, m = prepara_video(s)
        if not ok:
            raise S.Bloccata("the video is not generated in the box: " + m)
        segno = s.segno_registro()
        c, t = accendi_video(s)
        if c != 0:
            raise S.Bloccata("ffplay does not start in the session: " + t[-200:])
        time.sleep(4)
        # the video window, by difference
        box, desc, prime = None, "", []
        fine = time.time() + 40
        while time.time() < fine and box is None:
            im, _p, perche = G4.foto_ridotta(s.g, 0.5)
            if im is not None:
                prime = (prime + [im])[-4:]
            if len(prime) >= 4:
                box, desc = G4.trova_video(prime)
            time.sleep(0.7)
        ev = []
        if box is None:
            if prime and o.evidenze:
                p = os.path.join(o.evidenze, "f013-video-NON-trovato.jpg")
                prime[-1].save(p, quality=80)
                ev.append(p)
            _c, log = s.come_utente("tail -n 5 /home/%s/.c15-SDL_VIDEODRIVERwayland.log "
                                    "/home/%s/.c15-*.log 2>/dev/null" % (s.chi, s.chi), 20)
            _c, vivo = segnale(s, "0")
            ev.append(s.salva_testo("ffplay-f013.txt", log))
            if "morto" in vivo:
                raise S.Bloccata("ffplay died in the session: " + log[-300:])
            E.metti("F-013", S.FAIL, "ffplay runs in the session but in the canvas no "
                    "moving video is seen: " + desc, atteso="visible video that moves",
                    osservato=desc, evidenze=ev + [s.salva_console()])
            return
        print("   video found: %s" % desc, flush=True)
        # the gesture: a real click outside the video window
        note = []
        stato, conti = G4.aspetta_contesto(s.g, 20)
        note.append("audio context «%s»" % stato)
        fx, fy = fuori_dal_video(box, prime[-1])
        note.append(G4.clic_vero(s, fx, fy))
        time.sleep(1.5)
        stato2, _ = G4.aspetta_contesto(s.g, 5)
        note.append("after the click «%s»" % stato2)

        # A — the SOUND, listened to without photographing: `[M]` 24 Sep, Firefox's 4K
        #     photo stops the page's main thread, which is the same one
        #     that schedules the audio (250 ms cushion) ⇒ the gaps were made by the bench.
        ta = G4.ora_pagina(s.g)
        time.sleep(o.ascolto_s)
        r = G4.leggi_orecchio(s.g, ta) or {}
        es, ds, ns = G4.giudica_suono(r.get("campioni") or [], TONO_HZ, min_frazione=0.95,
                                      max_buco_s=1.0, min_campioni=int(o.ascolto_s * 3))
        # B — the IMAGE, one photo per second; the sound of this window is only
        #     a diagnostic (it also hears the price of the photos)
        tb = G4.ora_pagina(s.g)
        quadri, salvate = guarda(s, o, box, o.video_s, "sano")
        rb = G4.leggi_orecchio(s.g, tb) or {}
        ev += salvate + [G4.salva_json(o, "f013-orecchio-sano.json", r),
                         G4.salva_json(o, "f013-orecchio-durante-le-foto.json", rb)]
        ei, di, ni = G4.giudica_immagine(quadri)
        esb, dsb, nsb = G4.giudica_suono(rb.get("campioni") or [], TONO_HZ, min_frazione=0.95,
                                         max_buco_s=1.0, min_campioni=10)
        note.append("sound DURING the photos (diagnostic, does not judge): %s %s" % (esb, dsb))
        ev += [s.salva_testo("server-f013.txt", s.registro_da(segno) if segno else []),
               s.salva_console()]
        atteso = ("sound: for %.0f s 660 Hz tone audible >=95%%, gap <=1 s; then image for "
                  "%.0f s that moves (>=90%% different photos, freeze <=4 s, frames without mosaic)"
                  % (o.ascolto_s, o.video_s))
        oss = "%s · IMAGE %s · SOUND %s" % ("; ".join(note), di, ds)
        num = {"immagine": ni, "suono": ns, "suono_durante_foto": nsb, "finestra": desc}
        if "BLOCKED" in (ei, es) and "FAIL" not in (ei, es):
            E.metti("F-013", S.BLOCKED, "I could not look: image «%s» · sound «%s»"
                    % (di, ds), atteso=atteso, osservato=oss, evidenze=ev, numeri=num)
        elif ei == "PASS" and es == "PASS":
            E.metti("F-013", S.PASS, "continuous video and sound present: %s · %s" % (di, ds),
                    atteso=atteso, osservato=oss, evidenze=ev, numeri=num)
        else:
            male = []
            if ei != "PASS":
                male.append("image: " + di)
            if es != "PASS":
                male.append("sound: " + ds)
            E.metti("F-013", S.FAIL, " · ".join(male), atteso=atteso, osservato=oss,
                    evidenze=ev, numeri=num)

        if o.guasto:
            _c, v = segnale(s, "STOP")
            time.sleep(2.0)
            ta = G4.ora_pagina(s.g)
            qg, sg = guarda(s, o, box, GUASTO_S, "guasto", salva_ogni=5)
            rg = G4.leggi_orecchio(s.g, ta) or {}
            eig, dig, _ = G4.giudica_immagine(qg)
            esg, dsg, _ = G4.giudica_suono(rg.get("campioni") or [], TONO_HZ, min_frazione=0.95,
                                           max_buco_s=1.0, min_campioni=int(GUASTO_S * 3))
            segnale(s, "CONT")
            segnale(s, "KILL")
            evg = sg + [G4.salva_json(o, "f013-orecchio-guasto.json", rg)]
            if "BLOCKED" in (eig, esg):
                E.guasto("F-013", None, "player stopped: image %s «%s» · sound %s «%s»"
                         % (eig, dig, esg, dsg), evidenze=evg)
            else:
                E.guasto("F-013", eig == "FAIL" and esg == "FAIL",
                         "player stopped (SIGSTOP, %s): image ⇒ %s «%s» · sound ⇒ %s «%s»"
                         % (v.strip()[-10:], eig, dig, esg, dsg), evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra))
