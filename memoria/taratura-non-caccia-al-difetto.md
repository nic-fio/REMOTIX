---
name: taratura-non-caccia-al-difetto
description: "Quando Nic riferisce una cosa piccola, dice anche quanto e' piccola — e si aspetta che il registro della risposta la segua: messa a punto, non caccia al difetto"
metadata:
  type: feedback
---

Il 22 agosto 2026 Nic ha descritto l'unico appunto che gli restava — una finestra trascinata veloce
e' *«leggermente meno fluido»* del locale. Io ho risposto con un tetto aritmetico, i ~16 ms non
spiegati promossi a *«meta' del tuo problema»* e una lista da caccia al guasto. Lui ha corretto il
registro, non i fatti: **«bada bene: e' questione di micro-secondi, non di secondi, ecco perche'
parlavo di ottimizzazione e non di debug»**.

**Why:** non stava contestando le misure — stava dicendo che il prodotto **non e' rotto**, e che
un difetto grosso trovato dentro un sintomo che lui chiama piccolo e' quasi sempre segno che ho
scambiato un tetto di progetto per un guasto. Trattare una messa a punto come un'emergenza gli fa
perdere fiducia nel resto delle mie misure, e gonfia il lavoro di una fase che lui aveva
dimensionato bene.

**How to apply:**
- quando dice **«ottimizzazione»**, il lavoro e' spostare un numero che gia' funziona; quando dice
  **«non funziona»**, e' un difetto. Sono due registri, e la parola la sceglie lui apposta;
- la grandezza che riferisce e' un **dato**: se le mie misure dicono molto piu' grande, e' un
  disaccordo da dichiarare in una riga — con il numero — non da risolvere alzando il tono;
- e resta la regola di [[la-prova-la-fa-lutente]]: la misura del caso che descrive **lui** (la
  finestra trascinata) viene prima di qualunque conto derivato da scene d'altro tipo.

Vedi [[processo-proporzionato-non-cerimonia]] e [[parlare-come-al-regista]].
