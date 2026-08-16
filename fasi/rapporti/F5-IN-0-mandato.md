# Mandato per la fase 5 — la sessione

⛔ **Scritto il 15 agosto 2026, mattina, a fase 4 CHIUSA e macchina in ordine**, per decisione
dell'utente: *«per la fase 5 useremo una nuova sessione»*.

⭐ Il giudizio con cui si chiude quel che c'è prima: *«sia su Linux sia su Android (DeX) è tutto
perfetto»*.

---

## 1 · ⭐ IL COMPITO, e la scena che l'utente giudicherà

> **«Chiude il client, va a pranzo, riapre — e ritrova tutto com'era.»**

`PIANO.md` §«Fase 5 — La sessione» per intero. ⛔ **Il primo gesto è aprire
`fasi/05-la-sessione.md`**, prima di scrivere una riga di codice: `fasi/README.md` lo impone, e la
coda della fase 4 quella regola l'ha violata (il suo documento è stato scritto alla chiusura, e
porta la riserva in testa).

---

## 2 · ⭐⭐ LA MACCHINA, COM'È ADESSO — si legge prima di toccare qualcosa

| | |
|---|---|
| **il server** | ACCESO su `192.168.0.2:7700`, col binario del 15 agosto. Pid in `/media/REMOTIX/tmp/04-vero/pid` |
| **si riavvia** | `printf 'nicfio\n' \| sudo -S -p 'Password:' /media/REMOTIX/tmp/riavvia-7700.sh` — ⛔ e la forma `sudo -S -p 'Password:'` è obbligatoria |
| **il registro** | `/media/REMOTIX/tmp/04-vero/registro.log` (root; `--parlantina` è acceso) |
| **si entra** | `python3 v1/strumenti/sshpw.py '<comando>'` · `--put <locale> <remoto>` |
| **l'utente di prova** | `prova` / `prova2026`, con la sua sessione GNOME headless viva. ⛔ Si conserva, e ⛔ NON si usa `nicfio` (una sessione per utente, §5.1) |
| ⚠ **l'orologio** | quello della macchina di prova è **indietro di due ore**: le ore nel registro non sono le tue |

### Come si costruisce — **due strade, e rispondono a due domande diverse**

| domanda | strada |
|---|---|
| **«compila?»** — venti secondi, mentre si scrive | `bash src/costruisci-in-contenitore.sh` sul portatile: `podman` **da utente**, niente `sudo`. L'immagine si fa una volta sola: `podman build -t remotix-costruzione -f src/Contenitore src/` |
| **«gira?»** — solo sulla macchina di prova | i sorgenti in `/media/REMOTIX/src/04-vero-src/`, poi `bash /media/REMOTIX/enter.sh --root 'bash /srv/src/04-vero-src/src/costruisci.sh'` |

⛔ **Il binario del contenitore NON si copia sulla macchina di prova**: è legato a ngtcp2/nghttp3 di
`/usr/local` **dentro l'immagine**. Il `riavvia-7700.sh` lo verifica e si rifiuta di partire.
⚠ E dentro `enter.sh` il `/srv/src` che si vede **È** `/media/REMOTIX/src` dell'host: è il montaggio
che il 14 agosto era stato cercato e non trovato.

---

## 3 · ⛔ QUEL CHE DELLA FASE 5 È GIÀ VIVO — non si riscrive, si PROVA

*Tutto quel che segue è implementato e **almeno una volta osservato**, ⛔ ma nessuno di questi ha un
banco: è esattamente il lavoro della fase.*

| pezzo | dov'è | che cosa se ne è visto |
|---|---|---|
| **I2 — una sola sessione per utente** | `rcp.c`, il registro dei «posti» + `torna_a_parlare()` | ⭐ `[M]` 15 ago: la seconda sessione viene congedata con **§8.2 `0x0F`**, e il banco `04-b31` caso 18 lo prova |
| **I4 — il palco sopravvive al distacco** | `figlio.c` | ⭐ `[M]` 15 ago: l'utente si è staccato e riattaccato **da due macchine diverse** ritrovando la sessione |
| **il ri-attacco a misura diversa** | `rcp.c`, gancio `tela_del_palco` | ⭐ `[M]` `SESSIONE` concede la tela che il palco ha già, zero fotogrammi scartati |
| **i tre orologi** | `rcp.c`: `TETTO_CIAO` 5 s · `TETTO_CREDENZIALI` · `TETTO_ATTACCA` 10 s · `SILENZIO` 30 s | `[M]` lo staccato per silenzio si vede nel registro |
| **il rilascio dei tasti al distacco** | `rcp.c` `rilascia_al_distacco()`, su congedo · silenzio · errore | `[M]` nel registro: *«rilascio al distacco: 0 fra tasti e pulsanti»* ⛔ **ma con zero tasti premuti**: la prova vera non è mai stata fatta |
| **PAM per intero, asincrono** | `aiutante.c` + `DECISIONI.md` §1.10 | il filo non si ferma più durante la verifica |

---

## 4 · ⛔⛔ QUEL CHE MANCA DAVVERO, in ordine di quanto morde

### 1. ⭐ Il banco del riattacco che **batte un tasto DOPO**

`PIANO.md` lo chiede sia alla fase 5 sia alla 6, e chiude una riserva che la coda della fase 4 si
porta dietro. ⛔ La ragione è misurata: al cambio di geometria **`libei` distrugge e ricrea i
dispositivi assoluti**, `[M]` 15 agosto nel registro — *«il puntatore è stato TOLTO dal compositore
(ricambio n. 640)»* — e `input.c` li riaggancia. ⚠ Ma un banco che **batta un tasto e muova il
puntatore dopo un riattacco** non esiste, e senza quello la prova è verde per costruzione.

⛔ E si stacca **con un tasto premuto**: `RCP.md` §11 la chiama *«la regola col rapporto danno/costo
più alto del documento»*. Un `Ctrl` rimasto giù rende il desktop inservibile e nessuno collega le
due cose.

### 2. ⛔ `SESSIONE_LOCALE_PREVALSA` (0x04) e `GIA_ATTIVA_LOCALE` (0x05): **definiti e mai emessi**

`[R]` Stanno in `src/rcp.h:44-45` e **nessuna riga di nessun `.c` li spedisce**. ⚠ È la stessa forma
di guasto di `RCP_SERVER_IN_CHIUSURA` — definito e senza emittente, trovato il 10 agosto (rilievo
B-7): chi era collegato aspettava i trenta secondi del silenzio e leggeva «errore di rete».

⇒ Serve chi **guarda** le sessioni locali: `logind`. Oggi l'unico file che lo nomina è `sessione.c`.

### 3. ⛔⛔ La macchina si addormenta — e **NON è teorico: si è visto stanotte**

⭐ `[M]` 15 agosto 2026: in due schermate del desktop remoto compare la notifica di GNOME

> **«Automatic Suspend — Suspending soon because of inactivity»**

`sleep-inactive-ac-type` vale `suspend` a **900 s**, upstream e su Debian `[R]`. ⛔ Oggi non morde
solo per accidente, e **`energia.c` in `src/` non esiste affatto** (era un file di v1). La cura è
una chiamata sola — `SessionManager.Inhibit(…, 12)`, cioè `SUSPEND|IDLE` **insieme** — ⛔ e mai il
bit `LOGOUT`.

⚠ E senza questa, il banco delle «sei ore di abbandono» **non misura niente**: la macchina si
sospende a quindici minuti e al risveglio la sessione c'è ancora, quindi il banco resta verde.

### 4. ⚠ L'headless si **dichiara e si verifica**

Il blocca-schermo di GNOME non mostra un blocco: **stacca**. Ci salva `is_headless()`, che però
Mutter si mette da solo quando la sessione logind non ha un seat — cioè **per accidente, non perché
l'abbiamo chiesto** (`DECISIONI.md` §4.3-bis). Va chiesto, e verificato **dopo** l'avvio.

### 5. Il resto della fase, dal piano

Distacco e riaggancio **due volte di fila** (`LEZIONI.md` §2.3-ter); la sessione **senza nessuno che
guarda** (in v1 il monitor virtuale spariva al distacco e `libmutter` andava in asserzione fallita);
i tre orologi ciascuno con la sua prova.

---

## 5 · ⛔ E QUEL CHE LA CODA DELLA FASE 4 HA LASCIATO APERTO

| | |
|---|---|
| ⏳ **la riga che manca a `RCP.md` §7.1** | che cosa fa il server quando il palco cambia misura **da sé**. Oggi lo richiama e non manda nessun `TELA` — funziona, ⛔ ma è una regola del prodotto che l'arbitro non nomina |
| ⚠ **i 4 ms di ritardo medio aggiunto** | `MOVIMENTO_ATTESA_S` è 8 ms ed è un **ripiego dichiarato**: la cura vera è un descrittore che la cattura scrive quando il fotogramma è pronto, nello stesso `poll()` del padre e di `libei`. Tocca il posto di scambio di `cattura.c`, che gira sul thread di tempo reale |
| ⚠ **il ripiego su KWin dichiarato nel registro** | non verificabile finché KDE è la fase 11 |
| `[?]` **il mezzo pixel del `margin: 0 auto`** | giudizio dell'utente sul DeX: «tutto perfetto» ⇒ **non si presenta**, ma nessuno l'ha misurato |
| ⚠ **i banchi RCP/1 non esercitano `ADATTA_TELA`** | `01-b3-cliente.py` e `01-b4-validatore.py` restano verdi perché il filo non è cambiato |

---

## 6 · ⭐⭐ LE TRE LEZIONI DI STANOTTE, da non ripagare

1. **Una deduzione al posto di un messaggio è un difetto che aspetta** (`LEZIONI.md` §7.5). Il padre
   indovinava l'esito di una richiesta guardando i fotogrammi; reggeva finché gli eventi erano uno
   per volta, e cadeva appena se ne accavallavano due.
2. **Un'attesa che protegge un anello è un ritardo per tutti gli altri** (§6.2-bis). I 250 ms
   dell'attesa del fotogramma erano il ritardo di ogni clic.
3. ⛔ **Il numero che spiega tutto può essere nel registro da un giorno** (§6.2-ter). Due volte in
   due giorni: *«3 attese a vuoto»* e *«213 movimenti registrati»*. ⇒ Quando un numero non torna, si
   rilegge il registro **cercando quel numero**, non il difetto.

⚠ E la quarta, che non è una lezione ma un fatto: **tre difetti su tredici li ha trovati l'utente**,
non i banchi — compreso il più grosso della notte. Il metro è quel che lui vede (I8).

---

## 7 · Dove guardare

- `fasi/04-si-comanda.md` §«la coda della fase 4» — il documento di chiusura, con le misure;
- `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` — il rapporto tecnico, i dieci difetti refutati;
- `banchi/04-b31-tela.c` (19 casi) e `banchi/04-b31-certifica.sh` (12 guasti innestati) — ⭐ **il
  modello di banco da copiare**: l'atteso dichiarato prima, e il controllo che i casi rossi siano
  **quelli attesi**;
- `PIANO.md` §«Fase 5» e §«Fase 6» (quest'ultima con la tabella di quel che è già fatto);
- `DECISIONI.md` §5.0-sexies (la tela), §4.3-bis (l'headless), §1.10 e §1.10-bis (PAM e il figlio).
