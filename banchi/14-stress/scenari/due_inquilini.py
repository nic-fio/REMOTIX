#!/usr/bin/env python3
"""due-inquilini — due utenti insieme sulla stessa scatola: uno pesante e uno
normale, e nessuno dei due si deve fermare.

⭐ PERCHE' CONTA: il prodotto serve piu' sessioni con processi separati (I2, un
   figlio per utente).  Un difetto che si vede solo con due e' proprio quello
   che una prova a un utente solo non trova mai: la coda di uscita condivisa,
   il budget, l'attribuzione delle righe nel registro.

⛔ E IL SECONDO GIUDICE, che e' quello di C9: il registro deve dire DI CHI
   parla.  Se le righe dei due si mescolano, una diagnosi futura e' gia' persa.

⚠ SCELTA DICHIARATA: il pesante e' un BROWSER VERO sul tablet, il normale e' il
  cliente in Python DENTRO la scatola (`01-b3-cliente.py`).  ⛔ Due browser veri
  insieme su questo tablet (N100, 7,5 GB) falserebbero i numeri di tutt'e due, e
  la domanda di questo scenario e' sul SERVER, non sul tablet.  ⇒ Il cliente in
  Python basta per essere un secondo inquilino vero dal lato del prodotto.
"""
import time

import _comune as C

NOME = "due-inquilini"
DURATA_S = 180
TETTO_S = 12 * 60


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    durata = float(o.get("durata_s", DURATA_S))
    fermo_massimo = float(o.get("fermo_massimo_s", 25.0))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    pesante = o.get("chi") or C.nome_inquilino("d1")
    normale = (o.get("chi_secondo") or C.nome_inquilino("d2"))
    parola2 = "stress2026"
    b = C.Banco(nucleo, desktop, marca, pesante, misura=o.get("misura", (1400, 1000)),
                dove=o.get("dove"))
    secondo_creato = False
    try:
        cod, perche = b.apparecchia("pesante")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())

        fatto, perche = C.crea_inquilino(nucleo, desktop, normale, parola2)
        if not fatto:
            return C.non_so(NOME, desktop, marca,
                            "non ho potuto creare il secondo inquilino: %s" % perche,
                            secondi=tetto.passati())
        secondo_creato = True
        # ⛔ `setsid` e stdin chiuso: un cliente in sfondo senza di loro finisce
        #    in stato T al primo tocco del terminale (lezione del 22 set 2026).
        C.dentro(nucleo, desktop,
                 "setsid python3 /opt/remotix/01-b3-cliente.py --indirizzo 127.0.0.1 "
                 "--porta %d --utente %s --parola %s --resta %d "
                 "</dev/null >/tmp/due-%s.log 2>&1 & echo lanciato"
                 % (C.PORTE[desktop], normale, parola2, int(durata) + 60, normale), 90)

        for _ in range(60):
            if C.compositore_vivo(nucleo, desktop, normale):
                break
            time.sleep(1.0)
        else:
            return C.non_so(NOME, desktop, marca,
                            "il secondo inquilino non ha aperto una sessione "
                            "grafica: non sono in due", secondi=tetto.passati())

        storia = C.guarda_per(nucleo, b.browser, min(durata, tetto.resta() - 90),
                              passo=5.0, tetto=tetto)
        sempre, fermo = C.sempre_in_salita(storia, "consegnati", fermo_massimo)
        cresciuta = C.cresciuti(storia[0], storia[-1])
        srv_pesante = C.dal_server(nucleo, desktop, b.segno, pesante)
        srv_normale = C.dal_server(nucleo, desktop, b.segno, normale)

        # ⭐ Il giudice di C9: nessuna riga dell'uno nomina l'altro.
        c, t = C.dentro(nucleo, desktop,
                        "grep -a '\\[%s\\]' %s | grep -c '%s'"
                        % (pesante, C.REGISTRO, normale), 90)
        try:
            mescolate = int((t or "0").strip().splitlines()[-1])
        except (ValueError, IndexError):
            mescolate = -1

        vivo_il_normale = C.compositore_vivo(nucleo, desktop, normale)
        misure = {"pesante": {"consegnati": storia[-1].get("consegnati"),
                              "cresciuti": cresciuta.get("consegnati"),
                              "fermo_piu_lungo_s": fermo, "server": srv_pesante},
                  "normale": {"server": srv_normale, "sessione_viva": vivo_il_normale},
                  "righe_mescolate": mescolate}
        regole = {"fermo_massimo_s": fermo_massimo, "durata_s": durata}
        C.salva(o.get("dove"), "storia-due.json", storia)

        guasti = []
        if not cresciuta.get("consegnati"):
            guasti.append("il pesante non ha ricevuto nessun fotogramma")
        elif not sempre:
            guasti.append("il pesante si e' fermato per %.1f s" % fermo)
        if not srv_normale.get("spediti"):
            guasti.append("al normale non e' partito nessun fotogramma")
        if srv_pesante.get("linee_morte") or srv_normale.get("linee_morte"):
            guasti.append("linea morta (pesante %s, normale %s)"
                          % (srv_pesante.get("linee_morte"),
                             srv_normale.get("linee_morte")))
        if mescolate > 0:
            guasti.append("%d righe del registro del pesante nominano il normale"
                          % mescolate)
        if not vivo_il_normale:
            guasti.append("la sessione del normale e' morta nel mezzo")

        # ⭐ Il PROTAGONISTA del giro e' il pesante: i suoi numeri vanno anche
        #   in vista sulla riga (`pagina`/`server`), cosi' la tabella del
        #   mattino non deve indovinare in quale ramo di `misure` stavano.
        in_vista = dict(pagina=storia[-1], server=srv_pesante)
        if guasti:
            return C.rosso(NOME, desktop, marca, "; ".join(guasti), misure=misure,
                           regole=regole, secondi=tetto.passati(),
                           guasti=guasti, **in_vista)
        return C.verde(NOME, desktop, marca,
                       "due inquilini insieme per %.0f s: il pesante ha ricevuto "
                       "%d fotogrammi senza fermarsi piu' di %.1f s, al normale ne "
                       "sono partiti %s, e il registro non mescola le righe"
                       % (durata, cresciuta.get("consegnati", 0), fermo,
                          srv_normale.get("spediti")),
                       misure=misure, regole=regole, secondi=tetto.passati(),
                       **in_vista)
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
        if secondo_creato:
            C.sgombera(nucleo, desktop, normale)
