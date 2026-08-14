#!/usr/bin/env python3
"""04-b31-gemelli.py — ⛔ IL BANCO DEL CICLO A VUOTO: quando la sessione grafica
muore SOTTO un figlio vivo, che cosa fa il figlio?

    python3 04-b31-gemelli.py --certifica
    python3 04-b31-gemelli.py --spia FILE --etichetta g1-prima \\
            --scena "..." --esiti 04-b31-esiti.jsonl

⚠ Gira dove c'e' `python3` e basta: niente rete, niente ffmpeg.  Legge l'uscita
  di `04-b31-terreno.sh spia`, che e' l'unica cosa che si puo' misurare **da
  fuori** senza rallentare quel che si sta guardando.

===========================================================================
⛔ IL DIFETTO, MISURATO E NON DEDOTTO
===========================================================================

`[M]` 14 agosto 2026, sessione vera dell'utente: la sessione grafica e' morta
sotto un figlio vivo, la cattura e' andata in `connection error`, e il figlio ha
continuato a girare scrivendo il registro **a raffica**: ⛔ **30,8 GB di
registro e 112 milioni di righe identiche, tutte nello stesso millisecondo.**

⇒ Su una macchina vera **riempie il disco**.  E il disco pieno non e' un difetto
  del desktop remoto: e' un difetto della macchina dell'utente, prodotto da noi.

===========================================================================
⛔ DUE GRANDEZZE, E UNA SOLA NON BASTA
===========================================================================

  · ⭐ **il registro che cresce** — byte al secondo.  E' il danno vero (il
    disco), ed e' quel che l'utente ha misurato;
  · ⭐ **la CPU bruciata dal figlio** — frazione di un nucleo.  ⛔ Serve perche'
    una cura che si limitasse a **tacere** (una riga di registro in meno)
    lascerebbe il ciclo a girare a vuoto: il registro tornerebbe verde e il
    difetto sarebbe ancora li', con la ventola accesa e la batteria che scende.

⚠ Sono due misure, e il verdetto le vuole **tutt'e due** sotto soglia.

===========================================================================
⛔ LE SOGLIE, SCRITTE PRIMA DEL GIRO
===========================================================================

  `REGISTRO_MAX = 1 000 000` byte al secondo.
     Un figlio sano su una scena viva scrive **una riga al secondo** (il conto
     del ciclo, `figlio.c`), cioe' ~200 B/s: la soglia e' cinquemila volte
     tanto.  ⛔ E il difetto vivo sta cento volte SOPRA la soglia (30,8 GB in
     pochi minuti).  ⇒ Fra il sano e il guasto ci sono cinque ordini di
     grandezza, e la soglia sta in mezzo: non e' una soglia da limare.

  `CPU_MAX = 0,50` nuclei.
     ⚠ Non e' zero, e non deve esserlo: un figlio che **codifica** consuma —
     `[M]` ~3 ms per fotogramma a 60/s fa ~0,2 nuclei.  Un ciclo che gira a
     vuoto consuma **un nucleo intero**.

===========================================================================
⛔ I CODICI D'USCITA
===========================================================================

    0  ⭐ VERDE            il figlio non gira a vuoto e non scrive a raffica
    1  ⛔ ROSSO            gira a vuoto, scrive a raffica, o tutt'e due
    2  ⛔ NON GIUDICABILE  la spia non ha potuto misurare
    4     USO SBAGLIATO
"""
import argparse
import json
import sys
import time

# --- le soglie, SCRITTE PRIMA DEL GIRO -------------------------------------
REGISTRO_MAX = 1_000_000   # byte al secondo
CPU_MAX = 0.50             # nuclei

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def dimmi(*a):
    print(*a, flush=True)


def leggi_spia(testo):
    """Le righe `CHIAVE valore` che `04-b31-terreno.sh spia` stampa.

    ⛔ Se manca una delle quattro non si mette uno zero al suo posto: «non l'ho
       misurato» e «e' zero» sono la stessa faccia solo per chi non guarda
       (`CODER.md` §3.10)."""
    v = {}
    for r in testo.splitlines():
        p = r.split()
        if len(p) == 2 and p[0].isupper():
            v[p[0]] = p[1]
    if "SPIA nessun_figlio" in testo:
        return None, "non c'era nessun figlio da spiare"
    for k in ("SPIA_SECONDI", "SPIA_TICK", "SPIA_HZ", "SPIA_BYTE"):
        if k not in v:
            return None, f"la spia non ha stampato «{k}»: non si e' misurato niente"
    try:
        s = float(v["SPIA_SECONDI"])
        tick = float(v["SPIA_TICK"])
        hz = float(v["SPIA_HZ"])
        byte = float(v["SPIA_BYTE"])
    except ValueError as e:
        return None, f"la spia ha stampato qualcosa che non e' un numero: {e}"
    if s <= 0 or hz <= 0:
        return None, "la finestra della spia e' zero: non si e' misurato niente"
    return {"secondi": s, "nuclei": round(tick / hz / s, 3),
            "byte_al_secondo": round(byte / s, 1), "byte": byte,
            "totale": float(v.get("SPIA_REGISTRO_TOTALE", 0))}, None


def giudica(m):
    """⛔ Tutt'e due sotto soglia, o e' rosso — e si dice QUALE delle due."""
    male = []
    if m["byte_al_secondo"] > REGISTRO_MAX:
        male.append(f"il registro cresce di {m['byte_al_secondo']:.0f} B/s "
                    f"(soglia {REGISTRO_MAX})")
    if m["nuclei"] > CPU_MAX:
        male.append(f"il figlio brucia {m['nuclei']:.2f} nuclei "
                    f"(soglia {CPU_MAX})")
    return male


def principale(a):
    if a.certifica:
        return certifica()
    if not a.spia:
        dimmi("⛔ serve --spia FILE (l'uscita di `04-b31-terreno.sh spia`)")
        return 4
    try:
        with open(a.spia, encoding="utf-8") as f:
            testo = f.read()
    except OSError as e:
        dimmi(f"   ⛔ NON GIUDICABILE: la spia non si legge ({e})")
        return 2

    dimmi(f"== O1 · 04-b31 — il ciclo a vuoto, «{a.etichetta}»")
    dimmi(f"   scena: {a.scena}")
    m, perche = leggi_spia(testo)
    riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "banco": "04-b31-gemelli", "etichetta": a.etichetta,
            "scena": a.scena, "registro_max": REGISTRO_MAX, "cpu_max": CPU_MAX}
    if m is None:
        dimmi(f"\n   {GIALLO}⇒ NON GIUDICABILE: {perche}{GRIGIO}")
        riga.update(verdetto="NON GIUDICABILE", uscita=2, perche=perche)
        scrivi(a, riga)
        return 2

    dimmi(f"   finestra: {m['secondi']:.0f} s")
    dimmi(f"   registro: +{m['byte']:.0f} byte  ⇒ {m['byte_al_secondo']:.0f} B/s"
          f"   (soglia {REGISTRO_MAX})")
    dimmi(f"   CPU:      {m['nuclei']:.2f} nuclei"
          f"                    (soglia {CPU_MAX})")
    riga.update(**{k: v for k, v in m.items()})

    male = giudica(m)
    if male:
        dimmi(f"\n   {ROSSO}⇒ IL FIGLIO GIRA A VUOTO{GRIGIO}")
        for x in male:
            dimmi(f"      ⛔ {x}")
        dimmi("      ⚠ Un figlio senza palco non e' «una sessione ferma» "
              "(§8.3): e' un")
        dimmi("        figlio che non serve a niente, e che puo' riempire il "
              "disco.")
        riga.update(verdetto="GIRA A VUOTO", uscita=1, perche="; ".join(male))
        scrivi(a, riga)
        return 1
    dimmi(f"\n   {VERDE}⇒ VERDE: il figlio non gira a vuoto e non scrive a "
          f"raffica{GRIGIO}")
    riga.update(verdetto="FERMO", uscita=0)
    scrivi(a, riga)
    return 0


def scrivi(a, riga):
    if a.esiti:
        with open(a.esiti, "a") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")


# ===========================================================================
def certifica():
    """⭐ Lo strumento sa dire di si', di no, e «non ho potuto guardare».

    ⛔ E i casi non sono tre a caso: sono i quattro modi in cui questo giudizio
       puo' sbagliare, uno per volta.  In particolare **il caso `solo-cpu`**:
       una cura che togliesse la riga di registro e lasciasse il ciclo a girare
       farebbe verde un banco che guardasse il solo disco.
    """
    dimmi("== O1 · 04-b31 — la certificazione del giudizio sul ciclo a vuoto")
    casi = [
        ("sano", "SPIA_SECONDI 3\nSPIA_TICK 30\nSPIA_HZ 100\nSPIA_BYTE 600\n",
         0, "0,10 nuclei e 200 B/s: un figlio che codifica"),
        ("raffica", "SPIA_SECONDI 3\nSPIA_TICK 300\nSPIA_HZ 100\n"
                    "SPIA_BYTE 400000000\n", 1,
         "⛔ il difetto vivo: 133 MB/s e un nucleo intero"),
        ("solo-cpu", "SPIA_SECONDI 3\nSPIA_TICK 300\nSPIA_HZ 100\n"
                     "SPIA_BYTE 600\n", 1,
         "⛔ gira a vuoto IN SILENZIO: il registro e' pulito e il nucleo brucia"),
        ("solo-registro", "SPIA_SECONDI 3\nSPIA_TICK 3\nSPIA_HZ 100\n"
                          "SPIA_BYTE 400000000\n", 1,
         "⛔ scrive a raffica senza consumare: il disco si riempie lo stesso"),
        ("niente-figlio", "SPIA nessun_figlio\n", 2,
         "«non c'era niente da spiare» NON e' «e' tutto a posto»"),
        ("spia-monca", "SPIA_SECONDI 3\nSPIA_HZ 100\n", 2,
         "manca una grandezza ⇒ non si giudica, e non si mette uno zero"),
    ]
    esito = 0
    for nome, testo, atteso, dice in casi:
        m, perche = leggi_spia(testo)
        if m is None:
            u = 2
        else:
            u = 1 if giudica(m) else 0
        segno = VERDE + "OK" + GRIGIO if u == atteso else ROSSO + "NO" + GRIGIO
        extra = (f"{m['nuclei']:.2f} nuclei, {m['byte_al_secondo']:.0f} B/s"
                 if m else perche)
        dimmi(f"   {segno}  {nome}: uscita {u}, attesa {atteso} — {dice}")
        dimmi(f"        [{extra}]")
        if u != atteso:
            esito = 2
    dimmi("")
    if esito == 0:
        dimmi(f"   {VERDE}⭐ lo strumento distingue il sano, le due facce del "
              f"guasto e il «non ho potuto guardare»{GRIGIO}")
    else:
        dimmi(f"   {ROSSO}⛔ non certificato{GRIGIO}")
    return esito


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="O1 — il ciclo a vuoto")
    p.add_argument("--spia", help="il file con l'uscita di `terreno.sh spia`")
    p.add_argument("--etichetta", default="senza-nome")
    p.add_argument("--scena", default="(non dichiarata)")
    p.add_argument("--esiti", default="")
    p.add_argument("--certifica", action="store_true")
    sys.exit(principale(p.parse_args()))
