# F4-A4 — L'iniezione: l'input arriva DAVVERO al desktop

*Anello **A4** della fase 4, 14 agosto 2026. Banco: `banchi/04-b24-*`.
Codice: `src/input.c` (attua `src/input.h` su `libei` 1.3.901) e la cucitura
`ConnectToEIS` in `src/mutter.c`.*

---

## 1. Che cosa cambia per l'utente

⭐ **Il puntatore va dove lo mette lui, il tasto che preme arriva alla finestra, la lettera esce
e la rotella scorre nel verso giusto** — misurato dal lato che riceve, su una finestra vera aperta
dentro la sessione di `prova`.

⚠ E la riga onesta accanto: qui è misurato **il tratto `input_*()` → compositore → finestra**. Il
tratto che sta prima — browser → filo → socket → `input_*()` — l'ha cucito il coordinatore lo
stesso giorno; ⛔ **il numero dell'anello intero (input → vetro) lo dà A10, non questo banco**.

---

## 2. Serve una decisione di Nic?

⛔ **No, nessuna.** Tutto quel che c'era da decidere era già deciso (`RCP.md` §7.3 per il segno,
§11 per il rilascio) e qui è stato **misurato**, non scelto.

⚠ Ma c'è **una domanda tecnica che non è mia** e che il coordinatore deve girare a chi tocca —
non serve Nic: **chi decide la misura della tela** ora che non la dà più la sessione (`RCP.md`
§4.5, domanda aperta n.1 della fase 4). `input.c` la riceve da fuori e, se la regione di `libei`
non è grande come la tela, **scala e lo dichiara** invece di decidere da sé. Vedi §5.

---

## 3. Che cosa ho MISURATO — e i quattro `[R]` portati a `[M]`

Tutto `[M]` **14 agosto 2026**, macchina di prova **192.168.0.2**, utente **`prova`** (uid 1001),
sessione `gnome-shell --headless --no-x11` **senza `--virtual-monitor`**, **libmutter 48.7**,
**libei 1.3.901**, **wayland 1.23.1**, `wl_seat` versione **8**.
Si ricontrolla con `bash banchi/04-b24-lancia.sh` sul server; i due registri sono
`/tmp/04-b24/04-b24-visto.jsonl` (quel che la finestra ha visto) e `/tmp/04-b24/iniettore.log`.

### 3.0 ⛔ Come si è misurato, perché è la metà che conta

**Dal lato che riceve** (`CODER.md` §3.8), e il testimone è **`banchi/04-b24-testimone.c`**: una
finestra Wayland vera, a schermo intero **sul `wl_output` della misura che abbiamo montato noi**,
che stampa una riga JSON per ogni `wl_pointer`/`wl_keyboard` che il compositore le consegna.
⛔ Il registro dell'iniettore *non è* la misura: dice che abbiamo chiamato una funzione.

⭐ **E il monitor non si spera, si sceglie per misura**: la sessione di `prova` aveva già un
monitor `Meta-0` 1920×1080 di un altro client; il nostro `RecordVirtual` monta **`Meta-1`
1600×900**, e il testimone si mette a schermo intero su *quello*. Senza questo, ogni iniezione
sarebbe andata sul monitor sbagliato — la forma **E2** che ha reso verde il banco di F2.2 mentre
la cattura riceveva zero fotogrammi.

### 3.0-bis ⛔⛔ IL BANCO È CERTIFICATO — cioè gli è stato fatto vedere il difetto

`CODER.md` §3.3: *«il banco si certifica prima della misura»*, e §4.6: *«il verde non è vero»*. Il
banco ha **due guasti innestabili**, che toccano una **copia** di `input.c` e mai il prodotto
(`GUASTO=…` in `banchi/04-b24-lancia.sh`; se la copia risulta identica all'originale il banco
**si rifiuta di girare**, perché un guasto che non cambia niente certifica il nulla):

| guasto innestato | che cosa cambia | il banco ha detto |
|---|---|---|
| **`GUASTO=segno`** — si toglie il meno da `input_rotella` | `+120` non viene più invertito | ⛔ **ROSSO**: *«+120 (utente IN SU) → axis_value120=**+120** > 0, cioè il contenuto SCENDE: lo schermo remoto scorre AL CONTRARIO»*. E la riga del mezzo scatto è rimasta verde, cioè il banco ha accusato **il segno** e non «qualcosa» |
| **`GUASTO=conto`** — `input_rilascia_tutto()` ritorna 0 senza rilasciare | il Ctrl resta giù | ⛔ **ROSSO** su tre righe: il numero sbagliato, ⭐ **«la finestra NON ha visto il rilascio del tasto»** e il conto che resta a `tasti_premuti=1 pulsanti_premuti=1` |

⇒ ⭐ **Il banco accusa il difetto quando c'è, e con la ragione giusta.** Solo dopo questo il verde
del giro sano vale qualcosa. I tre giri stanno in `banchi/04-b24-esiti.txt`,
`banchi/04-b24-certifica-segno.txt` e `banchi/04-b24-certifica-conto.txt` — ⛔ **depositati nel
deposito perché il rootfs della macchina di prova vive in RAM e si azzera al riavvio**
(`LEZIONI.md` §2.5-bis).

**Il giro sano: 27 righe `OK`, zero `NO`, zero `??`, 65 eventi visti dalla finestra.**
Il registro completo del testimone è in `banchi/04-b24-visto.jsonl`, quello dell'iniettore in
`banchi/04-b24-iniettore.log`.

### 3.1 ⭐ `[R]` → `[M]` — il `mapping-id` è di Mutter, e v1 era INVERTITO *(tesi 4)*

| | |
|---|---|
| quello che **dichiariamo** noi a `RecordVirtual` | `277896a5-dd3d-44c1-880f-e5c1456ef5fc` |
| quello che **Mutter pubblica** nei `Parameters` del flusso | `d72788c1-df86-4246-aa4c-01ec19f507a2` |
| quello che **la `ei_region` porta** | ⛔ **il secondo** |

⇒ La tesi è **vera**. `handle_record_virtual` legge `cursor-mode` e `is-platform` **e basta**: la
nostra proprietà `mapping-id` è ignorata **in silenzio**. ⛔ **`compositore_mapping_id` di v1
cercava la regione con l'UUID nostro, quindi non la trovava mai** e cadeva ogni volta sul ripiego
«prendo la prima» — verde con uno schermo, storto con due. Riusare v1 alla lettera qui avrebbe
prodotto un puntatore che finisce sull'altro monitor.

`src/mutter.c` ora espone `mutter_mapping_id_pubblicato()`, e `input.c` riconosce la regione
**per chiave**, con un ripiego per geometria e uno «regione unica», ⛔ **ciascuno dichiarato nel
registro** e nessuno «prendo la prima».

### 3.2 ⭐⭐ E il fatto che nessun documento diceva: **la regione NON è all'origine**

```
regione 0: 1920,0  1600x900  (mapping-id «d72788c1-…»)
```

⛔ La regione del nostro monitor comincia a **x = 1920**, perché `Meta-0` sta a sinistra. ⇒ Chi
passasse a `ei_device_pointer_motion_absolute` la coordinata della tela **così come è arrivata**
manderebbe il puntatore **sull'altro monitor**, e senza errore. `input.c` somma l'origine della
regione, e con regione grande come la tela **quella somma è l'unica operazione**: nessuna scala,
nessun arrotondamento — che è ciò che `RCP.md` §7.3 pretende.

**Verificato dal testimone**, tre punti compresi i due estremi:

| chiesto | visto dalla finestra |
|---|---|
| `punta 100 100` | `100.0, 100.0` |
| `punta 1599 899` (l'angolo, `tela−1`) | `1599.0, 899.0` |
| `punta 800 450` | `800.0, 450.0` |

### 3.3 ⭐ `[M]` — IL SEGNO DELLA ROTELLA, nei DUE versi

| il client manda (`RCP.md` §7.3) | la finestra riceve | che cosa vuol dire |
|---|---|---|
| **`+120`** — l'utente gira **in su** | `axis_value120 = **−120**`, `axis = −10.0` | il contenuto **sale**: giusto |
| **`−120`** — l'utente gira **in giù** | `axis_value120 = **+120**`, `axis = +10.0` | il contenuto **scende**: giusto |

⛔ **I due versi danno segno opposto**, che è la cosa che «qualcosa si muove» non dimostra. ⇒ La
tesi 1 è **vera e in vigore**: l'inversione dell'asse verticale sta in `input_rotella()`, in un
posto solo.

⚠ **Il ponte con la misura del 10 agosto è `[S]`, non `[M]`.** Allora si misurò `deltaY` di un
evento `wheel` in Firefox; qui si misura `wl_pointer.axis`, un piano più in basso. Le due si
legano con la convenzione che la specifica di Wayland fissa — *«the value is positive in the
direction the content moves»* — quindi `axis` positivo ⇔ `deltaY` positivo ⇔ la pagina scende.
⛔ Chi vuole la catena intera rifaccia `banchi/01-s7-rotella.sh`; qui il browser non ha funzionato
(§4).

**E l'orizzontale, misurato anche lui nei due versi**: `+120 → v120 = +120`, `−120 → v120 = −120`
sull'asse 1. ⇒ ⭐ **l'orizzontale passa così come è**, e il contratto che dice «si inverte solo il
verticale» è giusto — non per simmetria dedotta, per misura.

### 3.4 ⭐ `[R]` → `[M]` — i mezzi scatti NON si perdono *(tesi 2)*

`rotella 0 60` (mezzo scatto) → la finestra riceve **`axis_value120 = −60`**, `axis = −5.0`.

⇒ La tesi è **vera**: con `ei_device_scroll_discrete` quel 60 sarebbe diventato `60 / 120 = 0` in
una divisione intera e **non avrebbe prodotto niente**. `input.c` va di **`ei_device_scroll_delta`**
con il fattore `120 → 10.0`, dove Mutter forza `SOURCE_WHEEL`, salta l'accumulatore, e la soglia
vera di uno scatto è **60**. ⚠ E il fattore 12 è di **Mutter**, non del protocollo: su KWin
`scroll_delta` non produce nessuno scatto, e `kwin.c` non se lo porterà dietro.

### 3.4-bis ⭐ `[M]` — la LETTERA esce, e la disposizione viene da `libei`

`lettera 97` (`U+0061`, la «a») → `input_lettera` ritorna **0**, e la finestra vede il codice
evdev **30** (`KEY_A`). ⭐ E la disposizione **non l'abbiamo scelta noi**: arriva col dispositivo
tastiera e il registro la nomina —

```
tastiera  disposizione in vigore (consegnata dalla sessione): della sessione [English (US)]
input     KEYMAP CAMBIATA: 68402 byte, impronta ac84656f (era: nessuna) → «… [English (US)]»
…                                                                        → «… [German]»
```

cioè il giro del ricambio (§3.5) si legge **anche** come il nome della disposizione che cambia.

⚠ **Una riga che chi legge il registro deve sapere**: `input.c` chiama
`tastiera_apri_da_keymap(testo, misura, **NULL**, …)`. Con `negoziata = NULL` il confronto fra la
disposizione dichiarata dal client in `ATTACCA` e quella vera **non si fa mai**, quindi la riga
`RIPIEGO DICHIARATO` di `tastiera.c` ⛔ **non uscirà mai** — e «non è mai comparsa» non vuol dire
«combaciano sempre». Il giorno che `input.h` porterà fin qui la disposizione negoziata basta
passarla al posto di quel `NULL`; il commento è nel codice, sul punto esatto.

### 3.5 ⭐⭐ `[R]` → `[M]` — I DUE RICAMBI SILENZIOSI, riprodotti tutt'e due *(tesi 3)*

⛔ **Riprodotti mentre il dispositivo era in uso**, non provati una volta all'avvio:

| ricambio | come si è provocato | che cosa si è visto | dopo, funziona? |
|---|---|---|---|
| **keymap** | `gsettings set …input-sources sources "[('xkb','de')]"` a dispositivo vivo | ⭐ il modulo rilegge la keymap: **68 403 → 70 138 byte**, `ricambi_tastiera 0 → 1`; e **la finestra riceve una `wl_keyboard.keymap` nuova**, cioè lo vede anche il lato che riceve | ✅ `KEY_A` arriva ancora |
| **geometria** | il flusso PipeWire si rinegozia da **1600×900 a 1280×720** a dispositivo vivo | ⭐ `ricambi_puntatore 0 → **2**` (l'assoluto viene distrutto e ricreato due volte) | ✅ `punta 640 360` → la finestra vede **640,360** |

⇒ Le tesi sono **vere**, e ⭐ **il codice le regge**, perché rilegge keymap **e** regioni a **ogni**
`DEVICE_ADDED` e prende sempre l'ultimo dispositivo arrivato. Un modulo che leggesse una volta
all'avvio sarebbe rimasto attaccato a un oggetto morto **senza un errore da nessuna parte**.

> ### ⛔ E il contatore dei ricambi era CIECO al primo giro — `CODER.md` §3.4 in atto
>
> `ricambi_puntatore` contava solo quando arrivava un dispositivo **diverso** da quello tenuto. Ma
> Mutter manda `DEVICE_REMOVED` **e poi** `DEVICE_ADDED`: al momento dell'aggiunta il vecchio è già
> `NULL`, e il contatore ⛔ **restava a zero**. Il banco stampava *«il ricambio NON è stato
> riprodotto»* **mentre il testimone vedeva il posto perdere tastiera e puntatore**. ⇒ Il conto si
> tiene sulla **rimozione**. Un banco verde su strumento cieco, trovato perché il lato che riceve
> diceva un'altra cosa.

### 3.6 ⭐⭐ `[M]` — IL RILASCIO AL DISTACCO, con il conto e con l'evento

`RCP.md` §11 — *«la regola col rapporto danno/costo più alto del documento»*:

| | |
|---|---|
| si tiene giù `KEY_LEFTCTRL` (29) **e** `BTN_LEFT` (272) | il modulo dice `tasti_premuti=1 pulsanti_premuti=1` |
| `input_rilascia_tutto()` | ritorna **2**, ed è il numero giusto |
| ⭐ **e dal lato che riceve** | la finestra vede `{"codice":29,"premuto":0}` **e** `{"bottone":272,"premuto":0}` |
| dopo | `tasti_premuti=0 pulsanti_premuti=0` |

⛔ **Non è solo il conto: è l'evento.** Un conteggio che torna a zero senza che il rilascio esca
sarebbe la stessa cosa di non rilasciare niente, e nel registro avrebbe lo stesso aspetto.

⚠ **E la metà che resta aperta, dichiarata invece che taciuta**: alla fase 4 **non c'è ancora una
sessione a cui riattaccarsi**. Il «si riattacca a verificare che il Ctrl non sia rimasto giù» è
della **fase 5**. Qui si misurano il conteggio e l'evento.

### 3.7 `[M]` — il controllo del silenzio

Dieci secondi senza iniettare: **zero** righe nuove sul testimone, con lo strumento che nello
stesso giro ne aveva già registrate **42** — cioè un contatore che **sa vedere** quel che c'è, non
un'assenza di righe.

### 3.8 `[M]` — e le cose che nessuno aveva chiesto, ma che chi viene dopo deve sapere

| | |
|---|---|
| ⛔ **senza un consumatore PipeWire il dispositivo assoluto non nasce affatto** | il flusso diventa *configured* dentro `..._src_enable`, cioè **quando qualcuno legge davvero**; senza viewport `add_viewport_devices` esce in silenzio (`FIXME: should be an error`). ⇒ **il banco dell'input deve consumare video**, o misura un silenzio e lo chiama difetto |
| i tre dispositivi che Mutter crea | `remotix virtual pointer` (relativo, **zero regioni**), `remotix virtual keyboard`, `remotix shared virtual absolute pointer` (**una regione**). ⛔ Si prende il terzo: col relativo il puntatore finisce dove capita |
| ⛔ la keymap di Mutter **non ha nome** | porta `xkb_symbols "(unnamed)"`. Un banco che cercasse un cambio di *nome* resterebbe verde: si prende **misura in byte più una somma di controllo** |
| con una sessione di cattura, i viewport vengono **dai nostri flussi** | due monitor in sessione, e `libei` annuncia **una regione sola**: il puntatore può raggiungere solo il nostro schermo |
| `ConnectToEIS` prima di `Start` | funziona, ed è l'ordine del riferimento. ⚠ `[R]` dice che regge anche l'inverso, perché `initialize_viewports` è chiamata da chi arriva secondo |
| `input_ritela()` | esercitata: `ritela 1280 720` dopo il ricambio di geometria, e il puntatore continua ad arrivare al pixel giusto |

### 3.9 ⚠ La tesi 5 resta `[R]`, e si dice invece di far finta

*«`transform_position` che fallisce non è un errore: una riga di log, e il metodo D-Bus ritorna con
successo»* — ⛔ **non misurata, e non è per pigrizia**: quel fallimento vive sul percorso **D-Bus**
(`NotifyPointerMotionAbsolute`), e ⭐ **noi non lo usiamo**: `input.c` passa tutto da `libei`. Il
gemello che ci riguarda sul nostro percorso è un altro, ed è `[R]`: `find_viewport` che non trova
la regione fa `return` **silenzioso** (`meta-eis-client.c:470-472`). ⇒ È coperto per costruzione:
`input_puntatore()` ritorna **−1** senza mandare niente se la regione non è nota, e il registro
dice quante regioni c'erano e con che chiave.

---

## 4. ⛔ Che cosa NON ha funzionato

1. ⛔⛔ **IL BROWSER — lo strumento di misura già certificato — non funziona in questa sessione.**
   Il banco doveva essere quello di S7: una pagina in Firefox `--kiosk` che misura `deltaY`.
   `[M]` 14 agosto: Firefox **parte e non chiede mai la pagina**. Processo vivo, stato `S`, ⛔
   **zero richieste HTTP dopo 149 secondi**, registro di Firefox **vuoto**. Provato **cinque
   volte**: profilo nuovo, profilo riusato, con e senza pseudo-terminale, con e senza `LANG`.
   ⚠ **La causa non è stata trovata.** ⇒ Il testimone è diventato una finestra Wayland nostra
   (`04-b24-testimone.c`), che è più vicina alla verità — fra `libei` e la pagina c'erano Mutter
   *e* il browser — ⛔ **ma il ponte con `deltaY` scende da `[M]` a `[S]`** (§3.3).
   **Resta aperto**: chi rifà S7 per gli altri compositori (la fase di KDE, la 11) troverà questo muro.

2. ⛔ **Il contatore dei ricambi era cieco**, e il banco ha stampato «non riprodotto» su un
   difetto che era avvenuto (§3.5). Trovato dal lato che riceve, non da una rilettura.

3. ⛔ **Il mio controllo del fuoco diceva NO e OK nella stessa schermata.** Puntava il puntatore
   dove **già stava**, e Wayland non emette `motion` se la posizione non cambia: «stessa
   posizione» e «non consegnato» hanno lo stesso aspetto (`CODER.md` §3.10). Curato puntando a un
   posto diverso.

4. ⛔ **La prova del rilascio, al primo giro, girava DOPO i due ricambi** e falliva: il testimone
   aveva perso il fuoco (`FUOCO dentro:0`) e poi il posto aveva perso tastiera e puntatore. ⇒ Il
   banco accusava **la cosa sbagliata**, che è il peggiore dei rossi. Spostata prima dei ricambi,
   con un controllo positivo sul fuoco davanti.

5. ⛔ **Tre giri buttati sull'impalcatura, non sul prodotto**: `printf | sudo -S` si rompe appena
   il comando ha una redirezione addosso (la fifo prende il posto della pipe); `sudo -v` una volta
   sola non regge tre passi più in là; un raccoglitore superstite del giro prima teneva la porta e
   il controllo `pgrep` **passava lo stesso** perché vedeva quello vecchio. Tutte e tre scritte
   dentro `04-b24-lancia.sh`, dove il prossimo le legge.

6. ⚠ **`tastiera_apri_da_keymap()` non era ancora attuata** in `src/tastiera.c` al primo giro:
   `src/tastiera.h` la dichiarava, `src/input.c` la chiamava com'è giusto, e il **collegamento
   del banco si fermava**. ⇒ Nel banco (⛔ **non** nel prodotto) è rimasta una definizione `weak`
   che apre la disposizione per nome e **stampa una riga che marca `[?]` ogni misura sulle
   lettere**. Per un giro intero `LETTERA` è valsa `[?]`.
   ⭐ **Chiuso**: A5 ha consegnato, il simbolo forte vince su quello debole, e all'ultimo giro
   ⛔ **la riga «RIPIEGO DEL BANCO» non compare più** ⇒ le lettere salgono a `[M]` (§3.4-bis).
   ⚠ Il `weak` resta nel banco come rete: se un domani quel simbolo sparisse, il banco lo
   **direbbe** invece di non collegarsi e basta.

7. ⚠ **`systemctl --user show-environment` ha risposto vuoto** dentro una sostituzione di comando
   dello script, mentre la stessa riga a mano dava `WAYLAND_DISPLAY=wayland-0`. Causa non trovata:
   il banco ora chiede su **tre strade** e dichiara quale ha risposto.

8. ⛔ **Il banco azzerava il registro del testimone quando lo riapriva** dopo il ricambio di
   geometria, e con quello ⛔ **spariva la prova di metà del giro** — le righe del segno, dei
   pulsanti, del rilascio. Il primo deposito ne ha portate **16 su 45**. Curato: si appende, e
   tutte le ricerche lavorano già per numero di riga. ⚠ È la forma «lo strumento cancella la
   propria misura», e si è vista soltanto perché la misura si è **depositata** invece di lasciarla
   sulla macchina.

9. ⚠ **`banchi/04-b24-pagina.html` e `04-b24-raccogli.py` sono stati scritti e poi TOLTI.** Erano
   la strada del browser; morto quello, tenerli avrebbe lasciato in `banchi/` due strumenti che
   sembrano vivi e non lo sono. Chi riprende la strada della pagina parta da
   `banchi/01-s7-pagina.html`, che è certificata.

10. ⛔⛔ **E la cura del punto 8 ha aperto il difetto opposto, che è peggiore: il banco leggeva
    il verde di IERI.** Smesso di azzerare il registro del testimone, il controllo di prontezza
    (`grep '"tipo":"PRONTA"'`) trovava il `PRONTA` del **giro precedente** e dichiarava pronto un
    testimone **non ancora nato**. Risultato: due righe `NO` su difetti inesistenti, e ⛔ **una
    delle due accusava il prodotto** — *«dopo il ricambio il puntatore NON si muove più: il
    difetto è vivo»*, che era falso.
    ⭐ È `LEZIONI.md` §1.9 punto 8 alla lettera: *«un file di ieri risponde sì a "esiste?"
    esattamente come uno di adesso»*. ⇒ Il registro si azzera **una volta per giro** e la
    prontezza si cerca **dopo la riga corrente**, mai con un `grep` su tutto il file. Le due cure
    tirano in direzioni opposte e stanno scritte **insieme** dentro `04-b24-lancia.sh`, perché il
    prossimo non ne applichi una sola.

---

## 5. Le cuciture — chieste, e ⭐ **tutte accolte lo stesso giorno**

> ⭐ *Chiuse dal coordinatore il 14 agosto 2026, con la sua metà già in vigore. Qui restano
> scritte per intero perché la ragione di ciascuna è una misura, e la ragione non si butta quando
> la richiesta è accolta.*
>
> | | esito |
> |---|---|
> | **5.1** `input_descrittore()` | ⭐ nel contratto **e già nel `poll()` del figlio**, con `libei` servito per primo. ⛔ **Attuata qui**: era dichiarata e non definita, e il prodotto non si collegava |
> | **5.2** contratto del thread | scritto in testa a `input.h` |
> | **5.3** `figlio.c` passa la sessione | fatto |
> | **5.4** la tela negoziata | ⚠ **non chiudibile qui**: la risposta l'ha misurata **A1** — la misura non la decide `RecordVirtual`, la decide **il nostro formato PipeWire** `[R]`, e oggi la tela concessa è una promessa che nessuno mantiene (`[M]`: client a 1280×720 ⇒ **145 fotogrammi prodotti, 0 spediti**, client nero senza errori). ⇒ La cura è della **fase 6**. ⭐ E il comportamento di `input.c` resta quello giusto: **se la regione non è grande come la tela, scala e lo DICHIARA** — non decide |
> | **5.5** `input_ritela()` | resta, con la ragione misurata qui (§5.5) riscritta nel contratto |
> | **5.6** `input_conto()` | resta **fuori** dal contratto: la legge solo il banco |



### 5.1 ⛔ Il descrittore per il `poll()` — e senza, il figlio deve girare a vuoto

```c
int input_descrittore(Input *);   /* ⭐ accolta, e ATTUATA in src/input.c */
```

Senza, l'unica strada è chiamare `input_gira()` a intervalli, che è **latenza aggiunta sul
percorso dell'input** — e il terzo numero di `CODER.md` §1-bis (tetto 50 ms) è precisamente quello
che paga. ⚠ Il banco sonda ogni 50 ms e per misurare va bene; nel prodotto no.

⚠ **E una riga che chi la usa deve avere sotto gli occhi**: è un descrittore da **sorvegliare**,
non da leggere. Chi lo mette nel `poll()` non ci fa `read()` sopra — quando diventa leggibile
chiama `input_gira()`, l'unico posto dove `ei_dispatch()` può stare. Un byte tolto a mano da sotto
i piedi di `libei` sarebbe l'ennesimo difetto che non dà errore.

### 5.2 ⛔ Il contratto del thread va SCRITTO, perché è un difetto che non dà errore

`libei` non è rientrante. **Tutte** le funzioni di `input.h` vanno chiamate dallo **stesso** thread
che chiama `input_gira()`. Oggi non è scritto da nessuna parte, e due thread su uno `struct ei`
sono un difetto che non dà errore. ⇒ Chiedo una riga in `input.h`.

### 5.3 ⭐ Quel che `figlio.c` deve passare a `input_apri()`

```c
Input *canale = input_apri(sessione /* MutterSessione*, da mutter_apri() */,
                           tela_l, tela_a, &errore);
```
e le due nuove di `src/mutter.h`, che sono mie e sono già in vigore:
```c
int         mutter_eis_fd(const MutterSessione *);            /* -1 = niente input, e il registro dice perche' */
const char *mutter_mapping_id_pubblicato(MutterSessione *);   /* la chiave VERA della regione */
```
⚠ `mutter_apri()` **non fallisce** se `ConnectToEIS` è rifiutata: dichiara e va avanti, perché una
sessione che si guarda vale più di nessuna sessione (`CODER.md` §4.2). ⇒ È `input_apri()` a
fallire, con un errore che rimanda al registro dell'area «cattura».

### 5.4 ⛔ `tela_l`/`tela_a` devono essere la misura NEGOZIATA, non quella chiesta

⛔ **Se la regione di `libei` non è grande come la tela, `input.c` scala e lo dichiara** — e quella
è una decisione che questo modulo **non dovrebbe prendere**. La domanda è `RCP.md` §4.5 (la tela
concessa) e la domanda aperta n.1 della fase 4. ⇒ Chi cuce deve passare la misura **negoziata con
PipeWire** (quella che `cattura.c` conosce), non quella che il client ha chiesto — e quando il
client ne chiede un'altra, chiamare `input_ritela()`.

### 5.5 ⚠ `input_ritela()` resta necessaria, e adesso si sa perché

Il `[?]` del contratto — *«forse `input_gira()` basterebbe già»* — è **mezzo chiuso**:
⭐ `[M]` le **regioni** si rileggono da sé a ogni `DEVICE_ADDED`, e dopo un cambio di geometria il
puntatore continua ad arrivare al pixel giusto **senza che nessuno chiami niente**;
⛔ ma la **tela** è un numero del *client*, e `libei` non ne sa nulla: nessun `DEVICE_ADDED`
arriverà mai per un `TELA(ADATTATA)`. ⇒ La funzione serve, e la sua ragione è la seconda metà, non
la prima.

### 5.6 ⚠ E una che non è una cucitura ma va detta

`src/input.c` espone `input_conto()` — il conto di quel che è premuto e il numero dei ricambi —
che **non sta in `input.h`** di proposito: la legge solo il banco, che la dichiara `extern`. Se il
coordinatore la vuole nel contratto, la firma è nel file.
