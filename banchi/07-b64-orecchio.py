#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-orecchio — IL GIUDICE CHE SENTE GLI SCOPPIETTII.

⛔ `07-b42` sa dire se quel che arriva e' **un tono** (frequenza, ampiezza,
   purezza).  ⚠ Non sa dire se quel tono ha dentro un **buco**: mezzo secondo
   di segnale saltato in mezzo a otto secondi sposta la purezza di un'inezia, e
   il verdetto resta verde.  ⇒ E' esattamente il difetto che R26 descrive —
   *«audio che scoppietta quando il desktop lavora»* — e nessuno strumento del
   progetto lo vedeva.

⭐ COME SI SENTE UNO SCOPPIETTIO, e non e' un conteggio.

   Un seno puro obbedisce a una ricorrenza di secondo ordine ESATTA:

        x[n] = 2·cos(ω)·x[n-1] − x[n-2]          ω = 2π·f/48000

   ⇒ Il **residuo** r[n] = x[n] − 2cos(ω)x[n-1] + x[n-2] vale zero su un tono
   perfetto, e vale **solo** dove la forma d'onda si spezza: un salto di fase
   (campioni persi e ricuciti), un silenzio che comincia, un ripieno a zero.
   ⛔ Non conta blocchi e non conta byte: guarda i CAMPIONI, che e' la regola
   (a) di `07-b43` e la prima riga di `LEZIONI.md` §2.2.

   ⚠ Il rumore di quantizzazione a 16 bit da' |r| di pochi LSB — con ampiezza
   0,5 (picco 16383) sono ~0,00025 dell'ampiezza.  La soglia sta a **0,02**,
   ottanta volte sopra: non si accende sul rumore, e si accende su un salto di
   fase di poco piu' di un grado.

⛔ E IL CONTROLLO POSITIVO STA DENTRO QUESTO FILE (`--certifica`): si fabbrica
   un tono perfetto, gli si tolgono 137 campioni nel mezzo, e si pretende che
   il giudice veda **quel** buco e **solo** quello.  Un giudice che non sa
   vedere il difetto che cerca non ha diritto al verde (`PIANO.md` §0.3.4).

Uso:
    python3 07-b64-orecchio.py --certifica
    python3 07-b64-orecchio.py giro.jsonl [--rif giro.rif.wav] [--hz 440]
"""
import argparse, base64, json, math, os, struct, sys, wave

FREQUENZA = 48000
CANALI = 2
PASSO_PCM_US = 5000          # §5.3: il blocco PCM e' di 5 ms
SOGLIA = 0.02                # frazione dell'ampiezza di picco


# ══════════════════════════════════════════════════════════════════════════
def residui(campioni, hz):
    """La ricorrenza di secondo ordine.  Torna il residuo, campione per campione."""
    w = 2.0 * math.cos(2.0 * math.pi * hz / FREQUENZA)
    fuori = [0.0, 0.0]
    for n in range(2, len(campioni)):
        fuori.append(campioni[n] - w * campioni[n - 1] + campioni[n - 2])
    return fuori


def scoppiettii(campioni, hz, soglia=SOGLIA):
    """⛔ Gli eventi, non i campioni: uno strappo dura qualche campione e
       conterebbe per tre o quattro.  Si raggruppa quel che sta entro 5 ms."""
    if len(campioni) < 64:
        return {"esito": "NIENTE DA GIUDICARE", "campioni": len(campioni)}
    picco = max(abs(x) for x in campioni) or 1.0
    r = residui(campioni, hz)
    lim = soglia * picco
    eventi, ultimo = [], None
    for n, v in enumerate(r):
        if abs(v) > lim:
            if ultimo is not None and n - ultimo["fine"] <= 240:
                ultimo["fine"] = n
                ultimo["salto"] = max(ultimo["salto"], abs(v) / picco)
            else:
                ultimo = {"campione": n, "fine": n, "ms": round(n * 1000.0 / FREQUENZA, 1),
                          "salto": abs(v) / picco}
                eventi.append(ultimo)
    for e in eventi:
        e["salto"] = round(e["salto"], 4)
        del e["fine"]
    # ⭐ Il residuo tipico, che dice se la soglia e' lontana o appiccicata
    ordinati = sorted(abs(v) for v in r)
    return {"esito": "GIUDICATO", "campioni": len(campioni),
            "picco": round(picco, 1),
            "residuo_mediano_rel": round(ordinati[len(ordinati) // 2] / picco, 6),
            "residuo_99_rel": round(ordinati[int(len(ordinati) * 0.99)] / picco, 6),
            "soglia_rel": soglia,
            "scoppiettii": len(eventi),
            "al_secondo": round(len(eventi) / (len(campioni) / FREQUENZA), 3),
            "dove": eventi[:40]}


# ══════════════════════════════════════════════════════════════════════════
def da_jsonl(percorso):
    """I blocchi PCM del cliente → i campioni del canale sinistro, e i BUCHI
       dichiarati dagli `istante` (§6.3: l'orologio del server, non il nostro)."""
    campioni, istanti = [], []
    for r in open(percorso):
        r = r.strip()
        if not r:
            continue
        d = json.loads(r)
        if d.get("codec") != 2:
            continue                       # ⛔ solo PCM: l'Opus lo giudica il browser
        b = base64.b64decode(d["byte"])
        n = len(b) // (2 * CANALI)
        v = struct.unpack("<%dh" % (n * CANALI), b[:n * CANALI * 2])
        campioni.extend(v[0::CANALI])
        istanti.append(d["istante"])
    buchi = []
    for i in range(1, len(istanti)):
        dt = istanti[i] - istanti[i - 1]
        if dt != PASSO_PCM_US:
            buchi.append({"blocco": i, "passo_us": dt})
    durata_dichiarata = (istanti[-1] - istanti[0] + PASSO_PCM_US) / 1e6 if istanti else 0.0
    return {"campioni": campioni, "blocchi": len(istanti), "buchi_istante": buchi,
            "durata_dichiarata_s": round(durata_dichiarata, 3),
            "durata_campioni_s": round(len(campioni) / FREQUENZA, 3)}


def da_wav(percorso):
    w = wave.open(percorso, "rb")
    n = w.getnframes(); ch = w.getnchannels()
    d = w.readframes(n)
    v = struct.unpack("<%dh" % (len(d) // 2), d)
    return {"campioni": list(v[0::ch]), "blocchi": None, "buchi_istante": [],
            "durata_dichiarata_s": round(n / w.getframerate(), 3),
            "durata_campioni_s": round(n / w.getframerate(), 3)}


# ══════════════════════════════════════════════════════════════════════════
def giudizio_completo(dati, hz, finestra_s):
    """⛔ La finestra del Goertzel dev'essere un numero INTERO di secondi, o il
       giudice di `07-b42` boccia un tono perfetto (§2.1, il riquadro)."""
    c = dati["campioni"]
    r = {"blocchi": dati["blocchi"],
         "durata_dichiarata_s": dati["durata_dichiarata_s"],
         "durata_campioni_s": dati["durata_campioni_s"],
         "buchi_istante": len(dati["buchi_istante"]),
         "buchi_istante_dove": dati["buchi_istante"][:20]}
    # ⭐ La deriva: quanti campioni MANCANO rispetto al tempo dichiarato.  Se il
    #    grafo salta un ciclo, i campioni non arrivano affatto e gli `istante`
    #    non se ne accorgono — questo numero si'.
    if dati["durata_dichiarata_s"]:
        atteso = dati["durata_dichiarata_s"] * FREQUENZA
        r["campioni_mancanti"] = int(atteso - len(c))
        r["resa_campioni"] = round(len(c) / atteso, 5) if atteso else None
    r.update({"scoppiettii": scoppiettii(c, hz)})
    # Il giudice certificato di 07-b42, su una finestra intera nel mezzo.
    n = finestra_s * FREQUENZA
    if len(c) >= n:
        i = (len(c) - n) // 2
        qui = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, qui)
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "g42", os.path.join(qui, "07-b42-giudice.py"))
        g42 = importlib.util.module_from_spec(sp); sp.loader.exec_module(g42)
        r["tono"] = g42.giudica([x / 32768.0 for x in c[i:i + n]])
    else:
        r["tono"] = {"esito": "NIENTE DA GIUDICARE",
                     "perche": "meno di %d s di campioni" % finestra_s}
    return r


# ══════════════════════════════════════════════════════════════════════════
def certifica(hz=440):
    """⛔ Il controllo positivo, e sono quattro casi: il giudice e' credibile
       solo se il caso sano da' ZERO e i tre guasti si vedono."""
    import random
    amp = 0.5 * 32767
    def seno(n0, n):
        return [int(amp * math.sin(2 * math.pi * hz * (n0 + k) / FREQUENZA)) for k in range(n)]
    sano = seno(0, FREQUENZA * 4)
    casi = []

    casi.append(("0-sano — un tono perfetto di 4 s", sano, 0))

    # 1 · 137 campioni tolti nel mezzo, e ricuciti: e' il BUCO di R26
    tagliato = sano[:FREQUENZA * 2] + seno(FREQUENZA * 2 + 137, FREQUENZA * 2 - 137)
    casi.append(("1-buco — 137 campioni (2,9 ms) tolti e ricuciti", tagliato, 1))

    # 2 · 10 ms di silenzio nel mezzo (il ripieno a zero di chi si e' svuotato)
    muto = sano[:FREQUENZA * 2] + [0] * 480 + sano[FREQUENZA * 2 + 480:]
    casi.append(("2-silenzio in mezzo — 10 ms di zeri", muto, 2))

    # 3 · dieci strappi sparsi
    #
    # ⛔ E la prima stesura di questo caso era SBAGLIATA, e il giudice l'ha
    #    denunciata: costruiva i tagli dal fondo (`for p in reversed(...)`)
    #    rigenerando ogni volta tutta la coda, cosi' ogni taglio cancellava
    #    quelli dopo di lui — ne restava **uno**, e il banco diceva «giudice
    #    cieco» su un giudice sano.  ⇒ Il difetto era nella SCENA, non nello
    #    strumento, ed e' la ragione per cui l'atteso si scrive prima: qui il
    #    disaccordo fra 10 e 1 ha trovato un difetto mio (`LEZIONI.md` §1.11).
    random.seed(7)
    posti = sorted(random.sample(range(FREQUENZA // 2, FREQUENZA * 7 // 2), 10))
    tanti, prima, salto = [], 0, 0
    for p in posti:
        tanti += seno(prima + salto, p - prima)
        prima, salto = p, salto + 61
    tanti += seno(prima + salto, len(sano) - prima)
    casi.append(("3-dieci strappi da 61 campioni", tanti, 10))

    print("⭐ CERTIFICAZIONE DEL GIUDICE — l'atteso e' scritto PRIMA\n")
    verde = True
    for nome, c, atteso in casi:
        e = scoppiettii(c, hz)
        visti = e["scoppiettii"]
        buono = (visti == atteso)
        verde = verde and buono
        print("  %-52s atteso %2d · visti %2d · residuo mediano %.6f  %s"
              % (nome, atteso, visti, e["residuo_mediano_rel"],
                 "OK" if buono else "⛔ NO"))
    print()
    if verde:
        print("⭐ quattro casi su quattro: il giudice sa vedere il difetto che cerca.")
    else:
        print("⛔ IL GIUDICE E' CIECO (o troppo sensibile): non si crede a un suo verde.")
    return 0 if verde else 3


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", nargs="?")
    p.add_argument("--rif", default="", help="il wav dell'arbitro indipendente (pw-record)")
    p.add_argument("--hz", type=int, default=440)
    p.add_argument("--finestra", type=int, default=1)
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()
    if a.certifica:
        return certifica(a.hz)
    if not a.jsonl:
        print("⛔ serve il JSONL, o --certifica", file=sys.stderr); return 2
    fuori = {"file": a.jsonl}
    if not os.path.exists(a.jsonl) or os.path.getsize(a.jsonl) == 0:
        # ⛔ CODER.md §3.10: «non ho letto niente» e' un esito SUO, non uno zero.
        fuori["esito"] = "NIENTE DA GIUDICARE — il JSONL non c'e' o e' vuoto"
        print(json.dumps(fuori, ensure_ascii=False, indent=1)); return 2
    fuori["nostro"] = giudizio_completo(da_jsonl(a.jsonl), a.hz, a.finestra)
    if a.rif and os.path.exists(a.rif) and os.path.getsize(a.rif) > 1000:
        fuori["arbitro_pw_record"] = giudizio_completo(da_wav(a.rif), a.hz, a.finestra)
    elif a.rif:
        fuori["arbitro_pw_record"] = "NIENTE DA GIUDICARE — il wav non c'e' o e' vuoto"
    print(json.dumps(fuori, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
