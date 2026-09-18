---
name: fase-12-kde-sotto-la-rete
description: "Direttiva di Nic per la fase 12 (18 set 2026) — KDE a piccoli incrementi, rete completa dopo ognuno, checkpoint come cancelli, Fable 5 sui bloccanti, stato ogni 30 min"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7ed6518e-06c6-45b1-a053-d2827ab2eb17
  modified: 2026-09-18T15:25:28.685Z
---

Direttiva vincolante di Nic, 18 settembre 2026, aprendo la fase 12 (KDE): *«Voglio arrivare a KDE
funzionante senza dover mai dire "prima funzionava, ma questa modifica era necessaria"»*.

**Why:** la rete della fase 11 va usata come guardiano permanente, non come collaudo finale.

**How to apply:**
- ciclo per ogni incremento: CP0 baseline (rete completa `--famiglia tutto`, 4 scatole, stesso
  binario) → CP1 definizione (OBIETTIVO/INVARIANTE/MODULI/PROVA KDE/PROVA CLIENT/REGRESSIONI
  GNOME/CRITERIO) → CP2 osservazione misurata GNOME vs KDE → CP3 modifica minima → implementazione
  → CP4 prova KDE → client reali (Chrome e Firefox Linux, Chrome sull'emulatore Android) → rete
  completa → GNOME invariato + guasti ancora presi → checkpoint (commit) → prossimo incremento;
- rosso su GNOME = regressione finché non provato il contrario; classi A/B/C/D, D mai scorciatoia;
- problema serio/bloccante ⇒ agente col modello **fable** con richiesta strutturata (PROBLEMA,
  CONTESTO, ATTESO, OSSERVATO, PROVE, ULTIMA CONFIG BUONA, VINCOLI, TENTATIVI, DOMANDA); la sua
  risposta va poi misurata e certificata;
- agenti in parallelo sul lavoro indipendente, con perimetro scritto; integrazione e
  certificazione restano mie;
- silenzio: un aggiornamento ogni ~30 min nel formato STATO/OBIETTIVO/LAVORO/TEST/REGRESSIONI/
  BLOCCHI/PROSSIMO; si interrompe solo per checkpoint, regressione, blocco, Fable, decisione.

Vedi [[parlato-al-minimo]], [[agenti-a-refutare]], [[niente-eccezioni-per-compositore]].
