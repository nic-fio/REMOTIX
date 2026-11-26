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

---

## F. Versione 1.2.0 (26 nov 2026): Debian 13 allineata a Fedora 45

Regola del proprietario (25 nov): dove Fedora fa una cosa e su Debian si può fare, si fa come Fedora, senza varianti di
Debian. Il lavoro è stato fatto a blocchi sui file di Debian (mai copiando interi `child.c`, `session.c`, `main.c`...,
perché avrebbero riportato codice tolto apposta e rotto il filo che tiene viva la sessione dell'utente). Le prove sono
sul banco a macchine virtuali (sezione G) e a mano, dal proprietario, sulle quattro live. Dove una cura non è stata
vista scattare su Debian, lo dico.

### F1. Il desktop remoto parlava sempre inglese
- **Che cosa si vedeva:** qualunque lingua avesse l'utente, il desktop remoto partiva in inglese.
- **Causa:** il server non passava nessuna lingua alla sessione.
- **Cura:** la sessione usa la lingua che l'utente ha scelto nelle Impostazioni (la legge dal servizio di sistema che
  tiene i dati degli utenti) e, se non ne ha scelta una, quella del sistema, con i formati (date, numeri). Misurato su
  GNOME e su XFCE/LXQt: la lingua arriva a tutti i processi del desktop.
- **Il gestore utente:** su KDE, XFCE e LXQt anche il gestore dei servizi dell'utente riceve la lingua (funzione
  `manager_set_locale` in `src/session.c`), perché da lì nascono i servizi di contorno; a fine sessione il valore torna
  com'era. Nella chiusura «leggera» per accesso locale la lingua resta lì **di proposito**: non si rimette a posto,
  e non è un difetto.
- **KDE:** la lingua del desktop la decide il file `plasma-localerc` dell'utente, come in locale. Se quel file dice
  un'altra lingua, vince lui (è così che è stato trovato: il primo esito «la lingua non arriva a Plasma» era dovuto a un
  file `plasma-localerc` già presente, non a REMOTIX). Non è un difetto.
- **Resta:** `xfconfd` (il servizio di impostazioni di XFCE) resta nella lingua di sistema; da verificare su Fedora se la
  lingua dell'utente arriva al desktop KDE (non è mai stato misurato lì).
- **Su una distribuzione nuova:** misurare la lingua dentro i processi del desktop (non solo del processo figlio) e
  guardare se il desktop ha un suo file di lingua per utente.

### F2. `PATH` fisso: i programmi dell'utente in `~/.local/bin` non partivano
- **Causa:** il `PATH` del desktop remoto era una lista fissa.
- **Cura (regola di Fedora):** si usa il `PATH` che il sistema dà all'accesso; se manca, il ripiego con `~/.local/bin` e
  `~/bin` davanti alle cartelle di sistema, come un accesso grafico locale (`src/child.c`, blocco «PATH»). Dalla
  revisione è stata corretta anche una graffa mancante in quel blocco.

### F3. Schermo nero quando manca `labwc` (XFCE, LXQt)
- **Che cosa succedeva:** `labwc` è solo «raccomandato» dal pacchetto; su una macchina con XFCE o LXQt senza `labwc` il
  desktop non nasceva e l'utente vedeva nero.
- **Cura:** il server riconosce che il compositor non è installato e manda il rifiuto `0x0E` con un messaggio chiaro, e il
  registro nomina il pacchetto (`src/main.c`, `src/session.c`). In più `debian/remotix.postinst` avvisa all'installazione
  (solo se la macchina ha XFCE o LXQt e né GNOME né Plasma, per non avere dubbi su quale desktop partirà); l'avviso non
  fa mai fallire `apt`.

### F4. La fine della sessione veniva detta al browser troppo tardi
- **Cura:** il saluto di fine sessione parte subito, prima di smontare tutto (`§7.6` in `src/child.c`), e un nuovo
  accesso non si aggancia a un desktop che sta morendo. Vale su GNOME, XFCE e LXQt; KDE è escluso di proposito e usa la sorveglianza del Log Out (F7), provata a mano con e senza browser.

### F5. XFCE: il pulsante «azioni» del pannello spariva dal desktop locale (D-X3)
- **Che cosa si vedeva:** dopo una sessione remota, nel desktop locale del pannello mancava il pulsante di uscita/azioni.
- **Causa:** il file con cui REMOTIX blocca il pannello nascondeva il tipo del plugin (`xfconfd` non scrive nel file
  dell'utente un valore uguale a quello di sistema), e il pannello locale, vedendo un plugin senza tipo, lo cancellava.
  Riprodotto su Debian 13 con xfconf 4.20 (era già il difetto D-X3 di Ubuntu).
- **Cura:** controllo di integrità del pannello (`xfce_panel_integrity()` in `src/session.c`) e blocco scritto in modo
  che il tipo resti. In più i programmi inutili in una sessione remota (Bluetooth) non partono.
- **Su una distribuzione nuova:** dopo una sessione remota, aprire il desktop locale e guardare il pannello.

### F6. XFCE: una finestra di password di amministratore al centro del desktop remoto
- **Che cosa si vedeva:** nella prova di mouse e tastiera su XFCE comparivano finestre di password («Authenticate») che
  facevano fallire le prove di mouse e tastiera.
- **Causa:** `xiccd`, il programma dei profili colore (parte di `colord`), parte da solo all'avvio del desktop e chiede
  a polkit di creare un dispositivo colore. Una sessione remota non è «seduta alla macchina», quindi polkit chiede la
  password di amministratore.
- **Cura:** `xiccd.desktop` non viene avviato nella sessione remota (`SESSION_NOT_IN_REMOTE_AUTOSTART` in
  `src/session.c`, con `blueman.desktop`). I profili colore di un desktop remoto senza schermo vero non servono.
- **Perché NON una regola polkit:** era stata provata e poi ritirata (commit `7d75a36`, annullato da `c92da17`).
  `colord` è un servizio unico per tutta la macchina, non per sessione: una regola che dà alle sessioni remote il permesso
  vale per la macchina intera. Il revisore l'ha bocciata.
- **Resta:** da verificare se Xubuntu ha `xiccd` (serve alla 1.2.0 di Ubuntu).

### F7. KDE: chiusura per accesso locale, fotogramma perso, Ctrl+Alt+Canc, Log Out
- **Chiusura per accesso locale:** attesa di 5 secondi (prima 10) e chiusura forzata che ferma `graphical-session.target`
  (`src/session.c`, `src/child.c`). Su Plasma 6.3.6 fermare quel gruppo o `plasma-workspace.target` ferma tutto nello stesso
  tempo (0,37 contro 0,47 s), quindi su Debian la cura è innocua e uniforme più che necessaria; resta come in Fedora.
- **Fotogramma perso:** se KWin non manda l'immagine, il server lo «tocca» (`src/capture.c`, `src/kwin.c`), con
  un limite di tocchi consecutivi e una riga di registro. Su Debian **non è mai scattato** (0 righe in tre avvii): innocuo,
  non visto in azione.
- **Ctrl+Alt+Canc:** il difetto di Fedora (Plasma 6.4 e oltre chiede a `org.freedesktop.ScreenSaver` se lo schermo è
  bloccato, e senza risposta non apre la finestra di uscita) su Plasma 6.3.6 di Debian non nasce; il piccolo servizio di
  appoggio che risponde «non bloccato» è portato lo stesso, per uniformità (`src/kwin.c`). Le prove della pagina (Ctrl+Alt+Canc
  nascosto, catena, Ctrl+Alt+Fine) passano.
- **Log Out dal menu senza nessuno collegato:** riconosciuto anche senza browser; il desktop sparisce in 2 secondi, nessun
  processo resta. Provato a mano.
- **Resta, dichiarato:** KDE con KWin da solo e cambio di risoluzione a caldo servono a KWin 6.8; Debian ha 6.3.6 (protocollo
  alla versione 12, ne servono 22). KDE resta dentro il labwc di Debian.

### F8. GNOME: primo movimento del puntatore e scala dello schermo
- **Puntatore:** il primo movimento dopo l'avvio del dispositivo viene inviato due volte (`src/input.c`), come su Fedora: il primo arrivava con una coordinata a zero (misurato su Fedora, Mutter 51; su Debian non misurato).
- **Scala:** se l'utente ha una scala diversa da 1 (per esempio 200%), la sessione riporta il suo monitor a 1
  (`mutter_scale_to_one()` in `src/mutter.c`); se non riesce, chiude la sessione con un messaggio. La chiave
  `scaling-factor` è fra quelle bloccate (`DCONF_KEYS`). Su GNOME 48 di Debian (mutter 48.7) il cambio è possibile
  (`supports-changing-layout-mode` vero); prima la scena veniva rifiutata e ritentata in loop.
- **Resta:** alcune protezioni nate su GNOME 50 su Debian potrebbero non scattare mai: sono innocue ma «non viste
  scattare su Debian».

### F9. AppArmor: la riga `deny unix` per i kernel nuovi (voce C4 del registro di Ubuntu)
- **Causa e cura:** la riga `deny unix addr=@*,` del profilo del lato rete porta con sé anche il permesso di *creare*
  un socket e, su un kernel che controlla i socket unix (quello di Ubuntu 26.04), vieta tutto: niente D-Bus, niente
  risposta di logind e ogni accesso viene rifiutato. Ora le righe nominano le operazioni
  (`deny unix (bind, listen) addr=@**,` e `deny unix (connect, send, receive) peer=(addr=@**),`), `debian/remotix_network.apparmor`.
- **Su Debian oggi non si vedeva:** il kernel 6.12 di Debian 13 non controlla i socket unix (nel kernel non ci sono le
  funzioni `af_unix` di AppArmor), quindi la riga non aveva effetto. È messa a posto perché un kernel più nuovo
  (backports, Debian futura) non faccia lo stesso danno. Non provata su un kernel che li controlli.
- **Limite noto:** resta permesso l'«autobind»; il secondo muro (landlock) resta. Da riguardare quando il profilo passerà
  da «complain» a «enforce».

### F10. AppArmor: il profilo non copriva la lettura di `org.kde.remotix.desktop`
- **Come si è visto:** il nuovo controllo del banco (`check-apparmor.py`, guarda nel registro del kernel le righe del
  profilo `remotix_network`) su KDE ha trovato righe «ALLOWED» tutte uguali: lettura di
  `/usr/share/applications/org.kde.remotix.desktop`, il file del permesso di cattura per KWin.
- **Causa:** il profilo è in «complain» (voluto e scritto nei manuali): non blocca, ma segnala. In «enforce» sarebbe un rifiuto.
- **Cura:** riga `r` su quel percorso in `debian/remotix_network.apparmor`.
- **Su una distribuzione nuova:** far girare il controllo dei rifiuti/avvisi di AppArmor su ogni desktop e a fine giro.

### F11. L'aggancio «il locale chiude il remoto» si controlla a ogni avvio; la riga PAM si toglie dopo l'arresto
- **Cura:** a ogni avvio del servizio `ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check` guarda se la riga è in
  `/etc/pam.d/common-session` e, se manca (un aggiornamento, una modifica a mano), la rimette con `pam-auth-update` e lo scrive nel
  registro. Non impedisce mai l'avvio. Se l'amministratore ha modificato a mano il file, lo strumento di Debian rifiuta e
  resta la sola riga di avviso (come prima).
- **Riga tolta troppo presto:** in `debian/remotix.prerm` la riga PAM ora si toglie **dopo** l'arresto del servizio; prima,
  un riavvio fra la rimozione e l'arresto l'avrebbe rimessa, lasciandola dopo la rimozione.
- **`postinst`:** il controllo «la riga c'è già?» cerca ora la riga vera (`session ... pam_exec.so ... remotix-local-login`)
  e non una qualunque riga che contenga il nome.

### F12. Piccole voci
- **Sentinella «na»:** la sentinella chiede al sistema se le azioni di spegnimento sono permesse; la risposta «na» («non
  disponibile su questa macchina», per esempio una VM o un server) conta come «no», sicura, e non è più un allarme (`src/sentinel.c`).
- **Chiusura della connessione:** una riga di registro dice chi ha chiuso (il browser col suo saluto, un silenzio, la rete) e perché
  (`src/transport.c`).
- **`needrestart`:** `debian/needrestart/remotix.conf` impedisce che un aggiornamento di libreria riavvii da solo il servizio, che
  chiuderebbe tutti i desktop remoti: il servizio compare fra quelli «da riavviare a mano».
- **Cache di Mesa di root:** la prova delle schede video faceva scrivere a Mesa una cache in `/root/.cache`, che dopo la
  rimozione restava. Ora la prova e il servizio hanno `MESA_SHADER_CACHE_DISABLE=true` (`debian/remotix.service`,
  `debian/remotix.postinst`); i desktop degli utenti non cambiano e tengono la loro cache.
- **Licenze ripulite:** via ogni riferimento a materiale che il pacchetto non contiene (installatore, moduli Go, labwc e
  wlroots, file `.run`). Principio del proprietario: ogni distribuzione rispecchia il proprio pacchetto.
- **Testi:** i messaggi «reinstalla il pacchetto» danno il comando giusto per un `.deb`; via i riferimenti a Fedora, Arch e SUSE.
- **Regola polkit per gli aggiornamenti firmware** (Fedora): inserita ma su Debian 13 non fa nulla (fwupd 2.0.20 non ha
  quell'azione): innocua, non vista in azione.

### F13. Voci del registro di Ubuntu che ora valgono anche per Debian
- **B3-bis (lezione di metodo):** una riga rossa uguale su tutti i desktop fa sospettare lo strumento, ma va dimostrato prima
  di archiviarla; guardare gli eventi grezzi della finestra di prova (`WAYLAND_DEBUG`). Su Ubuntu con GTK 4.22 tre prove di
  trascinamento fallivano per un cambiamento del campo di testo; con GTK 4.18 (Debian) erano verdi. Qui vale ancora per
  `kbd-not-producible` su Firefox in LXQt (sezione H).
- **C4:** vedi F9.
- **C5, database di impostazioni di sistema (dconf): DIFFERENZA DICHIARATA, non portata.** Su Ubuntu le regole di sessione
  stanno in `/etc/dconf/db/remotix` e nel profilo `$XDG_RUNTIME_DIR/dconf/profile`, perché i programmi Flutter e gli «snap» di Ubuntu
  non leggono il profilo a tre strati. Su Debian 13 non ci sono quei programmi e il meccanismo a tre strati (profilo in
  `$XDG_RUNTIME_DIR/remotix/dconf/`, database a runtime) funziona; per decisione del proprietario (25 nov 2026) non si porta.
  Conseguenza: Debian non scrive il file `~/.config/dconf/remotix` nella casa dell'utente, e non ha il database di sistema.
  Se un giorno su Debian compariranno programmi che scartano il profilo (`Unknown DConf source`), la strada è quella di Ubuntu.
- **E3 (variabili del gestore utente):** nella chiusura fatta dal lato root la «foto» dell'ambiente dell'utente non viene
  cancellata, e alcuni punti trattano «non ho potuto chiedere se il desktop è vivo» come «è chiuso» (`session_alive()` e
  l'uscita in `child.c`). Casi forzati, non provocabili sul banco; correzione piccola consigliata, **non fatta**. Su Debian
  il codice è lo stesso, quindi vale uguale; non misurato su Debian.
- **E4 (piccoli scatti nel video da Chrome su Android):** misurati su Ubuntu (nessun pacchetto perso, un fotogramma su venti in
  ritardo di pochi millisecondi); causa non distinta fra telefono, rete e riproduttore. Non bloccante; su Debian non misurato.

---

## G. Banco di prova: lezione per le prossime distribuzioni (26 nov 2026)

### G1. Il server si è bloccato quattro volte con una VM Debian sulla scheda Radeon passata
- **Quando e come si è visto:** 26 nov, durante le prove a macchine virtuali. Alle 01:17 e alle 08:26 il server intero si è
  bloccato (né ping né ssh) sulla VM `kde`, nello stesso punto: la prova «accesso locale vero» (P7), cioè il riavvio di `sddm`
  dentro la VM. La terza volta, il 26 nov alle 09:14, sulla VM `xfce` durante la voce `desktop` di `all.sh`, mentre partiva anche la VM `costruzione`; la quarta ancora sulla VM `xfce`, mentre si installava il pacchetto. Ogni volta serviva il ripristino a mano del proprietario.
- **Prima diagnosi, SBAGLIATA:** «il riavvio del display manager con la Radeon passata fa cadere il server». Si è vietato quel passo
  e tutti i simili (nel file `COME-SI-LANCIA.md`), ma è caduto anche dopo, senza riavvii di display manager (installazione del
  pacchetto): la causa era un'altra.
- **Causa vera:** nell'ospite Debian il driver `amdgpu` del kernel 6.12 metteva a dormire e risvegliava di continuo la scheda
  (nel registro: `amdgpu: SMU is resuming...`, 19 volte in 9 minuti). La scheda era passata senza monitor e il suo controllo
  dei consumi (`runpm`) la addormentava; nel server comparivano errori PCIe (`CmpltTO`, `vfio_bar_restore`) un attimo prima del blocco.
- **Cura:** `amdgpu.runpm=0` nella riga di avvio del kernel di **ogni VM Debian del banco**, messo PRIMA di dare la
  Radeon alla VM (`GRUB_CMDLINE_LINUX` in `/etc/default/grub`, poi `update-grub`; copia di prima in
  `/etc/default/grub.prima-runpm`). Controlli prima di ogni giro: `/proc/cmdline` contiene `amdgpu.runpm=0`;
  `/sys/module/amdgpu/parameters/runpm` vale 0; nel registro del kernel `SMU is resuming` non compare mai. Se uno non torna,
  si spegne la VM. Da allora nessun blocco, su GNOME, KDE, XFCE e LXQt, comprese installazioni e prove complete.
- **Il divieto di P7/P8** non era la cura: resta scritto in `studio/prove-1.2.0/COME-SI-LANCIA.md`.
- **Su una distribuzione nuova:** (1) scheda passata a una VM senza monitor ⇒ guardare subito `runpm` dell'ospite; (2) dopo una
  caduta del server non fidarsi della prima ipotesi: cercare nel registro del kernel il minuto prima del blocco; (3) un'ipotesi
  si verifica con una prova che *dovrebbe* fallire, non solo con una che passa.

### G2. La costruzione del `.deb` senza contenitori
- **Regola del proprietario:** niente contenitori. Il pacchetto si costruisce in una VM del server, `costruzione`
  (mai con la Radeon), con `build/build-deb-vm.sh [etichetta]`: accende la VM, costruisce, controlla con `lintian` (gli errori
  fanno fallire la costruzione), spegne. Uscita in `/media/REMOTIX-DEBIAN/pacchetti/<etichetta>/`. I file vecchi
  (`build/build-deb.sh`, `build/Containerfile`) restano ma non si usano.
- **Provato:** `remotix_1.2.0-1+deb13_amd64.deb`, `lintian` senza errori né avvisi.

### G3. Controlli nuovi nel giro di prove
- **AppArmor:** `prove/check-apparmor.py` legge nel registro del kernel le righe del profilo `remotix_network` dall'inizio del
  giro; se il profilo non è caricato o il giro non ha un orario di partenza, risponde BLOCKED e non «nessuna riga»
  (è così che si è trovata la voce F10).
- **Core dump:** `systemd-coredump` installato nelle VM di prova, così un programma di REMOTIX che muore lascia traccia e la prova lo vede.
- **Dopo la prova di rimozione:** nessun file di REMOTIX in `/etc /usr /var /root /home`; l'unica eccezione trovata era una cache di
  Mesa di root, ora evitata (F12).
- **Metodo:** P1-P6 delle prove «locale chiude remoto» girano su tutti i desktop; P7/P8 (accesso locale grafico vero) sulle
  quattro live in mano al proprietario, che il 26 nov le ha provate a mano e sono andate tutte bene.

---

## H. Rinviati o aperti nella 1.2.0 (non bloccanti)

### H1. `media/screen-updates` di poco oltre la soglia su GNOME, KDE e LXQt
- **Misurato:** il tempo fra il cambio di un contatore nella sessione e la sua comparsa nel browser è 1,0-1,5 secondi
  (GNOME 1,05-1,2; KDE 1,03-1,06; LXQt 1,5), la soglia della prova è 1,0. Nessun passo indietro, animazione a 58-61 fotogrammi al secondo.
- **Che cosa non si sa:** la causa. Stesso ordine di grandezza su tutti i desktop, quindi non è di uno; sospetti: VM senza monitor,
  strumento, carico del server. Soglia non allargata. Da confrontare con la 1.0.1 e con una macchina vera.

### H2. `pkexec` su GNOME
- **Noto, su tutte le distribuzioni:** nella prova `desktop/users-shell-and-environment` `pkexec` dà `SHELL` vuoto e non mostra
  la finestra di password. Il resto della prova (terminale, cartella personale, gruppi) è a posto. Voluto così, come nel giro di prove da sempre.

### H3. `kbd-not-producible` su Firefox in LXQt
- **Probabile difetto dello strumento** (da confermare): la prova passa su Chrome; su Firefox il testo scritto è giusto
  (`entry 'xyz'`) e non arriva nulla di finto al desktop, ma una riga attesa del registro compare una volta su due. Su KDE il
  FAIL del primo giro non si è ripresentato col pacchetto aggiornato.

### H4. P7/P8 automatiche solo su GNOME
- Le prove automatiche «accesso locale vero con programmi aperti» (P7/P8) sono girate solo su GNOME; sulle altre VM sono vietate per
  la sezione G1. Il proprietario ha provato la chiusura per accesso locale con programmi aperti sulle quattro live Debian 13.8.0, su macchina vera, il 26 nov 2026: GNOME, KDE, XFCE, LXQt tutte OK.

### H5. Da verificare altrove
- Se su Fedora 1.2.0 la lingua scelta dall'utente arriva al desktop KDE (mai misurato).
- Se Xubuntu ha `xiccd` (per Ubuntu 1.2.0).
- `xfconfd` resta nella lingua di sistema su XFCE (F1).
