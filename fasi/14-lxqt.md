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
