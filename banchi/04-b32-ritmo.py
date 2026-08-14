#!/usr/bin/env python3
"""04-b32-ritmo.py — ⭐⭐ DOVE SI PERDE IL RITMO, contato in QUATTRO punti.

    python3 banchi/04-b32-ritmo.py [--secondi 30]

⛔ NASCE DA UNA TESI DEL MANDATO O2, E SERVE A REFUTARLA:

  > *«I 10,8 cambiamenti al secondo che l'utente ha misurato dal suo video non
  >  sono un limite nostro: sono quante volte Mutter ci consegna qualcosa.»*

⇒ Se e' vera, ottimizzare il nostro codice non sposta niente e va detto.
  ⛔ Ma «Mutter non consegna» e «noi non siamo li' a prendere» hanno **lo stesso
  aspetto** da fuori — ed e' gia' successo: `src/figlio.c:2669` porta la riga
  *«la tesi era falsa: Mutter aveva i fotogrammi, e noi non eravamo li' a
  prenderli»*, e la riga di registro che avrebbe dovuto smascherarlo accusava il
  compositore di un difetto nostro.

⭐ ⇒ Il ritmo si conta in QUATTRO punti della stessa catena, nella stessa
   finestra di tempo, e i quattro numeri si guardano in faccia:

     1. la SCENA disegna            (`disegni` nel suo blocco di stato)
     2. Mutter CONSEGNA a noi       (`ciclo: N fotogrammi consegnati`)
     2-bis. e quante volte abbiamo aspettato A VUOTO
                                    (`attese a vuoto` — ⛔ e' la riga che
                                     distingue «non consegna» da «non c'eravamo»)
     3. il server SPEDISCE sul filo (`fotogramma N SPEDITO`)
     4. la pagina DIPINGE           — ⚠ questo NON si legge da qui: lo misura
                                     `04-b30` (Q9, il ritmo con e senza lettura)

⛔ Perche' i due primi non bastano: se la scena disegna 58/s e Mutter ne
   consegna 33, il collo puo' essere di Mutter **oppure** nostro; ⭐ ma se le
   «attese a vuoto» sono ZERO vuol dire che ogni volta che abbiamo chiesto un
   fotogramma ce n'era uno pronto — cioe' **non stiamo aspettando Mutter**, e il
   limite e' a valle di lui.  ⚠ E se le attese a vuoto crescono, e' il contrario.

⚠ Precondizione: un client dev'essere ATTACCATO, o il ciclo dei fotogrammi non
  gira affatto e questo strumento misurerebbe una sessione ferma.  ⛔ Lo
  strumento se ne accorge (i conti non crescono) e lo DICE invece di stampare
  degli zeri.
"""
import argparse
import base64
import json
import os
import re
import struct
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}", flush=True)
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}", flush=True)
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}", flush=True)
def inf(t): print(f"    --  {t}", flush=True)
def log(t): print(f"\n\033[1m== {t}\033[0m", flush=True)


def sshpw(comando, attesa=200):
    return subprocess.run(["python3", os.path.join(RADICE, "v1/strumenti/sshpw.py"),
                           comando], capture_output=True, text=True, timeout=attesa)


def istantanea(a):
    """⛔ I quattro conti, letti IN UNA SOLA ANDATA.

    ⚠ Leggerli con tre `ssh` diversi vorrebbe dire tre istanti diversi, e a
      trenta fotogrammi al secondo tre secondi di scarto sono cento fotogrammi
      di errore su un conto che ne misura mille.
    """
    r = sshpw("sudo -S -p 'Password sudo: ' bash -c "
              "\"base64 -w0 /dev/shm/%s; echo; "
              "grep -a 'ciclo:' %s | tail -1; "
              "grep -ac 'SPEDITO' %s\"" % (a.shm, a.registro, a.registro))
    d = {"quando": time.time()}
    righe = [x.rstrip("\n") for x in (r.stdout or "").splitlines()]
    for x in righe:
        x = x.strip()
        if len(x) > 200 and re.fullmatch(r"[A-Za-z0-9+/=]+", x):
            try:
                b = base64.b64decode(x)
                # `disegni` sta a offset 24 del primo blocco (dopo magia,
                # versione, taglia, riempi0, seq)
                (d["disegni"],) = struct.unpack("<Q", b[24:32])
            except Exception:                        # noqa: BLE001
                pass
        m = re.search(r"ciclo: (\d+) fotogrammi consegnati \((\d+) chiavi\), "
                      r"(\d+) attese a vuoto", x)
        if m:
            d["consegnati"] = int(m.group(1))
            d["chiavi"] = int(m.group(2))
            d["attese_a_vuoto"] = int(m.group(3))
        if re.fullmatch(r"\d+", x):
            d["spediti"] = int(x)
    d["grezzo"] = righe[-3:]
    return d


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--secondi", type=float, default=30.0)
    p.add_argument("--shm", default="remotix-04-b30")
    p.add_argument("--registro", default="/media/REMOTIX/tmp/04-b30/registro.log")
    a = p.parse_args()

    log("⭐⭐ IL RITMO, contato in quattro punti della STESSA catena")
    inf("⛔ Precondizione: un client dev'essere attaccato, o il ciclo dei "
        "fotogrammi non gira e questi numeri sarebbero di una sessione ferma.")
    uno = istantanea(a)
    inf("t0: %s" % json.dumps({k: v for k, v in uno.items()
                               if k not in ("grezzo", "quando")}))
    time.sleep(a.secondi)
    due = istantanea(a)
    inf("t1: %s" % json.dumps({k: v for k, v in due.items()
                               if k not in ("grezzo", "quando")}))
    dt = due["quando"] - uno["quando"]

    def tasso(chiave):
        if chiave not in uno or chiave not in due:
            return None
        return (due[chiave] - uno[chiave]) / dt

    r = {"secondi": round(dt, 2),
         "1_la_scena_disegna": tasso("disegni"),
         "2_Mutter_consegna": tasso("consegnati"),
         "2bis_attese_a_vuoto": tasso("attese_a_vuoto"),
         "3_il_server_spedisce": tasso("spediti")}
    log("I QUATTRO NUMERI, al secondo")
    for k, val in r.items():
        if k == "secondi":
            continue
        (inf if val is not None else dub)(
            "%-24s %s" % (k, ("%.2f/s" % val) if val is not None
                          else "⛔ NON HO POTUTO GUARDARE"))
    if r["2_Mutter_consegna"] is None or r["1_la_scena_disegna"] is None:
        ko("⛔ non ho letto abbastanza: nessun verdetto")
        return 3
    if r["2_Mutter_consegna"] <= 0.1:
        ko("⛔ il ciclo dei fotogrammi NON GIRA (0 consegnati in %.0f s): "
           "nessun client attaccato, o il palco non c'e'.  ⚠ Questi numeri non "
           "dicono niente sul ritmo" % dt)
        return 3

    log("CHE COSA DICONO")
    quota = r["2_Mutter_consegna"] / max(r["1_la_scena_disegna"], 1e-9)
    inf("Mutter ci consegna il %.0f %% di quel che la scena disegna" % (quota * 100))
    if r["2bis_attese_a_vuoto"] is not None and r["2bis_attese_a_vuoto"] < 0.5:
        ok("⛔⭐ E LE ATTESE A VUOTO SONO ~ZERO (%.2f/s): ogni volta che abbiamo "
           "chiesto un fotogramma ce n'era uno pronto.  ⇒ **NON stiamo "
           "aspettando Mutter**: il limite sta a valle di lui, cioe' DENTRO IL "
           "NOSTRO CICLO.  ⚠ La tesi «e' Mutter che non consegna» non regge "
           "qui" % r["2bis_attese_a_vuoto"])
    else:
        ok("⭐ le attese a vuoto sono %.2f/s: stiamo davvero aspettando che "
           "Mutter consegni, e il limite e' SUO"
           % (r["2bis_attese_a_vuoto"] or 0.0))
    inf("⚠ E il quarto punto — quanti ne DIPINGE la pagina — non si legge da "
        "qui: lo misura `04-b30` (Q9).")
    print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
