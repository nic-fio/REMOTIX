# S1 — L'eccezione di certificato copre la sessione WebTransport?

*9 agosto 2026.*

**La domanda:** l'eccezione che l'utente concede a un certificato autofirmato quando carica la
pagina (TCP/TLS su 7447) copre anche la sessione WebTransport (HTTP/3, UDP 7447) verso lo stesso
host e la stessa porta?

**Marcature** (`CODER.md` §5): **[S]** letto in una specifica o documentazione, con URL · **[R]**
letto nel codice sorgente di un progetto di riferimento, con file e riga · **[?]** ipotizzato o
dedotto · **[✗]** verificata assente, con il controllo positivo dichiarato.
⛔ *In questo rapporto non c'è nessuna riga `[M]`: nulla è stato misurato. Il §4 dice come si misura.*

**Provenienza dei sorgenti citati** — scaricati il 9 agosto 2026 dai mirror ufficiali:
`chromium/chromium@main` (`https://raw.githubusercontent.com/chromium/chromium/main/…`),
`mozilla/gecko-dev@master`, `google/quiche@main`. I numeri di riga sono quelli di quei file a
quella data.

**Versioni di riferimento** — Chrome stabile Linux **151.0.7922.108** (rilasciata il 5 agosto 2026,
`chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Linux`) [S] · Firefox stabile
**153.0.3**, ESR **140.13.0** (`product-details.mozilla.org/1.0/firefox_versions.json`) [S] ·
Safari: WebTransport dichiarato da **26.4** nei dati di compatibilità MDN [S].

---

## 1. La risposta in cinque righe

1. **No, non copre — e la ragione è diversa nei due motori, ma la conseguenza è la stessa.**
2. **Chrome/Edge:** l'eccezione vive nel processo browser (`SSLHostStateDelegate`) ed è consultata
   *soltanto* sul percorso `URLRequest` → `SSLManager::OnCertError`; il client WebTransport sta in
   `net/` e non la interroga mai — non esiste nemmeno il canale IPC per chiederlo. In più, il QUIC
   di Chrome pretende una **radice nota** (built-in): un autofirmato fallisce con
   `ERR_QUIC_CERT_ROOT_NOT_KNOWN` **anche se l'hai importato nel magazzino di sistema**. [R]
3. **Firefox:** l'eccezione *è* consultata anche su HTTP/3 (stesso hook di verifica del TCP), ma
   subito dopo `Http3Session::Authenticated` spegne HTTP/3 quando la radice non è incorporata —
   pref `network.http.http3.disable_when_third_party_roots_found`, **default `true`**. Esito
   pratico: no. [R]
4. **Safari (26.4+) è l'unico che potrebbe dire di sì**, perché la sua «eccezione» non è un
   aggiramento interno al browser ma un certificato messo nel **portachiavi**, e la sua WebTransport
   passa dallo stesso `SecTrust` del sistema. Ipotesi non documentata da nessuno: **è la prima cosa
   da misurare** (§3.3).
5. **La strada che funziona su tutti e tre i motori è una sola: `serverCertificateHashes`** —
   certificato ECDSA (mai RSA), validità **≤ 14 giorni**, impronta SHA-256 del DER servita dalla
   pagina. Chrome dal 100, Firefox dal 125, Safari dal 26.4. Il prodotto va disegnato su questo.

---

## 2. La matrice per browser

| Motore / browser | Versione | L'eccezione TCP copre la WebTransport? | Perché | `serverCertificateHashes` | Marca |
|---|---|---|---|---|---|
| **Blink** — Chrome, Edge desktop | Chrome 151 (ago 2026) | **No** | `SSLHostStateDelegate` non è sul percorso QUIC; e serve una **radice nota** | **Sì**, da Chrome 100 | [R]+[S] |
| **Blink** — Chrome Android | 151 | **No** | stesso `net/`, stesso `services/network/` | Sì | [R]+[?] |
| **Gecko** — Firefox desktop | 153 / ESR 140 | **No, in pratica** | l'override *è* letto, poi h3 viene spento perché la radice non è incorporata | **Sì**, da Firefox 125 | [R] |
| **Gecko** — Firefox Android | 153 | **No** | stesso codice Gecko | Sì | [R]+[?] |
| **WebKit** — Safari macOS | 26.4+ | **forse sì — da misurare** | l'eccezione va nel **portachiavi**, e la WebTransport usa `SecTrustEvaluateAsyncWithError` | **Sì**, da 26.4 | [R]+[?] |
| **WebKit** — Safari iOS/iPadOS | 26.4+ | **da misurare**; ignoto persino se l'eccezione si possa concedere | Apple non documenta il caso su iOS | Sì | [?] |
| Chrome / Firefox **su iOS** | qualunque | = riga Safari | su iOS il motore è WebKit | = Safari | [?] |

Fuori matrice, ma decisivo quanto la matrice: **su Chrome, dietro un'eccezione, il Service Worker
non si installa** — il recupero dello script rifiuta qualunque errore di certificato senza
consultare l'eccezione (§3.9). Non è S1, ma cambia la forma del client tanto quanto.

Fonte delle versioni delle funzionalità: `mdn/browser-compat-data@main`, `api/WebTransport.json` —
`WebTransport` chrome 97 / firefox 114 / safari 26.4; opzione `serverCertificateHashes`
chrome 100 / firefox 125 / safari 26.4 [S].

---

## 3. Il dettaglio, domanda per domanda

### 3.1 Chrome/Edge — dove vive l'eccezione, e perché il QUIC non la vede

**Dove vive.** L'eccezione dell'utente è registrata dal *processo browser*:
`SSLManager::OnCertErrorInternal` chiama il contorno di UI, e alla risposta positiva
`OnAllowCertificate` esegue
`state_delegate->AllowCert(handler->request_url().GetHost(), …)`
(`content/browser/ssl/ssl_manager.cc:76`, `:348`). [R]

**Come è indicizzata.** `StatefulSSLHostStateDelegate` costruisce la chiave con
`GURL GetSecureGURLForHost(host) { return GURL("https://" + host); }`
(`components/security_interstitials/content/stateful_ssl_host_state_delegate.cc:60-63`):
**solo l'host, senza porta**. Il valore memorizzato è la coppia (impronta del certificato, codice
d'errore). Scadenza: `kCertErrorBypassExpirationInSeconds = 604800` — **una settimana**
(`:43`, con il commento *«Certificate error bypasses are remembered for one week»*). [R]

> ⚠ **Conseguenza già decisiva per il prodotto:** l'eccezione di Chrome è legata all'**impronta**
> del certificato e dura **7 giorni**. Un certificato che ruota ogni 14 giorni farebbe ricomparire
> l'avviso a ogni rotazione. Il certificato della **pagina** deve essere longevo e stabile; quello
> della **WebTransport** è un altro oggetto (§5). [R]+[?]

**Chi la consulta.** Un solo punto: `SSLManager::OnCertError`
(`content/browser/ssl/ssl_manager.cc:285-313`), che chiama
`ssl_host_state_delegate_->QueryPolicy(host, cert, cert_error, …)` e, se la risposta è `ALLOWED`,
fa `handler->ContinueRequest()`. Quel percorso è alimentato dagli errori di certificato di una
`URLRequest`: `URLLoader::OnSSLCertificateError`
(`services/network/url_loader.cc:1119`) inoltra al `URLLoaderNetworkServiceObserver`, che li porta
nel processo browser. [R]

**Il percorso WebTransport non passa di lì.** Il client è
`net::DedicatedWebTransportHttp3Client`; il verificatore glielo costruisce `CreateProofVerifier`
(`net/quic/dedicated_web_transport_http3_client.cc:92-120`):

- se **non** ci sono impronte, usa `ProofVerifierChromium` con un insieme
  `hostnames_to_allow_unknown_roots` che nasce **solo** dai parametri QUIC di riga di comando
  (`origins_to_force_quic_on`, `force_quic_everywhere`, `webtransport_developer_mode`) — `:96-108`;
- se ci sono impronte, usa `ChromiumWebTransportFingerprintProofVerifier` — `:110-120`.

In nessuno dei due rami compare l'eccezione dell'utente.

**[✗] Verificata assente, con controllo positivo.** Il canale IPC fra il servizio di rete e il
processo browser per la WebTransport è `WebTransportHandshakeClient`
(`services/network/public/mojom/web_transport.mojom:233-249`): ha `OnBeforeConnect`,
`OnConnectionEstablished`, `OnHandshakeFailed(WebTransportError?)` — e **nient'altro**. Non esiste
un `OnCertificateError` con richiamo che permetta al browser di dire «l'utente ha già accettato,
prosegui».
*Controllo positivo:* lo stesso `grep -n "OnSSLCertificateError"` eseguito su
`services/network/url_loader.cc` trova la riga 1119, dove quel meccanismo **c'è** per le
`URLRequest`. Lo strumento sa trovare il metodo quando esiste; su `web_transport.mojom` non c'è. [✗]

**E c'è un secondo muro, indipendente dal primo.** Anche con il certificato *perfettamente valido*
per il sistema operativo (CA privata importata nel magazzino), `ProofVerifierChromium` aggiunge:

```
if (result == OK &&
    !verify_details_->cert_verify_result.is_issued_by_known_root &&
    !ShouldAllowUnknownRootForHost(hostname_)) {
  result = ERR_QUIC_CERT_ROOT_NOT_KNOWN;
}
```
(`net/quic/crypto/proof_verifier_chromium.cc:428-431`; `ShouldAllowUnknownRootForHost` a `:382-389`). [R]

`is_issued_by_known_root` è vero solo per le radici **incorporate** in Chrome, non per quelle
aggiunte localmente. L'unica scappatoia documentata è un interruttore di riga di comando:
`NETWORK_SWITCH(kWebTransportDeveloperMode, "webtransport-developer-mode")`, commentato
*«Disables known-root checks for outgoing WebTransport connections»*
(`components/network_session_configurator/common/network_switch_list.h:39-40`, letto in
`components/network_session_configurator/browser/network_session_configurator.cc:826-827`). [R]
Un interruttore di riga di comando non è un prodotto per l'utente finale.

Nota di completezza: `--ignore-certificate-errors-spki-list` **non** basta da solo, perché
`IgnoreErrorsCertVerifier::Verify` fa `verify_result->Reset()` e non marca la radice come nota
(`services/network/ignore_errors_cert_verifier.cc:83-91`) — resta quindi
`ERR_QUIC_CERT_ROOT_NOT_KNOWN`. [R]+[?]

### 3.2 Firefox — l'eccezione è letta, e poi HTTP/3 viene spento lo stesso

**Dove vive l'eccezione.** `nsICertOverrideService`, indicizzata per **host + porta + certificato**:
`overrideService->HasMatchingOverride(aHostName, aPort, aOriginAttributes, aCert, &isTemporaryOverride, &haveOverride)`
(`security/manager/ssl/SSLServerCertVerification.cpp:695`; se c'è, la funzione restituisce `0`,
cioè «nessun errore», a `:702-707`). [R]

**Chi la consulta su HTTP/3.** `Http3Session::CallCertVerification`
(`netwerk/protocol/http/Http3Session.cpp:2232`) chiama
`psm::AuthCertificateHookWithInfo(...)` a `:2291` — **lo stesso hook del TLS su TCP**. Quindi, a
differenza di Chrome, **l'override viene davvero consultato anche per QUIC**. [R]

**E però.** Subito dopo, `Http3Session::Authenticated`
(`netwerk/protocol/http/Http3Session.cpp:2303-2340`):

```
} else if (StaticPrefs::network_http_http3_disable_when_third_party_roots_found()) {
    bool hasThirdPartyRoots = … : !mSocketControl->IsBuiltCertChainRootBuiltInRoot();
    // If serverCertificateHashes is used a thirdPartyRoot is legal
    if (hasThirdPartyRoots && !aServCertHashesSucceeded) {
      if (mFirstHttpTransaction) { mFirstHttpTransaction->DisableHttp3(false); }
      mUdpConn->CloseTransaction(this, NS_ERROR_NET_RESET);
      return;
    }
}
```

Il default della preferenza è `true`:
`- name: network.http.http3.disable_when_third_party_roots_found / type: RelaxedAtomicBool / value: true`
(`modules/libpref/init/StaticPrefList.yaml:15090-15092`). [R]

Un certificato autofirmato — o firmato da una CA nostra — non ha radice incorporata, dunque
`hasThirdPartyRoots` è vero, dunque la sessione HTTP/3 viene chiusa con `NS_ERROR_NET_RESET`
**a meno che** l'autenticazione sia avvenuta per impronta. Il commento nel codice lo dice esplicito:
*«If serverCertificateHashes is used a thirdPartyRoot is legal»*. [R]

**Dedotto [?]:** l'eccezione, da sola, non fa funzionare la WebTransport su Firefox; e la leva per
farla funzionare (`network.http.http3.disable_when_third_party_roots_found = false` in
`about:config`) è una configurazione manuale, non un prodotto.

### 3.3 Safari / WebKit — l'unico motore dove la risposta potrebbe essere «sì»

**WebTransport c'è, da Safari 26.4 (24 marzo 2026).** [S]
Il blog WebKit: *«Safari 26.4 adds support for WebTransport… It runs over HTTP/3 and QUIC…
**When the underlying network environment doesn't support QUIC, WebTransport can run over HTTP/2
and TCP as a fallback with the same API.**»*
(https://webkit.org/blog/17862/webkit-features-for-safari-26-4/).
*Controllo positivo:* il post di Safari 26.0 (giugno 2025) non nomina WebTransport
(https://webkit.org/blog/17333/webkit-features-in-safari-26-0/) — la finestra di introduzione è
davvero 26.0→26.4, e la ricerca sa distinguere presenza da assenza. [S]

> ⚠ **Safari ha il ripiego su HTTP/2/TCP, gli altri no.** È l'unico motore che implementa
> WebTransport anche su HTTP/2. Per noi significa che su Safari un fallimento di QUIC **non** è
> necessariamente la fine: il browser proverà TCP. Ma il nostro server non parla WebTransport su
> HTTP/2, quindi il ripiego finirebbe comunque in errore. **Va deciso** se implementarlo
> (`draft-ietf-webtrans-http2`) o dichiarare Safari fuori dal ripiego. [S]+[?]

**Il flag è acceso di default.** `Source/WebKit/Shared/WebPreferencesDefaultValues.cpp:540-547`:
`defaultWebTransportEnabled()` restituisce `true` se `HAVE(WEBTRANSPORT)`. L'IDL
(`Source/WebCore/Modules/webtransport/WebTransport.idl`) è `[EnabledBySetting=WebTransportEnabled,
SecureContext]`. [R]

**`serverCertificateHashes`: la posizione di WebKit è cambiata — chi cita il rifiuto usa un dato
scaduto.** La cronologia, verificata: [S]
- **3 dicembre 2024** — Anne van Kesteren (Apple) apre w3c/webtransport#623 *Consider removing
  serverCertificateHashes* e scrive: *«As things stand today WebKit does not intend to implement
  this.»*
- **20 maggio 2025** — Eric Kinnear (Apple) chiude la discussione: *«Chatting a bit more with
  @annevk and other WebKit folks… we have no objection to implementing, as well. From that
  perspective, we'd like to recommend closing this issue with no action — keeping
  serverCertificateHashes in the spec.»* L'issue è chiusa senza rimuovere nulla dalla specifica.
- **2 ottobre 2025** — WebKit **implementa** la funzionalità, bug 300057 *Implement
  WebTransportOptions.serverCertificateHashes*, `RESOLVED FIXED`
  (https://bugs.webkit.org/show_bug.cgi?id=300057). [R]

L'implementazione sta in
`Source/WebKit/NetworkProcess/webtransport/cocoa/NetworkTransportSessionCocoa.mm`: [R]
- `:77` `leafCertificateMatchesWebTransportHash(sec_trust_t, const Vector<WebTransportHash>&)` —
  SHA-256 del foglia, e il limite di **due settimane** di validità come da specifica;
- `:126-129` in `didReceiveServerTrustChallenge(...)`: se l'elenco di impronte **non** è vuoto, la
  verifica PKI di sistema viene **saltata** e conta solo il confronto delle impronte;
- `:222` le impronte arrivate da JavaScript vengono propagate nella configurazione TLS/QUIC.

E l'IDL le espone: `Source/WebCore/Modules/webtransport/WebTransportOptions.idl`,
`sequence<WebTransportHash> serverCertificateHashes = [];` [R]

**L'indizio che rende Safari diverso da tutti.** Quando le impronte **non** ci sono,
`NetworkTransportSessionCocoa.mm:126-160` costruisce un `NSURLAuthenticationChallenge` con
`NSURLAuthenticationMethodServerTrust` e chiama `SecTrustEvaluateAsyncWithError` — cioè **il motore
di fiducia del sistema**, lo stesso di una normale sfida TLS su HTTPS. [R]
E l'«eccezione» di Safari, a differenza di Chrome e Firefox, **non è un aggiramento interno al
browser**: è un certificato che finisce nel **portachiavi**. La guida Apple lo dice:
*«The certificate is stored on your computer. You can change the trust settings of the certificate
later using Keychain Access.»*
(https://support.apple.com/guide/safari/avoid-fraud-by-using-encrypted-websites-sfri40697/mac) [S]

**[?] Ipotesi, non fatto:** su Safari macOS l'eccezione **potrebbe davvero coprire** la
WebTransport, perché entrambe passano da `SecTrust` e il portachiavi è comune. Non ho trovato
nessuna dichiarazione, nessun test e nessun bug che lo confermi o lo smentisca —
*controllo positivo:* la ricerca ha trovato la discussione pertinente su certificati e WebTransport
(w3c/webtransport#508, *Confirm behaviour of server certificates*), quindi il metodo trova cose in
quel dominio; semplicemente questo punto non è trattato da nessuna parte. **È la cosa più
interessante da misurare per prima su Mac** (§4).

**HTTP/3 e `Alt-Svc` in Safari.** HTTP/3 sperimentale da Safari 14 (novembre 2020,
https://webkit.org/blog/11340/new-webkit-features-in-safari-14/) [S]; acceso di default da Safari 16
secondo fonti secondarie convergenti, **non** confermato da un post ufficiale WebKit [?].
Safari usa `Alt-Svc`, ma con una particolarità: la cache dura **24 ore** e il passaggio a QUIC si
vede solo alla visita successiva; in alternativa Safari usa il record **DNS HTTPS (SVCB)** con
`alpn="h3"` per passare a QUIC già al primo accesso — Geoff Huston (APNIC), IEPG a IETF 123, luglio
2025, https://www.iepg.org/2025-07-20-ietf123/slides-123-iepg-sessa-quic-safari-https-and-the-dns-01.pdf [S].
Per REMOTIX resta irrilevante (§3.4): la WebTransport non nasce da `Alt-Svc`.

### 3.4 `Alt-Svc`: non c'entra con RCP — e questo è una buona notizia

**[✗] WebTransport non usa `Alt-Svc`.** La stringa `Alt-Svc` compare **zero** volte in
`draft-ietf-webtrans-http3-13`, **zero** volte in RFC 9297 (*HTTP Datagrams*) e **zero** volte
nella specifica W3C WebTransport.
*Controllo positivo:* nello stesso `draft-ietf-webtrans-http3-13` la stringa `SETTINGS` compare
**50** volte — il metodo di ricerca funziona su quei file. [✗]

Il client apre **direttamente** una connessione QUIC verso host e porta dell'URL
(`new WebTransport("https://192.168.0.2:7447/rcp")` ⇒ QUIC su UDP 7447), negozia
`SETTINGS_ENABLE_WEBTRANSPORT` e manda un CONNECT esteso
(draft §3.1). Nessuna promozione da TCP, nessun `Alt-Svc`, nessuna intesa con la connessione della
pagina. [S]

**Che cosa succede invece alla *pagina*, se le mettiamo `Alt-Svc: h3=":7447"`.** Chrome avvia due
lavori in parallelo (`main_job_` su TCP, `alternative_job_` su QUIC). Se quello QUIC fallisce e
c'è ancora un altro lavoro vivo, il fallimento viene **ignorato in silenzio**:

```
if (GetJobCount() >= 2) {
  // Hey, we've got other jobs! Maybe one of them will succeed, let's just ignore this failure.
  … alternative_job_.reset(); return;
}
```
(`net/http/http_stream_factory_job_controller.cc:460-471`), e poi
`MaybeReportBrokenAlternativeService` → `MarkAlternativeServiceBroken` (`:1257-1301`) segna il
servizio come rotto, così i tentativi successivi non si ripetono. [R]

**Conseguenza per noi [?]:** il ripiego silenzioso su TCP riguarda **solo la pagina**, e per la
pagina va benissimo. RCP non ci passa. Quindi `Alt-Svc` è, per REMOTIX, un'ottimizzazione
rinunciabile: se h3 non parte per la pagina, non ce ne accorgiamo e non ci perdiamo niente.
La domanda «e se il salto a h3 fallisce in silenzio?», che sarebbe stata fatale, **non si applica**
perché la WebTransport non nasce da un salto.

### 3.5 `serverCertificateHashes`: i vincoli esatti, oggi

**La specifica W3C** (`https://w3c.github.io/webtransport/`, §6.9 e §14.4) [S]:

- *«This option is only supported for transports using dedicated connections. For transport
  protocols that do not support this feature, having this field non-empty SHALL result in a
  `NotSupportedError` exception being thrown.»*
- *«If supported and non-empty, the user agent SHALL deem a server certificate trusted **if and only
  if** it can successfully verify a certificate hash against `serverCertificateHashes` and
  satisfies custom certificate requirements.»* — cioè **sostituisce** la verifica della catena, non
  si aggiunge ad essa. E, di conseguenza, **non c'è verifica del nome**: il certificato della
  WebTransport non ha bisogno del SAN con l'indirizzo IP.
- *«This cannot be used with `allowPooling`.»*
- Requisiti del certificato: *«the certificate MUST be an X.509v3 certificate …, the key used in the
  Subject Public Key field MUST be one of the allowed public key algorithms, the current time MUST
  be within the validity period … and the total length of the validity period **MUST NOT exceed two
  weeks**. The user agent MAY impose additional implementation-defined requirements.»*
- Algoritmi di chiave: *«… MUST include ECDSA with the secp256r1 (NIST P-256) named group … to
  provide an interoperable default. It **MUST NOT** contain RSA keys.»*
- Impronta: solo `"sha-256"`, sul **DER del certificato foglia**; le impronte con algoritmo
  sconosciuto vanno ignorate (§6.9, algoritmi *compute a certificate hash* / *verify a certificate
  hash*).

**Chrome** — implementato in `quiche` più una stretta di Chromium: [R]

| Vincolo | Dove |
|---|---|
| validità massima **14 giorni** (+1 s di tolleranza) | `net/quic/dedicated_web_transport_http3_client.cc:43` (`kCustomCertificateMaxValidityDays = 14`), applicata in `quiche/quic/core/crypto/web_transport_fingerprint_proof_verifier.cc:218-227` |
| solo `sha-256`, formato esadecimale con `:` | stesso file, `:69-107` e `:202-216` |
| **RSA rifiutata** | `dedicated_web_transport_http3_client.cc:82-89` (sovrascrive la politica permissiva di quiche a `:236-251`) |
| ammessi P-256, P-384, Ed25519 | `web_transport_fingerprint_proof_verifier.cc:241-244` |
| **nessuna** verifica del nome host | `VerifyCertChain(const std::string& /*hostname*/, …)` — il parametro è anonimo, `:139-195` |
| l'URL deve essere `https:` | `third_party/blink/renderer/modules/webtransport/web_transport.cc:1488` |
| `allowPooling` non è nemmeno implementato in Chrome | `mdn/browser-compat-data`, `options_allowPooling_parameter`: chrome `false` [S] |

**Firefox** — `netwerk/protocol/http/WebTransportCertificateVerifier.cpp`: [R]

| Vincolo | Dove |
|---|---|
| validità massima **14 giorni** | `:236-237` (`certDuration > Duration(60*60*24*14)` ⇒ `ERROR_VALIDITY_TOO_LONG`) |
| **RSA rifiutata**, con commento esplicito | `:114-122` (*«RSA is not supported for serverCertificateHashes … we do not support it»*) |
| qualunque curva ECDSA accettata | `:140-145` (`CheckECDSACurveIsAcceptable` ⇒ `Success`) |
| solo `"sha-256"` | `:265` |
| sostituisce la catena (non si aggiunge) | `Http3Session::CallCertVerification` a `:2244-2266`: se le impronte tornano bene, chiama `Authenticated(0, true)` e **ritorna**, senza `AuthCertificateHookWithInfo` |
| 0-RTT disattivato quando ci sono impronte | `Http3Session.cpp:221` |

Storia: la prima implementazione (bug 1806693) trattava le impronte come un controllo **in più**,
non come sostituto — quindi un autofirmato veniva comunque respinto. Il bug **1873263** è
`RESOLVED FIXED`, *target milestone Firefox 125*
(`https://bugzilla.mozilla.org/show_bug.cgi?id=1873263`) [S]. Coincide con il dato di
compatibilità MDN (`serverCertificateHashes`: firefox 125).

**Contesto sicuro.** `WebTransport` è `[SecureContext]` nella IDL della specifica [S]: la **pagina**
deve stare in un contesto sicuro. Se una pagina caricata *con eccezione* conti come contesto sicuro
è la domanda del §3.9.

**Local Network Access (Chrome 147+).** I dati MDN segnano `api.WebTransport.local_network_access`
= chrome 147 [S]. La specifica: *«A request is a local network request if request's current url's
host maps to an IP address whose IP address space is **less public than** request's policy
container's IP address space»* (`https://wicg.github.io/local-network-access/` §2.2) [S].
**[?]** Se la pagina è servita da `192.168.0.2` il suo spazio è già *local*, e una WebTransport
verso `192.168.0.2` non è *less public*: quindi niente richiesta di permesso. Il caso che invece
scatta è la pagina servita da un indirizzo pubblico che apre una WebTransport verso un IP privato —
uno scenario che REMOTIX non ha. **Va comunque confermato al banco** (§4, passo 7).

### 3.6 Che cosa serve al certificato perché il browser offra «prosegui»

- **Il SAN con l'indirizzo IP è obbligatorio, e deve essere di tipo `iPAddress`.** Chrome, per un
  host che *è* un indirizzo IP, confronta **solo** i SAN `iPAddress`:
  `if (host_info.IsIPAddress()) { return std::ranges::contains(cert_san_ip_addrs, …); }`
  (`net/cert/x509_certificate.cc:465-468`); e se non c'è nessun SAN fallisce subito
  (`:444-448`, *«Either a dNSName or iPAddress subjectAltName MUST be present»*). Il `CN` non viene
  mai guardato. Un SAN `DNS:192.168.0.2` **non** vale. [R]
- **La regola dei 398 giorni non ci riguarda.** `HasTooLongValidity` è invocata solo se
  `verify_result->is_issued_by_known_root` (`net/cert/cert_verify_proc.cc:533`); lo stesso vale per
  il rifiuto dei nomi non unici (`:545`). Un autofirmato non ha radice nota, quindi non incontra né
  il limite di durata né il divieto sui nomi non unici. Per curiosità, il limite attuale per i
  certificati pubblici è sceso: **200 giorni** per quelli emessi dal 15 marzo 2026, 100 dal 15 marzo
  2027, 47 dal 15 marzo 2029 (`net/cert/cert_verify_proc.cc:767-835`). [R]
- **Quando il browser *non* offre di proseguire.** In Chrome dipende da
  `TransportSecurityState::ShouldSSLErrorsBeFatal(hostname)` — HSTS o *pinning* statico rendono
  l'errore fatale (`net/quic/crypto/proof_verifier_chromium.cc:433-436` per il ramo QUIC; la stessa
  nozione governa l'interstiziale). In Firefox la regola è scritta in chiaro:
  `OverrideAllowedForHost` restituisce `aOverrideAllowed = !strictTransportSecurityEnabled &&
  !isStaticallyPinned`, con l'annotazione che **un indirizzo IP non può essere un host HSTS**
  (`security/manager/ssl/SSLServerCertVerification.cpp:310-374`). [R]
  **[?]** Poiché serviamo su un indirizzo IP, HSTS non può esistere per quell'host: il pulsante
  «prosegui» ci sarà sempre, su Chrome e Firefox.
- **Tipo di chiave della pagina:** nessun vincolo imposto dal browser per un autofirmato oltre a
  quelli generali di TLS. ECDSA P-256 è comunque la scelta sensata perché è l'unica obbligatoria
  *anche* per il ramo `serverCertificateHashes`. [?]

### 3.7 Safari e iOS: si può accettare, e per quanto tempo

**macOS — sì, ed è persistente.** La guida Apple, sezione *Respond to a certificate warning*:
*«Click Show Certificate, then review the certificate content… If you continue to the website,
verify the address in the Safari toolbar… **The certificate is stored on your computer. You can
change the trust settings of the certificate later using Keychain Access.**»*
(https://support.apple.com/guide/safari/avoid-fraud-by-using-encrypted-websites-sfri40697/mac) [S]
Non è quindi un'eccezione «di sessione» come si legge in giro: è una **modifica al portachiavi**.
Il meccanismo sottostante è `SecTrustSettingsSetTrustSettings` a livello `.user`, come descritto da
un ingegnere Apple DTS (https://developer.apple.com/forums/thread/658149) [?].
La documentazione attuale **non** riporta più l'etichetta esatta del pulsante («Visita comunque
questo sito web»): il comportamento è confermato, la stringa no. [S]/[?]

**iOS / iPadOS — non documentato da Apple. È un «non trovato», non un «verificato assente».**
*Controllo positivo dichiarato:* la pagina equivalente per Mac esiste ed è esplicita (sopra); la
pagina corrispondente per iPhone
(https://support.apple.com/guide/iphone/digital-certificates-and-encrypted-websites-iph1b914c6d4/ios)
è stata letta per intero e **non contiene** alcuna sezione «Respond to a certificate warning»: dice
soltanto *«Safari checks if the site's certificate is legitimate. If it's not, Safari warns you»*,
senza pulsanti, senza opzioni, senza una parola sulla persistenza. Quindi: l'assenza nella
documentazione è verificata; il **comportamento** resta ignoto. [S]+[?]
Fonti terze descrivono per iOS lo stesso percorso di macOS (*Show Details* → *visit this website* →
*Visit Website*), ma con l'avvertenza, nelle fonti stesse, che l'opzione potrebbe non esserci più
nelle versioni recenti: dato **non verificato** per Safari 26.x. [?]

**Quando Safari non offre affatto di proseguire.** Fonti community (Apple Community, Jamf)
riportano che l'avviso *«This Connection Is Not Private»* compare **senza** possibilità di
continuare quando il problema non è la fiducia nel certificato ma il protocollo: TLS troppo vecchio
(≤ 1.1) o connessione in chiaro. Per il caso «certificato autofirmato» l'opzione risulta
generalmente presente. Fonte di qualità bassa, marcata [?].

**Sequenza da misurare su iPhone**, e va misurata prima di promettere qualsiasi cosa (§4):
(a) l'avviso offre di proseguire? (b) chiudendo e riaprendo Safari, ricompare? (c) dopo il riavvio
del telefono, ricompare? (d) e allora `new WebTransport(...)` funziona? Le quattro risposte insieme
decidono se il telefono è un cliente supportato o no.

### 3.8 Le alternative senza dominio pubblico

#### a) Let's Encrypt con sfida DNS-01, per un nome che risolve a un IP privato — **si può**

[S] La sfida DNS-01 prova solo il controllo del **DNS** (record TXT su `_acme-challenge.<nome>`),
non la raggiungibilità del servizio né l'indirizzo a cui il nome punta: *«it works well even if
your web server isn't reachable from the public internet»*
(https://letsencrypt.org/docs/challenge-types/).
Il divieto delle Baseline Requirements riguarda **ciò che finisce nel certificato**, non ciò che il
DNS restituisce: *«CAs SHALL NOT issue Certificates containing Internal Names or Reserved IP
Addresses»* (`cabforum/servercert`, `docs/BR.md`, riga 1332 —
https://github.com/cabforum/servercert/blob/main/docs/BR.md). Un `casa.esempio.it` è un nome sotto
un TLD registrato IANA: non è un *Internal Name*, e che risolva a `192.168.0.2` è irrilevante. [S]

Prezzo per l'utente: **serve comunque un dominio registrato** (anche gratuito, tipo DuckDNS) e un
provider DNS con API per automatizzare il rinnovo (certbot con plugin `dns-*`, oppure acme.sh,
lego, Caddy). [S]/[?]

**Le durate, aggiornate:** [S] https://letsencrypt.org/2025/12/02/from-90-to-45.html
— profilo `classic` **90 giorni** oggi, 64 dal 10 febbraio 2027, **45** dal 16 febbraio 2028; profilo
opt-in `tlsserver` a 45 giorni dal 13 maggio 2026; profilo `shortlived` **~160 ore (poco più di 6
giorni)**. *(La «regola dei 47 giorni» citata nella domanda è la tabella del CA/Browser Forum lato
browser — Chrome la applica dal 15 marzo 2029, §3.6 — non la durata di Let's Encrypt.)*

#### b) Certificati Let's Encrypt per **indirizzo IP** — esistono, ma non servono a noi

[S] In disponibilità generale dal **15 gennaio 2026**
(https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability.html), dopo il primo
certificato sperimentale del 1° luglio 2025. Ma:
- **solo IP pubblici** — gli esempi sono `54.215.62.21` e `2600:1f1c:446:4900::65`; nessun supporto
  per RFC 1918/ULA, ed è coerente col divieto sui *Reserved IP Address* (BR riga 481, 2948);
- **obbligatoriamente short-lived** (~160 ore);
- validazione solo `http-01` o `tls-alpn-01`: **niente DNS-01 per gli IP**, quindi serve un IP
  pubblico raggiungibile.

**Conclusione:** non risolve lo scenario REMOTIX (IP privato o VPN). [S]

#### c) `.local` / mDNS — **impossibile, per definizione**

[S] BR `docs/BR.md`: *Internal Name* = *«a string of characters (not an IP address) … that cannot be
verified as globally unique within the public DNS … because it does not end with a Top-Level Domain
registered in IANA's Root Zone Database»* (riga 374); il SAN *«MUST NOT contain an Internal Name»*
(riga 2943). `.local` non è un TLD IANA ⇒ nessuna CA pubblica può emettere. Conferma indipendente:
Let's Encrypt rifiuta `localhost` con la stessa motivazione
(https://letsencrypt.org/docs/certificates-for-localhost/). [S]
La data esatta della cessazione delle emissioni (novembre 2015 nella letteratura corrente) non è
stata riverificata su fonte primaria: [?].

#### d) Che cosa fanno, di fatto, i self-hosted con lo stesso problema

| Prodotto | Prassi reale | Marca |
|---|---|---|
| **Plex** | ⭐ Il precedente più vicino al nostro. Ogni server ottiene `1-2-3-4.HASH.plex.direct`; il DNS **pubblico** di Plex risolve quel nome all'**IP privato** codificato nel nome, e Plex emette un certificato **wildcard** `*.HASH.plex.direct`. L'IP non entra mai nel certificato, quindi le BR sono rispettate. CA: oggi Let's Encrypt. Effetto: **zero click** per l'utente. Richiede però che il *venditore* possieda e gestisca un dominio | [S] + [?] sulla conformità dedotta |
| **Home Assistant** (Nabu Casa) | Remote UI con certificato Let's Encrypt gestito dal servizio; proxy TCP che instrada per SNI, la chiave resta sull'istanza locale. Fuori da Nabu Casa: add-on Let's Encrypt + DuckDNS, cioè la via (a) fatta a mano | [S] / [?] |
| **Proxmox VE** | Autofirmato all'installazione, firmato da una **CA per-cluster** (`/etc/pve/pve-root-ca.pem`) che l'utente deve **importare a mano** nel proprio trust store; in alternativa client ACME integrato nella GUI, con DNS-01 per gli homelab non esposti | [S] |
| **Jellyfin** | HTTPS **disattivato di default**; i certificati autofirmati sono *«strongly discouraged»*; si consiglia Let's Encrypt o un reverse proxy. Il problema è interamente scaricato sull'utente | [S] |
| **Syncthing** | Nessuna CA: il **Device ID è lo SHA-256 del certificato** (base32). Fiducia per confronto diretto dell'identificatore — TOFU/pinning, cugino del nostro `serverCertificateHashes`. La GUI web sta di default su HTTP solo da localhost | [S] |
| **Xpra** | Autofirmato generato all'installazione; e la documentazione ammette che portare l'impronta al client HTML5 *«will not be handled by xpra, it simply cannot be»*. Nessun QUIC: TCP/WebSocket | [S] |
| **Nextcloud / Immich** | Autofirmato o reverse proxy con dominio pubblico. Nessuna automazione senza dominio | [S] |

#### e) Chi già usa il pattern «la pagina porta l'impronta»

- **libp2p** — il caso più maturo: due certificati autofirmati **in rotazione** (uno attivo, uno
  «prossimo»), validità 14 giorni, impronta pubblicata dentro il multiaddr
  `/ip4/…/udp/…/quic/webtransport/certhash/<hash>`; in produzione in js-, go- e rust-libp2p
  (https://github.com/libp2p/specs/blob/master/webtransport/README.md) [S].
- **moq-rs / moq** (oggi in orbita Cloudflare) — `rs/moq-native/src/server.rs`, `generate()`
  (`:271-286`) crea una chiave ECDSA con `rcgen` e validità «da ieri a fra 14 giorni»;
  `fingerprints()` (`:288-298`) calcola lo SHA-256; il relay lo serve su `GET /certificate.sha256`
  [R]+[S].
- **`@fails-components/webtransport`** (Node, usata da Socket.IO) — la guida ufficiale dà
  letteralmente il comando `openssl req … -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 …
  -days 14` (https://socket.io/get-started/webtransport) [S].
- **Controllo negativo dichiarato:** nessuna delle fonti esaminate documenta un caso «desktop
  remoto, singolo server domestico» uguale al nostro. Il pattern è solido e standardizzato, ma non
  esiste un prodotto consumer di riferimento da copiare. [S]/[?]

> ⚠ **Una correzione al filone di ricerca, per non tramandare un errore.** La ricerca secondaria
> riportava che «`serverCertificateHashes` funziona in modo affidabile solo su Chrome ad agosto
> 2026, Firefox senza ETA, Safari da decidere». **È falso, e il codice lo smentisce:** Firefox lo ha
> dal 125 (§3.2, `WebTransportCertificateVerifier.cpp`), Safari dal 26.4 (§3.3,
> `NetworkTransportSessionCocoa.mm`). È esattamente il tipo di affermazione — vera nel 2024, ripetuta
> nel 2026 — contro cui vale la regola delle marche.

### 3.9 Contesto sicuro: che cosa cambia con un'eccezione

**La regola formale: sì, è contesto sicuro.** L'algoritmo *«Is origin potentially trustworthy?»*
(https://w3c.github.io/webappsec-secure-contexts/ §3.1) guarda **solo lo schema** e l'host:
*«If origin's scheme is either "https" or "wss", return "Potentially Trustworthy"»*. La validità
del certificato non compare da nessuna parte del documento. Lo spec distingue anzi in modo
esplicito *«authenticated and encrypted in the traditional sense»* da *«potentially trustworthy»*. [S]

E i tre motori lo implementano così: [R]
- Blink — `services/network/public/cpp/is_potentially_trustworthy.cc:281-327`
  (`GURL::SchemeIsCryptographic(origin.scheme())` alla `:295`), richiamato da
  `SecurityOrigin::IsPotentiallyTrustworthy()`
  (`third_party/blink/renderer/platform/weborigin/security_origin.cc:474-482`);
- Gecko — `nsContentUtils::ComputeIsSecureContext` (`dom/base/nsContentUtils.cpp:10738-10768`)
  restituisce `principal->GetIsOriginPotentiallyTrustworthy()`;
- WebKit — `shouldTreatAsPotentiallyTrustworthy` (`Source/WebCore/page/SecurityOrigin.cpp:88-107`).

**Quindi `window.isSecureContext === true`**, e le interfacce marcate `[SecureContext]` restano
esposte: `WebTransport` (`modules/webtransport/web_transport.idl:9`), `Clipboard`
(`modules/clipboard/clipboard.idl:18`), `GPU` (`modules/webgpu/gpu.idl:27`), `VideoDecoder`/
`VideoEncoder` (`modules/webcodecs/video_decoder.idl:12`, `video_encoder.idl:9`), `Keyboard.lock()`
(`modules/keyboard/keyboard.idl`). [R]

**Due delle API che ci servono non sono nemmeno soggette a contesto sicuro:** `requestPointerLock`
(`core/dom/element.idl:143`) e `requestFullscreen` (`core/fullscreen/element_fullscreen.idl`) **non
hanno** l'attributo `[SecureContext]`. La domanda «cambiano con l'eccezione?» per loro non si pone. [R]

#### ⚠ L'eccezione vera, e non è piccola: il **Service Worker** su Chrome

La registrazione passa (`content/common/origin_util.cc:18-32`, solo schema), ma il **recupero dello
script** ha un controllo dedicato e **incondizionato** in
`content/browser/service_worker/service_worker_loader_helpers.cc`, `CheckResponseHead` (~`:174-198`): [R]

```cpp
if (!devtools_instrumentation::ShouldBypassCertificateErrors() &&
    net::IsCertStatusError(response_head.cert_status) &&
    !base::CommandLine::ForCurrentProcess()->HasSwitch(switches::kIgnoreCertificateErrors)) {
  … *out_error_message = ServiceWorkerConsts::kServiceWorkerSSLError; return false;
}
```

con il messaggio *«An SSL certificate error occurred when fetching the script.»*
(`service_worker_consts.h:81-82`). **Non consulta `SSLHostStateDelegate`**: l'eccezione già
concessa dall'utente non serve a niente. Le sole vie d'uscita sono `--ignore-certificate-errors` o
il «bypass» di DevTools. [R]
Coerente: `SSLManager::OnSSLCertificateError` (`content/browser/ssl/ssl_manager.cc:106-145`) porta
il commento *«This handle can be null if the request is from service worker»* e, quando manca il
frame, fa `handler->DenyRequest()` **prima** del ramo che interroga le eccezioni. [R]

Lo specifico dello standard non lo richiede: il ServiceWorker spec pretende solo un'origine
*potentially trustworthy* (https://w3c.github.io/ServiceWorker/) [S]. È una scelta di Chromium, più
severa della specifica. Riscontro esterno coerente: w3c/ServiceWorker#1514 riporta esattamente
quell'errore in Chrome con certificato autofirmato, *«the same setup works without issues in
Firefox»* (https://github.com/w3c/ServiceWorker/issues/1514) [S].

> **Conseguenza per REMOTIX** [?]: se la pagina client vive dietro un'eccezione di certificato,
> **niente Service Worker su Chrome**. Quindi niente installazione come PWA, niente cache offline,
> niente `manifest` che funzioni davvero. Va deciso subito se il client è una pagina semplice — e
> allora nessun problema — o se punta a essere installabile, e allora questa è una seconda ragione,
> indipendente da S1, per volere un certificato fidato.

#### Le altre API: nessun blocco trovato, ma la ricerca non è esaustiva

I permessi (fotocamera, microfono, appunti, notifiche) **non** guardano il certificato:
`components/permissions/permission_context_base.cc:510-524` usa solo
`network::IsUrlPotentiallyTrustworthy`, e la ricerca di `cert_status`/`SSLStatus` in
`permission_context_base.cc` e `permission_util.cc` non trova nulla. [R]
*Controllo positivo dichiarato:* la stessa ricerca, sullo stesso corpus, ha trovato in modo pulito
il controllo `cert_status` del Service Worker (sopra). Quindi l'assenza qui è un'assenza vera, non
un limite del metodo. [✗]

`content::SSLStatus` e i suoi bit (`DISPLAYED_CONTENT_WITH_CERT_ERRORS`,
`RAN_CONTENT_WITH_CERT_ERRORS`, `content/public/browser/ssl_status.h:20-65`) risultano
infrastruttura di **interfaccia e telemetria**: `MixedContentChecker::HandleCertificateError`
(`third_party/blink/renderer/core/loader/mixed_content_checker.cc:1005-1021`) si limita a
notificare il pannello Issues, non blocca. [R]

Per **WebCodecs, WebGPU, Clipboard, WebTransport, Keyboard Lock** non è stato trovato alcun blocco
legato al certificato — ma la ricerca **non è stata esaustiva** e questo resta un **[?]**, non un
[✗]. Su Gecko è stato controllato solo `dom/serviceworkers/` (nessun controllo analogo); su WebKit
solo il livello base di `SecurityOrigin`. **Sono lacune dichiarate**, e sono nella lista del banco
(§4.2, prova P5).

⚠ Nota di igiene, perché è un errore facile: la mixed content non c'entra. La pagina è `https:` e
la WebTransport è `https:`; il fatto che il certificato sia autofirmato non rende «misto» niente.

---

## 4. Il banco: come si misura S1 sul ferro

*Serve un server Debian Trixie, un portatile e un telefono. Nessuno dei passi qui sotto è stato
eseguito: sono istruzioni.*

### 4.0 Che cosa si sta misurando, in una riga

Se, **dopo** aver accettato l'avviso sulla pagina, `new WebTransport("https://IP:7447/rcp").ready`
si risolve oppure viene respinto. Tutto il resto è contorno per non ingannarsi.

### 4.1 Preparare il server

Due certificati, non uno — la distinzione è il cuore della misura.

```bash
IP=192.168.0.2

# A) certificato della PAGINA: longevo e stabile, SAN iPAddress
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -noenc \
  -keyout pagina.key -out pagina.crt -days 3650 \
  -subj "/CN=$IP" -addext "subjectAltName=IP:$IP" \
  -addext "keyUsage=digitalSignature" -addext "extendedKeyUsage=serverAuth"

# B) certificato della WEBTRANSPORT: ECDSA P-256, validità 13 giorni (< 14)
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -noenc \
  -keyout wt.key -out wt.crt -days 13 \
  -subj "/CN=$IP" -addext "subjectAltName=IP:$IP"

# l'impronta da mettere nella pagina: SHA-256 del DER
openssl x509 -in wt.crt -outform der | openssl dgst -sha256 -binary | base64
openssl x509 -in wt.crt -outform der | openssl dgst -sha256   # forma esadecimale, per leggerla
```

Verifica del certificato prima ancora di provarlo (evita mezza giornata persa):

```bash
openssl x509 -in pagina.crt -noout -text | grep -A1 "Subject Alternative Name"
# deve dire  IP Address:192.168.0.2   — se dice  DNS:192.168.0.2  è sbagliato
```

Il server ascolta su TCP 7447 (pagina, certificato A) e su UDP 7447 (HTTP/3 + WebTransport,
certificato B). ⚠ Nessun `Alt-Svc` in questa fase: non serve, e aggiungerlo confonde la lettura.

### 4.2 Le cinque prove, in quest'ordine

La pagina servita deve contenere quattro pulsanti, ognuno che stampa `ready` risolta oppure il
messaggio dell'errore.

| # | Prova | Che cosa si guarda |
|---|---|---|
| **P1** | `new WebTransport("https://IP:7447/rcp")` — **senza** impronte, dopo aver accettato l'avviso sulla pagina | ⇐ **è S1**. `ready` risolta ⇒ «sì copre». Respinta ⇒ «no» |
| **P2** | `new WebTransport(url, {serverCertificateHashes:[{algorithm:"sha-256", value: <impronta di wt.crt>}]})` | **controllo positivo**: deve *riuscire*. Se fallisce anche questo, il banco è rotto (server, porta, firewall), non il browser |
| **P3** | come P2 ma con un'impronta **sbagliata** di un byte | **controllo negativo**: deve *fallire*. Se riesce, il banco non distingue nulla |
| **P4** | come P2 ma con un certificato B rigenerato a `-days 30` e la sua impronta giusta | deve fallire con un errore di *durata*. Conferma che il limite dei 14 giorni è quello vero, e che stiamo leggendo davvero il verdetto del browser |
| **P5** | dalla stessa pagina: `navigator.serviceWorker.register('/sw.js')`, `navigator.keyboard.lock()`, `navigator.clipboard.writeText('x')`, `document.body.requestPointerLock()`, `VideoDecoder.isConfigSupported({codec:'…'})`, e stampare `window.isSecureContext` | chiude il §3.9 nella parte rimasta [?]. Atteso: `isSecureContext === true` ovunque; `register()` **fallisce su Chrome** con *«An SSL certificate error occurred when fetching the script»* e **riesce su Firefox**; il resto funziona. Ogni scostamento da questa attesa è una scoperta, e va scritta |

**Perché P2, P3 e P4 sono obbligatori.** Senza di loro, un fallimento di P1 non distingue «il
browser rifiuta l'eccezione» da «il server non risponde su UDP 7447». P2 dice che il canale c'è;
P3 e P4 dicono che il banco sa anche dire di no. Sono, insieme, la risposta alla domanda «come
apparirebbe il caso opposto?».

### 4.3 Che cosa si guarda, browser per browser

**Chrome/Edge.** `chrome://net-export/` → *Include raw bytes* non serve, basta il livello base →
riprodurre P1 → *Stop* → aprire il file con `https://netlog-viewer.appspot.com/`.
- Se S1 è **no**: si vede una sorgente `WEB_TRANSPORT_CLIENT` che finisce con
  `QUIC_SESSION_CERTIFICATE_VERIFY_FAILED` oppure con errore **-380**
  (`ERR_QUIC_CERT_ROOT_NOT_KNOWN`) o **-358** (`ERR_QUIC_HANDSHAKE_FAILED`).
  I numeri stanno in `net/base/net_error_list.h:859` e `:777` [R].
- Se S1 è **sì**: la stessa sorgente arriva a `QUIC_SESSION_WEBTRANSPORT_CLIENT_STATE_CHANGED`
  con `next_state` `CONNECTED` — l'evento esiste, `dedicated_web_transport_http3_client.cc:122-135` [R].
- **Prova a parte, che vale da sola:** rilanciare Chrome con
  `--webtransport-developer-mode` e ripetere P1. Se P1 fallisce senza l'interruttore e riesce con
  l'interruttore, allora la causa è **esattamente** il controllo della radice nota, e non altro.
  È il controllo che separa la nostra ipotesi da tutte le altre.

**Firefox.**
```bash
MOZ_LOG='nsHttp:5,Http3Session:5' MOZ_LOG_FILE=/tmp/ff.log firefox
```
- Se S1 è **no** per la ragione che diciamo noi, nel registro compare la riga di
  `Http3Session::Authenticated` con `hasThirdPartyRoots=1, servCertHashesSucceeded=0`
  (`Http3Session.cpp:2321-2325`) e la chiusura con `NS_ERROR_NET_RESET` [R].
- **Il controllo che isola la causa:** in `about:config` mettere
  `network.http.http3.disable_when_third_party_roots_found = false` e ripetere P1. Se ora P1
  riesce, la causa è quella preferenza e nient'altro; se continua a fallire, la causa è a monte
  (l'override non è stato applicato) e la nostra lettura del codice va rivista.
- Verificare anche che l'eccezione sia stata davvero registrata: *Impostazioni → Privacy e
  sicurezza → Certificati → Visualizza certificati → Server*, dev'esserci `192.168.0.2:7447`.

**Safari (macOS) e iPhone.** Non c'è un `net-export`. Si usa quello che c'è:
- macOS: *Sviluppo → Mostra Web Inspector → Console*; la promessa `ready` respinta stampa un
  `WebTransportError`. Se serve di più, *Developer → Show Network Requests*.
- iPhone: collegarlo al Mac, *Impostazioni → Safari → Avanzate → Web Inspector*, poi ispezionarlo
  dal Safari del Mac.
- Prima di P1, annotare **come** Safari ha accettato l'eccezione (§3.7) e se, chiudendo e
  riaprendo il browser, l'avviso ricompare: quella è la differenza fra eccezione persistente e di
  sessione, ed è un dato del prodotto quanto S1.
- **Il controllo che isola la causa su macOS**, e che vale il viaggio: dopo aver accettato,
  aprire *Accesso Portachiavi* e verificare che il certificato di `192.168.0.2` **ci sia**, con le
  impostazioni di fiducia modificate. Poi:
  - se P1 **riesce** e il certificato è nel portachiavi ⇒ l'ipotesi del §3.3 è confermata: su Safari
    l'eccezione copre, perché passa dal `SecTrust` di sistema;
  - se P1 **fallisce** benché il certificato sia nel portachiavi ⇒ l'ipotesi è falsa, e WebKit ha un
    controllo suo che non abbiamo trovato: allora va cercato in
    `NetworkTransportSessionCocoa.mm`;
  - se il certificato **non è** nel portachiavi ⇒ l'eccezione di Safari non è quel che credevamo, e
    va rifatto il §3.7 prima di concludere alcunché.
  Le tre uscite sono distinguibili: è questo che rende la prova utile.
- **Su Safari, in più, va provato che cosa succede quando QUIC non parte affatto** (server con UDP
  7447 chiuso nel firewall): il blog WebKit dichiara il ripiego su HTTP/2/TCP (§3.3). Se il
  ripiego esiste davvero, l'errore che si vede sarà quello di un CONNECT rifiutato dal nostro
  server, non un errore di QUIC. È l'unico modo per sapere se dobbiamo prevedere quel percorso.

### 4.4 Il controllo positivo del banco, detto in chiaro

> **Come faccio a sapere che il banco saprebbe accorgersi del fallimento?**
> Perché nello stesso giro, sullo stesso browser, sulla stessa pagina, **P2 riesce e P3 fallisce**.
> Se P2 riuscisse e P3 pure, il banco non sta leggendo il verdetto del browser (per esempio sta
> guardando una promessa sbagliata). Se P2 fallisse, non sto misurando S1: sto misurando un server
> che non risponde. Solo con P2 verde e P3 rosso il risultato di P1 significa qualcosa.
> E il verdetto va scritto **per ciascun** browser e ciascuna versione, non «sul browser».

### 4.5 Errori che rovinano la misura

1. Accettare l'avviso in **navigazione privata** e poi provare P1 in una finestra normale: sono due
   depositi diversi.
2. Riusare lo **stesso** certificato per pagina e WebTransport: se dura più di 14 giorni P2 fallirà
   per un motivo che non c'entra con S1; se dura meno di 14 giorni l'eccezione della pagina scadrà
   in continuazione.
3. Provare con `localhost` o `127.0.0.1`: Chrome ha una corsia riservata per localhost
   (`ssl_manager.cc:290-297`, interruttore `--allow-insecure-localhost`) e la misura non
   rappresenta il caso reale. **Va usato un IP privato di rete**, da una macchina diversa.
4. Lasciare `Alt-Svc` acceso e credere che il fallimento di h3 sulla pagina sia S1: sono due cose
   diverse (§3.4).
5. Non annotare la **versione** esatta del browser. Un risultato senza versione, fra sei mesi, non
   vale niente.

---

## 5. Che cosa decide questa risposta per il prodotto

### Caso «sì, copre» (che oggi il codice dice essere falso su Blink e Gecko)

Il prodotto sarebbe semplice: **un solo certificato**, autofirmato, longevo, con SAN `iPAddress`;
l'utente accetta una volta al primo incontro, il browser ricorda, e la WebTransport parte senza
altro. Nessuna rotazione, nessuna impronta nella pagina, nessun secondo certificato. Il modello
SSH che il progetto ha scelto sarebbe realizzabile alla lettera.

### Caso «no, non copre» — il caso da preparare

**La forma del prodotto cambia, e cambia in un modo preciso:**

1. **Due certificati, con due mestieri diversi.** [?]
   - *Pagina* (TCP 7447): ECDSA P-256, SAN `iPAddress`, **lunga durata** e **impronta stabile** —
     perché l'eccezione di Chrome è indicizzata sull'impronta e dura 7 giorni (§3.1): se ruota,
     l'avviso ricompare a ogni rotazione.
   - *WebTransport* (UDP 7447): ECDSA P-256, **≤ 14 giorni**, ruotato dal server, **senza bisogno
     di SAN** perché il ramo a impronte non verifica il nome (§3.5).
2. **La pagina pubblica l'impronta del certificato B**, e il codice del client la passa a
   `new WebTransport(url, {serverCertificateHashes: […]})`. È la catena di fiducia che tiene tutto:
   *l'utente si fida della pagina (una volta, alla SSH) → la pagina dichiara l'impronta → la
   WebTransport si fida solo di quell'impronta.* Non c'è nessuna impronta da confrontare a mano:
   la decisione dell'utente resta una sola, quella iniziale.
3. **La rotazione diventa un requisito funzionale del server, non un dettaglio.** Il server deve
   generare un nuovo certificato B prima della scadenza, pubblicare **entrambe** le impronte durante
   la sovrapposizione (la specifica permette più impronte proprio per questo, §14.4 [S]), e — punto
   delicato — **la pagina già aperta in un browser ha in mano un'impronta che invecchia**: alla
   riconnessione dopo la rotazione va ricaricata la pagina o richiesta l'impronta corrente. Va
   deciso dove sta questo aggiornamento in RCP.
4. **`allowPooling` è vietato** con le impronte [S]: la WebTransport avrà sempre una connessione
   QUIC dedicata. Nessun risparmio di connessione da inseguire.
5. **Safari, se `serverCertificateHashes` non ci fosse, sarebbe fuori.** L'alternativa a `[S]`
   confermare è la sola via che i tre motori condividono; se un motore non ce l'ha, per quel motore
   non esiste un modo senza dominio pubblico. Vedi §3.7.
6. **La strada «prendiamo un vero certificato» resta aperta e va valutata a parte** (§3.8): se
   l'utente ha un nome di dominio, un certificato pubblico toglie di mezzo *tutto* questo capitolo —
   sia l'avviso, sia le impronte, sia la rotazione a 14 giorni. Ma non si può **richiedere** un
   dominio: lo scenario dichiarato del progetto è «spesso senza nome di dominio».
7. **Niente Service Worker su Chrome** (§3.9): il client resta una pagina, non una PWA
   installabile, e non avrà cache offline. Se questo è inaccettabile, il certificato fidato smette
   di essere un'ottimizzazione e diventa un requisito.
8. **Safari va trattato a parte finché non si misura**: se l'ipotesi del §3.3 regge, su Mac e
   iPhone potremmo persino non aver bisogno delle impronte — ma non si progetta su un'ipotesi. Il
   codice del client deve usare `serverCertificateHashes` **sempre**, perché è la via che funziona
   ovunque; se poi Safari accettasse anche senza, sarebbe un ripiego in più, non un percorso
   diverso.
9. **Una decisione da registrare in `DECISIONI.md` in ogni caso:** il modello di fiducia SSH resta
   valido, ma si sposta di un piano — l'utente si fida della **pagina**, e la pagina si fa garante
   del **trasporto**. È una catena in più, e va scritta.

### Una terza strada, che non è nessuno dei due casi

Il precedente **Plex** (§3.8d) risolve *tutto* — avviso, impronte, rotazione a 14 giorni, Service
Worker — al prezzo di un pezzo di infrastruttura che oggi non abbiamo: un dominio pubblico nostro,
con DNS che risolve nomi tipo `1-2-3-4.HASH.remotix.example` all'**IP privato** del server, e
certificati (wildcard o per nome) da Let's Encrypt via DNS-01. È l'unica soluzione «zero click»
censita che funzioni davvero senza dominio *dell'utente*. Non è una decisione da prendere in questo
rapporto, ma **va messa sul tavolo prima di scrivere il codice della rotazione delle impronte**,
perché le due strade portano a prodotti diversi: una è autosufficiente e chiede un clic, l'altra è
comoda e chiede un servizio sempre acceso da qualche parte. [S]+[?]

---

## 6. Le fonti

### Specifiche
- W3C **WebTransport** — https://w3c.github.io/webtransport/ (§6.9 `WebTransportOptions`, §14.4
  *Server Authentication using Certificate Hashes*)
- IETF **draft-ietf-webtrans-http3-13** — https://www.ietf.org/archive/id/draft-ietf-webtrans-http3-13.txt
- **RFC 9297**, *HTTP Datagrams and the Capsule Protocol* — https://www.rfc-editor.org/rfc/rfc9297.txt
- WICG **Local Network Access** — https://wicg.github.io/local-network-access/
- MDN, *Local network access* — https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Local_network_access
- W3C **Secure Contexts** — https://w3c.github.io/webappsec-secure-contexts/
- WHATWG **HTML**, §8.1.3.5 *Secure contexts* — https://html.spec.whatwg.org/multipage/webappapis.html
- W3C **Service Workers** — https://w3c.github.io/ServiceWorker/
- W3C WebTransport, *explainer* — https://github.com/w3c/webtransport/blob/main/explainer.md

### Dati di compatibilità e versioni
- `mdn/browser-compat-data`, `api/WebTransport.json` —
  https://raw.githubusercontent.com/mdn/browser-compat-data/main/api/WebTransport.json
- Chromium Dash, rilasci stabili —
  https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Linux
- Mozilla product-details — https://product-details.mozilla.org/1.0/firefox_versions.json

### Codice — Chromium (`chromium/chromium@main`, letto il 9 ago 2026)
- `net/quic/dedicated_web_transport_http3_client.cc` — https://raw.githubusercontent.com/chromium/chromium/main/net/quic/dedicated_web_transport_http3_client.cc
- `net/quic/crypto/proof_verifier_chromium.cc` — https://raw.githubusercontent.com/chromium/chromium/main/net/quic/crypto/proof_verifier_chromium.cc
- `content/browser/ssl/ssl_manager.cc` — https://raw.githubusercontent.com/chromium/chromium/main/content/browser/ssl/ssl_manager.cc
- `components/security_interstitials/content/stateful_ssl_host_state_delegate.cc` — https://raw.githubusercontent.com/chromium/chromium/main/components/security_interstitials/content/stateful_ssl_host_state_delegate.cc
- `services/network/public/mojom/web_transport.mojom` — https://raw.githubusercontent.com/chromium/chromium/main/services/network/public/mojom/web_transport.mojom
- `services/network/url_loader.cc` (controllo positivo) — https://raw.githubusercontent.com/chromium/chromium/main/services/network/url_loader.cc
- `services/network/ignore_errors_cert_verifier.cc` — https://raw.githubusercontent.com/chromium/chromium/main/services/network/ignore_errors_cert_verifier.cc
- `net/cert/x509_certificate.cc` — https://raw.githubusercontent.com/chromium/chromium/main/net/cert/x509_certificate.cc
- `net/cert/cert_verify_proc.cc` — https://raw.githubusercontent.com/chromium/chromium/main/net/cert/cert_verify_proc.cc
- `net/http/http_stream_factory_job_controller.cc` — https://raw.githubusercontent.com/chromium/chromium/main/net/http/http_stream_factory_job_controller.cc
- `net/base/net_error_list.h` — https://raw.githubusercontent.com/chromium/chromium/main/net/base/net_error_list.h
- `components/network_session_configurator/common/network_switch_list.h` — https://raw.githubusercontent.com/chromium/chromium/main/components/network_session_configurator/common/network_switch_list.h
- `third_party/blink/renderer/modules/webtransport/web_transport.cc` — https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/modules/webtransport/web_transport.cc

### Codice — quiche (`google/quiche@main`)
- `quiche/quic/core/crypto/web_transport_fingerprint_proof_verifier.cc` — https://raw.githubusercontent.com/google/quiche/main/quiche/quic/core/crypto/web_transport_fingerprint_proof_verifier.cc

### Codice — Gecko (`mozilla/gecko-dev@master`, letto il 9 ago 2026)
- `netwerk/protocol/http/Http3Session.cpp` — https://raw.githubusercontent.com/mozilla/gecko-dev/master/netwerk/protocol/http/Http3Session.cpp
- `netwerk/protocol/http/WebTransportCertificateVerifier.cpp` — https://raw.githubusercontent.com/mozilla/gecko-dev/master/netwerk/protocol/http/WebTransportCertificateVerifier.cpp
- `security/manager/ssl/SSLServerCertVerification.cpp` — https://raw.githubusercontent.com/mozilla/gecko-dev/master/security/manager/ssl/SSLServerCertVerification.cpp
- `modules/libpref/init/StaticPrefList.yaml` — https://raw.githubusercontent.com/mozilla/gecko-dev/master/modules/libpref/init/StaticPrefList.yaml

### Codice — WebKit (`WebKit/WebKit@main`, letto il 9 ago 2026)
- `Source/WebCore/Modules/webtransport/WebTransport.idl` — https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/Modules/webtransport/WebTransport.idl
- `Source/WebCore/Modules/webtransport/WebTransportOptions.idl` — https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/Modules/webtransport/WebTransportOptions.idl
- `Source/WebKit/NetworkProcess/webtransport/cocoa/NetworkTransportSessionCocoa.mm` — https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebKit/NetworkProcess/webtransport/cocoa/NetworkTransportSessionCocoa.mm
- `Source/WebKit/Shared/WebPreferencesDefaultValues.cpp` — https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebKit/Shared/WebPreferencesDefaultValues.cpp
- `Source/WebCore/page/SecurityOrigin.cpp` — https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/page/SecurityOrigin.cpp

### Codice — contesto sicuro e Service Worker (Chromium, Gecko)
- `services/network/public/cpp/is_potentially_trustworthy.cc` — https://raw.githubusercontent.com/chromium/chromium/main/services/network/public/cpp/is_potentially_trustworthy.cc
- `content/browser/service_worker/service_worker_loader_helpers.cc` — https://raw.githubusercontent.com/chromium/chromium/main/content/browser/service_worker/service_worker_loader_helpers.cc
- `content/browser/service_worker/service_worker_consts.h` — https://raw.githubusercontent.com/chromium/chromium/main/content/browser/service_worker/service_worker_consts.h
- `content/common/origin_util.cc` — https://raw.githubusercontent.com/chromium/chromium/main/content/common/origin_util.cc
- `components/permissions/permission_context_base.cc` — https://raw.githubusercontent.com/chromium/chromium/main/components/permissions/permission_context_base.cc
- `content/public/browser/ssl_status.h` — https://raw.githubusercontent.com/chromium/chromium/main/content/public/browser/ssl_status.h
- `third_party/blink/renderer/core/loader/mixed_content_checker.cc` — https://raw.githubusercontent.com/chromium/chromium/main/third_party/blink/renderer/core/loader/mixed_content_checker.cc
- `dom/base/nsContentUtils.cpp` (Gecko) — https://raw.githubusercontent.com/mozilla/gecko-dev/master/dom/base/nsContentUtils.cpp

### Certificati senza dominio: CA, regole, prassi
- CA/Browser Forum, **Baseline Requirements** — https://github.com/cabforum/servercert/blob/main/docs/BR.md
- Let's Encrypt, *Challenge Types* — https://letsencrypt.org/docs/challenge-types/
- Let's Encrypt, *Rate Limits* — https://letsencrypt.org/docs/rate-limits/
- Let's Encrypt, *From 90 to 45 days* — https://letsencrypt.org/2025/12/02/from-90-to-45.html
- Let's Encrypt, *6-day and IP general availability* — https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability.html
- Let's Encrypt, *Issuing our first IP address certificate* — https://letsencrypt.org/2025/07/01/issuing-our-first-ip-address-certificate.html
- Let's Encrypt, *Certificates for localhost* — https://letsencrypt.org/docs/certificates-for-localhost/
- Plex, *How to Use Secure Server Connections* — https://support.plex.tv/articles/206225077-how-to-use-secure-server-connections/
- F. Valsorda, *How Plex is doing HTTPS for all its users* — https://words.filippo.io/how-plex-is-doing-https-for-all-its-users/
- Proxmox VE, *Certificate Management* — https://pve.proxmox.com/wiki/Certificate_Management
- Jellyfin, *Networking* — https://jellyfin.org/docs/general/post-install/networking/
- Syncthing, *Device IDs* — https://docs.syncthing.net/dev/device-ids.html
- Xpra, *SSL* — https://github.com/Xpra-org/xpra/blob/master/docs/Network/SSL.md
- Home Assistant / Nabu Casa, *Remote access deep dive* — https://support.nabucasa.com/hc/en-us/articles/25619268678557-Remote-access-Deep-dive
- libp2p, *WebTransport spec* — https://github.com/libp2p/specs/blob/master/webtransport/README.md
- moq, `rs/moq-native/src/server.rs` — https://github.com/kixelated/moq
- Socket.IO, *WebTransport* — https://socket.io/get-started/webtransport

### Safari / WebKit
- *WebKit Features for Safari 26.4* — https://webkit.org/blog/17862/webkit-features-for-safari-26-4/
- *WebKit Features in Safari 26.0* (controllo positivo) — https://webkit.org/blog/17333/webkit-features-in-safari-26-0/
- *New WebKit Features in Safari 14* — https://webkit.org/blog/11340/new-webkit-features-in-safari-14/
- Apple, *Avoid fraud by using encrypted websites* (macOS) — https://support.apple.com/guide/safari/avoid-fraud-by-using-encrypted-websites-sfri40697/mac
- Apple, *Digital certificates and encrypted websites* (iPhone) — https://support.apple.com/guide/iphone/digital-certificates-and-encrypted-websites-iph1b914c6d4/ios
- Apple Developer Forums, `SecTrustSettingsSetTrustSettings` — https://developer.apple.com/forums/thread/658149
- G. Huston (APNIC), *Triggering QUIC*, IEPG @ IETF 123, luglio 2025 — https://www.iepg.org/2025-07-20-ietf123/slides-123-iepg-sessa-quic-safari-https-and-the-dns-01.pdf

### Bug e discussioni
- Bugzilla **1873263**, *Webtransport: serverCertificateHashes does not work as expected*
  (RESOLVED FIXED, Firefox 125) — https://bugzilla.mozilla.org/show_bug.cgi?id=1873263
- Bugzilla **1806693** (prima implementazione) — https://bugzilla.mozilla.org/show_bug.cgi?id=1806693
- w3c/webtransport issue **#623**, *Consider removing serverCertificateHashes* (rifiuto di WebKit del
  3 dic 2024, **ritrattato** il 20 mag 2025) — https://github.com/w3c/webtransport/issues/623
- w3c/webtransport issue **#508**, *Confirm behaviour of server certificates* — https://github.com/w3c/webtransport/issues/508
- Bugzilla WebKit **300057**, *Implement WebTransportOptions.serverCertificateHashes*
  (`RESOLVED FIXED`, 2 ott 2025) — https://bugs.webkit.org/show_bug.cgi?id=300057
- WebKit standards-positions **#18**, posizione «support» su WebTransport — https://github.com/WebKit/standards-positions/issues/18
- w3c/ServiceWorker issue **#1514**, *SSL certificate error when fetching the script* — https://github.com/w3c/ServiceWorker/issues/1514

---

## 7. Che cosa questo rapporto **non** sa

Perché la prossima persona non le riscopra credendo che siano chiuse:

1. **Se su Safari macOS l'eccezione copra davvero la WebTransport.** È l'ipotesi più promettente e
   nessuno l'ha scritta da nessuna parte (§3.3). *Come apparirebbe il caso opposto:* P1 fallisce con
   il certificato regolarmente presente nel portachiavi.
2. **Se su Safari iOS si possa concedere un'eccezione**, e se sopravviva al riavvio (§3.7). Apple non
   lo documenta: verificata l'assenza nella documentazione, ignoto il comportamento.
3. **Se WebCodecs, WebGPU, Clipboard e Keyboard Lock cambino qualcosa** dietro un'eccezione: nessun
   blocco trovato, ricerca non esaustiva, resta [?] (§3.9, prova P5).
4. **Se Gecko o WebKit abbiano un blocco del Service Worker** analogo a quello di Chromium: su Gecko
   controllato solo `dom/serviceworkers/`, su WebKit non controllato (§3.9).
5. **Se il ripiego di Safari su WebTransport-su-HTTP/2 sia reale e come si manifesti** con un server
   che non lo parla (§3.3).
6. **Se Local Network Access di Chrome 147+ scatti** nel nostro caso: la lettura della specifica dice
   di no, ma è una deduzione (§3.5).
7. **La data esatta in cui le CA pubbliche hanno smesso di emettere per nomi interni** (§3.8c): il
   concetto è nelle BR dal 2014, la cessazione è comunemente datata novembre 2015, non riverificata
   su fonte primaria.
