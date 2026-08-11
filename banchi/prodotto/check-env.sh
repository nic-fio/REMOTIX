#!/bin/bash
# Verifica dell'ambiente di sviluppo REMOTIX, eseguita DENTRO il contenitore.
echo "sistema:  $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)"
echo "rustc:    $(rustc --version 2>&1)"
echo "cargo:    $(cargo --version 2>&1)"
echo "gcc:      $(gcc --version 2>&1 | head -1)"
echo "clang:    $(clang --version 2>&1 | head -1)"
echo
echo "librerie di sviluppo:"
for m in wayland-server wayland-client libva libva-drm libdrm libpipewire-0.3 \
         xkbcommon vulkan gbm egl libsystemd dbus-1 openssl; do
    printf "  %-18s %s\n" "$m" "$(pkg-config --modversion "$m" 2>/dev/null || echo MANCANTE)"
done
echo
echo "PAM:      $(ls /usr/include/security/pam_appl.h >/dev/null 2>&1 && echo presente || echo MANCANTE)"
echo "GPU:      $(ls /dev/dri/ 2>/dev/null | tr '\n' ' ')"
echo "sorgenti: /srv/src -> $(stat -c '%U:%G modo %a' /srv/src 2>&1)"
echo "spazio:   $(df -h /srv/src | tail -1 | awk '{print $4" liberi"}')"
