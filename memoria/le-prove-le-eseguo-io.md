---
name: le-prove-le-eseguo-io
description: "«Se non mi dai il tempo di fare le prove non si va da nessuna parte; altrimenti falle tu» — i banchi da browser li guido io con Marionette, non li faccio aprire a lui"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6917bf53-6d6d-42bb-8bd5-f1d628833c28
  modified: 2026-08-17T17:36:50.026Z
---

⛔ **17 agosto 2026, e la frase è sua**: *«se non mi dai il tempo di fare le
prove non si va da nessuna parte»* — *«altrimenti falle tu»* — *«tanto hai il
controllo del tablet»*.

Era successo questo: gli avevo chiesto di aprire lo stesso banco sei volte con
sei interruttori diversi, **e intanto cambiavo la pagina sotto**. Le sue misure
descrivevano versioni che non esistevano più.

**Why:** un giro di banco costa a me trenta secondi e a lui un'interruzione; e
una pagina che cambia fra una sua apertura e l'altra produce numeri che non si
possono confrontare — cioè lo fa lavorare per niente.

**How to apply:**
- ⭐ un banco che gira nel browser **lo guido io**: `banchi/07-b48-testimone.py`
  accende un Firefox vero col protocollo Marionette, fa tutti i giri e legge
  `window.RISULTATO` — nessuna coordinata, nessun occhio;
- ⛔ **non** chiedergli di aprire più di UN indirizzo per volta, e non toccare
  la pagina finché non ha risposto;
- ⚠ `--visibile` gli apre una finestra sullo schermo: si avvisa **prima**, non
  dopo;
- quel che resta suo è il **giudizio** — «gli artefatti ci sono», «l'audio fa
  schifo» — che nessun banco sa dare: vedi [[la-prova-la-fa-lutente]].

⛔⛔ **E il 20 agosto 2026 l'ha detto più forte**: *«non voglio fare più test:
hai il controllo del PC, sistema tutto e fai le prove su chrome e firefox»* —
dopo che gli avevo fatto ricaricare la pagina tre volte per difetti che un
banco avrebbe trovato da solo in due minuti.

⭐ **Lo strumento che ne è nato**: `banchi/07-b51-due-browser.py` — Firefox con
Marionette **e** Chrome col protocollo di diagnosi (CDP), quattro controlli per
browser, e l'input verificato **dal registro del server** (dove è arrivato il
clic), non dalla pagina. ⛔ Da usare **prima** di chiamarlo a guardare.

⚠ **E la regola sotto**: *un solo motore non è una prova, è mezza prova*. La
cura di `DECISIONI.md` §5.4 era misurata su Firefox e su Chrome ha rotto
immagine **e** input.

Vedi [[via-libera-permanente]], [[nic-regista-non-programmatore]].
