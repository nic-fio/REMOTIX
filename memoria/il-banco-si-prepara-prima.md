---
name: il-banco-si-prepara-prima
description: "«Non chiamarmi se non funziona» — the scene is prepared and LOOKED AT before asking for a judgment, and a counter is not looking"
metadata:
  type: feedback
---

⭐ **25 Aug 2026, phase 10.** I had given him address and credentials asking him
to look at the product. He, three times, until he stopped: *«Firefox non
funziona»* · ⛔ **«senza Firefox nessun test di rilievo ha senso, quindi non
chiamarmi se non funziona»** · *«io non faccio più niente, non posso fare test in
queste condizioni»*.

⛔⛔ **And then the correction that brings everything back into focus**:

> **«Il Firefox che deve funzionare è quello del SERVER, non quello del tablet.»**

⇒ It is not a bench nuisance: ⛔ **a remote desktop in which a browser
does not open is not a remote desktop.** It is the product as seen by the user.

⛔ **And the serious part was not the browser: it was that I did not know it.** I tried
**four roads** to see the image of that desktop — the child's internal
snapshot (`SIGUSR1`), the screenshot (GNOME does not give it), the page's
canvas via Marionette, the frame count — and ⛔ **none gave me the
picture**. I declared the scene ready **without having looked at it**.

**Why:** his judgment is invariant I8, that is the ultimate meter of the product —
⛔ **and every empty call consumes a piece of it.** It is the only tool of the
project that cannot be rebuilt. His time is for **looking**, not for starting
things up nor for discovering that they are broken.

**How to apply:**
- ⛔ **before calling him, LOOK at the scene yourself**: not «the process is alive», not
  «493 frames have gone through» — ⭐ **the image**. *493 black frames are
  493 frames*;
- ⭐ **the witness that shows is calibrated like every meter**: put in the desktop
  a **recognisable mark** (`04-b30-scena --giro NOME`) and verify that the
  witness finds it, ⛔ **plus the negative control**: with the desktop black it must
  say «black», not return just any image;
- ⛔ **if it could not look it must return «I don't know», never an empty
  image**: *«I did not look»* is not *«it is black»*;
- if the scene cannot be prepared, ⭐ **report the gap** — which
  roads I tried, where each one stopped, what would be needed — and **do not
  ask him to try it himself**.

⚠ **And a premise I had got wrong**: the test machine has no screen, and
from this I had concluded *«the browser must run on his computer»*. ⛔ False:
the browser must run **inside the remote session**, which does have a screen —
it is the one the product serves.

See [[la-prova-la-fa-lutente]], [[le-prove-le-eseguo-io]],
[[come-guarda-nic-lo-schermo]], [[nic-regista-non-programmatore]],
[[testimone-sul-desktop-vero]].
