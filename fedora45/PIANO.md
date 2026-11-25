# PIANO — REMOTIX per Fedora 45: studio dei quattro desktop

Scritto il 21 nov 2026. Stato: passi 1 e 2 **fatti** (21 nov). Passo 3: decisioni D1-D8 prese il 21 nov; **piano di sviluppo in fondo, approvato il 21 nov**; passo 0 in corso; nessun codice del prodotto toccato.

## Obiettivo
Capire a fondo, prima di scrivere codice, come funzionano i quattro desktop su Fedora 45 (GNOME, KDE, XFCE, LXQt)
e che cosa cambia rispetto a Ubuntu 26.04 e Debian 13. Solo studio: il prodotto non si tocca.
Le ISO sono le quattro «Live 45-1.4» in `/media/DOWNLOAD` del server.

## Regola del banco
Niente contenitori (niente podman). Si lavora solo su macchine virtuali con Fedora installata davvero,
con la Radeon passata alla macchina virtuale.

## Passi
1. **Banco.** Si adatta a Fedora lo script delle macchine virtuali già usato per Ubuntu (`server/vm-radeon.sh`,
   copiato in `fedora45/server/`): quattro macchine `gnome`, `kde`, `xfce`, `lxqt`, ciascuna costruita dal
   contenuto della sua ISO (come fatto per Kubuntu, Xubuntu e Lubuntu), con il kernel di Fedora, SELinux attivo
   com'è su una Fedora appena installata, utenti `prova` (amministratore) e `prova2`, password `prova2026`.
   Cartella sul server: `/media/REMOTIX-FEDORA/vm-radeon/`. Porte: ssh 2351-2354, REMOTIX 8851-8854.
   Lo script lo scrive il `programmatore`, lo controlla il `revisore`.
   Fatto quando: ognuna delle quattro macchine si accende con la Radeon, mostra la sua schermata di accesso,
   l'accesso locale di `prova` arriva al desktop giusto; istantanea `pulito` di ciascuna.
2. **Studio.** Quattro agenti insieme, uno per desktop, ciascuno sulla SUA macchina virtuale. Ognuno legge
   prima il registro dei problemi e gli studi fatti per Ubuntu, poi osserva sulla macchina vera: schermata di
   accesso e avvio della sessione locale, versioni e pacchetti presenti, come nasce e come si chiude il desktop,
   cattura dello schermo e ingresso di tastiera e mouse, audio, portachiavi, SELinux, firewall, aggancio al
   login (authselect/PAM), codec video (H.264 su Fedora non è di serie), pacchetto RPM e sue dipendenze.
   Consegna: un documento per desktop in `fedora45/studio/`, con i fatti distinti in verificato / dal web /
   supposizione, e in fondo «problemi da affrontare», «che cosa non si può sapere senza provare», «prove consigliate».
3. **Riscontro.** Leggo i quattro studi, verifico a campione, e scrivo qui il piano di sviluppo per Fedora
   (con le decisioni che spettano al proprietario). Si scrive codice solo dopo il suo OK.

## La Radeon è una sola
Le quattro macchine restano accese insieme durante lo studio (5 GB di memoria ciascuna: 20 GB su 31), ma solo
una alla volta ha la Radeon; le altre tre hanno una scheda video virtuale, che basta per leggere pacchetti,
file, registri e per avviare il desktop. Ogni agente chiede la Radeon solo per le osservazioni che la
richiedono (grafica vera, codifica video) e la rilascia subito; lo script impedisce che due macchine la
prendano insieme.

## Rischi
- La costruzione della macchina dal contenuto della ISO su Fedora è nuova (SELinux va rietichettato al primo
  avvio, avviatore e initramfs diversi da Ubuntu): se per un gusto non riesce, si ripiega sull'installatore
  automatico di Fedora (kickstart) per quel gusto.
- Con quattro macchine accese la memoria del server è occupata per due terzi: niente altro lavoro pesante insieme.

## Stato del server (21 nov)
Prima dell'ordine «niente podman» avevo già installato podman sul server e scritto due suoi file di
configurazione in `/etc/containers/`; nessuna immagine scaricata, nessun contenitore creato. Stanno nella
memoria del server e spariscono al prossimo riavvio. Non li uso. Le quattro ISO sono montate in sola lettura
sotto `/media/REMOTIX-FEDORA/iso/` (servono al passo 1).

---

# Riscontro dello studio (21 nov 2026, sera)

Quattro studi in `studio/` (1 GNOME, 2 KDE, 3 XFCE, 4 LXQt), fatti sulle quattro macchine virtuali. Verifica a
campione fatta da me sulle macchine (versioni, zona del firewall, profilo authselect, domini SELinux dei display
manager, driver video aggiunti nella macchina GNOME): i valori citati tornano. Il prodotto non è stato né costruito
né installato: tutto ciò che riguarda REMOTIX vero su Fedora resta da provare.

## Che cosa c'è su Fedora 45
- GNOME 51 (gdm), Plasma 6.8 (plasmalogin, nuovo: non più sddm), XFCE 4.20 (lightdm, sessione locale X11),
  LXQt 2.4 (sddm; la sessione locale è Wayland su miriway). systemd 262. labwc 0.20.2 nei repository, non installato di serie.

## Che cosa regge già
- GNOME: l'avvio headless come su Ubuntu (GNOME 50) regge su GNOME 51; il modello delle impostazioni (dconf) regge;
  i programmi Flatpak partono senza nulla di speciale.
- XFCE e LXQt: nascono dentro il labwc di Fedora come oggi.
- Regola «nessuno spegne»: le 19 azioni esistono tutte; provata su XFCE.
- «Installato spento»: su Fedora è il comportamento normale dei servizi.

## Ostacoli, in ordine di peso
1. **Video H.264/HEVC assente di serie** (tutti i desktop): il Mesa di Fedora esclude questi codec; con la Radeon
   nessun codificatore. Con RPM Fusion (driver «freeworld») i codec compaiono (visto nella macchina GNOME; la
   codifica vera non è stata provata).
2. **SELinux blocca l'avvio del desktop** se il file di accesso di REMOTIX è copiato da quello di sshd (riga
   `pam_selinux`): osservato su GNOME e XFCE. Senza quella riga il desktop parte, ma i programmi dell'utente
   restano etichettati come «servizio». Serve una cura studiata (piccolo modulo SELinux nel pacchetto o altra via).
3. **Aggancio all'accesso locale** («il locale esclude il remoto»): su Fedora i file di accesso comuni sono
   riscritti da authselect; il gancio va messo altrove (file di ciascun display manager oppure profilo
   authselect proprio). In più su LXQt/sddm SELinux impedirebbe al gancio di scrivere il suo file.
   Il difetto A2 si ripresenta su lightdm, sddm e plasmalogin (su plasmalogin la schermata resta congelata);
   A1 si ripresenta su gdm.
4. **KDE**: il labwc di Fedora ha ancora il difetto che blocca le finestre; la nostra modifica (3 righe) portata
   alla versione di Fedora funziona. Novità: KWin 6.8 da solo (`--virtual`) ora sa cambiare risoluzione a caldo,
   quindi il labwc nostro potrebbe non servire più (cattura dopo il cambio non provata).
5. **XFCE**: sfondo nero senza icone (xfdesktop di Fedora è compilato senza Wayland): nessun aggiornamento lo cura.
6. **Portachiavi**: GNOME usa `oo7` (bloccato nella sessione remota), KDE `ksecretd`; XFCE e LXQt non ne hanno.
7. **Pacchetto**: RPM da scrivere da zero; OpenSSL di Fedora è 4.0 (c'è anche il 3.5 «compat»); file di accesso
   da riscrivere per Fedora; nessun equivalente pronto del profilo AppArmor; firewall chiuso su XFCE e LXQt
   (zona `public`), aperto su GNOME e KDE (zona Workstation: porte da 1025 in su).
8. **Minori**: programmi avviati di serie da spegnere nella sessione remota (dnfdragora-updater, abrt, geoclue,
   nm-applet, Welcome Center/Tour), PATH e lingua della sessione, labwc 0.20 da provare a fondo (era 0.9.3).

## Decisioni che spettano al proprietario
- D1. Video: **DECISO (21 nov)**: i codec sono una dipendenza necessaria, come la scheda grafica. L'amministratore
  Fedora li installa (RPM Fusion); il manuale utente e quello tecnico di Fedora lo dichiarano. Nessuna codifica software.
  A nostro carico resta solo preparare le macchine virtuali di prova con i codec (istantanea `codec` sopra `pulito`).
  Nessun lavoro in più nel prodotto per questo punto.
  All'installazione resta il comportamento di oggi (rifiuto senza scheda grafica, solo avviso se la scheda non
  codifica): nessun rifiuto nuovo. I manuali di Fedora avranno una sezione «Requirements» in primo piano; se serve,
  la stessa sezione anche nei manuali di Debian e Ubuntu.
- D2. KDE: **DECISO (21 nov)**: KWin 6.8 da solo (`--virtual`, risoluzione cambiata a caldo), senza labwc nostro.
  Motivo del proprietario: il codice viaggia fra le distro; quando Debian e Ubuntu avranno KDE 6.8 lo troveranno
  già scritto e provato. Primo passo dello sviluppo KDE: prova delle incognite (cattura dopo il cambio di
  risoluzione, cursore, programmi X11, Chrome). Ripiego se la prova fallisce: labwc modificato, già visto funzionare.
- D3. SELinux: **DECISO (21 nov)**: regole SELinux complete nel pacchetto (stesso «muro» attorno alla parte di rete
  che AppArmor dà su Debian e Ubuntu), più la cura per l'avvio del desktop. Senza il muro Fedora non si pubblica.
  Il proprietario mette in conto un paio di giorni in più rispetto alle altre distro.
- D4. Aggancio all'accesso locale: **DECISO (21 nov)**: la specifica non cambia — una sessione locale chiude quella
  remota, su tutti e quattro i desktop. Il modo tecnico lo sceglie lo sviluppo (scelta: aggancio nelle regole di
  ciascuna schermata di accesso, con controllo di REMOTIX che l'aggancio ci sia ancora, senza sostituire la
  configurazione degli accessi dell'amministratore). Criteri di accettazione: (1) accesso locale con desktop remoto
  aperto → il remoto si chiude e il locale arriva al desktop, su gdm, plasmalogin, lightdm, sddm; (2) vale ancora
  dopo un aggiornamento del pacchetto della schermata di accesso; (3) alla rimozione di REMOTIX non resta nulla.
  (4) tutto automatico: l'amministratore non deve fare né controllare nulla perché la regola valga (proprietario:
  «l'admin non può preoccuparsi di quando un utente accede da remoto o è seduto davanti a un PC»).
- D5. Firewall: **DECISO (21 nov)**: come su Debian e Ubuntu. REMOTIX usa la porta 7447 (o quella scelta
  dall'amministratore); aprire la porta nel firewall e nel router è compito dell'amministratore. L'installazione
  non apre nulla. Il pacchetto porta la «scheda» di REMOTIX per il firewall di Fedora (come quella per ufw su Ubuntu).
- D6. Portachiavi: **DECISO (21 nov)**: come su Debian e Ubuntu (uniformità dei comportamenti): nessuna funzione
  nuova, la differenza rispetto all'accesso locale è dichiarata nel manuale.
- D7. XFCE, sfondo nero e nessuna icona sulla scrivania: **DECISO (21 nov)**: limite dichiarato nel manuale di
  Fedora, nessun rimedio nel codice (proprietario: evitare troppe personalizzazioni). Durante lo sviluppo solo una
  prova breve per sapere se un rimedio esiste; se sì, lo si riporta al proprietario con il costo.
- D8. OpenSSL: scelta tecnica, non del proprietario. Si usa quello di serie di Fedora (4.0) se il prodotto si
  costruisce e supera le prove; altrimenti il 3.5 che Fedora offre accanto. Si riferisce solo l'esito.

## Stato del banco
Quattro macchine spente, Radeon libera, istantanea `pulito` di ciascuna. Lo stato attuale delle macchine contiene
ciò che gli agenti hanno installato per lo studio (elenco in fondo a ogni documento); prima dello sviluppo vanno
riportate a `pulito`. Script `server/vm-radeon.sh` approvato dal revisore (terzo passaggio).

---

# Piano di sviluppo — REMOTIX per Fedora 45 (approvato dal proprietario il 21 nov 2026)

## Obiettivo
REMOTIX su Fedora 45 nei quattro desktop, con lo stesso comportamento di Debian 13 e Ubuntu 26.04 (versione 1.0.1),
protetto da SELinux come lo è da AppArmor sulle altre due. Codice solo per Fedora, in questa cartella; `debian13/`
e `ubuntu26.04/` non si toccano.

## Regole
- Si parte dalla copia del codice di Ubuntu (il più vicino) e si cambia solo ciò che Fedora richiede.
- Niente contenitori: si costruisce e si prova solo su macchine virtuali. Il codice lo scrive il `programmatore`,
  ogni pezzo passa dal `revisore`. Come e quando fare le prove lo decide il proprietario.
- A ogni problema chiuso o rimandato: una voce nel registro dei problemi.
- Sito, manuali e pubblicazione solo a prodotto pronto e su ordine del proprietario.

## Passi
0. **Preparazione.** Copia del codice di Ubuntu in questa cartella. Le quattro macchine tornano a `pulito`, ricevono
   i codec (RPM Fusion) e l'istantanea `codec`; prova della codifica vera con la Radeon. Una quinta macchina
   virtuale, senza Radeon, serve solo a costruire il pacchetto.
   Fatto quando: sulla macchina con la Radeon la prova di codifica H.264 riesce; la macchina di costruzione è pronta.
1. **Il pacchetto RPM.** Scritto da capo per Fedora: dipendenze con i nomi di Fedora, servizio installato spento,
   rifiuto senza scheda grafica e avviso se la scheda non codifica (come oggi), «scheda» per il firewall.
   Fatto quando: `dnf install ./remotix-….rpm` riesce sulle quattro macchine e la rimozione lascia il sistema pulito.
2. **Il desktop parte.** Regole di accesso di REMOTIX riscritte per Fedora e cura perché SELinux lasci partire il
   desktop; riconoscimento dei quattro desktop (plasmalogin compreso).
   Fatto quando: dal browser, password → desktop giusto su GNOME, XFCE e LXQt; mouse, tastiera, audio, appunti, uscita.
3. **KDE da solo (D2).** Prima la prova delle incognite (cattura dopo il cambio di risoluzione, cursore, programmi
   vecchio stile, Chrome); poi il codice. Se la prova fallisce: ci si ferma e si torna dal proprietario.
   Fatto quando: come al passo 2, su KDE, con cambio di dimensione della finestra del browser.
4. **Il locale chiude il remoto (D4).** Aggancio sulle quattro schermate di accesso, automatico e resistente agli
   aggiornamenti. Fatto quando: i quattro criteri di D4 sono verificati su gdm, plasmalogin, lightdm, sddm.
5. **Il muro SELinux (D3).** Regole complete attorno alla parte di rete, tradotte dal profilo AppArmor di Ubuntu.
   Fatto quando: con SELinux attivo e le regole in vigore, i passi 2-4 riescono ancora su tutti e quattro e il
   registro di SELinux non segnala rifiuti.
6. **Rifiniture.** Programmi avviati di serie da spegnere nella sessione remota, lingua e percorsi della sessione,
   controllo a fondo del componente labwc di Fedora (versione nuova) per XFCE e LXQt, prova breve sul rimedio
   per lo sfondo di XFCE (D7), convivenza della regola «nessuno spegne» con lightdm.
7. **Prove.** Le macchine vengono consegnate pronte al proprietario (apre solo il browser). Giri automatici solo se
   e come li decide lui. Prima di chiudere: accesso riuscito su ciascuna macchina con SELinux attivo e la Radeon.
8. **Chiusura.** Registro dei problemi, manuali di Fedora con la sezione «Requirements» in primo piano, pacchetto
   definitivo. Rilascio e sito solo su ordine del proprietario.

Ordine (proprietario, 21 nov: un desktop alla volta, non quattro insieme): 0 → 1 → poi per ciascun desktop, in
fila, i passi 2 e 4 (il desktop parte; il locale chiude il remoto), con consegna della macchina al proprietario per
le sue prove prima di passare al successivo: **GNOME** (il più vicino al codice di Ubuntu; qui nascono le cure
comuni: regole di accesso, SELinux per l'avvio) → **KDE** (passo 3, strada nuova: affrontata presto, così se la prova
delle incognite fallisce lo si sa subito) → **XFCE** → **LXQt** (stesso componente labwc, vicini fra loro).
Poi 5 (muro SELinux, provato su tutti e quattro) e 6. Dentro un desktop, i lavori indipendenti vanno in parallelo. Il passo 5 viene dopo perché le regole SELinux
si scrivono su un prodotto che già funziona.

## Rischi
- KDE da solo è una strada nuova: può richiedere il ripiego sul componente modificato.
- SELinux: regole sbagliate bloccano gli accessi (successe con AppArmor sulla prima prova di Ubuntu); per questo
  si provano sulle macchine vere, non a fine lavoro.
- OpenSSL 4.0 e labwc 0.20 sono versioni più nuove di quelle usate finora: possibili adattamenti del codice.
- La Radeon è una sola: le prove con la scheda vera vanno in fila.

## Stato (21 nov 2026, sera)
- Passo 0 fatto (istantanee `codec`, macchina `costruzione`, codifica vera con la Radeon riuscita).
- Passo 1 fatto e approvato dal revisore: `rpm/remotix.spec`, `build/build-rpm.sh`.
- GNOME: passi 2 e 4 fatti e approvati dal revisore (modulo SELinux per l'avvio, regole di accesso Fedora,
  `src/remotix-pam-hook` per gdm). Pacchetto `p4f` (sha256 `11768c64…2b7b`) sul server in
  `/media/REMOTIX-FEDORA/pacchetti/p4f/`. Macchina `gnome` consegnata al proprietario per le sue prove:
  istantanea `consegna-gnome` (Fedora pulita + codec + REMOTIX acceso), accesa con la Radeon, https://192.168.0.2:8851.
- Prossimo: KDE (passo 3). Finché il proprietario prova GNOME la Radeon è sua: su KDE solo lavoro senza scheda.
- 21 nov, sera — prove a mano del proprietario su GNOME (pacchetto `p4f`, macchina `gnome` con la Radeon): appunti,
  stacco e riattacco da due dispositivi (portatile Windows e PC Linux), audio e video: «tutto ok».
  Non provati da lui: due utenti insieme, telefono, programmi Flatpak, accesso locale.
- 21 nov, sera — prova del proprietario da Android su GNOME: video 1440p fluidissimo, anche scorrendolo avanti e
  indietro (su Ubuntu in macchina virtuale si erano visti piccoli scatti da Chrome su Android: voce E4 del registro).
- 22 nov, notte — KDE: passi 3 e 4 fatti e approvati dal revisore (secondo giro). KWin 6.8 da solo
  (`--kwin-virtual`, cambio di misura con `kde_output_management_v2`), gancio «il locale chiude il remoto» su
  plasmalogin; il blocco PAM ora sta subito dopo `pam_selinux close` (vale anche per gdm, riprovato).
  Pacchetto `k4b` (sha256 `bac4a375…8e86`) in `/media/REMOTIX-FEDORA/pacchetti/k4b/`. Macchina `kde` consegnata
  al proprietario: istantanea `consegna-kde` (Fedora pulita + codec + REMOTIX acceso), accesa con la Radeon,
  https://192.168.0.2:8852. Controllo di base 5/5 sulla macchina di consegna.
- Rimandati al passo 6 (registro F13, F16 e rilievi minori del revisore): riga di registro del rifiuto KDE,
  `g_set_error` in `kwin.c`, file di errore dei programmi Plasma alla chiusura forzata da fuori (prima misurare
  il caso reale «accesso locale con remoto aperto»). Codice labwc-per-KDE morto: da togliere dopo le prove del
  proprietario (elenco in `studio/5-kde-progetto.md` §8).
- Prossimo: XFCE (lightdm), dopo le prove del proprietario su KDE (la Radeon è della macchina `kde`).
- 22 nov, notte — XFCE (lightdm) e LXQt (sddm), parte SENZA Radeon fatta e approvata dal revisore: gancio «il locale
  chiude il remoto» attivo sui quattro display manager, trigger nello spec, `remotix.firewalld.xml` corretto (F17),
  sddm con file PAM del pacchetto modificati sul posto e cura per gli aggiornamenti (`prepare`/`apply`, F21).
  Pacchetto `l6` in `/media/REMOTIX-FEDORA/pacchetti/l6/` (vale per tutti e quattro i desktop; le macchine consegnate
  `gnome` = `p4f`, `kde` = `k4b`). Istantanee `xfce-x3`, `lxqt-l6`.
- ASPETTA LA RADEON (oggi alla macchina `kde` per le prove del proprietario): XFCE e LXQt con il desktop remoto vivo —
  `prove/giro-xfce-radeon.sh`, `prove/giro-lxqt-radeon.sh` (prove 1, 2, 3 del gancio, desktop, input, ciclo di vita,
  D7). Poi revisione, consegna, e passo 5 (muro SELinux).
- 22 nov — prove a mano del proprietario su KDE (pacchetto `k4b`, macchina `kde` con la Radeon): audio e video,
  appunti, stacco e riattacco da dispositivi diversi con risoluzioni diverse: «OK». Istantanea
  `dopo-prove-proprietario` sulla macchina `kde`. La Radeon passa a XFCE, poi a LXQt.
- 22 nov — deciso dal proprietario: le prove a mano di «il locale chiude il remoto» le fa lui ALLA FINE (passo 7),
  perché richiedono il riavvio del server. Fino ad allora valgono le prove automatiche. Prima del riavvio: controllare
  che VM, istantanee e pacchetti siano sul disco; dopo: `prepara-server.sh`.
- 22 nov — XFCE e LXQt col desktop remoto vivo (Radeon): tutte le prove passate, codice invariato, pacchetto `l6`
  (sha256 `26b5cc03…1eea4`) = pacchetto unico dei quattro desktop. Istantanee `xfce-fatto`, `lxqt-fatto`.
  Macchine di consegna: `consegna-xfce-2`, `consegna-lxqt-2` (Fedora pulita + codec + l6 + servizio acceso + porta
  aperta nel firewall). `xfce` accesa con la Radeon, https://192.168.0.2:8853; poi `lxqt` su :8854.
- DA SISTEMARE (passo 6, registro F20): subito dopo l'installazione `firewall-cmd --permanent --add-service=remotix`
  risponde INVALID_SERVICE finché non si fa `firewall-cmd --reload` (visto preparando le macchine di consegna):
  la riga del manuale deve cominciare con `--reload`, oppure lo fa il pacchetto.
- 22 nov, mattina — prove del proprietario su XFCE: dal notebook Windows «Opening handshake failed». Causa trovata e
  confermata: orologio del notebook sballato (il certificato di sessione, nato pochi minuti prima con notBefore =
  adesso − 1 h, risultava «non ancora valido»). Rimessa l'ora, il riaggancio funziona. Non è un difetto del prodotto.
  Per le rifiniture: riga di registro col motivo della chiusura di una connessione (in lavorazione, pacchetto `d1`);
  nota nei «Requisiti» del manuale: orologio del dispositivo client giusto; voce nel registro dei problemi.
- 22 nov — prove del proprietario su XFCE (pacchetto `l6`): «anche xfce è passato». Istantanea
  `dopo-prove-proprietario` sulla macchina `xfce`. Radeon a `lxqt` (`consegna-lxqt-2`), https://192.168.0.2:8854.
- 22 nov, LXQt: prove del proprietario OK («come gli altri»). Istantanea `dopo-prove-proprietario` su lxqt, Radeon
  libera. Tutti e quattro i desktop provati dal proprietario con il pacchetto l6. Si passa al passo 5 (muro SELinux).
- 22 nov, revisione della riga «chi ha chiuso» (d1, `src/transport.c` close_why): DA CORREGGERE, gravità bassa, solo
  testo di log. (1) la chiusura per silenzio (30 s) esce come «transport error 0x0 NO_ERROR» invece di «idle timeout»:
  nei rami NGTCP2_ERR_IDLE_CLOSE (righe ~2181 e ~2585) registrare l'errore in `last_error`, oppure in close_why dire
  «no error recorded» per l'errore di default; allineare il commento (~959). (2) facoltativo: sostituire anche `"`
  nella reason del client (~1069). Da fare al passo 6, a regole SELinux stabili, poi di nuovo revisore.
- 22 nov, passo 5 (muro SELinux): consegnato dal programmatore, pacchetto `s8` (sha256 40893dcd…34529807), in
  revisione. Dichiarato: enforcing, 0 rifiuti nostri sui quattro desktop; xfce e lxqt 60 PASS 0 FAIL; gnome e kde
  con i soli FAIL già presenti senza muro (da riconfermare: reattach-windows-inside su KDE non confrontato); prova
  negativa 18/18 su tutte e quattro; F5 (utenti confinati) provato solo su GNOME; F10 chiuso. Tipo di porta proprio
  non fatto (motivato). Resta largo il lato root (`remotix_t`), in particolare le «faccende» nel gestore utente:
  alternativa (rieseguirle nel dominio dell'utente) non fatta, giudizio chiesto al revisore. Istantanee
  `selinux-<de>`. Non provato: accesso locale vero da gdm/plasmalogin con il muro, riavvio della VM col modulo.
- 22 nov, revisione del muro SELinux (s8): DA CORREGGERE, rimandato allo stesso programmatore. Bloccante: la
  funzione del contesto utente prosegue anche in caso d'errore (utente confinato in sessione non confinata).
  Prima di pubblicare: il servizio con SELinux attivo non deve partire senza muro (oggi solo un avviso); prova
  negativa da rifare in modo che provi SELinux e non i permessi Unix, con log salvati; portachiavi di sessione per
  utenti confinati da verificare su XFCE/LXQt/KDE. Rifiniture: regole 282-283, 225, 331 del .te, restorecon in
  rimozione. Giudizio del revisore sul lato root largo (`remotix_t`): accettabile per pubblicare (come sshd; su
  Debian/Ubuntu non è confinato affatto); far rieseguire le «faccende» nel dominio dell'utente: DOPO, priorità bassa.
- 22 nov, proprietario: «REMOTIX dev'essere omogeneo tra le varie distro». Applicato: la correzione «il servizio
  non parte senza muro» è RITIRATA — resta come AppArmor su Debian/Ubuntu (criterio non caricato = avviso e si
  prosegue; caricato e rifiutato = la parte di rete non parte). Il lato root non si stringe oltre su Fedora sola.
  Il programmatore deve elencare ogni punto in cui Fedora si comporta diversamente da Debian/Ubuntu.
- 22 nov sera, correzioni al muro SELinux consegnate: pacchetto `s13` (sha256 f65c37e9…10b11a20), in seconda
  revisione. Dichiarato: gnome 51 PASS (FAIL pkexec noto), kde 64 PASS (4 FAIL identici senza muro, compreso
  reattach-windows-inside confrontato con k4b), xfce 60/0, lxqt 60/0; prova negativa rifatta 25/25 sulle quattro
  (ha trovato e tolto due larghezze vere); portachiavi degli utenti confinati corretto; riavvio VM col modulo ok.
  F30: XFCE con utente staff_u, pannello non parte — riprodotto senza REMOTIX, non nostro (da dichiarare).
  Differenze di codice rispetto a Ubuntu: contesto/portachiavi SELinux (child.c), compilazione dconf (session.c),
  MESA_SHADER_CACHE_DISABLE nell'unità. Non provati: percorsi di rifiuto 44-46, avviso del %post, suite
  multiuser/media/resilience/phone con s13. Istantanee `selinux2-<de>`.
- 22 nov sera, seconda revisione del muro (s13): tutto approvato tranne tre punti piccoli, rimandati al
  programmatore per `s14`: portachiavi di sessione di proprietà di root invece che dell'utente (prima di
  pubblicare), commento non veritiero in child.c, nome `remotix.new` in rimozione. Nello stesso giro: correzione
  di close_why (idle timeout), prova dei rifiuti 44-46, contatore di perdite AVC, suite complete su gnome.
- 22 nov notte, correzioni consegnate: pacchetto `s15` (sha256 7fdf1725…8c703ffa; s14 + una regola per i segnali
  della spazzata verso Xwayland e agenti). Portachiavi ora dell'utente (provato contro ssh su GNOME/XFCE/KDE);
  rifiuti 44 e 37 provati; perdite audit 0; close_why corretto e provato. Giro completo con s14 sui quattro +
  all.sh su gnome; con s15 completo solo xfce, mirato sulle altre. In terza revisione (muro) e seconda (close_why).
- 22 nov notte, terza revisione del muro (s15): approvati portachiavi, rifiuti, spec, perdite audit; close_why
  APPROVATO. Da correggere prima di pubblicare: i segnali della spazzata vanno permessi verso ogni dominio (anche
  SIGKILL), non tipo per tipo — altrimenti un desktop orfano può sopravvivere. Rifinitura: non sostituire il
  portachiavi di PAM quando l'etichetta è già giusta (uguale a Ubuntu nel caso comune). Rimandato al programmatore
  insieme alle rifiniture del passo 6 (FAIL pre-esistenti di gnome/kde, autostart, lingua/percorsi, lightdm+polkit,
  riga di log del gancio, firewall reload, misura F16, labwc/D7). Rinviata: rimozione del codice morto labwc-KDE.
- 23 nov notte, rifiniture consegnate: pacchetto candidato `f1` (sha256 f4a749e9…c843efe0), in quarta revisione.
  Giro completo f1 in enforcing: gnome 52 PASS (FAIL pkexec noto) + all.sh 36 PASS (FAIL two-users, three-users,
  tap-click-portrait); kde 78/0 (i FAIL di prima erano del banco/della prova: Chromium mancante, aiutante
  tollerato, aspettativa sulla finestra rimpicciolita da KWin); xfce 60/0; lxqt 60/0; AVC nostri 0. Segnali verso
  ogni dominio fatti e provati; firewall: `%firewalld_reload`, la riga dell'amministratore riesce subito; F16: 0
  core dump nel caso reale simulato; labwc 0.20.2 a posto; D7 resta limite dichiarato. Istantanee `finale-<de>`.
  Aperti e in lavorazione: (1) su GNOME un click arriva con una coordinata a 0 nelle prove con più utenti e
  telefono — in indagine; (2) lingua della sessione remota (C.UTF-8 invece di quella di sistema) — in correzione.
  Aperto e noto: pkexec su GNOME (SHELL vuoto, comune a Ubuntu).
- 23 nov notte, quarta revisione (f1): prodotto, regole SELinux, firewall, gancio e prove riviste APPROVATI. Manca
  solo una conferma scritta nelle prove (il permesso di SIGKILL verso ogni dominio non compare nel file salvato per
  un filtro dello script; riga del journal della spazzata) e un minimo nella prova KDE della finestra. Rimandate al
  programmatore insieme all'indagine sul click e alla lingua.
- 23 nov notte, consegnato `g6` (sha256 d1f67e0b…4b34a78681) = f1 + due correzioni, in quinta revisione:
  (1) click su GNOME: il primo movimento del puntatore dopo l'accesso arrivava con una coordinata a 0 (difetto di
  mutter 51, con un solo utente; quasi certamente lo stesso di E2 su Ubuntu); cura in input.c (primo movimento
  inviato due volte); two/three-users e phone ora PASS. (2) lingua della sessione = quella dell'utente/di sistema
  invece di C.UTF-8, e PATH come in locale (child.c). Base+input 31/0 sui quattro. Conferma scritta di SIGKILL
  ottenuta (K), minimo nella prova KDE (L). DA DIRE AL PROPRIETARIO: le due correzioni valgono anche per
  Debian/Ubuntu (là la lingua remota è ancora C.UTF-8 e il primo tocco su GNOME è «saltuario»): portarle è sua scelta.
- 23 nov notte, quinta revisione (g6): approvati la cura del puntatore, il PATH, K e L. Da correggere: la lingua
  scelta dall'utente (AccountsService) non viene mai letta perché il file è di root e il codice lo legge dopo il
  cambio d'identità ⇒ vale sempre la lingua di sistema. Rimandato: lettura da root prima del cambio d'identità +
  regola SELinux di sola lettura; poi giro finale completo sui quattro e macchine `consegna-finale-<de>` (dalla
  `codec` pulita + pacchetto finale) per le prove del proprietario.
- 23 nov mattina, consegnato `h1` (sha256 550f368b…c9de191c71, modulo SELinux 1.1.1), in sesta revisione: lingua
  scelta dall'utente letta da root prima del cambio d'identità (+ regola di sola lettura), LC_* passati; provato
  su GNOME con desktop davvero in italiano. Giro finale h1 in enforcing: gnome 52 PASS (FAIL pkexec noto) + all.sh
  39 PASS; kde 76; xfce 60; lxqt 60; prova negativa 0 FAIL; AVC nostri 0. Macchine per il proprietario pronte:
  istantanee `consegna-finale-<de>` (dalla `codec` pulita + solo h1, servizio acceso, porta aperta), spente.
- 23 nov mattina, sesta revisione: `h1` APPROVATO (lingua, LC_*, regola SELinux di sola lettura). Restano fuori dal
  prodotto: (a) `prove/giro-selinux.sh` nasconde un controllo morto a metà (su KDE `check-kde-exit` caso «service
  restart» una volta è uscito senza risultato; da solo 3/3: intermittente, causa da trovare quando il giro
  conserverà l'uscita) — prima di pubblicare; (b) commento a `src/child.c:1636` da allineare; (c) da provare: lingua
  senza codifica in AccountsService (`it_IT`). GNOME di consegna accesa con la Radeon per le prove del proprietario.
- 23 nov, prove finali del proprietario con h1 e muro SELinux: GNOME OK (istantanea `dopo-prove-finali`).
- 23 nov, prove finali del proprietario: KDE OK (istantanea `dopo-prove-finali`).
- 23 nov, prove finali del proprietario: XFCE OK (istantanea `dopo-prove-finali`).
- 23 nov, prove finali del proprietario: LXQt OK (istantanea `dopo-prove-finali`). Tutti e quattro i desktop provati dal proprietario con h1 e il muro SELinux. Resta la sua prova a mano «il locale chiude il remoto» (riavvio del server).
- 23 nov, STATO ALLA CHIUSURA DELLA CHAT. Pacchetto finale approvato e provato dal proprietario sui quattro
  desktop: `h1` (/media/REMOTIX-FEDORA/pacchetti/h1/, sha256 550f368b…c9de191c71). Istantanee
  `consegna-finale-<de>` (pulite + h1) e `dopo-prove-finali`. Tutto spento, Radeon libera; VM, istantanee e
  pacchetti sono su disco (nvme), `prepara-server.sh` in /media/REMOTIX-FEDORA/.
  PROSSIMO: prova a mano «il locale chiude il remoto» — il proprietario la farà con le LIVE di Fedora sul server
  (parole sue: «le prove di fedora con le live sul server»), stasera, riaprendo la chat.
  DECISIONE del proprietario: le due correzioni nate stanotte (lingua della sessione; primo clic su GNOME) RESTANO
  in Fedora e Debian/Ubuntu vanno adeguate: piano in `../PIANO-1.0.2-debian-ubuntu.md`, IN ATTESA del suo OK e di
  quattro sue decisioni (numero di versione, come costruire i .deb, ampiezza delle prove, ISO di Debian).
  Errore mio da non ripetere: le due correzioni sono state fatte senza piano né OK e hanno creato una differenza
  fra le distro. Aperti prima di pubblicare Fedora: `prove/giro-selinux.sh` nasconde un controllo morto a metà
  (KDE, check-kde-exit «service restart», intermittente); commento a child.c:1636; lingua senza codifica in
  AccountsService da provare; manuali Fedora con «Requirements»; fedora45/ non è ancora in git.
- 25 nov, prova a mano del proprietario «il locale chiude il remoto» sulla macchina vera (server avviato dalla chiavetta
  Fedora 45 LIVE, due schede: Intel + Radeon; pacchetto `h1` installato con `server/live-installa.sh`, nuovo, APPROVATO
  dal revisore; SELinux enforcing, 0 rifiuti dopo l'installazione; codifica riuscita sulla Intel): **GNOME (gdm) OK**
  — parole sue: «la sessione locale ha disconnesso la sessione remotix». Registri della live non salvati (macchina già
  spenta). Seguono KDE, XFCE, LXQt con le rispettive chiavette. Copia dello script sul server: `/media/fedora_install.sh`.
- 25 nov, stessa prova sulla live **KDE (plasmalogin): NON SUPERATA — difetto del prodotto**. Remoto di `prova` aperto
  (con Konsole e `top` dentro), accesso locale di `prova`: il browser viene scollegato, ma il desktop remoto NON viene
  chiuso e il desktop locale non parte (schermo fermo; la macchina è viva). Fatti letti dai registri: (1) la chiusura
  ordinata (`org.kde.Shutdown.logout`) non finisce entro 10 s; (2) la chiusura forzata viene RIFIUTATA dal nostro muro
  SELinux: `remotix_t` non può fare `stop` su `plasma-kwin_wayland.service` (etichetta `xdm_unit_file_t`), 3 rifiuti;
  (3) al tetto di tempo il figlio viene ucciso e l'accesso locale è lasciato passare con KWin, plasmashell, ksmserver
  remoti ancora vivi nel gestore dell'utente → `startplasma-wayland` locale senza compositore, programmi di Plasma in
  core dump. Le prove sulle VM non l'hanno visto: lì la chiusura ordinata riusciva e la strada forzata non girava mai.
  Prove salvate sul tablet: `~/remotix-prove-live/fedora45-kde-live-25nov*`. Altro rifiuto visto (innocuo?, da
  guardare): `remotix_t` `search` su `/proc/sys/dev`. DA FARE: piano di correzione (regola SELinux + che cosa fare
  quando la chiusura forzata non riesce + prova di banco con un programma aperto), poi OK del proprietario.
- 25 nov, stessa prova sulla live **XFCE (lightdm): OK**. Il primo «blocco» non era del prodotto (tastiera del
  proprietario collegata al tablet: la password non arrivava alla schermata di accesso). Al tentativo vero: chiusura
  ordinata del desktop remoto in 1,7 s, sessione locale di `prova` aperta al primo colpo, niente rimasto del remoto,
  nessun rifiuto SELinux nuovo, nessun core dump dell'utente. Registri: `~/remotix-prove-live/fedora45-xfce-live-25nov*`.
  Resta da provare LXQt; KDE resta NON superata (vedi sopra).
- 25 nov, stessa prova sulla live **LXQt (sddm): OK**. Chiusura ordinata del desktop remoto in 0,7 s, sessione locale
  di `prova` aperta al primo colpo, niente rimasto del remoto, nessun rifiuto SELinux nuovo, nessun core dump
  dell'utente. Registri: `~/remotix-prove-live/fedora45-lxqt-live-25nov*`.
  SOMME delle prove da chiavetta (25 nov): GNOME OK, XFCE OK, LXQt OK, **KDE NON superata** (difetto del prodotto).
  Fedora non è pubblicabile finché KDE non passa la stessa prova. PROSSIMO: piano di correzione di KDE, da mostrare
  al proprietario; serve il server riavviato in modo normale (`prepara-server.sh`).

## PIANO DI CORREZIONE — KDE: «il locale chiude il remoto» (25 nov, IN ATTESA dell'OK del proprietario)

**Obiettivo.** Su Fedora KDE, quando un utente con il desktop remoto aperto accede in locale, il desktop remoto deve
chiudersi DEL TUTTO prima che parta quello locale, anche se ha programmi aperti e anche se Plasma non collabora.
Nessun cambiamento di comportamento voluto: è la regola già decisa (D4), che oggi su KDE non viene rispettata.

**Che cosa non ha funzionato (dai registri della live).**
1. La chiusura gentile (chiedere a Plasma di uscire) non è finita nei 10 secondi. Causa non ancora accertata;
   sospetto: il terminale con un programma in corso.
2. La chiusura forzata è partita ma su Plasma 6.8 ferma solo il «contenitore», non il gestore dello schermo, il
   pannello e il gestore di sessione, che restano vivi.
3. L'ultima difesa (fermare il gestore dello schermo remoto dalla parte amministrativa di REMOTIX) è stata RIFIUTATA
   dal nostro muro SELinux: manca una regola.
4. Scaduto il tempo, l'accesso locale passa comunque e trova il desktop remoto vivo: schermo locale inservibile.

**Passi.**
1. Rifare il guasto sulla macchina virtuale `kde` (remoto con Konsole e `top` aperti, poi accesso locale): senza
   questo nessuna correzione è verificabile. Aggiungere il caso alla prova di banco (`prove/check-prelocal.py`):
   oggi la prova passa perché non apre programmi e la strada forzata non gira mai.
2. Muro SELinux (`selinux/`): permettere a REMOTIX di fermare le unità di Plasma dell'utente (solo «ferma» e «stato»,
   solo sulle unità del desktop), e controllare con lo stesso metodo le unità degli altri tre desktop.
3. Chiusura forzata di KDE (`src/session.c`): deve fermare davvero gestore dello schermo, pannello e gestore di
   sessione, non solo il contenitore; capire perché la chiusura gentile non finisce e, se dipende dal programma
   aperto, come si comporta un'uscita normale di Plasma nello stesso caso.
4. Rete di sicurezza comune ai quattro desktop (`src/rootside.c`): se alla scadenza il desktop remoto è ancora vivo,
   va detto chiaramente nel registro; che cosa fare in quel caso è la DECISIONE qui sotto.
5. Pacchetto nuovo sulla VM di costruzione, revisore, poi prova di banco sui quattro desktop con SELinux attivo.
6. Prova finale del proprietario da chiavetta KDE (stessa prova di oggi). Voce nel registro dei problemi.

**File.** `selinux/*.te`, `src/session.c`, `src/rootside.c`, `prove/check-prelocal.py`, `docs/REGISTRO-problemi.md`.

**Rischi.** Una regola SELinux troppo larga indebolisce il muro (per questo: solo «ferma/stato», solo unità del
desktop). Toccare la chiusura di KDE può cambiare l'uscita normale dal desktop remoto: va riprovata anche quella.
Debian 13 e Ubuntu 26.04 usano un'altra strada per KDE: da controllare a tavolino se il punto 2 dei guasti li riguarda.

**DECISIONE del proprietario.** Se, nonostante tutto, il desktop remoto non si chiude entro il tempo massimo:
(a) REMOTIX termina di forza tutti i programmi del desktop remoto e poi lascia entrare l'utente (consigliata: è la
regola «niente di vivo»; si perde ciò che non era salvato nel remoto); oppure (b) come oggi, lascia entrare e basta.

**Fatto quando.** Sulla VM `kde` e sulla chiavetta KDE: remoto con programmi aperti → accesso locale → desktop
locale al primo colpo, niente di vivo del remoto, nessun rifiuto SELinux, nessun core dump; GNOME, XFCE, LXQt
continuano a passare la stessa prova.

**DECISO dal proprietario (25 nov, «No, sistemiamo solo KDE»).** Piano approvato, ma ristretto: si corregge SOLO KDE.
Il passo 4 (rete di sicurezza comune ai quattro desktop) NON si fa: alla scadenza resta il comportamento di oggi
(opzione b). Nessuna modifica al codice di GNOME, XFCE, LXQt; nessun giro di prove sugli altri tre desktop se non lo
chiede lui. Prove: banco su KDE, poi la sua prova da chiavetta KDE. Fatti finora: regola SELinux scritta
(`selinux/remotix.te`: `remotix_t` può fare `stop`/`status` sulle unità `xdm_unit_file_t`), casi di banco P7/P8
scritti in `prove/check-prelocal.py` (non ancora eseguiti). Messo da parte, da decidere dopo: (1) GNOME ha la stessa
costruzione di KDE e nessuna «ultima difesa» (non provato, nessun guasto visto); (2) Debian/Ubuntu hanno lo stesso
codice di chiusura di KDE (da provare quando ci sarà il loro banco); (3) rifiuto innocuo `search` su `/proc/sys/dev`.
- 25 nov, correzione di KDE fatta: `src/session.c` (la forzata di KDE ferma `graphical-session.target`, non più
  `plasma-workspace.target`) e `selinux/remotix.te` (regola stop/status su `xdm_unit_file_t`). Revisore: APPROVATO.
  Pacchetto `i1` (/media/REMOTIX-FEDORA/pacchetti/i1/, sha256 06cf6dcd…41b414a8; costruito un attimo prima di due
  ritocchi ai soli commenti: il binario e il modulo sono quelli dell'albero). Banco sulla VM `kde` (Radeon, enforcing):
  guasto rifatto con h1 (programma che chiede «salvare?»: Plasma aspetta senza limite); con i1: senza programmi
  chiusura ordinata 2,9 s; con Konsole+top+kwrite non salvato forzata a 10,0 s e tutto fermo 0,54 s dopo (gancio a
  10,9 s, margine ~2 s sulla scadenza dei 13 s), 3 prove pulite; ultima difesa da sola (figlio ucciso): stop di kwin
  riuscito, 0 rifiuti; uscita normale dal remoto e rientro: come prima; `check-prelocal.py` P1–P8 su KDE tutti PASS
  (P7 terminale = strada ordinata, P8 editor non salvato = strada forzata). Istantanea `kde-i1-provato`.
  Non provato: chiusura per abbandono. Osservato e messo da parte: con Konsole resta un piccolo aiutante di podman
  (`catatonit`) nel gestore dell'utente dopo l'accesso locale (innocuo); nella strada «ultima difesa» i programmi
  Plasma rimasti vanno in core dump quando KWin viene fermato (noto, F9); `dm_restart` del banco fragile su plasmalogin.
  PROSSIMO: prova del proprietario da chiavetta KDE con `i1` (il tablet lo serve già a `fedora_install.sh`).
- 25 nov, prova del proprietario da chiavetta KDE con `i1`: **KDE OK** («Funziona, ma ci ha messo qualche secondo in più
  della media»). Registri: forzata a 10,05 s, tutto fermo 0,56 s dopo, gancio liberato a 10,9 s, desktop locale subito,
  0 rifiuti SELinux, 0 core dump (`~/remotix-prove-live/fedora45-kde-live-25nov-i1-journal-completo.txt.gz`). I secondi
  in più sono i 10 s di attesa della chiusura gentile. Voce F36 nel registro. I quattro desktop hanno passato la prova
  sulla macchina vera (GNOME, XFCE, LXQt con h1; KDE con i1). Da decidere col proprietario: accorciare l'attesa su KDE?
- 25 nov, DECISO dal proprietario («facciamo una prova con 5 secondi»): su KDE, solo nella chiusura per accesso locale,
  la chiusura gentile aspetta 5 s invece di 10 prima della forzata (`src/session.c`, `KDE_PRELOCAL_ORDERLY_MS`).
  Revisore: APPROVATO. È una PROVA: pacchetto `i2` da costruire (server da riavviare in modo normale), giro breve sul
  banco KDE, poi chiavetta KDE. Atteso: gancio liberato a ~6 s invece di ~11. Compromesso da dire al proprietario: una
  chiusura sana che impiegasse fra 5 e 10 s (macchina lenta, molti programmi) ora viene troncata dalla forzata.
  Messo da parte (revisore): `force_guard_on` resta acceso dopo una chiusura per accesso locale fallita (`session.c:8770`).
- 25 nov, pacchetto `i2` (attesa 5 s; /media/REMOTIX-FEDORA/pacchetti/i2/, sha256 172d4e89…6393930b), giro breve sulla
  VM `kde` (enforcing): senza programmi 2,9 s; Konsole+top+kwrite non salvato ×2: forzata a 5,03 s, tutto fermo 0,54 s
  dopo, gancio a 5,87 s (margine ~7 s); dieci programmi sani: chiusura ordinata in 1,1 s, nessuna forzata; uscita
  normale dal remoto con kwrite non salvato: nessuna forzata (come prima), rientro ok; P1–P8 PASS. Istantanea
  `kde-i2-provato`. Non provati: programmi lenti a chiudersi, chiusura per abbandono. PROSSIMO: chiavetta KDE con i2.
- 25 nov, prova del proprietario da chiavetta KDE con `i2` (attesa 5 s): **KDE OK**. Registri: forzata a 5,04 s, tutto
  fermo 0,56 s dopo, gancio liberato a 5,9 s, desktop locale subito, 0 rifiuti SELinux, 0 core dump, niente di vivo del
  remoto (`~/remotix-prove-live/fedora45-kde-live-25nov-i2-journal-completo.txt.gz`). I 5 s restano (prova riuscita).
  Proprietario: «Possiamo considerare chiuso il discorso fedora». PACCHETTO CANDIDATO: `i2`
  (/media/REMOTIX-FEDORA/pacchetti/i2/, sha256 172d4e89b5070d14a8d3ddf443ff20409559f9173b632bc821564d086393930b).
  Stato delle prove su macchina vera: GNOME, XFCE, LXQt con h1; KDE con i2 (i2 differisce da h1 solo per la chiusura
  di KDE e la regola SELinux; NON è stato rieseguito sugli altri tre desktop, per decisione del proprietario).
  Restano prima di pubblicare (già in elenco): `prove/giro-selinux.sh` che nasconde un controllo morto a metà; commento
  a child.c:1636; lingua senza codifica in AccountsService; manuali Fedora con «Requirements»; `fedora45/` non è in
  git. Rilascio solo su ordine del proprietario. Messi da parte il 25 nov: GNOME senza ultima difesa; Debian/Ubuntu con
  lo stesso codice di forzata; `catatonit`; rifiuto `/proc/sys/dev`; `force_guard_on` (session.c:8770).

## PIANO — MANUALI DI FEDORA 45, versione 1.2 (25 nov, IN ATTESA dell'OK del proprietario; lo studio è già partito)

**Obiettivo.** Due manuali per Fedora 45, come per Debian e Ubuntu: «User Manual — Fedora 45» (6 capitoli) e «Technical
Manual — Fedora 45» (25 capitoli), in inglese, un file HTML ciascuno in `fedora45/manuals/`, controllati contro il codice
di `fedora45/` (`build.py --check` verde). Versione scritta nei manuali e nel pacchetto: **1.2** (ordine del proprietario
del 25 nov; il motivo lo spiegherà lui). Nel pacchetto RPM la scrivo `1.2.0`, nello schema a tre numeri usato finora.

**Metodo (lo stesso usato per Ubuntu, che ha funzionato).**
1. Studio (sola lettura, cinque lettori in parallelo): i capitoli del manuale di Ubuntu, sezione per sezione, confrontati
   con ciò che su Fedora è diverso (pacchetto RPM e dnf, SELinux al posto di AppArmor, codec da RPM Fusion, firewalld,
   KDE con KWin da solo e plasmalogin, aggancio all'accesso locale sulle quattro schermate, macchine virtuali al posto
   dei contenitori, i problemi F1–F36). Per ogni sezione: vale com'è / da correggere / da riscrivere.
   Esito in `studio/manuali/inventario-*.md`.
2. Sorgenti: copia dei sorgenti dei manuali di Ubuntu in `fedora45/manuals/sources/` (cartelle `user-fedora45`,
   `technical-fedora45`), `build.py` adattato (titoli, nomi dei file, versione letta da `rpm/remotix.spec`).
3. Scrittura (cinque scrittori in parallelo, un gruppo di capitoli ciascuno, file diversi): secondo l'inventario.
   Nel manuale utente la sezione **«Requirements»** in primo piano (decisione D1): scheda video che codifica H.264,
   driver da RPM Fusion, porta 7447 nel firewall (riga già pronta, registro F20), SELinux attivo. Limiti dichiarati:
   portachiavi (D6), sfondo e icone di XFCE (D7), nessuno spegnimento dal desktop.
4. Versione: `Version: 1.2.0` in `rpm/remotix.spec` (con la riga di storia), pacchetto ricostruito sulla VM di
   costruzione; i nomi dei file citati nei manuali seguono (`remotix-1.2.0-1.fc45.x86_64.rpm`).
5. Controllo: `build.py --check` verde, revisore sui manuali (a gruppi), correzioni, poi la lettura del proprietario.
6. Sito: DOPO i manuali, con un piano a parte.

**File.** Nuovi: `fedora45/manuals/**`, `fedora45/studio/manuali/*`. Modificati: `rpm/remotix.spec` (solo versione e
storia). Nessun file di `debian13/` e `ubuntu26.04/` viene toccato.

**Rischi.** Il manuale tecnico è grande (25 capitoli, ~10 000 righe): copiare da Ubuntu frasi vere lì e false su Fedora
(per questo l'inventario sezione per sezione e il revisore). Cifre da ricontare sul codice di Fedora, non da copiare.
Il pacchetto 1.2.0 è lo stesso codice di `i2` con un altro numero: va comunque ricostruito e la sua installazione
riprovata una volta (non le prove dei desktop). Le cose «messe da parte» il 25 nov restano fuori e vanno dichiarate
dove il manuale ne parla, senza promettere ciò che non c'è.

**Decisioni che servono dal proprietario.** (a) OK al piano; (b) «1.2.0» va bene come scrittura di «1.2»?; (c) il
pacchetto 1.2.0 lo costruisco io alla fine (serve il server in modo normale) — sì/no.

**Fatto quando.** I due file HTML esistono, `--check` è verde, il revisore ha approvato, il proprietario li ha letti.
- 25 nov, piano dei manuali APPROVATO dal proprietario; versione scritta `1.2.0` (OK suo). Passo 1 (studio, cinque
  lettori) e passo 2 (sorgenti + `build.py`) in corso. Il pacchetto 1.2.0 lo ricostruisco io al passo 4.
- 25 nov, motivo del numero 1.2.0 (proprietario): le modifiche nate su Fedora (parole sue: «in KDE sono state introdotte
  delle modifiche che ho deciso di estendere ai 4 DE di debian e ubuntu») sono sostanziali; per tenere allineato il
  codice anche Debian 13 e Ubuntu 26.04 avanzeranno alla 1.2.0. A fine lavoro: preparare la consegna per la prossima
  sessione (Debian e Ubuntu 1.2.0); il vecchio `../PIANO-1.0.2-debian-ubuntu.md` confluisce lì.
- 25 nov, su ordine del proprietario («labwc esce dalla responsabilità di remotix, è un pacchetto dei repository
  standard di fedora»; «correggi»): `LICENSE.md` §8 senza il paragrafo su labwc; `THIRD-PARTY-LICENSES` senza le voci
  e i testi di labwc 0.9.3 e wlroots 0.19.2 (programma separato che il pacchetto Fedora non porta); `src/kwin.c`: i tre
  messaggi RX-KDE-001/002/003 consigliano `sudo dnf reinstall remotix` (era `apt install --reinstall`). `Version: 1.2.0`
  nello spec. DA FARE prima del pacchetto 1.2.0: revisore su queste modifiche. DA DECIDERE (proprietario):
  `THIRD-PARTY-LICENSES` cita ancora «remotix-install» e il motore di installazione in Go (17 moduli), che il pacchetto
  Fedora non contiene (residuo ereditato; c'è anche nei file di Debian e Ubuntu già pubblicati).
- 25 nov, il proprietario ha scaricato sul server le quattro live di Debian 13.8.0 (gnome, kde, lxqt, xfce) in
  `/media/DOWNLOAD`: con le quattro di Ubuntu 26.04.1 già presenti ci sono tutte le immagini per rifare i banchi di
  Debian e Ubuntu (lavoro 1.2.0, prossima sessione).
- 25 nov, perimetro della 1.2.0 di Debian e Ubuntu (proprietario): «allineare il più possibile, tenendo conto di:
  specificità della distro e versione di KDE». Quindi non solo le correzioni di oggi: portare il codice il più vicino
  possibile a quello di Fedora; resta diverso solo ciò che dipende dalla distribuzione o dal Plasma più vecchio.
- 25 nov, su ordine del proprietario («elimina da fedora riferimento a materiale che non c'è in remotix»):
  `THIRD-PARTY-LICENSES` di Fedora senza «remotix-install», Go 1.25.14 e i 17 moduli Go (18 voci tolte); restano 17 voci,
  tutte di cose che il pacchetto contiene (ngtcp2, nghttp3, sfparse, libopus, Emscripten, musl, 12 protocolli Wayland;
  ricontati: i 12 file .xml di `src/protocols` sono tutti compilati dal Makefile). Descrizione di `wlr-layer-shell`
  corretta (strada non percorsa su Fedora). Per Debian/Ubuntu lo stesso residuo va nella 1.2.0. Revisore: prima del pacchetto.
- 25 nov, stessa classe dei tre messaggi di KDE (ordine «correggi»): altri tre messaggi all'amministratore con
  strumenti di Debian corretti per Fedora, solo testo: `src/main.c` (servizio PAM mancante → «sudo dnf reinstall
  remotix»; desktop che non parte → «weak dependency … --setopt=install_weak_deps=False»), `src/session.c` (D-015 e
  la riga vicina: pacchetto `dconf`, non `dconf-cli`). Da passare al revisore col resto prima del pacchetto 1.2.0.
  I manuali vanno riallineati dove citano il testo vecchio di questi messaggi. Residui NON toccati (commenti, strumenti
  di prova ancora di Ubuntu, codice labwc-per-KDE irraggiungibile): elenchi in `studio/manuali/note-*.md`.
- 25 nov sera, MANUALI DI FEDORA scritti: `manuals/Technical Manual — Fedora 45.html` (25 capitoli, 1,6 MB) e
  `manuals/User Manual — Fedora 45.html` (6 capitoli, 161 KB), versione 1.2.0. Metodo del piano: inventario di 283
  sezioni (cinque lettori, `studio/manuali/inventario-*.md`), sei scrittori, sei revisori (prima lettura: tutti DA
  CORREGGERE; correzioni; seconda lettura: tutti APPROVATI, l'ultima frase di ch10 sistemata dopo), `build.py --check`
  verde («manual aligned with the code»). Note degli scrittori con ciò che NON è verificato e i residui dei sorgenti:
  `studio/manuali/note-*.md`. Manca: la lettura del proprietario.
  `LICENSE.md` §1: tolto dalla definizione di «REMOTIX» il vecchio installatore (`remotix-*.run`): ora «the REMOTIX
  packages» (stesso ordine: niente riferimenti a materiale che non c'è). Revisore sulle modifiche al prodotto: in corso.
- 25 nov sera: revisore (Fable) sulle modifiche al prodotto di oggi (versione, licenze, messaggi): un rilievo
  (il rimedio «sudo dnf reinstall remotix» non funziona con un pacchetto installato da file → ora «reinstall the
  package from its file (sudo dnf reinstall ./remotix-<version>.rpm)» in kwin.c ×3 e main.c, manuali riallineati),
  poi APPROVATO. Il pacchetto 1.2.0 si può costruire (quando il server è libero dalle VM di Debian).

## PIANO — SITO: la parte di Fedora (25 nov; preparazione in locale, pubblicazione SOLO su ordine del proprietario)

**Obiettivo.** Aggiungere Fedora 45 al sito https://remotix.nicfio.it senza cambiare ciò che dice di Debian e Ubuntu
(che restano alla 1.0.1 finché non esce la loro 1.2.0).
**Stato di partenza.** Il sito non ha sorgenti in locale: le pagine vive (`index.html`, `debian13.html`,
`ubuntu2604.html`, `docs.html`, `docs/*`, `download/*`) sono state copiate oggi, in sola lettura, in
`~/remotix-1.2.0-fedora/sito-prima/` (copia di sicurezza: non si tocca).
**Passi.** (1) In `~/remotix-1.2.0-fedora/sito-nuovo/`: pagina nuova `fedora45.html` sul modello di `ubuntu2604.html`
(installazione con dnf, «What Fedora 45 needs» con i requisiti in primo piano: scheda che codifica, RPM Fusion,
firewalld, SELinux; «What was tried … and what was not» con i soli fatti di PIANO/registro; storia «1.2.0»);
`index.html` e `docs.html` con Fedora accanto a Debian e Ubuntu (testi, scheda della distribuzione, menu, manuali);
i due manuali come `docs/user-manual-fedora45.html` e `docs/technical-manual-fedora45.html`. (2) Pacchetto 1.2.0 in
`download/` e la sua impronta SHA-256 nella pagina (dopo la costruzione). (3) Revisore sulle pagine. (4) Il
proprietario le guarda in locale. (5) Su suo ordine: copia sul server web e controllo da fuori (curl + sha256).
Anche il rilascio su GitHub (`fedora45-1.2.0`) e il commit di `fedora45/` solo su suo ordine.
**Rischi.** Scrivere sul sito cose non provate (per questo: solo fatti del registro); rompere le pagine di Debian e
Ubuntu (per questo: confronto riga per riga col prima, modifiche minime); dati personali nei file (controllo prima
di pubblicare, come alla 1.0.0).
**Fatto quando.** Le pagine nuove sono in `sito-nuovo/`, il revisore le ha approvate, il proprietario le ha viste.
- 25 nov sera, SITO preparato in locale (`~/remotix-1.2.0-fedora/sito-nuovo/`): `fedora45.html` nuova, Fedora
  aggiunto in `index.html` (terza scheda; 3 colonne da 1200px, 2 da 900px) e `docs.html`, voce di menu in
  `debian13.html` e `ubuntu2604.html`; i due manuali in `docs/*-fedora45.html`. Revisore: quattro rilievi (avvertenza
  `--allowerasing` per Intel, più schede provate dalle quattro live, tempo di GNOME misurato su VM, colonne), corretti,
  poi APPROVATO. Mancano: impronta SHA-256 al posto di `@@SHA256_FEDORA@@` e il file rpm in `download/` (dopo il
  pacchetto 1.2.0); scelta del proprietario sul logo di Fedora nella scheda (oggi un disegno: anello con «f»);
  la sua occhiata alle pagine; pubblicazione solo su suo ordine.
- 25 nov sera, BANCO DI DEBIAN preparato (ordine del proprietario): quattro VM Debian 13.8 (gnome, kde, xfce, lxqt) in
  `/media/REMOTIX-DEBIAN/vm-radeon/`, pulite (nessun REMOTIX), istantanea `pulito`, spente; script nuovi
  `../debian13/server/vm-radeon.sh`, `prepara-server-vm.sh`, scheda `VM-BANCO.md` (porte ssh 2361-2364, REMOTIX
  8861-8864; utenti prova/prova2). Versioni: kernel 6.12, systemd 257, GNOME 48.7 (gdm3), Plasma 6.3.6 (sddm), XFCE
  4.20 (lightdm), LXQt 2.1.1 (sddm); labwc 0.8.3 nei repository. Verificate: avvio, avvio con la Radeon, accesso
  locale (in modo virtuale), rete. Anomalie annotate: su GNOME con la Radeon senza monitor il sistema resta «starting»
  (plymouth aspetta il greeter); lxqt creata con una versione precedente dello script. Revisore sullo script: in corso.
  Pacchetto Fedora 1.2.0: in costruzione e prova di installazione sulla VM `kde`.
- 25 nov sera, PACCHETTO 1.2.0 costruito: `/media/REMOTIX-FEDORA/pacchetti/v1.2.0/remotix-1.2.0-1.fc45.x86_64.rpm`,
  sha256 6c31e3e881c5d2cac4cbb138a622a48ace5a5a56fbbc225ac5f7b1657f8b738e (copia sul tablet in
  `~/remotix-1.2.0-fedora/pacchetto/`). Rispetto a i2 cambiano 4 file (il programma: solo i testi dei messaggi; il
  programma del gancio `remotix-local-login`: differenza NON guardata riga per riga; le due licenze); modulo SELinux
  identico; stessi 36 percorsi. Non firmato: `sudo dnf install ./…rpm` riesce senza opzioni (solo un avviso di dnf).
  Sulla VM `kde` (enforcing): installazione pulita come da manuale OK (firewall, servizio, porta TCP+UDP, codifica
  hardware, pagina 200), un accesso remoto OK, P8 PASS (forzata a 5,03 s, gancio a 5,9 s), aggiornamento da i2 OK
  (servizio e gancio restano), rimozione: non resta nulla tranne la regola firewalld aggiunta dall'amministratore
  (il manuale lo dice già). Istantanea `kde-1.2.0-provato`. NON provato su GNOME/XFCE/LXQt né su macchina vera.
  Manuali e pagina del sito aggiornati su questo punto; impronta nella pagina `fedora45.html`; `server/live-installa.sh`
  ora punta al file 1.2.0 (la copia sul server `/media/fedora_install.sh` è ancora quella vecchia: non toccata).
- 25 nov notte, indicazione del proprietario sui siti dei progetti: niente problemi incontrati, solo le novità delle
  release. Dalla pagina locale `fedora45.html` tolta la sezione «What was tried on Fedora 45, and what was not» (e la
  sua voce di menu); la versione di prima è in `~/remotix-1.2.0-fedora/fedora45-con-sezione-prove.html`. Quel
  materiale resta nei manuali. Le pagine VIVE di Debian e Ubuntu hanno la stessa sezione: chiesto al proprietario se
  toglierla anche lì. Il sito non è ancora pubblicato (serve il suo sì e la scelta del logo).

## PIANO — SITO RIFATTO: solo le novità delle versioni (25 nov notte; ordine del proprietario)

**Regola (parole sue).** «I problemi dello sviluppo stanno su github. Sul sito solo le novità delle varie versioni.»
Vale per tutte le pagine: «gli stessi problemi sono presenti anche nelle versioni debian e ubuntu. Il sito va rifatto».
**Che cosa si fa** (solo contenuti: aspetto e impianto restano), in `~/remotix-1.2.0-fedora/sito-nuovo/`, secondo
l'inventario `~/remotix-1.2.0-fedora/sito-inventario-problemi.md` (80 passi trovati: Debian 27, Ubuntu 25, Fedora 11,
pagina iniziale 17, documenti 0):
1. Via le sezioni «What was tried on … and what was not» (Debian, Ubuntu; Fedora già fatto) e «Measurements» (Debian).
2. Via le frasi sparse «non provato», «non verificato», prove e cautele nelle sezioni di installazione e requisiti.
3. Stessa struttura per le tre pagine delle distribuzioni: Install · What it needs · Manuals · Changes.
4. «Changes» come elenco di novità per versione (Debian 1.0.0, 1.0.1; Ubuntu 1.0.0, 1.0.1; Fedora 1.2.0).
5. Pagina iniziale: tabella dei browser e note senza «tried/not tested»; resto come da decisioni qui sotto.
Resta ciò che serve a chi installa (scheda che codifica, porta, driver, comandi). Poi revisore, occhiata del
proprietario, pubblicazione solo sul suo sì.
**Decisioni chieste al proprietario** (con la mia raccomandazione): sezione «Limits, on purpose» e paragrafi «What it
deliberately does not do»; limiti per distribuzione (sfondo di XFCE, portachiavi, pkexec); browser non supportati;
NVIDIA; «up to 8 users». Finché non risponde, questi punti restano com'erano nelle pagine di lavoro.
- 25 nov notte, NVIDIA (rilievo del proprietario: «chi ha detto che nvidia non è mai stata provata? … Vulkan è una
  libreria universale»): aveva ragione. Nel codice ci sono misure `[M]` su una RTX 4090 (driver 595) del 5-6 ott 2026,
  Ubuntu 26.04, GNOME 50 e XFCE/labwc; la frase «mai provata» veniva da SPECS/DECISIONS del 1° ott, mai aggiornate, ed
  era finita su sito e manuali. Vulkan Video è la strada generale scelta per capacità (su Fedora la usa anche la
  Radeon). Corretti: sito in locale (4 frasi → «Intel, AMD e NVIDIA, NVIDIA col driver proprietario») e manuali di
  Fedora (15 frasi; «non riprovata su Fedora 45, misurata su Ubuntu il 5-6 ott»), `--check` verde, copie nel sito
  locale aggiornate. DA FARE con la 1.2.0: stessa correzione nei manuali di Debian e Ubuntu e in `docs/SPECS.md`.
  Lezione: una frase «mai provato» ereditata va verificata sulle misure del codice prima di ripeterla.
- 25 nov notte, sito in locale: tolti i riferimenti a «8 utenti» e «3K» (decisione del proprietario: sono misure
  fatte sul suo server, non limiti del prodotto; con una macchina più grande crescerebbero). Via la riga «Supported
  limits» dalle tre pagine e «Up to 8» dalla pagina iniziale. Nei manuali NON toccato (lì c'è scritto altrove: da
  chiedere se vuole la stessa cosa).
- 25 nov notte, SITO RIFATTO in locale secondo le decisioni del proprietario: via ciò che REMOTIX non fa («Limits, on
  purpose» e paragrafi nelle tre pagine), via 8 utenti e 3K, NVIDIA corretta, logo ufficiale di Fedora (Simple Icons)
  nella scheda; tre pagine con la stessa struttura (Install · What it needs · Manuals · Changes). Manuali di Fedora:
  tolti 8 utenti/3K come «limiti dichiarati» (restano tetto di 10 sessioni `--session-cap` e tela massima 4096×2304,
  letti nel codice), `--check` verde. Revisore sul sito: regola rispettata, nessuna affermazione falsa, due ritocchi
  minori (voce «Easy update» fuori dalle novità della 1.0.1; frase ripetuta su Fedora) applicati. Copia delle pagine
  prima della pulizia: `~/remotix-1.2.0-fedora/sito-nuovo-prima-della-pulizia/`. Manca solo il sì del proprietario
  a pubblicare (sito; poi rilascio GitHub e commit, su suo ordine).
- 25 nov, 21:43 — SITO PUBBLICATO su ordine del proprietario («procedi»): https://remotix.nicfio.it con Fedora 45
  (pagina `fedora45.html`, scheda e testi nell'indice, manuali in `docs/*-fedora45.html`, pacchetto
  `download/remotix-1.2.0-1.fc45.x86_64.rpm`) e tutte le pagine rifatte con la regola «solo le novità delle versioni».
  Controllo da fuori: otto file 200 e identici ai locali; impronta del pacchetto scaricato = 6c31e3e8…7f8b738e; i
  file di Debian e Ubuntu (manuali, pacchetti 1.0.1, sorgente di labwc) rispondono ancora. Prima di caricare: tolti
  dal manuale tecnico l'indirizzo interno del server e i dettagli della postazione di lavoro (tablet, percorsi di
  home, l'episodio della tastiera), come nel commit c96b03b. Le pagine vive di prima sono in
  `~/remotix-1.2.0-fedora/sito-prima/` (per tornare indietro: ricopiarle sul server).
  NON fatto (serve un suo ordine): rilascio GitHub `fedora45-1.2.0`, commit di `fedora45/` e dei file nuovi.
  Il repository pubblico NON contiene ancora Fedora: la pagina dei documenti/licenza rimanda a GitHub.
