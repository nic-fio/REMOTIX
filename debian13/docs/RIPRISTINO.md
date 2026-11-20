# RIPRISTINO — rifare REMOTIX (Debian 13) da zero, partendo solo dal repo

BOZZA del 20 nov 2026. Vale per la cartella `debian13/` del ramo `main` del repo pubblico `https://github.com/nic-fio/REMOTIX`.

Il 20 nov 2026 il repo è stato riordinato: un solo ramo `main` con una cartella per distribuzione (`debian13/`, `ubuntu26.04/`). **Dopo il riordino i comandi qui sotto sono aggiornati ma la costruzione NON è stata riprovata** (verrà riprovata a parte): le marche PROVATO sotto valgono per la forma precedente del repo (un ramo per distribuzione, clone nella cartella `debian`).

Ogni passo è marcato:

- **PROVATO** = eseguito il 20 nov 2026 su un server pulito, partendo da un clone fresco del repo, senza altro materiale.
- **NON RIPROVATO** = scritto nel repo o nei manuali, ma non rieseguito in questa prova.

Segnaposto usati qui: `<UTENTE>` = l'utente normale del server (con `sudo`), `<IP-SERVER>` = l'indirizzo del server
di sviluppo, `<CARTELLA>` = dove si clona il repo (nella prova: una cartella nuova sotto `/media/`).

## 1. Che cosa serve

| Cosa | Dettaglio | Stato |
|---|---|---|
| Un server di sviluppo | Debian 13 (trixie), x86-64, rete, un disco persistente montato su `/media`. Nella prova: 20 processori, 31 GB di RAM; il sistema gira dalla RAM (a ogni riavvio si perde tutto fuori da `/media`). Per la sola costruzione del pacchetto bastano molta meno RAM e processori. | PROVATO |
| Un utente normale con `sudo` | Gli script usano `echo \| sudo -S`, cioè **`sudo` senza password** per quell'utente. Se `sudo` chiede una password, gli script di preparazione non vanno (da cambiare gli script o la configurazione di `sudo`). | PROVATO |
| Accesso alla rete dal server | `github.com` (clone del repo; la costruzione clona `ngtcp2` e `nghttp3`), `docker.io` (immagine `debian:trixie`), i server dei pacchetti Debian. Nessun altro. | PROVATO |
| `git` e `podman` sul server | Li installa `server/prepara-server.sh` (vedi passo 3). | PROVATO |
| Il tablet | Serve solo per leggere e scrivere testo. **Mai** compilare sul tablet. | — |

Non servono: Go, i vecchi repository, la cartella `benches/`, copie locali. Nella prova non c'era nulla di REMOTIX sul server.

## 2. Clonare il repo (sul server)

```
mkdir -p <CARTELLA> && cd <CARTELLA>
git clone https://github.com/nic-fio/REMOTIX
cd REMOTIX/debian13
```

PROVATO. (La cartella `ubuntu26.04/` è un altro pacchetto, vedi la sua `docs/RIPRISTINO.md`.)

## 3. Preparare il server

Dopo ogni riavvio del server (il sistema è in RAM) si lancia, **dal clone**, come utente normale (non root):

```
bash <CARTELLA>/REMOTIX/debian13/server/prepara-server.sh
```

PROVATO: finisce con `ALL OK`. Fa, in ordine: mette il nome della macchina in `/etc/hosts`; crea le cartelle di lavoro sotto
`/media/REMOTIX-DEBIAN/`; installa `podman` e i suoi aiuti (`uidmap passt slirp4netns fuse-overlayfs crun git rsync curl`);
scrive la configurazione di podman (le immagini stanno sul disco, in `/media/REMOTIX-DEBIAN/podman/`, non in RAM);
alza i limiti di `inotify`; poi installa cose che servono **solo alle prove**, non alla costruzione (Chromium, Firefox ESR,
`labwc`, PipeWire, QEMU), avvia un server audio di prova e dà all'utente l'accesso a `/dev/kvm`. Infine prova `podman run debian:trixie`
come utente e come root. È ripetibile senza danni.

Cose da sapere (PROVATO):

- Lo script scrive **percorsi fissi**: `/media/REMOTIX-DEBIAN/...` per cartelle e per lo spazio di podman. Quindi `/media` deve esistere
  e essere scrivibile con `sudo`. Per cambiare cartella bisogna modificare lo script (la variabile `BASE`).
- Per **sola costruzione** basta una parte: `podman`, `uidmap`, `passt`, `slirp4netns`, `fuse-overlayfs`, `crun`, `git`, `curl`,
  `ca-certificates` e la configurazione di podman. I pacchetti per le prove (Chromium, Firefox, QEMU...) non servono per costruire;
  nella prova sono stati installati lo stesso perché lo script li installa sempre.
- Durante il lancio via `ssh` senza terminale compare la riga `tput: No value for $TERM`: è innocua.

## 4. Costruire il pacchetto

Il pacchetto di riferimento è `remotix_1.0.0-1+deb13_amd64.deb`, impronta sha256 attesa:

```
421b0e4b39a4663f815e17b6a7b6fe5da07e97b91177a43f41ff475441cecf92
```

Comando (PROVATO, stima: una decina di minuti la prima volta, con l'immagine di costruzione da fare da zero; non cronometrato):

```
cd <CARTELLA>/REMOTIX/debian13
SOURCE_DATE_EPOCH=1795130069 RX_VERSION=1.0.0 RX_REVISION=1 \
  OUTPUT=<CARTELLA>/pacchetti  build/build-deb.sh > costruzione.log 2>&1 &
```

Spiegazione dei valori:

- `RX_VERSION=1.0.0`, `RX_REVISION=1`: danno la versione `1.0.0-1+deb13`. Senza, lo script usa `1.0.0~dev`.
- `SOURCE_DATE_EPOCH=1795130069` (= 19 nov 2026, 23:14:29 UTC): la «data di costruzione» scritta nel pacchetto. **Questo valore non è
  scritto da nessuna parte nel repo**: l'ho ricavato dal file `.buildinfo` del pacchetto di riferimento (riga `SOURCE_DATE_EPOCH=`).
  Da un clone fresco lo script ne calcolerebbe uno diverso (la data del clone), e il pacchetto uscirebbe diverso.
- `OUTPUT`: dove finiscono i risultati. Senza, lo script scrive in `/media/REMOTIX-DEBIAN/pacchetti`.

Il risultato (nella cartella `OUTPUT`): il `.deb`, il `.buildinfo`, `costruzione.log`, `immagine.log`, `lintian.txt`,
`controlli.txt`, `elenco.txt`. Controlli attesi: `lintian: E=0 W=0` e in `controlli.txt` quattro righe `SI` (R13 ×2, R14, R4).

### 4.1 L'impronta: una trappola con le date dei file

PROVATO. Se si costruisce **così com'è** da un clone fresco, l'impronta esce diversa:

```
8c4afdc11fdd3012e1fcd8eb4b25365c08751d02a432611e4925776669e35d9d
```

Il pacchetto è identico in tutto (stessi file, stesso contenuto byte per byte, stesso binario, stesso elenco di dipendenze)
tranne **la data di modifica di 3 file**. Il motivo: `git` non conserva le date dei file; il pacchetto prende la data del file
se è più vecchia di `SOURCE_DATE_EPOCH`, altrimenti la data viene portata a `SOURCE_DATE_EPOCH`. Nel pacchetto di riferimento
3 file avevano la data in cui erano stati scritti (17 nov), nel clone fresco hanno la data del clone (dopo l'epoca).

I tre file e le date del riferimento (secondi dall'epoca Unix):

| File nel repo | Data nel riferimento |
|---|---|
| `debian/remotix.service` | 1794944120 (17 nov 2026, 20:35) |
| `debian/remotix.tmpfiles` | 1794944092 (17 nov 2026, 20:34) |
| `debian/remotix.lintian-overrides` | 1794931143 (17 nov 2026, 16:59) |

Per ottenere **esattamente** l'impronta attesa, prima di costruire:

```
cd <CARTELLA>/REMOTIX/debian13
touch -d @1794944120 debian/remotix.service
touch -d @1794944092 debian/remotix.tmpfiles
touch -d @1794931143 debian/remotix.lintian-overrides
```

Con questi tre `touch` e l'epoca sopra, la costruzione ha dato **421b0e4b…cecf92**, uguale al riferimento (PROVATO).

Se non si vogliono fare i `touch`, si può verificare l'uguaglianza del contenuto così (PROVATO; due pacchetti uguali nel contenuto
danno la stessa impronta finale):

```
mkdir x && dpkg-deb -x remotix_1.0.0-1+deb13_amd64.deb x
(cd x && find . -type f -exec sha256sum {} + | sort -k2 | sha256sum)
# atteso: b7c599dc9c466f01f5159ecc4ae9c168cd3dec8a34d78b153b220bdf6e4a83cd
```

La costruzione non dipende dalle versioni delle librerie del momento nel modo che si temeva: nella prova (20 nov, il giorno dopo
la costruzione di riferimento) le librerie di Debian erano le stesse. Se in futuro Debian aggiorna librerie o compilatore
(`.buildinfo` del riferimento elenca le versioni esatte usate), l'impronta cambierà anche con tutto il resto uguale: in quel caso
non è un errore del repo.

## 5. Rigenerare i manuali

PROVATO. I manuali in `manuals/*.html` si generano da `manuals/sources/`. Servono `python3`, `python3-pygments` e `python3-pil`
(sul server: `sudo apt-get install python3-pygments python3-pil`; `python3-pil` c'era già).

```
cd <CARTELLA>/REMOTIX/debian13
python3 manuals/sources/build.py            # riscrive i due manuali (Technical e User, Debian 13)
python3 manuals/sources/build.py --check    # dice «manual aligned with the code» se sono allineati al codice
```

Risultato nella prova: i due file rigenerati sono **identici byte per byte** a quelli del repo (`git status` pulito dopo la generazione).
Nessun clone, nessuna data da passare. Si lancia sul server o su una macchina con python (è solo testo, ma meglio il server).

## 6. Il banco di prova (container) e le prove

NON RIPROVATO in questa prova (scritto nel repo). Il banco è un container `podman` con systemd per ogni desktop
(`xfce`, `lxqt`, `gnome`, `kde`), senza REMOTIX dentro: il pacchetto si installa con `apt`.

Ordine dei comandi (dalle intestazioni di `boxes/box.sh`, `prove/fresh.sh`, `prove/all.sh`):

1. Preparare il server (passo 3) e costruire il pacchetto (passo 4).
2. Costruire le immagini: `boxes/box.sh build xfce` (e `lxqt`, `gnome`, `kde`). Ogni immagine installa il desktop completo
   (`task-<desktop>-desktop`) da Debian: molto tempo e molta rete. La chiave `ssh` del banco (`boxes/box-key`) si crea da sola alla prima volta.
3. Accendere: `boxes/box.sh boot xfce`. Stato: `boxes/box.sh status`. Porte: ssh 2211-2214, REMOTIX 8811-8814.
4. Lanciare le prove di un desktop, in `prove/`: `prove/all.sh xfce --fresh <percorso del .deb>` (azzera il box, installa il pacchetto, abilita
   il servizio, poi lancia tutti i controlli uno dopo l'altro, un log per controllo in `prove/log/<tag>/` e la tabella in `summary.txt`).
   Esce con 0 solo se ogni riga è PASS. I quattro desktop si possono lanciare insieme.
   Senza `--fresh`, `prove/fresh.sh` e `all.sh` cercano il `.deb` più recente in `/media/REMOTIX-DEBIAN/pacchetti`.
5. Per i controlli servono sul server Chromium, Firefox ESR, `labwc`, PipeWire (installati da `prepara-server.sh`, passo 3).

Regola del proprietario: le prove le decide e le lancia lui, non partono da sole.

La macchina virtuale di `server/vm.sh` (Debian 13 «genericcloud» sotto KVM, porte ssh 2301 e REMOTIX 8901) è un altro strumento di prova:
NON RIPROVATO; l'immagine `debian-13-genericcloud-amd64.qcow2` va scaricata a mano da Debian (non c'è nel repo; il nome del file è atteso dallo script).

## 7. Che cosa non si trova nel repo (elenco completo di questa prova)

1. Il valore `SOURCE_DATE_EPOCH=1795130069` (solo qui e nel `.buildinfo` salvato).
2. Le tre date dei file del passo 4.1 (solo qui e nel pacchetto salvato).
3. Il fatto che `sudo` debba funzionare senza password per l'utente (gli script usano `echo | sudo -S`).
4. I percorsi fissi `/media/REMOTIX-DEBIAN/...` (script di preparazione, `build-deb.sh`, `prove/fresh.sh`): un disco persistente su `/media` è un requisito.
5. L'ordine: clone (un solo clone per tutte le distribuzioni), poi `cd debian13`, `prepara-server.sh`, poi `build-deb.sh` (il repo lo dice nelle intestazioni, ma non in un punto solo: ora è qui).
6. La rete: `github.com`, `docker.io` e i server di pacchetti Debian devono essere raggiungibili dal server.
7. Per i manuali: `python3-pygments` e `python3-pil` (scritti nell'intestazione di `build.py`, ma non installati da `prepara-server.sh`).
8. Per la macchina virtuale `vm.sh`: l'immagine Debian «genericcloud» da scaricare (NON RIPROVATO).
