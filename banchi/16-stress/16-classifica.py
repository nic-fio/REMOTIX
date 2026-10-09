#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-classifica — IL GIUDIZIO DI UN LIVELLO, CON LE SOGLIE DI §9 (fase 16)

    python3 16-classifica.py --livello-dir DIR/livello-NN [--fps-video 30]
                             [--finestra-s 120] [--registro banchi/16-stress/registro.jsonl]
                             [--campagna intel-4k-kde] [--livello N] [--secco]
    python3 16-classifica.py --certifica

⛔ Le soglie sono quelle di `fasi/16-stress-e-capacita.md` §9, APPROVATE
   dall'utente il 25 set 2026 e FERME: stanno nella tabella SOGLIE qui sotto,
   una riga per riga di §9, e nessun parametro le cambia.  Solo `f` (la
   frequenza del video scelto, --fps-video) e la finestra di controllo
   (--finestra-s, gli ultimi 2 minuti del livello) sono parametri.

Scrive in fondo al registro (sole aggiunte) UNA riga per il livello e UNA per
ogni sessione (§10), e stampa il giudizio leggibile.  --secco: non scrive.

CHE COSA LEGGE, nella cartella del livello
----------------------------------------------------------------------------
  livello.json        (facoltativo, lo scrive chi conduce la salita) i campi
                      di §10 che non si misurano: campagna, livello, desktop,
                      scheda, driver, misura, commit, binario, pagina, nucleo,
                      inizio, durata_s, fps_video, tetto_sessioni,
                      utenti:[{utente, profilo, browser, versione, nuovo}]
  risorse.jsonl       di 16-risorse.py (una riga al secondo)
  utente-NN/stato.jsonl   una riga ogni 5 s, scritta dall'attore:
      {"t": <epoch s>, "utente": 3, "profilo": "C", "browser": "firefox",
       "versione": "Firefox 140…", "inquilino": "c16u03",
       "conti": {"consegnati","dipinti","salt","buchi","tard",
                 "ricevuti","suonati","BUCHI","mancati"}   ← CUMULATIVI, dalla
                 pagina (oppure "diario": la riga «audio: ricevuti … dipinti …
                 video X→Y … salt … buchi …» della pagina, e si legge da qui)
       "giro": {"visti": n, "campioni": [ms, …]}   ← `window.REMOTIX.giro`
                 della pagina (gli ultimi 200 ritardi comando → fotogramma);
                 oppure "giro_ms": [solo i campioni NUOVI dall'ultima riga]
       "input": [{"ok": true, "latenza_ms": 180, "azione": "cartella"}, …]
                 le azioni dell'intervallo, con l'effetto VERIFICATO (foto)
       "blocco_max_ms": 420   ← il blocco piu' lungo dell'immagine nei 5 s
                 con lavoro in corso (l'attore guarda la tela: da qui a 5 s di
                 grana non si vede sotto i 5 s)
       "lavoro": true,  "caduta": false,  "errori": ["…"]}
  utente-NN/nascita.json  {"accesso_ms": <epoch ms>, "primo_fotogramma_ms":
                      <epoch ms>, "esito": "ok"|"rifiuto"|"…"} (o "nascita_ms")
  controllo-corto.json    {"utente": N, "esiti": {"F-004": "PASS", …}}
  server.log          l'estratto del registro del server tagliato sul livello

LE MISURE, e da dove vengono (§7 → §9)
----------------------------------------------------------------------------
  ritardo   (26 set, dal coordinatore) p95, sulla finestra, dei p95 AL SECONDO
            delle righe «⭐ NOSTRO nel secondo (copia → byte fuori, §3.2)» del
            figlio (commit ebc9dcd: solo i fotogrammi di quel secondo, senza il
            «produttore» del compositore) + 9 ms (tetto costruttivo del tratto
            d'ingresso, il poll di 8 ms del figlio): il pezzo del PRODOTTO.  Il
            max al secondo si registra.  Le righe «TRATTO cattura → byte fuori»
            si REGISTRANO soltanto (il loro `max` e' del campione mobile di 512
            fotogrammi, e dentro c'e' il produttore).
            ⚠ Sulla strada wlroots la riga conta la «copia» due volte (~4 ms in
            piu'): NON corretto, dal lato prudente.  Senza righe ⇒ non misurato.
            Il GIRO della pagina (sotto) si registra come ESPERIENZA: `giro_eco`
            (solo battitura) e `giro` intero, che non classificano.
            Il GIRO e' la misura
            che il PRODOTTO fa (`pagina.html`, `GIRO.parte` sull'input,
            `GIRO.torna` quando arriva il fotogramma che porta quell'input nei
            28 byte di RCP §6.2; il server timbra l'id nel figlio, all'istante
            della cattura).  ⚠ Non comprende decodifica e disegno: e' un limite
            INFERIORE di quel che l'occhio vede (lo dice la pagina stessa).  Il
            server NON scrive nel registro un ritardo input→fotogramma (scrive
            «TRATTO cattura → byte fuori», che si registra come `tratto_server`
            ma non classifica).  La latenza dell'input VERIFICATO dall'attore
            (gesto → effetto nella foto) si registra (`input_latenza_p95`) ma
            non classifica: dentro c'e' la foto.  «Input perso» (un'azione con
            ok=false) ⇒ FAIL, come dice §9.  Profilo D (solo video, niente
            input): la voce non si applica, salvo campioni presenti.
            ⚠ La verifica «video_avanza» falsa (profilo D: il tempo del video
            nella scena non avanza) NON e' un input perso: va alla voce del
            video (DEGRADED significativo: fermo nella scena, causa da guardare).
  saltati   (Δconsegnati − Δdipinti) / Δconsegnati — `video X→Y` della pagina:
            tutto quel che il filo ha portato e non e' arrivato al vetro
            (saltati_coda, tardivi, scartati, persi nel decodificatore).  E' il
            verso SCOMODO: il solo `salt` (saltati_coda) si registra a parte.
  blocco    il massimo di `blocco_max_ms`.  Senza, dai contatori: 5 s con
            lavoro e nessun fotogramma dipinto ⇒ blocco >= 5 s (FAIL); la
            finestra intera senza fotogrammi ⇒ «immagine ferma» (FAIL); se non
            si vede niente sotto i 5 s ⇒ «non misurato» (la grana non basta).
  buchi     Δbuchi al minuto (chiavi richieste dalla pagina).
  video     (profilo D) Δdipinti / Δt contro f = --fps-video.
  audio     (profilo D) Δsuonati / (Δricevuti + Δmancati): quel che il server
            ha mandato e si e' sentito.  Nessun blocco mentre il video gira ⇒ 0 %.
  nascita   primo_fotogramma_ms − accesso_ms; «rifiuto» ⇒ FAIL.  Solo per gli
            utenti nati nel livello: `nuovo` in livello.json (la sua assenza e'
            «non misurato»); se l'elenco non c'e', solo se `accesso_ms` cade
            dentro il livello.  Le altre nascita.json sono di un gradino
            precedente (la cartella dell'attore si porta dietro): si REGISTRANO
            (`nascita_precedente`) e non classificano.
  corto     controllo-corto.json: un FAIL ⇒ FAIL; un BLOCKED ⇒ non misurato.
  caduta    `caduta` nello stato, contatori della pagina ripartiti da zero
            (pagina ricaricata o riattaccata), e nel registro del server per
            quell'inquilino: «la sessione e' finita», «il palco … se n'e'
            andato», «il figlio … se ne va», errore di protocollo — ⚠ in TUTTO il
            livello, non solo nella finestra: una caduta al minuto 3 e' una
            caduta.  Il riavvio del server (una riga «avvio REMOTIX», o il pid
            del padre che cambia in risorse.jsonl) ⇒ FAIL per tutte.
  memoria   (livello) PSS dei recinti `remotix` e `sessioni` su TUTTO il lavoro
            del livello, non sulla finestra (§6: l'ultimo gradino dura 30 min
            apposta per vedere le perdite): da inizio del lavoro + 60 s di
            assestamento (inizio del lavoro = fine − durata_lavoro_s di
            livello.json; se no inizio_t; se no la prima riga; e comunque dopo
            l'ultima nascita di un utente nuovo che si conosce) all'inizio del
            controllo corto (fine − controllo_min: la sessione 99 nasce li' e
            pesa sul recinto `sessioni`), se no alla fine.
            crescita = (media degli ultimi 30 s − media dei primi 30 s) / primi.
            «E continua» = la retta dei minimi quadrati sulla SECONDA META' del
            tratto sale (a) piu' del 2 % all'ora della media e (b) di piu' di un
            terzo della crescita totale lungo la meta' (pendenza × meta' durata).
            Una crescita lineare da' 1/2 ⇒ continua; uno scalino nella prima
            meta' e poi piatto ⇒ ferma.  Soglie §9 invariate: > 15 % e ferma ⇒
            DEGRADED significativo.
            Il recinto `browser` si registra e NON classifica (§9).

«NON MISURATO» — mai verde per assenza
----------------------------------------------------------------------------
Una voce che si applica e non ha dati vale DEGRADED col segno `non_misurato`,
e conta come DEGRADED SIGNIFICATIVO (non si sa di quanto): la salita si ferma
e si guarda l'impianto, invece di salire su un numero che non c'e'.

--sistema xrdp (fasi/20 §7.3, 9 ott 2026): le serie di 16-attore-rdp.py.  Stesse soglie, e
            le voci si leggono cosi':
  ritardo   p95 dei `ritardi_ms` delle righe (impulso → primo disegno XDamage dopo, dal
            LATO DI CHI GUARDA: tasto, clic, tacca), sulla finestra; con meno di 5
            campioni nella finestra, su tutto il livello (detto nella nota).  ⚠ Non e'
            il «NOSTRO + 9 ms» di REMOTIX (lato server): si confronta col GIRO della
            pagina.  Profilo D senza impulsi: la voce non si applica.  «Input perso» ⇒
            FAIL come sempre.
  saltati, buchi, audio  ⛔ NON MISURATI PER COSTRUZIONE: xrdp non manda i fotogrammi
            che non puo', non ha contatori nella pagina, e l'audio viaggia senza essere
            suonato.  Non entrano nella classe (sono in `misure.non_misurati_per_costruzione`).
  caduta    dall'attore (xfreerdp uscito, la finestra sparita); il registro di xrdp
            non ha l'ora nella forma del nostro e non si legge per le cadute.
  registro  le righe vanno in registro-xrdp.jsonl, col campo `sistema`.

IL LIVELLO (§9): GREEN se tutte le sessioni (e le voci di livello) sono
GREEN; DEGRADED se almeno una e' DEGRADED e nessuna FAIL; FAIL se almeno una e'
FAIL.  DEGRADED SIGNIFICATIVO = piu' di un quarto delle sessioni DEGLI ATTORI
DEGRADED (il controllo, utente 99, non conta; k·4 > n, esatto), o una misura
oltre META' della fascia DEGRADED (colonna `meta` di SOGLIE).
⛔ ENTRATI: se gli attori presenti (cartelle utente-NN, e quelli dell'elenco
`utenti` di livello.json senza cartella contano come assenti) sono meno del
livello dichiarato (--livello, se no livello.json) ⇒ voce di livello
`entrati` FAIL «entrati K su N»: un gradino non raggiunto non e' superato.
"""
import argparse
import datetime as _dt
import glob
import json
import math
import os
import re
import shutil
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
FPS_VIDEO_SCELTO = 30          # il video del profilo D (dal coordinatore, 26 set 2026)
REGISTRO = os.path.join(QUI, "registro.jsonl")
ORDINE = {"GREEN": 0, "DEGRADED": 1, "FAIL": 2}

# ⛔ §9, FERME.  (verso, verde, degradato, meta', unita').
#   verso "su": il valore buono e' basso (GREEN se <= verde; DEGRADED se <= degradato)
#   verso "giu": il valore buono e' alto (GREEN se >= verde; DEGRADED se >= degradato)
#   Le fasce del video sono in frazioni di f.
SOGLIE = {
    "ritardo_p95_ms":  ("su", 50.0, 150.0, 100.0, "ms"),
    "saltati_pct":     ("su", 2.0, 10.0, 6.0, "%"),
    "blocco_max_s":    ("su", 1.0, 3.0, 2.0, "s"),
    "buchi_al_min":    ("su", 0.0, 1.0, 0.5, "/min"),
    "video_frazione_f": ("giu", 0.8, 0.4, 0.6, "·f"),
    "audio_udibile_pct": ("giu", 99.0, 95.0, 97.0, "%"),
    "nascita_s":       ("su", 5.0, 15.0, 10.0, "s"),
    "memoria_crescita_pct": ("su", 5.0, 15.0, 10.0, "%"),
}
NOMI_VOCI = {
    "ritardo_p95_ms": "ritardo input → fotogramma (p95)",
    "saltati_pct": "fotogrammi saltati",
    "blocco_max_s": "blocco piu' lungo dell'immagine",
    "buchi_al_min": "buchi nella catena del video",
    "video_frazione_f": "video: dipinti al secondo",
    "audio_udibile_pct": "audio udibile",
    "nascita_s": "nascita (accesso → primo fotogramma)",
    "controllo_corto": "controllo funzionale corto",
    "caduta": "caduta, riavvio, errore che stacca",
    "memoria_crescita_pct": "crescita della memoria",
}

# le righe del registro del server che dicono «questa sessione e' caduta»
CADUTE = [
    (re.compile(r"\[(c[0-9a-z]+)\].*la sessione e' finita"), "la sessione e' finita (§4.2)"),
    (re.compile(r"il palco di «(c[0-9a-z]+)».*se n'e' andato"), "il palco se n'e' andato"),
    (re.compile(r"il figlio di «(c[0-9a-z]+)».*se ne va"), "il figlio se ne va"),
    (re.compile(r"\[(c[0-9a-z]+)\].*(?:ERRORE_PROTOCOLLO|errore di protocollo)", re.I),
     "errore di protocollo"),
    (re.compile(r"\[(c[0-9a-z]+)\].*SFRATTO per silenzio"), "sfratto per silenzio (§5.3)"),
]
RIAVVIO = re.compile(r"^\d\d:\d\d:\d\d(?:\.\d+)?\s+avvio\s+REMOTIX\b")
# ⚠ non «rifiut» e basta: `[M]` 25 set il figlio scrive «FIFO NON OTTENUTO … rifiut…» a
#   ogni nascita, e non e' un rifiuto dell'accesso.  Sono le tre porte di rcp.c/webtransport.c.
RIFIUTO = re.compile(r"(?:\[(c[0-9a-z]+)\]|«(c[0-9a-z]+)»).*(?:posto NEGATO|attacco NEGATO|"
                     r"sessione WebTransport RIFIUTATA)")
NOSTRO = re.compile(r"\[(c[0-9a-z]+)\] ⭐ NOSTRO nel secondo \([^)]*\): p95 ([\d.]+) ms · max ([\d.]+) · "
                    r"mediana ([\d.]+) · (\d+) fotogrammi")
PRODUTTORE = re.compile(r"produttore ([\d.]+) \(max ([\d.]+)\)")
RETE = re.compile(r"\[(c[0-9a-z]+)\] rete-quic (\S+) (.*)$")
TRATTO = re.compile(r"\[(c[0-9a-z]+)\] ⭐ TRATTO cattura → byte fuori: mediana ([\d.]+) ms \(max ([\d.]+)\)")


# ─────────────────────────────── giudizio di una voce ──────────────────────
def giudica(voce, valore, f=None):
    """→ (classe, significativo).  `valore` None non arriva qui."""
    verso, g, d, meta, _ = SOGLIE[voce]
    if voce == "video_frazione_f":
        valore = valore                        # gia' in frazioni di f
    if verso == "su":
        if valore <= g:
            return "GREEN", False
        if valore <= d:
            return "DEGRADED", valore > meta
        return "FAIL", True
    if valore >= g:
        return "GREEN", False
    if valore >= d:
        return "DEGRADED", valore < meta
    return "FAIL", True


def voce_misurata(voce, valore, nota="", extra=None):
    c, s = giudica(voce, valore)
    v = {"valore": _tondo(valore), "classe": c, "significativo": s, "nota": nota}
    v.update(extra or {})
    return v


def non_misurato(perche):
    return {"valore": None, "classe": "DEGRADED", "significativo": True,
            "non_misurato": True, "nota": "NON MISURATO: " + perche}


def fallita(valore, perche):
    return {"valore": valore, "classe": "FAIL", "significativo": True, "nota": perche}


def verde(valore, nota):
    return {"valore": valore, "classe": "GREEN", "significativo": False, "nota": nota}


def _tondo(x):
    return round(x, 3) if isinstance(x, float) else x


def p95(v):
    if not v:
        return None
    a = sorted(v)
    return a[max(0, math.ceil(0.95 * len(a)) - 1)]


# ─────────────────────────────── lettura ───────────────────────────────────
def jsonl(p):
    out = []
    if not os.path.exists(p):
        return out
    for x in open(p, encoding="utf-8", errors="replace"):
        x = x.strip()
        if x:
            try:
                out.append(json.loads(x))
            except ValueError:
                pass
    return out


def jfile(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


DIARIO = {
    "ricevuti": r"audio: ricevuti (\d+)", "suonati": r"\bsuonati (\d+)",
    "BUCHI": r"\bBUCHI (\d+)", "mancati": r"\bmancati (\d+)", "dipinti": r"\bdipinti (\d+)",
    "salt": r"\bsalt (\d+)", "buchi": r"\bbuchi (\d+)", "tard": r"\btard (\d+)",
}


def conti_di(riga):
    c = dict(riga.get("conti") or {})
    d = riga.get("diario")
    if d:
        for k, rx in DIARIO.items():
            if k not in c:
                m = re.search(rx, d)
                if m:
                    c[k] = int(m.group(1))
        m = re.search(r"\bvideo (\d+)→(\d+)", d)
        if m and "consegnati" not in c:
            c["consegnati"] = int(m.group(1))
            c.setdefault("dipinti", int(m.group(2)))
    return c


def campioni_giro(fin, chiave, chiave_lista):
    """I campioni NUOVI nella finestra: `chiave` = {visti, campioni} (gli ultimi
    200 della pagina: i nuovi sono gli ultimi `visti − visti_prima`), oppure
    `chiave_lista` = [solo i campioni nuovi dall'ultima riga]."""
    camp, pv = [], None
    for r in fin:
        g = r.get(chiave)
        if isinstance(g, dict) and g.get("campioni") is not None:
            vi = g.get("visti", 0)
            if pv is not None and r is not fin[0]:
                nuovi = max(0, vi - pv)
                camp += list(g["campioni"])[-nuovi:] if nuovi else []
            pv = vi
        elif isinstance(g, list) and r is not fin[0]:
            camp += list(g)
        elif r.get(chiave_lista) is not None and r is not fin[0]:
            camp += list(r[chiave_lista])
    return camp


def delta(righe, chiave):
    """Crescita di un contatore cumulativo lungo le righe; i ripartiti da zero
    si sommano per pezzi e si CONTANO (ripartenze)."""
    tot, ripartenze, prima, visto = 0, 0, None, False
    for r in righe:
        v = r["_c"].get(chiave)
        if v is None:
            continue
        visto = True
        if prima is not None:
            if v >= prima:
                tot += v - prima
            else:
                ripartenze += 1
                tot += v
        prima = v
    return (tot if visto else None), ripartenze


# ─────────────────────────────── una sessione ──────────────────────────────
NON_MISURATI_XRDP = ("saltati_pct", "buchi_al_min", "audio_udibile_pct")


def voce_ritardo_xrdp(dentro, righe, prof, misure, t_liv=None):
    """xrdp: il ritardo dal lato di chi guarda (impulso → primo disegno XDamage).
    → voce, o None se la voce non si applica (profilo D senza impulsi)."""
    camp = [x for r in dentro for x in (r.get("ritardi_ms") or [])]
    eco = [x for r in dentro for x in (r.get("ritardi_eco_ms") or [])]
    dove = "finestra"
    if len(camp) < 5:
        tutte = [r for r in righe if t_liv is None or t_liv[0] - 1 <= r.get("t", 0) <= t_liv[1] + 1]
        camp2 = [x for r in tutte for x in (r.get("ritardi_ms") or [])]
        if len(camp2) > len(camp):
            camp, dove = camp2, "tutto il livello (nella finestra %d campioni)" % len(camp)
            eco = [x for r in tutte for x in (r.get("ritardi_eco_ms") or [])]
    misure["xrdp_ritardi"] = {"campioni": len(camp), "p95_ms": _tondo(p95(camp)) if camp else None,
                              "mediana_ms": _tondo(sorted(camp)[len(camp) // 2]) if camp else None,
                              "eco_campioni": len(eco), "eco_p95_ms": _tondo(p95(eco)) if eco else None,
                              "su": dove}
    if not camp:
        if prof == "D":
            misure["ritardo_non_si_applica"] = "profilo D: nessun impulso"
            return None
        return non_misurato("nessun impulso chiuso da un disegno XDamage (righe `ritardi_ms` vuote)")
    v = p95(camp)
    misure["ritardo_p95_ms"] = _tondo(v)
    return voce_misurata("ritardo_p95_ms", v, "xrdp, LATO DI CHI GUARDA: p95 di %d attese impulso → primo "
                         "disegno XDamage (%s); a eco %s ms su %d" % (
                             len(camp), dove, _tondo(p95(eco)) if eco else "—", len(eco)))


def sessione(dir_u, w0, w1, f_video, meta_u, nuovo, corto, log_eventi, tratto, rete=None, tratti=None,
             desktop=None, t_liv=None, sistema=None):
    """`nuovo`: True/False dall'elenco di livello.json; None se l'elenco non
    c'e' (allora la nascita si giudica solo se `accesso_ms` cade in `t_liv`)."""
    righe = jsonl(os.path.join(dir_u, "stato.jsonl"))
    for r in righe:
        r["_c"] = conti_di(r)
    num = int(re.sub(r"\D", "", os.path.basename(dir_u)) or 0)
    prof = (meta_u or {}).get("profilo") or next((r.get("profilo") for r in righe if r.get("profilo")), None)
    info = {"utente": num, "profilo": prof,
            "browser": (meta_u or {}).get("browser") or next((r.get("browser") for r in righe if r.get("browser")), None),
            "versione": (meta_u or {}).get("versione") or next((r.get("versione") for r in righe if r.get("versione")), None),
            "inquilino": next((r.get("inquilino") for r in righe if r.get("inquilino")), (meta_u or {}).get("inquilino"))}
    voci, misure = {}, {}
    # la finestra: la riga di base e' l'ultima prima di w0 (i contatori sono cumulativi)
    prima = [r for r in righe if r.get("t", 0) <= w0]
    dentro = [r for r in righe if w0 < r.get("t", 0) <= w1]
    fin = ([prima[-1]] if prima else []) + dentro
    d_video = prof == "D"
    if len(fin) < 2:
        perche = "nessuna riga di stato nella finestra (l'attore non scrive, o e' morto)"
        for v in ("ritardo_p95_ms", "saltati_pct", "blocco_max_s", "buchi_al_min"):
            voci[v] = non_misurato(perche)
        if d_video:
            voci["video_frazione_f"] = non_misurato(perche)
            voci["audio_udibile_pct"] = non_misurato(perche)
        if sistema == "xrdp" and prof == "D":
            voci.pop("ritardo_p95_ms", None)
    else:
        dt = fin[-1]["t"] - fin[0]["t"]
        misure["finestra_s"] = round(dt, 1)
        cons, r1 = delta(fin, "consegnati")
        dip, r2 = delta(fin, "dipinti")
        ripartenze = max(r1, r2)
        # ── ritardo input → fotogramma: il pezzo del PRODOTTO ──
        # ⛔ 26 set 2026, dal coordinatore, su una diagnosi misurata (fase16/
        #   diagnosi-eco): giro_eco = nostro (ingresso ~5–9 ms + fotogramma in
        #   mano → pagina ~14 ms) + NON nostro (l'app che disegna l'eco, il
        #   compositore).  §9 classifica «(prodotto, p95)», §7 «quello che il
        #   prodotto misura dal suo lato» ⇒ CLASSIFICA: p95 dei `max` delle righe
        #   TRATTO del figlio nella finestra + 9 ms (il tetto costruttivo del
        #   tratto d'ingresso).  giro_eco e giro intero si registrano come
        #   ESPERIENZA e non classificano.
        tutti = campioni_giro(fin, "giro", "giro_ms")
        eco = campioni_giro(fin, "giro_eco", "giro_eco_ms")
        misure["esperienza"] = {
            "giro_eco_p95_ms": _tondo(p95(eco)) if eco else None, "giro_eco_campioni": len(eco),
            "giro_tutti_p95_ms": _tondo(p95(tutti)) if tutti else None, "giro_tutti_campioni": len(tutti)}
        tutte_ver = [x for r in dentro for x in (r.get("input") or [])]
        # ⚠ «video_avanza» (profilo D) non e' un input: il video nella scena
        #   fermo va alla voce del video, non al ritardo
        vid_fermo = [x for x in tutte_ver if x.get("azione") == "video_avanza" and x.get("ok") is False]
        inp = [x for x in tutte_ver if x.get("azione") != "video_avanza"]
        persi = [x for x in inp if x.get("ok") is False]
        misure["video_non_avanza"] = len(vid_fermo)
        lat = [x["latenza_ms"] for x in inp if x.get("ok") and x.get("latenza_ms") is not None]
        misure["input_azioni"] = len(inp)
        misure["input_persi"] = len(persi)
        misure["input_latenza_p95_ms"] = _tondo(p95(lat)) if lat else None
        if sistema == "xrdp":
            vr = voce_ritardo_xrdp(dentro, righe, prof, misure, t_liv)
        else:
            vr = voce_ritardo(info["inquilino"], tratti, desktop, misure)
        rit = vr["valore"] if vr else None
        if persi:
            voci["ritardo_p95_ms"] = fallita(_tondo(rit), "input PERSO: %d azioni su %d senza effetto (%s)"
                                             % (len(persi), len(inp),
                                                ", ".join(str(x.get("azione")) for x in persi[:3])))
        elif vr:
            voci["ritardo_p95_ms"] = vr
        elif sistema == "xrdp":
            pass                               # profilo D senza impulsi: non si applica
        else:
            voci["ritardo_p95_ms"] = non_misurato("nessuna riga «NOSTRO nel secondo» del figlio per %s nella "
                                                  "finestra (binario prima di ebc9dcd? le righe TRATTO si "
                                                  "registrano e non classificano)"
                                                  % (info["inquilino"] or "l'inquilino ignoto"))
        # ── saltati ──
        if cons is None or dip is None:
            voci["saltati_pct"] = non_misurato("la pagina non ha dato `video X→Y`")
        elif cons == 0:
            voci["saltati_pct"] = non_misurato("nessun fotogramma consegnato nella finestra")
        else:
            v = max(0.0, 100.0 * (cons - dip) / cons)
            sa, _ = delta(fin, "salt")
            misure.update(consegnati=cons, dipinti=dip, salt=sa, saltati_pct=_tondo(v))
            voci["saltati_pct"] = voce_misurata("saltati_pct", v, "%d consegnati, %d dipinti (salt %s)"
                                                % (cons, dip, sa))
        # ── blocco ──
        # ⚠ `lavoro: false` (per D: prima che il video parta) NON conta, ne' qui
        #   ne' per i dipinti al secondo: si guardano solo gli intervalli di lavoro.
        bm = [r["blocco_max_ms"] for r in dentro
              if r.get("blocco_max_ms") is not None and r.get("lavoro", True) is not False]
        fermi, dip_lav, dt_lav = 0, 0, 0.0
        for a, b in zip(fin, fin[1:]):
            da, db = a["_c"].get("dipinti"), b["_c"].get("dipinti")
            lav = b.get("lavoro", True) is not False
            if da is not None and db is not None and lav:
                dip_lav += max(0, db - da) if db >= da else db
                dt_lav += b["t"] - a["t"]
                if db == da:
                    fermi += 1
        misure["lavoro_s"] = round(dt_lav, 1)
        if dip_lav == 0 and dt_lav > 0 and dip is not None:
            voci["blocco_max_s"] = fallita(round(dt_lav, 1), "IMMAGINE FERMA: nessun fotogramma dipinto "
                                           "in %.0f s di lavoro" % dt_lav)
        elif bm:
            v = max(bm) / 1000.0
            misure["blocco_max_s"] = _tondo(v)
            voci["blocco_max_s"] = voce_misurata("blocco_max_s", v, "dall'attore (%d righe)" % len(bm))
            if fermi:
                voci["blocco_max_s"] = fallita(max(v, 5.0), "%d intervalli di 5 s senza fotogrammi "
                                               "con lavoro in corso" % fermi)
        elif fermi:
            voci["blocco_max_s"] = fallita(5.0, "%d intervalli di 5 s senza nessun fotogramma "
                                           "dipinto con lavoro in corso ⇒ blocco >= 5 s" % fermi)
        else:
            voci["blocco_max_s"] = non_misurato("manca `blocco_max_ms` e i contatori a 5 s non "
                                                "vedono sotto i 5 s")
        # ── buchi ──
        bu, _ = delta(fin, "buchi")
        if bu is None:
            voci["buchi_al_min"] = non_misurato("la pagina non ha dato `buchi`")
        else:
            v = bu / (dt / 60.0) if dt > 0 else 0.0
            misure["buchi"] = bu
            voci["buchi_al_min"] = voce_misurata("buchi_al_min", v, "%d buchi in %.0f s" % (bu, dt))
        # ── video e audio (profilo D) ──
        if d_video:
            if dip is None:
                voci["video_frazione_f"] = non_misurato("la pagina non ha dato `dipinti`")
            elif not f_video:
                voci["video_frazione_f"] = non_misurato("manca f, la frequenza del video (--fps-video)")
            elif dt_lav <= 0:
                voci["video_frazione_f"] = non_misurato("nessun intervallo di lavoro nella finestra "
                                                        "(il video non e' partito?)")
            else:
                fps = dip_lav / dt_lav
                misure["video_fps"] = _tondo(fps)
                voci["video_frazione_f"] = voce_misurata("video_frazione_f", fps / f_video,
                                                         "%.1f dipinti/s in %.0f s di video, f = %s"
                                                         % (fps, dt_lav, f_video))
            su, _ = delta(fin, "suonati")
            ri, _ = delta(fin, "ricevuti")
            ma, _ = delta(fin, "mancati")
            if su is None or ri is None:
                voci["audio_udibile_pct"] = non_misurato("la pagina non ha dato `suonati`/`ricevuti`")
            else:
                den = ri + (ma or 0)
                v = 100.0 * su / den if den else 0.0
                misure["audio_udibile_pct"] = _tondo(v)
                voci["audio_udibile_pct"] = voce_misurata(
                    "audio_udibile_pct", min(v, 100.0),
                    "%d suonati su %d mandati (%d ricevuti + %d mancati)" % (su, den, ri, ma or 0)
                    if den else "NESSUN blocco audio nella finestra mentre il video gira")
            if vid_fermo:
                vv = voci.get("video_frazione_f")
                if not vv or vv["classe"] == "GREEN":
                    voci["video_frazione_f"] = {
                        "valore": (vv or {}).get("valore"), "classe": "DEGRADED", "significativo": True,
                        "nota": "il VIDEO NELLA SCENA non avanza in %d verifiche su %d (%s): fermo o in pausa, "
                                "causa da guardare%s" % (
                                    len(vid_fermo), sum(1 for x in tutte_ver if x.get("azione") == "video_avanza"),
                                    (vid_fermo[0].get("det") or "")[:80],
                                    (" · " + vv["nota"]) if vv else "")}
                else:
                    vv["nota"] += " · il video nella scena non avanza in %d verifiche" % len(vid_fermo)
        # ── caduta: lo stato ──
        cad = [r for r in righe if r.get("caduta")]
        if cad:
            voci["caduta"] = fallita(True, "l'attore dice CADUTA alle %s: %s" % (
                _ora(cad[0]["t"]), "; ".join(cad[0].get("errori") or [])[:200]))
        elif ripartenze:
            voci["caduta"] = fallita(True, "i contatori della pagina sono ripartiti da zero %d volte: "
                                     "pagina ricaricata o sessione riattaccata" % ripartenze)
    # il ritardo del prodotto non ha bisogno dell'attore: senza righe di stato
    #   lo si prende lo stesso dalle righe TRATTO del figlio
    if len(fin) < 2 and sistema != "xrdp":
        vr = voce_ritardo(info["inquilino"], tratti, desktop, misure)
        if vr:
            voci["ritardo_p95_ms"] = vr
    if sistema == "xrdp":
        tolte = [v for v in NON_MISURATI_XRDP if v in voci]
        for v in tolte:
            voci.pop(v)
        misure["non_misurati_per_costruzione"] = tolte
    # ── caduta: il registro del server (tutto il livello) ──
    inq = info["inquilino"]
    ev = [e for e in log_eventi if e["inquilino"] == inq or e["inquilino"] == "*"] if inq else \
        [e for e in log_eventi if e["inquilino"] == "*"]
    if ev and voci.get("caduta", {}).get("classe") != "FAIL":
        voci["caduta"] = fallita(True, "registro del server: " + "; ".join(
            "%s %s" % (e["ora"], e["cosa"]) for e in ev[:3]))
    elif "caduta" not in voci:
        voci["caduta"] = verde(False, "nessuna caduta, riavvio o errore che stacca"
                               + ("" if inq else " (⚠ inquilino ignoto: solo il riavvio e' guardato)"))
    # la rete (§7), dal registro del server: si REGISTRA, non classifica
    misure["rete"] = (rete or {}).get(inq) if inq else None
    if inq and tratto.get(inq):
        misure["tratto_server_ms"] = tratto[inq]
    # ── nascita ──
    na = jfile(os.path.join(dir_u, "nascita.json"))
    if na is not None and nuovo is not True:
        # ⛔ nata in questo livello?  Con l'elenco: solo se `nuovo`.  Senza:
        #   solo se l'accesso cade dentro il livello.
        acc = na.get("accesso_ms")
        dentro_liv = (nuovo is None and acc is not None and t_liv is not None
                      and t_liv[0] - 1 <= acc / 1000.0 <= t_liv[1])
        if not dentro_liv:
            misure["nascita_precedente"] = {
                "nascita_s": round(na["nascita_ms"] / 1000.0, 2) if na.get("nascita_ms") is not None else
                (round((na["primo_fotogramma_ms"] - acc) / 1000.0, 2)
                 if acc is not None and na.get("primo_fotogramma_ms") is not None else None),
                "esito": na.get("esito"),
                "nota": "nascita di un gradino precedente: si registra, non classifica"}
            na = None
    if na is not None:
        es = str(na.get("esito", "ok")).lower()
        ms = na.get("nascita_ms")
        if ms is None and na.get("accesso_ms") is not None and na.get("primo_fotogramma_ms") is not None:
            ms = na["primo_fotogramma_ms"] - na["accesso_ms"]
        if "rifiut" in es:
            voci["nascita_s"] = fallita(None, "RIFIUTO all'accesso")
        elif ms is None:
            voci["nascita_s"] = fallita(None, "nessun primo fotogramma (esito %s)" % es) if es != "ok" \
                else non_misurato("nascita.json senza tempi")
        else:
            misure["nascita_s"] = round(ms / 1000.0, 2)
            voci["nascita_s"] = voce_misurata("nascita_s", ms / 1000.0, "accesso → primo fotogramma")
            if es not in ("ok", "pass"):
                voci["nascita_s"] = fallita(misure["nascita_s"], "esito %s" % es)
    elif nuovo:
        voci["nascita_s"] = non_misurato("utente nato nel livello senza nascita.json")
    rif = [e for e in log_eventi if e.get("rifiuto") and e["inquilino"] == inq] if inq else []
    if rif:
        voci["nascita_s"] = fallita(None, "rifiuto nel registro del server: " + rif[0]["riga"][:160])
    # ── controllo corto ──
    if corto and int(corto.get("utente", -1)) == num:
        voci["controllo_corto"] = voce_corto(corto)
    return info, misure, voci


def voce_nascita_controllo(na):
    """`nascita` di controllo-corto.json: {pagina_s, ammissione_s, nascita_s
    (accesso → primo fotogramma dipinto), primo_non_degenere_s, rifiuto, esito,
    ragione}.  §9: <= 5 s GREEN, 5–15 DEGRADED, > 15 o rifiuto FAIL."""
    if not na:
        return non_misurato("controllo-corto.json senza `nascita`")
    if na.get("rifiuto"):
        return fallita(None, "RIFIUTO all'accesso: %s" % (na.get("ragione") or "")[:160])
    if na.get("nascita_s") is None:
        if str(na.get("esito", "")).upper() == "FAIL":
            return fallita(None, "la sessione del controllo non e' nata: %s" % (na.get("ragione") or "")[:160])
        return non_misurato("`nascita` senza nascita_s")
    v = voce_misurata("nascita_s", float(na["nascita_s"]), "accesso → primo fotogramma dipinto, a carico pieno"
                      + (" (non degenere a %s s)" % na["primo_non_degenere_s"]
                         if na.get("primo_non_degenere_s") is not None else ""))
    if str(na.get("esito", "PASS")).upper() == "FAIL":
        v = fallita(v["valore"], "il primo fotogramma: %s" % (na.get("ragione") or "")[:160])
    return v


def sessione_controllo(cart, corto, log_eventi):
    inq = corto.get("inquilino")
    info = {"utente": int(corto.get("utente", 99)), "profilo": "controllo", "browser": corto.get("browser"),
            "versione": corto.get("versione"), "inquilino": inq}
    na = corto.get("nascita") or {}
    misure = {"nascita_s": na.get("nascita_s"), "ammissione_s": na.get("ammissione_s"),
              "primo_non_degenere_s": na.get("primo_non_degenere_s"),
              "sessioni_durante": corto.get("sessioni_durante")}
    voci = {"nascita_s": voce_nascita_controllo(na), "controllo_corto": voce_corto(corto)}
    rif = [e for e in log_eventi if e.get("rifiuto") and inq and e["inquilino"] == inq]
    if rif:
        voci["nascita_s"] = fallita(None, "rifiuto nel registro del server: " + rif[0]["riga"][:160])
    return (os.path.join(cart, "controllo-corto"), info, misure, voci)


def voce_corto(corto):
    es = corto.get("esiti") or {}
    if isinstance(es, list):
        es = {x.get("funzione"): x.get("esito") for x in es}
    if not es:
        return non_misurato("controllo-corto.json senza esiti")
    f = [k for k, v in es.items() if v == "FAIL"]
    b = [k for k, v in es.items() if v not in ("PASS", "FAIL")]
    if f:
        return fallita(es, "FAIL: " + ", ".join(f))
    if b:
        r = non_misurato("non guardate: " + ", ".join(b))
        r["valore"] = es
        return r
    return verde(es, "tutto PASS (%s)" % ", ".join(sorted(es)))


def _ora(t):
    return _dt.datetime.fromtimestamp(t).strftime("%H:%M:%S")


def classe_di(voci):
    c = "GREEN"
    for v in voci.values():
        if ORDINE[v["classe"]] > ORDINE[c]:
            c = v["classe"]
    return c


def ragione_di(voci):
    brutte = sorted(((k, v) for k, v in voci.items() if v["classe"] != "GREEN"),
                    key=lambda kv: -ORDINE[kv[1]["classe"]])
    if not brutte:
        return "tutte le voci GREEN"
    return " · ".join("%s %s: %s%s" % (v["classe"], NOMI_VOCI.get(k, k),
                                        "" if v.get("valore") is None or isinstance(v["valore"], (dict, bool))
                                        else "%s — " % v["valore"], v.get("nota", ""))
                      for k, v in brutte)


# ─────────────────────────────── il registro del server ────────────────────
def epoca_log(ora, t_rif, fuso):
    """«HH:MM:SS.mmm» del registro (ora del server, `fuso` ore da UTC; la
    scatola e' in UTC) → epoca, col giorno piu' vicino a `t_rif`."""
    m = re.match(r"(\d\d):(\d\d):(\d\d(?:\.\d+)?)", ora)
    if not m or not t_rif:
        return None
    base = _dt.datetime.fromtimestamp(t_rif, _dt.timezone.utc) + _dt.timedelta(hours=fuso)
    t = base.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
    t = t.timestamp() - fuso * 3600 + float(m.group(3))
    for g in (-86400, 86400):
        if abs(t + g - t_rif) < abs(t - t_rif):
            t += g
    return t


def eventi_log(p, t_rif, fuso=0.0):
    """Le righe che contano, con l'ora.  ⚠ Quelle DOPO la fine del livello
    (`t_rif`) non contano: lo sgombero di fine livello chiude le sessioni, e
    «la sessione e' finita» li' e' il congedo, non una caduta."""
    ev, tratto = [], {}
    if not p or not os.path.exists(p):
        return ev, tratto, False
    for riga in open(p, encoding="utf-8", errors="replace"):
        riga = riga.rstrip("\n")
        ora = riga[:12]
        te = epoca_log(ora, t_rif, fuso)
        if te is not None and te > t_rif + 2:
            continue
        if RIAVVIO.search(riga):
            ev.append({"inquilino": "*", "ora": ora, "cosa": "RIAVVIO del server (avvio REMOTIX)", "riga": riga})
            continue
        for rx, cosa in CADUTE:
            m = rx.search(riga)
            if m:
                ev.append({"inquilino": m.group(1), "ora": ora, "cosa": cosa, "riga": riga})
                break
        m = RIFIUTO.search(riga)
        if m and "rifiuto" not in (e.get("cosa") for e in ev[-1:]):
            ev.append({"inquilino": m.group(1) or m.group(2), "ora": ora, "cosa": "rifiuto",
                       "rifiuto": True, "riga": riga})
        m = TRATTO.search(riga)
        if m:
            tratto[m.group(1)] = {"mediana": float(m.group(2)), "max": float(m.group(3)), "ora": ora}
    return ev, tratto, True


TETTO_INGRESSO_MS = 9.0   # il tratto d'ingresso: il poll di 8 ms del figlio (figlio.c:3794) + 1


def tratti_log(p, w0, w1, fuso=0.0):
    """Due serie del figlio nella finestra, per inquilino:
    `nostro`  «⭐ NOSTRO nel secondo (copia → byte fuori, §3.2): p95 X ms · max Y ·
              mediana Z · N fotogrammi» (commit ebc9dcd): SOLO i fotogrammi di
              quel secondo, SENZA il «produttore» del compositore ⇒ CLASSIFICA;
    `tratto`  «⭐ TRATTO cattura → byte fuori: mediana X (max Y) …»: ⚠ il `max`
              e' del CAMPIONE MOBILE di 512 fotogrammi (non del secondo) e dentro
              c'e' il produttore ⇒ si REGISTRA soltanto (serve a spiegare)."""
    out = {"nostro": {}, "tratto": {}}
    if not p or not os.path.exists(p):
        return out
    for riga in open(p, encoding="utf-8", errors="replace"):
        if "NOSTRO nel secondo" not in riga and "TRATTO cattura" not in riga:
            continue
        te = epoca_log(riga[:12], w1, fuso)
        if te is None or te <= w0 or te > w1 + 2:
            continue
        m = NOSTRO.search(riga)
        if m:
            out["nostro"].setdefault(m.group(1), []).append(
                (te, float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(5))))
            continue
        m = TRATTO.search(riga)
        if m:
            pr = PRODUTTORE.search(riga)
            out["tratto"].setdefault(m.group(1), []).append(
                (te, float(m.group(2)), float(m.group(3)), float(pr.group(1)) if pr else None))
    return out


def voce_ritardo(inq, tratti, desktop, misure):
    """La voce del ritardo del PRODOTTO e le misure registrate.  → voce o None."""
    tratti = tratti or {"nostro": {}, "tratto": {}}
    no = tratti["nostro"].get(inq) or [] if inq else []
    tr = tratti["tratto"].get(inq) or [] if inq else []
    if tr:
        pm = [x[3] for x in tr if x[3] is not None]
        misure["tratto"] = {"righe": len(tr), "mediana_p95_ms": _tondo(p95([x[1] for x in tr])),
                            "max_campione_p95_ms": _tondo(p95([x[2] for x in tr])),
                            "produttore_mediana_ms": _tondo(sorted(pm)[len(pm) // 2]) if pm else None}
    if not no:
        return None
    p95s = [x[1] for x in no]
    rit = p95(p95s) + TETTO_INGRESSO_MS
    misure["ritardo_p95_ms"] = _tondo(rit)
    misure["nostro"] = {"righe": len(no), "p95_dei_p95_ms": _tondo(p95(p95s)),
                        "max_al_secondo_max_ms": _tondo(max(x[2] for x in no)),
                        "max_al_secondo_p95_ms": _tondo(p95([x[2] for x in no])),
                        "mediana_ms": _tondo(sorted(x[3] for x in no)[len(no) // 2]),
                        "fotogrammi": sum(x[4] for x in no)}
    nota = ("p95 dei p95 al secondo di «NOSTRO» (copia → byte fuori, %d righe del figlio) %.1f ms + %.0f ms "
            "d'ingresso (tetto costruttivo: poll di 8 ms)" % (len(no), p95(p95s), TETTO_INGRESSO_MS))
    if (desktop or "").lower() in ("xfce", "lxqt"):
        nota += (" · ⚠ strada wlroots: la «copia» e' contata due volte (~4 ms in piu', cattura.c:2309 / "
                 "figlio.c:5191) — NON corretto, e' dal lato prudente")
    return voce_misurata("ritardo_p95_ms", rit, nota)


RETE_CUM = ("persi", "byte_persi", "spediti", "byte_spediti", "ricevuti", "scartati",
            "dgram_persi", "dgram_ok", "dgram_falsi")


def rete_log(p, w0, w1, fuso=0.0):
    """§7, la rete per sessione: le righe `rete-quic` del server (una al secondo per
    connessione, contatori CUMULATIVI della connessione) nella finestra ⇒ per
    inquilino i Δ (sommati sulle connessioni: un rientro apre una connessione
    nuova e i contatori ripartono), la perdita %, il ritmo, e srtt/pto.
    ⚠ QUIC non scrive un contatore «ritrasmissioni»: i pacchetti `persi` sono
    quelli che ngtcp2 ha dichiarato persi, e il loro contenuto si ritrasmette ⇒
    `persi`/`byte_persi` SONO la misura delle ritrasmissioni.  Si registra e non
    classifica."""
    if not p or not os.path.exists(p):
        return {}
    conn = {}                                  # (inq, indirizzo) → [prima, ultima, srtt[], pto[]]
    for riga in open(p, encoding="utf-8", errors="replace"):
        if "rete-quic" not in riga:
            continue
        m = RETE.search(riga.rstrip("\n"))
        if not m:
            continue
        te = epoca_log(riga[:12], w1, fuso)
        if te is None or te <= w0 or te > w1 + 2:
            continue
        kv = {}
        for k, v in re.findall(r"(\w+)=(-?\d+)", m.group(3)):
            kv[k] = int(v)
        c = conn.setdefault((m.group(1), m.group(2)), [kv, kv, [], [], te, te])
        c[1] = kv
        c[5] = te
        if "srtt_us" in kv:
            c[2].append(kv["srtt_us"] / 1000.0)
        if "pto_us" in kv:
            c[3].append(kv["pto_us"] / 1000.0)
    out = {}
    for (inq, _), (a, b, srtt, pto, t0, t1) in conn.items():
        r = out.setdefault(inq, {k: 0 for k in RETE_CUM})
        r.setdefault("connessioni", 0)
        r["connessioni"] += 1
        r.setdefault("_srtt", []).extend(srtt)
        r.setdefault("_pto", []).extend(pto)
        r["_s"] = r.get("_s", 0) + max(0.0, t1 - t0) + 1.0   # la prima riga copre gia' da_ms
        for k in RETE_CUM:
            # la prima riga della finestra vale come base, ma i suoi `_d` sono dentro
            base = a.get(k, 0) - a.get(k + "_d", 0) if (k + "_d") in a else a.get(k, 0)
            r[k] += max(0, b.get(k, 0) - base)
    for inq, r in out.items():
        sr, pt, dur = r.pop("_srtt"), r.pop("_pto"), r.pop("_s")
        r["perdita_pct"] = round(100.0 * r["persi"] / r["spediti"], 3) if r["spediti"] else None
        r["mbit_s"] = round(r["byte_spediti"] * 8 / 1e6 / dur, 2) if dur else None
        r["srtt_ms"] = {"mediana": round(sorted(sr)[len(sr) // 2], 2), "max": round(max(sr), 2)} if sr else None
        r["pto_ms_max"] = round(max(pt), 1) if pt else None
        r["secondi"] = round(dur)
    return out


def journal_err(cart, t0, t1, scatola=None):
    """Le righe a priorita' <= 3 (err) del journal della scatola nel livello — da
    quando c'e' `--journal` (26 set 2026) il prodotto ci manda gli EVENTI, con
    REMOTIX_INQUILINO.  Fonte: `journal-err.jsonl` nella cartella del livello
    (l'uscita di `journalctl -t remotix -p err -o json`), oppure, con --journal-scatola,
    lo si chiede alla scatola adesso (serve root).  Si REGISTRA, non classifica.
    ⚠ Il registro completo resta registro.log: e' la fonte del classificatore."""
    p = os.path.join(cart, "journal-err.jsonl")
    righe, fonte = None, None
    if os.path.exists(p):
        righe, fonte = open(p, encoding="utf-8", errors="replace").read().splitlines(), p
    elif scatola:
        import subprocess
        cmd = ["podman", "exec", "rete11-" + scatola, "journalctl", "-t", "remotix", "-p", "err",
               "--since", "@%d" % int(t0), "--until", "@%d" % int(t1 + 1), "-o", "json", "--no-pager"]
        try:
            o = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            righe, fonte = o.stdout.splitlines(), " ".join(cmd)
            with open(p, "w", encoding="utf-8") as f:      # l'evidenza resta nel livello
                f.write(o.stdout)
        except (OSError, subprocess.SubprocessError) as e:
            return {"righe": None, "nota": "journal non letto: %s" % e}
    if righe is None:
        return None
    per, esempi, n = {}, [], 0
    for x in righe:
        x = x.strip()
        if not x:
            continue
        try:
            j = json.loads(x)
            msg, inq, pr = j.get("MESSAGE"), j.get("REMOTIX_INQUILINO"), j.get("PRIORITY")
            if pr is not None and int(pr) > 3:
                continue
            if isinstance(msg, list):                       # journalctl: byte non UTF-8
                msg = bytes(msg).decode("utf-8", "replace")
        except ValueError:
            msg, inq = x, None                              # `-o cat`: una riga, niente campi
            m = re.search(r"\[(c[0-9a-z]+)\]", x)
            inq = m.group(1) if m else None
        n += 1
        if inq:
            per[inq] = per.get(inq, 0) + 1
        if len(esempi) < 5:
            esempi.append(str(msg)[:200])
    return {"righe": n, "per_inquilino": per, "esempi": esempi, "fonte": fonte}


# ─────────────────────────────── le risorse ────────────────────────────────
def risorse(p, w0, w1):
    righe = [r for r in jsonl(p) if r.get("tipo") == "campione"]
    tutte = righe
    fin = [r for r in righe if w0 < r.get("t", 0) <= w1]
    if not fin:
        return None, tutte

    def serie(f):
        out = []
        for r in fin:
            try:
                v = f(r)
            except (KeyError, TypeError):
                v = None
            if v is not None:
                out.append(v)
        return out

    def som(v):
        if not v:
            return None
        return {"media": round(sum(v) / len(v), 2), "p95": round(p95(v), 2), "max": round(max(v), 2)}
    s = {"campioni": len(fin),
         "cpu_macchina_pct": som(serie(lambda r: r["macchina"]["cpu_pct"])),
         "carico_1m": som(serie(lambda r: r["macchina"]["carico"][0])),
         "mem_usata_mb": som(serie(lambda r: r["macchina"]["mem_usata_mb"])),
         "mem_totale_mb": fin[-1]["macchina"].get("mem_totale_mb"),
         "thread": som(serie(lambda r: r["macchina"]["thread"])),
         "misuratore_cpu_s": som(serie(lambda r: r["misuratore"]["cpu_s"])),
         "recinti": {}, "gpu": {}}
    for rc in ("remotix", "sessioni", "browser", "altro_scatola", "labwc_cliente"):
        s["recinti"][rc] = {
            "cpu_core": som(serie(lambda r: r["recinti"][rc]["cpu_core"])),
            "pss_mb": som(serie(lambda r: r["recinti"][rc]["pss_mb"])),
            "processi": som(serie(lambda r: r["recinti"][rc]["processi"])),
            "gpu": {c: som(serie(lambda r: r["recinti"][rc]["gpu"].get(c)))
                    for c in sorted({c for r in fin for c in r["recinti"][rc].get("gpu", {})})},
        }
    for pdev in sorted({p for r in fin for p in r.get("gpu", {})}):
        gg = {"scheda": fin[-1]["gpu"].get(pdev, {}).get("scheda"),
              "driver": fin[-1]["gpu"].get(pdev, {}).get("driver")}
        for c in sorted({c for r in fin for c in r["gpu"].get(pdev, {}).get("categorie", {})}):
            gg[c] = som(serie(lambda r: r["gpu"][pdev]["categorie"].get(c)))
        for k in ("freq_att_mhz", "freq_mhz", "temp_c", "potenza_w", "vram_usata_mb", "occupata_pct"):
            gg[k] = som(serie(lambda r: r["gpu"][pdev].get(k)))
        stroz = {}
        for r in fin:
            for x in r["gpu"].get(pdev, {}).get("strozzatura") or []:
                stroz[x] = stroz.get(x, 0) + 1
        gg["strozzatura_frazione"] = {k: round(v / len(fin), 2) for k, v in stroz.items()}
        s["gpu"][pdev] = gg
    s["avvisi"] = sorted({a for r in fin for a in r.get("avvisi") or []})[:10]
    return s, tutte


ASSESTAMENTO_S = 60.0     # dopo l'inizio del lavoro, prima di misurare la memoria
CONTINUA_PCT_ORA = 2.0    # «e continua»: pendenza della seconda meta' oltre il 2 %/ora della media...
CONTINUA_FRAZ = 1.0 / 3   # ...e crescita lungo la seconda meta' oltre 1/3 della totale


def pendenza(pts):
    """La pendenza dei minimi quadrati di [(t, v)], per secondo."""
    n = len(pts)
    mt = sum(t for t, _ in pts) / n
    mv = sum(v for _, v in pts) / n
    den = sum((t - mt) ** 2 for t, _ in pts)
    return sum((t - mt) * (v - mv) for t, v in pts) / den if den else 0.0


def voci_livello(ris_tutte, w0, w1, m0=None, m1=None):
    """`m0`–`m1`: il tratto della memoria (il lavoro del livello, vedi sopra);
    None ⇒ dalla prima riga di risorse all'ultima."""
    voci = {}
    fin = [r for r in ris_tutte if (m0 is None or r.get("t", 0) >= m0) and (m1 is None or r.get("t", 0) <= m1)]
    if not fin:
        return {"memoria_remotix": non_misurato("nessuna riga di risorse.jsonl nel lavoro del livello"),
                "memoria_sessioni": non_misurato("nessuna riga di risorse.jsonl nel lavoro del livello")}
    for rc in ("remotix", "sessioni"):
        pts = [(r["t"], r["recinti"][rc]["pss_mb"]) for r in fin
               if r.get("recinti", {}).get(rc, {}).get("processi")]
        if len(pts) < 20 or pts[-1][0] - pts[0][0] < 60:
            voci["memoria_" + rc] = non_misurato("serie della memoria di %s troppo corta (%d punti)"
                                                 % (rc, len(pts)))
            continue
        t0, t1 = pts[0][0], pts[-1][0]
        a = [v for t, v in pts if t <= t0 + 30]
        b = [v for t, v in pts if t >= t1 - 30]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        cresc = 100.0 * (mb - ma) / ma if ma > 0 else 0.0
        tm = (t0 + t1) / 2.0
        seconda = [(t, v) for t, v in pts if t >= tm]
        media = sum(v for _, v in pts) / len(pts)
        k = pendenza(seconda) if len(seconda) >= 10 else 0.0
        k_ora = 100.0 * k * 3600.0 / media if media > 0 else 0.0
        su_meta = k * (t1 - tm)
        continua = k_ora > CONTINUA_PCT_ORA and (mb - ma) > 0 and su_meta > CONTINUA_FRAZ * (mb - ma)
        nota = ("PSS %.0f → %.0f MB in %.0f s di lavoro (%s–%s); seconda meta' %+.1f %%/ora, %+.0f MB su "
                "%+.0f%s" % (ma, mb, t1 - t0, _ora(t0), _ora(t1), k_ora, su_meta, mb - ma,
                             " e CONTINUA a salire" if continua else ""))
        v = voce_misurata("memoria_crescita_pct", cresc, nota,
                          {"continua": continua, "pendenza_pct_ora": _tondo(k_ora), "tratto_s": round(t1 - t0)})
        if v["classe"] == "FAIL" and not continua:
            # §9: FAIL e' «> 15 % E continua»; oltre il 15 % ma ferma: si segnala
            v.update(classe="DEGRADED", significativo=True,
                     nota=nota + " — oltre il 15 % ma FERMA: si segnala (§9)")
        voci["memoria_" + rc] = v
    # il riavvio visto dalle risorse: il pid del padre cambia (in TUTTO il livello)
    pids = [r.get("remotix_pid") for r in ris_tutte if r.get("remotix_pid")]
    vuoti = [r for r in ris_tutte if r.get("recinti", {}).get("remotix", {}).get("processi") == 0]
    if len(set(pids)) > 1:
        voci["riavvio_server"] = fallita(sorted(set(pids)), "il pid del padre remotix e' CAMBIATO nel "
                                         "livello: %s" % " → ".join(str(p) for p in _senza_ripetuti(pids)))
    elif vuoti:
        voci["riavvio_server"] = fallita(len(vuoti), "recinto remotix VUOTO in %d campioni" % len(vuoti))
    else:
        voci["riavvio_server"] = verde(pids[0] if pids else None, "il padre remotix e' lo stesso per "
                                       "tutto il livello")
    return voci


def _senza_ripetuti(v):
    out = []
    for x in v:
        if not out or out[-1] != x:
            out.append(x)
    return out


# ─────────────────────────────── il livello ────────────────────────────────
def classifica(cart, fps_video=None, finestra_s=120.0, campagna=None, livello=None, fuso_log=0.0,
               journal_scatola=None, sistema=None):
    meta = jfile(os.path.join(cart, "livello.json")) or {}
    # f: --fps-video, poi livello.json, poi il video scelto nel piano (30 quadri/s)
    fps_video = fps_video or meta.get("fps_video") or FPS_VIDEO_SCELTO
    utenti_meta = {int(u["utente"]): u for u in meta.get("utenti") or [] if "utente" in u}
    dirs = sorted(glob.glob(os.path.join(cart, "utente-*")))
    # la fine del livello: l'ultima riga di qualunque serie
    ts = []
    for d in dirs:
        ts += [r.get("t", 0) for r in jsonl(os.path.join(d, "stato.jsonl"))]
    ris_p = os.path.join(cart, "risorse.jsonl")
    ts_r = [r.get("t", 0) for r in jsonl(ris_p) if r.get("tipo") == "campione"]
    w1 = meta.get("fine") or max(ts + ts_r or [0])
    w0 = w1 - finestra_s
    ris, ris_tutte = risorse(ris_p, w0, w1)
    ev, tratto, c_log = eventi_log(os.path.join(cart, "server.log"), w1, fuso_log)
    tratti = tratti_log(os.path.join(cart, "server.log"), w0, w1, fuso_log)
    rete = rete_log(os.path.join(cart, "server.log"), w0, w1, fuso_log)
    t_inizio = meta.get("inizio_t") or min(ts + ts_r or [w0])
    journal = journal_err(cart, t_inizio, w1, journal_scatola)
    corto = jfile(os.path.join(cart, "controllo-corto.json"))
    ha_elenco = bool(utenti_meta)
    sess = []
    for d in dirs:
        n = int(re.sub(r"\D", "", os.path.basename(d)) or 0)
        mu = utenti_meta.get(n)
        nuovo = bool(mu.get("nuovo")) if mu else (False if ha_elenco else None)
        info, misure, voci = sessione(d, w0, w1, fps_video, mu, nuovo,
                                      corto, ev, tratto, rete, tratti, meta.get("desktop"), (t_inizio, w1),
                                      sistema)
        if journal and info.get("inquilino"):
            misure["journal_err"] = journal["per_inquilino"].get(info["inquilino"], 0)
        sess.append((d, info, misure, voci))
    # il tratto della memoria: il LAVORO del livello (+ assestamento), fino al controllo corto
    if meta.get("durata_lavoro_s") is not None and meta.get("fine"):
        m0, da = meta["fine"] - meta["durata_lavoro_s"], "inizio del lavoro"
    elif meta.get("inizio_t"):
        m0, da = meta["inizio_t"], "inizio del livello"
    else:
        m0, da = min(ts_r or [t_inizio]), "prima riga di risorse"
    nate = []
    for d in dirs:
        n = int(re.sub(r"\D", "", os.path.basename(d)) or 0)
        if (utenti_meta.get(n) or {}).get("nuovo"):
            na = jfile(os.path.join(d, "nascita.json")) or {}
            if na.get("primo_fotogramma_ms") is not None and na["primo_fotogramma_ms"] / 1000.0 <= w1:
                nate.append(na["primo_fotogramma_ms"] / 1000.0)
    if nate and max(nate) > m0:
        m0, da = max(nate), "ultima nascita"
    m0 += ASSESTAMENTO_S
    m1 = w1
    if corto is not None and meta.get("controllo_min") and meta.get("fine"):
        m1 = min(w1, meta["fine"] - float(meta["controllo_min"]) * 60.0)
    # ⛔ [M] 26 set 00:56 (intel-4k-xfce livello-01): il controllo corto duro' 156 s e non
    #    120, la «fine − controllo_min» cadde 28 s DOPO la nascita della sessione u99 ⇒
    #    +25 MB di un inquilino nuovo letti come perdita (FAIL falso).  Il tratto della
    #    memoria finisce prima che il controllo compaia nelle risorse, qualunque sia la
    #    durata del controllo; e mai dopo l'inizio della finestra dichiarato dalla salita.
    if meta.get("inizio_finestra_t"):
        m1 = min(m1, float(meta["inizio_finestra_t"]))
    for r in ris_tutte:
        t_r = r.get("t")
        if t_r is None or t_r < m0:
            continue
        chi = set()
        for rec in (r.get("recinti") or {}).values():
            if isinstance(rec, dict):
                chi.update((rec.get("per_inquilino") or {}).keys())
        if any(str(c).endswith("u99") for c in chi):
            m1 = min(m1, t_r - 5.0)
            break
    lv = voci_livello(ris_tutte, w0, w1, m0, m1)
    for k in ("memoria_remotix", "memoria_sessioni"):
        if not lv[k].get("non_misurato"):
            lv[k]["nota"] += " · da: %s + %.0f s" % (da, ASSESTAMENTO_S)
    # ⛔ un gradino non raggiunto non e' un gradino superato
    n_dich = livello if livello is not None else meta.get("livello")
    presenti = {int(re.sub(r"\D", "", os.path.basename(d)) or 0) for d in dirs}
    senza_cart = sorted(set(utenti_meta) - presenti)
    if n_dich is not None:
        k_ent = len(presenti)
        if k_ent < int(n_dich):
            lv["entrati"] = fallita(k_ent, "entrati %d su %d%s" % (
                k_ent, int(n_dich), (" (nell'elenco senza cartella: %s)" % senza_cart) if senza_cart else ""))
        else:
            lv["entrati"] = verde(k_ent, "entrati %d su %d" % (k_ent, int(n_dich)))
    if not c_log:
        lv["registro_server"] = non_misurato("manca server.log: cadute ed errori del server non guardati")
    if corto is None:
        lv["controllo_corto"] = non_misurato("manca controllo-corto.json")
    elif not any("controllo_corto" in s[3] for s in sess):
        # ⭐ il controllo corto e' una SESSIONE NUOVA sua (16-controllo-corto.py,
        #   utente 99): si classifica come sessione a parte, profilo «controllo»,
        #   con la sua nascita a carico pieno (§9 «nascita di un utente nuovo»)
        sess.append(sessione_controllo(cart, corto, ev))
    if not sess:
        lv["sessioni"] = non_misurato("nessuna cartella utente-NN")
    classi = [classe_di(v) for _, _, _, v in sess]
    c_liv = classe_di(lv)
    for c in classi:
        if ORDINE[c] > ORDINE[c_liv]:
            c_liv = c
    # ⚠ il quarto si conta sugli ATTORI: il controllo (utente 99) non c'entra
    att = [classe_di(v) for _, i, _, v in sess if i.get("profilo") != "controllo"]
    n_att = len(att)
    n_deg = sum(1 for c in att if c == "DEGRADED")
    sig_voci = [(os.path.basename(d), k) for d, _, _, v in sess for k, x in v.items()
                if x["classe"] == "DEGRADED" and x.get("significativo")]
    sig_voci += [("livello", k) for k, x in lv.items() if x["classe"] == "DEGRADED" and x.get("significativo")]
    significativo = c_liv == "FAIL" or (c_liv == "DEGRADED" and (
        (n_att and n_deg * 4 > n_att) or bool(sig_voci)))
    return {"meta": meta, "w0": w0, "w1": w1, "fps_video": fps_video, "sessioni": sess, "journal": journal,
            "voci_livello": lv, "risorse": ris, "classe": c_liv, "significativo": significativo,
            "n_degradate": n_deg, "n_attori": n_att, "sig_voci": sig_voci, "campagna": campagna or meta.get("campagna"),
            "livello": livello if livello is not None else meta.get("livello", len(sess)),
            "cart": cart, "sistema": sistema or "remotix"}


BASE = ("desktop", "scheda", "driver", "misura", "commit", "binario", "pagina", "nucleo",
        "tetto_sessioni", "inizio", "durata_s")


def righe_registro(g):
    m = g["meta"]
    base = {"campagna": g["campagna"], "livello": g["livello"], "sistema": g.get("sistema", "remotix")}
    for k in BASE:
        base[k] = m.get(k)
    base["finestra"] = [_ora(g["w0"]), _ora(g["w1"])] if g["w1"] else None
    base["fps_video"] = g["fps_video"]
    out = []
    conti = {"GREEN": 0, "DEGRADED": 0, "FAIL": 0}
    for d, info, misure, voci in g["sessioni"]:
        c = classe_di(voci)
        conti[c] += 1
        r = dict(base, tipo="sessione", **info)
        r.update(misure=misure, voci=voci, classe=c, ragione=ragione_di(voci),
                 non_misurate=sorted(k for k, v in voci.items() if v.get("non_misurato")),
                 evidenze=[d])
        out.append(r)
    lvr = dict(base, tipo="livello", utenti=len(g["sessioni"]), sessioni=conti,
               journal_err=g.get("journal"),
               voci=g["voci_livello"], risorse=g["risorse"], classe=g["classe"],
               significativo=g["significativo"],
               ragione=_ragione_livello(g, conti), evidenze=[g["cart"]])
    return [lvr] + out


def _ragione_livello(g, conti):
    p = ["%d GREEN · %d DEGRADED · %d FAIL" % (conti["GREEN"], conti["DEGRADED"], conti["FAIL"])]
    brutte = [k for k, v in g["voci_livello"].items() if v["classe"] != "GREEN"]
    if brutte:
        p.append("livello: " + ragione_di({k: g["voci_livello"][k] for k in brutte}))
    if g["classe"] == "DEGRADED":
        if g["significativo"]:
            perche = []
            if g["n_attori"] and g["n_degradate"] * 4 > g["n_attori"]:
                perche.append("piu' di un quarto degli attori DEGRADED (%d su %d)"
                              % (g["n_degradate"], g["n_attori"]))
            if g["sig_voci"]:
                perche.append("oltre meta' fascia o non misurato: " + ", ".join(
                    "%s/%s" % x for x in g["sig_voci"][:6]))
            p.append("⛔ DEGRADED SIGNIFICATIVO (" + "; ".join(perche) + "): non si sale")
        else:
            p.append("DEGRADED non significativo")
    return " · ".join(p)


def stampa(g):
    print("LIVELLO %s · %s · finestra %s–%s · %s%s" % (
        g["livello"], g["campagna"] or "?", _ora(g["w0"]), _ora(g["w1"]), g["classe"],
        " (SIGNIFICATIVO)" if g["classe"] == "DEGRADED" and g["significativo"] else ""))
    for d, info, misure, voci in g["sessioni"]:
        print("  utente %-3s %-2s %-8s %-14s %s" % (info["utente"], info["profilo"] or "?",
                                                   info["browser"] or "?", info["inquilino"] or "?",
                                                   classe_di(voci)))
        for k, v in voci.items():
            val = v.get("valore")
            print("      %-8s %-40s %s%s" % (v["classe"], NOMI_VOCI.get(k, k),
                                            "" if val is None or isinstance(val, (dict, bool)) else "%s — " % val,
                                            v.get("nota", "")))
    for k, v in g["voci_livello"].items():
        print("  livello  %-8s %-30s %s" % (v["classe"], k, v.get("nota", "")))
    r = g["risorse"]
    if r:
        print("  risorse: cpu macchina %s %% (media) · mem usata %s MB · %s" % (
            (r["cpu_macchina_pct"] or {}).get("media"), (r["mem_usata_mb"] or {}).get("max"),
            " · ".join("%s %s" % (g2.get("scheda"), ", ".join("%s %s%%" % (c, (g2[c] or {}).get("media"))
                                                               for c in ("disegno", "video", "video_enhance")
                                                               if g2.get(c)))
                       for g2 in r["gpu"].values())))


# ─────────────────────────────── certifica ─────────────────────────────────
def certifica():
    esiti = []

    def guarda(nome, ok, dettaglio=""):
        esiti.append(ok)
        print("  %s %s%s" % ("PASS" if ok else "FAIL", nome, (" — " + dettaglio) if dettaglio else ""))

    print("16-classifica --certifica")
    print(" 1. ogni riga di §9 ai confini")
    casi = [
        ("ritardo_p95_ms", 50.0, "GREEN"), ("ritardo_p95_ms", 50.1, "DEGRADED"),
        ("ritardo_p95_ms", 150.0, "DEGRADED"), ("ritardo_p95_ms", 150.1, "FAIL"),
        ("saltati_pct", 2.0, "GREEN"), ("saltati_pct", 2.01, "DEGRADED"),
        ("saltati_pct", 10.0, "DEGRADED"), ("saltati_pct", 10.01, "FAIL"),
        ("blocco_max_s", 1.0, "GREEN"), ("blocco_max_s", 1.01, "DEGRADED"),
        ("blocco_max_s", 3.0, "DEGRADED"), ("blocco_max_s", 3.01, "FAIL"),
        ("buchi_al_min", 0.0, "GREEN"), ("buchi_al_min", 0.2, "DEGRADED"),
        ("buchi_al_min", 1.0, "DEGRADED"), ("buchi_al_min", 1.05, "FAIL"),
        ("video_frazione_f", 0.8, "GREEN"), ("video_frazione_f", 0.79, "DEGRADED"),
        ("video_frazione_f", 0.4, "DEGRADED"), ("video_frazione_f", 0.39, "FAIL"),
        ("audio_udibile_pct", 99.0, "GREEN"), ("audio_udibile_pct", 98.9, "DEGRADED"),
        ("audio_udibile_pct", 95.0, "DEGRADED"), ("audio_udibile_pct", 94.9, "FAIL"),
        ("nascita_s", 5.0, "GREEN"), ("nascita_s", 5.01, "DEGRADED"),
        ("nascita_s", 15.0, "DEGRADED"), ("nascita_s", 15.01, "FAIL"),
        ("memoria_crescita_pct", 5.0, "GREEN"), ("memoria_crescita_pct", 5.1, "DEGRADED"),
        ("memoria_crescita_pct", 15.0, "DEGRADED"), ("memoria_crescita_pct", 15.1, "FAIL"),
    ]
    sbagliati = [(v, x, a, giudica(v, x)[0]) for v, x, a in casi if giudica(v, x)[0] != a]
    guarda("%d casi ai confini" % len(casi), not sbagliati, "; ".join("%s %s: atteso %s, dato %s" % s
                                                                      for s in sbagliati))
    meta = [("ritardo_p95_ms", 100.0, False), ("ritardo_p95_ms", 100.5, True),
            ("video_frazione_f", 0.6, False), ("video_frazione_f", 0.59, True),
            ("audio_udibile_pct", 97.0, False), ("audio_udibile_pct", 96.9, True)]
    sb = [m for m in meta if giudica(m[0], m[1])[1] != m[2]]
    guarda("oltre meta' della fascia DEGRADED ⇒ significativo", not sb, str(sb))

    print(" 2. livelli sintetici, dalle cartelle")
    tmp = tempfile.mkdtemp(prefix="16-classifica-cert-")
    T0 = 1_790_000_000.0
    try:
        def livello(nome, utenti, log="", ris=True, mem=lambda t: 1000.0, corto=None, pid=lambda t: 111,
                    fps=30, tratto=None, elenco=True):
            c = os.path.join(tmp, nome)
            os.makedirs(c)
            lj = {"campagna": "cert", "livello": len(utenti), "desktop": "kde", "scheda": "intel",
                  "fps_video": fps,
                  "utenti": [{"utente": i + 1, "profilo": u["profilo"], "browser": "firefox",
                              "nuovo": u.get("nuovo", False)} for i, u in enumerate(utenti)]}
            if not elenco:
                del lj["utenti"]
            json.dump(lj, open(os.path.join(c, "livello.json"), "w"))
            for i, u in enumerate(utenti):
                d = os.path.join(c, "utente-%02d" % (i + 1))
                os.makedirs(d)
                with open(os.path.join(d, "stato.jsonl"), "w") as f:
                    for k in range(0, 601, 5):
                        f.write(json.dumps(u["riga"](T0 + k, k)) + "\n")
                if u.get("nascita") is not None:
                    json.dump(u["nascita"], open(os.path.join(d, "nascita.json"), "w"))
            with open(os.path.join(c, "server.log"), "w") as f:
                f.write(log)
                # le righe TRATTO del figlio, una al secondo per inquilino: max 30 ms
                #   salvo `tratto` = {inquilino: max, o None per NESSUNA riga}
                for i, u in enumerate(utenti):
                    inq = "c16u%02d" % (i + 1)
                    mx = (tratto or {}).get(inq, 30.0)
                    if mx is None:
                        continue
                    for k in range(470, 601):
                        o = _dt.datetime.fromtimestamp(T0 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
                        f.write("%s figlio  [%s] ⭐ TRATTO cattura → byte fuori: mediana %.2f ms (max %.2f) su "
                                "512 fotogrammi del campione, 9000 in tutto — produttore 24.00 (max 60.00)\n"
                                % (o, inq, 43.0, 6339.0))
                        if mx != "solo-tratto":
                            f.write("%s figlio  [%s] ⭐ NOSTRO nel secondo (copia → byte fuori, §3.2): p95 %.2f "
                                    "ms · max %.2f · mediana %.2f · 30 fotogrammi\n" % (o, inq, mx, mx * 1.5,
                                                                                         mx * 0.6))
            json.dump(corto or {"utente": 1, "esiti": {"F-003": "PASS", "F-004": "PASS",
                                                       "F-007": "PASS", "F-014": "PASS"}},
                      open(os.path.join(c, "controllo-corto.json"), "w"))
            if ris:
                with open(os.path.join(c, "risorse.jsonl"), "w") as f:
                    for k in range(0, 601):
                        t = T0 + k
                        f.write(json.dumps({"tipo": "campione", "t": t, "remotix_pid": pid(k),
                                            "macchina": {"cpu_pct": 30, "carico": [2, 2, 2],
                                                         "mem_usata_mb": 9000, "mem_totale_mb": 32000,
                                                         "thread": 900},
                                            "misuratore": {"cpu_s": 0.01},
                                            "recinti": {rc: {"cpu_core": 1, "pss_mb": mem(k) if rc != "browser"
                                                             else 500 + k, "processi": 5, "gpu": {}}
                                                        for rc in ("remotix", "sessioni", "browser",
                                                                   "altro_scatola", "labwc_cliente")},
                                            "gpu": {}}) + "\n")
            return c

        def sano(prof, inq, fps_pag=30.0, fermo_da=None, salt_pct=0.0, buchi_min=0.0, giro=20.0,
                 blocco=300, audio_pct=100.0, persi=False, caduta_a=None, diario=False, eco=True,
                 giro_lento=None, video_da=None, video_fermo=False):
            def riga(t, k):
                n = k * fps_pag
                if fermo_da is not None and k > fermo_da:
                    n = fermo_da * fps_pag
                cons = int(k * fps_pag / (1 - salt_pct / 100.0)) if salt_pct else int(n)
                r = {"t": t, "utente": int(inq[-2:]), "profilo": prof, "browser": "firefox",
                     "inquilino": inq, "lavoro": True, "blocco_max_ms": blocco,
                     "giro": {"visti": k, "campioni": [giro_lento or giro] * min(200, k)}}
                if eco:
                    r["giro_eco"] = {"visti": k, "campioni": [giro] * min(200, k)}
                if video_da is not None:
                    r["lavoro"] = k > video_da
                    n = max(0, k - video_da) * fps_pag
                conti = {"consegnati": cons, "dipinti": int(n), "salt": 0,
                         "buchi": int(k / 60.0 * buchi_min),
                         "ricevuti": k * 50, "suonati": int(k * 50 * audio_pct / 100.0), "mancati": 0}
                if diario:
                    r["diario"] = ("audio: ricevuti %(ricevuti)d suonati %(suonati)d BUCHI 0 vecchi 0 "
                                   "mancati %(mancati)d volte 0 | tasti 3 dipinti %(dipinti)d video "
                                   "%(consegnati)d→%(dipinti)d fuori 1 dentro 0 coda_dec 0 bmp 0 salt "
                                   "%(salt)d buchi %(buchi)d ord 0" % conti)
                else:
                    r["conti"] = conti
                if prof != "D":
                    r["input"] = [{"ok": not persi or k < 550, "latenza_ms": 150, "azione": "clic"}]
                elif video_fermo:
                    r["input"] = [{"ok": k < 550, "latenza_ms": None, "azione": "video_avanza",
                                   "det": "t 12.0→12.0"}]
                if caduta_a is not None and k >= caduta_a:
                    r["caduta"] = True
                    r["errori"] = ["la tela e' nera"]
                return r
            return {"profilo": prof, "riga": riga}

        quattro = [sano("A", "c16u01"), sano("B", "c16u02", diario=True), sano("C", "c16u03"),
                   sano("D", "c16u04")]
        g = classifica(livello("verde", quattro))
        guarda("livello sano ⇒ GREEN", g["classe"] == "GREEN", _ragione_livello(g, _conti(g)))

        u = list(quattro)
        u[1] = sano("B", "c16u02", fermo_da=400)
        g = classifica(livello("fermo", u))
        s2 = g["sessioni"][1][3]
        guarda("⛔ GUASTO: una sessione ferma ⇒ livello FAIL",
               g["classe"] == "FAIL" and s2["blocco_max_s"]["classe"] == "FAIL",
               s2["blocco_max_s"]["nota"])

        u = list(quattro)
        u[3] = sano("D", "c16u04", fps_pag=20.0)       # 20/30 = 0,67 f: DEGRADED, sotto meta' fascia
        g = classifica(livello("video-deg", u))
        guarda("video a 0,67·f ⇒ DEGRADED, non significativo (1 su 4)",
               g["classe"] == "DEGRADED" and not g["significativo"], g["sessioni"][3][3]["video_frazione_f"]["nota"])
        u[3] = sano("D", "c16u04", fps_pag=15.0)       # 0,5 f: oltre meta' fascia
        g = classifica(livello("video-sig", u))
        guarda("video a 0,5·f ⇒ DEGRADED SIGNIFICATIVO", g["classe"] == "DEGRADED" and g["significativo"])
        g = classifica(livello("due-deg", quattro, tratto={"c16u01": 60.0, "c16u02": 60.0}))
        guarda("2 sessioni su 4 DEGRADED (ritardo 60 ms) ⇒ significativo (> un quarto)",
               g["classe"] == "DEGRADED" and g["significativo"], _ragione_livello(g, _conti(g)))
        u = [sano("A", "c16u01", salt_pct=5.0), sano("B", "c16u02"), sano("C", "c16u03"),
             sano("D", "c16u04", audio_pct=96.0)]
        g = classifica(livello("salt-audio", u))
        s1, s4 = g["sessioni"][0][3], g["sessioni"][3][3]
        guarda("saltati 5 % ⇒ DEGRADED; audio 96 % ⇒ DEGRADED oltre meta' fascia",
               s1["saltati_pct"]["classe"] == "DEGRADED" and s4["audio_udibile_pct"]["classe"] == "DEGRADED"
               and s4["audio_udibile_pct"]["significativo"],
               "%s · %s" % (s1["saltati_pct"]["valore"], s4["audio_udibile_pct"]["valore"]))
        u = [sano("A", "c16u01", buchi_min=2.0), sano("B", "c16u02", persi=True), sano("C", "c16u03"),
             sano("D", "c16u04")]
        g = classifica(livello("buchi-persi", u))
        guarda("2 buchi al minuto ⇒ FAIL; input perso ⇒ FAIL",
               g["sessioni"][0][3]["buchi_al_min"]["classe"] == "FAIL"
               and g["sessioni"][1][3]["ritardo_p95_ms"]["classe"] == "FAIL")
        u = list(quattro)
        u[2] = sano("C", "c16u03", blocco=None)
        u[2]["nascita"] = None
        g = classifica(livello("non-misurato", u))
        s3 = g["sessioni"][2][3]
        guarda("⛔ misura MANCANTE ⇒ mai GREEN: «non misurato», significativo",
               s3["blocco_max_s"].get("non_misurato") and g["classe"] == "DEGRADED" and g["significativo"],
               s3["blocco_max_s"]["nota"])
        u = [dict(sano("A", "c16u01"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 4800}, nuovo=True),
             dict(sano("B", "c16u02"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 16000}, nuovo=True),
             dict(sano("C", "c16u03"), nascita={"esito": "rifiuto"}, nuovo=True),
             dict(sano("D", "c16u04"), nuovo=True)]
        g = classifica(livello("nascite", u))
        cl = [g["sessioni"][i][3].get("nascita_s", {}).get("classe") for i in range(4)]
        guarda("nascite 4,8 s / 16 s / rifiuto / assente ⇒ GREEN, FAIL, FAIL, non misurato",
               cl == ["GREEN", "FAIL", "FAIL", "DEGRADED"] and g["sessioni"][3][3]["nascita_s"].get("non_misurato"),
               str(cl))
        # ⛔ GUASTO (revisione 26 set): la nascita.json di un gradino precedente
        #   (la cartella dell'attore resta) veniva rigiudicata a ogni livello
        u = list(quattro)
        u[1] = dict(sano("B", "c16u02"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 7000})
        g = classifica(livello("nascita-vecchia", u))
        s2 = g["sessioni"][1]
        nsa = (T0 + 100) * 1000
        u2 = [dict(sano("A", "c16u01"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 7000}),
              dict(sano("B", "c16u02"), nascita={"accesso_ms": nsa, "primo_fotogramma_ms": nsa + 7000}),
              sano("C", "c16u03"), sano("D", "c16u04")]
        g2 = classifica(livello("nascita-senza-elenco", u2, elenco=False))
        guarda("⛔ GUASTO: nascita di un gradino precedente (non `nuovo`, o accesso fuori dal livello) ⇒ "
               "registrata, NON classifica; accesso dentro il livello ⇒ classifica",
               "nascita_s" not in s2[3] and s2[2].get("nascita_precedente", {}).get("nascita_s") == 7.0
               and g["classe"] == "GREEN"
               and "nascita_s" not in g2["sessioni"][0][3]
               and g2["sessioni"][1][3].get("nascita_s", {}).get("classe") == "DEGRADED",
               json.dumps(s2[2].get("nascita_precedente"), ensure_ascii=False))
        hh = _dt.datetime.fromtimestamp(T0 + 300, _dt.timezone.utc).strftime("%H:%M:%S.000")
        dopo = _dt.datetime.fromtimestamp(T0 + 900, _dt.timezone.utc).strftime("%H:%M:%S.000")
        log = ("%s rcp     [c16u03] ⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2, "
               "la sessione e' finita\n" % hh)
        log += ("%s rcp     [c16u01] ⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2, "
                "la sessione e' finita\n" % dopo)
        log += ("%s figlio  [c16u02] ⛔⛔ FIFO **NON** OTTENUTO: politica NORMALE, rifiutato\n" % hh)
        g = classifica(livello("caduta-log", quattro, log=log))
        guarda("registro: la sessione e' finita ⇒ FAIL; dopo la fine del livello e «rifiut» qualunque ⇒ no",
               [classe_di(s[3]) for s in g["sessioni"]] == ["GREEN", "GREEN", "FAIL", "GREEN"])
        # la rete e il journal: si registrano, non classificano
        rq = ""
        for k in range(0, 31):
            o = _dt.datetime.fromtimestamp(T0 + 540 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
            rq += ("%s wt      [c16u01] rete-quic [192.168.0.2]:4000 da_ms=1000 persi=%d persi_d=1 "
                   "byte_persi=%d byte_persi_d=1200 spediti=%d spediti_d=100 byte_spediti=%d "
                   "ricevuti=%d ricevuti_d=50 srtt_us=%d pto_us=20000 giudizio=--\n"
                   % (o, 10 + k, 12000 + 1200 * k, 1000 + 100 * k, 125000 * (10 + k), 500 + 50 * k,
                      1000 + 100 * k))
        cr = livello("rete", quattro, log=rq)
        with open(os.path.join(cr, "journal-err.jsonl"), "w") as f:
            f.write(json.dumps({"MESSAGE": "⛔ qualcosa", "PRIORITY": "3", "REMOTIX_INQUILINO": "c16u01"}) + "\n")
            f.write(json.dumps({"MESSAGE": "⚠ avviso", "PRIORITY": "4", "REMOTIX_INQUILINO": "c16u01"}) + "\n")
        g = classifica(cr)
        rt = g["sessioni"][0][2].get("rete") or {}
        guarda("rete per sessione dal registro: 31 righe ⇒ persi 31, spediti 3100, 1 % (non classifica)",
               rt.get("persi") == 31 and rt.get("spediti") == 3100 and rt.get("perdita_pct") == 1.0
               and g["classe"] == "GREEN" and g["sessioni"][1][2].get("rete") is None,
               json.dumps(rt))
        guarda("journal: 1 riga a priorita' <= 3 (la 4 no), per inquilino, non classifica",
               g["journal"]["righe"] == 1 and g["sessioni"][0][2].get("journal_err") == 1
               and g["classe"] == "GREEN", json.dumps(g["journal"], ensure_ascii=False)[:160])
        g = classifica(livello("riavvio-log", quattro, log="%s avvio   REMOTIX — fase 1\n" % hh))
        guarda("riavvio nel registro ⇒ tutte FAIL", all(classe_di(s[3]) == "FAIL" for s in g["sessioni"]))
        g = classifica(livello("rifiuto-log", quattro, log="%s rcp     [c16u04] ⛔ posto NEGATO a c16u04 da "
                                                           "x: il registro delle sessioni e' PIENO\n" % hh))
        guarda("posto NEGATO nel registro ⇒ nascita FAIL",
               g["sessioni"][3][3].get("nascita_s", {}).get("classe") == "FAIL")
        g = classifica(livello("riavvio-pid", quattro, pid=lambda k: 111 if k < 300 else 222))
        guarda("pid del padre cambiato in risorse ⇒ livello FAIL",
               g["classe"] == "FAIL" and g["voci_livello"]["riavvio_server"]["classe"] == "FAIL")
        u = list(quattro)
        u[0] = sano("A", "c16u01", caduta_a=590)
        g = classifica(livello("caduta-stato", u))
        guarda("l'attore dice caduta ⇒ FAIL", classe_di(g["sessioni"][0][3]) == "FAIL")
        g = classifica(livello("corto-fail", quattro, corto={"utente": 2, "esiti": {"F-003": "PASS",
                                                                                   "F-014": "FAIL"}}))
        guarda("controllo corto con un FAIL ⇒ la sua sessione FAIL",
               classe_di(g["sessioni"][1][3]) == "FAIL" and classe_di(g["sessioni"][0][3]) == "GREEN")
        cc = {"utente": 99, "inquilino": "c1604u99", "browser": "chrome",
              "esiti": {"F-003": "PASS", "F-004": "PASS", "F-007": "PASS", "F-014": "PASS"},
              "nascita": {"pagina_s": 0.8, "ammissione_s": 0.4, "nascita_s": 7.2,
                          "primo_non_degenere_s": 7.9, "esito": "PASS", "ragione": "ok"}}
        g = classifica(livello("corto-99", quattro, corto=cc))
        s99 = [x for x in g["sessioni"] if x[1]["utente"] == 99]
        v = s99[0][3]["nascita_s"] if s99 else {}
        guarda("controllo corto = sessione 99 «controllo»: nascita 7,2 s a carico pieno ⇒ DEGRADED",
               len(g["sessioni"]) == 5 and s99 and s99[0][1]["profilo"] == "controllo"
               and v.get("classe") == "DEGRADED" and g["classe"] == "DEGRADED"
               and "controllo_corto" not in g["voci_livello"], v.get("nota", ""))
        cc["nascita"] = {"ammissione_s": 1.0, "rifiuto": True, "esito": "FAIL", "ragione": "l'accesso: rifiutato"}
        g = classifica(livello("corto-rifiuto", quattro, corto=cc))
        guarda("controllo corto rifiutato ⇒ FAIL", g["classe"] == "FAIL")
        # ⛔ GUASTO (revisione 26 set): il quarto contava anche il controllo
        cc["nascita"] = {"nascita_s": 7.2, "esito": "PASS"}
        g = classifica(livello("quarto-attori", quattro, corto=cc, tratto={"c16u01": 60.0}))
        guarda("⛔ GUASTO: 1 attore su 4 DEGRADED + il controllo DEGRADED ⇒ NON significativo "
               "(il quarto e' degli attori, 1·4 > 4 e' falso)",
               g["classe"] == "DEGRADED" and not g["significativo"],
               _ragione_livello(g, _conti(g)))
        u = list(quattro)
        u[0] = sano("A", "c16u01", giro=200, giro_lento=900)
        g = classifica(livello("tratto-30", u))
        v30 = g["sessioni"][0][3]["ritardo_p95_ms"]
        es = g["sessioni"][0][2]["esperienza"]
        g2 = classifica(livello("tratto-60", u, tratto={"c16u01": 60.0}))
        v60 = g2["sessioni"][0][3]["ritardo_p95_ms"]
        guarda("ritardo del PRODOTTO: NOSTRO p95 30 ⇒ 39 ms GREEN, 60 ⇒ 69 ms DEGRADED (le righe TRATTO col "
               "max 6339 NON contano); giro_eco (200) e giro intero (900) solo ESPERIENZA",
               v30["classe"] == "GREEN" and abs(v30["valore"] - 39.0) < 1e-6
               and v60["classe"] == "DEGRADED" and abs(v60["valore"] - 69.0) < 1e-6
               and es["giro_eco_p95_ms"] == 200 and es["giro_tutti_p95_ms"] == 900, v30["nota"])
        g3 = classifica(livello("solo-tratto", u, tratto={"c16u01": "solo-tratto"}))
        v = g3["sessioni"][0][3]["ritardo_p95_ms"]
        guarda("⛔ GUASTO: solo righe TRATTO (niente NOSTRO) ⇒ non misurato, e il TRATTO registrato",
               v.get("non_misurato") and g3["classe"] == "DEGRADED"
               and g3["sessioni"][0][2]["tratto"]["produttore_mediana_ms"] == 24.0, v["nota"])
        u = list(quattro)
        u[3] = sano("D", "c16u04", video_da=540)       # il video parte a 540 s: 60 s di lavoro su 120
        g = classifica(livello("d-lavoro", u))
        s4 = g["sessioni"][3]
        guarda("profilo D: `lavoro: false` prima del video non conta (fps 30 su 60 s, niente blocco)",
               s4[3]["video_frazione_f"]["classe"] == "GREEN" and s4[3]["blocco_max_s"]["classe"] == "GREEN"
               and abs(s4[2]["video_fps"] - 30.0) < 0.6, s4[3]["video_frazione_f"]["nota"])
        g = classifica(livello("mem-perdita", quattro, mem=lambda k: 1000.0 * (1 + 0.004 * max(0, k - 480))))
        v = g["voci_livello"]["memoria_sessioni"]
        guarda("memoria +48 % e continua ⇒ FAIL", v["classe"] == "FAIL", v["nota"])
        g = classifica(livello("mem-scalino", quattro,
                               mem=lambda k: 1000.0 if k < 200 else 1200.0))
        v = g["voci_livello"]["memoria_sessioni"]
        guarda("memoria +20 % ma FERMA ⇒ DEGRADED significativo (non FAIL)",
               v["classe"] == "DEGRADED" and v["significativo"], v["nota"])
        # ⛔ GUASTO (revisione 26 set): una perdita lenta e costante (+20 % sul
        #   livello) nella finestra di 120 s fa +3 %: era verde
        g = classifica(livello("mem-lenta", quattro, mem=lambda k: 1000.0 * (1 + 0.20 * k / 600.0)))
        v = g["voci_livello"]["memoria_sessioni"]
        guarda("⛔ GUASTO: memoria +20 % lineare su tutto il livello ⇒ FAIL (crescita dall'inizio del lavoro, "
               "pendenza della seconda meta')", v["classe"] == "FAIL" and v["continua"], v["nota"])
        # ⛔ GUASTO (revisione 26 set): con meno attori del livello si giudicavano solo quelli presenti
        g = classifica(livello("pochi", quattro), livello=6)
        v = g["voci_livello"].get("entrati", {})
        guarda("⛔ GUASTO: livello 6 dichiarato con 4 attori ⇒ FAIL «entrati 4 su 6»",
               g["classe"] == "FAIL" and v.get("classe") == "FAIL" and v.get("valore") == 4, v.get("nota", ""))
        # ⛔ GUASTO (revisione 26 set): «video_avanza» falso contava come input PERSO
        u = list(quattro)
        u[3] = sano("D", "c16u04", video_fermo=True)
        g = classifica(livello("video-avanza", u))
        s4 = g["sessioni"][3][3]
        guarda("⛔ GUASTO: il video nella scena non avanza (profilo D) ⇒ voce del video DEGRADED "
               "significativo, NON «input perso» sul ritardo",
               s4["ritardo_p95_ms"]["classe"] == "GREEN" and s4["video_frazione_f"]["classe"] == "DEGRADED"
               and s4["video_frazione_f"]["significativo"], s4["video_frazione_f"]["nota"])
        g = classifica(livello("mem-browser", quattro, mem=lambda k: 1000.0))
        guarda("il recinto browser che cresce NON classifica", g["classe"] == "GREEN")
        g = classifica(livello("senza-risorse", quattro, ris=False))
        guarda("senza risorse.jsonl ⇒ memoria non misurata", g["voci_livello"]["memoria_remotix"].get("non_misurato")
               and g["classe"] == "DEGRADED")
        # il registro: una riga per livello e una per sessione, in fondo
        reg = os.path.join(tmp, "registro.jsonl")
        g = classifica(livello("registro", quattro))
        righe = righe_registro(g)
        with open(reg, "a") as f:
            for r in righe:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        rr = jsonl(reg)
        guarda("registro: 1 livello + 4 sessioni, coi campi di §10",
               len(rr) == 5 and rr[0]["tipo"] == "livello" and all(
                   k in rr[1] for k in ("campagna", "livello", "utente", "profilo", "browser", "desktop",
                                        "scheda", "misura", "commit", "classe", "ragione", "evidenze")))

        print(" 3. --sistema xrdp (fasi/20 §7.3)")

        def rdp(prof, inq, rit=30.0, persi=False):
            def riga(t, k):
                r = {"t": t, "utente": int(inq[-2:]), "profilo": prof, "browser": "freerdp",
                     "inquilino": inq, "sistema": "xrdp", "conti": {"dipinti": int(k * 30)},
                     "lavoro": True, "blocco_max_ms": int(rit) if prof != "D" else 40}
                if prof != "D":
                    r["ritardi_ms"] = [rit, rit]
                    r["input"] = [{"ok": not persi or k < 550, "latenza_ms": 150, "azione": "tasti"}]
                return r
            return {"profilo": prof, "riga": riga}
        xq = [rdp("A", "c16u01"), rdp("B", "c16u02"), rdp("C", "c16u03"), rdp("D", "c16u04")]
        g = classifica(livello("xrdp-verde", xq), sistema="xrdp")
        s1, s4 = g["sessioni"][0][3], g["sessioni"][3][3]
        guarda("xrdp sano ⇒ GREEN, senza saltati/buchi/audio, ritardo dal lato di chi guarda",
               g["classe"] == "GREEN" and "saltati_pct" not in s1 and "audio_udibile_pct" not in s4
               and s1["ritardo_p95_ms"]["valore"] == 30.0 and "ritardo_p95_ms" not in s4,
               _ragione_livello(g, _conti(g)))
        # ⛔ GUASTO: lo stesso livello letto da REMOTIX (senza --sistema) e' NON MISURATO
        g = classifica(livello("xrdp-come-remotix", xq))
        guarda("⛔ GUASTO: le serie xrdp lette senza --sistema xrdp ⇒ non misurato (DEGRADED)",
               g["classe"] == "DEGRADED" and g["significativo"])
        u = list(xq)
        u[2] = rdp("C", "c16u03", rit=200.0)
        g = classifica(livello("xrdp-lento", u), sistema="xrdp")
        guarda("⛔ GUASTO: xrdp con 200 ms impulso → disegno ⇒ FAIL", g["classe"] == "FAIL"
               and g["sessioni"][2][3]["ritardo_p95_ms"]["classe"] == "FAIL")
        u = list(xq)
        u[1] = rdp("B", "c16u02", persi=True)
        g = classifica(livello("xrdp-perso", u), sistema="xrdp")
        guarda("⛔ GUASTO: xrdp con input perso ⇒ FAIL", g["classe"] == "FAIL")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(esiti), sum(esiti)
    print("CERTIFICA %s — %d su %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def _conti(g):
    c = {"GREEN": 0, "DEGRADED": 0, "FAIL": 0}
    for s in g["sessioni"]:
        c[classe_di(s[3])] += 1
    return c


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--livello-dir")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--finestra-s", type=float, default=120.0)
    a.add_argument("--registro", default=REGISTRO)
    a.add_argument("--campagna", default=None)
    a.add_argument("--livello", type=int, default=None)
    a.add_argument("--fuso-log", type=float, default=0.0,
                   help="ore da UTC dell'orologio del registro del server (la scatola: UTC)")
    a.add_argument("--journal-scatola", choices=("gnome", "kde", "xfce", "lxqt"), default=None,
                   help="se manca journal-err.jsonl nel livello, lo chiede alla scatola (root)")
    a.add_argument("--secco", action="store_true", help="non scrive nel registro")
    a.add_argument("--sistema", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: le serie di 16-attore-rdp.py (fasi/20 §7.3); registro-xrdp.jsonl")
    a.add_argument("--json", action="store_true", help="stampa anche le righe del registro")
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.livello_dir:
        a.error("serve --livello-dir (o --certifica)")
    if o.sistema == "xrdp" and o.registro == REGISTRO:
        o.registro = os.path.join(QUI, "registro-xrdp.jsonl")
    g = classifica(o.livello_dir, o.fps_video, o.finestra_s, o.campagna, o.livello, o.fuso_log,
                   o.journal_scatola, o.sistema)
    stampa(g)
    righe = righe_registro(g)
    if o.json:
        for r in righe:
            print(json.dumps(r, ensure_ascii=False))
    if not o.secco:
        with open(o.registro, "a", encoding="utf-8") as f:
            for r in righe:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("→ %d righe in %s" % (len(righe), o.registro))
    return {"GREEN": 0, "DEGRADED": 3, "FAIL": 1}[g["classe"]]


if __name__ == "__main__":
    sys.exit(main())
