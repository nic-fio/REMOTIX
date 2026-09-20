#!/bin/bash
# I10 della fase 12: dentro la sessione Plasma, le tre leve dell'ambiente.
#
#   podman exec rete11-kde bash /rete11/12-i10-menu-e-puntatore.sh
#
# ⭐ Tre cure riportate da v1, e ciascuna col suo giudice DENTRO la sessione:
#   1. il cursore invisibile — `[M]` 19 set 2026, la prova dell'utente: «la coda
#      del puntatore».  Con `--virtual` KWin disegna il cursore DENTRO
#      l'immagine, e chi guarda ne vede due.  ⇒ le tre XCURSOR_* nell'ambiente
#      di kwin_wayland, il tema con le sue forme, e ⛔ NESSUN ripiego
#      («Failed to load cursor theme» nel journal = il tema non si e' caricato);
#   2. il menu senza «Blocca» e «Cambia utente» (KIOSK, `XDG_CONFIG_DIRS`);
#   3. spegnere/riavviare/sospendere: logind dice «no» (DECISIONI.md §4.7, tre
#      cinture messe da `src/provisiona.sh` e, nelle scatole, da `11-accendi.sh`).
U=k10; PORTA=8512
loginctl terminate-user $U 2>/dev/null; sleep 1; userdel -r $U >/dev/null 2>&1
useradd -m -s /bin/bash $U && printf '%s:provanic2026\n' $U | chpasswd && usermod -aG video,render $U
python3 /opt/remotix/01-b3-cliente.py --indirizzo 127.0.0.1 --porta $PORTA --utente $U --parola provanic2026 --resta 40 > /tmp/cliente-$U.log 2>&1 &
for i in $(seq 160); do pgrep -u $U -x kwin_wayland >/dev/null && break; sleep 0.25; done
sleep 6
P=$(pgrep -u $U -x kwin_wayland)
[ -n "$P" ] || { echo "⛔ KWin non e' partito: non ho potuto guardare"; loginctl terminate-user $U; exit 3; }
AMB=$(tr '\0' '\n' < /proc/$P/environ)
TEMA=$(echo "$AMB" | grep -c -E '^XCURSOR_(THEME=remotix-invisibile|SIZE=|PATH=)')
FORME=$(ls /run/user/$(id -u $U)/remotix/icons/remotix-invisibile/cursors 2>/dev/null | wc -l)
RIPIEGO=$(journalctl --no-pager --since -3min 2>/dev/null | grep -c -i "Failed to load cursor theme")
echo "1. cursore invisibile : $([ "$TEMA" = 3 ] && [ "$FORME" -gt 40 ] && [ "$RIPIEGO" = 0 ] && echo "⭐ SI" || echo "⛔ NO")  (XCURSOR_* $TEMA/3 · forme $FORME · ripieghi $RIPIEGO)"
R=/run/user/$(id -u $U)
chiedi() { runuser -u $U -- env DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus "$@" 2>&1; }
KIOSK=$(echo "$AMB" | grep -c "XDG_CONFIG_DIRS=.*remotix/xdg")
REGOLE=$(grep -c -E 'lock_screen=false|switch_user=false|start_new_session=false' $R/remotix/xdg/kdeglobals 2>/dev/null)
echo "2. menu senza blocco  : $([ "$KIOSK" = 1 ] && [ "$REGOLE" = 3 ] && echo "⭐ SI" || echo "⛔ NO")  (XDG_CONFIG_DIRS $KIOSK/1 · regole $REGOLE/3)"
NO=0
for v in CanPowerOff CanReboot CanSuspend CanHibernate; do
	chiedi busctl call org.freedesktop.login1 /org/freedesktop/login1 \
		org.freedesktop.login1.Manager $v | grep -q '"no"' && NO=$((NO+1))
done
echo "3. nessuno spegne     : $([ "$NO" = 4 ] && echo "⭐ SI" || echo "⛔ NO")  ($NO/4 rispondono «no»)"
loginctl terminate-user $U
