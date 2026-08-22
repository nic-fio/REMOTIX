#!/bin/bash
#
# 04-b30-scena-costruisci.sh — ⛔ GIRA **DENTRO** IL CONTENITORE (sull'host non
# c'e' `gcc`).  Costruisce `04-b30-scena.c`, la scena che risponde all'input.
#
#     bash /media/REMOTIX/enter.sh --root "bash /srv/src/04-b30-scena-costruisci.sh"
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ PERCHE' QUESTO FILE ESISTE — e' un difetto MISURATO, non una preferenza
# ═══════════════════════════════════════════════════════════════════════════
#
# `[M]` 22 agosto 2026, fase 8, agente A: `04-b30-lancia.sh scena-costruisci`
# **non funziona**.  La costruzione stava dentro una riga sola, e quella riga
# attraversa TRE livelli di virgolette — `ssh` → `enter.sh` → `bash -c`.  ⇒ Le
# variabili di shell (`$L`, `$P`) si perdono per strada e il comando che arriva
# a `gcc` e' `gcc -o /scena.nuovo`, cioe' un percorso assoluto sbagliato.
#
# ⚠ E il difetto e' della forma peggiore: **non si accorge di niente**.  Il
#   comando gira, `gcc` fallisce con un errore che nessuno legge, e il banco
#   parte con la scena di ieri — o con nessuna.
#
# ⭐ Ed era gia' scritto nell'intestazione di `04-b30-lancia.sh`, fra le regole
#    di casa: *«un file non ha livelli di virgolette: quel che deve girare sul
#    server sta in uno SCRIPT, non dentro `ssh → enter.sh → bash -c`»*.  ⇒ La
#    regola c'era, il codice non la seguiva.  Adesso la segue.
#
# ⛔ Si compila su un nome NUOVO e poi si rinomina: il nucleo rifiuta di
#    scrivere su un eseguibile in esecuzione (`ETXTBSY`) e `gcc -o` lascia un
#    binario **troncato** — cioe' un banco che parte e non si sa che cosa
#    esegua.  E' la lezione di `03-scena-accendi.sh`.
set -u

SORGENTE=${SORGENTE:-/srv/src/04-b30-scena.c}
LAV=${LAV:-/srv/src/04-b30-scena-lav}
NOME=${NOME:-04-b30-scena}
PROTO=${PROTO:-/usr/share/wayland-protocols}

ko() { printf '⛔ %s\n' "$*" >&2; exit 1; }

[ -f "$SORGENTE" ] || ko "il sorgente non c'e': $SORGENTE"
command -v gcc >/dev/null || ko "manca «gcc»: questo script gira DENTRO il contenitore"
command -v wayland-scanner >/dev/null || ko "manca «wayland-scanner»"

mkdir -p "$LAV" || ko "non posso creare $LAV"
cd "$LAV" || ko "non posso entrare in $LAV"

for x in xdg-shell:stable/xdg-shell \
         presentation-time:stable/presentation-time; do
	n=${x%%:*}
	p="$PROTO/${x#*:}/$n.xml"
	[ -f "$p" ] || ko "manca il protocollo $p"
	wayland-scanner client-header "$p" "$n-client-protocol.h" || ko "scanner header $n"
	wayland-scanner private-code  "$p" "$n-protocol.c"        || ko "scanner code $n"
done

gcc -O2 -Wall -Wextra -o "$LAV/scena.nuovo" "$SORGENTE" \
    "$LAV/xdg-shell-protocol.c" "$LAV/presentation-time-protocol.c" \
    -I"$LAV" $(pkg-config --cflags --libs wayland-client) -lrt \
    || ko "gcc ha fallito"

# ⛔ E si VERIFICA che sia un eseguibile vero prima di rinominarlo: un file di
#    zero byte passerebbe `mv` senza lamentarsi.
[ -s "$LAV/scena.nuovo" ] || ko "il binario e' vuoto"
mv -f "$LAV/scena.nuovo" "$LAV/$NOME" || ko "mv fallito"
chmod 755 "$LAV" "$LAV/$NOME" || ko "chmod fallito"
printf 'COSTRUITA %s (%d byte)\n' "$LAV/$NOME" "$(stat -c %s "$LAV/$NOME")"
