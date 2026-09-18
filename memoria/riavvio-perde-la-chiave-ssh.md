---
name: riavvio-perde-la-chiave-ssh
description: "Il rootfs di 192.168.0.2 vive in RAM: ogni riavvio cancella chiave, pacchetti, utenti; e dal 18 set 2026 la ricetta per rifare il server DA ZERO"
metadata:
  type: project
---

La macchina di prova (`192.168.0.2`, hostname `NIC-OS`) ha il **rootfs in RAM** (avvia `live.img`
da `/mnt`, ~210 pacchetti, niente GNOME). ⇒ Un riavvio porta via `authorized_keys`, gli utenti di
prova, polkit, i drop-in, **e tutti i pacchetti installati** (GNOME, podman, python3). Resta solo
quel che sta sui dischi: `/media` (NVMe) e `/srv` (sda), che l'utente monta a mano dopo l'avvio.

**Why:** i banchi entrano con `ssh -o BatchMode=yes`; senza chiave nessuna misura è possibile, e la
diagnosi «la macchina è spenta» è sbagliata: il ping risponde.

## ⭐ La ricetta, provata il 18 settembre 2026 — server ripartito DA ZERO

Quel giorno `/media/REMOTIX` **non c'era più**: l'aveva cancellato l'utente stesso (con
`/media/root`) prima di chiamarmi. ⇒ Si è rifatto tutto, e l'ordine giusto è questo:

0. ⛔ **la strada verso internet**: il profilo di NetworkManager dice gateway `192.168.0.1` ma la
   rotta di default **non c'era** ⇒ `apt` falliva con «does not have a Release file».
   Cura volatile: `sudo ip route add default via 192.168.0.1 dev enp6s0`.
1. **chiave**: `~/SERVER.ssh` sul tablet (tre righe `host:` `user:` `pass:`; la parola è ancora
   `nicfio`), `ssh-keygen -t ed25519`, e la pubblica in `authorized_keys` passando da
   `fondamenta/strumenti/sshpw.py`.
2. **contenitore di compilazione**: copiare `fondamenta/banco/*.sh` in `/media/REMOTIX/` e lanciare
   `provision.sh` (mmdebstrap trixie → `devroot`, ~4 min). ⚠ Serve un **pty** perché `sudo` resti
   valido: `ssh -tt … 'printf "nicfio\n" | sudo -S -v && bash …'`.
3. **ngtcp2 1.25 / nghttp3 1.18** in `/media/REMOTIX/src/b2` (stesse versioni di `src/Contenitore`;
   nghttp3 in `b2/prefisso`, ngtcp2 costruita in `b2/ngtcp2/build`) — dentro `enter.sh`.
4. **prodotto**: `git archive HEAD src banchi/rcp` in `src/04-vero-src/`, poi
   `enter.sh "bash /srv/src/04-vero-src/src/costruisci.sh"`. Le tre librerie vanno **copiate** in
   `src/04-vero-src/src/lib-remotix/`, che `provisiona.sh` registra con `ldconfig`.
5. **pacchetti dell'ospite**: l'elenco `PKGS` di `fondamenta/banco/provision-server.sh` + `podman
   crun netavark fuse-overlayfs uidmap python3 nftables rsync git`, con la cache in
   `/media/REMOTIX/cache/apt-host`.
6. `sudo bash src/provisiona.sh` e poi `… verifica` ⇒ deve dire «la macchina e' nello stato che il
   prodotto si aspetta» (dal 18 set scrive anche la regola dei **quattro comandi senza password** dei banchi, ✅ decisa dall'utente: senza, il gancio remoto si blocca al primo `sudo`). ⚠ `gpu-udev.sh` deve essere **eseguibile** in `/media/REMOTIX/`.
7. **scatole**: `/etc/containers/storage.conf` con `graphroot = /media/REMOTIX/contenitori/storage`
   (così le immagini **sopravvivono** al riavvio; il file in `/etc` no, va riscritto);
   `/media/REMOTIX/rete11/` = `banchi/11-scatole/*` + `10-f1-testimone.py` +
   `attrezzi-gruppi-scheda.sh` + `prodotto/{remotix,pagina.html,remotix.pam,01-b3-cliente.py,lib/}`;
   poi `11-accendi.sh costruisci|accendi|passo0|prodotto|server <desktop>` per i quattro.
8. ⛔ **la rete si lancia SUL SERVER**, non dal tablet: `gira` dal tablet non trova nessuna scatola
   e dà tutto «non ho potuto guardare». Sul server:
   `sudo systemd-run --unit=… bash /media/REMOTIX/rete11/11-gancio.sh gira --famiglia tutto`.

Vedi [[credenziali-da-rigenerare]], [[costruire-serve-il-contenitore]], [[la-prova-la-fa-lutente]].
