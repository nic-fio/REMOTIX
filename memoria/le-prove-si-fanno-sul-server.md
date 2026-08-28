---
name: le-prove-si-fanno-sul-server
description: regola di Nic, 28 ago 2026 — le prove girano sulla macchina di prova, mai sul tablet; sul tablet si scrive e si compila
metadata:
  type: feedback
---

**«Le prove si fanno sul server, non sul tablet»** — Nic, 28 agosto 2026, mentre si
svuotava il tablet.

**Perché:** il tablet e' un CHUWI Hi10 X1 con 7,5 GB di RAM e una N100 a 4 thread; la
macchina di prova e' un i5-13500T a 20 thread con 31 GB. ⛔ Un numero misurato sul
tablet non dice niente del prodotto: dice del tablet. ⇒ E il tablet non ha bisogno di
tenersi installato **niente** di quel che serve a FAR GIRARE i banchi.

**Come si applica:**

- sul tablet si **scrive** e si **compila** (podman, `remotix-costruzione`); sulla
  macchina di prova si **fa girare** (`fondamenta/banco/enter.sh`).
  Vedi [[costruire-serve-il-contenitore]].
- le dipendenze dei banchi si installano **la'**, con `fondamenta/banco/provision.sh`,
  ⛔ non a mano sul tablet — lo dice il banco stesso quando manca `cargo`.
- ⇒ 28 ago 2026: tolto Rust dal tablet (1,3 GB, residuo di v1 che era in Rust), le
  due immagini podman nostre e 3,3 GB di uscite di banco sparse in casa e in
  `/var/tmp`. Da 41 a 33 GB.

⭐ **L'eccezione, e non e' un'eccezione:** l'SDK Android e l'emulatore restano sul
tablet. `DECISIONI.md` §5-bis.0-ter, 9 agosto 2026: *«sull'emulatore si sviluppa,
non si misura — nessun numero di questo progetto viene dichiarato su un
emulatore»*. ⇒ Non e' un banco: e' ambiente di sviluppo, ed e' coerente con questa
regola invece di contraddirla. Vedi [[emulatore-android-per-provare]].

⚠ E il rovescio, che resta vero: [[la-prova-la-fa-lutente]] — il giudizio finale non
lo da' ne' il tablet ne' il server, lo da' Nic guardando lo schermo.
