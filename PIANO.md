# PIANO — KDE recente (KWin ≥ 6.5) funzionante: due correzioni (ramo `kde-ospite`, da v15c)

Trovato il 28 ott 2026 sul noleggio NVIDIA, ma NON dipende dalla scheda: riguarda ogni distribuzione con
KWin 6.5 o più recente (Ubuntu 26.04 ha KWin 6.6.6). Debian 13 (KWin 6.3) non è toccata.
Prove e misure: `/media/REMOTIX-15/lavori/NVIDIA-28ott-da-correggere.md`, punti 7-13.

## Obiettivo
Su KDE con KWin ≥ 6.5 le finestre si aggiornano (oggi restano ferme al primo fotogramma) e lo schermo
remoto segue i cambiamenti senza ritardo, come su XFCE e su Debian 13.

## Correzione A — REMOTIX: saltare i fotogrammi «senza cambiamenti» (piccola, in `src/capture.c`)
- Fatto: KWin 6.6 manda ~60 immagini/s anche a schermo fermo e dichiara «niente è cambiato» (meta
  VideoDamage presente, prima regione vuota). Oggi REMOTIX lo legge come «danno assente» e codifica tutto:
  53 fotogrammi/s di nulla, chi guarda resta indietro di 1-3 s (F-003 rosso).
- Correzione: in `look_damage()` distinguere «meta assente» (si codifica, come oggi) da «meta presente e
  vuoto» (fotogramma uguale al precedente ⇒ si restituisce il buffer a PipeWire senza codificarlo).
  Mai saltare: il primo fotogramma dopo l'avvio o dopo una rinegoziazione/cambio misura, e i fotogrammi
  che portano solo il cursore (restano gestiti come oggi). Un contatore nel riepilogo che già esiste.
- Provato sul noleggio con una versione di prova: F-003 KDE PASS, 5 fotogrammi/s invece di 53, ritardo ~0.

## Correzione B — il labwc che ospita KWin con wlroots corretto (opzione 2, decisa con l'utente)
- Fatto: KWin ≥ 6.5 mette come fondo della sua finestra un pixel nero speciale e il contenuto in
  sottofinestre; wlroots non dichiara mai «presentato» quel fondo ⇒ KWin dà ai programmi un orologio a 0 ⇒
  Firefox crede la finestra coperta e smette di disegnare (28 test KDE BLOCKED).
- Correzione: wlroots della distribuzione + una patch di poche righe (`types/scene/surface.c`, nel
  `frame_done`: la radice di una superficie mostrata conta come presentata). Provata sul noleggio:
  3163 presented / 5 discarded; suite KDE da 15 PASS + 28 BLOCKED a 21 PASS (Firefox) e 20 (Chrome), gli
  altri rossi sono del banco (sotto).
- Come si distribuisce (deciso la sera del 28 ott, dopo il passo 1): un LABWC NOSTRO con dentro la wlroots
  corretta LEGATA STATICAMENTE, installato come `/usr/lib/remotix/labwc` e usato SOLO per ospitare KWin
  (`kwin.c` lo sa già fare: `make LABWC=/usr/lib/remotix/labwc`, DECISIONI §10.43). Versioni fisse, le stesse
  provate sul noleggio: labwc 0.9.3 + wlroots 0.19.2 + la nostra patch (`packaging/labwc-ospite/`: VERSIONI con
  sha256, patch, script di costruzione comune). Così NON dipendiamo dalla wlroots di ciascuna distribuzione
  (0.18/0.19/0.20) né dal suo ABI. XFCE e LXQt continuano a usare il labwc della distribuzione.
  Le patch per 0.18/0.19/0.20 restano pronte per le segnalazioni a monte.
  Alma: oggi costruisce labwc 0.8.4 su wlroots 0.18 EPEL ⇒ passa allo stesso labwc ospite.
- Dove: le 5 distribuzioni con KWin ≥ 6.5 (tabella). Debian 13 e Leap 16 restano come sono.

## Distribuzioni toccate (passo 1, verificato il 28 ott nei contenitori di costruzione)
| Distribuzione | KWin | labwc | wlroots | Serve la correzione B |
|---|---|---|---|---|
| Debian 13 | 6.3.6 | 0.8.3 | 0.18.2 | no |
| Leap 16 | 6.4.2 | 0.8.1 | 0.18 | no |
| Ubuntu 26.04 | 6.6.6 | 0.9.3 | 0.19.2 | sì |
| Alma 10 | 6.6.4 | nostro 0.8.4 | 0.18.2 (EPEL) | sì |
| Fedora 44 | 6.7.5 | 0.9.6 | 0.20.2 | sì |
| Tumbleweed | 6.8.1 | (0.20.2?) | 0.20 | sì |
| Arch | 6.8.1 | (0.20.2?) | 0.20 | sì |
⇒ la patch va scritta per tre versioni di wlroots: 0.18, 0.19, 0.20 (Debian e Leap: nessun cambiamento).

## Passi
1. (fatto) Versioni per distribuzione: tabella sopra.
2. Correzione A (programmatore) + test unitari di `look_damage` (meta assente / vuoto / parziale / pieno).
3. Correzione B: `packaging/labwc-ospite/` (VERSIONI + sha256 + patch + build.sh: labwc con wlroots
   statico, opzioni minime come per Alma), chiamato dai pacchetti deb (Ubuntu 26.04), rpm (Fedora 44, Alma 10,
   Tumbleweed), arch; `make LABWC=/usr/lib/remotix/labwc` in quei pacchetti. Licenze: labwc GPL-2.0 (sorgente
   pubblicato come per Alma), wlroots MIT, in THIRD-PARTY-LICENSES.
4. Revisore su A e B.
5. Prove: a casa la suite KDE su Ubuntu 26.04 (box) e la suite intera come oggi (nessun peggioramento:
   702/704); se serve, una giornata NVIDIA per ripetere la suite KDE.
6. Segnalazioni a wlroots e KWin: testo pronto, invio solo con l'ok dell'utente.

## Rischi
- La wlroots nostra va aggiornata quando la distribuzione aggiorna la sua (stessa versione/ABI di labwc).
- Saltare fotogrammi con un produttore diverso da KWin: si salta solo il caso «meta presente e vuoto»,
  che Mutter non manda; il resto resta identico.
- Il pannello KDE 6.6 traslucido inganna il giudice di F-018 (banco, non prodotto).

## Criteri di completamento
- Suite KDE su Ubuntu 26.04: nessun BLOCKED per finestra ferma, F-003 PASS.
- Suite intera a casa invariata (702/704), nessun peggioramento di prestazioni su XFCE/LXQt/GNOME.
- Revisore APPROVATO.

## Fuori da questo piano (banco, a parte)
- `DESKTOP_NV=xfce` avvia KDE se è installato, e lo registra come xfce.
- F-018: giudice del pannello basato sul colore (falso rosso con pannello traslucido).
- F-013 con Firefox su NVIDIA: il browser che guarda decodifica il 4K in software (con Chrome PASS).
- Punti 1-3 del file degli appunti (grub, passi rossi saltati, segfault di 19-compare).
