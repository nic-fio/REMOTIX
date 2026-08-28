---
name: niente-eccezioni-per-compositore
description: "Una funzione che non si può fare su tutti i desktop supportati esce dal prodotto, invece di restare dietro un interruttore"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 15e28402-67da-47fb-bd4c-3dda47c97a40
  modified: 2026-08-17T05:29:49.571Z
---

Se una funzione si può fare su un compositore e non su un altro, Nic la toglie invece di
tenerla dietro un interruttore o un ramo condizionato. Parole sue, 17 agosto 2026, decidendo
sul ridimensionamento a caldo della tela: *«non voglio mettere delle eccezioni nel progetto.
Il dynamic resolution esce dalle funzionalità di Remotix»* — e valeva anche per una funzione
già scritta, misurata (6 ms su Mutter) e verde in banco.

**Why:** un prodotto che fa cose diverse a seconda di chi lo ospita costa due rami, due banchi
e una spiegazione all'utente per ognuno — e il ramo povero resta vivo per anni, perché le
distribuzioni stabili non aggiornano i desktop. Nello stesso spirito aveva già fermato il
multi-monitor («non è previsto dal progetto. Sei andato fuori strada»).

**How to apply:** prima di proporre o scrivere una funzione che tocca il compositore, dire
subito su quali dei desktop supportati si può fare e su quali no — quello, non il costo in
millisecondi, è il dato che decide. Se la risposta è «su uno sì e su un altro no», la proposta
da portargli è toglierla, non nasconderla dietro un interruttore spento. ⚠ Non confondere il
caso con quello che resta legittimo: una cosa fatta **prima che la sessione esista** (la tela
presa dalla misura della finestra all'attacco) non è un'eccezione, perché ogni compositore la
sa fare a modo suo. L'eccezione è cambiare a caldo. Vedi [[processo-proporzionato-non-cerimonia]]
e [[nic-regista-non-programmatore]].
