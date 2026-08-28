---
name: agenti-a-refutare
description: "Nic chiede esplicitamente più agenti in parallelo per accelerare — e il mandato che rende più: «prova a REFUTARE questa frase», non «verifica»"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4825e50b-60a3-47f4-968c-276b245986d4
  modified: 2026-08-13T08:52:25.210Z
---

Il 13 agosto 2026, a fase 2 quasi chiusa, Nic ha scritto: *«usa agenti multipli per accelerare lo
sviluppo, cerchiamo di chiudere questa fase 2»*. ⇒ **Il parallelismo con agenti è richiesto, non da
proporre ogni volta** — vale come via libera sul metodo, come [[via-libera-permanente]] vale sul
merito.

**Why:** quel giro ha prodotto il risultato migliore della giornata, e non per la velocità. Un
agente mandato con mandato **avversariale** — *«questa frase è falsa: provalo»* — ha refutato la
riga su cui stavo per chiedere il giudizio di fase: uno dei dodici guasti del metro era **verde per
costruzione** (il banco leggeva un contatore `reset` che il prodotto chiama `azzerati`, quindi
valeva sempre zero). Un agente mandato a *verificare* avrebbe letto la stessa riga e confermato.
⭐ E lo stesso vale al contrario: l'agente mandato a **curare** ha **rifiutato la cura che gli avevo
passato io**, con un caso concreto — la mia cura avrebbe prodotto un falso rosso, peggio del falso
verde. Un mandato che ammette il rifiuto vale più di uno che ordina.

**How to apply:**
- il mandato si scrive per **refutare**, non per verificare: *«parti dall'ipotesi che sia falsa e
  cerca la prova; se non ci riesci, dillo — ma solo dopo averci provato davvero»*;
- si chiede sempre **che cosa sarebbe vero se l'agente avesse ragione** — lo scenario concreto,
  ingresso e uscita sbagliata — o il rilievo resta un'opinione;
- si dice esplicitamente che **il rifiuto del mandato è ammesso**: *«se la grandezza giusta non è
  quella che ti ho detto, dillo e fermati»*;
- si dichiarano i **vincoli sulle risorse condivise** in ogni mandato (porte vive, file di un altro
  agente) — vedi [[banchi-in-parallelo-isolamento]];
- si verifica **da soli** il rilievo più grave prima di crederci: due minuti di `grep` sul codice
  hanno confermato il difetto di M8 prima che agissi.

Vedi [[processo-proporzionato-non-cerimonia]] e [[nic-regista-non-programmatore]].
