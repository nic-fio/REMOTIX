# The NVIDIA bench — read before renting

It is used to test REMOTIX on a real NVIDIA card, in one or two days of rental, without
improvising: from the laptop you launch one command, the bench does everything by itself and brings home the
evidence. (`fasi/19-nvidia.md` §2.4.)

## What to rent

- **A whole machine, or a virtual machine with the whole card passed through.** ⛔ Not a
  "container with GPU" (like vast.ai, RunPod): there you do not own the machine, and REMOTIX
  wants systemd, real users and `/dev/dri`.
- **The card: NVIDIA RTX 20 series / T4 or newer, with the video encoder.** T4, L4,
  L40S, A10, A16, RTX 4000/6000 Ada, RTX 30 and 40 are fine. ⛔ **Not A100, H100, H200**: they are compute cards
  without a video encoder, and the bench would stop right away.
- **The system: Ubuntu 26.04 or Debian 13, if the rental company offers them; otherwise the most
  recent Ubuntu it offers, from 20.04 up.** REMOTIX does not run on old Ubuntu releases (their OpenSSL is
  too old), but the bench brings the system to 26.04 by itself before starting, one hop at a
  time: about an hour per hop (from 24.04 one, from 22.04 two, from 20.04 three) and the reboots, which
  it does by itself. ⛔ The machine is returned upgraded: the cleanup does not undo this.
- **NVIDIA driver 550 or newer.** If the machine arrives without it, the bench installs it (and reboots it
  by itself once).
- **Root access via ssh**, or a user with passwordless `sudo` (for example `ubuntu`).
- At least 30 GB of free disk and 8 GB of memory (under 12 GB the bench adds 4 GB of
  swap on disk by itself, and removes it at the end). No monitor needed.

## The day before, on the laptop (once only)

From the REMOTIX folder, on the `fase-19` branch:

    bash banchi/19-nvidia/19-nvidia.sh prepara

It builds the REMOTIX packages and the installer, and puts everything in a "suitcase". About twenty
minutes.

## The rental day

    bash banchi/19-nvidia/19-nvidia.sh tutto ADDRESS

(with a user other than root: `UTENTE=ubuntu bash banchi/19-nvidia/19-nvidia.sh tutto ADDRESS`;
with a particular ssh key: `CHIAVE=~/.ssh/noleggio`.)

The bench, in order: brings Ubuntu to 26.04 if it is older · looks at the card and the driver · installs the driver if missing · installs the light
desktop (XFCE) and the two browsers · installs REMOTIX **with its installer** · checks that it encodes
H.264 and HEVC on the NVIDIA · runs the encoding comparison bench · runs the suite's
tests (login, first image, screen update, canvas at attach, video, detach and
reattach, reattach at a different size) with real Firefox and Chrome · packs the evidence and brings it
to the laptop, in `misure/19-nvidia/`.

You do not need to stay in front of it: if the connection drops the bench goes on, and you find it again with
`bash banchi/19-nvidia/19-nvidia.sh segui ADDRESS`.

**How long it takes, roughly:** half a day. Driver and programs from half an hour to an hour (it depends on the machine's
network), the encoding comparison up to an hour, the suite a couple of hours. One day of
rental is enough; the second is margin.

## At the end

1. The evidence is already on the laptop (`misure/19-nvidia/remotix-nv-….tar.gz`); inside, `passi.txt`
   says in one line per step what is green and what is not.
2. `bash banchi/19-nvidia/19-nvidia.sh pulisci ADDRESS` — removes REMOTIX, the bench users,
   all the programs the bench installed (driver included, if it installed it) and puts the repositories back
   as they were. It refuses if the evidence has not been taken away yet.
3. Return the machine.

## If something goes wrong

- `bash banchi/19-nvidia/19-nvidia.sh stato ADDRESS` says which step was reached.
- Resume with `tutto` again: steps already done are skipped.
- Red initial checks stop everything (for example: the card has no encoder, or the system
  is not Debian 13 / Ubuntu 22.04-26.04). The reason is in `controlli.txt`, inside the evidence.
