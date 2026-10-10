---
name: costruire-serve-il-contenitore
description: "How REMOTIX is built: two roads, podman on the laptop to compile and enter.sh on the test machine to run"
metadata:
  node_type: memory
  type: project
  modified: 2026-08-14T23:13:10.891Z
  originSessionId: 704c141d-0a68-4975-8670-6223b9edf97e
---

✅ **Resolved on the night of 15 Aug 2026, without asking the user.** The block
of 14 Aug («non riesco a costruire il C») was **a path mistake**:
inside `bash /media/REMOTIX/enter.sh` the `/srv/src` you see **IS**
the host's `/media/REMOTIX/src` — `enter.sh` mounts it with `--bind`. The sources
had been copied into the **host's** `/srv/src/...`, which is another folder.

⭐ **Two roads, and they answer two different questions:**

| question | road |
|---|---|
| **«compila?»** — twenty seconds, while writing | `bash src/costruisci-in-contenitore.sh` on the laptop: `podman` **as user**, no `sudo`, the tree mounted, the binary comes out **owned by the user**. The image is made once: `podman build -t remotix-costruzione -f src/Contenitore src/` (~4 min: inside are ngtcp2 1.25 and nghttp3 1.18 from source) |
| **«gira?»** — only there | on the test machine: `tar` of the sources into `/media/REMOTIX/src/04-vero-src/`, then `bash /media/REMOTIX/enter.sh --root 'bash /srv/src/04-vero-src/src/costruisci.sh'`, then `sudo -S -p 'Password:' /media/REMOTIX/tmp/riavvia-7700.sh` |

⛔ **The container's binary is NOT copied to the test machine**: it is tied
to the ngtcp2/nghttp3 of `/usr/local` **inside the image**, and there the ones from
`/media/REMOTIX/src/b2` are needed. `riavvia-7700.sh` checks it and refuses to start.

**Why:** «compila» is not «gira», and tonight both were needed ten times:
you write and compile on the laptop, you test on the real machine. The password
for `sudo` on the test machine is the one in `~/SERVER.ssh` and is passed with
`printf 'nicfio\n' | sudo -S -p 'Password: ' -v` **before** calling
`enter.sh`, without redirections around `enter.sh`.

**How to apply:** the page needs no build, it is just copied —
but the server must be **restarted**, because `pagina.c` reads it once at startup.
And to read the log: `sudo -S -p 'Password:' tail /media/REMOTIX/tmp/04-vero/registro.log`.

See [[dex-mouse-aperto]] and `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` §1.
