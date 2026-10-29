# The NVIDIA bench — read before renting

It is used to test REMOTIX on a real NVIDIA card, in one or two days of rental, without
improvising: from the laptop you launch one command, the bench does everything by itself and brings home the
evidence. (`phases/19-nvidia.md` §2.4.)

## Where the browsers are (CLIENTS)

⭐ 27 Oct 2026. By default (`CLIENTS=home`) the machine runs **only what a customer's server runs**: REMOTIX and the
desktop. The browsers of the tests stay at home, on the home server (192.168.0.2), which connects over internet
like a real user. So the bench measures the NVIDIA card without the browsers on its back, and the real network:
open ports, traffic from outside, the delay of internet.

- **Ask the provider**: the machine must accept **inbound TCP and UDP on port 7447** (REMOTIX's port) from our
  address. Many providers close UDP by default (a "security group" or firewall in their panel, outside the machine,
  that the bench cannot see or change). Without UDP REMOTIX does not talk: the step `porta` and the first login
  of the suite say so.
- On the machine the step `porta` opens the port **only towards the address ssh comes from** (read from ssh itself,
  no external service; `CLIENT_ADDR=…` forces it, for example behind a jump host), **only if** a firewall is active
  there (ufw or nftables); the rule is recorded and `clean` removes it. It also checks that REMOTIX listens on a
  non-loopback address.
- **The fallback**: if the provider will not open UDP, `CLIENTS=machine` (on every command) does what the bench has
  always done: Firefox and Chrome installed on the machine, the suite run there, in a labwc without screen.
  Say it in the results: that run measures the card with the browsers on it.

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

    bash benches/19-nvidia/19-nvidia.sh prepare

The rest of the rental runs **on the home server** (not on the tablet: it freezes with long jobs), with the ssh key
of the rented machine on it.

It builds the REMOTIX packages and the installer, and puts everything in a "suitcase". About twenty
minutes.

## The rental day

The order, `CLIENTS=home` (default). On the home server:

    bash benches/19-nvidia/19-nvidia.sh all ADDRESS          # 1. the machine: everything, up to REMOTIX ready
    bash benches/19-nvidia/19-nvidia.sh suite-casa ADDRESS   # 2. the tests, with the browsers at home
    bash benches/19-nvidia/19-nvidia.sh collect ADDRESS      # 3. the evidence archive, here
    bash benches/19-nvidia/19-nvidia.sh clean ADDRESS        # 4. the machine as found

(with a user other than root: `ACCOUNT=ubuntu bash …`; with a particular ssh key: `SSH_KEY=~/.ssh/noleggio`.)

**1. `all`** (on the machine, in a systemd unit): brings Ubuntu to 26.04 if it is older · looks at the card and the
driver · installs the driver if missing · installs the light desktop (XFCE) **without browsers** · installs REMOTIX
**with its installer** · opens the port towards us (`porta`) · checks that it encodes H.264 and HEVC on the NVIDIA ·
runs the encoding comparison bench. It stops there: it does not run the suite and does not collect (the evidence
is collected after the suite). With `CLIENTS=machine` it also installs Firefox and Chrome, runs the suite and
collects, as it has always done.

**2. `suite-casa`** (on the home server): first it checks that the server is free (the preflight of the nightly
chains, profile suite: no test or chain alive, free ports, compositors on — if another measurement is running it
stops, it never interrupts it; `PREFLIGHT=skip` skips it and the evidence says so), measures the delay towards the
machine (ping) and **writes it down**, checks that the port answers from outside (TCP and REMOTIX's page over https),
reads the machine's clock, and then runs the tests (login, first image, screen update, canvas at attach, video,
detach and reattach, reattach at a different size) with real Firefox and Chrome **here**, in the headless labwc of
the desktop (`15-compositors.sh`), connected to `ADDRESS:7447`. What the tests do "inside the desktop" (commands,
scenes, reading REMOTIX's log) goes over ssh to the machine (one shared connection). The evidence is in
`measurements/19-nvidia/suite-casa-<date>/` and is also sent to the machine, so that `collect` has it in the archive.
`passi.txt` gets the line «browsers at home, RTT N ms, …». About two hours; **the home server is busy** for that
time: no performance measures here meanwhile.

**The delay and the limits.** The tests have time limits designed for a local network. The only one the suite lets
one change is `--cap-s` (login and first image, 45 s): if the round trip is above `RTT_WIDEN_MS` (30 ms) it grows by
RTT/5 seconds, and the line in `passi.txt` and `rete.txt` say so. The others (for example the age of the image in F-003,
1000 ms) are **not** widened: with internet some of them may fail for the delay, and that is read as such, with the
RTT and the clock offset (`rete.txt`) next to it. F-003 compares the clock of the scene inside the desktop (the
machine's) with the home server's: with more than 100 ms of difference `suite-casa` warns.

**3. `collect`**, **4. `clean`**: as below. `clean` also removes the firewall rule `porta` added.

⭐ 1.5 (26 Oct 2026), right after `all`, the two things 1.5 has never run on an NVIDIA card: KDE (born inside a
headless labwc since 10 Oct, and the «unchanged» filter of the capture) and the device modes:

    REDO="deps" DESKTOP_NV=kde bash benches/19-nvidia/19-nvidia.sh start ADDRESS all
    DESKTOP_NV=kde bash benches/19-nvidia/19-nvidia.sh suite-casa ADDRESS

(`deps` installs Plasma for KDE; the second command runs the suite on KDE from home.)

and read `evidenze/dev-nvidia.txt`, `nvidia-params.txt` (a mode other than 0666 is the black-desktop risk of
DECISIONS-11 §11.38) and `apparmor.txt`.  Rent an Ada card (RTX 40, L4, L40S) if you can: zero copy was measured on Ada only.

You do not need to stay in front of it: if the connection drops the machine's bench goes on, and you find it again with
`bash benches/19-nvidia/19-nvidia.sh follow ADDRESS`. `suite-casa` instead runs in the foreground on the home server:
launch it in the background with the output on a file.

**How long it takes, roughly:** half a day. Driver and programs from half an hour to an hour (it depends on the machine's
network), the encoding comparison up to an hour, the suite a couple of hours. One day of
rental is enough; the second is margin.

## Trying `suite-casa` before the rental (no NVIDIA)

Against one of the home containers acting as the "machine" (the product runs in `rete11-xfce` on 8513; "inside" is
`sudo podman exec` into it, the log is `/var/lib/rete11/registro.log`). Only when the net's measurements are over (it
uses the server's browsers and the preflight asks for a free server):

    CONTAINER=rete11-xfce PORT=8513 bash benches/19-nvidia/19-nvidia.sh suite-casa 192.168.0.2

The 7 tests with Firefox and Chrome must come out green, as in the home suite. Nothing is sent to a machine; the
evidence stays in `measurements/19-nvidia/suite-casa-<date>/`. `19-nv-test-in-container.sh` (a debian/ubuntu
container with systemd, `CLIENTS=home` to also try `porta`) covers the machine side.

## At the end

1. `collect ADDRESS` brings the evidence here (`measurements/19-nvidia/remotix-nv-….tar.gz`; with `CLIENTS=machine`
   `all` already did it); inside, `passi.txt` says in one line per step what is green and what is not, `suite-casa`
   included.
2. `bash benches/19-nvidia/19-nvidia.sh clean ADDRESS` — removes REMOTIX, the bench users,
   all the programs the bench installed (driver included, if it installed it) and puts the repositories back
   as they were. It refuses if the evidence has not been taken away yet.
3. Return the machine.

## If something goes wrong

- `bash benches/19-nvidia/19-nvidia.sh status ADDRESS` says which step was reached.
- Resume with `all` again: steps already done are skipped (`porta` is always redone: a firewall rule does not
  survive a reboot).
- `suite-casa` says NO at the port: the provider's firewall (outside the machine) or the UDP port; see "Where the
  browsers are". The way back is `CLIENTS=machine`.
- Red initial checks stop everything (for example: the card has no encoder, or the system
  is not Debian 13 / Ubuntu 22.04-26.04). The reason is in `controlli.txt`, inside the evidence.
