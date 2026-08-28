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

## M1 · ⭐⭐⭐ GNOME non arriva al desiderato — e per arrivarci bisognerebbe chiedergli un numero diverso

> ### ⭐⭐⭐ LA REGOLA CHE SEMPLIFICA QUESTA VOCE — *l'utente, 25 agosto 2026*
>
> > *«Rendiamola semplice: il 4K/60 fps è il tetto che chiediamo a tutti (desiderio). Per i prossimi
> > DE lo chiediamo, per GNOME dovremo tornarci.»*
>
> ⇒ ⭐ **Il bersaglio è uno solo per tutti**, ed è il **desiderato** che era già deciso l'8 agosto
> 2026 (`DECISIONI.md` §2.2): **4K · 60 fotogrammi al secondo · 10 bit**. Nessun bersaglio su misura
> per compositore.
>
> ⭐⭐ **E per i desktop nuovi non c'è niente da fare**, e va detto perché è la parte lieta: il
> prodotto **già chiede 60 a chiunque**. Se KDE, XFCE e LXQt li consegnano, ⇒ **su di loro il buco
> non esiste proprio**. `[M]` KWin ne consegna **58,9** senza che gli si chieda niente di speciale.
>
> ⛔ **Il buco è di GNOME soltanto**, e questa voce è la sua.

**Che cos'è, in una riga.** ⛔ **Per farsi dare 60 fotogrammi da GNOME bisogna chiedergliene 90** —
e il prodotto non sa chiedere un numero che non sia 60.

Quel numero è **scritto dentro il programma** — `MOVIMENTO_FPS 60`, `src/figlio.c` · `MOVIMENTO_FPS` `[M]`
verificato il 25 agosto 2026 — e non esiste nessun modo di cambiarlo: né da riga di comando, né da
nessun'altra parte. ⚠ **Chiedere 60 va benissimo con chi obbedisce**: il difetto si vede solo con
chi, a 60, se ne dimezza.

**Da dove viene.** Messo il **13 agosto 2026** (primo commit che lo contiene: `92105b5`), quando il
multi-tenant non era ancora in discussione. ⛔ **Non è stata una scelta: è il numero ovvio** — lo
schermo va a 60, il browser disegna a 60. `DECISIONI.md` **§2.5-bis**.

**E il fatto che lo rende una voce e non una curiosità.** `[M]` 13 agosto: chiedendo alla **stessa**
Mutter, sulla stessa macchina e con la stessa scena, un ritmo diverso (monitor 120, freno 90), ne
sono usciti **61,4** invece di **31,5** — cioè **quanto KWin**. ⇒ ⛔ *Il tetto di GNOME non è di
Mutter: è nostro.* La ragione della decisione «su GNOME il desiderato non si promette» è cambiata il
13 agosto, e **la decisione non è mai stata rimessa in discussione**.

⚠ **Il perché è `[R]`, letto e non misurato**: nel codice di Mutter il freno tronca una divisione
(16666 invece di 16666,67), e chi cade sotto perde un tick intero. ⛔ E una riga che diceva *«legge
verificata su 13 punti»* **era falsa**, corretta il 13 agosto: il file di misura conteneva due celle,
tutt'e due non valide.

**Che cosa costa se non si fa MAI.**
⭐ **Poco, e va detto chiaro perché nessuno si spaventi.** Il prodotto funziona, i numeri sono onesti,
e la fluidità di GNOME l'utente l'ha giudicata accettabile **due volte** — il 9 agosto (§2.5-bis) e
il 25 agosto davanti a un video 4K. ⇒ **REMOTIX esce lo stesso.** Il costo è **un'occasione persa**:
su GNOME si resta a circa metà dei fotogrammi che quella macchina saprebbe dare — ⛔ e **su un solo
desktop dei quattro**, che è quel che rende questa voce rimandabile invece che urgente.
⛔ **E un costo che non è di fluidità**: finché il numero non si può chiedere, **una scelta
dell'utente la sta facendo una costante** — *più fluidità a testa* o *più gente insieme* — e la sta
facendo in silenzio.

**Che cosa serve prima.** ⛔ **Una misura che non esiste**: `[?]` quanto costa in **capienza** un
fotogramma in più a testa. Il tetto trovato nella fase 10 è **il lavoro di composizione**
(0,97 Gpixel/s, §6.11), quindi raddoppiare i fotogrammi per sessione dovrebbe **dimezzare** quante
sessioni ci stanno — ⚠ **ragionamento, non misura**.

**Quanto pesa.** `[?]` Non stimato. ⭐ Ma è **un lavoro solo, non quattro**: la costante è nostra e
condivisa, quindi il giorno che diventa chiedibile lo diventa **per tutti e quattro i desktop
insieme**. ⇒ È la ragione per cui questa voce sta qui e non dentro le fasi dei desktop nuovi:
`DECISIONI.md` §0.4 e la **regola di raccolta** qui sotto.

> ### ⛔⛔ E LA PARTE CHE **NON** ASPETTA LA FINE — la regola di raccolta
>
> ⭐ *«Per gli altri DE non ci portiamo dietro questo buco»* — l'utente, 25 agosto 2026.
>
> ⛔ **Non può voler dire una strada diversa per ogni compositore**: sarebbe un'eccezione per
> compositore, che il prodotto non ammette (`DECISIONI.md` §5.1-bis). ⇒ Quel che non ci si porta
> dietro **non è la cura: è l'ignoranza.**
>
> ⭐⭐ **All'ingresso di ogni desktop nuovo — fasi 12, 13, 14 — mezz'ora di prova e UNA domanda:
> *«ti chiedo 4K a 60: quanti me ne dai?»*** ⇒ Se ne dà 60, si scrive e si va avanti. ⛔ **Se ne dà
> la metà, è un GNOME anche lui**, e lo si sa il primo giorno invece che undici giorni dopo.
> ⚠ Il numero si scrive e basta: **nessuna riga di prodotto**.
>
> ⇒ Così il giorno di M1 ci sono **quattro numeri già in tasca** e si fa **una** modifica, invece di
> aprire **quattro indagini**. ⛔ E soprattutto non si scopre la stessa cosa quattro volte, per caso,
> ogni volta undici giorni dopo — che è **esattamente** com'è andata su GNOME.
>
> ⚠ **Questo pezzo sta in `PIANO.md`, nelle fasi 12-13-14**, non qui: è lavoro che succede **prima**
> della fine, e questo documento non è il posto delle cose che non aspettano.

---

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

## M4 · ⚠ Due client sullo stesso desktop nello stesso momento

**Che cos'è.** Oggi un utente ha **un** posto: chi arriva secondo viene respinto. Due schermi che
guardano lo stesso desktop insieme — per assistenza, per mostrare qualcosa a qualcuno — **non si può
fare**.

**Da dove viene.** `DECISIONI.md` **§7.3**: la terza possibilità che *non è mai stata chiesta da
nessuno*, e che è rimasta fuori senza essere discussa.

**Che cosa costa se non si fa MAI.** ⭐ **Niente al prodotto com'è**: nessuno l'ha chiesta, e
l'invariante I2 (un posto per utente) è stata **decisa apposta**. ⇒ È una **funzione nuova**, non un
buco.
⛔ **Ma cambia il protocollo**, e questo la rende diversa dalle altre: va decisa **prima** di
scriverlo, non dopo — e il protocollo è già scritto.

**Che cosa serve prima.** Che l'utente dica se la vuole. ⛔ Nient'altro: qui non manca una misura,
manca una decisione.

**Quanto pesa.** `[?]` Il palco persistente c'è già, quindi *«costerebbe poco»* (§7.3) — ⚠ ma è una
stima dell'8 agosto 2026, mai rifatta.

---

# ⚠ Le cose che qualcuno potrebbe voler mettere qui, e NON ci vanno

⛔ Perché il documento resti corto, va detto anche che cosa **rifiuta**.

| | dove va invece | perché |
|---|---|---|
| aggiornare il server senza buttare fuori nessuno | **`PIANO.md`, fase 14** | è già una fase. Non aspetta la fine |
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
