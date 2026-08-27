# Fase 11 — La rete di sicurezza

*Aperta il **25 agosto 2026**. Chiusa il —*

> ### 📋 QUESTO DOCUMENTO È SCRITTO ANCHE PER CHI NON CONOSCE IL PROGETTO
>
> È il disegno della rete anti-regressione di REMOTIX. ⇒ **§0** il contesto minimo, **§1-§5** il
> disegno, **§6** quel che la rete **non** prende, **§7** il piano di lavoro, **§8** le domande e le
> risposte avute.
>
> **Le marche usate ovunque nel progetto**, e vanno lette:
> `[M]` misurato da noi, sul ferro, con la data · `[R]` letto nel codice di un riferimento ·
> `[S]` letto in una specifica · `[?]` **ipotizzato, non ancora misurato**.
> ⛔ Una decisione che poggia su una `[?]` è una decisione presa a metà, e va scritta come
> provvisoria.

> ## ⭐⭐⭐ REVISIONATO DA DUE REVISORI ESTERNI — *25 agosto 2026, sera*
>
> La **prima stesura** di questo documento è stata sottoposta a due revisori esterni indipendenti
> (**Qwen** e **Gemini**), su richiesta dell'utente: *«meglio quattro occhi che due»*.
>
> ⭐ **Questa è la seconda stesura**, che integra i rilievi accolti. Le due revisioni sono
> convergenti su cinque punti — ⛔ e la convergenza di due lettori che non si sono parlati vale più
> di un rilievo solo (`PIANO.md` §0.4: *due programmi scritti dalla stessa mano che vanno d'accordo
> non confermano niente*).
>
> | il rilievo | chi | esito |
> |---|---|---|
> | **`logind` nel contenitore va provato PRIMA di costruire** | tutt'e due | ✅ **accolto**: diventa il **passo 0**, ed è una precondizione, non un'opzione (§3.5) |
> | **la marca da sola non basta** | tutt'e due | ✅ **accolto** (§4.2), nella forma **povera** di Qwen |
> | **C8 è la prova più importante ed è la più fragile** | tutt'e due | ⚠ **accolto il rilievo, la cura aspetta l'utente** (§4.4) |
> | **manca la politica del rosso** | Qwen | ✅ **accolto** (§5.2) |
> | **la rete non controlla sé stessa nel tempo** | Qwen | ✅ **accolto**: C11-C13 (§4) |
> | **prove cieche al desktop = lista comune + adattatori** | tutt'e due | ✅ **accolto** (§3.7) |
> | **famiglia veloce sotto i 3 minuti** | tutt'e due | ✅ accolto come **tetto provvisorio** da misurare (§5.1) |
> | **micro-macchine-virtuali (Firecracker) se il contenitore non regge** | Gemini | ⛔ **respinto**, §3.5-bis: si porta via la scheda grafica, cioè la ragione per cui le macchine virtuali erano già state scartate |
> | **confronto d'immagine con SSIM / visione artificiale** | Gemini | ⛔ **respinto**, §4.2: peso e dipendenze nuove per un problema che si chiude con una **tolleranza** |
> | osservazioni sull'ambiente della macchina di prova | Qwen §3.11 | ⛔ **fuori bersaglio**, escluse dall'utente |

---

# §0 · Il contesto minimo

## 0.1 Che cos'è REMOTIX

Un desktop remoto per Linux: **un server**, **nessun client da installare** — basta un browser
moderno — e un protocollo nostro che viaggia su WebTransport/QUIC.

Il server gira su una macchina Linux e, quando qualcuno si collega, **accende per lui una sessione
grafica sua**: un compositore Wayland privato, senza monitor fisico, catturato e codificato in
hardware, spedito al browser. Più persone possono avere ciascuna la propria, sulla stessa macchina e
sulla stessa scheda grafica.

| | |
|---|---|
| **il prodotto** | ~53 000 righe di C in `src/` (24 file) |
| **il client** | una pagina web servita dal server stesso |
| **il ferro di prova** | i5-13500T · 31 GB · **Intel UHD 730 integrata** — ⛔ non una scheda potente, e ogni numero di questo progetto va letto sapendolo |

## 0.2 A che punto è

**Dieci fasi chiuse.** L'ultima (multi-tenant) si è chiusa il 25 agosto 2026 sul giudizio
dell'utente: un video **4K** dentro il desktop remoto, con la banda del suo tablet strozzata a
**10 Mbit/s** — *«audio e video fluidi e in sync»*.

`[M]` **Sei sessioni** contemporanee sulla scena satura, **almeno undici** sul desktop vero (lì il
soffitto non è stato trovato: sono finiti gli utenti, non la macchina).

**Oggi funziona un solo desktop: GNOME.** Le prossime tre fasi aggiungono **KDE (Plasma)**,
**XFCE** e **LXQt**. ⛔ **Questa fase sta in mezzo, ed è stata decisa dall'utente proprio per stare
in mezzo.**

## 0.3 ⛔ Perché questa fase esiste — tre guasti veri, non un timore generico

Tutti e tre trovati **lo stesso giorno**, il 25 agosto 2026:

| il guasto | nascosto per | ⛔ perché era invisibile |
|---|---|---|
| **la sessione che nasce cieca** | giorni | il compositore, su una sessione **appena nata**, non annuncia nessun monitor ⇒ **nessuna applicazione può aprire una finestra**. ⛔ Invisibile perché **nessuno apriva mai una sessione NUOVA**: tutte le prove riusavano sessioni già aperte, che il monitor ce l'avevano |
| **il browser che non parte agli utenti dopo il primo** | **due fasi** | sulla macchina la cartella della cache degli utenti punta a una cartella condivisa — ⭐ **scelta voluta del proprietario, non un guasto**. ⛔ Ma **è il nostro prodotto** a creare dieci utenti che finiscono tutti a scrivere lì: il primo si prende la cartella, e per gli altri nove il browser non nasce |
| **cinque banchi che contavano zero fotogrammi** | un giro | una cura al registro ne aveva rotto le espressioni, e la funzione tornava **0 invece di «non lo so»** |

> ### ⛔⛔ E TUTTI E TRE SONO LO STESSO ERRORE VISTO DA TRE LATI
>
> 1. **Si ripartiva sempre dallo stesso punto**, e quel punto era già a posto. Una prova che riusa
>    uno stato che funzionava **non può trovare un guasto della nascita**, per costruzione.
> 2. **Si contava il processo invece di guardare il pixel.** `[M]` Il conto dei processi diceva
>    **1** sia con la finestra sia senza — **finestra o non finestra, lo stesso numero.**
>
> ⚠ **E la contromisura non è «più prove».** Ce n'erano già **più di cento**, e i tre guasti sono
> passati **in mezzo a loro**. ⇒ Il problema non è la quantità: è **da dove partono** le prove e
> **che cosa guardano**.

## 0.4 ⛔ E la ragione per cui va fatto ADESSO

Da qui in avanti ogni fase aggiunge un desktop, e ogni desktop si aggiunge **toccando il codice
comune**. Chi lo tocca in quel momento sta guardando il desktop nuovo, e non ha nessun motivo di
sospettare di aver appena rotto quello vecchio — perché quello vecchio funzionava.

⇒ ⛔ **Un guasto che oggi si trova una volta, con quattro desktop si troverà quattro volte — e nel
caso peggiore su tre non si troverà affatto**, perché nessuno pensa a riprovare il primo.

⭐ **E il costo vero di un guasto non è ripararlo: è la distanza fra quando è entrato e quando lo si
trova.** Il guasto del browser, una volta capito, è stato curato in un pomeriggio. È costato due
fasi perché era **vecchio**, e perché aveva addosso una spiegazione sbagliata — *«non è nostro»* —
che è la spiegazione che **non chiede di continuare a cercare**.

---

# §1 · Il mandato, e il metro

## 1.1 Che cosa deve produrre

**Un modo di accorgersi da soli che qualcosa si è rotto, prima che lo scopra l'utente.**

L'utente non vede niente di nuovo sullo schermo — ⭐ **e questo è il punto**: vede che le cose che
funzionavano continuano a funzionare quando arrivano i desktop nuovi.

## 1.2 ⛔⛔ Il metro della fase, e non è «quante prove girano»

> ### Il metro è uno solo: **che cosa la rete PRENDE.**

⛔ **Il collaudo è già scritto, ed è severo.** La rete si punta contro il codice del 25 agosto 2026 e
**deve diventare rossa da sola su tutti e due i guasti**, ⛔ **senza che nessuno le abbia detto dove
guardare**:

| | |
|---|---|
| **collaudo A** | la **sessione che nasce cieca** |
| **collaudo B** | il **browser che non parte al secondo utente** |

⇒ ⛔ **Se non li prende, non è una rete: è un rituale.** E se alla fine non ha preso niente che
l'occhio non avrebbe preso, **la fase è fallita e va detto**.

## 1.3 ⚠ Il pericolo di questa fase, dichiarato in apertura

Una fase così è **precisamente** il tipo di lavoro che può gonfiarsi fino a mangiarsi il progetto che
doveva proteggere. ⇒ Le tre guardie che ci mettiamo addosso:

1. ⛔ **Poche prove, corte.** Una rete con cento maglie che nessuno legge è cerimonia, e la cerimonia
   costa tempo esattamente come i difetti.
2. ⛔ **Ogni prova si giustifica su un guasto VERO**, già successo o che sarebbe successo. Non su un
   timore.
3. ⛔ **Le prove che non prendono niente si buttano**, e si scrive che sono state buttate.

⚠ **E la revisione esterna ha aggiunto tredici cose.** ⛔ **Non sono state accolte tutte**, e le
non-accolte sono scritte in testa con il motivo — perché *«il revisore ha detto»* non è una ragione
per far crescere una rete che deve restare corta.

---

# §2 · Le decisioni già prese — ⚠ **non sono in discussione**

*Prese dall'utente il 25 agosto 2026, discutendo questa fase.*

| # | la decisione | la ragione, com'è stata data |
|---|---|---|
| **D1** | **Un contenitore per desktop**, non macchine virtuali | ⛔ la macchina virtuale si porta via la **scheda grafica vera**, e tutti i nostri numeri vengono da lì. Il contenitore sta sulla stessa macchina e la usa davvero |
| **D2** | ⭐ **CORRETTA il 26 agosto 2026**: una scatola può avere **fino a dieci** inquilini — *«è un dato già misurato con GNOME»*. ⇒ La rete ne usa **due** | il vincolo era sulla **capienza**, che non si rifà; ⛔ non sulla **correttezza a più inquilini**, che è un'altra domanda. `DECISIONI.md` §4.6-terdecies ⇒ **§4.4 è chiusa: C8 sta in una scatola** |
| **D3** | **4K · 60 fotogrammi/s è il bersaglio per TUTTI i desktop** | *«è il tetto che chiediamo a tutti»*. Nessun bersaglio su misura per compositore |
| **D4** | ⛔ **Niente eccezioni per compositore** | *«non voglio mettere delle eccezioni nel progetto»*. ⚠ **Riguarda il PRODOTTO**: §3.7 spiega perché gli adattatori del banco non la violano |
| **D5** | **I contenitori vanno tenuti allineati** | *«se sul container GNOME abbiamo remotix v1 e sul container KDE remotix v1.2 andiamo a sbattere»* |
| **D6** | Le cose del «dopo» non entrano qui | vanno in `MASTERPLAN.md`, con scritto **che cosa costa non farle mai** |

⚠ **E un vincolo che non è una decisione ma un fatto**: `[M]` **la scheda grafica è UNA**. Quattro
contenitori possono essere accesi insieme, ma **non possono misurare insieme**.

---

# §3 · Il disegno

## 3.1 La rete è fatta di tre pezzi, e i contenitori sono uno solo

| | | |
|---|---|---|
| **DOVE** si prova | i quattro contenitori + la macchina vera | §3.2 |
| **CHE COSA** si controlla | la lista corta — ⭐ **è questa la rete vera** | §4 |
| **QUANDO** parte | il gancio che la fa girare da sola | §5 |

## 3.2 I contenitori — e le tre regole che li tengono onesti

**Quattro contenitori, uno per desktop, sulla stessa macchina, con accesso alla scheda grafica
vera.** Dentro ciascuno: un desktop, un utente, e il server.

> ### ⛔ R1 · **Un solo binario, compilato una volta, copiato in tutti e quattro**
>
> ⛔ **Non compilato dentro ciascun contenitore**: se ogni scatola si compila il suo, si hanno
> quattro binari diversi e i confronti non valgono niente (D5).

> ### ⛔ R2 · **Le ricette dei contenitori dichiarano le versioni esatte**
>
> ⛔ *«l'ultima disponibile»* **è una data travestita da versione**. Una scatola costruita martedì e
> una costruita giovedì differiscono anche a parità del nostro codice, perché in mezzo si è mosso il
> magazzino dei pacchetti. ⇒ Poi si vede un numero peggiore su XFCE e si dà la colpa a XFCE, mentre
> la colpa era di **giovedì**.

> ### ⛔ R3 · **L'allineamento si VERIFICA, non si dà per buono**
>
> Ogni contenitore dichiara **l'impronta del binario E della propria ricetta**; la rete le confronta
> **prima** di credere a qualunque numero, e **si ferma dichiarandolo** se non combaciano.
> ⭐ **E la ricetta conta quanto il binario**: se una scatola si ricostruisce e tira dentro una
> versione più nuova del desktop, ⛔ l'impronta del binario **combacia lo stesso** e la rete
> rassicura mentre l'ambiente è cambiato sotto. ⇒ È il controllo **C11**.
> ⚠ Nel progetto c'è già il precedente: un controllo che verifica che *«quello che misuro è quello
> che leggo»*, nato da questa stessa ferita.

## 3.3 ⭐⭐ La regola dei confronti: **si muove una cosa per volta**

⛔ Non è vero che le scatole debbano essere sempre identiche: se lo fossero, la rete non servirebbe a
niente — tutto il senso è confrontare **prima** e **dopo** una modifica.

| il confronto | che cosa cambia | a che domanda risponde |
|---|---|---|
| **stesso desktop, due versioni del nostro codice** | il nostro codice | *«la modifica ha rotto qualcosa?»* — ⭐ **è la rete anti-regressione** |
| **stessa versione del nostro codice, quattro desktop** | il desktop | *«questo desktop si comporta diversamente?»* — serve quando ne arriva uno nuovo |

⛔ **Quel che non si fa mai è muovere tutt'e due insieme.** Codice nuovo su KDE contro codice vecchio
su GNOME **non risponde a niente, e sembra rispondere.**

> ### ⚠ E il giorno in cui arriva un desktop nuovo, «una cosa per volta» diventa difficile
>
> *Rilievo di Qwen §3.6, accolto.* Aggiungere KDE significa **due modifiche insieme**: si tocca il
> codice comune **e** nasce una scatola nuova. ⇒ La regola si salva **spezzando in tre passi**:
>
> 1. le modifiche al **codice comune**, provate sui desktop **già esistenti** — ⛔ **prima** che la
>    scatola nuova entri in gioco. È qui che si prende la regressione;
> 2. il **codice nuovo** del desktop, che i vecchi non attraversano;
> 3. l'**accensione** della scatola nuova.
>
> ⛔ Se il primo passo non si può separare, **va dichiarato nel documento della fase**: da quel
> momento un rosso ha due sospetti invece di uno, e chi legge deve saperlo.

## 3.4 ⭐⭐ Le due famiglie di prove — e solo una guadagna dal parallelo

| famiglia | che cosa chiede | come gira | quanto costa |
|---|---|---|---|
| ⭐ **FUNZIONA** | risposte sì/no: la sessione nasce, la finestra si apre, si vede, il tasto arriva, il suono c'è | **tutte e quattro insieme** | minuti |
| ~~**VA VELOCE**~~ | ⛔ **non esiste, e non si fa** — vedi il riquadro qui sotto | | |

> ### ⛔ E «VA VELOCE» era una contraddizione, sciolta il 27 agosto 2026
>
> Questa tabella dichiarava **due** famiglie; ⛔ **§6 dichiara che la rete non è una rete di
> prestazioni**; e `[M]` nel gancio quella famiglia **non è mai esistita**: ci sono `funziona`,
> `rete`, `rete-intera`, `tutto`, `desktop-nuovo`.
>
> ⇒ ⭐ **Ha ragione §6, e la famiglia non va creata.** Le quindici maglie sono tutte sì/no; una
> famiglia di numeri duplicherebbe i ~40 banchi delle fasi 9 e 10 **fuori dalle condizioni in cui
> quei numeri valgono**, e sarebbe la prima cosa che qualcuno smetterebbe di far girare.
> ⇒ ⚠ Quel che resta vero di questa riga è **come girano le misure quando si fanno**: ⛔ una scatola
> per volta, in fila, col lucchetto della scheda. Ed è una regola sul **lucchetto**, non un catalogo.
> ⇒ ⛔ **Il buco che resta si dichiara in §6**: *nessun banco confronta ieri con oggi.*

⭐ **E la buona notizia sta nella divisione**: la famiglia veloce è quella che serve **spesso**, e i
tre guasti di ieri erano **tutti** suoi — nessuno era un problema di velocità, erano tutti *«non si
vede niente»*.

⛔ **Ma «le quattro scatole non si disturbano» è affermato, non dimostrato** — rilievo di Qwen §3.10,
accolto. ⇒ Va **misurato** una volta: le stesse prove da sole e in parallelo devono dare lo stesso
esito, e il tempo non deve esplodere. È il controllo **C14**, e finché non è girato la parola resta
`[?]`.

## 3.5 ⛔⛔ IL PASSO 0 — **il contenitore va validato PRIMA di costruire**

*Rilievo su cui **tutt'e due i revisori** convergono, e il più grave dei due giri.*

Il prodotto si appoggia parecchio al pezzo di sistema che tiene il conto di chi è collegato
(`systemd`/`logind`: linger, sessioni d'utente, il guardiano che chiude le sessioni morte). ⛔ Dentro
un contenitore quel pezzo **può comportarsi diversamente**.

> ⛔⛔ **Il rischio non è «una prova sbagliata»: è che l'intero strato dei contenitori diventi un
> simulacro** — cioè **la peggiore forma di sicurezza, quella falsa.**

⚠ **E la prima stesura era ottimista**, e la correzione è accolta: diceva *«se non regge, quella
singola prova torna sulla macchina vera»*. ⛔ Se quel pezzo non regge, a tornare indietro non è **una**
prova: è **una famiglia di comportamenti**.

### ✅ La regola che sostituisce la `[?]`

> **Il contenitore è valido solo se supera il passo 0.** Se il passo 0 fallisce, le prove che
> dipendono da quel comportamento **restano sulla macchina vera**, e lo si scrive.
> ⛔ **Non è un'opzione: è una precondizione.** Nessuna scatola definitiva si costruisce prima.

### Le otto cose che il passo 0 verifica — *mezza giornata, non di più*

| # | | deve risultare |
|---|---|---|
| 1 | la sessione d'utente **esiste** ed è del tipo giusto | come sulla macchina vera |
| 2 | il **linger** funziona: i servizi dell'utente vivono senza che nessuno abbia fatto login | idem |
| 3 | il **server parte dentro la sessione d'utente**, senza trucchi che sulla macchina vera non si potrebbero fare | idem |
| 4 | quando la sessione finisce, ⛔ **i processi muoiono davvero** e non restano orfani | idem |
| 5 | la cartella privata dell'utente per i socket esiste, è scrivibile, ⛔ **e non è condivisa fra contenitori** | idem |
| 6 | il canale di messaggi della sessione esiste e il desktop lo vede | idem |
| 7 | il **compositore nasce, vede un'uscita**, e un'applicazione riesce ad aprire una finestra | idem |
| 8 | la **cattura e il codificatore hardware** sono raggiungibili, e i fotogrammi escono | idem |

⇒ ⛔ **Il contenitore è accettabile solo se tutti e otto si comportano come sulla macchina vera**
per i punti che il prodotto usa davvero. **L'esito diventa `[M]`, con la data.**

## 3.5-bis ⛔ La strada di ripiego, se il passo 0 fallisce — **e non è quella proposta**

Gemini propone **micro-macchine-virtuali** (Firecracker). ⛔ **Respinto**: una macchina virtuale si
porta via la **scheda grafica vera**, che è esattamente la ragione per cui le macchine virtuali erano
già state scartate (D1). Su una scheda **integrata** il passaggio della GPU a una macchina virtuale
non è una strada praticabile, e senza scheda i numeri di `VA VELOCE` non valgono niente.

⭐ **Le due strade di ripiego vere, in quest'ordine:**

1. un contenitore **di sistema** invece che d'applicazione (⭐ **suggerito da Gemini stesso**, ed è il
   suo consiglio buono su questo punto): stessa scheda grafica, ma un avvio vero dentro;
2. ⚠ quelle prove **restano sulla macchina vera**, e le scatole tengono solo il resto — con scritto
   **quali** prove sono rimaste fuori e perché.

## 3.6 ⛔⛔ La rete è un banco anche lei, e va certificata

`[M]` Nella fase 10 sono stati trovati **sei difetti nello strato che coordina i banchi** — non nei
banchi: nel pavimento su cui poggiano. Fra questi: un lucchetto che si poteva **aspettare sé stessi**
(⛔ 80 minuti di scheda grafica bloccati per cinque prove, **e nessuna riga rossa da nessuna parte**),
e un comando di pulizia globale che ha rischiato di **uccidere il lavoro di un'altra prova in corso**.

> ⭐⭐ **La regola: ogni cosa da cui dipende una misura è una cosa da certificare — e il fatto che non
> produca numeri non la esenta.**

⇒ La rete ha un `--certifica` suo: si inietta un guasto noto, e si verifica che la rete **lo veda**.
⛔ **Ogni prova della lista ha, obbligatoriamente, il suo guasto innestato** (colonna «come so che sa
dare rosso» in §4), **e quel caso va fatto girare, non immaginato**.

> ### ⚠ E il rilievo di Qwen (§3.8), accolto: **così la rete è certificata contro il PASSATO**
>
> I guasti che si iniettano sono guasti **già noti**. ⛔ Ma i desktop nuovi porteranno guasti **loro**:
> quello tipico di GNOME non è detto sia quello tipico di KDE.
>
> ⇒ ⭐ **Regola aggiunta**: ogni desktop nuovo entra con **almeno un guasto suo, inventato e fatto
> girare** — non serve che sia già accaduto, serve che sia **plausibile** e che la rete lo veda.
> E il registro di quel che è stato iniettato, quando, e con che esito, **è parte della rete** (C13).

## 3.7 ⭐⭐⭐ Come si resta ciechi al desktop — **lista comune, adattatori sotto**

*Risposta convergente dei due revisori alla domanda più difficile.*

⛔ **Il pericolo, detto da Gemini**: per non scrivere quattro liste si finisce con **una lista sola
piena di «se il desktop è KDE allora…»**, che è la stessa cosa travestita.

⭐ **La forma che regge — tre livelli:**

| livello | che cosa dice | vale per |
|---|---|---|
| **1 · esiste** | la sessione nasce, c'è un'uscita, l'immagine non è degenere | ⭐ **tutti e quattro, identico** |
| **2 · si vede** | la marca c'è, la finestra si vede, l'input cambia i pixel | ⭐ **tutti e quattro, identico** |
| **3 · come si fa** | come si avvia questo compositore, quale protocollo di cattura, dove si mette la marca | ⛔ **specifico**, e sta in un **adattatore** per desktop |

> ⭐⭐ **La rete non deve sapere tutto di ogni desktop: deve sapere che cosa CHIEDERE.**
> La lista principale (C1-C14) resta **una**; ogni desktop porta un adattatore piccolo che risponde
> alle stesse quattro domande.

⚠ **E questo NON viola D4**, e va detto perché la confusione è facile: D4 vieta le eccezioni **nel
prodotto** — un ramo KDE diverso dal ramo GNOME dentro `src/`. ⛔ Qui siamo nel **banco**, e un banco
che non sapesse come si avvia un compositore non potrebbe provarlo affatto. ⇒ **Il confine**: se un
adattatore comincia a contenere *comportamento del prodotto* invece che *modo di avviarlo e
guardarlo*, ⛔ **è un'eccezione travestita**, e va tolta.

---

# §4 · La lista — ⭐ **è la rete vera**

⚠ **Le due colonne che di solito mancano sono la terza e la quarta**, e sono quelle che spiegano i
tre guasti di ieri: *da dove parte* e *che cosa guarda*.

## 4.1 Le prove del prodotto

| # | che cosa deve essere vero | ⭐ da dove parte | ⭐ che cosa guarda | ⛔ come so che sa dare rosso | dove gira |
|---|---|---|---|---|---|
| **C1** | ⭐⭐ **la sessione nasce e si VEDE** | ⛔ **da zero**: utente mai usato, sessione nuova, mai riusata | un'immagine: ⭐ **marca presente** *e* **immagine non degenere** (§4.2) | (a) sessione **senza monitor** ⇒ rosso, ⛔ distinguendo *«nero»* da *«non ho guardato»* · (b) ⭐ **immagine con i colori spostati apposta** ⇒ **deve restare VERDE**, o la soglia è troppo stretta e la rete si butta fra due settimane | scatole |
| **C2** | ⭐⭐ **una finestra si apre** | da zero, sessione nuova | ⛔ **il pixel**: la finestra si deve VEDERE — non si conta il processo | applicazione che muore subito ⇒ rosso. ⚠ E il controllo che il conto dei processi **non** basta: `[M]` diceva 1 in tutt'e due i casi | scatole |
| **C3** | **i fotogrammi arrivano, e la scena CAMBIA** | sessione nuova, **scena dichiarata e in movimento** | ⭐ **canarino anti-morte**: fotogrammi > 0 · **non crollati** rispetto a un riferimento grezzo · ⛔ **i fotogrammi consecutivi sono diversi fra loro** | si ferma il codificatore ⇒ rosso · ⭐ si manda **lo stesso fotogramma ripetuto** ⇒ rosso (immagine congelata). ⚠ E *«scena ferma»* **non** deve dare rosso | scatole |
| **C4** | **il tasto arriva fino allo schermo** | sessione nuova | ⛔ **il pixel, prima e dopo**: immagine · tasto · immagine, e i pixel **della zona attesa** devono cambiare | si stacca il percorso dell'input ⇒ rosso | scatole |
| **C5** | **il suono c'è e non è silenzio** | sessione nuova | i byte che arrivano al client, e che **non siano silenzio** | si toglie la sorgente ⇒ rosso | scatole |
| **C6** | **si stacca e si ritrova** | sessione **già viva** (⚠ qui è giusto così) | dopo il riattacco: stessa sessione, stesse finestre, **viste nell'immagine** | si uccide la sessione ⇒ rosso | scatole |
| **C7** | **si chiude tutto, e non resta niente** | dopo una sessione finita | processi orfani, socket, lucchetti, scheda grafica tornata a riposo | si lascia un processo apposta ⇒ rosso | scatole |
| **C8a** | ⭐⭐⭐ **il SECONDO utente apre il browser** | ⛔ **da zero, e con DUE utenti** | ⛔ il pixel: il browser **rende una pagina** (`#FF00FF`, tolleranza dichiarata) | ✅ **misurato il 26 ago 2026**: si disfa la cura della provvista ⇒ ⛔ il **secondo** dà rosso, il primo no | ⭐ **qualunque scatola** — non passa dal prodotto |
| **C8b** | e la stessa pagina **si vede DAL CLIENTE** | come sopra | il pixel, attraverso il prodotto | ⭐ **misurato il 27 ago 2026**: il verdetto è una **differenza** — primo fotogramma senza pagina, ultimo con. Desktop nero ⇒ `3`, pagina già presente ⇒ `3`, ⛔ mai un verde regalato | ⭐ **gnome**, e solo lì |
| **C9** | **il registro dice DI CHI parla** | qualunque | ogni riga del registro ha l'inquilino | si toglie il nome ⇒ rosso | scatole |
| **C10** | **le due copie gemelle del protocollo combaciano** | prima di compilare | i due file | se ne cambia uno ⇒ rosso. ⚠ **c'è già**, e va solo agganciata | ovunque |

### ⭐⭐⭐ Che cosa di questa lista ESISTE, al 27 agosto 2026 — **tutta**

| | |
|---|---|
| le prove del **prodotto** | **C1 · C2 · C3 · C4 · C5 · C6 · C7 · C8a · C8b · C9 · C10** — ⭐ **undici su undici** |
| le prove che guardano **la rete** | **C11 · C12 · C13 · C14** — e ⭐ **C15**, che non era nella lista e serviva |

⛔ **Niente è più bloccato**, e la ragione va detta perché è la storia della giornata: le cinque prove
dichiarate «bloccate dalle sessioni cieche» **non erano bloccate**. `[M]` Il monitor di una sessione
headless nasce **quando un consumatore si aggancia al flusso** ⇒ **mentre un cliente è attaccato, lo
schermo c'è**, che è esattamente la condizione in cui quelle cinque lavorano. ⇒ §7-bis.19.

## 4.2 ⭐⭐ Le prove che guardano la RETE, non il prodotto

*Rilievo di Qwen §3.12, accolto: **la rete può continuare a girare e smettere di essere credibile.***

| # | che cosa verifica | ⛔ il guasto che prende |
|---|---|---|
| **C11** | ⭐ **l'allineamento**: stessa impronta del binario in tutte le scatole, ricetta dichiarata e datata, ⛔ **nessuna scatola costruita con «l'ultima disponibile»** | è il guasto di D5, quello che l'utente ha visto per primo: *«remotix v1 su una scatola e v1.2 sull'altra»* |
| **C12** | **il gancio è vivo**: esiste, è eseguibile, e c'è traccia dell'ultima volta che ha girato | ⛔ **il gancio spento in silenzio** — il modo in cui muoiono queste reti |
| **C13** | **la certificazione è recente**: negli ultimi N giri almeno un guasto è stato iniettato e la rete ha dato rosso | una rete che non è più capace di dare rosso **ha esattamente l'aspetto di una rete che non trova niente** |
| **C14** | ⭐ **le scatole non si disturbano**: le stesse prove da sole e in parallelo danno lo stesso esito | §3.4 lo **afferma**; questo lo **misura** |
| **C15** | ⭐⭐ **la metà remota gira davvero**: il gancio ha due metà su due macchine, e questa guarda che quella con le scatole non abbia smesso | ⛔ **il guasto che nessuna delle altre prende**: macchina di prova spenta per sempre, e `[M]` **C12 e C13 restano verdi**. Il segno non è il nome della macchina: è **una maglia che vuole una scatola e arriva a un giudizio invece che a un `3`** |

⚠ **Sono quattro, e non di più, di proposito.** Sono tutte a costo quasi zero e nessuna accende una
sessione.

## 4.3 ⭐⭐⭐ Come si guarda un'immagine senza costruire una prova fragile

⛔ **Il confronto pixel-per-pixel con un'immagine di riferimento marcisce in una settimana**: cambia
un carattere, cambia lo sfondo, e la prova diventa rossa senza che niente sia rotto. ⇒ Una prova che
dà rosso a vuoto **viene spenta da chi lavora**, ed è peggio di nessuna prova.

### ⛔ E la marca da sola non basta — *rilievo accolto, tutt'e due i revisori*

La marca dice *«qualcosa c'è»*, ⛔ **non dice «quel che c'è è giusto»**. I casi che passerebbero:

| | |
|---|---|
| metà schermo nero, e la marca sta nell'altra metà | ⛔ verde |
| tutto rovinato intorno alla marca | ⛔ verde |
| immagine **congelata**: la marca c'è, ma niente si aggiorna | ⛔ verde |

### ⭐ La forma accolta — **tre controlli poveri**, e nessuno sa che aspetto abbia un desktop

1. **la marca**, con ⛔ **una tolleranza dichiarata** — non il colore esatto. *Rilievo di Gemini,
   accolto*: i compositori applicano profili di colore e riscalamenti, e un `#FF00FF` può tornare
   indietro leggermente diverso. ⛔ Una prova che pretende il colore esatto è già morta;
2. **l'immagine non è degenere**: non tutta nera, non tutta di un colore, abbastanza varia. ⭐ È un
   controllo di **sanità**, non di estetica, e non richiede di sapere come è fatto nessun desktop;
3. **la zona attesa cambia** quando deve cambiare (C4) e **i fotogrammi consecutivi differiscono**
   quando la scena si muove (C3).

⛔ **Respinta la visione artificiale** (SSIM, riconoscimento di forme) proposta da Gemini: porta
dipendenze e peso per un problema che si chiude con una **tolleranza** e un istogramma. ⚠ Se la
tolleranza non bastasse, ⭐ **allora** quella strada torna sul tavolo — e sarà una decisione con una
misura sotto, non un'anticipazione.

### ⚠ E il metro va tarato prima di essere creduto

La marca dev'essere **ritrovata quando c'è** e **non ritrovata quando non c'è**. ⭐ E il testimone
esiste già: si attacca alla sessione col cliente di prova, si fa dare i fotogrammi dal filo e ne tira
fuori un'immagine — **con il terzo esito distinto**: `0` ho guardato e regge · `1` ho guardato e non
regge · ⛔ **`3` non ho potuto guardare**, che non è un rosso.

## 4.4 ❓ **LA DOMANDA CHE RESTA ALL'UTENTE** — C8 e il senso di D2

⛔ **Tutt'e due i revisori dicono la stessa cosa, ed è il rilievo più serio**: C8 è **la prova più
importante** — è metà del collaudo — **ed è la più difficile da eseguire**. ⇒ *Una prova costosa da
preparare viene eseguita meno; una prova eseguita meno lascia il guasto nascosto più a lungo.*

⭐⭐ **E portano una distinzione che la prima stesura non faceva:**

| tipo di prova | domanda | D2 |
|---|---|---|
| **capienza** | *quanti utenti ci stanno insieme?* | ⛔ **già misurata**, non si rifà |
| ⭐ **correttezza a più utenti** | *il secondo utente riesce a fare quel che deve?* | ⚠ **non è capienza**, e D2 non parla di questo |

> ## ✅⭐⭐ RISPOSTA DELL'UTENTE — *26 agosto 2026*
>
> > *«Per quanto mi riguarda un container può anche avere 10 utenti, è un dato già misurato con
> > GNOME.»*
>
> ⇒ ⭐ **C8 sta in una scatola**, con due inquilini — non dieci, perché la domanda è la correttezza,
> non la capienza. ⛔ Cade la strada «C8 sulla macchina vera con uno script di ricostruzione»: la
> prova più importante **non sarà anche la più difficile da eseguire**, che era il rilievo dei due
> revisori.
> ⚠ E resta in piedi l'altra metà del rilievo, **rimandata di proposito**: farne tre (browser ·
> finestra · input) si valuta **solo dopo** che la prima ha preso qualcosa.

⇒ *(la domanda che era stata posta, e la sua risposta è qui sopra:)*

> **D2 vieta un contenitore con DUE utenti dedicato alla sola correttezza?**
>
> | se D2 è **assoluta** | C8 resta sulla macchina vera, ⛔ e allora **serve uno script che ricostruisca lo stato da zero** — utenti, cartelle, la condizione che genera il guasto, il primo utente, il secondo, e il giudizio sull'immagine. ⚠ Senza quello script, C8 non è una prova: è una cosa che sa fare solo chi c'era |
> |---|---|
> | se D2 riguarda **la capienza** | ⭐ una scatola speciale a due utenti, ⛔ **due utenti e basta — non dieci**, e non torna a misurare capienza |

⚠ **E in tutt'e due i casi**, il rilievo di far diventare C8 **tre prove** (browser · finestra ·
input) è ⛔ **rimandato**: la fase deve restare corta, e la terza guardia di §1.3 vale anche contro i
revisori. ⇒ Si comincia con **una**, e si aggiungono le altre **solo se quella prende qualcosa**.

## 4.5 ⛔ La regola sugli esiti, che vale per ogni prova della lista

| uscita | vuol dire | si rifà? |
|---|---|---|
| 0 / 1 | ⭐ **un giudizio** — regge / non regge | ⛔ **mai** |
| **3** | *«non giudico»*: ha misurato, e qualche pezzo non ha potuto parlare | ⛔ **mai** |
| 2 | il terreno non regge, o l'uso è sbagliato | ⛔ mai — **un terreno cattivo si GUARDA** |
| **4** | ⭐ **il turno non è mai arrivato** (lucchetto della scheda) | ✅ **sì** |

⛔⛔ **E il `3` NON si rimette in coda, di proposito**: è la strada esatta per **misurare due volte
finché esce il numero che piace**. In un progetto che ha già ritirato due conclusioni per questa
ragione, la tentazione si chiude con una regola, non con la buona volontà.

---

# §5 · Quando parte, e che cosa succede quando dice rosso

⛔ **Le tre volte in cui, ieri, nessuno ha riprovato il vecchio, nessuno era distratto: semplicemente
non c'era il gancio.**

## 5.1 Il gancio — ⛔ definito per percorso, non per buona volontà

| quando | che cosa gira |
|---|---|
| ⭐ **si tocca `src/`** (il prodotto) | la famiglia **FUNZIONA**, su tutte e quattro le scatole insieme |
| si toccano **i banchi o la rete** | C11-C14 (le prove della rete) |
| **prima di chiudere una fase** | tutto, **VA VELOCE** compresa, una scatola per volta |
| **all'ingresso di un desktop nuovo** | tutto sul nuovo, ⭐ **più la regressione sui vecchi** — e senza riscrivere una riga della lista |

⚠ **Il tetto di tempo**, e i due revisori convergono: **sotto i 3 minuti** per la famiglia veloce.
Sopra i 5 comincia il rischio che venga spenta; sopra i 10 è quasi certo. ⛔ E se il tempo vero lo
supera **si tagliano prove**, non si alza il tetto.

> ### ⭐ E ADESSO IL TETTO È MISURATO — *`[M]` 26 agosto 2026*
>
> La famiglia veloce, girata davvero: **153 secondi su 180**. ⛔ **Il tetto è pieno**: qualunque
> maglia in più va **scambiata** con qualcosa che esce, non sommata.
>
> Ci stanno **C11 + due giri di C1**, e basta. ⇒ Quel che è rimasto fuori, e quanto costa:
>
> | tagliato | ⛔ che cosa costa |
> |---|---|
> | ⛔⛔ **C8, tutt'e due le prove** | **il taglio più caro**: la maglia più importante della lista **non viene guardata a ogni modifica**. Resta nel giro completo |
> | **C1 dal terzo giro in poi** | oggi non morde — `[M]` 10 sessioni su 10 nascono cieche, e due giri bastano ad accorgersene. ⚠ **Il giorno in cui il difetto sarà curato e tornerà raro, due giri non basteranno** |
> | **il passo 0** | guarda l'ambiente, che non cambia quando cambia `src/`. ⭐ E una scatola ricostruita di nascosto la prende **C11**, che nella famiglia veloce c'è — è per questo che c'è |
>
> ⭐ E il gancio **salta** la maglia che non ci sta invece di troncarla, e **scrive nel registro che
> cosa ha saltato e perché**: ⛔ troncare darebbe un rosso che non è del prodotto (`LEZIONI.md` §1.45).

### ⚠ Due cose sul gancio che si sono decise scrivendolo

1. ⭐ **Si aggancia PRIMA DI MANDARE** (`pre-push`), non a ogni salvataggio. ⛔ Tre minuti a ogni
   commit sono esattamente la cosa che questa sezione dice che fa **spegnere** un gancio. Chi vuole
   `pre-commit` lo chiede per nome.
2. ⚠ *«Prima di chiudere una fase»* **non è un percorso**: è una decisione, e si chiede per nome
   (`--famiglia tutto`). ⛔ Far finta che un percorso possa indovinarla vorrebbe dire una regola che
   non scatta mai e di cui nessuno si accorge che non è scattata. ⭐ L'ingresso di un **desktop
   nuovo** invece sì: si vede da una `Contenitore.<nome>` che compare.

## 5.2 ⭐⭐ La politica del rosso — *rilievo di Qwen §3.7, accolto per intero*

⛔ **Il documento spiegava benissimo come trovare il rosso e non diceva che cosa succede dopo.** E il
primo rosso importante genererà una discussione, ⇒ **e la discussione costa più della riparazione.**

| il caso | la regola |
|---|---|
| **rosso in FUNZIONA** | ⛔ **blocca**: si ripara prima di andare avanti. Non si archivia come *«poi vediamo»* |
| **rosso in VA VELOCE** | va capito **prima di chiudere la fase**. Se confermato, blocca la chiusura; se è dell'ambiente, si scrive perché |
| ⛔ **rosso intermittente** | ⛔ **è un rosso.** Non si ripete la prova sperando nel verde: *«a volte succede»* spesso vuol dire *«succede sempre, aspetta solo il momento»* |
| **esito 3 ripetuto** | il singolo `3` è neutro; ⛔ **un `3` frequente è un guasto del banco**, non un esito |
| **falso allarme** | si può dichiarare **solo dopo averlo capito**, e **si scrive**. ⛔ Una prova che dà falsi allarmi ripetuti **si ripara o si butta** |
| **prova che non prende niente** | ⛔ **si toglie, e si scrive perché.** Non si lascia morire per disuso |

---

# §6 · ⛔ QUEL CHE LA RETE **NON** PRENDE — *e va scritto, o qualcuno se ne fiderà troppo*

*Rilievo di Qwen §3.2-E e Q1, accolto.*

> ⭐ **La rete è fatta contro i guasti di nascita, di visibilità, di funzionamento di base e di
> correttezza fra due utenti.** ⛔ **Non è** una rete di prestazioni, non è una rete di compatibilità
> fra browser, e non è una prova di lunga durata.

| classe | perché resta fuori |
|---|---|
| **regressioni visive sottili** — colori un po' diversi, testo un po' storto, difetti grafici non degeneri | ⛔ per costruzione: i controlli sono **poveri** apposta, o marciscono (§4.3) |
| **perdite lente di memoria** — aprire e chiudere cento sessioni | vuole una prova di lunga durata, che è un altro mestiere |
| **corse fra eventi** che dipendono dai tempi | la rete gira in condizioni tranquille |
| **rete degradata** — perdita, ritardo, disordine | ⭐ **è tutto il tema della fase 9**, che ha i suoi banchi. Qui si duplicherebbe |
| **browser diversi** | la pagina gira su tre motori; la rete ne usa **uno** |
| **qualità fine di audio e video** | è giudizio dell'utente (I8), non di un banco |
| **aggiornamenti dei desktop** | ⚠ **coperto solo a metà**: C11 vede che la ricetta è cambiata, ⛔ non che il desktop nuovo si comporta peggio |
| **degrado termico** | fuori bersaglio |
| ⛔⛔ **le regressioni di PRESTAZIONE** | ⭐ dichiarato il 27 ago 2026: **nessun banco confronta ieri con oggi**. Un fotogramma che diventa più lento senza che nulla smetta di funzionare **passa**. ⇒ §3.4 |
| ⛔⛔ **il prodotto sugli altri tre desktop** | `[M]` 27 ago: il prodotto **sa avviare solo GNOME** (`src/sessione.c:778`) ⇒ su KDE, XFCE e LXQt la rete prova **l'ambiente, il suono, i residui, il registro e l'allineamento**, ⛔ **non il prodotto**. È materia della fase 12 |
| ⛔ **le scelte mai fatte** | non si è **rotto** niente: quella roba sta in `MASTERPLAN.md` (D6), e la rete non la prenderà mai — **ed è giusto così** |

> ### ⛔⛔⛔ E OGGI C'È UNA COSA IN PIÙ CHE LA RETE NON PRENDE, e non è per scelta — *26 agosto 2026*
>
> **La rete non riesce a guardare NESSUN pixel attraverso il prodotto**, e non perché sia scritta
> male: `[M]` **dieci sessioni GNOME nuove su dieci nascono senza monitor** (§7-bis.13), cioè non
> c'è niente da guardare. ⇒ ⛔ Restano fuori **C2, C3, C4, C6 e la metà B di C8** — cioè la parte
> della rete che dovrebbe dire *«si vede»* invece di *«è nato»*.
>
> ⭐ **Quel che regge lo stesso**: C1 (che quel difetto lo PRENDE, ed è il suo mestiere) e **C8a**,
> che guarda il pixel **senza passare dal prodotto** — ed è la ragione per cui è stata spezzata in
> due invece di essere rimandata.
>
> ⚠ **E questo NON è un buco della rete: è un difetto del prodotto**, aperto dalla fase 10. ⛔ La
> differenza conta: un buco si tura scrivendo un'altra maglia, questo si tura **curando il
> prodotto**, e finché è lì la fase 12 partirebbe senza modo di vedere se GNOME regge ancora.

---

# §7 · Il piano di lavoro

⛔ **Una scatola sola per prima, non quattro.** ⭐ E prima ancora, il passo 0.

| # | | perché in quest'ordine |
|---|---|---|
| **0** | ⛔⛔ **il PASSO 0** (§3.5): mezza giornata, e la `[?]` su `logind` diventa `[M]` | ⛔ **precondizione.** Scoprire dopo quattro scatole che l'ambiente non è quello vero è il modo peggiore di spendere questa fase |
| **1** | la **lista** (§4) e le tre decisioni aperte | ⛔ la forma della scatola dipende da che cosa ci si deve provare dentro |
| **2** | **una** scatola, per GNOME: ricetta con le versioni, binario unico, impronta, marca, testimone, registro leggibile | |
| **3** | ⭐⭐ **la si punta contro il codice del 25 agosto**, e si guarda se **C1 diventa rossa da sola** | ⛔ **è il punto di non ritorno.** Se prende, la forma è giusta. **Se non prende, non si costruiscono le altre: si capisce perché** |
| **3-bis** | ⭐ **si prova anche il rosso SBAGLIATO**: immagine coi colori spostati apposta ⇒ **deve restare verde** | ⛔ *rilievo di Gemini, accolto*: se la marca cade per uno scarto minimo di colore, **la rete si butta fra due settimane** |
| **4** | il **collaudo B** (C8), nella forma che l'utente avrà scelto (§4.4) | l'altra metà del collaudo |
| **5** | le altre tre scatole, a stampo | ⛔ solo ora |
| **6** | le prove della rete (C11-C14) | |
| **7** | il **gancio** (§5.1) | ⚠ per ultimo, e **solo dopo che la rete ha preso almeno un guasto vero**: agganciare una rete che non prende niente è il modo più veloce di trasformarla in cerimonia |

---

# §7-bis · ⭐⭐⭐⭐⭐ CHE COSA È STATO FATTO — *la notte del 25-26 agosto 2026*

> ## ⭐ IN UNA RIGA, PER CHI LEGGE SOLO QUESTA
>
> | il piano di §7 | dove siamo |
> |---|---|
> | **0** il passo 0 | ✅ `[M]` **18/18**, e non su una scatola: **su tutte e quattro** |
> | **1** la lista e le decisioni aperte | ✅ la lista c'è; ⭐ l'ultima domanda aperta (C8) l'ha chiusa l'utente |
> | **2** una scatola | ✅ ⭐ **quattro** — GNOME, Plasma, XFCE, LXQt |
> | **3** ⭐⭐ il **collaudo A** | ✅ **rossa da sola**, `[M]` 10 sessioni cieche su 10 |
> | **3-bis** il rosso sbagliato | ✅ nella certificazione di C8: colore spostato ⇒ **resta verde** |
> | **4** ⭐⭐ il **collaudo B** | ✅ **preso**: col guasto innestato il **secondo** inquilino non apre il browser, il primo sì |
> | **5** le altre tre scatole | ✅ fatte, e ⭐ **senza riscrivere una riga della lista** |
> | **6** le prove della rete | ✅ ⭐ **tutte e quattro**: C11 verde · C12 e C13 girano · C14 verde e misurata |
> | **7** il gancio | ✅ ⭐ **c'è, e ha già girato davvero**: `[M]` **153 s** su un tetto di 180 |
>
> ⛔ **E la cosa che pesa di più non è nessuna di queste**: `[M]` **dieci sessioni GNOME nuove su
> dieci nascono senza monitor** ⇒ metà della rete — tutte le maglie che vogliono guardare un pixel
> **attraverso il prodotto** — non ha niente da guardare. ⚠ Non è un buco della rete: è il difetto
> **aperto** della fase 10 §7.4. ⇒ §7-bis.13, e la domanda all'utente in §11.

> ## ⭐⭐⭐⭐⭐ IL COLLAUDO A È PASSATO — **la rete è diventata rossa da sola**
>
> `[M]` **25 agosto 2026, 22:42 UTC**, il primo giro in assoluto. Puntata contro il codice del 25
> agosto, dentro una scatola, su **sei utenti nuovi**, la maglia C1 ha detto:
>
> ```
>   giro  1/6  NO   CIECA          giro  4/6  ?    NON-LO-SO
>   giro  2/6  ?    NON-LO-SO      giro  5/6  NO   CIECA
>   giro  3/6  NO   CIECA          giro  6/6  ?    NON-LO-SO
>
>   nate con un monitor: 0   ⛔ CIECHE: 3   non giudicate: 3
>   ⛔⛔ ROSSO — 3 sessioni su 6 sono nate CIECHE.
> ```
>
> ⚠ *Questo è il **primo** giro. Il 26 agosto, con dieci utenti e il banco curato, il numero è
> diventato **10 cieche su 10 e zero non giudicate** — ⇒ §7-bis.13.*
>
> ⛔ **Nessuno le aveva detto dove guardare.** Apre una sessione nuova, legge quel che il prodotto
> dice di sé, e giudica. ⇒ **La riga che l'ha fatta scattare**, presa dal registro del server:
>
> ```
> 22:42:15.826 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva: e' la sessione
>                                «viva, completa e NERA» di STUDI.md §gnome §3.1
> 22:39:18.145 figlio  ⛔ il palco di «c1u1»: monitor «» (0 prima, 2 dopo), 0x0 stride 0 a 0 bit
> ```
>
> ⭐ E il **terzo stato** di `fasi/10…` §7.4 — *«una volta per utente ne nascono due, senza nome»* —
> ⭐ **si è riprodotto identico**: `monitor «» (0 prima, **2** dopo)`.
>
> ⇒ ⛔ **Il guasto del 25 agosto vive dentro la scatola.** Che è la seconda notizia, e non è minore:
> vuol dire che la scatola **non lo nasconde**, cioè che è il posto giusto dove tendere la rete.

## 7-bis.1 ⭐ IL PASSO 0 È PASSATO — `[M]` **18 verdi, 0 rossi, 0 «non lo so»**

*La `[?]` più pesante del documento è diventata un `[M]`.*

| # | | esito |
|---|---|---|
| 0 | il primo processo è `systemd`, il sistema parte | ⭐ **sì** (con una sola unità fallita, `polkit`, dichiarata) |
| 1 | `logind` conosce l'utente, sessione aperta | ⭐ **sì** |
| 2 | il **linger** si accende e il gestore d'utente vive senza login | ⭐ **sì** |
| 3 | un'unità d'utente si avvia da dentro la sessione | ⭐ **sì** |
| 4 | chiusa la sessione, ⛔ **i figli muoiono davvero** | ⭐ **sì** |
| 5 | la cartella privata c'è, è sua, ed è **di questa scatola** (tmpfs) | ⭐ **sì** |
| 6 | il canale di messaggi della sessione c'è e risponde | ⭐ **sì** |
| 7 | il compositore vive, **annuncia un'uscita**, e un cliente vero disegna | ⭐ **sì** |
| 8 | ⭐⭐ **la scheda grafica e il codificatore in hardware** | ⭐ **sì**: `iHD 25.2.3`, **3 profili H.264 di codifica** |

> ### ⛔⛔ E IL PREZZO, MISURATO PERMESSO PER PERMESSO — *non uno per abitudine*
>
> ⛔ **Non è stato usato `--privileged`.** Un permesso generico avrebbe fatto passare tutto e non
> avrebbe insegnato niente. ⇒ Quel che il prodotto chiede **davvero**:
>
> | permesso | ⛔ che cosa si rompe senza |
> |---|---|
> | `--device /dev/dri` | ⭐ **la scheda vera.** È la ragione di D1 |
> | ⛔ **`--cap-add=AUDIT_CONTROL`** | `[M]` `pam_loginuid.so`, che in Debian è **`required`**, fallisce con *«Cannot make/remove an entry for the specified session»* ⇒ ⛔ **il gestore d'utente non parte affatto**: niente sessione, niente canale, niente desktop |
> | `--cap-add=AUDIT_WRITE` | accompagna il precedente nella stessa catena |
> | ⚠ `--network=host` | ⛔ **non è una scelta**: `netavark` su questa macchina non applica le regole (*«nft did not return successfully»*). ⇒ **Prezzo dichiarato**: quattro scatole insieme condividono le porte dell'ospite, quindi ognuna ha la sua (8511-8514) — e resta da rivedere a **C14** |
>
> ⭐ **E la strada scartata**: togliere `pam_loginuid` dalla catena PAM avrebbe fatto passare tutto
> senza permessi in più — ⛔ **e avrebbe provato una catena PAM diversa da quella consegnata**, cioè
> esattamente il simulacro che §3.5 esiste per impedire.

## 7-bis.2 ⛔⛔ IL GUASTO CHE NESSUNO DEI DUE REVISORI AVEVA PREVISTO — **il gruppo della scheda**

`[M]` Al primo giro il nodo `/dev/dri/renderD128` è entrato nella scatola col **numero** di gruppo
dell'ospite (991), ⛔ **ma dentro Debian quel numero appartiene a un altro gruppo** (`polkitd`).
⇒ L'inquilino è rimasto fuori, e il compositore ha ripiegato:

```
libEGL warning: failed to open /dev/dri/renderD128: Permission denied
libmutter-Message: Created surfaceless renderer without GPU
```

> ⛔⛔ **Una scatola che misura la codifica in SOFTWARE credendo di misurare l'hardware** — e
> **nessun rosso da nessuna parte**: solo numeri peggiori, che qualcuno avrebbe attribuito al
> desktop. ⭐ È la forma di *«silenzio invece di rosso»* applicata a un ambiente invece che a un
> banco.

⭐ **La cura, e non è inchiodare 991**: un'unità dentro la scatola **legge il numero dal nodo**
all'avvio e vi allinea il gruppo `render`, **dichiarandolo**. ⇒ Inchiodare il numero avrebbe fatto
una scatola che funziona su questa macchina e **tace** su un'altra.

## 7-bis.3 ⛔ E DUE VOLTE IL DIFETTO ERA NEL BANCO, non nella scatola

*`REVIEWER.md` §1: il banco è il primo imputato. Confermato due volte in una notte.*

| | ⛔ che cosa faceva | la cura |
|---|---|---|
| **il punto 4 buttava giù il campo agli altri** | chiude la sessione per vedere se i figli muoiono ⇒ si porta via `/run/user/…` ⇒ **i punti 5, 6 e 7 davano TRE ROSSI FALSI** | chi prova la chiusura ha il dovere di **riaprire e verificare** prima di lasciar giudicare gli altri |
| **il punto 1 giudicava prima di aver chiesto** | leggeva mentre il gestore d'utente era ancora `activating` ⇒ *«la scatola non regge»* quando la verità era *«non avevo ancora chiesto niente»* | si **prepara** come fa il prodotto, si aspetta l'evento, **poi** si giudica |

> ⭐⭐ **E la lezione nuova è il rovescio di quella nota.** `LEZIONI.md` §1.29 dice *«silenzio invece
> di rosso»*. ⛔ Qui è stato **rosso invece di niente** — e costa uguale: *una rete che dà rossi a
> vuoto viene spenta da chi lavora*, e allora non c'è più nessuna rete.

## 7-bis.4 ⛔⛔ IL BINARIO ERA GIUSTO E LE LIBRERIE NO — **e il sintomo era dalla parte sbagliata**

`[M]` Il prodotto è stato messo nella scatola con le librerie prese da `/lib` dell'ospite:
`libngtcp2.so.16` **versione 16.2.9**. ⛔ Ma il server vero gira con quella costruita in
`src/b2/ngtcp2/build/lib`, **16.11.0**. ⇒ **Stesso nome, stesso `so.16`, cosa diversa.**

| | |
|---|---|
| il server | è **partito**, ha detto tutte le sue righe d'avvio, ha generato i certificati, si è messo in ascolto |
| ⛔ al **primo cliente** | è morto con `ngtcp2_settingslen_version: Unreachable` |
| ⛔⛔ e il cliente | ha visto soltanto **«Idle timeout»** |

> ⭐⭐ **È il guasto che l'utente aveva nominato per primo** — *«se sul container GNOME abbiamo
> remotix v1 e sul container KDE remotix v1.2 andiamo a sbattere»* (D5) — ⛔ **arrivato però da una
> porta che nessuno guardava**: non due versioni del prodotto, **due versioni di una libreria con lo
> stesso nome.** ⇒ R1 va letta così: *un solo binario **e le sue librerie**, presi dove li prende il
> server vero.*

⚠ **E la stessa famiglia, due volte ancora**: `libei1` e `python3-aioquic` funzionavano perché
qualcun altro se li tirava dietro. ⇒ Adesso le librerie che il prodotto chiede sono **dichiarate
nella ricetta**, riga per riga, invece di essere ereditate per caso.

## 7-bis.5 ⭐ IL PRODOTTO GIRA DENTRO LA SCATOLA — e la prova è un cliente vero

`[M]` 26 agosto 2026: il cliente di prova si è attaccato al server **dentro la scatola**, ed è stato
**AMMESSO in 1004 ms**, con `SESSIONE: stato=1 tela=1920x1080`, restando attaccato 30 s senza che
cadesse niente. ⇒ ⭐ Il guardiano di `logind` si è collegato al bus di sistema **dentro il
contenitore**, che era la `[?]` di Q2.

⚠ **E una sessione, quella volta, è nata col monitor**: `monitor 1/1: connettore «Meta-0» …
1920x1080@60`. ⛔ **Non è una smentita del rosso di sopra: è l'intermittenza**, la stessa che sul
ferro dava a `provanic3` **2 riusciti e 6 falliti**.

## 7-bis.6 ⛔ E DUE COSE CHE RESTANO APERTE, scritte invece che dimenticate

| | |
|---|---|
| ⛔ **la scatola non si spegne da sola** | `[M]` un `podman rm -f` normale è rimasto appeso **oltre quattro minuti** aspettando uno spegnimento ordinato che non arrivava, bloccando anche i comandi successivi. Per ora si ammazza (`-t 0`). ⚠ **Non tocca il passo 0** (la scatola è usa-e-getta) ⛔ **ma tocca C7** — *«si chiude tutto e non resta niente»* — e lì quella domanda diventa il bersaglio |
| ⚠ **tre giri su sei non hanno giudicato** | il palco impiega ~13 s a nascere e a volte non nasce affatto; l'attesa dichiarata è 45 s. ⇒ Restano **«non lo so»**, ⛔ **e non diventano verdi** |

## 7-bis.7 ⭐⭐⭐⭐ LA SECONDA SCATOLA — **e le stesse prove girano su PLASMA senza una riga cambiata**

`[M]` **26 agosto 2026, 04:05 UTC.** Costruita una seconda scatola con **KWin** al posto di Mutter,
e le **stesse identiche otto verifiche** hanno detto:

> ### ⭐ `regge: 18 · non regge: 0 · non ho potuto guardare: 0`

⛔ **Non è stata riscritta una riga della lista.** Ogni scatola porta allo stesso percorso un
**adattatore** — un file corto che risponde a tre domande: *come ti chiami · da che pacchetto vieni ·
come ti accendo*. ⇒ È la forma su cui **tutt'e due i revisori** avevano risposto la stessa cosa (Q3,
§3.7), e ⭐ **adesso è misurata invece che creduta**.

### ⛔⛔ E il secondo desktop ha chiesto subito una cosa che il primo non chiedeva — **due volte**

| | ⛔ che cosa è successo | ⭐ che cosa insegna |
|---|---|---|
| **il gruppo della scheda non esisteva** | nella scatola di GNOME `render` c'era già: lo portava un pacchetto che `gnome-shell` si tira dietro. ⛔ In quella di Plasma **non esiste**, e la ricetta è morta con `usermod: group 'render' does not exist` | il primo desktop non era «giusto»: era **generoso**, e nascondeva una dipendenza che nessuno aveva dichiarato |
| ⛔⛔ **KWin non partiva affatto** | `env: 'kwin_wayland': Operation not permitted`. ⇒ `/usr/bin/kwin_wayland` porta addosso `cap_sys_nice=ep`, e **un programma con un permesso scritto sul file non si avvia** se quel permesso non è nell'insieme della scatola | ⭐ un desktop nuovo può chiedere **permessi** che il primo non chiedeva — e il sintomo non somiglia per niente alla causa |

⭐ **La cura è per desktop e dichiarata**: `SYS_NICE` va **solo** alla scatola di Plasma. ⛔ Darlo a
tutte vorrebbe dire provare GNOME in un ambiente diverso da quello in cui gira davvero — cioè
allontanare la scatola dal prodotto per comodità nostra.

> ### ⭐⭐⭐ E QUESTA È LA TESI DELLA FASE, CAPITATA AL PRIMO TENTATIVO
>
> Due cose che il secondo desktop ha fatto emergere **in dieci minuti**, e che dentro la fase 12 —
> in mezzo al codice nuovo, con Plasma da far funzionare — sarebbero costate mezza giornata **e una
> diagnosi sbagliata**: sarebbero sembrate difetti del nostro codice KDE.
>
> ⇒ ⛔ **È esattamente la ragione per cui l'utente ha messo questa fase PRIMA dei desktop nuovi.**

⚠ **E quel che questa scatola NON fa, oggi**: il prodotto non sa ancora accendere KDE (è la fase 12),
quindi lì dentro girano **solo** le verifiche dell'ambiente. Le maglie della rete che vogliono il
prodotto — C1 e le altre — girano per ora **solo su GNOME**.

## 7-bis.9 ⭐⭐⭐⭐⭐ LA TERZA E LA QUARTA SCATOLA — **e le quattro sono in piedi**

`[M]` **26 agosto 2026, 03:5x UTC.** Costruite le scatole di **XFCE** e **LXQt**, e la stessa
identica lista di otto verifiche — ⛔ **non una riga cambiata, ancora** — ha detto:

> ### ⭐ XFCE `regge: 18 · non regge: 0 · non ho potuto guardare: 0`
> ### ⭐ LXQt `regge: 18 · non regge: 0 · non ho potuto guardare: 0`

⇒ ⭐⭐ **Quattro scatole, quattro desktop, un solo elenco di prove.** La cecità al desktop di §3.7
non è più una proposta: è `[M]` su quattro compositori, e il costo per aggiungerne uno è **un
adattatore da quaranta righe**.

### ⛔ E una cosa scomoda, detta prima che qualcuno la scopra contando male

**Le scatole sono quattro; i compositori sono TRE.** XFCE e LXQt non portano un compositore proprio
su Wayland: portano una **sessione** e si appoggiano a uno di famiglia `wlroots` — e la scelta, per
tutt'e due, è **labwc**. ⛔ Non è una comodità di questa fase: `DECISIONI.md` ha già misurato il
ridimensionamento sotto l'etichetta **«labwc (XFCE, LXQt)»** (`[M]` 5,1 ms, 0 fotogrammi persi su
25), e `PIANO.md` fase 13 lo dice in una riga — *«il terzo e il quarto desktop, che condividono
wlroots e quindi quasi tutto»*.

⇒ ⚠ **Che cosa mette alla prova davvero la quarta scatola**: una quarta **sessione**, una quarta
**ricetta**, dipendenze diverse, e un demone d'inattività che `DECISIONI.md` dà già per **diverso**
da quello di XFCE. ⛔ **Non** un quarto compositore. Chi legge i risultati conti così.

### ⭐ E il terzo desktop non ha chiesto niente di nuovo — *ed è un risultato, non un non-evento*

⛔ Il secondo desktop aveva chiesto **due** cose che il primo non chiedeva (§7-bis.7). Il terzo e il
quarto: **zero**. `labwc` non porta permessi scritti sul file, non pretende gruppi che non ci sono,
e nasce senza schermo con `WLR_BACKENDS=headless` — la terza parola diversa per la stessa cosa, dopo
`--headless` di Mutter e `--virtual` di KWin, ⭐ **e sta tutta nell'adattatore.**

⚠ E va letto per quel che è: **non** *«allora le scatole nuove sono gratis»*. È **un** desktop che
non ha chiesto niente dopo **uno** che aveva chiesto due cose — cioè la ragione per cui la domanda
si fa a ciascuno invece di generalizzare dal primo.

## 7-bis.10 ⭐⭐⭐⭐⭐ IL COLLAUDO B È PASSATO — *C8 prende il difetto, e lo prende dal SECONDO*

⛔ Era la domanda aperta della fase (§4.4), chiusa dall'utente il 26 agosto: **C8 sta in una scatola,
con due inquilini.** ⇒ È scritta, è certificata, ⭐ **e ha preso il guasto.**

> ### `[M]` 26 agosto 2026 — le due righe che valgono la fase
>
> **con la cura della provvista:**
> `c8u1 ⭐ la pagina copre il 98,7 % · c8u2 ⭐ la pagina copre il 98,7 %`
>
> **senza la cura** (il guasto innestato, cioè il codice del 25 agosto):
> `c8u1 ⭐ la pagina copre il 98,7 %` · ⛔ `c8u2 NO — profilo: è di «c8u1» · sa scrivere in ~/.cache/mozilla: NO`

⭐⭐ **E l'asimmetria è quella giusta**: il **primo** apre il browser, il **secondo** no. ⛔ Un rosso su
tutt'e due non sarebbe stato il difetto di §4.6-undecies — sarebbe stato il banco — e ⭐ **adesso è
C8 stessa a dirlo**, invece di lasciarlo dedurre a chi legge (§7-bis.12).

### ⛔⛔ E C8 SI È DOVUTA SPEZZARE IN DUE — *la ragione va letta prima dei numeri*

| | che cosa guarda | oggi |
|---|---|---|
| ⭐ **A · il browser rende la pagina** | Firefox si fotografa da sé, da utente, sulla macchina com'è configurata. ⛔ Il giudizio resta **nel pixel** | ✅ **si misura**, ed è quel che ha preso il guasto |
| **B · e la pagina si vede DAL CLIENTE** | la stessa pagina, guardata **attraverso il prodotto** | ⚠ **oggi non si misura** |

⛔⛔ **Perché B non si misura**: `[M]` 26 agosto 2026, dentro la scatola **nessuna sessione GNOME nuova
nasce con un monitor** — è il difetto **APERTO** della fase 10 §7.4, *«la sessione che nasce cieca»*,
che sta **a monte** di C8. ⇒ ⭐ **Un desktop nero non testimonia sul browser**: chiamare quello «rosso
di C8» vorrebbe dire dare la colpa al browser di una cosa successa **prima che il browser esistesse**.
⚠ Quindi B dice *«non ho potuto guardare»* e **nomina il perché**, e non diventa mai un verde.

⭐ **E la spaccatura ha un guadagno che non era previsto**: la prova A **non passa dal prodotto**, e
quindi gira in **qualunque** scatola — anche in una dove il prodotto non c'è nemmeno. ⛔ Il collaudo
qui sopra è girato dentro la scatola di **PLASMA**.

### ⭐ Le scelte del banco che contano

| | |
|---|---|
| ⭐ **il terreno se lo prepara lei** | mette `/etc/skel/.cache -> /tmp`, cioè **riproduce la configurazione della macchina vera** — che è una **scelta del proprietario**, non un guasto. ⛔ Provare su uno scheletro pulito risponderebbe a una domanda più facile di quella vera |
| ⭐ **gli inquilini nascono come li fa il prodotto** | `useradd -m`, che copia lo scheletro. ⛔ Una via più pulita qui proverebbe un prodotto diverso da quello consegnato |
| ⭐⭐ **il bersaglio nei pixel è un COLORE** | la pagina è `#FF00FF` a schermo intero, e si misura **quanta parte dell'immagine è diventata di quel colore** — tolleranza **±48 per canale**, almeno il **25 %**. ⛔ Nessun desktop mette quel colore da solo: il metro non ha bisogno di sapere che aspetto abbia GNOME |
| ⛔ **il motivo accanto al sintomo** | «non ha disegnato» da solo nasconde tre guasti: il browser morto, il profilo mai nato, la pagina non a schermo. Li distingue e li stampa — ⭐ ed è così che si legge *«profilo: è di «c8u1»»* |
| ⛔ **e non guarda il collegamento** | guardare la causa che crediamo di conoscere invece dell'effetto che ci interessa vorrebbe dire una prova che tace il giorno che la cura cambia |

### ⭐ La certificazione del giudice — `[M]` **8 casi su 8**

| il caso | perché c'è |
|---|---|
| pagina intera · desktop senza browser · schermo nero | il minimo: vede quando c'è, non vede quando non c'è |
| ⭐ **colore spostato di (−30, +30, −30) ⇒ deve restare VERDE** | i compositori applicano profili di colore e la catena passa per un H.264 **4:2:0**, che sottocampiona proprio il croma. ⛔ Una prova che pretende il colore esatto è già morta (§4.3, rilievo di Gemini) |
| colore spostato **troppo** ⇒ deve restare ROSSO | o la tolleranza non separa più niente |
| una macchia piccola non è una pagina | una finestra che si apre e non disegna |
| ⛔ **il file che non c'è e il file vuoto ⇒ «non lo so», non zero** | *«non ho guardato»* e *«ho guardato e non c'era»* sono due cose diverse |

⚠ **E la certificazione si dichiara per quel che copre**: il **lettore dei pixel**. ⛔ Non copre che il
browser sia davvero partito — quello lo dice `--senza-cura` sul vero, ed è il collaudo qui sopra.

## 7-bis.11 ⛔⛔⛔ **QUATTRO VOLTE IL DIFETTO ERA NEL BANCO** — *e le quattro lezioni*

⚠ **Va scritto, e va scritto per intero**: prima di prendere il guasto vero, il banco ha sbagliato
**quattro volte** — tre rossi falsi e ⛔ **un verde falso**. ⭐ Ognuno è una forma d'errore che questa
fase esiste per non ripetere, e tutti e quattro sono finiti in `LEZIONI.md`.

| | ⛔ che cosa succedeva | ⭐ la lezione |
|---|---|---|
| **il predicato che non poteva fallire** | *«prova a scrivere in `~/.cache`»* — ⛔ ma col collegamento `~/.cache` **è `/tmp`**, scrivibile da chiunque (`1777`). ⇒ Diceva **sì** anche all'inquilino che il browser non apriva | `LEZIONI.md` §1.44 — **applicare E1 non basta: bisogna applicarlo NEL POSTO CHE MORDE** (`~/.cache/mozilla`), o il predicato ⛔ ha lo stesso aspetto di uno che passa |
| **il tetto prestato** | il primo avvio di Firefox in una scatola fredda passa i 25 s, e il banco gli dava il tetto pensato per un'altra attesa ⇒ ⛔ **rosso a tutt'e due, con la cura e senza** | `LEZIONI.md` §1.45 — ⛔ e il danno vero non è il rosso falso: è che **il collaudo smette di valere**, perché non distingue più il guasto dal banco |
| **il banco che si dava rosso da solo** | la cartella di lavoro è di `root` a modo `0755`, e Firefox gira **da utente** ⇒ non poteva scriverci l'immagine, e il banco leggeva *«il browser non ha disegnato»* | ⭐ la cura: **scatta in casa sua**, e a portare fuori l'immagine ci pensa `root` dopo |
| ⛔⛔ **e un QUARTO, che è peggio di un rosso** | un comando annidato tre volte (`ssh` → `systemd-run` → `podman exec sh -c`) ha perso le virgolette, **non ha eseguito niente** e ha restituito **`0`** | `LEZIONI.md` §1.46 — ⛔ **un verde senza nessuna misura sotto**, identico a un giro riuscito. ⇒ Niente gusci in mezzo, e **un banco che non stampa niente non è «riuscito»** |

> ### ⭐⭐ E la cosa che le tiene insieme
>
> I primi tre davano **rosso**, ed erano **del banco**. ⛔ In una fase che costruisce una rete di
> sicurezza questo è il pericolo numero uno di §1.3: *«una rete che dà rosso a vuoto viene spenta da
> chi lavora»*. ⇒ ⭐ **Il guasto innestato li ha presi tutti e tre**, e in dieci minuti: senza
> `--senza-cura` sarebbero passati per «il difetto c'è, guarda che rosso».
>
> ⛔⛔ **Il quarto no**, e per questo sta a parte: un **verde** non lo prende nessun guasto innestato,
> perché il guasto innestato serve a controllare che si sappia dare rosso. ⇒ ⭐ Contro quello serve
> l'altra regola: **pretendere di vedere le righe**. Un banco muto non è un banco contento.

## 7-bis.12 ⛔ E UNA GUARDIA NUOVA, NATA DA QUEI ROSSI: **«ha fallito anche il PRIMO»**

Il guasto di §4.6-undecies morde **dal secondo inquilino in poi**. ⇒ ⭐ Se col guasto innestato dà
rosso **anche il primo**, quel che si sta misurando **non è quel guasto**.

⛔ C8 adesso lo dice da sé, e in quel caso **esce 1 invece di 0** — cioè *«il collaudo non vale»*, e
non *«il collaudo è riuscito»*. ⚠ È il rovescio esatto della trappola: una maglia che festeggia un
rosso senza guardare **di chi** è.

## 7-bis.13 ⛔⛔⛔ **DIECI SESSIONI NUOVE, ZERO CON UN MONITOR** — *e il banco che adesso giudica tutte e dieci*

`[M]` 26 agosto 2026, C1 dentro la scatola di GNOME, **dieci** inquilini nuovi, attesa del palco
alzata a **90 s**. Due giri, e il secondo dopo una cura al banco:

| | esito |
|---|---|
| primo giro | `nate con un monitor: 0 · ⛔ CIECHE: 5 · **non giudicate: 5**` |
| ⭐ secondo giro, col banco curato | `nate con un monitor: 0 · ⛔ **CIECHE: 10** · non giudicate: **0**` |

⭐ **Il rosso è quello atteso**, ed è il collaudo A che regge: la maglia punta il codice del 25 agosto
e diventa rossa sul difetto della fase 10 §7.4. ⛔ **E il numero è peggiore di quel che il documento
di fase lasciava sperare**: non «intermittente», ma **dieci su dieci**. ⚠ È coerente con la misura sul
ferro (`provanic4/5/6`: **mai**, su 98 · 55 · 50 tentativi) — ⇒ per un utente **nuovo** il guasto non
è raro: **è la regola**.

> ⛔⛔ **E questo è il fatto che blocca metà di C8** (§7-bis.10, prova B), e non solo: blocca **tutte**
> le maglie che vogliono guardare un pixel attraverso il prodotto — C2, C3, C4, C6.
> ⇒ ⚠ **E il fatto, senza consiglio**: cominciare la fase 12 con questo aperto vorrebbe dire far
> funzionare KDE **senza avere modo di vedere se GNOME continua a funzionare**. ⭐ La scelta è
> dell'utente, e sta in §11.

### ⭐⭐ La cura del banco: **i cinque «non lo so» si alternavano, ed era lo sgombero**

⛔ Il primo giro aveva dato `? NO ? NO ? NO ? NO ? NO` — **uno sì e uno no, dieci giri di fila**. ⚠ Una
alternanza perfetta non è un caso: è **uno stato che sopravvive al giro**.

⇒ ⭐ **Era lo sgombero**: `loginctl terminate-user` più `pkill` tornano **subito**, e il giro dopo
partiva mentre il precedente stava ancora morendo — il compositore nuovo non riusciva nemmeno a
nascere, e il registro non diceva né «monitor» né «cieca». Il giro ancora dopo trovava il campo
libero e giudicava.

⛔ **La cura è la stessa regola di sempre: si aspetta l'EVENTO, non l'orologio.** Adesso C1 aspetta
che l'inquilino del giro precedente non abbia **né sessione né processi**, e se entro il tempo
dichiarato non se n'è andato **lo dice**, invece di partire fingendo di non saperlo.

> ### ⭐ E il risultato è la differenza fra un banco e un banco che serve
>
> `non giudicate: 5` ⇒ `non giudicate: **0**`. ⚠ Nessuno dei cinque era un rosso — la maglia aveva la
> decenza di non giudicare (§4.5) — ⛔ **ma una prova che giudica la metà delle volte vale la metà.**

### ⚠ E il TEMPO, misurato invece che stimato — *criterio §9.9*

`[M]` I dieci giri sono durati **12 minuti e 20 secondi**: ⭐ **74 secondi a giro**.

⇒ ⛔ **Il tetto dei 3 minuti per la famiglia veloce ci sta dentro solo con DUE giri.** ⚠ E questo è un
numero preso **con il difetto aperto**: ogni giro spende l'attesa intera del palco (90 s di tetto) e
poi lo sgombero. ⭐ Con le sessioni sane il giro sarà molto più corto — ⛔ ma finché non lo è, il
gancio non può far girare dieci giri di C1 a ogni modifica: **si tagliano prove, non si alza il
tetto** (§5.1).

## 7-bis.14 ⭐⭐⭐ **C11 È VIVA E DICE VERDE** — *la maglia che guarda la rete, non il prodotto*

⭐ È il guasto che l'utente ha nominato **per primo**, con parole sue: *«se sul container gnome
abbiamo remotix v1 e sul container kde remotix v1.2 andiamo a sbattere»* (D5). ⇒ Adesso c'è una
maglia che lo va a cercare, e `[M]` **26 agosto 2026**:

> ### ⭐ `le 4 scatole accese sono allineate su tutte le 13 voci dichiarate`

| ⭐ dev'essere uguale | ⛔ dev'essere diverso |
|---|---|
| la base (`13.6`) · mesa · libva · pipewire · libavcodec · ffmpeg · **firefox-esr** · libc · libssl · libei · libpci · ⭐ **l'md5 del binario del prodotto** | **il desktop** — `gnome-shell 48.7` · `kwin-wayland 6.3.6` · `labwc 0.8.3` · `labwc 0.8.3` |

⛔⛔ **E si guarda quel che c'è DENTRO le scatole accese, non quel che c'è scritto nelle ricette.** Le
ricette sono diverse **apposta**, e un confronto che deve prima «togliere le parti diverse» diventa
un confronto su cui si discute. ⇒ È la regola E1 applicata all'ambiente: *scritto non è in vigore*.

⚠ **Il primo giro è stato ROSSO**, e per la ragione giusta: il prodotto stava **solo** nella scatola
di GNOME. ⭐ Messo lo stesso identico binario in tutte e quattro, è diventato verde — ⇒ **la maglia
ha fatto esattamente il suo mestiere al primo colpo.**

### ⛔⛔ E ha avuto anche lei il suo difetto, che è il più insidioso di tutti

`[M]` Tre voci su tredici chiedevano pacchetti col nome sbagliato (`libssl3` invece di `libssl3t64`).
⇒ Tutte e quattro le scatole rispondevano **`?`** — e ⭐⭐ **`?` uguale a `?` è uguale**: quelle tre
voci **passavano il confronto**, per sempre, senza guardare niente.

> ⇒ ⭐ C11 adesso le **conta e le stampa**: *«N voci a cui nessuna scatola sa rispondere — e una voce
> muta passa il confronto senza aver guardato niente»*. `LEZIONI.md` §1.47.
>
> ⚠ È la stessa forma d'errore di §1.44 vista da un'altra parte: là il predicato diceva sempre sì,
> qui il confronto diceva sempre uguale. ⛔ **Un controllo che non ha mai dato rosso in vita sua va
> guardato in faccia, non festeggiato.**

## 7-bis.15 ⭐⭐⭐⭐ **C14 — LE QUATTRO SCATOLE NON SI DISTURBANO**, e adesso è misurato

§3.4 lo **affermava**; ⭐ adesso c'è la misura sotto. `[M]` **26 agosto 2026**, la stessa prova
(C8a) fatta girare **una scatola per volta** e poi **tutte e quattro insieme**:

| | sole | insieme |
|---|---|---|
| col guasto innestato | `1 sì · 1 no` × 4 | `1 sì · 1 no` × 4 |
| con la cura | `2 sì · 0 no` × 4 | `2 sì · 0 no` × 4 |

⇒ ⭐ **Stesso identico esito, quattro scatole su quattro, in tutt'e due i modi.**

### ⭐ E si chiude la riga che `11-accendi.sh` portava aperta

*«`--network=host` … quattro scatole accese insieme condividono le porte dell'ospite … **da rivedere
quando si fa C14**»*. ⇒ ⭐ **Rivista, e regge**: ciascuna ascolta la sua porta, ciascuna riconosce
come **propria** solo la sua e come **di un altro** le altre tre. La separazione per porta **è una
separazione vera**, e adesso ha una misura sotto invece di una speranza.

### ⚠ Il tempo — che è informazione, non verdetto

`[M]` **6,6 s da sola → 7,0 s in parallelo**, cioè **×1,06**. E il totale scende da 26,2 s a 7,0 s:
⭐ **il parallelo fa risparmiare ×3,76**.

⛔ **E un tempo misurato è stato BUTTATO, e il banco lo dichiara da sé**: col guasto innestato i
quattro tempi erano `125,9 · 126,0 · 126,0 · 126,1` s. ⚠ Quattro numeri uguali a un decimo non sono
un caso: col guasto il secondo inquilino non apre il browser e C8 lo **aspetta** fino al suo tetto.
⇒ Quel tempo è quasi tutto **attesa fissa nostra**, non lavoro — e chiamarlo «contesa» vorrebbe dire
misurare il proprio tetto e crederlo un difetto del prodotto.

### ⛔⛔ E che cosa NON misura, dichiarato

**Non misura la contesa vera sulla scheda grafica.** La prova A di C8 accende un browser che disegna
**in software**: la scheda non la tocca. La contesa vera vorrebbe quattro sessioni vive, e le
sessioni oggi nascono cieche (§7-bis.13). ⇒ Quel che è misurato è **lo strato di sotto**: le quattro
scatole riescono ad **aprire il codificatore nello stesso istante** (3 profili H.264 ciascuna, sole e
insieme). ⭐ Se già questo non reggesse, la contesa vera non avrebbe bisogno di essere provata.

### ⭐ E la certificazione ha bocciato il banco stesso

`[M]` **15 casi su 15**, ma solo dopo una correzione: il primo giudice buttava via il giudizio quando
**una sola** scatola aveva saputo rispondere. ⛔ Sbagliato — *una scatola che gira e non riesce a
riferire sta comunque occupando la macchina*, quindi il carico c'è e il giudizio delle altre vale.

⭐ **E la prova che sa dare rosso su dati veri, non solo sui casi finti**: `--smentisci` fa girare il
parallelo chiedendo di proposito l'**altro** modo di C8, così le impronte *devono* essere diverse ⇒
**4 scatole su 4 rosse.**

## 7-bis.16 ⭐⭐⭐ **IL GANCIO, C12 E C13** — *e il primo giro vero*

⛔ Il piano diceva di fare il gancio **per ultimo, e solo dopo che la rete avesse preso almeno un
guasto vero**: *«agganciare una rete che non prende niente è il modo più veloce di trasformarla in
cerimonia»*. ⇒ La condizione è soddisfatta — la rete ne ha presi due.

| | |
|---|---|
| `11-gancio.sh` | decide **per percorso** · fa girare · **lascia traccia** · si installa come hook di git |
| `11-c12-il-gancio-e-vivo.py` | esiste, è installato, è girato **davvero** e di recente. ⛔ Prende **il gancio spento in silenzio** |
| `11-c13-la-certificazione-e-recente.py` | negli ultimi giri un guasto è stato innestato **ed è stato visto** |

⭐ **Certificazioni: 11 su 11 ciascuna.** E il caso che tiene in piedi C13 merita di essere scritto:

> ⛔ **Un rosso venuto da un'altra maglia non certifica niente.** Se in un giro la rete è diventata
> rossa per conto suo (C1 sulla sessione cieca) **e** il guasto innestato **non** è stato visto, una
> C13 ingenua direbbe «certificata»: il giro porta scritto *ha dato rosso* e *guasto innestato*.
> ⇒ ⭐ Questa dà **rosso**, e fa **il nome della maglia** che ha mancato il guasto.

### ⛔⛔ Le prove TAGLIATE per stare nei 3 minuti — *e il taglio è dichiarato, non subìto*

`[M]` Un giro di C1 costa 74 s ⇒ nei 180 s ci stanno **due giri**. Nella famiglia veloce restano
**C11 + C1×2**. Fuori:

| tagliato | ⛔ che cosa costa |
|---|---|
| ⛔⛔ **C8, tutt'e due le prove** | **il taglio più caro**: la maglia più importante **non viene guardata a ogni modifica**. Resta nel giro completo |
| **C1 dal terzo giro in poi** | oggi non morde (10 su 10 nascono cieche, e due giri bastano) ⚠ **ma il giorno in cui il difetto sarà curato e tornerà raro, due giri non basteranno** |
| **il passo 0** | guarda l'ambiente, che non cambia quando cambia `src/`; e una scatola ricostruita di nascosto la prende **C11**, che nella famiglia veloce c'è |

⭐ E il gancio **salta** la maglia che non ci sta invece di troncarla a metà, e **scrive nel registro
che cosa ha saltato e perché**: ⛔ troncare darebbe un rosso che non è del prodotto (`LEZIONI.md`
§1.45).

### ⚠ E il gancio si aggancia PRIMA DI MANDARE, non a ogni salvataggio

Tre minuti a ogni commit sono esattamente la cosa che §5.1 dice che fa **spegnere** un gancio. ⇒ Il
predefinito è `pre-push`; chi vuole `pre-commit` lo chiede per nome.

⚠ E una cosa che il percorso **non sa dire**, dichiarata invece di essere nascosta: *«prima di
chiudere una fase»* non è un file che cambia, è una **decisione** ⇒ si chiede per nome
(`--famiglia tutto`). ⭐ L'ingresso di un desktop nuovo invece **sì**: si vede da una
`Contenitore.<nome>` che compare.

### ⛔⛔ IL PRIMO GIRO VERO — e ha trovato tre cose che nessuna prova a secco aveva preso

`[M]` 26 agosto 2026. Il gancio è stato costruito **senza la macchina di prova** (l'agente che lo
scriveva non ce l'aveva, e lo ha dichiarato). ⇒ Al primo giro vero:

| ⛔ che cosa è successo | ⭐ che cosa insegna |
|---|---|
| ⛔ **`GIRA_C11: command not found`** — una funzione che non esiste. L'esito è stato **127**, e il giro è proseguito come se niente fosse: la famiglia veloce girava **senza la sua prima maglia** | ⚠ `bash -n` passa, perché la sintassi è valida (`LEZIONI.md` §1.40). ⛔ **Si vede solo facendola girare** |
| ⛔ **il gancio pretendeva un deposito git per GIRARE** | ⭐ le due metà vivono in due posti diversi: **decidere** vuole il deposito (portatile), **far girare** vuole le scatole (macchina di prova, dove il deposito **non c'è**). ⇒ Con la famiglia chiesta per nome non c'è niente da decidere, e il deposito non serve |
| tre `git: command not found` per giro | rumore che somiglia a un guasto ⇒ senza deposito non si elenca niente, e **non è un errore** |

### ⭐⭐⭐ E IL GIRO COMPLETO È STATO FATTO — *`[M]` 26 agosto 2026, 28 minuti*

La famiglia `tutto` su GNOME, quella che si fa **prima di chiudere una fase**, girata dal gancio dal
principio alla fine:

| maglia | esito | tempo |
|---|---|---|
| passo 0 | ⭐ regge — 18/18 | 16 s |
| C1 × 10 | ⛔ **NON REGGE** — 10 cieche su 10, **zero non giudicate** | 760 s |
| C8 | ⭐ regge — tutt'e due gli inquilini aprono il browser | 6 s |
| ⭐⭐ **C8 col guasto innestato** | ⭐ **il guasto è stato VISTO**: 1 inquilino su 2 non apre il browser | 126 s |
| C11 | ⭐ regge — 13 voci su 13 | 10 s |
| C12 | ⚠ *terreno non regge* — ⛔ e **è la risposta giusta**: su quella macchina non c'è il deposito git, e C12 guarda i ganci di git | 0 s |
| C13 | ⛔ NON REGGE **durante il giro**, ⭐ **verde subito dopo** | 0 s |
| C14 | ⭐ regge | 786 s |
| | | **totale 1 704 s** |

> ### ⭐⭐ E il momento che conta è quello di C13
>
> Durante il giro C13 era **rossa**, e diceva il vero: *«negli ultimi giri **nessun guasto è mai
> stato innestato** ⇒ la rete gira, e nessuno la mette alla prova. ⛔ Da fuori è indistinguibile da
> una rete che funziona benissimo.»*
>
> ⇒ Finito il giro — che il guasto innestato **ce l'aveva dentro** — C13 è **verde**:
> *«negli ultimi 3 giri un guasto è stato innestato ed **è stato visto**»*.
>
> ⭐ **Cioè la rete adesso sa dire di sé stessa se è ancora capace di dare rosso.** ⚠ E lo dice con
> il suo limite attaccato: *«sui guasti che CONOSCE — e ogni desktop nuovo deve entrare con un
> guasto suo»* (§3.6).

⚠ **E due letture che vanno fatte con attenzione**, perché sembrano buone notizie e non lo sono:

| | |
|---|---|
| **C1 × 10 costa 760 s** | ⭐ 76 s a giro, coerente con i 74 misurati prima. ⛔ È il motivo per cui nella famiglia veloce ce ne stanno **due**, e non è un numero che si può migliorare tagliando: è il tempo che il prodotto impiega a **non** far nascere un monitor |
| **C8 è durata 6 s** | ⚠ **non è la sua velocità vera**: gli inquilini c'erano già dal giro prima, col profilo del browser già fatto. ⛔ Da zero costa molto di più — lo dice l'altra riga, i **126 s** del giro col guasto innestato |

## 7-bis.17 Che cosa esiste adesso, su disco

| file | |
|---|---|
| `banchi/11-scatole/Contenitore.gnome` | ⭐ la **ricetta** della scatola: sistema, desktop, scheda, attrezzi, l'inquilino, e l'unità che allinea il gruppo della scheda |
| `banchi/11-scatole/11-accendi.sh` | costruisci · accendi · prodotto · server · **c1** · **c5** · **c7** · **c8** · **c9** · **c10** · passo0 · impronta · spegni — ⭐ **con ogni permesso giustificato da quel che si rompe senza** |
| `banchi/11-scatole/11-passo0.sh` | ⭐ le **otto verifiche** dell'ambiente, con i tre esiti distinti |
| `banchi/11-scatole/11-c1-nasce-e-si-vede.py` | ⭐⭐ **la prima maglia della rete**, e il collaudo A. Con `--certifica`: **5 casi su 5**, compreso quello in cui *«cieca»* deve vincere su *«monitor 1/1»* |
| `banchi/11-scatole/Contenitore.kde` | ⭐ la **seconda scatola**, con KWin — la prova che la rete non è fatta su misura di GNOME |
| `banchi/11-scatole/Contenitore.xfce` · `Contenitore.lxqt` | ⭐ la **terza e la quarta**, con `labwc` — ⚠ quattro scatole, **tre** compositori (§7-bis.9) |
| `banchi/11-scatole/adattatore.{gnome,kde,xfce,lxqt}.sh` | ⭐⭐ **il «come» di ogni desktop**, allo stesso percorso dentro ogni scatola: la lista delle prove resta **una** |
| `banchi/11-scatole/11-c8-il-secondo-apre-il-browser.py` | ⭐⭐⭐ **la maglia più importante**, e il collaudo B. Con `--certifica`: **8 casi su 8**; con `--senza-cura`: il guasto innestato |
| `banchi/11-scatole/11-c8-pagina.html` | il **bersaglio nei pixel**: `#FF00FF` a schermo intero, con le scritte apposta per non essere «tinta unita» |
| `banchi/11-scatole/11-c11-allineamento.py` | ⭐⭐ **la maglia che guarda LA RETE**: le quattro scatole d'accordo su tredici voci, e l'md5 del prodotto fra queste. Con `--certifica`: **6 casi su 6** |
| `banchi/11-scatole/11-c14-non-si-disturbano.py` | ⭐⭐ **le quattro scatole non si disturbano**, misurato: stesso esito sole e insieme. Con `--certifica`: **15 casi su 15**; con `--smentisci`: dà rosso su dati veri |
| `banchi/11-scatole/11-gancio.sh` | ⭐⭐⭐ **quando parte la rete, e che cosa parte** — deciso **per percorso**, col tetto dei 3 minuti e le prove tagliate dichiarate |
| `banchi/11-scatole/11-gancio-registro.jsonl` | la **traccia** di ogni giro: che cosa è partito, che esito, quanto è durato, se è stato innestato un guasto. ⛔ È quel che tiene in vita C12 e C13 |
| `banchi/11-scatole/11-c12-il-gancio-e-vivo.py` · `11-c13-la-certificazione-e-recente.py` | ⭐ le due maglie che guardano **il gancio**. `--certifica`: **11 casi su 11** ciascuna |
| `banchi/11-scatole/11-c5-il-suono-non-e-silenzio.py` | ⭐⭐ **il suono**: si misura l'**RMS** dei campioni che arrivano al cliente, soglia dichiarata **328/32767** (−40 dBFS). ⭐ Giudica **byte**, non pixel ⇒ è l'unica maglia che oggi attraversa il prodotto da cima a fondo. `--certifica`: **12 casi su 12** |
| `banchi/11-scatole/11-c7-si-chiude-e-non-resta-niente.py` | ⭐⭐ **i residui**: impronta prima, sessione, chiusura, impronta dopo. ⚠ E il caso che **non** deve dare rosso: «si stacca soltanto» (I4). `--certifica`: **13 casi su 13** |
| `banchi/11-scatole/11-c9-il-registro-dice-di-chi.py` | ⭐⭐ **il registro**: due inquilini vivi **insieme**, e ogni riga obbligata deve dire quale. `--certifica`: **16 casi su 16** |
| `banchi/11-scatole/11-c10-le-copie-gemelle.py` | ⭐ **le copie gemelle**, e ⛔ l'elenco lo **legge da `src/Makefile`** invece di ricopiarlo. `--certifica`: **15 casi su 15**. ⭐ Gira **ovunque**, in 0,04 s, e non accende niente |
| `banchi/10-f1-testimone.py` | ⛔ **non è di questa fase e non si tocca**: è il giudice delle immagini, già tarato sul vero. C8 lo **importa** — due giudici che possono divergere in silenzio sono peggio di uno |

## 7-bis.18 ⭐⭐⭐⭐⭐ **QUATTRO MAGLIE IN PIÙ — e la rete adesso guarda anche quel che non è un pixel**

`[M]` 26 agosto 2026, sera. Quattro agenti in parallelo, **una scatola per ciascuno** (kde, xfce,
lxqt, e il portatile), inquilini con prefissi separati, log e unità separate. ⭐ E il criterio della
scelta è uno solo: **nessuna delle quattro giudica un pixel** ⇒ sono le quattro che il difetto delle
sessioni cieche (§7-bis.13) **non blocca**.

| maglia | il metro | certificazione | costo `[M]` |
|---|---|---|---|
| **C5** il suono non è silenzio | **RMS** dei campioni che arrivano al cliente · soglia **328/32767** (−40 dBFS) · ≥ 200 blocchi · ≥ 50 % sopra soglia | **12 su 12** | 38 s |
| **C7** si chiude e non resta niente | impronta **prima** / sessione / chiusura / impronta **dopo** — processi, socket, unità, scheda | **13 su 13** | 26 s |
| **C9** il registro dice di chi parla | **due** inquilini vivi insieme, e ogni riga obbligata deve dire quale | **16 su 16** | 50 s |
| **C10** le copie gemelle | i tre file gemelli byte per byte, ⭐ con l'elenco **letto da `src/Makefile`** | **15 su 15** | 0,04 s |

### ⭐ E la taratura di C5 è stata fatta attraversando il confine, non dichiarata

`[M]` Sei sessioni vere: ampiezza **0,02 ⇒ RMS 463, VERDE** · ampiezza **0,01 ⇒ RMS 231, ROSSO**. Il
percorso è trasparente (guadagno **1,0000**), e i valori sintetici della certificazione coincidono
con quelli del filo (463,4 contro 463,1). ⛔ Una soglia che non si è vista fallire è un numero
inventato.

### ⭐⭐ E C5 dimostra la sua tesi con un numero, invece di affermarla

Nello stesso giro in cui il registro diceva *«nessun monitor virtuale da catturare»* e *«0 fotogrammi
spediti»*, C5 ha contato **4 878 blocchi di suono, 4,6 MB, RMS 23 168**. ⇒ ⭐ **Zero pixel, e
qualcosa da giudicare lo stesso**: oggi C5 è l'unica maglia che attraversa il prodotto da cima a
fondo.

### ⛔⛔ IL PRIMO ROSSO CHE LA RETE TIRA FUORI DAL PRODOTTO — **due righe di `src/tastiera.c`**

`[M]` C9, su **tutte e quattro** le scatole: 5 752 righe di registro, **5 490 obbligate**, e **4** che
non si possono attribuire a nessun inquilino. Sono `src/tastiera.c:342` e `:486`, che scrivono nel
**padre** senza `registro_dice_di()`. ⛔ Due righe identiche parola per parola, una per inquilino:
**con due sessioni vive non si può dire quale sia di chi.**

⭐ Non è un guasto iniettato, non è un banco che sbaglia: **è il prodotto**, e non lo cercava
nessuno. La cura è di due righe — ⛔ **non applicata**, perché toccare `src/` obbliga a ricostruire e
a rimettere il binario in quattro scatole, e l'ordine delle fasi è una decisione dell'utente (§11).

⚠ **E accanto, un rilievo che NON è un rosso**: `[M]` **1 402 righe (25,5 %)** nominano l'inquilino
solo nella prosa e non nella parentesi. Sono attribuibili ⇒ C9 le conta e le stampa senza giudicarle.
Volerle rosse è una decisione, non un difetto.

### ⛔⛔⛔ IL SECONDO ROSSO — **e questa volta è di UN desktop solo**

`[M]` Cablate le maglie, sono state fatte girare **tutte e tre su tutte e quattro le scatole**, con i
loro guasti innestati. Ventotto giri. Ed è saltato fuori questo:

| | gnome | kde | xfce | lxqt |
|---|---|---|---|---|
| **C5** il suono | ⛔ **ROSSO** | ✅ | ✅ | ✅ |
| C5 col guasto innestato | ⭐ visto | ⭐ visto | ⭐ visto | ⭐ visto |
| **C7** i residui | ✅ | ✅ | ✅ | ✅ |
| C7 «si stacca soltanto» (I4) | ✅ | ✅ | ✅ | ✅ |
| C7 col guasto innestato | ⭐ visto | ⭐ visto | ⭐ visto | ⭐ visto |
| **C9** il registro | ⛔ rosso *(il difetto del prodotto, uguale dappertutto)* | ⛔ | ⛔ | ⛔ |

⭐⭐ **C5 è verde su tre desktop e rossa sul quarto**, e il quarto è **GNOME** — cioè quello su cui il
prodotto è nato. I numeri:

| | gnome | kde / xfce / lxqt |
|---|---|---|
| blocchi arrivati al cliente in 25 s | `[M]` **34 – 41** | `[M]` **~4 878** |
| blocchi entrati nel codificatore | `[M]` **115** | `[M]` **~4 996** |
| di cui silenzio digitale, taciuti | `[M]` **74 su 115** | ~2 % |
| RMS di quel che arriva | **22 977** (forte) | 23 168 |

⇒ ⛔ **Non è «il suono manca»: è che ne arriva un quarantesimo.** Quel che arriva è forte e giusto
(RMS 22 977, picco al fondo scala, 100 % sopra soglia): ⭐ **la soglia non c'entra**, e infatti C5 non
dà rosso per il livello ma per il **conto** — *«41 blocchi su 200 attesi al minimo: non è un
flusso»*.

⚠ **E non è la scatola invecchiata**: la scatola di GNOME è stata **buttata giù e rifatta**, prodotto
e server rimessi dentro, e il rosso è tornato identico. ⛔ Tre giri su tre.

> ⭐⭐⭐ **Ed è la tesi della fase, misurata una seconda volta e nel verso che nessuno si aspettava.**
> §7-bis.7 diceva *«il secondo desktop ha chiesto una cosa che il primo non chiedeva»*. ⇒ Qui il
> desktop che si comporta diversamente è **il primo**, quello di casa: le tre scatole nuove vanno, e
> quella su cui il prodotto è cresciuto no. ⛔ Senza le altre tre, questo numero sarebbe stato letto
> come *«il suono va così»*.
>
> `[?]` **La causa non è stata trovata**, ed è scritta invece che indovinata: il sospetto è che nella
> sessione GNOME qualcosa d'altro tocchi il grafo audio dell'inquilino (`wireplumber` che sospende, o
> un secondo `pipewire` della sessione), ma ⛔ **non è misurato**, e finché non lo è resta un `[?]`.

### ⛔⛔ E UN DIFETTO NEL CABLAGGIO, che nessuna certificazione poteva prendere

`[M]` `esegui_maglia` legge una maglia innestata **al contrario**: `0` vuol dire *«il guasto è stato
visto»*, e nel registro finisce `ha_visto_il_guasto`, che è quel che C13 legge. ⛔ **C9 usciva col
verdetto grezzo** ⇒ nel giro col guasto avrebbe scritto `false` **proprio quando il guasto era stato
visto benissimo**, e C13 avrebbe cominciato a mentire.

⭐ **E la cura non era invertire l'esito**: C9 è rossa **anche senza guasto** (le due righe di
`tastiera.c`), quindi un semplice *«rosso ⇒ visto»* avrebbe detto «visto» anche se l'iniezione non
avesse morso — un predicato che non può fallire, §1.44 di nuovo, e stavolta a reggere la
certificazione di tutta la rete. ⇒ Si pretendono **due** cose: verdetto rosso **e** più righe senza
nome di prima. `[M]` 4 senza guasto ⇒ 5 490 col guasto. ⇒ `LEZIONI.md` §1.52.

⚠ E un secondo difetto dello stesso genere, `LEZIONI.md` §1.51: `11-accendi.sh prodotto` falliva su
tutte e quattro le scatole con *«Text file busy»* — ⛔ un rosso che veniva dall'**ordine dei
comandi**, non dal prodotto.

### ⭐⭐ LA METÀ-PORTATILE DEL GANCIO ADESSO È VIVA — **e ci mette 1 secondo**

§4.6-novemdecies aveva scoperto che il gancio ha due metà su due macchine. ⛔ Quella sul portatile
non innestava **nessun** guasto ⇒ C13 là non avrebbe potuto **mai** diventare verde. ⇒ C10 ha adesso
un `--guasto-innestato` che copia i file **veri** in una cartella temporanea, ne cambia **un byte** e
pretende il rosso.

`[M]` Sul portatile, famiglia `rete`: **C10 verde · C12 verde · C13 verde**, ⭐ in **1 secondo**,
senza accendere niente. (C11 e C14 dicono *«non ho potuto guardare»*, ed è giusto: le scatole non
sono lì.) Il gancio è stato **installato** come `pre-push`.

### ⚠ E i tagli, dichiarati invece che subìti

`[M]` Il tetto della famiglia veloce è a **173 s su 180** — ⚠ misurato di nuovo il 26 agosto con
C10 dentro e con la voce nuova di C11: **venti secondi in più di quanto si credeva**, e resta pieno.
§5.1 dice che una maglia in più si
**scambia**, non si somma. ⇒ C5 (38 s), C7 (26 s) e C9 (50 s) stanno in `tutto` e in `desktop-nuovo`,
col loro guasto innestato accanto. ⛔ **L'unica che entra nella veloce è C10**, che costa meno della
risoluzione del cronometro. ⭐ E ci entra **due volte**: anche nella famiglia `rete`, perché il
gemello vive metà in `src/` e metà in `banchi/rcp/`, e un cambiamento **lì** fa scattare `rete` — cioè
esattamente il cambiamento che rompe il gemello.

## 7-bis.19 ⭐⭐⭐⭐⭐ **IL 27 AGOSTO — la rete è completa, e il tappo non c'era**

`[M]` Una giornata, fino a **dieci agenti insieme**, e il risultato in una riga: ⭐ **le quindici
maglie esistono, girano, e il difetto più vecchio del progetto è chiuso.**

### ⭐⭐⭐ Il fatto della giornata: **le sessioni non nascevano cieche**

Il difetto di `fasi/10-…` §7.4 — *«dieci sessioni nuove su dieci nascono senza monitor»* — bloccava
cinque prove della rete e rinviava la fase 12. ⛔ **Non era del prodotto, e non era nemmeno un
difetto solo.** Sono state tre cose, e ciascuna nascondeva la successiva:

| | che cos'era | come si è visto |
|---|---|---|
| ⛔⛔ **la prova** | **C1 non poteva dire verde** — leggeva `ZERO MONITOR`, che il prodotto scrive nel percorso di una nascita **riuscita**, e il suo ramo verde era irraggiungibile | un agente mandato a **smentirla** ⇒ `LEZIONI.md` §1.53 |
| ⛔ **la scatola** | il §6 della ricetta spostava il gruppo `polkitd` da 991 per darlo alla scheda; `groupmod` non porta i file ⇒ `polkit` moriva, `gnome-shell` incassava **4 scadenze da 25 s** | `[M]` da **~97 s** a **1,0 s** dopo la cura ⇒ §1.54 |
| ⭐⭐⭐ **la causa vera** | **l'inquilino non era nei gruppi `video` e `render`** | `[M]` **17 sessioni su 17** vedono coi gruppi · **0 su 4** senza · ⭐ dati i gruppi allo stesso inquilino ⇒ **2,04 s**. Una variabile sola, esito ribaltato |

⭐⭐ **E la tabella di §7.4 si spiega da sola**: `provanic4/5/6` — quelli che non videro **mai**, su
**98 · 55 · 50** tentativi — non hanno quei gruppi; `prova` e `provanic1`, che videro sempre, li
hanno. ⇒ ⛔ **Non era intermittente: erano due popolazioni di inquilini.**

⚠ **E la coda tocca il passato**: i banchi creavano inquilini per conto loro in **tredici** posti, e
⛔ senza quei gruppi. ⇒ Ogni banco che ha misurato lì ha misurato **una sessione che non vedeva**.
⭐ Curati dodici in **un file solo** (`banchi/attrezzi-gruppi-scheda.sh`), e uno di essi
(`07-b64-terreno.sh`) lo usano **ventitré banchi** delle fasi 9 e 10.

### ⭐⭐ E il monitor: come nasce davvero, letto e misurato

`[R]` `--headless` da solo **non crea nessun monitor**, ed è voluto. In tutto Mutter **due** posti ne
creano uno: la bandiera `--virtual-monitor` all'avvio, e `RecordVirtual`. ⭐ E quello di
`RecordVirtual` nasce **quando PipeWire fissa il formato**, cioè **dopo che un consumatore si è
agganciato** — `[M]` 65–93 ms dopo, mai prima.

⇒ ⭐⭐ **Ecco perché le cinque prove «bloccate» non erano bloccate**: mentre un cliente è attaccato,
lo schermo **c'è** — che è esattamente la condizione in cui quelle cinque lavorano.

⚠ E un debito, scritto invece che nascosto: `[M]` il monitor **muore con la connessione D-Bus** di
chi ha chiamato `RecordVirtual`, che nel prodotto è il **figlio**, e il figlio muore col client. ⛔ Sulla
carta contraddice I4. ⭐ Ma **C6 misura verde**: `[M]` stesso figlio, stessa scena (60,5 % ⇒ 60,5 %,
scarto 0,000) — **le finestre si ritrovano**. ⇒ Resta un debito dichiarato, non un lavoro di oggi.

### ⭐ Le cinque maglie che mancavano, e la sesta che nessuno aveva chiesto

| | certificazione |
|---|---|
| **C2** una finestra si apre — il pixel, non il conto dei processi | 51 casi |
| **C3** i fotogrammi cambiano — il canarino contro l'immagine congelata | 56 |
| **C4** il tasto arriva **fino allo schermo** — e solo nella **zona attesa** | 37 |
| **C6** si stacca e si ritrova — ⭐ legge il **pid del figlio**, non il colore | 46 |
| **C8b** la pagina vista **dal cliente** — il verdetto è una **differenza** | 17 |
| ⭐⭐ **C15** la metà remota gira davvero | 21 |

⭐⭐ **C15 non era nella lista, ed è il buco più serio che restava**: ⛔ con la macchina di prova spenta
per sempre, `[M]` **C12 e C13 restano verdi** e nessuno si accorge che le maglie vere non girano più.
⇒ Dimostrato togliendo dal registro l'unica riga eseguita sulle scatole: **C12 verde · C13 verde ·
C15 ROSSA** sullo stesso file.

### ⛔⛔ E le maglie mentivano ancora — **dieci difetti, e due erano in tutte**

⭐ Due agenti mandati a **refutare** hanno trovato quel che nessuna certificazione aveva preso:

| | |
|---|---|
| ⛔⛔ **«AMMESSO» era un predicato che non poteva dire di no** | quella parola sta **anche nei due messaggi di rifiuto** ⇒ **nove maglie** credevano di essere entrate anche quando erano respinte. ⭐ Curato con **una** funzione per nove, e la prova: col controllo vecchio, **7 casi nuovi su 9** rispondevano male |
| ⛔ **il guasto innestato letto sul colore** | una maglia già rossa per conto suo diceva *«il guasto è stato visto»* anche se l'iniezione non aveva morso ⇒ §1.52, curato in **C5, C9, C10** |
| ⛔⛔ **C7 diceva verde su una I4 rotta** | chiedeva *«è cambiato qualcosa?»* invece di *«il figlio c'è ancora?»* |
| ⛔ **C8 accusava il filo** | un cliente **respinto** usciva come *«nessun fotogramma è arrivato dal filo»* |
| ⛔ **il gancio** | un esito `3` faceva scrivere `ha_visto_il_guasto: false` — un'accusa a una prova che non è girata |

### ⭐⭐⭐ IL GIRO INTERO, e i numeri

`[M]` 27 agosto 2026, `--famiglia tutto` sulle quattro scatole, binario `aa950804fed7`:

| | |
|---|---|
| durata | **7 896 s** (2 h 11) |
| esiti `0` | **57** |
| ⭐ **guasti innestati visti** | **23 su 25** |
| esiti `3` (*«non ho potuto guardare»*) | **6** |
| ⛔ rossi | **3**, e sono **lo stesso rosso**: C1 su kde/xfce/lxqt |
| ⭐⭐ **rossi del banco** | **nessuno** |
| **C11** allineamento | ⭐ verde, 14 voci, stesso binario in tutte e quattro |
| **C14** non si disturbano | ⭐ verde, **801 s**, impronta identica sola e in parallelo |

⛔ **E i tre rossi sono il prodotto, ed è la fase 12**: `[R]` `src/sessione.c:778` — il prodotto sa
avviare **solo GNOME**. ⇒ Su KDE, XFCE e LXQt la rete prova l'ambiente, il suono, i residui, il
registro e l'allineamento; ⛔ **non il prodotto**, perché lì il prodotto non ci gira.

### ⭐ E cinque cure nel prodotto, tutte nate da una maglia

| | |
|---|---|
| `src/tastiera.c` · `webtransport.c` | ⭐ **il primo rosso che la rete ha tirato fuori dal prodotto**: 4 righe di registro su 5 490 non dicevano di chi parlavano |
| `src/figlio.c` — l'anello dell'audio | ⛔ non si svuotava senza palco ⇒ `[M]` **96 489 ms** di trabocco |
| `src/figlio.c` — la busta non inizializzata | ⛔ **il «terzo stato» di §7.4 era memoria sporca** ⇒ §1.55 |
| `src/mutter.c` | una riga diceva *«monitor virtuale montato»* quando il monitor **non esisteva ancora** |
| `src/provisiona.sh` + `src/figlio.c` | ⭐⭐ i gruppi della scheda, letti **dal nodo**, e un controllo che **lo dice nel registro** invece di far nascere una sessione che non si vede |

---

# §8 · Le domande, e le risposte avute

*Le sei domande della prima stesura. ⭐ Cinque hanno avuto risposta dai due revisori; una resta
all'utente.*

| | | esito |
|---|---|---|
| **Q1** | che classe di regressione il disegno non prende? | ✅ **risposta**, ed è diventata **§6** |
| **Q2** | il contenitore regge il pezzo che tiene il conto di chi è collegato? | ⭐⭐ **CHIUSA CON UN `[M]`, 26 agosto 2026: SÌ** — 18 verdi su 18, al prezzo di due permessi dichiarati (§7-bis.1) |
| **Q3** | come si resta ciechi al desktop? | ⭐⭐ **CHIUSA CON UN `[M]`, 26 agosto 2026**: le stesse otto verifiche girano su **Mutter e su KWin** senza una riga cambiata — 18/18 su tutt'e due (§7-bis.7) |
| **Q4** | un utente per scatola: che cosa si perde? | ⚠ **la correttezza a più utenti, che non è capienza** ⇒ ❓ **§4.4, decide l'utente** |
| **Q5** | quanto deve durare la famiglia veloce? | ✅ `[?]` **3 minuti**, provvisorio, da misurare (§5.1) |
| **Q6** | la marca è la strada giusta? | ✅ *«sì, ma da sola no»* ⇒ **§4.3** |

## 8.1 ⚠ E una cosa che nessuno dei due revisori ha detto, e va scritta

⛔ **Tutt'e due hanno accettato senza discutere la premessa più fragile del disegno**: che il
contenitore debba ospitare **il prodotto intero**. ⇒ Non è stato chiesto a nessuno se esista un
taglio diverso — per esempio il desktop dentro e il server fuori.
⚠ La risposta breve è che **non si può**, perché il prodotto accende il compositore **dentro** la
sessione che governa lui. ⭐ Ma è una `[?]` mai messa alla prova, e va lasciata scritta invece che
data per chiusa.

---

# §9 · I criteri di chiusura della fase

*Proposti dalla revisione, accolti: la fase **non è chiusa** se manca uno di questi.*

*⭐ Aggiornati il **26 agosto 2026**, mattina, con quel che è stato fatto nella notte.*

| # | | a che punto |
|---|---|---|
| 1 | il **passo 0** è stato eseguito e scritto, con esito `[M]` | ✅ **18/18 su quattro desktop** |
| 2 | esiste **una** scatola GNOME che gira | ✅ ⭐ **ne esistono quattro** |
| 3 | ⭐⭐ **la rete diventa rossa sul collaudo A senza suggerimenti** | ✅ `[M]` 5 sessioni cieche su 10 giudicate |
| 4 | la rete prende il **collaudo B**, ⚠ oppure è scritto perché non può e come si compensa | ✅ ⭐ **preso**: col guasto innestato il **secondo** inquilino non apre il browser, il primo sì (§7-bis.10) |
| 5 | le prove visive **non si basano solo sulla marca** | ✅ colore con **tolleranza dichiarata** + istogramma + il «prima» |
| 6 | il **gancio** è definito per percorso, non per buona volontà | ✅ ⭐ `11-gancio.sh`, e ha già girato sul vero (§7-bis.16) |
| 7 | esiste la **politica del rosso** | ✅ §5.2 |
| 8 | la rete ha **almeno una prova che controlla sé stessa** | ✅ ⭐⭐ **cinque**: C11 · C12 · C13 · C14 · **C15**, che non era nella lista ed era il buco più serio (§7-bis.19) |
| 9 | il **tempo** della famiglia veloce è misurato, non stimato | ✅ ⭐ `[M]` **173 s** su un tetto di **180**, e il **giro intero** `[M]` **7 896 s** (§7-bis.19). ⛔ La veloce è **piena**: una maglia in più si **scambia**, non si somma |
| 10 | ⛔ **quel che la rete non prende è scritto** | ✅ §6, ⭐ **compreso quel che oggi non può guardare e perché** |
| 12 | ⭐⭐⭐ **e la lista è finita**: undici prove del prodotto e cinque della rete, **tutte scritte, tutte certificate, tutte fatte girare** | ✅ `[M]` 27 ago: **57 esiti `0`**, **23 guasti innestati visti su 25**, ⛔ **nessun rosso del banco** (§7-bis.19) |
| 11 | ⭐⭐ e il criterio dell'utente, che sta sopra tutti: **la rete ha preso qualcosa che l'occhio non avrebbe preso**. Se no, **la fase è fallita e va detto** | ✅ ⭐⭐⭐⭐ **sì, e il conto è un altro adesso**: ⭐ **il difetto più vecchio del progetto**, chiuso il 27 ago — i gruppi `video` e `render` (§7-bis.19) · **cinque cure nel prodotto**, ognuna nata da una maglia · ⛔ **dieci difetti nelle maglie stesse**, due dei quali erano in **nove maglie su nove** · e prima ancora: **sì, e cinque volte**: la sessione che nasce cieca · il secondo inquilino che non apre il browser · ⛔ **tre rossi del BANCO** che sarebbero passati per difetti del prodotto (§7-bis.11) · ⭐ **le quattro righe di registro senza inquilino** · ⭐⭐ **il suono che su GNOME arriva a un quarantesimo** — e quest'ultimo **nessun occhio l'avrebbe visto**, perché il suono c'era ed era forte (§7-bis.18) |

---

# §10 · Che cosa resta `[?]` all'apertura

| | |
|---|---|
| ~~`[?]`~~ ⭐ **`[M]`** | ~~se il contenitore regga il pezzo di sistema che tiene il conto di chi è collegato~~ ⇒ **passo 0 eseguito il 26 agosto 2026: regge, 18 su 18** (§7-bis.1) |
| ~~`[?]`~~ ⭐ **`[M]`** | ~~quanto dura davvero la famiglia veloce~~ ⇒ **153 s su 180**. ⛔ E il tetto è **pieno**: qualunque maglia in più va **scambiata**, non sommata |
| ~~❓~~ ⭐ **chiusa** | ~~come si esegue C8~~ ⇒ **in una scatola, con due inquilini** (risposta dell'utente, §4.4), e ⭐ **il collaudo è passato** (§7-bis.10) |
| ~~`[?]`~~ ⭐ **`[M]`** | ~~se le quattro scatole davvero non si disturbano~~ ⇒ **misurato**: stesso esito sole e in parallelo, quattro su quattro (§7-bis.15). ⚠ **Resta fuori** la contesa vera sulla scheda grafica, che vuole sessioni vive |
| `[?]` | se esista un taglio diverso fra contenitore e prodotto (§8.1) |
| ~~❓ decide l'utente~~ ✅ **deciso** | il **registro del gancio** va in git — deciso dall'utente il 27 agosto 2026. ⭐ Con `merge=union` in `.gitattributes`: il quaderno è fatto di righe che si **aggiungono**, e due macchine che scrivono in giorni diversi non sono un conflitto da risolvere a mano. ⚠ Il prezzo, dichiarato: il file risulta modificato a ogni giro |
| ⛔ **APERTO, ed è la fase 12** | ⭐ `[M]` **il prodotto sa avviare solo GNOME** (`src/sessione.c:778`) ⇒ C1 dà rosso su kde/xfce/lxqt, ed è **l'unico rosso** che il giro intero produce. ⚠ E una cosa che la fase 12 troverà: ⛔ **KWin non sa nascere cieco** — con `--output-count 0` un'uscita la fa lo stesso, quindi il disegno «zero monitor propri» **non si trasporta uguale** |
| ⚠ **debito dichiarato** | il **palco muore con la connessione D-Bus del figlio** ⇒ sulla carta contraddice I4. ⭐ Ma `[M]` C6 misura **verde**: le finestre si ritrovano. ⇒ Scritto, non curato — la cura è architetturale (`DECISIONI.md` §4.6-teretvicies) |
| ~~⛔ aperto~~ ⭐ **chiuso** | ~~perché la scatola non si spegne da sola~~ ⇒ **era il SEGNALE, non un'unità appesa**: `[M]` SIGTERM (il predefinito di `podman stop`) lascia la scatola in piedi **30 s su 30** — `systemd` come primo processo lo ignora; `SIGRTMIN+3` la spegne in **3,1 s**. ⇒ I «quattro minuti» erano un tetto scaduto, non un'attesa. La cura (`STOPSIGNAL` nelle ricette) è in vigore, e ⛔ l'ipotesi *«la tiene su una sessione viva»* è **smentita**: con una sessione dentro lo spegnimento è quello pulito (§7-bis.18) |
| ~~⛔⛔ APERTO~~ ⭐ **chiuso** | ~~C5 è rossa su GNOME~~ ⇒ **era la stessa radice della sessione cieca**: senza palco il prodotto non svuotava l'anello dell'audio (`[M]` **96 489 ms** di trabocco). Curato in `src/figlio.c`; `[M]` C5 verde su tutte e quattro le scatole. *(voce vecchia: `[M]` C5 rossa su GNOME e verde sugli altri tre*: al cliente arrivano **34–41** blocchi di suono in 25 s invece di **~4 878**, e quel che arriva è forte e giusto. ⛔ Non è la scatola invecchiata (rifatta da zero, stesso rosso) e non è la soglia. `[?]` La causa non è misurata (§7-bis.18) |
| ~~⛔ APERTO~~ ✅ **curato** | ~~4 righe di registro su 5 490 non dicono di chi parlano~~ ⇒ curato il 27 ago in `src/tastiera.c`, `tastiera.h`, `webtransport.c` — ⚠ **otto righe, non due**: le due misurate più sei gemelle nella stessa funzione. `[M]` C9 verde su tutte e quattro |
| ❓ **decide l'utente** | il **registro del gancio** va in git o no? In git dà a C13 una memoria sola per tutte le macchine; fuori evita di avere quel file modificato a ogni giro. ⚠ E oggi ne esiste **uno solo, sulla macchina di prova** (`DECISIONI.md` §4.6-novemdecies) |
| ~~⛔ aperto~~ ⭐ **chiuso** | ~~perché la metà dei giri di C1 non giudica~~ ⇒ **era lo sgombero**: si aspetta l'evento e non l'orologio, e `[M]` il giro dopo dà **10 giudizi su 10** (§7-bis.13) |
| ~~⛔⛔ blocca~~ ⭐⭐⭐ **CHIUSO il 27 agosto** | **erano i gruppi `video` e `render` dell'inquilino**: `[M]` 17 sessioni su 17 vedono coi gruppi, **0 su 4** senza, e la controprova ribalta l'esito con una variabile sola (§7-bis.19). ⛔ E non era del prodotto: era della **provvista**, più una maglia che non poteva dire verde e una scatola che si rompeva da sola. *(voce vecchia: `[M]` dieci sessioni GNOME nuove su dieci nascono cieche* ⇒ C2, C3, C4, C6 e la metà B di C8 **non si possono misurare**. È il difetto APERTO della fase 10 §7.4 — ⛔ si tura curando il **prodotto**, non scrivendo un'altra maglia |
| `[?]` | quanto costa in capienza un fotogramma in più a testa — ⚠ **fuori da questa fase**, sta in `MASTERPLAN.md` M1 |

---

# §11 · ✅ **LA DOMANDA È DECADUTA** — *e la ragione vale più della risposta*

Questa sezione chiedeva: **«si va avanti con KDE avendo metà della rete che non può guardare, oppure
prima si cura la sessione che nasce cieca?»**

⇒ ⭐⭐ **La domanda non esiste più, perché la premessa era falsa.** `[M]` 27 agosto 2026: le sessioni
**non nascevano cieche**. Erano tre cose sovrapposte — una **maglia** che non poteva dire verde, una
**scatola** che si rompeva da sola, e la causa vera: ⭐ **l'inquilino non era nei gruppi `video` e
`render`** (§7-bis.19).

⇒ Le cinque prove dichiarate «bloccate» **non erano bloccate**, e oggi girano tutte.

> ### ⛔⛔ E la lezione è più grossa della fase
>
> Per settimane un numero — *«dieci sessioni su dieci»* — ha governato l'ordine del lavoro, il
> rinvio di una fase, e una lista di cose «impossibili». ⛔ **Quel numero veniva da un'unica prova, e
> quella prova non poteva produrre nessun altro risultato.**
>
> ⭐ Ci sono voluti dieci minuti a un agente il cui mandato era **«prova a smentirla»**. ⇒ La regola
> che ne esce, e vale oltre questa fase: **quando un rosso regge da giorni e nessuno riesce a farlo
> tornare verde, la prima domanda non è *«perché il prodotto è rotto»* ma *«questa prova sa dire
> verde?»***. ⇒ `LEZIONI.md` §1.53.

## ⭐ Quel che resta all'utente, adesso

| | |
|---|---|
| ✅ **il quaderno del gancio in git** | **deciso il 27 agosto**: sì, con `merge=union`. ⚠ Il prezzo è un file che risulta modificato a ogni giro |
| ⭐ **la fase 12 è il prossimo passo, e non è più bloccata** | ⛔ Ma quel che troverà è già misurato: il prodotto **sa avviare solo GNOME** (`src/sessione.c:778`), ed è **l'unico rosso** che il giro intero produce. ⚠ E KWin **non sa nascere cieco**: il disegno «zero monitor propri» non si trasporta uguale |
| ⚠ **un debito, non un lavoro** | il palco muore con la connessione D-Bus del figlio ⇒ sulla carta contraddice I4, ⭐ ma C6 misura **verde**: le finestre si ritrovano. Curarlo è architetturale, e ⇒ `DECISIONI.md` §4.6-teretvicies |

---

# §12 · Il giudizio dell'utente

*(da riempire alla chiusura)*
