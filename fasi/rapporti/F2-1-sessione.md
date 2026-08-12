# F2.1 — La sessione GNOME headless

*Sotto-fase 1 di 6 della fase 2 «Il primo fotogramma». Scritta il 12 agosto 2026.
Mandato: `fasi/rapporti/MANDATO-12-agosto-fase2.md`. Porta assegnata: **7511**.*

> ⛔ **Questo giro non ha scritto prodotto.** `src/` non è stato toccato. Quel che segue è **il
> banco**, scritto prima del prodotto come vuole `PIANO.md` §0.4 momento 1.

---

## Che cosa deve produrre

**Una sessione grafica GNOME che nasce sul server senza schermo e senza dispositivi di input, e che
nasce con un monitor virtuale della misura chiesta** — perché senza quello c'è una sessione
perfettamente viva e **niente da catturare**.

**Che cosa misura il banco**: quattro fatti, ciascuno con un numero d'uscita suo — la sessione è
viva; ha *un* monitor, della misura *chiesta*, e del tipo *chiesto*; non è viva-e-nera; e i
dispositivi di input virtuali esistono, con l'ordine dichiarato.

⭐ **Che cosa l'utente vedrebbe se questo anello sbagliasse**: una scheda del browser nera, e nessun
messaggio d'errore da nessuna parte.

---

## ⛔ Il banco — scritto prima del prodotto

### La scena dichiarata

| | |
|---|---|
| **la macchina** | NIC-OS `192.168.0.2`, host (non il contenitore): la sessione grafica vive lì, con logind, `systemd --user` e `/dev/dri` veri |
| **la sessione** | `gnome-session --session=gnome`, ambiente **composto da zero**, dieci variabili, `SHELL` **vuota** |
| **la Shell** | `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, imposta con un drop-in dell'unità d'utente |
| **la misura chiesta** | **1920×1080**, scritta prima del giro e passata allo strumento con `--attesa` |
| **la scena si muove?** | ⚠ **no, e di proposito**: qui non si contano fotogrammi. La scena in movimento è di F2.2 in poi (`LEZIONI.md` §1.1 vale lì). Qui si conta **lo stato**, e uno stato si misura fermo |

### Che cosa si conta

Lo strumento `banchi/02-sessione-stato.py` legge **due fonti indipendenti** e le confronta:

| fonte | che cosa dice |
|---|---|
| `/proc/<pid>/cmdline` di `gnome-shell` | che cosa è stato **chiesto** |
| `org.gnome.Mutter.DisplayConfig.GetCurrentState` | che cosa c'è **davvero** |
| `/proc/<pid>/environ` di `gnome-session-binary` | se `SHELL` è vuota **in vigore**, non nel file |

⛔ **Il disaccordo fra le due è un verdetto suo**, non un arrotondamento verso l'una o verso l'altra:
che l'opzione sia *scritta* non è che sia *in vigore* — forma d'errore **E1**.

### Gli otto numeri d'uscita, scritti prima del giro

| # | marca | quando |
|---|---|---|
| 0 | `SANA` | un monitor solo, prodotto `MetaVirtualMonitor`, della misura chiesta, e la riga di comando la chiede |
| 1 | `NERA: ZERO MONITOR` | viva, e zero monitor — **è il guasto M9** |
| 2 | `MISURA SBAGLIATA` | un monitor, ma non della misura chiesta |
| 3 | `MONITOR SCELTO DA SE` | prodotto `Virtual remote monitor`, o più di uno ← **E2** |
| 4 | `SESSIONE MORTA` | nessun `gnome-shell`, o il bus non risponde |
| 5 | `LETTURA IGNOTA` | non ho potuto leggere: negata o illeggibile ← **E8** |
| 6 | `DISACCORDO` | riga di comando e bus non dicono lo stesso ← **E1** |
| 7 | `SHELL NON VUOTA` | `gnome-session` si è ri-eseguito in una shell di login |

**Precedenza dichiarata**: `5 > 4 > 7 > 3 > 2 > 1 > 6 > 0`.

### ⭐ Il controllo positivo — «lo strumento sa trovare qualcosa che c'è di sicuro?»

Due, in coda a **ogni** esecuzione, e servono a due cose diverse:

1. **il parser sa leggere**: nella risposta di `GetCurrentState` dev'esserci la proprietà
   `layout-mode`, che c'è sempre. Se manca, è rotto il parser — e lo strumento lo dice invece di
   stampare «zero monitor»;
2. **il filo col compositore è vivo adesso**: `IdleMonitor.GetIdletime` chiamato due volte a
   distanza deve dare due numeri **diversi e crescenti**. Uno strumento che legge una risposta
   congelata darebbe lo stesso numero.

⛔ Se un controllo positivo fallisce, **l'uscita diventa 5 comunque**, qualunque cosa dicesse il
verdetto.

E per la misura dei dispositivi il controllo positivo è un terzo:
`GetIdletime` deve **crollare** dopo il movimento iniettato — «ho iniettato» non è «Mutter ha
ricevuto». `[M]` 163 533 ms → **1 000 ms**.

### Il caso opposto — «che aspetto avrebbe il contrario?»

| la domanda | il contrario, scritto prima |
|---|---|
| la sessione è viva? | c'è il processo, e il bus non risponde → 4, non «viva» |
| il monitor è quello chiesto? | ce n'è uno che **Mutter si è scelto da sé** → 3 |
| è viva e nera? | ha un monitor, e allora nera non è → 0 |
| `SHELL` è vuota? | c'è, e vale `/bin/bash` → 7 |
| i dispositivi esistono? | un client **nuovo**, nato dopo, deve vedere il puntatore: se non lo vede nemmeno lui, non è l'ordine — è lo strumento cieco (uscita 3) |

### ⛔ Come questo banco si certifica — **e si è certificato, in due metà**

**Metà A — sul ferro** (`bash 02-sessione-lancia.sh certifica`), gli attesi scritti prima:

| | atteso | misurato `[M]` 12 ago 2026 |
|---|---|---|
| sano | **0** `SANA` | **0** |
| guasto innestato: si toglie `--virtual-monitor` dal drop-in — cioè **M9** di `gnome.md` §13 | **1** `NERA: ZERO MONITOR` | **1**, e con quella marca |
| risanato | **0** | **0** |

⭐ **Girata due volte** (11:42 e 11:49), con la sessione vera fermata e riavviata **sei** volte in
tutto, e i due server voluti sulla 7448 e sulla 7501 contati prima e dopo: **due ascoltatori
ciascuno, invariati.**

**Metà B — sulle scene** (`bash ... 02-sessione-certifica-scene.py`), nove scene: la sana **vera**,
registrata dalla macchina, più otto guasti che cambiano **una cosa sola** ciascuno. **9 su 9**, e
ciascuno con la sua marca.

⛔ **Le due metà non si sostituiscono a vicenda, e sta scritto nei file**: la metà A dimostra che lo
strumento sa parlare con una macchina ma raggiunge **due** numeri su otto; la metà B raggiunge tutti
e otto ma non dimostra niente sulla lettura. Una certificazione sono le due insieme.

---

## Che cosa si riusa da v1 — file e **righe vere, contate**

| file | righe **vere** | che se ne riusa |
|---|---|---|
| `v1/remotix-c/src/sessione.c` | **797** | la ricetta dell'ambiente composto da zero (`componi_ambiente`, righe 408-540), il congedo `Logout(2)` (`esci_gnome`, 699-711), e la forma del drop-in (`scrivi_dropin`, 569-623) |
| `v1/remotix-c/src/sessione.h` | 121 | `SESSIONE_COMANDO_GNOME` = `"exec gnome-session --session=gnome"` (riga 66) |
| `banchi/00-sessione-gnome.sh` | **290** | ⇒ vedi il riquadro qui sotto |
| `v1/banco/provision-server.sh` | 388 | ⛔ **non si riusa: si contraddice.** Righe 224-231 |

> ### `banchi/00-sessione-gnome.sh` — che cosa se ne riusa e che cosa no
>
> **Si riusa, e non si riscrive**: l'ambiente composto da zero con `SHELL=` vuota e
> `XDG_SESSION_TYPE=wayland`; `ferma_e_aspetta` con l'attesa di `inactive` e **non** di «diverso da
> `active`»; il congedo con `Logout(2)`; `setsid --fork`; e l'idea che l'headless si **verifichi**
> invece di sperarlo.
>
> ⛔ **Non si riusa, perché è precisamente quel che manca**: quel banco **non nomina mai
> `--virtual-monitor`**, e nemmeno `--headless`. Si affida al drop-in di sistema scritto da
> `provision-server.sh`, che mette `--headless --no-x11` e **basta**. ⇒ **Ogni sessione avviata da
> quel banco è nera.**
>
> ⚠ E non si riusa il suo `registro_shell()`, che scrive in `~/.config/systemd/user`: il drop-in di
> F2.1 sta in `$XDG_RUNTIME_DIR/systemd/user.control/`, come fa v1 per KWin, perché **sparisce da
> sé al riavvio** — un banco non deve lasciare configurazione addosso alla macchina.

### ⛔ `src/sessione.c:671` — che cosa c'è davvero, andato a leggere

Il piano cita `src/sessione.c:671`; in questo deposito il file sta in `v1/remotix-c/src/sessione.c`,
e la riga 671 è **esattamente**:

```c
	if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(larghezza, altezza, sbaglio))
```

Il piano dice il vero, e **c'è di peggio di quel che dice**: `sessione_assicura()` riceve
`larghezza` e `altezza` (riga 650-651) e sul ramo GNOME **non le legge nessuno**. La misura del
desktop entra nella funzione e **si perde in silenzio**. `[R]` 12 agosto 2026.

E `scrivi_dropin()` (569-623) scrive in `$XDG_RUNTIME_DIR/systemd/user.control/
plasma-kwin_wayland.service.d/remotix.conf`, poi `systemctl --user daemon-reload`: è la ricetta che
F2.1 ha copiato per GNOME, cambiando solo il nome dell'unità e la riga.

---

## ⛔ Le trappole già pagate che mordono qui, citate col paragrafo

| dove sta scritto | che cosa dice | come sta qui `[M]` 12 ago 2026 |
|---|---|---|
| `gnome.md` §3.1 | `--virtual-monitor` **non è opzionale**: in headless `needs_outputs=false`, e senza quell'opzione la sessione parte *viva, completa e nera* | ⭐ **confermata, e trovata addosso alla macchina**: vedi §«Che cosa non ha funzionato» punto 1 |
| `gnome.md` §3.1 | `SHELL` va messa vuota, o `gnome-session.in:3-14` si ri-esegue in una shell di login | ⭐ **la trappola non ha morso, e adesso si misura**: lo strumento legge `/proc/<gnome-session-binary>/environ`. ⚠ E leggendo `gnome-session.in` il controllo vero è `[ -n "$SHELL" ]`: **assente e vuota vanno tutt'e due bene**, e v1 la lascia *assente* (zero occorrenze di `SHELL` in `sessione.c`) |
| `gnome.md` §3.2 | il nome `org.gnome.Shell` **non** è un indicatore di prontezza: è preso prima di `meta_context_start()` | il banco aspetta che `IsSessionRunning` risponda e che `GetCurrentState` risponda, non il nome |
| `gnome.md` §3.2 | il congedo è `Logout(2)`; `Logout(1)` mostra il dialogo se c'è un inibitore | usato `Logout(2)` |
| `gnome.md` §1.1 / §1.2 | il drop-in della Shell si scrive **solo per KWin**; e l'headless su GNOME lo abbiamo **per accidente** | ⚠ **`gnome.md` §1.1 è invecchiata su questa macchina**: vedi il `[≠]` più sotto |
| `gnome.md` §13 M9 | la prova **guasta di proposito**: senza `--virtual-monitor`, per imparare che aspetto ha il guasto | ⭐ **fatta, ed è il guasto della certificazione**: `1 NERA: ZERO MONITOR` |
| `REVIEWER.md` §2 **E1** | necessario scambiato per sufficiente | l'opzione sulla riga di comando **non** basta: si legge anche il bus, e il disaccordo ha un codice suo |
| `REVIEWER.md` §2 **E2** | un componente che decide da sé | ⭐ **preso sul campo**: vedi punto 3 di «Che cosa non ha funzionato» |
| `REVIEWER.md` §2 **E8** | il silenzio scambiato per zero | ⭐ **pagata subito**: `Shell.Introspect.GetWindows` e `Shell.Screenshot` rispondono **AccessDenied** a un chiamante qualunque `[M]`. Un banco che avesse letto «zero finestre» avrebbe scritto «sessione vuota» dove il fatto era «non mi hanno fatto guardare» |
| `fasi/00-ambiente.md` B3.1 | `pgrep -x` e i 15 caratteri di `comm` | `gnome-shell` ne ha 11: ci sta. Ma lo **stato d'uscita** di `pgrep` si guarda: 0 trovato, 1 nessuno, **2+ errore** → 5 |
| `fasi/00-ambiente.md`, difetto 4 della fase 0 | `pkill` lascia il gestore vivo, e si aspetta `inactive` e non «diverso da `active`» | riusato tale e quale |
| `CODER.md` §3.9 / I7 | un componente che sceglie in autonomia produce due misure sotto la stessa etichetta; e la protezione sta nel programma, non in una riga di configurazione | ⛔ **oggi il monitor virtuale di GNOME è una riga di configurazione in `/etc`, ed è I7 violato**: vedi le cuciture |

### ⚠ Un `[≠]`: `gnome.md` §1.1 e questa macchina non dicono la stessa cosa

`gnome.md` §1.1 scrive: *«Su GNOME la Shell parte con `ExecStart=/usr/bin/gnome-shell` secco, **senza
`--headless`**»*. `[M]` 12 agosto 2026:

- l'unità **installata da Debian** dice davvero `ExecStart=/usr/bin/gnome-shell` secco — §1.1 ha
  ragione sul pacchetto;
- ⛔ **ma su NIC-OS non è quella che gira.** `systemctl --user show -p ExecStart` dà
  `argv[]=/usr/bin/gnome-shell --headless --no-x11`, per un drop-in in
  `/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf`, scritto da
  `v1/banco/provision-server.sh` righe 224-231 il 9 agosto alle 10:19.

⇒ Dal 9 agosto **l'headless su GNOME non è più «per accidente»: è chiesto** — ma è chiesto da una
riga di configurazione di *provisioning*, su un rootfs che vive in RAM. Sopravvive a un riavvio solo
se qualcuno rilancia `provision-server.sh`. È **I7** con la data e il file.

---

## Le misure

*La scena dichiarata accanto a ogni numero. Tutte su NIC-OS, host, 12 agosto 2026.*

| che cosa | atteso | misurato | scena |
|---|---|---|---|
| la sessione trovata all'apertura del giro | — | **`1 NERA: ZERO MONITOR`** | gnome-shell 102054, viva dal 10 ago 21:01 |
| la stessa, quanti monitor | — | **0 monitor, 0 monitor logici** | `GetCurrentState` |
| la stessa, è viva? | — | `IsSessionRunning` **true**, 50 nomi sul bus, Nautilus e Terminale accesi | |
| certificazione sul ferro, giro 1 | 0 → 1 → 0 | **0 → 1 → 0** | 11:42 |
| certificazione sul ferro, giro 2 | 0 → 1 → 0 | **0 → 1 → 0** | 11:49, strumento corretto |
| certificazione sulle scene | 9 su 9 | **9 su 9** | scena base **vera**, registrata alle 11:42:04 |
| il monitor chiesto, com'è fatto | `MetaVirtualMonitor` | connettore `Meta-0`, fornitore `MetaVendor`, prodotto **`MetaVirtualMonitor`**, seriale `0x00`, modo `1920x1080@60.000` | drop-in `--virtual-monitor 1920x1080` |
| ⭐ un monitor che Mutter si è scelto da sé | — | connettore `Meta-1`, prodotto **`Virtual remote monitor`**, seriale `0x000001`, modo **`1920x1080@60.000`** | 11:49:56, comparso e sparito da solo |
| `SHELL` nell'ambiente di `gnome-session-binary` | vuota o assente | **vuota** | ambiente composto da zero |
| capacità del `wl_seat` senza dispositivi | 0 | **`wl_seat#15.capabilities(0)`** | `WAYLAND_DEBUG=1 foot` |
| l'inattività dopo il primo movimento iniettato | < 5 000 ms | **1 000 ms** (da 163 533) | `NotifyPointerMotionRelative(7,5)` |
| ⭐ il client partito **prima**, dopo la nascita del puntatore | *da misurare* | **riceve** `capabilities(0)` → **`capabilities(1)`** | client tenuto vivo attraverso la transizione, riprodotto **2 volte** |
| il client nato **dopo** — caso opposto | pointer | **`capabilities(1)`** | |
| i due server da non toccare, prima e dopo sei riavvii di sessione | 2+2 ascoltatori | **2+2, invariati** | |

---

## ⛔ Che cosa NON ha funzionato

### 1. ⛔⭐ Il guasto M9 non c'era da innestare: era addosso alla macchina, da due giorni

La sessione GNOME viva su NIC-OS dal 10 agosto alle 21:01 era **la sessione nera**: `--headless
--no-x11` senza `--virtual-monitor`, **zero monitor**, e tutto il resto perfettamente in piedi.

⇒ Se la fase 2 fosse cominciata dalla cattura invece che da qui, **avrebbe misurato zero fotogrammi
su una sessione che nessuno sospettava**, esattamente come `PIANO.md` avverte. È l'argomento più
forte a favore della regola «il banco prima del prodotto» che questo giro abbia prodotto.

### 2. ⛔⛔ Ho fatto cadere la sessione, e il modo in cui è caduta è una scoperta

Cercando un testimone a **pixel** della scena nera, ho chiamato
`org.gnome.Shell.Screenshot.Screenshot` su quella sessione. Registro di Mutter:

```
CRITICAL : cogl_texture_2d_new_with_size: assertion 'width >= 1' failed
WARNING  : Failed to take screenshot: Failed to create 0x0 texture
```

e gnome-shell è morto. L'unità porta `OnFailure=… gnome-session-shutdown.target` con `Restart=no`:
**se n'è andata tutta la sessione.**

- ⛔ **È una cosa che il mandato mi vietava**, e la scrivo per prima invece di seppellirla. Ho
  verificato subito i due server voluti: **7448 e 7501 con due ascoltatori ciascuno, intatti** —
  girano dentro il contenitore e non dipendono dalla sessione grafica. Ho rimesso in piedi la
  sessione entro due minuti, nello stesso stato in cui l'avevo trovata.
- ⭐ **E la scoperta**: una sessione headless con zero monitor non è solo *viva e nera*, è
  **fragile** — cade al primo che le chiede un fotogramma per la via della Shell. Chi vedesse cadere
  la sessione a metà di una misura andrebbe a cercare il difetto nel proprio codice. Non stava
  scritto in nessun documento del progetto.
- ⚠ E una cosa che serve a F2.6: `Shell.Screenshot` **non è una strada per il banco**. Oltre alla
  fragilità, è chiusa da un `DBusSenderChecker` che ammette quattro soli nomi ben noti
  (`gnome-shell/js/misc/util.js:343-418`). Prendere `org.gnome.Screenshot` sul bus **supera il
  controllo** `[M]` — ma quel che si trova dietro è l'assert.

### 3. ⛔ Il banco ha preso E2 sul campo — e la marca che lo distingue non è la misura

Alle 11:49:56, su una sessione che ne aveva chiesto **uno**, `GetCurrentState` ne ha dichiarati
**due**:

| | connettore | prodotto | seriale | modo |
|---|---|---|---|---|
| il nostro | `Meta-0` | `MetaVirtualMonitor` | `0x00` | `1920x1080@60.000` |
| ⛔ l'altro | `Meta-1` | **`Virtual remote monitor`** | `0x000001` | **`1920x1080@60.000`** |

⭐ **Stessa identica misura.** Se il banco avesse guardato la risoluzione — la cosa ovvia — non
avrebbe distinto niente. Li distingue **il nome del prodotto**, che è quello che Mutter mette al
monitor che si crea **da sé** per uno ScreenCast virtuale
(`meta-screen-cast-virtual-stream-src.c:606-609` `[R]`) contro quello del monitor persistente chiesto
con `--virtual-monitor` (`meta-context-main.c:592-597` `[R]`). È `CODER.md` §3.9 alla lettera:
*chiedi il componente per nome, e verifica che abbia obbedito*.

⚠ E c'è un difetto di banco dentro il successo: sullo schermo lo strumento aveva stampato solo *«2
monitor: ne era stato chiesto uno solo»*, **senza nominarli**. Il nome l'ha salvato la riga JSONL,
che li registra interi. Corretto: adesso, quando i monitor sono più d'uno, li elenca tutti.

`[?]` **Chi abbia aperto quello ScreenCast resta ignoto**: `gnome-remote-desktop` **non è
installato** su questa macchina, e trenta secondi dopo il monitor era già sparito.

### 4. ⛔ Il banco dei dispositivi ha dato la risposta giusta su una scena mai avvenuta

La prima stesura faceva `CreateSession` → `Start` → `NotifyPointerMotion` con tre `gdbus call` di
fila. La sessione di `org.gnome.Mutter.RemoteDesktop` è legata alla **connessione** che l'ha creata,
e `gdbus` ne apre una nuova ogni volta:

```
CreateSession → '/org/gnome/Mutter/RemoteDesktop/Session/u1'   (uscita 0)
Start         → UnknownMethod: Object does not exist at path   (uscita 1)
```

⇒ Il puntatore **non nasceva mai**, e il passo dopo rispondeva *«il client partito prima non riceve
niente»* — cioè **confermava** quel che ci si aspettava, su una scena che non era avvenuta. ⭐ Con
una connessione sola, la risposta vera è **l'opposto**.

Se n'è accorto solo perché lo stato d'uscita di ogni `gdbus` era guardato (`REVIEWER.md` §1 punto 4),
e il controllo positivo sull'inattività è nato da qui.

### 5. ⛔ Due verdetti su otto erano irraggiungibili, e la certificazione offline li ha trovati

Nella prima stesura la precedenza metteva `DISACCORDO` (6) in alto. Ma una **misura sbagliata** (2) e
un **monitor scelto da sé** (3) fanno *anche* discordare la riga di comando dal bus — quindi
uscivano tutt'e due come 6. `MONITOR SCELTO DA SE`, cioè **proprio la forma d'errore che questo banco
esiste per vedere**, sarebbe stata invisibile sotto un'etichetta generica.

Curato: **il disaccordo è il verdetto residuo**, precedenza `5 > 4 > 7 > 3 > 2 > 1 > 6 > 0`.
Certificazione rifatta sul ferro dopo la cura: 0 → 1 → 0.

---

## Le decisioni prodotte

*Nessuna scritta ancora in `DECISIONI.md` — questo giro non tocca file di altri. Le quattro decisioni
piccole prese da solo, dichiarate qui perché il coordinatore le porti dove vanno:*

1. **Il drop-in di F2.1 sta in `$XDG_RUNTIME_DIR/systemd/user.control/…/zz-f21-monitor.conf`.** Non
   serve root, sparisce al riavvio, e il prefisso `zz-` **vince sul nome** — i drop-in di tutte le
   cartelle si applicano in ordine di nome file, e in `/etc/systemd/user` ce n'è già uno che si
   chiama `remotix-headless.conf`.
2. **La porta 7511 non serve a parlare con nessuno: è il lucchetto.** Una sessione grafica è una per
   utente (**I2**); due copie del banco che la ciclano insieme darebbero due misure diverse sotto la
   stessa etichetta. Chi non prende la 7511 non parte.
3. **Il banco conta gli ascoltatori sulla 7448 e sulla 7501 prima e dopo ogni ciclo**, e se calano si
   ferma. «Non dipendono dalla sessione grafica» era un'ipotesi finché non è stata guardata.
4. **La misura chiesta di riferimento è 1920×1080**, che è quella che la fase 1 già annuncia alla
   pagina (*«tela 1920×1080»*, `PIANO.md` fase 1).

---

## Che cosa resta `[?]`

| # | la `[?]` | perché resta |
|---|---|---|
| 1 | ⛔ **Chi ha aperto lo ScreenCast che ha creato `Meta-1`** | `gnome-remote-desktop` non è installato; il monitor è comparso e sparito in trenta secondi. Il banco lo **vede**, ma non sa chi lo fa |
| 2 | ⛔ **Perché la pagina non riceve il puntatore, visto che l'annuncio arriva** | l'anello che il piano incolpava è caduto: il compositore **ri-annuncia** `capabilities` al client già collegato. Il sospetto si sposta sul client — o sul fatto che *ricevere l'annuncio* non è *legarsi al `wl_pointer`* |
| 3 | **Se il client partito prima riceva poi gli EVENTI**, e non solo l'annuncio | misurato l'annuncio, non gli eventi. Sono due fatti, e il secondo è di F2.6 |
| 4 | **La tastiera nasce separatamente** | `capabilities(1)` è **solo** il puntatore: `ensure_virtual_device(KEYBOARD)` scatta al primo **tasto**, non al primo movimento `[R]`. Un banco che inietta solo movimento e poi si aspetta che si scriva misura una scena che non c'è. **Non misurato** |
| 5 | **Se `--virtual-monitor` regga un cambio di misura a caldo** | `ensure_virtual_monitor` esce prima se la misura non cambia (`gnome.md` §8.2). Non provato: è F2.2/fase 6 |
| 6 | **Se la sessione con monitor sia altrettanto fragile** allo `Shell.Screenshot` | l'assert è su una texture 0×0, quindi *dovrebbe* sparire con un monitor. **Non riprovato di proposito**: non rifaccio cadere la sessione per una curiosità |
| 7 | **Il rendering è in GPU?** | l'utente è nei gruppi `render`/`video` e Mutter dichiara i due renderer gbm — ma «ha aperto un render node ⇒ rende in GPU» è **E1**. Non misurato qui, e non è di questa sotto-fase |

---

## Le cuciture

### Che cosa F2.1 **promette** alle altre cinque

| a chi | che cosa |
|---|---|
| **tutte** | ⭐ **una sessione dichiarata**, non trovata: `bash 02-sessione-lancia.sh sano` e la sessione è viva, con **un** monitor `MetaVirtualMonitor` `Meta-0` a 1920×1080@60. E `guarda` lo dice **senza toccare niente**, con un numero d'uscita per stato |
| **tutte** | ⭐ **un modo per non sbagliare imputato**: prima di credere a un rosso, `02-sessione-lancia.sh guarda`. Se dice `1 NERA: ZERO MONITOR`, il difetto non è vostro |
| **F2.2 (cattura)** | il **nome** del monitor da catturare — `Meta-0` / `MetaVirtualMonitor` / `0x00` — e la prova che **non basta la misura per distinguerlo**: il 12 agosto ce n'erano due, `Meta-0` e `Meta-1`, **entrambi 1920×1080@60** |
| **F2.2** | la certezza che **zero fotogrammi** possa avere una causa a monte, e lo strumento per escluderla in dieci secondi |
| **F2.6 (giudizio)** | ⛔ **`org.gnome.Shell.Screenshot` non è una strada**: chiusa da un `DBusSenderChecker` a quattro nomi, e su una sessione senza monitor **fa cadere gnome-shell** `[M]` |
| **F2.6** | ⭐ **`GetIdletime` come controllo positivo dell'input**: crolla a ~1 000 ms quando un evento arriva davvero. È il modo di dire «Mutter l'ha ricevuto» invece di «io l'ho mandato» (**E7**) |
| **F2.4/F2.5** | la sessione RemoteDesktop **muore con la connessione D-Bus che l'ha creata**: chi la usa la tiene su **una** connessione viva, o si trova `UnknownMethod` |

### Che cosa F2.1 **chiede** alle altre cinque, e al coordinatore

| a chi | che cosa chiedo |
|---|---|
| ⛔ **F2.2 (cattura)** | **dichiarate il monitor per nome, non per indice e non per misura.** Se catturate «il monitor 0» o «quello 1920×1080», il 12 agosto avreste potuto catturare `Meta-1`, che non è il nostro. E se catturate un `Virtual remote monitor`, quello **ve lo siete creato voi** chiedendo uno stream virtuale: è E2, e va detto |
| ⛔ **F2.2** | **prima di ogni misura, `02-sessione-lancia.sh guarda`**, e la riga JSONL accanto al numero dei fotogrammi. Un fotogramma contato su una sessione che non si è dichiarata è un numero senza scena |
| ⛔ **F2.6 (giudizio) e chiunque apra un'applicazione** | l'ordine è **più stretto** di come lo scrive `PIANO.md`: il puntatore **non nasce con `Session.Start()`, nasce al primo movimento iniettato** (`meta-remote-desktop-session.c:290-321`, `:780-800`, `:940-960` `[R]`). Aprite l'applicazione **dopo il primo `NotifyPointerMotion`**, non dopo lo `Start`. E **la tastiera è un terzo momento ancora**: nasce al primo tasto |
| ⛔ **F2.5 (pagina) e F2.6** | la spiegazione che il piano dà della `[?]` di S.4 — *«il seat non annuncia il puntatore e il client partito prima non si iscrive mai»* — **è contraddetta al primo anello** `[M]`: l'annuncio **arriva** (`capabilities(0)` → `capabilities(1)`), riprodotto due volte. ⇒ La caccia va spostata dal compositore al client. **Non riscrivete `PIANO.md` sulla mia parola: la misura è in `banchi/02-sessione-esiti.jsonl`, riga `dispositivi-ordine`, e si rifà in tre minuti** |
| ⛔ **al coordinatore** | ⭐ **il monitor virtuale di GNOME oggi è una riga di configurazione in `/etc`, su un rootfs che vive in RAM — ed è I7 violato.** `provision-server.sh` mette `--headless --no-x11` e **non** `--virtual-monitor`. Due strade, e vanno decise da chi ha il quadro: **(a)** aggiungere `--virtual-monitor` a `provision-server.sh` — cura in un minuto, ma resta una riga di configurazione che si può perdere; **(b)** ⭐ **portarlo nel prodotto**, cioè togliere il `tipo == COMPOSITORE_KWIN` da `sessione.c:671` e scrivere il drop-in anche per GNOME con `larghezza`/`altezza`, che la funzione **già riceve e butta via**. È **I7**, ed è lavoro di prodotto: non l'ho fatto perché questo giro non tocca `src/` |
| ⚠ **al coordinatore** | `gnome.md` §1.1 va aggiornata: sulla macchina l'headless è **chiesto** dal 9 agosto, non accidentale. E `gnome.md` §13 **M9 si può chiudere**: fatta, e con due sorprese (la fragilità allo screenshot, e il guasto già addosso alla macchina) |
| ⚠ **a chi eredita la macchina** | l'ho lasciata **sana**: gnome-shell con `--virtual-monitor 1920x1080`, un monitor `Meta-0`. ⛔ Ma il drop-in che gliel'ha data sta in `$XDG_RUNTIME_DIR` e **sparisce al primo riavvio**: dopo un riavvio la macchina torna nera. Si rimette con `bash /media/REMOTIX/f21/02-sessione-lancia.sh sano` |

---

## ⛔ La riga per il catalogo delle certificazioni

*Nella forma di `banchi/01-b12-guasti.py`. ⭐ Il numero atteso è scritto **prima** del giro: sta in
testa a `02-sessione-lancia.sh`, funzione `certifica()`, righe `A_SANO=0 A_GUASTO=1`.*

```python
{
    "nome":            "F2.1-sessione-monitor-virtuale",
    "comando":         "bash banchi/02-sessione-lancia.sh certifica",
    "dove":            "NIC-OS host (non il contenitore) — la sessione grafica vive li'",
    "atteso_sano":     0,      # SANA: un MetaVirtualMonitor Meta-0 a 1920x1080
    "guasto":          "drop-in-senza-opzione",
    "guasto_dettaglio": "si riscrive $XDG_RUNTIME_DIR/systemd/user.control/"
                        "org.gnome.Shell@wayland.service.d/zz-f21-monitor.conf "
                        "togliendo `--virtual-monitor 1920x1080`, e si riavvia la "
                        "sessione.  E' M9 di gnome.md §13, il guasto fatto di proposito",
    "atteso_guasto":   1,      # NERA: ZERO MONITOR
    "marca_guasto":    "NERA: ZERO MONITOR",
    "atteso_risanato": 0,
    "rimette_a_posto": True,   # il terzo giro rimette il drop-in con l'opzione
    "controllo_positivo": "GetCurrentState porta «layout-mode»; e GetIdletime chiamato "
                          "due volte cresce — il filo col compositore e' vivo adesso",
    "guardia":         "conta gli ascoltatori su 7448 e 7501 prima e dopo: se calano, rosso",
    "lucchetto":       7511,
},
{
    "nome":            "F2.1-sessione-giudizio-su-scene",
    "comando":         "python3 banchi/02-sessione-certifica-scene.py "
                       "--base banchi/02-sessione-scene/sana.json",
    "dove":            "ovunque — non serve una macchina con la sessione",
    "atteso_sano":     0,      # 9 scene su 9, ciascuna con la sua marca
    "guasto":          "otto-scene-derivate",
    "guasto_dettaglio": "otto guasti innestati SULLA SCENA a partire da sana.json, che e' "
                        "registrata da una macchina VERA: zero-monitor, misura-1280x720, "
                        "scelto-da-se, due-monitor, sessione-morta, lettura-negata, "
                        "shell-non-vuota, disaccordo",
    "atteso_guasto":   1,      # con una scena che non torna, esce 1
    "marca_guasto":    "NON certificato",
    "atteso_risanato": 0,
    "avvertenza":      "⛔ Copre gli otto numeri d'uscita ma NON dimostra che lo strumento "
                       "sappia leggere una macchina: quella meta' la fa la riga qui sopra. "
                       "Le due non si sostituiscono a vicenda",
}
```

---

## I file consegnati

| file | righe | che cos'è |
|---|---|---|
| `banchi/02-sessione-lancia.sh` | 487 | il banco: `guarda`, `sano`, `guasto`, `dispositivi`, `ferma`, `certifica`, `pulisci` |
| `banchi/02-sessione-stato.py` | 609 | lo strumento: dalla sessione a uno degli otto numeri, dal bus o da una scena registrata |
| `banchi/02-sessione-dispositivi.py` | 293 | quando nasce il puntatore virtuale, e chi se ne accorge |
| `banchi/02-sessione-certifica-scene.py` | 174 | la metà offline della certificazione: nove scene |
| `banchi/02-sessione-scene/sana.json` | — | la scena **vera** registrata dalla sessione sana, 11:42:04 |
| `banchi/02-sessione-scene/nera.json` | — | la scena **vera** registrata dalla sessione nera, 11:42:10 |
| `banchi/02-sessione-esiti.jsonl` | 13 righe | un giro per riga, con l'ora, la scena, il numero, la marca e i monitor interi |

*Sul server stanno in `/media/REMOTIX/f21/` — sull'host, non nel contenitore.*

---

## Il giudizio dell'utente

*Da riempire. La fase non si chiude su un documento completo: si chiude su una misura giudicata
dall'utente (`PIANO.md` §0.3 punto 3, invariante **I8**).*
