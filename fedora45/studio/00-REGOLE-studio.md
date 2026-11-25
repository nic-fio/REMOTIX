# Regole comuni per gli agenti di studio — Fedora 45 (21 nov 2026)

Scopo: studio a fondo, PRIMA di scrivere codice, di ciò che serve per portare REMOTIX 1.0.1 (oggi Debian 13 e
Ubuntu 26.04) su Fedora 45 nei quattro desktop: GNOME (Workstation), KDE Plasma, XFCE, LXQt.
È solo studio: non si scrive codice del prodotto, non si costruisce il prodotto, non lo si installa né lo si prova.
Ogni agente studia UN desktop, sulla SUA macchina virtuale.

## Dove leggere (tablet, sola lettura)
- Repository: `/home/nicfio/Documenti/REMOTIX`. Il codice più vicino a Fedora è quello di Ubuntu: `ubuntu26.04/`
  (`CLAUDE.md`, `src/` — soprattutto `session.c` e i file del proprio desktop —, `debian/` per pacchetto, PAM, polkit,
  AppArmor, `docs/REGISTRO-problemi.md` DA LEGGERE PER PRIMO, `docs/SPECS.md`, `docs/DECISIONS*.md`, `docs/LESSONS.md`,
  `docs/STORIA-ubuntu-26.04.md`).
- Gli studi fatti per Ubuntu, in `ubuntu26.04/studio/`: sono il modello di profondità e di forma, e dicono che cosa
  guardare. GNOME: `1-gnome50-avvio.md`, `2-gnome50-chiusura-gdm.md`, `3-sessione-ubuntu.md`, `4-mutter50-cattura-input.md`,
  `12-verifiche-gnome.md`. KDE: `6-kubuntu-kwin-labwc.md`, `10-kde-controprova-labwc.md`, `12-verifiche-kde.md`.
  XFCE/LXQt: `7-xubuntu-lubuntu.md`, `9-xfce-pannello-plugin-perso.md`, `13-riunito-xfce-lxqt.md`, `12-verifiche-<de>.md`.
  Per tutti: `5-sistema-ubuntu.md` (sistema: PAM, logind, sicurezza), `8-pacchetto-e-prove.md`.
- Piano Fedora: `fedora45/PIANO.md`.

## Principi del prodotto da tenere presenti
- La sessione remota = un accesso locale dello stesso utente, meno i danni possibili su una macchina condivisa
  (nessuno spegne o riavvia la macchina). Una regola generale, non rattoppi per distro.
- Un utente con una sessione grafica locale attiva ⇒ il remoto è rifiutato; e viceversa l'accesso locale deve
  convivere pulito con ciò che REMOTIX ha lasciato.
- XFCE e LXQt in REMOTIX girano dentro labwc (Wayland) con Xwayland; KDE su Ubuntu ha richiesto un labwc nostro
  modificato; GNOME usa gnome-shell/Mutter headless. Va detto che cosa di tutto questo regge su Fedora 45.
- La rimozione del pacchetto deve lasciare il sistema pulito.

## La macchina virtuale (fatti veri su Fedora 45)
- Server: `ssh -o BatchMode=yes nicfio@192.168.0.2 'export TERM=dumb; ...'`. Niente contenitori: podman NON si usa, mai.
- Script: `/media/REMOTIX-FEDORA/vm-radeon/vm-radeon.sh <comando> <gnome|kde|xfce|lxqt>` (uso completo in testa allo script).
  La propria VM è quella col nome del proprio desktop: Fedora 45 installata dal contenuto della ISO Live ufficiale,
  SELinux enforcing, firewall com'è di serie, utenti `prova` (wheel, sudo) e `prova2`, password `prova2026`.
  Comandi nel guest: `vm-radeon.sh ssh <nome> '<cmd>'`.
- La VM parte in modo **virtuale** (scheda video virtuale, 5 GB): `vm-radeon.sh accendi <nome> virtuale`. Basta per quasi
  tutto: pacchetti (`rpm -qa`, `rpm -ql`, `dnf repoquery`, `dnf download --source`), file, unità systemd, journal, PAM,
  SELinux, e anche per un accesso locale dalla schermata di accesso (comandi `tasti` e `schermo` dello script).
- **La Radeon è una sola.** Serve solo per ciò che dipende dalla grafica vera (driver amdgpu, VA-API/codifica video,
  comportamento del compositor con GPU). Per usarla: spegnere la propria VM, `accendi <nome>` (senza `virtuale`); se lo
  script risponde che è occupata, aspettare e riprovare più tardi (intanto si continua in modo virtuale). Tenerla il
  meno possibile (al massimo 20 minuti per volta), poi `spegni` e di nuovo `accendi <nome> virtuale`.
- Nel guest si può: installare pacchetti dai repository Fedora per leggerli o provarli (`dnf install`, `dnf download`),
  abilitare repository per vedere che cosa offrono (es. RPM Fusion: dichiararlo), fare accessi locali, guardare.
  Tutto ciò che si cambia va annotato nel documento. Esiste l'istantanea `pulito` (sistema appena installato): se
  serve tornare pulita, `spegni` poi `ripristina <nome> pulito`. NON fare `dnf upgrade` dell'intero sistema.
- Vietato: toccare le VM o le cartelle degli altri agenti, `/media/DOWNLOAD`, lo script `vm-radeon.sh`; installare
  qualcosa sul server; lasciare la Radeon occupata. Uscite lunghe: su file (nel guest o in
  `/media/REMOTIX-FEDORA/studio/<nome>/` sul server, cartella propria), poi leggere solo ciò che serve.
- Alla fine: lasciare la propria VM SPENTA, con la Radeon libera. Non ripristinare l'istantanea (lo stato resta per i controlli).

## Vietato sul tablet (questa macchina)
- Modificare, spostare, cancellare qualunque file del repository. L'unico file che si scrive è il proprio documento.
- Compilare, clonare repository grossi, installare pacchetti, lavori pesanti.

## Che cosa studiare (ognuno per il proprio desktop; la parte «sistema» la fa ciascuno per ciò che lo tocca)
1. **Che cosa c'è**: versioni vere (desktop, compositor, display manager, systemd, PipeWire/WirePlumber, Xwayland,
   portali, labwc/wlroots e se sono nei repository), sessioni offerte (`/usr/share/wayland-sessions`, `xsessions`),
   quale parte in un accesso locale, X11 o Wayland.
2. **Accesso locale vero**, osservato: dalla schermata di accesso al desktop — processi, unità systemd dell'utente,
   variabili d'ambiente della sessione, sessione logind (tipo, classe, seat), file di avvio letti, portachiavi/wallet,
   D-Bus. È il termine di paragone per la sessione remota.
3. **Come REMOTIX avvia e chiude oggi questo desktop** (dal codice Ubuntu) e che cosa su Fedora 45 non regge più:
   nomi di binari, unità, percorsi (`/usr/libexec`, `/usr/lib64`), opzioni, versioni cambiate; cattura dello schermo
   e ingresso di tastiera/mouse; chiusura pulita; convivenza con il display manager (voci A1, A2 del registro).
4. **Sistema Fedora**: aggancio a PAM (authselect: come si aggiunge un modulo senza rompere e senza farsi cancellare),
   pam_faillock, SELinux (in quale dominio girerebbe un servizio di terzi installato da RPM, che cosa gli sarebbe
   negato — confinato/unconfined, porte, transizioni verso la sessione dell'utente; che cosa prende il posto del
   profilo AppArmor), firewalld (porta tcp+udp 7447 chiusa di serie? come la apre un pacchetto correttamente),
   polkit (regole, gruppo `wheel`), logind.
5. **Video e audio**: H.264 su Fedora (che cosa c'è di serie: openh264, VA-API con Mesa di Fedora, ffmpeg-free; che cosa
   manca senza RPM Fusion; con la Radeon: `vainfo`, encoder disponibili), PipeWire.
6. **Pacchetto**: nomi Fedora delle dipendenze di compilazione e d'uso oggi elencate in `ubuntu26.04/debian/control`,
   che cosa manca nei repository, regole RPM che toccano REMOTIX (scriptlet, unità systemd preset: «installato
   disabilitato», file in `/etc`, SELinux module in un RPM, licenze dei codec).
I punti 4–6 sono comuni: ciascuno li guarda sulla propria macchina e riporta i fatti; le differenze fra i quattro
gusti (pacchetti presenti o assenti di serie) sono proprio ciò che interessa.

## Che cosa si consegna
1. Un documento `/home/nicfio/Documenti/REMOTIX/fedora45/studio/<N>-<desktop>-fedora45.md` (N: 1 gnome, 2 kde, 3 xfce,
   4 lxqt), in italiano (termini tecnici in originale), dettagliato quanto serve a chi poi scriverà il codice: fatti con
   la fonte (percorso:riga nel repository, pacchetto e versione Fedora, comando e uscita osservata, file sorgente),
   distinguendo sempre **[V] verificato** (dove), **[W] dal web**, **[S] supposizione**. Deve chiudersi con:
   «Problemi da affrontare» (elenco numerato: che cosa, dove nel codice, peso piccolo/medio/grande, cura già nota
   da Ubuntu/Debian sì/no e dove), «Decisioni che spettano al proprietario», «Che cosa non si può sapere senza
   provare», «Prove consigliate», «Che cosa ho cambiato nella VM».
2. Come risposta finale: un riassunto di al massimo 40 righe con le scoperte principali, i problemi con il peso,
   le incognite, le decisioni per il proprietario. Mai scrivere «funziona» per ciò che non è stato osservato.
