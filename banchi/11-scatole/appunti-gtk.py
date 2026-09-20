#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
appunti-gtk — L'ARBITRO DEGLI APPUNTI CHE FUNZIONA ANCHE SU GNOME
===========================================================================

    python3 appunti-gtk.py copia «testo» [secondi]   mette il testo e RESTA
    python3 appunti-gtk.py incolla                   stampa quel che c'e'

⛔ PERCHE' ESISTE — `[M]` 19-20 settembre 2026, fase 12.  `wl-clipboard`
   (`wl-copy`, `wl-paste`) parla `zwlr_data_control_manager_v1`: KWin ce l'ha,
   ⛔ **Mutter no**.  Su GNOME i due comandi restano APPESI fino al `timeout`
   (uscita 124) — aspettano un fuoco che una sessione senza schermo non da' —
   e la maglia C17 degli appunti non poteva guardare (esito 3).

⭐ LA STRADA GIUSTA E' QUELLA DELLE APPLICAZIONI: `wl_data_device`, cioe' la
   clipboard che usano Firefox, il terminale e tutto il resto.  Qui si arriva
   con GTK (`python3-gi`), che **non e' nostro** e non ha mai sentito parlare
   di RCP: e' un arbitro esterno, come vuole il banco.
⛔ E serve una FINESTRA VERA, presentata e col fuoco: la clipboard di Wayland
   si concede a chi ha il fuoco, e una finestra che non si mostra non ce l'ha.

⚠ Vale su GNOME **e** su KDE: dove c'e' `wl-clipboard` si puo' continuare a
  usare quello, ma la differenza fra i due desktop smette di essere un muro.
"""
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402


def finestra(app):
    """Una finestra vera, piccola e presentata: senza fuoco niente clipboard."""
    f = Gtk.ApplicationWindow(application=app, title="REMOTIX appunti")
    f.set_default_size(160, 60)
    f.set_child(Gtk.Label(label="appunti"))
    f.present()
    return f


def al_fuoco(f, fatto):
    """⭐⭐ SI ASPETTA IL FUOCO, E NON SI FA NIENTE PRIMA — 20 set 2026.

    ⛔ `[M]` Su GNOME la clipboard si concede a chi ha la finestra ATTIVA, e in
       una sessione remota nessuno clicca: la finestra c'e' e il fuoco no, quindi
       copiare e incollare falliscono in silenzio.  ⇒ Il banco il clic lo manda
       davvero, passando da REMOTIX (come C4 col tasto), e qui si aspetta che
       arrivi: `is-active` e' Mutter che dice «adesso sei tu».
    ⚠ Su KWin il fuoco alla sola finestra arriva da se': la stessa riga vale per
      tutt'e due i desktop.
    """
    if f.is_active():
        fatto()
        return
    f.connect("notify::is-active", lambda *_: f.is_active() and fatto())


def copia(testo, secondi):
    """Mette il testo negli appunti QUANDO ha il fuoco, e RESTA vivo a servirlo.

    ⛔ Non si esce subito: su Wayland la selezione la serve il processo che la
       offre — chi esce se la porta via, ed e' il difetto che fa dire «copiato»
       a un desktop che non ha piu' niente.
    """
    def avviato(app):
        f = finestra(app)

        def adesso():
            Gdk.Display.get_default().get_clipboard().set(testo)
            print("copiato A FUOCO: %d caratteri, resto vivo %g s"
                  % (len(testo), secondi), flush=True)

        print("finestra aperta, aspetto il fuoco", flush=True)
        al_fuoco(f, adesso)
        GLib.timeout_add_seconds(int(secondi), lambda: (app.quit(), False)[1])

    app = Gtk.Application(application_id="org.remotix.appunti.copia")
    app.connect("activate", avviato)
    return app.run([])


def incolla():
    """Legge gli appunti della sessione e li stampa (niente = riga vuota)."""
    esito = {"testo": ""}

    def avviato(app):
        f = finestra(app)

        def letto(clip, ris):
            try:
                esito["testo"] = clip.read_text_finish(ris) or ""
            except GLib.Error as e:
                print("⛔ non ho potuto leggere: %s" % e.message, file=sys.stderr)
            app.quit()

        def adesso():
            Gdk.Display.get_default().get_clipboard().read_text_async(None, letto)

        print("finestra aperta, aspetto il fuoco", file=sys.stderr, flush=True)
        al_fuoco(f, adesso)
        GLib.timeout_add_seconds(25, lambda: (app.quit(), False)[1])

    app = Gtk.Application(application_id="org.remotix.appunti.incolla")
    app.connect("activate", avviato)
    app.run([])
    print(esito["testo"], end="")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "copia":
        sys.exit(copia(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 60))
    if len(sys.argv) >= 2 and sys.argv[1] == "incolla":
        sys.exit(incolla())
    print(__doc__)
    sys.exit(2)
