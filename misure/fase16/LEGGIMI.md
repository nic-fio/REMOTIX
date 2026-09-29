# Fase 16 — le misure conservate

Copia, il 29 set 2026, della parte **compatta** di `/media/REMOTIX/misure/fase16/` sul server
(28 MB di 42 GB): quanto basta per rigenerare il rapporto e ricontrollare ogni giudizio.

- `registro.jsonl` — il registro a sole aggiunte di `16-classifica.py`: una riga per livello e
  una per sessione, con misure, risorse e ragioni. **È la fonte del rapporto.**
- `rapporto.html` — il rapporto generato (`16-rapporto.py --campagne intel-b amd-b intel-c`).
- `<campagna>/salita.log|salita.jsonl|stato.json` — il diario di ogni salita.
- `<campagna>/<livello>/classifica.log|livello.json|controllo-corto.json` — il giudizio di ogni
  livello e il controllo funzionale del livello.
- `coda-*.log|jsonl`, `campagna.log`, `ripresa-28set.sh` — le code della notte.
- `16-corta-*.log` — le suite corte di regressione della fase.

**Campagne valide** (fasi/16-stress-e-capacita.md §11 e le anomalie): `intel-b-*` (prodotto
45d048c8), `amd-b-*` (28a947f5, dopo la cura D-023), `intel-c-*-lxqt` (LXQt 4K/3K/2K rifatti con
l'attore corretto). Le altre (`intel-*` della prima notte, `amd-*` del 27 mattina con lo schermo
nero di D-023, `amd-freq-*`, `prova-*`) restano come storia: `16-rapporto.py --campagne` le esclude.

Rigenerare: `python3 banchi/16-stress/16-rapporto.py --registro misure/fase16/registro.jsonl
--campagne intel-b amd-b intel-c --html /tmp/rapporto.html`.

⚠ I dati grezzi (server.log 15 GB, journal 18 GB, foto 2,9 GB, risorse) NON sono qui: stanno sul
server e in un archivio compresso fuori dal deposito (vedi fasi/16 §17.3).
