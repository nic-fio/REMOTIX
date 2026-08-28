---
name: dex-mouse-aperto
description: "Il mouse sul DeX: il sintomo vero è «si muove solo col tasto premuto», è noVNC #1727 e non è nostro — e la cura è «due tele 1:1»"
metadata:
  node_type: memory
  type: project
  originSessionId: 9394ca2b-2373-463b-909d-b459cf512df0
  modified: 2026-08-15T05:47:38.706Z
---

⭐ **Il sintomo vero si è saputo solo la sera del 14 agosto 2026**, con le parole
dell'utente: *«per attivare il puntatore del desktop devo premere il tasto
sinistro; se muovo il mouse il puntatore del server non si muove, se lo muovo
col tasto premuto allora si muove»*.

⇒ È **noVNC #1727** — *«Moving hardware mouse without drag ignored on Chrome
Android»*, aperto dal 2022, specifico di **Samsung**, riprodotto da KasmVNC
#222, Kasm #20 e ⭐ **moonlight-android #573, che è un'app NATIVA**. ⛔ **Non è
nostro e non si cura**: su quel dispositivo i movimenti a pulsanti alzati non
arrivano alla pagina.

⛔ **Le quattro cure della sera sono tutte fuori bersaglio** e sono state
comunque corrette perché erano difetti veri: `CURSORE_FORMA` ricevuta e buttata,
i tre modi del puntatore, **l'84 % dei movimenti spediti due volte** (erano
registrati sia `mousemove` sia `pointermove`), e il clic che non portava la
propria posizione. Nessuna ha cambiato il sintomo.

⭐⭐ **La cura vera l'ha disegnata l'utente**: *«abbiamo due tele, quella del
server e quella del client — bisogna solo convertire le coordinate»*, e poi
*«se i compositori sanno dare la misura esatta, non servono nemmeno le
conversioni»*. ⇒ `DECISIONI.md` **§5.0-sexies**, e il difetto diventa
**innocuo** invece che curato: ogni evento porta la propria posizione, quindi
**puntare e cliccare colpisce giusto anche senza hover**. Si perde solo
l'anteprima (pulsanti che non si illuminano, niente suggerimenti).

⛔ **Due `[?]` sono MORTE, non ripescarle**: `cursor: none` **non** toglie i
movimenti su Android (era `pointermove` che mancava, e in Android
`dispatchPointerEvent()` viene prima di `maybeUpdatePointerIcon()`); e la
cattura del puntatore **peggiora** (`movementX` è ricostruito da Chromium).

**Why:** per due giorni si è curato **un giudizio** — *«è inutilizzabile»* —
invece di **un sintomo**. La domanda che ha risolto tutto era *«che cosa vedi
esattamente succedere?»*, e non è stata fatta. ⚠ E la contraddizione che la
conteneva era nel registro da ore: 213 movimenti registrati dal server mentre
l'utente ne vedeva zero.

**How to apply:** leggere `fasi/rapporti/F4-IN-6-punto-fermo.md` (il punto
fermo) e `F4-IN-7-due-tele.md` (il disegno in byte).

✅ **E la cura è STATA SCRITTA la notte del 15 agosto 2026**: la catena
`figli_ritela()` → `cattura_ridimensiona()` c'è, e `[M]` la tela del server
prende la misura della finestra (1264×800), la scala di disegno vale **1,000**
(`pixelated`) e GNOME *Impostazioni → Displays* **dentro la sessione remota**
dichiara «Resolution 1264 × 800». ⇒ Puntare e cliccare colpisce, e il testo non
è più interpolato. Il rapporto è `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.

⚠ **Il difetto di Chrome resta quello che era**: l'hover non arriva, quindi
niente anteprima (pulsanti che non si illuminano, niente suggerimenti). Quel che
è cambiato è che **non è più un problema di correttezza**.

✅ **E il DeX l'ha giudicato il 15 agosto 2026**: *«sia su Linux sia su Android
(DeX) è tutto perfetto»*. ⇒ Il `[?]` del mezzo pixel (il `margin: 0 auto` quando
`clientWidth × devicePixelRatio` è dispari) **non si presenta** — ⚠ ma nessuno
l'ha misurato: se un giorno il testo del terminale tornasse sfrangiato su una
larghezza dispari, la prima cosa da guardare è quella.

Vedi anche [[agenti-a-refutare]] e [[utente-prova-si-conserva]].
