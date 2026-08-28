#!/bin/bash
# Gli appunti con le immagini, nei due versi.
#
# ⚠ Il client di FreeRDP accetta dal proprio X solo le immagini che WinPR sa
#   convertire in DIB: sul banco sono i BMP.  Il verso «client → sessione» si
#   prova quindi con un BMP, non con un PNG — altrimenti non si misura REMOTIX,
#   si misura che cosa il client sa leggere.
set -u
BASE=/media/REMOTIX
BANCO=/srv/remotix/tmp/banco-b
vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

echo "== 0. un PNG di prova nella sessione"
vm 'python3 - <<PY
import struct, zlib
larg, alt = 8, 8
righe = b"".join(b"\x00" + bytes([(x*30)%256, (y*30)%256, 128, 255][k] for x in range(larg) for k in range(4)) for y in range(alt))
def pezzo(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t+d))
png = b"\x89PNG\r\n\x1a\n" + pezzo(b"IHDR", struct.pack(">IIBBBBB", larg, alt, 8, 6, 0, 0, 0)) + pezzo(b"IDAT", zlib.compress(righe)) + pezzo(b"IEND", b"")
open("/tmp/prova.png","wb").write(png)
print("   PNG 8x8 scritto, primo pixel (0,0,128)")
PY'

echo "== 1. server e client"
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BASE/src/remotix-c/build/src/remotix" >/dev/null || exit 1
vm "bash avvia-remotix.sh --aperto" | tail -1
cnt "bash $BANCO/fumo8-client.sh"

echo "== 2. LA SESSIONE copia un PNG, il client incolla (e riceve un BMP)"
vm "pkill -x wl-copy 2>/dev/null; setsid nohup env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wl-copy --type image/png < /tmp/prova.png >/dev/null 2>&1 & sleep 3; echo '   immagine copiata nella sessione'"
sleep 2
cnt "DISPLAY=:110 timeout 10 xclip -selection clipboard -t TARGETS -o 2>&1 | tr '\n' ' ' | sed 's/^/   il client vede: /'; echo"
cnt "DISPLAY=:110 timeout 10 xclip -selection clipboard -t image/bmp -o > /tmp/dal-server.bmp 2>/dev/null; python3 - <<'PY'
import struct
d = open('/tmp/dal-server.bmp','rb').read()
if len(d) < 54 or d[:2] != b'BM':
    print('   il client NON ha ricevuto un BMP valido (%d byte)' % len(d))
else:
    off, larg, alt, bpp = struct.unpack('<I', d[10:14])[0], struct.unpack('<i', d[18:22])[0], struct.unpack('<i', d[22:26])[0], struct.unpack('<H', d[28:30])[0]
    p = d[off:off+4]
    print('   il client ha ricevuto un BMP %dx%d a %d bit, pixel in basso a sinistra BGR=%d,%d,%d'
          % (larg, alt, bpp, p[0], p[1], p[2]))
PY"

echo "== 3. IL CLIENT copia quel BMP, la sessione incolla (e riceve un PNG)"
cnt "pkill -x xclip 2>/dev/null; setsid nohup env DISPLAY=:110 xclip -selection clipboard -t image/bmp -i /tmp/dal-server.bmp >/dev/null 2>&1 & sleep 3; echo '   immagine copiata nel client'"
sleep 2
vm "env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 timeout 10 wl-paste --list-types 2>&1 | tr '\n' ' ' | sed 's/^/   la sessione vede: /'; echo"
vm "env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 timeout 10 wl-paste --type image/png > /tmp/dal-client.png 2>/dev/null; python3 - <<'PY'
import gi
gi.require_version('GdkPixbuf','2.0')
from gi.repository import GdkPixbuf
try:
    p = GdkPixbuf.Pixbuf.new_from_file('/tmp/dal-client.png')
    px = p.get_pixels()
    n = p.get_n_channels()
    print('   la sessione ha ricevuto un PNG %dx%d, primo pixel RGB=%d,%d,%d'
          % (p.get_width(), p.get_height(), px[0], px[1], px[2]))
except Exception as e:
    print('   la sessione NON ha ricevuto un PNG valido:', e)
PY"

echo "== 4. registro"
vm "grep -iE 'appunti' ~/remotix.log | tail -8"
cnt "pkill -x xfreerdp3 2>/dev/null; pkill -x xclip 2>/dev/null; echo '   chiuso'"
vm "pkill -x wl-copy 2>/dev/null; echo '   sgombrato'"
