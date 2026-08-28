---
name: remotix-v2-convenzioni
description: "In REMOTIX_V2 si scrive in italiano, ogni affermazione porta una marca, e le decisioni stanno in DECISIONI.md una sola volta"
metadata: 
  node_type: memory
  type: project
  originSessionId: f705453b-99bd-4262-9ad0-9967e8c7c1df
  modified: 2026-08-09T06:15:49.110Z
---

Documenti, commenti e nomi nel codice sono **in italiano** (`palco`, `cattura`, `sentinella`,
`appunti`). Ogni affermazione porta una marca: `[M]` misurato con la data, `[R]` letto nel codice,
`[S]` letto in una specifica, `[?]` ipotizzato. Le decisioni stanno in `DECISIONI.md` **una sola
volta**, marcate ✅ (decisa dall'utente), 🔸 (derivata da me, correggibile senza discussione) o ❓
(aperta); gli altri documenti rimandano invece di copiare.

**Why:** il progetto è morto una volta su misure che non misuravano quel che si credeva, e il
codice di v1 è andato perso mentre i documenti sono sopravvissuti — sono loro ad aver reso
possibile ripartire. Distinguere «l'utente ha detto sì» da «l'ho dedotto io» è la differenza che
`LEZIONI.md` §2.3-quater dice di non perdere.

**How to apply:**
- prima di affermare un'assenza, **certifica lo strumento** su un caso dove la cosa c'è di sicuro:
  il 9 agosto una ricerca cercava in `src/` e non trovava `RecordVirtual` **nemmeno in Mutter**,
  dove c'è, perché gli XML stanno in `data/dbus-interfaces/`;
- quando una misura contraddice un documento, aggiornalo **nello stesso momento**, con data e
  fonte;
- il punto di ingresso è `README.md`, che dice in quale ordine leggere.

Vedi [[nic-regista-non-programmatore]].
