# MASTERPLAN — quel che si fa DOPO

*Aperto il **25 agosto 2026**, per decisione dell'utente:*

> *«Per gli altri DE non ci portiamo dietro questo buco, per GNOME potremmo fare una manutenzione
> evolutiva al termine del progetto, insieme all'integrazione di altre funzioni. Potrebbe essere
> utile creare un documento `MASTERPLAN.md` dove annotare tutte queste cose da fare al termine del
> progetto.»*

⇒ La decisione sta in [`DECISIONI.md` §0.4](DECISIONI.md).

---

## Che cos'è questo documento — e che cosa NON è

**È** l'elenco delle cose che si faranno **quando il prodotto sarà finito**: migliorie, scelte
rimandate apposta, funzioni che non erano nel patto iniziale.

⛔ **Non è**:

| | |
|---|---|
| il registro delle decisioni | quello è [`DECISIONI.md`](DECISIONI.md), e ogni voce di qui **rimanda** là invece di ricopiare |
| l'elenco delle domande aperte | quello è `DECISIONI.md` **§7** — là stanno i buchi del *pensiero*, qui i lavori del *dopo* |
| il piano delle fasi | quello è [`PIANO.md`](PIANO.md). ⛔ **Se una cosa deve succedere PRIMA della fine, non sta qui: sta lì, con la sua fase** |
| un elenco di guasti | un guasto non aspetta la fine del progetto. Se è rotto si cura, e se non si cura si dichiara nella fase |

---

## ⛔⛔ LA REGOLA CHE TIENE IN PIEDI QUESTO DOCUMENTO — e non è una formalità

> ### Ogni voce deve dire **che cosa costa non farla MAI**.

⛔ **Un elenco di cose da fare dopo è il cassetto dove le cose vanno a morire.** Ci finisce tutto, si
allunga, nessuno lo rilegge, e a un certo punto guardarlo mette solo ansia — e un documento che mette
ansia non si apre più.

⇒ ⭐ **Il costo del «mai» è l'unica informazione che serve davvero**, perché è quella che separa *«va
fatto»* da *«sarebbe bello»*, e quella scelta la fa l'utente, non chi scrive la voce.

⚠ E il rovescio, che vale quanto la regola: **una voce il cui costo del «mai» è ZERO si cancella**.
Non si tiene per rispetto: si toglie, e il documento resta corto abbastanza da essere riletto.

---

## Il modello di una voce

```markdown
### M<n> · <titolo in parole normali>

**Che cos'è**            due righe, senza gergo
**Da dove viene**        la fase e il documento dove è nato, con la data
**Che cosa costa se non si fa MAI**   ⛔ la riga che decide tutto
**Che cosa serve prima** la misura o la prova che rende la scelta informata
**Quanto pesa**          `[?]` finché non è stato guardato davvero
```

---

# Le voci

## M2 · ⚠ QVBR non è mai stata accesa, e la prova che servirebbe non è stata fatta

**Che cos'è.** Un modo diverso di far lavorare il codificatore. Oggi è **spenta**, e valgono i numeri
di fabbrica (tetto 10, riserva 0,5).

**Da dove viene.** Fase 10, `fasi/10-multi-tenant-e-il-budget.md` **§10-bis**: due decisioni **non
prese**, con i predefiniti in vigore.

**Che cosa costa se non si fa MAI.** ⭐ **Su un utente solo, niente**: il regolatore fa già il suo
mestiere, e la fase 10 lo ha argomentato. ⛔ Il dubbio riguarda **dieci insieme su un filo vero**, e
quel giro non è stato fatto: nella fase 10 i clienti giravano dentro la macchina, quindi **il filo è
contato, non provato**.

**Che cosa serve prima.** Dieci clienti **su rete vera**, non dentro la macchina. ⚠ È una prova che
vuole apparecchiatura, non un pomeriggio.

**Quanto pesa.** `[?]`

---

## M3 · ⚠ L'algoritmo che decide quanto spingere sul filo non è mai stato scelto

**Che cos'è.** Sul filo il trasporto usa **CUBIC**. ⛔ Nessuno l'ha scelto: è quel che c'era.

**Da dove viene.** Fase 9, elencata fra le cose aperte nel `README.md`.

**Che cosa costa se non si fa MAI.** `[?]` **Non si sa, ed è questo il punto.** La prova per
contrasto non è mai stata fatta **perché nessuna opzione lo espone** — quindi non è che l'abbiamo
provato e andava bene: non l'abbiamo mai provato.
⚠ Sulle reti sane non cambierebbe probabilmente nulla; il sospetto riguarda **le reti sporche**, che
sono il tema su cui l'utente ha corretto il bersaglio della fase 9.

**Che cosa serve prima.** Un'opzione che lo esponga, e due giri sullo stesso filo sporco.

**Quanto pesa.** `[?]` Piccolo il lavoro, **incerta** la resa.

---

## M5 · Scegliere il desktop quando sulla macchina ce n'è più d'uno

**Che cos'è.** Oggi una macchina ha **un** desktop, e REMOTIX accende quello. Con GNOME e KDE
installati insieme, nessuno può dire «a me KDE»: né l'utente dalla pagina, né chi amministra il server.

**Da dove viene.** Fase 12, aprendo KDE — `DECISIONI.md` **§4.6-duodetricies**, 18 settembre 2026:
*«la funzionalità di scelta di desktop multipli la lasciamo per una futura implementazione»*.

**Che cosa costa se non si fa MAI.** Su una macchina con un desktop solo, **niente**. Su una con due,
il secondo **non è raggiungibile** da REMOTIX: vince GNOME, sempre, per tutti gli utenti. ⚠ Chi
installa KDE accanto a GNOME e si aspetta di usarlo da remoto resta deluso senza un messaggio chiaro —
per questo il server lo scrive nel registro all'avvio.

**Che cosa serve prima.** Che l'utente dica **chi** sceglie (l'amministratore per la macchina, o ogni
utente per sé). ⛔ La seconda tocca la pagina e il protocollo, e cambia `RCP.md`.

**Quanto pesa.** `[?]` Con la scelta per macchina, poco: un'impostazione. Con la scelta per utente,
una funzione nuova.

---

## M6 · Stampare sulla stampante di chi è collegato (solo PDF, dal server al client)

**Che cos'è.** Una stampante virtuale «REMOTIX» sul server trasforma la stampa in **PDF**; il PDF arriva alla
pagina, che apre la finestra di stampa del browser, e chi è collegato stampa sulla **sua** stampante (quella di
casa, per chi lavora da fuori; quelle di rete già installate sul suo PC, per chi è in ufficio). ⛔ **Solo PDF,
solo dal server al client** (utente, 10 ott 2026), mai al contrario. ⭐ **Una tecnologia sola per ogni stampante**
(utente: *«niente casi particolari per stampanti locali o stampanti remote: usiamo la stessa tecnologia per
entrambi i casi»*): la stampa va dove sa stampare il dispositivo di chi è collegato. Le stampanti che
l'amministratore configura da sé sul server (CUPS) sono affare del sistema, non una funzione di REMOTIX.

**Da dove viene.** 10 ottobre 2026, dal confronto con i prodotti commerciali: *«trovo la condivisione di files
piuttosto pericolosa, mentre si potrebbe ragionare sul discorso stampanti»*; poi *«solo pdf, server -> client. La
annotiamo nel masterplan»*. La decisione sta in `DECISIONI.md` §10.41; fino ad allora era fuori dal progetto
(`SPECIFICHE.md` §12).

**Che cosa costa se non si fa MAI.** Da REMOTIX **non si stampa**: chi lavora deve farsi arrivare il documento
per altra via (email, una cartella condivisa) — cioè proprio i passaggi di file che non vogliamo — oppure
l'amministratore deve configurare a mano le stampanti sul server, una per una. Per un'azienda piccola è una delle
prime domande.

**Che cosa serve prima.** ⚠ Dichiarare all'amministratore che **stampare è portare fuori un documento**: dalla
finestra di stampa il browser lo salva anche come PDF. ⇒ Le regole proposte: **spenta finché l'amministratore non
la accende**; **ogni stampa nel registro** (chi, quando, quante pagine); il PDF non si salva sul client da
REMOTIX, va solo alla finestra di stampa. Poi: quale stampante virtuale (CUPS con un backend nostro, o
`cups-pdf`), un canale nuovo in `RCP.md` per il PDF, la prova sui quattro desktop e sui browser serviti.

**Quanto pesa.** `[?]` Non guardato davvero. Stima a occhio: una fase piccola (stampante virtuale, un canale,
la finestra di stampa nella pagina, il banco). ⚠ Il prezzo d'uso: ogni stampa passa dalla finestra del browser e
chiede un clic (i browser non stampano in silenzio).

---

# ⚠ Le cose che qualcuno potrebbe voler mettere qui, e NON ci vanno

⛔ Perché il documento resti corto, va detto anche che cosa **rifiuta**.

| | dove va invece | perché |
|---|---|---|
| aggiornare il server senza buttare fuori nessuno | **`PIANO.md`, fase 15** | è già una fase. Non aspetta la fine |
| il ritardo che sfora il tetto | resta `[?]` in `DECISIONI.md` §2.5 | è una **grandezza dichiarata**, non un lavoro rimandato |
| il ridimensionamento a caldo | ⛔ **fuori dal prodotto** (`DECISIONI.md` §5.1-bis) | tolto **per decisione dell'utente**. Rimandare è diverso da togliere, e questa è tolta |
| la sessione che nasce cieca | **fase 11**, il collaudo della rete | è un **guasto vivo**. Un guasto non aspetta la fine del progetto |
| una frase sbagliata in un commento | si corregge **subito** | non è un lavoro: sono due minuti |

---

## Come si tiene questo documento

1. ⛔ **Una voce entra solo con la riga «che cosa costa se non si fa mai» compilata.** Senza quella
   riga non è una voce: è un desiderio.
2. ⛔ **Una voce il cui costo del «mai» diventa zero si CANCELLA**, e si scrive in fondo perché.
3. ⛔ **Le voci non si numerano di nuovo** quando una se ne va: `M3` resta `M3` per sempre, o i
   rimandi degli altri documenti puntano nel vuoto.
4. ⚠ **Questo documento non decide niente.** Quando una voce viene affrontata, la decisione va in
   `DECISIONI.md` e il lavoro in `PIANO.md`; qui resta il rimando.
5. ⭐ **Si rilegge alla chiusura di ogni fase**, insieme al `README.md` — è l'unico modo perché un
   elenco del «dopo» non diventi archeologia.

---

## Le voci tolte

⭐ **21 settembre 2026, decisione dell'utente**: *«M2, M3 e M5 sono gli unici punti da conservare
nel masterplan»* (poi, il 10 ottobre, è entrata **M6**). ⇒ Tolte, e i numeri **non** si riusano (regola 3):

| | che cos'era | perché è uscita |
|---|---|---|
| **M1** | GNOME consegna meno fotogrammi di quelli che gli si chiedono (per averne 60 bisognerebbe chiedergliene di più, e `MOVIMENTO_FPS` è una costante) | deciso dall'utente: non è più un lavoro del «dopo». Il fatto resta scritto in `DECISIONI.md` §2.5-bis |
| **M4** | due client sullo stesso desktop nello stesso momento | deciso dall'utente: non è un lavoro del «dopo». L'invariante I2 (un posto per utente) resta com'è, `DECISIONI.md` §7.3 |
