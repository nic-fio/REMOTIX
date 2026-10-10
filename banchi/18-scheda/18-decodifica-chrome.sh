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
#   table writes it as NOT TESTED.
set -u
FOLDER=${1:?folder with the *.bin streams and esiti.jsonl}; shift
PAGE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/18-decodifica-chrome.html
CHROME=${CHROME:-google-chrome}
PROFILE=$(mktemp -d)
trap 'rm -rf "$PROFILE"' EXIT
python3 - "$FOLDER/esiti.jsonl" <<'EOF' > "$PROFILE/items"
import json, sys
for r in open(sys.argv[1]):
    r = r.strip()
    if not r: continue
    e = json.loads(r)
    b = e.get("bench", {})
    print(e["prova"], e["version_v"], b.get("codec_string", ""))
EOF
while read -r prova version_v codec; do
	[ -n "$codec" ] || continue
	f="$FOLDER/$prova-$version_v.bin"
	[ -f "$f" ] || continue
	rm -rf "$PROFILE/p"
	row=$(timeout --foreground 90 "$CHROME" --headless=new --no-sandbox --user-data-dir="$PROFILE/p" \
		--allow-file-access-from-files --enable-logging=stderr --v=0 "$@" \
		"file://$PAGE?flow=file://$f&codec=$codec" 2>&1 \
		| grep -o 'OUTCOME {[^"]*"[^}]*}' | head -1)
	echo "$prova $version_v $codec ${row#OUTCOME }"
done < "$PROFILE/items" | tee "$FOLDER/chrome.txt"
# old against new: same decoded frames and same fingerprints?
python3 - "$FOLDER/chrome.txt" <<'EOF'
import json, sys
per = {}
for r in open(sys.argv[1]):
    parts = r.rstrip("\n").split(" ", 3)
    if len(parts) < 4 or not parts[3].startswith("{"): continue
    per.setdefault(parts[0], {})[parts[1]] = json.loads(parts[3].replace('\\"', '"'))
rossi = 0; passed = 0; untried = 0
for prova, v in sorted(per.items()):
    a, b = v.get("prior"), v.get("fresh")
    if not a or not b:
        print(f"FAIL {prova}: a version is missing"); rossi += 1; continue
    if not a.get("supported") and not b.get("supported"):
        print(f"NOT TESTED {prova}: Chrome does not decode {b.get('codec')} here (it needs the GPU)"); untried += 1; continue
    equal = a["decoded"] > 0 and a["decoded"] == b["decoded"] and a["fingerprints"] == b["fingerprints"] and not b["errors"]
    print(f"{'PASS' if equal else 'FAIL'} {prova}: old {a['decoded']}/{a['chunk']} new {b['decoded']}/{b['chunk']} · size {b.get('gauge')} · errors {b['errors']} · fingerprints {'equal' if a['fingerprints']==b['fingerprints'] else 'DIFFERENT'}")
    rossi += 0 if equal else 1
    passed += 1 if equal else 0
print(f"{passed} PASS · {rossi} FAIL · {untried} not tested")
sys.exit(1 if rossi else 0)
EOF
