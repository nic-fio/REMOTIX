#!/usr/bin/env python3
"""04-b27-classico.py — ⭐ IL BANCO DEL MODO CLASSICO (anello A7 della fase 4).

    python3 banchi/04-b27-classico.py --certifica         ⭐ senza browser: il
                                                             giudice sa vedere
                                                             il difetto?
    python3 banchi/04-b27-classico.py --gira --porta 7661 --diagnosi 7662
    python3 banchi/04-b27-classico.py --verdetto banchi/04-b27-registro.jsonl

===========================================================================
⛔ CHE COSA MISURA, E DA CHE PARTE STA

`SPECIFICHE.md` §7.1/§7.3 e `RCP.md` §7.3.  La pagina del prodotto
(`src/pagina.html`, ancora `F4-INPUT-CLASSICO`) trasforma il mouse fisico e la
tastiera vera in **cinque messaggi di RCP**.  Questo file NON guarda il
registro della pagina: guarda **i byte**, e li decodifica con un lettore
scritto qui, dalla tabella di `RCP.md` §7.3, senza guardare il JavaScript.

⭐ E' la stessa forma di `banchi/02-pagina-prodotto.html`: due implementazioni
   indipendenti degli stessi byte.  ⛔ Se un giorno non andranno d'accordo,
   **quel disaccordo e' il regalo** — e ricopiare lo scrittore della pagina lo
   farebbe sparire senza che nessuno se ne accorga.

⛔ `CODER.md` §3.8 — «si verifica dal lato che deve ricevere».  I byte escono
   dal browser su un socket (`POST /byte`), e il giudizio si fa **in questo
   processo**, su una registrazione su disco che chiunque puo' rileggere.  Il
   registro della pagina non entra in nessun verdetto.

===========================================================================
⛔ I QUATTRO CASI CHE IL MANDATO PRETENDE

  B1  IL BORDO.  Il puntatore all'angolo estremo della vista DEVE produrre
      **1919, 1079** su una tela 1920x1080 — mai 1920.  `RCP.md` §7.3: «le
      coordinate sono indici di pixel, 0 <= x < tela_larghezza … la
      conversione e' del client, ARROTONDANDO PER DIFETTO», e il riquadro del
      rilievo R1.16 dice che cosa costa sbagliarla: «una pagina che divide per
      il fattore di scala e arrotonda per eccesso produce 1920 su una tela di
      1920: una lettura lo inietta, l'altra CHIUDE LA SESSIONE» — cioe' la cosa
      che `SPECIFICHE.md` §8.3 vieta, «mai staccare».
      ⇒ Si prova a **piu' fattori di scala**, scelti perche' producono i
        decimali peggiori (viste dispari e prime rispetto a 1920).

  B2  `Ctrl+C` COPIA, NON SCRIVE UNA `c`.  `RCP.md` §7.3: «`LETTERA` si usa
      quando si scrive del testo; `POSIZIONE_TASTO` quando e' premuto un
      modificatore di comando».  ⇒ Sul filo DEVONO esserci quattro
      `POSIZIONE_TASTO` (29 giu', 46 giu', 46 su, 29 su) e **zero `LETTERA`**.
      ⚠ E il controllo che rende il caso non banale e' il suo gemello: una `c`
        senza modificatori DEVE produrre **una `LETTERA` e nessuna posizione**.
        Senza quel gemello, una pagina che non manda NIENTE passerebbe B2.

  B3  IL RILASCIO ALLA PERDITA DEL FUOCO.  `SPECIFICHE.md` §7.3-bis (O10): la
      Keyboard Lock «si spegne da sola quando la pagina perde il fuoco, cioe'
      esattamente nell'istante in cui un modificatore resta premuto».  ⇒ Si
      preme un modificatore E un pulsante, si toglie il fuoco, e si conta che
      cosa la pagina rilascia.  Se non rilascia, il banco e' **ROSSO**.

  B4  IL CONTROLLO POSITIVO.  `CODER.md` §3.10: «ogni misura vuole un controllo
      positivo sullo stesso strumento — questo strumento sa vedere qualcosa che
      c'e' di sicuro?».  Qui e' in DUE posti:
        · nella scena  — la `c` nuda di B2, che arriva di sicuro se il canale
          funziona.  Se non arriva nemmeno quella, il rosso e' del BANCO;
        · nel giudice  — `--certifica`, che passa al verdetto tre registrazioni
          fatte a mano (sana, guasta, risanata) e pretende verde-rosso-verde.
          ⛔ Un giudice che non sa dire rosso non sa dire verde.

===========================================================================
⚠ LA SCENA, DICHIARATA — e il palco si verifica dall'altro capo

I browser stanno su CHUWI, sul desktop VERO dell'utente: `XDG_SESSION_TYPE`
dice `wayland`, e Chrome ignora `DISPLAY`.  ⛔ Non si forza
`--ozone-platform=x11`: curerebbe la scena distruggendo la misura.  ⇒ La
scena si scrive in ogni riga del registro (`scena`), e il lanciatore la
ricava dall'ambiente invece di dichiararla a memoria.

⛔ E il canale di input NON esiste ancora nel prodotto: `src/pagina.html` non
   apre lo stream unidirezionale di `RCP.md` §2.5 (lo aprira' la cucitura del
   coordinatore, e la firma sta nel rapporto A7).  ⇒ Qui la cucitura la mette
   IL BANCO, da fuori, con `Page.addScriptToEvaluateOnNewDocument`: si definisce
   `window.REMOTIX_INPUT = { prossimo_id(), manda(tipo, corpo) }` — ⭐ la stessa
   firma che chiedono A7 e A8 — e il `manda` spedisce i byte a questo processo
   invece che sullo stream.  ⚠ Quel che si misura e' quindi **lo scrittore dei
   messaggi del prodotto**, non il trasporto: il trasporto e' la cucitura, e
   il rapporto lo dichiara come non misurato.

===========================================================================
⛔ ZERO E FALLIMENTO — `CODER.md` §3.10

«Nessun messaggio» ha quattro cause con lo stesso aspetto: il browser non e'
partito · la pagina non si e' aperta · il modo non si e' acceso · i messaggi
non sono usciti.  Ciascuna ha qui la sua riga e il suo stato d'uscita, e il
verdetto stampa SEMPRE il conto dei byte ricevuti accanto a ogni caso.
"""
import argparse
import http.server
import importlib.util
import json
import os
import socketserver
import struct
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# ---------------------------------------------------------------------------
# ⛔ IL LETTORE DEI MESSAGGI DI INPUT — scritto dalla tabella di `RCP.md` §7.3
#    e dall'inquadratura di §6.1.  Nessuna riga viene dal prodotto.
#
#     §6.1   u16 tipo · u32 lunghezza · corpo
#     §7.3   u32 id (da 1, 0 riservato) · u64 istante (microsecondi)
#            PUNTATORE        + u32 x · u32 y
#            PULSANTE         + u16 codice · u8 premuto
#            ROTELLA          + i32 asse_x · i32 asse_y     (120 per scatto)
#            LETTERA          + u32 carattere               (scalare Unicode)
#            POSIZIONE_TASTO  + u16 codice · u8 premuto
# ---------------------------------------------------------------------------
PUNTATORE, PULSANTE, ROTELLA, LETTERA, POSIZIONE = (
    0x0101, 0x0102, 0x0103, 0x0104, 0x0105)
NOME_TIPO = {PUNTATORE: "PUNTATORE", PULSANTE: "PULSANTE", ROTELLA: "ROTELLA",
             LETTERA: "LETTERA", POSIZIONE: "POSIZIONE_TASTO"}

# I codici evdev che il banco nomina.  `linux/input-event-codes.h`.
KEY_LEFTCTRL, KEY_C, KEY_A, KEY_ESC = 29, 46, 30, 1
BTN_LEFT, BTN_RIGHT, BTN_MIDDLE = 0x110, 0x111, 0x112


class Violazione(Exception):
    pass


def decodifica(byte):
    """Da un flusso di byte ai messaggi.  ⛔ Lancia se l'inquadratura non torna:
    una lunghezza incoerente col tipo e' `ERRORE_PROTOCOLLO` (§6.1), e un banco
    che la ignorasse direbbe verde su un filo rotto."""
    fuori, o = [], 0
    while o < len(byte):
        if len(byte) - o < 6:
            raise Violazione("coda di %d byte: non c'e' nemmeno l'inquadratura"
                             % (len(byte) - o))
        tipo, lung = struct.unpack_from(">HI", byte, o)
        o += 6
        if len(byte) - o < lung:
            raise Violazione("il corpo di 0x%04x e' troncato (%d < %d)"
                             % (tipo, len(byte) - o, lung))
        corpo, o = byte[o:o + lung], o + lung
        if tipo not in NOME_TIPO:
            raise Violazione("tipo 0x%04x: non e' del canale di input (§2.5: "
                             "il byte alto DEVE essere 0x01)" % tipo)
        if len(corpo) < 12:
            raise Violazione("%s: corpo di %d byte, i due campi comuni ne "
                             "vogliono 12" % (NOME_TIPO[tipo], len(corpo)))
        mid, istante = struct.unpack_from(">IQ", corpo, 0)
        m = {"tipo": tipo, "nome": NOME_TIPO[tipo], "id": mid,
             "istante": istante, "byte": len(corpo)}
        resto = corpo[12:]
        atteso = {PUNTATORE: 8, PULSANTE: 3, ROTELLA: 8, LETTERA: 4,
                  POSIZIONE: 3}[tipo]
        if len(resto) != atteso:
            raise Violazione("%s: %d byte di corpo proprio invece di %d "
                             "(§6.1: la lunghezza DEVE essere esatta)"
                             % (m["nome"], len(resto), atteso))
        if tipo == PUNTATORE:
            m["x"], m["y"] = struct.unpack(">II", resto)
        elif tipo in (PULSANTE, POSIZIONE):
            m["codice"], m["premuto"] = struct.unpack(">HB", resto)
        elif tipo == ROTELLA:
            m["asse_x"], m["asse_y"] = struct.unpack(">ii", resto)
        elif tipo == LETTERA:
            (m["carattere"],) = struct.unpack(">I", resto)
        fuori.append(m)
    return fuori


# ---------------------------------------------------------------------------
# ⛔ IL GIUDICE.  Prende la registrazione (fasi + byte) e produce i casi.
#    ⚠ Ogni caso porta con se' il CONTO dei messaggi che ha visto: un «verde»
#      su zero messaggi e' la forma E10, e senza il conto non si distingue.
# ---------------------------------------------------------------------------
def _messaggi_di(righe, fase):
    byte = b""
    for r in righe:
        if r.get("fase") == fase and r.get("hex"):
            byte += bytes.fromhex(r["hex"])
    return decodifica(byte)


def _nota_di(righe, fase):
    """La nota che il conduttore ha lasciato per quella fase: il rettangolo
    letto, i punti spediti e le attese CALCOLATE IN PYTHON."""
    for r in righe:
        if r.get("fase") == fase and isinstance(r.get("nota"), dict):
            return r["nota"]
    return {}


def _tutti(righe):
    byte = b""
    for r in righe:
        if r.get("hex"):
            byte += bytes.fromhex(r["hex"])
    return decodifica(byte)


def giudica(righe, tela=(1920, 1080)):
    tela_l, tela_a = tela
    casi = []

    def caso(nome, verde, quanti, perche):
        casi.append({"caso": nome, "esito": "verde" if verde else "ROSSO",
                     "messaggi": quanti, "perche": perche})

    # -- il controllo positivo dello strumento ------------------------------
    try:
        tutti = _tutti(righe)
        rotto = None
    except Violazione as e:
        tutti, rotto = [], str(e)
    if rotto:
        caso("B0-inquadratura", False, 0, "i byte non si decodificano: " + rotto)
        return casi
    caso("B0-inquadratura", len(tutti) > 0, len(tutti),
         "%d messaggi decodificati dall'inquadratura di §6.1" % len(tutti))

    # -- B4a: la `c` nuda e' arrivata? (il controllo positivo nella scena) ---
    try:
        soli = _messaggi_di(righe, "F0-c-nuda")
    except Violazione as e:
        soli = []
        caso("B4a-controllo-positivo", False, 0, str(e))
    else:
        lettere = [m for m in soli if m["tipo"] == LETTERA]
        pos = [m for m in soli if m["tipo"] == POSIZIONE]
        caso("B4a-controllo-positivo",
             len(lettere) == 1 and lettere[0]["carattere"] == 0x63
             and len(pos) == 0, len(soli),
             "una `c` senza modificatori: attesa 1 LETTERA U+0063 e 0 "
             "POSIZIONE_TASTO — viste %d LETTERA %s e %d POSIZIONE_TASTO"
             % (len(lettere), [hex(x["carattere"]) for x in lettere], len(pos)))

    # -- B1a: il bordo SENZA lock, a piu' fattori di scala ------------------
    # ⛔⭐ E L'ATTESA NON E' «1919» A OGNI SCALA — RISCRITTA IL 14 AGOSTO 2026,
    #     SU UNA MISURA DELLO STRUMENTO.
    #
    # La prima stesura pretendeva `1919, 1079` a ogni fattore di scala.  ⛔ E'
    # falso, e il rosso era del BANCO: `[M]` Chrome consegna coordinate del
    # mouse INTERE, quindi in una vista larga 1361 px l'ultimo punto
    # raggiungibile e' `1360`, che sulla tela vale `1360 × 1920 / 1361 =
    # 1918,59` — cioe' **1918**, non 1919.  Una vista rimpicciolita non puo'
    # indirizzare tutti i pixel della tela, ed e' giusto cosi'.
    #
    # ⇒ L'attesa la calcola QUESTO file, in Python, dal punto che ha spedito e
    #   dal rettangolo che ha letto: `floor((x − sinistra) × tela / larghezza)`.
    #   ⭐ E' un secondo calcolo indipendente della stessa formula, ed e' quel
    #   che distingue `floor` da `round` e da `ceil`: a 1361 px il valore vero e'
    #   1918,59, dove il difetto di R1.16 direbbe 1919.
    fasi_bordo = sorted({r["fase"] for r in righe
                         if r.get("fase", "").startswith("F1-bordo-")})
    if not fasi_bordo:
        caso("B1a-bordo", False, 0, "nessuna fase di bordo nella registrazione")
    for f in fasi_bordo:
        attese = _nota_di(righe, f).get("attese")
        try:
            mm = [m for m in _messaggi_di(righe, f) if m["tipo"] == PUNTATORE]
        except Violazione as e:
            caso("B1a-bordo/" + f, False, 0, str(e))
            continue
        fuori = [(m["x"], m["y"]) for m in mm
                 if m["x"] >= tela_l or m["y"] >= tela_a]
        visto = [(m["x"], m["y"]) for m in mm]
        att = [tuple(a) for a in (attese or [])]
        # ⚠ Non si pretende un messaggio per punto: un puntatore che non cambia
        #   pixel non ha niente da dire, ed e' quel che fa anche un mouse vero.
        #   Si pretende che ogni valore visto sia uno di quelli calcolati, e che
        #   l'ULTIMO sia l'ultimo.
        ok = (bool(visto) and not fuori and bool(att)
              and visto[-1] == att[-1]
              and all(v in att for v in visto))
        caso("B1a-bordo/" + f, ok, len(mm),
             "attesi (calcolo indipendente, ARROTONDANDO PER DIFETTO) %s; "
             "visti %s; fuori intervallo %s"
             % (att, visto, fuori[:4] or "nessuna"))

    # -- B1b: la saturazione all'ultimo pixel, AGGANCIATI -------------------
    # ⛔⭐ E' QUI CHE IL 1920 PUO' NASCERE.  Agganciati (`Pointer Lock`) il
    #    puntatore lo tiene la pagina e lo spinge oltre il bordo: una pagina che
    #    saturasse alla TELA invece che all'ultimo pixel — o che arrotondasse
    #    per eccesso — spedirebbe **1920**, e il server chiuderebbe la sessione
    #    (`RCP.md` §7.3, rilievo R1.16; `SPECIFICHE.md` §8.3 «mai staccare»).
    for f, atteso in (("F8-satura-alto", (tela_l - 1, tela_a - 1)),
                      ("F8-satura-basso", (0, 0))):
        n = _nota_di(righe, f)
        try:
            mm = [m for m in _messaggi_di(righe, f) if m["tipo"] == PUNTATORE]
        except Violazione as e:
            caso("B1b-satura/" + f, False, 0, str(e))
            continue
        if n.get("agganciato") is not True:
            casi.append({"caso": "B1b-satura/" + f, "esito": "non-misurato",
                         "messaggi": len(mm),
                         "perche": "`Pointer Lock` non era agganciato: senza, il "
                                   "puntatore non si puo' spingere OLTRE il bordo, "
                                   "e il caso non e' stato misurato (non e' verde "
                                   "e non e' rosso)"})
            continue
        fuori = [(m["x"], m["y"]) for m in mm
                 if m["x"] >= tela_l or m["y"] >= tela_a]
        ultimo = (mm[-1]["x"], mm[-1]["y"]) if mm else None
        caso("B1b-satura/" + f, bool(mm) and not fuori and ultimo == atteso,
             len(mm),
             "spinto oltre il bordo con la lock: atteso %s e nessuna coordinata "
             ">= tela; ultimo %s, fuori intervallo %s"
             % (str(atteso), ultimo, fuori[:4] or "nessuna"))

    # -- B2: Ctrl+C ---------------------------------------------------------
    try:
        mm = _messaggi_di(righe, "F2-ctrl-c")
    except Violazione as e:
        caso("B2-ctrl-c", False, 0, str(e))
    else:
        atteso = [(POSIZIONE, KEY_LEFTCTRL, 1), (POSIZIONE, KEY_C, 1),
                  (POSIZIONE, KEY_C, 0), (POSIZIONE, KEY_LEFTCTRL, 0)]
        visto = [(m["tipo"], m.get("codice"), m.get("premuto")) for m in mm]
        lettere = [m for m in mm if m["tipo"] == LETTERA]
        caso("B2-ctrl-c", visto == atteso and not lettere, len(mm),
             "atteso %s e ZERO LETTERA; visto %s (LETTERA: %d)"
             % (atteso, visto, len(lettere)))

    # -- B2-bis: Maiusc non e' un comando (§7.3: «serve a FARE la lettera») --
    try:
        mm = _messaggi_di(righe, "F6-maiusc-a")
    except Violazione as e:
        caso("B2bis-maiusc", False, 0, str(e))
    else:
        lettere = [m for m in mm if m["tipo"] == LETTERA]
        pos = [m for m in mm if m["tipo"] == POSIZIONE]
        caso("B2bis-maiusc",
             len(lettere) == 1 and lettere[0]["carattere"] == 0x41
             and not pos, len(mm),
             "Maiusc+a: attesa 1 LETTERA U+0041 e ZERO posizioni; viste %d "
             "LETTERA %s e %d posizioni %s"
             % (len(lettere), [hex(x["carattere"]) for x in lettere], len(pos),
                [(p["codice"], p["premuto"]) for p in pos]))

    # -- B2-ter: la lettera accentata diretta -------------------------------
    try:
        mm = _messaggi_di(righe, "F9-accento-diretto")
    except Violazione as e:
        caso("B2ter-accento", False, 0, str(e))
    else:
        lettere = [m for m in mm if m["tipo"] == LETTERA]
        caso("B2ter-accento",
             len(lettere) == 1 and lettere[0]["carattere"] == 0xE0
             and not [m for m in mm if m["tipo"] == POSIZIONE], len(mm),
             "`à` come tasto DIRETTO (disposizione italiana): attesa 1 LETTERA "
             "U+00E0 e nessuna posizione; viste %s"
             % [hex(x["carattere"]) for x in lettere])

    # -- B3: il rilascio alla perdita del fuoco -----------------------------
    try:
        mm = _messaggi_di(righe, "F3-fuoco-perso")
    except Violazione as e:
        caso("B3-fuoco", False, 0, str(e))
    else:
        rilasci_tasto = [m for m in mm
                         if m["tipo"] == POSIZIONE and m["premuto"] == 0]
        rilasci_pulsante = [m for m in mm
                            if m["tipo"] == PULSANTE and m["premuto"] == 0]
        codici = sorted(m["codice"] for m in rilasci_tasto)
        pulsanti = sorted(m["codice"] for m in rilasci_pulsante)
        caso("B3-fuoco", KEY_LEFTCTRL in codici and BTN_LEFT in pulsanti,
             len(mm),
             "perso il fuoco con Ctrl (29) e BTN_LEFT (0x110) premuti: attesi "
             "i due rilasci; visti tasti %s e pulsanti %s"
             % (codici, [hex(p) for p in pulsanti]))
        # ⛔ E il gemello negativo: PRIMA di perdere il fuoco non deve essere
        #    uscito nessun rilascio, o «rilascia» e «non ha mai premuto»
        #    avrebbero lo stesso aspetto.
        try:
            prima = _messaggi_di(righe, "F3-fuoco-tenuto")
        except Violazione as e:
            caso("B3bis-nessun-rilascio-prima", False, 0, str(e))
        else:
            r = [m for m in prima if m.get("premuto") == 0]
            caso("B3bis-nessun-rilascio-prima", not r, len(prima),
                 "a fuoco tenuto non deve uscire nessun rilascio; visti %d" % len(r))

    # -- B5: la rotella (segno e mezzi scatti) ------------------------------
    for fase, atteso_y in (("F4-rotella-su", +120), ("F4-rotella-giu", -120),
                           ("F4-rotella-mezzo-su", +60)):
        try:
            mm = [m for m in _messaggi_di(righe, fase) if m["tipo"] == ROTELLA]
        except Violazione as e:
            caso("B5-rotella/" + fase, False, 0, str(e))
            continue
        somma = sum(m["asse_y"] for m in mm)
        caso("B5-rotella/" + fase, bool(mm) and somma == atteso_y, len(mm),
             "atteso asse_y = %+d (unita' da 120 per scatto, il client manda "
             "+120 quando l'utente gira IN SU; il segno lo inverte il SERVER, "
             "una volta sola); somma vista %+d" % (atteso_y, somma))

    # -- B6: l'id cresce su TUTTO il canale, e comincia da 1 ----------------
    ids = [m["id"] for m in tutti]
    crescente = all(b > a for a, b in zip(ids, ids[1:]))
    caso("B6-id", bool(ids) and ids[0] == 1 and crescente, len(ids),
         "l'id DEVE cominciare da 1 (0 e' riservato) e crescere di almeno uno "
         "su tutto il canale, non uno per tipo; primo %s, crescente %s"
         % (ids[0] if ids else None, crescente))

    # -- B7: l'istante non fa credere a una precisione che non ha -----------
    istanti = [m["istante"] for m in tutti]
    tondi = [i for i in istanti if i % 1000 != 0]
    monotono = all(b >= a for a, b in zip(istanti, istanti[1:]))
    caso("B7-istante", bool(istanti) and not tondi and monotono, len(istanti),
         "§7.3 (R1.27): in una pagina l'orologio e' in millisecondi, il client "
         "scrive millisecondi x 1000; non tondi %d, monotono %s"
         % (len(tondi), monotono))

    return casi


# ---------------------------------------------------------------------------
# ⛔ LA CERTIFICAZIONE DEL GIUDICE — sano, guasto, risanato.  `CODER.md` §3.3:
#    «accerta che il banco sappia produrre il risultato atteso prima di
#    puntarlo sull'incognita».  Qui non serve nessun browser.
# ---------------------------------------------------------------------------
def _msg(tipo, mid, istante, resto):
    corpo = struct.pack(">IQ", mid, istante) + resto
    return struct.pack(">HI", tipo, len(corpo)) + corpo


def _registrazione(guasto=None):
    """Una registrazione fatta a mano che DEVE passare tutti i casi.  Il
    parametro `guasto` ne rompe uno solo per volta."""
    righe, n, t = [], [0], [1000000]

    def m(fase, tipo, resto):
        n[0] += 1
        t[0] += 1000
        righe.append({"fase": fase, "hex": _msg(tipo, n[0], t[0], resto).hex()})

    m("F0-c-nuda", LETTERA, struct.pack(">I", 0x63))
    # ⛔ Il bordo SENZA lock: le attese le calcola il conduttore, e la
    #    registrazione finta le porta con se' come la vera.
    for nome, attese in (("1361x766", [[959, 540], [1918, 1078]]),
                         ("777x437", [[958, 538], [1917, 1077]])):
        righe.append({"fase": "F1-bordo-" + nome,
                      "nota": {"vista": [0, 0, 0, 0], "attese": attese}})
        for k, (x, y) in enumerate(attese):
            # ⛔ Il guasto e' quello di R1.16: si arrotonda per ECCESSO, e a
            #    1918,59 esce 1919 — un pixel che sulla tela c'e' ancora, ma
            #    che NON e' quello dove sta il mouse.  ⚠ E' il guasto piu'
            #    insidioso proprio perche' non chiude la sessione: la chiude
            #    solo all'ultimo pixel, cioe' un utente su cento.
            if guasto == "bordo" and k == len(attese) - 1:
                x += 1
            m("F1-bordo-" + nome, PUNTATORE, struct.pack(">II", x, y))
    # E il bordo CON la lock: la saturazione all'ultimo pixel valido.
    righe.append({"fase": "F8-satura-alto", "nota": {"agganciato": True}})
    m("F8-satura-alto", PUNTATORE, struct.pack(">II", 0, 0))
    m("F8-satura-alto", PUNTATORE,
      struct.pack(">II", 1920 if guasto == "satura" else 1919,
                  1080 if guasto == "satura" else 1079))
    righe.append({"fase": "F8-satura-basso", "nota": {"agganciato": True}})
    m("F8-satura-basso", PUNTATORE, struct.pack(">II", 0, 0))
    if guasto == "ctrl-c":
        m("F2-ctrl-c", POSIZIONE, struct.pack(">HB", KEY_LEFTCTRL, 1))
        m("F2-ctrl-c", LETTERA, struct.pack(">I", 0x63))     # la `c` che NON va
        m("F2-ctrl-c", POSIZIONE, struct.pack(">HB", KEY_LEFTCTRL, 0))
    else:
        for c, p in ((KEY_LEFTCTRL, 1), (KEY_C, 1), (KEY_C, 0), (KEY_LEFTCTRL, 0)):
            m("F2-ctrl-c", POSIZIONE, struct.pack(">HB", c, p))
    m("F6-maiusc-a", LETTERA, struct.pack(">I", 0x41))
    m("F9-accento-diretto", LETTERA,
      struct.pack(">I", 0x65 if guasto == "accento" else 0xE0))
    m("F3-fuoco-tenuto", POSIZIONE, struct.pack(">HB", KEY_LEFTCTRL, 1))
    m("F3-fuoco-tenuto", PULSANTE, struct.pack(">HB", BTN_LEFT, 1))
    if guasto != "fuoco":
        m("F3-fuoco-perso", POSIZIONE, struct.pack(">HB", KEY_LEFTCTRL, 0))
        m("F3-fuoco-perso", PULSANTE, struct.pack(">HB", BTN_LEFT, 0))
    else:
        righe.append({"fase": "F3-fuoco-perso", "hex": ""})
    su = -120 if guasto == "rotella" else +120
    m("F4-rotella-su", ROTELLA, struct.pack(">ii", 0, su))
    m("F4-rotella-giu", ROTELLA, struct.pack(">ii", 0, -120))
    m("F4-rotella-mezzo-su", ROTELLA, struct.pack(">ii", 0, +60))
    if guasto == "id":
        # due contatori separati: l'id riparte da 1 per tipo
        righe.append({"fase": "F5-id", "hex": _msg(LETTERA, 1, t[0] + 1000,
                                                   struct.pack(">I", 0x64)).hex()})
    if guasto == "istante":
        righe.append({"fase": "F5-id", "hex": _msg(LETTERA, n[0] + 1, t[0] + 137,
                                                   struct.pack(">I", 0x64)).hex()})
    return righe


def certifica():
    print("⭐ certificazione del GIUDICE — sano, guasto, risanato "
          "(nessun browser, nessuna rete)")
    ok = True
    casi = giudica(_registrazione())
    rossi = [c for c in casi if c["esito"] == "ROSSO"]
    print("  sano      → %d casi, %d rossi" % (len(casi), len(rossi)))
    for c in rossi:
        print("      ⛔", c["caso"], "—", c["perche"])
    ok = ok and not rossi
    for g, atteso in (("bordo", "B1a-bordo"), ("satura", "B1b-satura"),
                      ("ctrl-c", "B2-ctrl-c"),
                      ("accento", "B2ter-accento"),
                      ("fuoco", "B3-fuoco"), ("rotella", "B5-rotella"),
                      ("id", "B6-id"), ("istante", "B7-istante")):
        casi = giudica(_registrazione(g))
        rossi = [c["caso"] for c in casi if c["esito"] == "ROSSO"]
        preso = any(r.startswith(atteso) for r in rossi)
        print("  guasto «%-8s» → rossi %s   %s"
              % (g, rossi or "NESSUNO", "✅ visto" if preso else "⛔ NON VISTO"))
        ok = ok and preso
    casi = giudica(_registrazione())
    rossi = [c for c in casi if c["esito"] == "ROSSO"]
    print("  risanato  → %d rossi" % len(rossi))
    ok = ok and not rossi
    print("⭐ giudice CERTIFICATO" if ok else "⛔ giudice NON certificato")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# IL SERVITORE: serve `src/pagina.html` del PRODOTTO e raccoglie i byte.
# ⛔ Il file si serve com'e', coi soli quattro segnaposti che il server vero
#    riempie (`__IMPRONTA__`, `__AVVISO__`, `__BANNATO__`, `__RESTANO_MS__`):
#    un banco che ne servisse una copia modificata misurerebbe la copia (E10).
# ---------------------------------------------------------------------------
class Raccolta:
    def __init__(self):
        self.righe = []
        self.fase = "F-nessuna"
        self.blocco = threading.Lock()
        self.byte = 0

    def marca(self, fase):
        with self.blocco:
            self.fase = fase
            self.righe.append({"t": time.time(), "fase": fase, "marca": True})

    def aggiungi(self, dati):
        with self.blocco:
            self.byte += len(dati)
            self.righe.append({"t": time.time(), "fase": self.fase,
                               "hex": dati.hex()})

    def annota(self, obj):
        """Quel che il CONDUTTORE sa e i byte non dicono: il rettangolo in cui
        ha spinto il mouse, i punti che ha spedito, e le attese che ha calcolato
        da se'.  ⛔ Non e' una misura del prodotto: e' la scena, scritta accanto
        ai byte perche' il verdetto si possa rifare fra un mese."""
        with self.blocco:
            self.righe.append({"t": time.time(), "fase": self.fase,
                               "nota": obj})


def servitore(porta, raccolta, pagina_html):
    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass                      # il registro utile e' quello dei byte

        def _corpo(self, tipo, dati, stato=200):
            self.send_response(stato)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dati)))
            # ⛔⭐ LE TRE INTESTAZIONI DELL'ISOLAMENTO FRA ORIGINI, come le manda
            #    il prodotto (`src/pagina.c`, `SPECIFICHE.md` §11.5, `web.md` O11).
            #    ⚠ Non sono un ornamento del banco: `[M]` 14 agosto 2026 senza di
            #    esse `crossOriginIsolated` e' `false` e la grana di
            #    `performance.now()` cambia — cioe' il banco misurerebbe un
            #    orologio che il prodotto non ha (`LEZIONI.md` §1.11: si
            #    misurerebbe la scena).
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.end_headers()
            self.wfile.write(dati)

        def do_GET(self):
            p = self.path.split("?")[0].split("#")[0]
            if p == "/":
                self._corpo("text/html; charset=utf-8", pagina_html)
            elif p == "/stato":
                self._corpo("application/json",
                            json.dumps({"byte": raccolta.byte,
                                        "righe": len(raccolta.righe)}).encode())
            else:
                self._corpo("text/plain", b"non c'e'", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            dati = self.rfile.read(n)
            p = self.path.split("?")[0]
            if p == "/byte":
                raccolta.aggiungi(dati)
            elif p == "/fase":
                raccolta.marca(dati.decode("utf-8", "replace"))
            elif p == "/nota":
                raccolta.annota(json.loads(dati.decode("utf-8")))
            self._corpo("text/plain", b"ok")

    # ⛔ `allow_reuse_address` PRIMA di costruire, non dopo: il socket lo lega il
    #    costruttore, e un giro appena finito lascia la porta in TIME_WAIT — cioe'
    #    il banco non si potrebbe rilanciare due volte di fila.
    class S(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    # ⚠ E se un giro precedente sta ancora morendo, si RIPROVA per qualche
    #   secondo invece di dire «porta occupata»: due cause diverse — «un altro
    #   banco ci sta sopra» e «il mio giro di prima non e' ancora sepolto» —
    #   avrebbero lo stesso messaggio, e solo la prima e' un errore.
    fine, ultimo = time.time() + 8, None
    while True:
        try:
            s = S(("127.0.0.1", porta), H)
            break
        except OSError as e:
            ultimo = e
            if time.time() > fine:
                raise RuntimeError("la porta %d non si libera in 8 s: %s"
                                   % (porta, ultimo))
            time.sleep(0.5)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


# ---------------------------------------------------------------------------
# LA GUIDA: CDP.  Il cliente e' quello gia' scritto per il banco delle misure
# (`02-pagina-misura-cdp.py`), che documenta da se' perche' il banco guarda da
# FUORI invece di farsi consegnare gli esiti dal prodotto.
# ---------------------------------------------------------------------------
def _cdp():
    p = os.path.join(QUI, "02-pagina-misura-cdp.py")
    spec = importlib.util.spec_from_file_location("cdpmod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔⭐ LA CUCITURA, MESSA DAL BANCO — ED E' LA STESSA CHE CHIEDONO A7 E A8.
#
#     window.REMOTIX_INPUT = { prossimo_id(), manda(tipo, corpo) }
#
# E' la riga che il coordinatore scrivera' in `collega()`: li' il `manda`
# scrivera' sullo stream unidirezionale di §2.5, qui spedisce gli stessi byte a
# questo processo.  ⚠ E' l'unica differenza fra il banco e il prodotto, ed e'
# dichiarata: il TRASPORTO non e' misurato qui.
#
# ⛔ E LE SPEDIZIONI SI METTONO IN CODA, UNA DIETRO L'ALTRA.  Con `fetch` in
#    parallelo l'ordine di arrivo non e' quello di partenza: un banco che
#    giudicasse «l'id cresce» su byte riordinati dalla rete misurerebbe la
#    rete.  ⇒ Una catena di promesse, e la marca di fase entra nella STESSA
#    catena — o una fase potrebbe marcare byte che non sono ancora arrivati.
#
# ⛔ E il prologo va PRIMA di ogni script della pagina
#    (`Page.addScriptToEvaluateOnNewDocument`): la cucitura deve esistere prima
#    che il modo classico spedisca il primo messaggio.
PROLOGO = r"""
(function () {
  var n = 0, coda = Promise.resolve();
  window.__b27 = { spediti: 0, errori: [] };
  window.REMOTIX_INPUT = {
    prossimo_id: function () {
      n = (n >= 4294967295) ? 1 : n + 1;
      return n;
    },
    manda: function (tipo, corpo) {
      var m = new Uint8Array(6 + corpo.length);
      var v = new DataView(m.buffer);
      v.setUint16(0, tipo); v.setUint32(2, corpo.length); m.set(corpo, 6);
      window.__b27.spediti++;
      coda = coda.then(function () {
        return fetch("/byte", { method: "POST", body: m });
      }).catch(function (e) { window.__b27.errori.push(String(e)); });
    },
  };
  window.__b27.fase = function (nome) {
    coda = coda.then(function () {
      return fetch("/fase", { method: "POST", body: nome });
    }).catch(function (e) { window.__b27.errori.push(String(e)); });
    return coda;
  };
  window.__b27.attendi = function () { return coda.then(function () { return true; }); };
  /* ⛔⭐ LO STRUMENTO SI GUARDA ALLO SPECCHIO.  `CODER.md` §3.11: «quando codice
     letto e misura si contraddicono, il sospetto va PRIMA sulla misura».  Qui
     si registra che cosa il BROWSER ha davvero consegnato alla pagina — le
     coordinate di ogni `mousemove` e i campi crudi di ogni `wheel` — cosi' un
     rosso si puo' attribuire: al prodotto, o al banco che non ha consegnato
     l'evento che credeva.  ⚠ Sono osservazioni del banco su Chrome, non il
     registro del prodotto: nessun verdetto si costruisce su questi campi. */
  window.__b27.crudi = { mosse: [], rotelle: [] };
  addEventListener("mousemove", function (ev) {
    if (window.__b27.crudi.mosse.length < 200)
      window.__b27.crudi.mosse.push([Math.round(ev.clientX * 100) / 100,
                                     Math.round(ev.clientY * 100) / 100,
                                     ev.movementX, ev.movementY,
                                     ev.target && ev.target.id]);
  }, true);
  addEventListener("wheel", function (ev) {
    if (window.__b27.crudi.rotelle.length < 40)
      window.__b27.crudi.rotelle.push([ev.deltaX, ev.deltaY, ev.deltaMode,
                                       ev.wheelDeltaX, ev.wheelDeltaY]);
  }, true);
})();
"""

# La scena: la tela del prodotto si accende e prende la misura che il banco
# dichiara.  ⚠ `data-schermo="acceso"` e' quel che il prodotto scrive da se' al
# primo fotogramma (`componi()`), ed e' la condizione a cui il modo classico
# lega la cattura della tastiera: senza, il banco misurerebbe un modo spento.
SCENA = r"""
(function () {
  document.body.dataset.schermo = "acceso";
  const t = document.getElementById("schermo");
  t.width = %d; t.height = %d;
  const c = window.REMOTIX_CLASSICO, s = window.REMOTIX && window.REMOTIX.input_classico;
  if (!c || !s) return "⛔ REMOTIX_CLASSICO / REMOTIX.input_classico non esistono";
  return JSON.stringify({ disposizione: document.body.dataset.disposizione,
                          stato: s.stato() });
})()
"""

VISTA = r"""
(function () {
  const t = document.getElementById("schermo");
  t.style.width = "%dpx"; t.style.height = "%dpx";
  const r = t.getBoundingClientRect();
  return [r.left, r.top, r.width, r.height];
})()
"""


def gira(porta, diagnosi, esiti, registro, tela=(1920, 1080), attesa=30):
    cdp = _cdp()
    with open(os.path.join(RADICE, "src", "pagina.html"), "rb") as f:
        html = f.read()
    for chiave, valore in ((b"__IMPRONTA__", b""), (b"__AVVISO__", b""),
                           (b"__BANNATO__", b"no"), (b"__RESTANO_MS__", b"0")):
        html = html.replace(chiave, valore)
    raccolta = Raccolta()
    s = servitore(porta, raccolta, html)
    print("  servitore su http://127.0.0.1:%d — pagina del PRODOTTO, %d byte"
          % (porta, len(html)))

    b = cdp.pagina(diagnosi, attesa)
    c = cdp.Cdp(b["webSocketDebuggerUrl"])
    c.chiama("Page.enable")
    c.chiama("Runtime.enable")
    c.chiama("Page.addScriptToEvaluateOnNewDocument", source=PROLOGO)
    # ⚠ `?disposizione=classico` e' la via di servizio che l'ancora del TOCCO
    #   dichiara per il banco e la diagnosi: la scena si DICHIARA invece di
    #   dipendere da come il browser risponde a `(any-pointer: fine)` sul
    #   desktop di chi lancia.  ⛔ E si verifica dall'altro capo, leggendo
    #   `body[data-disposizione]` — che e' il prodotto a scrivere.
    c.chiama("Page.navigate",
             url="http://127.0.0.1:%d/?disposizione=classico" % porta)
    time.sleep(2.0)

    scena = {
        "macchina": os.uname().nodename,
        "sessione": os.environ.get("XDG_SESSION_TYPE"),
        "wayland": os.environ.get("WAYLAND_DISPLAY"),
        "display": os.environ.get("DISPLAY"),
        "browser": c.valuta("navigator.userAgent"),
        "tela": list(tela),
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print("  scena:", json.dumps(scena, ensure_ascii=False))

    # ⛔⭐ LA GRANA DELL'OROLOGIO, MISURATA INVECE CHE CREDUTA.
    # `RCP.md` §7.3 (R1.27) dice: «in una pagina l'orologio monotono e' in
    # MILLISECONDI e la sua grana e' deliberatamente ingrossata».  ⇒ E' una
    # premessa, e una premessa si misura: si prendono mille letture di fila e si
    # guarda il piu' piccolo scarto diverso da zero.  Il numero finisce nel
    # rapporto A7 accanto alla tesi che lo riguarda.
    grana = c.valuta("""(function(){
      var v=[],i,d=[],min=Infinity;
      for(i=0;i<4000;i++) v.push(performance.now());
      for(i=1;i<v.length;i++){var s=v[i]-v[i-1]; if(s>0&&s<min) min=s;}
      return JSON.stringify({minimo_ms:min, isolata:!!self.crossOriginIsolated,
                             esempio:v.slice(0,3)});})()""")
    scena["orologio"] = json.loads(grana) if grana else None
    print("  orologio:", grana)

    acceso = c.valuta(SCENA % (tela[0], tela[1]))
    print("  scena della pagina:", acceso)
    if not acceso or acceso.startswith("⛔"):
        s.shutdown()
        return 3, scena, []
    scena["pagina"] = json.loads(acceso)
    if scena["pagina"].get("disposizione") != "classico":
        print("  ⛔ la disposizione in vigore non e' «classico»: il banco "
              "misurerebbe l'altra meta' della pagina")
        s.shutdown()
        return 3, scena, []

    inceppi = []

    def quiete(fermo=0.4, tetto=4.0):
        """⛔⭐ SI ASPETTA CHE I BYTE SIANO ARRIVATI, NON UN TEMPO.
        `[M]` 14 agosto 2026: con tre browser sulla stessa macchina una rotella
        spedita nella fase «su» e' arrivata dentro la fase «giu'», e il banco ha
        dato ROSSO a un prodotto corretto — la somma dei due scatti opposti fa
        zero.  ⚠ L'attesa a tempo fisso e' una grandezza SOSTITUTIVA (la
        famiglia P8→P20 di `LEZIONI.md` §1.13): il tempo non e' l'arrivo.  ⇒ Si
        aspetta che il conto dei byte ricevuti stia fermo, e si dichiara se non
        si e' fermato."""
        fine = time.time() + tetto
        ultimo, da = raccolta.byte, time.time()
        while time.time() < fine:
            time.sleep(0.05)
            if raccolta.byte != ultimo:
                ultimo, da = raccolta.byte, time.time()
            elif time.time() - da >= fermo:
                return True
        inceppi.append({"metodo": "quiete", "fase": raccolta.fase,
                        "errore": "i byte non si sono fermati in %.1f s" % tetto})
        return False

    def fase(nome):
        # ⛔ La marca entra nella STESSA coda dei byte, e si aspetta che la coda
        #    si svuoti: senza, una fase marcherebbe byte della precedente.
        quiete()
        c.valuta("window.__b27.attendi()")
        c.valuta("window.__b27.fase(%s)" % json.dumps(nome))
        c.valuta("window.__b27.attendi()")

    def scarica():
        c.valuta("window.__b27.attendi()")

    # ⛔⭐ UN COLPO CHE NON TORNA NON UCCIDE LA MISURA, E SI SCRIVE.
    #    `[M]` 14 agosto 2026: su una macchina con dieci banchi in parallelo
    #    `Input.dispatchMouseEvent` ha smesso di rispondere entro il tetto del
    #    cliente CDP, due giri di fila e in punti diversi.  ⚠ E' la scena, non il
    #    prodotto — ma un banco che morisse li' butterebbe anche le fasi gia'
    #    misurate, e chi legge il rosso non saprebbe distinguere «il prodotto non
    #    manda» da «il banco e' morto a metà».  ⇒ Si registra e si va avanti.
    def colpo(metodo, **p):
        try:
            c.chiama(metodo, **p)
            return True
        except Exception as e:                        # noqa: BLE001
            inceppi.append({"metodo": metodo, "errore": str(e)[:120],
                            "fase": raccolta.fase})
            print("  ⚠ %s non ha risposto (%s): si va avanti e lo si scrive"
                  % (metodo, str(e)[:60]))
            return False

    def tasto(tipo, key, code, vk, modificatori=0, testo=None):
        p = {"type": tipo, "key": key, "code": code,
             "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk,
             "modifiers": modificatori}
        if testo is not None:
            p["text"] = testo
        colpo("Input.dispatchKeyEvent", **p)

    def mouse(tipo, x, y, **k):
        colpo("Input.dispatchMouseEvent", type=tipo, x=x, y=y, **k)

    # ⛔ Il fuoco alla pagina prima di battere: senza, la tastiera va altrove e
    #    lo zero sarebbe del banco, non del prodotto.
    c.chiama("Page.bringToFront")
    time.sleep(0.4)

    # -- F0: il controllo positivo — una `c` che arriva di sicuro -----------
    fase("F0-c-nuda")
    tasto("keyDown", "c", "KeyC", 67, 0, "c")
    tasto("keyUp", "c", "KeyC", 67, 0)
    time.sleep(0.4)

    # -- F1: il bordo, a piu' fattori di scala ------------------------------
    # ⚠ Le viste sono scelte perche' `1920 / vista` e' un decimale cattivo: 1361,
    #   777 e 641 sono dispari e primi rispetto a 1920, 1366×768 e' la misura
    #   vera di un portatile, 1279×719 e' «quasi 1:1» — dove un errore di
    #   arrotondamento e' piu' piccolo di un pixel e sfugge a chi guarda a occhio.
    # ⛔ E TUTTE STANNO DENTRO LA FINESTRA: un angolo fuori dal viewport non
    #    produce nessun evento, e il banco misurerebbe il proprio bordo.
    for vl, va in ((1361, 766), (777, 437), (1366, 768), (641, 361),
                   (1279, 719)):
        r = c.valuta(VISTA % (vl, va))
        if not isinstance(r, list):
            continue
        left, top, w, h = r
        fase("F1-bordo-%dx%d" % (vl, va))
        # ⛔ COORDINATE INTERE.  `[M]` 14 agosto 2026: Chrome consegna alla
        #    pagina `clientX/clientY` TRONCATI, ma fa il collaudo del bersaglio
        #    sul valore ARROTONDATO — un punto a `w − 0,01` finisce sull'`<h1>`
        #    che sta sotto la tela, e l'evento alla tela non arriva mai.  Il
        #    banco perdeva l'angolo e dava rosso al prodotto.
        punti, attese = [], []
        for x, y in ((int(left + w // 2), int(top + h // 2)),
                     (int(left + w) - 1, int(top + h) - 1)):
            punti.append([x, y])
            # ⭐ L'attesa, calcolata QUI e non chiesta alla pagina: indice di
            #   pixel sulla tela, ARROTONDATO PER DIFETTO e saturato all'ultimo.
            ax = min(tela[0] - 1, max(0, int((x - left) * tela[0] / w)))
            ay = min(tela[1] - 1, max(0, int((y - top) * tela[1] / h)))
            attese.append([ax, ay])
        raccolta.annota({"vista": [left, top, w, h], "punti": punti,
                         "attese": attese})
        for x, y in punti:
            mouse("mouseMoved", x, y, button="none", buttons=0)
            time.sleep(0.12)
        scarica()
    c.valuta(VISTA % (1361, 766))

    # -- F2: Ctrl+C ---------------------------------------------------------
    fase("F2-ctrl-c")
    tasto("rawKeyDown", "Control", "ControlLeft", 17, 2)
    tasto("rawKeyDown", "c", "KeyC", 67, 2)
    tasto("keyUp", "c", "KeyC", 67, 2)
    tasto("keyUp", "Control", "ControlLeft", 17, 0)
    time.sleep(0.4)

    # -- F6: Maiusc+a — Maiusc NON e' un comando ----------------------------
    fase("F6-maiusc-a")
    tasto("rawKeyDown", "Shift", "ShiftLeft", 16, 8)
    tasto("keyDown", "A", "KeyA", 65, 8, "A")
    tasto("keyUp", "A", "KeyA", 65, 8)
    tasto("keyUp", "Shift", "ShiftLeft", 16, 0)
    time.sleep(0.4)

    # -- F4: la rotella -----------------------------------------------------
    r = c.valuta(VISTA % (1361, 766))
    left, top, w, h = r
    cx, cy = left + w / 2, top + h / 2
    for nome, dy in (("F4-rotella-su", -100), ("F4-rotella-giu", +100),
                     ("F4-rotella-mezzo-su", -50)):
        fase(nome)
        mouse("mouseWheel", cx, cy, deltaX=0, deltaY=dy, button="none",
              buttons=0)
        time.sleep(0.35)

    # -- F7: Pointer Lock ---------------------------------------------------
    # ⛔ Sta DOPO il bordo di proposito: agganciati, il puntatore lo muovono gli
    #    SPOSTAMENTI, e un banco che agganciasse prima misurerebbe il ripiego
    #    invece della strada principale — o viceversa, senza saperlo.
    fase("F7-lock")
    # ⛔⭐ IL FUOCO SI RIPRENDE E SI VERIFICA PRIMA DI CHIEDERE LA LOCK.
    #    `[M]` 14 agosto 2026: `Pointer Lock` e' risultato agganciato in un giro
    #    e NEGATO nel giro dopo, a codice identico.  ⚠ La causa e' la scena: sul
    #    desktop dell'utente girano in parallelo i banchi degli altri anelli, e
    #    una finestra che passa davanti toglie il fuoco a questa — e senza fuoco
    #    il browser NEGA la lock.  ⇒ Il fuoco si riprende, si aspetta, e SI
    #    SCRIVE se c'era: un caso non misurato non e' un caso rosso, e un banco
    #    che li confondesse accuserebbe il prodotto per una finestra altrui.
    for _ in range(6):
        c.chiama("Page.bringToFront")
        time.sleep(0.4)
        if c.valuta("document.hasFocus()") is True:
            break
    fuoco = c.valuta("document.hasFocus()")
    print("  fuoco alla pagina prima della lock:", fuoco)
    mouse("mousePressed", cx, cy, button="left", buttons=1, clickCount=1)
    mouse("mouseReleased", cx, cy, button="left", buttons=0, clickCount=1)
    time.sleep(1.0)
    prima_lock = c.valuta("JSON.stringify(window.REMOTIX.input_classico.stato())")
    lock = json.loads(prima_lock) if prima_lock else {}
    scena["lock"] = {"agganciato": lock.get("agganciato"),
                     "grezzo": lock.get("lock_grezzo"),
                     "fuoco": fuoco,
                     "ripieghi": lock.get("ripieghi")}
    print("  Pointer Lock:", json.dumps(scena["lock"], ensure_ascii=False))
    scarica()

    # -- F8: LA SATURAZIONE ALL'ULTIMO PIXEL, agganciati --------------------
    # ⛔ Agganciati il puntatore lo tiene la pagina, e si puo' spingere OLTRE il
    #    bordo: e' l'unica strada per cui un `1920` puo' nascere davvero, ed e'
    #    quella che chiude la sessione (`RCP.md` §7.3, rilievo R1.16).
    # ⚠ Sotto lock il cursore non si muove: quel che conta e' lo SPOSTAMENTO,
    #   cioe' la differenza fra due posizioni spedite.  Da (10,10) a (1400,760)
    #   sono ~1390×750 px CSS, che sulla vista di 641×361 valgono ~4160×2240
    #   pixel di tela: abbastanza per sbattere contro il bordo da qualunque
    #   punto si parta.
    c.valuta(VISTA % (641, 361))
    fase("F8-satura-alto")
    ag = c.valuta("window.REMOTIX.input_classico.stato().agganciato")
    raccolta.annota({"agganciato": ag, "vista": [641, 361]})
    mouse("mouseMoved", 10, 10, button="none", buttons=0)
    time.sleep(0.15)
    mouse("mouseMoved", 1400, 760, button="none", buttons=0)
    time.sleep(0.3)
    scarica()
    fase("F8-satura-basso")
    raccolta.annota({"agganciato": c.valuta(
        "window.REMOTIX.input_classico.stato().agganciato"), "vista": [641, 361]})
    mouse("mouseMoved", 10, 10, button="none", buttons=0)
    time.sleep(0.3)
    scarica()
    c.valuta(VISTA % (1361, 766))

    # -- F3: il fuoco perso con un modificatore e un pulsante premuti -------
    fase("F3-fuoco-tenuto")
    mouse("mousePressed", cx, cy, button="left", buttons=1, clickCount=1)
    tasto("rawKeyDown", "Control", "ControlLeft", 17, 2)
    time.sleep(0.5)
    scarica()
    fase("F3-fuoco-perso")
    # ⛔ IL FUOCO SI TOGLIE DAVVERO, con una scheda nuova che passa davanti.
    #    Un `window.blur()` chiamato da JavaScript non e' la stessa cosa: la
    #    lock si spegne su un evento del BROWSER, e falsificarlo misurerebbe il
    #    nostro gestore invece del caso vero.
    nuovo = c.chiama("Target.createTarget", url="about:blank")
    time.sleep(1.2)
    c.chiama("Target.closeTarget", targetId=nuovo["targetId"])
    time.sleep(0.8)
    scarica()

    # -- F9: la lettera accentata DIRETTA ------------------------------------
    # ⛔⭐ `web.md` §1.2 C prevede il caso concreto: «si arriva alla fase 4, si
    #    scopre che `^`+`e` non produce `ê` su nessun motore, si aggiunge il campo
    #    nascosto sopra la tela — e si perde la strada di disegno».  ⚠ Quella
    #    previsione vale per i tasti MORTI; su una disposizione italiana `à` e' un
    #    tasto DIRETTO, e `ev.key` la porta gia' fatta.  ⇒ Qui si misura quale
    #    metà del problema esiste davvero, invece di ereditare la previsione.
    fase("F9-accento-diretto")
    tasto("keyDown", "à", "Quote", 222, 0, "à")
    tasto("keyUp", "à", "Quote", 222, 0)
    time.sleep(0.35)
    scarica()

    stato = c.valuta("JSON.stringify(window.REMOTIX.input_classico.stato())")
    spediti = c.valuta("window.__b27 && window.__b27.spediti")
    errori = c.valuta("window.__b27 && window.__b27.errori")
    crudi = c.valuta("JSON.stringify(window.__b27.crudi)")
    scena["strumento"] = json.loads(crudi) if crudi else None
    if scena["strumento"]:
        print("  ⚙ lo strumento: %d mousemove consegnati, rotelle crude %s"
              % (len(scena["strumento"]["mosse"]),
                 scena["strumento"]["rotelle"]))
        print("    ultime mosse:", scena["strumento"]["mosse"][-6:])
    print("  spediti dalla pagina: %s · errori di spedizione: %s"
          % (spediti, errori))
    print("  stato del modo:", stato)
    time.sleep(0.6)
    s.shutdown()

    with open(registro, "w") as f:
        for r in raccolta.righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    casi = giudica(raccolta.righe, tela)
    scena["spediti_dalla_pagina"] = spediti
    scena["byte_ricevuti"] = raccolta.byte
    scena["stato_modo"] = json.loads(stato) if stato else None
    with open(esiti, "a") as f:
        f.write(json.dumps({"scena": scena, "casi": casi},
                           ensure_ascii=False) + "\n")
    rossi = [c_ for c_ in casi if c_["esito"] == "ROSSO"]
    # ⛔ «NON MISURATO» NON E' VERDE — `CODER.md` §4.6, «il silenzio non e' zero e
    #    il verde non e' vero».  Un riassunto che dicesse «verde su tutti» con
    #    due casi non misurati e' la peggiore delle prove, perche' da' fiducia.
    ignoti = [c_ for c_ in casi if c_["esito"] == "non-misurato"]
    for c_ in casi:
        print("  %-28s %-12s (%3d msg)  %s"
              % (c_["caso"], c_["esito"], c_["messaggi"], c_["perche"]))
    if rossi:
        print("⛔ %d casi ROSSI su %d (e %d non misurati)"
              % (len(rossi), len(casi), len(ignoti)))
    elif ignoti:
        print("⚠ nessun rosso, ma %d casi su %d NON SONO STATI MISURATI: %s"
              % (len(ignoti), len(casi), [c_["caso"] for c_ in ignoti]))
    else:
        print("⭐ VERDE su tutti i %d casi" % len(casi))
    return (1 if rossi else (2 if ignoti else 0)), scena, casi


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--gira", action="store_true")
    p.add_argument("--porta", type=int, default=7661)
    p.add_argument("--diagnosi", type=int, default=7662)
    p.add_argument("--esiti", default=os.path.join(QUI, "04-b27-esiti.jsonl"))
    p.add_argument("--registro",
                   default=os.path.join(QUI, "04-b27-registro.jsonl"))
    p.add_argument("--verdetto")
    a = p.parse_args()
    if a.certifica:
        return certifica()
    if a.verdetto:
        righe = [json.loads(r) for r in open(a.verdetto) if r.strip()]
        for c in giudica(righe):
            print("  %-28s %-6s (%3d msg)  %s"
                  % (c["caso"], c["esito"], c["messaggi"], c["perche"]))
        return 0
    if a.gira:
        stato, _, _ = gira(a.porta, a.diagnosi, a.esiti, a.registro)
        return stato
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
