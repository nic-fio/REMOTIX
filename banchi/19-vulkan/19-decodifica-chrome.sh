#!/bin/bash
# 19-decodifica-chrome.sh — headless Chrome (on the server, as a normal user)
# decodes with WebCodecs every stream of the matrix, VA-API and Vulkan, and the two
# outcomes are put side by side: same decoded frames, same fingerprints.
#
#   bash 19-decodifica-chrome.sh /media/REMOTIX/src/f19-vulkan/tmp/comparison [Chrome flags…]
#
# ⚠ The page writes the outcome with `console.log`, and it is read from Chrome's
#   log (`--enable-logging=stderr`): `--dump-dom` with virtual time does not
#   wait for either the file fetch or the decoder.  Chrome stays open
#   until `timeout` closes it.
# ⚠ HEVC in Chrome exists ONLY in hardware: without the GPU `isConfigSupported`
#   says no for both versions, and a "0 = 0" is not a PASS — the
#   table writes it as NOT TESTED.
set -u
FOLDER=${1:?folder with the *.bin streams and esiti.jsonl}; shift
PAGE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../18-scheda/18-decodifica-chrome.html
CHROME=${CHROME:-google-chrome}
PROFILE=$(mktemp -d)
trap 'rm -rf "$PROFILO"' EXIT
python3 - "$FOLDER/esiti.jsonl" <<'EOF' > "$PROFILE/lista"
import json, sys
for r in open(sys.argv[1]):
    r = r.strip()
    if not r: continue
    e = json.loads(r)
    b = e.get("bench", {})
    print(e["prova"], e["version"], b.get("codec_string", ""))
EOF
while read -r prova version codec; do
	[ -n "$codec" ] || continue
	f="$FOLDER/$prova-$version.bin"
	[ -f "$f" ] || continue
	rm -rf "$PROFILE/p"
	line=$(timeout --foreground 90 "$CHROME" --headless=new --no-sandbox --user-data-dir="$PROFILE/p" \
		--allow-file-access-from-files --enable-logging=stderr --v=0 "$@" \
		"file://$PAGE?stream=file://$f&codec=$codec" 2>&1 \
		| grep -o 'ESITO {[^"]*"[^}]*}' | head -1)
	echo "$prova $version $codec ${line#ESITO }"
done < "$PROFILE/lista" | tee "$FOLDER/chrome.txt"
# VA-API against Vulkan: same decoded?  (DIFFERENT fingerprints are expected here: two different encoders)
python3 - "$FOLDER/chrome.txt" <<'EOF'
import json, sys
per = {}
for r in open(sys.argv[1]):
    parti = r.rstrip("\n").split(" ", 3)
    if len(parti) < 4 or not parti[3].startswith("{"): continue
    per.setdefault(parti[0], {})[parti[1]] = json.loads(parti[3].replace('\\"', '"'))
rossi = 0; passati = 0; non_provati = 0
for prova, v in sorted(per.items()):
    a, b = v.get("vaapi"), v.get("vulkan")
    if not a or not b:
        print(f"FAIL {prova}: one version is missing"); rossi += 1; continue
    if not a.get("supported") and not b.get("supported"):
        print(f"NOT TESTED {prova}: Chrome does not decode {b.get('codec')} here (the GPU is needed)"); non_provati += 1; continue
    uguali = a["decoded"] > 0 and a["decoded"] == b["decoded"] and not b["errors"] and b.get("supported")
    print(f"{'PASS' if uguali else 'FAIL'} {prova}: vaapi {a['decoded']}/{a['chunk']} vulkan {b['decoded']}/{b['chunk']} · size {b.get('size')} · errors {b['errors']} · fingerprints {'equal' if a['fingerprints']==b['fingerprints'] else 'DIFFERENT'}")
    rossi += 0 if uguali else 1
    passati += 1 if uguali else 0
print(f"{passati} PASS · {rossi} FAIL · {non_provati} not tested")
sys.exit(1 if rossi else 0)
EOF
