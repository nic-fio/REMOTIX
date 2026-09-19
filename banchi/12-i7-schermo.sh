#!/bin/bash
# I7 della fase 12: lo schermo della sessione remota di Plasma NON si spegne.
#
# Si gira DENTRO la scatola `kde` (col prodotto e il server gia' messi):
#   podman exec rete11-kde bash /rete11/12-i7-schermo.sh
#
# ⭐ Il giudice e' powerdevil stesso, non il nostro registro: gli si chiede
#    `PolicyAgent.HasInhibition(4)` (4 = ChangeScreenSettings, quello che tiene
#    acceso lo schermo) dal bus della sessione dell'utente.
#    «true»  ⇒ qualcuno lo tiene acceso;  «false» ⇒ dopo 10 minuti si spegne.
# ⛔ La controprova si fa col binario vecchio (senza il ramo KDE di
#    `sessione_inibisci()`): deve dire «false», o il banco non distingue.
U=ki7; PORTA=8512
loginctl terminate-user $U 2>/dev/null; sleep 1; userdel -r $U >/dev/null 2>&1
useradd -m -s /bin/bash $U && printf '%s:provanic2026\n' $U | chpasswd && usermod -aG video,render $U
python3 /opt/remotix/01-b3-cliente.py --indirizzo 127.0.0.1 --porta $PORTA --utente $U --parola provanic2026 --resta 60 > /tmp/cliente-$U.log 2>&1 &
for i in $(seq 120); do pgrep -u $U -f org_kde_powerdevil >/dev/null && break; sleep 0.25; done
pgrep -u $U -f org_kde_powerdevil >/dev/null && echo "powerdevil vivo" || echo "⛔ powerdevil NON e' partito"
sleep 8
R=/run/user/$(id -u $U)
chiedi() {
	runuser -u $U -- env DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus busctl --user call \
		org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement/PolicyAgent \
		org.kde.Solid.PowerManagement.PolicyAgent "$@" 2>&1
}
echo "HasInhibition(4) schermo      : $(chiedi HasInhibition u 4)"
echo "HasInhibition(1) inattivita'  : $(chiedi HasInhibition u 1)"
echo "registro del figlio           : $(grep -a -o 'Plasma: [^(]*' /var/lib/rete11/registro.log | tail -1)"
# ⭐ E se powerdevil muore?  systemd lo fa ripartire (`Restart=on-failure`), e
#    l'inibizione vecchia e' morta con lui: il figlio deve richiederla.
if [ "${1:-}" = riparte ]; then
	pkill -KILL -u $U -f org_kde_powerdevil
	for i in $(seq 40); do sleep 0.5; chiedi HasInhibition u 4 | grep -q true && break; done
	sleep 4
	echo "--- powerdevil ucciso e ripartito"
	echo "HasInhibition(4) schermo      : $(chiedi HasInhibition u 4)"
	echo "registro del figlio           : $(grep -a -o 'Plasma: [^(]*(.*ripartito' /var/lib/rete11/registro.log | tail -1 | cut -c1-80)"
fi
loginctl terminate-user $U
