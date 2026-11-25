# Giro 1 - GNOME (VM `gnome`, ssh 2361, REMOTIX 8861) - 25/26 nov 2026

Pacchetto: `remotix_1.2.0-1+deb13_amd64.deb` (giro1). Log sul server: `/media/REMOTIX-DEBIAN/log/giro1/gnome/` e
`/media/REMOTIX-DEBIAN/tmp/prove-run/prove/log/gnome-giro1/` (summary.txt, un .out per voce). Procedura: `COME-SI-LANCIA.md`.

## Esito del giro completo (`all.sh gnome --clean`, 46 minuti)
123 PASS, 3 FAIL, 1 BLOCKED, 3 SKIP (SKIP previsti dello strumento: real-greeter, ban/other-addresses, package).

| Voce | Esito | Note |
|---|---|---|
| installazione, servizio, hook PAM | PASS | riga «the local-login hook is in place in /etc/pam.d/common-session»; labwc tirato dentro dai Recommends |
| AppArmor | NOTA | il profilo `remotix_network` e' in **complain** (non enforce): voluto e scritto nei manuali; nessuna prova di enforce |
| base (Chrome, Firefox), lifecycle, multiuser, resilience, audio, clipboard, input (Chrome, Firefox), phone, ban | PASS | tutte le voci |
| desktop/users-shell-and-environment | FAIL NOTO | `pkexec`: SHELL vuoto, nessuna finestra password (noto su GNOME, tutte le distribuzioni); il resto della voce (terminale, HOME, gruppi) a posto |
| media/screen-updates | FAIL | vedi sotto; ripetuto, stesso risultato; causa non stabilita |
| prelocal P1-P6 | PASS | |
| prelocal P7 (terminale con `top`) | FAIL poi PASS dopo correzione dello STRUMENTO | vedi sotto |
| prelocal P8 | BLOCKED | previsto su GNOME |
| rimozione (`apt purge`) e reinstallazione | PASS | nessun file di REMOTIX in /etc /usr /var /root /home (nemmeno `~/.local/state/remotix` degli utenti); utente e gruppo `remotix` tolti; riga PAM tolta; reinstallazione ok |

## media/screen-updates: FAIL (due esecuzioni)
Ritardo costante di circa 1,05-1,2 s fra l'istante in cui il contatore cambia nella sessione e quello in cui lo si vede nel browser:
mediana del primo avvistamento 1083 ms (1238 ms nella seconda esecuzione), eta' dell'immagine al momento dello screenshot 1067 ms,
fine di una raffica sullo schermo dopo 1,02-1,05 s (soglia dello strumento: 1,0 s). Nessun valore perso (161 su 161), nessun passo indietro,
animazione a 60 Hz: 35 fotogrammi/s dipinti. Il registro mostra i fotogrammi tutti inviati (0 abbandonati). Il ritardo e' quasi fisso:
puo' essere del prodotto su GNOME (mutter/encoder), della VM senza monitor o del browser di prova sul server (carico 1,29).
NON stabilito. Il confronto con gli altri tre desktop dice se e' di GNOME. Non allargata la soglia.

## P7 (accesso locale con `gnome-terminal -- top` aperto)
- Misurato dal registro: accesso locale trattenuto in PAM alle 00:07:17, «nothing of its REMOTIX desktop is left (871 ms, closed by its child)».
  Quindi 0,87 s (non i 10,5 s attesi: `top` termina subito alla chiusura della sessione, la strada «forzata» non e' servita).
  Il desktop locale e' arrivato dopo 4 s dal riavvio di gdm3 (autologin del banco).
- Il primo FAIL era dello **strumento**: dopo la chiusura restavano attive, con lo stesso identificativo, due `.slice` VUOTE
  (`app-gnome-session-manager.slice`, `app-org.gnome.Terminal.slice`, senza alcun processo dentro: `cgroup.procs` vuoto) e il `.socket`
  `gnome-keyring-daemon.socket` (condiviso con la sessione locale, sempre in ascolto), perche' il gestore utente `user@UID` resta vivo
  (la sessione locale parte subito). Processi, sessioni logind e unita' con processi: tutto sparito. Correzione: `check-prelocal.py`
  non conta piu' come residuo una slice vuota o un socket (`unit_residue`), e li elenca come nota; aggiunta anche la riga `unit-detail`
  (da quando e' attiva l'unita', chi c'e' nel cgroup) quando resta un residuo vero. Rilanciato: P7 PASS.

## Novita' 1.2.0 viste a mano (utente `bc1`, sessione aperta con `hold.py`)
- Ambiente del desktop remoto (gnome-shell e gestore utente): `LANG=en_US.UTF-8` (lingua di sistema, non `C.UTF-8`); nessun `LC_*`;
  `PATH=/home/bc1/.local/bin:/home/bc1/bin:/usr/local/bin:/usr/bin` (ripiego presente).
- Lingua dell'utente: generato `it_IT.UTF-8` nella VM (`/etc/locale.gen`, resta), `SetLanguage s it_IT.UTF-8` con AccountsService
  (era `""`): nuova sessione remota con `LANG=it_IT.UTF-8` (processo gnome-shell e ambiente del gestore utente). Lingua rimessa a `""`.
- Chiusura della connessione: nel registro, alla chiusura del browser, `the client said farewell ...`, `closed the WebTransport session, code 0x10`
  (o 0x04 per la chiusura voluta dall'accesso locale), poi `child ... is leaving: Connection reset by peer`; la riga `farewell reason=0x10 detail=...`
  compare con il motivo; se il browser sparisce senza saluto: `quic connection ... closed ... dropped without a CONNECTION_CLOSE: idle timeout (silence)`.
- Scala (U4): con `scaling-factor 2` scritto per `bc1` (`gsettings set org.gnome.desktop.interface scaling-factor 2`, sessione chiusa; `monitors.xml`
  assente): il nuovo accesso e' stato ammesso, desktop nato e visto (canvas 1344x768), nessun rifiuto, nessun codice 0x0E, nessun messaggio sulla scala nel registro.
  Dentro la sessione il monitor virtuale `Meta-0` risulta a scala 1.0 mentre la chiave resta `2`. Quindi: il desktop nasce a scala 1, la chiave NON viene
  toccata ne' bloccata dal prodotto (ne' pagina nera ne' errore). Chiave rimessa a `0` (era `0`).
- Primo clic (A4): `check-multiuser` e `check-phone` PASS; gli strumenti non misurano la posizione del primo clic a parte `input/mouse-coordinates`
  e `phone/tap-click-*` (PASS: il clic cade dove sta il puntatore).
- Chi ha il bench autologin: P7 usa l'autologin di gdm3 (`/etc/gdm3/daemon.conf`, rimesso a posto dallo strumento).

## Correzioni agli strumenti
1. `debian13/server/prepara-server-vm.sh`: aggiunti i passi per le prove (chromium, firefox-esr, labwc, wlr-randr, python3-pil, libavcodec61,
   PipeWire con sink nullo, directory runtime, limiti inotify). Provato sul server riavviato: ALL OK.
2. `debian13/prove/check-prelocal.py`: residui «slice vuote / socket» non contati (P7), riga `unit-detail`.
3. `debian13/studio/prove-1.2.0/COME-SI-LANCIA.md`: procedura.

## Stato finale
VM `gnome` col pacchetto 1.2.0 installato (reinstallato dopo il purge, servizio abilitato e acceso come dopo il passo 1), SPENTA, istantanea `giro1`;
Radeon libera. Restano nella VM gli utenti di prova creati dal giro (bc1, pl1-3, ecc.) e il locale it_IT.UTF-8.
Nota: `apt install` dopo il `purge` lascia il servizio `disabled` (come si aspetta un pacchetto Debian): l'ho abilitato io prima dello spegnimento,
poi l'istantanea; il disco ha quindi il servizio abilitato.
