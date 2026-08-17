#!/usr/bin/env python3
"""
07-b43 — il giudizio dell'audio VERO: quello che ESCE DALLA SESSIONE.

===========================================================================
⛔ PERCHE' ESISTE, DATO CHE `07-b42-giudice.py` C'E' GIA'
===========================================================================

⭐ **Lo strumento di misura resta uno solo, e resta quello certificato**: le
   due funzioni che *ascoltano* — `giudica()` (Goertzel a passo 1 Hz, RMS,
   purezza) e `pcm_campioni()` (s16 little-endian interlacciato) — **si
   importano** da `07-b42-giudice.py`, non si riscrivono.  E' `CODER.md` §4.1,
   e qui pesa il doppio: quelle due funzioni sono le uniche di questa fase
   che abbiano un controllo positivo alle spalle (`07-b40`, **sei casi su
   sei**, `fasi/07-audio-e-appunti.md` §2.1).  Riscriverle vorrebbe dire
   buttare la certificazione e ricominciare.

⛔ **Quel che 07-b42 non sa fare, e serve qui — sono quattro cose, e nessuna
   e' un dettaglio:**

  1. **l'atteso SILENZIO.**  07-b42 dichiara rosso ogni `rms < 0,05`: e'
     giusto per il tono di prova, che deve esserci sempre.  Qui il silenzio
     e' una delle scene, ⭐ ed e' la scena che il **muto** deve produrre.  Un
     giudice che non sa dire *«qui il silenzio e' l'esito giusto»* non puo'
     giudicare il cursore del volume;
  2. **il confronto FRA giri.**  L'atteso del giro col volume al 25 % non e'
     un numero scritto a mano: e' **l'RMS del giro sano moltiplicato per il
     guadagno lineare letto nel grafo di PipeWire**.  Nessun giudice che
     guardi un file per volta puo' calcolarlo;
  3. ⛔⛔ **la disciplina della finestra**, ed e' la scoperta di oggi — vedi
     il riquadro qui sotto: la **purezza dipende da quanti campioni le si
     danno**, e una finestra che non sia un numero **intero di secondi**
     fa dare al giudice certificato un rosso falso;
  4. **l'atteso si dichiara PRIMA** (`06-b38-tela.sh`, regola B0.4): ogni giro
     porta il suo `.atteso.json`, scritto dal lanciatore **prima** di
     allestire la scena.  Questo programma non decide che cosa aspettarsi:
     lo **legge**, e dice se combacia.

===========================================================================
⛔⛔ LA FINESTRA DEVE ESSERE UN NUMERO INTERO DI SECONDI — `[M]` 17 ago 2026
===========================================================================

`giudica()` misura la purezza come *«quanta energia sta nella riga
dominante»*, sommando su righe distanti **1 Hz**.  Due righe a 1 Hz di
distanza sono ortogonali **solo** su una finestra di 48 000 campioni (o un
suo multiplo): sotto, l'energia del tono si spalma sulle righe vicine e la
purezza **crolla senza che il segnale sia cambiato**.

`[M]` misurato sul portatile con lo **stesso** file registrato (tono 440 Hz
puro, ampiezza 0,5, catturato dal monitor di un sink `support.null-audio-sink`):

    | finestra | campioni | hz  | rms    | purezza |
    |----------|----------|-----|--------|---------|
    | 0,25 s   |  12 000  | 440 | 0,3535 | **0,2501** |
    | 0,50 s   |  24 000  | 440 | 0,3535 | **0,5001** |
    | 1,00 s   |  48 000  | 440 | 0,3535 | ⭐ **1,000** |
    | 1,50 s   |  72 000  | 440 | 0,3535 | 0,900 |
    | 2,00 s   |  96 000  | 440 | 0,3535 | ⭐ **1,000** |

⛔ **La soglia di 07-b42 e' 0,80.**  Un banco che avesse analizzato mezzo
   secondo avrebbe letto **0,50** e scritto *«non e' un tono, e' rumore — il
   difetto di v1»* su un tono perfetto: un rosso su codice giusto, che
   `LEZIONI.md` §2.3 dice costare quanto un verde su codice sbagliato.
   ⚠ E la forma e' esattamente quella di `LEZIONI.md` §1.2, il riquadro:
   *«in quale UNITA' gliel'ho fatto produrre?»* — qui l'unita' e' la
   **lunghezza della finestra**, e non si vede finche' non la si cambia.

⇒ Questo programma **rifiuta** una finestra che non sia un intero di secondi,
  e taglia i campioni a un multiplo esatto di 48 000 prendendoli **dalla
  coda** (che e' anche il regime, `CODER.md` §3.5).

===========================================================================
COME SI USA
===========================================================================

    python3 07-b43-giudizio.py <cartella> [--giri 1-sano,2-silenzio,...]

Per ogni giro `N` la cartella deve contenere:

    N.atteso.json   scritto dal lanciatore PRIMA della scena (l'atteso)
    N.stato.json    scritto dal lanciatore DOPO la scena (che cosa c'era)
    N.jsonl         i blocchi raccolti da `01-b3-cliente.py --audio-scrivi`

I codici d'uscita, e sono quattro perche' i casi sono quattro:

    0  ⭐ ogni giro ha fatto quel che era dichiarato prima
    1  ⛔ IL PRODOTTO e' rosso: un giro di misura non combacia
    2  ⚠  NON HO MISURATO: file mancanti, zero blocchi, codec non PCM
          (`CODER.md` §3.10 — non e' uno zero, e' un'assenza)
    3  ⛔ IL BANCO E' CIECO: un giro di controllo NON ha prodotto il rosso
          che doveva produrre.  ⚠ E' il piu' grave dei quattro, perche' un
          banco cieco fa passare per verde tutto quel che gli si mette
          davanti (`LEZIONI.md` §2.2)
"""
import argparse
import base64
import importlib.util
import json
import os
import sys

FREQUENZA = 48000
BLOCCO_US_PCM = 5000  # §5.3: un blocco PCM ogni 5 ms
CODEC_PCM = 2

# ── Le tolleranze, dichiarate qui e non sparse nel codice ──────────────────
#
# ⚠ Sono tre, e ognuna ha una ragione diversa:
TOLLERANZA_HZ = 2          # come 07-b42: la stessa riga dominante
PUREZZA_MINIMA = 0.80      # come 07-b42, certificata su sei casi
SILENZIO_RMS = 0.01        # `[M]` il silenzio vero di un null-sink da' 0,0000
                           #     esatto: 0,01 e' due ordini di grandezza sopra
FATTORE_ROSSO = 2.0        # ⛔ oltre un fattore 2 dall'atteso e' rosso
SCARTO_GUARDA = 0.10       # ⚠ oltre il 10 % si segnala, non si boccia: la
                           #   catena sink→monitor→PCM non ha guadagni, quindi
                           #   dovrebbe combaciare all'1 % — ma una banda
                           #   stretta su una catena mai misurata produce rossi
                           #   falsi, e un rosso falso costa quanto un verde
                           #   falso (`LEZIONI.md` §2.3)
VOLUME_NON_ARRIVA = 0.80   # ⛔ se il guadagno chiesto e' <= 0,5 e l'RMS resta
                           #   sopra l'80 % di quello a volume pieno, il volume
                           #   NON sta arrivando al monitor: e' §kde §10.5


def carica_07b42():
    """⭐ Il giudice certificato, importato — non ricopiato.

    ⛔ Il nome del file non e' un identificatore Python valido (comincia per
       cifra e porta trattini), quindi la strada normale dell'`import` non c'e'.
       ⚠ Ricopiare le due funzioni sarebbe stato piu' corto **e avrebbe
         perso la certificazione**: due copie divergono, e quella che diverge
         e' sempre quella che nessuno ha esercitato.
    """
    qui = os.path.dirname(os.path.abspath(__file__))
    percorso = os.path.join(qui, "07-b42-giudice.py")
    if not os.path.exists(percorso):
        print(f"⛔ non trovo il giudice certificato in «{percorso}».")
        print("   ⚠ Questo non e' «l'audio non va»: e' «non ho lo strumento».")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location("giudice_07b42", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


G42 = carica_07b42()


# ══════════════════════════════════════════════════════════════════════════
# La lettura dei blocchi, e la finestra
# ══════════════════════════════════════════════════════════════════════════
def leggi_blocchi(percorso):
    """I blocchi, oppure il MOTIVO per cui non ce ne sono.

    ⛔ `CODER.md` §3.10: «vuoto» e «proibito» hanno lo stesso aspetto, e qui
       ce n'e' un terzo — «il file non c'e' perche' il cliente non e' mai
       arrivato in fondo».  Tre cause, tre messaggi.
    """
    if not os.path.exists(percorso):
        return None, (f"il file «{os.path.basename(percorso)}» NON ESISTE: il "
                      f"cliente non ha scritto niente (non e' silenzio)")
    try:
        with open(percorso) as f:
            righe = [r.strip() for r in f if r.strip()]
    except OSError as e:
        return None, f"il file non si legge: {e}"
    if not righe:
        return None, ("il file c'e' ed e' VUOTO: zero datagram di audio "
                      "ricevuti.  ⚠ E' «non e' arrivato niente», non «e' "
                      "arrivato silenzio»: i due hanno cure diverse")
    try:
        return [json.loads(r) for r in righe], None
    except json.JSONDecodeError as e:
        return None, f"il file e' rotto alla riga {e.lineno}: {e}"


def finestra_di_coda(blocchi, secondi):
    """Gli ultimi `secondi` INTERI di presa, scelti sull'orologio del SERVER.

    ⭐ Si prende la CODA e non la testa per due ragioni, e tutt'e due sono
       regole scritte:
       · `CODER.md` §3.5 — «un campione preso all'avvio non dice niente del
         regime»: la testa della presa e' il tempo in cui il cliente si
         attacca e la scena non suona ancora;
       · e la scena, in questo banco, **comincia dopo** il cliente: il tono
         parte quando il grafo di PipeWire dice che e' collegato, non quando
         un `sleep` e' scaduto (`LEZIONI.md` §2.3-quinquies).

    ⛔ Il taglio si fa sugli `istante` — l'orologio del server, §6.3 — e non
       sull'ora di parete di chi legge: sono due orologi, e il secondo non ha
       niente a che vedere col primo.
    """
    ultimo = blocchi[-1]["istante"]
    soglia = ultimo - int(secondi * 1_000_000)
    return [b for b in blocchi if b["istante"] > soglia]


def campioni_dai_blocchi(blocchi):
    campioni = []
    for b in blocchi:
        campioni.extend(G42.pcm_campioni(base64.b64decode(b["byte"])))
    return campioni


# ══════════════════════════════════════════════════════════════════════════
# Il giudizio di UN giro
# ══════════════════════════════════════════════════════════════════════════
def giudica_giro(cartella, nome, riferimenti):
    """Ritorna un dizionario: che cosa era atteso, che cosa si e' visto, e se
    combacia.  ⛔ Non decide l'atteso: lo legge dal file scritto PRIMA."""
    esito = {"nome": nome}

    percorso_a = os.path.join(cartella, f"{nome}.atteso.json")
    if not os.path.exists(percorso_a):
        esito["stato"] = "NON MISURATO"
        esito["perche"] = f"manca «{nome}.atteso.json»: nessuno ha dichiarato " \
                          f"l'atteso, quindi non c'e' niente da confrontare"
        return esito
    with open(percorso_a) as f:
        atteso = json.load(f)
    esito["atteso"] = atteso

    percorso_s = os.path.join(cartella, f"{nome}.stato.json")
    stato = {}
    if os.path.exists(percorso_s):
        with open(percorso_s) as f:
            stato = json.load(f)
    esito["stato_scena"] = stato

    # ── 1. la scena si DICHIARA accanto al numero — `LEZIONI.md` §2.0 ──────
    #
    # ⛔ «Un banco che risponde NO deve scrivere accanto alla risposta la
    #    scena da cui l'ha data.»  Qui la scena e' il grafo di PipeWire: che
    #    sink c'era, con che guadagno, con quanti legami in ingresso.
    if not stato:
        esito["stato"] = "NON MISURATO"
        esito["perche"] = (f"manca «{nome}.stato.json»: la scena non e' stata "
                           f"registrata, e un numero senza la sua scena non e' "
                           f"una misura (`LEZIONI.md` §2.0)")
        return esito

    # ── 2. i blocchi ──────────────────────────────────────────────────────
    blocchi, guasto = leggi_blocchi(os.path.join(cartella, f"{nome}.jsonl"))
    if blocchi is None:
        esito["stato"] = "NON MISURATO"
        esito["perche"] = guasto
        return esito

    codec = blocchi[0]["codec"]
    if any(b["codec"] != codec for b in blocchi):
        esito["stato"] = "NON MISURATO"
        esito["perche"] = "il codec CAMBIA a meta' presa: §4.3 lo negozia una " \
                          "volta sola, e questo e' un difetto suo, non del suono"
        return esito
    if codec != CODEC_PCM:
        # ⛔ `07-b42` lo dice e vale identico qui: i pacchetti Opus li giudica
        #    il BROWSER, che ha il decodificatore dell'utente.  Giudicarli con
        #    un altro decodificatore e' la forma d'errore E10.
        esito["stato"] = "NON MISURATO"
        esito["perche"] = (f"codec {codec} (Opus): qui non si giudica il "
                           f"segnale — il lanciatore deve chiedere «--audio-"
                           f"codec pcm», che §4.3 rende obbligatorio ai due capi")
        return esito

    # ── 3. la finestra, e il suo denominatore ─────────────────────────────
    #
    # ⛔ `LEZIONI.md` §1.9 regola 4: «una misura DEVE dichiarare su che cosa ha
    #    guardato — il denominatore, non solo il risultato».
    secondi = atteso.get("finestra_s", 2)
    if secondi != int(secondi) or secondi < 1:
        esito["stato"] = "BANCO ROTTO"
        esito["perche"] = (f"finestra di {secondi} s: deve essere un INTERO di "
                           f"secondi >= 1, o la purezza crolla da sola — vedi "
                           f"la tabella in cima a questo file")
        return esito
    secondi = int(secondi)

    coda = finestra_di_coda(blocchi, secondi)
    campioni = campioni_dai_blocchi(coda)
    attesi_blocchi = secondi * (1_000_000 // BLOCCO_US_PCM)
    attesi_campioni = secondi * FREQUENZA

    # ⛔ E si TAGLIA a un multiplo esatto di 48 000, dalla coda.
    intero = (len(campioni) // FREQUENZA) * FREQUENZA
    if intero == 0:
        esito["stato"] = "NON MISURATO"
        esito["perche"] = (f"{len(campioni)} campioni nella finestra di "
                           f"{secondi} s: meno di un secondo intero, e sotto "
                           f"il secondo la purezza non significa niente")
        return esito
    campioni = campioni[-intero:]

    d = esito["denominatore"] = {
        "blocchi_totali": len(blocchi),
        "blocchi_nella_finestra": len(coda),
        "blocchi_attesi": attesi_blocchi,
        "campioni_giudicati": len(campioni),
        "campioni_attesi": attesi_campioni,
        "secondi_giudicati": len(campioni) // FREQUENZA,
    }

    # ── 4. il RITMO, riferito e non giudicato ─────────────────────────────
    #
    # ⚠ `fasi/07-audio-e-appunti.md` §8, e va detto invece di taciuto: «il tono
    #   di prova non prova il ritmo dell'audio VERO — la sua cadenza gliela da'
    #   il battito di QUIC, quella dell'audio vero la dara' PipeWire.  Sono due
    #   orologi diversi».  ⇒ Qui il passo si STAMPA con il suo minimo e il suo
    #   massimo, e NON produce un rosso: il numero che questo banco deve
    #   difendere e' il segnale.  Il ritmo dell'audio vero vuole una soglia
    #   posta da chi l'ha misurato, e nessuno l'ha ancora misurato.
    passi = [coda[i]["istante"] - coda[i - 1]["istante"]
             for i in range(1, len(coda))]
    esito["ritmo"] = {
        "passo_atteso_us": BLOCCO_US_PCM,
        "minimo": min(passi) if passi else None,
        "massimo": max(passi) if passi else None,
        "fuori_passo": sum(1 for d in passi if d != BLOCCO_US_PCM),
        "giudicato": False,
    }

    # ── 5. il SEGNALE, con lo strumento certificato ───────────────────────
    g = G42.giudica(campioni)
    esito["misura"] = g

    # ── 6. l'atteso in numeri, e da dove viene ────────────────────────────
    #
    # ⭐ L'RMS atteso di un giro col volume abbassato NON e' un numero scritto
    #    a mano: e' quello del giro sano moltiplicato per il **guadagno lineare
    #    letto nel grafo** (`Props.channelVolumes`).  ⛔ E' l'unico modo di non
    #    sbagliare la curva: `wpctl set-volume 0.25` scrive **0,015625** nel
    #    nodo — la curva cubica di PulseAudio, 0,25³ — e chi si aspettasse un
    #    quarto del segnale darebbe rosso a un prodotto sano.
    #    `[M]` 17 ago 2026: 0,3535 × 0,015625 = 0,005523, misurato **0,0055**.
    guadagno = 1.0
    if stato.get("mute"):
        guadagno = 0.0
    cv = stato.get("channel_volumes")
    if isinstance(cv, list) and cv:
        guadagno = 0.0 if stato.get("mute") else float(cv[0])
    esito["guadagno_letto_dal_grafo"] = guadagno

    base = atteso.get("rms_base")
    if atteso.get("rms_da_giro"):
        rif = riferimenti.get(atteso["rms_da_giro"])
        if rif is None:
            esito["stato"] = "NON MISURATO"
            esito["perche"] = (f"l'atteso viene dal giro «{atteso['rms_da_giro']}», "
                               f"che non ha prodotto una misura: senza il "
                               f"riferimento questo giro non ha un atteso")
            return esito
        base = rif
    if base is None:
        base = 0.0
    rms_atteso = base * guadagno if atteso.get("scala_col_guadagno", True) else base
    esito["rms_atteso"] = round(rms_atteso, 6)

    # ── 7. IL VERDETTO SUL SEGNALE ────────────────────────────────────────
    rossi = []
    rms = g.get("rms", 0.0)

    if rms_atteso < SILENZIO_RMS:
        # L'atteso e' il silenzio, o quasi: il sink e' muto o quasi chiuso.
        if rms >= SILENZIO_RMS:
            rossi.append(("VOLUME-NON-ARRIVA" if guadagno <= 0.5 else "AMPIEZZA",
                          f"atteso rms {rms_atteso:.4f} (guadagno {guadagno}"
                          + (" e MUTO" if stato.get("mute") else "")
                          + f"), dal monitor arriva rms {rms}"))
    elif rms < SILENZIO_RMS:
        # ⛔ Quando non esce niente, la FREQUENZA non si giudica: `giudica()`
        #    scrive `hz 0` perche' non c'e' nessuna riga, e chiamarlo «la
        #    frequenza e' sbagliata» sarebbe accusare il codice di un difetto
        #    che non ha.  Il difetto qui e' uno solo, ed e' il silenzio.
        rossi.append(("SILENZIO",
                      f"rms {rms} su {d['campioni_giudicati']} campioni: dal "
                      f"monitor NON esce niente, mentre la scena dovrebbe "
                      f"suonare a {rms_atteso:.4f}.  ⚠ E i campioni ci sono: "
                      f"questo e' silenzio MISURATO, non «non ho misurato»"))
    else:
        if abs(g.get("hz", 0) - atteso.get("hz", 440)) > TOLLERANZA_HZ:
            rossi.append(("FREQUENZA",
                          f"la riga dominante e' a {g.get('hz')} Hz e non a "
                          f"{atteso.get('hz', 440)}: o la sessione suona "
                          f"un'altra cosa, o le frequenze di campionamento dei "
                          f"due capi non combaciano (§5.3 impone 48 000)"))
        if not (rms_atteso / FATTORE_ROSSO <= rms <= rms_atteso * FATTORE_ROSSO):
            rossi.append(("AMPIEZZA",
                          f"rms {rms} contro {rms_atteso:.4f} attesi: fuori "
                          f"dal fattore {FATTORE_ROSSO}"))
        p = g.get("purezza")
        if p is None or p < PUREZZA_MINIMA:
            rossi.append(("PUREZZA",
                          f"purezza {p} sotto {PUREZZA_MINIMA}: non e' un tono, "
                          f"e' rumore — ⛔ e' il difetto di v1, quello che un "
                          f"banco che conta i blocchi non vede"))

    # ⛔⛔ IL DIFETTO CHE VALE DA SOLO — `STUDI.md` §kde §10.5.
    #
    #    Senza `monitor.channel-volumes` il volume del sink NON arriva al
    #    monitor, **muto compreso**: chi cattura riceve il segnale a fondo
    #    scala qualunque cosa dica il cursore.  `[M]` la tabella dell'8 agosto:
    #    la colonna «non chiesta» e' PIATTA a 25,39 % da 100 % a 0 %.
    #
    #    ⇒ Questo controllo e' SEPARATO da quello dell'ampiezza, e ha un nome
    #      suo, perche' la cura e' una riga sola in `suono.c` e chi legge il
    #      rosso deve trovarla scritta.  `[M]` riprodotto sul portatile il 17
    #      agosto 2026 su due sink gemelli:
    #        mcv=true : 100 % -> 0,3535 · 25 % -> 0,0055 · muto -> 0,0000
    #        mcv=false: 100 % -> 0,3535 · 25 % -> 0,3535 · muto -> 0,3535
    rif_pieno = riferimenti.get(atteso.get("rms_da_giro") or "")
    if (guadagno <= 0.5 and rif_pieno and rms >= VOLUME_NON_ARRIVA * rif_pieno):
        rossi.append(("VOLUME-NON-ARRIVA",
                      f"il grafo dice guadagno {guadagno}"
                      + (" e MUTO" if stato.get("mute") else "")
                      + f", e dal monitor esce rms {rms} — cioe' il "
                      f"{100 * rms / rif_pieno:.0f} % di quel che usciva a "
                      f"volume pieno.  ⛔ Il volume non arriva al monitor: "
                      f"manca «monitor.channel-volumes» fra le proprieta' del "
                      f"sink (`STUDI.md` §kde §10.5, e l'ha aperta l'utente)"))

    # ⚠ Lo scarto piccolo si SEGNALA e non boccia: e' un'informazione, non un
    #   verdetto.  La catena sink→monitor→PCM non ha guadagni, quindi uno
    #   scarto del 10 % vuol dire che qualcuno ne ha uno.
    if rms_atteso >= SILENZIO_RMS and rms > 0:
        esito["scarto"] = round(rms / rms_atteso - 1.0, 4)
        esito["scarto_da_guardare"] = abs(esito["scarto"]) > SCARTO_GUARDA

    # ⚠ Un motivo si dice UNA volta: due righe con la stessa etichetta fanno
    #   sembrare due difetti quel che ne e' uno, e chi legge cerca il secondo.
    visti, unici = set(), []
    for m, t in rossi:
        if m not in visti:
            visti.add(m)
            unici.append((m, t))
    rossi = unici
    esito["rossi"] = [{"motivo": m, "testo": t} for m, t in rossi]
    esito["stato"] = "ROSSO" if rossi else "VERDE"
    return esito


# ══════════════════════════════════════════════════════════════════════════
# Il confronto con quel che era stato dichiarato PRIMA
# ══════════════════════════════════════════════════════════════════════════
def combacia(esito):
    """⛔ Il verdetto del BANCO non e' il verdetto del giro.

    Un giro di controllo positivo e' andato bene **quando ha dato rosso**: e'
    li' per questo.  ⇒ Si confronta lo stato osservato con
    `rosso_atteso` del file scritto prima, e il banco e' verde solo se
    combaciano tutti.
    """
    atteso = esito.get("atteso") or {}
    voluto = atteso.get("rosso_atteso")  # None = il giro deve essere VERDE
    stato = esito.get("stato")

    if stato in ("NON MISURATO", "BANCO ROTTO"):
        return False, stato
    motivi = [r["motivo"] for r in esito.get("rossi", [])]
    if voluto is None:
        return (stato == "VERDE"), ("come dichiarato" if stato == "VERDE"
                                    else f"doveva essere VERDE, e' ROSSO {motivi}")
    if stato != "ROSSO":
        return False, (f"⛔ IL BANCO E' CIECO: doveva vedere «{voluto}» e ha "
                       f"detto VERDE")
    if voluto not in motivi:
        return False, (f"⛔ ha dato rosso per {motivi}, ma il difetto innestato "
                       f"era «{voluto}»: il banco vede una cosa diversa da "
                       f"quella che gli e' stata messa davanti")
    return True, f"⭐ ha visto «{voluto}», come dichiarato prima"


def main():
    p = argparse.ArgumentParser(
        description="il giudizio dell'audio VERO della sessione")
    p.add_argument("cartella")
    p.add_argument("--giri", default="",
                   help="i nomi dei giri separati da virgola; senza, si "
                        "prendono tutti i «*.atteso.json» in ordine di nome")
    a = p.parse_args()

    if not os.path.isdir(a.cartella):
        print(f"⛔ «{a.cartella}» non e' una cartella.")
        return 2

    if a.giri:
        nomi = [x for x in a.giri.split(",") if x]
    else:
        nomi = sorted(f[:-len(".atteso.json")]
                      for f in os.listdir(a.cartella)
                      if f.endswith(".atteso.json"))
    if not nomi:
        print(f"⛔ NIENTE DA GIUDICARE: nessun «*.atteso.json» in {a.cartella}.")
        print("   ⚠ E non e' «l'audio non arriva»: e' «il banco non ha girato».")
        return 2

    print("=" * 74)
    print("== 07-b43 · IL SUONO DELLA SESSIONE, giudicato sul SEGNALE")
    print("=" * 74)

    riferimenti = {}   # nome del giro -> rms misurato, per i giri che ci si appoggiano
    esiti = []
    for nome in nomi:
        e = giudica_giro(a.cartella, nome, riferimenti)
        esiti.append(e)
        if e.get("misura", {}).get("esito") == "GIUDICATO":
            riferimenti[nome] = e["misura"]["rms"]

        at = e.get("atteso") or {}
        print(f"\n── {nome} ──────────────────────────────────────────")
        print(f"   scena     : {at.get('descrizione', '(non dichiarata)')}")
        print(f"   ⛔ ATTESO dichiarato PRIMA: {at.get('atteso_a_parole', '—')}")
        st = e.get("stato_scena") or {}
        if st:
            print(f"   grafo     : sink «{st.get('sink_nome')}» id {st.get('sink_id')}"
                  f" · monitor.channel-volumes={st.get('monitor_channel_volumes')}"
                  f" · channelVolumes={st.get('channel_volumes')}"
                  f" · mute={st.get('mute')}"
                  f" · legami in ingresso={st.get('legami_in_ingresso')}")
            print(f"   scena     : suona={st.get('scena_suona')}"
                  f" hz={st.get('tono_hz')}"
                  f" · il suonatore era vivo alla fine: {st.get('tono_vivo_alla_fine')}"
                  f" · cliente uscito {st.get('cliente_uscita')}")
        d = e.get("denominatore")
        if d:
            print(f"   guardato  : {d['campioni_giudicati']} campioni "
                  f"({d['secondi_giudicati']} s interi) da "
                  f"{d['blocchi_nella_finestra']} blocchi su "
                  f"{d['blocchi_attesi']} attesi · {d['blocchi_totali']} in tutto")
        r = e.get("ritmo")
        if r:
            print(f"   ritmo     : passo {r['minimo']}-{r['massimo']} µs "
                  f"(atteso {r['passo_atteso_us']}), fuori passo "
                  f"{r['fuori_passo']} ⚠ RIFERITO, non giudicato")
        if "misura" in e:
            m = e["misura"]
            print(f"   misurato  : {json.dumps(m, ensure_ascii=False)}")
            print(f"   atteso    : rms {e.get('rms_atteso')} "
                  f"(guadagno letto dal grafo: {e.get('guadagno_letto_dal_grafo')})")
            if e.get("scarto") is not None:
                segno = "⚠ " if e.get("scarto_da_guardare") else "  "
                print(f"   {segno}scarto : {e['scarto'] * 100:+.1f} % sull'atteso")
        if e.get("perche"):
            print(f"   ⚠ {e['perche']}")
        for x in e.get("rossi", []):
            print(f"   ⛔ ROSSO {x['motivo']}: {x['testo']}")

        ok, spiegazione = combacia(e)
        e["combacia"] = ok
        e["spiegazione"] = spiegazione
        print(f"   ⇒ {'⭐ COMBACIA' if ok else '⛔ NON COMBACIA'}: {spiegazione}")

    # ── La tabella, che e' quel che si legge davvero ───────────────────────
    print("\n" + "=" * 74)
    print("== La tabella — ⛔ e si legge la RIGA, non il colore in fondo")
    print("   (`LEZIONI.md` §1.1-bis: il campo che salva la giornata e la riga")
    print("    che la butta stanno nello stesso file, a due centimetri)")
    print("=" * 74)
    print(f"{'giro':<22} {'atteso':<26} {'visto':<18} esito")
    for e in esiti:
        at = e.get("atteso") or {}
        voluto = at.get("rosso_atteso") or "VERDE"
        m = e.get("misura") or {}
        visto = (f"{m.get('hz', '-')} Hz rms {m.get('rms', '-')}"
                 if m.get("esito") == "GIUDICATO" else e.get("stato", "-"))
        print(f"{e['nome']:<22} {voluto:<26} {visto:<18} "
              f"{'⭐ combacia' if e.get('combacia') else '⛔ NO'}")

    # ── I quattro codici d'uscita, in ordine di gravita' ───────────────────
    non_misurati = [e for e in esiti if e.get("stato") in ("NON MISURATO", "BANCO ROTTO")]
    ciechi = [e for e in esiti
              if (e.get("atteso") or {}).get("rosso_atteso") and not e.get("combacia")
              and e.get("stato") not in ("NON MISURATO", "BANCO ROTTO")]
    rotti = [e for e in esiti
             if not (e.get("atteso") or {}).get("rosso_atteso") and not e.get("combacia")
             and e.get("stato") not in ("NON MISURATO", "BANCO ROTTO")]

    print()
    if non_misurati:
        print("⚠ NON HO MISURATO su "
              f"{len(non_misurati)} giri su {len(esiti)} — e NON e' un rosso "
              "del prodotto:")
        for e in non_misurati:
            print(f"   · {e['nome']}: {e.get('perche')}")
        return 2
    if ciechi:
        print(f"⛔⛔ IL BANCO E' CIECO su {len(ciechi)} controlli su "
              f"{len(esiti)}: un difetto innestato NON e' stato visto.")
        for e in ciechi:
            print(f"   · {e['nome']}: {e.get('spiegazione')}")
        print("   ⚠ Finche' questo non e' verde, i verdi degli altri giri non")
        print("     valgono niente: un banco cieco da' verde a tutto.")
        return 3
    if rotti:
        print(f"⛔ IL PRODOTTO E' ROSSO su {len(rotti)} giri su {len(esiti)}:")
        for e in rotti:
            print(f"   · {e['nome']}: {e.get('spiegazione')}")
        return 1
    print(f"⭐ VERDE su {len(esiti)} giri — e vale per quel che ha guardato: il "
          f"SEGNALE che esce")
    print("   dalla sessione, non il numero dei blocchi.  ⚠ Il RITMO dell'audio")
    print("   vero non e' giudicato: e' riferito, e la sua soglia la deve porre")
    print("   chi l'avra' misurato (`fasi/07-audio-e-appunti.md` §8).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
