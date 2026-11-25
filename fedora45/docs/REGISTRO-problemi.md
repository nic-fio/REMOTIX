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
  difetto. Lo stesso valeva da agosto per i pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine, tolti dalla pagina ma ancora
  nelle prove: allineate il 18 nov 2026 (`page-cad-hidden`: fuori dalla diagnostica la pagina non mostra quei
  pulsanti; `page-ctrl-alt-end-passes`: Ctrl+Alt+Fine arriva al desktop come ogni altra combinazione).
- **Regola:** quando si cambia un comportamento per decisione, nello stesso lavoro si aggiornano le prove che lo
  descrivono. Una riga rossa «già nota» è una riga che prima o poi nasconde un difetto vero.

### B3-bis. Una riga rossa uguale su tutti i desktop: prima si dimostra, poi si archivia
- **Che cosa è successo (18 nov 2026, Ubuntu 26.04):** tre righe (`mouse-drag` con Chrome e con Firefox,
  `tap-and-half-drag-select`) fallivano uguali sulle quattro macchine, mentre su Debian 13 erano verdi.
- **Come si è visto:** il testo risultava selezionato, ma la finestra di prova non registrava il rilascio del tasto.
- **Causa:** non era un difetto del prodotto. Guardando gli eventi che il client riceve davvero (`WAYLAND_DEBUG`) il
  rilascio arrivava. Con GTK 4.22 (Ubuntu) il campo di testo, quando reclama il trascinamento, nega la sequenza ai
  gesti delle finestre che lo contengono; con GTK 4.18 (Debian) no. Il gesto della finestra di prova non vedeva più il rilascio.
- **Soluzione:** la finestra di prova legge il rilascio dagli eventi grezzi, che non dipendono da chi reclama la
  sequenza; il controllo continua a fallire se il rilascio non arriva davvero.
- **Lezione:** una riga rossa uguale su tutti i desktop fa sospettare lo strumento, ma va dimostrato prima di archiviarla.
- **Su una distribuzione nuova:** se una prova di input fallisce su tutte le macchine, guardare prima gli eventi grezzi.

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

### C4. Su Ubuntu vero ogni accesso era rifiutato: una riga del profilo di sicurezza vietava tutti i socket locali
- **Quando:** 19 nov 2026, prima prova del proprietario su una macchina vera (live Ubuntu 26.04.1, kernel 7.0).
- **Che cosa è successo:** password accettata, poi «the server could not open your session, and it is not your
  mistake» per qualunque utente. Nel registro: `logind unreachable (Unable to create socket: Permission denied)`.
- **Causa:** nel profilo AppArmor del lato rete la riga `deny unix addr=@*,` voleva vietare solo i socket «astratti»,
  ma porta con sé anche il permesso di *creare* un socket, che non ha indirizzo: sul kernel di Ubuntu (che controlla
  i socket unix) vietava tutti i socket locali, quindi niente D-Bus e niente domanda a logind; REMOTIX, non potendo
  verificare l'assenza di una sessione locale, rifiuta. Un `deny` vale anche con il profilo in modalità «complain»
  e non lascia righe di avviso.
- **Perché non si era visto:** nei contenitori di prova AppArmor non è in vigore; sul kernel di Debian 13 quella riga
  non ha effetto.
- **Soluzione:** due righe che nominano le operazioni (`deny unix (bind, listen) addr=@**,` e
  `deny unix (connect, send, receive) peer=(addr=@**),`; due asterischi perché uno solo si ferma alla barra `/`). Misurato sulla macchina: bus di sistema e journal
  raggiungibili, socket astratti ancora rifiutati, controllo delle sessioni locali «CONNECTED».
- **Limite noto:** resta permesso l'«autobind» (un socket che si fa dare dal sistema un nome astratto a caso): serve
  solo a farsi raggiungere da un processo complice, non a raggiungere i socket della macchina, e il secondo muro
  (landlock) resta. Da riguardare quando il profilo passerà da «complain» a «enforce».
- **Su una distribuzione nuova:** i contenitori non provano il profilo di sicurezza: prima di chiudere serve un
  accesso riuscito su una macchina vera (o virtuale) con AppArmor/SELinux in vigore, e nel registro di avvio va
  letta la riga «§5.1 … CONNECTED». Dopo un passaggio a un kernel nuovo, riprovare anche Debian.

### C5. Su Ubuntu i programmi «snap» e Flutter non digerivano il profilo delle impostazioni della sessione remota (GNOME)
- **Quando:** 19 nov 2026, stessa prova su macchina vera della voce C4 (live Ubuntu 26.04.1), poi misure sulla macchina
  virtuale `ubuntu` (dconf 0.49, GNOME 50).
- **Che cosa è successo:** il programma di installazione della live mostrava «Something went wrong» (`Unknown DConf
  source`); Firmware Updater e Security Center dicevano `No DConf source to write to`. Il desktop si apriva comunque.
- **Causa:** REMOTIX passava le sue regole alla sessione con la variabile `DCONF_PROFILE` che puntava a un profilo di tre
  strati in `/run/user/<uid>/remotix/dconf/` (righe `file-db:` e `service-db:`). I programmi Flutter di Ubuntu hanno un
  lettore dconf proprio che conosce solo `user-db` e `system-db` e, a una riga diversa, scarta tutto il profilo; gli snap
  confinati, con un `XDG_RUNTIME_DIR` diverso, non possono nemmeno aprire quel percorso.
- **Perché non si era visto:** nei contenitori non c'è nessuno snap e AppArmor non agisce; Debian non ha quei programmi.
- **Soluzione (19 nov 2026):** i blocchi diventano il database di sistema `/etc/dconf/db/remotix`, compilato dal postinst
  con `dconf compile` da file chiave che il pacchetto genera IN COSTRUZIONE dalla tabella `DCONF_KEYS` di `session.c`
  (`remotix --dconf-keyfiles`: una sola lista); tolto da postrm a `remove` e `purge`. La sessione non ha più
  `DCONF_PROFILE` (né nell'ambiente né nel gestore utente): scrive `$XDG_RUNTIME_DIR/dconf/profile`, il file che dconf
  legge quando la variabile manca, con la prima riga del profilo di base, `system-db:remotix`, `user-db:remotix` e il
  resto del profilo di base. I valori che cambiano a sessione viva (la tastiera) vanno nel database utente `remotix`
  (`~/.config/dconf/remotix`, scritto dal servizio dconf come `/ca/desrt/dconf/Writer/remotix`) invece che nello strato
  in memoria; svuotato e riempito alla nascita. Misurato prima su macchina virtuale: stessi blocchi, cambio a sessione
  viva visto da `gsettings monitor`, file `user` identico, nessuna eccezione dei programmi Flutter.
- **Fine sessione:** la «cintura» agisce sul nuovo file, che comincia con una riga di riconoscimento: a sessione finita
  viene TOLTO se il profilo di base è quello predefinito (un file assente è ciò che un accesso locale aveva prima di noi),
  altrimenti riscritto con il solo profilo di base; ogni nascita lo rimette. Un `DCONF_PROFILE` dell'amministratore resta
  il profilo di base e, nella sessione, la variabile punta al nostro file (altrimenti dconf lo ignorerebbe). La pulizia
  del gestore utente continua a togliere `DCONF_PROFILE` anche se lo ha lasciato la versione precedente del pacchetto
  (aggiornamento a caldo).
- **Ripiego dichiarato:** se `/etc/dconf/db/remotix` manca o non si legge, o `dconf` manca, la sessione torna al
  comportamento di 1.0.0 (tre strati compilati al volo, `DCONF_PROFILE` col percorso) e il registro dice «DECLARED
  FALLBACK, D-015 (19 Nov 2026)».
- **Rilievi del revisore (stesso giorno):** un profilo di runtime che non è nostro (nessun marchio nella prima riga) non si
  sovrascrive mai: si usa il ripiego dichiarato, che lo prende come base. Il file di runtime si scrive alla nascita (o
  all'avvio del figlio solo se si ritrova un desktop vivo): un figlio che muore prima non lascia nulla leggibile da un
  accesso locale. Se il profilo di base è dichiarato da un `DCONF_PROFILE` (nell'ambiente del figlio o solo nel gestore
  utente, es. `environment.d`) il file porta nella riga di testa il segno «referenced by DCONF_PROFILE: rewrite, never
  remove» e a fine sessione si riscrive, mai si toglie. Il servizio, all'avvio, compila `/etc/dconf/db/remotix` se manca
  o è più vecchio dei file chiave (dconf-cli può arrivare dopo di noi; un aggiornamento può fallire).
- **Limiti noti:** (1) un figlio che muore DOPO la nascita lascia il file finché il lato root non chiude il desktop
  orfano (strada già esistente della chiusura leggera, che esegue la cintura come utente); un accesso locale di un utente
  SENZA alcuna sessione REMOTIX nota non esegue la cintura (servirebbe un fork nuovo come utente): probabilità bassa,
  perché il file ora nasce solo alla nascita. (2) Aggiornamento a caldo con un desktop nato dal modello vecchio (strato in
  memoria): il nuovo figlio scrive nel database `remotix`, il desktop legge ancora lo strato in memoria, quindi un cambio
  di tastiera non lo raggiunge fino alla nascita seguente; il modello vecchio su Ubuntu non è mai stato distribuito.
  (3) A `purge` il file `~/.config/dconf/remotix` si toglie come l'utente (stesso schema dello stato in
  `~/.local/state/remotix`): solo quel file regolare, senza seguire collegamenti; gli utenti che il sistema non elenca in
  quel momento (es. directory di rete non raggiungibile) lo conservano, ed è inerte senza REMOTIX.
- **Vita del desktop all'avvio del figlio:** tre esiti, come la regola di `session_life()`. Vivo: il file runtime si scrive
  subito. Morto: si neutralizza un file nostro rimasto e si scrive alla nascita. SCONOSCIUTO (nessuna risposta in tempo):
  non si tocca nulla, né si scrive né si toglie, e il registro lo dice; la nascita lo scrive se manca. Il servizio, a ogni
  avvio, compila `/etc/dconf/db/remotix` in un file temporaneo e sostituisce il database solo se il contenuto è diverso
  (non confronta le date, che non vedrebbero un database vecchio compilato dopo la costruzione del pacchetto).
- **Non provato sul campo:** il ramo «vita SCONOSCIUTA» all'avvio del figlio (sia nel modello nuovo sia nel ripiego) e il
  ramo «database diverso/più vecchio» della compilazione all'avvio del servizio (provato solo «database mancante»).
- **Differenze da dichiarare:** un piccolo file nostro `~/.config/dconf/remotix` nella casa dell'utente (tre chiavi della
  tastiera; il file `user` non si scrive mai; il file `remotix` si toglie con `apt purge`); il profilo della sessione sta
  in `$XDG_RUNTIME_DIR/dconf/profile`, quindi lo leggono anche altri programmi nati nel frattempo con quella cartella
  (prima: solo chi ereditava la variabile dal gestore utente). Il profilo obbligatorio `/run/dconf/user/<uid>` continua a
  vincere ed è dichiarato come prima.
- **Su una distribuzione nuova:** provare con i programmi snap veri dentro la sessione remota (nessuna eccezione dconf nel
  registro, nessun DENIED di AppArmor); verificare che dconf legga il profilo di runtime senza `DCONF_PROFILE` (dconf
  0.49 sì; Debian con dconf 0.40 non misurato); controllare che il postinst abbia fatto `/etc/dconf/db/remotix`.

---

### C6. «Nessuno spegne la macchina»: il riavvio restava possibile all'utente seduto al computer (20 nov 2026)
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
  riavviare dal menu della schermata di accesso senza accedere. Con la regola nuova: tutte e 19 negate. 
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
- **KDE (Kubuntu 26.04, Plasma 6.6), uscita chiesta nei primi secondi: si perdeva (18 nov).** Causa: «Esci» avvia
  `plasma-shutdown`, che chiede a systemd di fermare la sessione grafica; se in quel momento un servizio (di solito il
  portale) è ancora in avvio, systemd rifiuta, `plasma-shutdown` non lo ripete ed esce. Il desktop resta vivo e il
  client non viene avvisato. Il vecchio rimedio aspettava che un'unità si fermasse, ma su Plasma 6.6 non si ferma mai.
  Cura: REMOTIX si accorge che `plasma-shutdown` ha finito, chiede a ksmserver se sta davvero chiudendo e, solo se
  sì, dopo 4 secondi ripete lo stop (prima in modo normale, poi «replace» che passa anche con un avvio in coda). Se
  lo stop resta rifiutato per circa un minuto, chiude la sessione con la strada che il prodotto ha già.
  Limiti noti: lo spegnimento e il riavvio chiesti dal desktop non rilasciano il nome e, rifiutati nei primi
  secondi, resterebbero persi (raggiungibili solo senza le voci di menu, che REMOTIX toglie); un riavvio di KWin
  durante l'attesa azzera la richiesta (raro).
  **Lezione:** il primo rimedio (fermato in revisione, mai rilasciato) chiudeva la sessione appena `plasma-shutdown` partiva, quindi anche con un documento
  non salvato aperto (KWin aspetta la risposta dell'utente) o dopo «Annulla»: lavoro perso. Le prove a desktop
  vuoto non bastano. Un'uscita va provata anche con lavoro non salvato (salva / scarta / annulla) e con la finestra
  «Esci» annullata. Su una distribuzione nuova, ripetere queste prove prima di fidarsi dell'uscita.
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
- Coordinate del mouse su XFCE nell'angolo coperto dal pannello; un controllo su GNOME voluto così (`pkexec`); primo tocco da telefono su GNOME, saltuario.

### E3. Variabili del gestore utente: la «foto» può essere vecchia, e «non ho potuto guardare» vale «chiuso» (19 nov 2026)
- **Visto:** dal revisore leggendo il codice, e in una prova sulla macchina virtuale di Ubuntu con un `DCONF_PROFILE`
  dell'amministratore messo solo nell'ambiente dell'utente (`environment.d`).
- **Che cosa succede:** quando è il lato root a chiudere un desktop (per esempio perché il servizio si ferma), la «foto»
  dell'ambiente dell'utente presa prima della sessione non viene cancellata. Alla sessione successiva la pulizia la crede
  ancora valida e può togliere dall'ambiente dell'utente una variabile che nel frattempo l'amministratore ha aggiunto.
  La sessione nasce comunque giusta, e senza «linger» l'ambiente si ricrea da solo all'accesso seguente (misurato).
- **Secondo punto, stessa famiglia:** la pulizia dell'ambiente (`session.c`, vicino a `session_alive()`) e l'uscita del
  figlio (`child.c`) trattano «non ho potuto chiedere al desktop se è vivo» come «è chiuso». Nella preparazione delle
  impostazioni questo è stato corretto il 19 nov (tre esiti); in quei due punti no.
- **Deciso:** non corretto ora: casi forzati (foto vecchia + «linger» + nascita fallita; desktop vivo che non risponde
  proprio in quel momento), e non provocabili sul banco. **Correzione consigliata, piccola:** la chiusura fatta dal
  lato root cancelli la foto; i due punti usino i tre esiti.
- **Su una distribuzione nuova:** niente di specifico; da riprendere quando si rimette mano al ciclo di vita.

### E4. Piccoli scatti nel video visto da Chrome su Android (19 nov 2026, macchina virtuale Ubuntu)
- **Visto:** dal proprietario, riproducendo un video (1440p e Full HD) nella sessione remota GNOME, dal telefono Android.
  Dal tablet (Chrome su Linux) non li ha notati.
- **Misurato sul server (40 s di video verso il telefono):** nessun pacchetto perso, 1,5-5 Mbit/s, 60 fotogrammi al secondo
  in 35 secondi su 39 (gli altri: 57, 56, 52, 43); circa un fotogramma su venti partito in ritardo di qualche
  millisecondo; ritardo di rete verso il telefono 8 ms tipico con picchi fino a 125 ms (tablet: 3,5 ms, picchi 27 ms).
- **Non distinto:** telefono (rete Wi-Fi e decodifica HEVC di Android), riproduttore video nella macchina virtuale,
  cadenza dei fotogrammi in una macchina virtuale, percorso di codifica sulla Radeon. Il proprietario propende per il
  telefono («Android fa a pugni con i codec video»).
- **Deciso:** non bloccante, nessuna modifica. **Per chiudere il dubbio:** stesso video dal tablet con la stessa misura
  sul server, e la stessa prova su una macchina vera.

## F. Fedora 45 (da 21 nov 2026)

### F1. Il programma porta ancora il percorso del labwc modificato, che il pacchetto Fedora non contiene (21 nov 2026, passo 1)
- **Visto:** il programma (`src/kwin.c`, costruito con `LABWC=/usr/libexec/remotix/labwc`) cerca ancora il labwc modificato di Ubuntu; il pacchetto
  RPM per Fedora non lo costruisce né lo installa (decisione D2: su Fedora KDE userà KWin da solo).
- **Conseguenza:** KDE non può partire finché non si fa il passo KDE (voluto). GNOME, XFCE e LXQt non usano quel percorso.
- **Deciso:** rimandato al passo KDE (nessuna modifica a `src/` per ora).

### F2. Su Fedora il desktop non partiva con lo stack di accesso copiato da sshd (21 nov 2026, passo 2, GNOME) — RISOLTO
- **Visto (studio):** con la riga `pam_selinux open` il desktop era negato da SELinux (il servizio installato da RPM gira come
  `unconfined_service_t` e non può passare al contesto dell'utente); senza la riga partiva, ma i processi dell'utente restavano «di servizio».
- **Cura:** un modulo SELinux nel pacchetto (`selinux/remotix.te`, `.fc`, `.if`) dà al programma un tipo suo (`remotix_exec_t` → `remotix_t`) con i
  diritti di un programma di login (come sshd), largo per ora; il file di accesso `src/remotix.pam` è lo stack di sshd di Fedora più le nostre righe
  (esclusione di root, `pam_env` con `/etc/locale.conf`). Il passo 5 restringerà il modulo senza rifarlo.
- **Verificato sulla macchina GNOME con la Radeon, SELinux attivo:** accesso dal browser fino al desktop, mouse, tastiera, uscita pulita (0 processi
  dell'utente dopo 13 s), nessun rifiuto di SELinux. I processi dell'utente hanno `unconfined_u:unconfined_r:unconfined_t`, come un accesso ssh.
- **Resta una differenza minore:** il capofila della sessione e il suo primo processo hanno la «gamma» `s0` e non `s0-s0:c0.c1023` come con ssh
  (tutto il resto della sessione ha la gamma piena). La prova con `use_current_range` è peggiore (niente cambio di dominio): non adottata. Anche senza l'opzione `env_params` la gamma resta `s0` (provato il 21 nov): l'opzione non c'entra.

### F3. Finestra di password sul desktop remoto per l'aggiornamento del firmware (21 nov 2026, passo 2, GNOME) — RISOLTO
- **Visto:** GNOME Software chiede all'avvio `org.freedesktop.fwupd.refresh-remote`; chi siede al PC lo ottiene senza password, la sessione remota no,
  e la finestra di richiesta (utente «prova») copriva il desktop e si prendeva mouse e tastiera.
- **Cura:** l'azione è stata aggiunta alle tre già concesse dalla regola `40-remotix-remote-sessions.rules` (decisione del 14 nov: l'aggiornamento
  dell'elenco programmi vale per tutti gli utenti REMOTIX). Verificato: nessuna richiesta, nessun errore di polkit.

### F4. PATH della sessione remota su Fedora (21 nov 2026, passo 2, GNOME) — NOTA
- Con l'accesso locale il PATH include `~/.local/bin` e `~/bin` (li aggiunge la shell di accesso); nella sessione remota è `/usr/local/bin:/usr/bin:/bin`
  (Fedora non ha `/etc/environment`). Non corretto: da decidere se serve (uniformità con Debian/Ubuntu, dove non c'è questa differenza).

### F5. Un utente SELinux «confinato» non può far nascere il desktop remoto (21 nov 2026, passo 2, da trattare al passo 5)
- Se l'amministratore ha mappato un utente su un utente SELinux confinato (`user_u`, `staff_u`), il passaggio di dominio verso il suo contesto
  non c'è: il modulo dà il punto di ingresso (`entrypoint`) solo a `unconfined_t`. Provato solo con utenti «unconfined» (il caso normale di Fedora).

### F6. L'accesso locale chiude il desktop remoto: come si aggancia PAM su Fedora (21 nov 2026, passo 4, GNOME/gdm)
- **Problema:** su Debian/Ubuntu il pacchetto mette una riga in `/etc/pam.d/common-session` con `pam-auth-update`; su Fedora quei file sono
  generati da `authselect` (una modifica a mano sparisce al primo `authselect apply-changes`) e un pacchetto di terzi non può sostituire il profilo
  scelto dall'amministratore.
- **Soluzione:** la riga va nei file PAM della schermata di accesso, non in quelli di sistema. Per gdm (`/usr/lib/pam.d/gdm-*`, file del
  fornitore) lo script `/usr/libexec/remotix/remotix-pam-hook` crea in `/etc/pam.d` un file omonimo = copia del file del fornitore + il nostro blocco
  (prima riga: marcatore «generato da REMOTIX»); se esiste già un file omonimo dell'amministratore, aggiunge solo il blocco marcato e alla rimozione
  toglie solo quello. Lo script gira: nello `%post`, nei trigger RPM (ogni volta che `gdm` viene installato o aggiornato, anche se arriva dopo
  REMOTIX), a ogni avvio del servizio (`ExecStartPre`, con riga nel registro) e alla rimozione (`%preun`). Non tocca mai i collegamenti di authselect;
  scrive su file temporaneo, controlla la forma di ogni riga e rinomina; se qualcosa non torna non tocca nulla e avvisa.
- **Scoperta (da ricordare per le altre schermate di accesso):** su Fedora la riga deve stare PRIMA della prima riga `session`, non dopo `pam_systemd`:
  (1) gdm mette da sé `XDG_SEAT`, `XDG_SESSION_TYPE` e `XDG_VTNR` nell'ambiente PAM prima della pila di sessione, ed è tutto ciò che il programma guarda;
  (2) `pam_selinux open` imposta il contesto dell'`exec` SUCCESSIVO: una riga `pam_exec` dopo di lui spende quell'exec sul nostro programma
  (AVC `entrypoint`, rifiutato). Ogni schermata di accesso va provata così prima di accenderla.
- **SELinux:** il programma gira nel proprio dominio `remotix_hook_t` (`xdm_t` non è allargato: ottiene solo il passaggio di dominio); può solo
  cercare l'utente e lavorare nella cartella `/run/remotix/prelocal` (tipo `remotix_prelocal_t`). 0 rifiuti con il dominio in vigore.
- **Provato sulla macchina GNOME (Radeon, SELinux attivo), con l'accesso automatico di gdm come accesso locale (la schermata di accesso non si
  può fotografare con la Radeon e i tasti mandati alla cieca non hanno raggiunto il campo del nome):** (1) desktop remoto aperto → accesso locale:
  il remoto si chiude in 1-2 s, la sessione locale (seat0) resta attiva e la shell di GNOME è viva dopo 45 s, nessun nuovo file di errore di
  `gnome-session`; (2) desktop remoto «in chiusura» dopo un `kill -9` del suo capofila, e riavvio del servizio con il desktop aperto: accesso locale
  riuscito; (3) con la sessione locale attiva, l'accesso remoto è rifiutato («that user is already signed in locally»); (4) `dnf reinstall gdm`,
  `dnf upgrade gdm` (51.0 → 51.1.1), `authselect apply-changes` e cambio di funzione e ritorno: la riga c'è ancora, il file è sempre la copia esatta
  del file del fornitore corrente + il blocco; un file lasciato vecchio viene rigenerato dal trigger; un file mancante viene rimesso all'avvio del
  servizio (con riga nel registro); un file dell'amministratore riceve solo il blocco e alla rimozione torna identico byte per byte; un collegamento
  simbolico non viene toccato; (5) rimozione: nessun file nostro in `/etc/pam.d`, tutti gli altri file PAM identici (45 file, sha256), modulo
  SELinux tolto; (6) accesso locale senza remoto: 0,4 s contro 0,3 s senza la riga (nessuna differenza misurabile), nessun errore.
- **Non visto:** la schermata di accesso vera (password digitata) e le altre schermate di accesso (lightdm, sddm, plasmalogin: ognuna va provata
  al suo turno, vedi la scoperta sull'ordine delle righe). Il rifiuto `{ view } key stratisd_t` di `xdm_t` compare anche senza REMOTIX: non è nostro.
- **Prova con la schermata di accesso vera (macchina virtuale, schermo visibile, 21 nov 2026):** scelta dell'utente `prova` con le frecce, password
  digitata: desktop raggiunto, sessione `gdm-password` su seat0 (classe `user`, wayland), `gnome-shell` vivo, nel registro di sistema il modulo PAM
  `pam_exec` è il primo della sessione e non c'è nessun errore né rifiuto di SELinux. Blocco dello schermo e sblocco con password: lo sblocco fa
  solo l'autenticazione (non apre una sessione), quindi il nostro programma non viene chiamato e non succede nulla. Uscita, password SBAGLIATA
  (la schermata ripropone il campo), poi quella giusta: riesce. Il programma non lascia traccia nel registro quando non c'è un desktop remoto
  (la riga è `quiet`): la sua esecuzione si vede da `pam_exec` fra i moduli riusciti della sessione.
- **Rafforzamenti dello script dopo la revisione (21 nov 2026):** ogni passo della composizione di un file PAM ha il suo esito controllato; prima
  di installare si verifica che il file composto, senza il nostro blocco e il nostro marcatore, sia identico alla sorgente (un file troncato non
  passa); un blocco con BEGIN e senza END non viene toccato; se la copia NOSTRA non si riesce a rinnovare viene cancellata (meglio nessun gancio
  che un file di accesso vecchio); `remove` toglie anche i file temporanei lasciati da un'interruzione; la cartella di prova si indica solo con
  `--test-root`, non dall'ambiente. Nel pacchetto, la rimozione dell'aggancio avviene dopo l'arresto del servizio.

### F7. KDE su Fedora: KWin da solo, senza labwc (21 nov 2026, passo 3, decisione D2) — FATTO
- **Che cosa è cambiato:** il desktop remoto KDE nasce con `kwin_wayland --virtual` (il programma `remotix --kwin-virtual` avvia solo il piccolo servizio che risponde a
  `org.freedesktop.ScreenSaver` e poi diventa il wrapper di KWin); niente labwc, niente patch, niente copie statiche di wlroots. Il cambio di dimensione dell'uscita di KWin è nel
  programma (`kwin_output_resize()`, protocollo `kde_output_management_v2` ≥ 22, modo personalizzato con `add_cvt`: qualsiasi misura, anche dispari; ~3 ms).
- **Rifiuto pulito:** se KWin non offre quel protocollo (KWin più vecchio di 6.8) la sessione è RIFIUTATA con un messaggio chiaro (registro del servizio e utente); nessun ripiego silenzioso.
- **Lo stream non segue il cambio di dimensione:** si smonta, si cambia l'uscita e si rimonta (ordine invariato rispetto a prima); uno stream nuovo prende la misura che gli si offre.
- **Il segno «questo KWin è di REMOTIX»** (per fermarlo a fine sessione, `kdehost.h`): l'opzione `--kwin-virtual` nella riga di comando e `REMOTIX_KDE_HOST=1` nell'ambiente
  dell'unità; non possono servire a toccare l'unità di un altro utente (il segno non sceglie né l'utente né l'unità: contano il gruppo di controllo e il proprietario del processo).
- **Codice del labwc-per-KDE rimasto ma non più raggiungibile** (da togliere dopo le prove del proprietario): in `kwin.c` la parte labwc di `kwin_nested_alive()`, `kwin_host_*`, `mode_*`;
  in `kwin.h` il riquadro «nested» e le cinque funzioni `kwin_host_*`; in `child.c` il ramo «nessun host» dopo il cambio; in `main.c` il vecchio `--kwin-nested` ora risponde con un errore;
  nel `Makefile` `-DREMOTIX_LABWC` (solo una stringa: il pacchetto non ha bisogno del labwc statico).

### F8. KWin ricorda l'ultima dimensione di `Virtual-0` (21 nov 2026, passo 3) — NOTA PER IL MANUALE
- **Visto:** KWin salva il modo corrente e i modi personalizzati dell'uscita in `~/.config/kwinoutputconfig.json` (file di KWin, nella casa dell'utente): `--width/--height` della riga di
  avvio valgono solo la prima volta. Il programma quindi controlla la dimensione alla nascita e la corregge PRIMA di montare lo stream (stessa funzione del cambio a caldo).
- **Il file non si tocca** (è di KWin; contiene una voce `Virtual-0`, innocua per il desktop locale che usa altre uscite). Il manuale di Fedora deve dirlo.

### F9. «Il locale chiude il remoto» su plasmalogin (21 nov 2026, passo 4, KDE) — FATTO
- **Verificato sul campo:** l'aiutante di plasmalogin mette `XDG_SEAT`, `XDG_SESSION_TYPE`, `XDG_SESSION_CLASS` e `XDG_VTNR` nell'ambiente PAM PRIMA di `pam_selinux open` (prova con un
  programma che stampa l'ambiente, prima riga di sessione), quindi `remotix-pam-hook` funziona com'è: file del fornitore `/usr/lib/pam.d/plasmalogin` e `plasmalogin-autologin`
  (non il greeter); attivato nell'elenco predefinito e trigger sul pacchetto `plasma-login-manager`.
- **Provato come per gdm:** desktop remoto aperto → accesso locale (il remoto si chiude in 1-2 s); remoto «in chiusura» dopo `kill -9` e riavvio del servizio con il desktop aperto; locale attivo →
  remoto rifiutato; `dnf reinstall plasma-login-manager`, `authselect apply-changes`/cambio di funzione, file rimesso all'avvio del servizio, file dell'amministratore; rimozione byte per byte; accesso locale
  senza remoto (0,2 s contro 0,3 s); accesso con password dalla schermata vera (macchina virtuale, foto). Alla chiusura forzata del desktop remoto alcuni programmi di sfondo di KDE
  (`kdeconnectd`, `kalendarac`) lasciano un file di errore: abortiscono quando KWin sparisce (avviene a ogni chiusura forzata della sessione remota, non è dell'aggancio).
- **Trucco di prova per la schermata di plasmalogin dalla tastiera:** una barra spaziatrice per svegliarla finisce nel campo del nome; si usa un tasto neutro (Maiusc), poi «nome» + Invio, poi «password» + Invio.

### F10. Rimandato al passo 5: `remotix_t` e la lettura di `/proc/<pid>/environ` (21 nov 2026)
- Il secondo segno «questo KWin è di REMOTIX» (`REMOTIX_KDE_HOST=1`, `kdehost.h`) si legge da `/proc/<pid>/environ` dei processi dell'utente. Oggi `remotix_t` è senza limiti (unconfined), quindi funziona.
- **Quando `remotix_t` sarà confinato** servirà una regola esplicita (lettura di quei file `/proc` e `sys_ptrace` sui processi utente, solo in lettura); senza, il secondo segno smette di funzionare IN SILENZIO e resta solo il primo (`--kwin-virtual` nella riga di comando, che si legge da `cmdline`). Va provato col modulo confinato.

### F11. Incognite ancora aperte sul KDE di Fedora: «da vedere nelle prove del proprietario» (21 nov 2026)
- **I11** DMA-BUF verso il codificatore: il percorso ha funzionato in tutte le prove sul banco, ma non è stato isolato né misurato a parte.
- **I2** forma e posizione del cursore dopo un cambio di dimensione: provate sul banco (cursore a testo, freccia, bordo; nessun doppio cursore), ma da guardare a occhio dal proprietario su uno schermo vero.
- **I13** le sonde `rxout`/`rxcast` su KWin 6.8.3: il prodotto ripassa sulle prove principali con 6.8.3, ma le sonde da sole non sono state rifatte.

### F12. Più schede grafiche: non provabile sul banco (21 nov 2026) — NOTA PER IL MANUALE
- Il banco ha una sola Radeon passata alla macchina virtuale: la scelta della scheda con KWin da solo (`--virtual`, nessuna scelta di scheda nel drop-in) non si può provare con due schede. Il manuale deve dirlo come «non provato».

### F13. KWin non risponde o non accetta la misura: che cosa fa il prodotto (21 nov 2026, correzione del revisore)
- Uscita di KWin esistente ma KWin dice no o tace (FAILED / TIMED_OUT): lo stage si monta alla misura che KWin ha, con una riga «DECLARED FALLBACK» nel registro; la pagina riscala. Niente schermo nero.
- KWin senza il protocollo (NOT_SUPPORTED): UNA riga nel registro, il messaggio all'utente (0x0E) e la sessione grafica viene chiusa dalla stessa strada del rifiuto per la scala (`fatal`); niente tentativi all'infinito.
- KWin o la sua uscita non ancora pronti (NOT_FOUND, NOT_INITIALIZED, connessione persa): si ritenta, con una riga di registro ogni 5 s (con il conto dei tentativi saltati).
- ⚠ Limite noto (22 nov 2026): un KWin lento OLTRE i 3 s alla nascita fa partire il ripiego (si monta alla misura che ha); quella misura resta vecchia fino al riaggancio successivo.
- Il dialogo con KWin ha ora una scadenza vera (poll sul descrittore, non `wl_display_roundtrip`) e libera tutti gli oggetti prima di chiudere la connessione.

### F14. Il ridimensionamento a caldo non esiste, su nessun desktop (21-22 nov 2026, passo 3, correzione del revisore) — NOTA
- Il prodotto chiede la misura del desktop SOLO alla nascita e al riaggancio (`ask_canvas("the attach")`); con la sessione viva ridimensionare la finestra del browser non cambia mai il desktop, la pagina riscala l'immagine (`renegotiate_view` → `fit_view`; decisione del proprietario del 17 ago 2026, DECISIONS.md §5.1-bis). Vale per tutti i desktop, non è una scelta di KDE.
- Provato su KDE (`prove/check-kde-live.py`): 8 ridimensionamenti di fila della finestra viva (anche misure dispari: 1001x601, 901x555, 777x513) con Firefox X11 e Chromium aperti: il desktop resta 1344x768, il click al 60%/50% cade al 60%/50%, dopo ogni cambio arrivano 49-80 immagini nuove a un carattere digitato.
- Il «cambio di misura» vero (riaggancio con un'altra misura) è provato da `check-kde-resize.py` (10/10 e 6/6 con Chromium).

### F15. SELinux: un `avc: denied { view }` di `gdm-session-worker` su un portachiavi di `stratisd_t` (22 nov 2026) — NON NOSTRO
- Su Fedora 45 con gdm, ogni accesso LOCALE da gdm lascia un AVC `xdm_t` → `stratisd_t` `{ view }` su `key`. Provato A/B nella stessa macchina: compare uguale con il gancio PAM di REMOTIX tolto (1 per accesso, con e senza). Quindi `ausearch -m avc` vuoto dopo un accesso locale da gdm non è ottenibile su questa installazione; l'AVC non viene da REMOTIX. Con plasmalogin, 0 AVC.

### F16. I programmi di sfondo di KDE abortiscono se la sessione remota viene chiusa «da fuori» (22 nov 2026) — DA SAPERE
- Misura (VM `kde`, `coredumpctl`): uscita normale dal remoto (Log Out) → 0 file di errore; chiusura forzata della sessione remota (`loginctl terminate-session`) → 27 file in 25 s (`kaccess`, `kded6`, `gmenudbusmenuproxy`, `xembedsniproxy`, `org_kde_powerdevil`, `plasmashell`, `xdg-desktop-portal-kde`: SIGABRT quando KWin sparisce prima di loro); uscita locale di Plasma senza REMOTIX, normale o con `terminate-session` → 0.
- Causa probabile: alla chiusura da fuori il prodotto ferma per primo il servizio di KWin («stop» della nostra unità), mentre il resto di Plasma è ancora vivo. Non corretto qui; da decidere se fermare tutto lo scope insieme.

### F17. Il file del servizio firewalld non era un XML valido (22 nov 2026, passo XFCE) — CORRETTO
- **Visto:** su una VM nuova `firewall-cmd --reload` rifiutava il servizio («not well-formed … line 3»): il commento di `rpm/remotix.firewalld.xml` conteneva `--add-service` (due trattini dentro un commento XML sono vietati). Quindi il servizio `remotix` non esisteva per firewalld e la porta 7447 non si poteva aprire con `--add-service=remotix`.
- **Corretto:** commento riscritto senza trattini doppi (pacchetto x2). Controllato: il file ora si legge come XML e firewalld lo accetta. Gli altri file di pacchetto XML da controllare con lo stesso metro: nessuno.
- **Per il banco:** `rpm -U` non apre la porta (voluto: «definito, non aperto»): sulla VM `xfce` serve `firewall-cmd --reload` e `--add-service=remotix` (solo a runtime).

### F18. XFCE su Fedora 45 (lightdm) in modo virtuale: che cosa regge e che cosa aspetta la Radeon (22 nov 2026, passi 2 e 4)
- **lightdm attivato** nel gancio PAM (`DEFAULT_DMS`) e nei trigger del pacchetto `lightdm`. File: `/usr/lib/pam.d/lightdm` e `lightdm-autologin` (non il greeter, che non porta la riga). Il blocco va subito dopo `pam_selinux close` (prima di `pam_selinux open`), come per gdm e plasmalogin.
- **Verificato sul campo, accesso con password alla schermata vera di lightdm:** nell'ambiente PAM, al momento del gancio (`open_session`, contesto `xdm_t`), ci sono `XDG_SEAT=seat0`, `XDG_SESSION_TYPE=x11`, `XDG_VTNR=7`, `DISPLAY=:0`, `XDG_SESSION_DESKTOP=xfce`. `XDG_SESSION_CLASS` NON c'è ancora (lo mette `pam_systemd` dopo): `local_login.c` lo accetta vuoto e accetta `x11`. Sessione locale: `Type=x11 Class=user Seat=seat0 Service=lightdm`.
- **Tre cose NON si possono provare senza la scheda** (il remoto non viene ammesso: «the server and this page have nothing in common to speak», non c'è codifica H.264 in una VM senza Radeon): «remoto aperto → accesso locale chiude il remoto», «orfano A1», «accesso locale attivo → remoto rifiutato», e tutto il desktop remoto visibile (input, ciclo di vita, D7). Pronto per quel giro: `prove/giro-xfce-radeon.sh`.
- **Pacchetti che servono a XFCE in remoto:** nello spec c'erano già `Recommends: labwc, wlr-randr, xorg-x11-server-Xwayland, dconf, dejavu-sans-fonts` (con `dnf install` arrivano: labwc 0.20.2, wlr-randr 0.5.0; con `rpm -U` no). Nessun `Requires` in più: il pacchetto non porta mai un desktop. Messaggio d'errore dello spec: citava solo gdm.
- (22 nov 2026) `remotix-pam-hook check` contava anche file di lightdm che non esistono: ora `lightdm` si comporta come gdm e plasmalogin (solo i file che ci sono davvero, greeter escluso); pacchetto x3. Provato con `--test-root` (gdm + lightdm + lightdm-greeter: il greeter resta senza riga) e sulla VM `xfce` (prova 4 ripetuta).

### F19. LXQt su Fedora 45 (sddm) in modo virtuale: che cosa regge e che cosa aspetta la Radeon (22 nov 2026, passi 2 e 4)
- **sddm attivato** nel gancio PAM e nei trigger del pacchetto `sddm`. ⚠ Diverso dagli altri: i file `sddm`, `sddm-autologin`, `sddm-greeter` stanno in `/etc/pam.d` e sono DEL PACCHETTO sddm (`%config`); non c'è niente in `/usr/lib/pam.d`. Il blocco si aggiunge quindi sul posto (ramo «file dell'amministratore» dello script) e si toglie byte per byte. Finché REMOTIX è installato `rpm -V sddm` segnala i due file come modificati (`S.5....T`); dopo la rimozione resta solo l'ora di modifica (`.......T`). Il greeter non porta la riga.
- **Verificato sul campo, accesso con password alla schermata vera di sddm (greeter Wayland su miriway):** nell'ambiente PAM al momento del gancio (`open_session`, contesto `xdm_t`, prima di `pam_selinux open`): `XDG_SEAT=seat0`, `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `XDG_VTNR=2`, `PAM_TTY=/dev/tty2`. Sessione locale: `Type=wayland Class=user Desktop=LXQt Service=sddm`, 0 AVC. Foto: /media/REMOTIX-FEDORA/tmp/foto/z01-greeter.png, z02-typed.png, z03-desktop.png.
- **Prove 4, 5, 6:** `dnf reinstall sddm`, `authselect apply-changes` e cambio di funzione, il file del pacchetto rimesso com'era (come farebbe una versione nuova) più il trigger, il blocco tolto a mano più riavvio del servizio: sempre 2/2 uguali al file ORIGINALE del pacchetto una volta tolto il nostro blocco; greeter intatto. `remotix-pam-hook remove` e `dnf remove remotix`: `/etc/pam.d/sddm*` byte per byte uguali agli originali (sha256), nessun file nostro in `/etc/pam.d`, modulo, `/run/remotix`, `/etc/remotix`, utente: 0. Accesso locale senza remoto: 0,4 s senza gancio, 0,3 s con (sessione wayland attiva, `lxqt-panel` e `miriway-shell` vivi, 0 AVC).
- **Con `dnf remove remotix`** se ne vanno anche i pacchetti arrivati con lui come dipendenze deboli (labwc, wlr-randr, wlroots, `swaylock` con il suo `/etc/pam.d/swaylock`…): non sono nostri file, è dnf che pulisce. Con `dnf install` tornano.
- **Dipendenze per LXQt in remoto, rispetto a XFCE:** nessuna in più. Servono `labwc` e `wlr-randr` (già `Recommends`); Xwayland c'è di serie, `qlipper` non c'è (Fedora), nessun portachiavi. `dnf` porta anche `lxqt-labwc-session` (parte di labwc): non serve a REMOTIX.
- **Cose da sapere del banco:** due riavvii di sddm ravvicinati fanno scattare il limite di avvii di systemd («start of the service was attempted too often»): serve `systemctl reset-failed sddm`.
- **Aspetta la Radeon** (il remoto non viene ammesso in virtuale, manca la codifica H.264): prove 1 (remoto aperto → accesso locale), 2 (orfano), 3 (locale attivo → remoto rifiutato), desktop remoto LXQt visibile, input, ciclo di vita. Pronto in `prove/giro-lxqt-radeon.sh`.

### F20. Firewall: la riga per il manuale (D5, la porta la apre l'amministratore) (22 nov 2026)
- **Provato sulla VM `lxqt`** (zona `public`, predefinita, interfaccia `enp0s1`; come XFCE: sulla VM `xfce` il comando a runtime è già riuscito col pacchetto x2): dopo F17 `firewall-cmd --reload` conosce il servizio `remotix` (`7447/tcp 7447/udp`); `--add-service=remotix` funziona subito (dal server la pagina risponde 200, prima 000); con `--permanent` la regola sopravvive a `--reload`.
- **Riga per il manuale** (come amministratore): `sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload` — apre TCP e UDP 7447 nella zona predefinita; per un'altra zona aggiungere `--zone=NOME`. Per chiuderla: `sudo firewall-cmd --permanent --remove-service=remotix && sudo firewall-cmd --reload`. Il pacchetto non la apre mai da solo; il servizio systemd resta spento finché l'amministratore non fa `systemctl enable --now remotix`.

### F21. sddm: aggiornamento e rimozione del pacchetto con il nostro blocco dentro il suo file di configurazione (22 nov 2026, correzione del revisore) — CORRETTO (l4)
- **Caso vero** (`rpm -q --qf '[%{FILENAMES} %{FILEFLAGS:fflags}\n]' sddm`): `/etc/pam.d/sddm`, `sddm-autologin`, `sddm-greeter` sono `%config(noreplace)` del pacchetto sddm; lightdm invece ha i suoi file in `/usr/lib/pam.d` (`dnf repoquery -l lightdm`), come gdm e plasmalogin: lì facciamo solo una copia nostra in `/etc/pam.d`, nessun problema di questo tipo.
- **Difetto provato** (pacchetti sddm rifatti sulla VM `costruzione` con release 17 e 18 e una riga di commento in più nel file PAM; pacchetto REMOTIX l2): aggiornamento 16 → 17 con il nostro blocco nel file → RPM tiene il testo vecchio e scrive `.rpmnew`: la versione nuova del fornitore non entra in vigore. Rimozione di sddm → resta `.rpmsave`.
- **La correzione proposta (togliere il blocco in `%triggerprein`/`%triggerun`) NON basta da sola**, provato: RPM decide che cosa fare di un file di configurazione PRIMA di eseguire qualunque scriptlet o trigger (`rpmtsPrepare`, confronto fra il file sul disco e la firma del pacchetto vecchio). Con solo quel trigger l'aggiornamento 16 → 17 scriveva ancora `.rpmnew`.
- **Che cosa fa ora il pacchetto** (`remotix-pam-hook prepare` e `apply`, funzioni `prepare_one`/`adopt_one`): prima dell'aggiornamento o della rimozione (`%triggerprein`, `%triggerun` solo per una rimozione vera, `$2` = 0) si controlla se il file senza il nostro blocco è IDENTICO a quello che il pacchetto aveva messo (firma nel database RPM); se sì si annota la firma in `/var/lib/remotix/pam-pristine/` e si toglie il blocco. Dopo (`%triggerin`, `%triggerpostun`) si rimette la cosa come RPM l'avrebbe fatta per un file non toccato: il `.rpmnew` diventa il file, il `.rpmsave` (provato identico al testo vecchio) si cancella; poi si rimette il blocco. Si cancella o si sostituisce solo se la firma prova che è il vecchio testo del fornitore.
- **Provato sulla VM `lxqt`** (pacchetto l4, sddm 16 → 17 → 18 → 17 → 16): aggiornamento con file non toccato → file nuovo del fornitore + nostro blocco, nessun `.rpmnew`/`.rpmsave` (sddm, sddm-autologin; greeter senza blocco); file modificato dall'amministratore → comportamento normale di RPM (`.rpmsave` con la sua riga, senza la nostra) più il blocco sul file nuovo; `rpm -e sddm` con REMOTIX installato su file non toccato → nessun file di sddm rimasto e nessun file con la nostra riga (RPM aveva scritto un `.rpmsave`, il trigger l'ha tolto perché identico al testo vecchio); installazione nuova di sddm → il blocco arriva da `%triggerin`; ritorno alla versione precedente → file originale + blocco. Il confronto contro la versione senza correzione del gancio: gdm, plasmalogin e lightdm generano gli stessi file (stessa firma dal secondo rigo in poi), seconda `apply` silenziosa, `remove` completo lascia 0 file.
- **Finestra accettata:** durante l'aggiornamento di sddm, fra `%triggerprein` e `%triggerin` (pochi secondi) il blocco non c'è: un accesso locale in quel momento non chiude prima il desktop remoto. Se l'aggiornamento fallisce a metà il blocco manca fino al prossimo avvio del servizio (`ExecStartPre` `check` lo rimette) o al prossimo `%triggerin`.
- **Per il manuale (a):** righe scritte dall'amministratore DENTRO il nostro blocco (fra `# BEGIN remotix-pam-hook` e `# END remotix-pam-hook`) si perdono al prossimo `apply`; `rpm -V sddm` segnala `sddm` e `sddm-autologin` come modificati finché REMOTIX è installato (dopo la rimozione resta solo l'ora di modifica).
- **Caso residuo (b):** lightdm configurato come server XDMCP o VNC potrebbe dare `XDG_SEAT` a una sessione che di fatto è remota: il gancio la prenderebbe per locale e chiuderebbe il desktop REMOTIX dell'utente. Non provato, non previsto nelle impostazioni predefinite (l'XDMCP di lightdm è spento).
- **Correzione del revisore (22 nov 2026, pacchetto l5): il `.rpmnew` si adotta solo se è provato che è di QUESTA transazione.** Quasi tutti gli aggiornamenti e ogni `dnf reinstall sddm` non cambiano il file PAM e RPM non scrive niente: un `.rpmnew` VECCHIO lasciato da un aggiornamento precedente non deve entrare in vigore. Ora `prepare` annota anche la firma di un `.rpmnew` già presente (o «none»), e `apply` lo adotta solo se: il file che teniamo (senza blocco) ha ancora la firma annotata; il `.rpmnew` NON ha la firma che aveva prima (se è identico a prima non lo ha toccato questo aggiornamento); è diverso dal testo vecchio; e la sua firma è quella che il database RPM ha ADESSO per quel percorso (il pacchetto nuovo). Nel dubbio non si tocca niente e il marcatore si consuma. Le chiamate a `rpm` del gancio hanno `timeout 10`: un `rpm` bloccato non ferma la transazione, e il fallimento vuol dire «non adottare» (lato sicuro).
- **Limiti noti (a):** se Fedora cambiasse l'algoritmo delle firme dei file, il controllo sulla lunghezza (64 caratteri, SHA-256) spegnerebbe l'adozione in silenzio: si ricade sul comportamento normale di RPM (`.rpmnew`/`.rpmsave`) senza il nostro blocco nel mezzo. **(b)** REMOTIX e sddm RIMOSSI nella stessa transazione possono lasciare un `sddm.rpmsave` con il solo testo del fornitore: innocuo.
- **Pacchetto finale l6 (l5 aveva un difetto trovato dalla prova):** durante un aggiornamento il database RPM elenca per un attimo sia il pacchetto vecchio sia il nuovo, quindi per lo stesso percorso ci sono DUE firme; controllare solo la prima (quella vecchia) faceva rifiutare il `.rpmnew` giusto. Ora il `.rpmnew` si adotta se la sua firma è UNA di quelle del database e non è né quella vecchia né quella che il `.rpmnew` aveva già prima. Prove sulla VM `lxqt` (sddm 16/17): `.rpmnew` vecchio presente + `dnf reinstall sddm` → niente adottato, il `.rpmnew` resta com'era; `.rpmnew` vecchio presente + aggiornamento vero 16 → 17 → RPM lo sovrascrive con il testo del 17 e il gancio lo mette in vigore (il `.rpmnew` sparisce, file = testo del 17 + blocco); caso base 16 → 17 → 16 senza `.rpmnew` vecchio e ritorno: file giusto + blocco, nessun residuo; `dnf remove remotix`: `sddm`, `sddm-autologin`, `sddm-greeter` byte per byte originali.

### F22. XFCE (lightdm) e LXQt (sddm) col desktop remoto VIVO e la Radeon (22 nov 2026, pacchetto l6)
- **Prove** (VM `xfce` da `xfce-x3`, VM `lxqt` da `lxqt-l6`, una alla volta con la scheda; porta aperta come farebbe l'amministratore, `firewall-cmd --permanent --add-service=remotix` + `--reload`). XFCE e LXQt, stessi numeri: `check-base` 5/5, `check-input` 26/26, `check-lifecycle` 4/4, `check-clipboard` 2/2, `check-audio` 1/1; `check-desktop` XFCE 9/9, LXQt 8 PASS + `settings-intact` PASS dopo aver corretto il percorso del `panel.conf` di sistema (vedi sotto); `check-resize.py` (nuovo: 10 riagganci a misure diverse, anche dispari, con un terminale aperto, click al posto giusto, immagine viva) 10/10 su entrambi; `check-exit.py` (nuovo: `terminate-session`, riavvio del servizio, chiusura pagina e ripresa) 3/3 su entrambi, nessun processo del desktop rimasto, nessuna sessione REMOTIX in logind.
- **«Il locale chiude il remoto»** (sessione locale X11 con lightdm, Wayland con sddm/miriway; `prove/prelocal.sh`): prova 1 (remoto aperto → accesso locale automatico: il remoto sparisce in 1-2 s, `labwc` del remoto 0, shell locale viva dopo 40 s), 2a (orfano: `kill -9` del capo del remoto, il lato root dice «local login HELD in PAM: its REMOTIX desktop is closed first»), 2b (riavvio del servizio con il remoto aperto), 3 (locale attivo → il remoto è rifiutato con «that user is already signed in locally», sessione locale intatta): tutte riuscite su entrambe. Accesso con password alla schermata vera (macchina virtuale, foto): vedi F18/F19; ripetuto con l6 su entrambe (`lxqt-sddm-l6-072954-*.png`, `f01..f03`). AVC 0 su tutte le prove, su entrambe le VM.
- **Nota di banco:** `hold.py` senza `RX_KEEP` alla sua uscita chiude TUTTE le sessioni dell'utente, anche quella locale: nelle prove 2a/2b una `hold.py` di 150 s scadeva dentro la finestra di controllo e faceva sembrare che la sessione locale sparisse dopo 40 s. Con `hold.py` di 400 s la sessione locale resta (provato). Non è del prodotto.
- **D7 (XFCE, sfondo nero e niente icone)** — sonda rapida: confermato, limite DICHIARATO. Nel desktop remoto XFCE su Fedora il fondo è nero pieno senza icone; il pannello in alto (Applications, orologio, utente) e il dock in basso ci sono. Il registro di sessione dice `xfdesktop was not built with Wayland support` (xfdesktop 4.20.2-2, libxfce4windowing 4.20.7: la causa di Ubuntu/Debian, E1, qui non c'è; questa è strutturale). In LXQt invece sfondo, icone (`pcmanfm-qt --desktop`) e pannello ci sono (foto `surv-lxqt.png`).
- **labwc 0.20.2 contro quello di Ubuntu (0.9.3):** nessuna opzione né configurazione da cambiare: `-m`, `-S`, `-C`, `rc.xml` di REMOTIX e `wlr-randr --custom-mode` funzionano; il pulsante di spegnimento resta assente e le regole polkit reggono (`power-entries-absent`, `power-implied`, `power-local-seat`, `no-password-windows` tutti PASS su XFCE). Restano solo avvisi innocui: `xfce4-screensaver: Unsupported windowing environment`, `xfce4-power-manager: Unable to inhibit systemd sleep: AccessDenied`, avvisi di `xkbcomp` di Xwayland.
- **LXQt senza qlipper:** gli appunti passano per il protocollo data-control di labwc: `check-clipboard` 2/2. PATH remoto = cartella dei comandi nostri + `/usr/local/bin:/usr/bin:/bin` (senza `~/.local/bin`, come già noto, D3 del proprietario). Dopo Log Out nessun processo dell'utente resta (nel solito elenco di LXQt: pcmanfm-qt, nm-applet, dnfdragora-updater, geoclue agent… spariscono tutti).
- **Difetto di banco corretto, non del prodotto:** `check-desktop.py` cercava il `panel.conf` di sistema di LXQt in `/usr/share/lxqt/` (Ubuntu); su Fedora sta in `/etc/xdg/lxqt/panel.conf`. Il prodotto non usa quel percorso (rimette a posto solo il file dell'utente). Strumenti nuovi in `prove/`: `check-resize.py`, `check-exit.py`, `prelocal.sh`, `banco-vm/autologin-lightdm.sh`, `banco-vm/autologin-sddm.sh`; `giro-xfce-radeon.sh` e `giro-lxqt-radeon.sh` ora lanciano davvero tutto questo.
- **Controprova GNOME e KDE col pacchetto l6** (stati separati da `consegna-gnome` e `consegna-kde`, snapshot intatti): `check-base` 5/5 PASS su entrambi, 0 AVC.
- **Non misurato:** i tre programmi che sopravvivono all'uscita su XFCE (abrt-applet, geoclue agent, localsearch: studio 3) non sono stati contati dopo il Log Out col prodotto; `check-exit` controlla labwc, sessione, pannello, xfdesktop e Xwayland.

### F23. Perché una connessione QUIC si è chiusa: ora il registro lo dice (22 nov 2026, pacchetto d1)
- **Visto** (XFCE, proprietario): da un dispositivo il browser diceva «Opening handshake failed»; nel registro solo `GET /fingerprint`, `quic new connection … address validated with a Retry` e `closed (0 left)`: non diceva chi aveva chiuso né perché.
- **Fatto:** la riga di chiusura (`transport.c`, `close_why()` letto da ngtcp2 1.25: `ngtcp2_conn_get_ccerr2`, `ngtcp2_conn_get_handshake_completed2`) dice ora: chi ha chiuso (il PEER / NOI / chiusura senza CONNECTION_CLOSED), tipo e codice dell'errore, se è un errore CRYPTO (0x100-0x1ff) l'alert TLS con il nome (42 bad_certificate, 45 certificate_expired, 46 certificate_unknown, 48 unknown_ca…), la frase di motivo del peer ripulita (solo ASCII stampabile, 60 caratteri al massimo), il silenzio di 30 s, e se la stretta di mano TLS era COMPLETATA o no. Una riga per connessione, nessun dato in più del client, nessun cambio di comportamento. ⚠ Le chiusure di connessioni che non hanno mai fatto l'accesso restano soggette al limite già esistente (BIRTH_LINES per finestra): oltre il limite la riga va nel dettaglio (con lo stesso testo).
- **Provato** (VM `lxqt`, virtuale, da `lxqt-fatto`, pacchetto d1): un WebTransport dal browser di prova con l'impronta del certificato sbagliata e uno senza impronta → il browser dice «Opening handshake failed» e il registro: `connection with … closed (0 left) — the PEER closed it: transport error CRYPTO 0x12e = TLS alert 46 certificate_unknown "…46: certifi…"; TLS handshake NOT completed`. Cioè esattamente il sintomo del proprietario, ora spiegato.
- **Sospetto da verificare (non corretto):** `certificates.c:143` dà al certificato di sessione `notBefore` = adesso − 3600 s (un'ora di margine), `notAfter` = adesso + giorni. Identico in Debian 13 e Ubuntu 26.04 (stessa riga, stesso margine: `-3600`, commento «one hour of margin»). Nei registri di Fedora, Ubuntu e Debian NON c'è una voce sugli orologi dei client. Se l'orologio del dispositivo è indietro di oltre un'ora rispetto al server, il browser rifiuta il certificato di sessione (alert 45/46 o 42) e lo stesso accade dopo ogni rotazione del certificato; il nuovo registro lo mostrerà come alert.

**F23 — esito (22 nov 2026).** Sospetto confermato dal proprietario: l'orologio del notebook Windows era sballato; rimessa
l'ora, lo stesso dispositivo entra e riaggancia la sessione XFCE. Non è un difetto del prodotto (vale uguale su Debian e
Ubuntu: stesso margine di un'ora in `src/certificates.c`). Fatto: la riga di registro col motivo della chiusura
(pacchetto `d1`, da far passare al revisore). Da fare al passo 8: nei «Requisiti» del manuale, orologio del dispositivo
client giusto. Non si allarga il margine di notBefore: un orologio molto sbagliato rompe comunque ogni sito sicuro.

### F24. Il muro SELinux attorno alla parte di rete (D3, passo 5) — FATTO, rivisto (22 nov 2026, pacchetto s13)
- **Che cosa è:** il gemello del profilo AppArmor `remotix_network` di Debian/Ubuntu. La parte di rete (QUIC/WebTransport e HTTP/3, uid `remotix`) nasce nel dominio `remotix_net_t`: il lato root, prima della `execve`, scrive il contesto in `/proc/thread-self/attr/exec` (`src/walls.c`, `selinux_exec_net`). Stesso comportamento di AppArmor (omogeneità tra le distro): protezione spenta = nota e si prosegue; attiva ma lato root non in `remotix_t` o dominio non nel criterio (EINVAL) = nota con ⚠ e si prosegue; caricato e scrittura rifiutata = la parte di rete non parte. Nessuna uscita 78, nessun interruttore di banco.
- **Che cosa può:** usare i tre descrittori ricevuti (canale, UDP, TCP: socket del lato root, tipo `remotix_t`; nessun `create`/`bind`/`name_bind`/`name_connect` su socket IP); leggere i suoi file (programma, `/usr/share/remotix`, xkb, openssl, `/etc/passwd`); scrivere SOLO `/var/lib/remotix/net` e `/run/remotix/net`; chiedere a logind sul bus di sistema (nessun altro servizio), journal, userdb (multiplexer, machined, homed, DynamicUser, gdm: solo domande); `access(X_OK)` sui programmi dei desktop (`execute` su `bin_t`, senza `execute_no_trans`). Nessuna capability, nessun ptrace.
- **Nessun tipo di porta proprio** (valutato): un modulo non può portare un `portcon`; servirebbe `semanage port` (dipendenza, scriptlet prima di togliere il modulo, comando a mano per ogni altra porta). Il muro non ne guadagna: la parte di rete non fa `bind`. Il lato root lega le porte non riservate e le http.
- **Prova negativa rifatta (revisione):** `prove/wall-selinux.sh` + `wall-neg-domain.py`: la sonda gira in `remotix_net_t` COME ROOT CON TUTTE LE CAPABILITY contro bersagli raggiungibili per permessi Unix (file di root, socket 0666): solo SELinux può dire no. 21 tentativi vietati (shadow, home, file di stato del lato root, scrittura in `/run/remotix/prelocal`, shell, altro programma, scrittura in /etc, /usr, `/var/lib/remotix`, socket TCP/UDP/UDP6/raw/packet, socket X e di `/run/user` 0666, `/run/systemd/private`, `/proc/1/environ`, segnale a un processo `remotix_t`, `/proc/<lato root>/mem`, chiamata D-Bus a systemd1 e a polkit) + 2 permessi (D-Bus a logind, scrittura in `/var/lib/remotix/net` come uid remotix). PASS solo se negato E c'è una riga AVC (o `user_avc` del bus) di `remotix_net_t` nella finestra di QUEL tentativo (0,6 s l'uno dall'altro). Ha trovato due larghezze vere, tolte: `dbus_system_bus_client()` (parlare con PID 1 e con ogni servizio non confinato) e `auth_read_passwd()` (aggiunge `init_dbus_chat`); già prima `auth_use_nsswitch()` (creare socket IP). Log salvati sul server in `prove-sel/log-final/<vm>-wall/` (`probe.out`, `checks.out`, `avc.txt`, `policy-facts.txt` = `sesearch -A -s remotix_net_t` e `-T` sul criterio caricato, con `prove/wall-sesearch.sh`).
- **Il database dconf (revisione):** il lato root non crea più file qualunque in `/etc`: compila in `/run/remotix/dconf-compile.tmp` (tipo nostro) e crea in `/etc/dconf/db` solo due NOMI fissi (`remotix.new`, poi `remotix`), con transizioni di tipo PER NOME verso `remotix_dconf_db_t` (`src/session.c`, Fedora: diverso da Ubuntu, dove il compilatore scrive accanto al database). Provato: database mancante e database diverso, etichetta giusta, 0 AVC.
- **Pacchetto:** `rpm/remotix.spec` (BuildRequires `libselinux-devel`; `restorecon` dopo la compilazione dconf; se il modulo non entra il `%post` lo dice chiaramente e non fallisce, come il postinst Debian; in rimozione `restorecon -R /var/lib/remotix` se la cartella resta; `%selinux_modules_uninstall` espanso: agisce solo con `$1 -eq 0`), `rpm/remotix.service` (`MESA_SHADER_CACHE_DISABLE=true`: la sonda codec del lato root apriva la cache Mesa in /root/.cache; solo Fedora), `selinux/remotix.te|fc|if` (1.1.0).
- **Installazione/aggiornamento/rimozione/riavvio:** aggiornamento da `l6`/`k4b` provato; rimozione (anche con una cartella `/var/lib/remotix` rimasta: etichetta riportata a `var_lib_t`); reinstallazione da zero; riavvio della VM con il modulo caricato: il servizio riparte in `remotix_t` e la parte di rete in `remotix_net_t`, 0 AVC. **Finestra dell'aggiornamento:** salendo da un pacchetto senza muro con il servizio acceso, per un attimo (tra il caricamento del modulo e il riavvio del servizio) il vecchio lato root e la sua parte di rete vecchia girano in `remotix_t` e rifiutano `session.pem/.key`: 2 righe AVC una tantum, il servizio riparte pulito.
- **Esito per VM (pacchetto s13, enforcing, nessun permissive, dontaudit di serie, Radeon):** vedi la consegna; log in `prove-sel/log-final/` (`giro-<vm>.log`, `final-<vm>.log`, `ausearch-<vm>.txt` = `journalctl -b -g avc:`: su queste VM `ausearch` non vede nulla anche quando il giornale ha gli AVC).

### F25. F5 chiusa: utenti SELinux confinati (staff_u, user_u) — il contesto della sessione remota è quello dell'accesso locale (22 nov 2026, rivista)
- **Misurato (`selinuxdefcon`):** con `remotix_t` come chiamante la tabella di libselinux non ha riga: per `staff_u` ripiega su `staff_u:unconfined_r:unconfined_t` (il figlio nasceva unconfined), per `user_u` NON dà niente (EINVAL: l'accesso non poteva nascere). Da `xdm_t` dà `staff_t` e `user_t`. (Il testo precedente diceva «user_u finirebbe unconfined_t»: era sbagliato.)
- **Cura (`src/child.c`):** `selinux_exec_like_local_login()` chiede alla tabella ciò che chiede un accesso grafico (chiamante `xdm_t`) e imposta il contesto dell'`exec`. Poi `selinux_exec_checked()`, DOPO il passaggio all'uid dell'utente e subito prima della `execve`, rilegge `getexeccon()` (vuoto o `remotix_t` = rifiuto 46) e crea una nuova catena di chiavi di sessione con quel contesto (`setkeycreatecon` + `KEYCTL_JOIN_SESSION_KEYRING`; errore = rifiuto 47): pam_selinux imposta il contesto delle chiavi dalla SUA scelta e `pam_keyinit` (dopo di lui) creava il portachiavi `unconfined_t` mentre la sessione girava in `staff_t`. Fatto DOPO il setuid il portachiavi è dell'utente (uid/gid dell'utente, permessi `3f030000`, etichetta del contesto), come in un accesso ssh dello stesso utente (confrontato: stessi proprietario e permessi per un utente non confinato e per uno `staff_u`); una prima versione lo faceva da root e lo rendeva di root. **Con SELinux attivo ogni errore rifiuta l'accesso** (uscite 44, 45, 46, 47, tradotte in `why_exited`, nel log). `execute_no_trans` su `remotix_exec_t` resta a `remotix_t` perché serve all'aiutante PAM (`helper.c`); il FIGLIO non lo ha.
- **Policy:** transizione verso i domini utente non privilegiati (come `sshd_t`, non `sysadm_t`); `remotix_exec_t` punto d'ingresso ed `execute_no_trans` per quei domini (su KDE il gestore utente avvia il compositore con `remotix --kwin-virtual`: trovato con KDE e staff_u); `noatsecure/siginh/rlimitinh`; `fd use`, `sigchld`, socket del canale; lettura (con `map`) del database dconf.
- **Verificato (pacchetto s13, Radeon, SELinux enforcing):** su GNOME, KDE, XFCE, LXQt: `staff_u` → figlio e sessione in `staff_t` con gamma piena, portachiavi `staff_t`; `user_u` → `user_t`, portachiavi `user_t`; 0 rifiuti nostri. Desktop con video: GNOME, KDE, LXQt sì per entrambi; XFCE con `staff_u`: il pannello non parte (vedi F30, non nostro). Orfano e pulizia del gestore utente provati su GNOME per `staff_u`. `sysadm_u` non entra (come ssh e gdm di serie).

### F26. F10 chiusa: `remotix_t` e la lettura di `/proc/<pid>/environ` (22 nov 2026)
- **Visto sulla VM `kde`:** `sys_ptrace` e `perfmon` negati a `remotix_t` (93 volte in una corsa) appena non è più senza limiti. **Regole:** `sys_ptrace`, `capability2 perfmon`, `userdom_ptrace_all_users` (spenta se `deny_ptrace` è attivo: resta il primo segno, `--kwin-virtual` nella riga di comando). Sola lettura. Dopo: su KDE 0 rifiuti; `check-kde-exit` PASS.

### F27. Che cosa resta largo in `remotix_t` (lato root) e perché (22 nov 2026, rivista)
`remotix_t` non è più `unconfined_domain`; ogni diritto è in `selinux/remotix.te`, con la ragione. Resta largo:
- **diritti di un programma di login** (`auth_login_pgm_domain`, come sshd): PAM, cambio di identità, lettura dello stato di tutti i processi, `corecmd_exec_bin`;
- **passaggio verso ogni dominio utente non privilegiato** e `unconfined_t`: deve far nascere la sessione di chiunque;
- **`sys_admin`, `net_admin`, `setpcap`, `mount`/`mounton` su `/`, `/proc`, `/dev`, `/tmp` e sulle due cartelle della rete**: solo per costruire le stanze private della parte di rete nel fork;
- **le «faccende» nel gestore utente** (chiusura leggera «il locale chiude il remoto», spazzata degli orfani, unità KWin): fork del lato root che scendono all'uid dell'utente ma restano `remotix_t`: bus di sessione dell'utente, `systemctl --user`, file XDG di REMOTIX nella home (`config_home_t`, `gconf_home_t`, `data_home_t`, `user_home_t`), `kill` anche in namespace utente. È la parte più larga dopo i diritti di login. **Alternativa** (decisione del proprietario): far rieseguire quei fork nel dominio dell'utente, come fa il figlio; cambia la struttura del prodotto;
- **scrittura in `/etc/dconf/db`**: ora solo due nomi fissi (vedi F24);
- **porte:** lega le non riservate e le http.

### F28. Rifiuti SELinux che restano e NON sono nostri (22 nov 2026, rivista)
- Con gli utenti confinati: `relabelto` su `tmp_t` del `systemd` utente (PrivateTmp, criterio di Fedora); `map` su `/etc/udev/hwdb.bin` in `user_t`; `bwrap` (`cap_userns` `net_admin`/`setpcap`/`sys_ptrace`) in `staff_t`/`user_t` (F30); su XFCE `ssh-agent` (avviato da xfce4-session) non può accodarsi a `~/.local/state/remotix/session.log` (il file di registro di REMOTIX ereditato come stderr, `gconf_home_t`) né scrivere nella home: innocuo, solo utenti confinati su XFCE, non nei domini nostri.
- F15 (`gdm-session-worker` → `stratisd_t`): non osservato (nessun accesso locale vero da gdm in queste corse).
- I rifiuti di `rxpy`/`remotix_net_t` della prova negativa sono la prova stessa; 2 righe `session.pem/.key` all'aggiornamento (F24).
- Con `semodule -DB` compaiono migliaia di righe di altri domini (dontaudit del criterio di serie). La scoperta in modo `permissive` con `-DB` PERDE righe (sys_admin, fsetid non comparivano): le regole vanno verificate in enforcing, col criterio com'è.

### F29. Controlli di `prove/` che falliscono anche SENZA il muro (22 nov 2026)
Confrontati sulla stessa VM con il pacchetto precedente (`l6` su `gnome`, `k4b` su `kde`: `remotix_t` senza limiti), stessi esiti: `check-multiuser` `two-users`/`three-users` e `check-phone` `tap-click-portrait` (GNOME); `check-kde-live` («Chromium GONE», KDE); `check-prelocal.py` P1/P4 (KDE). `check-desktop` `reattach-windows-inside` (KDE: stesso FAIL col pacchetto `k4b` senza muro, confrontato il 22 nov); `users-shell-and-environment` (GNOME, `pkexec`, voluto, riga 335; fallisce uguale anche col muro a metà); P6 di `check-prelocal.py` (solo Debian). `check-ban` passa (serve la regola per il socket di comando di banco, come dice il profilo AppArmor); `check-package` non si applica a un RPM.

### F30. XFCE con un utente `staff_u`: il pannello non parte — NON nostro, limite di Fedora 45 (22 nov 2026)
`xfce4-panel` si ferma perché il caricatore di immagini SVG di GTK (glycin, via `bwrap --unshare-all`) è negato in `staff_t` (`cap_userns` `net_admin`/`setpcap`/`sys_ptrace`). Riprodotto SENZA REMOTIX: accesso ssh come `staff_u` (`staff_t`) e `GdkPixbuf.Pixbuf.new_from_file(".../image-missing.svg")` → «Loader process exited early with status '1'» con lo stesso `bwrap`. Il criterio di REMOTIX non tocca quelle regole. Nota per il manuale: XFCE (GTK 3) non è utilizzabile da un utente SELinux `staff_u`/`user_u` su Fedora 45, nemmeno in locale presumibilmente (accesso locale non provato: l'autologin lightdm di `staff_u` non è partito in banco).

### F31. Rifiuti dell'accesso con SELinux provati; log della chiusura per silenzio (22 nov 2026, revisione)
- **Percorsi di rifiuto (prova al banco, nessuna modifica del prodotto):** un utente Linux mappato a `guest_u` (nessun contesto raggiungibile da `xdm_t`: `selinuxdefcon` dà EINVAL) → accesso rifiutato, il figlio esce con **44**, il log dice «SELinux: no context like a local login's could be worked out… REFUSED», 0 processi dell'utente. Un utente mappato a `sysadm_u` (da `xdm_t` dà `sysadm_t`, ma `remotix_t` non può passarci) → il figlio esce con **37** («could not execute the server binary», la `execve` è negata dal criterio), 0 processi. 45, 46 e 47 (impostare il contesto, il contesto che non lascia `remotix_t`, il portachiavi) NON sono raggiungibili senza toccare il prodotto o il criterio: non provati.
- **Perdite di audit:** a fine corsa di ogni VM si salvano `auditctl -s` (campo `lost`) e `journalctl -b -g "audit.*(lost|backlog)"` in `prove-sel/log-final/auditloss-<vm>.txt`.
- **`src/transport.c` `close_why()` (solo testo di log):** la chiusura per silenzio usciva «transport error 0x0 NO_ERROR» perché `NGTCP2_CCERR_TYPE_IDLE_CLOSE` non veniva mai scritto: i due punti che vedono `NGTCP2_ERR_IDLE_CLOSE` ora scrivono `last_error` (`ngtcp2_ccerr_set_liberr`, solo per la riga di log: dopo non si scrive nessun CONNECTION_CLOSE, come prima); fuori dal closing period un `last_error` intatto (DROP_CONN, stateless reset) dice «no error recorded»; nella reason del client `"` diventa `.`. Provato: browser ucciso con SIGKILL → dopo 30 s «dropped without a CONNECTION_CLOSE: idle timeout (silence)».

### F32. Seconda revisione del muro: pacchetti s14 e s15 (22-23 nov 2026)
- **Portachiavi (A):** la prima versione faceva il `JOIN_SESSION_KEYRING` da root (portachiavi di root per ogni sessione remota). Ora in `selinux_exec_checked()`, dopo il passaggio all'uid dell'utente: proprietario e gruppo dell'utente, permessi `3f030000`, etichetta del contesto di accesso; confrontato con un accesso ssh dello stesso utente (non confinato e `staff_u`) su GNOME, XFCE, KDE: stessi proprietario, gruppo, permessi (`keyctl describe`) ed etichetta. Un `setperm` dall'esterno è negato a chi non possiede il portachiavi, uguale per il portachiavi di un accesso ssh. Il `setperm` riuscito dall'interno della sessione remota non è provabile da fuori. Nota: da root `/proc/keys` non mostra i portachiavi di un altro utente con permessi `other=0`: si guarda come quell'utente.
- **`signull` su `xserver_t` (s15):** il lato root, nello spazzare lo scope di una sessione, ha segnalato l'Xwayland dell'utente (`xserver_t`, fuori da `userdomain`) e SELinux ha negato `signull`. Aggiunta `signal signull` su `xserver_t gpg_agent_t ssh_agent_type session_bus_type`. Dopo, XFCE: 60 PASS senza quell'AVC (la regola non è stata esercitata in modo mirato).
- Il resto (E perdite di audit = 0 su tutte le VM; F log di `transport.c`; D rifiuti 44 e 37) è in F31. `check-phone` `two-finger-scroll` è fallito una volta su gnome e ha passato in due ripetizioni: instabile, nessun AVC.

### F33. Terza revisione del muro e rifiniture del passo 6 (23 nov 2026, pacchetti s16, s17, f1)
**Correzioni del muro**
- **G (segnali della spazzata):** `lx_signal()` segnala tutti i pid di `session-N.scope` per cgroup, non per dominio (segnale 0, SIGTERM, SIGKILL; e `kill` sul figlio): un rifiuto lascia un desktop orfano. `remotix_t` ha `domain_signal_all_domains`, `domain_signull_all_domains`, `domain_kill_all_domains` (al posto degli elenchi stretti di prima), con il motivo nel `.te`. Provato su GNOME con una sessione orfana (figlio ucciso con SIGKILL): un processo che ignora SIGTERM (`trap ""`) e uno in un altro dominio (`ping_t`) messi nello scope spariscono entrambi, 0 AVC. Le altre `kill` del lato root (figli, aiutanti, residui della parte di rete) riguardano suoi figli o `remotix_net_t`.
- **H (portachiavi):** se il portachiavi di sessione che `pam_keyinit` ha già fatto ha lo stesso `utente:ruolo:tipo` del contesto d'exec (utente non confinato: il caso comune) RESTA, come su Ubuntu; si rifà solo se differisce (staff_u, user_u). Provato con `strace -f -e keyctl` sul servizio: per l'utente non confinato dopo `GET_SECURITY` non c'è nessun `JOIN`; per staff_u c'è un `JOIN` e, per user_u, il nuovo portachiavi (letto dall'utente) è dell'utente, permessi `3f030000`, etichetta `user_u:user_r:user_t:s0`. **Correzione di F32:** le righe di `/proc/keys` che avevo attribuito al figlio erano in gran parte del gestore utente di systemd (molte referenze, stesse in ssh); la prova vera è l'`strace`.
- **I:** tolto «a stateless reset» dai due commenti di `transport.c` (un reset porta in draining: la riga dice «the PEER closed it»).
- **J:** log della prova negativa e `sesearch -A -s remotix_t -c process` salvati per ogni VM in `prove-sel/log-final/<vm>-wall/policy-facts.txt` (`prove/wall-sesearch.sh` ora emette anche il lato root).

**Rifiniture del passo 6** (regola: come Ubuntu; la sessione remota = accesso locale meno i danni)
1. *I FAIL che c'erano già.* `check-kde-live` («Chromium GONE»): difetto del BANCO, la VM non aveva Chromium; con `dnf install chromium` passa 8/8; la prova ora si BLOCCA con un messaggio chiaro se manca (`check-kde-live.py`). `check-prelocal` P1/P4 su KDE: difetto della PROVA, `plasma_waitforname` (aiutante di Plasma) c'è ancora un istante al primo campione e sparisce entro la grazia: aggiunto all'elenco degli aiutanti (`check-prelocal.py`); con VM pulita P1-P5 passano; P6 era scritta per Debian (`common-session`): su Fedora controlla che la riga del gancio stia PRIMA di `pam_selinux open` nei file di ogni schermata di accesso (passa). `reattach-windows-inside` su KDE: KWin rimpicciolisce una finestra che non sta più nello schermo (politica sua, come a uno schermo locale che cambia); la prova chiedeva «stessa misura» come labwc/mutter: per KDE ora accetta una finestra rimpicciolita ma INTERAMENTE dentro (lo scopo di F-018b), le altre desktop come prima. `pkexec` su GNOME (`users-shell-and-environment`): la sessione GNOME ha `SHELL=` vuoto per costruzione (cura della trappola della shell di login di gnome-session, stesso codice di Ubuntu) e il terminale di Fedora non lo reimposta: `pkexec` rifiuta («SHELL not in /etc/shells»); è la riga già nota «pkexec voluto così su GNOME» di E2: DIFETTO DEL PRODOTTO comune a Ubuntu, non corretto (cambiare l'ambiente passato al gestore utente non è piccolo né chiaro: resta da decidere). `multiuser` (two-users, three-users) e `phone tap-click-portrait` su GNOME: in tutti i fallimenti un click arriva con un'ascissa (o ordinata) a 0 mentre l'altra è giusta; è un difetto del PRODOTTO o del compositore (mutter 51), identico col pacchetto senza muro; NON indagato a fondo né corretto (non piccolo); il tap da telefono è già nell'elenco «saltuario» di E2.
2. *Programmi avviati di serie.* Il prodotto ha già (come su Ubuntu) la spazzata dei residui dello scope dopo l'uscita (`session_clear_out_scope`): nessun processo resta dopo Log Out su XFCE e LXQt (`check-lifecycle`/`check-exit` PASS). L'elenco dei file di autostart nascosti è quello di Ubuntu (solo `blueman.desktop`); non ne ho aggiunti di Fedora (abrt, dnfdragora, nm-applet non danneggiano più di quanto `update-notifier` o `nm-applet` su Ubuntu, che non sono nascosti).
3. *PATH e lingua (F4).* Misurato su XFCE, accesso locale (lightdm) contro remoto: locale `PATH=~/.local/bin:~/bin:/usr/local/bin:/usr/bin`, `LANG=en_US.UTF-8`; remoto `PATH=/usr/local/bin:/usr/bin:/bin`, `LANG=C.UTF-8`. Sono le stesse regole di Ubuntu (il figlio prende solo `PATH` e `XDG_SESSION_ID` da PAM; la lingua nasce dal ripiego `C.UTF-8` di `session.c`), ma su Ubuntu `/etc/environment` rende il PATH uguale al locale. Allinearli è una modifica di `child.c`/`session.c` valida per tutte le distro (non toccate): NON fatta, da decidere; proposta: prendere `LANG` anche dal file di PAM `/etc/locale.conf` già letto.
4. *lightdm e la regola «nessuno spegne».* `50-remotix-no-poweroff.rules` è identica a quella di Ubuntu e ordina prima di `lightdm.rules` (che darebbe «sì» all'utente `lightdm` su tutto `login1`): provato — col nostro file `CanPowerOff` dell'utente lightdm = «no», senza il nostro file = «sì», rimesso = «no».
5. *Gancio PAM e `.rpmnew` di sddm:* un rifiuto dell'adozione ora scrive una riga `⚠ … NOT adopted (<motivo>)` (`remotix-pam-hook`); provato su lxqt simulando un `.rpmnew` uguale al testo vecchio.
6. *Firewall (F20):* `%firewalld_reload` in `%post` e `%postun` (macro standard dei pacchetti Fedora con una definizione di servizio); NON apre la porta. Provato su una VM pulita (`codec`): prima dell'installazione `--permanent --add-service=remotix` dà INVALID_SERVICE, subito dopo l'installazione riesce senza `--reload`; la porta resta chiusa.
7. *F16 (core dump di Plasma).* Caso reale «accesso locale con remoto aperto» simulato col gancio su KDE (65 processi dell'utente, gancio, 50 s di osservazione): 0 core dump (`coredumpctl`), 0 processi dopo 10 s. Non corretto, nessun problema da correggere in questo caso.
8. *labwc 0.20.2 (XFCE, LXQt).* Letto `NEWS.md` da 0.9.3: il nostro `rc.xml` usa `<core><decoration>`, `<keyboard><default/>` + una `<keybind>` con `ForEach`/`SetDecorations`/`FitToOutput`/`WarpCursor`: tutte esistono in 0.20; cambiano solo i tasti di serie (`W-<freccia>` a quarti di schermo, il terminale di serie è `lab-sensible-terminal`, `A-<freccia>` deprecato) e c'è una regressione nota di lxqt-panel con wlroots < 0.20.2. Le prove di XFCE e LXQt (ridimensionamento, riaggancio, uscita, appunti, mouse) passano 60/60. D7 (sfondo XFCE): la prova breve del rimedio (xfdesktop sotto XWayland) NON è riuscita a partire in banco (nessuna sessione viva al momento del comando): resta il limite dichiarato, non provato.
- **Esito del giro finale (pacchetto f1, sha256 `f4a749e9860a83169507f749b4013d22029b5f4f1abb96ef18179d26c843efe0`, enforcing, nessun permissive, dontaudit di serie, Radeon):** gnome 52 PASS (FAIL solo `pkexec`) + resto di all.sh 36 PASS (FAIL: `two-users`, `three-users`, `tap-click-portrait`); kde 78 PASS, 0 FAIL, 0 BLOCKED (tutte le righe che prima non erano verdi lo sono, dopo gli adattamenti di sopra e Chromium nella VM); xfce 60 PASS; lxqt 60 PASS. Prova negativa 25/25 su tutte e quattro; perdite di audit 0. AVC nostri in esercizio: nessuno (restano le 2 righe `session.pem/.key` dell'aggiornamento e i `send_msg` D-Bus della prova negativa). Istantanee `finale-gnome|kde|xfce|lxqt`. Log in `prove-sel/log-final/`; `policy-f1/policy-facts.txt` ha `sesearch -A/-T` di `remotix_net_t` e `sesearch -A -s remotix_t -c process`.

### F34. Il primo movimento assoluto su GNOME arriva con una coordinata a 0; lingua e PATH della sessione remota (23 nov 2026)
**Click a coordinata 0 (GNOME, `multiuser` e `phone tap-click-portrait`)**
- **Misurato (VM gnome, pacchetto f1/g1, mutter 51.0):** riproducibile con UN SOLO utente (`one-user`), senza il test del telefono e senza il muro SELinux. La
  finestra di prova registra il primo `motion` e il primo `click` con una coordinata a 0 e l'altra giusta (a volte x, a volte y; nel telefono x=0 e y=del
  puntatore). Dopo quel primo evento tutti i movimenti successivi sono esatti (0,6/0,3, 0,3/0,6, 0,8/0,2).
- **Dove nasce lo 0:** non nella pagina né nel protocollo né nel nostro calcolo. Traccia temporanea in `input_pointer()` (g1): arriva `POINTER (336,192)`, canvas
  1344x768, regione 0,0 1344x768, e a libei va `336.0,192.0`: giusto. Quindi lo 0 è di mutter 51: il PRIMO movimento assoluto dopo l'avvio del dispositivo
  puntatore arriva alle finestre con una delle due coordinate a 0. Non dipende da orientamento, dimensione dello schermo o numero di utenti.
- **Ubuntu (E2, «primo tocco da telefono su GNOME, saltuario»):** stesso codice (`input_pointer` identico) e stesso mutter: con ogni probabilità la stessa causa; non
  provato su Ubuntu qui. Che cosa vede l'utente: solo il PRIMO clic fatto subito dopo l'accesso, senza prima muovere il mouse (tipico: il primo tocco sul telefono), cade sul
  bordo dello schermo; ogni movimento successivo corregge la posizione.
- **Correzione (piccola, nel nostro codice, `input.c`):** il primo movimento assoluto dopo ogni `DEVICE_RESUMED` del puntatore è inviato due volte (campo `pointer_primed`).
  Provata la sola doppia spedizione (g3): `one-user`, `two-users` PASS. Con g4/g6: `two-users`, `three-users`, `same-user`, tutto `check-phone` PASS (`tap-click-portrait` due volte). Sul percorso
  wlroots (XFCE, LXQt) il codice non passa di lì. Se mutter correggerà il difetto, il secondo invio è innocuo.
**Lingua e PATH (F4)**
- **Misurato in locale (gdm, GNOME):** `LANG=it_IT.UTF-8` (dopo `localectl set-locale`), `PATH=~/.local/bin:~/bin:/usr/local/bin:/usr/bin`, sia nel gestore utente sia in `gnome-shell`.
  Il remoto aveva `LANG=C.UTF-8` (`session.c`, ripiego, perché `child.c` non passava nulla) e `PATH=/usr/local/bin:/usr/bin:/bin`. (Su Ubuntu la lingua è oggi uguale, C.UTF-8: il difetto è lo stesso; il PATH lì
  coincide col locale grazie a `/etc/environment`.)
- **Correzione (solo albero fedora45, `child.c`):** `LANG` = quello scelto dall'utente nel desktop (AccountsService, `Language=`: lo leggono gdm e lightdm), altrimenti quello di sistema
  (`/etc/locale.conf`, già nell'ambiente PAM per la seconda riga `pam_env`); solo caratteri semplici; `session.c` controlla ancora che il locale esista e sia UTF-8. `PATH`: se PAM non ne dà uno (Fedora non ha
  `/etc/environment`), il ripiego è `~/.local/bin:~/bin:/usr/local/bin:/usr/bin` (se PAM ne dà uno, resta quello).
- **Provato (VM gnome, g5/g6):** con `LANG=it_IT.UTF-8` di sistema, accesso remoto di `lc1`: `gnome-shell` e gestore utente `LANG=it_IT.UTF-8`; PATH uguale al locale con g6. Locale ripristinato (VM ripristinate dalle istantanee `finale-*`).
  Non provato: il desktop effettivamente tradotto in italiano (i `langpacks-it` non sono nella VM); la scelta per utente in AccountsService; `LC_*` e `LANGUAGE` (non passati).
- **Regressione (g6):** `check-base` + `check-input` su gnome, kde, xfce, lxqt: 31 PASS ciascuno, 0 FAIL.
**Rifiniture K, L delle prove:** `wall-sesearch.sh` ora salva anche `sesearch -A -s remotix_t -c process -p sigkill|signal|signull` senza filtro (`allow login_pgm domain:process sigkill;` e `allow remotix_t domain:process { signal signull }`),
  in `log-final/k/`. Sessione orfana con un processo che ignora SIGTERM (nello scope, `SigIgn 0x4006`): nel journal `session-668.scope … still had processes after the SIGTERM: SIGKILL sent to them, ended`; processo sparito, nessun AVC
  (`log-final/k/orphan-sigterm-ignored-gnome.txt`): il permesso c'è, il .te non cambia. `check-desktop.py` `reattach-windows-inside` (KDE): il restringimento è accettato solo se ogni misura resta almeno metà di prima.

### F35. Quinta revisione: lingua scelta dall'utente (M), LC_* e LANGUAGE (N), commento (O); giro finale e macchine di consegna (23 nov 2026, pacchetto h1)
**Pacchetto h1**, sha256 `550f368bffdd6b7815989f065048788ec98ec3d11a28f72ec1d921c9de191c71` (modulo SELinux 1.1.1).
- **M.** La scelta dell'utente in AccountsService non veniva mai letta: `child_lang()` girava dopo `setuid()` e la cartella `/var/lib/AccountsService/users/` è `root:root 0700`
  (tipo `accountsd_var_lib_t`, i file dentro 0644). Ora `child_locale_read()` gira PRIMA del cambio d'identità (passo 2-quater, da root): `open(O_RDONLY|O_NOFOLLOW|O_CLOEXEC)`, file
  regolare, al massimo 4 KiB; legge `Languages=` (la chiave che scrive `SetLanguage` in questa versione, conta il primo elemento) o `Language=` (la vecchia); il valore validato
  resta per il passo 5. `selinux/remotix.te`: `allow remotix_t accountsd_var_lib_t:dir search; allow remotix_t accountsd_var_lib_t:file { open read getattr };`, commentata, niente altro
  (la lettura nella cartella 0700 è già coperta da `dac_read_search`). Provato con `busctl … SetLanguage it_IT.UTF-8` per `lc1` e sistema `en_US`: accesso locale gdm e accesso remoto
  danno LANG=it_IT.UTF-8; `lc2` senza scelta: LANG=en_US.UTF-8 (di sistema); 0 AVC. Con `langpacks-it` installato il desktop remoto è davvero in italiano (cattura: barra «lun 23 nov», finestra
  «Aggiornare cartelle standard alla lingua attuale?»); VM poi ripristinate dalle istantanee. `SetFormatsLocale` non esiste in questa accountsservice: `FormatsLocale` non provato.
- **N.** In un accesso locale `LC_TIME` messo in `/etc/locale.conf` con `localectl` arriva a `gnome-shell` e al gestore utente (misurato); il remoto non lo aveva. Ora `child.c` passa
  `LC_*` e `LANGUAGE` dell'ambiente PAM (cioè di `/etc/locale.conf`) con validazione (nome `LC_<MAIUSCOLE_>` o `LANGUAGE`, valore di caratteri semplici, max 64, al più 12) e `session.c` li mette
  nell'ambiente del desktop; i nomi sono anche in `OUR_VARIABLES` (ripristinati a fine sessione). Provato: `LC_TIME=it_IT.UTF-8` di sistema, remoto di `lc1` e `lc2`: presente.
  `LANGUAGE` non provato (il sistema rifiuta un valore `en` senza il locale installato).
- **O.** `input.c`: il commento del doppio invio dice «TO BE REMOVED WHEN MUTTER IS FIXED».
- **Giro finale su h1 (enforcing, nessun permissive, dontaudit di serie, Radeon; log in `prove-sel/log-final/h1/`; istantanee `finale2-<de>`):** gnome 52 PASS (1 FAIL, `users-shell-and-environment`,
  il pkexec/SHELL vuoto già noto) + resto di all.sh 39 PASS; kde 76 PASS; xfce 60; lxqt 60 (il primo tentativo su lxqt è saltato per un'interruzione di rete verso il server alle 06:22, ripetuto per intero);
  prova negativa del muro su tutte e quattro: 0 FAIL; perdite audit 0; gli AVC sono la stessa famiglia del giro f1 (prova negativa e rumore dei programmi di prova), nessuno con `accountsd_var_lib_t`.
  KDE: nel giro mancavano due righe di `check-kde-exit` (service restart, close and wait) rispetto a f1, senza FAIL; rilanciato da solo sullo stato finale: 3/3 PASS. Causa del vuoto non trovata.
- **Macchine di consegna** (da `codec`, solo h1 via dnf, `firewall-cmd --permanent --add-service=remotix && --reload` riusciti senza reload preventivo, `enable --now`): servizio attivo, `remotix_t` e rete in `remotix_net_t`,
  `--encoding-test h264` hardware (h264_vulkan, Radeon), pagina https 200 dal server (885x), utenti solo `prova` e `prova2`, 0 AVC nostri; spente, istantanee `consegna-finale-<de>` (gnome, kde, xfce, lxqt).

### F36. KDE: con un programma che non si chiude da solo, l'accesso locale passava col desktop remoto vivo (25 nov 2026) — CORRETTO (i1)
- **Quando:** 25 nov 2026, prima prova del proprietario su macchina vera (server avviato dalla chiavetta Fedora 45 KDE live, due schede
  video, SELinux enforcing, pacchetto h1). GNOME, XFCE e LXQt, provati lo stesso giorno allo stesso modo, sono passati.
- **Che cosa è successo:** desktop remoto di `prova` con Konsole e `top`; accesso locale di `prova`: browser scollegato, ma KWin, pannello e
  gestore di sessione remoti restano vivi e il desktop locale parte senza compositore (schermo fermo, programmi di Plasma in core dump).
- **Cause, tre in fila:** (1) `org.kde.Shutdown.logout` aspetta senza limite un programma che non si chiude o chiede conferma (sulla VM
  lo fa un editor con testo non salvato; sulla macchina vera anche Konsole con `top`); (2) la chiusura forzata fermava
  `plasma-workspace.target`, ma KWin, ksmserver e plasmashell sono `PartOf=graphical-session.target`, che se ne va solo ~4,5 s dopo: oltre la
  scadenza della parte root (13 s dalla richiesta, 3 s dopo la forzata); (3) l'ultima difesa (`systemctl --user stop
  plasma-kwin_wayland.service` dalla parte root) era rifiutata dal nostro muro: nessuna regola `class service` per `remotix_t`
  (`avc: denied { stop } ... tcontext=xdm_unit_file_t`).
- **Perché le prove non l'avevano visto:** `check-prelocal.py` apriva un desktop remoto VUOTO: la chiusura ordinata riusciva sempre e le
  strade forzate non giravano mai, quindi nemmeno il muro veniva interpellato.
- **Soluzione:** `src/session.c` `exit_kde(TRUE)`: `StopUnit("graphical-session.target","fail")` (tutto fermo in ~0,5 s);
  `selinux/remotix.te`: `allow remotix_t xdm_unit_file_t:service { stop status };`. Solo KDE (decisione del proprietario); alla scadenza
  resta il comportamento di prima (nessuna rete di sicurezza comune).
- **Provato:** VM `kde` (guasto rifatto con h1; con i1 tre prove pulite, ultima difesa da sola, uscita normale e rientro, P1–P8 PASS);
  macchina vera, chiavetta KDE, i1, Konsole con `top`: forzata a 10,05 s, tutto fermo 0,56 s dopo, gancio liberato a 10,9 s, desktop
  locale subito, 0 rifiuti SELinux, 0 core dump. Casi nuovi di banco: P7 (terminale con `top`), P8 (editor con testo non salvato).
- **Attesa accorciata (i2, decisione del proprietario):** su KDE, solo nella chiusura per accesso locale, la chiusura ordinata aspetta
  5 s invece di 10 (`KDE_PRELOCAL_ORDERLY_MS`). Macchina vera, chiavetta KDE, i2: forzata a 5,04 s, gancio liberato a 5,9 s, 0 rifiuti,
  0 core dump. Sulla VM dieci programmi sani si chiudono da soli in 1,1 s (nessuna forzata); programmi lenti a chiudersi non provati.
- **Resta (non corretto, messo da parte):** GNOME ha la stessa costruzione di KDE e nessuna ultima difesa; Debian/Ubuntu hanno lo stesso codice di forzata; `catatonit` (aiutante
  di podman avviato da Konsole) resta nel gestore dell'utente dopo l'accesso locale; rifiuto innocuo `search` su `/proc/sys/dev`.
- **Su una distribuzione o un desktop nuovo:** provare «il locale chiude il remoto» SEMPRE con programmi aperti nel remoto (uno che si
  chiude da solo e uno che chiede conferma), su macchina vera prima di pubblicare; guardare a quale unità sono legati compositore e
  pannello (`systemctl --user show -p PartOf`), e l'etichetta SELinux dei file di unità che la parte root deve fermare.
