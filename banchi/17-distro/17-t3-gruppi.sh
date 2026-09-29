#!/bin/sh
# 17-t3-gruppi.sh — fase 17, T3 linea C: il PASSO DEL MOTORE «le persone nei
# gruppi della scheda», fatto a mano nella VM di prova, e il suo ritorno indietro.
#
#   (DENTRO la VM, da root)  sh 17-t3-gruppi.sh iscrivi | annulla
#
# ⭐ `DECISIONI.md` §10.12: il pacchetto non tocca i gruppi; lo fa il motore
#    (`installatore/motore`, azione `aggiungi-utente-a-gruppo`, col suo
#    registro).  Finche' il motore non monta i pacchetti, le prove fanno qui lo
#    stesso gesto, con lo stesso criterio, e lo annotano come «passo del motore».
#
# ⭐ `DECISIONI.md` §7.21: una sessione remota non ha un seat, quindi l'ACL di
#    logind sui nodi /dev/dri non arriva mai; restano SOLO i gruppi.  Alla
#    installazione si iscrivono le persone gia' sulla macchina: UID_MIN..UID_MAX
#    di login.defs, e solo chi ha una shell vera (gli account di servizio no).
#    I nomi dei gruppi si chiedono ai NODI (`stat -c %g`), non si inchiodano.
#
# ⭐ `fasi/17-l-installatore.md` §6.4 e §6.6.4 (R6, R33): ogni coppia
#    persona-gruppo si annota nel registro con la sua ORIGINE:
#        c-era  <persona> <gruppo>   c'era gia' prima  ⇒ PREESISTENTE, non si tocca mai
#        messo  <persona> <gruppo>   l'ha messo il pacchetto ⇒ DIRETTA, `annulla` la toglie
#    Una coppia gia' annotata non si annota di nuovo: installare due volte non
#    cambia niente (R5), e un aggiornamento non trasforma un «messo» in «c-era».
#
# ⚠ Quel che questo registro NON vede: le persone che il PRODOTTO iscrive alla
#   loro prima connessione (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`).
#   Oggi quelle vanno solo nel journal; ⇒ la disinstallazione non le toglie.
#   Vale anche per il motore: annotato in §13.1 come «da fare».
#
# ⚠ Esce sempre con 0: un'iscrizione mancata la DICE.
set -u

REGISTRO=/var/tmp/remotix-t3-gruppi.registro

# login.defs: su openSUSE sta in /usr/etc (e /etc lo sovrascrive se c'e').
leggi_defs()
{
	v=""
	for f in /usr/etc/login.defs /etc/login.defs; do
		[ -r "$f" ] || continue
		x=$(awk -v k="$1" '$1 == k { print $2 }' "$f")
		[ -n "$x" ] && v=$x
	done
	printf '%s' "${v:-$2}"
}

gruppi_della_scheda()
{
	for n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$n" ] || continue
		g=$(stat -c %g "$n" 2>/dev/null) || continue
		[ "$g" = 0 ] && continue       # root: nessuno va messo nel gruppo di root
		getent group "$g" | cut -d: -f1
	done | sort -u
}

# c'e' gia' (come gruppo supplementare o primario)?
membro()
{
	id -nG "$1" 2>/dev/null | tr ' ' '\n' | grep -qx "$2"
}

annotata()
{
	[ -f "$REGISTRO" ] && grep -qE "^(c-era|messo) $1 $2\$" "$REGISTRO"
}

iscrivi()
{
	min=$(leggi_defs UID_MIN 1000)
	max=$(leggi_defs UID_MAX 60000)
	gruppi=$(gruppi_della_scheda)
	if [ -z "$gruppi" ]; then
		echo "remotix: nessun nodo /dev/dri su questa macchina: nessun gruppo della scheda da dare"
		return 0
	fi
	[ -f "$REGISTRO" ] || { : >"$REGISTRO"; chmod 0600 "$REGISTRO"; }
	persone=$(awk -F: -v a="$min" -v b="$max" \
		'$3 >= a && $3 <= b && $7 !~ /(nologin|false)$/ { print $1 }' /etc/passwd)
	for p in $persone; do
		for g in $gruppi; do
			annotata "$p" "$g" && continue
			if membro "$p" "$g"; then
				echo "c-era $p $g" >>"$REGISTRO"
			elif gpasswd -a "$p" "$g" >/dev/null 2>&1; then
				echo "messo $p $g" >>"$REGISTRO"
				echo "remotix: $p iscritto a $g (la sessione remota non ha il seat: senza, pagina bianca)"
			else
				echo "remotix: ⛔ $p NON iscritto a $g (gpasswd ha rifiutato)"
			fi
		done
	done
	return 0
}

annulla()
{
	[ -f "$REGISTRO" ] || return 0
	grep '^messo ' "$REGISTRO" | while read -r _ p g; do
		getent passwd "$p" >/dev/null || continue
		if membro "$p" "$g" && gpasswd -d "$p" "$g" >/dev/null 2>&1; then
			echo "remotix: $p tolto da $g (ce l'aveva messo il passo del motore)"
		fi
	done
	rm -f "$REGISTRO"
	return 0
}

case ${1:-} in
iscrivi) iscrivi ;;
annulla) annulla ;;
*) echo "uso: $0 iscrivi|annulla" >&2; exit 2 ;;
esac
