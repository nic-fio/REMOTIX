#!/bin/bash
# 19-decodifica-chrome.sh — Chrome headless (sul server, come utente normale)
# decodifica con WebCodecs ogni flusso della matrice, VA-API e Vulkan, e i due
# esiti si mettono in colonna: stessi fotogrammi decodificati, stesse impronte.
#
#   bash 19-decodifica-chrome.sh /media/REMOTIX/src/f19-vulkan/tmp/confronto [flag di Chrome…]
#
# ⚠ La pagina scrive l'esito con `console.log`, e lo si legge dal registro di
#   Chrome (`--enable-logging=stderr`): `--dump-dom` col tempo virtuale non
#   aspetta ne' il fetch del file ne' il decodificatore.  Chrome resta aperto
#   finche' non lo chiude `timeout`.
# ⚠ HEVC in Chrome esiste SOLO in hardware: senza la GPU `isConfigSupported`
#   dice no per tutt'e due le versioni, e un «0 = 0» non e' un PASS — la
#   tabella lo scrive come NON PROVATO.
set -u
CARTELLA=${1:?cartella con i flussi *.bin e esiti.jsonl}; shift
PAGINA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../18-scheda/18-decodifica-chrome.html
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
# VA-API contro Vulkan: stessi decodificati?  (le impronte DIVERSE qui sono attese: due codificatori diversi)
python3 - "$CARTELLA/chrome.txt" <<'EOF'
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
        print(f"FAIL {prova}: manca una versione"); rossi += 1; continue
    if not a.get("supportato") and not b.get("supportato"):
        print(f"NON PROVATO {prova}: Chrome non decodifica {b.get('codec')} qui (serve la GPU)"); non_provati += 1; continue
    uguali = a["decodificati"] > 0 and a["decodificati"] == b["decodificati"] and not b["errori"] and b.get("supportato")
    print(f"{'PASS' if uguali else 'FAIL'} {prova}: vaapi {a['decodificati']}/{a['chunk']} vulkan {b['decodificati']}/{b['chunk']} · misura {b.get('misura')} · errori {b['errori']} · impronte {'uguali' if a['impronte']==b['impronte'] else 'DIVERSE'}")
    rossi += 0 if uguali else 1
    passati += 1 if uguali else 0
print(f"{passati} PASS · {rossi} FAIL · {non_provati} non provati")
sys.exit(1 if rossi else 0)
EOF
