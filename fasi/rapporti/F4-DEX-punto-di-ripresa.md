# Il mouse sul DeX — punto di ripresa

⛔ **Scritto il 14 agosto 2026 a sera, a lavoro NON finito e a giudizio negativo
dell'utente**: *«Non funziona, il mouse è inutilizzabile»*. Questo documento
esiste perché la sessione successiva **non rifaccia le sei strade già chiuse**.

⚠ Chi legge: il difetto è ancora **aperto**. Qui non c'è una cura, c'è una mappa
di quel che è stato misurato — e la mappa vale proprio perché la maggior parte
delle caselle è **smentita**.

---

## 1 · La scena

| | |
|---|---|
| cliente | **Samsung DeX col cavo**, monitor **2560×1080** (ultrawide 21:9), Chrome per Android |
| periferiche | mouse e tastiera **Bluetooth** |
| finestra | `2133×772` CSS · `devicePixelRatio` **1,2** · vista dichiarata **2560×926** |
| server | `192.168.0.2:7700`, sorgente `/media/REMOTIX/src/04-vero-src/src`, lavoro `/media/REMOTIX/tmp/04-vero` |
| utente | **`prova`** (uid 1001) — ⛔ da conservare, vedi la memoria |
| riavvio | `sudo /media/REMOTIX/tmp/riavvia-7700.sh` — ⚠ la pagina si legge **una volta sola all'avvio** (`pagina.c:627`) |

⛔ **Porte da non toccare**: 7448 · 7501 · 7561 · 7571. Il banco 04-b30 (7721-7723,
utente `provao2`) è ancora acceso: `[M]` **non codifica**, quindi non ruba il
codificatore — ma consuma processore e va spento quando l'utente lo dice.

---

## 2 · Il sintomo, con le parole dell'utente

1. *«Il mouse ha sempre problemi con le coordinate degli elementi (esempio barra
   della finestra del terminale)»*
2. *«L'input da tastiera è sempre laggato»*
3. *«È come se si perdessero gli input»*
4. *«Il mouse è al limite dell'usabilità»* → poi **«inutilizzabile»**

---

## 3 · ⛔ LE SEI STRADE CHIUSE — non ripercorrerle

| ipotesi | come è caduta |
|---|---|
| **la conversione delle coordinate sbaglia** | `[M]` verificata a mano sui numeri veri del DeX: `(1170/0,833 − 457)/0,857 = 1105` contro il **1104** dichiarato dalla pagina, e `160/0,833/0,857 = 224` contro **223**. ⭐ E il controllo indipendente sulla schermata: la barra del titolo del terminale stava a tela ≈(636…1370, 232) e il puntatore risultava a **(1104, 223)**. Confermato anche da `F4-AND-1-puntatore.md` |
| **la mappatura ignora le bande** | ⛔ falso: `componi()` riempie `schermo.dipinta` a **ogni fotogramma** e `cl_geometria()` sottrae `bx0`. Il ramo di ripiego lo farebbe, ma non è quello in vigore (`?video=worker` è **spento** per difetto, `pagina.html:527`) |
| **è il Wi-Fi / il risparmio energetico di Android** | ⛔ `F4-AND-5-latenza.md`: Doze e App Standby valgono a schermo spento; il risparmio 802.11 accoda la **discesa**, non la salita. ⭐ E l'utente **usa il cavo** |
| **è l'IME di Android (`keyCode 229`)** | ⛔ `F4-AND-2-tastiera.md`, `[R]` Chromium `ImeAdapterImpl.java:569`: l'IME entra **solo col fuoco su un nodo modificabile**. E `[M]` 13 lettere sono arrivate: con l'IME nel mezzo sarebbero state scartate tutte |
| **incolonnamento nel canale di input** | ⛔ `[M]` dal pannello del DeX: **coda del filo 1 (peggiore 1), puntatori sorpassati 0**. La coda non si è mai riempita |
| **il banco rimasto acceso ruba il codificatore** | ⛔ `[M]` il suo registro ha solo battiti di controllo: **non codifica** |

⭐ **E il tratto «prima di noi» chiude la questione della rete**: `[M]`
`performance.now() − event.timeStamp` = **9 ms per i tasti, 12 ms per i
movimenti**. In quel numero non c'è **nessun salto di rete**. ⇒ Il comando esce
dal telefono in dieci millisecondi: Bluetooth, Android, IME e coda del thread
principale sono **tutti scagionati**.

---

## 4 · ⭐⭐ QUEL CHE REGGE, ED È IL FILONE DA CUI RIPARTIRE

> `[M]` 14 agosto 2026: **134 fotogrammi in due minuti = 1,1 al secondo.**

Due scelte, ciascuna corretta, che insieme fanno il difetto:

1. `figlio.c` — **Mutter consegna un fotogramma solo quando qualcosa cambia**
   («scena ferma: Mutter consegna solo quando qualcosa cambia»);
2. `mutter.c:503` — il cursore lo prendiamo come **metadato**
   (`cursor-mode: CURSORE_METADATO`), cioè **non dipinto dentro l'immagine**.

⇒ **Muovere il mouse sopra lo sfondo non cambia un pixel, quindi non arriva
nessun fotogramma.** Il desktop remoto è, letteralmente, **fermo** mentre l'utente
muove il mouse. *«Come se si perdessero gli input»* è la descrizione esatta di
questo: non se ne perde nessuno, **non si vede che arrivano**.

⚠ E ha una seconda conseguenza, che ha inquinato mezza giornata di misure: il
**giro completo** misurato dalla pagina (`GIRO`, campo `input` di §6.2) si chiude
solo **al fotogramma successivo**. A 1,1 fotogrammi al secondo il «peggiore
2161 ms» **non è latenza**: è attesa del prossimo fotogramma. ⛔ La mediana di
130 ms regge; la coda no.

---

## 5 · ⛔ LA REGRESSIONE CHE HO INTRODOTTO, e la sua misura

Cura tentata: rimettere la **freccia disegnata dalla pagina** (che si muove alla
velocità della mano, in locale) e nascondere il cursore del browser con
`cursor: none` su tutto il modo classico.

`[M]` Risultato, sessione delle 15:09: **4 clic e ZERO movimenti**, contro
**165 · 227 · 320 · 200** nelle quattro sessioni precedenti. Una variabile sola
cambiata. La freccia è rimasta piantata nell'angolo dell'immagine — cioè a tela
(0,0), il valore che `cl_px` non ha mai lasciato.

⇒ `cursor: none` **rimesso a `[data-agganciato="si"]`**, e la freccia disegnata
**resta**. Stato consegnato: due puntatori sovrapposti.

⚠ **`[?]` Il meccanismo non è letto in nessuna fonte.** È una correlazione a una
variabile sola, forte ma **non spiegata**. Ipotesi da verificare: su Android il
cursore che si muove è quello di **sistema**, e nascondere l'icona del puntatore
(`PointerIcon.TYPE_NULL`) gli toglie anche gli eventi di passaggio.

⭐ **Ed è la prima cosa da misurare nella sessione nuova**, perché se è vera
vincola ogni cura futura: **sul DeX non si può nascondere il cursore del
browser**, quindi la strada «disegniamo noi il puntatore» è **preclusa** e resta
solo la strada 6.1.

---

## 6 · Le tre strade aperte, in ordine di forza

### 6.1 ⭐⭐ Chiedere a Mutter un monitor della misura del client

`F4-AND-4-come-fanno-gli-altri.md`, letto nel codice vero: **quattro progetti su
cinque** (Guacamole, KasmVNC, xpra, Chrome Remote Desktop) **non impaginano**:
chiedono al server di cambiare la misura del desktop perché combaci con la
finestra. Chrome RD non impagina **mai** (`desktop_viewport.cc:149`, `std::max`).

⭐ E la misura **è nostra da scegliere**: `mutter.c:502-518` chiama
`RecordVirtual` **senza dire nessuna misura**; la chiediamo dopo, sul flusso
(riga di registro «*cattura avviata sul nodo 53: chiesti 1920x1080*»).

Guadagni: bande zero · conversione a **uno stadio** invece di tre · ⭐ **il 36 %
di pixel neri che oggi codifichiamo e spediamo sparisce**, cioè banda e ritardo
in meno.

⛔ **È una decisione dell'utente**, non del programmatore: cambia la forma del
prodotto e va in `DECISIONI.md`.

### 6.2 Il cursore dentro l'immagine, o un fotogramma su movimento

Se il puntatore non lo può disegnare il client (vedi §5), le uniche strade sono:
chiedere a Mutter il cursore **dipinto** (`cursor-mode` embedded) — che fa
arrivare un fotogramma a ogni movimento, al prezzo di banda — oppure forzare una
cattura quando arriva un `PUNTATORE`. ⚠ Nessuna delle due è misurata.

### 6.3 I difetti trovati leggendo, non ancora provati sul campo

- ⛔ `?video=worker`: `[S]` HTML §4.12.5 vieta di cambiare `width` a un canvas
  trasferito ⇒ `tela.width` resta **16 per sempre** e il puntatore si inchioda a
  (0,0). Oggi non è in vigore, ma è una mina.
- ⛔ `pagina.html:5301` `pieno = innerWidth >= screen.width - 2`: mescola pixel
  CSS zoomati e non ⇒ su DeX vale **`false` per costruzione**, anche a schermo
  intero perfetto. Cura: `matchMedia("(display-mode: fullscreen)")`.
- ⛔ `[S]`+`[R]` in una finestra DeX lo schermo intero **non toglie le barre di
  DeX** ⇒ la promessa di `SPECIFICHE.md` §6.1-bis *«a schermo intero torna
  1:1»* è una **`[?]` nuova e a rischio, sull'uso primario**.
- ⛔ `misura_vista()` non ha guardia su `visualViewport.scale`: con «richiedi
  sito desktop» dichiara `2754` px su un vetro che ne ha 1080 (`[M]`, ×2,55).
- `[R]` `getLayoutMap()` su Android risponde **mappa vuota** senza errore.
- `[R]` la Keyboard Lock su Android **esiste**, da Android 16 QPR1.

---

## 7 · Quel che è stato messo in piedi oggi e va tenuto

⭐ **Tre strumenti nuovi nella pagina**, tutti nel pannello del tastino `⌨`:

1. **il giro completo** — il campo `input` di §6.2 tornava già dentro ogni
   fotogramma e **nessuno lo raccoglieva** (`pagina.html:1568` lo leggeva e lo
   buttava). ⚠ Da leggere con la riserva di §4;
2. **il tratto «prima di noi»** — `performance.now() − event.timeStamp`,
   separato fra tasti e movimenti. ⛔ Non contiene nessun salto di rete: è la
   misura che ha scagionato Android in un colpo solo;
3. **la coda del filo** (`desiredSize`, mai letta prima) e il conto dei
   **puntatori sorpassati**.

E tre cure che restano valide indipendentemente dal difetto aperto:

- `pointermove` accanto a `mousemove` — `[M]` senza, i movimenti si spegnevano
  del tutto (35 clic e zero movimenti in 12 secondi);
- `tabindex="-1"` sulla tela: senza, le due `focus()` dopo l'accesso erano
  **colpi a vuoto** e il fuoco restava nel campo della parola d'ordine (noVNC ha
  la stessa riga, `core/rfb.js:233`);
- `willReadFrequently` **tolto** dalla tela visibile: nessuno ne legge i pixel, e
  il contrassegno teneva l'immagine fuori dalla scheda grafica;
- il **sorpasso del puntatore** quando il filo è pieno (oggi non si è mai
  acceso: `sorpassi 0`).

---

## 8 · La forma del difetto, di nuovo

⚠ Come le sette volte precedenti di questa fase: **nessun pezzo sbagliava per
conto suo.** Mutter fa bene a non mandare fotogrammi inutili; noi facciamo bene a
prendere il cursore come metadato; la pagina fa bene a disegnare il puntatore in
locale. ⛔ **Il difetto sta fra i tre**, e nessun banco lo guardava perché nessun
banco possiede una cucitura.
