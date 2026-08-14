# F4-IN-2 · gnome-remote-desktop — l'input e la cattura, sulla nostra stessa API

⛔ Scritto il 14 agosto 2026. Bersaglio: **gnome-remote-desktop 48.1** e **mutter 48.7**, letti
nel codice in `reference-gnome/`. ⚠ Questo rapporto **non** rifà `gnome-remote-desktop.md` nella
radice (che è del percorso RDP): va oltre, sul **cursore** e sulla **cattura**.

---

## ⭐⭐ IL VERDETTO IN TRE RIGHE

1. ⭐⭐ **La frase da refutare è FALSA in tutt'e due i punti, e il secondo è la cura del difetto.**
   `[R]` Mutter **consegna già oggi un buffer PipeWire a ogni movimento del puntatore**, anche
   quando non cambia un pixel: `meta-screen-cast-virtual-stream-src.c:159-175` lo chiede con
   `META_SCREEN_CAST_RECORD_FLAG_CURSOR_ONLY`, e
   `meta-screen-cast-stream-src.c:1198-1202` lo spedisce con `chunk->size = 0` e dentro
   `spa_meta_cursor->position` **già in pixel di tela**.
2. ⭐⭐ **E noi quel buffer lo riceviamo, lo leggiamo, e ne buttiamo via la posizione.**
   `cattura.c:632-635` lo conta come `solo_cursore` e `cursore.c:301-321` legge solo la *forma*.
   `[M]`-da-fare `spa_meta_cursor->position` **non compare in nessuna riga di `src/`**
   (ricerca certificata, §Q1). ⇒ La cura costa **un messaggio RCP nuovo da 8 byte**, non un
   fotogramma, e **non richiede `cursor: none`** — cioè scavalca la regressione di §5 del punto
   di ripresa invece di riaprirla.
3. `[R]` E il ridimensionamento a caldo del monitor virtuale **esiste e costa una chiamata**:
   `grd_rdp_pipewire_stream_resize()` (`grd-rdp-pipewire-stream.c:336-353`) ricostruisce il POD
   del formato con la misura nuova e chiama `pw_stream_update_params()`. Nessun `RecordVirtual`
   nuovo, nessuna sessione nuova. ⇒ La strada §5.1 del briefing è **tecnicamente aperta**.

> ⭐ **La riga che cambia il prodotto**, se ne dovessi tenere una sola:
> **`grd-vnc-pipewire-stream.c:788-789`**
> ```c
> *cursor_x = spa_meta_cursor->position.x;
> *cursor_y = spa_meta_cursor->position.y;
> ```
> `[R]` È il percorso **VNC** di gnome-remote-desktop — non quello RDP — ed è l'unico dei due che
> ha il nostro stesso problema: un client che **non sa da solo** dove sta il puntatore. Loro
> leggono la posizione da ogni buffer, compresi quelli senza pixel, e la spediscono sul filo.
> Noi leggiamo lo stesso metadato e ci prendiamo solo la bitmap.

---

## ⚠ IL RIFIUTO PARZIALE DEL MANDATO — tre premesse del mandato sono sbagliate

Il briefing è avversariale, quindi lo dico prima di rispondere.

| premessa del mandato | come sta davvero |
|---|---|
| «il clone è la **51.alpha**, mentre su Trixie c'è la **48.1**: dichiara la divergenza» | ⛔ **Falso, e in nostro favore.** `[R]` `reference-gnome/gnome-remote-desktop/meson.build:2` → `version: '48.1'`, `git describe` → `48.1`; `dpkg -l` → `gnome-remote-desktop 48.1-4`. ⭐ **Il codice che ho letto è esattamente quello che gira.** Idem per mutter: clone `48.7`, installato `48.7-0+deb13u1`. `[M]` 14 ago 2026, `find` su tutta la macchina: **non esiste un secondo clone** alla 51. ⇒ Nessuna divergenza da dichiarare, e la fiducia nelle citazioni è più alta di quanto il mandato chiedesse |
| «noi iniettiamo l'input con l'interfaccia D-Bus `RemoteDesktop`» | ⛔ **Falso.** `[R]` `grep NotifyPointerMotionAbsolute\|NotifyKeyboardKeycode src/*.c` → **zero**. REMOTIX inietta con **libei/EIS**: `mutter.c:453` `ConnectToEIS`, `input.c:758` `ei_device_pointer_motion_absolute`. Certificato: la stessa ricerca su `ConnectToEIS` lo trova a `mutter.c:58,374,414,453` |
| «loro stanno sulla nostra stessa API» ⇒ implicito: D-Bus `Notify*` | ⚠ **Vero, ma non per la ragione detta.** `[R]` Anche GRD 48.1 ha abbandonato i `Notify*`: zero call-site in `.c`, tutto libei (`grd-session.c:1403-1406` `ei_new_sender`/`ei_setup_backend_fd`). ⭐ Siamo sulla stessa API **anche qui**, e la domanda 4 del briefing («il D-Bus è sincrono? quanto costa una chiamata?») **non si applica a nessuno dei due** |

⭐ **E la domanda giusta non è quella che mi è stata data.** Il mandato mi chiedeva di cercare
*«un modo di far arrivare un fotogramma quando si muove soltanto il puntatore»*. La risposta è che
**quel fotogramma arriva già**, e la domanda vera è un'altra:

> ⛔ **Perché la posizione del puntatore che Mutter ci consegna sessanta volte al secondo non
> arriva al client?**

Perché il protocollo RCP **non ha un messaggio per dirla** (§7.1: c'è `CURSORE_FORMA` `0x000A`,
non c'è nessun `CURSORE_POSIZIONE`), e quindi `cursore.c` non ha nessun posto dove metterla.

---

## Q1 · Quando il mouse si muove e non cambia niente, che cosa viaggia sul filo?

### La catena, provata riga per riga in Mutter 48.7

⭐ Vale **esattamente** per la nostra configurazione: flusso da `RecordVirtual`, `cursor-mode = 2`
(metadato). `[R]`:

| # | dove | che cosa |
|---|---|---|
| 1 | `meta-screen-cast-virtual-stream-src.c:242-249` | in modo **METADATA** si aggancia `position-invalidated` del `MetaCursorTracker` (⛔ e in modo `HIDDEN` **no**: il ramo è vuoto, `:257-258`) |
| 2 | `meta-screen-cast-virtual-stream-src.c:123-127` | `pointer_position_invalidated()` → `clutter_stage_view_schedule_update()`: **muovere il mouse programma un giro di scena** |
| 3 | `meta-screen-cast-virtual-stream-src.c:205-210` | se il giro non dipinge niente scatta il `META_STAGE_WATCH_SKIPPED_PAINT` |
| 4 | `meta-screen-cast-virtual-stream-src.c:159-175` | `on_skipped_paint()` registra con `flags = META_SCREEN_CAST_RECORD_FLAG_CURSOR_ONLY` |
| 5 | `meta-screen-cast-stream-src.c:1062-1069` | si scarta **solo se il cursore non si è mosso davvero** (`is_cursor_metadata_valid`) |
| 6 | `meta-screen-cast-virtual-stream-src.c:498-522` | e «non si è mosso» vuol dire: stessa `x`, stessa `y`, bitmap non invalidata |
| 7 | `meta-screen-cast-stream-src.c:1198-1199` | ⭐ altrimenti **esce un buffer** con `spa_data->chunk->size = 0` e `SPA_CHUNK_FLAG_CORRUPTED` |
| 8 | `meta-screen-cast-stream-src.c:1202` + `:660-676` | e `maybe_record_cursor()` ci mette dentro il metadato del cursore |
| 9 | `meta-screen-cast-stream-src.c:477-487` | per un movimento puro: `id = 1`, `position.x/y` **valorizzati**, `bitmap_offset = 0` |
| 10 | `meta-screen-cast-stream-src.c:1206-1210` | ⚠ e `header->flags = 0`: l'intestazione **non** è marcata corrotta. Solo il *chunk* lo è |

⭐ E la posizione arriva **già nelle coordinate del flusso**: `get_cursor_position()`
(`meta-screen-cast-virtual-stream-src.c:466-494`) sottrae l'origine della vista e moltiplica per
la scala **prima** di scriverla. ⇒ Per noi è **zero stadi di conversione**: è già un pixel di tela.

⚠ Il tetto: la prova di cadenza (`meta-screen-cast-stream-src.c:1093-1114`) si applica **anche**
ai fotogrammi di solo cursore, e il tetto è il `maxFramerate` che chiediamo noi. `[R]`
`cattura.c:826` lo mette a `fotogrammi_al_secondo`, che `figlio.c:1780` fissa a **60**.
⇒ **Fino a 60 posizioni al secondo**, non di più e non di meno.

### Come lo legge gnome-remote-desktop

⭐ La riga più pulita di tutto il riferimento, `[R]` `grd-pipewire-utils.c:143-147`:

```c
gboolean
grd_pipewire_buffer_has_frame_data (struct pw_buffer *buffer)
{
  return buffer->buffer->datas[0].chunk->size > 0;
}
```

E il ciclo che ne discende (`grd-rdp-pipewire-stream.c:921-985`, identico in
`grd-vnc-pipewire-stream.c:794-882`) tiene **due** ultimi buffer distinti — `last_pointer_buffer`
e `last_frame_buffer` — perché **un buffer può essere l'uno, l'altro, o tutt'e due**. Il cursore
si tratta anche quando il fotogramma non c'è (`grd-rdp-pipewire-stream.c:973-980`).

### E che cosa fa REMOTIX oggi

`[R]` sul nostro codice, e la notizia è **migliore** di quel che il punto di ripresa dice:

- `cattura.c:568` ⭐ `guarda_cursore()` è chiamata **prima di ogni scarto**, e il riquadro sopra
  (`cattura.c:455-465`) spiega perfettamente perché: *«un buffer marcato `CORRUPTED` è un buffer
  SENZA fotogramma, spedito **proprio perché** il cursore si è mosso»*. ⇒ **La cucitura c'è già.**
- `cattura.c:632-635` conta quei buffer in `conto.solo_cursore` e li restituisce.
- `cursore.c:301-321` — il ramo «la forma non è cambiata», `bitmap_offset == 0` — e lì c'è, alla
  lettera, la riga di registro: *«il puntatore è visibile e la sua forma non è ancora arrivata
  **(solo posizione)**: niente da mandare, si aspetta»*.

⛔ **Certificazione dello strumento** (regola §8 del briefing). Ricerca:
`grep -rn "position\.x\|position\.y\|->position" src/*.c src/*.h`
→ solo `cattura.c:517,523,524`, che sono `spa_meta_region.position` del **danno**, un'altra
struttura. Controprova positiva: la stessa forma di ricerca su `hotspot` (che c'è di sicuro) trova
`cursore.c:422-446`; e su `position.x` nel riferimento trova `grd-vnc-pipewire-stream.c:788`.
⇒ Lo strumento funziona, e **`spa_meta_cursor->position` non è letto da nessuna parte in REMOTIX.**

### ⛔ E un difetto concreto: il numero che proverebbe tutto non si stampa quasi mai

`[R]` `cattura.c:576` `conto.arrivati++` — conta **anche** i buffer di solo cursore.
`[R]` `cattura.c:759` `if (cattura->conto.arrivati % 300 == 0)` — la riga di registro che
stampa `solo_cursore`.
`[R]` `cattura.c:770` `restituisci:` — **e la riga di registro sta PRIMA dell'etichetta.**

⇒ Ingresso: una sessione con 60 buffer di solo cursore al secondo e 1,1 fotogrammi veri
(`[M]` 14 ago 2026). Uscita sbagliata: il modulo 300 si valuta **solo sul ramo del fotogramma
vero**, cioè su ~1,6 % degli arrivi. `[?]` La probabilità che un multiplo di 300 caschi su un
fotogramma vero è ~1,6 %; su due minuti ci sono ~23 multipli, quindi **l'attesa è di zero
stampe**. ⭐ È per questo che nessuno ha mai visto il conto `solo_cursore` — **il numero che
decide l'intera tesi di §4 del punto di ripresa è di fatto invisibile.**

⚠ Cura di una riga (non applicata: sessione di studio): spostare il blocco di registro **sotto**
`restituisci:`, oppure contare a parte gli arrivi di solo cursore con un modulo proprio.

---

## Q2 · Chi disegna il puntatore

`[R]` **gnome-remote-desktop 48.1 chiede il cursore come METADATO in ogni percorso, sempre.**
Certificato: `grep -rn "CURSOR_MODE_EMBEDDED\|CURSOR_MODE_METADATA" src/*.c *.h` →

- `grd-rdp-layout-manager.c:828` e `:835` → `GRD_SCREEN_CAST_CURSOR_MODE_METADATA`
- `grd-session-vnc.c:873` e `:882` → `GRD_SCREEN_CAST_CURSOR_MODE_METADATA`
- `GRD_SCREEN_CAST_CURSOR_MODE_EMBEDDED` compare **solo** nella definizione dell'enum
  (`grd-session.h:39`): **zero usi**.

⛔ **Correzione a `gnome-remote-desktop.md`:1 riga 564-566**, che dice *«salvo in modalità
screen-share dove si usa `CURSOR_MODE_EMBEDDED`»*. `[R]` In 48.1 **non è vero**: `EMBEDDED` non è
usato in nessun percorso. ⇒ Il riferimento fa la nostra stessa scelta, e la fa **ovunque**.

E i due percorsi divergono su **chi mette il puntatore al suo posto**:

| | RDP (`grd-rdp-cursor-renderer.c`) | VNC (`grd-vnc-pipewire-stream.c`) |
|---|---|---|
| forma | mandata al client come sprite | mandata al client come `rfbCursor` |
| **posizione** | ⛔ **mai mandata** — il client RDP *è* il posto dove il mouse vive, e sa già dove sta | ⭐ **letta e mandata**, `:788-789` |
| `has_pointer_bitmap` | richiede `bitmap_offset != 0` (`grd-pipewire-utils.c:130-137`) ⇒ un movimento puro **non** è un aggiornamento di forma | idem, ma la posizione si legge **prima**, da ogni buffer (`:775-791`) |

⭐ **Ed è qui la lezione per noi.** REMOTIX ha copiato il percorso **RDP** — solo la forma — ma
REMOTIX **non è** un client RDP: la nostra pagina non ha un puntatore di sistema di cui fidarsi
(vedi la regressione di §5 del punto di ripresa). Siamo, architetturalmente, il caso **VNC**.

Che cosa succede quando la forma cambia: `[R]` `grd-rdp-pipewire-stream.c:563-611` costruisce un
`GrdRdpCursorUpdate` (`NORMAL` con bitmap, oppure `HIDDEN` se la bitmap è vuota) e lo consegna al
renderer del cursore. È la nostra stessa logica: `cursore.c` distingue `id = 0` (nascosto),
`bitmap_offset = 0` (invariato) e bitmap vuota (nascosto) — ⭐ e la nostra è **più severa**,
perché controlla che l'offset stia dentro il metadato (`cursore.c:325-333`), controllo che GRD
sostituisce con tre `g_assert()` (`grd-rdp-pipewire-stream.c:574-576`) che in produzione sono
disabilitati o abortiscono.

### Con che ritmo spediscono la forma — ⛔ nessuno: non c'è nessun ritmo

`[R]` `grd-rdp-cursor-renderer.c` **non ha né timer, né timeout, né coda, né ritardo deliberato.**
Lo slot è **singolo**, non una coda (`:54 GrdRdpCursorUpdate *pending_cursor_update;`), il submit
sostituisce quel che c'era (`:79-82`) e sveglia subito (`:85 g_source_set_ready_time (..., 0)`).

⭐ Il risparmio lo fanno **per deduplicazione, non per attesa** — ed è la stessa scelta di
`cursore.c`:

- `[R]` `:377-383` bitmap identica alla corrente ⇒ **niente sul filo**;
- `[R]` `:385-416` cache LRU di puntatori (`:244 /* Least recently used cursor */`), misura
  negoziata col client (`:497-498 FreeRDP_PointerCacheSize`): se la forma è già in cache si manda
  un `PointerCached` di due byte invece della bitmap;
- `[R]` `:368-374` oltre **384×384** si ripiega su `SYSPTR_DEFAULT`; ≤96 → `PointerNew`, >96 →
  `PointerLarge`; tutto trasparente → `SYSPTR_NULL` (`:168-184`).

⚠ Confronto: noi tagliamo a **256** per il tetto di `RCP.md` §7.2 (`cattura.c:441-444`), loro a
384. E noi **non abbiamo una cache di forme**: rimandiamo la bitmap intera a ogni cambio. `[?]`
Costo non misurato, ma il cambio di forma è raro — non è il difetto di oggi.

---

## Q2-bis · Il ritmo dei fotogrammi — ⭐ e la conferma che il nostro 1,1 fps è *corretto*

`[R]` **Non esiste nessun orologio in tutto gnome-remote-desktop.** Cursore, superfici e layout
sono tre `GSource` con il solo `dispatch`, a riposo con `ready_time = -1`
(`grd-rdp-surface-renderer.c:796`, `:838`), armate a `0` solo da chi consegna un buffer
(`:325`, `:340`). A scena ferma la callback **non viene nemmeno invocata**: il ciclo si blocca in
`g_main_context_iteration(..., TRUE)` (`grd-rdp-renderer.c:164`).

⇒ ⭐⭐ **A scena ferma tacciono del tutto: zero traffico, zero processore, nessun battito, nessuna
chiave periodica.** ⚠ È **esattamente** quel che fa `figlio.c`, e ⛔ **conferma che il punto 1 di
§4 del punto di ripresa non è un difetto**: il riferimento che sta sulla nostra stessa API fa la
stessa identica scelta. Il difetto è **solo** il punto 2 — la posizione buttata.

Il tetto di cadenza non lo mette il server: `[R]` `grd-rdp-layout-manager.c:32`
`#define TARGET_SURFACE_REFRESH_RATE 60` finisce in `grd-rdp-pipewire-stream.c:217`
`max_framerate = SPA_FRACTION (refresh_rate, 1)`, ed è **PipeWire/Mutter** a non consegnarne di
più. ⭐ **60, come il nostro `MOVIMENTO_FPS` (`figlio.c:1780`), e per la stessa strada.**

Il controllo di flusso vero è sugli **ACK** del client, non sul tempo: `[R]`
`grd-rdp-gfx-frame-controller.c:122-124` deriva la soglia da RTT × refresh rate, e `:159-162`
mette `total_frame_slots = 0` — **rendering sospeso** — quando i fotogrammi non riscontrati
superano la soglia. `[R]` `:181` in regime attivo:
`total_frame_slots = enc_rate > ack_rate + 1 ? 0 : ack_rate + 2 - enc_rate`, cioè **si codifica
al ritmo a cui il client riesce a riscontrare**. ⚠ Noi non abbiamo niente del genere; è materia
di un'altra fase, non di questa.

### Il rilevatore di danno

`[R]` Quattro implementazioni, tutte a **tessere 64×64** (`grd-damage-detector-sw.c:28-29`,
`grd-rdp-damage-detector-memcmp.c:27`). Il cuore confronta i pixel **davvero**, `memcmp` riga per
riga con uscita alla prima differenza (`grd-damage-utils.c:34-39`). Il buffer del danno è **un
`uint32_t` per tessera**, non per pixel (`grd-damage-detector-sw.c:139-143`). La versione CUDA
confronta per pixel e poi riduce ad albero fino alla tessera 64×64
(`grd-cuda-damage-utils.cu:45-48`, `:120-121`).

⭐ **La riga dove un fotogramma senza danno viene buttato**, `[R]` `grd-rdp-renderer.c:873-878`:

```c
if (!grd_rdp_frame_is_surface_damaged (rdp_frame))
  {
    release_acquired_resource (renderer, render_context, view_creator);
    g_hash_table_iter_remove (&iter);
    continue;
  }
```

⚠ E il punto in cui lo buttano è tardi: il fotogramma è **già stato convertito** BGRX→NV12, e si
scarta **prima del codificatore**. Il predicato è `cairo_region_num_rectangles (damage_region) > 0`
(`grd-rdp-frame.c:117`). Nel percorso vecchio lo scarto è più precoce
(`grd-rdp-surface-renderer.c:633-634`).

⚠ Noi il danno lo leggiamo e lo consegniamo come **informazione** (`cattura.c:499-548`,
`guarda_danno`), senza mai scartare un fotogramma per danno vuoto. `[?]` Non so se ci convenga:
con Mutter che consegna solo quando qualcosa cambia, un fotogramma a danno vuoto dovrebbe essere
raro. Non misurato.

---

## Q3 · Il client chiede la misura del desktop al server?

`[R]` **Sì, ed è il cuore della loro architettura.** `grd-rdp-layout-manager.c` è una macchina a
stati che esiste **solo** per questo. La catena, che risponde anche alla domanda 6 del mandato:

1. La richiesta del client arriva e produce un `GrdRdpMonitorConfig`.
2. `create_or_update_streams()` (`grd-rdp-layout-manager.c:838-878`) decide, per **ogni** flusso:
   - se il flusso **non esiste ancora** → `create_stream()` (`:812-836`) → `grd_session_record_virtual()`
   - se il flusso **esiste già** → ⭐ `update_stream_params()` (`:795-810`), che chiama
     `grd_rdp_pipewire_stream_resize()`
3. `grd_rdp_pipewire_stream_resize()` (`grd-rdp-pipewire-stream.c:336-353`):
   ```c
   stream->pending_resize = TRUE;
   n_params += add_format_params (stream, virtual_monitor, &pod_builder, params, MAX_FORMAT_PARAMS);
   pw_stream_update_params (stream->pipewire_stream, params, n_params);
   ```
4. Mutter risponde con `on_stream_param_changed()` (`grd-rdp-pipewire-stream.c:408-489`), che
   ridimensiona rilevatore di danno e pool di buffer, emette `video-resized` e azzera
   `pending_resize`.

⛔ **Nessun `RecordVirtual` nuovo, nessuna sessione nuova, nessun `ConnectToEIS` nuovo.**
⇒ Lo stato dei tasti premuti **non si perde**, che è esattamente il prezzo che REMOTIX paga oggi.

### E la misura, dove entra nel POD

`[R]` `grd-rdp-pipewire-stream.c:228-243`: se c'è un `virtual_monitor`, la misura entra come
**rettangolo FISSO**; se non c'è, come intervallo aperto.

```c
if (virtual_monitor)
  {
    virtual_monitor_rect = SPA_RECTANGLE (virtual_monitor->width, virtual_monitor->height);
    spa_pod_builder_add (pod_builder, SPA_FORMAT_VIDEO_size,
                         SPA_POD_Rectangle (&virtual_monitor_rect), 0);
  }
```

⭐ **E noi facciamo già identico**: `cattura.c:878` `SPA_POD_Rectangle(&misura)`, con il commento
`cattura.c:875-877` che dà la stessa ragione (*«un intervallo aperto lascerebbe scegliere Mutter,
che sceglie 1280×720»*). ⇒ **Il meccanismo del ridimensionamento a caldo è a portata di una
funzione**: ricostruire il POD con la misura nuova e chiamare `pw_stream_update_params()`, che
`cattura.c:450` **già chiama** (in `su_parametri`).

### E l'XML lo dice

`[S]` `mutter/data/dbus-interfaces/org.gnome.Mutter.ScreenCast.xml:159-162`, la documentazione di
`RecordVirtual`:

> *«Record a virtual area that will be represented as a virtual monitor. **The width and height
> corresponds to the non-scaled intended stream size.**»*

⛔ Il metodo **non ha argomenti di misura** — né in 48.7 né altrove: `CreateVirtualMonitor`,
`SelectVirtualMonitor` e un `virtual-monitor` con `MonitorConfig` **non esistono**.
⚠ Certificazione: la stessa lettura dell'XML trova `RecordArea` (`:149-155`) che **ha** `x, y,
width, height` fra gli argomenti ⇒ se ci fossero, li vedrei. ⇒ La misura del monitor virtuale
è **e resta** una proprietà del flusso PipeWire, non della chiamata D-Bus. **Che è la strada che
già percorriamo**, e che GRD percorre due volte: all'apertura e a ogni ridimensionamento.

⇒ ⭐ **La strada §5.1 del briefing non richiede nessuna API che non abbiamo.** Richiede solo di
scegliere la misura, cioè la decisione dell'utente.

### Da dove arriva la richiesta del client, e con che limiti

`[R]` Il canale è `grd-rdp-display-control.c` (⚠ **non** `grd-rdp-dvc-display-control.c`, che non
esiste). La catena:

1. `:185` `disp_context->DispMonitorLayout = disp_monitor_layout;` — la richiesta del client
2. `:111` `disp_monitor_layout()`, con due guardie che **terminano la sessione**: PDU prima delle
   capacità (`:120-127`), troppi monitor (`:129-136`)
3. `:139-140` → `grd_rdp_monitor_config_new_from_disp_monitor_layout()` (`grd-rdp-monitor-config.c:308`)
4. `:154-155` → `grd_rdp_layout_manager_submit_new_monitor_config()` (`grd-rdp-layout-manager.c:532`)
5. `grd-rdp-layout-manager.c:539-544` — **slot singolo, l'ultimo vince**, e sveglia la sorgente

⭐ **I limiti stanno in una riga sola**, `[R]` `grd-rdp-monitor-config.c:73-80`:

```c
if (width % 2 ||
    width < 200 || height < 200 ||
    width > 8192 || height > 8192)
```

⇒ minimo **200×200**, massimo **8192×8192**, e la **larghezza** dev'essere pari.
⛔ **Nessun allineamento a 16**, e ⚠ **l'altezza non ha vincolo di parità** — asimmetria vera nel
codice, verificata a mano. E il rifiuto è **rigido**: non arrotondano, restituiscono errore e il
chiamante chiude la sessione (`grd-rdp-display-control.c:145-147`).

⚠ ⛔ **E qui `RCP.md` §7.1 è più giusto di loro**: da noi una misura fuori limiti in `ADATTA_TELA`
si rifiuta con `TELA(MISURA_FUORI_LIMITI)` invece di chiudere, ed è una scelta **dichiarata**
(eccezione 4 di §3). ⭐ *«L'utente che trascina male una finestra non deve perdere la sessione»* —
GRD invece la perde. **Non rubare questo.**

### La macchina a stati, e quanto dura il buco

`[R]` `grd-rdp-layout-manager.c:34-43`, sette stati. Il percorso di un ridimensionamento a
sessione aperta:

| stato | che cosa succede | ha un timer? |
|---|---|---|
| `AWAIT_CONFIG` | raccoglie il config e **inibisce il rendering** (`:889-893`) | no |
| `AWAIT_INHIBITION_DONE` | ⭐ attende che **tutti i contesti di render in volo** siano rilasciati (`grd-rdp-renderer.c:270-277`) | ⛔ **no**, `:896-897` è `break` |
| `PREPARE_SURFACES` | azzera le misure (`:748`), poi `create_or_update_streams()` | no |
| `AWAIT_VIDEO_SIZES` | attende la conferma da PipeWire | ⛔ **no**, `:911-913` è `break` |
| `START_RENDERING` | `uninhibit_rendering()` e si riparte (`:914-917`) | no |

⛔ **Non c'è nessun timeout, nessun watchdog, nessuna durata dichiarata** in tutto il percorso.
`[?]` La durata è quella che ci mette Mutter a rinegoziare, e **non è misurata da nessuno** — né
da loro né da me.

⭐ **Che cosa vede il client durante il buco**: l'ultimo fotogramma **congelato**, non un nero e
non uno stream interrotto — perché il rendering è inibito, non fermato.

⚠ E se la misura consegnata **non è quella chiesta**, `[R]` `:396-403` **termina la sessione**
con *«Unexpected video size change of PipeWire stream… Terminating session»*.

⛔ **E un dettaglio che ci riguarda da vicino**: `[R]` `grd-rdp-layout-manager.c:562-563` —
durante tutto il ridimensionamento **l'input del puntatore viene scartato**:

```c
if (layout_manager->state != UPDATE_STATE_AWAIT_CONFIG)
  return FALSE;
```

⚠ ⭐ È la stessa scelta che `rcp.h:462-472` prende per l'altro verso (il «secondo di grazia» sulle
coordinate vecchie, eccezione 3 di §3) — **ma opposta**: loro **buttano**, noi **tolleriamo**.
`[?]` Non so quale sia giusta; so che è una scelta che qualcuno dovrà fare consapevolmente il
giorno in cui `ADATTA_TELA` verrà servito, e che `RCP.md` l'ha già fatta e scritta.

---

## Q4 · Quanti stadi ha la conversione delle coordinate

| | stadi | dove |
|---|---|---|
| **GRD / RDP** | **3** | 1. offset del monitor nel layout, `grd-rdp-layout-manager.c:580-583` · 2. scala sulla regione EI, `grd-session.c:646-651` · 3. offset della regione, `grd-session.c:653-655` |
| **GRD / VNC** | **2** | niente offset di layout (un monitor solo); restano gli stadi 2 e 3 |
| **REMOTIX** (input) | ⭐ **1, ed è una somma** | `input.c:738-741`: se la regione è grande come la tela, `fx = reg_x + x`. Nessuna divisione |
| **REMOTIX** (pagina) | ⛔ **3** | vetro→tela, bande dentro la tela, tela→desktop |

⭐ **Nota che smentisce un pezzo del briefing.** Il briefing dice *«nessuno dei cinque studiati ne
ha più di uno»*. `[R]` **GRD/RDP ne ha tre** — e non è un difetto: sono tre stadi **sul server**,
dove i numeri sono interi e la geometria è nota, non tre stadi **sul vetro** dove ci sono
`devicePixelRatio` e bande nere. ⇒ Il problema di REMOTIX non è il numero di stadi: è **dove
stanno**.

⚠ E c'è una cosa che GRD fa e noi no: `[R]` `grd-rdp-layout-manager.c:573-577` **rifiuta** (non
satura) un punto fuori da ogni superficie, e l'evento si perde (`:587 return FALSE`). Noi
saturiamo, sul client (`pagina.html:3650-3656`). ⭐ La nostra è più giusta: saturare al bordo è
quel che fa un mouse vero.

---

## Q5 · Come si misura e come si limita la latenza dell'input

`[R]` **Nessun accorpamento, nessun limite di frequenza, nessuna coda che scarta.** In tutt'e due
i percorsi di GRD: **1 evento del client = 1 chiamata `ei_device_*` + 1 `ei_device_frame()`.**

- RDP: la coda `grd-rdp-event-queue.c` esiste **solo** per il salto di filo dal thread del socket
  FreeRDP al ciclo principale. `[R]` `:205-213` è una `g_queue_push_tail` pura senza ispezione
  dell'ultimo elemento, seguita da `g_source_set_ready_time (flush_source, 0)` — sveglia
  **subito**. `[R]` `:158` il flush drena tutta la coda **un evento per volta**.
- VNC: chiamata **diretta**, senza coda (`grd-session-vnc.c:470-486`).
- ⭐ L'**unica** ottimizzazione in tutto il riferimento: `[R]` `grd-session-vnc.c:471`
  `if (x != session_vnc->prev_x || y != session_vnc->prev_y)` — si scarta il movimento a
  coordinate **identiche**. ⚠ E noi ce l'abbiamo già, sul client: `pagina.html:3669`
  `if (x === cl_ux && y === cl_uy) return null;`

⛔ **La domanda del mandato «il D-Bus è sincrono, e quanto costa una chiamata?» non si applica**:
GRD 48.1 non usa più il D-Bus per l'input. `[R]` Certificato:
`grep -rn "call_notify_pointer\|call_notify_keyboard\|call_notify_touch" src/` → **zero** in
`.c`/`.h`, solo l'XML. Controprova positiva: `NotifyKeyboardKeycode` si trova a
`grd-session.h:110`, `grd-session.c:400`, `grd-rdp-event-queue.c:165` — ma quelle sono funzioni
**interne** il cui corpo è `ei_device_keyboard_key()` (`grd-session.c:409-410`). Lo strumento
funziona.

⇒ Il costo per evento è **una `write()` su socket UNIX**, non un giro sul bus. `[R]` `ConnectToEIS`
si chiama **una volta sola**, asincrona (`grd-session.c:1499`); poi `ei_new_sender` +
`ei_setup_backend_fd` (`:1403-1406`) e una GSource sull'fd (`:1415-1420`).

⭐ **E REMOTIX fa la stessa cosa, riga per riga.** `mutter.c:453` `ConnectToEIS`; `input.c:170-172`
`ei_device_frame` **dopo ogni evento e non a gruppi**; `input.c:85` 120 unità RCP = 10.0 di
`ei_device_scroll_delta`, e `[R]` GRD ha lo stesso numero (`DISCRETE_SCROLL_STEP 10.0`,
`grd-session-rdp.c:53`). ⇒ **Sul canale di input non c'è niente da rubare: siamo già identici.**

⚠ E questo **conferma** la quinta strada già chiusa del briefing (l'incolonnamento nel canale di
input): non è che la nostra coda funzioni per caso — è che **nemmeno il riferimento ne ha una**,
perché a questo costo non serve.

---

## Q6 · Che cosa c'è di specifico per Android, per il tocco e per DeX

⛔ **Niente, e vale la pena dirlo.** `[R]` GRD 48.1 non ha **nessun** codice per il tocco:

- `grep -n "notify_touch\|EI_DEVICE_CAP_TOUCH" src/` → zero in `.c`;
- le capacità richieste a libei sono `POINTER, KEYBOARD, POINTER_ABSOLUTE, BUTTON, SCROLL`
  (`grd-session.c:1282-1288`) — ⛔ **senza `TOUCH`**;
- i metodi `NotifyTouchDown/Motion/Up` esistono nell'XML di Mutter
  (`org.gnome.Mutter.RemoteDesktop.xml:185-211`) e **nessuno li chiama**.

⚠ Certificazione: la stessa ricerca su `EI_DEVICE_CAP_SCROLL` lo trova a `grd-session.c:1287`.
⇒ Non è una ricerca cieca: il tocco **non c'è davvero**.

⇒ Su Android, DeX e tocco, gnome-remote-desktop **non ha niente da insegnarci**. Chi cerca lì
perde tempo: le risposte stanno in `F4-AND-1/2/3/5`.

---

## Q7 · Che cosa ruberei, e che cosa NON ruberei

### ⭐⭐ DA RUBARE 1 — la posizione del cursore sul filo (il pezzo che vale il rapporto)

**Fonte**: `[R]` `grd-vnc-pipewire-stream.c:775-791` (`maybe_consume_pointer_position`) e
`:851-880` (che la impacchetta in `VncPointer` e sveglia una sorgente dedicata).

**Che cosa cambia da noi**: `cursore.c` legge `m->position.x/y` sul ramo che oggi torna 0, e RCP
guadagna un messaggio nuovo — `CURSORE_POSIZIONE`, due `u16`, sul canale di controllo, a fianco di
`CURSORE_FORMA` (`0x000A`). La pagina lo usa per muovere la freccia che **già disegna**
(`pagina.html:3642` `cl_px`/`cl_py`, `:3723` la trasformazione).

**Il costo**: `[?]` ~8 byte per movimento, fino a 60 al secondo = **~480 byte/s**, contro un
fotogramma HEVC. ⇒ Trascurabile, e **negativo** rispetto alla strada «cursore dipinto», che
costerebbe un fotogramma intero a ogni movimento.

⭐ **E perché scavalca la regressione di §5 del punto di ripresa**: oggi la pagina disegna già la
freccia **insieme** al cursore del browser (*«due puntatori sovrapposti»*, stato consegnato). La
cura non chiede di **nascondere** niente — chiede solo di far muovere quella freccia con la
**verità del server** invece che con la stima locale. ⇒ La `[?]` su `PointerIcon.TYPE_NULL` resta
aperta e **non vincola più** questa strada.

⚠ E c'è di più: la freccia guidata dal server è la **prova visibile che l'input è arrivato**, che
è precisamente ciò che manca all'utente (*«è come se si perdessero gli input»*). Oggi la freccia
locale si muove **anche se il server è morto**; con la posizione dal server si muove **solo se il
giro si è chiuso**. ⭐ È anche una misura di latenza gratuita, e a differenza del `GIRO` di §4 del
punto di ripresa **non aspetta il fotogramma successivo**.

⛔⛔ **E QUI IL RIFERIMENTO HA UN DIFETTO VERO: non copiare la sua guardia.**
`[R]` `grd-session-vnc.c:193-200`, letto e riletto a mano il 14 agosto 2026:

```c
grd_session_vnc_move_cursor (GrdSessionVnc *session_vnc, int x, int y)
{
  if (session_vnc->rfb_screen->cursorX == x ||
      session_vnc->rfb_screen->cursorY == y)
    return;
```

⛔ **Quell'`||` dev'essere un `&&`.** Ingresso: il puntatore va da `(100, 200)` a `(150, 200)` —
un movimento **puramente orizzontale**, cioè il caso più comune che esista.
Uscita sbagliata: `cursorY == y` è vero, si ritorna, e **la posizione non viene mandata**.
⇒ Nel percorso VNC di gnome-remote-desktop 48.1 il cursore si aggiorna **solo sui movimenti
diagonali**. ⚠ Il che, per inciso, è un'ottima spiegazione del perché la posizione del cursore su
VNC-GNOME sia notoriamente a scatti.

⭐ **Per noi vale doppio**: è la prova che questa cura ha un modo silenzioso di sbagliare, e che
la sua prova di collaudo deve essere *«muovi il mouse in orizzontale e conta i messaggi»* — non
*«muovi il mouse»*. La forma giusta è quella che la pagina ha già:
`pagina.html:3669` `if (x === cl_ux && y === cl_uy) return null;`

### ⭐ DA RUBARE 2 — `chunk->size > 0` al posto del bit `CORRUPTED`

**Fonte**: `[R]` `grd-pipewire-utils.c:143-147`.

Oggi `cattura.c:632-635` distingue il buffer di solo cursore dal `SPA_CHUNK_FLAG_CORRUPTED`.
⚠ Funziona — `[R]` Mutter mette quel bit (`meta-screen-cast-stream-src.c:1199`) — ma **lo mette
anche quando la registrazione è FALLITA** (`:1192-1193`, ramo `else` di `do_record_frame`).
⇒ Ingresso: una cattura fallita davvero. Uscita sbagliata: la contiamo come `solo_cursore`, cioè
**come una cosa normale**, e il guasto sparisce dal registro. GRD distingue le due con
`chunk->size`, che è il fatto positivo, invece che con un bit che ne significa due.

### ⭐ DA RUBARE 3 — la macchina a stati del ridimensionamento

**Fonte**: `[R]` `grd-rdp-layout-manager.c:838-878` + `grd-rdp-pipewire-stream.c:336-353`.
Il valore non è il codice: è **la prova che si può ridimensionare senza rifare la sessione**, cioè
la risposta alla domanda che `rcp.h:475-477` lascia aperta (*«la risposta vuole un compositore che
sappia ridimensionare»*). ⭐ **Il compositore sa.**

### ⛔ DA NON RUBARE 1 — il cursore dipinto (`cursor-mode: embedded`)

`[R]` GRD non lo usa **da nessuna parte** (§Q2). ⇒ Se il riferimento che sta sulla nostra stessa
API l'ha scartato in tutt'e quattro i suoi percorsi, la strada §5.2-prima-metà del briefing è da
chiudere: costa un fotogramma pieno per movimento e in cambio dà meno di quel che dà il metadato.

### ⛔ DA NON RUBARE 2 — i tre stadi di conversione del percorso RDP

`[R]` `grd-session.c:646-651` divide **sempre**, anche quando le due misure coincidono. `input.c`
fa una somma quando coincidono e lo dichiara quando non coincidono (`input.c:738-753`): è più
giusto, e la riga di registro che si lamenta è più giusta ancora.

### ⛔ DA NON RUBARE 3 — le `g_assert()` sul metadato del cursore

`[R]` `grd-rdp-pipewire-stream.c:574-576`: tre asserzioni su dati che vengono da un altro
processo. Il nostro `cursore.c:325-333` controlla e **dichiara**. Meglio noi.

---

## Q8 · La refutazione del mandato

> «gnome-remote-desktop NON ha nessun modo di (a) chiedere a Mutter un monitor virtuale della
> misura del client, né (b) far arrivare un fotogramma quando si muove soltanto il puntatore.»

**(a) REFUTATA.** `[R]` `grd-rdp-pipewire-stream.c:336-353`, chiamata da
`grd-rdp-layout-manager.c:795-810` a ogni cambio di configurazione dei monitor. La misura si dà
come rettangolo fisso nel POD del formato (`:228-243`) e si cambia con
`pw_stream_update_params()`, **a flusso vivo**.

**(b) REFUTATA, e più di quanto il mandato immaginasse.** `[R]` Non solo si può: **succede già,
e succede a noi.** `meta-screen-cast-virtual-stream-src.c:159-175` +
`meta-screen-cast-stream-src.c:1198-1202`. Il buffer arriva, `cattura.c:568` lo legge, e la
posizione che porta dentro finisce nel cestino perché il protocollo non ha dove metterla.

⛔ **E la conclusione del mandato — «non c'è niente da copiare» — è la parte più sbagliata.**
C'è da copiare **due righe** (`grd-vnc-pipewire-stream.c:788-789`), e sono quelle che tolgono
all'utente la sensazione che gli input si perdano.

---

## ⭐ QUEL CHE QUESTO RAPPORTO NON DICE

⛔ Obbligatoria per la regola §8 del briefing. In ordine di quanto pesa.

1. ⭐⭐ **Non ho misurato che i buffer di solo cursore arrivino davvero da noi.** Tutta la catena è
   `[R]` — letta nel codice di Mutter 48.7, che è la versione installata. Ma `[M]` **no**:
   `conto.solo_cursore` non è mai stato letto, e §Q1 spiega perché (la riga di registro è dietro
   un `goto`). ⛔ **È la prima cosa da misurare**, e costa lo spostamento di una riga.
   ⚠ Non ho potuto misurarlo io: il banco è su 192.168.0.2, e `/media/REMOTIX` **non è montato**
   su questo portatile (`[M]` 14 ago 2026, `ls` → *«File o directory non esistente»*).
2. ⚠ **Non ho verificato che `position` sia utile quanto sembra sul nostro caso.** In particolare:
   `get_cursor_position()` usa `clutter_stage_view_get_scale()`. `[?]` Su un monitor virtuale con
   scala 1 la posizione è in pixel di tela; **con una scala diversa da 1 non l'ho verificato**, e
   quel giorno arriverà se si sceglie la strada §5.1 con una misura da DeX.
3. ⚠ **Non ho verificato quanti buffer al secondo Mutter consegni davvero muovendo il mouse.**
   Il tetto letto è 60 (`maxFramerate`), ma `position-invalidated` scatta sul ritmo del
   compositore, non del mouse. `[?]` Potrebbe essere meno.
4. ⚠ **Il ritmo, il rilevatore di danno e il canale Display Control li ho fatti leggere a un
   agente parallelo**, non li ho letti io riga per riga. ⭐ Ho **riverificato a mano** le tre
   affermazioni che pesano di più — il difetto `||` di `grd-session-vnc.c:198-199`, lo scarto del
   fotogramma senza danno di `grd-rdp-renderer.c:873-878`, e i limiti di
   `grd-rdp-monitor-config.c:73-80` — e **tornano alla lettera**. ⚠ Il resto di quelle sezioni
   porta la marca `[R]` sulla fiducia di quella lettura, non della mia.
5. ⚠ **Non ho misurato il costo di un ridimensionamento a caldo, e non lo ha misurato nessuno.**
   `[R]` So che GRD lo fa senza rifare la sessione e che il flusso PipeWire **non si disconnette
   mai** (`pw_stream_update_params`, non `pw_stream_disconnect`). `[?]` **Non so quanto duri** il
   buco: nel percorso non c'è nessun timeout e nessuna durata dichiarata, e i due stati d'attesa
   sono passivi. ⚠ ⇒ Chiunque scelga la strada §5.1 dovrà **misurare quel buco**, perché è il
   tempo in cui il desktop dell'utente resta congelato a ogni cambio di finestra.
6. ⛔ **Non ho verificato che `pw_stream_update_params()` basti anche a noi.** GRD, dopo il
   ridimensionamento, rifà rilevatore di danno e pool di buffer (`grd-rdp-pipewire-stream.c:441-443`)
   ⇒ da noi servirebbe **anche di rifare il codificatore**, e `codificatore.h` dice che non è
   gratis. `[?]` Costo non stimato.
7. ⚠ **Non ho verificato la 51.alpha.** Il mandato la citava; sulla macchina **non c'è**. Se
   upstream ha cambiato qualcosa dopo la 48.1 su questi punti, io non lo so — ma è irrilevante per
   noi, perché sul nostro ferro gira la 48.1.
8. ⚠ **Non ho toccato `src/`.** Nessuna delle cure descritte è applicata, e nessuna è compilata.
   ⛔ E la strada §5.1 resta **una decisione dell'utente**: questo rapporto dice solo che
   tecnicamente è possibile, non che si debba fare.
9. ⚠ **Non ho aperto nessuna porta e non ho toccato nessun servizio.** Nessuna misura sul campo,
   nessun `git commit`. Nessun sorgente clonato: quelli in `reference-gnome/` c'erano già.
