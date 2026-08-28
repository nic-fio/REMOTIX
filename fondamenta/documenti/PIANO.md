# PIANO — piano di sviluppo

*Come si costruisce REMOTIX: in che ordine, che cosa si vede alla fine di ogni tappa, e che cosa si
legge prima di cominciarla.*

Documenti di riferimento:

- [`SPECIFICA.md`](SPECIFICA.md) — che cosa si costruisce e perché
- [`REFERENCE.md`](REFERENCE.md) — **le regole da rispettare mentre si scrive** (§7.0 di `SPECIFICA.md`:
  regola vincolante)
- [`LEZIONI.md`](LEZIONI.md) — **quel che GNOME ci ha insegnato e che vale oltre GNOME**: da leggere
  prima di aprire la fase 11, perché è scritto per chi apre un desktop nuovo
- [`protocollo-rdp.md`](protocollo-rdp.md), [`gnome-remote-desktop.md`](gnome-remote-desktop.md),
  [`client-android.md`](client-android.md), [`xrdp-funzionalita.md`](xrdp-funzionalita.md) — lo studio
- [`kde.md`](kde.md) — **lo studio del codice di KDE Plasma e KWin 6.3.6**: da leggere per intero
  prima di scrivere una riga della fase 11

---

## 0. Come è fatto questo piano

**Ogni fase finisce con qualcosa che si guarda.** L'utente non legge il codice: giudica vedendo il
software funzionare (§7 di `SPECIFICA.md`). Una fase che finisce con «il modulo compila» non è una
fase: è un passo interno.

Ogni fase ha cinque voci:

| Voce | Che cos'è |
|---|---|
| **Obiettivo** | in una riga |
| **Si vede** | che cosa l'utente guarda per dire «fatto» |
| **Prima di scrivere** | le sezioni di `REFERENCE.md` da leggere — **vincolante** |
| **Come si prova** | i client, nell'ordine giusto |
| **Rischi noti** | dove ci si aspetta di perdere tempo |

**Le fasi non hanno date.** Hanno una **taglia** relativa: piccola (una sessione di lavoro), media
(qualche sessione), grande (un capitolo a sé).

**La regola dei tre client vale ovunque** (`REFERENCE.md` §1.1): una prova verde su `xfreerdp3` non
dice nulla finché non è stata rifatta su mstsc e su RDM.

---

## Fase 0 — Le due misure che mancano ✅ **CHIUSA il 4 agosto 2026**

> **Esito, in due righe.**
>
> | | |
> |---|---|
> | **A — RDM rende RFX Progressive?** | **Sì.** Il desktop compare e funziona. `REFERENCE.md` §1.7 e §10 n.2 |
> | **B — bordi della regione AVC420?** | **Esclusivi.** `REFERENCE.md` R5 e §10 n.3 |
>
> Il percorso Android regge e la decisione dei due codec è confermata da una misura, non più dedotta
> da un selettore. Si va in fase 1.
>
> **Due ricadute emerse per strada**, entrambe già a documento:
>
> 1. **FreeRDP codifica H.264 lato server** — `avc420_compress` è API pubblica, la usa il suo shadow
>    server, e ha il controllo del bitrate (VBR, bitrate, framerate, QP). `protocollo-rdp.md` §19.4
>    diceva l'opposto ed è stato corretto. La fase 2 non deve **scrivere** un codificatore, deve
>    **configurarne** uno; e la taratura della qualità (fase 10) non parte da zero.
> 2. **Sul banco, FreeRDP allinea entrambi i lati a 16**, non l'altezza a 64. R4 non è stata toccata —
>    allineare a 64 soddisfa anche il 16 — ma la tensione è annotata, da sciogliere con mstsc.
>
> **Il banco resta in piedi** ed è riproducibile: VM di runtime con grd su sessione Wayland senza
> monitor (misura A), contenitore del server con `freerdp-shadow-cli3` e VA-API (misura B). Gli
> innesti `LD_PRELOAD` che leggono i codec e i rettangoli stanno in `/media/REMOTIX/tmp/banco-b`.

**Taglia: piccola.** Nessuna riga di codice.

**Obiettivo.** Chiudere le due domande che decidono l'architettura del codificatore, prima di
scriverlo.

| # | Domanda | Perché blocca |
|---|---|---|
| **A** | **RDM rende davvero RemoteFX Progressive?** | Tutto il percorso Android poggia su questo codec, e **non l'abbiamo mai visto funzionare**: la prova del 3 agosto mandava PLANAR e RDM ha mostrato nero. Che lo renda è dedotto dal selettore «RDP 8.0», non misurato |
| **B** | **I bordi della regione AVC420 sono inclusivi o esclusivi?** | §5.4 di `SPECIFICA.md` dice inclusivi, `gnome-remote-desktop` scrive esclusivi e funziona con mstsc. Le due cose non possono essere entrambe vere, e sbagliare significa rinegoziazione e disconnessione su mstsc |

**Come si fa.**

Per **A**: il banco di `REFERENCE.md` §8.7, con `gnome-remote-desktop` su una **sessione Wayland** —
non su quella X11 usata il 3 agosto, dove il flusso PipeWire si chiudeva prima di disegnare. Senza
accelerazione grafica grd ripiega su RFX Progressive da solo, che è esattamente quello che serve
vedere. Si collega RDM: se disegna, la domanda è chiusa.

Per **B**: si cattura una sessione mstsc funzionante — di nuovo grd — e si guardano **i byte** della
metablock AVC420, non il codice che li produce.

**Si vede**: due righe aggiornate in `REFERENCE.md`, §1.7 e R5, con la marca `[M]` e la data.

> **Se A dà esito negativo** il piano cambia prima di cominciare: Android non sarebbe servibile né in
> H.264 né in RFX Progressive, e §3.7 di `SPECIFICA.md` andrebbe riaperto una seconda volta. È
> improbabile — RDM dichiara «RDP 8.0», che *è* EGFX con RFX Progressive — ma è il genere di
> improbabilità che costa un mese se la si scopre dopo.

---

## Fase 1 — L'ambiente e lo scheletro ✅ **CHIUSA il 4 agosto 2026**

> **Si vede**, e la prova sta in `src/remotix-c/prove/fase1.sh`, da eseguire dentro la VM:
>
> ```
> ==> 1. versione        REMOTIX 0.1.0 — FreeRDP 3.15.0, GLib 2.84.4
> ==> 3. opzione sbagliata: rifiutata, non ignorata
> ==> 4. arresto con SIGINT     uscito con codice 0 in 8 ms
> ==> 4. arresto con SIGTERM    uscito con codice 0 in 7 ms
> ==> 5. nessun processo residuo
> ```
>
> **Dov'e' cosa.** Il progetto in C sta in `/media/REMOTIX/src/remotix-c` (`/srv/src/remotix-c` dentro
> il contenitore); il progetto in Rust resta intatto in `src/remotix`, che e' un repository git a se'.
>
> ```
> bash /media/REMOTIX/enter.sh "meson setup $REMOTIX_BUILD $REMOTIX_SRC"
> bash /media/REMOTIX/enter.sh "ninja -C $REMOTIX_BUILD"
> bash /media/REMOTIX/vm.sh copia src/remotix-c/build/src/remotix
> bash /media/REMOTIX/vm.sh ssh "bash avvia-remotix.sh [--aperto]"
> ```
>
> **Gli strumenti, per non rifarli.**
>
> | Dove | Che cos'e' |
> |---|---|
> | `strumenti/sshpw.py` *(sul notebook, accanto ai documenti)* | esegue comandi sul server fornendo la password da `~/SERVER.ssh`. Serve perche' il rootfs del server e' live in RAM e il riavvio cancella `authorized_keys`. Ha `--put` e `--get`: **i file si spostano con quelli, mai catturando lo stdout di un `cat` remoto**, dove finirebbe anche la richiesta di password |
> | `/media/REMOTIX/tmp/banco-b/` | il banco delle misure: `spia-avc420.c` e `spia-progressive.c` (innesti `LD_PRELOAD` che leggono codec e rettangoli **come arrivano dal filo**), `spia-dsp.c` (chiama la sola `freerdp_dsp_encode` su un seno noto: e' quello che ha chiuso la questione n.10), piu' gli script di prova |
> | `/media/REMOTIX/tmp/avvia-remotix.sh` | avvia il server nella VM staccato dalla sessione SSH |
> | `/media/REMOTIX/provision.sh.rust`, `vm.sh.prima-di-copia` | le copie degli script prima delle modifiche del 4 agosto |
>
> **Due avvertenze pagate**, entrambe sul modo di guidare gli script da fuori:
>
> - **non si redirige lo stderr di `sudo`**: la richiesta di password finisce nel file e chi la deve
>   fornire resta appeso per sempre, in silenzio;
> - **`| tail` su un comando remoto ne bufferizza l'uscita** fino alla fine: se quel comando si
>   blocca, non si vede dove.
>
> **Tre correzioni agli script, che valgono oltre questa fase:**
>
> 1. `provision.sh` generava un `enter.sh` con `sudo -v -S -p ''`, **richiesta vuota**: chi fornisce la
>    password da standard input non ha nulla da riconoscere e resta appeso per sempre, in silenzio.
>    L'`enter.sh` su disco era stato corretto a mano, ma lo script lo riscriveva rotto a ogni giro.
>    Ora la richiesta e' esplicita in entrambi i punti.
> 2. `vm.sh` ha un comando nuovo, **`copia`**: il binario si costruisce nel contenitore e si esegue
>    nella VM, che sono due macchine distinte per vincolo (§6.2), e senza un trasporto ogni fase se ne
>    inventerebbe uno.
> 3. La toolchain del contenitore e' passata da Rust a **C, meson e FreeRDP 3**, e `provision.sh`
>    adesso **verifica che `pkg-config` veda tutte le dipendenze** invece di scoprirlo a meson.
>
> **Deciso strada facendo**: le opzioni sono in italiano come il resto del progetto (`--versione`,
> `--registro`, `--porta`), con `--version` accettato lo stesso perche' e' quello che si prova per
> primo.

**Taglia: piccola.**

**Obiettivo.** Avere due macchine pronte e un programma che compila, si avvia e si ferma con dignità.

**Contenuto.**

- `provision.sh` per il contenitore di sviluppo su `192.168.0.2:/media/REMOTIX` — idempotente, e
  **niente fuori da `/media/REMOTIX`** (§6.1 di `SPECIFICA.md`).

  > ⚠ **Su `/media/REMOTIX` c'è già un `provision.sh`**, del progetto precedente. Il rootfs del server
  > è live in RAM e si azzera a ogni riavvio, ma `/media` no: quel file sopravvive.
  >
  > **Va letto prima di riscriverlo**, perché contiene almeno una correzione pagata cara: i
  > `mount --make-rslave` dopo ogni `--rbind`. Senza, la funzione di pulizia smonta il `/dev/pts` del
  > server, il kernel non alloca più pseudo-terminali e nessuno riesce ad aprire una sessione SSH
  > interattiva — mentre tutto il resto continua a funzionare, quindi non se ne accorge nessuno
  > (§6.1 di `SPECIFICA.md`, 3 agosto).
  >
  > Vale lo stesso per gli altri script già presenti (`enter.sh`, `vm.sh`, `provision-vm.sh`): sono
  > scritti per il progetto in Rust, ma le correzioni che contengono valgono per qualunque linguaggio.
  > **Si guarda cosa c'è prima di decidere cosa buttare.**
- `provision-vm.sh` per la VM di runtime, effimera e senza nulla di preinstallato;
- scheletro **meson** — come il riferimento — con le dipendenze: `freerdp3`, `winpr3`,
  `freerdp-server3`, `glib-2.0`, `gio-2.0`, `libpipewire-0.3`, `pam`, `libsystemd`;
- `main.c`: opzioni da riga di comando, registro con livelli, segnali `SIGINT`/`SIGTERM`, uscita
  pulita.

**Si vede**: `remotix --version` gira dentro la VM; `Ctrl-C` lo ferma senza lasciare processi.

**Prima di scrivere**: nulla di `REFERENCE.md` — è l'unica fase che non tocca il protocollo.

**Rischi noti**: nessuno tecnico. Il rischio è **spendere troppo tempo qui**: lo scheletro serve a
partire, non a essere definitivo.

---

## Fase 2 — Il server disegna ✅ **CHIUSA il 4 agosto 2026**

> **Si vede: i tre client aprono e vedono la stessa immagine di prova, che si aggiorna.**
>
> | Client | Codec | Esito |
> |---|---|---|
> | `xfreerdp3` | AVC420 **e** RFX Progressive | automatico, in `prove/fase2.sh` |
> | **mstsc** | AVC420 | **si vede** — ed è il client che non supplisce a nulla |
> | **RDM** | **RemoteFX Progressive** | **«vista perfetta»** |
>
> Che mstsc disegni chiude sul filo, e non solo nel codice, i cinque difetti di §5.4 di
> `SPECIFICA.md`: `MapSurfaceToOutput`, l'elenco completo delle versioni EGFX, l'allineamento
> ×16/×64 col bordo riempito, i bordi esclusivi della regione e `ResetGraphics` con il monitor
> dichiarato. Che RDM la veda **corretta** chiude R18: l'ordine delle bande di quantizzazione di
> `progressive_compress` è giusto, e quello un contatore di fotogrammi non poteva dirlo.
>
> | Pezzo | Stato |
> |---|---|
> | Negoziazione TLS puro, TLS 1.2 minimo, i due flag della `NEG_RSP` | fatto |
> | Rifiuti di §3.3, ciascuno con il proprio codice d'errore | fatto |
> | PAM con la guardia che parte da negato (R14) e il confronto con l'utente effettivo | fatto |
> | EGFX: dieci versioni (R2), `CapsConfirm` singola, `ResetGraphics` (R6), `CreateSurface` + `MapSurfaceToOutput` (R1) | fatto |
> | Due codec scelti dai flag (R3): AVC420 e RemoteFX Progressive | fatto, entrambi provati |
> | Allineamento ×16/×64 col bordo riempito (R4), rettangoli esclusivi (R5) | fatto |
> | `SET_ERROR_INFO` prima di ogni chiusura (R12) | fatto |
> | Immagine sintetica: barre, griglia, cornice, orologio, barra che scorre | fatto |
> | Prova sui tre client | **fatta** |
>
> **Quattro trappole dell'API di FreeRDP** sono costate ore e stanno ora in `REFERENCE.md` §11
> (R15–R18). La più istruttiva è R17: il certificato TLS condiviso fra le connessioni uccide il
> server **alla seconda**, e una prova a connessione singola resta verde per sempre — la regola dei
> tre client applicata al *numero* di connessioni invece che al tipo.
>
> **Costruzione e prove**: `prove/fase2.sh` nel progetto; il server si porta nella VM con
> `vm.sh copia` e si avvia con `avvia-remotix.sh [--aperto]`.

**Taglia: grande. È la fase che decide se il progetto sta in piedi.**

**Obiettivo.** Un server RDP completo dal punto di vista del protocollo, che manda **un'immagine
sintetica** — nessun compositore, nessuna cattura.

**Contenuto.**

1. **Accettazione e negoziazione**: `freerdp_peer`, TLS 1.2+1.3, `PROTOCOL_SSL`, i due flag nella
   `NEG_RSP`;
2. **capacità**: i 13–15 capability set di `REFERENCE.md` §4, e i rifiuti di §3.3 **con il codice
   d'errore**;
3. **autenticazione PAM** con la guardia che parte da negato (R14) e il confronto con l'utente
   effettivo del processo (§3.4 di `SPECIFICA.md`);
4. **EGFX**: canale, `CapsAdvertise` → scelta della versione più alta fra le dieci → `CapsConfirm` →
   `ResetGraphics` → `CreateSurface` → **`MapSurfaceToOutput`**;
5. **i due codificatori**, scelti dai flag (R3):
   - **AVC420** — `libavcodec`, profilo *Constrained High*, niente fotogrammi B;
   - **RemoteFX Progressive** — `rfx_encode_message` di FreeRDP più l'involucro EGFX scritto da noi,
     **con le bande di quantizzazione rimescolate**;
6. **immagine sintetica**: barre di colore, una griglia con le coordinate e un orologio che scorre.
   Serve a vedere a occhio se la geometria è giusta, se l'immagine è spostata, e se i fotogrammi
   arrivano;
7. **chiusura** con `SET_ERROR_INFO` (R12).

**Si vede**: **i tre client aprono e vedono la stessa immagine di prova, che si aggiorna.** La griglia
è allineata ai bordi, l'orologio scorre, i colori sono giusti.

**Prima di scrivere**: §0, §1.6, §1.7, §3, §4, §5, R1, R2, R3, R4, R5, R6, R11, R12, R13, R14.
Cioè: quasi tutto. È la fase per cui `REFERENCE.md` è stato scritto.

**Come si prova**, in quest'ordine:

1. `xfreerdp3 /gfx:avc420` — deve comparire subito;
2. **mstsc** — la griglia deve essere allineata e non spostata, e non deve esserci rinegoziazione;
3. **RDM** — deve comparire, in RFX Progressive.

**Rischi noti.** Sono i sette errori di `REFERENCE.md` §8. In particolare:

- la convenzione dei bordi (esito della fase 0 **B**) — punisce su mstsc;
- l'allineamento ×16/×64 — punisce su mstsc;
- l'involucro EGFX di RFX Progressive, con il rimescolamento delle bande — punisce su RDM;
- il controllo del bitrate di AVC420: `libavcodec` lo dà, ma il punto di lavoro va trovato
  (§3.1 di `SPECIFICA.md`), e **nessuno dei due riferimenti ha niente da insegnare** perché
  `gnome-remote-desktop` codifica a QP costante.

> **Perché l'immagine sintetica prima del desktop vero.** Isola il pezzo più rischioso. Se qualcosa non
> si vede, il sospetto è su una sola cosa — il protocollo — invece che su tre (protocollo, cattura,
> compositore). È la lezione di §5.4 di `SPECIFICA.md` applicata in anticipo.

---

## Fase 3 — Il desktop vero ✅ **CHIUSA il 4 agosto 2026**

> **Si vede: il desktop GNOME vero, sui due codec.** La fotografia presa dal client mostra la
> sessione con lo sfondo di Debian, la barra in alto e l'indicatore arancione di registrazione di
> Mutter — e i colori sono giusti, cioè il BGRx è letto per il verso giusto.
>
> | Percorso | Esito |
> |---|---|
> | `xfreerdp3 /gfx:AVC420` → EGFX 8.1, AVC420 | desktop pieno |
> | `xfreerdp3 /gfx:RFX` → **EGFX 10.7 con `AVC_DISABLED`**, RemoteFX Progressive | desktop pieno — ed è **l'impronta esatta di RDM** (§1.6 di `REFERENCE.md`) |
> | **mstsc** | **«si vede perfettamente»** [M, utente] |
> | **RDM** | **«si vede perfettamente»** [M, utente] |
> | Avvio **a freddo**: nessun compositore, REMOTIX avvia la sessione | riuscito |
> | Regressione della fase 2, protocollo isolato | 298 fotogrammi, tre connessioni di fila |
>
> **La regola dei tre client è soddisfatta**, ed è il punto: il banco automatico prova solo
> `xfreerdp3`, che supplisce alle omissioni: sono mstsc e RDM a dire che il desktop vero passa
> davvero. Che entrambi vedano bene chiude sul filo, e non solo nel codice, la cattura PipeWire, la
> convenzione dei colori BGRx, l'allineamento della tela con il desktop dentro, e R9.
>
> **La prova automatica è `prove/fase3.sh`**, e va eseguita **sul server** perché mette insieme due
> macchine: la VM, dove c'è GNOME e gira REMOTIX, e il contenitore, dove c'è il client strumentato.
> Sorveglia le cinque cose che contano — sequenza di Mutter, misura negoziata, fotogrammi arrivati,
> riaggancio, e che il palco **non** venga smontato alla disconnessione.
>
> ```
> OK  monitor virtuale montato: nodo PipeWire 50, flusso .../Stream/u1
> OK  misura negoziata 1282x802, cioe' quella chiesta
> OK  primo fotogramma dal desktop: 1282x802, passo 5128
> OK  alla seconda connessione il palco e' stato RIUSATO (R9, riaggancio)
> OK  nessun «Removed virtual monitor» nel registro della Shell
> ```
>
> **Due misure, entrambe già a documento.**
>
> 1. **Il rettangolo PipeWire: ha ragione il riferimento.** Il `SPA_POD_Rectangle` **singolo**
>    funziona e negozia esattamente la misura chiesta; provato anche l'intervallo chiuso, funziona
>    pure lui. Il `no more input formats` del 2 agosto era un fatto della catena in Rust di allora.
>    `SPECIFICA.md` §5.6 e `gnome-remote-desktop.md` §11.1 e §18.2 n.6 sono stati corretti.
> 2. **La regola R10 si vede lavorare**: `atteso il ridisegno alla misura nuova: 7 fotogrammi
>    raccolti`. Sono i fotogrammi che sarebbero finiti al client come immagine parziale.
>
> **La decisione presa qui: libei.** Come raccomandato dalla fase 4, e la ragione che pesa di più è
> che chiude la questione aperta n.7 leggendo la keymap dalla sessione invece di dedurla. Ribalta
> §5.8 e §8 di `SPECIFICA.md`, entrambi aggiornati. **La fase 3 non ha scritto una riga di input**:
> crea la sessione di controllo — che serve comunque, perché la cattura vi si registra — e lascia
> alla fase 4 l'innesto di `ConnectToEIS`. Tornare indietro costa una chiamata.
>
> **Il palco è stato anticipato dalla fase 5**, e non per zelo: appartiene al **server**, non alla
> connessione. Smontarlo alla disconnessione lascia Mutter con zero schermi e rompe la sessione — e
> la prova di questa fase è «il desktop sui tre client», cioè tre connessioni una dopo l'altra, che
> è precisamente la sequenza che quel difetto rovina. In dote arriva il riaggancio.
>
> **Che cosa è nuovo, per non cercarlo.**
>
> | File | Che cos'è |
> |---|---|
> | `src/sessione.c` | avvia la sessione GNOME senza monitor, con l'ambiente composto da zero |
> | `src/mutter.c` | la sequenza obbligata di Mutter, fino al nodo PipeWire annunciato |
> | `src/cattura.c` | il flusso PipeWire su un `pw_thread_loop` suo |
> | `src/palco.c` | tiene insieme i due, conserva l'ultimo fotogramma (R9), aspetta il ridisegno (R10) |
> | `--immagine-di-prova` | manda la scena sintetica invece del desktop. **Non è un residuo**: è il banco che isola il protocollo dalla cattura, ed è quello che `prove/fase2.sh` usa |
>
> **Una trappola nuova, che vale oltre questa fase.** `pkill -f "Xvfb :103"` **uccide la shell che
> lo esegue**, se quella riga compare nella sua stessa riga di comando — cioè sempre, quando il
> blocco è passato come argomento. Il sintomo è un blocco che non stampa nulla e un `Terminated`
> comparso altrove. Si ancora il pattern: `pkill -f "^Xvfb :103"`.
>
> **E una vecchia, ripagata**: `2>&1 | tail` su un comando che passa da `enter.sh` inghiotte la
> richiesta di password di `sudo`, e chi la deve fornire resta appeso per sempre in silenzio. È
> l'avvertenza della fase 1, e non basta averla scritta.
>
> **Che cosa questa fase NON ha provato, e non doveva**: il ridimensionamento a caldo. Qui il
> desktop nasce della misura che il client dichiara alla connessione e resta quella; MS-RDPEDISP e
> la macchina a stati del ridimensionamento sono la **fase 6**. Il pezzo che ci arriva già pronto è
> `pw_stream_update_params`: il palco esiste, ha una misura, e cambiargliela non dovrà rifare la
> cattura.

**Taglia: media.**

**Obiettivo.** Sostituire l'immagine sintetica con il desktop, senza toccare il protocollo.

**Contenuto.**

- avvio della **sessione GNOME senza monitor** (§5.9-bis di `SPECIFICA.md`): `gnome-session` con
  l'ambiente composto **da zero** con `env_clear()`, locale forzata a UTF-8;
- **la sequenza obbligata** di Mutter (§5 di `gnome-remote-desktop.md`): `CreateSession` →
  `ConnectToEIS` **oppure** i metodi `Notify*` → `ScreenCast.CreateSession` con
  `remote-desktop-session-id` e **`disable-animations`** → `Session.Start` → `RecordVirtual` →
  `Stream.Start`;
- **cattura PipeWire**: monitor virtuale della misura chiesta dal client, formato `BGRx`, cadenza
  dichiarata a zero con massimo a intervallo, **stride letto dal chunk**;
- **l'ultimo fotogramma conservato e rispedito** (R9).

**Si vede**: **il desktop vero sui tre client**, non ancora comandabile.

**Prima di scrivere**: R9, R10, §7 di `REFERENCE.md`; e §5.6 di `SPECIFICA.md`, che è tutto ancora
valido perché parla di Mutter e non di IronRDP.

**Rischi noti.**

- il **rettangolo PipeWire**: valore singolo o intervallo chiuso? Divergenza già segnalata fra la
  nostra misura e il riferimento (`gnome-remote-desktop.md` §11.1);
- **Xwayland che non completa l'avvio** nella VM (questione aperta n.8): per ora `--no-x11`;
- il primo fotogramma vuoto dopo un rimontaggio (R10).

**Decisione da prendere qui**: ~~**libei o i metodi `Notify*` di D-Bus?**~~ **PRESA il 4 agosto:
libei.** Vedi fase 4 per le ragioni, e il riquadro di chiusura qui sopra per quel che ne è
disceso.

---

## Fase 4 — Si comanda ✅ **CHIUSA il 4 agosto 2026**

> **Si vede: il desktop si comanda da tutti e tre i client.** `xfreerdp3`, **mstsc** e **RDM**:
> tastiera, puntatore e rotella. [M, utente]
>
> Che RDM comandi chiude anche **il percorso Unicode**, che fino a quel momento era scritto e non
> misurato: su Android non esiste una tastiera fisica da cui mandare scancode, quindi ciò che arriva
> sono caratteri, e l'unico modo di farli comparire è tradurli nel tasto che li produce **nella
> disposizione della sessione** — cioè la keymap letta da libei. È la questione aperta n.7 chiusa
> sul filo e non solo nel codice.
>
> **La prova automatica sta in `prove/fase4.sh`**, da eseguire sul server come quella della fase 3:
>
> ```
> OK  il canale libei si e' aperto
> OK  disposizione della sessione letta da libei: English (US)
> OK  regione del puntatore: 0,0 1282x802 (mapping-id «2eb0967b-…»)
> OK  20 eventi di tastiera inoltrati al compositore
> OK  le tre posizioni del puntatore sono arrivate esatte
> OK  la rotella: uno scatto vale uno scatto, nei due versi
> OK  il clic arriva, premuto e rilasciato
> OK  rilascio quel che era rimasto premuto: 1 tasti
> ```
>
> E la fotografia che vale più dei controlli: **«remotix» scritto per intero nella ricerca della
> panoramica di GNOME** — sette lettere, tutte comparse, prima inclusa.
>
> **Due questioni chiuse, e una che non esiste più.**
>
> 1. **La questione aperta n.7 è chiusa**: la disposizione di tastiera **si legge dalla sessione**,
>    non si dichiara e non si deduce dal KLID. `REMOTIX_TASTIERA` non serve più.
> 2. **Il colpo a vuoto della regola 5 di §5.8 è sparito**, non aggirato: con libei i dispositivi li
>    annuncia il compositore e non si può spedire nulla prima che esistano, quindi la «prima lettera
>    persa» non ha più dove presentarsi.
> 3. **`GetKeycodeFromVirtualKeyCode(…, WINPR_KEYCODE_TYPE_EVDEV)` dà il codice evdev vero**, senza
>    il −8: quel −8 serve solo al percorso xkb. Misurato, perché sbagliarlo avrebbe spostato ogni
>    tasto di otto posizioni senza dare alcun errore.
>
> **Che cosa è nuovo.**
>
> | File | Che cos'è |
> |---|---|
> | `src/input.c` | libei: connessione, dispositivi, regioni, coda degli eventi, invio |
> | `src/tastiera.c` | scancode → evdev, conto dei premuti, Pausa a quattro stati, Unicode via xkbcommon |
> | `mutter.c` | `ConnectToEIS` subito dopo `CreateSession`, e il `mapping-id` dichiarato a `RecordVirtual` |
> | `provision.sh` | `libei-dev` e `xdotool` |
>
> **Due trappole di banco pagate**, entrambe fuori dal codice del prodotto:
>
> - **`ssh` senza `-n` eredita lo standard input dello script**: quando quello è un terminale che non
>   finisce mai, la sessione remota resta aperta anche dopo che il comando è finito, e il sintomo è
>   un passo che «non torna» pur essendo già andato a buon fine;
> - **la rotella e il clic risultavano rotti, e la rotta era la prova**: cercava `asse dy=-10` mentre
>   il registro scrive `asse dx=0 dy=-10`, e il clic non era mai stato mandato. È il rovescio della
>   regola dei tre client — una prova che boccia il codice giusto costa quanto una che promuove
>   quello sbagliato.
>
**Taglia: media.**

**Obiettivo.** Tastiera, mouse e rotella funzionanti sui tre client.

**La decisione: libei. Presa il 4 agosto 2026**, chiudendo la fase 3, che ha già creato la sessione
di controllo: alla fase 4 resta da innestarci `ConnectToEIS`. La ragione è nelle misure:

| | `Notify*` (D-Bus) | **libei** |
|---|---|---|
| Disposizione di tastiera della sessione | non la si legge | **`ei_device_keyboard_get_keymap`** |
| Stato reale di BlocMaiusc/BlocNum | si indovina | **evento `KEYBOARD_MODIFIERS`** |
| Punto di sincronizzazione | non c'è | **`ei_ping`** |
| Regioni degli schermi | si calcolano | **`ei_region` con `mapping_id`** |
| È la strada del riferimento | no | **sì** |

Il costo è che i dispositivi virtuali si negoziano invece di essere imposti. Il guadagno è che la
**questione aperta n.7** si chiude leggendo la disposizione dalla sessione invece di dichiararla.

**Contenuto.**

- scancode → vkcode → keycode evdev, con la tabella dei tasti premuti (R6 di `REFERENCE.md` §6.1);
- **percorso Unicode**, che su Android è primario;
- il tasto Pausa a quattro stati;
- rotella: /120 → ×10, verticale invertito, **coordinate scartate** quando i flag rotella sono accesi;
- riconciliazione dei lucchetti dopo un `ei_ping`;
- **rilascio di tutto a fine connessione**, anche senza sessione a cui parlare.

**Si vede**: si apre un terminale nella sessione remota **da ciascuno dei tre client** e si scrive; il
puntatore va dove deve; la rotella scorre di uno scatto per scatto.

**Prima di scrivere**: §6 di `REFERENCE.md`, tutto.

**Rischi noti**: le prove automatiche con `xdotool` mentono (§5.8 di `SPECIFICA.md`) — perde battute e
consegna la posizione precedente del puntatore. Si cerca **la coppia di letture attesa**, non la prima
e l'ultima.

---

## Fase 5 — La sessione ✅ **CHIUSA il 4 agosto 2026**

> ### Come è stata chiusa
>
> **Verificata dall'utente su tutti e tre i client** — xfreerdp3, mstsc e Android — con il ciclo che
> conta: *«mi collego, faccio qualcosa, mi sloggo, poi rientro»*. Il rientro trova il desktop, non
> uno schermo nero.
>
> **`fase5.sh` passa tutti i controlli, tre esecuzioni consecutive.** Compreso il ritorno dopo il
> logout, che prima non si poteva nemmeno provare perché il server non c'era più.
>
> ```
> OK  registrati con gnome-session: l'uscita si sa subito
> OK  il client e' caduto 0.01s dopo l'annuncio dell'uscita (soglia: 2 s)
> OK  il client ha ricevuto ERRINFO_LOGOFF_BY_USER: sa PERCHE' e' finita
> OK  il palco e' stato smontato: chi si ricollega ne trova uno nuovo
> OK  REMOTIX e' sopravvissuto al logout: puo' riaprire la sessione a chi torna
> OK  la sessione e' stata riavviata da REMOTIX per chi e' tornato
> OK  il palco e' stato rimontato sulla sessione nuova
> OK  il portiere ha rifiutato la seconda connessione
> OK  il secondo client ha ricevuto ERRINFO_SERVER_DENIED_CONNECTION, non un errore di rete
> OK  il primo client non e' stato disturbato
> OK  il palco e' stato riusato: il desktop ricompare all'istante, con le finestre dov'erano
> OK  una sola «nuova sorgente» in tutta la sessione
> ```
>
> ### ⛔ La sopravvivenza al logout: la diagnosi era sbagliata, e per tre volte
>
> Per un giorno intero questo blocco ha detto che REMOTIX moriva perché GNOME smonta l'albero
> dell'utente, e che la cura era una **sessione PAM** rimandata alla fase 12. Era falso. La misura
> in tre cgroup diversi — `session-N.scope`, `app.slice`, `background.slice`, tutti con SIGTERM —
> sembrava dimostrarlo, e invece non dimostrava niente: il mittente non era mai stato **chiesto**,
> era stato **dedotto**.
>
> Il registro di sistema diceva `remotix.service: Deactivated successfully.` **senza** alcuno
> `Stopping…` prima, cioè systemd dichiarava di non essere stato lui. A quel punto, invece di
> continuare a ipotizzare, un gestore di `SIGTERM` con `SA_SIGINFO` che registra `si_pid`, `si_uid`,
> `si_code` e la pila di chiamate. Venti righe, una sola esecuzione, e il registro ha detto:
>
> ```
> SIGTERM mandato da pid 30202 (remotix), uid 1000 — si_code -6: raise()/pthread_kill() da dentro
>   pila #3  libc.so.6(gsignal+0x12)
>   pila #4  libgio-2.0.so.0(+0x8b6b8)
>   pila #8  libgobject-2.0.so.0(g_signal_emit+0x93)
> ```
>
> **Era REMOTIX a uccidersi**, dentro un gestore di segnale GObject: sulla connessione condivisa al
> bus di sessione GIO tiene acceso `exit-on-close`, e al logout — quando `dbus.service` dell'utente
> si ferma — chiama `raise(SIGTERM)` per conto nostro. Una riga per spegnere l'interruttore.
>
> **La regola che ne discende**: quando un processo muore e nessuno ammette di averlo ucciso, non si
> deduce il mittente — **lo si chiede al nucleo**. Costo della deduzione: tre diagnosi sbagliate e
> una fase rimandata a torto. Costo della domanda: venti righe. Sta in §7.4 di `REFERENCE.md`.
>
> ### ⛔ E poi lo schermo nero al secondo accesso
>
> Sopravvissuto al logout, REMOTIX era cieco al giro dopo: la sessione ripartiva, il palco no.
> Al logout `dbus.service` si ferma e `gnome-session-restart-dbus.service` ne avvia **un altro**
> sullo stesso socket; l'oggetto connessione che tenevamo in mano era quello vecchio, chiuso.
> Usarlo non dà errore: dà **silenzio**. Ogni presa del bus ora controlla `is_closed()` e riapre.
>
> È la stessa regola che si legge in `gnome-remote-desktop` e in `xrdp`: **chi sopravvive al logout
> non riusa niente della sessione morta**. Loro la rispettano per costruzione — demone di sistema,
> sessione nuova chiesta a GDM o forcata via PAM. REMOTIX tiene lo stesso processo su entrambi i
> lati, quindi la applica a mano, in un punto solo (`sessione_bus`), con il divieto scritto
> nell'intestazione.
>
> ### ⛔ Il rifiuto che partiva metà delle volte
>
> `SET_ERROR_INFO` è un **Share Data PDU**: esiste solo dopo l'attivazione della sessione RDP.
> Spedirlo da `PostConnect` — dove sta naturalmente il rifiuto, perché è lì che si scopre di dover
> rifiutare — lo mandava in un punto in cui il client non lo aspetta. Il controllo del banco usciva
> ora **7** (codice ricevuto) ora **147** (niente), senza che nulla cambiasse: per due giorni è
> stato archiviato come rumore. **Un difetto che passa metà delle volte costa più di uno che non
> passa mai.** Ora il rifiuto si registra e si dice in `Activate`. R12 di `REFERENCE.md` è stata
> estesa.
>
> ### ⛔ Il difetto più grosso di tutto il progetto finora, e stava dentro la regola scritta per evitarlo
>
> **`freerdp_set_error_info` non manda niente.** Registra il codice. A spedirlo è
> `freerdp_send_error_info`, che è una funzione a parte. R12 di `REFERENCE.md` diceva
> «`freerdp_set_error_info()` prima di `Disconnect`» — ed era **sbagliata**: così il client riceve
> una chiusura di socket e nient'altro, cioè esattamente il difetto che R12 esiste per togliere.
>
> Era lì dalla fase 2. Le fasi 2, 3 e 4 sono passate senza accorgersene perché **nessuna prova
> aveva mai guardato dal lato del client**: il nostro registro diceva compìto «congedo il client:
> … (0x000C)», e quello del client, alla stessa ora, diceva `Network disconnect!`.
>
> **La regola che ne discende, e vale oltre questo caso**: un congedo si verifica **dal lato che lo
> deve ricevere**. Il registro di chi manda dice che ha chiamato una funzione, non che il byte è
> arrivato. `REFERENCE.md` R12 è stata corretta.
>
> ### Che cosa è nuovo
>
> | File | Che cos'è |
> |---|---|
> | `src/uscita.c` | registrazione con `gnome-session`, e la **regola dell'ostaggio**: si risponde sempre, e per primo |
> | `src/sentinella.c` | logind: c'è una sessione grafica **locale**? Segnali più ripasso ogni 2 s |
> | `server.c` | il portiere (`compare_exchange`, non «leggi poi scrivi»), il registro delle connessioni, il congedo pilotato, keepalive stretti e `TCP_USER_TIMEOUT` |
> | `sessione.c` | `Logout(1)` e, se serve, `Logout(2)` dichiarandolo nel registro; **`sessione_bus`**, unica porta al bus di sessione |
> | `main.c` | la **spia del `SIGTERM`**: gestore `SA_SIGINFO` incatenato dietro quello di glib, che registra `si_pid`, `si_uid`, `si_code` e la pila. Resta lì: il giorno in cui il server morirà di nuovo senza spiegazioni, la risposta sarà già nel registro |
>
> ### Che cosa resta, e non tiene aperta la fase
>
> 1. **I casi 6 e 8 della tabella delle nove combinazioni** — quelli che coinvolgono una sessione
> grafica **locale**. Il codice c'è ed è quello di §5.10; a mancare è il banco, perché nella VM non
> c'è nessuno seduto davanti. Serve `finta-sessione-locale`, che apre una sessione PAM dichiarando
> `XDG_SESSION_TYPE=wayland` e `XDG_SEAT=seat0` — con l'avvertenza già pagata: **`pam_systemd` non
> registra nulla se il processo chiamante è già dentro una sessione**, quindi va avviato come unità
> transitoria.
> 2. **La sessione PAM della questione n.10** resta da fare — ma non più per sopravvivere al logout,
> che ora funziona senza. Serve perché il sistema sappia che c'è una sessione remota. Fase 12.

**Taglia: grande.**

**Obiettivo.** La sessione vive, sopravvive alla disconnessione, e le regole d'accesso valgono.

**Contenuto.**

- **il palco** (cattura, controllo, monitor virtuale) appartiene alla **sessione**, non alla
  connessione: resta montato fra un client e l'altro. È la questione n.5, già risolta una volta;
- **riaggancio**: chi torna alla stessa misura ritrova il desktop com'era, senza rifare la cattura;
- **avvio della sessione** da parte di REMOTIX, e **rilevamento dell'uscita** registrandosi con
  `gnome-session` (`RegisterClient`, agganciandosi a `EndSession` e non a `QueryEndSession`);
- **le nove combinazioni** di §3.4 di `SPECIFICA.md`: sessione unica per utente, la locale vince,
  la seconda connessione RDP rifiutata **con `ERRINFO_SERVER_DENIED_CONNECTION`**;
- **sentinella logind**: segnali `SessionNew`/`SessionRemoved` **più** un ripasso periodico, perché il
  `Type` cambia dopo la nascita;
- **keepalive stretti + `TCP_USER_TIMEOUT`**, perché con la sessione unica chi perde la rete non deve
  restare chiuso fuori un quarto d'ora.

**Si vede**: si chiude il client, si riapre, **le finestre sono dove erano**. Si fa «Esci» e il client
cade entro due secondi **dicendo perché**. Una seconda connessione viene rifiutata con un messaggio.

**Prima di scrivere**: R12, R14, **§7.4**, §8.5 e §8.6 di `REFERENCE.md`.

**Rischi noti**: la finestra di sovrapposizione del caso 8 (tre secondi in cui due sessioni grafiche
coesistono), e la **questione aperta n.10** — la sessione remota non è registrata in `logind`. Si
rimanda alla fase 12, dove il servizio di sistema la risolve alla radice.

---

## Fase 6 — La risoluzione segue la finestra ✅ **CHIUSA il 5 agosto 2026**

> ### Come è stata chiusa
>
> **Verificata dall'utente su tutti e tre i client**, ciascuno per quello che sa fare:
>
> | | Esito | Che cosa prova |
> |---|---|---|
> | **xfreerdp3** | ✅ ridimensiona | il percorso completo, trascinando il bordo |
> | **RDM** (Android) | ✅ ridimensiona | la rotazione — nel registro `2560x984 → 1384x662 → 2560x984`, due giri, **zero ripieghi**. Ed è l'unico che esercita il filtro sul DPI |
> | **mstsc** | ✅ non ridimensiona, **come atteso** | la non regressione: `canale DISP aperto` anche per lui, e nessuna seconda `nuova sorgente` |
>
> **`fase6.sh` passa tutti i controlli, tre esecuzioni consecutive** — 23 controlli, zero falliti.
> Il banco sta in `src/remotix-c/prove/fase6.sh` e mette insieme i due ambienti: il contenitore per
> il client, la VM per il desktop vero.
>
> ```
> OK  il canale MS-RDPEDISP e' stato aperto e le capacita' sono partite
> OK  la tela grafica e' stata ridichiarata, senza riattivazione (R7)
> OK  il client non ha ricaricato canali e non e' caduto: nessuna riattivazione (R7)
> OK  la misura e' cambiata SENZA rifare la cattura: pw_stream_update_params
> OK  nessun ripiego: la strada buona ha retto
> OK  una sola «nuova sorgente» in tutta la sessione (1 montaggio)
> OK  la regione del puntatore e' stata riletta dopo il cambio di misura
> OK  le richieste si sono ACCORPATE: 8 trascinamenti → 2 ridimensionamenti
> OK  nessun ridimensionamento nei dieci secondi di quiete: il ping-pong non riparte
> OK  tre trascinamenti, tre ridimensionamenti: nessuno perso, nessuno di troppo
> OK  il desktop e' finito sull'ultima misura chiesta
> ```
>
> ### ⛔ L'eco: il difetto che il banco ha trovato, e che nessuna regola prevedeva
>
> Applicare ogni `MONITOR_LAYOUT` appena arriva sembra la cosa giusta e non lo è. Un
> ridimensionamento costa **mezzo secondo**, e in quel mezzo secondo il client continua a mandarne:
> quelle richieste descrivono la finestra **prima** di conoscere la nostra risposta. Applicarle
> innesca una rincorsa fra i due lati che **va avanti da sola**.
>
> Misurato: 8 trascinamenti in 2,4 s producevano **38 richieste e 37 ridimensionamenti**, che
> continuavano per oltre **quaranta secondi dopo** che nessuno toccava più niente. Su Android
> sarebbero stati altrettanti riavvii del decodificatore.
>
> **Che fosse la nostra latenza e non il protocollo** non è stato dedotto: è stato misurato con due
> banchi di controllo, ed è la lezione di §5.4 di `SPECIFICA.md` applicata a una latenza invece che
> a un codec.
>
> | Banco di controllo | Esito |
> |---|---|
> | scena sintetica, stessa raffica — ridimensionamento **istantaneo**, non c'è palco | 8 richieste, 8 applicazioni, **converge** |
> | desktop vero, 3 trascinamenti **distanziati di 3 s** | 3 richieste, 3 applicazioni, **converge** |
>
> Due contromisure, entrambe necessarie: **assestamento** (si applica quando le richieste smettono
> di arrivare, e il conto riparte a ridimensionamento concluso) e **guardia sull'eco** (si scarta chi
> richiede la misura appena lasciata entro 250 ms). Sta in `REFERENCE.md` **R10-bis**.
>
> ### Che cosa è nuovo
>
> | File | Che cos'è |
> |---|---|
> | `src/misura.c` | la configurazione monitor validata, **un filtro solo** per Client Core Data e MS-RDPEDISP. Con il controllo sul **DPI** e non solo sui millimetri: i 1000 mm di RDM passano il filtro del riferimento e fanno 24 DPI |
> | `src/cattura.c` | `cattura_ridimensiona`: `pw_stream_update_params` e **attesa della conferma**, non di un silenzio |
> | `src/palco.c` | `palco_ridimensiona`, e `palco_assicura` che ora **ridimensiona invece di rimontare** anche per chi si ricollega a un'altra misura |
> | `server.c` | il canale DISP, la macchina di §7.2 su tre stati, l'assestamento, la guardia sull'eco, e il puntatore scartato a geometria instabile |
>
> ### Due cose che la prova a mano ha insegnato, e che il banco non poteva
>
> 1. **RDM dichiara i millimetri uguali ai pixel** — `1384×662 px su 1384×662 mm`, cioè **25 DPI**.
>    La misura del 3 agosto («984 px su 1000 mm», 24 DPI) era una lettura approssimata dello stesso
>    fatto. Il filtro sul DPI lo prende; quello sui soli millimetri del riferimento no. E xfreerdp3
>    **non può esercitarlo**, perché deriva i millimetri da un 75 DPI fisso: lo prova RDM e nessun
>    altro. `REFERENCE.md` §7.1 aggiornato.
> 2. **Il caso di R8 non si presenta più**, per come la fase 6 apre i canali: le capacità DISP
>    partono solo quando il client conferma la creazione del canale, cioè nella stessa finestra in
>    cui si negozia EGFX. Su RDM, `canale DISP aperto` ed `EGFX negoziato` distano **un millesimo**,
>    e il primo `MONITOR_LAYOUT` arriva quattro secondi dopo. **Il rinvio resta comunque**: costa
>    niente, e l'ordine dei canali è una proprietà del nostro codice, non del protocollo.

**Taglia: media.**

**Obiettivo.** MS-RDPEDISP, e il ridimensionamento fatto come lo fa il riferimento.

**Contenuto.**

- canale `Microsoft::Windows::RDS::DisplayControl`, capacità dichiarate, `MONITOR_LAYOUT` ricevuti;
- **la macchina a stati** di `REFERENCE.md` §7.2: inibisci → prepara → attendi stream → attendi
  misure → riprendi;
- **il ridimensionamento non rifà la cattura**: `pw_stream_update_params`. È la correzione che toglie
  il prezzo pagato in §5.8 di `SPECIFICA.md` (i tasti premuti persi al resize);
- validazione della configurazione monitor, **con il controllo sul DPI** e non solo sui millimetri;
- il layout arrivato prima di EGFX si **rinvia** (R8).

**Si vede**: si trascina il bordo della finestra su `xfreerdp3` e su RDM e **l'immagine segue senza
sporcarsi**; si ruota il telefono avanti e indietro cinque volte e non si rompe niente.

**Prima di scrivere**: R7, R8, R9, R10, §7 di `REFERENCE.md`.

**Rischi noti**: le raffiche di `MONITOR_LAYOUT` trascinando il bordo; su Android ogni cambio è anche
un riavvio del decodificatore.

---

## Fase 7 — La misura e il regolatore ✅ **CHIUSA il 5 agosto 2026**

**Taglia: media.**

> ### Come è stata chiusa
>
> **`fase7.sh` passa tutti i controlli** — 17 controlli, zero falliti. Il banco sta in
> `src/remotix-c/prove/fase7.sh` e usa la **scena sintetica anche nella VM**: quel che si misura è il
> rapporto fra rete e fotogrammi, e serve un produttore che non si fermi mai. Un desktop vero, fermo,
> non manda niente e il regolatore non ha nulla da regolare.
>
> Con `tc netem delay 120ms rate 250kbit` fra la VM e il client:
>
> | | rete libera | strozzata |
> |---|---|---|
> | RTT medio misurato | 6 ms | **556 ms** |
> | soglia del regolatore | 2 | **18** |
> | fotogrammi in volo, massimo | 1 | **10** — mai oltre la soglia |
> | fotogrammi al secondo | 30 | **23** |
>
> ```
> OK  il client dichiara l'autodetect e la misura si e' accesa
> OK  la banda si misura sul fotogramma vero: 30 856 byte contati dal client
> OK  solo i fotogrammi da almeno 10 KB avviano una misura
> OK  la sospensione dei riscontri e' stata riconosciuta, e dopo sono partiti altri 505 fotogrammi
> OK  l'RTT misurato segue il ritardo iniettato: 6 ms → 556 ms
> OK  la soglia del regolatore e' cresciuta con l'RTT: 2 → 18
> OK  i fotogrammi in volo non sono mai andati oltre la soglia: al massimo 10 su 18
> OK  e sono di meno: 30 al secondo a rete libera, 23 strozzata
> OK  l'RTT e' tornato a 4 ms: la finestra mobile segue la rete che migliora
> ```
>
> ### ⛔ Il difetto che il banco ha trovato: la misura che pesava il nulla
>
> Le scritture sui **canali dinamici sono accodate** (`wts_queue_send_item`); i PDU di autodetect
> vanno **dritti sul socket**. Stringere la misura di banda attorno a `SurfaceFrameCommand` manda
> quindi entrambi i marcatori *prima* del fotogramma, e il client conta i byte di quel che c'è in
> mezzo — cioè niente. Rispondeva **«10 byte in 0 ms»**, e da lì una banda di 80 kbit/s: un numero
> plausibile, prodotto da una misura vuota, senza nessun errore da nessuna parte.
>
> I marcatori vanno attorno allo **svuotamento della coda**. È **R19** di `REFERENCE.md`, ed è il
> motivo per cui il registro riporta i due numeri grezzi accanto al risultato: la banda stimata da
> sola non dice se il risultato è credibile, lo dice il rapporto fra byte e millisecondi.
>
> Trovato guardando il registro invece che ragionandoci sopra — il valore fermo a 80 kbit/s su
> loopback era il segnale, e il difetto non ne dava altri.
>
> ### L'adattamento di risoluzione è passato alla fase 10
>
> Era l'ultima voce del contenuto: *«adattamento di risoluzione come rete di sicurezza, riusando la
> macchina della fase 6»*. **Non è stato fatto qui, ed è una decisione, non una dimenticanza.**
>
> Il motivo sta nel codice del client di riferimento. `xf_disp.c` rimanda un `MONITOR_LAYOUT` ogni
> volta che la misura della **sua finestra** non coincide con l'ultima mandata, e lo rifà **a ogni
> secondo** sul timer (`xf_disp_OnTimer` → `xf_disp_sendResize`). Quindi:
>
> | Modo del client | Cosa succede se il server rimpicciolisce da solo |
> |---|---|
> | a finestra | il client ridimensiona la **finestra dell'utente** per seguirci |
> | a schermo intero | la sua misura non cambia: **ci rimanda la richiesta ogni secondo**, e disfa la nostra scelta |
>
> Nel secondo caso la guardia sull'eco (R10-bis) non aiuta: copre la misura appena *lasciata* per
> 250 ms, non una richiesta ripetuta a intervalli di un secondo. E in entrambi i casi il prezzo è
> alto — cambiare la misura del monitor virtuale **ridispone le finestre dell'utente**, per un calo di
> banda che può durare due secondi.
>
> Si aggiunga che il segnale che dovrebbe farlo scattare è il più grossolano che abbiamo: banda
> misurata a millisecondi interi, solo sui fotogrammi grandi. Guidare un'azione così vistosa con una
> misura così ruvida è il modo di ottenere un desktop che si riorganizza da solo senza motivo.
>
> **Il regolatore basta già a mantenere la promessa** — «rallenta senza bloccarsi», misurato. Quel che
> resta va con la **fase 10**, dove la scala 4K → 2K → 1080p di §3.1 di `SPECIFICA.md` si tara come
> una cosa sola insieme al bitrate, e dove si può valutare la strada che **non** litiga con
> MS-RDPEDISP: `MAPSURFACETOSCALEDOUTPUT`, che lascia il desktop della misura chiesta e rimpicciolisce
> solo la superficie codificata, lasciando scalare il client. FreeRDP la espone già lato server
> (`MapSurfaceToScaledOutput`); quali client la rendano davvero è da misurare.

> **Perché è una fase a sé, e perché viene adesso.** *Deciso il 5 agosto 2026, chiudendo la fase 6.*
>
> Il piano aveva un'unica «fase 7 — la qualità» che teneva insieme due cose con dipendenze opposte:
> lo **strumento** (misurare la rete, regolare il flusso) e la **taratura** (dove mettere il punto di
> lavoro del bitrate). Il primo non dipende dal codificatore; il secondo sì — e la fase 9 il
> codificatore lo cambia. §5.5 di `SPECIFICA.md` dice che *«gli encoder hardware rendono peggio a
> bitrate bassi»*: un punto di lavoro tarato su `libx264` andrebbe rifatto daccapo su VA-API.
>
> Lo strumento invece serve **prima** delle due fasi che lo useranno, ed è la ragione decisiva per
> anticiparlo: la fase 9 promette *«a parità di scena, il consumo di CPU crolla»*, e senza la misura
> della rete e il conteggio dei fotogrammi in volo quella frase non ha una bilancia su cui pesarsi.
> È la lezione della fase 0 applicata di nuovo — **il banco si certifica prima della misura**.
>
> La taratura è diventata la **fase 10**, agganciata alla 9.

**Obiettivo.** Sapere in che condizioni è la rete, e non spedire più di quanto il client digerisca.

**Contenuto.**

- **misura della rete**: RTT e banda (MS-RDPBCGR 2.2.14), con le due cadenze 70 ms / 700 ms e la
  misura di banda solo su fotogrammi ≥ 10 KB;
- **il regolatore a posti-fotogramma** con soglia ricavata dall'RTT — poche decine di righe, e dà
  l'adattamento di base gratis. Sostituisce il controllo di flusso minimo di fase 2, che oggi è un
  «non più di due fotogrammi non riscontrati» scritto a mano in `manda_fotogramma`;
- **`queueDepth == 0xFFFFFFFF`** già gestito (§5 di `REFERENCE.md`), ma qui va provato: un regolatore
  che aspetta riscontri che non arriveranno più si blocca per sempre;
- ~~adattamento di **risoluzione** come rete di sicurezza, riusando la macchina della fase 6~~ →
  **spostato alla fase 10**, con la misura che lo ha deciso: il riquadro qui sopra.

**Si vede**: si strozza la banda con `tc` e il desktop **rallenta senza bloccarsi**; nel registro
compaiono RTT e banda stimata, e il numero di fotogrammi in volo segue la strozzatura invece di
crescere all'infinito.

**Prima di scrivere**: §5 di `REFERENCE.md` (i riscontri e la sospensione), §16 di
`protocollo-rdp.md`, e §10 di `gnome-remote-desktop.md` per il regolatore.

**Rischi noti**: la misura di banda del protocollo è grossolana e va sui fotogrammi grandi; su una
rete locale come quella del banco l'RTT è vicino a zero e non discrimina nulla. Serve una
strozzatura artificiale per avere qualcosa da regolare.

---

## Fase 8 — Audio e appunti

**Taglia: media.**

> ### A che punto è, il 5 agosto 2026
>
> **Voci 0, 1 e 2 fatte e misurate, e l'audio adesso si ascolta.** Il banco è
> `src/remotix-c/prove/fase8.sh`: **22 controlli, zero falliti**.
>
> | | |
> |---|---|
> | **il sink virtuale** | nasce nella sessione, la sessione lo prende come uscita predefinita, e **resta in piedi dopo la disconnessione** — è della sessione, non della connessione |
> | **audio in uscita** | PCM 44 100 Hz stereo sul canale dinamico; il client **riscontra i blocchi**, e **l'onda che suona è quella che la sessione ha suonato** — registrata e misurata, non dedotta |
> | **il silenzio** | non si spedisce: dieci secondi di desktop muto costano 678 fotogrammi invece di 440 000 |
> | **appunti: testo** | nei due versi, verificato leggendo dall'altra parte con gli strumenti di quel lato |
> | **appunti: immagini** | PNG della sessione → BMP del client e ritorno, con **misura, orientamento e colori conservati** |
>
> Gli appunti hanno un banco tutto loro — `prove/fase8-appunti.sh`, **15 controlli, zero falliti** —
> che prova quel che si rompe davvero: 90 KB di testo in un colpo, accenti ed **emoji** (che in
> UTF-16 sono coppie surrogate), i fine riga contati sul filo e non sulla selezione del client,
> l'HTML con la sua intestazione di offset, un'immagine 320×200, cinque copie di fila, **la
> riconnessione**, e una richiesta di un formato che non c'è — che è il caso peggiore, perché si
> presenta come un desktop piantato invece che come un errore.
>
> ### ✅ Il rumore era `freerdp_dsp_encode`, e la questione n.10 è chiusa
>
> *Misurato il 5 agosto 2026 con `banco-b/spia-dsp.c`. `REFERENCE.md` **R24**.*
>
> `SendSamples` fa passare i campioni dal DSP di FreeRDP anche quando non c'è niente da convertire, e
> quel DSP — compilato con FFmpeg, come su Debian — manda il PCM a 16 bit **con segno** di RDP al
> codificatore `AV_CODEC_ID_PCM_U16LE`, che è **senza segno**: somma `0x8000` a ogni campione. Entra
> un seno di ampiezza 3000, esce la stessa onda a fondo scala, `x ^ 0x8000`, su 8 820 campioni su
> 8 820.
>
> Si spedisce ora con **`SendSamples2`**, che scrive i byte come sono — la stessa scelta di
> `gnome-remote-desktop`, e per noi non è un aggiramento: la sorgente **è** il formato scelto dal
> client, quindi non c'era niente da convertire.
>
> **La bisezione è costata quaranta righe**, ed era già scritta nella questione n.10: fra i campioni
> puliti e i PDU ben formati restavano due anelli, e li si è chiamati da fuori invece di guardarli
> attraverso il server.
>
> **Il banco ha imparato la lezione più cara.** Era **verde** mentre l'audio era inascoltabile:
> contava fotogrammi spediti e blocchi riscontrati, e il difetto cambiava i campioni senza cambiarne
> il numero. Adesso `fase8.sh` **registra quel che il client suona** e ne guarda la forma d'onda
> (sezione 4-bis), col registratore certificato prima — e il controllo è stato provato a rovescio:
> sulla stessa registrazione col segno ribaltato diventa rosso.
>
> | | picco | rms | campioni a fondo scala |
> |---|---|---|---|
> | quel che il client suona adesso | 3 000 | 2 105 | **0 %** |
> | quel che suonava prima (stessa onda, segno ribaltato) | 32 768 | 31 689 | **100 %** |
>
> ### ✅ E poi scoppiettava, ed era il ritmo dei blocchi
>
> *Sentito dall'utente — «credo si tratti di jitter» — e misurato col registro di `rdpsnd` del
> client, il 5 agosto 2026. `REFERENCE.md` **R25**.*
>
> Tolto il rumore, il suono si sentiva a scatti, e la causa era **nostra e recente**: `SendSamples`
> accumulava i campioni fino a 50 ms prima di comporre un PDU, `SendSamples2` no. Da lì la dimensione
> dei blocchi era diventata quella del **ciclo**, che si sveglia anche per un tasto o per un
> riscontro. Il client di FreeRDP butta i blocchi più corti della metà di quel che ha già in coda:
> **35 blocchi da 5 ms buttati in sei secondi**, uno per uno, scritti nel suo registro.
>
> **La risposta stava in xrdp**, ed è stata l'idea dell'utente andarla a cercare lì:
> `sound_send_wave_data` non spedisce mai un blocco parziale — accumula in un buffer da 8 192 byte e
> manda solo quando è pieno. Ora fa così anche REMOTIX: **un blocco intero per giro, mai parziale,
> mai due di fila**; se è in ritardo ne manda **uno più grande** invece di due, perché un blocco
> grande porta con sé una tolleranza grande; oltre mezzo secondo di coda butta il passato. E manda
> **mezzo secondo di coda di silenzio** prima di tacere: smettere al primo blocco muto costava uno
> strappo a ogni ripresa — su una voce, a ogni pausa.
>
> | Sei secondi di tono | prima | dopo |
> |---|---|---|
> | blocchi buttati dal client | 35 | **0** |
> | vuoti | 17 | 1 |
> | strappi nell'onda suonata | 168 | **4**, e due sono nella sorgente |
>
> Lo studio di xrdp — i blocchi fissi, il regolatore sui riscontri, i due workaround per mstsc — sta
> in §8.3.1 di `xrdp-funzionalita.md`, che prima non lo aveva.
>
> ### 🎧 La prova dell'orecchio, fatta: si sente, ed è in sincrono
>
> *[M, 5 agosto 2026, utente], su tutti e tre i client.*
>
> | Client | Esito |
> |---|---|
> | `xfreerdp3` su Linux | **audio sincronizzato col video e comprensibile**, con qualche micro-stutter |
> | **mstsc** | idem |
> | **RDM** su Android | comprensibile, ma il micro-stutter è **molto più marcato** |
>
> La regola dei tre client è soddisfatta per il *contenuto*: quel che si sente è quel che la sessione
> suona. Resta il **micro-stutter**, che è la questione n.13 di `REFERENCE.md` — e la n.5 si
> ridimensiona: audio e grafica insieme su Android **reggono**, semplicemente reggono peggio. La
> motivazione con cui `gnome-remote-desktop` spegne l'audio ai client Android descrive una
> degradazione, non un'impossibilità.
>
> ### ✅ E il micro-stutter non era il canale: era la cattura senza priorità
>
> *Misurato il 5 agosto 2026, con lo schermo sotto carico. `REFERENCE.md` **R26**.*
>
> Due passi, e il secondo ha spostato il colpevole dove non lo cercavo.
>
> **Uno.** L'audio era cadenzato dal ciclo che codifica il video, e nell'ordine sbagliato: si
> svuotava la coda dei canali, *poi* si componeva il blocco audio, *poi* si codificava il fotogramma
> — quindi ogni blocco partiva **al giro dopo, dopo una codifica intera**. Tre righe spostate: a
> desktop fermo gli strappi scendono da 4 a **2**, cioè alle sole giunture della sorgente.
>
> **Due.** Con lo schermo che scorre, però, ne comparivano **venti**. E la bisezione ha detto che i
> salti stavano **già nei byte consegnati al canale**: non il trasporto, la **cattura**. Il servizio
> gira come utente con `RLIMIT_RTPRIO` a zero, quindi PipeWire non *può* chiedere `SCHED_FIFO` e il
> suo `data-loop` perde il quanto ogni volta che il codificatore si prende un core.
>
> Una riga nell'unità systemd — `LimitRTPRIO=20` — e sotto lo stesso carico:
>
> | Sei secondi di tono, schermo che scorre | senza priorità | con priorità |
> |---|---|---|
> | picco dell'onda consegnata | 3 299, deformata | **3 000 esatto** |
> | strappi in quel che il client suona | 12 | **7, identici a quelli consegnati** |
>
> Le due analisi coincidono fino al conteggio dei campioni: **il trasporto non aggiunge più niente**,
> e quel che resta è già nella sorgente.
>
> **Ricaduta sulla fase 9**: l'accelerazione hardware toglierà la contesa alla radice, ma non era
> l'unica leva e non era la prima. La priorità serve comunque, perché una sessione che lavora
> competerà sempre con la cattura.
>
> **Su RDM lo scatto è sopravvissuto**, e allora si è misurato il server *mentre l'utente guardava un
> video **YouTube 1080p30***: sugli stessi quattro vCPU, insieme, la decodifica del video, la
> composizione di GNOME in software e la codifica RFX Progressive di 2560×984. 130 secondi di
> sessione vera, e **il lato server è pulito** — fotogrammi catturati a
> +0,17 % dagli attesi, zero xrun in tutto il grafo audio, coda fra 10 e 69 ms mai in crescita, tutti
> i blocchi riscontrati. All'orecchio lo scatto è **periodico**, che è la forma di un confine di
> buffer e non di una rete che inciampa: l'indiziato è il telefono, che decodifica RFX Progressive a
> 2560×984 in software mentre rende l'audio — la stessa contesa che abbiamo appena corretto sul
> server, a parti invertite (§10 n.13 di `REFERENCE.md`).
>
> Il server ora **misura anche il viaggio dei riscontri** e lo scrive nel registro: è il segnale con
> cui xrdp regola il flusso, e serve alla n.12 quando verrà il momento.
>
> **Quel che resta**: la prova che costa meno — abbassare risoluzione o fotogrammi al secondo su RDM
> e riascoltare: se si liscia, è la CPU del telefono e non c'è niente da correggere qui. Poi le voci
> **3, 4 e 5**: AAC, microfono, appunti dei file.
>
> ⏸ **Il microfono (voce 4) è sospeso per decisione dell'utente, 6 agosto 2026**: si scriverà quando
> sarà lui a dirlo. Non tiene aperta la fase — le voci 0, 1 e 2 sono chiuse e misurate — e non è un
> prerequisito della fase 9.
>
> **La clipboard invece è chiusa sul campo**: copia-incolla di testo verde su `xfreerdp3`, **mstsc e
> RDM** — la regola dei tre client soddisfatta, non dedotta da uno solo. [M, 5 agosto 2026]
>
> E strada facendo la prova su mstsc ha trovato un difetto che non era di questa fase: minimizzando
> la finestra la connessione cadeva, perché non dichiaravamo `refreshRectSupport` e
> `suppressOutputSupport` (**R23**). Corretto e misurato: a finestra minimizzata i fotogrammi si
> fermano, riaprendola ripartono, e la connessione regge.
>
> Cinque difetti trovati dai banchi e corretti, tutti **silenziosi per costruzione**: il silenzio
> spedito a 1,4 Mbit/s; il formato PipeWire non verificato (che avrebbe fatto passare del rumore per
> audio); i tipi mime dentro una tupla nel segnale di Mutter, che spegneva un verso solo degli
> appunti; l'annuncio dei formati spedito prima che il client dichiarasse le proprie capacità, che
> lasciava vuoti gli appunti di chi si ricollegava; e `DisableClipboard`, che in Mutter 48.7 è a
> senso unico — chiamarlo alla disconnessione uccideva la clipboard per tutta la sessione grafica
> (`REFERENCE.md` §7.6).
>
> Il sesto — il segno dei campioni ribaltato dal DSP — è l'unico che i banchi **non** hanno trovato,
> ed è il motivo per cui adesso il banco ascolta invece di contare.

> ### ⛔ Quel che la misura d'apertura ha trovato: non c'è niente da catturare
>
> *Misurato il 5 agosto 2026, prima di scrivere una riga.* `REFERENCE.md` §7.5.
>
> Il contenuto qui sotto diceva «audio in uscita PCM, sorgente PipeWire», e dava per scontato che
> una sorgente ci fosse. **Non c'è.** Nella sessione senza monitor, con `pipewire`,
> `pipewire-pulse` e `wireplumber` tutti attivi, `wpctl status` mostra **zero device, zero sink,
> zero source**: la macchina non ha una scheda sonora, ed è il caso normale per un server.
>
> Il riferimento non copre il caso: `gnome-remote-desktop` cattura il monitor di ogni
> `Audio/Sink` che trova nel registro PipeWire, e un sink non lo crea mai. Con il suo codice, sulla
> VM di runtime, non arriverebbe un campione.
>
> **Quindi la fase 8 ha un pezzo in più, ed è il primo**: REMOTIX crea il proprio sink virtuale
> nella sessione (`support.null-audio-sink`), che diventa il predefinito perché è l'unico, e ne
> cattura il monitor. Provato: un tono suonato da un'applicazione è tornato dalla cattura
> identico, 44 100 Hz, 2 canali, picco invariato.
>
> **Il sink appartiene alla sessione, la cattura alla connessione** — la stessa divisione del palco
> (fase 5). Un sink che nascesse col client farebbe cambiare dispositivo alle applicazioni a ogni
> riconnessione.

**Obiettivo.** Suono e copia-incolla.

**Contenuto, in quest'ordine di priorità.**

0. **il sink virtuale della sessione**, senza il quale i punti 1 e 3 non hanno sorgente. Vive nel
   palco, come cattura e monitor virtuale;
1. **audio in uscita PCM** — funziona con tutti e tre i client (§1.5 di `REFERENCE.md`), quindi si
   scrive per primo. Sul canale **dinamico** `AUDIO_PLAYBACK_DVC`, che è quello con cui il
   riferimento ha negoziato PCM sia con mstsc sia con RDM (§1.2, §1.7), e che non compete con i
   canali statici;
2. **appunti: testo e immagini** — poche centinaia di righe. Canale statico `cliprdr` da un lato,
   e dall'altro la clipboard della sessione, che Mutter espone sulla **stessa sessione
   `RemoteDesktop`** del palco (`EnableClipboard`, `SetSelection`, `SelectionRead`,
   `SelectionWrite`, più i segnali `SelectionOwnerChanged` e `SelectionTransfer`);
3. **AAC**, solo dopo aver chiuso la questione n.8: se nessuno lo negozia, è codice per nessuno;
4. **microfono** (MS-RDPEAI) — ⏸ **sospeso per decisione dell'utente, 6 agosto 2026**: non si scrive
   finché non sarà lui a deciderlo. Non tiene aperta la fase e non blocca la 9;
5. **appunti: file** — è un progetto a sé, con un filesystem virtuale FUSE. Va valutato se vale.

**Si vede**: si sente l'audio da tutti e tre i client; si copia un testo dal desktop remoto e lo si
incolla in locale, e viceversa.

**Prima di scrivere**: **§7.5** di `REFERENCE.md` (il sink che non c'è) e **§7.6** (le due
asimmetrie della clipboard di Mutter, e perché le immagini passano tutte da `CF_DIB`); §1.5 e §10
n.5 e n.8 (che cosa i client negoziano davvero); **R21**, **R22** e **R24** — le trappole dell'API
dei canali `rdpsnd` e `cliprdr`, e il DSP che ribalta il segno del PCM; **R19** — che vale anche per
l'audio: i campioni si accodano, e partono quando il ciclo svuota la coda. Poi §14 e §15 di `protocollo-rdp.md`, e §14.1-14.2 di
`gnome-remote-desktop.md`.

**Come si prova**: `xfreerdp3 /sound /clipboard` per primo, perché è quello che dice di più nel
registro; poi mstsc e RDM, che sono i due severi. Le due domande aperte si chiudono qui e non
altrove: **n.8** guardando i formati che ciascun client dichiara, **n.5** tenendo audio e video
insieme su RDM per qualche minuto.

**Rischi noti**: la questione n.5 — audio e grafica insieme su Android. Da misurare qui.

---

## Fase 9 — Accelerazione hardware ✅ **CHIUSA il 7 agosto 2026, con la copia zero rinviata**

> ### Come è stata chiusa
>
> **L'accelerazione hardware c'è e funziona**: AVC420 codificato in GPU con `h264_vaapi`, immagine
> corretta su `xfreerdp3` e **mstsc** [M, utente, 7 agosto]. L'obiettivo della fase — «togliere la
> codifica dalla CPU» — è raggiunto e misurato.
>
> **La cattura a copia zero è rinviata**, e non per prudenza: acceso il DMA-BUF, il client vede
> riapparire schermate già passate. La causa è **misurata** (`REFERENCE.md` R29): il buffer che
> Mutter presta non è un fotogramma intero, è un *diff*. Due tentativi di correzione sono falliti nel
> corso della stessa giornata, il secondo peggiorando le cose su mstsc.
>
> | | ms di CPU per fotogramma |
> |---|---|
> | copia zero + codifica in GPU — **rinviata** | 6 |
> | memoria + codifica in GPU — **quel che si spedisce** | **18** |
>
> La copia zero **nasce spenta nel codice** (`palco.c`), e `REMOTIX_DMABUF=1` la accende.
>
> ⛔ **Fino al pomeriggio del 7 agosto quel predefinito stava in `/etc/default/remotix`, e non ha
> retto mezza giornata**: il file vive in RAM, è stato riscritto per portare la porta alla 3392, la
> riga di guardia è sparita con lui e l'utente si è ritrovato il difetto in faccia — *«di nuovo le
> schermate vecchie a programma chiuso e lo schermo che flasha»*. **La protezione di un difetto noto
> non si affida a una riga di configurazione che si può perdere.** Il racconto sta in fondo a R29.
>
> **Quel che resta da guardare**: la prova su **RDM** sul percorso in memoria. `xfreerdp3` e mstsc
> sono stati verificati il 7 agosto.
>
> ### ⛔ La regola che è costata la giornata
>
> **Non si spedisce una correzione collaudata su un banco che il difetto non lo mostra.** Le due
> riproduzioni costruite il 7 agosto — client nel contenitore su loopback, client su un'altra
> macchina in LAN — restavano verdi mentre il difetto era vivo nell'uso reale; la correzione scritta
> su quella base è stata provata dall'utente e ha peggiorato mstsc. È la regola dei tre client
> (§1.1 di `REFERENCE.md`) applicata a **chi collauda**, non a che cosa si collauda: *una prova verde
> sul banco sbagliato non vale, e chi la usa per validare fa collaudare l'utente.*
>
> Da cui il vincolo per chi riprenderà la copia zero: **prima il banco che il difetto lo fa comparire
> da solo, poi la correzione.** Senza quel banco, la copia zero non si fa.

**Taglia: media.**

> ### A che punto è, il 6 agosto 2026
>
> **La GPU è dentro la VM e codifica.** La scheda integrata Intel dell'host (`0000:00:02.0`) è
> ceduta alla macchina di runtime con VFIO; dentro la VM `i915` la prende, `vainfo` dichiara
> `VAProfileH264High : VAEntrypointEncSliceLP`, e REMOTIX ci codifica sopra.
>
> **Il codificatore si sceglie per nome, a runtime** (§3.1 di `SPECIFICA.md`), con `--codificatore`:
> `h264_vaapi`, `h264_qsv`, `h264_nvenc`, `libx264`, più `freerdp` che tiene raggiungibile il
> vecchio percorso — non per nostalgia, ma perché è il termine di paragone con cui si misura.
>
> **Il confronto, a parità di scena, misura e macchina** (`prove/fase9.sh confronto`, scena
> sintetica 2560×984, quattro vCPU):
>
> | | fotogrammi/s | CPU | ms di CPU per fotogramma |
> |---|---|---|---|
> | AVC420 via FreeRDP — il «prima» | 29,0 | **1,21 core** | 41 |
> | AVC420 via `libx264` — stesso lavoro, in casa nostra | 26,7 | 0,74 core | 27 |
> | **AVC420 via `h264_vaapi` — in GPU** | **22,7** | **0,47 core** | 20 |
> | RemoteFX Progressive — il percorso di Android | 30,4 | 1,20 core | 39 |
>
> **Il consumo di CPU è calato del 61 %. E il ritmo è calato del 22 %** — che non è un dettaglio da
> nascondere sotto il primo numero.
>
> ### ⛔ Il collo di bottiglia si è spostato, e adesso si sa dove
>
> Il registro misura il tempo di ogni fotogramma diviso in tre, e la risposta è netta:
>
> | conversione BGRx → NV12, in CPU | caricamento sulla scheda | **codifica vera** |
> |---|---|---|
> | **12,5 ms** | 3,1 ms | **3,8 ms** |
>
> Tolta la codifica dalla CPU, il tempo se lo prende il pezzo rimasto. È `REFERENCE.md` **R28**, e
> indica da sé il lavoro che resta: la **cattura zero-copy con DMA-BUF**, che consegna il fotogramma
> già sulla scheda e lascia la conversione a lei. Adesso si sa quanto vale prima di scriverla.
>
> *(Provato e scartato: dare più thread a `libswscale` non cambia niente — 13,8 ms contro 12,5.)*
>
> ### Tre cose che, mancando, non davano un errore utile
>
> Stanno in `REFERENCE.md` **R27**, e sono costate la mattinata: il nodo di rendering giusto **non è
> il primo** (`renderD128` è virtio-gpu); il firmware sta in `firmware-intel-graphics` e **non** in
> `firmware-misc-nonfree`, e senza di lui il driver offre il solo `CQP`; l'entrypoint delle Intel
> recenti è solo quello a basso consumo, quindi `low_power=1`.
>
> ### Il DMA-BUF: i due fatti che lo rendevano impossibile, tolti di mezzo
>
> *6 agosto 2026, e sono misure, non deduzioni.*
>
> 1. **Il compositore disegnava sulla scheda sbagliata.** Con `virtio-gpu` presente, Mutter disegna
>    lì, e i fotogrammi che consegna a PipeWire sono buffer di *quella* scheda: un DMA-BUF così non
>    si importa nella Intel — nel migliore dei casi è una copia fra due dispositivi. Ora la VM ha
>    **una sola scheda DRM**, la Intel: `virtio-gpu` non si dichiara più a QEMU e `bochs` si spegne
>    dal lato del kernel dell'ospite (`modprobe.blacklist=bochs`).
>    ⚠ La VGA d'emergenza resta a QEMU e serve: togliendola del tutto (`-vga none`) la macchina
>    annuncia l'avvio e non risponde più.
> 2. **Mutter i DMA-BUF li dà**, e non era scontato: dichiarando i modificatori nel formato **e** il
>    tipo di dati in `SPA_PARAM_Buffers` — che è la metà della regola che non stava da nessuna parte
>    — il registro dice `i fotogrammi arrivano come DMA-BUF`, modificatore `0x0` (lineare).
>
> In dote arriva la cosa che §8.6-bis di `REFERENCE.md` elencava come falsante: **GNOME non compone
> più in software.** E la fase 3 passa tutti i controlli sulla nuova configurazione.
>
> **La negoziazione stava dietro `REMOTIX_DMABUF=1`**, perché chiedere i DMA-BUF senza saperli
> leggere non dà errore: dà uno schermo fermo. ✅ **L'interruttore si è girato il 6 agosto**: adesso
> la copia zero è il percorso normale e `REMOTIX_DMABUF=0` la spegne — vedi più sotto, e `R30`.
>
> ### ✅ La cattura a copia zero, fatta e misurata
>
> *6 agosto 2026. Il dettaglio dei cinque rifiuti silenziosi che è costata sta in `REFERENCE.md`
> **R29**.*
>
> Il DMA-BUF che Mutter consegna a PipeWire arriva al codificatore **senza essere copiato**: si
> importa come superficie della scheda (filtro `hwmap`), si converte in NV12 e si depone dentro una
> superficie già allineata e già nera (`overlay_vaapi`) — un solo passaggio sulla scheda, e il bordo
> di R4 è riempito senza allungare l'immagine.
>
> **Misurato sul desktop vero**, stessa scena mossa dagli stessi tasti:
>
> | | fotogrammi | CPU | ms di CPU per fotogramma |
> |---|---|---|---|
> | in memoria | 110 | 0,28 core | **25** |
> | **a copia zero** | 142 | **0,11 core** | **7** |
>
> Il costo per fotogramma cala del **72 %**, e i fotogrammi consegnati salgono del 29 % a parità di
> tutto il resto. Sono spariti, in un colpo solo: la copia dalla cattura alla tela, la conversione di
> colore in CPU (i 12,5 ms di R28) e il caricamento sulla scheda.
>
> **Il terzo punto — «trattenere il buffer» — non serviva**, ed è la cosa che vale la pena ricordare:
> convertendo subito, quel che si conserva per R9 è la **nostra** superficie, e il buffer torna al
> compositore appena la richiamata finisce. Tenere in ostaggio una risorsa di chi ce l'ha prestata
> sarebbe stato il modo peggiore di rispettare quella regola.
>
> ### ✅ La copia zero è il percorso normale, e il palco sa tornare in memoria
>
> *6 agosto 2026. Il come, per intero, sta in `REFERENCE.md` **R30**.*
>
> Era la condizione che teneva l'interruttore chiuso: il palco che lavora sulla scheda non ha pixel
> in CPU, e RemoteFX Progressive — cioè ogni client Android — li vuole lì. Adesso il palco **cambia
> strada a cattura viva**, dalla stessa porta del ridimensionamento (`pw_stream_update_params`), e
> il giro completo costa **18 ms**.
>
> **A sceglierla non è il codec, è il codificatore che si è aperto davvero** — la stessa lezione di
> R27 applicata a un'altra domanda. Tre casi finiscono lì, e due non si vedrebbero guardando il
> codec: RemoteFX Progressive, `--codificatore libx264` (che è AVC420 ma comprime in CPU, ed è il
> termine di paragone con cui si misura questa fase), e un `h264_vaapi` che abbia ripiegato sul
> proprio nodo.
>
> **L'interruttore si è girato**: la copia zero è il percorso predefinito, e `REMOTIX_DMABUF=0` la
> spegne — non per prudenza, ma perché è il termine di paragone del banco.
>
> ### ✅ Il banco della copia zero è dentro `prove/fase9.sh`
>
> `bash prove/fase9.sh copia-zero`, **11 controlli, zero falliti**, due esecuzioni consecutive. Sul
> **desktop vero**, non sulla scena sintetica: quella la disegniamo noi in memoria, e un
> caricamento lo pagherebbe sempre. La scena si muove battendo tasti dal client, come in fase 4.
>
> | Stessa scena, stessi tasti | in memoria | a copia zero |
> |---|---|---|
> | ms di CPU per fotogramma | 24–25 | **7–9** |
> | fotogrammi consegnati in 10 s | 99–105 | **120–148** |
>
> ```
> OK  la copia zero toglie almeno il 40% del costo per fotogramma
> OK  il palco e' tornato in memoria per il client RemoteFX Progressive
> OK  i fotogrammi arrivano davvero in memoria dopo il cambio di strada
> OK  il client RemoteFX Progressive riceve fotogrammi: 33 spediti
> OK  il palco e' tornato sulla scheda quando il client se n'e' andato
> OK  con libx264 il palco e' tornato in memoria, pur essendo AVC420
> ```
>
> ### ⛔ E il banco della fase 6 ha trovato un segfault della fase 9
>
> Con `--immagine-di-prova` il server non crea alcun palco, e `palco_superfici(NULL)` lo uccideva
> **a ogni connessione AVC420**: il registro finiva su «EGFX negoziato» e il client vedeva
> `BIO_read retries exceeded`, cioè una caduta di rete dalla parte sbagliata del filo. Era lì dalla
> prima metà della fase 9, e rendeva inservibili la sezione 1 di `fase6.sh`, `fase2.sh` e il modo
> `confronto` di questo stesso banco.
>
> **La lezione, che non riguarda il NULL**: una fase che tocca un percorso condiviso si chiude
> rieseguendo i banchi delle fasi che quel percorso lo attraversavano già. Corretto e riverificato:
> `fase3.sh`, `fase6.sh` (23 controlli) e `fase9.sh confronto` tornano tutti verdi, e il confronto
> ripete i numeri della tabella qui sopra.
>
> ### ⛔ La prova su `xfreerdp3` ha aperto una caccia, e ha spostato la macchina
>
> *6 agosto 2026, sera. L'utente segnala «dei flash» e poi «due immagini sovrapposte».*
>
> Quattro sospetti, eliminati uno per uno con una misura ciascuno — ed è il metodo di R10-bis
> applicato a un difetto che il banco non poteva vedere, perché conta fotogrammi e qui il numero era
> giusto:
>
> | sospetto | escluso da |
> |---|---|
> | la cattura a copia zero | difetto presente con `REMOTIX_DMABUF=0`, cioè i pixel in memoria |
> | il codificatore in GPU | difetto presente con `--codificatore libx264`, in CPU |
> | l'hypervisor | difetto presente **sul ferro nudo**, dopo il trasloco |
> | quel che Mutter consegna | i fotogrammi salvati prima di RDP sono puliti (**R10**) |
>
> **Quel che resta è il transitorio del client**, che riadatta l'immagine vecchia alla tela nuova nei
> ~120 ms in cui non spediamo. Non è un difetto nostro, ed è quel che l'utente stesso aveva letto:
> *«è dovuto allo stream video che dev'essere riadattato»*.
>
> **Ma la caccia ha trovato quattro difetti veri**, e nessuno di questi si sarebbe visto senza di lei:
>
> | difetto | trovato da |
> |---|---|
> | il ridimensionamento **perdeva la copia zero** e scivolava su `libx264` in CPU (**R30**) | l'utente, ridimensionando a video in corso |
> | `palco_superfici(NULL)` **uccideva il server** con la scena sintetica | il banco della fase 6 |
> | il ridimensionamento **inchiodava 2,5 s** su un desktop che lavora (**R10**) | il registro della sessione dell'utente |
> | un doppio rilascio nella spia dei fotogrammi | l'utente, e la colpa era di chi scrive |
>
> ### 🖥 La macchina di runtime è passata al ferro nudo
>
> *Deciso dall'utente: «le prove che riguardano l'hardware devono essere fatte su HW nativo».*
>
> `provision-server.sh` installa GNOME e il necessario **sul server**, e `server.sh` lo guida con gli
> stessi verbi di `vm.sh`. Cadono tutti e quattro i falsanti di §8.6-bis di `REFERENCE.md`; il conto
> sta in §6.2 di `SPECIFICA.md`, compreso quel che si perde.
>
> **Ricaduta immediata**: tutte le misure di questa fase sono state prese nella VM. Restano valide
> come confronti — stessa macchina, stesso minuto — e **vanno rifatte sul ferro** prima di essere
> citate come cifre del prodotto.
>
> ### ✅ E sul ferro la fase 9 gira per intero, con i banchi traslocati
>
> I banchi parlavano `vm.sh`. Ora includono **`prove/runtime.sh`**, che decide da dove si comanda la
> macchina di runtime: `server` è il predefinito, `RUNTIME=vm` riporta tutto sulla VM — e non per
> nostalgia, ma perché la VM è la sola macchina su cui esistano le misure delle fasi 2-9, quindi
> resta il termine di paragone finché non saranno rifatte.
>
> **`fase3.sh`, `fase6.sh` (23 controlli) e `fase9.sh copia-zero` (16 controlli) passano sul ferro.**
>
> | stessa scena, desktop vero | in memoria | a copia zero |
> |---|---|---|
> | ms di CPU per fotogramma — **sul ferro** | 18 | **6** |
> | ms di CPU per fotogramma — nella VM | 24–25 | 7–9 |
> | fotogrammi in 10 s (ferro) | 125 | **137** |
>
> **Due trappole pagate nel trasloco**, entrambe in `REFERENCE.md` §8.6-ter: il **gestore systemd
> dell'utente non aggiorna i gruppi**, quindi Mutter disegnava in software e la copia zero non si
> accendeva — e il sospetto naturale (due schede DRM invece di una) era sbagliato; e i banchi hanno
> bisogno di `sudo` **senza password**, perché eseguono con lo standard input chiuso e lì `sudo` non
> fallisce: non torna.
>
> ### ⛔ E la prova sui client ha trovato il difetto che tiene aperta la fase
>
> *7 agosto 2026. Il dettaglio, con la registrazione contata fotogramma per fotogramma, sta in
> `REFERENCE.md` **R29**, sesto punto.*
>
> **A copia zero lo schermo alterna due fotogrammi**: la scrivania di adesso e una **già passata**,
> entrambe intere e pulite, avanti e indietro per secondi. L'utente l'aveva segnalato il 6 agosto
> come «chiudendo Firefox ricompare un fotogramma di prima», e il riquadro qui sopra lo aveva
> archiviato come sintomo senza spiegazione: era lo stesso difetto, visto piano.
>
> **Misurato su due client** — `xfreerdp3` e mstsc — cambiando una cosa sola: con
> `REMOTIX_DMABUF=0`, cioè gli stessi pixel per la strada della memoria e lo stesso codificatore in
> GPU, **sparisce su entrambi**.
>
> Il meccanismo non è ancora misurato; i due sospetti — sincronizzazione mancante e ridisegno
> parziale nei buffer riciclati — hanno la stessa radice: **non chiediamo alcun metadato a
> PipeWire**. Finché non è corretto, **la copia zero resta spenta**, e con lei il guadagno della
> fase: 18 ms di CPU per fotogramma invece di 6.
>
> ### Che cosa resta
>
> 0. **Il difetto dell'alternanza qui sopra.** Viene prima di tutto il resto: è la strada dei pixel
>    che la fase 9 esiste per aprire.
> 1. **La prova sui tre client, ed è quella che chiude la fase.** Il banco conta i fotogrammi e
>    guarda i registri; che l'immagine sia **giusta** lo dicono mstsc e RDM (§1.1). Vale doppio qui,
>    perché la copia zero cambia la strada che i pixel percorrono e un errore di geometria o di
>    colore su quella strada non produce alcun errore — produce un'immagine sbagliata. Su RDM la
>    domanda è precisa: con la copia zero accesa il palco torna in memoria per lui, e il desktop si
>    deve vedere come prima.
> 2. **`h264_qsv` e `h264_nvenc`** sono scritti e non provati: su questa macchina non c'è NVIDIA, e
>    QSV vuole il proprio runtime. Vanno dichiarati non misurati finché non lo saranno.
> 3. **`fase2.sh` non gira**, e non per il codice: la sua directory di banco
>    (`tmp/banco-b/dati`) è rimasta di `root` dal 4 agosto e `openssl` non ci scrive il certificato.
>    Il percorso che collauda — scena sintetica dentro il contenitore — è comunque coperto verde
>    dalla sezione 1 di `fase6.sh`.

**Obiettivo.** Togliere la codifica dalla CPU.

**Contenuto**: cattura **zero-copy** con DMA-BUF da PipeWire; codificatore scelto per nome a runtime
(`h264_vaapi`, `h264_qsv`, `h264_nvenc`), con `libx264` come ripiego sempre disponibile. Passthrough
GPU sulla VM, orientamento verso l'integrata Intel (§6.2 di `SPECIFICA.md`).

**Si vede**: a parità di scena, il consumo di CPU crolla e si può salire di risoluzione.

**Prima di cominciare**, quel che la fase 8 ha lasciato in eredità a questa — misurato il 5 agosto
2026:

| | |
|---|---|
| **La macchina di oggi non ha 3D affatto** | `virtio-gpu` **senza virgl**: GNOME disegna in software, sulla stessa CPU del codificatore. La scheda completa della VM, con la colonna «che cosa falsa», è in **§8.6-bis** di `REFERENCE.md` — da leggere prima di attribuire alla fase 9 meriti che sono del passthrough |
| **Il codificatore affama la cattura audio** | e si è visto: senza priorità di tempo reale la cattura perdeva campioni sotto carico (**R26**). La priorità c'è ora, e **va tenuta anche dopo**: togliere la codifica dalla CPU riduce la contesa, non la elimina |
| **C'è un carico di riferimento, e regge** | YouTube 1080p30 su RDM a 2560×984 in RFX Progressive, tutto in software: l'audio è arrivato con la cattura a +0,17 % dagli attesi e zero xrun. È il metro con cui misurare il «prima» e il «dopo» |
| **La rete della VM è SLIRP** | uno stack TCP/IP in spazio utente. Se la fase 9 alza la risoluzione, è il prossimo collo di bottiglia, ed è finto: va sciolto con un `tap` prima di dare la colpa al codec |

**Si misura il guadagno, non lo si dichiara**: a parità di scena e di carico di riferimento, il
consumo di CPU e i fotogrammi al secondo prima e dopo. Il banco della fase 7 dà già i numeri della
rete; per l'audio bastano i contatori di `fase8.sh`, che ora sanno ascoltare.

**Rischi noti**: è qui che si scopre se **Xwayland** (questione n.8) era un problema di accelerazione
mancante nella VM. Da riverificare appena la VM ha una GPU vera.

> **Non si taratura la qualità qui**, e non è pigrizia: si sceglie il codificatore e si verifica che
> funzioni. Dove metterne il punto di lavoro è la fase 10, che viene subito dopo perché ha bisogno di
> sapere **quale** codificatore si spedisce.

---

## Fase 10 — La qualità ✅ **CHIUSA il 7 agosto 2026 senza essere rifatta, per giudizio dell'utente**

**Taglia: grande** — e non è stata spesa.

> ### ✅ «La qualità va bene così»
>
> *Detto dall'utente il 7 agosto 2026, dopo aver provato sui tre client il punto di lavoro nuovo
> (cadenza a 60, AVC420 a banda costante verso i 10 Mbps).* Il metro è quel che si vede (§7 di
> `SPECIFICA.md`), e il metro ha detto che basta.
>
> **La fase era già stata azzerata quella mattina** (il racconto è più sotto, e va letto lo stesso:
> le tre ragioni del fallimento valgono oltre la fase). Adesso non va nemmeno rifatta, e c'è una
> ragione tecnica che si somma al giudizio: **quel che la fase 10 avrebbe ottimizzato è precisamente
> ciò che l'utente ha dichiarato di non volere ottimizzato.** R31 misura che a banda costante un
> desktop fermo spende quasi dieci megabit per nulla — ma §3.1 dice che **i 10 Mbps sono un
> pavimento, non un budget**, e che «la banda non spesa non torna utile a nessuno». Il controllo
> attuale è quindi allineato alla decisione, non in difetto rispetto a essa.
>
> **Che cosa resta in piedi come rete di sicurezza**, e non è poco: il regolatore della fase 7, che
> misurato regge la strozzatura senza bloccarsi (30 → 23 fps a 250 kbit/s). L'adattamento di
> **risoluzione** non c'è e non si può fare — lo rende un client su tre (§10.2 di `REFERENCE.md`) —
> ed è già scritto in §3.1 di `SPECIFICA.md` come funzionalità non realizzabile.
>
> ⚠ **Il limite dichiarato del giudizio**: è stato dato su una rete di casa, con RTT fra 5 e 19 ms e
> banda abbondante. Su un collegamento povero l'immagine degraderà, e l'unica leva sarà il ritmo. Se
> un giorno REMOTIX uscirà di casa, questa fase si riapre — non perché il giudizio fosse sbagliato,
> ma perché sarebbe un'altra domanda.

> ### ⛔ AZZERATA il 7 agosto 2026, per decisione dell'utente
>
> *«La fase 10 va azzerata e ricominciare da zero.»*
>
> Il codice è tornato allo stato di chiusura della fase 9: controllo del bitrate com'era, nessun
> adattamento, nessuno strumento nuovo. I banchi sono stati rimossi. **La fase è da rifare da capo.**
>
> **Perché è andata così, e va letto prima di ricominciare** — l'errore non è stato tecnico:
>
> 1. **Si è spedita sul server di lavoro una modifica a quel che si vede, validata solo sul banco.**
>    Il passaggio a VBR aveva dalla sua PSNR, SSIM e un fotogramma fermo guardato a occhio; non aveva
>    il giudizio dell'utente sul desktop vero, che è il metro (§7 di `SPECIFICA.md`). Il giudizio,
>    quando è arrivato, è stato: *«siamo tornati indietro»*.
> 2. **Si è ottimizzato nella direzione sbagliata.** «Spendere meno banda» era considerato un
>    guadagno; per il prodotto i 10 Mbps sono un **pavimento** e non un budget (§3.1 di
>    `SPECIFICA.md`, precisato dall'utente lo stesso giorno). Metà delle misure erano giuste e
>    servivano a rispondere alla domanda sbagliata.
> 3. **Non si è controllato lo stato della macchina prima di cominciare.** `/etc/default/remotix`
>    era stato letto all'inizio della sessione e la riga che teneva spenta la copia zero non c'era
>    più; nessuno l'ha notato, e l'utente si è ritrovato il difetto di R29 in faccia a metà giornata.
>
> **Che cosa resta valido, e non va rifatto**: le misure, che stanno in `REFERENCE.md` con data e
> fonte — R31 (il modo di controllo del bitrate dedotto dal driver, il pavimento dei ~4 Mbit/s del
> codificatore hardware), §5.1 (la banda misurata può essere vecchia di due ordini di grandezza),
> §10.2 (mstsc non rende lo scaled output). E le decisioni dell'utente: risoluzione adattiva fuori,
> AVC444 fuori, codifica per regioni fuori, 10 Mbps come pavimento.
>
> **Che cosa sappiamo che cambia l'ordine, quando si ricomincerà**: il tetto dei fotogrammi non è nel
> nostro ciclo. Misurato affiancando i due contatori: la cattura consegna 17,7 fotogrammi al secondo
> e noi ne spediamo 17,9 — **si spedisce tutto quello che il compositore dà**. Il ritmo lo decide la
> consegna della cattura, e sul percorso in memoria quella la paga Mutter, che si copia lo schermo
> intero a ogni fotogramma. Cioè: **la qualità percepita passa da R29**, non dalla taratura del
> bitrate.

> ### ✅ E la sera del 7 agosto la cattura è stata misurata: i 18 erano nostri
>
> *Il compito che l'utente aveva posto — «misuriamo le performance che Mutter è in grado di erogare»
> — è stato eseguito. Le tabelle per intero stanno in **R32** di `REFERENCE.md`; il banco in
> `/media/REMOTIX/tmp/banco-compositori`, fuori dal prodotto.*
>
> **REMOTIX dichiara 30 fotogrammi al secondo alla cattura, e Mutter ne consegna 18. Dichiarandone
> 60 ne consegna 37.** Il numero che la fase 10 aveva davanti come un fatto della macchina era una
> nostra riga di codice.
>
> | | |
> |---|---|
> | **Da fare per primo, e costa una riga** | portare `--fotogrammi` a 60. Dal compositore 18 → 37, e **fino al client 18,7 → 32,4** a 1080p, misurato sulla catena intera: il minimo dell'utente è superato. Nessuna scelta di codifica ha mai spostato tanto |
> | ⛔ **E la copia zero non serve a questo** | sulla catena intera dà 31,5 contro 32,4 a 1080p e 17,0 contro 16,9 a 4K: **non tocca il ritmo**. Taglia la CPU per fotogramma da 16 a 3 ms. Chi riprende R29 lo faccia per il consumo, non per la fluidità |
> | ⚠ **Il 4K non è ancora misurato** | il banco si ferma a 17 fps, ma il tappo è il **client di prova** che decodifica in software: `in volo 2 di 2` su 835 campioni, server a 0,08 core. Serve un client con decodifica hardware prima di dire qualunque cosa sul 4K |
> | ✅ **Provato dall'utente su tutti e tre i client** | 7 agosto 2026: `xfreerdp3` **a posto**, **mstsc «va benissimo»** (29–33 fps, AVC420 in GPU), **RDM «performance eccellenti»** (23–29, RemoteFX Progressive). La regola dei tre client è soddisfatta |
> | ✅ **E il 60 è nel codice** | `main.c`, non più in `/etc/default/remotix` — quel file vive in RAM e si sarebbe perso al primo riavvio, come si perse la riga della copia zero. Binario ridistribuito e verificato con la sola configurazione predefinita: **33,3 fps a 1080p** sulla catena intera |
> | Che cosa **non** serve | abbassare la risoluzione o la profondità di colore. Misurato: alla cattura non costano niente, 4K rende come 1080p, BGRA come BGRx |
> | Che cosa la copia zero **non** dà | fotogrammi: 36,6 contro 34,0. Dà CPU (R29/R30). Chi la riprende lo faccia per quella |
> | Il tetto che resta | ~37, ed è di Mutter: il client disegna 60 su uno schermo virtuale a 60 Hz, e il compositore perde il 40 % dei ridisegni. **KWin e wlroots, sulla stessa macchina, non lo perdono** |

**Obiettivo.** Rendere guardabile il risultato dentro la banda disponibile.

**Contenuto.**

- **controllo del bitrate** verso il punto di lavoro di §3.1 di `SPECIFICA.md`, sul codificatore che
  la fase 9 ha scelto. **Qui siamo soli**: nessuno dei due riferimenti lo fa —
  `gnome-remote-desktop` lascia il quantizzatore costante (§9.1 di `gnome-remote-desktop.md`);
- **il punto di lavoro cambia con il codificatore**: §5.5 di `SPECIFICA.md` — gli encoder hardware
  rendono peggio a bitrate bassi. Va misurato per ciascuno di quelli che la fase 9 accende, non
  dedotto da uno;
- **AVC444 per fotogramma** su connessioni buone, come il riferimento: si manda la sola luma e la si
  completa con la croma quando c'è margine. Solo mstsc lo rende (§1.7 di `REFERENCE.md`);
- la **codifica per regioni** di §5.2 di `SPECIFICA.md`, se RemoteFX Progressive la rende gratis;
- **l'adattamento di risoluzione**, arrivato dalla fase 7 il 5 agosto 2026 con la misura che lo ha
  spostato (riquadro della fase 7). Qui è al posto giusto: la scala 4K → 2K → 1080p di §3.1 di
  `SPECIFICA.md` è una scelta di **qualità**, non di controllo di flusso, e si tara insieme al
  bitrate invece che contro di lui.
  **Da valutare prima di scrivere**: `MAPSURFACETOSCALEDOUTPUT`, che lascia il desktop alla misura
  chiesta dal client e rimpicciolisce solo la superficie codificata. È l'unica strada che non litiga
  con MS-RDPEDISP — cambiare la misura del monitor virtuale ridispone le finestre dell'utente, e a
  schermo intero il client rimanda la propria richiesta ogni secondo. FreeRDP la espone già lato
  server; **quali client la rendano davvero è da misurare**, ed è la prima cosa da fare.

**Si vede**: il desktop resta fluido mentre si scorre una pagina; **il testo è leggibile**; strozzando
la banda l'immagine degrada senza bloccarsi.

**Prima di scrivere**: R3, R4, R11, §1.7, e §9 di `gnome-remote-desktop.md`.

**Rischi noti**: è la fase con più incognite di misura e meno riferimenti. Richiede di confrontare
varianti **a parità di scena** — cosa che la fase 6 ha reso possibile fermando la geometria, e la
fase 7 misurabile dando una bilancia.

---

## Fase 11 — Gli altri desktop 🟡 **KDE ✅ CHIUSO l'8 agosto 2026 — il prossimo è XFCE**

> ### ✅ KDE, in una riga
>
> **Cinque voci su cinque, tutte chiuse dal giudizio dell'utente su tre client** (xfreerdp, RDM
> Android, mstsc). REMOTIX parla due compositori, e le porte hanno retto: `compositore.h` per schermo
> e input, `appunti.h` per la clipboard — nessuna delle due nomina un desktop.
>
> **Che cosa resta da KDE, e non è lavoro di KDE**:
>
> | | |
> |---|---|
> | ⛔ «una via audio nuova parte al massimo» non funziona | percorso **condiviso**: fallisce identico su Mutter, si cerca senza KDE (`REFERENCE.md` §7.5) |
> | ⏸ la regola udev per la GPU | scritta, **non installata**: nega il nodo a tutta la sessione dell'utente, e la decisione è sua |
> | ⏸ riavviare la sessione quando un client chiede un'altra misura | decisione, non lavoro. La proposta è **no**: il ridimensionamento vero arriva con KWin 6.8 |
>
> ### ⬅ E il prossimo è **XFCE**, cioè la terza famiglia: **wlroots**
>
> *Deciso dall'utente l'8 agosto 2026, chiudendo KDE.*
>
> ⭐ **Una parte del lavoro è già fatta**: `appunti_wlr.c` usa `zwlr_data_control_manager_v1`, che è
> un protocollo **di wlroots** — KWin lo implementa, ma la famiglia è quella. Gli appunti di XFCE
> dovrebbero funzionare senza scrivere niente.
>
> ⚠ **E una parte cambia più che fra Mutter e KWin**: wlroots **fa tirare** i fotogrammi
> (`zwlr_screencopy_manager_v1`, una richiesta per fotogramma) invece di spingerli su PipeWire. È la
> domanda 2 di `LEZIONI.md` §3, ed è l'unica che cambia la **forma** del codice invece che i suoi
> parametri.

**Il taglio di apertura**: si rifà quel che ha funzionato per KDE — prima lo studio del codice, poi
un pomeriggio di misure sulle quattordici domande di `LEZIONI.md` §3, poi si scrive. Il passo zero
resta *«chi, al mondo, fa questa cosa su questo desktop?»* (§9): per wlroots la risposta è
**`wayvnc`** e i portali di `xdg-desktop-portal-wlr`, e vanno letti prima.

**Taglia: grande.**

> **Deciso dall'utente il 7 agosto 2026**, chiudendo GNOME: *«prossimo DE KDE»*. La fase 12
> (confezionamento) viene dopo i desktop, non prima — *«prima di arrivare alla pacchettizzazione ci
> sono almeno altri 3 DE da supportare»*.
>
> **⛔ Le due domande da chiudere prima di progettare qualunque cosa** — stanno nel riquadro qui
> sotto, e sono: **come si ottiene il permesso della cattura** per un servizio non presidiato, e
> **se KWin senza monitor può disegnare sulla GPU**. Nessuna delle due è un dettaglio: la prima
> decide se la strada esiste, la seconda se i numeri misurati valgono su una macchina da server.

> ### ✅ LO STUDIO DEL CODICE DI KDE È FATTO — [`kde.md`](kde.md), 7 agosto 2026
>
> *Otto repository di KDE clonati alla versione di Trixie (**6.3.6**) in `reference-kde/`, letti da
> dieci ricerche parallele. **Da leggere per intero prima di scrivere una riga**, come
> `LEZIONI.md`.*
>
> **Le quattro domande della fase hanno una risposta**, e tre su quattro sono migliori del previsto:
>
> | | |
> |---|---|
> | **Il permesso della cattura** | ✅ **un file `.desktop` con `X-KDE-Wayland-Interfaces`**: nessun dialogo, mai, nemmeno la prima volta; sopravvive a riavvio e logout; zero patch. È il meccanismo con cui si autorizzano il portale di KDE e `krfb-virtualmonitor`. Due vincoli di confezionamento: **non girare come root**, e `Exec=` deve nominare il binario vero |
> | **La GPU senza monitor** | ✅ il backend `--virtual` **apre da sé un render node e usa EGL/gbm**: ⛔ **la nostra misura del 7 agosto è contraddetta dal codice e va rifatta** (`REFERENCE.md` R32, riquadro nuovo) |
> | **L'avvio della sessione** | ✅ due sole variabili obbligatorie, unità del compositore sovrascritta, `startplasma-wayland`. Nessun `ConditionEnvironment`, e il bus di sessione **non muore al logout**. Ma `--xwayland` **non è opzionale**: ksmserver dereferenzia il display X11 senza controlli |
> | **L'input** | ✅ **libei**, con **una sola chiamata D-Bus a KWin** e **senza alcun controllo di permesso**: `input.c` e `tastiera.c` si riusano quasi per intero. `SPECIFICA.md` §3.8 è stata corretta |
>
> **E due risultati che non erano nelle domande:**
>
> 1. ✅ **il difetto che tiene spenta la copia zero su GNOME non si ripresenta**: KWin consegna
>    **fotogrammi interi** e **si sincronizza lui** (`glFlush`, `glFinish` su NVidia e llvmpipe). La
>    superficie di accumulo di R29 su KDE non serve — e il codice di KWin suggerisce l'ipotesi nuova
>    per Mutter: *non c'è fence implicita da aspettare se chi disegna non fa il flush*;
> 2. ⛔ **la risoluzione dinamica su KDE non si fa come su GNOME**: un output virtuale ha **un solo
>    modo, immutabile**, e va chiuso e ricreato. Su KDE però **questo non trascina l'input** (che è
>    indipendente dalla cattura), quindi il prezzo è un buco video e il riposizionamento delle
>    finestre — lo stesso prezzo che su GNOME ha fatto scartare l'adattamento automatico.
>
> **Tre scelte vanno messe davanti all'utente prima di scrivere** (`kde.md` §13.4): `--virtual`
> contro `--drm`; che fare del ridimensionamento; e se aprire **anche** una connessione Wayland per
> avere BlocMaiusc e BlocNum. E **dodici misure** aprono la fase, in ordine (`kde.md` §14): le due
> che decidono sono «il `.desktop` autorizza davvero?» e «`Activate()` di logind riesce su una
> sessione senza seat?».

> ### ✅ E IL BANCO È STATO FATTO LA SERA STESSA — cinque misure su dodici, con le due decisive
>
> *[M, 7 agosto 2026. Script in `reference-kde/banco/` (`misure-kde.sh`, `permesso-kde.sh` …
> `permesso6-kde.sh`), macchina lasciata pulita: nessun compositore residuo, nessuna porta toccata.
> Il dettaglio in `kde.md` §14.]*
>
> | Misura | Esito |
> |---|---|
> | **M1 — il `.desktop` autorizza?** | ✅ **sì**, con `NoDisplay=true`, la forma di KRdp. ⛔ **Ma serve anche `XDG_MENU_PREFIX=plasma-`**: senza, l'indice dei servizi di KDE si costruisce vuoto e KWin non trova nessun file. In una sessione Plasma la mette `startplasma`; **in un ambiente composto da noi va messa a mano** |
> | **M2 — `--drm` è praticabile senza seat?** | ⛔ **no**: esce con stato 1 (`Failed to activate … session` → `No suitable DRM devices have been found`), e **non** per permessi Unix. Quindi **`--virtual`**, e **una delle tre scelte da porre all'utente si è chiusa da sé** |
> | **M3 — GPU o software?** | ✅ **GPU**: `renderD129` aperto, `libEGL_mesa` + `libgbm`, `zwp_linux_dmabuf_v1` v4. **R32 è stata corretta**: i numeri restano, l'etichetta «in software» era sbagliata — e la prima misura non poteva vedere, perché `kwin_wayland` è **non dumpable** (xattr `security.capability`) |
> | **M5 — `connectToEIS`?** | ✅ **`(handle 0, 1)`** da una shell SSH qualunque: nessuna sessione, nessun portale, nessun dialogo, nessun `.desktop` |
> | **M6 — Debian compila KWin con libeis?** | ✅ **sì**: `eis.so` in `kwin-common` 4:6.3.6-1 |
>
> **Nessuna misura ha smentito il codice**; una ha smentito **noi**, e una ha aggiunto un requisito che
> nessuna lettura di codice mostrava.

> ### ✅ E L'8 AGOSTO 2026 SONO STATE CHIUSE LE ALTRE SETTE — con tre risultati che cambiano il piano
>
> *[M] Script in `reference-kde/banco/` (`misure2..6-kde.sh`, `plasma..plasma6-kde.sh`). Il dettaglio
> in `kde.md` §14; la macchina è stata lasciata pulita e i permessi ripristinati.*
>
> **La catena intera è stata vista funzionare**: sessione Plasma avviata da zero con
> `startplasma-wayland`, plasmashell in **1 secondo**, cattura **autorizzata** dal solo `.desktop`,
> **flusso PipeWire attivo**, logout ordinato che **non porta via il bus**.
>
> ⭐ **1. La copia zero è la condizione per il numero che hai chiesto.** Sulla **Intel integrata**
> (la GPU che hai scelto), con la scena in movimento:
>
> | | copia zero | in memoria |
> |---|---|---|
> | 1920×1080 | **59,2** | 43,3 |
> | **3840×2160** | **59,0** | **27,0** |
>
> Cioè **60 fps a 4K sono raggiungibili su una GPU integrata**, ma solo a copia zero: il collo di
> bottiglia è **la copia**, non il compositore. La fase 9, rinviata su GNOME per il «diff», su KDE
> non ha quel difetto — i fotogrammi sono interi, va solo aspettata la fence.
>
> ⛔ **2. `KWIN_COMPOSE=O2` non protegge** (M4): KWin ripiega in software **e parte**. Ogni misura va
> accompagnata dalla stringa del renderer, che KWin dà su D-Bus.
>
> ⛔ **3. Il modo ovvio di scegliere la GPU rompe il permesso della cattura**: `InaccessiblePaths=`
> nell'unità del compositore dà la Intel **e chiude il cancello**. La via buona sono i **permessi del
> nodo** (per il prodotto: una regola udev per id PCI) — provata, con cattura e flusso funzionanti.
>
> **Le altre**: M8 la cattura è **indipendente dal VT** (cambio di VT: tutto resta vivo); M9 il bus
> **sopravvive** al logout; M10 KWin **non inverte** la rotella e tratta i due assi alla stessa
> maniera (l'adattamento è nostro); M11 KWin **non cade** su nessuna misura assurda (ma la validazione
> non è misurabile con `--virtual`); M12 il dialogo modale è **il secondo** dei rischi — il primo è che
> plasmashell scriva `SceneGraphBackend=software` **in modo persistente** nella casa dell'utente.

> ### ✅ LE TRE DECISIONI, PRESE DALL'UTENTE l'8 agosto 2026
>
> | | |
> |---|---|
> | **Copia zero** | ✅ **adesso, dentro KDE** — quindi la cattura **nasce a copia zero**, non si scrive due volte. È la condizione dei 60 fps a 4K (`kde.md` §5.7) |
> | **Ridimensionamento** | ✅ **misura fissa alla connessione** su Trixie, **scritta nella forma della negoziazione PipeWire** perché su KWin 6.8 si accenda da sé (`kde.md` §8.2) |
> | **BlocMaiusc/BlocNum** | ✅ **si legge lo stato vero** (`org_kde_kwin_keystate`): su KDE la connessione Wayland c'è già per la cattura, quindi costa un nome nel `.desktop` e un ascoltatore |

### Il piano di lavoro della fase 11 — cinque voci, in quest'ordine

*Scritto l'8 agosto 2026, dopo lo studio (`kde.md`), due giornate di banco e le tre decisioni. Ogni
voce ha un «fatto quando» che si giudica **vedendo**, non leggendo (`LEZIONI.md` §7.3).*

| # | Voce | Che cosa comprende | Fatto quando |
|---|---|---|---|
| **0** | **Il debito di lettura** ✅ **fatto l'8 agosto** | riversati in `kde.md`: **§12.0-bis**, i **quattordici difetti di KRdp da non ripetere** che ci riguardano (con `file:riga`), e **§8.2-bis**, la **guardia contro il ciclo di rinegoziazione** — che è obbligatoria per la decisione sul ridimensionamento. ⚠ Restano da riversare tre dettagli, e servono **dentro** le voci che li usano, non prima: la banda a **finestra a orologio** (voce 1), il **cursore** in 171 righe (voce 1), il **gate a tre condizioni** degli appunti (voce 4) | ✅ `kde.md` §12.0-bis e §8.2-bis |
| **1** | **Cattura, a copia zero dal principio** ✅ **FATTA l'8 agosto 2026** | client Wayland (`zkde_screencast_unstable_v1` v5, `stream_output`); il `.desktop` con **due** interfacce; `XDG_MENU_PREFIX` nell'ambiente; consumatore PipeWire riusato dalle fasi 6 e 9; **attesa della fence** (§4.8); buffer di solo cursore **scartati** (§4.7); `DRM_FORMAT_MOD_LINEAR` per l'encoder; niente superficie di accumulo, perché i fotogrammi sono interi | ✅ **il desktop KDE si vede su `xfreerdp3`**, e la cattura consegna **58,1 fps a 1080p e 58,4 a 4K** sulla Intel — contro i 59,2 e 59,0 del banco |
| **2** | **Input** ✅ **scritta, provata e GIUDICATA l'8 agosto 2026** | `connectToEIS` su D-Bus; riuso di `input.c` e `tastiera.c`; **`ei_device_scroll_discrete(±120)`** invece del nostro `/120 → ×10`; regioni cercate **per geometria**; dispositivi ricreati a ogni cambio di output; **`org_kde_kwin_keystate`** per le spie | tastiera, mouse, rotella (verso compreso) e spie **giusti a occhio**, su tre client |
| **3** | **Sessione e macchina** ✅ **scritta e provata l'8 agosto 2026** — ⚠ *la regola udev è scritta ma NON installata* | ambiente da zero con le due variabili obbligatorie **+ `XDG_MENU_PREFIX`**; drop-in dell'unità con `--virtual --width/--height` e **`--xwayland`**, **senza alcuna opzione che implichi un mount namespace**; **regola udev** che esclude la GPU da non usare (per id PCI); `--no-lockscreen` e `AddInhibition(types=4)` di powerdevil; logout via `org.kde.Shutdown` | ✅ connessione **da macchina appena avviata**, sessione che non si blocca da sé, logout che non lascia processi |
| **4** | **Appunti** ✅ **CHIUSA l'8 agosto 2026, banco E giudizio** | `zwlr_data_control_manager_v1` v2, senza permessi; guardia contro l'eco di `setSelection`; passo minimo verso klipper | ✅ `prove/fase11-appunti.sh` zero guasti, e l'utente: *«clipboard OK su Linux, mstsc e Android»* |
| **5** | **Il giudizio** ✅ **CHIUSA l'8 agosto 2026: tutti e tre i client, e va bene** | tre client, due connessioni di fila, e la parola dell'utente su quel che vede | l'utente dice che va bene (`LEZIONI.md` §2.6) |

> ### ✅ IL GIUDIZIO DELL'UTENTE — 8 agosto 2026, xfreerdp e RDM
>
> **«La riproduzione di un video a 1080p è alla massima fluidità»**, **«audio OK, audio e video sono
> sincronizzati»**, **«la rotella è ok, anche il terminale funziona (comprese le operazioni
> privilegiate)»**, e su Android **«performance sotto RDM sono eccellenti»**.
>
> I numeri letti *durante* quella riproduzione, che confermano il giudizio invece di sostituirlo:
> **57,8 fotogrammi al secondo consegnati**, codifica **1,7 ms** per fotogramma, **conversione 0,0 ms
> e caricamento 0,0 ms** — la copia zero DMA-BUF, che su Mutter non si era ottenuta (fase 9). Il
> codificatore è impegnato al **10 %** del tempo disponibile: il margine per i 4K a 60 c'è.
> L'audio nello stesso tratto: **0 blocchi buttati**, coda fra 1,8 e 11 KB.
>
> **I tre difetti li ha trovati l'utente, non il banco** — ed è la lezione §2.4 in forma concreta:
>
> | difetto | esito |
> |---|---|
> | **doppio puntatore** | primo tentativo: nascondere quello del **client** con `SYSPTR_NULL` — ✅ su xfreerdp, ⛔ **su RDM restano due**, perché il secondo è il *touch pointer* dell'app, fuori dal protocollo. ⭐ **Cura definitiva**: il cursore di KDE si rende **trasparente** con un tema `XCURSOR_THEME` 1×1 ad alfa zero, e il puntatore torna a essere quello del client — come su Mutter, uno solo su ogni client (il riquadro sul cursore in testa a `kde.md`) |
> | **il cursore del volume non governava niente** | `monitor.channel-volumes` mancava sul nostro sink: in PipeWire il volume si applica **a valle** della presa del monitor (`kde.md` §10.5). ⚠ Una misura fatta su un sink creato con `pactl` **assolveva** il codice, perché `pipewire-pulse` quella proprietà la mette da sé |
> | **«Blocca» e «Cambia utente» nel menu** | tolte con KIOSK (`kde.md` §10.6). ⚠ Hanno effetto **dal prossimo avvio di sessione** |
>
> ✅ **E il terzo client c'è**: *«mstsc OK!»* — TLS puro senza NLA regge anche lì, come diceva R13.
> La regola dei tre client è soddisfatta, e con essa le voci 1, 2 e 3 sono chiuse **dal giudizio**,
> non dal banco.
>
> ✅ **E anche la voce 4 ha il suo giudizio, sui tre client**: *«clipboard OK su Linux, mstsc e
> Android»*. Contava più del solito averlo, perché la clipboard ha tre coinquilini — klipper, la
> sponda Xwayland, il client — e il banco ne pilota due.
>
> ## ✅ LA FASE 11 È CHIUSA per KDE: cinque voci su cinque, tutte con il giudizio dell'utente.

> ### ✅ LA VOCE 1 È CHIUSA — 8 agosto 2026, banco `prove/fase11.sh`
>
> **Si vede il desktop di KDE.** Il banco passa tutti i controlli, in due configurazioni
> (`bash prove/fase11.sh` per la prova funzionale, `INTEL=1 bash prove/fase11.sh misura` per il
> ritmo), e la macchina resta pulita: permessi del nodo ripristinati, nessun processo, nessuna porta.
>
> ```
> OK  zkde_screencast_unstable_v1 versione 5: il cancello e' aperto
> OK  cattura KDE avviata sull'uscita «Virtual-0» (3840x2160), nodo PipeWire 59
> OK  la tela ha preso la misura del compositore, non quella chiesta dal client
> OK  i pixel passano dalla scheda: copia zero
> OK  il client ha DECODIFICATO 24 fotogrammi del desktop di KDE
> OK  la cattura consegna 58.4 fotogrammi al secondo (2100 fotogrammi in 36.0 s)
> OK  l'attesa del disegno non e' mai scaduta
> ```
>
> | | 1920×1080 | 3840×2160 |
> |---|---|---|
> | **cattura, scena in movimento, Intel UHD 770** | **58,1** | **58,4** |
> | il banco del 7-8 agosto, stessa scena (`kde.md` §5.7) | 59,2 | 59,0 |
>
> Cioè: **la catena intera regge il numero del banco**, e il mezzo fotogramma che manca è la
> conversione sulla scheda che il banco non faceva. ⚠ **Il numero al CLIENT invece non misura
> REMOTIX**: 24 fotogrammi a 4K, e il tappo è `xfreerdp3` che decodifica l'H.264 in software sulla
> stessa macchina — è la nota di R32, e vale identica qui.
>
> **Che cosa è nuovo, per non cercarlo.**
>
> | File | Che cos'è |
> |---|---|
> | `src/kwin.c` | il client Wayland: registry, `stream_output`, il nodo, e una pompa di eventi che tiene viva la connessione — perché il flusso vive quanto lei |
> | `src/compositore.c` | la porta unica verso chi possiede schermo e input, con due implementazioni. Il palco non nomina più Mutter |
> | `src/protocolli/` | l'XML del protocollo di cattura, alla **v5**: quella che KWin 6.3.6 annuncia davvero |
> | `--compositore`, `--installa-desktop` | si riconosce da sé (§2 di `SPECIFICA.md`), e il file che apre il cancello lo scrive lui |
> | `prove/fase11.sh` | il banco, in due modi |
>
> **Quattro cose misurate che i documenti non dicevano:**
>
> 1. ✅ **il permesso funziona anche per noi**, non solo per KRdp: `.desktop` con `Exec=` sul binario
>    vero più `XDG_MENU_PREFIX=plasma-`, e il global compare;
> 2. ✅ **la fence si aspetta e basta**: 2 400 buffer su 2 400 arrivano col disegno in corso — la
>    misura dell'8 agosto confermata su un campione otto volte più grande — e **l'attesa non è mai
>    scaduta**. Il difetto di R29 non si presenta;
> 3. ⚠ **il modificatore negoziato è `0x0` (lineare)**, che è quello che il codificatore vuole
>    (`kde.md` §11.2). Chiederlo per primo è bastato;
> 4. ⛔ **la misura la impone il compositore, e va ADOTTATA in due punti**: nel palco e nella tela
>    grafica. Dichiarare al client la misura che ha chiesto significa un desktop che copre una parte
>    della superficie — il sintomo che il 3 agosto costò una caccia.
>
> ⚠ **Quel che la voce 1 NON ha provato, e non doveva**: input (voce 2), appunti (voce 4), la
> sessione avviata da REMOTIX e la regola udev per la GPU (voce 3). Nel banco la sessione Plasma la
> avvia lo script, e la Radeon si nega a mano.

> ### ✅ LA VOCE 2 È SCRITTA E PROVATA SUL BANCO — 8 agosto 2026
>
> ⏳ **Ma NON è chiusa**, e la differenza conta: il «fatto quando» dice *«giusti a occhio, su tre
> client»*, e nessuno l'ha ancora guardato. Quel che segue è un banco, non un giudizio.
>
> ```
> OK  canale di input concesso da KWin (gettone 1)
> OK  disposizione della sessione letta da libei: English (US)
> OK  14 eventi di tastiera inoltrati al compositore
> OK  regione del puntatore: 0,0 1920x1080 (mapping-id «assente»)
> OK  la rotella arriva come SCATTI DISCRETI nei due versi (1 su', 1 giu')
> OK  lucchetti secondo KWin: BlocMaiusc spento, BlocNum spento
> ```
>
> **Le quattro differenze del piano, tutte scritte:**
>
> | | |
> |---|---|
> | **`connectToEIS`** | una chiamata D-Bus, **nessun controllo di permesso**, e il descrittore viaggia in una lista a parte — `g_dbus_connection_call_with_unix_fd_list_sync`, perché il tipo `h` porta solo un **indice**: chi legge il corpo del messaggio si ritrova in mano uno zero e crede che sia un fd |
> | **la rotella** | `ei_device_scroll_discrete(±120)`, e il valore di RDP si passa **quasi com'è** — più semplice di Mutter, non più complicato. Con `scroll_delta` KWin darebbe `deltaV120 = 0`, cioè **nessuno scatto** |
> | **le regioni** | cercate per **geometria**, perché KWin non le marca affatto. Misurato: `mapping-id «assente»` e la regione trovata lo stesso |
> | **i lucchetti** | `org_kde_kwin_keystate` v5 sulla connessione Wayland che c'è già, con `fetchStates` per partire da un **fatto** invece che da un'ipotesi. Su Mutter la chiamata non fa niente, ed è giusto: là lo stato arriva da libei |
>
> ⛔ **E la cosa che rende tutto questo necessario invece che elegante**: su KWin
> `EI_EVENT_KEYBOARD_MODIFIERS` **non arriva mai** — `eis_device_keyboard_send_xkb_modifiers` non è
> chiamato in tutto KWin 6.3.6. Senza `keystate`, la riconciliazione di BlocMaiusc e BlocNum sarebbe
> **codice scritto che non gira**, che è peggio di codice che manca: nessuno va a cercarlo.
>
> ⚠ **Il banco ha trovato tre difetti, e tutti e tre erano suoi**: `xdotool windowactivate` senza
> gestore di finestre (si usa `windowfocus` e `--window`), una variabile non definita, e — la più
> istruttiva — **tre controlli rossi perché il banco girava a `diagnostica` mentre i tasti e gli
> scatti si scrivono a `traccia`**. Codice giusto, prova rossa: `LEZIONI.md` §2.3.

> ### ✅ LA VOCE 3 È SCRITTA E PROVATA — 8 agosto 2026, `bash prove/fase11.sh sessione`
>
> **La macchina è come dopo un riavvio: nessun desktop, nessun gestore d'accesso.** Il banco si
> astiene — non scrive il drop-in, non avvia Plasma — e il primo client che bussa deve trovare un
> desktop. Lo trova.
>
> ```
> OK  unita' del compositore sovrascritta: desktop 1280x720, senza schermo di blocco
> OK  avvio la sessione grafica: exec startplasma-wayland
> OK  il desktop e' venuto 1280x720: la misura la ha decisa il client che si e' collegato
> OK  la sentinella dell'uscita e' passiva: sorveglia un nome, non si registra
> OK  schermo della sessione tenuto acceso (inibizione 1)
> OK  il compositore gira senza schermo di blocco
> OK  REMOTIX se n'e' accorto SUBITO, non alla morte della cattura
> OK  il logout non ha lasciato processi
> OK  REMOTIX e' sopravvissuto al logout: puo' riaprire la sessione a chi torna
> ```
>
> ⭐ **La cosa che vale più delle altre: «misura fissa alla connessione» è diventata letterale.**
> `--virtual` vuole `--width/--height` all'avvio, e chi avvia la sessione è REMOTIX quando il primo
> client si collega — quindi la misura del desktop *è* quella che il client ha chiesto. Il ripiego
> che la decisione dell'8 agosto accettava («l'immagine si scala nel client») serve ora solo a chi si
> collega **dopo**, con una misura diversa.
>
> **Le cinque cose scritte, e la ragione di ciascuna:**
>
> | | |
> |---|---|
> | **l'ambiente** | le due obbligatorie **+ `XDG_MENU_PREFIX=plasma-`**, e nient'altro: `XDG_CURRENT_DESKTOP` e compagne le mette Plasma, e `DISPLAY`/`WAYLAND_DISPLAY`/`QT_QPA_PLATFORM` **vanno lasciate fuori** o KWin sceglie il backend annidato |
> | **il drop-in** | lo scrive REMOTIX in `$XDG_RUNTIME_DIR/systemd/user.control`, a ogni avvio, con la misura dentro. ⛔ Senza `InaccessiblePaths` né altro che implichi un mount namespace |
> | **`--no-lockscreen`** | non è una comodità: **a blocco attivo powerdevil ignora le inibizioni**, quindi è la precondizione di quella qui sotto |
> | **l'inibizione** | `AddInhibition(types=4)` — 4 è `ChangeScreenSettings` e implica `InterruptSession`; la via freedesktop mappa solo sul secondo e **non ferma lo schermo** |
> | **l'uscita** | sentinella **passiva** su `org.kde.Shutdown`. ⛔ L'equivalente di `RegisterClient` su KDE è XSMP su ICE, e chi si registrasse senza rispondere **frenerebbe il logout dell'utente di quindici secondi** |
>
> ⛔ **E un difetto trovato dal banco, che il codice letto non poteva mostrare**: powerdevil **non
> c'è ancora** quando il palco si monta — parte con `plasma-workspace.target`, tre anelli dopo il
> compositore — e chiedergli l'inibizione una volta sola significa non chiedergliela mai. L'errore
> era `ServiceUnknown`, cioè «non esiste **ancora**», non «non esisterà mai». Ora si aspetta, su un
> thread suo, senza trattenere il montaggio.
>
> ⚠ **La regola udev per la GPU è scritta e NON installata**, ed è una scelta: `/media/REMOTIX/gpu-udev.sh`
> la mette e la toglie, ma negare un nodo coi permessi lo nega **a tutta la sessione dell'utente** —
> non solo al compositore. È una modifica alla macchina con un prezzo, e il prezzo lo paga chi la
> usa: va messa quando l'utente lo decide, non di nascosto.

> ⚠ **Le due trappole da non dimenticare mentre si scrive**, entrambe pagate sul banco:
> **niente `InaccessiblePaths`** (o simili) nell'unità del compositore — chiude il cancello della
> cattura; e **`KWIN_COMPOSE=O2` non garantisce niente** — la GPU si verifica chiedendo a KWin la
> stringa del renderer.
>
> ⭐ **Le due lezioni di metodo sono in `LEZIONI.md` §1.9 e §1.10**, e valgono oltre KDE: *una lettura
> negata non è una lettura che dice zero*, e *prima di provare varianti, si accende il registro del
> componente che nega*.

> ### 🔎 Misurato in anticipo il 7 agosto 2026, e cambia il senso della fase
>
> *Le tabelle stanno in **R32** di `REFERENCE.md`. Qui c'è quel che serve a chi apre la fase.*
>
> Questa fase nasceva come «servire più desktop». La misura dei compositori le ha aggiunto un
> secondo motivo, e più forte: **il tetto dei fotogrammi che blocca il numero desiderato dell'utente
> è di Mutter, e gli altri due non ce l'hanno.** Stessa macchina, stesso minuto, stessa scena, stesso
> misuratore:
>
> | | 1920×1080 | 2560×1440 | 3840×2160 |
> |---|---|---|---|
> | **Mutter** (GPU) | 36,6 | 36,6 | 38,2 |
> | **KWin 6.3.6** (DMA-BUF) | **59,5** | **59,1** | **60,0** |
> | **sway 1.10.1 / labwc 0.8.3** (wlroots) | **61,0** | **61,5** | 40,3 |
>
> **Tre cose già pagate, che si incontrano al primo tentativo:**
>
> 1. **KWin tiene la cattura dietro un controllo di permessi.** `zkde_screencast_unstable_v1` non
>    viene annunciato a un client qualunque, e il sintomo è «questo compositore non ha il
>    protocollo». Sul banco lo si apre con `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1`; per il prodotto va
>    trovata la via che KDE prevede, ed è una domanda da chiudere **prima** di scrivere;
> 2. ~~**KWin senza monitor disegna in software.**~~ ⛔ **SMENTITO dal banco della sera stessa**
>    (riquadro sopra, misura M3): KWin `--virtual` **compone sulla GPU** — render node aperto,
>    `libEGL_mesa` e `libgbm` caricate, `zwp_linux_dmabuf_v1` v4 annunciato. La prima misura leggeva
>    un `/proc` che il kernel le negava. **I numeri di questa tabella valgono, e valgono su GPU**;
> 3. **wlroots non ha né D-Bus né un protocollo di cattura proprio**: si passa da
>    `zwlr_screencopy_manager_v1` con `copy_with_damage`, che è un modello **a tiro** — una richiesta
>    e un giro di socket per fotogramma. Nonostante questo consegna 61; a 4K scende a 40, e lì il
>    costo è la copia in memoria condivisa.
>
> Il pezzo di codice del banco che serve alla fase è già scritto e riusabile: `nodo-kwin` (il client
> del protocollo di KWin) e `misura-wlroots` (il client screencopy), in
> `/media/REMOTIX/tmp/banco-compositori`.
>
> **Prima di scrivere una riga si legge [`LEZIONI.md`](LEZIONI.md)**, ed è vincolante come §7.0 di
> `SPECIFICA.md`: la sezione 3 è la lista delle undici domande da fare al compositore nuovo, la
> sezione 9 è la ricetta per aprire un desktop, e la 8 elenca i vicoli ciechi già percorsi.

**Obiettivo.** KDE, poi XFCE e LXQt (che girano su wlroots), poi Cinnamon.

**Contenuto**: astrarre cattura e input dietro un'interfaccia con tre implementazioni — Mutter, KWin,
wlroots — e il rilevamento delle capacità all'avvio (§2 di `SPECIFICA.md`: rilevare le capacità, non
la distribuzione).

**Si vede**: la stessa sessione remota su un desktop diverso, senza cambiare configurazione.

**Prima di scrivere**: [`LEZIONI.md`](LEZIONI.md) per intero — §3 (le undici domande al compositore
nuovo, con le risposte di KWin già in tabella), §9 (la ricetta in otto passi), §8 (i vicoli ciechi).
Poi §7.3, R29, R30 e **R32** di `REFERENCE.md`, che sono le regole della cattura da rifare per un
compositore diverso.

**Le quattro domande hanno una risposta dal codice** (riquadro in testa alla fase, e
[`kde.md`](kde.md)). Quel che resta non è più «trovare la strada» ma **provarla**, in quest'ordine:

1. ✅ **Il permesso della cattura**: un file `.desktop` con
   `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1` (`kde.md` §3). **Prima misura della fase**:
   che autorizzi davvero, senza `KWIN_WAYLAND_NO_PERMISSION_CHECKS`. Finché non è provata, ogni altra
   misura gira su una scorciatoia da banco.
2. ⚠ **La GPU senza monitor**: il codice dice che il backend `--virtual` disegna in GPU per
   costruzione, e il DMA-BUF che abbiamo misurato lo conferma. **La misura del «software» va
   rifatta** con le due prove che non dipendono da quel che KWin dichiara — il tipo di buffer del
   flusso e la presenza di `zwp_linux_dmabuf_v1` (`kde.md` §5.3) — perché `KWIN_COMPOSE` **non
   protegge** e il ripiego in software è silenzioso per costruzione.
3. ✅ **La sessione Plasma senza monitor**: la ricetta è in `kde.md` §6.1. Due vincoli duri:
   `--xwayland` obbligatorio (ksmserver), e con `--virtual` **`stream_virtual_output` non funziona**
   — cioè la scelta del backend è anche la scelta di che cosa si può catturare.
4. ✅ **L'input**: **libei**, `connectToEIS` su D-Bus, nessun permesso (`kde.md` §7). Da provare che
   Debian compili KWin con `libeis`, e da cambiare la conversione della rotella
   (`ei_device_scroll_discrete(±120)` invece del nostro `/120 → ×10`).

**E una quinta domanda, che non era nell'elenco e costa più delle altre**: ⛔ **su KWin un output
virtuale non si ridimensiona** (`kde.md` §8). La risoluzione dinamica di fase 6 non si trasporta:
va scelto se rifare lo stream a ogni cambio — cosa che su KDE **non trascina l'input** — o servire la
sola misura della connessione. È una delle **tre scelte da mettere davanti all'utente** prima di
scrivere (`kde.md` §13.4).

**Rischi noti**: che il vincolo 1 non abbia una risposta accettabile per un servizio non presidiato.
In quel caso la fase cambia forma prima di cominciare, e va detto subito invece di scoprirlo a metà.

---

## Fase 12 — Servizio e confezionamento

**Taglia: media.**

**Obiettivo.** REMOTIX diventa un servizio di sistema installabile.

**Contenuto**: unità systemd; apertura di una **sessione PAM** per la sessione grafica remota, che
chiude la questione n.10; configurazione della macchina ospite (sospensione e spegnimento tolti alla
sessione remota, §3.4-bis); multiutente vero, una sessione per utente; pacchetto.

**Si vede**: si installa, si abilita, si riavvia la macchina e funziona.

---

## Ordine, e perché

```
0  misure     ──► 1 scheletro ──► 2 IL SERVER DISEGNA ──► 3 desktop ──► 4 input ──► 5 sessione
                                                                                        │
                                     6 risoluzione dinamica ◄───────────────────────────┘   ✅
                                                │
                     7 misura e regolatore ◄────┘   ✅ ← la BILANCIA: serve alle due che seguono
                                                │
                     8 audio/appunti ◄──────────┤
                     9 accelerazione ◄──────────┘
                                                │
                     10 QUALITÀ ◄───────────────┘      ✅ chiusa dal giudizio, non dalla taratura
                                                │
                              11 altri desktop ─┴─► 12 servizio
```

Quattro scelte d'ordine che vale la pena motivare:

1. **Le misure prima del codice** (fase 0). Due domande aperte decidono l'architettura del
   codificatore. Costano mezza giornata adesso e un mese dopo.
2. **Il protocollo prima del desktop** (fase 2 prima della 3). Con un'immagine sintetica, se qualcosa
   non si vede il sospetto è su una cosa sola. È la lezione di §5.4 applicata in anticipo.
3. **La bilancia prima di ciò che va pesato** (fase 7 prima di 8, 9 e 10). Audio e accelerazione si
   giudicano su quanta banda e quanta CPU costano: senza la misura della rete e il conteggio dei
   fotogrammi in volo, «*a parità di scena il consumo crolla*» è un'affermazione senza strumento.
   È la fase 0 applicata una seconda volta — il banco si certifica prima della misura.
4. **La taratura dopo il codificatore** (fase 10 dopo la 9). Il punto di lavoro del bitrate dipende
   da *quale* encoder si spedisce (§5.5 di `SPECIFICA.md`: quelli hardware rendono peggio a bitrate
   bassi). Tararlo su `libx264` e poi cambiare encoder è farlo due volte.

> **Nota sulla rinumerazione.** Fino al 5 agosto 2026 la fase 7 era una sola, «la qualità», e teneva
> insieme strumento e taratura. Le due metà sono diventate la **7** e la **10**; audio e
> accelerazione hanno tenuto il proprio numero, «altri desktop» e «servizio» sono slittate a **11** e
> **12**. I rimandi negli altri documenti sono stati aggiornati nello stesso momento.

---

## Il metodo, in quattro righe

1. **Prima di ogni fase si legge `REFERENCE.md`**, le sezioni indicate. È vincolante (§7.0 di
   `SPECIFICA.md`).
2. **Ogni fase finisce con qualcosa che si guarda**, sui tre client — non su uno.
3. **Quando una misura contraddice `REFERENCE.md`, si aggiorna il documento nello stesso momento**,
   con data e fonte.
4. **Una prova verde sul client sbagliato non vale.** Va fatta su quello che il difetto lo mostra.
