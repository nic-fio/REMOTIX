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
| **le dipendenze che mancano le porta REMOTIX** | *«se ci sono pacchetti/dipendenze assenti da una particolare distro, REMOTIX le deve includere e/o scaricare»*; eccezione i codec brevettati, confine i desktop | `DECISIONI.md` §10.6; D2 chiusa |
| **una VM per desktop** | *«4 VM distinte, esempio Ubuntu/GNOME, Ubuntu/KDE, Ubuntu/XFCE, Ubuntu/LXQt»* | il cliente ha di solito **un** desktop: con quattro insieme, un pezzo dimenticato per XFCE arriverebbe lo stesso trascinato da KDE, e la prova direbbe verde |

---

## 3. Dove REMOTIX può girare: la matrice

Distribuzioni e desktop che entrano nella fase (✅ = da portare e provare; ⛔ = fuori, col perché).

| distribuzione | GNOME | KDE | XFCE | LXQt | note |
|---|---|---|---|---|---|
| **Debian 13** (riferimento) | ✅ | ✅ | ✅ | ✅ | la base di oggi |
| **Ubuntu 26.04 LTS** | ✅ | ✅ | ✅ | ✅ | GNOME 50 (§5.1); il GNOME «vanilla» va installato (§4.6) |
| Ubuntu 24.04 LTS | ⛔ | ⛔ | ⛔ | ⛔ | **fuori** (D7, decisione dell'utente del 29 set): si parte dalla 26.04. KDE 5.27, XFCE 4.18 e LXQt 1.4 non vanno su Wayland; GNOME 46 sì, ma chiederebbe di portare dentro OpenSSL 3.5 e due adattamenti per ffmpeg 6.1 e libei 1.2. Con lei resta fuori Mint 22 (Mint 23 sarà «compatibile, non certificata») |
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

⇒ **La matrice di certificazione: 26 macchine virtuali** — Debian 13, Ubuntu 26.04, Fedora 44, Arch,
Tumbleweed, Leap 16 × 4 desktop (24), più Alma 10 × 2 (GNOME, KDE) = **26**. **Fedora 43 e Ubuntu 24.04 (D7) sono analizzate ma fuori
dalla matrice.**

⚠ **Che cosa si certifica, e che cosa no.** Si certifica solo quel che gira nelle nostre VM: **Alma 10**,
non «la famiglia RHEL 10». Rocky 10 e RHEL 10 si dichiarano **compatibili, non certificate**: stessa
base di pacchetti, ma nessuno le ha provate. Lo stesso per Manjaro ed EndeavourOS rispetto ad Arch,
e per Mint 23 rispetto a Ubuntu 26.04. Una derivata diventa certificata solo con la sua VM nella
matrice.

### 3.1 Le versioni supportate — per il manuale tecnico

*Richiesta dell'utente (30 set 2026): «andrà documentato, anche nel manuale tecnico, da quali versioni gli
SO sono supportati da REMOTIX». ⚠ La fonte unica è il **catalogo** del motore (§6.6.8): la tabella del
manuale si **genera** dal catalogo a ogni rilascio, non si ricopia a mano. Questa è quella di oggi.*

**Le distribuzioni**

| distribuzione | versione minima | stato | desktop | condizioni |
|---|---|---|---|---|
| Debian | **13** (Trixie) | certificata | GNOME, KDE, XFCE, LXQt | — |
| Ubuntu | **26.04 LTS** | certificata | GNOME, KDE, XFCE, LXQt | `gnome-session` per GNOME (D8) |
| Fedora | **44** | certificata | GNOME, KDE, XFCE, LXQt | H.264: RPM Fusion (D5); PAM senza `pam_selinux` fino a T6 |
| AlmaLinux | **10.1** (OpenSSL 3.5) | certificata | GNOME, KDE | EPEL e CRB; H.264: RPM Fusion; niente XFCE/LXQt |
| Arch Linux | rolling (da set 2026) | certificata | GNOME, KDE, XFCE, LXQt | — |
| openSUSE Tumbleweed | rolling (da set 2026) | certificata | GNOME, KDE, XFCE, LXQt | H.264: Packman; `breeze6-wallpapers` (KDE) |
| openSUSE Leap | **16.0** | certificata | GNOME, KDE, XFCE, LXQt | H.264: Packman; un carattere scalabile per LXQt (`google-droid-fonts`) |
| Rocky Linux, RHEL | 10.1 | compatibile, non certificata | GNOME, KDE | come Alma |
| Manjaro, EndeavourOS | rolling | compatibile, non certificata | come Arch | Manjaro è indietro di qualche settimana |
| Linux Mint | **23** (base 26.04) | compatibile, non certificata | quelli di Ubuntu (non Cinnamon) | come Ubuntu |

**Il principio** (`DECISIONI.md` §10.9): prodotto nuovo, tecnologie di nuova generazione; una versione
**entra** quando ha i componenti minimi e passa il giro sulle VM, **esce** quando la distribuzione smette di
aggiornarla.

**Fuori, e perché**: Debian 12 e RHEL 9 (base troppo vecchia: mutter 43/GNOME 40, niente libei, niente
labwc); Ubuntu 24.04 e Mint 22 (D7); Fedora 43 (fuori supporto a fine 2026); openSUSE Leap 15.6 (fine vita);
SLES 16 (solo GNOME, niente Packman: si rivede su richiesta); distribuzioni senza systemd; immutabili (D9).

**Le versioni minime dei componenti** (per chi usa una distribuzione non in elenco; `[L]` dal codice e dalle
misure della fase):

| componente | minimo | perché |
|---|---|---|
| nucleo Linux | quello della distribuzione certificata più vecchia (6.12) | driver i915/xe e amdgpu, DMA-BUF |
| systemd / logind | con `systemctl --user` e sessioni `Remote=yes` | le sessioni per utente |
| OpenSSL | **3.5** | l'API QUIC del ponte `ngtcp2_crypto_ossl` |
| ngtcp2 / nghttp3 | 1.25.0 / 1.18.0 | dentro il binario (`DECISIONI.md` §10.6) |
| libavcodec (ffmpeg) | **61.13.100** (ffmpeg 7.1) | `avcodec_get_supported_config` |
| libei | 1.3 | `ei_disconnect` |
| PipeWire | 0.3.48 | la cattura di GNOME e KDE |
| GNOME (mutter) | **46** (API `ConnectToEIS`, `--headless`); da 50 l'unità `@user` | `sessione.c` |
| KDE Plasma (KWin) | **6.1** (`connectToEIS`) | `kwin.c` |
| XFCE | **4.20** (Wayland) | la sessione sotto labwc |
| LXQt | **2.0** (Wayland) | la sessione sotto labwc |
| labwc / wlroots | labwc 0.8 con `-m/-C/-S`; wlroots 0.18 (screencopy, virtual pointer/keyboard, data-control, output-management) | `wlroots.c`, `sessione.c` |
| un carattere scalabile | qualunque (DejaVu, Noto, Droid…) | senza, labwc muore (labwc #2525) |
| VA-API | driver con H.264 in codifica (`iHD` Intel, `radeonsi` AMD); NVIDIA proprietaria no | la codifica sulla scheda; altrimenti il ripiego software |

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

⭐ **Un programma solo, monolitico** (`DECISIONI.md` §10.14): `remotix-install` è motore, CLI, TUI e GUI in un
eseguibile; parla con systemd, logind, firewalld e polkit dall'interno (D-Bus); lancia solo un elenco chiuso
di programmi di sistema (il gestore di pacchetti, `usermod`/`gpasswd`) col percorso completo e ogni chiamata
nel registro; la GUI gira come l'utente e rilancia lo stesso eseguibile con i permessi di polkit.

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

⭐ **L'installatore è l'unica via** (`DECISIONI.md` §10.12): il pacchetto porta i pezzi **inerti** — niente
servizio acceso, niente gruppi, niente firewall, le cinture spente in `/usr/share/remotix/`; il motore li
monta col consenso e li registra; le vie sono due sole — l'installatore o il codice sorgente a mano, a proprio rischio — e REMOTIX non ha né blocchi né opzioni per una via intermedia: `remotix stato` dice solo se l'installazione è certificata dall'installatore;
un aggiornamento del pacchetto richiama il motore. Quel che segue va letto così: lo fa **il motore**, non
gli script del pacchetto.

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

### 6.5-bis Che cosa l'installatore chiede a REMOTIX — elenco chiuso (30 set 2026)

*Preoccupazione dell'utente: «su T5 andrà fatto un ragionamento, perché rischiamo di dover introdurre
funzionalità in REMOTIX non previste». ⇒ Quel che l'installatore chiede al prodotto sta **solo** in questo
elenco; una richiesta nuova passa dall'utente prima di entrare.*

| richiesta a REMOTIX | perché | stato |
|---|---|---|
| ritrovare i desktop vivi dopo un riavvio del servizio | aggiornare senza chiudere i desktop (§5.2, T7) | decisa (T2) |
| una prova di codifica: un fotogramma in H.264, e dire se riesce | la certificazione, fase 7 (§6.0) | proposta del 30 set |
| `remotix stato`: installazione certificata o no, condizioni attive | assistenza (§10.12) | decisa |
| non scrivere più da sé il file di KDE (`kwin.c:48`) | il pacchetto possiede i suoi file | correzione |
| annotare chi iscrive ai gruppi alla prima connessione (`figlio.c:~1525`) | la disinstallazione sa chi togliere | correzione |

⛔ **Non** stanno in REMOTIX, e li fa il motore: gruppi, cinture, firewall, desktop, archivi, pacchetti, e alla
**disinstallazione** la chiusura dei desktop aperti — il motore li trova da logind (sessioni col servizio PAM
`remotix`) e li fa chiudere da logind (vedi sotto).

**La disinstallazione** (parola dell'utente, 30 set: *«è un'operazione dell'admin del server: l'admin avverte
gli utenti nelle modalità classiche (email, WhatsApp…); poi, quando avvia la disinstallazione, l'installer
chiude le sessioni REMOTIX degli utenti e i loro processi e avvia la pulizia del sistema»*):
1. **prima**, l'amministratore avvisa le persone coi suoi mezzi — REMOTIX non ha né avrà un sistema di messaggi
   per questo;
2. **nessuna domanda in più**: se ci sono ancora persone collegate, le loro sessioni REMOTIX si chiudono e basta
   — erano state avvisate (parola dell'utente, 30 set). Il piano di disinstallazione, che si conferma una volta
   sola come ogni piano, ne porta solo la riga «chiudo le sessioni REMOTIX ancora aperte (N)»;
3. il motore chiude **le sessioni REMOTIX** e tutti i programmi nati dentro di esse (logind `TerminateSession`
   sulla sessione, che porta via il suo gruppo di processi) — ⚠ **non** tutti i processi dell'utente: la stessa
   persona può avere una sessione davanti al monitor o un lavoro via ssh, e quelli non si toccano;
4. poi la **pulizia** del sistema, ripercorrendo il registro (§6.6.4).

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
| `C-DESKTOP` | il desktop non c'è (o non è supportato) e l'installatore lo aggiunge dagli archivi della distribuzione | Ubuntu Server, un'immagine cloud, una macchina con solo Cinnamon |

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
- `[M]` 29 set: **le 27 macchine sono pronte** con la foto «cliente» (tutte rc=0); ubuntu2404-gnome resta per confronto, fuori dalla matrice (D7).
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
- **giro intero**, prima di dichiarare pronta una versione: tutte le 26 — circa 2 ore, tre alla volta,
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
| R38 | una macchina senza desktop | VM «nuda» (senza desktop): risposta «sì» ⇒ desktop installato, `graphical.target` e schermata d'accesso NON attivati, desktop nel browser; risposta «no» ⇒ BLOCCATA con `RX-DESKTOP-001` e impronte invariate | un desktop che parte davanti al monitor; una macchina toccata dopo un «no» |
| R39 | l'aggiornamento automatico passa dal gestore di pacchetti e non chiude i desktop | versione N+1 di manutenzione pubblicata nell'archivio di prova; il timer di REMOTIX la trova e (secondo D14) la applica con due utenti collegati; poi un catalogo nuovo che aggiunge una versione di distribuzione | un file di REMOTIX cambiato fuori dal gestore di pacchetti; una finestra persa; il catalogo nuovo non letto |
| R40 | ⭐ il pacchetto da solo non accende niente | `apt install`/`dnf install`/`pacman -U` del solo pacchetto su una VM «cliente»: impronte prima e dopo, porte in ascolto, gruppi; poi `remotix stato` | il servizio acceso o in ascolto; un gruppo, una regola del firewall o una cintura attivati; `remotix stato` che non dica «installazione non certificata» |
| R41 | un programma solo | durante un'installazione completa, l'albero dei processi figli del motore (`/proc`) | un processo che non sia il motore stesso o un programma dell'elenco chiuso; uno script eseguito; una chiamata a un programma non annotata nel registro |
| R42 | la lingua segue il sistema | la stessa installazione con `LANG=it_IT.UTF-8`, `LANG=en_US.UTF-8`, `LANG=de_DE.UTF-8` e `LANGUAGE=it:en`, in GUI (che si rilancia con polkit) e in TUI | una schermata o un messaggio nella lingua sbagliata; un codice `RX-…` diverso fra le lingue |
| R43 | la disinstallazione chiude solo le sessioni REMOTIX | un utente con un desktop REMOTIX aperto e, insieme, una sessione ssh con un processo che scrive l'ora ogni secondo; disinstallazione | il desktop REMOTIX ancora vivo; il processo della sessione ssh interrotto |

---

## 9. Le tappe

| tappa | che cosa | produce | stato |
|---|---|---|---|
| **T0** | il banco delle VM e le 27 macchine «cliente» | `banchi/17-distro/17-vm.sh`, foto `cliente` e `iso` | ✅ 29 set: 27 «cliente» + 6 «iso» (differenze in `banchi/17-distro/iso-differenze.md`); 4 VM insieme |
| **T1** | REMOTIX **compila e gira** su ogni distribuzione, installato a mano: le cure di §4.4 e §5.1 | il prodotto portabile; R27 verde, a mano | ✅ 30 set: compila 7/7; gira 7 famiglie su 7 col binario del prodotto, con le condizioni di §11.1 |
| **T2** | la **misura** di §5.2: che cosa uccide i desktop quando si ferma il servizio | la causa, e la stima vera | ✅ 29 set: nessun desktop muore; cura leggera (§5.2) |
| **T3** | le tre **ricette** dei pacchetti e i contenitori di costruzione per famiglia | `.deb`, `.rpm`, `.pkg.tar.zst`; R4, R13, R14, R23 | |
| **T4** | gli oggetti e gli stati di §6.6 (formato, registro, codici), poi il motore con la CLI, fasi 0-4: TRUST, PREFLIGHT, COMPATIBILITY, PLANNING, CONSENT & SAFETY (`remotix verifica`, `install.sh`) | R1, R2, R3, R25 | 🔸 30 set, linea A, prima parte (aec8402): il motore con gli oggetti, gli stati, il registro e la ripresa, 4 azioni vere, PREFLIGHT, catalogo, CLI; R1 verde in 4 contenitori, R30 in piccolo verde (§13.1) |
| **T5** | il motore, fasi 5-8: il registro delle azioni, la certificazione, COMMIT / ROLLBACK; la disinstallazione | R5, R6, R26, R28, R29 | |
| **T6** | PAM per famiglia, SELinux, firewall | R19, R20 | |
| **T7** | l'aggiornamento senza chiudere i desktop (secondo T2 e D1) | R7-R12 | |
| **T8** | depositi firmati, canali, ritorno indietro, SBOM; l'aggiornamento automatico (timer, catalogo, D14) | R11, R17, R18, R24 | |
| **T9** | la **TUI** e la **GUI** sul motore finito (R36, R37); senza domande e senza rete; la codifica sulla scheda vera per famiglia (scatole) | R21, R22 | |
| **T10** | il giro intero sulle 26 macchine della matrice, e la chiusura | tutti verdi | |

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
| **D2** | ✅ **CHIUSA il 29 set**: sì, ngtcp2 e nghttp3 dentro — dalla regola generale dell'utente (`DECISIONI.md` §10.6): *quel che manca o è troppo vecchio lo porta REMOTIX*, salvo i codec brevettati (archivio esterno col consenso) e i desktop (fuori matrice) | — | — |
| **D3** | La **politica contro i tentativi**: che cosa si vuole — quanti errori, per conto e per indirizzo, blocco o rallentamento, vale anche davanti alla macchina o solo da remoto, chi sblocca e come, che cosa si registra. Da lì si decide se la pila di REMOTIX tiene il `pam_faillock` della distribuzione | T6, con una proposta scritta di minacce e difese | da remoto un blocco per conto permette a chiunque di chiudere fuori il proprietario; proposta: rallentamento per conto + ban per indirizzo in REMOTIX, niente blocco del conto, tutto nel registro |
| **D4** | Le tre cinture (la macchina non si spegne, non si sospende, i tasti non spengono) sulle macchine **degli altri**: sempre, o scelta dell'amministratore all'installazione? | T3 | predefinite, dichiarate nel benvenuto, disattivabili |
| **D5** | RPM Fusion (Fedora) e Packman (openSUSE): l'installatore li **aggiunge chiedendo il consenso**, o si limita a **dire** il comando? | T4 | chiede il consenso, mai in silenzio; senza consenso REMOTIX si installa e il benvenuto dice che la codifica sulla scheda manca |
| **D6** | Il firewall: l'installatore **apre** la porta 7447, o la definisce e dice il comando? | T4 | la apre chiedendo, come D5 |
| **D7** | ✅ **CHIUSA il 29 set: Ubuntu 24.04 fuori**, si parte dalla 26.04 (parola dell'utente: *«partiamo dalla 26.04»*) | — | — |
| **D8** | Su Ubuntu, chi si collega vede il GNOME **di Ubuntu** (dock, colori) o quello **vanilla** di Debian? | T1 | quello di Ubuntu: è quello che l'utente ha davanti al monitor |
| **D9** | Le distribuzioni **immutabili** (Silverblue, Aeon, Kinoite, Kalpa): dentro questa fase o dopo? | fine fase | dopo; da guardare allora `systemd-sysext` e i portable services (`DECISIONI.md` §10.11) |
| **D10** | Dove si costruiscono e si ospitano i pacchetti: contenitori nostri e un deposito nostro, o **OBS** di openSUSE (che costruisce per tutte le famiglie, ma vuole progetti pubblici)? | T3 | contenitori nostri finché il codice è privato — ⭐ REMOTIX sarà open source (`DECISIONI.md` §10.13): OBS diventa possibile |
| **D11** | La **custodia della chiave madre** (dove sta, chi la tiene, copia di riserva) e la cadenza della rotazione | T8 | fuori linea, due copie in due posti, sottochiavi annuali |
| **D12** | Con che cosa si fanno **TUI e GUI** (requisito irrinunciabile): per la GUI GTK 4 o Qt 6 (una sola, che si vede bene su tutti e quattro i desktop), per la TUI una libreria a schermo intero | T4, prima di scrivere le interfacce | GUI in **Qt 6** (è di casa su KDE e LXQt, e si integra bene su GNOME e XFCE); TUI con **newt** (è la libreria degli installatori di Debian e Fedora, già presente quasi ovunque) ⚠ Con §10.14 (un eseguibile solo) la GUI va scritta in un toolkit che si possa usare dal Go dello stesso eseguibile, o la scelta cambia forma: da decidere guardando i legami Go di Qt 6 e GTK 4 |
| **D13** | **La parte grafica**: le schermate e il percorso (una per fase del motore: controllo, compatibilità, piano da approvare, avanzamento, certificato), l'aspetto (colori, logo ufficiale, caratteri, tema chiaro e scuro, i quattro desktop), il tono e le lingue dei testi | **prima di T9**, su un **prototipo cliccabile** coi dati veri di una VM (per esempio Fedora senza RPM Fusion, per vedere un «a condizioni») — si decide guardando, poi si scrive la GUI vera | il prototipo si può fare presto, in parallelo: dipende solo dagli oggetti di §6.6.1, non dal codice del motore ⭐ Le lingue sono decise: italiano e inglese, secondo la lingua del sistema (`DECISIONI.md` §10.15). Il prototipo: https://claude.ai/artifact/8ehEBPwyEst2JqY5JrpEEV |
| **D14** | L'**aggiornamento automatico** (`DECISIONI.md` §10.10): che cosa si applica da solo — sicurezza e ricostruzioni automatiche e la versione annuale su scelta dell'amministratore, oppure solo avviso | T8 | sicurezza e ricostruzioni automatiche; la versione annuale su scelta |

**Le scelte di chi installa: quasi nessuna** (indicazione dell'utente, 29 set: *«non riesco ad immaginare
grandi scelte da parte dell'utente sull'installazione di REMOTIX, se non solamente la porta»*):
- **la porta** (predefinita 7447): una sola domanda, che vale per **TCP** (la pagina) **e UDP** (QUIC);
- due **consensi**, non preferenze, e **solo dove servono**: l'archivio esterno per H.264 (solo Fedora
  e openSUSE, D5) e l'apertura del firewall (solo se è acceso, D6);
- ⛔ tutto il resto ha un valore predefinito e **non si chiede**: chi entra (gli utenti della macchina,
  root escluso), il certificato (generato), le tre cinture (attive, dette nel benvenuto, D4), i gruppi
  della scheda. Chi vuole altro lo cambia dopo in `/etc/remotix/remotix.conf.d/`.

**Se sulla macchina non c'è un desktop** (proposta dell'utente, 29 set 2026: *«se REMOTIX non trova nessun
desktop installato, o chiede di installarlo all'utente oppure REMOTIX non si installa»*):
- PREFLIGHT lo rileva; nella schermata delle scelte compare **una domanda in più, solo in quel caso**:
  «su questa macchina non c'è un desktop: vuoi installarne uno?», con i soli desktop che il catalogo dà per
  buoni su quella distribuzione (Alma: GNOME e KDE), fra cui **chi installa sceglie quale** (parola dell'utente); uno è **già selezionato**, quello di riferimento della distribuzione — GNOME su Debian, Ubuntu, Fedora, Alma; KDE su openSUSE e Arch — ed è anche quello che si installa senza domande se il file di risposte non dice altro. **Sì** ⇒ l'installazione del desktop entra nel piano
  come azione dichiarata, col suo peso (pacchetti, GB); **no** ⇒ REMOTIX non si installa (BLOCCATA,
  `RX-DESKTOP-001`, col perché e il rimedio);
- lo stesso se c'è **solo un desktop non supportato** (Cinnamon, MATE, i3…): quello esistente non si tocca, il
  nuovo si aggiunge accanto;
- il desktop viene **dagli archivi della distribuzione** (il confine di `DECISIONI.md` §10.6 resta: REMOTIX
  non se lo porta dietro), e si installa **senza cambiare come parte la macchina**: niente schermata di
  accesso locale né avvio in grafica — i desktop di REMOTIX nascono senza schermo, e un server resta un
  server davanti al monitor;
- è un'azione **AL_MEGLIO** (§6.6.4): toglierla non rende la macchina identica, e il piano lo dice prima del
  consenso.

**Il linguaggio delle schermate** (indicazione dell'utente sul prototipo, 30 set: *«il riepilogo a volte usa
termini quasi da programmatore»*): chi installa legge **che cosa succede e che cosa deve decidere**, in parole
comuni («Accesso», «Protezione del sistema», «Serve il tuo consenso», «Lo sistemo io»); driver, percorsi,
nomi di pacchetti, codici `RX-…` e impronte stanno in un «Mostra i dettagli tecnici» chiuso di serie — è lì
che li cerca l'assistenza. Si scrive **«password»**, non «parola d'ordine»: è il termine che conoscono tutti (parola dell'utente, 30 set).

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
  - **(D)** tela nera su Tumbleweed (KWin) e Leap (labwc) — la verifica a smentire ha trovato **due cause
    diverse**, nessuna delle due quella scritta: il `CREATE_DUMB: Permission denied` è di Mesa sul nodo
    `renderD128` (il nucleo lo rifiuta a tutti, root compreso) ed esce identico su Arch, dove va.
    - **Tumbleweed: manca lo sfondo.** L'immagine *Minimal-VM* ha `solver.onlyRequires = true` ⇒ il gruppo
      KDE non porta `breeze6-wallpapers`, plasmashell non trova lo sfondo «Next» e non mostra né desktop né
      pannello (nero anche nella foto di KWin stesso). Con il pacchetto, il desktop arriva. ⇒ è della
      **piattaforma installata senza raccomandati** (un'altra ragione per lo stato ISO, §7.2);
      l'installatore su openSUSE porta `breeze6-wallpapers` (`C-COMPONENTE`);
    - **Leap 16: labwc non riesce a creare il buffer sulla scheda virtuale** (`gbm_bo_create failed`), anche
      lanciato a mano senza REMOTIX. Con `WLR_RENDERER=pixman` il desktop XFCE arriva. ⇒ limite di una
      macchina **senza 3D**, come (A). ✅ **Curato** (§13.1, `scheda_sa_disegnare()`): REMOTIX prova il
      buffer prima di dare il nodo a labwc e, se non nasce, avvia labwc con `WLR_RENDERER=pixman`
      dichiarato. `[M]` 29 set: su Leap 16 XFCE il desktop arriva, **anche col binario del prodotto**
      (labwc si cattura da `wlroots.c`, non da PipeWire: (A) qui non pesa); sull'Intel del server e del
      portatile la prova dice «sì» e la strada resta la scheda.
      - ⛔ **«rifiuta la misura» è smentito**: l'uscita passa a 1872×944 in 3 ms (riletta). Resta
        1280×720 **solo lo sfondo di xfdesktop**, anche minuti dopo: xfdesktop nasce ~150 ms **prima**
        della richiesta di misura e non ridisegna — è la stessa gara curata per LXQt (fase 14, incr. 3,
        `primario_lxqt()`), non pixman. La cura XFCE non è nello stesso punto: tocca la riga di avvio
        (`SESSIONE_RIGA_XFCE`), cioè la cintura del logout (`XFCE4_SESSION_COMPOSITOR`); e su Leap
        `wlr-randr`, che la cura di LXQt usa, **non è installato** (⇒ dipendenza per T3).
- **Chiusura di T1** (binario del prodotto con le due cure, 9e035c5): **scatole 208 PASS / 0 FAIL / 0 BLOCKED**,
  copia zero intatta su GNOME e KDE (14/14 palchi sulla scheda), la scheda Intel dice «sì» a labwc (zero
  ripieghi pixman); **VM: desktop nel browser su debian13-gnome, ubuntu2604-kde, fedora44-gnome, alma10-kde,
  arch-xfce, tumbleweed-kde** (con le condizioni: RPM Fusion e PAM senza `pam_selinux` su Fedora/Alma, 0
  rifiuti SELinux in enforcing; Packman e `breeze6-wallpapers` su Tumbleweed; su Arch il gruppo xfce4 non
  porta ffmpeg: dipendenza per T3). Su Alma RPM Fusion va **dopo** EPEL, o `libavcodec-free` va in conflitto.
  - **leap16-lxqt: mancano i caratteri.** `[M]` 29 set sera: la VM ha **solo caratteri bitmap** (PCF,
    `xorg-x11-fonts-core`; `fc-match sans` = «Misc Fixed»). Pango 1.56 non li sa misurare: l'altezza del
    titolo esce **1 398 724 px**, `create_corners()` chiede a cairo una superficie 9×1 398 724, cairo
    rifiuta (`_cairo_surface_nil_invalid_size`) e l'`assert` di `buffer_adopt_cairo_surface` (buffer.c:90)
    abbatte labwc (gdb con i simboli: `main` → `theme_init` → `create_corners` → `rounded_rect` →
    `buffer_create_cairo`). Non è pixman né LXQt: labwc nudo, senza configurazione, muore uguale. Il
    carattere lo porterebbe il pattern `lxqt` (`google-droid-fonts`, **raccomandato**), perso con
    `solver.onlyRequires` dell'immagine Minimal-VM — la stessa trappola dello sfondo di Tumbleweed; il
    pattern `xfce` porta i caratteri per altra via, e XFCE passava. È il difetto noto labwc#2525 (chiuso
    dall'autore «mancava un carattere», **nessuna cura**: nel ramo principale del 26 set 2026 l'`assert`
    c'è ancora). Con `google-droid-fonts` (+ Packman per libx265, (C)): **PASS** col binario del prodotto,
    0 SIGABRT, labwc in pixman dichiarato, desktop a 0,6 s. ⇒ **T3**: l'installatore esige un carattere
    scalabile (su openSUSE `google-droid-fonts`, `C-COMPONENTE`); REMOTIX da solo non lo può evitare —
    senza un carattere vettoriale non c'è niente da indicare a labwc. `[?]` proposta, non fatta: una
    riga «⛔ nessun carattere scalabile: labwc morirà» prima dell'avvio (fontconfig, `FC_OUTLINE`).
  - **Il primo fotogramma wlroots «NERO» nelle scatole non è nuovo e non è un guasto.** `[M]` c'era già
    in fase 16 (27 set, binario 45d048c8, `/media/REMOTIX/misure/fase16/intel-*/livello-*/server.log`):
    XFCE 107 palchi su 367, LXQt 150 su 278, e uguale sulla Radeon; 0 su GNOME/KDE (passano da PipeWire).
    Nella chiusura di T1: XFCE 12 su 14, LXQt 3 su 14 (le «24 righe» sono ognuna doppia, journal +
    registro della sessione). È il primo fotogramma preso alla nascita di labwc, prima che sfondo e
    pannello siano dipinti; le due cure non toccano la strada wlroots sull'Intel (0 ripieghi). Proposta
    non fatta: guardare il primo fotogramma dopo ~1 s, perché la riga segnali solo un nero che dura.
- **Stato ISO** (T0): 6 macchine su 6; le differenze che contano per l'installatore: `render` non c'è mai;
  Fedora Workstation apre 1025-65535, **Alma e Tumbleweed hanno la 7447 chiusa**; Tumbleweed con accesso
  automatico, btrfs e snapper (fotografie di sistema già pronte, §6.6.4), raccomandati installati; Ubuntu
  desktop minimo + snap, ufw spento; rete con NetworkManager ovunque.
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
| 192d482 | `sessione.c` `scheda_sa_disegnare()`: prima di dare il nodo a labwc (XFCE, LXQt) si crea un buffer di prova con `gbm` — XRGB8888 256×256, usi `SCANOUT\|RENDERING` e poi solo `RENDERING`, gli stessi con cui ripiega l'allocatore di wlroots. Se nessuno dei due nasce: `WLR_RENDERER=pixman`, niente `WLR_RENDER_DRM_DEVICE`, e una riga «RIPIEGO DICHIARATO» col motivo; se nasce, tutto come prima | macchina senza 3D (VM `virtio_gpu`, §11.1 D): il nodo si apre ma labwc non crea il buffer (`gbm_bo_create failed`) ⇒ tela nera. Criterio generico (si chiede alla macchina), nessuna eccezione per distribuzione o desktop | `[M]` 29 set: compila Leap 16 e Debian 13, zero avvisi. Sonda da sola (`gbm`): Intel del portatile e del server (i915) ⇒ «sì» con tutt'e due gli usi; VM Leap 16 ⇒ «no», `Permission denied`. Leap 16 XFCE installata a mano (T1c, + Packman per libx264/x265, solo diagnosi), Chrome vero: **PASS** col binario di diagnosi e **PASS col binario del prodotto**, senza impostazioni a mano; labwc con `WLR_RENDERER=pixman` nel suo ambiente. ⚠ Lo sfondo di xfdesktop resta 1280×720 (gara di nascita, §11.1 D) | no |
| 6bede6a | `cattura.c`/`cattura.h`/`figlio.c`: il **ripiego sulla memoria dopo il rifiuto della scheda**. `cattura_formato_rifiutato()` = flusso in errore **e** nessun formato mai concordato (due fatti, non il testo di PipeWire); `cattura_avvia()` lo dice con `G_IO_ERROR_NOT_SUPPORTED` se arriva prima che torni. In `prendi_il_palco()` `ripiega_se_rifiutata()` passa la strada alla MEMORIA, scrive «la strada della SCHEDA e' stata RIFIUTATA … RIPIEGO DICHIARATO», segna `scheda_mai_piu` e riapre la sola cattura sullo stesso palco. `cattura_prendi()` esce subito da un flusso in errore invece di aspettare 5 s. Niente offerta doppia (la memoria accanto alla scheda lascerebbe scegliere il compositore) e niente ripiego sul silenzio (un compositore lento su scheda vera darebbe lo stesso silenzio); nessuna eccezione per compositore | T1c: senza 3D (VM `virtio-vga` senza virgl, server senza scheda) il compositore non ha DMA-BUF, la negoziazione muore con «no more input formats» e il ripiego di `scheda_da_abbandonare` vive dentro un fotogramma che non arriva ⇒ «Ammesso» e desktop mai; il figlio rimontava sulla scheda ogni 5 s per sempre | `[M]` 29 set, binari di `costruisci-tutti.sh`, Chrome vero: **VM** debian13-gnome PASS (desktop a 4,5 s; prima del ripiego rapido 10 s), arch-kde PASS, ubuntu2604-gnome PASS (col binario vecchio 0 su 3); il rifiuto e il ripiego stanno a **7 ms** dalla cattura avviata. **Scatole Intel** (binario debian13 `3e026237`, PAM nuovo + `utenti-negati`), giro `17-cura-copia-zero` f001 f003 f004 f011 f016 f018 f018b × 4 desktop × Chrome e Firefox: **208 PASS / 0 FAIL / 0 BLOCKED** (25 min); nel registro 14 palchi per desktop tutti «SCHEDA (DMA-BUF, copia zero)», 0 «MEMORIA», 0 «RIFIUTATA»; GNOME e KDE 14/14 «i fotogrammi arrivano come DMA-BUF», XFCE e LXQt 28 «PRIMO fotogramma della SCHEDA» e 0 ripieghi wlroots | no (scatole tornate a `4fb3287d` e al PAM di prima) |
| — | ⚠ **non fatto, annotato**: `figlio.c:4684` apre sempre `renderD128` per il codificatore: con due schede può prendere quella sbagliata; va scelto dal driver (§4.4). Fuori dalla T1a per mandato | — | — | — |
| c95146c | **T3, linea B — il pacchetto `.deb`** (`packaging/debian/`, debhelper 13, `dh_installsystemd`): `/usr/libexec/remotix/remotix`, `/usr/share/remotix/{pagina.html,remotix.conf}`, `/etc/remotix/remotix.conf.d/` vuota; **conffile** `/etc/pam.d/remotix` (il PAM di Debian, `src/remotix.pam`) e `/etc/remotix/utenti-negati` (root); `remotix.service` da root (`KillMode=mixed`, `Restart=on-failure`, `--nome %H`, `--journal`, nessuna opzione di banco; certificato generato dal programma al primo avvio, `certificati.c:302`); il permesso di KWin `/usr/share/applications/org.kde.remotix.desktop` **identico byte per byte** a quello che scrive `kwin.c:606`; le tre cinture nei percorsi del **fornitore** (`/usr/share/polkit-1/rules.d/50-…`, `/usr/lib/systemd/{logind,sleep}.conf.d/`) — ⚠ **dipendono da D4, aperta**; `tmpfiles.d` (`/var/lib/remotix` 0700, `/run/remotix`); postinst: le persone (UID_MIN..UID_MAX, shell vera) nei gruppi LETTI dai nodi `/dev/dri`, ogni coppia annotata in `/var/lib/remotix/modifiche.log` come DIRETTA o PREESISTENTE, una coppia già annotata non si riscrive (R5); postrm purge: via **solo** le DIRETTE, poi `/var/lib/remotix`. **Dipendenze**: `dpkg-shlibdeps` + `libpam-systemd libpam-modules passwd systemd dbus-user-session` (usate a tempo di esecuzione, dpkg non le vede); **Recommends** `va-driver-all \| va-driver, labwc, wlr-randr, xwayland` e, solo su Ubuntu, `gnome-session \| plasma-workspace \| xfce4-session \| lxqt-session` (D8 aperta: la sessione vanilla solo se non c'è già un altro desktop). `Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0)` (D2 chiusa). `src/costruzione/costruisci-deb.sh`: copia dell'albero, `debian/changelog` con versione e data del commit (⇒ `SOURCE_DATE_EPOCH`), `dpkg-buildpackage -b` nel contenitore, lintian, controlli R4/R13/R14/R23 sul pacchetto FINITO; `Contenitore.debian13`/`.ubuntu2604` con uno strato di attrezzi `.deb` in coda | T3 (§6.1-§6.4): la ricetta nativa, dipendenze calcolate e non scritte a mano (`LEZIONI.md` §2.5-bis) | `[M]` 29 set, 313ccfc: **compila** Debian 13 e Ubuntu 26.04; **lintian 0 E / 0 W**, 1 informazione (`systemd-service-file-missing-documentation-key`), 3 sostituzioni motivate (`pagina.html` non è documentazione; `systemctl reload systemd-logind`, che `deb-systemd-invoke` non sa fare); **R13** 0 frasi della funzione di banco nel binario estratto dal `.deb`, 1 nel controllo positivo (`rcp.o` con `BANCO_ACCESO 1`), nessuna opzione di banco nell'unità; **R14** nessun file del banco; **R4** `ldd` 108 (Debian) e 111 (Ubuntu) librerie, 0 mancanti, ngtcp2/nghttp3 non dinamiche; **R23** due costruzioni in due copie pulite ⇒ `.deb` **identici** byte per byte (Debian `a907d059…`, Ubuntu `966fcd73…`). Prove in VM: vedi §13.2 | sì, nelle VM di prova (poi tolto) |
| — | ⚠ **non fatto, annotato dalla T3** (tocca il C, fuori mandato): (1) `kwin.c:606` `kwin_scrivi_permesso()` deve smettere di **scrivere** `/usr/share/applications/org.kde.remotix.desktop` (è del pacchetto) e solo verificarlo — oggi non lo riscrive perché lo trova uguale; (2) `figlio.c:1525` `iscrivi_ai_gruppi_della_scheda()` iscrive alla prima connessione chi è nato dopo l'installazione ma **non lo annota** in `/var/lib/remotix/modifiche.log`: il purge non lo toglie; (3) con `--journal` sotto systemd **ogni riga compare due volte** nel journal (una da stderr, una strutturata): il programma dovrebbe tacere su stderr quando `JOURNAL_STREAM` è il suo stderr; (4) il certificato di §6.6.13 (`0-generato.pem`, `/etc/remotix/certificati.d/`) non c'è: il pacchetto si appoggia a quello di oggi (`pagina.pem`/`sessione.pem`, marca `.nostro`); (5) `/usr/bin/remotix` (verifica, stato…) e la configurazione vera sono di T4: oggi `remotix.conf` è un `EnvironmentFile` provvisorio | — | — | — |
| a3b722a…a6d0908 | **T3, linea D — il pacchetto Arch** (`packaging/arch/`): `PKGBUILD` che costruisce dal **tarball del commit** (`costruisci.sh`: `git archive` di `src/`, `banchi/rcp/`, `packaging/arch/`, poi `makepkg` nel contenitore `arch` come utente, namcap in un contenitore usa-e-getta, lista nera R14, `SOURCE_DATE_EPOCH` = data del commit); ngtcp2 1.25.0 e nghttp3 1.18.0 **statiche** dai tarball ufficiali con sha256 fissata, costruite in `build()` (D2 chiusa; ⓘ per §10.6 su Arch si potrebbe usare `libngtcp2`/`libnghttp3` di sistema, già 1.25 col ponte crypto_ossl: resta dentro per uniformità); `-ffile-prefix-map` (i `__FILE__` delle assert di ngtcp2 portavano `$srcdir` nel binario); `!lto !debug`. **Percorsi di Arch**: il binario in `/usr/lib/remotix/remotix` (Arch non usa libexec: namcap «ELF outside of a valid path»), `pagina.html` in `/usr/share/remotix/`, unità `remotix.service` (da root, `KillMode=mixed`, `LimitRTPRIO=20`, `LimitNICE=-11`, `Restart=on-failure`, `REMOTIX_PORTA=7447` e `REMOTIX_NOME=%H` cambiabili con un drop-in, nessuna opzione di banco), `tmpfiles.d` (`/var/lib/remotix` 0700), PAM `src/remotix.pam.arch` in `/etc/pam.d/remotix` e `/etc/remotix/utenti-negati` (root) in `backup=()` (**D3 aperta**: il `pam_faillock` arriva con `system-auth` di pambase, non aggiunto né tolto), il permesso di KWin `/usr/share/applications/org.kde.remotix.desktop` **identico byte per byte** a quello di `kwin_scrivi_permesso()` con `Exec=/usr/lib/remotix/remotix`, il servizio firewalld **definito** (`/usr/lib/firewalld/services/remotix.xml`, nessuna zona toccata); ⛔ **§10.12**: le tre cinture **spente** in `/usr/share/remotix/cinture/` (le monta il motore, D4), `remotix.install` **non** iscrive ai gruppi e non accende niente (post_install: solo un avviso; post_upgrade: `try-restart`, il posto dove richiamare il motore; pre_remove: `disable --now`; post_remove: via certificati e ban). **Dipendenze**: per **soname** (`libavcodec.so=63-64`, `libssl.so=3-64`, … calcolati da makepkg sul binario) + i pacchetti; più `labwc wlr-randr` (XFCE/LXQt, nessun gruppo di Arch li porta; labwc tira `ttf-font`, il carattere di labwc #2525) e `pipewire wireplumber pipewire-pulse` (il gruppo xfce4 non ha l'audio). ⭐ **Rolling release**: legame al **soname**, non alla versione esatta: ffmpeg si aggiorna libero finché l'ABI resta, e a un cambio di soname `pacman -Syu` **rifiuta** («breaks dependency») finché non si ricostruisce — la versione esatta bloccherebbe ogni aggiornamento di ffmpeg, sicurezza compresa, e con lui tutto il `-Syu`. A carico nostro: ricostruire a ogni soname nuovo. `Contenitore.arch`: + `labwc wlr-randr wireplumber pipewire-pulse` (makepkg vuole vedere installate anche le dipendenze di esecuzione) | T3 (§6.1-§6.4), §10.6, §10.12 | `[M]` 29 set, a6d0908: **compila** pulito (0 avvisi di REMOTIX), `make dipendenze` verde; `check()`: `BANCO_ACCESO 0`, ldd senza ngtcp2/nghttp3 né mancanti. **namcap**: 1 E — licenza `LicenseRef-REMOTIX` senza file in `/usr/share/licenses/remotix/` (manca una licenza del prodotto: da decidere); W — `libgcc` implicita (normale), «forse non servono» `systemd labwc wlr-randr pipewire wireplumber pipewire-pulse` (non collegate: servono a esecuzione, voluto); PKGBUILD pulito. **R14** 30 voci, nessuna della lista nera. **R23** due costruzioni ⇒ pacchetto **identico** byte per byte (`51d6ea2f…`); senza `SOURCE_DATE_EPOCH` stesso binario, pacchetto diverso solo per `builddate`. ⚠ R13 solo per `BANCO_ACCESO 0` nel sorgente: la ricerca delle frasi nel binario estratto (come la linea B) non è fatta. Prove in VM: §13.2 | sì, nelle VM di prova (poi tolto) |
| — | ⚠ **non fatto, annotato dalla linea D** (tocca il C): (1) come la linea B, `kwin_scrivi_permesso()` deve solo verificare (su Arch `[M]` il programma trova il file del pacchetto uguale e scrive «c'e' gia'»); (2) **R40 rosso a metà**: il pacchetto da solo non accende niente, ma `systemctl start remotix` a mano **parte** — manca il controllo `RX-INST-001` (§10.12 punto 3); (3) il prodotto a esecuzione scrive fuori dal pacchetto e dopo `-Rns` resta: `~/.local/state/remotix/sessione.log` (DIRETTA) e su XFCE le impostazioni di energia dell'utente (`xfce4-power-manager.xml`, scritta da `sessione.c`: DIRETTA ma voluta persistente da §8.2) — il motore deve dire che cosa ne fa | — | — | — |
| aec8402 | **T4, linea A, prima parte — il motore `remotix-install`** (`installatore/`, Go statico, `CGO_ENABLED=0`, 4 MB; unica dipendenza `godbus/dbus` v5.1.0 in `vendor/`, costruzione senza rete). **Oggetti** `remotix-install/1` (profilo, rapporto di compatibilità, piano, insieme risolto — vuoto, senza pacchetti —, registro, rapporto di verifica, certificato JSON + testo) ed **eventi JSON a riga** (`--eventi`, il canale di TUI e GUI). **Stati** di §6.6.2 con le sole transizioni del disegno (`stati.go`), stato in `<operazioni>/<id>/stato` scritto atomico, serratura `flock`. **Registro** `registro.jsonl`: INTENZIONE (con lo stato di prima e l'origine) → effetto → FATTA/FALLITA, fsync del file e della cartella; la riga finale troncata si toglie e si dice (`RX-RIPRESA-003`); **ripresa** con la tabella di §6.6.3 (niente ⇒ la fa; INTENZIONE ⇒ `controlla`: completo ⇒ FATTA, assente ⇒ rifà, a metà ⇒ annulla e rifà, **estraneo** ⇒ BLOCCATA `RX-RIPRESA-001`; FATTA ⇒ controllo di coerenza). **Azioni** con fai/controlla/annulla/annullata/vincoli, reversibilità e origine: `scrivi-file` (salvataggio del file di prima nella cartella dell'operazione, temporaneo a nome fisso + rinomina, cartelle create tolte se vuote), `aggiungi-utente-a-gruppo` (`gpasswd`; PREESISTENTE anche come gruppo principale, mai tolto), `abilita-unita` (D-Bus systemd1: GetUnitFileState, EnableUnitFiles, DisableUnitFiles, Reload), `regola-firewall` (D-Bus FirewallD1, vive e permanenti, solo le regole nostre si tolgono; ufw e nftables riconosciuti e dichiarati `RX-FW-004`); **dichiarati e non fatti** (`installa-desktop`, `installa-pacchetti`, `aggiungi-deposito`, `attiva-cintura`, `accendi-servizio`): stanno nel piano, e l'operazione si ferma prima di toccare con `RX-AZIONE-004`. **PREFLIGHT** in sola lettura: os-release e famiglia, immutabili, systemd, desktop e pacchetti dall'archivio (dpkg e pacman dai loro file, **una** `rpm -q` per le famiglie RPM), depositi di terzi, schede e nodi col driver (NVIDIA proprietaria), H.264 dalla libavcodec (h264_vaapi, libx264) e dai driver VA-API, SELinux/AppArmor, porta in ascolto (`/proc/net`), firewall (firewalld sul bus, i file di ufw, nftables come unità), PAM della famiglia (e `pam_faillock`, `pam_systemd`), OpenSSL, `KillUserProcesses` (logind sul bus ⇒ VERIFICATO), gruppi `video`/`render`, caratteri scalabili; ogni fatto RILEVATO/VERIFICATO/SCONOSCIUTO, i programmi lanciati nel profilo (R41). **Impronta** vincolante (sha256 del testo canonico) + annotata; il piano la porta, `applica` la rifà e dice gli elementi cambiati (`RX-PIANO-001`). **Consenso**: approvazione legata al digest del piano (`approva`, o `--approva` a mano); senza, RIFIUTATA. **Catalogo** `catalogo/catalogo.json` (incorporato; versione, sequenza, scadenza, motore minimo, firma separata prevista): la matrice di §3 e §3.1, Ubuntu 24.04 e Mint 22 fuori (D7), derivate, escluse, condizioni `C-…` (depositi H.264, `gnome-session`, `breeze6-wallpapers`, `wlr-randr`, carattere scalabile, EPEL per KDE su Alma, `C-DESKTOP`), versioni minime dei componenti; `remotix-install catalogo --tabella` **genera** le tabelle di §3.1. **Senza desktop** (§10.7): la scelta nel piano coi desktop del catalogo e quello di riferimento già selezionato; «no» ⇒ BLOCCATA `RX-DESKTOP-001`. **`installazione.json`** accanto alle operazioni (id dell'operazione CONFERMATA, solo mestieri `installazione`/`aggiornamento`: informativo, §10.12); `remotix-install aggiornato` per gli script del pacchetto (dice se certificata, rifà la verifica, TryRestartUnit sul bus). **Bilingue** (§10.15): lingua da LANGUAGE, LC_ALL, LC_MESSAGES, LANG o `--lingua`; codici in `codici.go` + `codici_en.go`, il resto in `testi.go` | §6.0, §6.6, §8 (R1, R2, R5, R28-R32, R36), DECISIONI §10.10, §10.12, §10.14, §10.15; il motore deve girare da root prima di qualunque pacchetto: niente Python né librerie | `[M]` 30 set, `go test`: **120 PASS / 0 FAIL** — il motore **ucciso con SIGKILL** (processo figlio, niente pulizia) in 35 punti dell'applicazione (per ognuna delle 7 azioni: prima dell'intenzione, dopo l'intenzione, a file scritto a metà, a effetto fatto, dopo FATTA; e in 4 transizioni) poi `riprendi` ⇒ **CONFERMATA** con la macchina **identica** a quella di un giro senza interruzioni e nessuna azione FATTA due volte; gli stessi 35 poi `annulla` ⇒ **ANNULLATA** con la macchina identica a prima (la regola del firewall e il membro di `video` che c'erano restano); ucciso in 16 punti **durante l'annullamento** ⇒ la ripresa finisce l'annullamento; interrotta prima di toccare (6 stati) ⇒ BLOCCATA senza toccare, e un `applica` nuovo parte; riga di registro troncata; FATTA disfatta da altri ⇒ BLOCCATA, poi ANNULLATA (o ANNULLATA_IN_PARTE se il file è stato cambiato dall'amministratore, che resta suo); passo che fallisce (R28 in piccolo) ⇒ ANNULLATA; impronta cambiata (R31) ⇒ BLOCCATA senza toccare; controllo senza risposta (R32) ⇒ UNKNOWN e mai CONFERMATA; idempotenza (R5) ⇒ tutto PREESISTENTE, zero scritture. Due **mutazioni** a mano (ripresa che rifotografa la macchina invece di usare lo stato di prima del registro; gruppo sempre PREESISTENTE) ⇒ rosse subito (`TestAnnullaDopoInterruzione`, più sottoprove ciascuna): le prove hanno i denti. **R1** (`prove/r1-contenitori.sh`, impronta di `/etc` con permessi, proprietari, ore e sha256): **identica** dopo `verifica` e `verifica --json` in debian:13 (161 voci), fedora:44 (1189), archlinux (948), tumbleweed (130). **Dal vero** (`prove/systemd-giro.sh`, Fedora 44 con systemd acceso in podman): piano → approva → applica ⇒ **CONFERMATA**, unità `enabled` via D-Bus, `provamotore` in `video` via `/usr/bin/gpasswd`, i due programmi lanciati nel registro; un passo che fallisce dopo i due file e l'unità ⇒ **ANNULLATA**, unità di nuovo `not-found`, `/etc` identica nei contenuti, permessi e proprietari (non nelle ore delle cartelle). Sul portatile (Debian 13, Intel): `verifica` legge logind sul bus (VERIFICATO), la libavcodec con h264_vaapi e libx264, 7 driver VA-API. ⚠ firewalld non parte in podman senza root: la regola del firewall via D-Bus è provata solo coi finti | no |
| — | ⚠ **non fatto, annotato dalla linea A** (T4 prima parte): (1) **H.264 VERIFICATO nel PREFLIGHT**: col codice di prima (un fotogramma codificato da `ffmpeg -f null`) il portatile dava `h264.scheda = si VERIFICATO`; ffmpeg non è nell'elenco chiuso di §10.14, e il PREFLIGHT ora dice SCONOSCIUTO (la prova la farà 7a col binario di REMOTIX) — metterlo nell'elenco è una riga, **decisione dell'utente**; (2) la **firma** del catalogo e del motore (TRUST): modello pronto, schema e chiavi con D11 (T8); oggi `--senza-firma` esplicito e annotato; `sequenza` del catalogo non ancora usata contro il ritorno a un catalogo vecchio; (3) TUI, GUI (D12, D13), `install.sh`, il file di risposte, la lingua nel file di risposte; (4) i **testi del catalogo** (motivi, note, la tabella di §3.1) e i dettagli diagnostici del registro sono solo italiani; (5) BLOCCATA **dopo aver toccato** la macchina (§6.6.3, ultima riga) il motore la tiene **aperta** (se ne esce con `riprendi` o `annulla`): §6.6.2 dice «BLOCCATA: niente è stato toccato» — scelta del motore, da confermare; (6) il nome del file di stato: il motore scrive `/var/lib/remotix/installazione.json`, la linea B aveva proposto `installazione-confermata`; (7) R2 (difetti noti col codice) provato solo su radici finte, non sulle VM | — | — | — |
| 165906c | **T3, linea C — il pacchetto `.rpm`** (`packaging/rpm/remotix.spec`, UN solo spec coi rami `0%{?fedora}` / `0%{?rhel}` / `0%{?suse_version}` come `cockpit.spec`): `/usr/libexec/remotix/remotix`, `/usr/share/remotix/{pagina.html,remotix.conf}`, `remotix.service` (uguale nella sostanza a quello del `.deb`: root, `--nome %H`, `--journal`, `KillMode=mixed`, nessuna opzione di banco), `tmpfiles.d` (`/var/lib/remotix` 0700, `/run/remotix`); PAM `.fedora` in `/etc/pam.d/remotix` `%config(noreplace)`, `.suse` in **`%{_pam_vendordir}`** (`/usr/lib/pam.d`); `/etc/remotix/utenti-negati` (root) `%config(noreplace)`, `/etc/remotix/remotix.conf.d/` vuota; il permesso di KWin identico byte per byte a `kwin.c`; certificati, marche `.nostro`, `ban` e `ban.nuovo` **`%ghost`** (la disinstallazione li toglie). **§10.12**: niente `%systemd_post`/`%service_add_post` (applicherebbero il *preset*: con «enable \*» il servizio si abiliterebbe da solo), niente gruppi, cinture **spente** in `/usr/share/remotix/cinture/`, firewalld solo **definito** (`/usr/lib/firewalld/services/remotix.xml`); restano `%systemd_preun` e `%systemd_postun_with_restart` (*try-restart*). **Dipendenze**: le librerie le calcola rpmbuild (anche `libssl.so.3(OPENSSL_3.5.0)`: il minimo di OpenSSL non va scritto); a mano solo quel che rpm non vede, **condizionato al desktop** (§10.7, nessun desktop tirato dentro): Fedora `(labwc if xfce4-session)`, `(xorg-x11-server-Xwayland if xfce4-session)`, `(labwc if lxqt-session)`, `(wlr-randr if lxqt-session)`, `(default-fonts-core-sans if labwc)`, `firewalld-filesystem`, Recommends `mesa-dri-drivers`, `(libva-intel-media-driver or intel-media-driver)`; openSUSE le stesse con `xwayland`, `((google-droid-fonts or dejavu-fonts or google-noto-sans-fonts or liberation-fonts) if labwc)` (labwc #2525), `(breeze6-wallpapers if plasma6-workspace)`, Recommends `Mesa-libva`, `intel-media-driver`; Alma niente in più (EPEL/CRB e RPM Fusion sono passi del motore). `Provides: bundled(ngtcp2) = 1.25.0`, `bundled(nghttp3) = 1.18.0` (D2 chiusa), controllate in `%build` con `pkg-config`. Flag di costruzione della distribuzione nell'**ambiente** (`CFLAGS ?=` del Makefile: sulla riga di comando di make scavalcherebbero i `+=`); su openSUSE `-fPIE -pie`. **`src/remotix.pam.fedora`: `pam_selinux` close/open COMMENTATO — provvisorio, la decisione è di T6** (§11.1 B). `costruisci-rpm.sh`: archivio dall'albero, `rpmbuild -ba` e rpmlint nel contenitore del bersaglio, controlli sul pacchetto finito (R4, R13 col controllo positivo, R14, XML del servizio firewalld) | T3 (§6.1-§6.4): la ricetta nativa per Fedora, Alma, Tumbleweed, Leap; §10.12 (pezzi inerti) | `[M]` 29 set: **4 su 4 costruiti** (`remotix-0.17.0-1.fc44`, `.el10`, TW, Leap); `ldd` 0 mancanti, ngtcp2/nghttp3 non dinamiche; **R13** 0 frasi di banco nel pacchetto, 1 nel controllo positivo, nessuna opzione di banco nell'unità; **R14** nessun file del banco. **rpmlint** Fedora/Alma: 0 E veri, 4 W `invalid-license` (licenza non scelta), 2 `invalid-url` (Source0 locale), 2 `no-%check-section`, 1 `no-documentation`; 64-65 E `spelling-error` (testo italiano). TW/Leap in più: E `systemd-service-without-service_add_pre/post` (**voluti**, §10.12), E `no-binary` (debugsource), W `dir-or-file-outside-snapshot` (TW), `unstripped-binary-or-object` (debuginfo), `strange-permission` (sorgenti 664), `post-without-tmpfile-creation` (Leap: il macro lì è vuoto); prima delle correzioni anche `position-independent-executable-suggested` (curato), `macro-in-comment`, `polkit-file-unauthorized` (sparito con le cinture spente). Prove in VM: §13.2 | sì, nelle VM di prova (poi tolto) |
| — | ⚠ **non fatto, annotato dalla linea C** (tocca il C o il motore): (1) come le linee B e D, `kwin_scrivi_permesso()` (`kwin.c:48`, `:606`) deve solo **verificare** il file del pacchetto: `[M]` su TW il programma lo trova uguale («c'e' gia'») e `rpm -V` resta pulito, ma se il binario cambia percorso lo riscriverebbe; (2) il **registro della sessione** in `~/.local/state/remotix/sessione.log` resta nella casa dell'utente dopo la disinstallazione (visto su 4 VM su 4): chi lo toglie (motore alla disinstallazione, o si lascia come dato dell'utente) è da decidere; (3) le persone iscritte ai gruppi **dal prodotto** alla prima connessione (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`) vanno solo nel journal: nessun registro le vede, la disinstallazione non le toglie; (4) **firewalld**: aprire e poi richiudere il servizio lascia `/etc/firewalld/zones/public.xml` (+ `.old`) che prima non c'era (Fedora, Alma): il ritorno indietro del motore deve toglierlo se l'ha creato lui; (5) su Alma **RPM Fusion va in conflitto con EPEL** (`libavcodec-freeworld` 7.1.5 vuole `libavcodec-free` ≥ 7.1.5, EPEL ha 7.1.2): serve `--allowerasing`, che toglie `libavcodec-free` (REMOTIX resta soddisfatto dalla libreria di RPM Fusion); su Fedora `libavcodec-freeworld` **retrocede** tutta ffmpeg-free 8.1.2 → 8.0.1 (CON_FOTOGRAFIA): D5 deve dirlo nel consenso | — | — | — |

### 13.2 L'impianto di prova (banchi, VM)

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| (questo commit) | `banchi/17-distro/17-vm.sh`: una VM per `<distro>-<desktop>` dalle immagini cloud ufficiali, cloud-init, porte per macchina, `vesti` col gruppo di pacchetti ufficiale, foto «cliente», riavvio vero controllato col `boot_id` | decisione dell'utente del 29 set: le prove dell'installatore in VM, una per desktop | `[M]` 9 distribuzioni su 9 accese, ssh in 3-39 s | copiata sul server |
| 12f6782…(questo commit) | `banchi/17-distro/17-carico.sh`: la prova di carico delle VM; ritmo dai contatori dei fotogrammi su ~60 s; journal letto con sudo **dopo** lo spegnimento, VM spente una alla volta | decidere quante VM insieme (4 o 8) | `[M]` 8 VM non reggono (memoria); si resta a 4 | copiata sul server |
| (questo commit) | `banchi/17-t2/`: la misura di T2 (sessione viva con tre testimoni e sentinella a 50 ms; ferma / uccidi-padre / uccidi-figlio; catena dal journal) | §5.2 | `[M]` 10 prove su 4 desktop: nessun desktop muore | sul server, in /media/REMOTIX/tmp/t2 |
| (questo commit) | `src/costruzione/`: un `Contenitore.<bersaglio>` per debian13, ubuntu2604, ubuntu2404, fedora44, alma10 (EPEL+CRB), arch, tumbleweed, leap16 — dipendenze dal gestore di pacchetti della distribuzione, ngtcp2 1.25.0 e nghttp3 1.18.0 **statiche** (`quic-statiche.sh`, solo `.a` in `/usr/local/lib`, `LIBRARY_PATH`: il Makefile non cambia); `costruisci-tutti.sh` costruisce uno o tutti in una copia dell'albero e scrive per bersaglio binario, registri, versioni, `ldd` fatto nel contenitore. `src/Contenitore` resta com'era | §6.2 e §6.3: si compila per ogni distribuzione, niente `ld.so.conf.d` | `[M]` 29 set, sul portatile: **7 su 7 compilano**, `ldd` senza «not found» e senza ngtcp2/nghttp3. Ubuntu 24.04 si ferma a ngtcp2 (OpenSSL 3.0.13 senza QUIC); una sonda senza il ramo OpenSSL mostra poi solo `codificatore.c:1419,1436` (ffmpeg 6.1) e `ei_disconnect` assente (`input.c:1218`, libei 1.2.1) — D7. Versioni: OpenSSL 3.5.0 (Leap) … 3.6.4 (Arch); libavcodec 61 (Debian, Alma, Leap), 62 (Ubuntu, Fedora), 63 (Arch, TW); libei 1.3.901…1.6.0; PipeWire 1.4.2…1.6.9; glib 2.80…2.88. Arch e TW hanno già ngtcp2 1.25 con crypto_ossl: usabile, non usata per uniformità | no (solo portatile) |
| (questo commit) | **T1c**: `banchi/17-distro/17-t1c-installa.sh` (REMOTIX a mano in una VM, famiglia per famiglia: dipendenze, PAM, `utenti-negati`, polkit/logind/sleep, utente `prova`, unità transitoria sulla 7447), `17-t1c-browser.py` (Chrome vero con le guide di `12-client-veri.py`: apri → entra → primo fotogramma col giudice dei pixel), `17-t1c-guarda.sh` (labwc suo sull'Intel, `127.0.0.1` perché l'inoltro UDP di QEMU è solo IPv4) | far girare il prodotto portato e vederlo da un browser vero, prima dell'installatore | `[M]` 29 set, 7 VM «cliente», Full HD. **Col binario del prodotto: 0 su 7.** Tutte entrano («Ammesso»), nessuna dipinge: (1) nella VM `virtio_gpu` senza 3D la negoziazione PipeWire muore con «no more input formats» (strada della SCHEDA con modificatore obbligatorio, `cattura.c:1487`; il ripiego sulla memoria scatta solo dopo un fotogramma, `figlio.c:5362`) — Debian, Ubuntu, Arch, TW; (2) Fedora e Alma: figlio uscito con 37, AVC `{ transition } unconfined_service_t → unconfined_t` da `pam_selinux open`; (3) Fedora/Alma/openSUSE senza depositi di terzi: «libx265 non c'è in questa libavcodec: non se ne prende un altro» (Chrome chiede HEVC). **Col binario di diagnosi** (`-DCOPIA_ZERO=0`, non il prodotto): PASS Debian 13, Ubuntu 26.04 (GNOME 50, `@user` con `--headless`), Arch KDE; Fedora 44 e Alma 10 PASS solo con `pam_selinux` tolto dal PAM + `libavcodec-freeworld` (RPM Fusion); TW KDE (con Packman) e Leap XFCE BLOCKED dalla VM: KWin e labwc non allocano (`DRM_IOCTL_MODE_CREATE_DUMB: Permission denied` sul nodo virtio) ⇒ tela nera. `provisiona.sh` fuori da Debian installa `remotix.pam` (Debian) e la sua verifica dice lo stesso «⭐ a posto» | copiati sul server (`/media/REMOTIX/vm17/t1c/`) |
| (questo commit) | **Stato ISO**: `17-vm.sh da-iso <macchina>-iso` (ISO ufficiale scaricata e verificata con la sha256 del sito, kernel e initrd presi dall'ISO, risposte servite in HTTP su 10.0.2.2, disco NUOVO, UEFI con NVRAM propria, foto «iso» con la NVRAM), `impronta [foto]` (firewall, SELinux, display manager, rete, pacchetti; da una foto in sola lettura, porte k=6), `schermo` (schermata dal monitor, senza socat); risposte in `banchi/17-distro/iso-risposte/` (preseed, autoinstall, kickstart ×2, archinstall 4.4, AutoYaST); porte k=5 | §7.2: una immagine cloud con un desktop sopra non è la macchina di un cliente | `[M]` 29 set: **6 su 6 fatte** con la foto «iso» (ssh, sudo, graphical.target): Debian 10 min, Ubuntu 11, Fedora 7, Alma 7, Arch ~10, Tumbleweed 14. Contro cloud+DESKTOP (`impronta … cliente`): 7447 chiusa da firewalld su Alma e **Tumbleweed ISO** (la cloud TW non ha firewall), aperta su Fedora Workstation (1025-65535); `video` già dato dall'installatore Debian, `render` mai; rete NetworkManager su tutte le ISO (cloud Debian/Ubuntu/Arch: networkd); TW ISO con accesso automatico, snapper su btrfs, raccomandati (+1701 pacchetti) e root con la parola dell'utente; Alma ISO su LVM; Fedora ISO con `noopenh264` — tutto in `banchi/17-distro/iso-differenze.md` | copiata sul server |
| (questo commit) | **T3, linea B — la prova del `.deb` in VM**: `banchi/17-distro/17-t3-prova.sh <macchina> <deb>` (foto «cliente» → persona `prova` già in `video` → impronta → `apt-get install ./…deb` e nient'altro → Chrome vero su `127.0.0.1` con `17-t1c-guarda.sh` → impronta → `--reinstall` → impronta → `purge` → impronta → `autoremove --purge` → impronta → spenta e tornata a «cliente»; ⛔ non spegne una macchina già accesa, si ferma a 4 VM) e `17-t3-impronta.sh` (file di `/etc` con sha256, di `/usr` con dimensione e data, gruppi, conti, unità, pacchetti, manuali, logind/sleep in vigore, nft) | R4, R5, R6 in piccolo, a livello pacchetto (senza motore) | `[M]` 29 set, `.deb` 313ccfc, sul server in `/media/REMOTIX/vm17/t3/deb/esiti/`. **debian13-gnome**: installa con 10 dipendenze in più (labwc, wlr-randr e 8 librerie di wlroots; `va-driver` e `xwayland` c'erano già), 0 aggiornate; `nicfio` messo in `video`+`render`, `prova` in `render` (DIRETTE), `prova` in `video` PREESISTENTE; servizio attivo, certificato generato (`DNS:rx-debian13-gnome`); `ldd` da `prova` con ambiente vuoto: 0 mancanti; **Chrome PASS** («Ammesso, sessione nuova, desktop gnome», immagine a 4,8 s). **ubuntu2604-kde**: 8 dipendenze in più, `gnome-session` **non** portata (`plasma-workspace` soddisfa l'alternativa); stessi gruppi; **Chrome PASS** («desktop kde»); il file di KWin del pacchetto **non** riscritto dal programma. **R5**: fra «dopo il browser» e «reinstallato» nessun file cambiato di contenuto; restano le date delle cartelle rifatte da dpkg, `mimeinfo.cache` rigenerata da un innesco (stessa dimensione), CUPS e il numero di sessione (estranei). **R6**, prima → dopo `purge`+`autoremove`: **nessuna differenza DIRETTA**: gruppi identici a prima (`prova` resta in `video`: R33), `/etc/remotix`, `/etc/pam.d/remotix`, `/var/lib/remotix`, unità, cinture e i 10/8 pacchetti spariti; **INDIRETTE** (da dichiarare): `/etc/group-` e `/etc/gshadow-` (le copie di riserva di `gpasswd`, con lo stato di mezzo), date delle cartelle di `/usr`, cache di icone e mime rigenerate; **estranee**: CUPS, `fwupd.conf` 644→640 (fwupd, a macchina ferma di REMOTIX). ⚠ Dopo il purge `prova` ha ancora il **desktop vivo** (`session-cN.scope`): sopravvive al servizio (§5.2) ma non lo raggiunge più nessuno — domanda per T5 | copiati sul server (`/media/REMOTIX/vm17/t3/deb/`) |
| 5e287cb, 631ce8d, cdefd1f (questo commit) | **T3, linea B, rifatta per DECISIONI §10.12 (l'installatore è l'unica via) — il `.deb` coi pezzi INERTI e la prova R40**: `dh_installsystemd --no-enable --no-start --restart-after-upgrade` (in aggiornamento `try-restart`: riparte solo se girava); via il postinst (niente gruppi, niente `modifiche.log`); `prerm` che al solo `remove` ferma il servizio (con `--no-start` debhelper non lo fa più); `postrm purge` toglie solo certificati, ban, `/run/remotix` e `/var/lib/remotix` se vuota, **non tocca i gruppi**; le tre cinture SPENTE in `/usr/share/remotix/cinture/`; PAM e `utenti-negati` restano (inerti). L'unità rifiuta di partire senza `/var/lib/remotix/installazione-confermata` (nome **proposto** per T4-T5) con `RX-INST-001` e uscita 78 del processo principale (`sh -c 'test … ; exec remotix …'`) e `RestartPreventExitStatus=78` — ⚠ il controllo vero va nel programma (punto 3 di §10.12). `17-t3-prova.sh`: R40 dopo `apt install` (abilitata? attiva? porta 7447? gruppi? cinture in vigore?), `systemctl start` senza installatore, poi **i passi del motore fatti a mano e dichiarati** (`prova` nei gruppi dei nodi, cinture copiate in `/etc/{polkit-1/rules.d,systemd/logind.conf.d,systemd/sleep.conf.d}`, marca, `enable --now`), browser, reinstallazione, passi disfatti a mano, `purge`, `autoremove`; porte in ascolto nell'impronta | DECISIONI §10.12, R40 | `[M]` 29 set, `.deb` cdefd1f (lintian 0 E/0 W; R13, R14, R4 verdi; **R23** due costruzioni identiche: Debian `6655ae2c…`, Ubuntu `223fdb75…`), **debian13-gnome e ubuntu2604-kde**: dopo `apt install` **servizio disabled e inactive, 0 socket sulla 7447, gruppi identici a prima, 0 cinture in vigore** — le sole aggiunte sono i file del pacchetto, le dipendenze (10 / 8), `/var/lib/remotix` e `/run/remotix` vuote (tmpfiles) e il file di stato di debhelper; **`systemctl start`** ⇒ `failed`, `RX-INST-001` nel journal, 0 ripartenze, 0 socket (⚠ `start` esce 0: con `Type=simple` il rifiuto si legge solo nel journal e in `is-active`). `[M]` La prima versione con `ExecStartPre` ripartiva ogni 2 s (`RestartPreventExitStatus` guarda solo il processo principale) — curata. Coi passi del motore a mano: attiva, 2 socket, **Chrome PASS** su tutte e due (GNOME, KDE). **R5**: nessun file cambia contenuto; la reinstallazione aggiunge il file di stato `deb-systemd-helper-enabled/…/remotix.service` (debhelper registra l'abilitazione fatta dal motore: al purge la toglie lui) e rigenera `mimeinfo.cache`. **R6** (passi disfatti + purge + autoremove): nessuna differenza DIRETTA; INDIRETTE `/etc/group-`/`gshadow-` (copie di `gpasswd`, dai passi del motore), cache di icone e mime; estranee CUPS e `fwupd.conf`. ⚠ Il desktop di `prova` resta vivo dopo il purge — su KDE con `kdeconnectd` (1716), avahi e porte UDP sue in ascolto: la domanda per T5 si fa più concreta | copiati sul server (`/media/REMOTIX/vm17/t3/deb/`) |
| 3c8607e | **T3, linea D — la prova del pacchetto Arch in VM**: `banchi/17-distro/17-t3-pacchetto.sh <macchina> <passo>` (un passo per chiamata: `prepara` = persona `prova` già in `video`; `impronta <nome>`; `installa` = copia e `pacman -U --noconfirm`, nient'altro; `r40`; `motore-monta` / `motore-smonta` = i **passi del motore fatti a mano** — `prova` nei gruppi letti dai nodi, col registro MESSO/C'ERA, e `enable --now`; `togli` = `pacman -Rns`; `confronta`) e `17-t3-impronta-arch.sh` (file di `/etc`, `/usr/lib/systemd`, polkit, tmpfiles, applications, `/var/lib/remotix` con sha256, il resto di `/usr` e `/var/lib` con la dimensione; gruppi, conti, unità, pacchetti espliciti/dipendenze, i nomi sotto `/home`) | R4, R5, R6, R33, R40 a livello pacchetto, senza motore | `[M]` 29 set, pacchetto `0.17.0-3` (3c8607e), VM «cliente», sul server in `/media/REMOTIX/vm17/t3/arch-{kde,xfce}/` (le prove del `-1`, prima di §10.12, in `t3/arch-pkgrel1/`). **R4**: `pacman -U` da solo risolve tutto dagli archivi: **arch-kde** +8 pacchetti (labwc, wlr-randr, wlroots0.20, seatd, …), **arch-xfce** +86 (ffmpeg con x264/x265 e ~50 librerie, pipewire+wireplumber+pipewire-pulse, labwc, `gnu-free-fonts` come `ttf-font`: il gruppo xfce4 non porta né ffmpeg né l'audio); 0 aggiornati; due domande di provider (`jack`, `ttf-font`) risposte col predefinito. **R40**: dopo il solo pacchetto servizio `disabled/inactive`, 0 in ascolto sulla 7447, `render` vuoto, 0 cinture e logind/sleep in vigore invariati, firewall intatto — ⛔ ma `systemctl start remotix` **parte** (manca `RX-INST-001`, §13.1). **Passi del motore a mano** ⇒ **Chrome PASS su tutt'e due**: arch-kde «desktop kde», primo fotogramma a 4,2 s, il file di KWin trovato uguale e non riscritto; arch-xfce «desktop xfce» (sfondo nero come in T1), e col `-3` il sink audio «remotix» montato (col `-1`, senza pipewire: «contesto PipeWire non creato … SENZA SUONO»). **R5**: reinstallazione a servizio acceso e sessione viva ⇒ **0 differenze** nelle impronte; il `try-restart` riavvia il server in ~4 s e la sessione di `prova` resta (25 e 39 processi). **R6/R33**, prima → dopo `motore-smonta`+`-Rns`: **nessuna differenza DIRETTA del pacchetto** (via `/etc/remotix`, `/etc/pam.d/remotix`, `/var/lib/remotix`, unità, collegamento d'accensione, tutte le dipendenze portate); `prova` di nuovo solo in `video` (PREESISTENTE, intatta). **INDIRETTE** da dichiarare: il gruppo di sistema `seat` (sysusers di `seatd`, via labwc) che pacman non toglie ⇒ `/etc/group`, `/etc/gshadow` e le copie `-`; su XFCE il collegamento `/usr/lib/libvsscript.so` lasciato da vapoursynth (via ffmpeg); i file del desktop in `/home/prova` (KDE/XFCE, cache, pipewire). **DIRETTE del prodotto a esecuzione, rimaste**: `~/.local/state/remotix/sessione.log`, e su XFCE `xfce4-power-manager.xml` (§8.2). ⚠ Nella prova del `-1`, dopo `-Rns` la sessione KDE di `prova` era già chiusa (2 processi, il gestore d'utente); con la linea B il desktop restava vivo: non guardato oltre | copiati sul server (`/media/REMOTIX/vm17/t3/`) |
| aec8402 | **T4, linea A — le prove del motore** (`installatore/`): `costruisci.sh` (costruzione e `go test` nel contenitore `golang:1.25`, cache in `.cache/` perché `/tmp` del portatile è quasi pieno, `-mod=vendor`, niente rete); `motore/*_test.go` (la macchina finta sotto una cartella: `/etc/group`, `/etc/passwd`, systemd e firewalld finti in file JSON, così lo stato sopravvive al processo ucciso; il gancio `PuntoDiProva`, che nel binario resta sempre nil); `prove/impronta` (impronta di una cartella in Go, indipendente dal motore, con `-confronta` perché i contenitori minimi non hanno `diff`); `prove/r1-contenitori.sh` (R1 in debian:13, fedora:44, archlinux, tumbleweed); `prove/Contenitore.systemd` + `prove/systemd-giro.sh` (Fedora 44 con systemd acceso: le azioni vere sul D-Bus e `gpasswd`) | R30 e R1 in piccolo, senza le VM del server (usate da altri) | vedi §13.1, aec8402 | solo portatile |
| 165906c | **T3, linea C — la prova del `.rpm` in VM**: `banchi/17-distro/17-t3-rpm.sh <macchina> <passo>` (gemello di `17-t3-pacchetto.sh`, con dnf/zypper: `prepara` = persona `prova` già in `video`; `impronta`; `installa` = `dnf install ./…rpm` / `zypper install --allow-unsigned-rpm ./…rpm` e nient'altro; `r40`; `motore` = **i passi del motore a mano** — gruppi della scheda con `17-t3-gruppi.sh` (registro chi c'era / chi è stato messo), servizio firewalld aperto se firewalld è acceso, `enable --now`; `terzi` = RPM Fusion / Packman, **passo separato** (la condizione di §11.1, D5); `selinux` = `ausearch -m avc,user_avc,selinux_err`; `reinstalla`; `motore-annulla`; `togli` = `dnf remove` / `zypper remove --clean-deps`; `confronta`); `17-t3-impronta-rpm.sh` (file, gruppi, utenti, unità, pacchetti con la ragione dnf/zypper, contesti SELinux dei nostri percorsi, firewalld) | provare il pacchetto dove lo troverebbe un cliente, e vedere R40 | `[M]` 29 set, foto «cliente», Chrome vero su `127.0.0.1`, SELinux **enforcing** su tutte e quattro. **R40 verde 4/4**: dopo l'installazione servizio `disabled`/`inactive`, 0 in ascolto sulla 7447, 0 cinture attive, gruppi invariati, firewalld (dove acceso) senza `remotix`. **R4**: `tumbleweed-kde` porta da sé `libavcodec63 libavutil61 libswresample7 libswscale10 breeze6-wallpapers`; `leap16-xfce` 77 pacchetti (ffmpeg, pipewire, libei, libva, **labwc, xwayland**); `fedora44-kde` nessuno (ffmpeg-free già lì); `alma10-gnome` **rifiutato senza EPEL** (`nothing provides libavcodec.so.61`, niente toccato), poi con EPEL+CRB (passo del motore) 28 pacchetti da EPEL. **Desktop nel browser** coi passi del motore: senza depositi di terzi Fedora e Alma **entrano ma non dipingono** («libx265 non c'e' in questa libavcodec», causa C di §11.1); con RPM Fusion / Packman **PASS su tutte e quattro** (TW KDE, Fedora KDE, Alma GNOME, Leap XFCE). ⚠ `fedora44-gnome` era occupata da un'altra prova: Fedora provata su `fedora44-kde`. **R19** 0 rifiuti SELinux in enforcing (Fedora, Alma, TW, Leap) col PAM senza `pam_selinux`; processi del server `unconfined_service_t`. **R5**: reinstallazione ⇒ 0 differenze di REMOTIX (solo rumore del desktop: `cups/subscriptions.conf`, unità transitorie di KDE), servizio ancora acceso; `rpm -V remotix` pulito (il permesso di KWin non riscritto). **R6/R33** (impronta prima dell'installazione ↔ dopo `motore-annulla` + rimozione): **nessuna differenza DIRETTA del pacchetto** (dopo la cura `%ghost` delle marche `.nostro`, che su TW lasciavano `/var/lib/remotix`); gruppi **identici** a prima, `prova` ancora in `video` (PREESISTENTE non toccato); INDIRETTE: `/etc/group-` e `/etc/gshadow-` (copie di gpasswd), le dipendenze che `zypper --clean-deps` tiene perché raccomandate (`breeze6-wallpapers`), la casa di `prova` (file del desktop usato e `~/.local/state/remotix/sessione.log`); del **passo del motore** D5/D6, non annullato qui: il deposito di terzi e le sue librerie (Fedora: ffmpeg-free retrocessa 8.1.2 → 8.0.1), `/etc/firewalld/zones/public.xml` | sul server, in `/media/REMOTIX/vm17/t3-rpm/`; VM tornate a «cliente» |

### 13.3 L'ambiente del server

| che cosa | perché |
|---|---|
| `qemu-system-x86 qemu-utils genisoimage ovmf` installati, `nicfio` nel gruppo `kvm` (29 set) | le VM di §7; ⚠ volatile: sta nella ricetta del dopo-riavvio |
