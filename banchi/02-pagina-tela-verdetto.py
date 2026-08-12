#!/usr/bin/env python3
"""02-pagina-tela-verdetto.py — il verdetto sul cambio di tela, calcolato FUORI
dal browser.

    python3 banchi/02-pagina-tela-verdetto.py <giro> [<giro> …]
    python3 banchi/02-pagina-tela-verdetto.py --ultimi        gli ultimi 4 giri

⛔ PERCHE' IL VERDETTO NON LO DA' LA PAGINA

La pagina misura; chi misura non giudica.  E qui la separazione paga due volte:

 1. **«il banco funziona?» e «il buco esiste?» sono due domande diverse**, e
    questo programma non lascia che la seconda si legga senza la prima.  Se
    P1/P2 sono rossi il lettore e' cieco, e ogni «8 su 8» del giro vale zero;
    se il caso (a) e' rosso, la configurazione stessa non decodifica e su (b) e
    (c) **non si scrive niente**;

 2. ⛔ **un codec assente non e' un codec che sbaglia.**  `[M]` 12 ago 2026: su
    Firefox e su Xvfb `configure()` di HEVC lancia `NotSupportedError`.  Un
    programma che leggesse quei «NIENTE» come esiti del cambio di tela
    scriverebbe una regola di `RCP.md` su un motore che il codec non ce l'ha —
    la forma **E10**.  Qui quelle righe si marcano **NON MISURABILE QUI**, e
    non entrano in nessuna conclusione.

⛔ Lo stato d'uscita dice **se il banco vale**, non se il buco c'e': un caso
   rosso e' una misura, non un difetto del banco.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "02-pagina-tela-esiti.jsonl"

VERDE = "\033[1;32m"
ROSSO = "\033[1;31m"
GIALLO = "\033[1;33m"
FINE = "\033[0m"


def righe(giri):
    fuori = []
    if not REGISTRO.exists():
        return fuori
    for r in REGISTRO.open(encoding="utf-8"):
        try:
            d = json.loads(r)
        except Exception:
            continue
        if d.get("giro") in giri:
            fuori.append(d)
    return fuori


def motore_corto(ua):
    if not ua:
        return "?"
    if "Firefox/" in ua:
        return "Firefox " + ua.split("Firefox/")[1].split()[0]
    if "Chrome/" in ua:
        return "Chrome " + ua.split("Chrome/")[1].split()[0]
    return ua[:24]


def principale():
    argomenti = sys.argv[1:]
    if not argomenti:
        print("uso: 02-pagina-tela-verdetto.py <giro> …", file=sys.stderr)
        return 2
    if argomenti == ["--ultimi"]:
        visti = OrderedDict()
        for r in REGISTRO.open(encoding="utf-8"):
            try:
                visti[json.loads(r).get("giro")] = 1
            except Exception:
                pass
        argomenti = list(visti)[-4:]

    tutte = righe(set(argomenti))
    if not tutte:
        print(f"{ROSSO}NO{FINE}  nessuna riga per {argomenti}: il registro non "
              "porta questo giro, e «nessuna misura» non e' «misura negativa»")
        return 1

    guasto = {d.get("guasto") for d in tutte if d.get("guasto")}
    if guasto:
        print(f"{GIALLO}⚠  GUASTO INNESTATO: {', '.join(sorted(guasto))}{FINE}")

    esito_banco = 0
    for giro in argomenti:
        mie = [d for d in tutte if d.get("giro") == giro]
        if not mie:
            print(f"{ROSSO}NO{FINE}  {giro}: nessuna riga")
            esito_banco = 1
            continue
        motore = motore_corto(next((d.get("motore") for d in mie if d.get("motore")), None))
        scena = next((d.get("scena") for d in mie if d.get("scena")), "?")
        finito = next((d for d in mie if d.get("tipo") == "FINITO"), None)
        print(f"\n\033[1m== {giro}  ·  {motore}  ·  scena {scena}{FINE}")
        if not finito or finito.get("esito") != "COMPLETO":
            print(f"   {ROSSO}NO{FINE}  il giro non e' COMPLETO "
                  f"({finito.get('esito') if finito else 'nessun FINITO'}): "
                  "le righe qui sotto sono un giro a meta'")
            esito_banco = 1

        # --- I controlli del lettore -------------------------------------
        controlli = [d for d in mie if d.get("tipo") == "CONTROLLO"]
        lettore_ok = True
        for d in [x for x in controlli if x.get("prova") == "P1-P2"]:
            buono = d.get("p1_ok") and d.get("p2_ok")
            lettore_ok = lettore_ok and buono
            print(f"   {'OK ' if buono else ROSSO + 'NO ' + FINE}P1/P2 a "
                  f"{d['misura']}: dice SI' {d['p1_corrette']}/{d['attese']} · "
                  f"dice NO {d['p2_corrette']}/{d['attese']}")
        if not lettore_ok:
            print(f"   {ROSSO}⛔ il lettore e' cieco: ogni «8 su 8» di questo "
                  f"giro vale zero{FINE}")
            esito_banco = 1

        casi = [d for d in mie if d.get("tipo") == "CASO"]
        for famiglia in ("hevc", "av1"):
            print(f"\n   ── {famiglia.upper()}")
            miei = [d for d in casi if d.get("famiglia") == famiglia]
            if not miei:
                print(f"      {ROSSO}NO{FINE}  nessun caso per {famiglia}")
                esito_banco = 1
                continue
            # ⛔ Il caso (a) e' il controllo positivo DENTRO questa
            #    configurazione: se non dipinge, il codec qui non c'e'.
            a = next((d for d in miei if d["caso"].startswith("a-controllo")), None)
            disponibile = bool(a and a["prima"]["celle_giuste"]
                               == a["prima"]["celle_attese"])
            if not disponibile:
                motivo = (a["prima"].get("errore_configure") if a else None) \
                         or "nessun pixel dipinto"
                print(f"      {GIALLO}⚠ NON MISURABILE QUI{FINE}: il controllo "
                      f"positivo (a) non dipinge — {str(motivo)[:90]}")
                print(f"      ⇒ i «NIENTE» di sotto sono del CODEC ASSENTE, non "
                      f"del cambio di tela.  Non entrano in nessuna conclusione "
                      f"(forma E10).")
            for d in miei:
                p7 = None
                esito = d["esito"]
                colore = VERDE if esito.startswith("GIUSTI") else (
                    ROSSO if d.get("spazzatura_in_silenzio") else GIALLO)
                dopo = d.get("dopo")
                coda = ""
                if dopo:
                    coda = (f" nuova {dopo['celle_giuste_misura_NUOVA']}/"
                            f"{dopo['celle_attese_nuova']}"
                            f" vecchia {dopo['celle_giuste_misura_VECCHIA']}/"
                            f"{dopo['celle_attese_vecchia']}"
                            f" fot {dopo['fotogrammi']}"
                            f" {dopo['misure_dei_fotogrammi'] or ''}")
                    voci = list(dopo.get("errori") or [])
                    if dopo.get("errore_configure"):
                        voci.append("configure: " + dopo["errore_configure"])
                    if voci:
                        coda += "  ⛔ " + " | ".join(v[:110] for v in voci)
                marca = "" if disponibile else f"{GIALLO}[non misurabile]{FINE} "
                print(f"      {marca}{colore}{esito:18s}{FINE} "
                      f"{d['caso']:38s}{coda}")
                if disponibile and d.get("spazzatura_in_silenzio"):
                    print(f"         {ROSSO}⛔⛔ SPAZZATURA IN SILENZIO: ha "
                          f"dipinto qualcosa che non e' l'immagine attesa, e "
                          f"NESSUNO l'ha detto.  E' la forma di P6.{FINE}")
            for d in [x for x in controlli if x.get("famiglia") == famiglia]:
                col = VERDE if d["esito"].startswith("GIUSTI") else GIALLO
                voci = list(d.get("errori") or [])
                if d.get("errore_configure"):
                    voci.append("configure: " + d["errore_configure"])
                print(f"      {col}{d['esito']:18s}{FINE} {d['prova']:38s}"
                      f" celle {d['celle_giuste']}/{d['celle_attese']}"
                      + ("  ⛔ " + " | ".join(v[:110] for v in voci) if voci else ""))
            # ⛔ P7 e' il controllo che protegge i casi (b): se il flusso
            #    piccolo, da solo, non dipinge, un rosso su (b) non e' del
            #    cambio di tela.
            p7 = next((x for x in controlli
                       if x.get("prova", "").startswith("P7") and
                       x.get("famiglia") == famiglia), None)
            if disponibile and p7 and not p7["esito"].startswith("GIUSTI"):
                print(f"      {ROSSO}⛔ P7 rosso: il flusso piccolo non dipinge "
                      f"nemmeno da solo ⇒ un rosso sui casi (b) NON e' del "
                      f"cambio di tela, e su (b) non si scrive niente{FINE}")
                esito_banco = 1

    print()
    if esito_banco == 0:
        print(f"   {VERDE}OK{FINE}  il banco e' valido: i suoi numeri si possono "
              "leggere")
    else:
        print(f"   {ROSSO}NO{FINE}  il banco NON e' valido in qualche punto: "
              "vedi sopra")
    print("   ⚠ Un caso rosso e' una MISURA, non un difetto del banco: lo stato "
          "d'uscita dice se il banco vale.")
    return esito_banco


if __name__ == "__main__":
    sys.exit(principale())
