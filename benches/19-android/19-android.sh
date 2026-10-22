#!/bin/bash
# 19-android.sh — the Android tests of phase 19 (§5, §5.1) on the user's REAL phone,
# from the laptop.  All the work is in 19-android.py; read README.md.
#
#   bash benches/19-android/19-android.sh check
#   bash benches/19-android/19-android.sh test <1..10>|all [--desktop kde]
#   bash benches/19-android/19-android.sh restore
#   bash benches/19-android/19-android.sh dry-run
exec python3 "$(cd "$(dirname "$0")" && pwd)/19-android.py" "$@"
