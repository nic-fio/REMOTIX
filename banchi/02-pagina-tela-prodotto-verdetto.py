#!/usr/bin/env python3
"""02-pagina-tela-prodotto-verdetto.py — il verdetto sui casi del cambio di tela,
   calcolato FUORI dal browser.

    python3 banchi/02-pagina-tela-prodotto-verdetto.py <giro> [<giro> …]
    python3 …  <giro> --pretendi T5-ordine-prima-della-misura-av1=rosso

===========================================================================
⛔ PERCHE' IL CONFRONTO NON STA NELLA PAGINA

B0.4: *l'atteso lo confronta il banco, non chi legge* — e qui vale doppio,
perche' la pagina che misura gira **dentro** l'imputato, in un iframe della
stessa origine.  Un confronto fatto li' sarebbe d'accordo con il difetto.

⛔ E i casi con `errori_protocollo` attesi hanno un guasto apposta (`muto`) che
butta i testi: senza, «il prodotto ha rifiutato e ha detto perche'» e «il
prodotto ha rifiutato» sarebbero la stessa riga.
"""
import json
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "02-pagina-tela-esiti.jsonl"
VERDE = "\033[1;32mOK\033[0m"
ROSSO = "\033[1;31mNO\033[0m"
GIALLO = "\033[1;33m??\033[0m"


def carica(giri):
    per_giro = {g: [] for g in giri}
    if not REGISTRO.exists():
        print(f"{ROSSO}  {REGISTRO} non esiste", file=sys.stderr)
        return per_giro
    illeggibili = 0
    for riga in REGISTRO.open(encoding="utf-8"):
        riga = riga.strip()
        if not riga:
            continue
        try:
            d = json.loads(riga)
        except Exception:
            illeggibili += 1
            continue
        if d.get("giro") in per_giro:
            per_giro[d["giro"]].append(d)
    if illeggibili:
        print(f"    ⚠ {illeggibili} righe illeggibili nel registro, saltate")
    return per_giro


def stampa(giro, righe):
    print(f"\n\033[1m== giro {giro}\033[0m")
    if not righe:
        print(f"    {ROSSO}  nessuna riga: il browser non ha misurato niente")
        return {"casi": {}, "valido": False}
    print(f"    motore: {(righe[0].get('motore') or '')[:90]}")
    print(f"    scena:  {righe[0].get('scena') or 'NON DICHIARATA'}")
    guasto = righe[0].get("guasto") or ""
    if guasto:
        print(f"    ⚠ GUASTO INNESTATO: {guasto}")
    fin = next((d for d in righe if d.get("tipo") == "FINITO"), None)
    print(f"    fine: {(fin or {}).get('esito') or 'MANCA'}")

    # I due controlli del lettore: se cadono, dei casi non si scrive niente.
    controlli_ok = True
    for d in righe:
        if d.get("tipo") != "CONTROLLO":
            continue
        ok = d.get("p1_ok") and d.get("p2_ok")
        controlli_ok = controlli_ok and ok
        print(f"      {VERDE if ok else ROSSO}  P1/P2 a {d.get('misura')}: "
              f"dice si' {d.get('p1_corrette')}/{d.get('attese')} · dice no "
              f"{d.get('p2_corrette')}/{d.get('attese')}")

    print("\n    -- i casi, con l'atteso scritto PRIMA del giro")
    casi = {}
    for d in righe:
        if d.get("tipo") != "CASO":
            continue
        # ⛔ Un caso SALTATO non e' un caso verde: e' un caso che su questa
        #    scena non si poteva porre.  Metterlo fra i verdi farebbe leggere
        #    «28 casi verdi» dove i casi eseguiti erano diciannove.
        if d.get("saltato"):
            casi[d["caso"]] = "saltato"
            print(f"      {GIALLO}  {d['caso']}: SALTATO — {d.get('perche')}")
            continue
        atteso = d.get("atteso_scritto_prima") or {}
        visto = d.get("visto") or {}
        differenze = [k for k in atteso if atteso[k] != visto.get(k)]
        esito = "verde" if not differenze and not d.get("eccezione") else "rosso"
        casi[d["caso"]] = esito
        segno = VERDE if esito == "verde" else ROSSO
        print(f"      {segno}  {d['caso']}")
        if d.get("eccezione"):
            print(f"          ⛔ eccezione: {str(d['eccezione'])[:200]}")
        for k in differenze:
            print(f"          ⛔ {k}: atteso {atteso[k]!r}, visto "
                  f"{visto.get(k)!r}")
        if esito == "verde":
            interessanti = {k: visto[k] for k in
                            ("dipinti", "tollerati", "scartati_ordine",
                             "trattenuti", "errori_protocollo", "buchi",
                             "riconfigurazioni", "dec")
                            if k in visto}
            print(f"          {interessanti}")
        # ⛔ Il testo con cui il prodotto ha rifiutato si stampa: un rifiuto
        #    senza motivo e uno con il motivo sbagliato hanno lo stesso aspetto.
        for p in (d.get("protocolli") or [])[:1]:
            print(f"          -- il prodotto ha detto: {p[:160]}")

    valido = controlli_ok and bool(casi)
    if not valido:
        print(f"\n    {ROSSO}  BANCO NON VALIDO: i controlli del lettore non "
              "reggono, e dei casi non si scrive niente")
    return {"casi": casi, "valido": valido}


def principale(argomenti):
    pretese, giri, i = [], [], 0
    while i < len(argomenti):
        if argomenti[i] == "--pretendi":
            pretese.append(argomenti[i + 1]); i += 2; continue
        giri.append(argomenti[i]); i += 1
    if not giri:
        print(__doc__)
        return 2
    per_giro = carica(giri)
    esiti = {g: stampa(g, per_giro.get(g, [])) for g in giri}

    if pretese:
        print("\n\033[1m-- le pretese di questo giro (la certificazione)\033[0m")
        mancate = 0
        for p in pretese:
            nome, _, atteso = p.partition("=")
            visti = {e["casi"].get(nome, "assente") for e in esiti.values()}
            if visti == {atteso}:
                print(f"      {VERDE}  {nome} = {atteso}, come atteso")
            else:
                print(f"      {ROSSO}  {nome}: atteso «{atteso}», trovato "
                      f"{sorted(visti)}")
                mancate += 1
        return 1 if mancate else 0

    rossi = [n for e in esiti.values() for n, v in e["casi"].items() if v == "rosso"]
    saltati = [n for e in esiti.values() for n, v in e["casi"].items() if v == "saltato"]
    if saltati:
        print(f"    -- {len(saltati)} casi SALTATI: su questa scena il loro "
              "codec non arriva al pixel, e non si possono porre")
    validi = [g for g, e in esiti.items() if e["valido"]]
    print(f"\n    -- {len(rossi)} casi diversi dall'atteso su "
          f"{sum(len(e['casi']) for e in esiti.values())}, "
          f"{len(validi)} giri su {len(giri)} con banco valido")
    if not validi:
        return 1
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(principale(sys.argv[1:]))
