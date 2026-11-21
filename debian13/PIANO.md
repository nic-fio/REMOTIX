# PIANO — REMOTIX per Debian 13 (trixie)

Deciso dal proprietario il 17 nov 2026. Stato: **in corso** (vedi «Stato» in fondo).

- **20 nov 2026, riordino del repo:** un solo ramo `main`, una cartella per distribuzione (`debian13/`, `ubuntu26.04/`), ciascuna autonoma. Il ramo `ubuntu-26.04` è stato unito dentro `ubuntu26.04/` con la storia. Nei testi più sotto, «ramo `main`» e «ramo `ubuntu-26.04`» (voci datate prima del riordino) vanno letti come le cartelle `debian13/` e `ubuntu26.04/`. Costruzione non riprovata dopo lo spostamento.

## Obiettivo
REMOTIX funzionante su Debian 13, con i 4 desktop (XFCE, LXQt, GNOME, KDE), con le specifiche originali
(`SPECS.md`, `RCP.md`, `DECISIONS.md` del vecchio repo). Il codice è solo per Debian: nessun riconoscimento
di distro, nessun adattamento per altre. Una distro futura avrà un codice suo, separato.

## Regole
- Il vecchio codice (`~/Documenti/REMOTIX`) si riusa finché è possibile; resta in sola lettura, non si cancella.
- Si porta un pezzo alla volta nella cartella nuova, togliendo tutto ciò che non è Debian.
- Il codice lo scrivono agenti Sonnet. Fable (sessione principale) controlla ogni pezzo prima di accettarlo.
- Le prove: poche, piccole, con un browser vero, un container alla volta. Quando e come farle lo decide il proprietario.
- Ogni passo si chiude con la prova del proprietario. Non si passa al successivo se il precedente non funziona.
- Niente sito, manuali, repo pubblici finché il prodotto non è pronto.

## Passi
0. **Preparazione.** Cartella nuova con repo git locale. Script che rimette sul server gli strumenti dopo ogni
   riavvio (podman, compilatore, git) e cartella di lavoro `/media/REMOTIX-DEBIAN`.
   Fatto quando: lo script, lanciato su server appena riavviato, lascia tutto pronto per compilare.
1. **La base.** Si portano dal vecchio codice prodotto e pacchetto Debian; si costruisce il `.deb` in un container trixie.
   Fatto quando: `apt install ./remotix.deb` riesce su una Debian pulita.
2. **I 4 desktop insieme** (deciso dal proprietario il 17 nov: una sola distro, quindi si lavora in parallelo).
   4 container Debian, uno per desktop (XFCE, LXQt, GNOME, KDE), un agente per desktop.
   Fatto quando, su ciascuno: dal browser password → desktop, mouse e tastiera funzionano.
   **Punto di decisione:** qui il proprietario prova e decide se continuare.
3. **Pulizia del codice non Debian**, un pezzo alla volta, ciascuno controllato, senza cambiare il comportamento.
4. **Le altre funzioni**, una alla volta sui 4 desktop: staccare/riattaccare, uscita dalla sessione, audio,
   appunti, più utenti insieme, blocco dopo tentativi sbagliati, telefono e tastiera a schermo.
5. **Sicurezza e pacchetto finale.** Separazione dei privilegi, AppArmor, installazione/rimozione pulite.
6. **Rilascio.** Manuali riscritti dal codice, pubblicazione — solo su decisione del proprietario.

## Cosa sparisce rispetto al vecchio
Installatore multi-distro, pacchetti Fedora/Arch/SUSE/Alma, SELinux, varianti di login per distro,
labwc modificato, la logica Ubuntu, il vecchio banco di prove (194.000 righe).

## Scelte prese (salvo indicazione diversa)
Installazione con `apt`, servizio spento finché non lo si accende; Intel e AMD nella prima versione (NVIDIA dopo);
obiettivi della 1.5 (3K, 8 utenti); nessun aggiornamento dalla 1.x.
Le righe delle specifiche che parlano di più distro vengono sospese con una decisione scritta.

## Rischi
- GNOME (nascita e chiusura della sessione) e KDE dentro labwc sono le parti più delicate.
- Nel portare il codice si può rompere qualcosa che funzionava: per questo si porta un pezzo alla volta, con controllo.
- Un solo server di prova, con schede Intel e AMD.

## Stima
Con il riuso del vecchio codice: 6–10 settimane in tutto (stima a giudizio, non misurata).
Passi 0–2: circa 1–2 settimane.

## Stato (17 nov 2026, sera)
- Passi 0, 1, 2 fatti. Pacchetto corrente: `remotix_2.0.0~dev-4+deb13` (server: /media/REMOTIX-DEBIAN/pacchetti/pulizia1).
- Passo 3 (pulizia): tranche 1 fatta e confermata dal giro completo (docs/PULIZIA-tranche1.md); il resto è in docs/INVENTARIO-non-debian.md.
- Passo 4 (funzioni), sui 4 desktop con `prove/all.sh` (34 controlli per desktop, tutti PASS nel giro «pulizia1b»):
  base (Chrome, Firefox), riattacco ×3, Log Out, più utenti ×3, riavvio del servizio, caduta rete, ingressi simultanei,
  uscita di un utente con un altro al lavoro, tempi, audio (Chrome, Firefox), appunti, blocco dopo password sbagliate.
- Correzioni al prodotto fatte oggi: (1) la sessione logind resta attiva per tutta la vita del desktop e il Log Out chiude
  davvero la sessione su tutti i desktop (child.c); (2) KDE: il Log Out va a buon fine anche se systemd rifiuta lo stop (session.c).
- Deciso (17 nov): nessun comando di sblocco per l'amministratore (non è una funzione prevista); il blocco dell'indirizzo resta
  a 20 tentativi falliti in 5 minuti (specifiche allineate: SPECS §4.2, DECISIONS-11 §11.53).
- Aperti: appunti con Firefox; telefono; XFCE ignora un Log Out chiesto mentre si sta ancora avviando (comportamento del
  desktop); container di prova con rete condivisa (33 schermi X in tutto); AppArmor da provare su macchina vera (profilo in «complain»).
- Non ancora fatto: passo 5 (installazione/rimozione pulite, AppArmor), passo 6. Versione del prodotto: **1.6.0**. Commit, manuali e sito solo a prodotto finito e funzionante (proprietario, 17 nov).

## Stato (17 nov 2026, ore 19:40) — parte Debian chiusa per il funzionamento
- Pacchetto: `remotix_1.6.0-1+deb13_amd64.deb` (server: /media/REMOTIX-DEBIAN/pacchetti/1.6.0/), costruito da questo albero.
- Giro finale `prove/all.sh` sui 4 desktop insieme (log server: prove/log/v160-<de>/summary.txt): XFCE 111/118, LXQt 112/118,
  KDE 111/118, GNOME 104/118. Non verdi, tutti spiegati: Ctrl+Alt+Canc (pulsante nascosto dal 16 ago) e Ctrl+Alt+Fine (tolto il
  17 ago) — specifiche §7.3-bis e §5.2-bis da allineare; dimensione massima 3840×2160 = tetto della scala di sonde del decoder nella pagina (`MEASURE_PROBES` in page.html, che si ferma a 3840×2160 apposta; non è il decoder del browser di prova; vedi «Revisione dei manuali» in fondo);
  XFCE angolo coperto dal pannello; KDE tasto Canc trattenuto dal desktop (solo in diagnostica); GNOME pkexec (SHELL vuota, voluto).
  GNOME telefono simulato: da solo 18/19 (primo tocco dopo l'ingresso non registrato: in accertamento, priorità bassa).
- Prova del proprietario con Samsung DeX su GNOME (17 nov): appunti, audio/video, ridimensionamento finestra: tutto regolare.
  La modalità «a tocco» su schermo da 6" non interessa al proprietario (priorità bassa).
- Pacchetto: check-package 8/8 sui 4 desktop; VM Debian 13 vera: installazione, AppArmor (complain ed enforce: 0 negazioni fino
  alla connessione; sessione non provabile senza scheda video), riavvio, rimozione e purge senza residui.
- Correzioni al prodotto del 17 nov: sessione logind attiva + Log Out che chiude davvero (child.c); Log Out KDE (session.c);
  prerm/postrm (rimozione con utente collegato, file di stato); priorità dei messaggi (31 righe, docs/REGISTRO-priorita.md);
  primo tocco da telefono (page.html); regola polkit con «halt» (15 azioni); pulizia tranche 1 (docs/PULIZIA-tranche1.md).
- Rifiniture rimaste (non bloccanti): senza scheda video l'errore si ripete ogni 2 s nel registro; `xfce-chiavi` non viene tolto
  dopo il ripristino; profilo AppArmor da osservare in sessione su macchina con scheda video prima di passarlo a enforce;
  pulizia tranche 2 (docs/INVENTARIO-non-debian.md); canvas-limits da giudicare sul tetto che la pagina dichiara (3840×2160, scala di sonde della pagina).
- Burocrazia (commit, manuali, sito, allineamento del testo delle specifiche): solo su decisione del proprietario.
- Aggiunta delle 19:40: il pacchetto rifiuta una NUOVA installazione su una macchina senza scheda video (nessun nodo DRM di
  render; richiesta del proprietario) e, se la scheda c'è ma non codifica, lo dice all'installazione (preinst/postinst). Provato:
  VM senza scheda = rifiuto pulito; container con scheda = check-package 8/8. I 4 container hanno questo pacchetto.
- GNOME, modalità a tocco: i fallimenti erano della prova (GNOME nasce nella Panoramica, che trattiene i tocchi: lo vede anche un
  utente vero). Residuo non dimostrato, 1 caso su 13: il primo tocco può cadere nel punto iniziale se la posizione del puntatore
  arriva prima che Mutter sia pronto (page.html `touch_announce_pointer`, un solo invio per sessione). Priorità bassa.

## Nuova vita (17 nov 2026, sera) — decisione del proprietario
- Questo codice è la base da cui riparte tutto: la versione è **1.0.0** (non più 1.6.0; i numeri 1.6.0 qui sopra indicano lo
  stesso codice, provato con quel numero provvisorio). Pacchetto: `remotix_1.0.0-1+deb13_amd64.deb`.
- Su git e sul sito deve esistere solo questo codice: il vecchio repo GitHub viene eliminato e ricreato con questo solo contenuto.
- Le altre distribuzioni: nei prossimi giorni, ciascuna con il suo codice.

## Revisione dei manuali (17 nov, sera)
- La revisione ha trovato testi vecchi (programma di installazione, openSUSE/Fedora/Arch, «motore», sblocco dell'amministratore,
  «12» tentativi per indirizzo invece di 20, pulsante Ctrl+Alt+Canc, messaggi con `/dev/dri/renderD*`) e due spiegazioni sbagliate
  qui sopra (il tetto 3840×2160 è la scala di sonde della pagina, non il decoder del browser di prova).
- Corretto da me (solo testi): messaggi di kwin.c, authentication.c, command.c, preinst, postinst, page.html; commenti di debian/*,
  rootside*.h, rcp.h, walls.*, encoder.c, page.c, Makefile, AppArmor; CLAUDE.md; prove (check-ban 12→20, fresh.sh/base-check.py cartella
  `boxes`, lib.sweep con `in` e `ph`); DECISIONS-11 §11.54 con rimandi nelle specifiche. Logica non toccata.
- Non cambiato, da decidere: `MEASURE_PROBES` si ferma a 3840×2160 apposta (commento in page.html: livello 5.1 dichiarato, HEVC 5.1
  arriva a 4096×2176; le sonde sono generate da uno script di banco fuori da questo albero), quindi 4096×2304 non è raggiungibile
  da nessun client; LICENSE.md e THIRD-PARTY-LICENSES sono testi legali del proprietario (proposte nel rapporto).

## Accesso locale con un desktop remoto rimasto «orfano» — FATTO (17-18 nov 2026)

- **Difetto:** dopo un riavvio del servizio REMOTIX, il desktop remoto restava vivo senza più nessuno a sorvegliarlo; l'accesso locale dello stesso utente rompeva la schermata di accesso di GNOME (serviva `systemctl restart gdm3`).
- **Decisione del proprietario (opzione 1, DECISIONS-11 §11.56):** i desktop remoti si chiudono quando il servizio si ferma; mentre il servizio gira, un desktop rimasto senza il suo processo `child` viene chiuso («no orphan desktops»).
- **File toccati:** `src/rootside.c`, `src/main.c`, `src/child.c`, `src/child.h`.
- **Revisione (Fable):** tre giri, APPROVATO.
- **Pacchetto:** costruito sul server in `/media/REMOTIX-DEBIAN/pacchetti/noorfani/` (nessun errore, lintian E=0 W=0), installato sul tablet il 18 nov alle 07:01.
- **Prove del proprietario (18 nov, tablet + notebook aziendale, GNOME), confermate dal registro di sistema:** accesso locale dopo il riavvio del servizio; chiusura del desktop remoto al riavvio (servizio fermo e ripartito in meno di 2 s); stacca e riattacca (stesso desktop ripreso); il locale caccia il remoto nel caso normale. Tutte riuscite.
- **Resta aperto:**
  1. leggere che cosa succede su KDE, XFCE, LXQt, le cui schermate di accesso non hanno il «fermo» di GNOME nemmeno nel caso normale;
  2. caso limite noto: servizio ucciso di colpo e non ancora ripartito (circa 2 s), in quell'intervallo nessuno può chiudere il desktop rimasto;
  3. (chiuso) modifiche salvate in git e su GitHub il 18 nov, su richiesta del proprietario.

## L'accesso locale chiude prima il desktop remoto, su tutti i desktop — FATTO e provato dal proprietario sul tablet (18 nov 2026)

- **Difetto (letto nei sorgenti):** su KDE, XFCE e LXQt la schermata di accesso non trattiene chi ha un desktop remoto aperto; il desktop locale partiva mentre quello remoto era ancora vivo (KDE e XFCE: ritorno alla schermata di accesso; LXQt: desktop senza sfondo né notifiche).
- **Regola unica (DECISIONS-11 §11.57):** all'accesso locale grafico il sistema chiama `remotix-local-login` (PAM, `pam_exec`, riga messa da `pam-auth-update`); REMOTIX chiude del tutto il desktop remoto di quell'utente e solo dopo l'accesso prosegue. Mai un accesso fallito: riga `optional`, uscita sempre 0, tetto 25 s, uscita immediata se il servizio è fermo.
- **File:** `src/local_login.c` (nuovo), `src/rootside.c`, `rootside.h`, `rootside_proto.h`, `main.c`, `child.c`, `child.h`, `session.c`, `session.h`, `Makefile`, `debian/` (rules, control, postinst, prerm, `remotix.pam-config` nuovo), `prove/check-prelocal.py` (nuovo), `prove/all.sh`, `prove/lib.py`, `prove/check-package.py`.
- **Revisione (Fable):** due giri, APPROVATO. Note non bloccanti lasciate: abbandono dimenticato se una chiusura già chiesta fallisce (main.c ~1945); pid del genitore preso all'ordine e non all'avvio (session.c ~4461); secondo accesso locale dello stesso utente entro pochi secondi; pulizia saltata se il child ucciso non è ancora raccolto (codice precedente).
- **Pacchetto:** server `/media/REMOTIX-DEBIAN/pacchetti/prelocal2/`, tablet `~/remotix-prelocal/` (non installato).
- **Prove sul server (log: `/media/REMOTIX-DEBIAN/prove-prelocal2/log/giro-<de>/`):**
  - `check-prelocal` 6/6 sui quattro desktop: desktop remoto chiuso dal suo child in 0,6-1,3 s, pagina avvisata con 0x04, nuovo desktop apribile dopo, nessun effetto da accessi che non c'entrano, nessun rallentamento a servizio fermo, riga PAM dopo `pam_systemd`.
  - Giro completo: GNOME 117, KDE 117, XFCE 117, LXQt 119 righe PASS. Non verdi: quelle di ieri (Ctrl+Alt+Canc, Ctrl+Alt+Fine, coordinate XFCE, pkexec GNOME) più due:
    - `resilience/service-restart` sui quattro: la prova si aspetta ancora di ritrovare lo stesso desktop dopo il riavvio del servizio; dal 17 nov notte (§11.56) i desktop si chiudono al riavvio. È la prova da allineare, non il prodotto.
    - `phone/tap-click-portrait` su GNOME: il primo tocco già noto come instabile (vedi sopra, priorità bassa).
- **Limiti delle prove:** nei contenitori non c'è una schermata di accesso vera: l'accesso locale è simulato chiamando il programma a mano, senza sessione locale registrata. Il salto della guardia nel `child` e l'intreccio con i controlli periodici si esercitano solo con un accesso locale vero (tablet, GNOME). Su KDE/XFCE/LXQt con SDDM/LightDM veri: non provato. Nei contenitori RealtimeKit non parte e trattiene per 25 s l'uscita di un child giovane (la prova aspetta 31 s; sul tablet non succede).
- **Prova del proprietario sul tablet (GNOME, gdm vero, 18 nov 08:45), confermata dal registro:** accesso locale di `user` con desktop remoto aperto: accesso trattenuto in PAM, desktop remoto chiuso dal suo child in 803 ms (chiusura completa, guardia saltata come previsto), pagina avvisata con 0x04, sessione locale entrata e rimasta. Un minuto prima, a sessione locale aperta, il remoto era stato rifiutato (0x05).
- **Prova del riavvio allineata (§11.56):** `resilience/service-restart` ora si aspetta il desktop chiuso col servizio e una sessione nuova al rientro; `check-resilience` rigirato sui quattro desktop: tutto PASS (log server: `prove-prelocal2/log/resil2/`).
- **Prova del proprietario su KDE vero (18 nov, Debian 13 live avviata sul server, SDDM):** REMOTIX installato sulla live, desktop remoto aperto dal tablet, poi accesso grafico locale sul server: il desktop remoto è stato disconnesso e l'accesso locale è entrato al primo tentativo (riferito dal proprietario; registro non letto).
- **Prove del proprietario su XFCE e LXQt veri (18 nov, Debian 13 live avviate sul server):** come per KDE, l'attivazione della sessione grafica locale disconnette la sessione remota e l'accesso locale entra al primo tentativo (riferito dal proprietario; registri non letti).
- **Resta:** niente di aperto su questo punto. Le quattro schermate di accesso vere (GNOME, KDE, XFCE, LXQt) sono state provate dal proprietario.

## Rifiniture rimandate (non bloccanti, decisione del proprietario 18 nov 2026)

- **XFCE, sessione remota: sfondo nero invece di quello scelto dall'utente** (visto dal proprietario sulla live XFCE; nelle prove del server l'immagine era al 93% di un solo colore). REMOTIX non tocca le impostazioni dello sfondo. Ipotesi non verificata: XFCE salva lo sfondo per nome del monitor e lo schermo virtuale remoto ha un altro nome. Da accertare su una macchina con XFCE; controllare anche gli altri tre desktop (regola unica: nel remoto l'utente ritrova il suo sfondo). Cosmesi: si fa dopo.

## Manuali allineati al prodotto prima del rilascio — FATTO (18 nov 2026)

- **Controllo:** due agenti in sola lettura hanno confrontato i manuali con codice, pacchetto e decisioni. Numeri, blocchi, tempi, opzioni, PAM e pacchetto erano giusti; sbagliato o mancante tutto ciò che è cambiato il 17 e 18 nov.
- **Corretto (solo testi, sorgenti in `manuals/sources/`, HTML rigenerati con `build.py`, `--check` allineato):** riavvio del servizio che chiude i desktop (§11.56) in entrambi i manuali; accesso locale che chiude il desktop remoto (§11.57), con sezione nuova nel tecnico (ch14) e i fatti distribuiti negli altri capitoli; limiti noti dichiarati (sfondo XFCE, servizio ucciso di colpo, cosa è stato provato e come, artefatto RealtimeKit, finestra della password su GNOME non verificata); resti vecchi tolti (sezione «altre distribuzioni», «installer», «NOT ACTIVE YET», «one binary»); limiti dichiarati 3K e 8 utenti (§11.58) accanto a quelli tecnici veri.
- **Revisione (Fable):** due giri, APPROVATO.
- **Limite del controllo:** il manuale tecnico non è stato riletto tutto per intero; ch05, ch06, ch09, ch10, ch11, ch21 solo per parole chiave (parti non toccate dal 17 nov).
- **Aperto, decisione del proprietario:** scrivere «3K» anche in pixel nei manuali.
- **Testi vecchi dentro il prodotto, da sistemare alla prossima costruzione (già annotati nel manuale tecnico):** messaggio di registro in `main.c` ~466-473 che nomina i file PAM di Fedora/SUSE/Arch; messaggio in `main.c` ~3918-3923 («the desktops stay alive»); commenti in `debian/rules`, `postinst`, `prerm`, `remotix.service` che dicono che i desktop sopravvivono allo stop.
- **Da verificare su macchina vera (non bloccante):** su GNOME, `pkexec true` in un terminale del desktop remoto: compare la finestra della password?

## Rilascio 1.0.0 — FATTO (18 nov 2026)

- Pacchetto definitivo: `remotix_1.0.0-1+deb13_amd64.deb`, SHA-256 `d2ec4771…4f61`. Programma identico byte per byte
  a quello provato dal proprietario sulle quattro schermate di accesso; rispetto a quello cambia solo l'indirizzo del
  responsabile del pacchetto (ora `remotix@nicfio.it`). Copia sul tablet in `~/remotix-1.0.0-definitivo/`; installato sul tablet.
- Sito di nuovo online (https://remotix.nicfio.it): testi controllati dal revisore contro i manuali (tre giri,
  APPROVATO), pagine rigenerate con `site/standalone.py`, pacchetto in `download/`. La pagina di avviso del 16 nov è
  salvata sul VPS (`~/remotix-avviso-ritiro-20261116.html`).
- GitHub: repo `nic-fio/REMOTIX` cancellato dal proprietario e ricreato pubblico con la storia ripulita; release
  `v1.0.0` con pacchetto e manuali. Copia del repo com'era prima: `~/remotix-repo-prima-pulizia-20261118.git`.
- Server ripreparato dopo la pulizia (`server/prepara-server.sh`); le macchine di prova NON sono state ricostruite.
- Rimandati alla versione successiva: tre testi vecchi dentro il prodotto, sfondo nero su XFCE, verifica di `pkexec`
  su GNOME. `site/` resta fuori dal repo.

## XFCE: sfondo nero nella sessione remota — accertato, nessuna modifica a REMOTIX (18 nov 2026)

- **Riprodotto** sulla macchina di prova Debian 13 XFCE con il pacchetto 1.0.0, anche con utente nuovo: non dipende
  dallo sfondo scelto. `xfdesktop` non dipinge né immagine né colore (icone sì).
- **Causa:** difetto della libreria di XFCE `libxfce4windowing` 4.20.2 (quella di Debian 13). Il compositore (labwc)
  dice a quale schermo appartiene l'area di lavoro, ma la libreria riceve il messaggio prima di conoscere lo schermo e
  lo perde; senza quel dato `xfdesktop` dipinge nero. Non è REMOTIX e non è una modifica di Debian.
  (Una prima lettura attribuiva la mancanza a labwc: era sbagliata, un filtro nei comandi nascondeva delle righe.)
- **Già corretto dagli autori di XFCE:** modifica del 25 lug 2025 («Connect to XfwScreen::monitor-(added|removed)»),
  presente da `libxfce4windowing` 4.20.4. Debian 13 ha la 4.20.2; Debian testing (forky) ha la 4.20.7.
- **Non verificato sul campo:** che con la libreria nuova lo sfondo compaia davvero (la compilazione di prova non è
  stata completata). Verificato invece: fornendo a mano il dato mancante lo sfondo compare (foto prima/dopo).
- **Deciso con il proprietario:** difetto solo estetico; niente rimedio dentro REMOTIX per Debian 13. Si ricontrolla
  quando si passa a forky, dove dovrebbe sparire da solo.
- **Resta comunque vero:** XFCE tiene uno sfondo per ogni schermo; lo sfondo scelto in locale non passa da solo allo
  schermo remoto (la prima volta si vede quello di base).

## PIANO — Sito: manuali per distribuzione e pagina di Ubuntu 26.04 (20 nov 2026, OK del proprietario: «Sì, comincia a lavorare sul sito»)

**Obiettivo.** Ogni distribuzione ha i suoi due manuali (utente e tecnico): deciso dal proprietario il 20 nov. Il sito
va adeguato e riceve la pagina di Ubuntu 26.04. Tutto in locale: niente va online finché non lo dice lui.

**Passi.**
1. Ramo `main`: il manuale utente di Debian diventa «User Manual — Debian 13» (file, titolo, generatore).
2. Ramo `ubuntu-26.04`: via i due manuali di Debian (copie); ogni ramo tiene i suoi.
3. `site/distributions.json`: per ogni distribuzione i due manuali; nuova voce Ubuntu 26.04 (i suoi manuali si leggono
   dall'albero di Ubuntu).
4. `site/docs.html`: testo nuovo, una coppia utente + tecnico per distribuzione; il vecchio indirizzo
   `docs/user-manual.html` resta e rimanda alla pagina dei manuali.
5. `site/ubuntu2604.html`: pagina nuova sul modello di `debian13.html`, con solo affermazioni vere per Ubuntu.
6. `site/standalone.py` adeguato; generazione in `site/out/`; controllo dei collegamenti.

**Rischi.** Frasi di Debian copiate nella pagina di Ubuntu e false lì; schermate di Debian spacciate per Ubuntu (non
si usano: servono schermate vere dal proprietario); l'impronta del pacchetto sulla pagina deve essere quella del
pacchetto che verrà pubblicato.

**Fatto quando.** Il sito si genera senza errori, il revisore dà APPROVATO, il proprietario l'ha visto in locale.

**Stato (20 nov).** Passi 1-6 fatti in locale, revisore APPROVATO al secondo giro; per decisione del proprietario le
pagine delle distribuzioni non hanno schermate. Manca: che il proprietario lo veda (`site/out/index.html`) e dica
quando pubblicare. Alla pubblicazione: copiare il .deb di Ubuntu (`unione11`) in `site/out/download/`; se si pubblica
anche il pacchetto Debian corretto, cambiare insieme file e impronta nella pagina di Debian. Da decidere: le schermate
di Debian usate nella home come immagini generiche.

**Pubblicato (20 nov, ordine del proprietario «pubblica il sito»).** Sito online con la pagina di Ubuntu 26.04, i
manuali per distribuzione e il pacchetto Ubuntu `unione11` (sha256 `08772d85…36ab`); file online identici a `site/out/`.
NON pubblicati: il rilascio di Ubuntu su GitHub e il pacchetto Debian corretto (online resta `d2ec4771…`, regola a 15
azioni, mentre il manuale tecnico di Debian online descrive già la regola a 19): da decidere.

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
(US)» e Firefox in inglese senza toccare il menu — tutti i caratteri giusti. Manca: la prova su Ubuntu 26.04 (macchine
virtuali da ricostruire), il commit, la pubblicazione (sito, rilasci su GitHub, una frase nel manuale utente).
