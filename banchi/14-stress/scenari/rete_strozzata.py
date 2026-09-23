#!/usr/bin/env python3
"""rete-strozzata — 5 Mbit/s e poi 1 Mbit/s: si deve DEGRADARE, non bloccarsi.

⛔ LA REGOLA, ed e' scritta in `RCP.md` §5.2: «se la linea e' cosi' cattiva da
   far abbandonare in continuazione, il rimedio NON e' mandare chiavi in
   continuazione — e' calare i fotogrammi».  Un fotogramma chiave per ogni
   delta abbandonato e' LA SPIRALE, ed e' il difetto del 22 settembre 2026.

⭐ QUINDI I GIUDICI SONO DUE, e vanno insieme:
   · l'immagine CONTINUA ad arrivare (meno fluida: giusto) — il contatore sale
     per tutto il tempo, a 5 Mbit/s come a 1;
   · e NON parte la spirale: le chiavi chieste restano poche rispetto ai
     fotogrammi spediti, e la linea non muore.

⛔ DOVE SI STROZZA: sul TABLET, sulla scheda vera (`wlo1`), non su `lo` e non
   sul server — il percorso da misurare e' quello che attraversa il filo
   (memoria «wondershaper sul tablet»).  ⚠ Il server non ha `tc` ne'
   `wondershaper`: il suo rootfs vive in RAM ed e' minimo.

⚠ E LA RETE SI RIMETTE SEMPRE, anche se il giro muore: una scheda lasciata
  strozzata falserebbe tutte le misure che vengono dopo, e nessuno collegherebbe
  le due cose.  ⇒ `finally` + un guardiano che libera comunque allo scadere del
  tetto.
"""
import threading
import time

import _comune as C

NOME = "rete-strozzata"
DURATA_S = 2 * 120
TETTO_S = 12 * 60
GRADINI = (5000, 1000)      # kbit/s


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    gradini = list(o.get("gradini", GRADINI))
    per_gradino = float(o.get("per_gradino_s", 120))
    fermo_massimo = float(o.get("fermo_massimo_s", 40.0))
    # ⚠ Con la linea stretta le chiavi aumentano per forza: il tetto non e' zero.
    #   Quel che NON deve succedere e' la spirale — una chiave ogni pochi
    #   fotogrammi.  `[M]` 22 set 2026 la spirale dava 347 chiavi al minuto.
    chiavi_per_cento = float(o.get("chiavi_per_cento", 5.0))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    chi = o.get("chi") or C.nome_inquilino("rt")
    b = C.Banco(nucleo, desktop, marca, chi, misura=o.get("misura", (1280, 900)),
                dove=o.get("dove"))

    # ⭐ Il guardiano: qualunque cosa succeda, allo scadere del tetto la rete
    #    torna libera.  ⛔ Senza, un'eccezione fuori posto lascia il tablet
    #    strozzato per tutta la notte.
    guardiano = threading.Timer(tetto.secondi + 30, C.libera)
    guardiano.daemon = True
    guardiano.start()

    misurati = []
    try:
        fatto, perche = C.strozza(gradini[0])
        if not fatto:
            return C.non_so(NOME, desktop, marca,
                            "non posso strozzare la rete del tablet: %s.  "
                            "⇒ serve che `wondershaper` giri senza parola: una "
                            "riga in sudoers («nicfio ALL=(root) NOPASSWD: "
                            "/usr/local/bin/wondershaper»), oppure la parola in "
                            "REMOTIX_PAROLA_TABLET" % perche[:120],
                            secondi=tetto.passati())
        C.libera()      # si accende la sessione a rete piena, poi si strozza

        cod, perche = b.apparecchia("pesante")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())
        time.sleep(10)

        for kbit in gradini:
            if tetto.scaduto():
                break
            fatto, perche = C.strozza(kbit)
            if not fatto:
                return C.non_so(NOME, desktop, marca,
                                "a %d kbit/s la strozzatura non si e' applicata: %s"
                                % (kbit, perche[:120]),
                                misure={"gradini": misurati}, secondi=tetto.passati())
            segno = C.istante(nucleo, desktop)
            # ⚠ L'occhio guarda anche qui, ma il suo verdetto in questo scenario
            #   si MISURA e non si giudica (vedi in fondo): la cadenza delle
            #   fotografie resta quella giusta, cosi' il numero c'e' il giorno
            #   che qualcuno lo tarera' sulla linea stretta.
            storia = C.guarda_per(nucleo, b.browser,
                                  min(per_gradino, max(30.0, tetto.resta() - 120)),
                                  passo=5.0, tetto=tetto, occhio=b.occhio,
                                  topo=b.topo)
            sempre, fermo = C.sempre_in_salita(storia, "consegnati", fermo_massimo)
            cresciuta = C.cresciuti(storia[0], storia[-1])
            srv = C.dal_server(nucleo, desktop, segno, chi)
            spediti = srv.get("spediti") or 0
            chieste = srv.get("rc_accolte") or 0
            quota = (100.0 * chieste / spediti) if spediti else None
            misurati.append({"kbit": kbit, "cresciuti": cresciuta.get("consegnati"),
                             "fermo_piu_lungo_s": fermo, "server": srv,
                             "chiavi_per_cento": round(quota, 2) if quota is not None else None})
            if not cresciuta.get("consegnati"):
                return C.rosso(NOME, desktop, marca,
                               "a %d kbit/s l'immagine si e' FERMATA invece di "
                               "degradare: nessun fotogramma in %.0f s"
                               % (kbit, per_gradino), misure={"gradini": misurati},
                               secondi=tetto.passati())
            if not sempre:
                return C.rosso(NOME, desktop, marca,
                               "a %d kbit/s l'immagine si e' fermata per %.1f s "
                               "(tetto %.0f)" % (kbit, fermo, fermo_massimo),
                               misure={"gradini": misurati}, secondi=tetto.passati())
            if srv.get("linee_morte"):
                return C.rosso(NOME, desktop, marca,
                               "a %d kbit/s la linea e' morta %d volte: la rete "
                               "stretta non deve chiudere la sessione"
                               % (kbit, srv["linee_morte"]),
                               misure={"gradini": misurati}, secondi=tetto.passati())
            if quota is not None and quota > chiavi_per_cento:
                return C.rosso(NOME, desktop, marca,
                               "a %d kbit/s LA SPIRALE: %d chiavi chieste su %d "
                               "fotogrammi spediti (%.1f%%, tetto %.1f%%)"
                               % (kbit, chieste, spediti, quota, chiavi_per_cento),
                               misure={"gradini": misurati}, secondi=tetto.passati())

        C.salva(o.get("dove"), "gradini-rete.json", misurati)
        # ⛔⛔ QUI L'OCCHIO SI MISURA MA NON GIUDICA, e la ragione e' che le sue
        #     soglie non sono MAI state tarate su una linea strozzata: `[M]` le
        #     soglie di `stress_occhio` vengono da un giro a banda piena, dove
        #     il sano sta a **0 celle guaste su 66 000**.  A 1 Mbit/s con la
        #     scena pesante il codificatore e' affamato per costruzione, e non
        #     si sa se una cella impastata sia il difetto o la linea.
        #     ⇒ Il numero si scrive, il verdetto lo dara' chi lo avra' tarato:
        #       ⛔ una soglia messa a occhio qui fabbrica rossi falsi, ed e' la
        #       stessa trappola scritta sopra `giudizio_dei_numeri`.
        misure = {"gradini": misurati}
        # ⚠ E il topo come l'occhio: il mouse si muove e il blocco piu' lungo
        #   si MISURA, ma non si giudica — ⛔ a 1 Mbit/s un blocco lungo puo'
        #   essere la linea, e la soglia di 10 s e' tarata (quando lo sara')
        #   a banda piena.
        C.vede_il_topo(b, misure, guasti=None, giudica=False)
        C.vede_l_occhio(b, misure, guasti=None, giudica=False)
        C.conta_il_ritmo(b, misure, guasti=None, giudica=False)
        return C.verde(NOME, desktop, marca,
                       "la linea stretta DEGRADA senza bloccare: %s"
                       % "; ".join("%d kbit/s → %s fotogrammi, %s%% chiavi"
                                   % (m["kbit"], m["cresciuti"],
                                      m["chiavi_per_cento"]) for m in misurati),
                       misure=misure,
                       regole={"gradini": gradini, "per_gradino_s": per_gradino,
                               "chiavi_per_cento": chiavi_per_cento},
                       secondi=tetto.passati())
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], misure={"gradini": misurati},
                        secondi=tetto.passati())
    finally:
        C.libera()
        guardiano.cancel()
        b.chiudi_tutto()
