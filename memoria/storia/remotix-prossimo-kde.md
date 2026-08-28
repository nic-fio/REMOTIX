---
name: remotix-prossimo-kde
description: "REMOTIX fase 11: KDE CHIUSO e documentato l'8 agosto 2026. Il prossimo desktop e' XFCE (famiglia wlroots). Resta un difetto aperto nel percorso condiviso e due decisioni"
metadata:
  node_type: memory
  type: project
  originSessionId: 1aac11ab-166c-4641-9520-e34064b18f20
  modified: 2026-08-08T14:55:48.072Z
---

# Fase 11, KDE — CHIUSO. Il prossimo è XFCE

> **8 agosto 2026, decisione dell'utente**: *«nella prossima sessione occuparci del prossimo DE:
> XFCE. Però prima chiudere in modo ordinato la parte di KDE — documentazione e codice»*. Fatto:
> `PIANO.md` fase 11 riscritta (KDE chiuso, XFCE aperto), `kde.md` §14-bis di chiusura, `LEZIONI.md`
> §3 con **due righe corrette e due domande nuove** (la 13 «uno schermo virtuale si ridimensiona?» e
> la 14 «la clipboard di chi è?»), i due banchi che ora dichiarano davvero i propri guasti.
>
> ⭐ **Per XFCE, tre cose che valgono più di tutte**: `appunti_wlr.c` **è già scritto** per quella
> famiglia (il protocollo è di wlroots); wlroots **fa tirare** i fotogrammi invece di spingerli, ed è
> l'unica differenza che cambia la *forma* del codice; e il passo zero resta *«chi, al mondo, fa
> questa cosa su questo desktop?»* — per wlroots la risposta è **wayvnc** e
> `xdg-desktop-portal-wlr`.

*Compito posto dall'utente il 7 agosto 2026 («prossimo DE KDE»), e la sera stessa: **«prima leggi la
documentazione, poi studia a fondo la codebase di KDE con 10 subagenti e produci `kde.md`»**. Fatto.*

## Lo studio esiste: `kde.md`, e va letto per intero

**`~/Documenti/REMOTIX/kde.md`** (1295 righe) è il quinto studio del progetto, nella forma di
`gnome-remote-desktop.md`. Gli otto repository di KDE sono clonati alla versione di Trixie —
**6.3.6** — in `~/Documenti/REMOTIX/reference-kde/`, con i dieci rapporti dei subagenti in
`reference-kde/rapporti/` (9500 righe: il dettaglio con `file:riga` che `kde.md` riassume).
`reference-kde/banco/` ha le copie dei nostri programmi di banco riprese dal server.

Fa parte della documentazione da leggere prima di scrivere ([[remotix-metodo-documentazione]]), ed è
citato in `SPECIFICA.md`, `PIANO.md` e `REFERENCE.md`.

## Le quattro domande hanno risposta — e la sera del 7 agosto sono state **misurate**

| | |
|---|---|
| **Permesso della cattura** | un file `.desktop` con `X-KDE-Wayland-Interfaces` (`NoDisplay=true` va bene): **nessun dialogo, mai**. ✅ **misurato**. ⛔ **Ma serve anche `XDG_MENU_PREFIX=plasma-` nell'ambiente**, o l'indice dei servizi di KDE si costruisce **vuoto** e KWin dice «Could not find the desktop file». In sessione Plasma la mette `startplasma` (`startplasma.cpp:366`); in un ambiente composto da noi **va messa a mano**. Non girare come root, `Exec=` deve nominare il binario vero |
| **Input** | **libei**: `connectToEIS` su D-Bus a KWin, **senza alcun controllo**. ✅ **misurato**: `(handle 0, 1)` da una shell SSH. `input.c` si riusa quasi per intero |
| **Sessione senza monitor** | due variabili obbligatorie **+ `XDG_MENU_PREFIX`**, unità del compositore sovrascritta. `--xwayland` **obbligatorio** (ksmserver) |
| **GPU senza monitor** | ✅ **GPU, misurato**: la stringa del renderer via D-Bus lo dice per nome. **R32 corretta**: la nostra «in software» era sbagliata, perché `kwin_wayland` è **non dumpable** (xattr `security.capability`) e il `/proc` va letto con `sudo`. ⚠ E «render node aperto» **non prova la GPU**: è aperto anche in QPainter |

⛔ **E `--drm` non è praticabile**: da una sessione senza seat esce con stato 1 (`Failed to activate …
session`), e non per permessi Unix. Quindi **`--virtual`**, col suo prezzo (§8.1) — e **una delle tre
scelte da porre all'utente l'ha chiusa la misura, non l'utente**. Ne restano due: ridimensionamento e
BlocMaiusc/BlocNum.

**Stato: tutte e 12 le misure chiuse fra il 7 e l'8 agosto 2026**, più una tredicesima trovata strada
facendo. Script in `reference-kde/banco/` — `permesso*-kde.sh`, `misure2..6-kde.sh`,
`plasma..plasma6-kde.sh` — anche sul server.

✅ **La catena intera è stata vista funzionare**: `startplasma-wayland` → plasmashell in **1 secondo**
→ cattura autorizzata dal solo `.desktop` → **flusso PipeWire** → logout ordinato che **non porta via
il bus d'utente**.

## ⭐ La GPU: decisione dell'utente, e la trappola attaccata

**«Non usare la Radeon, usa la Intel integrata»** (8 agosto 2026). Il server ha **Intel UHD 770
(i915) = `renderD128`** e **Radeon RX 6800 (amdgpu) = `renderD129`**; KWin `--virtual` prende **la
prima che si apre** (`findRenderDevice()`: nessuna variabile, `KWIN_DRM_DEVICES` vale solo per `--drm`).

| Come negare la Radeon | GPU | Cancello della cattura |
|---|---|---|
| `InaccessiblePaths=` nell'unità | Intel ✅ | ⛔ **CHIUSO** (0 righe `KWIN_UTILS` contro 13) |
| `DeviceAllow=`/`DevicePolicy=closed` | ⛔ nessun effetto: in un'unità **d'utente** i device non sono delegati | aperto |
| ✅ **permessi del nodo** (fuori dal gruppo `render`) | **Intel** ✅ | ✅ **aperto**, flusso ottenuto |

⛔ **Da cui: mai irrigidire l'unità del compositore con opzioni che implicano un mount namespace.** Per
il prodotto la GPU si esclude con una **regola udev per id PCI**
(`/dev/dri/by-path/pci-0000:03:00.0-render`), non col numero del nodo, che non è stabile.

## ⭐ La copia zero è la condizione del requisito, non un'ottimizzazione

Misurato sulla **Intel**, scena dichiarata e in movimento: **59 fps da 720p a 4K a copia zero**; in
memoria **43,3** a 1080p e **27,0** a 4K. I 60 a 4K che l'utente chiede
([[remotix-requisito-prestazione]]) si ottengono **solo** con la copia zero: il collo di bottiglia è
**la copia**, non il compositore né la GPU.

E su KWin **la cattura consegna fotogrammi interi**, quindi il difetto che tiene spenta la copia zero
su GNOME non si ripresenta ([[remotix-fase9-ripresa]]) — ma ⚠ **la sincronizzazione va aspettata**: il
100 % dei buffer DMA-BUF arriva col disegno in corso, perché KWin fa `glFlush` e **non** `glFinish`
(che fa solo su NVidia e llvmpipe). «Si sincronizza da sé» va inteso come «sottomette», non «attende».

## Le altre risposte, in breve

- ⛔ **`KWIN_COMPOSE=O2` non protegge**: con i render node inaccessibili KWin ripiega in QPainter **e
  parte**. `LIBGL_ALWAYS_SOFTWARE` e le altre variabili di Mesa **non hanno effetto** su KWin. L'unica
  prova valida: `gdbus … org.kde.KWin.supportInformation | grep 'renderer string'`.
- ⚠ `ksmserver` e `Xwayland` **non sono partiti** e la sessione ha funzionato: il vincolo
  «`--xwayland` obbligatorio per ksmserver» **non si è manifestato** — ma non toglierlo senza aver
  verificato il logout ordinato.
- ✅ la cattura è **indipendente dal VT**; KWin **non cade** su misure assurde (0×0, 99999²…); la
  rotella **non è invertita** da KWin e i due assi sono trattati con la stessa formula.
- ⚠ plasmashell, al primo fallimento di OpenGL, scrive **`SceneGraphBackend=software` in modo
  persistente** in `kdeglobals` e si riavvia da sé: il dialogo modale è solo il secondo giro. Una
  sessione avviata senza GPU **lascia un segno nella casa dell'utente**.
- ⏱ montare un flusso costa **65–67 ms**; la prima sessione Plasma crea **23 file** in `~/.config`.

## ⭐ Il riferimento è `KRdp`, e il primo giro di studio l'aveva mancato

Esiste **un `gnome-remote-desktop` per KDE**: `plasma/krdp`, C++ su FreeRDP + kpipewire, 4 222 righe.
Il suo `.desktop` dichiara `X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1`
— cioè **la via del permesso non è una nostra deduzione**. Conferma anche i due codec, il regolatore
dall'RTT, i bordi esclusivi delle regioni e TLS-con-PAM. Non risolve invece: **non avvia la sessione**
(vive dentro Plasma) e sul percorso diretto **non ha appunti** (funzione vuota).

⚠ Trixie ha **krdp 6.3.5**. I rapporti 11-16 in `reference-kde/rapporti/` hanno il dettaglio, compresi
**i difetti corretti fra la 6.3.6 e il ramo di sviluppo**, che sono difetti che noi non dobbiamo fare.

**Il primo giro di studio l'aveva mancato** perché ha cercato dentro gli otto repository scelti da me:
la lezione è il passo **zero** aggiunto a `LEZIONI.md` §9 — *«chi, al mondo, fa questa cosa su questo
desktop?»*, e si chiede prima di leggere.

## ✅ Il ridimensionamento: risolto upstream, arriva in KWin 6.8

Su 6.3.6 un output virtuale non si ridimensiona. Ma `kwin!7932` («Resizable Virtual Monitors») è
**unita il 29 luglio 2026**, milestone **6.8**, e il meccanismo scelto è **la negoziazione PipeWire**
(`SPA_POD_CHOICE_RANGE_Rectangle`) — cioè **il codice della nostra fase 6**. Una richiesta `resize`
nel protocollo era stata proposta e **respinta** proprio per quel motivo.

⛔ **Da cui la regola per chi scrive**: il ridimensionamento su KDE si scrive **nella forma della
negoziazione**, che diventa giusta da sé; «chiudi e rifai lo stream» è il ripiego per le versioni che
non ce l'hanno, non la strada principale.

## ✅ Le tre decisioni, prese dall'utente l'8 agosto 2026

| | |
|---|---|
| **Copia zero** | **adesso, dentro KDE**: la cattura **nasce a copia zero** (con l'attesa della fence), non si scrive due volte |
| **Ridimensionamento** | **misura fissa alla connessione** su Trixie, ma **scritta nella forma della negoziazione PipeWire**, così su KWin 6.8 si accende da sé |
| **BlocMaiusc/BlocNum** | **si legge lo stato vero** con `org_kde_kwin_keystate` — costa poco perché su KDE la connessione Wayland c'è già per la cattura: un nome in più nel `.desktop` |

## ✅ LA VOCE 1 È FATTA — 8 agosto 2026: si vede il desktop di KDE

**`prove/fase11.sh` passa tutti i controlli**, in due modi (`fase11.sh` funzionale,
`INTEL=1 fase11.sh misura` per il ritmo), e lascia la macchina pulita.

| | 1920×1080 | 3840×2160 |
|---|---|---|
| **cattura, catena vera, Intel UHD 770** | **58,1** | **58,4** |
| il solo misuratore, 7-8 agosto | 59,2 | 59,0 |

Cioè **il numero del banco regge fuori dal banco**; il mezzo fotogramma che manca è la conversione
sulla scheda. ⚠ Il numero **al client** è un'altra cosa (24 a 4K): il tappo è `xfreerdp3` che
decodifica in software, come già in R32.

**Che cosa è nuovo**: `src/kwin.c` (client Wayland: registry, `stream_output`, pompa di eventi che
tiene viva la connessione), `src/compositore.c` (la porta unica: il palco non nomina più Mutter),
`src/protocolli/` (l'XML alla **v5**), le opzioni `--compositore` e `--installa-desktop`,
`prove/fase11.sh`.

**Le quattro cose confermate sul campo**: il permesso funziona anche per noi (`.desktop` +
`XDG_MENU_PREFIX`); la fence si aspetta e basta (2400 buffer su 2400 col disegno in corso, **zero
attese scadute** con tetto 50 ms); il modificatore che si ottiene è **0x0 lineare**, chiedendolo per
primo; la misura la impone il compositore e **va adottata in due punti** — nel palco e nella tela
grafica.

## ✅ ANCHE LA VOCE 2 (INPUT) È SCRITTA E PROVATA — stessa giornata

⏳ **Ma non è chiusa**: il «fatto quando» dice *«giusti a occhio, su tre client»*, e nessuno l'ha
ancora guardato. Il banco dice:

```
OK  canale di input concesso da KWin (gettone 1)
OK  disposizione della sessione letta da libei: English (US)
OK  14 eventi di tastiera inoltrati al compositore
OK  regione del puntatore: 0,0 1920x1080 (mapping-id «assente»)
OK  la rotella arriva come SCATTI DISCRETI nei due versi
OK  lucchetti secondo KWin: BlocMaiusc spento, BlocNum spento
```

**Le quattro differenze, tutte scritte**: `connectToEIS` con
`g_dbus_connection_call_with_unix_fd_list_sync` (⛔ il tipo `h` porta un **indice**, non un fd: chi
legge il corpo prende uno zero, che è lo standard input); `ei_device_scroll_discrete(±120)`;
regioni per **geometria**; `org_kde_kwin_keystate` v5 con `fetchStates`.

⛔ **La conferma che vale di più è negativa**: `EI_EVENT_KEYBOARD_MODIFIERS` non è mai arrivato. Su
KDE la riconciliazione dei lucchetti scritta per GNOME **non girerebbe**, e senza `keystate` sarebbe
rimasta scritta e morta.

## ✅ E ANCHE LA VOCE 3 (SESSIONE E MACCHINA) — stessa giornata

`bash prove/fase11.sh sessione`: la macchina è come dopo un riavvio, il banco **si astiene**, e il
primo client che bussa trova un desktop.

```
OK  unita' del compositore sovrascritta: desktop 1280x720, senza schermo di blocco
OK  avvio la sessione grafica: exec startplasma-wayland
OK  il desktop e' venuto 1280x720: la misura la ha decisa il client che si e' collegato
OK  la sentinella dell'uscita e' passiva: sorveglia un nome, non si registra
OK  schermo della sessione tenuto acceso (inibizione 1)
OK  REMOTIX se n'e' accorto SUBITO / il logout non ha lasciato processi / e' sopravvissuto
```

⭐ **«Misura fissa alla connessione» è diventata LETTERALE**: `--virtual` vuole `--width/--height`
all'avvio, e ad avviare la sessione è REMOTIX quando il primo client si collega — quindi il desktop
*è* della misura chiesta. Lo scalare nel client serve solo a chi arriva dopo con un'altra misura.

⛔ **Il difetto che il codice letto non poteva mostrare**: powerdevil **non c'è ancora** quando il
palco si monta (parte tre anelli dopo il compositore), e l'errore era `ServiceUnknown` — «non esiste
ancora», non «mai». Ora `energia.c` aspetta su un thread suo.

⚠ **La regola udev per la GPU è scritta e NON installata**: `/media/REMOTIX/gpu-udev.sh` la mette e
la toglie (per id PCI: la Radeon è `0000:03:00.0`, la Intel `0000:00:02.0`). Negare un nodo coi
permessi lo nega **a tutta la sessione dell'utente**: è una modifica alla macchina con un prezzo, e
va messa quando l'utente lo decide.

## ⬅ DOVE RIPRENDERE

**Dalla voce 4: gli appunti.** `zwlr_data_control_manager_v1` v2, che su KWin **non è dietro alcun
permesso** (`kde.md` §9); attenzione all'eco su `setSelection` — il server cicla su *tutti* i data
control device compreso l'originatore — e al gate a tre condizioni del rapporto 11. E klipper
rimette l'ultimo elemento quando la clipboard si svuota.

**Il piano è in `PIANO.md` fase 11**: (1) cattura ✅; (2) input ✅; (3) sessione ✅; (5) giudizio ✅.

## ✅ VOCE 4 — GLI APPUNTI, scritti e verdi sul banco l'8 agosto 2026

`prove/fase11-appunti.sh`, **zero guasti**, e il giudizio dell'utente sui tre client: *«clipboard OK
su Linux, mstsc e Android»*. Averlo contava più del solito: la clipboard ha tre coinquilini
(klipper, la sponda Xwayland, il client) e il banco ne pilota due.

⭐ **CON QUESTO LA FASE 11 È CHIUSA PER KDE**: cinque voci su cinque, tutte con il giudizio.

## ✅ Il debito su GNOME è pagato — e il banco ha trovato un difetto nuovo

`prove/fase11-volume.sh mutter` (8 agosto 2026, **rifatta da macchina appena riavviata** su richiesta
dell'utente): il cursore governa **su tutti e due i compositori, con gli stessi numeri** —
25,8 / 0,40 / 0,00 su un tono di 25,9 %.

⚠ **Il ripristino del server ha DUE passi non scritti**, scoperti proprio con quel riavvio: il disco
`/media/REMOTIX` **non si monta da solo**, e `provision-server.sh` **non installa
`pulseaudio-utils`** (né `wl-clipboard`/`xclip`, né KDE) — i banchi ne dipendono. Vedi
[[remotix-lezioni]] §2.5-bis. La correzione stava nel percorso
condiviso e regge, come previsto ma ora **misurato**.

⛔ **RESTA APERTO**: «una via audio nuova parte al massimo» **non funziona**, né su KWin né su Mutter.
Chi zittisce, si scollega e si ricollega ritrova il silenzio. Il difetto è emerso solo **rinforzando
il controllo** (prima si zittiva a client collegato e il valore era già tornato su alla lettura:
[[remotix-lezioni]] §1.3). Quel che si sa: `pw_node_set_param` ritorna un numero di sequenza
asincrono (accettato, non un errore); campionando ogni mezzo secondo il valore **non si muove mai**,
quindi non è una corsa; e **`pw-cli set-param` sullo stesso nodo funziona** — il sospetto è il
**proxy**, preso da `pw_core_create_object` invece che legato dal registro. Dettaglio in
`REFERENCE.md` §7.5.

Sta in **`src/appunti_wlr.c`** — `wlr` e non `kwin` perché il protocollo è di wlroots, quindi il file
serve già i compositori di XFCE e LXQt. `appunti.h` è rimasta una porta sola: `appunti.c` smista, la
strada di Mutter è in `appunti_mutter.c`. Stessa forma di `compositore.c`.

Le due cose imparate scrivendolo:

- ⛔ **la guardia contro l'eco è di STATO, non di tempo**: si ignora un annuncio se la sorgente è
  **ancora nostra** e i tipi coincidono. Regge perché quando copia qualcun altro KWin manda
  `cancelled` *prima* dell'annuncio. Il criterio «la prima dopo la nostra» che `kde.md` proponeva è
  una regola a tempo, e le regole a tempo sbagliano quando due cose capitano insieme;
- ⛔ **`POLLHUP` vale come «pronto» in lettura**: chi possiede gli appunti scrive e chiude, e con dati
  corti la `poll` torna con solo `POLLHUP`. Guardando solo `POLLIN` il codice dichiarava una scadenza
  di 5 s **dopo 3 s** — il numero impossibile a registro è stato l'unico indizio.

## ✅ LA VOCE 5 È CHIUSA — 8 agosto 2026, tutti e tre i client

**xfreerdp ✅, RDM (Android) ✅, mstsc ✅** — *«mstsc OK!»*. La regola dei tre client è soddisfatta,
quindi le voci 1, 2 e 3 sono chiuse **dal giudizio** e non dal banco. Il giudizio, per esteso: **rotella ✅**, **terminale ✅**
(comprese le operazioni privilegiate), **audio ✅ e sincronizzato col video**, **video 1080p «alla
massima fluidità»**, **RDM (Android): «performance eccellenti»**.

I numeri letti in parallelo alla riproduzione: **57,8 fps consegnati**, codifica **1,7 ms** per
fotogramma, **conversione e caricamento a zero** — cioè la copia zero DMA-BUF che su Mutter non si
era ottenuta ([[remotix-fase9-ripresa]]). Il codificatore lavora al 10 % del tempo disponibile.

**I tre difetti li ha trovati lui, e sono chiusi lo stesso giorno:**

1. **doppio puntatore** — ⭐ la cura è **rendere trasparente il cursore di KDE**: un tema
   `XCURSOR_THEME` con un cursore 1×1 ad alfa zero (KWin lo guarda **solo se c'è anche
   `XCURSOR_SIZE`**), e il puntatore torna a essere quello del client, come su Mutter. Il primo
   tentativo — `SYSPTR_NULL` al client — funzionava su xfreerdp ma **non su RDM**, dove il secondo
   puntatore è il *touch pointer* dell'app, fuori dal protocollo. ⛔ Se il tema risulta vuoto KWin
   **ripiega sul tema visibile**: le forme si scrivono tutte (68), e il controllo che vale è
   l'assenza del ripiego nel journal. ⚠ Si perde il cambio di forma, come su GNOME: restituirlo
   vuol dire mandare la forma vera sul **canale puntatore di RDP**, dai metadati PipeWire
2. **il cursore del volume non governava niente** — `monitor.channel-volumes` mancava sul nostro
   sink, e in PipeWire il volume si applica **a valle** della presa del monitor (`kde.md` §10.5).
   ⚠ La misura fatta su un sink creato con `pactl` **assolveva** il codice, perché
   `pipewire-pulse` quella proprietà la mette da sé: la lezione è in [[remotix-lezioni]] §5.
   ⭐ **Decisione dell'utente**: il livello lo porta il **server**, dentro i campioni — è l'unica
   strada che regge su mstsc, Linux e Android e su ogni desktop, e il verso client → server in RDP
   **non esiste**. Da cui il sink si rialza al massimo **a ogni collegamento** (non solo alla
   creazione: WirePlumber rimette i livelli salvati e vince la corsa). Tutto in `REFERENCE.md` §7.5
3. **«Blocca» e «Cambia utente» nel menu** — tolte con KIOSK (`kde.md` §10.6); ⚠ hanno effetto
   **dal prossimo avvio di sessione**, non su una viva

⚠ **Quel che la voce 1 non ha fatto e serve alle altre**: nel banco la sessione Plasma la avvia lo
script e la Radeon si nega a mano (`INTEL=1`, `chgrp`); `uscita.c` cerca ancora `gnome-session` e su
KDE non lo troverà mai (adesso lo dice una volta sola invece che due volte al secondo). Tutto questo
è la **voce 3**.

⚠ **Tre dettagli dei rapporti restano da riversare, e si leggono dentro la voce che li usa**: la banda
a **finestra a orologio** e il **cursore** in 171 righe (voce 1), il **gate a tre condizioni** degli
appunti (voce 4).

⛔ **E le due trappole da rileggere prima di toccare l'unità systemd del compositore**: niente
`InaccessiblePaths` (o altro che implichi un mount namespace) — chiude il cancello della cattura; e
`KWIN_COMPOSE=O2` non garantisce la GPU, che si verifica solo chiedendo a KWin la stringa del renderer.

⚠ E prima di rimisurare: `misura-cattura.c` va corretto in due punti (`--fissa` non negozia con KWin;
i buffer `SPA_CHUNK_FLAG_CORRUPTED` del cursore vengono contati come fotogrammi).

## Due trappole di banco che sono costate mezza sessione

1. **`/proc/<pid>` di `kwin_wayland` è negato** perché il binario porta l'xattr `security.capability`:
   un binario con file capabilities è **non dumpable**, e `fd`/`maps` diventano root-only *anche per
   chi l'ha avviato*. `ls | grep` non stampa niente, l'errore va sullo stderr, e «vuoto» sembra
   «zero nodi DRM». Copiare il binario per perdere l'xattr **non funziona**: la copia non carica il
   plugin QPA `wayland-org.kde.kwin.qpa` e muore con `Aborted`. Si legge con `sudo`.
2. **Su Mesa ≥ 25 llvmpipe sta dentro `libgallium-*.so`**: cercare `llvmpipe`/`swrast_dri` fra le
   librerie caricate non prova più niente. La prova che regge è **il render node aperto**.

E la diagnosi del permesso si fa in tre secondi con `QT_LOGGING_RULES='KWIN_UTILS.debug=true'`: la
riga sta in **`KWIN_UTILS`**, non `kwin_core`, e distingue «Could not find the desktop file» (indice)
da «Interfaces found … : ()» (campo vuoto). Sono le lezioni `LEZIONI.md` §1.9 e §1.10.

## Il server, dopo il riavvio del 7 agosto

Rootfs in RAM, si rimette in tre comandi, in quest'ordine:
`provision-server.sh` → `server.sh copia` → `tmp/banco-compositori/provision-banco.sh`.
La cadenza a 60 sta in `main.c`, non in un file d'ambiente — e non va rimessa a mano.

⚠ **Stato lasciato la sera del 7 agosto**: il servizio REMOTIX **non è installato** (`systemctl
is-active remotix` → `not-found`, `/etc/default/remotix` assente), quindi nessuna porta 33xx è in
ascolto. Per il banco KDE sono stati installati `kwin-wayland`/`kwin-common` **4:6.3.6-1**,
`pipewire 1.4.2`, `wayland-utils`, `weston`, e l'utente è nei gruppi `video,render`. La macchina ha
**due GPU** (`card0`/`renderD128`, `card1`/`renderD129`) e KWin prende `renderD129`.

⚠ E ogni comando SSH apre una **sessione logind nuova** (49, 50, 51…), tutte **senza seat**: un
identificativo di sessione letto in un comando non vale in quello dopo.
