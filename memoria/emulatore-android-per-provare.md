---
name: emulatore-android-per-provare
description: "Android is not tested on Nic's phone: there is an emulator with Firefox 154 on the laptop, and bench 07-b59 does the round by itself"
metadata:
  type: project
---

⛔ **21 Aug 2026, and Nic imposed it**: *«non sei in grado di far funzionare
Firefox per android con remotix»* after **six rounds of tests on his phone**,
then *«Installa la suite android sdk, usa quella»*.

⇒ **Android is not tested by asking him.** On the laptop there is:

| | |
|---|---|
| SDK | `~/Android/Sdk` (cmdline-tools, platform-tools, emulator, `system-images;android-34;google_apis;x86_64`) |
| machine | AVD **`remotix`** (pixel_6), starts headless with KVM |
| browser | **Firefox 154.0 for Android** installed — the same version as Nic's phone |
| bench | `banchi/07-b59-firefox-android.py` — starts, accepts the certificate, logs in as «prova», measures, takes pictures, **and shuts everything down** |

⚠ **What the emulator does NOT reproduce, and it must be declared**: hardware
decoding. ⇒ The delay **numbers** do not count; the **behaviour** does —
whether it paints or not, whether it stops or not, and why.

⭐ And the desktop sibling: `banchi/07-b58-senza-webcodecs.py` removes WebCodecs from
a normal Firefox with `dom.media.webcodecs.enabled=false`. It catches almost everything,
⛔ but not the presentation rules of the mobile engines — those only `07-b59`.

⛔ **The lesson, which is about method**: when a test requires more than one round from
a person, the wrong tool is not the product — it is the bench. See
[[la-prova-la-fa-lutente]], which stays true for the **judgment**, not for the
diagnosis.

See [[le-prove-le-eseguo-io]], [[banchi-in-parallelo-isolamento]].
