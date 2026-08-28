---
name: remotix-fase9-ripresa
description: "REMOTIX fase 9 — chiusa il 7 agosto 2026 con la copia zero rinviata: l'accelerazione in GPU c'è, il DMA-BUF no, e il vincolo per chi lo riprende"
metadata: 
  node_type: memory
  type: project
  originSessionId: aab51c1c-bc54-45fb-b6ac-36c9b5b96a98
  modified: 2026-08-07T09:08:14.642Z
---

La **fase 9 è chiusa il 7 agosto 2026**, con l'accelerazione hardware che funziona
(AVC420 via `h264_vaapi` in GPU, verificato su `xfreerdp3` e mstsc) e la **cattura a
copia zero rinviata**. Il racconto sta in `PIANO.md` (riquadro fase 9) e in
`REFERENCE.md` R27-R30, in particolare **R29 sesto punto**.

**Lo stato del server**: `REMOTIX_DMABUF=0` è il predefinito, scritto in
`provision-server.sh` con il perché. Costa 18 ms di CPU per fotogramma invece di 6.
La porta di lavoro è la **3392** (3389, 3390 e 3391 sono dei banchi).

**Il difetto rinviato**, per non ricominciare da capo: il buffer che Mutter presta a
copia zero **non è un fotogramma, è un *diff*** — ricicla quattro buffer e vi ridipinge
solo la regione cambiata (282 fotogrammi su 300). Chi lo prende per intero consegna
schermate già passate. La correzione giusta — accumulo delle regioni su una superficie
persistente — **è scritta e ha peggiorato le cose su mstsc**: sta dietro
`REMOTIX_ACCUMULO=1`, spenta. Il primo sospetto di quel che manca è
`SPA_META_SyncTimeline`.

**Il vincolo per chi riprende, ed è la lezione della giornata:** prima il banco che il
difetto lo fa comparire **da solo**, poi la correzione. Le due riproduzioni costruite il
7 agosto — client nel contenitore su loopback, client in LAN — restavano verdi mentre il
difetto era vivo nell'uso reale, e la correzione validata lì è stata collaudata
dall'utente. Senza quel banco, la copia zero non si fa.

**Da fare ancora**: la prova su **RDM** sul percorso in memoria; `h264_qsv` e
`h264_nvenc` restano non misurati.

Vedi [[remotix-metodo-documentazione]] e [[remotix-microfono-sospeso]].
