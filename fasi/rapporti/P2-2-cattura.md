# P2.2 — La cattura, il PRODOTTO

*Secondo anello della fase 2. Il banco sta in [`F2-2-cattura.md`](F2-2-cattura.md), ed era stato
scritto **prima** di questo codice e certificato lo stesso giorno.
Porta assegnata: **7512** — e nemmeno questo giro ne apre una.*

Scritto il **12 agosto 2026**.

---

## Che cosa ho portato, e che cosa ho lasciato

| file | righe | che cos'è |
|---|---|---|
| `src/cattura.h` + `src/cattura.c` | 300 + 780 | il consumatore PipeWire: **un fotogramma in memoria con il tipo di buffer dichiarato** |
| `src/mutter.h` + `src/mutter.c` | 140 + 430 | la sequenza D-Bus che monta il monitor virtuale e apre il flusso |
| `banchi/02-cattura-prodotto.c` | 560 | ⭐ lo **stesso** produttore del banco, ma la cattura la fa il PRODOTTO |
| `banchi/02-cattura-costruisci.sh` | 150 | la costruzione, con le stesse opzioni del `Makefile` |

⛔ **Non ho toccato `src/Makefile` né `src/main.c`** (le righe esatte stanno più sotto), e non ho
toccato niente altro in `src/`.

### Che cosa di v1 **non** è entrato — e la ragione, una per riga

*Il mandato dice «non ricopiare quel che non serve». Delle 1060 righe di `v1/…/cattura.c` ne
sopravvivono le tre regole e nessuna delle strutture.*

| lasciato fuori | perché |
|---|---|
| `cattura_dmabuf()` — girare la strada **a cattura viva** | esisteva perché **AVC420 si codifica in GPU e RemoteFX in CPU**, e quale dei due si spedisse si sapeva solo al `CapsAdvertise` di RDP. ⛔ In V2 non c'è RDP e non c'è quel bivio: la strada si dichiara all'avvio |
| `cattura_ridimensiona()` + `misura_negoziabile` | è la risoluzione dinamica della **fase 6** e il ramo KWin 6.8 della **fase 11** (KDE). Portarlo adesso vuol dire mantenere per due mesi un codice che nessuno esegue |
| `REMOTIX_MISURA_INTERVALLO`, `REMOTIX_FENCE_MS`, `REMOTIX_FOTO` | tre interruttori d'ambiente per esperimenti chiusi. ⚠ E l'invariante **I7**: una protezione che vive in una variabile d'ambiente si perde |
| l'attesa della **fence** (`poll` sul DMA-BUF) | serve a chi **importa** il buffer sulla scheda, cioè alla fase 8. Qui la strada della scheda si dichiara e non si legge |
| `superficie.c` (675) | l'import sulla scheda: fase 8. F2.2 vuole i pixel **leggibili** |
| `palco.c` (1545) | vedi il riquadro «la copia zero spenta su GNOME» |
| `ConnectToEIS` in `mutter.c` | è l'input, cioè la **fase 4**. ⭐ Il punto esatto della sequenza in cui va infilato è scritto nel codice, con la ragione: fra `CreateSession` e `Start` |

⭐ **Quel che invece è stato riportato riga per riga** è la sequenza D-Bus di `mutter.h` con le due
punizioni scritte accanto a ogni passo, e le tre regole di `cattura.h`: **lo stride si legge**, **il
tipo di buffer si chiede in due posti**, **la cadenza si dichiara a zero**.

---

## ⛔ I quattro fatti che dichiaro a valle

*Non sono un commento: sono `CatturaConsegna`, una struttura che chi sta a valle **legge**. Ogni
campo ha accanto il campo «chi lo dice», e i valori qui sotto sono `[M]` del 12 agosto 2026,
NIC-OS, Mutter 48.7 headless, scena «bandiera», monitor `Meta-1`.*

| # | il fatto | il valore `[M]` | chi lo dice |
|---|---|---|---|
| **1** | **tipo di buffer** | **MemFd** sulla strada della memoria · **DMA-BUF** su quella della scheda | `spa_data.type` del piano 0. ⛔ E **chiesto** e **dichiarato** sono due campi diversi |
| **2** | **bit per canale** | **8** | il formato negoziato (**BGRx**). ⛔ 0 se il formato è ignoto — mai un numero inventato |
| **3** | **geometria** | 1920×1080, **stride 7680 LETTO dal chunk**, **8 294 400 byte** | `chunk->stride`. ⛔ `stride_letto = FALSE` finché un fotogramma non è arrivato: prima non è un fatto |
| **4** | **colore** | range · matrice · trasferimento · primari: **NON DICHIARATI dal produttore** (i quattro zeri di SPA) | `spa_video_info_raw`, chiesto a lui |

⭐ **E il quarto fatto ha una seconda metà, perché quattro «non dichiarato» non bastano a chi deve
codificare**: il range **lo misura il prodotto** sui pixel che ha in mano, e lo scrive **come
misura**. `[M]` sul fotogramma di regime: **min 0 / max 255 su tutti e tre i canali ⇒ compatibile
con il PIENO**.

⛔ **E ci sono due sole risposte, non tre**: `COMPATIBILE_PIENO` e `NON CONCLUSIVO`. Non esiste
`LIMITATO`, e non per dimenticanza: ⚠ una scena che non porta il nero e il bianco pieni non arriva
agli estremi, e **questo non proverebbe un range limitato — proverebbe solo quella scena**. La
misura di oggi vale perché la scena «bandiera» porta apposta i due estremi.

⚠ **Sulla matrice la risposta onesta resta che alla cattura non ce n'è una**: i pixel sono RGB, e
nessuna conversione è stata applicata da noi. La sceglie F2.3, e F2.6 deve confrontare con la
stessa — *un confronto di pixel fatto con la matrice sbagliata misura la matrice*.

### ⭐ E un quinto fatto che nessuno aveva chiesto: **il fotogramma nero**

`misura_i_pixel()` gira sul thread di chi chiama (⛔ non dentro la richiamata di tempo reale) e nello
stesso passaggio che misura il range risponde a due domande: **è nero?** e **è uniforme?**

⛔ **E il prodotto non rifiuta: dichiara.** Un desktop può legittimamente essere nero, e rifiutarlo
sarebbe decidere al posto dell'utente; tacerlo sarebbe consegnare il nulla senza una riga. Quando il
massimo è 0 su tutti e tre i canali il registro dice:

```
⛔ il fotogramma consegnato e' NERO (massimo 0 su tutti e tre i canali): e' quel che
   consegna una sessione senza monitor virtuale — STUDI.md §gnome §3.1, guasto M9
```

⚠ E «nero» e «uniforme» sono **due marche diverse**, per la stessa ragione per cui lo sono nel
giudice del banco: un grigio uniforme chiamato nero manda a cercare il difetto dalla parte sbagliata.

---

## ⛔ E1, pagata due volte, e come questo codice la para

*«consegna MemFd ⇒ è in software» e «ha aperto un render node ⇒ rende in GPU» sono **due errori**.*

Il tipo di buffer qui **si chiede e si dichiara**, in tre campi separati (`buffer_chiesto`,
`buffer_dichiarato`, e il nome di chi lo dice), e la riga che il prodotto scrive nel registro porta
l'avvertenza **dentro di sé**, non in un documento:

```
i fotogrammi arrivano come MemFd (1 piani) — ⚠ e questo NON dice dove Mutter renda:
e' la risposta a quel che abbiamo chiesto noi (E1)
```

⛔ **E la strada si verifica, non si dà per chiesta**: se si chiede la scheda e arriva la memoria (o
viceversa) `cattura_prendi` **fallisce dichiarandolo** invece di ripiegare in silenzio. E la proposta
è **una sola**: offrirne due — con e senza modificatori — sarebbe un ripiego, e un ripiego silenzioso
produce due comportamenti sotto la stessa etichetta.

---

## ⛔ La copia zero spenta su GNOME: la ragione è morta, la decisione no

`v1/remotix-c/src/palco.c:598-628` tiene la copia zero **spenta su GNOME**, e la ragione scritta lì è
*«il buffer che Mutter presta non è un fotogramma intero, è un diff»*.

⭐ **Quella ragione è smentita da due strade indipendenti**: `STUDI.md` §gnome §8.1 `[R]` (blit dell'intero
framebuffer, stack di clip svuotato deliberatamente) e la misura di F2.2 `[M]` (danno **parziale** su
410 fotogrammi su 410, e le sette bande **intere**). Oggi il mio giro lo conferma una terza volta:
**388 fotogrammi, danno parziale su tutti, scena intera.**

⚠ **Ma «la ragione è morta» non è «la copia zero va accesa»**, e le due frasi vanno tenute separate:

| | |
|---|---|
| ⛔ quel che **cade** | il motivo scritto in `palco.c`: il diff non esiste |
| ⚠ quel che **non** discende | che la copia zero su GNOME convenga. I **59 contro 43,3** sono di **KWin** (`STUDI.md` §kde §5.7), e su GNOME il ritmo in memoria **non è mai stato misurato**: la fase 0 dà 36 ± 2 **sulla strada DMA-BUF** |
| ⛔ quel che V2 fa oggi | la strada la **dichiara chi chiama**, e la fase 2 chiede la **memoria** per una ragione sua e scritta: **vuole i pixel leggibili**. Non è più un predefinito ereditato da un difetto |

⇒ La decisione «quale strada su GNOME» diventa una misura di **ritmo**, e il ritmo non è di questo
anello: è della fase 3, e ora ha due strade tutt'e due funzionanti su cui girare.

---

## ⭐⭐ La `[?]` dei dieci bit, chiusa con una misura — su tutt'e due le strade

*Il mandato: «DMA-BUF è l'unica strada su cui i 10 bit possono ancora esistere». Ho chiesto tutt'e
due le cose al compositore invece di dedurle.*

### 1. La strada DMA-BUF **esiste**, ed è la prima volta che qualcuno la percorre su questo banco

`[M]` 12 agosto 2026, `STRADA=dmabuf`, scena «bandiera», monitor `Meta-1`:

| | |
|---|---|
| tipo di buffer dichiarato | ⭐ **DMA-BUF** — chiesto in due posti e **ottenuto** |
| fotogrammi | **388** (44 prima della scena, 344 dopo) |
| buffer distinti riciclati | **4** |
| formato negoziato | ⛔ **BGRx — 8 bit per canale** |
| modificatore | **0x0**, cioè `DRM_FORMAT_MOD_LINEAR` (⭐ è esattamente quello che la fase 8 vorrà) |
| stride | **7680**, ⭐ **letto dal chunk anche qui**: sulla scheda i pixel non sono nostri, lo stride sì |
| danno | parziale su 388 su 388 |
| verdetto del giudice | **uscita 3 — «SOLO IL TIPO»**: i pixel non si leggono da qui, e non è un rosso |

### 2. I dieci bit, **chiesti** — e il rifiuto è un rifiuto

Il prodotto sa chiedere `xBGR_210LE`, `xRGB_210LE`, `ABGR_210LE`, `ARGB_210LE`, e li chiede **da
soli**: ⛔ mettere BGRx nello stesso elenco avrebbe fatto negoziare BGRx e non si sarebbe imparato
niente.

| # | che cosa ho chiesto | risposta di Mutter `[M]` |
|---|---|---|
| **A** | ⭐ **controllo positivo**: BGRx, memoria, **stesso binario, stessa sequenza** | formato negoziato, flusso **attivo**, fotogrammi MemFd |
| **B** | 10 bit, strada **memoria** | ⛔ **`no more input formats`** — il flusso non diventa mai attivo |
| **C** | 10 bit, strada **scheda** | ⛔ **`no more input formats`** — identico |

⭐ **La `[?]` è chiusa, e non per deduzione**: da questa sorgente **dieci bit veri non escono, né via
MemFd né via DMA-BUF**. La lettura del codice e la misura concordano — `STUDI.md` §gnome §8.3 `[R]`,
`supported_formats[]` in `meta-screen-cast-stream-src.c` di Mutter 48.7 ha **due voci**, BGRx e BGRA,
e la stessa tabella alimenta **anche** l'elenco con i modificatori.

⇒ ⛔ **F2.3-A non è un rischio, è una certezza, e l'imputato è la cattura**: un Main10 alimentato da
qui porta **8 bit promossi a 10**. Il desiderato di `SPECIFICHE.md` §3.1 **non è raggiungibile dalla
sorgente GNOME**, su nessuna delle due strade, e la promozione va **dichiarata** e non subita.

⚠ **E quel che questo NON chiude**: che *nessun* compositore dia dieci bit. È misurato su **Mutter
48.7**. KWin e wlroots non sono stati chiesti — è la fase di KDE (la 11), e la domanda adesso ha un metodo.

### 3. E la `[?]` che resta aperta, dichiarata invece che assolta

⛔ **Il buffer della scheda sbagliata.** La macchina ha due GPU (Intel `00:02.0`, Radeon `03:00.0`),
e il sintomo è composizione in software **senza un errore da nessuna parte**. ⚠ Oggi so **di più** di
ieri — il modificatore negoziato è LINEAR, e `[R]` Mutter offre una proposta con modificatori **solo
se la scheda gliene dà** (`meta_screen_cast_query_modifiers`: lista vuota ⇒ quel formato entra solo
nell'elenco senza modificatori) — ⛔ **ma «ho ricevuto un DMA-BUF» non è «lo saprei importare»**: chi
importa è la fase 8, e finché nessuno lo importa la trappola 6 **non è stata guardata da nessuno**.

---

## Il banco contro il mio codice

⭐ **Il banco non è stato riscritto, e nemmeno il giudice**: `banchi/02-cattura-prodotto.c` presenta
la **stessa riga di comando**, scrive lo **stesso manifesto** e gli **stessi due `.raw`**, con gli
**stessi quattro stati d'uscita** — ma la cattura la fanno `src/cattura.c` e `src/mutter.c`.
`02-cattura-giudica.py` e `02-cattura-certifica.sh` **non sono cambiati di una riga**: giudicano i
pixel, e non sanno chi li ha fatti.

⛔ **E la ragione per cui questo era obbligatorio**: il banco del 12 agosto certificava il produttore
scritto **dentro di sé**, perché il prodotto non esisteva. Quel verde non diceva niente sul prodotto
(`LEZIONI.md` §1.3).

L'unica modifica al banco: in `02-cattura-lancia.sh`, `PROG` e `FONTE` diventano `${…:-}`, cioè si
possono dichiarare. ⭐ **E i due produttori restano tutt'e due**, perché insieme sono un controllo
positivo che nessuno dei due sarebbe da solo.

### La certificazione, girata contro il prodotto

**Comando**, con la guardia della sessione davanti:

```
bash banchi/02-sessione-guardia.sh --etichetta P2.2-certifica -- \
  env PROG=…/02-cattura-prodotto FONTE=…/02-cattura-prodotto.c \
      bash /media/REMOTIX/src/02-cattura-certifica.sh
```

`[M]` 12 agosto 2026, NIC-OS, sessione GNOME headless, scena «bandiera», monitor `Meta-1`:

| | esito |
|---|---|
| **sano** | **0** — VERDE: 1920×1080 BGRx MemFd, la scena si vede, il regime è distinto dal primo |
| **G1 nero** | **1**, marca `FOTOGRAMMA NERO` |
| **G2 grigio** | **1**, marche `FOTOGRAMMA UNIFORME` + `SCENA NON RICONOSCIUTA`, ⛔ **vietata assente** |
| **G3 troncato** | **1**, marca `BYTE NON TORNANO` |
| **G4 copia** | **1**, marca `IL BUFFER NON È CAMBIATO`, ⛔ **vietata assente** |
| **risanato** | **0** dopo ognuno, impronta tornata a `82270430…afad6a` ogni volta |

⭐ **CERTIFICATO: `sano 0 → quattro guasti 1 → risanato 0`** — e questa volta a essere certificato è
**il prodotto**, non una sua copia.

⚠ **E non dice che il prodotto sia giusto**: dice che il banco sa vedere **questi quattro** difetti
su di lui. «Non ho trovato niente» non è «è giusto» (`REVIEWER.md` §0).

**I numeri del giro sano** `[M]`: 386-395 fotogrammi arrivati (43-44 prima della scena), **MemFd**, 4
buffer riciclati, **stride 7680**, **8 294 400 byte**, danno **parziale su tutti**, sfumatura
**255/256/255 livelli distinti** e multipli di 4 a **0,259 / 0,259 / 0,249** ⇒ ⭐ **otto bit veri,
tutti e otto**, e le sette bande riconosciute.

---

## ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura. Qui sono **quattro**, e tre le ha trovate il banco
girando — non una rilettura.*

### 1. ⭐ Il monitor virtuale **non esiste** quando lo si chiede — e il mio codice lo dichiarava rotto

`mutter.c` cerca il nome del nostro schermo con **due strade che devono concordare** (il diff dei
connettori, e il nome del prodotto). Al primo giro contro il banco ha scritto:

```
⚠ dopo il montaggio sono comparsi 0 monitor nuovi invece di 1 (1 prima, 1 dopo)
```

su una sessione **perfettamente sana** — mentre lo script del banco, un istante dopo, trovava
`Meta-1` senza fatica. ⛔ Un rosso su un banco sano, cioè la voce 2 di `fasi/00-ambiente.md`.

**La causa, misurata in tre punti** `[M]`:

| quando | il monitor c'è? |
|---|---|
| appena `RecordVirtual` ritorna | ⛔ **no** |
| dopo `Stream.Start`, **anche aspettando tre secondi** | ⛔ **no** |
| quando il **consumatore** si è agganciato e il flusso è attivo | ⭐ **sì** — `Meta-1` / «Virtual remote monitor» |

⇒ **Mutter crea il monitor virtuale quando qualcuno comincia davvero a leggere**, non quando glielo
si chiede. La cura non è un'attesa più lunga: è che il nome **si chiede quando serve**
(`mutter_monitor_cerca`, chiamata a flusso attivo) — ed è anche il momento giusto, perché la scena si
apre **dopo**, e va mandata su quello schermo per nome.

⚠ E la prima cura che avevo scritto — «aspetta fino a tre secondi dopo `Stream.Start`» — era
**sbagliata e sarebbe passata**: avrebbe rallentato ogni montaggio di tre secondi e avrebbe continuato
a dichiarare di non sapere.

### 2. ⛔ Un argomento non capito, letto come «il produttore non parte»

Il primo giro vero è uscito **2** con la riga d'uso stampata: mancava `--etichetta` nel mio
interprete degli argomenti. Da fuori aveva l'aspetto di un produttore che non si avvia.

⚠ È `fasi/00-ambiente.md` **B3 punto 2** — *un'opzione rifiutata non è un difetto del bersaglio* —
pagata di nuovo. ⭐ **La cura non è aver aggiunto l'opzione**: è che adesso il programma **dice quale
argomento non ha capito**, così la prossima volta la diagnosi costa dieci secondi invece di un giro.

### 3. ⛔ Ho fatto io una redirezione **attorno** a `enter.sh`, e il comando è restato appeso

```
sshpw.py "bash …/02-cattura-costruisci.sh > …/costr2.txt 2>&1"
```

La redirezione sta attorno al comando che dentro chiama `enter.sh`, quindi la richiesta di parola
d'ordine di `sudo` — che va sullo stderr — è finita nel file. `sudo -v -S -p` è restato in attesa **in
silenzio** finché non l'ho ucciso.

⚠ È `fasi/00-ambiente.md` **B3.3**, pagata **cinque volte prima di me**, ed è la sesta. È nominata a
lettere intere nel mandato che avevo letto un'ora prima, ⛔ **ed è scritta a lettere intere anche in
testa allo script che stavo lanciando, scritto da me un'ora prima.** La forma non è «ricordarsela»:
la protezione deve stare in un programma, e qui non c'è — chi digita il comando la può sempre
rifare.

### 4. ⚠ Ho misurato su una sessione che un altro banco stava tenendo NERA di proposito

La guardia ha rifiutato con **verdetto 5** e le due domande separate: *viva* sì, *monitor* **zero**.
⛔ La prima reazione giusta sarebbe stata rimettere la sessione con `02-sessione-lancia.sh sano`; ho
guardato **chi** ci fosse dietro prima di farlo, e c'era un altro agente che stava eseguendo la
propria **scena guasta dichiarata** (`02-sessione-costruisci.sh scena-nera`).

⭐ **Aspettare invece di curare era la risposta giusta**, e l'ho saputo perché ho chiesto al nucleo
chi tenesse quello stato invece di dedurlo (`CODER.md` §3.7). ⚠ E la lezione per i giri in parallelo:
**la sessione grafica è un bene condiviso senza un lucchetto che lo dica a chi passa** — la 7511 è il
lucchetto di chi la cicla, ma chi *misura* non lo prende e non lo guarda.

---

## Le `[?]` che lascio

| `[?]` | perché resta aperta |
|---|---|
| ⛔ **il buffer della scheda sbagliata** | due GPU, e il sintomo non dà errori. Ricevere un DMA-BUF non è saperlo importare: la prova è della fase 8 |
| ⛔ **il ritmo sulle due strade di GNOME** | questo prodotto **non lo misura e non deve** (copia dentro la richiamata di tempo reale). Resta 36 ± 2 `[M]` su DMA-BUF, e **niente** sulla memoria |
| ⚠ **il fotogramma di regime è identico byte per byte fra i giri** | ⭐ `[M]`: **cinque giri, due produttori indipendenti e due istanti di presa diversi** danno lo stesso `sha256 82270430…`. Il blocco bianco misurato sta a x 346-878 sulle righe 960-1060, e il suo periodo è `1760/720 = 2,444 s`: le prese cadono su **fasi congruenti**, e mpv nel suo registro dichiara di aver suonato fino a 10 s. ⛔ Non lo spiego fino in fondo: lo dichiaro, ed è **un regalo per F2.6** (il riferimento è stabile) e **una trappola per chi contasse su di esso** (il banco non confronta mai due fotogrammi di regime fra loro: una scena congelata passerebbe) |
| ⚠ **il danno «parziale» anche sul primo fotogramma** | 388 su 388 anche qui, come F2.2. Non lo spiego |
| ⚠ **`cattura_prendi` prende il PROSSIMO fotogramma** | i fotogrammi che arrivano mentre nessuno aspetta si contano e basta. Per un'immagine ferma è quel che serve; ⛔ per la fase 3 il consumo va per richiamata, ed è l'altra porta di questo modulo — **mai eseguita**, perché in fase 2 nessuno la chiama |

---

## Le cuciture

### A **F2.3** (la codifica) — quel che trova, e come lo legge

```c
CatturaConsegna c;
if (!cattura_consegna(cattura, &c))   /* FALSE = «non lo so ancora», non «è zero» */
        …;
c.bit_per_canale        /* 8  — dal formato negoziato, 0 se ignoto */
c.formato               /* "BGRx" */
c.range_grezzo          /* 0 = NON DICHIARATO: è una risposta */
```

e dal fotogramma, **non ricalcolati**:

```c
CatturaFermo f;
switch (cattura_prendi(cattura, 5.0, &f, &sbaglio)) { … }
f.stride                /* 7680 — ⛔ LETTO, mai larghezza×4 */
f.byte                  /* 8 294 400 */
f.consegna.range_misurato   /* CATTURA_RANGE_COMPATIBILE_PIENO [M] */
f.consegna.nero             /* ⛔ e se è vero, l'immagine è il nulla */
```

⛔ **E la riga che F2.3 deve avere sotto gli occhi**: **8 bit, misurati e chiesti su due strade.** Un
Main10 da qui è una promozione, e va dichiarata.

### A **F2.1** (la sessione)

1. ⭐ **Il monitor virtuale della cattura adesso lo monta il programma** (`RecordVirtual` dentro
   `mutter_apri`): l'invariante **I7** che `v1/…/sessione.c:671` violava è rispettato **dal
   prodotto**. ⚠ Resta vero che la sessione ha bisogno del **suo** monitor per non essere nera.
2. ⛔ **Chi apre una finestra sul nostro schermo lo deve chiamare per nome**, e il nome lo dà
   `mutter_monitor_nostro()` — **solo a flusso attivo**. Prima non esiste, ed è misurato.

### A **F2.4 / F2.5 / F2.6**

| a chi | che cosa |
|---|---|
| **F2.4** | il fotogramma è **8,3 MB non compressi**, righe da **7680 byte**: la misura del messaggio la decide F2.3 |
| **F2.6** | ⭐ il `.raw` catturato è su disco, e **si riproduce byte per byte fra i giri** `[M]`: il confronto si fa contro **quello**, non contro l'MP4 della scena |
| **F2.6** | ⛔ se i pixel non tornassero, **la matrice è la prima sospetta**: la cattura è RGB e non ne applica nessuna |

---

## ⛔ Le righe per il `Makefile` e per `main.c` — da innestare, non le ho scritte io

*Quattro agenti scrivono gli altri anelli adesso: due che toccassero il `Makefile` si
cancellerebbero a vicenda.*

### `src/Makefile`

**1.** la riga `SORGENTI` diventa:

```make
SORGENTI := main.c trasporto.c webtransport.c pagina.c comando.c certificati.c \
            tls.c registro.c rcp.c autenticazione.c aiutante.c cattura.c mutter.c
```

**2.** subito dopo il blocco `LIBS := …`:

```make
# ⛔ LE TRE DIPENDENZE DELLA CATTURA, DICHIARATE (LEZIONI.md §2.5-bis):
#   libpipewire-0.3   il flusso dei fotogrammi        (src/cattura.h)
#   gio-2.0           il bus di sessione di Mutter    (src/mutter.h)
#   libdrm            i DRM_FORMAT_MOD_*: solo intestazioni, nessuna libreria
# Su Debian Trixie: libpipewire-0.3-dev, libglib2.0-dev, libdrm-dev.
CATTURA_CFLAGS := $(shell pkg-config --cflags libpipewire-0.3 gio-2.0 libdrm)
CATTURA_LIBS   := $(shell pkg-config --libs libpipewire-0.3 gio-2.0)
override CFLAGS += $(CATTURA_CFLAGS)
LIBS += $(CATTURA_LIBS)
```

**3.** nel bersaglio `dipendenze`, l'elenco delle intestazioni diventa:

```make
	for h in ngtcp2/ngtcp2.h ngtcp2/ngtcp2_crypto_ossl.h nghttp3/nghttp3.h \
	         openssl/ssl.h security/pam_appl.h \
	         pipewire/pipewire.h gio/gio.h drm_fourcc.h; do \
```

**4.** in fondo, accanto alle altre:

```make
cattura.o:        cattura.h registro.h
mutter.o:         mutter.h registro.h
```

⚠ `cattura.c` e `mutter.c` **non** vanno fra i `GEMELLATI`: non esistono in `banchi/rcp/`.

### `src/main.c` — il montaggio del palco, quando la fase 2 lo vorrà

⛔ **Non c'è ancora nessuno che chieda un fotogramma**: la codifica è di F2.3 e il filo di F2.4.
Queste sono le righe **esatte** del montaggio, e vanno dove il server monta la sessione dell'utente
**dopo** l'autenticazione (I3: la guardia parte da negato).

```c
#include "cattura.h"
#include "mutter.h"
```

```c
	MutterSessione *sessione = mutter_apri(&sbaglio);
	if (!sessione)
		return …;   /* ⛔ e si dichiara: senza monitor virtuale non c'è niente da catturare */

	Cattura *cattura = cattura_avvia(mutter_nodo(sessione), 1920, 1080, 60,
	                                 CATTURA_STRADA_MEMORIA, CATTURA_COLORE_BGRX,
	                                 NULL, NULL, NULL, &sbaglio);

	/* ⛔ SOLO ADESSO il monitor esiste, ed è misurato: chi aprirà una finestra
	 *    su questo schermo lo deve chiamare per nome. */
	mutter_monitor_cerca(sessione);

	CatturaFermo f;
	switch (cattura_prendi(cattura, 5.0, &f, &sbaglio))
	{
	case CATTURA_PRESA_FATTA:        /* f.pixel, f.stride, f.consegna: a F2.3 */
	case CATTURA_PRESA_ZERO:         /* ⭐ desktop fermo: è un risultato        */
	case CATTURA_PRESA_PIXEL_ALTROVE:/* strada della scheda: fase 8            */
	case CATTURA_PRESA_GUASTO:       /* ⛔ e questo NON è uno zero              */
		break;
	}
	cattura_fermo_libera(&f);
	cattura_ferma(cattura);
	mutter_chiudi(sessione);
```

---

## Lo stato del terreno, contato prima e dopo

| | prima | dopo |
|---|---|---|
| ascoltatori su **7448** e **7501** | **2** | ⭐ **2** — intatte |
| sessione GNOME | sana (`Meta-0` / MetaVirtualMonitor) | sana, guardia 0 prima **e** dopo ogni giro |

### Le certificazioni che questo giro fa scadere

⛔ *«Scaduta» non è «fallita», e non è nemmeno «pulita».*

| | |
|---|---|
| **nessuna** certificazione di prodotto | il binario `remotix` **non è stato ricostruito**: `cattura.c` e `mutter.c` non entrano nel `Makefile` finché il coordinatore non innesta le righe qui sopra. I due server sulla 7448 e sulla 7501 girano sullo stesso binario di prima |
| ⚠ **`attrezzi-allinea-prodotto.sh guarda` dice ROSSO**, e ha ragione | «il binario è **più vecchio** di: cattura.h mutter.c mutter.h cattura.c …». È il fatto vero, e si risolve **con l'innesto**, non prima. ⚠ Nella stessa lista ci sono `codificatore.*` e `sessione.*`: sono di altri due agenti, non miei |
| ⭐ **la certificazione di F2.2 è stata RIFATTA**, non invalidata | il banco è lo stesso, il giudice è lo stesso, ed è stato girato **contro il prodotto**: `0 → 1×4 → 0` |

### La riga per il catalogo delle certificazioni

```
nome            P2.2 — la cattura, il PRODOTTO
comando         bash banchi/02-sessione-guardia.sh --etichetta P2.2 -- \
                  env PROG=/media/REMOTIX/tmp/02-cattura/02-cattura-prodotto \
                      FONTE=/media/REMOTIX/src/02-cattura-prodotto.c \
                      bash /media/REMOTIX/src/02-cattura-certifica.sh
costruzione     bash /media/REMOTIX/src/02-cattura-costruisci.sh
atteso sano     0   VERDE: 1920×1080 BGRx MemFd con dentro la scena dichiarata,
                    prodotto da src/cattura.c + src/mutter.c
guasti          nero · grigio · troncato · copia — innestati nel .raw, mai nel codice
atteso guasto   1   ciascuno, con la marca PRETESA e quella VIETATA
atteso risanato 0   dopo ognuno, impronta 82270430c1823ff113a3f4627fbd8b61350e9cf1
                    9d2962cda643fc1d19afad6a
costa           una presa da 12 s per il giro sano; i guasti sono copie di file
esito           ⭐ [M] 12 agosto 2026, NIC-OS: 0 → 1 ×4 → 0. CERTIFICATO
riferimento     fasi/rapporti/P2-2-cattura.md · F2-2-cattura.md · STUDI.md §gnome §8.1 §8.3 §13 M9 ·
                LEZIONI.md §1.9 §1.11 §4 trappole 1, 2, 6, 8 · REVIEWER.md E1, E2, E8, E9 ·
                fasi/00-ambiente.md B3, voci 2, 8, 12-bis
```

---

## ⛔ I due riferimenti che questo giro fa invecchiare, e che non sono miei da correggere

*`CODER.md` §0: un riferimento che invecchia in silenzio è peggio di nessun riferimento. Le righe
sostitutive sono scritte qui, pronte da innestare.*

1. **`fasi/rapporti/F2-2-cattura.md`**, tabella «Le `[?]` da misurare», prima riga — *«la strada
   DMA-BUF non è stata provata da questo banco»*. ⛔ **Provata il 12 agosto 2026 dal prodotto**: 388
   fotogrammi DMA-BUF, modificatore LINEAR, formato BGRx a 8 bit, stride 7680, 4 buffer riciclati.
   Vedi `P2-2-cattura.md`.
2. **`fasi/02-primo-fotogramma.md`**, «Che cosa resta `[?]`», riga *«i 10 bit veri … restano possibili
   solo per via DMA-BUF, non provata»*. ⛔ **Chiusa**: i formati a 10 bit sono **rifiutati da Mutter
   su tutt'e due le strade** con `no more input formats`, con il controllo positivo BGRx accanto. I
   dieci bit **non esistono da questa sorgente**.

---

## Il giudizio dell'utente

⏳ Non ancora dato, e questa sotto-fase non si chiude senza (I8).

⚠ La cosa da mettergli davanti non è questa tabella: è **il fotogramma**, e adesso è uscito dal
prodotto. Sta in `/media/REMOTIX/tmp/02-cattura/giro-*-regime.raw` — 1920×1080 BGRx, 8 294 400 byte,
e si guarda così:

```
ffmpeg -f rawvideo -pix_fmt bgra -s 1920x1080 -i giro-…-regime.raw -frames:v 1 fotogramma.png
```
