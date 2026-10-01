#!/bin/bash
# 19-android.sh — le prove Android della fase 19 (§5, §5.1) sul telefono VERO dell'utente,
# dal portatile.  Tutto il lavoro e' in 19-android.py; leggi LEGGIMI.md.
#
#   bash banchi/19-android/19-android.sh controlla
#   bash banchi/19-android/19-android.sh prova <1..10>|tutte [--desktop kde]
#   bash banchi/19-android/19-android.sh ripristina
#   bash banchi/19-android/19-android.sh a-secco
exec python3 "$(cd "$(dirname "$0")" && pwd)/19-android.py" "$@"
