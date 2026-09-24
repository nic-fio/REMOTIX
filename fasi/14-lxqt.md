# Fase 14 — LXQt

*Aperta il **24 settembre 2026**. Chiusa il —*

⚠ Numerazione: `PIANO.md` metteva LXQt nella fase 13 («XFCE e LXQt») e chiamava 14 «Il registro».
L'utente, aprendola, l'ha chiamata **fase 14**: vale il suo nome, e il registro scala di uno.

## Che cosa deve produrre

Il quarto desktop: l'utente apre il browser e vede il suo desktop **LXQt**, come oggi GNOME, Plasma
e XFCE.

⛔ **La regola della fase, dell'utente, 24 settembre 2026**: *«aggiungere LXQt a REMOTIX mantenendo
intatte tutte le capacità già certificate di GNOME, KDE e XFCE»*. ⇒ **Il baseline protetto sono
tre.** Si lavora con i cancelli della fase 13 (CP0 baseline · CP1 definizione · CP2 osservazione ·
CP3 modifica minima · CP4 prova LXQt · client veri · rete completa · checkpoint), e con due accenti
nuovi: **sviluppo parallelo con molti agenti, integrazione e certificazione in mano sola**; e ogni
attività finisce in **PASS / FAIL / BLOCKED** (con causa, evidenza, dipendenza, condizione).

---

## ⭐ La differenza che cambia la forma della fase

LXQt, come XFCE, **non ha un compositore suo**: su Wayland si appoggia a **labwc** (wlroots).
⇒ Cattura (screencopy), input (virtual-keyboard/pointer), appunti (data-control) e misura
dell'uscita sono **già scritti** per XFCE e non guardano il desktop `[R]`. Quel che cambia è la
**sessione**: `lxqt-session` al posto di `xfce4-session`, e un gestore diverso per bus, uscita,
inattività e impostazioni.

`[R]` Due cose che la fase 13 non aveva:
- **in trixie nessun pacchetto fa partire LXQt su Wayland** (niente `lxqt-wayland-session`, niente
  `startlxqtwayland`): la riga d'avvio la scrive il prodotto, `labwc -C <cartella nostra> -S
  lxqt-session`, imitando lo script upstream 0.1.1 ma senza il suo `autostart` (che accende
  `swayidle … wlopm --off` a 5 minuti) e senza il suo wizard;
- **la scatola `rete11-lxqt` non conteneva il desktop**: solo `labwc lxqt-session xwayland`. Niente
  pannello, scrivania, `qt6-wayland`. ⇒ Prima di ogni prova, la ricetta.

---

## Gli incrementi

### Incremento 1 — LXQt si riconosce, nasce e si vede

| | |
|---|---|
| **obiettivo** | su una macchina con `lxqt-session` + `labwc` il prodotto riconosce LXQt, fa nascere labwc headless con `lxqt-session`, cattura, porta mouse e tastiera, sa chiudere |
| **invariante** | GNOME, KDE, XFCE **identici**: l'enum `SESSIONE_DESKTOP_LXQT = 4` va in coda; ogni ramo esistente resta con lo stesso effetto |
| **moduli** | `src/sessione.{c,h}` (riconoscimento, ambiente, avvio, viva/stato, esci, impostazioni), `src/figlio.c` (5 punti `== XFCE` → `sessione_su_wlroots()`); la ricetta `Contenitore.lxqt`; il gesto «Esci» di C20 |
| **prova LXQt** | C1(lxqt) verde; il desktop nudo fotografato e passato ai giudici **prima** di aprire la capacità `immagine`; la sonda dei processi e dell'ambiente |
| **prova client** | Firefox e Chrome veri sulla 8514 |
| **regressioni da guardare** | C1, C7 e tutto il certificato su gnome/kde/xfce |
| **criterio** | rete intera: nessun rosso nuovo su gnome/kde/xfce, C1(lxqt) verde, guasti ancora presi |

**CP3 — la modifica** (`1f99d60` prodotto; `cd7a088` `61bdc5a` `58262da` `2330e79` banchi):
- `riconosci_desktop`: marcatore `lxqt-session`, ramo dopo XFCE; con tutti e due, XFCE e
  «AMBIGUO» dichiarato;
- ambiente: `XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots` (la forma dello script upstream quando il
  compositore è configurato), `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share`, `QT_QPA_PLATFORM=wayland`,
  `QT_QPA_PLATFORMTHEME=lxqt`, `XDG_MENU_PREFIX=lxqt-`, più le variabili labwc di XFCE;
- `rc.xml` e `autostart` **nostri** in `$XDG_RUNTIME_DIR/remotix/labwc-lxqt/`;
- viva/stato: il nome `org.lxqt.session` sul bus; «Esci»: `logout()` senza risposta, poi SIGTERM
  a labwc;
- inattività: `enableIdlenessWatcher=false` **e** `runCheckLevel=1` (sotto 1 il demone la rimette a
  vero), riletti; niente comando di blocco (`/bin/false` aprirebbe una modale);
- la scatola: `lxqt-core qt6-wayland lxqt-menu-data lxqt-powermanagement nano`, `nictest`,
  `wlr-randr`; **esclusi** `lxqt-branding-debian` (lxqt-leave nel pannello), `qlipper` (sporca gli
  appunti), `swayidle swaylock wlopm kanshi`.

**Revisione avversaria** (agente mandato a smentire): GNOME/KDE/XFCE identici — **non smentito**.
Sul ramo LXQt:
- ereditati da XFCE, non nuovi: la guardia e la forza di chiusura guardano **ogni** `labwc`
  dell'utente, e il bus d'utente è uno per uid ⇒ lo stesso utente con una sessione locale aperta
  confonde il prodotto. `[?]` da decidere a parte: non è di LXQt;
- ⚠ **da misurare**: il nome sul bus nasce prima dei moduli ⇒ una `lxqt-session` che muore
  all'avvio sarebbe letta come «l'utente è uscito» (congedo 0x10);
- minore: `g_key_file_save_to_file` sostituisce un collegamento simbolico con un file vero.

Binario **`404f9907`** (md5), costruito dall'albero integrato `ae6c3ba`.

**CP4 — la prova LXQt**, 24 set 2026, su una **quinta scatola di sviluppo** `rete14-lxqt` (porta
8524, immagine `lxqt:p1`, cartella `/media/REMOTIX/rete14-lxqt`), decisa dall'utente per non
aspettare la baseline: *«parti subito con la quinta scatola. Ogni DE deve avere la sua scatola
dedicata»*. Le quattro scatole della rete restano intatte.
- `[M]` il prodotto dice «il desktop di questa macchina: LXQt (c'e' lxqt-session, e labwc per farlo
  girare)»; **C1(lxqt)×3 VERDE**, monitor `HEADLESS-1` 1920x1080;
- `[M]` lo scatto del desktop nudo: **disegnato** (4181 colori), sfondo LXQt e pannello; **nessuno** dei
  colori delle scene sopra lo 0,0 % ⇒ C2/C3/C8b non possono essere ingannati dallo sfondo;
- `[M]` la sonda: labwc → lxqt-session → pannello, scrivania, powermanagement, notifiche, policykit,
  runner; **Qt su wayland**, niente Xwayland, niente wizard né `lxqt-leave` aperti, niente
  swayidle/qlipper/locker; `enableIdlenessWatcher=false` e `runCheckLevel=1` **vincono** dal file
  dell'utente; labwc offre layer-shell, foreign-toplevel, screencopy, input virtuale, data-control;
- `[M]` **il giro di tutte le maglie di scatola su LXQt**, con le capacità aperte **solo nella copia di
  sviluppo**: passo0, C7 (+ distacco), C5, C8, C9, C18, C2, C3 (+ scena ferma), C4, C6, C8b, C17,
  C20, C19 **tutte verdi**, e **16 guasti innestati su 16 VISTI**. C20: il gesto è il `logout()` di
  `org.lxqt.session`, «il figlio è sopravvissuto e se n'è accorto», rientro pulito.
  ⚠ Un primo C19 rosso era **classe C, del mio giro**: non sgomberava gli inquilini fra le maglie come
  fa il gancio; sgomberato, C19 verde e i suoi due guasti visti.

**Il difetto trovato guardando**: il pannello **senza icone** e senza pulsante del menu ⇒ incremento 2.

### Incremento 2 — le icone, e niente voci pericolose

| | |
|---|---|
| **obiettivo** | il pannello LXQt ha icone e menu; il menu non offre blocco, sospensione, ibernazione, riavvio, spegnimento; «Esci» resta |
| **invariante** | GNOME/KDE/XFCE identici: solo `impostazioni_lxqt()` e uno strato nuovo **in coda** alla ricetta |
| **causa** `[R]` | `icon_theme=breeze` in `/usr/share/lxqt/lxqt.conf`, ma il tema lo porta `lxqt-system-theme` solo come *Recommends*; il pulsante del menu vuole `qt6-svg-plugins`. ⚠ È la **scatola**: una macchina con `apt` normale li prende |
| **modifica** | R5 `kf6-breeze-icon-theme qt6-svg-plugins` (`afc0cb0`); sei `.desktop` `Hidden=true` per l'utente, **riletti** (`a1f771e`, DECISIONI §4.7) |
| **misura** `[M]` | lo scatto mostra menu, notifiche, volume, «mostra scrivania»; registro «⭐ LXQt: 6/6 voci nascoste, RILETTE; resta "Esci"» |

⚠ Residui dichiarati, come la finestra «Log Out» di XFCE: il pulsante «Leave» dentro il menu è
fisso nel codice di fancymenu e apre `lxqt-leave`, dove spegnimento/riavvio/sospensione sono **grigi**
(polkit/logind) e «Lock screen» è **cliccabile ma inerte** (nessun comando di blocco). «n/a» a sinistra
è il cambia-desktop, che su wlroots non ha motore: innocuo.

**Client veri** — binario **`1a10a66e`** (albero `a1f771e`), labwc senza schermo sul server:
**Firefox 140 PASS · Chrome 154 PASS** (`12-client-veri`: pagina, ammissione, primo fotogramma,
continuità 63–66 fotogrammi in 8 s, tastiera e mouse al server, 0 errori JS e di rete, rientro).
⛔ **E la fotografia della tela mostra un difetto che i contatori non vedono**: con la tela del
browser (1400x914) il pannello va giusto in fondo, ma **lo sfondo di pcmanfm-qt resta della misura
di nascita** e il resto è nero. Col cliente Python (1920x1080) riempiva tutto. In diagnosi.

---

### Incremento 3 — lo sfondo nasce della misura del cliente

`[M]` La causa, con il cliente Python e senza browser: **una gara alla nascita**. labwc nasce con
l'uscita 1280x720 e il prodotto la ridimensiona ~200 ms dopo; pcmanfm-qt parte ~160 ms dopo labwc.
`[R]` pcmanfm-qt 2.1.0 calcola lo sfondo da `screen->size()` e lo ricalcola solo su `resizeEvent`: se
Qt aggiorna lo schermo dopo la finestra, lo sfondo resta 1280x720 per sempre.
**Cura** (`e4ecfbb`, solo ramo LXQt): il client primario di labwc diventa `sh -c` che dà all'uscita la
misura del cliente con `wlr-randr` **prima** di `exec lxqt-session` (`;` e non `&&`: se fallisce,
resta la richiesta tardiva di prima). `wlr-randr` passa da attrezzo diagnostico a dipendenza del
prodotto su LXQt. `[M]` 1400x914: **prima 1 difetto su 20, dopo 0 su 20**; e 0 su 5 a 1920x1080, 0 su
5 a 3840x2160.

### La cura di Firefox (decisione dell'utente: «curarlo subito»)

`ec9c561`: la **larghezza** della tela chiesta si tronca a multiplo di 16 (l'altezza resta pari),
per tutti i browser, senza rami. `[M]` Firefox: striscia da 8 e 12 px → **0**, margine dell'ultima
icona uguale a Chrome (7 px); Chrome invariato. Il prezzo: bande nere di al più 7-8 px ai lati.

### CP0 — la baseline, chiusa

`[M]` 24 set 2026, 07:36 → 12:00, binario `e681a262` (quello di prima della fase), `--famiglia tutto`
sulle quattro scatole: **un solo rosso, `C1(lxqt)×10`**, quello atteso (il binario vecchio non
riconosce LXQt); **117 guasti innestati visti su 117**; C14 regge; C10 C12 C15 C16 «il terreno non
regge» dal server, come sempre. ⇒ nessuna differenza inattesa rispetto al checkpoint del 24 notte.

### Client veri col binario finale **`c0e8f010`** e pagina **`d77177f1`**

`[M]` sulla scatola di sviluppo, **Firefox 140 e Chrome 154 PASS** a finestra 1400x914 (tela
1392x828) **e in 4K** (tela 3840x2014): a–g tutti verdi. La foto 4K di Firefox: sfondo pieno, 0 %
nero, l'ultima colonna è sfondo (1,81,129) e non la striscia.

### ✅ LA RETE INTERA SULLE QUATTRO SCATOLE — nessun rosso

`[M]` 24 set 2026, 12:00 → 17:18, binario **`c0e8f010`** e pagina **`d77177f1`** in tutte e quattro,
`rete11-lxqt` **rifatta** dalla ricetta nuova, `--famiglia tutto`: **«nessun rosso»**.
**34 verdi su gnome, 34 su kde, 34 su xfce, 34 su lxqt** — LXQt fa esattamente le stesse maglie
degli altri tre; **nessun guasto innestato sfuggito**; C14 (le quattro insieme) regge; C10 C12 C15
C16 «il terreno non regge» dal server, come sempre. ⇒ GNOME, KDE e XFCE **non hanno perso niente**,
né per LXQt né per la cura di Firefox che tocca tutti.

### ✅ I browser veri sulle quattro scatole ufficiali

`[M]` 24 set 2026, sera, binario `c0e8f010`, pagina `d77177f1`, labwc senza schermo sul server,
finestra 1400x914 (tela 1392x828):

| | `12-client-veri` Firefox 140 | `12-client-veri` Chrome 154 | `12-c20-veri` Firefox | `12-c20-veri` Chrome |
|---|---|---|---|---|
| **gnome** | PASS | PASS | VERDE | VERDE |
| **kde** | PASS | PASS | VERDE | VERDE |
| **xfce** | PASS | PASS | VERDE | VERDE |
| **lxqt** | PASS | PASS | VERDE | VERDE |

⚠ Su gnome il primo giro ha dato **BLOCKED** alla voce *e* (input): senza `--registro-cmd` il banco
cerca l'id dell'input nei fotogrammi, e Mutter a scena «muovi» ne manda solo 7-8 in 8 s ⇒ **classe C**,
del banco. Rifatto con `--registro-cmd`: **PASS** su tutti e due, 7-8 righe d'input nel registro.
Android: resta all'utente, col suo telefono (l'emulatore non fa partire Chrome, 19 set).

### ✅ Sessioni coi browser veri su LXQt (al massimo 10 minuti — l'utente, 24 set) e la guardia

`[M]` `14-il-cliente-che-non-sta-fermo --desktop lxqt`, mouse in moto nel 100 % dei secondi:
**Firefox 10 min: blocco più lungo 0 s, 0 buchi · Chrome 10 min: blocco più lungo 0 s, 0 buchi.**
Guardia del battito col guasto `--schermo-congelato` (SIGSTOP a labwc trovato per socket): **esito 1,
«lo schermo si è fermato per 23,9 s mentre il mouse si muoveva» — il guasto è stato VISTO.**

## ⭐ CHECKPOINT — 24 settembre 2026, sera

| | |
|---|---|
| **binario** | `c0e8f010` (md5), albero `a8bedb6` + banchi; pagina `d77177f1` |
| **LXQt** | riconosciuto, nasce, si vede, input, appunti, «Esci», sfondo della misura del cliente, icone, voci pericolose nascoste; **34/34** nella rete, capacità `immagine input appunti` aperte |
| **GNOME · KDE · XFCE** | **34/34 ciascuno**, invariati |
| **client** | Firefox 140 e Chrome 154 PASS e C20 VERDE sulle quattro; sessioni LXQt 10 min verdi; Android: all'utente |
| **rete** | «nessun rosso», nessun guasto sfuggito, C14 regge; guardia del battito vede il guasto su LXQt |
| **fuori da LXQt, curato** | la striscia verde di Firefox (tutti i desktop), decisione dell'utente |

## ⛔ Un difetto trovato per strada, che NON è di LXQt — Firefox e il riempimento del codificatore

`[M]` 24 set 2026, da 380 fotografie di tela (`c20veri` del 23 set, `topo`, `veri-lxqt`): **Firefox 140
mostra a destra una striscia verde (0,76,0) larga quanto manca a un multiplo di 16** (8 px a 1400,
4 px a 3788, 12 px a 1348), e **schiaccia in orizzontale** l'immagine (1408 → 1400: l'orologio del
pannello LXQt sta 6 px più a sinistra che in Chrome). In altezza il ritaglio lo onora. (0,76,0) è
esattamente YUV (0,0,0) letto BT.709 limitato ⇒ è il riempimento del codificatore che arriva allo
schermo. **Chrome 154: nessuna striscia**, su nessun desktop. `[R]` il server dichiara il ritaglio
nell'SPS (`frame_cropping_flag`); la pagina disegna con `createImageBitmap(f)` su `bitmaprenderer`
(`pagina.html:3188`), che per specifica deve rispettare il rettangolo visibile: Chrome lo fa, Firefox
a destra no.
- ⇒ **su GNOME, KDE, XFCE e LXQt**, ogni volta che la tela non è larga un multiplo di 16; c'era già il
  23 settembre ⇒ **non è una regressione della fase 14**, e non si cura dentro la fase 14 senza una
  decisione: la cura minima (larghezza della tela troncata a multiplo di 16 in `tela_da_chiedere()`)
  cambia la tela **per tutti** i browser, al prezzo di fino a 15 px di bordo.
- ⚠ i contatori di `12-client-veri` erano verdi: lo si è visto solo **guardando** la fotografia.

## Che cosa resta [?]

- **Android** (Chrome sul telefono dell'utente) su LXQt e sui tre con la pagina nuova: dell'utente.
- **la prova a mano dell'utente** su `rete11-lxqt` (8514), utente `nictest`/`nictest` — come per le
  altre tre scatole.
- `[?]` il pulsante «Leave» di fancymenu: «Lock screen» cliccabile e inerte (dichiarato, come la
  finestra «Log Out» di XFCE).
- `[?]` ereditati da XFCE, da decidere a parte: la guardia e la forza di chiusura guardano ogni
  `labwc` dell'utente; lo stesso utente con una sessione locale aperta confonde il prodotto.
- `[?]` xfdesktop ha la stessa gara alla nascita di pcmanfm-qt? Su XFCE lo sfondo nella scatola è
  nero, quindi non si vedrebbe: non misurato.
- la scatola di sviluppo `rete14-lxqt` (8524, `/media/REMOTIX/rete14-lxqt`) resta accesa per le
  prossime prove; non entra nella rete.
