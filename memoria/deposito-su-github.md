---
name: deposito-su-github
description: dal 28 ago 2026 il progetto si chiama REMOTIX (non piu' _V2), sta in ~/Documenti/REMOTIX e su github.com/nic-fio/REMOTIX, privato
metadata:
  type: project
---

**Il progetto si chiama REMOTIX.** Il «_V2» e' caduto il 28 agosto 2026: serviva
a distinguerlo da v1, e v1 non esiste piu' come progetto a se'.

- cartella: `~/Documenti/REMOTIX`
- deposito: `https://github.com/nic-fio/REMOTIX` — **PRIVATO**, ramo predefinito
  `fase-10-cure` (`master` e' fermo al 9 agosto, non e' il ramo di lavoro)

⛔ **Perche' resta privato**: la parola d'ordine `sudo` della macchina di prova
e' scritta in chiaro in 9 file dei banchi (`printf 'nicfio\n' | sudo -S ...`).
Finche' ci sono quelle righe il deposito non si puo' aprire — e cancellarle dopo
non basta, la storia di git non dimentica. Si toglie cambiando la parola d'ordine
sul server e facendogliela leggere da un file. ⇒ Lavoro da fare col server acceso.

⭐ **v1 e' dentro il deposito, sotto `fondamenta/`, e NON e' un archivio**:
`fondamenta/strumenti/sshpw.py` (39 richiami), `fondamenta/remotix-c/src` (34), `fondamenta/banco/enter.sh`
e i filmati di `fondamenta/calibrazione/` sono attrezzatura viva dei banchi.
Vedi [[costruire-serve-il-contenitore]] e [[riavvio-perde-la-chiave-ssh]].

⚠ **I registri di misura non sono stati rinominati**: `*.jsonl` e `*.log` portano
ancora «REMOTIX_V2», e devono. Sono verbali di misure fatte, e dicono con che nome
girava il prodotto quel giorno. ⭐ Un registro si aggiunge, non si corregge.

⚠ **Il rebranding non e' stato riprovato sul ferro** (macchina in assistenza dal
27 agosto): al ritorno del server, il primo giro della rete anti-regressione vale
anche come collaudo. La marca d'avvio e' cambiata su tutt'e due i lati insieme —
`src/main.c` la scrive, `01-b0-bersaglio`, `10-b96`, `10-b90` e `11-c9` la
controllano. Vedi [[progetto-in-pausa-agosto-2026]].

⚠ Fuori dal deposito e NON su GitHub: `~/SERVER.ssh` e `~/.ssh/id_ed25519`,
preparate in `~/DA-SALVARE/` prima della pulizia del tablet.
