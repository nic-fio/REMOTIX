#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b93-pieno — CHE COSA SUCCEDE QUANDO LA TABELLA E' PIENA, misurato OGGI.

    porta 8030 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6` (1105)
    albero `/media/REMOTIX/src/10a8-src` · lavoro `/media/REMOTIX/tmp/10a8`
    unita' `remotix-8030` · lucchetto GPU `10-a8`

    python3 banchi/10-b93-pieno.py --certifica    ⭐ senza rete e senza macchina
    bash    banchi/10-b93-lancia.sh               il giro vero

═══════════════════════════════════════════════════════════════════════════════
⛔ DA DOVE NASCE — una cura scritta e MAI VISTA SCATTARE
═══════════════════════════════════════════════════════════════════════════════

`PIANO.md` scrive il banco della fase 10 cosi': *«si satura il codificatore di
proposito e si verifica che l'undicesimo riceva `BUDGET_PIENO` — e che i dieci
che stavano lavorando non peggiorino»*.

⛔ Ma **prima** di scrivere `BUDGET_PIENO 0x06` bisogna sapere che cosa il
   prodotto fa OGGI, e oggi fa qualcosa: il rilievo **R9.3** ha separato due
   fatti che avevano lo stesso esito — «il posto di questo utente e' occupato»
   e «la tabella e' piena» — e la cura manda `SESSIONE_NON_SERVIBILE 0x0E` col
   dettaglio nel corpo invece del `CONGEDO 0x0F` che diceva a un utente senza
   nessuna sessione *«hai gia' una sessione attiva altrove»*.

⛔⛔ **Nessuno l'ha mai vista scattare.**  E questo progetto ha gia' scoperto due
     volte del *«codice presente, che sembrava giusto, e che non faceva
     niente»*.  ⇒ Questo banco esiste per farla scattare e guardarla.

═══════════════════════════════════════════════════════════════════════════════
⛔⭐⭐ IL TRUCCO, DICHIARATO IN TESTA COME SI DEVE
═══════════════════════════════════════════════════════════════════════════════

L'albero sulla macchina di prova e' compilato con **`MAX_ATTACCATE` piccolo**
(`10-b93-terreno.sh`, predefinito **2**), cosi' la tabella si riempie con due
clienti invece che con sedici sessioni grafiche vere.

⛔ **QUEL CHE SI MISURA E' IL COMPORTAMENTO AL RIEMPIMENTO, NON IL NUMERO.**
   Due non e' dieci e non e' sedici; nessuna riga di questo file pretende il
   contrario, e il numero vero e' un'altra misura di questa fase.

⚠ E `MAX_FIGLI` (`figlio.c:91`) resta a **16**: il commento accanto dichiara che
  «segue» `MAX_ATTACCATE`, ma sono due `#define` separati e nessuna riga li
  lega.  ⇒ Il banco misura anche la DIVERGENZA, invece di nasconderla
  allineandoli a mano.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE SETTE DOMANDE, e per ciascuna il predicato che sa dare rosso
═══════════════════════════════════════════════════════════════════════════════

 1. **quale motivo** riceve chi arriva a tabella piena, letto **sul filo**
    (`p_motivo_sul_filo`) — `0x0E` e' giusto, `0x0F` e' la bugia curata da R9.3;
 2. **il corpo porta il dettaglio?** (`p_dettaglio_nel_corpo`) — §8.2 lo IMPONE
    per `0x0E`, e `RCP.md` riga 2301: *ogni motivo DEVE essere mostrabile in una
    frase comprensibile*;
 3. **che frase mostra la PAGINA** (`p_frase_della_pagina`) — ⛔ letta da un
    Firefox VERO che si collega al prodotto, non dedotta dal codice del server;
 4. **chi era gia' dentro peggiora?** (`p_I1`) — `DECISIONI.md` §4.6-bis e
    l'invariante I1 lo vietano.  Fotogrammi/s, peggior secondo, ritardo fra
    fotogrammi, deriva ⛔ **e la quota di fotogrammi chiave**, che e' il
    MECCANISMO accanto al sintomo (`LEZIONI.md` §1.31);
 5. **il respinto lascia strascichi?** (`p_niente_strascichi`) — dieci rifiuti
    di fila, e si guarda se qualcosa cresce;
 6. **quanto in la' arriva prima di essere respinto** (`p_confine_del_rifiuto`)
    — ⛔ *rifiutare dopo aver acceso un desktop non e' rifiutare*;
 7. **e quando uno se ne va, il posto torna?** (`p_posto_torna`) — e in quanti
    secondi, nei due modi di andarsene: il commiato e la morte improvvisa.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ LE TRE COSE CHE RENDONO ONESTO QUESTO BANCO
═══════════════════════════════════════════════════════════════════════════════

 **a. IL METRO SI TARA PRIMA** (`LEZIONI.md` §1.33).  Tre tarature, e girano
    anche nel giro vero, non solo in `--certifica`:
      · T1 — il lettore del canale ritrova un `CONGEDO` NOTO scritto a mano in
        una traccia §11.1 fabbricata qui;
      · T2 — lo spezzettatore in finestre ritrova ritmi NOTI iniettati;
      · T3 — ⛔ **i due orologi**.  Il giornale dei fotogrammi ha l'orologio del
        CLIENTE (relativo al suo primo blocco), il registro ha quello del
        SERVER.  L'offset si ricava da un'ancora — il `SESSIONE` — e si
        VERIFICA con una **seconda** ancora indipendente: se le due non vanno
        d'accordo entro 200 ms, il banco **non giudica** le finestre.
        ⭐ Che i due orologi siano lo stesso hardware (il cliente gira DENTRO la
          macchina di prova) e' quel che rende possibile la taratura, e va
          saputo: da due macchine diverse questa misura non si farebbe cosi'.

 **b. LE FINESTRE HANNO UN'ANCORA CHE LE RENDE IMPOSSIBILI DA CONFONDERE.**
    ⛔ Il conto della sessione «prima» letto **dopo** il tentativo e' un verde
    per costruzione — la forma d'errore piu' comoda che ci sia.  ⇒
    `ancora_finestre()` verifica che OGNI fotogramma di «prima» sia arrivato
    prima dell'istante del primo tentativo e ogni fotogramma di «dopo» dopo
    l'ultimo, e si RIFIUTA se una sola riga sfora.  Il guasto G5 lo dimostra.

 **c. LA SOLLECITAZIONE SI CONTA** (`LEZIONI.md` §1.30).  Un rifiuto che non e'
    mai partito — parola sbagliata, indirizzo bannato, server spento — deve dare
    ⚠ **«non ho misurato»**, non ✅ «respinto correttamente»: e' la forma
    «silenzio invece di rosso» che in fase 9 ha prodotto nove difetti su nove.
    Il guasto G3 lo dimostra.

═══════════════════════════════════════════════════════════════════════════════
⚠ QUEL CHE QUESTO BANCO **NON** MISURA, dichiarato prima
═══════════════════════════════════════════════════════════════════════════════

 · ⚠ **Non misura il numero di sessioni che il ferro regge**: la tabella e' a 2
   per costruzione.  Il pixel/s del codificatore e' un'altra misura della fase.
 · ⚠ **Non misura `BUDGET_PIENO 0x06`**: oggi il prodotto non lo emette da
   nessuna parte.  L'ultima sezione e' un DISEGNO, non una misura — e la
   decisione la prende l'utente del progetto.
 · ⚠ **Non misura la rete**: nessun `netem`, ne' su `lo` ne' su `enp7s0`.  La
   linea e' quella che c'e', e chi confronta questi numeri con quelli della
   fase 9 deve saperlo.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import shlex
import struct
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# L'AMBIENTE — e il banco si rifiuta di misurare su un terreno che non e' suo
# ═══════════════════════════════════════════════════════════════════════════
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "8030"))
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10a8")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/10a8-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/10a8-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10a8")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
SCENA_BIN = os.environ.get("SCENA_BIN",
                           "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")
FUORI = os.environ.get("FUORI", "/tmp/10-b93")

# ⛔ I MIEI utenti, e nessun altro.  I due DENTRO riempiono la tabella, il terzo
#    e' il respinto — e dev'essere un utente DIVERSO, o `posto_prendi()`
#    prenderebbe la strada `POSTO_OCCUPATO` (0x0F) invece di quella della
#    tabella piena (0x0E): sono due rami diversi, e questo banco misura il
#    secondo.
DENTRO = [("provadec4", 1103), ("provadec5", 1104)]
RESPINTO = ("provadec6", 1105)
TUTTI = DENTRO + [RESPINTO]

# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, e non si toccano mai
#    (`LEZIONI.md` §1.26 — due banchi sulla stessa macchina non danno un rosso,
#    danno un numero plausibile).
VICINE = ["7700", "7710", "7720", "7730", "7900", "8010", "8020", "8040"]

CODEC_CHIESTO = os.environ.get("CODEC", "h264")
TELA = os.environ.get("TELA", "1920x1080")
MONITOR_ATTESO = os.environ.get("MONITOR", "Meta-0")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CATENA DI ROOT — la forma CURATA, e le due trappole che copre
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ **Un solo `sudo`, e la catena intera dentro la SUA `bash -c`.**  Se un `|`,
#    un `<` o un `>` restano fuori, li esegue la shell dell'utente e non root: il
#    file non si scrive, e «non ho letto» prende la faccia di «zero».
# ⛔ E niente redirect in coda: `printf … | sudo -S … < file` da' il FILE allo
#    stdin di `sudo`, che allora non riceve piu' la parola — e `|| echo 0`
#    stampa uno zero perfettamente plausibile (`09-b70-ritmo.py`, 23 ago 2026).
def catena_root(comando):
    return ("printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
            % (PAROLA_SUDO, shlex.quote(comando)))


def root(comando, tetto=300):
    """Torna `(rc, stdout, stderr)`.  ⚠ `rc != 0` NON e' un'eccezione: chi
       chiama deve poter distinguere «ha detto no» da «non ho potuto chiedere»."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                        catena_root(comando)],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def dentro(comando, tetto=300):
    """Un comando DENTRO il contenitore, da root."""
    return root("bash /media/REMOTIX/enter.sh --root %s" % shlex.quote(comando),
                tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I DUE OROLOGI — e il ponte fra loro, che e' una MISURA e non un'assunzione
# ═══════════════════════════════════════════════════════════════════════════
#
# Il registro del server scrive `HH:MM:SS.mmm` (`registro.c:35`); la traccia
# §11.1 del cliente scrive millisecondi **dal suo primo blocco**.  Sono due
# orologi diversi, e mescolarli darebbe finestre spostate di qualche secondo —
# cioe' un I1 verde o rosso a caso.
#
# ⭐ Sono pero' lo STESSO hardware: il cliente gira dentro la macchina di prova.
#    ⇒ Basta un offset, e l'offset si ricava da un'ANCORA visibile da tutt'e due
#    le parti.  ⛔ E si VERIFICA con una seconda ancora: un offset ricavato da
#    un'ancora sola non e' misurato, e' indovinato.
RE_ORA = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s")


def sod_dalla_riga(riga):
    """I secondi dall'inizio del giorno di una riga di registro, o `None`."""
    m = RE_ORA.match(riga)
    if not m:
        return None
    h, mi, s, ms = (int(x) for x in m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000.0


def sod_adesso_sul_server():
    """⛔ L'ora del SERVER, non la mia: il portatile e la macchina di prova sono
       due macchine, e i loro orologi non sono lo stesso orologio."""
    rc, out, _ = root("date '+%H:%M:%S.%N'")
    t = out.strip()
    if not re.match(r"^\d{2}:\d{2}:\d{2}\.\d+$", t):
        return None
    h, mi, resto = t.split(":")
    s, frac = resto.split(".")
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(frac[:3]) / 1000.0


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL LETTORE DEL CANALE DI CONTROLLO — spedito sulla macchina
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ **IL FORMATO NON SI RIDESCRIVE QUI.**  Magia, disposizione del blocco,
#    codici di `fine` e versi si importano da `01-b4-validatore.py`, che e'
#    l'ARBITRO di §11.1.  Due descrizioni dello stesso formato in due file sono
#    due descrizioni che divergono, ed e' gia' costato un giro intero (16 agosto
#    2026: il registratore scriveva `0x00 0x01` e l'arbitro pretendeva `0x00
#    0x02`, e OGNI traccia usciva «malformata»).
#
# ⚠ E questo lettore fa un mestiere che `09-b70-leggi.py` NON fa: quello riduce
#   il canale VIDEO al giornale dei fotogrammi, questo sfoglia il canale di
#   CONTROLLO e ne tira fuori i messaggi con tipo, corpo e istante.  Non c'e'
#   sovrapposizione, e nessuno dei due ricopia l'altro.
CANALE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b93-canale — dal `.rcpreg` di §11.1 ai MESSAGGI del canale di controllo.

Stampa in JSON: `{"esito": …, "blocchi": n, "messaggi": [ … ]}`.
Ogni messaggio: `{"verso": "client"|"server", "tipo": 0x000c, "nome": "CONGEDO",
                  "istante_ms": …, "corpo_hex": …, "motivo": …, "dettaglio": …}`.

⛔ `motivo` e `dettaglio` sono valorizzati SOLO per `CONGEDO` e `RESPINTO`, e
   `None` quando il corpo non basta a leggerli: un dettaglio vuoto e un
   dettaglio non letto non devono avere la stessa faccia (`LEZIONI.md` §1.9).
"""
import importlib.util, json, struct, sys

CANALE_CONTROLLO = 0x00
NOMI = {0x0001: "CIAO", 0x0002: "ECCOMI", 0x0003: "CREDENZIALI",
        0x0004: "AMMESSO", 0x0005: "RESPINTO", 0x0006: "ATTACCA",
        0x0007: "SESSIONE", 0x0008: "VISTA", 0x0009: "DISPOSIZIONE",
        0x000A: "CURSORE_FORMA", 0x000B: "ADATTA_TELA", 0x000C: "CONGEDO",
        0x000D: "RICHIEDI_CHIAVE", 0x000E: "TELA", 0x0011: "TERMINA_SESSIONE"}


def arbitro(percorso):
    spec = importlib.util.spec_from_file_location("b4arbitro", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def principale():
    traccia, validatore = sys.argv[1], sys.argv[2]
    A = arbitro(validatore)
    with open(traccia, "rb") as f:
        d = f.read()
    if len(d) < 16 or d[:8] != A.MAGIA:
        print(json.dumps({"esito": "NON HO NIENTE DA LEGGERE — la traccia non "
                                   "porta la magia di §11.1",
                          "primi8": d[:8].hex()}))
        return 3
    quanti, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    p, letti = 16, 0
    # (verso, stream) -> [byte accumulati, istante dell'ultimo pezzo]
    flussi = {}
    ordine = []
    # ⭐ L'istante dell'ULTIMO blocco di TUTTA la traccia, canale video
    #    compreso: e' la SECONDA ancora fra i due orologi, e senza di lui
    #    l'offset si ricaverebbe da un'ancora sola — cioe' si indovinerebbe.
    ultimo_ms = None
    for _ in range(quanti):
        if p + A.BLOCCO_BYTE > len(d):
            break
        verso, canale, fine, ist, stream, lung, nosc = struct.unpack(
            A.BLOCCO, d[p:p + A.BLOCCO_BYTE])
        p += A.BLOCCO_BYTE
        p += nosc * 40                       # (ini u32, quanti u32, impronta 32 B)
        carico = d[p:p + lung]
        p += lung
        letti += 1
        if ultimo_ms is None or ist > ultimo_ms:
            ultimo_ms = ist
        if canale != CANALE_CONTROLLO:
            continue
        k = (verso, stream)
        if k not in flussi:
            flussi[k] = {"byte": bytearray(), "istanti": []}
            ordine.append(k)
        # ⚠ L'istante si tiene PER OGNI byte aggiunto, cosi' il messaggio porta
        #   l'istante del blocco in cui il suo ULTIMO byte e' arrivato: e' il
        #   momento in cui chi legge poteva davvero averlo.
        base = len(flussi[k]["byte"])
        flussi[k]["byte"] += carico
        flussi[k]["istanti"].append((base + len(carico), ist))
    messaggi = []
    for k in ordine:
        verso, stream = k
        b = bytes(flussi[k]["byte"])
        istanti = flussi[k]["istanti"]
        i = 0
        while i + 6 <= len(b):
            tipo, lung = struct.unpack("!HI", b[i:i + 6])
            if i + 6 + lung > len(b):
                break
            corpo = b[i + 6:i + 6 + lung]
            fine_byte = i + 6 + lung
            ist = None
            for limite, quando in istanti:
                if limite >= fine_byte:
                    ist = quando
                    break
            m = {"verso": "server" if verso == A.SERVER else "client",
                 "stream": stream, "tipo": tipo,
                 "nome": NOMI.get(tipo, "0x%04x" % tipo),
                 "istante_ms": ist, "lunghezza": lung,
                 "corpo_hex": corpo.hex(), "motivo": None, "dettaglio": None,
                 "dettaglio_letto": False}
            if tipo in (0x000C, 0x0005) and lung >= 1:
                m["motivo"] = corpo[0]
                if tipo == 0x000C:
                    if lung >= 3:
                        n = struct.unpack("!H", corpo[1:3])[0]
                        if 3 + n <= lung:
                            m["dettaglio"] = corpo[3:3 + n].decode("utf-8", "replace")
                            m["dettaglio_letto"] = True
            messaggi.append(m)
            i = fine_byte
    print(json.dumps({"esito": "letto", "blocchi": letti,
                      "orologio": A.OROLOGIO.get(orologio, orologio),
                      "ultimo_blocco_ms": ultimo_ms,
                      "messaggi": messaggi}))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
'''


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL FABBRICANTE DI TRACCE — serve alla TARATURA e ai GUASTI
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ E scrive col REGISTRATORE del cliente, non con una sua idea del formato:
#    `01-b3-cliente.py` porta `Registratore`, e usarlo qui vuol dire che se il
#    formato cambia questa taratura se ne accorge invece di certificare un
#    lettore contro un fabbricante sbagliato tutti e due allo stesso modo.
def fabbrica_traccia(percorso, messaggi, cliente):
    """`messaggi` = [(verso, tipo, corpo_bytes, istante_ms), …]."""
    r = cliente.Registratore()
    r.stream = 4
    for verso, tipo, corpo, ist in messaggi:
        quadro = struct.pack("!HI", tipo, len(corpo)) + corpo
        r.aggiungi(verso, quadro, istante=ist)
    r.scrivi(percorso)


def corpo_congedo(motivo, dettaglio):
    b = dettaglio.encode("utf-8")
    return bytes([motivo]) + struct.pack("!H", len(b)) + b


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ANCORA DELLE FINESTRE — la riga che rende impossibile il verde comodo
# ═══════════════════════════════════════════════════════════════════════════
def ancora_finestre(finestre, t_ini, t_fine):
    """⛔ Verifica che le tre finestre siano quelle che dicono di essere.

    `finestre` = `{"prima": [fotogrammi], "durante": […], "dopo": […]}`, con
    ogni fotogramma che porta `sod` — il suo istante sull'orologio del SERVER.

    Torna `[]` se tutto regge, altrimenti l'elenco dei guai.  ⛔ Un guaio qui
    NON e' un rosso sul prodotto: e' un banco che stava per giudicare una cosa
    diversa da quella che dichiara, ⇒ chi lo riceve **si rifiuta**.

    ⚠ Il caso che questa funzione esiste per rendere impossibile: leggere il
      conto della sessione «prima» **dopo** il tentativo.  Con le finestre
      calcolate da un offset sbagliato — o da un `t_ini` preso male — quel conto
      arriva lo stesso, ha l'aria giusta, e assolve chiunque.
    """
    guai = []
    if t_ini is None or t_fine is None:
        return ["gli istanti del tentativo non sono stati misurati: senza, "
                "«prima» e «dopo» non sono definibili"]
    if not (t_fine >= t_ini):
        guai.append("il tentativo finisce (%.3f) prima di cominciare (%.3f)"
                    % (t_fine, t_ini))
    for nome, atteso in (("prima", "<"), ("durante", "="), ("dopo", ">")):
        f = finestre.get(nome) or []
        if not f:
            guai.append("la finestra «%s» e' VUOTA: non c'e' niente da "
                        "confrontare" % nome)
            continue
        fuori = 0
        for x in f:
            t = x.get("sod")
            if t is None:
                fuori += 1
                continue
            if atteso == "<" and not (t < t_ini):
                fuori += 1
            elif atteso == ">" and not (t > t_fine):
                fuori += 1
            elif atteso == "=" and not (t_ini <= t <= t_fine):
                fuori += 1
        if fuori:
            guai.append("⛔ %d fotogrammi su %d della finestra «%s» stanno "
                        "FUORI dal suo intervallo (tentativo %.3f → %.3f): "
                        "questa finestra non e' quella che dichiara"
                        % (fuori, len(f), nome, t_ini, t_fine))
    # ⛔ E le tre non si sovrappongono: due finestre che condividono un
    #    fotogramma non sono un prima e un dopo, sono lo stesso momento contato
    #    due volte.
    chiavi = {}
    for nome in ("prima", "durante", "dopo"):
        for x in finestre.get(nome) or []:
            n = x.get("numero")
            if n in chiavi and chiavi[n] != nome:
                guai.append("⛔ il fotogramma %s sta in «%s» e in «%s»: le "
                            "finestre si sovrappongono" % (n, chiavi[n], nome))
                break
            chiavi[n] = nome
    return guai


def spezza_in_finestre(giornale, offset, t_ini, t_fine, largo, guardia):
    """Dal giornale di un cliente alle tre finestre, sull'orologio del SERVER.

    `offset` porta `arrivo_ms` (orologio del cliente) sui secondi del giorno del
    server.  ⛔ Se `offset` e' `None` non si indovina: si torna `None`, e chi
    riceve si rifiuta di giudicare.
    """
    if offset is None or t_ini is None or t_fine is None:
        return None
    fuori = {"prima": [], "durante": [], "dopo": []}
    for f in giornale:
        g = dict(f)
        g["sod"] = offset + f["arrivo_ms"] / 1000.0
        t = g["sod"]
        if t_ini - guardia - largo <= t < t_ini - guardia:
            fuori["prima"].append(g)
        elif t_ini <= t <= t_fine:
            fuori["durante"].append(g)
        elif t_fine + guardia < t <= t_fine + guardia + largo:
            fuori["dopo"].append(g)
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I PREDICATI — scritti PRIMA, e ognuno sa dare rosso
# ═══════════════════════════════════════════════════════════════════════════
#
#   (True,  perche)  l'atteso ha retto
#   (False, perche)  ⛔ rosso
#   (None,  perche)  ⚠ NON GIUDICO — e non e' un verde educato: e' un esito suo
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)

MOTIVO_GIUSTO = 0x0E          # SESSIONE_NON_SERVIBILE — §8.2, rilievo R9.3
MOTIVO_BUGIARDO = 0x0F        # GIA_ATTIVA_REMOTA — la bugia che R9.3 ha curato
MOTIVO_BUDGET = 0x06          # BUDGET_PIENO — dichiarato, mai emesso

# ⛔ Le soglie di I1 sono SCELTE MIE e si dichiarano: non sono nel prodotto e non
#    sono nei documenti.  I numeri grezzi si stampano sempre accanto, cosi' chi
#    legge puo' non essere d'accordo con la soglia senza perdere la misura.
I1_FPS = 0.90            # il ritmo medio non scende sotto il 90% di «prima»
I1_PEGGIOR_SECONDO = 0.75  # il peggior secondo non scende sotto il 75%
I1_P95 = 1.50            # il ritardo fra fotogrammi non piu' di 1,5 volte
I1_DERIVA_MS = 100.0     # la deriva non peggiora di piu' di 100 ms
I1_QUOTA_CHIAVI = 0.02   # ⭐ IL MECCANISMO: la quota di chiavi non sale di 2 punti


def p_ha_morso(tentativi):
    """⛔⛔ IL PREDICATO DELLA SOLLECITAZIONE — `LEZIONI.md` §1.30, e viene PRIMA
       di ogni giudizio sul motivo.

    Un cliente che non e' mai arrivato all'`ATTACCA` — parola sbagliata,
    indirizzo bannato, server spento, aioquic che manca — **non e' stato
    respinto per posto pieno**.  ⛔ E chiamarlo «respinto correttamente» e' la
    forma «silenzio invece di rosso» che in fase 9 ha prodotto nove difetti su
    nove: il banco resta verde e la cura non e' mai stata esercitata.

    ⇒ Tre esiti, non due: ha morso, non ha morso, o non lo so.
    """
    if not tentativi:
        return _muto("nessun tentativo e' stato fatto")
    senza = [t for t in tentativi if t.get("arrivato_a") is None]
    if senza:
        return _muto("%d tentativi su %d non dicono dove sono arrivati"
                     % (len(senza), len(tentativi)))
    non_morsi = [t for t in tentativi if t["arrivato_a"] != "ATTACCA"]
    if non_morsi:
        quali = ", ".join(sorted({str(t["arrivato_a"]) for t in non_morsi}))
        return _muto("⛔ NON HO MISURATO IL POSTO PIENO: %d tentativi su %d si "
                     "sono fermati PRIMA dell'ATTACCA (%s).  ⚠ Questo NON e' "
                     "«respinto correttamente»: la strada della tabella piena "
                     "non e' stata nemmeno imboccata"
                     % (len(non_morsi), len(tentativi), quali))
    return _si("tutti e %d i tentativi sono arrivati fino all'ATTACCA: la "
               "strada della tabella piena e' stata percorsa" % len(tentativi))


def p_motivo_sul_filo(tentativi):
    """⛔ QUALE MOTIVO, letto sul FILO e non nel registro del server.

    `0x0E SESSIONE_NON_SERVIBILE` e' il motivo giusto (§8.2, rilievo R9.3).
    `0x0F GIA_ATTIVA_REMOTA` sarebbe la bugia: dice a un utente che non ha
    nessuna sessione da nessuna parte che ne ha gia' una altrove.
    """
    if not tentativi:
        return _muto("nessun tentativo")
    senza = [t for t in tentativi if t.get("motivo") is None]
    if senza:
        return _muto("%d tentativi su %d non portano nessun motivo LETTO SUL "
                     "FILO: la traccia §11.1 non si e' letta, e il registro del "
                     "server non e' il filo" % (len(senza), len(tentativi)))
    motivi = sorted({t["motivo"] for t in tentativi})
    if motivi == [MOTIVO_GIUSTO]:
        return _si("tutti e %d i tentativi hanno ricevuto CONGEDO %#04x "
                   "SESSIONE_NON_SERVIBILE — §8.2, ed e' la cura di R9.3 vista "
                   "scattare" % (len(tentativi), MOTIVO_GIUSTO))
    if MOTIVO_BUGIARDO in motivi:
        return _no("⛔⛔ LA BUGIA DI R9.3 E' VIVA: sul filo e' arrivato "
                   "%#04x GIA_ATTIVA_REMOTA, e questi utenti non hanno nessuna "
                   "sessione altrove.  Motivi visti: %s"
                   % (MOTIVO_BUGIARDO, [hex(m) for m in motivi]))
    return _no("⛔ motivo inatteso sul filo: %s (atteso solo %#04x)"
               % ([hex(m) for m in motivi], MOTIVO_GIUSTO))


def p_dettaglio_nel_corpo(tentativi):
    """⛔ §8.2: `0x0E` **DEVE** portare il dettaglio nel corpo.

    ⚠ E il dettaglio NON si mostra all'utente (§8.2, ultima riga): e' per chi
      diagnostica.  ⇒ Qui si pretende che ci SIA e che dica qualcosa; la frase
      dell'utente e' un'altra misura (`p_frase_della_pagina`).
    """
    if not tentativi:
        return _muto("nessun tentativo")
    non_letti = [t for t in tentativi if not t.get("dettaglio_letto")]
    if non_letti:
        return _muto("%d tentativi su %d hanno un corpo che non si e' potuto "
                     "sfogliare: «vuoto» e «non letto» sono due fatti diversi"
                     % (len(non_letti), len(tentativi)))
    vuoti = [t for t in tentativi if not (t.get("dettaglio") or "").strip()]
    if vuoti:
        return _no("⛔ %d tentativi su %d portano un CONGEDO %#04x col corpo "
                   "SENZA dettaglio: §8.2 lo IMPONE, e senza di quello nel "
                   "registro resta un numero" % (len(vuoti), len(tentativi),
                                                 MOTIVO_GIUSTO))
    testi = sorted({t["dettaglio"] for t in tentativi})
    return _si("il dettaglio c'e' in tutti e %d, e dice: «%s»"
               % (len(tentativi), "» · «".join(testi)))


def p_motivo_anche_nel_codice(tentativi, capsula=None):
    """⛔⛔ LA SECONDA STRADA — `RCP.md` §3.1 punto 3.

    *«DEVE chiudere la sessione WebTransport con il codice d'errore applicativo
    pari al codice del motivo di §8.2»*, e il riquadro dice perche':

    > ⭐ *Il terzo punto e' quello che salva le diagnosi: se il congedo non
    > arriva — perche' lo stream era rotto, perche' il messaggio era illeggibile
    > — il motivo viaggia comunque, dentro la chiusura della sessione.  In v1 il
    > server scriveva «congedo il client» e il client leggeva «errore di rete»
    > per tre fasi.*

    ⚠ E §3.1 chiude cosi': *«Il codice 0 significa "chiusura senza motivo" e NON
      DEVE essere usato»*.  ⇒ Uno zero qui non e' un dettaglio: e' la strada di
      riserva che non c'e'.

    ⛔ E si legge DAL LATO CHE RICEVE — la riga `[wt]` che il cliente stampa
       quando la capsula di chiusura arriva — perche' e' il solo posto da cui si
       possa dire che il motivo e' ARRIVATO, e non solo che e' partito.
    """
    if not tentativi:
        return _muto("nessun tentativo")
    letti = [t for t in tentativi if t.get("codice_wt") is not None]
    if not letti:
        # ⚠ E qui `None` NON e' «zero»: puo' voler dire che la capsula non e'
        #   mai arrivata (⛔ il difetto) oppure che il cliente non l'ha
        #   stampata (⚠ il banco).  ⇒ Si guarda il LATO CHE MANDA prima di
        #   accusare, e sono due conti diversi nel registro del server:
        #   quante volte la chiusura e' stata **armata** e quante volte la
        #   capsula e' stata **messa in coda** davvero.
        quic = sorted({t.get("codice_quic") for t in tentativi})
        c = capsula or {}
        arm, spe = c.get("rimandate"), c.get("spedite")
        if arm is None or spe is None:
            return _muto("nessun tentativo porta un codice di chiusura della "
                         "SESSIONE WebTransport letto sul filo, e non ho letto "
                         "i conti del lato che manda: non giudico.  ⚠ I codici "
                         "QUIC visti sono %s, ma quello e' un ALTRO piano "
                         "(§3.1, rilievo R1.4)" % quic)
        if arm > 0 and spe == 0:
            return _no("⛔⛔ LA SECONDA STRADA DI §3.1 NON PARTE.  Il server ha "
                       "ARMATO la chiusura della sessione %d volte e la capsula "
                       "e' finita in coda **%d** volte; il cliente non ha visto "
                       "nessun codice e la connessione QUIC e' terminata con %s. "
                       "⭐ Il MECCANISMO: `chiudi_sessione()` RIMANDA la capsula "
                       "di 500 ms (`WT_ATTESA_CHIUSURA_NS`) perche' un browser "
                       "non butti il `CONGEDO`, e un client che si stacca appena "
                       "letto il `CONGEDO` se ne va prima.  ⇒ Resta UNA strada "
                       "sola, e §3.1 ne vuole due" % (arm, spe, quic))
        return _muto("nessun codice letto sul filo, ma il lato che manda dice "
                     "armate %s / spedite %s: non giudico" % (arm, spe))
    if len(letti) != len(tentativi):
        return _muto("solo %d tentativi su %d portano il codice della sessione: "
                     "non giudico su meta' misura" % (len(letti), len(tentativi)))
    codici = sorted({t["codice_wt"] for t in letti})
    if codici == [MOTIVO_GIUSTO]:
        return _si("la sessione WebTransport si chiude con %#04x in tutti e %d: "
                   "le due strade di §3.1 dicono la stessa cosa"
                   % (MOTIVO_GIUSTO, len(letti)))
    if 0 in codici:
        return _no("⛔⛔ §3.1: la sessione si chiude col codice **0**, e §3.1 dice "
                   "che «NON DEVE essere usato» — e' la strada di riserva che "
                   "non c'e'.  Codici visti: %s" % [hex(c) for c in codici])
    return _no("⛔ le due strade di §3.1 NON dicono la stessa cosa: il CONGEDO "
               "porta %#04x e la chiusura della sessione %s"
               % (MOTIVO_GIUSTO, [hex(c) for c in codici]))


def p_frase_della_pagina(pagina):
    """⛔ CHE FRASE LEGGE L'UTENTE — letta da un Firefox VERO, non dedotta.

    ⚠ La pagina costruisce la frase dal MOTIVO, con la sua tabella
      (`src/pagina.html`, `const MOTIVO`).  ⛔ Tre esiti diversi da distinguere:
        · una frase che descrive il caso;
        · una frase GENERICA — l'utente non sa che cosa fare;
        · ⛔ una frase FALSA — e' il difetto di R9.3 visto dal lato dell'utente.
    """
    if not pagina or pagina.get("frase") is None:
        return _muto("la pagina non e' stata guardata (o non ha detto niente): "
                     "%s" % (pagina or {}).get("perche", "senza spiegazione"))
    frase = pagina["frase"].strip()
    if not frase:
        return _no("⛔ la pagina non mostra NESSUNA frase: §8.2 vuole che ogni "
                   "motivo sia mostrabile in una frase comprensibile")
    # ⛔ Le frasi che sarebbero FALSE per questo caso: dicono all'utente che ha
    #    gia' una sessione, e non ne ha nessuna.
    for bugia in ("gia' collegato", "già collegato", "altro client",
                  "sessione attiva altrove", "altro dispositivo"):
        if bugia in frase.lower():
            return _no("⛔⛔ LA PAGINA MENTE: mostra «%s» a un utente che non ha "
                       "nessuna sessione da nessuna parte" % frase)
    if pagina.get("motivo") is not None and pagina["motivo"] != MOTIVO_GIUSTO:
        return _no("⛔ la pagina ha costruito la frase dal motivo %#04x, non da "
                   "%#04x: «%s»" % (pagina["motivo"], MOTIVO_GIUSTO, frase))
    return _si("la pagina mostra: «%s»" % frase)


def _q(n, chiave):
    return (n or {}).get(chiave)


def p_I1(prima, durante, dopo, guai_ancora):
    """⛔⛔ CHI ERA GIA' DENTRO NON PEGGIORA — `DECISIONI.md` §4.6-bis, I1.

    *«Non si fa degradare chi sta gia' lavorando per far entrare chi arriva.
    Sarebbe la scelta apparentemente gentile, ma punisce in silenzio chi non ha
    fatto niente.»*  ⚠ Qui chi arriva NON entra — viene respinto — e la domanda
    e' se il solo TENTATIVO costa qualcosa a chi c'era.

    ⭐ E si guardano CINQUE grandezze, non una, perche' il sintomo e il
       meccanismo non arrivano insieme (`LEZIONI.md` §1.31):
         · il ritmo medio             — quando l'utente se ne accorge;
         · il PEGGIOR SECONDO         — quel che l'utente vede davvero;
         · il ritardo p95 fra fotogrammi;
         · la deriva;
         · ⭐ **la quota di fotogrammi CHIAVE** — il meccanismo: le chiavi
           salgono cinque volte prima che il ritmo scenda.
    """
    if guai_ancora:
        return _muto("⛔ NON GIUDICO: l'ancora delle finestre si e' rifiutata — "
                     + " · ".join(guai_ancora))
    for nome, n in (("prima", prima), ("durante", durante), ("dopo", dopo)):
        if not n or n.get("esito") != "misurato":
            return _muto("la finestra «%s» non ha niente da giudicare: %s"
                         % (nome, (n or {}).get("esito", "non c'e'")))
    guai, bene = [], []

    def confronta(etichetta, chiave, verso, soglia, assoluta=False):
        a, b = _q(prima, chiave), _q(durante, chiave)
        if a is None or b is None:
            guai.append("«%s» non e' stato letto in una delle due finestre"
                        % etichetta)
            return
        if verso == "giu":       # b non deve scendere sotto soglia*a
            ok = b >= soglia * a
            reg = "%s: prima %.2f → durante %.2f (soglia %.0f%% = %.2f)" % (
                etichetta, a, b, soglia * 100, soglia * a)
        elif verso == "su":      # b non deve salire sopra soglia*a
            ok = b <= soglia * a
            reg = "%s: prima %.2f → durante %.2f (tetto %.2f)" % (
                etichetta, a, b, soglia * a)
        else:                    # differenza assoluta
            ok = abs(b) <= abs(a) + soglia
            reg = "%s: prima %.1f → durante %.1f (tetto %.1f)" % (
                etichetta, a, b, abs(a) + soglia)
        (bene if ok else guai).append(("⭐ " if ok else "⛔ ") + reg)

    confronta("fotogrammi/s", "fps", "giu", I1_FPS)
    confronta("peggior secondo", "fps_finestra_min", "giu", I1_PEGGIOR_SECONDO)
    confronta("ritardo p95 fra fotogrammi (ms)", "intervallo_p95_ms", "su", I1_P95)
    confronta("deriva a fine finestra (ms)", "deriva_fine_ms", "abs", I1_DERIVA_MS)
    # ⭐ IL MECCANISMO, e ha una soglia sua perche' e' una quota, non un rapporto.
    qa, qb = _q(prima, "quota_delta"), _q(durante, "quota_delta")
    if qa is None or qb is None:
        guai.append("la quota di fotogrammi chiave non e' stata letta")
    else:
        chiavi_a, chiavi_b = 1 - qa, 1 - qb
        if chiavi_b <= chiavi_a + I1_QUOTA_CHIAVI:
            bene.append("⭐ quota di CHIAVI: prima %.4f → durante %.4f "
                        "(tetto %.4f)" % (chiavi_a, chiavi_b,
                                          chiavi_a + I1_QUOTA_CHIAVI))
        else:
            guai.append("⛔⛔ IL MECCANISMO: la quota di CHIAVI sale da %.4f a "
                        "%.4f (tetto %.4f) — `LEZIONI.md` §1.31, si vede cinque "
                        "volte prima del sintomo"
                        % (chiavi_a, chiavi_b, chiavi_a + I1_QUOTA_CHIAVI))
    # ⚠ E i buchi: un fotogramma partito e non arrivato non e' un ritmo piu'
    #   basso, e' una perdita.
    ba, bb = _q(prima, "buchi_numero"), _q(durante, "buchi_numero")
    if ba is not None and bb is not None:
        if bb <= ba:
            bene.append("⭐ buchi nella numerazione: prima %d → durante %d" % (ba, bb))
        else:
            guai.append("⛔ buchi nella numerazione: prima %d → durante %d" % (ba, bb))
    if guai:
        return _no("I1 VIOLATA — " + " · ".join(guai)
                   + (" || quel che ha retto: " + " · ".join(bene) if bene else ""))
    return _si("I1 regge su tutte e sei le grandezze — " + " · ".join(bene))


def p_niente_strascichi(scatti):
    """⛔ IL RESPINTO LASCIA STRASCICHI? — dieci rifiuti di fila.

    ⚠ *Un difetto che si vede solo alla decima e' il difetto che l'utente
      trovera'.*  ⇒ Si guardano le grandezze che CRESCONO, non quelle che
      cambiano.

    ⛔⛔ E il confronto parte dalla fotografia scattata **dopo il PRIMO
        rifiuto**, non da prima di tutto: quel che il primo rifiuto mette in
        piedi — un figlio, una sessione grafica — non e' uno strascico della
        RIPETIZIONE, e' il CONFINE del rifiuto, e lo giudica
        `p_confine_del_rifiuto()`.  ⚠ Mescolare le due domande darebbe un rosso
        solo che non dice quale delle due e' successa.
    """
    if len(scatti) < 3:
        return _muto("meno di tre fotografie: non c'e' una tendenza da guardare")
    guai, bene = [], []
    for chiave, umano, tolleranza in (
            ("posti_presi_dal_respinto", "posti PRESI dall'utente respinto", 0),
            ("figli", "figli vivi di QUESTO server", 0),
            ("gnome_respinto", "sessioni grafiche dell'utente respinto", 0),
            ("proc_respinto", "processi dell'utente respinto", 2),
            ("fd", "descrittori aperti dal server", 8),
            ("rss_kb", "memoria del server (kB)", 4096)):
        v = [s.get(chiave) for s in scatti]
        if any(x is None for x in v):
            guai.append("«%s» non e' stato letto in tutte le fotografie: uno "
                        "zero che vuol dire «non ho letto» qui assolverebbe"
                        % umano)
            continue
        # ⛔⛔ E LA CRESCITA SI GUARDA NELLA **SECONDA META'** DELLA SERIE.
        #
        #     `[M]` 24 agosto 2026, primo giro: `processi dell'utente respinto`
        #     faceva `[15, 42, 41, 41, …, 41]` — e non e' una perdita che si
        #     accumula, e' **la sessione grafica del primo rifiuto che finisce
        #     di accendersi**.  ⛔ Un gradino che avviene UNA volta e una
        #     perdita che si ripete a ogni rifiuto hanno lo stesso segno se si
        #     guardano solo il primo e l'ultimo valore, e sono due difetti
        #     diversissimi: il gradino lo giudica `p_confine_del_rifiuto()`.
        #     ⇒ Se la ripetizione costa qualcosa, costa anche dal quinto
        #       rifiuto al decimo.  Se non cresce li', non e' la ripetizione.
        meta = len(v) // 2
        cresciuta = v[-1] - v[meta]
        if cresciuta > tolleranza:
            guai.append("⛔ %s CRESCE nella seconda meta': %s (da %s a %s, "
                        "tolleranza %s)" % (umano, v, v[meta], v[-1], tolleranza))
        else:
            bene.append("⭐ %s: %s (seconda meta': %s → %s)"
                        % (umano, v, v[meta], v[-1]))
    if guai:
        return _no("STRASCICHI — " + " · ".join(guai)
                   + (" || fermo: " + " · ".join(bene) if bene else ""))
    return _si("dopo %d rifiuti di fila non cresce niente — " % len(scatti)
               + " · ".join(bene))


def p_confine_del_rifiuto(confine):
    """⛔⛔ DOVE STA IL CONFINE — *rifiutare dopo aver acceso un desktop non e'
       rifiutare*.

    ⚠ Questo predicato non ha un «giusto» scritto da nessuna parte: nessun
      documento dice dove il rifiuto DEVE cadere.  ⇒ Da' rosso su una sola cosa,
      che e' un fatto e non un'opinione: se il respinto lascia dietro di se' una
      SESSIONE GRAFICA ACCESA, il server ha speso il ferro per chi non e'
      entrato, e nessuno la spegne.
    """
    if not confine or confine.get("autenticato") is None:
        return _muto("il confine non e' stato misurato")
    passi = []
    for chiave, umano in (("autenticato", "PAM ha detto si'"),
                          ("figlio_nato", "un figlio e' NATO"),
                          ("sessione_grafica", "una sessione grafica si e' ACCESA"),
                          ("palco_acceso", "il palco ha consegnato un fotogramma")):
        v = confine.get(chiave)
        passi.append("%s: %s" % (umano, {True: "SI", False: "no",
                                         None: "non letto"}[v]))
    dove = " · ".join(passi)
    if confine.get("sessione_grafica") is None:
        return _muto("non ho letto se una sessione grafica si sia accesa — " + dove)
    if confine.get("sessione_grafica"):
        return _no("⛔⛔ IL RIFIUTO ARRIVA DOPO IL DESKTOP: " + dove
                   + " ⇒ il server ha acceso una sessione grafica per un utente "
                     "che poi ha respinto, e quella sessione RESTA (invariante "
                     "I4: il palco sopravvive al client)")
    return _si("il rifiuto cade prima della sessione grafica — " + dove)


def p_posto_torna(uscite):
    """⛔ E QUANDO UNO SE NE VA, IL POSTO TORNA?

    Due modi di andarsene, e sono diversi:
      · **il commiato** — il client manda `CONGEDO` e il posto si libera SUBITO
        (`congeda()` chiama `posto_lascia()`);
      · **la morte improvvisa** — il filo cade senza dire niente, e il posto
        resta del fantasma finche' `rcp_tempo()` non lo stacca per silenzio
        (`SILENZIO` = 30 000 ms in `rcp.c:263`).  ⚠ Lo SFRATTO di §4.4 NON aiuta
        qui: vale solo **fra client dello stesso utente**, e chi aspetta e' un
        utente diverso.
    """
    if not uscite:
        return _muto("nessuna uscita provata")
    guai, bene = [], []
    for u in uscite:
        nome, atteso, misurato = u["come"], u.get("atteso_s"), u.get("secondi")
        if misurato is None:
            guai.append("⚠ «%s»: il respinto NON e' rientrato entro il tetto "
                        "(%s s) — o non l'ho misurato" % (nome, u.get("tetto_s")))
            continue
        if atteso is not None and misurato > atteso:
            guai.append("⛔ «%s»: il posto e' tornato dopo %.2f s, oltre "
                        "l'atteso di %.1f s" % (nome, misurato, atteso))
        else:
            bene.append("⭐ «%s»: il posto e' tornato dopo %.2f s" % (nome, misurato))
    if guai:
        return _no("IL POSTO — " + " · ".join(guai)
                   + (" || " + " · ".join(bene) if bene else ""))
    return _si(" · ".join(bene))


def p_due_numeri(numeri):
    """⚠ `MAX_ATTACCATE` e `MAX_FIGLI` sono due `#define` separati, e il secondo
       DICHIARA di seguire il primo.

    ⛔ Se non lo segue e' un difetto, e va detto: uno dei due si riempie prima e
       l'altro non se ne accorge.  ⇒ Il rosso qui non e' «il numero e' 2 invece
       di 16»: e' «i due numeri divergono e nessuna riga di codice li lega».
    """
    a, f = numeri.get("max_attaccate"), numeri.get("max_figli")
    if a is None or f is None:
        return _muto("non ho letto i due numeri dai sorgenti sulla macchina")
    if a == f:
        return _si("MAX_ATTACCATE = MAX_FIGLI = %d" % a)
    return _no("⛔ MAX_ATTACCATE = %d ma MAX_FIGLI = %d: il commento di "
               "`figlio.c:91` dice che il secondo segue il primo, e NESSUNA "
               "riga lo fa.  ⇒ La tabella dei posti si riempie a %d mentre la "
               "tabella dei figli ne accetta ancora %d, e i figli in piu' "
               "nascono per utenti che verranno respinti" % (a, f, a, f - a))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA TARATURA DEL METRO — `LEZIONI.md` §1.33, e gira SEMPRE
# ═══════════════════════════════════════════════════════════════════════════
def _fab_giornale(quanti, fps, t0_ms=0, chiave_ogni=0, byte=20000,
                  numero0=0, deriva_per_fot=0.0):
    """Un giornale di fotogrammi NOTO, per tarare la riduzione."""
    g = []
    passo = 1000.0 / fps
    for i in range(quanti):
        arrivo = t0_ms + i * passo
        g.append({"numero": numero0 + i,
                  "chiave": bool(chiave_ogni) and (i % chiave_ogni == 0),
                  "tipo": 0x0301 if (chiave_ogni and i % chiave_ogni == 0) else 0x0302,
                  "codec": 3, "l": 1920, "a": 1080, "byte": byte,
                  "istante_us": int((t0_ms + i * passo - deriva_per_fot * i) * 1000),
                  "arrivo_ms": arrivo})
    return g


def taratura(B70, cliente, verboso=True):
    """⛔ Si inietta un valore NOTO e si verifica che il metro lo ritrovi.

    Torna `(tutte_ok, righe)`.  ⛔ Se una taratura fallisce il banco NON misura:
    un metro non tarato produce numeri, non misure.
    """
    righe, ok = [], True

    # T1 — il lettore del canale ritrova un CONGEDO noto.
    perc = os.path.join(FUORI, "taratura.rcpreg")
    os.makedirs(FUORI, exist_ok=True)
    dettaglio_noto = "il registro delle sessioni di questo server e' pieno"
    fabbrica_traccia(perc, [
        (cliente.CLIENT, 0x0001, b"\x00\x01", 0),
        (cliente.SERVER, 0x0002, b"\x00\x01", 5),
        (cliente.SERVER, 0x000C, corpo_congedo(MOTIVO_GIUSTO, dettaglio_noto), 42),
    ], cliente)
    letto = leggi_canale_qui(perc)
    congedi = [m for m in letto.get("messaggi", []) if m["nome"] == "CONGEDO"]
    if (len(congedi) == 1 and congedi[0]["motivo"] == MOTIVO_GIUSTO
            and congedi[0]["dettaglio"] == dettaglio_noto
            and congedi[0]["istante_ms"] == 42):
        righe.append("⭐ T1 il lettore del canale ritrova il CONGEDO %#04x "
                     "iniettato, col dettaglio e l'istante giusti" % MOTIVO_GIUSTO)
    else:
        ok = False
        righe.append("⛔ T1 il lettore del canale NON ritrova quel che ho "
                     "iniettato: %s" % json.dumps(congedi)[:300])

    # T2 — lo spezzettatore ritrova ritmi NOTI, e le finestre stanno al loro posto.
    #      «prima» a 40/s, «durante» a 12/s, «dopo» a 40/s.
    # ⚠ Con `offset = 90` un `arrivo_ms` vale `90 + arrivo_ms/1000` secondi sul
    #   quadrante del server: e' quella la corrispondenza che si sta tarando.
    t_ini, t_fine = 100.0, 110.0
    g = (_fab_giornale(400, 40.0, t0_ms=0, numero0=0)
         + _fab_giornale(120, 12.0, t0_ms=10000, numero0=1000)
         + _fab_giornale(400, 40.0, t0_ms=21100, numero0=2000))
    fin = spezza_in_finestre(g, offset=90.0, t_ini=t_ini, t_fine=t_fine,
                             largo=8.0, guardia=1.0)
    guai = ancora_finestre(fin, t_ini, t_fine)
    n_pr = B70.misura(fin["prima"], 8.0, scaldata_s=0.0)
    n_du = B70.misura(fin["durante"], 10.0, scaldata_s=0.0)
    if (not guai and abs((n_pr.get("fps") or 0) - 40.0) < 1.0
            and abs((n_du.get("fps") or 0) - 12.0) < 1.0):
        righe.append("⭐ T2 lo spezzettatore ritrova i ritmi iniettati: prima "
                     "%.2f/s (atteso 40), durante %.2f/s (atteso 12), e "
                     "l'ancora non ha guai" % (n_pr["fps"], n_du["fps"]))
    else:
        ok = False
        righe.append("⛔ T2 lo spezzettatore NON ritrova i ritmi iniettati: "
                     "prima %s, durante %s, ancora %s"
                     % (n_pr.get("fps"), n_du.get("fps"), guai))

    # T3 — l'ancora si rifiuta quando le finestre non sono quelle che dicono.
    #      ⛔ E' la taratura del RIFIUTO: un'ancora che non sa dire di no non e'
    #      un'ancora.
    storta = spezza_in_finestre(g, offset=90.0, t_ini=t_ini, t_fine=t_fine,
                                largo=8.0, guardia=1.0)
    storta["prima"] = storta["prima"] + storta["dopo"][:5]
    if ancora_finestre(storta, t_ini, t_fine):
        righe.append("⭐ T3 l'ancora si RIFIUTA se in «prima» finiscono "
                     "fotogrammi arrivati dopo il tentativo")
    else:
        ok = False
        righe.append("⛔ T3 l'ancora NON si accorge di «prima» inquinata da "
                     "fotogrammi di «dopo»: e' un verde per costruzione")

    # ⛔⛔ T4 — I DUE OROLOGI, e questa e' la taratura che l'ancora NON puo' fare.
    #
    #     L'ancora guarda gli istanti GIA' tradotti: un offset sbagliato **di
    #     tutto quanto** le passa davanti perfettamente ordinato, e allora
    #     «prima» sarebbe fatta di fotogrammi arrivati durante o dopo il
    #     tentativo — con l'aria giusta.  ⇒ La sola difesa e' misurare l'offset
    #     con DUE ancore indipendenti e rifiutarsi se non vanno d'accordo, ed e'
    #     esattamente questo che si tara qui.
    msg = [{"nome": "SESSIONE", "verso": "server", "istante_ms": 1000}]
    buone = ["12:00:01.000 rcp     posto PRESO da provadec4 via [x]:1 (occupati adesso: 1)",
             "12:01:01.000 rcp     posto LASCIATO da provadec4 via [x]:1 (occupati adesso: 0)"]
    off, come = offset_del_cliente(msg, buone, ultimo_blocco_ms=61000)
    atteso = 12 * 3600 + 0 * 60 + 1 - 1.0
    if off is not None and abs(off - atteso) < 0.002:
        righe.append("⭐ T4a l'offset iniettato (%.3f) e' quello ritrovato "
                     "(%.3f)" % (atteso, off))
    else:
        ok = False
        righe.append("⛔ T4a l'offset non e' quello iniettato: %s (%s)" % (off, come))
    storte = [buone[0],
              "12:01:02.000 rcp     posto LASCIATO da provadec4 via [x]:1 (occupati adesso: 0)"]
    off2, come2 = offset_del_cliente(msg, storte, ultimo_blocco_ms=61000)
    if off2 is None:
        righe.append("⭐ T4b con le due ancore in disaccordo di 1 s l'offset si "
                     "RIFIUTA di uscire: le finestre non si costruiscono")
    else:
        ok = False
        righe.append("⛔ T4b due ancore a 1 s di distanza e l'offset esce lo "
                     "stesso (%.3f): un offset indovinato sposta le finestre e "
                     "rende I1 verde o rosso a caso" % off2)
    off3, come3 = offset_del_cliente(msg, buone[:1], ultimo_blocco_ms=None)
    if off3 is not None and "UNA SOLA ANCORA" in come3:
        righe.append("⭐ T4c con una sola ancora l'offset esce ma si DICHIARA "
                     "non verificato: «non ho controllato» non prende la faccia "
                     "di «ho controllato»")
    else:
        ok = False
        righe.append("⛔ T4c con una sola ancora l'offset esce SENZA dirlo: %s"
                     % come3)

    if verboso:
        for r in righe:
            (_ok if r.startswith("⭐") else _ko)(r)
    return ok, righe


def leggi_canale_qui(percorso):
    """Il lettore del canale, eseguito SUL PORTATILE (serve alla taratura e ai
       guasti: non c'e' nessuna macchina di mezzo)."""
    fn = os.path.join(FUORI, "10-b93-canale.py")
    os.makedirs(FUORI, exist_ok=True)
    with open(fn, "w") as f:
        f.write(CANALE)
    p = subprocess.run([sys.executable, fn, percorso,
                        os.path.join(QUI, "01-b4-validatore.py")],
                       capture_output=True, timeout=300)
    try:
        return json.loads(p.stdout.decode("utf-8", "replace"))
    except Exception as e:
        return {"esito": "il lettore non ha risposto: %s — %s"
                         % (e, (p.stdout + p.stderr).decode("utf-8", "replace")[-300:])}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL MODO --certifica — un banco non e' finito finche' non lo si e' visto
#      dare ROSSO (`LEZIONI.md` §1.29)
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """Sano → guasto → risanato, per ogni predicato che questo banco usa.

    ⛔ I guasti si INNESTANO e si FANNO GIRARE: nessuno e' immaginato.
    """
    cliente = _carica("b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
    B70 = _carica("b70ritmo", os.path.join(QUI, "09-b70-ritmo.py"))
    esiti = []

    def prova(nome, atteso, chiamata):
        """`atteso` ∈ {True, False, None}."""
        try:
            passa, perche = chiamata()
        except Exception as e:
            passa, perche = "ECCEZIONE", "%s: %s" % (type(e).__name__, e)
        bene = (passa is atteso)
        esiti.append((nome, atteso, passa, bene, perche))
        segno = {True: "verde", False: "ROSSO", None: "non giudico"}.get(passa, passa)
        (_ok if bene else _ko)("%-42s atteso %-11s → %s%s"
                               % (nome, {True: "verde", False: "ROSSO",
                                         None: "non giudico"}[atteso], segno,
                                  "" if bene else "   ⛔ « " + str(perche)[:220]))
        return bene

    _log("0 · LA TARATURA DEL METRO — e se non passa, il banco non misura")
    tarato, _righe = taratura(B70, cliente)
    esiti.append(("taratura del metro", True, tarato, tarato, ""))

    # ── I tentativi: sano, e i tre guasti che lo riguardano ────────────────
    _log("1 · IL MOTIVO SUL FILO, IL DETTAGLIO, E LA SOLLECITAZIONE")
    dett = "il registro delle sessioni di questo server e' pieno"
    sano = [{"arrivato_a": "ATTACCA", "motivo": MOTIVO_GIUSTO,
             "dettaglio": dett, "dettaglio_letto": True} for _ in range(10)]
    prova("p_ha_morso · sano", True, lambda: p_ha_morso(sano))
    prova("p_motivo_sul_filo · sano", True, lambda: p_motivo_sul_filo(sano))
    prova("p_dettaglio_nel_corpo · sano", True, lambda: p_dettaglio_nel_corpo(sano))

    # ⛔ G1 — IL MOTIVO SBAGLIATO SUL FILO, e si innesta DOVE si legge davvero:
    #    in una traccia §11.1 fabbricata col registratore del cliente, letta dal
    #    lettore vero.  ⚠ Passare un dizionario con `motivo: 0x0F` proverebbe il
    #    predicato e NON il lettore, che e' meta' dello strumento.
    perc = os.path.join(FUORI, "g1.rcpreg")
    fabbrica_traccia(perc, [
        (cliente.SERVER, 0x000C, corpo_congedo(MOTIVO_BUGIARDO, dett), 10)],
        cliente)
    letto = leggi_canale_qui(perc)
    g1 = [dict(t) for t in sano]
    for t, m in zip(g1, [m for m in letto.get("messaggi", [])
                         if m["nome"] == "CONGEDO"] * 10):
        t["motivo"] = m["motivo"]
    prova("⛔ G1 motivo 0x0F sul filo", False, lambda: p_motivo_sul_filo(g1))
    prova("   G1 risanato", True, lambda: p_motivo_sul_filo(sano))

    # ⛔ G2 — IL CORPO VUOTO dove §8.2 lo pretende, innestato nella traccia.
    perc = os.path.join(FUORI, "g2.rcpreg")
    fabbrica_traccia(perc, [
        (cliente.SERVER, 0x000C, corpo_congedo(MOTIVO_GIUSTO, ""), 10)], cliente)
    letto = leggi_canale_qui(perc)
    vuoto = [m for m in letto.get("messaggi", []) if m["nome"] == "CONGEDO"][0]
    g2 = [{"arrivato_a": "ATTACCA", "motivo": vuoto["motivo"],
           "dettaglio": vuoto["dettaglio"],
           "dettaglio_letto": vuoto["dettaglio_letto"]} for _ in range(10)]
    prova("⛔ G2 corpo VUOTO dove §8.2 lo impone", False,
          lambda: p_dettaglio_nel_corpo(g2))
    prova("   G2 risanato", True, lambda: p_dettaglio_nel_corpo(sano))

    # ⛔⛔ G3 — IL CLIENTE CHE NON ARRIVA NEMMENO A PROVARCI.  Tre forme, e tutte
    #     e tre devono dare «NON HO MISURATO», mai «respinto correttamente».
    for forma, dove in (("parola sbagliata", "RESPINTO"),
                        ("indirizzo bannato", "TROPPI_TENTATIVI"),
                        ("server spento", "niente connessione")):
        g3 = [{"arrivato_a": dove, "motivo": None, "dettaglio": None,
               "dettaglio_letto": False} for _ in range(10)]
        prova("⛔ G3 %s" % forma, None, lambda g=g3: p_ha_morso(g))
    prova("   G3 risanato", True, lambda: p_ha_morso(sano))

    # ── §3.1 punto 3: la seconda strada ───────────────────────────────────
    sano_wt = [dict(t, codice_wt=MOTIVO_GIUSTO) for t in sano]
    prova("p_motivo_anche_nel_codice · sano", True,
          lambda: p_motivo_anche_nel_codice(sano_wt))
    prova("⛔ G11a la sessione si chiude col codice 0", False,
          lambda: p_motivo_anche_nel_codice(
              [dict(t, codice_wt=0) for t in sano]))
    prova("⛔ G11b le due strade di §3.1 si contraddicono", False,
          lambda: p_motivo_anche_nel_codice(
              [dict(t, codice_wt=MOTIVO_BUGIARDO) for t in sano]))
    prova("   G11c il codice della sessione non e' stato letto", None,
          lambda: p_motivo_anche_nel_codice(
              [dict(t, codice_wt=None, codice_quic=0) for t in sano]))
    prova("⛔ G11e armate 10, spedite 0 (la seconda strada non parte)", False,
          lambda: p_motivo_anche_nel_codice(
              [dict(t, codice_wt=None, codice_quic=0) for t in sano],
              {"rimandate": 10, "spedite": 0}))
    prova("   G11f armate 10, spedite 10 ma nessun codice letto", None,
          lambda: p_motivo_anche_nel_codice(
              [dict(t, codice_wt=None, codice_quic=0) for t in sano],
              {"rimandate": 10, "spedite": 10}))
    prova("   G11d meta' misura", None, lambda: p_motivo_anche_nel_codice(
        [dict(t, codice_wt=MOTIVO_GIUSTO) for t in sano[:5]]
        + [dict(t, codice_wt=None) for t in sano[5:]]))
    prova("   G11 risanato", True, lambda: p_motivo_anche_nel_codice(sano_wt))

    # ── I1 ─────────────────────────────────────────────────────────────────
    _log("2 · I1 — CHI ERA GIA' DENTRO")
    # ⚠ `offset = 90` ⇒ `arrivo_ms` di 10 000 vale il secondo 100 sul quadrante
    #   del server, cioe' l'inizio del tentativo.  Le tre finestre cadono su
    #   `arrivo_ms` [1000,9000) · [10000,40000] · (41000,49000].
    t_ini, t_fine = 100.0, 130.0
    base = (_fab_giornale(400, 40.0, t0_ms=0, numero0=0, chiave_ogni=0)
            + _fab_giornale(1200, 40.0, t0_ms=10000, numero0=1000, chiave_ogni=0)
            + _fab_giornale(400, 40.0, t0_ms=41100, numero0=3000, chiave_ogni=0))
    fin = spezza_in_finestre(base, 90.0, t_ini, t_fine, largo=8.0, guardia=1.0)
    an = ancora_finestre(fin, t_ini, t_fine)
    n = {k: B70.misura(v, 8.0, scaldata_s=0.0) for k, v in fin.items()}
    prova("p_I1 · sano (40/s ovunque)", True,
          lambda: p_I1(n["prima"], n["durante"], n["dopo"], an))

    # ⛔⛔ G4 — UN PEGGIORAMENTO FINTO, e senza questo il punto 4 e' un verde per
    #     costruzione.  Tre forme: il ritmo, il peggior secondo, e ⭐ IL
    #     MECCANISMO (le chiavi che salgono col ritmo INTATTO).
    peggio = (_fab_giornale(400, 40.0, t0_ms=0, numero0=0)
              + _fab_giornale(300, 10.0, t0_ms=10000, numero0=1000)
              + _fab_giornale(400, 40.0, t0_ms=41100, numero0=3000))
    fp = spezza_in_finestre(peggio, 90.0, t_ini, t_fine, largo=8.0, guardia=1.0)
    np_ = {k: B70.misura(v, 8.0, scaldata_s=0.0) for k, v in fp.items()}
    prova("⛔ G4a il ritmo CROLLA durante il tentativo", False,
          lambda: p_I1(np_["prima"], np_["durante"], np_["dopo"],
                       ancora_finestre(fp, t_ini, t_fine)))
    # ⛔ G4b — IL RITMO MEDIO REGGE E IL DESKTOP SI PIANTA PER DUE SECONDI.
    #    E' il caso che la media assolve: 1120 fotogrammi in 30 s fanno 37,3/s,
    #    cioe' il 93% di 40 — sopra la soglia — e in mezzo c'e' un buco in cui
    #    l'utente vede un'immagine ferma.  ⇒ Lo prende il PEGGIOR SECONDO.
    buco = (_fab_giornale(400, 40.0, t0_ms=0, numero0=0)
            + _fab_giornale(600, 40.0, t0_ms=10000, numero0=1000)
            + _fab_giornale(600, 40.0, t0_ms=27000, numero0=1600)
            + _fab_giornale(400, 40.0, t0_ms=41100, numero0=3000))
    fb = spezza_in_finestre(buco, 90.0, t_ini, t_fine, largo=8.0, guardia=1.0)
    nb = {k: B70.misura(v, 8.0, scaldata_s=0.0) for k, v in fb.items()}
    prova("⛔ G4b un buco di 2 s col ritmo medio quasi intatto", False,
          lambda: p_I1(nb["prima"], nb["durante"], nb["dopo"],
                       ancora_finestre(fb, t_ini, t_fine)))
    # ⭐ G4c — IL MECCANISMO SENZA IL SINTOMO: 40/s prima e durante, ma durante
    #    una chiave ogni 10 fotogrammi.  ⛔ Un banco che guardasse il solo ritmo
    #    darebbe VERDE a questo, ed e' il caso di `LEZIONI.md` §1.31.
    mecc = (_fab_giornale(400, 40.0, t0_ms=0, numero0=0, chiave_ogni=0)
            + _fab_giornale(1200, 40.0, t0_ms=10000, numero0=1000, chiave_ogni=10)
            + _fab_giornale(400, 40.0, t0_ms=41100, numero0=3000, chiave_ogni=0))
    fm = spezza_in_finestre(mecc, 90.0, t_ini, t_fine, largo=8.0, guardia=1.0)
    nm = {k: B70.misura(v, 8.0, scaldata_s=0.0) for k, v in fm.items()}
    prova("⛔ G4c LE CHIAVI salgono col ritmo intatto (il meccanismo)", False,
          lambda: p_I1(nm["prima"], nm["durante"], nm["dopo"],
                       ancora_finestre(fm, t_ini, t_fine)))
    prova("   G4 risanato", True,
          lambda: p_I1(n["prima"], n["durante"], n["dopo"], an))

    # ⛔⛔ G5 — IL CONTO DELLA SESSIONE «PRIMA» LETTO DOPO IL TENTATIVO, e sono
    #     DUE difetti diversi che vanno tutti e due chiusi.
    #
    # G5a — **l'offset non c'e'**.  E' quel che succede nel giro vero quando le
    #       due ancore non vanno d'accordo: `spezza_in_finestre()` torna `None`,
    #       e il banco NON costruisce finestre a caso.
    niente = spezza_in_finestre(base, None, t_ini, t_fine, largo=8.0, guardia=1.0)
    prova("⛔ G5a l'offset fra i due orologi non e' misurato", None,
          lambda: p_I1({}, {}, {},
                       ["l'offset fra i due orologi non e' stato misurato"]
                       if niente is None else []))
    # ⛔ G5b — l'offset c'e' ed e' giusto, ma «prima» e' INQUINATA da cinque
    #    fotogrammi di «dopo»: e' letteralmente il conto della sessione «prima»
    #    letto dopo il tentativo, ed e' la forma che ha l'aria piu' innocua.
    inquinato = spezza_in_finestre(base, 90.0, t_ini, t_fine, largo=8.0, guardia=1.0)
    inquinato["prima"] = inquinato["prima"] + inquinato["dopo"][:5]
    ni = {k: B70.misura(v, 8.0, scaldata_s=0.0) for k, v in inquinato.items()}
    prova("⛔ G5b «prima» inquinata da 5 fotogrammi di «dopo»", None,
          lambda: p_I1(ni["prima"], ni["durante"], ni["dopo"],
                       ancora_finestre(inquinato, t_ini, t_fine)))
    prova("   G5 risanato", True,
          lambda: p_I1(n["prima"], n["durante"], n["dopo"], an))

    # ── Gli strascichi ─────────────────────────────────────────────────────
    _log("3 · GLI STRASCICHI, IL CONFINE, IL POSTO CHE TORNA")
    fermi = [{"posti_presi_dal_respinto": 0, "figli": 3, "gnome_respinto": 1,
              "proc_respinto": 40, "fd": 40, "rss_kb": 30000} for _ in range(10)]
    prova("p_niente_strascichi · sano", True, lambda: p_niente_strascichi(fermi))
    cresce = [dict(x) for x in fermi]
    for i, x in enumerate(cresce):
        x["figli"] = 3 + i            # ⛔ un figlio nuovo a ogni rifiuto
    prova("⛔ G6a un figlio in piu' a ogni rifiuto", False,
          lambda: p_niente_strascichi(cresce))
    posti = [dict(x) for x in fermi]
    for i, x in enumerate(posti):
        # ⛔ un posto che il respinto si prende e nessuno libera
        x["posti_presi_dal_respinto"] = i
    prova("⛔ G6b un posto preso dal respinto e mai liberato", False,
          lambda: p_niente_strascichi(posti))
    muto = [dict(x) for x in fermi]
    for x in muto:
        x["rss_kb"] = None            # ⚠ non letto ≠ zero
    prova("⛔ G6c la memoria NON letta", False, lambda: p_niente_strascichi(muto))
    prova("   G6 risanato", True, lambda: p_niente_strascichi(fermi))

    prova("p_confine · rifiuto prima del desktop", True,
          lambda: p_confine_del_rifiuto({"autenticato": True, "figlio_nato": False,
                                         "sessione_grafica": False,
                                         "palco_acceso": False}))
    prova("⛔ G7 rifiuto DOPO il desktop acceso", False,
          lambda: p_confine_del_rifiuto({"autenticato": True, "figlio_nato": True,
                                         "sessione_grafica": True,
                                         "palco_acceso": True}))
    prova("   G7 «non letto» non e' «no»", None,
          lambda: p_confine_del_rifiuto({"autenticato": True, "figlio_nato": True,
                                         "sessione_grafica": None,
                                         "palco_acceso": None}))

    prova("p_posto_torna · sano", True, lambda: p_posto_torna(
        [{"come": "commiato", "atteso_s": 3.0, "secondi": 0.4, "tetto_s": 60},
         {"come": "morte improvvisa", "atteso_s": 35.0, "secondi": 30.7,
          "tetto_s": 60}]))
    prova("⛔ G8a il posto NON torna", False, lambda: p_posto_torna(
        [{"come": "commiato", "atteso_s": 3.0, "secondi": None, "tetto_s": 60}]))
    prova("⛔ G8b il posto torna troppo tardi", False, lambda: p_posto_torna(
        [{"come": "commiato", "atteso_s": 3.0, "secondi": 31.0, "tetto_s": 60}]))

    prova("p_due_numeri · allineati", True,
          lambda: p_due_numeri({"max_attaccate": 16, "max_figli": 16}))
    prova("⛔ G9 i due numeri divergono", False,
          lambda: p_due_numeri({"max_attaccate": 2, "max_figli": 16}))

    prova("p_frase_della_pagina · sano", True, lambda: p_frase_della_pagina(
        {"frase": "il server e' pieno", "motivo": MOTIVO_GIUSTO}))
    prova("⛔ G10a la pagina MENTE", False, lambda: p_frase_della_pagina(
        {"frase": "quell'utente e' gia' collegato da un altro dispositivo",
         "motivo": MOTIVO_GIUSTO}))
    prova("⛔ G10b la pagina non dice niente", False, lambda: p_frase_della_pagina(
        {"frase": "", "motivo": MOTIVO_GIUSTO}))
    prova("   G10c la pagina non e' stata guardata", None,
          lambda: p_frase_della_pagina({"frase": None, "perche": "senza Firefox"}))

    _log("L'ESITO DELLA CERTIFICAZIONE")
    male = [e for e in esiti if not e[3]]
    _inf("%d prove · %d hanno fatto quel che dovevano · %d NO"
         % (len(esiti), len(esiti) - len(male), len(male)))
    for nome, atteso, avuto, _b, perche in male:
        _ko("%s: atteso %s, avuto %s — %s" % (nome, atteso, avuto, str(perche)[:200]))
    return 0 if not male else 1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIRO VERO — da qui in giu' si tocca la macchina di prova
# ═══════════════════════════════════════════════════════════════════════════
def ascoltatori(porta):
    rc, out, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % porta)
    t = out.strip()
    return int(t) if t.isdigit() else None


def terreno_controlla():
    _log("IL TERRENO — porta %d · utenti %s · albero %s"
         % (PORTA, ", ".join(u for u, _ in TUTTI), ALB))
    guai = []
    for u, uid in TUTTI:
        rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % u)
        if "si" not in out:
            guai.append("l'utente «%s» non c'e': bash banchi/10-b93-terreno.sh utenti" % u)
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % LAV)
    rc, out, _ = root("test -s %s/banchi/01-b4-validatore.py && echo si || echo no" % ALB)
    if "si" not in out:
        guai.append("manca l'arbitro di §11.1 in %s/banchi: senza, i lettori "
                    "della traccia non partono e OGNI giro sembra una sessione "
                    "morta" % ALB)
    rc, out, _ = root("test -x %s && echo si || echo no" % SCENA_BIN)
    if "si" not in out:
        guai.append("la scena «%s» non e' eseguibile" % SCENA_BIN)
    n = ascoltatori(PORTA)
    conto = []
    for p in VICINE:
        conto.append("%s:%s" % (p, ascoltatori(p)))
    _inf("ascoltatori NON miei (si contano, non si toccano): %s" % " ".join(conto))
    _inf("il mio server sulla %d: %s ascoltatore/i" % (PORTA, n))
    if not n:
        guai.append("nessuno ascolta sulla %d: bash banchi/10-b93-terreno.sh accendi"
                    % PORTA)
    for g in guai:
        _ko(g)
    if not guai:
        _ok("il terreno c'e', ed e' mio")
    return not guai


def i_due_numeri():
    """⛔ I due `#define`, letti DAI SORGENTI CHE HANNO PRODOTTO IL BINARIO.

    ⛔⛔ IL NUMERO SI E' SPOSTATO — 25 agosto 2026, cura C3 della fase 10.

        Erano QUATTRO `#define` a 16 copiati a mano, e tre di essi
        DICHIARAVANO PER ISCRITTO un legame che il compilatore non conosceva.
        Adesso il numero e' UNO — `RCP_TETTO_SESSIONI` in `rcp.h` — e
        `MAX_ATTACCATE` e `MAX_FIGLI` lo SEGUONO davvero.

    ⛔ E il modo in cui questo lettore falliva era il solito: i due modelli non
       trovavano piu' niente, i due numeri restavano `None`, il predicato
       finiva fra i MUTI, la riga finale annunciava «una tabella da None»
       — ⛔ **e `--certifica` restava verde**, perche' inietta i dizionari a
       mano.  Strumento verde, misura spenta.

    ⇒ Si legge il numero UNICO, e si tiene la lettura dei due nomi come
      CONTROLLO: se uno dei due non rimanda al numero unico, il legame si e'
      rotto di nuovo e va detto."""
    rc, out, _ = root(
        "grep -h '^#define RCP_TETTO_SESSIONI' %s/src/rcp.h; "
        "grep -h '^#define MAX_ATTACCATE' %s/src/rcp.c; "
        "grep -h '^#define MAX_FIGLI' %s/src/figlio.c; "
        "md5sum %s/src/rcp.h %s/src/rcp.c %s/src/figlio.c %s/src/remotix"
        % (ALB, ALB, ALB, ALB, ALB, ALB, ALB))
    n = {"max_attaccate": None, "max_figli": None, "tetto": None,
         "seguono": None, "md5": {}}
    segue_att = segue_fig = False
    for r in out.splitlines():
        m = re.match(r"#define RCP_TETTO_SESSIONI (\d+)", r.strip())
        if m:
            n["tetto"] = int(m.group(1))
        m = re.match(r"#define MAX_ATTACCATE (\d+)", r.strip())
        if m:
            n["max_attaccate"] = int(m.group(1))
        elif re.match(r"#define MAX_ATTACCATE\s+RCP_TETTO_SESSIONI", r.strip()):
            segue_att = True
        m = re.match(r"#define MAX_FIGLI (\d+)", r.strip())
        if m:
            n["max_figli"] = int(m.group(1))
        elif re.match(r"#define MAX_FIGLI\s+RCP_TETTO_SESSIONI", r.strip()):
            segue_fig = True
        m = re.match(r"([0-9a-f]{32})\s+(\S+)", r.strip())
        if m:
            n["md5"][os.path.basename(m.group(2))] = m.group(1)
    # ⭐ Se seguono il numero unico, i due valori SONO quel numero: si scrivono,
    #    cosi' tutto il resto del banco continua a leggerli come prima.
    if n["tetto"] is not None:
        if segue_att:
            n["max_attaccate"] = n["tetto"]
        if segue_fig:
            n["max_figli"] = n["tetto"]
    n["seguono"] = {"max_attaccate": segue_att, "max_figli": segue_fig}
    return n


def righe_registro():
    """Quante righe ha il registro ADESSO — `None` se non l'ho letto.
    ⛔ Uno zero che vuol dire «non ho letto» e uno che vuol dire «non e'
       successo niente» non devono avere la stessa faccia (`LEZIONI.md` §1.9)."""
    rc, out, _ = root("wc -l < %s/registro.log" % LAV)
    t = out.strip()
    return int(t) if t.isdigit() and int(t) > 0 else None


def registro_da(riga0, filtro=None, tetto=4000):
    """Le righe del registro DA `riga0` in poi.

    ⛔⛔ IL `tail -n TETTO` IN CODA TIENE LE **ULTIME** RIGHE, e questa e' una
        trappola che ha gia' morso: `[M]` 24 agosto 2026, primo giro di questo
        banco.  Due sessioni vive scrivono migliaia di righe al minuto, e il
        `posto PRESO` — che sta all'INIZIO del giro — cadeva fuori dal tetto.
        ⇒ `offset_del_cliente()` non trovava la sua ancora e I1 usciva «non
          giudico» su due sessioni perfettamente misurate.
    ⇒ Chi cerca una riga rara passa un `filtro`: il `grep` viene PRIMA del
      tetto, quindi il tetto morde sulle righe che interessano e non su tutte.
    """
    if riga0 is None:
        return None
    f = ("| grep -a %s" % shlex.quote(filtro)) if filtro else ""
    rc, out, _ = root("tail -n +%d %s/registro.log %s | tail -n %d"
                      % (riga0 + 1, LAV, f, tetto))
    return out


# ⛔ Le tre righe che fanno da ANCORA fra i due orologi.  Si cercano per nome,
#    non «tutte le righe che contengono l'utente»: la seconda sono migliaia.
FILTRO_ANCORE = "posto PRESO da\\|posto LASCIATO da\\|l'ultima sessione di\\|STACCATO per silenzio"


def righe_ancora(riga0, utente):
    testo = registro_da(riga0, FILTRO_ANCORE, tetto=400) or ""
    return [r for r in testo.splitlines() if utente in r]


CHIAVI_SCATTO = {"PRESI": "posti_presi_dal_respinto", "FIGLI": "figli",
                 "GNOME": "gnome_respinto", "PROC": "proc_respinto",
                 "FD": "fd", "RSS": "rss_kb", "OCCUPATI": "occupati"}


def conti_capsula(riga0):
    """⛔ §3.1 punto 3 dal LATO CHE MANDA: due conti che devono coincidere.

    `chiudi_sessione()` scrive «chiusura della sessione RIMANDATA» quando ARMA
    l'attesa, e `manda_capsula_chiusura()` scrive «chiusa la sessione
    WebTransport» quando la capsula finisce davvero in coda.  ⭐ La differenza
    fra i due conti e' il numero di volte in cui il motivo NON e' partito per la
    seconda strada.
    """
    fuori = {"rimandate": None, "spedite": None}
    for chiave, testo in (("rimandate", "chiusura della sessione RIMANDATA"),
                          ("spedite", "chiusa la sessione WebTransport")):
        t = registro_da(riga0, testo, tetto=4000)
        if t is None:
            continue
        fuori[chiave] = len([r for r in t.splitlines() if testo in r])
    return fuori


def fotografia(pid, riga0):
    """⛔ Le grandezze che, se il rifiuto lascia strascichi, CRESCONO.
    ⚠ Ognuna torna `None` se non l'ho letta — e `None` non e' zero.

    ⚠ **`occupati` si legge e non si giudica**, e la ragione e' una riga del
      prodotto: `congeda()` chiama `posto_lascia()` **senza** scrivere il nuovo
      conto (`rcp.c:1663`), mentre `posto PRESO`, `posto LASCIATO` e lo stacco
      per silenzio lo scrivono.  ⇒ L'ultimo «occupati adesso: N» del registro
      puo' essere VECCHIO di un congedo, e un predicato costruito su di lui
      darebbe rossi che non sono del prodotto.  ⭐ Il posto che non torna lo
      misura la prova 6, che e' un fatto e non una lettura.
    """
    f = {}
    rc, out, _ = root(
        "echo PRESI $(tail -n +%d %s/registro.log | grep -ac 'posto PRESO da %s' || true); "
        # ⛔ E I FIGLI SI CONTANO SU `argv[0]`, NON CON UN `pgrep -f` NUDO —
        #    `[M]` 24 ago 2026, primo giro: contava **7** dove ce n'erano
        #    **tre**, e gli altri quattro erano l'`ssh`, il `sudo` e le due
        #    `bash` con cui STAVO CHIEDENDO.  ⚠ Non ha dato un rosso falso (il
        #    numero era costante), ma un numero sbagliato in un rapporto e' una
        #    bugia lo stesso.
        # ⚠ E NON si guarda `comm`: il figlio si rinomina con `prctl`, quindi
        #   `comm` resta **«remotix»** e `argv[0]` diventa «remotix-figlio» —
        #   un `^remotix-figlio` su `comm` non trova MAI niente e conta zero
        #   figli su una macchina che ne ha tre (secondo giro, stessa sera).
        # ⛔ E la classe `[o]` impedisce alla riga di contare SE STESSA.
        "echo FIGLI $(ps -eo args= | grep -c -- "
        "'^remotix-figlio --figlio-intern[o] .*%s/rilievo' || true); "
        "echo GNOME $(pgrep -u %d -c gnome-shell || true); "
        "echo PROC $(pgrep -u %d -c . || true); "
        "echo FD $(ls /proc/%d/fd 2>/dev/null | wc -l); "
        "echo RSS $(awk '/VmRSS/{print $2}' /proc/%d/status); "
        "echo OCCUPATI $(grep -a 'occupati adesso:' %s/registro.log | tail -1 | "
        "grep -ao 'occupati adesso: [0-9]*' | grep -o '[0-9]*$')"
        % ((riga0 or 0) + 1, LAV, RESPINTO[0], LAV, RESPINTO[1], RESPINTO[1],
           pid, pid, LAV))
    for r in out.splitlines():
        p = r.split()
        if len(p) != 2 or not p[1].lstrip("-").isdigit():
            continue
        k = CHIAVI_SCATTO.get(p[0])
        if k:
            f[k] = int(p[1])
    for k in CHIAVI_SCATTO.values():
        f.setdefault(k, None)
    return f


def occupati_adesso():
    """Quanti posti risultano occupati, dall'ultima riga che lo dichiara.

    ⚠ **Si legge e non si giudica.**  `congeda()` chiama `posto_lascia()` senza
      scrivere il nuovo conto (`rcp.c:1663`), mentre `posto PRESO`, `posto
      LASCIATO` e lo stacco per silenzio lo scrivono.  ⇒ Questo numero puo'
      essere VECCHIO di un congedo.  Serve ad aspettare, non ad accusare.
    """
    rc, out, _ = root("grep -a 'occupati adesso:' %s/registro.log | tail -1 | "
                      "grep -ao 'occupati adesso: [0-9]*' | grep -o '[0-9]*$'" % LAV)
    t = out.strip()
    return int(t) if t.isdigit() else None


def clienti_miei_vivi():
    """Quanti clienti di prova sulla MIA porta sono ancora vivi.  `None` se non
       l'ho letto.  ⛔ `[0]1-` perche' la riga non conti se stessa."""
    rc, out, _ = root("ps -eo args= | grep -c -- '%s' || true"
                      % modello_cliente("--porta %d" % PORTA))
    t = out.strip()
    return int(t) if t.isdigit() else None


def aspetta_tabella_vuota(tetto=60.0):
    """⛔ FRA UNA PROVA E L'ALTRA SI ASPETTA CHE I POSTI TORNINO LIBERI.

    `[M]` 24 agosto 2026, primo giro: la seconda prova d'uscita partiva subito
    dopo che la prima aveva ucciso i clienti a `-9`, e i posti erano ancora dei
    FANTASMI.  ⇒ Il cliente che doveva riempire riceveva `0x0F` (posto occupato
    dal suo stesso fantasma, e lo sfratto vuole 15 s di silenzio), non prendeva
    nessun posto, e la prova si dichiarava «non ho misurato» — un buco del banco
    con la faccia di un difetto del prodotto.
    """
    # ⛔ Tre condizioni, e servono tutte e tre:
    #      1. nessun cliente MIO ancora vivo — o i posti sono legittimamente
    #         occupati e non c'e' niente da aspettare;
    #      2. il registro dichiara zero posti occupati;
    #      3. ⛔ e poi si aspetta comunque la LINEA MORTA (10 s + margine): un
    #         cliente ucciso a `-9` non manda niente, il suo posto resta del
    #         fantasma, e chi arriva in quei secondi si becca `0x0F` — non
    #         `0x0E` — perche' lo sfratto di §4.4 vuole 15 s di silenzio.
    #      `[M]` 24 ago 2026: senza il punto 3 la prova d'uscita brutale si e'
    #      dichiarata «non ho misurato» due volte di fila.
    scade = time.time() + tetto
    fermi_da = None
    while time.time() < scade:
        vivi = clienti_miei_vivi()
        n = occupati_adesso()
        if vivi == 0 and n == 0:
            if fermi_da is None:
                fermi_da = time.time()
            elif time.time() - fermi_da >= 13.0:
                return True
        else:
            fermi_da = None
        time.sleep(2.0)
    return False


def pid_del_server():
    rc, out, _ = root("systemctl show -p MainPID --value %s.service" % UNITA)
    t = out.strip()
    return int(t) if t.isdigit() and int(t) > 0 else None


def spedisci_lettori(B70):
    """⛔ I due lettori si spediscono in base64, e la catena vive TUTTA dentro la
       shell di root: le virgolette di un heredoc dentro un `sudo` dentro un
       `ssh` sono tre livelli, e uno sbagliato non da' un errore — da' un file
       troncato."""
    ok = True
    for nome, testo in (("09-b70-leggi.py", B70.LETTORE),
                        ("10-b93-canale.py", CANALE)):
        b = base64.b64encode(testo.encode("utf-8")).decode("ascii")
        root("mkdir -p %s && printf '%%s' '%s' | base64 -d > %s/%s"
             % (LAV, b, LAV, nome))
        rc, out, _ = root("wc -c < %s/%s" % (LAV, nome))
        n = out.strip()
        if not (n.isdigit() and int(n) > 1000):
            _ko("il lettore «%s» non si e' scritto in %s (%s byte)" % (nome, LAV, n))
            ok = False
    return ok


# ⛔⛔ IL `pkill -f` CHE UCCIDE CHI LO STA CHIEDENDO — `[M]` 24 agosto 2026.
#
#     `root("pkill -f '01-b3-cliente.py …'")` finisce dentro
#     `sudo -S bash -c '<catena>'`: la catena e' l'`argv` di QUELLA bash, quindi
#     il modello ci si trova dentro e `pkill` **ammazza la shell che lo sta
#     eseguendo**.  ⇒ Il `; true` in coda non gira mai, il comando torna un
#     codice strano, e — la parte peggiore — i comandi che venivano DOPO nella
#     stessa catena non vengono eseguiti.  Il banco crede di aver fatto pulizia
#     e non l'ha fatta, ⚠ e la prova successiva parte contro dei fantasmi.
#
# ⇒ Si spezza la prima lettera con una classe di caratteri: `[0]1-b3-…` non
#   corrisponde a se stesso quando `pkill` guarda l'`argv` di questa shell, ma
#   corrisponde benissimo al processo vero.
def modello_cliente(coda):
    return "[0]1-b3-cliente.py .*%s" % coda


def cliente_riga(utente, resta, registra=None, extra=""):
    return ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
            "--utente %s --parola-file %s/parola --audio-codec pcm "
            "--video-codec %s --adatta %s %s--resta %s %s"
            % (DENTRO_ALB, IND, PORTA, utente, DENTRO_LAV, CODEC_CHIESTO, TELA,
               ("--registra %s/%s.rcpreg " % (DENTRO_LAV, registra)) if registra else "",
               resta, extra))


def avvia_cliente(utente, resta, registra=None):
    """Un cliente in SOTTOFONDO, dentro il contenitore.  Torna il `Popen`."""
    riga = catena_root("bash /media/REMOTIX/enter.sh --root %s"
                       % shlex.quote(cliente_riga(utente, resta, registra)))
    return subprocess.Popen(["ssh", "-o", "BatchMode=yes", MACCHINA, riga],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def riempi(durata, registra=False, corto=None):
    """Riempie la tabella: un cliente per ogni utente DENTRO.

    Torna `{"proc": {utente: Popen}, "riga0": n}`.  ⚠ `riga0` si prende PRIMA
    di lanciare, o il «posto PRESO» che si sta per aspettare potrebbe essere di
    un giro precedente.
    """
    riga0 = righe_registro()
    proc = {}
    for u, _uid in DENTRO:
        d = corto if (corto is not None and u == DENTRO[-1][0]) else durata
        proc[u] = avvia_cliente(u, d, registra=("dentro-%s" % u) if registra else None)
        time.sleep(2.0)
    return {"proc": proc, "riga0": riga0}


def aspetta_posti(riga0, tetto=90):
    """⛔ Che i posti siano presi lo dice il REGISTRO del prodotto, non il fatto
       che io abbia lanciato dei clienti.  ⚠ E se non si riempie non si tira
       dritto: senza tabella piena la prova che segue misura un server LIBERO."""
    scade = time.time() + tetto
    while time.time() < scade:
        testo = registro_da(riga0, "posto PRESO da", tetto=200) or ""
        if all(("posto PRESO da %s" % u) in testo for u, _ in DENTRO):
            return True
        time.sleep(1.0)
    return False


def riempi_e_aspetta(durata, corto=None, giri=3):
    """Riempie la tabella e RIPROVA se non ci riesce.

    ⛔ Un cliente che arriva mentre il posto del suo stesso utente e' ancora del
       fantasma riceve `0x0F` e muore: e' il caso normale subito dopo una prova
       che ha ucciso i clienti a `-9`.  ⇒ Non si dichiara subito «non ho
       misurato»: si aspetta che il fantasma muoia e si ritenta.
    """
    for g in range(giri):
        rip = riempi(durata, corto=corto)
        if aspetta_posti(rip["riga0"], tetto=45):
            return rip
        for pr in rip["proc"].values():
            try:
                pr.kill()
            except Exception:
                pass
        root("pkill -f '%s'; true" % modello_cliente("--porta %d" % PORTA))
        _dub("⚠ giro %d: la tabella non si e' riempita (occupati: %s) — "
             "aspetto che i fantasmi muoiano e riprovo" % (g + 1, occupati_adesso()))
        aspetta_tabella_vuota()
    return None


def scena_accendi(utente, uid, giro):
    """⭐ La scena che MUOVE: senza, Mutter consegna solo quando qualcosa cambia
       e il ritmo di «prima» sarebbe zero — cioe' niente da confrontare."""
    root("pkill -u %d -f '0[4]-b30-scena'; true" % uid)
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "%s --uscita %s --movimento barra --shm /%s --giro %s "
         ">/dev/null 2>&1 & echo acceso"
         % (uid, uid, utente, utente, uid, SCENA_BIN, MONITOR_ATTESO, giro, giro))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % uid)
    return bool(out.strip())


def scena_spegni(uid):
    root("pkill -u %d -f '0[4]-b30-scena'; true" % uid)


def leggi_traccia_canale(nome):
    rc, out, err = root("python3 %s/10-b93-canale.py %s/%s.rcpreg "
                        "%s/banchi/01-b4-validatore.py" % (LAV, LAV, nome, ALB), 600)
    try:
        return json.loads(out)
    except Exception as e:
        return {"esito": "il lettore del canale non ha risposto: %s — %s"
                         % (e, (out + err)[-300:])}


def leggi_traccia_video(nome):
    rc, out, err = root("python3 %s/09-b70-leggi.py %s/%s.rcpreg "
                        "%s/banchi/01-b4-validatore.py" % (LAV, LAV, nome, ALB), 600)
    try:
        d = json.loads(out)
        return d, d.pop("giornale", [])
    except Exception as e:
        return ({"esito": "il lettore del video non ha risposto: %s — %s"
                          % (e, (out + err)[-300:])}, [])


def offset_del_cliente(messaggi, righe, ultimo_blocco_ms=None, tolleranza=0.300):
    """⛔⛔ IL PONTE FRA I DUE OROLOGI, e si MISURA con DUE ancore.

    **Ancora 1 — l'inizio**: il `SESSIONE` (server → client) nella traccia, e la
    riga «posto PRESO da <utente>» nel registro del server.  Le separa un mezzo
    giro di rete sulla LAN, cioe' meno di un millisecondo.

    **Ancora 2 — la fine**: l'istante dell'ULTIMO blocco della traccia e la riga
    «posto LASCIATO da <utente>» (o «l'ultima sessione di …»).  ⚠ Il cliente di
    prova NON manda mai un `CONGEDO` d'addio — chiude e basta — quindi l'addio
    non si puo' cercare fra i messaggi: si cerca l'ultimo BLOCCO, che c'e'
    sempre.

    ⛔ Se le due non vanno d'accordo entro `tolleranza`, si torna `None`: un
       offset ricavato da un'ancora sola non e' misurato, e' indovinato — e
       basta a spostare le finestre di quel tanto che rende I1 verde o rosso a
       caso.  ⭐ E la deriva fra i due orologi non c'entra: il cliente gira
       DENTRO la macchina di prova, quindi e' lo stesso hardware e resta un
       offset puro.
    """
    ses = [m for m in messaggi if m["nome"] == "SESSIONE" and m["verso"] == "server"]
    if not ses or ses[0]["istante_ms"] is None:
        return None, "nella traccia non c'e' nessun SESSIONE con un istante"
    presa = [r for r in righe if "posto PRESO da" in r]
    if not presa:
        return None, "nel registro non c'e' nessun «posto PRESO» per questo utente"
    t1 = sod_dalla_riga(presa[0])
    if t1 is None:
        return None, "la riga «posto PRESO» non porta un'ora leggibile"
    off1 = t1 - ses[0]["istante_ms"] / 1000.0
    via = [r for r in righe if "posto LASCIATO da" in r] or \
          [r for r in righe if "l'ultima sessione di" in r] or \
          [r for r in righe if "STACCATO per silenzio" in r]
    if not via or ultimo_blocco_ms is None:
        # ⚠ Una seconda ancora non c'e': l'offset si USA lo stesso ma si
        #   DICHIARA che non e' stato verificato.  Non e' la stessa cosa.
        return off1, ("⚠ UNA SOLA ANCORA (posto PRESO): l'offset %.3f NON e' "
                      "stato verificato con una seconda" % off1)
    t2 = sod_dalla_riga(via[-1])
    if t2 is None:
        return off1, "⚠ la seconda ancora non porta un'ora leggibile"
    off2 = t2 - ultimo_blocco_ms / 1000.0
    if abs(off2 - off1) > tolleranza:
        return None, ("⛔ le due ancore non vanno d'accordo: %.3f contro %.3f "
                      "(%.0f ms, tolleranza %.0f ms) — NON giudico le finestre"
                      % (off1, off2, (off2 - off1) * 1000, tolleranza * 1000))
    return off1, ("⭐ due ancore d'accordo entro %.0f ms (offset %.3f)"
                  % (abs(off2 - off1) * 1000, off1))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA PAGINA — un Firefox VERO, sul portatile, contro il prodotto
# ═══════════════════════════════════════════════════════════════════════════
def tabella_motivo_servita():
    """⛔ La tabella `MOTIVO` **del file che il server sta servendo**.

    ⚠ Non da `src/pagina.html` del repository: dalla copia in `$ALBERO`, che e'
      quella passata al server con `--pagina`.  ⭐ Serve a legare la frase che il
      browser ha MOSTRATO al codice che l'ha prodotta: senza questo legame «la
      pagina ha scritto una frase» non dice da quale motivo l'ha costruita, e un
      giorno in cui la pagina sbagliasse riga il banco resterebbe verde.

    ⚠ La tabella si legge da Marionette solo se `MOTIVO` fosse una proprieta' di
      `window`, e non lo e': un `const` in cima a uno `<script>` classico crea
      un legame di SCRIPT, non una proprieta' dell'oggetto globale, e il
      sandbox di Marionette non lo vede.  `[M]` 24 agosto 2026, primo giro:
      tornava `null` per tutti e tre i codici.
    """
    rc, out, _ = root("grep -aoE \"^  0x0[0-9A-Fa-f]: \\\"[^\\\"]*\\\"\" %s/src/pagina.html"
                      % ALB)
    tab = {}
    for r in (out or "").splitlines():
        m = re.match(r'\s*(0x[0-9A-Fa-f]{2}):\s*"(.*)"\s*$', r.strip())
        if m:
            tab[m.group(1).lower()] = m.group(2)
    return tab


def guarda_la_pagina(marionette=2830):
    """⛔ Che frase legge l'UTENTE quando la tabella e' piena.

    ⚠ Firefox gira sul PORTATILE e si collega alla macchina di prova: cosi' non
      aggiunge carico alla GPU che si sta misurando.  ⛔ E se non parte, o se la
      pagina non arriva a mandare l'`ATTACCA`, si torna `None` — «non ho
      guardato» non e' «non ha detto niente».
    """
    try:
        M = _carica("b46mar", os.path.join(QUI, "07-b46-marionette.py"))
    except Exception as e:
        return {"frase": None, "perche": "non ho potuto caricare Marionette: %s" % e}
    p = mar = prof = None
    try:
        p, mar, prof = M.accendi(porta=marionette, headless=True, largo=1200, alto=800)
        mar.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        mar.vai("https://%s:%d/" % (IND, PORTA))
        mar.js("""document.getElementById('utente').value = arguments[0];
                  document.getElementById('parola').value = arguments[1];
                  document.getElementById('vai').click(); return true;""",
               [RESPINTO[0], os.environ.get("PAROLA_UTENTE", "dec-pieno-2026")])
        t0 = time.time()
        frase = ""
        while time.time() - t0 < 60:
            frase = (mar.js("return document.getElementById('esito').textContent")
                     ["value"] or "").strip()
            if frase:
                break
            time.sleep(0.4)
        schermo = mar.js("return document.body.dataset.schermo || '(nessuno)'")["value"]
        reg = (mar.js("return document.getElementById('registro').innerText.slice(-1500)")
               ["value"] or "")
        if not frase:
            return {"frase": None, "schermo": schermo, "registro": reg,
                    "perche": "in 60 s la pagina non ha scritto nessun esito"}
        # ⛔ E si legge anche CHE COSA la pagina crede di aver ricevuto: la sua
        #    tabella `MOTIVO`, interrogata sul motivo che ci interessa.  ⚠ E'
        #    la PAGINA a rispondere, non io a dedurlo dal suo sorgente.
        tab = {}
        for cod in (MOTIVO_GIUSTO, MOTIVO_BUDGET, MOTIVO_BUGIARDO):
            try:
                tab["0x%02x" % cod] = mar.js(
                    "return (typeof MOTIVO !== 'undefined' && MOTIVO[arguments[0]]) "
                    "|| null", [cod])["value"]
            except Exception:
                tab["0x%02x" % cod] = None
        # ⛔ E IL LEGAME FRA LA FRASE E IL CODICE: si confronta con la voce
        #    `0x0E` della tabella del file che il server serve.  Se combacia
        #    byte per byte, la pagina ha costruito la frase da QUEL motivo.
        servita = tabella_motivo_servita()
        motivo = None
        for cod, testo in servita.items():
            if testo.strip() == frase:
                motivo = int(cod, 16)
                break
        return {"frase": frase, "schermo": schermo, "registro": reg,
                "tabella_motivo_dal_browser": tab,
                "tabella_motivo_servita": servita,
                "motivo": motivo}
    except Exception as e:
        return {"frase": None, "perche": "%s: %s" % (type(e).__name__, e)}
    finally:
        if p is not None:
            try:
                M.spegni(p, prof)
            except Exception:
                pass


def principale():
    a = argparse.ArgumentParser()
    a.add_argument("--certifica", action="store_true",
                   help="⭐ innesta i guasti e conta sano→guasto→risanato, "
                        "senza rete e senza macchina")
    a.add_argument("--durata", type=float, default=160.0,
                   help="quanto restano attaccati i clienti che riempiono")
    a.add_argument("--rifiuti", type=int, default=10,
                   help="⛔ quanti rifiuti di fila (un difetto che si vede solo "
                        "alla decima e' quello che l'utente trovera')")
    a.add_argument("--finestra", type=float, default=12.0,
                   help="quanto e' larga la finestra «prima» e «dopo»")
    a.add_argument("--guardia", type=float, default=2.0)
    a.add_argument("--niente-pagina", action="store_true")
    a.add_argument("--niente-lucchetto", action="store_true",
                   help="⛔ per la messa a punto: i numeri di un giro senza "
                        "lucchetto NON si riferiscono")
    a.add_argument("--fuori", default=os.path.join(FUORI, "esiti.json"))
    o = a.parse_args()

    if o.certifica:
        return certifica()
    return giro_vero(o)


def giro_vero(o):
    from datetime import datetime
    cliente = _carica("b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
    for k, v in (("PORTA", str(PORTA)), ("LAV", LAV), ("ALBERO", ALB),
                 ("UTENTE", DENTRO[0][0]), ("UID_B", str(DENTRO[0][1])),
                 ("MACCHINA", MACCHINA), ("PAROLA_SUDO", PAROLA_SUDO),
                 ("IND", IND), ("DENTRO_ALB", DENTRO_ALB),
                 ("DENTRO_LAV", DENTRO_LAV), ("FUORI", FUORI)):
        os.environ[k] = v
    B70 = _carica("b70ritmo", os.path.join(QUI, "09-b70-ritmo.py"))
    # ⛔⛔ E POI SI CONTROLLA CHE L'IMPORT ABBIA PRESO IL MIO AMBIENTE: un modulo
    #     che misurasse sulla porta di un altro banco darebbe numeri plausibili
    #     invece di un errore (`LEZIONI.md` §1.26).
    if str(B70.PORTA) != str(PORTA) or B70.LAV != LAV or B70.ALB != ALB:
        raise SystemExit("⛔ NON MISURO: 09-b70-ritmo non ha preso il mio "
                         "ambiente (porta %s, lavoro %s, albero %s)"
                         % (B70.PORTA, B70.LAV, B70.ALB))

    esiti = {"quando": datetime.now().isoformat(timespec="seconds"),
             "porta": PORTA, "albero": ALB, "durata": o.durata,
             "rifiuti": o.rifiuti, "predicati": {}}

    _log("0 · LA TARATURA DEL METRO — e se non passa, non misuro")
    tarato, righe = taratura(B70, cliente)
    esiti["taratura"] = righe
    if not tarato:
        _ko("⛔ il metro non e' tarato: NON MISURO")
        return 3

    if not terreno_controlla():
        return 2
    if not spedisci_lettori(B70):
        return 2

    numeri = i_due_numeri()
    esiti["numeri"] = numeri
    _log("I DUE NUMERI, letti dai sorgenti che hanno prodotto il binario")
    _inf("MAX_ATTACCATE = %s · MAX_FIGLI = %s" % (numeri["max_attaccate"],
                                                  numeri["max_figli"]))
    _inf("md5: %s" % numeri["md5"])
    esiti["predicati"]["p_due_numeri"] = p_due_numeri(numeri)

    luc = None
    if not o.niente_lucchetto:
        os.environ["LUCCHETTO"] = os.environ.get(
            "LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
        luc = _carica("luc", os.path.join(QUI, "09-lucchetto.py"))
        _log("IL LUCCHETTO DELLA GPU — «10-a8»")
        luc.prendi("10-a8", secondi=2400, attesa=5400)
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON si riferiscono")
    try:
        rc = giro_dentro_al_lucchetto(o, B70, esiti)
    finally:
        if luc is not None:
            luc.molla("10-a8")
    os.makedirs(os.path.dirname(o.fuori), exist_ok=True)
    with open(o.fuori, "w") as f:
        json.dump(esiti, f, indent=1, ensure_ascii=False, default=str)
    _inf("gli esiti stanno in %s" % o.fuori)
    return rc


def giro_dentro_al_lucchetto(o, B70, esiti):
    pid = pid_del_server()
    if not pid:
        _ko("⛔ non ho il pid del server: NON MISURO")
        return 2
    _inf("il server e' il pid %d" % pid)

    # ── 1 · IL RIEMPIMENTO ────────────────────────────────────────────────
    _log("1 · IL RIEMPIMENTO — %d clienti per una tabella da %s"
         % (len(DENTRO), esiti["numeri"]["max_attaccate"]))
    riga0 = righe_registro()
    if riga0 is None:
        _ko("⛔ non ho letto il registro: da qui in poi ogni conto sarebbe "
            "cumulativo dall'accensione.  NON MISURO")
        return 2
    esiti["riga0"] = riga0
    rip = riempi(o.durata, registra=True)
    processi = rip["proc"]
    for u, _uid in DENTRO:
        _inf("cliente «%s» avviato (traccia dentro-%s.rcpreg)" % (u, u))
    # ⛔ Si ASPETTA che tutt'e due abbiano il posto, e lo si legge dal REGISTRO
    #    del prodotto: «ho lanciato due clienti» non e' «due posti sono presi».
    if not aspetta_posti(rip["riga0"]):
        _ko("⛔ i %d posti non sono stati presi in 90 s: NON MISURO il posto "
            "pieno" % len(DENTRO))
        for p in processi.values():
            p.kill()
        return 3
    _ok("i %d posti sono presi" % len(DENTRO))

    # ⭐ Le scene: senza, Mutter consegna solo quando qualcosa cambia e non c'e'
    #    nessun ritmo da confrontare.
    for u, uid in DENTRO:
        if scena_accendi(u, uid, "b93-%d" % uid):
            _ok("scena accesa per «%s» sul monitor «%s»" % (u, MONITOR_ATTESO))
        else:
            _ko("⚠ la scena di «%s» NON e' partita: il ritmo di questa sessione "
                "sara' quello di un desktop fermo" % u)
    time.sleep(o.finestra + o.guardia + 6.0)   # la scaldata + la finestra «prima»

    # ── 2 · IL RESPINTO, dieci volte ──────────────────────────────────────
    _log("2 · IL RESPINTO — %d tentativi di fila di «%s»" % (o.rifiuti, RESPINTO[0]))
    scatti = [fotografia(pid, riga0)]
    _inf("prima di tutto: %s" % scatti[0])
    t_ini = sod_adesso_sul_server()
    tentativi = []
    for k in range(o.rifiuti):
        nome = "respinto-%02d" % k
        rc, out, err = dentro(cliente_riga(RESPINTO[0], 2, registra=nome), 180)
        testo = out + err
        canale = leggi_traccia_canale(nome)
        msg = canale.get("messaggi", [])
        cong = [m for m in msg if m["nome"] == "CONGEDO" and m["verso"] == "server"]
        resp = [m for m in msg if m["nome"] == "RESPINTO"]
        nomi = [m["nome"] for m in msg]
        # ⛔ DOVE E' ARRIVATO — e le tre risposte sono diverse.
        if resp:
            arrivato = "RESPINTO"
        elif "ATTACCA" in nomi:
            arrivato = "ATTACCA"
        elif "CREDENZIALI" in nomi:
            arrivato = "CREDENZIALI"
        elif nomi:
            arrivato = nomi[-1]
        else:
            arrivato = None
        m = re.search(r"\[quic\] connessione TERMINATA: codice (\d+)", testo)
        # ⭐ §3.1 punto 3, letto dal lato che riceve: la capsula di chiusura
        #    della SESSIONE WebTransport, che e' un piano diverso dal QUIC.
        mw = re.search(r"\[wt\]\s+sessione chiusa dal server, codice (0x[0-9a-f]+)",
                       testo)
        t = {"giro": k, "arrivato_a": arrivato,
             "motivo": cong[0]["motivo"] if cong else None,
             "dettaglio": cong[0]["dettaglio"] if cong else None,
             "dettaglio_letto": cong[0]["dettaglio_letto"] if cong else False,
             "codice_quic": int(m.group(1)) if m else None,
             "codice_wt": int(mw.group(1), 16) if mw else None,
             "capsula_nuda": "capsula di chiusura NUDA" in testo,
             "messaggi": nomi,
             "lettore": canale.get("esito"),
             "coda": testo[-1500:]}
        tentativi.append(t)
        _inf("#%02d arrivato a %s · motivo %s · wt %s · quic %s · dettaglio «%s»"
             % (k, arrivato,
                ("%#04x" % t["motivo"]) if t["motivo"] is not None else "—",
                ("%#04x" % t["codice_wt"]) if t["codice_wt"] is not None else "—",
                t["codice_quic"], (t["dettaglio"] or "")[:70]))
        scatti.append(fotografia(pid, riga0))
    t_fine = sod_adesso_sul_server()
    esiti["tentativi"] = tentativi
    esiti["scatti"] = scatti
    esiti["tentativo_ini"] = t_ini
    esiti["tentativo_fine"] = t_fine
    esiti["predicati"]["p_ha_morso"] = p_ha_morso(tentativi)
    esiti["predicati"]["p_motivo_sul_filo"] = p_motivo_sul_filo(tentativi)
    esiti["predicati"]["p_dettaglio_nel_corpo"] = p_dettaglio_nel_corpo(tentativi)
    esiti["capsula"] = conti_capsula(riga0)
    _inf("§3.1 punto 3, dal lato che manda: chiusure ARMATE %s · capsule messe "
         "in coda %s" % (esiti["capsula"].get("rimandate"),
                         esiti["capsula"].get("spedite")))
    esiti["predicati"]["p_motivo_anche_nel_codice"] = p_motivo_anche_nel_codice(
        tentativi, esiti["capsula"])
    # ⛔ Dal SECONDO scatto in poi: il primo rifiuto e' il CONFINE, non uno
    #    strascico della ripetizione — vedi il riquadro del predicato.
    esiti["predicati"]["p_niente_strascichi"] = p_niente_strascichi(scatti[1:])

    # ── 3 · IL CONFINE ────────────────────────────────────────────────────
    _log("3 · IL CONFINE — quanto in la' arriva il respinto prima di essere respinto")
    reg = registro_da(riga0) or ""
    u = RESPINTO[0]
    # ⛔ `[o]` perche' la riga non conti se stessa, e `argv[0]` perche' il
    #    figlio si rinomina con `prctl` e `comm` resta «remotix» (vedi
    #    `fotografia()`).
    rc, out, _ = root("ps -eo args= | grep -- "
                      "'^remotix-figlio --figlio-intern[o] %s ' | head -3; "
                      "echo GNOME $(pgrep -u %d -c gnome-shell || true); "
                      "ls /run/user/%d >/dev/null 2>&1 && echo RUNTIME si || echo RUNTIME no"
                      % (u, RESPINTO[1], RESPINTO[1]))
    # ⛔ «Autenticato» si legge SUL FILO, non nel registro del server: il
    #    cliente manda `ATTACCA` solo dopo aver ricevuto `AMMESSO`, e i nomi dei
    #    messaggi vengono dalla traccia §11.1 letta dal lettore del canale.
    nomi0 = (tentativi[0].get("messaggi") or []) if tentativi else []
    confine = {
        "autenticato": ("AMMESSO" in nomi0) if nomi0 else None,
        "figlio_nato": bool(re.search(r"--figlio-interno %s " % re.escape(u), out)),
        "sessione_grafica": None,
        "palco_acceso": bool(re.search(r"fotogramma da «%s»" % re.escape(u), reg)),
        "messaggi_del_respinto": nomi0,
        "runtime_dir": "RUNTIME si" in out,
        "grezzo": out.strip()[:400],
    }
    m = re.search(r"GNOME (\d+)", out)
    if m:
        confine["sessione_grafica"] = int(m.group(1)) > 0
    esiti["confine"] = confine
    for k, v in confine.items():
        if k != "grezzo":
            _inf("%-18s %s" % (k, v))
    esiti["predicati"]["p_confine_del_rifiuto"] = p_confine_del_rifiuto(confine)

    # ── 4 · I1 — la finestra «dopo», e VIENE PRIMA DELLA PAGINA ─────────
    # ⛔ Il Firefox della prova successiva apre una sessione
    #    WebTransport vera contro questo server: se lo facesse mentre la
    #    finestra «dopo» si riempie, il confronto di I1 misurerebbe il
    #    BANCO invece del tentativo respinto.  ⇒ Prima si chiude «dopo».
    _log("5 · I1 — aspetto la finestra «dopo» e poi guardo chi era gia' dentro")
    aspetta = o.guardia + o.finestra + 3.0
    _inf("aspetto %.0f s perche' la finestra «dopo» sia piena" % aspetta)
    time.sleep(aspetta)
    # ⛔⛔ E LA SCENA SI SPEGNE **DOPO** CHE I CLIENTI HANNO FINITO — `[M]` 24
    #     agosto 2026, e prima era il contrario.
    #
    #     A scena spenta Mutter non consegna piu' niente, quindi il cliente
    #     smette di ricevere fotogrammi ma resta ATTACCATO fino al suo
    #     `--resta`.  ⇒ L'ultimo blocco della traccia cadeva **42 secondi**
    #     prima della riga «posto LASCIATO» del server, le due ancore
    #     dell'offset non andavano d'accordo, e I1 usciva «non giudico» su due
    #     sessioni misurate benissimo.
    # ⚠ Un banco che avesse avuto UNA sola ancora non se ne sarebbe accorto:
    #   avrebbe costruito le finestre con l'offset giusto e nessuno avrebbe
    #   saputo che il metro era in dubbio.
    for u, p in processi.items():
        try:
            p.wait(timeout=o.durata + 120)
        except Exception:
            p.kill()
    for u, uid in DENTRO:
        scena_spegni(uid)
    esiti["I1"] = {}
    peggiore = None
    for u, uid in DENTRO:
        canale = leggi_traccia_canale("dentro-%s" % u)
        letto, giornale = leggi_traccia_video("dentro-%s" % u)
        righe_u = righe_ancora(riga0, u)
        off, come = offset_del_cliente(canale.get("messaggi", []), righe_u,
                                       canale.get("ultimo_blocco_ms"))
        _inf("«%s»: %d fotogrammi nella traccia · %s" % (u, len(giornale), come))
        fin = spezza_in_finestre(giornale, off, esiti["tentativo_ini"],
                                 esiti["tentativo_fine"], o.finestra, o.guardia)
        guai = ancora_finestre(fin, esiti["tentativo_ini"],
                               esiti["tentativo_fine"]) if fin else \
            ["l'offset fra i due orologi non e' stato misurato: %s" % come]
        n = {k: B70.misura(v, o.finestra, scaldata_s=0.0)
             for k, v in (fin or {"prima": [], "durante": [], "dopo": []}).items()}
        p = p_I1(n["prima"], n["durante"], n["dopo"], guai)
        esiti["I1"][u] = {"offset": off, "come": come, "guai_ancora": guai,
                          "lettore": letto,
                          "finestre": {k: {kk: vv for kk, vv in (v or {}).items()
                                           if kk != "server"}
                                       for k, v in n.items()},
                          "predicato": p}
        for nome in ("prima", "durante", "dopo"):
            q = n[nome]
            _inf("  %-8s %s fotogrammi · %s/s · peggior secondo %s · p95 %s ms · "
                 "chiavi %s · deriva %s ms · buchi %s"
                 % (nome, q.get("fotogrammi"), q.get("fps"),
                    q.get("fps_finestra_min"), q.get("intervallo_p95_ms"),
                    q.get("chiavi"), q.get("deriva_fine_ms"), q.get("buchi_numero")))
        (_ok if p[0] else (_ko if p[0] is False else _dub))("«%s» — %s" % (u, p[1]))
        if peggiore is None or (p[0] is False) or (p[0] is None and peggiore[0] is True):
            peggiore = p
    esiti["predicati"]["p_I1"] = peggiore or _muto("nessuna sessione misurata")

    # ── 5 · LA PAGINA — a finestre chiuse ─────────────────────────────────
    if not o.niente_pagina:
        _log("5 · LA PAGINA — un Firefox VERO, sul portatile, a tabella piena")
        # ⛔ E LA TABELLA VA RIEMPITA DI NUOVO: i due clienti di prima sono
        #    finiti con la finestra «dopo», e una pagina che entrasse
        #    tranquillamente misurerebbe il caso opposto a quello che dichiara.
        #    ⚠ Senza il controllo positivo qui sotto, «la pagina ha mostrato una
        #      frase» non direbbe se quella frase e' del posto pieno.
        aspetta_tabella_vuota()
        rip = riempi_e_aspetta(180)
        pieno = rip is not None
        if not pieno:
            rip = {"proc": {}}
            _ko("⛔ la tabella non si e' riempita: NON guardo la pagina")
            pag = {"frase": None,
                   "perche": "la tabella non si e' riempita: la pagina avrebbe "
                             "misurato un server LIBERO"}
        else:
            _ok("i %d posti sono presi: adesso il Firefox e' il respinto"
                % len(DENTRO))
            pag = guarda_la_pagina()
        for pr in rip["proc"].values():
            try:
                pr.kill()
            except Exception:
                pass
        root("pkill -f '%s'; true" % modello_cliente("--porta %d" % PORTA))
        esiti["pagina"] = pag
        if pag.get("frase") is not None:
            _inf("la pagina mostra: «%s»" % pag["frase"])
            _inf("data-schermo: %s" % pag.get("schermo"))
            _inf("la sua tabella MOTIVO: %s" % pag.get("tabella_motivo"))
        else:
            _dub("non ho guardato la pagina: %s" % pag.get("perche"))
        esiti["predicati"]["p_frase_della_pagina"] = p_frase_della_pagina(pag)
    else:
        esiti["predicati"]["p_frase_della_pagina"] = _muto("--niente-pagina")

    # ── 6 · IL POSTO CHE TORNA ────────────────────────────────────────────
    _log("6 · E QUANDO UNO SE NE VA, IL POSTO TORNA?")
    esiti["uscite"] = uscite = []
    # (a) LA MORTE IMPROVVISA — il filo cade senza dire niente.  ⚠ Lo sfratto di
    #     §4.4 NON aiuta: vale solo fra client dello stesso utente, e chi aspetta
    #     e' un altro utente.  ⇒ Si aspetta `SILENZIO` (30 s).
    # ⚠ L'atteso e' **18 s**, e non i 30 di `SILENZIO`: con la LINEA MORTA
    #   accesa (predefinito dal 24 agosto 2026) il filo cade a ~10 s di
    #   silenzio, e i secondi in piu' sono il mio ciclo di ritenta.
    uscite.append(prova_uscita(o, "morte improvvisa (SIGKILL al client)",
                               brutale=True, atteso_s=18.0, tetto_s=75.0))
    # (b) IL COMMIATO — il client finisce e manda `CONGEDO`.
    uscite.append(prova_uscita(o, "chiusura pulita (il `--resta` del cliente scade)",
                               brutale=False, atteso_s=8.0, tetto_s=70.0))
    esiti["predicati"]["p_posto_torna"] = p_posto_torna(uscite)

    # ── L'ESITO ───────────────────────────────────────────────────────────
    _log("L'ESITO")
    rossi = muti = 0
    for nome, (passa, perche) in esiti["predicati"].items():
        if passa is True:
            _ok("%-26s %s" % (nome, perche))
        elif passa is False:
            _ko("%-26s %s" % (nome, perche)); rossi += 1
        else:
            _dub("%-26s %s" % (nome, perche)); muti += 1
    _inf("%d predicati · %d rossi · %d «non giudico»"
         % (len(esiti["predicati"]), rossi, muti))
    disegno(esiti)
    return 1 if rossi else (3 if muti else 0)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA RIGA DI DISEGNO CHE SI CONSEGNA ALLA FASE — ⚠ e' un DISEGNO, non una
#    decisione: la decisione la prende l'utente del progetto.
# ═══════════════════════════════════════════════════════════════════════════
def disegno(esiti):
    """Stampa il disegno alla luce di quel che questo giro ha misurato.

    ⛔ Sta QUI, in fondo al banco che l'ha misurato, e non in un documento: un
       disegno separato dalla misura che lo giustifica invecchia senza che
       nessuno se ne accorga.
    """
    _log("⭐ IL DISEGNO — `BUDGET_PIENO 0x06` sostituisce `0x0E` o si aggiunge?")
    for r in [
        "⛔ SI AGGIUNGE.  Sono DUE fatti diversi, e `RCP.md` §8.2 ha gia' un",
        "   codice per ciascuno:",
        "",
        "   · `0x0E SESSIONE_NON_SERVIBILE` — «l'attacco e' ben formato ma non si",
        "     puo' servire».  E' il codice di un LIMITE AMMINISTRATIVO: la tabella",
        "     delle sessioni e' piena.  ⭐ Oggi e' quello che esce, ed e' giusto:",
        "     il numero e' un `#define`, non una capacita' misurata.",
        "",
        "   · `0x06 BUDGET_PIENO` — «la macchina non ha piu' capacita' di",
        "     codifica».  E' il codice di un LIMITE FISICO: il codificatore non",
        "     ce la fa, e il tetto amministrativo non c'entra.",
        "",
        "⛔ E la ragione per cui NON si sostituiscono e' che all'utente vanno",
        "   dette due cose diverse, e portano a due GESTI diversi:",
        "",
        "   | quando | codice | la frase che l'utente deve leggere |",
        "   |---|---|---|",
        "   | la tabella delle sessioni e' piena | `0x0E` | «questo server ha gia'",
        "     tutte le sessioni che puo' tenere: riprova fra poco, o chiedi",
        "     all'amministratore di alzare il tetto» |",
        "   | il budget del codificatore e' esaurito | `0x06` | «questa macchina non",
        "     ha piu' capacita' di codifica: riprova fra poco, o entra chiedendo",
        "     meno qualita'» ⭐ e il secondo mezzo e' un GESTO, non una consolazione |",
        "",
        "⚠ E la frase di OGGI per `0x0E` — «quella sessione non si puo' servire» —",
        "  e' GENERICA, non falsa.  Non dice ne' di chi e' la colpa ne' che cosa",
        "  fare, e `RCP.md` riga 2301 chiede che ogni motivo sia «mostrabile in una",
        "  frase comprensibile».  ⛔ Ma `0x0E` copre gia' tre casi diversi in",
        "  `rcp.c` (disposizione sconosciuta, tela sotto il minimo legale, tabella",
        "  piena): una frase piu' precisa per uno dei tre sarebbe FALSA per gli",
        "  altri due.  ⇒ O la frase resta generica, o `0x0E` si spacca — e",
        "  `BUDGET_PIENO` e' gia' meta' di quella spaccatura.",
        "",
        "⛔ E il pezzo che questo banco ha misurato e che il disegno DEVE portarsi",
        "   dietro: **oggi il rifiuto arriva dopo che il desktop e' acceso**.",
        "   Qualunque sia il codice, un `BUDGET_PIENO` deciso al momento",
        "   dell'`ATTACCA` arriva quando la sessione grafica del respinto e' gia'",
        "   in piedi — cioe' quando il budget e' gia' stato speso.  ⇒ Il budget va",
        "   chiesto **prima di far nascere il figlio**, e quel punto e' una riga",
        "   sola: `consegna_verdetto()` in `src/main.c`.",
    ]:
        print("    %s" % r, flush=True)
    p = (esiti.get("predicati") or {}).get("p_confine_del_rifiuto")
    if p and p[0] is False:
        _ko("e questo giro lo ha MISURATO: " + p[1][:200])


def prova_uscita(o, come, brutale, atteso_s, tetto_s):
    """Riempie, respinge, fa uscire uno dei dentro, e guarda se il respinto entra.

    ⛔⛔ **I DUE MODI DI ANDARSENE NON SONO LO STESSO MODO**, e la differenza e'
        tutta la misura:

      · **la chiusura pulita** — il `--resta` del cliente scade, la connessione
        QUIC si chiude col suo `CONNECTION_CLOSE`, il server lo vede e libera il
        posto subito (`rcp_chiusa_dal_client()` → `posto_lascia()`).
        ⚠ E NON si ottiene con un `SIGTERM`: `01-b3-cliente.py` non ha nessun
          gestore di segnale, quindi un `SIGTERM` uccide il processo senza che
          parta un solo pacchetto — sarebbe la morte improvvisa con un altro
          nome, cioe' la stessa prova due volte.  ⇒ Il cliente si lancia con un
          `--resta` CORTO e lo si lascia finire da solo.
      · **la morte improvvisa** — `SIGKILL`, e sul filo non parte niente.  Il
        posto resta del fantasma finche' `rcp_tempo()` non lo stacca per
        silenzio (`SILENZIO` = 30 000 ms, `rcp.c:263`).  ⛔ Lo SFRATTO di §4.4
        NON aiuta qui: vale solo **fra client dello stesso utente**, e chi
        aspetta e' un utente diverso.

    ⛔ E i due istanti si leggono dagli OROLOGI DEL SERVER, dalle sue righe di
       registro — non dal mio orologio dopo un giro di ssh, che aggiungerebbe
       alla misura il tempo del banco.

    ⛔ E la sollecitazione si CONTA: se il respinto non e' respinto PRIMA che uno
       esca, questa prova non ha misurato niente, e lo dice.
    """
    _log("   uscita «%s»" % come)
    esito = {"come": come, "secondi": None, "atteso_s": atteso_s,
             "tetto_s": tetto_s, "brutale": brutale}
    vittima, vittima_uid = DENTRO[-1]
    resta_vittima = 260 if brutale else 45
    rip = riempi_e_aspetta(260, corto=resta_vittima)
    if rip is None:
        esito["perche"] = ("⛔ la tabella non si e' riempita in tre giri: non ho "
                           "misurato (occupati: %s)" % occupati_adesso())
        _ko(esito["perche"])
        return esito
    proc, riga0 = rip["proc"], rip["riga0"]

    def spegni_tutto():
        for p in proc.values():
            try:
                p.kill()
            except Exception:
                pass
        root("pkill -f '%s'; true" % modello_cliente("--porta %d" % PORTA))


    # ⛔ IL CONTROLLO POSITIVO: PRIMA che uno esca, il respinto DEVE essere
    #    respinto per posto pieno.  Senza questa riga, «e' entrato» dopo non
    #    vorrebbe dire niente — poteva entrare anche prima.
    rc, out, err = dentro(cliente_riga(RESPINTO[0], 1, registra="uscita-prima"), 180)
    canale = leggi_traccia_canale("uscita-prima")
    cong = [m for m in canale.get("messaggi", [])
            if m["nome"] == "CONGEDO" and m["verso"] == "server"]
    if not cong or cong[0]["motivo"] != MOTIVO_GIUSTO:
        spegni_tutto()
        esito["perche"] = ("⛔ a tabella piena il respinto NON ha ricevuto %#04x "
                           "(ha ricevuto %s): questa prova non misura il posto "
                           "che torna" % (MOTIVO_GIUSTO,
                                          cong[0]["motivo"] if cong else "niente"))
        return esito
    _ok("il controllo positivo regge: a tabella piena il respinto prende %#04x"
        % MOTIVO_GIUSTO)

    riga1 = righe_registro()
    t_kill = None
    if brutale:
        root("pkill -9 -f '%s'; true" % modello_cliente("--utente %s" % vittima))
        t_kill = sod_adesso_sul_server()
        try:
            proc[vittima].kill()
        except Exception:
            pass
        _inf("«%s» ucciso con -9 alle %.3f (orologio del server)" % (vittima, t_kill or -1))
    else:
        _inf("aspetto che il `--resta %d` di «%s» scada da solo"
             % (resta_vittima, vittima))

    # ⛔ Si tenta finche' non entra, e l'istante buono lo dice il REGISTRO.
    entrato = None
    scade = time.time() + tetto_s
    tentativi = 0
    while time.time() < scade:
        rc, out, err = dentro(cliente_riga(RESPINTO[0], 1, registra="uscita-dopo"), 120)
        tentativi += 1
        if "⭐ SESSIONE" in (out + err):
            entrato = True
            break
        time.sleep(1.0)
    esito["tentativi_di_rientro"] = tentativi

    # ⛔ Il `grep` PRIMA del tetto: due sessioni vive scrivono migliaia di righe
    #    in trenta secondi, e le tre che servono starebbero fuori dal `tail`.
    reg = registro_da(riga1, FILTRO_ANCORE + "\\|linea-morta", tetto=600) or ""
    righe = reg.splitlines()
    presa = [r for r in righe if "posto PRESO da %s" % RESPINTO[0] in r]
    lascia = [r for r in righe if "posto LASCIATO da %s" % vittima in r]
    silenzio = [r for r in righe if "STACCATO per silenzio" in r and vittima in r]
    esito["riga_uscita"] = (lascia[:1] + silenzio[:1])[:1]
    esito["riga_entrata"] = presa[:1]
    t_via = None
    if brutale:
        # ⛔⭐ E L'ISTANTE DELLA MORTE LO DICE IL PRODOTTO, NON IL MIO OROLOGIO.
        #
        #     `[M]` 24 agosto 2026: `t_kill` si prende DOPO il giro di `ssh` che
        #     ha spedito il `-9` e DOPO un secondo giro per chiedere l'ora — due
        #     round-trip, cioe' un paio di secondi di BANCO dentro una misura da
        #     dieci.  ⇒ Il numero buono lo scrive il server da solo: la riga
        #     `linea-morta` porta `silenzio_ms`, cioe' **da quanto non vede un
        #     pacchetto** nell'istante in cui chiude — che e' esattamente «da
        #     quanto quel client e' morto».
        #
        # ⚠ E il MECCANISMO va detto accanto al numero: a chiudere NON e'
        #   `SILENZIO` di §5.3 (30 000 ms) ma la **LINEA MORTA** della fase 9,
        #   accesa per predefinito dal 24 agosto 2026.
        for r in righe:
            m = re.search(r"linea-morta .*silenzio_ms=(\d+) "
                          r"soglia_silenzio_ms=(\d+)", r)
            if m:
                esito["linea_morta"] = {"silenzio_ms": int(m.group(1)),
                                        "soglia_silenzio_ms": int(m.group(2)),
                                        "riga": r.strip()[:500]}
                break
        if silenzio:
            m = re.search(r"STACCATO per silenzio: (\d+) ms", silenzio[0])
            esito["silenzio_dichiarato_ms"] = int(m.group(1)) if m else None
        t_lasciato = (sod_dalla_riga(lascia[0]) if lascia else
                      (sod_dalla_riga(silenzio[0]) if silenzio else None))
        ms = (esito.get("linea_morta") or {}).get("silenzio_ms")
        if ms is None:
            ms = esito.get("silenzio_dichiarato_ms")
        if t_lasciato is not None and ms is not None:
            t_via = t_lasciato - ms / 1000.0      # l'ultimo segno di vita
            esito["morto_a"] = round(t_via, 3)
            esito["posto_libero_dopo_s"] = round(ms / 1000.0, 3)
            _inf("⭐ dal prodotto: l'ultimo pacchetto del client era %d ms prima "
                 "della chiusura ⇒ il posto e' tornato libero %.3f s dopo la "
                 "morte" % (ms, ms / 1000.0))
        else:
            t_via = t_kill
            esito["nota_orologio"] = ("⚠ il prodotto non ha dichiarato da quanto "
                                      "quel client taceva: uso il MIO istante "
                                      "del `-9`, che porta dentro due giri di ssh")
        esito["quando_lasciato"] = t_lasciato
    else:
        if lascia:
            t_via = sod_dalla_riga(lascia[0])
        esito["quando_lasciato"] = t_via
        esito["posto_libero_dopo_s"] = 0.0 if lascia else None
    t_dentro = sod_dalla_riga(presa[0]) if presa else None
    esito["quando_entrato"] = t_dentro
    if t_via is not None and t_dentro is not None and t_dentro >= t_via:
        esito["secondi"] = round(t_dentro - t_via, 3)
        # ⚠ E si dichiara che cosa c'e' DENTRO questo numero: il tempo del
        #   prodotto PIU' il mio ciclo di ritenta (un tentativo ogni ~2,5 s).
        #   Chi vuole il numero del solo prodotto guardi `posto_libero_dopo_s`.
        _ok("il posto e' tornato dopo %.2f s, e il respinto e' dentro (⚠ dentro "
            "ci sono anche i miei %d tentativi di rientro, uno ogni ~2,5 s)"
            % (esito["secondi"], tentativi))
    else:
        if not entrato:
            _ko("il respinto NON e' rientrato entro %.0f s (%d tentativi)"
                % (tetto_s, tentativi))
            esito["perche"] = "il respinto non e' rientrato entro il tetto"
        else:
            _dub("⚠ e' rientrato ma non ho i due istanti dal registro: "
                 "uscita %s, entrata %s" % (t_via, t_dentro))
            esito["perche"] = ("e' rientrato, ma il registro non porta i due "
                               "istanti: non misuro i secondi")
    spegni_tutto()
    return esito


if __name__ == "__main__":
    sys.exit(principale())
