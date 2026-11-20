# Regole comuni per gli agenti di studio (18 nov 2026)

Scopo: studio a fondo, PRIMA di scrivere codice, di ciò che serve per portare REMOTIX 1.0.0 (oggi solo Debian 13)
su Ubuntu 26.04 nei quattro gusti: Ubuntu (GNOME), Kubuntu (KDE), Xubuntu (XFCE), Lubuntu (LXQt).
È solo studio: non si scrive codice del prodotto, non si costruisce, non si prova il prodotto.

## Dove leggere
- Codice attuale (Debian 13, 1.0.0): `/home/nicfio/Documenti/REMOTIX-DEBIAN` — `CLAUDE.md`, `PIANO.md`,
  `docs/REGISTRO-problemi.md`, `docs/PULIZIA-tranche1.md` (pezzi tolti perché morti su Debian, molti servivano a Ubuntu),
  `docs/INVENTARIO-non-debian.md`, `docs/DECISIONS*.md`, `docs/LESSONS.md`, `src/`, `debian/`, `build/`, `boxes/`, `prove/`.
- Vecchio albero multi-distro 1.5.x (ritirato; lì Ubuntu 26.04 era già stata portata e provata):
  `/home/nicfio/Documenti/REMOTIX` — `src/`, `packaging/`, `assessment/<desktop>/ubuntu2604.md`, `CHANGES-1.5.md`,
  `DECISIONS*.md`, `benches/`. È memoria: serve a capire i problemi e le cure già trovate.
- Piano Ubuntu: `/home/nicfio/Documenti/REMOTIX-UBUNTU/PIANO.md`.
- Fatti veri su Ubuntu 26.04: sul server di sviluppo, in un contenitore usa-e-getta (vedi sotto). Il web solo come ripiego,
  dichiarandolo.

## Server (fatti veri su Ubuntu 26.04)
- `ssh -o BatchMode=yes nicfio@192.168.0.2 'export TERM=dumb; ...'`. L'immagine `docker.io/library/ubuntu:26.04` è già scaricata.
- Ogni agente usa UN contenitore suo, di nome `studio-<N>` (N = il proprio numero), e UNA cartella sua
  `/media/REMOTIX-UBUNTU/studio/<N>/` (crearla; montarla con `-v`). Esempio:
  `podman run -d --name studio-<N> -v /media/REMOTIX-UBUNTU/studio/<N>:/w docker.io/library/ubuntu:26.04 sleep infinity`
  poi `podman exec studio-<N> ...`.
- Dentro il contenitore si può: `apt-get update`, `apt-cache policy/show/depends`, `apt-get download`, `dpkg-deb -x`,
  `apt-get source` (abilitare `deb-src` in `/etc/apt/sources.list.d/ubuntu.sources`), `apt-file`, installare pacchetti per
  leggerne i file. Servono le versioni e i file VERI dei pacchetti di Ubuntu 26.04, e i sorgenti quando serve capire un comportamento.
- Vietato sul server: toccare `/media/REMOTIX-DEBIAN` (in nessun modo), toccare contenitori o cartelle altrui, usare sudo,
  avviare REMOTIX, lanciare prove. Alla fine fermare e togliere SOLO il proprio contenitore `studio-<N>`; lasciare la propria cartella.
- Uscite lunghe: su file nella propria cartella, poi leggere solo ciò che serve (grep, head).

## Vietato sul tablet (questa macchina)
- Modificare, spostare, cancellare qualunque file nei due alberi `REMOTIX` e `REMOTIX-DEBIAN`.
- Compilare, clonare repository grossi, installare pacchetti, lavori pesanti.
- L'unico file che si scrive è il proprio documento di studio (vedi sotto).

## Che cosa si consegna
1. Un documento `/home/nicfio/Documenti/REMOTIX-UBUNTU/studio/<N>-<nome>.md`, in italiano (termini tecnici in originale),
   dettagliato quanto serve a chi poi scriverà il codice: fatti con la fonte (percorso:riga nei due alberi, pacchetto e
   versione Ubuntu, file sorgente upstream), distinguendo sempre **[V] verificato** (dove), **[W] dal web**, **[S] supposizione**.
   Deve chiudersi con: «Problemi da affrontare» (elenco numerato: che cosa, dove nel codice, peso piccolo/medio/grande,
   cura già nota nel vecchio albero sì/no e dove), «Che cosa non si può sapere senza provare» e «Prove consigliate».
2. Come risposta finale: un riassunto di al massimo 40 righe con le scoperte principali, i problemi da affrontare con il peso,
   le incognite, e ogni fatto che contraddice il piano o gli studi precedenti.
