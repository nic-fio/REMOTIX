# PIANO — REMOTIX per Debian 13 (trixie)

Deciso dal proprietario il 17 nov 2026. Stato: **in corso** (vedi «Stato» in fondo).

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
  3. le modifiche non sono in git (nessun commit senza richiesta).
