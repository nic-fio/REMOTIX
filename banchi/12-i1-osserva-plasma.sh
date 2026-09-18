#!/bin/bash
# osservazione I1 (fase 12): la ricetta v1 di Plasma headless, a mano, dentro rete11-kde
U=${1:-kobs1}; W=${2:-1600}; H=${3:-900}
id $U >/dev/null 2>&1 || useradd -m -s /bin/bash -G video,render $U
UID_=$(id -u $U); R=/run/user/$UID_
cat > /tmp/avvia-$U.sh <<EOS
#!/bin/bash
R=\$XDG_RUNTIME_DIR
mkdir -p \$R/systemd/user.control/plasma-kwin_wayland.service.d
cat > \$R/systemd/user.control/plasma-kwin_wayland.service.d/remotix.conf <<X
[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width $W --height $H --no-lockscreen
X
systemctl --user daemon-reload
echo "sessione: \$XDG_SESSION_ID classe=\$(loginctl show-session \$XDG_SESSION_ID -p Class --value)"
T0=\$(date +%s.%N)
setsid --fork env -i XDG_RUNTIME_DIR=\$R DBUS_SESSION_BUS_ADDRESS=unix:path=\$R/bus XDG_MENU_PREFIX=plasma- HOME=\$HOME USER=\$USER PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 sh -c 'exec startplasma-wayland >>\$XDG_RUNTIME_DIR/plasma.log 2>&1'
for i in \$(seq 120); do
  busctl --user status org.kde.KWin >/dev/null 2>&1 && { echo "KWin sul bus dopo \$(python3 -c "import time;print(round(time.time()-\$T0,2))") s"; break; }; sleep 0.25; done
for i in \$(seq 120); do
  pgrep -u \$USER -x plasmashell >/dev/null && { echo "plasmashell dopo \$(python3 -c "import time;print(round(time.time()-\$T0,2))") s"; break; }; sleep 0.25; done
sleep 5
EOS
chmod +x /tmp/avvia-$U.sh
runuser -l $U -c "/tmp/avvia-$U.sh"
echo "--- processi di $U"; ps -u $U -o pid,etimes,args | grep -v "ps -u" | cut -c1-150
echo "--- socket"; ls $R | grep wayland
S=$(ls $R | grep -E '^wayland-[0-9]+$' | head -1)
echo "--- wayland-info ($S)"; runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>&1 | grep -A6 "interface: 'wl_output'" | grep -E "name|mode|interface" | head -20
runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>&1 | grep -c "interface: 'wl_output'"
echo "--- renderer"; runuser -u $U -- env DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus gdbus call --session --dest org.kde.KWin --object-path /KWin --method org.kde.KWin.supportInformation 2>/dev/null | grep -oE 'OpenGL renderer string: [^\\]*'
echo "--- unità fallite"; runuser -u $U -- env XDG_RUNTIME_DIR=$R DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus systemctl --user --failed --no-legend | head
echo "--- sessioni"; loginctl list-sessions --no-legend | grep $U
echo "--- log"; tail -15 $R/plasma.log
