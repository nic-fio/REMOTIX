#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f001 — F-001 LOGIN AND SESSION CREATION · F-002 FIRST IMAGE

    python3 15-f001-accesso-e-prima-immagine.py --scatola kde --browser chrome [--guasto]

F-001  expected: the page opens, the form is there and visible, right user and password
       ⇒ «Admitted», and the server declares the tenant's session.
F-002  expected: within the cap the canvas shows the DESKTOP (non-degenerate photo:
       not all black, not all one colour), at full resolution.

FAULT F-001: the page pointed at a server that is not there ⇒ the test must NOT
       see the admission.  ⛔ Not the wrong password: the ban (3 attempts, 12 h)
       would hit the bench's address and stop the whole suite.
FAULT F-002: the pixel judge receives a BLACK canvas of the same size as the
       real photo ⇒ it must call it degenerate.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-001", "F-002")


def png_uniforme(w, h, rgb=(0, 0, 0)):
    riga = b"\x00" + bytes(rgb) * w
    dati = zlib.compress(riga * h, 9)

    def pezzo(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n" + pezzo(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + pezzo(b"IDAT", dati) + pezzo(b"IEND", b""))


def certifica():
    nero = png_uniforme(64, 48)
    deg, desc = S.VERI.giudica_pixel(nero)
    ok = deg is True
    print("%s judge: a black canvas is degenerate (%s)" % ("⭐" if ok else "⛔", desc))
    return 0 if ok else 1


def corpo(o, E):
    with S.Sessione(o, "001", E) as s:
        segno = s.segno_registro()
        ok, m = s.pr.apri()
        if not ok:
            raise S.Bloccata("the page does not open: " + m)
        e, m, st = s.pr.entra(s.parola)
        server = s.registro_da(segno) if segno is not None else []
        ev = [s.salva_testo("server-f001.txt", server)]
        if e != S.VERDE:
            E.metti("F-001", S.FAIL, "right user and password, and it does not get in: " + m,
                    atteso="«Admitted» and session created", osservato=m, evidenze=ev)
            raise S.Bloccata("without login there is no first image to look at")
        E.metti("F-001", S.PASS, m, atteso="«Admitted» and session created",
                osservato="%s · %d server lines for %s" % (m, len(server), s.chi),
                evidenze=ev)

        e, m, st = s.pr.primo_fotogramma()
        e, m = S.C20V.desktop_scuro_ma_vivo(e, m, st)
        png, dove = s.foto("prima-immagine")
        ev = [dove] if png and dove else []
        if e == S.VERDE and png:
            deg, desc = S.VERI.giudica_pixel(png)
            if deg:
                # ⚠ the same tolerance as the first frame (12-c20-veri
                #   desktop_scuro_ma_vivo): the XFCE background in the box is
                #   BLACK, and in 4K panel and icons are 2 % ⇒ «dominant 98 %
                #   black» but 72 distinct colours.  `[M]` round 1, 25 Sep: BENCH
                #   FAIL on xfce (D-010, class C).
                e, m = S.C20V.desktop_scuro_ma_vivo(
                    S.ROSSO, "the full-resolution photo is degenerate: " + desc, st)
        E.metti("F-002", e, m, atteso="desktop drawn, not degenerate, within %d s" % o.tetto_s,
                osservato=m, evidenze=ev + [s.salva_console()])

        if o.guasto:
            # F-002: the judge on a black canvas of the same size
            if png:
                import struct as _s
                w, h = _s.unpack(">II", png[16:24])
                deg, desc = S.VERI.giudica_pixel(png_uniforme(min(w, 640), min(h, 360)))
                E.guasto("F-002", bool(deg), "black canvas ⇒ the judge says «%s»" % desc)
            else:
                E.guasto("F-002", None, "no real photo to start from")
            # F-001: the address of a server that is not there (⛔ NOT the wrong
            #   password: three failed attempts ban the bench's address
            #   for twelve hours, and would stop the whole suite)
            s.pr.url = s.o.url.rsplit(":", 1)[0] + ":8599/"
            ok, m = s.pr.apri()
            if ok:
                e, m, st = s.pr.entra(s.parola)
                ok = e == S.VERDE
            E.guasto("F-001", not ok, "nonexistent server ⇒ %s"
                     % ("no login: " + m if not ok else "ADMITTED anyway"))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
