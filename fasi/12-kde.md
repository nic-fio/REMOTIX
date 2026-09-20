# Fase 12 — KDE

*Aperta il **18 settembre 2026**. Chiusa il —*

## Che cosa deve produrre

Il secondo desktop: **la stessa cosa su Plasma** (`PIANO.md` fase 12). L'utente apre il browser e
vede il suo desktop KDE, come oggi vede GNOME.

⛔ **La regola della fase, dell'utente, 18 settembre 2026**: *«Devi sviluppare KDE senza rompere ciò
che già funziona su GNOME.»* ⇒ La rete della fase 11 non è il collaudo finale: è il **guardiano** di
ogni passo. Si procede per **incrementi**, e ogni incremento attraversa gli stessi cancelli:

| | |
|---|---|
| **CP0** | la baseline: rete completa sulle quattro scatole, stesso binario ovunque |
| **CP1** | l'incremento è definito: obiettivo, invariante, moduli, prova KDE, prova client, regressioni GNOME da guardare, criterio |
| **CP2** | GNOME e KDE **osservati** sul punto dell'incremento, e la differenza scritta — niente dedotto |
| **CP3** | la modifica minima progettata: file, perché, che cosa di GNOME resta com'è |
| **CP4** | la prova KDE fatta davvero, sulla scena dichiarata |
| **client** | Chrome e Firefox su Linux, Chrome sull'emulatore Android — quando l'incremento tocca il percorso |
| **rete** | la rete completa, GNOME invariato, i guasti innestati ancora presi |
| **checkpoint** | un commit che si può riprendere |

⇒ Un rosso su GNOME è **una regressione finché non è dimostrato il contrario**, e si classifica:
A regressione vera · B assunzione GNOME nel codice comune · C difetto del banco · D invariante
sbagliato (⛔ mai come scorciatoia).

## Le decisioni prodotte

- **19 settembre 2026, dell'utente**: *emulatore Android sul server*. ⚠ Cambia la regola d'agosto
  «SDK ed emulatore restano sul tablet» (`DECISIONI.md` §5-bis.0-ter): `[M]` il tablet (7,5 GB) non
  regge Android 17 — memoria libera a 170 MB, Chrome mai partito. Il server ha KVM, 20 processori,
  22 GB liberi. ⇒ L'SDK sta in `/media/REMOTIX/android` (disco: il sistema del server vive in RAM).
  ⛔ Firefox per Android resta NON supportato (§7.18); si prova il **Chrome** dell'immagine
  Android 17 (145), e Chromium no (niente H.264).
  ⛔ **Dove si è arrivati, `[M]` 19 set**: SDK in `/media/REMOTIX/android`, KVM «installed and
  usable», AVD `remotix37` visto; ma **Chrome 145 non parte**: il fuoco resta al launcher, nessun
  socket `chrome_devtools_remote`, e la grafica emulata abortisce (`Assertion failed:
  !rcEnc->featureInfo()->hasReadColorBufferDma`) con `-gpu swiftshader_indirect`; con `-gpu guest`
  l'emulatore non arriva nemmeno ad `adb`. Stesso blocco sul tablet ⇒ non è la memoria.
- **19 settembre 2026, dell'utente**: *«alla fine farò io stesso i test come ultima verifica e
  validazione finale»* ⇒ la prova Android sull'emulatore si **ferma qui** (dichiarato, non
  nascosto): Android lo valida l'utente col suo Chrome. Se si riprende, si parte dalla riga sopra.
- **19 settembre 2026, dell'utente**: *«adesso ci occupiamo di KDE, LXQt verrà dopo — togli XFCE e
  LXQt»* ⇒ finché si lavora su KDE la rete gira con `--scatola "gnome kde"`: le maglie per desktop
  solo su GNOME (il guardiano) e KDE (il lavoro). ⚠ Il prezzo, dichiarato: per quel tempo non si
  vede se una modifica tocca xfce e lxqt. C11 e C14 restano sulle quattro scatole (allineamento e
  isolamento). Si torna alle quattro quando si apre il desktop successivo.
- `DECISIONI.md` §4.6-duodetricies — **un desktop per macchina**; la scelta fra più desktop è
  rimandata (`MASTERPLAN.md` M5).

## Il banco — scritto prima di sviluppare

Il banco è **la rete della fase 11** (`banchi/11-scatole/`), puntata sulla scatola `kde`. Il segno
che KDE è servito è quello già scritto: **`C1(kde)` diventa verde**, e dopo di lei C2, C3, C4, C6,
C7, C8b, C9 sulla stessa scatola.

⚠ **Tre cose del banco che la fase deve toccare, e si dichiarano qui prima di toccarle** (letture
del 18 settembre, `[R]`):

1. ⛔ **Tre cancelli «solo gnome» nel lancio delle maglie** — `11-gancio.sh` (`le_cinque_nuove`, e
   la famiglia veloce che fa C1 solo su gnome) e `11-accendi.sh` (c8b esce 3 fuori da gnome). Il
   commento che dice *«il giorno che il prodotto saprà accendere KDE non c'è niente da togliere»* è
   falso. ⇒ Aprirli **non ammorbidisce nessun giudizio**: è la condizione perché le maglie guardino
   KDE. Si aprono nell'incremento in cui la maglia corrispondente può diventare verde, non prima.
2. ⚠ **La scatola `kde` non contiene Plasma**: solo `kwin-wayland` e `xwayland`
   (`Contenitore.kde`). Il prodotto accende una sessione Plasma ⇒ la scatola cresce, dichiarandolo.
3. ⭐ **Un guasto di KDE, inventato e fatto girare** (`fasi/11-…` §3.6): oggi non esiste.

## Gli incrementi

| # | obiettivo | maglia che lo prova | stato |
|---|---|---|---|
| **0** | la baseline | la rete intera | ✅ **PASS** 18 set |
| **1** | la sessione Plasma **nasce** per un utente nuovo | nessuna ancora verde: C1(kde) resta rossa (manca la cattura) — si prova con la misura di I1 qui sotto | ✅ CP1 · CP2 · CP3 · CP4 · client (Firefox, Chrome) · rete — ⚠ Android del banco aperto |
| **2** | l'immagine di Plasma arriva al browser | ⭐ **C1(kde)** | ✅ CP1 · CP2 · CP3 · CP4 · client · rete — ⭐ **C1(kde) VERDE** |
| **3** | mouse e tastiera arrivano a Plasma | ⭐ **C4(kde)**, e C3 · C6 su kde | ✅ CP1 · CP2 · CP4 · client · rete — ⭐ **C4(kde) VERDE** |
| **4** | il banco guarda KDE come GNOME | ⭐ **C2(kde)**, **C8b(kde)** | ✅ cura · certificazioni · prove · rete — ⭐ **KDE: tutte le maglie** |
| **5** | gli appunti su KDE | `07-b54 --scatola rete11-kde` + controprova | ✅ prove · rete |

### Incremento 1 — la sessione Plasma nasce

| | |
|---|---|
| **OBIETTIVO** | un utente che si collega per la prima volta, su una macchina che ha **solo** Plasma, ottiene dal prodotto una sessione Plasma **sua**, senza schermo fisico, della misura della finestra del suo browser — e il prodotto la **riconosce viva**. ⛔ Niente cattura, niente input: sono gli incrementi dopo |
| **INVARIANTE** | su una macchina con GNOME **nulla cambia**: stesso stato letto, stesso drop-in, stesso comando, stessi tempi. E su KDE nessuna seconda sessione, nessun residuo dopo la chiusura (C7) |
| **MODULI** | `src/sessione.c` (riconoscere il desktop installato; far nascere Plasma; dire «viva» leggendo KWin) · `banchi/11-scatole/Contenitore.kde` (la scatola riceve Plasma, dichiarandolo) |
| **PROVA KDE** | nella scatola `kde`, un cliente vero (`01-b3-cliente.py`) entra con un utente nuovo ⇒ entro il tetto di C1 (26 s): `kwin_wayland --virtual --width W --height H` **con la misura del cliente**, `plasmashell` vivo, **una** `wl_output` W×H (`wayland-info` sul socket dell'utente), e il registro del prodotto che dice la sessione viva. **Controllo negativo**: col binario di oggi, sulla stessa scena, niente di tutto questo |
| **PROVA CLIENT** | l'immagine su KDE non c'è ancora ⇒ su KDE il browser non ha niente da mostrare. ⚠ Ma `sessione.c` è sul percorso di **ogni** nascita ⇒ Chrome e Firefox su Linux e Chrome sull'emulatore si collegano alla scatola **GNOME** e devono vedere il desktop come prima |
| **REGRESSIONI GNOME** | la rete intera; in particolare C1(gnome)×10 (nascita e tempi), C6 (stacco e riattacco: lo stato della sessione), C7 (chiusura) |
| **CRITERIO** | PROVA KDE verde e controllo negativo rosso · client su GNOME verdi · rete intera come la baseline, **tranne** quel che l'incremento cambia apposta — e C1(kde) che può cambiare motivo del rosso («nata, ma senza immagine»), non colore |


#### CP2 — osservato, non dedotto (`[M]` 18 set 2026, dentro `rete11-kde`)

| | GNOME (dal prodotto, baseline) | KDE (ricetta di v1 a mano con `banchi/12-i1-osserva-plasma.sh`, poi dal prodotto) |
|---|---|---|
| chi nasce | `gnome-session` → `org.gnome.Shell@wayland` col drop-in `--headless --no-x11` | `startplasma-wayland` → `plasma-kwin_wayland.service` col drop-in `--xwayland --virtual --width W --height H --no-lockscreen` |
| monitor alla nascita | ⛔ **zero**: il monitor lo monta la cattura (`RecordVirtual`) | ⭐ **uno**, `Virtual-0`, della misura della riga — `[M]` 1600x900 chiesto ⇒ 1600x900, una sola `wl_output` |
| quanto ci mette | ~1 s (C1) | KWin sul bus **0,79 s**, `plasmashell` **1,31 s** |
| la scheda | Intel | `OpenGL renderer string: Mesa Intel(R) UHD Graphics 770` — ⭐ GPU, non llvmpipe |
| la chiusura | `loginctl terminate-user` pulisce | ⭐ **0 processi in 529 ms**, `/run/user` sparita |

⇒ **DIFFERENZA**: su KDE l'uscita nasce con la sessione e la misura è quella del **primo** cliente;
non si cambia più finché la sessione vive. ⇒ **DECISIONE**: il prodotto scrive la misura nel drop-in
alla nascita (su GNOME la riga non la porta, e resta così).

⛔ **Un vicolo cieco di osservazione, scritto perché non lo si ripaghi**: il primo tentativo è stato
installare Plasma **a mano dentro la scatola accesa** (`apt-get install`). ⇒ `polkitd` è nato fuori
dalla ricetta dei gruppi (`LEZIONI.md` §1.54) ed è morto, e `loginctl` ha cominciato a rispondere
*«Connection timed out»*: `terminate-user` non chiudeva più niente (20 processi vivi dopo 55 s).
⭐ Con la scatola **ricostruita dalla ricetta** (R2 in `Contenitore.kde`) il difetto non c'è.
⇒ Non era Plasma: era la scatola fatta a mano.

#### CP3 — la modifica minima

| file | che cosa | GNOME |
|---|---|---|
| `src/sessione.h` | `SessioneDesktop`, `sessione_desktop()`, le tre costanti di Plasma | niente |
| `src/sessione.c` | `sessione_desktop()` (una volta per processo: KDE **solo** se c'è `startplasma-wayland` e non `gnome-session`); `sessione_viva`/`sessione_stato` su KWin; ambiente (`XDG_MENU_PREFIX=plasma-`, niente variabili GNOME); drop-in dell'unità di KWin **con la misura**; comando; unità da aspettare; uscita (`org.kde.Shutdown.logout`, poi `StopUnit` a forza); impostazioni e inibizione **dichiarate rimandate** | ⭐ ogni ramo GNOME è testualmente com'era: le righe nuove stanno **prima** e tornano, o scelgono un nome |
| `src/main.c` | una riga d'avvio: quale desktop, e perché | una riga in più nel registro (`avvio`, non area di sessione ⇒ C9 non la guarda) |
| `Contenitore.kde` | `plasma-workspace plasma-desktop` (R2) | niente |

⚠ **Rimandato, e dichiarato nel registro del prodotto**: le impostazioni di Plasma (sospensione,
menu KIOSK) e l'inibizione via powerdevil. Il blocco del desktop è già spento dalla riga di avvio.

#### CP4 — la prova KDE (`[M]` 18 set 2026, binario `6693555c`)

Prova a mano con `banchi/12-i1-nasce-plasma.sh` (dentro la scatola: un cliente `01-b3-cliente.py` vero, utente nuovo `ki1`):

| | atteso | misurato |
|---|---|---|
| `plasmashell` dell'utente | entro 26 s | ⭐ **2,59 s** dall'avvio del cliente |
| KWin | `--virtual`, misura del cliente | ⭐ `Virtual-0` **1920x1080** = la tela dichiarata dal cliente |
| sessioni nate | una | ⭐ **una** (`startplasma-wayland` ×1) — la guardia delle unità regge |
| il prodotto la vede viva | sì | ⭐ ultima «nessun KWin sul bus» a +0,8 s, poi più nessuna |
| la chiusura | niente resti | ⭐ 0 processi in 527 ms |
| ⛔ **controllo negativo**: binario di baseline `bfc5936a`, stessa scatola, stessa scena | niente | ⭐ `plasmashell` **MAI**, 0 processi Plasma |

⇒ Dopo la nascita il figlio prova a montare la cattura e dice *«Mutter non espone RemoteDesktop»*:
**atteso**, è l'incremento 2.

#### I client veri su GNOME (`[M]` 18 set 2026, binario `6693555c`, `banchi/12-client-veri.py`)

Utente nuovo `i1cli` nella scatola `gnome` (porta 8511), scena `muovi`, headless, registro del server letto con `--registro-cmd`. Il banco è stato **certificato** prima (`--certifica`): porta vuota ⇒ rosso su tutti e tre, parola sbagliata ⇒ rosso per rifiuto su Firefox e Chrome, giudice dei pixel ⇒ nero degenere e sfumatura no.

| browser | a · b · c · d · e · f · g | verdetto |
|---|---|---|
| Firefox 140 ESR (Linux) | 0 · 0 · 0 · 0 · 0 · 0 · 0 — 7 righe d'input nel registro del server, fotografia = il desktop GNOME | ⭐ **PASS** |
| Chrome 153 (Linux) | 0 · 0 · 0 · 0 · 0 · 0 · 0 — 8 righe d'input nel registro del server | ⭐ **PASS** |
| Chrome 113 sull'emulatore Android 14 | 0 · **1** · 3 · 3 · 3 · **1** · 3 — *«Opening handshake failed»*, `net::ERR_METHOD_NOT_SUPPORTED` su `/rcp/1` | ⛔ **FAIL — classe C, c'era già** |

⇒ **Android, perché non è una regressione**: il server apre la sessione WebTransport e il Chrome
dell'emulatore non apre mai il canale di controllo (congedo `0x0d` dopo 5 s): il guasto sta
**prima** dell'accesso, dove `sessione.c` non arriva. ⭐ **Controllo**: rimesso nella scatola il
binario di baseline `bfc5936a`, stessa scena ⇒ **stesso FAIL, stesse righe**. Poi rimesso
`6693555c` (md5 uguale nelle quattro scatole). ⇒ È il Chrome 113 dell'immagine di sistema
dell'emulatore, quaranta versioni indietro rispetto al Chrome da tavolo. ⚠ **Aperto**, è un buco
del banco e non del prodotto: la gamba Android va rifatta (decisione dell'utente, vedi sotto).

⚠ Due difetti del banco, trovati e curati nella stessa prova: Marionette non ha
`WebDriver:TakeElementScreenshot` (si usa `TakeScreenshot` con `id`) ⇒ Firefox dava 3 su (c) e (g);
e senza `--registro-cmd` Chrome dava 3 su (e). Né l'uno né l'altro è un verde regalato: erano 3.

⚠ La pagina scrive *«desktop sconosciuto»* anche su GNOME: è fisso in `src/rcp.c` («in fase 1 non
c'è compositore»), non toccato da questo incremento. ⇒ Da rivedere quando il prodotto saprà dire
quale desktop ha acceso.

#### La rete intera (`[M]` 18 set 2026, 19:53→22:06, binario `6693555c`, 7 969 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde**, come la baseline |
| kde · xfce · lxqt | come la baseline: ⛔ solo C1×10 rosso. ⭐ **C1(kde) ha cambiato motivo, non colore**: 10 su 10 *«la sessione è partita e nessun testimone del monitor ha parlato»* (CIECA) — è «nata, ma senza immagine», il criterio di I1. C7(kde) verde **con Plasma che adesso nasce davvero** |
| rete, sul server | C11 · C13 · C14 verdi (md5 uguale nelle quattro) |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| guasti innestati | ⭐ **25 su 25 visti** (24 sulle scatole, 1 sul portatile) |

⇒ **Incremento 1: CRITERIO soddisfatto** su KDE, GNOME e rete; la gamba Android del banco è
rossa per un motivo che c'era già (controllo fatto) ed è dichiarata aperta.

### Incremento 2 — l'immagine di Plasma arriva al browser

| | |
|---|---|
| **OBIETTIVO** | nella sessione Plasma dell'incremento 1 il figlio prende i fotogrammi da KWin e li manda al cliente: il browser **vede** il desktop KDE. ⛔ Niente input (incremento 3), niente appunti |
| **INVARIANTE** | su GNOME il palco si monta **come oggi**: stessa sequenza verso Mutter, stesse righe di registro, stessi tempi di C1. La scelta KWin/Mutter si fa **una volta**, con `sessione_desktop()` dell'incremento 1 — nessun secondo modo di riconoscere il desktop |
| **MODULI** | ⭐ nuovo `src/kwin.c` — da `fondamenta/remotix-c/src/kwin.c` di v1: il protocollo Wayland `zkde_screencast_unstable_v1` (`stream_output` sull'uscita `Virtual-0` ⇒ nodo PipeWire), cursore METADATO · `src/figlio.c` (monta/smonta il palco: Mutter **o** KWin; dopo, `cattura_avvia(nodo)` è la stessa) · `src/Makefile` (`wayland-scanner`, `wayland-client`) · il permesso: un `.desktop` con `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1`, com'era in v1 · `src/cattura.c` **solo se** CP2 misura che serve (v1: la fence di KWin, 830 buffer su 830 non pronti) |
| **PROVA KDE** | ⭐ **C1(kde)×10 VERDE** — la maglia di sempre, nessuna maglia nuova: 10 utenti nuovi, sessione nata **con un monitor** e fotogrammi entro il tetto. E una fotografia del desktop Plasma presa dal browser |
| **PROVA CLIENT** | Firefox e Chrome Linux sulla scatola **kde** (a·b·c·d·f·g verdi; (e) input resta rosso/3, è l'incremento 3) e sulla scatola **gnome** (come l'incremento 1). Android: vedi la decisione aperta |
| **REGRESSIONI GNOME** | la rete intera; in particolare C1, C3, C6 (il palco si rimonta dopo lo stacco), C8b |
| **CRITERIO** | C1(kde) verde · client su kde vedono Plasma · rete intera come dopo I1 **tranne** C1(kde) verde · GNOME invariato · guasti tutti presi. ⚠ I cancelli «solo gnome» di C3/C8b **non** si aprono qui se richiedono input |

#### CP2 — osservato (`[M]` 18 set 2026, dentro `rete11-kde`, `banchi/12-i2-cancello.sh`)

| | GNOME | KDE |
|---|---|---|
| chi dà il nodo PipeWire | Mutter, D-Bus `ScreenCast.RecordVirtual` (`mutter.c`) — un monitor **nuovo** della misura chiesta | KWin 6.3.6, protocollo **Wayland** `zkde_screencast_unstable_v1` **v5**, `stream_output` sull'uscita che c'è già (`Virtual-0`) |
| il cancello | nessuno | ⛔ il global **non c'è** per un client qualunque (58 altri sì); ⭐ c'è con un `.desktop` in `/usr/share/applications` che dichiara `X-KDE-Wayland-Interfaces` e ha `Exec=` sull'eseguibile canonico — **anche scritto a sessione già viva** (+3 s). `XDG_MENU_PREFIX=plasma-` nell'ambiente di KWin: sì (dall'incremento 1) |
| la misura | segue la tela chiesta | ⛔ **fissa**: l'uscita è della misura del primo cliente e KWin 6.3.6 non la ridimensiona (v1: `kwin!7932`, atteso per 6.8). `[M]` chiedere 1384x912 a un'uscita 1388x914 ⇒ PipeWire `no more input formats` ⇒ palco **mai più** montato |
| il primo fotogramma | la Shell | ⭐ la **schermata d'avvio di Plasma** («Plasma made by KDE», 99 % nero + logo) per ~2,4 s, poi il desktop. `[M]` aspettare `org.kde.plasmashell` sul bus **non** la evita (il nome arriva prima) ⇒ provato e **tolto** |
| il resto della strada | `cattura.c` → `codificatore.c` | ⭐ **la stessa**: dal nodo in poi niente cambia. `cattura.c` scarta già i buffer `SPA_CHUNK_FLAG_CORRUPTED` (i buffer di solo cursore di KWin, v1 §4.7) |

⚠ **Non misurato e dichiarato**: la *fence* di KWin (v1: 830 buffer su 830 arrivano col disegno
in corso). Le fotografie prese dal browser non mostrano strappi, ma una fotografia non è una
misura: resta aperto per quando si guarderanno i numeri.

#### CP3 — la modifica

| file | che cosa | GNOME |
|---|---|---|
| ⭐ `src/kwin.c`, `src/kwin.h` (nuovi) | da `fondamenta/remotix-c/src/kwin.c` di v1, **solo la cattura**: registry, uscita, `stream_output` col cursore METADATO, attesa del nodo (5 s), pompa Wayland, chiusura; e `kwin_scrivi_permesso()` | non chiamato |
| `src/protocolli/zkde-screencast-unstable-v1.xml`, `src/Makefile` | l'XML di v1; `wayland-scanner` genera il codice a ogni costruzione; `wayland-client` fra le librerie | una libreria in più nel binario (c'è in tutte e quattro le scatole: `ldd` 0 mancanti) |
| `src/main.c` | all'avvio, **solo su KDE**: il server scrive `/usr/share/applications/org.kde.remotix.desktop` con `Exec=` sul proprio binario (il figlio è un `execve` dello stesso) | niente |
| `src/figlio.c` | `palco_kwin` accanto a `mut`: su KDE `kwin_apri()` al posto di `mutter_apri()`, poi `cattura_avvia(nodo)` com'era; `misura_del_palco()`: su KDE la cattura chiede la misura dell'uscita, e il cambio di tela risponde con quella («la pagina riscala», §4.5) | ⭐ il ramo `else` è il codice di prima, testuale; `nodo_del_palco(mut)` = `mutter_nodo(mut)` |

#### CP4 — le prove KDE (`[M]` 18 set 2026, binario `8694ec33`)

| | misurato |
|---|---|
| C1(kde)×3 (`11-accendi.sh c1 kde 3`) | ⭐ **VERDE** 3 su 3, monitor «Virtual-0» (1 dopo), ~150 fotogrammi — la prima volta |
| Firefox Linux, utente nuovo, scatola `kde` | ⭐ **PASS** 7 su 7: schermata d'avvio a 0,9 s, desktop Plasma a 3,3 s; riconnessione in 0,3 s |
| Chrome Linux, stessa sessione | a·b·c·e·f·g verdi · ⛔ (d) 0 fotogrammi muovendo il mouse — ⭐ **atteso**: l'input arriva al server (e) ma non ancora a KWin (incremento 3), e il cursore lo disegna la pagina ⇒ il desktop non cambia |
| ⚠ (e) su KDE | il banco prova che l'input arriva **al server**, non al desktop: su KDE il figlio dice *«il canale di input NON si apre»*. Il verde di (e) qui **non** vuol dire «si comanda» |
| prima della cura della misura (`b835dc63`) | ⛔ la riconnessione di Chrome chiedeva 1384x912: `no more input formats`, palco mai più montato, 0 fotogrammi in 30 s ⇒ curato con `misura_del_palco()` |

⚠ **Il banco dei client è cambiato** (`12-client-veri.py` (c)): una fotografia sola a +1 s giudicava
la schermata d'avvio di Plasma; ora si fotografa **fino al tetto** e si scrive quando è arrivato il
desktop e quante fotografie degeneri l'hanno preceduto. Ricertificato (`--certifica`: porta vuota,
parola sbagliata, giudice dei pixel — tutti presi). ⚠ Il ramo «degenere fino al tetto» non ha una
prova di certificazione sua: è dichiarato.

#### La rete intera (`[M]` 18→19 set 2026, 22:41→00:50, binario `8694ec33`, 7 710 s)

| | |
|---|---|
| GNOME | ⭐ tutto verde **tranne C9** — ⛔ e C9 era **mio**: l'unica riga senza padrone era *««i1cli» ricontrollato…»*, cioè la sessione della prova client lasciata viva nella scatola mentre C9 contava i suoi due inquilini (classe **C**). ⭐ Chiusa la sessione, **C9(gnome) da sola: esito 0**, 631 righe obbligate su 631 col nome |
| ⭐ **kde** | **C1(kde)×10 VERDE** — 10 su 10 nate con «Virtual-0», 155-174 fotogrammi; C5, C7, C8, C9 verdi, guasti visti |
| xfce · lxqt | come la baseline: solo C1×10 rosso |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| guasti innestati | ⭐ 24 visti sulle scatole + 1 sul portatile |

⇒ **Incremento 2: CRITERIO soddisfatto.** ⚠ Lezione di metodo: gli utenti delle prove a mano si
chiudono **prima** di lanciare la rete — la rete guarda il registro intero, anche quel che non è suo.

### Incremento 3 — mouse e tastiera arrivano a Plasma

| | |
|---|---|
| **OBIETTIVO** | quel che l'utente fa nel browser (puntatore, pulsanti, tasti, rotella) arriva al desktop Plasma |
| **INVARIANTE** | su GNOME il canale di input nasce e guarisce come oggi (`mutter_eis_fd`, `mutter_eis_riattacca`, la regione per chiave, la rotella con `UNITA_PER_DELTA`) |
| **MODULI** | `src/kwin.c` (`connectToEIS(7)` di v1, il gettone, la guarigione) · `src/input.c` (tre punti: il descrittore, la regione, la rotella) · `src/figlio.c` (quale canale aprire) · il banco: il cancello «solo gnome» di `11-gancio.sh` |
| **PROVA KDE** | ⭐ **C4(kde) verde** — il tasto arriva fino allo schermo, la maglia di sempre — e i suoi due guasti visti |
| **PROVA CLIENT** | Firefox e Chrome Linux su `kde` e su `gnome`: 7 su 7 |
| **REGRESSIONI GNOME** | la rete intera; in particolare C4, C6 (la guarigione dell'input), C8b |
| **CRITERIO** | C4(kde) verde · le maglie che ora possono essere verdi su KDE lo sono, e i loro guasti si vedono · GNOME invariato |

#### CP2 — osservato (`[M]` 19 set 2026, binario `a77366b2`, scatola `kde`)

| | GNOME | KDE |
|---|---|---|
| chi dà il canale | Mutter, `RemoteDesktop.Session.ConnectToEIS` | ⭐ KWin, `org.kde.KWin.EIS.RemoteDesktop.connectToEIS(7)` ⇒ descrittore + gettone — concesso al primo colpo, nessun permesso da chiedere |
| la regione | per chiave (`mapping-id`) | ⭐ *«regione del puntatore per geometria: 0,0 1384x912 (di 1, mapping-id «assente»)»* — il ramo che `input.c` aveva già |
| la rotella | `scroll_delta` / 12 | `scroll_discrete` in unità da 120 (v1: `scroll_delta` su KWin non fa scatti) — ⚠ **non ancora misurata** da una maglia |

#### CP4 — le prove KDE

| | misurato |
|---|---|
| Chrome e Firefox Linux su `kde` | ⭐ **PASS 7 su 7** tutt'e due; (d) muovendo il mouse **76** fotogrammi nuovi in 8 s (prima dell'input: 0) |
| ⭐ **C4(kde)** | **VERDE**: la zona attesa passa dal colore di partenza a quello d'arrivo al 100 %, la cornice cambia dello 0 % |
| C4(kde) guasti | `--senza-tasto` ⭐ visto · `--scena-sorda` ⭐ visto |
| ⭐ **C3(kde)** | **VERDE** (10 994 fotogrammi in 187 s, 60 coppie su 60 diverse); `--fotogramma-ripetuto` ⭐ visto; `--scena-ferma` regge |
| ⚠ C3(kde) `--codificatore-fermo` | **3**, non giudica: l'innesto (SIGSTOP 2 s dopo che il codificatore lavora) cade sulla schermata d'avvio di Plasma e l'ultimo fotogramma è quasi nero ⇒ **saltato su KDE, dichiarato** nel gancio. Il guasto di C3 su KDE resta `--fotogramma-ripetuto` |
| ⭐ **C6(kde)** | **VERDE** (si ritrova); `--uccidi-la-sessione` ⭐ visto (*«specie: un'altra sessione»*) |
| C2(kde) | **3**: i primi 12 fotogrammi sono la schermata d'avvio, e C2 li prende per il suo «prima» ⇒ **saltata su KDE, dichiarato**: si adatta il banco in un incremento suo |
| C8b(kde) | ferma da `11-accendi.sh` (*«il prodotto avvia solo GNOME»*) ⇒ **saltata, dichiarato**: stesso incremento |

⇒ **Il banco**: `11-gancio.sh` `le_cinque_nuove` apre `kde` per C3, C4, C6 (coi guasti che si vedono) e lo
tiene chiuso per C2, C8b e per il guasto «codificatore fermo», ciascuno con la sua ragione nel
registro; xfce e lxqt restano chiuse.

#### La rete intera (`[M]` 19 set 2026, 01:33→03:58, binario `a77366b2`, 8 698 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde**, C9 compresa (utenti delle prove a mano chiusi prima) |
| ⭐ **kde** | **tutto verde**: passo 0, C1×10, C3 (+ scena ferma), **C4**, C5, **C6**, C7, C8, C9 — e i guasti di C3, C4 (×2), C6, C5, C7, C8, C9 visti. Saltate, dichiarato: C2, C8b, C3 «codificatore fermo» |
| xfce · lxqt | come la baseline: solo C1×10 rosso |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| guasti innestati | ⭐ **28 visti** sulle scatole (erano 24: i 4 nuovi sono di KDE) + 1 sul portatile |
| client su GNOME, binario `a77366b2` | Firefox e Chrome **PASS** 7 su 7 |

⇒ **Incremento 3: CRITERIO soddisfatto.**

### Incremento 4 — il banco guarda KDE come GNOME (C2, C8b)

⛔ **Solo banco, niente prodotto**: il binario resta `a77366b2`.

| | |
|---|---|
| **OBIETTIVO** | C2 e C8b giudicano anche su KDE |
| **LA CAUSA, `[M]`** | tutt'e due prendevano il «prima» dai primissimi fotogrammi del flusso, e su KDE quelli sono la schermata d'avvio di Plasma (~2,4 s, 100-200 fotogrammi neri). C2 ne guardava 12, C8b 1 ⇒ «non lo so» per sempre |
| **LA CURA** | la stessa regola in tutt'e due, e vale per ogni desktop: il «prima» è il **primo fotogramma non nero** fra i primi 240. C2 la aveva già (`scegli_il_prima`) — si alza solo il numero, da 12 a 240; C8b la riceve (`estrai(…, giudice)`). ⛔ Se sono tutti neri resta «a monte» / «non lo so», come prima; se il primo non nero è già la pagina, «già magenta» e non si giudica |
| **GNOME** | ⭐ invariato: il primo disegnato è il fotogramma **1** (C2 lo scrive: *«fotogrammi guardati per il prima: 1»*) |
| **certificazioni** | `--certifica` di C2 e di C8b: uscita 0 |

| `[M]` 19 set 2026 | esito |
|---|---|
| C8b(kde) | ⭐ **VERDE**, 2 su 2 vedono la pagina dal cliente — il «prima» è il fotogramma 181 |
| C8b(kde) `--senza-cura` | ⭐ guasto **visto** (1 su 2 non la vede, e il primo sì) |
| C8b(gnome) | ⭐ VERDE, 2 su 2 |
| C2(kde) | ⭐ **VERDE** — il «prima» fra 204 fotogrammi |
| C2(kde) `--applicazione-che-muore` · `--finestra-che-non-si-apre` | ⭐ tutt'e due **visti** |
| C2(gnome) | ⭐ VERDE, «prima» = fotogramma 1 |

⇒ I cancelli: `11-gancio.sh` apre C2 e C8b a `kde`; `11-accendi.sh` lascia girare C8b su `gnome` e
`kde`. ⚠ Resta chiuso su KDE il solo guasto «codificatore fermo» di C3 (l'innesto cade durante la
schermata d'avvio): curarlo vuol dire spostare l'istante dell'innesto, ed è un passo suo.

#### La rete intera (`[M]` 19 set 2026, 04:50→07:48, binario `a77366b2`, 10 645 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde** (C2 e C8b col banco nuovo: il «prima» resta il fotogramma 1) |
| ⭐ **kde** | **tutto verde, e adesso ci sono tutte e dieci le maglie**: passo 0, C1×10, **C2**, C3 (+ scena ferma), C4, C5, C6, C7, C8, **C8b**, C9 — guasti visti. Saltato, dichiarato: il solo guasto «codificatore fermo» di C3 |
| xfce · lxqt | come la baseline: solo C1×10 rosso |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| guasti innestati | ⭐ **31 visti** sulle scatole (erano 28: i 3 nuovi sono C2 ×2 e C8b su KDE) + 1 sul portatile |

⇒ **Incremento 4: CRITERIO soddisfatto.**

### Incremento 5 — gli appunti su KDE

| | |
|---|---|
| **OBIETTIVO** | copia e incolla di testo nei due versi, browser ↔ desktop Plasma, come su GNOME (decisione dell'utente, 19 set) |
| **INVARIANTE** | su GNOME gli appunti restano `appunti.c` com'era: il guscio passa la mano a KDE con una riga in cima a ogni funzione pubblica, solo se `kde` c'è |
| **MODULI** | ⭐ `src/appunti_kde.c` e `src/appunti_kde.h` (da `fondamenta/remotix-c/src/appunti_wlr.c` di v1: `zwlr_data_control_manager_v1`, **nessun** permesso da chiedere) · `src/appunti.c` e `src/appunti.h` (`appunti_apri_kde()` e i passa-mano) · `src/kwin.c` e `src/kwin.h` (`kwin_display_apri()` esportata) · `src/figlio.c` (quale aprire) · `src/Makefile` + `src/protocolli/wlr-data-control-unstable-v1.xml` · il banco: R3 `wl-clipboard` nelle ricette gnome e kde, `07-b54-appunti-due-versi.py --scatola` |
| **FORMA** | la stessa di GNOME: SOLO TESTO (`DECISIONI.md` §5-ter.1), la stessa fila dei tipi, lo stesso tetto, la stessa memoria dell'ultimo testo, e se il client non ha niente si rende alla sessione il SUO testo. Le trappole di v1 portate: l'eco (criterio di stato), il giro completo prima di leggere, `POLLHUP` = pronto, il passo minimo verso klipper, mai `x-kde-onlyReplaceEmpty` |

| `[M]` 19 set 2026, binario `954a208c` | esito |
|---|---|
| `07-b54 --scatola rete11-kde`, Firefox e Chrome | ⭐ **sessione→client ⭐ · client→sessione ⭐ · tastiera dopo l'incolla ⭐**, tutt'e due |
| ⛔ **controprova**: binario `a77366b2` (senza appunti KDE), stessa scena | ⭐ **rosso nei due versi** — il banco distingue |
| `07-b54 --scatola rete11-gnome` | Chrome ⭐⭐⭐ · Firefox: verso A ⛔ — ⚠ **c'era già**: stesso rosso col binario `a77366b2` ×2, e con Chrome **da solo** su sessione nuova. ⇒ È «la PRIMA connessione su una sessione GNOME appena nata»: la copia di `wl-copy` non arriva nemmeno al registro (Mutter non annuncia niente). Ipotesi, **non dimostrata**: `wl-copy` su Mutter non ha data-control e senza una superficie col fuoco non copia ⇒ banco. **Aperto**, fuori da KDE |
| rete intera, binario `954a208c` (08:07→11:05, 10 637 s) | GNOME e KDE **tutto verdi**, xfce/lxqt come la baseline, C11 · C13 · C14 verdi, **31 guasti visti** |

⚠ **Non ancora nella rete**: gli appunti non hanno una maglia della fase 11. Sono provati da `07-b54`
con la controprova, e il giorno che entrano nella rete sarà una maglia sua.

### Incremento 6 — il guasto «codificatore fermo» di C3 anche su KDE

| | |
|---|---|
| **OBIETTIVO** | l'ultimo guasto chiuso a `kde` (decisione dell'utente, 19 set: «anche questo punto va fatto») |
| **LA CAUSA** | la schermata d'avvio di Plasma si anima per ~2,4 s: `aspetta_che_i_fotogrammi_arrivino` passava sull'animazione, e il SIGSTOP cadeva sul nero |
| **LA CURA** | nel banco, non nel prodotto: `11-c3` aspetta che il codificatore **si fermi** (`aspetta_che_il_desktop_si_fermi`) prima di accendere la scena, più un respiro di 2 s prima dell'innesto (`--respiro-innesco`), contato in `secondi_prima`. Su GNOME il desktop è già fermo ⇒ un passo solo. Nessuna domanda sul desktop |
| **IL CANCELLO** | `11-gancio.sh` apre a `kde` il guasto «codificatore fermo» |

#### La rete (`[M]` 19 set 2026, 13:21→15:51, binario `954a208c`, `--scatola "gnome kde"`, 9 028 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde**, C3 «codificatore fermo» compreso (col banco nuovo) |
| ⭐ **kde** | **tutto verde, e adesso nessun guasto è saltato**: passo 0, C1×10, C2, C3 (+ scena ferma), C4, C5, C6, C7, C8, C8b, C9 — ⭐ **C3 «codificatore fermo» visto** |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto — ⚠ C16 era rosso per tre percorsi abbreviati (del tipo «kwin.c/.h») in questo documento: classe C, scritti per intero |

### La sospensione — era già chiusa, e per tutti i desktop

L'utente (19 set) propone: *«perché non si fa in modo che remotix disabiliti alla radice standby,
reboot e suspend della macchina per tutti gli utenti normali, cioè tutti eccetto root?»* ⇒ ⭐ **è
già così**, e da una decisione sua: `DECISIONI.md` §4.7 (15 agosto), tre cinture messe da
`src/provisiona.sh` — polkit (12 azioni, `*-multiple-sessions` comprese), `AllowSuspend=no`,
logind sui tasti. Nessuna delle tre sa quale desktop giri.

`[M]` 19 set 2026, sul server, da `nicfio`: `CanSuspend` · `CanReboot` · `CanPowerOff` ·
`CanHibernate` = **«no»** tutte e quattro.

⚠ **Il monitor fisico del server** può continuare ad andare in standby (chiarito con l'utente): le
sessioni remote hanno ciascuna il proprio schermo virtuale.

⚠ **Resta un pezzo, ed è un altro**: lo schermo **della sessione remota** di Plasma, che
powerdevil spegne dopo 10 minuti di inattività (su GNOME la stessa cosa è spenta da
`sessione_impostazioni()`). È il ramo KDE di `sessione_inibisci()` — incremento 7.

### Incremento 7 — lo schermo della sessione remota di Plasma non si spegne

| | |
|---|---|
| **OBIETTIVO** | powerdevil non spegne lo schermo della sessione remota dopo 10 minuti (su GNOME lo fa già `sessione_impostazioni()`) |
| **MODULI** | `src/sessione.c`: `guardia_di_powerdevil()`, un filo che ogni 2 s guarda chi possiede `org.kde.Solid.PowerManagement` e chiede `PolicyAgent.AddInhibition(4)` ogni volta che il proprietario **cambia** · il banco: `banchi/12-i7-schermo.sh` · la scatola: R4 `powerdevil` in `Contenitore.kde`, `--cap-add=WAKE_ALARM` in `11-accendi.sh` |
| **INVARIANTE** | su GNOME `sessione_inibisci()` resta com'era: il filo nasce solo se `e_kde()` |

⛔ **Due scoperte**, `[M]` 19 set 2026:
1. **nella scatola powerdevil non partiva**: il suo eseguibile porta `cap_wake_alarm=ep`, fuori dal
   limite del contenitore ⇒ 203/EXEC «Operation not permitted». Classe C: `--cap-add=WAKE_ALARM`,
   che avvicina la scatola alla macchina vera.
2. **una chiamata sola arriva troppo presto** (binario `6a41a28e`): quando il palco è pronto
   powerdevil non c'è ancora («ServiceUnknown» — è un'unità di `plasma-core.target`, non si attiva
   dal bus). E il figlio non ha un ciclo GLib ⇒ un filo che guarda, invece di `g_bus_watch_name`.

| `[M]` 19 set 2026, `12-i7-schermo.sh`, giudice **powerdevil stesso** (`HasInhibition`) | esito |
|---|---|
| ⛔ controprova: binario `954a208c` (senza il ramo) | **false** — lo schermo si spegnerebbe |
| binario `6a41a28e` (una chiamata sola) | **false** — «ServiceUnknown» |
| ⭐ binario `c7b228c5` (il filo) | **true** |
| ⭐ `c7b228c5`, powerdevil ucciso a sessione viva | systemd lo fa ripartire ⇒ **true** di nuovo, il figlio l'ha richiesta al nuovo proprietario |

#### La rete (`[M]` 19 set 2026, 15:59→18:30, binario `c7b228c5`, `--scatola "gnome kde"`, 9 030 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde** |
| ⭐ **kde** | **tutto verde**, nessun guasto saltato — e nel registro della scatola **20** inibizioni chieste a powerdevil, **0** rifiutate, **0** «non è comparso» |
| rete, sul server | C13 · C14 verdi · ⛔ **C11 rossa, classe C**: il binario nuovo era messo solo in gnome e kde, xfce e lxqt avevano ancora `954a208c` — la maglia ha fatto il suo lavoro. Messo `c7b228c5` anche là ⇒ C11 **verde** |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |


### Incremento 8 — gli appunti entrano nella rete (C17), e un difetto di tutti i desktop

| | |
|---|---|
| **OBIETTIVO** | gli appunti di KDE controllati a ogni rete, non più solo a mano (`07-b54`) |
| **LA MAGLIA** | `banchi/11-scatole/11-c17-gli-appunti-vanno-nei-due-versi.py`: tre fatti col loro nome — **A** dispositivo → sessione (`wl-paste` legge quel che il cliente ha annunciato) · **B** sessione → dispositivo (`wl-copy`, e il server lo annuncia al cliente attaccato) · **R** chi si riattacca lo riceve. Guasto innestato `--senza-copia` ⇒ tre rossi |
| **L'ARBITRO** | `wl-clipboard` vuole `zwlr_data_control_manager_v1` (o `ext_…`): KWin ce l'ha, Mutter no. ⛔ `[M]` su GNOME `wl-paste` e `wl-copy` restano appesi (uscita 124) mentre il server scrive «22 byte consegnati alla sessione» ⇒ la maglia lo chiede a `wayland-info` e, se manca, esce **3** dicendolo. Nessun cancello per desktop nel gancio |

⛔⛔ **Il difetto trovato, ed è di TUTTI i desktop** (`src/rcp.c`, copia gemella in `banchi/rcp/`):
un cliente che si riattacca a un figlio vivo fa rileggere la clipboard del desktop, ma la lettura
arriva quando la sessione RCP è ancora in `attesa-verdetto`. Il testo si teneva «per chi si
attaccherà» e **nessuno lo annunciava mai**: chi rientrava non sapeva che cosa c'era negli
appunti. ⇒ `annuncia_il_tenuto()`, chiamata appena la sessione passa ad `S_ATTIVA` (§2.5: dopo
`SESSIONE`).

| `[M]` 19 set 2026, scatola `kde` | A | B | R |
|---|---|---|---|
| ⛔ controprova: binario `c7b228c5` (senza la cura) | ⭐ | ⭐ | ⛔ «None» |
| ⭐ binario `2563cb22` (la cura) | ⭐ | ⭐ | ⭐ |
| `2563cb22`, `--senza-copia` | ⛔ | ⛔ | ⛔ — il guasto si vede |
| prova a mano, 5 giri | 5/5 | — | 5/5 |
| scatola `gnome` | esito **3**: l'arbitro non c'è su Mutter | | |

#### La rete (`[M]` 19 set 2026, 19:56→22:28, binario `2563cb22`, `--scatola "gnome kde"`, 9 116 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde** (la cura di `rcp.c` vale anche qui) · C17(gnome) **3** e 3 col guasto: l'arbitro non c'è, detto |
| ⭐ **kde** | **tutto verde**, C17 compresa · ⛔ **C17 guasto innestato «NON REGGE», classe C**: il guasto era VISTO (A, B, R rossi) ma la maglia usciva 1, e nella rete col guasto l'esito si legge al contrario (0 = visto). Corretta, e rifatta da sola: kde verde · guasto visto con esito 0 · gnome 3 e 3 |
| ⚠ e in più | la maglia aspetta che il compositore risponda (`wl_compositor`) prima di dire «l'arbitro non c'è»: un 3 su una sessione sana non deve poter capitare |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |

⚠ **Resta aperto, dichiarato**: su GNOME gli appunti non hanno ancora un arbitro nella rete. Serve
un client Wayland con `wl_data_device` e il fuoco (GTK), come diceva `07-b45`: è lavoro di GNOME,
non di questa fase.

### Incremento 9 — quel che ha trovato la prova dell'utente (19-20 set 2026)

L'utente prova KDE da Chrome sul suo portatile, e in un'ora tira fuori **quattro cose**. ⭐ Tre
erano decisioni già prese e **perdute nel passaggio da v1 a v2**: è il prezzo del riporto selettivo,
e la cura è che adesso ciascuna ha un banco (`banchi/12-i9-logout.sh`, `banchi/12-i10-menu-e-puntatore.sh`).

| | che cosa vedeva l'utente | la causa | la cura |
|---|---|---|---|
| **1. si poteva spegnere** | dal menu di Plasma «Spegni» e «Riavvia» | ⛔ **la scatola**, non il prodotto: le tre cinture di §4.7 le mette `src/provisiona.sh` sulla macchina vera, e nelle scatole non c'erano mai state — `CanPowerOff` diceva «challenge» invece di «no» | le stesse righe, negli stessi file, nella preparazione della scatola (`11-accendi.sh`) |
| **2. «Blocca» e «Cambia utente»** | voci che non fanno niente | le regole KIOSK di v1 (`scrivi_regole_menu`) non riportate | `scrivi_regole_menu_kde()`: `lock_screen`, `start_new_session`, `switch_user` a `false` in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals`, davanti a `/etc/xdg`. ⛔ `logout` non si tocca |
| **3. il logout non chiudeva** | dopo «Esci» la pagina restava sull'ultima immagine | ⛔ **del prodotto**: su Plasma la sessione muore in SILENZIO — KWin non chiude il flusso, il nodo PipeWire sparisce e la presa torna «zero» per sempre. E `vista_viva` era una `static` accesa solo dalla lettura dello stato, che su KDE non si fa mai ⇒ il figlio credeva la sessione «non ancora nata» e la faceva RINASCERE | `kwin.c`: la caduta della connessione Wayland segna `chiuso`. `figlio.c`: se `kwin_chiuso()` si smonta il palco, e `vista_viva` si accende anche col palco di KWin ⇒ §7.6 fa il resto (congedo `0x10`, la pagina torna al modulo d'accesso) |
| **4. la coda del puntatore** | due puntatori, il secondo che insegue | ⛔ con `--virtual` KWin disegna il cursore DENTRO l'immagine (`STUDI.md` §kde, misurato l'8 ago 2026). La cura di v1 — tema del cursore trasparente — non riportata | `scrivi_tema_cursore_kde()`: 68 forme 1×1 ad alfa zero in `$XDG_RUNTIME_DIR/remotix/icons`, più `XCURSOR_THEME`+`SIZE`+`PATH` (KWin guarda il tema **solo** se c'è anche `SIZE`) |

| `[M]` 19-20 set 2026, scatola `kde` | vecchio `2563cb22` | nuovo `d7a5db20` |
|---|---|---|
| `12-i9`: la pagina dopo «Esci» | ⛔ attaccata, nessun `0x10`, dopo 30 s ancora lì | ⭐ chiusa dopo **2 s** col codice `0x10`, e KWin **non rinasce** |
| `12-i10` 1. cursore invisibile | ⛔ NO (XCURSOR_* 0/3, 0 forme) | ⭐ SI (3/3, **68 forme**, 0 ripieghi) |
| `12-i10` 2. menu senza blocco | ⛔ NO (0/1, regole assenti) | ⭐ SI (regole 3/3) |
| `12-i10` 3. nessuno spegne | ⭐ SI (4/4 «no») — è della scatola, e infatti non cambia col binario | ⭐ SI |

#### La rete (`[M]` 20 set 2026, 02:21→04:52, binario `d7a5db20`, `--scatola "gnome kde"`, 9 119 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde** — le tre cure toccano `sessione.c`, `kwin.c` e `figlio.c`, e GNOME non se n'è accorto |
| ⭐ **kde** | **tutto verde**, C17 compresa: il cursore invisibile non disturba le maglie che guardano i pixel, e il menu ridotto non disturba niente |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| rossi | **nessuno** |

### Incremento 10 — la seconda tornata della prova dell'utente (20 set 2026)

L'utente riprova e trova **tre cose**, due sue e una che chiude un buco vecchio.

| che cosa vedeva | la causa | la cura |
|---|---|---|
| **nessun puntatore** (dopo il tema invisibile) | il tema invisibile arriva anche nel METADATO: il client si vestiva di una forma invisibile. ⛔ Peggio di due puntatori | `cursore.c`: una bitmap tutta trasparente è «nascosto» (§5.5) · e su Plasma il nascondimento NON si consegna (`cursore_mai_nascondere`, acceso dal figlio quando il palco è KWin) ⇒ chi guarda tiene il puntatore del suo sistema |
| **le finestre non si ridimensionano** | Plasma nasce con `BorderSizeAuto`: bordi di pochi pixel. Al monitor si prendono perché il cursore cambia forma, ⛔ in remoto il cursore del desktop è invisibile apposta | `sessione.c`: `kwinrc` nella stessa cartella delle regole, `BorderSize=Normal` — ⚠ **senza** `[$i]`: è un punto di partenza, e da Impostazioni di sistema l'utente lo cambia |
| **su Firefox la clipboard non va dal client al server** | ⭐ **non è un difetto**: Firefox concede la lettura degli appunti **solo** nell'istante del `Ctrl+V` sulla pagina. Con «Incolla» dal menu del desktop remoto la pagina serve 0 byte — `[M]` il registro: «rilettura negata … servo quel che ho» | `pagina.html`: un cartello di 7 s sulla tela — «premi Ctrl+V su questa pagina» — quando la lettura è negata e non c'è testo da servire (deciso dall'utente) |

⭐ **E nelle scatole entrano gli strumenti per lavorare** (chiesti dall'utente): `konsole`, `dolphin`
e `nano` su kde; `gnome-terminal`, `nautilus` e `nano` su gnome. Sono del banco, non del prodotto.

#### La rete (`[M]` 20 set 2026, 07:20→09:52, binario `836a88b6` + pagina `4eb65ca2`, 9 087 s)

| | |
|---|---|
| GNOME · **kde** | ⭐ **tutto verde**, nessun rosso in nessuna maglia |
| rete, sul server e sul portatile | C10 · C11 · C12 · C13 · C14 · C15 · C16 verdi |

⭐ **E LA PROVA DELL'UTENTE È COMPLETA**: Chrome e Firefox su Linux, **Chrome su Android** —
audio, video e appunti. ⚠ Un giro su tre di `07-b54` (Firefox su Wayland) ha dato rosso sulla
**tastiera dopo l'incolla**: intermittente, da tenere d'occhio.

### Incremento 11 — i gruppi della scheda, messi da REMOTIX (decisione dell'utente, 20 set 2026)

Domanda dell'utente: *«REMOTIX chiede che gli utenti appartengano ai gruppi video e render.
Normalmente le distro non ce li mettono: potrebbe essere un problema?»* ⇒ Sì, e il sintomo è il
peggiore: **si collega e non vede niente**, senza un errore. La decisione e la misura stanno in
`DECISIONI.md` §7.21; qui restano i moduli e l'esito.

| | |
|---|---|
| **all'installazione** | `src/provisiona.sh`: tutte le persone della macchina (`UID_MIN..UID_MAX` letti da `/etc/login.defs`, solo chi ha una shell vera) |
| **in esercizio** | `src/figlio.c`: `iscrivi_ai_gruppi_della_scheda()` — dopo il sì di PAM, prima del `fork`, con `usermod` e il gestore d'utente fatto rinascere. ⚠ `raccogli_gruppi_scheda()` estratta: i nodi si leggono in **un posto solo** |
| ⛔ **e cambia I7** | il prodotto adesso tocca i gruppi, non solo la sessione. Le due garanzie: solo dopo PAM, e ogni iscrizione nel registro |

| `[M]` 20 set 2026, scatola `kde`, utente `senzagr` creato senza gruppi | esito |
|---|---|
| ⛔ binario `836a88b6` (senza la cura) | `id -nG` = «senzagr» · **zero fotogrammi** |
| ⭐ binario `9e3154a6` (la cura) | «PRIMA CONNESSIONE: ce lo metto io» · `id -nG` = «senzagr video render» · **105 fotogrammi consegnati** |
| ⭐ sul server vero, `provisiona.sh` | **3 persone** iscritte · `nicfio` da «nicfio sudo» a «nicfio sudo video render» |

⭐ **E due riparazioni del banco**, trovate dal `pre-push` dell'utente:
1. `11-gancio.sh remoto` passava `--scatola gnome kde` **senza apici**: la metà remota riceveva
   «kde» come comando suo e il giro non partiva;
2. ⛔ e quando non riusciva a lanciare, **aveva già cancellato il log** del giro in corso — che ha
   continuato a scrivere in un file inesistente. ⇒ Adesso guarda PRIMA se l'unità è attiva, e in
   quel caso non tocca niente ed esce 3 dicendolo.
3. `fondamenta/strumenti/sshpw.py` imponeva la password (`PubkeyAuthentication=no`), scritta quando
   un riavvio aveva cancellato la chiave: ⇒ prova la chiave e tiene la password come ripiego.

#### La rete (`[M]` 20 set 2026, 10:02→12:45, binario `9e3154a6`, `--scatola "gnome kde"`)

| | |
|---|---|
| GNOME · **kde** | ⭐ **tutto verde**, nessun rosso · esito remoto **0** |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| ⚠ la delega | il tetto d'attesa di `remoto` è **2 400 s** e la famiglia `tutto` ne vuole ~9 000: la metà locale dichiara «non ha finito entro 2 400 s» mentre di là il giro prosegue e finisce bene. Da allargare quando servirà |

### Incremento 12 — il rosso intermittente, e il muro degli appunti su GNOME

**1. Il rosso intermittente di `07-b54` era del BANCO** (`[M]` 20 set 2026: un giro su tre diceva
«la tastiera è morta dopo il Ctrl+V», i due dopo erano verdi). ⛔ Guardava il registro **una volta
sola**, 2 s dopo la lettera: se la riga arrivava un attimo più tardi, il banco misurava il proprio
ritardo e lo chiamava guasto del prodotto. ⇒ Adesso aspetta fino a 8 s, e si ferma appena la riga
c'è. **Cinque giri di fila verdi.** ⚠ Un rosso intermittente fa spegnere la maglia: è il motivo per
cui non si archivia.

**2. L'arbitro degli appunti per GNOME: `banchi/11-scatole/appunti-gtk.py`** — GTK (`python3-gi`),
cioè `wl_data_device`, la stessa strada delle applicazioni vere, con una finestra presentata perché
su Wayland la clipboard si concede a chi ha il fuoco.

⛔⛔ **E il muro, misurato** (scatola `gnome`, sessione viva, client attaccato):

| chi prova | esito |
|---|---|
| `wl-copy` (senza ucciderlo: resta vivo apposta) | ⛔ il prodotto non vede nessuna copia |
| `wl-paste`, 20 s, anche con `gnome-terminal` aperto | ⛔ resta appeso (uscita 124) |
| `appunti-gtk.py copia` | ⭐ copia **dentro di sé** … ⛔ e nessun altro la vede |
| `appunti-gtk.py incolla` | ⛔ legge vuoto |
| ⭐ il PRODOTTO | consegna i byte e **chiude il tubo** (verificato in `appunti.c`: `close(fd)` prima di `SelectionWriteDone`) |

⇒ Il blocco è **come Mutter concede gli appunti alle applicazioni in una sessione senza seat**:
senza fuoco non li concede, e lì il fuoco non c'è mai davvero. ⚠ Non è un difetto del prodotto e
non è del banco: è la scena. ⇒ C17 su GNOME resta **esito 3, dichiarato**, e gli appunti di GNOME
restano provati a mano (`07-b54`). Si riapre quando si aprirà il lavoro su GNOME.

## Le misure

| che cosa | atteso | misurato | data |
|---|---|---|---|
| **CP0** — giro `tutto` sulle quattro scatole, lanciato **sul server** | GNOME verde; su kde/xfce/lxqt solo C1 rosso; guasti tutti presi; un binario solo | ⭐ **come atteso** — vedi sotto | `[M]` 18 set 2026, 17:25→19:38 |

#### CP0 in dettaglio — binario `bfc5936a2b0f` (sorgenti `src/` di `c82c910`), 7 967 s

| | |
|---|---|
| GNOME | ⭐ **tutto verde**: passo 0, C1×10, C2, C3 (+ scena ferma), C4, C5, C6, C7, C8, C8b, C9 |
| kde · xfce · lxqt | passo 0, C5, C7, C8, C9 verdi · ⛔ **C1×10 ROSSO** su tutte e tre (il mandato) · C2 C3 C4 C6 C8b **saltate** dal cancello «solo gnome» (esito 3) |
| rete, sul server | C11 verde (14 voci allineate, **stesso md5 nelle quattro**) · C13 verde · C14 verde (786 s) |
| rete, sul portatile | C10, C12, C15, C16 verdi, C10 col guasto visto — ⚠ **queste quattro vogliono il deposito git**: lanciate sul server danno 2/3 «il terreno non regge», e non è un rosso. Si fanno girare **qui**, nello stesso giro di certificazione |
| ⭐ **guasti innestati** | **25 su 25 visti** (24 sulle scatole, 1 sul portatile) |
| rossi del banco | nessuno |

⚠ **I conti non si confrontano con quelli del 27 agosto**, e va detto perché sembrano diversi: il
`README.md` dice *«58 verdi, 3 rossi, 49 guasti su 49»*, `fasi/11-…` §7-bis.19 dice *«57 · 23 su 25
· 6 esiti 3 · 3 rossi»* — due conteggi diversi dello **stesso** giro. ⇒ Il confronto che vale è
**la forma**: gli unici rossi sono i tre `C1` fuori da GNOME, **com'era allora**. Oggi: 58 esiti 0
sulle scatole (34 verdetti + 24 guasti visti), 3 rossi, e i guasti presi sono 25 su 25.

## ⛔ Che cosa NON ha funzionato

## Che cosa resta [?]

### Lo schermo che cambia misura a sessione viva — la strada per il futuro (`[R]` 19 set 2026)

Chiesto dall'utente: *«credo che nelle ultime versioni di KWin questo problema sia stato superato»*.
⭐ **In parte sì**: KWin **6.8** (uscita prevista il 14 ottobre 2026) rende **ridimensionabili i
monitor virtuali della cattura** — commit `452707eb` «screencast: Resizable Virtual Monitors» di
David Edmundson, bug KDE 512620, *fixed in 6.8.0*. Il meccanismo è quello di GNOME: la misura si
**rinegozia nel formato PipeWire** fra chi cattura e KWin (con i cambi gemelli in KPipeWire e KRDP).
Prima la misura era fissa a 1920×1080, e rinegoziarla congelava il flusso.

⛔ **Ma per noi non basta da solo, e va detto perché** — due condizioni da verificare quando arriva:
1. **il backend.** Il fix vale per `stream_virtual_output`, cioè per un monitor virtuale CREATO dalla
   cattura. Noi siamo sul backend `--virtual` (una macchina senza seat), e lì `stream_virtual_output`
   **non esiste**: `VirtualBackend` non ridefinisce `createVirtualOutput()` ⇒ «Could not find output»
   (`STUDI.md` §kde, riga di `stream_virtual_output`, verificato). Serve che 6.8 lo aggiunga al
   backend virtuale, oppure che l'uscita `Virtual-0` accetti un modo nuovo (i «modi personalizzati
   per gli schermi virtuali», Plasma 6.6, sono da leggere per questo);
2. **la distribuzione.** Il server ha la KWin di Debian Trixie, **6.3.6**: 6.8 arriva solo con
   una distribuzione nuova o con i backport.

⭐ **E LA PRIMA DELLE DUE CONDIZIONI E' GIA' CADUTA** — `[R]` 20 set 2026, letto nel codice di KWin
(`master`): `VirtualBackend` **dichiara** `createVirtualOutput(const QString &name, const QString
&description, const QSize &size, qreal scale)`, con la stessa firma della base
(`OutputBackend::createVirtualOutput`, virtuale con implementazione predefinita). ⇒ Il «Could not
find output» del backend `--virtual` — che nella 6.3.6 veniva dalla base che tornava `nullptr` —
**su KWin nuovo non c'è più**: anche senza seat si può chiedere uno schermo virtuale alla cattura,
e dalla 6.8 quello schermo si ridimensiona. ⇒ Resta solo la seconda condizione: la **versione**
(Trixie ha la 6.3.6).

⭐ **Dalla nostra parte il lavoro sarebbe piccolo**: `misura_del_palco()` chiede già a KWin la misura
vera e la cattura rinegozia già la misura su GNOME ⇒ si tratterebbe di chiedere la misura nuova
invece di riscalare nella pagina. Fonti: blog KDE «This Week in Plasma: Emoji Resizing» (1 ago
2026), bug KDE 512620.


## Il giudizio dell'utente
