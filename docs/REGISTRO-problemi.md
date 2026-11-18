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

## E. Aperti (non bloccanti)

### E1. XFCE: nella sessione remota lo sfondo è nero invece di quello scelto dall'utente
- **Visto:** dal proprietario sulla live XFCE, 18 nov 2026. Rimandato per sua decisione (cosmesi).
- **Che cosa si sa:** REMOTIX non tocca le impostazioni dello sfondo. Ipotesi non verificata: XFCE salva lo sfondo
  per nome del monitor, e lo schermo virtuale della sessione remota ha un altro nome.
- **Da fare:** accertare su una macchina con XFCE; controllare lo stesso punto sugli altri desktop.

### E2. Righe non verdi note nel giro di prove
- Pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine (prove da allineare, vedi B3); coordinate del mouse su XFCE nell'angolo
  coperto dal pannello; un controllo su GNOME voluto così (`pkexec`); primo tocco da telefono su GNOME, saltuario.
