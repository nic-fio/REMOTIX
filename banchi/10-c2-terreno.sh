#!/usr/bin/env bash
# ===========================================================================
# 10-c2-terreno — il terreno dell'incarico 10-c2 (fase 10): IL FIGLIO CHE
#                 MUORE DI SIGSEGV SU UNA LARGHEZZA DI FINESTRA QUALSIASI.
#
#   porta 8220 · utenti provadec1 (1100) e provadec1b (1123)
#   albero /media/REMOTIX/src/10c2-src · lavoro /media/REMOTIX/tmp/10c2
#   unita' remotix-8220 · lucchetto GPU `10-c2`
#
# ⛔ NON RISCRIVE `10-b2-terreno.sh` ne' `07-b64-terreno.sh`: gli passa il MIO
#    ambiente e li chiama.  ⭐ L'unica cosa che aggiunge di suo e' quella che
#    l'incarico pretende e che nessun terreno esistente sa fare:
#
#      ⭐⭐ `accendi-core` — il server acceso con **`LimitCORE=infinity`**, e la
#           macchina messa in condizione di SCRIVERE il core di un processo che
#           ha cambiato uid (`fs.suid_dumpable=2`).
#
#    ⛔ Senza tutt'e due, il figlio muore e NON lascia niente da leggere: il
#       figlio scende da root a `provadec1` con `setresuid`, e un processo che
#       ha cambiato credenziali e' `dumpable=0` per predefinito — il nucleo
#       il core non lo scrive nemmeno, e non lo dice a nessuno.
#
# ⚠ E i due `sysctl` sono DI TUTTA LA MACCHINA, non miei: si salvano prima e si
#   rimettono con `core-rimetti`.  ⛔ Lasciarli cambiati vorrebbe dire lasciare
#   una trappola a chi trovera' la macchina domani.
#
# Uso (dal portatile):
#     bash banchi/10-c2-terreno.sh utenti
#     bash banchi/10-c2-terreno.sh porta
#     bash banchi/10-c2-terreno.sh core-prepara
#     bash banchi/10-c2-terreno.sh accendi        # con LimitCORE=infinity
#     bash banchi/10-c2-terreno.sh sgombra
#     bash banchi/10-c2-terreno.sh spegni
#     bash banchi/10-c2-terreno.sh core-rimetti
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8220}
export UTENTE=${UTENTE:-provadec1}
export UID_B=${UID_B:-1100}
export PAROLA_UTENTE=${PAROLA_UTENTE:-b2-browser-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10c2-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10c2}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10c2-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10c2}
export UNITA=${UNITA:-remotix-$PORTA}
CORE_DIR=${CORE_DIR:-/media/REMOTIX/tmp/10c2/core}
SALVA=/media/REMOTIX/tmp/10c2/.core-prima

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

root() { ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c '$1'"; }

PASSO=${1:-stato}
case "$PASSO" in

core-prepara)
	log "⛔ IL NUCLEO DEVE POTER SCRIVERE IL CORE DI UN PROCESSO CHE HA CAMBIATO UID"
	root "mkdir -p $CORE_DIR && chmod 1777 $CORE_DIR
	      if [ ! -f $SALVA ]; then
	        { cat /proc/sys/kernel/core_pattern; cat /proc/sys/fs/suid_dumpable; } > $SALVA
	      fi
	      cat $SALVA | sed \"s/^/        PRIMA /\"
	      sysctl -w kernel.core_pattern=$CORE_DIR/core.%e.%p.%s >/dev/null
	      sysctl -w fs.suid_dumpable=2 >/dev/null
	      echo \"        ADESSO \$(cat /proc/sys/kernel/core_pattern)\"
	      echo \"        ADESSO suid_dumpable=\$(cat /proc/sys/fs/suid_dumpable)\"" \
		|| { ko "⛔ non ho potuto preparare il core"; exit 2; }
	ok "core in $CORE_DIR"
	exit 0 ;;

core-rimetti)
	log "⛔ E I DUE SYSCTL TORNANO COM'ERANO — sono di tutta la macchina, non miei"
	root "if [ -f $SALVA ]; then
	        p=\$(sed -n 1p $SALVA); d=\$(sed -n 2p $SALVA)
	        sysctl -w kernel.core_pattern=\"\$p\" >/dev/null
	        sysctl -w fs.suid_dumpable=\$d >/dev/null
	        rm -f $SALVA
	      fi
	      echo \"        ADESSO \$(cat /proc/sys/kernel/core_pattern)\"
	      echo \"        ADESSO suid_dumpable=\$(cat /proc/sys/fs/suid_dumpable)\"" \
		|| { ko "⛔ non ho potuto rimettere i sysctl"; exit 2; }
	ok "rimessi"
	exit 0 ;;

accendi)
	log "Il server sulla $PORTA — unita' $UNITA.service, con LimitCORE=infinity"
	B2=/media/REMOTIX/src/b2
	LDP="$B2/ngtcp2/build/lib:$B2/prefisso/lib"
	root "set -e
	      mkdir -p $LAV/certificati $LAV/rilievo $CORE_DIR
	      chmod 1777 $LAV/rilievo $CORE_DIR; chmod 755 $LAV
	      : > $LAV/registro.log
	      systemctl stop $UNITA.service 2>/dev/null || true
	      systemctl reset-failed $UNITA.service 2>/dev/null || true
	      i=0; while ss -uln 2>/dev/null | grep -q \":$PORTA \" && [ \$i -lt 50 ]; do i=\$((i+1)); sleep 0.2; done
	      systemd-run --unit=$UNITA --collect \
	        --description=\"REMOTIX_V2, incarico 10-c2 (SIGSEGV del figlio)\" \
	        --working-directory=$ALBERO/src \
	        --setenv=LD_LIBRARY_PATH=$LDP \
	        --property=StandardOutput=append:$LAV/registro.log \
	        --property=StandardError=append:$LAV/registro.log \
	        --property=KillMode=mixed \
	        --property=LimitCORE=infinity \
	        --property=LimitRTPRIO=20 --property=LimitNICE=-11 \
	        $ALBERO/src/remotix --indirizzo 0.0.0.0 --nome $IND --porta $PORTA \
	        --certificati $LAV/certificati --pagina $ALBERO/src/pagina.html \
	        --ban-file $LAV/ban --comando-socket $LAV/comando.sock \
	        --rilievo $LAV/rilievo ${OPZIONI_SERVER:-} --parlantina >/dev/null
	      i=0; PID=0
	      while [ \$i -lt 60 ]; do
	        PID=\$(systemctl show -p MainPID --value $UNITA.service 2>/dev/null || echo 0)
	        [ \"\$PID\" != 0 ] && [ -n \"\$PID\" ] && break
	        i=\$((i+1)); sleep 0.1
	      done
	      echo \"        pid \$PID\"
	      grep -E \"Max core|Max realtime\" /proc/\$PID/limits | sed \"s/^/        LIM /\"" \
		|| { ko "⛔ il server non e' partito"; exit 2; }
	ok "acceso"
	exit 0 ;;

*)
	exec env PORTA=$PORTA UTENTE=$UTENTE UID_B=$UID_B PAROLA_UTENTE=$PAROLA_UTENTE \
		ALBERO=$ALBERO LAV=$LAV DENTRO_ALB=$DENTRO_ALB DENTRO_LAV=$DENTRO_LAV \
		UNITA=$UNITA MACCHINA=$MACCHINA PAROLA_SUDO=$PAROLA_SUDO IND=$IND \
		bash "$QUI/banchi/10-b2-terreno.sh" "$PASSO" ;;
esac
