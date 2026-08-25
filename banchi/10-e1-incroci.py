#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-e1-incroci — ⛔⛔ I TRE PUNTI IN CUI DUE CURE SI TOCCANO, sull'albero CUCITO.

    porta 8310 · albero /media/REMOTIX/src/10e1-src · lavoro /media/REMOTIX/tmp/10e1
    unita' remotix-8310 · lucchetto GPU `10-e1`

═══════════════════════════════════════════════════════════════════════════
⛔ PERCHE' ESISTE — nessun banco delle quattro cure fa QUESTA domanda
═══════════════════════════════════════════════════════════════════════════

Le quattro cure della fase 10 sono state provate **ciascuna sul proprio
albero**.  Cucite in uno solo, **tre di loro toccano gli stessi file**.  ⇒ Un
banco per cura ritrova il proprio numero e **non guarda** il punto in cui la
cura del vicino gli e' finita accanto.

Qui si guardano i tre punti, e ognuno ha il suo predicato che sa dare rosso:

  I1 · ⛔ `figlio.c` — C2 (rimonta il solo flusso) + C4 (il figlio posa il
       proprio nome).  ⇒ **Dopo il rimontaggio le righe del figlio portano
       ANCORA il nome?**  Se il rimontaggio azzerasse l'identita', il registro
       tornerebbe muto **proprio nel momento in cui serve**.

  I2 · ⛔ `webtransport.c` — C1 (la riga dello sfratto coi sette testimoni) +
       C4 (il gancio del registro).  ⇒ **La riga `linea-morta` porta il nome
       dell'utente?**
       ⚠ E il secondo pezzo: `fermo_ms=` dice di essere «da quando questa
       sessione e' nata» (commento a `webtransport.c:4786`) ma passa il
       contatore **globale** `giro_fermo_ms`.  ⇒ Due sfratti a distanza e si
       vede se il numero **riparte** o no.

  I3 · ⛔ `main.c` — C1 (il giro del padre, `sentinella_conti()`) + C3 (il no
       prima di `figli_assicura()`).  ⇒ **Il rifiuto esce ancora in ~0,6 s**, e
       **`sentinella_conti()` continua a scrivere la sua riga al minuto**
       (`[M]` 30 chiamate al minuto = una per ripasso).

═══════════════════════════════════════════════════════════════════════════
⛔ QUEL CHE QUESTO BANCO **NON** SA DIRE — detto prima, non dopo
═══════════════════════════════════════════════════════════════════════════

 · ⚠ Non misura nessuna delle quattro cure: quelle hanno i loro banchi, e
   questo li affianca.  Qui si guardano **solo le cuciture**.
 · ⛔ Non giudica il tempo del rifiuto da solo: quel numero e' di
   `10-c3-palchi.py`, che verifica anche che la scena sia quella giusta.  Qui
   si legge la **riga del registro** per dire che il no esce **dentro** il
   ciclo che C1 ha cambiato.
 · ⛔ `None` non e' zero: ogni funzione che non ha letto torna `None`, e chi
   giudica si rifiuta di giudicare.

Uso:
    python3 banchi/10-e1-incroci.py --certifica
    python3 banchi/10-e1-incroci.py --da-registro /media/REMOTIX/tmp/10e1/registro.log
    python3 banchi/10-e1-incroci.py --da-file /tmp/registro.txt
"""
import argparse
import os
import re
import subprocess
import sys

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA FORMA DELLA RIGA — una sola espressione, e vale per tutte
# ═══════════════════════════════════════════════════════════════════════════
#
# `registro.c` compone: «HH:MM:SS.mmm area    [nome] corpo», e la parentesi sta
# in **testa al corpo** apposta (⇒ un lettore vecchio continua a leggere).
# ⛔ Percio' qui l'area si prende dal campo 2 e il nome si cerca SOLO all'inizio
#    del corpo: cercarlo in mezzo troverebbe un `[…]` scritto da chiunque.
RIGA = re.compile(
    r"^(?P<ora>\d\d:\d\d:\d\d\.\d\d\d) (?P<area>\S+)\s+(?:\[(?P<chi>[^\]]*)\] )?"
    r"(?P<corpo>.*)$")

# ⭐ Le aree che SOLO il figlio scrive.  ⛔ «video» NON c'e': `codificatore.c`
#    usa `REG_CODIFICA "video"`, che e' **la stessa stringa** di `REG_VIDEO` del
#    padre — e battezzarla porterebbe a contare righe del padre fra quelle del
#    figlio.  Il riquadro di `figlio.c` lo dice esplicitamente.
AREE_DEL_FIGLIO = ("figlio", "appunti", "audio")

CAMBIO_STRADA = "la STRADA DEI PIXEL e' cambiata in"
BUCO_CICLO = "il ciclo del padre e' rimasto indietro di"


def spezza(testo):
    """⛔ `None` se non ho letto niente; una lista (anche vuota) se ho letto."""
    if testo is None:
        return None
    fuori = []
    for r in testo.splitlines():
        m = RIGA.match(r)
        if m:
            fuori.append(m.groupdict())
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
# I1 · `figlio.c` — l'identita' SOPRAVVIVE al rimontaggio del solo flusso?
# ═══════════════════════════════════════════════════════════════════════════
def identita_dopo_rimontaggio(testo, utente):
    """⭐ Quante righe del figlio, **dopo** l'ultimo cambio di strada, portano
       il nome.

    ⛔ «dopo l'ultimo», non «dopo il primo»: se i rimontaggi sono piu' d'uno, e'
       l'ultimo che dimostra che l'identita' regge a tutti.
    ⛔ E se il rimontaggio non c'e' stato torna `None` con il perche': una
       scena in cui la cucitura non e' stata sollecitata non prova niente
       (`LEZIONI.md` §1.30).
    """
    righe = spezza(testo)
    if righe is None:
        return None
    tagli = [i for i, r in enumerate(righe) if CAMBIO_STRADA in r["corpo"]]
    if not tagli:
        return {"rimontaggi": 0, "dopo": None, "col_nome": None, "quota": None,
                "anonime": None,
                "perche": "nessun rimontaggio: la cucitura non e' stata toccata"}
    dopo = [r for r in righe[tagli[-1] + 1:] if r["area"] in AREE_DEL_FIGLIO]
    if not dopo:
        return {"rimontaggi": len(tagli), "dopo": 0, "col_nome": None,
                "quota": None, "anonime": None,
                "perche": "nessuna riga del figlio dopo il rimontaggio"}
    # ⛔⛔ E L'AREA DA SOLA NON BASTA A DIRE CHI HA SCRITTO — trovato facendolo
    #     girare, 25 agosto 2026.  `figlio.c` e' compilato **nei due processi**:
    #     `figlio_vive()` gira nel figlio (e li' l'identita' c'e'), ma
    #     `figli_assicura()`, `fotogramma da «X»` e i comandi al palco li scrive
    #     il PADRE, che di identita' di processo non ne ha e non puo' averne —
    #     serve tutti gli inquilini.  ⚠ Quelle righe **nominano l'utente nel
    #     corpo**, quindi non sono mute: sono senza parentesi.
    #  ⇒ Il predicato chiede che nessuna riga resti **anonima**; la parentesi si
    #    conta a parte, perche' e' l'unica che non ha bisogno di nessun ponte.
    nel_corpo = re.compile(r"(?<![0-9A-Za-z_])%s(?![0-9A-Za-z_])"
                           % re.escape(utente))
    col = sum(1 for r in dopo if r["chi"] == utente)
    anonime = [r for r in dopo
               if r["chi"] != utente and not nel_corpo.search(r["corpo"])]
    return {"rimontaggi": len(tagli), "dopo": len(dopo), "col_nome": col,
            "quota": col / len(dopo), "anonime": len(anonime),
            "esempi_anonime": [r["corpo"][:70] for r in anonime[:3]],
            "perche": None}


def p_identita_regge(m):
    """⭐ Verde se dopo il rimontaggio **nessuna** riga resta anonima.

    ⛔ E' la domanda che conta: *«il registro torna muto proprio nel momento in
       cui serve?»*.  ⚠ Non *«tutte hanno la parentesi»* — quella darebbe rosso
       sulle righe del PADRE, che la parentesi non puo' averla e il nome ce
       l'hanno nel corpo.
    """
    if m is None or m.get("anonime") is None:
        return None
    return m["anonime"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# I2 · `webtransport.c` — la riga dello sfratto porta il nome?
# ═══════════════════════════════════════════════════════════════════════════
CAMPO = re.compile(r"(\w+)=([^\s]+)")


def sfratti(testo):
    """Le righe `linea-morta`, ciascuna coi suoi campi e col nome (o senza)."""
    righe = spezza(testo)
    if righe is None:
        return None
    fuori = []
    for r in righe:
        if not r["corpo"].startswith("linea-morta "):
            continue
        c = dict(CAMPO.findall(r["corpo"]))
        fuori.append({"ora": r["ora"], "chi": r["chi"], "area": r["area"],
                      "causa": c.get("causa"),
                      "fermo_ms": int(c["fermo_ms"]) if "fermo_ms" in c else None,
                      "giri_fermi": int(c["giri_fermi"]) if "giri_fermi" in c else None,
                      "saltati": int(c["saltati"]) if "saltati" in c else None,
                      "provenienza": r["corpo"].split()[1]})
    return fuori


def buchi(testo):
    """Le righe del buco del ciclo (C1), col nome o senza."""
    righe = spezza(testo)
    if righe is None:
        return None
    return [{"ora": r["ora"], "chi": r["chi"]}
            for r in righe if BUCO_CICLO in r["corpo"]]


def nome_per_area(testo):
    """⭐ Quante righe, per AREA, portano `[nome]` in testa al corpo.

    ⛔ E' una MISURA, non un giudizio: dice **dove** la cura di C4 arriva e dove
       no.  ⚠ Non e' la «frazione attribuibile» di `10-b96-registro.py`: quella
       conta anche i nomi che il **corpo** porta da se' e il ponte
       provenienza→utente.  ⇒ Qui si guarda solo la parentesi, che e' l'unica
       che non ha bisogno di nessun ponte.
    ⛔ `None` se non ho letto.
    """
    righe = spezza(testo)
    if righe is None:
        return None
    per = {}
    for r in righe:
        d = per.setdefault(r["area"], {"righe": 0, "col_nome": 0})
        d["righe"] += 1
        if r["chi"]:
            d["col_nome"] += 1
    for d in per.values():
        d["quota"] = d["col_nome"] / d["righe"]
    return per


def p_sfratto_col_nome(ss):
    """⛔ `None` se non c'e' stato nessuno sfratto: senza sollecitazione non si
       giudica.  Verde solo se **ogni** riga di sfratto porta un nome."""
    if ss is None or not ss:
        return None
    return all(s["chi"] for s in ss)


def fermo_riparte(ss):
    """⭐ ⛔ `fermo_ms` e' **per sessione** (come dice il commento) o **globale**?

    Due sfratti a distanza: se il campo fosse per-sessione, il secondo non
    potrebbe portare i buchi accumulati **prima che quella sessione nascesse**.
    ⇒ Se il secondo e' >= al primo **e** il primo e' gia' > 0, il numero non e'
      ripartito.  ⛔ `None` con meno di due sfratti o senza il campo.
    """
    if ss is None or len(ss) < 2:
        return None
    v = [s["fermo_ms"] for s in ss if s["fermo_ms"] is not None]
    if len(v) < 2:
        return None
    # ⛔⛔ E SE SONO TUTTI ZERO NON SI GIUDICA — trovato facendolo girare, 25
    #     agosto 2026.  Con `fermo_ms=0` dappertutto le due letture — «per
    #     sessione» e «globale» — dicono la STESSA cosa: il ciclo del padre non
    #     si e' mai fermato, quindi la domanda non ha risposta.  ⚠ Giudicare
    #     «non riparte» li' sarebbe un rosso su una prova che non ha morso
    #     (`LEZIONI.md` §1.30), ed e' quel che questo predicato faceva.
    if max(v) == 0:
        return None
    # ⚠ «riparte» vuol dire che almeno una volta il numero e' SCESO.
    return any(v[i + 1] < v[i] for i in range(len(v) - 1))


# ═══════════════════════════════════════════════════════════════════════════
# I3 · `main.c` — `sentinella_conti()` scrive ancora, e a che ritmo?
# ═══════════════════════════════════════════════════════════════════════════
GUARDIANO = re.compile(r"guardiano: chiamate=(\d+) peggiore_ms=(\d+) "
                       r"giri_fermi=(\d+) giro_peggiore_ms=(\d+)")


def _sec(ora):
    h, m, s = ora.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def guardiano_al_minuto(testo):
    """⭐ Le righe «guardiano: chiamate=…», e il **passo** fra due conteggi.

    ⛔ Il numero che conta non e' `chiamate=` (e' cumulativo): e' la
       DIFFERENZA fra due righe consecutive divisa per il tempo fra loro.
       `[M]` l'autore di C1 ha misurato 30 al minuto = una per ripasso.
    ⛔ Con meno di due righe non si misura un ritmo: `None`.
    """
    righe = spezza(testo)
    if righe is None:
        return None
    v = []
    for r in righe:
        m = GUARDIANO.search(r["corpo"])
        if m:
            v.append({"ora": r["ora"], "chi": r["chi"],
                      "chiamate": int(m.group(1)),
                      "peggiore_ms": int(m.group(2)),
                      "giri_fermi": int(m.group(3))})
    if len(v) < 2:
        return {"righe": len(v), "al_minuto": None, "campioni": v,
                "perche": "meno di due righe: non si misura un ritmo"}
    passi = []
    for i in range(len(v) - 1):
        dt = _sec(v[i + 1]["ora"]) - _sec(v[i]["ora"])
        dn = v[i + 1]["chiamate"] - v[i]["chiamate"]
        # ⛔ Un contatore che torna indietro vuol dire che il server e'
        #    RIPARTITO in mezzo: quel passo non si misura, non vale zero.
        if dt > 0 and dn >= 0:
            passi.append(60.0 * dn / dt)
    if not passi:
        return {"righe": len(v), "al_minuto": None, "campioni": v,
                "perche": "nessun passo misurabile (il server e' ripartito?)"}
    return {"righe": len(v), "al_minuto": sum(passi) / len(passi),
            "massimo_al_minuto": max(passi), "passi": passi,
            "campioni": v, "perche": None}


def p_guardiano_scrive(g, atteso=30.0, tolleranza=0.25):
    """⛔ Verde se il ritmo sta entro il ±25 % delle 30 al minuto misurate da C1.

    ⚠ La tolleranza non e' generosita': il conteggio esce **ogni minuto** e i
      ripassi sono a 2 s, quindi un ritardo di un paio di ripassi su una
      finestra di 60 s vale gia' qualche punto percentuale.

    ⛔⛔ E SI GIUDICA SUL **MASSIMO**, NON SULLA MEDIA — corretto il 25 agosto
        2026, dopo che questo predicato ha dato ROSSO su codice giusto.
        `wt_sorveglia_locali()` chiama il guardiano **solo se c'e' almeno una
        sessione attaccata**; un registro di campagna contiene lunghi tratti a
        ZERO sessioni (le aperture, gli sgomberi, i cambi di binario), e la
        media su quel registro dice 1,1 al minuto su un prodotto sanissimo.
        ⇒ La domanda e' *«quando ci sono inquilini, il ripasso chiama ancora
          una volta per giro?»*, e a quella risponde il minuto migliore.

    ⚠⚠ E QUESTO PREDICATO NON SI LEGGE SU UN BINARIO CON L'INNESTO di
       `10-c1-innesta.py`: li' `ripassa_sessioni_locali()` **salta**
       `sentinella_locali()` ogni volta che la leva e' armata, quindi il
       contatore non sale per costruzione.  ⛔ Si guarda su un binario NUDO.
    """
    if g is None or g.get("massimo_al_minuto") is None:
        return None
    return abs(g["massimo_al_minuto"] - atteso) <= atteso * tolleranza


# ═══════════════════════════════════════════════════════════════════════════
def root(cmd):
    p = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", MACCHINA,
         "printf '%%s\\n' '%s' | sudo -S -p '' bash -c %s"
         % (PAROLA_SUDO, _cita(cmd))],
        capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _cita(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def leggi(percorso):
    rc, out, _ = root("cat %s 2>/dev/null" % percorso)
    if rc != 0 or not out:
        return None
    return out


def riferisci(testo, utente):
    rossi, muti = [], []

    def dillo(nome, v, extra=""):
        if v is True:
            _ok("%s %s" % (nome, extra))
        elif v is False:
            _ko("%s %s" % (nome, extra)); rossi.append(nome)
        else:
            _dub("⚠ %s — NON HO MISURATO %s" % (nome, extra)); muti.append(nome)

    _log("I1 · `figlio.c` — C2 (rimonta il solo flusso) + C4 (il nome)")
    m = identita_dopo_rimontaggio(testo, utente)
    if m is None:
        _dub("⚠ registro non letto")
        muti.append("I1")
    else:
        _inf("rimontaggi del solo flusso: %s · righe del figlio DOPO l'ultimo: "
             "%s · con la parentesi «[%s]»: %s · ⛔ ANONIME: %s"
             % (m["rimontaggi"], m["dopo"], utente, m["col_nome"],
                m["anonime"]))
        for e in (m.get("esempi_anonime") or []):
            _dub("anonima: %s" % e)
        if m["perche"]:
            _inf("⚠ %s" % m["perche"])
        dillo("I1 · l'identita' del figlio sopravvive al rimontaggio",
              p_identita_regge(m),
              "" if m["quota"] is None
              else "(parentesi sul %.1f %%; il resto e' del PADRE, che nomina "
                   "l'utente nel corpo)" % (100 * m["quota"]))

    _log("I2 · `webtransport.c` — C1 (lo sfratto) + C4 (il nome)")
    ss = sfratti(testo)
    bb = buchi(testo)
    if ss is None:
        _dub("⚠ registro non letto"); muti.append("I2")
    else:
        _inf("righe `linea-morta`: %d · col nome: %d"
             % (len(ss), sum(1 for s in ss if s["chi"])))
        for s in ss[:6]:
            _inf("   [%s] %s causa=%s fermo_ms=%s giri_fermi=%s saltati=%s"
                 % (s["chi"] or "MUTA", s["provenienza"], s["causa"],
                    s["fermo_ms"], s["giri_fermi"], s["saltati"]))
        dillo("I2 · la riga dello sfratto porta il nome dell'utente",
              p_sfratto_col_nome(ss))
        if bb is not None:
            _inf("righe del buco del ciclo: %d · col nome: %d"
                 % (len(bb), sum(1 for b in bb if b["chi"])))
            dillo("I2-bis · la riga del buco del ciclo porta il nome",
                  None if not bb else all(b["chi"] for b in bb))
        r = fermo_riparte(ss)
        if r is None:
            _dub("⚠ `fermo_ms` fra due sfratti — NON HO MISURATO (servono due "
                 "sfratti col campo)")
        elif r:
            _ok("⭐ `fermo_ms` RIPARTE fra uno sfratto e l'altro: e' per sessione")
        else:
            _ko("⛔ `fermo_ms` NON riparte: e' il contatore GLOBALE, e il "
                "commento di `webtransport.c` dice un'altra cosa")
            rossi.append("I2-ter")

    _log("⭐ LA MISURA CHE SPIEGA I2 — chi porta `[nome]` e chi no, per area")
    per = nome_per_area(testo)
    if per is None:
        _dub("⚠ registro non letto")
    else:
        for a in sorted(per, key=lambda x: -per[x]["righe"]):
            d = per[a]
            _inf("%-9s %7d righe · col nome %7d (%5.1f %%)"
                 % (a, d["righe"], d["col_nome"], 100 * d["quota"]))

    _log("I3 · `main.c` — C1 (`sentinella_conti()`) + C3 (il no)")
    g = guardiano_al_minuto(testo)
    if g is None:
        _dub("⚠ registro non letto"); muti.append("I3")
    else:
        _inf("righe «guardiano:» %d · ritmo medio %s al minuto · ⭐ minuto "
             "migliore %s (⚠ la media affoga nei tratti a ZERO sessioni)"
             % (g["righe"], "?" if g["al_minuto"] is None
                else "%.1f" % g["al_minuto"],
                "?" if g.get("massimo_al_minuto") is None
                else "%.1f" % g["massimo_al_minuto"]))
        if g["perche"]:
            _inf("⚠ %s" % g["perche"])
        dillo("I3 · `sentinella_conti()` scrive ancora, una per ripasso",
              p_guardiano_scrive(g))

    _log("IL VERDETTO")
    for r in rossi:
        _ko(r)
    for m2 in muti:
        _dub("non ho misurato: %s" % m2)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ le tre cuciture reggono")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CERTIFICAZIONE — ogni predicato col suo guasto (`LEZIONI.md` §1.29)
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    buoni = malati = 0

    def caso(nome, vero, atteso):
        nonlocal buoni, malati
        if vero == atteso:
            _ok(nome); buoni += 1
        else:
            _ko("%s — atteso %r, avuto %r" % (nome, atteso, vero)); malati += 1

    _log("A · la forma della riga")
    caso("sano · la riga col nome si spezza",
         spezza("07:30:12.398 figlio  [provadec6] ciclo: 1108 fotogrammi")[0]["chi"],
         "provadec6")
    caso("⭐ la riga MUTA si spezza lo stesso, e il nome e' None",
         spezza("07:29:41.112 rcp     fotogramma 214 SPEDITO")[0]["chi"], None)
    caso("⛔ un `[…]` in mezzo al corpo NON e' un nome",
         spezza("07:29:41.112 rcp     v[16] contro attaccate[2]")[0]["chi"], None)
    caso("⛔ niente da leggere ⇒ None, non lista vuota", spezza(None), None)
    caso("⭐ letto e vuoto ⇒ lista vuota MISURATA", spezza("boh"), [])

    _log("B · I1 · l'identita' dopo il rimontaggio")
    pre = "07:00:00.000 figlio  [provadec1] il palco si monta\n"
    cambio = ("07:00:01.000 figlio  [provadec1] ⭐⭐ la STRADA DEI PIXEL e' "
              "cambiata in «MEMORIA»\n")
    dopo_ok = ("07:00:02.000 figlio  [provadec1] ciclo: 10 fotogrammi\n"
               "07:00:03.000 audio   [provadec1] blocchi\n")
    dopo_muto = ("07:00:02.000 figlio  ciclo: 10 fotogrammi\n"
                 "07:00:03.000 audio   blocchi\n")
    caso("sano · tutte col nome",
         p_identita_regge(identita_dopo_rimontaggio(pre + cambio + dopo_ok,
                                                    "provadec1")), True)
    caso("⛔ G1: il rimontaggio azzera l'identita' ⇒ ROSSO",
         p_identita_regge(identita_dopo_rimontaggio(pre + cambio + dopo_muto,
                                                    "provadec1")), False)
    caso("⛔ G2: una sola su due muta ⇒ ROSSO",
         p_identita_regge(identita_dopo_rimontaggio(
             pre + cambio + dopo_ok.splitlines()[0] + "\n"
             + dopo_muto.splitlines()[1] + "\n", "provadec1")), False)
    caso("⛔ G3: il nome e' di UN ALTRO utente ⇒ ROSSO",
         p_identita_regge(identita_dopo_rimontaggio(pre + cambio + dopo_ok,
                                                    "provadec5")), False)
    # ⛔⛔ IL GUASTO CHE HA TROVATO IL DIFETTO DEL BANCO — le righe del PADRE:
    #     area «figlio», niente parentesi, e il nome nel corpo.  ⚠ Il predicato
    #     di prima le contava come mute e dava rosso su codice giusto.
    padre = "07:00:02.000 figlio  fotogramma da «provadec1»: codec 3, 99 byte\n"
    caso("⭐ G3-bis: la riga del PADRE nomina nel corpo ⇒ NON e' anonima",
         p_identita_regge(identita_dopo_rimontaggio(pre + cambio + dopo_ok
                                                    + padre, "provadec1")), True)
    caso("⭐ G3-ter: ...e la parentesi resta sotto il 100 %, e si dice",
         round(identita_dopo_rimontaggio(pre + cambio + dopo_ok + padre,
                                         "provadec1")["quota"], 3), 0.667)
    caso("⚠ G4: nessun rimontaggio ⇒ non giudico",
         p_identita_regge(identita_dopo_rimontaggio(pre + dopo_ok,
                                                    "provadec1")), None)
    caso("⚠ G5: rimontaggio ma nessuna riga dopo ⇒ non giudico",
         p_identita_regge(identita_dopo_rimontaggio(pre + cambio, "provadec1")),
         None)
    caso("⚠ G6: registro non letto ⇒ non giudico",
         p_identita_regge(identita_dopo_rimontaggio(None, "provadec1")), None)
    caso("⛔ G7: «video» NON conta come area del figlio (e' anche del padre)",
         identita_dopo_rimontaggio(
             pre + cambio + "07:00:02.000 video   fotogramma 3\n",
             "provadec1")["dopo"], 0)

    _log("C · I2 · lo sfratto e il nome")
    sf_muto = ("07:00:10.000 wt      linea-morta 10.0.0.1:5 causa=silenzio "
               "fermo_ms=0 giri_fermi=0 saltati=0 giudizio=fuori\n")
    sf_nome = ("07:00:10.000 wt      [provaf1] linea-morta 10.0.0.1:5 "
               "causa=silenzio fermo_ms=0 giri_fermi=0 saltati=0 giudizio=fuori\n")
    caso("⛔ G8: la riga dello sfratto e' MUTA ⇒ ROSSO",
         p_sfratto_col_nome(sfratti(sf_muto)), False)
    caso("⭐ col nome ⇒ verde", p_sfratto_col_nome(sfratti(sf_nome)), True)
    caso("⛔ G9: una su due muta ⇒ ROSSO",
         p_sfratto_col_nome(sfratti(sf_nome + sf_muto)), False)
    caso("⚠ G10: nessuno sfratto ⇒ non giudico (nessuna sollecitazione)",
         p_sfratto_col_nome(sfratti("niente")), None)
    caso("⚠ G11: registro non letto ⇒ non giudico",
         p_sfratto_col_nome(sfratti(None)), None)
    caso("sano · i campi si leggono",
         sfratti(sf_nome)[0]["fermo_ms"], 0)
    caso("⛔ G12: il campo non c'e' ⇒ None, non zero",
         sfratti("07:00:10.000 wt      linea-morta 10.0.0.1:5 causa=x "
                 "giudizio=y\n")[0]["fermo_ms"], None)

    _log("C-bis · `nome_per_area` — la misura che spiega I2")
    misto = ("07:00:00.000 rcp     [provaf1] fotogramma 1 SPEDITO\n"
             "07:00:00.001 rcp     [provaf2] fotogramma 2 SPEDITO\n"
             "07:00:00.002 wt      rete-quic 10.0.0.1:5 persi=0\n")
    caso("sano · rcp al 100 %", nome_per_area(misto)["rcp"]["quota"], 1.0)
    caso("⛔ G12-bis: wt allo 0 %", nome_per_area(misto)["wt"]["quota"], 0.0)
    caso("⛔ registro non letto ⇒ None, non {}", nome_per_area(None), None)

    _log("D · I2-ter · `fermo_ms` riparte o no")
    a = sf_nome.replace("fermo_ms=0", "fermo_ms=12000")
    b = sf_nome.replace("fermo_ms=0", "fermo_ms=24000")
    c = sf_nome.replace("fermo_ms=0", "fermo_ms=3000")
    caso("⛔ G13: cresce sempre ⇒ e' il contatore GLOBALE", fermo_riparte(sfratti(a + b)),
         False)
    caso("⭐ G14: scende ⇒ e' per sessione", fermo_riparte(sfratti(b + c)), True)
    caso("⚠ G15: un solo sfratto ⇒ non giudico", fermo_riparte(sfratti(a)), None)
    caso("⚠ G15-bis: tutti a ZERO ⇒ non giudico (la prova non ha morso)",
         fermo_riparte(sfratti(sf_nome * 3)), None)
    caso("⚠ G16: due sfratti ma senza il campo ⇒ non giudico",
         fermo_riparte(sfratti("07:00:10.000 wt      [x] linea-morta p causa=c "
                               "giudizio=g\n" * 2)), None)

    _log("E · I3 · il ritmo del guardiano")
    def gr(ora, n):
        return ("%s sessione [x] guardiano: chiamate=%d peggiore_ms=6 "
                "giri_fermi=0 giro_peggiore_ms=0\n" % (ora, n))
    caso("sano · 30 al minuto ⇒ verde",
         p_guardiano_scrive(guardiano_al_minuto(
             gr("07:00:00.000", 29) + gr("07:01:00.000", 59)
             + gr("07:02:00.000", 89))), True)
    caso("⛔ G17: il contatore non si muove ⇒ ROSSO",
         p_guardiano_scrive(guardiano_al_minuto(
             gr("07:00:00.000", 29) + gr("07:01:00.000", 29))), False)
    caso("⛔ G18: 7 al minuto (il ripasso non gira) ⇒ ROSSO",
         p_guardiano_scrive(guardiano_al_minuto(
             gr("07:00:00.000", 0) + gr("07:01:00.000", 7))), False)
    caso("⛔ G19: 120 al minuto ⇒ ROSSO (non e' una per ripasso)",
         p_guardiano_scrive(guardiano_al_minuto(
             gr("07:00:00.000", 0) + gr("07:01:00.000", 120))), False)
    caso("⚠ G20: una riga sola ⇒ non giudico (un cumulativo non e' un ritmo)",
         p_guardiano_scrive(guardiano_al_minuto(gr("07:00:00.000", 29))), None)
    caso("⚠ G21: nessuna riga ⇒ non giudico",
         p_guardiano_scrive(guardiano_al_minuto("niente")), None)
    caso("⚠ G22: il contatore torna indietro (server ripartito) ⇒ non giudico",
         p_guardiano_scrive(guardiano_al_minuto(
             gr("07:00:00.000", 90) + gr("07:01:00.000", 29))), None)
    caso("⚠ G23: registro non letto ⇒ non giudico",
         p_guardiano_scrive(guardiano_al_minuto(None)), None)
    # ⛔⛔ IL GUASTO CHE HA TROVATO IL DIFETTO DEL BANCO — un registro di
    #     campagna: un minuto buono a 30, e sei a zero perche' non c'era
    #     nessuno attaccato.  ⚠ La MEDIA dice 4,3 e darebbe rosso su codice
    #     sanissimo; il minuto migliore dice 30.
    lungo = (gr("07:00:00.000", 0) + gr("07:01:00.000", 30)
             + gr("07:02:00.000", 30) + gr("07:03:00.000", 30)
             + gr("07:04:00.000", 30) + gr("07:05:00.000", 30)
             + gr("07:06:00.000", 30) + gr("07:07:00.000", 30))
    caso("⛔ G24: la MEDIA su un registro di campagna dava rosso su codice giusto",
         round(guardiano_al_minuto(lungo)["al_minuto"], 1), 4.3)
    caso("⭐ G24-bis: il minuto migliore lo salva",
         p_guardiano_scrive(guardiano_al_minuto(lungo)), True)

    print()
    if malati:
        print("  \033[1;31m%d su %d\033[0m" % (buoni, buoni + malati))
    else:
        print("  \033[1m%d su %d\033[0m" % (buoni, buoni))
    return 0 if not malati else 1


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--da-registro", default=None,
                   help="il registro SULLA MACCHINA di prova")
    p.add_argument("--da-file", default=None, help="un registro gia' qui")
    p.add_argument("--utente", default="provadec1",
                   help="di chi devono essere le righe del figlio (I1)")
    a = p.parse_args()
    if a.certifica:
        return certifica()
    if a.da_file:
        with open(a.da_file, errors="replace") as f:
            testo = f.read()
    elif a.da_registro:
        testo = leggi(a.da_registro)
    else:
        _ko("⛔ serve --da-registro o --da-file")
        return 2
    if testo is None:
        _ko("⛔ non ho letto il registro: NON MISURO")
        return 3
    return riferisci(testo, a.utente)


if __name__ == "__main__":
    sys.exit(principale())
