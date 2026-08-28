# Il protocollo RDP da Windows 10 in avanti — studio

*Che cosa un client moderno negozia davvero, che cosa un server deve implementare, e dove sta ciascuna
cosa in FreeRDP 3.*

Fonti di questo documento:

- le **specifiche aperte Microsoft** della famiglia MS-RDP*, citate per numero di sezione;
- il codice di **FreeRDP 3.22.0** (commit `e3ef4c71`, 21 gennaio 2026), clonato come riferimento
  implementativo: tutte le costanti numeriche riportate qui sono **lette dai suoi header**, non
  ricordate;
- le misure sul campo già registrate in [`SPECIFICA.md`](SPECIFICA.md) §5.4 e §5.7 e le scelte del
  riferimento in [`gnome-remote-desktop.md`](gnome-remote-desktop.md).

Perché «da Windows 10 in avanti»: è la soglia sotto la quale REMOTIX non va (§1 di `SPECIFICA.md`:
*«niente compatibilità con protocolli e client di vent'anni fa»*). Tagliare lì non è una comodità —
**cancella circa i due terzi del protocollo**, e questo documento serve anche a mostrare quali due
terzi.

---

## 1. Le versioni, e che cosa vuol dire «RDP 10»

Attenzione a non confondere tre numerazioni diverse che circolano tutte come «versione di RDP».

**1. La versione del protocollo di base**, quella scambiata nel Client/Server Core Data
([MS-RDPBCGR] 2.2.1.3.2 e 2.2.1.4.2). Valori esatti (`include/freerdp/settings_types.h`):

| Costante | Valore |
|---|---|
| `RDP_VERSION_4` | `0x00080001` |
| `RDP_VERSION_5_PLUS` | `0x00080004` |
| `RDP_VERSION_10_0` | `0x00080005` |
| `RDP_VERSION_10_1` … `10_12` | `0x00080006` … `0x00080011` |

Un client Windows 10 dichiara **10.x**; ma **la versione di base è quasi irrilevante** per un server
moderno, perché tutto ciò che conta si negozia altrove. Serve solo a sapere che il client non è del
2003.

**2. La versione della pipeline grafica** ([MS-RDPEGFX] 2.2.3), che è quella che decide davvero cosa si
può mandare. Vedi §8.

**3. La versione commerciale del client** (`mstsc.exe` 10.x, «Windows App», «Remote Desktop»), che non
sta sul filo e non si può interrogare.

**La regola pratica**: la sola cosa che dice cosa un client sa fare è la combinazione di
*early capability flags* (§4.2), *capability set* (§6) e *caps advertise di EGFX* (§8.1).

---

## 2. Le specifiche che contano

| Documento | Che cosa copre | Serve a REMOTIX |
|---|---|---|
| **MS-RDPBCGR** | Il nucleo: trasporto, connessione, sicurezza, capacità, input, output di base | **Sì, tutto** |
| **MS-RDPEDYC** | Canali dinamici (drdynvc) — il trasporto di tutto il resto | **Sì** |
| **MS-RDPEGFX** | Pipeline grafica: superfici, codec, frame | **Sì, è il cuore** |
| **MS-RDPEDISP** | Risoluzione dinamica | **Sì** |
| **MS-RDPECLIP** | Appunti | **Sì** |
| **MS-RDPEA** | Audio in uscita (rdpsnd) | **Sì** |
| **MS-RDPEAI** | Audio in ingresso (microfono) | **Sì** |
| **MS-RDPEI** | Tocco e penna | Questione aperta n.1 |
| **MS-RDPRFX** | RemoteFX e RemoteFX Progressive | Solo se serve il testo nitido |
| **MS-RDPNSC** | NSCodec | No |
| **MS-RDPEGDI** | Ordini di disegno GDI | **No** — è il grosso di ciò che si taglia |
| **MS-RDPELE** | Licenze | Minimo indispensabile (§7) |
| **MS-RDPERP** | RemoteApp (RAIL) | No |
| **MS-RDPEFS**, **MS-RDPESC**, **MS-RDPEPC** | Dischi, smartcard, stampanti | No |
| **MS-RDPEMT**, **MS-RDPEUDP** | Trasporto UDP | No |
| **MS-RDPECAM** | Webcam del client | No |
| **MS-RDPET** | Telemetria | No |
| **MS-RDPEAR** | Autenticazione remota (Kerberos) | No |

---

## 3. Lo stack, dal basso

```
TCP 3389
 └── TPKT (RFC 1006)            — intestazione a 4 byte con la lunghezza
      └── X.224 (classe 0)      — Connection Request/Confirm, poi Data TPDU
           └── MCS (T.125)      — Connect Initial/Response, Erect Domain, Attach User,
                │                 Channel Join, Send Data Request/Indication
                ├── canale I/O  — il traffico grafico e di input
                └── canali virtuali statici (max 31): drdynvc, cliprdr, rdpsnd, rdpdr…
                     └── drdynvc → canali dinamici: EGFX, DISP, AUDIO_INPUT, RDPEI…
```

E, **in parallelo**, il **fastpath**: dopo l'attivazione, input e output possono saltare X.224 e MCS e
viaggiare in un incapsulamento ridotto. Un client Windows 10 usa il fastpath per **tutto** l'input e
per **tutto** l'output. La strada lenta (`slowpath`, PDU dentro MCS Send Data) resta obbligatoria solo
per la fase di connessione e per pochi PDU di controllo.

Dimensioni di fastpath (`libfreerdp/core/fastpath.h`):

- `FASTPATH_MAX_PACKET_SIZE = 0x3FFF` — sono 14 bit utili, **non 15**: il commento di FreeRDP annota
  che la specifica ne consentirebbe 0x8000 ma «in pratica quasi tutte le implementazioni falliscono
  sopra 0x3FFF»;
- `FASTPATH_FRAGMENT_SAFE_SIZE = 0x3F80` — la soglia sotto la quale non serve frammentare.

La frammentazione fastpath ha quattro stati: `SINGLE`, `FIRST`, `NEXT`, `LAST`.

---

## 4. La connessione, passo per passo

La macchina a stati completa è in `include/freerdp/types.h` (`CONNECTION_STATE`), ed è la spina
dorsale di qualunque implementazione:

```
INITIAL
NEGO                                   ← X.224 + RDP_NEG_REQ/RSP
NLA | AAD                              ← se negoziati (CredSSP / Azure AD)
MCS_CREATE_REQUEST / _RESPONSE         ← Connect Initial/Response con i blocchi GCC
MCS_ERECT_DOMAIN
MCS_ATTACH_USER / _CONFIRM
MCS_CHANNEL_JOIN_REQUEST / _RESPONSE   ← uno per canale
RDP_SECURITY_COMMENCEMENT              ← solo con la cifratura RDP classica
SECURE_SETTINGS_EXCHANGE               ← Client Info PDU
CONNECT_TIME_AUTO_DETECT_REQUEST / _RESPONSE
LICENSING
MULTITRANSPORT_BOOTSTRAPPING_REQUEST / _RESPONSE
CAPABILITIES_EXCHANGE_DEMAND_ACTIVE
CAPABILITIES_EXCHANGE_MONITOR_LAYOUT
CAPABILITIES_EXCHANGE_CONFIRM_ACTIVE
FINALIZATION_SYNC → COOPERATE → REQUEST_CONTROL → PERSISTENT_KEY_LIST → FONT_LIST
FINALIZATION_CLIENT_SYNC → _COOPERATE → _GRANTED_CONTROL → _FONT_MAP
ACTIVE
```

### 4.1 Negoziazione del livello di sicurezza (X.224)

Il client manda una **Connection Request** che può contenere un `RDP_NEG_REQ` con la maschera dei
protocolli che sa fare; il server risponde con `RDP_NEG_RSP` scegliendone **uno solo**, oppure con
`RDP_NEG_FAILURE`.

Protocolli (`libfreerdp/core/nego.h`):

| Costante | Valore | Che cos'è |
|---|---|---|
| `PROTOCOL_RDP` | `0x00` | Cifratura RDP classica (RC4). **Morta**: Windows la rifiuta per default da anni |
| `PROTOCOL_SSL` | `0x01` | TLS puro, autenticazione dentro RDP |
| `PROTOCOL_HYBRID` | `0x02` | **NLA** — CredSSP sopra TLS |
| `PROTOCOL_RDSTLS` | `0x04` | Usato dopo una redirezione, con credenziali passate nella redirezione |
| `PROTOCOL_HYBRID_EX` | `0x08` | NLA con Early User Authorization Result |
| `PROTOCOL_RDSAAD` | `0x10` | Autenticazione Azure AD |

Codici di fallimento: `SSL_REQUIRED_BY_SERVER`, `SSL_NOT_ALLOWED_BY_SERVER`, `SSL_CERT_NOT_ON_SERVER`,
`INCONSISTENT_FLAGS`, `HYBRID_REQUIRED_BY_SERVER`, `SSL_WITH_USER_AUTH_REQUIRED_BY_SERVER`.

**Bandiere della risposta**, ed è qui che si annida un dettaglio che conta:

| Bandiera | Valore | Significato |
|---|---|---|
| `EXTENDED_CLIENT_DATA_SUPPORTED` | `0x01` | Il server accetta i blocchi di dati estesi (monitor!) |
| **`DYNVC_GFX_PROTOCOL_SUPPORTED`** | `0x02` | Il server sa fare **EGFX** |
| `RESTRICTED_ADMIN_MODE_SUPPORTED` | `0x08` | |
| `REDIRECTED_AUTHENTICATION_MODE_SUPPORTED` | `0x10` | |

> **`EXTENDED_CLIENT_DATA_SUPPORTED` va sempre acceso.** Senza, il client non manda il blocco
> `CS_MONITOR` e il server non sa nulla della disposizione degli schermi: si ritrova con la sola
> risoluzione del Client Core Data. È una bandiera di una riga che decide se il multi-monitor è
> possibile.

### 4.2 I blocchi di dati del client (GCC, dentro MCS Connect Initial)

| Blocco | Tipo | Contenuto rilevante |
|---|---|---|
| `CS_CORE` | `0xC001` | Versione, larghezza/altezza desktop, profondità colore, **KLID (layout tastiera)**, tipo e sottotipo tastiera, nome del client, `earlyCapabilityFlags`, `supportedColorDepths`, dimensione fisica, orientamento, fattore di scala |
| `CS_SECURITY` | `0xC002` | Metodi di cifratura (irrilevante con TLS/NLA) |
| `CS_NET` | `0xC003` | Elenco dei **canali virtuali statici** richiesti, con le opzioni |
| `CS_CLUSTER` | `0xC004` | Redirezione di sessione |
| `CS_MONITOR` | `0xC005` | **Disposizione dei monitor** (solo se `EXTENDED_CLIENT_DATA_SUPPORTED`) |
| `CS_MCS_MSGCHANNEL` | `0xC006` | Canale messaggi (serve all'autodetect e al multitransport) |
| `CS_MONITOR_EX` | `0xC008` | Attributi dei monitor: dimensione fisica, orientamento, scala |
| `CS_MULTITRANSPORT` | `0xC00A` | Capacità UDP |

**Early capability flags** (client → server), `settings_types.h`. Sono la lista di controllo più utile
che esista per capire con chi si sta parlando:

| Bandiera | Valore | Significato |
|---|---|---|
| `RNS_UD_CS_SUPPORT_ERRINFO_PDU` | `0x0001` | Sa leggere il codice d'errore alla disconnessione |
| `RNS_UD_CS_WANT_32BPP_SESSION` | `0x0002` | |
| `RNS_UD_CS_SUPPORT_STATUSINFO_PDU` | `0x0004` | |
| `RNS_UD_CS_RELATIVE_MOUSE_INPUT` | `0x0010` | Sa mandare il mouse in coordinate relative |
| `RNS_UD_CS_VALID_CONNECTION_TYPE` | `0x0020` | Il campo `connectionType` è valido (modem / LAN / satellite…) |
| `RNS_UD_CS_SUPPORT_MONITOR_LAYOUT_PDU` | `0x0040` | Accetta il **Monitor Layout PDU** dal server |
| `RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT` | `0x0080` | **Autodetect di rete** (RTT e banda) |
| **`RNS_UD_CS_SUPPORT_DYNVC_GFX_PROTOCOL`** | `0x0100` | **EGFX** |
| `RNS_UD_CS_SUPPORT_DYNAMIC_TIME_ZONE` | `0x0200` | |
| `RNS_UD_CS_SUPPORT_HEARTBEAT_PDU` | `0x0400` | Battito cardiaco a livello RDP |
| `RNS_UD_CS_SUPPORT_SKIP_CHANNELJOIN` | `0x0800` | Salta gli MCS Channel Join uno per uno |

Profondità colore supportate: `RNS_UD_24BPP_SUPPORT 0x0001`, `16BPP 0x0002`, `15BPP 0x0004`,
**`RNS_UD_32BPP_SUPPORT 0x0008`**. Un client che dichiara codec o EGFX **deve** dichiarare anche 32 bpp:
`gnome-remote-desktop` tratta il contrario come violazione di protocollo e chiude.

> **`RNS_UD_CS_SUPPORT_HEARTBEAT_PDU`** merita una nota per REMOTIX. §5.9 di `SPECIFICA.md` risolve il
> problema del client sparito con keepalive TCP stretti e `TCP_USER_TIMEOUT`. Il protocollo ha **un suo
> battito** ([MS-RDPBCGR] 2.2.16.1, `FreeRDP_HeartbeatPdu`): il server manda un `Server Heartbeat PDU`
> con periodo e tolleranze, e il client risponde. È più preciso dei keepalive TCP perché misura il
> client, non il socket. Da valutare come *aggiunta*, non come sostituzione.

### 4.3 Il Client Info PDU

Arriva subito dopo lo scambio di sicurezza e porta: dominio, nome utente, password, programma
alternativo, directory di lavoro, fuso orario, **flag di performance** e le bandiere di sessione.

I flag rilevanti:

- `INFO_AUTOLOGON` — le credenziali sono nel PDU (è il percorso che permette a chi non usa NLA di
  autenticarsi);
- `INFO_UNICODE`, `INFO_MOUSE`, `INFO_DISABLECTRLALTDEL`, `INFO_ENABLEWINDOWSKEY`;
- **`PERF_DISABLE_WALLPAPER`, `PERF_DISABLE_FULLWINDOWDRAG`, `PERF_DISABLE_MENUANIMATIONS`,
  `PERF_DISABLE_THEMING`, `PERF_DISABLE_CURSOR_SHADOW`, `PERF_DISABLE_CURSORSETTINGS`,
  `PERF_ENABLE_FONT_SMOOTHING`, `PERF_ENABLE_DESKTOP_COMPOSITION`** — le *experience settings*, cioè
  quello che il client chiede di spegnere per risparmiare banda.

> Per REMOTIX: quei flag arrivano e vanno **onorati o ignorati consapevolmente**. Su Wayland non c'è
> modo di spegnere il wallpaper per la sola sessione remota; ma `disable-animations` sulla sessione di
> cattura di Mutter (vedi `gnome-remote-desktop.md` §5) fa metà del lavoro, e collegarlo a
> `PERF_DISABLE_MENUANIMATIONS` è coerente.

### 4.4 Il difetto strutturale del percorso senza NLA

Con `PROTOCOL_SSL` puro, l'autenticazione avviene **dentro** il Client Info PDU, e quindi *dopo* che la
connessione è stabilita. Ne discendono due cose che REMOTIX ha già pagato (§3.4 di `SPECIFICA.md`):

1. **un client può non mandare credenziali affatto.** Il campo è opzionale. Un server che valida «se ci
   sono credenziali» non valida niente;
2. la sessione grafica va allocata **dopo** la validazione, non prima, altrimenti si è già speso il
   costo di una sessione per un ospite non autorizzato.

Con NLA il problema non esiste: CredSSP conclude prima che l'MCS parta. È il motivo per cui
`gnome-remote-desktop` impone NLA, e il motivo per cui REMOTIX, che ha scelto TLS puro, deve tenere la
**guardia che parte da negato**.

---

## 5. Sicurezza: che cosa un client Windows 10 accetta davvero

| Livello | mstsc (Win10/11) | Windows App | FreeRDP 3 | Client Android |
|---|---|---|---|---|
| RDP classico (RC4) | rifiutato per policy | rifiutato | supportato ma sconsigliato | vario |
| **TLS puro** (`PROTOCOL_SSL`) | **accettato** con avviso sul certificato | accettato | accettato | accettato |
| **NLA** (`PROTOCOL_HYBRID`) | preferito, spesso **richiesto** dalla policy locale | preferito | supportato | vario |
| RDSTLS | solo dopo redirezione | idem | supportato | no |
| RDSAAD | solo con Entra ID | sì | parziale | no |

Note pratiche:

- **mstsc con TLS puro funziona**, ma se la policy locale del client impone NLA («Richiedi
  autenticazione a livello di rete») il collegamento viene rifiutato *dal client*, non dal server, con
  un messaggio che non spiega. È il primo posto dove guardare quando «mstsc non si collega e il
  registro del server è vuoto».
- Il certificato autofirmato produce sempre un avviso. Non c'è modo di evitarlo se non con una CA
  vera.
- Le versioni TLS le negozia OpenSSL sotto FreeRDP; imporre **TLS 1.2 minimo** è ragionevole, TLS 1.3
  funziona con i client recenti.

---

## 6. Lo scambio di capacità

Il server manda un **Demand Active PDU** con i propri capability set, il client risponde con
**Confirm Active PDU** con i suoi. L'insieme utile è l'intersezione.

Tutti i tipi (`libfreerdp/core/capabilities.h`), con il verdetto per un server **solo EGFX**:

| Tipo | Valore | Serve? |
|---|---|---|
| `GENERAL` | `0x01` | **Sì, obbligatorio** — versione, `extraFlags` (fastpath output, no-bitmap-compression-hdr) |
| `BITMAP` | `0x02` | **Sì, obbligatorio** — porta larghezza, altezza, bpp e `desktopResizeFlag` |
| `ORDER` | `0x03` | **Sì**, ma con tutti gli ordini spenti |
| `BITMAP_CACHE` / `_V2` / `_V3_CODEC_ID` | `0x04`, `0x13`, `0x06` | No |
| `CONTROL` | `0x05` | **Sì**, valori fissi |
| `ACTIVATION` | `0x07` | **Sì**, valori fissi |
| `POINTER` | `0x08` | **Sì** — `colorPointerFlag`, dimensione della cache |
| `SHARE` | `0x09` | **Sì**, valori fissi |
| `COLOR_CACHE` | `0x0A` | No |
| `SOUND` | `0x0C` | Solo se si fa il beep |
| `INPUT` | `0x0D` | **Sì** — fastpath input, unicode, layout tastiera |
| `FONT` | `0x0E` | **Sì**, valori fissi |
| `BRUSH`, `GLYPH_CACHE`, `OFFSCREEN_CACHE` | `0x0F`, `0x10`, `0x11` | No |
| `BITMAP_CACHE_HOST_SUPPORT` | `0x12` | No |
| `VIRTUAL_CHANNEL` | `0x14` | **Sì** — `VCChunkSize`, compressione |
| `DRAW_NINE_GRID_CACHE`, `DRAW_GDI_PLUS` | `0x15`, `0x16` | No |
| `RAIL`, `WINDOW` | `0x17`, `0x18` | No |
| `COMP_DESK` | `0x19` | Opzionale |
| `MULTI_FRAGMENT_UPDATE` | `0x1A` | **Sì** — dice quanto può essere grande un aggiornamento riassemblato |
| `LARGE_POINTER` | `0x1B` | **Sì** — `96x96` (`0x01`) e `384x384` (`0x02`) |
| `SURFACE_COMMANDS` | `0x1C` | **Sì** — serve anche con EGFX |
| `BITMAP_CODECS` | `0x1D` | **Sì** — dichiara RemoteFX/NSCodec; con solo EGFX può restare vuoto |
| `FRAME_ACKNOWLEDGE` | `0x1E` | **Sì** — il controllo di flusso |

**Il conto**: dei 30 capability set, un server solo-EGFX ne usa **13**, e di questi almeno 6 sono
costanti da riempire una volta e non guardare più. Questa tabella è il taglio di §4.3 di `SPECIFICA.md`
espresso in numeri.

### 6.1 La sequenza di riattivazione, e perché va evitata

Dopo il Confirm Active, la finalizzazione è una **danza obbligata in otto PDU** (quattro per parte:
Synchronize, Control Cooperate, Control Request/Granted, Font List/Map). Solo alla fine si è `ACTIVE`.

Se il server manda un **Deactivate All PDU** (`PDU_TYPE_DEACTIVATE_ALL = 0x6`), tutto ricomincia dal
Demand Active. È quello che accade quando si cambia la risoluzione **per la via classica**.

> **È la regola 1 di §5.7 di `SPECIFICA.md`, vista dal lato del protocollo**: con EGFX attivo la misura
> nuova si comunica ridichiarando la tela grafica, non riattivando la sessione. La riattivazione
> azzera lo stato grafico del client, e alcuni client — misurato su Android — **non rinegoziano più
> EGFX** dopo di essa.

C'è però un terzo modo, più pulito del Deactivate All e meno noto:

### 6.2 Il Monitor Layout PDU (server → client)

`DATA_PDU_TYPE_MONITOR_LAYOUT = 0x37`. Se il client ha dichiarato
`RNS_UD_CS_SUPPORT_MONITOR_LAYOUT_PDU (0x0040)`, il server può comunicargli una nuova disposizione di
monitor **senza riattivare**. Nella macchina a stati di FreeRDP ha uno stato suo
(`CONNECTION_STATE_CAPABILITIES_EXCHANGE_MONITOR_LAYOUT`), fra Demand Active e Confirm Active.

Serve a dire al client *«il desktop è fatto così»*; il ridimensionamento vero e proprio, con EGFX,
resta compito di `ResetGraphics` (§8.4).

---

## 7. Licenze

[MS-RDPELE]. Per un server che non fa da Terminal Server Windows, la cosa giusta e sufficiente è
rispondere alla richiesta di licenza con un **`ERROR_ALERT`** (`bMsgType = 0xFF`) che porta
`STATUS_VALID_CLIENT` (`0x00000007`) e `ST_NO_TRANSITION` (`0x00000002`) — cioè: *«non serve licenza,
prosegui»*.

xrdp fa così, `gnome-remote-desktop` fa così, ed è quello che FreeRDP genera da solo lato server se non
si installa un `LicenseCallback`. **Nessun codice da scrivere**, basta non intralciare.

---

## 8. MS-RDPEGFX — la pipeline grafica

È il cuore, e per REMOTIX è **l'unico percorso di rendering**.

Il canale è dinamico e si chiama `Microsoft::Windows::RDS::Graphics`. Il suo trasporto è drdynvc (§11).

### 8.1 Negoziazione delle capacità

Il client manda **`CAPSADVERTISE`** con un elenco di capability set; il server ne sceglie **uno solo**
e risponde **`CAPSCONFIRM`**.

Versioni, con i valori esatti (`include/freerdp/channels/rdpgfx.h`):

| Versione | Valore | Note |
|---|---|---|
| `RDPGFX_CAPVERSION_8` | `0x00080004` | RDP 8.0 — **niente AVC** |
| `RDPGFX_CAPVERSION_81` | `0x00080105` | RDP 8.1 — AVC420 **solo se** `AVC420_ENABLED` |
| `RDPGFX_CAPVERSION_10` | `0x000A0002` | RDP 10.0 — AVC420 e AVC444 |
| `RDPGFX_CAPVERSION_101` | `0x000A0100` | **non ha il campo `flags`** |
| `RDPGFX_CAPVERSION_102` | `0x000A0200` | |
| `RDPGFX_CAPVERSION_103` | `0x000A0301` | Da qui in poi è lecito un secondo `CAPSADVERTISE` |
| `RDPGFX_CAPVERSION_104` | `0x000A0400` | |
| `RDPGFX_CAPVERSION_105` | `0x000A0502` | |
| `RDPGFX_CAPVERSION_106` | `0x000A0600` | ⚠ vedi sotto |
| `RDPGFX_CAPVERSION_107` | `0x000A0701` | |

> ⚠ **Il trabocchetto della 10.6.** Il valore documentato nella specifica era `0x000A0601` ed **è
> sbagliato**; l'errata `[MS-RDPEGFX]-180912` lo corregge in `0x000A0600`. FreeRDP definisce
> **entrambi** (`RDPGFX_CAPVERSION_106` e `RDPGFX_CAPVERSION_106_ERR`) proprio perché in giro esistono
> implementazioni che usano ancora il valore vecchio.
>
> **Un server deve accettarli tutti e due.** E questo è particolarmente rilevante per REMOTIX, perché
> la misura di §5.4 di `SPECIFICA.md` dice che **mstsc si ferma alla 10.6** — cioè proprio sulla
> versione con il valore ambiguo.

**Bandiere di capacità:**

| Bandiera | Valore | Da |
|---|---|---|
| `RDPGFX_CAPS_FLAG_THINCLIENT` | `0x01` | 8.0 |
| `RDPGFX_CAPS_FLAG_SMALL_CACHE` | `0x02` | 8.0 |
| `RDPGFX_CAPS_FLAG_AVC420_ENABLED` | `0x10` | 8.1 |
| `RDPGFX_CAPS_FLAG_AVC_DISABLED` | `0x20` | 10.0 |
| `RDPGFX_CAPS_FLAG_AVC_THINCLIENT` | `0x40` | 10.3 |
| `RDPGFX_CAPS_FLAG_SCALEDMAP_DISABLE` | `0x80` | 10.7 |

**La logica, che va scritta esattamente così** (è quella di `gnome-remote-desktop`, §8.1 di
`gnome-remote-desktop.md`):

```
versione ≥ 10.0 :  AVC420 e AVC444 disponibili  ⟺  NON (flags & AVC_DISABLED)
versione = 8.1  :  AVC420 disponibile           ⟺  (flags & AVC420_ENABLED),  AVC444 mai
versione = 8.0  :  nessun AVC
```

Da cui il difetto di §5.4 di `SPECIFICA.md`: ripiegare sulla 8.1 con un client che non accende
`AVC420_ENABLED` significa **zero fotogrammi H.264**, e con un percorso solo-EGFX significa schermo
nero.

### 8.2 I comandi

`RDPGFX_CMDID_*`, valori esatti:

| Comando | ID | Direzione | Serve? |
|---|---|---|---|
| `WIRETOSURFACE_1` | `0x0001` | S→C | **Sì** — è il fotogramma |
| `WIRETOSURFACE_2` | `0x0002` | S→C | Solo per RFX Progressive con contesto |
| `DELETEENCODINGCONTEXT` | `0x0003` | S→C | Con RFX Progressive |
| `SOLIDFILL` | `0x0004` | S→C | Opzionale, utile |
| `SURFACETOSURFACE` | `0x0005` | S→C | Utile con superficie di rendering separata |
| `SURFACETOCACHE` | `0x0006` | S→C | No |
| `CACHETOSURFACE` | `0x0007` | S→C | No |
| `EVICTCACHEENTRY` | `0x0008` | S→C | No |
| **`CREATESURFACE`** | `0x0009` | S→C | **Sì** |
| **`DELETESURFACE`** | `0x000A` | S→C | **Sì** |
| **`STARTFRAME`** | `0x000B` | S→C | **Sì** |
| **`ENDFRAME`** | `0x000C` | S→C | **Sì** |
| **`FRAMEACKNOWLEDGE`** | `0x000D` | C→S | **Sì** |
| **`RESETGRAPHICS`** | `0x000E` | S→C | **Sì** |
| **`MAPSURFACETOOUTPUT`** | `0x000F` | S→C | **Sì, e non è opzionale** |
| `CACHEIMPORTOFFER` | `0x0010` | C→S | Va **risposto** anche se vuoto |
| `CACHEIMPORTREPLY` | `0x0011` | S→C | Risposta vuota |
| **`CAPSADVERTISE`** | `0x0012` | C→S | **Sì** |
| **`CAPSCONFIRM`** | `0x0013` | S→C | **Sì** |
| `MAPSURFACETOWINDOW` | `0x0015` | S→C | Solo RAIL |
| `QOEFRAMEACKNOWLEDGE` | `0x0016` | C→S | Accettare e ignorare |
| `MAPSURFACETOSCALEDOUTPUT` | `0x0017` | S→C | No |
| `MAPSURFACETOSCALEDWINDOW` | `0x0018` | S→C | No |

Intestazione comune: 8 byte (`cmdId` 16, `flags` 16, `pduLength` 32).

> **`CREATESURFACE` e `MAPSURFACETOOUTPUT` sono due comandi distinti**, e questo è il punto su cui
> REMOTIX ha perso due giorni (§5.4 di `SPECIFICA.md`). Creare la superficie la fa esistere; agganciarla
> all'uscita la fa **vedere**. FreeRDP e i client Android disegnano lo stesso, mstsc no — e mstsc ha
> ragione.

### 8.3 Superfici

`CREATESURFACE` porta `surfaceId` (16 bit), larghezza, altezza e formato:

- `GFX_PIXEL_FORMAT_XRGB_8888 = 0x20`
- `GFX_PIXEL_FORMAT_ARGB_8888 = 0x21`

`MAPSURFACETOOUTPUT` porta `surfaceId`, `outputOriginX`, `outputOriginY`. Con un monitor solo l'origine
è (0, 0); con più monitor è l'angolo del monitor **nella tela complessiva**.

### 8.4 `RESETGRAPHICS`

Ridichiara la tela: larghezza e altezza del *Graphics Output Buffer*, più l'array dei `MONITOR_DEF`.

Il `MONITOR_DEF` usa **bordi inclusivi**:

```c
monitor_def->right  = left + width  - 1;
monitor_def->bottom = top  + height - 1;
```

e la bandiera `MONITOR_PRIMARY = 0x00000001` marca il primario.

**Regole che ne discendono**, tutte già pagate almeno una volta:

1. l'elenco dei monitor **non può essere vuoto** — un `ResetGraphics` senza monitor produce
   un'immagine disegnata fuori posto (§5.4 di `SPECIFICA.md`, quarto difetto);
2. **tutte le superfici vanno cancellate prima** di un `ResetGraphics`. `gnome-remote-desktop` lo
   verifica con un `g_assert`;
3. dopo un `ResetGraphics` si ricrea la superficie, e **si rimappa all'uscita**.

### 8.5 Fotogrammi e riscontri

```
STARTFRAME(frameId, timestamp)
WIRETOSURFACE_1(surfaceId, codecId, pixelFormat, left, top, right, bottom, bitmapData)
ENDFRAME(frameId)
```

Il `timestamp` è impacchettato: `ora<<22 | minuti<<16 | secondi<<10 | millisecondi`.

Il client risponde con `FRAMEACKNOWLEDGE(queueDepth, frameId, totalFramesDecoded)`.

**`queueDepth` ha un valore speciale**: `SUSPEND_FRAME_ACKNOWLEDGEMENT` (`0xFFFFFFFF`) significa *«non
mandarmi più riscontri, non li userò»*. Un server che aspetta i riscontri per regolare il flusso deve
accorgersene e passare a un conteggio locale, altrimenti **si blocca per sempre**.

`totalFramesDecoded` permette di ricostruire quanti fotogrammi sono ancora in volo anche se un ack si
è perso: `in_volo = totale_codificati − totalFramesDecoded`.

### 8.6 Le due convenzioni di geometria

Questo è il punto che vale la pena scrivere in grande, perché **all'interno dello stesso protocollo
convivono due convenzioni** e sbagliarle produce lo stesso sintomo (rinegoziazione, disconnessione,
o immagine spostata di un pixel):

| Struttura | Convenzione |
|---|---|
| `RDPGFX_SURFACE_COMMAND` (`left`, `top`, `right`, `bottom`) | `right = x + width` — **esclusiva** |
| `RECTANGLE_16` della metablock AVC420 | `right = x + width` — **esclusiva** |
| `MONITOR_DEF` di `RESETGRAPHICS` | `right = left + width − 1` — **inclusiva** |

> §5.4 di `SPECIFICA.md` registra *«i bordi della regione AVC420 sono inclusivi»*. Il riferimento
> `gnome-remote-desktop` scrive `right = x + width`, cioè esclusivo, e funziona con mstsc. **Le due
> affermazioni non possono essere entrambe vere.** Va accertato sui byte, non sul codice, prima di
> scrivere l'encoder.

---

## 9. I codec

`RDPGFX_CODECID_*`:

| Codec | ID | Che cos'è | Per REMOTIX |
|---|---|---|---|
| `UNCOMPRESSED` | `0x0000` | Pixel grezzi | **Non renderizzato da mstsc** (§5.4) |
| `CAVIDEO` | `0x0003` | RemoteFX | No |
| `CLEARCODEC` | `0x0008` | ClearCodec | No |
| `CAPROGRESSIVE` | `0x0009` | **RemoteFX Progressive** | Il ripiego di GNOME; utile per il testo |
| `PLANAR` | `0x000A` | Planar | No |
| **`AVC420`** | `0x000B` | H.264 4:2:0 | **Sì, la base** |
| `ALPHA` | `0x000C` | Canale alfa | No |
| `CAPROGRESSIVE_V2` | `0x000D` | | No |
| `AVC444` | `0x000E` | H.264 4:4:4, v1 | Opzionale |
| **`AVC444v2`** | `0x000F` | H.264 4:4:4, v2 | Opzionale, preferito su v1 |

**Non esistono HEVC né AV1.** È il vincolo di §5.1 di `SPECIFICA.md`, e il codice lo conferma: la
tabella dei codec finisce qui.

### 9.1 AVC420 — la metablock

Un `WIRETOSURFACE_1` con `codecId = AVC420` non porta solo il flusso H.264: porta una
`RFX_AVC420_METABLOCK` che dice **quali rettangoli dello schermo** quel flusso aggiorna, e con quale
qualità:

```
numRegionRects        (UINT32)
regionRects[]         (RECTANGLE_16 ciascuno: left, top, right, bottom)
quantQualityVals[]    (uno per rettangolo: qp:6bit, r:1bit, p:1bit, qualityVal:8bit)
```

- `qp` — il quantizzatore usato (0–51);
- `p` — 1 se il rettangolo viene da un frame P, 0 se da un I/IDR;
- `qualityVal` — 0–100, indicativo.

**Il flusso H.264 copre l'intera superficie allineata**; i rettangoli dicono al client quali parti
della superficie sono cambiate davvero, così il decodificatore può saltare il resto. Un server che
dichiara un solo rettangolo grande quanto lo schermo è corretto ma spreca.

### 9.2 Allineamento

Il flusso H.264 deve avere dimensioni compatibili col codificatore. La regola misurata, e confermata da
`gnome-remote-desktop`:

```
larghezza allineata a 16
altezza    allineata a 64
```

L'altezza a 64 e non a 16 è la sorpresa: viene dal fatto che il decodificatore Microsoft lavora a
macroblocchi raggruppati. **Violarla produce rinegoziazione e disconnessione su mstsc**, non un
errore leggibile.

Il bordo in eccesso si assorbe **riempiendolo**, non riducendo lo schermo: il desktop resta della
misura chiesta dal client (§5.4 di `SPECIFICA.md`, regola operativa).

### 9.3 AVC444 e AVC444v2

Il 4:2:0 sottocampiona la crominanza e **sfuoca il testo colorato**. AVC444 risolve mandando la
crominanza mancante come **un secondo flusso H.264**, impacchettata in un fotogramma ausiliario.

La struttura `RDPGFX_AVC444_BITMAP_STREAM` porta:

- `cbAvc420EncodedBitstream1` — dimensione del primo flusso, e nei 2 bit alti il campo **`LC`**;
- `bitstream[0]` — vista principale (luma + croma sottocampionata);
- `bitstream[1]` — vista ausiliaria (la croma mancante), presente solo se `LC = 0`.

Valori di `LC`:

| `LC` | Significato |
|---|---|
| `0` | **Vista doppia**: entrambi i flussi presenti |
| `1` | Solo vista principale (YUV420) |
| `2` | Solo vista ausiliaria (Chroma420) |

Quando `LC = 2`, `cbAvc420EncodedBitstream1` **deve valere zero** ([MS-RDPEGFX] 2.2.4.6).

> **La strategia che ne discende, ed è quella di `gnome-remote-desktop`**: si manda `LC = 1` sempre, e
> quando il collegamento è tranquillo si **completa** il fotogramma già mandato con un `LC = 2` poco
> dopo. Il costo del 4:4:4 si paga solo quando c'è margine, e non si raddoppia la banda per default.
> È la risposta operativa a §5.2 di `SPECIFICA.md`, migliore di «AVC444 attivabile su connessioni
> migliori» perché la granularità è il fotogramma, non la sessione.

### 9.4 RemoteFX Progressive

Trasportato con `WIRETOSURFACE_2` (che ha un `codecContextId`) oppure con `WIRETOSURFACE_1`. La
struttura dei blocchi, per chi dovesse scriverla a mano:

| Blocco | `blockType` |
|---|---|
| `RFX_PROGRESSIVE_SYNC` | `0xCCC0` |
| `RFX_PROGRESSIVE_FRAME_BEGIN` | `0xCCC1` |
| `RFX_PROGRESSIVE_FRAME_END` | `0xCCC2` |
| `RFX_PROGRESSIVE_CONTEXT` | `0xCCC3` |
| `RFX_PROGRESSIVE_REGION` | `0xCCC4` |
| `RFX_PROGRESSIVE_TILE_SIMPLE` | `0xCCC5` |

Un trabocchetto documentato nel codice di `gnome-remote-desktop`: **l'ordine delle bande di
quantizzazione è diverso** fra MS-RDPRFX e MS-RDPEGFX.

```
RDPRFX:   LL3, LH3, HL3, HH3, LH2, HL2, HH2, LH1, HL1, HH1
RDPEGFX:  LL3, HL3, LH3, HH3, HL2, LH2, HH2, HL1, LH1, HH1
```

Chi riusa l'encoder RemoteFX di FreeRDP per produrre Progressive **deve rimescolare**.

---

## 10. Superfici, fastpath e puntatore

### 10.1 Surface Commands (la via pre-EGFX)

Anche con EGFX, il capability set `SURFACE_COMMANDS` va dichiarato, perché il client lo usa per capire
che il server sa lavorare a superfici. I comandi veri (`SET_SURFACE_BITS`, `FRAME_MARKER`) servono
solo al percorso senza EGFX.

`FreeRDP_SurfaceFrameMarkerEnabled` e `FreeRDP_FrameMarkerCommandEnabled` vanno accesi entrambi.

### 10.2 Aggiornamenti fastpath

`FASTPATH_UPDATETYPE_*`: `ORDERS 0x0`, `BITMAP 0x1`, `PALETTE 0x2`, `SYNCHRONIZE 0x3`,
**`SURFCMDS 0x4`**, `PTR_NULL 0x5`, `PTR_DEFAULT 0x6`, `PTR_POSITION 0x8`, `COLOR 0x9`, `CACHED 0xA`,
**`POINTER 0xB`**, **`LARGE_POINTER 0xC`**.

Un server solo-EGFX usa **solo quelli del puntatore**: il resto viaggia nel canale dinamico.

### 10.3 Il puntatore

Non passa da EGFX: resta sul percorso classico. Tre forme:

- `PTR_NULL` / `PTR_DEFAULT` — nascosto / freccia di sistema;
- `POINTER` (new pointer, 32 bpp) e `LARGE_POINTER` — l'immagine, con hotspot;
- `CACHED` — riusa un cursore già mandato, per indice.

Il capability set `POINTER` dichiara la **dimensione della cache** (`gnome-remote-desktop` usa 100;
FreeRDP rifiuta un client che dichiari cache zero), e `LARGE_POINTER` dichiara se si può andare oltre
32×32:

- `LARGE_POINTER_FLAG_96x96 = 0x01`
- `LARGE_POINTER_FLAG_384x384 = 0x02`

> Con la cattura PipeWire il cursore arriva **come metadato separato** (`SPA_META_Cursor`, fino a
> 384×384 in `gnome-remote-desktop`), non disegnato nell'immagine. È l'accoppiata giusta: cursore
> fuori dal flusso video significa che si muove alla latenza della rete e non a quella del codificatore.

---

## 11. MS-RDPEDYC — i canali dinamici

Tutto ciò che è moderno viaggia qui. Il canale statico si chiama `drdynvc`; sopra di lui si aprono i
canali dinamici per nome.

PDU (`include/freerdp/channels/drdynvc.h`):

| PDU | Valore |
|---|---|
| `CREATE_REQUEST_PDU` | `0x01` |
| `DATA_FIRST_PDU` | `0x02` |
| `DATA_PDU` | `0x03` |
| `CLOSE_REQUEST_PDU` | `0x04` |
| `CAPABILITY_REQUEST_PDU` | `0x05` |
| `DATA_FIRST_COMPRESSED_PDU` | `0x06` |
| `DATA_COMPRESSED_PDU` | `0x07` |
| `SOFT_SYNC_REQUEST_PDU` | `0x08` |
| `SOFT_SYNC_RESPONSE_PDU` | `0x09` |

**Il frammentamento è obbligatorio**: un messaggio più lungo del chunk va spezzato in un `DATA_FIRST`
(che porta la lunghezza totale) seguito da `DATA`. Il chunk dipende da `VCChunkSize` del capability set
`VIRTUAL_CHANNEL`; `gnome-remote-desktop` usa **16256**.

Le versioni del protocollo (1, 2, 3) cambiano la dimensione del campo `ChannelId` e abilitano il
*soft sync* — cioè lo spostamento di canali su trasporto UDP, che REMOTIX non usa.

Nomi dei canali dinamici rilevanti:

| Nome | Che cos'è |
|---|---|
| `Microsoft::Windows::RDS::Graphics` | EGFX |
| `Microsoft::Windows::RDS::DisplayControl` | MS-RDPEDISP |
| `Microsoft::Windows::RDS::Input` | MS-RDPEI (tocco e penna) |
| `AUDIO_PLAYBACK_DVC` | Audio in uscita |
| `AUDIO_PLAYBACK_LOSSY_DVC` | Audio in uscita con perdita |
| `AUDIO_INPUT` | Microfono |
| `Microsoft::Windows::RDS::Telemetry` | Telemetria |
| `Microsoft::Windows::RDS::Video::*` | Camera (MS-RDPECAM) |

Nota: `cliprdr`, `rdpsnd` e `rdpdr` sono canali **statici**, non dinamici. L'audio in uscita esiste in
entrambe le forme.

---

## 12. MS-RDPEDISP — risoluzione dinamica

Il più semplice dei canali, e il più utile.

Due PDU:

| PDU | Valore | Direzione |
|---|---|---|
| `DISPLAY_CONTROL_PDU_TYPE_MONITOR_LAYOUT` | `0x00000002` | C→S |
| `DISPLAY_CONTROL_PDU_TYPE_CAPS` | `0x00000005` | S→C |

Il server apre il canale e manda subito le **capacità**: numero massimo di monitor,
`MaxMonitorAreaFactorA` e `...B` (entrambi **8192** in `gnome-remote-desktop`). Il client risponde,
quando vuole, con un `MONITOR_LAYOUT` — tipicamente quando l'utente ridimensiona la finestra.

**I limiti sono nel protocollo**, non inventati (`include/freerdp/channels/disp.h`):

| Vincolo | Valore |
|---|---|
| `DISPLAY_CONTROL_MIN_MONITOR_WIDTH` / `HEIGHT` | **200** |
| `DISPLAY_CONTROL_MAX_MONITOR_WIDTH` / `HEIGHT` | **8192** |
| `MIN` / `MAX_PHYSICAL_MONITOR_WIDTH` (mm) | 10 / 10000 |
| `DISPLAY_CONTROL_MONITOR_LAYOUT_SIZE` | 40 byte per monitor |
| `DISPLAY_CONTROL_MONITOR_PRIMARY` | `0x00000001` |

Ogni voce porta: `Flags`, `Left`, `Top`, `Width`, `Height`, `PhysicalWidth`, `PhysicalHeight`,
`Orientation`, `DesktopScaleFactor`, `DeviceScaleFactor`.

> **`DeviceScaleFactor` va ignorato**: è deprecato (solo Windows 8.1). Lo annota il codice di
> `gnome-remote-desktop` in tre punti diversi.
>
> **Larghezza e altezza vanno pari.** Non è nella specifica ma è pratica universale: un monitor di
> larghezza dispari rompe qualunque codificatore 4:2:0.

Le regole di validazione da applicare — sono quelle di `gnome-remote-desktop`, e derivano dalla
specifica: primario a (0,0), niente sovrapposizioni, scala fra 100 e 500.

### 12.1 Il tranello dei tempi

Misurato in §5.7 di `SPECIFICA.md`: **il client Android manda il suo `MONITOR_LAYOUT` entro un decimo
di secondo dalla connessione**, cioè *prima* di aver negoziato EGFX. Applicarlo subito costringe alla
riattivazione (§6.1) e rovina la sessione.

La regola: **si rinvia il ridimensionamento finché la pipeline grafica non è pronta**, e allora si
applica per la via della tela grafica. Solo se la pipeline non arriva affatto si ricorre alla
riattivazione.

---

## 13. Input

### 13.1 Eventi fastpath

`FASTPATH_INPUT_EVENT_*`:

| Evento | Valore |
|---|---|
| `SCANCODE` | `0x0` |
| `MOUSE` | `0x1` |
| `MOUSEX` (pulsanti estesi) | `0x2` |
| `SYNC` (stato dei tasti a scatto) | `0x3` |
| `UNICODE` | `0x4` |
| `TS_FP_RELPOINTER_EVENT` | `0x5` |
| `TS_FP_QOETIMESTAMP_EVENT` | `0x6` |

### 13.2 Tastiera

Le bandiere (`include/freerdp/input.h`):

| Bandiera | Slowpath | Fastpath |
|---|---|---|
| Rilascio | `KBD_FLAGS_RELEASE 0x8000` | `FASTPATH_INPUT_KBDFLAGS_RELEASE 0x01` |
| Esteso (prefisso `0xE0`) | `KBD_FLAGS_EXTENDED 0x0100` | `..._EXTENDED 0x02` |
| Esteso1 (prefisso `0xE1`) | `KBD_FLAGS_EXTENDED1 0x0200` | `..._PREFIX_E1 0x04` |

Il codice è uno **scancode set 1**. La conversione verso evdev passa per due tabelle di WinPR:

```c
fullcode = (flags & EXTENDED) ? scancode | KBDEXT : scancode;
vkcode   = GetVirtualKeyCodeFromVirtualScanCode (fullcode, keyboardType);
vkcode   = (flags & EXTENDED) ? vkcode | KBDEXT : vkcode;
keycode  = GetKeycodeFromVirtualKeyCode (vkcode, WINPR_KEYCODE_TYPE_EVDEV);
```

**Il tasto Pausa** è l'unico con prefisso `0xE1`, e sul filo arriva come una **sequenza di quattro
eventi**: `Ctrl↓(E1)`, `NumLock↓`, `Ctrl↑(E1)`, `NumLock↑`. Va riconosciuto con una macchina a stati.

**Gli eventi Unicode** arrivano come UTF-16, e servono per i caratteri che la disposizione del client
non colloca su nessun tasto. Vanno tradotti in keysym e poi in una posizione fisica della disposizione
*della sessione*.

**La disposizione del client** viaggia come **KLID** nel Client Core Data (`0x0410` = italiano,
`0x0409` = US…), e FreeRDP la mette in `rdpSettings` (`FreeRDP_KeyboardLayout`), insieme a
`KeyboardType` e `KeyboardSubType`. **È a disposizione del server, senza contributi a monte.**

### 13.3 Mouse

| Bandiera | Valore |
|---|---|
| `PTR_FLAGS_MOVE` | `0x0800` |
| `PTR_FLAGS_DOWN` | `0x8000` |
| `PTR_FLAGS_BUTTON1` (sinistro) | `0x1000` |
| `PTR_FLAGS_BUTTON2` (destro) | `0x2000` |
| `PTR_FLAGS_BUTTON3` (centrale) | `0x4000` |
| `PTR_FLAGS_WHEEL` | `0x0200` |
| `PTR_FLAGS_HWHEEL` | `0x0400` |
| `PTR_FLAGS_WHEEL_NEGATIVE` | `0x0100` |
| `WheelRotationMask` | `0x01FF` |
| `PTR_XFLAGS_DOWN` | `0x8000` |
| `PTR_XFLAGS_BUTTON1` / `2` (laterali) | `0x0001` / `0x0002` |

**La rotella.** Il valore sta nei 9 bit bassi (`WheelRotationMask`), **in complemento a due** quando
`PTR_FLAGS_WHEEL_NEGATIVE` è acceso. Uno scatto vale **120**. La conversione corretta:

```c
value = flags & WheelRotationMask;
if (value & PTR_FLAGS_WHEEL_NEGATIVE) { value = (~value & WheelRotationMask) + 1; }
step = -value / 120.0;
if (flags & PTR_FLAGS_WHEEL_NEGATIVE) step = -step;
```

E poi: **il verticale è invertito rispetto a Wayland, l'orizzontale no.**

Le coordinate degli eventi di rotella **sono riempite di zeri** da molti client: un server che tratta
ogni evento mouse come un movimento fa saltare il puntatore nell'angolo a ogni scatto. Vanno scartate
quando `WHEEL` o `HWHEEL` sono accesi.

### 13.4 Sincronizzazione

`FASTPATH_INPUT_EVENT_SYNC` porta lo stato dei tasti a scatto: `KBD_SYNC_SCROLL_LOCK 0x01`,
`KBD_SYNC_NUM_LOCK 0x02`, `KBD_SYNC_CAPS_LOCK 0x04`, `KBD_SYNC_KANA_LOCK 0x08`. Arriva quando il client riprende il
fuoco. **Va usato per rilasciare tutto e riconciliare i lucchetti**, non ignorato.

### 13.5 MS-RDPEI — tocco e penna

Canale dinamico `Microsoft::Windows::RDS::Input`. Versioni: `V10 0x00010000`, `V101 0x00010001`,
`V200 0x00020000`, `V300 0x00030000`.

Stati di un contatto: `DOWN 0x0001`, `UPDATE 0x0002`, `UP 0x0004`, `INRANGE 0x0008`,
`INCONTACT 0x0010`, `CANCELED 0x0020` — e non tutte le combinazioni sono valide, la specifica dà le
transizioni ammesse ([MS-RDPEI] 3.1.1.1).

Campi opzionali per contatto: rettangolo, orientamento, pressione.

Per la penna: `PENFLAGS`, `PRESSURE`, `ROTATION`, `TILTX`, `TILTY`.

`gnome-remote-desktop` gestisce fino a **256 contatti**.

---

## 14. Audio

### 14.1 Uscita — MS-RDPEA

Canale statico `rdpsnd`, oppure dinamico `AUDIO_PLAYBACK_DVC` (preferibile: non compete con gli altri
canali statici).

Il client manda l'elenco dei formati che sa decodificare; il server ne sceglie uno. I `wFormatTag`
rilevanti:

| Formato | Tag | Note |
|---|---|---|
| PCM | `0x0001` | **Sempre disponibile**, 16 bit, la base obbligatoria |
| A-law / μ-law | `0x0006` / `0x0007` | |
| ADPCM | `0x0002`, `0x0011` | |
| MP3 | `0x0055` | |
| **AAC** | `0xA106` (`WAVE_FORMAT_AAC_MS`) | Il migliore per il rapporto qualità/banda |
| **Opus** | `0x704F` (`WAVE_FORMAT_OPUS`) | 48 kHz, ottima latenza |

`gnome-remote-desktop` prova in ordine **AAC → Opus → PCM**, stereo fisso.

Due avvertenze misurate dal riferimento, entrambe rilevanti per REMOTIX:

1. se il client **non fa autodetect di rete**, l'audio viene spento: senza misura della banda peggiora
   il video;
2. i client **iOS e Android** vengono esclusi dall'audio con la motivazione *«non sanno gestire grafica
   e audio insieme»*. Da verificare sul campo, ma è un avviso serio dato che Android è fra i client di
   riferimento di REMOTIX.

### 14.2 Ingresso — MS-RDPEAI

Canale dinamico `AUDIO_INPUT`. Sequenza: `VERSION` → `FORMATS` → `OPEN` → `OPEN_REPLY` →
`DATA_INCOMING` → `DATA`, più `FORMATCHANGE`.

I formati sono gli stessi dell'uscita. Il server **decodifica**: `gnome-remote-desktop` implementa
almeno la decodifica A-law oltre al PCM.

---

## 15. Appunti — MS-RDPECLIP

Canale statico `cliprdr`. La sequenza minima:

```
S→C  CLIPRDR_MONITOR_READY
C→S  CLIPRDR_CAPS                 (general caps: long format names, stream file clip, …)
C→S  CLIPRDR_FORMAT_LIST          quando il client copia qualcosa
S→C  CLIPRDR_FORMAT_LIST_RESPONSE
S→C  CLIPRDR_FORMAT_DATA_REQUEST  quando la sessione incolla
C→S  CLIPRDR_FORMAT_DATA_RESPONSE
```

e simmetrico nell'altro verso.

Formati: `CF_UNICODETEXT` (13), `CF_TEXT` (1), `CF_DIB` (8), `CF_DIBV5` (17), più formati registrati
per nome — `HTML Format`, `PNG`, `JFIF`, `GIF`, e **`FileGroupDescriptorW`** per i file.

> **Il testo è poche centinaia di righe; i file sono un progetto a sé.** `FileGroupDescriptorW` porta
> solo i metadati; il contenuto si chiede blocco per blocco con `CLIPRDR_FILECONTENTS_REQUEST`, e per
> esporlo nella sessione serve un filesystem virtuale — in `gnome-remote-desktop` sono 1591 righe di
> FUSE. §3.5 di `SPECIFICA.md` dice «clipboard bidirezionale» in una riga: va spacchettata in due
> tappe, testo e immagini prima, file molto dopo.

---

## 16. Misura della rete

[MS-RDPBCGR] 2.2.14. Due meccanismi, sullo stesso canale messaggi.

**RTT**: il server manda `RTT Measure Request` con un numero di sequenza, il client risponde subito con
`RTT Measure Response`. La differenza è il round trip.

**Banda**: `Bandwidth Measure Start` → (il server manda dati veri, tipicamente un fotogramma) →
`Bandwidth Measure Stop` → il client risponde con `Bandwidth Measure Results`, che riporta byte e
tempo.

Poi il server può informare il client con un `Network Characteristics Result`.

Esiste anche l'autodetect **al momento della connessione**, con uno stato dedicato nella macchina
(`CONNECT_TIME_AUTO_DETECT_REQUEST/RESPONSE`), che dà una prima stima prima ancora di disegnare.

Cadenze usate da `gnome-remote-desktop`: **70 ms** quando serve precisione, **700 ms** a riposo; la
misura di banda si aggancia solo a fotogrammi **≥ 10 KB**, altrimenti il risultato è rumore.

> Prerequisito: il client deve aver dichiarato `RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT (0x0080)`. Chi non
> lo dichiara non va misurato, e va servito con parametri prudenti.

**Quel che il client conta davvero.** Fra `Bandwidth Measure Start` e `Stop` il client somma la
lunghezza di **ogni PDU che riceve** — `rdp.c:1678` e `:1817` di FreeRDP lo fanno sia sul percorso
TPKT sia su quello fastpath, canali dinamici compresi. Il carico della misura è quindi il fotogramma
vero: non serve spedire i dati di riempimento, che servono solo alla misura *alla connessione*.
[R, 5 agosto 2026]

**⛔ Ma i marcatori vanno messi dove i byte passano davvero**, non dove si chiama la funzione che li
produce: le scritture sui canali dinamici sono accodate, quelle di autodetect no. È R19 di
`REFERENCE.md`, e senza quella il client risponde di aver contato dieci byte. [M, 5 agosto 2026]

**Chi lo dichiara**, misurato al banco il 5 agosto: `xfreerdp3` **sì**, e la misura funziona
completa (sonde, banda, `NETCHAR_RESULT`). Per mstsc e RDM non è ancora stato verificato — l'unica
conseguenza è che restano alla soglia prudente, quindi non è bloccante.

---

## 17. Fine sessione e codici d'errore

`DATA_PDU_TYPE_SET_ERROR_INFO = 0x2F` porta un codice a 32 bit che dice **perché** la sessione finisce.
Mandarlo prima di chiudere il socket è la differenza fra un client che spiega e un client che dà
«errore di rete».

I codici che servono (`include/freerdp/error.h`):

| Codice | Valore | Quando |
|---|---|---|
| `ERRINFO_RPC_INITIATED_DISCONNECT` | `0x01` | Il server chiude di sua iniziativa |
| `ERRINFO_RPC_INITIATED_LOGOFF` | `0x02` | Disconnessione per logoff |
| `ERRINFO_IDLE_TIMEOUT` | `0x03` | Inattività |
| `ERRINFO_LOGON_TIMEOUT` | `0x04` | |
| `ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION` | `0x05` | **Un altro client ha preso il posto** |
| `ERRINFO_OUT_OF_MEMORY` | `0x06` | |
| `ERRINFO_SERVER_DENIED_CONNECTION` | `0x07` | **Il server rifiuta** |
| `ERRINFO_RPC_INITIATED_DISCONNECT_BY_USER` | `0x0B` | |
| **`ERRINFO_LOGOFF_BY_USER`** | `0x0C` | **L'utente è uscito dalla sessione** |
| `ERRINFO_CLOSE_STACK_ON_DRIVER_FAILURE` | `0x11` | Guasto del sottosistema |
| `ERRINFO_BAD_CAPABILITIES` | `0x10EA` | Capacità del client inaccettabili |
| `ERRINFO_BAD_MONITOR_DATA` | `0x1129` | Disposizione monitor non valida |
| `ERRINFO_BAD_FRAME_ACK_DATA` | `0x112C` | |
| `ERRINFO_GRAPHICS_SUBSYSTEM_FAILED` | `0x112F` | |

> **Per REMOTIX questo chiude due debiti registrati in `SPECIFICA.md`.**
>
> Il primo è §5.9, *«il client dice “connessione chiusa”, non “c'è già qualcuno”… RDP non ha un codice
> di rifiuto che significhi occupato»*. **Ce l'ha**: `ERRINFO_SERVER_DENIED_CONNECTION (0x07)`, e per il
> caso «soppiantato» c'è `ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION (0x05)`.
>
> Il secondo è il congedo dopo un logout: `ERRINFO_LOGOFF_BY_USER (0x0C)` esiste ed è esattamente
> quello che serve.
>
> Con FreeRDP entrambi si mandano con `freerdp_set_error_info()`. Il prerequisito è che il client abbia
> dichiarato `RNS_UD_CS_SUPPORT_ERRINFO_PDU (0x0001)`, cosa che tutti i client moderni fanno.

Nota su `SO_LINGER`: §5.9 di `SPECIFICA.md` usa un RST per troncare di netto. **Con il codice d'errore
disponibile il RST diventa la seconda scelta**: prima si manda `SET_ERROR_INFO`, poi si chiude in modo
ordinato. Il RST resta utile solo quando serve tagliare *subito*, prima che il client abbia tempo di
leggere.

---

## 18. Che cosa fanno davvero i client

Riassunto di quello che si è misurato, fra §5.4 e §5.7 di `SPECIFICA.md` e il codice del riferimento.

| | mstsc (Win 10/11) | Windows App | FreeRDP 3 | Android moderno |
|---|---|---|---|---|
| Versione EGFX massima | **10.6** | 10.7 | 8.1 (per default) | varia |
| Negozia EGFX | subito | subito | subito | **dopo** aver chiesto la propria misura |
| EGFX non compresso | **non lo disegna** | idem | lo disegna | lo disegna |
| Superficie non mappata all'uscita | **non la disegna** | idem | la disegna comunque | la disegna comunque |
| Ridimensiona da sé | **no** | sì | solo se richiesto | sì, subito |
| Autodetect di rete | sì | sì | sì | spesso no |
| Audio + grafica insieme | sì | sì | sì | **problematico** |
| Tolleranza agli errori del server | **nessuna** | bassa | alta | alta |

**La regola dei tre client**, che vale più di ogni tabella: *nessuno dei tre copre i casi degli altri*.
FreeRDP e Android suppliscono alle omissioni del server; mstsc prende alla lettera. Un difetto che si
vede solo su mstsc è quasi sempre **un'informazione che il server ha omesso**, non un'anomalia del
client.

E il corollario sulle prove automatiche, pagato in §5.9 di `SPECIFICA.md`: **una prova verde su
xfreerdp non dice nulla** se il difetto lo mostra mstsc. La prova va fatta sul client che il difetto lo
mostra.

---

## 19. Il minimo indispensabile per REMOTIX

Messo in fila, ecco cosa va scritto — e cosa no.

### 19.1 Obbligatorio

| Pezzo | Perché |
|---|---|
| X.224 + `RDP_NEG_REQ/RSP` con `PROTOCOL_SSL` | Il collegamento |
| Bandiere `EXTENDED_CLIENT_DATA_SUPPORTED` + `DYNVC_GFX_PROTOCOL_SUPPORTED` nella risposta | Senza, niente monitor e niente EGFX |
| MCS fino a `CHANNEL_JOIN` | Obbligatorio |
| Client Info PDU, con **guardia che parte da negato** | §4.4 |
| Risposta di licenza `STATUS_VALID_CLIENT` | Una riga |
| 13 capability set (§6) | Lo scambio non è saltabile |
| Finalizzazione in otto PDU | Idem |
| drdynvc con frammentazione | Trasporto di tutto il resto |
| EGFX: caps, superficie, map, reset, frame, ack | Il rendering |
| AVC420 con metablock e allineamento 16/64 | Il codec |
| Fastpath input: scancode, unicode, mouse, mousex, sync | I comandi |
| Puntatore: new/large/cached/null | Altrimenti non si vede il mouse |
| `SET_ERROR_INFO` prima di ogni chiusura | §17 |

### 19.2 Subito dopo

MS-RDPEDISP (risoluzione dinamica), autodetect di rete + regolatore a posti-fotogramma, audio in uscita
AAC/PCM, appunti testo e immagini.

### 19.3 Più tardi, o mai

AVC444v2 (quando serve il testo nitido), RemoteFX Progressive (idem, alternativa), MS-RDPEI (tocco),
audio in ingresso, appunti file.

**Mai**: ordini GDI, cache di bitmap/glifi/pennelli, MPPC, cifratura RDP classica, RAIL, dischi,
stampanti, smartcard, UDP, gateway, camera.

### 19.4 Dove sta ciascuna cosa in FreeRDP 3

Il vantaggio del vincolo del 3 agosto: **quasi niente di §19.1 va scritto a mano.**

| Pezzo | API di FreeRDP 3 |
|---|---|
| Peer, connessione, capacità | `freerdp_peer_new`, `peer->Initialize`, ganci `Capabilities`, `PostConnect`, `Activate`, `Logon` |
| Impostazioni | `freerdp_settings_set_*` / `get_*` (`FreeRDP_TlsSecurity`, `FreeRDP_SupportGraphicsPipeline`, …) |
| Ciclo eventi | `peer->GetEventHandles` + `WaitForMultipleObjects` + `peer->CheckFileDescriptor` |
| Canali virtuali | `WTSOpenServerA`, `WTSVirtualChannelManagerCheckFileDescriptor`, `...GetDrdynvcState` |
| EGFX | `rdpgfx_server_context_new` — `CreateSurface`, `MapSurfaceToOutput`, `StartFrame`, `SurfaceCommand`, `EndFrame`, `ResetGraphics`, `CapsConfirm`; ganci `CapsAdvertise`, `FrameAcknowledge` |
| DISP | `disp_server_context_new` — `DisplayControlCaps`, gancio `DispMonitorLayout` |
| Input | `peer->context->input->{KeyboardEvent, UnicodeKeyboardEvent, MouseEvent, ExtendedMouseEvent, RelMouseEvent, SynchronizeEvent}` |
| Scancode → evdev | `GetVirtualKeyCodeFromVirtualScanCode`, `GetKeycodeFromVirtualKeyCode` (WinPR) |
| Autodetect | `peer->context->autodetect`, gancio `OnConnectTimeAutoDetectBegin`, `RTTMeasureRequest`, `BandwidthMeasureStart/Stop` |
| Audio | `rdpsnd_server_context_new` / `audin_server_context_new` |
| Appunti | `cliprdr_server_context_new` |
| Tocco | `rdpei_server_context_new` |
| Codice d'errore | `freerdp_set_error_info` |
| RemoteFX | `rfx_context_new`, `rfx_encode_message` (per Progressive va poi riscritto, §9.4) |
| H.264 | `h264_context_new(TRUE)`, `avc420_compress`, `avc444_compress` — **c'è**, vedi sotto |

> ⛔ **Correzione del 4 agosto 2026.** Questa riga diceva: *«**Niente.** FreeRDP non codifica H.264
> lato server: l'encoder è nostro»*, e ne discendeva *«l'unica cosa grossa che resta da scrivere è il
> codificatore H.264»*. **È falso.** [M, 4 agosto]
>
> | Accertamento | Esito |
> |---|---|
> | `avc420_compress`, `avc444_compress` | **API pubbliche** (`FREERDP_API` in `codec/h264.h`), esportate da `libfreerdp3.so.3` su Debian Trixie |
> | Chi le usa | lo **shadow server di FreeRDP** stesso (`server/shadow/shadow_client.c`) |
> | Backend compilati su Debian | `libx264` e `libavcodec` linkati; presente anche `h264_vaapi` |
> | Prova sul campo | `freerdp-shadow-cli3` 3.15 ha prodotto fotogrammi **AVC420 su EGFX** decodificati da un client FreeRDP — è il banco della misura B, `REFERENCE.md` R5 |
>
> **E il controllo del bitrate c'è**, contro quanto lascia intendere `gnome-remote-desktop.md` §9.1:
> `H264_CONTEXT_OPTION_RATECONTROL` (`H264_RATECONTROL_VBR` o `CQP`), `..._BITRATE`, `..._FRAMERATE`,
> `..._QP`, più il tipo d'uso `H264_SCREEN_CONTENT_REAL_TIME` (dalla 3.6.0). Quel paragrafo resta vero
> su *`gnome-remote-desktop`*, che sceglie CQP a QP 22 e non regola nulla — ma non su FreeRDP.
>
> **Cosa cambia**: la fase 2 non deve scrivere un codificatore, deve **configurarne uno**; e la
> taratura della qualità (**fase 10**, ex 7b) non parte da zero sul punto di lavoro dei 10 Mbps,
> parte da VBR con un bitrate dichiarato. Resta da
> verificare quali backend siano compilati sulla macchina di runtime e quanto valga la resa di
> `avc420_compress` rispetto a `libavcodec` chiamata da noi — §3.1 di `SPECIFICA.md` sceglie
> `libavcodec` per poter cambiare codificatore per nome a runtime, e quella ragione **regge ancora**.

---

## 20. I sette errori che costano di più

Raccolti da questo studio, da `SPECIFICA.md` §5.4/§5.7 e dal riferimento. Nessuno dà un messaggio
d'errore leggibile: tutti danno **schermo nero, disconnessione, o un'immagine sbagliata**.

1. **Creare la superficie e non mapparla all'uscita.** FreeRDP e Android disegnano lo stesso; mstsc no.
2. **Elenco delle versioni EGFX incompleto**, o senza la variante errata della 10.6. Si ripiega su una
   versione dove AVC è spento, e non parte un fotogramma.
3. **Allineamento sbagliato** — larghezza ×16, altezza **×64**. Rinegoziazione e disconnessione.
4. **Convenzione dei bordi confusa** — esclusiva sulle regioni, inclusiva sui `MONITOR_DEF`.
5. **`ResetGraphics` con l'elenco dei monitor vuoto.** Immagine spostata.
6. **Ridimensionare con un Deactivate All** invece che ridichiarando la tela. Alcuni client non
   rinegoziano più EGFX per il resto della sessione.
7. **Applicare un `MONITOR_LAYOUT` arrivato prima della negoziazione di EGFX.** Ricade nel 6.

A cui si aggiunge, sul lato non grafico:

8. **Non mandare `SET_ERROR_INFO` prima di chiudere.** Il client dà «errore di rete» e l'utente non sa
   se è caduta la linea o se l'ha fatto lui.
