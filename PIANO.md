# PIANO — REMOTIX per Ubuntu 26.04

Scritto il 18 nov 2026. Stato: **in attesa dell'OK del proprietario**. Nulla è stato ancora toccato.

## Obiettivo
REMOTIX funzionante su Ubuntu 26.04 nei quattro «gusti»: Ubuntu (GNOME), Kubuntu (KDE), Xubuntu (XFCE),
Lubuntu (LXQt), con lo stesso comportamento della 1.0.0 per Debian 13. Il codice è solo per Ubuntu, separato
da quello Debian, che non viene toccato.

## Da dove si parte
- Base: il codice Debian 1.0.0 (`~/Documenti/REMOTIX-DEBIAN`), copiato in questa cartella.
- Il vecchio albero (`~/Documenti/REMOTIX`) resta in sola lettura. Da lì si riprendono, uno alla volta e
  controllati, solo i pezzi tolti il 17 nov perché inutili su Debian e che su Ubuntu avevano già funzionato
  (elenco in `docs/PULIZIA-tranche1.md` dell'albero Debian). Niente meccanismi multi-distro.
- Studio del 18 nov: pacchetto `.deb`, aggancio al login (`pam-auth-update`) e AppArmor restano come su Debian.

## Regole (le stesse del lavoro su Debian)
- Il codice lo scrivono agenti Sonnet; il controllo finale di ogni pezzo è del revisore.
- Come e quando fare le prove lo decide il proprietario: ogni giro parte solo dopo il suo OK.
- Prima si misura, poi si corregge: il giro completo deve funzionare prima di toccare il prodotto.
- A ogni problema chiuso o rimandato: una voce nel registro dei problemi.
- Niente sito, manuali, pubblicazione finché il prodotto non funziona.

## Passi
0. **Preparazione.** Questa cartella riceve la copia del codice Debian, su un ramo git separato
   (`ubuntu-26.04`) dello stesso repo; non si pubblica nulla. Sul server: ambiente di costruzione Ubuntu 26.04
   e quattro macchine di prova (una per gusto), ciascuna con la sua schermata di accesso vera.
   Fatto quando: le quattro macchine di prova partono e il desktop locale di ciascuna è quello giusto.
1. **Il pacchetto.** Si costruisce il `.deb` per Ubuntu 26.04 con il codice com'è, sistemando solo nomi e
   dipendenze dei pacchetti.
   Fatto quando: `apt install ./remotix_….deb` riesce sulle quattro macchine pulite.
2. **Misura iniziale.** Giro completo di prove sui quattro gusti, senza correggere nulla. Ne esce l'elenco
   preciso di ciò che non va.
   **Punto di decisione (KDE):** si vede se su Kubuntu le finestre si aggiornano con i componenti di Ubuntu
   o se serve di nuovo il nostro componente modificato (vedi «Decisioni»).
3. **Correzioni.** Già previste dallo studio:
   - a. GNOME 50: avvio del desktop (su Debian c'è GNOME 48, il modo di avviarlo è cambiato).
   - b. Riconoscere i quattro gusti e scegliere la sessione giusta (su Ubuntu quella con la barra di Ubuntu).
   - c. Il desktop remoto deve trovare le stesse cartelle di impostazioni di un accesso locale
        (Xubuntu e Lubuntu ne hanno di proprie).
   - d. KDE: aggiornamento delle finestre, secondo l'esito del passo 2.
   - e. Nome utente inesistente: stessa risposta e stesso tempo di una password sbagliata.
   - f. XFCE: pannello e programmi rimasti dopo l'uscita, se si ripresentano.
   I punti a, b, c toccano lo stesso file e vanno in sequenza; d può andare in parallelo.
   Fatto quando: su ogni gusto, dal browser, password → desktop giusto, mouse, tastiera, audio, appunti, uscita.
4. **Giro completo di conferma** sui quattro gusti, confrontato riga per riga con quello del passo 2 e con
   l'ultimo giro Debian: nessuna riga non verde che non sia spiegata.
5. **Prove su macchina vera** (del proprietario), con le quattro immagini «live» ufficiali:
   il locale esclude il remoto, riavvio del servizio e poi accesso locale, installazione e rimozione,
   AppArmor in modalità severa.
6. **Chiusura.** Registro dei problemi aggiornato, manuale scritto dal codice Ubuntu, pacchetto definitivo.
   Rilascio e sito solo su decisione del proprietario.

## Dopo lo studio (18 nov 2026, sera) — che cosa cambia nei passi
Otto studi in `studio/` (1–8), fatti sui pacchetti e sui sorgenti veri di Ubuntu 26.04.1. Verifica a campione fatta.
Proposta di revisione, in attesa dell'OK del proprietario:

- **Passo 1 (pacchetto):** nessun ostacolo trovato. Tutti i pacchetti necessari esistono con lo stesso nome; alcuni
  stanno nell'archivio «universe» di Ubuntu. Il nostro componente per KDE entra subito nella costruzione (vedi sotto).
- **Passo 2 (misura):** così com'è, il codice Debian su Ubuntu **non apre GNOME** (si ferma con un rifiuto pulito) e
  su Xubuntu sceglie il desktop sbagliato. Quindi la misura iniziale ha senso solo dopo le correzioni 3a e 3b.
  Nuovo ordine: 0 → 1 → 3a, 3b, 3d → misura (2) → resto del 3 → conferma (4).
- **Passo 3, correzioni (con il peso e se la cura è già nota dalla 1.5):**
  - a. GNOME 50, avvio: il modo di avviare il desktop è cambiato. Medio, cura nota. In più un controllo nuovo:
       GNOME 50 rifiuta di partire se un'altra sessione grafica dello stesso utente non è ancora chiusa del tutto. Piccolo, nuovo.
  - b. Riconoscere i quattro gusti (oggi Xubuntu verrebbe scambiato per GNOME) e scegliere la sessione «Ubuntu». Piccolo, cura nota.
  - c. Stesse impostazioni dell'accesso locale: cartelle di Ubuntu, Xubuntu, Lubuntu; programmi snap raggiungibili
       (`/snap/bin`); tre variabili di Xubuntu. Medio, cura nota in parte; per GNOME il meccanismo vero è diverso da
       quello che la 1.5 presumeva.
  - d. KDE: rimettere il nostro componente modificato (certezza 90–95% che serva: quello di Ubuntu è la stessa
       versione senza la correzione, e gli autori non l'hanno sistemato). Medio, cura nota e già provata su 26.04.
       Con esso: testi delle licenze da correggere e sorgenti da pubblicare.
  - e. ~~Nome utente inesistente~~: la cura è già nel codice 1.0.0 (verificato). Resta solo la prova.
  - f. XFCE: voce del menu persa dal pannello dopo una chiusura. Mai curato, causa non ancora trovata; su Xubuntu
       conta di più perché da quel menu passa il blocco di «spegni/riavvia». Medio-grande, da riprodurre.
  - g. Sistema (nuovo, tutto piccolo): avviso falso nel registro (Ubuntu tiene viva la sessione in un altro modo);
       impedire che un aggiornamento automatico di sistema riavvii REMOTIX chiudendo i desktop; due percorsi da
       aggiungere alle protezioni AppArmor; una chiave di blocco schermo propria di Ubuntu.
  - h. Prove (nuovo, piccolo): tre controlli che presumono Debian (messaggio di `sudo`, nome del terminale,
       percorsi); la macchina virtuale di prova non ha scheda video e il pacchetto la rifiuta.
- **Da vedere solo provando:** ridimensionamento della finestra su GNOME 50; Firefox e gli altri snap dentro la
  sessione remota (mai provati); portafoglio delle password di KDE e portachiavi di GNOME; uscita da KDE;
  schermata di accesso di GNOME 50 con un desktop remoto aperto, compreso il nuovo pulsante «Force Stop», che ora
  chiude anche il desktop remoto; AppArmor in modalità severa (serve una Ubuntu vera, non un contenitore).
- **Macchine di prova:** Xubuntu va costruita con un accorgimento (altrimenti nasce con la schermata di accesso di
  GNOME); circa 70 GB in tutto sul server, 20–25 minuti per macchina.

## Decisioni del proprietario dopo lo studio (18 nov 2026, sera)
- Revisione dei passi approvata: prima le quattro macchine di prova sul server, poi un agente per ciascun punto.
- A. **Repo unico, una sottocartella per distro.** Il riordino (Debian in una sua cartella) si fa al rilascio di
  Ubuntu; fino ad allora si lavora sul ramo `ubuntu-26.04`, non pubblicato.
- B. File di avvio personali dell'utente (`~/.profile`): **prima si studia che cosa accade, poi si decide.**
- C. Portafoglio di KDE / portachiavi di GNOME: **prima si studia che cosa accade, poi si decide.**
- D. **REMOTIX non supporta macchine con più desktop installati**: nessun lavoro per seguire la scelta fatta alla
  schermata di accesso.
- E. **Nessuna segnalazione agli autori di KDE o dei componenti**: non è compito nostro.

## Avanzamento
- 18 nov, sera: ramo `ubuntu-26.04` creato in questa cartella (copia del codice Debian 1.0.0).
- **Costruzione — fatto, APPROVATO dal revisore.** `remotix_1.0.0-1+ubuntu26.04_amd64.deb` si costruisce sul server
  (`/media/REMOTIX-UBUNTU/pacchetti/base/`), lintian 0/0, dipendenze risolte in simulazione, costruzione riproducibile.
- **Macchine di prova — fatte, APPROVATE.** `rxu-gnome|kde|xfce|lxqt` (ssh 2221-2224, REMOTIX 8821-8824), accese;
  comandi: `/media/REMOTIX-UBUNTU/albero/boxes/box.sh`. Girano sotto podman di root (`podman ps` da utente non le mostra).
  Nei box il gestore di accesso è registrato ma non acceso; snapd c'è ma è fermo (gli snap si provano solo su macchina vera).
  Tre unità falliscono in ogni box e sono attese: `netplan-configure.service`, `tpm-udev.path`, `tpm-udev.service`.
- **Strumenti di prova adattati — fatto, APPROVATO**, già in questo albero.
- **Diagnosi del menu XFCE perso — fatta** (`studio/9-…`): causa probabile all'80% nel modo in cui REMOTIX scrive il blocco.
- **I cinque punti di sviluppo — fatti, tutti APPROVATI dal revisore e riuniti in questo albero (18 nov, sera):**
  `sistema` (1 giro), `xfce-pannello` (2), `gusti-ambiente` (3), `kde` (2), `gnome-avvio` (3). Script di preparazione
  del server adattato e approvato (non eseguito). Ritocchi finali del coordinatore approvati; fusione di `session.c`
  verificata dal revisore byte per byte.
- **Pacchetto unico costruito** (server: `/media/REMOTIX-UBUNTU/pacchetti/unione/`, albero in `/media/REMOTIX-UBUNTU/unione/albero`):
  `remotix_1.0.0-1+ubuntu26.04_amd64.deb`, SHA-256 `2c473ac9…cb3d`; tutti i controlli SI, costruzione riproducibile
  (pacchetto e archivio dei sorgenti del componente KDE), lintian 0/0, avvisi del compilatore: solo i 4 già presenti
  nella base più 2 nei sorgenti altrui del componente. Verificato dal coordinatore sui registri.
- **KDE: necessità del nostro componente DIMOSTRATA** (`studio/10-kde-controprova-labwc.md`): con il componente di Ubuntu
  0 fotogrammi «mostrati» su 755, Firefox fermo; con il nostro 759 su 760, Firefox vivo. Il terminale di KDE si aggiorna
  in entrambi i casi (per questo una prima controprova aveva ingannato).
- Visto dal vivo dai singoli agenti, ciascuno sul SUO pacchetto e sulla SUA macchina (non ancora sul pacchetto unico):
  controllo base 5/5 sui quattro gusti; GNOME: uscita in 0,17–0,29 s, rientro in 6–7 s, rifiuto di una seconda sessione
  osservato; Xubuntu e Lubuntu: desktop e cartelle giuste; Kubuntu: Plasma nel nostro componente.
- **Prossimo passo: giro di misura completo sulle quattro macchine con il pacchetto unico — attende il via del proprietario.**
  Da guardare in quel giro (elenchi dei revisori): GNOME cartelle `ubuntu`/`gnome` e chiavi bloccate; rifiuto→attesa→nascita;
  XFCE punti a–f della cura del pannello; KDE ridimensionamento al riaggancio, ripiego senza componente, nessun residuo
  dopo l'uscita; sessione che resta attiva (systemd 259); XFCE/LXQt ancora sul `labwc` di Ubuntu.
- **Giro di misura «unione1» — fatto (18 nov, sera), via dato dal proprietario.** Rapporti: `studio/giro1-<de>.md`; registri sul
  server in `/media/REMOTIX-UBUNTU/albero/prove/log/unione1-<de>/`. Righe verdi: Ubuntu 116/124, Kubuntu 111/124, Xubuntu
  117/124, Lubuntu 117/124; nessun controllo bloccato.
  - Non verdi già note da Debian: pulsanti Ctrl+Alt+Canc/Fine (prove da allineare, decisione del proprietario); `pkexec` su GNOME.
  - Non verdi nuove, uguali sui quattro: `mouse-drag` (Chrome, Firefox) e `phone/tap-and-half-drag-select`: lo strumento di prova
    non registra il «rilascio» (GTK4 di Ubuntu), la selezione avviene. Probabile difetto della prova, DA DIMOSTRARE.
  - **Difetti veri trovati:** (1) KDE: un Log Out chiesto nei primi secondi di vita del desktop si perde e la forzatura non
    scatta (restano 42 processi, client non avvisato); dopo un minuto funziona. (2) Lubuntu: finestra di errore «X Compositor
    crashed too many times» al centro del desktop (picom, solo X11, rilanciato da LXQt). 
  - Da chiarire: KDE `media/codec` con Firefox (bordo di 130 px, non rieseguito); KDE `reattach-windows-inside` (probabile
    difetto della prova).
  - Confermato dal vivo: cura del menu XFCE (tutti i punti); sfondo di Xubuntu non nero; desktop e cartelle giuste sui quattro;
    sessione attiva senza falso avviso; GNOME rifiuto→attesa→nascita da sola (client con schermo vuoto per circa 27 s);
    KDE nostro componente in uso, ridimensionamento al riaggancio, ripiego dichiarato; nessuna finestra di KWallet.
  - Non osservabile nei contenitori: confronto con un accesso locale vero, schermate di accesso, snap dentro la sessione,
    AppArmor severo, needrestart: restano alle prove su macchina vera (passo 5).
- **Tre correzioni dopo il giro di misura — fatte, APPROVATE dal revisore e riunite (18 nov, notte):**
  (1) KDE, uscita nei primi secondi: REMOTIX aspetta che KDE abbia finito di chiedere conferme, gli chiede se sta davvero
  chiudendo e solo allora completa la chiusura; mai con lavoro non salvato aperto; tetto di circa un minuto, poi chiusura
  forzata con la strada esistente (3 giri di revisione: il primo rimedio avrebbe chiuso con un documento non salvato aperto).
  (2) Lubuntu: i gestori di effetti per il vecchio sistema grafico non partono nella sessione remota (lista di ruolo in un
  punto solo, accettata dal revisore). (3) Strumenti di prova: rilascio nel trascinamento (era lo strumento, dimostrato),
  controlli dei pulsanti tolti ad agosto allineati (deciso dal proprietario), misura della finestra nel riattacco.
  Copie di lavoro: `~/Documenti/REMOTIX-UBUNTU-lavori2/`.
- **Pacchetto finale costruito**: server `/media/REMOTIX-UBUNTU/pacchetti/unione2/`, SHA-256 `5bfc4da6…c54b`; controlli tutti
  SI, riproducibile, lintian 0/0, avvisi del compilatore: i 6 noti (verificato dal coordinatore).
- **Giro di conferma «unione2» — in corso** sulle quattro macchine (lanciato su indicazione del proprietario: «quando sei
  pronto passiamo ai test sui container»); quattro agenti lo seguono, rapporti attesi in `studio/giro2-<de>.md`. In più:
  osservazioni per le decisioni rimandate (portachiavi di GNOME, snap dentro la sessione, regolazioni di Xubuntu).
- **Decisione del proprietario (18 nov, notte): portachiavi e Xubuntu (XFCE) si allineano al comportamento dei rispettivi
  desktop su Debian.** Quindi: nessuna funzione nuova per il portachiavi di GNOME (vale la regola già in uso: nessuna finestra
  di password non richiesta nel remoto); le tre regolazioni di `56xubuntu-session` NON si riproducono nel remoto (la
  differenza dall'accesso locale si dichiara nel manuale). Restano solo da accertare i fatti su Ubuntu nel giro di conferma.
- **Mandato per la notte (proprietario, 18 nov, sera):** a giro «unione2» finito e quadro chiaro, si attua da soli il piano di
  correzione dei difetti emersi (un agente per difetto, revisore per ogni modifica) e poi si lancia un nuovo giro completo per
  confermare; senza altri via. Limiti che mi do: nessuna pubblicazione, nessun commit, nulla di cancellato; ciò che è una
  scelta di prodotto nuova non si decide: si annota per il mattino con le opzioni, seguendo nel dubbio «come su Debian».
- Lezioni di metodo di oggi (da portare nel registro dei problemi): (1) installare nelle macchine di prova un pacchetto con
  la stessa versione non sostituiva il programma (corretto in `boxes/box.sh`; resta da aggiungere il confronto dopo
  l'installazione); (2) «0 avvisi» va letto nel registro, non creduto al rapporto: un ritocco aveva spento una protezione e
  il compilatore l'aveva detto; (3) una controprova con il programma sbagliato (terminale) può smentire a torto.
- Da fare prima del rilascio: data di costruzione giusta (i pacchetti di prova di oggi, tranne quello unico, portano il
  2025); ripulire i testi di licenza dai resti della 1.5 (Go, `.run`, `remotix-install`).
- Decisioni rimandate a dopo l'osservazione sulle macchine: file di avvio personali e script di sistema dell'accesso
  locale (comprese le tre variabili di Xubuntu); portafoglio di KDE e portachiavi di GNOME.

## File interessati
`src/session.c`, `src/session.h` (a, b, c); `src/kwin.c`, `src/Makefile`, `debian/rules` (d);
`src/rootside.c` (e); `debian/control`, `build/Containerfile`, `build/build-deb.sh` (pacchetto);
`boxes/` (macchine di prova con `apt` di Ubuntu e i quattro gusti); `prove/` solo dove nominano Debian.

## Decisioni del proprietario (18 nov 2026)
1. **KDE, componente nostro: sì**, se la misura del passo 2 lo richiede (costruzione più lunga, sorgenti da
   pubblicare per la licenza GPL).
2. **Numero di versione: 1.0.0 per tutte le distro.** Pacchetto `remotix_1.0.0-1+ubuntu26.04_amd64.deb`.
3. **Prove: sì** a due giri completi (passi 2 e 4) più le prove su live del passo 5; ogni giro parte al suo via.
4. **Prima di scrivere codice: studio a fondo di GNOME e di Ubuntu** (in corso dal 18 nov: otto agenti,
   documenti in `studio/`, regole in `studio/00-REGOLE-studio.md`). I passi qui sopra si rivedono dopo lo studio.
5. **Repo unico o uno per distro:** da decidere (proposta: repo unico, una cartella per distro).

## Rischi
- KDE è il punto più pesante e meno certo: da solo può valere metà del lavoro.
- GNOME 50 è la parte più delicata del prodotto (nascita e chiusura della sessione).
- Due codici separati: una correzione che vale per entrambi andrà fatta due volte (Debian e Ubuntu).
- AppArmor su Ubuntu è più severo che su Debian e non è mai stato provato in modalità severa.
- Il server è stato azzerato il 18 nov: le macchine di prova vanno ricostruite da zero.

## Stima
2–3 settimane (a giudizio, non misurata). Passi 0–2: 2–3 giorni.

## Fatto quando
Sui quattro gusti: giro completo senza righe inspiegate, le quattro prove su live riuscite, registro aggiornato.

## Nota per dopo (18 nov 2026)
Ordine delle distro successive: Fedora 44, poi Arch. Arch non ha un'immagine «live» con desktop già
pronto: andrà costruita quando servirà per le prove su macchina vera.

### Giro `unione2` — esito (18 nov, 21:20) e fase di verifica delle voci scoperte

- Esito: gnome 123/124 (resta solo `users-shell-and-environment`, pkexec, voluto così), kde 121/124, xfce 126/128, lxqt 124/124. Nessuna regressione vera. Rapporti: `studio/giro2-<de>.md`.
- Confermate chiuse: uscita KDE presto (`lifecycle/logout`, `settings-intact`), finestra picom su Lubuntu, trascinamento (strumento), pulsanti tolti, `reattach-windows-inside`.
- Ancora aperte dal giro: KDE Ctrl+Alt+Canc non apre la schermata di uscita (`page-cad-chain`, era così anche in unione1); KDE `canvas-limits` fallito una volta (non riprodotto); XFCE finestra «internal error» di apport per il crash di `blueman-applet` (3 su ~30 sessioni: copre la finestra di prova); Lubuntu finestra «Lubuntu Update crashed too many times» vista su un utente, non riprodotta; XFCE Log Out a sessione STACCATA lascia il processo remotix vivo e il rientro trova una sessione senza desktop; GNOME notifica «Screen Lock disabled» alla nascita.
- Riscontro studi↔lavoro: `studio/11-riscontro-studi-lavoro.md` (27 voci scoperte, 4 di rischio alto).
- In corso (21:30–): quattro agenti di verifica, uno per box, su queste voci e sulle scoperte (uscita nei primi secondi, rientro subito dopo l'uscita, uscita a sessione staccata, `check-package.py`, inattività 20 min, linger, portafoglio KDE). Rapporti attesi: `studio/12-verifiche-<de>.md`. Poi: piano di correzione → programmatori → revisore → pacchetto `unione3` → giro `unione3`.
- Controllo periodico portato a 15 minuti su richiesta dell'utente.

### Notte 18→19 nov — verifiche, correzioni e stato (aggiornato 02:55)

Verifiche (rapporti `studio/12-verifiche-<de>.md`, `studio/13-riunito-xfce-lxqt.md`) → difetti trovati e loro stato:

| Difetto | Desktop | Stato |
|---|---|---|
| Log Out a sessione staccata: il processo resta vivo, il login seguente va a vuoto (c'è anche nel codice Debian 1.0.0) | XFCE, LXQt | corretto, approvato, RIUNITO (`input_dropped()`, `really_terminate()` con prova doppia) |
| idem | KDE | corretto e approvato («KWIN IS GONE» spostato), in attesa di riunione con il resto del lavoro KDE |
| Allarme falso «machine can be powered off» con risposta `na` di logind | tutti | corretto, RIUNITO (gli errori restano allarme, ora nominati) |
| Finestra «Lubuntu Update crashed too many times» con più utenti | LXQt | corretto, approvato, RIUNITO (non avviato in sessione remota, come picom) |
| labwc assente (`--no-install-recommends`): nero senza messaggio | XFCE, LXQt | corretto, RIUNITO (rifiuto con messaggio generico + riga di registro che nomina il pacchetto + avviso in postinst) |
| Falso «session has ended» a chi rientra mentre la sessione chiude | tutti | corretto (codice scritto dalla sessione principale: `wt_dismiss_user_session_over()`), approvato, RIUNITO |
| Notifica «Screen Lock disabled» alla prima sessione | GNOME | corretto, RIUNITO |
| Variabili rimaste nel gestore utente con linger | GNOME | corretto, RIUNITO |
| Uscita di una sessione giovane: pagina ferma ~17 s se RealtimeKit non parte (contenitori, VPS) | tutti | in correzione (`lavori4/chiusura-avviso`: avviso al genitore prima dello smontaggio audio/video) |
| Ctrl+Alt+Canc non apre la schermata di uscita | KDE | in correzione, secondo giro (servizio `org.freedesktop.ScreenSaver` nostro; `Inhibit`/`Lock` → errore standard) |
| Finestra che resta a metà animazione (ultimo fotogramma non arrivato finché nulla si muove) | KDE | DIAGNOSI in corso — difetto vero del prodotto, trovato dal revisore dietro il falso FAIL di `canvas-limits` |

Pacchetto intermedio `pacchetti/unione3a` (sha `f7ff0294…`, 6 avvisi, lintian 0/0, riproducibile): provato su xfce e lxqt, tutto PASS.

Da scrivere nel registro problemi / da decidere al mattino (NON curati stanotte):
- `terminate_in_child` e `abandon_expired` (main.c) mandano 0x10/0x03 subito anche a chi aspetta PAM (rompe il secondo fisso, rivela l'account): cura naturale `wt_dismiss_user_session_over()`, con prove proprie.
- Sconosciuto con password sbagliata riceve 0x0F «slot occupato» se il titolare è attaccato (rivela l'account): tema §4.4.
- `scaling-factor=2` su GNOME: sessione rifiutata ma l'utente vede nero senza messaggio (uguale su Debian); serve un piano suo.
- Xubuntu: finestra apport per il crash di `blueman-applet` (5 su 90 sessioni; non dipende dal remoto): decidere se non avviarlo nella sessione remota.
- XFCE: Log Out nei primi 7 s ignorato dal desktop stesso (non nostro).
- KDE portafoglio: `secret-tool store` fa comparire la finestra di ksecretd e l'app resta bloccata (regola: come su Debian; non verificato su Debian).
- Gestore di sessione fermo (SIGSTOP): la chiusura poggia solo sulla rete di sicurezza lato root (comportamento preesistente).
- Il difetto «Log Out a sessione staccata» c'è anche nel codice Debian 1.0.0 pubblicato: decidere se portare lì la cura.
- `box.sh install` non riavvia il servizio: dopo l'installazione riavviare e verificare lo sha di `/proc/<MainPID>/exe`.

### 19 nov, 04:40 — tutte le correzioni riunite, pacchetto `unione3`, giro di conferma avviato

- Riunite anche: avviso di fine sessione PRIMA dello smontaggio audio/video (GNOME, XFCE, LXQt; KDE escluso in attesa di prova dal vivo: nei contenitori senza RealtimeKit la pagina ora è avvisata in ~6 s invece di 17-20; su XFCE 1,3 → 0,25 s); KDE: Ctrl+Alt+Canc (servizio `org.freedesktop.ScreenSaver` nostro in `kwin.c`, con inoltro di `Inhibit` a powerdevil), Log Out a sessione staccata («KWIN IS GONE» spostato), prova `canvas-limits` resa severa (foto ferma e sbagliata = FAIL).
- Pacchetto finale: `/media/REMOTIX-UBUNTU/pacchetti/unione3/remotix_1.0.0-1+ubuntu26.04_amd64.deb`, SHA-256 `8ff13c0bd88a0ef09191f82f03ba69c385631b1eb0ffbf5cfa9b55790d9bbe38`; 6 avvisi noti, lintian 0/0, riproducibile, nessun controllo NO. Albero: `/media/REMOTIX-UBUNTU/unione3/albero`.
- Giri: `unione3b` (pacchetto intermedio senza le parti KDE) su gnome/xfce/lxqt partito alle 04:10; `unione3-kde` partito alle 04:40; a seguire `unione3` su gnome/xfce/lxqt.
- NUOVO difetto KDE diagnosticato e NON curato (decisione al mattino): finestra appena aperta a sessione giovane che resta a metà animazione per 18-26 s (8 su 19 prove; 0 su 4 a sessione di 70 s). L'ultimo fotogramma non esce dallo screencast di KWin finché non c'è un «danno vero»; nel contenitore lo sblocca plasmashell dopo un'attesa di 25 s (ModemManager che non parte). Conseguenza: `canvas-limits` su KDE può dare FAIL (giusto). Cure possibili: riavvio dello stream dopo ~300 ms di soli buffer-cursore (rischioso: ricrea i dispositivi di input) oppure un piccolo cliente nostro di KWin con superficie di 1 px che produce danno (da misurare). Serve misura fuori dal contenitore e su 20 sessioni calme.
- Altre voci per il registro: KDE escluso dall'avviso anticipato; difesa 3 con nuovo ordine e ramo «canale chiuso con Mutter lento» verificati solo alla lettura; `resilience/clocks` può dare FAIL alla prima esecuzione per colpa dello strumento (la rotazione del journal scarta la riga di avvio che `in_force()` cerca); servizio ScreenSaver KDE: nessun tetto alla tabella dei cookie e caso powerdevil riavviato (raccomandazioni non bloccanti del revisore); Ctrl+Alt+Canc nei primi ~25 s di vita su KDE arriva in ritardo nel contenitore (kded6 aspetta ModemManager): da vedere su macchina vera.

### 19 nov, 06:00 — giro `unione3` e pacchetto definitivo `unione4`

- Giro `unione3` (pacchetto `8ff13c0b…`): kde 124/124, xfce 124/124 (righe tutte PASS), lxqt tutte PASS, gnome 2 righe rosse: `users-shell-and-environment` (pkexec, voluto) e `settings-intact` — il file `lock-warning-shown` creato dalla cura della notifica restava nella home. Curato: il file viene tolto alla fine della sessione se è ancora il nostro (segno in `/run/user/<uid>/remotix/lock-warning-made`), revisore APPROVATO, riunito.
- Pacchetto definitivo della notte: `/media/REMOTIX-UBUNTU/pacchetti/unione4/remotix_1.0.0-1+ubuntu26.04_amd64.deb`, SHA-256 `5c7b1f5baac936e740a09abd7aacc8e82ad999822e0ac41ac4cb6a0ccdbbd0b4`; 6 avvisi noti, lintian 0/0, riproducibile. Albero: `/media/REMOTIX-UBUNTU/unione4/albero` = albero principale locale (nessun commit).
- Giro `unione4` sui quattro box partito alle 06:02 (ora del server). Registri: `albero/prove/log/unione4-<de>/`.

### 19 nov mattina — decisioni del proprietario
- Xubuntu: `blueman-applet` NON va avviato nella sessione remota (OK del proprietario). Da fare appena il box xfce è libero.
- KDE finestra a metà: curare ADESSO (in corso, `lavori6/kde-fotogramma`, agente Fable).
- GNOME scala 2: «sistema» (in corso, `lavori6/gnome-scala`).
- Debian 1.0.0: NESSUNA correzione, nessuna 1.0.1. Il caso «desktop che finisce a browser scollegato» non capita in uso normale (il timeout della sessione abbandonata funziona ed è provato): per il proprietario non è un bug. Argomento chiuso, non riproporlo. L'albero Debian non si tocca.

### 19 nov, 09:15 — SVILUPPO UBUNTU CHIUSO: pacchetto `unione5`

- Riunite e approvate dal revisore le ultime tre: KDE finestra a metà (fotogramma perso dallo screencast: conteggio dei numeri dei buffer di KWin, fotogramma intero dopo un buco, «poke» del nostro pixel se entro 200 ms non arriva nulla; solo KDE); GNOME scala (chiave bloccata a 1 nella sessione remota; scala salvata in monitors.xml riportata a 1 in modo temporaneo; rete di sicurezza con messaggio); Xubuntu/Lubuntu `blueman-applet` non avviato nella sessione remota.
- La riga rossa `canvas-limits` di XFCE nel giro `unione4` era la finestra di apport del crash di blueman che copriva lo schermo (studio/14-canvas-xfce.md): non un difetto di REMOTIX; `audio-firefox` di GNOME rilanciato: PASS.
- Pacchetto: `/media/REMOTIX-UBUNTU/pacchetti/unione5/remotix_1.0.0-1+ubuntu26.04_amd64.deb`, SHA-256 `f588a58fdf430c93dbb787827de7a3ccd93ad5b9dc0cd116dbfa0452925e38d5`; 6 avvisi noti, lintian 0/0, riproducibile, nessun controllo NO. Albero: `/media/REMOTIX-UBUNTU/unione5/albero` = albero principale locale. Nessun commit.
- Da qui il codice è FERMO. Prossimo passo: prove sui container, quando e come decide il proprietario. Il giro completo su `unione5` NON è ancora stato fatto.
- Restano in corso solo le ultime prove dell'agente KDE sul suo pacchetto (check-desktop, canvas-limits, SIGSTOP, stacco).

### 19 nov, 10:45 — giro `unione5` e container pronti per le prove a mano del proprietario
- Giro `unione5` (pacchetto `f588a58f…`): kde, xfce, lxqt tutte le righe PASS; gnome tutte PASS tranne `desktop/users-shell-and-environment` (pkexec, voluto). Registri: `albero/prove/log/unione5-<de>/summary.txt`.
- I quattro container sono stati azzerati con `fresh.sh` e hanno `unione5` installato, servizio attivo, utenti `prova` e `prova2` (password `prova2026`), nessuna sessione. Indirizzi: https://192.168.0.2:8821 gnome, :8822 kde, :8823 xfce, :8824 lxqt. Accesso di controllo fatto con `base-check.py` (5/5 PASS su ciascuno, uno alla volta) e poi nuovo azzeramento.
- Il proprietario ripete le prove a mano dal browser. Codice fermo: non toccare i container né il codice finché non dà indicazioni.

### 19 nov — prove a mano del proprietario (container, pacchetto `unione5`)
- GNOME: OK da Windows, Linux e Android (tablet, DeX, notebook): detach/reattach, audio/video, clipboard, reattach a risoluzioni diverse. Firefox 160 (deb di Mozilla) installato a mano nei quattro container: dopo un azzeramento va rimesso.
- Da provare da parte sua: KDE, XFCE, LXQt.
- KDE: OK (prova a mano del proprietario, 19 nov). Restano XFCE e LXQt.
- XFCE: OK (prova a mano del proprietario, 19 nov). Resta LXQt.
- LXQt: OK. PROVE A MANO SUI CONTAINER CONCLUSE: OK su tutti e 4 i desktop (proprietario, 19 nov). Prossimo passo chiesto: prova su macchina vera con le distro live → serve un installatore da usare nelle live.
- Installatore di prova per le live: `server/live-installa.sh`, servito dal server in `/media/REMOTIX-UBUNTU/live/` sulla porta 8830 (`python3 -m http.server`, da rilanciare dopo un riavvio del server: vedi `LEGGIMI.txt` lì). Comando nella live: `wget -qO- http://192.168.0.2:8830/installa.sh | sudo bash`. Provato sui 4 container, rivisto (corretti: script letto da pipe, lock di apt). Rapporto: `studio/15-installatore-live.md`. NON provato su una live vera.

### 19 nov, pomeriggio — prima prova su macchina vera (live Ubuntu 26.04.1 avviata sul server stesso)
- Ogni accesso rifiutato: una riga del profilo AppArmor vietava tutti i socket locali. Corretta in `debian/remotix_network.apparmor` (due righe con `@**`), misurata sulla live, revisore APPROVATO. Pacchetto `unione5` NON ancora ricostruito. Registro: voce C4.
- Corretto quello, il desktop GNOME si apre. Difetto nuovo: i programmi «snap» di Ubuntu fatti con Flutter non digeriscono il file con cui REMOTIX passa le impostazioni alla sessione remota (`DCONF_PROFILE` in `/run/user/<uid>/remotix/dconf/profile`, con righe `file-db:` e `service-db:`). Installatore della live: finestra «Something went wrong» (`Unknown DConf source`). Firmware Updater e Security Center: `No DConf source to write to` (il recinto snap vieta la lettura del file). App Center: nessun errore di questo tipo. DA CORREGGERE.
- Perché non si era visto: nei container non c'è nessuno snap e AppArmor non agisce.

## PIANO — banco di prova su macchine virtuali con la Radeon (deciso dal proprietario, 19 nov 2026) — IN ATTESA DI OK

**Obiettivo.** Provare REMOTIX su Ubuntu installato davvero (con i suoi programmi snap e le sue protezioni), con il video funzionante, senza installare nulla sul server: macchine virtuali che ricevono la scheda Radeon del server (passthrough).

**Che cosa si sa già (letto oggi dalla live, stesso hardware).** Radeon RX 6800 in un gruppo isolato, la sua uscita audio in un altro: si può cedere a una macchina virtuale. Il server ha anche la grafica Intel integrata, che resta al server. 20 processori logici, 31 GB di memoria, disco NVMe da 1,8 TB in `/media` per i dischi delle macchine.

**Conseguenza da accettare.** La Radeon è una sola: UNA macchina virtuale accesa per volta con il video. I quattro desktop si provano uno dopo l'altro, non insieme. Finché una macchina virtuale ha la Radeon, i container non possono usarla.

**Passi.**
1. Al ritorno del server: controllare che il suo sistema permetta il passthrough (stessa lettura fatta oggi sulla live; se manca un'opzione di avvio, dirlo al proprietario prima di toccare l'avvio del server).
2. Una macchina virtuale di prova con Ubuntu 26.04 (GNOME) installato davvero e la Radeon ceduta; verificare che REMOTIX codifichi il video e che la Radeon torni al server allo spegnimento. Se questo passo non riesce, FERMARSI e riferire.
3. Script unico (`server/vm.sh` esteso) per creare, accendere, spegnere e riportare a zero ciascuna delle quattro macchine (Ubuntu, Kubuntu, Xubuntu, Lubuntu), con un indirizzo fisso per le prove dal browser.
4. Ricostruire il pacchetto con la correzione AppArmor; correggere il difetto delle impostazioni con i programmi snap (piano di dettaglio a parte, dopo le misure sulla macchina virtuale GNOME).
5. Giro automatico e poi prove a mano del proprietario, un desktop per volta. La live su macchina vera resta l'ultimo controllo.

**File.** `server/vm.sh`, `server/prepara-server.sh`, `debian/remotix_network.apparmor` (già fatto), `src/session.c` (impostazioni, passo 4), `docs/REGISTRO-problemi.md`.

**Rischi.** Il sistema del server potrebbe non avere il passthrough attivo all'avvio. Alcune Radeon non si «liberano» bene quando la macchina virtuale si spegne (servirebbe riavviare il server fra una prova e l'altra). Il server vive in memoria: i dischi delle macchine virtuali vanno su `/media` e ogni preparazione deve essere rifacibile da script. Le prove diventano più lente (un desktop per volta, avvio di una macchina intera).

**Fatto quando.** Sulle quattro macchine virtuali: accesso riuscito con AppArmor in vigore, desktop visibile dal browser, App Center / Firmware Updater / Security Center aperti senza errori nella sessione remota (dove esistono), giro automatico verde, prove a mano del proprietario.

### 19 nov, sera — avanzamento del piano «macchine virtuali con la Radeon»
- Piano approvato dal proprietario; server riavviato da lui con `intel_iommu=on iommu=pt vfio-pci.ids=1002:73bf,1002:ab28 modprobe.blacklist=amdgpu`. Deciso: kernel di Ubuntu nella VM (non quello del server); una distro per volta.
- Su suo ordine: cancellati i quattro container `rxu-*` e le loro immagini. Restano le immagini di costruzione del pacchetto.
- Passo 1 FATTO (Radeon libera, IOMMU attivo). Passo 2 FATTO: VM `ubuntu` (Ubuntu 26.04 Desktop installato con autoinstall, kernel 7.0.0-44-generic, solo la Radeon come scheda video) in `/media/REMOTIX-UBUNTU/vm-radeon/ubuntu/`; script `server/vm-radeon.sh crea|accendi|spegni|ssh|stato <nome>`; indirizzo per le prove https://192.168.0.2:8841 (ssh 2341). Verificato: amdgpu, codifica video hardware, AppArmor attivo, snap presenti, «§5.1 CONNECTED», un accesso di prova riuscito, spegnimento e riaccensione senza riavviare il server.
- Nella VM c'è il pacchetto `unione5` con il profilo AppArmor corretto copiato a mano: il pacchetto NON è ancora ricostruito (passo 4). Difetto delle impostazioni con i programmi snap: ancora da correggere (passo 4).
- Prossimo: revisione dello script (in corso), passo 3 (kubuntu, xubuntu, lubuntu), passo 4.
- 19 nov, sera: `server/vm-radeon.sh` revisionato (DA CORREGGERE → corretto → APPROVATO). Pacchetto `unione6` costruito (`/media/REMOTIX-UBUNTU/pacchetti/unione6/`, sha256 `62d26cbb…2421`, albero in `/media/REMOTIX-UBUNTU/unione6/albero`): rispetto a `unione5` cambia solo `/etc/apparmor.d/remotix_network` (più la data del changelog); binario identico, controlli tutti SI, lintian pulito, riproducibile. Copia per le VM: `/media/REMOTIX-UBUNTU/vm-radeon/remotix_1.0.0-1+ubuntu26.04_amd64.unione6.deb`. NON ancora installato in nessuna VM. Nota: `/media/REMOTIX-UBUNTU/albero` sul server non è il sorgente completo (solo boxes, prove, server): il sorgente di ogni costruzione sta in `unioneN/albero`.
- 19 nov, notte — passo 3 FATTO (dischi): VM `xubuntu`, `lubuntu`, `kubuntu` costruite dallo squashfs della ISO (xubuntu: autoinstall fallito per un Oops del kernel live -14; kubuntu e lubuntu hanno Calamares), kernel di Ubuntu dentro il disco (xubuntu e lubuntu 7.0.0-14, kubuntu 7.0.0-30; `ubuntu` 7.0.0-44 aggiornato), verificate con `prova-avvio` (scheda virtuale): schermata di accesso, AppArmor, snap, utenti. Istantanea `pulito` su tutte e tre. NON ancora provate con la Radeon né con REMOTIX. Senza aggiornamenti: in attesa della decisione del proprietario.
- `server/vm-radeon.sh`: quattro giri di revisione, ultimo esito APPROVATO. Comandi: `crea|accendi|spegni|ssh|stato|prova-avvio|istantanea|ripristina <nome>`. Mai provati sul campo: spegnimento/riaccensione con lo script corretto, ramo ACPI/kill, `ripristina`, costruttore dopo l'ultima modifica. Due minuzie del revisore da fare al prossimo ritocco: riga 198 (`mount | grep -q` con pipefail → `findmnt` o `if`), riga 7 (il commento deve citare anche xubuntu).
- Snap per distro: firmware-updater su ubuntu, xubuntu, lubuntu; snap-store su ubuntu, xubuntu; kubuntu nessuno dei due.

## PIANO — impostazioni della sessione remota GNOME leggibili anche dai programmi snap (19 nov 2026, notte)
Autorizzato dal proprietario senza attesa dell'OK sul piano (19 nov, notte), con revisore obbligatorio e verifica sulle VM; fermarsi solo se serve una scelta sua.

**Problema (misurato sulla VM `ubuntu`, registri in `/media/REMOTIX-UBUNTU/log/dconf-misure/`).** Nella sessione remota REMOTIX mette `DCONF_PROFILE=/run/user/<uid>/remotix/dconf/profile` con tre strati: `user-db:user`, `file-db:…/locks.db`, `service-db:shm/remotix`. I programmi Flutter di Ubuntu (Firmware Updater, Security Center, App Center, installatore della live) hanno un lettore proprio che conosce SOLO `user-db` e `system-db`: a una riga `file-db`/`service-db` scarta tutto il profilo (`Unknown DConf source`); gli snap confinati non possono nemmeno leggere quel percorso (`No DConf source to write to`). I programmi si aprono lo stesso (misurato), l'installatore della live no.

**Che cosa si è misurato che funziona (forme F e D2).**
- Un profilo con sole righe `user-db:user` / `system-db:<blocchi>` / `user-db:<sessione>` dà a GNOME gli stessi blocchi di oggi e il valore della tastiera, il cambio a sessione viva arriva a chi osserva (`gsettings monitor`, `dconf watch`), il file `user` dell'utente non cambia, e il lettore Flutter non dà eccezioni.
- Se `DCONF_PROFILE` NON è impostata, dconf legge il profilo da `$XDG_RUNTIME_DIR/dconf/profile`; gli snap confinati (che hanno un altro `XDG_RUNTIME_DIR`) non lo vedono e usano il normale `user-db:user`, senza eccezioni.

**Correzione.**
1. Il pacchetto installa il database dei blocchi come database di sistema `/etc/dconf/db/remotix`, compilato in `postinst` (tolto alla rimozione) da file chiave generati IN COSTRUZIONE dalla tabella `DCONF_KEYS` di `src/session.c` (una sola fonte: niente elenco doppio).
2. La sessione non usa più `DCONF_PROFILE` (né nell'ambiente della sessione né nel gestore utente): scrive `$XDG_RUNTIME_DIR/dconf/profile` con `user-db:user`, `system-db:remotix`, `user-db:remotix` e le altre righe del profilo di base.
3. I valori che cambiano a sessione viva (`input-sources`) vanno nel database utente `remotix` (`~/.config/dconf/remotix`) invece che nello strato in memoria; svuotato e riempito alla nascita come oggi.
4. La «cintura» di fine sessione e il ripristino alla nascita restano, applicati al nuovo file (a sessione finita il file torna al solo profilo di base o sparisce: chi nasce dopo legge le impostazioni normali).
5. Ripiego dichiarato: se `/etc/dconf/db/remotix` manca o non si legge, comportamento di oggi (tre strati compilati al volo) con una riga nel registro.

**Differenza da dichiarare.** Un piccolo file nostro `~/.config/dconf/remotix` nella casa dell'utente (tre chiavi della tastiera), al posto dello strato in memoria. Il file `user` dell'utente resta intatto.

**File.** `src/session.c`, `src/input.c`, `src/child.c` (ambiente e cintura), `debian/remotix.postinst`, `debian/remotix.postrm`/`prerm`, `debian/rules` o `build/` (generazione dei file chiave), `debian/control` se cambia una dipendenza, manuali e `docs/REGISTRO-problemi.md` (voce nuova), prove (`prove/check-desktop.py` se legge il profilo).

**Rischi.** Codice delicato del ciclo di vita della sessione (nascita, uscita, rientro, cintura): va letto tutto ciò che tocca `DCONF_PROFILE` prima di cambiare. Un profilo obbligatorio dell'amministratore (`/run/dconf/user/<uid>`) continua a vincere, come oggi. Un `DCONF_PROFILE` già presente nel sistema va rispettato come profilo di base. Su Debian (dconf 0.40) questa strada non è misurata: questo albero è solo Ubuntu.

**Fatto quando.** Sulla VM `ubuntu` con il pacchetto nuovo: (a) nella sessione remota Firmware Updater, Security Center e App Center partono senza eccezioni dconf nel registro; (b) i blocchi sono in vigore (stesse chiavi e valori di prima, non scrivibili) e la tastiera scelta dal client arriva e cambia a sessione viva; (c) il file `user` dell'utente è identico prima e dopo; (d) dopo l'uscita, `DCONF_PROFILE` non è nel gestore utente e un programma nuovo legge le impostazioni normali; (e) uscita e rientro ripetuti lasciano il profilo giusto; (f) giro automatico verde su tutte e quattro le VM; revisore APPROVATO.

### 19 nov, notte — avanzamento
- Deciso dal proprietario: preparazione delle VM senza video a DUE per volta (4 GB ciascuna); prove con la Radeon una per volta, ordine Ubuntu, Kubuntu, Xubuntu, Lubuntu. Autorizzati: correzione delle impostazioni senza attendere il suo OK sul piano, e giro automatico sulle VM lanciato da me. Lo si chiama a provare solo a prodotto pronto.
- Le quattro VM sono aggiornate (kernel 7.0.0-44) con istantanee `pulito` e `aggiornato` (`ubuntu`: `unione6`). `server/vm-radeon-aggiorna.sh` nuovo; `vm-radeon.sh` ha `prova-avvio <nome> --resta`. Spegnimento/riaccensione di `ubuntu` con lo script corretto: provati (5 s / 18 s). `unione6` installato su `ubuntu`.
- Giro di prove adattato alle VM: `prove/banco-vm/{box.sh,fresh-vm.sh}`, `RX_BANCO=vm`. Revisione: DA CORREGGERE (falso verde con RX_TEMPO non intero, gawk, pulizia non verificata, apt muto) → corretto → APPROVATO. Comando: `cd /media/REMOTIX-UBUNTU/albero/prove && RX_BANCO=vm TAG=vm-<de> nohup ./all.sh <de> --clean > log/vm-<de>.run 2>&1 < /dev/null &` (oppure `--fresh <deb>`); riepilogo in `log/<TAG>/summary.txt`. MAI ancora eseguito sul campo. Righe SKIP dichiarate: `prelocal/real-greeter`, `ban/other-addresses`, `package`. Minuzie rimaste: `all.sh:19` (zeri iniziali), `fresh-vm.sh:40` (`deactivating`), `all.sh:43-46` (dimensione del file di prova). Incognita: le prove audio su macchine senza scheda (uscita predefinita della sessione).
- Correzione delle impostazioni: in scrittura (pacchetto `unione7`).
- Deciso dal proprietario (19 nov, notte): giro RIDOTTO prima di chiamarlo — giro completo solo su `ubuntu` (GNOME, l'unico desktop toccato dalla correzione delle impostazioni); su `kubuntu`, `xubuntu`, `lubuntu` solo accensione con la Radeon, un accesso che arriva al desktop con il video, uscita. Le prove fini su quei tre le fa lui.
- 19 nov, notte tarda — correzione delle impostazioni: tre giri di revisione (unione7 → DA CORREGGERE; unione8b → DA CORREGGERE per «UNKNOWN non è DEAD»; unione9 → APPROVATO alla lettura; unione10 = unione9 + tre minuzie → APPROVATO). Pacchetto corrente: `unione10` (`/media/REMOTIX-UBUNTU/pacchetti/unione10/`, sha256 `07b270e8…63aa`), installato su `ubuntu`. Deciso dal proprietario: «la disinstallazione deve lasciare il sistema pulito» → il purge toglie `~/.local/state/remotix` e `~/.config/dconf/remotix` (come l'utente). Prove sulla VM fatte e non producibili: voce C5 del registro; punti aperti: voce E3. Giro su VM: funziona (primo lancio fermato dal suo controllo iniziale, che era sbagliato: corretto in `all.sh` e `banco-vm/box.sh`, ritocchi miei NON ancora passati dal revisore, insieme a `check-desktop.py:359` che ora ignora `.config/dconf/remotix`).
- 19 nov, notte tarda — GIRO COMPLETO su VM `ubuntu` (GNOME, `unione10`, TAG `vm-gnome-unione10`, 47 min): 120 PASS, 2 FAIL, 1 BLOCKED, 3 SKIP. FAIL `desktop/users-shell-and-environment` = riga nota e accettata (identica a `unione5-gnome`). FAIL `ban/typed-names-not-logged` = falso rosso del banco (righe di sudo del banco nel journal): il banco ora entra come root con la chiave (`banco-vm/box.sh rootkey`; la chiave resta in `/root/.ssh/authorized_keys` delle VM su cui gira il giro) → `ban` 8/8 PASS. BLOCKED `audio-firefox` = Firefox di prova muto al primo avvio: ripetuto 2 volte PASS. `all.sh --only a,b` per i giri parziali (riga finale «PARTIAL RUN», uscita 3). Attrezzatura: revisione DA CORREGGERE → corretta → APPROVATA. Limite: dopo il passaggio a root il giro completo non è stato rieseguito per intero.
- `unione10` installato anche su kubuntu, xubuntu, lubuntu (istantanea `unione10`). In corso: controllo breve con la Radeon sulle tre e `ubuntu` riportata a pulita (`ripristina ubuntu unione6` + `unione10`).

### 19 nov, fine nottata — CONSEGNA AL PROPRIETARIO PER LE PROVE A MANO (pacchetto `unione10`)
- Quattro VM con `unione10`, ognuna riportata allo stato «appena installata + REMOTIX» (istantanea `unione10`); `ubuntu` ACCESA con la Radeon su https://192.168.0.2:8841, le altre spente (kubuntu :8842, xubuntu :8843, lubuntu :8844). Utenti `prova` / `prova2`, password `prova2026`. Cambio di macchina: `vm-radeon.sh spegni <a>` poi `accendi <b>` (5 s + 18 s).
- Controllo breve con la Radeon su tutte e quattro (accesso come `prova2`, poi ripristino): desktop giusto e immagine vera su ognuna (immagini in `/media/REMOTIX-UBUNTU/log/consegna/`). `ripristina` provato sul campo: salva da sé lo stato corrente (`prima-<data-ora>`).
- Da guardare a mano: nell'immagine di Kubuntu (10 s dopo il primo accesso) si vede il Welcome Center ma non il pannello di KDE. Su Xubuntu lo sfondo c'è (il difetto E1 di Debian qui non compare).
- All'avvio della macchina il servizio scrive una riga «CANNOT ENCODE VIDEO» e 2 s dopo «the card arrived»: gara con il driver della scheda, si risolve da sola.
- Non coperto dal giro: accesso locale vero dalla schermata di accesso dopo una sessione remota; giro completo solo su GNOME (deciso: ridotto); dopo il passaggio del banco a root il giro completo non è stato rieseguito.
- Nessun commit: tutto il lavoro di oggi è nell'albero locale (branch `ubuntu-26.04`) e sul server.

### 19 nov, tarda sera — prove a mano del proprietario sulle VM (`unione10`)
- Ubuntu (GNOME): «funziona abbastanza bene». Annotati: avviso di Ubuntu «internal error» = `wireplumber` che si interrompe alla chiusura della sessione dell'utente (anche dopo un'uscita da REMOTIX, visto alle 21:50; da chiarire se dipende dalla VM senza scheda audio); piccoli scatti nel video da Chrome su Android (registro, voce E4).
- Kubuntu (KDE): «tutto regolare» (tablet e telefono Android). Il silenzio dal telefono era Phonestra sul tablet (portava altrove l'audio del telefono): nessun difetto di REMOTIX.
- Restano da provare: Xubuntu, Lubuntu.
- Xubuntu (XFCE): OK. In più il proprietario ha provato detach/reattach da Linux e da Android (quindi a risoluzioni diverse) su quanto provato finora: sempre OK. Resta Lubuntu.
- Lubuntu (LXQt): OK. PROVE A MANO SULLE QUATTRO VM CONCLUSE (proprietario, 19 nov sera, `unione10`): GNOME, KDE, XFCE, LXQt tutte OK, compresi detach/reattach da Linux e Android. Prossimo: riprova della live vera sul server (chiavetta pronta); pacchetto per la live sul disco del server: `/media/remotix-unione10.deb` (`sudo apt install -y /media/remotix-unione10.deb && sudo systemctl enable --now remotix`). Tutte le VM spente prima del riavvio del server.

### 19 nov, notte — LIVE VERA di Ubuntu 26.04.1 sul server, pacchetto `unione10` (seconda prova del proprietario)
- `apt install /media/remotix-unione10.deb` + `systemctl enable --now remotix`: accesso riuscito al primo tentativo («§5.1 CONNECTED», sessione GNOME NEW); zero `Unknown DConf source` / `No DConf source` nel journal; l'installatore della live parte nella sessione remota senza errore (stato WAITING, `error: null`). I due guasti del pomeriggio sono chiusi anche su macchina vera.
- Prova «locale esclude remoto» fatta a mano (era lo SKIP `prelocal/real-greeter`): accesso locale di `ubuntu` alla schermata di GDM con il desktop remoto aperto → accesso trattenuto in PAM, desktop remoto chiuso in 851 ms, client mandato via con 0x04, profilo dconf di runtime REMOVED nello stesso secondo, poi l'accesso locale prosegue. Dopo il Log Out locale, nuovo accesso remoto riuscito (tastiera «it» dal client), uscita pulita, nulla di nostro rimasto. Nessuna segnalazione in /var/crash.
- Non provate su macchina vera: le live di Kubuntu, Xubuntu, Lubuntu.
- LIVE VERA di Kubuntu 26.04.1 (kernel 7.0.0-30), `unione10`: accesso riuscito al primo tentativo (`SESSION to kubuntu: NEW … desktop kde`), «§5.1 CONNECTED», profilo AppArmor caricato, labwc e dconf-cli installati da apt come Recommends, nessuna segnalazione in /var/crash, zero errori dconf. Nota: sulla macchina vera il video passa da VA-API sulla scheda `renderD128` («HEVC: yes via vaapi»), nelle VM dalla via Vulkan sulla Radeon: le due strade di codifica sono state provate entrambe, su banchi diversi.
- Live vera di Kubuntu, prova «locale esclude remoto» fatta a mano dal proprietario: accesso locale da SDDM con il desktop remoto aperto → trattenuto in PAM, client mandato via con 0x04, desktop remoto chiuso dal suo figlio in 10,9 s (su GNOME 0,85 s: è il tempo di chiusura di KDE già descritto nel registro, sezione D), poi l'accesso locale prosegue («Session started true»). Nessuna segnalazione in /var/crash.
- LIVE VERA di Xubuntu 26.04, `unione10`: «sembra funzionare tutto ok» (prova a mano del proprietario; registro della live non letto: SSH non attivato). Domanda del proprietario: l'utente locale non riesce a spegnere la macchina → è la regola polkit `50-remotix-no-poweroff.rules` (voluta, nel manuale). CONFERMATO da lui il 19 nov: «è il comportamento corretto: un utente locale non può sapere se ci sono utenti remoti che stanno lavorando». Non riproporre modifiche. Resta non provata come live: Lubuntu.
- LIVE VERA di Lubuntu 26.04, `unione10`: OK (prova a mano del proprietario; registro non letto).
- **19 nov 2026, notte — il proprietario dichiara chiuso il lavoro su Ubuntu** («per ubuntu abbiamo terminato»): `unione10` provato da lui sulle quattro VM e sulle quattro live vere (Ubuntu, Kubuntu, Xubuntu, Lubuntu). Da fare prima della pubblicazione: commit (albero mai committato da `unione5` in poi), manuali HTML da rigenerare (`python3 manuals/sources/build.py`), riordino del repo «una sottocartella per distro», pubblicazione (ricetta nella memoria della 1.0.0 Debian). Aperti non bloccanti: registro E3, E4; avviso `wireplumber` visto solo sulla VM.
