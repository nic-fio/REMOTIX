# F4-A8 — La pagina, modo tocco

*Anello A8 della fase 4, 14 agosto 2026. Macchina di prova **CHUWI**, sessione `wayland`,
Google Chrome **151.0.7922.137**. Banco `banchi/04-b28-gesti.py` + `04-b28-lancia.sh`, porte
7671-7672. Codice: `src/pagina.html`, **solo** dentro l'ancora `F4-TOCCO`.*

---

## 1. Che cosa cambia per l'utente

**Il telefono in mano diventa un trackpad**: il dito trascina una freccia che si vede *prima* di
cliccare, e la pagina passa **da sola** fra le due disposizioni — prendi il mouse e diventa
classica, tocchi lo schermo e torna a tocco — senza nessuna impostazione da cercare.

---

## 2. Serve una decisione di Nic? — ⭐ **SÌ, e su tre cose**

⭐ *«Un gesto non si giudica leggendolo, si giudica usandolo»* (`DECISIONI.md` §5-bis.3). Le
soglie qui sotto sono **misurate sul riconoscitore**, non su una mano: le ho scelte da due
riferimenti indipendenti e dal decimo di millimetro che `SPECIFICHE.md` §7.1 usa già. Ma
**quanto si scollano indice e medio della mano di Nic non l'ha misurato nessuno**.

| | La domanda | Perché non la chiude un banco |
|---|---|---|
| ⭐ **1** | ⛔ **Il clic destro esce come doppio clic sinistro quando le due dita non si sovrappongono.** Quanto capita, con una mano vera? | Ho provato che sotto la sovrapposizione di **un campione** succede. Con che frequenza succeda a Nic è `[?]`, e la cura costerebbe **300 ms su ogni clic sinistro** — vietati da `CODER.md` §1-bis |
| **2** | **180 ms per contatto bastano al tap a TRE dita?** | Tre dita non si staccano insieme. `[M]` la sola mano sintetica ne consuma 147 su 180 |
| **3** | **Il verso della rotella a due dita, e il guadagno del trackpad** | Ho scelto «dita che scendono = rotella in su» e guadagno 1,0. Sono `[?]`: si giudicano con un dito, in dieci secondi |

⚠ E il ridimensionamento di §5-bis.0 vale: su Android l'uso primario è **DeX**, con mouse e
tastiera veri. Questi gesti servono al telefono in mano, che è il ripiego. **Non ho speso tempo
sul pizzico.**

---

## 3. Che cosa ho MISURATO

### 3.1 Il banco — `[M]` 14 agosto 2026, due giri consecutivi

| | |
|---|---|
| **il giudice, certificato prima della misura** | ⭐ **verde → rosso → verde su CINQUE guasti**, uno per famiglia di confusione: il tap lungo che clicca, i 30 ms che diventano doppio sinistro, la rotella al contrario, il tap-e-mezzo che non trascina, il pizzico che manda una rotella. Ciascuno tinge di rosso **solo il suo caso** |
| **la misura** | ⭐ **24 verdi su 25**, due giri su due, **zero guasti dello strumento** |
| ⛔ **l'unico rosso** | **S1b — la cucitura del puntatore**, ed è dell'anello A7: vedi §5 |
| **i byte** | **78 messaggi** di `RCP.md` §7.3, identificatori da **1 a 78**, crescenti su tutto il canale, decodificati da un lettore scritto nel banco dalla tabella — non copiato dalla pagina |
| **dove si ricontrolla** | `banchi/04-b28-esiti.jsonl` (scena, verdetti e guasti) · `banchi/04-b28-registro.jsonl` (i byte in esadecimale, gesto per gesto) · `python3 banchi/04-b28-gesti.py --verdetto …` rigiudica senza browser |

⛔ **La scena, dichiarata**: il browser si apre sul **desktop vero** dell'utente — non l'ho spostato
su uno schermo finto. Il tocco lo dichiara il banco (`Emulation.setTouchEmulationEnabled`), e
⚠ **quel che se ne ricava è l'emulazione, non un dito** (`LEZIONI.md` §1.11): da qui escono i
**confini del riconoscitore**, che sono deterministici, e **nessun numero su una mano vera**.

### 3.2 ⛔ Le soglie — in millisecondi e in pixel CSS

⚠ Pixel **CSS** e non fisici: il dito è largo dieci millimetri su qualunque schermo, e il pixel
fisico raddoppia sui telefoni.

| Soglia | Valore | Da dove viene | Che confusione separa |
|---|---|---|---|
| `T_TAP` | **180 ms**, ⛔ **per CONTATTO** | `[S]` `ViewConfiguration.TAP_TIMEOUT` di Android **e** il tap timeout di libinput — due riferimenti indipendenti | il tap dal contatto che resta giù |
| `D_TAP` | **9 px CSS** | `[S]` la `touch slop` di Android, 8 dp | il tap dal trascinamento |
| `T_SEQUENZA` | **300 ms** | `[S]` `DOUBLE_TAP_TIMEOUT` di Android | quanto dura l'aggancio del tap-e-mezzo |
| ⭐ `D_STESSO_DITO` | **40 px CSS ≈ 10 mm** | ⭐ **da noi**: `SPECIFICHE.md` §7.1, *«un dito è largo ~10 mm»* | ⛔ **il tap-e-mezzo dal tap a due dita** — è la soglia più importante di tutte |
| `D_PIZZICO` | **24 px CSS** | `[?]` ipotizzato | il pizzico dalla rotella |
| `PX_PER_SCATTO` | **40 px CSS** = 120 unità | `[?]` ipotizzato. ⛔ **Non** è il 114 misurato l'11 agosto: quello è il fattore Firefox+Mutter, e `RCP.md` dice che non è una costante del protocollo | — |
| `GUADAGNO` | **1,0** | `[?]` il puntatore sta sotto il dito | — |
| ⭐ **la sovrapposizione** | ⛔ **≥ 1 campione** | misurata, vedi §3.3 | il clic destro dal doppio clic sinistro |

### 3.3 ⭐⭐ Le tre confusioni che ho trovato — e §5-bis.3 ne nomina **zero**

`DECISIONI.md` §5-bis.3 dice: *«tap e trascinamento a due dita non si confondono — un tap è breve
e fermo»*. ⭐ **È vero, e nomina la coppia sbagliata**: quei due si separano con due soglie ovvie.

**⑴ ⛔ TAP-E-MEZZO E DOPPIO CLIC SONO LO STESSO GESTO, E NON SI SEPARANO.**
Il doppio clic — che nella tabella dei sette **non c'è**, e che si fa cento volte al giorno — è
«tap, poi tap». Il tap-e-mezzo è «tap, poi premi e trascina». ⇒ Nell'istante in cui il secondo
dito si appoggia hanno prodotto **la stessa identica sequenza**, e nessuna soglia li distingue.

⭐ **La cura non è una soglia, è un cambio di forma: si preme al contatto e si rilascia al
distacco.** Il dito si stacca subito e fermo ⇒ premuto+rilasciato = il secondo colpo di un doppio
clic. Il dito resta giù e trascina ⇒ premuto, il puntatore segue, rilasciato = trascinamento.
**Le due strade partono dallo stesso byte e divergono da sole, senza nessun ritardo aggiunto.**
⛔ La stesura «prudente» — aspettare *T* ms per decidere — sembra più sicura e **rompe il doppio
clic**, ritardandone il secondo colpo di *T*.
`[M]` provato dai due casi gemelli **C5a** (doppio clic: quattro eventi del sinistro, **zero**
PUNTATORE) e **C5b** (trascinamento: clic, premuto, **7 PUNTATORE**, rilasciato) — stessa apertura,
esiti diversi.

**⑵ ⛔ LA COPPIA CHE SI CONFONDE DAVVERO È «2 DITA TAP» CONTRO «1 DITO TAP RIPETUTO»** — cioè un
clic destro che esce come doppio clic sinistro. Succede quando le due dita **non si sovrappongono
nel tempo**: indice giù a 0 ms e su a 100, medio giù a 130 e su a 230. Ciascun contatto, per conto
suo, è un tap a un dito perfetto.

⛔ **Non esiste una soglia in millisecondi che li separi**, perché la stessa sequenza è anche
«clicco qui, poi clicco subito lì» — legittimo e frequente. L'unica cura sarebbe **ritardare ogni
clic sinistro di 300 ms**, e il tetto del ritardo *nostro* è 50 ms in tutto (`CODER.md` §1-bis).

⇒ ⭐ **La soglia dichiarata è una SOVRAPPOSIZIONE, non un tempo: due dita fanno un gesto a due dita
se sono giù insieme per almeno UN campione.** Il conteggio del gesto è il **massimo di dita
contemporanee**, non quelle di partenza né quelle rimaste. `[M]` caso **C3** — due dita a **30 ms**
di distanza ma sovrapposte ⇒ **un clic destro e basta**. `[M]` caso **C4** — due contatti che non
si sovrappongono mai ⇒ **due clic sinistri**, ed è il difetto che il banco **pretende così com'è**:
il giorno in cui cambiasse, C4 diventa rosso e questa riga si rilegge.

⭐ **E il tap-e-mezzo NON cade nella stessa trappola, perché lì la separazione è SPAZIALE**: due
contatti che non si sovrappongono sono **lo stesso dito che ribatte** se ricadono entro
**40 px CSS ≈ 10 mm**, due dita diverse se ricadono più lontano. ⭐ Lo stesso decimo di
millimetro che motiva il puntatore disegnato (`SPECIFICHE.md` §7.1) è quello che separa i due
gesti. ⚠ E il banco lo prova con **identificatori di contatto diversi**, come fa un pannello vero:
l'aggancio non guarda l'identità del contatto, guarda dove e quando.

**⑶ ⛔ ROTELLA CONTRO PIZZICO — la terza, e la tabella dei sette non la nomina affatto.**
Sono tutt'e due «due dita che si muovono», e nessuna delle due è un tap: le soglie del tap non le
separano. Si guardano due grandezze e vince la più grande — di quanto è cambiata la **distanza**
fra le dita (pizzico) contro di quanto si è spostato il loro **centro** (rotella) — e ⛔ la
decisione si prende **una volta e si tiene** per tutto il gesto, o si oscillerebbe fra zoom e
scorrimento dentro lo stesso trascinamento. `[M]` **C7a** (dita che si allontanano: **zero**
ROTELLA, vista a 3,00×) e **C7b** (dita parallele: **8** ROTELLA, vista ferma a 1,00×).

### 3.4 ⛔ Due difetti del riconoscitore che ha trovato il banco, non la lettura

**⒜ La durata si misura per CONTATTO, non sul gesto intero.** `[M]` caso G6: il tap a **tre dita**
non produceva **nessun clic centrale**, e il gesto letto sulla carta era perfetto. Misurata dal
primo dito giù all'ultimo su, la soglia dei 180 ms la mangiavano gli scarti di appoggio. ⇒ Un tap
è breve se **ogni contatto** è durato meno di `T_TAP` — la regola di libinput, l'unica che
sopravvive a più di un dito.

**⒝ ⭐ Un dito che si stacca somiglia a uno scorrimento.** Il centro di due dita a −40 e 0 sta a
−20; il centro di due dita a 0 e +40 sta a +20. Tre dita che si staccano una per volta passano dal
primo insieme al secondo **senza che nessun dito si sia mosso di un micron**, e il centro salta di
40 px — oltre la sbavatura. Il riconoscitore decideva «rotella», e un gesto deciso non è più un
tap. ⇒ **La differenza fra due centri ha senso solo sullo STESSO insieme di dita**: quando
l'insieme cambia, il riferimento si rifonda e non si decide niente in quel campione. E il
`touchend` non fa più un giro di riconoscimento.

### 3.5 ⭐ Il passaggio automatico — misurato su eventi VERI

⛔ **Il contesto si legge da che cosa c'è, non dal sistema operativo**: nell'ancora `F4-TOCCO` non
compare `userAgent` né `navigator.platform` (caso **D4**, verificato sul sorgente, commenti
esclusi). Le prove, dalla più forte alla più debole: **un evento di puntatore vero**
(`pointerType`), poi `(any-pointer: fine)`, poi `(pointer: coarse)`, e ⚠ come **ripiego dichiarato**
la larghezza della finestra se `matchMedia` non risponde. Un cambio di media query **butta
l'osservazione**: staccato il mouse, ricomanda il contesto.

`[M]` caso **D2**, e si legge da `body[data-disposizione]` — che lo scrive il **prodotto**:

> all'avvio **«tocco»** · dopo un DITO **«tocco»** · dopo un CLIC di mouse **«classico»** ·
> dopo un altro DITO **«tocco»**

e la spia della pagina conferma la catena vera degli eventi:
`pointerdown/touch → touchstart → pointerdown/mouse → mousedown → pointerdown/touch → touchstart`.

⛔ **E «in vigore» vuol dire che l'altra è SPENTA** (caso **D3**), provato su tre fatti: in classico
il tocco è spento e il classico acceso; dopo il gesto il classico è spento; e il trascinamento
cominciato **nell'altra** disposizione produce **zero clic fantasma**.

⚠ **Il contesto letto su CHUWI**: `any-pointer: fine` **falso**, `pointer: coarse` **vero**,
`any-hover` falso, finestra 1461×788 px CSS ⇒ **tocco**. `[?]` Resta non misurato che Chrome per
Android rivaluti `(any-pointer: fine)` quando si attacca un mouse Bluetooth a sessione aperta:
**è proprio per questo che l'evento di puntatore vero vince sulla media query.**

---

## 4. ⛔ Che cosa NON ha funzionato

| | |
|---|---|
| ⛔ **Il primo giro accusava il PRODOTTO di non tornare al tocco** | Era lo STRUMENTO. `Input.dispatchTouchEvent`, dopo una seconda `Page.navigate` e dopo un evento di mouse, **non consegna più niente alla pagina** e torna senza errore. ⭐ L'ha detto la **spia** messa nel prologo (`CODER.md` §3.7 — non si deduce, si chiede): né `touchstart` né `pointerdown` di tipo touch. ⇒ Il passaggio si misura ora in una **scheda nuova** |
| ⛔ **Il banco moriva a metà, in fasi diverse a ogni giro** | `Input.dispatchTouchEvent` scadeva. ⭐ La causa è la **scena**: la finestra finisce dietro un'altra sul desktop vero, il renderer smette di produrre quadri — lo stesso fatto che `web.md` §6.2 misura su Xvfb — e l'assenso all'evento non arriva mai. Cura: `Emulation.setFocusEmulationEnabled` + `Page.bringToFront`. **Dopo: zero guasti in due giri** |
| ⛔ **Riprovare una fase guasta la CORROMPEVA** | I byte del tentativo mezzo riuscito restavano nella fase: il giudice leggeva «tre eventi del sinistro su quattro» su un gesto fatto due volte bene. ⇒ **Un tentativo solo**, e il guasto si **dichiara** con un segno tutto suo — non verde, non rosso, «da rifare» (`CODER.md` §3.10) |
| ⛔ **Riusare l'identificatore di un contatto rilasciato blocca CDP** | Riproducibile, due giri su due, al primo `touchMove` dopo il riappoggio. ⭐ E l'identificatore nuovo è anche più fedele: un pannello tattile non ricicla il `tracking id` |
| ⛔ **Una spia NON passiva blocca il primo contatto** | Aggiunto un ascoltatore `touchstart` non passivo, il banco si fermava al primo gesto. Una spia che cambia quel che misura non è una spia |
| ⛔ **`allow_reuse_address` scritto DOPO la costruzione non ha nessun effetto** | `TCPServer.__init__` lega la porta subito. Sintomo: «Address already in use» col porto che `ss` dichiara libero. ⚠ **Lo stesso difetto è in `banchi/04-b27-classico.py`** |
| ⚠ **G6 misurava lo strumento** | Con 80 ms di attesa il tap a tre dita usciva senza clic: `durata_max` **147 ms** su 180, perché sei andate-e-ritorni CDP costano ~120 ms da sole (`LEZIONI.md` §1.11) |
| ⚠ **Il primo controllo D4 era rosso su un proprio COMMENTO** | Cercava `userAgent` e trovava la riga che diceva «qui non compare `navigator.userAgent`». Un controllo che legge le proprie spiegazioni misura la prosa |
| ⚠ **Ripieghi dichiarati che restano** | il **puntatore di ripiego** è un elemento **sopra la tela** (`web.md` S4: fa cadere il percorso overlay e la tela desincronizzata) — vale finché la cucitura non regge; il **pizzico** ingrandisce con una trasformazione CSS, che **ricampiona**: l'ingrandimento vero va dentro `componi()`, che non è mio |
| `[?]` **Non misurato** | il verso dell'asse **orizzontale** della rotella (`RCP.md` non lo fissa) · la Keyboard Lock su DeX · il comportamento di una **mano vera** su qualunque soglia di §3.2 |

---

## 5. Le cuciture che chiedo — con la firma esatta

### ⛔⛔ 5.1 LA CUCITURA ROTTA, ed è l'unico rosso del banco — **cura di UNA riga, e non è mia**

⭐ È esattamente il difetto della fase 3 (`fasi/rapporti/F5-desktop-vero.md`): *due pezzi corretti
per conto loro, e il risultato uno schermo vuoto.* L'ho trovato leggendo l'ancora di A7 **prima**
di scrivere, e il banco lo misura.

`REMOTIX_PUNTATORE.muovi()` (ancora `F4-INPUT-CLASSICO`) scrive la posizione e ridisegna, ma
**non accende `cl_noto`** — che è il flag che `cl_disegna()` guarda per decidere se il puntatore si
vede. ⇒ Su una pagina che nasce **in disposizione a tocco** e non entra mai nel classico,
⛔ **il puntatore non compare mai: il dito trascina qualcosa di invisibile.**

```js
/* ancora F4-INPUT-CLASSICO, anello A7 */
muovi: function (x, y) { cl_px = x; cl_py = y; cl_noto = true; cl_satura(); cl_disegna(); },
```

⚠ Finché non c'è, l'ancora `F4-TOCCO` **verifica la cucitura una volta sola** e, se è rotta,
**dichiara nel registro** e ripiega sul proprio puntatore — quindi l'utente vede comunque una
freccia (caso **S1a**, verde). Appena la riga di sopra c'è, il controllo passa e il ripiego non
nasce nemmeno: **non ci saranno mai due frecce.**

### 5.2 Le due cuciture che ho assunto — e che **combaciano** con quelle di A7

| Firma | Stato |
|---|---|
| `window.REMOTIX_CLASSICO = { entra(perche: string): void, esci(): void }` | ✅ **cucita** — A7 la espone identica (caso **S2**, verde). La chiamo io: il passaggio automatico è mio |
| `window.REMOTIX_PUNTATORE = { muovi(x_tela, y_tela): void, mostra(): void, nascondi(): void }` | ✅ esposta da A7, ⛔ **con il difetto di §5.1**. Le coordinate sono quelle della **TELA**, non della vista: è l'unico riferimento che tocco e classico hanno in comune |

### 5.3 ⛔ La cucitura che manca ancora — è del coordinatore, e tocca il filo

```js
window.REMOTIX_INPUT = {
  prossimo_id(): number,                        // §7.3
  manda(tipo: number, corpo: Uint8Array): void  // corpo INTERO, id e istante compresi
}
```

⛔ **Il contatore dev'essere UNO SOLO per tocco e classico insieme**: `RCP.md` §7.3 dice che l'id
cresce di almeno uno *su tutto il canale*, non uno per tipo, ed è quello che torna nel campo
`input` dei fotogrammi (§6.2). Con due contatori separati **non tornerebbe niente**.
⚠ È la stessa firma che chiede A7, parola per parola, e il banco la mette da fuori
(`window.REMOTIX_INPUT`, prologo di `04-b28-gesti.py`) mandando i byte a sé stesso.
⚠ Finché non c'è, i messaggi si costruiscono, si numerano con un contatore locale e **non
partono**: restano in `REMOTIX.tocco.spediti`.

### 5.4 Quel che l'ancora `F4-TOCCO` espone da leggere

`REMOTIX.tocco = { soglie, spediti, contesto(), disposizione(), perche(), rivaluta(), stato() }`
— ⚠ oggetti **da leggere** (invariante I6): `rivaluta()` non impone niente, ricalcola dal contesto.
E `document.body.dataset.disposizione` (`"tocco"` | `"classico"`) è **il metro del banco**: la
disposizione in vigore si legge dal documento, non da una funzione che dice di cambiarla.
La via di servizio `?disposizione=tocco|classico` è per il banco e la diagnosi, **non**
un'impostazione dell'interfaccia, e si dichiara nel registro quando è in vigore.
