# Fase 15 — La suite funzionale

*Decisa il **24 settembre 2026**, sera. Da aprire in una sessione nuova.*

## Perché esiste

Il 24 settembre, a fine fase 14, l'utente ha provato a mano e ha trovato **sei difetti** che la rete
anti-regressione non aveva visto (`fasi/14-lxqt.md`, «La sera del 24 settembre»): il bordo che non si
afferra, Maiusc+freccia, la striscia di Firefox in larghezza e in altezza, il blocco di LXQt, il clic di
Chrome, l'«Esci» di LXQt che fa rinascere la sessione. ⇒ La rete guarda i **pezzi** (il fotogramma arriva,
il tasto arriva al server); non guarda quel che **l'utente fa** (seleziono un testo, afferro un bordo,
esco). La fase 15 guarda quello.

L'utente: *«Prima si verifica che REMOTIX faccia correttamente ciò che deve fare. Solo dopo si misura
quanto carico il sistema è in grado di sostenere.»* ⇒ La fase 15 viene **prima** della fase 16 (stress e
capacità) e del sistema d'installazione.

## Le decisioni dell'utente (24 set 2026, sera)

| | decisione |
|---|---|
| **sostituisce la rete intera** | *«eviterei la rete intera… questi test la sostituiscono»*. Sotto la suite resta solo uno **strato tecnico corto**: C7 (non resta niente), C9 (il registro dice di chi), C14 (le scatole non si disturbano), C18 (i gruppi della scheda), C19 (la scatola resta pulita) |
| **browser veri** | Firefox e Chrome sul server, finestre vere; il cliente Python e gli script **non certificano** (possono solo diagnosticare) |
| **la matrice nasce da `SPECIFICHE.md`** | e si rivede con l'utente **prima** di scrivere una sola prova nuova |
| **via** le funzioni che REMOTIX non ha | risoluzione a caldo (uscita il 17 ago 2026, `DECISIONI.md` §5.1-bis), multi-monitor, riaggancio per «ID di sessione» (si rientra con utente e parola) |
| **dentro** quelle che il documento non aveva | appunti nei due versi · forma del puntatore · disposizione di tastiera, accenti, AltGr · stesso utente da due schede (fantasma, sfratto) · i tre orologi di §5.3 · parola sbagliata e ban · tocco Android |
| **aggiunta dell'utente** | stacco e **riattacco a misura diversa** |
| ⭐ **eccezione dichiarata** | al riattacco a misura diversa, su **KDE** (KWin < 6.8, `SPECIFICHE.md` ~851) la tela resta quella vecchia e **il browser riscala**: su KDE è l'atteso, non un FAIL. Su GNOME, XFCE, LXQt la tela prende la misura nuova. Da scrivere anche in `DECISIONI.md` |
| **il rapporto serve alla BONIFICA** | ogni esecuzione registrata, ogni FAIL un difetto numerato |
| **il ciclo** | giro 1 ⇒ elenco dei difetti ⇒ bonifica ⇒ **giro 2 completo con esito ZERO difetti** ⇒ fase 16 |
| ⛔ **congelamento** | fra la fine della bonifica e il giro 2 non si toccano né il prodotto né le prove; se il giro 2 trova un difetto, lo si cura e si rifà il giro 2 **completo**, non la sola prova rossa |
| **ogni prova ha il suo guasto innestato** | una prova che non ha mai dato rosso non è una prova (come C21-C24) |
| **durata** | ogni prova < 10 minuti (l'utente: *«limitiamole ad un massimo di 10 minuti»*); la suite intera: obiettivo < 1 ora |

## I desktop, i browser, le combinazioni

- **Desktop**: GNOME (8511), KDE (8512), XFCE (8513), LXQt (8514) — le scatole `rete11-*`.
- **Browser**: Firefox 140 e Chrome 154, **veri**, sul server, nel labwc senza schermo a 3840x2160
  (`XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 REMOTIX_SCHERMO_ANNIDATO=1
  REMOTIX_SUL_SERVER=1 REMOTIX_CHROME_OPZIONI=--ozone-platform=wayland MOZ_ENABLE_WAYLAND=1`).
- **Chrome Android**: colonna **dell'utente**, col suo telefono (sull'emulatore Chrome non parte, 19 set).
- ⇒ **8 suite per giro** (4 desktop × 2 browser), più la colonna Android a mano.
- ⚠ La matrice dei browser resta **separata** da quella dei desktop (documento dell'utente, §25).

## La matrice (proposta, da rivedere con l'utente)

`[?]` = copertura esistente da verificare; «nuova» = prova da scrivere.

| ID | funzione | cosa si guarda (dalla fotografia o dal campo, non da un contatore) | copertura oggi |
|---|---|---|---|
| F-001 | accesso e creazione della sessione | pagina, modulo, ammissione, desktop in vista | `12-client-veri` a-b, C1 |
| F-002 | prima immagine | desktop disegnato, non degenere, entro il tetto | `12-client-veri` c |
| F-003 | aggiornamento dello schermo | finestra aperta/chiusa, spostata, cambi rapidi | C2, C3 (Python) ⇒ nuova coi browser |
| F-004 | mouse | movimento, clic sinistro e destro, doppio clic, trascinamento, selezione | `12-client-veri` e ⇒ nuova (effetto a schermo) |
| F-005 | forma del puntatore | freccia, I sul testo, freccia doppia sul bordo | **C21** |
| F-006 | ridimensionare dal bordo | il bordo destro si sposta, gli altri no | **C22** |
| F-007 | tastiera: caratteri e tasti speciali | Invio, Backspace, Esc, frecce, Tab dentro un'applicazione | C4 (Python) ⇒ nuova coi browser |
| F-008 | modificatori e combinazioni | Maiusc+frecce, Ctrl+Maiusc+frecce, Ctrl+C/V nell'applicazione | **C23** (+ allargare) |
| F-009 | disposizione, accenti, AltGr | «è», «à», «@», «€» con disposizione it | nuova |
| F-010 | scorciatoie del desktop | quelle d'uso funzionano; quelle pericolose (blocco) no | nuova |
| F-011 | la tela all'attacco | misura della finestra, multiplo di 16, niente striscia verde, sfondo pieno | foto di `12-client-veri` ⇒ nuova |
| F-012 | audio | un'applicazione vera suona, il browser riceve suono non silenzio | C5 (Python) ⇒ nuova coi browser |
| F-013 | video | un video in un'applicazione: immagine continua e suono | nuova |
| F-014 | appunti, browser → sessione | incollato nell'applicazione | C17 (Python) ⇒ nuova |
| F-015 | appunti, sessione → browser | copiato nella sessione, arriva al browser | C17 (Python) ⇒ nuova |
| F-016 | stacco (detach) | la sessione resta, i programmi restano | C6 (Python) ⇒ nuova |
| F-017 | riattacco alla stessa misura | ritrovo lo stato (finestra, testo scritto) | C6 ⇒ nuova |
| F-018 | **riattacco a misura diversa** | GNOME/XFCE/LXQt: tela nuova, desktop che la segue (sfondo, pannello); **KDE: tela vecchia, riscalata (eccezione)** | nuova |
| F-019 | perdita di rete e rientro | linea morta: il filo cade, si rientra a mano, la sessione c'è | nuova (⚠ come simulare la rete: da decidere) |
| F-020 | browser chiuso di colpo, poi nuova connessione | la sessione c'è ancora, ci si riattacca | `12-client-veri` g (ricarica) ⇒ nuova |
| F-021 | «Esci» dal menu | la sessione finisce, i programmi si chiudono, la pagina torna al modulo, niente rinascita | `12-c20-veri`, **C24** (dieci volte) |
| F-022 | orologio del silenzio (30 s) | cliente muto ⇒ staccato, sessione viva | nuova, orologi accorciati |
| F-023 | orologio d'inattività (1800 s) | ⇒ `--inattivita-s` corto | nuova, orologi accorciati |
| F-024 | orologio d'abbandono (3600 s) | la sessione si chiude coi programmi | nuova, orologi accorciati |
| F-025 | stesso utente da due schede | fantasma, sfratto dopo 15 s, `GIA_ATTIVA_REMOTA` | nuova |
| F-026 | più utenti insieme (2-3) | sessioni indipendenti, input e immagine non si mescolano | C14 (Python) ⇒ nuova |
| F-027 | parola sbagliata | rifiuto chiaro, nessuna sessione | nuova |
| F-028 | ban | dopo N errori la porta si chiude per quell'indirizzo; `GIA_ATTIVA_REMOTA` non conta | nuova |
| F-029 | voci pericolose assenti | niente blocco, sospensione, riavvio, spegnimento nel menu; «Esci» c'è | nuova (foto del menu) |
| F-030 | lo schermo non si spegne e non si blocca da solo | 11 minuti fermi, schermo acceso | nuova (⚠ supera i 10 min: da accorciare o dichiarare) |
| F-031 | tocco (Android) | tocco, tocco e mezzo per trascinare | **utente**, a mano |

**Percorsi completi** (documento dell'utente, §26): A creazione→desktop→input→stacco→riattacco→input ·
B creazione→attività→perdita rete→rientro→attività · C creazione→riattacco a misura diversa→riattacco
indietro · D creazione→video/audio→perdita rete→rientro · E creazione→browser chiuso→attesa→nuova
connessione · F creazione→applicazione aperta→stacco→attesa→riattacco→stato. ⚠ C è cambiato: la
risoluzione a caldo non c'è, il cambio di misura si fa solo riattaccandosi.

**Prove negative** (§27, adattate): utente inesistente · parola sbagliata · sessione già chiusa con «Esci»
(si rientra e nasce una sessione NUOVA, pulita) · rete non disponibile (la pagina non si raggiunge: cosa
dice) · stesso utente già attivo da un altro dispositivo.

**Numero delle prove.** 30 funzioni automatiche × 4 desktop × 2 browser = **240 caselle**; 6 percorsi ×
8 = **48**; ~5 negative × 4 desktop = **20** (le negative non dipendono dal browser: una sola passata) ⇒
**circa 300 esecuzioni per giro**, più la colonna Android a mano. Non 300 sessioni: una suite per desktop
e browser **fa nascere la sessione una volta** e prova le funzioni in fila come un utente vero; solo le
prove che chiudono o riattaccano ne fanno nascere un'altra.

## Come si esegue

- **una suite per (desktop, browser)**, i **quattro desktop in parallelo** (una scatola ciascuno,
  browser e porte di debug separati — `banchi-in-parallelo-isolamento`), i due browser uno dopo l'altro;
- ogni prova: inquilino della rete (`c<n>u<n>`, visto da C19 e dallo sgombero), scena nota nella
  sessione, giudizio dalla **fotografia** o dal **valore del campo**, **mai** da un contatore;
- ogni prova ha `--certifica` (funzioni pure) e il suo **guasto innestato** (esito al rovescio: 0 = visto);
- esiti: **PASS**, **FAIL**, **BLOCKED** (= non ho potuto guardare, *con la ragione*: un BLOCKED non è
  un PASS);
- ⛔ la suite **rifà le scatole da zero**: prima di lanciarla si chiede all'utente se sta provando a mano
  (24 set: una sua sessione `nictest` chiusa senza avviso);
- le prove automatiche restano **nella rete**: la suite è la nuova rete (famiglia nuova in `11-gancio.sh`).

## Che cosa si registra, e come

**1. Il registro delle esecuzioni** — `banchi/15-suite/registro.jsonl`, **solo aggiunte, mai
cancellazioni** (un giro ripetuto resta con tutti i suoi giri: è così che si vede una gara), una riga per
esecuzione:

| campo | esempio |
|---|---|
| `giro` | `1`, `2`, o `bonifica` |
| `test` / `funzione` | `T-018-kde-firefox` / `F-018` |
| `desktop` · `browser` · `versione` | `kde` · `firefox` · `140.16.0` |
| `sistema` | `Debian 13, labwc senza schermo 3840x2160` |
| `binario` · `pagina` · `commit` | md5 `7dfd6a96` · md5 `87268f13` · `53d07b4` |
| `inizio` · `durata_s` | ISO 8601 · `41` |
| `esito` | `PASS` / `FAIL` / `BLOCKED` |
| `ragione` | una frase: che cosa si è visto (obbligatoria per FAIL e BLOCKED) |
| `atteso` · `osservato` | le due frasi, come nel caso di test |
| `guasto_visto` | `true`/`false` per la passata col guasto innestato |
| `evidenze` | percorsi: foto prima/dopo, registro del prodotto, errori JS del browser, righe RCP/WebTransport |
| `difetto` | `D-007` se il FAIL ha aperto o toccato un difetto |

**2. Le evidenze** — sul server in `/media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<test>/`
(foto a scala 1, `registro.log` della scatola tagliato sull'intervallo, console del browser, `journalctl`
dell'inquilino quando serve). Collegate al Test ID e al commit.

**3. L'elenco dei difetti** — `banchi/15-suite/difetti.jsonl` (e il rapporto lo mostra):
`id` (D-001…), che cosa si vede (con le parole dell'utente se l'ha trovato lui), desktop e browser dove
succede, **classe** (A regressione vera · B assunzione di un desktop nel codice comune · C difetto del
banco · D invariante sbagliato, ⛔ mai come scorciatoia), **stato** (aperto · in cura · curato ·
verificato), la causa misurata, il commit della cura, **la prova che da quel giorno lo sorveglia**.

**4. Il rapporto** — si **genera** dal registro, non si scrive a mano: la matrice funzione × desktop ×
browser con l'ultimo esito e il commit su cui è stato misurato; l'elenco dei difetti col loro stato; per
ogni casella FAIL/BLOCKED la ragione e il link alle evidenze. Serve alla **bonifica**, non all'utente;
si può pubblicare anche come pagina privata aggiornata a ogni giro.

## Limiti da dichiarare, e decisioni ancora aperte

- `[?]` **perdita di rete** (F-019, percorsi B e D): sul server non ci sono `tc`/`wondershaper`; col
  browser sul server si può strozzare `lo` o un veth; il percorso vero è dal tablet (`wondershaper`,
  [[wondershaper-sul-tablet]]). **Da decidere con l'utente.**
- **orologi lunghi** (F-022…F-024, F-030): si provano con gli orologi accorciati da riga di comando
  (`--inattivita-s`, abbandono) su una scatola dedicata; dichiarato.
- **Android**: all'utente.
- il **puntino di 1 px** sotto la punta del puntatore (prezzo della forma su KDE e labwc): giudizio
  dell'utente, da registrare come voce della matrice (F-005).

## L'ordine

1. la matrice qui sopra **rivista con l'utente**;
2. le prove nuove, in parallelo (un agente per gruppo di funzioni), ognuna col suo guasto, dentro la rete;
3. il registro, l'elenco dei difetti e il generatore del rapporto;
4. **giro 1** (le 8 suite) + colonna Android dell'utente ⇒ elenco dei difetti;
5. **bonifica**;
6. ⛔ congelamento, **giro 2**: zero difetti ⇒ fase 16.

---

## Come è stata costruita

*24 settembre notte → 25 settembre 2026, mattina (`9264c52`, `d9743dc`).*

**Dieci gruppi di prove**, scritti in parallelo (un agente per gruppo), ognuno con la sua base comune
importata e non copiata:

| gruppo | funzioni | prove | attrezzi comuni |
|---|---|---|---|
| **G1** | F-001 F-002 F-003 F-011 | `15-f001` `15-f003` `15-f011` | — |
| **G1b** «il desktop si comporta da desktop remoto» | F-010 F-029 F-030 | `15-f010` `15-f029` `15-f030` | `15-g1b-comune.py` (clic e tasti veri al browser, OCR della foto); `15-g1b-esplora.py` solo diagnosi |
| **G2** mouse e tastiera | F-004 F-007 F-009 | `15-f004` `15-f007` `15-f009` | `15-g2-scena.py`: una pagina nota servita nella casa dell'inquilino e aperta in kiosk **dentro** la sessione |
| **G3** | F-005 F-006 F-008 | `15-f005` `15-f006` `15-f008` | `15-g3-comune.py`: C21, C22, C23 della fase 14 importate così come sono |
| **G4** audio e video | F-012 F-013 | `15-f012` `15-f013` | `15-g4-comune.py`: l'**orecchio** nella pagina e l'occhio sul video |
| **G5** appunti | F-014 F-015 | `15-f014` | — |
| **G6** stacco e riattacco | F-016 F-017 F-018 F-020, P-A P-C P-E P-F | `15-f016` `15-f018` `15-f020` | `15-g6-comune.py` (la scena e i giudici puri) |
| **G7** la rete che cade e gli orologi | F-019 F-022 F-023 F-024, P-B P-D | `15-f019` `15-f022` | `15-g7-comune.py` + `15-g7-server.sh`: un **secondo server** del prodotto per scatola (porte 8611-8614, orologi accorciati da riga di comando), e la **linea morta simulata sul server con nftables** (una tabella nostra che scarta l'UDP della sola porta della prova) |
| **G8** gli utenti, la parola, il ban | F-025 F-026 F-027 F-028, N-1 N-3 N-4 | `15-f025` `15-f026` `15-f027` `15-n027` | `15-g8-comune.py` + `15-g8-server.sh`: secondo server con porte 8621-8624, ban-file, socket e registro **suoi** (`banchi-in-parallelo-isolamento`) |
| **G10** «Esci» | F-021 | `15-f021` | — |

⚠ I nomi G1 e G5 qui sopra sono ricostruiti: le loro prove non scrivono il gruppo in testa (G5 compare
solo in un rilievo di `suite.py`, il profilo di Firefox). Gli altri li scrivono le prove stesse.

⇒ **25 prove** che coprono F-001…F-030, i percorsi A-F e le negative N-1, N-3, N-4. Ogni prova
dichiara in testa, come righe di testo, che cosa guarda: `FUNZIONI = (…)`, e se serve
`PER_BROWSER = False` (una volta sola, con Firefox: F-027/F-028, F-030, le negative), `LUNGA = True`,
`SERVER = "15-g7-server.sh"`.

**La base comune** — `banchi/15-suite/suite.py`. Una sola lingua per tutte le prove:
- riga di comando: `--scatola` e `--browser` (uno solo), `--guasto` (dopo la passata sana, la passata
  col guasto innestato **nella stessa sessione**, esito al rovescio), `--certifica` (solo le funzioni
  pure), `--evidenze`, `--porte-base` (porte di debug dei browser, ⛔ diverse per ogni desktop in
  parallelo), 4K di default;
- uscita: una riga `SUITE {…}` per funzione guardata, che il giro raccoglie; codice 0 tutto PASS · 1
  almeno un FAIL o un guasto non visto · 3 almeno un BLOCKED;
- l'inquilino si chiama `c15<nnn>u<n>` (C19 e lo sgombero lo riconoscono) e si sgombera **sempre**;
- si appoggia a `12-client-veri.py` (le guide dei browser: Marionette per Firefox, CDP per Chrome),
  `12-c20-veri.py` (la scatola, il registro del server, gli inquilini) e `11-c21-…` (foto a piena
  risoluzione);
- ⭐ sul server i comandi dentro le scatole vanno con `sudo podman exec` **locale**, non per ssh verso
  sé stesso: `[M]` 24 set, dieci agenti insieme, sshd ne troncava una parte ⇒ inquilini non creati e
  BLOCKED che non erano del prodotto (rilievo del G7).

**Il giro** — `banchi/15-suite/15-giro.py`, sul server come `nicfio` (i browser veri stanno là; i
banchi ci arrivano con `15-porta.sh`, una prova sola si lancia con `15-una.sh`):
- trova le prove `15-f*.py` e `15-n*.py` e ne legge le dichiarazioni;
- ⭐ **i quattro desktop in parallelo**, una fila per desktop; nella fila Firefox e poi Chrome; porte di
  debug diverse per desktop;
- ogni prova con `--guasto`, tetto **10 minuti** (oltre: BLOCKED «oltre i 10 minuti», e il processo si
  uccide);
- ⛔ prima di partire guarda se nelle scatole c'è una persona (chiunque non sia un inquilino
  `c<n>u<n>`): se c'è, si ferma. Le scatole si rifanno da zero con `15-rifai-scatole.sh`, solo col via
  dell'utente (permesso dato il 25 set).

⭐ **Un labwc senza schermo per desktop** — `15-compositori.sh accendi|spegni|stato`, 3840x2160 ciascuno.
`[M]` gruppi G2 e G8, 25 set: coi quattro desktop nello **stesso** labwc le finestre di Chrome si
coprono a vicenda, e **Chrome coperto non ridipinge**: `Page.captureScreenshot` resta appeso (una foto
appesa 17 minuti, tre corse finite a 900 s). Firefox si fotografa anche coperto, Chrome no. ⇒ Ogni
desktop ha il suo compositore, e in ciascuno un browser alla volta; il giro legge il socket da
`$XDG_RUNTIME_DIR/15-compositori/<desktop>` e lo passa come `WAYLAND_DISPLAY`.

**Il registro** — `/media/REMOTIX/misure/fase15/registro.jsonl` sul server, copiato in
`banchi/15-suite/registro.jsonl`; solo aggiunte, una riga per esecuzione coi campi della tabella qui
sopra (più `passata`: `sana` o `guasto`, e `prova`). Le evidenze in
`/media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<prova>/` (l'uscita intera in `uscita.log`,
foto e console dentro). I difetti in `banchi/15-suite/difetti.jsonl`.

**Il rapporto** — `banchi/15-suite/15-rapporto.py`, **generato dal registro, mai scritto a mano**:
la matrice funzione × desktop × browser con l'ultimo esito della passata sana del giro scelto e il segno
del guasto, i difetti col loro stato, per ogni casella FAIL o BLOCKED la ragione e le evidenze; in testa
binario, pagina, commit e i conti. `--testo` per il terminale, `--html` per una pagina.

    python3 banchi/15-suite/15-rapporto.py --registro banchi/15-suite/registro.jsonl \
        --difetti banchi/15-suite/difetti.jsonl --giro 1 --testo

**Lo strato tecnico** — `15-giro.py --strato-tecnico` (o `--solo-strato-tecnico`): per ogni desktop, in
parallelo, **C7 C9 C18 C19**, ciascuna sana e col suo guasto (`--lascia-un-processo`, `--togli-nome
tutto`, `--senza-usermod`, `--lascia-un-inquilino`), lanciate da `11-accendi.sh`; poi **C14** con le
quattro insieme. ⛔ Prima di ogni maglia la stessa **sgomberata** di `11-gancio.sh` (vedi D-013).

**Nella rete** — famiglia **`suite`** di `banchi/11-scatole/11-gancio.sh` (`227611d`, 25 set 09:35):
`GIRA_SUITE` lancia `15-giro.py --giro ${GIRO_SUITE:-rete} --strato-tecnico` come l'utente dei browser,
dall'albero intero dei banchi; il gancio avvisa «⛔ ~2 ore». È la nuova rete, come deciso il 24 set.

## Il giro 1 — 25 settembre 2026

`[M]` Binario **`7dfd6a96`**, pagina **`87268f13`** (quelli consegnati dalla fase 14), banchi
`9264c52`+modifiche; Debian 13, labwc senza schermo 3840x2160, i5-13500T con Intel UHD 770; Firefox
140.16.0 e Chrome 154.0.8037.57, finestre vere. Dalle 04:09 alle 06:12 (ora del server 02:09-04:12
UTC): **123 minuti** per le 8 suite e lo strato tecnico, più C14 (786 s). La prova più lunga: F-030,
490 s, sotto il tetto dei 10 minuti.

**609 esecuzioni** nel registro:

| passata | PASS | FAIL | BLOCKED | totale |
|---|---|---|---|---|
| **sana** (quella che conta per la matrice) | 256 | 42 | 7 | 305 |
| **col guasto** | 299 (guasto **visto**) | 0 | 5 | 304 |
| **insieme** | 555 | 42 | 12 | 609 |

⇒ **nessun guasto innestato sfuggito**: dei 304, 299 visti e 5 BLOCKED (le stesse caselle bloccate
della passata sana). **C14 VERDE** (le quattro scatole non si disturbano).

**Le caselle non verdi della passata sana** (tutte le altre `ok` — F-001, F-003…F-008, F-010…F-012,
F-014…F-016, F-018, F-020, F-022, F-026…F-030, i percorsi A-F, le negative N-1 N-3 N-4, C7, C18, e C9 su
gnome):

| | gnome ff/ch | kde ff/ch | xfce ff/ch | lxqt ff/ch | difetto |
|---|---|---|---|---|---|
| **F-002** prima immagine | ok / ok | ok / ok | FAIL / FAIL | ok / ok | D-010 (banco) |
| **F-009** accenti, AltGr | ok / ok | FAIL / FAIL | ok / ok | ok / ok | D-008 |
| **F-013** video | FAIL / ok | ok / ok | FAIL / ok | FAIL / ok | D-006, D-014 |
| **F-017** riattacco stessa misura | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | D-001 |
| **F-019** la rete cade | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | D-002 |
| **F-021** «Esci» | FAIL (guasto BLOCKED) / ok | FAIL / FAIL | ok / ok | ok / ok | D-003, D-005, D-016 |
| **F-023** inattività | FAIL / ok | FAIL / FAIL | BLOCKED / BLOCKED | FAIL / ok | D-003, D-011 |
| **F-024** abbandono | ok / ok | ok / ok | BLOCKED / BLOCKED | ok / ok | D-011 |
| **F-025** stesso utente, due schede | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | D-002 |
| **C9** il registro dice di chi | ok | BLOCKED | BLOCKED | BLOCKED | D-012 (banco) |
| **C19** la scatola resta pulita | FAIL | FAIL | FAIL | FAIL | D-013 (banco) |

Quel che si è visto, con le parole del registro:
- **F-017** (8/8): lo stato si ritrova (finestra in foto, striscia di testo, gettone invariato) **ma**
  la pagina dice «Ammesso, sessione nuova, … desktop sconosciuto» a una sessione ripresa;
- **F-019** (8/8): *«il filo cade e la pagina NON lo dice: desktop congelato senza una parola (si rientra
  solo ricaricando di propria iniziativa)»*; **F-025** (8/8) cade sul punto 3, la stessa cosa;
- **F-023**: *«staccato per inattività, ma la pagina non lo dice»* (il congedo c'è, a 12-13 s col tetto
  di 12 s; la pagina resta vestita da desktop);
- **F-021** kde: la sessione finisce pulita, ma **il rientro non è pulito** (Plasma riapre il programma);
- **F-009** kde: *«RIPIEGO DICHIARATO: lo schema org.gnome.desktop.input-sources non c'è»* ⇒ la sessione
  resta English (US);
- **F-013** Firefox: gnome udibile 89 %, lxqt 75 %, buchi fino a 0,3-0,4 s; xfce: il contesto audio
  della pagina **mai** «running», 0 % per 40 s;
- **F-002** xfce: la foto a piena risoluzione giudicata degenere (62-72 colori, 98 % nero: lo sfondo
  della scatola).

⇒ 42 FAIL e 12 BLOCKED riportati a **14 difetti** (D-001…D-014): 8 del prodotto, 3 del banco curati
subito, 3 da indagare o decidere (`774595d`). Nel corso della bonifica se ne sono aggiunti cinque
(D-015…D-019). Chrome Android: colonna dell'utente, a mano.

## I difetti

Da `banchi/15-suite/difetti.jsonl`, con lo stato scritto nel file. Classi: **A** regressione vera ·
**B** assunzione di un desktop nel codice comune · **C** difetto del banco · **?** da stabilire.

| id | che cosa si vede | dove | classe | stato | cura · prova |
|---|---|---|---|---|---|
| D-001 | dopo l'accesso la pagina dice sempre «sessione nuova» e «desktop sconosciuto», anche a sessione ripresa | tutti, ff e ch | A | in cura | `9ff4c1f` · `15-f016` (F-017 8/8) |
| D-002 | la linea cade (o il browser congelato si risveglia): la pagina resta congelata col desktop, non dice niente, non torna al modulo | tutti, ff e ch (F-019 8/8, F-025 8/8) | A | in cura | `c7a67ea` · `15-f019` |
| D-003 | dopo il congedo per inattività (e dopo «Esci») un fotogramma in volo ri-veste la pagina da desktop: modulo nascosto | F-023 su 4 caselle, F-021 gnome/ff | A | in cura | `c7a67ea` · `15-f022` |
| D-004 | una sessione aperta e mai toccata non scade mai per abbandono | codice (`[R]`) | A | in cura | `9ff4c1f` · `15-f024b` |
| D-005 | KDE: dopo «Esci» il nuovo accesso non è pulito, Plasma riapre il programma | kde, ff e ch | B | in cura | `aa4014d` · `15-f021` |
| D-006 | Firefox con un video: buchi di suono corti e ripetuti (0,1-0,4 s); Chrome no | gnome/ff 89 %, lxqt/ff 75 % | A | da confermare sul dispositivo vero | prima cura tolta (`b40856d`) · `15-f013` |
| D-007 | XFCE: riattaccandosi più piccoli, una finestra grande resta in parte fuori dal bordo | xfce | ? | da giudicare (l'utente) | — |
| D-008 | KDE: la disposizione della tastiera del browser non si applica («è à ò ù é ç ° §» non escono) | kde, ff e ch | B | in cura | `aa4014d` · `15-f009` |
| D-009 | a server spento la pagina impiega 31 s a dire «Non si collega» | tutti, ff | A | da decidere | `e719d08` · `15-n027` |
| D-010 | F-002 su XFCE: il desktop nero giudicato degenere senza la tolleranza «scuro ma vivo» | xfce | C | curato | `15-f001` |
| D-011 | orologi su XFCE: il banco aspettava 45 s il primo fotogramma «non degenere» senza gesti, e l'inattività accorciata chiudeva la sessione | xfce, ff e ch | C | curato | `e670ee3` · `15-f022` |
| D-012 | C9 BLOCKED: l'area «forma» del registro (`src/forma.c`, fase 14) sconosciuta | kde, xfce, lxqt | C | curato | `11-c9` |
| D-013 | C19 FAIL: lo strato tecnico non sgomberava gli inquilini fra una maglia e l'altra | tutti | C | curato | `15-giro.py` |
| D-014 | XFCE con Firefox, video: il contesto audio mai «running», 40 s di silenzio | xfce/ff | ? | non riprodotto | `15-f013` (sorveglia nel giro 2) |
| D-015 | GNOME: la disposizione negoziata si scrive nel dconf dell'**utente** e ci resta | gnome | B | aperto | `ddcf28d` `85697c9` · `15-f009`, `15-f031b` |
| D-017 | XFCE: il prodotto scrive nei canali xfconf dell'utente voci che non sono blocco/riavvio/sospensione/stand-by, e cancella `~/.cache/sessions` | xfce | B | aperto | `85697c9` `7543c6a` · `15-f031b` |
| D-018 | LXQt: il prodotto scrive in `~/.config/lxqt/*.conf` e mette voci `Hidden` nelle applicazioni dell'utente | lxqt | B | aperto | `85697c9` `e8115e5` · `15-f031b` |
| D-016 | F-021 gnome/ff BLOCKED: la fetta di registro vuota dopo «Esci» letta come «non letta», e il guasto non rientrava in una sessione viva | gnome/ff | C | curato | `c3741d3` · `15-f021` |
| D-019 | P-B e P-D su xfce/ch: dopo il rientro l'immagine sembrava quasi ferma (cambi 0,9-1,6 %) | xfce/ch | C | curato | `2f6c0a2` · `15-f019` |

⚠ Per D-015, D-017 e D-018 il file dice ancora «aperto», ma le cure sono sul ramo `bonifica-15`
(sezione «La bonifica»). Per D-009 la cura è scritta dopo la decisione dell'utente. Le cure del banco
(classe C) stanno su `fase-10-cure`.

## Le decisioni dell'utente del 25 settembre

Mattina, dopo il giro 1. Registrate anche in `DECISIONI.md` §8.

| difetto | decisione |
|---|---|
| **D-005** | la sessione remota KDE parte **vuota** di suo (`loginMode=emptySession` nella cartella della sessione); ma se l'utente in Impostazioni ha scelto «ripristina la sessione salvata», **vince la sua scelta** |
| ⭐ **D-015, D-017, D-018** | *«le impostazioni utente non si toccano»* — su nessun desktop. Precisata la stessa mattina: *«Le impostazioni dell'utente non si toccano TRANNE quelle che riguardano blocco-schermo, riavvio sistema, sospensione e stand-by: queste sono impostazioni pericolose per altri utenti presenti sulla macchina»*. ⇒ Quelle quattro famiglie si scrivono nelle impostazioni dell'utente (persistenti); tutto il resto (tastiera, voci di menu, scorciatoie, «Esci» visibile, cambio utente, Ctrl+Alt+F…) vale **solo per la sessione remota**, sui quattro desktop |
| **D-002** | la frase *«il collegamento con il server si è interrotto: per rientrare scrivi di nuovo la parola d'ordine»* va bene |
| **D-009** | il server spento si dice **subito** (~1 s, dal rifiuto di `/impronta`), non dopo i 30 s del browser |
| ⭐ **D-006** | *«concordo sulla soluzione D [dichiararlo], ma il problema va risolto con la soluzione B [decodificatore Opus nostro in WebAssembly nella pagina, per TUTTI i browser], che è la scelta che ci consente di avere un prodotto bugs-free»* ⇒ B si fa **prima del giro 2** |

## La bonifica

Sul ramo **`bonifica-15`** (`git log fase-10-cure..bonifica-15 --oneline`), le cure del prodotto; le
correzioni del banco nate su `fase-10-cure` ci sono riportate con le fusioni «bonifica-15: …».

| commit | che cosa cura |
|---|---|
| `9ff4c1f` | **D-001**: `SESSIONE` dice `2 = RIPRESA` quando la sessione grafica di quell'utente c'era già al verdetto di PAM, e il nome vero del desktop (gnome/kde/xfce/lxqt). **D-004**: l'orologio dell'abbandono parte alla **nascita** del palco (il riattacco non lo rinnova, decisione del 16 ago) |
| `e3c8804` | prova nuova **F-024b** (`15-f024b-sessione-mai-toccata.py`): server G7 con `--abbandono-s 60`, nessun gesto ⇒ la riga «§5.3 — ABBANDONO» entro 90 s; guasto = l'orologio di serie |
| `c7a67ea` | **D-002**: la chiusura del trasporto senza CONGEDO dice la frase decisa dall'utente e torna al modulo. **D-003**: `torna_al_modulo()` chiude lo schermo prima di togliere il vestito, i fotogrammi in volo si buttano |
| `aa4014d` | **D-005**: KDE nasce vuoto (`ksmserverrc loginMode=emptySession` della sessione). **D-008**: la disposizione arriva a KWin (`kxkbrc` della sessione con `[$i]` + `org.kde.keyboard reloadConfig`); la frase falsa del ripiego corretta |
| `202b514` → `b40856d` | **D-006**, prima cura (l'ora del contesto stantia su Firefox): **tolta**. `[M]` coi browser veri peggiorava: lxqt udibile 68 % (giro 1: 75 %), buco 1,2 s, gnome FAIL |
| `e719d08` | **D-009**: `/impronta` rifiutata dalla rete ⇒ «il server non risponde: è spento o non raggiungibile», senza aprire WebTransport; un server lento non ha orologi |
| `ddcf28d` | **D-015** (GNOME): la disposizione e le chiavi della sessione in un **dconf della sessione** (`DCONF_PROFILE`: `service-db:shm/remotix` in cima, `user-db:user` sotto in sola lettura), svuotato a ogni nascita |
| `85697c9` | **D-015/D-017/D-018**, la regola intera: GNOME le permesse (`sleep-inactive-*`, `idle-delay`, `lock-enabled`) all'utente, le altre alla sessione; XFCE un xfconf **della sessione** (proprietà `locked` in una cartella in testa a `XDG_CONFIG_DIRS` di xfconfd), `SessionName=REMOTIX` + `SaveOnExit=false` al posto di `rm ~/.cache/sessions`; LXQt panel.conf e voci `Hidden` nelle cartelle della sessione |
| `db117f4` | prova nuova **F-031B** (`15-f031b-impostazioni-intatte.py`, una volta per desktop): dconf, xfconf, lxqt, applications, kxkbrc, `~/.cache/sessions` letti dal disco prima dell'accesso e dopo «Esci»; guasto = scrittura persistente simulata |
| `7543c6a` · `a0101a6` | **D-017**: Sospendi, Iberna, Sonno ibrido sono sospensione ⇒ permesse, di nuovo nel canale dell'utente; nella sessione restano 4 chiavi. Il guasto di `13-w2` rifatto |
| `e8115e5` | **D-018**: `lxqt-panel` all'avvio riscriveva nel panel.conf dell'utente ⇒ ora `--configfile $XDG_RUNTIME_DIR/remotix/lxqt-pannello.conf` |
| `5792418` `7fccca7` `f99b6e7` `0efffe4` `4382bbc` `cb7b025` `f0bbf01` | il banco riallineato: registro, C9, strato tecnico (D-012, D-013), D-016, D-019, D-011, la famiglia `suite` |

⚠ Resta prima del giro 2: **D-006 soluzione B** (Opus in WebAssembly), D-007 al giudizio dell'utente,
D-014 sorvegliato. Poi ⛔ congelamento e **giro 2 completo**.

## Lezioni

Sette difetti **del banco** trovati dal giro stesso: ognuno un verde o un rosso che non era del
prodotto.

- **La foto su sfondo nero** (D-010, D-011). Lo sfondo della scatola XFCE è nero, e in 4K il giudice
  dei pixel dice «degenere» a ogni foto (62-72 colori, 98 % nero). Il primo fotogramma aveva la
  tolleranza «scuro ma vivo», la foto a piena risoluzione no. ⇒ Un giudice va provato **su tutti e
  quattro** gli sfondi, non su quello più colorato.
- **C9 e l'area «forma»** (D-012). `src/forma.c` (fase 14) scrive nel registro un'area che C9 non
  conosceva ⇒ BLOCKED su kde, xfce, lxqt. La rete intera non era stata rifatta dopo la fase 14 (decisione
  del 24 set): il primo giro la trova. Il BLOCKED era onesto: *«un verde che le ignora sarebbe un verde
  che non le ha guardate»*.
- **C19 e lo sgombero** (D-013). Le maglie cancellano il loro inquilino **prima** di crearlo, non
  dopo; `11-gancio.sh` sgombera fra una maglia e l'altra, lo strato tecnico del giro no ⇒ C19 vedeva
  gli inquilini di C9. È la stessa lezione del C19 rosso della fase 14: chi rifà un giro fuori dal
  gancio deve rifare **anche lo sgombero**.
- **F-021 e la fetta vuota** (D-016). Dopo «Esci» la fetta di registro può essere vuota: vuota non vuol
  dire «non letta». E la passata col guasto deve rientrare in una sessione **viva**, se no il suo
  gesto parla a un bus che non c'è.
- **L'orologio accorciato contro l'ingresso lento** (D-011). A 12 s l'inattività era più corta della
  nascita di XFCE in 4K (CONGEDO 0x02 subito dopo il primo fotogramma); a 25 s ancora no, perché la
  causa vera era il banco che fotografava per 45 s senza gesti. ⇒ Nelle fasi a orologi corti il primo
  fotogramma si guarda con un tetto **più corto dell'orologio**. Un orologio accorciato accorcia anche
  la pazienza del banco.
- **Le pause fisse contro l'animazione** (D-019). Il giudice del movimento fotografava ogni ~0,9 s,
  cioè il mezzo giro del triangolo di `weston-simple-egl`: foto sempre nello stesso punto, «immagine
  ferma» a immagine viva. ⇒ Pause **irregolari** e confronto fra **tutte** le coppie.
- **L'orecchio innocente ma gonfiante** (D-006). L'orecchio del G4 sostituisce il collegamento audio
  della pagina: il sospetto era che i buchi di Firefox fossero suoi. `[M]` misurato **senza orecchio**
  (60 s, lxqt e kde): Firefox+video 3-5 riarmi anche col video nel worker, Firefox senza video 0,
  Chrome 0, Firefox+video in PCM 0, CPU del server 11-14 % ⇒ il difetto è **vero** (il decodificatore
  Opus di Firefox), l'orecchio non lo crea. Ma lo **gonfia**: le percentuali di F-013 (75-89 %) non sono
  la misura del difetto. E la prima cura, scritta su un banco che non somigliava a Firefox vero, coi
  browser veri peggiorava: tolta.

---

## ⭐⭐ IL GIRO 2 — 25 settembre 2026: ZERO DIFETTI

`[M]` Prodotto e prove **congelati** al commit `d121715` (segno `fase15-giro2-congelato`), binario
**`b1443a0b`**, pagina **`942f2873`**; scatole rifatte da zero; 11:25 → 13:38 (133 minuti), i quattro
desktop in parallelo, Firefox 140 e Chrome 154 veri, 3840x2160, più lo strato tecnico e C14.

| | esecuzioni | esito |
|---|---|---|
| passate sane | 329 | **329 PASS** — 0 FAIL, 0 BLOCKED |
| passate col guasto innestato | 328 | **328 guasti visti** — nessuno sfuggito |
| strato tecnico (C7 C9 C18 C19 × 4, C14) | compreso sopra | tutto verde |

Funzioni coperte: F-001…F-030 (F-031, il tocco su Android, resta dell'utente col telefono), F-018b e
F-018c (le finestre dentro lo schermo al riattacco a misura diversa, nate con D-007), F-024b (la
sessione mai toccata scade), F-031B (le impostazioni dell'utente intatte dopo la sessione remota, e il
gestore d'utente pulito), i percorsi A-F, le negative N-1, N-3, N-4.

⇒ **Il cancello della fase 15 è passato**: giro 1 ⇒ 21 voci (14 del prodotto, 7 del banco) ⇒ bonifica
⇒ giro 2 a zero. Tutte le voci sono «verificato (giro 2)»; D-014 non si è ripetuto.

**Il rapporto**, generato dal registro e mai scritto a mano:
`banchi/15-suite/rapporto-giro2.html` (e `.txt`), `banchi/15-suite/rapporto-giro1.html` (e `.txt`); il
registro intero di tutti i giri — giro 1, caselle rifatte, verifiche della bonifica, prove generali,
giro 2 — è `banchi/15-suite/registro.jsonl` (2455 righe, solo aggiunte), i difetti
`banchi/15-suite/difetti.jsonl`; le evidenze sul server in `/media/REMOTIX/misure/fase15/giro2/`.

**Come si rifà**: `bash banchi/15-suite/15-porta.sh`, poi sul server (con le scatole rifatte:
`bash …/15-suite/15-rifai-scatole.sh`) `python3 …/15-suite/15-giro.py --giro <nome> --strato-tecnico`;
oppure `bash banchi/11-scatole/11-gancio.sh gira --famiglia suite`. Il rapporto:
`python3 banchi/15-suite/15-rapporto.py --registro banchi/15-suite/registro.jsonl --difetti
banchi/15-suite/difetti.jsonl --giro <nome> --html <file>`.

### Che cosa è entrato nel prodotto con la bonifica

| difetto | che cosa si vedeva | la cura |
|---|---|---|
| D-001 | «sessione nuova» e «desktop sconosciuto» anche a sessione ripresa | SESSIONE dice RIPRESA (2) e il desktop vero |
| D-002, D-021 | linea caduta o browser congelato: pagina muta sul desktop fermo | la pagina lo dice e torna al modulo, anche nella finestra fra SESSIONE e l'apertura dell'input |
| D-003 | dopo lo stacco o «Esci» un fotogramma in volo rimetteva il desktop sopra il modulo | `Schermo.chiudi()` al congedo |
| D-004 | una sessione mai toccata non scadeva mai | l'orologio dell'abbandono parte alla nascita |
| D-005 | KDE riapriva i programmi dopo «Esci» | sessione Plasma vuota di suo (salvo scelta dell'utente) |
| D-006 | buchi di suono con Firefox e un video (decodificatore Opus di Firefox) | **decodificatore Opus nostro in WebAssembly** (libopus 1.5.2), per tutti i browser |
| D-007 | XFCE/LXQt: al riattacco più piccolo finestre in parte fuori dallo schermo | il prodotto fa riportare dentro le finestre a labwc |
| D-008 | KDE: gli accenti non uscivano | la disposizione negoziata arriva a KWin (kxkbrc della sessione) |
| D-009 | server spento: 31 s prima di «Non si collega» | detto subito |
| D-015, D-017, D-018, D-020 | REMOTIX scriveva nelle impostazioni dell'utente e lasciava tracce nel gestore d'utente | le impostazioni dell'utente non si toccano, salvo blocco/riavvio/sospensione/stand-by; tutto il resto vale solo per la sessione remota e si toglie alla fine |

⚠ **Resta dell'utente**: la colonna Android (F-031) col suo telefono, e il giudizio a orecchio
dell'audio di Firefox col video sul tablet (D-006 è verde in suite; il giudice ultimo è lui).
