# Gli esiti della sonda del browser — S1b · S2 · S3a · S5 · S6 · S7

Notte del **10 agosto 2026**. Sei righe della tabella «La sonda» di
`fasi/01-filo-nudo.md`, e le due `[?]` di `RCP.md` che due di loro tengono aperte.

> ## ⛔ La divisione, prima di ogni numero
>
> Tre di queste misure pretendono ferro che quella notte non era collegato: il telefono Android, il
> DeX, una rete LTE. **Non sono state eseguite, e non sono state dedotte**: dedurle sarebbe la forma
> **E5**, e un `[M]` falso costa più di una misura mancante. Per quelle tre c'è **il banco pronto a
> girare**, con i controlli che i rapporti prescrivono e la procedura — così la misura costa un
> pomeriggio il giorno che il dispositivo c'è.

| | Eseguita? | Esito |
|---|---|---|
> ## ⛔ E la seconda divisione, aggiunta l'11 agosto 2026: quali numeri hanno una provenienza
>
> La revisione avversariale R12 (rilievi **A26**, **A30**, **R12.6**) ha trovato in questo documento
> un numero che **non torna con la propria aritmetica**, uno pubblicato **contro il proprio
> registro**, e uno che **nessun revisore poteva ritrovare**. Sono stati ricontati tutti, uno per uno:
> la tabella completa è in **§0-bis**, e ogni numero qui sotto porta adesso il file in cui vive.
> ⛔ *Un `[M]` senza provenienza è peggio di una riga vuota*, e per una notte qui ce n'è stato uno.

| | Eseguita? | Esito |
|---|---|---|
| **S7** — il segno della rotella | ⭐ **SÌ**, completa; **due controlli su quattro sono nel registro**, due stanno solo nell'uscita a schermo (§0-bis) | `ei_device_scroll_discrete(0, +120)` manda la pagina **verso la fine del documento** ⇒ ⛔ **il server RCP deve invertire l'asse verticale** |
| **S1b** — la durata dell'eccezione | ⏳ **AVVIATA**: giorno 0 preso, orologio in moto | Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z**. ⛔ **NON** «604 800 s esatti dalla concessione»: dai due numeri che questo documento pubblica escono **604 786,889 s** (§2.2-bis). Il numero sul campo si legge fra sette giorni |
| **S5** — la tela dichiarata | ⚠ **metà**: il browser del portatile sì, **il DeX no** | ⛔ **i due motori NON concordano**: Firefox 140 dà la tela invariante, **Chrome 151 la fa crescere a 2880×1620** |
| **S2** — HEVC Main10 in hardware | ⛔ **NO** — manca il **telefono Android** e il **PC per `chrome://inspect`**; e le cinque sequenze sono della fase 2 | resta `[?]`. Banco pronto: `01-s2-pagina.html` |
| **S3a** — la tastiera nei tre stati | ⛔ **NO** — manca il **DeX** | resta `[?]`. Banco pronto: `01-s3a-pagina.html` |
| **S6** — il carico utile di un datagram | ⛔ **NO** — manca **una LTE vera** (e un server che faccia l'eco dei datagram) | resta `[?]`. Banco pronto: `01-s6-pagina.html` |

---

# 0-bis. ⛔ La ricontata: quali numeri sopravvivono e quali no

*Fatta l'11 agosto 2026 sui rilievi A26, A30 e R12.6, ricalcolando ogni numero **dai file su disco**
e non da questo documento. ⛔ Dove il file non c'era, è stato portato qui (S7) o il numero è stato
declassato (S1b). ⛔ Nessun numero è stato arrotondato per farlo tornare.*

| Numero | Dove vive | Sopravvive? |
|---|---|---|
| S1b — impronta `DPJnKQDqIsekIEk9PJqURz01cvbwgJ8EH/Hf7g97fl8=` | `banchi/01-s1b-stato.jsonl` riga 1 | ✅ **sì**, `[M]`, ed è nelle tre righe del registro |
| S1b — Chrome **151.0.7922.108** | idem | ✅ **sì**, `[M]` |
| S1b — giorno 0 **2026-08-10T21:10:01Z** | idem, campo `ora` | ⚠ **sì, ma non è quel che dice**: è l'istante in cui la riga è stata **scritta**, cioè dopo due visite da ~28 s l'una. **Non** è l'istante del clic |
| S1b — il valore grezzo **13431474587889370** | idem, dentro la stringa `"valore non interpretabile: '…'"` | ✅ **sì**: il numero c'è su disco, dentro la riga che dice di non averlo capito |
| S1b — scadenza **2026-08-17T21:09:47.889Z** | ⛔ **in nessun file** | ⚠ **la conversione è giusta** (ricalcolata: `13431474587889370/1e6 − 11644473600` → `2026-08-17T21:09:47.889370+00:00`, `[M]`), **ma nessun giro l'ha scritta**. È una decodifica fatta a mano su un valore che sì è su disco. Da `[M]` a **`[M]` sul grezzo + conversione dichiarata** |
| S1b — «**604 800 s esatti** dalla concessione», ⛔ scritto **due volte** | — | ⛔ **NO, NON SOPRAVVIVE.** Fra i due numeri che questo documento pubblica ci sono **604 786,889 s**. Mancano **13,111 s**, e «esatti» era falso in tutt'e due i punti. Vedi §2.2-bis |
| S1b — la chiave `https://192.168.0.2:443,*` e il blocco `cert_exceptions_map` | ⛔ **in nessun file**: trascritti a mano dall'uscita a schermo del giro «avvia» | ⚠ **`[M]` a vista, senza provenienza su disco.** Coerenti col grezzo (`decision_expiration_time` = lo stesso 13431474587889370), ma un revisore non li può ritrovare. ⭐ Da adesso `01-s1b-eccezione.sh` li registra a ogni giro «oggi» |
| S7 — `deltaY` **+114 / −114**, `wheelDeltaY` **−342 / +342**, `deltaMode` **0** | `banchi/01-s7-esiti.jsonl` — ⭐ **portato in questo albero l'11 agosto** (prima era solo sul server: rilievo A30) | ✅ **sì**, `[M]`, e **due volte in due giri distinti** (`7sd0u7jv`, `oq7jqrdv`) |
| S7 — i due strumenti concordano (`deltaY` e `scrollY`) | idem, campi `deltaY` e `scorrimento` | ✅ **sì**: `+114 → scorrimento +114`, `−114 → −114`, in tutt'e due i giri |
| S7 — la scena: **Firefox/140.0**, schermo **1920×1080**, `dpr` 1, partenza **8000 px** | idem, campi `motore`, `schermo`, `dpr`, `base` | ✅ **sì**, riga per riga |
| S7 — **2026-08-10 20:59 UTC** | idem, campo `ora` | ✅ **sì**: 20:59:27 → 20:59:57 |
| S7 — «**`natural-scroll` nei due stati**, e il segno non cambia» | ⚠ i **due giri** ci sono e danno lo stesso segno; ⛔ **quale giro fosse quale stato NON è nel registro** | ⚠ **metà**: `[M]` che due giri indipendenti danno lo stesso segno; `[?]` che fossero i due stati di `natural-scroll`. Quell'etichetta stava solo nell'uscita a schermo del lanciatore, che non è stata tenuta |
| S7 — «`ei_device_scroll_delta` ha lo stesso verso» | ⛔ **nessuna riga del registro lo porta** | ⛔ **NO**: non è ritrovabile. Resta come cosa vista, non come misura consegnata |
| S7 — «il silenzio: dieci secondi senza iniettare, nessuno scatto» | è un'**assenza** di righe fra i timbri | ⚠ **coerente col registro, non provato da lui**: un'assenza senza denominatore è quel che `LEZIONI.md` §1.9 insegna a non leggere come un fatto |
| S5 — Chrome 100 % **1920×1080**, 150 % **2880×1620**, `dpr` 1 → 1,5 | `banchi/01-s5-esiti.jsonl` | ✅ **sì**, e **due volte** (23:13 e 23:14) |
| S5 — Firefox 150 %: `screen` **1280×720**, tela **1920×1080** | idem | ✅ **sì**, e due volte |
| S5 — «`xdpyinfo` fuori dal browser dice 1920×1080» | ⛔ **in nessun file**: sta nell'uscita a schermo di `01-s5-tela.sh` | ⚠ **senza provenienza su disco**. Il campo `schermo_l/schermo_a` del registro è quel che dichiara **il browser**, non `xdpyinfo` |

⛔ **Il conto**: dei numeri che questo documento pubblicava, **uno era falso** («604 800 esatti»),
**due erano senza provenienza** (la scadenza decodificata e la chiave del `Preferences`), **uno non
era ritrovabile da nessuna parte** (l'intero registro di S7), e **tre** vivevano solo nell'uscita a
schermo di un lanciatore. ⭐ Tutti gli altri hanno retto la ricontata, riga per riga.

---

# 1. ⭐ S7 — da che parte gira la rotella · `RCP.md` §7.3

## 1.1 Il numero, con la scena accanto

| | |
|---|---|
| **misurato** | `ei_device_scroll_discrete(0, **+120**)` → l'evento `wheel` della pagina porta **`deltaY = +114`** (`deltaMode = 0`, pixel; `wheelDeltaY = −342`) e la pagina **scende di 114 px**.<br>`ei_device_scroll_discrete(0, **−120**)` → **`deltaY = −114`**, la pagina **sale di 114 px**. |
| **la scena** | server **192.168.0.2**, sessione GNOME senza monitor avviata da `banchi/00-sessione-gnome.sh`, `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; la pagina in **Firefox 140.13.0esr** (`rv:140.0 … Firefox/140.0`) in `--kiosk` a schermo pieno sul monitor virtuale |
| **quando** | 2026-08-10, **20:59:27 → 20:59:57 UTC** · registro `banchi/01-s7-esiti.jsonl` |
| **dove si ricontrolla** | ⭐ **il registro è in questo albero** dall'11 agosto 2026. ⛔ Fino a quel giorno stava **solo** sul server (`/media/REMOTIX/src/`) e non era in questa copia: il rilievo **A30** dice che il numero che chiude la `[?]` di `RCP.md` §7.3 — la sola misura dichiarata completa della notte — non aveva, da questa parte, nessun dato a cui un revisore potesse risalire, e che la scena (la sessione GNOME col monitor virtuale) era già stata smontata. ⚠ Il numero non era contestato: era **non riverificabile**, che è la ragione per cui i registri si tengono |

## 1.2 ⛔ La lettura, e da dove viene il segno

`deltaY` positivo vuol dire che il contenuto va **verso la fine** del documento: è quel che succede
quando l'utente gira la rotella **in giù**. `RCP.md` §7.3 fissa l'altra metà — *«il client manda
`+120` perché l'utente ha girato la rotella **in su**»*. Le due convenzioni sono **opposte**:

> ⛔ **Il server RCP deve invertire il segno dell'asse verticale** prima di passarlo a
> `ei_device_scroll_discrete`. Iniettando il valore così com'è, lo schermo remoto scorrerebbe al
> contrario per ogni utente.

⭐ E il confronto è onesto perché i due lati parlano **la stessa lingua**: `deltaY` è esattamente la
grandezza che il client legge quando l'utente gira la rotella vera. Non si confrontano due mondi, si
confronta due volte lo stesso strumento.

⚠ **Un fatto in più, che serve a chi scriverà il codice**: uno scatto (120 unità) si traduce in
**114 pixel** su Firefox, cioè tre righe. È il fattore di conversione di Mutter+Firefox, non una
costante del protocollo.

## 1.3 I quattro controlli, e tre sono di quelli che dicono *no*

*⛔ E accanto a ogni riga, dall'11 agosto 2026, **dove si ricontrolla**: due dei quattro sono nel
registro, due stanno soltanto nell'uscita a schermo del lanciatore — che non è stata tenuta (§0-bis).*

| Controllo | Esito | Ritrovabile? |
|---|---|---|
| ⛔ **il segno opposto**: si inietta anche `−120`, e la pagina deve andare **dall'altra parte** | ✅ `+120 → +114`, `−120 → −114`. Si sta misurando **il segno**, non «che qualcosa si muove» | ✅ `01-s7-esiti.jsonl`, righe `SCATTO` dei giri `7sd0u7jv` e `oq7jqrdv` |
| ⛔ **`natural-scroll` nei due stati** (mouse *e* touchpad), ⛔ **con il dispositivo rifatto da capo a ogni stato** | ✅ **il segno NON cambia**: `+120 → +114` in tutt'e due i giri. Il numero è una proprietà del percorso, **non della scrivania di prova** — la forma **E11** non si applica | ⚠ **metà**: i due giri ci sono e concordano; ⛔ **quale giro fosse quale stato non è nel registro**. `[?]` sull'etichetta, `[M]` sulla concordanza |
| ⛔ **il silenzio**: dieci secondi senza iniettare niente | ✅ nessuno scatto registrato | ⚠ è un'**assenza** di righe: coerente coi timbri, non provata da loro |
| ⛔ **i due strumenti devono concordare**: l'evento `wheel` e lo spostamento vero di `scrollY` | ✅ concordano su tutte le prove | ✅ campi `deltaY` e `scorrimento` di ogni riga `SCATTO`: `+114/+114`, `−114/−114` |
| ⭐ *in più* — `ei_device_scroll_delta` ha lo stesso verso di `ei_device_scroll_discrete`? | ✅ **sì** (`liscio 0 +120 → deltaY +114`). Il prodotto usa gli scatti, ma se le due chiamate avessero segni opposti il difetto nascerebbe muto il giorno che qualcuno usasse l'altra | ⛔ **NO: nessuna riga del registro lo porta.** Resta una cosa vista a schermo, non una misura consegnata |

E due **controlli positivi sullo strumento**, prima di tutto: la pagina dichiara di essersi messa a
8 000 px dal bordo (se il documento non scorresse, ogni «non si è mossa» che segue non vorrebbe dire
niente) e dichiara di vedere uno schermo **1920×1080**, cioè il monitor virtuale chiesto.

## 1.4 ⛔ Che cosa `libei` NON dice, ed è il motivo per cui S7 esiste

`libei.h` 1.3.901, documentazione di `ei_device_scroll_discrete` letta il 10 agosto:

> *«A discrete scroll event is based logical scroll units (equivalent to one mouse wheel click). The
> value for one scroll unit is 120 … @param y The y scroll distance in fractions or multiples of
> 120»*

**Dichiara la grandezza e non il verso.** Non è una lacuna della nostra lettura: la convenzione non
sta nell'API, sta nel compositore. È precisamente perché `RCP.md` §7.3 aveva ragione a tenere la riga
`[?]` invece di deciderla.

## 1.5 Che cosa resta `[?]`

⚠ **La misura è su Mutter, e §7.3 vincola cinque desktop.** Se `libei` normalizza, il numero vale
ovunque; se normalizza il compositore, la fase 10 troverà un segno diverso su KWin. **Non è chiuso da
questa misura**, e il banco è rieseguibile su KWin senza cambiare una riga della pagina.

---

# 2. ⏳ S1b — quanto dura l'eccezione su Chrome

## 2.1 ⛔ Prima di tutto: il rimando di `fasi/01-filo-nudo.md` è sbagliato

Il documento di fase manda a **`S1 §4.2 P5`**. ⛔ **P5 non è questa prova**: è la prova del *contesto
sicuro* (Service Worker, keyboard lock, appunti, pointer lock, `isSecureContext`). **Nel rapporto S1
non esiste nessuna prova di banco sulla durata**: i sette giorni sono **solo sorgente letto** (§3.1),
mai messi a banco — e la sola persistenza messa a banco è quella di **Safari** (§4.3).

⇒ Il banco qui descritto è **nuovo**, e il rimando in `fasi/01-filo-nudo.md` va corretto: non c'è una
procedura da seguire, ce n'era una da scrivere.

## 2.2 Il giorno 0, misurato

| | |
|---|---|
| **quando** | **2026-08-10T21:10:01Z** — l'orologio parte qui |
| **il browser** | **Google Chrome 151.0.7922.108** (`Chrome/151.0.0.0` nella stringa d'agente), profilo persistente in `~/.remotix-s1b/profilo`, su uno schermo finto `Xvfb :77 1280x1024x24` |
| **il sito** | `https://192.168.0.2:7452/01-s1b-pagina.html`, certificato **ECDSA P-256, 3650 giorni, SAN `IP Address:192.168.0.2`** — ⛔ **non** `localhost` (Chrome ha una corsia riservata) e ⛔ **non** in navigazione privata (è un altro deposito) |
| **l'impronta della pagina** | `DPJnKQDqIsekIEk9PJqURz01cvbwgJ8EH/Hf7g97fl8=` (SHA-256 del DER), letta **dal filo** con `openssl s_client`, non dal file sul server |
| **la scadenza che Chrome si è segnato** | il valore grezzo **`13431474587889370`** µs dal 1601, che decodificato dà **2026-08-17T21:09:47.889Z**. ⛔ Il grezzo è su disco, la decodifica **non lo è**: vedi §2.2-bis, dove il numero che questo documento pubblicava da questa riga è stato rifatto |

⭐ **Due cose che il rapporto S1 dava per lettura di sorgente, e adesso sono viste sul campo**, dal
`Preferences` del profilo:

```
chiave : https://192.168.0.2:443,*
valore : {"cert_exceptions_map": {"-202DPJnKQDqIsekIEk9PJqURz01cvbwgJ8EH/Hf7g97fl8=": 1},
          "decision_expiration_time": "13431474587889370", "version": 1}
```

> ⚠ **E da dove viene questo blocco**, perché è la domanda che nessuno si era fatto: è **trascritto a
> mano dall'uscita a schermo** del giro «avvia», e **non sta in nessun file**. `banchi/01-s1b-stato.jsonl`
> ne porta soltanto il `decision_expiration_time`, e ce lo porta dentro la stringa
> `"valore non interpretabile: '13431474587889370'"`. ⛔ Un revisore non può ritrovare questa chiave da
> nessuna parte, ed è la stessa forma del numero di S7 (§0-bis). ⭐ **Curato nello strumento**: da
> adesso `01-s1b-eccezione.sh` registra a ogni giro «oggi» sia la scadenza sia la chiave, così dal
> prossimo giro la riga ha una provenienza — senza dover rifare il giro «avvia», che azzererebbe
> l'orologio dei sette giorni.

| | |
|---|---|
| **l'indicizzazione è per HOST, senza porta** | la chiave dice **`:443`** mentre il sito risponde su **7452**. `[R]` diventa `[M]` — ⚠ con la provenienza dichiarata qui sopra |
| **la chiave porta il codice d'errore e l'impronta** | `-202` (`ERR_CERT_AUTHORITY_INVALID`) seguito **dalla nostra impronta esatta**. Un certificato che cambia **non è coperto**, ed è il motivo per cui il controllo qui sotto esiste |
| **la scadenza** | `13431474587889370` µs dal 1601 → 2026-08-17T21:09:47.889Z. ⚠ È un **secondo strumento** sullo stesso fatto, non la stessa misura: dice *«che cosa Chrome ha deciso»*, non *«la pagina si apre ancora»* |

## 2.2-bis ⛔ Il numero che non tornava con la propria aritmetica

*Rilievi **A26** e **R12.6**, 11 agosto 2026. Questa sezione sta qui e non in fondo perché è il posto
in cui il numero sbagliato si leggeva.*

**Che cosa diceva questo documento**, in due punti: *«scade il 2026-08-17T21:09:47Z, cioè **604 800 s
esatti** dalla concessione»*. **Rifatto il conto sui due numeri che il documento stesso pubblica:**

```
concessione (riga del registro)   2026-08-10T21:10:01+00:00
scadenza    (13431474587889370 µs dal 1601, decodificata)
                                  2026-08-17T21:09:47.889370+00:00
differenza                        604 786,889 s      ⛔  non 604 800
sette giorni esatti sarebbero     2026-08-17T21:10:01Z  ⛔  non 21:09:47,889Z
```

⛔ **Mancano 13,111 s**, e la parola «esatti» compariva **due volte**. Un numero che non torna con la
propria aritmetica è un numero che nessuno ha ricontato.

⛔ **E non si arrotonda: si rimisura, oppure si dichiara che non è stato misurato.** Qui non si può
rimisurare — il giro «avvia» non si rifà senza far ripartire l'orologio da capo — quindi si dichiara,
e si dichiara anche la ragione dello scarto:

| | |
|---|---|
| ✅ **`[M]`, e regge** | Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z**. Il valore grezzo è su disco; la conversione (`/1e6 − 11644473600`) è stata **ricalcolata due volte** l'11 agosto |
| ⚠ **`[?]`, ed è una deduzione** | che siano **604 800 s esatti dal clic**. Lo sarebbero se il clic fosse avvenuto alle **21:09:47,889**, cioè **13,1 s prima** della riga di registro. È plausibile — la riga si scrive alla fine del giro, dopo due visite da ~28 s l'una — ⛔ **ma l'istante del clic non è stato registrato da nessuno**, e questa lettura non era scritta in nessun punto del documento |
| ⛔ **quel che NON è** | la riga `"ora"` del registro **non è** l'istante della concessione: è l'istante in cui la riga è stata **scritta**. Chiamarla «la concessione» è quel che faceva tornare il conto a occhio e non sulla carta |

⚠ **E la seconda metà del rilievo, che è la più netta**: il documento citava come provenienza il
registro dello strumento, e il registro **dice il contrario**. `banchi/01-s1b-stato.jsonl` riga 1:

```json
"scadenza_memorizzata": "valore non interpretabile: '13431474587889370'"
```

⭐ **Delle due letture che R12.6 lasciava aperte, è vera la prima, e adesso è dimostrata.** Il dato
grezzo è stato prodotto da uno strumento **anteriore** alla cura, e non «la cura c'è e non ha
funzionato». La prova sta nella forma della stringa: il codice di oggi, quando non riesce a
convertire, scrive `valore non interpretabile: <valore> (<errore>)` — **con l'errore fra parentesi**.
La riga su disco **non ha le parentesi**, cioè è uscita da una versione precedente del messaggio. E
il messaggio d'errore che il codice di oggi produrrebbe su quel numero letto come tempo Unix è
`year 425628455 is out of range` (`[M]`, verificato l'11 agosto): la conversione di oggi, su quel
numero, **non fallisce affatto**.

⛔ **Che cosa è stato curato nello strumento**: `registra` nel ramo `oggi` non portava il campo
`scadenza_memorizzata` **affatto**, quindi nessun giro successivo poteva rimettere il numero su
disco. Adesso lo porta, insieme alla chiave. Dal primo giro «oggi» dell'11 agosto in poi, questa riga
ha una provenienza che si può aprire con un editore di testo.

## 2.3 I controlli, e girano a ogni giro — ⛔ da tre sono diventati **quattro**

| Controllo | Esito il giorno 0 |
|---|---|
| ⛔ **l'impronta letta dal filo dev'essere quella del giorno 0** — senza, un certificato rigenerato fa scrivere «l'eccezione è durata quattro giorni» (R3.15) | ✅ stessa impronta |
| ⛔ **un profilo NUOVO deve vedere l'avviso** — è «come apparirebbe il caso opposto» | ✅ un profilo appena nato **non arriva alla pagina**: lo strumento distingue |
| ⛔ **il sito dev'essere vivo** — altrimenti «non si apre» non è «è scaduta», è «non c'è nessuno» | ✅ certificato preso dal filo prima di ogni verdetto |
| ⭐ **il CANALE DI LETTURA dev'essere certificato** — *nuovo, 11 agosto 2026, rilievo **A27*** | dal primo giro dell'11 agosto in poi |

> ### ⛔ Il quarto controllo, e perché è il più importante dei quattro
>
> `visita()` rispondeva **NO** in ogni caso che non fosse un riscontro: `ssh` caduto, credenziali
> rifiutate, `01-s1b-visite.jsonl` cancellato o rinominato, il sito acceso da un percorso diverso.
> ⛔ **E il secondo controllo — «un profilo nuovo deve NON arrivare» — legge lo stesso canale**:
> a canale rotto il profilo nuovo dà NO, e quel controllo **si dichiara passato da sé**.
>
> Il giro che ne usciva stampava, in quest'ordine: *«un profilo appena nato NON arriva alla pagina:
> lo strumento distingue»*, poi *«la pagina NON si apre»*, e chiudeva con
> **`OK  a N giorni l'eccezione NON c'è più: è questo il numero di S1b»`** — ⛔ **il numero della
> misura, in verde, da uno strumento muto.** Ed è un orologio da sette giorni: se sbaglia, se ne
> accorge qualcuno **fra una settimana**.
>
> ⭐ **La cura**: prima di ogni verdetto si scrive una riga nel registro passando dalla **stessa
> porta della pagina** (`POST /esito`, che è quel che fa `sendBeacon`) e la si rilegge con lo
> **stesso `ssh`**. Se il token torna, i tre pezzi su cui il verdetto poggia — il server che scrive,
> `ssh` che legge, il `grep` che trova — funzionano; se non torna, **nessun verdetto si dà** e lo
> stato d'uscita è 6.
> ⚠ E si dichiara che cosa questo controllo **non** prova: non prova che un *browser* arrivi alla
> pagina (lì c'è di mezzo l'interstiziale, che è quel che si misura). Prova il canale di lettura,
> che è quello su cui poggiava il verdetto e che nessun altro controllo guardava.
>
> ⛔ **E `visita()` adesso ha tre esiti, non due**: `SI` · `NO` · `IGNOTO`. Il comando remoto si fa
> stampare il proprio stato d'uscita (`grep -c`: 0 trovato · 1 non trovato · ≥2 non ho potuto
> leggere), e se il marcatore non torna affatto il comando non è nemmeno arrivato in fondo — che è
> un terzo fatto ancora. Verificato l'11 agosto sui quattro casi: trovato → `SI`, assente → `NO`,
> registro illeggibile → `IGNOTO`, `ssh` morto → `IGNOTO` (`[M]`).

⛔ **E `--ignore-certificate-errors` non compare in nessuna riga del banco**: sarebbe il modo più
rapido di far aprire la pagina e il modo più sicuro di non misurare più niente. ⚠ Il `curl -k` del
quarto controllo non è quella cosa: non tocca nessun profilo e non concede nessuna eccezione — è lo
strumento che si certifica, non il fatto che si misura.

## 2.4 Come si riprende, e quando

```
bash banchi/01-s1b-eccezione.sh oggi     # una volta al giorno, fino al 18 agosto
bash banchi/01-s1b-eccezione.sh stato    # tutti i giri finora
```

Ogni giro accende e spegne il sito da sé, rifà i **quattro** controlli e appende una riga a
`banchi/01-s1b-stato.jsonl` con **la versione esatta di Chrome**, la scadenza che Chrome si è
segnato e la chiave del `Preferences`. Il numero di S1b è **il giorno in cui `eccezione_regge` passa
da `SI` a `NO`** con il profilo nuovo ancora bloccato ⛔ **e il canale di lettura certificato**.

⛔ **Gli stati d'uscita, e sono sei**: `0` giro fatto · `2` uso sbagliato · `3` il sito o lo schermo
non ci sono · `4` l'impronta è cambiata (misura da rifare) · `5` la concessione non è riuscita ·
⭐ `6` **niente verdetto**: il canale non è certificato, o il controllo che dice *no* non è passato,
o zero controlli approvati. ⚠ Il `6` è nato l'11 agosto: prima quei casi uscivano **0**.

⚠ **E una scena che il banco adesso verifica invece di supporre** (rilievo A29): lo schermo finto
`:77`. Se esiste già, se ne legge la **geometria** con `xdpyinfo` e si pretende `1280x1024`.
`01-s5-tela.sh` usa lo **stesso numero di schermo** a `1920x1080`: un suo giro rimasto appeso
lasciava lì una scena di un'altra misura, e la finestra di Chrome — che `xdotool` deve cliccare a
**coordinate fisse** (`mousemove 640 500`) — sarebbe nata dove il clic non arriva.

⛔ **Che cosa può rompere l'orologio, e va detto a chi lavora sulla stessa macchina**: rigenerare
`/media/REMOTIX/s1b-certificato/s1b-pagina.pem`, cancellare `~/.remotix-s1b/`, o far cadere la data
del server. I primi due li vede il controllo dell'impronta; il terzo no.

## 2.5 Che cosa resta `[?]`

- **il numero sul campo**: fino al 17 agosto S1b resta *«a N giorni l'eccezione c'è ancora»*. Il
  `[R]` dei sette giorni **non è ancora confermato dal comportamento**, solo dalla contabilità di
  Chrome.
- **Firefox e Safari**: questo banco misura **Chrome**. Firefox tiene l'eccezione per `host:porta` in
  un elenco visibile nelle impostazioni (S1 §4.3) e non ha la stessa scadenza; non è misurato.

---

# 3. ⚠ S5 — la tela che il client dichiara · metà misurata

## 3.1 I numeri, con la scena accanto

Schermo: **Xvfb 1920×1080×24** (dichiarato: non è il pannello del portatile), risoluzione letta
**fuori dal browser** con `xdpyinfo`: **1920×1080**. Misura ripetuta **due volte**, identica.

| Motore | zoom | `screen` | `devicePixelRatio` | **tela dichiarata** |
|---|---|---|---|---|
| **Google Chrome 151.0.7922.108** | 100 % | 1920×1080 | 1 | **1920×1080** |
| | 150 % | **1920×1080** | 1,5 | ⛔ **2880×1620** |
| **Firefox 140.13.0esr** | 100 % | 1920×1080 | 1 | **1920×1080** |
| | 150 % | **1280×720** | 1,5 | ✅ **1920×1080** |

## 3.2 ⛔ Il risultato, ed è un difetto di prodotto, non del banco

`SPECIFICHE.md` §6.1-bis calcola la tela come `screen.width × devicePixelRatio`, e `fasi/01-filo-nudo.md`
lo giustifica così: *«`screen.width` cala di un terzo, `devicePixelRatio` sale di un mezzo, il
prodotto resta»*.

> ⛔ **Su Chrome 151 non resta.** `screen.width` **non cambia con lo zoom di pagina**, mentre
> `devicePixelRatio` sale: il prodotto diventa `risoluzione × zoom`. Un client scritto secondo
> §6.1-bis, su un portatile 1920×1080 con lo zoom al 150 %, dichiarerebbe **2880×1620** — una tela
> del 50 % più grande di quella che esiste.

⭐ **È esattamente il difetto che `DECISIONI.md` §5.0-quater temeva**, trovato dal controllo giusto:
il controllo vecchio (*«i due numeri devono differire»*) sarebbe stato **verde su Chrome e rosso su
Firefox**, cioè avrebbe premiato il motore rotto.

⚠ **E la formula non si aggiusta con una riga**: lo zoom di pagina non è leggibile da JavaScript in
modo portabile. La cura è di chi tiene `SPECIFICHE.md` §6.1-bis; qui si consegna il fatto, non la
soluzione. ⛔ Fino ad allora, la tela dichiarata da Chrome **non è quella vera** appena l'utente tocca
lo zoom.

## 3.3 I controlli

| Controllo | Chrome | Firefox |
|---|---|---|
| ⛔ **lo zoom è entrato in vigore davvero** (lo dice `devicePixelRatio`, non il tasto premuto) | ✅ 1 → 1,5 in 3 passi | ✅ 1 → 1,5 in 4 passi |
| ⛔ **la tela a 100 % e a 150 % è la stessa** | ⛔ **NO** — 1920×1080 contro 2880×1620 | ✅ sì |
| ⛔ **coincide con la risoluzione letta fuori dal browser** | ✅ a 100 % | ✅ ai due zoom |
| **la tela dichiarata è pari sui due assi** (invariante I7) | ✅ | ✅ |

⚠ E la terza domanda di S5 — *«l'arrotondamento può produrre un numero dispari?»* — **non è chiudibile
con una misura**: qui i numeri sono pari, e da un pari non si ricava che i dispari non esistano
(`LEZIONI.md` §1.3). La protezione sta nel programma, e la pagina la applica (`Math.floor(x/2)*2`).

## 3.4 Che cosa resta `[?]`

⛔ **La metà su DeX non è stata misurata: manca il dispositivo.** *«Il Chrome del portatile lo fa»*
non dice niente del Chrome del telefono — forma **E10**. La pagina è la stessa
(`01-s5-pagina.html`): il giorno che il DeX c'è, si apre quell'indirizzo e si legge la riga.

---

# 4. ⛔ S2 — HEVC Main10 in hardware · NON ESEGUITA

**Perché no**: mancano **il telefono Android**, **il PC collegato per `chrome://inspect`** (il
controllo C), e ⛔ **le cinque sequenze di prova da `hevc_vaapi`**, che dipendono dal codificatore
della **fase 2**.

⛔ **Non è stata dedotta da nessuna prova fatta qui**, e non poteva esserlo: su Android il
decodificatore vive dietro MediaCodec, ed è precisamente lì che i segnali JavaScript smettono di dire
la verità. L'atteso resta **`[?]`** — ⛔ *non* «sì da Chrome 108», che riguarda il supporto in
WebCodecs e non l'hardware.

## 4.1 Che cosa è pronto

`banchi/01-s2-pagina.html` — servita in HTTPS dal sito di S1b (WebCodecs vuole un contesto sicuro):

| | |
|---|---|
| ⭐ **i due controlli che validano il banco non aspettano la fase 2** | la sequenza **D** (VP9 1080p60) **la costruisce la pagina** con `VideoEncoder`, da rumore che cambia a ogni fotogramma. Controllo **A** (`prefer-software` ⇒ dev'essere software) e **B** (`prefer-hardware` ⇒ dev'essere hardware) si eseguono **il giorno stesso in cui il telefono arriva** |
| ⛔ **e finché A e B non passano, la pagina non pubblica verdetti** | il bottone di HEVC risponde `BANCO_NON_VALIDO`. S2 §4: *«un banco che non ha dimostrato di saper riconoscere un decodificatore software non ha il diritto di dichiarare hardware»* |
| ⛔ **le sequenze HEVC assenti si DICHIARANO** | la pagina scrive `SEQUENZA_ASSENTE` e non misura. Non le sostituisce con una più facile: una sequenza più facile non misura «un po' meno», misura un'altra cosa |
| **le tre letture, non due** | ≥ 90 fps ⇒ hardware · ≤ 30 ⇒ software · **in mezzo ⇒ verdetto sospeso** |
| **la canarina di CPU** | in un worker suo, iterazioni per 100 ms a riposo e sotto carico, rapporto `I₁/I₀` (> 0,85 hw · < 0,4 sw) |
| **il decadimento** | venti campioni a 30 s l'uno per dieci minuti, rapporto finale/iniziale (> 0,9 hw · < 0,6 sw), con l'avvertenza che la scheda deve restare in primo piano o si misura il congelamento invece del calore |
| **la tabella «che cosa avrebbe detto l'API»** | `isConfigSupported`, `decodingInfo().powerEfficient`, `VideoFrame.format`, nuclei, stringa d'agente — raccolti e **mai creduti da soli** |
| ⛔ **il controllo C non è automatizzabile** | `chrome://inspect` → `chrome://media-internals` → la riga `Created MediaCodec <nome>, is_software_codec=<bool>`; nomi `c2.android.` / `omx.google.` ⇒ software. Procedura in `bash banchi/01-s-telefono.sh s2` |

**Verificato stanotte**: la pagina si carica dal sito HTTPS, in contesto sicuro, con `WebCodecs`
presente (`Chrome/151.0.0.0`, 4 nuclei) — cioè il banco **si accende**. ⚠ Questo non è S2: è la prova
che lo strumento parte.

---

# 5. ⛔ S3a — la tastiera nei tre stati · NON ESEGUITA

**Perché no**: manca **il DeX**. E ⛔ una seconda riga di S3 §4.4 non è eseguibile nemmeno con il DeX:
**Firefox ≥ 151** serve per `requestFullscreen({keyboardLock})`, e su questa macchina c'è la **140.13.0esr**
— chi provasse qui misurerebbe **l'assenza della lock** e la scambierebbe per scorciatoie perdute.

## 5.1 Che cosa è pronto, e la cura del difetto che invertiva la misura

`banchi/01-s3a-pagina.html`:

| | |
|---|---|
| ⭐ **il registro è già fuori dalla pagina, sempre** | ogni evento parte per il server con `sendBeacon` **nell'istante in cui succede**, e prima di ogni combinazione parte una riga `ARMATO`. `Ctrl+W` chiude la scheda **dopo** che il registro è al sicuro |
| ⭐ **e i tre stati li classifica il banco, non chi legge** | `bash banchi/01-s-telefono.sh analizza` legge il registro e stampa: `ARMATO`+`keydown`+pagina viva ⇒ **A** · `ARMATO`+`keydown`+`pagehide` ⇒ ⛔ **B, consegnata e riservata** · `ARMATO`+niente+`pagehide` ⇒ **C**. È la distinzione senza la quale il banco *conta* invece di *ascoltare*, e dichiara innocuo il caso pericoloso (R3.11) |
| ⛔ **e da stanotte lo stato d'uscita è quello del CONFRONTO** (rilievo **A28**) | fino all'11 agosto `analizza` **non usciva mai ≠ 0**: trovare uno stato **B** — il caso pericoloso per cui S3a esiste — produceva una riga di testo e **uscita 0**; e se `ssh` non partiva, il `2>/dev/null` buttava la ragione e il testo onesto *«nessuno ha misurato»* usciva **0** lo stesso. Adesso sono quattro esiti: `0` nessuno stato B · `1` almeno uno stato B · `2` **zero combinazioni da giudicare** · `3` il registro non si è potuto leggere. ⭐ Verificato l'11 agosto sui tre casi (`[M]`) |
| **i quattro controlli positivi** | `A` nudo · `Ctrl+Maiusc+A` · appunti in uscita · ⛔ schermo intero **da JavaScript** — perché con `F11` la lock non esiste e non lo dice |
| **le due API della lock** | si chiamano tutt'e due e ⛔ **si prova l'effetto, non l'esistenza**: `requestFullscreen` ignora in silenzio le opzioni che non conosce |
| **le combinazioni, nell'ordine di S3 §4.3** | dalla meno rischiosa alla più rischiosa, ⛔ con `Ctrl+T`, `Ctrl+N`, `Ctrl+W` **ultime** e segnate in rosso |

⛔ **Da verificare prima di misurare, o la misura vale un'altra cosa**: che il DeX sia **almeno
Android 16 QPR1**, e la versione va **scritta accanto al numero**.

**Verificato stanotte**: la pagina si carica in contesto sicuro; su Chrome 151 esistono **tutt'e due**
le API della lock e gli appunti. ⚠ *Esistono*: che blocchino è un'altra domanda, ed è quella che il
banco pone.

---

# 6. ⛔ S6 — quanto porta davvero un datagram · NON ESEGUITA

**Perché no**: manca **una rete LTE vera** (o una VPN a MTU 1400) e il **telefono**. E manca la metà
di server: serve qualcosa che **faccia l'eco dei datagram**.

⛔ **Non è una grandezza del motore**: lo decide il cammino. Perciò `01-s6-pagina.html` **si rifiuta di
misurare senza `?percorso=`** — un numero senza percorso sono due misure diverse sotto la stessa
etichetta (**E2**, R3.22) — e il percorso viaggia dentro **ogni riga** del registro.

| | |
|---|---|
| ⭐ **il controllo positivo, prima di tutto** | un datagram da **64 byte deve tornare**. Se non torna, il server non fa eco o il cammino li butta tutti: in nessuno dei due casi «non torna» misura la *misura*, e la prova **si ferma lì** |
| **il controllo vero** | si spedisce un datagram della misura esatta e ⛔ **si verifica che ARRIVI dall'altra parte**, non che l'API lo accetti: un datagram troppo grande si perde **in silenzio** |
| **la ricerca** | binaria fra 64 e 65535 byte, ⛔ **e il numero trovato si riconferma tre volte** — su un cammino che perde pacchetti una ricerca binaria può scendere per una perdita casuale |
| **il numero che decide** | **972 byte** (PCM 5 ms: 480 campioni × 2 canali × 2 byte + 12 di intestazione, `RCP.md` §5.3). Sotto quella soglia il blocco audio va accorciato |
| ⚠ **`maxDatagramSize` dichiarato dall'API** | si registra e **non si crede**: è la promessa del motore, non la portata del cammino. Se i due numeri divergono, conta quello misurato |

⚠ **E la riga di S6 che va letta prima di misurare**: se quel numero deve diventare un **tetto di
protocollo**, S6 dice di non misurarlo affatto e di prendere il minimo garantito da QUIC. Misurare in
LAN e alzare il tetto significa spedire audio che l'utente vero non riceve.

---

# 7. ⛔ I difetti di banco pagati questa notte

*Sette, e **cinque hanno prodotto un rosso su strumento sano**: è la famiglia che `LEZIONI.md` §1.9
punto 3 descrive — quando banco e realtà si contraddicono, il primo sospetto è il banco.*

| # | Che cosa ha detto il banco | Che cosa era |
|---|---|---|
| 1 | «il drop-in non ha avuto effetto» | **vero**, ed è il controllo B0.1 che l'ha detto: systemd ordina i drop-in **per nome di file** mescolando le cartelle, e `99-s7-…` finisce **prima** di `remotix-headless.conf` della fase 0. Rinominato `zz-`. ⭐ Il controllo *«si verifica sulla riga di comando del processo, non sul file»* ha risparmiato mezz'ora di misure su una finestra che non esisteva |
| 2 | «regione 0,0 0×0» | i quattro getter di `libei` tornano `uint32_t`, passati a un `%.0f`. ⛔ **La spazzatura aveva l'aspetto di una diagnosi vera** — «la regione è degenere» — mentre la regione era 1920×1080 |
| 3 | «la pagina non ha detto PRONTA in 45 s» | la stava scrivendo in quel momento. Il contatore della pagina **riparte da 1** a ogni caricamento, e il segnaposto valeva 1: la riga nuova non è mai stata «maggiore». Curato con **la posizione nel file** + **un marchio di giro sorteggiato dalla pagina** |
| 4 | «la pagina non ha registrato niente» (×5) | ⛔ **l'ordine fra iniettore e browser**: vedi §8 |
| 5 | «la pagina non si è mossa» | con un ascoltatore passivo Firefox scorre **prima** che il gestore giri: `scrollY` letto nel gestore e 250 ms dopo era **uguale**, e la differenza zero. Il numero giusto era già nel registro sotto un altro nome. Curato misurando **dall'ultima posizione ricentrata** |
| 6 | «la concessione dell'eccezione è fallita» | era **riuscita**: la funzione restituisce «SI»/«NO» stampandolo, e le righe di diagnostica finivano sullo **stesso flusso**. Il valore restituito era «--  concedo…\nSI», che non è uguale a «SI» |
| 7 | «zero finestre di Chrome» | questa macchina ha `WAYLAND_DISPLAY=wayland-0`, e **Chrome 151 sceglie Wayland da sé**: `DISPLAY=:77` davanti al comando non basta, la finestra si apriva sulla scrivania vera mentre `xdotool` cercava su :77. Curato con `env -u WAYLAND_DISPLAY` + `--ozone-platform=x11` |

⭐ **Nessuno dei sette ha prodotto un verde falso**, e non per fortuna: in cinque casi su sette a
fermare il banco è stato **un controllo scritto prima di misurare** — il denominatore, il controllo
positivo dello strumento, o la verifica che l'opzione fosse in vigore.

---

# 8. ⭐⛔ Una scoperta che non è di questa fase, e va portata alla 2 e alla 6

*Trovata dal controllo che dice «la pagina non vede nemmeno muoversi il puntatore», dopo tre giri di
S7 andati a vuoto.*

| | |
|---|---|
| **il fatto**, `[M]` 10 agosto 2026 | in una sessione GNOME **senza dispositivi di input fisici**: se il browser parte **prima** che il puntatore virtuale di `libei` esista, **non riceve nulla** — né rotella, né bottoni, **né il movimento del puntatore**. Se parte **dopo**, riceve tutto |
| **e non è che l'iniezione non arrivi** | Mutter la riceve in tutt'e due i casi: `org.gnome.Mutter.IdleMonitor.GetIdletime` cade da **35 952 ms a 1 013 ms** al primo movimento. ⛔ Il compositore la prende **e non la consegna alla finestra** |
| `[?]` **la causa** | la spiegazione plausibile — una sessione senza dispositivi annuncia un `wl_seat` **senza puntatore**, e il cliente partito prima non si iscrive mai — **non è stata verificata**. Quel che è `[M]` è l'ordine |
| ⛔ **perché riguarda il prodotto** | nel prodotto la sessione grafica nasce **senza alcun dispositivo di input**, e le applicazioni aperte **prima** che un client si colleghi potrebbero trovarsi nello stesso stato: l'utente muove il mouse e quella finestra non risponde. **È una domanda per le fasi 2 e 6**, e va posta lì invece di essere riscoperta da un utente |

---

# 9. I rilievi da portare fuori da questo rapporto

| # | Dove | Che cosa |
|---|---|---|
| **S.1** | `RCP.md` §7.3 | ⭐ **la `[?]` del segno si può chiudere**: `+120` di `libei` è la rotella **in giù**, quindi il server **inverte** l'asse verticale. ⚠ Misurato su **Mutter**; per gli altri quattro desktop resta aperto |
| **S.2** | `fasi/01-filo-nudo.md`, riga S1b | il rimando `S1 §4.2 P5` è **sbagliato**: P5 è il contesto sicuro, e in S1 **non esiste** una prova di durata. Il banco è `banchi/01-s1b-eccezione.sh` |
| **S.3** | `SPECIFICHE.md` §6.1-bis · `DECISIONI.md` §5.0-quater | ⛔ **`screen.width × devicePixelRatio` non è invariante allo zoom su Chrome 151**: dà `risoluzione × zoom`. La formula della tela va rivista, e finché non lo è un client su Chrome con zoom ≠ 100 % dichiara una tela sbagliata |
| **S.4** | `PIANO.md` fasi 2 e 6 | l'ordine fra la nascita del puntatore virtuale e l'avvio delle applicazioni (§8) |
| **S.5** | `web.md` §8 · `fasi/01-filo-nudo.md` | S1b non è più *«da avviare»*: è **avviata**, e il giorno del verdetto è il **17-18 agosto 2026** |
| **S.6** ⭐ | `fasi/01-filo-nudo.md` §«La sonda», colonne **Misurato** e **Data** | ⛔ *(rilievo **R12.7**, 11 agosto 2026)* i numeri di **S7**, **S1b** e **S5** sono stati misurati e **non sono entrati nella tabella di fase**: quelle celle sono ancora vuote. Il progetto tiene i numeri lì, con la data accanto; finché restano solo qui, chi legge il documento di fase crede che la misura non ci sia. ⚠ Non è un file di questo autore: è scritto qui perché è la sua unica traccia |
| **S.7** ⛔ | `RCP.md` §7.3 e §1275-1300 | *(rilievo **R12.7**)* la `[?]` del segno della rotella è **ancora aperta in `RCP.md`** — *«il segno è da misurare, non da decidere»*, col riquadro «va misurato» — mentre è **chiusa qui** da una misura che `RCP.md` non cita. ⛔ È la forma «una cosa che tutti danno per fatta da un altro»; qui per fortuna nel verso innocuo (una `[?]` rimasta aperta) invece che in quello caro |

---

# 10. Che cosa è stato lasciato acceso, e che cosa è stato rimesso a posto

| | |
|---|---|
| **rimesso** | il drop-in `zz-s7-monitor-virtuale.conf` è stato **tolto** e la sessione GNOME riavviata: `gnome-shell --headless --no-x11`, come l'avevamo trovata. `natural-scroll` rimesso a `mouse=false touchpad=true`. ⚠ `bash 01-s7-rotella.sh --pulisci` esiste apposta, perché con `--tieni` il drop-in resta e **il giro dopo non sa che era nostro** |
| **lasciato** | il certificato **longevo** di S1b in `/media/REMOTIX/s1b-certificato/` (⛔ **non si rigenera** per sette giorni) e il profilo di Chrome in `~/.remotix-s1b/`. Il sito su :7452 è **spento**: lo accende da sé chi lancia il giro |
| **portato qui l'11 agosto** | ⭐ `banchi/01-s7-esiti.jsonl`, **copiato dal server in sola lettura** (`/media/REMOTIX/src/01-s7-esiti.jsonl`, 8 023 byte, del 10 agosto 20:59). È la cura del rilievo **A30**: il numero che chiude §7.3 adesso ha, da questa parte, un file che un revisore può aprire. ⚠ Copiato, non rifatto: la scena — la sessione GNOME col monitor virtuale — è stata smontata quella notte e non c'è più |
| **non toccato** | ⛔ `/media/REMOTIX/s1b-certificato/` e `~/.remotix-s1b/` **non sono stati né rigenerati né sfiorati**: sono l'orologio dei sette giorni, e rifarli azzererebbe la misura senza che nessuno se ne accorga per una settimana. Nessun file di altri: solo `banchi/01-s*` e questo rapporto. Nessun commit |
