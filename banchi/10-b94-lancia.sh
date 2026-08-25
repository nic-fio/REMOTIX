#!/bin/bash
# 10-b94-lancia — la sequenza dello STUDIO DEL FERRO (fase 10, agente A10).
#
# ⛔⛔ Ogni passo che produce un numero vuole il LUCCHETTO DELLA GPU in mano:
#     questo script NON lo prende — lo prende chi lo lancia, così:
#
#       LUCCHETTO=/media/REMOTIX/tmp/.lucchetto-gpu.d \
#       python3 - <<'FINE'
#       import importlib.util, os
#       spec = importlib.util.spec_from_file_location("luc", "banchi/09-lucchetto.py")
#       luc = importlib.util.module_from_spec(spec); spec.loader.exec_module(luc)
#       luc.prendi("10-a10", secondi=2700, attesa=21600)
#       try:    os.system("ssh nicfio@192.168.0.2 'cd LAV && bash 10-b94-lancia.sh'")
#       finally: luc.molla("10-a10")
#       FINE
#
# ⚠ Il metro dei motori (PMU di i915) vuole i privilegi di root: il banco lancia
#   da sé un sottoprocesso `sudo` e la parola passa sullo stdin, mai in argv.
#
# Si lavora in /media/REMOTIX/tmp/10a10 sulla macchina di prova.  ⛔ Solo
# `renderD128`: la Radeon `renderD129` è chiusa apposta (DECISIONI.md §4.6-quinquies).
set -u
LAV="${LAV:-/media/REMOTIX/tmp/10a10}"
cd "$LAV"
V=10-b94-ferro-vaapi.py
B=10-b94-ferro-carico.py

echo "═══ 0 · CERTIFICAZIONE DEI DUE BANCHI (⛔ senza questa i numeri valgono zero)"
python3 $V --certifica
python3 $B --certifica

echo "═══ 1 · CHE COSA IL DRIVER DICHIARA  (non serve il lucchetto)"
python3 $V dichiara
python3 $V obbedisce

echo "═══ 2 · QUANTI CONTESTI SI APRONO"
python3 $V contesti --gradini 1,2,4,8,16,32,64,128,256,512,1024,2048
python3 $V contesti --processi-separati --gradini 8,64,256,1024
python3 $B memoria

echo "═══ 3 · LA TARATURA DEI TRE METRI (⛔ prima dei numeri, LEZIONI §1.33)"
python3 $B taratura

echo "═══ 4 · CHE COSA CAMBIA SOTTO CARICO: 1 / 4 / 8 a parità di richiesta"
python3 $B confronto --gradini 1,4,8 --fotogrammi 3000

echo "═══ 5 · IL GIRO LUNGO — frequenza e termico (⚠ LEZIONI §1.32: due durate)"
python3 $B lungo --minuti 12 --codifiche 8
