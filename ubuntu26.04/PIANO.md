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

## PIANO — Versione 1.2.0 per Ubuntu 26.04 (26 nov 2026) — IN ATTESA DELL'OK DEL PROPRIETARIO

### Obiettivo
Portare REMOTIX per Ubuntu 26.04 (Ubuntu, Kubuntu, Xubuntu, Lubuntu) alla 1.2.0, il più vicino possibile al codice e
al comportamento di Fedora 45 1.2.0, come già fatto per Debian 13. Regola: dove Fedora fa una cosa e su Ubuntu si può
fare, si fa come Fedora. Resta diverso solo ciò che non si può portare, e viene dichiarato.

### Da dove si parte
Analisi del 26 nov, cinque rapporti in `studio/analisi-1.2.0/` (uno per desktop più le parti comuni), fatti sul codice
di oggi confrontando Ubuntu con Fedora e con Debian 1.2.0. Risultato: **Ubuntu è già vicina alla 1.2.0**, perché
gran parte di ciò che Debian ha dovuto recuperare era nato proprio su Ubuntu. Il codice che manca è poco e quasi
tutto già scritto e rivisto per Debian; **il grosso del lavoro sono il banco, la costruzione senza contenitori e le
prove**. Tutto ciò che i rapporti segnano «non verificato» si misura sulle macchine virtuali prima di scrivere codice.

Metodo obbligato: si lavora **a blocchi sui file di Ubuntu**, mai copiando interi i file grandi di Fedora o Debian
(`child.c`, `session.c`, `main.c`, `kwin.c`): porterebbero via le parti proprie di Ubuntu elencate più sotto.
L'unico file che si prende intero è `transport.c` (identico in Fedora e Debian, solo registro).

### Che cosa entra
Parti comuni ai quattro desktop:
1. **Lingua del desktop remoto**: quella scelta dall'utente nelle Impostazioni, altrimenti quella di sistema, con i
   formati di date e numeri. Oggi è sempre inglese. È la voce più grande e più delicata.
2. **Aggancio «il locale chiude il remoto» controllato e rimesso a posto a ogni avvio del servizio**, con una riga
   nel registro (oggi lo fa solo l'installazione).
3. **Registro**: riga «chi ha chiuso la connessione e perché».
4. **Regola per gli aggiornamenti firmware** (come Fedora).
5. **Niente cache grafica nella cartella di root.** I file lasciati lì dalla 1.0.1 non vengono toccati (come su Debian).
6. **Testi**: messaggio «reinstalla il pacchetto» col comando giusto; via i residui (Debian trixie, Fedora, Arch, SUSE).
7. **Pacchetto**: una riga in più nel profilo AppArmor, ordine corretto alla disinstallazione, controllo più preciso
   all'installazione.
8. **Licenze**: via installatore, file `.run` e moduli Go (circa 510 righe che non corrispondono a nulla nel
   pacchetto). labwc e wlroots **restano**, perché nel pacchetto Ubuntu ci sono davvero. Sono testi legali: la
   proposta riga per riga viene mostrata prima di scrivere.
9. **Versione 1.2.0**, registro dei problemi, `CLAUDE.md` di questa cartella (parla ancora di Debian e di podman).

Per desktop:
- **GNOME**: primo movimento del puntatore inviato due volte (il primo clic non cade più sul bordo).
- **KDE**: nella chiusura per accesso locale attesa di 5 secondi invece di 10, e chiusura forzata che ferma tutto il
  desktop. Lingua portata anche dentro Plasma (serve un pezzo in più, quello di Debian).
- **XFCE**: `xiccd` (profili colore) non parte nel desktop remoto, come su Debian — **solo se** sulla macchina
  virtuale risulta che dà fastidio (su Debian apriva una finestra di password).
- **LXQt**: nessun codice proprio; solo le parti comuni.

### Differenze che restano, dichiarate
- **KDE con KWin da solo e cambio di risoluzione a caldo**: servono a KWin 6.8, Kubuntu ha 6.6. KDE resta dentro il
  nostro labwc contenuto nel pacchetto (misura di un minuto sulla macchina virtuale per conferma).
- **`PATH`**: su Ubuntu il sistema ne dà già uno all'accesso, quindi il ripiego di Fedora non avrebbe effetto e non
  si porta. Misuro sui quattro desktop se il `PATH` remoto coincide con quello locale; se non coincide lo porto al
  proprietario.
- **Niente SELinux, RPM, firewalld**; niente del meccanismo che su Debian tiene viva la sessione (a Ubuntu non serve).
- **Restano proprie di Ubuntu**: database delle impostazioni «di sistema» (per i programmi snap), labwc nostro,
  avvio di GNOME 50, AppArmor per il kernel nuovo, particolarità di Xubuntu e Lubuntu (sfondo e icone che
  funzionano, pannello, `lubuntu-update`), snap.
- **«Ultima difesa» alla chiusura** su GNOME, XFCE, LXQt: non si costruisce, come su Fedora e Debian; si prova con
  programmi aperti e si interviene solo se fallisce.

### Banco e protezione della Radeon (strutturale)
Su Debian il server è caduto quattro volte perché la macchina virtuale metteva a riposo la Radeon. Da ora:
1. **Alla creazione** di ogni macchina virtuale lo script mette da solo il blocco del risparmio energetico della
   scheda (`amdgpu.runpm=0`), anche su Ubuntu, che finora non ha mai dato il problema.
2. **All'accensione con la Radeon** lo script controlla che il blocco sia attivo nella macchina; se non lo è,
   **rifiuta** di darle la scheda. Lo stesso controllo vale dopo il ripristino di un'istantanea.
3. **Sul server**, a ogni preparazione: registro del kernel copiato su disco da solo, e blocco del riposo della
   scheda anche dal lato server (senza toccare la riga di avvio). Questo terzo livello non è dimostrabile senza
   provocare un blocco: la garanzia sono i primi due.
4. Debian e Fedora non si toccano (proprietario, 26 nov: i blocchi venivano dai driver vecchi delle macchine Debian;
   «non tocchiamo più debian»). La protezione resta solo negli script del banco di Ubuntu.

Macchine: `ubuntu`, `kubuntu`, `xubuntu`, `lubuntu` dalle ISO 26.04.1 in `/media/DOWNLOAD` (utente `prova`,
password di prova solita, gruppo `sudo`), istantanea `pulito`; più una quinta, `costruzione`, che non riceve mai la
Radeon. Cartella `/media/REMOTIX-UBUNTU`. Lo script acquista il modo «senza Radeon» (più macchine accese insieme
per i lavori che non richiedono video). Nessun contenitore, nemmeno per preparare il server.

### Costruzione senza contenitori
Nuovo `build/build-deb-vm.sh` sul modello di Debian, con in più ciò che è solo di Ubuntu: costruzione del nostro
labwc/wlroots, controlli sul labwc, archivio del sorgente da pubblicare accanto al pacchetto. Il vecchio
`build-deb.sh` resta com'è (non si cancella), aggiornato solo nel numero di versione.

### Passi
1. **Banco** (script con la protezione Radeon, revisore) → creazione delle cinque macchine → istantanee `pulito`.
   In parallelo: script di costruzione.
2. **Misure** sulle macchine dei punti «non verificati»: `PATH` locale e remoto, lingua, `xiccd` su Xubuntu,
   firmware, versione del protocollo di KWin, programmi presenti per le prove (`kwrite` su Kubuntu).
3. **Codice**, un desktop alla volta nell'ordine GNOME → KDE → XFCE → LXQt, partendo dalle parti comuni
   (`programmatore`, poi `revisore` su Fable). I punti della lingua fra avvio e cambio d'identità li guarda il
   revisore uno per uno.
4. **Pacchetto** costruito nella macchina `costruzione`.
5. **Prove automatiche**, una macchina alla volta con la Radeon: giro completo sui quattro desktop; aggiornamento
   dalla 1.0.1 pubblicata alla 1.2.0; disinstallazione che non lascia nulla; chiusura forzata di KDE su un desktop
   appena nato; «il locale chiude il remoto» con programmi aperti (anche un Firefox snap) — vedi decisione 1.
6. **Prove del proprietario** sulle quattro macchine virtuali (consegnate pulite, solo da aprire nel browser).
7. **Prove del proprietario sulle quattro live** su macchina vera (`server/live-installa.sh` aggiornato alla 1.2.0,
   fa tutto da solo).
8. Poi, su suo ordine: manuali, sito, GitHub.

### File toccati
- Prodotto: `src/child.c`, `src/session.c`, `src/main.c`, `src/input.c`, `src/kwin.c`, `src/transport.c`,
  `src/rootside.c`, regole polkit, nuovo `src/remotix-pam-hook`.
- Pacchetto: `debian/remotix.service`, `rules`, `remotix.postinst`, `remotix.prerm`, `remotix_network.apparmor`.
- Costruzione: nuovo `build/build-deb-vm.sh`; `build/build-deb.sh` (solo versione).
- Banco: `server/vm-radeon.sh`, nuovo `server/prepara-server-vm.sh`, `server/live-installa.sh`; `prove/` (casi
  «il locale chiude il remoto», controlli di uscita, controllo AppArmor, adattati alle schermate di accesso di
  Ubuntu).
- Testi: `LICENSE.md`, `THIRD-PARTY-LICENSES`, `CLAUDE.md`, `docs/REGISTRO-problemi.md`.

### Rischi
- **Lingua**: codice delicato, eseguito al momento dell'accesso; un errore lì impedisce di entrare. Si prova su
  tutti e quattro i desktop, con lingua scelta, lingua di sistema e lingua non installata (ripiego sull'inglese).
- **Chiusura forzata di KDE su un desktop appena nato**: su Kubuntu il sistema ha già rifiutato quel comando nei
  primi ~25 secondi di vita del desktop. Se la prova fallisce, la cura (un secondo tentativo) è un cambio di
  comportamento: si ferma e si porta al proprietario.
- **Costruzione nella macchina virtuale**: prima volta per Ubuntu, con il labwc dentro; possibile qualche giro a vuoto.
- **«Il locale chiude il remoto» su Xubuntu e Lubuntu**: mai provato su macchina vera con programmi aperti.
- **Blocco del server**: coperto dalla protezione sopra; se accade comunque, il registro su disco dice perché.

### Decisioni del proprietario
1. Le prove «il locale chiude il remoto» che riavviano la schermata di accesso dentro la macchina virtuale (vietate
   sul banco di Debian): sul banco di Ubuntu **si fanno** (26 nov: il rischio riguardava solo le macchine Debian;
   proposto al proprietario, nessuna obiezione), poi lui le ripete sulle live.
2. Se le misure mostrano un `PATH` remoto diverso da quello locale: come allinearlo (si porta quando c'è il dato).
3. Finestra del portafoglio di KDE: mai decisa su nessuna distribuzione; resta com'è.
4. Manuali (sezione «Requirements», NVIDIA misurata e non «mai provata»): dopo il codice, come su Debian.

### Fatto quando
- Giro automatico verde sui quattro desktop (a parte le righe note e dichiarate), aggiornamento dalla 1.0.1 e
  disinstallazione puliti.
- Desktop remoto nella lingua dell'utente sui quattro desktop.
- «Il locale chiude il remoto» riuscito con programmi aperti sulle quattro schermate di accesso.
- Revisore APPROVATO; prove del proprietario riuscite sulle macchine virtuali e sulle quattro live.
- Nessun blocco del server causato dalla Radeon.
