# Fase 13 — XFCE

*Aperta il **20 settembre 2026**. Chiusa il —*

## Che cosa deve produrre

Il terzo desktop: **la stessa cosa su XFCE** (`PIANO.md` fase 13). L'utente apre il browser e vede
il suo desktop XFCE, come oggi vede GNOME e Plasma.

⛔ **La regola della fase, dell'utente, 20 settembre 2026**: *«aggiungere XFCE a REMOTIX senza
perdere nessuna capacità già certificata di GNOME e KDE»*. ⇒ **Da oggi il baseline protetto sono
due**: una regressione di KDE vale quanto una di GNOME. KDE esce dal cantiere ed entra nel
guardiano.

Si procede per **incrementi**, e ogni incremento attraversa gli stessi cancelli della fase 12:

| | |
|---|---|
| **CP0** | la baseline: rete completa sulle **quattro** scatole, stesso binario ovunque |
| **CP1** | l'incremento è definito: obiettivo, invariante, moduli, prova XFCE, prova client, regressioni GNOME **e KDE** da guardare, criterio |
| **CP2** | GNOME, KDE e XFCE **osservati** sul punto dell'incremento, e la differenza scritta — niente dedotto |
| **CP3** | la modifica minima progettata: file, perché, che cosa di GNOME e di KDE resta com'è |
| **CP4** | la prova XFCE fatta davvero, sulla scena dichiarata |
| **client** | Chrome e Firefox su Linux, Chrome sull'emulatore Android — quando l'incremento tocca il percorso |
| **rete** | la rete completa, GNOME **e KDE** invariati, i guasti innestati ancora presi |
| **checkpoint** | un commit che si può riprendere |

⇒ Un rosso su GNOME o su KDE è **una regressione finché non è dimostrato il contrario**, e si
classifica: A regressione vera · B assunzione di un desktop nel codice comune · C difetto del banco
· D invariante sbagliato (⛔ mai come scorciatoia).

---

## ⭐ La differenza che cambia la forma della fase

GNOME ha Mutter, KDE ha KWin. ⛔ **XFCE non ha un compositore proprio**: su Wayland si appoggia a
**labwc**, che è **wlroots** — la terza e ultima famiglia. ⇒ La fase 13 non è «un terzo ramo come il
secondo»: due pezzi del prodotto **non si riusano affatto**.

| pezzo | GNOME e KDE, oggi | XFCE (wlroots) | costo |
|---|---|---|---|
| **appunti** | `src/appunti_kde.c`, `zwlr_data_control` | ⭐ **quasi gratis**: quel file si chiama «kde» ma parla **già** il protocollo di wlroots (`src/appunti_kde.h:6-10`) | piccolo |
| **riconoscimento** | `riconosci_desktop()`, `src/sessione.c:275-303` | terzo valore dell'enum, in **coda** (viaggia come `uint32_t` fra figlio e padre) | piccolo |
| **sessione** | due rami in `sessione.c` | ~14 punti; ⛔ e `scrivi_dropin()` **non ha oggetto**: su XFCE il compositore non è un'unità systemd | medio |
| **cattura** | PipeWire che **spinge** i fotogrammi | ⛔ `zwlr_screencopy_manager_v1`, modello **a tiro**: un fotogramma per richiesta, niente PipeWire, niente D-Bus | grosso |
| **input** | **libei** (`ConnectToEIS`) | ⛔ libei **non esiste** su wlroots (`STUDI.md` §xfce §7, verifica per assenza con controllo positivo). `zwp_virtual_keyboard` + `zwlr_virtual_pointer`, e i **modificatori** vanno scritti da zero | il più grosso |

⭐ **E lo studio è già fatto**: `STUDI.md`, sezione «XFCE, labwc e wlroots» (857 righe, §1-§15), con
le quattordici domande di `LEZIONI.md` §3 già riempite, undici misure d'apertura (M1-M11) e cinque
scelte da mettere davanti all'utente. ⛔ Si legge **prima** di riaprirne una.

---

## Le decisioni prodotte

- **20 settembre 2026, dell'utente**: *«allo stato attuale remotix e' destinato a sistemi con un
  solo DE installato. I sistemi con DE multipli installato sono per il momento fuori scope»* ⇒
  `DECISIONI.md` **§0.6**, che allarga §4.6-duodetricies. ⭐ Il riconoscimento resta semplice: si
  cerca il desktop che c'è, non si arbitra fra desktop che convivono, e ⛔ l'opzione `--compositore`
  di v1 **non si rimette**.
- **20 settembre 2026, dell'utente**: la fase si lavora *«in silenzio»*, con un aggiornamento
  indicativamente ogni mezz'ora, e si interrompe solo per checkpoint, regressione, blocco,
  decisione o milestone.
- ⇒ **Cade la decisione del 19 settembre** *«togli XFCE e LXQt»* (`fasi/12-kde.md:45-48`): le quattro
  scatole rientrano nei giri. ⭐ Non c'è niente da cambiare nel gancio per ottenerlo — il predefinito
  è **già** `DESKTOP_NOTI="gnome kde xfce lxqt"` (`11-gancio.sh:240`) e il `pre-push` non passa
  `--scatola`: bastava smettere di passarlo a mano.
- **LXQt resta fuori dal cantiere**, e può restare rossa per le capacità non implementate. ⚠ Ma è
  della **stessa famiglia** di XFCE (labwc/wlroots, `adattatore.lxqt.sh` è identico a quello xfce)
  ⇒ quasi tutto quel che si scrive qui la serve, e la fase 14 sarà corta.

---

## Il banco — che cosa va toccato, e si dichiara prima di toccarlo

Il banco è **la rete della fase 11** (`banchi/11-scatole/`), puntata sulla scatola `xfce`. Il segno
che XFCE è servito è quello già scritto: **`C1(xfce)` diventa verde**, e dopo di lei C2, C3, C4, C6,
C7, C8b, C9, C17 sulla stessa scatola.

Letture del 20 settembre 2026, `[R]`:

1. ⛔ **Il cancello a due nomi**, `11-gancio.sh:809-813` (`le_cinque_nuove`): *«il prodotto sa
   avviare solo GNOME e KDE»*. ⚠ Salta **15 esecuzioni**, non cinque — C2×3, C3×4, C4×3, C6×2,
   C8b×2 **e C17×2**, perché le due chiamate di C17 (`:863-864`) stanno **dopo** il `return`. ⇒ E
   C17 viene saltata **senza essere nominata** nel registro: la riga si chiama ancora
   `"C2($d) C3 C4 C6 C8b"`. Il commento di `:856-862` — *«Nessun cancello per desktop QUI»* — è
   falso per quel punto di chiamata.
2. ⛔ **Il gemello disallineato**, `11-accendi.sh:557-560`: stessa whitelist, ma copre **solo C8b**.
   ⇒ Due posti da aprire; aprendone uno solo, C8b(xfce) resta muta a 3.
3. ⛔ **La scatola `xfce` non contiene XFCE**: `Contenitore.xfce` installa `labwc xfce4-session
   xwayland`, ⛔ ma **né `xfce4-panel` né `xfdesktop`** — una sessione che nasce lì dentro non ha
   pannello né scrivania. ⇒ La scatola cresce, come `Contenitore.kde` è cresciuta (R5).
4. ⛔ **E l'adattatore non avvia una sessione XFCE**: `adattatore.xfce.sh:32-43` lancia `labwc`
   **nudo** — niente `--session xfce4-session`, niente `XFCE4_SESSION_COMPOSITOR`. ⇒ Oggi quel banco
   misura **un compositore**, non un desktop, e in particolare non può far scattare la trappola del
   logout (§9.2 dello studio).
5. ⛔ **Gli attrezzi degli appunti mancano** nella scatola xfce (e lxqt): niente `wl-clipboard`,
   niente `python3-gi gir1.2-gtk-4.0` — che kde e gnome hanno. ⚠ E ⛔ **il banco non lo dice**:
   `11-c17:150` prende `stdout` senza guardare il codice d'uscita, quindi `wl-paste: command not
   found` diventa `""`, la guardia di `:242` (che controlla `None`) non scatta, e la maglia stampa
   **ROSSO** invece di «non ho potuto guardare». ⛔ Un attrezzo che manca deve dare 3.
6. ~~⚠ **C1 dice la causa sbagliata**: su xfce esce *«nata CIECA»* mentre il fatto è *«mai nata,
   perché il prodotto cercava `gnome-session`»*.~~ ✅ **CHIUSA dall'incremento 1, e senza toccare
   il banco.** ⭐ La diagnosi era falsa perché lo era il prodotto: adesso la sessione **nasce
   davvero** e l'immagine non c'è, quindi *«nata cieca»* è esatta alla lettera. ⇒ Era un difetto
   del prodotto travestito da difetto del banco — e il modo di scoprirlo è stato curare il
   prodotto, non ritarare la maglia.
7. ⚠ **C7(xfce) oggi è verde in parte a vuoto**, e il banco lo stampa (`11-c7:1184-1204`): la voce
   `/dev/dri` è vuota in tutt'e tre le impronte *«perché senza compositore nessuno apre la scheda»*.
   ⇒ Il giorno che XFCE si accende, C7 diventa **più severa** — e può diventare rossa per ragioni
   vere.
8. ⚠ **C11 non vedrebbe** l'aggiunta di `wl-clipboard`/`python3-gi` alla sola xfce: non sono nella
   sua lista di pacchetti. ⇒ O si mettono in **tutte e quattro**, o si aggiungono alla lista.
9. ⚠ **La famiglia `desktop-nuovo` non scatterà mai da sola** per xfce: `decidi_famiglia`
   (`11-gancio.sh:345-357`) riconosce un desktop nuovo solo da un `Contenitore.*` **non presente**
   in `DESKTOP_NOTI`, e xfce c'è già. ⇒ Va chiesta per nome.
10. ⚠ **Dieci commenti scaduti** dicono ancora *«solo gnome»* o *«il prodotto ne sa accendere UNO»*
    (`11-gancio.sh:203-205`, `:1300-1307`, `:774` · `11-accendi.sh:23-24`, `:498`, `:511`, `:522`,
    `:533` · `11-c8b:56-59` · `11-c15:114-116`). ⛔ Sono quelli che uno legge **prima** di provare
    su xfce.
11. ⭐ **Un guasto di XFCE, inventato e fatto girare** (`fasi/11-…` §3.6): oggi non esiste, come non
    esisteva quello di KDE.

⛔ **Aprire i cancelli non ammorbidisce nessun giudizio**: è la condizione perché le maglie guardino
XFCE. Si aprono nell'incremento in cui la maglia corrispondente **può** diventare verde, non prima.

---

## Gli incrementi

| # | obiettivo | maglia che lo prova | stato |
|---|---|---|---|
| **0** | la baseline sulle **quattro** scatole | la rete intera | ✅ **PASS** 20 set — 32 guasti su 32 |
| **1** | la sessione XFCE **nasce** per un utente nuovo | nessuna ancora verde: C1(xfce) resta rossa (manca la cattura) — si prova con la misura di I1 | ✅ **PASS** — CP1 · CP2 · CP3 · CP4 · rete intera |
| **2** | l'immagine di XFCE arriva al browser (`zwlr_screencopy`) | ⭐ **C1(xfce)** | ✅ C1(xfce) VERDE, 530 fotogrammi · ⛔ **colori scambiati** trovati dal revisore e curati · ⏳ prova dei colori (C2) e rete |
| **3** | mouse e tastiera arrivano a XFCE (`virtual-keyboard`, `virtual-pointer`) | ⭐ **C4(xfce)**, e C3 · C6 su xfce | 🔧 scritto (agente, 21 set), `[M]` **provato sul portatile** contro labwc 0.8.3 — ⏳ sulla macchina |
| **4** | il banco guarda XFCE come GNOME | ⭐ **C2(xfce)**, **C8b(xfce)** | 🔧 cancelli aperti per capacità (`11-capacita-del-prodotto.sh`), C17 dà 3 e non rosso — ⏳ sulla macchina |
| **5** | gli appunti su XFCE | ⭐ **C17(xfce)** | 🔧 scritto e costruito, **non provato** (21 set) |
| **6** | ⭐ lo schermo cambia misura a sessione viva (`set_custom_mode`) — ⛔ **si può**, qui: è il ripiego che KDE ci aveva imposto | da definire | 🔧 `zwlr_output_manager` v4 scritto dentro l'incremento 2 — ⏳ sulla macchina |
| — | energia, blocco, voci pericolose (decisione dell'utente del 21 set) | la prova degli 11 minuti | 🔧 scritto (agente) — ⏳ sulla macchina |
| — | la strada della SCHEDA per la cattura (copia zero, `gbm`) | tratto e CPU di labwc | 🔧 scritto (agente), `[M]` sul portatile: CPU di labwc **dimezzata** — ⚠ **da portare a mano** sopra il `wlroots.c` riscritto |

⚠ **L'ordine 2-3 può invertirsi**, e la ragione va scritta il giorno che si decide: su KDE la
cattura è venuta prima dell'input perché era la più piccola; qui sono **tutte e due grosse**, e la
cattura è quella che rende verde una maglia.

### Incremento 1 — la sessione XFCE nasce *(CP1 abbozzato il 20 set; CP2 non ancora fatto)*

| | |
|---|---|
| **OBIETTIVO** | un utente che si collega per la prima volta, su una macchina che ha **solo** XFCE, ottiene dal prodotto una sessione XFCE **sua**, senza schermo fisico, e il prodotto la **riconosce viva**. ⛔ Niente cattura, niente input, niente appunti. ⛔⛔ E **niente misura**: su wlroots l'output non nasce della misura chiesta — il ridimensionamento è l'incremento 6, e questo si scrive nell'obiettivo invece di scoprirlo |
| **INVARIANTE** | su GNOME e su KDE **nulla cambia**: stesso desktop riconosciuto, stesso drop-in, stesso comando, stessi tempi. Su XFCE nessuna seconda sessione, nessun residuo dopo la chiusura (C7). ⚠ Le macchine con più desktop sono fuori scopo (`DECISIONI.md` §0.6) e restano come oggi |
| **MODULI** | `src/sessione.c` + `src/sessione.h` · `banchi/11-scatole/Contenitore.xfce` · `banchi/11-scatole/adattatore.xfce.sh` |

#### ⭐⭐ La cura non è «aggiungere XFCE all'elenco»: è **togliere il ripiego**

⛔ Oggi `riconosci_desktop()` ha un quarto caso (`src/sessione.c:295-299`): nessun desktop
conosciuto ⇒ **GNOME per ripiego, in silenzio**. È lì che cade una macchina solo-XFCE.

⚠ E il guasto **non arriva dove si crede**: `scrivi_dropin()` (`src/sessione.c:1175-1189`) rilegge
l'`ExecStart` di `org.gnome.Shell@wayland.service`, unità che non esiste, ottiene una risposta
vuota e scrive *«un altro drop-in vince sul mio»*. ⛔ **Il sintomo accusa un drop-in altrui; la
causa è che GNOME non c'è.** `[?]` da confermare in CP2.

⇒ Con «un desktop per macchina» (§0.6) quel ramo è **l'unico posto in cui il prodotto può
sbagliare desktop, e sbaglia in silenzio**. Se l'incremento 1 aggiungesse XFCE lasciandolo lì, il
giorno di LXQt si ripeterebbe identico. ⇒ Dopo la cura il quarto caso dice **«non riconosco nessun
desktop»** e non fa nascere niente. ⚠ È un cambiamento di comportamento su una macchina senza
desktop, ed è dichiarato.

#### ⛔ I tre pericoli che il sopralluogo ha trovato, e che non sono rami da aggiungere

1. ⛔⛔ **Una guardia che evapora, senza una riga di registro.** `unita_inattiva()`
   (in `src/sessione.c`) protegge dalla seconda sessione chiedendo a systemd se l'unità del
   compositore è ferma; `unita_ferma()` (`:1290-1300`) accetta `unknown` ⇒ **risponde vero per
   un'unità che non esiste**. Su XFCE, dove unità non ce n'è, la protezione pagata il 16 agosto 2026
   **non fallirebbe: sparirebbe**. Serve un fatto vero (nome assente dal bus **e** nessun `labwc`
   dell'utente).
2. ⛔ **`scrivi_dropin()` non ha oggetto su XFCE**: esiste perché il compositore è un'unità systemd
   d'utente — vero per GNOME e KDE, **falso qui**. Non è un ramo da aggiungere: è una funzione che
   su questo desktop non ha di che parlare, e il ramo deve **dichiararlo nel registro**, non far
   finta di aver scritto.
3. ⛔ **Tredici negazioni implicite.** Non esiste nessun `!e_kde()` letterale in `src/`: la
   negazione è sempre un `else` o una caduta in fondo — `:345`, `:550`, `:908`, `:1084`, `:1406`,
   `:1537`, `:1751`. ⚠ Aggiungere un terzo valore all'enum le trasforma **tutte insieme** da
   «GNOME» in «GNOME **o** XFCE», ⛔ **senza un avviso del compilatore**. Dimenticarne una sola non
   dà un errore: dà una sessione XFCE che nasce con l'ambiente di GNOME.

⚠ E un quarto, che non si cura qui ma si dichiara: `sessione_assicura()` (`:1891-2086`) è **codice
morto** (nessun chiamante), ⛔ ma il suo `case SESSIONE_SANA` (`:1902-1931`) butterebbe giù una
sessione XFCE sana. Non si tocca, si scrive.

#### CP2 — osservato, non dedotto (`[M]` 20 set 2026, dentro `rete11-xfce`)

**(1) Che cosa fa oggi il prodotto su una macchina solo-XFCE.** ⭐ La riga d'avvio **dice la verità**:

> `il desktop di questa macchina: GNOME per ripiego — ⛔ non trovo NE' gnome-session NE'
> startplasma-wayland: nessuna sessione grafica potra' nascere`

⛔ **Ma poi il guasto accusa due innocenti**, e l'ipotesi del sopralluogo è confermata alla lettera:

| `[M]` la riga | che cosa fa credere |
|---|---|
| `⚠ «gnome-shell» non e' nel PATH: ripiego dichiarato su /usr/bin/gnome-shell` | onesta |
| ⛔ `ho scritto «--headless --no-x11» e il gestore dice un'altra cosa: un altro drop-in vince sul mio. ExecStart in vigore:` *(vuoto)* | ⛔ **accusa un drop-in altrui**; la causa è che GNOME non c'è |
| ⛔ `senza il drop-in in vigore non la faccio nascere` | conseguenza della precedente |
| ⛔ `nessun monitor virtuale da catturare: ScreenCast: Mutter non espone RemoteDesktop (la sessione grafica e' avviata?)` | ⛔ **accusa Mutter**, che su quella macchina non esiste |

⇒ E C1 legge **solo la fetta dell'inquilino**, dove la riga vera non c'è: perciò dice *«nata
CIECA»* invece di *«il prodotto cercava gnome-session»*. Due diagnosi, una faccia sola.

**(2) ⛔ Il pericolo della guardia che evapora è CONFERMATO.** `[M]` Dentro la scatola, a un'unità
che **non esiste**: `systemctl --user is-active org.gnome.Shell@wayland.service` → **`inactive`**,
codice 4. ⇒ `unita_ferma()` (`src/sessione.c:1290-1300`) accetta `inactive` e risponde **vero**: su
XFCE la guardia contro la seconda sessione non fallirebbe, **sparirebbe**.

**(3) ⭐⭐ La sessione XFCE headless nasce, e nasce intera.** `[M]` Ricetta a mano dentro la scatola
— `labwc --session xfce4-session` con l'ambiente di `STUDI.md` §xfce §9.3 — vivi insieme:
`labwc` · `xfce4-session` · `xfce4-panel` · `xfdesktop` · `xfsettingsd` · `xfconfd` · `Thunar`.
⭐ E `org.xfce.SessionManager` compare sul **bus D'UTENTE**, non su uno privato: ⇒ eseguendo
`labwc` direttamente (senza passare da `startxfce4 --wayland`, che porta `dbus-run-session`) la
**decisione 4 si scioglie da sé** — il prodotto vede la vitalità della sessione con il codice che ha
già.

**(4) ⛔ L'output nasce 1280×720, e non lo decide il cliente.** `[M]` `HEADLESS-1, 1280×720,
refresh 0.000 Hz`. ⇒ Su wlroots la misura **non entra nella nascita**: si dà dopo, col protocollo.
⚠ E questo pesa sull'ordine degli incrementi — un'immagine consegnata a 1280×720 mentre il cliente
ne chiede 1920×1080 non è utile, quindi l'incremento 6 potrebbe dover salire accanto al 2.

**(5) ⭐⭐ I protocolli ci sono TUTTI — 47 global annunciati, e questi sono quelli che contano:**

| serve a | protocollo | `[M]` |
|---|---|---|
| **cattura** | `zwlr_screencopy_manager_v1` | **v3** |
| cattura, l'altra strada | `zwlr_export_dmabuf_manager_v1` | v1 — ⭐ esportazione DMA-BUF diretta, che `STUDI.md` non aveva pesato |
| **tastiera** | `zwp_virtual_keyboard_manager_v1` | v1 |
| **mouse** | `zwlr_virtual_pointer_manager_v1` | v2 |
| **appunti** | `zwlr_data_control_manager_v1` | **v2** — ⭐ è esattamente quello che `src/appunti_kde.c` già parla |
| **misura dell'output** | `zwlr_output_manager_v1` | **v4** — ⇒ il ridimensionamento a caldo **si può** |
| energia (chi spegne l'output) | `zwlr_output_power_manager_v1` | v1 |
| il pannello e la scrivania | `zwlr_layer_shell_v1` | v4 |
| buffer | `zwp_linux_dmabuf_v1` v4 · `wp_presentation` v1 | |

⛔ **Assenti, e va saputo prima di scrivere**: `ext_image_copy_capture_manager_v1` (il successore di
screencopy: ⇒ si scrive contro `zwlr_screencopy`, non contro di lui) e
`wp_linux_drm_syncobj_manager_v1` (le fence esplicite: ⇒ la sincronizzazione va risolta
diversamente). ⚠ E `ext_data_control_manager_v1` non c'è — come su KWin, e come `STUDI.md` prevedeva:
la strada resta `zwlr_data_control`.

**(6) La scatola è cresciuta**, e la ricetta lo dichiara (R6): `xfce4-panel`, `xfdesktop4`,
`xfce4-terminal`, `thunar`, `nano`. ⛔ Non è estetica: senza `xfdesktop` e `xfce4-panel` due dei modi
in cui la nascita fallisce — `exit(1)` senza layer-shell, e l'uscita muta con `n_monitors == 0` —
**non si possono nemmeno vedere**.

#### ⭐ La prova, e il controllo negativo che vale più della prova

- **controllo negativo del ripiego**: stessa scatola, **binario di oggi** ⇒ la riga d'avvio dice
  *«GNOME per ripiego»* e la sessione non nasce; **binario curato** ⇒ dice *«XFCE»* e nasce. È la
  prova che la cura ha colpito il ramo giusto e non un altro.
- ⭐ **la prova della trappola del logout** (non ha analogo su KDE): se la riga del compositore non
  contiene **sia** `labwc` **sia** `--session`, al logout `xfce4-session` esegue `loginctl
  terminate-session ''` — cioè **ammazza la sessione logind di REMOTIX**, non solo il desktop.
  ⛔ `STUDI.md` §xfce §9.2 dice di provarla **sul banco e mai sull'utente**.
- ⚠ **il tetto dell'attesa va giustificato**, non copiato da KDE: su Wayland nessun client di XFCE
  si registra e ogni gruppo di priorità si sblocca a scadenza — `STARTUP_TIMEOUT_WAYLAND` = **8 s
  per gruppo**, strutturali e non accorciabili.
- ⚠ **le cinture xfconf si rileggono**: `xfconf-query` esce con zero anche quando il demone ha
  rifiutato e ripristinato il valore. Una scrittura riuscita non è una configurazione applicata.

#### CP3 — la modifica minima (`src/sessione.c`, `src/sessione.h`)

⭐ **Due file, e nessun ramo di GNOME o di KDE toccato**: ogni blocco nuovo sta **prima** di quello
di GNOME e torna con `goto la_coda` o `return`, così i rami vecchi restano testualmente quelli.

| # | dove | che cosa |
|---|---|---|
| 1 | `sessione.h` | `SESSIONE_RIGA_XFCE` / `SESSIONE_COMANDO_XFCE` — ⭐ **la riga si scrive una volta e si usa due** (comando, e `XFCE4_SESSION_COMPOSITOR`): scriverla due volte vorrebbe dire poterle far divergere, e divergendo scatterebbe la trappola del logout senza una riga che lo dica |
| 2 | `sessione.h` | enum: `SESSIONE_DESKTOP_XFCE = 2`, `SESSIONE_DESKTOP_NESSUNO = 3` — ⚠ **in coda**, perché il numero viaggia come `uint32_t` fra padre e figlio |
| 3 | `riconosci_desktop()` | il ramo `xfce4-session`, **dopo** GNOME e KDE; ⛔ e il ripiego **tolto**: chi non riconosce nessuno adesso lo dice |
| 4 | `e_xfce()` · `e_nessuno()` | ⛔ e mai un `!e_kde()`: le tredici negazioni implicite sono il pericolo, e il modo di non caderci è scritto sopra le due funzioni |
| 5 | `nodo_della_scheda()` | il nodo si **apre**, non si inchioda: `renderD128` e `renderD129` si scambiano fra due avvii, e se l'apertura fallisce wlroots ripiega su pixman **in silenzio** |
| 6 | `sessione_viva()` · `sessione_stato()` | il nome `org.xfce.SessionManager` sul bus d'utente, con dichiarato che «viva» **non** vuol dire «della misura giusta» |
| 7 | `componi_ambiente()` | dieci variabili, ciascuna con la sua ragione — ⭐ e la colonna «da togliere» era già gratis: la funzione costruisce da zero |
| 8 | `scrivi_dropin()` | ⛔ su XFCE **non ha oggetto**, e lo dice invece di tornare `TRUE` in silenzio |
| 9 | `avvia()` | il comando a tre vie, non un ternario annidato |
| 10 | `unita_inattiva()` | ⛔ la guardia che sarebbe **sparita**: si guardano due fatti (`/proc` e il nome sul bus) invece di chiedere a systemd di un'unità che non c'è |
| 11 | `sessione_termina()` | `Logout`, poi **SIGTERM a labwc** — qui la forza non è systemd. ⚠ `SIGTERM` e non `SIGKILL`: labwc chiude i suoi client, e un `SIGKILL` lascerebbe dietro proprio quel che C7 cerca |
| 12 | `sessione_impostazioni()` | la cintura `WaylandLogoutCommand=/bin/true`, ⭐ **riletta**; la cache delle sessioni salvate cancellata; il resto dichiarato rimandato |
| 13 | `sessione_inibisci()` | ⛔ **no-op dichiarato**: `xfce4-session` non consulta l'inibitore, quindi chiedere darebbe un ⛔ falso e zero protezione |
| 14 | `sessione_fai_nascere()` | il rifiuto onesto quando non c'è nessun desktop — ⭐ **nella fetta dell'inquilino**, dove il banco la legge |
| 15 | `nome_desktop()` | ⚠ `LEZIONI.md` §1.9: il tema del cursore, scritto per KWin e riusato da labwc, annunciava «⭐ **Plasma**» dentro una sessione XFCE. La riga non si duplica: si fa dire il nome giusto |

#### CP4 — la prova (`[M]` 20 set 2026, binario `48c87296`)

| che cosa | atteso | misurato |
|---|---|---|
| il desktop riconosciuto, nelle quattro scatole | quattro risposte diverse e giuste | ⭐ gnome → *GNOME* · kde → *KDE Plasma* · xfce → ⭐ *XFCE (c'è xfce4-session, e labwc per farlo girare)* · lxqt → ⛔ *NESSUN DESKTOP RICONOSCIUTO* |
| **la sessione XFCE nasce** per un inquilino nuovo | labwc + xfce4-session vivi | ⭐ **e nasce intera**: `labwc` · `xfce4-session` · `xfce4-panel` · `xfdesktop` · `xfsettingsd` · `xfconfd` · `Thunar` · `wrapper-2.0` |
| il prodotto la **riconosce viva** | il nome sul bus d'utente | ⭐ *«il gestore di sessione XFCE c'è sul bus: la sessione è viva»* |
| quanto ci mette | ≥ 8 s (gruppi di priorità) | `[M]` **17,0 s** dal «la faccio nascere» al nome sul bus (giro pulito delle 21:40). ⚠ Un secondo giro ha dato 0,4 s e **non lo conto**: il registro non era stato ritroncato, e due misure che non si possono separare non si mediano — `[?]` da rifare pulita prima di tarare il tetto del banco |
| la cintura del logout | scritta **e riletta** | ⭐ *«WaylandLogoutCommand = /bin/true, RILETTA»* |
| la scheda data a wlroots | aperta, non dedotta | ⭐ *«la scheda che do a wlroots è /dev/dri/renderD128 (aperta, non dedotta)»* |
| il drop-in | dichiarato assente, non finto | ⭐ *«nessun drop-in da scrivere … E la tela chiesta (1920x1080) NON entra nella nascita»* |
| **C7(xfce)** — si chiude e non resta niente | verde | ⭐ **VERDE**, 1,15 s. ⚠ E il banco dichiara da sé che una voce (`/dev/dri`) passa ancora **a vuoto**: la sessione non apre la scheda finché non c'è la cattura |
| **C1(xfce)** | ⛔ **rosso, e per un motivo NUOVO** | ⛔ rosso: *«nate CIECHE»*. ⭐ E adesso è vero alla lettera — la sessione c'è, l'immagine no: è l'incremento 2 |
| **C1(gnome)** · **C1(kde)** | verdi, invariati | ⭐ **verdi tutt'e due**, 2 sessioni su 2 ciascuna |

⚠ **Quel che resta storto e si dichiara**, perché è l'incremento dopo a curarlo: su XFCE la cattura
cade ancora nel ramo di Mutter e scrive *«Mutter non espone RemoteDesktop»* — ⛔ una riga che accusa
un innocente. È lo stesso punto in cui si fermò l'incremento 1 di KDE, ed è il primo che
l'incremento 2 toglie di mezzo.

#### La rete intera (`[M]` 20→21 set 2026, 23:48→03:00, binario `48c87296`, 11 460 s)

| | |
|---|---|
| **GNOME** | ⭐ **tutto verde**, C17 compresa — identico al CP0 |
| **KDE** | ⭐ **tutto verde**, e ⭐⭐ **C2(kde) è tornata a giudicare**: 0 · 0 · 0 dove al CP0 dava 3 · 3 · 3. La cura del «prima» (240→900) regge, e i suoi **due guasti innestati sono visti** |
| **xfce** | passo0, C5, C7, C8, C9 verdi coi guasti · ⛔ **C1 rosso** — ed è l'incremento 2, dichiarato |
| **lxqt** | uguale a xfce — ⚠ e il suo C1 rosso adesso ha una causa **nuova e giusta**: il prodotto le dice in faccia che **non riconosce nessun desktop** |
| la rete | C11 verde (stesso binario nelle quattro) · C13 verde · C14 verde, 786 s |
| ⭐ **guasti innestati** | **34 su 34 visti** — due in piu' del CP0, e sono proprio i due di C2(kde) che il CP0 non aveva potuto certificare |
| rossi | **2**, e sono i due dichiarati |

⇒ ⭐ **L'incremento 1 passa il cancello**: XFCE ha guadagnato la nascita della sessione, GNOME e KDE
non hanno perso niente, e la rete sa ancora dare rosso.

---

### Incremento 2 — l'immagine di XFCE arriva al browser *(CP1, 21 set 2026 — non ancora cominciato)*

| | |
|---|---|
| **OBIETTIVO** | un cliente attaccato alla sessione XFCE **vede il desktop**: fotogrammi veri, che cambiano. La maglia che lo prova è **C1(xfce)**, la stessa che lo provò per Plasma |
| **INVARIANTE** | su GNOME e su KDE **nulla cambia**: stessa strada (PipeWire), stessi numeri, stesso libro del danno. ⛔ E il consumatore del DMA-BUF delle fasi 8-9 **si riusa, non si riscrive** |
| **LA DECISIONE CHE LO GOVERNA** | ✅ cattura **diretta** (`zwlr_screencopy_manager_v1` v3), dell'utente, 20 set 2026 |

#### ⛔ La differenza che fa il lavoro, e non è il protocollo: è il verso

Su GNOME e su KDE il compositore **spinge**: monta un flusso PipeWire e i fotogrammi arrivano da
soli. Tutto `src/cattura.c` (2 348 righe) è costruito su quel verso, e `figlio.c` lo usa in **35
punti** attraverso dieci funzioni (`cattura_avvia` ×7, `cattura_prendi` ×5, `cattura_fermo_libera`
×7, `cattura_ridimensiona` ×3, `cattura_risveglia` ×3, …).

⛔ Su wlroots si **tira**: `capture_output → frame → copy → ready`, **una richiesta per
fotogramma**, e nessun nodo PipeWire da nessuna parte. ⇒ Il ritmo non è una proprietà del
compositore: **è il nostro ciclo** — che è precisamente quel che la decisione dell'utente ha
comprato.

⚠ **E la domanda di progetto da sciogliere in CP3** è una sola, e va posta bene: la seconda sorgente
entra **accanto** a `Cattura` (una sorgente che si sceglie, e i trentacinque punti di `figlio.c`
restano dove sono) oppure **sotto** di lei? ⛔ La risposta non si sceglie per gusto: la si sceglie
misurando quante delle dieci funzioni hanno senso sul verso a tiro. `cattura_ridimensiona`, per
esempio, su wlroots **non è la stessa cosa**: lì la misura si cambia sull'output, non sul flusso.

#### Quel che è già stato misurato, e non va rimisurato

| | `[M]` 20 set 2026, dentro `rete11-xfce` |
|---|---|
| il protocollo | `zwlr_screencopy_manager_v1` **v3** — e c'è anche `zwlr_export_dmabuf_manager_v1` v1, una seconda strada che `STUDI.md` non aveva pesato |
| il permesso | ✅ **non esiste**: nessun `.desktop`, nessun portale, nessun dialogo |
| il buffer della scheda | `zwp_linux_dmabuf_v1` **v4** |
| ⛔ le fence esplicite | **assenti** (`wp_linux_drm_syncobj_manager_v1` non c'è) ⇒ la sincronizzazione va risolta per un'altra strada, e va misurata |
| ⛔ il successore | `ext_image_copy_capture_manager_v1` **assente** su Trixie ⇒ si scrive contro screencopy, sapendolo |
| ⛔ la misura dell'uscita | nasce **1280×720** cablata, e il cliente ne chiede 1920×1080 |

#### CP2/CP4 del primo passo — `[M]` 21 set 2026: **i pixel arrivano**

⭐⭐ Il modulo `src/wlroots.c` + `src/wlroots.h` esiste, e il banco
`banchi/13-w1-un-fotogramma.c` lo prova dentro una sessione XFCE viva.

| che cosa | misurato |
|---|---|
| fotogrammi tirati | ⭐ **10 su 10**, poi 3 su 3 — nessun fallito, nessuno scaduto |
| l'uscita | `HEADLESS-1`, **1280×720**, stride 5120 |
| il formato | **XB24** (`XBGR8888`) — ⚠ **non** quello che si sarebbe dato per scontato |
| il contenuto | **199-201 colori distinti**, 6,1 % dei campioni non nero ⇒ è un desktop vero, non uno schermo spento |
| il tempo per fotogramma | `[M]` **8,8-14,9 ms** in media, 16,5 ms il peggiore — ⚠ ed è il giro INTERO col copiamento in memoria, su Intel UHD 730 |
| il puntatore | **dentro l'immagine** (`overlay_cursor = 1`), come previsto: su questa famiglia non c'è un canale per la sua forma |

#### ⛔⛔ E una trappola pagata subito, che vale piu' del fotogramma

`[M]` La prima stesura del banco scriveva i canali nell'ordine di `XRGB8888`.
L'immagine è uscita **con le cartelle arancioni** — e sembrava giusta: un desktop
Xfce con le icone color zucca è perfettamente plausibile. ⛔ Ma labwc dichiara
**XBGR8888**, che in memoria è `R G B X`: erano **R e B scambiati**, e le cartelle
vere di Adwaita sono **blu**.

⇒ ⭐ È `LEZIONI.md` §1.9 nella sua forma peggiore: **un controllo che dà un
risultato plausibile non è un controllo**. Il fatto si chiede al formato — che lo
dice — invece di dedurlo da come appare. ⚠ E se fosse arrivato fino al
codificatore, l'utente avrebbe visto un desktop blu senza che una riga lo
spiegasse.

#### CP3/CP4 — `[M]` 21 set 2026: **C1(xfce) è VERDE**

⭐⭐ **La seconda sorgente entra SOTTO la porta della cattura, non accanto.** Come gli appunti, che
in casa hanno già due costruttori dietro una porta sola. ⇒ `figlio.c` usa quell'interfaccia in **35
punti e non ne cambia nessuno**: GNOME e KDE restano testualmente quelli di prima.

| file | che cosa |
|---|---|
| `src/wlroots.c` · `.h` | il client Wayland: `zwlr_screencopy` v3 (i fotogrammi) e `zwlr_output_manager` v4 (la misura) |
| `src/cattura.h` | `cattura_avvia_wlr()`: il costruttore dell'altro verso |
| `src/cattura.c` | il campo `wlr` in cima a `struct Cattura`, e una guardia in cima a ogni funzione pubblica |
| `src/figlio.c` | il terzo ramo del palco: su XFCE **non c'è niente da aprire**, la sorgente è la cattura |
| `banchi/13-w1-un-fotogramma.c` | il banco, che lega **gli stessi oggetti del prodotto** (R12.3) |

| la prova | misurato |
|---|---|
| **C1(xfce)** | ⭐⭐ **VERDE**, 3 sessioni su 3 |
| C1(gnome) · C1(kde) | ⭐ verdi, 3 su 3 ciascuna |
| i fotogrammi **veri** | ⭐ **530 consegnati, 19 chiavi, 0 guasti** |

⛔ **E quell'ultima riga è quella che conta**: C1 legge una riga di registro, e una riga si può
scrivere. I fotogrammi no. ⇒ Si contano apposta, perché il verde di una maglia che guarda il
registro non vale finché non si è visto passare il traffico.

#### ⛔⛔ Tre difetti trovati PROVANDO, e due RILEGGENDO

Provando:
1. `mutter_monitor_cerca(NULL)` — un'asserzione fallita nel registro. Rumore che somiglia a un
   guasto: su wlroots il monitor è l'uscita del compositore, e non c'è nessuna sessione di Mutter.
2. Il testimone *«formato negoziato: LxA»* lo scriveva la richiamata di PipeWire, che qui non
   esiste. ⇒ Senza, la maglia avrebbe detto *«nata cieca»* di una sessione che si vede benissimo.
3. La divergenza fra tela **chiesta** (1920×1080) e uscita **vera** (1280×720): adesso si dichiara
   alla prima riga.

⭐ Rileggendo il proprio codice, **prima che si vedessero**:

4. **Il buffer riusato dopo una copia abbandonata.** Mollato un fotogramma dopo aver mandato `copy`,
   il compositore può scriverci dentro **più tardi**: riusarlo dà un fotogramma vecchio in mezzo ai
   nuovi — ⛔ non un errore, uno **sfarfallio**. È `LEZIONI.md` §8 (non era *acquire*, era
   *release*). ⇒ Chi abbandona dopo `copy` marca il buffer.
5. ⛔⛔ **Il canale scambiato, arrivato fino al codificatore.** `figlio.c` dichiara
   `CODIFICATORE_PIXEL_BGRX` — `B G R x` in memoria, inchiodato dalla fase 2 — e labwc offre per
   primo **XBGR8888**, che è `R G B x`. ⇒ **L'utente avrebbe visto il desktop con il rosso e il blu
   scambiati**, senza una riga che lo spiegasse.
   ⭐ E la cura non è insegnare un formato nuovo al codificatore, che GNOME e KDE usano: è
   **chiedere quello che si sa già leggere**. Su screencopy v3 il compositore ne offre più d'uno
   apposta, e `buffer_done` esiste per questo. ⚠ E l'elenco offerto finisce nel registro, perché il
   giorno che i canali escono storti la prima domanda è *«che cosa offriva il compositore?»*.

⭐ **La stessa trappola, due volte in un giorno, e la seconda non è arrivata all'utente.** La prima
l'aveva pagata il banco (cartelle **arancioni** che sembravano giuste, e invece erano blu). ⇒ È
`LEZIONI.md` §1.9 nella forma peggiore: **un risultato plausibile non è una conferma**.

#### ⚠ E l'ordine con l'incremento 6 va deciso qui, non subito

Un'immagine consegnata a **1280×720** mentre il cliente ne ha chiesta una a **1920×1080** non è
«l'immagine che arriva»: è un'immagine sbagliata. ⇒ O l'incremento 2 si prende anche
`zwlr_output_manager_v1` (che c'è, v4), o C1(xfce) resterà rossa per una ragione che non è la
cattura. **Si decide col primo fotogramma in mano**, non prima.

---

### Incremento 5 — gli appunti su XFCE *(scritto e costruito il 21 set 2026; C17(xfce) non ancora girata)*

⭐ **Il modulo c'era già**: `src/appunti_kde.c` parla `zwlr_data_control_manager_v1`, che è di
wlroots. La modifica è di cinque file e non tocca il protocollo:

- `appunti_kde.c`: l'apertura diventa `apri_su(compositore)`, con due porte —
  `appunti_kde_apri()` («KWin») e `appunti_kde_apri_wlroots()` («labwc»). Il nome serve **solo** alle
  tre righe di registro; su KDE escono uguali lettera per lettera;
- `src/appunti.c` e `src/appunti.h`: `appunti_apri_wlroots()`, lo stesso involucro di `appunti_apri_kde()`;
- `figlio.c`: se `sessione_desktop() == SESSIONE_DESKTOP_XFCE` si apre quella, **prima**; il ramo
  KWin/Mutter di sotto è quello di prima.

⚠ **`kwin_display_apri()` resta**, dichiarato: prende `WAYLAND_DISPLAY` o il primo `wayland-0..9` che
risponde, senza guardare chi c'è dietro `[R]` (`kwin.c`). Spostarlo in un file neutro vorrebbe dire
toccare `kwin.c`, che porta il video di KDE, per guadagnare solo un nome. ⇒ La riserva 1 di
`STUDI.md` §xfce §8 è **chiusa**.

**Le altre riserve, rilette sul sorgente di wlroots 0.18.2** (`sources.debian.org`, 21 set 2026):

| riserva | esito |
|---|---|
| l'eco | ⭐ **certa, e la guardia regge** `[R]`: ogni device è iscritto a `set_selection` senza filtro (`wlr_data_control_v1.c:459-468`); `wlr_seat_set_selection` distrugge la sorgente vecchia (⇒ `cancelled`, `:145`) **prima** di emettere il segnale, e le due notizie viaggiano sulla stessa connessione |
| MIME duplicati ⇒ ciclo | ⭐ **non può scattare** `[R]`: wlroots scarta solo i duplicati `strcmp`-uguali (`:38-45`), e noi offriamo sempre e solo i tre tipi di `TIPI_TESTO`, tutti diversi. Era un rischio di v1, che rigirava l'elenco del client. ⚠ E se la guardia saltasse non ci sarebbe comunque un ciclo: la lettura della nostra sorgente dalla pompa che la serve scade in 5 s senza consegnare niente |
| `onlyReplaceEmpty` | ⭐ **nessun danno** `[R]`: non lo offriamo e non lo leggiamo mai |
| la selezione che muore con chi ha copiato | ⚠ **vera, e non è nostra**: in XFCE su Wayland non c'è gestore. Arriva `selection(NULL)` ⇒ al client non si manda niente, e il client tiene l'ultimo testo. La **nostra** sorgente (il testo del client) vive quanto il figlio |

⛔ **Per provarlo** (C17 su xfce) la scatola deve avere gli attrezzi degli appunti — vedi il punto 5
del banco qui sopra: senza `wl-clipboard` la maglia legge `""` e non lo dice.

## 🔸 Le scelte che aspettano l'utente

Le cinque di `STUDI.md` §xfce §13, più le tre uscite dal sopralluogo del 20 settembre. ⛔ Si pongono
**quando la misura che le riguarda è stata fatta**, non prima.

| # | la scelta | quando si pone |
|---|---|---|
| ~~**1**~~ | ✅ **DECISA il 20 set 2026, dall'utente: cattura DIRETTA.** *«Li chiediamo noi»* — il ritmo, il cursore e la misura restano nostri, e si riusa intero il consumatore DMA-BUF delle fasi 8-9. ⛔ Il ponte PipeWire è escluso: quattro processi dentro un budget di 16,6 ms, e nessuna delle tre cose sopra | ⭐ fatta |
| **2** | il ridimensionamento a caldo si accende subito o dopo? | incremento 6 |
| **3** | il cursore dentro l'immagine o sul canale del puntatore? | incremento 3 |
| **4** | il bus di sessione: `dbus-run-session` (privato) o bus d'utente? ⛔ Col privato la vitalità della sessione è **cieca** per il prodotto com'è scritto oggi | incremento 1, dopo CP2 |
| ~~**5**~~ | ✅ **DECISA il 21 set 2026, dall'utente**: *«anche in XFCE vanno disabilitate le voci di standby, lockscreen, reset e spegnimento»* — le stesse di GNOME e KDE (`DECISIONI.md` §4.7). ⛔ **«Esci» resta** (§4.1-ter): è l'unico gesto che termina la sessione. ⚠ «Cambia utente» non è stato nominato: resta aperto | in corso |
| **6** | «viva» = il nome sul bus, oppure `StateChanged(0→1)`? Il primo è un ramo di due righe; il secondo è un **sorvegliante di segnali**, che in `sessione.c` non esiste | incremento 1, dopo CP2 |
| **7** | quanto cresce `Contenitore.xfce`: pannello e scrivania già nell'incremento 1? | incremento 1 |

⚠ **E una cosa che la decisione 1 si porta dietro, saputa dal primo giorno.** L'XML di
`wlr-screencopy-unstable-v1` — messo in deposito in `src/protocolli/` il 20 set 2026, e verificato
rigenerandoci sopra il codice: le tabelle escono **identiche** a quelle che v1 aveva generato — porta
in testa una riga nuova rispetto ad allora:

> *«This protocol is deprecated and not intended for production use. The ext-image-copy-capture-v1
> protocol should be used instead.»*

⛔ Ma `[M]` 20 set 2026 labwc su Trixie **non espone** `ext_image_copy_capture_manager_v1`: non c'è
niente da usare al suo posto. ⇒ Si scrive contro screencopy **sapendolo**, e `STUDI.md` §xfce §4.6
dice già come: il codice si scrive perché il secondo attuatore possa entrare accanto al primo, non
al suo posto.

---

## Le misure

| che cosa | atteso | misurato | data |
|---|---|---|---|
| **CP0** — giro `tutto` sulle **quattro** scatole, lanciato sul server | GNOME verde; KDE verde per tutto il certificato; su xfce/lxqt solo C1 rosso; guasti tutti presi; un binario solo | ⚠ **come atteso tranne una casella**, spiegata e curata — vedi sotto | `[M]` 20 set 2026, 16:19→19:31 |

### CP0 in dettaglio — binario `9e3154a6`, 11 521 s, 86 maglie

| | |
|---|---|
| **GNOME** | ⭐ **tutto verde**: passo0, C1×10, C2 (+2 guasti), C3 (+scena ferma +2 guasti), C4 (+2), C5, C6, C7, C8, C8b, C9, **C17 (+guasto)** |
| **KDE** | verde ovunque **tranne C2 ×3, uscita 3** — ⚠ l'unica differenza inattesa del giro, classificata **C (difetto del banco)**: vedi sotto |
| **xfce · lxqt** | passo0, C5, C7, C8, C9 verdi coi loro guasti · ⛔ **C1×10 ROSSO** su tutt'e due (il mandato della fase) · C2 C3 C4 C6 C8b **e C17** saltate dal cancello «solo GNOME e KDE» |
| **la rete** | C11 verde (stesso binario nelle quattro) · C13 verde · **C14 verde, 786 s, quattro scatole** · C10 C12 C15 C16 a 2/3 perché sul server il deposito git non c'è — dichiarato, non è un rosso |
| ⭐ **guasti innestati** | **32 su 32 visti** |
| rossi | **2**, e sono i due dichiarati: `C1(xfce)` e `C1(lxqt)` |

⇒ ⭐ **C17 su GNOME è verde dentro un giro completo**: l'incremento 13 della fase 12 chiude qui, e
quella casella smette di essere «provata a mano».

#### ⛔ L'unica differenza inattesa — C2(kde), e non era il prodotto

`[M]` Nel giro, C2(kde) è uscita **3** tutt'e tre le volte (sana + due guasti): *«i primi 240
fotogrammi sono tutti neri o quasi: il desktop non aveva niente da mostrare PRIMA
dell'applicazione»*. ⛔ Ma **la finestra si era aperta**: l'immagine «dopo» del giro è il colore
dichiarato che copre lo schermo. ⇒ Il banco non aveva il **termine di paragone**, e si è astenuto —
che è il suo dovere, non un difetto di giudizio.

`[M]` Rimisurata subito, sulla stessa scatola, **tre volte**: **186** · **186** (scatola rifatta da
zero) · **189** (⭐ e con la cache dell'ospite svuotata, per togliere di mezzo il disco freddo).
⇒ Il numero vero è **~187 e stabile**: il margine su 240 era **54 fotogrammi, il 29 %**.

`[?]` Perché dentro il giro completo ne servano di più (379 fotogrammi in tutto contro 249) non è
misurato. Il sospetto è scritto: fra due banchi sullo stesso posto **il posto di prima resta
attaccato una ventina di secondi**, e C2(kde) nel giro viene subito dopo C9(kde), che di sessioni ne
ha fatte due.

⭐ **La cura è un tetto che non morda**, non un tetto ritarato al pelo: `--fotogrammi-prima` da 240 a
**900**, cioè più di quanti il flusso ne abbia mai avuti. ⛔ E **il giudizio non cambia di una
virgola** — il metro resta il colore che cresce di 20 punti e copre il 25 %: cambia solo quanto a
lungo il banco cerca il proprio termine di paragone, e la ricerca **si ferma al primo fotogramma
disegnato**, quindi alzare il tetto non costa niente quando il desktop dipinge presto.

#### ⚠ E due disallineamenti chiusi nello stesso giro

1. **Immagini indietro rispetto alle ricette**: `Contenitore.gnome` e `Contenitore.kde` erano state
   toccate dall'incremento 13 (`nano`, `python3-gi`, `gir1.2-gtk-4.0`) ma le immagini no. ⚠ Nessuna
   maglia ne dipendeva (`[M]` gnome aveva `gi` per dipendenza; su kde C17 usa `wl-clipboard`), ma
   alla prossima prova a mano `nano` non ci sarebbe stato. ⇒ **Ricostruite**, e le quattro scatole
   portano lo stesso binario `9e3154a6`.
2. **Il tetto d'attesa della delega remota** era 2 400 s contro giri da 11 521: la metà che aspetta
   mollava dopo 40 minuti dicendo «non ho potuto guardare» **mentre di là si stava ancora
   misurando**. ⇒ `ATTESA_REMOTA` a 14 400, e scritto che la protezione vera non è il tetto ma la
   domanda sull'unità remota.

### ⭐ La certificazione — binario di `4cd86a0`, 21 set 2026, 14 697 s

Giro `tutto` sulle quattro scatole **rifatte da zero**, innesco `fase13-danno-scheda`, lanciato sul
server alle 13:26 UTC e chiuso alle 17:31 UTC.

| | |
|---|---|
| ⭐ **XFCE** | **27 maglie su 27 verdi**: passo0, C1×10, C2 (+2 guasti), C3 (+scena ferma +2 guasti, **compreso «codificatore fermo»**), C4 (+2), C5, C6, C7, C8, C8b, C9, **C17 (+guasto)** |
| **GNOME · KDE** | nessuna regressione: verdi come a CP0 |
| **lxqt** | come a CP0: il prodotto non lo riconosce, e le maglie del prodotto saltano dicendolo |
| **la rete** | C11 C13 C14 verdi sul server · ⭐ **C10 C12 C15 C16 fatte girare sul portatile, dove il deposito c'è: tutte verdi** |
| ⭐ **guasti innestati** | **43 su 43 visti** |

⇒ **XFCE è nel perimetro protetto**, accanto a GNOME e KDE.

#### Le due cure che la rete ha chiesto prima di dare verde

1. ⛔ **C3(xfce) non vedeva il guasto «codificatore fermo»** (rete delle 10:27): labwc consegnava
   **60 fotogrammi identici al secondo** su un desktop fermo, e un flusso che non cambia non
   distingue un codificatore fermo da uno sano. ⇒ **`copy_with_damage`** (screencopy v2+): il
   compositore risponde solo quando lo schermo cambia. ⚠ Che ha rotto subito C4(xfce): una copia
   «col danno» pendente bloccava il fotogramma intero forzato ⇒ se il palco deve dare un fotogramma
   intero e c'è una copia col danno in sospeso, **la si abbandona**. `[M]` Poi: 62 fps sulla strada
   della scheda, C3 e C4 verdi coi loro guasti.
2. ⛔ **C17 rossa su tutti e tre i desktop** — classificata **C (difetto del banco)**: il file
   dell'arbitro in `/tmp` aveva un nome fisso, apparteneva a un altro utente, e le mie prove a mano
   l'avevano sporcato. Provato per bisezione (il binario di ieri era rosso anche lui nella scatola
   sporca; il nuovo verde in una scatola pulita). ⇒ Nome per utente, tolto alla fine.

### ⭐ I client veri — 21 set 2026, sera, porta 8513

`banchi/12-client-veri.py`, **certificato prima** (porta vuota e parola sbagliata visti su tutt'e
due i browser):

| browser | verdetto | che cosa |
|---|---|---|
| **Firefox 140** Linux | ⭐ **PASS** | modulo · ammesso · primo fotogramma in 1,0 s · 84 fotogrammi in 8 s · tasto e mouse nel registro del server · 0 errori · riconnessione |
| **Chrome 153** Linux | ⭐ **PASS** | idem: 85 fotogrammi in 8 s, primo fotogramma subito, riconnessione |
| **Chrome Android** | ⏳ **all'utente** | l'emulatore non lo lancia già dalla fase 12: la validazione resta sua, come per KDE |

`[M]` La fotografia del desktop: pannello in alto, icone Home e File System, il dock in basso, le
cartelle **blu** (i canali sono giusti). ⚠ Lo sfondo è **nero**: alla scatola manca il pacchetto
degli sfondi — è la scatola, non il prodotto.
⚠ La pagina dice «desktop sconosciuto» su XFCE — ⛔ **e lo dice anche su GNOME e KDE**: il server
manda la stringa fissa della fase 1 (`src/rcp.c`, messaggio `SESSIONE`). Non è di questa fase, e
toccarlo toccherebbe GNOME e KDE: resta com'è.

### ⭐ Le voci che spengono — decisione 5

`[M]` Nella scatola, a sessione accesa:

| | |
|---|---|
| menu utente del pannello | `-lock-screen`, `-suspend`, `-hibernate`, `-hybrid-sleep`, `-shutdown`, `-restart` · ⭐ **`+logout` c'è** · `+switch-user` c'è |
| xfce4-session | `LockCommand=/bin/false` · `ShowSuspend/Hibernate/HybridSleep=false` · `WaylandLogoutCommand=/bin/true` |
| xfce4-power-manager | `dpms-enabled=false` · inattività 0 |
| la finestra «Log Out» del menu Applications | riavvia e spegni **grigi**: la regola polkit `50-remotix-niente-spegnimento.rules` c'è, logind nega `CanPowerOff`/`CanReboot` e dice `CanSuspend=no` (`sleep.conf`) — la cintura 1 di `DECISIONI.md` §4.7, la stessa di tutti i desktop |
| ⭐ **11 minuti di sessione ferma** | lo schermo è **ancora il desktop**: niente blocco, niente nero, nessun salvaschermo in giro |

### ⭐ La trappola del logout — `banchi/13-w2`

| modo | esito |
|---|---|
| `--certifica` (il giudice a secco) | ⭐ 0 |
| sano | ⭐ **VERDE**: il desktop sparisce in 0,3 s, la sessione logind resta viva per tutti i 20 s |
| `--senza-xfconf` | ⭐ guasto **visto** |
| `--senza-variabile` | ⭐ guasto **visto** |
| `--senza-cinture` | ⚠ **3**, dichiarato: la sessione non cade |

⭐⭐ **Perché la trappola non morde** `[M]`: nel binario `xfce4-session` 4.20.2 di Trixie il comando
è scritto **`loginctl terminanate-session`** — un errore di battitura a monte. Il comando fallisce, e
la sessione si salva da sola. ⇒ **Oggi la trappola dorme**; le due cinture restano, per il giorno in
cui a monte correggeranno la parola. ⛔ E il 3 di `--senza-cinture` resta un 3: il banco non può
dimostrare una difesa contro un colpo che non parte.

⚠ **E una correzione al banco, misurata prima di farla.** La prima stesura pretendeva che la
sessione del prodotto fosse `active` prima del logout, e usava `State=closing` come «caduta». `[M]`
Ma **su GNOME (baseline) e su XFCE** la sessione del prodotto è `Service=remotix State=closing` **dal
primo istante**, col figlio vivo: è lo stato di sempre, non un segnale. ⇒ «Viva» adesso vuol dire
logind la descrive **e** il suo Leader (il figlio) è vivo; «caduta» vuol dire logind l'ha
dimenticata **o** il figlio è morto. Il giudice a secco resta certificato.

## ⛔ Che cosa NON ha funzionato

## Che cosa resta [?]

- ✅ **KDE RIPARTE DOPO UN RIAVVIO DEL SERVER ANCHE SE LA FINESTRA HA CAMBIATO MISURA** — 22 set 2026,
  binario `1c592928`. Trovato dall'utente: la sessione Plasma sopravvive al server (I4), ⛔ ma la tabella
  delle tele dei palchi vive nel PROCESSO e col riavvio si azzera ⇒ il ripiego di §4.5 («si concede quel
  che il palco **ha**») non aveva niente da concedere e passava la misura del client; KWin `--virtual`
  non ridimensiona, §6.2 vieta di spedire un fotogramma di misura diversa, e lo schermo restava **nero
  per sempre** mentre il registro ripeteva «gli richiedo» con un'attesa che raddoppia.
  ⭐ Cura in `src/rcp.c` (`rcp_tela_dal_palco()`, ramo 4): finché **non è uscito nessun fotogramma** il
  server **adotta** la misura del palco e la annuncia con un `TELA(ADATTATA)`; dopo il primo fotogramma
  resta vietato. `RCP.md` §7.1 chiude così la `⏳` del 15 agosto («che cosa fa il server quando il palco
  cambia misura senza che nessun `ADATTA_TELA` gliel'abbia chiesto»).
  `[M]` browser VERI sulla 8512, sessione nata a 1548x862 e rientro da una finestra di altra misura:

  | browser | prima (`f1807378`) | dopo (`1c592928`) |
  |---|---|---|
  | **Firefox 140** | ⛔ schermo mai acceso, **0** fotogrammi in 60 s | ⭐ acceso in **2,0 s**, **+3324** fotogrammi, 0 buchi |
  | **Chrome 153** | ⛔ schermo mai acceso, **0** fotogrammi in 40 s | ⭐ acceso, **+2273** fotogrammi, 0 buchi |

  ⚠ In tutti e quattro i giri la tela adottata è quella del palco (1548x862), non quella chiesta dalla
  finestra (1228x722 · 1240x692): è il `TELA` che lo dice, e i fotogrammi partono da lì.
- ✅ **IL VIDEO PESANTE: CURATO IN DUE COLPI** — 22 set 2026, binario `f1807378` + pagina `e2b8c43`.
  (1) `a50b389` la **spirale della chiave** (RCP.md §5.2): la pagina non si inchioda più — prima si fermava
  a 41 consegnati su 8810 stream. (2) `e2b8c43` **l'ordine di consegna**: gli stream si leggono incatenati,
  nell'ordine in cui il server li apre. Non era Firefox: 173 buchi su 173 erano fotogrammi arrivati dopo il
  loro successore, con 0 abbandoni lato server.
  `[M]` KDE, scena ~236 Mbit/s, 190 s, browser veri e visibili: Firefox buchi **173 → 3**, fuori ordine
  207 → 3, consegnati/s 37,9 → 48,1, tela **pulita** (dispersione dei blocchi 8×8 sul rumore 37,8 → 23,3,
  Chrome 16,7); Chrome buchi 14 → 2. Nessuna linea morta. La catena non costa ritardo: tratto
  cattura→byte fuori 16,4–16,9 ms, come prima.
  ⏳ **Aperti, e nessuno dei due è di oggi**: (a) Firefox riceve 48/s e ne dipinge 37/s — 1858 fotogrammi
  spariscono dentro il suo decodificatore, senza errori e senza che **nessuno li conti** (serve un contatore
  `decode()` contro fotogrammi in uscita) → ⭐ **il (a) è stato riletto il 23 set, e non è quel che
  sembrava: vedi la voce qui sotto**; (b) restano 3 buchi in 190 s: la catena rispetta l'ordine in cui
  il browser presenta gli stream, non i `numero` — si chiuderebbero solo con un riordino e una breve attesa.
  ⚠ In KDE gli inquilini lasciati dalla rete sono stati tolti a mano (restano `nictest` e `provanic`): C7 non
  li toglie, e in GNOME e XFCE ci sono ancora.

- ⏳ **I fotogrammi che «spariscono» in Firefox NON sono in coda: sono buttati, e a RAFFICHE** —
  23 set 2026, riletti i diari del 22 (nessuna misura nuova: solo aritmetica su registri già in mano),
  pagina `src/pagina.html`.

  ⛔ **La sottrazione vecchia era ambigua, e andava disfatta prima di tutto.** Fra `consegnati` («l'ho
  dato a `decode()`») e `dipinti` («è sul vetro») ci sono **quattro** passaggi e se ne contava **uno**
  (`saltati_coda`). ⇒ `consegnati − dipinti` non era «persi dal decodificatore»: era un numero senza
  padrone. `[M]` La **maggioranza** dei casi si spiega già oggi da sola: su 477 righe di diario con
  `consegnati − dipinti − salt − tard` fra 0 e 2, il resto è solo il fotogramma **in volo** all'istante
  della lettura (i due contatori si leggono in momenti diversi — la domanda era giusta). E l'episodio
  `dipinti 1097 video 3882→1097 salt 2785` chiude **esattamente**: 3882 − 1097 = 2785 = `salt`, zero
  ignoti. ⇒ Il buco vero è solo quello che resta **dopo** aver tolto `salt` e `tard`: lo chiamo **residuo**.

  ⭐⭐ **E IL RESIDUO NON È UN RITARDO — la prova è `voff`, che era già sulla stessa riga.**
  `voff` = (ora del client al vetro) − (`istante` del server di quel fotogramma): se il residuo fosse
  una coda, `voff` dovrebbe crescere **con lei**, di `residuo / ritmo`.

  | `[M]` 22 set, 190-200 s per giro | residuo finale | crescita di `voff` attesa **se fosse una coda** | crescita di `voff` **misurata** |
  |---|---|---|---|
  | Firefox 140, KDE (`n-ff-kde`) | **2007** | **+45 600 ms** | **+47 ms** |
  | Firefox 140, KDE (`h-ff-kde-base`) | **1757** | **+39 900 ms** | **+3 ms** |
  | Firefox 140, XFCE (`v-fi-xfce`) | **937** (piatto per 60 s) | **+21 300 ms** | **+155 ms** |
  | Firefox 140, GNOME (`v-fi-gnome`) | **1** | +23 ms | +32 ms |
  | Chrome 153, KDE (`n-cr-kde`) | **0** su 10 066 | 0 | +106 ms |

  ⇒ **Mille fotogrammi di residuo e zero millisecondi di ritardo.** La pagina dipinge sempre
  l'immagine **corrente**: quei fotogrammi non stanno aspettando da nessuna parte, **non esistono più**.

  ⭐ **E la forma è una raffica, non un tasso.** `[M]` Su 39 intervalli da 5 s di `n-ff-kde`, **17 perdono
  esattamente 0** e altri 6 perdono 1-2 fotogrammi (il volo); i **16** che restano perdono dal 16 %
  all'**88 %**: `t18` = 261 entrati, **31 dipinti**. ⇒ La media
  «48 riceve / 37 dipinge» **nasconde il difetto invece di dirlo**: quel che l'utente vede non è un ritmo
  più basso, sono **congelamenti di 1-4 secondi** più volte al minuto, con il desktop che poi riparte
  dall'immagine giusta. ⚠ È lo stesso difetto che la fase 9 chiamava `F4-CODA-DEL-DECODIFICATORE`, e
  **la guardia è cieca**: `saltati_coda` scatta su `dec.decodeQueueSize > 2`, e Firefox teneva
  `decodeQueueSize` **sotto 3 con 1800 fotogrammi mancanti all'appello**. Un interruttore che non si
  accende mai è peggio di uno che non c'è.

  ⭐ **IL CONTATORE, scritto oggi** (`src/pagina.html`, `conti.usciti` + `conti.in_bmp`), sulla riga del
  diario accanto agli altri: `video C→D **fuori U dentro N coda_dec Q bmp B** salt … tard … err …`.
  `fuori` si segna nella **prima riga di `dipingi()`**, che è il richiamo del decodificatore; `dentro` =
  `C − U`; `coda_dec` è quel che dichiara **lui**; `bmp` sono le `createImageBitmap` in volo. Costo: **tre
  somme di interi per fotogramma**, nessuna allocazione, nessun orologio. Il conto adesso **chiude**:
  `consegnati = fuori + dentro` e `fuori = salt + dipinti + tard + bmp + bmp_falliti`. Gli stessi nomi
  escono da `REMOTIX.tratti()`. ⚠ Curata nello stesso punto una riga che **falsificava il tratto 8**:
  `t_dec` si svuotava **tutta** oltre le 240 voci — cioè proprio quando il decodificatore non consegna —
  e adesso butta solo la più vecchia.

  ⭐⭐ **LA PREVISIONE, scritta PRIMA della misura sul ferro** (Intel UHD 730 integrata, non una scheda
  potente), e con dichiarato che cosa mi smentirebbe. Le due ipotesi sono separabili perché il contatore
  le separa:
  - **Prevedo `dentro` ≈ residuo e `bmp` ≈ 0-2**, con `coda_dec` ≤ 3 per tutto il giro. Vorrebbe dire che
    il decodificatore di Firefox **prende `decode()` e non produce nulla**, in silenzio: il difetto è suo,
    la nostra catena è pulita, e la cura è di rinunciare a quei fotogrammi **sapendolo** (cioè: `dentro`
    che cresce diventa un verdetto rosso, non un silenzio).
  - ⛔ **MI SMENTISCE: `bmp` che sale a centinaia e resta su.** Vorrebbe dire il contrario — che il
    decodificatore consegna e siamo **noi** a non finire di disegnare, con le `createImageBitmap` che non
    si risolvono mai e trattengono il `VideoFrame`. In quel caso il difetto è **nostro**, sta in
    `mostra()`, ed è la stessa famiglia della «perdita che nessun registro nomina».
  - ⚠ Mi smentisce anche `dentro ≈ 0` con `fuori ≈ dipinti` e il residuo sparito: vorrebbe dire che il
    residuo del 22 era un artefatto dei binari di quel giorno, curato da `a50b389`/`e2b8c43`.

  ⇒ **La misura vera la fa l'utente quando la rete libera il campo**: Firefox visibile su KDE, ~190 s di
  scena in movimento, e si leggono `dentro` e `bmp` sulla riga del diario. Fino ad allora questo punto
  resta ⏳.
- ✅ **Tre «linee morte» in 13 minuti su KDE: CHI TACEVA È IL BROWSER, ed era già stato CHIUSO** —
  23 set 2026, dai registri del 22 (`registri-22set/kde-1045.log`, che va da 10:27 a 10:45 **UTC** =
  12:27-12:45 locali) messi accanto al **giornale del tablet** (`journalctl`, ora locale). ⭐ La prova
  che chiude il punto sono gli **scope di systemd**: il processo del browser muore PRIMA del silenzio,
  non dopo.

  | | ultima parola del client (registro, UTC) | il processo del browser esce (giornale del tablet, locale) | linea morta |
  |---|---|---|---|
  | **12:30** Chrome 153 | 10:30:11.698 «il client si congeda, motivo=0x01 **la scheda è stata chiusa**» | `app-…Chrome-4339.scope` **12:30:11** (1,8 G di picco) | 10:30:22.330 |
  | **12:41** Firefox 140 | 10:41:26.73 ultimo pacchetto · 10:41:27.834 ultimo diario | `app-…firefox-esr-5792.scope` **12:41:28** (7min 9s CPU, 1,7 G) | 10:41:36.874 |
  | **12:42** Firefox 140 | 10:42:33.47 ultimo pacchetto | `app-…firefox-esr-6666.scope` **12:42:33** (830 M) | 10:42:44.297 |

  ⇒ In tutti e tre il client parlava fino **all'istante in cui il processo è uscito**: nessun
  congelamento di 10 s del browser, nessun OOM, nessun messaggio del kernel, nessun evento WiFi nella
  finestra. Le tre righe `causa=silenzio` portano tutte `offerti=0 usciti_byte=0 coda_video=0
  persi=0`: non aspettavamo niente di nostro, **non c'era più nessuno dall'altra parte**. ⇒ (a) rete,
  (c) tablet e (d) server sono **esclusi con la misura**; il ping continuo non serviva.

  ⭐ **E il difetto vero stava PRIMA, ed è quello che l'utente ha poi curato lo stesso pomeriggio.**
  Il diario della pagina (ogni 5 s, sempre puntuale al millisecondo ⇒ il filo principale della pagina
  NON era bloccato) tiene i contatori **fermi**, mentre il server continua a spedire ~58 fotogrammi/s
  e 1,5 MB/s:
  - sessione Firefox delle 12:39-12:41: `dipinti 1097 video 3882→1097 salt 2785` **identico per 50 s**
    (10:40:37.788 → 10:41:27.834). Si ferma esattamente sul **video pesante**: il fotogramma 3882 è
    l'ultimo contato, e subito dopo arrivano il 3886 da **131 238 byte** e la CHIAVE 3888 da **152 074
    byte**, chiesta dalla pagina a 10:40:34.583 (§5.2) perché i `buchi` erano appena passati da 1 a 3.
  - sessione Firefox delle 12:41-12:42: `dipinti 146 video 190→146` **fermo per 40 s**, e il
    fotogramma 190 pesa **144 305 byte**, il 193 è la CHIAVE da **152 901 byte** chiesta a 10:41:49.283.
  ⇒ È **la spirale della chiave**, parola per parola come la racconta `a50b389` («la pagina restava
  ferma sull'ultima immagine buona, con Firefox e con Chrome, **finché la linea moriva**»): curata il
  22 set alle **17:08** (`a50b389`) e alle **18:55** (`e2b8c43`), cioè **4 ore e mezza dopo** questi
  tre episodi. La riga di «che cosa resta» era rimasta indietro. Il `[M]` post-cura (190 s, browser
  veri, ~236 Mbit/s, «nessuna linea morta») è già qui sopra.
  ⛔ **Due correzioni alla vecchia riga**: i 1097 su 3882 erano di **Firefox 140**, non di Chrome —
  Chrome, nella stessa mezz'ora, dipingeva `817 video 817→817 salt 0 buchi 0`; e la linea morta non è
  un sintomo del blocco, è la **coda** del browser che l'utente chiudeva perché lo schermo era fermo.

- ✅ **Una linea morta ⛔ non si scrive più su un client che ci ha appena salutato** — 23 set 2026,
  binario `5f0be589`, ed era l'ultimo residuo nostro dei tre episodi.
  Episodio delle 12:30: 10:30:11.698 la pagina si congeda (`motivo=0x01`, scheda chiusa) → 10:30:11.798
  **noi stessi** scriviamo «PING del trasporto spenti: la sessione è finita, **non c'è più niente da
  tenere vivo**» → 10:30:12.199 spediamo la capsula di chiusura → e poi teniamo aperta la connessione
  QUIC, spedendo 2 pacchetti ogni secondo o due a un browser che non c'è più, finché a 10:30:22.330
  esce un ⛔ **LINEA MORTA** che si legge come un guasto del prodotto.
  ⚠ Quando invece è il client a mandare il `CONNECTION_CLOSE` la connessione se ne va in **9 ms**
  (10:39:11.675 congedo → 10:39:11.684 «connessione chiusa»): il comportamento dipende dal client, e
  Chrome che esce non saluta a livello QUIC.
  ⇒ Il guardiano è `linea_morta_giudica()` (`src/webtransport.c`): si fermava su `!w->rcp ||
  w->chiusura >= 0`, **ma non guardava lo stato `"finita"`** — lo stesso stato su cui
  `regola_tienila_viva()` (`src/webtransport.c`) spegne i PING. ⛔ `w->rcp` non si azzera al
  congedo: lo azzera solo `wt_stream_chiuso()`, cioè il CLIENT che chiude lo stream — e un browser
  che esce non lo chiude mai. ⇒ **Cura: una riga, `if (rcp_e_finita(w->rcp)) return;`**.

  ⭐ **Delle due strade possibili è stata scelta la prima, e la seconda è stata rifiutata con le
  ragioni in chiaro.** Chiudere la connessione QUIC quando se ne va l'ultima sessione sarebbe parso
  più onesto, ma «sessione finita, connessione ancora viva» è uno stato **previsto due volte in
  questo stesso file**, e tutt'e due le volte la scelta fu liberare il POSTO e lasciare il trasporto
  in piedi: `fin_dal_client()` («la pagina che chiude la parte scrivente del canale e tiene viva la
  connessione») e `chiusa_dal_client()` («il posto si lascia adesso … aspettare lo smontaggio del
  trasporto vuol dire tenerlo occupato addosso a chi si ricollega subito»). E `wt_stream_chiuso()`
  rimette `w->sessione` a `-1` apposta perché una sessione nuova possa aprirsi lì sopra. ⇒ La
  seconda strada disferebbe una decisione presa due volte; la prima non è un cerotto, è **il
  commento che c'era già che diventa vero**. E lo spreco non c'è: i PING sono già spenti, e il
  trasporto se ne va da solo col `max_idle_timeout` di 30 s (`src/trasporto.c`).

  `[M]` **23 set 2026, scatola `gnome` (8511), binario `5f0be589`, Chrome 153 VERO headless** — due
  giri identici con **una sola differenza**: se il client saluta prima di sparire.
  ⭐ `5f0be589` è il binario che in questo momento gira su **tutte e tre** le scatole (`md5sum
  /proc/<pid>/exe` su gnome, kde e xfce), e contiene **tutte e tre** le cure di stamattina: `7e0c0e2`
  (il fotogramma già codificato paga la chiave), `f5527c2` (la chiave si chiede quando nasce il
  debito) e questa. Il server della scatola gnome è nato alle 05:06:34 UTC, cioè **prima** dei due
  giri qui sotto, e in tutto il suo registro c'è **esattamente una** riga `linea-morta`: quella del
  giro B.

  | giro | che cosa fa il client | linea morta | come finisce la connessione |
  |---|---|---|---|
  | **A** | `about:blank` (⇒ congedo `0x01` «la scheda è stata chiusa») e **300 ms dopo `SIGKILL`** — niente `CONNECTION_CLOSE`, come Chrome il 22 set | ⭐ **NESSUNA**, in 30 s di silenzio | 05:08:12.276 «**trenta secondi di silenzio, staccato (§2.2)**» — un motivo VERO al posto di un allarme falso |
  | **B** | **`SIGKILL` e basta**, con la sessione ATTIVA | ⛔ **SCATTA**, `causa=silenzio silenzio_ms=10017 prove=13` | 05:08:42.064, la connessione si chiude come deve |

  ⇒ La cura toglie **solo** il falso positivo: chi muore non saluta, e il guardiano lo prende ancora.
  In A il registro percorre tutta la sequenza del 22 settembre — congedo 05:07:41.775, PING spenti
  05:07:41.875, capsula 05:07:42.276, `ricevuti` fermo a 40 per 30 s — e **non scrive nessun ⛔**.
  ⚠⚠ **E IL PREZZO DELLA CURA, DICHIARATO invece che scoperto dopo.** La linea morta, sbagliando,
  faceva anche una cosa utile: chiudendo la connessione a +10 s fermava **il palco**. Il registro lo
  dice in tutt'e due i casi — 22 set, congedo 10:30:11.698 → «il palco smette di catturare»
  10:30:22.330 (**+10,6 s**); 23 set col binario curato, congedo 05:07:41.775 → «il palco smette di
  catturare» 05:08:12.276 (**+30,5 s**, cioè al `max_idle_timeout`). ⇒ La finestra in cui **si
  cattura e si codifica per nessuno** passa da ~10 s a ~30 s.
  ⭐ Sul desktop fermo della prova costa niente (11 fotogrammi in tutto), ma su una scena viva a 58
  fotogrammi/s sono **venti secondi di codifica in più per ogni client che se ne va**, su una
  macchina che ha altri inquilini. La misura sotto carico è nella sessione lunga.

- ⏳ **Il palco smette di catturare quando muore il TRASPORTO, non quando il client si CONGEDA** —
  23 set 2026, trovato curando la linea morta. Al congedo liberiamo il posto (`posto LASCIATO …
  occupati adesso: 0`) ma **non** spegniamo la cattura: quella si ferma solo quando se ne va la
  connessione QUIC. Nel mezzo ogni fotogramma viene catturato, codificato, offerto, **rifiutato** da
  `rcp_video_apri()` (`src/rcp.c`, `RCP_VIDEO_PRIMA_DI_SESSIONE`) e messo a verbale come
  `⛔ NIENTE VIDEO: «SESSIONE» non è stata spedita (stato finita)`.
  ⇒ È lavoro fatto per nessuno **e** una riga ⛔ che somiglia a un guasto. 🔸 La cura sensata è
  spegnere il ciclo dei fotogrammi sullo stesso evento che libera il posto — ⚠ ma va guardata contro
  I4 («il palco resta in piedi»), che è un'altra cosa: fermare la *cattura* non è smontare il palco.

- ✅ **LA RETE DOPO LA CURA DEI FANTASMI È GIRATA** — 22 set 2026, `--famiglia tutto --scatola "gnome kde
  xfce"`, binario `defc5ad5`: **nessun rosso**, 13 506 s, C14 compreso (sole e insieme, stessa impronta).
  ⚠ La rete usa il cliente Python, non un browser: il blocco del video in **Firefox** qui sotto NON lo
  vede. ✅ E `13-w4` **è diventato una maglia fissa della rete** — 23 set 2026, vedi `C20` qui sotto.
- ✅ **LA RETE SPORCA LE SCATOLE: adesso è un VERDETTO** — chiuso il 23 set 2026. La sgomberata era
  già fatta (22 set, `08172a6`, `d0406fd`): il **gancio** sgombera dopo ogni maglia, sullo spazio di
  nomi della rete (utenti, home, unità `user@` fallite, orfani di `/tmp`); la scena si lancia con
  `setsid`; C3 ferma solo il processo del prodotto e non più il browser.
  ⭐ Mancava il giudizio, ed è **C19** (`banchi/11-scatole/11-c19-la-scatola-resta-pulita.py`,
  `la_scatola_resta_pulita` nel gancio, **ultima maglia di ogni scatola** in `tutto` e in
  `desktop-nuovo`): *«a fine giro non sopravvive nessun inquilino della rete»*. Prima la sporcizia era
  una riga `inf` annotata `riuscita=true`, cioè ⛔ la rete poteva lasciare venti inquilini dentro una
  scatola e dirsi verde lo stesso.
  ⭐⭐ **L'insidia di `nictest` è risolta contando per NOME, non per uid.** `bilancio` conta
  `uid>=1000` escluso il solo `provanic` ⇒ per lui `nictest` è un inquilino; C19 conta sullo **spazio
  di nomi della rete** (`^c[0-9]+b?u[0-9]+$`, lo stesso di `sgombera_inquilini`) ⇒ `nictest`,
  `provanic` e gli utenti di sistema non ci cascano dentro **per forma**, non per una lista di
  eccezioni. I due restano diversi apposta: `bilancio` è una misura per chi diagnostica, C19 è il
  giudizio.
  ⚠ Giudica **U** (utenti), **C** (case rimaste, cioè il `userdel` senza `-r`) e **P** (processi);
  unità `user@` fallite orfane e orfani di `/tmp` restano **rilievo**, non verdetto — sono la
  spazzatura degli inquilini, non gli inquilini, e un rosso perpetuo per un file in `/tmp` sarebbe un
  interruttore che qualcuno spegne (§1.49). Chi vuole misurarli lo chiede: `--anche-lo-sporco`.
  `[M]` 23 set 2026, binario `9b5df38b`, scatole **kde** e **xfce**: giro sano **VERDE** su tutt'e due
  (0 inquilini, 0 case, 0 processi; rilievo kde 8 unità fallite · 0 orfani, xfce 10 · 49), e i **due**
  guasti innestati **VISTI** su tutt'e due — `--lascia-un-inquilino` (U·C·P rossi) e
  `--lascia-una-casa` (solo C rosso: ⭐ il residuo che nessun `pgrep` e nessun `getent` vedrebbero).
  ⚠ E un rilievo che la maglia stampa e nessuno guardava: in kde c'era `occhio2`, in xfce `corrx1` e
  `corrx2` — inquilini di altri banchi **fuori** dallo spazio di nomi, quindi né sgomberati dal gancio
  né contati da C19. 🔸 I banchi nuovi diano ai loro inquilini un nome `c<n>u<n>`, come fa C20.
- ✅ **`13-w4` È DIVENTATO C20, MAGLIA FISSA DELLA RETE** — 23 set 2026.
  `banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py`, dentro `le_cinque_nuove` (cioè in
  `tutto` e in `desktop-nuovo`), col cancello delle capacità: vuole l'**immagine**.
  Sorveglia il difetto che l'utente ha trovato il 22 set su KDE con Chrome — dopo «Esci» e un nuovo
  accesso lo schermo alternava desktop, schermata d'uscita e nero — e che `src/codificatore.c`
  descrive come *«un'immagine VECCHIA, senza nessun errore»*: ⛔ proprio perché non c'è errore, se ne
  accorge solo chi **guarda**.
  ⭐ Entrando nella rete ha preso tre cose che da banco di una sera non aveva:
  (1) **il guasto innestato** `--scena-che-lampeggia` (senza, il giorno che il giudice smettesse di
  guardare direbbe verde per sempre); (2) **non sa più che cosa sia Plasma** — nascita e fine della
  sessione le legge dal registro del prodotto (`formato negoziato`, `la sessione grafica … E' FINITA`)
  e il gesto «Esci» se lo cerca con la stessa domanda di `src/sessione.c` (`org.kde.Shutdown` ·
  `org.gnome.SessionManager` · `xfce4-session-logout`); (3) l'inquilino si chiama **`c20u<n>`**,
  dentro lo spazio di nomi della rete, così il gancio lo sgombera e C19 lo vede.
  ⛔⛔ **E ha dovuto mettere lei una scena, come C3** — è la misura che ha riscritto la maglia. A
  desktop fermo, nel secondo accesso: **kde 1 800 fotogrammi in 45 s** (KWin consegna sempre),
  **xfce 7 in 60 s** (labwc, come ogni wlroots, consegna solo sul danno) ⇒ su xfce e lxqt la maglia
  sarebbe stata **3 per sempre**. La cura è `banchi/11-scatole/11-c20-scena.html`: una banda scura che
  scorre su fondo chiaro, **due** bande a 100 punti di distanza così che in vista ci sia sempre
  esattamente il 20 % di scuro ⇒ ⭐ ogni fotogramma è diverso (c'è danno, quindi consegna) **e la
  luminanza media non si muove**. `[M]` misurata: **156**, e un **solo valore distinto** su 2 166
  fotogrammi.
  `[M]` 23 set 2026, binario `9b5df38b`, con la scena dichiarata:

  | | giro sano | guasto innestato (`--scena-che-lampeggia`) |
  |---|---|---|
  | **kde** | ⭐ VERDE (esito 0) — 4 332 fotogrammi, coda 2 166, **0 salti**, luminanza **156**, 1 valore distinto; cache: 4 superfici buttate | ⭐ VISTO (esito 0) — **762 salti** su una coda di 2 167, 26 valori distinti (14…234) |
  | **xfce** | ⭐ VERDE (esito 0) — 4 454 fotogrammi, coda 2 227, **0 salti**, luminanza **156**, 1 valore distinto; cache: 5 superfici | ⭐ VISTO (esito 0) — **766 salti** su una coda di 2 229, 25 valori distinti |

  ⚠ Due insidie trovate mentre si certificava, e tutt'e due erano del BANCO:
  (a) il browser non dipingeva perché `/tmp/mozilla` era di un altro inquilino — è la cura della
  provvista che C3 paga dal 27 agosto, e adesso C20 la chiama (⛔ non se ne fa una copia);
  (b) il controllo «lo schermo è nero» stava **prima** di quello sul lampeggio ⇒ la scena di C3, che
  è scura (mediana 17), faceva uscire **3** invece che rosso. ⭐ Uno schermo che alterna non è mai
  ambiguo, per quanto scuro: è il nero **fermo** che non si distingue da un'immagine congelata.
- ⏳ **La rete non guarda i browser veri sotto carico** — 22 set 2026, e per questo la spirale della
  chiave è passata: la rete usa il cliente Python, e `12-client-veri.py` prova Firefox e Chrome veri
  per **8 s a desktop fermo**. 🔸 Serve un giro con un video a schermo intero per minuti, coi contatori
  della pagina (`video consegnati→dipinti`, `buchi`) come giudizio.
- ⏳ **Chrome Android** su XFCE: la validazione è dell'utente.
- ✅ **I gruppi `video`/`render` su TUTTI i desktop** — chiuso il 22 set 2026, e la cura non serviva:
  il codice che iscrive (`src/figlio.c`, `iscrivi_ai_gruppi_della_scheda`) sta nel **padre**, gira da
  root dopo PAM e **prima del `fork`** ⇒ non sa nemmeno quale compositore nascerà, e vale su ogni
  desktop. Era **misurato** solo su kde, non fatto solo per kde.
  `[M]` 22 set 2026, inquilini creati SENZA gruppi, browser **veri** e finestra vera: gnome Firefox 140
  **PASS** · Chrome 153 **PASS**; xfce Firefox **PASS** · Chrome **PASS**. In tutti e quattro il
  registro dice «PRIMA CONNESSIONE … ce lo METTO io» e poi «è nei gruppi della scheda … può vedere in
  hardware», `id -nG` passa da «solo se stesso» a «video render», e il primo fotogramma arriva in
  0,6–1,6 s. (kde era già `[M]` il 20 set, `DECISIONI.md` §7.21.)
  ⭐ **E adesso la rete lo guarda**: maglia **C18** «i gruppi della scheda li mette il prodotto»,
  l'unica che NON chiama `garantisci_i_gruppi` — tutte le altre glieli mettono da sé e così
  **nascondevano** quel pezzo di prodotto. Guasto innestato `--senza-usermod` (si nasconde `usermod`
  per la durata del giro, e si rimette sempre): `[M]` VERDE e guasto VISTO su gnome e xfce.
- ⏳ ⛔ **PRIMA DI LXQt, le prove a mano dell'utente** — chiesto il 21 set 2026: nelle tre scatole
  gnome, kde e xfce ci sono Firefox, un terminale e un gestore di file (già negli strati), e
  l'inquilino **`nictest`** (parola `nictest`, nel gruppo `sudo`), nuovo ultimo strato delle tre
  ricette. ⭐ `[M]` 21 set 2026, sera: immagini rifatte, `nictest` in `sudo video render` nelle tre
  scatole, `sudo` risponde, e Firefox entra come `nictest` su **8511 · 8512 · 8513**: PASS su tutti e
  tre. ⏳ Restano le prove dell'utente.
- ✅ **«Cambia utente»** — ⭐ DECISO dall'utente il 21 set 2026, sera: esce **su tutti i desktop**,
  resta solo «Esci». `[M]` binario `eb327ffd`: XFCE `-switch-user` nel pannello e
  `ShowSwitchUser=false`; GNOME `disable-user-switching=true` con `always-show-log-out=true`; KDE
  già dalla fase 12. ⭐ `[M]` rete **gnome+xfce** (ridotta per decisione dell'utente: KDE non passa dal codice toccato), innesco `fase13-cambia-utente`, 9 275 s: **GNOME 27/27 · XFCE 27/27 · guasti 26/26 visti**, C10 C12 C15 C16 verdi sul portatile.
- `[?]` **La sessione del prodotto è `closing` dalla nascita**, su ogni desktop («logged out.
  Waiting for processes to exit» nel giornale subito dopo «New session»). Non è di questa fase né
  una regressione (GNOME è uguale), ma con `KillUserProcesses=yes` logind potrebbe trattarla da
  sessione finita. ⇒ Da guardare in una fase sua.
- `[?]` Le scelte 2, 3, 4, 6, 7 della tabella sopra sono state **affrontate nel codice** dagli
  incrementi (ridimensionamento acceso, bus d'utente, vitalità dai fatti di `/proc` e del bus) e
  vanno rilette con l'utente, non date per decise.

## Il giudizio dell'utente
