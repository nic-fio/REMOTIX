#!/usr/bin/env python3
"""02-pagina-verdetto.py — legge `02-pagina-esiti.jsonl` e CALCOLA il verdetto.

    python3 02-pagina-verdetto.py <giro> [<giro> …]
    python3 02-pagina-verdetto.py <giro> --pretendi P2=rosso --pretendi P4=verde

===========================================================================
⛔ PERCHE' IL VERDETTO NON STA NELLA PAGINA

B0.4, e in questo banco vale doppio: *l'atteso lo confronta il banco, non chi
legge* — e nemmeno chi misura.  La pagina di prova gira **dentro** l'imputato:
se il motore avesse un difetto che tocca il confronto, il confronto sarebbe
d'accordo con il difetto.  Qui il verdetto lo calcola un programma che gira
fuori dal browser, su un registro su disco che chiunque puo' rileggere fra sei
mesi.

⚠ E c'e' una seconda ragione, piu' prosaica: la pagina di prova **e' anche
  l'imputato dei giri con il guasto innestato**.  Un guasto che facesse
  mentire il verdetto della pagina non sarebbe visibile dalla pagina stessa.

===========================================================================
⛔ LA DISTINZIONE CHE QUESTO PROGRAMMA ESISTE PER TENERE

Ci sono **due domande diverse**, e confonderle e' il modo piu' facile di
scrivere un `[M]` falso:

  1. **il banco funziona?**     P1 il lettore dice si' · P2 il lettore dice no ·
                                 P3 il banco distingue i due pattern · P4 la
                                 catena esiste (VP9) · P5 l'immagine dipinta e'
                                 quella chiesta · P6 lo zero ha sempre una
                                 causa.  Se una cade, il banco non ha il
                                 diritto di pubblicare niente su HEVC — e
                                 questo programma esce **1**.
  2. **HEVC arriva al pixel?**  E' la MISURA.  Un «no» qui non e' un difetto
                                 del banco e non e' un difetto nostro
                                 (`DECISIONI.md` §2.7: il massimo lo offre il
                                 server, l'altezza la mette il client) — e' un
                                 **fatto da dichiarare**.  Questo programma
                                 NON esce 1 per un «no» su HEVC.

⛔ Un banco che uscisse rosso perche' Firefox non decodifica HEVC insegnerebbe
   a chi legge a ignorare il rosso — e il giorno in cui il rosso fosse del
   banco, nessuno lo guarderebbe.
"""
import json
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "02-pagina-esiti.jsonl"

VERDE = "\033[1;32mOK\033[0m"
ROSSO = "\033[1;31mNO\033[0m"
GIALLO = "\033[1;33m??\033[0m"
CELLE = 8


def carica(giri):
    if not REGISTRO.exists():
        print(f"{ROSSO}  {REGISTRO} non esiste: nessun giro ha mai scritto niente",
              file=sys.stderr)
        return {}
    per_giro = {g: [] for g in giri}
    illeggibili = 0
    with REGISTRO.open(encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            try:
                d = json.loads(riga)
            except Exception:
                illeggibili += 1
                continue
            if d.get("giro") in per_giro:
                per_giro[d["giro"]].append(d)
    if illeggibili:
        # ⛔ Non si tace: righe illeggibili nel registro sono una misura persa,
        #    e «poche righe» e «molte righe buttate» hanno lo stesso aspetto.
        print(f"    ⚠ {illeggibili} righe del registro non sono JSON e sono "
              "state saltate")
    return per_giro


def prima(righe, tipo, prova=None):
    for d in righe:
        if d.get("tipo") == tipo and (prova is None or d.get("prova") == prova):
            return d
    return None


def controlli(righe):
    """I SEI controlli che rendono valido il banco.  Ciascuno ritorna
       (esito, frase) dove esito e' 'verde', 'rosso' o 'assente'.

       ⚠ Erano quattro nella prima stesura.  P5 e P6 sono nati **certificando**,
         il 12 agosto 2026: due guasti innestati apposta non facevano virare
         niente, ed e' il modo in cui un controllo che non controlla si
         dichiara (`LEZIONI.md` §1.3)."""
    fuori = {}

    p1 = prima(righe, "CONTROLLO", "P1-lettore-si")
    if p1 is None:
        fuori["P1"] = ("assente", "P1 non e' stato eseguito")
    elif p1.get("corrette") == CELLE:
        fuori["P1"] = ("verde", f"il lettore trova {CELLE}/{CELLE} tinte "
                                "dipinte a mano: getImageData e la "
                                "classificazione funzionano")
    else:
        fuori["P1"] = ("rosso", f"il lettore trova {p1.get('corrette')}/{CELLE} "
                                "tinte che ci sono di sicuro: e' il LETTORE a "
                                "non funzionare, non il decodificatore"
                                + (f" — {p1.get('errore')}" if p1.get("errore") else ""))

    p2 = prima(righe, "CONTROLLO", "P2-lettore-no")
    if p2 is None:
        fuori["P2"] = ("assente", "P2 non e' stato eseguito")
    elif p2.get("corrette", CELLE) < CELLE:
        fuori["P2"] = ("verde", f"su una tela grigia piatta il lettore trova "
                                f"{p2.get('corrette')}/{CELLE}: sa dire di no")
    else:
        fuori["P2"] = ("rosso", "su una tela grigia piatta il lettore trova "
                                f"{CELLE}/{CELLE}: risponde sempre giusto, "
                                "quindi ogni verde di questo banco e' vuoto")

    vp9 = prima(righe, "SEQUENZA", "P4-controllo-vp9")
    if vp9 is None:
        fuori["P4"] = ("assente", "il controllo VP9 non e' stato eseguito")
    elif vp9.get("celle_giuste") == CELLE:
        fuori["P4"] = ("verde", f"VP9 arriva al pixel: {vp9.get('fotogrammi_usciti')} "
                                f"fotogrammi, {vp9.get('disegni')} disegni, "
                                f"{CELLE}/{CELLE} celle — la catena "
                                "decodifica→tela→rilettura ESISTE su questo motore")
    else:
        fuori["P4"] = ("rosso", "VP9 NON arriva al pixel "
                                f"({vp9.get('celle_giuste')}/{CELLE} celle, "
                                f"{vp9.get('fotogrammi_usciti')} fotogrammi): "
                                "⛔ su HEVC questo giro non ha il diritto di "
                                "scrivere niente")

    # P3 — la distinzione: le letture di A NON devono classificarsi anche su B.
    #      Si guarda su ogni sequenza che abbia dipinto, e basta una che
    #      confonda i due pattern per bocciare.
    confusi, esaminati = [], 0
    for d in righe:
        if d.get("tipo") != "SEQUENZA" or not d.get("disegni"):
            continue
        cl = d.get("contro_pattern") or {}
        if "corrette" not in cl:
            continue
        esaminati += 1
        if cl["corrette"] == CELLE and d.get("celle_giuste") == CELLE:
            confusi.append(d.get("prova"))
    if esaminati == 0:
        fuori["P3"] = ("assente", "nessuna sequenza ha dipinto: la distinzione "
                                  "fra i due pattern non e' stata messa alla prova")
    elif confusi:
        fuori["P3"] = ("rosso", "gli stessi pixel si classificano bene su TUTT'E "
                                f"DUE i pattern ({', '.join(confusi)}): il banco "
                                "non distingue l'immagine giusta da quella "
                                "sbagliata")
    else:
        fuori["P3"] = ("verde", f"su {esaminati} sequenze dipinte, i pixel di un "
                                "pattern non si classificano mai sull'altro")

    # ⛔⭐ P5 — «l'immagine dipinta e' quella CHIESTA», ed e' nato da un buco
    #    trovato certificando: il guasto «scambio» — dare i byte del pattern B
    #    dicendo di aver chiesto A — **non faceva virare niente**.  P3 chiede
    #    se il classificatore sa distinguere; questo chiede se il flusso
    #    arrivato e' quello che si e' chiesto, che e' un'altra domanda.
    #    ⚠ Senza, un banco che pescasse la sequenza sbagliata (un nome di file
    #      scambiato, una cache) avrebbe scritto «HEVC arriva al pixel» avendo
    #      dipinto un'altra immagine — e i pixel sarebbero stati giusti per
    #      qualcun altro.
    sbagliate = []
    guardate = 0
    for d in righe:
        if d.get("tipo") != "SEQUENZA" or not d.get("disegni"):
            continue
        cl = d.get("contro_pattern") or {}
        if "corrette" not in cl:
            continue
        guardate += 1
        if cl["corrette"] > (d.get("celle_giuste") or 0):
            sbagliate.append(f"{d.get('prova')} ({d.get('celle_giuste')}/{CELLE} "
                             f"sul suo pattern, {cl['corrette']}/{CELLE} sull'altro)")
    if guardate == 0:
        fuori["P5"] = ("assente", "nessuna sequenza ha dipinto: non si e' potuto "
                                  "controllare che l'immagine fosse quella chiesta")
    elif sbagliate:
        fuori["P5"] = ("rosso", "l'immagine dipinta somiglia all'ALTRO pattern "
                                f"piu' che al suo: {'; '.join(sbagliate)} — al "
                                "decodificatore sono arrivati byte diversi da "
                                "quelli che il banco crede di avergli dato")
    else:
        fuori["P5"] = ("verde", f"su {guardate} sequenze dipinte, l'immagine e' "
                                "sempre piu' vicina al pattern chiesto che all'altro")
    # ⛔⭐ P6 — «LO ZERO HA SEMPRE UNA CAUSA».  `REVIEWER.md` §1 punto 4 e
    #    `LEZIONI.md` §1.9: *una misura che puo' dire «zero» deve poter dire
    #    anche «sono fallito»*.  Prima che questo controllo esistesse, quella
    #    regola era **scritta nel banco e non provata dal banco** — e la
    #    differenza e' precisamente quella fra una regola e una speranza.
    #
    # ⚠ Il caso concreto che chiude: una sequenza che non dipinge e non
    #   dichiara nessun errore.  Chi legge il registro vede `disegni: 0` e ha
    #   due letture — «il motore l'ha rifiutata» e «il banco non gliel'ha
    #   nemmeno data» — che qui hanno lo stesso aspetto.
    mute = []
    zeri = 0
    for d in righe:
        if d.get("tipo") != "SEQUENZA":
            continue
        if (d.get("disegni") or 0) > 0:
            continue
        zeri += 1
        ha_causa = bool(d.get("errore_configure")) or bool(d.get("errori_decode")) \
            or bool(d.get("errore_callback")) or bool(d.get("errore_lettura")) \
            or d.get("esito") == "SEQUENZA_ASSENTE"
        if not ha_causa:
            mute.append(d.get("prova"))
    # ⛔⭐ P9 — IL CONTROLLO POSITIVO DEL PERCORSO DEL PRODOTTO, e c'e' solo nei
    #    giri puntati sul prodotto (`02-pagina-prodotto.html`).
    #
    # P4 dice «questo MOTORE porta un video fino al pixel», e lo dice
    # decodificando VP9 nella pagina del banco — perche' `RCP.md` §4.3 non ha
    # VP9 e il prodotto non lo sa fare per decisione.  ⛔ Da solo non basta piu':
    # con P4 verde e HEVC a zero, «HEVC non arriva su questo motore» e «la
    # catena del PRODOTTO non funziona» hanno ancora lo stesso aspetto.
    #
    # ⇒ P9 chiude quel buco con AV1 — che `[M]` 12 agosto 2026 arriva al pixel
    #   in tutte e quattro le caselle, con GPU e senza — fatto passare per
    #   l'oggetto `Schermo` del prodotto: intestazione di §6.2, regole di §5.2,
    #   `VideoDecoder` e tela del prodotto.  Se P9 e' verde, un «no» su HEVC e'
    #   di HEVC; se P9 e' rosso mentre P4 e' verde, il «no» e' del prodotto.
    prodotto = [d for d in righe if d.get("bersaglio") == "prodotto"]
    if prodotto:
        av1 = [d for d in prodotto
               if d.get("tipo") == "SEQUENZA" and "-av1-" in (d.get("prova") or "")]
        buone = [d for d in av1 if d.get("celle_giuste") == CELLE]
        if not av1:
            fuori["P9"] = ("assente", "nessuna sequenza AV1 e' stata data al "
                                      "prodotto")
        elif buone:
            fuori["P9"] = ("verde", f"AV1 arriva al pixel ATTRAVERSO IL "
                                    f"PRODOTTO: {len(buone)} sequenze su "
                                    f"{len(av1)} a {CELLE}/{CELLE} celle — la "
                                    "catena intestazione→regole→decodifica→tela "
                                    "del prodotto ESISTE")
        else:
            fuori["P9"] = ("rosso", "nessuna sequenza AV1 arriva al pixel "
                                    "attraverso il prodotto: ⛔ il «no» non e' "
                                    "di HEVC, e' della catena del prodotto — su "
                                    "HEVC questo giro non scrive niente")

    if zeri == 0:
        fuori["P6"] = ("verde", "nessuna sequenza e' rimasta a zero disegni: "
                                "non c'e' nessuno zero da spiegare")
    elif mute:
        fuori["P6"] = ("rosso", f"{len(mute)} sequenze non hanno dipinto e non "
                                f"dicono perche' ({', '.join(mute)}): «zero» e "
                                "«sono fallito» hanno lo stesso aspetto")
    else:
        fuori["P6"] = ("verde", f"tutti i {zeri} zeri hanno una causa scritta "
                                "accanto: «zero» e «sono fallito» sono distinti")
    return fuori


def stato_hevc(misure):
    """⛔ NON e' un controllo del banco: e' LA MISURA, e sta fuori da `valido`.

    Un banco che uscisse rosso perche' un motore non decodifica HEVC
    insegnerebbe a ignorare il rosso (`DECISIONI.md` §2.7: l'altezza la mette
    il client, e un «no» e' un fatto da dichiarare, non un difetto nostro).
    Serve pero' alla certificazione, che deve poter pretendere che un guasto
    innestato faccia sparire i pixel."""
    bersagli = [m for m in misure if "bit-" in (m["prova"] or "")]
    if not bersagli:
        return "assente"
    return "arriva" if any(m["stato"] == "PIXEL-GIUSTI" for m in bersagli) \
           else "non-arriva"


def misura(righe):
    """La MISURA: che cosa arriva al pixel, sequenza per sequenza."""
    fuori = []
    for d in righe:
        if d.get("tipo") != "SEQUENZA":
            continue
        prova = d.get("prova", "")
        dipinto = (d.get("disegni") or 0) > 0
        giuste = d.get("celle_giuste")
        if d.get("errore_configure"):
            stato = "configure-rifiutata"
        elif d.get("errori_decode"):
            stato = "decode-fallita"
        elif not dipinto:
            stato = "nessun-disegno"
        elif giuste == CELLE:
            stato = "PIXEL-GIUSTI"
        else:
            stato = "pixel-sbagliati"
        prof = d.get("profondita_fotogramma") or {}
        fuori.append({
            "prova": prova, "stato": stato,
            "codec": d.get("codec_chiesto"),
            "descrizione": d.get("con_descrizione"),
            "pezzi": f"{d.get('pezzi_dati')}/{d.get('pezzi_attesi')}",
            "fotogrammi": d.get("fotogrammi_usciti"),
            "disegni": d.get("disegni"),
            "celle": f"{giuste}/{d.get('celle_attese')}",
            "formato": prof.get("formato"),
            "luma_massimo": prof.get("luma_massimo"),
            "api": (d.get("api_dichiarata") or {}).get("supported"),
            "errore": d.get("errore_configure")
                      or (d.get("errori_decode") or [None])[0],
            "png": d.get("png"),
            "ms": d.get("ms"),
        })
    return fuori


def stampa(giro, righe):
    print(f"\n\033[1m== giro {giro}\033[0m")
    if not righe:
        print(f"    {ROSSO}  nessuna riga nel registro per questo giro: "
              "il browser non ha misurato niente")
        return {"valido": False, "controlli": {}, "misure": []}

    amb = prima(righe, "AMBIENTE") or {}
    fin = prima(righe, "FINITO") or {}
    motore = (righe[0].get("motore") or "")[:100]
    guasto = righe[0].get("guasto") or ""
    print(f"    motore: {motore}")
    print(f"    scena:  {righe[0].get('scena') or 'NON DICHIARATA'}")
    if guasto:
        print(f"    ⚠ GUASTO INNESTATO: {guasto}")
    print(f"    WebCodecs: {amb.get('webcodecs')} · contesto sicuro: "
          f"{amb.get('contesto_sicuro')} · fine: {fin.get('esito') or 'MANCA'}")

    if fin.get("esito") == "SENZA_WEBCODECS":
        print(f"    {GIALLO}  questo motore non ha WebCodecs: non c'e' niente "
              "da misurare, e non e' un difetto del banco")
        return {"valido": False, "senza_webcodecs": True,
                "controlli": {}, "misure": []}
    if not fin:
        print(f"    {ROSSO}  la riga FINITO non c'e': il giro si e' interrotto, "
              "e le righe qui sotto sono un giro a meta'")

    c = controlli(righe)
    bersaglio = righe[0].get("bersaglio") or "il banco"
    print(f"\n    -- i controlli che rendono valido il banco  (bersaglio: "
          f"\033[1m{bersaglio}\033[0m)")
    # ⚠ P9 esiste solo nei giri puntati sul prodotto: elencarlo sempre lo
    #   farebbe leggere come «non eseguito» dove non ha senso.
    quali = ["P1", "P2", "P3", "P4", "P5", "P6"] + (["P9"] if "P9" in c else [])
    for nome in quali:
        esito, frase = c.get(nome, ("assente", "non eseguito"))
        segno = {"verde": VERDE, "rosso": ROSSO}.get(esito, GIALLO)
        print(f"      {segno}  {nome}: {frase}")
    valido = all(c.get(n, ("assente",))[0] == "verde" for n in quali)

    m = misura(righe)
    print("\n    -- la misura: che cosa arriva al PIXEL")
    print(f"      {'prova':34s} {'stato':20s} {'pezzi':7s} {'fot':4s} "
          f"{'celle':6s} {'formato':10s} api")
    for r in m:
        segno = {"PIXEL-GIUSTI": "\033[1;32m", "pixel-sbagliati": "\033[1;33m"}.get(
            r["stato"], "\033[1;31m")
        print(f"      {r['prova']:34s} {segno}{r['stato']:20s}\033[0m "
              f"{r['pezzi']:7s} {str(r['fotogrammi']):4s} {r['celle']:6s} "
              f"{str(r['formato']):10s} {r['api']}")
        if r["errore"]:
            print(f"          ⛔ {r['errore'][:150]}")

    s = prima(righe, "SONDAGGIO")
    if s:
        # ⛔ Si stampa PER DIRE DI CHE COSA E' IL «NO», e la riga di
        #    avvertimento sotto non e' un ornamento: senza, questa tabella
        #    diventa la prova che non e'.
        print("\n    -- il sondaggio: che cosa DICHIARA l'API (⛔ non e' una misura)")
        hevc_si = [r for r in s["righe"]
                   if r["codec"].startswith(("hev1", "hvc1"))
                   and r.get("isConfigSupported") is True]
        altri_si = [r for r in s["righe"]
                    if not r["codec"].startswith(("hev1", "hvc1"))
                    and r.get("isConfigSupported") is True]
        for r in s["righe"]:
            mc = r.get("mediaCapabilities")
            pe = mc.get("powerEfficient") if isinstance(mc, dict) else mc
            print(f"      {r['codec']:20s} isConfigSupported="
                  f"{str(r.get('isConfigSupported')):6s} powerEfficient={pe} "
                  f"· {r['perche']}")
        # ⛔⭐ LA CONTRADDIZIONE FRA API, E VALE PIU' DI TUTTA LA TABELLA.
        #    `[M]` 12 agosto 2026 su Firefox 140 ESR: per HEVC
        #    `mediaCapabilities.decodingInfo()` risponde `supported: true,
        #    smooth: true, powerEfficient: true` e `canPlayType` risponde
        #    «probably» — mentre `isConfigSupported` dice **false** e ogni
        #    decodifica muore con `NotSupportedError`.
        #    ⇒ Una pagina che scegliesse il codec chiedendo a `mediaCapabilities`
        #      sceglierebbe HEVC su Firefox e non dipingerebbe niente.  E' la
        #      forma d'errore **E1** — necessario preso per sufficiente — con
        #      TRE testimoni concordi e sbagliati.
        bugiardi = []
        for r in s["righe"]:
            mc = r.get("mediaCapabilities")
            dice_si = isinstance(mc, dict) and mc.get("supported") is True
            play = r.get("canPlayType") in ("probably", "maybe")
            if r.get("isConfigSupported") is not True and (dice_si or play):
                bugiardi.append(r["codec"])
        if bugiardi:
            print(f"      {ROSSO}  ⛔⭐ CONTRADDIZIONE FRA API su "
                  f"{len(bugiardi)} codec: {bugiardi}")
            print("          `mediaCapabilities`/`canPlayType` dicono SI', "
                  "`isConfigSupported` dice NO.")
            print("          ⇒ Una pagina che scegliesse il codec da quelle due "
                  "sceglierebbe un codec")
            print("            che questo browser NON decodifica, e non "
                  "dipingerebbe niente (forma E1).")

        if not hevc_si and altri_si:
            print(f"      {GIALLO}  ⛔ NESSUNA stringa HEVC accettata, mentre "
                  f"{len(altri_si)} non-HEVC lo sono: il «no» NON e' della "
                  "nostra stringa di codec — e' di HEVC su questo motore IN "
                  "QUESTA SCENA")
        elif hevc_si:
            print(f"      -- stringhe HEVC accettate dall'API: "
                  f"{[r['codec'] for r in hevc_si]}")

    # ⛔ La cucitura con F2.4: due lettori indipendenti degli stessi 28 byte.
    #    Un disaccordo qui non e' un difetto del banco — e' un fraintendimento
    #    della specifica trovato da due letture separate, che e' il pezzo di
    #    arbitro che il progetto ha comprato apposta (`PIANO.md` §0.4).
    ints = prima(righe, "INTESTAZIONE")
    if ints:
        segno = VERDE if (ints.get("discordi") == 0
                          and ints.get("senza_intestazione") == 0) else ROSSO
        print(f"\n    -- l'intestazione di RCP §6.2 (lettore di F2.5, "
              f"indipendente da quello di F2.4)")
        print(f"      {segno}  {ints.get('pezzi')} pezzi, "
              f"{ints.get('discordi')} in disaccordo, "
              f"{ints.get('senza_intestazione')} senza intestazione")
        for r in (ints.get("righe") or []):
            if r.get("guai"):
                print(f"          ⛔ pezzo {r['pezzo']}: {'; '.join(r['guai'])}")

    hevc = stato_hevc(m)
    print(f"\n    -- HEVC al pixel: \033[1m{hevc.upper()}\033[0m  "
          "(⛔ e' LA MISURA, non un controllo del banco: un «non-arriva» non e' "
          "un rosso — DECISIONI.md §2.7)")

    if not valido:
        print(f"\n    {ROSSO}  \033[1mBANCO NON VALIDO\033[0m — ⛔ le righe qui "
              "sopra su HEVC NON si scrivono da nessuna parte come misure.")
    else:
        print(f"\n    {VERDE}  banco valido: sa dire di si' (P1, P4), sa dire di "
              "no (P2), distingue (P3), dipinge quel che ha chiesto (P5) "
              "e non tace sugli zeri (P6)")
    controlli_e_misura = {k: v[0] for k, v in c.items()}
    controlli_e_misura["HEVC"] = hevc
    return {"valido": valido, "controlli": controlli_e_misura, "misure": m}


def principale(argomenti):
    pretese = []
    giri = []
    i = 0
    while i < len(argomenti):
        if argomenti[i] == "--pretendi":
            pretese.append(argomenti[i + 1])
            i += 2
            continue
        giri.append(argomenti[i])
        i += 1
    if not giri:
        print(__doc__)
        return 2

    per_giro = carica(giri)
    esiti = {}
    for g in giri:
        esiti[g] = stampa(g, per_giro.get(g, []))

    if pretese:
        # ⛔ La certificazione: si dichiara PRIMA che cosa deve virare, e qui
        #    si verifica.  Un guasto innestato che non fa virare niente e' un
        #    controllo che non controlla (LEZIONI.md §1.3).
        print("\n\033[1m-- le pretese di questo giro (la certificazione)\033[0m")
        mancate = 0
        for p in pretese:
            nome, _, atteso = p.partition("=")
            visti = {e["controlli"].get(nome, "assente") for e in esiti.values()
                     if not e.get("senza_webcodecs")}
            if not visti:
                print(f"      {ROSSO}  {nome}: nessun motore ha prodotto questo "
                      "controllo")
                mancate += 1
            elif visti == {atteso}:
                print(f"      {VERDE}  {nome} = {atteso}, come atteso")
            else:
                print(f"      {ROSSO}  {nome}: atteso «{atteso}», trovato "
                      f"{sorted(visti)}")
                mancate += 1
        return 1 if mancate else 0

    # ⛔ L'uscita dice se il BANCO vale, non se HEVC funziona.  Vedi
    #    l'intestazione: le due domande sono diverse.
    validi = [g for g, e in esiti.items() if e["valido"]]
    senza = [g for g, e in esiti.items() if e.get("senza_webcodecs")]
    print(f"\n    -- giri con banco valido: {len(validi)} su "
          f"{len(giri) - len(senza)} che hanno WebCodecs "
          f"({len(senza)} senza WebCodecs, non contati)")
    if not validi:
        print(f"    {ROSSO}  nessun giro valido: non si pubblica nessun "
              "verdetto su HEVC")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(principale(sys.argv[1:]))
