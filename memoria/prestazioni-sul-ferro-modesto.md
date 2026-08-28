---
name: prestazioni-sul-ferro-modesto
description: "Le prestazioni di REMOTIX si dichiarano SEMPRE insieme al ferro: sono ottenute su una Intel UHD 730 integrata, non su una scheda potente"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 884e8876-d549-42f8-9eaf-845107fbde4b
  modified: 2026-08-16T20:50:45.841Z
---

Il 16 agosto 2026, dopo il giudizio *«il test su Windows lo dichiaro superato al 100 %»*, Nic ha
aggiunto: **«ricordiamoci sempre che otteniamo performance eccellenti su una Intel integrata»**.

⇒ **Un numero di prestazione di questo progetto non si riferisce mai da solo**: si riferisce con il
ferro su cui è stato preso — `[M]` **Intel UHD 730** (`i915`, `0000:00:02.0`, `renderD128`), che è
un'integrata modesta. La Radeon RX 6800 della stessa macchina è **esclusa apposta** con una regola
udev (`DECISIONI.md` §4.6-ter e §4.6-quinquies).

**Why:** sono due cose in una, e tutt'e due sue.
1. **È il metodo che ha posto lui** il 15 agosto 2026: *«i test vanno fatti sulla GPU integrata,
   altrimenti "trucchiamo" il gioco. La solidità del sistema la si vede su GPU poco potenti, non
   mostri come la RX 6800»* — e quella regola nacque perché una misura dell'Aquarium a 60 fps era
   stata presa **sulla scheda sbagliata**, per accidente.
2. **È il risultato**, e senza il ferro accanto non si capisce quanto vale: *«funziona tutto e con
   performance eccellenti»* su un'integrata da ufficio dice del prodotto quel che lo stesso numero
   su una scheda da gioco non direbbe affatto.

**How to apply:**
- quando si riporta un numero — fps, ms, ritardo, fotogrammi — si nomina **la scheda**, non solo la
  macchina: «su Intel UHD 730 integrata», mai «sulla macchina di prova» e basta;
- ⛔ se una misura viene da un ferro diverso (la Radeon, un portatile, un telefono), **si dichiara
  in quella riga**: una misura sul ferro migliore non dice se il prodotto regge, dice quanto è
  veloce quel ferro;
- vale anche verso l'esterno: è la frase che qualifica il prodotto, e va tenuta in testa a qualunque
  riassunto di prestazioni.

⏳ E resta la domanda che la fase 8 eredita: la codifica hardware sceglie la sua scheda da sé
(VA-API). Se il compositore disegna sull'integrata e il codificatore cercasse la discreta — chiusa —
il ripiego è in CPU, e va **dichiarato** invece che subito.

Vedi [[remotix-v2-convenzioni]], [[la-prova-la-fa-lutente]] e [[utente-prova-si-conserva]].
