#!/usr/bin/env python3
"""07-b45-arbitro.py — l'ARBITRO ESTERNO degli appunti, e non e' roba nostra.

    python3 07-b45-arbitro.py copia  <testo>   mette il testo negli appunti e resta a servirlo
    python3 07-b45-arbitro.py leggi            stampa quel che c'e' negli appunti
    python3 07-b45-arbitro.py svuota           toglie quel che c'e'

Gira DENTRO la sessione grafica, come un'applicazione qualunque.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ PERCHE' GTK E NON `xclip` — e la ragione e' una misura, non una preferenza

`fasi/07-audio-e-appunti.md` §2.4 prometteva `xclip`: «su GNOME la sponda X11 di
Mutter e' incondizionata nei due versi» (`STUDI.md` §gnome §10 `[R]`).

⛔ **E' vero del codice di Mutter e falso delle nostre sessioni.**  `[M]` 17
   agosto 2026: il compositore gira come `gnome-shell --headless --no-x11`, cioe'
   **XWayland non parte affatto**.  ⚠ I socket in `/tmp/.X11-unix` sono avanzi di
   due giorni prima: un banco che li avesse presi per buoni avrebbe misurato una
   sessione morta e chiamato rosso il prodotto.

⭐ E l'arbitro giusto e' **migliore** di quello promesso: le applicazioni del
   desktop non parlano X11 — sono client Wayland e prendono la clipboard con
   `wl_data_device`.  ⇒ Questo programma percorre **la stessa strada di
   un'applicazione vera**, mentre `xclip` avrebbe provato una sponda che i nostri
   utenti non hanno.

⚠ `wl-copy` c'e' sulla macchina ed e' stato scartato: parla
  `zwlr_data_control_manager_v1`, che e' di wlroots e su GNOME **non esiste**
  (`LEZIONI.md` §3, domanda 14).  Un arbitro che fallisce sempre darebbe rosso a
  ogni giro, e il rosso sarebbe suo.

═══════════════════════════════════════════════════════════════════════════════
⛔ E QUESTO PROGRAMMA NON E' NOSTRO PER LA PARTE CHE CONTA

Le righe qui sotto chiamano GDK e non fanno nessuna scelta di protocollo: chi
parla con Mutter e' **GTK**, che non ha mai sentito parlare di RCP.  ⚠ E' quel
che `PIANO.md` §0.4 chiede — non far parlare fra loro due pezzi nostri, che
«non conferma niente».

═══════════════════════════════════════════════════════════════════════════════
⛔ «COPIA» RESTA VIVO, E NON E' UNA SVISTA

Su Wayland chi copia **resta il proprietario della selezione**: quando qualcun
altro incolla, il compositore chiede il contenuto **a lui**.  ⇒ Un programma che
copiasse e uscisse porterebbe via gli appunti nello stesso istante, e il banco
misurerebbe «non c'e' niente da incollare» su un prodotto sano.

⚠ E' l'altra faccia della riga di `STUDI.md` §gnome §10: «la clipboard non
  sopravvive alla morte di chi ha copiato — ⛔ su GNOME **sopravvive**, Mutter ha
  un clipboard manager interno».  Il manager pero' tiene **un solo tipo MIME** e
  interviene alla morte del proprietario: appoggiarcisi vorrebbe dire misurare
  LUI invece della nostra catena.
"""
import sys

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

# ⛔ Il tetto e' quello di `RCP.md` §5.4, e vale anche per l'arbitro: se un
#    giorno il banco provasse un testo piu' grande, questo programma NON deve
#    essere il pezzo che lo tronca in silenzio.
TETTO = 1000000


def appunti():
    """⛔ IL DISPLAY SI APRE, NON SI CHIEDE — e la differenza e' costata un giro.

    `[M]` 17 agosto 2026: `Gdk.Display.get_default()` torna **`None`** in un
    programma che non ha chiamato `Gtk.init()`, ⚠ e il messaggio che ne veniva
    era «nessun display Wayland: la sessione grafica non c'e'» — cioe' l'arbitro
    accusava la SESSIONE di non esistere mentre la sessione era viva e il difetto
    era suo.  ⛔ E' `CODER.md` §3.11 alla lettera: quando codice letto e misura
    si contraddicono, il sospetto va **prima sulla misura**.

    ⛔ E LA SECONDA STRADA NON ERA `Gdk.Display.open(None)`: GTK 4 risponde
       **`gdk_display_open() was called before gtk_init()`** e ABORTA (codice
       133).  ⚠ Due tentativi, due modi diversi di non funzionare, e nessuno dei
       due diceva la cosa giusta: e' `Gtk.init_check()` che apre il display
       leggendo l'ambiente e **restituisce un booleano** invece di morire.

    ⭐ `init_check` e non `init`: quest'ultima esce dal processo se il display
       non c'e', e allora «la sessione non c'e'» e «l'arbitro e' rotto»
       tornerebbero ad avere la stessa faccia — che e' il difetto che i due
       codici d'uscita (3 e 1) esistono per separare.
    """
    if not Gtk.init_check():
        print("⛔ GTK non apre nessun display: WAYLAND_DISPLAY="
              + str(__import__("os").environ.get("WAYLAND_DISPLAY", "(vuota)")),
              file=sys.stderr)
        sys.exit(3)
    d = Gdk.Display.get_default()
    if d is None:
        # ⛔ «Non ho potuto guardare» ha un codice SUO (3), diverso da «gli
        #    appunti non funzionano» (1).  `LEZIONI.md` §1.9 regola 1.
        print("⛔ nessun display Wayland aperto: WAYLAND_DISPLAY="
              + str(__import__("os").environ.get("WAYLAND_DISPLAY", "(vuota)")),
              file=sys.stderr)
        sys.exit(3)
    return d.get_clipboard()


def finestra():
    """⛔⛔ UNA FINESTRA SERVE, e non e' un ornamento — `[M]` 17 agosto 2026.

    Un client Wayland **senza finestra** non puo' possedere la selezione: per
    `wl_data_device.set_selection` serve il *serial* di un evento d'ingresso, e
    a un client che non ha nessuna superficie non arriva nessun evento.
    ⇒ `clipboard.set()` **riesce localmente e non arriva mai al compositore**, e
    chi legge da un altro processo trova `Cannot read from empty clipboard`.

    ⚠ E il primo sospetto era un altro — «il seat non ha tastiera», che e' quel
      che dice `wl-copy` — ma con un client REMOTIX attaccato la tastiera
      virtuale c'e' (`input.c` la crea con libei) e la lettura falliva lo
      stesso.  ⛔ Due cause plausibili per lo stesso sintomo, e solo la seconda
      era quella vera: `CODER.md` §3.11.

    ⭐ E questo NON allontana l'arbitro dalla scena vera: le applicazioni che
       copiano hanno tutte una finestra.  Un arbitro senza finestra era LUI
       l'anomalia.
    """
    f = Gtk.Window()
    f.set_default_size(200, 80)
    f.present()
    # ⚠ Si lascia girare il ciclo qualche battuta: la finestra deve arrivare al
    #   compositore e prendere il fuoco PRIMA che si tocchi la selezione.
    #   ⛔ Un `set()` chiamato prima riuscirebbe di nuovo solo in locale.
    ciclo = GLib.MainLoop()
    GLib.timeout_add(700, lambda: (ciclo.quit(), False)[1])
    ciclo.run()
    return f


def copia(testo):
    """Mette il testo negli appunti e RESTA VIVO a servirli — vedi la testata."""
    if len(testo.encode("utf-8")) > TETTO:
        print(f"⛔ {len(testo.encode('utf-8'))} byte: oltre il tetto di §5.4 "
              f"({TETTO}).  NON tronco", file=sys.stderr)
        sys.exit(2)
    c = appunti()
    finestra()
    c.set(testo)
    # ⭐ Il marcatore per l'altro lato: si stampa e si SCARICA, perche' chi
    #    aspetta legge lo stdout — e Python bufferizza quando e' rediretto.
    #    E' la trappola pagata da B3 il 10 agosto 2026: una riga stampata e' una
    #    speranza sul momento in cui qualcuno la vedra'.
    print("COPIATO", flush=True)
    GLib.MainLoop().run()


def leggi():
    """Legge il testo degli appunti.  ⛔ Con un fondo di tempo SUO: se nessuno
    risponde, «non c'e' niente» e «nessuno ha risposto» sono due fatti diversi.
    """
    c = appunti()
    # ⛔ La finestra serve anche a LEGGERE: su Wayland la selezione si offre al
    #    client che ha il fuoco, e senza superficie non c'e' fuoco (vedi
    #    `finestra()`).
    finestra()
    ciclo = GLib.MainLoop()
    esito = {"testo": None, "sbaglio": None}

    def fatto(sorgente, risultato):
        try:
            esito["testo"] = sorgente.read_text_finish(risultato)
        except GLib.Error as e:
            esito["sbaglio"] = e.message
        ciclo.quit()

    c.read_text_async(None, fatto)
    # ⛔ Cinque secondi e poi si esce DICENDO che si e' usciti per tempo: un
    #    programma che restasse appeso farebbe restare appeso il banco, e il
    #    sintomo sarebbe «il banco non finisce» invece di «gli appunti tacciono».
    GLib.timeout_add_seconds(5, lambda: (ciclo.quit(), False)[1])
    ciclo.run()

    if esito["sbaglio"] is not None:
        print(f"⛔ lettura fallita: {esito['sbaglio']}", file=sys.stderr)
        sys.exit(1)
    if esito["testo"] is None:
        # ⚠ Appunti VUOTI: e' un fatto lecito, e ha un codice suo (4) perche' il
        #   banco lo distingua da «ho letto e c'era altro».
        sys.exit(4)
    sys.stdout.write(esito["testo"])
    sys.stdout.flush()


def svuota():
    """⛔ E su Wayland «svuotare» vuol dire LASCIARE la selezione, non metterci
    la stringa vuota: una stringa vuota e' un contenuto, e chi legge trova un
    proprietario che offre zero byte — che non e' la stessa cosa di «non c'e'
    nessun proprietario».
    """
    c = appunti()
    finestra()
    c.set_content(None)
    print("SVUOTATO", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        sys.exit(2)
    azione = sys.argv[1]
    if azione == "copia":
        if len(sys.argv) < 3:
            print("⛔ «copia» vuole il testo", file=sys.stderr)
            sys.exit(2)
        copia(sys.argv[2])
    elif azione == "leggi":
        leggi()
    elif azione == "svuota":
        svuota()
    else:
        print(f"⛔ azione ignota: {azione}", file=sys.stderr)
        sys.exit(2)
