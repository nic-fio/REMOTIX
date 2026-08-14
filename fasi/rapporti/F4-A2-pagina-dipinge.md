# A2 — La pagina che dipinge

*Anello A2 della fase 4, 14 agosto 2026. Due tesi da refutare, e **tutt'e due sono cadute**.*

> ## ⛔⛔⛔ IN DUE RIGHE, E NON SONO QUELLE CHE MI ASPETTAVO
>
> **1.** ⭐ **Il browser dell'utente DIPINGE HEVC** — anche il flusso esatto che il prodotto manda.
> E nella sessione del nero il server **non ha consegnato UN fotogramma**: `[M]` il contatore entra
> a 1748 ed esce a 1748, per 2 min 38 s. ⇒ *Il nero non è «consegnati e non dipinti»: è **niente
> consegnato**, ed è il monitor vuoto di §0-quater — lavoro di **A1**.*
>
> **2.** ⭐ **Il disegno costa 2,25 ms, non 28,0.** I 28 sono `[M]` il **trasferimento GPU→CPU che
> il banco della fase 3 provoca con la propria rilettura dei pixel**, riscosso una colonna più in
> là — su HEVC soltanto, perché è l'unico codec i cui fotogrammi vivono sulla GPU.
>
> ⇒ ⛔ **Delle due cose che la fase 3 consegna alla 4, nessuna delle due è dove la fase 3 l'ha
> messa, e nessuna delle due è nel percorso video della pagina.**

---

## 1. Che cosa cambia per l'utente

⭐ **Niente nel codice, e questo è il risultato**: le due cose per cui l'utente vedeva nero e lento
**non stanno nella pagina** — il nero è il monitor vuoto (**A1**) e i 28 ms sono del banco. ⇒ Il
tempo della fase 4 va **tutto** sul desktop vero, e i 28 ms che stavamo per andare a togliere dal
disegno **non ci sono**: toglierli sarebbe stato ottimizzare nella direzione sbagliata
(`LEZIONI.md` §7.2).

---

## 2. Serve una decisione di Nic?

⭐ **Sì, una sola, e pesa**: ⛔ **il numero su cui la fase 3 si è chiusa porta dentro un tratto che
il banco produce da sé.**

| | |
|---|---|
| dove sta scritto | `README.md` (riquadro del 14 agosto), `PIANO.md`, `fasi/rapporti/F3-E-anello-rimisurato.md` |
| che cosa dice | totale **78,1 ms**, di cui **disegno 28,0 — il 36 %**, *«il collo di bottiglia nuovo»* |
| `[M]` che cosa misuro io | lo stesso disegno, stesso confine, stessa misura, scena dichiarata: **2,25 ms** |
| ⛔ e il resto dove va | nel `getImageData` che **il banco** fa sul deposito per rileggere la sua marca |

⇒ **La decisione**: il 78,1 si **rimisura** (togliendo o scontando la lettura della marca) o si
**lascia con la riserva scritta accanto**? ⚠ Non è una decisione mia: il metro è dell'anello
**A10**, e il numero è di una fase **chiusa**. ⭐ E la parte del numero che NON è in discussione è
grande: cambia **un tratto su sette**, non l'architettura.

⚠ **E non decide questo rapporto da solo**: il coordinatore ha girato la stessa domanda ad A10.
Se arriviamo a due conclusioni diverse, **è un risultato**, e la mia sta qui sotto con la marca.

---

## 3. Che cosa ho MISURATO

⛔ **Il palco, dichiarato prima dei numeri, e non spostato** (`README.md` riga 397): Chrome
**151.0.7922.137** sul **desktop vero dell'utente** (CHUWI), Wayland da `XDG_SESSION_TYPE`,
**nessuna `--ozone-platform`**, **nessuna `--disable-gpu`**. Verificato **dall'altro capo**, cioè
letto dalla pagina: `screen` **2560×1080**, `webgl` **ANGLE (Intel, Mesa Intel(R) Graphics
(ADL-N))** — ⭐ **la GPU vera**. ⇒ È lo stesso palco su cui l'utente ha visto il nero.

### 3.1 ⛔ TESI 1 — *«HEVC viene consegnato e 0 vengono dipinti»* · **NON REGGE**

`banchi/04-b21-dipinge.py --matrice` isola la funzione sospetta e la chiama da fuori
(`CODER.md` §3.6): **quattro caselle**, profilo della *stringa* × profondità del *flusso*, perché
nel prodotto **le due non coincidono** — `[R]` `src/rcp.c:1198` negozia `8` (`NOSTRA_PROFONDITA
"8,10"`, e `prima_comune()` prende la prima) mentre `[R]` `src/figlio.c:1605` scrive
`r.profondita = 10;` **fisso**.

`[M]` 14 agosto 2026, e **il profilo è letto NEI BYTE** con `ffprobe` (secondo testimone: la riga
di comando che lo chiede non è la prova che sia stato dato):

| | flusso Main (8 bit) | flusso Main10 (10 bit) |
|---|---|---|
| **stringa `hev1.1.6` (Main)** | ⭐ dipinge *(controllo +)* | ⭐⭐ **dipinge** — ⛔ **è la sessione vera** |
| **stringa `hev1.2.4` (Main10)** | ⭐ dipinge | ⭐ dipinge *(controllo +)* |

⭐ **8 caselle su 8 dipingono**, a **64×48 e a 1920×1080**, HEVC e AV1, **zero cieche**. E i
controlli positivi sono verdi, quindi il verdetto **si può scrivere**: se uno solo fosse caduto,
sull'incognita non ci sarebbe niente da dire.

⭐ **E non è un fotogramma solo**: `04-b22` decodifica **60 fotogrammi su 60 offerti**, chiave +
delta a 1920×1080, con la combinazione esatta della sessione vera — **sei giri su sei**,
`consegnati == dipinti`, `0 guasti`.

> ### ⛔⛔⛔ E NELLA SESSIONE DEL NERO IL SERVER NON HA MANDATO **UN** FOTOGRAMMA
>
> `[M]` 14 agosto 2026, letto nel registro del prodotto —
> `/media/REMOTIX/tmp/02-figlio/registro.log` sul server, **6 735 736 byte, in append, sei
> accensioni dentro**. ⛔ **Le righe si leggono per finestra, e la finestra si nomina.**
>
> La sessione del nero è quella delle **05:35:06** — ed è la sua, letta nel registro:
> ```
> 05:35:06.321 rcp  sessione aperta utente=nicfio via=[192.168.0.3]:45161
>                   tela=1920x1080 vista=2545x927 disposizione=it
> 05:35:06.321 rcp  ⭐ FASE 3: canale video ACCESO — codec 1, tela 1920x1080
> 05:35:06.572 figlio ciclo: 1748 fotogrammi consegnati (118 chiavi),  837 attese a vuoto…
> 05:37:44.746 figlio ciclo: 1748 fotogrammi consegnati (118 chiavi), 1469 attese a vuoto…
> ```
>
> ⇒ ⛔⛔⛔ **Il contatore entra a 1748 ed esce a 1748.** Per **2 minuti e 38 secondi** il prodotto
> ha consegnato **ZERO fotogrammi**, e nello stesso tempo *«attese a vuoto»* è salito da **837 a
> 1469** — quattro al secondo, e la riga dice pure perché: *«scena ferma: Mutter consegna solo
> quando qualcosa cambia»*.
>
> ⭐ **E il 1748 è della sera prima.** La sessione delle **21:48** parte da *«0 fotogrammi
> consegnati (0 chiavi)»* e arriva a 1748: ⛔ `ciclo_fotogrammi` (`src/figlio.c:1486`) è **statico
> di file** e **non riparte con la sessione** — quel numero è un **residuo**, non una consegna.
>
> | il numero di §0-ter | `[M]` che cos'è davvero |
> |---|---|
> | *«**1 748** fotogrammi consegnati, e **0 vengono dipinti**»* | ⛔ nella sessione del nero i fotogrammi consegnati sono **ZERO**. Il 1748 è il contatore **dell'accensione**, fermo dalla sera prima |
> | *«il client richiede una chiave **1 659 volte**»* | ⛔ è il `grep -c` su **TUTTO IL FILE** (oggi dice **1661**). Nella finestra della sessione del nero sono **653**; in quella delle 21:48 sono **298** |
>
> ⇒ ⭐⭐⭐ **Il nero è spiegato per intero, e non c'entra il codec**: il client chiede una chiave
> (653 volte, ed è §5.2 che glielo impone), il server gira la richiesta al palco (e fa bene), **e
> il palco non ha niente da dare perché su quel monitor non cambia mai un pixel**.
> ⛔ **È §0-quater, non §0-ter** — il monitor **aggiunto e vuoto** — ed è il lavoro dell'anello
> **A1**.
>
> ⇒ ⭐ *Un client che non riceve fotogrammi e uno che li riceve e non li dipinge hanno lo stesso
> aspetto: schermo nero. La differenza sta in una riga di registro che nessuno aveva letto per
> finestra.*
>
> ⚠ **E il «0 dipinti» resta senza fonte**, ma adesso non serve più: nessuna riga del *server* può
> conoscerlo — `dipinti` è un contatore della **pagina** (`src/pagina.html:1878`) — e con **zero
> consegnati** un `dipinti` a zero è **la cosa giusta**, non un difetto.

**Dove si ricontrolla**: `python3 banchi/04-b21-dipinge.py --matrice --misure 64x48,1920x1080`
(verbale con `--json`). Il registro: `python3 v1/strumenti/sshpw.py "grep -c 'vuole una CHIAVE'
/media/REMOTIX/tmp/02-figlio/registro.log"`.

**Il pezzo cieco**: `[?]` **16-40 ms** fra il disegno e il pixel acceso, che nessuna API vede
(`web.md` §6.2). ⭐ **Su questo palco ESISTE** — è il desktop vero, non Xvfb. ⚠ Qui non entra in
nessun numero, perché §3.1 **conta pixel, non tempi**: si dichiara perché il confronto col §3.2
sia leggibile.

### 3.2 ⛔ TESI 2 — *«il disegno costa 28,0 ms su 78,1»* · **NON REGGE DOV'È MESSA**

`banchi/04-b22-disegno.py` spezza `Schermo.dipingi()` (`src/pagina.html:1839`) nei suoi **quattro**
pezzi. Scena dichiarata e **in movimento a ogni fotogramma**: `testsrc2` 1920×1080, vista
1280×720, 60 fotogrammi, mediana sulla **seconda metà** (`CODER.md` §3.5, e la prima metà si
stampa accanto perché il transitorio si veda).

`[M]` 14 agosto 2026 — **un caso solo per giro**, per togliere l'effetto dell'ordine, **3 giri per
colonna**, flusso **Main10** letto con la stringa **Main8** (⭐ *la sessione vera*):

| tratto (ms, mediana delle 3 mediane) | ⭐ **lettura del banco SPENTA** | ⛔ lettura **480×240 accesa**, come `03-b17:534` |
|---|---|---|
| 0 preparazione del deposito | 0,00 | 0,00 |
| 1 fotogramma → **deposito** (`drawImage(VideoFrame)`) | **0,60** | **2,50** |
| 2 `f.close()` | 0,00 | 0,00 |
| 3 le bande (`fillRect`) | 0,00 | 0,00 |
| 4 deposito → **tela**, riscalato (`drawImage`) | **1,60** | 0,90 |
| ⭐ **⇒ tratto 6 — il «disegno» della fase 3** | ⭐ **2,25** | **3,50** |
| ⛔ ⇒ fino alla **TELA LEGGIBILE** *(il confine SCOMODO)* | **18,85** | 20,40 |
| ⚠ *(fuori dai tratti)* la **lettura del banco** | 0,00 | ⛔ **16,55** |

*(i tre giri, uno per uno — tratto 6 spento: **2,25 · 2,30 · 2,00**; acceso: **3,50 · 3,20 · 4,30**;
tela leggibile spento: **20,30 · 18,85 · 15,65**; acceso: **20,40 · 19,30 · 22,20**.)*

⭐⭐ **IL CONTROLLO POSITIVO TIENE, ED È QUEL CHE RENDE SCRIVIBILE IL RESTO.** AV1 a 8 bit, nello
**stesso giro**: `[M]` **8,45 · 7,75 · 7,05 · 6,25 ms** — e la fase 3 lo misura **9,07**.
⇒ *Lo stesso cronometro che dice 2,25 su HEVC dice ~8 su AV1, e su AV1 concorda con la fase 3.*
⛔ **Quindi il cronometro non è il problema: il problema è che i due numeri di HEVC non sono lo
stesso numero.**

> ### ⛔⛔⛔ DOVE FINISCONO I 28 ms — e non è un'ipotesi, è la stessa scena con **una variabile sola**
>
> `03-b17-ritardo.py:534` rilegge **480×240 dal DEPOSITO a ogni fotogramma** per ritrovare la sua
> marca, e cronometra quella lettura **A PARTE** (`t_let − t_dip`): ⭐ correttamente, **non entra
> nel tratto 6**.
>
> ⛔ **Ma il costo non resta dove viene cronometrato.** Un fotogramma HEVC esce dal decodificatore
> **opaco** — `[M]` `VideoFrame.format` è **`null`**, cioè vive sulla GPU (AV1 esce `I420`/`I420P10`,
> cioè già in memoria di CPU). Il trasferimento GPU→CPU **lo paga chi tocca i pixel per primo**, e
> un `getImageData` ripetuto fa cambiare **sostrato** alla tela: da lì in poi lo paga
> `drawImage(VideoFrame → deposito)` — cioè **dentro il tratto 6**, sul fotogramma **DOPO**.
>
> ⭐ **E si vede a occhio nudo: la somma si conserva, e le due colonne si scambiano il conto.**
> `[M]` 14 agosto 2026, **un solo giro**, quattro casi in fila, lettura del banco **accesa**:
>
> | caso *(stesso giro, stessa scena)* | `VideoFrame.format` | tratto 6 | lettura del banco | **somma** |
> |---|---|---|---|---|
> | HEVC 10 bit — deposito **rimasto sulla GPU** | `null` (opaco) | 6,00 | ⛔ **17,20** | **23,20** |
> | HEVC 8 bit — deposito **passato alla CPU** | `BGRX` | ⛔ **27,35** | 0,60 | **27,95** |
> | AV1 10 bit | `I420P10` | 8,55 | 0,70 | **9,25** |
> | ⭐ AV1 8 bit *(controllo +)* | `I420` | 8,40 | 0,60 | **9,00** |
>
> ⇒ ⛔⛔ **`27,35 + 0,60 = 27,95` è il «28,0 ms del disegno» della fase 3** — ⭐ e non è un
> accostamento fortunato: **AV1 non si muove di un millesimo** fra le due colonne, **perché non ha
> niente da trasferire**.
>
> ⭐ **E lo scambio si riproduce a comando.** `[M]` due giri successivi, caso «sessione vera» e
> caso «hevc 10/10» — **lo stesso flusso**, l'uno dopo l'altro nello stesso giro:
>
> | | tratto 6 | lettura | somma |  | tratto 6 | lettura | somma |
> |---|---|---|---|---|---|---|---|
> | giro 1 · sessione vera | 4,80 | 22,15 | 26,95 | giro 1 · hevc 10/10 | **19,90** | 0,50 | 20,40 |
> | giro 2 · sessione vera | 3,25 | 14,55 | 17,80 | giro 2 · hevc 10/10 | **21,50** | 0,50 | 22,00 |
>
> ⇒ ⛔ **Il primo che gira tiene il deposito sulla GPU, il secondo lo trova già passato alla CPU.**
> *Il numero che esce dal tratto 6 dipende da quel che è successo prima — cioè non è una proprietà
> del prodotto.*
>
> ⇒ ⭐⭐⭐ *La fase 3 non ha misurato il disegno del prodotto: ha misurato **la propria lettura dei
> pixel**, riscossa una colonna più in là.* ⛔ **E per questo il difetto è comparso solo su HEVC**:
> è l'unico codec i cui fotogrammi vivono sulla GPU.

> ### ⭐ E IL CONFINE È STATO SPOSTATO NELLA DIREZIONE SCOMODA — tutt'e due le volte
>
> `CODER.md` §1-bis: *«ogni confine ha due posizioni difendibili, e quella che favorisce chi misura
> si sceglie da sé se nessuno la nomina»*. Qui ne restavano **due**, e le misuro **tutt'e due**:
>
> | confine | `[M]` | che cosa è |
> |---|---|---|
> | il **ritorno** di `drawImage` | **2,25 ms** | quanto sta fermo il JavaScript. ⛔ È il confine della fase 3, e `drawImage` **può tornare prima** che il lavoro sia fatto |
> | ⭐ la **tela LEGGIBILE** | **18,85 ms** | il lavoro finito davvero. ⚠ E forzarla **cambia la cosa misurata** |
>
> ⛔ **E NON SI SOMMANO AL PEZZO CIECO.** `[?]` 16-40 ms fra il disegno e il pixel acceso: per un
> fotogramma che vive sulla GPU, **la tela leggibile e il pezzo cieco misurano lavoro che si
> sovrappone** — il trasferimento GPU→CPU che io forzo è lavoro che **l'utente non paga**, perché
> il compositore va GPU→GPU. ⇒ ⭐ **Il numero onesto per l'utente è 2,25 ms + il pezzo cieco
> `[?]` 16-40**, e il 18,85 è il **tetto** che si paga solo se qualcuno rilegge i pixel.
> ⚠ *È una `[?]`, ed è il primo posto dove guarderei se il numero della fase 4 non tornasse.*

**Dove si ricontrolla**:
`python3 banchi/04-b22-disegno.py --fotogrammi 60 --solo "sessione vera" --lettura 0 --json FILE`
e lo stesso con `--lettura 480`: **una variabile sola.**

### 3.3 I due banchi, **certificati**

| | `--certifica` | esito `[M]` 14 agosto 2026 |
|---|---|---|
| `banchi/04-b21-dipinge.py` | sano → **una-tinta** → **vuoto** → risanato | ⭐ **PROMOSSO 4 giri su 4** |
| `banchi/04-b22-disegno.py` | sano → **disegno-lento** → **niente-fotogrammi** → risanato | ⭐ **PROMOSSO 4 giri su 4** |

⭐ **E i guasti sono scelti per provare quel che il banco dichiara di saper fare**, non per far
girare quattro volte lo stesso giro:

| guasto | l'atteso, scritto PRIMA | `[M]` che cosa è successo |
|---|---|---|
| **una-tinta** *(b21)* | nessuna casella dipinge — la prova vuole **due** letture giuste **e diverse** | ⭐ **0 su 8** (sano e risanato: **8 su 8**) |
| **vuoto** *(b21)* | 0 dipinte **e 0 cieche**: un flusso vuoto è un fallimento **che si nomina** | ⭐ **0 dipinte, 0 cieche** ⇒ zero e fallimento non si confondono (`CODER.md` §3.10) |
| ⭐⭐ **disegno-lento** *(b22)* | 10 ms dentro il **tratto 1** ⇒ deve salire **il tratto 1 e non un altro** | ⭐ **deposito +9,70 · componi −0,05 · bande +0,00** ⇒ **la scomposizione accusa il tratto giusto**, ed è l'unica prova che «scomporre» voglia dire qualcosa |
| **niente-fotogrammi** *(b22)* | `n = 0` **col motivo**, mai «0,0 ms» | ⭐ **5 casi su 5**: *«n = 0 — nessun fotogramma entro 30 s»* |

⭐⭐ **E la certificazione ha prodotto la quarta e quinta misura indipendente del numero**: nei
giri **sano** e **risanato**, il caso «sessione vera» esce **2,30 e 2,30 ms** — contro i
**2,25 · 2,30 · 2,00** dei tre giri puliti. ⇒ **Cinque giri, dispersione 0,30 ms**, contro i
**28,0** della fase 3.

---

## 4. ⛔ Che cosa NON ha funzionato

1. ⛔⛔ **NON HO ACCESO UN PRODOTTO MIO SULLA 7611, e il mandato chiedeva un banco che riproducesse
   il nero.** ⇒ Il nero l'ho **spiegato dal registro**, letto per finestra — e la spiegazione è
   solida (zero consegnati, misurato) — ⛔ **ma spiegare non è riprodurre**: se domani il desktop
   vero di A1 si muovesse e lo schermo restasse nero lo stesso, questo rapporto non basterebbe.
   ⚠ **E il banco per rifarlo esiste già a metà**: `04-b22` decodifica e dipinge il flusso vero;
   gli manca solo di prenderlo dal filo invece che da un file. La cucitura è **C2**.
2. ⛔ **La mia prima ipotesi era sbagliata, ed era scritta prima di misurare.** Avevo letto
   `rcp.c:1198` + `figlio.c:1605` e concluso: *«il server dice 8 e manda 10 ⇒ il decodificatore
   Main riceve un Main10 ⇒ errore ⇒ nero»*. ⭐ **La matrice l'ha smentita alla prima casella**, su
   tutt'e due le misure. *Il codice letto diceva una cosa vera — la profondità negoziata non arriva
   davvero al codificatore — e la conseguenza che ne avevo tratto era falsa.* (`CODER.md` §3.11.)
3. ⚠ **Il primo giro di `04-b22` mi ha ingannato sull'ORDINE**: coi cinque casi in fila, lo stesso
   caso dava **1,15 ms** in un giro e **20,65** in un altro, perché il sostrato che Chrome sceglie
   per una tela dipende **da quel che è successo prima**. ⇒ Curato con `--solo`, un caso per giro,
   e i tre giri concordano entro **0,30 ms**. ⛔ **Senza quella cura avrei scritto un numero e il
   suo contrario.**
4. ⚠ **Il banco si è rotto da sé alla certificazione**: `s.shutdown()` ferma il ciclo ma **non
   chiude il socket in ascolto**, e il secondo giro trovava la porta occupata **da se stesso**
   (`OSError: Address already in use`). Curato con `server_close()` in tutt'e due i banchi.
   ⭐ *Il primo giro era verde: se la certificazione fosse stata di un giro solo, non l'avrei
   visto — ed è esattamente la ragione per cui i giri sono quattro e non uno.*
5. ⚠ **`SONDE_MISURA.hevc` sono tutte a 8 bit** (`src/pagina.html:589`) mentre il prodotto manda
   **sempre 10** ⇒ `video.misura_massima` — il tetto a cui il server obbedisce per la tela — è
   misurato **in una condizione che non è quella d'uso**. ⛔ **NON l'ho cambiato**: `[M]` la
   matrice dimostra che oggi **non morde** (il flusso a 10 bit si dipinge con la stringa a 8), e
   riscrivere su un sospetto misurato *negativo* sarebbe la mossa che `CODER.md` §6 vieta. ⇒ Resta
   scritto qui con la riga, perché è **la stessa famiglia** del difetto che il 13 agosto è costato
   il codec dell'intero prodotto (`banchi/02-pagina-sonda-codec.py:126`).
6. ⛔ **`src/pagina.html` NON l'ho toccato**, ed è una scelta: le due accuse contro il percorso
   video **sono cadute tutt'e due**, e un cambiamento senza un difetto misurato dietro è
   esattamente quel che questo progetto paga più caro.

---

## 5. Le cuciture che chiedo al coordinatore

*⛔ Nessuna è mia: stanno tutte in file del coordinatore o di altri anelli. Le descrivo con la
firma esatta invece di scriverle.*

### C1 — ⛔ La profondità negoziata non arriva al codificatore *(`src/figlio.c`)*

`[R]` `src/figlio.c:1605` scrive `r.profondita = 10;` **fisso**, mentre `src/rcp.c:1482`
(`prima_comune`) ha appena negoziato **8** e lo scrive nel registro. ⇒ **Il prodotto dichiara al
client una profondità e ne manda un'altra**, e `RCP.md` §4.3 non lo permette.

⚠ **Non è il difetto del nero** — la matrice lo dimostra — ma è una **`[R]` viva**: oggi la salva
solo il fatto che Chromium legga la profondità dall'SPS invece che dalla stringa.

La firma esatta, e i due modi (⭐ la scelta è di chi possiede il file):

```c
/* dentro codificatore_di(), src/figlio.c:1590 — la profondita' arriva da fuori */
static Codificatore *codificatore_di(CodecVideo codec, uint8_t indice,
                                     uint32_t tela_l, uint32_t tela_a,
                                     int profondita);          /* ⬅ nuovo */
```
oppure, se la promozione a 10 bit è **voluta** (`CODER.md` §1: il 10 bit è la scelta dell'8 agosto),
allora è `NOSTRA_PROFONDITA` a mentire, e la cura è di **una riga sola** in `src/rcp.c:1198`:

```c
#define NOSTRA_PROFONDITA "10,8"   /* prima_comune() prende la PRIMA in comune */
```
⭐ **La seconda è la più piccola e dice la verità**: il prodotto codifica a 10 bit, e lo dichiara.

### C2 — ⭐ Il `dipinti` della pagina non arriva a nessuno *(cucitura di protocollo)*

⛔ **`0 dipinti` non ha una fonte.** Il server conta `consegnati`; solo la **pagina** conta
`dipinti` (`src/pagina.html:1878`), e nessuno dei due lo vede dall'altra parte. ⇒ Il sintomo
*«consegno e non si vede»* **non è misurabile da nessun capo da solo**, ed è precisamente il
sintomo su cui questa fase ha perso una giornata.

⚠ La cura più piccola non è di protocollo: è che **il banco dell'anello legga il contatore della
pagina accanto a quello del server** — `window.REMOTIX.schermo.conti` è già esportato
(`src/pagina.html:2069`). ⇒ Lo chiedo ad **A10**, che possiede il metro:

```
verbale["dipinti"]    = REMOTIX.schermo.conti.dipinti        /* dal CLIENT */
verbale["consegnati"] = REMOTIX.schermo.conti.consegnati     /* dal CLIENT */
verbale["server_consegnati"] = <riga «fotogrammi consegnati» del registro>
```
⛔ **E i due `consegnati` non sono lo stesso numero**: quello del server è **cumulativo
dell'accensione**, quello della pagina è **della sessione**. Confrontarli senza dirlo è
esattamente l'errore di §0-ter.

### C3 — ⛔ Il contatore del ciclo è dell'ACCENSIONE, non della sessione *(`src/figlio.c:2287`)*

`[M]` la riga *«ciclo: N fotogrammi consegnati»* esce **identica per otto ore** quando la scena è
ferma, perché `ciclo_fotogrammi` (`src/figlio.c:1486`) è statico di file e **non riparte con la
sessione**. ⇒ Chi lo legge da fuori — e §0-ter l'ha fatto — crede di avere il conto di **una
sessione** e ha quello dell'**accensione**, congelato.

⭐ La cura più piccola è **una parola nella riga**, non un contatore nuovo:

```c
/* src/figlio.c:2287 — «ciclo:» diventa «ciclo (dall'accensione):» */
"ciclo (dall'accensione): %llu fotogrammi consegnati (%llu chiavi), …"
```

### C4 — ⚠ Il registro è in append e nessuno lo dice a chi lo grep-a

`[M]` `/media/REMOTIX/tmp/02-figlio/registro.log` = **6,7 MB**, **sei accensioni** dentro.
Un `grep -c` ci ha già messo dentro **1 659** al posto di **298**. ⚠ `F3-E` documenta la stessa
trappola su un altro campo. ⇒ Chiedo a chi possiede i banchi di fase (**A10**) che **ogni lettura
del registro sia ancorata all'ultima riga `pronto: https://`**, come già fa `03-b17`.

---

## ⛔ Che cosa resta `[?]`, e va misurato prima di essere creduto

1. ⛔ **Se, quando la scena si muoverà, i fotogrammi arriveranno.** `[M]` oggi il prodotto non ne
   consegna perché non c'è niente da consegnare; ⚠ ma *«zero perché la scena è ferma»* e *«zero
   perché qualcos'altro è rotto a valle»* **hanno lo stesso aspetto finché la scena è ferma**.
   ⇒ Si chiude sul desktop vero di **A1**, e la prova che conta è una sola: `dipinti > 0` letto
   **dalla pagina** (C2). Se restasse zero con la scena in movimento, torna mia.
2. `[?]` **Se il compositore paghi davvero il trasferimento che io forzo.** Il **2,25 ms** è quel
   che paga il JavaScript; i **18,85** sono quel che paga chi rilegge i pixel. **Nessuno dei due è
   quel che vede l'utente**, e in mezzo c'è il pezzo cieco `[?]` **16-40 ms** che nessuna API vede.
   ⇒ Si misura solo **da fuori**, con una macchina fotografica — che è lo stesso metodo con cui il
   14 agosto si è misurato il giudizio dell'utente dal suo video.
3. `[?]` **Firefox non ha HEVC in WebCodecs** (`README.md`): la matrice qui sopra è **Chrome
   soltanto**, e va detto accanto a ogni casella.
