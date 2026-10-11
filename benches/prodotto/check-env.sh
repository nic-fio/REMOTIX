#!/bin/bash
# Check of the REMOTIX development environment, run INSIDE the container.
echo "system:   $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)"
echo "rustc:    $(rustc --version 2>&1)"
echo "cargo:    $(cargo --version 2>&1)"
echo "gcc:      $(gcc --version 2>&1 | head -1)"
echo "clang:    $(clang --version 2>&1 | head -1)"
echo
echo "development libraries:"
for m in wayland-server wayland-client libva libva-drm libdrm libpipewire-0.3 \
         xkbcommon vulkan gbm egl libsystemd dbus-1 openssl; do
    printf "  %-18s %s\n" "$m" "$(pkg-config --modversion "$m" 2>/dev/null || echo MISSING)"
done
echo
echo "PAM:      $(ls /usr/include/security/pam_appl.h >/dev/null 2>&1 && echo present || echo MISSING)"
echo "GPU:      $(ls /dev/dri/ 2>/dev/null | tr '\n' ' ')"
echo "sources:  /srv/src -> $(stat -c '%U:%G mode %a' /srv/src 2>&1)"
echo "space:    $(df -h /srv/src | tail -1 | awk '{print $4" free"}')"
