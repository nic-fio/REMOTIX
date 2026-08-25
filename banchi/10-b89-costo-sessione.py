#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b89 — ⭐⭐⭐ QUANTO COSTA **UNA** SESSIONE.  La riga zero della fase 10.

═══ LA DOMANDA, E PERCHE' NESSUNO L'HA ANCORA POSTA ═════════════════════════
`DECISIONI.md` §4.6 promette **dieci sessioni** e dichiara, per la memoria, una
**stima**: *«dieci sessioni GNOME ferme sono ~12 GB dei 31»*.  §4.6-sexies
spiega perche' il multi-tenant sta **dopo la fase 8**: la **copia zero** ha
cambiato quanto costa una sessione, e *«un budget misurato prima della copia
zero e' un budget da rifare»*.
⇒ ⛔ **Nessuno ha misurato quanto costa UNA sessione dopo la fase 8.**  Senza
  quel numero «dieci» non si puo' ne' promettere ne' negare.

E serve una seconda volta: §4.6-bis promette che **chi sta gia' lavorando non
peggiora** quando arriva chi non entra.  Quella promessa si verifica **solo**
contro una misura di riferimento presa **da sola** — ed e' questa.

═══ ⛔ CHE COSA SI MISURA, E CHE COSA SI RIFIUTA DI MISURARE ════════════════
Cinque grandezze, su tre scene dichiarate:

  1. **memoria** — RSS, e ⛔ **PSS e USS**: dieci figli condividono le stesse
     librerie, e sommare dieci RSS conta dieci volte le stesse pagine.  Con la
     memoria della **sessione grafica** (gnome-shell, PipeWire, i portali), che
     e' la parte grossa;
  2. **GPU** — il motore di **rendering** (il compositore disegna) e quello di
     **codifica** (il codificatore codifica): due consumi diversi sulla stessa
     scheda, e vanno separati;
  3. **CPU** — quanto del i5-13500T, separato fra compositore, figlio e padre;
  4. **filo** — i bit al secondo che escono davvero;
  5. **quel che l'utente vede** — fotogrammi/s consegnati, byte per fotogramma,
     cadenza, e il **risveglio** (pixel → byte fuori) sulla scena a strappi.
     ⛔ Senza questa colonna il costo non dice niente: una sessione che costa
     poco perche' non consegna niente non e' economica, e' rotta.

═══ ⛔⛔ LE TRE SCENE, E IL CONTATORE CHE LE SMASCHERA ══════════════════════
`LEZIONI.md` §1.30: in fase 9 **tre giudizi sono stati buttati** perche' la
scena non aveva niente da rompere — fotogrammi da **242 byte**.
⇒ Qui ogni riga porta accanto **byte per fotogramma** e **fotogrammi
  consegnati**, e c'e' un predicato che **da' rosso** se la scena non morde:

  | scena      | com'e' fatta                                   | il predicato |
  |------------|------------------------------------------------|--------------|
  | `ferma`    | il desktop appena aperto, nessuno tocca niente | ⛔ e' rosso se si MUOVE: una «ferma» che consegna 25/s e' un video rimasto acceso sotto (`09-b72`, 23 ago) |
  | `desktop`  | due finestre vere + movimento a **strappi**    | ⛔ rosso se i colpi non arrivano o i fotogrammi sono minuscoli |
  | `continuo` | cambiamento a pieno ritmo, il caso peggiore    | ⛔ rosso se i byte per fotogramma o i fotogrammi/s crollano: e' la scena che dice di muoversi e sta ferma |

═══ ⛔ IL METRO DELLA GPU SI TARA PRIMA (`LEZIONI.md` §1.33, regola 6) ══════
`intel_gpu_top` non c'e' su questa macchina.  Si legge `/proc/<pid>/fdinfo`
(`drm-engine-*` su `i915`) — ⛔ **e prima di crederci gli si inietta un carico
NOTO**: due codifiche VA-API della stessa durata a **15 e 30 fotogrammi/s**, cioe'
un rapporto **2:1** deciso da noi.  Il metro deve ritrovarlo.  Se non lo
ritrova, i suoi numeri **non si riferiscono** (`passo tara-gpu`).

═══ ⛔⛔ E IL BANCO NON E' FINITO FINCHE' NON L'HO VISTO DARE ROSSO ═════════
`LEZIONI.md` §1.29.  `--certifica` innesta cinque guasti e li **fa girare**:
  G1  la sessione **non si apre**            ⇒ rosso, non «0 fotogrammi, regolare»
  G2  il palco resta **orfano** dal giro prima ⇒ rosso **prima** di misurare
  G3  il lettore della **memoria** non legge  ⇒ `None`, mai zero
  G4  la scena «continuo» **non si muove**    ⇒ i byte/fotogramma la smascherano
  G5  il lettore della **GPU** non legge      ⇒ `None`, e niente colonna GPU

⛔⛔ IL LUCCHETTO DELLA GPU: ogni giro da cui esce un numero che si riferisce lo
    prende (`10-a3`).  Una sessione vera fa lavorare la GPU, e mentre la fa
    lavorare nessun altro puo' misurarla (`LEZIONI.md` §1.26).

Uso (dal portatile):
    bash banchi/10-b89-terreno.sh utente
    bash banchi/10-b89-terreno.sh porta
    bash banchi/10-b89-terreno.sh accendi
    python3 banchi/10-b89-costo-sessione.py stato
    python3 banchi/10-b89-costo-sessione.py tara-gpu
    python3 banchi/10-b89-costo-sessione.py tutto --secondi 40
    python3 banchi/10-b89-costo-sessione.py certifica
    python3 banchi/10-b89-costo-sessione.py chiudi
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔⛔ L'ISOLAMENTO E' MIO E STA QUI SOPRA A TUTTO: porta 8010, utente
#     `provadec1` (uid 1100), albero `10a3-src`, lavoro `tmp/10a3`, unita'
#     `remotix-8010`.  Si esporta PRIMA di caricare `09-b68`, che legge
#     l'ambiente al momento dell'importazione.
os.environ.setdefault("PORTA", "8010")
os.environ.setdefault("UTENTE", "provadec1")
os.environ.setdefault("UID_B", "1100")
os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10a3")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10a3-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10a3")
os.environ.setdefault("ALB_NOME", "10a3-src")
os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "ab31ac36-86ed-4f24-8d71-e41da4a7da6e/scratchpad/b89")
os.environ["FUORI"] = FUORI
os.makedirs(FUORI, exist_ok=True)


def _carica(nome, file_):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⭐ Il mestiere non si riscrive: `09-b68` ha ssh, sudo, `lo` e il registro;
#    `09-b71` ha la sessione e il battitore; `09-lucchetto` ha il turno.
b68 = _carica("b68", "09-b68-ritmo.py")
b71 = _carica("b71", "09-b71-risveglio.py")
luc = _carica("luc", "09-lucchetto.py")

root, rem = b68.root, b68.rem
LAV = b68.LAV
UTENTE = b68.UTENTE
UID_B = b68.UID_B
ALBERO = os.environ.get("ALBERO", "/media/REMOTIX/src/10a3-src")
UNITA = os.environ.get("UNITA", "remotix-%d" % b68.PORTA)
UNITA_AGENTE = "b89-a3-agente"
TELA = os.environ.get("TELA", "1920x1080")
IO_SONO = "10-a3"

# ── ⛔ LE SOGLIE CHE FANNO DARE ROSSO, e da dove vengono ───────────────────
#
# ⚠ Non sono scelte a occhio: `LEZIONI.md` §1.30 misura che una prova con
#   fotogrammi da **242-283 byte** «non aveva niente da rompere», e che
#   trascinare una finestra vera faceva picchi da **3 801 byte**.  ⇒ il
#   confine fra «una scena che morde» e «una scena che non morde» sta fra i
#   due, e si scrive **dal lato prudente** (`CODER.md` §3.3-quinquies): meglio
#   dichiarare non-valida una scena buona che riferire un numero preso su una
#   scena morta.
# ⛔⛔ ⇒ E LA PRIMA TARATURA DI QUESTA SOGLIA E' ANDATA STORTA, il 24 agosto
#      2026, esattamente nella forma di `REVIEWER.md` **E15**: la soglia era a
#      2 000 byte, e `[M]` la scena `pieno` **sana** ne fa **1 789** contro i
#      **1 368** della stessa scena **congelata**.  ⇒ ⛔ i byte per fotogramma
#      NON separano i due estremi noti — fra loro c'e' un fattore **1,3** — e
#      nessuna soglia su quella grandezza poteva farlo.
#      ⭐ La grandezza che li ordina e' il **ritmo**: 44,45 fotogrammi/s sana
#      contro il ritmo di una scena ferma.  ⇒ per «continuo» si guarda PRIMA il
#      ritmo, e i byte restano come **seconda colonna** — quella che dice quanto
#      la scena chiedeva (`LEZIONI.md` §1.30), con un pavimento basso e
#      giustificato: `[M]` un fotogramma di desktop **fermo** ne pesa **455**, e
#      il caso buttato di fase 9 ne pesava **242-283**.
SOGLIA_BYTE_MORDE = 600           # byte medi per fotogramma — sopra il fermo (455)
SOGLIA_FPS_CONTINUO = 10.0        # fotogrammi/s: sotto, «continuo» non e' continuo
SOGLIA_FPS_FERMA = 2.0            # ⛔ sopra, «ferma» non e' ferma
SOGLIA_COLPI_BUONI = 0.6          # frazione di strappi che devono aver prodotto un fotogramma

# ⚠ Quanti motori ha ciascun tipo su questa scheda — letto in `fdinfo`
#   (`drm-engine-capacity-video: 2`) e confermato da `10-b87-metro-gpu.py`.
CAPACITA = {"render": 1, "copy": 1, "video": 2, "video-enhance": 1}
MOTORI_NOMI = {"render": "rendering (il compositore disegna)",
               "video": "codifica (il codificatore codifica)",
               "copy": "copia", "video-enhance": "ritocco video"}

# ⛔⛔ L'IDENTITA' FRA L'AREA E IL CORPO — 25 agosto 2026, cura C4 della fase 10.
#
#   Da quel giorno ogni riga che sa di chi e' porta `[nome] ` **in testa al
#   corpo**, subito dopo l'area.  Un modello ancorato che non lo preveda
#   ⛔ non trova piu' NIENTE — e il guaio non e' che si ferma: e' che il
#   conto esce **zero**, cioe' un numero che ACCUSA il prodotto di non aver
#   spedito un fotogramma mentre li spediva tutti.
#   ⇒ Il gruppo qui sotto e' FACOLTATIVO apposta: cosi' il lettore funziona
#     sui registri di prima **e** su quelli di adesso.
R_SPED = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) rcp\s+(?:\[[^\]]{1,48}\] )?fotogramma (\d+) SPEDITO: "
                    r"(CHIAVE|delta) 0x0\d0\d, codec (\d+), (\d+)x(\d+), (\d+) byte", re.M)


def sdg(hh, mm, ss, ms):
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def stat(v):
    return b71.statistica(v)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL POSTO E' LIBERO?  — si VERIFICA, non si conta il tempo
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ In fase 9 un palco orfano ha quasi fatto accusare tre cure innocenti: il
#    giro precedente aveva lasciato viva una sessione, e il giro dopo misurava
#    **la sessione di prima** credendo di misurare la sua.  ⇒ non si aspetta
#    «tanto sara' morto»: si guarda, e se c'e' qualcosa di mio ancora vivo il
#    banco **si ferma prima di misurare**.
def posto_libero(parla=True):
    d = {}
    rc, out, _ = root("pgrep -au %d -f 'remotix-figlio' || true" % UID_B)
    d["figli_orfani"] = [x for x in out.splitlines() if x.strip()]
    rc, out, _ = root("pgrep -au %d -f '04-b30-scen[a]|nautilu[s]|gnome-termina[l]' || true" % UID_B)
    d["scene_orfane"] = [x for x in out.splitlines() if x.strip()]
    rc, out, _ = root("pgrep -au %d -f 'gnome-shel[l]' || true" % UID_B)
    d["sessioni_grafiche_orfane"] = [x for x in out.splitlines() if x.strip()]
    rc, out, _ = root("pgrep -a -f '01-b3-client[e].py' || true")
    d["clienti_orfani"] = [x for x in out.splitlines() if x.strip()]
    rc, out, _ = root("systemctl is-active %s.service" % UNITA_AGENTE)
    d["agente_del_giro_prima"] = out.strip()
    # ⛔ E si guarda anche che ci sia solo IL MIO server: due server sullo
    #    stesso albero sarebbero due misure sulla stessa GPU (`LEZIONI.md` §1.26).
    rc, out, _ = root("pgrep -a -f '%s/src/remoti[x]' || true" % ALBERO)
    d["server_miei"] = [x for x in out.splitlines() if x.strip()]

    libero = not (d["figli_orfani"] or d["scene_orfane"] or
                  d["sessioni_grafiche_orfane"] or d["clienti_orfani"] or
                  d["agente_del_giro_prima"] == "active")
    d["libero"] = libero
    if parla:
        print("== ⛔ IL POSTO E' LIBERO?  (il palco orfano si VERIFICA, non si aspetta)")
        for k in ("figli_orfani", "scene_orfane", "sessioni_grafiche_orfane",
                  "clienti_orfani"):
            print("   %-26s %s" % (k, d[k] or "nessuno"))
        print("   %-26s %s" % ("agente del giro prima", d["agente_del_giro_prima"]))
        print("   %-26s %s" % ("il mio server (8010)",
                               [x[:60] for x in d["server_miei"]] or "⛔ NESSUNO"))
        print("   %s il posto %s" % ("OK " if libero else "⛔ ",
                                     "e' libero" if libero else
                                     "NON e' libero: c'e' roba di un giro precedente"))
    return d


def server_vivo():
    """⛔ «La sessione non si apre» e «il server non c'e'» sono due guasti
       diversi, e vanno detti con due frasi diverse: un banco che li confonde
       manda a cercare il difetto nel posto sbagliato."""
    rc, out, _ = root("systemctl is-active %s.service" % UNITA)
    return out.strip() == "active"


# ═══════════════════════════════════════════════════════════════════════════
# LA TARATURA DEL METRO DI GPU — ⛔ PRIMA di crederci
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ Il metro tarato si chiede prima all'agente A1 (`banchi/10-b87-metro-gpu.py`):
#    se c'e', lo si dichiara e si usa quello.  Se non c'e', si tara qui — e
#    l'esito **si dichiara accanto a ogni numero di GPU**.
def metro_di_a1():
    p = os.path.join(QUI, "10-b87-metro-gpu.py")
    return p if os.path.exists(p) else None


def tara_gpu(secondi=20):
    """⛔ Si inietta un carico NOTO e si verifica che il metro lo ritrovi.
       Il noto qui e' il **rapporto**: stessa scena, stessa durata, 15 e 30
       fotogrammi/s ⇒ il doppio dei fotogrammi codificati.  Il metro deve dire
       ~2, e i nanosecondi per fotogramma devono restare gli stessi."""
    print("\n== ⛔ LA TARATURA DEL METRO DI GPU (`LEZIONI.md` §1.33 · regola 6)")
    a1 = metro_di_a1()
    print("   metro di A1 (`10-b87-metro-gpu.py`): %s"
          % (a1 if a1 else "⚠ NON c'e' — taro il mio e lo dichiaro"))
    esiti = {}
    for ritmo in (15, 30):
        etich = "tara-%d" % ritmo
        usc = "%s/b89-%s.jsonl" % (LAV, etich)
        # ⛔ `-re` legge la sorgente in tempo reale: in `secondi` secondi
        #    ffmpeg codifica esattamente `ritmo * secondi` fotogrammi, ed e'
        #    il numero NOTO che il metro deve ritrovare.
        root("systemctl stop b89-tara.service 2>/dev/null; "
             "systemctl reset-failed b89-tara.service 2>/dev/null; true")
        rc, out, err = root(
            "systemd-run --unit=b89-tara --collect "
            "--property=StandardOutput=append:%s/b89-tara.log "
            "--property=StandardError=append:%s/b89-tara.log "
            "/usr/bin/ffmpeg -hide_banner -loglevel error -re -f lavfi "
            "-i testsrc2=size=1920x1080:rate=%d -t %d "
            "-vaapi_device /dev/dri/renderD128 -vf format=nv12,hwupload "
            "-c:v h264_vaapi -f null -" % (LAV, LAV, ritmo, secondi + 6))
        if rc != 0:
            return {"guasto": "⛔ ffmpeg non e' partito: %s" % (out + err)[:300]}
        time.sleep(2.0)                     # il tempo di aprire il nodo DRM
        d = campiona(secondi, usc, etichetta=etich)
        root("systemctl stop b89-tara.service 2>/dev/null; true")
        if d is None:
            return {"guasto": "⛔ l'agente non ha campionato"}
        g = d["gpu"].get("taratura")
        if g is None:
            return {"guasto": "⛔ il metro non ha visto nessun cliente DRM per ffmpeg: "
                              "NON ho misurato (e non e' uno zero)"}
        fot = ritmo * d["durata_s"]
        ns = g.get("video", 0)
        esiti[ritmo] = {"fotogrammi_attesi": round(fot),
                        "video_ns": ns, "ns_per_fotogramma": round(ns / fot) if fot else None,
                        "occupazione_video": round(ns / (d["durata_s"] * 1e9), 4),
                        "render_ns": g.get("render", 0),
                        "durata_s": round(d["durata_s"], 1)}
        print("   %2d fotogrammi/s ⇒ %6d fotogrammi · motore di CODIFICA %10d ns "
              "(%d ns/fotogramma, occupazione %.1f%% di un motore)"
              % (ritmo, esiti[ritmo]["fotogrammi_attesi"], ns,
                 esiti[ritmo]["ns_per_fotogramma"] or 0,
                 100 * esiti[ritmo]["occupazione_video"]))
    a, b = esiti[15], esiti[30]
    if not a["video_ns"] or not b["video_ns"]:
        return dict(esiti=esiti, tarato=False,
                    perche="⛔ uno dei due carichi noti ha dato 0 ns: il metro e' cieco")
    rapporto = b["video_ns"] / a["video_ns"]
    scarto_per_fot = abs(b["ns_per_fotogramma"] - a["ns_per_fotogramma"]) / a["ns_per_fotogramma"]
    # ⛔ Il verso PRIMA del valore (`REVIEWER.md` E15): se il metro non ordina
    #    i due estremi noti nel verso giusto, tararlo e' tempo perso.
    ordina = b["video_ns"] > a["video_ns"]
    tarato = ordina and 1.6 <= rapporto <= 2.4 and scarto_per_fot <= 0.25
    print("   ⭐ il noto era **2,00**; il metro dice **%.2f** "
          "(ns per fotogramma: %d contro %d, scarto %.0f %%)"
          % (rapporto, b["ns_per_fotogramma"], a["ns_per_fotogramma"], 100 * scarto_per_fot))
    print("   %s il metro %s" % ("OK " if tarato else "⛔ ",
                                 "E' TARATO: i suoi numeri si riferiscono"
                                 if tarato else "NON e' tarato: i numeri di GPU si "
                                 "riportano come `[?]`"))
    return {"esiti": esiti, "rapporto": round(rapporto, 3), "atteso": 2.0,
            "ordina": ordina, "scarto_ns_per_fotogramma": round(scarto_per_fot, 3),
            "tarato": tarato, "metro_di_a1": a1}


# ═══════════════════════════════════════════════════════════════════════════
# IL CAMPIONATORE — l'agente gira SULLA MACCHINA, e qui si spoglia
# ═══════════════════════════════════════════════════════════════════════════
def agente_accendi(secondi, uscita, memoria_rotta=False, gpu_rotta=False):
    root("systemctl stop %s.service 2>/dev/null; "
         "systemctl reset-failed %s.service 2>/dev/null; true" % (UNITA_AGENTE, UNITA_AGENTE))
    cmd = ("systemd-run --unit=%s --collect "
           "--property=StandardOutput=append:%s/b89-agente.log "
           "--property=StandardError=append:%s/b89-agente.log "
           "/usr/bin/python3 %s/10-b89-agente.py --uid %d --albero %s "
           "--secondi %g --uscita %s%s%s"
           % (UNITA_AGENTE, LAV, LAV, LAV, UID_B, ALBERO, secondi, uscita,
              " --memoria-rotta" if memoria_rotta else "",
              " --gpu-rotta" if gpu_rotta else ""))
    rc, out, err = root(cmd)
    if rc != 0:
        print("   ⛔ l'agente non e' partito: %s" % (out + err)[:300])
        return False
    return True


def agente_aspetta(tetto):
    fine = time.time() + tetto
    while time.time() < fine:
        rc, out, _ = root("systemctl is-active %s.service" % UNITA_AGENTE)
        if out.strip() not in ("active", "activating"):
            return True
        time.sleep(1)
    return False


def campiona(secondi, uscita, etichetta="", memoria_rotta=False, gpu_rotta=False,
             durante=None):
    """Accende l'agente, lascia correre `durante()` (se c'e'), e spoglia."""
    if not agente_accendi(secondi, uscita, memoria_rotta, gpu_rotta):
        return None
    if durante is not None:
        durante()
    else:
        time.sleep(secondi + 1)
    if not agente_aspetta(secondi + 120):
        print("   ⛔ l'agente non e' finito in tempo")
        root("systemctl stop %s.service; true" % UNITA_AGENTE)
        return None
    rc, jl, _ = root("cat %s 2>/dev/null || true" % uscita, 180)
    righe = [json.loads(x) for x in jl.splitlines() if x.strip()]
    if len(righe) < 2 or righe[0].get("che") != "intestazione":
        print("   ⛔ l'agente non ha lasciato campioni leggibili")
        return None
    testa = righe[0]
    coda = [x for x in righe if x.get("che") == "coda"]
    if not coda:
        print("   ⛔ l'agente non ha scritto la coda: NON ha finito il giro")
        return None
    coda = coda[0]
    with open(os.path.join(FUORI, "agente-%s.jsonl" % (etichetta or "giro")), "w") as f:
        f.write(jl)
    return spoglia_agente(testa, coda)


def spoglia_agente(testa, coda):
    durata = coda["durata_s"]
    hz = testa["hz"]
    fili = testa["cpu_filati"] or 20
    d = {"durata_s": durata, "campioni": coda["campioni"], "cpu_filati": fili,
         "gpu_altre_schede": coda.get("gpu_altre_schede", {}),
         "gt": coda.get("gt_act_mhz"), "gt_fine": coda.get("gt_fine")}
    # ⛔⛔ La residenza in RC6 e' una SECONDA misura, indipendente dai fdinfo:
    #     `100 − RC6` e' il tetto superiore all'occupazione di tutta la scheda
    #     (`10-b87-metro-gpu.py`, agente A1).  Se i fdinfo dicessero piu' di
    #     quello, uno dei due metri sta mentendo.
    gi, gf = (testa.get("gt_inizio") or {}), (coda.get("gt_fine") or {})
    if gi.get("rc6_ms") is not None and gf.get("rc6_ms") is not None and durata > 0:
        d["rc6_per_cento"] = round(100 * (gf["rc6_ms"] - gi["rc6_ms"]) / (durata * 1000), 1)
        d["gpu_accesa_per_cento"] = round(100 - d["rc6_per_cento"], 1)
    else:
        d["rc6_per_cento"] = None
        d["gpu_accesa_per_cento"] = None

    # ── CPU ────────────────────────────────────────────────────────────────
    cpu = {}
    for g, tac in coda["cpu_tacche"].items():
        letti = coda["cpu_letti"].get(g, 0)
        if letti == 0:
            cpu[g] = None                # ⛔ non ho letto: None, non zero
            continue
        s = tac / hz
        cpu[g] = {"secondi_cpu": round(s, 2),
                  "per_cento_di_un_filo": round(100 * s / durata, 1),
                  "per_cento_della_macchina": round(100 * s / durata / fili, 2)}
    d["cpu"] = cpu

    # ── GPU ────────────────────────────────────────────────────────────────
    # ⛔ «Nessun cliente DRM in tutta la macchina» non e' uno zero: e' un
    #    lettore che non ha letto.  Il gnome-shell della sessione UN cliente
    #    DRM ce l'ha di sicuro — e' il controllo positivo di questo metro.
    if not coda.get("gpu_letture_ok"):
        d["gpu"] = None
        d["gpu_perche"] = ("⛔ il lettore di `/proc/<pid>/fdinfo` non ha letto NIENTE: "
                           "None, non zero")
    else:
        gpu = {}
        for g, motori in coda["gpu_ns"].items():
            gpu[g] = {k: v for k, v in motori.items()}
        d["gpu"] = gpu
        # ⛔ il controllo positivo: la sessione grafica DEVE avere un motore di
        #    rendering che si muove.  Se e' fermo, o il metro e' cieco o la
        #    sessione non c'e' — e in nessuno dei due casi si riferisce.
        r = (gpu.get("grafica") or {}).get("render", 0)
        d["gpu_controllo_positivo"] = r > 0
    d["gpu_letture_ok"] = coda.get("gpu_letture_ok")

    # ── memoria ────────────────────────────────────────────────────────────
    mem = {}
    for g in coda["memoria_fine"]:
        f = coda["memoria_fine"][g]
        i = testa["memoria_inizio"].get(g, {})
        if f.get("misurato", 0) is None:
            mem[g] = None                # ⛔ None, non zero
            continue
        mem[g] = {"rss_mb": round(f["rss_kb"] / 1024, 1),
                  "pss_mb": round(f["pss_kb"] / 1024, 1),
                  "uss_mb": round(f["uss_kb"] / 1024, 1),
                  "processi": f["letti"], "mancati": f["mancati"],
                  "pss_mb_inizio": round(i["pss_kb"] / 1024, 1)
                                   if i.get("misurato", 0) is not None else None}
    d["memoria"] = mem

    # ── filo ───────────────────────────────────────────────────────────────
    fi, ff = testa.get("filo_inizio"), coda.get("filo_fine")
    if not fi or not ff:
        d["filo"] = None
    else:
        by = ff["tx_byte"] - fi["tx_byte"]
        pa = ff["tx_pac"] - fi["tx_pac"]
        d["filo"] = {"byte": by, "pacchetti": pa,
                     "mbit_s": round(by * 8 / durata / 1e6, 3),
                     "byte_per_pacchetto": round(by / pa, 1) if pa else None}
    return d


# ═══════════════════════════════════════════════════════════════════════════
# LE SCENE
# ═══════════════════════════════════════════════════════════════════════════
def scena_spegni():
    rc, out, _ = root("env LAV=%s UID_B=%d UTENTE=%s sh %s/10-b89-scena.sh -- spegni"
                      % (LAV, UID_B, UTENTE, LAV), 120)
    return "SPENTO TUTTO" in out, out.strip()[:200]


def esci_dalla_vista():
    """⛔ La sessione headless di GNOME sta nella vista d'insieme e ci resta:
       le finestre sarebbero **anteprime rimpicciolite** (`09-b72`, 23 ago).
       L'ESC si manda per la porta che usa il prodotto."""
    rc, out, err = root("python3 %s/09-b72-tasto.py --uid %d --tasti 1"
                        % (LAV, UID_B), 90)
    return "TASTI MANDATI" in out


def scena_accendi(quale):
    """⛔ «ferma» non e' «una scena che non si muove»: e' **nessuna scena**, e
       si VERIFICA che non sia rimasto niente acceso dal giro prima."""
    if quale == "ferma":
        ok, chi = scena_spegni()
        if not ok:
            return False, "⛔ «ferma» non e' ferma: %s" % chi
        time.sleep(1.5)
        return True, "nessuna scena, nessuna finestra"
    scena_spegni()
    usc = b68.monitor()
    if not usc:
        return False, "⛔ nessun monitor nel registro: il palco non e' mai nato"
    if quale == "desktop":
        rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s sh %s/10-b89-scena.sh finestre"
                            % (LAV, UID_B, UTENTE, LAV), 180)
        if "FINESTRE CHIESTE" not in out:
            return False, "⛔ le finestre non si sono aperte: %s" % (out + err)[:300]
        finestre = out.strip().splitlines()[-1]
        rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s sh %s/10-b89-scena.sh strappi %s"
                            % (LAV, UID_B, UTENTE, LAV, usc), 180)
        if "SCENA ACCESA" not in out:
            return False, "⛔ la scena a strappi non e' partita: %s" % (out + err)[:300]
        esci_dalla_vista()
        return True, "%s + scena in finestra su «%s»" % (finestre, usc)
    rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s sh %s/10-b89-scena.sh continuo %s"
                        % (LAV, UID_B, UTENTE, LAV, usc), 180)
    if "SCENA ACCESA" not in out:
        return False, "⛔ la scena continua non e' partita: %s" % (out + err)[:300]
    esci_dalla_vista()
    return True, "scena a schermo intero su «%s», movimento pieno" % usc


# ═══════════════════════════════════════════════════════════════════════════
# IL BATTITORE — gli strappi, e con loro il RISVEGLIO (pixel → byte fuori)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Si chiama `09-b71-agente.py` a mano invece di `b71.arm()` per una ragione
#    sola e non negoziabile: `arm()` ha `--shm 09-b68` **scritto dentro**, e
#    `/dev/shm` e' UNO su tutta la macchina.  Due agenti della fase 10 con lo
#    stesso nome si leggerebbero i disegni a vicenda **senza dare rosso**.
def batti(etichetta, pulsazioni, quiete=1.0, accensione=0.30):
    usc = "%s/b89-batti-%s.jsonl" % (LAV, etichetta)
    tetto = int(pulsazioni * (quiete + accensione + 1.5) + 120)
    rc, out, err = root("python3 %s/09-b71-agente.py --shm 10-b89 --pulsazioni %d "
                        "--quiete %.3f --accensione %.3f --etichetta %s --uscita %s"
                        % (LAV, pulsazioni, quiete, accensione, etichetta, usc), tetto)
    if rc != 0:
        return {"guasto": "⛔ il battitore: %s" % (out + err).strip()[:400]}
    rc, jl, _ = root("cat %s" % usc, 120)
    righe = [json.loads(x) for x in jl.splitlines() if x.strip()]
    if not righe:
        return {"guasto": "⛔ il battitore non ha lasciato niente"}
    return {"testa": righe[0], "battute": [x for x in righe if "pulsazione" in x]}


def risveglio(bat, reg_testo):
    """Il tratto **primo pixel → byte fuori dal server**, per ogni strappo.
       ⚠ NON e' l'anello intero: manca il volo, la decodifica e la pittura."""
    if "guasto" in bat:
        return None, bat["guasto"]
    testa = bat["testa"]
    hh, mm, resto = testa["ancora_locale"].split(":")
    ss, ms = resto.split(".")
    mez = testa["ancora_epoch"] - sdg(hh, mm, ss, ms)
    sped = sorted((mez + sdg(m.group(1), m.group(2), m.group(3), m.group(4)),
                   m.group(6), int(m.group(10)))
                  for m in R_SPED.finditer(reg_testo))
    fuori, colpi_buoni = [], 0
    for b in bat["battute"]:
        td = b.get("t_disegno")
        if not td:
            fuori.append(None)
            continue
        dopo = [x for x in sped if x[0] > td - 0.002]
        if not dopo:
            fuori.append(None)
            continue
        colpi_buoni += 1
        fuori.append(round((dopo[0][0] - td) * 1000, 1))
    n = len(bat["battute"])
    return ({"risveglio_ms": stat(fuori), "colpi": n, "colpi_buoni": colpi_buoni,
             "frazione_buoni": round(colpi_buoni / n, 2) if n else None}, None)


# ═══════════════════════════════════════════════════════════════════════════
# LO SPOGLIO DEL REGISTRO — quel che l'utente vede
# ═══════════════════════════════════════════════════════════════════════════
def resa(reg_testo, durata):
    sped = [(sdg(m.group(1), m.group(2), m.group(3), m.group(4)), m.group(6),
             int(m.group(8)), int(m.group(9)), int(m.group(10)))
            for m in R_SPED.finditer(reg_testo)]
    sped.sort()
    n = len(sped)

    # ⛔⛔ IL METRO SI CONTROLLA DA SE' — 25 agosto 2026.
    #
    #   Il 25 agosto la cura del registro ha anteposto `[nome] ` al corpo di
    #   ogni riga, e questo modello — ancorato su «ora + area + corpo» — ha
    #   smesso di trovare qualunque cosa.  ⛔ Il guaio non e' che si e'
    #   fermato: e' che ha restituito **zero fotogrammi** su un server che li
    #   spediva tutti, cioe' un numero che ACCUSA il prodotto.
    #
    # ⇒ Si contano le occorrenze CRUDE della parola nel testo, e se ce ne sono
    #   ma il modello non ne ha prese, il metro e' rotto e **lo dice**.  Uno
    #   zero vero e uno zero da modello morto hanno la stessa faccia: l'unico
    #   modo di distinguerli e' guardare il testo con occhi piu' grossolani.
    crude = reg_testo.count(" SPEDITO:")
    if crude and n == 0:
        raise SystemExit(
            "⛔⛔ IL METRO E' ROTTO: nel registro ci sono %d righe con « SPEDITO:» "
            "e il modello R_SPED non ne ha presa NESSUNA.\n"
            "    Non riferisco «zero fotogrammi»: sarebbe un'accusa al prodotto "
            "per un difetto del banco.\n"
            "    ⇒ Guarda R_SPED: la forma della riga e' cambiata." % crude)

    if n == 0:
        # ⛔ Zero fotogrammi e' un FATTO su una scena ferma e un GUASTO su una
        #    scena che si muove: qui si riporta il fatto, e a giudicare e' il
        #    predicato della scena, non questa funzione.
        # ⭐ E adesso e' uno zero VERO: il controllo qui sopra ha escluso che
        #    sia il modello a non vedere.
        return {"fotogrammi": 0, "fotogrammi_s": 0.0, "byte_totali": 0,
                "byte_medio_fotogramma": None, "chiavi": 0, "delta": 0,
                "tela": None, "mpixel_s": 0.0, "cadenza_ms": None,
                "kbit_s_carico_video": 0.0}
    byte = sum(x[4] for x in sped)
    tele = {}
    for x in sped:
        tele["%dx%d" % (x[2], x[3])] = tele.get("%dx%d" % (x[2], x[3]), 0) + 1
    tela = max(tele, key=tele.get)
    l, h = (int(v) for v in tela.split("x"))
    gap = [round((sped[i + 1][0] - sped[i][0]) * 1000, 1) for i in range(n - 1)]
    fps = n / durata
    return {"fotogrammi": n, "fotogrammi_s": round(fps, 2),
            "byte_totali": byte, "byte_medio_fotogramma": round(byte / n),
            "byte_max_fotogramma": max(x[4] for x in sped),
            "chiavi": sum(1 for x in sped if x[1] == "CHIAVE"),
            "delta": sum(1 for x in sped if x[1] == "delta"),
            "tela": tela, "tele_viste": tele,
            "mpixel_s": round(l * h * fps / 1e6, 2),
            "cadenza_ms": stat(gap),
            "kbit_s_carico_video": round(byte * 8 / durata / 1000, 1)}


# ⛔⛔ IL PREDICATO CHE SMASCHERA UNA SCENA CHE NON MORDE (`LEZIONI.md` §1.30)
def scena_morde(quale, r, ris):
    """Torna (bool, perche').  ⛔ Sta QUI, dove il numero SI CONSUMA, e non
       dentro `resa()`, dove si produce (`LEZIONI.md` §1.29 corollario 2)."""
    if quale == "ferma":
        if r["fotogrammi_s"] > SOGLIA_FPS_FERMA:
            return False, ("⛔ «ferma» NON e' ferma: %.2f fotogrammi/s (> %.1f). "
                           "Qualcosa e' rimasto acceso sotto"
                           % (r["fotogrammi_s"], SOGLIA_FPS_FERMA))
        return True, ("il desktop e' davvero fermo: %d fotogrammi in tutto"
                      % r["fotogrammi"])
    # ⛔ IL RITMO PRIMA DEI BYTE, per «continuo»: e' la grandezza che ORDINA i
    #    due estremi noti (vedi il riquadro sulle soglie, e `REVIEWER.md` E15).
    if quale == "continuo" and r["fotogrammi_s"] < SOGLIA_FPS_CONTINUO:
        return False, ("⛔ «movimento continuo» che NON si muove: %.2f "
                       "fotogrammi/s (< %.1f) — e i byte per fotogramma erano %s, "
                       "cioe' NON avrebbero smascherato niente"
                       % (r["fotogrammi_s"], SOGLIA_FPS_CONTINUO,
                          r["byte_medio_fotogramma"]))
    if r["byte_medio_fotogramma"] is None or r["byte_medio_fotogramma"] < SOGLIA_BYTE_MORDE:
        return False, ("⛔ LA SCENA NON MORDE: %s byte per fotogramma (< %d). "
                       "In fase 9 tre giudizi sono stati buttati per questo"
                       % (r["byte_medio_fotogramma"], SOGLIA_BYTE_MORDE))
    if quale == "continuo":
        return True, ("%.1f fotogrammi/s da %d byte l'uno (%.1f kbit/s di carico "
                      "video — ⚠ e non e' il caso peggiore in BYTE: le bande di "
                      "colore si comprimono benissimo)"
                      % (r["fotogrammi_s"], r["byte_medio_fotogramma"],
                         r["kbit_s_carico_video"]))
    # desktop: quel che deve mordere sono i COLPI, non il ritmo
    if ris is None:
        return False, "⛔ nessuna misura dei colpi: il battitore non ha battuto"
    if (ris["frazione_buoni"] or 0) < SOGLIA_COLPI_BUONI:
        return False, ("⛔ solo %d strappi su %d hanno prodotto un fotogramma "
                       "(%.0f %% < %.0f %%): la scena a strappi non ha sollecitato"
                       % (ris["colpi_buoni"], ris["colpi"],
                          100 * (ris["frazione_buoni"] or 0), 100 * SOGLIA_COLPI_BUONI))
    return True, ("%d strappi su %d hanno prodotto un fotogramma, %d byte l'uno"
                  % (ris["colpi_buoni"], ris["colpi"], r["byte_medio_fotogramma"]))


# ═══════════════════════════════════════════════════════════════════════════
# UN GIRO INTERO
# ═══════════════════════════════════════════════════════════════════════════
def giro(quale, secondi, assestamento=12, memoria_rotta=False, gpu_rotta=False,
         congela_scena=False):
    print("\n\033[1m== scena «%s» · %d s (piu' %d s di assestamento)\033[0m"
          % (quale, secondi, assestamento))
    d = {"scena": quale, "secondi_chiesti": secondi}

    if not server_vivo():
        d["esito"] = "⛔ IL SERVER (unita' %s) NON E' ATTIVO: non misuro" % UNITA
        print("   " + d["esito"])
        return d

    # ⛔ LA SESSIONE C'E'?  E la dichiara IL PRODOTTO, nel suo registro, non
    #    l'esistenza di un processo (`09-b71`, 23 ago: quattro bracci su sei
    #    hanno misurato il nulla e il banco non se n'e' accorto).
    if not b71.sessione_viva():
        d["esito"] = "⛔ LA SESSIONE NON E' VIVA: non misuro"
        print("   " + d["esito"])
        return d

    ok, dettaglio = scena_accendi(quale)
    d["scena_dettaglio"] = dettaglio
    if not ok:
        d["esito"] = dettaglio
        print("   " + dettaglio)
        return d
    print("   OK  %s" % dettaglio)

    if congela_scena:
        # ⛔ IL GUASTO G4, INNESTATO: la scena che dice di muoversi e sta ferma.
        rc, out, _ = root("pkill -STOP -u %d -f 04-b30-scena && echo CONGELATA" % UID_B)
        print("   ⛔ GUASTO INNESTATO: la scena e' CONGELATA (SIGSTOP) — %s"
              % ("congelata" if "CONGELATA" in out else "non sono riuscito"))

    # ⚠ `CODER.md` §3.5: un campione preso all'avvio non dice niente del regime.
    print("   --  assestamento %d s (si misura il REGIME, non l'avvio)" % assestamento)
    time.sleep(assestamento)

    riga0 = b68.righe_registro()
    fb, pb = b68.filo()
    usc = "%s/b89-%s.jsonl" % (LAV, quale)
    bat = {"guasto": "(nessun battitore: scena senza strappi)"}

    def durante():
        if quale != "desktop":
            time.sleep(secondi + 1)
            return
        # gli strappi: ~1,3 s l'uno ⇒ tanti quanti ne stanno nella finestra
        n = max(4, int(secondi / (1.0 + 0.30 + 0.30)))
        bat.clear()
        bat.update(batti(quale, n, quiete=1.0, accensione=0.30))

    d0 = campiona(secondi, usc, etichetta=quale, memoria_rotta=memoria_rotta,
                  gpu_rotta=gpu_rotta, durante=durante)
    fa, pa = b68.filo()
    if congela_scena:
        root("pkill -CONT -u %d -f 04-b30-scena; true" % UID_B)

    if d0 is None:
        d["esito"] = "⛔ IL CAMPIONATORE NON HA MISURATO: non giudico"
        print("   " + d["esito"])
        return d
    d.update(d0)

    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    with open(os.path.join(FUORI, "reg-%s.log" % quale), "w") as f:
        f.write(reg)
    d["resa"] = resa(reg, d["durata_s"])
    d["filo_lo_dal_portatile"] = {"byte": fa - fb, "pacchetti": pa - pb,
                                  "mbit_s": round((fa - fb) * 8 / d["durata_s"] / 1e6, 3)}
    ris, guasto_ris = (None, None)
    if quale == "desktop":
        ris, guasto_ris = risveglio(bat, reg)
    d["risveglio"] = ris
    d["risveglio_guasto"] = guasto_ris

    morde, perche = scena_morde(quale, d["resa"], ris)
    d["scena_morde"] = morde
    d["scena_morde_perche"] = perche

    if not b71.sessione_viva():
        d["esito"] = "⛔ LA SESSIONE E' MORTA DURANTE IL GIRO: il numero non vale"
        print("   " + d["esito"])
        return d
    d["esito"] = "OK" if morde else "⛔ la scena non ha sollecitato"
    return d


# ═══════════════════════════════════════════════════════════════════════════
# LA STAMPA
# ═══════════════════════════════════════════════════════════════════════════
def stampa(d):
    if "resa" not in d:
        print("   %s" % d.get("esito", "⛔ niente"))
        return
    r = d["resa"]
    print("\n   \033[1mQUEL CHE L'UTENTE VEDE\033[0m — %s" % d["scena_morde_perche"])
    print("     fotogrammi %d in %.1f s ⇒ %.2f/s · %s byte l'uno (max %s) · tela %s ⇒ %.2f Mpixel/s"
          % (r["fotogrammi"], d["durata_s"], r["fotogrammi_s"],
             r["byte_medio_fotogramma"], r.get("byte_max_fotogramma"),
             r["tela"], r["mpixel_s"]))
    if r["cadenza_ms"]:
        c = r["cadenza_ms"]
        print("     cadenza fra due fotogrammi: mediana %.1f ms · p95 %.1f · max %.1f"
              % (c["mediana"], c["p95"], c["max"]))
    if d.get("risveglio"):
        s = d["risveglio"]["risveglio_ms"]
        print("     ⭐ RISVEGLIO (pixel → byte fuori dal server): mediana %s ms · "
              "p95 %s · n=%s  [%d colpi su %d hanno prodotto un fotogramma]"
              % (s["mediana"] if s else "?", s["p95"] if s else "?",
                 s["n"] if s else 0, d["risveglio"]["colpi_buoni"], d["risveglio"]["colpi"]))
    elif d.get("risveglio_guasto"):
        print("     ⚠ risveglio: %s" % d["risveglio_guasto"])

    print("   \033[1mMEMORIA\033[0m (⛔ PSS e USS, non solo RSS: dieci figli condividono le librerie)")
    for g in ("padre", "figlio", "grafica", "scena", "cliente"):
        m = d["memoria"].get(g)
        if m is None:
            print("     %-9s ⛔ NON MISURATA (None, non zero)" % g)
            continue
        if m["processi"] == 0:
            continue
        print("     %-9s %3d proc · RSS %8.1f MB · PSS %8.1f MB · USS %8.1f MB%s"
              % (g, m["processi"], m["rss_mb"], m["pss_mb"], m["uss_mb"],
                 "  ⚠ %d non letti" % m["mancati"] if m["mancati"] else ""))

    print("   \033[1mCPU\033[0m (i5-13500T, %d filati)" % d["cpu_filati"])
    for g in ("padre", "figlio", "grafica", "scena", "cliente", "agente"):
        c = d["cpu"].get(g)
        if c is None:
            print("     %-9s ⛔ NON MISURATA" % g)
            continue
        if c["secondi_cpu"] == 0:
            continue
        print("     %-9s %7.2f s di CPU ⇒ %6.1f %% di un filo · %5.2f %% della macchina"
              % (g, c["secondi_cpu"], c["per_cento_di_un_filo"],
                 c["per_cento_della_macchina"]))

    if d["gpu"] is None:
        print("   \033[1mGPU\033[0m  ⛔ %s" % d.get("gpu_perche", "non misurata"))
    else:
        print("   \033[1mGPU\033[0m Intel UHD 730 (`renderD128`) — occupazione di UN motore")
        for g in ("grafica", "figlio", "scena", "padre"):
            m = d["gpu"].get(g) or {}
            righe = [(k, v) for k, v in sorted(m.items()) if v]
            if not righe:
                continue
            print("     %-9s %s" % (g, " · ".join(
                "%s %.2f %% (%.1f ms/s)"
                % (MOTORI_NOMI.get(k, k), 100 * v / (d["durata_s"] * 1e9),
                   v / d["durata_s"] / 1e6) for k, v in righe)))
        g = d.get("gt") or {}
        print("     ⛔ contesto GT (senza, l'occupazione e' un numero senza unita' —"
              " `10-b87` §CLOCK, fattore 3,8): %s MHz medi (min %s, max %s) · "
              "GT accesa il %s %% del tempo (100 − RC6)"
              % (g.get("media"), g.get("min"), g.get("max"), d.get("gpu_accesa_per_cento")))
        if not d.get("gpu_controllo_positivo"):
            print("     ⛔ CONTROLLO POSITIVO FALLITO: il motore di rendering della "
                  "sessione grafica e' fermo — o il metro e' cieco o la sessione non c'e'")
    if d["gpu_altre_schede"]:
        print("     ⚠ contatori visti su ALTRE schede (non l'integrata): %s"
              % d["gpu_altre_schede"])

    if d["filo"] is None:
        print("   \033[1mFILO\033[0m ⛔ NON MISURATO")
    else:
        f = d["filo"]
        print("   \033[1mFILO\033[0m `lo`: %.3f Mbit/s (%d byte, %d pacchetti, %s byte/pacchetto)"
              % (f["mbit_s"], f["byte"], f["pacchetti"], f["byte_per_pacchetto"]))
        print("     ⚠ il filo porta anche QUIC, l'audio PCM e i riscontri: il carico "
              "video da solo e' %.1f kbit/s" % d["resa"]["kbit_s_carico_video"])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA PREVISIONE PER DIECI — ⛔ una PREVISIONE, non un risultato
# ═══════════════════════════════════════════════════════════════════════════
def per_dieci(d, n=10):
    """⛔ `DECISIONI.md` §4.6 promette dieci sessioni.  Questo e' il conto che
       ne esce **moltiplicando una sessione**, e va tenuto separato dalla
       verifica con dieci sessioni vere (agente A6): finche' non si incontrano
       sono due cose diverse.

       ⭐ E la moltiplicazione della memoria si fa in DUE modi, perche' la
       verita' sta fra i due:
         · **basso**  = n × USS + (PSS − USS) contato **una volta sola**: le
           pagine condivise fra dieci figli restano una copia;
         · **alto**   = n × PSS: come se non condividessero niente."""
    if "resa" not in d or d.get("memoria") is None:
        return None
    mem = d["memoria"]
    per_sessione = ("figlio", "grafica")
    if any(mem.get(g) is None for g in per_sessione) or mem.get("padre") is None:
        return {"guasto": "⛔ manca una lettura di memoria: NON moltiplico per dieci"}
    uss = sum(mem[g]["uss_mb"] for g in per_sessione)
    pss = sum(mem[g]["pss_mb"] for g in per_sessione)
    condiviso = max(0.0, pss - uss)
    padre_pss = mem["padre"]["pss_mb"]
    basso = (n * uss + condiviso + padre_pss) / 1024.0
    alto = (n * pss + padre_pss) / 1024.0

    cpu = d["cpu"]
    if any(cpu.get(g) is None for g in per_sessione):
        cpu_dieci = None
    else:
        c = sum(cpu[g]["per_cento_della_macchina"] for g in per_sessione)
        cpu_dieci = round(n * c, 1)

    gpu_dieci = None
    if d["gpu"] is not None:
        somma = {}
        for g in per_sessione + ("padre",):
            for k, v in (d["gpu"].get(g) or {}).items():
                somma[k] = somma.get(k, 0) + v
        gpu_dieci = {k: round(100 * n * v / (d["durata_s"] * 1e9), 1)
                     for k, v in somma.items() if v}

    filo_dieci = round(n * d["filo"]["mbit_s"], 1) if d["filo"] else None
    px_dieci = round(n * d["resa"]["mpixel_s"], 1)
    return {"n": n, "memoria_gb_basso": round(basso, 2), "memoria_gb_alto": round(alto, 2),
            "uss_per_sessione_mb": round(uss, 1), "pss_per_sessione_mb": round(pss, 1),
            "condiviso_una_volta_mb": round(condiviso, 1), "padre_pss_mb": round(padre_pss, 1),
            "cpu_per_cento_macchina": cpu_dieci, "gpu_per_cento_motore": gpu_dieci,
            "filo_mbit_s": filo_dieci, "mpixel_s": px_dieci}


def stampa_dieci(p, scena):
    if p is None:
        print("   ⛔ non moltiplico: manca una misura")
        return
    if "guasto" in p:
        print("   " + p["guasto"])
        return
    print("\n\033[1m   ⭐ PREVISIONE PER %d SESSIONI — scena «%s»\033[0m"
          "   ⛔ e' una PREVISIONE: la verifica e' di A6, con dieci sessioni vere"
          % (p["n"], scena))
    print("     MEMORIA   fra %.2f e %.2f GB dei 31"
          "   (USS %.0f MB + PSS %.0f MB per sessione, %.0f MB condivisi, padre %.0f MB)"
          % (p["memoria_gb_basso"], p["memoria_gb_alto"], p["uss_per_sessione_mb"],
             p["pss_per_sessione_mb"], p["condiviso_una_volta_mb"], p["padre_pss_mb"]))
    print("     PIXEL     %.1f Mpixel/s da codificare" % p["mpixel_s"])
    print("     FILO      %.1f Mbit/s" % (p["filo_mbit_s"] or 0))
    print("     CPU       %.1f %% della macchina (%d filati)"
          % (p["cpu_per_cento_macchina"] or 0, 20))
    if p["gpu_per_cento_motore"]:
        print("     GPU       %s" % " · ".join(
            "%s %.1f %%" % (MOTORI_NOMI.get(k, k), v)
            for k, v in sorted(p["gpu_per_cento_motore"].items())))
    # ⭐ QUALE FINISCE PER PRIMA
    corse = []
    if p["memoria_gb_alto"]:
        corse.append(("memoria", 100 * p["memoria_gb_alto"] / 31.0, "dei 31 GB"))
    if p["cpu_per_cento_macchina"]:
        corse.append(("CPU", p["cpu_per_cento_macchina"], "della macchina"))
    for k, v in (p["gpu_per_cento_motore"] or {}).items():
        # ⚠ I VDBOX sono DUE (`drm-engine-capacity-video: 2`): il 100 % di UN
        #   motore video e' il 50 % della capacita' della scheda.  Il motore di
        #   rendering e' UNO, e li' 100 % vuol dire saturo.
        cap = CAPACITA.get(k, 1)
        corse.append(("GPU " + MOTORI_NOMI.get(k, k), v / cap,
                      "della capacita' (%d motore/i)" % cap))
    if p["filo_mbit_s"]:
        # ⭐ il budget di rete: `DECISIONI.md` §3.1-bis punto 2 — 10 × 30 Mbit/s
        corse.append(("filo", 100 * p["filo_mbit_s"] / 300.0, "dei 300 Mbit/s di §3.1-bis"))
    corse.sort(key=lambda x: -x[1])
    print("     ⭐ CHI FINISCE PER PRIMA: %s"
          % " > ".join("%s %.0f %% %s" % c for c in corse))
    # ⛔⛔ E IL LIMITE DI QUESTA RIGA, che va letto PRIMA dei numeri:
    print("     ⛔ la colonna GPU e' un TETTO SUPERIORE, non un valore: "
          "`10-b87-metro-gpu.py` §CLOCK misura che la stessa codifica occupa "
          "**3,8 volte** piu' tempo con la GT a 300 MHz che a 1550. Qui la GT "
          "era bassa (carico leggero) ⇒ moltiplicando per dieci si SOVRASTIMA. "
          "Il valore vero sta fra questo numero e questo diviso ~4, e a "
          "deciderlo sono le dieci sessioni vere di A6.")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ `--certifica` — I GUASTI SI INNESTANO E SI FANNO GIRARE
# ═══════════════════════════════════════════════════════════════════════════
def certifica(secondi=18):
    print("\n\033[1m════ ⛔⛔ CERTIFICA — un banco non e' finito finche' non "
          "l'ho visto dare ROSSO (`LEZIONI.md` §1.29)\033[0m")
    esiti = []

    def segna(nome, atteso, avuto, dettaglio=""):
        ok = (atteso == avuto)
        esiti.append({"guasto": nome, "atteso": atteso, "avuto": avuto,
                      "come_deve": ok, "dettaglio": dettaglio[:300]})
        print("   %s %-46s atteso %-6s avuto %-6s  %s"
              % ("OK " if ok else "⛔ ", nome, atteso, avuto, dettaglio[:110]))
        return ok

    # ── G2 · il palco orfano ───────────────────────────────────────────────
    print("\n-- G2 · IL PALCO ORFANO DAL GIRO PRECEDENTE")
    chiudi(parla=False)
    d = posto_libero(parla=False)
    segna("G2 sano — nessun orfano", True, d["libero"],
          "figli %d · scene %d · shell %d" % (len(d["figli_orfani"]),
                                              len(d["scene_orfane"]),
                                              len(d["sessioni_grafiche_orfane"])))
    # l'innesto: un processo dell'utente della sessione che porta nel nome
    # esattamente quel che il guardiano cerca.
    root("setsid setpriv --reuid=%d --regid=%d --init-groups "
         "sh -c 'sleep 200 # 04-b30-scena orfano innestato' >/dev/null 2>&1 & true"
         % (UID_B, UID_B))
    time.sleep(1.5)
    d = posto_libero(parla=False)
    segna("G2 guasto — un orfano innestato ⇒ ROSSO", False, d["libero"],
          "trovati: %s" % (d["scene_orfane"] or d["figli_orfani"]))
    root("pkill -u %d -f '04-b30-scena orfano innestato'; true" % UID_B)
    time.sleep(1.5)
    d = posto_libero(parla=False)
    segna("G2 risanato — l'orfano e' morto", True, d["libero"], "")

    # ── G1 · la sessione non si apre ──────────────────────────────────────
    #
    # ⛔⛔ IL GUASTO SI INNESTA SPEGNENDO IL SERVER, **non** con una parola
    #     sbagliata.  La parola sbagliata farebbe scattare il ban per indirizzo
    #     di `RCP.md` §4.4-bis, che dura **12 ore** e parte dallo stesso
    #     indirizzo di tutti gli altri agenti della fase: un guasto innestato
    #     non deve poter fermare il lavoro di qualcun altro.
    print("\n-- G1 · LA SESSIONE NON SI APRE ⇒ rosso, non «0 fotogrammi, regolare»")
    root("systemctl stop %s.service; true" % UNITA)
    time.sleep(2)
    segna("G1 guasto — il server e' spento", False, server_vivo(), "")
    aperta = b71.sessione_apri("cert-g1", 30, utente=UTENTE, tela=TELA)
    segna("G1 guasto — la sessione NON si apre", False, aperta, "")
    d = giro("continuo", 6, assestamento=1)
    segna("G1 guasto — il giro dice ROSSO invece di «0 fotogrammi, regolare»", False,
          d.get("esito") == "OK", d.get("esito", "?"))
    b71.sessione_chiudi()
    subprocess.run(["bash", os.path.join(QUI, "10-b89-terreno.sh"), "accendi"],
                   capture_output=True)
    time.sleep(2)
    segna("G1 risanato — il server e' riacceso", True, server_vivo(), "")
    aperta = b71.sessione_apri("cert-g1r", 1200, utente=UTENTE, tela=TELA)
    segna("G1 risanato — con la parola vera la sessione si apre", True, aperta, "")
    if not aperta:
        print("   ⛔ senza sessione non posso innestare gli altri tre guasti")
        return esiti
    time.sleep(8)

    # ── G3 · il lettore della memoria ─────────────────────────────────────
    print("\n-- G3 · IL LETTORE DELLA MEMORIA NON LEGGE ⇒ `None`, mai zero")
    usc = "%s/b89-cert-mem.jsonl" % LAV
    d0 = campiona(6, usc, etichetta="cert-mem-sano")
    sano = d0 is not None and d0["memoria"].get("grafica") is not None
    segna("G3 sano — la memoria della sessione grafica si legge", True, sano,
          "PSS %.0f MB" % d0["memoria"]["grafica"]["pss_mb"] if sano else "?")
    d1 = campiona(6, usc, etichetta="cert-mem-rotto", memoria_rotta=True)
    rotto_none = d1 is not None and d1["memoria"].get("grafica") is None
    segna("G3 guasto — lettore rotto ⇒ None (NON zero)", True, rotto_none,
          "grafica = %s" % (d1["memoria"].get("grafica") if d1 else "?"))
    # ⛔ E la guardia sta dove il numero SI CONSUMA: `per_dieci` deve
    #    RIFIUTARSI, non moltiplicare uno zero per dieci.
    p = per_dieci(dict(d1, resa={"mpixel_s": 0}, filo=None)) if d1 else None
    segna("G3 guasto — la moltiplicazione per dieci si RIFIUTA", True,
          bool(p and "guasto" in p), (p or {}).get("guasto", "?"))
    d2 = campiona(6, usc, etichetta="cert-mem-risanato")
    segna("G3 risanato — la memoria si rilegge", True,
          d2 is not None and d2["memoria"].get("grafica") is not None, "")

    # ── G5 · il lettore della GPU ─────────────────────────────────────────
    print("\n-- G5 · IL LETTORE DELLA GPU NON LEGGE ⇒ `None`, e niente colonna GPU")
    d3 = campiona(6, "%s/b89-cert-gpu.jsonl" % LAV, etichetta="cert-gpu-rotto",
                  gpu_rotta=True)
    segna("G5 guasto — fdinfo illeggibile ⇒ gpu = None", True,
          d3 is not None and d3["gpu"] is None, (d3 or {}).get("gpu_perche", "?"))

    # ── G4 · la scena «continuo» che non si muove ─────────────────────────
    print("\n-- G4 · LA SCENA «MOVIMENTO CONTINUO» CHE IN REALTA' NON SI MUOVE")
    d4 = giro("continuo", secondi, assestamento=6)
    stampa(d4)
    segna("G4 sano — la scena continua MORDE", True, bool(d4.get("scena_morde")),
          d4.get("scena_morde_perche", "?"))
    d5 = giro("continuo", secondi, assestamento=6, congela_scena=True)
    if "resa" in d5:
        print("      ⭐ il braccio CONGELATO, per iscritto: %.2f fotogrammi/s · "
              "%s byte per fotogramma  ⇒ e' il RITMO che separa, non i byte"
              % (d5["resa"]["fotogrammi_s"], d5["resa"]["byte_medio_fotogramma"]))
    segna("G4 guasto — scena congelata ⇒ i byte/fotogramma la smascherano", False,
          bool(d5.get("scena_morde")), d5.get("scena_morde_perche", "?"))
    d6 = giro("continuo", secondi, assestamento=6)
    segna("G4 risanato — la scena rimorde", True, bool(d6.get("scena_morde")),
          d6.get("scena_morde_perche", "?"))

    buoni = sum(1 for x in esiti if x["come_deve"])
    print("\n   \033[1m%d predicati su %d si sono comportati come dovevano\033[0m"
          % (buoni, len(esiti)))
    with open(os.path.join(FUORI, "b89-certifica.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    return esiti


# ═══════════════════════════════════════════════════════════════════════════
def chiudi(parla=True):
    scena_spegni()
    b71.sessione_chiudi()
    root("systemctl stop %s.service 2>/dev/null; "
         "systemctl reset-failed %s.service 2>/dev/null; true" % (UNITA_AGENTE, UNITA_AGENTE))
    root("systemctl stop b89-tara.service 2>/dev/null; "
         "systemctl reset-failed b89-tara.service 2>/dev/null; true")
    # ⛔ La sessione grafica SOPRAVVIVE al distacco: e' l'invariante I4, non un
    #    difetto.  ⇒ chiudere il cliente non libera il posto, e il giro dopo
    #    misurerebbe la sessione del giro prima credendola sua.  Per liberarlo
    #    davvero si termina l'utente — ⚠ ed e' un atto forte, che si fa solo
    #    sul MIO uid e solo qui.
    root("loginctl terminate-user %s 2>/dev/null; true" % UTENTE)
    for _ in range(20):
        rc, out, _ = root("pgrep -u %d -f 'gnome-shel[l]' || true" % UID_B)
        if not out.strip():
            break
        time.sleep(1)
    root("loginctl enable-linger %s 2>/dev/null; true" % UTENTE)
    if parla:
        d = posto_libero()
        return d["libero"]
    time.sleep(3)
    return True


def prepara():
    """Porta i copioni sulla macchina.  ⛔ Ognuno si verifica con l'md5: un
       file «arrivato» e un file arrivato UGUALE non sono la stessa cosa."""
    # ⛔ `10-ambiente-sessione.sh` va con `10-b89-scena.sh`: quello lo INCLUDE
    #    (l'ambiente di una sessione sta in un posto solo, 25 agosto 2026), e
    #    senza il compagno il banco morirebbe alla prima riga invece di
    #    misurare.
    for f in ("09-b71-sessione.sh", "09-b71-agente.py", "09-b72-tasto.py",
              "10-b89-agente.py", "10-ambiente-sessione.sh",
              "10-b89-scena.sh"):
        b71.porta(f)
    print("   OK  i copioni sono sulla macchina, con l'md5 verificato")


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?", default="tutto",
                   choices=["stato", "prepara", "tara-gpu", "giro",
                            "tutto", "certifica", "chiudi"])
    # ⭐ `--certifica` come interruttore, oltre che come passo: e' il nome con
    #    cui il modo e' chiesto dalla fase, e due nomi per la stessa cosa
    #    valgono meno di un nome che risponde a tutt'e due le chiamate.
    p.add_argument("--certifica", action="store_true",
                   help="innesta i cinque guasti e conta sano→guasto→risanato")
    p.add_argument("--scena", default="continuo", choices=["ferma", "desktop", "continuo"])
    p.add_argument("--secondi", type=int, default=40)
    p.add_argument("--assestamento", type=int, default=12)
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⛔ solo per la messa a punto: quei numeri NON si riferiscono")
    a = p.parse_args()
    if a.certifica:
        a.passo = "certifica"

    print("== 10-b89 · QUANTO COSTA UNA SESSIONE — porta %d, utente «%s», albero %s"
          % (b68.PORTA, UTENTE, ALBERO))
    print("   ferro: i5-13500T · 31 GB · Intel UHD 730 (`renderD128`, `i915`) — ⛔ "
          "l'integrata, non la discreta (`DECISIONI.md` §4.6-quinquies)")

    if a.passo == "stato":
        posto_libero()
        print("   monitor: %s · sessione viva: %s" % (b68.monitor(), b71.sessione_viva()))
        print("   lucchetto della GPU: %s" % (luc.stato(),))
        return 0
    if a.passo == "prepara":
        prepara()
        return 0
    if a.passo == "chiudi":
        return 0 if chiudi() else 2

    prepara()
    if not a.senza_lucchetto:
        luc.prendi(IO_SONO, secondi=2400, attesa=3600)
    try:
        if a.passo == "tara-gpu":
            t = tara_gpu()
            with open(os.path.join(FUORI, "b89-tara-gpu.json"), "w") as f:
                json.dump(t, f, ensure_ascii=False, indent=1)
            return 0 if t.get("tarato") else 2

        if a.passo == "certifica":
            esiti = certifica()
            chiudi()
            return 0 if all(x["come_deve"] for x in esiti) else 2

        # ── i giri veri ────────────────────────────────────────────────────
        d = posto_libero()
        if not d["libero"]:
            print("⛔ MI FERMO: il posto non e' libero, e misurare qui vorrebbe "
                  "dire misurare il giro di qualcun altro")
            return 2
        # ⚠ `b71.pulizia()` conta solo le porte **7xxx** (era la fase 9): la mia
        #    e' la 8010, quindi il suo verdetto «pulita» qui non vale, e non lo
        #    si usa.  Se ne prende quel che qui SERVE: gli altri banchi vivi e
        #    la disciplina su `lo`.
        pul = b71.pulizia()
        if pul["altri_banchi"]:
            print("⚠ altri banchi vivi sulla macchina: %s" % pul["altri_banchi"])
        if "netem" in pul["tc_lo"] or "tbf" in pul["tc_lo"]:
            print("⛔ MI FERMO: c'e' una disciplina su `lo` che non e' mia: %s"
                  % pul["tc_lo"])
            return 2
        # ⛔ Il metro si tara PRIMA, e prima anche della sessione: una sessione
        #    accesa fa lavorare la stessa GPU, e il carico noto della taratura
        #    non sarebbe piu' noto (`LEZIONI.md` §1.33 e §1.26).
        tar = tara_gpu()
        print("\n== la sessione: utente «%s», tela %s" % (UTENTE, TELA))
        if not b71.sessione_apri("costo", 4000, utente=UTENTE, tela=TELA):
            print("⛔ LA SESSIONE NON SI APRE: non misuro, e non dico «0 fotogrammi»")
            return 2
        time.sleep(10)
        scene = [a.scena] if a.passo == "giro" else ["ferma", "desktop", "continuo"]
        esiti = []
        try:
            for s in scene:
                d = giro(s, a.secondi, a.assestamento)
                stampa(d)
                d["tara_gpu"] = {"tarato": tar.get("tarato"),
                                 "rapporto": tar.get("rapporto")}
                d["per_dieci"] = per_dieci(d)
                stampa_dieci(d["per_dieci"], s)
                esiti.append(d)
        finally:
            scena_spegni()
        with open(os.path.join(FUORI, "b89-esiti.json"), "w") as f:
            json.dump(esiti, f, ensure_ascii=False, indent=1)
        print("\n== esiti in %s/b89-esiti.json" % FUORI)
        buoni = [x for x in esiti if x.get("esito") == "OK"]
        return 0 if len(buoni) == len(scene) else 2
    finally:
        if not a.senza_lucchetto:
            luc.molla(IO_SONO)


if __name__ == "__main__":
    sys.exit(principale())
