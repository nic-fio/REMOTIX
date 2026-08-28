---
name: emulatore-android-per-provare
description: "Android non si prova sul telefono di Nic: c'è un emulatore con Firefox 154 sul portatile, e il banco 07-b59 fa il giro da solo"
metadata:
  type: project
---

⛔ **21 agosto 2026, e l'ha imposto Nic**: *«non sei in grado di far funzionare
Firefox per android con remotix»* dopo **sei giri di prove sul suo telefono**,
poi *«Installa la suite android sdk, usa quella»*.

⇒ **Android non si prova chiedendo a lui.** Sul portatile c'è:

| | |
|---|---|
| SDK | `~/Android/Sdk` (cmdline-tools, platform-tools, emulator, `system-images;android-34;google_apis;x86_64`) |
| macchina | AVD **`remotix`** (pixel_6), si accende headless con KVM |
| browser | **Firefox 154.0 per Android** installato — la stessa versione del telefono di Nic |
| banco | `banchi/07-b59-firefox-android.py` — accende, accetta il certificato, entra come «prova», misura, fotografa, **e spegne tutto** |

⚠ **Quel che l'emulatore NON riproduce, e va dichiarato**: la decodifica in
hardware. ⇒ I **numeri** del ritardo non valgono; vale il **comportamento** —
dipinge o no, si ferma o no, e perché.

⭐ E il fratello da tavolo: `banchi/07-b58-senza-webcodecs.py` toglie WebCodecs a
un Firefox normale con `dom.media.webcodecs.enabled=false`. Prende quasi tutto,
⛔ ma non le regole di presentazione dei motori mobili — quelle solo `07-b59`.

⛔ **La lezione, che è di metodo**: quando una prova richiede più di un giro di
una persona, lo strumento sbagliato non è il prodotto — è il banco. Vedi
[[la-prova-la-fa-lutente]], che resta vera per il **giudizio**, non per la
diagnosi.

Vedi [[le-prove-le-eseguo-io]], [[banchi-in-parallelo-isolamento]].
