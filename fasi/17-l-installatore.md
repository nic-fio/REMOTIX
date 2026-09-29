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
| Fedora 43 | ✅ | ✅ | ✅ | ✅ | GNOME 49; esce di supporto a fine 2026 |
| **Alma / Rocky / RHEL 10** | ✅ | ✅ | ⛔ | ⛔ | KDE da EPEL; né labwc né XFCE né LXQt in RHEL/EPEL 10; su AMD niente VA-API (Mesa senza) |
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

⇒ **27 macchine virtuali** nella matrice di oggi (6 distribuzioni × 4 desktop, più Alma × 2, più
Ubuntu 24.04 × GNOME se D7 dice sì).

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

### 5.2 Aggiornare senza chiudere i desktop: la causa non è quella scritta

`PIANO.md` (Fase 15, «Il servizio»), `fasi/10` §7.5, `SPECIFICHE.md:374` e `DECISIONI.md:3178` dicono
che fermare il servizio uccide le sessioni **per `KillMode=mixed`**. La verifica sul codice (`[L]`):

1. il padre gira da root nell'unità del servizio;
2. il figlio di ogni utente apre la sessione con `pam_systemd` ⇒ logind lo sposta in
   `session-cN.scope`, **fuori dall'unità**; il palco (gnome-session, startplasma, labwc) resta lì con
   lui; `gnome-shell`, `kwin` e PipeWire stanno in `user@UID.service`;
3. ⇒ `KillMode=mixed` colpisce solo quel che resta nell'unità: **né il figlio né il palco**;
4. il figlio muore col padre **per scelta**, per tre strade volute: `figli_spegni()` (`figlio.c:2987`),
   `PR_SET_PDEATHSIG` (`figlio.c:6966`) e la chiusura del socket (`figlio.c:7338`);
5. il fatto misurato il 25 agosto resta vero: il desktop **muore**. La causa vera è **da misurare**:
   il candidato è la morte del capo della sessione logind e la reazione a catena che ne segue.

⇒ Prima si **misura** (mezza giornata: `systemd-cgls` e `loginctl` prima di fermare il servizio, poi i
registri, sui 4 desktop). Poi, secondo quel che si vede:
- se il palco sopravvive già: il padre nuovo deve **ritrovare** i palchi vivi, e `loginctl
  terminate-user` (`figlio.c:1577`) va disinnescato — **1-2 giorni** più la rete;
- se il palco muore col capo della sessione: il figlio si divide in un **custode** che tiene la
  sessione PAM e sopravvive al padre, e un figlio di cattura che rinasce dentro — **3-5 giorni** più
  la rete e le prove di guasto.

Quel che i migliori insegnano (`[L]`): **NoMachine** butta fuori tutti a ogni aggiornamento e lo scrive
nella guida; **xrdp** ha sessioni che sopravvivono ma che nessuno ritrova (schermo nero). ⇒ Far
sopravvivere è metà del lavoro, **ritrovare** è l'altra metà. Lo strumento fatto apposta è il deposito
dei descrittori di systemd (*fdstore*), che sopravvive a un `systemctl restart`. Le connessioni QUIC
**non** sopravvivono comunque: la promessa onesta è *«aggiornare costa a chi è collegato un riattacco
di pochi secondi; le finestre restano»*. ⇒ **Decisione D1.**

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

### 7.2 La macchina «come il cliente»

`vesti` installa il desktop **col gruppo di pacchetti ufficiale** della distribuzione (`task-kde-desktop`,
`kubuntu-desktop`, `dnf group install kde-desktop-environment`, `pacman -S plasma`, i *pattern* di
zypper…), poi la macchina si spegne e si fotografa: la foto **«cliente»** è il punto da cui parte ogni
prova. ⛔ `vesti` non installa niente di REMOTIX: labwc, i gruppi della scheda, i codec sono mestiere
dell'installatore, e la prova deve vederli mancare se lui li dimentica.

### 7.3 Il copione di una prova

Su ogni macchina, automatico:

1. `torna cliente` · impronte della macchina (`/etc`, `/usr`, gruppi, unità, firewall);
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
| R2 | il controllo trova ogni difetto noto | macchine **guaste apposta**: senza scheda, senza `h264_vaapi`, porta occupata, PAM mancante, SELinux senza modulo, firewall chiuso | un guasto non detto, o detto senza il comando che rimedia |
| R3 | un comando installa | `install.sh`, e il gestore di pacchetti, su ogni famiglia | uscita ≠ 0, o `remotix verifica` rosso dopo |
| R4 | le dipendenze sono tutte dichiarate | installazione sulla macchina «cliente» senza niente a mano; librerie viste con l'uid di un inquilino | un `not found`, o un pacchetto aggiunto a mano |
| R5 | idempotenza | installare due volte | la seconda scrive qualcosa |
| R6 | ⭐ la disinstallazione rimette la macchina com'era | impronte prima dell'installazione e dopo `purge` | una differenza non registrata; ⛔ un utente tolto da un gruppo in cui c'era prima |
| R7 | ⭐ aggiornare non chiude le finestre | due utenti con un browser vero e un terminale aperto; aggiornamento a N+1 | una finestra sparita, un palco morto, uno schermo nero al riattacco |
| R8 | aggiornare costa al massimo un riattacco breve | tempo fra l'ultimo fotogramma prima e il primo dopo | oltre la soglia che l'utente sceglierà |
| R9 | il server nuovo ritrova **tutti** i palchi | `remotix stato` prima e dopo; ciascuno rientra nel **suo** | una sessione viva ma non ritrovata (il caso xrdp) |
| R10 | la scheda del browser già aperta sopravvive al cambio di versione | una scheda aperta durante R7, poi ricaricata | un errore non spiegato |
| R11 | si torna indietro | N → N+1 → N con sessione viva | una sessione persa, o la configurazione non letta |
| R12 | una configurazione sbagliata non spegne il servizio | file rotto in `/etc/remotix/remotix.conf.d/`, poi aggiornamento | il servizio vecchio fermato prima di sapere che il nuovo parte |
| R13 | ⛔ niente funzioni di banco attive | marche e opzioni di banco cercate nel binario **estratto dal pacchetto**, col controllo positivo sul binario di prova | trovate nel pacchetto, o non trovate in quello di prova |
| R14 | ⛔ niente file del banco nel pacchetto | elenco dei file contro una lista nera | una corrispondenza |
| R15 | regge il riavvio | installazione, riavvio vero, connessione | qualcosa che andava prima e non dopo |
| R16 | il certificato nasce al primo avvio e si sostituisce | cancellato e riavviato ⇒ nuovo; uno dell'amministratore ⇒ usato quello | nessun certificato, o quello dell'amministratore ignorato |
| R17 | depositi firmati e verificati | un byte alterato; una firma sbagliata | il gestore lo accetta |
| R18 | la chiave vale solo per REMOTIX | `Signed-By`, niente `trusted.gpg.d` | chiave globale |
| R19 | SELinux attivo, zero rifiuti | Fedora, Alma, Tumbleweed in *enforcing*: sessione completa, poi `ausearch -m avc` | un rifiuto legato a REMOTIX |
| R20 | PAM giusto su ogni famiglia | accesso giusto ⇒ sessione logind `user`, `Remote=yes`; sbagliato ⇒ rifiuto; root ⇒ rifiuto | un caso diverso |
| R21 | installazione senza domande | cloud-init con un file di configurazione depositato | una domanda, un'attesa |
| R22 | installazione senza rete | sorgente preparata prima, VM senza rete | un accesso alla rete |
| R23 | costruzione riproducibile | due costruzioni in due contenitori puliti | `diffoscope` trova differenze |
| R24 | SBOM completo | lo SBOM nomina ngtcp2/nghttp3 con la versione che sta nel binario | versione assente o diversa |
| R25 | benvenuto utile | l'uscita ha le cinque voci di §6.5 punto 8 | una voce mancante |
| R26 | il registro dice tutto | ogni modifica trovata da R6 è in `modifiche.log` | una modifica non registrata |
| R27 | il desktop nasce su ogni combinazione della matrice | la suite funzionale corta (fase 15) su ogni VM, in Full HD col ripiego software | un rosso che su Debian non c'è |
| R28 | ⭐ un'installazione che fallisce a metà si annulla per intero | guasto innestato in ogni passo della fase 6 (rete tagliata, disco pieno, pacchetto rotto) | impronte diverse da prima dell'inizio |
| R30 | ⭐ un'installazione interrotta si riprende | corrente tolta alla VM (kill di QEMU) in ogni passo della fase 6, poi riavvio e motore rilanciato | la macchina resta a metà, o la ripresa non la porta a «completata» o «annullata» |
| R31 | il piano non si applica a una macchina diversa | piano fatto, macchina cambiata (un pacchetto tolto), poi applicazione | il piano applicato lo stesso |
| R29 | la certificazione non mente | la fase 7 su macchine guaste apposta (scheda che non codifica, PAM rotto, porta chiusa) | un «verde» su una macchina guasta |

---

## 9. Le tappe

| tappa | che cosa | produce | stato |
|---|---|---|---|
| **T0** | il banco delle VM e le 27 macchine «cliente» | `banchi/17-distro/17-vm.sh`, foto `cliente` | 🔨 in corso (29 set: 9 distribuzioni accese, desktop in costruzione) |
| **T1** | REMOTIX **compila e gira** su ogni distribuzione, installato a mano: le cure di §4.4 e §5.1 | il prodotto portabile; R27 verde, a mano | |
| **T2** | la **misura** di §5.2: che cosa uccide i desktop quando si ferma il servizio | la causa, e la stima vera | |
| **T3** | le tre **ricette** dei pacchetti e i contenitori di costruzione per famiglia | `.deb`, `.rpm`, `.pkg.tar.zst`; R4, R13, R14, R23 | |
| **T4** | il motore, fasi 0-4: TRUST, PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY (`remotix verifica`, `install.sh`) | R1, R2, R3, R25 | |
| **T5** | il motore, fasi 5-8: il registro delle azioni, la certificazione, COMMIT / ROLLBACK; la disinstallazione | R5, R6, R26, R28, R29 | |
| **T6** | PAM per famiglia, SELinux, firewall | R19, R20 | |
| **T7** | l'aggiornamento senza chiudere i desktop (secondo T2 e D1) | R7-R12 | |
| **T8** | depositi firmati, canali, ritorno indietro, SBOM | R11, R17, R18, R24 | |
| **T9** | senza domande e senza rete; la codifica sulla scheda vera per famiglia (scatole) | R21, R22 | |
| **T10** | il giro intero sulle 27 macchine, e la chiusura | tutti verdi | |

Ordine delle distribuzioni dentro ogni tappa: prima quelle che rendono di più con meno (**Debian 13,
Ubuntu 26.04**), poi **Fedora e Arch**, poi **openSUSE** (la più scomoda per H.264) e **Alma**.

Metodo, come nelle fasi 12-16: incrementi piccoli, la rete completa dopo ognuno; le rifiniture dei
banchi **non fermano** le tappe (*«ci stiamo avvitando in inezie tecniche bloccando il progetto»*,
29 set); le prove mirate si fanno in secondi, il giro intero solo quando serve.

---

## 10. Le decisioni che spettano all'utente

Una per volta, ognuna nel momento in cui serve (la tappa è indicata).

| | la domanda | quando | la proposta |
|---|---|---|---|
| **D1** | Le sessioni **aspettano** il server nuovo per qualche secondo invece di morire con lui? Cambia una scelta scritta (*«nessun orfano attaccato al monitor virtuale di un utente»*): la garanzia resta, con un termine invece che subito | T7, dopo la misura di T2 | sì, con un termine di 30-60 s |
| **D2** | ngtcp2 e nghttp3 **dentro** il binario, con gli aggiornamenti di sicurezza a carico nostro? | T3 | sì: quasi nessuna distribuzione ha la 1.25 |
| **D3** | Il **blocco dei tentativi** della distribuzione (`pam_faillock`: 3 errori ⇒ conto chiuso 10 minuti, anche davanti alla macchina) si tiene, o REMOTIX usa una pila sua senza, e si affida al proprio ban dell'indirizzo? | T6 | pila nostra senza faillock: da remoto chiunque potrebbe chiudere fuori il proprietario |
| **D4** | Le tre cinture (la macchina non si spegne, non si sospende, i tasti non spengono) sulle macchine **degli altri**: sempre, o scelta dell'amministratore all'installazione? | T3 | predefinite, dichiarate nel benvenuto, disattivabili |
| **D5** | RPM Fusion (Fedora) e Packman (openSUSE): l'installatore li **aggiunge chiedendo il consenso**, o si limita a **dire** il comando? | T4 | chiede il consenso, mai in silenzio; senza consenso REMOTIX si installa e il benvenuto dice che la codifica sulla scheda manca |
| **D6** | Il firewall: l'installatore **apre** la porta 7447, o la definisce e dice il comando? | T4 | la apre chiedendo, come D5 |
| **D7** | **Ubuntu 24.04** (LTS fino al 2029, e Mint 22) solo con GNOME: si supporta? Costa OpenSSL 3.5 statico e un `#if` per ffmpeg 6.1 | T1 | sì, solo GNOME, dichiarato |
| **D8** | Su Ubuntu, chi si collega vede il GNOME **di Ubuntu** (dock, colori) o quello **vanilla** di Debian? | T1 | quello di Ubuntu: è quello che l'utente ha davanti al monitor |
| **D9** | Le distribuzioni **immutabili** (Silverblue, Aeon, Kinoite, Kalpa): dentro questa fase o dopo? | fine fase | dopo |
| **D10** | Dove si costruiscono e si ospitano i pacchetti: contenitori nostri e un deposito nostro, o **OBS** di openSUSE (che costruisce per tutte le famiglie, ma vuole progetti pubblici)? | T3 | contenitori nostri finché il codice è privato |

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

### 13.2 L'impianto di prova (banchi, VM)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| (questo commit) | `banchi/17-distro/17-vm.sh`: una VM per `<distro>-<desktop>` dalle immagini cloud ufficiali, cloud-init, porte per macchina, `vesti` col gruppo di pacchetti ufficiale, foto «cliente», riavvio vero controllato col `boot_id` | decisione dell'utente del 29 set: le prove dell'installatore in VM, una per desktop | `[M]` 9 distribuzioni su 9 accese, ssh in 3-39 s | copiata sul server |

### 13.3 L'ambiente del server

| che cosa | perché |
|---|---|
| `qemu-system-x86 qemu-utils genisoimage ovmf` installati, `nicfio` nel gruppo `kvm` (29 set) | le VM di §7; ⚠ volatile: sta nella ricetta del dopo-riavvio |
