# Regole comuni per gli agenti che seguono il giro di misura «unione1» (18 nov 2026)

## Il quadro
REMOTIX per Ubuntu 26.04: il pacchetto unico `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (SHA-256 `2c473ac9…`, in
`/media/REMOTIX-UBUNTU/pacchetti/unione/`) contiene i cinque lavori di oggi. Il proprietario ha dato il via al giro di misura
completo: sul server girano GIÀ, in parallelo, quattro `all.sh <de> --fresh <deb>` (uno per macchina: gnome=Ubuntu, kde=Kubuntu,
xfce=Xubuntu, lxqt=Lubuntu), lanciati dal coordinatore. Ogni agente segue UNA macchina. È una MISURA: non si corregge nulla.
Piano e stato: `/home/nicfio/Documenti/REMOTIX-UBUNTU/PIANO.md`. Studi: `/home/nicfio/Documenti/REMOTIX-UBUNTU/studio/`.
Registro dei problemi già noti su Debian (righe non verdi attese: voce E2; comportamenti dei desktop: voce D):
`/home/nicfio/Documenti/REMOTIX-UBUNTU/docs/REGISTRO-problemi.md`.

## Dove stanno le cose (server: `ssh -o BatchMode=yes nicfio@192.168.0.2 'export TERM=dumb; ...'`)
- Prove: `/media/REMOTIX-UBUNTU/albero/prove/` (`all.sh`, `check-*.py`, `lib.py`); registri del giro in
  `/media/REMOTIX-UBUNTU/albero/prove/log/unione1-<de>/` (`<controllo>.out`, e alla fine `summary.txt`); uscita di `all.sh` in
  `/media/REMOTIX-UBUNTU/log/giro-unione1/<de>.out`.
- Macchine: `cd /media/REMOTIX-UBUNTU/albero/boxes && ./box.sh status | ssh <de> <cmd>` (podman di root: `podman ps` da utente non
  le mostra). Nel box: il registro del servizio è `journalctl -u remotix`, ma le righe della sessione (`session [utente] …`, scritte dal
  processo figlio) stanno nel journal dell'UTENTE: `journalctl _UID=<uid>`.
- Il giro dura fino a 4 ore e mezza. Per aspettare: un comando in background che finisce quando compare
  `/media/REMOTIX-UBUNTU/albero/prove/log/unione1-<de>/summary.txt` (per esempio `until [ -f …/summary.txt ]; do sleep 30; done`).
  NON usare `pgrep -f all.sh` in un ciclo (trova sé stesso e non finisce mai). Nel frattempo si possono leggere i `.out` dei controlli finiti.

## Che cosa fare
1. MENTRE il giro gira: solo lettura (registri del giro, journal nel box). Non installare, non riavviare, non aprire sessioni, non toccare
   utenti o file nel box: falserebbe le misure.
2. QUANDO `summary.txt` c'è: leggere la tabella; per OGNI riga non PASS leggere il `.out` di quel controllo e i journal del box attorno
   all'ora del guasto e classificarla: (a) nota e attesa (già su Debian: citare la voce del registro), (b) della prova (lo strumento
   presume Debian o altro: dire quale riga di quale file di `prove/`), (c) del prodotto su Ubuntu (dire che cosa si vede, con le righe
   di registro, e in quale file/zona del codice sta probabilmente la causa — senza correggere), (d) dell'ambiente (contenitore, rete,
   macchina carica), (e) non capita. Riportare le righe di registro che provano la classificazione.
3. POI, a giro finito, le verifiche in più elencate nel proprio compito, sulla PROPRIA macchina: sono osservazioni mirate. Per aprire una
   sessione usare gli strumenti di `prove/` (`lib.Rig`, come fa `check-base.py`) in uno script proprio sotto
   `/media/REMOTIX-UBUNTU/lavoro/giro-<de>/` (non nell'albero). Ogni cosa cambiata nel box per una verifica va rimessa com'era e
   dichiarata. Non reinstallare il pacchetto, non fare `box.sh reset`.
4. Mai correggere il prodotto o le prove, mai toccare altre macchine, `/media/REMOTIX-DEBIAN`, gli alberi sul tablet (sola lettura,
   tranne il proprio rapporto). Niente lavori pesanti sul tablet. Uscite lunghe: su file, poi grep/tail.

## Consegna
Un documento `/home/nicfio/Documenti/REMOTIX-UBUNTU/studio/giro1-<de>.md` (italiano; tabella completa PASS/non PASS con la
classificazione e le prove; esito di ogni verifica in più con i valori osservati per intero; che cosa NON è stato possibile vedere), e
come risposta finale un riassunto di al massimo 35 righe: quante righe PASS su quante, elenco dei non PASS con la classe, i difetti
veri del prodotto in ordine di gravità, l'esito delle verifiche in più. Mai scrivere «funziona» per ciò che non è stato osservato.

---
# Aggiunta per il giro di CONFERMA «unione2» (18 nov 2026, notte)
Valgono tutte le regole qui sopra, con queste differenze:
- Il giro si chiama `unione2`: registri in `/media/REMOTIX-UBUNTU/albero/prove/log/unione2-<de>/`, uscita di `all.sh` in
  `/media/REMOTIX-UBUNTU/log/giro-unione2/<de>.out`. Pacchetto: `/media/REMOTIX-UBUNTU/pacchetti/unione2/` (SHA-256 `5bfc4da6…`).
  Cartella propria per script e istantanee: `/media/REMOTIX-UBUNTU/lavoro/giro2-<de>/`. Documento da consegnare:
  `/home/nicfio/Documenti/REMOTIX-UBUNTU/studio/giro2-<de>.md`.
- Rispetto al giro `unione1` (rapporti `studio/giro1-<de>.md`, registri in `prove/log/unione1-<de>/`) il pacchetto contiene tre
  correzioni: (1) KDE: un'uscita chiesta nei primi secondi ora viene completata (e mai forzata con lavoro non salvato aperto);
  (2) Lubuntu: niente più finestra «X Compositor crashed too many times»; (3) strumenti di prova: il rilascio del tasto nel
  trascinamento viene registrato (`mouse-drag`, `tap-and-half-drag-select`), i controlli dei pulsanti tolti sono diventati
  `page-cad-hidden` e `page-ctrl-alt-end-passes`, la misura della finestra nel riattacco non include più i pixel del pannello.
- Il lavoro principale è il CONFRONTO riga per riga con `unione1`: per ogni riga dire se era verde ed è verde, era non verde ed
  è verde (quale correzione l'ha chiusa), era verde ed è NON verde (REGRESSIONE: va capita a fondo, con i journal), era non verde
  e lo è ancora (perché). Le righe nuove o rinominate vanno dette. Una regressione è la cosa più importante del rapporto.
- In più, per ogni macchina: un'istantanea del desktop appena nato di un utente NUOVO a 10 s e a 40 s, guardata con attenzione:
  nessuna finestra di errore o richiesta inattesa (password, portachiavi/portafoglio, assistenti di primo avvio, avvisi di crash).
