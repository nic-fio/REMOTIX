#!/bin/bash
# 18-decodifica-chrome.sh — headless Chrome (on the server, as a normal user)
# decodes with WebCodecs every stream of the matrix, old and new, and the two
# outcomes are put side by side: same decoded frames, same fingerprints.
#
#   bash 18-decodifica-chrome.sh /media/REMOTIX/src/f18-scheda/tmp/confronto [Chrome flags…]
#
# ⚠ The page writes the outcome with `console.log`, and it is read from Chrome's
#   log (`--enable-logging=stderr`): `--dump-dom` with virtual time waits
#   neither for the file fetch nor for the decoder.  Chrome stays open
#   until `timeout` closes it.
# ⚠ HEVC in Chrome exists ONLY in hardware: without the GPU `isConfigSupported`
#   says no for both versions, and a «0 = 0» is not a PASS — the
#   table writes it as NON PROVATO.
set -u
CARTELLA=${1:?folder with the *.bin streams and esiti.jsonl}; shift
PAGINA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/18-decodifica-chrome.html
CHROME=${CHROME:-google-chrome}
PROFILO=$(mktemp -d)
trap 'rm -rf "$PROFILO"' EXIT
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
	rm -rf "$PROFILO/p"
	riga=$(timeout --foreground 90 "$CHROME" --headless=new --no-sandbox --user-data-dir="$PROFILO/p" \
		--allow-file-access-from-files --enable-logging=stderr --v=0 "$@" \
		"file://$PAGINA?flusso=file://$f&codec=$codec" 2>&1 \
		| grep -o 'ESITO {[^"]*"[^}]*}' | head -1)
	echo "$prova $versione $codec ${riga#ESITO }"
done < "$PROFILO/lista" | tee "$CARTELLA/chrome.txt"
# old against new: same decoded frames and same fingerprints?
python3 - "$CARTELLA/chrome.txt" <<'EOF'
import json, sys
per = {}
for r in open(sys.argv[1]):
    parti = r.rstrip("\n").split(" ", 3)
    if len(parti) < 4 or not parti[3].startswith("{"): continue
    per.setdefault(parti[0], {})[parti[1]] = json.loads(parti[3].replace('\\"', '"'))
rossi = 0; passati = 0; non_provati = 0
for prova, v in sorted(per.items()):
    a, b = v.get("vecchio"), v.get("nuovo")
    if not a or not b:
        print(f"FAIL {prova}: a version is missing"); rossi += 1; continue
    if not a.get("supportato") and not b.get("supportato"):
        print(f"NON PROVATO {prova}: Chrome does not decode {b.get('codec')} here (it needs the GPU)"); non_provati += 1; continue
    uguali = a["decodificati"] > 0 and a["decodificati"] == b["decodificati"] and a["impronte"] == b["impronte"] and not b["errori"]
    print(f"{'PASS' if uguali else 'FAIL'} {prova}: old {a['decodificati']}/{a['chunk']} new {b['decodificati']}/{b['chunk']} · size {b.get('misura')} · errors {b['errori']} · fingerprints {'equal' if a['impronte']==b['impronte'] else 'DIFFERENT'}")
    rossi += 0 if uguali else 1
    passati += 1 if uguali else 0
print(f"{passati} PASS · {rossi} FAIL · {non_provati} not tested")
sys.exit(1 if rossi else 0)
EOF
