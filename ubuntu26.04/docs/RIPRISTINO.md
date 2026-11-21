# RIPRISTINO — rifare REMOTIX (Ubuntu 26.04) da zero, partendo solo dal repo

BOZZA del 20 nov 2026. Vale per la cartella `ubuntu26.04/` del ramo `main` del repo pubblico `https://github.com/nic-fio/REMOTIX`.

Il 20 nov 2026 il repo è stato riordinato: un solo ramo `main` con una cartella per distribuzione (`debian13/`, `ubuntu26.04/`). **Dopo il riordino la costruzione del pacchetto è stata riprovata lo stesso giorno** dalla forma nuova, con i comandi scritti qui sotto: impronta identica a quella attesa. Le altre marche PROVATO (preparazione del server, manuali) valgono per la prova fatta poche ore prima sulla forma precedente a due rami. Nota pratica: via ssh la costruzione va lanciata in modo che sopravviva alla chiusura del collegamento (`setsid nohup … &`), con il registro fuori dall'albero del repo.

Ogni passo è marcato:

- **PROVATO** = eseguito il 20 nov 2026 su un server pulito, partendo da un clone fresco del repo, senza altro materiale.
- **NON RIPROVATO** = scritto nel repo o nei manuali, ma non rieseguito in questa prova. Il banco a macchine virtuali (passo 6) **non** è stato ricreato.

Segnaposto usati qui: `<UTENTE>` = l'utente normale del server (con `sudo`), `<IP-SERVER>` = l'indirizzo del server
di sviluppo, `<CARTELLA>` = dove si clona il repo (nella prova: una cartella nuova sotto `/media/`).

## 1. Che cosa serve

| Cosa | Dettaglio | Stato |
|---|---|---|
| Un server di sviluppo | **Debian 13** (anche per costruire il pacchetto Ubuntu: si costruisce in un container Ubuntu 26.04), x86-64, rete, un disco persistente montato su `/media`. Nella prova: 20 processori, 31 GB di RAM; il sistema gira dalla RAM (a ogni riavvio si perde tutto fuori da `/media`). Per la sola costruzione bastano molta meno RAM e processori. | PROVATO |
| Un utente normale con `sudo` | Gli script usano `echo \| sudo -S`, cioè **`sudo` senza password**. Altrimenti gli script di preparazione non vanno. | PROVATO |
| Rete dal server | `github.com` (clone del repo; la costruzione clona `ngtcp2`, `nghttp3` e scarica `labwc` 0.9.3), `gitlab.freedesktop.org` (`wlroots` 0.19.2), `docker.io` (immagine `ubuntu:26.04`), i server dei pacchetti Ubuntu (con `universe`). I due sorgenti `labwc` e `wlroots` sono controllati con sha256 scritti in `build/labwc-ospite/VERSIONS`. | PROVATO |
| `git` e `podman` | Li installa `server/prepara-server.sh` (passo 3). | PROVATO |
| Per il banco a macchine virtuali (passo 6) | Una scheda video dedicata da cedere alle macchine virtuali (nel repo: una Radeon RX 6800), IOMMU attivo, QEMU/KVM, le ISO. Vedi passo 6. | NON RIPROVATO |
| Il tablet | Solo testo. **Mai** compilare sul tablet. | — |

## 2. Clonare il repo (sul server)

```
mkdir -p <CARTELLA> && cd <CARTELLA>
git clone https://github.com/nic-fio/REMOTIX
cd REMOTIX/ubuntu26.04
```

PROVATO.

## 3. Preparare il server

Dopo ogni riavvio del server (sistema in RAM), **dal clone**, come utente normale (non root):

```
bash <CARTELLA>/REMOTIX/ubuntu26.04/server/prepara-server.sh
```

PROVATO: finisce con `ALL OK`. Fa, in ordine: nome macchina in `/etc/hosts`; cartelle di lavoro in `/media/REMOTIX-UBUNTU/`;
installa `podman` e gli aiuti; configura podman (se manca) con le immagini su disco in **`/media/REMOTIX-DEBIAN/podman/`** (lo spazio
di podman è condiviso con il lavoro Debian: il nome «DEBIAN» è voluto, non va cambiato); limiti `inotify`; poi pacchetti per le
**prove** (Chromium, Firefox ESR, `labwc`, PipeWire, QEMU, `ovmf`, `xorriso`, `gdisk`, `dosfstools`), un server audio di prova, accesso a `/dev/kvm`;
infine `podman run ubuntu:26.04` come utente e come root. Ripetibile senza danni.

Cose da sapere (PROVATO):

- Percorsi fissi scritti nello script: `/media/REMOTIX-UBUNTU` (cartelle) e `/media/REMOTIX-DEBIAN` (spazio di podman). `/media` deve essere scrivibile con `sudo`.
- Per la **sola costruzione** servono solo `podman`, `uidmap`, `passt`, `slirp4netns`, `fuse-overlayfs`, `crun`, `git`, `curl`, `ca-certificates` e la configurazione di podman; il resto è per le prove.
- Via `ssh` senza terminale compare `tput: No value for $TERM`: innocua.

## 4. Costruire il pacchetto

Pacchetto di riferimento: `remotix_1.0.0-1+ubuntu26.04_amd64.deb`, sha256 atteso:

```
08772d85d0b13298ee211e43b61ecf7295a3cce1713bef933dcadee4f46736ab
```

Comando (PROVATO; stima: una decina di minuti la prima volta, con l'immagine di costruzione da fare da zero; non cronometrato):

```
cd <CARTELLA>/REMOTIX/ubuntu26.04
SOURCE_DATE_EPOCH=1795130069 RX_VERSION=1.0.0 RX_REVISION=1 \
  OUTPUT=<CARTELLA>/pacchetti  build/build-deb.sh > costruzione.log 2>&1 &
```

- `RX_VERSION=1.0.0`, `RX_REVISION=1`: danno la versione `1.0.0-1+ubuntu26.04`. Senza, `1.0.0~dev`.
- `SOURCE_DATE_EPOCH=1795130069` (= 19 nov 2026, 23:14:29 UTC): la data di costruzione scritta nel pacchetto. **Non è scritta
  da nessuna parte nel repo**: l'ho ricavata dal `.buildinfo` del pacchetto di riferimento (riga `SOURCE_DATE_EPOCH=`). Da un clone fresco
  lo script ne calcolerebbe uno diverso e il pacchetto uscirebbe diverso.
- `OUTPUT`: dove vanno i risultati. Senza, `/media/REMOTIX-UBUNTU/pacchetti`.

Risultato in `OUTPUT`: il `.deb`, il `.buildinfo`, `costruzione.log`, `immagine.log`, `lintian.txt`, `controlli.txt`, `elenco.txt` e, in più rispetto a Debian,
`remotix-1.0.0-labwc-source.tar.gz` (+ `.sha256`: il sorgente del nostro `labwc`, che per la licenza GPL va pubblicato con il pacchetto).
Controlli attesi: `lintian: E=0 W=0`; `controlli.txt` con sei righe `SI`; il tarball dei sorgenti deve avere sha256
`14805f925fb6901e1e86549b2dec2c1b465a2229de0deeb7819de60a51fcf271` (PROVATO: identico al riferimento).

### 4.1 L'impronta: una trappola con le date dei file

PROVATO. Costruendo **così com'è** da un clone fresco l'impronta esce diversa:

```
5ab79829f84d0fa664058e1af46f301df6a78a00cdcda81214b0fe23684b15de
```

Il pacchetto è identico in tutto (stessi file, contenuto uguale byte per byte, stesso binario, stesse dipendenze, stesso `labwc`)
tranne **la data di modifica di 4 file**. Motivo: `git` non conserva le date dei file; il pacchetto tiene la data del file se più vecchia di
`SOURCE_DATE_EPOCH`, altrimenti usa l'epoca. Nel riferimento 4 file avevano la data di quando erano stati scritti (18 nov), nel clone fresco hanno la data del clone.

| File nel repo | Data nel riferimento (secondi dall'epoca Unix) |
|---|---|
| `debian/remotix.service` | 1795012701 (18 nov 2026, 15:38) |
| `debian/remotix.tmpfiles` | 1795012701 |
| `debian/remotix.lintian-overrides` | 1795012701 |
| `debian/needrestart/remotix.conf` | 1795013328 (18 nov 2026, 15:48) |

Per ottenere **esattamente** l'impronta attesa, prima di costruire:

```
cd <CARTELLA>/REMOTIX/ubuntu26.04
touch -d @1795012701 debian/remotix.service debian/remotix.tmpfiles debian/remotix.lintian-overrides
touch -d @1795013328 debian/needrestart/remotix.conf
```

Con questi `touch` e l'epoca sopra, la costruzione ha dato **08772d85…6736ab**, uguale al riferimento (PROVATO).

Verifica alternativa del solo contenuto (PROVATO):

```
mkdir x && dpkg-deb -x remotix_1.0.0-1+ubuntu26.04_amd64.deb x
(cd x && find . -type f -exec sha256sum {} + | sort -k2 | sha256sum)
# atteso: b3c12e4b64249a2e67bf48e461c9924846a0582cac9e1d74ea5d56f2a4d0c09a
```

Nella prova (il giorno dopo la costruzione di riferimento) le librerie e gli strumenti di Ubuntu erano gli stessi. Se in futuro
Ubuntu li aggiorna (il `.buildinfo` del riferimento elenca le versioni esatte), l'impronta cambierà anche con tutto il resto uguale: non è un errore del repo.

## 5. Rigenerare i manuali

PROVATO. Servono `python3`, `python3-pygments`, `python3-pil` (`sudo apt-get install python3-pygments python3-pil`).

```
cd <CARTELLA>/REMOTIX/ubuntu26.04
python3 manuals/sources/build.py            # riscrive «Technical Manual — Ubuntu 26.04.html» e «User Manual — Ubuntu 26.04.html»
python3 manuals/sources/build.py --check    # «manual aligned with the code» se allineati al codice
```

Nella prova i due file rigenerati sono **identici byte per byte** a quelli del repo (`git status` pulito). I manuali di Debian stanno nella cartella `debian13/`.

## 6. Il banco di prova: quattro macchine virtuali con la scheda video ceduta

NON RIPROVATO (nessuna macchina virtuale è stata creata in questa prova). Quanto segue è letto da `server/vm-radeon.sh` e dai file in `docs/`
e `manuals/` (capitolo «The VM bench» del manuale tecnico, `docs/STORIA-ubuntu-26.04.md`, `studio/8-pacchetto-e-prove.md`).

**Idea.** Quattro macchine virtuali QEMU/KVM con UEFI, una per gusto di Ubuntu, installate davvero da ISO; la scheda video del server
(passthrough `vfio-pci`) va a **una sola macchina per volta**. Disco 40 GB, 12 GB di memoria, 8 processori ciascuna.

| Nome | Desktop | ISO attesa da `vm-radeon.sh` | Porte ssh / REMOTIX |
|---|---|---|---|
| `ubuntu` | gnome | `ubuntu-26.04.1-desktop-amd64.iso` (installazione automatica) | 2341 / 8841 |
| `kubuntu` | kde | `kubuntu-26.04.1-desktop-amd64.iso` | 2342 / 8842 |
| `xubuntu` | xfce | `xubuntu-26.04.1-desktop-amd64.iso` | 2343 / 8843 |
| `lubuntu` | lxqt | `lubuntu-26.04.1-desktop-amd64.iso` | 2344 / 8844 |

**Preparazione dell'hardware (cose NON nel codice, ma nei documenti).**

1. Il server va avviato con questi parametri del kernel (da `docs/STORIA-ubuntu-26.04.md` e dal manuale tecnico): 
   `intel_iommu=on iommu=pt vfio-pci.ids=1002:73bf,1002:ab28 modprobe.blacklist=amdgpu`.
   I due codici `1002:73bf` e `1002:ab28` sono quelli **di quella Radeon RX 6800** (scheda e sua uscita audio). Con un'altra scheda vanno cambiati.
2. Gli indirizzi PCI della scheda sono scritti dentro `server/vm-radeon.sh`: `GPU=0000:03:00.0` e `GPUA=0000:03:00.1`. Su un'altra macchina
   si controllano con `lspci -nn` e si correggono nello script. Il server aveva anche una grafica Intel integrata, che resta al server.
3. Pacchetti QEMU, OVMF e strumenti disco: li installa `prepara-server.sh` (passo 3). Lo script cerca il firmware UEFI in
   `/usr/share/OVMF/OVMF_CODE_4M.fd` e `OVMF_VARS_4M.fd`.
4. Le ISO vanno scaricate a mano in **`/media/DOWNLOAD/`** (percorso fisso nello script). Cartelle ufficiali (da `studio/8-pacchetto-e-prove.md`, non riverificate oggi;
   ogni cartella ha `SHA256SUMS`): `https://releases.ubuntu.com/26.04/`, `https://cdimage.ubuntu.com/kubuntu/releases/26.04/release/`,
   `https://cdimage.ubuntu.com/xubuntu/releases/26.04/release/`, `https://cdimage.ubuntu.com/lubuntu/releases/26.04/release/`.
   Dal 21 nov 2026 lo script si aspetta per tutti e quattro i file `…26.04.1…` (prima tre erano senza `.1`): controllare comunque il nome esatto in cartella.
5. Tutti i comandi di `vm-radeon.sh` hanno percorsi fissi in `/media/REMOTIX-UBUNTU/vm-radeon/` e vogliono `sudo` senza password.

**Comandi** (da `server/vm-radeon.sh`, uno per volta; la scheda è una sola e uno `.lock` impedisce due comandi insieme):

```
server/vm-radeon.sh crea <nome>            # crea disco e macchina (ubuntu: installazione automatica; gli altri tre: disco costruito dagli strati squashfs della ISO); dieci minuti circa
server/vm-radeon.sh prova-avvio <nome>     # avvio di controllo SENZA la scheda; poi spegne
server/vm-radeon.sh accendi <nome>         # cede la scheda e accende (attende ssh fino a 6 minuti)
server/vm-radeon.sh spegni <nome>          # spegne e restituisce la scheda al server
server/vm-radeon.sh istantanea <nome> <etichetta>   # copia dello stato del disco (macchina spenta)
server/vm-radeon.sh ripristina <nome> <etichetta>   # torna a quella copia (macchina spenta; comando esplicito)
```

Gli utenti di prova delle macchine (nomi e password) sono scritti in `server/vm-radeon.sh`. Una chiave `ssh` del banco (`vmkey`) si crea dentro la cartella di ogni macchina.

**Installare il pacchetto in una macchina**, come farebbe un amministratore (da `server/vm-radeon-installa.sh`):

```
server/vm-radeon-installa.sh <nome> <pacchetto.deb> [etichetta]
```

Altri script nella stessa cartella: `vm-radeon-aggiorna.sh` (aggiorna una macchina come farebbe un utente), `vm-radeon-controllo.sh` (controllo breve con la scheda),
`server/vm.sh` (una macchina Ubuntu più semplice da immagine cloud `ubuntu-26.04-server-cloudimg-amd64.img`, da scaricare da `cloud-images.ubuntu.com`),
`server/live-installa.sh` (installatore di prova per una macchina reale avviata da una ISO live: scarica da un server web a un indirizzo e una porta scritti dentro lo script (variabile `SORGENTE`), da cambiare).

## 7. Lanciare le prove

NON RIPROVATO. Le prove sono in `prove/`; `prove/all.sh` esegue **tutti** i controlli su un desktop, in sequenza, un log per controllo
in `prove/log/<tag>/` e una tabella in `summary.txt`; esce con 0 solo se ogni riga è PASS.

Sul banco a macchine virtuali (il banco della versione finale):

```
cd <CARTELLA>/REMOTIX/ubuntu26.04/prove
RX_BANCO=vm ./all.sh gnome --fresh <percorso del .deb>     # macchina «ubuntu»: stato pulito, installa il pacchetto, poi tutti i controlli
RX_BANCO=vm ./all.sh gnome --clean                          # stato pulito, senza reinstallare
```

`gnome`, `kde`, `xfce`, `lxqt` corrispondono a `ubuntu`, `kubuntu`, `xubuntu`, `lubuntu`. Una macchina alla volta. Prima delle prove, una volta per macchina,
va messa la chiave del banco per l'utente root (`prove/banco-vm/box.sh rootkey <desktop>`). `RX_TEMPO=2` (il valore standard sul banco VM) raddoppia i tempi limite.
Il controllo `check-ban` sta sempre per ultimo e da solo.

Sul banco a **container** (vecchio, ma ancora nel repo): `boxes/box.sh build|boot|install|reset <desktop>` e poi `prove/all.sh <desktop> --fresh <deb>` senza `RX_BANCO`.
Immagini grandi, molta rete; NON RIPROVATO.

Regola del proprietario: le prove le decide e le lancia lui, non partono da sole.

## 8. Che cosa non si trova nel repo (elenco completo di questa prova)

1. Il valore `SOURCE_DATE_EPOCH=1795130069`.
2. Le quattro date dei file del passo 4.1.
3. `sudo` senza password per l'utente (gli script usano `echo | sudo -S`).
4. I percorsi fissi: `/media/REMOTIX-UBUNTU/...` (script, `build-deb.sh`, `prove/fresh.sh`, banco VM), `/media/REMOTIX-DEBIAN/podman` (immagini podman, **condiviso con Debian**), `/media/DOWNLOAD/` (le ISO).
5. L'ordine: clone (un solo clone per tutte le distribuzioni), poi `cd ubuntu26.04`, `prepara-server.sh`, `build-deb.sh`.
6. La rete: `github.com`, `gitlab.freedesktop.org`, `docker.io`, i server dei pacchetti Ubuntu devono essere raggiungibili dal server (e il server di costruzione è Debian 13, non Ubuntu).
7. `python3-pygments` e `python3-pil` per i manuali (nell'intestazione di `build.py`, ma non installati da `prepara-server.sh`).
8. Il file di impronte di riferimento: i due sha256 sono qui, non nel repo.
9. (NON RIPROVATO) I parametri del kernel per il passthrough sono nei documenti (`docs/`, manuale), non in uno script. I codici `1002:73bf,1002:ab28` e gli indirizzi `03:00.0/03:00.1` valgono solo per quella scheda e quella macchina.
10. (NON RIPROVATO) Le ISO: scaricate a mano, nomi dei file diversi fra studio e script (passo 6, punto 4).
11. (NON RIPROVATO) Un indirizzo fisso del server scritto in `server/live-installa.sh`.
