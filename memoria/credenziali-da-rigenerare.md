---
name: credenziali-da-rigenerare
description: 28 ago 2026 le credenziali del server sono state CANCELLATE dal tablet; si rifanno quando la macchina torna, e finche' non si rifanno i banchi non la raggiungono
metadata:
  type: project
---

**Sul tablet non c'e' piu' nessuna credenziale del server.** Cancellate il 28 agosto
2026 per decisione di Nic — *«le rigenereremo quando il server tornera' disponibile»* —
prima della pulizia della macchina.

Cancellati (sovrascritti, non solo scollegati): `~/SERVER.ssh`, `~/.ssh/id_ed25519`
e la pubblica, i certificati TLS in `~/.local/state/remotix/` e in `~/.remotix-f26/`.
⭐ **Restano apposta** l'accesso a GitHub (`~/.config/gh/hosts.yml`) e a Claude
(`~/.claude/.credentials.json`): git parla con GitHub in **HTTPS col gettone `gh`**,
non con la chiave ssh, quindi cancellarla non ha toccato il deposito.

## ⛔ Il conto da pagare, e non e' un difetto

`fondamenta/strumenti/sshpw.py` legge `~/SERVER.ssh`, e **46 richiami** passano di
li'. Finche' la credenziale non c'e', quei banchi **non raggiungono la macchina**:
e' voluto, non e' un guasto da diagnosticare.

## Quando il server torna — nell'ordine

1. `ssh-keygen -t ed25519` — chiave nuova sul tablet (o sulla macchina nuova).
2. Parola d'ordine nuova sul server, e riscritta in `~/SERVER.ssh` (una riga).
3. `ssh-copy-id -i ~/.ssh/id_ed25519.pub nicfio@192.168.0.2` — e ⚠ va rifatto a
   **ogni riavvio**: il rootfs e' live in RAM. Vedi [[riavvio-perde-la-chiave-ssh]].
4. ⛔⛔ **I 9 file dei banchi con la parola d'ordine `sudo` in chiaro**
   (`printf 'nicfio\n' | sudo -S ...`) vanno rifatti nello stesso giro: con una
   parola d'ordine nuova sul server smettono di funzionare comunque, ⇒ e' il
   momento giusto per fargliela **leggere da un file** invece che scriverla dentro.
   ⭐ E' anche l'unica cosa che separa il deposito dal poter diventare pubblico.
   Vedi [[deposito-su-github]].
