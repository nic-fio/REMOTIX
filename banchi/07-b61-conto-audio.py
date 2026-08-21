#!/usr/bin/env python3
"""07-b61 — IL CONTO DELL'AUDIO SI CHIUDE, oppure dice DOVE non si chiude.

    python3 banchi/07-b61-conto-audio.py <registro.log> [--cuscino 250]
    python3 banchi/07-b61-conto-audio.py --certifica     # i controlli positivi

⛔ PERCHE' ESISTE — 21 agosto 2026, e la ragione e' una riga di `fasi/07` §8
   che questo banco ha smentito con i numeri del registro che quella riga
   citava:

     *«Il conto chiude e assolve tutti gli altri anelli: non si perde niente,
       da nessuna parte.»*

   ⛔ Nella stessa sessione il figlio ha spedito **50,00 blocchi al secondo** e
   la pagina ne ha ricevuti **49,71**: 61 blocchi, cioe' **1,2 secondi di audio
   spariti in tre minuti e mezzo**.  E nella sessione di un'ora prima 684, con
   una finestra di 25 s al **47 % di perdita**.

⛔⛔ E LA RAGIONE PER CUI NESSUNO L'AVEVA VISTO E' LA FORMA DEI CONTATORI, non
    la disattenzione.  Ogni anello contava **se stesso** e ognuno era verde:

      · il figlio      «8256 blocchi spediti, **0 persi**» — vero: la sua
                       spedizione non fallisce mai, quel contatore misura le
                       chiamate riuscite, non i blocchi arrivati;
      · la pagina      «ricevuti 10621 · vecchi 0 · errori 0» — vero: un
                       datagram che non arriva **non e' un evento** da questa
                       parte.  `ricevuti` sale piu' piano, e un numero che sale
                       sembra sempre sano;
      · il server      «Rifiutati 2200» — ⛔ scritto nel registro **una volta
                       ogni cento** e mai sommato da nessuno.

    ⇒ La perdita non sta dentro nessun anello: sta **fra due anelli**, ed e'
    visibile solo a chi SOTTRAE il contatore di uno da quello dell'altro.  E'
    la stessa famiglia del difetto di sincronia di §9.7-bis — quattro anelli
    verdi e l'esperienza sbagliata — e la cura e' la stessa: si guarda la
    DIFFERENZA fra due flussi, non un flusso per volta.

⭐ E IL SECONDO CONTO, che e' quello che spiega il ritardo.  La coda dell'audio
   della pagina non e' un cuscino: e' un **serbatoio a senso unico**.

     coda(n) = coda(n-1) + (blocchi_ricevuti - blocchi_attesi) x 20 ms

   Il codice fa avanzare l'orologio di riproduzione di `n/48000` **per ogni
   blocco che arriva**, mai per il tempo che passa: un blocco perduto toglie
   20 ms di cuscino **per sempre**, e l'unica cosa che lo rimette a 250 e' un
   BUCO (la coda a zero) o il traboccamento a 600 ms.  ⇒ Il cuscino scende a
   scaletta fino al primo scatto udibile, e ricomincia.

   Questo banco calcola quella previsione e la confronta con la `coda` scritta
   nel diario.  ⛔ Se combaciano, il ritardo e' spiegato per intero da questi
   due termini e **non c'e' nessun terzo termine da cercare**.  Se non
   combaciano, c'e' dell'altro e va detto invece che dedotto.

⚠ QUEL CHE QUESTO BANCO NON SA FARE, dichiarato perche' non se ne prenda di
  piu' di quel che da':

  1. ⛔ **non misura la distanza fra quel che si vede e quel che si sente**.
     Misura la coda dell'audio, che ne e' il termine grosso ma non l'unico: la
     latenza del dispositivo di uscita e la coda del video non ci sono dentro.
     Il metro vero e' `07-b61-distanza.py`, e chiede una riga al percorso
     video che oggi non c'e';
  2. non distingue **dove** si perde il datagram — se nel pacer del server,
     nel Wi-Fi o nella coda di ricezione del browser.  Dice quanti e quando, e
     riporta la diagnosi che il server stesso scrive accanto al rifiuto;
  3. legge un registro **gia' scritto**: non accende niente e non tocca la
     sessione di nessuno.

⛔ E LA REGOLA DI `CODER.md` §3.10 E' L'OSSATURA DEL VERDETTO: «zero» e «non ho
   guardato» non hanno lo stesso aspetto.  Un registro senza righe del figlio
   non da' verde: da' `NIENTE DA GIUDICARE`, che e' un esito a se'.
"""
import argparse
import os
import re
import sys
import tempfile
import urllib.parse

# Un blocco di Opus dura 20 ms: 50 blocchi al secondo.  ⚠ Non e' una costante
# del protocollo — `RCP.md` §6.3 non fissa la durata del blocco — ed e' per
# questo che il banco la MISURA sul registro (il passo mediano dei `ricevuti`)
# invece di crederci, e usa questa solo come ripiego dichiarato.
DURATA_BLOCCO_MS_RIPIEGO = 20.0

# Quanto puo' sbagliare la previsione della coda prima che si dichiari che c'e'
# un terzo termine.  ⚠ La `coda` del diario e' un'istantanea presa a un momento
# qualunque dei 5 s, e i blocchi arrivano a grappoli: `[M]` sulla sessione vera
# lo scarto fra previsione e misura sta entro 20 ms su 42 campioni su 43.
TOLLERANZA_CODA_MS = 30.0


def _t2s(t):
    """«17:58:19.736» → secondi dalla mezzanotte."""
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


# ── Il registro: tre anelli, tre forme di riga ──────────────────────────────

_RE_FIGLIO = re.compile(
    r"^(\d\d:\d\d:\d\d\.\d+) figlio\s+audio: (\d+) blocchi spediti, (\d+) persi")
_RE_PAGINA = re.compile(
    r"^(\d\d:\d\d:\d\d\.\d+) pagina\s+GET /diario\?(\S+)")
_RE_RIFIUTO = re.compile(
    r"^(\d\d:\d\d:\d\d\.\d+) wt\s+.*datagram di \d+ byte NON messo.*"
    r"Rifiutati (\d+)\.(.*)$")


def leggi(testo):
    """Dal registro ai tre elenchi.  ⛔ Non giudica: legge e basta."""
    figlio, pagina, rifiuti = [], [], []
    for r in testo.splitlines():
        m = _RE_FIGLIO.match(r)
        if m:
            figlio.append((_t2s(m.group(1)), int(m.group(2)), int(m.group(3))))
            continue
        m = _RE_RIFIUTO.match(r)
        if m:
            perche = "congestione" if "E' LA CONGESTIONE" in m.group(3) else (
                "pacer" if "guarda il quanto" in m.group(3) else "?")
            rifiuti.append((_t2s(m.group(1)), int(m.group(2)), perche))
            continue
        m = _RE_PAGINA.match(r)
        if m:
            q = urllib.parse.unquote(m.group(2))
            def num(chiave):
                mm = re.search(chiave + r"\s+(\d+)", q)
                return int(mm.group(1)) if mm else None
            if num("ricevuti") is None:
                continue          # una riga di diario che non parla di audio
            pagina.append({
                "t": _t2s(m.group(1)), "ricevuti": num("ricevuti"),
                "suonati": num("suonati"), "buchi": num("BUCHI"),
                "vecchi": num("vecchi"), "pieni": num("pieni"),
                "errori": num("errori"), "coda": num("coda"),
            })
    figlio.sort(key=lambda x: x[0])
    pagina.sort(key=lambda x: x["t"])
    return figlio, pagina, rifiuti


def sessioni(pagina):
    """Una sessione nuova comincia dove `ricevuti` torna indietro.

    ⛔ Non si spezza sull'ORA: due sessioni possono attaccarsi a un secondo di
       distanza, e la pagina riparte da zero comunque.  Il contatore lo dice."""
    fuori, corrente = [], []
    for p in pagina:
        if corrente and p["ricevuti"] < corrente[-1]["ricevuti"]:
            fuori.append(corrente)
            corrente = []
        corrente.append(p)
    if corrente:
        fuori.append(corrente)
    return [s for s in fuori if len(s) >= 3]


def _interpola(figlio, t):
    """Il cumulativo del figlio all'istante `t`, fra due sue righe.

    ⛔ Serve l'interpolazione e non «la riga piu' vicina»: il figlio scrive una
       volta al secondo e la pagina una ogni cinque, e prendere la riga prima
       introdurrebbe fino a 50 blocchi di errore — cioe' l'ordine di grandezza
       di quel che si sta cercando."""
    if len(figlio) < 2 or t < figlio[0][0] or t > figlio[-1][0]:
        return None
    for i in range(len(figlio) - 1):
        a, b = figlio[i], figlio[i + 1]
        if a[0] <= t <= b[0]:
            if b[0] == a[0]:
                return float(a[1])
            return a[1] + (b[1] - a[1]) * (t - a[0]) / (b[0] - a[0])
    return None


def passo_misurato(sess, figlio):
    """La durata del blocco, misurata SUL PRODUTTORE e non sul consumatore.

    ⛔⛔ E QUI C'ERA UN DIFETTO DI QUESTO BANCO, trovato girandolo sul registro
        vero il 21 agosto 2026 — il primo giro dichiaro' *«il modello NON
        spiega la coda»* su una sessione che il modello spiega entro 20 ms.

        La prima scrittura prendeva la **mediana di Δt/Δricevuti**.  ⚠ E'
        circolare: `Δricevuti` e' depresso proprio dai blocchi che il banco sta
        cercando: la stima usciva 20,06 ms invece di 20,00, cioe' lo 0,3 % — e
        0,3 % su una finestra di 5 s sono 15 ms di errore che si SOMMANO
        campione dopo campione, fino a 284 ms su tre minuti.  ⇒ Il banco
        accusava il prodotto di un terzo termine che era **suo**.

    ⭐ La cura: il passo si misura sul figlio, che spedisce 50,00 blocchi al
       secondo qualunque cosa faccia la rete.  ⛔ E se il figlio non c'e', non
       si ripiega in silenzio sui 20 ms: si dichiara `RIPIEGO`, e il modello
       non si crede (§3.10 di nuovo — una stima presa da un'altra parte non e'
       una misura)."""
    if figlio:
        dentro = [f for f in figlio if sess[0]["t"] <= f[0] <= sess[-1]["t"]]
        if len(dentro) >= 2:
            dn = dentro[-1][1] - dentro[0][1]
            dt = dentro[-1][0] - dentro[0][0]
            if dn > 0 and dt > 0:
                return dt * 1000.0 / dn, "figlio"
    return DURATA_BLOCCO_MS_RIPIEGO, "RIPIEGO"


def giudica_sessione(sess, figlio, rifiuti, cuscino_ms):
    """Il verdetto di una sessione: il conto, e il modello della coda."""
    e = {"da": sess[0]["t"], "a": sess[-1]["t"], "campioni": len(sess)}
    e["durata_s"] = sess[-1]["t"] - sess[0]["t"]
    e["ricevuti"] = sess[-1]["ricevuti"] - sess[0]["ricevuti"]
    e["buchi_inizio"] = sess[0]["buchi"]
    e["buchi_dopo"] = sess[-1]["buchi"] - sess[0]["buchi"]
    e["pieni"] = sess[-1]["pieni"]
    e["vecchi"] = sess[-1]["vecchi"] - sess[0]["vecchi"]
    e["errori"] = sess[-1]["errori"]
    e["coda_min"] = min(p["coda"] for p in sess)
    e["coda_max"] = max(p["coda"] for p in sess)
    passo, da_dove = passo_misurato(sess, figlio)
    e["passo_ms"] = passo
    e["passo_da"] = da_dove

    # ── 1. Il conto fra il figlio e la pagina ───────────────────────────────
    s1 = _interpola(figlio, sess[0]["t"])
    s2 = _interpola(figlio, sess[-1]["t"])
    if s1 is None or s2 is None:
        # ⛔ §3.10: non e' «zero persi», e' «non ho potuto guardare».
        e["conto"] = "NIENTE DA GIUDICARE"
        e["motivo_conto"] = ("il registro non ha righe «figlio audio: N blocchi "
                             "spediti» che coprano questa sessione")
        e["spediti"] = e["persi"] = e["persi_pc"] = e["persi_ms"] = None
    else:
        e["conto"] = "letto"
        e["spediti"] = s2 - s1
        e["persi"] = e["spediti"] - e["ricevuti"]
        e["persi_pc"] = (100.0 * e["persi"] / e["spediti"]) if e["spediti"] else 0.0
        e["persi_ms"] = e["persi"] * passo

    # ── 2. I rifiuti del server dentro la finestra ──────────────────────────
    dentro = [r for r in rifiuti if sess[0]["t"] <= r[0] <= sess[-1]["t"]]
    e["rifiuti_righe"] = len(dentro)
    # ⚠ Il server scrive 1-poi-ogni-100: il contatore dell'ULTIMA riga e' il
    #   numero vero, le righe sono solo i campioni.  Se non c'e' nessuna riga
    #   il rifiutato puo' comunque essere fino a 99 — e si dichiara.
    e["rifiutati"] = dentro[-1][1] if dentro else 0
    e["rifiuti_perche"] = sorted({r[2] for r in dentro})
    e["rifiuti_incerti"] = (not dentro)

    # ── 3. Il modello della coda ────────────────────────────────────────────
    # coda(n) = coda(n-1) + (ricevuti - attesi) x passo, riarmata a `cuscino`
    # quando andrebbe sotto zero e quando supera il tetto.
    pred = float(sess[0]["coda"])
    scarti, serie, saltati = [], [], 0
    for a, b in zip(sess, sess[1:]):
        dt = b["t"] - a["t"]
        attesi = dt * 1000.0 / passo
        pred = pred + (b["ricevuti"] - a["ricevuti"] - attesi) * passo
        if pred < 0:
            pred = float(cuscino_ms)      # il BUCO: la coda si riarma
        # ⛔ E QUESTO E' IL SECONDO LIMITE DEL MODELLO, dichiarato invece che
        #    nascosto in una tolleranza larga: dentro una finestra di 5 s la
        #    coda puo' riarmarsi PIU' VOLTE (nella raffica delle 17:50 dieci
        #    volte in cinque secondi), e a che punto della finestra sia
        #    successo il modello non lo sa.  ⇒ La finestra in cui `BUCHI`
        #    sale non si giudica: la previsione si riaggancia alla misura e si
        #    riparte.  ⚠ Non e' indulgenza — e' che li' il modello non ha
        #    niente da dire, e giudicarlo lo stesso darebbe rosso al banco
        #    invece che al prodotto.
        if b["buchi"] > a["buchi"] or b["pieni"] > a["pieni"]:
            saltati += 1
            pred = float(b["coda"])
            serie.append((b["t"], b["coda"], None))
            continue
        serie.append((b["t"], b["coda"], pred))
        scarti.append(abs(pred - b["coda"]))
    e["modello_saltati"] = saltati
    e["modello_giudicati"] = len(scarti)
    e["modello_scarto_max"] = max(scarti) if scarti else 0.0
    e["modello_scarto_medio"] = (sum(scarti) / len(scarti)) if scarti else 0.0
    e["modello_fuori"] = sum(1 for s in scarti if s > TOLLERANZA_CODA_MS)
    e["modello_serie"] = serie

    # ── 4. I verdetti ───────────────────────────────────────────────────────
    if e["passo_da"] == "RIPIEGO" or e["modello_giudicati"] < 3:
        # ⛔ §3.10: senza il passo del produttore, o con meno di tre finestre
        #    pulite, il modello non si giudica.  Non e' «spiega».
        e["modello"] = "NIENTE DA GIUDICARE"
    elif e["modello_fuori"] == 0:
        e["modello"] = "SPIEGA"
    elif e["modello_fuori"] <= max(1, len(scarti) // 10):
        e["modello"] = "SPIEGA (con %d campioni fuori)" % e["modello_fuori"]
    else:
        e["modello"] = "NON SPIEGA"

    # ⛔ Ogni rilievo porta la sua MARCA accanto al testo, e la marca e' quel
    #    che la certificazione controlla.  ⚠ Senza, un caso innestato per
    #    provare il modello puo' diventare rosso per un'ALTRA regola e la
    #    certificazione lo conterebbe buono: sarebbe un banco che «sa diventare
    #    rosso» senza saper vedere la cosa per cui e' stato scritto.
    rossi = []
    if e["conto"] == "letto" and e["persi"] > max(2.0, 0.05 * e["durata_s"]):
        rossi.append(("persi",
            "PERSI %.0f blocchi fra il figlio e la pagina (%.2f %%, %.0f ms di "
            "audio) — e nessuno dei due contatori lo dice"
            % (e["persi"], e["persi_pc"], e["persi_ms"])))
    if e["buchi_dopo"] > 0:
        rossi.append(("buchi",
            "%d BUCHI DOPO il primo campione: sono scatti udibili in mezzo "
            "alla sessione, non dell'attacco" % e["buchi_dopo"]))
    if e["vecchi"] > 0:
        rossi.append(("vecchi", "%d datagram fuori ordine (§6.3)" % e["vecchi"]))
    if e["errori"] > 0:
        rossi.append(("errori", "%d errori del decodificatore" % e["errori"]))
    if e["coda_max"] - e["coda_min"] > 150:
        rossi.append(("vaga",
            "la coda VAGA di %d ms (da %d a %d): il ritardo fra quel che si "
            "vede e quel che si sente non e' una costante, e nessuna scelta "
            "di `AUDIO_CUSCINO_MS` lo rende tale finche' la coda si accorcia "
            "a ogni perdita"
            % (e["coda_max"] - e["coda_min"], e["coda_min"], e["coda_max"])))
    if e["modello"] == "NON SPIEGA":
        rossi.append(("modello",
            "il modello «serbatoio a senso unico» NON spiega la coda (%d "
            "campioni fuori di piu' di %.0f ms, massimo %.0f): c'e' un TERZO "
            "termine, e va trovato prima di curare gli altri due"
            % (e["modello_fuori"], TOLLERANZA_CODA_MS, e["modello_scarto_max"])))
    e["rossi"] = rossi
    e["marche"] = [m for m, _ in rossi]
    return e


def stampa(e, n):
    print("\n── sessione %d · %.0f s · %d campioni ─────────────────────────"
          % (n, e["durata_s"], e["campioni"]))
    print("   passo del blocco  %.3f ms (dal %s)" % (e["passo_ms"], e["passo_da"]))
    if e["conto"] == "NIENTE DA GIUDICARE":
        print("   ⭐ conto figlio→pagina  NIENTE DA GIUDICARE — %s"
              % e["motivo_conto"])
    else:
        print("   spediti dal figlio  %8.0f  (%.2f/s)"
              % (e["spediti"], e["spediti"] / e["durata_s"]))
        print("   ricevuti in pagina  %8d  (%.2f/s)"
              % (e["ricevuti"], e["ricevuti"] / e["durata_s"]))
        print("   ⛔ PERSI            %8.0f  (%.2f %%, %.0f ms di audio)"
              % (e["persi"], e["persi_pc"], e["persi_ms"]))
    print("   rifiutati dal server %7d %s%s"
          % (e["rifiutati"],
             ("(" + ", ".join(e["rifiuti_perche"]) + ")") if e["rifiuti_perche"] else "",
             "  ⚠ nessuna riga: puo' valere fino a 99 (si scrive 1 ogni 100)"
             if e["rifiuti_incerti"] else ""))
    print("   BUCHI  %d all'avvio + %d DOPO   ·  pieni %d  ·  vecchi %d  ·  errori %d"
          % (e["buchi_inizio"], e["buchi_dopo"], e["pieni"], e["vecchi"], e["errori"]))
    print("   coda   da %d a %d ms  (vaga di %d)"
          % (e["coda_min"], e["coda_max"], e["coda_max"] - e["coda_min"]))
    print("   modello «serbatoio a senso unico»: %s  — su %d finestre pulite "
          "(%d saltate perche' li' la coda si e' riarmata): scarto medio "
          "%.0f ms, massimo %.0f ms, %d fuori tolleranza"
          % (e["modello"], e["modello_giudicati"], e["modello_saltati"],
             e["modello_scarto_medio"], e["modello_scarto_max"],
             e["modello_fuori"]))
    for marca, r in e["rossi"]:
        print("   ⛔ [%s] %s" % (marca, r))
    if not e["rossi"]:
        print("   ⭐ nessun rilievo su questa sessione")


# ── LA CERTIFICAZIONE — ⛔ un banco che non sa diventare rosso non e' un banco ─

def _finto(durata_s=200.0, perdita=None, buchi_meta=False, con_figlio=True,
           con_pagina=True, coda_finta=None, cuscino=250, passo=20.0):
    """Fabbrica un registro finto con un guasto NOTO dentro.

    ⛔ Il guasto si innesta QUI, in una copia sintetica, e non nel prodotto:
       `PIANO.md` §0.3.4.  E ogni caso ha un atteso scritto prima."""
    righe = []
    t0 = 3600.0
    sped = 0
    ric = 0
    coda = float(cuscino)
    buchi = 1
    perdita = perdita or []      # elenco di (secondo, quanti blocchi persi)
    # il figlio: una riga al secondo, sempre 50 blocchi/s, sempre «0 persi»
    if con_figlio:
        for s in range(int(durata_s) + 6):
            sped += int(round(1000.0 / passo))
            righe.append((t0 - 3 + s, "%s figlio  audio: %d blocchi spediti, 0 persi, "
                          "128 fotogrammi in attesa nell'anello — codec 1"
                          % (_s2t(t0 - 3 + s), sped)))
    # la pagina: una riga ogni 5 s
    if con_pagina:
        for k in range(int(durata_s // 5) + 1):
            t = t0 + 5.0 * k
            attesi = int(round(5000.0 / passo))
            giu = sum(q for (s, q) in perdita if t - 5.0 < t0 + s <= t)
            arrivati = attesi - giu if k else 0
            ric += arrivati
            if k:
                coda += (arrivati - attesi) * passo
                if coda < 0:
                    coda = float(cuscino)
                    buchi += 1
            if buchi_meta and abs(t - (t0 + durata_s / 2)) < 2.5:
                buchi += 3
            c = coda if coda_finta is None else coda_finta(k, coda)
            riga = ("audio: ricevuti %d suonati %d BUCHI %d vecchi 0 pieni 0 "
                    "errori 0 coda %dms ctx running | tasti 0 ultimo - "
                    % (ric, ric, buchi, int(round(c))))
            righe.append((t, "%s pagina  GET /diario?%s da 10.0.0.1:1"
                          % (_s2t(t), urllib.parse.quote(riga))))
    righe.sort(key=lambda x: x[0])
    return "\n".join(r for _, r in righe) + "\n"


def _s2t(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    return "%02d:%02d:%06.3f" % (h, m, s % 60)


def certifica(cuscino):
    """I casi in cui questo banco DEVE diventare rosso, E PER LA RAGIONE GIUSTA.

    ⛔ L'atteso non e' «rosso»: e' la MARCA del rilievo.  Un caso innestato per
       provare il modello che diventasse rosso perche' un'altra regola ha visto
       le perdite passerebbe una certificazione scritta sul colore, e il banco
       resterebbe cieco proprio dove serve."""
    casi = [
        # (nome, registro finto, atteso, marca che DEVE comparire)
        ("sano — 0 persi, coda ferma al cuscino",
         _finto(), "VERDE", None),

        # ⭐ il caso VERO: la sessione di Windows del 21 agosto, 0,6 % a strappi
        ("perdita lenta 0,6 % (la sessione vera del 21 agosto)",
         _finto(perdita=[(100, 8), (105, 4), (110, 4), (115, 4),
                         (120, 13), (125, 6), (130, 8), (180, 8)]),
         "ROSSO", "persi"),

        # ⭐ la raffica delle 17:50, 47 % per 25 s
        ("raffica 47 % per 25 s (le 17:50 del 21 agosto)",
         _finto(perdita=[(s, 118) for s in range(60, 85, 5)]),
         "ROSSO", "persi"),

        ("buchi a meta' sessione, senza nessuna perdita",
         _finto(buchi_meta=True), "ROSSO", "buchi"),

        # ⛔ IL CASO CHE CERTIFICA IL MODELLO, e va costruito con cura: si
        #    perdono blocchi e la coda NON scende.  Sotto il modello e'
        #    impossibile ⇒ c'e' un terzo termine.  ⚠ La coda resta piatta,
        #    quindi la regola «vaga» NON puo' rubare il verdetto.
        ("si perde e la coda non scende: c'e' un TERZO termine",
         _finto(perdita=[(s, 10) for s in range(50, 150, 5)],
                coda_finta=lambda k, c: 250), "ROSSO", "modello"),

        # ⛔ e il suo gemello: la coda scende senza che si perda niente
        ("la coda scende e non si perde niente: terzo termine, altro verso",
         _finto(coda_finta=lambda k, c: max(10, 250 - 12 * k)),
         "ROSSO", "modello"),

        # ⛔ §3.10: «zero persi» e «non ho guardato» non hanno lo stesso aspetto
        ("registro senza le righe del figlio",
         _finto(con_figlio=False), "NIENTE DA GIUDICARE", None),
        ("registro senza le righe della pagina",
         _finto(con_pagina=False), "NIENTE DA GIUDICARE", None),
    ]

    print("⛔ CERTIFICAZIONE — un banco che non sa diventare rosso non e' un "
          "banco, e uno che diventa rosso per la ragione sbagliata e' peggio\n")
    ok = 0
    for i, (nome, testo, atteso, marca) in enumerate(casi):
        figlio, pagina, rifiuti = leggi(testo)
        sess = sessioni(pagina)
        marche = []
        if not sess:
            visto, det = "NIENTE DA GIUDICARE", "nessuna sessione nel registro"
        else:
            e = giudica_sessione(sess[0], figlio, rifiuti, cuscino)
            marche = e["marche"]
            if e["conto"] == "NIENTE DA GIUDICARE" and not e["rossi"]:
                visto, det = "NIENTE DA GIUDICARE", e["motivo_conto"]
            elif e["rossi"]:
                visto, det = "ROSSO", e["rossi"][0][1]
            else:
                visto, det = "VERDE", "nessun rilievo"
        bene = (visto == atteso) and (marca is None or marca in marche)
        ok += bene
        print("  %s %d · %-52s atteso %-20s visto %-20s"
              % ("⭐" if bene else "⛔", i, nome[:52], atteso, visto))
        print("        marca attesa %-9s viste %-28s"
              % (marca or "—", ",".join(marche) or "—"))
        print("        %s" % det[:110])
    print("\n%s %d casi su %d" % ("⭐" if ok == len(casi) else "⛔", ok, len(casi)))
    return 0 if ok == len(casi) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("registro", nargs="?", help="il registro.log da leggere")
    p.add_argument("--cuscino", type=int, default=250,
                   help="AUDIO_CUSCINO_MS in vigore nella pagina (default 250)")
    p.add_argument("--certifica", action="store_true",
                   help="i controlli positivi, su registri finti")
    a = p.parse_args()

    if a.certifica:
        return certifica(a.cuscino)
    if not a.registro:
        p.error("serve un registro, oppure --certifica")
    if not os.path.exists(a.registro):
        print("⛔ non c'e': " + a.registro)
        return 2

    testo = open(a.registro, encoding="utf-8", errors="replace").read()
    figlio, pagina, rifiuti = leggi(testo)
    print("registro: %s" % a.registro)
    print("  righe del figlio  %d   ·  righe di diario  %d  ·  rifiuti scritti  %d"
          % (len(figlio), len(pagina), len(rifiuti)))
    sess = sessioni(pagina)
    if not sess:
        # ⛔ §3.10 di nuovo, al livello del registro intero.
        print("\n⭐ NIENTE DA GIUDICARE: nessuna sessione con almeno tre "
              "campioni di diario.  ⚠ Non e' «tutto a posto»: e' «non ho "
              "guardato niente».")
        return 3
    esiti = [giudica_sessione(s, figlio, rifiuti, a.cuscino) for s in sess]
    for i, e in enumerate(esiti):
        stampa(e, i)
    rossi = sum(len(e["rossi"]) for e in esiti)
    print("\n%s in tutto: %d rilievi su %d sessioni"
          % ("⛔" if rossi else "⭐", rossi, len(esiti)))
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
