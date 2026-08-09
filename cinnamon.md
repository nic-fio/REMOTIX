# Cinnamon e Muffin — studio del codice, per il quinto desktop

*Scritto il 9 agosto 2026, su `muffin` e `cinnamon` **6.7.4** (cloni del giorno stesso).*

> ## ⛔ Tutto quel che segue è `[R]`. Nulla è misurato.
>
> Questo studio è stato fatto **leggendo il codice**, e vale quel che vale una lettura: dice che
> cosa il compositore *può* fare, non che cosa *fa* sulla nostra macchina. È la lezione che
> `LEZIONI.md` §1.11 e il riquadro di §3 hanno già pagato su KDE — dove la lettura diceva GPU e
> la prima misura diceva software, e ad avere ragione era il codice **ma solo dopo che la misura
> era stata rifatta**.
>
> Le ricerche negative di questo documento (*«X non esiste»*) sono state fatte con lo strumento
> **certificato su Mutter prima dell'uso**: la prima ricerca cercava in `src/`, non trovava
> `RecordVirtual` nemmeno in Mutter — dove c'è — perché Mutter recente tiene gli XML in
> `data/dbus-interfaces/`. Con il percorso corretto il controllo positivo passa, e solo allora
> l'assenza su Muffin significa qualcosa. È `LEZIONI.md` §1.9, presa sul fatto.

---

## 1. In due minuti

**Cinnamon sta a Muffin esattamente come gnome-shell sta a Mutter**: il binario `cinnamon` *è* il
compositore — chiama `meta_get_option_context()`, `meta_plugin_manager_set_plugin_type()`,
`meta_init()` e `meta_run()` (`cinnamon/src/main.c:327-418`). Non è un'analogia: è la stessa
architettura, con i nomi cambiati.

Da cui la buona notizia e la cattiva, che sono la stessa cosa vista da due lati.

⭐ **La buona**: metà di `gnome.md` si trasferisce senza tradurre. `org.cinnamon.Muffin.ScreenCast`
e `org.cinnamon.Muffin.RemoteDesktop` sono le interfacce di Mutter rinominate, la cattura passa da
PipeWire come là, e **non c'è nessun cancello sul permesso** — `check_permission()` verifica solo
che chi chiama sia lo stesso che ha creato la sessione (`meta-screen-cast-session.c:196-201`),
esattamente come Mutter e al contrario di KWin.

⛔ **La cattiva**: il fork si è staccato dal *backend* di Mutter parecchi anni fa, e tre cose che
REMOTIX dà per acquisite **non ci sono affatto**.

| Cerchiamo | In Mutter | In Muffin 6.7.4 |
|---|---|---|
| `RecordVirtual` — creare uno schermo virtuale | ✅ `data/dbus-interfaces/…ScreenCast.xml` | ⛔ **0 file** su tutto l'albero |
| `virtual_monitor` — il monitor virtuale nel backend | ✅ 22 occorrenze in `meta-monitor-manager.c` | ⛔ **0 file** |
| `ConnectToEIS` — l'input via libei | ✅ `…RemoteDesktop.xml`, `…InputCapture.xml` | ⛔ **0 file** |
| `EnableClipboard` — gli appunti della sessione remota | ✅ `…RemoteDesktop.xml` | ⛔ **0 file** |
| un backend *headless* | ✅ modo del backend nativo | ⛔ `headless` compare **solo in `src/tests/`** |

E il paradosso che spiega tutto: **i protocolli Wayland di Muffin sono aggiornatissimi** —
`cursor-shape`, `single-pixel-buffer`, `xdg-dialog`, `xdg-toplevel-icon`, `xdg-toplevel-tag`,
`pointer-warp`, roba del 2024-2025. Mint tiene il passo sul lato *client* di Wayland e **non ha
mai portato l'evoluzione del backend remoto di Mutter**. Il risultato è un compositore moderno
con un'API di desktop remoto ferma a circa Mutter 41.

**Il verdetto provvisorio**: Cinnamon non è escluso, ma **non è servibile con il codice che
abbiamo**, e la sua fattibilità dipende da una misura sola, descritta in §3.3. Finché quella non
è fatta, ogni giudizio è `[?]`.

---

## 2. La mappa

| Dove | Che cosa |
|---|---|
| `muffin/src/backends/` | la parte che ci interessa, gemella di quella di Mutter |
| `muffin/src/org.cinnamon.Muffin.{ScreenCast,RemoteDesktop,DisplayConfig,IdleMonitor}.xml` | le interfacce D-Bus — ⚠ ancora in `src/`, mentre Mutter le ha spostate in `data/dbus-interfaces/` |
| `muffin/src/backends/meta-monitor-manager-dummy.c` | ⭐ **il pezzo che decide tutto**, vedi §3 |
| `muffin/src/backends/native/` | il backend KMS |
| `muffin/src/backends/x11/nested/` | il backend annidato in X11 |
| `cinnamon/src/main.c` | il plugin che *è* il desktop |
| `cinnamon/cinnamon-wayland.session.in` | la sessione |

---

## 3. ⛔ La domanda che decide: lo schermo virtuale

È la domanda 5 di `LEZIONI.md` §3, ed è quella che su KDE è costata più di tutte.

### 3.1 La via di Mutter non esiste

`org.cinnamon.Muffin.ScreenCast` espone **due soli metodi di registrazione**:

```
RecordMonitor (connector, properties) → stream_path
RecordWindow  (properties)            → stream_path
```

Niente `RecordVirtual`, niente `RecordArea`. E non è un XML rimasto indietro rispetto al codice:
`virtual_monitor` non compare in **nessun file** dell'albero, XML compresi.

Quindi la strada di `gnome-remote-desktop` — *creo uno schermo che non esiste e ci catturo sopra*
— su Cinnamon **non c'è**.

### 3.2 I tre backend, e perché nessuno è headless

`calculate_compositor_configuration()` (`muffin/src/core/main.c:434-496`) ne sceglie uno di tre:

| Opzione | Backend | Che cosa serve |
|---|---|---|
| `--wayland` / `--display-server` | `META_TYPE_BACKEND_NATIVE` | un dispositivo DRM con un'uscita **vera** |
| `--nested` | `META_TYPE_BACKEND_X11_NESTED` | un server X in cui annidarsi |
| (nessuna) | X11 compositing manager | un server X |

**Non esiste `--headless` e non esiste `--virtual-monitor`.** Il backend nativo non ha nemmeno
l'enumerazione dei modi che in Mutter distingue `DEFAULT` da `HEADLESS`.

### 3.3 ⭐ Ma c'è un monitor fittizio, e due variabili d'ambiente che lo comandano

È il pezzo che salva lo studio, ed è la ragione per cui Cinnamon non va dichiarato fuori scope.

`meta_backend_create_monitor_manager()` (`muffin/src/backends/meta-backend.c:804-812`):

```c
static MetaMonitorManager *
meta_backend_create_monitor_manager (MetaBackend *backend, GError **error)
{
  if (g_getenv ("META_DUMMY_MONITORS"))
    return g_object_new (META_TYPE_MONITOR_MANAGER_DUMMY, NULL);

  return META_BACKEND_GET_CLASS (backend)->create_monitor_manager (backend, error);
}
```

⭐ **Quel controllo sta nella classe base, prima della chiamata virtuale**: `META_DUMMY_MONITORS`
scavalca la scelta di **qualunque** backend, nativo compreso.

E la misura di quello schermo finto si detta da fuori
(`meta-monitor-manager-dummy.c:148-175`, `:403-431`):

| Variabile | Effetto |
|---|---|
| `MUFFIN_DEBUG_DUMMY_MODE_SPECS` | i modi, come `1920x1080@60`, più d'uno separati da `:` |
| `MUFFIN_DEBUG_NUM_DUMMY_MONITORS` | quanti schermi |
| `MUFFIN_DEBUG_DUMMY_MONITOR_SCALES` | le scale |
| `MUFFIN_DEBUG_TILED_DUMMY_MONITORS` | schermi affiancati |

**È l'equivalente funzionale del `--virtual --width W --height H` di KWin**: la misura del desktop
si decide **all'avvio del compositore** e non si cambia più a sessione viva — che è esattamente il
vincolo di KDE, e che il modello della tela di `DECISIONI.md` §5.0 già assorbe.

### 3.4 ⛔ Le due strade, e quale va misurata per prima

**Strada (A) — nativo + monitor fittizio.** `META_DUMMY_MONITORS=1
MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60 cinnamon --wayland --replace`.
Se regge, Cinnamon gira **senza X e senza monitor**, e il costo per REMOTIX crolla.

⚠ **Ma è precisamente il tipo di deduzione che `LEZIONI.md` §1.11 vieta di dare per buona.** Che
il gestore dei monitor sia finto non dice che il *renderer* lo sia: il backend nativo disegna via
KMS e vuole dei CRTC su cui presentare, e con schermi inventati quei CRTC non ci sono. Può
funzionare, può fallire all'avvio, e **può funzionare consegnando zero fotogrammi** — che è il
modo peggiore, perché sembra riuscito.

**Strada (B) — annidato in Xvfb.** `--nested` usa il monitor fittizio **per costruzione**
(`meta-backend-x11-nested.c:57-60`): è la sua unica implementazione di `create_monitor_manager`.
Quindi la (B) funziona quasi certamente, al prezzo di un server X in più nella pila e,
verosimilmente, di **GL software** (llvmpipe) — cioè il desktop intero disegnato in CPU, che
`LEZIONI.md` §3 domanda 4 considera discriminante per dire se un desktop è servibile su una
macchina da server.

> ## Il piano: si misura (A), e (B) è il ripiego
>
> La (A) è il premio e la (B) è la rete di sicurezza. **La misura si fa nell'ordine
> (A) → (B)**, e la (A) non si dichiara riuscita perché il processo sta in piedi: si dichiara
> riuscita quando `misura-cattura` (in `v1/banchi/banco-compositori/`) conta fotogrammi su una
> scena dichiarata e sempre in movimento. È `LEZIONI.md` §1.1 e §3.2 di `CODER.md`.

---

## 4. La cattura: la parte che funziona

**Pienamente implementata**, e con la stessa struttura di Mutter:
`meta-screen-cast-monitor-stream-src.c`, `meta-screen-cast-window-stream-src.c`,
`handle_record_monitor()` a `meta-screen-cast-session.c:299`.

✅ **Nessun cancello.** `check_permission()` confronta il nome D-Bus di chi chiama con quello che
ha creato la sessione — è un controllo di proprietà, non di autorizzazione. Nessun polkit, nessun
portale, nessun campo in un file `.desktop`. Su questo Cinnamon sta con GNOME e wlroots, **non**
con KDE.

`[?]` **Quel che non si può leggere**: quanti fotogrammi consegna, se il buffer arriva già
disegnato, se il cursore finisce dentro l'immagine, quanto costa la risoluzione. Su Mutter erano
37 al secondo `[M]`; su Muffin **non c'è ragione di supporre lo stesso numero**, perché il
percorso di rendering è quello che è cambiato di più fra i due — ed è esattamente la deduzione
che §1.11 vieta.

---

## 5. L'input: un salto indietro di due anni

`org.cinnamon.Muffin.RemoteDesktop` espone i vecchi metodi di notifica:

```
NotifyKeyboardKeycode · NotifyKeyboardKeysym
NotifyPointerButton · NotifyPointerAxis · NotifyPointerAxisDiscrete
NotifyPointerMotionRelative · NotifyPointerMotionAbsolute
NotifyTouchDown · NotifyTouchMotion · NotifyTouchUp
```

⛔ **Niente `ConnectToEIS`**, quindi **niente libei** — e `v1/remotix-c/src/input.c` (906 righe) è
scritto per libei, deciso il 4 agosto 2025 chiudendo la fase 3 di v1.

Le tre conseguenze:

1. **serve un secondo percorso di input**, quello D-Bus, che v1 aveva scritto *prima* di passare
   a libei e che non è sopravvissuto nel codice attuale;
2. ⭐ **`NotifyKeyboardKeysym` esiste**, e vale la pena notarlo alla luce di `DECISIONI.md`
   §5-bis.6: qui il *simbolo* si può iniettare direttamente, senza cercare quale tasto lo
   produca. Non cambia la decisione — la regola resta «le lettere viaggiano come lettere» — ma su
   Cinnamon il lato server costa meno;
3. ⚠ **e c'è `zwp_virtual_keyboard_v1`** fra i protocolli Wayland, che sarebbe una terza strada.
   `[?]` Da valutare solo se la seconda si rivelasse insufficiente: §0.1 di `DECISIONI.md` dice di
   non collezionare percorsi.

`[?]` **Non letto, e va letto prima di scrivere**: se `NotifyPointerMotionAbsolute` accetti un
riferimento allo *stream* come su Mutter, e come si comporti con il monitor fittizio.

---

## 6. ⛔ Gli appunti: qui la strada non c'è proprio

È il buco peggiore, e non ha un ripiego evidente.

| Via | Su Cinnamon |
|---|---|
| `EnableClipboard` sull'oggetto RemoteDesktop (la via di GNOME) | ⛔ **0 occorrenze**: l'API è precedente all'aggiunta della clipboard in Mutter |
| `zwlr_data_control_manager_v1` (la via di KDE, XFCE e LXQt) | ⛔ **assente** dai protocolli di Muffin |
| `ext_data_control_v1` | ⛔ assente |

Quindi **nessuno dei due file che abbiamo serve**: né `appunti_mutter.c` (450 righe), né
`appunti_wlr.c` (796), che insieme coprono tutti e quattro gli altri desktop.

`[?]` **Le vie residue, tutte da verificare e nessuna gradevole**: fare il client `wl_data_device`
ordinario — ma la clipboard di Wayland richiede il fuoco, e una sessione non presidiata non ce
l'ha; passare da XWayland; o contribuire a monte. **La terza è probabilmente la sola sensata**, ed
è la stessa conclusione a cui `kde.md` §8.2 era arrivato per il ridimensionamento.

⚠ Da mettere in conto nella decisione «Cinnamon dentro o fuori»: `DECISIONI.md` §5-ter mette la
clipboard bidirezionale fra le funzioni promesse. **Su Cinnamon oggi non è servibile.**

---

## 7. Che cosa si trasferisce da `gnome.md`, e che cosa no

| Argomento | Si trasferisce? |
|---|---|
| l'architettura ScreenCast/PipeWire | ✅ **sì, quasi alla lettera** |
| l'assenza di cancello sul permesso | ✅ sì |
| il ciclo di vita della sessione D-Bus | ✅ probabilmente `[?]` |
| **la revoca al blocco schermo** (`inhibit_remote_access`) | `[?]` **da verificare**, ed è importante: se c'è, vale la stessa cura di `DECISIONI.md` §4.3 |
| `RecordVirtual` e il monitor virtuale | ⛔ no, non esistono |
| libei e `ConnectToEIS` | ⛔ no |
| la clipboard | ⛔ no |
| il lockdown via `org.gnome.desktop.lockdown` | `[?]` Cinnamon ha il proprio albero di impostazioni |

---

## 8. Le quattordici domande di `LEZIONI.md` §3, colonna Cinnamon

| # | Domanda | Cinnamon / Muffin 6.7.4 |
|---|---|---|
| 1 | Come si chiede la cattura senza portale? | ✅ D-Bus `org.cinnamon.Muffin.ScreenCast` — gemella di Mutter `[R]` |
| 2 | Spinge i fotogrammi o li fa tirare? | ✅ spinge, PipeWire `[R]` |
| 3 | È dietro un permesso? | ✅ **no** — solo controllo di proprietà `[R]` |
| 4 | Senza monitor, disegna sulla GPU? | ⛔ `[?]` **la domanda che decide** — vedi §3.4. Sulla strada (B) quasi certamente **no** |
| 5 | Si può chiedere uno schermo virtuale della misura voluta? | ⛔ **no** via protocollo; ⭐ **sì** via `META_DUMMY_MONITORS` + `MUFFIN_DEBUG_DUMMY_MODE_SPECS`, all'avvio `[R]` |
| 6 | Quanti fotogrammi consegna? | `[?]` **non deducibile da Mutter** |
| 7 | La cadenza dichiarata come si comporta? | `[?]` |
| 8 | Fotogrammi interi o «diff»? | `[?]` |
| 9 | Il buffer arriva già disegnato? | `[?]` |
| 10 | Che cosa costa la risoluzione? | `[?]` |
| 11 | Che cosa costa la profondità di colore? | `[?]` |
| 12-bis | Il cursore è dentro l'immagine catturata? | `[?]` — e con `DECISIONI.md` §5-bis.2 è **obbligatorio** saperlo |
| 13 | Uno schermo virtuale si ridimensiona a caldo? | ⛔ **no** `[R]`: la misura è nell'ambiente all'avvio, come su KDE |
| 14 | La clipboard di chi è? | ⛔ **di nessuno raggiungibile** — vedi §6 |

**Undici domande su quattordici restano `[?]`**, contro le undici su undici che lo studio di KDE
aveva chiuso leggendo. Non è pigrizia dello studio: è che su KDE le risposte stavano nel codice,
e qui le tre che contano stanno in un'esecuzione.

---

## 9. Il piano di misure, in ordine

Il minimo per decidere «dentro o fuori». Serve una macchina con Cinnamon 6.7 e i banchi di
`v1/banchi/banco-compositori/`.

| # | Che cosa | Come si dichiara riuscita |
|---|---|---|
| **M1** | strada (A): `META_DUMMY_MONITORS=1 MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60 cinnamon --wayland` da SSH, senza monitor | il compositore sta in piedi **e** `RecordMonitor` apre uno stream **e** `misura-cattura` conta fotogrammi > 0 su scena in movimento. Tre condizioni, non una |
| **M2** | se M1 fallisce: strada (B), `--nested` dentro Xvfb | idem |
| **M3** | i fotogrammi al secondo consegnati, con scena dichiarata | il numero, confrontabile con Mutter 37 / KWin 60 / wlroots 61 |
| **M4** | rende in GPU o in software? | ⚠ **non** «ha aperto un render node» (§1.11): si guarda il tipo di buffer che lo stream riesce a offrire, **dopo** aver chiesto DMA-BUF |
| **M5** | il cursore è dentro l'immagine? | si guarda un fotogramma |
| **M6** | il blocco schermo revoca la cattura, come su GNOME? | si blocca e si guarda se lo stream muore |

⛔ **M1 non si dichiara riuscita perché il processo non è morto.** È la forma d'errore E1: una
condizione necessaria presa per sufficiente.

---

## 10. Il conto per REMOTIX

**Quel che si riusa**, se M1 o M2 passano: la struttura della cattura (`cattura.c`), il ciclo di
sessione D-Bus, e il modello della tela di `DECISIONI.md` §5.0 — che assorbe già il vincolo
«la misura si decide all'avvio», perché lo assorbiva per KDE.

**Quel che va scritto nuovo**, e non è poco:

| | Costo |
|---|---|
| un `cinnamon.c` accanto a `mutter.c` e `kwin.c` | medio — è Mutter con altri nomi |
| **un secondo percorso di input**, D-Bus invece di libei | ⚠ **alto**: è la fase 4 di v1 rifatta |
| **gli appunti**, che oggi non hanno strada | ⛔ **aperto** — vedi §6 |

**Il giudizio, dichiarato come provvisorio:** Cinnamon è il desktop che costa **più di tutti** fra
i cinque, e le sue due difficoltà — l'input e la clipboard — non sono difficoltà di lettura ma
funzionalità mancanti a monte. Non va dichiarato fuori scope, perché M1 potrebbe cambiare il
conto; ma va messo **ultimo**, dopo che gli altri quattro funzionano, e la decisione va presa
sulle misure di §9 e non su questo documento.

⚠ **E se M1 e M2 fallissero entrambe**, Cinnamon non è servibile affatto — non per una nostra
mancanza, ma perché un compositore che non sa disegnare senza uno schermo non può servire una
sessione remota. In quel caso la voce si chiude, con la misura accanto.
