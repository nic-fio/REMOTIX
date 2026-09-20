#!/bin/bash
# I9 della fase 12: il logout dall'interno di Plasma chiude la sessione PULITA.
#
# Si gira DENTRO la scatola `kde` (col prodotto e il server gia' messi):
#   podman exec rete11-kde bash /rete11/12-i9-logout.sh
#
# ⭐ Il gesto e' quello dell'utente: «Esci» dal menu, cioe'
#    `org.kde.Shutdown.logout` sul bus della sessione.
# ⭐ I giudici sono tre, e nessuno e' il registro del figlio da solo:
#    · il CLIENTE: la sessione chiusa col codice 0x10 (la pagina torna al
#      modulo d'accesso, `DECISIONI.md` §4.1-quater);
#    · i PROCESSI: 15 s dopo KWin non c'e' e NON e' rinato;
#    · il registro: la riga del figlio che ha visto KWin andarsene.
# ⛔ `[M]` 19 set 2026, binario `2563cb22`: il figlio restava vivo a risvegliare
#    un flusso morto ogni 400 ms, e il cliente restava attaccato a una pagina
#    ferma.  La controprova si fa con quel binario.
U=ki9; PORTA=8512
loginctl terminate-user $U 2>/dev/null; sleep 1; userdel -r $U >/dev/null 2>&1
useradd -m -s /bin/bash $U && printf '%s:provanic2026\n' $U | chpasswd && usermod -aG video,render $U
python3 /opt/remotix/01-b3-cliente.py --indirizzo 127.0.0.1 --porta $PORTA --utente $U --parola provanic2026 --resta 60 > /tmp/cliente-$U.log 2>&1 &
CLI=$!
for i in $(seq 120); do pgrep -u $U -x plasmashell >/dev/null && break; sleep 0.25; done
sleep 6
R=/run/user/$(id -u $U)
echo "Plasma vivo: $(pgrep -u $U -x kwin_wayland >/dev/null && echo si || echo NO)"
runuser -u $U -- env DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus busctl --user call \
	org.kde.Shutdown /Shutdown org.kde.Shutdown logout 2>&1 | head -2
T0=$(date +%s)
for i in $(seq 60); do kill -0 $CLI 2>/dev/null || break; sleep 0.5; done
echo "il cliente e' uscito dopo $(( $(date +%s) - T0 )) s (su 30): $(kill -0 $CLI 2>/dev/null && echo "⛔ NO, e' ancora attaccato" || echo si)"
echo "la chiusura vista dal cliente: $(grep -a -q 'chiusa dal server, codice 0x10' /tmp/cliente-$U.log && echo '⭐ codice 0x10 (l utente e uscito)' || echo '⛔ niente 0x10')"
sleep 15
echo "KWin 15 s dopo il logout     : $(pgrep -u $U -x kwin_wayland >/dev/null && echo '⛔ vivo (rinato?)' || echo '⭐ andato, e NON rinato')"
# ⚠ Il figlio resta vivo, ed e' il disegno (come su GNOME, §7.6): aspetta un
#   attacco NUOVO e non rifa' la sessione da cui l'utente e' uscito.
echo "il figlio dopo il logout     : $(pgrep -f "remotix-figlio --figlio-interno $U " >/dev/null && echo 'vivo, in attesa di un attacco nuovo (il disegno)' || echo 'andato')"
echo "il registro                 : $(grep -a "\[$U\]" /var/lib/rete11/registro.log | grep -a -o -E "KWIN NON C'E' PIU'|SESSIONE CHIUSA[^.]{0,40}|chiusa dall.utente[^.]{0,40}" | sort | uniq -c | tr '\n' ' ')"
kill $CLI 2>/dev/null
loginctl terminate-user $U
