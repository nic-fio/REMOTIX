#!/bin/bash
# 19-android.sh — the Android tests of phase 19 (§5, §5.1) on the user's REAL phone,
# from the laptop.  All the work is in 19-android.py; read LEGGIMI.md.
#
#   bash banchi/19-android/19-android.sh controlla
#   bash banchi/19-android/19-android.sh prova <1..10>|tutte [--desktop kde]
#   bash banchi/19-android/19-android.sh ripristina
#   bash banchi/19-android/19-android.sh a-secco
exec python3 "$(cd "$(dirname "$0")" && pwd)/19-android.py" "$@"
