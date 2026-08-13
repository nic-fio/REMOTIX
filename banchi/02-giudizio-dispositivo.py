#!/usr/bin/env python3
"""02-giudizio-dispositivo.py — CHI E' ARRIVATO ALLA PAGINA, senza credere allo
                                user agent.

    python3 banchi/02-giudizio-dispositivo.py <registro.jsonl> [--giro G]
                                             [--dichiarazioni <file.json>]
    python3 banchi/02-giudizio-dispositivo.py --certifica      ⛔ i dodici casi

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

⇒ Le etichette dell'asse 2 sono **cinque**, non due:

    ANDROID-MANO          telefono in mano: mobile=true, tocco, puntatore
                          grossolano, schermo da telefono
    ANDROID-DOCK          ⭐ silicio da telefono su uno schermo ESTERNO GRANDE.
                          `[M]` E' quel che si MISURA: un dock c'e'.
    ANDROID-DEX           ⭐ `[D]` lo stesso, ma con la parola «DeX» — e quella
                          parola **la dice l'operatore**, non il browser
    ANDROID-SITO-DESKTOP  ⚠ Android che si traveste da desktop restando sullo
                          schermo del telefono («richiedi sito desktop»)
    DESKTOP               un computer
    INCERTA               ⛔ non si sa: **nessun verdetto**, e si dice perche'

⛔ La distinzione DOCK / DEX **non e' misurabile e non si indovina**: nel
   browser una dichiarazione del sistema non esiste.  ⇒ `ANDROID-DOCK` e' il
   misurato, `ANDROID-DEX` e' il misurato **piu' una dichiarazione**, e la riga
   di registro dice quale dei due pezzi e' quale.

===========================================================================
⛔⛔ IL SECONDO RIFIUTO — D18 e D19, e l'utente ha ripagato il conto
    (13 agosto 2026, mattina)

Curato D17, l'utente ha riaperto la pagina **dal telefono in DeX**.  Il banco
ha detto di nuovo di no:

    RIFIUTATO · DESKTOP · provenienza 192.168.0.25
       segnale: userAgentData.platform = Linux
       segnale: tocco=5 · nuclei=8 · memoria=8 GB

⛔ E l'impronta, quella vera, portava questo — misurato, e' nel registro:

    gpu.resa            = «ANGLE (Qualcomm, Adreno (TM) 740, OpenGL ES 3.2)»
    piattaforma_legacy  = «Linux armv81»
    ua_dati_alta_entropia.architecture = «x86»       ⇐ ⭐ contraddice armv81
    ua_dati_alta_entropia.formFactors  = ["Desktop"]
    tocco_massimo=5 · pointer:coarse · hover:none
    schermo 2560x1080 @ dpr 1.2

**D18 — la regola «almeno DUE segnali d'accordo» CONTAVA i segnali invece di
        pesarli, e in caso di parita' la scrivania vinceva in silenzio.**
  L'Adreno c'era, ed e' il segnale piu' forte dell'intera impronta: il nome del
  silicio, letto da WebGL, che il travestimento «richiedi sito desktop» non
  tocca.  Ma era **UNO**, la soglia voleva **DUE**, e il controllo cadeva sul
  ramo `if scrivania:` — che stampava `platform=Linux` e **buttava via
  l'Adreno senza nominarlo**.  ⛔ Un segnale letto e non stampato e' un
  silenzio scambiato per zero: forma **E8**, dentro il codice scritto per
  curare E8.
  ⛔ Ed e' la forma esatta di `LEZIONI.md` §1.14: un criterio «almeno N di M»
     si scrive **solo** se le M sono intercambiabili.  Il nome della GPU e la
     stringa dello user agent **non lo sono** — uno e' silicio, l'altra e' una
     frase che il browser compone.  ⇒ Il criterio giusto non e' «quanti», e'
     **«quale»**, e il banco deve dirlo.
  ⚠ E `piattaforma_legacy` — «Linux armv81», cioe' un processore ARM — la
    pagina la raccoglieva **e nessuno la leggeva**: un secondo segnale di
    silicio buttato prima ancora di essere contato.

**D19 — l'etichetta ANDROID-DEX poggiava su `puntatore_fine`, che in DeX e'
        FALSO.**
  ⛔ Anche col conteggio curato, il ramo `if fine and largo and dpr <= 1.5`
     **non sarebbe scattato**: `[M]` il telefono in DeX su un monitor
     2560x1080 dichiara `pointer: coarse`, `hover: none`, `maxTouchPoints=5`
     — **identico a un telefono in mano**, perche' Chrome descrive il puntatore
     primario del DISPOSITIVO, non quello del dock.
  ⇒ Il puntatore **non distingue DeX**, e la riga che ci poggiava sopra non
    poteva prendere il caso per cui era stata scritta.  Lo **schermo** invece
    distingue: 2560x1080 non e' lo schermo di un telefono, e «richiedi sito
    desktop» lascia `screen.width` a quello del telefono (~412).

⇒ LA CURA, e non e' «aggiungere il tocco all'elenco»:
  1. i segnali si dividono per **peso** — SILICIO (che il browser non compone),
     DICHIARAZIONE (che compone), FORMA (com'e' adesso il dispositivo) — e la
     natura la decide il **silicio**, non il numero;
  2. ⛔ **si stampano TUTTI**, anche e soprattutto quelli in contraddizione:
     «l'Adreno dice telefono, formFactors dice Desktop» e' un'informazione, e
     un verdetto che ne butta meta' e' E8;
  3. ⭐ dove il browser **non puo'** rispondere — «e' DeX?» — risponde
     l'**operatore**, con `serve --dispositivo android-dex`, e la riga di
     registro dice `[D] dichiarato dall'operatore, NON misurato`;
  4. ⛔ e la dichiarazione **non promuove niente**: non scavalca la provenienza
     (veto E10) e non fabbrica silicio da telefono dove il silicio dice Mesa
     Intel.  Puo' solo **dare un nome** a un dock che e' gia' misurato.

⭐ E la proprieta' che conta piu' di tutte: **l'accettazione non dipende dalla
   dichiarazione**.  Un telefono in DeX senza dichiarazione e' `ANDROID-DOCK` e
   viene **ACCETTATO** lo stesso.  Se dimenticare una bandierina potesse far
   rifiutare il dispositivo, avremmo costruito il terzo rifiuto.

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

# ⭐ Il secondo segnale di SILICIO, e la pagina lo raccoglieva gia': il
#    `navigator.platform` d'anteguerra.  In DeX vale «Linux armv81» — ARM — e
#    la corsia moderna (`userAgentData.architecture`) dice «x86».  ⛔ Le due
#    NON possono essere vere insieme, e la contraddizione e' essa stessa il
#    segnale: la dichiarazione e' stata riscritta, il silicio no.
CPU_ARM = re.compile(r"\barm|aarch64", re.I)
CPU_X86 = re.compile(r"x86|i686|win32|win64|macintel|amd64", re.I)

# ⛔ Uno schermo da telefono e uno schermo da monitor, in pixel CSS.  `[M]` 13
#    ago 2026: telefono in mano 412, lo stesso telefono in DeX 2560.  La banda
#    in mezzo non si promuove: si dichiara incerta (LEZIONI.md §1.9).
SCHERMO_DOCK = 1280
SCHERMO_TELEFONO = 1024

# ⭐ QUEL CHE L'OPERATORE PUO' DICHIARARE — e nient'altro.
#    ⛔ Non e' un elenco di verdetti: e' un elenco di NOMI che si possono dare
#       a una forma gia' misurata.  Vedi `applica_dichiarazione`.
DISPOSITIVI_DICHIARABILI = {
    "android-dex": ("ANDROID-DEX",
                    "un telefono Android su un dock con monitor esterno "
                    "(Samsung DeX o equivalente)"),
    "android-mano": ("ANDROID-MANO", "un telefono Android tenuto in mano"),
    "android-sito-desktop": ("ANDROID-SITO-DESKTOP",
                             "un telefono Android con «richiedi sito desktop»"),
    "computer": ("DESKTOP", "un computer — dichiarabile per i giri di "
                            "controllo, e non promuove nulla"),
}


def leggi_dichiarazioni(percorso):
    """⭐ LE DICHIARAZIONI DELL'OPERATORE — la forma di `--sonde-del-banco`.

    `01-p5-lancia.sh` ha gia' in casa questo meccanismo (`LEZIONI.md` §1.14):
    dove il banco **non puo' sapere**, chi conduce il giro **dichiara**, e il
    dichiarato viaggia accanto al misurato invece di travestirsi da misura.

    Il file e' `{"giri": {"<giro>": {"dispositivo": "android-dex", ...}}}`.
    ⛔ Assente non e' un errore: senza dichiarazione si giudica sul misurato, e
       il misurato da solo **accetta lo stesso** un telefono in DeX.
    """
    if not percorso or not os.path.isfile(percorso):
        return {}
    try:
        with open(percorso, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write("    ⚠ la dichiarazione %s non si legge (%s): si "
                         "giudica sul solo misurato, E LO DICO\n"
                         % (percorso, e))
        return {}
    return d.get("giri") or {}


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


def segnali(impronta):
    """⛔ TUTTI i segnali dell'impronta, ciascuno col suo PESO e il suo VERSO.

    ⭐ E **nessuno si butta**.  D18 e' nato qui: l'Adreno era stato letto, non
       superava una soglia di conteggio, e spariva dalla riga senza essere
       nominato.  Adesso ogni segnale letto **viene stampato**, anche quando
       perde — soprattutto quando perde, perche' e' li' che sta l'informazione.

    I pesi, e non sono tre gradi della stessa cosa:

      SILICIO        quel che il browser **non compone**: il nome del
                     disegnatore letto da WebGL, il processore.  Sopravvive a
                     «richiedi sito desktop» e a DeX.
      DICHIARAZIONE  quel che il browser **compone**: `userAgentData`, la
                     stringa dello user agent.  In DeX **e' falsa per
                     costruzione**, e non e' un difetto di Chrome: e' quel che
                     l'utente ha chiesto quando ha chiesto un sito desktop.
      FORMA          com'e' il dispositivo **adesso**: tocco, puntatore,
                     schermo.  ⛔ Non dice CHE COSA E', dice COM'E' MESSO.

    Torna la lista di dizionari {peso, verso, testo}.
    """
    fuori = []

    def s(peso, verso, testo):
        fuori.append({"peso": peso, "verso": verso, "testo": testo})

    alta = impronta.get("ua_dati_alta_entropia") or {}
    dati = impronta.get("ua_dati") or {}
    ogpu = impronta.get("gpu") or {}
    gpu = ogpu.get("resa") or ""
    ua = impronta.get("ua_stringa") or ""
    legacy = impronta.get("piattaforma_legacy") or ""
    schermo = impronta.get("schermo") or {}

    # ── SILICIO ──────────────────────────────────────────────────────────
    if gpu and GPU_MOBILE.search(gpu):
        s("SILICIO", "android", "GPU WebGL «%s» — e' silicio da telefono" % gpu)
    if gpu and GPU_SCRIVANIA.search(gpu):
        s("SILICIO", "scrivania", "GPU WebGL «%s» — e' silicio da computer" % gpu)
    if gpu and not GPU_MOBILE.search(gpu) and not GPU_SCRIVANIA.search(gpu):
        s("SILICIO", "—", "⚠ GPU WebGL «%s»: non e' in nessuno dei due "
                          "elenchi.  L'elenco e' incompleto per costruzione, e "
                          "questo e' il modo in cui lo dice" % gpu)
    if ogpu.get("mascherato"):
        s("SILICIO", "—", "⛔ la GPU e' MASCHERATA: il segnale piu' forte "
                          "dell'impronta non c'e' su questo giro")
    if not gpu:
        s("SILICIO", "—", "⛔ nessun nome di GPU nell'impronta (niente WebGL, "
                          "o pagina vecchia)")
    if legacy and CPU_ARM.search(legacy):
        s("SILICIO", "android",
          "navigator.platform=«%s» — processore ARM, non un PC x86.  "
          "⚠ dice ARM, non «Android»: ci sono computer ARM" % legacy)
    if legacy and CPU_X86.search(legacy):
        s("SILICIO", "scrivania", "navigator.platform=«%s» — x86" % legacy)

    # ── DICHIARAZIONE ────────────────────────────────────────────────────
    piatta = str(alta.get("platform", "") or dati.get("platform", "") or "")
    if piatta.lower() == "android":
        s("DICHIARAZIONE", "android", "userAgentData.platform=Android")
    elif piatta.lower() in ("linux", "windows", "macos", "chrome os", "chromeos"):
        s("DICHIARAZIONE", "scrivania", "userAgentData.platform=%s" % piatta)
    if alta.get("model"):
        s("DICHIARAZIONE", "android", "userAgentData.model=%s" % alta["model"])
    if dati.get("mobile") is True:
        s("DICHIARAZIONE", "android", "userAgentData.mobile=true")
    elif dati.get("mobile") is False:
        s("DICHIARAZIONE", "scrivania", "userAgentData.mobile=false")
    ff = alta.get("formFactors") or alta.get("formFactor")
    if ff:
        verso = "scrivania" if "desktop" in str(ff).lower() else "—"
        s("DICHIARAZIONE", verso, "userAgentData.formFactors=%s" % (ff,))
    if alta.get("architecture"):
        verso = ("scrivania" if CPU_X86.search(str(alta["architecture"]))
                 else ("android" if CPU_ARM.search(str(alta["architecture"]))
                       else "—"))
        s("DICHIARAZIONE", verso,
          "userAgentData.architecture=%s" % alta["architecture"])
    if re.search(r"android|iphone|ipad", ua, re.I):
        s("DICHIARAZIONE", "android",
          "⚠ stringa UA dice Android/iOS — ed e' il segnale che ha prodotto D17")
    elif re.search(r"x11|windows nt|macintosh", ua, re.I):
        s("DICHIARAZIONE", "scrivania",
          "⚠ stringa UA dice desktop — ed e' il segnale che ha prodotto D17")

    # ── FORMA ────────────────────────────────────────────────────────────
    s("FORMA", "—", "tocco=%s · puntatore=%s · sorvolo=%s"
      % (impronta.get("tocco_massimo"),
         "grossolano" if impronta.get("puntatore_grossolano")
         else ("fine" if impronta.get("puntatore_fine") else "?"),
         "no" if impronta.get("niente_sorvolo") else "si"))
    s("FORMA", "—", "schermo=%sx%s@%s · finestra=%sx%s · nuclei=%s · memoria=%s GB"
      % (schermo.get("l"), schermo.get("a"), schermo.get("dpr"),
         (impronta.get("finestra") or {}).get("l"),
         (impronta.get("finestra") or {}).get("a"),
         impronta.get("nuclei"), impronta.get("memoria_gb")))

    # ── ⭐ LE CONTRADDIZIONI, che sono esse stesse un segnale ────────────
    if legacy and alta.get("architecture"):
        arm_vero = bool(CPU_ARM.search(legacy))
        x86_detto = bool(CPU_X86.search(str(alta["architecture"])))
        if arm_vero and x86_detto:
            s("SILICIO", "android",
              "⭐ CONTRADDIZIONE: navigator.platform dice «%s» (ARM) e "
              "userAgentData.architecture dice «%s» (x86).  ⛔ Non possono "
              "essere vere insieme: la DICHIARAZIONE e' stata riscritta, il "
              "silicio no.  E' la firma di «richiedi sito desktop» / DeX"
              % (legacy, alta["architecture"]))
    return fuori


def natura(impronta):
    """ASSE 2 — che cosa E', deciso dal SILICIO e non da un conteggio.

    Torna (etichetta, segnali_usati, note).

    ⛔ LA REGOLA CHE HA SOSTITUITO «almeno due segnali» (D18, `LEZIONI.md`
       §1.14): i segnali non sono intercambiabili, quindi non si contano.
       **Decide il silicio.**  La dichiarazione non decide da sola — mai, in
       nessun verso — e la forma non decide **che cosa e'**: decide solo
       **com'e' messo**, cioe' l'etichetta fra MANO, DOCK e SITO-DESKTOP.
    """
    note = []
    if not impronta:
        return "INCERTA", [], ["la pagina non ha spedito nessuna impronta: "
                               "o e' una versione vecchia della pagina, o "
                               "non e' un browser (curl)"]

    sg = segnali(impronta)
    usati = ["[%s] %s" % (x["peso"], x["testo"]) for x in sg]

    sil_and = [x for x in sg if x["peso"] == "SILICIO" and x["verso"] == "android"]
    sil_scr = [x for x in sg if x["peso"] == "SILICIO" and x["verso"] == "scrivania"]
    dic_and = [x for x in sg if x["peso"] == "DICHIARAZIONE" and x["verso"] == "android"]
    dic_scr = [x for x in sg if x["peso"] == "DICHIARAZIONE" and x["verso"] == "scrivania"]

    # ⭐ E la contraddizione si DICE, sempre, prima di qualunque verdetto.
    if sil_and and dic_scr:
        note.append("⭐ I DUE VERSI SI CONTRADDICONO, e si stampano tutti e "
                    "due: il SILICIO dice telefono (%d segnali), la "
                    "DICHIARAZIONE dice computer (%d segnali).  ⛔ Vince il "
                    "silicio: e' quel che il browser non compone.  In DeX e in "
                    "«richiedi sito desktop» questa contraddizione e' la norma, "
                    "non l'anomalia."
                    % (len(sil_and), len(dic_scr)))
    if sil_scr and dic_and:
        note.append("⭐ I DUE VERSI SI CONTRADDICONO: il SILICIO dice computer "
                    "(%d segnali), la DICHIARAZIONE dice telefono (%d).  ⛔ "
                    "Vince il silicio — ed e' esattamente il travestimento che "
                    "curare D17 rendeva possibile."
                    % (len(sil_scr), len(dic_and)))

    if sil_and and sil_scr:
        note.append("⛔ IL SILICIO SI CONTRADDICE DA SOLO (%s contro %s): "
                    "nessuna delle due meta' si butta, e nessun verdetto si "
                    "da'."
                    % (sil_and[0]["testo"][:40], sil_scr[0]["testo"][:40]))
        return "INCERTA", usati, note

    if not sil_and and not sil_scr:
        note.append("⛔ NESSUN segnale di SILICIO in questa impronta.  ⚠ La "
                    "dichiarazione da sola non basta in NESSUN verso: e' la "
                    "regola nata da D17, e vale anche quando fa comodo.")
        return "INCERTA", usati, note

    if sil_scr:
        return "DESKTOP", usati, note

    # ── da qui: il silicio dice TELEFONO.  Resta da dire COM'E' MESSO. ──
    schermo = impronta.get("schermo") or {}
    dati = impronta.get("ua_dati") or {}
    larghezza = schermo.get("l") or 0
    dpr = schermo.get("dpr") or 0
    mobile = dati.get("mobile")
    grossolano = bool(impronta.get("puntatore_grossolano"))
    tocco = (impronta.get("tocco_massimo") or 0) > 0

    # ⛔ D19: il puntatore NON entra piu' qui.  `[M]` 13 ago 2026, telefono in
    #    DeX su monitor 2560x1080: pointer:coarse, hover:none, tocco 5 —
    #    identico al telefono in mano.  Decide lo SCHERMO.
    if larghezza >= SCHERMO_DOCK:
        note.append("⭐ schermo di %s px CSS (dpr %s): non e' lo schermo di un "
                    "telefono ⇒ c'e' un DOCK con un monitor.  ⛔ Che quel dock "
                    "si chiami «Samsung DeX» il browser NON lo dice: e' [?], e "
                    "la sola strada onesta e' che lo dichiari l'operatore "
                    "(`serve --dispositivo android-dex`)." % (larghezza, dpr))
        if mobile is True:
            note.append("⚠ e userAgentData.mobile resta true: il telefono e' "
                        "su un monitor ma non si dichiara desktop")
        return "ANDROID-DOCK", usati, note

    if larghezza and larghezza < SCHERMO_TELEFONO:
        # ⛔⭐ D20 — E' LA TERZA VOLTA CHE LA STESSA FORMA MORDE, e stavolta
        #     l'ha trovata il giro VERO dell'utente delle 05.51 (`[M]`).
        #     Il ramo era `if mobile is True or (grossolano and tocco)` ⇒
        #     ANDROID-MANO.  Ma su un telefono `grossolano and tocco` e'
        #     **sempre** vero — D19 l'ha appena misurato: in DeX come in mano,
        #     `pointer: coarse` e `maxTouchPoints=5`.  ⇒ la seconda meta' della
        #     condizione era una TAUTOLOGIA, e ANDROID-SITO-DESKTOP era un ramo
        #     **irraggiungibile**: scritto per un caso che non poteva prendere.
        #     ⚠ Esattamente D19 (una FORMA usata per decidere una NATURA), e
        #     la cura e' la stessa: a distinguere «richiedi sito desktop» non
        #     e' il puntatore, e' la **DICHIARAZIONE** — un telefono che si
        #     dichiara desktop restando sullo schermo del telefono.
        if mobile is True:
            note.append("⭐ schermo da telefono (%s px) e il browser si "
                        "dichiara mobile: il telefono e' in mano e non si "
                        "traveste" % larghezza)
            return "ANDROID-MANO", usati, note
        if dic_scr:
            note.append("⚠ schermo da telefono (%s px, dpr %s) ma il browser "
                        "si dichiara DESKTOP (%d segnali di dichiarazione): e' "
                        "«richiedi sito desktop» — il telefono e' in mano, e' "
                        "solo la dichiarazione a essere riscritta.  ⛔ Il "
                        "puntatore qui NON distingue (grossolano=%s, tocco=%s): "
                        "in mano e in DeX vale lo stesso, ed e' D19."
                        % (larghezza, dpr, len(dic_scr), grossolano, tocco))
            return "ANDROID-SITO-DESKTOP", usati, note
        note.append("⚠ schermo da telefono (%s px) e il browser non si "
                    "dichiara ne' mobile ne' desktop: si sta sulla forma "
                    "(tocco=%s, puntatore grossolano=%s)"
                    % (larghezza, tocco, grossolano))
        return "ANDROID-MANO", usati, note

    note.append("⛔ il silicio dice telefono, ma la larghezza dello schermo "
                "(%s px) cade nella banda in mezzo fra telefono (<%d) e dock "
                "(>=%d): la banda in mezzo NON si promuove.  Il dispositivo e' "
                "accettato come Android, la sua forma resta [?]."
                % (larghezza or "assente", SCHERMO_TELEFONO, SCHERMO_DOCK))
    return "ANDROID-FORMA-INCERTA", usati, note


def applica_dichiarazione(nat, dichiarato, note):
    """⭐ LA DICHIARAZIONE DELL'OPERATORE — che puo' DARE UN NOME, non promuovere.

    ⛔ Le tre cose che NON puo' fare, e ciascuna e' un buco gia' pagato:
      · non scavalca la provenienza — quel veto lo applica `giudica`, prima di
        arrivare qui, e vale anche se l'operatore giurasse il contrario (E10);
      · non fabbrica silicio: su un DESKTOP misurato, «android-dex» non
        produce un Android.  Sarebbe il buco `terzo-portatile`;
      · non contraddice la forma misurata: se lo schermo e' quello di un
        telefono, «dex» non lo allarga.

    ⇒ Puo' fare **una** cosa: mettere la parola «DeX» su un dock che il banco
      ha gia' misurato, e la riga dice che quella parola e' `[D]`, dichiarata.
    """
    if not dichiarato:
        return nat
    chiave = str(dichiarato.get("dispositivo", "")).strip().lower()
    if chiave not in DISPOSITIVI_DICHIARABILI:
        note.append("⚠ dichiarazione «%s» sconosciuta: si ignora, e LO DICO. "
                    "Dichiarabili: %s"
                    % (chiave, ", ".join(sorted(DISPOSITIVI_DICHIARABILI))))
        return nat
    etichetta, testo = DISPOSITIVI_DICHIARABILI[chiave]
    note.append("[D] DICHIARATO dall'operatore (⛔ NON misurato): «%s» — %s"
                % (chiave, testo))
    if nat == "ANDROID-DOCK" and etichetta == "ANDROID-DEX":
        note.append("⭐ il misurato dice DOCK, il dichiarato dice DeX: "
                    "coincidono, e la riga porta l'etichetta ANDROID-DEX con "
                    "il pezzo «DeX» marcato [D] e il pezzo «dock» marcato [M]")
        return "ANDROID-DEX"
    if nat == etichetta:
        note.append("⭐ il dichiarato coincide col misurato: niente cambia, e "
                    "la coincidenza e' essa stessa un controllo passato")
        return nat
    note.append("⛔ IL DICHIARATO NON COINCIDE COL MISURATO — dichiarato «%s», "
                "misurato «%s».  ⭐ Vince il MISURATO, e la discordanza si "
                "stampa invece di essere risolta in silenzio: una dichiarazione "
                "che potesse promuovere sarebbe la porta di servizio di E10."
                % (etichetta, nat))
    return nat


def vecchio_riconoscimento(ua):
    """⛔ Il riconoscimento di PRIMA — tenuto qui apposta.

    Non serve piu' a decidere: serve a **misurare la differenza**.  Un rilievo
    che dice «adesso e' meglio» senza il vecchio accanto non e' una misura.
    """
    return bool(re.search(r"Android|iPhone|iPad|Mobile", ua or ""))


def impronte_per_indirizzo(righe):
    """⭐ CHI HA MANDATO L'IMPRONTA, INDIRIZZO PER INDIRIZZO — e serve a non
       costruire il TERZO rifiuto.

    ⛔ IL DIFETTO D21, e l'ha trovato il giro vero dell'utente delle 07.43.
       Le righe `tipo: "pixel"` sono una POST di byte grezzi: portano `ip`,
       `ua` e il nome del file, e **non portano nessuna impronta** — la pagina
       l'impronta la manda con l'esito, non con i pixel.
       ⇒ Giudicate da sole, quelle righe danno sempre `INCERTA` ⇒ `SOSPESO`,
         e `02-giudizio-telefono.sh` — che tiene solo i pixel di un
         dispositivo **ACCETTATO** — non ne teneva **nessuno**.  Il telefono
         dell'utente ha dipinto quattro immagini giuste e il banco avrebbe
         detto «nessun file di pixel viene da un dispositivo accettato».
       ⛔ E' di nuovo la forma E8: «non ha dipinto» e «ha dipinto e la riga
          dei pixel non porta l'impronta» avevano la stessa faccia.

    ⇒ La cura: l'impronta si PRESTA dalla riga di esito dello **stesso
      indirizzo**, e la riga di giudizio dice che e' prestata — `[R]`, non
      `[M]`.  ⚠ Non e' un dettaglio di forma: due giri dello stesso telefono
      possono avere due FORME diverse (in DeX e in mano, `[M]` 13 ago), e
      allora l'etichetta prestata dice il DISPOSITIVO giusto e puo' dire la
      forma sbagliata.  Percio' si presta la piu' vicina **nel tempo**.

    ⛔ E NON APRE E10: il veto sta sull'indirizzo della riga dei PIXEL, che
       resta il suo.  Un file di pixel spedito da questo portatile resta
       rifiutato anche se in registro c'e' l'impronta di un telefono.
    """
    fuori = {}
    for d in righe:
        dati = d.get("dati") or {}
        imp = dati.get("impronta") or d.get("impronta")
        ip = d.get("ip")
        if imp and ip:
            fuori.setdefault(ip, []).append((str(d.get("ora") or ""), imp))
    for ip in fuori:
        fuori[ip].sort(key=lambda x: x[0])
    return fuori


def _presta_impronta(per_ip, ip, ora):
    """L'impronta piu' vicina NEL TEMPO fra quelle dello stesso indirizzo.

    ⛔ La piu' vicina, non «l'ultima»: i pixel delle 07.43 sono del giro in
       DeX, quelli delle 07.51 del giro col telefono in mano.  Prendere
       sempre l'ultima attribuirebbe i primi alla forma sbagliata — e una
       forma sbagliata in una riga di prova e' un `[M]` falso.
    """
    cand = (per_ip or {}).get(ip) or []
    if not cand:
        return None, None
    ora = str(ora or "")
    if not ora:
        return cand[-1][1], cand[-1][0]
    prima = [c for c in cand if c[0] <= ora]
    scelta = prima[-1] if prima else cand[0]
    return scelta[1], scelta[0]


def giudica(riga, locali, dichiarazioni=None, impronte_per_ip=None):
    ip = riga.get("ip")
    dati = riga.get("dati") or {}
    impronta = dati.get("impronta") or riga.get("impronta")
    prestata_da = None
    if not impronta and impronte_per_ip:
        impronta, prestata_da = _presta_impronta(impronte_per_ip, ip,
                                                 riga.get("ora"))
    prov, perche_prov = provenienza(ip, locali)
    nat, segnali_usati, note = natura(impronta)
    if prestata_da is not None:
        note.append("[R] ⭐ QUESTA RIGA NON PORTA L'IMPRONTA (e' una POST di "
                    "pixel, non un esito): l'impronta e' PRESTATA dall'esito "
                    "delle %s dello stesso indirizzo %s.  ⛔ Il DISPOSITIVO e' "
                    "quello — l'indirizzo non lo scrive il browser — ma la "
                    "FORMA (mano / dock) e' quella di un'altra riga, e se fra "
                    "le due il telefono e' stato tolto dal dock l'etichetta "
                    "puo' essere la forma sbagliata.  ⚠ `[R]`, non `[M]`."
                    % (prestata_da or "?", ip))
    elif not impronta and impronte_per_ip is not None:
        note.append("⛔ nessuna impronta su questa riga E NESSUNA da prestare "
                    "per l'indirizzo %s: non e' «il dispositivo ha fallito», "
                    "e' «di questa riga non si sa chi l'ha mandata»" % ip)

    dichiarato = (dichiarazioni or {}).get(dati.get("giro") or "")

    # ⛔ IL VETO: la provenienza vince sempre.  E' la difesa E10.
    if prov in ("QUESTA-MACCHINA", "LOOPBACK"):
        # ⛔⭐ E LA DICHIARAZIONE NON SI APPLICA NEMMENO: qui non e' che «viene
        #    scavalcata», e' che non entra proprio.  Se entrasse, l'etichetta
        #    del portatile direbbe ANDROID-DEX in una riga RIFIUTATA — e la
        #    prima persona che leggesse l'etichetta invece del verdetto
        #    riaprirebbe E10 dalla porta di servizio.
        if dichiarato:
            note.append("⛔ c'e' una dichiarazione dell'operatore per questo "
                        "giro («%s») e NON e' stata applicata: la provenienza "
                        "e' QUESTA macchina, e li' nessuna dichiarazione entra."
                        % dichiarato.get("dispositivo"))
        verdetto = "RIFIUTATO"
        motivo = ("forma E10 — il giro viene da QUESTA macchina.  "
                  "Un numero misurato qui certifica lo STRUMENTO e non "
                  "misura S2")
        if nat.startswith("ANDROID"):
            motivo += (".  ⛔ E la pagina si dichiarava %s: la dichiarazione "
                       "NON scavalca l'indirizzo" % nat)
        return _riga_di_giudizio(verdetto, motivo, prov, perche_prov, nat,
                                 segnali_usati, note, impronta, riga, None,
                                 prestata_da)

    nat = applica_dichiarazione(nat, dichiarato, note)

    if prov == "SERVER-NIC-OS":
        verdetto = "RIFIUTATO"
        motivo = "e' il server, non un dispositivo dell'utente"
    elif prov == "SCONOSCIUTA":
        verdetto = "SOSPESO"
        motivo = ("senza l'indirizzo di provenienza la difesa E10 non esiste: "
                  "nessun verdetto")
    # ⭐ TUTTE le etichette ANDROID-* si accettano, DOCK e FORMA-INCERTA
    #    comprese: il silicio ha detto «telefono» e la provenienza ha detto
    #    «terzo dispositivo».  ⛔ Che il dock si chiami DeX o no NON cambia il
    #    diritto del dispositivo a essere misurato — se lo cambiasse, un
    #    operatore che dimentica una bandierina si vedrebbe rifiutare il
    #    telefono, ed e' il terzo rifiuto che stiamo scrivendo per non avere.
    elif nat.startswith("ANDROID"):
        verdetto = "ACCETTATO"
        motivo = "terzo dispositivo, e il suo SILICIO e' da telefono: %s" % nat
    elif nat == "DESKTOP":
        verdetto = "RIFIUTATO"
        motivo = ("e' un terzo dispositivo ma e' un COMPUTER: «non e' questo "
                  "portatile» non vuol dire «e' un telefono»")
    else:
        verdetto = "SOSPESO"
        motivo = ("un terzo dispositivo e' arrivato, ma il suo silicio non si "
                  "e' fatto riconoscere: potrebbe essere un altro portatile.  "
                  "⛔ Nessun verdetto su S2")

    return _riga_di_giudizio(verdetto, motivo, prov, perche_prov, nat,
                             segnali_usati, note, impronta, riga, dichiarato,
                             prestata_da)


def _riga_di_giudizio(verdetto, motivo, prov, perche_prov, nat, segnali_usati,
                      note, impronta, riga, dichiarato, prestata_da=None):
    """⛔ La riga che finisce nel registro — e porta SEMPRE, separati, il
       misurato e il dichiarato.  Sono due cose, e un giorno qualcuno dovra'
       poter rileggere quale delle due portava il verdetto."""
    ua = (impronta or {}).get("ua_stringa") or riga.get("ua") or ""
    return {
        "verdetto": verdetto,
        "motivo": motivo,
        "provenienza": prov,
        "provenienza_perche": perche_prov,
        "natura": nat,
        "segnali_usati": segnali_usati,
        "note": note,
        "dichiarazione_operatore": (dichiarato or {}).get("dispositivo"),
        # ⛔ `None` = l'impronta e' di QUESTA riga `[M]`.  Una data = e'
        #    PRESTATA da un'altra riga dello stesso indirizzo `[R]`.  Le due
        #    cose non si confondono, mai.
        "impronta_prestata_da": prestata_da,
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
#   · ⭐ `dex-reale-13ago` e' l'impronta **VERA** del telefono dell'utente in
#     DeX, copiata riga per riga da `02-giudizio-sonda.jsonl` (esito delle
#     07.43.02 del 13 agosto 2026, provenienza 192.168.0.25).  ⛔ Non e' piu'
#     `[?]`: i valori che Chrome espone in DeX adesso li abbiamo MISURATI, e
#     sono precisamente quelli che hanno prodotto il secondo rifiuto.
#   · `telefono-in-mano` ha l'asse 1 misurato e l'asse 2 dichiarato: `[?]`, e
#     resta `[?]` — quel che quel caso certifica e' **la decisione**.
#
# ⭐ E i due casi che il mandato del 13 agosto chiede per nome, che girano
#    tutt'e due a OGNI esecuzione:
#      dex-reale-13ago-dichiarato   ⇒ ACCETTATO e marcato DEX
#      portatile-dichiarato-dex     ⇒ RIFIUTATO, e la dichiarazione non entra
# ===========================================================================

# ⭐ L'IMPRONTA VERA DEL 13 AGOSTO — verbatim dal registro dell'utente.
#    ⛔ Non si abbrevia e non si «pulisce»: e' la prova, ed e' l'unica riga di
#       questo file che nessuno ha inventato.
IMPRONTA_DEX_VERA = {
    "quando": "2026-08-13T05:42:51.934Z",
    "ua_stringa": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "piattaforma_legacy": "Linux armv81",
    "ua_dati": {"mobile": False, "platform": "Linux"},
    "ua_dati_alta_entropia": {
        "architecture": "x86", "bitness": "64", "formFactors": ["Desktop"],
        "mobile": False, "model": "", "platform": "Linux",
        "platformVersion": ""},
    "memoria_gb": 8, "nuclei": 8, "tocco_massimo": 5,
    "puntatore_grossolano": True, "puntatore_fine": False,
    "niente_sorvolo": True,
    "schermo": {"l": 2560, "a": 1080, "dpr": 1.2000000476837158,
                "disponibile_l": 2560, "disponibile_a": 1080,
                "colore_bit": 24},
    "finestra": {"l": 2133, "a": 772}, "fuso": "Europe/Rome",
    "gpu": {"resa": "ANGLE (Qualcomm, Adreno (TM) 740, OpenGL ES 3.2)",
            "fornitore": "Google Inc. (Qualcomm)", "mascherato": False},
}

# ⭐ E LA SECONDA IMPRONTA VERA — lo STESSO telefono, 9 minuti dopo, TOLTO dal
#    dock e tenuto in mano con «richiedi sito desktop» ancora acceso.
#    ⛔ E' la riga che ha scoperto D20: schermo 384x832 (quello del telefono),
#       silicio identico, e la dichiarazione ancora quella del desktop.
#    ⚠ `[M]`, verbatim da `02-giudizio-sonda.jsonl`, esito delle 05.51.44 UTC.
IMPRONTA_MANO_TRAVESTITA = {
    "quando": "2026-08-13T05:51:44.515Z",
    "ua_stringa": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "piattaforma_legacy": "Linux armv81",
    "ua_dati": {"mobile": False, "platform": "Linux"},
    "ua_dati_alta_entropia": {
        "architecture": "x86", "bitness": "64", "formFactors": ["Desktop"],
        "mobile": False, "model": "", "platform": "Linux",
        "platformVersion": ""},
    "memoria_gb": 8, "nuclei": 8, "tocco_massimo": 5,
    "puntatore_grossolano": True, "puntatore_fine": False,
    "niente_sorvolo": True,
    "schermo": {"l": 384, "a": 832, "dpr": 3.375000238418579,
                "disponibile_l": 384, "disponibile_a": 832,
                "colore_bit": 24},
    "finestra": {"l": 816, "a": 1476}, "fuso": "Europe/Rome",
    "gpu": {"resa": "ANGLE (Qualcomm, Adreno (TM) 740, OpenGL ES 3.2)",
            "fornitore": "Google Inc. (Qualcomm)", "mascherato": False},
}

DICH_DEX = {"20260812-2035": {"dispositivo": "android-dex",
                              "da": "operatore, per la certificazione"}}

CASI = [
    ("portatile-onesto", "RIFIUTATO", "DESKTOP", None,
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

    ("portatile-travestito", "RIFIUTATO", "DESKTOP", None,
     # ⛔⭐ IL CASO CHE LA CURA DI D17 RENDE POSSIBILE: il Chrome del portatile
     #     con uno user agent da telefono.  Il vecchio riconoscimento lo
     #     ACCETTA (ed e' misurato sotto), il nuovo lo RIFIUTA per indirizzo.
     # ⚠ 13 ago: l'atteso della NATURA cambia da ANDROID-MANO a DESKTOP, e il
     #    cambiamento e' un irrobustimento — il silicio (Mesa Intel) adesso
     #    smaschera il travestimento **anche sull'asse 2**, mentre prima la
     #    sola dichiarazione bastava a farlo passare per un Android.
     #    ⛔ E percio' questo caso non certifica piu' il VETO: il veto lo
     #       certifica `portatile-silicio-falsificato`, qui sotto.
     {"ip": "192.168.0.3", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Linux; Android 14; SM-S918B) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/151.0.0.0 Mobile Safari/537.36",
         "ua_dati": {"mobile": True, "platform": "Android"},
         "ua_dati_alta_entropia": {"platform": "Android", "mobile": True,
                                   "model": "SM-S918B"},
         "gpu": {"resa": "Mesa Intel(R) UHD Graphics (JSL)"},
         "piattaforma_legacy": "Linux x86_64",
         "tocco_massimo": 5, "puntatore_grossolano": True,
         "puntatore_fine": False,
         "schermo": {"l": 412, "a": 915, "dpr": 2.6}}}}),

    ("portatile-silicio-falsificato", "RIFIUTATO", "ANDROID-MANO", None,
     # ⛔⭐ IL CASO CHE CERTIFICA IL VETO, E BASTA LUI.  Un portatile su cui
     #     TUTTO — silicio compreso — dichiara un telefono: GPU Adreno, ARM,
     #     mobile=true, schermo da telefono.  L'asse 2 e' completamente
     #     ingannato, e dice ANDROID-MANO.  ⇒ Il RIFIUTO che si legge qui
     #     sotto viene **solo** dalla provenienza, che e' quel che E10 chiede.
     {"ip": "192.168.0.3", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Linux; Android 14; SM-S918B) …Mobile…",
         "ua_dati": {"mobile": True, "platform": "Android"},
         "ua_dati_alta_entropia": {"platform": "Android", "mobile": True,
                                   "model": "SM-S918B", "architecture": "arm"},
         "gpu": {"resa": "ANGLE (Qualcomm, Adreno (TM) 740, OpenGL ES 3.2)"},
         "piattaforma_legacy": "Linux armv81",
         "tocco_massimo": 5, "puntatore_grossolano": True,
         "puntatore_fine": False,
         "schermo": {"l": 412, "a": 915, "dpr": 2.6}}}}),

    ("dex-sintetico", "ACCETTATO", "ANDROID-DOCK", None,
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

    # ═══ ⭐⭐ I DUE CASI DEL MANDATO DEL 13 AGOSTO — l'impronta VERA ═══════
    ("dex-reale-13ago", "ACCETTATO", "ANDROID-DOCK", None,
     # ⭐ La riga che il banco ha RIFIUTATO stamattina, rigiudicata senza
     #    nessuna dichiarazione.  ⛔ Deve essere ACCETTATA lo stesso: il
     #    diritto del dispositivo a essere misurato non puo' dipendere da una
     #    bandierina che l'operatore puo' dimenticare.
     {"ip": "192.168.0.25",
      "dati": {"giro": "20260812-2035", "impronta": IMPRONTA_DEX_VERA}}),

    ("dex-reale-13ago-dichiarato", "ACCETTATO", "ANDROID-DEX", DICH_DEX,
     # ⭐ La stessa identica riga, con la dichiarazione dell'operatore.  L'unica
     #    cosa che cambia e' il NOME: «dock» resta [M], «DeX» diventa [D].
     {"ip": "192.168.0.25",
      "dati": {"giro": "20260812-2035", "impronta": IMPRONTA_DEX_VERA}}),

    ("mano-travestita-13ago", "ACCETTATO", "ANDROID-SITO-DESKTOP", None,
     # ⭐ IL CASO CHE HA SCOPERTO D20, e non e' costruito: e' il giro delle
     #    05.51 dell'utente.  Lo stesso telefono, fuori dal dock.
     #    ⛔ Prima della cura questa riga diceva ANDROID-MANO — accettata lo
     #       stesso, quindi il difetto non si vedeva dal verdetto: si vedeva
     #       solo dall'ETICHETTA, ed e' il modo in cui i difetti sopravvivono.
     {"ip": "192.168.0.25",
      "dati": {"giro": "20260812-2035",
               "impronta": IMPRONTA_MANO_TRAVESTITA}}),

    ("mano-travestita-dichiarata-dex", "ACCETTATO", "ANDROID-SITO-DESKTOP",
     DICH_DEX,
     # ⛔⭐ E LA STESSA RIGA CON LA DICHIARAZIONE «android-dex» ADDOSSO — che e'
     #     quel che succede DAVVERO se l'operatore accende la bandierina una
     #     volta per tutto il giro e poi l'utente toglie il telefono dal dock.
     #     ⇒ La dichiarazione NON allarga lo schermo: il misurato dice
     #       SITO-DESKTOP, e la discordanza si STAMPA.
     {"ip": "192.168.0.25",
      "dati": {"giro": "20260812-2035",
               "impronta": IMPRONTA_MANO_TRAVESTITA}}),

    ("portatile-dichiarato-dex", "RIFIUTATO", "DESKTOP", DICH_DEX,
     # ⛔⭐ IL CASO OPPOSTO DEL MANDATO: lo stesso giro, la stessa
     #     dichiarazione «android-dex», ma la connessione nasce sul PORTATILE.
     #     ⇒ RIFIUTATO, e la dichiarazione non entra nemmeno.  La provenienza
     #     ha diritto di veto, e la dichiarazione non e' un modo di aggirarlo.
     {"ip": "192.168.0.3", "dati": {"giro": "20260812-2035", "impronta": {
         "ua_stringa": "Mozilla/5.0 (X11; Linux x86_64) …Chrome/151…",
         "ua_dati": {"mobile": False, "platform": "Linux"},
         "ua_dati_alta_entropia": {"platform": "Linux", "mobile": False,
                                   "architecture": "x86"},
         "piattaforma_legacy": "Linux x86_64",
         "gpu": {"resa": "Mesa Intel(R) UHD Graphics (JSL)"},
         "tocco_massimo": 0, "puntatore_fine": True, "nuclei": 8,
         "memoria_gb": 8, "schermo": {"l": 1920, "a": 1080, "dpr": 1}}}}),

    ("terzo-computer-dichiarato-dex", "RIFIUTATO", "DESKTOP", DICH_DEX,
     # ⛔ E il buco piu' sottile: un computer che NON e' questo portatile —
     #    quindi il veto della provenienza non scatta — dichiarato «telefono in
     #    DeX».  ⇒ La dichiarazione **non fabbrica silicio**: la GPU dice
     #    NVIDIA, e il verdetto resta RIFIUTATO.
     {"ip": "192.168.0.10", "dati": {"giro": "20260812-2035", "impronta": {
         "ua_stringa": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) …Chrome/151…",
         "ua_dati": {"mobile": False, "platform": "Windows"},
         "ua_dati_alta_entropia": {"platform": "Windows", "mobile": False},
         "piattaforma_legacy": "Win32",
         "gpu": {"resa": "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11)"},
         "tocco_massimo": 0, "puntatore_fine": True,
         "schermo": {"l": 2560, "a": 1440, "dpr": 1}}}}),

    ("telefono-in-mano", "ACCETTATO", "ANDROID-MANO", None,
     {"ip": "192.168.0.24", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Linux; Android 14; SM-S918B) …Mobile…",
         "ua_dati": {"mobile": True, "platform": "Android"},
         "ua_dati_alta_entropia": {"platform": "Android", "mobile": True,
                                   "model": "SM-S918B"},
         "gpu": {"resa": "ANGLE (ARM, Mali-G78, OpenGL ES 3.2)"},
         "tocco_massimo": 5, "puntatore_grossolano": True,
         "puntatore_fine": False,
         "schermo": {"l": 412, "a": 915, "dpr": 2.6}}}}),

    ("terzo-portatile", "RIFIUTATO", "DESKTOP", None,
     # ⭐ Il buco che si apre curando D17: «non e' questa macchina» non vuol
     #    dire «e' un telefono».  In casa ci sono altri computer.
     {"ip": "192.168.0.10", "dati": {"impronta": {
         "ua_stringa": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) …Chrome/151…",
         "ua_dati": {"mobile": False, "platform": "Windows"},
         "ua_dati_alta_entropia": {"platform": "Windows", "mobile": False},
         "gpu": {"resa": "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11)"},
         "tocco_massimo": 0, "puntatore_fine": True,
         "schermo": {"l": 2560, "a": 1440, "dpr": 1}}}}),

    ("dex-reale-12ago", "SOSPESO", "INCERTA", None,
     # ⚠ La riga VERA di stasera: c'e' l'indirizzo, non c'e' l'impronta —
     #    perche' quella versione della pagina non la spediva.  ⛔ L'esito
     #    giusto per questa riga NON e' «accettato»: e' «sospeso», e il
     #    secondo giro raccogliera' l'asse 2.
     {"ip": "192.168.0.24", "ua":
         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like "
         "Gecko) Chrome/150.0.0.0 Safari/537.36", "dati": {}}),

    ("curl-del-controllo", "RIFIUTATO", "INCERTA", None,
     {"ip": "127.0.0.1", "ua": "curl/8.14.1", "dati": {}}),
]

# ⛔ I due casi che il mandato del 13 agosto chiede per nome.  Se uno dei due
#    mancasse dall'elenco, `certifica` lo direbbe — un banco che certifica «i
#    casi che ci sono» non certifica quelli che dovrebbero esserci.
CASI_OBBLIGATORI = ("dex-reale-13ago-dichiarato", "portatile-dichiarato-dex")


def certifica_prestito(locali):
    """⛔ LA CERTIFICAZIONE DI D21 — l'impronta prestata, e il buco che NON apre.

    Tre casi, e il terzo e' quello che conta: prestare un'impronta non deve
    diventare un modo di far entrare i pixel del PORTATILE.
    """
    print("\n\033[1m== D21 — L'IMPRONTA PRESTATA ALLE RIGHE DEI PIXEL\033[0m")
    registro = [
        # l'esito col telefono in DeX, alle 07.43
        {"ora": "2026-08-13T07:43:02", "ip": "192.168.0.25", "tipo": "esito",
         "dati": {"giro": "20260812-2035", "impronta": IMPRONTA_DEX_VERA}},
        # i pixel, subito dopo, dallo STESSO indirizzo e senza impronta
        {"ora": "2026-08-13T07:43:10", "ip": "192.168.0.25", "tipo": "pixel",
         "nome": "pagina-20260812-2035-A-10bit-annexb.rgb24", "dati": {}},
        # lo stesso telefono TOLTO DAL DOCK, alle 07.51, e i suoi pixel
        {"ora": "2026-08-13T07:51:44", "ip": "192.168.0.25", "tipo": "esito",
         "dati": {"giro": "20260812-2035",
                  "impronta": IMPRONTA_MANO_TRAVESTITA}},
        {"ora": "2026-08-13T07:51:56", "ip": "192.168.0.25", "tipo": "pixel",
         "nome": "pagina-20260812-2035-A-10bit-annexb.rgb24", "dati": {}},
        # ⛔⭐ E I PIXEL DEL PORTATILE, nello stesso registro: se il prestito
        #     fosse fatto male, l'impronta del telefono qui sopra li
        #     promuoverebbe.  Devono restare RIFIUTATI.
        {"ora": "2026-08-13T07:55:00", "ip": "192.168.0.3", "tipo": "pixel",
         "nome": "pagina-20260812-2035-A-10bit-annexb.rgb24", "dati": {}},
    ]
    atteso = [
        ("esito 07.43 (DeX)",           "ACCETTATO", "ANDROID-DOCK",         False),
        ("pixel 07.43 → presta DeX",    "ACCETTATO", "ANDROID-DOCK",         True),
        ("esito 07.51 (in mano)",       "ACCETTATO", "ANDROID-SITO-DESKTOP", False),
        ("pixel 07.51 → presta MANO",   "ACCETTATO", "ANDROID-SITO-DESKTOP", True),
        ("pixel dal PORTATILE",         "RIFIUTATO", "INCERTA",              False),
    ]
    per_ip = impronte_per_indirizzo(registro)
    male = 0
    for riga, (nome, av, an, ap) in zip(registro, atteso):
        g = giudica(riga, locali, None, per_ip)
        prestata = g["impronta_prestata_da"] is not None
        bene = (g["verdetto"] == av and g["natura"] == an and prestata == ap)
        print("    %s  %-28s atteso %s/%s/prestata=%s → %s/%s/prestata=%s"
              % ("\033[1;32mOK\033[0m" if bene else "\033[1;31mNO\033[0m",
                 nome, av, an, ap, g["verdetto"], g["natura"], prestata))
        if not bene:
            male = 3
    print("    ⭐ e il caso che conta: i pixel del PORTATILE restano RIFIUTATI "
          "anche con l'impronta di un telefono nello stesso registro — il "
          "prestito riempie l'asse 2, il veto E10 sta sull'asse 1 e non si "
          "presta.")
    return male


def certifica():
    locali = indirizzi_locali() | {"192.168.0.3"}
    print("\n\033[1m== LA CERTIFICAZIONE DEL RICONOSCIMENTO — atteso scritto "
          "PRIMA\033[0m")
    print("    --  indirizzi di questa macchina: %s"
          % ", ".join(sorted(locali)))
    esito = 0

    # ⛔ PRIMA DI GIUDICARE: i casi che il mandato chiede PER NOME ci sono?
    #    Un banco che certifica «i casi che ci sono» non certifica quelli che
    #    dovrebbero esserci, e il buco si legge come un OK.
    nomi = {c[0] for c in CASI}
    mancanti = [n for n in CASI_OBBLIGATORI if n not in nomi]
    if mancanti:
        print("\n    \033[1;31mNO\033[0m  ⛔ mancano dall'elenco i casi "
              "OBBLIGATORI: %s" % ", ".join(mancanti))
        esito = 3
    else:
        print("    --  i %d casi obbligatori del mandato ci sono tutti: %s"
              % (len(CASI_OBBLIGATORI), ", ".join(CASI_OBBLIGATORI)))

    for nome, atteso_v, atteso_n, dich, riga in CASI:
        g = giudica(riga, locali, dich)
        bene = (g["verdetto"] == atteso_v and g["natura"] == atteso_n)
        marca = "\033[1;32mOK\033[0m" if bene else "\033[1;31mNO\033[0m"
        print("\n    %s  %-22s atteso %s/%s → %s/%s"
              % (marca, nome, atteso_v, atteso_n, g["verdetto"], g["natura"]))
        print("        provenienza: %s (%s)"
              % (g["provenienza"], g["provenienza_perche"]))
        if dich:
            print("        dichiarazione dell'operatore in ingresso: %s "
                  "(⛔ applicata? %s)"
                  % (list(dich.values())[0].get("dispositivo"),
                     "si'" if g["dichiarazione_operatore"] else "NO"))
        for s in g["segnali_usati"]:
            print("        segnale: %s" % s)
        for n in g["note"]:
            print("        %s" % n)
        print("        vecchio riconoscimento (per user agent): %s"
              % g["vecchio_riconoscimento_avrebbe_detto"])
        if not bene:
            esito = 3
    esito = certifica_prestito(locali) or esito

    print("\n    --  ⭐ e la differenza MISURATA, non affermata:")
    for nome, _a, _b, dich, riga in CASI:
        g = giudica(riga, locali, dich)
        if g["vecchio_riconoscimento_avrebbe_detto"] != g["verdetto"]:
            print("        %-22s vecchio: %-10s nuovo: %s"
                  % (nome, g["vecchio_riconoscimento_avrebbe_detto"],
                     g["verdetto"]))
    if esito:
        print("\n    \033[1;31mNO\033[0m  ⛔ il riconoscimento NON fa quel che "
              "ha dichiarato: nessun verdetto si da'")
    else:
        print("\n    \033[1;32mOK\033[0m  %d casi su %d, e i due che il "
              "mandato chiede per nome sono: telefono in DeX ACCETTATO e "
              "marcato DEX, portatile RIFIUTATO anche dichiarandolo DeX"
              % (len(CASI), len(CASI)))
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
    # ⭐ LA DICHIARAZIONE DELL'OPERATORE, sul percorso VERO e non solo nella
    #    certificazione.  ⛔ `leggi_dichiarazioni` esisteva e non la chiamava
    #    nessuno: una funzione scritta e mai invocata e' una cura che non e'
    #    mai entrata in servizio, e si legge come se ci fosse.
    #    ⚠ Assente non e' un errore: senza, il telefono in DeX resta
    #    ANDROID-DOCK ed e' ACCETTATO lo stesso.
    percorso_dich = None
    if "--dichiarazioni" in arg:
        percorso_dich = arg[arg.index("--dichiarazioni") + 1]
    dichiarazioni = leggi_dichiarazioni(percorso_dich)
    if percorso_dich and not dichiarazioni:
        print("    ⚠ --dichiarazioni %s non ha prodotto nessuna "
              "dichiarazione: si giudica sul SOLO misurato, E LO DICO"
              % percorso_dich)
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
    # ⭐ D21: le impronte si raccolgono PRIMA, per poterle prestare alle righe
    #    che non ne portano una (i pixel).  Vedi `impronte_per_indirizzo`.
    per_ip = impronte_per_indirizzo(righe)

    conteggio = {}
    for d in righe:
        if d.get("tipo") == "prova":
            continue                       # il gettone del controllo, non un giro
        g = giudica(d, locali, dichiarazioni, per_ip)
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
