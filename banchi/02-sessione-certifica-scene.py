#!/usr/bin/env python3
"""02-sessione-certifica-scene.py — la seconda meta' della certificazione di
F2.1: gli OTTO stati dello strumento, uno per uno, e ciascuno col suo caso
opposto.

  python3 02-sessione-certifica-scene.py --base 02-sessione-scene/sana.json

===========================================================================
⛔ PERCHE' ESISTE, VISTO CHE `02-sessione-lancia.sh certifica` GIA' CERTIFICA
===========================================================================

`02-sessione-lancia.sh certifica` fa il ciclo **sul ferro**: sano 0 → guasto 1
→ risanato 0, con la sessione vera fermata e riavviata tre volte.  E' la
certificazione che conta di piu', ed e' anche l'unica che dimostra che lo
strumento sa parlare con una macchina.

⛔ Ma copre **due** degli otto numeri d'uscita.  Gli altri sei si otterrebbero
solo rompendo la macchina in sei modi diversi — e tre di quei modi (la lettura
negata, il monitor che Mutter si sceglie da se', la SHELL non vuota) non si
innestano senza lasciare addosso alla macchina qualcosa che poi va tolto.

⇒ Qui gli stessi otto stati si innestano **sulla scena**, non sulla macchina.

⛔ E LA COSA CHE VA DETTA SUBITO, perche' altrimenti questo file mente: una
   scena costruita a mano NON prova che lo strumento legga bene una macchina.
   Prova solo che il GIUDIZIO — la funzione che dalla scena tira fuori il
   numero — non sbaglia.  Le due meta' insieme fanno una certificazione; da
   sola, nessuna delle due basta.  (`REVIEWER.md` §1 punti 2 e 3.)

⭐ Per questo la scena di partenza **non e' inventata**: e' `sana.json`,
   registrata dalla sessione vera di NIC-OS il 12 agosto 2026, e ogni guasto
   cambia UNA cosa sola a partire da li'.  Chi legge vede esattamente che cosa
   e' stato toccato.
"""

import argparse
import copy
import json
import subprocess
import sys
import os

VERDE, ROSSO, FINE = "\033[1;32m", "\033[1;31m", "\033[0m"

# ⛔ GLI ATTESI, SCRITTI PRIMA DEL GIRO — nome, che cosa si cambia rispetto
#    alla scena vera, uscita attesa, marca attesa.
def guasti(base):
    def con(f):
        s = copy.deepcopy(base)
        f(s)
        return s

    def togli_monitor(s):
        s["display"]["monitor"] = []
        s["display"]["logici"] = 0
        s["shell_riga"] = [a for a in s["shell_riga"]
                           if not a.startswith("--virtual-monitor")
                           and not a[0].isdigit()]

    def cambia_misura(s):
        s["display"]["monitor"][0]["modo_corrente"]["larghezza"] = 1280
        s["display"]["monitor"][0]["modo_corrente"]["altezza"] = 720

    def scelto_da_se(s):
        s["display"]["monitor"][0]["prodotto"] = "Virtual remote monitor"
        s["display"]["monitor"][0]["seriale"] = "0x000001"

    def due_monitor(s):
        s["display"]["monitor"].append(copy.deepcopy(s["display"]["monitor"][0]))
        s["display"]["logici"] = 2

    def morta(s):
        s["shell_pid"] = []
        s["shell_riga"] = None
        s["sessione_gira"] = False

    def negata(s):
        s["ignote"].append("non leggo /proc/1234/cmdline: [Errno 13] Permission denied")

    def shell_piena(s):
        s["shell_var"] = "/bin/bash"
        s["shell_var_presente"] = True

    def disaccordo(s):
        # ⛔ IL DISACCORDO PURO, e trovarne uno costa: dev'essere un caso in cui
        #    la riga di comando e il bus non dicono lo stesso E NIENTE di piu'
        #    preciso regge, o il verdicto giusto e' l'altro.  Qui il monitor sul
        #    bus e' esattamente quello chiesto — ma la riga di comando non lo
        #    chiede: qualcuno l'ha messo per un'altra strada.
        s["shell_riga"] = [a for a in s["shell_riga"]
                           if not a.startswith("--virtual-monitor")
                           and not a[0].isdigit()]

    return [
        # nome                    che cosa cambia          atteso  marca attesa
        ("zero-monitor",          togli_monitor,  1, "NERA: ZERO MONITOR"),
        ("misura-1280x720",       cambia_misura,  2, "MISURA SBAGLIATA"),
        ("scelto-da-se",          scelto_da_se,   3, "MONITOR SCELTO DA SE"),
        ("due-monitor",           due_monitor,    3, "MONITOR SCELTO DA SE"),
        ("sessione-morta",        morta,          4, "SESSIONE MORTA"),
        ("lettura-negata",        negata,         5, "LETTURA IGNOTA"),
        ("shell-non-vuota",       shell_piena,    7, "SHELL NON VUOTA"),
        ("disaccordo",            disaccordo,     6, "DISACCORDO"),
    ], con


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True,
                   help="la scena SANA registrata da una macchina vera")
    p.add_argument("--strumento", default=None)
    p.add_argument("--attesa", default="1920x1080")
    p.add_argument("--tmp", default="/tmp/f21-scene-finte")
    a = p.parse_args()
    strumento = a.strumento or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "02-sessione-stato.py")

    with open(a.base) as f:
        base = json.load(f)
    print(f"\n\033[1m== La scena di partenza, e non e' inventata{FINE}")
    print(f"    --  {a.base}, registrata il {base.get('quando')} su "
          f"{base.get('macchina')}")
    os.makedirs(a.tmp, exist_ok=True)

    elenco, con = guasti(base)

    print(f"\n\033[1m== Gli attesi, SCRITTI PRIMA del giro{FINE}")
    print("    --  sano: 0 (SANA)")
    for nome, _, atteso, marca in elenco:
        print(f"    --  {nome:22s} → {atteso}  «{marca}»")

    falle = 0

    def giro(nome, scena, atteso, marca):
        nonlocal falle
        percorso = os.path.join(a.tmp, nome + ".json")
        with open(percorso, "w") as f:
            json.dump(scena, f, indent=1, ensure_ascii=False)
        e = subprocess.run([sys.executable, strumento, "--attesa", a.attesa,
                            "--da-scena", percorso, "--etichetta", "finta-" + nome],
                           capture_output=True, text=True)
        uscita = e.returncode
        # ⛔ Non basta che il numero torni: la marca dev'essere QUELLA, o il
        #    banco e' rosso per un'altra ragione e non ha certificato niente.
        marca_c = f"uscita {uscita} — {marca}" in e.stdout
        if uscita == atteso and marca_c:
            print(f"    {VERDE}OK{FINE}  {nome:22s} → {uscita} «{marca}»")
        else:
            print(f"    {ROSSO}NO{FINE}  {nome:22s} → {uscita} "
                  f"(atteso {atteso}), marca giusta: {marca_c}")
            print("        " + "\n        ".join(e.stdout.strip().splitlines()[-8:]))
            falle += 1

    print(f"\n\033[1m== Il giro SANO — la scena vera, non toccata{FINE}")
    giro("sano", base, 0, "SANA")

    print(f"\n\033[1m== Gli otto guasti, uno per volta{FINE}")
    for nome, f, atteso, marca in elenco:
        giro(nome, con(f), atteso, marca)

    print(f"\n\033[1m== Il verdetto{FINE}")
    if falle == 0:
        print(f"    {VERDE}⭐ IL GIUDIZIO DI F2.1 E' CERTIFICATO su 9 scene: "
              f"il sano e otto guasti, ciascuno nel suo punto{FINE}")
        print("    --  ⛔ e questo NON dice che lo strumento sappia leggere una")
        print("        macchina: quella meta' la fa `02-sessione-lancia.sh certifica`,")
        print("        sul ferro, e le due meta' non si sostituiscono a vicenda.")
        return 0
    print(f"    {ROSSO}⛔ NON certificato: {falle} scene su 9 non tornano{FINE}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
