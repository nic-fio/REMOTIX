#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f013 — F-013 VIDEO: un video in un'applicazione della sessione, IMMAGINE CONTINUA e SUONO

    python3 15-f013-video.py --scatola gnome --browser firefox [--guasto] [--ascolto-s 40] [--video-s 60]

LA SCENA.  Nella scatola, ffmpeg genera un file vero (H.264 + AAC, 1280x720,
30 quadri/s, 150 s): fondo a TINTA UNIFORME che ruota (47°/s) con una MIRA
bianca che si muove, e un tono continuo a 660 Hz.  Lo riproduce `ffplay`
(lettore vero: decodifica il file, finestra Wayland, audio verso il sink
predefinito) dentro la sessione dell'inquilino.

IL GIUDIZIO — dalla FOTOGRAFIA della tela e dall'ORECCHIO della pagina, in due
  finestre di seguito sullo stesso video che gira:
  A suono   `--ascolto-s` (40 s) SENZA fotografare: l'`AnalyserNode` passante di
            `15-g4-comune.py`, udibile >= 95 % dei campioni, picco 660 ± 12 Hz,
            nessun buco di silenzio piu' lungo di 1 s.
            ⛔ Senza foto perche' `[M]` 24 set, KDE/Firefox: la foto 4K di
            Firefox ferma il thread principale della pagina (fino a 7 s), che e'
            lo stesso che programma l'audio ⇒ durante le foto 84 % udibile, senza
            foto 96,5 %.  I buchi li faceva la macchina fotografica del banco.
            Il suono DURANTE le foto si registra lo stesso, come diagnostica.
  B immagine `--video-s` (60 s), una foto al secondo: la finestra del video si
            trova per differenza (e' l'unica cosa che cambia sempre); ogni quadro
            deve avere il fondo saturo uniforme con la mira (niente mosaico:
            tessere di un altro colore oltre la mira ⇒ rosso; niente nero/grigio),
            due foto consecutive DIVERSE (>= 90 %), nessun blocco oltre 4 s.
  Il browser e' a 4K (Sessione).  Il contesto audio si sveglia con un CLIC
  VERO sulla tela, fuori dalla finestra del video.

GUASTO (stessa sessione): il lettore si FERMA (SIGSTOP a ffplay: immagine
  ferma e suono muto, come una pausa) ⇒ per 20 s l'immagine deve risultare
  FERMA (FAIL) e il suono SILENZIO (FAIL).  Visto = tutt'e due rossi.
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
                   help="quanto si fotografa il video nella passata sana")
    a.add_argument("--ascolto-s", type=float, default=40.0,
                   help="quanto si ascolta, senza foto, prima di fotografare")


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
    """Un punto della tela (frazioni) fuori dalla finestra del video, lontano dai bordi."""
    w, h = im.size
    x0, y0, x1, y1 = box[0] / w, box[1] / h, box[2] / w, box[3] / h
    for fx, fy in ((0.86, 0.5), (0.14, 0.5), (0.5, 0.82), (0.5, 0.2), (0.86, 0.25), (0.14, 0.75)):
        if not (x0 - 0.04 <= fx <= x1 + 0.04 and y0 - 0.04 <= fy <= y1 + 0.04):
            return fx, fy
    return 0.97, 0.5


def guarda(s, o, box, secondi, nome, salva_ogni=6, minimo=6, tetto=90.0):
    """Foto per `secondi` (e almeno `minimo` foto, entro `tetto` s):
    [(t, crop)], [percorsi salvati].
    ⚠ `[M]` 24 set: con la pagina FERMA Chrome fotografa in ~8 s l'una ⇒ un
    video bloccato (il guasto, o un difetto vero) darebbe 3 foto e un BLOCKED
    invece di un rosso: si continua fino a `minimo` foto."""
    quadri, salvate = [], []
    t0 = time.time()
    k = 0
    while (time.time() - t0 < secondi or len(quadri) < minimo) and time.time() - t0 < tetto:
        # ⚠ una foto al secondo al piu': Chrome fotografa ogni 0,15 s, e a
        #   quel passo due foto uguali vogliono dire «nessun quadro nuovo in
        #   150 ms», non «immagine ferma» (`[M]` 24 set, GNOME/Chrome: 87 %)
        prossima = t0 + k * 1.0
        if time.time() < prossima:
            time.sleep(prossima - time.time())
        im, _png, perche = G4.foto_ridotta(s.g, 0.5)
        t = time.time() - t0
        if im is None:
            print("   ⚠ foto %d: %s" % (k, perche), flush=True)
            time.sleep(0.5)
            continue
        quadri.append((t, G4.ritaglia(im, box)))
        if o.evidenze and (k % salva_ogni == 0):
            p = os.path.join(o.evidenze, "f013-%s-%03d.jpg" % (nome, k))
            im.save(p, quality=70)
            salvate.append(p)
        k += 1
    if o.evidenze and quadri:
        # tutti i ritagli, in una striscia: si vede a occhio se cammina
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
            raise S.Bloccata("il video non si genera nella scatola: " + m)
        segno = s.segno_registro()
        c, t = accendi_video(s)
        if c != 0:
            raise S.Bloccata("ffplay non parte nella sessione: " + t[-200:])
        time.sleep(4)
        # la finestra del video, per differenza
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
            _c, log = s.come_utente("tail -5 /home/%s/.c15-SDL_VIDEODRIVERwayland.log "
                                    "/home/%s/.c15-*.log 2>/dev/null" % (s.chi, s.chi), 20)
            _c, vivo = segnale(s, "0")
            ev.append(s.salva_testo("ffplay-f013.txt", log))
            if "morto" in vivo:
                raise S.Bloccata("ffplay e' morto nella sessione: " + log[-300:])
            E.metti("F-013", S.FAIL, "ffplay gira nella sessione ma nella tela non si vede "
                    "un video che si muove: " + desc, atteso="video visibile che cammina",
                    osservato=desc, evidenze=ev + [s.salva_console()])
            return
        print("   video trovato: %s" % desc, flush=True)
        # il gesto: un clic vero fuori dalla finestra del video
        note = []
        stato, conti = G4.aspetta_contesto(s.g, 20)
        note.append("contesto audio «%s»" % stato)
        fx, fy = fuori_dal_video(box, prime[-1])
        note.append(G4.clic_vero(s, fx, fy))
        time.sleep(1.5)
        stato2, _ = G4.aspetta_contesto(s.g, 5)
        note.append("dopo il clic «%s»" % stato2)

        # A — il SUONO, ascoltato senza fotografare: `[M]` 24 set, la foto 4K di
        #     Firefox ferma il thread principale della pagina, che e' lo stesso
        #     che programma l'audio (cuscino 250 ms) ⇒ i buchi li faceva il banco.
        ta = G4.ora_pagina(s.g)
        time.sleep(o.ascolto_s)
        r = G4.leggi_orecchio(s.g, ta) or {}
        es, ds, ns = G4.giudica_suono(r.get("campioni") or [], TONO_HZ, min_frazione=0.95,
                                      max_buco_s=1.0, min_campioni=int(o.ascolto_s * 3))
        # B — l'IMMAGINE, una foto al secondo; il suono di questa finestra e' solo
        #     diagnostica (sente anche il prezzo delle foto)
        tb = G4.ora_pagina(s.g)
        quadri, salvate = guarda(s, o, box, o.video_s, "sano")
        rb = G4.leggi_orecchio(s.g, tb) or {}
        ev += salvate + [G4.salva_json(o, "f013-orecchio-sano.json", r),
                         G4.salva_json(o, "f013-orecchio-durante-le-foto.json", rb)]
        ei, di, ni = G4.giudica_immagine(quadri)
        esb, dsb, nsb = G4.giudica_suono(rb.get("campioni") or [], TONO_HZ, min_frazione=0.95,
                                         max_buco_s=1.0, min_campioni=10)
        note.append("suono DURANTE le foto (diagnostica, non giudica): %s %s" % (esb, dsb))
        ev += [s.salva_testo("server-f013.txt", s.registro_da(segno) if segno else []),
               s.salva_console()]
        atteso = ("suono: per %.0f s tono 660 Hz udibile >=95%%, buco <=1 s; poi immagine per "
                  "%.0f s che cammina (>=90%% foto diverse, blocco <=4 s, quadri senza mosaico)"
                  % (o.ascolto_s, o.video_s))
        oss = "%s · IMMAGINE %s · SUONO %s" % ("; ".join(note), di, ds)
        num = {"immagine": ni, "suono": ns, "suono_durante_foto": nsb, "finestra": desc}
        if "BLOCKED" in (ei, es) and "FAIL" not in (ei, es):
            E.metti("F-013", S.BLOCKED, "non ho potuto guardare: immagine «%s» · suono «%s»"
                    % (di, ds), atteso=atteso, osservato=oss, evidenze=ev, numeri=num)
        elif ei == "PASS" and es == "PASS":
            E.metti("F-013", S.PASS, "video continuo e suono presente: %s · %s" % (di, ds),
                    atteso=atteso, osservato=oss, evidenze=ev, numeri=num)
        else:
            male = []
            if ei != "PASS":
                male.append("immagine: " + di)
            if es != "PASS":
                male.append("suono: " + ds)
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
                E.guasto("F-013", None, "lettore fermo: immagine %s «%s» · suono %s «%s»"
                         % (eig, dig, esg, dsg), evidenze=evg)
            else:
                E.guasto("F-013", eig == "FAIL" and esg == "FAIL",
                         "lettore fermato (SIGSTOP, %s): immagine ⇒ %s «%s» · suono ⇒ %s «%s»"
                         % (v.strip()[-10:], eig, dig, esg, dsg), evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra))
