# La tela che cambia — la catena scritta, refutata e misurata

⭐ **Notte del 15 agosto 2026.** Il mandato di `F4-IN-12` era uno solo: *«scrivere la catena
`figli_ritela()` → `cattura_ridimensiona()`»*, con davanti un blocco dichiarato — *«non sono
riuscito a costruire il C»*. Questo rapporto dice come è andata: il blocco sciolto, la catena
scritta, **dieci difetti trovati refutandola**, e le misure dal vivo.

---

## 1 · ⛔ IL BLOCCO DELLA COSTRUZIONE, SCIOLTO — e non serviva l'utente

`F4-IN-12` §3 chiudeva così: *«La prima domanda alla prossima sessione è all'utente: come si
costruisce questo progetto?»*. La domanda non è stata fatta, perché la risposta si poteva
**misurare**: le tre strade morte erano tre, e la quarta non era stata provata.

| dove | esito |
|---|---|
| portatile `CHUWI`, a mano | ⛔ mancano `nghttp3`, `ngtcp2` e `libswscale` |
| macchina di prova (`192.168.0.2`) | ⛔ niente `gcc`, niente `make`: il rootfs è live in RAM |
| dentro `enter.sh` con i sorgenti in `/srv/src/…` sull'**host** | ⛔ `/srv/src` **dentro** il chroot è `/media/REMOTIX/src`, non `/srv/src` dell'host: era un errore di percorso, non un mancato montaggio |
| ⭐ **`podman` da utente, sul portatile** | ✅ **funziona**, e non chiede `sudo` |

⇒ **Due strade, tutt'e due vive, e vanno dette insieme perché rispondono a due domande diverse:**

- `src/Contenitore` + `src/costruisci-in-contenitore.sh` — **sul portatile, senza `sudo`**: podman
  monta l'albero, dentro c'è tutto (ngtcp2 1.25 e nghttp3 1.18 costruiti dai sorgenti
  nell'immagine), e il binario esce **dell'utente**. Serve a *compilare mentre si scrive*: quattro
  minuti la prima volta, venti secondi le successive. ⛔ Il binario che ne esce è legato alle
  librerie di `/usr/local` **dentro l'immagine**: non si copia sulla macchina di prova.
- `src/costruisci.sh` dentro `bash /media/REMOTIX/enter.sh --root …` — **sulla macchina di prova**,
  con i sorgenti in `/media/REMOTIX/src/04-vero-src/`. Serve a *far girare*: il binario si lega a
  `/media/REMOTIX/src/b2`, che è quel che `riavvia-7700.sh` pretende.

⚠ **E «compila» non è «gira»**: la prima strada dice che il codice è corretto per il compilatore,
la seconda che esiste un binario che la macchina di prova sa eseguire. Stanotte si sono usate
tutt'e due, in quest'ordine, dieci volte.

---

## 2 · ⭐ LA CATENA, per nome — e la risposta torna indietro

```
pagina.html  chiedi_tela()            ADATTA_TELA(l, a)  ─────────┐
                                                                  ▼
rcp.c        T_ADATTA_TELA   §4.5: limiti, parità, video.misura_massima
                             ⛔ NON risponde: segna «in volo»
                                                                  │
webtransport.c → main.c → figlio.c   figli_ritela()               │  confine
                                     MSG_INPUT / RITELA           │  di processo
                                                                  ▼
figlio.c (figlio)  cattura_ridimensiona() → pw_stream_update_params()
                                                                  │
                   … il compositore rinegozia, e arriva un FOTOGRAMMA
                                                                  │
figlio.c           riconciliazione: codificatore riaperto, puntatore
                   rimappato, tela_l/tela_a = quel che i pixel SONO
                   MSG_TELA (voluta, avuta) ────────────────────► │
                                                                  ▼
rcp.c        rcp_tela_dal_palco()    TELA(ADATTATA, la misura VERA)
```

⛔ **La riga che conta è la penultima.** La prima stesura di stanotte non aveva `MSG_TELA`: il padre
**indovinava** l'esito dai fotogrammi — *«se ne arriva uno di misura diversa, il palco ha
obbedito»*. Sembrava fedele al principio («la verità la dice il fotogramma»), ⚠ e sbagliava: dal
fotogramma si vede *che* la misura è cambiata, **non a quale richiesta risponde**.

---

## 3 · ⛔⛔ I DIECI DIFETTI TROVATI REFUTANDO — e nessuno con un banco verde

Quattro agenti, mandato **avversariale** (`«parti dall'ipotesi che sia falsa e cerca la prova»`),
su quattro fronti: la macchina a stati, il figlio e la cattura, la pagina, e le regole scritte.
⭐ **Tre affermazioni su quattro sono state smentite.** In ordine di gravità:

| # | il difetto | che cosa avrebbe fatto all'utente |
|---|---|---|
| 1 | ⛔ la guardia sui byte del fotogramma copriva un verso solo (`byte ≥ passo × altezza`) e non l'altro (`passo ≥ larghezza × 4`) | **lettura oltre la memoria copiata** quando la tela si ALLARGA ⇒ il figlio muore e si porta via il palco, l'input e la sessione |
| 2 | ⛔ il `TELA` **non richiesto** quando il palco cambia da sé | §6.2 non dà al client nessun modo di accettarlo ⇒ `ERRORE_PROTOCOLLO`: **sessione chiusa in cui nessuno ha sbagliato** |
| 3 | ⛔ due `ADATTA_TELA` incatenate: il fotogramma della prima preso per la risposta della seconda | il desktop si assesta sulla misura **sbagliata**, coi conti dei messaggi in ordine ⇒ bande e testo interpolato, e niente che lo dica |
| 4 | ⛔ il ritorno a una misura **già stata in vigore** con una richiesta in volo | il client chiudeva la sessione per aver trascinato un bordo e averlo rimesso dov'era |
| 5 | ⛔ la guardia di `STUDI.md` §kde §8.2-bis confrontava il **chiesto** invece dell'**attuale** | dopo un tentativo andato a vuoto, «adatta il desktop» **non funzionava più**, per sempre |
| 6 | ⛔ `ADATTA_TELA` non rispettava `video.misura_massima` (§4.5) | su un client hi-dpi: tela che il decodificatore non regge ⇒ **schermo nero senza ritorno** |
| 7 | ⛔ i limiti della tela erano 200..8192 invece dei 320×240..7680×4320 di §4.5 | una tela concessa da `TELA` veniva **rifiutata da `ATTACCA`** al ri-attacco |
| 8 | ⛔ `cattura->guasto` letto **dopo** aver mollato il lucchetto | lettura di memoria liberata, proprio mentre la sessione grafica muore |
| 9 | ⛔ `pw_stream_update_params()` **sostituisce** la lista dei parametri | il metadato del **cursore** poteva sparire, e `CURSORE_FORMA` tornare un canale senza sorgente |
| 10 | ⛔ le chiavi tenute (`tenuto[]`) restavano alla misura vecchia | `RIMANDA_PALCO` spediva pixel di una misura dichiarandone un'altra |

⚠ E altri sei minori, tutti corretti: `palchi[]` mai svuotata e con il nome troncato a 64 caratteri,
la riapertura del codificatore ritentata a ogni fotogramma (la forma dei 30,8 GB di registro), il
`schermo.sessione` che col worker restava falso di qua, l'interruttore leggibile solo da `?`, il
mittente `ADATTA_TELA` vivo dopo la fine della sessione, i due campi di `TELA(RIFIUTATA)` buttati.

⭐⭐ **La riga di metodo**: nessuno di questi dieci sarebbe uscito da un banco verde, e otto sono
**nati stanotte insieme alla cura**. Quel che li ha trovati è un mandato che chiedeva di
**smentire**, non di verificare — e che ammetteva il rifiuto.

---

## 4 · ⭐ IL BANCO, e la sua certificazione

`banchi/04-b31-tela.c` monta `rcp.c` **nudo**, con un palco finto che si può far rispondere in
ritardo, concedere altro, o non rispondere affatto. **17 casi**, ciascuno con l'atteso dichiarato
prima.

`banchi/04-b31-certifica.sh` innesta **10 guasti** in una copia di `rcp.c` e pretende che i casi
**attesi** diventino rossi — non «che diventi rosso qualcosa»:

```
OK  controllo POSITIVO: sul codice intatto il banco e verde
OK  G1-risposta-subito       ROSSI i casi 1,3,4,14,15,16
OK  G4-riconosce-la-risposta ROSSI i casi 14
OK  G8-tela-non-richiesta    ROSSI i casi 9,14
…  ⭐ tutti i guasti innestati diventano rossi
```

⚠ **E due attesi erano sbagliati**, non il banco: G1 accendeva sei casi e ne avevo dichiarati dieci,
G9 restava verde perché un **secondo** controllo mascherava il guasto innestato nel primo. Corretti
sulla misura, con la ragione scritta accanto (`LEZIONI.md` §1.11).

---

## 5 · `[M]` LE MISURE, dal vivo — macchina di prova, utente `prova`, GNOME headless

| | 14 agosto | 15 agosto |
|---|---|---|
| ⭐⭐ dal canale video al primo fotogramma | **4,4 s** (659 «attese a vuoto») | **311 ms** |
| tela in vigore all'attacco | 1920×1080 fissa | **1264×800** = la finestra |
| scala di disegno del client | 0,658, `imageRendering: auto` | **1,000**, `pixelated` |
| ridimensionamento a caldo 1264×800 → 1000×640 | non esisteva | ⭐ **6 ms** dalla risposta del palco alla chiave spedita |
| ri-attacco a finestra uguale | tela di ieri, fotogrammi scartati | ⭐ `SESSIONE` concede **la tela del palco**, zero scarti |
| fotogrammi scartati per misura · trattenuti · errori | — | **0 · 0 · 0** |

⭐ **La conferma che non viene da noi**: GNOME *Impostazioni → Displays*, **dentro** la sessione
remota, dice **«Resolution 1264 × 800 (3:2)»** e **«Scale 100%»**. E il clic su una voce della barra
laterale colpisce la voce: la conversione delle coordinate è l'identità.

### La cura dei quattro secondi, e perché non è quella che sembra

⛔ Il ridimensionamento **da solo non basta**: al ri-attacco la misura è già giusta, quindi nessuna
`ADATTA_TELA` parte e nessuno riavvia il flusso. ⇒ La cura vera è nel figlio, e vale sempre:

> **quando una chiave è dovuta e la scena è ferma da 400 ms, si riavvia il flusso.**

`[M]` Nel registro della notte: `una CHIAVE è dovuta e la scena è ferma da 400 ms: riavvio il flusso`
→ 31 ms dopo, `TELA NUOVA DAL PALCO` → 30 ms dopo, `fotogramma 1 SPEDITO`.

⚠ `[?]` E resta una marca da chiudere: che la rinegoziazione consegni un buffer **su una scena
ferma** è dedotto dal meccanismo e confermato una volta; non è una misura ripetuta.

---

## 5-bis · ⭐⭐ IL QUARTO DI SECONDO SUL CLIC — e il numero che lo spiegava era nel registro da un giorno

*15 agosto 2026, mattina. L'utente: «ridurre di qualche decimo di secondo il tempo fra il clic e
quando il server riceve l'evento». ⛔ Non era cosmesi: `CODER.md` §1-bis fissa il **tetto a 50 ms**.*

**La misura, sui suoi clic veri** (registro delle 05:25, 25 pressioni, metrica «clic ricevuto →
primo fotogramma spedito»):

```
mediana 136 ms · peggiore 502 ms · migliore 0 ms
```

⛔ **La causa era una riga di `figlio.c` scritta alla fase 3**, e il suo commento la sfiorava:

```c
#define MOVIMENTO_ATTESA_S 0.25   /* quanto si aspetta un fotogramma */
```

Il ciclo del figlio legge i messaggi del padre **prima** dell'attesa. Un clic che arriva un
millisecondo **dopo** che il ciclo è entrato in `cattura_prendi()` resta fermo nel socket per i 249
ms che restano. ⚠ Su un desktop che si muove non si vede: il fotogramma arriva subito e il giro
riparte. Su un desktop **fermo** — che è il caso in cui si clicca — si paga tutto, ogni volta.

⭐⭐ **E il numero stava nel registro da un giorno**, stampato una volta al secondo:

> `ciclo: 4 fotogrammi consegnati, 3 attese a vuoto …`

*Tre-quattro attese a vuoto al secondo* vuol dire *quattro giri al secondo*, cioè *250 ms per giro*.
La riga era stata scritta per rispondere a un'altra domanda («la scena è ferma o il ciclo è fermo?»)
e conteneva la risposta a questa. ⛔ È la stessa forma del 14 agosto — *213 movimenti registrati
mentre l'utente ne vedeva zero* — e ci sono passato sopra per due giorni.

**Dopo**, stessa metrica, stessa scena, stessa macchina (`MOVIMENTO_ATTESA_S` 0,25 → **0,008**):

| | prima | dopo |
|---|---|---|
| clic → primo fotogramma spedito | mediana **136 ms**, peggiore 502 | mediana **41 ms**, peggiore **47** |
| il giro completo misurato dalla PAGINA (`GIRO`) | 135 ms (`[M]` 14 ago, DeX) | **55 ms**, peggiore 71 |
| risvegli del ciclo | 4 al secondo | **122 al secondo** |

⭐ E la **dispersione** è la prova che la diagnosi era giusta: prima i campioni andavano da 0 a 502
ms, adesso stanno tutti fra 34 e 47. Un'attesa casuale fra 0 e 250 ms produce esattamente la prima
distribuzione, e toglierla produce esattamente la seconda.

⚠ **E resta un ripiego dichiarato**: 8 ms di attesa sono 4 ms di ritardo medio *aggiunto*, e 122
risvegli al secondo. La cura vera è non aspettare a tempo — un descrittore che la cattura scrive
quando il fotogramma è pronto, nello stesso `poll()` del socket del padre e di `libei`. ⛔ Non si è
fatta subito perché tocca il posto di scambio di `cattura.c`, che gira sul thread di tempo reale di
PipeWire: è una cura da misurare, non da improvvisare.

---

## 6 · ⛔ QUEL CHE RESTA APERTO — dichiarato, non scoperto

1. ⏳ **`RCP.md` §7.1 non dice che cosa fa il server quando il palco cambia misura da sé.** Oggi
   richiede al palco di tornare, con un'attesa che cresce, e non manda nessun `TELA`: funziona, ma è
   una regola del prodotto che l'arbitro non nomina.
2. `[?]` **Il mezzo pixel del `margin: 0 auto`.** Quando `clientWidth × dPR` è dispari, la tela
   (pari) è mezzo pixel CSS più stretta del contenitore, e `margin: auto` lo divide in due. Con
   `image-rendering: pixelated` uno scostamento di mezzo pixel **potrebbe** sfasare la griglia: da
   guardare sul DeX, sullo stesso terminale del 14 agosto.
3. `[?]` **Il ritardo non è stato rimisurato** dopo questo lavoro: la tela più piccola dovrebbe
   ridurlo (meno pixel da convertire e codificare), e nessuno l'ha verificato.
4. ⚠ **KWin resta fuori**: `SPECIFICHE.md` §6.3 e `DECISIONI.md` §5.0-bis. Su KDE ≤ 6.7.4 la
   risposta sarà `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` — che è vera, e il client la mostra spenta.
5. ⚠ **`banchi/01-b3-cliente.py` e `01-b4-validatore.py` non mandano `ADATTA_TELA`**: il filo non è
   cambiato, quindi restano verdi, ⛔ ma nessuno dei due esercita la strada nuova.

---

## 7 · ⭐⭐ La riga di metodo da portarsi via

> **Il padre indovinava, e l'architettura glielo permetteva.**

La prima stesura deduceva l'esito di una richiesta **da un effetto collaterale** — un fotogramma di
misura diversa — invece di farselo dire da chi lo sapeva. Funzionava in tutti i casi che avevo in
mente, e sbagliava nei tre che non avevo in mente. ⚠ La cura non è stata «più controlli»: è stata
**un messaggio in più**, dal processo che sa al processo che decide.

⇒ *Quando un pezzo deve dedurre qualcosa che un altro pezzo sa già, la deduzione non è un
risparmio: è un difetto che aspetta il caso a cui non hai pensato.*
