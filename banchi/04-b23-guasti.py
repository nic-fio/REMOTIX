#!/usr/bin/env python3
"""04-b23-guasti.py — ⛔ LA CERTIFICAZIONE di B23: il banco sa vedere il difetto?

    python3 04-b23-guasti.py
    python3 04-b23-guasti.py --solo bordo-stretto
    python3 04-b23-guasti.py --elenco

===========================================================================
⛔ PERCHE' QUESTO FILE ESISTE — `CODER.md` §3.3 e §4.6

«Accerta che il banco sappia produrre il risultato atteso PRIMA di puntarlo
sull'incognita.  Altrimenti un esito negativo e' ambiguo fra "non funziona
l'incognita" e "non funzionava il banco".»

⛔ E il rovescio, che e' piu' insidioso perche' il banco e' VERDE (§3.4): *«un
   banco verde mentre il difetto e' vivo e' la peggiore delle prove, perche' da'
   fiducia»*.  B23 e' passato al primo giro, 54 casi su 54.  ⚠ Un banco che
   passa al primo giro non ha ancora dimostrato niente: potrebbe essere scritto
   in modo da passare sempre.

⇒ Qui si ROMPE `banchi/rcp/rcp.c` in modi noti, uno alla volta, e si pretende
  che B23 diventi **rosso esattamente sui casi dichiarati** — non «da qualche
  parte», e non «su tutto».

===========================================================================
⛔⭐ LA COLONNA CHE CONTA DI PIU': `lunghezza-tardiva`

Il guasto sposta il controllo della lunghezza DOPO l'arrivo del corpo.  ⛔ Il
motivo resta giusto, il `CONGEDO` parte, il codice di chiusura e' quello, la
sessione muore: **un banco che contasse le violazioni resterebbe VERDE**.  A
diventare rosso e' la sola colonna «su quale byte» — e questo e' quel che
certifica che quella colonna ha i denti.

⚠ Ed e' il difetto vero, non uno di comodo: §6.1 dice «la lunghezza si controlla
  prima di allocare.  Un ricevente che alloca `lunghezza` byte e poi verifica ha
  gia' regalato un megabyte a chiunque sappia scrivere sei byte».

===========================================================================
⛔ IL FILE SI RIMETTE A POSTO, SEMPRE

Il guasto vive per un giro solo, e il ripristino sta in un `finally`: un
`banchi/rcp/rcp.c` lasciato guasto fermerebbe il costruttore di **tutti e dieci
gli anelli** (il `Makefile`, variabile `GEMELLATI`, confronta le due copie).
⚠ E alla fine si verifica che il file sia tornato IDENTICO a `src/rcp.c` — non
  «che il ripristino sia stato chiamato».
"""
import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
GEMELLO = os.path.join(QUI, "rcp", "rcp.c")
ORIGINALE = os.path.abspath(os.path.join(QUI, "..", "src", "rcp.c"))

VERDE, ROSSO, GIALLO, GRIGIO = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

# ===========================================================================
# ⛔ IL CATALOGO.  Ogni guasto: che cosa si rompe, e QUALI casi devono diventare
#    rossi — l'insieme ESATTO.
#
#    ⚠ «Esatto» e non «almeno»: un guasto che facesse cadere anche casi che non
#      c'entrano vorrebbe dire che il banco non separa le proprieta', e allora
#      un rosso non direbbe piu' dove guardare.  E' la stessa ragione per cui
#      `LEZIONI.md` §1.9 vuole i denominatori.
# ===========================================================================
GUASTI = {
    # ── ⛔⭐ QUELLO CHE CERTIFICA LA COLONNA DEL BYTE ──────────────────────
    "lunghezza-tardiva": {
        "cerca": "\t\t\tif (lung != attesa) {",
        "metti": "\t\t\tif (s->inp_acc_len >= (size_t)6u + lung && lung != attesa) {",
        "spiega":
            "⛔⭐ §6.1: il controllo della lunghezza si sposta DOPO l'arrivo del "
            "corpo.  Il motivo resta giusto e la sessione muore lo stesso: a "
            "cambiare colore e' SOLO la colonna «su quale byte».  ⚠ E "
            "`lunghezza-1mib` non viene accusato AFFATTO, perche' quel corpo non "
            "arriva mai — cioe' il megabyte regalato",
        "rossi": {"lunghezza-in-piu", "lunghezza-in-meno",
                  "pulsante-allineato-a-16", "lunghezza-1mib", "lunghezza-4gib"},
    },

    # ── ⛔ IL BORDO, che ha gia' un rilievo scritto contro di se' (R1.16) ──
    "bordo-stretto": {
        "cerca": "\tif (x < s->tela_l && y < s->tela_a)\n\t\treturn true;",
        "metti": "\tif (x + 1 < s->tela_l && y + 1 < s->tela_a)\n\t\treturn true;",
        "spiega":
            "⛔ L'ultimo pixel non e' piu' cliccabile: `>` invece di `>=`, il "
            "difetto piu' facile da scrivere di tutta §7.3.  ⚠ Il sintomo per "
            "l'utente sarebbe una colonna di pixel a destra e una riga in basso "
            "che non rispondono — e nessun conteggio di violazioni lo vede, "
            "perche' le violazioni restano tutte verdi",
        # ⛔⭐ E `x-enorme` CADE ANCHE LUI, e non e' un difetto del catalogo:
        #    con `x + 1` la somma va in overflow — `0xFFFFFFFF + 1` vale 0 — e
        #    la coordinata piu' sbagliata di tutte diventa la piu' accettabile.
        #    ⭐ La cura ingenua del bordo APRE un buco all'altro estremo, e il
        #      banco lo dice da se': e' quel che si compra scrivendo l'insieme
        #      ESATTO dei rossi invece di «almeno questi».
        "rossi": {"ok-puntatore-al-bordo-1919-1079", "x-enorme"},
    },

    # ── ⛔ IL SEGNO DELLA ROTELLA, invertito due volte ─────────────────────
    "rotella-invertita-due-volte": {
        "cerca": "\t\tesito = ha_canale_input(s) ? s->g.input_rotella(s->g.ctx, ax, ay) : -1;",
        "metti": "\t\tesito = ha_canale_input(s) ? s->g.input_rotella(s->g.ctx, ax, -ay) : -1;",
        "spiega":
            "⛔ `rcp.c` inverte l'asse verticale che `input_rotella()` invertira' "
            "di nuovo: le due si ANNULLANO, e la rotella va al contrario per ogni "
            "utente (forma d'errore E11, il riquadro `[M]` del 10 agosto 2026).  "
            "⚠ Nessuna violazione cambia colore: e' un difetto che vive solo nei "
            "casi che devono passare",
        "rossi": {"ok-rotella-uno-scatto-su", "ok-rotella-uno-scatto-giu",
                  "ok-rotella-mezzo-scatto"},
    },

    # ── ⚠ I MEZZI SCATTI arrotondati a zero ───────────────────────────────
    "mezzo-scatto-arrotondato": {
        "cerca": "\t\ts->inp_ultimo_id = id;\n\t\ts->inp_ultimo_istante_us = istante;\n\t\t/* ⛔⛔ E QUI NON SI TOCCA NIENTE",
        "metti": "\t\ts->inp_ultimo_id = id;\n\t\ts->inp_ultimo_istante_us = istante;\n\t\tax = ax / 120 * 120;\n\t\tay = ay / 120 * 120;\n\t\t/* ⛔⛔ E QUI NON SI TOCCA NIENTE",
        "spiega":
            "⚠ §7.3: «i mezzi scatti esistono: 60 e' mezzo scatto e NON DEVE "
            "essere arrotondato a zero».  E' la divisione intera per 120 che "
            "`gnome.md` §9 attribuisce a `ei_device_scroll_discrete`: qui la fa "
            "`rcp.c`, e lo scorrimento fine sparisce senza un errore",
        "rossi": {"ok-rotella-mezzo-scatto"},
    },

    # ── ⛔ IL CONTATORE PER TIPO invece che per canale ─────────────────────
    "id-senza-controllo": {
        "cerca": "\tif (id <= s->inp_ultimo_id) {",
        "metti": "\tif (false && id <= s->inp_ultimo_id) {",
        "spiega":
            "⛔ §7.3: l'`id` non viene piu' controllato affatto — ed e' il "
            "comportamento che cinque contatori per tipo avrebbero sul caso "
            "`id-per-tipo-invece-che-per-canale`.  ⚠ Il campo `input` dei "
            "fotogrammi (§6.2) smetterebbe di tornare indietro coerente con "
            "niente",
        "rossi": {"id-ripetuto", "id-indietro",
                  "id-per-tipo-invece-che-per-canale"},
    },

    # ── ⛔ I SURROGATI che passano ─────────────────────────────────────────
    "surrogati-ammessi": {
        "cerca": "\t\tif (car >= 0xD800u && car <= 0xDFFFu) {",
        "metti": "\t\tif (false && car >= 0xD800u && car <= 0xDFFFu) {",
        "spiega":
            "⛔ §7.3: «esclusi i surrogati 0xD800-0xDFFF».  ⚠ E' precisamente il "
            "controllo che un'implementazione ferma a `> 0x10FFFF` non ha — e "
            "che una pagina scritta con `charCodeAt` invece di `codePointAt` "
            "solletica a ogni emoji",
        "rossi": {"lettera-surrogato-d800", "lettera-surrogato-dfff"},
    },

    # ── ⛔ IL SECONDO DI GRAZIA che non si apre ────────────────────────────
    "niente-grazia": {
        "cerca": "\tbool grazia_aperta = s->tela_prec_l != 0 && s->tela_prec_a != 0 &&",
        "metti": "\tbool grazia_aperta = false && s->tela_prec_l != 0 && s->tela_prec_a != 0 &&",
        "spiega":
            "⛔ §7.1, terza eccezione di §3: senza la grazia, un `PUNTATORE` "
            "partito prima che il `TELA` arrivasse CHIUDE LA SESSIONE.  ⚠ E' "
            "esattamente «chiudere la sessione per un arrotondamento», che "
            "`SPECIFICHE.md` §8.3 vieta",
        "rossi": {"ok-grazia-satura", "ok-grazia-al-millesimo-1000"},
    },

    # ── ⛔ LA GRAZIA che diventa una tolleranza generale ───────────────────
    "grazia-sempre-aperta": {
        "cerca": "\t                     ora - s->tela_grazia_da <= TELA_GRAZIA;",
        "metti": "\t                     true;",
        "spiega":
            "⛔ Il rovescio del precedente, e §3 lo chiama per nome: «la grazia "
            "NON e' una tolleranza generale sulle coordinate — sarebbe "
            "l'indulgenza che §3 esiste per togliere».  Con la scadenza tolta, "
            "una coordinata vecchia passa per sempre",
        "rossi": {"grazia-scaduta"},
    },

    # ── ⛔ «RICEVUTO» al posto di «INIETTATO» ──────────────────────────────
    "campo-input-su-ricevuto": {
        "cerca": "\ts->inp_non_iniettati++;\n\tif (esito == 1 && tipo == T_LETTERA)",
        "metti": "\ts->inp_non_iniettati++;\n\ts->inp_ultimo_iniettato = id;\n\tif (esito == 1 && tipo == T_LETTERA)",
        "spiega":
            "⛔ §6.2: il campo `input` avanza anche quando il compositore ha "
            "detto di no.  ⚠ Il fotogramma prometterebbe un effetto che nella "
            "scena non c'e', e chi misura il ritardo dell'anello chiuso "
            "(`DECISIONI.md` §2.6) misurerebbe un input mai iniettato",
        "rossi": {"ok-campo-input-non-avanza-se-non-iniettato",
                  "ok-lettera-non-producibile"},
    },

    # ── ⛔ IL RILASCIO AL DISTACCO che non parte ───────────────────────────
    "niente-rilascio": {
        "cerca": "\tif (!s || s->inp_rilasciato)\n\t\treturn;\n\ts->inp_rilasciato = true;",
        "metti": "\tif (!s || s->inp_rilasciato)\n\t\treturn;\n\ts->inp_rilasciato = true;\n\tif (perche)\n\t\treturn;",
        "spiega":
            "⛔ §7.3, ultimo capoverso, che `RCP.md` §11 chiama «la regola col "
            "rapporto danno/costo piu' alto del documento».  ⚠ Un Ctrl rimasto "
            "giu' in una sessione che sopravvive al client rende il desktop "
            "inservibile al riattacco, e nessuno collega le due cose: il banco "
            "deve accorgersene DA SOLO, perche' l'utente non ci arrivera' mai",
        "rossi": set(),   # riempito sotto: tocca TUTTE le sessioni coi ganci
        "rilascio_zero": True,
    },

    # ── ⛔ `premuto` INDULGENTE ────────────────────────────────────────────
    "premuto-indulgente": {
        "cerca": "\t\tif (premuto > 1) {",
        "metti": "\t\tif (premuto > 255) {",
        "spiega":
            "⛔ §7.3: «1 = premuto, 0 = rilasciato».  Un 2 letto come «vero» e' "
            "il parser indulgente di §3: comodissimo il primo giorno, e il "
            "giorno in cui un client manda 2 per sbaglio il tasto resta giu' per "
            "sempre",
        "rossi": {"pulsante-premuto-2", "posizione-premuto-255"},
    },

    # ── ⛔⭐ §7.2: LA LUNGHEZZA DEL `CURSORE_FORMA` ────────────────────────
    #
    # ⚠ Questo guasto rimette **il difetto vero**, quello che il banco ha trovato
    #   al primo giro il 14 agosto 2026: si spedisce `w.len` invece di `n`.
    #   `scrittore` conta i byte passati DA LUI, e l'immagine ci arriva con una
    #   `memcpy` che non vede — quindi `w.len` vale 8 e il messaggio dichiara
    #   16x16 con OTTO byte di corpo.
    # ⛔ Il registro del server, intanto, scriveva la riga giusta: la calcolava
    #    da `n`.  **Il registro diceva il vero e il filo un'altra cosa** — ed e'
    #    la ragione per cui `CODER.md` §3.8 vuole che si verifichi dal lato che
    #    riceve.
    "cursore-lunghezza-da-scrittore": {
        "cerca": "\tmanda_messaggio(s, T_CURSORE_FORMA, corpo, n);",
        "metti": "\tmanda_messaggio(s, T_CURSORE_FORMA, corpo, w.len);",
        "spiega":
            "⛔⭐ IL DIFETTO VERO, rimesso: il `CURSORE_FORMA` dichiara 16x16 e "
            "porta otto byte di corpo.  ⚠ La pagina chiuderebbe con "
            "ERRORE_PROTOCOLLO a ogni cambio di forma del cursore, e il sintomo "
            "per l'utente sarebbe «la sessione cade quando muovo il mouse su un "
            "bordo».  ⛔ Il cursore NASCOSTO resta verde — li' il corpo E' otto "
            "byte — e questo e' quel che rende il difetto invisibile a un banco "
            "che provi il solo caso facile",
        "rossi": {"ok-cursore-16x16-sul-filo",
                  "ok-cursore-256x256-il-massimo-di-5.5"},
    },

    # ── ⛔ E LA LUNGHEZZA CHE NON SI CONTROLLA AFFATTO ─────────────────────
    "cursore-lunghezza-non-controllata": {
        "cerca": "\tif (byte_immagine != immagine_n) {",
        "metti": "\tif (false && byte_immagine != immagine_n) {",
        "spiega":
            "⛔ §7.2: senza il confronto, `rcp.c` legge `larghezza x altezza x 4` "
            "byte **sulla fiducia** — cioe' confeziona e spedisce il «cursore "
            "fatto di memoria altrui» che §7.2 nomina.  ⚠ Il caso "
            "`in-piu` resta verde: li' i byte ci sono davvero, e a mancare e' "
            "solo la lunghezza dichiarata",
        "rossi": {"cursore-lunghezza-non-torna-in-meno",
                  "cursore-lunghezza-non-torna-in-piu"},
    },

    # ── ⛔⭐ §5.5: «UNA SOLA DELLE DUE A ZERO» ─────────────────────────────
    #
    # ⚠ Il guasto rimette il buco che questo rapporto aveva dichiarato aperto, e
    #   che il coordinatore ha deciso di chiudere il 14 agosto 2026.
    # ⛔⭐ E il valore di questo guasto sta in quel che NON diventa rosso:
    #    `ok-cursore-nascosto-otto-byte` resta VERDE.  ⇒ Il banco distingue
    #    «rifiuto una sola delle due a zero» da «rifiuto tutti gli zeri», e la
    #    seconda farebbe sparire per sempre il cursore nascosto.
    "cursore-zeri-non-appaiati": {
        "cerca": "\tif ((larghezza == 0) != (altezza == 0)) {",
        "metti": "\tif (false && (larghezza == 0) != (altezza == 0)) {",
        "spiega":
            "⛔ §5.5: `0x5` verrebbe SPEDITO, e la sua lunghezza TORNA (otto "
            "byte, nessun pixel) — quindi nessun altro controllo di questa "
            "funzione lo fermerebbe.  ⚠ Il client lo rifiuterebbe come §5.5 gli "
            "ORDINA, e la sessione cadrebbe per colpa nostra",
        "rossi": {"cursore-una-sola-a-zero-0x5", "cursore-una-sola-a-zero-5x0"},
    },

    # ── ⛔⭐ E L'ALTRA META' DELLA COPPIA: si rifiutano TUTTI gli zeri ─────
    #
    # ⛔ E' l'errore che il coordinatore ha nominato, e va certificato nel verso
    #    in cui fa danno: un controllo che rifiuta **qualunque** zero soddisfa i
    #    due casi `0x5`/`5x0` — che restano verdi — e fa sparire per sempre il
    #    cursore NASCOSTO.  ⚠ Il sintomo per l'utente non nomina il cursore:
    #    «il puntatore resta fermo quando entro in un campo di testo».
    # ⭐ Da cui: l'insieme atteso dei rossi e' UNO SOLO, ed e' il caso positivo.
    #    Nessuno dei tre casi, da solo, distinguerebbe le due implementazioni.
    "cursore-rifiuta-ogni-zero": {
        "cerca": "\tif ((larghezza == 0) != (altezza == 0)) {",
        "metti": "\tif (larghezza == 0 || altezza == 0) {",
        "spiega":
            "⛔ Il cursore NASCOSTO di §5.5 non partirebbe mai: `0x0` e' proprio "
            "il modo in cui l'arbitro dice «nascosto», e rifiutarlo e' la forma "
            "di difetto che §5.5 ha gia' pagato una volta (rilievo R11.11, «una "
            "regola che vieta un caso che il documento stesso definisce»).  "
            "⚠ I due casi `0x5`/`5x0` restano VERDI: sono rifiutati anche cosi'",
        "rossi": {"ok-cursore-nascosto-otto-byte"},
    },

    # ── ⛔ LO STREAM DI INPUT prima di `SESSIONE` ──────────────────────────
    "input-senza-sessione": {
        # ⚠ L'ancora comprende la riga che segue: `if (!s->sessione_spedita) {`
        #   da sola compare DUE volte in `rcp.c` — l'altra e' in
        #   `tratta_richiedi_chiave()` — e un'ancora ambigua avrebbe innestato
        #   il guasto nel posto sbagliato.  ⛔ `applica()` se n'e' accorto e ha
        #   rifiutato invece di indovinare (§3 applicata al banco).
        "cerca": "\tif (!s->sessione_spedita) {\n\t\tviola_input(s,",
        "metti": "\tif (false && !s->sessione_spedita) {\n\t\tviola_input(s,",
        "spiega":
            "⛔ §2.5, e l'invariante I3 sul filo: si accetterebbe input da chi "
            "non ha ancora ricevuto `SESSIONE` — cioe' da chi, un istante prima, "
            "non era nemmeno passato dal validatore",
        "rossi": {"input-prima-di-sessione"},
    },
}


def applica(testo, g):
    if g["cerca"] not in testo:
        return None
    if testo.count(g["cerca"]) != 1:
        return None
    return testo.replace(g["cerca"], g["metti"], 1)


def gira_giudice(uscita):
    """⛔ Si compila e si gira DA CAPO: la traccia dev'essere di questo sorgente."""
    esiti = os.path.join(uscita, "esiti.json")
    if os.path.exists(esiti):
        os.remove(esiti)
    r = subprocess.run(
        [sys.executable, os.path.join(QUI, "04-b23-filo-input.py"),
         "--uscita", uscita, "--json-esiti", esiti],
        capture_output=True, text=True, cwd=QUI)
    if not os.path.exists(esiti):
        return None, r.stdout + r.stderr
    with open(esiti) as f:
        return json.load(f)["esiti"], r.stdout


def principale(a):
    if a.elenco:
        print(f"== la certificazione di B23: {len(GUASTI)} guasti innestati, "
              f"uno per giro\n")
        for nome, g in GUASTI.items():
            quali = (", ".join(sorted(g["rossi"])) if g["rossi"]
                     else "(tutte le sessioni coi ganci: vedi `rilascio_zero`)")
            print(f"  {nome}")
            print(f"     {g['spiega']}")
            print(f"     ⇒ devono diventare ROSSI: {quali}\n")
        return 0

    with open(GEMELLO) as f:
        sano = f.read()

    # ⛔ Il controllo positivo: col file SANO, B23 dev'essere tutto verde.  Senza
    #    questo, un rosso su un guasto non distingue «il banco vede il difetto»
    #    da «il banco era gia' rosso» (`CODER.md` §3.10).
    print("== ⭐ IL CONTROLLO POSITIVO — col sorgente SANO, B23 e' tutto verde?")
    base, uscita_testo = gira_giudice(a.uscita)
    if base is None:
        print(f"{ROSSO}⛔ il giudice non ha prodotto un verdetto{GRIGIO}\n"
              f"{uscita_testo[-3000:]}")
        return 2
    rossi_base = {k for k, v in base.items() if not v}
    if rossi_base:
        print(f"  {ROSSO}⛔ B23 e' gia' rosso su {len(rossi_base)} casi PRIMA "
              f"di innestare qualunque guasto: {', '.join(sorted(rossi_base))}"
              f"{GRIGIO}")
        print("     La certificazione non si puo' fare: un rosso non "
              "distinguerebbe il guasto dal difetto gia' presente.")
        return 2
    print(f"  {VERDE}✅{GRIGIO} {len(base)} casi, tutti verdi.  ⭐ Da qui in poi "
          f"ogni rosso e' del guasto innestato\n")

    # `niente-rilascio` tocca il conteggio del rilascio, non un caso: si
    # dichiara qui e si giudica sull'uscita del giudice.
    guasti_visti = 0
    provati = 0
    try:
        for nome, g in GUASTI.items():
            if a.solo and a.solo not in nome:
                continue
            provati += 1
            rotto = applica(sano, g)
            if rotto is None:
                print(f"  {ROSSO}⛔ {nome:32s} il pezzo di codice da rompere non "
                      f"si trova (o compare piu' volte){GRIGIO}")
                print(f"     ⚠ Il guasto non e' stato innestato: NON e' un "
                      f"verde, e' una prova non fatta.  Il catalogo e' rimasto "
                      f"indietro rispetto a `rcp.c`.")
                guasti_visti += 1
                continue
            with open(GEMELLO, "w") as f:
                f.write(rotto)

            esiti, testo = gira_giudice(a.uscita)
            if esiti is None:
                # ⚠ Un guasto che non compila e' una prova non fatta, non un
                #   verde: si dice, e si conta.
                print(f"  {ROSSO}⛔ {nome:32s} col guasto innestato il banco non "
                      f"gira affatto{GRIGIO}")
                guasti_visti += 1
                continue
            rossi = {k for k, v in esiti.items() if not v}

            if g.get("rilascio_zero"):
                # ⛔ Questo guasto non fa cadere un CASO: fa cadere il conteggio
                #    del rilascio, che ha un denominatore suo.  Si giudica li'.
                ok = "rilascio al distacco, UNA volta per sessione" in testo and \
                     ("chiamate diverse da 1" in testo)
                atteso = "il conteggio del rilascio va a zero"
                visto = ("il conteggio del rilascio e' caduto" if ok
                         else "⛔ NESSUNO se n'e' accorto")
            else:
                ok = rossi == g["rossi"]
                atteso = ", ".join(sorted(g["rossi"])) or "(nessuno)"
                visto = ", ".join(sorted(rossi)) or "(nessuno: B23 e' rimasto VERDE)"

            c = VERDE if ok else ROSSO
            print(f"  {c}{'✅' if ok else '⛔'}{GRIGIO} {nome:32s} {visto}")
            if not ok:
                guasti_visti += 1
                print(f"     atteso rosso su: {atteso}")
                print(f"     {g['spiega']}")
                if not rossi and not g.get("rilascio_zero"):
                    print(f"     {ROSSO}⛔ E QUESTO E' IL CASO PEGGIORE: il "
                          f"difetto e' vivo e il banco e' verde — `CODER.md` "
                          f"§3.4{GRIGIO}")
    finally:
        # ⛔ SEMPRE, e non «se tutto e' andato bene»: un gemello lasciato guasto
        #    ferma il costruttore di tutti e dieci gli anelli.
        with open(GEMELLO, "w") as f:
            f.write(sano)

    # ⛔ E il ripristino si VERIFICA, dal lato che conta: i due file identici.
    pari = filecmp.cmp(GEMELLO, ORIGINALE, shallow=False)
    if pari:
        print(f"\n  {VERDE}✅{GRIGIO} il gemello e' tornato IDENTICO a "
              f"`src/rcp.c` — il costruttore non si ferma")
    else:
        print(f"\n  {ROSSO}⛔⛔ IL GEMELLO NON E' TORNATO A POSTO: "
              f"`banchi/rcp/rcp.c` diverge da `src/rcp.c`, e il `Makefile` "
              f"fermera' TUTTI E DIECI GLI ANELLI{GRIGIO}")
        guasti_visti += 1

    print(f"\n  {provati} guasti innestati su {len(GUASTI)} del catalogo")
    if guasti_visti:
        print(f"\n    {ROSSO}⛔ LA CERTIFICAZIONE NON PASSA: {guasti_visti} "
              f"guasti che B23 non vede come dovrebbe{GRIGIO}")
        return 1
    print(f"\n    {VERDE}⭐ B23 e' CERTIFICATO{GRIGIO}: ciascuno dei {provati} "
          f"guasti lo fa diventare rosso esattamente dove dichiarato")
    print(f"    ⚠ e non su tutto: un banco che desse rosso ovunque non direbbe "
          f"piu' DOVE guardare")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="la certificazione di B23 — il banco sa vedere il difetto?")
    p.add_argument("--uscita", default="/tmp/b23")
    p.add_argument("--solo", default="")
    p.add_argument("--elenco", action="store_true")
    sys.exit(principale(p.parse_args()))
