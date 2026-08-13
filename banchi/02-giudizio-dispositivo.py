#!/usr/bin/env python3
"""02-giudizio-dispositivo.py — CHI E' ARRIVATO ALLA PAGINA, senza credere allo
                                user agent.

    python3 banchi/02-giudizio-dispositivo.py <registro.jsonl> [--giro G]
    python3 banchi/02-giudizio-dispositivo.py --certifica      ⛔ i sette casi

===========================================================================
⛔ PERCHE' ESISTE — il difetto D17, e l'utente lo ha pagato prima di me

Il 12 agosto 2026 l'utente ha aperto la sonda **dal telefono, in Samsung
DeX**.  Il banco ha stampato:

    ⛔ NESSUNA riga viene da un dispositivo mobile.
       Il verdetto e' «il dispositivo non e' arrivato»…

⛔ **Il dispositivo era li'.**  Chrome per Android in DeX — e in «richiedi
   sito desktop» — manda:

    Mozilla/5.0 (X11; Linux x86_64) … Chrome/150.0.0.0 Safari/537.36

   che dalla sola stringa e' **indistinguibile da un desktop**.  Il vecchio
   riconoscimento cercava `Android|iPhone|iPad|Mobile` nello user agent: su
   quella riga non c'e' niente di tutto cio', e il banco ha dato il verdetto
   sbagliato con la faccia del verdetto giusto.

⚠ Gli indizi che c'erano, e che nessuno guardava:
    · l'indirizzo di provenienza era **192.168.0.24** — non il portatile
      (192.168.0.3) e non il server (192.168.0.2): un **terzo** dispositivo;
    · la versione era **150**, mentre il Chrome del portatile e' **151**.

===========================================================================
⛔ LA REGOLA, IN UNA RIGA: NESSUN SEGNALE DA SOLO BASTA

Ogni segnale qui sotto si puo' falsificare o sbagliare **da solo**.  Percio'
il riconoscimento sta su **due assi indipendenti**, e ogni riga dichiara
**quali segnali ha usato**, cosi' un domani un verdetto si puo' rileggere.

  ┌ ASSE 1 — LA PROVENIENZA (la vede il SERVER, il browser non la scrive) ┐
  │  l'indirizzo IP di chi ha aperto la connessione.                      │
  │  ⭐ E' l'unico segnale che il browser **non puo' mentire**: chi non e' │
  │     il portatile ne' il server e' un TERZO dispositivo.               │
  │  ⚠ E dice «terzo», NON dice «telefono»: un secondo portatile in casa  │
  │    e' un terzo dispositivo anche lui.                                 │
  └───────────────────────────────────────────────────────────────────────┘
  ┌ ASSE 2 — LA NATURA (la dichiara il DISPOSITIVO, e si puo' falsificare) ┐
  │  `navigator.userAgentData.getHighEntropyValues` (platform, mobile,    │
  │  model) · il nome della GPU letto da WebGL · il tocco · il tipo di    │
  │  puntatore · la memoria · i nuclei · lo schermo.                      │
  │  ⛔ La **stringa** dello user agent si raccoglie e non si crede mai   │
  │     da sola: e' il segnale che ha prodotto D17.                       │
  └───────────────────────────────────────────────────────────────────────┘

⛔ **La difesa E10 sta sull'asse 1, e ci sta apposta.**  Curare D17 guardando
   solo l'asse 2 aprirebbe il buco esatto per cui la sonda esiste: un giro
   fatto sul Chrome del portatile, con uno user agent da telefono, verrebbe
   **accettato**.  ⇒ La provenienza ha diritto di **veto**: qualunque cosa la
   pagina dichiari, se la connessione viene da questa macchina il giro e'
   **RIFIUTATO**.  Il caso `portatile-travestito` di `--certifica` misura
   proprio questo, e misura anche che il vecchio riconoscimento l'avrebbe
   promosso.

===========================================================================
⭐ E DeX E' UN CASO A SE' — il registro lo deve poter DIRE, non scegliere

Un telefono in DeX **non e' un telefono in mano** (schermo grande, mouse,
finestre) e **non e' un desktop** (il silicio e' quello del telefono, e
MediaCodec e' lo stesso).  Per la domanda di S2 — *«il decodificatore del
telefono decodifica HEVC Main10 in hardware?»* — DeX vale, perche' il
decodificatore e' quello.  Per le domande sul consumo e sul calore vale meno,
perche' il telefono e' su un dock e spesso in carica.

⇒ Le etichette dell'asse 2 sono **quattro**, non due:

    ANDROID-MANO          telefono in mano: mobile=true, tocco, puntatore
                          grossolano
    ANDROID-DEX           ⭐ Android con schermo esterno grande e puntatore
                          fine: DeX, o un qualunque dock con monitor
    ANDROID-SITO-DESKTOP  ⚠ Android che si traveste da desktop restando sullo
                          schermo del telefono («richiedi sito desktop»)
    DESKTOP               un computer
    INCERTA               ⛔ non si sa: **nessun verdetto**, e si dice perche'

⛔ La distinzione DEX / SITO-DESKTOP e' `[?]`: poggia sul puntatore e sulla
   dimensione dello schermo, non su una dichiarazione del sistema, perche'
   una dichiarazione del sistema **non esiste** nel browser.  E' scritta cosi'
   perche' il registro la possa portare senza doverla decidere.

===========================================================================
⛔ IL CASO OPPOSTO, SCRITTO PRIMA (`LEZIONI.md` §1.11)

    che aspetto ha un giro fatto DAVVERO dal portatile?

    provenienza = QUESTA-MACCHINA (127.0.0.1 o 192.168.0.3)
    natura      = DESKTOP (GPU «Mesa Intel», nessun tocco, puntatore fine)
    verdetto    = ⛔ RIFIUTATO — forma E10

E la variante cattiva, quella che la cura di D17 rende possibile:

    provenienza = QUESTA-MACCHINA          ⇐ ⭐ il veto scatta qui
    natura      = ANDROID-MANO (dichiarata)
    verdetto    = ⛔ RIFIUTATO lo stesso, e la riga dice «la pagina si e'
                  dichiarata Android da un indirizzo che e' questa macchina»
===========================================================================
"""
import json
import os
import re
import subprocess
import sys

SERVER_NIC_OS = {"192.168.0.2"}
LOOPBACK = {"127.0.0.1", "::1", "localhost"}

# ⛔ Nomi di GPU che vivono dentro un telefono.  Non e' un elenco completo e
#    non pretende di esserlo: e' un segnale fra i tanti, e vale solo insieme
#    agli altri.  Fonte: i nomi che i driver mobili espongono in WebGL.
GPU_MOBILE = re.compile(r"adreno|mali|powervr|xclipse|immortalis|apple gpu"
                        r"|videocore|tegra", re.I)
GPU_SCRIVANIA = re.compile(r"mesa|intel|radeon|amd|nvidia|geforce|llvmpipe"
                           r"|swiftshader|angle \(intel|iris|vmware", re.I)


def indirizzi_locali():
    """Gli indirizzi di QUESTA macchina, chiesti al nucleo.

    ⛔ Non si scrivono a mano: il portatile prende l'indirizzo dal DHCP e il
       giorno che diventasse .4 il veto E10 smetterebbe di scattare — in
       silenzio, che e' il modo peggiore.
    """
    fuori = set(LOOPBACK)
    sovrascrittura = os.environ.get("NOSTRI_INDIRIZZI", "").strip()
    if sovrascrittura:
        fuori |= set(sovrascrittura.split(","))
        return fuori
    try:
        p = subprocess.run(["ip", "-o", "addr", "show"],
                           capture_output=True, text=True, check=True)
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write("    ⚠ non ho potuto chiedere gli indirizzi al "
                         "nucleo (%s): il veto E10 poggia solo su "
                         "127.0.0.1\n" % e)
        return fuori
    for riga in p.stdout.splitlines():
        campi = riga.split()
        for i, c in enumerate(campi):
            if c in ("inet", "inet6") and i + 1 < len(campi):
                fuori.add(campi[i + 1].split("/")[0])
    return fuori


def provenienza(ip, locali):
    """ASSE 1 — e questo asse il browser non lo scrive."""
    if ip is None or ip == "":
        return "SCONOSCIUTA", ("l'indirizzo non e' nel registro: il "
                               "raccoglitore non lo scriveva (difetto D16/D17)")
    if ip in LOOPBACK:
        return "LOOPBACK", "%s — la connessione nasce su questa macchina" % ip
    if ip in locali:
        return "QUESTA-MACCHINA", "%s — e' un indirizzo di questo portatile" % ip
    if ip in SERVER_NIC_OS:
        return "SERVER-NIC-OS", "%s — e' il server, non un dispositivo" % ip
    return "TERZO-DISPOSITIVO", ("%s — non e' questo portatile e non e' il "
                                 "server" % ip)


def natura(impronta):
    """ASSE 2 — che cosa dichiara di essere, e con quanti segnali d'accordo.

    Torna (etichetta, segnali_usati, note).  ⛔ `segnali_usati` finisce nella
    riga del registro: un verdetto che non dice su che cosa poggia non si puo'
    rileggere fra un mese.
    """
    usati = []
    note = []
    if not impronta:
        return "INCERTA", usati, ["la pagina non ha spedito nessuna impronta: "
                                  "o e' una versione vecchia della pagina, o "
                                  "non e' un browser (curl)"]

    alta = impronta.get("ua_dati_alta_entropia") or {}
    dati = impronta.get("ua_dati") or {}
    gpu = (impronta.get("gpu") or {}).get("resa") or ""
    ua = impronta.get("ua_stringa") or ""
    schermo = impronta.get("schermo") or {}

    # — i segnali che dicono ANDROID —
    android = []
    if str(alta.get("platform", "")).lower() == "android":
        android.append("userAgentData.platform=Android")
    if alta.get("model"):
        android.append("userAgentData.model=%s" % alta["model"])
    if GPU_MOBILE.search(gpu):
        android.append("GPU WebGL «%s»" % gpu)
    debole_ua = bool(re.search(r"android|iphone|ipad", ua, re.I))
    if debole_ua:
        # ⚠ conta, ma NON puo' essere l'unico: e' il segnale che ha prodotto D17
        android.append("⚠ stringa UA (debole)")

    scrivania = []
    if GPU_SCRIVANIA.search(gpu):
        scrivania.append("GPU WebGL «%s»" % gpu)
    if str(alta.get("platform", "")).lower() in ("linux", "windows", "macos",
                                                 "chrome os", "chromeos"):
        scrivania.append("userAgentData.platform=%s" % alta["platform"])

    forti_android = [s for s in android if not s.startswith("⚠")]

    # ⛔ LA REGOLA D'ACCOPPIAMENTO: «Android» vuole almeno DUE segnali
    #    d'accordo, di cui almeno uno che NON sia la stringa dello user agent.
    if len(android) >= 2 and forti_android:
        usati += android
        mobile = dati.get("mobile")
        tocco = (impronta.get("tocco_massimo") or 0) > 0
        grossolano = bool(impronta.get("puntatore_grossolano"))
        fine = bool(impronta.get("puntatore_fine"))
        largo = (schermo.get("l") or 0) >= 1024
        dpr = schermo.get("dpr") or 0
        usati.append("mobile=%s · tocco=%s · puntatore=%s · schermo=%sx%s@%s"
                     % (mobile, impronta.get("tocco_massimo"),
                        "grossolano" if grossolano else ("fine" if fine else "?"),
                        schermo.get("l"), schermo.get("a"), dpr))
        if mobile is True or (grossolano and tocco and not largo):
            return "ANDROID-MANO", usati, note
        # non e' «in mano»: o e' un dock con monitor, o e' «sito desktop»
        if fine and largo and dpr <= 1.5:
            note.append("⭐ schermo esterno grande, puntatore fine, dpr %s: "
                        "e' un dock — DeX o equivalente.  ⛔ La distinzione "
                        "DEX/SITO-DESKTOP e' [?]: nel browser non esiste una "
                        "dichiarazione del sistema, e questa poggia su "
                        "puntatore e schermo" % dpr)
            return "ANDROID-DEX", usati, note
        note.append("⚠ Android che non si dichiara mobile ma resta su uno "
                    "schermo da telefono: «richiedi sito desktop»")
        return "ANDROID-SITO-DESKTOP", usati, note

    if len(android) == 1 and debole_ua and not forti_android:
        usati += android
        note.append("⛔ SOLO la stringa dello user agent dice Android, e la "
                    "stringa e' precisamente il segnale che ha prodotto D17. "
                    "Un segnale solo non basta.")
        return "INCERTA", usati, note

    if scrivania:
        usati += scrivania
        usati.append("tocco=%s · nuclei=%s · memoria=%s GB"
                     % (impronta.get("tocco_massimo"), impronta.get("nuclei"),
                        impronta.get("memoria_gb")))
        return "DESKTOP", usati, note

    note.append("nessun segnale forte in nessuna delle due direzioni")
    return "INCERTA", usati, note


def vecchio_riconoscimento(ua):
    """⛔ Il riconoscimento di PRIMA — tenuto qui apposta.

    Non serve piu' a decidere: serve a **misurare la differenza**.  Un rilievo
    che dice «adesso e' meglio» senza il vecchio accanto non e' una misura.
    """
    return bool(re.search(r"Android|iPhone|iPad|Mobile", ua or ""))


def giudica(riga, locali):
    ip = riga.get("ip")
    dati = riga.get("dati") or {}
    impronta = dati.get("impronta") or riga.get("impronta")
    prov, perche_prov = provenienza(ip, locali)
    nat, segnali, note = natura(impronta)

    # ⛔ IL VETO: la provenienza vince sempre.  E' la difesa E10.
    if prov in ("QUESTA-MACCHINA", "LOOPBACK"):
        verdetto = "RIFIUTATO"
        motivo = ("forma E10 — il giro viene da QUESTA macchina.  "
                  "Un numero misurato qui certifica lo STRUMENTO e non "
                  "misura S2")
        if nat.startswith("ANDROID"):
            motivo += (".  ⛔ E la pagina si dichiarava %s: la dichiarazione "
                       "NON scavalca l'indirizzo" % nat)
    elif prov == "SERVER-NIC-OS":
        verdetto = "RIFIUTATO"
        motivo = "e' il server, non un dispositivo dell'utente"
    elif prov == "SCONOSCIUTA":
        verdetto = "SOSPESO"
        motivo = ("senza l'indirizzo di provenienza la difesa E10 non esiste: "
                  "nessun verdetto")
    elif nat in ("ANDROID-MANO", "ANDROID-DEX", "ANDROID-SITO-DESKTOP"):
        verdetto = "ACCETTATO"
        motivo = "terzo dispositivo, e la sua natura e' %s" % nat
    elif nat == "DESKTOP":
        verdetto = "RIFIUTATO"
        motivo = ("e' un terzo dispositivo ma e' un COMPUTER: «non e' questo "
                  "portatile» non vuol dire «e' un telefono»")
    else:
        verdetto = "SOSPESO"
        motivo = ("un terzo dispositivo e' arrivato, ma non ha dichiarato la "
                  "sua natura: potrebbe essere un altro portatile.  ⛔ Nessun "
                  "verdetto su S2")

    ua = (impronta or {}).get("ua_stringa") or riga.get("ua") or ""
    return {
        "verdetto": verdetto,
        "motivo": motivo,
        "provenienza": prov,
        "provenienza_perche": perche_prov,
        "natura": nat,
        "segnali_usati": segnali,
        "note": note,
        "ua_stringa": ua[:160],
        "vecchio_riconoscimento_avrebbe_detto":
            "ACCETTATO" if vecchio_riconoscimento(ua) else "RIFIUTATO",
    }


# ===========================================================================
# ⛔ LA CERTIFICAZIONE — sette casi, l'atteso scritto PRIMA
#
# ⚠ E si dichiara che cosa e' MISURATO e che cosa e' COSTRUITO:
#
#   · `portatile-onesto` e `portatile-travestito` sono **misurati** su questa
#     macchina da `02-giudizio-telefono.sh certifica`, con Chrome e Firefox
#     veri.  Qui ci sono nella forma della riga, per far girare la decisione
#     senza aprire un browser.
#   · `dex-reale-12ago` e' una riga **vera**, presa dal registro del 12 agosto
#     2026: l'indirizzo 192.168.0.24 e lo user agent sono quelli che l'utente
#     ha prodotto col telefono in DeX.
#   · `dex` e `telefono-in-mano` hanno l'asse 1 **misurato** (lo stesso
#     192.168.0.24) e l'asse 2 **dichiarato**: i valori che Chrome per Android
#     espone in DeX sono `[?]` finche' il secondo giro non li raccoglie.  ⛔ E
#     `[?]` resta `[?]`: quel che questi due casi certificano e' **la
#     decisione**, non il dispositivo.
# ===========================================================================
CASI = [
    ("portatile-onesto", "RIFIUTATO", "DESKTOP",
     {"ip": "127.0.0.1", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/151.0.7922.108 Safari/537.36",
         "ua_dati": {"mobile": False, "platform": "Linux"},
         "ua_dati_alta_entropia": {"platform": "Linux", "mobile": False,
                                   "model": ""},
         "gpu": {"resa": "Mesa Intel(R) UHD Graphics (JSL)"},
         "tocco_massimo": 0, "puntatore_fine": True,
         "puntatore_grossolano": False, "nuclei": 8, "memoria_gb": 8,
         "schermo": {"l": 1920, "a": 1080, "dpr": 1}}}}),

    ("portatile-travestito", "RIFIUTATO", "ANDROID-MANO",
     # ⛔⭐ IL CASO CHE LA CURA DI D17 RENDE POSSIBILE: il Chrome del portatile
     #     con uno user agent da telefono.  Il vecchio riconoscimento lo
     #     ACCETTA (ed e' misurato sotto), il nuovo lo RIFIUTA per indirizzo.
     {"ip": "192.168.0.3", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Linux; Android 14; SM-S918B) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/151.0.0.0 Mobile Safari/537.36",
         "ua_dati": {"mobile": True, "platform": "Android"},
         "ua_dati_alta_entropia": {"platform": "Android", "mobile": True,
                                   "model": "SM-S918B"},
         "gpu": {"resa": "Mesa Intel(R) UHD Graphics (JSL)"},
         "tocco_massimo": 5, "puntatore_grossolano": True,
         "puntatore_fine": False,
         "schermo": {"l": 412, "a": 915, "dpr": 2.6}}}}),

    ("dex", "ACCETTATO", "ANDROID-DEX",
     {"ip": "192.168.0.24", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
         "ua_dati": {"mobile": False, "platform": "Android"},
         "ua_dati_alta_entropia": {"platform": "Android", "mobile": False,
                                   "model": "SM-S918B"},
         "gpu": {"resa": "ANGLE (Qualcomm, Adreno (TM) 740, OpenGL ES 3.2)"},
         "tocco_massimo": 5, "puntatore_grossolano": False,
         "puntatore_fine": True, "nuclei": 8, "memoria_gb": 8,
         "schermo": {"l": 1920, "a": 1080, "dpr": 1}}}}),

    ("telefono-in-mano", "ACCETTATO", "ANDROID-MANO",
     {"ip": "192.168.0.24", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Linux; Android 14; SM-S918B) …Mobile…",
         "ua_dati": {"mobile": True, "platform": "Android"},
         "ua_dati_alta_entropia": {"platform": "Android", "mobile": True,
                                   "model": "SM-S918B"},
         "gpu": {"resa": "ANGLE (ARM, Mali-G78, OpenGL ES 3.2)"},
         "tocco_massimo": 5, "puntatore_grossolano": True,
         "puntatore_fine": False,
         "schermo": {"l": 412, "a": 915, "dpr": 2.6}}}}),

    ("terzo-portatile", "RIFIUTATO", "DESKTOP",
     # ⭐ Il buco che si apre curando D17: «non e' questa macchina» non vuol
     #    dire «e' un telefono».  In casa ci sono altri computer.
     {"ip": "192.168.0.10", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) …Chrome/151…",
         "ua_dati": {"mobile": False, "platform": "Windows"},
         "ua_dati_alta_entropia": {"platform": "Windows", "mobile": False},
         "gpu": {"resa": "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11)"},
         "tocco_massimo": 0, "puntatore_fine": True,
         "schermo": {"l": 2560, "a": 1440, "dpr": 1}}}}),

    ("dex-reale-12ago", "SOSPESO", "INCERTA",
     # ⚠ La riga VERA di stasera: c'e' l'indirizzo, non c'e' l'impronta —
     #    perche' quella versione della pagina non la spediva.  ⛔ L'esito
     #    giusto per questa riga NON e' «accettato»: e' «sospeso», e il
     #    secondo giro raccogliera' l'asse 2.
     {"ip": "192.168.0.24", "ua":
         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like "
         "Gecko) Chrome/150.0.0.0 Safari/537.36", "dati": {}}),

    ("curl-del-controllo", "RIFIUTATO", "INCERTA",
     {"ip": "127.0.0.1", "ua": "curl/8.14.1", "dati": {}}),
]


def certifica():
    locali = indirizzi_locali() | {"192.168.0.3"}
    print("\n\033[1m== LA CERTIFICAZIONE DEL RICONOSCIMENTO — atteso scritto "
          "PRIMA\033[0m")
    print("    --  indirizzi di questa macchina: %s"
          % ", ".join(sorted(locali)))
    esito = 0
    for nome, atteso_v, atteso_n, riga in CASI:
        g = giudica(riga, locali)
        bene = (g["verdetto"] == atteso_v and g["natura"] == atteso_n)
        marca = "\033[1;32mOK\033[0m" if bene else "\033[1;31mNO\033[0m"
        print("\n    %s  %-22s atteso %s/%s → %s/%s"
              % (marca, nome, atteso_v, atteso_n, g["verdetto"], g["natura"]))
        print("        provenienza: %s (%s)"
              % (g["provenienza"], g["provenienza_perche"]))
        for s in g["segnali_usati"]:
            print("        segnale: %s" % s)
        for n in g["note"]:
            print("        %s" % n)
        print("        vecchio riconoscimento (per user agent): %s"
              % g["vecchio_riconoscimento_avrebbe_detto"])
        if not bene:
            esito = 3
    print("\n    --  ⭐ e la differenza MISURATA, non affermata:")
    for nome, _a, _b, riga in CASI:
        g = giudica(riga, locali)
        if g["vecchio_riconoscimento_avrebbe_detto"] != g["verdetto"]:
            print("        %-22s vecchio: %-10s nuovo: %s"
                  % (nome, g["vecchio_riconoscimento_avrebbe_detto"],
                     g["verdetto"]))
    if esito:
        print("\n    \033[1;31mNO\033[0m  ⛔ il riconoscimento NON fa quel che "
              "ha dichiarato: nessun verdetto si da'")
    else:
        print("\n    \033[1;32mOK\033[0m  sette casi su sette, e i due che "
              "contano sono: DeX ACCETTATO, portatile RIFIUTATO")
    return esito


def principale():
    arg = sys.argv[1:]
    if arg and arg[0] == "--certifica":
        return certifica()
    if not arg:
        print(__doc__)
        return 2
    percorso = arg[0]
    giro = None
    if "--giro" in arg:
        giro = arg[arg.index("--giro") + 1]
    if not os.path.isfile(percorso):
        sys.stderr.write("    \033[1;31mNO\033[0m  il registro %s non c'e'\n"
                         % percorso)
        return 2
    locali = indirizzi_locali()
    righe = []
    for r in open(percorso, encoding="utf-8"):
        r = r.strip()
        if not r:
            continue
        try:
            d = json.loads(r)
        except Exception:                                     # noqa: BLE001
            continue
        if giro and (d.get("dati") or {}).get("giro") != giro:
            continue
        righe.append(d)
    if not righe:
        sys.stderr.write("    \033[1;31mNO\033[0m  nessuna riga%s\n"
                         % (" per il giro %s" % giro if giro else ""))
        return 2

    # ⛔ Si raggruppa anche per USER AGENT e per «c'e' l'impronta o no», e non
    #    e' pignoleria: senza, le righe di lettura (GET, che l'impronta non ce
    #    l'hanno) finiscono nello stesso mucchio degli esiti, e un dispositivo
    #    **travestito** sparisce dentro il mucchio di un altro.  `[M]` 12 ago
    #    2026: e' successo al primo giro di `certifica`.
    conteggio = {}
    for d in righe:
        if d.get("tipo") == "prova":
            continue                       # il gettone del controllo, non un giro
        g = giudica(d, locali)
        con_impronta = bool((d.get("dati") or {}).get("impronta"))
        chiave = (g["verdetto"], g["natura"], d.get("ip"),
                  (d.get("ua") or "")[:70], con_impronta)
        conteggio.setdefault(chiave, {"n": 0, "g": g,
                                      "impronta": con_impronta})
        conteggio[chiave]["n"] += 1

    if not conteggio:
        print("    --  solo gettoni di controllo nel registro: nessun "
              "dispositivo e' arrivato")
        return 3

    accettati = 0
    discordi = 0
    # ⛔ Le chiavi possono portare `None` — un campo che il browser non ha
    #    mandato, o una riga vecchia scritta da un raccoglitore che non lo
    #    scriveva ancora.  `sorted()` su una tupla mista `str`/`None` **crolla**,
    #    e lo strumento muore prima di stampare il verdetto: `[M]` 13 agosto
    #    2026, sul primo giro vero dal telefono dell'utente.
    #    ⚠ E crollava DOPO aver gia' letto tutto: la misura c'era, il lettore no.
    #    Si ordina su una chiave che tratta l'assente come stringa vuota — e
    #    l'assente resta `None` nei dati, perche' «non l'ha mandato» e «l'ha
    #    mandato vuoto» sono due cose diverse (E8).
    def _chiave(coppia):
        return tuple("" if c is None else str(c) for c in coppia[0])

    for (verdetto, nat, ip, _ua, con_impronta), v in sorted(conteggio.items(),
                                                            key=_chiave):
        g = v["g"]
        colore = {"ACCETTATO": "\033[1;32m", "RIFIUTATO": "\033[1;31m",
                  "SOSPESO": "\033[1;33m"}[verdetto]
        print("\n    %s%s\033[0m  %d righe · %s · provenienza %s%s"
              % (colore, verdetto, v["n"], nat, ip,
                 "" if con_impronta else "  (righe SENZA impronta: letture o "
                                         "pixel, non esiti)"))
        print("        %s" % g["motivo"])
        print("        provenienza: %s" % g["provenienza_perche"])
        for s in g["segnali_usati"]:
            print("        segnale: %s" % s)
        for n in g["note"]:
            print("        %s" % n)
        print("        user agent (raccolto, mai creduto da solo): %s"
              % g["ua_stringa"])
        print("        il vecchio riconoscimento avrebbe detto: %s"
              % g["vecchio_riconoscimento_avrebbe_detto"])
        if g["vecchio_riconoscimento_avrebbe_detto"] != verdetto:
            discordi += v["n"]
            print("        ⭐ QUI I DUE RICONOSCIMENTI NON SONO D'ACCORDO — e"
                  " la differenza e' misurata, non affermata")
        if verdetto == "ACCETTATO":
            accettati += v["n"]
    if discordi:
        print("\n    --  ⭐ %d righe su cui il riconoscimento per user agent "
              "dava un'altra risposta" % discordi)
    return 0 if accettati else 3


if __name__ == "__main__":
    sys.exit(principale())
