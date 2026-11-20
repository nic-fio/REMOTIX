# Regole comuni per gli agenti di sviluppo — REMOTIX per Ubuntu 26.04 (18 nov 2026)

## Il quadro
REMOTIX 1.0.0 esiste per Debian 13. Questo lavoro lo porta su Ubuntu 26.04 nei quattro gusti: Ubuntu (GNOME 50), Kubuntu (KDE 6.6),
Xubuntu (XFCE 4.20), Lubuntu (LXQt 2.3). Il codice di questo albero è SOLO per Ubuntu 26.04: niente rami «se Debian / se Ubuntu»,
niente riconoscimento della distribuzione. Regola del proprietario: una regola generale (la sessione remota si comporta come
l'accesso locale), mai una pezza per un caso. REMOTIX non supporta macchine con più desktop installati.
Piano: `/home/nicfio/Documenti/REMOTIX-UBUNTU/PIANO.md`. Studi (da leggere per il proprio punto): `/home/nicfio/Documenti/REMOTIX-UBUNTU/studio/1..8-*.md`.
Vecchio albero 1.5.x, SOLA LETTURA, fonte delle cure già provate su Ubuntu 26.04: `/home/nicfio/Documenti/REMOTIX`.
Codice Debian, SOLA LETTURA: `/home/nicfio/Documenti/REMOTIX-DEBIAN`.

## Dove si lavora
- Ogni agente ha una COPIA sua dell'albero: `/home/nicfio/Documenti/REMOTIX-UBUNTU-lavori/<nome>/` (senza git). Si modifica SOLO lì,
  e solo i file elencati nel proprio compito. `/home/nicfio/Documenti/REMOTIX-UBUNTU-lavori/base/` è la copia di riferimento
  intatta: non toccarla (serve per i diff). Non modificare `/home/nicfio/Documenti/REMOTIX-UBUNTU` (albero principale), né gli
  altri alberi, né le copie degli altri agenti.
- Niente compilazioni, podman o lavori pesanti sul tablet. Si costruisce sul server: `ssh -o BatchMode=yes nicfio@192.168.0.2 'export TERM=dumb; ...'`.
  Cartella propria sul server: `/media/REMOTIX-UBUNTU/lavoro/<nome>/` (albero copiato con `tar | ssh`: sul tablet non c'è rsync).
  Costruzione (circa 2 minuti), in background con output su file:
  `cd /media/REMOTIX-UBUNTU/lavoro/<nome>/albero && SOURCE_DATE_EPOCH=1763424000 OUTPUT=/media/REMOTIX-UBUNTU/pacchetti/<nome> RX_VERSION=1.0.0 build/build-deb.sh`
  Dei log si leggono solo le code e i grep. Il codice deve compilare senza avvisi nuovi.
- Macchine di prova (un altro agente le sta finendo; controlla con `podman ps`/`boxes/box.sh status` dalla copia sul server
  `/media/REMOTIX-UBUNTU/albero/boxes/`): contenitori `rxu-gnome`, `rxu-kde`, `rxu-xfce`, `rxu-lxqt`; ssh 2221..2224; REMOTIX 8821..8824
  (gnome, kde, xfce, lxqt). `box.sh install <de> <x.deb>`, `box.sh ssh <de> [cmd]`, `box.sh reset <de>`. Ogni agente usa SOLO il box
  assegnato nel suo compito. Se il box non è ancora pronto quando il codice compila, riprova ogni qualche minuto per al massimo
  40 minuti; se non arriva, consegna dicendo chiaramente «non verificato dal vivo».
- Verifica dal vivo consentita: installare il PROPRIO pacchetto nel PROPRIO box e controllare il proprio punto (journal del servizio,
  processi, file, variabili; e il controllo base `python3 check-base.py --box <de> --browser chrome` dalla propria copia di `prove/`
  sul server — lì, e solo lì, se serve si può mettere in `prove/lib.py` la mappa delle porte Ubuntu `{"gnome": 8821, "kde": 8822,
  "xfce": 8823, "lxqt": 8824}` come aiuto temporaneo, dichiarandolo). NON lanciare `all.sh` né giri completi: i giri li decide il proprietario.

## Divieti assoluti
- MAI cancellare, spostare o sovrascrivere ciò che non si è creato in questo compito. Non toccare `/media/REMOTIX-DEBIAN`, le immagini e i
  contenitori Debian, i box e le cartelle degli altri agenti. Nessun `podman system prune`/`rmi`.
- Niente commit git, niente push, niente pubblicazione. Nessun dato personale nei file (il responsabile del pacchetto è `remotix@nicfio.it`).
- Non allargare il compito: se serve toccare un file fuori dall'elenco, o se il compito non regge, fermarsi e dirlo nel rapporto.
- Commenti nel codice in inglese, nello stile del file. Si riusa il vecchio codice dove era già provato; nel dubbio si tiene il
  vecchio comportamento e si annota il dubbio. Niente codice morto, niente rami per altre distro.

## Consegna
Rapporto finale in italiano, massimo 40 righe: (1) che cosa è cambiato, file per file, con il perché; (2) `diff -ru` rispetto a
`base` salvato in `/home/nicfio/Documenti/REMOTIX-UBUNTU-lavori/<nome>.diff` (solo i propri file); (3) esito della costruzione
(errori, avvisi, lintian); (4) che cosa è stato verificato dal vivo e come, con le righe di registro che lo provano, e che cosa NO;
(5) dubbi, rischi, cose trovate fuori compito. Mai scrivere «funziona» per ciò che non è stato osservato.
