#!/usr/bin/env python3
"""03-deposita.py — scrive nel DEPOSITO l'esito di uno strumento del metro.

    python3 03-deposita.py <esiti.jsonl> <giro> <marca> <atteso> <json…>

⛔ PERCHE' ESISTE, E NON E' UNA COMODITA'

La cartella di lavoro di `03-scena-certifica.sh` sta in `/tmp`, e su questa
macchina il rootfs **vive in RAM e si azzera al riavvio** (`LEZIONI.md`
§2.5-bis).  ⇒ se l'esito di M6 e del `giro` di M8 restasse solo li', dopo un
riavvio resterebbe **il ricordo che «erano verdi»** e non i numeri: ed e'
esattamente il tipo di riga che un documento si porta dietro per settimane
senza piu' niente sotto.

⚠ E la riga porta con se' **il limite della catena**, non solo il verdetto: un
esito depositato senza dire su che cosa e' stato misurato e' un verdetto che
domani verra' letto come se valesse sulla catena del prodotto.
"""
import datetime
import json
import sys

CATENA = ("⛔ scena dipinta da 03-scena.c → libx265 Main10 QP 40 → ffmpeg.  "
          "NON e' la catena del prodotto: manca la cattura PipeWire di Mutter "
          "e manca la tela del browser riletta.  ⇒ quel che e' dimostrato e' "
          "che lo STRUMENTO e' vivo, non che la catena vera lo conservi")


def main():
    if len(sys.argv) < 6:
        print("uso: 03-deposita.py <esiti> <giro> <marca> <atteso> <json…>",
              file=sys.stderr)
        return 2
    esiti, giro, marca, atteso = sys.argv[1:5]
    pezzi = [x for x in sys.argv[5:] if x.strip()]
    giri = []
    for x in pezzi:
        try:
            giri.append(json.loads(x))
        except Exception as e:                   # noqa: BLE001
            # ⛔ Un pezzo illeggibile NON si butta in silenzio: si deposita
            #    dicendo che non si e' letto.  Un deposito con un giro in meno
            #    e nessuna riga che lo dica e' un conto gonfiato al contrario.
            giri.append({"⛔ non si e' letto": str(e), "grezzo": x[:300]})
    r = {"ora": datetime.datetime.now().isoformat(timespec="seconds"),
         "strumento": "03-scena-certifica.sh", "giro": giro, "marca": marca,
         "atteso": atteso, "metro": "02-giudizio-metro.py",
         "catena": CATENA, "quanti_giri": len(giri), "giri": giri}
    with open(esiti, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("        deposito → %s (%s, %d giri)" % (esiti, marca, len(giri)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
