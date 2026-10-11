#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f001 — F-001 LOGIN AND SESSION CREATION · F-002 FIRST IMAGE

    python3 15-f001-accesso-e-prima-immagine.py --box kde --browser chrome [--fault]

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

FUNCTIONS = ("F-001", "F-002")


def uniform_png(w, h, rgb=(0, 0, 0)):
    line = b"\x00" + bytes(rgb) * w
    data = zlib.compress(line * h, 9)

    def piece(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n" + piece(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + piece(b"IDAT", data) + piece(b"IEND", b""))


def certify():
    nero = uniform_png(64, 48)
    deg, desc = S.VERI.judge_pixel(nero)
    ok = deg is True
    print("%s judge: a black canvas is degenerate (%s)" % ("⭐" if ok else "⛔", desc))
    return 0 if ok else 1


def body(o, E):
    with S.Session(o, "001", E) as s:
        sign = s.log_mark()
        ok, m = s.pr.do_open()
        if not ok:
            raise S.Blocked("the page does not open: " + m)
        e, m, st = s.pr.enter(s.password)
        server = s.log_from(sign) if sign is not None else []
        ev = [s.save_text("server-f001.txt", server)]
        if e != S.GREEN:
            E.put("F-001", S.FAIL, "right user and password, and it does not get in: " + m,
                    expected="«Admitted» and session created", observed=m, evidence=ev)
            raise S.Blocked("without login there is no first image to look at")
        E.put("F-001", S.PASS, m, expected="«Admitted» and session created",
                observed="%s · %d server lines for %s" % (m, len(server), s.chi),
                evidence=ev)

        e, m, st = s.pr.first_frame()
        e, m = S.C20V.desktop_dark_but_alive(e, m, st)
        png, dove = s.photo("prima-immagine")
        ev = [dove] if png and dove else []
        if e == S.GREEN and png:
            deg, desc = S.VERI.judge_pixel(png)
            if deg:
                # ⚠ the same tolerance as the first frame (12-c20-veri
                #   desktop_dark_but_alive): the XFCE background in the box is
                #   BLACK, and in 4K panel and icons are 2 % ⇒ «dominant 98 %
                #   black» but 72 distinct colours.  `[M]` round 1, 25 Sep: BENCH
                #   FAIL on xfce (D-010, class C).
                e, m = S.C20V.desktop_dark_but_alive(
                    S.RED, "the full-resolution photo is degenerate: " + desc, st)
        E.put("F-002", e, m, expected="desktop drawn, not degenerate, within %d s" % o.cap_s,
                observed=m, evidence=ev + [s.save_console()])

        if o.fault:
            # F-002: the judge on a black canvas of the same size
            if png:
                import struct as _s
                w, h = _s.unpack(">II", png[16:24])
                deg, desc = S.VERI.judge_pixel(uniform_png(min(w, 640), min(h, 360)))
                E.fault("F-002", bool(deg), "black canvas ⇒ the judge says «%s»" % desc)
            else:
                E.fault("F-002", None, "no real photo to start from")
            # F-001: the address of a server that is not there (⛔ NOT the wrong
            #   password: three failed attempts ban the bench's address
            #   for twelve hours, and would stop the whole suite)
            s.pr.url = s.o.url.rsplit(":", 1)[0] + ":8599/"
            ok, m = s.pr.do_open()
            if ok:
                e, m, st = s.pr.enter(s.password)
                ok = e == S.GREEN
            E.fault("F-001", not ok, "nonexistent server ⇒ %s"
                     % ("no login: " + m if not ok else "ADMITTED anyway"))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
