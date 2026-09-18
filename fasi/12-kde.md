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

## Il giudizio dell'utente
