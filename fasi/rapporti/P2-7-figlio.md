# P2.7 — Il figlio per utente

*12 agosto 2026, sera. Mandato: `DECISIONI.md` **§1.10-bis**, deciso dall'utente davanti alla misura
del montaggio (`P2-6-montaggio.md` §5.4). Porta di questo giro: **7571**, albero dei sorgenti
**`02-figlio-src`** — ⛔ 7448, 7501 e 7561 contate prima e dopo, e mai toccate.*

> ⭐ **In una riga**: il server gira **da root**, e il desktop che compare nella scheda e' quello
> **di chi e' entrato** — catturato da un processo figlio che gira come lui, la cui identita' il
> padre non deduce ma **la fa timbrare dal nucleo su ogni messaggio**.
>
> ⛔ E il banco ha trovato **due difetti veri**, uno dei quali era una **fuga di pixel fra utenti**.

---

## 1. La forma scelta, e in che cosa differisce dall'aiutante

§1.10-bis dice che e' *«l'aiutante di §1.10 al contrario, ed e' la stessa regola: un mestiere per
processo»*. La forma dell'aiutante e' stata guardata prima di inventare, e tre cose sono diverse.

| | l'aiutante (§1.10) | il figlio (§1.10-bis) |
|---|---|---|
| **quando nasce** | **prima** dei socket, apposta: un `fork()` regala i descrittori, e uno acceso dopo si porterebbe dietro la porta | ⛔ **non puo'**: nasce quando un utente e' ammesso, cioe' per forza dopo gli ascoltatori. ⇒ Quel che l'aiutante compra col **momento**, questo lo compra con **`close_range()`** |
| **come si passa il testimone** | `fork()` e basta | ⛔ `fork()` **+ `execve()`**, e la ragione decide da sola: la memoria del padre contiene **la chiave privata TLS del server**, la tabella dei ban e lo stato di tutte le sessioni. Un figlio che girasse come l'utente **senza** `exec` gliela regalerebbe — `/proc/self/mem` e' leggibile dal proprietario del processo, e l'utente **e'** il proprietario |
| **quanto vive** | una transazione, poi muore | ⛔ **sopravvive al distacco** (I4): e' il palco. Muore col server — `PR_SET_PDEATHSIG` **e** l'EOF sul socket, due strade indipendenti perche' la prima puo' perdersi quando cambiano le credenziali |
| **il socket** | `socketpair` **SEQPACKET** anonimo | uguale, e per la stessa ragione: i confini dei messaggi li tiene il nucleo |
| **il fallimento** | e' un **NO**, mai un forse | uguale: nessun figlio ⇒ nessun palco, dichiarato — ⛔ e **il verdetto di PAM non cambia**: negare l'accesso perche' il palco non si e' montato farebbe pagare a chi entra un difetto nostro |

⭐ **E l'`exec` paga tre volte**: memoria pulita, **l'ambiente composto da zero per costruzione**
(`CODER.md` §4.5 non e' una disciplina, e' la firma di `execve`: quel che non sta nell'`envp` non
esiste), e nessun `fork` da una libreria con thread — ⛔ perche' il padre, da root, **non tocca piu'
ne' GLib ne' D-Bus ne' PipeWire**: `sessione_assicura()` e `primo_fotogramma()` sono **usciti da
`main.c`** e vivono in `figlio.c`, dall'altra parte del calo di privilegio.

⛔ **E si scende all'utente PRIMA dell'`exec`**: cosi' l'immagine nuova nasce gia' senza privilegi, e
non esiste nessun istante in cui il codice del figlio giri da root.

---

## 2. ⛔ Come si verifica che il figlio giri come l'utente **giusto**, a ogni messaggio

### 2.1 Il controllo che sembrava un controllo, e non lo era

La domanda «chi c'e' dall'altro capo del socket?» ha una risposta ovvia, `getsockopt(SO_PEERCRED)`,
⛔ **e su un `socketpair()` e' la risposta sbagliata**: il nucleo ci mette le credenziali del
processo che ha chiamato `socketpair()` — il padre, root — su **tutt'e due** i capi, e non le
aggiorna mai piu'. ⇒ Un padre che avesse controllato cosi' avrebbe letto `uid 0` per un figlio sceso
a `uid 1001`, avrebbe visto un numero, e **non avrebbe controllato niente**.

### 2.2 Il notaio e' il nucleo: `SO_PASSCRED` + `SCM_CREDENTIALS`

Il capo del padre ha `SO_PASSCRED`, e il nucleo timbra **ogni messaggio** con pid/uid/gid **veri del
mittente al momento della scrittura**. Un processo non privilegiato non ne puo' dichiarare di falsi.

⭐ **E' il numero di pratica dell'aiutante, con un notaio**: la pratica la scriviamo noi, le
credenziali le scrive il nucleo. Perche' un messaggio conti devono essere vere **cinque** cose
insieme (`credenziali_combaciano()`, ed e' l'unico punto del programma che dice di si'):

1. il nucleo ha attaccato le credenziali — ⛔ «senza credenziali» **non e'** «credenziali giuste»;
2. il pid del mittente e' **quel figlio li'**;
3. uid e gid timbrati sono quelli risolti dal **nome** dell'utente della sessione RCP;
4. la matricola e' la sua;
5. ⚠ il nome risolve **ancora oggi** a quell'uid (`getpwnam_r` rifatta): e' l'unica delle cinque che
   puo' cambiare mentre il figlio e' vivo, e un legame non piu' dimostrabile e' un **no**.

⛔ **E se una sola non regge, il figlio si abbatte** — non «il messaggio si butta»: il legame fra la
sessione RCP e l'identita' del palco non e' piu' dimostrabile, e un palco di cui non si sa di chi e'
non deve consegnare pixel.

### 2.3 E i messaggi ci sono anche quando non succede niente

Un figlio che ha consegnato il suo fotogramma e poi tace resterebbe verificato **una volta sola**,
cioe' esattamente quel che §1.10-bis vieta. ⇒ Il padre gli ridomanda **«chi sei» ogni minuto**
(`figli_ricontrolla`), la risposta ripassa dagli stessi cinque muri, e il figlio **rilegge i propri
uid dal nucleo** (`getresuid`) invece di ristampare una variabile scritta all'avvio.

### 2.4 I muri sono **tre**, e sono stati misurati uno per uno

| # | dove | che cosa guarda |
|---|---|---|
| 1 | nel figlio, **prima** dell'`exec` | `getresuid`/`getresgid`: reale, effettivo **e salvato**. ⛔ Un saved-uid a 0 e' un processo che puo' tornare root, e `setuid()` che ritorna 0 non lo esclude |
| 2 | nel figlio, **dopo** l'`exec` | lo stesso controllo su un'immagine nuova: un programma che si fidasse del proprio `argv` sarebbe un figlio che si dichiara da se' |
| 3 | ⭐ **nel padre, a ogni messaggio** | il timbro del nucleo |

---

## 3. L'esito del banco — **7 casi su 7**, coi loro guasti

`banchi/02-figlio-prova.py`, dentro il contenitore e **da root** (meta' delle letture sono su `/proc`
di un processo di root, e *«non ho potuto leggere»* non e' *«non c'era»*: senza root esce **2**).
⛔ L'atteso e' scritto **in testa al file** e si stampa con `--previsione`, prima del giro.

⛔ **E l'identita' non si legge nel registro**: il prodotto scrive *«sono il figlio di nicfio: uid
1000»*, e credergli sarebbe credere al processo che si dichiara. Si legge `/proc/<pid>/status`,
campo `Uid:`, **tutti e quattro i numeri**.

| caso | esito, `[M]` 12 agosto 2026, porta 7571 |
|---|---|
| **`nasce`** | ⭐ un figlio, `Uid: 1000 1000 1000 1000` e `Gid` idem; `argv[0] = remotix-figlio`; **4 descrittori alla nascita** (0,1,2 e il socket) contro gli 8 del padre; **zero socket in comune col padre**; «IL BUS DI SESSIONE E' MIO»; e un fotogramma arrivato al padre |
| **`due`** | ⭐ seconda connessione dello stesso utente ⇒ **un figlio solo, stesso pid** (I2), e il prodotto scrive la riga che lo dice |
| **`distacco`** | ⭐ il cliente se ne va, e dopo 6 s senza nessuna connessione il figlio e' **ancora vivo**, stesso pid, stato `S` — **I4** |
| **`muore`** | ⭐ `SIGKILL` al figlio ⇒ il pid **sparisce da /proc in 0,2 s** (raccolto, non zombie), il registro nomina la causa — *«l'ha ucciso il segnale 9»* — il deposito viene **svuotato**, e una connessione nuova fa nascere un figlio con **pid diverso** |
| **`senza-palco`** | ⭐ «prova» (uid 1001, senza `/run/user/1001`): il figlio **nasce**, `Uid: 1001 1001 1001 1001`, **dichiara di non avere il bus**, e ⭐⭐ **vede ZERO fotogrammi** |
| ⛔ **`guasto-uid`** | il `setuid` tolto ⇒ nessun figlio vivo, e il registro: *«e' uscito con 35 — ⛔ NON E' SCESO all'utente»* |
| ⛔⛔ **`guasto-cieco`** | il `setuid` tolto **e i due controlli del figlio tolti** ⇒ un figlio **a uid 0** si presenta dicendo di essere «nicfio», e ⭐⭐ **lo abbatte il PADRE**: *«MESSAGGIO RIFIUTATO … il nucleo dice uid 0 gid 1000, e «nicfio» e' uid 1000»* |

⭐ **Il `guasto-cieco` e' il caso che vale di piu'**, ed e' l'unico che possa vedere il muro 3: senza,
*«il padre verifica a ogni messaggio»* sarebbe una riga di codice che nessuno ha mai visto mordere.

⛔ **E il guasto e' stato innestato quattro volte, non una**: al primo tentativo ne avevo tolto uno
solo, il figlio si e' fermato al muro 1, e **il caso sarebbe stato verde senza aver provato niente**.

### 3.1 Il controllo che regge tutto, rimisurato adesso

`02-figlio-accendi.sh bus`, `[M]` 12 agosto 2026 — e sono **due**, perche' il negativo da solo
direbbe solo «gdbus non funziona»:

```
⭐ root NON si collega al bus di sessione di uid 1000   (il fatto di §1.10-bis)
⭐ uid 1000 CI ARRIVA                                    (il controllo POSITIVO)
```

### 3.2 Il tempo, e perche' il fotogramma fa in tempo

`[M]` dalla generazione del figlio ai due flussi in deposito: **303 ms**
(`11.369` generato → `11.380` si presenta → `11.381` bus → `11.468` catturato → `11.672` AV1 in
deposito). ⭐ Il bilancio **garantito dal protocollo** e' il secondo fisso di §4.4-bis, che scorre
fra «PAM ha detto si'» e `SESSIONE`: **1000 ms**. Margine ×3,3, e per questo il figlio prende il
palco **subito**, senza aspettare che qualcuno glielo chieda.

---

## 4. ⛔⛔ I due difetti che il banco ha trovato — e tutt'e due erano **del prodotto**

`REVIEWER.md` §1 dice che il banco e' il primo imputato. Stavolta no.

### 4.1 Il figlio ucciso restava **zombie** — e la lezione era di stamattina

`--caso muore`, primo giro: *«dopo 15 s il pid c'e' ancora, stato Z»*. ⛔ Il figlio moriva, il suo
socket dava EOF, e il padre **liberava la casella subito**, azzerando il pid: il `waitpid(WNOHANG)`
piu' sotto non aveva piu' niente da raccogliere.

⚠ **E' la stessa lezione che l'aiutante aveva gia' pagato oggi** (`PAM-filo-unico.md` §6), ricomparsa
di un passo piu' in la': in `/proc` uno zombie e un processo vivo hanno **la stessa faccia**, quindi
«il figlio e' morto» e «il figlio non muore» erano indistinguibili — **anche per il padre**.

⭐ **La cura**: il congedo e la liberazione sono **due passi**. `figlio_congeda()` chiude il socket,
manda `SIGTERM` e lascia la casella occupata **col pid dentro**; la casella si libera solo quando il
nucleo conferma, e la riga porta **la causa vera**. ⛔ E se non muore in 3 s, `SIGKILL`.
`[M]` dopo la cura: **0,2 s**, con *«l'ha ucciso il segnale 9»*.

### 4.2 ⛔⛔ La fuga di pixel fra utenti — «prova» ha ricevuto il desktop di «nicfio»

`--caso senza-palco`, primo giro: **il cliente di «prova» e' uscito 0, con un fotogramma conforme.**
⛔ Il suo palco non ne aveva prodotto nemmeno uno: quel fotogramma era il desktop di **nicfio**.

**La causa**: `wt_video_deposita()` in `webtransport.c` e' un deposito **di PROCESSO**. Alla fase 2
era giusto — c'era una sessione grafica sola, quella dentro cui girava il server. ⛔ **Con un figlio
per utente quella frase diventa un difetto**, e non e' «non ricevi niente»: e' **ricevi il desktop di
un altro**, e nessuno dei due se ne accorge. E' **I3 violata in modo invisibile** — precisamente la
forma che §1.10-bis nomina, ricomparsa all'ultimo centimetro.

⭐ **La guardia, e sta nel PROGRAMMA (I7)**, in `main.c`:

- il deposito ha un **padrone**, e a nominarlo e' **l'ammissione**, non il fotogramma: quando PAM
  dice si' a un utente diverso, il deposito si **svuota** e il padrone diventa lui;
- un fotogramma che arriva da un figlio che non e' il padrone viene **rifiutato** — anche se e'
  partito prima che il padrone cambiasse (⛔ e' il caso di corsa: il claim lo pone l'ammissione, non
  la consegna);
- al nuovo padrone si **chiede il suo** (`figli_chiedi_palco`), cosi' chi rientra rivede il proprio
  desktop invece di non vedere piu' niente. ⚠ Il figlio rimanda **lo stesso** fotogramma: la fase 2
  e' un'immagine ferma, e ricatturare consegnerebbe due immagini diverse sotto la stessa etichetta.

⛔ **Non c'e' nessuna strada verso `SESSIONE` che non passi da un'ammissione** (I3), quindi non c'e'
nessuna sessione che possa leggere il deposito di un altro.

⚠ **Il prezzo, dichiarato**: due utenti collegati **insieme** non possono vedere tutt'e due il
proprio desktop — l'ultimo che entra prende il deposito, e all'altro tocca rientrare. ⛔ **E questo
non e' un difetto di `main.c`: e' il §6 qui sotto.**

`[M]` dopo la cura: «prova» vede **zero** fotogrammi; «nicfio» che rientra dopo di lui li rivede.

---

## 5. ⭐ Il controllo positivo: la scena regge, e dice una cosa in piu'

`bash banchi/02-montaggio-scheda.sh` con `PORTA=7571`, Chrome 151 su Xvfb `:78` 2048×1280,
`[M]` 12 agosto 2026:

| chi entra | che cosa vede nella scheda |
|---|---|
| ⭐ **`nicfio`** | *«Ammesso, sessione nuova, tela 1920×1080»* e **il desktop di `nicfio` dipinto sulla tela**, AV1 — contro un server che gira **da root** |
| ⚠ **`prova`** | *«Ammesso, sessione nuova, tela 1920×1080»*, e **nessuna tela**: nessun pixel |

⛔ **E qui va detta una cosa che il mandato non poteva sapere.** La scena della 7561 e' *«entro come
`prova` e vedo un desktop»* — ⛔ **e quel desktop era di `nicfio`**: il server della 7561 gira come
uid 1000 e mostra a chiunque entri la sessione dentro cui gira lui (`02-montaggio-accendi.sh` lo
dichiara). ⇒ Quella scena **non puo' sopravvivere per costruzione**, perche' **era il difetto**.

⭐ Quel che sopravvive, ed e' la stessa cosa misurata meglio, e' *«entro e vedo il MIO desktop»*: con
`nicfio` la scheda mostra il suo, e con `prova` non mostra quello di nessun altro. ⚠ Che `prova` non
veda **niente** e' una misura, non un difetto: `prova` non ha mai fatto login su quella macchina,
quindi non ha `/run/user/1001`, quindi non ha bus, PipeWire ne' palco — e il figlio **lo dice**.

⛔ **E il cliente indipendente lo conferma dal lato che riceve**: `02-filo-cliente.py`, dentro il
contenitore, **uscita 0** — *«ACCETTATO stream 15, 11951 byte, finito con fin: chiave n. 1,
1920×1080 · 1 fotogrammi, tutti conformi a RCP.md»*, lo stesso numero di `P2-6` §3, ma con il
fotogramma catturato da un figlio a uid 1000 sotto un padre a uid 0.

---

## 6. ⛔ Che cosa NON si e' potuto chiudere, e di chi e'

| # | che cosa manca | perche' non l'ho fatto io |
|---|---|---|
| 1 | ⛔⛔ **il deposito del video dev'essere PER SESSIONE**, non per processo (`webtransport.c`, `video_forse()` e `wt_video_deposita()`) | ⛔ `webtransport.c` non e' di questo mandato. §4.2 e' la **guardia** che impedisce al difetto di nascere, non la cura: finche' il deposito e' uno, due utenti insieme non possono vedere tutt'e due il proprio desktop |
| 2 | ⚠ `video_forse()` pone `video_fatto = true` **anche quando il deposito e' vuoto**: quella sessione non ricevera' un fotogramma **mai piu'**, nemmeno quando arriva | ⛔ Stesso file. Oggi non morde perche' il figlio consegna in 303 ms contro il secondo garantito da §4.4-bis — ⚠ ma e' una **corsa vinta**, non una garanzia: la cura e' non arrendersi su un deposito vuoto, che e' quel che quella funzione fa gia' per la tela |
| 3 | ⛔ **far NASCERE la sessione grafica di un utente che non ce l'ha** | vuole `pam_open_session` (cioe' `pam_systemd`, che crea la sessione logind e `/run/user/<uid>`): e' la decisione del **login vero**, non di qui. Senza, un utente che non ha mai fatto login su quella macchina entra e non vede niente — dichiarato dal figlio, riga per riga |
| 4 | ⚠ il registro **si intreccia**: padre e figli scrivono sullo stesso descrittore, e `[M]` una riga e' uscita dentro un'altra | `[?]` non misurata a fondo, ed e' di `registro.c`, che non e' di questo mandato. ⚠ Chi legge il registro deve saperlo |
| 5 | ⚠ il tetto di **16 figli** non e' mai stato visto mordere | come il tetto delle sessioni di §1.11: e' **codice presente che nessuno ha visto funzionare**, la forma che B5 ha gia' trovato una volta |

---

## 7. I file

| file | |
|---|---|
| `src/figlio.h` · `src/figlio.c` | ⭐ **nuovi** (214 + 1.788 righe) — la meta' del padre (tabella, `SO_PASSCRED`, raccolta) e la meta' del figlio (calo di privilegio, ambiente, palco), separate dal calo di privilegio |
| `src/main.c` | ⛔ `sessione_assicura()` e `primo_fotogramma()` **tolti** (il padre non tocca piu' GLib/D-Bus/PipeWire); il ponte verdetto→figlio; il deposito col padrone; `--figlio-interno` come prima riga di `main()` |
| `src/aiutante.h` · `.c` | il verdetto porta anche **il nome dell'utente** (⛔ non la parola: quella e' gia' azzerata da §4.4) — e' l'unico posto che ha insieme la pratica e il nome |
| `src/Makefile` | `figlio.c` fra i sorgenti; ⛔ `main.o` **non dipende piu'** da `sessione.h`/`cattura.h`/`mutter.h`/`codificatore.h`. ⚠ NON fra i `GEMELLATI` |
| `banchi/02-figlio-prova.py` | il banco: 7 casi, l'atteso in testa, `/proc` invece del registro, e i due guasti |
| `banchi/02-figlio-accendi.sh` | il server **da root** sulla 7571, il controllo `bus` (negativo + positivo), e i guasti da innestare nella copia |
| `banchi/02-figlio-lancia.sh` | l'orchestratore da CHUWI, via `sshpw.py`, senza mai una redirezione attorno a `ssh` |
| `banchi/02-figlio-esiti.jsonl` | un esito per giro, con la scena dentro |

⛔ **Non toccati**: `RCP.md`, `src/rcp.c`, `src/rcp.h` (⇒ il gemello di `banchi/rcp/` resta identico
byte per byte), `webtransport.c`, `cattura.c`, `mutter.c`, `sessione.c`, `codificatore.c`,
`pagina.html`. Nessun `git` che scrive.

⚠ **E una regola di casa che questo giro ha ripagato**: `p=$(cat …)` dentro `ssh → enter.sh →
bash -lc` e' arrivato **vuoto**, e il banco e' morto su `argparse`. ⭐ Curato come dice la casa: il
pid lo legge il banco **da un file** (`--pid-file`) — *un file non ha livelli di virgolette*.

---

## 8. Le certificazioni invalidate — elencate, e **non rincorse**

⛔ *«Scaduta» non e' «fallita».* `src/` e' cambiato (`main.c`, `aiutante.*`, `Makefile`, piu' due file
nuovi), e `attrezzi-allinea-prodotto.sh` porta `src/` intero ⇒ **le nove `[ricostruisce]` del
catalogo scadono**: **B2, B3, B5, B6, B7, B8, B10, P5, P5R**. ⚠ Erano gia' scadute da `P2-6` §8 e
non sono state rifatte: **questo giro non le ha risanate e ne aggiunge la causa nuova**.

⭐ **E tre cose che NON scadono, e vanno dette perche' non si rincorrano:**

1. ⛔ **`rcp.c` non e' stato toccato**, quindi le certificazioni che poggiano sul gemello
   `banchi/rcp/` non scadono **per questo giro** (scadono per il binario, come sopra). Il `Makefile`
   ha confrontato le tre copie a ogni costruzione: **identiche**;
2. ⭐ **nessun binario in esecuzione e' stato sostituito**: si e' costruito in un albero proprio
   (`02-figlio-src`), e 7448, 7501 e 7561 girano ancora sui loro. `[M]` 2+2+2 ascoltatori prima e
   dopo ogni giro;
3. ⚠ **`RCP.md` §0-bis resta stantia** come la lasciava `PAM-filo-unico.md` §5: non l'ho toccata, e
   il filo non e' cambiato di un byte — nessun tipo nuovo, nessun motivo nuovo, nessun campo nuovo.

**Lo stato della macchina alla consegna**: 7448 · 7501 · 7561 **accese e intatte** (2 ascoltatori
ciascuna). ⛔ **La 7571 e' SPENTA**, e di proposito: un figlio vivo tiene un monitor virtuale in piu'
sulla sessione di `nicfio` (`[M]` «Meta-2», 2 monitor prima e 3 dopo), e l'utente sta guardando il
proprio desktop sulla 7561. Si riaccende con
`bash banchi/02-figlio-lancia.sh accendi`. ⭐ Alla chiusura: *«nessun figlio e' rimasto orfano»*.
