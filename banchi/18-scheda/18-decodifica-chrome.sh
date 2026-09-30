#!/bin/bash
# 18-decodifica-chrome.sh — Chrome headless (sul server, come utente normale)
# decodifica con WebCodecs ogni flusso della matrice, vecchio e nuovo, e i due
# esiti si mettono in colonna: stessi fotogrammi decodificati, stesse impronte.
#
#   bash 18-decodifica-chrome.sh /media/REMOTIX/src/f18-scheda/tmp/confronto
set -u
CARTELLA=${1:?cartella con i flussi *.bin e esiti.jsonl}
PAGINA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/18-decodifica-chrome.html
CHROME=${CHROME:-google-chrome}
PROFILO=$(mktemp -d)
trap 'rm -rf "$PROFILO"' EXIT
esito=0
python3 - "$CARTELLA/esiti.jsonl" <<'EOF' > "$PROFILO/lista"
import json, sys
for r in open(sys.argv[1]):
    r = r.strip()
    if not r: continue
    e = json.loads(r)
    b = e.get("banco", {})
    print(e["prova"], e["versione"], b.get("stringa_codec", ""))
EOF
while read -r prova versione codec; do
	[ -n "$codec" ] || continue
	f="$CARTELLA/$prova-$versione.bin"
	[ -f "$f" ] || continue
	riga=$("$CHROME" --headless=new --disable-gpu --no-sandbox --user-data-dir="$PROFILO/p" \
		--allow-file-access-from-files --virtual-time-budget=90000 --dump-dom \
		"file://$PAGINA?flusso=file://$f&codec=$codec" 2>/dev/null | grep -o 'ESITO {.*}' | head -1)
	echo "$prova $versione $codec ${riga#ESITO }"
done < "$PROFILO/lista" | tee "$CARTELLA/chrome.txt"
# vecchio contro nuovo: stessi decodificati e stesse impronte?
python3 - "$CARTELLA/chrome.txt" <<'EOF'
import json, sys
per = {}
for r in open(sys.argv[1]):
    parti = r.rstrip("\n").split(" ", 3)
    if len(parti) < 4 or not parti[3].startswith("{"): continue
    per.setdefault(parti[0], {})[parti[1]] = json.loads(parti[3])
rossi = 0
for prova, v in sorted(per.items()):
    a, b = v.get("vecchio"), v.get("nuovo")
    if not a or not b:
        print(f"{prova}: manca una versione"); rossi += 1; continue
    uguali = a["decodificati"] == b["decodificati"] and a["impronte"] == b["impronte"] and not b["errori"]
    print(f"{'PASS' if uguali else 'FAIL'} {prova}: vecchio {a['decodificati']}/{a['chunk']} nuovo {b['decodificati']}/{b['chunk']} · misura {b.get('misura')} · errori {b['errori']} · impronte {'uguali' if a['impronte']==b['impronte'] else 'DIVERSE'}")
    rossi += 0 if uguali else 1
print(f"{'⭐ Chrome decodifica i nuovi come i vecchi' if not rossi else '⛔ ' + str(rossi) + ' prove diverse'}")
sys.exit(1 if rossi else 0)
EOF
