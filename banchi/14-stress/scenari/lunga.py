#!/usr/bin/env python3
"""lunga — venti minuti di scena normale, per vedere se il server cresce.

⛔ QUELLO CHE CERCA: una perdita.  Descrittori, fili, figli e memoria del
   server non devono salire con il tempo.  ⚠ Nessuna delle altre prove della
   notte dura abbastanza per vederla: cinque minuti li regge anche un server
   che perde un descrittore al minuto.

⭐ E IL SECONDO GIUDICE, che e' quello che rende la prova onesta: alla fine
   l'immagine dev'essere ANCORA VIVA.  Un server che non cresce perche' ha
   smesso di lavorare sarebbe verde su tutt'e due i conti sbagliati.

⚠ Il metro della crescita e' `11-accendi.sh bilancio`, cioe' la stessa riga che
  legge il gancio: ⛔ non un modo nuovo di contare le stesse cose.
"""
import time

import _comune as C

NOME = "lunga"
# ⚠ Venti minuti, non quarantacinque: `[M]` 45 × sei combinazioni sono quattro
#   ore e mezza della notte per questo scenario solo.  ⛔ E si dichiara che cosa
#   costa il taglio: una perdita lenta — meno di un descrittore ogni venti
#   minuti — questo giro non la vede piu'.
DURATA_S = 20 * 60
TETTO_S = 28 * 60


def _bilancio(nucleo, desktop):
    """Il bilancio del server, ⭐ preso dalla stessa riga che legge il gancio.

    ⛔ Non se ne fa una copia: `conta_dal_server` porta gia' dentro
       `11-accendi.sh bilancio`, e due modi di contare le stesse cose sono due
       posti da cui divergere.
    """
    c = C.dal_server(nucleo, desktop) or {}
    return {k: v for k, v in c.items() if k.startswith("server_") or k == "inquilini"}


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    durata = float(o.get("durata_s", DURATA_S))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    # ⚠ Quanto si concede di crescere: zero sarebbe un rosso a ogni rumore
    #   (una cache che si riempie una volta non e' una perdita).  Questi numeri
    #   sono una scelta DICHIARATA, e la crescita vera si legge comunque.
    concesso = dict(o.get("concesso") or {"server_fd": 8, "server_fili": 2,
                                          "server_figli": 1})
    chi = o.get("chi") or C.nome_inquilino("lu")
    b = C.Banco(nucleo, desktop, marca, chi, misura=o.get("misura", (1280, 900)),
                dove=o.get("dove"))
    try:
        prima_del_giro = _bilancio(nucleo, desktop)
        cod, perche = b.apparecchia("normale")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())

        time.sleep(30)                      # la sessione si assesta
        prima = _bilancio(nucleo, desktop)
        n_prima = b.numeri()

        storia = C.guarda_per(nucleo, b.browser, min(durata, tetto.resta() - 120),
                              passo=60.0, tetto=tetto)
        n_dopo = b.numeri()
        dopo = _bilancio(nucleo, desktop)
        srv = b.server()
        C.salva(o.get("dove"), "storia-lunga.json",
                {"storia": storia, "bilancio_prima": prima, "bilancio_dopo": dopo,
                 "bilancio_prima_del_giro": prima_del_giro})

        cresciuta = {k: dopo[k] - prima[k] for k in prima
                     if k in dopo and k.startswith("server_") and k != "server_pid"}
        vivo = (n_dopo.get("consegnati", 0) or 0) > (n_prima.get("consegnati", 0) or 0)

        misure = {"bilancio_prima": prima, "bilancio_dopo": dopo,
                  "cresciuto": cresciuta, "server": srv,
                  "consegnati_alla_fine": n_dopo.get("consegnati"),
                  "minuti": round(tetto.passati() / 60.0, 1)}
        regole = {"concesso": concesso, "durata_s": durata}

        if prima.get("server_pid") != dopo.get("server_pid"):
            return C.non_so(NOME, desktop, marca,
                            "il server e' cambiato nel mezzo (%s→%s): la colonna "
                            "del prodotto non si confronta"
                            % (prima.get("server_pid"), dopo.get("server_pid")),
                            misure=misure, secondi=tetto.passati())

        guasti = []
        for k, quanto in sorted(cresciuta.items()):
            tetto_k = concesso.get(k)
            if tetto_k is not None and quanto > tetto_k:
                guasti.append("%s cresciuto di %d (concesso %d)" % (k, quanto, tetto_k))
        if not vivo:
            guasti.append("alla fine l'immagine non arriva piu': i fotogrammi "
                          "consegnati non sono saliti nell'ultimo giro")

        if guasti:
            return C.rosso(NOME, desktop, marca, "; ".join(guasti), misure=misure,
                           regole=regole, secondi=tetto.passati())
        return C.verde(NOME, desktop, marca,
                       "%.0f minuti: il server non e' cresciuto oltre il concesso "
                       "(%s) e l'immagine e' ancora viva"
                       % (tetto.passati() / 60.0,
                          ", ".join("%s +%d" % (k, v) for k, v in sorted(cresciuta.items()))
                          or "niente"),
                       misure=misure, regole=regole, secondi=tetto.passati())
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
