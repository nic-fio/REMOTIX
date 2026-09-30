#!/usr/bin/env bash
# t8-prepara-guasti.sh — fase 17, T8: i cataloghi e le revoche «guasti» per le prove della catena A
# (sul portatile, dove stanno le chiavi DI PROVA; l'uscita va sul server con t8-porta.sh).
#
#   bash banchi/17-t8/t8-prepara-guasti.sh <uscita> <catalogo-di-partenza.json>
#
#   scaduto/    catalogo sequenza 6, scadenza 2026-09-01, firmato BENE (A-2026) ⇒ RX-TRUST-002
#   revoca/     revoche sequenza 2 che revocano A-2026 (firmate dalla radice) ⇒ RX-TRUST-010
#   rotazione/  catalogo sequenza 7 firmato con la sottochiave NUOVA A-2027 (+ le revoche di sopra)
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
U=$(realpath -m "${1:?uscita}"); C=${2:?catalogo}
P="bash $ALBERO/packaging/archivio/pubblica.sh"
mkdir -p "$U"/{scaduto,revoca,rotazione}
python3 - "$C" "$U" <<'EOF'
import sys, re
c, u = sys.argv[1], sys.argv[2]
s = open(c).read()
def con(seq, scad=None):
    t = re.sub(r'"sequenza": \d+,', '"sequenza": %d,' % seq, s, count=1)
    t = re.sub(r'"versione": "[^"]+"', '"versione": "2026.09.30.%d"' % seq, t, count=1)
    if scad:
        t = re.sub(r'"scadenza": "[^"]+"', '"scadenza": "%s"' % scad, t, count=1)
    return t
open(u + "/scaduto/catalogo.json", "w").write(con(6, "2026-09-01"))
open(u + "/rotazione/catalogo.json", "w").write(con(7))
EOF
# la firma con lo strumento della catena A (nella cartella servita di prova, poi si sposta)
A=$U/.archivio; rm -rf "$A"; mkdir -p "$A"
ARCHIVIO=$A $P catalogo stabile "$U/scaduto/catalogo.json" A-2026
mv "$A/catalogo/stabile/catalogo.json" "$A/catalogo/stabile/catalogo.json.firma" "$U/scaduto/"
ARCHIVIO=$A $P catalogo stabile "$U/rotazione/catalogo.json" A-2027
mv "$A/catalogo/stabile/catalogo.json" "$A/catalogo/stabile/catalogo.json.firma" "$U/rotazione/"
ARCHIVIO=$A $P revoche 2 "A-2026=prova di T8: la sottochiave si considera persa"
cp "$A/catalogo/revoche.json" "$A/catalogo/revoche.json.firma" "$U/revoca/"
mv "$A/catalogo/revoche.json" "$A/catalogo/revoche.json.firma" "$U/rotazione/"
rm -rf "$A"
find "$U" -type f | sort
