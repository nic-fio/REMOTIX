# Giro unione2 su `lxqt` (Lubuntu 26.04, LXQt 2.3, box `rxu-lxqt`) — 18 nov 2026 (notte)

Pacchetto: `/media/REMOTIX-UBUNTU/pacchetti/unione2/remotix_1.0.0-1+ubuntu26.04_amd64.deb` (riga `fresh | PASS`).
Registri: `/media/REMOTIX-UBUNTU/albero/prove/log/unione2-lxqt/` (`summary.txt`, `<controllo>.out`, `sweep.out`: «34 test user(s) ended»).
Verifiche in più: script e istantanee in `/media/REMOTIX-UBUNTU/lavoro/giro2-lxqt/` (`l1.py/.out`, `l1b.py/.out`, `snap-*.png`, `snapb-*.png`).
Orologio del box = orologio del server meno 1 ora (orologio nelle istantanee: 20:17 = 21:17 server).

## 1. Esito: ALL PASS, 124 righe su 124 (unione1: 117 su 124)

Confronto riga per riga (`diff` delle due `summary.txt`, senza le intestazioni): le righe che differiscono sono ESATTAMENTE 7, tutte FAIL -> PASS; tutte le altre 117 erano PASS e sono PASS. **Nessuna regressione.** Il numero di righe è lo stesso (124).

| unione1 (FAIL) | unione2 | Chi l'ha chiusa |
|---|---|---|
| `input-chrome/mouse-drag` | PASS | correzione strumenti (3): rilascio del tasto registrato |
| `input-firefox/mouse-drag` | PASS | idem |
| `phone/tap-and-half-drag-select` | PASS | idem |
| `input-chrome/page-cad-button` | rinominata `page-cad-hidden`, PASS | correzione strumenti (3): il controllo ora verifica che il pulsante NON si veda |
| `input-firefox/page-cad-button` | rinominata `page-cad-hidden`, PASS | idem |
| `input-chrome/page-ctrl-alt-end` | rinominata `page-ctrl-alt-end-passes`, PASS | idem |
| `input-firefox/page-ctrl-alt-end` | rinominata `page-ctrl-alt-end-passes`, PASS | idem |

Righe nuove (non rinominate): nessuna. Righe tolte: nessuna oltre alle 4 rinominate. Nessuna riga non PASS in unione2, quindi niente da classificare.
Resta fuori dal confronto la correzione (2) (picom) perché nessuna riga la misura: vedi L1. La correzione (1) è di KDE, non riguarda questa macchina.

## 2. Verifiche in più

### L1 — finestra «Crash Report»: la finestra di picom NON c'è più; ma ne è comparsa un'ALTRA («Lubuntu Update crashed too many times»)
Script `l1.py`: per ogni utente, due sessioni (la seconda dopo un Log Out vero di `lxqt-session`), istantanee del canvas (1344x768) a 10, 20, 40 s dal login, `pgrep picom`, journal dell'utente.

**Utente NUOVO `nl1` (uid 1036), sessione 1 e 2 — pulito.**
- s1 a 10 s: sfondo Lubuntu (albero con stella, blu notte), icone Computer / Lubuntu Manual / Network / cartella `nl1` / Trash, pannello in basso (menu, «1», lanciatori, area di notifica, orologio 20:17); in alto a destra la notifica «lubuntu-update: Updates available! 3 to upgrade…». Nessuna finestra di errore, nessuna richiesta di password/portachiavi/assistente. A 20 s e 40 s: stessa immagine, la notifica è sparita (resta una campanella nel vassoio). Nessuna finestra.
- s2 a 10 s, 20 s, 40 s: identiche (notifica a 10 s, poi sparita). Nessuna finestra.
- journal `_UID=1036`: s1 una riga `picom: an X11 composition manager, not started in the remote session (labwc composes)`; dopo s2 due righe (una per sessione). `crashed too many`: 0. Nessun processo `picom` (`pgrep -u nl1 -ax picom` vuoto a 10/20/40 s in entrambe).
- Confronto con `/media/REMOTIX-UBUNTU/lavoro/giro-lxqt/desktop-lxqt.png` (unione1): lì, al centro, la finestra «Crash Report — X Compositor crashed too many times. Its autorestart has been disabled until next login.» con OK e voce «Crash Report» nella taskbar; ora non c'è.

**Utente GIÀ USATO `bc1` (uid 1002, usato dal giro dalle 19:33) — la finestra di picom non c'è, ma c'è un'altra finestra «Crash Report».**
- s1 e s2, a 10, 20 e 40 s (6 istantanee, tutte uguali): al centro «**Lubuntu Update** crashed too many times. Its autorestart has been disabled until next login.» (stesso aspetto della finestra vecchia, con OK; voce «Crash Report» nella taskbar; senza notifica). Stato del processo: `lubuntu-update` ASSENTE nell'elenco dei processi di bc1 a 40 s in entrambe le sessioni. `lxqt-session` l'ha rilanciato fino al limite, poi il dialogo.
- `picom`: nessun processo; journal `_UID=1002`: `picom: … not started …` una riga per sessione (3 dopo s1 = 2 sessioni del giro + questa; 4 dopo s2); `crashed too many`: 0 nel journal (il messaggio di lxqt-session non finisce nel journal: la prova è l'istantanea).
- **Non riproducibile subito dopo** (`l1b.py`, 4 sessioni di 25 s con campionamento ogni 0,4 s di `pgrep lubuntu-update`): `bc1` 21:22 — `lubuntu-update` vivo da +0,8 s, nessuna finestra (`snapb-bc1-212245.png`: desktop pulito, nessuna notifica); `nl1` 21:23 — vivo da +0,3 s; `nl2` (utente nuovo) 21:24 — vivo da +0,8 s; `bc1` 21:24 — vivo da +0,3 s. In tutte, nessun crash, nessuna finestra, alla fine albero di processi con `lubuntu-update` figlio di `lxqt-session`. Il dialogo non è comparso nelle 6 sessioni successive (4 qui + `nl1` 2 sessioni prima).
- Classe: **(e) non capita**, intermittente. Lo vedo solo in 2 sessioni di `bc1` consecutive alle 21:18:57 e 21:19:59 (ora server), subito dopo la fine del giro (21:16), non nelle sessioni di `nl1` pochi minuti prima né in quelle dopo. Non c'è traccia del crash né nel journal (nessuna riga `lubuntu-update`), né in `/var/crash`, né in `coredump`. Il pacchetto `lubuntu-update-notifier` e `/etc/xdg/xdg-Lubuntu/autostart/lubuntu-update*.desktop` (`Exec=/usr/bin/lubuntu-update`, `X-LXQt-Module=true`) non sono di REMOTIX. Non so se il crash dipenda da REMOTIX (per esempio una gara all'avvio con il bus/portale o con `lxqt-notificationd`) o dal programma stesso (controllo aggiornamenti): non l'ho dimostrato. Suggerimento per chi indaga: ripetere con molte sessioni di `bc1` e registrare `lubuntu-update` con `strace -f`/`QT_LOGGING_RULES`; confrontare con un login locale di Lubuntu. NON è picom.
- Sintesi L1: richiesta soddisfatta per picom (finestra assente, 1 riga `not started` a sessione, 0 `crashed too many` nel journal, 0 processi picom, su utente nuovo e usato, prima e seconda sessione); **ma in 2 sessioni su 8 dell'utente usato è comparsa un'altra finestra di crash (Lubuntu Update)**, che la verifica «nessuna finestra di errore» deve considerare un difetto da non chiudere come PASS.

### L2 — righe degli strumenti (dai `.out` di unione2, per intero)
```
PASS mouse-drag - left to right: press at fx 0.010 release at fx 0.990, 13 motion events, selected 'alpha beta gamma'; right to left: press at fx 0.990 release at fx 0.010, 13 motion events, selected 'alpha beta gamma'      [Chrome]
PASS mouse-drag - left to right: press at fx 0.009 release at fx 0.990, 37 motion events, selected 'alpha beta gamma'; right to left: press at fx 0.990 release at fx 0.009, 37 motion events, selected 'alpha beta gamma'      [Firefox]
PASS tap-and-half-drag-select - tap then, within the half-second, a finger down that dragged right: the tap clicked (press at fx 0.051), the second contact pressed the left button at fx 0.051 and held it while the pointer moved (14 motion events) and released at fx 0.472; the entry selected 'help '
PASS page-cad-hidden - outside diagnostics the page shows no Ctrl+Alt+Del / Ctrl+Alt+End button and no control that opens one (in the page but not displayed: ['shortcuts-open'])      [Chrome e Firefox, testo identico]
PASS page-cad-chain - with the page's diagnostics on (service route ?logbook) the Ctrl+Alt+Del button sends the three keys: the application saw ['Control_L', 'Alt_L', 'Delete']; page dispatched [{'name': 'Ctrl+Alt+Del', 'codes': [29, 56, 111], 'ms': 181287}]      [Chrome; Firefox: 'ms': 175295]
PASS page-ctrl-alt-end-passes - Ctrl+Alt+End typed on the client keyboard: no confirmation, the session is still on, the desktop application received ['Control_L', 'Alt_L', 'End'], End carrying modifiers ['ctrl', 'alt']      [Chrome e Firefox, testo identico]
```
Il rilascio è ora registrato in entrambe le direzioni (fx 0.990 / 0.010 e 0.990 / 0.009): la firma «release at fx -1.000» di unione1 è scomparsa. Il valore `ms` di `page-cad-chain` (181287 / 175295) è un timestamp della pagina, non una durata.

### L3 — fuori dalla sessione remota: PASS
Da `./box.sh ssh lxqt` (shell di root, non sessione remota): `command -v picom` = `/usr/bin/picom`; `-rwxr-xr-x 1 root root 831024 Jan 27 2026 /usr/bin/picom`; `file`: ELF 64-bit LSB pie executable (binario, non script); `dpkg -S /usr/bin/picom` = `picom: /usr/bin/picom` (pacchetto Ubuntu, non remotix); `type -a picom`: solo `/usr/bin/picom` (e il link `/bin/picom`). `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`: `/usr/local/bin` e `/usr/local/sbin` contengono solo gli strumenti del box (`box-common`, `box-gruppi`, `box-identity`, `box-set-dm`), nessuna riga di `remotix` in nessun file di `/usr/local/{bin,sbin}`, `/usr/{bin,sbin}`, `/{bin,sbin}` (`grep -l remotix`: vuoto); `dpkg -L remotix` non elenca nulla sotto `bin/`/`sbin/`. A sessioni chiuse `/run/user/*/remotix/bin-lxqt` non esiste: lo script sostitutivo vive solo in `/run/user/<uid>/remotix/bin-lxqt`, dentro il PATH della sessione remota.

### L4 — residui a fine giro: nessuno
Dopo il giro (21:16) e dopo le mie sessioni (21:26): `loginctl list-sessions` = solo due sessioni root (`c1554 user`, `c1555 manager-early`, quelle della mia shell ssh); `ps -eo uid,user,pid,comm | awk '$1>=1000'` = vuoto, nessun processo di utenti di prova. `sweep.out` del giro: «sweep lxqt: 34 test user(s) ended».

## 3. Che cosa NON è stato visto
- La causa del crash di `lubuntu-update` su `bc1` (intermittente, 2 sessioni su 8; non riprodotto nelle successive 6).
- Se `lubuntu-update` crasha anche in un accesso locale di Lubuntu (nel box non c'è).
- Il messaggio «crashed too many» non compare mai nel journal: l'assenza del dialogo di picom è provata dalle istantanee e dall'assenza di processi/righe, non da una riga di registro.
- `needrestart` (già non visto in unione1) non riguarda questo giro.

## 4. Cambiamenti nel box per le verifiche (da dichiarare)
Creati dagli strumenti (`ensure_user`): `nl1` (uid 1036), `nl2` (uid 1037), con le loro home (file di `/home/nl1`, `/home/nl2`); riusato `bc1` (già del giro; la sua home ha ora i file di 4 sessioni in più, `~/.config/Qlipper` ecc.). Sessioni chiuse con Log Out a fine prova, nessun processo rimasto. Pacchetto non reinstallato, nessun `box.sh reset`, nessun file di sistema toccato. Gli script `l1.py` e `l1b.py` sono in `/media/REMOTIX-UBUNTU/lavoro/giro2-lxqt/`.
