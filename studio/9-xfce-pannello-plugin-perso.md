# Studio 9 — D-X3: il pannello XFCE perde un plugin (whisker su Xubuntu, `actions` su Debian)

Data: 18 nov 2026. Agente di studio 9. Solo diagnosi: nessun codice del prodotto toccato, nessuna prova eseguita.

Convenzioni: **[V]** verificato (dove), **[W]** dal web (qui: nessuna fonte web usata), **[S]** supposizione.
Sigle: `U:` = `/home/nicfio/Documenti/REMOTIX-UBUNTU` (codice attuale; `U:src/session.c` e `U:src/child.c` sono **identici byte per byte**
a quelli di `REMOTIX-DEBIAN` [V: `diff -q`]), `O:` = `/home/nicfio/Documenti/REMOTIX` (vecchio albero 1.5.x, sola lettura).
Sorgenti veri Ubuntu 26.04 nel contenitore `studio-9` (cartella `/media/REMOTIX-UBUNTU/studio/9/`): `xfconf-4.20.0`, `xfce4-panel-4.20.7`,
`xfce4-session-4.20.4`, `xfce4-whiskermenu-plugin-2.10.1`, `xubuntu-default-settings 26.04` (estratto in `xds/`). Indicati come `X:<pacchetto>/...`.

---------------------------------------------------------------------------------------------------

## 1. Riassunto

**Ipotesi principale (H1, certezza alta sul meccanismo, media sull'ultimo gradino):** REMOTIX scrive nel file di blocco della sessione
(`$XDG_RUNTIME_DIR/remotix/xdg-xfce/.../xfce4-panel.xml`, letto da xfconfd come file *di sistema*) **anche il tipo del plugin** che
protegge (`plugin-1 = whiskermenu`, su Debian `plugin-10 = actions`). Per xfconf, un valore uguale a quello di sistema **non viene mai
scritto nel file dell'utente**: il file dell'utente resta con `plugin-1 type="empty"`. Finché il blocco è in memoria il plugin si vede
(valore ereditato dal «sistema»), ma sul disco il plugin non ha più un tipo suo. Poi, quando il ripristino lavora **con il blocco ancora
nella memoria di xfconfd** (succede dopo la chiusura «leggera»), `xfconf_set()` dice «messo» (rilegge il valore *effettivo*, che è quello
del blocco) senza aver scritto nulla, la chiave esce dalla copia, e subito dopo — riavviato xfconfd senza blocco — l'`unset` degli ultimi
figli (`show-command-*`) fa **cadere a cascata anche il padre `plugin-1`** (nodo senza valore e senza figli). Il pannello si ritrova con
`plugin-ids = 1…9` ma senza `/plugins/plugin-1`: alla partenza dopo si apre la finestra «Plugin could not be loaded, remove?» e,
con «Remove», il plugin è perso per sempre.

Perché proprio quel plugin: è **l'unico** plugin per cui REMOTIX scrive un nodo con tipo nel file di blocco (whisker su Xubuntu; `actions` su
Debian/Fedora/Arch). Gli altri plugin (`separator`, `tasklist`, …) hanno il loro valore scritto dal pannello nel file dell'utente.
Su openSUSE non si vede perché il tipo del plugin sta anche in un `xfce4-panel.xml` di sistema vero: sopravvive al ripristino.

**Cura proposta (una regola generale, desktop-indipendente):** REMOTIX non deve mai definire nel file di blocco un valore che non gli serve
bloccare. Nel blocco il nodo del plugin deve essere `type="empty"` (come già il padre `plugins`), con solo i figli bloccati.
In più due cinture: (a) il ripristino non conta come «fatto» un plugin se non è scritto nel file dell'utente; (b) un controllo finale
«ogni id di `plugin-ids` ha il suo tipo», con riparazione da copia o da `default.xml`.

**Prova che distingue (senza REMOTIX, 2 minuti):** §8, prova P1 (xfconf puro in un D-Bus privato) e P2 (sulla macchina Xubuntu: leggere il file
dell'utente a sessione aperta: prevista `plugin-1 type="empty"`).

---------------------------------------------------------------------------------------------------

## 2. Che cosa fa REMOTIX alla configurazione XFCE dell'utente (ricostruzione passo per passo)

Tutto in `U:src/session.c` (stesso file in `REMOTIX-DEBIAN`). Cosa REMOTIX **non** fa: non scrive file nei suoi `~/.config/xfce4/panel/` né
in `~/.config/xfce4/xfconf/` a mano; non usa kiosk né `xfce4-session` rc. Tocca la configurazione solo (1) con file *di sistema* in
`XDG_RUNTIME_DIR`, letti da xfconfd tramite un drop-in systemd, (2) con comandi `xfconf-query` (scrittura nel canale dell'utente) al ripristino,
(3) con una copia dei valori dell'utente in `~/.local/state/remotix/xfce-chiavi`.

### 2.1 Nascita della sessione (`session_born` → `session.c:7053` poi `:6773`)
1. `session_clear_out_handler("birth: leftovers from before")` (`:7053`, corpo `clear_out_handler_run` `:3948-4133`): toglie i drop-in nostri; `daemon-reload`
   (`:4013`); **riavvia xfconfd solo se ha tolto un drop-in suo in questa chiamata** (`xfconfd |= ...` `:3982`, `else if (xfconfd) run(restart)` `:4020-4021`);
   poi `xfce_restore_keys()` (`:4032`, se non è chiusura «leggera»).
2. `xfce_session_xfconf()` (`:6507-6726`, chiamata da `:6773`):
   - `:6542` `xfce_restore_keys()` di nuovo (copia di una sessione morta male) e `:6543` `xfce_migrate_old()`.
   - `:6546-6552` **la copia**: per ogni chiave bloccata (`XFCE_LOCKS` `:6345-6372`, 11 chiavi di `xfce4-session` e `xfce4-power-manager`) e per il pannello
     (`xfce_panel_xml()` `:6432-6505`) `xfce_copy_note()` (`:5244-5263`) annota il valore dell'utente **letto con `xfconf-query` (valore effettivo)**
     o «absent» se non c'è o se è uguale a un valore dei file di sistema veri (`xfce_same_as_system()`; la cartella `/remotix/xdg-xfce` è esclusa apposta, `:4924-4926`).
     Per i plugin del pannello annota: il **plugin stesso** (`kind=plugin`, `:6463`, `:6486-6488`) e le sue chiavi figlie (`items` per `actions`, `show-command-*`
     per il whisker, `WHISKER_HIDE` `:6424-6426`).
   - `:6563-6601` copia scritta su disco `~/.local/state/remotix/xfce-chiavi` (0600); `[stato] ripristinato=false`.
   - `:6603-6637` i **file di blocco** in `$XDG_RUNTIME_DIR/remotix/xdg-xfce/xfce4/xfconf/xfce-perchannel-xml/`: `xfce4-session.xml`, `xfce4-power-manager.xml`
     (`xfce_channel_xml()` `:6375-6405`) e `xfce4-panel.xml` (`xfce_panel_xml()`).
   - `:6639-6663` drop-in `…/user.control/xfconfd.service.d/zz-remotix-session.conf` con `XDG_CONFIG_DIRS=<cartella nostra>:<resto>`, `daemon-reload`, `try-restart xfconfd`.
   - `:6666-6725` rilettura degli effetti (valori effettivi).

   **Il file di blocco del pannello** (`:6451-6503`), cuore del problema:
   ```
   <channel name="xfce4-panel">
     <property name="plugins" type="empty">
       <property name="plugin-1" type="string" value="whiskermenu">      <!-- TIPO DEL PLUGIN: valore di SISTEMA -->
         <property name="show-command-lockscreen" type="bool" value="false" locked="<utente>"/> ... (6 chiavi)
       </property>
     </property>
   </channel>
   ```
   (per `actions`: `plugin-N type="string" value="actions"` con figlio `items` array `locked`, `:6468-6477`). [V]

### 2.2 Durante la sessione
Nulla di attivo. Il pannello, appena nato, **migra `default.xml`** nel canale (`X:xfce4-panel/panel/panel-application.c:211-219` chiama `migrate`;
`X:xfce4-panel/migrate/main.c:68-105`: se `/panels` non esiste applica `xfce4/panel/default.xml` con `xfconf_channel_set_property()` una proprietà alla volta,
`migrate-default.c:213`). xfconfd scrive il file utente **5 s dopo l'ultima modifica** (`WRITE_TIMEOUT 5`, `X:xfconf/xfconfd/xfconf-backend-perchannel-xml.c:71`, `:1003-1023`) e
alla chiusura regolare (SIGTERM/SIGINT/SIGHUP → `g_main_loop_quit` `main.c:163-165,105`; `finalize` fa il flush `:231-247`). Con SIGKILL si perdono al massimo gli ultimi 5 s.

### 2.3 Chiusura ordinata (Log Out)
`exit_xfce()` (`:3685-3706`, `org.xfce.Session.Manager.Logout`) → sessione finita → `session_clear_out_handler_due()` / `session_terminate()` (`:4447`):
`clear_out_handler_run()`: drop-in tolto → `daemon-reload` → **`try-restart xfconfd`** (`:4020-4021`; qui xfconfd esce senza blocco) → **`xfce_restore_keys()`** (`:4032`) con
xfconfd *nuovo*, senza blocco in memoria. È il percorso che funziona (prova S9b di `O:`: «13 locked keys put back», plugin tornato `actions`).

### 2.4 Chiusura forzata
`kill_xfce()` (`:3708-3743`) manda SIGTERM a `labwc`; i client Wayland (pannello, wrapper dei plugin) cadono con la connessione; poi stessa pulizia di 2.3. xfconfd
**non viene toccato** (è un'unità utente, non nello scope della sessione). Per la configurazione è equivalente alla 2.3. [V]

### 2.5 Chiusura «leggera» (l'utente ha una sessione locale), `child.c:9921-9980`
`local_light_close()` → `session_clear_out_light()` (`session.c:4121-4133`) = `clear_out_handler_run()` con `clear_out_local=TRUE`:
- toglie il drop-in e fa `daemon-reload` (`:4013`);
- **NON riavvia xfconfd** (`:4015-4019`: «it is the one of the user's LOCAL desktop»);
- **NON ripristina le chiavi** (`:4026-4031`).
Conseguenza [V da codice]: dopo la chiusura leggera xfconfd, vivo, ha ancora in **memoria** il file di blocco (letto all'apertura del canale, `load_channel`
`xfconf-backend-perchannel-xml.c:1669-1730`), anche se il drop-in non c'è più su disco; la copia resta `ripristinato=false`.

### 2.6 Ripristino (`xfce_restore_copy()` `:5348-5453`)
Per ogni gruppo `kN` della copia, nell'ordine in cui è stata scritta (plugin **prima** dei suoi figli, `:6463-6464`, `:6486-6498`):
- `kind=plugin` (`:5377-5398`): se `!absent` oppure (`any` e nessun valore *di sistema vero*) → `xfconf_set(canale, chiave, "string", valore)`; altrimenti `xfconf_unset()`.
- `absent` (`:5399-5400`): `xfconf_unset()` (scrive `x` con `-n`, poi `-r`, poi rilegge, `:4975-5002`).
- `array`/scalare: `xfconf_set_array` / `xfconf_set`.
- `ok` = il comando ha avuto successo **e la rilettura del valore effettivo coincide** (`xfconf_set` `:4776-4790`).
- Fine: `try-restart xfconfd` se c'è almeno una chiave (`:5421-5422`) — scrive il canale sul disco.
- Ripristino parziale (`:5437-5452`): i gruppi riusciti **escono dalla copia subito**; restano solo quelli che non sono tornati.

---------------------------------------------------------------------------------------------------

## 3. Osservazioni del difetto (vecchio albero, ogni dato)

| Dove | Distro / tipo di chiusura | Plugin | Fatti [V: letti nei file indicati] |
|---|---|---|---|
| `O:assessment/xfce/difformita.md:33-60` | Debian 13 `prova`, chiusura leggera (scenario B, locale arrivato) | `plugin-10` (`actions`) | `default.xml:69` lo ha; `panel-1/plugin-ids` dell'utente = `1…10`; file utente (mtime 09:35:14) senza `plugin-10`, altri 17 plugin presenti; journal 09:34:07 «light mode — the XFCE keys are NOT restored», 09:35:15 «`/plugins/plugin-10/items NOT put back`», poi a ogni nascita «no `actions` nor `whiskermenu` plugin in the panel nor in default.xml — no entry to lock» |
| stesso, riga 45-47 | Debian `nuovo1` | `plugin-10` | la copia fatta alla **prima nascita** segna `[k11] path=/plugins/plugin-10 kind=plugin absent=true` |
| stesso, riga 48-51 | Debian `nuovo1`, **logout pulito** | `plugin-10` | ripristino «13 locked keys put back»: `plugin-10` **resta** `actions` ⇒ il percorso 2.3 funziona. Durante la prima sessione il file utente aveva `plugin-10 type="empty"` con `items` vuoto (09:45:53) |
| stesso, 54-60 + `ubuntu2604.md:32,42,44` | **Xubuntu 26.04** `prova`, chiusura leggera 10:35:04 | `plugin-1` (whisker) | ripristino 10:36:15 «`/plugins/plugin-1/show-command-* NOT put back`»; default Xubuntu `plugin-1…9`, file utente (10:36:16) con `plugin-2…9` e **nessun `plugin-1`** |
| `ubuntu2604.md:44` (S9) | Xubuntu `nuovo1`, logout fatto mentre il client si staccava | `plugin-1` | il ripristino non c'è ancora stato (`ripristinato=false`) e il file utente ha `plugin-1" type="empty"`; whisker bloccato con 17 chiavi, `[k11] path=/plugins/plugin-1 kind=plugin plugin=whiskermenu`, `k12-k17 show-command-*` |
| `fedora44.md:22`, `arch.md:27` | Fedora 44, Arch XFCE | `plugin-10` | come Debian: `…/plugins/plugin-10/items NOT put back` (11:12:11, 11:52:25), poi «no actions nor whiskermenu…»; Arch `nuovo1`: `plugin-10" type="empty"` |
| `tumbleweed.md:22`, `leap16.md:21` | openSUSE Tumbleweed e Leap 16, chiusura leggera | `plugin-1` (whisker) | **NON riprodotto**: stesse righe `plugin-1/show-command-* NOT put back`, ma il whisker resta: «il tipo dei plugin viene dal default di sistema di xfconf e il file utente tiene solo `type="empty"` (13 plugin su 13)» |
| `O:assessment/RAPPORTO.md:70-75`, `fase3-xfce-lxqt.md:36-45` | sintesi | | ipotesi di allora: `xfce_system_value()` guarda solo `xfce-perchannel-xml` e non `default.xml` ⇒ `xfconf_unset()` toglie la chiave. Nota loro: «durante la chiusura leggera la sessione LOCALE parte con il plugin già come `type="empty"`» (deduzione) |

Nessun journal grezzo è rimasto sul tablet né sul server (`journal-completo.txt` citati nei rapporti non esistono più: cercati in `/home/nicfio/Documenti` e `/media`).
Nessuna osservazione su altre cause di chiusura (SIGKILL, crash di xfconfd, wrapper del plugin) è presente nel vecchio albero: **il difetto è stato visto solo dopo la chiusura leggera** (4 distro) e
**mai dopo logout pulito** (Debian `nuovo1` S9b); su openSUSE mai.

Cercato anche in `DECISIONS*.md`, `LESSONS.md`, `CHANGES-1.5.md`: nessun'altra riga su D-X3 (`CHANGES-1.5.md:316-325` parla solo del blocco del whisker; `DECISIONS.md:7210` del pannello Xubuntu da D-153).

---------------------------------------------------------------------------------------------------

## 4. Come funzionano davvero xfconf e il pannello (sorgenti veri Ubuntu 26.04)

Tutti [V] nei sorgenti estratti.

1. **Un valore uguale a quello di sistema non si scrive** — `X:xfconf/xfconfd/xfconf-backend-perchannel-xml.c:289-356` (`_set`): se la proprietà esiste e
   `_xfconf_gvalue_is_equal(valore_utente_se_c'è, altrimenti system_value, nuovo)` → **`return TRUE` senza memorizzare nulla**. Se è bloccata → permesso negato.
   Il test di uguaglianza tra tipi diversi/non inizializzati dà FALSE (`xfconf/common/xfconf-gvaluefuncs.c:313-327`), quindi su un nodo *senza* valore di sistema il valore viene memorizzato.
2. **Il file utente contiene solo il valore dell'utente** — `write_node` (`:1862-1929`) scrive `prop->value`; un nodo che ha solo `system_value` (o solo figli) esce `type="empty"`,
   figli compresi. Quindi un blocco di sistema trasforma il file utente in un elenco di segnaposto vuoti (osservato: `plugin-10`/`plugin-1 type="empty"`).
3. **Lettura**: i file di sistema si leggono in ordine inverso di `XDG_CONFIG_DIRS`, poi il file utente (`load_channel` `:1669-1730`; `handle_property` `:1150-1437`). Un `type="empty"` dell'utente
   non cancella il `system_value`. Il blocco è per-proprietà (`locked="<utente>"`).
4. **`reset` non ricorsivo** (`xfconf_proptree_reset` `:888-942`, richiamato da `xfconf-query -r`): vale solo se il nodo ha un *valore utente*; se il nodo ha figli o `system_value`
   si limita a svuotare il valore; **altrimenti toglie il nodo e poi risale togliendo ogni padre che non ha valore (utente o di sistema) né altri figli** (`:906-935`). ⇒ togliere l'ultimo
   figlio di un nodo senza valore cancella il nodo.
5. **Pannello, caricamento** (`X:xfce4-panel/panel/panel-application.c`, `load_real` `:381-540`): per ogni id di `/panels/panel-N/plugin-ids` legge `/plugins/plugin-<id>` come stringa;
   se `name == NULL` o `panel_application_plugin_insert()` fallisce, **apre una finestra modale** (`panel_application_remove_plugin_dialog` `:346-378`: «Plugin "%s" could not be loaded, do you want to remove it
   from xfce4-panel configuration?», predefinito **Quit**). Con «Remove»: `xfconf_channel_reset_property(.., TRUE)` ricorsivo e `panel_application_save(SAVE_PLUGIN_IDS)` (`:476-486`, `:540`): il plugin sparisce anche da `plugin-ids`.
   Con «Quit»: `gtk_main_quit()`: il pannello esce. Finché la finestra è aperta **gli id successivi non vengono caricati** (il ciclo è fermo in `gtk_dialog_run`).
6. **Plugin esterno che muore** (`panel-plugin-external.c:405-480`, `PANEL_PLUGIN_AUTO_RESTART 60` s, `common/panel-private.h:88`): il primo crash è riavviato in silenzio; il secondo entro 60 s apre «unexpectedly left the panel, restart?» con
   predefinito **Execute**; si toglie il plugin solo se qualcuno preme «Remove». Il whisker è esterno (`X-XFCE-Internal=false`, `X:xfce4-whiskermenu-plugin/panel-plugin/*.desktop:8`). Niente rimozione automatica.
7. **Whisker 2.10.1** salva su xfconf solo `favorites`, `recent`, `search-actions` quando modificati (`settings.cpp:287-289, 757-781, 1017-1055`); le sei `show-command-*` sono solo lette. Non scrive il tipo del plugin.
8. **File di sistema veri di Ubuntu 26.04**: nessun `xfce4-panel.xml` in `xfce-perchannel-xml` né in `xdg-xubuntu` né in `xfce4-panel` (solo `…/panel/default.xml`). `xdg-xubuntu/xfce4/panel/default.xml`:
   `plugin-1 = whiskermenu` **senza figli**, `plugin-3 tasklist` con figli, …, `plugin-9 clock`; **nessun `actions`**. [V: `xds/etc/xdg/xdg-xubuntu/xfce4/panel/default.xml`; `dpkg-deb -c xfce4-panel_4.20.7`] 

---------------------------------------------------------------------------------------------------

## 5. Ipotesi, in ordine di probabilità

### H1 — Il tipo del plugin è un valore «di sistema» nel blocco, mai scritto nel file utente; il ripristino a blocco ancora in memoria lo dà per fatto e poi lo cancella a cascata (≈ 80%)

Sequenza (una chiusura leggera + la nascita successiva; utente il cui canale `xfce4-panel` era vuoto alla prima nascita, es. `prova`, `nuovo1`):

1. **Prima nascita** (canale vuoto): `panel_plugins()` non trova nulla (`any=FALSE`, `:6441-6447`) e prende `plugin-1` da `default.xml` (`:6446`, `:5118-5153`).
   Copia: `plugin-1 kind=plugin absent=true`, `show-command-* absent=true`. Blocco scritto con `plugin-1 type="string" value="whiskermenu"` come valore di **sistema** (`:6489-6491`). [V]
2. **Il pannello migra `default.xml`**: `xfconf_channel_set_property("/plugins/plugin-1", "whiskermenu")` → `_set`: uguale al `system_value` → **`return TRUE`, nulla memorizzato** (§4.1).
   Gli altri plugin sono memorizzati. Dopo ≤5 s il file utente ha `plugin-1 type="empty"` + sei figli `empty` (§4.2). [V da sorgente; **coerente con l'osservato**: `nuovo1` `plugin-1" type="empty"` (`ubuntu2604.md:44`), `plugin-10 type="empty"` con `items` vuoto (`difformita.md:50`)]
3. **Chiusura leggera**: drop-in tolto, **xfconfd non riavviato, niente ripristino** (§2.5). Il blocco resta in memoria; la copia resta `ripristinato=false`. Il desktop locale, con lo stesso xfconfd, vede ancora il whisker (valore ereditato).
4. **Nascita successiva** (`session.c:7053`): `clear_out_handler_run` trova il drop-in già tolto ⇒ `drop=0`, `xfconfd=FALSE` ⇒ **nessun riavvio**; poi `xfce_restore_keys()` (`:4032`) **a blocco in memoria**:
   - `show-command-*` (absent ⇒ `xfconf_unset`): bloccate ⇒ fallisce ⇒ «**NOT put back**» (è esattamente la riga osservata, `ubuntu2604.md:42` e `difformita.md:55`; prova che il blocco era ancora attivo [V da log]).
   - `plugin-1` (`kind=plugin`, `absent=true`, `any=TRUE`, nessun valore di sistema vero ⇒ ramo `xfconf_set`, `:5390-5395`): `xfconf_set(…, "whiskermenu")` ⇒ il demone risponde «uguale al sistema, ok, non scrivo»; la rilettura dà `whiskermenu` ⇒ **`ok=TRUE`** (`:4776-4790`). Il gruppo è dato per fatto ed **esce dalla copia** (`:5439-5440`).
   - fine: `try-restart xfconfd` (`:5421-5422`): xfconfd si riavvia **senza blocco** e scrive il file (`plugin-1 empty`).
5. Subito dopo `xfce_session_xfconf()` (`:6542`) richiama `xfce_restore_keys()`: restano in copia solo i sei figli, ora **non più bloccati**. Per ciascuno `xfconf_unset` (`x` poi `-r`). Al sesto, `xfconf_proptree_reset` toglie il nodo e, risalendo, **toglie anche `plugin-1`** (nessun valore, nessun figlio, nessun valore di sistema, §4.4).
   `try-restart` ⇒ il file (10:36:16) non ha più `plugin-1` [V da codice; coerente con `ubuntu2604.md:42`: «file utente (10:36:16) con plugin-2…9 e nessun plugin-1»]. `plugin-ids` resta `1…9` (nessuno lo tocca; coerente con Debian `plugin-ids = 1…10`).
6. Da qui, ogni nascita: `xfce-panel_xml()` non trova più il plugin ⇒ «no `actions` nor `whiskermenu` plugin … no entry to lock» (`:6633-6635`; osservato su Debian, `difformita.md:42`) ⇒ nessuna protezione sulle voci di spegnimento (su Xubuntu: tutta la protezione).
7. Alla partenza del pannello (remota o locale) `/plugins/plugin-1` è `NULL` ⇒ finestra «could not be loaded, remove?» (§4.5). Con «Remove» la perdita diventa permanente anche in `plugin-ids`.

**Perché proprio quel plugin**: solo per i plugin che REMOTIX tocca (whisker, `actions`) il file di blocco definisce un nodo `plugin-N` con tipo di sistema (`:6468-6471`, `:6489-6491`).
Per tutti gli altri il tipo lo scrive il pannello come valore utente. Su Xubuntu il pannello non ha `actions` (§4.8) e perciò il solo nodo toccato è `plugin-1`.

**Perché non su openSUSE** [V: `tumbleweed.md:22`, `leap16.md:21`]: lì esiste un `xfce4-panel.xml` di sistema vero con i tipi; dopo il ripristino senza blocco il tipo di sistema resta e il plugin vive anche se il file utente ha solo `type="empty"` (osservato: «13 plugin su 13» vuoti, nessuna perdita).

**Perché non dopo logout pulito**: lì (§2.3) xfconfd è riavviato **prima** del ripristino; `xfconf_set(plugin-1,"whiskermenu")` trova il nodo **senza** valore di sistema e **memorizza** il valore utente; l'`unset` dei figli si ferma al padre perché ha un valore (§4.4). Prova osservata: `nuovo1` S9b, Debian.

*A favore*: tutto il filo regge con file, righe e orari osservati; spiega Debian/Fedora/Arch/Ubuntu e l'assenza su openSUSE; spiega perché `plugin-ids` resta; spiega «NOT put back» (blocco in memoria); spiega il messaggio successivo «no entry to lock».
*Contro / incognite*: nessun log di xfconfd grezzo; l'ordine esatto delle ultime due chiamate (primo ripristino a `:7053`, secondo a `:6542`) è dedotto dal codice e dagli orari (10:36:15 log, 10:36:16 file), non da trace; se il whisker avesse scritto un figlio non bloccato (es. `favorites`, §4.7) sotto `plugin-1`, la cascata si sarebbe fermata: sul banco evidentemente non c'era [S].

### H1b — Stessa causa, perdita senza alcun ripristino REMOTIX (≈ incluso nel 80%; variante)
Dopo la chiusura leggera il file utente ha già `plugin-1 type="empty"` (passo 2). Basta che xfconfd si riavvii senza blocco (riavvio della macchina, `systemctl --user restart xfconfd`, fine sessione locale con ripresa dopo) perché il plugin abbia nessun tipo: alla prima partenza del pannello compare la finestra (§4.5) e «Remove» lo cancella.
Spiega la nota del vecchio rapporto («la sessione LOCALE parte con il plugin già `type="empty"`», `fase3-xfce-lxqt.md:39`) e il caso `nuovo1` di Ubuntu (logout fatto mentre il client si staccava, `ripristinato=false`, `plugin-1 type="empty"`, `ubuntu2604.md:44`).
Conseguenza: anche correggendo solo il ripristino, finché il blocco definisce il tipo, ogni sessione lascia un file utente «vuoto» fino al ripristino: **serve togliere la causa** (cura C1).

### H2 — Ipotesi del vecchio rapporto: `xfconf_unset()` sul plugin perché `xfce_system_value()` non guarda `default.xml` (≈ 8%)
(`O:assessment/RAPPORTO.md:70-75`, `fase3-xfce-lxqt.md:39`). Il ramo `unset` per `kind=plugin` (`:5396-5398`) si prende solo se `absent` **e** (`!any` **oppure** esiste un valore di sistema vero).
Su Xubuntu/Debian non esiste nessun `xfce4-panel.xml` di sistema (§4.8) ⇒ il secondo caso è impossibile; `any` è TRUE perché gli altri plugin ci sono. E anche se `xfconf_unset(plugin-1)` fosse eseguito a blocco in memoria,
`xfconf_proptree_reset` lascerebbe il nodo (ha figli e `system_value`, §4.4). Quindi **non basta a rimuovere il nodo**. Resta possibile solo per un utente il cui canale non elenca ancora plugin (`any=FALSE`) al momento del ripristino [S].

### H3 — Il pannello/wrapper del whisker muore e il pannello rimuove il plugin da solo (≈ 3%)
Contro [V]: la rimozione automatica non esiste (§4.6): serve un clic su «Remove» e il predefinito è «Execute»; con la sessione che cade l'intero pannello muore con la connessione Wayland, senza finestra.
Non spiega perché `plugin-ids` resti intatto su Debian né perché il difetto compaia solo dopo la chiusura leggera né perché non su openSUSE.

### H4 — xfconfd/pannello uccisi a metà scrittura (SIGTERM/SIGKILL) (≈ 2%)
xfconfd scrive via file `.new` + `rename` con `fdatasync` (`flush_channel` `:1931-2032`): niente file troncati. SIGTERM → flush (§2.2). SIGKILL → perde al più 5 s, non cancella un plugin. Il pannello non tiene il file.
Contro: lo stesso difetto è deterministico dopo la chiusura leggera (4 distro su 4), non casuale.

### H5 — Finestra «Remove» premuta da un utente/script nel locale (≈ 7%, ma solo come ultimo gradino di H1b)
Non è una causa indipendente: la finestra compare solo se il tipo è già perso (§4.5).

---------------------------------------------------------------------------------------------------

## 6. Cure proposte in REMOTIX (regola generale: nessuna pezza per una distro)

Regola da scrivere nelle decisioni: **«REMOTIX blocca solo le chiavi foglia che deve bloccare; non definisce mai nei file di blocco un valore (tipo di plugin compreso) che l'utente deve poter possedere. Un nodo che esiste solo perché serve da padre ai blocchi è `type="empty"`.»**
Vale per qualunque desktop e distro (XFCE: pannello, `xfce4-session`, power manager; GNOME/KDE hanno già meccanismi senza file utente).

### C1 — Causa: il padre del plugin nel file di blocco diventa `type="empty"` (applica H1, H1b)  — peso piccolo
Dove: `U:src/session.c:6468-6471` (`actions`) e `:6489-6491` (whisker), dentro `xfce_panel_xml()`.
In parole: invece di `<property name="plugin-1" type="string" value="whiskermenu">` scrivere `<property name="plugin-1" type="empty">`. Restano uguali i figli bloccati.
Pseudo-codice:
```
// prima
append("<property name=\"%s\" type=\"string\" value=\"whiskermenu\">", base+9);
// dopo
append("<property name=\"%s\" type=\"empty\">", base+9);   // il tipo lo possiede l'utente: lo scrive il pannello (migrazione di default.xml)
```
Conseguenze:
- Nuovo utente: la migrazione del pannello fa `set plugin-1 = whiskermenu` su un nodo **senza** valore di sistema ⇒ **memorizzato** nel file utente (§4.1, test di uguaglianza FALSE su tipi diversi).
- Il padre ha sempre un valore utente ⇒ l'`unset` dei figli non lo cancella (§4.4), a blocco in memoria o no.
- `kind=plugin` nella copia e il ramo `:5377-5398` diventano inutili per le copie nuove: **non rimuoverli subito** (copie vecchie ancora in giro); trattarli come «verifica, non scrittura» (vedi C2).
- `panel_plugins("whiskermenu"/"actions")` (`:5084-5107`) legge il tipo con `xfconf-query -l -v`: con il padre vuoto in sistema e il valore utente presente continua a trovarlo (il valore è del canale). Per l'utente senza canale usa `default.xml` come oggi.
Rischi: (a) da verificare con la prova P1 che xfconfd 4.20 memorizzi davvero il valore del padre quando il nodo di sistema è `empty` con figli bloccati [S, atteso sì: il padre `plugins` è già così]; (b) se la migrazione del pannello avvenisse **prima** che il blocco sia letto non cambierebbe nulla (il valore è comunque utente).
Danneggiati già esistenti: servono C2/C3 per riparare chi ha già perso il plugin.

### C2 — Cintura nel ripristino: «fatto» significa «scritto nel file dell'utente», non «rilettura uguale» (applica H1, H1b)  — peso medio
Dove: `xfce_restore_copy()` `U:src/session.c:5348-5453`, ramo `kind=plugin` `:5377-5398` e `xfce_restore_keys()` `:5459-5467`.
Due modifiche, entrambe generali:
1. **Mai ripristinare con un blocco ancora in memoria.** Prima di `xfce_restore_keys()` controllare se l'xfconfd in esecuzione ha ancora la cartella di blocco: leggere `/proc/<MainPID di xfconfd.service>/environ` (o `systemctl --user show -p MainPID`) e cercare `/remotix/xdg-xfce`.
   - Se c'è e la chiusura è normale (non leggera): `try-restart xfconfd` **prima** del ripristino (oggi lo fa solo se ha tolto un drop-in in quella chiamata, `:3982`, `:4020-4021`).
   - Se c'è e siamo in chiusura leggera/nascita con il desktop locale vivo: **non ripristinare niente e lasciare la copia intatta** (nessun gruppo esce) — oggi `plugin-1` esce come «fatto».
   ```
   gboolean lock_in_xfconfd(void){ pid=MainPID("xfconfd.service"); return pid && environ_contains(pid,"/remotix/xdg-xfce"); }
   xfce_restore_keys(){ if (lock_in_xfconfd()) { if (!local_session_alive()) restart_xfconfd(); else return FALSE /*pending*/; } ... }
   ```
2. **Dopo un `xfconf_set` di `kind=plugin`** non fidarsi della rilettura effettiva: considerarlo fatto solo se nessun valore di sistema (blocco compreso) lo copre, cioè dopo il passo 1. In alternativa leggere il file `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml` dopo il `try-restart` finale e controllare `name="plugin-N" … value="…"`; se manca, **lasciare il gruppo nella copia**.
   Per le chiavi figlie vale lo stesso principio: `xfconf_unset` riuscito su un figlio è sicuro solo se il padre ha un valore utente (altrimenti cancella il padre, §4.4): controllare e, se il padre non ha valore, scriverglielo prima dall'ultima copia/`default.xml`.
Rischi: in chiusura leggera il ripristino resta in sospeso fino alla prossima sessione REMOTIX *senza* desktop locale (già la regola per le chiavi, comportamento dichiarato `:5185-5193`); cerca di non moltiplicare il rumore nel log (una riga sola).

### C3 — Cintura finale generale: ogni id di `plugin-ids` deve avere il suo tipo  — peso medio
Dove: nuova funzione `xfce_panel_integrity()` chiamata alla fine di `xfce_restore_copy()` (dopo `:5421-5422`) e in `xfce_session_xfconf()` prima di costruire il blocco (`:6552`).
In parole: leggere `/panels/panel-N/plugin-ids` (`xfconf-query -c xfce4-panel -p … -v`, array di int); per ogni id verificare che `/plugins/plugin-<id>` abbia un valore.
Se manca: prendere il tipo (1) dalla copia (`kind=plugin`, campo `plugin`/`value`), altrimenti (2) da `default.xml` lungo `XDG_CONFIG_DIRS` per lo stesso numero (funzione `default_plugins()` `:5118-5153` già legge la tabella; qui serve la mappa id→tipo); scriverlo con `xfconf_set` (solo se il blocco non è in memoria, vedi C2.1); registrare una riga ⭐ «plugin-N riparato». Se non si sa il tipo: **non indovinare**, registrare ⛔ e lasciare.
```
for id in ids(panel): if !has("/plugins/plugin-"+id): t = copy_type(id) ?: default_xml_type(id); if t && !lock_in_xfconfd(): set(...); log(...) else log(⛔)
```
Rischi: se l'utente ha tolto a mano un plugin lasciandolo negli id (mai: il pannello toglie anche l'id). Ripara anche gli utenti già danneggiati (una volta, alla prima nascita dopo l'aggiornamento).
Questa è la cura che fa da rete per **qualunque** causa futura (anche H3/H4/H5).

### C4 (architettura, non ora) — niente blocco nella memoria dello xfconfd condiviso
Radice di tutta la famiglia: i blocchi vivono nel demone condiviso con il desktop locale (`:6313-6334` lo dichiarano). Un xfconfd privato per la sessione remota non è possibile (nome D-Bus fisso per bus utente) [S]; resta solo ridurre quello che si scrive (C1) e verificare (C2/C3).

**Ordine consigliato**: C1 (piccolo, toglie la causa) + C3 (rete e riparazione dei danneggiati); C2 dopo, perché tocca il ripristino di tutte le chiavi.

Nota di coerenza con le altre decisioni: nel codice attuale `local_session()` (D-153) è svuotata (`U:src/session.c:2270-2290`): su Xubuntu `default_plugins("whiskermenu")` legge oggi `/etc/xdg/xfce4/panel/default.xml` (applicationsmenu, niente whisker) e non quello di Xubuntu. Quando D-153 sarà ripristinato (piano passo 3c) il whisker tornerà nel blocco e **il difetto D-X3 si presenterà anche su Xubuntu**: cure C1/C3 vanno fatte **prima o insieme**. Lo stesso difetto è già presente su Debian 13 (`actions`) nel codice 1.0.0 attuale (file identici). [V]

---------------------------------------------------------------------------------------------------

## 7. Raccordo con altri fatti letti

- Le voci di spegnimento su Xubuntu sono protette **solo** dal blocco del whisker (studio 7 §6.1): perdere `plugin-1` significa perdere l'intera protezione, non solo il menu. [V: `studio/7-xubuntu-lubuntu.md`; `xds/…/default.xml` senza `actions`]
- La chiusura leggera è raggiungibile in 1.0.0 ma più stretta (gancio PAM, studio 7 §6.1). Il difetto però non richiede la chiusura leggera in sé: richiede un ripristino **con blocco in memoria** (C2.1). Altri casi in cui accade [S, da verificare]: `try-restart` che fallisce, drop-in tolto da un'istanza e ripristino da un'altra, retry di `session_clear_out_handler_due()` dopo una rimozione parziale.
- `xfconf_unset()` ha già una nota sulla rilettura «gone» (`:4991-4996`) ma non sul rischio di cascata al padre: da aggiungere al commento.

---------------------------------------------------------------------------------------------------

## 8. Prove (da eseguire dal proprietario; io NON le ho eseguite)

### P1 — xfconf puro, senza REMOTIX (2 minuti, qualunque Ubuntu 26.04 con `xfconf` e `dbus-x11`; distingue H1 da tutto il resto)
```
T=$(mktemp -d); mkdir -p $T/lock/xfce4/xfconf/xfce-perchannel-xml $T/home
cat > $T/lock/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="whiskermenu">
      <property name="show-command-shutdown" type="bool" value="false" locked="prova"/>
    </property>
  </property>
</channel>
EOF
export XDG_CONFIG_HOME=$T/home XDG_CONFIG_DIRS=$T/lock:/etc/xdg   # e fare lo stesso come utente di nome "prova" o cambiare locked=
dbus-run-session -- bash -c '
 /usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd & sleep 1
 xfconf-query -c xfce4-panel -p /plugins/plugin-1                       # atteso: whiskermenu (ereditato)
 xfconf-query -c xfce4-panel -n -t string -p /plugins/plugin-1 -s whiskermenu   # il "set" della migrazione/ripristino
 sleep 7; cat $XDG_CONFIG_HOME/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml  # atteso (H1): plugin-1 type="empty" e il figlio vuoto; NIENTE value="whiskermenu"
 pkill -TERM xfconfd; sleep 1
 export XDG_CONFIG_DIRS=/etc/xdg; /usr/lib/x86_64-linux-gnu/xfce4/xfconf/xfconfd & sleep 1   # xfconfd "senza blocco"
 xfconf-query -c xfce4-panel -p /plugins/plugin-1                       # atteso (H1b): errore "does not exist"
 xfconf-query -c xfce4-panel -n -t string -p /plugins/plugin-1/show-command-shutdown -s x ; xfconf-query -c xfce4-panel -p /plugins/plugin-1/show-command-shutdown -r
 sleep 7; cat $XDG_CONFIG_HOME/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml  # atteso (H1a): anche il nodo plugin-1 è sparito dal file (cascata)
'
```
(Variante di controllo C1: stesso test con `type="empty"` al posto di `type="string" value="whiskermenu"` sul padre: atteso `plugin-1 type="string" value="whiskermenu"` nel file utente dopo il `set`, e nessuna perdita in nessuno dei passi.) Il percorso dell'eseguibile può essere `/usr/libexec/xfce4/xfconf/xfconfd`: cercarlo con `dpkg -L xfconf | grep xfconfd`.

### P2 — Sulla macchina Xubuntu con REMOTIX (osservare, non cambiare): utente nuovo `prova` mai entrato in XFCE
```
F=~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml
# 1) sessione remota APERTA, aspettare 15 s:
grep -n -A8 'name="plugin-1"' $F          # H1: type="empty" + 6 figli vuoti.  Alternativa: type="string" value="whiskermenu" => H1 sbagliata
grep -n -B1 -A4 '/plugins/plugin-1$' ~/.local/state/remotix/xfce-chiavi    # kind=plugin absent=true
xfconf-query -c xfce4-panel -p /plugins/plugin-1                           # whiskermenu (effettivo)
cat /proc/$(systemctl --user show -p MainPID --value xfconfd.service)/environ | tr '\0' '\n' | grep XDG_CONFIG_DIRS   # contiene .../remotix/xdg-xfce
# 2) Log Out normale; subito dopo e dopo 10 s:
grep -n -A8 'name="plugin-1"' $F          # atteso: type="string" value="whiskermenu" (percorso sano), figli assenti
```
### P3 — La chiusura leggera, passo per passo (stessa macchina, 3 minuti)
```
# sessione remota aperta, poi accesso locale (lightdm) con lo stesso utente  -> chiusura leggera
journalctl --user -u remotix* | grep -n "light mode"                         # "XFCE keys are NOT restored"
grep -n -A8 'name="plugin-1"' $F                                           # atteso: ancora type="empty" (non ancora perso)
xfconf-query -c xfce4-panel -p /plugins/plugin-1                           # atteso: whiskermenu (dalla MEMORIA con blocco)
cat /proc/$(systemctl --user show -p MainPID --value xfconfd.service)/environ | tr '\0' '\n' | grep XDG_CONFIG_DIRS   # blocco ANCORA in memoria (drop-in già tolto)
# H1b: fermare il locale e   systemctl --user restart xfconfd
xfconf-query -c xfce4-panel -p /plugins/plugin-1                           # atteso: "does not exist"  => perso senza ripristino REMOTIX
# H1a (rifare da capo la chiusura leggera, SENZA riavviare xfconfd), poi nuova sessione remota:
journalctl --user | grep -n "NOT put back\|no .actions. nor"                # 'show-command-* NOT put back' poi nessun plugin da bloccare
grep -c 'name="plugin-1"' $F; grep -n 'plugin-ids' -A12 $F                  # 0 occorrenze di plugin-1 ma plugin-ids contiene ancora 1
```
Esito che **smentisce** H1: dopo la chiusura leggera `plugin-1` è `type="string"` nel file utente (il tipo era già memorizzato) e viene perso comunque ⇒ passare a H2/H5; oppure il file non è mai `empty` e il plugin sparisce dopo un clic su «Remove» (finestra visibile a schermo).
Per distinguere H1a da H1b basta il confronto P3 con e senza `systemctl --user restart xfconfd` prima della nuova nascita.

---------------------------------------------------------------------------------------------------

## 9. Problemi da affrontare

| # | Che cosa | Dove nel codice | Peso | Cura già nota nel vecchio albero? |
|---|---|---|---|---|
| 1 | Nel blocco del pannello il plugin ha tipo di sistema ⇒ valore utente mai scritto (causa di D-X3) | `U:src/session.c:6468-6471`, `:6489-6491` | piccolo | **no** (vecchio albero: solo ipotesi `xfce_system_value`, `O:assessment/RAPPORTO.md:70-75`) |
| 2 | Ripristino con blocco ancora in memoria di xfconfd: `xfconf_set` «ok» per una rilettura effettiva e gruppo uscito dalla copia | `:5377-5398`, `:5439-5440`, `:4020-4021`, `:4026-4031`, `:5459-5467` | medio | no |
| 3 | `xfconf_unset` dell'ultimo figlio cancella il padre senza valore (cascata) | `:4975-5002`, `:5399-5400` | piccolo-medio | no |
| 4 | Manca un controllo «ogni id di `plugin-ids` ha il tipo» e la riparazione di chi ha già perso il plugin | nuova funzione, chiamare da `:5421` e `:6552` | medio | no |
| 5 | Tutta la protezione delle voci di spegnimento su Xubuntu passa dal whisker: finché D-X3 c'è, nessun blocco dopo la perdita | `:6441-6448`, `:6633-6635` | (conseguenza di 1-4) | no |
| 6 | Finestra «Plugin could not be loaded, remove?» in sessione remota/locale (ferma il caricamento dei plugin successivi; «Remove» è definitiva) | non nostro (`X:xfce4-panel/panel/panel-application.c:346-378, 470-486`) | piccolo (da evitare con 1-4) | no |
| 7 | D-153 svuotato: quando tornerà, il whisker di Xubuntu rientra nel blocco ⇒ D-X3 su Xubuntu certo; fare 1 e 4 prima/insieme (piano 3c) | `:2270-2290`, `:5118-5153` | collegamento | cura D-153 sì (`O:src/session.c:2274-2380`) |

## 10. Che cosa non si può sapere senza provare
1. Se l'ordine descritto (primo ripristino a `:7053`, secondo a `:6542`) è quello reale: serve il journal della nascita dopo una chiusura leggera (P3).
2. Se xfconfd 4.20.0 memorizza davvero il valore del padre quando il nodo di sistema è `type="empty"` con figli bloccati (previsto da `_set` `:289-356` e dal fatto che `plugins` già funziona così) — P1, variante di controllo.
3. Se in qualche macchina il whisker scrive un figlio non bloccato sotto `plugin-1` (es. `favorites` da `defaults.rc` di Xubuntu, `settings.cpp:287-289`), che fermerebbe la cascata e lascerebbe il padre vuoto (perdita via H1b, non H1a).
4. Quanto spesso, fuori dalla chiusura leggera, un ripristino capita con il blocco in memoria (casi in §7).
5. Il comportamento della finestra «could not be loaded» in sessione remota senza nessuno che la veda (probabile: il pannello resta fermo sul primo id, il resto del pannello non appare) [S].

## 11. Appendice: comandi e file letti
- `podman run -d --name studio-9 -v /media/REMOTIX-UBUNTU/studio/9:/w docker.io/library/ubuntu:26.04 sleep infinity`; `deb-src` abilitato; `apt-get source` (download) di `xfce4-panel 4.20.7-1`, `xfconf 4.20.0-1build1`, `xfce4-session 4.20.4-1`, `xfce4-whiskermenu-plugin 2.10.1-1`; `apt-get download xubuntu-default-settings xfce4-panel` ed estrazione con `dpkg-deb -x`/`-c`. Nessun comando di prova eseguito; nessun avvio di REMOTIX.
- File principali letti: `U:src/session.c` righe 3700-3740, 3800-3870, 3940-4135, 4480-4530, 4735-5002, 5004-5560, 6290-6726, 7035-7060; `U:src/child.c:9921-9980`; `studio/00-REGOLE-studio.md`, `studio/7-xubuntu-lubuntu.md`; `O:assessment/xfce/{difformita,ubuntu2604,debian13,fedora44,arch,tumbleweed,leap16}.md`, `O:assessment/{RAPPORTO,fase3-xfce-lxqt}.md`.
- Il contenitore `studio-9` viene fermato e tolto a fine studio; la cartella `/media/REMOTIX-UBUNTU/studio/9/` resta.
