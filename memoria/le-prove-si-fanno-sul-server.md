---
name: le-prove-si-fanno-sul-server
description: Nic's rule, 28 Aug 2026 — tests run on the test machine, never on the tablet; on the tablet you write and compile
metadata:
  type: feedback
---

**«Le prove si fanno sul server, non sul tablet»** — Nic, 28 Aug 2026, while the
tablet was being emptied.

**Why:** the tablet is a CHUWI Hi10 X1 with 7.5 GB of RAM and an N100 with 4 threads; the
test machine is an i5-13500T with 20 threads and 31 GB. ⛔ A number measured on the
tablet says nothing about the product: it says something about the tablet. ⇒ And the tablet does not need to
keep installed **anything** of what is needed to RUN the benches.

**How to apply:**

- on the tablet you **write** and **compile** (podman, `remotix-costruzione`); on the
  test machine you **run** (`fondamenta/banco/enter.sh`).
  See [[costruire-serve-il-contenitore]].
- the benches' dependencies are installed **there**, with `fondamenta/banco/provision.sh`,
  ⛔ not by hand on the tablet — the bench itself says so when `cargo` is missing.
- ⇒ 28 Aug 2026: removed Rust from the tablet (1.3 GB, a leftover of v1 which was in Rust), our
  two podman images and 3.3 GB of bench outputs scattered in home and in
  `/var/tmp`. From 41 to 33 GB.

⭐ **The exception, and it is not an exception:** the Android SDK and the emulator stay on the
tablet. `DECISIONI.md` §5-bis.0-ter, 9 Aug 2026: *«sull'emulatore si sviluppa,
non si misura — nessun numero di questo progetto viene dichiarato su un
emulatore»*. ⇒ It is not a bench: it is a development environment, and it is consistent with this
rule instead of contradicting it. See [[emulatore-android-per-provare]].

⚠ And the reverse, which stays true: [[la-prova-la-fa-lutente]] — the final judgment is
given neither by the tablet nor by the server, it is given by Nic looking at the screen.
