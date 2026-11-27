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

**Chiusura (20 nov 2026, sera; ordine del proprietario «chiudi i punti aperti»).** Pubblicati: sul sito il pacchetto Debian
corretto (sha256 `421b0e4b…cf92`, con nota nella storia della pagina e invito a reinstallare) e, per Ubuntu, il sorgente di
labwc/wlroots accanto al pacchetto; su GitHub i rilasci `debian13-1.0.0` e `ubuntu26.04-1.0.0` (pacchetti, manuali, sorgente
di labwc); il rilascio `v1.0.0` resta con una nota che rimanda a quello nuovo. Repo riordinato: un ramo, `debian13/` e
`ubuntu26.04/`. I sorgenti del sito restano fuori dal repo per scelta del proprietario. Prossimo lavoro: Fedora.

---

## Versione 1.0.1 — tastiera (21 nov 2026)

Nata da una prova del proprietario: da remoto, dentro QEMU, alcuni caratteri non uscivano o uscivano sbagliati.
QEMU (come altre macchine virtuali) legge i tasti grezzi, quindi mostra due difetti che nei programmi normali non si vedono.

### Parte A — tasti speciali (FATTA, in attesa della sola pubblicazione)
- **Difetto.** Per fare `$`, `(`, `)`, `=`, `€`, `±` il server sceglieva tasti «speciali» che su una tastiera da PC non
  esistono (un tasto solo batteva Shift+tasto). Dentro QEMU il carattere spariva.
- **Correzione.** In `src/keyboard.c` i tasti di una tastiera normale vengono sempre prima; quelli speciali restano come
  ultima scelta. Revisore: APPROVATO.
- **Verifica.** Confronto a tappeto sul server, codice vero, 98 tastiere, tabelle di Debian 13 e di Ubuntu 26.04: su 13.311
  combinazioni ne cambiano 359, tutte e solo di quei sei caratteri; nessun carattere perso. Pacchetto costruito, controlli
  tutti superati. Provato dal proprietario su Debian dentro QEMU con la sessione americana: funziona.

### Parte B — scelta della tastiera nella maschera di accesso (FATTA; OK del proprietario il 21 nov)
- **Difetto.** La pagina indovina la tastiera dalla lingua del browser. Chi ha browser italiano e tastiera americana (il
  proprietario) ottiene una sessione italiana: dentro QEMU escono caratteri diversi da quelli premuti, e le scorciatoie
  con Ctrl/Alt possono cadere su un altro tasto. Oggi l'unico rimedio è cambiare lingua al browser.
- **Obiettivo.** Nella maschera di accesso, sotto la password, un menu «Keyboard» con cui l'utente dice che tastiera ha.

**Come funziona**
1. Il menu nasce **preimpostato sulla tastiera che risulta dalla lingua del browser** (proposta del proprietario, 21 nov,
   al posto di una voce «Automatic»): chi non tocca nulla ottiene esattamente la tastiera di oggi.
2. Dalla lista si cambia: le tastiere per nome (English (US), English (UK), Italian, German, French, Spanish, …), le
   stesse che la pagina conosce già oggi, una trentina, in ordine alfabetico.
3. Una riga di aiuto sotto il campo dice da dove viene il valore («dalla lingua del browser, cambiala se la tua
   tastiera è diversa»; dopo una scelta: «scelta tua, ricordata su questo dispositivo»).
3-bis. La scelta fatta a mano viene ricordata in quel browser (è una proprietà del dispositivo, non dell'utente): al
   collegamento successivo è già selezionata. Se il browser non permette di ricordarla, si riparte dalla lingua del
   browser, senza errori. Esempio approvato dal proprietario il 21 nov («ok, aggiorna il piano e procedi»).
4. La scelta viaggia verso il server nello stesso messaggio di oggi: **nessuna modifica al server né al protocollo**,
   cambia solo la pagina. Il server rifiuta già, con un messaggio, una tastiera che il sistema non conosce.
5. La tastiera vale per quel collegamento; per cambiarla ci si scollega e si rientra.

**File.** `src/page.html` (maschera, funzione che sceglie la tastiera, memoria della scelta). Poi una riga in
`docs/DECISIONS.md` e la voce in `docs/REGISTRO-problemi.md`. Manuale utente: una frase, al momento della pubblicazione.

**Fuori da questo lavoro.** Le varianti (per esempio «US internazionale») e gli accenti composti, già dichiarati fuori;
il cambio di tastiera a sessione aperta.

**Rischi.**
- Una scelta sbagliata dell'utente dà scorciatoie sbagliate: è lo stesso effetto di oggi, ma ora rimediabile dal menu.
- La maschera è vista anche dal telefono: il menu non deve rovinare la disposizione su schermi piccoli.
- La pagina di Debian e quella di Ubuntu differiscono in pochi punti: la modifica va fatta uguale in entrambe.

**Fatto quando.**
- Con browser in italiano e scelta «English (US)», la sessione risulta americana e dentro QEMU i caratteri escono giusti.
- Senza toccare il menu il comportamento è identico alla 1.0.0.
- La scelta è ancora lì dopo aver chiuso e riaperto il browser.
- Il revisore dà APPROVATO e il proprietario ha provato su Debian (sul server) e su Ubuntu (macchine virtuali).

**Versione.** La parte B esce dentro la 1.0.1 (non tocca il server, e la 1.0.1 non è ancora pubblicata); il proprietario
può ancora chiedere di separarla in una 1.0.2.

**Stato (21 nov 2026).** Parti A e B scritte, revisore APPROVATO per entrambe, pacchetti `1.0.1-1` costruiti per Debian 13
e Ubuntu 26.04 (cartelle `pacchetti/1.0.1-con-tastiera` sul server; controlli tutti superati). **Provato dal proprietario
su Debian 13**, dentro QEMU, su GNOME e su XFCE (le due strade dei tasti): Chrome in italiano con tastiera scelta «English
(US)» e Firefox in inglese senza toccare il menu — tutti i caratteri giusti. **Provato dal proprietario su Ubuntu 26.04**, nella macchina virtuale `xubuntu` (XFCE) ricostruita
dalla ISO 26.04.1, e poi nella macchina `ubuntu` (GNOME), ciascuna con un sistema avviato dentro QEMU: la tastiera funziona in
entrambe. Codice nel repo (commit del 21 nov).

**Pubblicazione (21 nov 2026, ordine del proprietario «pubblica»).** Manuali utente e tecnico delle due distribuzioni
aggiornati alla 1.0.1 e rigenerati (revisore: APPROVATO al secondo giro; `build.py --check`: allineati). Pacchetti pubblicati,
costruiti con `SOURCE_DATE_EPOCH=1795252771 RX_VERSION=1.0.1 RX_REVISION=1`:
`remotix_1.0.1-1+deb13_amd64.deb` sha256 `07a7bf7b2a7a0acfe53c5fed804480c3f39cd1673a0463a6626bb5182051939f`;
`remotix_1.0.1-1+ubuntu26.04_amd64.deb` sha256 `cd3b6c72d56eba1c62f3817106f49d2a9301af3110f0cca89b89e3150ff2976f`;
sorgente di labwc `remotix-1.0.1-labwc-source.tar.gz` sha256 `bf6c3ab8ad4a01103c9bb8ecd91f397850086071729896cb2aca49c332edfb09`.
Sul sito: pagine di Debian 13 e Ubuntu 26.04 alla 1.0.1 con la voce «1.0.1 — the keyboard» nella storia, manuali e pacchetti
nuovi (quelli della 1.0.0 restano scaricabili). Su GitHub: rilasci `debian13-1.0.1` e `ubuntu26.04-1.0.1`.
Per la 1.0.1 non è stato fatto un giro completo di prove automatiche: valgono il confronto sulle 98 tastiere e le prove
a mano del proprietario. Prossimo lavoro: Fedora, che parte da questo codice.

---

## Versione 1.2.0 (26–27 nov 2026) — riepilogo

Ubuntu 26.04 portato dalla 1.0.1 alla 1.2.0, allineato a Fedora 45 e Debian 13 dove Ubuntu lo permette. Il piano
completo è nella storia di git (questo file, ramo `ubuntu-1.2.0`); i dettagli sono in `docs/REGISTRO-problemi.md`,
sezioni F (portato / non portato), G (banco, costruzione, risultati) e H (rinviati e aperti).

- **Portato:** lingua della sessione, primo movimento del puntatore, chiusura all'accesso locale (KDE: 5 s poi forzata),
  riga «chi ha chiuso la connessione», controllo PAM a ogni avvio, cache di Mesa spenta per root, riga AppArmor,
  `xiccd` escluso (Xubuntu), regola fwupd (inerte su Ubuntu).
- **Non portato:** KWin da solo e risoluzione a caldo (su Kubuntu resta il nostro labwc 0.9.3 + wlroots 0.19.2),
  ripiego PATH di Fedora, `--session-fd` di Debian, SELinux/RPM.
- **Banco:** quattro macchine virtuali con la Radeon, senza contenitori, con la protezione `amdgpu.runpm=0`
  (`server/VM-BANCO.md`); pacchetto costruito nella VM `costruzione` (`build/build-deb-vm.sh`).
- **Prove:** giro automatico sui quattro desktop (GNOME 125 PASS + 1 noto; KDE, XFCE, LXQt 126 PASS); aggiornamento
  dalla 1.0.1 e rimozione puliti; prove del proprietario sulle quattro macchine virtuali e sulle quattro live su
  macchina vera (27 nov 2026), tutte OK. Live di Lubuntu: registro H7, deciso di lasciare così.
- **Pacchetto finale:** `remotix_1.2.0-1+ubuntu26.04_amd64.deb`, build `finale1`, sha256 `78ebec78…51fe8f`,
  riproducibile, lintian pulito; licenze ripulite (via installatore e moduli Go; restano labwc e wlroots).
- **Manuali:** utente e tecnico alla 1.2.0, revisionati.
- **Per le prossime volte (proprietario):** niente prove sulle live; macchina vera = distribuzione installata su
  chiavetta USB.
