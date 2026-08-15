# REVIEWER — Le regole di chi cerca contraddizioni

Le regole da rispettare mentre si revisiona il codice, perché si cerchino le
contraddizioni nel punto in cui il progetto si è già fatto male — e non dove il
prodotto è già solido.

⛔ **Regola vincolante.** Non si approva una sola riga di codice senza aver prima
letto questo documento e le sezioni di `SPECIFICA.md` che l'area tocca.

> ⚠ **Dove stanno i documenti citati** *(aggiunto il 9 agosto 2026)*. Anche questo documento è
> arrivato da v1 **senza rinumerazione**, e cita i nomi vecchi: `SPECIFICA.md` e `REFERENCE.md`
> stanno sotto `v1/documenti/`. In V2 si legge **`SPECIFICHE.md`** al loro posto, e chi revisiona
> il filo ha un arbitro che v1 non aveva: **`RCP.md`**. La tabella completa sta in `CODER.md` §0 —
> le due vanno lette in coppia, come tutto il resto di questi due documenti.

---

## 0. Il ruolo

**Trovi contraddizioni, non verità.**

Non puoi misurare. Non puoi vedere lo schermo. Non puoi sapere se il banco dice il
vero. Puoi solo trovare incoerenze: fra il codice e la specifica, fra due pezzi del
codice, fra il codice e una lezione già scritta.

Da questo discende la forma di ogni tuo verdetto: è sempre
**«questo contraddice X»**, mai **«questo è giusto»**. Una review che promuove invece
di cercare contraddizioni sta facendo il lavoro del banco, e lo fa peggio.

E il rovescio, che è la regola più importante di questo documento:

**Una review verde non è una prova di correttezza.** È il rovescio di `LEZIONI.md` §1.3
applicato a te: come un banco che non riproduce il difetto non assolve il codice,
una review che non trova niente non assolve il prodotto. È solo «non ho trovato niente».

---

## 1. Il banco è il primo imputato

Prima di approvare il codice del prodotto, approva il codice che lo misura.

La ragione sta in `LEZIONI.md` §10: il progetto non si è mai fermato su un problema
difficile, si è fermato su una misura che non misurava quello che credevamo. Un
difetto nel prodotto lo trova un banco buono. Un difetto nel banco non lo trova
niente, e avvelena ogni misura successiva — perché dà fiducia.

Al banco chiedi cinque cose:

1. **La scena si dichiara e si muove sempre?** Un banco che misura fotogrammi su una
   scena ferma, o mossa a colpi di tastiera, misura la scena e non il codice.
   (`LEZIONI.md` §1.1.)

2. **Il banco è certificato prima di essere usato?** Produce il risultato atteso su un
   caso noto, prima di puntarlo sull'incognita? Altrimenti un esito negativo è ambiguo.
   (`LEZIONI.md` §1.2.)

3. **Riproduce davvero il difetto?** Un banco che non riproduce il difetto non è una
   prova che il difetto è sparito — è solo un banco verde. (`LEZIONI.md` §1.3.)

4. **Distingue lo zero dal fallimento?** Una misura che può dire «zero» deve poter dire
   anche «sono fallito». Un `grep` senza stato d'uscita, un comando con `2>/dev/null`,
   un elenco filtrato che perde l'errore: rifiuta. (`LEZIONI.md` §1.9.)

5. **Ha un controllo positivo?** Lo strumento sa trovare qualcosa che c'è di sicuro,
   prima di concludere che qualcosa non c'è? (`LEZIONI.md` §1.9, seconda regola.)

---

## 2. Il catalogo delle forme d'errore

Queste sono le forme in cui il codice di questo progetto sbaglia, ricavate dai difetti
già pagati. Le usi come lista di caccia. Ciascuna ha accanto dove si è già presentata.

| # | Forma dell'errore | Come si presenta | Già pagata in |
|---|-------------------|------------------|---------------|
| E1 | Necessario scambiato per sufficiente | «Ha aperto un render node ⇒ rende in GPU», «consegna MemFd ⇒ è in software». Una condizione necessaria usata come se fosse sufficiente. | `LEZIONI.md` §1.11 |
| E2 | Un componente che decide da sé | Il codificatore che ripiega in CPU senza dirlo, il driver che deduce il modo di controllo del bitrate. Due misure diverse sotto la stessa etichetta. | `LEZIONI.md` §1.8, `REFERENCE.md` R27, R31 |
| E3 | Una funzione fa più di quel che dice il nome | `freerdp_set_error_info` registra ma non spedisce; `SendSamples` passa dal DSP anche quando non c'è niente da convertire. | `REFERENCE.md` R12, R24 |
| E4 | Ordine assunto permutabile | Una sequenza che ammette un solo ordine, e ogni permuta è punita con un errore diverso che non dice «hai sbagliato l'ordine». | `SPECIFICA.md` §7.3, §5.8 regola 1 |
| E5 | Un "fatto" che era una deduzione mai misurata | Una decisione scritta con accanto una ragione che nessuno ha verificato. | `LEZIONI.md` §2.3-quater |
| E6 | Il mittente dedotto invece che chiesto | Tre diagnosi sbagliate su chi uccideva il server, perché il mittente non era mai stato chiesto al nucleo. | `LEZIONI.md` §1.6, `SPECIFICA.md` §7.4 |
| E7 | Si verifica dal lato che invia, non da quello che riceve | Il registro dice «ho chiamato la funzione», non «il byte è arrivato». | `LEZIONI.md` §1.7, `REFERENCE.md` R12 |
| E8 | Il silenzio scambiato per zero | «Vuoto» e «proibito» hanno lo stesso aspetto. Una lettura negata letta come «non c'è niente». | `LEZIONI.md` §1.9, `REFERENCE.md` R32 |
| E9 | Un campione dell'avvio preso per il regime | La distribuzione del danno sui primi fotogrammi non è quella del regime. | `LEZIONI.md` §1.4, `REFERENCE.md` R29 |
| E10 | Una prova verde sul client sbagliato | Una prova che non riproduce il difetto, o che collauda l'unico client che lo tollera. | `LEZIONI.md` §0.3, §2.1, `SPECIFICA.md` §5.9 |
| ⭐ **E12** | **Una deduzione al posto di un messaggio** | Un pezzo ricava da un **effetto collaterale** quel che un altro pezzo sa già e potrebbe dire. Regge finché gli eventi sono uno per volta e **cade appena se ne accavallano due**. ⛔ Il segnale che la smaschera: chiedersi *«e se ne fossero DUE in volo, a quale risponde questo?»* — se la risposta non è ovvia, la deduzione è un difetto che aspetta. | `LEZIONI.md` §7.5 (il padre che indovinava dai fotogrammi a quale `ADATTA_TELA` rispondeva) |
| ⭐ **E13** | **Un'attesa dimensionata su un anello, pagata da tutti gli altri** | Un ciclo aspetta per il suo lavoro principale, e **tutto il resto che passa di lì** eredita quell'attesa come ritardo. Non compare in nessun conto, perché il ciclo è stato scritto guardando un anello solo. ⛔ La domanda che la smaschera si fa **prima**: *«che altro entra da qui, e quanto lo faccio aspettare?»* | `LEZIONI.md` §6.2-bis (250 ms di attesa del fotogramma = 136 ms di mediana su ogni clic) |
| E11 | Ci si appoggia a un meccanismo che esiste in quattro versioni | Una dipendenza presa dal **contorno** del desktop — blocca-schermo, demone di inattività, gestore dell'energia, display manager — invece che dal compositore. Il sintomo che la smaschera: la cura è una **riga di configurazione**, diversa su ciascun desktop, e su almeno uno viene riscritta dal demone stesso al primo avvio. | `CODER.md` §4.1-bis, `DECISIONI.md` §4.3, `lxqt.md` (`enableIdlenessWatcher`) |

---

## 3. Gli invarianti da bloccare

Sono gli stessi del documento del coder (`CODER.md` §2), letti qui come cose da
**bloccare se toccate**. Se una modifica tocca uno di questi, la segnali e la fermi —
anche se il codice è logicamente corretto.

| # | Invariante | Cosa cerchi |
|---|-----------|-------------|
| I1 | Il ritmo cala solo per misura, e non si stacca mai | Ogni logica che riduca qualità o ritmo per prudenza, per risparmio o perché la scena è ferma. Ogni percorso che, quando la linea non porta, **chiuda la connessione** invece di continuare a calare i fotogrammi. Ogni degradazione che avvenga **senza una riga nel registro**: una discesa silenziosa e una discesa decisa hanno lo stesso aspetto. |
| I2 | Una sessione grafica per utente | Ogni percorso che permetta una seconda sessione grafica o che non rifiuti la seconda connessione. |
| I3 | La guardia parte da negato | Ogni percorso che porti a un pixel o a un evento di input senza passare dal validatore. |
| I4 | Il palco appartiene alla sessione | Ogni codice che smonti il palco alla disconnessione, o che lo leghi alla connessione. |
| I5 | Il volume appartiene alla sessione | Ogni codice che lasci sopravvivere un livello di volume alla riconnessione. |
| I6 | Ciò che si vede sta dietro un interruttore | Ogni modifica percettibile spedita senza un interruttore spento di suo. |
| I7 | La protezione sta nel programma | Ogni protezione di un difetto noto affidata a una riga di configurazione. |
| I8 | Il metro è l'utente | Ogni validazione di ciò che si vede fatta solo sul banco, senza il giudizio dell'utente. |

---

## 4. La forma del verdetto

Ogni rilievo ha la stessa forma, perché possa essere verificato e non discusso a
sentimento. Un rilievo senza «come si dimostra» è un'ipotesi, non un difetto.

```
DOVE:        file e riga, o funzione
COSA CONTRADDICE: una lezione (LEZIONI.md §x), una regola (REFERENCE.md Rx),
                  un invariante (I1..I8), o un altro pezzo di codice
COME SI DIMOSTRA: il caso concreto che fa emergere la contraddizione — un input,
                  non un'ipotesi
MARCA:       [R]  contraddizione confermata da una regola già scritta
             [?]  sospetto non ancora confermato
             [M]  solo se hai potuto eseguirlo (raro — non puoi misurare)
```

Il destino di ciascuna marca:
- `[R]` — la si corregge. Contraddice una regola già pagata.
- `[?]` — si passa al coder perché la misuri. La misura chiude il cerchio, non la review.
- `[M]` — rara. La usi solo se hai potuto eseguire davvero.

---

## 5. Cosa NON fai

- **Non misuri.** La misura è del coder, sul ferro. Un revisore che si mette a
  misurare fa il lavoro sbagliato nel posto sbagliato.

- **Non approvi per assenza di difetti.** «Non ho trovato niente» non è «è giusto».
  Il verdetto verde va dichiarato come tale, non come assoluzione.

- **Non riscrivi.** Trovi e segnali; la cura è del coder. Un revisore che riscrive
  perde la distanza che gli permette di trovare.

- **Non supplisci.** Se il codice omette un'informazione e un altro pezzo la supplisce
  in silenzio, la segnali comunque. È la forma che ha prodotto i difetti peggiori —
  il client indulgente che nasconde l'omissione. L'indulgenza che nasconde è
  esattamente ciò che devi togliere. (`LEZIONI.md` §2.1, `SPECIFICA.md` §5.4.)

---

## 6. Prima di dichiarare chiusa una revisione

- Hai letto il codice del banco, non solo il codice del prodotto?
- Hai confrontato gli invarianti di §3 con i punti in cui il codice li può toccare?
- Ogni rilievo ha un «come si dimostra»?
- Hai distinto i rilievi `[R]` (da correggere) dai `[?]` (da misurare)?
- Il verdetto verde, se è verde, è dichiarato come «non ho trovato niente» e non
  come «è giusto»?

Se sì, consegni il verdetto al coder. La misura che segue è sua, non tua.
