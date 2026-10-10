---
name: credenziali-da-rigenerare
description: on 28 Aug 2026 the server credentials had been DELETED from the tablet; REDONE on 18 Sep 2026 (new key, password unchanged)
metadata:
  type: project
---

⭐ **REDONE on 18 Sep 2026**: `~/SERVER.ssh` (lines `host:` `user:` `pass:`), new `ed25519` key, installed on the server. The server's password **stayed `nicfio`** — see [[deposito-su-github]]. The complete recipe is in [[riavvio-perde-la-chiave-ssh]].

~~On the tablet there is no longer any server credential.~~ (true from 28 Aug to 18 Sep 2026) Deleted on 28 Aug
2026 by Nic's decision — *«le rigenereremo quando il server tornera' disponibile»* —
before the cleanup of the machine.

Deleted (overwritten, not just unlinked): `~/SERVER.ssh`, `~/.ssh/id_ed25519`
and the public one, the TLS certificates in `~/.local/state/remotix/` and in `~/.remotix-f26/`.
⭐ **Kept on purpose**: access to GitHub (`~/.config/gh/hosts.yml`) and to Claude
(`~/.claude/.credentials.json`): git talks to GitHub over **HTTPS with the `gh` token**,
not with the ssh key, so deleting it did not touch the repository.

## ⛔ The bill to pay, and it is not a defect

`fondamenta/strumenti/sshpw.py` reads `~/SERVER.ssh`, and **46 calls** go through
it. As long as the credential is not there, those benches **do not reach the machine**:
it is intended, it is not a fault to diagnose.

## When the server comes back — in order

1. `ssh-keygen -t ed25519` — new key on the tablet (or on the new machine).
2. New password on the server, and rewritten in `~/SERVER.ssh` (one line).
3. `ssh-copy-id -i ~/.ssh/id_ed25519.pub nicfio@192.168.0.2` — and ⚠ it must be redone at
   **every reboot**: the rootfs is live in RAM. See [[riavvio-perde-la-chiave-ssh]].
4. ⛔⛔ **The 9 bench files with the `sudo` password in clear text**
   (`printf 'nicfio\n' | sudo -S ...`) must be redone in the same round: with a
   new password on the server they stop working anyway, ⇒ it is the
   right moment to have them **read it from a file** instead of writing it inside.
   ⭐ It is also the only thing that separates the repository from being able to become public.
   See [[deposito-su-github]].
