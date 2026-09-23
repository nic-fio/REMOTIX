#!/usr/bin/env python3
"""stacca-riattacca — dieci distacchi e altrettanti ritorni, ⭐ ogni volta con
la finestra di una MISURA DIVERSA.

⛔ IL DIFETTO, ed e' di stamattina: 22 settembre 2026, dopo un riavvio del
   server la sessione Plasma sopravviveva alla misura vecchia (2544×926), il
   client rientrava dichiarando 2560×962, KWin `--virtual` non ridimensiona e
   §6.2 vieta di spedire un fotogramma di misura diversa ⇒ **da li' non partiva
   piu' niente**, schermo nero per sempre.  Curato in `0b84a5b`: finche' non e'
   uscito nessun fotogramma il server ADOTTA la misura del palco.

⭐ QUI NON SI RIAVVIA IL SERVER (quello e' `riavvio-del-server`): si prova
   l'altro lato della stessa regola, cioe' §7.6 — il distacco NON e' l'uscita,
   la sessione grafica resta in piedi con la SUA misura, e chi torna con una
   finestra diversa deve rivedere lo schermo lo stesso.

⚠ Il giudizio e' sul RITORNO DELL'IMMAGINE, non sulla misura concessa: che la
  tela resti quella del palco e' il modo in cui il prodotto risolve, e potrebbe
  cambiare; che l'utente riveda lo schermo, no.
"""
import time

import _comune as C

NOME = "stacca-riattacca"
DURATA_S = 10 * 40
TETTO_S = 20 * 60

# ⚠ Dieci misure DIVERSE, e nessuna uguale alla precedente: il difetto nasce
#   dalla differenza, non dal numero.  ⛔ E nessuna piu' grande dello schermo
#   del tablet (1920×1080), o la finestra la decide il gestore e non io.
MISURE = [(1400, 1000), (1280, 720), (1600, 900), (1024, 768), (1280, 1000),
          (1500, 860), (1100, 820), (1680, 940), (1200, 760), (1440, 980)]


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    giri = int(o.get("giri", 10))
    tetto_immagine_s = float(o.get("tetto_immagine_s", 25.0))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    chi = o.get("chi") or C.nome_inquilino("sr")
    misure = (o.get("misure") or MISURE)[:giri]
    # ⛔ NIENTE OCCHIO QUI, e si dice perche': il giro e' fatto di dieci
    #   distacchi, e fra un rientro e l'altro si aspetta solo che il contatore
    #   riparta — spesso un secondo o due.  ⚠ L'occhio vuole che la scena
    #   SALGA (25 s) prima di contare qualcosa: qui non guarderebbe mai niente,
    #   e le fotografie subito dopo un rientro sono la finestra che si riapre,
    #   non il prodotto (`[M]` 10,8 % di celle guaste su una ripresa sana).
    #   ⇒ Si aggancia il giorno che ci sara' il ferro per misurare quanto dura
    #     davvero la risalita dopo un rientro.
    b = C.Banco(nucleo, desktop, marca, chi, misura=misure[0],
                dove=o.get("dove"), occhio=False)
    fatti = []
    try:
        cod, perche = b.apparecchia("normale")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())
        time.sleep(8)
        prima = b.numeri().get("consegnati", 0) or 0

        for giro, misura in enumerate(misure, 1):
            if tetto.scaduto():
                break
            cod, perche = b.rientra(misura=misura, scena_quale="normale")
            if cod != C.VERDE:
                return C.esito(NOME, desktop, marca, cod,
                               "al giro %d, con la finestra %dx%d, non sono "
                               "rientrato: %s" % (giro, misura[0], misura[1], perche),
                               misure={"giri": fatti}, secondi=tetto.passati())
            # ⭐ La domanda vera: l'immagine RIPARTE?  Si aspetta che il
            #   contatore dei consegnati salga, non che la pagina dica di essere
            #   entrata: il difetto di stamattina entrava benissimo e non
            #   dipingeva niente.
            fine = time.time() + tetto_immagine_s
            adesso = prima
            while time.time() < fine:
                adesso = b.numeri().get("consegnati", 0) or 0
                if adesso > prima:
                    break
                time.sleep(1.0)
            nuovi = adesso - prima
            fatti.append({"giro": giro, "finestra": list(misura), "nuovi": nuovi,
                          "secondi": round(tetto.passati(), 1)})
            if nuovi <= 0:
                srv = b.server()
                c, t = C.dentro(nucleo, desktop,
                                "grep -a '\\[%s\\]' %s | grep -c 'non e. alla tela "
                                "in vigore'" % (chi, C.REGISTRO), 90)
                return C.rosso(NOME, desktop, marca,
                               "al giro %d, rientrato con la finestra %dx%d, in "
                               "%.0f s non e' arrivato NESSUN fotogramma "
                               "(righe «il palco non e' alla tela in vigore»: %s)"
                               % (giro, misura[0], misura[1], tetto_immagine_s,
                                  (t or "?").strip().splitlines()[-1:]),
                               misure={"giri": fatti, "server": srv},
                               secondi=tetto.passati())
            prima = adesso

        srv = b.server()
        C.salva(o.get("dove"), "giri-stacca-riattacca.json", fatti)
        return C.verde(NOME, desktop, marca,
                       "%d distacchi e ritorni con finestre sempre diverse: "
                       "l'immagine e' ripartita ogni volta (al piu' %.0f s), "
                       "nessuna linea morta"
                       % (len(fatti), tetto_immagine_s),
                       misure={"giri": fatti, "server": srv},
                       regole={"giri": giri, "tetto_immagine_s": tetto_immagine_s},
                       secondi=tetto.passati())
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], misure={"giri": fatti},
                        secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
