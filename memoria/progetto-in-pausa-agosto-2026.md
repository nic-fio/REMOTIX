---
name: progetto-in-pausa-agosto-2026
description: "Dal 27 agosto 2026 il progetto è fermo per un intervento chirurgico di Nic; si riprende da KDE, e la prima mossa è far girare la rete"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5d851c2d-522d-4f85-b6a7-a7fa000732b0
  modified: 2026-08-27T19:48:28.207Z
---

Il 27 agosto 2026 Nic ha fermato REMOTIX_V2 per affrontare un **intervento chirurgico**. La pausa
prevista è di **qualche settimana**. Macchina di prova e tablet sono stati spenti, il deposito è
pulito e tutto è committato sul ramo `fase-10-cure`.

**Al ritorno si riprende dalla fase 12 (KDE)** — non da altro: la fase 11 è chiusa.

⭐ **La prima mossa non è scrivere codice: è far girare la rete anti-regressione**
(`banchi/11-scatole/11-gancio.sh gira --famiglia tutto`). ⛔ Se non dice **58 verdetti verdi, 3
rossi, 49 guasti innestati su 49 visti**, qualcosa è cambiato sotto e va guardato **prima** di
toccare KDE. I tre rossi attesi sono `C1` su kde/xfce/lxqt: non sono guasti, sono il mandato della
fase 12.

⚠ La macchina di prova ha la radice **in RAM** ⇒ dopo lo spegnimento va rifatta da capo: chiave ssh,
`src/provisiona.sh`, poi le quattro scatole. Vedi [[riavvio-perde-la-chiave-ssh]] e
[[costruire-serve-il-contenitore]].

⛔ **Non ricostruire il contesto dalla memoria**: il riquadro in testa a `README.md` è scritto apposta
per chi torna e non ricorda nulla, e contiene i numeri, l'ordine delle operazioni e le tre cose che
la fase 12 eredita già misurate. Si legge quello per primo.

⇒ Vale ancora tutto di [[la-prova-la-fa-lutente]] e [[le-prove-le-eseguo-io]]: al ritorno il giudizio
resta suo, ma i banchi li guido io.
