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
