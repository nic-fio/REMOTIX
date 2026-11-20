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
