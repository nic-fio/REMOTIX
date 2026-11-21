# Registro dei problemi e delle soluzioni

Scopo: non rifare gli stessi errori quando si lavorerà alle altre distribuzioni.
Ogni voce dice che cosa è successo, come ce ne siamo accorti, perché succedeva, come è stato risolto
e **che cosa controllare su una distribuzione nuova**. Il dettaglio tecnico sta nei documenti citati
(`DECISIONS-11.md`, `PIANO.md`, `LESSONS.md` per la storia più vecchia).

Regola d'uso: a ogni problema chiuso si aggiunge una voce qui, nello stesso momento in cui si aggiorna `PIANO.md`.
Le voci aperte stanno in fondo.

---

## A. Convivenza fra sessione locale e sessione remota

### A1. Dopo un riavvio del servizio, l'accesso locale rompeva la schermata di accesso (GNOME)
- **Quando:** 17 nov 2026, sul tablet. Schermata di accesso inutilizzabile finché non si riavviava `gdm3`.
- **Come si è visto:** prova manuale del proprietario; poi lettura del registro di sistema.
- **Causa:** al riavvio del servizio il desktop remoto restava vivo senza più nessun processo di REMOTIX a
  sorvegliarlo («orfano»). Per il sistema quella sessione risultava «in chiusura», quindi la schermata di accesso di
  GNOME non tratteneva più l'utente; il desktop locale partiva, trovava ancora attivi i pezzi del desktop remoto e
  moriva in 0,4 secondi. Il controllo periodico di REMOTIX (ogni 5 secondi) non poteva vedere una sessione che vive
  0,4 secondi.
- **Soluzione (scelta del proprietario, `DECISIONS-11` §11.56):** i desktop remoti si chiudono quando il servizio si
  ferma; mentre il servizio gira, un desktop rimasto senza il suo processo viene chiuso («nessun desktop orfano»).
- **Su una distribuzione nuova:** provare sempre *desktop remoto aperto → riavvio del servizio → accesso locale*.
  Verificare che dopo lo stop del servizio non resti nessuna sessione di REMOTIX con processi vivi.

### A2. Le schermate di accesso di KDE, XFCE e LXQt non trattengono chi ha un desktop remoto aperto
- **Quando:** 18 nov 2026. Trovato leggendo i sorgenti delle schermate di accesso, dopo il caso A1.
- **Causa:** solo la schermata di accesso di GNOME aspetta se lo stesso utente ha un'altra sessione grafica. SDDM e
  LightDM no: il desktop locale partiva subito, mentre quello remoto usava ancora lo stesso gestore dell'utente.
  Esito previsto: KDE e XFCE rimandano alla schermata di accesso, LXQt entra senza sfondo né notifiche.
- **Soluzione (`DECISIONS-11` §11.57):** una regola sola per tutti i desktop. Al momento dell'accesso locale il
  sistema di accesso (PAM) chiama un piccolo programma di REMOTIX, che fa chiudere del tutto il desktop remoto di
  quell'utente e solo dopo lascia proseguire l'accesso. Non può mai far fallire un accesso (riga facoltativa, esce
  sempre con «tutto bene», ha un tetto di tempo, esce subito se il servizio è fermo).
- **Provato:** dal proprietario con le schermate di accesso vere su GNOME (tablet), KDE, XFCE e LXQt (Debian live sul
  server): accesso al primo tentativo, desktop remoto chiuso.
- **Su una distribuzione nuova:** (1) quale schermata di accesso usa e se trattiene; non contarci mai. (2) Come si
  aggiunge una riga a PAM in modo pulito: su Debian è `pam-auth-update`, altrove il meccanismo è diverso
  (`authselect` su Fedora, file a mano altrove). (3) La riga deve venire **dopo** quella di `pam_systemd`, perché è
  quella che dice se l'accesso è grafico e su una postazione. (4) Se l'amministratore ha modificato a mano i file di
  PAM, l'aggancio può non essere installato: dirlo all'installazione.

### A3. Un difetto può restare nascosto per mesi se si prova su un desktop solo
- **Che cosa è successo:** il caso A2 esisteva da sempre, ma le prove del «locale che esclude il remoto» erano
  fatte quasi solo su GNOME, dove la schermata di accesso lo nasconde.
- **Regola:** ogni comportamento che dipende dal desktop o dalla schermata di accesso va provato su **tutti** i
  desktop supportati, non su quello a portata di mano. Se uno non si può provare, scriverlo come «non provato»,
  non come «funziona».

---

## B. Prove e ambiente di prova

### B1. Le macchine di prova (contenitori) non hanno una schermata di accesso vera
- **Effetto:** l'accesso locale lì si può solo simulare. La parte più delicata della correzione A2 non veniva
  esercitata dalle prove automatiche.
- **Soluzione:** immagine «live» ufficiale della distribuzione su pendrive, avviata su una macchina vera con scheda
  video; REMOTIX installato sulla live (cartella pronta: pacchetto, script di installazione, script che salva il
  registro, istruzioni).
- **Su una distribuzione nuova:** prevedere da subito la prova da live per tutto ciò che riguarda accesso locale,
  schermata di accesso, spegnimento.

### B2. Nei contenitori un processo di REMOTIX appena nato non riesce a uscire per 25 secondi
- **Come si è visto:** la chiusura del desktop impiegava 11 secondi nelle prove e meno di uno sul tablet.
- **Causa:** un servizio di sistema per l'audio in tempo reale (RealtimeKit) nei contenitori non parte; la parte
  audio di REMOTIX resta in attesa della sua risposta fino a 25 secondi. Su una macchina vera non succede.
- **Soluzione:** la prova aspetta che il desktop abbia almeno 31 secondi prima di misurare i tempi di chiusura.
- **Lezione:** un tempo strano in una prova va spiegato prima di toccare il prodotto: qui il prodotto era giusto.

### B3. Una prova automatica può restare indietro rispetto a una decisione
- **Che cosa è successo:** dopo la decisione A1 (i desktop si chiudono al riavvio del servizio) la prova «riavvio
  del servizio» continuava ad aspettarsi di ritrovare lo stesso desktop, e risultava fallita senza che ci fosse un
  difetto. Lo stesso vale da agosto per i pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine, tolti dalla pagina ma ancora
  nelle prove.
- **Regola:** quando si cambia un comportamento per decisione, nello stesso lavoro si aggiornano le prove che lo
  descrivono. Una riga rossa «già nota» è una riga che prima o poi nasconde un difetto vero.

### B4. «Non rompere nulla» si misura, non si promette
- **Metodo adottato il 18 nov:** dopo ogni modifica al prodotto gira lo stesso giro completo sui quattro desktop, e
  l'elenco delle righe non verdi si confronta con quello del giro precedente: non deve essercene una di più.
- **Su una distribuzione nuova:** avere il giro completo funzionante **prima** di cominciare a correggere.

### B5. I manuali e gli obiettivi dichiarati restano indietro se non li si aggiorna nello stesso lavoro
- **Che cosa è successo (18 nov 2026):** al controllo prima del rilascio i manuali descrivevano ancora il
  comportamento della sera prima (desktop che sopravvivono al riavvio del servizio) e non parlavano
  dell'accesso locale. In più gli obiettivi erano stati abbassati sulla carta (massimo 3K, 8 utenti) ma né il
  programma né i manuali li avevano seguiti: il programma accetta ancora 4K e 10 utenti.
- **Soluzione:** controllo dei manuali frase per frase contro il codice, correzioni, limiti noti dichiarati;
  i numeri garantiti sono 3K e 8 utenti, il programma non viene cambiato (`DECISIONS-11` §11.58).
- **Regola:** una decisione che cambia ciò che l'utente vede si chiude solo quando sono aggiornati insieme
  codice, prove, manuali e registro delle decisioni. Su una distribuzione nuova il manuale tecnico va scritto
  dal codice di quella distribuzione, non copiato e adattato.

---

## C. Pacchetto e installazione

### C1. Agganciarsi a PAM senza rischi
- Si usa il meccanismo della distribuzione (su Debian `pam-auth-update` con un file in `/usr/share/pam-configs`),
  mai la modifica diretta dei file di PAM. La riga si toglie alla rimozione del pacchetto, non all'aggiornamento.
- Se la riga non viene aggiunta (file modificati a mano), l'installazione lo dice con un avviso e il prodotto
  continua a funzionare con i soli controlli periodici.

### C2. Cose già decise il 17 nov (dettagli in `PIANO.md`)
- Il pacchetto rifiuta una **nuova** installazione su una macchina senza scheda video adatta, e avvisa se la scheda
  c'è ma non codifica.
- Rimozione con un utente collegato: i desktop vengono chiusi prima, senza lasciare residui.
- Nessun programma di installazione: solo `apt install ./remotix_….deb`.

### C3. Un indirizzo personale era finito nel pacchetto e nella storia del repo
- **Quando:** 18 nov 2026, trovato nel controllo fatto prima di rendere pubblico il repo.
- **Che cosa è successo:** come «responsabile del pacchetto» c'era l'indirizzo personale del proprietario invece di
  quello del progetto, in `debian/control` e in `build/build-deb.sh`; quindi anche dentro il `.deb` già messo sul sito.
- **Soluzione:** indirizzo del progetto nei due file; pacchetto ricostruito con la stessa data di costruzione e
  confrontato file per file con quello provato (programma identico, cambia solo quella riga); storia del repo
  riscritta; repo su GitHub cancellato e ricreato, perché GitHub conserva i commit vecchi anche dopo la riscrittura.
- **Su una distribuzione nuova / prima di ogni pubblicazione:** cercare dati personali (indirizzi, chiavi, nomi di
  macchine) nei file, nella storia **e dentro il pacchetto finito** (`dpkg-deb -f … Maintainer`) *prima* di
  pubblicare qualunque cosa. La costruzione riproducibile permette di rifare il pacchetto senza rifare le prove.

---

### C4. «Nessuno spegne la macchina»: il riavvio restava possibile all'utente seduto al computer (20 nov 2026)
- **Quando:** trovato dal proprietario il 20 nov 2026 sul proprio tablet Debian, davanti alla macchina: «come mai sembra
  che posso spegnere?».
- **Che cosa è successo:** la regola `50-remotix-no-poweroff.rules` vietava 15 azioni di logind e il giro di prove
  confermava «spegnere no, riavviare no». Ma l'utente locale, davanti alla macchina, otteneva «sì» al riavvio
  (`CanPowerOff` no, `CanReboot` yes; `pkcheck` autorizzava `reboot`). Il manuale dichiarava «nessuno».
- **Causa:** nella policy di logind quattro azioni NON vietate (`set-reboot-parameter`, `set-reboot-to-firmware-setup`,
  `set-reboot-to-boot-loader-menu`, `set-reboot-to-boot-loader-entry`) portano l'annotazione
  `org.freedesktop.policykit.imply` = `reboot` e il permesso «sì» per l'utente attivo seduto alla macchina: chi è
  autorizzato per una di esse lo è anche per `reboot`, e polkit lo concede per implicazione NONOSTANTE il NO
  della nostra regola su `reboot` (un NO esplicito non basta contro un'implicazione di un'azione autorizzata). Le quattro azioni sono ora vietate (19 in tutto).
- **Perché non si era visto:** il giro guardava solo la sessione REMOTA (`power-entries-absent`: logind e `pkcheck` dal
  desktop remoto, che non è «seduto alla macchina», quindi il «sì» per l'utente attivo non vale) e solo le 15 azioni che
  conoscevamo per nome; le implicazioni della policy non erano mai state lette. Una prova fatta dal posto sbagliato
  dice sempre quello che ci si aspetta.
- **Gravità, onesta (caso schermata di accesso, MISURATO il 20 nov 2026 su Ubuntu 26.04 GNOME, VM, regola vecchia):** l'utente della
  schermata di accesso (greeter) è «attivo e locale»: `pkcheck` da un suo processo CONCEDEVA `reboot` (e nient'altro fra le
  15: spegnere e le altre forme restavano negate). Quindi con nessuno collegato chi sta davanti alla macchina poteva
  riavviare dal menu della schermata di accesso senza accedere. Con la regola nuova: tutte e 19 negate. Su Debian 13 non misurato: dedotto dallo stesso meccanismo.
  Nota di metodo: il «Leader» della sessione del greeter è un processo di ROOT, e polkit autorizza root senza condizioni
  (il primo giro del controllo vedeva tutte le azioni concesse): `power-local-seat` prende un processo dell'utente del
  greeter, non di root. Per lo stesso motivo `pkcheck` per root non prova nulla, e `sudo systemctl reboot` resta possibile.
- **Gravità, onesta:** con altri utenti collegati logind chiede `reboot-multiple-sessions`, che era ed è negata. Il buco
  permetteva quindi il riavvio solo a un utente locale, e solo quando era l'unico sulla macchina. Non permetteva di
  spegnere. Il manuale però diceva «nessuno».
- **Soluzione:** quattro azioni in più nella regola; nuovo controllo `power-implied` in `prove/check-desktop.py`: legge la
  regola installata e TUTTI i file `*.policy` della macchina, costruisce le implicazioni (anche a catena) e fallisce se
  un'azione non vietata ne implica una vietata.
- **Provato su Debian 13 (20 nov 2026, tablet del proprietario, pacchetto ricostruito `1.0.0-1+deb13` con la regola a 19
  azioni, installato con `apt install --reinstall`):** da un processo dell'utente locale nella sua sessione attiva `pkcheck`
  nega `reboot`, `power-off`, `halt`, `suspend` e le quattro `set-reboot-*`; taratura: `chvt` concessa. logind risponde «no» a
  `CanReboot`, `CanPowerOff`, `CanHalt`, `CanRebootToFirmwareSetup` (prima della correzione `CanReboot` era «yes»). Non
  provato su Debian: il caso della schermata di accesso. Il pacchetto corretto di Debian non è ancora pubblicato.
- **Su una distribuzione nuova:** (1) una regola che vieta azioni va controllata anche contro le IMPLICAZIONI della
  policy, e dal posto dell'utente LOCALE (seduto), oltre che da quello remoto; (2) farlo girare `power-implied` con la
  versione di systemd della distribuzione (le azioni `set-reboot-*` e le loro implicazioni cambiano fra versioni);
  (3) provare a mano `pkcheck --action-id org.freedesktop.login1.reboot` dalla sessione locale.

---

## D. Comportamenti dei desktop da ricordare

- **XFCE** rifiuta un'uscita chiesta mentre si sta ancora avviando («deve essere a riposo»): REMOTIX in quel caso
  chiude il desktop con la forza. Visto il 17 e il 18 nov.
- **KDE**: l'uscita ordinata può non completarsi se il desktop è appena partito (un servizio è ancora in
  avviamento); dopo 10 secondi REMOTIX la forza. Per questo l'attesa concessa alla chiusura è più lunga di 10 secondi.
- **GNOME** nasce nella «Panoramica», che trattiene i primi tocchi da telefono: lo vede anche un utente vero.
- **La sessione dell'utente nel sistema** (logind) deve restare «attiva» per tutta la vita del desktop remoto, e
  l'uscita deve chiuderla davvero su tutti i desktop: corretto il 17 nov.

---

## D-bis. Tastiera e programmi che leggono i tasti grezzi (versione 1.0.1, 21 nov 2026)

Tutto nasce da una prova del proprietario: da remoto, dentro QEMU, alcuni caratteri non uscivano o uscivano diversi.
Nei programmi normali non si vede nulla, perché ricevono il carattere già fatto dal desktop; QEMU, le altre macchine
virtuali e forse qualche gioco leggono invece la **posizione** del tasto, e mostrano due difetti distinti.

### D-bis.1 Alcuni caratteri sparivano: il server premeva tasti che su un PC non esistono
- **Che cosa si vedeva:** dentro QEMU non uscivano `$`, `(`, `)` e, con la sessione italiana, nemmeno `=` e `€`.
- **Causa:** per ogni carattere il server sceglieva la strada con meno tasti. Le tabelle di tastiera di Linux hanno
  tasti «speciali» che fanno da soli quei caratteri (dollaro, euro, parentesi e uguale di certi tastierini): un tasto
  solo batteva Shift+4. Ma su una tastiera da PC quei tasti non ci sono, e QEMU li scartava.
- **Correzione:** `src/keyboard.c` — i tasti di una tastiera normale vengono sempre prima; quelli speciali restano come
  ultima scelta, per i caratteri che in quella tastiera non si fanno in altro modo.
- **Come è stato verificato:** confronto a tappeto regola vecchia/nuova con il codice vero, 98 tastiere, tabelle di
  Debian 13 e di Ubuntu 26.04: su 13.311 combinazioni ne cambiano 359, tutte e solo dei sei caratteri `$ ( ) = € ±`.
  Provato dal proprietario dentro QEMU su Debian.
- **Su una distribuzione nuova:** il difetto sta nel nostro codice e le tabelle sono comuni a tutto Linux: partire dal
  codice già corretto. Se le tabelle di una distribuzione portano altri tasti speciali, rifare il confronto.

### D-bis.2 Caratteri diversi da quelli premuti: la tastiera era indovinata dalla lingua del browser
- **Che cosa si vedeva:** browser in italiano e tastiera fisica americana (il caso del proprietario): dentro QEMU
  `(` dava `*`, `-` dava `/`, `@` dava `q`. Con il browser in inglese tutto giusto.
- **Causa:** una pagina web non può sapere che tastiera ha chi la guarda; la pagina la deduceva dalla lingua del browser
  e il server impostava la sessione di conseguenza. Sessione italiana + sistema ospitato americano = tasti letti con la
  tabella sbagliata. Lo stesso scarto può spostare le scorciatoie con Ctrl e Alt.
- **Correzione:** `src/page.html` — nella maschera di accesso c'è il menu «Keyboard», preimpostato sulla tastiera che
  risulta dalla lingua del browser; l'utente può cambiarla e la scelta resta ricordata in quel browser. Server e
  protocollo non cambiano. Chi non tocca il menu ottiene la tastiera di prima.
- **Regola per chi usa macchine virtuali da remoto:** la tastiera scelta nella maschera deve essere quella del sistema
  che gira dentro la macchina virtuale.
- **Limiti noti:** niente varianti (per esempio «US internazionale»); per cambiare tastiera ci si scollega e si rientra;
  se il server non ha la tastiera scelta, il messaggio di rifiuto è generico e non la nomina.

---

## E. Aperti (non bloccanti)

### E1. XFCE: nella sessione remota lo sfondo è nero
- **Visto:** dal proprietario sulla live XFCE, 18 nov 2026; riprodotto sulla macchina di prova, anche con utente nuovo.
- **Causa:** la libreria di XFCE `libxfce4windowing` 4.20.2 perde il messaggio con cui il compositore (labwc) dice su
  quale schermo sta l'area di lavoro, se arriva prima che lo schermo sia noto; `xfdesktop` allora dipinge nero.
  Non dipende da REMOTIX né dallo sfondo scelto. Corretto dagli autori dalla versione 4.20.4 (lug-ago 2025).
- **Deciso (18 nov 2026):** solo estetico, nessun rimedio in REMOTIX per Debian 13 (che ha la 4.20.2).
- **Su una distribuzione nuova (e su Debian forky):** guardare la versione di `libxfce4windowing`: da 4.20.4 in su lo
  sfondo dovrebbe comparire da solo — da verificare con una foto della sessione, non è stato provato sul campo.
  Ricordare che XFCE tiene uno sfondo per ogni schermo: quello scelto in locale non passa da solo allo schermo remoto.
- **Nota di metodo:** un filtro nei comandi di diagnosi (`grep -v tput`) nascondeva ogni riga con la parola «output» e
  ha fatto dare la colpa a labwc per errore. Filtrare sempre con un motivo preciso (`^tput:`).

### E2. Righe non verdi note nel giro di prove
- Pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine (prove da allineare, vedi B3); coordinate del mouse su XFCE nell'angolo
  coperto dal pannello; un controllo su GNOME voluto così (`pkexec`); primo tocco da telefono su GNOME, saltuario.
