# Giro di conferma unione2 su `kde` (Kubuntu 26.04, KWin/Plasma 6.6.7, box `rxu-kde`) — 18 nov 2026, sera

Pacchetto: `/media/REMOTIX-UBUNTU/pacchetti/unione2/remotix_1.0.0-1+ubuntu26.04_amd64.deb` (SHA-256 `5bfc4da6…`). Giro: `all.sh kde --fresh`,
registri in `/media/REMOTIX-UBUNTU/albero/prove/log/unione2-kde/` (summary.txt scritto alle 21:19, ora del server/CET; il box è in UTC, un'ora indietro).
Nulla di prodotto o prove è stato corretto. Miei script (solo sul server): `/media/REMOTIX-UBUNTU/lavoro/giro2-kde/`
(`m.py`, `e.py` copiati da `lavoro/kde-uscita/`; `k2.sh`, `k3.sh`, `k4.py`, `k5.py`, `k6.py`, `k8.py`, `k9.py`, uscite `*.out`). Istantanee in
`/media/REMOTIX-UBUNTU/albero/prove/shots/` (`g2k-*.png`, `ke-ed61-*.png`).

## 1. Risultato del giro: 121 PASS su 124 righe, 3 FAIL (nessun BLOCKED)
unione1: 111 su 124 (13 FAIL). Confronto riga per riga (stessi 124 nomi, salvo 4 rinominati):

| Riga | unione1 | unione2 | Esito del confronto |
|---|---|---|---|
| lifecycle/logout | FAIL | PASS | non verde → verde: correzione (1) «uscita nei primi secondi». Vedi anche K2 |
| desktop/settings-intact | FAIL | PASS | non verde → verde, stessa correzione (1) («session 1 ended 14 s after Log Out») |
| desktop/reattach-windows-inside | FAIL | PASS | non verde → verde: correzione (3) (misura senza i pixel del pannello): finestra 1783x981 → 1783x983 in 2544x1440 |
| media/codec | FAIL (Firefox, rise 130 px) | PASS | non verde → verde SENZA correzione dedicata: Chrome rise 0 px, Firefox PASS. La riga di unione1 era dunque una misura saltuaria (era classe (e)); resta non spiegata, ma non si è ripetuta |
| input-chrome/mouse-drag, input-firefox/mouse-drag | FAIL | PASS | non verde → verde: correzione (3) (rilascio del tasto registrato) |
| phone/tap-and-half-drag-select | FAIL | PASS | non verde → verde: correzione (3) |
| input-*/page-cad-button | FAIL | (rinominata) `page-cad-hidden` PASS | riga nuova/rinominata, verde |
| input-*/page-ctrl-alt-end | FAIL | (rinominata) `page-ctrl-alt-end-passes` PASS | riga nuova/rinominata, verde |
| input-chrome/page-cad-chain, input-firefox/page-cad-chain | FAIL | FAIL | non verde e lo è ancora: vedi 2 |
| **desktop/canvas-limits** | **PASS** | **FAIL** | **REGRESSIONE APPARENTE** (verde → non verde): vedi 3 |
| tutte le altre 105 righe | PASS | PASS | invariate |

Fuori da KDE nello stesso giro (solo da `summary.txt`): gnome 1 FAIL (`desktop/users-shell-and-environment`), xfce 2 FAIL (`base-firefox/mouse`, `keyboard`), lxqt tutto PASS.
`page-cad-chain` passa su gnome, xfce e lxqt: il FAIL è proprio di KDE.

## 2. page-cad-chain su KDE (FAIL, uguale a unione1: nessuna regressione) — classe (e) non capita, con prove; probabile (c)
Riga (Chrome): «Ctrl+Alt+Del button (diagnostics on) clicked: page dispatched [{'name': 'Ctrl+Alt+Del', 'codes': [29, 56, 111], 'ms': 185919}] but the application saw
['Control_L', 'Alt_L'] and the desktop did not react either in 9 s (focus kept: True, picture unchanged: True)» (`input-chrome.out:22`; Firefox identica, 'ms': 181353).
Su lxqt e xfce la finestra di prova vede `Control_L, Alt_L, Delete`; su GNOME vede Ctrl+Alt e poi il desktop reagisce (il controllo accetta questo caso, riga 563-ish di `check-input.py`).
Su KDE: Delete NON arriva alla finestra (la prende KWin), ma il desktop non fa nulla di visibile. Foto: `shots/input-kde-chrome-20261118-210355-cad.png` (solo la finestra di prova).
Sonda mia (`k6.py`, utente `kk7`, 20:37 UTC, `k6-kk7.out`):
- `kglobalshortcutsrc` dell'utente: `[ksmserver] Log Out=Ctrl+Alt+Del,Ctrl+Alt+Del,Show Logout Screen` — la scorciatoia è registrata (le regole KIOSK scritte da REMOTIX, `session.c:1483`, tolgono solo lock/new session/switch user, non il logout).
- Sul bus dell'utente (`busctl --user monitor`): kglobalaccel emette `globalShortcutPressed ("ksmserver","Log Out")` e subito dopo `globalShortcutReleased` (50 µs di distanza). Dopo non compare nessuna chiamata `promptLogout`, nessun processo `ksmserver-logou*`, nessuna istantanea a 1, 4, 9, 14 s con la schermata di uscita (`g2k-kk7-cad-4s.png`: solo la finestra di prova).
- Stesso esito con l'accordo Ctrl+Alt+Canc dalla tastiera del browser, tenuto premuto 0,4 s e rapido (`k8.py`, utente `kk8`): finestra vede solo `Control_L, Alt_L`; nessun processo greeter.
- Invece `busctl --user call org.kde.LogoutPrompt /LogoutPrompt org.kde.LogoutPrompt promptLogout` mostra subito la schermata «kk7 — Logging out in 26 seconds» (`g2k-kk7-prompt.png`; processo `ksmserver-logou`), e `isShuttingDown` resta false dopo Escape.
Conclusione onesta: il tasto Canc è mangiato da KWin e la scorciatoia raggiunge ksmserver, ma ksmserver non apre la schermata di uscita (via D-Bus la apre). Non so perché (non ho letto il codice di Plasma 6.6.7; non ho verificato se una sessione locale vera la apra). Non è una regressione (uguale in unione1, stessa riga di testo). Probabile (c) se si decide che su KDE Ctrl+Alt+Canc deve mostrare la schermata di uscita come in locale; altrimenti è un limite da accettare/documentare. Non tocca la correzione dell'uscita.

## 3. desktop/canvas-limits (PASS → FAIL) — non riprodotto; classe (e) probabile transitorio (d)
Riga (`desktop.out:16`): solo la PRIMA scena (vista 1280x720 → canvas 1264x720) è NON verde, per «edges WRONG — the white frame is not on all four edges»; quadranti ok; dimensioni tutte ok (pagina 1264x720, desktop nel box 1264x720, viewer 1264x720 scala 1.00); le altre 9 scene (200x150 … 5120x1440) PASS.
Foto `shots/desk-canvas-1280x720-kde-261118-203934.png` (21:39 CET), analizzata pixel per pixel: sul bordo centrale in alto le righe 0-1 sono sfondo scuro (51,79,66), il bianco inizia alla riga 2; in basso il bianco finisce 2 righe prima del bordo (riga 718: 149,183,223 = sfondo); a sinistra il bianco inizia alla colonna 3; a destra termina 2 colonne prima. Cioè la finestra-cornice è davvero più piccola della tela di 2-3 px su tutti i lati (bordi netti, non una scalatura). In unione1 (foto `…-172628.png`) il bianco era alla riga 0.
Ripetuta la stessa scena sulla stessa macchina con utenti nuovi (`k9.py`: vista 1280x720, finestra `geom-window.py frame`, istantanee a 10, 20, 40 s): 2 volte su 2 (`kk95`, `kk96`) il bianco sta esattamente sul bordo (riga/colonna 0 sui quattro lati), `{"ev":"size","w":1264,"h":720}`, rect [0.5, 0, 1264, 720]. Nessun difetto riprodotto. (Due primi tentativi miei, `kk91`/`kk92`/`kk93`/`kk94`, non hanno nemmeno aperto la finestra per un file di log `/tmp/rx-geom.err` di un altro utente non scrivibile: errore mio, non contano.)
Il journal di quel minuto (19:39 UTC) non è più leggibile nel box. Il corpo della correzione (1) (KDE, uscita) non tocca la geometria; il difetto non è nelle altre macchine. Non so spiegarlo: ipotesi, non provata, finestra in fullscreen appena aperta mentre KWin la sistemava, con il giro che girava in parallelo su 4 macchine. Va riprovato con una seconda esecuzione di `check-desktop.py --box kde --only canvas-limits` se si vuole una conferma (non lanciato: i test decide l'utente).

## 4. Verifiche in più (macchina `kde`)
**K1** (righe rosse solo su KDE in unione1), testo per intero dai `.out`:
- `lifecycle/logout`: PASS — «gesture "busctl" -> rc=0 started; client told after 11 s ("the session has ended: the programs were closed"), form back; no process and no logind session of lc2 left; new login "Admitted, new session, canvas 944×496, desktop kde", logind before ['c89 … State=active', 'c90 … manager'] now ['c116 … ', 'c117 …']; session idle (44 ticks/3 s) after 7 s».
- `desktop/settings-intact`: PASS — «user dkf10, 9 seeded value(s) intact, 1 changed by the desktop; session 1 ended 14 s after Log Out; .config/kdeglobals [General/ColorScheme] BreezeDark -> None: written by the desktop's own … not by REMOTIX; REMOTIX's own process wrote caches (not settings) …; 87 new files and 5 changed files in the home after two sessions …».
- `desktop/reattach-windows-inside`: PASS — «canvas (3824, 2160) -> (2544, 1440); the window was 1783x981 at (1020, 578), after the smaller reattach it is 1783x983 at (748, 398) in a picture of 2544x1440 (distance to right/bottom edge 12/58 px); … (entirely inside, same size +-3%)». Nota: con la finestra di questo giro (1783 px, più stretta del nuovo canvas) KWin non l'ha rimpicciolita; in unione1 era 2567 px (più larga del canvas) e il controllo era sbagliato: ora è evitato dalla misura corretta, ma NON è stata riprovata la finestra più larga del canvas.
- `media/codec`: PASS — Chrome 156.0.8078.79 h264 avc1.640033 8 bit, coded 1344x770/1344x768, contrasto 1px/2px/4px 1.00, bordo 10-90% rise 0 px; Firefox 153.7.0 h264 avc1.640033, coded 1392x800, picture 1392… (riga troncata nei miei appunti a 900 car.; il verdetto è PASS per entrambi).

**K2** (Log Out a 16 s dalla nascita, due volte, una alla volta; `m.py`, `k2-kk2a.out`, `k2-kk2b.out`; busctl `org.kde.Shutdown logout`; al gesto c'è in coda il job `132 xdg-desktop-portal.service start running`, cioè lo stesso scenario che in unione1 perdeva l'uscita):
- `kk2a`: client avvisato dopo 14,1 s dal gesto; processi/sessioni logind a 15, 30, 60 s: 15/1, 0/0, 0/0. Journal: 20:21:45.156 systemd «Requested transaction contradicts existing jobs: Transaction for graphical-session.target/stop is destructive (xdg-desktop-portal.service has 'start' job queued…)»; 20:21:45.730 `session [kk2a] Plasma: a logout is under way and KWin is still up (plasma-shutdown ended, ksmserver is shutting down) — plasma-workspace.target is active; giving it 4 s…`; 20:21:49.740 `Plasma logout stopped halfway: stop of graphical-session.target refused (attempt 1, mode fail): …TransactionIsDestructive`; 20:21:52.759 `… accepted (attempt 2, mode fail) — the normal end follows`.
- `kk2b`: client avvisato dopo 13,7 s; 15/1, 0/0, 0/0. Journal: 20:23:12.046 «a logout is under way…», 20:23:16.061 refused (attempt 1), 20:23:19.075 accepted (attempt 2).
- Attesa (zero al più tardi a 60 s): rispettata in entrambe (zero già a 30 s). Prima misura (non richiesta) sul pacchetto, fatta dall'agente della correzione: a T=5 s accettato solo al tentativo 6 (`prova-matrice-5s-nz5x1.out`, avviso a 24,9 s). Qui non ho rifatto la matrice.
Rispetto a unione1 (K2a: 120 s con il desktop vivo, zero avviso): chiuso.

**K3** (lavoro non salvato). `kwrite` non c'era nel box: l'ho installato io (`apt-get install -y kwrite` 4:25.12.3-0ubuntu1 + dipendenze; DICHIARATO, lasciato installato; il pacchetto REMOTIX e `labwc` non toccati).
- Prova A (`e.py` copia, utente `ed61`, `k3-cancel-ed61.out`): kwrite con «unsaved work» (istantanea `ke-ed61-typed.png`), Log Out alle 20:25:52; a 14,4 s clic su «Cancel Logout» nella notifica («The following applications did not close: KWrite — Logging out anyway in 2 minutes»; coordinate 1138,651 verificate sulla foto `ke-ed61-beforeclick.png`, nella finestra c'è anche il dialogo «Salva / Scarta / Annulla» di kwrite). Esito: `isShuttingDown` = false a 20, 60, 100, 115, 125, 150 s; kwin vivo, 43 processi e 2 sessioni a 20-125 s; a 150 s 41 processi, 2 sessioni (due processi in meno rispetto a prima, non identificati). Journal: `20:26:06 Plasma: plasma-shutdown ended and ksmserver is not shutting down (logout cancelled, or not a logout) — nothing is forced`. Nessuna riga di forzatura (halfway/force/kill) nel journal dell'utente; il solo stop di KWin (20:29:04, `reason: SIGTERM…`) è la fine della prova (190 s dopo il gesto, `rig.stop`). Sessione viva a 150 s: SÌ.
- Prova B (utente `ed62`, `k3-none-ed62.out`): kwrite non salvato, Log Out alle 20:30:14, senza toccare nulla: `isShuttingDown` = true a 20, 60, 100, 115 s, 44 processi, 2 sessioni, nessuna forzatura; KWin esce da sé alle 20:32:15 (121 s dopo il gesto), `KWIN IS GONE`, client avvisato a 122,7 s, 0 processi e 0 sessioni a 150 s. Nel journal di ed62 nessuna riga «halfway/forzatura» prima di quel momento (ho controllato `logout|force|halfway|plasma|SIGKILL|ended|kill`).

**K4** (utente nuovo, istantanee a 10 s e 40 s dalla nascita; `k4-nk41.out`, `k4-nk42.out`, `shots/g2k-nk41-10s.png`, `-40s`, `g2k-nk42-10s.png`, `-40s`; viste a occhio una per una): a 10 s solo lo sfondo Kubuntu a tutto schermo (pannello e icone non ancora comparsi); a 40 s sfondo, icone «HOW-TO Guides» e «Kubuntu Website», pannello in basso con orologio. Nessuna finestra di KWallet, di password, di crash o assistente in nessuna delle quattro. Processi a 40 s: `drkonqi-coredump-*`, `polkit-kde-auth`, `ksecretd` (compare tra 10 e 40 s), `kwalletd6` mai visto. Journal: `plasma-kwallet-pam.service … Started`, portale kwallet attivato; solo i servizi drkonqi di sfondo (nessun crash registrato, nessuna riga `crash|coredump` tranne le unità drkonqi che partono "skipped, unmet condition").

**K5** (`k5.py`, utente `kk5`, sessione viva): processo `labwc` pid 114029, `runuser -u kk5 -- readlink /proc/114029/exe` = `/usr/libexec/remotix/labwc`; `sha256sum /proc/114029/exe` (letto come l'utente) = `47e54654ab6c3b7307e2c8f2cea53bab544656ee60d9dd7a914941717997dcb4`; il file installato ha lo stesso valore; il `.deb` di unione2 estratto (`dpkg-deb --fsys-tarfile | tar -xO ./usr/libexec/remotix/labwc | sha256sum`) = `47e54654…dcb4`. Riga di comando `labwc -C /run/user/1051/remotix-kwin-host/labwc`; catena: remotix → kwin_wayland_wrapper → labwc → kwin_wayland. (Letto come root, `/proc/pid/exe` dà «Permission denied»: ci vuole l'utente.) Il valore coincide anche con quello di unione1: il labwc non è cambiato fra i due pacchetti.

## 5. Che cosa NON ho potuto vedere / limiti
- Causa del mancato avvio della schermata di uscita con Ctrl+Alt+Canc su KDE non stabilita; non provato su una sessione Plasma locale vera.
- canvas-limits: non riprodotto (2 ripetizioni pulite); il journal del minuto del guasto non è disponibile.
- K3: non ho provato «Salva» né «Scarta» (non richiesto); i 2 processi in meno a 150 s nella prova A non sono stati identificati. Non ho ripetuto la matrice dei tempi (5/10/25/40/61 s) di `kde-uscita`.
- reattach-windows-inside: non riprovato con una finestra più larga del nuovo canvas.
- Firefox su media/codec: non rieseguito oltre la riga del giro.
- Stato lasciato nel box: kwrite installato (+ dipendenze apt); utenti di prova `kk2a kk2b ed61 ed62 nk41 nk42 kk5 kk7 kk8 kk91-kk96` (senza processi né sessioni), file `/tmp/rx-geom-*`, `/tmp/mon-kk7.txt`, `/tmp/k-*.out`. Nessun file del pacchetto cambiato.
