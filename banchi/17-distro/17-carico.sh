#!/bin/bash
#
# 17-carico.sh — how many distribution VMs the server holds together (29 Sep 2026)
#
# User's decision: «if the system holds we go from 4 to 8; if it does not hold we go back to 4, so we
# keep a bit of margin». Every VM simulates the work of REMOTIX without a real card: desktop on
# (graphical.target), continuous SOFTWARE H.264 encoding Full HD 30 fps (the libx264 fallback: the
# heaviest load of REMOTIX in a VM), and 2.5 GB of memory in use (a desktop with programs).
#
#   bash 17-carico.sh <minuti> <macchina> [<macchina> …]
#
# It holds if, for the whole test: server available memory ≥ 3 GB; average swap (si+so, KiB/s) < 100
# pages/s; every encoding ≥ 29 fps; every VM answers ssh within 2 s; no kill by earlyoom
# or by the kernel.  At the end every VM goes back to the «cliente» photo.
#
set -uo pipefail
cd /media/REMOTIX/vm17
MIN=${1:?minutes}; shift
M=("$@")
OUT=/media/REMOTIX/vm17/carico-$(date -u +%Y%m%dT%H%M)-${#M[@]}vm
mkdir -p "$OUT"
vm() { bash 17-vm.sh "$@"; }
T0=$(date -u +%s)
echo "⭐ load test: ${#M[@]} VM × ${RX_VM_RAM:-6144} MB × ${RX_VM_CPU:-4} cpu, $MIN min → $OUT"

for m in "${M[@]}"; do
	( vm ferma "$m" >/dev/null 2>&1; vm torna "$m" cliente >/dev/null && vm avvia "$m" > "$OUT/avvio-$m.txt" 2>&1 ) &
done
wait
for m in "${M[@]}"; do
	grep -q "ssh answers" "$OUT/avvio-$m.txt" || { echo "⛔ $m did not start"; cat "$OUT/avvio-$m.txt"; }
done

# the work inside every VM (ffmpeg from the VM's package manager: the «cliente» photo is put back afterwards)
LAVORO='
set -e
if command -v apt-get >/dev/null; then sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q ffmpeg >/dev/null
elif command -v pacman >/dev/null; then sudo pacman -S --noconfirm --needed ffmpeg >/dev/null
elif command -v zypper >/dev/null; then sudo zypper -n install ffmpeg >/dev/null
elif command -v dnf >/dev/null; then sudo dnf -y -q install ffmpeg-free >/dev/null; fi
sudo systemctl isolate graphical.target || true
ENC=libx264; ffmpeg -hide_banner -encoders 2>/dev/null | grep -q " libx264 " || ENC=libopenh264
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q " $ENC " || ENC=mpeg4
echo "encoder: $ENC"
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
echo "   work on: $(for m in "${M[@]}"; do printf "%s=%s " "$m" "$(grep -o "encoder: .*" "$OUT/lavoro-$m.txt" | cut -d" " -f2)"; done)"

# the measurement: every 10 s
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
		# ⚠ ffmpeg's fps= is the AVERAGE since the start: a drop halfway through gets diluted in it. The
		#   frame counter is also read with the VM's clock, and the verdict computes the rate over 5 readings.
		l=$(timeout 10 bash 17-vm.sh ssh "$m" "f=\$(tail -c 400 /tmp/carico-ffmpeg.log | tr '\r' '\n' | grep -o 'frame=[ 0-9]*' | tail -1 | tr -d 'frame= '); echo \$(date +%s.%N) \$f" 2>/dev/null)
		ms=$(( ($(date +%s%N) - a) / 1000000 ))
		set -- $l
		riga="$riga $m:t=${1:-?},frame=${2:-?},ssh_ms=$ms"
	done
	echo "$riga" | tee -a "$OUT/misure.txt"
	sleep 5
done

# ⚠ shut down and restore ONE AT A TIME, and BEFORE reading the journal: the check of 29 Sep
#   found an earlyoom kill (xdg-desktop-portal-gtk, 15:28:19) during the parallel shutdown
#   of 8 VMs — one second after the verdict, which therefore had not seen it.
for m in "${M[@]}"; do vm ferma "$m" >/dev/null 2>&1; vm torna "$m" cliente >/dev/null; done
echo "   VMs shut down and back to the «cliente» photo (one at a time)"

# the verdict
# ⛔ the user cannot read the journal: without sudo the count would be 0 WITHOUT having looked (UNKNOWN ≠ PASS)
P=$(sed -n "s/^pass: *//p" ~/SERVER.ssh)
if J=$(printf "%s\n" "$P" | sudo -S -p "" journalctl --since "$J0" -q 2>/dev/null) && [ -n "$J" ]; then
	uccisi=$(printf "%s\n" "$J" | grep -c -i -E "earlyoom.*(sending|killing)|Out of memory|oom-kill")
else
	uccisi="?"
fi
python3 - "$OUT/misure.txt" "$uccisi" <<'PY' | tee "$OUT/giudizio.txt"
import sys,re
righe=[l.split() for l in open(sys.argv[1]) if l.strip()]
righe=righe[3:]   # the first 30 s: the work starting up
disp=[int(r[1].split("=")[1]) for r in righe]
sw=[int(r[2].split("=")[1]) for r in righe]
fps=[];ssh=[];ignoti=0;prec={}
for r in righe:
    for c in r[4:]:
        m=re.search(r"^([^:]+):t=([0-9.?]+),frame=([0-9?]+),ssh_ms=(\d+)",c)
        ssh.append(int(m.group(4)))
        if "?" in (m.group(2),m.group(3)): ignoti+=1; prec.pop(m.group(1),None); continue
        t,f=float(m.group(2)),int(m.group(3))
        # the rate over a window of 5 readings (~60 s), not the average since the start. ⚠ Not between two
        #   close readings: ffmpeg updates the counter every 15 frames, and over 12 s that makes ±1.3 fps of
        #   rounding alone (test A of 29 Sep: 28.7…31.2 with the encoding steady at 30.00).
        v=prec.setdefault(m.group(1),[]); v.append((t,f))
        if len(v)>5: fps.append((f-v[-6][1])/(t-v[-6][0]))
esiti=[
 ("minimum available memory ≥ 3072 MB", min(disp)>=3072, "%d MB"%min(disp)),
 ("average swap < 100 KiB/s (vmstat si+so columns)", sum(sw)/len(sw)<100, "%.0f"%(sum(sw)/len(sw))),
 ("every encoding ≥ 29 fps", bool(fps) and min(fps)>=29, "min %.1f fps"%(min(fps) if fps else -1)),
 ("no unknown fps (UNKNOWN is not PASS)", ignoti==0, "%d missed readings"%ignoti),
 ("every VM answers within 2 s", max(ssh)<=2000, "max %d ms"%max(ssh)),
 ("no kill (earlyoom/oom), journal read", sys.argv[2]=="0", sys.argv[2]),
]
for n,ok,v in esiti: print(("  PASS " if ok else "  FAIL ")+n+" — "+v)
print("⇒ HOLDS" if all(ok for _,ok,_ in esiti) else "⇒ DOES NOT HOLD")
PY

