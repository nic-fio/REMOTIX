#!/usr/bin/env python3
"""
07-b42 — il giudice dell'audio: ASCOLTA, non conta i blocchi.

⛔ `LEZIONI.md` §2.2, prima riga della tabella: «il banco contava fotogrammi
   spediti e blocchi riscontrati; il difetto cambiava **i campioni** — l'audio
   era rumore a fondo scala».  ⇒ Qui si misura il SEGNALE:

     hz        la frequenza dominante (Goertzel, passo 1 Hz)
     rms       l'ampiezza
     purezza   quanta energia sta nella riga dominante — ⭐ e' l'unico numero
               che distingue un TONO da RUMORE, ed e' quello che il giudice
               della sonda `07-b40` ha gia' certificato su sei casi

⭐ E in piu' misura una cosa che la sonda non poteva: **il ritmo**.  Gli
   `istante` di §6.3 sono l'orologio del server, quindi i buchi si contano
   dove sono nati invece di dedurli dal silenzio.

Legge il JSONL che `01-b3-cliente.py --audio-scrivi` produce.

Uso:  python3 07-b42-giudice.py blocchi.jsonl [--hz 440] [--secondi 3]
"""
import argparse
import base64
import json
import math
import sys

FREQUENZA = 48000
CANALI = 2
BLOCCO_US = {1: 20000, 2: 5000}  # Opus 20 ms, PCM 5 ms (§5.3)


def giudica(campioni):
    """La frequenza dominante, l'ampiezza e la purezza.

    ⛔ «Niente da giudicare» e' un esito SUO e non uno zero: `CODER.md` §3.10.
    """
    m = len(campioni)
    if m == 0:
        return {"esito": "NIENTE DA GIUDICARE", "campioni": 0}
    rms = math.sqrt(sum(x * x for x in campioni) / m)
    picco, hz, somma = 0.0, 0, 0.0
    for f in range(100, 2001):
        w = 2.0 * math.cos(2.0 * math.pi * f / FREQUENZA)
        s1 = s2 = 0.0
        for x in campioni:
            s1, s2 = w * s1 - s2 + x, s1
        p = max(0.0, s1 * s1 + s2 * s2 - w * s1 * s2)
        somma += p
        if p > picco:
            picco, hz = p, f
    return {"esito": "GIUDICATO", "campioni": m, "hz": hz,
            "rms": round(rms, 4),
            "purezza": round(picco / somma, 4) if somma > 0 else None}


def pcm_campioni(dati):
    """s16 LITTLE-endian, interlacciati (§5.3) — si prende il canale sinistro.

    ⛔ Il little-endian e' l'unica eccezione dichiarata all'ordine di rete, e
       leggerlo big-endian NON da' un errore: da' rumore a fondo scala.  E'
       il caso 2 del controllo positivo di `07-b40`.
    """
    fuori = []
    for i in range(0, len(dati) - 3, 2 * CANALI):
        v = int.from_bytes(dati[i:i + 2], "little", signed=True)
        fuori.append(v / 32768.0)
    return fuori


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--hz", type=int, default=440, help="il tono atteso")
    p.add_argument("--tolleranza-hz", type=int, default=2)
    p.add_argument("--purezza-minima", type=float, default=0.80)
    p.add_argument("--secondi", type=float, default=0,
                   help="quanti secondi di parete e' durata la presa: senza, "
                        "il ritmo non si giudica (e si DICE che non si giudica)")
    a = p.parse_args()

    blocchi = []
    with open(a.file) as f:
        for riga in f:
            riga = riga.strip()
            if riga:
                blocchi.append(json.loads(riga))

    if not blocchi:
        print("⛔ NIENTE DA GIUDICARE: il file non ha blocchi.")
        print("   ⚠ E non e' «l'audio non arriva»: e' «non ho niente da")
        print("     guardare».  I due casi hanno due esiti diversi apposta.")
        return 2

    codec = blocchi[0]["codec"]
    if any(b["codec"] != codec for b in blocchi):
        print("⛔ il codec CAMBIA a meta' presa: §4.3 lo negozia una volta sola.")
        return 1

    # ── il RITMO, dagli `istante` del server ────────────────────────────────
    atteso_us = BLOCCO_US.get(codec)
    istanti = [b["istante"] for b in blocchi]
    salti, passi = [], []
    for i in range(1, len(istanti)):
        d = istanti[i] - istanti[i - 1]
        passi.append(d)
        if atteso_us and d != atteso_us:
            salti.append((i, d))
    durata_s = (istanti[-1] - istanti[0] + (atteso_us or 0)) / 1e6

    # ── il CONTENUTO ────────────────────────────────────────────────────────
    if codec == 2:
        campioni = []
        for b in blocchi:
            campioni.extend(pcm_campioni(base64.b64decode(b["byte"])))
        # ⚠ 100 ms d'innesco scartati: `CODER.md` §3.5, «un campione preso
        #   all'avvio non dice niente del regime».
        salta = min(4800, len(campioni) // 4)
        g = giudica(campioni[salta:])
    else:
        g = {"esito": "NON GIUDICABILE QUI",
             "perche": "i pacchetti Opus li giudica il BROWSER, che ha il "
                       "decodificatore: qui si giudicherebbe con uno diverso "
                       "da quello dell'utente (forma d'errore E10)"}

    print(f"== 07-b42 · {len(blocchi)} blocchi · codec {codec} "
          f"({'Opus' if codec == 1 else 'PCM'})")
    print(f"   durata secondo il SERVER: {durata_s:.3f} s")
    if a.secondi:
        resa = durata_s / a.secondi
        print(f"   parete: {a.secondi:.3f} s  ⇒  resa {resa * 100:.1f} %")
    else:
        print("   ⚠ il ritmo NON e' giudicato: manca `--secondi`, cioe' quanto "
              "e' durata la presa")
    print(f"   passo fra i blocchi: atteso {atteso_us} µs · "
          f"minimo {min(passi) if passi else '-'} · "
          f"massimo {max(passi) if passi else '-'} · fuori passo {len(salti)}")
    if salti[:5]:
        print(f"   i primi salti: {salti[:5]}")
    print(f"   giudizio del segnale: {json.dumps(g, ensure_ascii=False)}")

    # ── il VERDETTO, e ogni riga rossa nomina la sua regola ─────────────────
    rossi = []
    if g["esito"] == "GIUDICATO":
        if abs(g["hz"] - a.hz) > a.tolleranza_hz:
            rossi.append(f"la frequenza e' {g['hz']} Hz e non {a.hz}: "
                         f"§5.3 impone 48 000 Hz ai due capi")
        if g["purezza"] is None or g["purezza"] < a.purezza_minima:
            rossi.append(f"purezza {g['purezza']} sotto {a.purezza_minima}: "
                         f"non e' un tono, e' rumore — il difetto di v1")
        if g["rms"] < 0.05:
            rossi.append(f"ampiezza {g['rms']}: silenzio, o guadagno perduto")
    if salti:
        rossi.append(f"{len(salti)} passi fuori dai {atteso_us} µs di §5.3")
    if a.secondi and durata_s / a.secondi < 0.95:
        rossi.append(f"resa {durata_s / a.secondi * 100:.1f} %: il server NON "
                     f"produce l'audio in tempo reale")

    if rossi:
        print("\n⛔ ROSSO:")
        for r in rossi:
            print(f"   · {r}")
        return 1
    print("\n⭐ VERDE — e vale per quel che ha guardato: contenuto"
          + (" e ritmo" if a.secondi else ", NON il ritmo"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
