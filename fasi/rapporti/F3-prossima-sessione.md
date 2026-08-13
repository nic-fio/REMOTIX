# La sessione nuova — tutto quel che c'è da lavorare

*Scritto la notte del 13 agosto 2026, **a codice fermo**, alla fine della giornata che ha misurato
la fase 3. ⭐ Deciso dall'utente: **la codifica in hardware si anticipa dentro la fase 3**, e la
fase **non si chiude** finché non è fatta.*

⛔ **Questo elenco è il compagno del riquadro «DA QUI SI RIPRENDE» del `README.md`**: là c'è il
*perché*, qui c'è il *che cosa*. Le voci sono in ordine di quando mordono, non di importanza.

---

## A. Prima di cominciare — quattro cose, e due sono bloccanti

| # | | |
|---|---|---|
| **A1** | ⛔⛔ **IL PUNTO CIECO DEL CATALOGO** | **Nessuna certificazione guarda `codificatore.c`. Nessuna. E nemmeno `figlio.c`.** ⇒ Si può riscrivere il codificatore da capo a fondo e il conto direbbe *«15 su 15, tutto verde»*. Non è un difetto nato oggi — è lì da sempre, e si vede **adesso** perché adesso qualcuno sta per toccare quel file. ⭐ **Costa due righe nel catalogo, e va fatto PRIMA di scrivere una riga di codificatore**, o tutta la sessione lavora senza rete |
| **A2** | ⛔⛔ **LO SCOGLIO HEVC** | Il codec negoziato nelle misure di oggi è **AV1**, perché la sonda HEVC di quel Chrome **fallisce su Xvfb** (`EncodingError: Decoding error`). ⛔ **Senza un client che accetti HEVC, l'anello intero non si misura** — al massimo il lato server, e sarebbe **mezzo anello**. ⇒ *Un client che accetti HEVC su questo palco esiste, sì o no?* **È la prima domanda della sessione**: se la risposta è no, cambia tutto il piano di misura |
| **A3** | **Lo stato, verificato e non ricordato** | albero · porte in ascolto (`ss -ltn` **su 192.168.0.2**, non su CHUWI — l'errore è già stato fatto oggi) · `python3 banchi/01-b12-guasti.py --registro` |
| **A4** | ⏳ **La scadenza** | `bash banchi/01-s1b-eccezione.sh oggi`, **una volta al giorno fino al 18 agosto**. Il 13 agosto: 4 controlli su 4, **2,50 giorni su 7**; la scadenza che Chrome si è segnato è il **2026-08-17T21:09:47Z** |

---

## B. Il lavoro principale — la codifica HEVC in hardware

⭐ **`[M]` L'hardware c'è**, verificato il 13 agosto sul server:

```
Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
```

| # | | |
|---|---|---|
| **B1** | la codifica HEVC Main10 via VA-API nel prodotto | ⛔ **su una COPIA** finché non è misurata, mai sull'albero del deposito |
| **B2** | **quale nodo di rendering** | ce ne sono **due** (`renderD128`, `renderD129`): si stabilisce e **si dichiara**, non si indovina |
| **B3** | ⭐ **l'anello rimisurato** | ⛔ **STESSO banco (`03-b17-ritardo.py`) e STESSA scena**, o i due numeri **non si sottraggono** |
| **B4** | ⛔ **i CINQUE tratti affiancati**, non il totale | *tolta la codifica software, gli altri quattro restano dove sono?* Se **restano** → la sottrazione `74,58 − 39,17 = 35,4` è confermata e **l'architettura è assolta**. Se **scendono** (meno contesa) o **salgono** (il pipelining nascondeva qualcosa) → hai trovato più del numero che cercavi |
| **B5** | ⚠ **i fotogrammi consegnati accanto ai millisecondi** | `LEZIONI.md` §6.2: in v1 il costo per fotogramma scese da **41 ms a 6** *mentre i consegnati calavano da **29 a 22,7***. Con un numero solo in mano non si vede |
| **B6** | ⚠ **`EncSliceLP` è la codifica «a bassa potenza»** | veloce, ma con limiti suoi di qualità e di funzioni. **Non è equivalente** alla piena: si dichiara **accanto al numero** |
| **B7** | ⚠ **chiave/delta e `RICHIEDI_CHIAVE` con VA-API** | i codificatori hardware trattano le **chiavi forzate** diversamente da quelli software. `RCP.md` §5.2, il debito di chiave, e il banco `03-b15-movimento.py` vanno **rigirati per controllo** — non perché la certificazione scada, ma perché **è il posto dove guarderei per primo** |
| **B8** | ⭐ **l'occasione dentro l'occasione** | `EncSliceLP` è l'entrypoint che `web.md` nomina come *«da verificare»* per i **sotto-livelli temporali**: la strada per **abbandonare un fotogramma senza rompere quelli dopo**, che oggi costa **una chiave ogni volta** |
| **B9** | ⛔ **che cosa NON si anticipa** | la **copia zero** resta alla fase 8 |

### ⚠ Le certificazioni che scadranno, e perché

**Cinque su quindici** — **B10 · B13 · P1 · P5 · P5R** — ⛔ e **nessuna per colpa del
codificatore**: scadono perché guardano **`remotix/Makefile`**, che cambierà per legare VA-API.
✅ **Reggono**: B3 · B5 · B6 · B7 · B8 (guardano `rcp/rcp.c`) · B9 (`RCP.md`) · B2 · B4 · B11 · C2 ·
03-b14 · 03-b15 · 03-b18 (guardano banchi propri).

### ⚠ Le misure che NON vanno rifatte

Solo **una** va rifatta, ed è tutto il punto: **l'anello del ritardo**.
✅ **Reggono**: la cadenza e la legge della griglia (misurano Mutter) · i fotogrammi dipinti a
saturazione (misurano la pagina, i fotogrammi glieli dà il banco) · la scena · la marca · M6 · M8 ·
B-18 · B-20 · il worker respinto.

---

## C. Rimasto aperto dalla fase 3 — lavoro tecnico

| # | | |
|---|---|---|
| **C1** | ⛔⛔ **I 74,58 ms sono `[M]` o `[?]`?** | `03-b17-ritardo.py --certifica` esce **30 su 31** da CHUWI (3 giri su 3, sempre lo stesso controllo, **del ponte**: *«fuori ordine: 0 inversioni su 40 pacchetti»*), mentre l'autore dichiarava **31/31**. ⇒ Se il controllo che cade **non entra** nel cammino della mediana, il numero regge e va detto **con la prova**; se ci entra, **il numero della fase è `[?]`**. ⭐ **È la domanda più urgente di tutte** |
| **C2** | ⛔ **P5, il fuori ordine, non è mai stato eseguito** | tre iniettori provati: 0 scavalcati su 200 · 0 su 220 · al terzo la pagina smetteva di consegnare. *«`scavalcati = 0` non è "l'anello regge", è "il fenomeno non si è presentato"»*. Serve un fotogramma **grosso** (una chiave) mentre scorrono delta piccoli, o un iniettore che ritardi **un intero stream** invece che dei pacchetti |
| **C3** | **Le marche dei banchi nuovi** | sette sono a catalogo come **MAI PROVATI**, col campo `marca` **vuoto di proposito** — *una marca si misura, e una dedotta dal sorgente è la forma d'errore già pagata su B4 e B7*. ⭐ Su `03-marca` poggia la mediana **74,58 ms**: se ce n'è una che vale, è quella |
| **C4** | **`03-deposita` non è certificabile** | e non per la marca: **nessuno rilegge `03-scena-esiti.jsonl`**, quindi un guasto lascerebbe il giro verde. Il controllo mancante **costa due righe**, ed è in nota nel catalogo |
| **C5** | **`03-b16` vuole una copia ad ALBERO** | e `prepara_copia()` non lo sa fare: va costruita a mano |
| **C6** | ⛔ **Il secondo motore** | `SPECIFICHE.md` §11.5 ne vuole **due**; i numeri sono di **Chrome soltanto**. Firefox non ha CDP e non apre finestre su Xvfb — ⭐ ma i **mattoni** sono verificati su due (`crossOriginIsolated` true anche nel worker, `VideoDecoder`, `WebTransport`, `OffscreenCanvas`, trasferimento di `ReadableStream`). La forma d'errore **E10** è dichiarata, non nascosta |
| **C7** | ⚠ **Propagazione su NIC-OS** | là il conto legge **11/15** perché tre file di *banco* sono vecchi. Non tocca la validità — quei giri sono partiti da CHUWI — ma va allineato |
| **C8** | ⛔ **I commit di `banchi/`** | il prodotto, i documenti e la decisione **sono committati**; ⛔ **`banchi/` no** (~46 voci: nove banchi nuovi, le cure ai vecchi, il catalogo). Erano in scrittura da due gruppi quando la sessione è finita |
| **C9** | ⚠ **`03-b15-lancia.sh`** | usa ancora la porta 7603 e l'ordine vecchio **scena → misura**, che dà **zero fotogrammi** |

---

## D. I due punti che l'utente ha lasciato APERTI di proposito

⛔ **Non sono dimenticanze: sono decisioni.** Tutt'e due per la stessa ragione — *non si decide su
un sintomo temuto invece che osservato* (`LEZIONI.md` §2.6). Il dettaglio sta in
[`../03-movimento.md`](../03-movimento.md).

| # | | come si chiude |
|---|---|---|
| **D1** | **il debito di chiave strozzato a una richiesta al secondo** — `rcp_video_serve_chiave()` non ha chiamanti in `src/`, e ⛔ **un abbandono legittimo ne genera fino a sessanta illegittimi** | ⭐ **leggendo il registro della sessione in cui l'utente dà il giudizio** — il prodotto scrive già ogni abbandono (`RCP.md` §5.1). **Costa zero.** Tre numeri: quante volte scatta · quanti delta per volta · quanto passa fino alla chiave |
| **D2** | **dove finisce di contare il tetto dei 50 ms** — al **disegno** o al **pixel acceso**? Con un codificatore gratis fa **~35,4** al disegno e **51-75** sul vetro: *la stessa architettura è promossa o bocciata a seconda di dove si mette il traguardo* | **dopo la misura in hardware**, con due numeri veri davanti invece di una forbice. ⚠ Il pezzo cieco è a sua volta una `[?]` larga **due volte e mezzo** (16-40 ms). ⛔ **Non scrivere una risposta in `SPECIFICHE.md` prima**: una soglia decisa per prudenza e poi trovata comoda si sposta di un passo a ogni rilettura |

---

## E. E poi, e solo poi

⭐ **Il giudizio dell'utente**: il desktop **che si muove**, dentro una scheda, e lui dice se è
fluido — su un numero che **non ha più il freno a mano tirato**.

⚠ **E il giudizio si dà davanti a un elenco**, come la fase 2: un'approvazione data senza sapere
che cosa manca è un'approvazione al buio.
⛔ **E va ricordato che sono DUE giudizi distinti**: quel che l'utente guarda è **il suo** desktop,
che si muove quando lo muove lui — un'altra scena da quella misurata. ⇒ Il suo giudizio dice *«è
fluido abbastanza»*, e **non conferma né smentisce** il numero dell'anello. Valgono tutti e due,
**separati**.

---

## F. Le trappole già pagate — non si ripagano

*Ciascuna è costata dei giri buttati oggi. Sono qui perché non li costino di nuovo.*

| | |
|---|---|
| ⛔ **la scena deve stare sul monitor che si sta catturando** | il palco ha **quattro** monitor virtuali (`Meta-0…3`, tutti 1920×1080@60): il proprio si legge **dal registro del proprio server**, non si indovina. Una scena sul monitor sbagliato dà **zero fotogrammi per dieci secondi con la catena perfetta**. Costo: **quattro giri** |
| ⛔ **la scena accesa PRIMA della sessione non disegna** | Mutter non manda i *frame callback* a una superficie su un monitor che nessuno registra. Si accende **a sessione aperta** |
| ⛔ **su Xvfb `requestAnimationFrame` non gira MAI** | 0 quadri in 3 s, con e senza GPU, a scheda «visible». Ogni cammino di prodotto che ci passa dietro è **codice morto sul banco** |
| ⛔ **`curl` normalizza** | non manda il frammento e si mangia il `?` vuoto. Sul filo grezzo serve `--request-target`, o si misura curl |
| ⛔ **`&` dentro `ssh → enter.sh → bash -c`** non arriva dove sembra | **si usa un file, non una riga annidata** |
| ⭐ **la parola d'ordine di `sudo` sta in `~/SERVER.ssh`** | convenzione del progetto (`banchi/02-pam-lancia.sh:59`). Un gruppo si è fermato **per non saperlo** |
| ⛔ **il prodotto legge `pagina.html` UNA VOLTA SOLA all'accensione** | dopo ogni modifica **si riaccende**, o si prova la pagina di prima |
| ⛔ **su CHUWI il prodotto NON si compila** | manca `nghttp3/nghttp3.h`. Vive in un contenitore su **192.168.0.2** (`enter.sh`, sorgenti `/srv/src/remotix`); i **browser veri** stanno su CHUWI |
| ⚠ **`/tmp` su CHUWI è una tmpfs da 3,8 G al 94 %** | quando si riempie, Chrome non apre il profilo e il banco fallisce con un errore che **accusa la pagina**. Si guarda il disco **prima** di credergli. ⛔ E dentro ci sono le **prove** dei giri di oggi: si guarda prima di cancellare |
| ⚠ **le porte protette** | **7448** (prodotto di casa) · **7501** (bersaglio di P5) · ⛔ **7561, quella che l'utente apre** — si leggono e **non si toccano** |

---

## G. ⭐⭐ E il metodo, che oggi ha reso più del codice

**Gli agenti si mandano a REFUTARE, non a verificare** — e il conto della giornata lo dimostra:

- **sette cure passate dal coordinatore rifiutate con un caso**, e avevano ragione **tutte e sette**;
- **un difetto attribuito al prodotto era del BANCO** — che annunciava il credito **dopo** la stretta
  di mano, contro RFC 9000 §4.6, e poi accusava il prodotto di non reggerlo;
- **un verde in catalogo lo produceva lo STRUMENTO** — una funzione di stampa opzionale svegliava il
  rendering, e quelle pretese non erano **mai** state innestate con un guasto;
- **tre falsi rossi** trovati nei banchi, che accusavano il prodotto mentre faceva la cosa giusta;
- ⛔ **e DUE righe ripetute invece che misurate hanno quasi deciso un piano**: i «37 fotogrammi di
  Mutter» e *«non c'è un codificatore hardware»*. **La seconda nella stessa giornata in cui si
  scopriva la prima.**

⇒ ⭐ **Zero volte i banchi hanno sbagliato a favore del prodotto.**
⭐ **E il mandato deve ammettere il rifiuto**: la cura che arriva dall'alto può essere sbagliata, e
chi cura deve poterla rifiutare **con un caso** — non con un'opinione.
