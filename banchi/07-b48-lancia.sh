#!/bin/bash
#
# 07-b48-lancia.sh — mette in piedi il banco «la tela contro la verità».
#
#   bash banchi/07-b48-lancia.sh [cartella-dei-dati]
#
# ⛔ SERVE `http://localhost`, e non è un capriccio: WebCodecs vuole un
#    contesto sicuro, e un `file://` non lo è — la pagina si aprirebbe e
#    `VideoDecoder` non esisterebbe, cioè un banco che dice «questo browser non
#    sa» di un browser che sa benissimo.
#
# I tre file dei dati (il flusso, il suo indice, la verità) NON stanno nel
# deposito: sono 27 MB di rilievo di una sessione.  Li si passa con la cartella
# che li contiene, o si lasciano dove `07-b48-verita.sh` li ha messi.
set -euo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DATI=${1:-$QUI/07-b48-dati}
PORTA=${PORTA:-8099}

for f in flusso.obu indice.json verita.json; do
	if [ ! -f "$DATI/$f" ]; then
		echo "⛔ manca $DATI/$f — il banco non ha né i pezzi né la verità."
		echo "   Si costruiscono con `07-b48-verita.sh` dal rilievo di una sessione."
		exit 2
	fi
done

# ⚠ La pagina si COPIA accanto ai dati invece di spostare i dati: il deposito
#   resta senza i 27 MB, e quel che il browser vede è un solo posto.
cp "$QUI/07-b48-tela-contro-verita.html" "$DATI/indice.html"
cp "$QUI/07-b48-tela-contro-verita.html" "$DATI/index.html"

echo "⭐ banco pronto.  Apri sul TABLET, in Firefox:"
echo
echo "     http://localhost:$PORTA/"
echo
echo "   e per i due modi separati:"
echo "     http://localhost:$PORTA/?modo=decodificatore"
echo "     http://localhost:$PORTA/?modo=tela"
echo "     http://localhost:$PORTA/?ritmo=0        (a tutta forza)"
echo
echo "   ⛔ Fermalo con Ctrl-C quando hai finito."
exec python3 -m http.server "$PORTA" --bind 127.0.0.1 --directory "$DATI"
