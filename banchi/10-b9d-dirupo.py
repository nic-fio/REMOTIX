#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
10-b9d-dirupo — ⭐⭐⭐ CHE COSA SI ROMPE FRA LA SESTA SESSIONE E L'OTTAVA
═══════════════════════════════════════════════════════════════════════════════

⛔ QUESTO BANCO NON MISURA IL DIRUPO: quello e' gia' misurato
   (`fasi/10-multi-tenant-e-il-budget.md` §6.5, 38 fot/s a sei, 1,5 a otto).
   ⭐ Questo banco cerca **il MECCANISMO**, e la differenza e' tutta qui:

   | il primo giro ha detto | questo deve dire |
   |---|---|
   | «a otto si crolla»     | «si crolla PERCHE'…», con la prova accanto |
   | «GPU render 99,5 %»    | ⭐ **CHI** tiene il motore render al 99,5 % |
   | «GPU video 1,6 %»      | ⭐ **dove** si ferma il fotogramma prima di arrivarci |

⛔⛔ E LA COLONNA CHE HA PARLATO NON E' QUELLA CHE SI GUARDAVA (`LEZIONI.md`
    §1.34).  A saturare e' `render`, ma `render` non e' un programma: e' un
    motore che tre popoli diversi si contendono — i **compositori** (uno per
    utente), le **scene** del banco, e i **figli** del prodotto, che sul motore
    render ci fanno la **conversione di colore** (§6.6: `vecs0` resta a zero, la
    conversione gira sulle EU).  ⇒ Finche' non si dice **quale dei tre** cresce,
    «render al 99,5 %» non e' un meccanismo: e' un altro sintomo.

───────────────────────────────────────────────────────────────────────────────
⭐⭐ LE CINQUE GRANDEZZE CHE QUESTO BANCO AGGIUNGE, e perche' ciascuna
───────────────────────────────────────────────────────────────────────────────

1. ⭐⭐⭐ **La GPU per PROGRAMMA** (`10-b9d-chi-tiene-la-gpu.py`).  `10-b92-sonda`
   somma per macchina e per uid; qui il delta si fa per **contesto DRM** (l'unica
   forma in cui quei nanosecondi si possano sottrarre) e si raggruppa **dopo**
   per `comm`.  ⇒ Al gradino del dirupo si legge se il render se lo prendono i
   `gnome-shell` o i `remotix-figlio`.  Sono due meccanismi opposti: nel primo
   caso il prodotto e' **affamato** da chi compone, nel secondo e' lui a mangiare.

2. ⭐⭐⭐ **Il TRATTO dei figli** (`figlio.c:4748`, una riga al secondo per
   figlio).  Dice dove se ne vanno i millisecondi di UN fotogramma, in dieci
   voci.  Tre di quelle voci sono tre spiegazioni diverse del dirupo, e si
   escludono a vicenda:
     · `nel posto`   alta ⇒ il fotogramma invecchia aspettando che il ciclo del
                     figlio torni a prenderlo: il consumatore e' lento;
     · `conversione` alta ⇒ si aspetta il `vaSyncSurface` del VPP
                     (`codificatore.c:3335`), che e' **bloccante e senza
                     scadenza** sul motore RENDER;
     · `spedizione`  alta ⇒ il `send()` verso il padre e' **bloccante**
                     (`figlio.c:2741`, nessun `MSG_DONTWAIT`, nessun timeout):
                     e' contropressione del padre, e ferma la cattura con se'.
   ⛔ E l'ASSENZA della riga e' a sua volta un dato: se il figlio e' appeso
      dentro `send()`, `⭐ TRATTO` e `ciclo:` **spariscono tutt'e due**.

3. ⭐⭐ **Le consegne del palco, PER SESSIONE** — la riga `ritmo di <prov>:
   arretrato LETTO N volte in quest'ultimo secondo` (`webtransport.c:4480`).
   ⛔ E' l'unica riga per-sessione che conta i fotogrammi **arrivati al padre**
   invece di quelli **usciti sul filo**.  ⇒ Separa «il padre non spedisce» da
   «al padre non arriva piu' niente», che e' il bivio del dirupo.

4. ⭐ **Il ripiego in software** (`RIPIEGO DICHIARATO`, `figlio.c:4470`): la
   `[?]` numero 11 di §3.6, lasciata aperta apposta.  Si conta, e si dichiara
   anche quando e' **zero** — perche' zero qui e' una risposta, non un silenzio.

   ⛔⛔ **E LA MARCA `RIPIEGO DICHIARATO` NON E' UNA SOLA.**  La stessa apre
   anche la riga della **tabella delle tele dei palchi piena**
   (`webtransport.c:5264`, `WT_PALCHI 8`), che e' un fatto **diverso** e morde
   al **NONO** utente.  ⇒ Un rivelatore che contasse la marca e basta
   accuserebbe il codificatore di essere ripiegato in CPU **proprio al gradino
   in cui il dirupo si manifesta**, e avrebbe chiuso la caccia sulla risposta
   sbagliata con un numero perfettamente plausibile.
   ⭐ La cura sta in `10-b9d-conti.py` accanto a `RE_RIPIEGO`: si distingue
   dalla FORMA della riga (`«X» su Y non si e' aperto … si scende su «Z»`), i
   due fatti si contano in due caselle diverse, e `--certifica` gli fa passare
   davanti una riga di ciascuno per vedere che non le confonda.

5. ⭐⭐ **Il confine su una grandezza CONTINUA invece che sul numero di
   sessioni.**  Se il dirupo cade a otto sessioni, l'ottava non ha niente di
   speciale: e' il carico che porta.  ⇒ Al gradino dell'ottava si cambia **solo
   il carico** — la stessa popolazione, le stesse otto sessioni, gli stessi
   otto desktop — spegnendo la scena di una, o mettendola in finestra.
   ⛔ E' l'esperimento che decide: se otto sessioni di cui una ferma si
   comportano come sette, il confine e' sul **carico**; se crollano come otto,
   il confine e' sul **numero**, e allora c'e' una risorsa per-sessione che
   finisce.  ⭐ Le due risposte mandano il prodotto in due direzioni diverse.

───────────────────────────────────────────────────────────────────────────────
⛔ QUEL CHE NON RIFA'
───────────────────────────────────────────────────────────────────────────────
`10-b92-dieci.py` e' **importato**, non riscritto: da lui vengono l'apertura
delle sessioni, le scene, il ritaglio delle fette, la sonda di CPU/memoria/filo,
il terreno e il lucchetto.  ⚠ Le sue globali si impostano **prima
dell'import** (leggono l'ambiente li'), e la tela per sessione si cambia
assegnando `B92.TELA` prima di aprire quella sessione — che e' il solo modo di
avere due sessioni con due tele senza toccare il suo codice.

───────────────────────────────────────────────────────────────────────────────
uso
───────────────────────────────────────────────────────────────────────────────
    python3 banchi/10-b9d-dirupo.py --certifica         # ⛔ prima di tutto
    python3 banchi/10-b9d-dirupo.py terreno
    python3 banchi/10-b9d-dirupo.py giro --da 5 --a 8 --durata 40
    python3 banchi/10-b9d-dirupo.py giro --da 5 --a 8 --fine   # + i bracci fini

l'ambiente (l'isolamento):  PORTA UTENTE ALBERO LAV UNITA IO_SONO FUORI
"""
import argparse
import importlib.util
import json
import os
import statistics
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, PRIMA DI IMPORTARE CHIUNQUE LEGGA L'AMBIENTE
# ═══════════════════════════════════════════════════════════════════════════
os.environ.setdefault("PORTA", "8190")
os.environ.setdefault("ALBERO", "/media/REMOTIX/src/10b9-src")
os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10b9")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10b9-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10b9")
os.environ.setdefault("UNITA", "remotix-8190")
os.environ.setdefault("IO_SONO", "10-b9")
os.environ.setdefault("FUORI", "/tmp/10-b9d")
os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
os.environ.setdefault("SHM_BASE", "10b9d")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _importa(nome, file_):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(spec)
    sys.modules[nome] = m
    spec.loader.exec_module(m)
    return m


B92 = None          # si carica in `principale()`: importarlo costa un `_importa_b70`


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA FOTOGRAFIA — quella di 10-b92 PIU' la GPU per programma, in UN ssh
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Un `ssh` per ciascuna sarebbe due istanti diversi, e la CPU, la memoria e
#    la GPU di due istanti diversi non fanno un ritratto: fanno un collage.
#    ⚠ Le due letture restano comunque **consecutive**, non simultanee: fra
#      l'una e l'altra passa il costo della prima, e quel costo si dichiara
#      (`costo_ms`) invece di fingere che sia zero.
def fotografia(quanti):
    uids = ",".join(str(B92.uid(i)) for i in range(1, quanti + 1))
    rc, out, err = B92.root(
        "python3 %s/10-b92-sonda.py %s %s %s; echo '---SPARTIACQUE---'; "
        "python3 %s/10-b9d-chi-tiene-la-gpu.py %s %s"
        % (B92.LAV, B92.PDEV_BUONO, uids, B92.UNITA,
           B92.LAV, B92.PDEV_BUONO, uids), 240)
    pezzi = out.split("---SPARTIACQUE---")
    if len(pezzi) != 2:
        _dub("⛔ la fotografia non e' tornata in due pezzi (rc=%s): %s"
             % (rc, (out + err)[-200:]))
        return None
    try:
        a = json.loads(pezzi[0])
        b = json.loads(pezzi[1])
    except Exception as e:
        _dub("⛔ la fotografia non si legge: %s — %s" % (e, (out + err)[-200:]))
        return None
    a["chi_tiene"] = b
    return a


# ⛔⛔ IL DELTA PER CONTESTO, E IL RAGGRUPPAMENTO DOPO.
#
#     `drm-engine-*` sono cumulativi **per contesto DRM**, e il contesto muore
#     col processo.  Raggruppare per programma PRIMA di sottrarre vorrebbe dire
#     sottrarre due somme prese su due platee diverse: `[M]` al primo giro
#     quell'errore ha prodotto un'occupazione **negativa del 76 %**.
#     ⇒ Si sottrae per contesto, si tengono solo i contesti presenti in tutt'e
#       due, e si SOMMA per `comm` alla fine.  I nati e i morti si contano.
def chi_tiene(a, b):
    if not a or not b:
        return {"esito": "⛔ NON GIUDICO — manca una delle due fotografie"}
    ca = (a.get("chi_tiene") or {}).get("per_contesto") or {}
    cb = (b.get("chi_tiene") or {}).get("per_contesto") or {}
    dt = ((b.get("chi_tiene") or {}).get("t_ms", 0)
          - (a.get("chi_tiene") or {}).get("t_ms", 0)) / 1000.0
    if dt <= 0.5:
        return {"esito": "⛔ NON GIUDICO — fra le due fotografie sono passati "
                         "%.2f s" % dt}
    cap = (b.get("chi_tiene") or {}).get("capacita") or {}
    comuni = set(ca) & set(cb)
    per_chi, negativi = {}, {}
    for cid in comuni:
        va, vb = ca[cid], cb[cid]
        chi = vb.get("chi") or "?"
        d = per_chi.setdefault(chi, {"contesti": 0, "pid": set()})
        d["contesti"] += 1
        d["pid"].add(vb.get("pid"))
        for m in ("render", "video", "video-enhance", "copy", "blitter"):
            if m not in va or m not in vb:
                continue
            ns = vb[m] - va[m]
            pc = 100.0 * ns / 1e9 / dt
            if ns < 0:
                negativi.setdefault(chi, {})[m] = round(pc, 2)
            d[m] = round(d.get(m, 0.0) + pc, 2)
    for chi, d in per_chi.items():
        d["pid"] = len(d["pid"])
    fuori = {"dt": round(dt, 2), "capacita": cap,
             "contesti_comuni": len(comuni),
             "contesti_nati": len(set(cb) - set(ca)),
             "contesti_morti": len(set(ca) - set(cb)),
             "per_programma": per_chi}
    if negativi:
        # ⛔ Un motore non lavora per un tempo negativo: se compare, il metro
        #    non e' quello che credo e il gradino NON si giudica.
        fuori["esito"] = ("⛔ NON GIUDICO — occupazione NEGATIVA: %s"
                          % json.dumps(negativi, ensure_ascii=False))
    else:
        fuori["esito"] = "misurato"
        # ⭐ Il controllo dove il numero si consuma: un motore serve una
        #    richiesta per volta, quindi la somma su tutti i programmi non puo'
        #    passare il 100 % **per ogni motore che ha** (i VDBOX sono DUE).
        for m in ("render", "video"):
            s = sum(d.get(m, 0.0) for d in per_chi.values())
            fuori["somma_" + m] = round(s, 1)
            if s > 100.0 * max(1, cap.get(m, 1)) + 5.0:
                fuori["esito"] = ("⛔ NON GIUDICO — il metro conta due volte: "
                                  "%s in somma %.1f %% con capacita' %s"
                                  % (m, s, cap.get(m, 1)))
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL REGISTRO — le sei grandezze del dirupo
# ═══════════════════════════════════════════════════════════════════════════
def dove_sono_fermi(modello="remotix-figlio", campioni=14, pausa=0.5):
    """⭐⭐ LA MISURA CHE DECIDE FRA LE DUE SPIEGAZIONI DEL DIRUPO, e la decide
       senza passare dal registro: in quale chiamata di sistema stanno fermi i
       thread dei figli, in questo istante.

    ⛔ `ioctl` su `/dev/dri/*` ⇒ attesa sulla GPU: e' il `vaSyncSurface` del VPP
       (`codificatore.c:3335`), bloccante e senza scadenza — e ⭐ **tiene il
       buffer del compositore** finche' non torna (`cattura.c`, la RITENUTA).
    ⛔ `sendto`/`sendmsg` su socket ⇒ contropressione del PADRE: il `send()`
       verso il padre e' bloccante (`figlio.c:2741`), e ferma la cattura con se'.
    ⛔ `ppoll`/`futex` ⇒ si aspetta qualcosa che non arriva: tipicamente un
       fotogramma dal compositore.
    ⚠ E' un CAMPIONE, non una prova: si conta in quale stato si e' trovato, che
      e' una frequenza.  ⇒ Il numero dei campioni sta nel risultato.
    """
    rc, out, err = B92.root("python3 %s/10-b9d-dove-sono-fermi.py %s %d %.2f"
                            % (B92.LAV, modello, campioni, pausa), 240)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception as e:
        return {"esito": "⛔ NON HO LETTO — la sonda non ha risposto: %s — %s"
                         % (e, (out + err)[-200:])}


def conti97(b0, b1, figli_attesi):
    if b0 is None or b1 is None or b1 <= b0:
        return {"esito": "⛔ NON HO LETTO — confini del registro «%s»→«%s»"
                         % (b0, b1)}
    rc, out, err = B92.root("python3 %s/10-b9d-conti.py %s/registro.log %d %d %d"
                            % (B92.LAV, B92.LAV, b0, b1, figli_attesi), 900)
    try:
        return json.loads(out)
    except Exception as e:
        return {"esito": "⛔ NON HO LETTO — il lettore non ha risposto: %s — %s"
                         % (e, (out + err)[-200:])}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ UN GRADINO — la popolazione che c'e' adesso, misurata per `durata` secondi
# ═══════════════════════════════════════════════════════════════════════════
def gradino(nome, quanti, durata, carico):
    """`carico` descrive quel che ciascuna sessione sta facendo, e sta nel
       risultato: un gradino senza la descrizione del carico e' un numero senza
       la scena accanto."""
    _log("GRADINO «%s» — %d sessioni · %d s · carico %s" % (nome, quanti, durata,
                                                            carico))
    B92.assicura_scene_dichiarate = None    # ⚠ non si tocca: le scene le governo io
    _inf("assestamento %.0f s" % B92.ASSESTAMENTO_S)
    time.sleep(B92.ASSESTAMENTO_S)

    f0 = fotografia(quanti)
    r0 = B92.registro_righe()
    d0 = B92.disegni_tutte(quanti)
    if f0 is None or f0.get("t_ms") is None:
        _ko("⛔ niente ancora: NON misuro il gradino «%s»" % nome)
        return None
    t0 = f0["t_ms"]
    # ⛔ A META' DELLA FINESTRA, non prima e non dopo: il campione deve cadere
    #    dentro il regime che il gradino sta misurando.  ⚠ E costa una scansione
    #    di `/proc` in sola lettura — non tocca ne' la GPU ne' i processi.
    time.sleep(max(0.0, durata / 2.0 - 7.0))
    fermi = dove_sono_fermi("remotix-figlio")
    fermi_shell = dove_sono_fermi("gnome-shell", campioni=6, pausa=0.4)
    time.sleep(max(0.0, durata / 2.0))
    f1 = fotografia(quanti)
    r1 = B92.registro_righe()
    d1 = B92.disegni_tutte(quanti)
    if f1 is None or f1.get("t_ms") is None:
        _ko("⛔ niente ancora finale: NON misuro il gradino «%s»" % nome)
        return None
    t1 = f1["t_ms"]

    d = B92.fra(f0, f1, quanti)
    g = chi_tiene(f0, f1)
    vive, scene, non_so = B92.chi_c_e(quanti)
    prov, posti = B92.mappa_provenienze()
    c = conti97(r0, r1, quanti)

    # ── le fette dei clienti ────────────────────────────────────────────
    #
    # ⛔ LA RIDUZIONE DI 09-b70 SI RIFIUTA SOTTO I 30 FOTOGRAMMI, e ha ragione:
    #    sotto quel numero non c'e' niente da ridurre.  ⚠ Ma nei bracci fini una
    #    sessione **a scena spenta** ne consegna una manciata, e quello e' il
    #    RISULTATO, non un guasto della prova.  ⇒ Per quelle sessioni si chiede
    #    a `10-b92` il conto scarno che ha gia' scritto per il braccio `ferma`
    #    (`conto_scarno`, che lascia `None` in tutte le colonne che con pochi
    #    fotogrammi non vogliono dire niente), invece di inventarne un altro.
    sessioni = {}
    vecchia_scena = B92.SCENA
    for i in range(1, quanti + 1):
        B92.SCENA = "satura" if carico.get(i, "satura") == "satura" else "ferma"
        sessioni[i] = B92.fetta(i, t0, t1, (t1 - t0) / 1000.0)
    B92.SCENA = vecchia_scena
    # ── i disegni della scena: l'INGRESSO della prova, non l'uscita ──────
    disegni = {}
    if d0 and d1:
        for i in range(1, quanti + 1):
            a, b = d0.get(i) or {}, d1.get(i) or {}
            if isinstance(a.get("disegni"), int) and isinstance(b.get("disegni"), int):
                disegni[i] = round((b["disegni"] - a["disegni"])
                                   / ((t1 - t0) / 1000.0), 1)
            else:
                disegni[i] = None
    else:
        disegni = None

    voce = {"nome": nome, "quanti": quanti, "durata_s": durata,
            "carico": carico, "t0": t0, "t1": t1,
            "macchina": d, "chi_tiene_la_gpu": g, "registro": c,
            "vive": vive, "scene": scene, "non_so": non_so,
            "posti_occupati": posti, "disegni_al_secondo": disegni,
            "_prov": prov, "sessioni": sessioni,
            "dove_sono_fermi": fermi, "dove_e_fermo_il_compositore": fermi_shell}
    stampa_gradino(voce)
    return voce


def _fps(f):
    if not isinstance(f, dict) or f.get("esito") != "misurato":
        return None
    return f.get("fps")


def stampa_gradino(v):
    n = v["quanti"]
    fps = [_fps(v["sessioni"].get(i)) for i in range(1, n + 1)]
    vivi = [x for x in fps if x is not None]
    _inf("fot/s a testa: %s   ⇒ AGGREGATO %s"
         % (" ".join("s%d=%s" % (i + 1, "None" if x is None else "%.2f" % x)
                     for i, x in enumerate(fps)),
            "None" if not vivi else "%.1f" % sum(vivi)))
    rit = []
    for i in range(1, n + 1):
        f = v["sessioni"].get(i) or {}
        r = (f.get("ritardo") or {}).get("mediano_ms") if isinstance(f, dict) else None
        rit.append("s%d=%s" % (i, r))
    _inf("ritardo mediano: %s" % " ".join(rit))
    if v.get("disegni_al_secondo"):
        dd = [x for x in v["disegni_al_secondo"].values() if x is not None]
        _inf("disegni/s delle scene (⭐ l'INGRESSO della prova): %s ⇒ somma %s"
             % (" ".join("s%s=%s" % (k, x)
                         for k, x in sorted(v["disegni_al_secondo"].items())),
                "None" if not dd else round(sum(dd), 1)))
    d = v["macchina"]
    _inf("CPU %s %% su %s nuclei (server %s nuclei) · GT %s MHz · RC6 %s %%"
         % (d.get("cpu_occupata_pc"), d.get("cpu_nuclei"),
            d.get("cpu_server_nuclei"), (d.get("gt") or {}).get("act_mhz"),
            (d.get("gt") or {}).get("rc6_pc")))
    _inf("GPU in somma %s   (capacita' %s)"
         % (json.dumps(d.get("gpu_pc")), json.dumps(d.get("gpu_capacita"))))
    g = v["chi_tiene_la_gpu"]
    if g.get("esito") == "misurato":
        righe = sorted(g["per_programma"].items(),
                       key=lambda kv: -(kv[1].get("render") or 0))
        _inf("⭐ CHI TIENE LA GPU (render / video, %% del tempo di parete):")
        for chi, dd in righe[:8]:
            if (dd.get("render") or 0) < 0.3 and (dd.get("video") or 0) < 0.3:
                continue
            print("          %-18s render %7.2f   video %7.2f   (%d contesti, "
                  "%d processi)" % (chi, dd.get("render") or 0.0,
                                    dd.get("video") or 0.0, dd["contesti"],
                                    dd["pid"]), flush=True)
        _inf("          somma render %s · somma video %s"
             % (g.get("somma_render"), g.get("somma_video")))
    else:
        _dub("chi tiene la GPU: %s" % g.get("esito"))
    c = v["registro"]
    if c.get("esito") == "letto":
        t = c.get("tratto_dei_figli") or {}
        if t.get("righe"):
            vv = t["voci"]
            _inf("⭐ TRATTO dei figli (mediana su %d righe): TOTALE %.1f ms  |  "
                 "%s" % (t["righe"], t["totale"]["mediana_ms"],
                         "  ".join("%s %.1f" % (k, vv[k]["mediana_ms"])
                                   for k in ("produttore", "nel posto",
                                             "conversione", "codifica",
                                             "spedizione")
                                   if k in vv)))
        else:
            _dub("TRATTO: %s" % t.get("esito"))
        cat = c.get("cattura_dei_figli") or {}
        if "attese_a_vuoto" in cat:
            _inf("cattura dei figli (in somma, %d serie): %d fotogrammi, %d "
                 "attese a vuoto, %d guasti — %s"
                 % (cat["serie"], cat["fotogrammi_catturati"],
                    cat["attese_a_vuoto"], cat["guasti"],
                    "%.0f attese/s per figlio"
                    % (cat["attese_a_vuoto"] / max(1, v["quanti"])
                       / max(1.0, v["durata_s"]))))
        else:
            _dub("cattura dei figli: %s" % cat.get("esito"))
        _inf("⛔ ripieghi in software nella finestra: %d %s"
             % (c["quanti_ripieghi"],
                json.dumps(c["ripieghi_software"][:3], ensure_ascii=False)
                if c["quanti_ripieghi"] else "(⭐ zero: la [?] 11 di §3.6 "
                                             "risponde NO in questa scena)"))
        _inf("cure: ritmo SCENDE %s / RISALE %s · coda SOPRA %s / SOTTO %s · "
             "abbandoni %s · involo pieno %s · %s"
             % (c["ritmo_scende_in_tutto"], c["ritmo_risale_in_tutto"],
                c["sopra_soglia_in_tutto"], c["sotto_soglia_in_tutto"],
                c["abbandoni_in_coda"], c["involo_pieno"],
                json.dumps(c["altri_conti"])))
        _inf("logind dentro il ciclo (main.c:1752 · sentinella.c:29): %s"
             % json.dumps(c.get("logind"), ensure_ascii=False))
        _inf("i buffer di PipeWire (cattura.c:586 ne chiede 6, min 4): %s"
             % json.dumps(c.get("buffer_di_pipewire"), ensure_ascii=False)[:300])
        pp = c.get("per_provenienza") or {}
        if pp:
            _inf("⭐ consegne del PALCO al padre, per sessione (fot/s letti dal "
                 "padre — mediana [min-max], secondi a zero):")
            inv = dict((val, k) for k, val in (v.get("_prov") or {}).items())
            for p, dd in sorted(pp.items()):
                if "esito" in dd:
                    print("          %-22s %s" % (inv.get(p, p), dd["esito"]),
                          flush=True)
                    continue
                print("          %-22s %3d [%d-%d]  zero %ds/%ds  scende %d/"
                      "risale %d  sopra %d/sotto %d  chiave ogni %s ms"
                      % (inv.get(p, p), dd["consegne_al_secondo_mediana"],
                         dd["consegne_al_secondo_min"],
                         dd["consegne_al_secondo_max"],
                         dd["secondi_a_zero_consegne"], dd["secondi_di_riga"],
                         dd["scende"], dd["risale"], dd["sopra_soglia"],
                         dd["sotto_soglia"], dd["chiave_ogni_ms"]),
                      flush=True)
    else:
        _dub("registro: %s" % c.get("esito"))

    f = v.get("dove_sono_fermi") or {}
    if f.get("dove"):
        _inf("⭐⭐ DOVE SONO FERMI I FIGLI (%d campioni · %d processi) — ⛔ `ioctl "
             "su /dev/dri/*` = attesa GPU (vaSyncSurface, e TIENE il buffer del "
             "compositore) · `sendto su socket` = contropressione del padre:"
             % (f.get("campioni", 0), len(f.get("processi") or {})))
        for tcomm, d in sorted(f["dove"].items(),
                               key=lambda kv: -sum(kv[1].values()))[:6]:
            tot = sum(d.values())
            righe = sorted(d.items(), key=lambda kv: -kv[1])[:4]
            print("          %-18s %s" % (tcomm,
                  "  ".join("%s %d%%" % (k, round(100.0 * n / tot))
                            for k, n in righe)), flush=True)
    else:
        _dub("dove sono fermi i figli: %s" % f.get("esito", "non letto"))
    ab = v.get("aritmetica_dei_buffer") or aritmetica_dei_buffer(v)
    if ab.get("esito") == "misurato":
        _inf("⭐⭐⭐ ARITMETICA DEI BUFFER: teniamo %.1f ms (conv %.1f + cod %.1f "
             "+ sped %.1f) contro soglia %.1f ms (%d liberi × %.1f) ⇒ ×%.2f  %s"
             % (ab["tenuto_ms"], ab["per_voce_ms"]["conversione"],
                ab["per_voce_ms"]["codifica"], ab["per_voce_ms"]["spedizione"],
                ab["soglia_ms"], ab["buffer_liberi"], ab["periodo_ms"],
                ab["margine"],
                "⛔ OLTRE" if ab["oltre_la_soglia"] else "⭐ sotto"))
    fs = v.get("dove_e_fermo_il_compositore") or {}
    if fs.get("dove"):
        d = fs["dove"].get("gnome-shell") or {}
        tot = sum(d.values()) or 1
        _inf("e il COMPOSITORE (gnome-shell, %d campioni): %s"
             % (fs.get("campioni", 0),
                "  ".join("%s %d%%" % (k, round(100.0 * n / tot))
                          for k, n in sorted(d.items(),
                                             key=lambda kv: -kv[1])[:4])))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I PREDICATI — e ciascuno ha il suo guasto innestato in `--certifica`
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def p_scena_morde(v):
    """⛔ `LEZIONI.md` §1.30: si conta quanta sollecitazione e' ARRIVATA prima di
       dichiarare un risultato.  Qui la sollecitazione e' quel che le scene
       hanno DISEGNATO, che e' l'ingresso — non i fotogrammi consegnati, che
       sono gia' un'uscita del prodotto."""
    d = v.get("disegni_al_secondo")
    if not d:
        return _muto("i disegni delle scene non si sono letti")
    attese = [i for i in range(1, v["quanti"] + 1)
              if v["carico"].get(i, "satura") == "satura"]
    if not attese:
        return _si("nessuna scena satura in questo braccio: niente da pretendere")
    vv = [d.get(i) for i in attese]
    if any(x is None for x in vv):
        return _muto("qualche scena non ha pubblicato i suoi disegni")
    if min(vv) < 5.0:
        return _no("⛔ LA SCENA NON MORDE: la piu' lenta delle sature disegna "
                   "%.1f volte al secondo.  Un giudizio su questi numeri "
                   "sembrerebbe un risultato e non lo sarebbe" % min(vv))
    return _si("le scene sature disegnano %.0f-%.0f volte al secondo"
               % (min(vv), max(vv)))


def p_ripiego_software(v):
    """⛔ La `[?]` 11 di §3.6.  ⚠ E lo ZERO qui e' una risposta: vuol dire che al
       gradino del dirupo **nessuno** era sceso in software, e la pista cade."""
    c = v.get("registro") or {}
    if c.get("esito") != "letto":
        return _muto("il registro non si e' letto: non so dire se qualcuno e' "
                     "ripiegato")
    if c["quanti_ripieghi"]:
        return _no("⛔ %d RIPIEGHI IN SOFTWARE nella finestra: %s — questo "
                   "gradino NON e' un gradino in hardware"
                   % (c["quanti_ripieghi"],
                      json.dumps(c["ripieghi_software"][:3], ensure_ascii=False)))
    return _si("⭐ ZERO ripieghi in software: tutti i figli codificano su "
               "renderD128")


def p_il_figlio_parla(v):
    """⛔⛔ L'ASSENZA DELLE RIGHE E' UN DATO, e distingue due meccanismi opposti.

    `⭐ TRATTO` si scrive dopo ogni spedizione riuscita e `ciclo:` a ogni giro
    del ciclo, una al secondo per figlio.  Se un figlio e' appeso dentro il
    `send()` bloccante verso il padre (`figlio.c:2741`), **tacciono tutt'e due**.
    ⇒ Silenzio = contropressione del padre.  Righe presenti con `conversione`
    alta = attesa sulla GPU.  Sono due cure diverse.
    """
    c = v.get("registro") or {}
    if c.get("esito") != "letto":
        return _muto("il registro non si e' letto")
    t = c.get("tratto_dei_figli") or {}
    cat = c.get("cattura_dei_figli") or {}
    attese = v["quanti"] * v["durata_s"] * 0.5      # meta' delle righe attese
    if not t.get("righe") and not cat.get("righe_ciclo"):
        return _no("⛔⛔ I FIGLI TACCIONO: zero righe «TRATTO» e zero «ciclo:» "
                   "in %d s con %d figli vivi.  Il ciclo del figlio e' fermo "
                   "dentro una chiamata — e l'unica bloccante senza scadenza "
                   "sulla sua strada e' il `send()` verso il padre "
                   "(figlio.c:2741)" % (v["durata_s"], v["quanti"]))
    if cat.get("righe_ciclo", 0) < attese:
        return _no("⛔ IL CICLO DEI FIGLI GIRA MENO DI UNA VOLTA AL SECONDO: %s "
                   "righe «ciclo:» in %d s con %d figli (ne attendevo ~%d).  "
                   "Quella riga si scrive PRIMA di guardare l'esito della "
                   "cattura: se manca, il giro non e' passato di li'"
                   % (cat.get("righe_ciclo"), v["durata_s"], v["quanti"],
                      v["quanti"] * v["durata_s"]))
    return _si("i figli parlano: %s righe «ciclo:» e %s «TRATTO» in %d s"
               % (cat.get("righe_ciclo"), t.get("righe"), v["durata_s"]))


def p_metro_gpu_sano(v):
    g = v.get("chi_tiene_la_gpu") or {}
    if g.get("esito") != "misurato":
        return _muto(g.get("esito", "non misurato"))
    return _si("il metro regge: render in somma %.1f %%, video %.1f %% "
               "(capacita' %s), %d contesti comuni, %d nati, %d morti"
               % (g["somma_render"], g["somma_video"],
                  json.dumps(g["capacita"]), g["contesti_comuni"],
                  g["contesti_nati"], g["contesti_morti"]))


def p_tutte_vive(v):
    morte = [i for i in range(1, v["quanti"] + 1) if not v["vive"].get(i)]
    if v.get("non_so"):
        return _muto("di %s non so dire se sono vive"
                     % ", ".join("s%d" % i for i in v["non_so"]))
    if morte:
        return _no("⛔ %s NON sono vive: la popolazione di questo gradino non e' "
                   "quella che dichiara" % ", ".join("s%d" % i for i in morte))
    return _si("tutte e %d le sessioni sono vive" % v["quanti"])


def p_i_byte_confermano_la_scena(v):
    """⛔ «Sature» non e' un'etichetta che scrivo io: si smaschera dai BYTE.

    ⚠ Una sessione che consegna pochi fotogrammi **e pochi byte a fotogramma**
      non stava saturando niente: stava guardando un desktop quasi fermo, e
      contarla fra le sature gonfia il carico dichiarato.  `[M]` §6.5: la scena
      satura vale ~5 600 byte/fotogramma, quella leggera 2 448.
    """
    sature = [i for i in range(1, v["quanti"] + 1)
              if v["carico"].get(i, "satura") == "satura"]
    if not sature:
        return _si("nessuna sessione dichiarata satura in questo braccio")
    magre, muti = [], []
    for i in sature:
        f = v["sessioni"].get(i) or {}
        b = f.get("byte_per_fotogramma") if isinstance(f, dict) else None
        if b is None:
            muti.append(i)
        elif b < 1500:
            magre.append((i, b))
    if muti and not magre:
        return _muto("di %s non ho letto i byte per fotogramma"
                     % ", ".join("s%d" % i for i in muti))
    if magre:
        return _no("⛔ %s sono dichiarate SATURE e consegnano %s byte per "
                   "fotogramma: non stavano saturando niente"
                   % (", ".join("s%d" % i for i, _b in magre),
                      ", ".join(str(b) for _i, b in magre)))
    return _si("le %d sature consegnano fra %d e %d byte per fotogramma"
               % (len(sature),
                  min(v["sessioni"][i]["byte_per_fotogramma"] for i in sature),
                  max(v["sessioni"][i]["byte_per_fotogramma"] for i in sature)))


# ⛔ Le famiglie in cui si raggruppano le chiamate campionate, e ciascuna e' una
#    DIAGNOSI diversa.  ⚠ Si dichiarano qui, non a occhio dentro il predicato:
#    un raggruppamento fatto guardando i numeri e' un raggruppamento scelto dopo.
FAMIGLIE = (
    ("attesa GPU (vaSyncSurface, e TIENE il buffer del compositore)",
     lambda k: k.startswith("ioctl") and "/dev/dri" in k),
    ("contropressione del padre (send bloccante, figlio.c:2741)",
     lambda k: k.startswith(("sendto", "sendmsg", "write")) and "socket" in k),
    ("si aspetta qualcosa che non arriva (poll/futex)",
     lambda k: k.startswith(("ppoll", "poll", "epoll", "futex", "select",
                             "pselect"))),
    ("dorme a tempo (nanosleep)",
     lambda k: k.startswith(("nanosleep", "clock_nanosleep"))),
    ("in esecuzione o non bloccato",
     lambda k: k.startswith("(")),
)


def famiglie_di(dove):
    """Dal conto per chiamata al conto per DIAGNOSI.  ⛔ Quel che non rientra in
       nessuna famiglia si conta a parte e si dichiara: metterlo in «altro» e
       tacerlo sarebbe nascondere proprio il caso che non avevo previsto."""
    fuori = dict((nome, 0) for nome, _f in FAMIGLIE)
    fuori["⚠ non classificate"] = 0
    dettaglio = {}
    for _tcomm, d in dove.items():
        for k, n in d.items():
            dettaglio[k] = dettaglio.get(k, 0) + n
            for nome, f in FAMIGLIE:
                if f(k):
                    fuori[nome] += n
                    break
            else:
                fuori["⚠ non classificate"] += n
    return fuori, dettaglio


def p_dove_sono_fermi(v):
    """⭐⭐⭐ IL PREDICATO CENTRALE DI QUESTO BANCO.

    ⛔ Non giudica il prodotto: giudica se **ho una diagnosi**.  Un campione che
       non trova nessun figlio, o che non riesce a leggere nessun thread, non e'
       «i figli non stanno aspettando niente»: e' un buco, e va detto.
    """
    f = v.get("dove_sono_fermi") or {}
    if not f.get("dove"):
        return _muto("il campione non si e' letto: %s"
                     % f.get("esito", "nessuna voce"))
    if not f.get("processi"):
        return _no("⛔ il campione non ha trovato NESSUN figlio con %d sessioni "
                   "vive: o il modello non combacia col `comm`, o i figli non "
                   "ci sono — e le due cose hanno bisogno di due cure diverse"
                   % v["quanti"])
    fam, _dett = famiglie_di(f["dove"])
    tot = sum(fam.values())
    if tot == 0:
        return _muto("nessun thread letto in %d campioni" % f.get("campioni", 0))
    if fam["⚠ non classificate"] > tot * 0.5:
        return _muto("⛔ piu' della meta' dei campioni (%d su %d) non rientra in "
                     "nessuna famiglia dichiarata: non ho una diagnosi, ho un "
                     "elenco" % (fam["⚠ non classificate"], tot))
    prima = max(((n, k) for k, n in fam.items() if n), default=(0, "?"))
    return _si("diagnosi dai %d campioni su %d figli: la famiglia piu' grossa e' "
               "«%s» col %d %% dei thread bloccati"
               % (f.get("campioni", 0), len(f["processi"]), prima[1],
                  round(100.0 * prima[0] / tot)))



# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ L'ARITMETICA DEI BUFFER — la soglia che il PRODOTTO saprebbe calcolare
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Letto nel codice, non nei commenti:
#
#   1. `cattura.c:586` chiede **6** buffer sulla strada della scheda (minimo 4,
#      massimo 8).  ⚠ E' un MINIMO CHIESTO, non un ordine: quanti ne dia
#      davvero il produttore lo dice `buffer_distinti`, che si CONTA.
#   2. Ne teniamo al massimo **due**, e lo dice la struttura, non un commento:
#      `cattura->posto` e' UNA casella sola e chi arriva rende subito quello che
#      trova (`cattura.c:1160-1165`); `cattura_prendi()` porta via il fotogramma
#      dalla casella (`:2054`) e chi consuma lo rende in `cattura_fermo_libera()`
#      (`:2197`).  ⇒ uno nella casella, uno in mano a chi legge.
#   3. ⛔⛔ E IL RILASCIO ARRIVA **DOPO TUTTO** `codifica_e_manda()` —
#      `figlio.c:7763`, e il commento accanto lo vuole li' apposta: *«si chiama
#      DOPO la codifica… spostarla di due righe piu' in su rimetterebbe in piedi
#      le due schermate che si alternano»*.  ⇒ La finestra in cui il buffer di
#      Mutter e' NOSTRO non e' la sola conversione: e' **conversione + codifica
#      + spedizione**, cioe' tre voci del TRATTO, e la spedizione e' un `send()`
#      bloccante (`figlio.c:2741`).
#
# ⇒ ⭐ LA DISUGUAGLIANZA: finche' teniamo un buffer per meno di
#
#         (buffer_liberi) × (periodo del fotogramma)
#
#   il compositore ha sempre qualcosa da riempire.  Appena la superiamo, resta
#   **senza buffer**, smette di comporre, e senza composizione non arriva niente
#   da codificare: l'anello si morde la coda, e ci si entra sopra una soglia e
#   non se ne esce.
#
# ⭐⭐ E il numero a destra e' una cosa che il PRODOTTO SA CALCOLARE — buffer
#     negoziati, buffer trattenuti, cadenza chiesta — mentre «otto sessioni» non
#     lo e': dipende dal ferro e dalla scena.  ⇒ Se il conto regge, il tetto da
#     scrivere nel codice e' questa disuguaglianza, non il numero sei.
#
# ⚠ E i limiti si dichiarano: `MOVIMENTO_FPS` e' 60 (`figlio.c:3228`), ed e' la
#   cadenza CHIESTA a Mutter, non quella che consegna; se `buffer_distinti` non
#   si e' letto si usa 6 e ⛔ **si marca l'assunzione**, invece di spacciarla.
MOVIMENTO_FPS = 60          # figlio.c:3228, la cadenza chiesta a Mutter
BUFFER_CHIESTI = 6          # cattura.c:586, minimo 4 massimo 8
BUFFER_TRATTENUTI = 2       # cattura.c: la casella + chi consuma
VOCI_TENUTA = ("conversione", "codifica", "spedizione")


def aritmetica_dei_buffer(v):
    """I due lati della disuguaglianza, o `None` con la ragione."""
    c = v.get("registro") or {}
    if c.get("esito") != "letto":
        return {"esito": "⛔ NON HO LETTO — il registro non si e' letto"}
    t = c.get("tratto_dei_figli") or {}
    if not t.get("righe"):
        return {"esito": "⛔ NON HO LETTO — nessuna riga «TRATTO»: senza quella "
                         "non so quanto teniamo il buffer.  ⚠ E l'assenza e' a "
                         "sua volta un dato: quella riga si scrive dopo ogni "
                         "spedizione riuscita"}
    voci = t.get("voci") or {}
    mancano = [k for k in VOCI_TENUTA if k not in voci]
    if mancano:
        return {"esito": "⛔ NON DICHIARO — mancano le voci %s del TRATTO"
                         % ", ".join(mancano)}
    tenuto = sum(voci[k]["mediana_ms"] for k in VOCI_TENUTA)
    tenuto_max = sum(voci[k]["max_ms"] for k in VOCI_TENUTA)
    b = c.get("buffer_di_pipewire") or {}
    distinti = (b.get("buffer_distinti") or [None])[-1]
    assunto = distinti is None
    quanti = BUFFER_CHIESTI if assunto else distinti
    liberi = max(0, quanti - BUFFER_TRATTENUTI)
    periodo = 1000.0 / MOVIMENTO_FPS
    soglia = liberi * periodo
    return {"esito": "misurato",
            "tenuto_ms": round(tenuto, 2), "tenuto_max_ms": round(tenuto_max, 2),
            "per_voce_ms": dict((k, voci[k]["mediana_ms"]) for k in VOCI_TENUTA),
            "buffer_totali": quanti, "buffer_assunti": assunto,
            "buffer_trattenuti": BUFFER_TRATTENUTI, "buffer_liberi": liberi,
            "periodo_ms": round(periodo, 2), "soglia_ms": round(soglia, 2),
            "oltre_la_soglia": tenuto > soglia,
            "margine": (None if soglia <= 0 else round(tenuto / soglia, 3))}


def p_aritmetica_dei_buffer(v):
    d = aritmetica_dei_buffer(v)
    v["aritmetica_dei_buffer"] = d
    if d["esito"] != "misurato":
        return _muto(d["esito"])
    come = ("⚠ buffer ASSUNTI a %d (cattura.c:586): il produttore non ha detto "
            "quanti ne da'" % d["buffer_totali"]) if d["buffer_assunti"] else \
           ("buffer CONTATI: %d" % d["buffer_totali"])
    frase = ("teniamo il buffer di Mutter %.1f ms (conversione %.1f + codifica "
             "%.1f + spedizione %.1f) contro una soglia di %.1f ms "
             "(%d liberi × %.1f ms) — ×%.2f della soglia · %s"
             % (d["tenuto_ms"], d["per_voce_ms"]["conversione"],
                d["per_voce_ms"]["codifica"], d["per_voce_ms"]["spedizione"],
                d["soglia_ms"], d["buffer_liberi"], d["periodo_ms"],
                d["margine"], come))
    if d["oltre_la_soglia"]:
        return _no("⛔⛔ OLTRE LA SOGLIA DEI BUFFER: " + frase
                   + ".  ⇒ Il compositore resta senza buffer da riempire e "
                     "SMETTE DI COMPORRE: senza composizione non arriva niente "
                     "da codificare (figlio.c:7763, il rilascio dopo TUTTA la "
                     "codifica e la spedizione)")
    return _si("sotto la soglia dei buffer: " + frase)


PREDICATI = [("la scena morde", p_scena_morde),
             ("ho una diagnosi di dove sono fermi", p_dove_sono_fermi),
             ("l'aritmetica dei buffer", p_aritmetica_dei_buffer),
             ("i byte confermano la scena", p_i_byte_confermano_la_scena),
             ("nessun ripiego in software", p_ripiego_software),
             ("i figli parlano", p_il_figlio_parla),
             ("il metro della GPU e' sano", p_metro_gpu_sano),
             ("la popolazione e' quella dichiarata", p_tutte_vive)]


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL RIVELATORE DEL DIRUPO — e deve saper dire «NESSUN DIRUPO»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ Un rivelatore che trovasse un dirupo dovunque non varrebbe niente quando ne
#    trova uno.  ⇒ La definizione e' scritta, non a occhio: fra due gradini
#    consecutivi c'e' un DIRUPO se il ritmo AGGREGATO (la somma dei fot/s di
#    tutte le sessioni) cade di almeno `CADUTA_DIRUPO` volte.
# ⚠ Sull'aggregato e non sul per-sessione, e la ragione e' aritmetica: passando
#   da N a N+1 sessioni il per-sessione cala di 1/(N+1) **anche quando non
#   succede niente di male**, perche' la stessa torta si divide fra piu' gente.
#   L'aggregato invece resta piatto se la macchina e' satura, e cade solo se si
#   e' rotto qualcosa.
CADUTA_DIRUPO = 3.0


def misurate(v):
    """{indice: fot/s} delle sole sessioni che si sono MISURATE."""
    if v is None:
        return {}
    fuori = {}
    for i in range(1, v["quanti"] + 1):
        f = _fps(v["sessioni"].get(i))
        if f is not None:
            fuori[i] = f
    return fuori


def aggregato(v):
    """⚠ La somma dei fot/s delle sessioni MISURATE, col loro numero accanto.

    ⛔ La prima stesura tornava `None` appena una sessione non si misurava — «un
       aggregato con un buco dentro non e' un totale» — e la regola e' giusta,
       ma `[M]` il 25 agosto 2026 ha morso dalla parte sbagliata: cinque
       sessioni su otto erano state SFRATTATE dal prodotto a meta' giro, quindi
       OGNI gradino aveva un buco, l'aggregato era `None` dappertutto e il
       verdetto sul dirupo non e' mai uscito — ⛔ **e i due bracci di controllo
       sono stati saltati**, con il banco che diceva «non ho ritrovato il
       dirupo» mentre il dirupo era li' sotto gli occhi.
    ⇒ Il totale si dichiara CON QUANTE sessioni e' fatto, e il confronto fra due
      gradini si fa **a coppie** (vedi `rileva_dirupo`), non fra due totali di
      popolazioni diverse.
    """
    m = misurate(v)
    return (sum(m.values()), len(m)) if m else (None, 0)


def rileva_dirupo(gradini):
    """⛔⛔ IL CONFRONTO E' A COPPIE, sulle sessioni presenti in TUTT'E DUE i
       gradini — non fra due totali.

    ⚠ Due ragioni, e sono tutt'e due state pagate:
      1. passando da N a N+1 sessioni il per-sessione cala di 1/(N+1) **anche
         quando non succede niente di male**: confrontare i per-sessione senza
         appaiarli chiamerebbe «dirupo» la torta divisa fra piu' gente;
      2. e la popolazione MISURATA cambia da sola quando il prodotto sfratta
         qualcuno a meta' giro (`[M]` 25 agosto 2026): confrontare due totali
         fatti con un numero diverso di sessioni misura il cambio di
         popolazione, non il fenomeno.
    ⇒ Si prendono le sessioni misurate in tutt'e due, si fa la MEDIA dei loro
      fot/s in ciascuno, e si guarda il rapporto.  ⭐ E' un confronto appaiato:
      le stesse sessioni, prima e dopo.
    """
    punti = []
    for v in gradini:
        m = misurate(v)
        tot, quante = aggregato(v)
        punti.append({"nome": v["nome"], "sessioni": v["quanti"],
                      "misurate": quante, "aggregato": tot, "per_sessione": m})
    peggio, dove = None, None
    coppie_mute = []
    for a, b in zip(punti, punti[1:]):
        comuni = sorted(set(a["per_sessione"]) & set(b["per_sessione"]))
        if not comuni:
            coppie_mute.append("%s→%s (nessuna sessione misurata in tutt'e due)"
                               % (a["nome"], b["nome"]))
            continue
        ma = sum(a["per_sessione"][i] for i in comuni) / len(comuni)
        mb = sum(b["per_sessione"][i] for i in comuni) / len(comuni)
        r = float("inf") if mb <= 0 else ma / mb
        if peggio is None or r > peggio:
            peggio, dove = r, (a["nome"], b["nome"], round(ma, 2),
                               round(mb, 2), comuni)
    if peggio is None:
        return {"esito": "⛔ NON GIUDICO — nessuna coppia di gradini ha "
                         "sessioni misurate in comune: %s"
                         % " · ".join(coppie_mute) or "meno di due gradini",
                "punti": punti}
    detto_comuni = ", ".join("s%d" % i for i in dove[4])
    fuori = {"caduta_peggiore": round(peggio, 2), "dove": dove[:4],
             "sessioni_appaiate": dove[4], "punti": punti,
             "coppie_mute": coppie_mute}
    if peggio < CADUTA_DIRUPO:
        fuori["esito"] = "nessun dirupo"
        fuori["detto"] = ("⭐ NESSUN DIRUPO: la caduta peggiore fra due gradini "
                          "consecutivi, sulle STESSE sessioni (%s), e' ×%.2f "
                          "(«%s»→«%s», %.1f → %.1f fot/s a testa), sotto la "
                          "soglia ×%.1f"
                          % (detto_comuni, peggio, dove[0], dove[1], dove[2],
                             dove[3], CADUTA_DIRUPO))
    else:
        fuori["esito"] = "DIRUPO"
        fuori["detto"] = ("⛔⛔ DIRUPO fra «%s» e «%s»: le STESSE sessioni (%s) "
                          "passano da %.1f a %.1f fot/s a testa, ×%.2f"
                          % (dove[0], dove[1], detto_comuni, dove[2], dove[3],
                             peggio))
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ UNA CURA SPENTA CHE NON SI E' SPENTA DAVVERO — `CODER.md` §2-bis
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Non si verifica dal comando che ho scritto io: si verifica **dal binario
#    che gira** e dalla **riga che il server ha scritto all'avvio**.  ⚠ Le cure
#    della fase 9 NASCONO ACCESE: un `--sgombra-soglia-ms 0` che non arriva
#    all'`ExecStart` non da' nessun errore — da' un braccio di controllo che
#    misura la stessa cosa del braccio normale, cioe' un confronto fra due
#    copie della stessa configurazione.
def cure_verificate(soglia_attesa_accesa, ritmo_atteso_acceso):
    """⛔⛔ SI VERIFICA DAL BINARIO CHE GIRA E DALLA RIGA D'AVVIO, non dal
       comando che ho scritto io (`CODER.md` §2-bis).

    ⚠ Le cure della fase 9 NASCONO ACCESE.  Un `--sgombra-soglia-ms 0` che non
      arriva all'`ExecStart` non da' nessun errore: da' un braccio di controllo
      che misura **la stessa configurazione** del braccio normale, cioe' un
      confronto fra due copie della stessa cosa.  ⛔ E il risultato somiglia in
      tutto a «la cura non c'entra».
    ⇒ Due testimoni indipendenti, e devono concordare: la riga di comando del
      PROCESSO (`/proc/<pid>/cmdline`) e la riga che il SERVER ha scritto nel
      registro all'avvio.  Se discordano, `None`: non so in che stato ho
      misurato.
    """
    rc, cmd, _ = B92.root(
        "P=$(systemctl show -p MainPID --value %s.service); "
        "tr '\\0' ' ' < /proc/$P/cmdline 2>/dev/null || true" % B92.UNITA)
    rc2, righe, _ = B92.root(
        "grep -a 'soglia della coda video (§5.1)\\|il regolatore del ritmo e.\\|"
        "IL REGOLATORE DEL RITMO' %s/registro.log | tail -4" % B92.LAV)
    fuori = {"riga_d_avvio": " ".join(cmd.split())[-400:],
             "righe_del_registro": righe.strip().splitlines()[-2:]}
    if not cmd.strip():
        fuori["esito"] = "⛔ NON HO LETTO — la riga d'avvio del processo"
        return None, fuori
    if not righe.strip():
        fuori["esito"] = ("⛔ NON HO LETTO — il server non ha scritto nessuna "
                          "riga sullo stato delle cure")
        return None, fuori
    argv = " ".join(cmd.split())
    guai = []
    for nome, atteso, opzione, acceso_reg, spento_reg in (
            ("soglia della coda", soglia_attesa_accesa, "--sgombra-soglia-ms 0",
             "100 ms — ACCESA", "0 ms — SPENTA"),
            ("regolatore del ritmo", ritmo_atteso_acceso,
             "--niente-ritmo-adattivo", "ritmo e' ACCESO", "SPENTO")):
        in_argv = opzione in argv
        # ⛔ La riga del registro e' il secondo testimone, e deve concordare.
        dal_registro = None
        for r in righe.splitlines():
            if acceso_reg in r:
                dal_registro = True
            elif spento_reg in r:
                dal_registro = False
        if atteso and in_argv:
            guai.append("«%s» doveva restare ACCESA e nella riga d'avvio c'e' "
                        "«%s»" % (nome, opzione))
        if (not atteso) and (not in_argv):
            guai.append("«%s» doveva essere SPENTA e «%s» NON c'e' nella riga "
                        "d'avvio del processo" % (nome, opzione))
        if dal_registro is None:
            fuori.setdefault("non_confermate", []).append(nome)
        elif dal_registro != atteso:
            guai.append("«%s»: mi aspettavo %s e il REGISTRO del server dice %s "
                        "— i due testimoni discordano"
                        % (nome, "accesa" if atteso else "spenta",
                           "accesa" if dal_registro else "spenta"))
        fuori[nome] = {"atteso_acceso": atteso, "opzione_in_argv": in_argv,
                       "dal_registro_acceso": dal_registro}
    if fuori.get("non_confermate") and not guai:
        fuori["esito"] = ("⛔ NON SO — il registro non conferma lo stato di %s"
                          % ", ".join(fuori["non_confermate"]))
        return None, fuori
    if guai:
        fuori["esito"] = "⛔ " + " · ".join(guai)
        return False, fuori
    fuori["esito"] = ("le due cure sono nello stato che dichiaro (soglia %s, "
                      "ritmo %s), e lo dicono TUTT'E DUE i testimoni: la riga "
                      "d'avvio del processo e il registro del server"
                      % ("accesa" if soglia_attesa_accesa else "SPENTA",
                         "acceso" if ritmo_atteso_acceso else "SPENTO"))
    return True, fuori


def ancora_avanza(gradini):
    """⛔ IL GRADINO LETTO DAL PRECEDENTE — il difetto che in fase 9 ha fatto
       riferire a tre profili di fila gli stessi identici numeri.  ⭐ Il confine
       di un gradino deve stare DOPO la fine del precedente, e si guarda invece
       di darlo per scontato."""
    guai = []
    for a, b in zip(gradini, gradini[1:]):
        if b["t0"] <= a["t1"]:
            guai.append("«%s» comincia a %.0f e «%s» finiva a %.0f"
                        % (b["nome"], b["t0"], a["nome"], a["t1"]))
    if guai:
        return False, ("⛔⛔ L'ANCORA NON AVANZA: %s — quei gradini hanno letto "
                       "i fotogrammi del precedente" % " · ".join(guai))
    return True, "l'ancora avanza a ogni gradino: nessuna finestra si sovrappone"


def giudica(v):
    esiti = []
    for nome, f in PREDICATI:
        try:
            passa, perche = f(v)
        except Exception as e:
            passa, perche = None, "⛔ il predicato e' alzato: %s: %s" % (
                type(e).__name__, e)
        (_ok if passa else (_dub if passa is None else _ko))(
            "%s — %s" % (nome, perche))
        esiti.append({"predicato": nome, "esito": passa, "perche": perche})
    v["predicati"] = esiti
    return esiti


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA POPOLAZIONE — e il carico si cambia SENZA cambiare la popolazione
# ═══════════════════════════════════════════════════════════════════════════
def spegni_scena_di(i):
    B92.root("pkill -u %d -f 04-b30-scena; true" % B92.uid(i))
    time.sleep(1.5)


def accendi_scena_in_finestra(i, misura="960x540"):
    """⭐ La stessa scena, la stessa strada, **meno pixel**: `--finestra` invece
       dello schermo intero.  ⛔ E' il braccio che sposta il carico senza
       toccare ne' il numero di sessioni ne' il numero di desktop."""
    n = B92.uid(i)
    usc = B92.uscita_del(i)
    if not usc:
        return None
    log = "%s/scena-%d.log" % (B92.LAV, i)
    B92.root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
             "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
             "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
             "%s --uscita %s --movimento pieno --finestra %s --shm /%s "
             "--giro b9d-%d >> %s 2>&1 & echo acceso"
             % (n, n, B92.utente(i), B92.utente(i), n, B92.SCENA_BIN, usc,
                misura, B92.shm_di(i), i, log))
    time.sleep(2.5)
    rc, out, _ = B92.root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % n)
    return usc if out.strip() else None


# ═══════════════════════════════════════════════════════════════════════════
def giro(a):
    esiti = {"passo": "giro", "da": a.da, "a": a.a, "durata_s": a.durata,
             "porta": B92.PORTA, "albero": B92.ALB, "gradini": []}
    resta = (a.a - a.da + 6) * (a.durata + B92.ASSESTAMENTO_S + 60) + 900

    # ⛔⛔ PRIMA DI TUTTO: IN CHE STATO SONO LE CURE?  `CODER.md` §2-bis.
    #     ⚠ Un braccio di controllo che non ha spento quel che dice di aver
    #       spento non da' errore: da' un numero uguale al braccio normale, e
    #       chi legge conclude «la cura non c'entra».
    _log("⛔ le due cure della fase 9 — dal PROCESSO e dal REGISTRO, non dal "
         "comando che ho scritto")
    stato, dettaglio = cure_verificate(not a.soglia_spenta, not a.ritmo_spento)
    esiti["cure"] = dettaglio
    if stato is False:
        _ko(dettaglio["esito"])
        _inf("riga d'avvio: %s" % dettaglio["riga_d_avvio"][-200:])
        return 2
    if stato is None:
        _dub(dettaglio["esito"])
        _inf("riga d'avvio: %s" % dettaglio["riga_d_avvio"][-200:])
        return 2
    _ok(dettaglio["esito"])

    _log("⛔ prima di misurare, i palchi del giro precedente si CHIUDONO")
    B92.chiudi_palchi(a.a + 1)
    if not B92.terreno(a.a):
        return 2

    aperte = 0
    try:
        # ── la salita fino al gradino del dirupo ─────────────────────────
        for g in range(1, a.a + 1):
            _log("apro s%d (%s)" % (g, B92.utente(g)))
            t0 = time.time()
            ok, detto = B92.apri_sessione(g, resta)
            if not ok:
                _ko("⛔ s%d non si apre: %s" % (g, detto))
                esiti["fermata_al"] = g
                break
            aperte = g
            _ok("s%d aperta in %d ms" % (g, int(1000 * (time.time() - t0))))
            if not B92.accendi_scena(g):
                _ko("⛔ la scena di s%d non parte" % g)
            if g < a.da:
                continue
            v = gradino("%dS" % g, g, a.durata,
                        dict((i, "satura") for i in range(1, g + 1)))
            if v:
                giudica(v)
                esiti["gradini"].append(v)

        # ── ⭐⭐ I BRACCI FINI: stessa popolazione, carico diverso ────────
        if a.fine and aperte >= a.a:
            _log("⭐⭐ I BRACCI FINI — %d sessioni SEMPRE, e cambia SOLO il "
                 "carico.  ⛔ Se il confine cade su una grandezza continua e "
                 "non sul numero di sessioni, quella e' meta' della risposta"
                 % a.a)
            carico = dict((i, "satura") for i in range(1, a.a + 1))

            spegni_scena_di(a.a)
            carico[a.a] = "ferma"
            v = gradino("%dS+1F" % (a.a - 1), a.a, a.durata, dict(carico))
            if v:
                giudica(v)
                esiti["gradini"].append(v)

            spegni_scena_di(a.a - 1)
            carico[a.a - 1] = "ferma"
            v = gradino("%dS+2F" % (a.a - 2), a.a, a.durata, dict(carico))
            if v:
                giudica(v)
                esiti["gradini"].append(v)

            # ⭐ e adesso una che chiede MENO PIXEL invece di zero
            if accendi_scena_in_finestra(a.a - 1):
                carico[a.a - 1] = "finestra 960x540"
            if accendi_scena_in_finestra(a.a):
                carico[a.a] = "finestra 960x540"
            v = gradino("%dS+2W" % (a.a - 2), a.a, a.durata, dict(carico))
            if v:
                giudica(v)
                esiti["gradini"].append(v)

            # ⛔⛔ L'ANCORA IN CODA: si rimettono le scene sature e si deve
            #     ritrovare il numero del primo braccio.  Senza, un braccio
            #     buono potrebbe essere solo la macchina che si e' raffreddata.
            for i in (a.a - 1, a.a):
                B92.root("pkill -u %d -f 04-b30-scena; true" % B92.uid(i))
                time.sleep(1.0)
                B92.accendi_scena(i)
                carico[i] = "satura"
            v = gradino("%dS (ancora in coda)" % a.a, a.a, a.durata, dict(carico))
            if v:
                giudica(v)
                esiti["gradini"].append(v)
    finally:
        # ⛔ Il riassunto PRIMA di scrivere il file, o il verdetto sul dirupo e
        #    quello sull'ancora non finirebbero dentro gli esiti.
        try:
            riassunto(esiti)
        except Exception as e:
            _ko("⛔ il riassunto e' alzato: %s: %s" % (type(e).__name__, e))
        os.makedirs(B92.FUORI, exist_ok=True)
        dove = os.path.join(B92.FUORI, "10-b9d-%s.json" % (a.etichetta or "giro"))
        with open(dove, "w") as f:
            json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
        _inf("esiti in %s" % dove)
    return 0


def riassunto(esiti):
    _log("⭐ IL RIASSUNTO — una riga per gradino")
    print("  %-22s %5s %8s %8s %8s %8s %8s %8s"
          % ("gradino", "sess", "fot/s tot", "render", "video", "disegni/s",
             "TRATTO", "conversi."), flush=True)
    for v in esiti["gradini"]:
        n = v["quanti"]
        fps = [_fps(v["sessioni"].get(i)) for i in range(1, n + 1)]
        vivi = [x for x in fps if x is not None]
        g = v.get("chi_tiene_la_gpu") or {}
        d = v.get("macchina") or {}
        dd = [x for x in (v.get("disegni_al_secondo") or {}).values()
              if x is not None]
        c = v.get("registro") or {}
        t = (c.get("tratto_dei_figli") or {})
        tot = t.get("totale", {}).get("mediana_ms") if t.get("righe") else None
        cv = (t.get("voci", {}).get("conversione") or {}).get("mediana_ms") \
            if t.get("righe") else None
        print("  %-22s %5d %8s %8s %8s %8s %8s %8s"
              % (v["nome"], n,
                 "%.1f" % sum(vivi) if vivi else "None",
                 (d.get("gpu_pc") or {}).get("render"),
                 (d.get("gpu_pc") or {}).get("video"),
                 round(sum(dd), 1) if dd else "None",
                 tot if tot is not None else "None",
                 cv if cv is not None else "None"), flush=True)
    if len(esiti["gradini"]) >= 2:
        d = rileva_dirupo(esiti["gradini"])
        esiti["dirupo"] = d
        (_ko if d["esito"] == "DIRUPO" else
         (_dub if d["esito"].startswith("⛔") else _ok))(
            d.get("detto", d["esito"]))
        ok, perche = ancora_avanza(esiti["gradini"])
        esiti["ancora"] = {"esito": ok, "perche": perche}
        (_ok if ok else _ko)(perche)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL MODO `--certifica` — un banco non e' finito finche' non l'hai visto
#     dare ROSSO (`LEZIONI.md` §1.29).  Qui NON si tocca la macchina di prova.
# ═══════════════════════════════════════════════════════════════════════════
def _finta_fotografia(t_ms, contesti, capacita=None):
    return {"t_ms": t_ms,
            "chi_tiene": {"t_ms": t_ms, "per_contesto": contesti,
                          "capacita": capacita or {"render": 1, "video": 2}}}


def _gradino_finto(quanti=8, durata=40, fps=38.0, disegni=60.0,
                   ripieghi=0, righe_ciclo=None, tratto=True,
                   conversione=3.0, vive=None, byte=5600):
    if righe_ciclo is None:
        righe_ciclo = quanti * durata
    voci = {}
    for k, x in (("produttore", 2.0), ("nel posto", 1.0),
                 ("conversione", conversione), ("codifica", 3.0),
                 ("spedizione", 0.4)):
        voci[k] = {"righe": 10, "mediana_ms": x, "min_ms": x, "max_ms": x}
    reg = {"esito": "letto", "quanti_ripieghi": ripieghi,
           "ripieghi_software": [{"chiesto": "h264_vaapi",
                                  "ripiego": "libx264"}] * ripieghi,
           "ritmo_scende_in_tutto": 0, "ritmo_risale_in_tutto": 0,
           "sopra_soglia_in_tutto": 0, "sotto_soglia_in_tutto": 0,
           "abbandoni_in_coda": 0, "involo_pieno": 0,
           "altri_conti": {"ricodifica": 0}, "per_provenienza": {},
           "cattura_dei_figli": {"serie": quanti, "righe_ciclo": righe_ciclo,
                                 "fotogrammi_catturati": 100,
                                 "attese_a_vuoto": 10, "guasti": 0},
           "tratto_dei_figli": ({"righe": righe_ciclo,
                                 "totale": {"mediana_ms": sum(
                                     v["mediana_ms"] for v in voci.values())},
                                 "voci": voci} if tratto
                                else {"esito": "⛔ NON HO LETTO — nessuna riga"})}
    return {"nome": "finto", "quanti": quanti, "durata_s": durata,
            "carico": dict((i, "satura") for i in range(1, quanti + 1)),
            "sessioni": dict((i, {"esito": "misurato", "fps": fps,
                                  "byte_per_fotogramma": byte}
                              if byte is not None
                              else {"esito": "misurato", "fps": fps})
                             for i in range(1, quanti + 1)),
            "disegni_al_secondo": dict((i, disegni) for i in range(1, quanti + 1)),
            "macchina": {"gpu_pc": {"render": 99.5, "video": 1.6},
                         "gt": {}, "gpu_capacita": {"video": 2}},
            "chi_tiene_la_gpu": {"esito": "misurato", "somma_render": 99.5,
                                 "somma_video": 1.6, "capacita": {"video": 2},
                                 "contesti_comuni": 20, "contesti_nati": 0,
                                 "contesti_morti": 0,
                                 "per_programma": {"gnome-shell":
                                                   {"render": 90.0, "video": 0.0,
                                                    "contesti": 8, "pid": 8}}},
            "vive": vive or dict((i, True) for i in range(1, quanti + 1)),
            "scene": dict((i, True) for i in range(1, quanti + 1)),
            "non_so": [], "registro": reg,
            "dove_sono_fermi": {"campioni": 14,
                                "processi": dict((str(i), "remotix-figlio")
                                                 for i in range(quanti)),
                                "dove": {"remotix-figlio":
                                         {"ioctl su /dev/dri/*": 40,
                                          "ppoll": 60}}}}


def certifica():
    _log("⛔⛔ `--certifica` — sano → guasto → risanato, e NON si tocca la "
         "macchina di prova")
    casi = []

    def prova(nome, v, quale, atteso):
        f = dict(PREDICATI)[quale]
        passa, perche = f(v)
        ok = (passa is atteso) if atteso is None else (passa == atteso)
        casi.append((nome, quale, atteso, passa, ok, perche))
        (_ok if ok else _ko)("%-46s  «%s» → %s (atteso %s)"
                             % (nome, quale, passa, atteso))

    # ── 1. il sano ───────────────────────────────────────────────────────
    sano = _gradino_finto()
    for nome, _f in PREDICATI:
        prova("SANO · " + nome, sano, nome, True)

    # ── 2. ⛔ il RIPIEGO IN SOFTWARE innestato apposta ────────────────────
    #    Se il rivelatore non lo trova quando c'e', non vale niente quando dice
    #    che non c'e'.  ⭐ E' la prova che l'incarico chiede per nome.
    prova("GUASTO · una sessione forzata in CPU",
          _gradino_finto(ripieghi=1), "nessun ripiego in software", False)
    prova("GUASTO · tre sessioni in CPU",
          _gradino_finto(ripieghi=3), "nessun ripiego in software", False)
    prova("RISANATO · zero ripieghi",
          _gradino_finto(ripieghi=0), "nessun ripiego in software", True)

    # ── 3. ⛔ i figli che TACCIONO (send bloccante) ───────────────────────
    prova("GUASTO · i figli tacciono del tutto",
          _gradino_finto(righe_ciclo=0, tratto=False), "i figli parlano", False)
    prova("GUASTO · il ciclo gira meno di 1 volta/s",
          _gradino_finto(righe_ciclo=40), "i figli parlano", False)
    prova("RISANATO · una riga al secondo per figlio",
          _gradino_finto(righe_ciclo=320), "i figli parlano", True)

    # ── 4. ⛔ la SCENA CHE NON MORDE — smascherata dai disegni ────────────
    prova("GUASTO · dieci schermi fermi contati come al lavoro",
          _gradino_finto(disegni=0.4), "la scena morde", False)
    prova("GUASTO · i disegni non si sono letti ⇒ None, non zero",
          _gradino_finto(disegni=None), "la scena morde", None)
    prova("RISANATO · le scene disegnano",
          _gradino_finto(disegni=59.0), "la scena morde", True)

    # ── 5. ⛔ una sessione morta a meta' ──────────────────────────────────
    m = dict((i, True) for i in range(1, 9))
    m[7] = False
    prova("GUASTO · una sessione morta dentro il gradino",
          _gradino_finto(vive=m), "la popolazione e' quella dichiarata", False)

    # ── 6. ⛔ il METRO DELLA GPU: i tre modi in cui mente ─────────────────
    _log("⛔ il metro della GPU per programma — tarato con valori NOTI "
         "(`LEZIONI.md` §1.33)")
    # ⭐ Taratura: due fotografie a 10 s con 2,00 s di render iniettati ⇒ 20,00 %
    a = _finta_fotografia(0.0, {"1": {"chi": "gnome-shell", "pid": 11,
                                      "render": 0, "video": 0},
                                "2": {"chi": "remotix-figlio", "pid": 22,
                                      "render": 0, "video": 0}})
    b = _finta_fotografia(10000.0, {"1": {"chi": "gnome-shell", "pid": 11,
                                          "render": 2000000000, "video": 0},
                                    "2": {"chi": "remotix-figlio", "pid": 22,
                                          "render": 500000000,
                                          "video": 3000000000}})
    g = chi_tiene(a, b)
    atteso = {"gnome-shell": 20.0, "remotix-figlio": 5.0}
    bene = (g["esito"] == "misurato"
            and abs(g["per_programma"]["gnome-shell"]["render"] - 20.0) < 0.01
            and abs(g["per_programma"]["remotix-figlio"]["render"] - 5.0) < 0.01
            and abs(g["per_programma"]["remotix-figlio"]["video"] - 30.0) < 0.01)
    casi.append(("TARATURA · valori noti ritrovati", "chi tiene la GPU", True,
                 bene, bene, json.dumps(g["per_programma"], default=str)))
    (_ok if bene else _ko)("TARATURA · iniettati 2,00 s e 0,50 s di render su "
                           "10 s ⇒ attesi %s, letti %s"
                           % (atteso,
                              dict((k, v.get("render"))
                                   for k, v in g["per_programma"].items())))

    # ⛔ un contesto MORTO fra le due fotografie non deve gonfiare niente
    b2 = _finta_fotografia(10000.0, {"1": {"chi": "gnome-shell", "pid": 11,
                                           "render": 2000000000, "video": 0}})
    g2 = chi_tiene(a, b2)
    ok = (g2["esito"] == "misurato" and g2["contesti_morti"] == 1
          and "remotix-figlio" not in g2["per_programma"])
    casi.append(("GUASTO · un contesto muore fra le due letture", "chi tiene la GPU",
                 True, ok, ok, json.dumps(g2, default=str)[:200]))
    (_ok if ok else _ko)("GUASTO · contesto morto: contato (%d) e NON sommato"
                         % g2["contesti_morti"])

    # ⛔ un contatore ALL'INDIETRO ⇒ NON GIUDICO
    b3 = _finta_fotografia(10000.0, {"1": {"chi": "gnome-shell", "pid": 11,
                                           "render": -5, "video": 0},
                                     "2": {"chi": "remotix-figlio", "pid": 22,
                                           "render": 0, "video": 0}})
    g3 = chi_tiene(a, b3)
    ok = g3["esito"].startswith("⛔")
    casi.append(("GUASTO · occupazione negativa", "chi tiene la GPU", True, ok,
                 ok, g3["esito"]))
    (_ok if ok else _ko)("GUASTO · occupazione negativa ⇒ «%s»"
                         % g3["esito"][:80])

    # ⛔ il DOPPIO CONTEGGIO: 3 s di render su 1 s di parete
    b4 = _finta_fotografia(1000.0, {"1": {"chi": "gnome-shell", "pid": 11,
                                          "render": 3000000000, "video": 0},
                                    "2": {"chi": "remotix-figlio", "pid": 22,
                                          "render": 0, "video": 0}})
    g4 = chi_tiene(a, b4)
    ok = g4["esito"].startswith("⛔")
    casi.append(("GUASTO · doppio conteggio (300 % su un motore)",
                 "chi tiene la GPU", True, ok, ok, g4["esito"]))
    (_ok if ok else _ko)("GUASTO · 300 %% su un motore da uno ⇒ «%s»"
                         % g4["esito"][:80])

    # ⭐ e il VIDEO a 150 % NON deve dare rosso: i VDBOX sono DUE
    b5 = _finta_fotografia(1000.0, {"1": {"chi": "gnome-shell", "pid": 11,
                                          "render": 0, "video": 1500000000},
                                    "2": {"chi": "remotix-figlio", "pid": 22,
                                          "render": 0, "video": 0}})
    g5 = chi_tiene(a, b5)
    ok = g5["esito"] == "misurato"
    casi.append(("SANO · video al 150 % con capacita' 2", "chi tiene la GPU",
                 True, ok, ok, g5["esito"]))
    (_ok if ok else _ko)("SANO · video 150 %% con capacita' 2 ⇒ «%s» ⭐ un "
                         "tetto a 100 avrebbe dato rosso proprio quando la "
                         "scheda comincia a lavorare" % g5["esito"][:60])

    # ⛔ due fotografie troppo vicine ⇒ NON GIUDICO
    g6 = chi_tiene(a, _finta_fotografia(100.0, {"1": {"chi": "x", "pid": 1,
                                                      "render": 0, "video": 0}}))
    ok = g6["esito"].startswith("⛔")
    casi.append(("GUASTO · due letture a 0,1 s", "chi tiene la GPU", True, ok,
                 ok, g6["esito"]))
    (_ok if ok else _ko)("GUASTO · letture a 0,1 s ⇒ «%s»" % g6["esito"][:70])

    # ── 5-bis. ⛔⛔ «DOVE SONO FERMI» — il predicato centrale, e i suoi guasti
    _log("⛔⛔ «dove sono fermi i figli» — il predicato che porta la diagnosi")

    def con_fermi(dove, processi=None):
        g = _gradino_finto()
        g["dove_sono_fermi"] = {"campioni": 14, "processi":
                                (processi if processi is not None
                                 else dict((str(i), "remotix-figlio")
                                           for i in range(8))),
                                "dove": dove}
        return g

    prova("SANO · i figli aspettano la GPU (ioctl su /dev/dri)",
          con_fermi({"remotix-figlio": {"ioctl su /dev/dri/*": 100,
                                        "ppoll": 12}}),
          "ho una diagnosi di dove sono fermi", True)
    prova("SANO · i figli aspettano il padre (sendto su socket)",
          con_fermi({"remotix-figlio": {"sendto su socket": 90, "ppoll": 8}}),
          "ho una diagnosi di dove sono fermi", True)
    prova("GUASTO · il campione non ha trovato nessun figlio",
          con_fermi({"remotix-figlio": {"ppoll": 3}}, processi={}),
          "ho una diagnosi di dove sono fermi", False)
    prova("GUASTO · la sonda non ha risposto ⇒ None, non «non aspettano»",
          con_fermi(None), "ho una diagnosi di dove sono fermi", None)
    prova("GUASTO · meta' dei campioni fuori da ogni famiglia ⇒ None",
          con_fermi({"remotix-figlio": {"syscall_999": 100, "ppoll": 3}}),
          "ho una diagnosi di dove sono fermi", None)
    #  ⭐ e la TARATURA del raggruppamento: valori noti, famiglie attese
    fam, _d = famiglie_di({"a": {"ioctl su /dev/dri/*": 10, "sendto su socket": 4,
                                 "ppoll": 6, "nanosleep": 1, "syscall_777": 2}})
    ok = (fam["attesa GPU (vaSyncSurface, e TIENE il buffer del compositore)"] == 10
          and fam["contropressione del padre (send bloccante, figlio.c:2741)"] == 4
          and fam["si aspetta qualcosa che non arriva (poll/futex)"] == 6
          and fam["⚠ non classificate"] == 2)
    casi.append(("TARATURA · le famiglie contano quel che devono", "fermi",
                 True, ok, ok, json.dumps(fam, ensure_ascii=False)))
    (_ok if ok else _ko)("TARATURA · 10 ioctl-dri / 4 sendto / 6 ppoll / 2 "
                         "ignote ⇒ %s" % json.dumps(fam, ensure_ascii=False)[:150])

    # ── 5-ter. ⭐⭐⭐ L'ARITMETICA DEI BUFFER — tarata su numeri NOTI
    _log("⭐⭐⭐ l'aritmetica dei buffer — tarata su numeri noti, poi i guasti")

    def con_tratto(conv, cod, sped, buffer_distinti=None):
        g = _gradino_finto()
        voci = {}
        for k, x in (("produttore", 2.0), ("nel posto", 1.0),
                     ("conversione", conv), ("codifica", cod),
                     ("spedizione", sped)):
            voci[k] = {"righe": 10, "mediana_ms": x, "min_ms": x, "max_ms": x}
        g["registro"]["tratto_dei_figli"] = {
            "righe": 320, "totale": {"mediana_ms": conv + cod + sped},
            "voci": voci}
        g["registro"]["buffer_di_pipewire"] = (
            {"righe": 3, "buffer_distinti": [buffer_distinti]}
            if buffer_distinti is not None
            else {"esito": "⛔ NON HO LETTO"})
        return g

    #  ⭐ TARATURA: 6 buffer, 2 trattenuti ⇒ 4 liberi × 16,67 ms = 66,67 ms
    d = aritmetica_dei_buffer(con_tratto(5.0, 3.0, 0.4, buffer_distinti=6))
    ok = (abs(d["soglia_ms"] - 66.67) < 0.02 and d["buffer_liberi"] == 4
          and abs(d["tenuto_ms"] - 8.4) < 0.01 and not d["oltre_la_soglia"]
          and d["buffer_assunti"] is False)
    casi.append(("TARATURA · 6 buffer, 2 tenuti, 60/s ⇒ soglia 66,67 ms",
                 "buffer", True, ok, ok, json.dumps(d)))
    (_ok if ok else _ko)("TARATURA · 6 buffer − 2 tenuti = 4 liberi × 16,67 ms "
                         "⇒ soglia %.2f ms, teniamo %.2f ⇒ ×%.3f"
                         % (d["soglia_ms"], d["tenuto_ms"], d["margine"]))

    #  ⛔ e il produttore che ne da' solo QUATTRO: la soglia si dimezza
    d4 = aritmetica_dei_buffer(con_tratto(5.0, 3.0, 0.4, buffer_distinti=4))
    ok = abs(d4["soglia_ms"] - 33.33) < 0.02 and d4["buffer_liberi"] == 2
    casi.append(("TARATURA · 4 buffer ⇒ soglia 33,33 ms", "buffer", True, ok,
                 ok, json.dumps(d4)))
    (_ok if ok else _ko)("TARATURA · con 4 buffer soli la soglia scende a "
                         "%.2f ms ⭐ e il dirupo si sposta col NUMERO DEI "
                         "BUFFER, non col numero di sessioni" % d4["soglia_ms"])

    prova("SANO · sotto la soglia (8,4 ms contro 66,7)",
          con_tratto(5.0, 3.0, 0.4, buffer_distinti=6),
          "l'aritmetica dei buffer", True)
    prova("GUASTO · la conversione da sola sfonda la soglia",
          con_tratto(80.0, 3.0, 0.4, buffer_distinti=6),
          "l'aritmetica dei buffer", False)
    prova("GUASTO · e' la SPEDIZIONE a sfondarla (contropressione del padre)",
          con_tratto(5.0, 3.0, 70.0, buffer_distinti=6),
          "l'aritmetica dei buffer", False)
    prova("GUASTO · nessuna riga TRATTO ⇒ None, non «sotto la soglia»",
          _gradino_finto(tratto=False), "l'aritmetica dei buffer", None)
    #  ⛔ e i buffer ASSUNTI si devono vedere da fuori
    da = aritmetica_dei_buffer(con_tratto(5.0, 3.0, 0.4))
    ok = da["buffer_assunti"] is True and da["buffer_totali"] == 6
    casi.append(("⛔ i buffer non contati si dichiarano ASSUNTI", "buffer",
                 True, ok, ok, json.dumps(da)))
    (_ok if ok else _ko)("⛔ senza la riga dei buffer si assume 6 e lo si "
                         "DICHIARA (buffer_assunti=%s)" % da["buffer_assunti"])

    # ── 5-quater. ⛔⛔ UNA CURA SPENTA CHE NON SI E' SPENTA DAVVERO
    _log("⛔⛔ la cura spenta che non si e' spenta davvero — e si guarda dal "
         "processo E dal registro, non dal comando scritto da me")

    class FintoB92:
        UNITA = "remotix-8190"
        LAV = "/x"

        def __init__(self, argv, registro):
            self.argv, self.registro = argv, registro

        def root(self, c, *a, **k):
            if "cmdline" in c:
                return 0, self.argv, ""
            return 0, self.registro, ""

    ACCESA = ("20:00 avvio ⭐ FASE 9, soglia della coda video (§5.1): 100 ms — "
              "ACCESA: sopra la soglia un delta fermo si abbandona\n"
              "20:00 avvio ⭐ FASE 9: il regolatore del ritmo e' ACCESO — un "
              "fotogramma NON parte quando 2 delta in volo\n")
    SPENTA = ("20:00 avvio ⛔ FASE 9, soglia della coda video (§5.1): 0 ms — "
              "SPENTA: si abbandona a ogni fotogramma piu' recente\n"
              "20:00 avvio ⭐ FASE 9: il regolatore del ritmo e' ACCESO — un "
              "fotogramma NON parte quando 2 delta in volo\n")
    BASE = "/x/remotix --porta 8190 --parlantina"

    global B92
    vero = B92
    try:
        casi_cure = [
            ("SANO · dico accesa ed e' accesa",
             BASE, ACCESA, True, True, True),
            ("SANO · dico spenta ed e' spenta davvero",
             BASE + " --sgombra-soglia-ms 0", SPENTA, False, True, True),
            ("⛔ GUASTO · dico spenta e l'opzione NON c'e' nella riga d'avvio",
             BASE, SPENTA, False, True, False),
            ("⛔⛔ GUASTO · l'opzione c'e' ma il REGISTRO dice ACCESA "
             "(i due testimoni discordano)",
             BASE + " --sgombra-soglia-ms 0", ACCESA, False, True, False),
            ("⛔ GUASTO · dico accesa e qualcuno l'ha spenta",
             BASE + " --sgombra-soglia-ms 0", SPENTA, True, True, False),
            ("⛔ il registro non dice niente ⇒ None, non «va bene»",
             BASE, "20:00 avvio pronto\n", True, True, None),
            ("⛔ la riga d'avvio non si legge ⇒ None",
             "", ACCESA, True, True, None),
        ]
        for nome, argv, reg, sog, rit, atteso in casi_cure:
            B92 = FintoB92(argv, reg)
            got, det = cure_verificate(sog, rit)
            ok = got is atteso if atteso is None else got == atteso
            casi.append((nome, "cure", atteso, got, ok, det.get("esito")))
            (_ok if ok else _ko)("%-62s → %s (atteso %s) · %s"
                                 % (nome, got, atteso,
                                    str(det.get("esito"))[:90]))
    finally:
        B92 = vero

    # ── 6-bis. ⛔⛔ IL RIVELATORE DEL DIRUPO — e il dirupo cercato DOVE NON C'E'
    _log("⛔⛔ il rivelatore del dirupo — e deve saper dire «NESSUN DIRUPO»")

    def gr(nome, quanti, fps):
        v = _gradino_finto(quanti=quanti, fps=fps)
        v["nome"] = nome
        v["t0"] = 1000.0 * quanti
        v["t1"] = 1000.0 * quanti + 500.0
        return v

    #  ⭐ il dirupo VERO, come misurato: 6 a 38 · 7 a 26 · 8 a 1,5
    veri = [gr("6S", 6, 38.0), gr("7S", 7, 26.0), gr("8S", 8, 1.5)]
    d = rileva_dirupo(veri)
    ok = d["esito"] == "DIRUPO" and d["dove"][0] == "7S"
    casi.append(("il dirupo dove C'E' (6→7→8)", "dirupo", True, ok, ok,
                 d.get("detto")))
    (_ok if ok else _ko)("il dirupo dove C'E': %s" % d.get("detto"))

    #  ⛔ e cercato DOVE NON C'E': due sessioni, tutt'e due a 38
    due = [gr("1S", 1, 39.0), gr("2S", 2, 38.0)]
    d = rileva_dirupo(due)
    ok = d["esito"] == "nessun dirupo"
    casi.append(("il dirupo cercato a DUE sessioni", "dirupo", True, ok, ok,
                 d.get("detto")))
    (_ok if ok else _ko)("cercato dove NON c'e' (due sessioni): %s"
                         % d.get("detto"))

    #  ⛔ la discesa NATURALE 1/N non deve diventare un dirupo: la stessa torta
    #     divisa fra sei fa scendere il PER-SESSIONE di sei volte, e non e' un
    #     dirupo — ⚠ ma il confronto appaiato lo vedrebbe come ×6.  ⇒ Con la
    #     soglia a ×3 questo caso DEVE dare dirupo se il per-sessione cade
    #     davvero di sei volte: e' il prezzo dichiarato del confronto appaiato,
    #     e il gradino intermedio esiste per non arrivarci mai a salti.
    graduale = [gr("5S", 5, 39.0), gr("6S", 6, 33.0), gr("7S", 7, 28.0)]
    d = rileva_dirupo(graduale)
    ok = d["esito"] == "nessun dirupo"
    casi.append(("la discesa graduale NON e' un dirupo", "dirupo", True, ok,
                 ok, d.get("detto")))
    (_ok if ok else _ko)("discesa graduale 39→33→28 a testa: %s"
                         % d.get("detto"))

    #  ⭐⭐ E IL CASO CHE HA MORSO DAVVERO: cinque sessioni SFRATTATE a meta'
    #     giro, quindi ogni gradino ha un buco.  ⛔ Il banco deve giudicare LO
    #     STESSO, sulle sessioni sopravvissute, invece di tacere.
    sfrattate = [gr("7S", 7, 33.5), gr("8S", 8, 1.6)]
    for v in sfrattate:
        for i in (1, 2, 3, 4, 5):
            v["sessioni"][i] = {"esito": "⛔ il cliente e' stato sfrattato"}
    d = rileva_dirupo(sfrattate)
    ok = d["esito"] == "DIRUPO" and d["sessioni_appaiate"] == [6, 7]
    casi.append(("⭐ il dirupo si vede anche con cinque sessioni sfrattate",
                 "dirupo", True, ok, ok, d.get("detto")))
    (_ok if ok else _ko)("con s1-s5 sfrattate, giudica su s6-s7: %s"
                         % d.get("detto"))

    #  ⛔ e se NON resta nessuna sessione in comune, allora si tace davvero
    nessuna = [gr("7S", 7, 33.5), gr("8S", 8, 1.6)]
    for i in range(1, 8):
        nessuna[0]["sessioni"][i] = {"esito": "⛔ non letta"}
    d = rileva_dirupo(nessuna)
    ok = d["esito"].startswith("⛔")
    casi.append(("nessuna sessione in comune ⇒ NON GIUDICO", "dirupo", True,
                 ok, ok, d["esito"]))
    (_ok if ok else _ko)("nessuna sessione misurata in comune ⇒ «%s»"
                         % d["esito"][:90])

    # ── 6-ter. ⛔ L'ANCORA — un gradino letto dal precedente ──────────────
    ok, perche = ancora_avanza(veri)
    casi.append(("SANO · l'ancora avanza", "ancora", True, ok, ok, perche))
    (_ok if ok else _ko)("SANO · %s" % perche)
    storto = [gr("6S", 6, 38.0), gr("7S", 7, 26.0)]
    storto[1]["t0"] = storto[0]["t1"] - 1000.0
    ok, perche = ancora_avanza(storto)
    casi.append(("GUASTO · un gradino letto dal precedente", "ancora", False,
                 ok, ok is False, perche))
    (_ok if ok is False else _ko)("GUASTO · %s" % perche[:110])

    # ── 6-quater. ⛔ le sessioni che NON erano sature, dai BYTE ───────────
    prova("SANO · i byte confermano la scena", _gradino_finto(),
          "i byte confermano la scena", True)
    magro2 = _gradino_finto()
    magro2["sessioni"][4]["byte_per_fotogramma"] = 300
    prova("GUASTO · una sessione dichiarata satura che non lo era",
          magro2, "i byte confermano la scena", False)
    prova("GUASTO · i byte per fotogramma non si sono letti ⇒ None",
          _gradino_finto(byte=None), "i byte confermano la scena", None)

    # ── 7. ⛔ il LETTORE DEL REGISTRO, su un registro FABBRICATO ──────────
    _log("⛔ il lettore del registro — su un registro fabbricato a valori noti")
    ok_reg = certifica_conti(casi)

    # ── il conto ─────────────────────────────────────────────────────────
    rossi = [c for c in casi if not c[4]]
    _log("⛔ IL CONTO: %d casi, %d rossi" % (len(casi), len(rossi)))
    for c in rossi:
        _ko("%s — «%s»: atteso %s, avuto %s (%s)" % (c[0], c[1], c[2], c[3],
                                                     str(c[5])[:120]))
    if not rossi:
        _ok("⭐ %d casi su %d: ogni predicato ha visto il suo guasto, e il "
            "sano e' rimasto sano" % (len(casi), len(casi)))
    return 0 if not rossi else 1


def certifica_conti(casi):
    """⛔ Il lettore del registro si prova su un registro FABBRICATO: righe vere,
       nel formato vero, con dentro numeri che io conosco."""
    import subprocess
    import tempfile

    righe = []
    # 8 figli, 3 righe «ciclo:» a testa, contatori monotoni e distinti
    for s in range(3):
        for f in range(8):
            righe.append("12:00:%02d.000 figlio  ciclo: %d fotogrammi "
                         "consegnati (%d chiavi), %d attese a vuoto (scena "
                         "ferma: Mutter consegna solo quando qualcosa cambia), "
                         "%d guasti — codec 1, 60/s chiesti, attesa 0.01 s"
                         % (s, 1000 * (f + 1) + 10 * s, f, 100 * (f + 1) + 5 * s,
                            f))
    righe.append("12:00:00.000 figlio  ⚠ RIPIEGO DICHIARATO: «h264_vaapi» su "
                 "/dev/dri/renderD128 non si e' aperto (boh) ⇒ si scende su "
                 "«libx264» IN SOFTWARE, che sul banco costa ~22 ms")
    righe.append("12:00:01.000 figlio  ⭐ TRATTO cattura → byte fuori: mediana "
                 "12.50 ms (max 40.00) su 512 fotogrammi del campione, 9000 in "
                 "tutto — produttore 2.00 (max 3.00) · allocazione 0.10 (max "
                 "0.20) · copia 0.00 (max 0.00) · nel posto 1.50 (max 2.00) · "
                 "misura 0.30 (max 0.40) · conversione 5.00 (max 20.00) · "
                 "caricamento 0.00 (max 0.00) · codifica 3.00 (max 5.00) · "
                 "spedizione 0.40 (max 1.00) · resto 0.20 (max 0.30)")
    righe.append("12:00:02.000 rcp     ritmo di 127.0.0.1:5000: arretrato "
                 "LETTO 38 volte in quest'ultimo secondo, massimo 1, ultimo 0, "
                 "posti 3 — 0 fotogrammi non partiti in questo secondo, 0 in "
                 "tutto.")
    righe.append("12:00:03.000 rcp     ritmo di 127.0.0.1:5000: arretrato "
                 "LETTO 2 volte in quest'ultimo secondo, massimo 3, ultimo 3, "
                 "posti 3 — 4 fotogrammi non partiti in questo secondo, 4 in "
                 "tutto.")
    righe.append("12:00:04.000 rcp     ⛔ 127.0.0.1:5000: il ritmo SCENDE — "
                 "arretrato 3 delta contro 3 posti, 90000 byte fermi nella "
                 "coda del video (90000 in tutto).")
    righe.append("12:00:05.000 rcp     ⭐ 127.0.0.1:5000: il ritmo RISALE — "
                 "l'episodio e' durato 120 ms e sono restati indietro 4 "
                 "fotogrammi.")
    righe.append("12:00:06.000 rcp     ⛔ 127.0.0.1:5000: la coda del video "
                 "passa SOPRA la soglia (90000 byte = 140 ms, soglia 100 ms, "
                 "stima), arretrato 3 delta")
    righe.append("12:00:07.000 rcp     fotogramma 12 ABBANDONATO NELLA CODA "
                 "(§5.1, RESET_STREAM): 5000 byte")
    # ⛔⛔ IL FALSO POSITIVO CHE HA IL DIRITTO DI ESISTERE: la stessa marca
    #     «RIPIEGO DICHIARATO» apre anche la riga della tabella delle tele dei
    #     palchi (`webtransport.c:5264`).  Un rivelatore che contasse la marca e
    #     basta direbbe «una sessione codifica in software» ogni volta che il
    #     nono utente arriva.
    righe.append("12:00:08.000 wt      ⚠ RIPIEGO DICHIARATO: la tabella delle "
                 "tele dei palchi e' piena (8): la tela di «provamt9» non si "
                 "registra")
    righe.append("12:00:09.000 rcp     🔸 127.0.0.1:5000: la CHIAVE si potra' "
                 "richiedere ogni 660 ms invece di 150 — l'ultima misurava "
                 "90000 byte e la banda MISURATA e' 1000 kbit/s")
    righe.append("12:00:10.000 wt      ⚠ logind ha impiegato 250 ms per "
                 "l'elenco delle sessioni")

    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
        f.write("\n".join(righe) + "\n")
        dove = f.name
    n = os.path.getsize(dove)
    p = subprocess.run([sys.executable, os.path.join(QUI, "10-b9d-conti.py"),
                        dove, "0", str(n), "8"], capture_output=True)
    try:
        d = json.loads(p.stdout.decode())
    except Exception as e:
        _ko("⛔ il lettore del registro non ha risposto: %s — %s"
            % (e, p.stderr.decode()[-200:]))
        casi.append(("il lettore del registro risponde", "conti", True, False,
                     False, p.stderr.decode()[-200:]))
        os.unlink(dove)
        return False

    controlli = [
        ("un ripiego trovato", d["quanti_ripieghi"] == 1),
        ("il ripiego dice CHI e SU COSA",
         d["ripieghi_software"][0].get("ripiego") == "libx264"),
        ("otto serie «ciclo:» ricostruite",
         d["cattura_dei_figli"].get("serie") == 8),
        ("i fotogrammi catturati sono 8x20 = 160",
         d["cattura_dei_figli"].get("fotogrammi_catturati") == 160),
        ("le attese a vuoto sono 8x10 = 80",
         d["cattura_dei_figli"].get("attese_a_vuoto") == 80),
        ("il TRATTO legge la conversione a 5,00 ms",
         (d["tratto_dei_figli"]["voci"]["conversione"]["mediana_ms"] == 5.0)),
        ("il TRATTO legge «nel posto» a 1,50 ms",
         (d["tratto_dei_figli"]["voci"]["nel posto"]["mediana_ms"] == 1.5)),
        ("le consegne del palco: mediana fra 2 e 38",
         d["per_provenienza"]["127.0.0.1:5000"]["consegne_al_secondo_mediana"]
         in (2, 38)),
        ("il ritmo SCENDE contato una volta", d["ritmo_scende_in_tutto"] == 1),
        ("il ritmo RISALE contato una volta", d["ritmo_risale_in_tutto"] == 1),
        ("la coda SOPRA la soglia contata una volta",
         d["sopra_soglia_in_tutto"] == 1),
        ("un abbandono in coda", d["abbandoni_in_coda"] == 1),
        ("⛔ la tabella dei palchi piena NON e' contata come ripiego software",
         d["quanti_ripieghi"] == 1 and d["altri_conti"]["palchi_pieni"] == 1),
        ("la CHIAVE ogni 660 ms letta per sessione",
         d["per_provenienza"]["127.0.0.1:5000"]["chiave_ogni_ms"] == 660),
        ("logind: una chiamata lenta da 250 ms",
         d["logind"]["chiamate_lente"] == 1 and d["logind"]["ms_massimo"] == 250),
    ]
    for nome, ok in controlli:
        (_ok if ok else _ko)("registro fabbricato · %s" % nome)
        casi.append(("REGISTRO · " + nome, "conti", True, ok, ok, ""))

    # ⛔ E IL RIFIUTO: se le serie non tornano, NON si dichiara un numero
    p2 = subprocess.run([sys.executable, os.path.join(QUI, "10-b9d-conti.py"),
                         dove, "0", str(n), "11"], capture_output=True)
    d2 = json.loads(p2.stdout.decode())
    ok = "esito" in d2["cattura_dei_figli"] and \
         d2["cattura_dei_figli"]["esito"].startswith("⛔")
    (_ok if ok else _ko)("registro fabbricato · ⛔ undici figli attesi e otto "
                         "serie trovate ⇒ NON DICHIARO (invece di un numero "
                         "plausibile)")
    casi.append(("REGISTRO · l'inseguimento che non torna ⇒ None", "conti",
                 True, ok, ok, str(d2["cattura_dei_figli"])[:120]))

    # ⛔ e un registro VUOTO non deve produrre zeri
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
        f.write("12:00:00.000 avvio   niente da vedere\n")
        vuoto = f.name
    p3 = subprocess.run([sys.executable, os.path.join(QUI, "10-b9d-conti.py"),
                         vuoto, "0", str(os.path.getsize(vuoto)), "8"],
                        capture_output=True)
    d3 = json.loads(p3.stdout.decode())
    ok = (d3["tratto_dei_figli"].get("esito", "").startswith("⛔")
          and d3["cattura_dei_figli"].get("esito", "").startswith("⛔"))
    (_ok if ok else _ko)("registro fabbricato · ⛔ registro senza righe di "
                         "figlio ⇒ «non ho letto», non «zero»")
    casi.append(("REGISTRO · vuoto ≠ zero", "conti", True, ok, ok, ""))

    os.unlink(dove)
    os.unlink(vuoto)
    return True


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    global B92
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?", choices=["terreno", "giro", "sgombra"])
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--da", type=int, default=5)
    p.add_argument("--a", type=int, default=8)
    p.add_argument("--durata", type=int, default=40)
    p.add_argument("--fine", action="store_true",
                   help="⭐ i bracci fini: stessa popolazione, carico diverso")
    p.add_argument("--etichetta", default="")
    p.add_argument("--soglia-spenta", action="store_true",
                   help="⛔ dichiaro che il server gira con "
                        "`--sgombra-soglia-ms 0`: il banco lo VERIFICA dal "
                        "processo e dal registro, e si rifiuta se non e' vero")
    p.add_argument("--ritmo-spento", action="store_true",
                   help="⛔ dichiaro che il server gira con "
                        "`--niente-ritmo-adattivo`: idem")
    p.add_argument("--senza-lucchetto", action="store_true")
    p.add_argument("--lucchetto-gia-mio", action="store_true",
                   help="⭐ il lucchetto della GPU ce l'ha gia' chi mi ha "
                        "lanciato, e lo tiene per tutto il giro (server "
                        "acceso compreso): non lo riprendo e non lo mollo")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    B92 = _importa("b92", "10-b92-dieci.py")
    B92.B70 = B92._importa_b70()
    for nome in ("10-b9d-conti.py", "10-b9d-chi-tiene-la-gpu.py",
                 "10-b9d-dove-sono-fermi.py"):
        with open(os.path.join(QUI, nome)) as f:
            if not B92.spedisci(f.read(), nome):
                _ko("⛔ «%s» non e' arrivato sulla macchina" % nome)
                return 2
    _ok("i due attrezzi nuovi sono in %s" % B92.LAV)

    if a.passo == "terreno":
        return 0 if B92.terreno(a.a) else 2
    if a.passo == "sgombra":
        import subprocess
        subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                        "sgombra"])
        return 0

    luc = None
    if a.lucchetto_gia_mio:
        rc, out, _ = B92.root("cat %s/chi 2>/dev/null || echo '(nessuno)'"
                              % os.environ["LUCCHETTO"])
        if B92.IO_SONO not in out:
            _ko("⛔ NON MISURO: dicevo di avere il lucchetto e dentro c'e' "
                "«%s»" % out.strip()[:120])
            return 2
        _ok("il lucchetto della GPU e' mio: %s" % out.strip()[:120])
    elif not a.senza_lucchetto:
        luc = B92._lucchetto()
        quanto = (a.a - a.da + 8) * (a.durata + 90) + 1200
        _inf("⛔ chiedo il lucchetto della GPU per %d s (%d min)"
             % (quanto, quanto // 60))
        try:
            luc.prendi(B92.IO_SONO, secondi=quanto, attesa=5400)
        except Exception as e:
            _ko("⛔ NON MISURO: %s" % e)
            return 2
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON valgono")
    try:
        return giro(a)
    finally:
        if luc:
            luc.molla(B92.IO_SONO)


if __name__ == "__main__":
    sys.exit(principale())
