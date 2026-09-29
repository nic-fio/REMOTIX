#!/bin/sh
# I nomi dei gruppi del desktop del catalogo (pacchetti_desktop) esistono davvero? Si chiede al
# gestore di ogni famiglia, in un contenitore, SENZA installare: dnf install --assumeno, zypper
# install --dry-run, pacman -Sp. Uscita: una riga per nome, «si» o «no».
set -u
f44='for g in @workstation-product-environment @kde-desktop-environment @xfce-desktop-environment @lxqt-desktop-environment; do if dnf install --assumeno "$g" 2>&1 | grep -q "Installing"; then echo "fedora44 $g si"; else echo "fedora44 $g NO"; fi; done'
alma='dnf -q install -y epel-release >/dev/null 2>&1; dnf -q config-manager --set-enabled crb; for g in @graphical-server-environment @kde-desktop-environment; do if dnf install --assumeno --allowerasing "$g" 2>&1 | grep -q "^Installing"; then echo "alma10 $g si"; else echo "alma10 $g NO"; fi; done'
tw='zypper -q ref >/dev/null 2>&1; for g in pattern:gnome pattern:kde pattern:xfce pattern:lxqt; do if zypper -n install --dry-run "$g" 2>&1 | grep -q "NEW package"; then echo "tumbleweed $g si"; else echo "tumbleweed $g NO"; fi; done'
arch='pacman -Sy >/dev/null 2>&1; for g in gnome plasma xfce4 xfce4-goodies lxqt breeze-icons; do n=$(pacman -Sp --print-format %n "$g" 2>/dev/null | wc -l); if [ "$n" -gt 0 ]; then echo "arch $g si ($n)"; else echo "arch $g NO"; fi; done'
podman run --rm registry.fedoraproject.org/fedora:44 sh -c "$f44"
podman run --rm docker.io/library/almalinux:10 sh -c "$alma"
podman run --rm registry.opensuse.org/opensuse/tumbleweed:latest sh -c "$tw"
podman run --rm docker.io/library/archlinux:latest sh -c "$arch"
