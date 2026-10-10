---
name: riavvio-perde-la-chiave-ssh
description: "The rootfs of 192.168.0.2 lives in RAM: every reboot wipes key, packages, users; and since 18 Sep 2026 the recipe to rebuild the server FROM SCRATCH"
metadata:
  type: project
---

The test machine (`192.168.0.2`, hostname `NIC-OS`) has its **rootfs in RAM** (it boots `live.img`
from `/mnt`, ~210 packages, no GNOME). ⇒ A reboot takes away `authorized_keys`, the test
users, polkit, the drop-ins, **and all installed packages** (GNOME, podman, python3). Only
what is on the disks stays: `/media` (NVMe) and `/srv` (sda), which the user mounts by hand after boot.

**Why:** the benches get in with `ssh -o BatchMode=yes`; without the key no measurement is possible, and the
diagnosis «the machine is off» is wrong: ping answers.

## ⭐ The recipe, tried on 18 Sep 2026 — server restarted FROM SCRATCH

That day `/media/REMOTIX` **was no longer there**: the user himself had deleted it (with
`/media/root`) before calling me. ⇒ Everything was redone, and the right order is this:

0. ⛔ **the road to the internet**: the NetworkManager profile says gateway `192.168.0.1` but the
   default route **was not there** ⇒ `apt` failed with «does not have a Release file».
   Volatile cure: `sudo ip route add default via 192.168.0.1 dev enp6s0`.
1. **key**: `~/SERVER.ssh` on the tablet (three lines `host:` `user:` `pass:`; the password is still
   `nicfio`), `ssh-keygen -t ed25519`, and the public one into `authorized_keys` going through
   `fondamenta/strumenti/sshpw.py`.
2. **build container**: copy `fondamenta/banco/*.sh` into `/media/REMOTIX/` and run
   `provision.sh` (mmdebstrap trixie → `devroot`, ~4 min). ⚠ A **pty** is needed for `sudo` to stay
   valid: `ssh -tt … 'printf "nicfio\n" | sudo -S -v && bash …'`.
3. **ngtcp2 1.25 / nghttp3 1.18** in `/media/REMOTIX/src/b2` (same versions as `src/Contenitore`;
   nghttp3 in `b2/prefisso`, ngtcp2 built in `b2/ngtcp2/build`) — inside `enter.sh`.
4. **product**: `git archive HEAD src banchi/rcp` into `src/04-vero-src/`, then
   `enter.sh "bash /srv/src/04-vero-src/src/costruisci.sh"`. The three libraries must be **copied** into
   `src/04-vero-src/src/lib-remotix/`, which `provisiona.sh` registers with `ldconfig`.
5. **host packages**: the `PKGS` list of `fondamenta/banco/provision-server.sh` + `podman
   crun netavark fuse-overlayfs uidmap python3 nftables rsync git`, with the cache in
   `/media/REMOTIX/cache/apt-host`.
6. `sudo bash src/provisiona.sh` and then `… verifica` ⇒ it must say «la macchina e' nello stato che il
   prodotto si aspetta» (since 18 Sep it also writes the rule of the benches' **four commands without password**, ✅ decided by the user: without it, the remote hook gets stuck at the first `sudo`). ⚠ `gpu-udev.sh` must be **executable** in `/media/REMOTIX/`.
7. **boxes**: `/etc/containers/storage.conf` with `graphroot = /media/REMOTIX/contenitori/storage`
   (so the images **survive** the reboot; the file in `/etc` does not, it must be rewritten);
   `/media/REMOTIX/rete11/` = `banchi/11-scatole/*` + `10-f1-testimone.py` +
   `attrezzi-gruppi-scheda.sh` + `prodotto/{remotix,pagina.html,remotix.pam,01-b3-cliente.py,lib/}`;
   then `11-accendi.sh costruisci|accendi|passo0|prodotto|server <desktop>` for the four.
8. ⛔ **the net is launched ON THE SERVER**, not from the tablet: `gira` from the tablet finds no box
   and gives everything «non ho potuto guardare». On the server:
   `sudo systemd-run --unit=… bash /media/REMOTIX/rete11/11-gancio.sh gira --famiglia tutto`.

See [[credenziali-da-rigenerare]], [[costruire-serve-il-contenitore]], [[la-prova-la-fa-lutente]].
