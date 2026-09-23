#!/usr/bin/env python3
"""pesante — un video a schermo intero per cinque minuti.

⛔ IL DIFETTO CHE QUESTO SCENARIO ESISTE PER PRENDERE, e l'ha trovato l'utente
   il 22 settembre 2026 con un YouTube 4K dentro KDE: la pagina si FERMA.  Non
   rallenta — si ferma, e non riparte piu'.
   `[M]` Firefox su KDE: 173 buchi in 3,4 minuti, tutti e 173 per fotogrammi
   arrivati DOPO il loro successore; la pagina bloccata a 41 fotogrammi
   consegnati su 8810 stream ricevuti; poi linea morta.

⭐⭐ E IL GIUDICE CHE IERI NOTTE MANCAVA, ed e' il primo della lista da oggi:
   **l'OCCHIO** (`stress_occhio.py`).  La scena e' quella DICHIARATA, si
   fotografa la tela **una volta al secondo** e si conta quante celle non sono
   quelle che la scena dice.  ⛔ Senza di lui questo scenario conta fotogrammi e
   non li guarda — e un fotogramma sbagliato conta come uno giusto.
   ⚠ Con la scena dell'occhio le STRISCE non si giudicano piu' (si misurano e
     si riportano): il perche', misurato, sta in `_comune.misura_le_strisce`.

⭐ GLI ALTRI QUATTRO GIUDICI, e nessuno di loro guarda un totale:
   1. il contatore dei fotogrammi CONSEGNATI sale per TUTTO il tempo (un totale
      alto e un contatore fermo a meta' danno lo stesso numero: la differenza e'
      precisamente il difetto);
   2. nessuna linea morta;
   3. i buchi stanno sotto una soglia DICHIARATA;
   4. la tela a meta' prova non e' sbavata a strisce — e si MISURA
      (`_comune.strisce`), non si guarda.

⚠ Quel che questo scenario NON giudica: quanti fotogrammi il browser riesca a
  dipingere.  `[M]` 22 set 2026 Firefox su questo tablet ne riceve 48/s e ne
  dipinge 37: e' il suo tetto, non un difetto del prodotto, e si RIPORTA senza
  bocciare.
"""
import time

import _comune as C

NOME = "pesante"
DURATA_S = 300
TETTO_S = 480


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    durata = float(o.get("durata_s", DURATA_S))
    soglia_buchi = int(o.get("soglia_buchi", 20))
    soglia_strisce = float(o.get("soglia_strisce", 30.0))
    fermo_massimo = float(o.get("fermo_massimo_s", 25.0))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    chi = o.get("chi") or C.nome_inquilino("pe")
    b = C.Banco(nucleo, desktop, marca, chi, misura=o.get("misura", (1400, 1000)),
                dove=o.get("dove"))
    try:
        cod, perche = b.apparecchia("pesante")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())

        # ⭐ La fotografia di RIFERIMENTO, presa appena la scena e' viva: serve a
        #   dire se le strisce c'erano gia' o sono nate sotto carico.
        time.sleep(10)
        riferimento, _, _ = C.misura_le_strisce(b, b.foto("tela-prima.png"))

        meta = {}

        def a_meta(n, storia):
            if not meta and tetto.passati() > durata / 2:
                meta["strisce"], meta["si_giudica"], meta["dove"] = \
                    C.misura_le_strisce(b, b.foto("tela-meta.png"))

        # ⭐⭐ E QUI DENTRO L'OCCHIO FOTOGRAFA LA TELA UNA VOLTA AL SECONDO: i
        #   contatori restano a cinque secondi, l'immagine si guarda fitta —
        #   ⛔ gli episodi di corruzione durano meno di mezzo secondo.
        storia = C.guarda_per(nucleo, b.browser, min(durata, tetto.resta() - 60),
                              passo=5.0, tetto=tetto, ogni_giro=a_meta,
                              occhio=b.occhio)
        if "strisce" not in meta:
            meta["strisce"], meta["si_giudica"], meta["dove"] = \
                C.misura_le_strisce(b, b.foto("tela-meta.png"))

        primo, ultimo = storia[0], storia[-1]
        sempre, fermo = C.sempre_in_salita(storia, "consegnati", fermo_massimo)
        srv = b.server()
        cresciuta = C.cresciuti(primo, ultimo)
        C.salva(o.get("dove"), "storia-pesante.json", storia)

        misure = {
            "consegnati": ultimo.get("consegnati"),
            "dipinti": ultimo.get("dipinti"),
            "buchi": ultimo.get("buchi"),
            "cresciuti": cresciuta.get("consegnati"),
            "fermo_piu_lungo_s": fermo,
            "strisce_prima": riferimento,
            "strisce_meta": meta.get("strisce"),
            "strisce_dove": meta.get("dove") or "",
            "server": srv,
            "errori_della_pagina":
                (nucleo.conta_dalla_pagina(b.browser) or {}).get("errori_testo", [])[-3:],
        }
        regole = {"fermo_massimo_s": fermo_massimo, "soglia_buchi": soglia_buchi,
                  "soglia_strisce": soglia_strisce}

        guasti = []
        if not cresciuta.get("consegnati"):
            guasti.append("nessun fotogramma consegnato in %.0f s" % durata)
        elif not sempre:
            guasti.append("il contatore si e' fermato per %.1f s (tetto %.0f)"
                          % (fermo, fermo_massimo))
        if srv.get("linee_morte"):
            guasti.append("linea morta %d volte" % srv["linee_morte"])
        if (ultimo.get("buchi") or 0) > soglia_buchi:
            guasti.append("%d buchi (soglia %d)" % (ultimo["buchi"], soglia_buchi))
        if (meta.get("si_giudica") and meta.get("strisce") is not None
                and meta["strisce"] > soglia_strisce):
            guasti.append("la tela e' sbavata: dispersione %.1f (soglia %.1f)"
                          % (meta["strisce"], soglia_strisce))

        # ⭐⭐ IL QUINTO GIUDICE, ed e' quello che ieri notte mancava: **l'occhio**.
        #   I quattro di sopra contano fotogrammi; questo GUARDA quel che c'e'
        #   sul vetro e lo confronta con la scena dichiarata.  ⛔ Un «non lo so»
        #   non diventa un rosso.
        C.vede_l_occhio(b, misure, guasti)
        # ⭐ E la seconda rete, sui soli numeri.  ⚠ Da qui in poi il browser e'
        #   chiuso e l'inquilino e' uscito: e' l'unico momento in cui il server
        #   ha gia' scritto le righe di riepilogo del ritmo.
        C.conta_il_ritmo(b, misure, guasti)

        # ⭐ Un solo inquilino: i suoi numeri vanno anche in vista sulla riga.
        in_vista = dict(pagina=ultimo, server=srv)
        if guasti:
            return C.rosso(NOME, desktop, marca, "; ".join(guasti),
                           misure=misure, regole=regole, secondi=tetto.passati(),
                           guasti=guasti, **in_vista)
        return C.verde(NOME, desktop, marca,
                       "%d fotogrammi consegnati e %d dipinti in %.0f s, mai "
                       "fermi piu' di %.1f s, %d buchi; e l'occhio: %s"
                       % (cresciuta.get("consegnati", 0),
                          cresciuta.get("dipinti", 0), durata, fermo,
                          ultimo.get("buchi") or 0,
                          (misure.get("occhio") or {}).get("perche", "non c'era")),
                       misure=misure, regole=regole, secondi=tetto.passati(),
                       **in_vista)
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
