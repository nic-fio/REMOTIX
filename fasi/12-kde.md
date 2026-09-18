# Fase 12 — KDE

*Aperta il **18 settembre 2026**. Chiusa il —*

## Che cosa deve produrre

Il secondo desktop: **la stessa cosa su Plasma** (`PIANO.md` fase 12). L'utente apre il browser e
vede il suo desktop KDE, come oggi vede GNOME.

⛔ **La regola della fase, dell'utente, 18 settembre 2026**: *«Devi sviluppare KDE senza rompere ciò
che già funziona su GNOME.»* ⇒ La rete della fase 11 non è il collaudo finale: è il **guardiano** di
ogni passo. Si procede per **incrementi**, e ogni incremento attraversa gli stessi cancelli:

| | |
|---|---|
| **CP0** | la baseline: rete completa sulle quattro scatole, stesso binario ovunque |
| **CP1** | l'incremento è definito: obiettivo, invariante, moduli, prova KDE, prova client, regressioni GNOME da guardare, criterio |
| **CP2** | GNOME e KDE **osservati** sul punto dell'incremento, e la differenza scritta — niente dedotto |
| **CP3** | la modifica minima progettata: file, perché, che cosa di GNOME resta com'è |
| **CP4** | la prova KDE fatta davvero, sulla scena dichiarata |
| **client** | Chrome e Firefox su Linux, Chrome sull'emulatore Android — quando l'incremento tocca il percorso |
| **rete** | la rete completa, GNOME invariato, i guasti innestati ancora presi |
| **checkpoint** | un commit che si può riprendere |

⇒ Un rosso su GNOME è **una regressione finché non è dimostrato il contrario**, e si classifica:
A regressione vera · B assunzione GNOME nel codice comune · C difetto del banco · D invariante
sbagliato (⛔ mai come scorciatoia).

## Le decisioni prodotte

- `DECISIONI.md` §4.6-duodetricies — **un desktop per macchina**; la scelta fra più desktop è
  rimandata (`MASTERPLAN.md` M5).

## Il banco — scritto prima di sviluppare

Il banco è **la rete della fase 11** (`banchi/11-scatole/`), puntata sulla scatola `kde`. Il segno
che KDE è servito è quello già scritto: **`C1(kde)` diventa verde**, e dopo di lei C2, C3, C4, C6,
C7, C8b, C9 sulla stessa scatola.

⚠ **Tre cose del banco che la fase deve toccare, e si dichiarano qui prima di toccarle** (letture
del 18 settembre, `[R]`):

1. ⛔ **Tre cancelli «solo gnome» nel lancio delle maglie** — `11-gancio.sh` (`le_cinque_nuove`, e
   la famiglia veloce che fa C1 solo su gnome) e `11-accendi.sh` (c8b esce 3 fuori da gnome). Il
   commento che dice *«il giorno che il prodotto saprà accendere KDE non c'è niente da togliere»* è
   falso. ⇒ Aprirli **non ammorbidisce nessun giudizio**: è la condizione perché le maglie guardino
   KDE. Si aprono nell'incremento in cui la maglia corrispondente può diventare verde, non prima.
2. ⚠ **La scatola `kde` non contiene Plasma**: solo `kwin-wayland` e `xwayland`
   (`Contenitore.kde`). Il prodotto accende una sessione Plasma ⇒ la scatola cresce, dichiarandolo.
3. ⭐ **Un guasto di KDE, inventato e fatto girare** (`fasi/11-…` §3.6): oggi non esiste.

## Gli incrementi

| # | obiettivo | maglia che lo prova | stato |
|---|---|---|---|
| **0** | la baseline | la rete intera | ✅ **PASS** 18 set |

## Le misure

| che cosa | atteso | misurato | data |
|---|---|---|---|
| **CP0** — giro `tutto` sulle quattro scatole, lanciato **sul server** | GNOME verde; su kde/xfce/lxqt solo C1 rosso; guasti tutti presi; un binario solo | ⭐ **come atteso** — vedi sotto | `[M]` 18 set 2026, 17:25→19:38 |

#### CP0 in dettaglio — binario `bfc5936a2b0f` (sorgenti `src/` di `c82c910`), 7 967 s

| | |
|---|---|
| GNOME | ⭐ **tutto verde**: passo 0, C1×10, C2, C3 (+ scena ferma), C4, C5, C6, C7, C8, C8b, C9 |
| kde · xfce · lxqt | passo 0, C5, C7, C8, C9 verdi · ⛔ **C1×10 ROSSO** su tutte e tre (il mandato) · C2 C3 C4 C6 C8b **saltate** dal cancello «solo gnome» (esito 3) |
| rete, sul server | C11 verde (14 voci allineate, **stesso md5 nelle quattro**) · C13 verde · C14 verde (786 s) |
| rete, sul portatile | C10, C12, C15, C16 verdi, C10 col guasto visto — ⚠ **queste quattro vogliono il deposito git**: lanciate sul server danno 2/3 «il terreno non regge», e non è un rosso. Si fanno girare **qui**, nello stesso giro di certificazione |
| ⭐ **guasti innestati** | **25 su 25 visti** (24 sulle scatole, 1 sul portatile) |
| rossi del banco | nessuno |

⚠ **I conti non si confrontano con quelli del 27 agosto**, e va detto perché sembrano diversi: il
`README.md` dice *«58 verdi, 3 rossi, 49 guasti su 49»*, `fasi/11-…` §7-bis.19 dice *«57 · 23 su 25
· 6 esiti 3 · 3 rossi»* — due conteggi diversi dello **stesso** giro. ⇒ Il confronto che vale è
**la forma**: gli unici rossi sono i tre `C1` fuori da GNOME, **com'era allora**. Oggi: 58 esiti 0
sulle scatole (34 verdetti + 24 guasti visti), 3 rossi, e i guasti presi sono 25 su 25.

## ⛔ Che cosa NON ha funzionato

## Che cosa resta [?]

## Il giudizio dell'utente
