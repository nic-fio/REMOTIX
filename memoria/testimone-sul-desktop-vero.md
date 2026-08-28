---
name: testimone-sul-desktop-vero
description: "Come si misura col browser quel che arriva davvero al desktop remoto — il file testimone, e le due reti da togliere alla pagina"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6c6f9648-d9f9-4e2a-9127-2557b8767681
  modified: 2026-08-16T13:59:02.925Z
---

⭐ **Il metro delle prove col browser** (16 agosto 2026, fase 5). Dentro la
sessione grafica di `prova` si lancia da ssh un terminale con:

```sh
while IFS= read -r _; do date +%s%N >> /tmp/testimone.txt; done
```

⇒ Ogni `Invio` che **arriva al desktop** scrive una riga con l'istante in
nanosecondi. Un tasto rimasto giù si ripete da solo — `[M]` **~33 battute al
secondo**, è il desktop remoto a farlo — e si confronta l'ultima battuta con
l'ora della riga nel registro. Precisione ottenuta: **millisecondi**.

**Due trappole, tutt'e due pagate:**

1. ⛔ **Il pilota del browser non sa TENERE PREMUTO** un tasto: `computer` manda
   sempre giù-e-su. Si usa `javascript_tool` con
   `window.dispatchEvent(new KeyboardEvent("keydown", {code:"Enter"}))` — le
   funzioni della pagina sono globali vere, raggiungibili per nome.
   ⚠ Solo i tasti **non-lettera** si possono tenere giù: una lettera parte come
   `LETTERA`, che è premi-e-rilascia.
2. ⛔⛔ **La pagina rilascia da sola** su `blur`, `visibilitychange` e
   `pagehide` (`cl_rilascia_tutto`). ⇒ Dal browser il server non ha quasi mai
   niente da rilasciare, e **si certifica la pagina credendo di certificare il
   server**. Per provare il server si sostituisce `window.cl_rilascia_tutto`
   con uno stub.

⚠ **E l'orologio del silenzio ruba trenta secondi alle prove**: se fra il
preparare e il provocare passano 30 s, `§5.3` ha già rilasciato tutto e la
misura è di un'altra cosa. È successo due volte.

Il taglio del filo si fa dal server con una tabella `nft` propria
(`nft delete table inet provataglio` per toglierla), mai con `iptables` — sulla
macchina di prova non c'è.

Vedi [[costruire-serve-il-contenitore]] e [[utente-prova-si-conserva]].
