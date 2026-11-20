# REMOTIX per Ubuntu 26.04 — stato (20 nov 2026)

## Chiuso

- 20 nov 2026: riordino del repo. Un solo ramo `main`; questo albero vive in `ubuntu26.04/` (storia del ramo `ubuntu-26.04` conservata). Le voci precedenti dicono «ramo» per ciò che ora è una cartella.

- REMOTIX 1.0.0 per Ubuntu 26.04 (Ubuntu/GNOME, Kubuntu/KDE, Xubuntu/XFCE, Lubuntu/LXQt). Pacchetto provato a mano dal
  proprietario sulle quattro macchine virtuali e sulle quattro live vere: `unione10` (sha256 `07b270e8…63aa`), commit
  `50d997b`. Giro automatico completo su GNOME (VM, `unione10`): 120 PASS, 2 FAIL (la riga nota
  `desktop/users-shell-and-environment`/pkexec e un falso rosso del banco), 1 BLOCKED (ripetuto due volte PASS), 3 SKIP.
- Difetto polkit del riavvio (registro C6; trovato dal proprietario sul tablet Debian, «è un bug e va corretto», la
  versione resta 1.0.0): regola a 19 azioni, controlli `power-implied` e `power-local-seat`, revisore APPROVATO. Pacchetto
  `unione11` (sha256 `08772d85…36ab`): provato solo sulla VM di Ubuntu, controllo del desktop prima/dopo (FAIL → PASS);
  nessun giro completo e nessuna prova sulle altre tre varianti. Su Debian: stessa correzione in `debian13/`, pacchetto
  ricostruito installato sul tablet e verificato dal posto dell'utente locale (riavvio e spegnimento negati).
- Manuale tecnico di Ubuntu (`manuals/Technical Manual — Ubuntu 26.04.html`, 25 capitoli) e manuale utente di Ubuntu
  (`manuals/User Manual — Ubuntu 26.04.html`, 6 capitoli): scritti, revisore APPROVATO, `build.py --check` verde.
  Scelta: un manuale per distribuzione, perché ogni manuale è controllato contro il codice della propria cartella. Manca la
  lettura del proprietario.
- La storia completa del lavoro è in `docs/STORIA-ubuntu-26.04.md`.

## Server (20 nov, per ordine del proprietario)

Le macchine virtuali di prova e le cartelle `/media/REMOTIX-UBUNTU` e `/media/REMOTIX-DEBIAN` sono state cancellate
(comprese le immagini di costruzione). Il banco si ricostruisce con `server/prepara-server.sh` e `server/vm-radeon*.sh`
(ISO in `/media/DOWNLOAD`). I pacchetti finali (`unione10`, `unione11`, Debian ricostruito) e i registri testuali delle
prove sono sul tablet in `~/remotix-salvati-dal-server/`. I percorsi del server citati nei manuali e nel registro
indicano dove stavano le prove: non esistono più.

## Da decidere / da fare (proprietario)

- Pubblicazione di Ubuntu (sito, GitHub) e del pacchetto Debian corretto (stessa versione 1.0.0: avvisare chi l'ha già
  installata?). Niente si pubblica finché non lo dice lui.
- `docs/STORIA-ubuntu-26.04.md` contiene l'indirizzo di rete di casa e la password di prova (testo già pubblico dal
  commit `50d997b`): lasciare o togliere.
- Riordino del repo: FATTO il 20 nov 2026 (un solo ramo `main`, cartelle `debian13/` e `ubuntu26.04/`; questo albero è `ubuntu26.04/`).
  Entrambi i manuali sono per distribuzione. Sito: preparato in locale (piano nel `PIANO.md` di `debian13/`). La costruzione non è stata riprovata dopo il riordino.
- Poi Fedora, poi Arch.

## Piccole cose del prodotto, non bloccanti, nessuna fatta

La riga di registro del ripiego dconf dice «three layers compiled now» anche quando `dconf` manca (`session.c` ~2384);
l'avviso del postinst su labwc non scatta su Xubuntu (c'è `gnome-shell`); commenti rimasti indietro («older than the
keyfiles» in `session.h`/`session.c`; «Debian trixie only» in `CLAUDE.md`; «DEBIAN 13 ONLY» in `src/remotix.pam`;
systemd 257 in `local_login.c`; ngtcp2/nghttp3 nel `Makefile`; «i desktop sopravvivono allo stop del servizio»);
`prove/check-package.py` non conosce `/etc/dconf/db/remotix` e pretende AppArmor in enforce. Aperti nel registro: E3, E4.
