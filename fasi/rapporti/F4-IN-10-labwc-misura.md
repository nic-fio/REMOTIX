# labwc sa dare la misura ESATTA che gli chiediamo?

> Studio del 14 agosto 2026 · vale per **XFCE (labwc)** e **LXQt (labwc)** — `SPECIFICHE.md` §11.2
>
> | marca | |
> |---|---|
> | **`[M]`** | **misurato** — con macchina, data e comando |
> | **`[R]`** | letto nel codice, con `file:riga` |
> | **`[S]`** | letto in una specifica (XML di protocollo), con `file:riga` |
> | **`[?]`** | ipotizzato |
> | **`[✗]`** | assenza verificata, col comando e il controllo positivo |

---

## Il verdetto, in tre righe

1. ⭐ **SÌ, e non è più una lettura: è una misura.** labwc 0.8.3 su wlroots 0.18.2 ha
   dato **2133×772 esatti — larghezza dispari compresa** — e `zwlr_screencopy` ha annunciato
   lo stesso identico buffer, `stride = 8532 = 2133×4`, copia `ready`. Provate anche
   `1×1`, `3×5`, `1919×1079`, `2133×773`, `32768×1080`: **tutte esatte al pixel, nessun
   arrotondamento**, né silenzioso né dichiarato. `[M]`
2. ⛔ **Ma il pericolo che il mandato cercava non è dove lo cercava.** Non c'è arrotondamento
   silenzioso: c'è una **morte silenziosa**. A `32768×32768` labwc è uscito per **SIGSEGV**
   con **zero righe di log anche a `-V`**. `[M]` La misura non la limita nessuno — né wlroots
   né labwc — quindi **la deve limitare il nostro codice**, prima di chiedere.
3. ⚠ **E la frase da refutare cade su un pezzo nostro, non su labwc**: il nostro codificatore
   **rifiuta le larghezze dispari** — `src/codificatore.c:1512`, «4:2:0 vuole misure pari»
   `[R]`. Quindi `2133` da capo a fondo **non passa**: passa `2132`. La conversione non
   sparisce del tutto, **si riduce a un pixel per asse** — che non è una scala e non è una
   banda nera, ma è una regola da scrivere. ⭐ E `F4-IN-11-codificatore-misura.md`, misurato
   in parallelo, arriva alla stessa riga da valle: **il vincolo è «pari», e basta**. ⇒ **Il
   disegno dell'utente regge.**

⛔⛔ **E una quarta riga, che il mandato chiedeva di cercare e che è stata trovata:**

> **«XFCE (labwc)» e «LXQt (labwc)» NON sono lo stesso caso.** Il compositore è lo stesso e la
> risposta *sulla misura* è la stessa — ma su **XFCE c'è un secondo comandante degli output,
> `xfsettingsd`, che per impostazione predefinita SPEGNE ogni output nuovo**, cioè proprio il
> nostro. Su **LXQt quel comandante non esiste**. `[R]` — vedi §7. È una premessa nostra
> sbagliata e va corretta in `SPECIFICHE.md` §11.2.

**Risposta alla frase da refutare** — *«labwc/wlroots sa creare un'uscita virtuale di misura
arbitraria scelta dal client, sa cambiarla a sessione aperta senza rompere il flusso, e non
impone né arrotondamenti né limiti che ci obblighino a riscalare»*:

| pezzo della frase | esito |
|---|---|
| «uscita virtuale di misura arbitraria **scelta dal client**» | ⛔ **falso a metà**: il client **non crea** l'uscita, la **ridimensiona**. Nasce 1280×720 cablati e la misura si dà **dopo**, col protocollo `[M]` |
| «di misura arbitraria» | ✅ **vero nell'intervallo che ci serve**, e verificato fino a 32768×16384 `[M]` |
| «cambiarla a sessione aperta senza rompere il flusso» | ✅ **vero, e costa pochissimo**: **5,1 ms** di risposta, **0 fotogrammi persi su 25**, un solo fotogramma più lento (36 ms contro 16) `[M]` |
| «non impone arrotondamenti» | ✅ **vero** — nessun arrotondamento in nessun punto del percorso `[M]` `[R]` |
| «né limiti» | ⛔ **FALSO**. Il limite c'è, non è dichiarato, e superarlo **non dà un errore: dà un SIGSEGV** `[M]` |
| «che ci obblighino a riscalare» | ⚠ **vero per labwc, falso per noi**: l'obbligo delle misure pari viene dal **nostro** 4:2:0 `[R]` |

---

## Come è stata ottenuta la risposta

⭐ Il mandato prevedeva `[R]`, perché su `192.168.0.2` gira GNOME. **Ma labwc 0.8.3-1 è
installato su questa macchina** (`CHUWI`, Debian Trixie, `apt-cache policy labwc` →
`0.8.3-1`, `libwlroots-0.18.so`) `[M]`, e **il backend headless non chiede né seat né DRM**:
si è potuto avviare un labwc di prova accanto alla sessione GNOME, su un socket suo
(`wayland-1`), senza toccare niente.

Sono stati scritti due clienti Wayland di misura, con `wayland-scanner` sulle XML del repo:

| | |
|---|---|
| `misura.c` | chiede una misura con `zwlr_output_configuration_head_v1::set_custom_mode`, legge l'esito, **rilegge la misura vera** dal `wl_output.mode` e dall'evento `buffer` di `zwlr_screencopy`, e fa la copia davvero |
| `caldo.c` | cattura in continuo e **cambia misura a metà**, contando i fotogrammi persi e il buco di tempo |

Comando del compositore:
`WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 labwc -V -C <cfg minima>`
`[M]` 14 agosto 2026 · `Mesa Intel(R) Graphics (ADL-N)` · GLES2 · `wl_shm`.

⚠ **Il banco è in `scratchpad`, non nel repo.** `src/` non è stato toccato, nessun commit.
⚠ Le porte vietate non sono state sfiorate: il banco parla solo su socket Unix Wayland.

---

## 1. Il meccanismo: chi crea l'uscita e chi la cambia

### Non esiste «creare un output della misura che voglio»

⛔ `wlr_headless_add_output(backend, width, height)` accetta sì una misura qualunque —
`[R]` `reference-xfce/wlroots/backend/headless/output.c:106-147`, e la mette in
`wlr_output_state_set_custom_mode` alla riga **121** senza controllarla — ma **nessun
protocollo la chiama**. `[✗]` Nessuno dei dieci protocolli in `wlr-protocols/unstable/` crea
un output; `wlr-output-management` li *configura* soltanto, e la sua XML lo dice:
`[S]` *«Heads cannot be created nor destroyed by the client»*.

Quindi la misura iniziale non la scegliamo:

| via | misura iniziale | dove |
|---|---|---|
| `WLR_HEADLESS_OUTPUTS=N` | **1280×720** cablati | `[R]` `wlroots/backend/backend.c:229-241` · `[M]` confermato: `PRIMA wl_output.mode 1280x720` al primo avvio |
| output virtuale di labwc (`VirtualOutputAdd`) | **1920×1080** cablati | `[R]` `labwc/src/output-virtual.c:52-53`; ⚠ la firma accetta **solo il nome**, `output-virtual.h:8-9` |
| `LABWC_FALLBACK_OUTPUT` | 1920×1080 (stessa via) | `[R]` `labwc/src/output-virtual.c:109-136` — ⛔ scatta **solo a layout vuoto**, quindi vuole `WLR_HEADLESS_OUTPUTS=0` (con la variabile assente wlroots crea già un output e il layout non è mai vuoto) |

⭐ **Il nome conta più di quanto sembri**: `[S]` `labwc/docs/environment:70-76` consiglia un nome
che cominci per `NOOP-` *«così wayvnc lo riconosce come output virtuale e permette ai client di
ridimensionarlo»* — ed è esattamente il `strncmp` del §6. `[M]` Il nostro si chiamava
`HEADLESS-1`, che è l'altro prefisso riconosciuto.

⭐ **La forma obbligata è quindi: si avvia, ci si collega, e si ridimensiona.** Non «si crea
alla misura giusta».

### Il cambio lo fa `wlr-output-management-unstable-v1`, e labwc lo espone

`[M]` Il nostro cliente nudo, **senza alcun permesso**, ha visto e usato:

```
global: output_manager v4 · screencopy v3
```

`[R]` labwc lo crea in `reference-xfce/labwc/src/server.c` e non lo filtra per i client del
socket normale (`server.c:344`, `return true` senza security context — già in `STUDI.md` §xfce §3).
⚠ **Nota di sicurezza che non era nel mandato**: un client qualunque della sessione può
ridimensionare il desktop — e, come si vede al §4, **ucciderlo**.

### La catena, dal protocollo al pixel

| passo | file:riga | che cosa controlla |
|---|---|---|
| il client chiede | `wlroots/types/wlr_output_management_v1.c:216-236` | **solo** `width > 0 && height > 0 && refresh >= 0`; altrimenti errore `invalid_custom_mode` `[R]` |
| labwc verifica | `labwc/src/output.c:689-745` (`verify_output_config_v1`) | ⭐ **niente sulla misura**: solo due casi del backend `wl` (nested) `[R]` |
| labwc prova | `labwc/src/output.c:294-323` (`output_test_auto`) | ⭐ **col client, prova SOLO la misura chiesta e restituisce l'esito** — riga **322**, `return wlr_output_test_state(...)`. **Nessun ripiego, nessuna sostituzione** `[R]` |
| labwc applica | `labwc/src/output.c:589-686` (`output_config_apply`) | riga **604-612**: `set_custom_mode` con i numeri del client, tali e quali `[R]` |
| il backend accetta | `wlroots/backend/headless/output.c:34-54` | ⛔ **nessun controllo di misura**: solo la maschera dei campi `[R]` |
| l'esito torna | `labwc/src/output.c:761-785` | `succeeded` **solo** se verifica e commit sono andati; altrimenti **`failed`** `[R]` |

⭐ Il ripiego pericoloso di `output_test_auto` (righe **325-370**: prova la modalità preferita,
poi tutte le altre, **sostituendole nello stato** alla riga **345** e **363**) **non ci
riguarda**: scatta solo con `is_client_request == false`, cioè alla creazione dell'output — e
su un headless l'elenco delle modalità è vuoto, quindi il ciclo non gira. `[R]`

---

## 2. La cattura: la misura del buffer la decide il compositore, e non si tratta

`[S]` `wlr-screencopy-unstable-v1.xml:106-116` — l'evento `buffer` (`format`, `width`,
`height`, `stride`) va **dal compositore al client**. Il client non ha nessuna richiesta per
proporre una misura. `[S]` righe **118-129**: *«The buffer must have the correct size»*.

`[M]` **E «correct» vuol dire esatta**: un buffer largo **un solo pixel in più** del dovuto
non viene adattato, **uccide il client**:

```
zwlr_screencopy_frame_v1#9: error 1: invalid buffer dimensions
⛔ CLIENT UCCISO: interfaccia=zwlr_screencopy_frame_v1 codice=1
```

`[R]` `wlroots/types/wlr_screencopy_v1.c:383-388` — il confronto è `!=`, non `<`: **anche un
buffer più grande è rifiutato**. E per `wl_shm` lo stride dev'essere **esattamente**
`width×4`, riga **423-428**, `!=` di nuovo — ⚠ mentre il `wl_shm` generico di wlroots
accetterebbe uno stride paddato (`types/wlr_shm.c:317-318`). **screencopy è più severo di
wl_shm**: un buffer legale altrove qui è fatale.

`[M]` Misurato su cinque misure diverse, lo stride annunciato è **sempre** `larghezza × 4`,
anche con larghezza dispari: `2133 → 8532`, `1919 → 7676`, `3 → 12`, `1 → 4`.
`[R]` È `pixel_format_info_min_stride`, `wlroots/render/pixel_format.c:239-247`, e per
`XRGB8888` non arrotonda niente. Il `// TODO: align?` in
`wlroots/render/allocator/shm.c:75` è la prova che **oggi non si allinea nulla**. `[R]`

**`ext-image-copy-capture-v1`**: `[✗]` **non esiste** né in wlroots 0.18.2 né in labwc 0.8.3
(`grep -rn "ext_image_copy_capture" wlroots/ labwc/` → zero; controllo positivo: `grep -rn
"screencopy" labwc/` → 3 righe, `labwc/src/server.c:18`, `:215`, `:643`). Esiste la sola
**specifica**, in `wayland-protocols/staging/`. `[S]` Quando arriverà cambia una cosa a
nostro favore: la misura sbagliata diventa un `failed(buffer_constraints)` **recuperabile**
invece di una disconnessione (XML righe **343-360**).

⚠ **Una trappola da evitare**: `capture_output_region` **non ritaglia**, malgrado la specifica
lo prometta (`[S]` XML righe 65-66). `[R]` `wlr_screencopy_v1.c:580-599` non ha nessun clamp;
il controllo arriva solo al commit (righe **309-313**) e allora **fallisce**. E sulla scala non
intera tronca in silenzio (righe **592-595**: `int *= float`). ⇒ **usare `capture_output`**,
e ritagliare noi.

---

## 3. I limiti: minimo, massimo, parità

| domanda | risposta | prova |
|---|---|---|
| **minimo** | **1×1** — accettato, catturato, copiato | `[M]` |
| **larghezza pari?** | ⭐ **NO, labwc non lo chiede**: `2133×772`, `2133×773`, `1919×1079`, `3×5` tutte esatte | `[M]` |
| **multipla di 8/16?** | ⭐ **NO** | `[M]` |
| **stride allineato?** | **NO**: sempre `larghezza×4` esatto | `[M]` `[R]` |
| **massimo dichiarato** | ⛔ **nessuno, in nessun punto** | `[✗]` `grep "& ~1\|ALIGN\|roundup\|MAX_WIDTH"` a zero su `wlr_screencopy_v1.c` e sul percorso di commit |
| **massimo reale** | ⛔ **c'è, e non è dichiarato**: `32768×16384` (2 GiB) passa, **`32768×32768` (4 GiB) uccide** | `[M]` |

⛔⛔ **Il massimo non dichiarato è la scoperta di questo studio.** Ripetuto due volte:

```
== CHIEDO 32768x32768 ==
  ⛔ ERRORE di connessione errno=32     ← EPIPE: il compositore non c'è più
labwc: MORTO DA SEGNALE 11 (SEGV)
ultime righe del log (-V):  …[../src/output.c:385] mode test failed for output HEADLESS-1
```

`[M]` **Nessuna riga sulla morte, nemmeno a `-V`.** `32768×32768×4 = 4 294 967 296` byte,
cioè **esattamente 2³²** `[?]`: è il sospetto di un troncamento a 32 bit nel calcolo della
dimensione, non l'OOM-killer (`journalctl -k` non riporta nulla, e la macchina aveva 4,5 GB
liberi). ⚠ La causa precisa **non è stata isolata**; il fatto sì.

⭐ **Che cosa ne consegue per noi**: la misura che chiediamo va **limitata dal nostro codice**,
perché nessun altro la limita. Un client remoto che dichiara una finestra assurda non deve
poter arrivare a `set_custom_mode`. Per il nostro uso (≤ 4K) il tetto è lontanissimo — ma il
tetto va messo **da noi**, non sperato.

---

## 4. ⛔ Errore o arrotondamento silenzioso? — La domanda più pericolosa

**Nessun arrotondamento. Mai. Da nessuna parte del percorso.** Le misure lo confermano su
undici valori diversi, dispari e primi compresi: quel che si chiede è quel che si ottiene,
al pixel. `[M]`

Le misure **non ammesse** danno un **errore esplicito**, non un adattamento:

| chiesto | esito misurato |
|---|---|
| `0×0` | ⛔ errore di protocollo `zwlr_output_configuration_head_v1` codice **3** (`invalid_custom_mode`) `[M]` |
| `0×100` | ⛔ stesso errore `[M]` |
| `2133×-772` | ⛔ stesso errore `[M]` |
| `32768×32768` | ⛔⛔ **SIGSEGV del compositore** `[M]` |

⭐ **Ma il silenzio esiste lo stesso, in due forme, e sono tutte e due trappole vere:**

### 4a. Il «riuscito» che non fa niente

`[M]` Chiedere la misura **che l'output ha già** dà `succeeded ✅` — e **nessun evento
`wl_output.mode` arriva**, perché non c'è stato alcun modeset.
`[R]` `wlroots/types/output/output.c:513-521`: `output_compare_state` **toglie il campo
`MODE`** quando i tre numeri coincidono. ⛔ **Un client che aspettasse l'evento `mode` come
conferma del ridimensionamento aspetterebbe per sempre.** È lo stesso inciampo che labwc
aggira alzando la larghezza di 1 (`labwc/src/output.c:1084-1104`, con tanto di rimando
all'issue wlroots 3946).

### 4b. Il «cancelled» che nessuno guarda

`[M]` Una configurazione creata con un **serial vecchio** riceve `cancelled ⚠` e **non
succede niente**, in silenzio. `[R]` `wlroots/types/wlr_output_management_v1.c:447-456`: ogni
cambio di stato degli output alza il serial, e una richiesta con il serial precedente viene
annullata.

⛔ **E qui c'è il precedente che ci riguarda**: wayvnc tratta `succeeded`, `failed` e
`cancelled` **nello stesso ramo**, con un solo `nvnc_trace` (invisibile in esercizio) e
nessun ritentativo — `[R]` `reference-xfce/wayvnc/src/output-management.c:131-156`. ⇒ **su
wayvnc un ridimensionamento può essere perso senza che nessuno lo sappia.**

⇒ **La regola per noi**: non fidarsi né dell'esito né dell'assenza di errori. **Rileggere
la misura**, e la fonte giusta è **l'evento `buffer` di screencopy**, che è quella su cui
poi si allocherà davvero.

---

## 5. Il cambio a caldo: quanto costa

`[M]` Cattura continua a ~60 fotogrammi al secondo, cambio da `1280×720` a `2133×772` al
decimo fotogramma:

```
 9    1280x720     17.2 ms  ok
>>> CAMBIO a 2133x772 : succeeded  (5.1 ms per la risposta del compositore)
10   2133x772     36.4 ms  ok      ← già alla misura nuova
11   2133x772     14.0 ms  ok
…
fotogrammi falliti: 0 su 25
```

| | |
|---|---|
| **risposta del compositore** | **5,1 ms** |
| **fotogrammi persi** | ⭐ **zero** |
| **fotogramma nero** | ⭐ **nessuno** |
| **costo sul primo fotogramma nuovo** | **+20 ms** (36,4 contro ~16), cioè **un periodo** |
| **il fotogramma subito dopo il cambio** | è **già** alla misura nuova, e valido |
| **input perso** | `[?]` **non misurato** — vedi «quel che questo rapporto non dice» |

⚠ **Ma è la misura del caso pulito**: un solo client, nessuna finestra aperta, e il nostro
cliente **richiede** un fotogramma alla volta invece di inseguire una cadenza. Con
applicazioni vive e finestre da riposizionare il costo sarà maggiore. `[?]`

⚠ E resta il vincolo già noto: `[R]` `wlroots/backend/headless/output.c:10-14`,
`ADAPTIVE_SYNC_ENABLED` è **fuori** dalla maschera dei campi ammessi, e
`wlr_output_head_v1_state_apply` (`wlr_output_management_v1.c:1028`) lo mette **sempre** nello
stato. Se il valore differisce da quello corrente, **l'intero commit fallisce** — un rifiuto
che sembra un rifiuto della misura. `[M]` Nel nostro banco non è mai scattato perché il valore
coincideva (`head.adaptive_sync 0`, e il log dice «adaptive sync disabled» a ogni cambio).

---

## 6. ⭐ Che cosa fa `wayvnc` con `SetDesktopSize`

**Lo attua.** La strada c'è ed è già scritta da qualcuno — ma è scritta **peggio di come la
scriveremmo noi**, e i suoi tre difetti sono tre cose da non copiare.

| passo | file:riga | |
|---|---|---|
| neatvnc riceve il messaggio | `reference-xfce/neatvnc/src/server.c:1876-1877` | tipo **251** `[R]` |
| e chiama la callback di wayvnc | `neatvnc/src/server.c:1654-1686` | `[R]` |
| wayvnc la implementa | `reference-xfce/wayvnc/src/main.c:802-826` (`on_client_resize`) | **ridimensiona davvero l'output Wayland**, non riscala `[R]` |
| e costruisce la configurazione | `wayvnc/src/output-management.c:230-287` | `set_custom_mode(w, h, 0)` alla riga **270-271** `[R]` |

⭐ **Il precedente conferma la nostra strada**: chi fa il nostro mestiere su wlroots
**ridimensiona l'output**, non converte le coordinate.

⛔ **I tre difetti da non copiare:**

1. **wayvnc non verifica mai di aver ottenuto la misura chiesta.** `[R]`
   `output-management.c:286`: `return true` **subito dopo `apply()`**, prima che il
   compositore abbia risposto. `[✗]` E non conserva nemmeno la misura chiesta
   (`grep "requested_width\|pending_width"` → zero), quindi il confronto è
   **strutturalmente impossibile**. ⇒ Se il compositore arrotondasse, **wayvnc non se ne
   accorgerebbe**.
2. **I tre esiti finiscono nello stesso ramo** (§4b): un `cancelled` è indistinguibile da un
   `succeeded`. `[R]` `output-management.c:131-156`.
3. **Il client VNC non riceve mai `SUCCESS`**, ma il codice **4 = «inoltrata»** — che non è
   nemmeno nella specifica RFB. `[R]` `neatvnc/src/server.c:1587`, `:1621`. La verità sulla
   misura vera arriva al client **di rimbalzo**, quando il primo fotogramma nuovo fa emettere
   a neatvnc un secondo rect `ExtendedDesktopSize` con le dimensioni **reali**
   (`neatvnc/src/server.c:2411-2432`). ⭐ **Questa parte invece è da copiare**: la verità la
   dice il fotogramma, non l'esito della richiesta. È esattamente la regola del §4.

**Quando wayvnc rifiuta**, e il perché vale quanto la risposta:

| condizione | file:riga |
|---|---|
| `--disable-resizing` (⚠ **solo da riga di comando**, `[✗]` nessuna chiave di configurazione) | `wayvnc/src/main.c:1927-1928`, `:1984-1985` |
| nessun output selezionato | `wayvnc/src/main.c:812-813` |
| **un altro client è già «padrone del layout»** — il secondo che chiede è rifiutato | `wayvnc/src/main.c:815-816`, `:1313-1314` |
| l'output non è «headless» | `wayvnc/src/output-management.c:239-244` |

⭐ E **come decide se un output è ridimensionabile** è la riga più istruttiva di tutte:

```c
self->is_headless =
    (strncmp(name, "HEADLESS-", strlen("HEADLESS-")) == 0) ||
    (strncmp(name, "NOOP-", strlen("NOOP-")) == 0);
```
`[R]` `wayvnc/src/output.c:220-229` — **è solo il prefisso del nome**. Nessuna interrogazione
di capacità. `[M]` Il nostro output si chiama infatti `HEADLESS-1`.

`[✗]` **E non c'è nessun ripiego di riscalatura**: `grep "pixman_f_transform\|crop"` su
wayvnc → zero. Se wayvnc rifiuta, il client VNC si tiene la risoluzione nativa e si arrangia.
⇒ **Nessuno, su wlroots, riscala lato server. Tutti ridimensionano l'output.**

---

## ⭐ La cosa che il mandato non chiedeva, e che decide la questione di prodotto

La domanda era su labwc. **Ma su `2133` non è labwc a dire di no: siamo noi.**

```c
/* ⚠ 4:2:0 vuole misure pari: una larghezza dispari darebbe un croma di
 *   mezzo campione, e il codificatore lo arrotonderebbe **in silenzio**. */
if ((richiesta->larghezza & 1) || (richiesta->altezza & 1)) {
        di(errore, errore_byte, "%ux%u: 4:2:0 vuole misure pari", ...);
```
`[R]` `src/codificatore.c:1370-1376`, e lo stesso controllo nel ridimensionamento a caldo,
`src/codificatore.c:1510-1514`.

⭐ **Il commento del nostro codice dice esattamente quel che il mandato temeva** — «lo
arrotonderebbe **in silenzio**» — e ci siamo già difesi. Il punto è che **la difesa è a valle**:
labwc darebbe volentieri `2133`, e sarebbe il codificatore a rifiutarlo.

⇒ **La regola end-to-end**: la misura chiesta al compositore va **portata al pari** prima di
chiederla, non dopo. Costa **al massimo un pixel per asse** — non è una scala, non è una banda
nera, ma è una conversione che **non sparisce del tutto** e va scritta in `DECISIONI.md`.

⭐ **E qui i due studi di oggi combaciano.** `F4-IN-11-codificatore-misura.md`, misurato in
parallelo sul banco `192.168.0.2`, arriva alla stessa riga da valle: *«il vincolo non è
"multipla di 16" e nemmeno "multipla di 8": è **pari**, e basta»*, e `[M]` ffmpeg nudo
**arrotonda `2133 → 2134` in silenzio, con `exit=0` e nessun avviso** — cioè esattamente il
difetto che il commento di `src/codificatore.c:1370` prevedeva e da cui il nostro controllo ci
difende. ⇒ **La domanda «2132 o 2134?» è già decisa da quel rapporto: si tronca in basso**,
`2133 → 2132`, invece di lasciar arrotondare il codificatore in alto.

⇒ ⭐ **Le due metà si incastrano: labwc dà qualunque misura pari al pixel esatto (questo
rapporto, `[M]`), e qualunque misura pari attraversa il codificatore intatta (`F4-IN-11`,
`[M]`). Il disegno dell'utente — scala 1, nessuna banda nera — REGGE, al prezzo di un pixel
per asse.**

---

## 7. ⭐⭐ XFCE e LXQt NON sono lo stesso caso

Il mandato chiedeva di dirlo esplicitamente se la risposta differisse. **Differisce.**

Il compositore è lo stesso, la risposta **sulla misura** è la stessa. Ma la domanda vera è
un'altra: **esiste, nella sessione, un secondo client che parla `wlr-output-management` e può
disfare quel che facciamo?**

| | XFCE | LXQt |
|---|---|---|
| **secondo comandante** | ⛔ **SÌ — `xfsettingsd`** | ✅ **NO** |
| prova | `[R]` `reference-xfce/xfce4-settings/xfsettingsd/displays-wayland.c:309-318`: `create_configuration` + `apply` | `[✗]` `grep -rn "zwlr_output_manager\|wlr-output" reference-lxqt/lxqt-config lxqt-session lxqt-wayland-session` → **0 righe** sui modi (l'unica riga è un commento su `wlr-output-**power**-management`). Controllo positivo: `grep -rn "KScreen" reference-lxqt/lxqt-config` → **181 righe** |
| quando parte | ⛔ **è il primo client della sessione**: `[R]` `reference-xfce/xfce4-session/settings/xfce4-session.xml:41-48`, blocco `FailsafeWayland`, `Client0_Command = xfsettingsd`, priorità 15 | — |
| che cosa manda | ⛔ una **riscrittura globale**, non differenziale: per **ogni** output `enable_head`+`set_mode`+`set_position`+`set_transform`+`set_scale`, oppure `disable_head` — `[R]` `displays-wayland.c:287-305` | — |

⛔⛔ **Il pericolo su XFCE non è la risoluzione: è lo spegnimento.**

`[R]` `reference-xfce/xfce4-settings/xfsettingsd/displays-wayland.c:509-540`: per ogni output
marcato `new`, se ci sono già altri output, **`output->enabled = FALSE`** (righe **526-529**),
poi `apply_all()` (**550-551**). E `[R]` `xfce4-settings/common/display-profiles.h:29-30,43`:
la condizione è `action <= SHOW_DIALOG`, dove `SHOW_DIALOG` vale **1 ed è il default** e
`DO_NOTHING` vale **0** — ⭐ **quindi anche «non fare nulla» spegne l'output nuovo**.
In più, riga **543-547**, gli apre in faccia `xfce4-display-settings`.

⭐ **Il nostro output virtuale È un output nuovo.** È esattamente il bersaglio.

⚠ E c'è un anello di reazione: `[R]` `displays-wayland.c:580-586` — quando **la nostra**
`apply` invalida il serial di una configurazione pendente di xfsettingsd, lui riceve
`cancelled`, mette `config_cancelled = TRUE`, e alla riga **446/460** quel flag **scavalca la
guardia** che eviterebbe la riapplicazione ⇒ **riapplica**. E la riga **543** è **fuori** dal
ciclo degli output nuovi: **basta un `cancelled` perché il dialogo si apra da solo.**

✅ **Ma la misura sopravvive**, e questo va detto perché ridimensiona la paura:
`[R]` `wlroots/types/wlr_output_management_v1.c:208-213` — `set_mode` azzera il `custom_mode`
**solo se il modo non è NULL**; e `[R]` `:353-378` + `:156-160` — `enable_head` ricopia lo
stato dell'output, quindi i nostri `2132×772` restano. `[✗]` xfsettingsd non usa mai
`set_custom_mode`. ⇒ **Su XFCE il rischio è `enabled = FALSE`, la scala e la posizione — non
la misura.**

✅ **Su LXQt niente di tutto questo**: `lxqt-config-monitor` passa da **KScreen**, che su labwc
non trova backend e **muore con `exit(1)`** (`[R]`
`reference-lxqt/lxqt-config/lxqt-config-monitor/monitorsettingsdialog.cpp:49-69`), ed è una
**voce di menu, non un autostart**. E ⭐ l'osservatore udev che rilancerebbe
`lxqt-config-monitor -l` a ogni cambio di display è **racchiuso in `if (isX11)`** — `[R]`
`reference-lxqt/lxqt-session/lxqt-session/src/sessionapplication.cpp:88-125`.
⚠ **Questo precisa `STUDI.md` §lxqt riga 146**: il «secondo comandante della risoluzione» lì
descritto esiste **solo nello scenario di ripiego a `xcb`**, che `STUDI.md` §lxqt §3.2 già impone di
evitare. Nella sessione Wayland fatta bene **non esiste**.

⚠ Un solo residuo su LXQt, innocuo: `[R]`
`reference-lxqt/lxqt-config/lxqt-config-monitor/monitorsettingsdialog.cpp:222-228` — il tasto
*Salva* scrive un autostart `lxqt-config-monitor -l` **senza** `X-LXQt-X11-Only`. Un utente che
l'abbia salvato ai tempi di X11 se lo ritrova eseguito — ma senza backend KScreen non emette
alcun comando, e comunque **non parla `wlr-output-management`**.

### E una differenza di pacchettizzazione, misurata

`[M]` (CHUWI, 14 agosto 2026): `apt-cache rdepends labwc` → **`Reverse Depends:` vuoto**.
Né `xfce4-session` né `lxqt-session` tirano dentro labwc: è **una scelta manuale nostra** in
tutti e due i casi. `ls /usr/share/wayland-sessions/` → `labwc.desktop` c'è; `[✗]`
`apt-cache policy lxqt-wayland-session` → **uscita vuota** (controllo positivo: `lxqt-panel`
→ `2.1.4-1`). ⇒ **XFCE-Wayland ha una sessione pacchettizzata, LXQt-su-labwc va composta a
mano.** Conferma `STUDI.md` §lxqt §1.

---

## Quel che questo rapporto NON dice

| | |
|---|---|
| ⛔ **Non dice che labwc regga una sessione vera.** Tutto è misurato su un labwc **vuoto**, senza `xfce4-session` né `lxqt-session`, senza pannelli e senza una sola finestra. Il cambio di misura a caldo con applicazioni vive **non è stato misurato** |
| ⛔ **Non dice dove sia esattamente il tetto.** Si sa che `32768×16384` passa e `32768×32768` uccide `[M]`. La soglia esatta e la causa (`[?]` troncamento a 2³²) **non sono state isolate** |
| ⛔ **Non dice niente sull'input durante il cambio.** La domanda 5 chiedeva anche «input perso?»: il banco cattura, non inietta. **Non misurato** |
| ⛔ **Non dice niente sulla scala.** Tutte le misure sono a `scale = 1.0` `[M]`. Che cosa succede alla misura catturata se un client imposta una scala frazionaria **non è stato provato** — e `wlr_output_head_v1_state_apply` la applica **sempre** (`wlr_output_management_v1.c:1026`) `[R]` |
| ⛔ **Non dice niente su DMA-BUF.** Tutte le copie sono `wl_shm` `[M]`. Sul ramo DMA-BUF lo stride lo sceglie il driver GBM (`wlroots/render/allocator/gbm.c:78`) `[R]` e **non è mai confrontato** da screencopy `[R]` — regole opposte a shm, e **lì si annida il prossimo difetto** |
| ⛔ **Non dice niente sui monitor multipli.** Un solo output, `HEADLESS-1` |
| ⛔ **Non dice che `xfsettingsd` ci spenga davvero l'output.** Il §7 è tutto `[R]`: `[M]` `apt-cache policy xfce4-settings lxqt-config` → **`Installed: (none)`** su questa macchina, né XFCE né LXQt sono installati. **È la misura più urgente che questo studio lascia aperta** |
| ⛔ **Non dice se la finestra tattica esista.** `[R]` `displays-wayland.c:448-454` e `:521-524`: al **primo** `done` xfsettingsd registra soltanto, e con `previous_n_outputs == 0` **abilita** invece di spegnere. ⇒ `[?]` un output virtuale **già presente prima** che xfsettingsd faccia il bind forse non è «nuovo». **Da misurare** — se regge, la cura è l'ordine di avvio |
| ⚠ **Non è la macchina di produzione.** `CHUWI`, Intel ADL-N, Mesa 25.0.7. Su `192.168.0.2` gira GNOME e labwc **non è stato provato lì** |
| ⚠ **`ext-image-copy-capture-v1` è letto solo come specifica** `[S]`: nessuna implementazione esiste su Trixie da cui misurarlo |
