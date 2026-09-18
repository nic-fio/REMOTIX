#!/bin/bash
# CP2 di I2: il cancello di KWin su zkde_screencast, osservato.
U=ki2; PORTA=8512
loginctl terminate-user $U 2>/dev/null; sleep 1; userdel -r $U >/dev/null 2>&1
useradd -m -s /bin/bash $U && printf '%s:provanic2026\n' $U | chpasswd && usermod -aG video,render $U
rm -f /usr/share/applications/org.kde.remotix-sonda.desktop
python3 /opt/remotix/01-b3-cliente.py --indirizzo 127.0.0.1 --porta $PORTA --utente $U --parola provanic2026 --resta 40 > /tmp/cliente-$U.log 2>&1 &
for i in $(seq 100); do pgrep -u $U -x plasmashell >/dev/null && break; sleep 0.25; done
sleep 3
R=/run/user/$(id -u $U); S=$(ls $R | grep -E '^wayland-[0-9]+$' | head -1)
W=$(readlink -f $(command -v wayland-info))
echo "wayland-info canonico: $W · socket $S"
echo "--- SENZA .desktop:"
runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>&1 | grep -cE "interface:"; runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>&1 | grep -E "zkde_screencast|org_kde_kwin_keystate|interface: .wl_output" | sed 's/^/   /'
cat > /usr/share/applications/org.kde.remotix-sonda.desktop <<D
[Desktop Entry]
Type=Application
Name=sonda
Exec=$W
NoDisplay=true
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1,org_kde_kwin_keystate
D
sleep 3
echo "--- CON .desktop in /usr/share/applications (scritto a sessione GIA' viva, +3 s):"
runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>&1 | grep -E "zkde_screencast|org_kde_kwin_keystate" | sed 's/^/   /'
echo "--- XDG_MENU_PREFIX di kwin: $(tr '\0' '\n' < /proc/$(pgrep -u $U -x kwin_wayland)/environ | grep XDG_MENU_PREFIX)"
rm -f /usr/share/applications/org.kde.remotix-sonda.desktop
loginctl terminate-user $U
