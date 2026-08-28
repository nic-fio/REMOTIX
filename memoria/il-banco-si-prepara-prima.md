---
name: il-banco-si-prepara-prima
description: "«Non chiamarmi se non funziona» — la scena si prepara e si GUARDA prima di chiedere un giudizio, e un contatore non è guardare"
metadata:
  type: feedback
---

⭐ **25 agosto 2026, fase 10.** Gli avevo dato indirizzo e credenziali chiedendo
di guardare il prodotto. Lui, tre volte, fino a smettere: *«Firefox non
funziona»* · ⛔ **«senza Firefox nessun test di rilievo ha senso, quindi non
chiamarmi se non funziona»** · *«io non faccio più niente, non posso fare test in
queste condizioni»*.

⛔⛔ **E poi la correzione che rimette a fuoco tutto**:

> **«Il Firefox che deve funzionare è quello del SERVER, non quello del tablet.»**

⇒ Non è un impiccio di banco: ⛔ **un desktop remoto in cui non si apre un
browser non è un desktop remoto.** È il prodotto visto dall'utente.

⛔ **E la parte grave non era il browser: era che non lo sapevo.** Ho provato
**quattro strade** per vedere l'immagine di quel desktop — lo scatto interno del
figlio (`SIGUSR1`), la fotografia dello schermo (GNOME non la dà), la tela della
pagina via Marionette, il conteggio dei fotogrammi — e ⛔ **nessuna mi ha dato il
quadro**. Ho dichiarato la scena pronta **senza averla guardata**.

**Why:** il suo giudizio è l'invariante I8, cioè il metro ultimo del prodotto —
⛔ **e ogni chiamata a vuoto ne consuma un pezzo.** È l'unico strumento del
progetto che non si può ricostruire. Il suo tempo serve a **guardare**, non a far
partire le cose né a scoprire che sono rotte.

**How to apply:**
- ⛔ **prima di chiamarlo, GUARDA la scena tu**: non «il processo è vivo», non
  «sono passati 493 fotogrammi» — ⭐ **l'immagine**. *493 fotogrammi neri sono
  493 fotogrammi*;
- ⭐ **il testimone che fa vedere si tara come ogni metro**: si mette nel desktop
  una **marca riconoscibile** (`04-b30-scena --giro NOME`) e si verifica che il
  testimone la ritrovi, ⛔ **più il controllo negativo**: col desktop nero deve
  dire «nero», non restituire un'immagine qualunque;
- ⛔ **se non ha potuto guardare deve tornare «non lo so», mai un'immagine
  vuota**: *«non ho guardato»* non è *«è nero»*;
- se la scena non si riesce a preparare, ⭐ **si riferisce il buco** — quali
  strade ho provato, dove si è fermata ciascuna, che cosa servirebbe — e **non
  gli si chiede di provarci lui**.

⚠ **E una premessa che avevo sbagliato**: la macchina di prova non ha schermo, e
da questo avevo concluso *«il browser deve girare sul suo computer»*. ⛔ Falso:
il browser deve girare **dentro la sessione remota**, che uno schermo ce l'ha —
è quella che il prodotto serve.

Vedi [[la-prova-la-fa-lutente]], [[le-prove-le-eseguo-io]],
[[come-guarda-nic-lo-schermo]], [[nic-regista-non-programmatore]],
[[testimone-sul-desktop-vero]].
