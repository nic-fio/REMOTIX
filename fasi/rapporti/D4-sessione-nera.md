# D4 — La sessione GNOME che tornava nera al primo riavvio

*Cura del difetto **D4** di `fasi/rapporti/DIFETTI-12-agosto.md`, scritta il 12 agosto 2026.
Difetto scoperto da `fasi/rapporti/F2-1-sessione.md`. Porta assegnata: **7524** (non è servita: la
guardia non ascolta, e il ciclo della sessione usa il lucchetto **7511** che era già lì).*

> ⛔ **Questo giro non ha scritto prodotto.** `src/` e `v1/remotix-c/` non sono stati toccati: il
> rilievo su `sessione.c:671` si **scrive** (§4), non si cura.

---

## 1. Che cosa era rotto, in una riga

`v1/banco/provision-server.sh` §4 scriveva `--headless --no-x11` e **basta**. In headless Mutter
mette `needs_outputs = false` (`STUDI.md` §gnome §3.1) ⇒ la sessione nasce **viva, completa e nera**. La
cura di F2.1 viveva in `$XDG_RUNTIME_DIR`, che il riavvio si porta via insieme a tutto il rootfs.
⇒ **la prima sessione nata dopo un riavvio sarebbe stata nera un'altra volta.**

---

## 2. ⭐ Che cosa ho reso persistente — e **come l'ho provato**

### La cura

| dove | che cosa |
|---|---|
| `v1/banco/provision-server.sh` §4 (`sezione_monitor()`) | scrive `--virtual-monitor 1920x1080` nel drop-in **persistente** `/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf`, **sempre** e non «solo se manca» |
| la stessa | ⛔ **verifica che sia IN VIGORE**, non che sia scritto: rilegge `ExecStart` dal gestore d'utente, e se un altro drop-in vince **elenca i drop-in e si ferma** (E1) |
| la stessa | ⛔ **guarda anche la Shell VIVA**: un drop-in vale dalla prossima nascita, e una sessione già in piedi resta nera. Tre uscite dichiarate: **0** in vigore e la Shell viva ce l'ha · **1** scritto e non in vigore · **2** in vigore ma la sessione che gira è ancora quella vecchia |
| la stessa | nuovo modo `provision-server.sh monitor`: fa **solo** la §4. Una cura che per essere riprovata chiede di rifare apt, polkit e il servizio non viene riprovata |
| il fondo dello script | se la §4 non è 0, **non esce «Fatto»**: esce col numero della §4 |
| `banchi/02-sessione-lancia.sh` | nuovo modo drop-in **`nudo`** e nuovo verbo **`come-al-riavvio`**: fa rinascere la sessione **senza nessun drop-in di banco**, cioè com'è dopo un riavvio |
| la stessa | `dilo_se_non_persiste()`: dopo ogni `sano` e ogni `guarda`, se il monitor lo tiene in piedi **solo** il drop-in di banco, lo dice **forte** — *«SANA ADESSO, NERA AL PROSSIMO RIAVVIO»* |

### La prova — `[M]` 12 agosto 2026, NIC-OS host, tutte con i numeri scritti prima

| # | scena | atteso | **misurato** |
|---|---|---|---|
| 1 | `come-al-riavvio` con la configurazione **vecchia** (nessun drop-in di banco) | **1** | **`1 NERA: ZERO MONITOR`** — gnome-shell 222547, riga `--headless --no-x11`, **0 monitor** |
| 2 | `provision-server.sh monitor` — la cura, con la sessione nera ancora viva | **2** | **2**, con `ExecStart` in vigore corretto **e** *«IL DROP-IN È A POSTO, MA LA SESSIONE CHE STA GIRANDO È NERA»* |
| 3 | `come-al-riavvio` con la configurazione **curata** | **0** | **`0 SANA`** — gnome-shell 223183, `--virtual-monitor 1920x1080`, monitor `Meta-0` / `MetaVirtualMonitor` / `1920x1080@60.000` |
| 4 | `certifica` — il banco di F2.1 **dopo** la cura | 0 → 1 → 0 | **0 → 1 → 0**, e il guasto nel suo punto (`NERA: ZERO MONITOR`) |
| 5 | `02-sessione-certifica-scene.py` sulle scene rigenerate | 9 su 9 | **9 su 9** |

⭐ **La riga 1 è la parte che conta**, ed è il rovescio di `CODER.md` §3.4: il difetto è stato
**fatto comparire di proposito** prima di curarlo, sulla stessa macchina e con lo stesso comando che
poi ha dato 0. Sano → guasto → risanato non sulla lettura, ma **sulla persistenza**.

⚠ **Perché la 4 andava rifatta**: mettere `--virtual-monitor` nel drop-in di `/etc` poteva rendere
**irraggiungibile il guasto M9** — se quel file avesse vinto sul `zz-f21-monitor.conf` del banco, il
guasto non si sarebbe più potuto innestare e F2.1 sarebbe rimasto **non certificabile**. Non è
successo (i drop-in si applicano in ordine di nome, `zz-` viene dopo `remotix-`), **ma è stato
misurato, non dedotto**.

### ⛔ Che cosa **non** ho provato, e la prova che manca

**Non ho riavviato il server, e la cura è quindi `[?]` sull'ultimo tratto.** Non l'ho fatto perché:

- ⛔ il rootfs vive in RAM: un riavvio **cancella tutto** — il drop-in di `/etc`, la home, la regola
  `sudoers` dei banchi — e la macchina torna a posto solo se qualcuno rilancia
  `provision-server.sh` a mano, di persona;
- ⛔ **la 7448 e la 7501 si spengono con la macchina**, ed è precisamente quel che il mandato
  vieta. Il vincolo dice che *un riavvio della sessione grafica* non le tocca — e infatti non le ha
  toccate — ma un riavvio del **server** sì;
- ⏳ e c'è `banchi/01-s1b-eccezione.sh oggi`, che ha una scadenza e un certificato in `/media`.

⇒ **La cura è dichiarata PROVATA sull'ultimo anello** (*data la configurazione persistente, una
sessione appena nata ha il monitor*) **e NON PROVATA sul riavvio vero**. La prova che manca, e come
si fa — è `LEZIONI.md` §2.5-bis alla lettera:

```
1. si avverte chi tiene 7448 e 7501, e li si lascia cadere di proposito
2. sudo reboot                          (o l'interruttore, essendo il polkit che lo vieta da remoto)
3. bash /media/REMOTIX/provision-server.sh          ← e si guarda che la §4 esca 0
4. bash /media/REMOTIX/f21/02-sessione-lancia.sh sano
5. bash /media/REMOTIX/f21/02-sessione-guardia.sh   ← atteso 0 SANA
   ⛔ e il passo che vale più di tutti: 3 e 4 devono bastare, senza nessun altro comando.
      Se serve altro, quel «altro» è il pezzo che il provisioning non dichiara — che è
      esattamente il difetto trovato l'8 agosto con `pulseaudio-utils` e `wl-clipboard`.
```

⚠ **Meglio una cura dichiarata non provata che una dichiarata provata e non esserlo**: il primo
riavvio vero è l'unica cosa che chiude questa `[?]`.

---

## 3. ⭐ Che cosa gira adesso **prima** di ogni misura che dipende dalla sessione

`banchi/02-sessione-guardia.sh` — **la guardia**. Nasce dal fatto che il difetto è rimasto invisibile
due giorni perché

> ⛔ *«la sessione è viva»* e *«la sessione ha un monitor»* sono **due domande diverse**, e se ne
> faceva **una sola** — quella che rispondeva di sì.

Si mette **davanti** al comando altrui, e il comando non parte se la seconda domanda risponde male:

```
bash 02-sessione-guardia.sh --etichetta cattura-30s -- python3 02-cattura-misura.py …
```

| | |
|---|---|
| **le due domande, separate e stampate una per riga** | `1. la sessione è VIVA? → sì, gnome-shell 226107 e IsSessionRunning=true` · `2. la sessione ha un MONITOR? → NO — ZERO monitor` |
| ⛔ **e quando la prima è sì e la seconda no**, lo dice a lettere sue | *«VIVA E NERA — è la forma esatta del difetto vissuto due giorni su questa macchina»* |
| ⛔ **tre bande di uscita, perché un rifiuto e un fallimento del comando non possono avere lo stesso numero** | senza comando: **0-7**, il verdetto · rifiuto: **70+verdetto** (71 nera, 74 morta, 75 non ho potuto leggere) · altrimenti **l'uscita del comando, tale e quale** |
| ⭐ **e riguarda anche DOPO** | una sessione nera cade da sola al primo screenshot: se la scena è caduta **sotto** la misura, l'uscita è **79** e vale più del numero del comando, anche se il comando dice 0 |
| **una riga JSONL per giro** | in `02-sessione-esiti.jsonl`, `banco: F2.1-guardia`, col comando sorvegliato e i due verdetti — così il numero di chi misura ha **una scena accanto** |
| ⚠ **niente `--misura-lo-stesso`** | una guardia che si può saltare si salta, e il giorno in cui la si salta è quello in cui serviva. Chi deve misurare su una sessione guasta usa `02-sessione-lancia.sh guasto`, che la scena guasta la **dichiara** |

### La guardia si certifica, nello stesso giro — `[M]` 12 ago 2026

| scena | atteso, scritto prima | misurato |
|---|---|---|
| sessione **sana**, comando che esce 0 | esegue, uscita **0** | **0**, e il comando è partito |
| sessione **sana**, comando che esce 7 | esegue, uscita **7** *(e 7 non è «SHELL NON VUOTA»: le bande sono separate)* | **7** |
| sessione **guasta** (M9 innestato) | **71**, e il comando **non parte** | **71**, e `grep -x` sulla riga del comando: **assente** |
| ⭐ sessione **sana prima**, e il comando la fa diventare **nera sotto la misura** | **79**, e il numero del comando non vale | **79** — *«LA SESSIONE ERA SANA PRIMA (0) E ADESSO È 1»* |
| **risanata** | esegue, uscita **0** | **0**, comando partito |

⭐ **La riga del 79 è stata fatta succedere davvero**, non descritta: il comando sorvegliato era
`02-sessione-lancia.sh guasto`, che innesta M9 mentre la guardia sta guardando. È il caso che F2.1 ha
pagato dal vivo — la sessione caduta a metà di una misura — e adesso ha un numero suo.

---

## 4. ⛔ Il rilievo per il prodotto — non è mio da curare

*Nella forma di `REVIEWER.md` §4. Va a chi scriverà il prodotto della fase 2.*

```
DOVE:             v1/remotix-c/src/sessione.c:671, dentro sessione_assicura()
                      if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(larghezza, altezza, sbaglio))

COSA CONTRADDICE: · l'invariante I7 (CODER.md §2): «la protezione di un difetto noto sta nel
                    programma, non in una riga di configurazione che si puo' perdere».  Il difetto
                    noto e' la sessione viva-e-nera (STUDI.md §gnome §3.1, M9 di §13); la protezione oggi
                    sta in provision-server.sh §4, cioe' in una riga di configurazione su un rootfs
                    che vive in RAM;
                  · e se stesso: sessione_assicura() RICEVE `larghezza` e `altezza` (righe 650-651)
                    e sul ramo GNOME non le legge nessuno.  La misura del desktop entra nella
                    funzione e si perde in silenzio — E3, «una funzione fa meno di quel che il suo
                    nome promette»: si chiama «assicura» e per GNOME non assicura la cosa senza cui
                    non c'e' niente da catturare.

COME SI DIMOSTRA: non serve un'ipotesi, e' stato fatto sul ferro il 12 agosto 2026.
                  1. `bash banchi/02-sessione-lancia.sh come-al-riavvio` con la configurazione
                     persistente PRIVA di --virtual-monitor  → uscita 1 NERA: ZERO MONITOR,
                     gnome-shell 222547, riga `--headless --no-x11`, GetCurrentState: 0 monitor;
                  2. la stessa identica cosa con la configurazione persistente che CONTIENE
                     --virtual-monitor 1920x1080             → uscita 0 SANA, Meta-0 /
                     MetaVirtualMonitor / 1920x1080@60.000.
                  ⇒ fra le due misure cambia UNA riga di configurazione, e cambia se l'utente vede
                    il suo desktop o una scheda nera.  Finche' quella riga e' fuori dal programma,
                    chiunque la perda riporta il difetto senza saperlo — ed e' successo: dal 9
                    agosto 10:19 (data del file) al 12 agosto.

LA CURA, QUANDO TOCCHERA' A CHI SCRIVE IL PRODOTTO:
                  togliere `tipo == COMPOSITORE_KWIN` e scrivere il drop-in anche per GNOME con
                  `larghezza`/`altezza` — che scrivi_dropin() gia' prende e sessione_assicura() gia'
                  riceve.  ⚠ Cambia il nome dell'unita' (org.gnome.Shell@wayland.service, non
                  plasma-kwin_wayland.service) e la riga (`--headless --no-x11 --virtual-monitor
                  LxA`), e va verificato IN VIGORE dopo il daemon-reload: scritto non e' in vigore.

MARCA:            [R] la contraddizione con I7 e con le righe 650-651 e' letta nel codice
                  [M] i due numeri che la dimostrano sono misurati, 12 agosto 2026
```

---

## 5. ⚠ La trappola misurata, che riguarda chiunque scriva un controllo

⛔ **`org.gnome.Shell.Screenshot` non è un modo di controllare se c'è un monitor.** Su una sessione a
zero monitor Mutter tenta una texture 0×0:

```
CRITICAL : cogl_texture_2d_new_with_size: assertion 'width >= 1' failed
WARNING  : Failed to take screenshot: Failed to create 0x0 texture
```

gnome-shell muore, e con `OnFailure=gnome-session-shutdown.target` e `Restart=no` **se ne va tutta la
sessione** `[M]` F2.1, 12 ago 2026. ⇒ Il controllo **distrugge la cosa che sta controllando**, e lo
fa **solo nel caso guasto**: verde quando è sana, macerie quando è nera. Sta scritto in testa alla
guardia e in testa alla §4 di `provision-server.sh`, perché il posto dove serve è quello dove
qualcuno sarebbe tentato di scriverlo. ⭐ Si chiede `GetCurrentState`, che risponde e non fa male a
nessuno.

---

## 6. ⛔ Quel che questo giro NON ha toccato, e come me ne sono accertato

| | prima | dopo |
|---|---|---|
| ascoltatori sulla **7448** | **2** (tcp + udp) | **2** |
| ascoltatori sulla **7501** | **2** (tcp + udp) | **2** |

Contati con `ss -tuln` all'apertura (13:14 UTC) e alla chiusura del giro, **e** da
`vicini_prima`/`vicini_dopo` dentro ogni ciclo del banco: **sette** nascite e morti della sessione
grafica oggi, e i due server non se ne sono accorti — girano dentro il contenitore e non dipendono
dalla sessione. ⭐ Resta vero quel che F2.1 aveva già guardato invece di supporre.

⛔ **Non ho riavviato la macchina** (§2), non ho toccato `src/` né `v1/remotix-c/`, non ho eseguito
nessun `git` che scrive, e non ho fatto girare `provision-server.sh` per intero: solo il modo
`monitor`. ⇒ Le sezioni 1-3 e 5-7 dello script sono **invariate e non rieseguite** — dichiarato, non
misurato.

**La macchina resta sana, e sana per la ragione giusta**: `02-sessione-guardia.sh` → `0 SANA`, e
l'unico drop-in che chiede il monitor è ora **quello persistente**; il `zz-f21-monitor.conf` di banco
è stato tolto con `pulisci`. La copia precedente dello script è in
`/media/REMOTIX/provision-server.sh.pre-monitor`.

---

## 7. Le righe per il catalogo delle certificazioni

*Nella forma di `banchi/01-b12-guasti.py`.*

```python
{
    "nome":            "D4-monitor-persistente",
    "comando":         "bash banchi/02-sessione-lancia.sh come-al-riavvio",
    "dove":            "NIC-OS host — e serve il lucchetto 7511",
    "atteso_sano":     0,      # SANA: il monitor lo da' la configurazione PERSISTENTE
    "guasto":          "provisioning-senza-opzione",
    "guasto_dettaglio": "si riscrive /etc/systemd/user/org.gnome.Shell@wayland.service.d/"
                        "remotix-headless.conf togliendo `--virtual-monitor 1920x1080` "
                        "(cioe' la §4 com'era fino al 12 agosto), e si fa rinascere la "
                        "sessione senza nessun drop-in di banco",
    "atteso_guasto":   1,      # NERA: ZERO MONITOR
    "marca_guasto":    "NERA: ZERO MONITOR",
    "atteso_risanato": 0,
    "rimette_a_posto": True,   # bash /media/REMOTIX/provision-server.sh monitor
    "avvertenza":      "⛔ NON e' un riavvio: prova l'ULTIMO anello (data la configurazione "
                       "persistente, una sessione appena nata ha il monitor).  Che /media si "
                       "rimonti e che qualcuno rilanci il provisioning restano [?]",
},
{
    "nome":            "D4-guardia-della-sessione",
    "comando":         "bash banchi/02-sessione-guardia.sh --etichetta prova -- bash -c 'exit 0'",
    "dove":            "NIC-OS host",
    "atteso_sano":     0,      # sessione sana ⇒ esegue, e ripassa l'uscita del comando
    "guasto":          "sessione-nera",
    "guasto_dettaglio": "bash banchi/02-sessione-lancia.sh guasto, poi la stessa riga",
    "atteso_guasto":   71,     # 70 + 1: la guardia RIFIUTA, e il comando non parte
    "marca_guasto":    "la guardia rifiuta: NERA: ZERO MONITOR",
    "atteso_risanato": 0,
    "rimette_a_posto": True,   # bash banchi/02-sessione-lancia.sh sano
    "controllo_positivo": "e' quello di 02-sessione-stato.py — «layout-mode» nella risposta "
                          "e GetIdletime che cresce — piu' la prova che il comando NON e' "
                          "partito nel caso guasto (grep -x sulla sua riga: assente)",
},
```

---

## 8. Le cuciture

### Che cosa questo giro **promette**

| a chi | che cosa |
|---|---|
| **F2.2 … F2.6** | ⭐ **una riga sola da mettere davanti al proprio comando**: `bash 02-sessione-guardia.sh --etichetta <la vostra scena> -- <il vostro comando>`. Se la sessione non è sana il comando non parte, e non c'è nessuno zero da spiegare |
| **tutte** | le uscite **70-79** sono della guardia, non vostre. **71** = sessione nera; **79** = la scena è caduta sotto la misura |
| **chi eredita la macchina** | dopo un riavvio bastano `provision-server.sh` e `02-sessione-lancia.sh sano`, e la §4 esce **0** o si ferma dicendo perché |

### Che cosa questo giro **chiede**

| a chi | che cosa |
|---|---|
| ⛔ **a chi scriverà il prodotto della fase 2** | il rilievo della §4. Finché `sessione.c:671` è com'è, **I7 resta violato** e questa cura è una riga di configurazione: protegge, ma si può perdere |
| ⛔ **al coordinatore** | ⏳ **il riavvio vero**, quando 7448 e 7501 si potranno lasciar cadere. È l'unica prova che chiude la `[?]` della §2, e va fatta **prima** che la fase 2 misuri qualcosa di serio su questa macchina |
| ⚠ **al coordinatore** | `STUDI.md` §gnome §1.1 va aggiornata (l'headless su NIC-OS è **chiesto**, non accidentale) e adesso porta anche `--virtual-monitor`: la riga in vigore dal 12 agosto è `/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor 1920x1080` |
| ⚠ **a F2.6** | la guardia riguarda la sessione **dopo** la misura: se vi esce **79**, la sessione è caduta mentre misuravate — guardate `Shell.Screenshot` prima di guardare il vostro codice |

---

## 9. Che cosa resta `[?]`

| # | la `[?]` | perché resta |
|---|---|---|
| 1 | ⛔ **Che la macchina si rimetta da sé dopo un riavvio vero** | non riavviato, e non si poteva: §2. Provato l'ultimo anello, non la catena |
| 2 | **Se `provision-server.sh` intero giri ancora** dopo la ristrutturazione | provato il modo `monitor` `[M]`; le altre sezioni sono invariate ma **non rieseguite** — far girare tutto avrebbe riavviato polkit e riscritto `remotix.service` durante il giro di altri agenti |
| 3 | **Se un drop-in nuovo di qualcun altro possa vincere** su quello persistente | la §4 lo **vede** e si ferma (uscita 1), ma nessuno l'ha ancora fatto succedere di proposito: il caso è coperto dal codice, non da una misura |

---

## Il giudizio dell'utente

*Da riempire. `PIANO.md` §0.3 punto 3, invariante **I8**: il metro è quel che l'utente vede.*
