# F4-A5 — La tastiera: dalla lettera al martelletto

*Anello A5 della fase 4, 14 agosto 2026. `src/tastiera.c` · `banchi/04-b25-*`.*

---

## 1. Che cosa cambia per l'utente

**Scrive `é` da un client con tastiera italiana e sul desktop compare `é`; scrive la stessa `é`
in una sessione con la disposizione sbagliata e non compare NIENTE — con una riga nel registro
che dice quale carattere e quale disposizione.** ⛔ Non compare una `e`, che è la cosa che
rovinerebbe una parola d'ordine senza che nessuno capisca perché.

---

## 2. Serve una decisione di Nic?

**No.** Nessuna scelta che l'utente debba giudicare: le tre tesi del mandato sono state provate
vere e attuate come stavano scritte. ⚠ Una cosa da sapere, non da decidere: **le emoji non si
scrivono e non si scriveranno** — non esistono su nessun tasto di nessuna disposizione, e
`SPECIFICHE.md` §7.3 dice di dichiararlo invece di inventare. Se un giorno l'utente le volesse,
è un lavoro diverso (gli appunti, `RCP.md` §7.4), non questo.

---

## 3. Che cosa ho MISURATO

⭐ **Tutto si rimisura con un comando solo, e non serve né una sessione né `libei` né una porta**
(`CODER.md` §3.6 — isola una funzione e chiamala da fuori):

```
bash banchi/04-b25-lancia.sh
```

Esiti in `banchi/04-b25-esiti.jsonl`. `[M]` 14 agosto 2026, **17 prove, 0 rosse**, identiche sulla
macchina di sviluppo e nel contenitore di **192.168.0.2** (`xkbcommon` **1.7.0** su tutt'e due).

### 3.1 ⛔ Il metro: si verifica DAL LATO CHE RICEVE

La tentazione era confrontare i codici usciti con numeri scritti a mano nel banco («la `é`
italiana è il tasto 26 con Maiusc»). Sarebbe stato un banco che prova la mia aritmetica contro
sé stessa. ⇒ **Il banco simula il compositore**: prende i codici evdev che il modulo consegna, li
batte su una `xkb_state` che si costruisce da sé — la stessa macchina che gira dentro Mutter — e
legge **che carattere ne esce**. Il metro è la lettera che appare, non il codice che è partito.

⛔ **E il simulatore ha il suo controllo positivo e il suo negativo** (`CODER.md` §3.10), perché
«non è uscito niente» e «non ho saputo guardare» hanno lo stesso aspetto:

| controllo | esito |
|---|---|
| ⭐ **positivo** — sa vedere una lettera che esce di sicuro? tasto 30 su `it` | ✅ esce `a` |
| ⭐ **negativo** — sa DISTINGUERE? tasto 26 su `it` **senza** Maiusc | ✅ esce `è`, **non** `é` |
| applica i modificatori? Maiusc+26 | ✅ esce `é` |

*Senza il negativo, un simulatore che dicesse «é» comunque avrebbe dato verde anche
all'implementazione che si dimentica i modificatori.*

### 3.2 Le prove che `PIANO.md` righe 630-632 nomina

| prova | esito misurato |
|---|---|
| ⭐ **`é` su `it`** | ✅ `42(Maiusc sx) + 26` ⇒ **esce `é`** |
| ⛔ **`é` su `us`** | ✅ **ha detto NO e non ha mandato niente**, e la riga è nel registro: `U+00E9 non è producibile con la disposizione us [English (US)]: NON mandato niente (RCP.md §7.3)` |
| **`@` su `it`** | ✅ `100(AltGr) + 16` ⇒ esce `@` |
| **`@` su `us`** | ✅ `42(Maiusc) + 3` ⇒ esce `@` — **stesso carattere, due strade** |
| **emoji 😀 (U+1F600)** su `it` e su `us` | ✅ non producibile su nessuna delle due |
| **中 (U+4E2D)** su `it` | ✅ non producibile |
| `è` su `it` (senza modificatore) · `a` su `it` · `A` su `us` | ✅ escono tutt'e tre |
| surrogato U+D800 · U+110000 | ✅ ritornano **-1**, e non si confondono col «non producibile» |

⇒ ⭐ **Le tre tesi del mandato reggono, tutt'e tre.** In particolare la seconda: `é` e `@` escono
dalla strada di `LETTERA`, con Maiusc e AltGr **dentro** il percorso — mai come comandi.

### 3.3 ⛔ La trappola cercata da solo: il ripiego silenzioso

`[M]` **`xkbcommon` 1.7.0 non ripiega da sé**: chiesta una disposizione che non esiste,
`xkb_keymap_new_from_names()` ritorna **NULL** e scrive `[XKB-338] Couldn't find file
"symbols/zz_non_esiste"`. ⇒ **Il ripiego poteva metterlo solo il nostro codice, e non c'è.**

⚠ Ma quelle righe **finiscono su stderr e basta**, e chi chiama vedrebbe un NULL senza motivo.
⇒ Il registro di `xkbcommon` viene **dirottato** (`xkb_context_set_log_fn`) e il primo errore
diventa il testo di `*errore`:

```
sconosciuta: la disposizione «zz_non_esiste» non si compila
             ([XKB-338] Couldn't find file "symbols/zz_non_esiste" in include paths)
```

⛔ **E il ripiego si vedrebbe anche se entrasse da un'altra parte**: `tastiera_disposizione()`
porta il nome che la disposizione **compilata** dà di sé — `it [Italian]`, `us [English (US)]`.
Una riga di registro che dicesse `it [English (US)]` si legge da sola.

### 3.4 ⭐ Il banco è CERTIFICATO — ha visto il difetto, tre volte

`banchi/04-b25-guasti.c` sono tre implementazioni sbagliate di proposito, e il lanciatore
**pretende** che il banco dica ROSSO su ciascuna **e sulla prova giusta** (un rosso per un motivo
qualunque non è aver visto il difetto):

| difetto messo apposta | il banco dice |
|---|---|
| ⛔ **manda la `e` al posto della `é`** | ✅ ROSSO: *«ha detto SI (18) e sarebbe uscita «e» (U+0065) al posto di «é»: una LETTERA DIVERSA, che RCP.md §7.3 vieta»* |
| **dimentica i modificatori** | ✅ ROSSO: *«battendo 26 esce «è» (U+00E8), non «é» (U+00E9)»* |
| ⛔ **ripiega su `us` in silenzio** | ✅ ROSSO: *«RIPIEGO SILENZIOSO: ha ritornato una tastiera per una disposizione che non esiste»* |

### 3.5 Le tre misure che hanno cambiato il codice

**(a) ⛔ evdev 84 — la scelta legale che nessuna tastiera può battere.**
La prima stesura chiedeva alla disposizione quale tasto accende quale modificatore (invece di
scriverlo a mano come v1), e per l'AltGr italiano sceglieva **evdev 84**. Il banco diceva verde:
battendolo esce davvero la `@`, perché nel file `keycodes/evdev` di XKB il tasto `<LVL3>` sta al
codice 92 e porta `ISO_Level3_Shift`. ⛔ **Ma evdev 84 è un buco**: `[M]` in
`linux/input-event-codes.h`, fra `KEY_KPDOT` (83) e `KEY_ZENKAKUHANKAKU` (85) **non c'è niente**.
Nessuna tastiera al mondo emette quel codice. Regge finché i due lati hanno la stessa tabella e
smette **senza un errore** il giorno che non ce l'hanno. ⇒ Aggiunta una **preferenza** (non una
tabella: se `ISO_Level3_Shift` stesse altrove la scansione lo troverebbe lo stesso) e adesso esce
**100 (AltGr)**.

**(b) `de(neo)` — la regoletta di v1 sbagliava di due cose, non di una.**
`[M]` 14 agosto 2026:

| | |
|---|---|
| `ä` U+00E4 | `46` |
| `→` U+2192 | `43 + 77` |
| `α` U+03B1 | `42 + 43 + 32` |
| `√` U+221A | `100 + 43 + 17` — ⛔ **due** modificatori di livello |

⛔ v1 aveva `#define KEY_RIGHTALT 100` per il terzo livello: su `de(neo)` il terzo livello è il
tasto **43** (`<BKSL>`). E il quinto livello la sua regoletta non lo nomina affatto.
⭐ **E la stessa misura risponde alla domanda che il contratto pone senza dirla: quattro posizioni
bastano.** Il caso peggiore trovato ne usa **tre**, e `de(neo)` è la disposizione con più livelli
che il sistema porti.

**(c) il Maiusc destro.** La preferenza, percorsa fino in fondo, lasciava vincere l'ultimo: per il
Maiusc usciva il **destro** (54). Funzionava, il banco era verde — ma un registro che dice «Maiusc
destro» dove ogni mano usa il sinistro fa perdere mezz'ora a chi lo legge. Adesso vince il primo
della lista (42).

---

## 4. ⛔ Che cosa NON ha funzionato

1. ⛔ **Il banco era verde su un codice che nessuna tastiera può battere** (evdev 84, §3.5a). È la
   forma peggiore: `CODER.md` §4.6, «il verde non è vero». **A trovarlo non è stato il banco**, è
   stato l'aver guardato il numero stampato e non aver riconosciuto il tasto. ⚠ E il banco **non è
   stato corretto** per vederlo: un banco che verifica dal lato che riceve non *può* vederlo, perché
   dal lato che riceve quel codice funziona. Resta una `[?]` sulla vera macchina: se `libei`
   scartasse i codici evdev inesistenti, la vecchia stesura avrebbe smesso di scrivere `@` **senza
   errore**.
2. ⛔ **Ho cancellato per sbaglio `tastiera_apri()` da `src/tastiera.c`** mentre toglievo il pezzo
   che il coordinatore mi ha detto di non attuare — uno script che cercava all'indietro il
   separatore di commento e ne ha trovato uno troppo su. Riscritta e rimessa; il banco l'ha vista
   subito (non compilava). ⚠ Il file era **non tracciato da git**: non c'era niente da cui
   recuperarlo.
3. ⚠ **Il messaggio del ripiego poteva troncare** — rilievo del costruttore del coordinatore, e
   diceva bene: 320 byte non bastano a un nome di disposizione (fino a 64, `RCP.md` §4.5) più una
   riga di `xkbcommon` (fino a 255). ⛔ Non è stile: quel testo **è** il modo in cui il ripiego si
   dichiara, e un messaggio troncato è un ripiego dichiarato a metà. Allargato a 448, e il file
   compila pulito anche con `-Wformat-truncation=2`.
4. ⚠ **Il caso `disposizione == NULL` è provato meno degli altri.** Vuol dire «quella in vigore
   nella sessione», e lì la risposta la dà l'ambiente (`XKB_DEFAULT_*`): il banco verifica che si
   apra e che il nome venga dichiarato, non *quale* disposizione esca — perché dipende da chi ha
   avviato il servizio. `[?]`

---

## 5. Le cuciture che chiedo al coordinatore

### 5.1 ⛔⛔ LA PRIMA, ED È UN RIFIUTO DEL MANDATO — la disposizione non può arrivare da una stringa

Il contratto dice: `tastiera_apri(const char *disposizione)`, «la stringa negoziata all'attacco».
**L'ho attuato così e funziona** — ma poggia su un presupposto che nessuno ha misurato: **che la
disposizione che compiliamo noi sia la stessa con cui il compositore interpreterà i codici che gli
mandiamo.**

⛔ **Il presupposto è fragile dalla parte peggiore. Noi non SCEGLIAMO la disposizione della
sessione: la sceglie GNOME, e `libei` ce la CONSEGNA.** Il dispositivo tastiera porta la sua
keymap (`ei_device_keyboard_get_keymap`, formato `XKB_KEYMAP_FORMAT_TEXT_V1`), ed è **quella**, non
il nostro nome, a decidere che lettera esce.

**Il danno, in concreto** — sessione `it`, client che ha negoziato `us`, l'utente scrive `[`:

| | |
|---|---|
| su `us` | `[` sta sul tasto **26**, da solo |
| su `it` | sul tasto **26** c'è la **`è`**, e `[` vuole l'AltGr |

⇒ Mandiamo `26` e sullo schermo dell'utente compare **`è`**. ⛔ Non un carattere mancante: **un
carattere diverso** — esattamente ciò che `RCP.md` §7.3 vieta, e la trappola di `CODER.md` §4.2
arrivata dall'altro lato. Nessuno collegherebbe mai il sintomo alla disposizione.

⚠ **E `DECISIONI.md` §5-bis.7 dice che la degradazione è morbida** — *«una disposizione vecchia non
produce mai caratteri sbagliati, al massimo rende irraggiungibili un paio di accenti»*. ⛔ **Quella
frase è vera SOLO se si usa la keymap della sessione.** Con la nostra, i caratteri sbagliati escono.

⭐ **E v1 lo faceva già così**: `v1/remotix-c/src/tastiera.c:69`, `tastiera_keymap(tastiera, buffer,
lunghezza)` — la disposizione arrivava da `libei` e nessuno la compilava per nome. È l'unico pezzo
di v1 che il contratto di V2 non ha ripreso.

**La firma esatta che chiedo, da aggiungere a `src/tastiera.h`** (l'attuazione è mia, la cucitura è
tua):

```c
/*
 * Apre la disposizione che la SESSIONE consegna — non quella che il client ha
 * chiesto.  `testo`/`lunghezza` sono la keymap che `libei` porta col dispositivo
 * tastiera (`ei_device_keyboard_get_keymap`, XKB_KEYMAP_FORMAT_TEXT_V1).
 *
 * `negoziata` e' il nome che il client ha dichiarato in `ATTACCA` (RCP.md §4.5),
 * o NULL.  Se non combacia con quella della sessione si usa QUELLA DELLA
 * SESSIONE — e' la verita', e con l'altra uscirebbero lettere sbagliate — e il
 * ripiego si DICHIARA nel registro (CODER.md §4.2).
 *
 * ⛔ Da chiamare a OGNI `DEVICE_ADDED`, non una volta all'avvio: STUDI.md §gnome §9
 *    misura che un cambio di keymap distrugge e ricrea il dispositivo tastiera,
 *    e il vecchio smette di funzionare SENZA ERRORE.
 */
Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza,
                                  const char *negoziata, char **errore);
```

⚠ **E la domanda che resta aperta, che è tua e non mia**: se la sessione ha `us` e il client ha
negoziato `it`, **chi cambia la disposizione della sessione?** `DECISIONI.md` §5-bis.7 dice che si
rinegozia all'attacco, ma un client `libei` **non può imporre una keymap all'EIS**: la riceve. ⇒ O
la si cambia dalla sessione (`org.gnome.desktop.input-sources` sul bus della sessione, prima di
attaccare), oppure §5-bis.7 va riscritta come «il client **dichiara**, il server **si adegua a quel
che trova** e lo dice». `[?]` — nessuno l'ha misurato.

### 5.2 Da dove arriva `disposizione`, oggi che nessuno gliela passa

`input.h:41` dice `input_apri(sessione, tela_l, tela_a, errore)`: **non c'è nessun parametro per la
disposizione**, e A4 non ha modo di costruire una `Tastiera`. Se la 5.1 si accoglie il problema si
scioglie da sé (la keymap arriva da `libei` dentro `input.c`); se non si accoglie, serve:

```c
Input *input_apri(void *sessione_mutter, uint32_t tela_l, uint32_t tela_a,
                  const char *disposizione, char **errore);
```

con `disposizione` che è il campo di `ATTACCA` (`RCP.md` §4.5), passato da `figlio.c`.

### 5.3 I due guasti di `RCP.md` §4.5 sono distinti, ma solo nel testo

§4.5 vuole **`ERRORE_PROTOCOLLO`** per una stringa mal formata e **`SESSIONE_NON_SERVIBILE`** per
una disposizione ben formata che il sistema non conosce. Il contratto dà un solo canale d'uscita
(NULL + testo), quindi oggi i due si distinguono dal **prefisso** del messaggio — `forma:` oppure
`sconosciuta:`. ⚠ Funziona ma è fragile: chi scriverà `rcp.c` deve saperlo. Se preferisci un
`int *motivo` in coda alla firma, lo attuo.

⭐ **E il controllo di forma serve a più di una lettera storta**: la stringa finisce nella macchina
degli `include` di XKB, che **apre file per nome**. Un `../../qualcosa` arriverebbe lì dentro. Oggi
si ammettono solo `[A-Za-z0-9_-]`, `≤ 64` byte, con la variante fra parentesi.

### 5.4 `REG_TASTIERA` sta dentro `tastiera.c`, non in `registro.h`

`registro.h` lo condividono dieci anelli che scrivono nello stesso momento: una riga aggiunta lì
era una collisione garantita. ⇒ `#define REG_TASTIERA "tastiera"` è locale al mio file. **Da unire
a `registro.h` quando la fase chiude** — è una cucitura.

### 5.5 Chi scrive la riga del «non producibile»

`input.h:81` dice che `input_lettera()` ritorna 1 e *«chi chiama lo scrive nel registro»*. ⛔ **La
riga la scrivo già io**, e con dentro **quale disposizione** — che è l'unica cosa utile a chi legge
il registro sei ore dopo, e che `rcp.c` non sa. ⇒ **`rcp.c` non la duplichi**, o si contano due
volte gli stessi caratteri.

### 5.6 `[?]` Lo stato di BlocMaiusc e BlocNum non arriva a questo modulo

Per fare una lettera non si preme mai un lucchetto — le maschere che nominano `Lock` o `Mod2` si
scartano apposta, perché un lucchetto **resta acceso dopo** e cambierebbe la lettera successiva.
⚠ Ma se il BlocMaiusc è **già** acceso nella sessione, `Maiusc+a` dà `a` e non `A`: i nostri codici
sono giusti e la lettera esce sbagliata lo stesso.

`STUDI.md` §gnome §9 dice dove sta la risposta: `EI_EVENT_KEYBOARD_MODIFIERS` **non arriva nemmeno su
GNOME**, e la fonte vera sono le due proprietà D-Bus `CapsLockState`/`NumLockState` con
`SYNC_CREATE` — che danno anche lo **stato iniziale**. ⇒ Se vuoi chiudere il caso, serve una via per
farlo sapere a questo modulo, e la propongo così:

```c
/* Lo stato dei due lucchetti nella sessione, da STUDI.md §gnome §9 (le due proprieta'
 * D-Bus).  Da richiamare quando cambiano: qui dentro non si preme mai un
 * lucchetto per fare una lettera, ma se e' gia' acceso la lettera cambia. */
void tastiera_lucchetti(Tastiera *, int maiuscole_accese, int numeri_accesi);
```

⚠ **Non l'ho attuata**: costa poco, ma senza misurarla su una sessione vera sarebbe una `[?]`
scritta in C. Dimmi se la vuoi nella fase 4 o alla 6.

---

## I file

| | |
|---|---|
| `src/tastiera.c` | l'attuazione. Compila pulito con `-Wall -Wextra -Wformat-truncation=2` |
| `banchi/04-b25-tastiera.c` | il banco: simula il compositore e legge la lettera che esce |
| `banchi/04-b25-guasti.c` | i **quattro** difetti messi apposta, che lo certificano |
| `banchi/04-b25-lancia.sh` | `bash banchi/04-b25-lancia.sh` — non serve né sessione né porta |
| `banchi/04-b25-esiti.jsonl` | gli esiti dell'ultimo giro |

---

# ⭐ Aggiunta — il rifiuto è stato accolto, e attuato

*14 agosto 2026, dopo la risposta del coordinatore. Il resto del rapporto resta com'è.*

Il coordinatore ha accolto il rifiuto di §5.1 e ha messo in `src/tastiera.h` la firma esatta che
avevo chiesto. **`tastiera_apri_da_keymap()` è attuata in `src/tastiera.c`.**

⛔ **E sbloccava il prodotto intero**: A4 aveva già scritto `src/input.c` contro il contratto nuovo,
e l'albero non si collegava (`input.c:413: undefined reference`). `[M]` 14 agosto 2026, nel
contenitore di 192.168.0.2:

```
— chi CHIEDE il simbolo:      U tastiera_apri_da_keymap   (input.o)
— chi lo DEFINISCE:  00000000000007d0 T tastiera_apri_da_keymap   (tastiera.o)
— collegando tutti i nostri oggetti: 0 errori che nominino tastiera_apri_da_keymap
```

⚠ Il collegamento finale si ferma su `-lngtcp2 -lnghttp3 -lngtcp2_crypto_ossl`, che nel contenitore
ci sono solo come runtime Debian (`libngtcp2.so.16`) e vanno costruite dai sorgenti — è l'ambiente
del coordinatore, non questo pezzo.

## Il banco è cresciuto: **26 prove, 0 rosse**, e **quattro** guasti certificati

`[M]` 14 agosto 2026, identiche in locale e nel contenitore di 192.168.0.2.

| la prova nuova | esito |
|---|---|
| ⛔ **sessione `it` + client `us`, l'utente scrive `[`** | ✅ `100(AltGr)+9` ⇒ **esce `[`** |
| sessione `us` + client `it`, `é` | ✅ non producibile — la sessione non ce l'ha |
| sessione `it` + client `it`, `é` · sessione `it` + nessuna negoziata, `[` | ✅ escono |
| ⭐ **due disposizioni vive insieme non si rimescolano** (`STUDI.md` §gnome §9: si riapre a ogni `DEVICE_ADDED`) | ✅ `it`⇒1, poi `us`⇒0, poi **ancora** `it`⇒1 con gli stessi codici |

⭐ **E il quarto guasto certifica proprio quello**: un'implementazione che si fida del nome negoziato
invece che della keymap della sessione ⇒ il banco dice ROSSO, con il sintomo esatto che era stato
previsto a tavolino:

> *«battendo 26 sulla disposizione DELLA SESSIONE esce «è» (U+00E8), non «[»: UNA LETTERA DIVERSA»*

## ⛔ Che cosa NON ha funzionato, la seconda volta

5. ⛔⛔ **Il confronto fra disposizioni gridava al ripiego anche quando erano la stessa.** La prima
   stesura confrontava le due keymap **per intero**. `[M]`: una keymap `it` serializzata e
   ricompilata — il giro esatto che fa la nostra, da Mutter a noi — torna con **due keysym in meno**,
   `XF86KbdInputAssistPrevgroup` e `Nextgroup` (evdev 610 e 611): due tasti che non fanno nessun
   carattere e che nessuna tastiera ha. ⇒ La riga `RIPIEGO DICHIARATO` sarebbe uscita **a ogni
   connessione**, compresa quella in cui va tutto bene. **Un falso allarme su quella riga vale quanto
   un silenzio**: chi legge il registro impara a saltarla. Adesso si confrontano solo i tasti che
   **producono un carattere**.
6. ⛔ **E il banco non l'aveva visto**: era verde, perché guardava la lettera che usciva e la lettera
   usciva giusta. **L'ho trovato leggendo il registro.** È `CODER.md` §4.6 di nuovo, e in un punto
   che il banco non copriva per costruzione. ⇒ Aggiunte **quattro prove che guardano la riga**
   (`prova_dichiarazione`): dirottano stderr su un file e verificano nei **due versi** — che il
   ripiego si dichiari quando c'è, e che **non** si dichiari quando non c'è. Con il suo controllo
   positivo: se non leggessi nessuna riga affatto, «non ha dichiarato» e «non ho saputo leggere»
   avrebbero lo stesso aspetto.
7. ⚠ **Il banco ha detto «uscita 2» sulla macchina di prova**, e ha fatto bene: la copia che avevo
   spedito là aveva ancora il `tastiera.h` vecchio, senza la firma nuova. **Non ha detto verde e non
   ha detto rosso** — ha detto «non ho saputo misurare», che è la terza uscita per cui esiste.

## Le cuciture, aggiornate

- **§5.1 è chiusa**: firma accolta e attuata. ⚠ Resta aperta la domanda che le sta sotto, ed è del
  coordinatore, non mia: **se la sessione ha `us` e il client ha negoziato `it`, chi cambia la
  disposizione della sessione?** Un client `libei` non può imporre una keymap all'EIS: la riceve.
  Oggi il codice fa la cosa onesta — usa quella della sessione e **lo dichiara** — ma è un ripiego,
  non la cura. `[?]`
- **§5.2 si è sciolta da sé**: `input.c` prende la keymap da `libei` dentro casa sua, e non serve
  nessun parametro in più a `input_apri()`.
- **§5.3, §5.4, §5.5, §5.6 restano come scritte.**
- ⭐ **Una nota per A4, che non costa niente e vale un'ora di diagnosi**: `input.c:413` chiama con
  `negoziata = NULL`, quindi il confronto non si fa mai e la riga `RIPIEGO DICHIARATO` **non uscirà
  mai**. Va benissimo finché la disposizione negoziata non arriva fin lì — ma il giorno che
  `ATTACCA` la porta, basta passarla al posto di quel `NULL` e il confronto si accende da solo.
