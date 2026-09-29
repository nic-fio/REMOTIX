#!/bin/bash
#
# 17-carico.sh — quante VM delle distribuzioni reggono insieme sul server (29 set 2026)
#
# Decisione dell'utente: «se il sistema regge passiamo da 4 a 8; se non regge torniamo a 4, così ci
# teniamo un po' di margine». Ogni VM simula il lavoro di REMOTIX senza scheda vera: desktop acceso
# (graphical.target), codifica H.264 IN SOFTWARE continua Full HD 30 fps (il ripiego libx264: il
# carico più pesante di REMOTIX in una VM), e 2,5 GB di memoria occupata (un desktop con programmi).
#
#   bash 17-carico.sh <minuti> <macchina> [<macchina> …]
#
# Regge se, per tutta la prova: memoria disponibile del server ≥ 3 GB; scambio (si+so, KiB/s) medio < 100
# pagine/s; ogni codifica ≥ 29 fps; ogni VM risponde a ssh entro 2 s; nessuna uccisione di earlyoom
# o del kernel.  Alla fine ogni VM torna alla foto «cliente».
#
set -uo pipefail
cd /media/REMOTIX/vm17
MIN=${1:?minuti}; shift
M=("$@")
OUT=/media/REMOTIX/vm17/carico-$(date -u +%Y%m%dT%H%M)-${#M[@]}vm
mkdir -p "$OUT"
vm() { bash 17-vm.sh "$@"; }
T0=$(date -u +%s)
echo "⭐ prova di carico: ${#M[@]} VM × ${RX_VM_RAM:-6144} MB × ${RX_VM_CPU:-4} cpu, $MIN min → $OUT"

for m in "${M[@]}"; do
	( vm ferma "$m" >/dev/null 2>&1; vm torna "$m" cliente >/dev/null && vm avvia "$m" > "$OUT/avvio-$m.txt" 2>&1 ) &
done
wait
for m in "${M[@]}"; do
	grep -q "ssh risponde" "$OUT/avvio-$m.txt" || { echo "⛔ $m non è partita"; cat "$OUT/avvio-$m.txt"; }
done

# il lavoro dentro ogni VM (ffmpeg dal gestore di pacchetti della VM: la foto «cliente» si rimette dopo)
LAVORO='
set -e
if command -v apt-get >/dev/null; then sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q ffmpeg >/dev/null
elif command -v pacman >/dev/null; then sudo pacman -S --noconfirm --needed ffmpeg >/dev/null
elif command -v zypper >/dev/null; then sudo zypper -n install ffmpeg >/dev/null
elif command -v dnf >/dev/null; then sudo dnf -y -q install ffmpeg-free >/dev/null; fi
sudo systemctl isolate graphical.target || true
ENC=libx264; ffmpeg -hide_banner -encoders 2>/dev/null | grep -q " libx264 " || ENC=libopenh264
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q " $ENC " || ENC=mpeg4
echo "codificatore: $ENC"
nohup python3 -c "b=bytearray(2500*1024*1024)
import time
for i in range(0,len(b),4096): b[i]=1
time.sleep(10**6)" >/dev/null 2>&1 &
nohup ffmpeg -hide_banner -nostdin -re -f lavfi -i testsrc2=size=1920x1080:rate=30 -c:v $ENC \
  $( [ $ENC = libx264 ] && echo "-preset veryfast -tune zerolatency" ) -b:v 8M -f null - \
  > /tmp/carico-ffmpeg.log 2>&1 &
'
for m in "${M[@]}"; do ( vm ssh "$m" "$LAVORO" > "$OUT/lavoro-$m.txt" 2>&1 ) & done
wait
echo "   lavoro acceso: $(for m in "${M[@]}"; do printf "%s=%s " "$m" "$(grep -o "codificatore: .*" "$OUT/lavoro-$m.txt" | cut -d" " -f2)"; done)"

# la misura: ogni 10 s
FINE=$(( $(date -u +%s) + MIN * 60 ))
J0=$(date -u "+%Y-%m-%d %H:%M:%S")
while [ "$(date -u +%s)" -lt "$FINE" ]; do
	t=$(( $(date -u +%s) - T0 ))
	disp=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
	sw=$(vmstat 5 2 | tail -1 | awk '{print $7+$8}')
	carico=$(cut -d" " -f1 /proc/loadavg)
	riga="$t disp_mb=$disp scambio=$sw carico=$carico"
	for m in "${M[@]}"; do
		a=$(date +%s%N)
		# ⚠ il fps= di ffmpeg è la MEDIA dall'inizio: un calo a metà prova ci si diluisce. Si legge
		#   anche il contatore dei fotogrammi con l'ora della VM, e il giudizio fa il ritmo su 5 letture.
		l=$(timeout 10 bash 17-vm.sh ssh "$m" "f=\$(tail -c 400 /tmp/carico-ffmpeg.log | tr '\r' '\n' | grep -o 'frame=[ 0-9]*' | tail -1 | tr -d 'frame= '); echo \$(date +%s.%N) \$f" 2>/dev/null)
		ms=$(( ($(date +%s%N) - a) / 1000000 ))
		set -- $l
		riga="$riga $m:t=${1:-?},frame=${2:-?},ssh_ms=$ms"
	done
	echo "$riga" | tee -a "$OUT/misure.txt"
	sleep 5
done

# ⚠ spegnere e ripristinare UNA ALLA VOLTA, e PRIMA di leggere il journal: la verifica del 29 set ha
#   trovato un'uccisione di earlyoom (xdg-desktop-portal-gtk, 15:28:19) durante lo spegnimento in
#   parallelo di 8 VM — un secondo dopo il giudizio, che quindi non l'aveva vista.
for m in "${M[@]}"; do vm ferma "$m" >/dev/null 2>&1; vm torna "$m" cliente >/dev/null; done
echo "   VM spente e tornate alla foto «cliente» (una alla volta)"

# il giudizio
# ⛔ l'utente non legge il journal: senza sudo il conto sarebbe 0 SENZA aver guardato (UNKNOWN ≠ PASS)
P=$(sed -n "s/^pass: *//p" ~/SERVER.ssh)
if J=$(printf "%s\n" "$P" | sudo -S -p "" journalctl --since "$J0" -q 2>/dev/null) && [ -n "$J" ]; then
	uccisi=$(printf "%s\n" "$J" | grep -c -i -E "earlyoom.*(sending|killing)|Out of memory|oom-kill")
else
	uccisi="?"
fi
python3 - "$OUT/misure.txt" "$uccisi" <<'PY' | tee "$OUT/giudizio.txt"
import sys,re
righe=[l.split() for l in open(sys.argv[1]) if l.strip()]
righe=righe[3:]   # i primi 30 s: il lavoro che si avvia
disp=[int(r[1].split("=")[1]) for r in righe]
sw=[int(r[2].split("=")[1]) for r in righe]
fps=[];ssh=[];ignoti=0;prec={}
for r in righe:
    for c in r[4:]:
        m=re.search(r"^([^:]+):t=([0-9.?]+),frame=([0-9?]+),ssh_ms=(\d+)",c)
        ssh.append(int(m.group(4)))
        if "?" in (m.group(2),m.group(3)): ignoti+=1; prec.pop(m.group(1),None); continue
        t,f=float(m.group(2)),int(m.group(3))
        # il ritmo su una finestra di 5 letture (~60 s), non la media dall'inizio. ⚠ Non fra due letture
        #   vicine: ffmpeg aggiorna il contatore ogni 15 fotogrammi, e su 12 s fa ±1,3 fps di solo
        #   arrotondamento (prova A del 29 set: 28,7…31,2 a codifica ferma a 30,00).
        v=prec.setdefault(m.group(1),[]); v.append((t,f))
        if len(v)>5: fps.append((f-v[-6][1])/(t-v[-6][0]))
esiti=[
 ("memoria disponibile minima ≥ 3072 MB", min(disp)>=3072, "%d MB"%min(disp)),
 ("scambio medio < 100 KiB/s (colonne si+so di vmstat)", sum(sw)/len(sw)<100, "%.0f"%(sum(sw)/len(sw))),
 ("ogni codifica ≥ 29 fps", bool(fps) and min(fps)>=29, "min %.1f fps"%(min(fps) if fps else -1)),
 ("nessun fps sconosciuto (UNKNOWN non è PASS)", ignoti==0, "%d letture mancate"%ignoti),
 ("ogni VM risponde entro 2 s", max(ssh)<=2000, "max %d ms"%max(ssh)),
 ("nessuna uccisione (earlyoom/oom), journal letto", sys.argv[2]=="0", sys.argv[2]),
]
for n,ok,v in esiti: print(("  PASS " if ok else "  FAIL ")+n+" — "+v)
print("⇒ REGGE" if all(ok for _,ok,_ in esiti) else "⇒ NON REGGE")
PY

