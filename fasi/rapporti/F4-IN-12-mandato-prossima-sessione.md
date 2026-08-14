# Mandato per la prossima sessione — un pezzo solo, e chiude quattro sintomi

⛔ **Scritto il 14 agosto 2026 a notte**, a lavoro **riuscito** ma non finito.
⭐ Giudizio dell'utente sul Samsung DeX, testuale: *«adesso è un'altra cosa»* — e poi, dopo le due
cure finali: *«i 2 problemi segnalati sono risolti»*, *«anche su Linux mouse e tastiera
funzionano»*.

---

## 1 · ⭐ IL COMPITO, ed è uno solo

> **Scrivere la catena `figli_ritela()` → `cattura_ridimensiona()`**: quella che porta la misura
> chiesta dal client dal filo fino a `pw_stream_update_params()`.

Oggi il server risponde `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` **e lo dichiara nel registro
nominando la riga che manca** — il ripiego è scritto in `src/rcp.c`, nel caso `T_ADATTA_TELA`.

### Perché vale più di quanto sembri: chiude QUATTRO sintomi, non uno

| sintomo | perché sparisce |
|---|---|
| **le bande nere laterali** | le due tele combaciano ⇒ niente da impaginare |
| **il testo interpolato** | scala **1** ⇒ nessuno ricampiona l'immagine |
| **il ri-attacco a misura diversa** | `[M]` Mutter cambia a caldo in **41,6 ms**, labwc in **5,1 ms** |
| ⭐⭐ **i 4 secondi fra login e desktop** | vedi §2 |

⇒ Non è fortuna: tutti e quattro nascono dalla stessa cosa — **la misura della tela non la chiede
nessuno**.

---

## 2 · ⭐⭐ Il quarto sintomo, misurato la notte del 14, e la sua cura non ovvia

`[M]` Registro del server, sessione delle 21:32:55:

```
21:32:55.607  §5.2 vuole una CHIAVE — richiesta girata al palco
   … una ogni 200 ms, per 4,4 secondi …
21:33:00.033  fotogramma 1 SPEDITO
```

e per tutto quel tempo il figlio scrive, una riga al secondo:

> `183 fotogrammi consegnati (2 chiavi), **659 attese a vuoto** (scena ferma: Mutter consegna solo
> quando qualcosa cambia)`

⇒ Il client chiede l'immagine, il server gira la richiesta al palco, **il palco non ha niente da
dare**: si aspetta che il desktop si muova da solo.

⛔ **Xpra risolve con `buffer_refresh` («ridipingi adesso») e a noi non serve**: su Wayland non si
può ordinare a un compositore di ridipingere. ⭐ **Ma la leva ce l'abbiamo già e è misurata:
riavviare il flusso consegna un buffer** — ed è precisamente quel che fa
`pw_stream_update_params()`.

⇒ **Il client che chiede la tela della propria misura all'attacco riconfigura il flusso, e il
fotogramma arriva.** La cura del ritardo è un effetto collaterale della cura delle bande.

---

## 3 · ⛔⛔ IL BLOCCO DA SCIOGLIERE PRIMA DI SCRIVERE UNA RIGA

**Non sono riuscito a costruire il C.** E finché non si costruisce, ogni riga nuova è codice che
nessuno ha mai visto girare.

| dove | che cosa manca |
|---|---|
| questo portatile (`CHUWI`) | `nghttp3` e `libswscale` ⇒ `make` si ferma su `main.c` e `codificatore.c` |
| macchina di prova (`192.168.0.2`) | **niente `gcc`, niente `make`**: il rootfs è live in RAM |
| dentro il contenitore (`bash /media/REMOTIX/enter.sh --root '...'`) | `gcc` e `make` **ci sono** ⛔ ma `/media/REMOTIX` **non è montato**, e `/srv/src` che si vede dentro **non è** quello dell'host — ho copiato i sorgenti in `/srv/src/04-vero-build` sull'host e dentro non c'erano |

⇒ ⭐ **La prima domanda alla prossima sessione è all'utente**: *come si costruisce questo
progetto?* Probabilmente c'è un montaggio da passare a `enter.sh` o una cartella condivisa che non
ho trovato. ⚠ Non si scrive `figli_ritela()` prima di saperlo.

---

## 4 · Quel che è GIÀ SCRITTO e non va rifatto

⭐ Tutto controllato col compilatore vero (`gcc -fsyntax-only` con i flag veri), gemelle
`banchi/rcp/` allineate byte per byte, **ma non costruito né eseguito**.

| file | che cosa c'è di nuovo |
|---|---|
| `src/rcp.c` | ⭐ `T_ADATTA_TELA` **servito** (prima buttava fuori il client, contro `RCP.md:483`) · `manda_tela()`, cioè `TELA` **finalmente spedito sul filo**: la funzione che cambiava lo stato c'era, il messaggio no |
| `src/rcp.h` | `rcp_misura_ammessa()` — `200…8192` e parità, **in un posto solo**. ⛔ Sta lì e non in `cattura.h` perché `rcp.h` include solo `stdbool/stddef/stdint`: è autosufficiente perché la gemella compili dentro `bsslserver` |
| `src/cattura.c` | la guardia **chiesto contro concesso** sul formato negoziato |
| `src/mutter.c` | `scala_dei_monitor_logici()` + la guardia: `[M]` con `scaling-factor 2` il layout diventa `1067×2 = 2134 ≠ 2133` ed è lo spazio dell'**input** |
| `src/pagina.html` | le bande **fuori dal buffer** (`componi()` + `cornice()` + `margin: 0 auto`) · `CURSORE_FORMA` cucita · l'interruttore A/B del puntatore · `SCENA` (età dell'immagine al movimento) · una porta sola per i movimenti · clic e rotella che portano la posizione |

⚠ **`src/pagina.html` è in linea e funziona**: la pagina non ha bisogno di costruzione, solo del
riavvio del server.

---

## 5 · ⛔ Quel che è MORTO — non ripescarlo

| ipotesi | come è caduta |
|---|---|
| `cursor: none` toglie i movimenti su Android | ⛔ era `pointermove` che **mancava** (`[R]` `git show 0075b4f`), e in Android `dispatchPointerEvent()` viene **prima** di `maybeUpdatePointerIcon()` |
| la cattura del puntatore (Pointer Lock) aiuta | ⛔ `[M]` **peggiora**: `movementX` è ricostruito da Chromium e i micro-movimenti scartati |
| il problema è il disegno del puntatore | ⛔ `[M]` i tre modi (`due`/`sistema`/`disegnata`) erano **indistinguibili** all'uso |
| «1,1 fotogrammi al secondo» spiega il mouse | ⚠ `[M]` erano **8/s** e il mouse andava male lo stesso |
| il difetto dei movimenti è nostro | ⛔ è **noVNC #1727**, aperto dal 2022, specifico di Samsung, riprodotto anche da un'app **nativa** (moonlight-android #573) |

---

## 6 · Le decisioni e i documenti dove guardare

- ⭐ `DECISIONI.md` **§5.0-sexies** — la decisione dell'utente, le quattro misure, le tre guardie,
  e la **nota sul ri-attacco** che ha chiesto lui;
- `DECISIONI.md` §5.0-bis — il ripiego su **KDE ≤ 6.7.4** (⛔ `Plasma/6.8` **non esiste**, ultimo
  tag `v6.7.4`);
- `SPECIFICHE.md` §11.2 — ⛔ **XFCE e LXQt non sono lo stesso caso**: su XFCE `xfsettingsd` spegne
  gli output nuovi;
- `fasi/rapporti/F4-IN-6-punto-fermo.md` — il punto fermo con la contraddizione che ha sbloccato
  tutto;
- `fasi/rapporti/F4-IN-7-due-tele.md` — il disegno in byte;
- `F4-IN-1…5` gli studi (xrdp · gnome-remote-desktop · xpra · Android · Devolutions),
  `F4-IN-8…11` i compositori e il codificatore.

---

## 7 · ⭐⭐ La riga di metodo da portarsi via

> Per due giorni si è curato **un giudizio** — *«il mouse è inutilizzabile»* — invece di **un
> sintomo**.

Il fatto che ha sbloccato tutto — *«si muove solo col tasto sinistro premuto»* — è arrivato dopo
cinque studi, quattro cure e otto ipotesi smentite. Era a **una domanda** di distanza, e la
domanda era: **«che cosa vedi esattamente succedere?»**

⚠ E la seconda, che vale quanto la prima: la contraddizione che la conteneva era **nel registro da
ore** — 213 movimenti registrati dal server mentre l'utente ne vedeva zero — e ci sono passato
sopra quattro volte perché avevo ogni volta una cura pronta da provare.

⇒ *Una cura pronta è il modo più efficace di non guardare una contraddizione.*
