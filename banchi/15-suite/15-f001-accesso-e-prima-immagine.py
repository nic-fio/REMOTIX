#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f001 — F-001 ACCESSO E CREAZIONE DELLA SESSIONE · F-002 PRIMA IMMAGINE

    python3 15-f001-accesso-e-prima-immagine.py --scatola kde --browser chrome [--guasto]

F-001  atteso: la pagina si apre, il modulo c'e' ed e' visibile, utente e parola
       giusti ⇒ «Ammesso», e il server dichiara la sessione dell'inquilino.
F-002  atteso: entro il tetto la tela mostra il DESKTOP (fotografia non degenere:
       non tutta nera, non tutta di un colore), a piena risoluzione.

GUASTO F-001: la pagina puntata a un server che non c'e' ⇒ la prova deve NON
       vedere l'ammissione.  ⛔ Non la parola sbagliata: il ban (3 tentativi, 12 h)
       colpirebbe l'indirizzo del banco e fermerebbe tutta la suite.
GUASTO F-002: il giudice dei pixel riceve una tela NERA della stessa misura della
       foto vera ⇒ deve dirla degenere.
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
    print("%s giudice: una tela nera e' degenere (%s)" % ("⭐" if ok else "⛔", desc))
    return 0 if ok else 1


def corpo(o, E):
    with S.Sessione(o, "001", E) as s:
        segno = s.segno_registro()
        ok, m = s.pr.apri()
        if not ok:
            raise S.Bloccata("la pagina non si apre: " + m)
        e, m, st = s.pr.entra(s.parola)
        server = s.registro_da(segno) if segno is not None else []
        ev = [s.salva_testo("server-f001.txt", server)]
        if e != S.VERDE:
            E.metti("F-001", S.FAIL, "utente e parola giusti, e non entra: " + m,
                    atteso="«Ammesso» e sessione creata", osservato=m, evidenze=ev)
            raise S.Bloccata("senza accesso non c'e' prima immagine da guardare")
        E.metti("F-001", S.PASS, m, atteso="«Ammesso» e sessione creata",
                osservato="%s · %d righe del server per %s" % (m, len(server), s.chi),
                evidenze=ev)

        e, m, st = s.pr.primo_fotogramma()
        e, m = S.C20V.desktop_scuro_ma_vivo(e, m, st)
        png, dove = s.foto("prima-immagine")
        ev = [dove] if png and dove else []
        if e == S.VERDE and png:
            deg, desc = S.VERI.giudica_pixel(png)
            if deg:
                # ⚠ la stessa tolleranza del primo fotogramma (12-c20-veri
                #   desktop_scuro_ma_vivo): lo sfondo di XFCE nella scatola e'
                #   NERO, e in 4K pannello e icone sono il 2 % ⇒ «dominante 98 %
                #   nero» ma 72 colori distinti.  `[M]` giro 1, 25 set: FAIL del
                #   BANCO su xfce (D-010, classe C).
                e, m = S.C20V.desktop_scuro_ma_vivo(
                    S.ROSSO, "la foto a piena risoluzione e' degenere: " + desc, st)
        E.metti("F-002", e, m, atteso="desktop disegnato, non degenere, entro %d s" % o.tetto_s,
                osservato=m, evidenze=ev + [s.salva_console()])

        if o.guasto:
            # F-002: il giudice su una tela nera della stessa misura
            if png:
                import struct as _s
                w, h = _s.unpack(">II", png[16:24])
                deg, desc = S.VERI.giudica_pixel(png_uniforme(min(w, 640), min(h, 360)))
                E.guasto("F-002", bool(deg), "tela nera ⇒ il giudice dice «%s»" % desc)
            else:
                E.guasto("F-002", None, "nessuna foto vera da cui partire")
            # F-001: l'indirizzo di un server che non c'e' (⛔ NON la parola
            #   sbagliata: tre tentativi falliti bannano l'indirizzo del banco
            #   per dodici ore, e fermerebbero tutta la suite)
            s.pr.url = s.o.url.rsplit(":", 1)[0] + ":8599/"
            ok, m = s.pr.apri()
            if ok:
                e, m, st = s.pr.entra(s.parola)
                ok = e == S.VERDE
            E.guasto("F-001", not ok, "server inesistente ⇒ %s"
                     % ("nessun accesso: " + m if not ok else "AMMESSO lo stesso"))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
