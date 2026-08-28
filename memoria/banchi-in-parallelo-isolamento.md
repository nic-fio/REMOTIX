---
name: banchi-in-parallelo-isolamento
description: "Come far girare più banchi REMOTIX insieme senza avvelenarsi: porta, ban-file e socket propri per ciascuno"
metadata: 
  node_type: memory
  type: project
  originSessionId: cb1700c8-7c41-4750-828a-e216987d359a
  modified: 2026-08-11T13:55:27.696Z
---

Più banchi possono girare **in parallelo** contro il prodotto solo se ciascuno accende
**il proprio server**: `remotix --porta N --ban-file … --comando-socket …`. Senza,
il ban di §4.4-bis (per indirizzo, 12 ore) fatto scattare da un banco mette fuori uso
tutti gli altri, perché partono tutti dallo stesso indirizzo.

Assegnazione usata l'11 agosto 2026, cinque agenti insieme: 7471-75 (B8) · 7481-85 (B13) ·
7491-95 (B10) · 7501-05 (P1/P5) · 7511-15. ⛔ La 7447 è dell'innesto e la 7448 del prodotto
acceso: non si toccano.

E tre regole di convivenza che sono costate meno di quanto avrebbero potuto:
- ogni agente possiede **file suoi** e i file condivisi si toccano solo con `Edit` su
  un'ancora unica, mai riscrivendoli interi (un `--put` dell'intero registro ha rischiato
  di cancellare la riga di un altro);
- **nessun agente scrive `.md` e nessuno fa `git`**: i documenti si scrivono alla fine,
  a codice fermo — è il rilievo R12C, e il git a più mani si pesta l'indice;
- i guasti di certificazione si innestano su una **copia** dell'albero del prodotto, o
  per qualche minuto gli altri misurano un binario bugiardo.

Vedi [[remotix-v2-convenzioni]] e [[via-libera-permanente]].
