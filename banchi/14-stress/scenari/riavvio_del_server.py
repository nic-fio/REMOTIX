#!/usr/bin/env python3
"""riavvio-del-server — il server si riavvia sotto una sessione viva, e chi torna
deve rivedere lo schermo.

⛔ IL DIFETTO, trovato dall'utente il 22 settembre 2026 e curato in `0b84a5b`:
   la tabella delle tele dei palchi vive nel PROCESSO del server, e il riavvio
   la azzera.  Al rientro il server non sapeva piu' che quella sessione grafica
   esisteva, concedeva la misura del client, e KWin `--virtual` non
   ridimensiona ⇒ schermo nero per sempre, con «gli richiedo» ripetuto.

⭐ CHE COSA PROVA, e sono tre cose che stanno insieme:
   1. la sessione grafica dell'inquilino SOPRAVVIVE al riavvio del server
      (I4: il palco e' della sessione, non del client);
   2. chi rientra rivede l'immagine, ⭐ anche con una finestra di misura
      diversa da quella con cui la sessione era nata;
   3. il registro lo dice a voce: «il palco era gia' a …: ADOTTO la sua misura».

⚠ E il giro si fa DUE volte: il difetto era proprio nel secondo stato — server
  nuovo, sessione vecchia — e un riavvio solo lo vedrebbe una volta sola.
"""
import time

import _comune as C

NOME = "riavvio-del-server"
DURATA_S = 4 * 60
TETTO_S = 15 * 60


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    giri = int(o.get("giri", 2))
    tetto_immagine_s = float(o.get("tetto_immagine_s", 40.0))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    chi = o.get("chi") or C.nome_inquilino("rs")
    # ⚠ Si NASCE con una misura e si TORNA con un'altra: e' la coppia che
    #   apriva il difetto.
    nasce = tuple(o.get("misura_alla_nascita", (1548, 862)))
    torna = tuple(o.get("misura_al_ritorno", (1400, 1000)))
    b = C.Banco(nucleo, desktop, marca, chi, misura=nasce, dove=o.get("dove"))
    fatti = []
    try:
        cod, perche = b.apparecchia("normale")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())
        time.sleep(10)
        if not C.compositore_vivo(nucleo, desktop, chi):
            return C.non_so(NOME, desktop, marca,
                            "la sessione grafica non e' nata: non c'e' niente a "
                            "cui sopravvivere", secondi=tetto.passati())

        for giro in range(1, giri + 1):
            if tetto.scaduto():
                break
            # ⛔ Il browser si chiude PRIMA del riavvio: un client attaccato a un
            #    server che muore e' un'altra prova (quella la fa `stacca`).
            C.chiudi(b.browser)
            b.browser = None
            acceso, dice = C.riavvia_il_server(desktop)
            if not acceso:
                return C.non_so(NOME, desktop, marca,
                                "al giro %d il server non si e' riacceso: %s"
                                % (giro, dice[-160:]), misure={"giri": fatti},
                                secondi=tetto.passati())
            # ⚠ Il registro e' stato azzerato dal riavvio: il segno si riprende.
            b.segno = C.istante(nucleo, desktop)
            viva = C.compositore_vivo(nucleo, desktop, chi)

            b.browser, cod, perche = C.apri_browser(nucleo, marca,
                                                     C.PORTE[desktop], torna, 90)
            if cod == C.VERDE:
                cod, perche = C.entra(b.browser, chi, b.parola, 90)
            if cod != C.VERDE:
                return C.esito(NOME, desktop, marca, cod,
                               "al giro %d, dopo il riavvio, non sono rientrato: %s"
                               % (giro, perche), misure={"giri": fatti},
                               secondi=tetto.passati())
            fine = time.time() + tetto_immagine_s
            consegnati = 0
            while time.time() < fine:
                consegnati = b.numeri().get("consegnati", 0) or 0
                if consegnati > 0:
                    break
                time.sleep(1.0)

            c, t = C.dentro(nucleo, desktop,
                            "grep -a '\\[%s\\]' %s | grep -c 'ADOTTO la sua misura'"
                            % (chi, C.REGISTRO), 90)
            try:
                adottata = int((t or "0").strip().splitlines()[-1])
            except (ValueError, IndexError):
                adottata = -1
            fatti.append({"giro": giro, "sessione_sopravvissuta": viva,
                          "consegnati_dopo": consegnati, "adotta_la_misura": adottata,
                          "finestra": list(torna)})

            if not viva:
                return C.rosso(NOME, desktop, marca,
                               "al giro %d la sessione grafica NON e' sopravvissuta "
                               "al riavvio del server (I4)" % giro,
                               misure={"giri": fatti}, secondi=tetto.passati())
            if consegnati <= 0:
                srv = b.server()
                return C.rosso(NOME, desktop, marca,
                               "al giro %d, rientrato con la finestra %dx%d su una "
                               "sessione nata %dx%d, in %.0f s non e' arrivato "
                               "NESSUN fotogramma"
                               % (giro, torna[0], torna[1], nasce[0], nasce[1],
                                  tetto_immagine_s),
                               misure={"giri": fatti, "server": srv},
                               secondi=tetto.passati())
            time.sleep(5)

        C.salva(o.get("dove"), "giri-riavvio.json", fatti)
        return C.verde(NOME, desktop, marca,
                       "%d riavvii del server sotto la stessa sessione: e' "
                       "sopravvissuta ogni volta e l'immagine e' tornata anche "
                       "con la finestra %dx%d su una sessione nata %dx%d"
                       % (len(fatti), torna[0], torna[1], nasce[0], nasce[1]),
                       misure={"giri": fatti, "server": b.server()},
                       regole={"giri": giri, "tetto_immagine_s": tetto_immagine_s},
                       secondi=tetto.passati())
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], misure={"giri": fatti},
                        secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
