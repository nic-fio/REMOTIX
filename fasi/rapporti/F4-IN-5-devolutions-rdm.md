# F4-IN-5 — Devolutions RDM per Android, e il suo parente aperto FreeRDP

Anello di studio, 14 agosto 2026. Marche: `[M]` misurato da noi · `[R]` letto in un sorgente
altrui, con file e riga · `[S]` letto in una specifica o in una fonte dichiarata · `[?]` ipotesi
non verificata.

---

## ⭐⭐ Il verdetto, in tre righe

1. **Il mandato è REFUTATO, e a refutarlo è RDM stesso.** RDM per Android ha, dal 21 ottobre 2024,
   un'impostazione che si chiama **«Use Pointer Capture»**, sotto la voce **«Interactive Method»**
   `[S]`. La cattura del puntatore è **esattamente** la cosa che una pagina web su Android **non
   può fare**: `[R]` su Chrome per Android la Pointer Lock **non esiste** (`crbug/153419`, il dato
   di compatibilità è stato corretto per dirlo). ⇒ Non è «RDP disegna il cursore»: **è che RDM è
   un'applicazione nativa e noi no.**
2. ⭐⭐ **La riga che vale il rapporto**, e va in `DECISIONI.md` come **vincolo di prodotto**:
   > **Su Android, dentro un browser, non possiamo prendere il controllo del puntatore.** Niente
   > movimenti relativi, niente cursore di sistema nascosto e sostituito col nostro, niente
   > puntatore confinato nella tela. Un'app nativa lo fa con **una** chiamata
   > (`View.requestPointerCapture()`, da Android 8) e **RDM quella chiamata ce l'ha**.
   ⇒ La strada «disegniamo noi il puntatore» (punto-di-ripresa §5) **è chiusa, e adesso ha un
   movente, non solo una correlazione.**
3. ⚠ **E il controesempio va ridimensionato, con le parole del venditore.** L'ingegnere di
   Devolutions, ad aprile 2026, su mouse Bluetooth e schermo esterno: *«**The implementation is a
   bit janky and could benefit from some rework**»* `[S]`. Il *«funziona molto bene»* dell'utente
   è vero **su DeX**, e il motivo lo dice lo stesso ingegnere: *«su DeX funziona meglio perché **lo
   schermo esterno è trattato come un desktop pienamente indipendente**»* `[S]`. ⇒ **Il merito è
   di DeX, non di RDM.**

---

## 0 · Le fonti, e la certificazione degli strumenti

| Fonte | Che cos'è | Marca |
|---|---|---|
| **FreeRDP 3.15.0** | clone in `/tmp/studio-input/freerdp/FreeRDP`, commit **`0ce68ddd1cd6ed067392a17d9858c739f2bf37ec`** (tag `3.15.0`, 14 aprile 2025). ⚠ clone **superficiale** (`--depth 50`, 129 commit): la *storia* non è affidabile, il *contenuto* sì | `[R]` |
| **[MS-RDPBCGR]**, **[MS-RDPEDISP]** | specifiche pubbliche Microsoft, `learn.microsoft.com/openspecs` | `[S]` |
| **Note di rilascio Android di RDM** | `devolutions.net/remote-desktop-manager/release-notes/android/`, pagina grezza di 860 KB scaricata intera: **59 versioni, da 2023.1.3.7 (5 giu 2023) a 2026.2.2.3 (29 lug 2026)**. Le citazioni sono **esatte al byte** | `[S]` **detto dal venditore** |
| **Forum Devolutions** | `forum.devolutions.net`. ⚠ **è un'applicazione JavaScript**: `curl` restituisce solo un guscio di 30 KB, quindi il testo è passato per un riassuntore. Le citazioni marcate ⚠︎ sono **fedeli ma non certificate al byte** | `[S]` |
| **Scheda Play Store** | `play.google.com/…/com.devolutions.remotedesktopmanager`, aggiornata **28 luglio 2026** | `[S]` **marketing** |
| **Android / Samsung / Chromium** | `developer.android.com`, `developer.samsung.com`, tracker Chromium, `mdn/browser-compat-data` | `[S]` / `[R]` |

⛔ **RDM non è stato installato né decompilato**, come da mandato. **Nessuna affermazione su RDM
qui dentro è `[M]` né `[R]`.**

### ⭐ Certificazione degli strumenti

⛔ Prima di ogni assenza dichiarata, la stessa ricerca è stata fatta girare su un caso dove la cosa
c'è di sicuro.

| assenza dichiarata | controprova che lo strumento funziona |
|---|---|
| «FreeRDP Android non implementa il puntatore» | la stessa `grep` trova un corpo **vero** in `xf_Pointer_Set` (`client/X11/xf_graphics.c:356`), `sdl_Pointer_Set` (`client/SDL/SDL3/sdl_pointer.cpp:99` **e** `SDL2/:99`), `wlf_Pointer_Set` (`client/Wayland/wlf_pointer.c:69`), `wf_Pointer_Set` (`client/Windows/wf_graphics.c:290`): **cinque client su sei** `[R]` |
| «FreeRDP Android non ha RDPEDISP» | `grep -r "disp\|DisplayControl" client/Android/` = **vuoto**; la stessa `grep` sull'albero intero trova `client/common/cmdline.c:1186`, `client/X11/xf_event.c:1320`, `channels/disp/client/disp_main.c:294` `[R]` |
| «FreeRDP non usa la cattura del puntatore in nessun client» | `grep -r "requestPointerCapture\|setPointerIcon" client/` = **vuoto**; la stessa `grep` sullo stesso albero trova `setSystemUiVisibility` in `SessionView.java:95` e `HomeActivity.java:71` `[R]` |
| «il GDI di FreeRDP non dipinge il puntatore nell'immagine» | in `libfreerdp/gdi/*.c` l'unica occorrenza è `gdi_GetPointer` (`bitmap.c:60`), che è un **indirizzo di pixel**, non un cursore `[R]` |
| «"bluetooth" e "relative" non compaiono mai nelle note di rilascio di RDM» | la stessa ricerca sulla stessa pagina grezza rende **9 riscontri per «mouse», 27 per «keyboard», 6 per «cursor»**: lo zero è vero zero `[S]` |
| «Devolutions non ha **nessuna** pagina di documentazione sull'ingresso o su DeX» | `docs.devolutions.net/sitemap.md` (723 KB) ha **835 pagine `/rdm/`**, di cui **quattro** per Android (MDM, permessi sui file, spazi di lavoro deprecati, ciclo di vita): **nessuna** su mouse, tocco o schermo. `/rdm/android/` risponde **404**. `llms-full.txt` (420 KB): **zero** riscontri per «dex» `[S]` |

⚠ **Due invenzioni del riassuntore, scoperte e corrette**: aveva collocato le correzioni su DeX
sotto la versione «2024.3» (la pagina grezza dice **2025.2.1.5** e **2025.2.0.17**), e aveva
inventato due numeri di discussione del forum, entrambi **404**. ⇒ Le note di rilascio qui sotto
sono lette dal **testo grezzo**, non dal riassunto.

---

## 1 · Quando il mouse si muove e sullo schermo non cambia niente, che cosa viaggia sul filo?

### `[S]` Nel protocollo: due PDU dedicate, fuori dagli aggiornamenti dello schermo

⭐ **Confermato sulla specifica.** In RDP il puntatore ha un tipo di PDU **suo**, con un
`pduType2` **suo**, distinto da quello degli aggiornamenti bitmap.

`[S]` [MS-RDPBCGR] §2.2.9.1.1.4 *Server Pointer Update PDU*:

> «The Pointer Update PDU is sent from server to client and is used to convey pointer information,
> including pointers' bitmap images, use of system or hidden pointers, use of cached cursors **and
> position updates**.»
> «The **pduType2** field of the Share Data Header MUST be set to **PDUTYPE2_POINTER (27)**.»

cioè **non** `PDUTYPE2_UPDATE (2)`, che è quello dei bitmap. In via veloce i due stanno come voci
**separate** dello stesso elenco di tipi di aggiornamento (§3.2.5.9): *Bitmap Update* da una parte,
*Pointer Position · System Pointer Hidden · System Pointer Default · Color Pointer · New Pointer ·
Cached Pointer · Large Pointer* dall'altra.

`[S]` §2.2.9.1.1.4.2 *Pointer Position Update* — **la sola posizione, quattro byte in tutto**:

> «The TS_POINTERPOSATTRIBUTE structure is used to indicate that **the client pointer MUST be moved
> to the specified position** relative to the top-left corner of the server's desktop.»

⇒ ⭐ **Nel protocollo RDP la risposta è: viaggiano quattro byte, e lo schermo non si muove.** È
precisamente il pezzo che ci manca: noi, per far sapere alla pagina dov'è il puntatore, **dobbiamo
aspettare un fotogramma** — e a `[M]` **1,1 fotogrammi al secondo** quel fotogramma non arriva.

### ⛔ Ma nel client Android di FreeRDP quei quattro byte finiscono nel cestino

`[R]` `client/Android/Studio/freeRDPCore/src/main/cpp/android_freerdp.c:240-245`:

```c
static BOOL android_Pointer_SetPosition(rdpContext* context, UINT32 x, UINT32 y)
{
	WINPR_ASSERT(context);

	return TRUE;
}
```

E **tutte e sei** le funzioni sono così (`android_freerdp.c:218-259`): `New`, `Free`, `Set`,
`SetPosition`, `SetNull`, `SetDefault` — nessuna tocca un pixel. Sono registrate lo stesso
(`:261-277`), quindi il PDU viene letto, decodificato… e scartato.

La catena è verificata a monte: `[R]` `libfreerdp/core/update.c:760-766` legge
`PTR_MSG_TYPE_POSITION` e chiama `pointer->PointerPosition`; `[R]` `libfreerdp/cache/pointer.c:77`
traduce in `pointer->SetPosition` — che su Android **è lo stub vuoto**.

⇒ **In FreeRDP per Android il puntatore che l'utente vede muoversi non è il cursore remoto: è il
cursore di sistema di Android**, che si muove alla velocità della mano perché **non ha mai
attraversato la rete**. Esattamente come il nostro cursore del browser sul DeX.

### ⭐ RDM invece il cursore lo disegna davvero — e si vede dai suoi difetti

`[S]` Note di rilascio, testo esatto:

| versione | data | voce |
|---|---|---|
| 2026.1.0.27 | 13 mar 2026 | «Fixed a potential **cursor corruption** issue in RDP sessions» |
| 2026.1.0.27 | 13 mar 2026 | «Fixed an issue with the **incorrect wait cursor color** in RDP sessions» |
| 2026.1.0.27 | 13 mar 2026 | «ARD sessions now properly support **cursor updates**» |
| 2024.3.2.6 | 21 ott 2024 | «Added a setting to set the **pointer size mode to 32x32**» |
| 2026.1.1.2 | 30 mar 2026 | «Added an option to **display the cursor when using Touch Mode**» |

⭐ **La prova sta nei difetti, non nelle promesse**: un cursore *corrotto nei colori* e un
*«pointer size mode 32x32»* si possono avere **solo** se sei tu a interpretare la maschera XOR/AND
che arriva dal server. Il `32x32` è la misura massima del puntatore RDP quando il client **non**
annuncia `LARGE_POINTER_FLAG_96x96` `[S]` (§2.2.7.2.7): RDM sta esponendo all'utente un pezzo del
negoziato di protocollo.

⚠ E resta rotto: nell'indice dei difetti Android c'è ancora *«Cursor colors are wrong or
corrupted»* (6 mesi fa, 4 risposte) `[S]`⚠︎.

---

## 2 · Chi disegna il puntatore

| chi | che cosa disegna | marca |
|---|---|---|
| il **protocollo RDP** prevede | il **client**, da una forma ricevuta e messa in **cache** | `[S]` |
| **RDM per Android** | ⭐ **il client**, dalla forma ricevuta (prova: corruzione colori, `32x32`, «display the cursor when using Touch Mode») | `[S]` |
| FreeRDP **X11 / SDL / Wayland / Windows** | il client, sul serio: `xf_Pointer_Set` (`client/X11/xf_graphics.c:356`), `sdl_Pointer_Set` (`client/SDL/SDL3/sdl_pointer.cpp:99`), `wlf_Pointer_Set` (`client/Wayland/wlf_pointer.c:69`), `wf_Pointer_Set` (`client/Windows/wf_graphics.c:290`) | `[R]` |
| FreeRDP **Android** | ⛔ **nessuno**: stub vuoti. Vede il cursore **di sistema** e, in modo tocco, una **grafica propria** (§6) | `[R]` |
| **noi** oggi | il cursore del browser **+** una freccia disegnata dalla pagina, **sovrapposti** (punto-di-ripresa §5) | `[M]` |

⭐ **La riga da leggere in questa tabella è l'ultima.** Tutti gli altri hanno **un** puntatore in
scena. Noi ne abbiamo **due**, e il tentativo di toglierne uno ha prodotto `[M]` **4 clic e ZERO
movimenti**.

### `[S]` Che cosa succede quando la forma cambia — e la `[?]` del mandato smentita

Il mandato chiedeva di trovare in §2.2.7.1.5 la prova che «se il client non supporta il puntatore a
colori, lo disegna il server dentro l'immagine».

⛔ **Quella prova non esiste, e il testo dice il contrario.** `[S]` §2.2.7.1.5:

> «**colorPointerFlag** … Since RDP supports monochrome cursors by using Color Pointer Updates and
> New Pointer Updates …, **the value of this field is ignored and is always assumed to be TRUE (at
> a minimum the Color Pointer Update MUST be supported by an RDP client)**.»

⇒ In RDP **non c'è nessun ripiego «lo disegna il server»**: il disegno lato client non è il caso
normale, è **l'unico**. La prova vera, e più forte, è `[S]` §3.2.5.9.2:

> «Once this PDU has been processed, **the client MUST carry out any operations necessary to update
> the local pointer position** … **or change the shape** … In the case of the Color and New Pointer
> Updates **the new pointer image MUST also be stored in the Pointer Image Cache**, in the slot
> specified by the **cacheIndex** field.»

La forma viaggia **una volta sola** e poi si richiama per indice — `[S]` §2.2.9.1.1.4.6: *«used to
instruct the client to change the current pointer shape to one already present in the pointer
cache»*, con la misura della cache annunciata dal **client** (`colorPointerCacheSize`,
`pointerCacheSize`, §2.2.7.1.5).

⚠ **Rilievo per noi**: è un pezzo di RDP che non abbiamo e che costerebbe poco. ⛔ **Ma non è il
pezzo che ci serve**, perché sul DeX nel browser il cursore che conta resta quello di sistema.

---

## 3 · Il client chiede la misura del desktop al server?

### ⭐ RDM: sì, e si chiama **«Force Dynamic Resolution»** — ma è arrivata tardi e rotta

`[S]` Note di rilascio, testo esatto:

| versione | data | voce |
|---|---|---|
| 2024.2.0.16 | 18 giu 2024 | «Introduced a **stretch resolution** option for RDP, VNC, and ARD sessions» |
| 2025.3.3.2 | 26 gen 2026 | «Fixed a regression that reduced the reliability of the **Dynamic Resolution** feature» |
| 2025.3.3.2 | 26 gen 2026 | «Fixed an issue where the **Force Dynamic Resolution** setting was not applied properly» |
| 2026.1.0.27 | 13 mar 2026 | «Added a prompt to optionally enable or disable the **Scale Factor** when toggling **Force Dynamic Resolution** in RDP sessions. The prompt is displayed only when the setting states are inconsistent» |

⭐⭐ **E c'è un cliente che descrive il NOSTRO difetto, parola per parola** — discussione 51934,
*«Dynamic resolution not working»*, gennaio 2026, l'utente `pawelm` `[S]`⚠︎:

> «When I connect to a standard win 10 RDP server from my tablet I want to have full available area
> used, so I selected **'Current work area size'** and **'Dynamic resolution'** options»

e i tre difetti che riporta:

1. ⛔ **bande nere** invece dell'adattamento: *«the connection is scaled down to fit»*;
2. ⛔ **la densità**: *«the connection is done at **1:1 DPI scaling**, instead of following the
   android DPI settings, so text is super small»*;
3. ⛔ **la rotazione non rinegozia**: *«Rotation of a device also does not trigger the resolution
   change of the RDP connection and old aspect ratio is just rotated»*.

Risposta dell'ingegnere Frederick Simard: l'impostazione mancante si chiama **«Auto scale
factor»**, *«in the same location as the Force Dynamic Resolution setting»*, e sul perché siano
separate: *«we received feedback from users who preferred having these options separated, as it
provides greater flexibility»* `[S]`⚠︎. Corretto in **2026.1.0.25**, marzo 2026 — cioè **cinque
mesi fa**.

⇒ ⭐ **Tre lezioni, e sono tutte per la nostra §5.1:**
- **anche RDM impagina con le bande quando la rinegoziazione fallisce**: le bande sono il ripiego
  di *tutti*, come già diceva `F4-AND-4`;
- ⭐ **la misura e la densità sono due impostazioni separate**, e Devolutions dice esplicitamente
  che è per scelta. **Conferma la lezione di `F4-AND-4` punto 3**: il DPR non va nella conversione,
  va nella richiesta, e va tenuto **come una manopola sua**;
- ⛔ **la rinegoziazione a ogni cambio di finestra è la parte difficile**, non la prima richiesta.

⚠ `[S]` Zero riscontri nelle note di rilascio per «smart sizing», «fit to screen», «match device»,
«screen size», «monitor».

### ⭐ FreeRDP Android: sì, e la misura è quella della **finestra vera**, non dello schermo

`[R]` `SessionActivity.java:241-252` — la misura si prende **dopo** l'impaginazione, e il commento
nel codice dice il perché:

```java
// This is because only then we can know the exact size of our session
// when using fit screen accounting for any status bars etc. that Android might throws on us.
final View activityRootView = findViewById(R.id.session_root_view);
activityRootView.getViewTreeObserver().addOnGlobalLayoutListener(new OnGlobalLayoutListener() {
    @Override public void onGlobalLayout() {
        screen_width = activityRootView.getWidth();     // riga 246
        screen_height = activityRootView.getHeight();   // riga 247
```

`[R]` `SessionActivity.java:486-490` la misura diventa la risoluzione chiesta
(`if (screenSettings.isFitScreen()) { setHeight(screen_height); setWidth(screen_width); }`), e
`[R]` `LibFreeRDP.java:281-282` la mette sul filo:

```java
args.add(String.format("/size:%dx%d", screenSettings.getWidth(), screenSettings.getHeight()));
```

**Unità**: `View.getWidth()` in Android è in **pixel fisici del dispositivo** — non `dp`, non pixel
CSS. ⭐ **`devicePixelRatio` non compare da nessuna parte**, perché non ci sono due sistemi di unità
da riconciliare. È la conclusione di `F4-AND-4` («togli il DPR dalla conversione»), qui in forma
ancora più netta: **il client nativo il problema non ce l'ha proprio**.

⚠ **Il modo «automatico» ha una regola che a noi non servirebbe** (`[R]` `:469-486`): su tablet usa
la misura vera, su telefono prende il lato più lungo e ne fa un 16:10 arbitrario
(`setWidth((int)(screenMax * 1.6f))`). ⛔ Su un DeX 21:9 quella regola sbaglierebbe di brutto.
`[?]` In pratica prende il ramo del tablet, perché `SCREENLAYOUT_SIZE_LARGE` su DeX dovrebbe essere
vero — **non verificato**.

### ⛔ E se il server non può accontentarlo: FreeRDP Android non riprova mai

`[R]` **il client Android non ha RDPEDISP** (certificato in §0): la misura si chiede **una volta
sola, alla connessione**. Se il server ne dà un'altra, il client si adatta (`OnGraphicsResize`,
`SessionActivity.java:887-893`) e amen. ⚠ E c'è una toppa che dice quanto è ruvida la faccenda —
`[R]` `SessionActivity.java:862-866`:

```java
// FIXME: the additional check (settings.getWidth() != width + 1) is for
if ((settings.getWidth() != width && settings.getWidth() != width + 1) || ...
```

cioè **un pixel di scarto previsto e tollerato a mano**, come il `Math.floor(x/2)*2` di KasmVNC.

### `[S]` La strada che RDP offre, e i vincoli da copiare

`[S]` [MS-RDPEDISP] §2.2.2.2 *DISPLAYCONTROL_MONITOR_LAYOUT_PDU*:

> «a **client-to-server PDU that is used to request a display configuration change on the server**,
> such as the addition of a monitor **or a new resolution for an existing monitor**.»

⭐ **I vincoli sui valori sono la cosa da portarsi via** — `[S]` §2.2.2.2.1:

> «**Width**: … **MUST be greater than or equal to 200 pixels and less than or equal to 8192
> pixels, and MUST NOT be an odd value**.»
> «**Height**: … MUST be greater than or equal to 200 pixels and less than or equal to 8192 pixels.»

⚠ Nota l'asimmetria: **la larghezza dev'essere pari, l'altezza no.** È nella specifica.

E la coppia scala/densità, che riguarda il nostro DeX direttamente:

> «**DesktopScaleFactor**: … MUST be ignored if it is less than 100 percent or greater than 500
> percent, **or if DeviceScaleFactor is not 100 percent, 140 percent, or 180 percent**.»

⇒ `[S]` **Microsoft ammette solo tre densità.** Il nostro `devicePixelRatio = 1,2` del DeX (`[M]`)
**non sarebbe rappresentabile** in RDPEDISP. ⭐ Lezione: la densità è un guaio noto da vent'anni, si
tratta **a parte**, e mai dentro la conversione delle coordinate — la stessa cosa che ha imparato
Devolutions a gennaio 2026 con «Auto scale factor».

⭐ **Per la nostra §5.1**: `[M]` la misura del DeX è **2560×926** — larghezza **pari**, dentro
l'intervallo `200…8192`. Il vincolo di sanità da mettere in `mutter.c` è già scritto, provato da
vent'anni, e costa tre righe.

---

## 4 · Quanti stadi ha la conversione, e dove vive l'offset

### ⭐ FreeRDP Android: **uno stadio (zoom), più lo scorrimento. Nessuna banda, mai.**

`[R]` `SessionActivity.java:1160-1172`, la formula intera:

```java
private Point mapScreenCoordToSessionCoord(int x, int y)
{
	int mappedX = (int)((float)(x + scrollView.getScrollX()) / sessionView.getZoom());
	int mappedY = (int)((float)(y + scrollView.getScrollY()) / sessionView.getZoom());
	...
}
```

cioè `x_remoto = (x_vista + scrollX) / zoom`.

**Perché non c'è nessun offset di bande**, ed è la parte da rubare:

1. `[R]` `SessionView.java:226-231` — la vista è **esattamente** grande come l'immagine per lo zoom:
   `setMeasuredDimension((int)(width * scaleFactor) + …, (int)(height * scaleFactor) + …)`;
2. ⭐ `[R]` `SessionView.java:43-44` — **lo zoom non scende mai sotto 1**:
   ```java
   public static final float MAX_SCALE_FACTOR = 3.0f;
   public static final float MIN_SCALE_FACTOR = 1.0f;
   ```
   ⇒ **non si impagina: si scorre.** È la scelta di Chrome Remote Desktop (`std::max`,
   `F4-AND-4` §5), presa da un **secondo** progetto in modo indipendente;
3. `[R]` `res/layout/session.xml` — la vista è figlia `wrap_content` di uno `ScrollView2D` con
   `fillViewport="true"`: **il contenitore non centra niente**, quindi non esiste nessun
   `(contenitore − immagine)/2` da calcolare;
4. `[R]` `SessionView.java:239` — il `canvas.drawColor(Color.BLACK)` sta **dentro** i limiti della
   vista, che è esattamente l'immagine: **non è una banda**.

⭐ **L'offset vive in una variabile sola, prodotta da chi disegna**: `scrollView.getScrollX()`. È
la stessa disciplina di `ViewMatrix::Invert()` di Chrome RD, e la stessa morale del punto 4 di
`F4-AND-4`: *«due formule scritte in due punti diversi sono la definizione del difetto
puntatore-altrove»*.

### ⛔ E c'è un secondo cammino che quella formula NON la applica — un difetto vero in FreeRDP

`[R]` `SessionView.java:100-114`, il cammino del **mouse esterno**:

```java
@Override public boolean onHoverEvent(MotionEvent event)
{
	if (event.getAction() == MotionEvent.ACTION_HOVER_MOVE)
	{
		...
		MotionEvent mappedEvent = mapTouchEvent(event);
		LibFreeRDP.sendCursorEvent(currentSession.getInstance(), (int)mappedEvent.getX(),
		                           (int)mappedEvent.getY(), Mouse.getMoveEvent());
	}
	return true;
}
```

e `mapTouchEvent` (`SessionView.java:258-265`) applica **solo** `invScaleMatrix`, cioè **solo lo
zoom**. ⇒ ⛔ **`onHoverEvent` non somma `scrollX/scrollY`.** Con la vista scorsa e un mouse vero
attaccato, le coordinate sono **sbagliate esattamente della quantità scorsa**.

⭐ **E RDM ha un difetto della stessa famiglia**, ancora aperto nell'indice dei difetti Android:
*«External mouse move too quickly in zoomed in»* (5 mesi fa, 3 risposte) `[S]`⚠︎ — **il mouse
esterno con lo zoom attivo**, cioè lo stesso incrocio.

⇒ ⚠ **Per noi vale come conferma di metodo, non come cura**: la nostra conversione è già verificata
al pixel (`[M]`, strada chiusa n. 1). Ma dice che **quando i cammini d'ingresso sono più d'uno, la
formula si sdoppia e uno resta indietro** — e che il cammino che resta indietro è **sempre quello
del mouse fisico**, in due progetti indipendenti. Noi di cammini ne abbiamo almeno due (`mousemove`
e `pointermove`, punto-di-ripresa §7): ⭐ **vanno tenuti sulla stessa funzione, sempre.**

---

## 5 · Come si misura e come si limita la latenza dell'input

### ⭐ FreeRDP: c'è accorpamento, ed è in Java, con una valvola di sfogo

`[R]` `SessionActivity.java:658-673`:

```java
private void sendDelayedMoveEvent(int x, int y)
{
	if (uiHandler.hasMessages(UIHandler.SEND_MOVE_EVENT))
	{
		uiHandler.removeMessages(UIHandler.SEND_MOVE_EVENT);
		discardedMoveEvents++;
	}
	else
		discardedMoveEvents = 0;

	if (discardedMoveEvents > MAX_DISCARDED_MOVE_EVENTS)
		LibFreeRDP.sendCursorEvent(session.getInstance(), x, y, Mouse.getMoveEvent());
	else
		uiHandler.sendMessageDelayed(Message.obtain(null, UIHandler.SEND_MOVE_EVENT, x, y),
		                             SEND_MOVE_EVENT_TIMEOUT);
}
```

con `[R]` `:88-89`: `MAX_DISCARDED_MOVE_EVENTS = 3`, `SEND_MOVE_EVENT_TIMEOUT = 150`.

In italiano: **ogni movimento aspetta 150 ms**; se ne arriva un altro prima, il precedente **viene
buttato** e riparte l'attesa. ⭐ **Ma se se ne buttano più di tre di fila, il quarto parte subito**:
la valvola che impedisce a un movimento continuo di non arrivare **mai**.

⚠ **E vale per un cammino su tre.** `sendDelayedMoveEvent` è chiamata **da un punto solo** (`[R]`
`:1144`, `onSessionViewMove`, il trascinamento col **dito**). ⛔ Il mouse esterno (`onHoverEvent`,
`SessionView.java:109`) e il puntatore-a-cerchio (`:1191`) **saltano l'accorpamento** e mandano
tutto. ⇒ ⭐ **La scelta, letta nel codice, è: il mouse vero non si accorpa.** L'accorpamento
protegge il filo dal *dito*.

Coerente con la nostra misura: `[M]` **coda del filo 1, puntatori sorpassati 0** — noi il problema
dell'accorpamento **non ce l'abbiamo**.

### La coda nativa: **nessun accorpamento, nessuno scarto, nessun limite di frequenza**

`[R]` `cpp/android_event.c:25-44` — la coda cresce raddoppiando (`new_size = size * 2`) e **non
scarta mai**; `[R]` `:76-120` la svuota tutta a ogni giro chiamando
`freerdp_input_send_mouse_event` uno per uno; `[R]` `:58-73` è una FIFO con `memmove` a mano,
**nessuna fusione di eventi adiacenti**.

⇒ ⭐ **Non c'è nessuna misura della latenza in nessuna parte del client Android di FreeRDP**:
nessun timestamp, nessun giro completo, nessun contatore. **Su questo noi siamo avanti**: i tre
strumenti del punto-di-ripresa §7 non hanno un equivalente.

### RDM: nessun numero pubblico, ma due voci che tradiscono il problema

`[S]` «Improved the **fluidity of mouse acceleration**» (2025.1.0.38, 12 mar 2025) · «Improved
handling of **physical mouse scroll wheel speed**» (2026.1.2.8, 15 apr 2026). ⚠ *«Fluidity»* e
*«speed»* senza un numero sono `[S]` di marketing: **non provano niente**, ma dicono che la
fluidità del mouse è stata un cantiere aperto **fino a quattro mesi fa**.

---

## 6 · Che cosa c'è di specifico per Android, per il tocco e per DeX

### ⭐⭐ I modi d'ingresso di RDM: sono **quattro**, hanno nomi, e sono scelte dell'utente

`[S]` Ricostruiti dalle note di rilascio (testo esatto) e dal forum:

| nome nell'interfaccia | dove | fonte |
|---|---|---|
| **Touch Mode** | barra della sessione | «Added an option to display the cursor when using **Touch Mode** in RDP, VNC, and ARD sessions» — 2026.1.1.2, 30 mar 2026 |
| **direct-touch mode** | — | «right-click context menu items were not clickable in **direct-touch mode** on RDP sessions» — 2026.1.1.2, 30 mar 2026 |
| **touchpad mode** | *Settings → User Interface → «Use touchpad mode by default»* | «the long-press functionality in **touchpad mode** was not working correctly» — 2023.3.0.24, 1 nov 2023 |
| ⭐⭐ **Use Pointer Capture** | *Session Settings → **Interactive Method*** | «Added a setting to use **Pointer Capture** as the input method for RDP, VNC, and ARD sessions» — **2024.3.2.6, 21 ott 2024** |

**Sono scelte dell'utente, non automatismi.** La fonte definitiva è il personale Devolutions,
discussione 31911 `[S]`⚠︎ (Nicolas Dufour):

> «The mouse mode can be toggled by tapping on the pointing finger (bottom toolbar). Unselecting
> the pointing finger will activate touch screen input. However, **it is less precise** than the
> mouse cursor and most user prefer the mouse cursor mode.»
> «The option can be found under the application general Setting, User Interface, **'Use touchpad
> mode by default.'**»

⚠ Nota la deriva terminologica **dentro le risposte di Devolutions stessa**: nella prosa dicono
«mouse cursor mode» e «touch screen input», ma la casella che hanno spedito dice **touchpad**.

### ⭐ Il mouse Bluetooth vero — il caso dell'utente

`[S]` **Zero riscontri per «bluetooth» e per «relative» in tre anni di note di rilascio**
(certificato in §0). La parola «physical» compare **due volte, entrambe recentissime**:

| versione | data | voce |
|---|---|---|
| 2026.1.0.27 | **13 mar 2026** | «Added a new setting to enable **right-click via long press with a physical mouse** on RDP/ARD/VNC sessions» |
| 2026.1.2.8 | **15 apr 2026** | «Improved handling of **physical mouse scroll wheel** speed» |

più la linea della cattura del puntatore:

| versione | data | voce |
|---|---|---|
| 2024.3.2.6 | 21 ott 2024 | «Added a setting to use **Pointer Capture** as the input method» |
| 2025.2.2.1 | 15 set 2025 | «Fixed an issue where enabling **pointer capture** … caused a **double-click when releasing the left mouse button**» |

⚠ ⛔ **Undici mesi con un difetto di doppio clic sul tasto sinistro** nella modalità che è la
risposta di RDM al mouse vero.

⭐ E la confessione dell'ingegnere, discussione 52111, febbraio 2026 (Frederick Simard) `[S]`⚠︎:

> «Some shortcuts can be controlled by us, while others are **handled by the operating system,
> which takes priority and cannot always be intercepted**.»

e Nicolas Dufour sul tasto Windows:

> «It works on Samsung phones, but **not on Pixel phones running Android 16. Unfortunately, there
> is nothing we can do about this.**»

⇒ ⭐ **Il trattamento serio del mouse fisico in RDM è di marzo-aprile 2026 — cioè di cinque mesi
fa — ed è ancora incompleto.** Difetti aperti nell'indice `[S]`⚠︎: *«Scroll wheel of external mouse
is not working well»* (6 mesi, **9 risposte**), *«Right mouse click issue»* (5 mesi, 8 risposte),
*«External mouse move too quickly in zoomed in»* (5 mesi, 3 risposte).

⚠ **E il difetto è vecchio di otto anni**: discussione 31028, *«Mouse Scrolling in Samsung DeX»*,
l'utente `peelos` `[S]`⚠︎: *«I am unable to scroll with my bluetooth mouse and right click does not
work»*, e — la riga che brucia — *«Bluetooth mouse is fully supported in the Microsoft Rd client app
on android»*.

### ⭐⭐ DeX: una riga di marketing, due correzioni di crollo, e una confessione

`[S]` **Nella scheda Play Store** (aggiornata 28 luglio 2026), sotto l'ultimo titolo, per intero:

> **Other**
> **Samsung Dex Support**

⛔ Questa è **tutta** la storia del venditore su DeX: **un punto elenco senza una riga di
spiegazione**, e `[S]` **zero pagine di documentazione** in 835 pagine `/rdm/` (certificato in §0).

`[S]` **In tre anni di note di rilascio DeX è nominato esattamente due volte, e sono due crolli:**

| versione | data | voce |
|---|---|---|
| 2025.2.0.17 | 4 giu 2025 | «Fixed an issue where **using Samsung DeX could cause the application to freeze**» |
| 2025.2.1.5 | 22 lug 2025 | «Fixed **black screen issue when using RDP sessions on Samsung DeX**» |

⚠ Nessuna delle due è una funzione. **Un anno fa RDM su DeX si piantava e faceva schermo nero.**

⭐⭐ **E qui c'è la fonte più importante di tutto il rapporto.** Discussione 52663, *«Bluetooth
mouse and keyboard cannot control RDP session on HDMI extended screen»*, aprile 2026, un utente con
mouse **e** tastiera **Bluetooth** su schermo esterno via **hub Type-C** — cioè **la scena
dell'utente, con un cavo e un monitor esterno**:

> «the Bluetooth mouse and keyboard can only move and input on the phone's local screen; they are
> **unable to control or input anything within the RDP remote desktop session on the external
> display**.» — «a critical bug that affects the usability of desktop mode.»

**La risposta di Frederick Simard, personale Devolutions** `[S]`⚠︎ (sopravvissuta identica a due
recuperi indipendenti):

> «**The implementation is a bit janky and could benefit from some rework.** On Pixel devices
> running Android 16 with Desktop mode and on Samsung devices using Samsung DeX, **it works better
> since the external monitor is treated as a fully independent desktop**.»

e il suo rimedio, che dice **esattamente dov'è la cucitura**:

1. aprire la sessione sullo schermo **interno**, non su quello esterno;
2. *Session Settings* dal menu della barra;
3. ⭐ accendere **«Use Pointer Capture»** sotto **«Interactive Method»**;
4. uscire e riaprire la sessione scegliendo lo schermo esterno.

⇒ ⭐⭐ **Tre conclusioni, e sono il cuore del rapporto:**

- **Il *«funziona molto bene»* dell'utente è vero, e il merito è di DeX, non di RDM**: lo dice
  l'ingegnere di Devolutions. Su DeX *«lo schermo esterno è trattato come un desktop pienamente
  indipendente»*. Fuori da DeX, la stessa applicazione con lo stesso mouse **non funziona affatto**.
- **Il rimedio di Devolutions al mouse su schermo esterno è la cattura del puntatore.** Cioè
  **precisamente la cosa che noi non possiamo fare** (§6-bis).
- ⚠ **La storia si ripete da nove anni.** Discussione 28327, *«Samsung DeX»*: nel 2017 il personale
  scrive *«Our new update is rolling out with **full support for Samsung Dex**»*, e **due anni
  dopo lo stesso cliente torna** `[S]`⚠︎: *«it opens the remote session within the frame of the RDM
  for Android … **No way to resize the frame**»*. ⛔ Nell'indice dei difetti c'è ancora *«RDP
  Blackscreen on External Screen after Screen Switching»* (un anno fa, 4 risposte).

### FreeRDP e DeX: tre righe di manifesto, copiate dalla guida Samsung

`[R]` `client/Android/Studio/freeRDPCore/src/main/AndroidManifest.xml:24-26`:

```xml
android:resizeableActivity="true"
<meta-data android:name="com.samsung.android.keepalive.density" android:value="true"/>
```

più `[R]` `aFreeRDP/src/main/AndroidManifest.xml`:
`android:configChanges="orientation|keyboardHidden|screenSize|smallestScreenSize|density|screenLayout"`.

⭐ **Quelle tre righe sono, alla lettera, le tre righe della guida Samsung** «*[Samsung DeX]
Optimization of VNC client for Samsung DeX*» (`developer.samsung.com`, 25 maggio 2017) `[S]`. Che
cosa fanno: `[S]` impediscono che l'applicazione **venga uccisa e ricreata** passando fra modo
telefono e modo DeX.

⚠ E la stessa guida Samsung, sul **mouse**, non dice altro che *«specify the type of the default
manipulator — Hardware Mouse»* `[S]`: **nessuna parola su cattura del puntatore, disegno del
cursore o risoluzione**. ⇒ La ricetta DeX ufficiale, per un client di desktop remoto, è tutta lì:
**sopravvivi al cambio di modo, e lascia fare al sistema**.

### I due modi d'ingresso di FreeRDP Android

`[R]` **tocco diretto** (per difetto): il dito *è* il mouse — tocco = clic
(`SessionView.java:356-382`), pressione lunga = trascinamento (`:314-330`), due dita = rotellina
(`:408-425`), due dita tocco = tasto destro (`:427-436`).

`[R]` ⭐ **puntatore a cerchio** (*Touch Pointer*, menu di sessione, `SessionActivity.java:692-706`):
una grafica di **9 quadranti disegnata dall'app** (`TouchPointerView.java:31-51`), con la punta nel
quadrante 0 (in alto a sinistra) e il dito che preme sul quadrante 4 (il centro), **a un pollice di
distanza**, così il dito non copre quel che indica. Si muove **in locale, alla velocità della mano**
(`movePointer`, `:130-134`) e manda la posizione al server **dopo** (`:307`).

⚠ **Le impostazioni globali sull'ingresso sono tre, e sono inezie** — `[R]`
`ApplicationSettingsActivity.java:274-295` e `res/values/strings.xml:166-168`: `Swap Mouse Buttons`
· `Invert Scrolling` · `Touch Pointer Auto Scroll`. ⛔ **Nessun «modo mouse», nessun touchpad
relativo, nessuna cattura del puntatore.** ⇒ **RDM, su questo, è nettamente più avanti di FreeRDP.**

---

## 7 · La tastiera fisica e l'IME — dove abbiamo un difetto dichiarato

### ⭐ RDM ha un interruttore che si chiama **«Disable local IME»**

`[S]` Note di rilascio, testo esatto:

| versione | data | voce |
|---|---|---|
| 2024.3.0.17 | 23 set 2024 | «Introduced an option to **disable local IME** for RDP sessions» |
| 2025.3.0.27 | 9 ott 2025 | «Fixed a crash that occurred when launching sessions with the **'Disable local IME'** option enabled» |
| 2025.1.0.38 | 12 mar 2025 | «Improvement to keyboard processing … Users can revert to the **legacy implementation** by toggling it off» |
| 2025.3.0.27 | 9 ott 2025 | «Enhanced **'Send Input as Unicode'** with **'Legacy Keyboard Processing'**» |
| 2026.1.0.27 | 13 mar 2026 | «Added a new option … to **automatically show the keyboard when tapping a text field** and hide it when tapping outside» |
| 2024.3.0.17 | 23 set 2024 | «Fixed multiple issues in RDP sessions where certain key combinations from **external keyboards** were not properly transmitted to the host» |

`[S]` **Zero riscontri per «scancode».** ⇒ Il modello di RDM è **Unicode prima di tutto**, con un
ripiego «legacy» commutabile.

⚠ ⛔ **E resta rotto**: nell'indice dei difetti Android c'è *«Physical keyboard cannot type some
chars»*, **vecchio di due anni, tredici risposte** `[S]`⚠︎. E le correzioni sulle disposizioni di
tastiera si ripetono ogni sei mesi (giapponese 2024.3.0.17, crollo scegliendo la disposizione
2025.2.1.10, crollo nella voce RDP 2024.3.4.4).

⭐⭐ **Per noi questo è un risultato, non un aneddoto.** `F4-AND-2` ha **scagionato** l'IME
(`[R]` Chromium `ImeAdapterImpl.java:569`: l'IME entra solo col fuoco su un nodo modificabile), e
`[M]` 13 lettere sono arrivate. ⇒ **RDM ha dovuto mettere un interruttore per spegnere l'IME
locale, e noi il problema non ce l'abbiamo.** La nostra strada 6.3 (Keyboard Lock, `getLayoutMap()`
vuota su Android) è **un'altra classe di problema**, e questa fonte lo conferma: chi ha davvero il
problema dell'IME ci mette un interruttore.

### FreeRDP: Unicode per difetto, codice virtuale solo per le combinazioni

`[R]` `SessionActivity.java:745-750`, commento nel codice:

> «We always use the unicode value to process input from the android keyboard except if key
> modifiers (like Win, Alt, Ctrl) are activated. In this case we will send the virtual key code to
> allow key combinations (like Win + E to open the explorer).»

`[R]` `KeyboardMapper.java:421-479` lo attua: `ACTION_UP` **si scarta** (riga 426-428, si processano
solo i `DOWN`), e la scelta fra `processVirtualKey` e `processUnicodeKey` dipende dal `metaState`.
`[R]` `SessionActivity.java:810-814`: l'Unicode viene mandato come **coppia giù-su immediata**.

⇒ ⭐ **Stessa scelta di RDM, presa in modo indipendente: Unicode prima, codice virtuale solo per le
scorciatoie.** Due progetti su due.

---

## 8 · Che cosa ruberei per REMOTIX, e che cosa NON ruberei

### ✅ Da rubare

**8.1 ⭐⭐ La misura chiesta è la misura della finestra impaginata, non dello schermo.**
`[R]` `SessionActivity.java:241-247`: si aspetta il primo `onGlobalLayout` **e poi** si legge
`getWidth()`, col commento che spiega *«accounting for any status bars etc.»*. **Costo: nullo.**
⭐ È la nostra §5.1 con un dettaglio che il punto-di-ripresa §6.3 segnalava già come mina: la nostra
`misura_vista()` non ha guardia su `visualViewport.scale`, e `pieno` è `false` per costruzione.

**8.2 ⭐ Misura e densità sono due manopole SEPARATE.** `[S]` RDM ha «Force Dynamic Resolution» e
«Auto scale factor» distinte, **per scelta esplicita**; `[S]` RDPEDISP separa `Width`/`Height` da
`DesktopScaleFactor`/`DeviceScaleFactor` e ammette **solo tre densità**. ⇒ ⛔ **Il nostro DPR 1,2
non va mai nella conversione delle coordinate.** Terza conferma indipendente dopo `F4-AND-4`.

**8.3 ⭐ Non impaginare: scorrere.** `[R]` `SessionView.java:44`, `MIN_SCALE_FACTOR = 1.0f`. Sesto
progetto su sei che rifiuta le bande come strada principale.

**8.4 ⭐ Una sola funzione di conversione, e TUTTI i cammini d'ingresso ci passano.** Il
controesempio è `onHoverEvent` (§4), e RDM ha un difetto gemello (*«External mouse move too quickly
in zoomed in»*). ⛔ Il difetto è **saltare** la funzione, non sbagliarla. **Costo: nullo**, ed è da
verificare oggi: `mousemove` e `pointermove` chiamano davvero la stessa `cl_geometria()`?

**8.5 I vincoli di sanità di [MS-RDPEDISP]** `[S]`: `200 ≤ misura ≤ 8192`, **larghezza pari**.
Tre righe in `mutter.c`, vent'anni di produzione dietro.

**8.6 La valvola dell'accorpamento** `[R]` `SessionActivity.java:668`: se scarti più di N di fila,
**il successivo parte subito**. ⚠ Non ci serve oggi (`[M]` sorpassi 0), ma è la forma giusta se un
giorno accenderemo il sorpasso.

### ⛔ Da NON rubare

**8.7 ⛔ Gli stub del puntatore di FreeRDP.** `[R]` `android_freerdp.c:218-259`. Funziona per loro
perché il cursore di sistema è **l'unico** puntatore in scena; il nostro sarebbe il **secondo**.

**8.8 ⛔ Il *Touch Pointer* a 9 quadranti.** `[R]` `TouchPointerView.java`. È una risposta al
**dito**; l'uso primario dell'utente è **mouse e tastiera Bluetooth col cavo**. Costo alto,
guadagno zero sul difetto aperto.

**8.9 ⛔ L'attesa di 150 ms sui movimenti.** `[R]` `SEND_MOVE_EVENT_TIMEOUT = 150`. ⚠ **Cura
sbagliata al male sbagliato**: `[M]` il nostro tratto «prima di noi» è **12 ms**, la coda del filo è
**1**. Peggiorerebbe l'unica cosa che oggi funziona.

**8.10 ⛔ La regola «16:10 sul lato lungo».** `[R]` `SessionActivity.java:481-484`: su un 21:9
darebbe una misura assurda.

**8.11 ⛔ La cattura del puntatore.** Non perché sia sbagliata — perché **non l'abbiamo** (§9).

---

## 9 · ⭐⭐ La domanda che vale il rapporto: che cosa possono fare loro e noi no

### ⛔ **La cattura del puntatore. È il vincolo, ed è netto — e adesso è provato dai due lati.**

**Da una parte, l'app nativa.** `[S]` `developer.android.com`, *Track touch and pointer movements*:

> «Pointer capture is a feature available in **Android 8.0 (API level 26)** and higher that provides
> this control by **delivering all mouse events to a focused view** in your app.»
> «When pointer capture is enabled, events from a mouse are delivered with the source
> **`InputDevice.SOURCE_MOUSE_RELATIVE`**, and **relative position changes** are available through
> `MotionEvent.getX` and `getY`.»
> ⭐ «**When the window has pointer capture, the mouse pointer icon will disappear and will not
> change its position.**»

⭐⭐ **E RDM quella chiamata ce l'ha**: `[S]` «Added a setting to use **Pointer Capture** as the
input method for RDP, VNC, and ARD sessions» (2024.3.2.6, 21 ottobre 2024) — sotto la voce
**«Interactive Method»**, ed è **il rimedio che l'ingegnere di Devolutions consiglia** per il mouse
su schermo esterno (§6).

**Dall'altra, la pagina web.** `[R]` `mdn/browser-compat-data#19829` (Chrome 112.0.5615.135,
Android 12, mouse esterno):

> la chiamata «**does not throw an exception, but also does not lock the pointer** (seems like
> essentially a no-op)»

Il difetto rimanda a `crbug/153419`, **aperto e non risolto**; il dato di compatibilità è stato
**corretto** di conseguenza (PR `#26738`) per dire che **Chrome per Android non supporta la Pointer
Lock**. ⚠ E Samsung Internet ha **la stessa base Chromium**, quindi lo stesso buco.

⇒ ⭐⭐ **Il vincolo, per `DECISIONI.md`:**

> **Su Android, dentro un browser, non possiamo prendere il controllo del puntatore.** Non possiamo
> avere movimenti relativi, non possiamo far sparire il cursore di sistema per sostituirlo col
> nostro, non possiamo confinare il puntatore dentro la tela. Un'applicazione nativa fa tutte e tre
> le cose con **una** chiamata (`View.requestPointerCapture()`, da Android 8), **e RDM — il
> riferimento scelto dall'utente perché "funziona molto bene" — quella chiamata ce l'ha, e il suo
> costruttore la consiglia proprio per il caso dello schermo esterno.**
> ⛔ Non è un difetto nostro, non è aggirabile, e nessuna quantità di lavoro sulla pagina lo cambia.

⚠ **Quanto conta per il difetto aperto?** `[?]` Con onestà: **non è la causa del difetto di oggi**,
che è il desktop fermo a `[M]` 1,1 fotogrammi al secondo. Ma **chiude una porta**: la §5 del
punto-di-ripresa chiedeva se «disegniamo noi il puntatore» sia una strada. ⇒ ⛔ **Non lo è**, e
adesso c'è un movente e non solo una correlazione a una variabile. Restano la strada §6.1 (chiedere
la misura giusta) e la §6.2 (fotogramma su movimento).

### ⚠ Un'ironia che vale la pena scrivere

`[S]` [MS-RDPBCGR] §2.2.8.1.1.3.1.1.7: **RDP ha un evento di mouse relativo** —
`TS_RELPOINTER_EVENT`, `xDelta`/`yDelta` interi con segno a 16 bit — annunciato con
`INPUT_FLAG_MOUSE_RELATIVE (0x0080)`, e valido **solo da RDP 10.12** (versione di protocollo
`0x00080011`). `[R]` FreeRDP lo implementa (`libfreerdp/core/input.c:991`; il criterio in
`client/common/client.c:2236-2249`).

⛔ **E il client Android di FreeRDP non lo usa**, perché servirebbe `requestPointerCapture()`, che
`[R]` **non compare in nessun client di FreeRDP** (certificato in §0). ⇒ Il pezzo di protocollo c'è,
il pezzo di piattaforma c'è, e **nessuno dei due è cablato all'altro**. È lo stesso tipo di difetto
che abbiamo noi — *«nessun pezzo sbagliava per conto suo, il difetto sta fra i pezzi»*
(punto-di-ripresa §8) — all'ottava volta, e stavolta in casa d'altri.

---

## 10 · ⭐⭐ La refutazione del mandato

> **La frase da refutare**: «RDM su Android sembra fluido per una ragione sola e banale: RDP disegna
> il cursore lato client, quindi il puntatore si muove alla velocità della mano anche con il desktop
> remoto fermo. Tolta quella, non c'è nient'altro nel suo trattamento dell'input che valga la pena
> studiare: nessuna scelta di interfaccia, nessun trattamento del tocco, nessun accorgimento sulla
> latenza che noi non potremmo dedurre da soli.»

### ⛔ La prima metà è FALSA — la spiegazione data è vera ma non è quella giusta

`[S]` È vero che **RDP disegna il cursore lato client** (§3.2.5.9.2), ed è vero che **RDM lo fa**
(§2, provato dai suoi difetti di corruzione colori). Su questo il mandato ha ragione.

⛔ **Ma non è per quello che è fluido su Android.** Due prove:

1. `[R]` **Il client Android ufficiale di FreeRDP quel disegno lo implementa con sei funzioni
   vuote** (`android_freerdp.c:218-259`) — e nessuno si lamenta che il mouse non si muova. Il
   puntatore che si vede è **quello di sistema di Android**, fluido perché **non attraversa la
   rete**, non perché RDP sia fatto bene.
2. `[S]` ⭐⭐ **Lo dice Devolutions.** Lo stesso RDM, con lo stesso mouse Bluetooth, su uno schermo
   esterno che **non** è DeX, *«is unable to control or input anything»*, e l'ingegnere risponde
   *«the implementation is a bit janky»*. Se il merito fosse del cursore disegnato dal client,
   funzionerebbe **uguale** dentro e fuori DeX. Non funziona. ⇒ **Il merito è di DeX**, che
   *«tratta lo schermo esterno come un desktop pienamente indipendente»*.

⭐ **La differenza vera fra loro e noi non è il protocollo: è che loro hanno UN puntatore e noi ne
abbiamo DUE**, e loro hanno una chiamata per farne sparire uno.

### ⛔ La seconda metà è FALSA per quattro cose che non avremmo dedotto da soli

1. ⭐⭐ **«Use Pointer Capture» sotto «Interactive Method»** (`[S]` 21 ott 2024) — **una scelta di
   interfaccia**, esattamente quel che il mandato diceva non esistere, ed è **il vincolo di
   prodotto** della §9.
2. ⭐ **La misura e la densità sono due manopole separate**, per scelta dichiarata (`[S]`), e
   Microsoft ammette **solo tre densità** (`[S]`). Il nostro DPR 1,2 non sarebbe rappresentabile.
3. **La misura si prende DOPO l'impaginazione**, e il codice dice perché (`[R]`
   `SessionActivity.java:241-247`). Noi abbiamo già una mina esattamente lì.
4. **La valvola dell'accorpamento** (`[R]` `:668`) — la forma corretta di uno scarto che non affama.

### ✅ E dove il mandato aveva ragione, va detto

⚠ Il mandato ammetteva *«è ammesso concludere che su RDM non si può sapere abbastanza»*.
**Metà di quella previsione si è avverata, metà no.** ⛔ **La documentazione di RDM su questo tema
non esiste**: `[S]` **zero** pagine su ingresso, mouse, tocco o DeX in 835 pagine `/rdm/`,
`/rdm/android/` risponde **404**, e la scheda Play Store dice *«Samsung Dex Support»* e nient'altro.
✅ **Ma le note di rilascio e il forum sono una miniera**, e valgono più di una documentazione: le
note dicono **quando** una cosa è arrivata, e il forum dice **che cosa non funziona ancora** e come
lo chiamano gli ingegneri. ⇒ **Il mandato non si rifiuta: si compie da una porta di servizio.**

⭐ **E una correzione al mandato, perché è quel che è successo**: la domanda giusta non era «che cosa
fa RDM che noi non facciamo», era **«che cosa può fare un'applicazione nativa su Android che una
pagina non può»**. È la §9, ed è la sola riga di questo rapporto che cambia il prodotto.

---

## Quel che questo rapporto NON dice

⛔ **Su Devolutions RDM, il buco resta e va dichiarato per primo.**

- **Non ho installato RDM, non ho decompilato l'APK, non ho catturato il suo traffico** (come da
  mandato). ⇒ **Nessuna affermazione su RDM qui dentro è `[M]` né `[R]`.** Tutte le sue righe sono
  `[S]`, e **le dice il venditore**.
- ⚠ **Le citazioni dal forum sono passate per un riassuntore**, perché `forum.devolutions.net` è
  un'applicazione JavaScript e `curl` restituisce un guscio vuoto per ogni indirizzo. Sono marcate
  `[S]`⚠︎. Le due che contano di più (*«a bit janky»* e la ricetta della cattura del puntatore) sono
  sopravvissute **identiche a due recuperi indipendenti**, ma **non sono certificate al byte**. ⛔ Le
  note di rilascio e la scheda Play Store **sì**: lette dal testo grezzo.
- ⛔ **Non ho i numeri di tre discussioni** citate dall'indice dei difetti (*«Scroll wheel of
  external mouse…»*, *«Right mouse click issue»*, *«External mouse move too quickly…»*): il
  riassuntore ne aveva **inventati due**, verificati **404** e scartati. Restano i titoli e il
  conteggio delle risposte, presi dall'indice.
- ⚠ **Non so se RDM usi la cattura del puntatore PER DIFETTO o solo se la si accende.** Le note
  dicono *«Added a setting»*, e l'ingegnere la consiglia come **rimedio**, il che suggerisce che sia
  **spenta** per difetto `[?]`. ⭐ **Se l'utente la trova accesa nella sua sessione, questa è la
  spiegazione del suo *«funziona molto bene»*.**
- ⭐ **La misura da trenta secondi che chiuderebbe la questione, e la può fare solo l'utente**:
  aprire una sessione RDM sul DeX e **muovere il mouse fino al bordo dello schermo**. Se il cursore
  **si ferma al bordo della finestra di RDM** invece di uscirne, la cattura del puntatore è attiva —
  e allora il confronto con la nostra pagina **non è alla pari, e non lo sarà mai**.

⛔ **Sul resto:**

- **Non ho fatto girare FreeRDP per Android.** Nessuna misura: tutto è `[R]` da codice al commit
  `0ce68ddd…`. In particolare **non ho provato** il difetto di `onHoverEvent` (§4): è dedotto
  leggendo, non osservato.
- ⚠ **Il clone è superficiale** (`--depth 50`): ogni affermazione sulla **storia** del codice
  sarebbe inaffidabile, e infatti **non ne faccio nessuna**.
- ⛔ **La `[?]` del punto-di-ripresa §5 resta aperta.** Ho cercato una fonte che spieghi perché
  `cursor: none` avrebbe spento i movimenti sul DeX: **non l'ho trovata**. Cercato in: tracker
  Chromium (`issues.chromium.org`, `cursor: none` + Android + mousemove), `blink-dev` (trovato solo
  il comunicato di M56: *«mice on Android M+ will no longer fire TouchEvents, and will fire a
  consistent sequence of MouseEvents»* — spiega il **contesto**, non il fenomeno), documentazione
  `PointerIcon`/`setPointerIcon`. ⇒ **Resta `[?]`.** ⭐ Ma questo rapporto aggiunge un **movente
  diverso e certo**: **non serve più capire `cursor: none`**, perché anche capendolo la strada resta
  chiusa — senza Pointer Lock non c'è modo di sostituire il puntatore di sistema in modo affidabile.
- **Non ho verificato che `SCREENLAYOUT_SIZE_LARGE` sia vero in modo DeX** (`[?]`, §3).
- **Non ho letto il lato server**: né `gnome-remote-desktop`/Mutter, né i nostri `src/`. Se la
  misura del monitor virtuale si possa davvero chiedere a Mutter resta la domanda aperta di
  `F4-AND-4`, e **questo rapporto non la risponde** — aggiunge solo che un **sesto** progetto,
  nativo e su Android, fa la stessa cosa degli altri cinque, e che un **settimo** (RDM) ci ha messo
  due anni a farla funzionare.
- ⛔ **Nessuna porta usata, nessun servizio toccato, `src/` non modificato**, come da §9 del
  briefing.
