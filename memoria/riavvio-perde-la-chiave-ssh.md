---
name: riavvio-perde-la-chiave-ssh
description: "Il rootfs di 192.168.0.2 vive in RAM: ogni riavvio cancella authorized_keys, e nessun banco entra più finché Nic non ricopia la chiave"
metadata:
  type: project
---

La macchina di prova (`192.168.0.2`) ha il **rootfs in RAM** (`DECISIONI.md:769`). ⇒ Un riavvio non
porta via solo gli utenti di prova e il linger — porta via anche **`~/.ssh/authorized_keys` di
`nicfio`**. Sintomo: `ssh` risponde `Permission denied (publickey,password)` mentre il ping passa.

**Why:** tutti i banchi entrano con `ssh -o BatchMode=yes` (nessuno digita niente), quindi **nessuna
misura è possibile** finché la chiave non torna. Il 23 agosto 2026, aprendo la fase 9, questo ha
fermato tutto al primo passo — e la diagnosi «la macchina è spenta» era sbagliata: rispondeva.

**How to apply:**
- il gesto è **di Nic**, una riga sola, e va chiesto subito invece di girarci attorno:
  `ssh-copy-id -i ~/.ssh/id_ed25519.pub nicfio@192.168.0.2` (parola d'ordine in `~/SERVER.ssh`);
- ⛔ **e non basta**: dopo un riavvio va anche **riprovisionata** la macchina —
  `sudo bash src/provisiona.sh`, poi `sudo bash src/provisiona.sh verifica`. Gli utenti `prova` e
  `prova2`, i gruppi `video`/`render`, polkit e i drop-in **non sopravvivono al riavvio**;
- ⇒ dopo ogni riavvio l'ordine è: **chiave → provisiona → verifica → misura**, e solo allora i
  numeri valgono. Vedi [[costruire-serve-il-contenitore]] e [[la-prova-la-fa-lutente]].
