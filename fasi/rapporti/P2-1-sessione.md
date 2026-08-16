# P2.1 — Il PRODOTTO del primo anello: la sessione GNOME

*Prodotto della sotto-fase 1 di 6 della fase 2. Scritto il 12 agosto 2026, la sera.
Il banco che lo giudica e' di `fasi/rapporti/F2-1-sessione.md`, scritto **prima**, e non e' stato
toccato. Il rilievo che lo ordina e' `fasi/rapporti/D4-sessione-nera.md` §4.*

> ⭐ **Questo giro ha scritto prodotto**, ed e' il primo della fase 2: `src/sessione.c` (935 righe,
> **562 vere**) e `src/sessione.h` (269). ⛔ E **non ha toccato** `src/Makefile`, `src/main.c` ne'
> nessun altro file di `src/`: le righe da innestare stanno in §6, e le innesta il coordinatore.

---

## 1. Che cosa doveva produrre, e che cosa produce

**Il server fa nascere da se' una sessione GNOME headless che ha davvero un monitor** — e non lo
affida a una riga di configurazione.

| la domanda | prima | adesso |
|---|---|---|
| chi chiede il monitor virtuale | `v1/banco/provision-server.sh` §4, una riga in `/etc` su un rootfs che vive in RAM | ⭐ **il programma**, a ogni nascita di sessione, e verifica di essere stato obbedito |
| che cosa aspetta chi avvia | `sessione_viva()` — «il bus risponde» | ⭐ **il monitor**: `sessione_stato()`, che ha un numero per stato |
| che cosa succede a una sessione **viva e nera** | niente: `sessione_assicura()` diceva «c'e' gia'» e tornava vero | ⭐ la **dichiara** e la fa **rinascere** — `[M]` §4.4 |
| su quale compositore si scrive il drop-in | ⛔ solo KWin (`v1/…/sessione.c:671`), e su GNOME `larghezza` e `altezza` si perdevano | **sempre**, e la scrittura non sta piu' dietro un `if` sul compositore |

⛔ **L'invariante pagato e' I7**: *la protezione di un difetto noto sta nel programma, non in una riga
di configurazione che si puo' perdere*. Quella riga si **era** persa, e la macchina e' stata nera dal
10 al 12 agosto senza che nessuno se ne accorgesse.

---

## 2. Che cosa ho portato da v1, e che cosa ho **lasciato**

*`v1/remotix-c/src/sessione.c`, 797 righe vere. Portato circa un terzo.*

| portato | dove stava | perche' |
|---|---|---|
| `sessione_bus()` | 20-65 | la connessione **nostra**, senza «exit-on-close»: al logout `gnome-session-ctl.c:130-133` ferma `dbus.service` e GIO farebbe `raise(SIGTERM)` per conto nostro. E' la pila del 4 agosto 2026 |
| `componi_ambiente()`, ramo GNOME | 408-540 | l'ambiente da zero, `CODER.md` §4.5 — **dieci** variabili, una per volta |
| `locale_utf8()` + `locale_esiste()` | 145-193 | la locale che dev'**esistere**, non solo dirsi UTF-8. ⭐ E sul ferro **ha morso davvero**: vedi §5 |
| la forma di `scrivi_dropin()` | 569-623 | cartella `user.control`, file, `daemon-reload` — e la regola «il drop-in **prima** del comando» |
| `avvia()` | 625-648 | `setsid --fork`, e il registro della sessione in `$XDG_RUNTIME_DIR` |
| `esci_gnome()` con `Logout(1)`→`Logout(2)` | 699-711 | il congedo di `STUDI.md` §gnome §3.2 |

| ⛔ **lasciato li'** | righe | perche' |
|---|---|---|
| tutto il ramo **KWin**: `nome_occupato()`, `esci_kde_ordinato()`, `esci_kde_a_forza()`, `SESSIONE_COMANDO_KDE` | ~90 | V2 alla fase 2 serve GNOME. ⛔ E `TipoCompositore`/`compositore.h` **in V2 non esistono**: crearli sarebbe apparato per un compositore che questa fase non serve — ed e' proprio il parametro che nascondeva il difetto |
| `scrivi_tema_cursore()` + `scrivi_cursore_vuoto()` + `cartella_cursori()` | ~120 | e' la cura del doppio puntatore di **KWin** (formato Xcursor scritto a mano). Su GNOME il cursore non sta dentro l'immagine catturata (`STUDI.md` §gnome §5.2) |
| `scrivi_regole_menu()` + `cartella_regole()` | ~35 | il **KIOSK** di KDE. Su GNOME l'equivalente e' il lockdown di dconf (`STUDI.md` §gnome §5.1), che e' un lavoro suo |
| `ksmserverrc`, `XDG_MENU_PREFIX`, `XCURSOR_*`, `XDG_CONFIG_DIRS` | ~30 | leve di Plasma |
| il parametro `comando` di `sessione_assicura()` | — | nessuno gli passava mai niente di diverso dal predefinito: una leva che moltiplicava le scene senza che nessuno la usasse |

E **una cosa portata da un banco invece che dal prodotto**: l'attesa di `inactive` e non di «diverso
da `active`» (`banchi/02-sessione-lancia.sh:ferma_e_aspetta`, difetto 4 della fase 0). v1 aspettava
solo che il processo sparisse; qui serve di piu', perche' **subito dopo si fa rinascere** la sessione,
e ripartire durante `deactivating` e' un'altra prima esecuzione.

### ⭐ E tre cose che in v1 non c'erano affatto

1. **`sessione_stato()`** — le due domande separate. Legge `GetCurrentState`, conta i monitor, e
   sceglie **per nome** (`MetaVirtualMonitor`), non per misura e non per indice: il 12 agosto sulla
   macchina ce n'erano **due**, `Meta-0` e `Meta-1`, **entrambi 1920×1080@60**.
2. ⛔ **La distinzione fra «zero» e «non ho potuto leggere»** (E8), in tre punti: il bus che non si
   apre; `ServiceUnknown` (→ 4 morta) contro qualunque altro errore (→ 5 non letta); e ⭐ **la forma
   della risposta**, che si controlla invece di dichiararla alla chiamata — cosi' il giorno in cui
   Mutter aggiunge un campo il verdetto e' «non so leggere» e mai «zero monitor».
3. ⭐ **Il controllo positivo dentro il prodotto**: `layout-mode` dev'esserci fra le proprieta' di
   `GetCurrentState`. Se non c'e', e' rotta la mia lettura — e allora non ho il diritto di dire «zero
   monitor». E' la stessa regola che il banco di F2.1 applica a se stesso.

---

## 3. Come il monitor finisce **nel programma** invece che nella configurazione

```
sessione_assicura(1920, 1080)
  │
  ├─ sessione_stato()                       ← «e' viva» E «ha un monitor», separate
  │    SANA        → non tocca niente (il palco appartiene alla sessione, I4)
  │    NON_LETTA   → ⛔ non tocca niente: «non ho potuto guardare» non e' «non c'e'»
  │    MISURA/E2   → ⚠ dichiara, elenca i monitor per nome, e prosegue
  │    NERA/MORTA  → prosegue qui sotto
  │
  ├─ scrivi_dropin()   ⛔ SEMPRE, non «se il compositore e' KWin»
  │    $XDG_RUNTIME_DIR/systemd/user.control/org.gnome.Shell@wayland.service.d/
  │        zz-remotix-monitor.conf
  │    ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor 1920x1080
  │    → systemctl --user daemon-reload
  │    → ⛔ RILEGGE `show -p ExecStart --value`: scritto non e' in vigore (E1).
  │         se un altro drop-in vince, si ferma QUI e lo scrive
  │
  ├─ se era NERA: sessione_termina()   ⛔ e solo DOPO che il drop-in e' in vigore,
  │                                      o si porterebbe via una sessione per
  │                                      rimpiazzarla con un'altra sessione nera
  ├─ avvia()      env -i composto da zero, SHELL vuota, setsid --fork
  └─ aspetta ⭐ IL MONITOR, non la vitalita'
        e restituisce **lo stato del mondo**: 0 riuscito, e ogni altro numero
        dice in che modo non lo e'
```

**Tre dettagli che sono la cura, non il contorno:**

- ⛔ **`zz-`** non e' un vezzo: i drop-in di tutte le cartelle si applicano in ordine di **nome file**,
  e in `/etc/systemd/user` ce n'e' gia' uno che si chiama `remotix-headless.conf`. `zz-…` viene dopo,
  quindi vince — **e la vittoria si verifica**, non si spera.
- ⛔ **Il numero d'uscita e' lo stesso alfabeto del banco** (0 SANA · 1 NERA · 2 MISURA · 3 SCELTO DA
  SE · 4 MORTA · 5 NON LETTA). Nessuno deve tradurre, e chi traduce sbaglia. I due numeri che il banco
  ha in piu' — **6 DISACCORDO** e **7 SHELL NON VUOTA** — il prodotto li **previene** invece di
  misurarli (rilegge l'`ExecStart` in vigore; e `SHELL` la mette vuota di sua mano). Che il prodotto
  non possa produrre uno stato **non toglie al banco il dovere di saperlo vedere**: quei due restano
  suoi.
- ⛔ **`SHELL=` vuota e non assente.** Per `gnome-session.in:3-14` il controllo e' `[ -n "$SHELL" ]`,
  quindi assente e vuota sono la stessa cosa — ma **due cose diverse per chi misura**: vuota si vede
  in `/proc/<gnome-session-binary>/environ`, assente si confonde con «non ho letto l'ambiente». v1 la
  lasciava assente **per costruzione, senza saperlo**.
- ⚠ **`XDG_SESSION_ID` NON si passa**, e la ragione e' scritta nel codice: `STUDI.md` §gnome §3.1 avverte che
  senza di essa Mutter puo' agganciare la sessione logind sbagliata — ma quella che erediteremmo e' la
  sessione di **chi ci ha avviati** (un ssh, cioe' `tty`), e regalargliela sarebbe mandarlo sulla
  sessione sbagliata con la nostra firma sopra. La scena misurata sana non la porta.

---

## 4. ⛔ L'esito del banco **contro il mio codice** — i tre numeri

### 4.1 Che cosa lo giudica, e chi l'ha scritto

| | |
|---|---|
| il **giudice** | `banchi/02-sessione-stato.py` e `banchi/02-sessione-guardia.sh` di F2.1/D4 — ⛔ **non riscritti e nemmeno sfiorati**. Le loro impronte si confrontano con quelle del deposito prima di credergli: `d509134f…` e `3e329a96…`, identiche `[M]` |
| il **programma minimo** | `banchi/02-sessione-costruisci.sh`, che porta un `02-sessione-prova.c` di **~50 righe**: chiama `sessione_assicura()` e restituisce il suo numero. `CODER.md` §3.6 alla lettera |
| il **guasto** | ⛔ non inventato: e' `v1/…/sessione.c:671` rimesso su una copia del sorgente — `if (0 && !scrivi_dropin(…))`, cioe' il corto circuito che faceva entrare la misura nella funzione e perderla. E l'innesto **si verifica di essere entrato** (una riga, non zero), e il sorgente del prodotto si verifica di **non portarlo** |
| il **lucchetto** | 7511, lo stesso di F2.1: una sessione grafica e' una per utente (I2) |

### ⭐ 4.2 La scena — «la configurazione dice di NO», ed e' tutto il punto

Una prova fatta su una macchina la cui configurazione **chiede gia'** il monitor non dimostrerebbe
niente: il monitor ci sarebbe comunque, e il prodotto potrebbe non scrivere una riga restando verde.

⇒ Il ciclo gira dentro la scena **opposta**: un drop-in `zy-scena-provisioning-perduto.conf` rimette
l'`ExecStart` com'era fino al 12 agosto — `gnome-shell --headless --no-x11`, **senza**
`--virtual-monitor` — cioe' la macchina come sarebbe se `provision-server.sh` §4 si perdesse di nuovo.

```
  remotix-headless.conf   (/etc, persistente: CHIEDE il monitor)
< zy-scena-…              (la scena del banco: NON lo chiede)     ← vince su /etc
< zz-remotix-monitor.conf (quello che scrive il PRODOTTO)         ← vince su tutti
```

⭐ Cosi' **la differenza fra 0 e 1 e' una riga di prodotto**, non una riga di configurazione: nei tre
giri la configurazione diceva **no** tutte e tre le volte. ⛔ E la scena **si impone**: dopo averla
scritta si rilegge l'`ExecStart` in vigore, e se dice ancora `--virtual-monitor` il banco si ferma.

### ⭐ 4.3 I tre numeri — `[M]` 12 agosto 2026, 18:28-18:29, NIC-OS host

*Attesi scritti prima del giro, in testa a `ciclo()`.*

| giro | atteso prodotto | **prodotto** | atteso giudice | **giudice** | atteso guardia | **guardia** |
|---|---|---|---|---|---|---|
| **sano** (il mio codice) | 0 | **0 SANA** | 0 | **0** | 0 | **0** |
| **guasto** (il ramo GNOME di v1) | 1 | **1 NERA: ZERO MONITOR** | 1 | **1**, con la marca | 71 | **71** — rifiuta, e il comando non parte |
| **risanato** | 0 | **0 SANA** | 0 | **0** | 0 | **0** |

```
⭐ P2.1 E' CERTIFICATO: sano 0 → guasto 1 (nel suo punto) → risanato 0
```

- ⭐ **Tre giudici indipendenti per ogni giro**, e devono dire lo stesso: il prodotto su se stesso, lo
  strumento di F2.1 dal bus, e la guardia con le due domande separate.
- ⛔ E il guasto e' rosso **nel suo punto**: `NERA: ZERO MONITOR`, non un rosso qualunque.
- **I vicini**: 7448 → 2 ascoltatori prima e dopo; 7501 → 2 prima e dopo. Sessione grafica fermata e
  rinata **cinque** volte in tutto, e i due server non se ne sono accorti.

### ⛔⭐ 4.4 Le due misure che il ciclo **non** tocca, fatte a mano

| che cosa | atteso | **misurato** |
|---|---|---|
| ⭐ **la sessione e' gia' sana: `assicura` la tocca?** | 0, e lo stesso processo | **0**, `pid 275020 → 275020`, e la riga *«c'e' gia' e ha il monitor chiesto: non la tocco (I4)»* |
| ⭐⭐ **la sessione e' VIVA E NERA** — la storia dei due giorni | dichiara, e la fa rinascere → 0 | **0**: `pid 275716` (nera, zero monitor) → dichiarata *«LA SESSIONE C'E' ED E' NERA … la faccio RINASCERE, e lo scrivo»* → `pid 276233` con `Meta-0`/`MetaVirtualMonitor`/1920×1080@60. Guardia dopo: **0** |

⛔ La seconda e' **la cura vera**, e nel ciclo non si vedeva: li' la sessione si ferma sempre prima, e
il caso «viva e nera» non si sarebbe presentato mai. ⚠ E in tutta la misura la configurazione
persistente **continuava a non chiedere il monitor**.

### ⛔⭐ 4.5 Che cosa NON ha funzionato — **il primo giro guasto e' uscito VERDE, col guasto vivo**

`[M]` 12 agosto, 18:27:39. Prima stesura del banco: `assicura` col codice di v1 dentro ha detto
**`0 SANA`**, e i tre giudici hanno detto **0** tutti e tre.

**Nessuno mentiva: la scena non era quella dichiarata.** La scena si imponeva **una volta sola** in
testa al ciclo; il giro «sano» faceva scrivere al prodotto il suo `zz-remotix-monitor.conf`, quel file
**sopravviveva al giro dopo**, e il giro «guasto» — che il drop-in non lo scrive per costruzione —
nasceva col monitor **lasciato dal giro precedente**.

- ⛔ E' la forma peggiore (`CODER.md` §4.6, `REVIEWER.md` §1 punto 3): **verde col difetto vivo**, cioe'
  una prova che da' fiducia. La stessa che F2.2 ha pagato il mattino dello stesso giorno.
- ⭐ **Curato**: la scena si rimette **prima di ogni giro** — si tolgono i due `zz-`, si riscrive
  `zy-`, `daemon-reload`, e si **verifica in vigore** che `--virtual-monitor` non ci sia. Se non si
  impone, quel giro non si misura.
- ⭐ E l'ha trovato **girare**, non rileggere: il difetto era in un file scritto e riletto un'ora
  prima.

---

## 5. Le misure, in breve

*Tutte NIC-OS host, 12 agosto 2026. La scena accanto a ogni numero.*

| che cosa | misurato | scena |
|---|---|---|
| il monitor letto dal **mio** parser | `Meta-0` / `MetaVendor` / **`MetaVirtualMonitor`** / `0x00` / **1920×1080@60.000** | sessione sana, lettura sola |
| ⭐ e coincide col banco di F2.1, campo per campo | stesse quattro stringhe e stessa misura | `02-sessione-stato.py` sulla stessa sessione |
| quanto ci mette una sessione a nascere **col monitor** | **~5,5 s** (avvio 18:28:53,4 → SANA 18:28:58,9), di cui **5,0 di grazia dichiarata** | scena senza monitor, prodotto |
| quanto ci mette a dire **NERA** | **~5,5 s**, non 40: la grazia scade e il numero e' quello | innesto v1 |
| il congedo `Logout(1)` | riuscito **5 volte su 5**, mai servito `Logout(2)` | sessione non presidiata, nessun inibitore |
| ⭐ **il ripiego della locale, dichiarato — e ha morso davvero** | `LANG=it_IT.UTF-8` e' UTF-8 **di nome** e **non e' generata**: la sessione parte con `C.UTF-8`, e la riga lo dice | ogni avvio |
| l'`ExecStart` in vigore dopo il drop-in del prodotto | `argv[]=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor 1920x1080` | riletto dal gestore, non dal file |
| 7448 / 7501 | **2 + 2 prima, 2 + 2 dopo** | cinque nascite e morti di sessione |

⚠ **E una cosa che questi numeri NON dicono**: che il prodotto compilato **dentro il server** si
comporti cosi'. Qui il modulo e' stato costruito nel contenitore e **eseguito sull'host**, dove vivono
`logind`, `systemd --user` e `/dev/dri`. Vedi la `[?]` 1 di §8.

---

## 6. ⛔ Le righe esatte da innestare — `Makefile` e `main.c`

*Non le ho scritte io: quattro altri agenti stanno scrivendo gli altri anelli, e quei due file sono il
punto in cui ci si scontrerebbe.*
⚠ **`gio-2.0` serve anche a F2.2** (`banchi/02-cattura-lancia.sh` compila gia' con
`libpipewire-0.3 gio-2.0 libdrm`): le righe qui sotto vanno messe **una volta sola**, non due.

### 6.1 `src/Makefile`

**(a)** riga 33-34, in coda a `SORGENTI`:

```make
SORGENTI := main.c trasporto.c webtransport.c pagina.c comando.c certificati.c \
            tls.c registro.c rcp.c autenticazione.c aiutante.c sessione.c
```

**(b)** subito **dopo** la riga 78 (`override CFLAGS += -D_GNU_SOURCE`):

```make
# ⛔ gio-2.0 — il bus di sessione e il drop-in dell'unita' della Shell
#    (`src/sessione.c`).  Su Debian Trixie: `libglib2.0-dev`.
# ⚠ `override` per la stessa ragione della riga sopra: chi passa CFLAGS= sulla
#   riga di comando cancellerebbe anche questa, e `gio/gio.h` sparirebbe con un
#   errore che non nomina nessuna opzione.
override CFLAGS += $(shell pkg-config --cflags gio-2.0)
```

**(c)** riga 87, `LIBS`:

```make
LIBS := -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam \
        $(shell pkg-config --libs gio-2.0)
```

**(d)** riga 145-146, l'elenco del bersaglio `dipendenze` — ⛔ o una dipendenza nuova fallirebbe venti
righe dopo su un `#include` che nessuno collega alla libreria assente:

```make
	for h in ngtcp2/ngtcp2.h ngtcp2/ngtcp2_crypto_ossl.h nghttp3/nghttp3.h \
	         openssl/ssl.h security/pam_appl.h gio/gio.h; do \
```

**(e)** in fondo, con le altre dipendenze di intestazione:

```make
# ⭐ `sessione.c` — la sessione GNOME headless che nasce CON un monitor
#    (invariante I7).  ⚠ NON e' fra i `GEMELLATI`: e' del PRODOTTO e basta.
sessione.o:       sessione.h registro.h
```

### 6.2 `src/registro.h` — una riga, e toglie una stonatura

Accanto alle altre sei aree; ⛔ e allora si **toglie** il `#define REG_SESSIONE "sessione"` che oggi
sta in testa a `src/sessione.h` con la nota che lo dichiara provvisorio:

```c
#define REG_SESSIONE "sessione"
```

### 6.3 `src/main.c`

**(a)** nel blocco di `#include` (righe 51-58), in ordine alfabetico fra `registro.h` e `tls.h`:

```c
#include "sessione.h"
```

**(b)** **prima** della riga 312 (`pam_aiuto = aiutante_accendi();`):

```c
	/* ⛔⭐ IL PALCO PRIMA DEGLI ASCOLTATORI — I4, e il difetto dei due giorni.
	 *
	 *     Qui, e non alla connessione, per tre ragioni dichiarate:
	 *     · il palco appartiene alla SESSIONE, non alla connessione (I4), e
	 *       sopravvive al distacco;
	 *     · far nascere una sessione costa fino a 40 s, e dentro il ciclo
	 *       `poll` fermerebbe TUTTE le connessioni insieme — la stessa forma
	 *       appena curata su PAM (`CODER.md` §4.4, `DECISIONI.md` §1.10);
	 *     · qui gli ascoltatori non sono ancora aperti, quindi non c'e'
	 *       nessuno in attesa: la porta compare quando c'e' che cosa mostrare.
	 *
	 * ⚠ E prima dell'aiutante di proposito: `sessione_assicura()` genera un
	 *   processo, e un processo generato dopo si porterebbe dietro il
	 *   socketpair dell'aiutante.  (GLib chiude da se' i descrittori > 2 nel
	 *   figlio, quindi oggi non accadrebbe — ma l'ordine giusto non si affida
	 *   a un comportamento di libreria.)
	 *
	 * ⚠ E il ripiego si DICHIARA (`CODER.md` §4.2): senza sessione il server
	 *   parte lo stesso — la pagina e l'autenticazione della fase 1 funzionano
	 *   — ma non c'e' niente da catturare, e chi legge il registro lo sa. */
	{
		bool nata = false;
		SessioneStato s = sessione_assicura(1920, 1080, &nata);

		if (s != SESSIONE_SANA)
			registro_dice(REG_AVVIO,
			              "⛔ nessuna sessione grafica con un monitor "
			              "(%d %s): il server parte lo stesso, ma non c'e' "
			              "niente da catturare.  Il ripiego e' dichiarato, "
			              "non silenzioso (CODER.md §4.2)",
			              (int) s, sessione_marca(s));
	}
```

⚠ **I due numeri `1920, 1080` sono scritti a mano, ed e' un debito dichiarato**: sono la tela che la
pagina della fase 1 gia' annuncia (`PIANO.md` fase 1, *«tela 1920×1080»*), ma stanno in due posti. Chi
innesta li leghi a una costante sola, o a un'opzione della riga di comando — e allora la misura del
desktop diventa una decisione, non una coincidenza.

---

## 7. ⛔ Le certificazioni che questa modifica invalida

**Oggi, con `src/` cosi' com'e': nessuna.** `sessione.c` non e' compilato dentro `remotix`, non cambia
un byte del binario, e non ho toccato nessun file esistente. ⛔ *«Nessuna» e' un fatto, non una
speranza: si legge dal `Makefile`, che non nomina `sessione.c`.*

⛔ **Al momento dell'innesto delle righe di §6, invece, scadono tutte quelle che ricostruiscono e
misurano il prodotto** — perche' il binario cambia, e `banchi/attrezzi-allinea-prodotto.sh` enumera
`src/` **intero**, quindi i due file nuovi partono da soli verso il server:

| | quali |
|---|---|
| **le nove `[ricostruisce]` del catalogo** | **B2, B3, B5, B6, B7, B8, B10, P5, P5R** (`01-b12-guasti.py --elenco`) |
| **e quelle misurate sul server acceso** | tutto cio' che poggia sui processi delle porte **7448** e **7501**: vanno ricostruiti e riaccesi, o si misura il server di ieri credendo di misurare quello di oggi (`attrezzi-allinea-prodotto.sh`, riquadro in testa) |
| **non toccate** | **B4, B9, B11, B13, C2, P1** — leggeri, di scena o di certificati: non passano dal binario. ⚠ B13 poggia su `rcp.c`, che non ho sfiorato |

⚠ *«Scaduta» non e' «fallita»*, e non e' nemmeno «pulita». ⛔ **E non le ho rincorse**, come il mandato
chiede: il conto lo rifa' chi innesta, **dopo** aver innestato, o rifarebbe due volte lo stesso giro.

---

## 8. Che cosa resta `[?]`

| # | la `[?]` | perche' resta |
|---|---|---|
| 1 | ⛔ **Dove gira `sessione.c` nel prodotto vero** | il server di prova gira **dentro il contenitore**, dove non ci sono `systemd --user`, `$XDG_RUNTIME_DIR` d'utente ne' il bus di sessione. Il modulo e' stato provato **sull'host**, che e' dove la sessione vive. ⇒ O il server esce dal contenitore, o `sessione_assicura()` uscira' sempre **5** dichiarandolo. **E' una decisione del coordinatore, non una riga di codice** |
| 2 | **Se `--virtual-monitor` regga un cambio di misura a caldo** | `ensure_virtual_monitor` esce prima se la misura non cambia (`STUDI.md` §gnome §8.2). Il codice **non ci prova**: dichiara e prosegue. Se la fase 6 vorra' il ridimensionamento, e' li' che si misura |
| 3 | ⚠ **Se la grazia di 5 000 ms basti su una macchina piu' lenta** | `[R]` il monitor lo crea `meta-context-main.c:592-597` **prima** che `DisplayConfig` risponda, quindi il fatto basterebbe gia'; la grazia e' prudenza sopra quel fatto. Sbaglia dalla parte che si vede (un falso «nera»), non da quella che si nasconde |
| 4 | **Se la sessione **con** monitor sia altrettanto fragile allo `Shell.Screenshot`** | ereditata da F2.1, e **non riprovata di proposito**: non rifaccio cadere la sessione per una curiosita' |
| 5 | ⚠ **`XDG_SESSION_ID` quando REMOTIX girera' come unita' di sistema** | oggi non si passa, e la scena sana non la porta. Da riguardare quando il server nasce da systemd invece che da una shell |
| 6 | **Che cosa fa il prodotto se la sessione e' `MISURA_ALTRA` per davvero** | il ramo c'e' ed e' dichiarato, ma **non e' stato fatto succedere**: il banco di F2.1 quel numero lo raggiunge sulle scene registrate, il mio no |

---

## 9. Le cuciture

### Che cosa P2.1 **promette**

| a chi | che cosa |
|---|---|
| **F2.2 (cattura)** | ⭐ **il monitor per NOME, dal prodotto**: `sessione_stato(l, a, &monitor)` riempie `connettore` (`Meta-0`), `fornitore`, `prodotto` (`MetaVirtualMonitor`), `seriale`, misura e refresh, **e `quanti` ce n'erano in tutto**. ⛔ Non deducetelo e non sceglietelo per misura: il 12 agosto ce n'erano due identici sulla misura |
| **F2.2 … F2.6** | `SESSIONE_PRODOTTO_CHIESTO` e' una costante di `sessione.h`: chi confronta quel nome lo prende da li', non lo ricopia |
| **tutte** | `sessione_bus()` — l'unico modo lecito di prendere il bus di sessione. ⛔ Chi chiama `g_bus_get_sync(G_BUS_TYPE_SESSION, …)` si prende «exit-on-close» e muore al primo logout |
| **tutte** | i numeri di `SessioneStato` **sono** le uscite 0-5 del banco di F2.1: un registro del prodotto e un'uscita del banco si leggono con lo stesso dizionario |
| **al coordinatore** | ⭐ **I7 e' pagato**: `bash banchi/02-sessione-costruisci.sh certifica` lo rifa' in due minuti, e la scena in cui gira e' *«la configurazione ha perso la riga»* |

### Che cosa P2.1 **chiede**

| a chi | che cosa |
|---|---|
| ⛔ **al coordinatore** | le righe di §6, **una volta sola** per `gio-2.0` (serve anche a F2.2), e il conto delle certificazioni scadute **dopo** l'innesto |
| ⛔ **al coordinatore** | la decisione della `[?]` 1: **dove gira il server**. Finche' gira nel contenitore, questo anello non ha una sessione da assicurare |
| ⚠ **al coordinatore** | i due numeri `1920, 1080` di §6.3 vanno legati alla tela che la pagina annuncia, o fra due settimane saranno tre posti |
| ⚠ **a F2.2 … F2.6** | `banchi/02-sessione-guardia.sh` resta la riga da mettere davanti alle vostre misure. ⭐ E adesso c'e' un secondo modo, dal prodotto: `02-sessione-prova stato` esce **0** solo se c'e' un monitor `MetaVirtualMonitor` della misura chiesta |
| ⚠ **a chi eredita la macchina** | l'ho lasciata **sana e pulita**: `gnome-shell 276233` con `--virtual-monitor 1920x1080`, un monitor `Meta-0`, **nessun drop-in di banco** in `$XDG_RUNTIME_DIR`, e quello persistente di `/etc` intatto. 7448 e 7501: due ascoltatori ciascuno |

---

## 10. ⛔ La riga per il catalogo delle certificazioni

*Nella forma di `banchi/01-b12-guasti.py`. Gli attesi sono scritti **prima** del giro, in testa a
`ciclo()`.*

```python
{
    "nome":            "P2.1-monitor-nel-programma",
    "comando":         "bash banchi/02-sessione-costruisci.sh certifica",
    "dove":            "da CHUWI; il ciclo gira su NIC-OS host (non nel contenitore)",
    "atteso_sano":     0,      # SANA: Meta-0 / MetaVirtualMonitor / 1920x1080@60
    "guasto":          "ramo-gnome-di-v1",
    "guasto_dettaglio": "su una COPIA di src/sessione.c si rimette il corto circuito di "
                        "v1/remotix-c/src/sessione.c:671 — `if (0 && !scrivi_dropin(...))`, "
                        "cioe' `tipo == COMPOSITORE_KWIN &&` sul ramo GNOME.  Il prodotto "
                        "non scrive nessun drop-in, e la sessione nasce nera",
    "atteso_guasto":   1,      # NERA: ZERO MONITOR
    "marca_guasto":    "NERA: ZERO MONITOR",
    "atteso_risanato": 0,
    "rimette_a_posto": True,   # scena_via(): toglie zy- e zz-, e daemon-reload
    "scena":           "⛔ la CONFIGURAZIONE non chiede il monitor in nessuno dei tre giri: "
                       "un drop-in `zy-scena-provisioning-perduto.conf` rimette l'ExecStart "
                       "com'era fino al 12 agosto.  E' l'unico modo in cui la differenza "
                       "fra 0 e 1 sia una riga di PRODOTTO (I7) e non una di configurazione",
    "controllo_positivo": "tre giudici indipendenti per ogni giro — il prodotto su se stesso, "
                          "02-sessione-stato.py dal bus (che porta i suoi: «layout-mode» e "
                          "GetIdletime che cresce) e 02-sessione-guardia.sh; e le impronte "
                          "dei due giudici confrontate con quelle del deposito",
    "guardia":         "conta gli ascoltatori su 7448 e 7501 prima e dopo: se calano, rosso",
    "lucchetto":       7511,
    "avvertenza":      "⛔ La scena si rimette PRIMA DI OGNI GIRO.  Nella prima stesura si "
                       "imponeva una volta sola, il drop-in scritto dal prodotto nel giro "
                       "sano sopravviveva al giro dopo, e il giro guasto usciva VERDE col "
                       "guasto vivo [M] 12 ago 2026 18:27",
},
```

---

## Il giudizio dell'utente

*Da riempire. ⛔ E qui il metro non e' un numero di questo rapporto: e' che **il desktop si veda**
dentro la scheda del browser — e finche' la catena non arriva alla tela, quel che questo anello puo'
dimostrare e' soltanto che **c'e' qualcosa da catturare** (`PIANO.md` §0.3 punto 3, invariante I8).*
