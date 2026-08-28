---
name: remotix-prove-sul-banco-non-sull-utente
description: "REMOTIX — l'utente non è il banco: le prove le fa il banco, le cacce hanno un tetto dichiarato, e la scelta «curo o rinvio» si mette davanti subito"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4bbea89f-379f-45d3-8703-bf57c8fe4e7c
  modified: 2026-08-07T13:53:48.773Z
---

In REMOTIX l'utente **non va usato come banco di prova**. Vale per le indagini lunghe:
ogni ipotesi che chiede «collegati e dimmi» costa un suo intervento, e una caccia fatta
così gli brucia la giornata anche quando la diagnosi è corretta.

**Why:** il 7 agosto 2026 la caccia al difetto dell'alternanza (fase 9, copia zero) ha
consumato mezza giornata dell'utente — «mi sembra che stiamo perdendo tempo», «il
progetto è arenato» — mentre la cura utilizzabile (`REMOTIX_DMABUF=0`) era nota dopo
un'ora. Il resto era il recupero di un'ottimizzazione: 6 ms di CPU per fotogramma invece
di 18, su una macchina a venti thread. E la correzione scritta al buio, validata su un
banco che il difetto non mostrava, gliel'ha peggiorato.

**How to apply:**

1. **appena la cura c'è, si applica e si dichiara**: «funziona, il resto è
   ottimizzazione» — e la scelta «continuo o rinvio» si mette davanti all'utente
   subito, non dopo cinque giri;
2. **si mette un tetto** a una caccia, dichiarato in partenza;
3. **le prove le fa il banco.** Se il banco non riproduce, non si spedisce niente da
   collaudare: prima il banco, poi la correzione (regola scritta in `PIANO.md` fase 9 e
   in `REFERENCE.md` R29);
4. **il metro è quel che si vede.** L'utente giudica il software funzionante (§7 di
   `SPECIFICA.md`): un numero di prestazione che nessuno percepisce non giustifica il
   suo tempo.

**⛔ E DUE REGOLE IN PIÙ, pagate il 7 agosto 2026 nel pomeriggio, che è costato la fase 10:**

5. **non si spedisce sul server di lavoro una modifica a quel che si VEDE, validata solo sul
   banco.** Il passaggio a VBR aveva PSNR, SSIM e un fotogramma fermo guardati a occhio; non aveva
   il giudizio dell'utente sul desktop vero. Il giudizio, arrivato dopo: *«siamo tornati indietro»*,
   poi *«sono proprio deluso del progetto, è un fallimento»*. Quel che cambia l'immagine sta dietro
   un interruttore spento finché non l'ha guardato lui;
6. **all'inizio di ogni sessione si confronta lo STATO DELLA MACCHINA con quel che i documenti
   dichiarano.** `/etc/default/remotix` era stato letto alle undici e la riga che teneva spenta la
   copia zero non c'era più — persa quando il file era stato riscritto per cambiare la porta, e quel
   file vive in RAM. Nessuno l'ha notato, e l'utente si è ritrovato in faccia un difetto noto. Da
   qui la regola generale, ora in `REFERENCE.md` R29: *la protezione di un difetto noto non si affida
   a una riga di configurazione che si può perdere* — sta nel codice.

Vedi [[remotix-requisito-prestazione]].

Vedi [[remotix-metodo-documentazione]] e [[remotix-fase9-ripresa]].
