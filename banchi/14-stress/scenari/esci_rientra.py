#!/usr/bin/env python3
"""esci-rientra — «Esci» dal menu e un nuovo accesso, cinque volte di fila.

⛔ IL DIFETTO: i FANTASMI.  22 settembre 2026, prova dell'utente su KDE con
   Chrome: dopo «Esci» e un nuovo accesso lo schermo alternava il desktop nuovo,
   la schermata d'uscita della sessione di PRIMA e il nero.  La generazione dei
   buffer ripartiva da zero con la cattura nuova, il codificatore no: stessa
   generazione, cache non buttata, descrittori riciclati sulle superfici morte.
   Curato in `e1e9fa7`, e il banco che lo prende e' `13-w4`.

⭐ QUI SI FA CINQUE VOLTE, e non una: `[M]` il difetto e' nato dal RICICLO dei
   descrittori, e il riciclo ha bisogno di giri.  ⚠ E il gesto e' quello vero —
   «Esci» dal bus del desktop, non un `kill` del compositore: un `kill` prova
   un'altra cosa.

⭐ DUE GIUDICI, come in `13-w4`:
   · i PIXEL: a desktop fermo la luminanza media dei fotogrammi dev'essere UNA.
     Se alterna fra valori lontani, e' il lampeggio.  ⚠ Qui si guarda dalla
     PAGINA (fotografie della tela a distanza di un secondo), perche' il
     browser e' vero e il video non passa da un file;
   · il REGISTRO del server: dopo la rinascita il codificatore deve dire «butto
     le N superfici importate».
"""
import time

import _comune as C

NOME = "esci-rientra"
DURATA_S = 5 * 150
TETTO_S = 20 * 60


def _luminanze(banco, quante=6, passo=1.0):
    """La luminanza media di alcune fotografie della tela, a un secondo l'una.

    ⛔ Torna `None` se non si puo' misurare: a desktop fermo una tela che non
       si fotografa non e' una tela stabile, e' una misura mancata.
    """
    try:
        import io
        import numpy as np
        from PIL import Image
    except Exception:
        return None
    fuori = []
    for _ in range(quante):
        png = banco.foto()
        if not png:
            return None
        try:
            a = np.asarray(Image.open(io.BytesIO(png)).convert("L"), dtype=np.float32)
        except Exception:
            return None
        fuori.append(float(a.mean()))
        time.sleep(passo)
    return fuori


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    giri = int(o.get("giri", 5))
    salto_massimo = float(o.get("salto_massimo", 8.0))   # livelli di luminanza
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    chi = o.get("chi") or C.nome_inquilino("es")
    b = C.Banco(nucleo, desktop, marca, chi, misura=o.get("misura", (1280, 900)),
                dove=o.get("dove"))
    fatti = []
    try:
        cod, perche = b.apparecchia("normale")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())

        for giro in range(1, giri + 1):
            if tetto.scaduto():
                break
            if not C.compositore_vivo(nucleo, desktop, chi):
                return C.non_so(NOME, desktop, marca,
                                "al giro %d la sessione grafica non c'era: non "
                                "posso uscirne" % giro, misure={"giri": fatti},
                                secondi=tetto.passati())
            segno = C.istante(nucleo, desktop)
            uscito, dice = C.esci_dalla_sessione(nucleo, desktop, chi)
            if not uscito:
                return C.non_so(NOME, desktop, marca,
                                "al giro %d «Esci» non ha risposto: %s" % (giro, dice),
                                misure={"giri": fatti}, secondi=tetto.passati())
            # il compositore deve andarsene davvero
            for _ in range(40):
                if not C.compositore_vivo(nucleo, desktop, chi):
                    break
                time.sleep(1.0)
            else:
                return C.rosso(NOME, desktop, marca,
                               "al giro %d 40 s dopo «Esci» il compositore e' "
                               "ancora vivo" % giro, misure={"giri": fatti},
                               secondi=tetto.passati())

            cod, perche = b.rientra(scena_quale="normale")
            if cod != C.VERDE:
                return C.esito(NOME, desktop, marca, cod,
                               "al giro %d non sono rientrato dopo «Esci»: %s"
                               % (giro, perche), misure={"giri": fatti},
                               secondi=tetto.passati())
            time.sleep(8)      # la sessione nuova si disegna

            lum = _luminanze(b)
            salti = None
            if lum:
                salti = sum(1 for a, c in zip(lum, lum[1:])
                            if abs(a - c) > salto_massimo)
            srv = C.dal_server(nucleo, desktop, segno, chi)
            c, testo = C.dentro(nucleo, desktop,
                                "grep -a '\\[%s\\]' %s | awk '$1>=\"%s\"' | "
                                "grep -c 'butto le'" % (chi, C.REGISTRO, segno), 90)
            try:
                buttate = int((testo or "0").strip().splitlines()[-1])
            except (ValueError, IndexError):
                buttate = -1
            fatti.append({"giro": giro, "luminanze": lum, "salti": salti,
                          "cache_buttata": buttate, "server": srv})

            if salti is None:
                return C.non_so(NOME, desktop, marca,
                                "al giro %d non ho potuto fotografare la tela"
                                % giro, misure={"giri": fatti},
                                secondi=tetto.passati())
            if salti > 1:
                return C.rosso(NOME, desktop, marca,
                               "FANTASMI al giro %d: %d salti di luminanza fra "
                               "fotogrammi a desktop fermo (%s)"
                               % (giro, salti, [round(x, 1) for x in lum]),
                               misure={"giri": fatti}, secondi=tetto.passati())
            if buttate == 0:
                return C.rosso(NOME, desktop, marca,
                               "al giro %d dopo la rinascita il codificatore NON "
                               "ha buttato la cache delle superfici" % giro,
                               misure={"giri": fatti}, secondi=tetto.passati())

        pulita, dice = b.pulita()
        return C.verde(NOME, desktop, marca,
                       "%d uscite e altrettanti rientri: nessun fantasma "
                       "(salti di luminanza %s), cache buttata ogni volta"
                       % (len(fatti), [f["salti"] for f in fatti]),
                       misure={"giri": fatti, "scatola": dice},
                       regole={"salto_massimo": salto_massimo, "giri": giri},
                       secondi=tetto.passati())
    except Exception as e:
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], misure={"giri": fatti},
                        secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
