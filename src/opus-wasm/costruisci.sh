#!/bin/sh
# Costruisce src/opus-wasm/opus.wasm (libopus solo decodifica, WebAssembly) e
# lo incastona in src/pagina.html fra i due segni OPUS_WASM.  RIPETIBILE:
# versioni fissate e impronte controllate; gira da utente, senza sudo, in un
# contenitore podman con l'immagine ufficiale di emscripten fissata per digest.
#
#   sh src/opus-wasm/costruisci.sh            # costruisce e incastona
#   sh src/opus-wasm/costruisci.sh --verifica # controlla che la pagina porti
#                                             # esattamente opus.wasm
set -eu

QUI=$(cd "$(dirname "$0")" && pwd)
PAGINA="$QUI/../pagina.html"

OPUS_VER=1.5.2
OPUS_URL="https://downloads.xiph.org/releases/opus/opus-$OPUS_VER.tar.gz"
OPUS_SHA256=65c1d2f78b9f2fb20082c38cbe47c951ad5839345876e46941612ee87f9a7ce1
# emscripten 4.0.15 (emcc 09f52557f0d48b65b8c724853ed8f4e8bf80e669)
EMSDK_IMG="docker.io/emscripten/emsdk@sha256:27bc6267cb285223b8aebb7627bfebae7cb3ad2aaa0d5923b8aa5321793033e8"

incastona() {
	python3 - "$QUI/opus.wasm" "$PAGINA" "$1" <<'PY'
import base64, re, sys
wasm, pagina, modo = sys.argv[1], sys.argv[2], sys.argv[3]
b64 = base64.b64encode(open(wasm, "rb").read()).decode()
t = open(pagina, encoding="utf-8").read()
rx = re.compile(r'(/\*OPUS_WASM_INIZIO\*/")([A-Za-z0-9+/=]*)("/\*OPUS_WASM_FINE\*/)')
m = rx.search(t)
if not m:
    sys.exit("⛔ i segni OPUS_WASM non ci sono in " + pagina)
if modo == "verifica":
    ok = m.group(2) == b64
    print(("⭐ la pagina porta esattamente opus.wasm (%d byte, %d in base64)" if ok
           else "⛔ la pagina NON porta opus.wasm (%d byte, %d in base64)") % (len(base64.b64decode(b64)), len(b64)))
    sys.exit(0 if ok else 1)
t = t[:m.start(2)] + b64 + t[m.end(2):]
open(pagina, "w", encoding="utf-8").write(t)
print("⭐ incastonato: %d byte di wasm, %d di base64" % (len(base64.b64decode(b64)), len(b64)))
PY
}

if [ "${1:-}" = "--verifica" ]; then
	incastona verifica
	exit $?
fi

LAV=$(mktemp -d)
trap 'rm -rf "$LAV"' EXIT
curl -sSfL -o "$LAV/opus.tar.gz" "$OPUS_URL"
echo "$OPUS_SHA256  $LAV/opus.tar.gz" | sha256sum -c -
cp "$QUI/decodifica.c" "$LAV/"

# ⚠ -O3 ma senza SIMD e senza estensioni oltre l'MVP: il modulo deve girare
#   anche sui browser vecchi dei telefoni.  Nessun import: niente libc esterna.
podman run --rm --network=none -v "$LAV:/w:Z" -w /w "$EMSDK_IMG" sh -euc '
	tar xzf opus.tar.gz --no-same-owner
	emcmake cmake -S opus-'"$OPUS_VER"' -B b -DCMAKE_BUILD_TYPE=Release \
		-DOPUS_BUILD_PROGRAMS=OFF -DOPUS_BUILD_TESTING=OFF \
		-DOPUS_HARDENING=OFF -DOPUS_STACK_PROTECTOR=OFF -DOPUS_FORTIFY_SOURCE=OFF \
		-DOPUS_DISABLE_INTRINSICS=ON -DOPUS_DRED=OFF -DOPUS_OSCE=OFF \
		-DCMAKE_C_FLAGS="-O3" >/dev/null
	cmake --build b -j4 >/dev/null
	emcc -O3 -I opus-'"$OPUS_VER"'/include decodifica.c b/libopus.a \
		-o opus.wasm --no-entry -sSTANDALONE_WASM -sSTACK_SIZE=262144 \
		-sINITIAL_MEMORY=1048576 -sALLOW_MEMORY_GROWTH=0 -sFILESYSTEM=0 \
		-sERROR_ON_UNDEFINED_SYMBOLS=1
'
cp "$LAV/opus.wasm" "$QUI/opus.wasm"
sha256sum "$QUI/opus.wasm" | sed "s#  .*#  opus.wasm#" > "$QUI/opus.wasm.sha256"
echo "⭐ opus.wasm: $(wc -c < "$QUI/opus.wasm") byte, sha256 $(cut -d' ' -f1 "$QUI/opus.wasm.sha256")"
incastona scrivi
