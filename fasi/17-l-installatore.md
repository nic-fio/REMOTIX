# Fase 17 — L'installatore, e REMOTIX su Linux in generale

*Aperta dall'utente il **29 settembre 2026**, a fase 16 chiusa nei numeri. Questo documento fissa
**prima** del lavoro tutto quel che la fase farà: la domanda, quel che l'indagine sulle distribuzioni
ha trovato, la forma dell'installatore, le tappe, le prove, e le decisioni che spettano all'utente.
Le decisioni prese stanno anche in `DECISIONI.md` §10; qui c'è il come.*

*Marche: `[M]` misurato sul ferro · `[L]` letto in una fonte primaria (sorgenti, file dei pacchetti,
documentazione ufficiale) · `[D]` dedotto · `[?]` da confermare. L'indagine del 29 settembre è
quasi tutta `[L]`: nessuna distribuzione diversa da Debian ha ancora fatto girare REMOTIX.*

---

## 1. La domanda

REMOTIX è nato e cresciuto su **Debian 13 Trixie**. L'obiettivo è che giri **su Linux in generale**,
e che si installi con un sistema **professionale, di assoluta eccellenza**.

Parole dell'utente (29 set 2026):

> *«Al momento REMOTIX è stato sviluppato su Debian Trixie, ma l'obiettivo è farlo girare su Linux in
> generale. Per ottenere questo risultato, e quindi avere basi solide per costruire l'installer, è
> necessario fare un'indagine approfondita sulle principali distro.»*
>
> *«REMOTIX dovrà essere dotato di un sistema di installazione professionale, di assoluta eccellenza.»*

⇒ L'installatore è un **requisito del prodotto**, non una rifinitura di fine lavori, e si misura come
il resto. È un sottosistema vero: largo (distribuzioni × desktop × schede × tre mestieri), anche se
ogni suo pezzo è noto e altri lo hanno già risolto.

**«Installare» sono tre mestieri**, e l'installatore li fa tutti e tre:

| | la macchina prima | che cosa deve succedere |
|---|---|---|
| **prima installazione** | REMOTIX non c'è | si controlla che la macchina abbia quel che serve, si installa, si dice come entrare |
| **aggiornamento** | REMOTIX c'è ed è **in uso**: magari 5 persone collegate | si cambia versione **senza chiudere i desktop** di chi è collegato |
| **disinstallazione** | REMOTIX c'è | si toglie, e la macchina **torna com'era** |

---

## 2. Le decisioni dell'utente (29 settembre 2026)

| | decisione | perché |
|---|---|---|
| **Linux in generale** | Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE | `DECISIONI.md` §10.1 |
| **installatore di eccellenza** | requisito del prodotto, con prove misurabili | `DECISIONI.md` §10.2 |
| **prima l'indagine, poi l'installatore** | l'installatore si scrive una volta sola, sapendo già le differenze | fatta il 29 set, §4 |
| **le prove in MACCHINE VIRTUALI, non nelle scatole** | *«stavolta non dobbiamo misurare le performance, ma il corretto funzionamento dell'installer, quindi la potenza bruta della GPU non serve»* | una VM ha kernel, SELinux, firewall e avvio **della distribuzione**; una scatola usa il kernel del server (Debian) e direbbe «tutto bene» dove la macchina vera rifiuterebbe |
| **il motore in otto fasi** | PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY, ACQUISITION, INSTALLATION & CONFIGURATION, VERIFICATION & CERTIFICATION, COMMIT / ROLLBACK | proposta dell'utente, rafforzata su sua richiesta (TRUST, tre esiti per desktop, il piano come documento, l'accensione fra 7a e 7b, la RIPRESA), §6.0 |
| **TUI e GUI irrinunciabili** | *«su TUI e GUI dico che è un requisito irrinunciabile»* | §6.6.1, D12 |
| **una VM per desktop** | *«4 VM distinte, esempio Ubuntu/GNOME, Ubuntu/KDE, Ubuntu/XFCE, Ubuntu/LXQt»* | il cliente ha di solito **un** desktop: con quattro insieme, un pezzo dimenticato per XFCE arriverebbe lo stesso trascinato da KDE, e la prova direbbe verde |

---

## 3. Dove REMOTIX può girare: la matrice

Distribuzioni e desktop che entrano nella fase (✅ = da portare e provare; ⛔ = fuori, col perché).

| distribuzione | GNOME | KDE | XFCE | LXQt | note |
|---|---|---|---|---|---|
| **Debian 13** (riferimento) | ✅ | ✅ | ✅ | ✅ | la base di oggi |
| **Ubuntu 26.04 LTS** | ✅ | ✅ | ✅ | ✅ | GNOME 50 (§5.1); il GNOME «vanilla» va installato (§4.6) |
| Ubuntu 24.04 LTS | 🔸 | ⛔ | ⛔ | ⛔ | KDE 5.27 (manca l'EIS di KWin ≥ 6.1), XFCE 4.18 e LXQt 1.4 senza Wayland. GNOME 46 sì, ma con OpenSSL 3.5 statico e un `#if` per ffmpeg 6.1 — **decisione D7** |
| **Fedora 44** | ✅ | ✅ | ✅ | ✅ | GNOME 50; H.264 da RPM Fusion (§4.2) |
| Fedora 43 | · | · | · | · | **analizzata, non certificata**: GNOME 49, esce di supporto a fine 2026; c'è la sua VM nuda per confronti |
| **Alma 10** (certificata) · Rocky / RHEL 10 (compatibili, non certificate) | ✅ | ✅ | ⛔ | ⛔ | KDE da EPEL; né labwc né XFCE né LXQt in RHEL/EPEL 10; su AMD niente VA-API (Mesa senza) |
| **Arch** (Manjaro, EndeavourOS) | ✅ | ✅ | ✅ | ✅ | tutto ufficiale, anche ngtcp2 1.25 e i codec |
| **openSUSE Tumbleweed** | ✅ | ✅ | ✅ | ✅ | GNOME 50; H.264 solo con Packman (§4.2) |
| **openSUSE Leap 16** | ✅ | ✅ | ✅ | ✅ | XFCE e LXQt sotto Wayland «sperimentali» per SUSE; ngtcp2 da portare dentro |

**Fuori, e perché** (`[L]`):
- **Debian 12** e **RHEL 9**: mutter 43 / GNOME 40, niente libei, niente labwc — la base è troppo vecchia.
- **openSUSE Leap 15.6**: fine vita il 30 aprile 2026. **SLES 16**: solo GNOME, niente Packman — si
  rivede se un cliente la chiede.
- **Linux Mint Cinnamon**: non è uno dei quattro desktop (Muffin non ha le API di mutter). Mint 22 si
  porta dietro i limiti di Ubuntu 24.04.
- **Distribuzioni senza systemd** (Alpine, Devuan, Artix con OpenRC…): REMOTIX usa logind, il gestore
  d'utente e `systemctl --user` dappertutto (`figlio.c:1158-1163`). Va scritto nei requisiti.
- **Immutabili** (Silverblue/Kinoite, Aeon/Kalpa, Ubuntu Core, SteamOS): `/usr` in sola lettura, gruppi
  in `/usr/lib/group`, installazione con riavvio. Si rimandano a dopo la fase (§12, D9).

⇒ **La matrice di certificazione: 27 macchine virtuali** — Debian 13, Ubuntu 26.04, Fedora 44, Arch,
Tumbleweed, Leap 16 × 4 desktop (24), più Alma 10 × 2 (GNOME, KDE), più Ubuntu 24.04 × GNOME (se D7
dice sì). **Fedora 43 è analizzata ma fuori dalla matrice.**

⚠ **Che cosa si certifica, e che cosa no.** Si certifica solo quel che gira nelle nostre VM: **Alma 10**,
non «la famiglia RHEL 10». Rocky 10 e RHEL 10 si dichiarano **compatibili, non certificate**: stessa
base di pacchetti, ma nessuno le ha provate. Lo stesso per Manjaro ed EndeavourOS rispetto ad Arch,
e per Mint 23 rispetto a Ubuntu 26.04. Una derivata diventa certificata solo con la sua VM nella
matrice.

---

## 4. Che cosa l'indagine ha trovato

Cinque ricerche in parallelo il 29 settembre (Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE, e «come
installano i migliori»), poi due verifiche mandate a **smentirle** (una sulle distribuzioni, una sul
codice di REMOTIX). La verifica sulle distribuzioni è `[?]` finché non torna: i punti che tocca sono
segnati.

### 4.1 Le voci, famiglia per famiglia

| voce | Debian 13 | Ubuntu 26.04 | Fedora 44 | RHEL/Alma 10 | Arch | openSUSE TW / Leap 16 |
|---|---|---|---|---|---|---|
| **H.264 sulla scheda** | ✅ | ✅ Mesa coi codec | ⛔ Intel e AMD: RPM Fusion | Intel: RPM Fusion; ⛔ AMD: Mesa senza VA-API | ✅ tutto ufficiale | ⛔ ffmpeg senza `h264_vaapi`: serve Packman |
| **ripiego software x264** | ✅ | ✅ | ⛔ solo RPM Fusion | ⛔ solo RPM Fusion | ✅ | ⛔ solo Packman |
| **OpenSSL ≥ 3.5** (QUIC) | ✅ 3.5 | ✅ 3.5 (26.10: **4.0**) | ✅ 3.5 | ✅ da 10.1 | ✅ 3.6 | ✅ 3.5 |
| **ngtcp2 ≥ 1.25** | da sorgente | ⛔ 1.16 | ⛔ 1.21 | ⛔ 1.22 (EPEL) | ✅ 1.25 | TW ✅ · Leap ⛔ 1.6 |
| **PAM** | `common-*` ✅ | `common-*` ✅ | ⛔ `password-auth` | ⛔ `password-auth` | ⛔ `system-auth`, niente `@include` | ⛔ un nome diverso, e in `/usr/lib/pam.d` |
| **SELinux / AppArmor** | — | AppArmor, non ci tocca | SELinux **attivo** | SELinux **attivo** | — | SELinux **attivo** (TW dal 2025, Leap 16) |
| **firewall di serie** | — | ufw (spento) | firewalld (Workstation: porta aperta; Server: chiusa) | firewalld, **chiuso** | — (EndeavourOS: firewalld) | firewalld, **chiuso** |
| **GNOME** | 48 | **50** ⚠ §5.1 | **50** ⚠ | 47→49 | **50** ⚠ | TW **50** ⚠ · Leap 48 |
| **KDE Plasma** | 6.3 | 6.6 | 6.x | 6.x (EPEL) | 6.7 | 6.7 · 6.4 |
| **labwc** (XFCE, LXQt) | 0.8.3 | 0.9.3 | 0.9.6 | ⛔ assente | 0.20.2 | 0.20.2 · 0.8.1 |
| **servizi nuovi** | accesi | accesi | **spenti** (preset) | spenti | **spenti** (`disable *`) | spenti |

`[M]` 29 set, dalle immagini ufficiali accese in VM: SELinux **Enforcing** su Fedora 43/44 e Alma 10;
su openSUSE i processi hanno l'etichetta SELinux ma l'immagine minima non ha `getenforce` (`[?]`);
**nessun firewall attivo** in nessuna immagine *cloud* — dal cliente, che installa dall'ISO, non
sarà così: le prove del firewall lo accendono apposta (R2).

### 4.2 La codifica H.264 e i brevetti

REMOTIX **non contiene** un codificatore H.264: usa quello della scheda (`h264_vaapi`, via libavcodec
e VA-API) e, come ripiego, `libx264` della distribuzione (`codificatore.c:1350`).

Fedora e openSUSE tolgono H.264 dai loro pacchetti per i brevetti, in punti diversi:
- **Fedora**: ffmpeg «free» ha `h264_vaapi`, ma **nessuna scheda codifica H.264 di serie**: Mesa è
  costruita senza (AMD ⇒ `mesa-va-drivers-freeworld` da RPM Fusion), e il driver Intel ridotto
  (`intel-media-driver-free`) è costruito con `AVC_Encode_VDEnc_Supported=no` e
  `AVC_Encode_VME_Supported=no` dal 2023 (Intel ⇒ `intel-media-driver` da RPM Fusion) `[L]` spec F44.
- **openSUSE**: la ffmpeg ufficiale **non ha `h264_vaapi`** (`[L]` nella lista degli encoder di
  `libavcodec62-8.1.2` di Tumbleweed, aperta: ci sono `av1/vp9/mpeg2_vaapi` e `libopenh264`). Senza Packman REMOTIX non codifica, su nessuna scheda: **il caso peggiore**.
- **RHEL 10**: Mesa costruita **senza VA-API**, e RPM Fusion non la sostituisce: su AMD niente; EPEL 10
  non ha nemmeno il driver Intel. ⇒ Su RHEL/Alma 10 il video sulla scheda c'è solo con depositi di
  terzi, e XFCE/LXQt non ci sono: **bersaglio debole**, si tiene per GNOME e KDE col ripiego dichiarato.
- **NVIDIA col driver proprietario**: non codifica via VA-API su nessuna distribuzione `[D]`. Il
  controllo preliminare la riconosce e lo dice prima.

⇒ Regole per l'installatore:
1. ⛔ **Non distribuire mai un'implementazione di H.264** (né x264 né ffmpeg «completa» dentro il
   pacchetto): REMOTIX **usa** quella della macchina, come fa gnome-remote-desktop dentro Fedora.
2. ⛔ **Non aggiungere depositi di terzi in silenzio** (RPM Fusion, Packman): il controllo preliminare
   lo **dice**, col comando esatto, e lo fa solo se l'amministratore acconsente (D5).
3. Non è un parere legale: prima di distribuire in grande serve un avvocato. L'ultimo brevetto H.264
   scade fra il 2027 e il 2030 (le fonti non concordano).

### 4.3 PAM: il file d'accesso

`/etc/pam.d/remotix` (sorgente `src/remotix.pam`) dice al sistema quali controlli fare quando
qualcuno scrive nome e parola d'ordine nella pagina. Oggi rimanda ai controlli standard di Debian
(`@include common-auth`, righe 43, 48, 50, 83). ⛔ E `@include` stesso è **una modifica di Debian** a
Linux-PAM (patch `031_pam_include`): altrove la riga è «illegal module type» e **fallisce anche
l'autenticazione** `[L]`. ⇒ Su Fedora, RHEL, Arch e openSUSE oggi **nessuno entra**.

⇒ **Un file per famiglia**, come fa Cockpit (che fa lo stesso mestiere su tutte e quattro):

| famiglia | base | dove |
|---|---|---|
| Debian/Ubuntu | `common-auth`, `common-account`, `common-session` | `/etc/pam.d/remotix` |
| Fedora/RHEL | `password-auth` + `postlogin`, `pam_selinux close/open`, `pam_loginuid` | `/etc/pam.d/remotix` |
| openSUSE | `common-*` (`common-session-nonlogin`) | **`/usr/lib/pam.d/remotix`** |
| Arch | `system-remote-login` (o `system-auth`) | `/etc/pam.d/remotix` |

In tutti: `pam_systemd` (senza, il desktop non nasce) e **root escluso** per impostazione predefinita.
Su Arch anche `pam_systemd_home`, o gli utenti di `systemd-homed` non entrano `[?]` da misurare.

⚠ **Il blocco dei tentativi.** Arch (e Fedora/RHEL con authselect) mettono `pam_faillock` nella pila
di serie: tre parole d'ordine sbagliate in 15 minuti chiudono il conto per 10 minuti — **anche per chi
si siede davanti alla macchina** (`[L]` pambase: `pam_faillock` senza parametri ⇒ deny=3,
fail_interval=900 s, unlock_time=600 s). Da remoto, chiunque raggiunga la porta e conosca un nome
utente può chiudere fuori il proprietario; il ban per indirizzo non basta se i tentativi arrivano da
più indirizzi. ⇒ **Decisione D3.**

### 4.4 Il codice di REMOTIX: le cose legate a Debian

Confermate dalla verifica sul codice (`[L]`), con la riga giusta:

| dove | che cosa | cura |
|---|---|---|
| `src/remotix.pam:43,48,50,83` | `@include common-*` | un file per famiglia (§4.3) |
| `src/sessione.h:95`, `sessione.c:1850-1960` | il drop-in `--headless` per `org.gnome.Shell@wayland.service` | GNOME 50 lo chiama `@user` (§5.1) |
| `src/main.c:348-358`, `autenticazione.c:158` | l'avviso cerca il PAM solo in `/etc/pam.d`, e il messaggio su «other» è **sbagliato anche su Debian** | cercare anche `/usr/lib/pam.d`; testo giusto |
| `src/kwin.c:48` (`main.c:1924`) | scrive `/usr/share/applications/org.kde.remotix.desktop` **mentre gira**, da root | lo porta il pacchetto; a esecuzione solo la verifica (`kwin.c:342`) |
| `src/Makefile:238-239` | `-L… /lib` e rpath su `lib` (Fedora/SUSE: `lib64`) | ngtcp2/nghttp3 statiche (§6.3): rpath non serve più |
| `src/Makefile:33` | dichiara libavcodec ≥ 61, serve la 7.1; `dipendenze` controlla solo le intestazioni | versioni minime vere, controllate |
| `src/codificatore.c:1419,1436` | `avcodec_get_supported_config` (manca in ffmpeg 6.1 di Ubuntu 24.04) | un `#if`, solo se D7 dice sì |
| `src/certificati.c:149` | `const` con OpenSSL 4.0 (Ubuntu 26.10, Fedora rawhide) | 5 righe |
| `src/figlio.c:4684` | nodo `renderD128` fisso per il codificatore | con più schede prende quella sbagliata: scegliere dal driver |
| `src/sessione.c:2236` | registro della sessione con nome prevedibile in `/tmp` | un altro utente lo può creare prima: spostarlo in `~/.local/state/remotix/` |
| `src/sessione.h:94,96` | GNOME riconosciuto dalla sola presenza di `gnome-session`, sessione sempre `gnome` | su Ubuntu serve il GNOME «vanilla» (§4.6) |
| `src/provisiona.sh` | utenti `prova`/`prova2` con parola d'ordine in chiaro, `sudoers` dei banchi, `gpu-udev.sh`, `ld.so.conf.d` | ⛔ è un allestitore **da banco**: l'installatore si scrive da capo, e niente di questo entra nel pacchetto |
| `src/Contenitore` | immagine `debian:13`, `apt`, pkgconfig `x86_64-linux-gnu` | un contenitore di costruzione per famiglia |

Versioni minime mai dichiarate, da scrivere: labwc con `-m/-C/-S` (tarato su 0.8.3), KWin ≥ 6.1
(`connectToEIS`), le API di mutter, `wlr-randr` (LXQt), `xfconfd.service`, OpenSSL ≥ 3.5, ngtcp2 ≥ 1.25.

### 4.5 La funzione di banco nel binario

Il piano chiedeva che il binario installato **non contenga** la funzione di banco (`BANCO_MARCA`,
`BANCO_ESITO`). `[L]` Il codice è sempre compilato, ma spento da `#define BANCO_ACCESO 0`
(`rcp.c:186`): il server rifiuta ogni marca e lo dichiara. ⇒ Il binario di oggi è già «da prodotto»
per questa funzione. Restano compilati altri arnesi (`--audio-prova`, `--rilievo`, `--comando-socket`,
`--sblocca`, `--parlantina`, lo scatto con `SIGUSR1/2`): l'unità del pacchetto **non li passa**, e la
prova R13 guarda anche quelli.

### 4.6 Altre differenze che l'installatore deve gestire

- **Ubuntu**: il GNOME di serie è la sessione `ubuntu` (dock, colori Ubuntu); REMOTIX avvia la sessione
  `gnome`, che c'è solo col pacchetto `gnome-session` (universe) ⇒ o lo si porta come dipendenza, o
  REMOTIX impara la sessione `ubuntu` (**decisione D8**: quale GNOME vede chi si collega?).
- **labwc** non è installato da nessun gruppo XFCE/LXQt di serie (Xubuntu e Lubuntu restano su X11):
  lo porta l'installatore.
- **Gruppi `video`/`render`**: numeri diversi da una macchina all'altra — il codice li legge già dal
  nodo della scheda (`provisiona.sh:71-83`). Su Arch `renderD*` è aperto a tutti (0666).
- **`/etc/login.defs`**: su openSUSE sta in `/usr/etc` (lo script oggi funziona per caso).
- **Firmware** diviso in pezzi su Arch (`linux-firmware-intel`, `-amdgpu`).
- **Rolling release** (Arch, Tumbleweed): ffmpeg e ngtcp2 cambiano spesso il numero della libreria; un
  binario pronto si romperebbe al primo aggiornamento del sistema ⇒ il pacchetto si lega alla versione
  esatta, o si ricostruisce a ogni cambio (§6.2).

---

## 5. Le due cure del prodotto che vengono PRIMA dell'installatore

### 5.1 GNOME 50: il servizio della Shell ha cambiato nome

`[L]` Da GNOME 50 (Fedora 44, Ubuntu 26.04, Tumbleweed, Arch; prima o poi Debian) l'unità
`org.gnome.Shell@wayland.service` non c'è più: c'è `org.gnome.Shell@.service` con
`ExecStart=gnome-shell --mode=%i`, e la sessione chiede `org.gnome.Shell@user.service`. Il nostro
drop-in con `--headless` finisce sotto un nome che nessuno usa ⇒ la Shell nasce **senza schermo
virtuale**. Anche gnome-session 49+ è stato riscritto (REMOTIX conosce a fondo i meccanismi interni
della 48, `sessione.h:420-523`) ⇒ **da riprovare tutto** su GNOME 50.

`[L]` commit gnome-shell `0eb754a08` (13 nov 2025): l'unità diventa il modello
`org.gnome.Shell@.service` con `ExecStart=gnome-shell --mode=%i`; `@user` lo chiede gnome-session 50.
GNOME 50 c'è su Fedora 44, Ubuntu 26.04, Tumbleweed e Arch; Fedora 43 (49), Leap 16 (48) e Debian 13
(48) hanno ancora `@wayland`. `--headless` e `--no-x11` in mutter 50 ci sono ancora;
`org.gnome.Shell@headless.service` **non** va (diventerebbe `--mode=headless`, che non esiste).

⛔ **E il nostro controllo darebbe un falso verde**: su GNOME 50 `systemctl --user show -p ExecStart
org.gnome.Shell@wayland.service` crea l'istanza «wayland» dal modello, ci applica il nostro drop-in e
restituisce la nostra riga — il controllo passa, mentre gnome-session avvia `@user` senza `--headless`.

Cura (`sessione.c`, `sessione.h`): scegliere l'unità da quel che è installato (`@wayland` se c'è,
altrimenti `@user`); il drop-in in `<unità>.d/`, **non** nella cartella del modello (toccherebbe anche
GDM); la riga `--headless --no-x11` senza `--mode=%i`; rileggere la stessa unità scelta; la pulizia di
`provisiona.sh:245,510` estesa a `@user` e `@`. Si prova su `fedora44-gnome` e `ubuntu2604-gnome`.

### 5.2 Aggiornare senza chiudere i desktop: la misura (T2, 29 set 2026) `[M]`

`PIANO.md` (Fase 15), `fasi/10` §7.5, `SPECIFICHE.md` e `DECISIONI.md` dicevano che fermare il servizio
uccide le sessioni per `KillMode=mixed` (misura del 25 agosto). La verifica sul codice aveva già
smentito la causa; **la misura di T2 smentisce il fatto**:

- **dieci prove con Firefox vero** sulle quattro scatole: 4 «ferma» (`systemctl stop`, `KillMode=mixed`),
  4 «uccidi il padre» (`kill -KILL` al solo padre), 2 «uccidi il figlio» (SIGTERM al solo figlio). In
  ogni sessione tre testimoni che scrivono l'ora ogni secondo (il terminale vero del desktop, un
  processo in `session-cN.scope`, uno in `user@.service`) e una sentinella a 50 ms su nascite e morti;
- **muoiono solo padre, aiutante PAM e figlio**, entro 0,06-1,2 s (GNOME: Stopping 53.596, «il figlio è
  spento» 54.307, unità Deactivated 54.311, poi nient'altro). logind non fa nulla
  (`KillUserProcesses=no`): nessuna sessione chiusa;
- **sopravvivono il compositore, la sessione e i programmi**: i tre testimoni battono senza buchi, in
  tutte e dieci le prove, fino allo sgombero 3 minuti e mezzo dopo;
- **al riattacco** torna lo stesso compositore, con lo stesso pid, e il terminale dov'era. Su GNOME il
  desktop ripreso è prima «ZERO MONITOR» (il monitor virtuale era del figlio morto): il figlio nuovo ne
  monta un altro e le finestre ricompaiono;
- **la causa**: il palco parte con `setsid --fork` e sta fuori dall'unità; la morte del figlio non si
  propaga e nessuno chiude la sessione logind. Il fatto del 25 agosto oggi non si riproduce (non si sa se
  allora il desktop fosse morto davvero o se si sia letta come morte la riga «New session … vuota»: anche
  un riattacco riuscito apre una sessione logind nuova).

⇒ **La cura è quella leggera, 1-2 giorni; il «custode» non serve.** Resta da fare (T7):
1. il **padre nuovo ritrova i desktop vivi** all'avvio: oggi riparte con «inquilini=0» e quei desktop
   non li conta nessuno (né il tetto delle sessioni, né il budget, né l'orologio dell'abbandono);
2. **`loginctl terminate-user`** (`figlio.c:1577`) non va dato quando l'utente ha già un desktop vivo.

⚠ Due cose per l'installatore: (a) la sessione logind del figlio risulta «in chiusura» 24 ms dopo la
nascita (`pam_end` senza `pam_close_session`): con **`KillUserProcesses=yes`** il desktop potrebbe morire —
`[?]` da misurare, e il controllo preliminare deve leggere quell'impostazione; (b) ogni riattacco lascia
una sessione logind in più (col capo morto), innocua per l'utente.

Quel che i migliori insegnano (`[L]`): **NoMachine** butta fuori tutti a ogni aggiornamento e lo scrive
nella guida; **xrdp** ha sessioni che sopravvivono ma che nessuno ritrova (schermo nero). ⇒ REMOTIX ha già
la metà difficile (sopravvivere); gli manca la metà di xrdp (**ritrovare**). Le connessioni QUIC non
sopravvivono comunque: la promessa onesta resta *«aggiornare costa a chi è collegato un riattacco di pochi
secondi; le finestre restano»*.

Il banco: `banchi/17-t2/` (`t2-misura.py`, `t2box.py`, `lancia.sh`, `catena.sh`, `riassunto.sh`,
`tabella.sh`); le evidenze sul server in `/media/REMOTIX/tmp/t2/<desktop>-<azione>/`.

---

## 6. La forma dell'installatore

### 6.0 Il motore d'installazione — lo schema dell'utente, rafforzato (29 set 2026)

**La proposta dell'utente**, in otto fasi: PREFLIGHT (conoscere il sistema) · COMPATIBILITY (stabilire
cosa è supportato) · PLANNING (costruire il piano) · CONSENT & SAFETY (presentare il piano e preparare
la protezione) · ACQUISITION (pacchetti, risorse, dipendenze) · INSTALLATION & CONFIGURATION
(applicare il piano) · VERIFICATION & CERTIFICATION (dimostrare che il prodotto funziona) · COMMIT /
ROLLBACK (rendere definitiva o annullare l'operazione).

Che cosa aggiunge a un installatore «buono»: un **piano esplicito presentato prima di agire**, e
un'operazione che si **conferma o si annulla per intero** — anche la prima installazione che fallisce
a metà, non solo l'aggiornamento. L'utente ha chiesto di rafforzarla nei punti deboli; le sei
aggiunte, tutte nelle giunture fra una fase e l'altra:

1. **una fase zero, TRUST**: il motore esegue comandi da root sulla macchina di un altro; prima di
   tutto verifica che **sé stesso e il catalogo** (le combinazioni supportate) siano autentici
   (firma) e aggiornati — un motore alterato o vecchio passerebbe tutte le fasi dopo;
2. **COMPATIBILITY ha tre esiti, per desktop**: *certificata* (provata nelle nostre VM, §7) ·
   *a condizioni* (RPM Fusion, labwc, ripiego software…) · *non supportata*; e una macchina può
   essere a posto per GNOME e non per XFCE;
3. **il piano è un documento**: si salva, si legge, si approva, si applica anche su cento macchine
   uguali; ogni azione porta **come si fa, come si verifica, come si annulla** — l'annullamento nasce
   col passo, non si aggiunge dopo; e il piano porta l'**impronta** della macchina su cui è stato
   fatto: se fra il piano e l'esecuzione la macchina è cambiata, il piano non vale più;
4. **ACQUISITION non è innocua**: aggiungere il deposito di RPM Fusion cambia già la macchina ⇒ è
   un'azione del piano come le altre; e la regola: **niente si installa finché tutto non è scaricato
   e verificato** — una rete che cade a metà ferma l'operazione *prima* di toccare la macchina;
5. **fra installare e verificare c'è l'ACCENSIONE**: si installa a servizio spento, si fanno i
   controlli che non chiedono il servizio (7a), si accende, si fanno quelli dal vivo (7b) — la gran
   parte degli errori si scopre quando annullare costa poco e nessuno è collegato;
6. **la RIPRESA**: ogni passo si scrive nel registro **prima** di farlo; se la corrente salta durante
   la fase 6, il giro dopo il motore trova l'operazione aperta e propone di completarla o annullarla.
   E nell'aggiornamento anche il ritorno indietro rispetta la regola di non chiudere i desktop.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          REMOTIX INSTALL ENGINE                          │
├──────────────────────────────────────────────────────────────────────────┤
│ 0. TRUST                 il motore e il catalogo sono autentici e freschi│
│ 1. PREFLIGHT             conoscere il sistema — sola lettura; l'impronta │
│ 2. COMPATIBILITY         per desktop: certificata · a condizioni · no    │
│ 3. PLANNING              il piano come documento: fai / verifica / annulla│
│ 4. CONSENT & SAFETY      approvazione (a mano o da file), salvataggi,    │
│                          registro aperto                                 │
│ 5. ACQUISITION           tutto scaricato e verificato prima di toccare   │
│ 6. INSTALLATION & CONF.  a servizio spento, ogni passo annotato prima    │
│ 7. VERIFICATION & CERT.  7a senza servizio → ACCENSIONE → 7b dal vivo    │
│ 8. COMMIT / ROLLBACK     conferma, o annulla ripercorrendo il registro   │
│ ↺  RIPRESA               un'operazione interrotta si completa o si annulla│
└──────────────────────────────────────────────────────────────────────────┘
```

**Un motore, tre mestieri.** Le fasi valgono per installare, aggiornare e disinstallare:

| fase | prima installazione | aggiornamento | disinstallazione |
|---|---|---|---|
| 0 TRUST | firma del motore e del catalogo | idem | idem |
| 1 PREFLIGHT | distribuzione, scheda (NVIDIA proprietaria compresa), H.264, desktop, PAM, porta, firewall, SELinux | in più: la versione installata e **le sessioni aperte** | che cosa c'è, e il registro delle modifiche fatte da REMOTIX |
| 2 COMPATIBILITY | la macchina contro il catalogo (§3), desktop per desktop | la N+1 sulla stessa macchina; N+1 accetta la configurazione di N | — |
| 3 PLANNING | azioni: depositi, pacchetti, gruppi, firewall | in più: «chi è collegato si riattacca in pochi secondi» | che cosa si toglie, che cosa resta (configurazione, se non `purge`) |
| 4 CONSENT & SAFETY | sì/no per ogni scelta (D5, D6); salvataggio di quel che si toccherà | salvataggio di `/etc/remotix` e `/var/lib/remotix` | salvataggio della configurazione |
| 5 ACQUISITION | depositi (annotati) e pacchetti scaricati e **verificati** | la N+1 | — |
| 6 INSTALLATION | il gestore di pacchetti installa, servizio spento; il motore fa il resto e annota | l'installazione della N+1 **mentre la N serve ancora** | il gestore di pacchetti toglie; il motore disfa il suo registro |
| 7 VERIFICATION | 7a · accensione · 7b | 7a · riavvio del servizio senza chiudere i desktop (§5.2) · 7b + sessioni ritrovate | le impronte tornate com'erano |
| 8 COMMIT / ROLLBACK | verde ⇒ si conferma; rosso ⇒ si annulla tutto | rosso ⇒ si torna a N, **senza chiudere i desktop** | — |

**Tre regole che tengono in piedi lo schema:**

1. ⛔ **Le fasi 5 e 6 le esegue il gestore di pacchetti della distribuzione, non il motore.** Il motore
   dirige (decide, chiede, controlla, annulla); i file di REMOTIX li mettono `apt`, `dnf`, `zypper`,
   `pacman`. Se li copiasse il motore ci sarebbero **due verità** su che cosa è installato, e gli
   aggiornamenti di sistema non lo conoscerebbero (Tailscale e Netdata fanno così, §6.5).
2. ⭐ **Il ritorno indietro è nostro.** Solo `dnf` ha un «annulla» vero (`dnf history undo`), e
   openSUSE su btrfs le fotografie di sistema (snapper); `apt` e `pacman` no. ⇒ Il motore ripercorre
   all'indietro il **registro** (le azioni del piano, ognuna col suo «come si annulla»); dove la
   macchina offre le fotografie di sistema, le usa in più. La promessa onesta: *«tutto quel che
   abbiamo fatto noi si annulla»*.
3. **Il consenso anche senza nessuno davanti allo schermo**: il piano approvato è un file, e si
   applica da cloud-init o Ansible su molte macchine; il motore lo rifiuta se l'impronta non combacia.

**La certificazione (fase 7), con quel che il motore può dimostrare da solo** — non ha un browser:
- *7a, a servizio spento*: le librerie viste con l'uid di un inquilino (nessun `not found`); la pila
  PAM si carica e rifiuta un utente inesistente; la configurazione si legge; la scheda **codifica
  davvero** un fotogramma di prova in H.264 (o si dichiara il ripiego software); per ogni desktop
  installato, il palco **parte senza schermo** e produce un'immagine;
- *7b, a servizio acceso*: attivo, la porta 7447 risponde (TCP e UDP), il certificato TLS è quello
  atteso, il firewall la lascia passare.

Il resto (un browser vero che entra e lavora) lo dimostrano le VM di §7, prima di ogni rilascio — ed
è quel che rende una combinazione «certificata» nel catalogo. L'esito si scrive nel **certificato
dell'installazione** (`/var/lib/remotix/certificato-<data>.txt`): versione, macchina, ogni prova con
l'esito — lo stesso che il benvenuto riassume.

### 6.1 Pacchetti nativi, e uno script d'ingresso

Scartati, col perché (`[L]`, i casi di RustDesk e Sunshine):
- **Flatpak, Snap, AppImage**: non installano servizi di sistema né file PAM, o non possono caricare
  i driver VA-API, Mesa e PAM della macchina;
- **binario unico statico**: REMOTIX carica a tempo di esecuzione i moduli PAM, il driver della scheda,
  Mesa, PipeWire — devono essere quelli della macchina.

⇒ **Pacchetti nativi** per ogni famiglia (`.deb`, `.rpm`, `.pkg.tar.zst`), come Cockpit, Docker,
Tailscale, gnome-remote-desktop:

```
                     un sorgente (git)
                           │
     ┌─────────────────────┼─────────────────────────┐
packaging/debian/   packaging/rpm/remotix.spec   packaging/arch/PKGBUILD
                    (%if fedora / rhel / suse,
                     come Cockpit)
     │                     │                         │
     ▼                     ▼                         ▼
 costruiti DENTRO la radice di ogni distribuzione (contenitori podman)
 ngtcp2 + nghttp3 statiche, versione fissata · tutto il resto della distribuzione
                           │
                           ▼
 depositi firmati:  apt (deb822 + keyring) · dnf / zypper · pacman
 canali: stabile · candidato     versioni vecchie conservate (per tornare indietro)
                           │
                           ▼
 install.sh — riconosce la distribuzione, --verifica, aggiunge il deposito, installa
 (ingresso comodo, come Tailscale; ⛔ non copia mai file del prodotto)
```

Gli strumenti nativi (`dpkg-shlibdeps`, `rpmbuild`, `makepkg`) **leggono il binario e calcolano da
soli** le librerie di cui ha bisogno: è la cura della lezione di `LEZIONI.md` §2.5-bis (i pacchetti
installati a mano che nessuno dichiarava). Per questo niente nFPM/fpm, che impacchettano file già
pronti con le dipendenze scritte a mano.

### 6.2 Si compila per ogni distribuzione

Il binario **non si copia** da una distribuzione all'altra: libavcodec (60, 61, 62), OpenSSL (3 o 4),
libei hanno versioni diverse. Un contenitore di costruzione per bersaglio, come `src/Contenitore` oggi
per Debian. Sulle rolling release il pacchetto si lega alle versioni esatte di ffmpeg: meglio un
aggiornamento **rifiutato** dal gestore di pacchetti che uno che rompe in silenzio.

### 6.3 Che cosa entra nel binario e che cosa no

| | scelta | perché |
|---|---|---|
| **ngtcp2, nghttp3** | dentro, **statiche**, versione fissata | serve ngtcp2 ≥ **1.25.0** (26 lug 2026: la impongono i flag `NGTCP2_STREAM_CLOSE2_FLAG_*` di `trasporto.c:296-299`; senza, 1.23) e quasi nessuna distribuzione la ha; sono piccole. ⚠ Gli **aggiornamenti di sicurezza diventano nostri** — **decisione D2** |
| OpenSSL | della distribuzione | è la libreria di sicurezza più curata dalle distribuzioni |
| libavcodec, driver, Mesa | ⛔ della distribuzione, **mai** dentro | è lì che stanno i codec brevettati (§4.2) |
| PAM, PipeWire, libei, glib, Wayland | della distribuzione | devono combaciare con la macchina |

⇒ `ld.so.conf.d` **sparisce**: oggi `provisiona.sh:394` mette la nostra ngtcp2 davanti a quella di
sistema, che usano anche curl e il gestore di pacchetti. Con le statiche non resta nessuna libreria
fuori dai percorsi di sistema.

### 6.4 Che cosa installa il pacchetto

| che cosa | dove |
|---|---|
| server e figlio | `/usr/libexec/remotix/` |
| comando dell'amministratore | `/usr/bin/remotix` — `verifica`, `stato`, `certificato`, `configurazione` |
| unità | `/usr/lib/systemd/system/remotix.service` (root; certificato generato all'avvio se manca) |
| predefiniti / scelte dell'amministratore | `/usr/share/remotix/remotix.conf` · `/etc/remotix/remotix.conf.d/` (vuota) |
| PAM | un file per famiglia (§4.3) |
| il permesso di cattura di KWin | `/usr/share/applications/org.kde.remotix.desktop` (oggi lo scrive il programma, §4.4) |
| le tre cinture di `DECISIONI.md` §4.7 (niente spegnimento, sospensione, tasti) | `/usr/share/polkit-1/rules.d/`, `/usr/lib/systemd/{logind,sleep}.conf.d/` — ⚠ cambiano la macchina: **decisione D4** |
| firewall | `/usr/lib/firewalld/services/remotix.xml`, `/etc/ufw/applications.d/remotix` — **definiti**, aperti solo col consenso (D6) |
| cartelle | `/var/lib/remotix` (0700), `/run/remotix` via `tmpfiles.d` |
| SELinux | sottopacchetto `remotix-selinux`, **solo se** le prove dicono che serve (prima si prova senza) |
| ⛔ **mai** | utenti di prova, `sudoers.d` dei banchi, `gpu-udev.sh`, `riavvia-*.sh`, `ld.so.conf.d` |

Dopo l'installazione: le persone vengono iscritte ai gruppi della scheda (`DECISIONI.md` §7.21) **e
lo si annota** (chi c'era già, chi l'ha messo REMOTIX), o la disinstallazione non sa che cosa togliere.

### 6.5 Le qualità dell'eccellenza

Prese da chi le fa meglio (`[L]`): Cockpit per PAM, SELinux e certificato; Tailscale per lo script
d'ingresso; Netdata per `--dry-run` e l'installazione senza rete; GitLab per il salvataggio prima di
aggiornare; Syncthing per il canale «candidato»; OpenSSH per la configurazione provata prima di
ripartire. ⚠ E da **non** copiare: Chrome (un cron che riscrive il deposito), Docker (la
disinstallazione che lascia la macchina diversa, e lo dice), la telemetria di Netdata (un server che fa
login non telefona a casa).

1. **Il controllo preliminare**, prima di toccare niente: `install.sh --verifica` e, a installazione
   fatta, `remotix verifica`. Guarda distribuzione e versione, scheda e nodo, **H.264 davvero
   disponibile** (profilo VA-API e `h264_vaapi` in libavcodec), desktop presenti e versioni, PAM,
   porta 7447 libera, firewall, SELinux, OpenSSL. Ogni problema con un messaggio in italiano semplice
   **e il comando che lo risolve**. ⚠ Non sta negli script del pacchetto: un pacchetto che rifiuta di
   installarsi perché manca la scheda rompe le immagini e cloud-init. Il pacchetto avvisa; il
   controllo decide quando lo si chiama.
2. **Idempotenza**: rieseguire non cambia niente.
3. **Disinstallazione** che rimette la macchina com'era; `remove` tiene la configurazione, `purge`
   toglie tutto; toglie dai gruppi **solo** chi ci aveva messo REMOTIX.
4. **Aggiornamento** senza chiudere i desktop (§5.2), con la configurazione **provata prima** di
   chiedere il riavvio del servizio.
5. **Ritorno alla versione precedente**: il deposito conserva le vecchie; prima di aggiornare si salva
   `/etc/remotix` e `/var/lib/remotix`; la versione N−1 legge la configurazione della N.
6. **Firme**: chiave per il solo deposito REMOTIX (`Signed-By`, mai `trusted.gpg.d`), pacchetto
   `remotix-archive-keyring`, sottochiave di firma con scadenza e un piano per ruotarla.
7. **Configurazione**: predefiniti in `/usr`, scelte dell'amministratore in `/etc` che vincono;
   `remotix configurazione --mostra` dice da quale file viene ogni voce.
8. **Benvenuto** alla fine: gli indirizzi da aprire, l'impronta del certificato, chi può entrare
   (root escluso), che cosa REMOTIX ha cambiato nella macchina, lo stato di H.264.
9. **Registro dell'installazione** e registro delle modifiche alla macchina
   (`/var/lib/remotix/modifiche.log`).
10. **Senza domande** per chi gestisce molte macchine (cloud-init, Ansible) e **senza rete**.
11. **Costruzione riproducibile** (`SOURCE_DATE_EPOCH`) e **SBOM** che nomina ngtcp2 e nghttp3 con la
    versione esatta.

### 6.6 La specifica del motore — stati, registro, azioni, fiducia (29 set 2026)

*Scritta dopo una revisione della bozza portata dall'utente: l'architettura in otto fasi regge; quel che
mancava era renderne le promesse **precise abbastanza da poterle provare in automatico**. Qui si fissa
quel che cambia i dati e il comportamento del motore — cambiarlo dopo vorrebbe dire riscriverlo. I
dettagli che dipendono da cose che oggi non esistono (il deposito pubblico, la custodia della chiave)
hanno il loro modello qui e la loro decisione alla tappa.*

#### 6.6.1 Il contratto: gli oggetti del motore

Il motore produce e consuma **sette oggetti**, file JSON con una versione di formato
(`"formato": "remotix-install/1"`). Sono suoi: chiunque usi il motore li legge, nessuno li inventa.

| oggetto | chi lo produce | che cosa contiene |
|---|---|---|
| **Profilo della macchina** | PREFLIGHT | ogni fatto rilevato, ciascuno con lo stato RILEVATO / VERIFICATO / SCONOSCIUTO (§6.6.7) |
| **Rapporto di compatibilità** | COMPATIBILITY | per desktop: livello e condizioni (§6.6.8), con la versione del catalogo usata |
| **Piano** | PLANNING | le azioni (§6.6.4) con le loro intenzioni e vincoli; l'impronta (§6.6.5); le scelte da approvare |
| **Insieme risolto** | ACQUISITION | gli artefatti esatti che il piano diventa (§6.6.6) |
| **Registro dell'esecuzione** | INSTALLATION, e il ritorno indietro | il giornale a scrittura anticipata (§6.6.3) |
| **Rapporto di verifica** | VERIFICATION | ogni controllo con esito PASS / FAIL / UNKNOWN / N.A. |
| **Certificato dell'installazione** | COMMIT | lo stato finale (§6.6.2), le condizioni, i riferimenti a motore, catalogo, piano, prodotto (§6.6.11) |

**Le interfacce: tre, e TUI e GUI sono un requisito irrinunciabile** (parola dell'utente, 29 set
2026):

| interfaccia | per chi | come gira |
|---|---|---|
| **CLI** (`remotix-install`, e `install.sh` che la scarica) | chi amministra da terminale, e l'installazione senza domande (§6.6.12) | da root |
| **TUI** (a schermo intero nel terminale) | chi amministra via ssh o dalla console, anche su una macchina senza nessuno davanti | da root, nel terminale |
| **GUI** (finestra nel desktop) | chi amministra dal desktop della macchina | ⛔ **come l'utente, non da root** (sotto Wayland un client grafico da root è sbagliato e spesso rifiutato): chiede i permessi al motore con **polkit**, come gli installatori grafici delle distribuzioni |

⛔ **Le interfacce non contengono logica d'installazione.** Mostrano gli oggetti del motore (profilo,
rapporto, piano, avanzamento dal registro, certificato) e raccolgono il consenso; non scelgono mai
pacchetti, depositi, PAM o ritorni indietro. Il motore è uno solo, e le tre interfacce parlano con lui
nello stesso modo: il motore scrive gli oggetti e gli eventi (JSON, una riga per evento) e legge il
consenso come un piano approvato. ⇒ La stessa operazione dà lo stesso piano, lo stesso registro e lo
stesso certificato qualunque interfaccia la guidi (R36). Lo strumento per TUI e GUI è la **decisione D12**.

#### 6.6.2 Gli stati dell'operazione

Un'operazione (installazione, aggiornamento, disinstallazione) ha un identificativo e **uno stato**,
scritto in `/var/lib/remotix/operazioni/<id>/stato`:

```
NUOVA → FIDATA → ESAMINATA → VALUTATA → PIANIFICATA → APPROVATA → ACQUISITA
      → IN_ESECUZIONE → APPLICATA → IN_VERIFICA → VERIFICATA → CONFERMATA
                ↓ interruzione          ↓ rosso               ↓ rosso
            INTERROTTA ──ripresa──→ IN_ESECUZIONE        IN_ANNULLAMENTO → ANNULLATA
                                                              ↓ un'azione non si annulla
                                                          ANNULLATA_IN_PARTE
dalle fasi 0-5, senza aver toccato niente:  BLOCCATA (serve un intervento) · RIFIUTATA (niente consenso)
```

| stato finale | vuol dire | il certificato dice |
|---|---|---|
| **CONFERMATA** | installata e verificata, tutti i controlli richiesti PASS | la piattaforma: CERTIFICATA o COMPATIBILE |
| **CONFERMATA_A_CONDIZIONI** | installata e verificata, con condizioni attive (§6.6.8) | le condizioni, una per una |
| **ANNULLATA** | tutto quel che REMOTIX ha fatto è stato disfatto | quel che resta di INDIRETTO (§6.6.4) |
| **ANNULLATA_IN_PARTE** | il ritorno indietro non ha potuto disfare tutto | l'elenco esatto di quel che resta, e perché |
| **BLOCCATA / RIFIUTATA** | niente è stato toccato | il codice del motivo (§6.6.9) |

Regole: ⛔ **nessuno stato si salta**; le transizioni valide sono solo quelle disegnate; il motore
rifiuta di partire se trova un'operazione in uno stato non finale e **non** la sua (va prima ripresa o
annullata). ⭐ **installata ≠ certificata**: CONFERMATA_A_CONDIZIONI su una piattaforma COMPATIBILE è
un'installazione riuscita, ma non una combinazione certificata.

#### 6.6.3 Il registro: scrittura anticipata e ripresa

Ogni azione del piano si esegue in quattro tempi, e il registro (`registro.jsonl`, una riga per
evento, `fsync` del file e della cartella prima di proseguire) li annota:

```
INTENZIONE(azione, stato_prima)  → [effetto]  → FATTA(azione, stato_dopo)
                                            ↘ FALLITA(azione, codice)
```

Ogni azione ha tre funzioni (§6.6.4): **fai**, **controlla** (dice se l'effetto c'è, senza cambiare
niente), **annulla**. La ripresa dopo un'interruzione guarda l'ultima riga di ogni azione:

| nel registro | che cosa è successo | che cosa fa la ripresa |
|---|---|---|
| niente | non cominciata | la fa |
| INTENZIONE senza FATTA | cominciata; forse finita, forse no, forse a metà | chiama **controlla**: effetto completo ⇒ annota FATTA; assente ⇒ la rifà; **a metà** ⇒ annulla quel che c'è e la rifà |
| FATTA | finita e annotata | passa oltre |
| FATTA ma l'effetto non c'è più (controllo di coerenza) | qualcuno l'ha disfatta dopo | ⛔ si ferma: BLOCCATA, «la macchina è cambiata durante l'operazione» |

⇒ Per questo ogni azione deve essere **idempotente** (rifarla non raddoppia l'effetto) e il suo
**controlla** deve saper distinguere completo / assente / a metà. Un file di configurazione si scrive
sempre su un nome temporaneo e poi si rinomina (mai a metà); un'unità si abilita e si controlla con
`systemctl is-enabled`.

⚠ **La transazione del gestore di pacchetti è un'azione speciale**: un'interruzione a metà lascia il
gestore nel suo stato di mezzo. La ripresa usa **il rimedio del gestore stesso** prima di tutto il resto:
`dpkg --configure -a` (apt), la ripetizione della transazione con `dnf` (e `rpm --verify`), la rimozione
del file di blocco e `pacman -Dk` (pacman), `zypper verify` (zypper); poi il **controlla** dell'azione
guarda i pacchetti uno per uno.

#### 6.6.4 Le azioni: quanto si annullano, e di chi è la modifica

Ogni azione del piano dichiara **quanto è reversibile**:

| classe | vuol dire | esempi |
|---|---|---|
| **ESATTA** | si torna allo stato di prima, byte per byte | un file nostro in `/etc`; un'unità abilitata; un utente aggiunto a un gruppo in cui non c'era; una regola del firewall aggiunta |
| **AL_MEGLIO** | si torna indietro, ma non per forza allo stesso stato | un pacchetto dipendenza tolto (se nessun altro lo vuole); un deposito tolto (ma i pacchetti presi da lì restano, e si dice) |
| **CON_FOTOGRAFIA** | reversibile solo con una fotografia di sistema (snapper, btrfs, LVM) | una dipendenza **aggiornata** dal gestore di pacchetti |
| **IRREVERSIBILE** | non si annulla | una conversione di formato che la versione vecchia non legge |

⛔ Un'azione IRREVERSIBILE ha **una riga sua nel consenso**, e il piano non la contiene se esiste
un'alternativa. Il certificato dice quali azioni CON_FOTOGRAFIA sono state fatte senza fotografia.

E ogni **modifica** della macchina ha un'**origine**, che decide fin dove il ritorno indietro è
autorizzato:

| origine | esempio | il ritorno indietro |
|---|---|---|
| **DIRETTA** | il file PAM di REMOTIX; un utente messo in `render` da noi | la disfa |
| **INDIRETTA** | libX aggiornata da 1.0 a 1.1 perché REMOTIX la chiede | ⛔ non la tocca (non si retrocede una libreria che altri possono già usare); la **dichiara** |
| **PREESISTENTE** | l'utente era già in `video` prima | ⛔ non la tocca mai |
| **CONCORRENTE** | l'amministratore cambia la stessa cosa durante l'operazione | ⛔ non la tocca; l'operazione si ferma (§6.6.3, ultima riga) |

⇒ **La promessa normativa** (R6, R28): *«tutto quel che REMOTIX ha fatto direttamente si annulla; quel
che è successo indirettamente si dichiara; quel che c'era prima non si tocca»*. Le dipendenze
**installate** per noi si tolgono se nessun altro le vuole (la marca «automatica» dei gestori:
`apt-mark auto`, `dnf` *userinstalled*, `pacman --asdeps`); quelle **aggiornate** restano aggiornate.

Per ogni modifica che tocca uno stato che c'era già (le tre cinture, i gruppi, il firewall) il registro
annota **lo stato di prima, la modifica, il consenso, lo stato dopo, come si annulla** (R33, R34).

#### 6.6.5 L'impronta della macchina

Il piano vale solo per la macchina su cui è stato fatto. L'impronta ha due parti:

| **vincolante** — se cambia, il piano non vale più | **annotata** — si registra, non invalida |
|---|---|
| distribuzione, versione, architettura | nome della macchina, indirizzi |
| i desktop installati e le loro versioni | pacchetti che il piano non tocca e da cui non dipende |
| i pacchetti che il piano tocca o da cui dipende, con la versione | carico, memoria libera |
| i depositi configurati (elenco e chiavi) | |
| scheda, driver, capacità H.264 rilevata | |
| i file che il piano scrive o legge (PAM, logind, polkit, firewall), con la loro impronta sha256 | |
| i gruppi `video`/`render` e i loro membri | |
| SELinux e il suo stato, il firewall e il suo stato | |
| versione del motore e del catalogo | |

L'impronta vincolante è un sha256 sul testo canonico di questi elementi (ordinati, un elemento per
riga); il piano la contiene, APPLY la ricalcola e la confronta. R31 prova ciascun elemento.

#### 6.6.6 Dal piano agli artefatti: PLAN → RESOLUTION → ARTIFACTS → VERIFY → APPLY

Il piano contiene **intenzioni con vincoli** («`remotix` ≥ 1.4, dal deposito REMOTIX; `labwc` dal
deposito della distribuzione»), non file. ACQUISITION le **risolve** nell'**insieme risolto**: per ogni
pacchetto nome, versione esatta, architettura, deposito, **digest** (sha256), firma verificata. Poi:
- APPLY installa **esattamente** quell'insieme, dalla cache locale già verificata (`apt install
  nome=versione` sui `.deb` già scaricati, `dnf install` sui file, `pacman -U` sui file) — mai «l'ultima
  versione» presa al momento;
- se la risoluzione esce dai vincoli del piano (il deposito è cambiato fra il piano e l'esecuzione), si
  torna a PLANNING con un **consenso nuovo**;
- l'insieme risolto entra nel registro: dice, a posteriori, che cosa è stato installato bit per bit.

#### 6.6.7 I fatti e i controlli: rilevato non è verificato, e UNKNOWN non è PASS

Ogni fatto del profilo ha uno di tre stati:

| stato | esempio |
|---|---|
| **RILEVATO** | «PipeWire è installato», «c'è una scheda AMD», «il file PAM esiste», «firewalld c'è» |
| **VERIFICATO** | «PipeWire risponde», «la scheda ha codificato un fotogramma H.264», «la pila PAM rifiuta un utente inesistente», «la porta è raggiungibile» |
| **SCONOSCIUTO** | lo strumento non c'è, il permesso manca, il tempo è scaduto |

E ogni controllo della certificazione ha uno di quattro esiti: **PASS**, **FAIL**, **UNKNOWN**,
**N.A.** (non si applica: il controllo di XFCE su una macchina senza XFCE).

⛔ **La regola generale: UNKNOWN non è mai PASS.** Un controllo che non riesce a dimostrare la sua
proprietà dà UNKNOWN; un controllo **richiesto** in UNKNOWN porta l'operazione a CONFERMATA_A_CONDIZIONI
(se la proprietà ha un ripiego dichiarato) o a IN_ANNULLAMENTO (se no). ⛔ E un fatto soltanto
RILEVATO non basta mai per un PASS. È la lezione del falso verde di GNOME 50 (§5.1) e dei contatori
che non vedono l'immagine: un verde su informazione incompleta è peggio di un rosso (R32).

#### 6.6.8 Compatibilità: livelli e condizioni

Il livello, **per desktop**:

| livello | vuol dire |
|---|---|
| **CERTIFICATA** | la combinazione distribuzione × versione × desktop è nella matrice (§3) e il catalogo registra un giro intero verde su di essa |
| **COMPATIBILE** | nessuna ragione nota di rifiuto, ma nessuna nostra VM l'ha provata (Rocky 10, Manjaro, Mint 23…) |
| **NON_SUPPORTATA** | un motivo noto, col suo codice (§6.6.9) |

E, sopra CERTIFICATA o COMPATIBILE, zero o più **condizioni**, ognuna col suo codice:

| codice | condizione | esempio |
|---|---|---|
| `C-DEPOSITO` | serve un deposito di terzi | RPM Fusion, Packman |
| `C-COMPONENTE` | l'installatore aggiunge un pezzo che il desktop di serie non ha | labwc per XFCE e LXQt; `gnome-session` su Ubuntu |
| `C-RIPIEGO` | una funzione passa al ripiego | H.264 in software (niente codifica sulla scheda) |
| `C-LIMITE` | una funzione manca | niente audio, una misura dello schermo non raggiungibile |
| `C-HARDWARE` | un requisito della scheda | NVIDIA col driver proprietario |
| `C-AMMINISTRATORE` | serve un passo a mano | aprire la porta sul router |

⭐ Le condizioni **non spariscono dopo il piano**: stanno nel certificato, in `remotix verifica` e in
`remotix stato` finché valgono (R35); se una si risolve (l'amministratore aggiunge RPM Fusion dopo),
`remotix verifica` lo vede e lo dice.

Il **catalogo** (le combinazioni e le loro regole) ha una versione, una data di scadenza e la versione
minima del motore che lo capisce; il certificato registra quale catalogo ha deciso lo stato di quella
installazione.

#### 6.6.9 Esiti e codici

Ogni messaggio del motore ha:
- una **gravità**: `INFO` · `AVVISO` · `BLOCCANTE`;
- una **natura**: `SERVE_AZIONE` (dell'amministratore) · `RIPROVABILE` (es. rete) · `RECUPERABILE` (la
  ripresa lo sistema) · `SERVE_ANNULLAMENTO` · `FATALE`;
- un **codice stabile** `RX-<AREA>-<NNN>` (`RX-PAM-001` «la pila d'accesso della distribuzione non si
  trova», `RX-H264-003` «la scheda non codifica H.264: su Fedora serve RPM Fusion»), con il testo in
  italiano semplice, il comando che rimedia, e la pagina del manuale.

Lo stesso codice compare nella riga di comando, nel registro, nel certificato, nel manuale e in ogni
futura interfaccia. ⛔ Un codice non si riusa mai per un altro significato.

#### 6.6.10 La fiducia: due catene separate

| catena | che cosa firma | chi la usa |
|---|---|---|
| **A — il motore e il catalogo** | `remotix-install`, `install.sh`, il catalogo | il motore stesso, alla fase 0 TRUST |
| **B — i pacchetti e i depositi** | i `.deb`/`.rpm`/`.pkg.tar.zst` e i metadati dei depositi | il gestore di pacchetti della distribuzione (R17, R18) |

⛔ **Le due catene hanno chiavi diverse**: la chiave dei depositi non autorizza il motore e viceversa.

Il modello (comune alle due):
- **radice**: una chiave madre **fuori linea**, mai sulla macchina che costruisce; firma **sottochiavi**
  con scadenza (un anno), che firmano gli artefatti;
- **distribuzione della radice**: l'impronta della chiave madre è scritta nel motore rilasciato,
  pubblicata sul sito e nel manuale; il pacchetto `remotix-archive-keyring` porta la catena B;
- **rotazione**: una sottochiave nuova firmata dalla madre, pubblicata **prima** che la vecchia scada;
- **revoca**: un elenco firmato di sottochiavi revocate, che il motore scarica con il catalogo;
- **catalogo «fresco»**: firmato, non scaduto, con versione minima del motore ≤ la propria;
- **se la fiducia non si verifica**: ⛔ BLOCCATA (`RX-TRUST-…`), niente viene toccato; si procede solo
  con un catalogo **fuori linea firmato** dato esplicitamente (§6.6.12), mai saltando il controllo.

La **custodia** della chiave madre e la **cadenza** della rotazione sono la **decisione D11** (T8): oggi
non esiste ancora un deposito pubblico. La supply chain è comunque già definita qui, perché TRUST e
ACQUISITION la presuppongono fin dalla T4.

#### 6.6.11 Il certificato si verifica a posteriori

Il certificato è un JSON (più la sua versione leggibile) con: identificativo dell'operazione, stato
finale (§6.6.2), versione del prodotto, **versione e digest del motore**, **versione e digest del
catalogo**, **digest del piano** e dell'insieme risolto, l'impronta, ogni controllo col suo esito, le
condizioni. ⚠ Onestamente: sulla macchina stessa non lo si può firmare in modo che valga contro root.
«Verificabile» vuol dire: `remotix verifica --certificato <file>` ricalcola i digest dagli oggetti
conservati in `/var/lib/remotix/operazioni/<id>/` e **rifà i controlli**, dicendo che cosa è ancora
come allora e che cosa è cambiato.

#### 6.6.12 Senza domande non vuol dire senza consenso; e che cosa vuol dire «senza rete»

- **Senza domande**: il consenso è **dato prima**, come un **piano approvato** (un file, fatto su una
  macchina di riferimento con la stessa impronta vincolante) o un file di risposte che il motore
  trasforma in piano e registra. ⛔ Mai un interruttore che salta CONSENT & SAFETY; ogni azione, anche
  quelle di D5 e D6 (depositi, firewall), è nel piano, nel consenso e nel registro.
- **Senza rete** (R22): un **pacchetto fuori linea**, preparato su una macchina collegata per una
  impronta data, che contiene il catalogo firmato, l'insieme risolto (tutti gli artefatti, con i
  digest e le firme), e i metadati firmati dei depositi. Il motore lo usa come un deposito locale; le
  firme si verificano come in linea.

#### 6.6.13 Il certificato del server (R16)

`/var/lib/remotix/certificati/0-generato.pem` si genera al primo avvio se manca. L'amministratore
mette il suo in `/etc/remotix/certificati.d/` (certificato + chiave, stesso nome base); **vince quello
col nome che viene ultimo in ordine alfabetico**, e quelli dell'amministratore vincono sempre sul
generato (la regola di Cockpit). `remotix certificato --mostra` dice quale è in uso e da dove viene.


---

## 7. Il banco: le macchine virtuali delle distribuzioni

### 7.1 L'impianto — ✅ in piedi il 29 settembre

`banchi/17-distro/17-vm.sh`, copia sul server in `/media/REMOTIX/vm17/`. Discende da
`/media/REMOTIX/vm.sh` (la VM unica di v1): QEMU diretto senza libvirt e senza root, rete in modalità
utente con inoltro delle porte, disco come sovrapposizione sull'immagine ufficiale, che resta intatta.

- **Le immagini** sono quelle *cloud* ufficiali di ogni distribuzione, con cloud-init: debian13,
  ubuntu2604, ubuntu2404, fedora44, fedora43, arch, tumbleweed, leap16, alma10.
- **Le macchine** si chiamano `<distro>-<desktop>` (`fedora44-kde`); `<distro>` da sola è «nuda».
- **Porte** sul server: ssh `2300 + 10·N + k`, REMOTIX `7500 + 10·N + k` (TCP e UDP), con N il numero
  della distribuzione e k del desktop (nudo 0, gnome 1, kde 2, xfce 3, lxqt 4).
- **Comandi**: `crea`, `avvia` (aspetta ssh e cloud-init), `vesti` (il desktop), `ssh`, `ferma`,
  `riavvia` (riavvio VERO dell'ospite, controllato col `boot_id`), `fotografa`/`torna`, `azzera`.
- `[M]` 29 set: **tutte e nove le distribuzioni partono** e rispondono a ssh in 3-39 s; SELinux
  Enforcing su Fedora e Alma.
- ⚠ Sul server QEMU va reinstallato dopo ogni riavvio (il sistema è in memoria): è nella ricetta.
- `[M]` 29 set: **le 27 macchine sono pronte** con la foto «cliente» (tutte rc=0).
- **Quante VM insieme: 4** (decisione dell'utente: *«se il sistema regge passiamo da 4 a 8; se non regge
  torniamo a 4, così ci teniamo un po' di margine»*). `[M]` `17-carico.sh`, 8 VM × 10 min, ognuna con la
  schermata d'accesso, una codifica software Full HD 30 fps e 2,5 GB occupati: **8 × 6 GB e 8 × 4 GB non
  reggono, per la sola memoria** (minimo disponibile 1954 e 2868 MB contro la soglia di 3072; scambio
  medio 1536 e 2882 KiB/s contro 100); codifica 29,7-29,9 fps e ssh ≤ 0,9 s sempre dentro. Le VM
  chiedono ~4,1-4,5 GB l'una, il server ne ha ~30 liberi a riposo (il sistema sta in RAM). Una verifica
  mandata a smentire l'ha confermato, e ha trovato un'uccisione di earlyoom durante lo spegnimento
  parallelo che il giudizio non vedeva (ora le VM si spengono una alla volta, prima di leggere il
  journal). ⚠ Senza *balloon* una VM si tiene la memoria toccata: in ore di lavoro una VM da 6 GB va
  verso i 6 GB, non i 4,5 misurati in 10 minuti. Stima non misurata: 6 × 4 GB probabile, 5 × 6 GB no.

### 7.2 La macchina «come il cliente»

Gli stati di una macchina di prova, con nomi precisi:

| stato | che cos'è | foto |
|---|---|---|
| **BASE** | l'immagine *cloud* ufficiale, dopo cloud-init | il disco nuovo |
| **DESKTOP** | BASE + il desktop col **gruppo di pacchetti ufficiale** della distribuzione (`task-kde-desktop`, `kubuntu-desktop`, `dnf group install kde-desktop-environment`, `pacman -S plasma`, i *pattern* di zypper…), `graphical.target` | `cliente` (il nome di oggi nel banco) |
| **ISO** | una macchina installata **dall'ISO ufficiale** con l'installatore automatico della distribuzione (preseed, autoinstall, kickstart, archinstall, agama) e il suo desktop di serie — la più vicina a una macchina vera | `iso` |

⚠ **Una immagine cloud con un desktop sopra non è la macchina di un cliente**: manca il firewall
acceso, il display manager configurato dall'installatore, a volte SELinux in un altro stato, i
pacchetti che l'ISO mette di serie. ⇒ Il giro di ogni giorno parte da DESKTOP (veloce da rifare); lo
stato **ISO** si costruisce per una macchina per famiglia (debian13-gnome, ubuntu2604-gnome,
fedora44-gnome, arch-kde, tumbleweed-kde, alma10-gnome) e il **giro intero** passa anche da lì. Le
differenze fra DESKTOP e ISO di una stessa combinazione si annotano: se una prova cambia esito fra le
due, la verità è quella di ISO. ⛔ `vesti` non installa niente di REMOTIX: labwc, i gruppi della scheda, i codec sono mestiere
dell'installatore, e la prova deve vederli mancare se lui li dimentica.

### 7.3 Il copione di una prova

Su ogni macchina, automatico:

1. `torna cliente` (DESKTOP) o `torna iso` · impronte della macchina (`/etc`, `/usr`, gruppi, unità, firewall);
2. **installa** (lo script d'ingresso, e separatamente il gestore di pacchetti);
3. un **browser vero** entra e vede il desktop (codifica col ripiego software, Full HD: nella VM non
   c'è la scheda vera);
4. **riavvio vero** della macchina, e si rientra;
5. **aggiorna** a N+1 con una sessione viva, e si guarda che le finestre ci siano ancora;
6. **disinstalla** (`purge`), e confronta le impronte con quelle del punto 1.

### 7.4 Giro corto e giro intero

- **giro corto**, a ogni modifica dell'installatore: una macchina per famiglia (debian13, ubuntu2604,
  fedora44, arch, tumbleweed) — circa 20 minuti;
- **giro intero**, prima di dichiarare pronta una versione: tutte le 27 — circa 2 ore, tre alla volta,
  anche di notte.

### 7.5 Le due cose che la VM non prova

1. **La codifica sulla scheda vera** con la Mesa e i driver di ogni distribuzione (RPM Fusion,
   Packman): si prova in una **scatola** di quella distribuzione, che usa la scheda del server. Una
   prova per famiglia, non a ogni giro.
2. **La scheda data alla VM** (passthrough): oggi impossibile, il server parte con l'IOMMU spento; per
   accenderlo si cambia l'avvio del server, che fa l'utente. Non serve per questa fase.

---

## 8. Le prove — i requisiti misurabili

Ognuna gira sulle VM di §7; «rosso se» è la condizione che la fa fallire.

| # | requisito | la prova | rosso se |
|---|---|---|---|
| R1 | il controllo preliminare non tocca niente | impronte prima/dopo `--verifica` | una differenza |
| R2 | il controllo trova ogni difetto noto, **col suo codice** | macchine **guaste apposta**: senza scheda, senza `h264_vaapi`, NVIDIA proprietaria, porta occupata, PAM mancante, SELinux senza modulo, firewall chiuso | un guasto non detto, detto senza il **codice stabile** (§6.6.9) o senza il comando che rimedia |
| R3 | un comando installa | `install.sh`, e il gestore di pacchetti, su ogni famiglia | uscita ≠ 0, o `remotix verifica` rosso dopo |
| R4 | le dipendenze sono tutte dichiarate | installazione sulla macchina «cliente» senza niente a mano; librerie viste con l'uid di un inquilino | un `not found`, o un pacchetto aggiunto a mano |
| R5 | idempotenza | installare due volte | la seconda scrive qualcosa |
| R6 | ⭐ la disinstallazione **annulla tutto quel che REMOTIX ha fatto** (§6.6.4) — non «rimette la macchina com'era»: una dipendenza aggiornata dal gestore di pacchetti non torna indietro | impronte prima dell'installazione e dopo `purge`, confrontate col registro | una differenza **di origine DIRETTA** rimasta; una differenza INDIRETTA non dichiarata nel certificato; ⛔ un utente tolto da un gruppo in cui c'era **prima** |
| R7 | ⭐ aggiornare non chiude le finestre | due utenti con un browser vero e un terminale aperto; aggiornamento a N+1 | una finestra sparita, un palco morto, uno schermo nero al riattacco |
| R8 | aggiornare costa al massimo un riattacco breve — quattro tempi, misurati a parte: (a) il servizio fermo, (b) il desktop vivo (0 processi del palco persi), (c) la sessione ritrovata dal server nuovo, (d) il browser di nuovo con l'immagine | nella stessa prova di R7 | (b) diverso da zero; (a), (c), (d) oltre le soglie che l'utente sceglierà **dopo la misura di T2** — fino ad allora R8 non è un requisito chiuso |
| R9 | il server nuovo ritrova **tutti** i palchi | `remotix stato` prima e dopo; ciascuno rientra nel **suo** | una sessione viva ma non ritrovata (il caso xrdp) |
| R10 | la scheda del browser già aperta sopravvive al cambio di versione | una scheda aperta durante R7, poi ricaricata | un errore non spiegato |
| R11 | si torna indietro | N → N+1 → N con sessione viva | una sessione persa, o la configurazione non letta |
| R12 | una configurazione sbagliata non spegne il servizio | file rotto in `/etc/remotix/remotix.conf.d/`, poi aggiornamento | il servizio vecchio fermato prima di sapere che il nuovo parte |
| R13 | ⛔ niente funzioni di banco attive | marche e opzioni di banco cercate nel binario **estratto dal pacchetto**, col controllo positivo sul binario di prova | trovate nel pacchetto, o non trovate in quello di prova |
| R14 | ⛔ niente file del banco nel pacchetto | elenco dei file contro una lista nera | una corrispondenza |
| R15 | regge il riavvio | installazione, riavvio vero, connessione | qualcosa che andava prima e non dopo |
| R16 | il certificato nasce al primo avvio e si sostituisce | cancellato e riavviato ⇒ nuovo; uno dell'amministratore ⇒ usato quello | nessun certificato, o quello dell'amministratore ignorato |
| R17 | depositi firmati e verificati | un byte alterato; una firma sbagliata | il gestore lo accetta |
| R18 | la chiave vale solo per REMOTIX, e non tocca i depositi che c'erano | `Signed-By`, niente `trusted.gpg.d`; su una macchina con **altri depositi di terzi già configurati**: le loro chiavi e i loro file invariati, e nessun pacchetto non-REMOTIX installabile dal nostro | chiave globale; un file di un altro deposito cambiato |
| R19 | SELinux attivo, zero rifiuti | Fedora, Alma, Tumbleweed in *enforcing*: sessione completa, poi `ausearch -m avc` | un rifiuto legato a REMOTIX |
| R20 | PAM giusto su ogni famiglia | accesso giusto ⇒ sessione logind `user`, `Remote=yes`; sbagliato ⇒ rifiuto; root ⇒ rifiuto | un caso diverso |
| R21 | installazione senza domande | cloud-init con un file di configurazione depositato | una domanda, un'attesa |
| R22 | installazione senza rete | sorgente preparata prima, VM senza rete | un accesso alla rete |
| R23 | costruzione riproducibile — quattro livelli: binario, pacchetto, metadati del pacchetto, deposito | due costruzioni in due contenitori puliti con lo stesso `SOURCE_DATE_EPOCH` | `diffoscope` trova differenze nel binario o nel pacchetto (T3); nei metadati e nel deposito (T8) |
| R24 | SBOM completo | lo SBOM nomina ngtcp2/nghttp3 con la versione che sta nel binario | versione assente o diversa |
| R25 | benvenuto utile | l'uscita ha le cinque voci di §6.5 punto 8 | una voce mancante |
| R26 | il registro dice tutto | ogni modifica trovata da R6 è in `modifiche.log` | una modifica non registrata |
| R27a | l'installatore **ha preparato la piattaforma** su ogni combinazione della matrice | la certificazione 7a/7b del motore (§6.0) | un controllo richiesto non PASS |
| R27b | REMOTIX **funziona** su quella piattaforma | la suite funzionale corta (fase 15) su ogni VM, in Full HD col ripiego software | un rosso che su Debian non c'è — ⚠ è una prova del **prodotto**, non dell'installatore |
| R28 | ⭐ un'installazione che fallisce a metà si annulla per intero | guasto innestato in ogni passo della fase 6 (rete tagliata, disco pieno, pacchetto rotto) | impronte diverse da prima dell'inizio |
| R29 | la certificazione non mente | la fase 7 su macchine guaste apposta (scheda che non codifica, PAM rotto, porta chiusa) | un «verde» su una macchina guasta |
| R30 | ⭐ un'installazione interrotta si riprende | QEMU ucciso in **ognuno di questi punti**: prima che il passo sia annotato; annotato ma non cominciato; a transazione del gestore di pacchetti cominciata; a metà di un file di configurazione scritto; a unità abilitata ma registro non aggiornato; durante il ritorno indietro. Poi riavvio e motore rilanciato | la macchina resta a metà; un passo rifatto due volte con effetto doppio; la ripresa non porta a COMMITTED o ROLLED_BACK |
| R31 | il piano non si applica a una macchina diversa | piano fatto, macchina cambiata (un pacchetto tolto), poi applicazione | il piano applicato lo stesso |
| R32 | ⭐ UNKNOWN non è mai PASS | ogni controllo della certificazione fatto fallire **nel modo di non sapere** (strumento assente, permesso negato, tempo scaduto) | un PASS, o un certificato COMMITTED senza CONDITIONAL/BLOCKED |
| R33 | i gruppi che c'erano restano | un utente già in `video` prima dell'installazione; dopo `purge` | l'utente tolto da `video` |
| R34 | le cinture si annullano al loro stato di prima | un `logind.conf.d` dell'amministratore già presente che tocca gli stessi tasti; installazione e `purge` | il suo file cambiato, o il comportamento di prima non tornato |
| R35 | lo stato «a condizioni» non sparisce | installazione su Fedora senza RPM Fusion (ripiego software); poi `remotix verifica` e il certificato | la condizione non scritta, o scritta solo nel piano |
| R36 | ⭐ tre interfacce, un solo motore | la stessa installazione guidata da CLI, TUI e GUI su tre copie della stessa macchina | piano, insieme risolto, registro (a parte gli orari) o certificato diversi fra le tre |
| R37 | la GUI non gira da root | processo della finestra durante l'installazione | uid 0 |

---

## 9. Le tappe

| tappa | che cosa | produce | stato |
|---|---|---|---|
| **T0** | il banco delle VM e le 27 macchine «cliente» | `banchi/17-distro/17-vm.sh`, foto `cliente` | 🔨 in corso (29 set: 9 distribuzioni accese, desktop in costruzione) |
| **T1** | REMOTIX **compila e gira** su ogni distribuzione, installato a mano: le cure di §4.4 e §5.1 | il prodotto portabile; R27 verde, a mano | 🔨 compila 7/7; gira: in cura (§11.1) |
| **T2** | la **misura** di §5.2: che cosa uccide i desktop quando si ferma il servizio | la causa, e la stima vera | ✅ 29 set: nessun desktop muore; cura leggera (§5.2) |
| **T3** | le tre **ricette** dei pacchetti e i contenitori di costruzione per famiglia | `.deb`, `.rpm`, `.pkg.tar.zst`; R4, R13, R14, R23 | |
| **T4** | gli oggetti e gli stati di §6.6 (formato, registro, codici), poi il motore con la CLI, fasi 0-4: TRUST, PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY (`remotix verifica`, `install.sh`) | R1, R2, R3, R25 | |
| **T5** | il motore, fasi 5-8: il registro delle azioni, la certificazione, COMMIT / ROLLBACK; la disinstallazione | R5, R6, R26, R28, R29 | |
| **T6** | PAM per famiglia, SELinux, firewall | R19, R20 | |
| **T7** | l'aggiornamento senza chiudere i desktop (secondo T2 e D1) | R7-R12 | |
| **T8** | depositi firmati, canali, ritorno indietro, SBOM | R11, R17, R18, R24 | |
| **T9** | la **TUI** e la **GUI** sul motore finito (R36, R37); senza domande e senza rete; la codifica sulla scheda vera per famiglia (scatole) | R21, R22 | |
| **T10** | il giro intero sulle 27 macchine, e la chiusura | tutti verdi | |

Ordine delle distribuzioni dentro ogni tappa: prima quelle che rendono di più con meno (**Debian 13,
Ubuntu 26.04**), poi **Fedora e Arch**, poi **openSUSE** (la più scomoda per H.264) e **Alma**.

Metodo, come nelle fasi 12-16: incrementi piccoli, la rete completa dopo ognuno; le rifiniture dei
banchi **non fermano** le tappe (*«ci stiamo avvitando in inezie tecniche bloccando il progetto»*,
29 set); le prove mirate si fanno in secondi, il giro intero solo quando serve.

---

## 10. Le decisioni che spettano all'utente

Una per volta, ognuna nel momento in cui serve (la tappa è indicata). Anche R8 aspetta una sua scelta: le soglie dei quattro tempi, **dopo** la misura di T2.

| | la domanda | quando | la proposta |
|---|---|---|---|
| **D1** | ~~Le sessioni aspettano il server nuovo invece di morire con lui?~~ ⭐ **Superata dalla misura di T2**: i desktop sopravvivono già. Resta una domanda più piccola: il figlio muore col padre (per scelta) — va bene così, visto che il desktop resta e il padre nuovo lo ritrova? | T7 | sì: il desktop è la cosa che conta, il figlio si rifà al riattacco |
| **D2** | ngtcp2 e nghttp3 **dentro** il binario, con gli aggiornamenti di sicurezza a carico nostro? | T3 | sì: quasi nessuna distribuzione ha la 1.25 |
| **D3** | La **politica contro i tentativi**: che cosa si vuole — quanti errori, per conto e per indirizzo, blocco o rallentamento, vale anche davanti alla macchina o solo da remoto, chi sblocca e come, che cosa si registra. Da lì si decide se la pila di REMOTIX tiene il `pam_faillock` della distribuzione | T6, con una proposta scritta di minacce e difese | da remoto un blocco per conto permette a chiunque di chiudere fuori il proprietario; proposta: rallentamento per conto + ban per indirizzo in REMOTIX, niente blocco del conto, tutto nel registro |
| **D4** | Le tre cinture (la macchina non si spegne, non si sospende, i tasti non spengono) sulle macchine **degli altri**: sempre, o scelta dell'amministratore all'installazione? | T3 | predefinite, dichiarate nel benvenuto, disattivabili |
| **D5** | RPM Fusion (Fedora) e Packman (openSUSE): l'installatore li **aggiunge chiedendo il consenso**, o si limita a **dire** il comando? | T4 | chiede il consenso, mai in silenzio; senza consenso REMOTIX si installa e il benvenuto dice che la codifica sulla scheda manca |
| **D6** | Il firewall: l'installatore **apre** la porta 7447, o la definisce e dice il comando? | T4 | la apre chiedendo, come D5 |
| **D7** | **Ubuntu 24.04** (LTS fino al 2029, e Mint 22) solo con GNOME: si supporta? Costa OpenSSL 3.5 statico e un `#if` per ffmpeg 6.1 | T1 | sì, solo GNOME, dichiarato |
| **D8** | Su Ubuntu, chi si collega vede il GNOME **di Ubuntu** (dock, colori) o quello **vanilla** di Debian? | T1 | quello di Ubuntu: è quello che l'utente ha davanti al monitor |
| **D9** | Le distribuzioni **immutabili** (Silverblue, Aeon, Kinoite, Kalpa): dentro questa fase o dopo? | fine fase | dopo |
| **D10** | Dove si costruiscono e si ospitano i pacchetti: contenitori nostri e un deposito nostro, o **OBS** di openSUSE (che costruisce per tutte le famiglie, ma vuole progetti pubblici)? | T3 | contenitori nostri finché il codice è privato |
| **D11** | La **custodia della chiave madre** (dove sta, chi la tiene, copia di riserva) e la cadenza della rotazione | T8 | fuori linea, due copie in due posti, sottochiavi annuali |
| **D12** | Con che cosa si fanno **TUI e GUI** (requisito irrinunciabile): per la GUI GTK 4 o Qt 6 (una sola, che si vede bene su tutti e quattro i desktop), per la TUI una libreria a schermo intero | T4, prima di scrivere le interfacce | GUI in **Qt 6** (è di casa su KDE e LXQt, e si integra bene su GNOME e XFCE); TUI con **newt** (è la libreria degli installatori di Debian e Fedora, già presente quasi ovunque) |
| **D13** | **La parte grafica**: le schermate e il percorso (una per fase del motore: controllo, compatibilità, piano da approvare, avanzamento, certificato), l'aspetto (colori, logo ufficiale, caratteri, tema chiaro e scuro, i quattro desktop), il tono e le lingue dei testi | **prima di T9**, su un **prototipo cliccabile** coi dati veri di una VM (per esempio Fedora senza RPM Fusion, per vedere un «a condizioni») — si decide guardando, poi si scrive la GUI vera | il prototipo si può fare presto, in parallelo: dipende solo dagli oggetti di §6.6.1, non dal codice del motore |

**Le scelte di chi installa: quasi nessuna** (indicazione dell'utente, 29 set: *«non riesco ad immaginare
grandi scelte da parte dell'utente sull'installazione di REMOTIX, se non solamente la porta»*):
- **la porta** (predefinita 7447): una sola domanda, che vale per **TCP** (la pagina) **e UDP** (QUIC);
- due **consensi**, non preferenze, e **solo dove servono**: l'archivio esterno per H.264 (solo Fedora
  e openSUSE, D5) e l'apertura del firewall (solo se è acceso, D6);
- ⛔ tutto il resto ha un valore predefinito e **non si chiede**: chi entra (gli utenti della macchina,
  root escluso), il certificato (generato), le tre cinture (attive, dette nel benvenuto, D4), i gruppi
  della scheda. Chi vuole altro lo cambia dopo in `/etc/remotix/remotix.conf.d/`.

⇒ La GUI (e la TUI) sono **cinque schermate**: controllo della macchina · **una** schermata di scelte ·
il piano, con un solo «conferma» · l'avanzamento · il certificato e il benvenuto con l'indirizzo.

---

## 11. Punti da confermare `[?]`

La verifica sulle distribuzioni (29 set) ha chiuso i cinque punti aperti: GNOME 50 confermato con la
cura di §5.1; Fedora con Intel **senza** H.264 di serie (smentita la ricerca sugli installatori);
ngtcp2 minima 1.25.0; `pam_faillock` di Arch 3/900 s/600 s; openSUSE SELinux enforcing di serie e
`common-session-nonlogin`. Restano **da misurare** sulle VM:
- `gnome-remote-desktop` acceso di serie accanto a REMOTIX (porta 3389, niente conflitto; ma apre
  sessioni di cattura sue sullo stesso mutter);
- gli utenti `systemd-homed` (Arch);
- eventuali modifiche di Ubuntu alle unità di gnome-shell 50;
- il salto di labwc 0.8 → 0.9 / 0.20 (wlroots 0.20.2 ha ancora tutti i protocolli che usiamo `[L]`).

---

### 11.1 Gli esiti di T1 (29 set 2026, sera) `[M]`

- **Compila** (T1b + T1a unite, 8ecc925): **7 distribuzioni su 7**, ngtcp2/nghttp3 statiche, `ldd` pulito
  su ognuna; Ubuntu 24.04 si ferma a OpenSSL 3.0 (per D7: poi `codificatore.c:1419,1436` per ffmpeg 6.1 e
  `input.c:1218` per libei 1.2).
- **Gira** (T1c, a mano in 7 VM): si **entra** ovunque («Ammesso», sessione creata), ma col binario del
  prodotto **il desktop non arriva su nessuna**. Le cause:
  - **(A) difetto del prodotto**: senza accelerazione 3D il compositore non offre DMA-BUF, REMOTIX chiede
    solo quelli (`cattura.c:~1487`) e il ripiego sulla memoria scatta solo dopo il primo fotogramma, che
    non arriva mai. Vale per ogni macchina senza scheda (VM, server senza GPU). Cura in corso: ripiego
    sulla memoria **dopo** il fallimento della negoziazione, la copia zero resta la strada di serie.
    Con la memoria da subito (binario di diagnosi) il desktop arriva su Debian, Ubuntu 26.04 (**la cura di
    GNOME 50 funziona**), Arch, Fedora, Alma;
  - **(B) SELinux** su Fedora e Alma: `pam_selinux open` porta a un rifiuto `transition
    unconfined_service_t → unconfined_t` all'esecuzione del figlio; senza `pam_selinux`, zero rifiuti in
    enforcing. ⇒ T6: una regola nostra (come Cockpit) o via `pam_selinux`;
  - **(C) nessun ripiego senza libx264/libx265**: senza depositi di terzi (Fedora, Alma, openSUSE) REMOTIX
    rifiuta di codificare, per scelta scritta nel codice, anche dove c'è openh264 o svt-av1; con RPM
    Fusion (`libavcodec-freeworld`) o Packman (`libavcodec63`) riparte. ⇒ pesa su D5;
  - **(D)** KWin su Tumbleweed e labwc su Leap: tela nera, `DRM_IOCTL_MODE_CREATE_DUMB: Permission denied`
    — classificata «limite della VM», `[?]` **in verifica**: potrebbe essere di piattaforma.
- **Dipendenze di esecuzione misurate** (per T3), oltre al binario: Ubuntu 26.04 `libavcodec62 libswscale9
  libavutil60 gnome-session`; Alma 10 `epel-release`, CRB, `libavcodec-free libavutil-free libswscale-free`;
  Tumbleweed `libavcodec63 libavutil61 libswscale10`; Leap 16 `libavcodec61 libavutil59 libswscale8
  libpipewire-0_3-0 libva2 libei1 labwc xwayland` (XFCE 4.20 senza Xwayland non parte); Debian e Arch
  niente in più; Fedora la porta 7447 in firewalld (acceso dopo il gruppo Workstation).
- `provisiona.sh` installa sempre il PAM di Debian e la sua verifica si accontenta di «pam_systemd»: su
  Fedora e Arch direbbe verde con un PAM con cui non entra nessuno (**falso verde**: conferma che
  l'installatore si scrive da capo).
- Trappola del banco: il browser su `127.0.0.1`, non `localhost` (QEMU inoltra UDP solo in IPv4, Chrome
  manda QUIC a `::1`).

---

## 12. Fuori da questa fase

- le distribuzioni immutabili (D9);
- le distribuzioni senza systemd;
- la scheda data alla VM (passthrough) e le prestazioni per distribuzione;
- un pacchetto **dentro** le distribuzioni ufficiali (Debian, Fedora): con ngtcp2 incorporata non
  passerebbe le loro regole; è un passo successivo, se mai.

---

## 13. Il registro delle modifiche della fase 17 — per il manuale tecnico

*Ogni modifica si annota qui nel momento in cui entra: commit · che cosa · perché · misura ·
installata sì/no.*

### 13.1 Il prodotto (`src/`)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| d7f82c2 | `src/Makefile`: le intestazioni di ffmpeg da `pkg-config --cflags libavcodec libavutil libswscale` | su Fedora e Alma (ffmpeg-free) stanno in `/usr/include/ffmpeg`: senza, `codificatore.c:24` non trova `<libavcodec/avcodec.h>`. Su Debian aggiunge solo `-I/usr/include/x86_64-linux-gnu`, che c'era già | `[M]` 29 set: Fedora 44 e Alma 10 compilano; Debian 13 identico (1 solo avviso, `main.c:500`) | no |
| c1573ae | `sessione.c` `unita_shell()`: la Shell si sceglie dal `FragmentPath` che il gestore d'utente dà per `@wayland` (il file `@wayland` ⇒ quella; il modello `@.service` ⇒ `@user`; altro ⇒ si ferma e lo dice); drop-in in `<istanza>.d/`, mai nel modello; la rilettura dell'`ExecStart` sulla stessa unità; lo sgombero conosce `@wayland.d` e `@user.d`; `provisiona.sh` pulisce e controlla anche `@user.d` e `@.d` (solo il nostro file) | GNOME 50 avvia `@user`: il drop-in su `@wayland` non si applicava e il controllo dava un falso verde (§5.1) | `[M]` compila pulito nel contenitore Debian 13; `[M]` sul portatile (GNOME 48.7) `FragmentPath` = `…/org.gnome.Shell@wayland.service`; `[M]` con un modello finto `x@.service` il `FragmentPath` di `x@wayland` è il modello e l'`ExecStart` di `x@user` porta `--mode=user`. ⛔ GNOME 50 vero non provato: tocca alla T1 sulle VM | no |
| 61ad596 | PAM per famiglia: `src/remotix.pam` (Debian/Ubuntu), `.fedora` (`password-auth`+`postlogin`, `pam_selinux` close/open, `pam_loginuid`; `pam_systemd` da `password-auth`), `.suse` (`common-*`, `common-session-nonlogin` + `pam_systemd`; va in `/usr/lib/pam.d`), `.arch` (`system-remote-login`). In tutti root escluso con `pam_listfile` su `/etc/remotix/utenti-negati`, in `auth` e `requisite` (niente oracolo sulla parola di root), `onerr=fail` (Cockpit usa `succeed`: il file perso toglierebbe l'esclusione in silenzio). `pam_faillock` non scelto da noi: D3 resta aperta, scritto in ogni file. `main.c` cerca il servizio in `/etc/pam.d` e poi in `/usr/lib/pam.d`; il testo su «other» corretto anche in `autenticazione.c` (e nella copia `banchi/rcp/`). `provisiona.sh` e `costruisci.sh` scrivono `utenti-negati` (root) se manca | `@include` è Debian: altrove nessuno entra (§4.3); il messaggio diceva «other è pam_deny su Debian», falso | `[M]` quattro contenitori (debian:13, fedora:44, archlinux, tumbleweed), `pam_authenticate`+`pam_acct_mgmt`: senza il file ⇒ respinto («Error in service module»); utente giusto ⇒ entra; parola sbagliata ⇒ respinto; root con la parola giusta ⇒ respinto senza che la parola venga chiesta. ⛔ La sessione (`pam_open_session`, `pam_selinux`, `pam_systemd`) non provata: nei contenitori non c'è systemd. ⚠ Da annotare, non fatto (tocca il C): `main.c` all'avvio non guarda `utenti-negati` | no |
| c687c0c | `certificati.c`: il nome del soggetto si costruisce con `X509_NAME_new` e si consegna con `X509_set_subject_name`/`X509_set_issuer_name`, invece di scrivere nel nome restituito da `X509_get_subject_name`; e l'esito di `X509_NAME_add_entry_by_txt` ora si guarda | in OpenSSL 4.0 `X509_get_subject_name` restituisce `const X509_NAME *` (Ubuntu 26.10, Fedora rawhide) | `[M]` `certificati.c` da solo con `-Wall -Werror`: su fedora:rawhide (OpenSSL **4.0.2**) il vecchio non compila (`discards 'const' qualifier`, riga 149), il nuovo sì; su debian:13 (3.5.7) compilano tutt'e due; in entrambi i certificati generati hanno soggetto = emittente = `CN=192.168.0.2` e il SAN giusto. ⚠ Il resto di `src/` con OpenSSL 4 non è stato compilato | no |
| e177e0c | `sessione.c` `registro_sessione_percorso()`: il registro della sessione passa da `/tmp/remotix-sessione-<uid>.log` a `$XDG_STATE_HOME/remotix/sessione.log` (di solito `~/.local/state/remotix/`); cartella 0700 verificata (vera, nostra, non scrivibile da altri), file aperto con `O_NOFOLLOW`, 0600, verificato regolare e nostro; se non si può, ripiego dichiarato su `XDG_RUNTIME_DIR`, e senza nemmeno quella la sessione parte senza registro (detto); il percorso passa alla shell con `g_shell_quote` | nome prevedibile in `/tmp`: un altro utente lo crea prima e il desktop non parte (con `protected_regular`), in silenzio — è R10-A9 di `fasi/10` | `[M]` compila pulito nel contenitore Debian 13; `[M]` le tre funzioni estratte e fatte girare da utente: caso normale ⇒ file 0600 al posto nuovo; cartella collegamento, file collegamento a `/etc/passwd`, cartella 0777 ⇒ ripiego dichiarato; niente casa e niente runtime ⇒ NULL dichiarato. `grep`: nessun banco legge il vecchio file (i banchi `04-*`/`06-*` usano un loro `/run/user/<uid>/remotix-sessione.log`) | no |
| fe9f354 | `Makefile`: minimi veri dichiarati e CONTROLLATI da `make dipendenze` con `pkg-config --atleast-version` (libavcodec ≥ 61.13.100, libavutil ≥ 59, libswscale ≥ 8, OpenSSL ≥ 3.5.0, ngtcp2 e ngtcp2_crypto_ossl ≥ 1.25.0, nghttp3 ≥ 1.18.0, libei ≥ 1.1.0, libpipewire ≥ 0.3.48, gio ≥ 2.80), tre esiti distinti (va / troppo vecchia / pkg-config non la conosce); con `PREFISSO` la cartella delle librerie si chiede a `pkg-config` dentro il prefisso (`lib64`, `lib/<multiarch>`, `lib`), e se non risponde si prendono le cartelle che esistono; `costruisci.sh` guarda anche `lib64`; tolto l'unico avvertimento della costruzione (`/*` in un commento di `main.c`) | «libavcodec ≥ 61» non bastava (serve FFmpeg 7.1); `dipendenze` guardava solo le intestazioni; il rpath assumeva `lib` (Fedora/SUSE: `lib64`) | `[R]` FFmpeg `APIchanges`: `avcodec_get_supported_config` = lavc 61.13.100; `[R]` libei.h 1.0.0 senza `ei_region_get_mapping_id`, 1.1.0 con; `[R]` pipewire `keys.h` 0.3.44 senza `PW_KEY_NODE_FORCE_QUANTUM`; `[M]` `cattura.c`/`cursore.c`/`suono.c` compilano con pipewire 0.3.48 (ubuntu:22.04), `input.c` con libei 1.2.1 (ubuntu:24.04); `[M]` `make dipendenze` nel contenitore: tutto OK, e con minimi finti dà NO/?? ed esce 2; `[M]` prefisso finto con `.pc` in `lib64` ⇒ `-L…/lib64 -Wl,-rpath,…/lib64`, senza `.pc` ⇒ la cartella `lib64` che c'è; costruzione da zero pulita, zero avvertimenti. `[?]` il minimo vero di nghttp3 non cercato | no |
| — | ⚠ **non fatto, annotato**: `figlio.c:4684` apre sempre `renderD128` per il codificatore: con due schede può prendere quella sbagliata; va scelto dal driver (§4.4). Fuori dalla T1a per mandato | — | — | — |

### 13.2 L'impianto di prova (banchi, VM)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| (questo commit) | `banchi/17-distro/17-vm.sh`: una VM per `<distro>-<desktop>` dalle immagini cloud ufficiali, cloud-init, porte per macchina, `vesti` col gruppo di pacchetti ufficiale, foto «cliente», riavvio vero controllato col `boot_id` | decisione dell'utente del 29 set: le prove dell'installatore in VM, una per desktop | `[M]` 9 distribuzioni su 9 accese, ssh in 3-39 s | copiata sul server |
| 12f6782…(questo commit) | `banchi/17-distro/17-carico.sh`: la prova di carico delle VM; ritmo dai contatori dei fotogrammi su ~60 s; journal letto con sudo **dopo** lo spegnimento, VM spente una alla volta | decidere quante VM insieme (4 o 8) | `[M]` 8 VM non reggono (memoria); si resta a 4 | copiata sul server |
| (questo commit) | `banchi/17-t2/`: la misura di T2 (sessione viva con tre testimoni e sentinella a 50 ms; ferma / uccidi-padre / uccidi-figlio; catena dal journal) | §5.2 | `[M]` 10 prove su 4 desktop: nessun desktop muore | sul server, in /media/REMOTIX/tmp/t2 |
| (questo commit) | `src/costruzione/`: un `Contenitore.<bersaglio>` per debian13, ubuntu2604, ubuntu2404, fedora44, alma10 (EPEL+CRB), arch, tumbleweed, leap16 — dipendenze dal gestore di pacchetti della distribuzione, ngtcp2 1.25.0 e nghttp3 1.18.0 **statiche** (`quic-statiche.sh`, solo `.a` in `/usr/local/lib`, `LIBRARY_PATH`: il Makefile non cambia); `costruisci-tutti.sh` costruisce uno o tutti in una copia dell'albero e scrive per bersaglio binario, registri, versioni, `ldd` fatto nel contenitore. `src/Contenitore` resta com'era | §6.2 e §6.3: si compila per ogni distribuzione, niente `ld.so.conf.d` | `[M]` 29 set, sul portatile: **7 su 7 compilano**, `ldd` senza «not found» e senza ngtcp2/nghttp3. Ubuntu 24.04 si ferma a ngtcp2 (OpenSSL 3.0.13 senza QUIC); una sonda senza il ramo OpenSSL mostra poi solo `codificatore.c:1419,1436` (ffmpeg 6.1) e `ei_disconnect` assente (`input.c:1218`, libei 1.2.1) — D7. Versioni: OpenSSL 3.5.0 (Leap) … 3.6.4 (Arch); libavcodec 61 (Debian, Alma, Leap), 62 (Ubuntu, Fedora), 63 (Arch, TW); libei 1.3.901…1.6.0; PipeWire 1.4.2…1.6.9; glib 2.80…2.88. Arch e TW hanno già ngtcp2 1.25 con crypto_ossl: usabile, non usata per uniformità | no (solo portatile) |
| (questo commit) | **T1c**: `banchi/17-distro/17-t1c-installa.sh` (REMOTIX a mano in una VM, famiglia per famiglia: dipendenze, PAM, `utenti-negati`, polkit/logind/sleep, utente `prova`, unità transitoria sulla 7447), `17-t1c-browser.py` (Chrome vero con le guide di `12-client-veri.py`: apri → entra → primo fotogramma col giudice dei pixel), `17-t1c-guarda.sh` (labwc suo sull'Intel, `127.0.0.1` perché l'inoltro UDP di QEMU è solo IPv4) | far girare il prodotto portato e vederlo da un browser vero, prima dell'installatore | `[M]` 29 set, 7 VM «cliente», Full HD. **Col binario del prodotto: 0 su 7.** Tutte entrano («Ammesso»), nessuna dipinge: (1) nella VM `virtio_gpu` senza 3D la negoziazione PipeWire muore con «no more input formats» (strada della SCHEDA con modificatore obbligatorio, `cattura.c:1487`; il ripiego sulla memoria scatta solo dopo un fotogramma, `figlio.c:5362`) — Debian, Ubuntu, Arch, TW; (2) Fedora e Alma: figlio uscito con 37, AVC `{ transition } unconfined_service_t → unconfined_t` da `pam_selinux open`; (3) Fedora/Alma/openSUSE senza depositi di terzi: «libx265 non c'è in questa libavcodec: non se ne prende un altro» (Chrome chiede HEVC). **Col binario di diagnosi** (`-DCOPIA_ZERO=0`, non il prodotto): PASS Debian 13, Ubuntu 26.04 (GNOME 50, `@user` con `--headless`), Arch KDE; Fedora 44 e Alma 10 PASS solo con `pam_selinux` tolto dal PAM + `libavcodec-freeworld` (RPM Fusion); TW KDE (con Packman) e Leap XFCE BLOCKED dalla VM: KWin e labwc non allocano (`DRM_IOCTL_MODE_CREATE_DUMB: Permission denied` sul nodo virtio) ⇒ tela nera. `provisiona.sh` fuori da Debian installa `remotix.pam` (Debian) e la sua verifica dice lo stesso «⭐ a posto» | copiati sul server (`/media/REMOTIX/vm17/t1c/`) |

### 13.3 L'ambiente del server

| che cosa | perché |
|---|---|
| `qemu-system-x86 qemu-utils genisoimage ovmf` installati, `nicfio` nel gruppo `kvm` (29 set) | le VM di §7; ⚠ volatile: sta nella ricetta del dopo-riavvio |
