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

# ⛔⛔ IL PICCO MINIMO, ED E' LA CURA DEL RILIEVO R7 — 22 agosto 2026.
#
#      La riga era `picco = max(abs(x) ...) or 1.0`, e su campioni **tutti
#      zero** il picco diventava **1,0**: la soglia scendeva a 0,02, i residui
#      erano zero, e il giudice rispondeva `scoppiettii 0`.
#      ⇒ **Il giudice dell'orecchio dava il voto massimo al silenzio**, che e'
#      la forma d'errore che questa fase esiste per non commettere
#      (`LEZIONI.md` §2.2: il banco restava verde mentre l'audio era rotto).
#
# ⭐ La cura non e' un `or` piu' furbo: e' che sotto un certo segnale il giudice
#    **rifiuta di giudicare**.  Il residuo di quantizzazione di un segnale a 16
#    bit vale ~4 LSB; perche' la soglia (2 % del picco) stia sopra quel rumore
#    serve un picco di almeno ~400.  Sotto, il rivelatore non distingue piu'
#    niente da niente, e dirlo e' l'unica risposta onesta (`CODER.md` §3.10).
PICCO_MINIMO = 400           # ~1,2 % del fondo scala a 16 bit

# ⛔⛔⛔ IL BUCO CIECO, E SI DICHIARA QUI PERCHE' NON SI PUO' TOGLIERE.
#
#       Un taglio di N campioni si ricuce **in fase** — cioe' invisibile al
#       residuo — quando N x f / 48000 e' un numero intero di cicli.  Con il
#       tono a **440 Hz** e i blocchi PCM da **240 campioni** (5 ms):
#
#           1200 campioni = 5 blocchi = **11,000 cicli esatti** → invisibile
#           2400 campioni = 10 blocchi = 22,000 cicli          → invisibile
#           1201 campioni                = 11,009 cicli        → visto
#
#       `[M]` 22 agosto 2026, riprodotto sul giudice di ieri: 25 ms e 50 ms di
#       audio spariti danno **scoppiettii 0**.
#
# ⭐ Non si cura dentro il rivelatore — su un seno perfetto quel taglio **non
#    lascia traccia nei campioni**, e nessun algoritmo puo' vederlo.  Si cura
#    con una SECONDA GAMBA che non guarda la forma d'onda ma il **conto**: i
#    campioni arrivati contro quelli attesi.  ⇒ `scoppiettii()` accetta
#    `attesi`, e il verdetto composto guarda tutt'e due.
#
# ⭐⭐ E PER LE SCENE FUTURE C'E' UNA CURA CHE COSTA UNA CIFRA: un tono che con
#     il blocco non va mai a numero intero.  A **443 Hz** un taglio di k blocchi
#     vale 2,215 k cicli, e il primo intero arriva a **200 blocchi = 1 secondo**
#     invece che a cinque.  ⚠ Il 440 resta finche' le misure vecchie servono a
#     confronto: cambiarlo adesso renderebbe incomparabili i numeri di ieri.
BLOCCO_PCM_CAMPIONI = 240    # 5 ms su un canale


# ══════════════════════════════════════════════════════════════════════════
def residui(campioni, hz):
    """La ricorrenza di secondo ordine.  Torna il residuo, campione per campione."""
    w = 2.0 * math.cos(2.0 * math.pi * hz / FREQUENZA)
    fuori = [0.0, 0.0]
    for n in range(2, len(campioni)):
        fuori.append(campioni[n] - w * campioni[n - 1] + campioni[n - 2])
    return fuori


def scoppiettii(campioni, hz, soglia=SOGLIA, attesi=None):
    """⛔ Gli eventi, non i campioni: uno strappo dura qualche campione e
       conterebbe per tre o quattro.  Si raggruppa quel che sta entro 5 ms.

    ⛔ `attesi` e' la SECONDA GAMBA (R7): quanti campioni avrebbero dovuto
       esserci.  Il residuo non vede un taglio multiplo di 1200 campioni; il
       conto si'.  ⚠ Se non lo si passa, il giudizio vale solo per quel che la
       forma d'onda sa dire, e questo esito lo dichiara."""
    if len(campioni) < 64:
        return {"esito": "NIENTE DA GIUDICARE", "campioni": len(campioni)}
    picco = max(abs(x) for x in campioni)
    if picco < PICCO_MINIMO:
        # ⛔ R7: qui prima usciva `scoppiettii 0`, cioe' il massimo dei voti.
        return {"esito": "SILENZIO O QUASI — NON GIUDICO",
                "perche": "picco %d sotto il minimo di %d: la soglia del "
                          "rivelatore finirebbe sotto il rumore di "
                          "quantizzazione, e ogni risposta sarebbe inventata"
                          % (picco, PICCO_MINIMO),
                "campioni": len(campioni), "picco": picco}
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
    # ⭐ LA SECONDA GAMBA: il conto, che vede quel che il residuo non puo'.
    manca = None
    cieco = None
    if attesi:
        manca = int(attesi) - len(campioni)
        if manca > 0:
            # ⚠ E si dice se quel buco sarebbe stato invisibile al residuo: e'
            #   l'informazione che spiega un «zero scoppiettii» accanto a un
            #   ammanco vero, invece di lasciarli contraddirsi in silenzio.
            cieco = abs(manca * hz / FREQUENZA
                        - round(manca * hz / FREQUENZA)) < 0.01
    return {"esito": "GIUDICATO", "campioni": len(campioni),
            "campioni_attesi": attesi,
            "campioni_mancanti": manca,
            "ammanco_invisibile_al_residuo": cieco,
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
    # ⛔ `attesi` viene dagli `istante` del server (§6.3), non dal nostro
    #    orologio: e' l'unico numero che dica quanti campioni ci dovevano essere.
    attesi = (int(round(dati["durata_dichiarata_s"] * FREQUENZA))
              if dati["durata_dichiarata_s"] else None)
    r.update({"scoppiettii": scoppiettii(c, hz, attesi=attesi)})
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
    """⛔ Il controllo positivo, e adesso sono SETTE casi.

    ⛔⛔ I due che mancavano li ha trovati il revisore (R7), non io, e sono
         proprio i due che rendevano credibile un verde falso:

           · **il silenzio**, che prendeva il voto massimo;
           · **il taglio da 1200 campioni**, invisibile al residuo perche' e'
             un numero intero di cicli (11,000 esatti a 440 Hz).

    ⭐ E il caso cieco NON si dichiara verde perche' il residuo tace: si
       dichiara verde solo se la SECONDA GAMBA — il conto dei campioni — lo
       vede.  Un banco che non sa vedere il difetto che cerca non ha diritto al
       verde (`PIANO.md` §0.3.4), e un banco che lo sa vedere solo con un altro
       strumento deve dire quale.
    """
    import random
    amp = 0.5 * 32767

    def seno(n0, n, f=hz):
        return [int(amp * math.sin(2 * math.pi * f * (n0 + k) / FREQUENZA))
                for k in range(n)]

    sano = seno(0, FREQUENZA * 4)
    casi = []

    def taglia(quanti):
        return sano[:FREQUENZA * 2] + seno(FREQUENZA * 2 + quanti,
                                           FREQUENZA * 2 - quanti)

    #  (nome, campioni, attesi, scoppiettii attesi, chi lo deve vedere)
    casi.append(("0-sano — un tono perfetto di 4 s", sano, None, 0, "nessuno: e' sano"))
    casi.append(("1-buco — 137 campioni (2,9 ms) tolti e ricuciti",
                 taglia(137), None, 1, "il residuo"))
    casi.append(("2-silenzio in mezzo — 10 ms di zeri",
                 sano[:FREQUENZA * 2] + [0] * 480 + sano[FREQUENZA * 2 + 480:],
                 None, 2, "il residuo"))

    random.seed(7)
    posti = sorted(random.sample(range(FREQUENZA // 2, FREQUENZA * 7 // 2), 10))
    tanti, prima, salto = [], 0, 0
    for p in posti:
        tanti += seno(prima + salto, p - prima)
        prima, salto = p, salto + 61
    tanti += seno(prima + salto, len(sano) - prima)
    casi.append(("3-dieci strappi da 61 campioni", tanti, None, 10, "il residuo"))

    # ⛔ R7a — IL SILENZIO.  Prima dava `scoppiettii 0`, cioe' il massimo.
    casi.append(("4-⛔ R7a: quattro secondi di ZERI", [0] * (FREQUENZA * 4),
                 None, "SILENZIO O QUASI — NON GIUDICO", "il rifiuto"))

    # ⛔ R7b — IL BUCO CIECO.  Il residuo non lo vede e non puo' vederlo: 1200
    #    campioni sono 11,000 cicli esatti.  Lo deve vedere IL CONTO.
    casi.append(("5-⛔ R7b: 1200 campioni tolti (25 ms = 11,000 cicli)",
                 taglia(1200), FREQUENZA * 4, 0, "⭐ il CONTO (1200 mancanti)"))
    casi.append(("6-⛔ R7b: 2400 campioni tolti (50 ms = 22,000 cicli)",
                 taglia(2400), FREQUENZA * 4, 0, "⭐ il CONTO (2400 mancanti)"))

    print("⭐ CERTIFICAZIONE DEL GIUDICE — l'atteso e' scritto PRIMA\n")
    verde = True
    for nome, c, attesi, atteso, chi in casi:
        e = scoppiettii(c, hz, attesi=attesi)
        if isinstance(atteso, str):
            visto = e.get("esito")
            buono = visto.startswith(atteso[:12])
        else:
            visto = e.get("scoppiettii")
            buono = (visto == atteso)
            # ⛔ E per i due casi ciechi il verde non basta che il residuo
            #    taccia: il conto DEVE dire quanto manca, o il banco e' cieco.
            if attesi is not None:
                manca = e.get("campioni_mancanti")
                if not manca or manca != attesi - len(c):
                    buono = False
                    visto = "%s (conto: %s)" % (visto, manca)
                else:
                    visto = "%s, e il conto vede %d mancanti (invisibile al "\
                            "residuo: %s)" % (visto, manca,
                                              e.get("ammanco_invisibile_al_residuo"))
        verde = verde and buono
        print("  %-52s atteso %-6s · %s\n      %s  chi lo vede: %s"
              % (nome, atteso, visto, "OK" if buono else "⛔ NO", chi))
    print()
    # ⭐ E il controllo del CONTROLLO: a 443 Hz il buco cieco non c'e' piu'.
    #    ⚠ Non e' una cura da applicare oggi (renderebbe incomparabili le misure
    #    di ieri): e' la prova che la diagnosi del buco cieco e' giusta.
    rotto443 = ([int(amp * math.sin(2 * math.pi * 443 * k / FREQUENZA))
                 for k in range(FREQUENZA * 2)]
                + [int(amp * math.sin(2 * math.pi * 443 * (k + FREQUENZA * 2 + 1200)
                                      / FREQUENZA))
                   for k in range(FREQUENZA * 2 - 1200)])
    e443 = scoppiettii(rotto443, 443)
    ok443 = e443.get("scoppiettii") == 1
    verde = verde and ok443
    print("  %-52s atteso %-6s · %s  %s"
          % ("7-⭐ lo stesso taglio a 443 Hz (11,075 cicli)", 1,
             e443.get("scoppiettii"), "OK" if ok443 else "⛔ NO"))
    print("      ⇒ il buco cieco e' del TONO, non del rivelatore: a 443 Hz sparisce")
    print()
    if verde:
        print("⭐ sette casi su sette: il giudice sa vedere il difetto che cerca,")
        print("   e dove NON puo' vederlo dice quale altro strumento lo vede.")
    else:
        print("⛔ IL GIUDICE E' CIECO: non si crede a un suo verde.")
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
