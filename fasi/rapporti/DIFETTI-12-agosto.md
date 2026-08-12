# I difetti aperti al 12 agosto 2026 — e chi li cura

*Scritto su richiesta dell'utente: «fai una lista dei bug emersi, e assegna un agente a ciascuno».*

⛔ **Non è un elenco di tutto quel che è stato trovato**: i difetti che chi li ha trovati ha **già
curato nello stesso giro** non stanno qui — stanno nei rapporti, sotto «Che cosa NON ha funzionato»,
che è il posto giusto perché sono chiusi. ⭐ Qui c'è **solo quel che è ancora aperto**, con accanto
chi lo prende.

⚠ **E tre voci non sono difetti**: sono `[?]` da misurare, o cose di altri. Stanno in fondo, separate,
perché confonderle con i difetti gonfierebbe il conto — ed è lo stesso errore che `REVIEWER.md` §4
vieta fra `[R]` e `[?]`.

---

## ⛔ A. Quel che il giro di oggi ha ROTTO — e va curato per primo

### D1 — **B9 è SCADUTA**, e l'ha fatta scadere la cura dell'arbitro

`[M]` 12 agosto 2026, `01-b12-guasti.py --registro`: **13 su 14**, e il quattordicesimo è **B9**,
*«cambiati da allora: `../RCP.md`»*.

⛔ **È la conseguenza esatta di ciò che il registro deve dire**: le sette righe di F2.4 sono entrate
in `RCP.md` (§2.5, §5.2, §6.2, §11.1), e B9 è il banco che `RCP.md` lo **legge**. *«Scaduta» non è
«fallita»*, ma non è nemmeno «pulita»: **va rieseguita**, e finché non lo è vale come non certificata.

⚠ *È la stessa forma della notte fra l'11 e il 12 agosto, quando la cura del congedo fece scadere
sette certificazioni. Allora fu una sorpresa; oggi era prevedibile, e non è stata prevista.*

### D2 — **Le sei regole nuove non sono nei due arbitri**

`RCP.md` adesso dice sei cose che né `01-b4-validatore.py` né `02-filo-fotogramma.py` sanno
giudicare: `numero` parte da **1** (P2) · il primo fotogramma dopo `SESSIONE` **DEVE** essere chiave
(P6) · `largh.`/`altezza` **DEVONO** valere la tela (P5) · un `0x03` sul canale di controllo è
`ERRORE_PROTOCOLLO` (P3) · **nessuno** stream video prima di `SESSIONE` (P1) · **FIN prima dei 28
byte** è `ERRORE_PROTOCOLLO` (P4).

⛔ **Un arbitro che non conosce una regola non la fa rispettare**, e il verde che dà è la forma
peggiore di verde: quella che dà fiducia.

### D3 — **Il formato della registrazione è cambiato, e le registrazioni no**

§11.1 porta adesso il campo `fine` e la magia **`RCPREG 0x00 0x02`**. ⛔ Le registrazioni di prova
esistenti — `banchi/02-filo-prove/` e quel che produce `01-b4-registrazioni.py` — sono al formato
**`0x00 0x01`**, e il validatore vecchio le legge ancora. ⇒ Finché non si propaga, **la cura di P7
esiste solo sulla carta**: l'arbitro continua a non poter distinguere un fotogramma abbandonato da
uno troncato per errore, che è la forma **E8** per cui la riga è stata scritta.

---

## ⛔ B. Il terreno e gli attrezzi

### D4 — **La sessione GNOME torna nera al primo riavvio**

La cura applicata oggi vive in `$XDG_RUNTIME_DIR`, che non sopravvive al riavvio; e
`v1/banco/provision-server.sh` **non passa `--virtual-monitor`**. ⛔ È l'invariante **I7**: *la
protezione di un difetto noto sta nel programma, non in una riga di configurazione che si può
perdere* — e qui non sta né nell'uno né nell'altra.

⚠ **La cura definitiva è di prodotto** e non è di questo giro: `v1/remotix-c/src/sessione.c:671`
scrive il monitor virtuale **solo se il compositore è KWin**, e sul ramo GNOME `larghezza` e
`altezza` entrano nella funzione e si perdono. ⇒ Qui si cura **il terreno**, e si lascia scritto il
rilievo per chi scriverà il prodotto della fase 2.

### D5 — **`01-b0-terreno.sh prodotto` guarda nel posto sbagliato**

Riga 235: cerca il binario in `remotix/build/remotix`, mentre `costruisci.sh` lo mette in
`remotix/remotix`. ⇒ **quel controllo non può uscire verde**: è un **IGNOTO fisso**, cioè un
controllo che non controlla niente e che nessuno legge più.

### D6 — **`01-b12-lancia.sh` non si può puntare sul prodotto**

`SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"` è scritto in chiaro (la porta invece è già
configurabile con `B12_PORTA`). ⇒ **B13 si certifica solo dal proprio script «sera»**, e **P1 e P5
stanno fuori dall'orchestratore**: due strumenti misurano due scene diverse e **solo uno dei due può
certificare B13**.

### D7 — **`misura-cattura.c` stampa la misura CHIESTA, non quella negoziata**

Rilievo `[R]` trovato da F2.2 e **lasciato aperto di proposito**: non era suo, ed è **lo strumento
che certifica gli altri banchi**. La voce 12-bis fu curata in `misura-wlroots` e **non lì**.
⛔ Un banco che dichiara una misura che non è quella in vigore fa attribuire i numeri alla scena
sbagliata.

### D8 — **`cattura.h` porta un commento che la misura smentisce**

`cattura.h` e `gnome.md` §8.1 si contraddicevano sul buffer riciclato. Misurato: danno **parziale**
e le sette bande **intere** ⇒ ha ragione `gnome.md`. ⛔ Se avesse avuto ragione il commento, la fase
2 avrebbe consegnato **mezzo desktop senza un errore**.

### D9 — **`01-b0-chiamate.py`: 7 chiamate su 52 restano IGNOTE**

**0 rotte** — quindi non è un rosso; ⛔ ma non è nemmeno un verde, e uno strumento nato per dire *«chi
chiama un banco gli passa quel che pretende?»* che su sette casi dice «non so» copre meno di quel che
sembra.

### D10 — **Il registro delle certificazioni si unisce a mano**

Vive in due copie, una per macchina, e **il numero dipende da dove lo si chiede** — 13 da CHUWI, un
altro dal server, perché là `RCP.md` non c'è e qua non c'è `remotix/pagina.c`. ⭐ Hanno ragione tutt'e
due e lo strumento scrive «non so» invece di arrotondare; ⛔ ma l'unione a mano è un passo che prima o
poi qualcuno salta.

### D11 — **Il guasto di P5 copre meno di quel che promette**

La pagina ritira `/impronta` **prima di ogni tentativo**, quindi l'impronta falsa **non uccide la
sessione**. ⇒ Per coprire davvero **R1.14** serve un guasto che colpisca **il ritiro**, non il valore.

### D12 — **La parola d'ordine sulla riga di comando dei banchi**

Per `parola-di-prova` finisce in `ps`. ⭐ Per la parola generata di `prova2` no: B10 la passa per file
`0600` e la cancella con una `trap` — la strada buona **esiste già in casa** e va estesa.

---

## ⚠ C. Quel che NON è un difetto, e sta qui per non essere confuso con uno

| | |
|---|---|
| ⚠ **`VideoEncoder.flush()` non ritorna in Chrome headless** | aggirato con una finestra vera, ⛔ **non capito**. È una `[?]` da misurare, non una riga da correggere — e chi riusa quel banco altrove deve saperlo |
| ⚠ **Firefox accetta `prefer-hardware` su AV1 dove `vainfo` non elenca nessun entrypoint** | `[?]`: o ha una strada che VA-API non dichiara, o **ripiega in silenzio** (forma **E2**). Non è nostro codice, e non è misurato quale delle due |
| ⚠ **Il tracciatore di P5 è cieco su Chrome dentro `pagehide`** | né `sendBeacon` né una XHR sincrona escono. **Dichiarato**, e su Chrome l'attribuzione poggia sul registro del server — che basta |
| ⛔ **I 10 bit non passano da MemFd** | non è un difetto: è **quel che Mutter consegna**. La `[?]` viva è la strada **DMA-BUF**, e si misura — non si cura |
| ⛔ **Il buffer della scheda sbagliata** | il banco della cattura **non lo vedrebbe**, e il suo verde non lo assolve. È una lacuna **dichiarata**, da chiudere con un banco nuovo quando la fase lo chiederà |

---

---

## ⛔ D. Nati la sera del 12 agosto, dalla correzione di `RCP.md` §6.2

*La cura di **P5** — «la tela **in vigore**», non quella di `SESSIONE` — ha reso legale il cambio di
tela a metà sessione. ⛔ E ogni volta che si rende legale una cosa nuova, si apre quel che quella
cosa nuova porta con sé.*

### D13 — **il primo fotogramma alla misura nuova può essere un delta**, e nessuno se ne accorge

`[M]` 12 agosto 2026, banco `banchi/02-pagina-tela-*`, atteso scritto **prima** di ogni giro:

| | Chrome · **HEVC** | Chrome e Firefox · **AV1** |
|---|---|---|
| solo delta alla misura nuova | ⛔⛔ **5 fotogrammi emessi, tutti dichiarati alla misura VECCHIA, dipinti, ZERO errori** — immagine strappata, 7/8 sul pattern vecchio e 1/8 sul nuovo | ⭐ `EncodingError`, 0 fotogrammi |
| chiave nuova coi suoi parameter set | ⭐ 8 su 8 | ⭐ 8 su 8 |

⛔⛔ **Chi dipinge spazzatura in silenzio è HEVC su Chrome, cioè l'unica casella in cui HEVC arriva
al pixel** — e AV1 protesta in tutte e quattro. ⇒ **La regola serve perché sul codec principale il
sintomo è muto**, e una regola non si scrive sul codec che si comporta bene. Il sintomo sarebbe *«il
desktop si strappa quando ridimensiono la finestra»*, e non nominerebbe né il protocollo né la tela.

⭐ E la cura **costa zero**: la chiave nuova va bene **sia** riconfigurando il decodificatore **sia**
senza, su tutt'e due i codec, tutt'e due i motori, tutt'e due i versi. ⚠ E non è prudenza ma
necessità: un `VideoDecoder` riconfigurato pretende una chiave (`DataError`), quindi senza la riga
quella chiave **non arriverebbe mai** e ogni cambio di tela costerebbe un giro di rete e un
fermo-immagine.

⚠ **Un'asimmetria misurata e non spiegata**, che vale la pena avere in mano: **rimpicciolire tace,
ingrandire protesta** (`EncodingError`). `[?]`

⇒ **Testo pronto** nel rapporto dell'agente; da applicare a `RCP.md` §5.2 **quando il giro di
ricertificazione ha finito** — B9 legge `RCP.md`, e cambiarlo sotto un giro in corso è l'errore che
oggi è già costato un giro intero.

### D14 — **i fotogrammi in volo uccidono una sessione sana** — trovato leggendo, `[?]` non misurato

§6.2 fa chiudere con `ERRORE_PROTOCOLLO` chi riceve una misura diversa dalla tela in vigore. ⛔ Ma
§6.2 dice **anche** che i fotogrammi possono arrivare **fuori ordine** — e dopo un `TELA(ADATTATA)`
quelli già in volo portano **legittimamente** la misura precedente. ⇒ **Un client conforme uccide
una sessione sana**, ed è la stessa forma di P5, che per due ore è stata dentro il documento.

⚠ È la scena che §7.1 protegge per le **coordinate di input** con la sua grazia di un secondo — e
per i fotogrammi quella grazia **non c'è**.

---

## Chi cura che cosa

⛔ **Un agente per difetto, e ognuno possiede file suoi**: due agenti sullo stesso file si
sovrascrivono, ed è il motivo per cui questo elenco è anche una tabella di proprietà.

⚠ **E in due ondate, non in una.** Alcuni difetti vogliono **la stessa cosa in esclusiva** — la
sessione grafica del server, o l'orchestratore che fa girare tutti i banchi — e messi insieme si
guasterebbero le misure a vicenda. La seconda ondata parte quando la prima ha finito.

| Onda | Difetti | Possiede | Porta |
|---|---|---|---|
| **1ª** | **D1 · D2 · D3** — l'arbitro e i suoi due lettori | `banchi/01-b4-*`, `banchi/02-filo-*`, il registro | 7521 |
| **1ª** | **D4** — la sessione che torna nera | `banchi/02-sessione-*`, `v1/banco/provision-server.sh` | 7524 |
| **1ª** | **D11 · D12** — il guasto di P5 e la parola in `ps` | `banchi/01-p5-*` | 7522 |
| **1ª** | **D9** — le sette chiamate ignote | `banchi/01-b0-chiamate.py` | — |
| **1ª** | **D10** — il registro unito a mano | `banchi/01-b12-guasti.py`, il registro | — |
| **2ª** | **D7 · D8** — lo strumento che certifica gli altri | `v1/banchi/banco-compositori/*`, `cattura.h` | 7525 |
| **2ª** | **D5** — il terreno del prodotto | `banchi/01-b0-terreno.sh` | 7527 |
| **2ª** | **D6** — l'orchestratore puntato sul prodotto | `banchi/01-b12-lancia.sh` | 7526 |
