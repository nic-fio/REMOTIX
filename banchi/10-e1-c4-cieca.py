#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-e1-c4-cieca — ⭐ `10-b96-registro.py` sull'albero CUCITO, con **TRE** utenti.

    porta 8310 · utenti provadec4/5/6 · albero /media/REMOTIX/src/10e1-src
    lavoro /media/REMOTIX/tmp/10e1 · unita' remotix-8310 · lucchetto `10-e1`

═══════════════════════════════════════════════════════════════════════════
⛔⛔ PERCHE' TRE E NON QUATTRO — e non e' una comodita', e' un vincolo
═══════════════════════════════════════════════════════════════════════════

`10-b96-registro.py` apre **quattro** sessioni: `provadec4/5/6` e `provamt1`,
tutte con **una parola sola**, perche' il cliente la legge da `$LAV/parola` e il
file e' uno.  ⛔ Ma su questa macchina le parole sono **due**:

    provadec4/5/6 → `dec-pieno-2026`   (l'ha posata `10-c3-terreno.sh`)
    provamt1      → `mt-dieci-2026`    (l'ha posata `10-b91-terreno-dieci.sh`)

`[M]` 25 agosto 2026, verificato con **un tentativo solo** (`10-e1-parola.sh`):
`mt-dieci-2026` su `provadec4` da' `CONGEDO 0x07 CREDENZIALI_ERRATE`.

⇒ Le due strade sarebbero: **rifare** la parola a uno dei due gruppi — ⛔ e
  l'incarico lo vieta, perche' la ruberebbe a chi sta misurando adesso e ogni
  respinto consuma uno dei tre tentativi del ban per INDIRIZZO — oppure
  **misurare con tre**.  ⭐ Si misura con tre, e si dichiara.

⚠ E IL PREZZO SI DICHIARA: la prova cieca diventa **3 su 3** invece di 4 su 4, e
  il campione delle righe e' piu' piccolo di un quarto.  ⛔ Quel che NON cambia
  e' la domanda: *«spengo una scena, il registro sa dirmi CHI si e' fermato?»* —
  con tre inquilini si puo' ancora sbagliare bersaglio in due modi su tre.

⛔ E non si riscrive una riga del banco: si importa, si restringe la lista, e si
   chiama la sua `principale()`.  Il suo `--certifica` (31/31) resta valido: qui
   non si tocca nessun predicato.

Uso:
    python3 banchi/10-e1-c4-cieca.py [altre opzioni di 10-b96-registro.py]
"""
import importlib.util
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))

os.environ.setdefault("PORTA", "8310")
os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10e1")
os.environ.setdefault("ALBERO", "/media/REMOTIX/src/10e1-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10e1-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10e1")
os.environ.setdefault("UNITA", "remotix-8310")
os.environ.setdefault("IO_SONO", "10-e1")
os.environ.setdefault("FUORI", "/tmp/10-e1")

_s = importlib.util.spec_from_file_location(
    "b96", os.path.join(QUI, "10-b96-registro.py"))
B96 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B96)

# ⛔ I tre che condividono DAVVERO la parola, e nell'ordine del banco.
B96.SESSIONI = [s for s in B96.SESSIONI if s[0] != "provamt1"]
B96.QUANTI = len(B96.SESSIONI)

if __name__ == "__main__":
    print("⚠ TRE sessioni (%s) invece di quattro: «provamt1» ha un'altra "
          "parola d'ordine e questo giro NON la rifa'."
          % " ".join(u for u, _n, _m, _d in B96.SESSIONI))
    sys.argv = [sys.argv[0]] + sys.argv[1:] + ["--prove", str(B96.QUANTI)]
    sys.exit(B96.principale())
