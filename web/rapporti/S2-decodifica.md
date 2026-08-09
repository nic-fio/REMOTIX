# S2 — Il browser decodifica HEVC Main10 in hardware, e restituisce 10 bit?

*Studio documentale del 9 agosto 2026. Nessuna misura: non ho lanciato browser né dispositivi.
Fonti: specifiche W3C, sorgente Chromium (`main`, scaricato oggi), sorgente WebKit (`main`),
sorgenti di tre progetti di riferimento, documentazione Android/Apple, un dataset di campo 2026.*

**Marche**: `[S]` letto in una specifica o documentazione, con URL · `[R]` letto nel codice
sorgente, con file e riga · `[?]` ipotizzato o dedotto.
⛔ **Nessun `[M]`**: questo rapporto non contiene una sola misura. Chi lo legge non deve mai
poter scambiare una lettura per un numero.

---

## 1. La risposta in cinque righe

1. **Sì, decodificano.** Chrome per Android decodifica HEVC **Main10** via WebCodecs da `108.0.5343.0`
   `[S]`, Safari da 16.4 (video-only) e pienamente da 26.0 `[S]`. Su Linux desktop Chrome lo fa solo
   via VA-API, da `108.0.5354.0` `[S]` — cioè dipende dalla stessa famiglia di driver che usiamo noi
   per codificare.
2. **No, non si può sapere da JavaScript se è hardware.** Non esiste alcuna API che lo dica `[S]`,
   e il segnale che sembra dirlo — `hardwareAcceleration: "prefer-hardware"` — **su Android non lo
   dice**: il percorso «hardware» di Chromium è MediaCodec, e Chromium **accetta esplicitamente un
   codec MediaCodec software per HEVC** `[R]`. È l'errore che ha ucciso la v1, riprodotto dentro
   un'API che sembra proteggerci.
3. **Sul formato del flusso la strada buona è l'opposto di quella che sembra.** Annex-B **senza**
   `description` è legale `[S]`, è quello che `hevc_vaapi` già produce, evita a Chromium una copia
   per fotogramma `[R]`, ed è la strada che tre progetti su tre hanno scelto `[R]`. L'hvcC è la
   strada con una trappola documentata (emulation prevention nel PTL) `[R]`.
4. **I 10 bit arrivano al decodificatore, ma non si possono verificare da JS**: su fotogramma
   decodificato in hardware Chrome espone `VideoFrame.format === null` e nega `copyTo()` `[S]`, e
   il rischio di troncamento a 8 bit è dichiarato dagli stessi sviluppatori Chromium `[S]`.
5. **Quindi S2 va misurata sul telefono vero** (§4), con un banco che porti il proprio controllo
   positivo: se il banco non sa riconoscere come software un decodificatore che *è* software di
   sicuro, il suo verdetto «hardware» su HEVC non vale nulla.

---

## 2. La matrice di supporto

### 2.1 `VideoDecoder` — l'API

| Browser | Piattaforma | `VideoDecoder` da | Marca |
|---|---|---|---|
| Chrome / Edge | Windows, macOS, Linux, Android, ChromeOS | **94** (fine origin trial, set. 2021) | `[S]` |
| Safari | macOS, iOS, iPadOS | **16.4** (solo interfacce video), completo in **26.0** | `[S]` |
| Firefox | desktop (Win/mac/Linux) | **130** | `[S]` |
| Firefox | **Android** | **assente** in release (solo Nightly) | `[S]` |

### 2.2 HEVC dentro `VideoDecoder`

| Browser · piattaforma | HEVC Main 8 bit | HEVC **Main10** | Dipendenza di piattaforma | Marca |
|---|---|---|---|---|
| Chrome/Edge **Windows 8+** | `107.0.5272.0` | **`108.0.5343.0`** | D3D11VA | `[S]` |
| Chrome/Edge **macOS 11+** | `107.0.5272.0` | **`108.0.5343.0`** | VideoToolbox | `[S]` |
| Chrome **Linux** | **`108.0.5354.0`** | idem | ⚠ **solo VA-API**, di fatto solo iGPU Intel; nessun decodificatore software HEVC nel binario | `[S]` |
| Chrome **Android 5.0+** | `107.0.5272.0` | `108.0.5343.0`; enumerazione dei livelli corretta da **`112.0.5612.0`** (prima tutto tagliato a 4K) | **MediaCodec** — e MediaCodec può essere software | `[S]` `[R]` |
| Chrome **ChromeOS** | sì | sì | solo GPU VA-API | `[S]` |
| **Safari** macOS/iOS/iPadOS | sì | sì | VideoToolbox; **nessun decodificatore HEVC software** in Apple | `[S]` `[?]` |
| **Firefox** desktop | macOS abilitato, Linux via VA-API (bug 1944991, 1949917) | `[?]` non verificato | copertura di campo minima | `[S]` |
| **Firefox** Android | assente | assente | — | `[S]` |
| **Edge** Windows | copertura di campo ~56% (licenze) | `[?]` | — | `[S]` |

**Copertura di campo 2026** `[S]` — 363 milioni di prove di codec su 1,14 milioni di sessioni,
gennaio-marzo 2026, misurate *interrogando WebCodecs*, non l'hardware:
`VideoDecoder` HEVC **78,87%** complessivo; **HEVC Main10 in decodifica ≈ 85%**; Safari quasi
universale; Chrome non-Windows ≈ 81%; Firefox ≈ 0-1,8%.
⚠ L'autore del dataset dichiara esplicitamente: **«The analysis does not distinguish between
hardware and software decoding»**. Quell'85% è una promessa dell'API, non un fatto sul silicio.

### 2.3 Il tetto: livello e profilo per 4K60 10 bit

`[S]` `[?]` 3840×2160×60 = 497 664 000 campioni di luma al secondo.
Livello **5** (`L150`) ammette 267 386 880 → **non basta**.
Livello **5.1** (`L153`) ammette 534 773 760 → **basta, con poco margine**.
Quindi la stringa minima corretta per il nostro traguardo è **livello 5.1**, non 5.0. `[?]` Se
superiamo i 40 Mbit/s serve il *tier* High (`H153`) invece del Main (`L153`): il tetto Main a 5.1
è 40 Mbit/s.

---

## 3. Il dettaglio, domanda per domanda

### 3.1 La stringa di configurazione, e che cosa dimostra

`[S]` La grammatica è `hev1.` o `hvc1.` più quattro campi separati da punto
(ISO/IEC 14496-15 §E.3):

| Campo | Significato |
|---|---|
| `A` | `general_profile_space` (lettera A/B/C, o niente per 0) + `general_profile_idc` decimale |
| `B` | `general_profile_compatibility_flags`, 32 bit in **esadecimale e in ordine di bit invertito** |
| `C` | `L` (tier Main) o `H` (tier High) + `general_level_idc` decimale |
| `D` | i 6 byte di constraint flag in esadecimale, byte a zero in coda omissibili |

Per **Main10 a 4K60** la stringa è dunque:

```
hvc1.2.4.L153.B0      (o hev1.2.4.L153.B0 — vedi §3.4)
     │ │ │    └── constraint: progressive, non-packed, frame-only
     │ │ └─────── tier Main, livello 5.1  (153 = 5.1 × 30)
     │ └───────── compatibility flags = 4  → bit 2 = Main10
     └─────────── general_profile_idc = 2 → Main10
```

`[R]` `hvc1.1.6.L153.B0` è la corrispondente **Main 8 bit**. moonlight-web usa esattamente
queste due, più `L150`, come lista di ripiego
(`frontend/js/util/Mp4Muxer.js:564-574`).

**⛔ Che cosa dimostra `isConfigSupported()` — e che cosa no.**
`[S]` La specifica dice solo: *«Returns a promise indicating whether the provided config is
supported by the User Agent»*. `[R]` Nel codice, `VideoDecoder::isConfigSupported`
(`third_party/blink/renderer/modules/webcodecs/video_decoder.cc:290-334`) con
`hardwareAcceleration` non specificato fa **due sole cose**: chiama
`media::IsDecoderSupportedVideoType()` e verifica che si riesca a costruire una
`media::VideoDecoderConfig`. Poi:

```cpp
  // Otherwise, the config is supported.
  support->setSupported(true);
```

Nessuna interrogazione della GPU. **`supported: true` è una dichiarazione di intenti del
browser, non un fatto sull'hardware.** Ed è già successo che mentisse: WebKit bug 262950,
`isConfigSupported()` restituiva `true` e poi la decodifica falliva con `VideoToolbox -12909` `[S]`.

### 3.2 `prefer-hardware`: che cosa garantisce davvero

`[S]` La specifica è tiepida per costruzione: *«User Agents are not obligated to honor the
`hardwareAcceleration` hint and may make independent decisions»*, e avverte che l'opzione
*«may expose the presence or absence of hardware encoders/decoders, which could increase
fingerprinting surface»*. Il dibattito su se esporlo o no (w3c/webcodecs#239) si è chiuso
lasciandolo come **preferenza scrivibile e mai rileggibile**.

Ma il codice di Chromium è **molto meno tiepido della specifica**, e questo va sfruttato.

`[R]` `third_party/blink/renderer/modules/webcodecs/video_decoder.cc:320-331` — con
`prefer-hardware`, `isConfigSupported()` **smette di rispondere subito** e va a interrogare le
*GPU factories*:

```cpp
  // If hardware is preferred, asynchronously check for a hardware decoder.
  if (hw_pref == HardwarePreference::kPreferHardware) {
    ...
    RetrieveGpuFactoriesWithKnownDecoderSupport(CrossThreadBindOnce(
        &DecoderSupport_OnKnown, ...
```

`[R]` `third_party/blink/renderer/modules/webcodecs/video_decoder_broker.cc:204-222` — e alla
`configure()`, con `prefer-hardware`, il broker **butta via del tutto la fabbrica di
decodificatori predefinita**, quella che contiene FFmpeg, libvpx e dav1d:

```cpp
    if (hardware_preference_ != HardwarePreference::kPreferSoftware) {
      external_decoder_factory = std::make_unique<media::MojoDecoderFactory>(...);
    }
    if (hardware_preference_ == HardwarePreference::kPreferHardware) {
      decoder_factory_ = std::move(external_decoder_factory);
      return;                          // ← DefaultDecoderFactory non viene mai creata
    }
    decoder_factory_ = std::make_unique<media::DefaultDecoderFactory>(
        std::move(external_decoder_factory));
```

`[R]` E il commento a `video_decoder_broker.cc:246-247` conferma che il caso «niente
decodificatore» è previsto: *«We can end up with a null `decoder_factory_` if
`hardware_preference_` filtered out all available factories»*.

**Conclusione su desktop** `[R]`: in Chromium, se `configure({hardwareAcceleration:
'prefer-hardware'})` riesce, i decodificatori software *interni* sono stati esclusi
strutturalmente, non per preferenza. Questa è **prova reale**, non l'errore della v1.

### 3.3 ⛔ E qui viene la trappola: su Android non vale

`[R]` Su Android l'unica «fabbrica esterna» è MediaCodec, e Chromium **sceglie di proposito un
codec MediaCodec software per HEVC quando non ne trova uno hardware**.
`media/gpu/android/media_codec_video_decoder.cc:178-215`, funzione `SelectMediaCodec`:

```cpp
    // Prioritize hardware decoder. Software decoder will be selected as a
    // fallback option.
    if (info.is_software_codec) {
      if (software_decoder.empty()) { software_decoder = info.name; }
      continue;
    }
    ...
  // Allow software decoder if either:
  // 1. the stream is encrypted.
  // 2. No software decoder is bundled into Chromium.
  if (!(config.is_encrypted()
        || config.codec() == VideoCodec::kH264
        || (config.codec() == VideoCodec::kHEVC &&
            base::FeatureList::IsEnabled(kPlatformHEVCDecoderSupport))
        ...)) {
    return false;                       // ← per HEVC questo ramo NON viene preso
  }
  *out_codec_name = software_decoder;   // ← per HEVC si finisce QUI
  return true;
```

La logica è coerente e persino ragionevole: Chromium non impacchetta un decodificatore HEVC
software (è un codec proprietario), quindi *se non lo fa MediaCodec, nessuno lo fa*. Ma la
conseguenza per noi è brutale:

> `[R]` Su Android, `hardwareAcceleration: "prefer-hardware"` + `configure()` riuscita
> **è perfettamente compatibile con `c2.android.hevc.decoder`**, un decodificatore HEVC in
> puro software, perché esso vive dietro la stessa interfaccia MediaCodec che Chromium
> considera «piattaforma». `MediaCodecVideoDecoder::GetDecoderType()` restituisce
> `kMediaCodec` a prescindere (`media_codec_video_decoder.cc:1428`), e la lista dei nomi
> software è in chiaro nel codice: `c2.android.hevc`, `omx.google.hevc`
> (`media/base/android/media_codec_util.cc:251-261`).

`[R]` La stessa cecità contagia `GenerateSupportedConfigs`
(`media_codec_video_decoder.cc:63-124`): per VP8/VP9/AV1/H.264-bundled c'è un filtro esplicito
`if (info.is_software_codec && !is_os_software_decoder_allowed) → dichiara supportato solo per
contenuto cifrato`; **nel ramo HEVC quel filtro non c'è affatto**, la config viene aggiunta e
basta.

**Esiste un modo qualunque, da JavaScript, di sapere se il decodificatore è hardware?**
**No.** `[S]` `[R]` Controllo positivo della ricerca: il dato *esiste* dentro Chromium ed è
persino calcolato — `decoder_->IsPlatformDecoder()` e `decoder_->GetDecoderType()` vengono letti
in `video_decoder_broker.cc:271-272` e usati in
`decoder_template.cc:705` e `:954` — ma **non viene mai messo su un attributo IDL**. Non è che
non l'ho trovato: l'ho trovato, e finisce solo in log interni e in una scelta di pressione sui
codec. Nessuna via verso JS.

### 3.4 I segnali indiretti che restano, con il loro caso opposto

| # | Segnale | Che cosa vale | ⛔ Come apparirebbe un decodificatore software che finge bene |
|---|---|---|---|
| **1** | `MediaCapabilities.decodingInfo({type:'media-source', video:{...}})` → **`powerEfficient`** | `[R]` In Chromium è letteralmente `gpu_factories->IsDecoderConfigSupportedOrUnknown(config) == kTrue` (`media_capabilities.cc:1461-1462`, `:1498`). È il segnale JS **più forte** che esista: interroga davvero l'elenco di capacità del processo GPU. `[S]` La specifica avverte però che la definizione è lasciata allo user agent. | **Su Android lo supera senza sforzo**: le capacità GPU per HEVC includono i codec software di MediaCodec `[R]` §3.3. Apparirebbe `powerEfficient: true` con dietro `c2.android.hevc.decoder`. Su iOS `[?]` non ho verificato come WebKit lo calcoli. |
| **2** | `configure({prefer-hardware})` che riesce | `[R]` Su **desktop** esclude FFmpeg/libvpx/dav1d strutturalmente (§3.2). Prova reale lì. | **Su Android non prova niente** (§3.3). Il decodificatore software passerebbe indistinguibile. |
| **3** | Nome della `DOMException` su errore di decodifica | `[R]` `decoder_template.cc:954`: se `!decoder_->IsPlatformDecoder()`, Chromium emette `MakeSoftwareCodecOperationError` invece di `MakeOperationError`. **È l'unico bit di verità che filtra fino a JS** — ma solo in caso di errore, e solo per i decodificatori *non* di piattaforma. | Un codec MediaCodec software **è** di piattaforma: emetterebbe l'errore «normale». Inutile su Android, che è il caso che ci preoccupa. |
| **4** | `chrome://media-internals` (fuori da JS) | `[R]` **La verità in chiaro**: `media_codec_video_decoder.cc:791-793` registra `MEDIA_LOG(INFO) << "Created MediaCodec " << codec_name_ << ", is_software_codec=" << codec->IsSoftwareCodec()`. `[S]` Raggiungibile su Android via `chrome://inspect` e debug remoto. | **Non può fingere**: la stringa arriva da `MediaCodec.getName()`. È il *ground truth* del banco su Android. Su iPhone `[?]` non esiste equivalente: Safari Web Inspector non ha un media-internals. |
| **5** | Portata a saturazione, energia, decadimento termico | §4. È l'unico segnale che vale **anche su iPhone**. | Vedi §4: al carico bersaglio (4K60 10 bit) e su una durata di minuti, non riesce a fingere. |

### 3.5 ⛔ Il formato del flusso — la parte che tocca `hevc_vaapi`

`[S]` La registrazione HEVC W3C definisce **due formati alternativi ed esclusivi**:

> *«If the description is present, it is assumed to be an HEVCDecoderConfigurationRecord, as
> defined by [iso14496-15], section 8.3.3.1, and the bitstream is assumed to be in hevc format.»*
> *«If the bitstream is in hevc format, [[internal data]] is assumed to be in canonical format,
> as defined in [iso14496-15] section 8.3.2.»* (= NAL con prefisso di lunghezza)
> *«If the bitstream is in annexb format, [[internal data]] is assumed to be in Annex B format,
> as defined in [ITU-T-REC-H.265] Annex B.»*

E sui fotogrammi chiave la differenza è sostanziale:

> `[S]` *in hevc format*: il chunk `key` deve contenere una figura IDR, CRA o BLA.
> *in annexb format*: deve contenere una figura IDR/CRA/BLA **«and all parameter sets necessary
> to decode all video data NAL units in the EncodedVideoChunk»**.

#### La raccomandazione per REMOTIX: **Annex-B, senza `description`**

Tre ragioni, tutte lette nel codice.

**(a) È quello che `hevc_vaapi` già produce.** `[?]` `libavcodec` restituisce i pacchetti HEVC in
Annex-B; l'hvcC non è mai prodotto dal codificatore ma dal *muxer* MP4
(`libavformat/hevc.c`, `ff_isom_write_hvcc`). Produrre un hvcC significherebbe o scriverlo a mano
o passare da un muxer fittizio. Basta **non** impostare `AV_CODEC_FLAG_GLOBAL_HEADER`, così i
parameter set VPS/SPS/PPS vengono ripetuti in banda prima di ogni IDR — che è esattamente ciò che
la registrazione richiede per il formato annexb.

**(b) In Chromium l'Annex-B è la strada *più veloce*, non la più lenta.** `[R]`
`video_decoder.cc:466-495`: se `description` è presente, Chromium costruisce un `VideoDecoderHelper`
e — commento testuale — *«The description should not be provided to the decoder because the stream
will be converted to Annex B format»*. Quella conversione costa, **per ogni singolo fotogramma**,
un'allocazione e una copia (`video_decoder.cc:611-633`):

```cpp
    std::vector<uint8_t> buf(output_size);
    ... ConvertNalUnitStreamToByteStream(...)
    decoder_buffer = media::DecoderBuffer::CopyFrom(base::span(buf).first(output_size));
```

A 4K60 sono 60 allocazioni e copie di alcuni megabyte al secondo, **regalate**. Dando Annex-B,
`decoder_helper` resta nullo e il buffer passa senza toccarlo.

**(c) È la prassi di chi lo fa già.** `[R]`
- **Xpra html5** (`html5/js/VideoDecoder.js:81-100`) passa solo `codec`,
  `hardwareAcceleration:"no-preference"`, `optimizeForLatency:true`. Un grep di `description` su
  tutti gli `html5/js/*.js` dà **0**: assenza verificata, non «non trovata».
- **scrcpy / Tango** (`libraries/scrcpy-decoder-webcodecs/src/video/codec/h26x.ts:36-45`) non emette
  `description`, e concatena VPS+SPS+PPS davanti al primo keyframe
  (`video/utils/video-decoder-stream.ts:57-59`). Grep di `hvcC|avcC` su tutto `libraries/`: solo due
  stringhe letterali di prefisso codec. Assenza verificata.
- **moonlight-web** (`frontend/js/stream/VideoDecodeWorker.js:451-463`) prova **per HEVC l'Annex-B
  per primo** e l'hvcC solo dopo, con questo commento nel codice: *«HEVC: Annex B (no description)
  first — Chromium keyframe validator only parses start codes; AVCC-with-description comes after»*.

#### ⚠ Se invece l'hvcC dovesse servire: la trappola documentata

`[R]` moonlight-web, `frontend/js/util/Mp4Muxer.js:252` (`buildHvcCDescription`) e il commento a
`:268-282`: ISO/IEC 14496-15 vuole gli *emulation prevention byte* **conservati** dentro gli array
NAL dell'hvcC; ma Chromium **riparsa l'SPS dall'array** e confronta il profile-tier-level con
l'header dell'hvcC — se l'SPS grezzo contiene `00 00 03` nella zona PTL, i valori non coincidono e
**`isConfigSupported()` rifiuta la configurazione**. Il loro rimedio è scrivere NAL *de-emulati*,
che loro stessi definiscono *«technically non-compliant with ISO 14496-15 but is required for
Chrome compatibility»*.
`[R]` Un'implementazione pulita e conforme, se serve un riferimento, è in `Vanilagy/mediabunny`,
`src/codec-data.ts:1054` (`extractHevcDecoderConfigurationRecord`) e `:1462`
(`serializeHevcDecoderConfigurationRecord`).

#### `hvc1` o `hev1`?

`[S]` La grammatica dei due prefissi è identica; `hev1` è la variante con parameter set in banda.
Con Annex-B e VPS/SPS/PPS ripetuti a ogni IDR, **`hev1` è la scelta semanticamente giusta**.
`[R]` WebKit accetta entrambi i prefissi: `Source/WebCore/Modules/webcodecs/WebCodecsVideoDecoder.cpp:81-82`
(`codec.startsWith("hev1."_s) || codec.startsWith("hvc1."_s)`).
`[R]` moonlight-web usa `hev1.…` per l'Annex-B e `hvc1.…` per l'hvcC — la stessa distinzione.
`[?]` Chromium accetta entrambi in Annex-B (Xpra e Tango passano Annex-B con prefisso `avc1.`), ma
questo va **provato al banco**, non dato per buono.

#### E Safari?

`[R]` **WebKit accetta Annex-B senza `description`, ed esiste il test che lo prova**: il commit
`8555adf` (8 dicembre 2023, PR #21496) aggiunge
`LayoutTests/http/wpt/webcodecs/hevc-decoder-annexb.https.any.js` e corregge
`H265AnnexBBufferToCMSampleBuffer()` in
`Source/ThirdParty/libwebrtc/Source/webrtc/sdk/objc/components/video_codec/nalu_rewriter.cc`
(`BytesRemaining()` → `BytesRemainingForAVC()`, righe 380-381; e il commento a `:416` corretto da
«Avcc NALUs» a «Hvcc NALUs»). Cioè: **WebKit fa la conversione inversa alla nostra** — prende
l'Annex-B e costruisce l'hvcC internamente, perché VideoToolbox vuole una
`CMVideoFormatDescription`.

⭐ **Il quadro completo**: non esiste un percorso gratis per entrambi i browser. Chromium converte
hvcC → Annex-B; WebKit converte Annex-B → hvcC. **Dando Annex-B paghiamo la conversione solo su
Safari; dando hvcC la paghiamo su Chrome *e* rischiamo la trappola del PTL.** Annex-B vince.

### 3.6 `key` e `delta`, e il fotogramma che abbandoniamo di proposito

**La mappatura.** `[S]` `key` = IDR / CRA / BLA (con tutti i parameter set, in Annex-B); `delta` =
tutto il resto. È una mappatura diretta sui nostri due tipi.

**Il vincolo di partenza.** `[S]` Dopo `configure()` e dopo `flush()`, il primo chunk **deve** essere
`key`, altrimenti `DataError`. `[R]` Chromium non si fida della nostra etichetta e **rilegge il
bitstream**: `video_decoder.cc:206-214` chiama `media::mp4::HEVC::AnalyzeAnnexB()`, e se l'etichetta
dice `key` ma i NAL dicono altro, errore. Ha persino un messaggio dedicato al nostro esatto errore
possibile (`video_decoder.cc:676-683`):

> *«A key frame is required after configure() or flush(). If you're using HEVC formatted H.265 you
> must fill out the description field in the VideoDecoderConfig.»*

**⛔ Che cosa succede quando manca un `delta`.**
`[R]` La verifica del bitstream avviene **solo quando `verify_key_frame` è vero**, cioè dopo
`configure()`/`flush()`. In regime, i chunk passano senza analisi. Quindi:

> `[?]` Se abbandoniamo un `delta`, il decodificatore **non se ne accorge e non solleva alcun
> errore**. Decodifica i `delta` successivi contro riferimenti sbagliati e produce corruzione
> visibile che **si propaga fino al prossimo `key`**. Nessuna API di WebCodecs segnala la
> discontinuità: non c'è un numero di sequenza, non c'è un `onerror` per «riferimento mancante».

`[S]` WebCodecs è anche **più severo** di `<video>` su questo: non usa i punti di ripristino SEI
(`recovery_point`), la cui adozione è ancora un'issue aperta (w3c/webcodecs#650). L'unico modo
documentato di rientrare è un chunk `key`.

**Come si recupera — e la conseguenza per il progetto.**
1. Il client rileva la corruzione (o meglio: il *server* sa di avere abbandonato) e si torna a un
   IDR. Serve dunque **un canale di ritorno** e la capacità del server di forzare un IDR.
2. `[S]` `reset()` rimette `[[key chunk required]] = true` e svuota la coda: è la ripartenza pulita.
   `flush()` no, aspetta i fotogrammi in volo.
3. ⭐ **La cura vera è a monte**: se vogliamo poter abbandonare fotogrammi *senza* rompere niente,
   devono essere fotogrammi **che nessuno usa come riferimento**. In HEVC significa **sotto-livelli
   temporali** (`nuh_temporal_id`): il livello temporale più alto non è mai riferimento, e si può
   buttare a piacere. `[?]` Questo va verificato su `hevc_vaapi`, che sulla UHD 730 espone solo il
   percorso `EncSliceLP` — se `EncSliceLP` non sa fare la piramide temporale, l'abbandono selettivo
   non è disponibile e ogni abbandono costa un IDR.

### 3.7 I 10 bit, davvero

**Che formato esce.** `[S]` L'enumerazione `VideoPixelFormat` della specifica **contiene** i formati
a 10 bit: `I420P10`, `I420P12` (oltre a `I420`, `I420A`, `I422`, `I444`, `NV12`, `RGBA`, `RGBX`,
`BGRA`, `BGRX`). `P010` **non c'è**: è un formato di piattaforma, non un formato WebCodecs.

**⛔ Ma in Chrome, sul fotogramma decodificato in hardware, `format` è `null`.**
`[S]` w3c/webcodecs discussion #631: decodificando video a 10 bit in Chrome, `VideoFrame.format`
restituisce **`null`**, e di conseguenza `copyTo()` non è utilizzabile. Dale Curtis (Chromium,
30 gennaio 2023) è esplicito su ciò che manca e su ciò che rischia di succedere:

> *«High bit depth pixel types are a work in progress… hardware-decoded cases will take some time
> since we don't have HBD readback paths»* e
> *«In Chrome, once #384 is resolved you'll be able to use `copyTo()` with all software decoded
> cases. **However hardware decoded cases may take some time or will undergo a conversion to
> 8-bit.**»*

`[S]` L'issue di riferimento (w3c/webcodecs#384, «HDR support», aperta il 22 ottobre 2021, etichette
`extension` e `p1`) **risulta ancora aperta**. `[?]` Non ho potuto verificare lo stato preciso
dell'implementazione Chromium ad agosto 2026: dichiaro questo come **non verificato**, non come
assente. È la prima cosa che il banco deve accertare.

**Il rischio di troncamento a 8 bit esiste, ed è documentato anche fuori dal browser.**
`[S]` mpv-android issue #462 (28 novembre 2021, Pixel 6 / Tensor con decodificatore Exynos):
i file HEVC 10 bit in decodifica hardware escono **verdi e distorti**, gli H.264 10 bit **neri**;
in software vanno bene. Diagnosi del segnalatore: *«While looking at the logs I noticed it is using
yuv420p as pixel format. Shouldn't this be yuv420p10le?»* — cioè il flusso a 10 bit trattato come
8 bit. Lo stesso quadro ricorre negli issue #423, #540, #855, #1088 dello stesso progetto.
`[?]` Non è la stessa catena del browser (mpv usa MediaCodec direttamente), ma **è la stessa
MediaCodec e lo stesso silicio**: il rischio non è teorico.

**Come si verifica che i 10 bit siano arrivati fino allo schermo.**
Onestamente: **da JavaScript, oggi, non si può in modo diretto** — `format === null` chiude la via
di `copyTo()`. Restano tre prove, in ordine di forza decrescente:

1. **Prova di sopravvivenza (negativa, ma forte).** `[?]` Si dà in pasto un Main10 e si guarda se
   esce l'immagine giusta o il verde di mpv #462. Se esce verde, i 10 bit *non* sono arrivati.
   Se esce giusta, non prova ancora che non siano stati troncati a 8 bit.
2. **Prova di banding, con controllo.** `[?]` Si codificano due sequenze: **A** una rampa di grigio
   verticale con passo di 1/1023 su tutta l'altezza (usa i 10 bit); **B** la stessa rampa
   *quantizzata a 8 bit* e poi codificata in Main10 (contiene solo 256 livelli). Si rendono su
   canvas e si contano le bande visibili con un'analisi delle differenze di riga sul canvas stesso.
   **Se il banco conta lo stesso numero di bande in A e in B, i 10 bit sono stati troncati.** Se ne
   conta ~4× di più in A, sono arrivati almeno fino al canvas.
   ⛔ **Caso opposto**: un decodificatore che tronca a 8 bit renderebbe A e B **identiche**. Il
   controllo positivo di questa prova è proprio B: se il banco non distingue A da B, non sta
   guardando i 10 bit, sta guardando il rumore di compressione.
   ⚠ Attenzione: il canvas 2D standard è a 8 bit per canale — la prova andrebbe fatta su un canvas
   `float16` o via WebGPU. `[?]` Non ho verificato la disponibilità di quel percorso su Chrome
   Android e Safari iOS: da accertare al banco.
3. **Prova di fedeltà oggettiva (fuori dal browser).** `[?]` Si mette a confronto il PSNR della
   ricostruzione software (FFmpeg, `yuv420p10le`) con quella catturata dal canvas. Un troncamento a
   8 bit ha una firma di errore precisa e riconoscibile.

⭐ Nel dubbio, **la posizione onesta da scrivere in DECISIONI.md** è: *i 10 bit sono verificabili
fino all'ingresso del decodificatore; oltre, sul telefono, oggi non lo sono da JavaScript.*

### 3.8 Limiti pratici sui telefoni

**Che cosa garantisce Android.** `[S]` La CDD Android 16 impone la decodifica HEVC (5.3/H-0-2);
per la Media Performance Class V **almeno un decodificatore hardware con capacità 4K60**
(5.1/H-1-15) e tre sessioni **10 bit HDR** concorrenti a 4K@30 (5.1/H-1-19).
⚠ `[?]` Da leggere con attenzione: il 4K60 garantito è *un* decodificatore, **non necessariamente
HEVC e non necessariamente a 10 bit**. La garanzia è più debole di quanto sembri.
`[S]` A runtime, `MediaCodecInfo.VideoCapabilities.getSupportedPerformancePoints()` restituisce i
punti prestazionali reali — ma `[?]` **non ho trovato modo di leggerli da WebCodecs**:
`isConfigSupported()` non espone il punto prestazionale, solo un sì/no.

**iPhone.** `[S]` HEVC Main10 esiste in VideoToolbox da iOS 11. `[?]` **Non ho trovato** una tabella
Apple pubblica che dichiari il livello HEVC massimo per modello, né una garanzia formale «4K60
Main10 da modello X». L'unica via praticabile resta interrogare `isConfigSupported()` con
`hvc1.2.4.L153.B0` e `codedWidth/codedHeight` a 3840×2160 — con tutte le riserve del §3.1.

**La scheda in sfondo.** Questo è un problema serio e **risolvibile per progetto**:
- `[S]` Chrome non chiama `requestAnimationFrame()` quando la pagina è in background (dal 2011).
- `[S]` **Freezing (Energy Saver)**: un browsing context group viene congelato se tutte le pagine
  sono *hidden e silent* da oltre **5 minuti** — sospende handler, timer e risoluzione di Promise.
  ⭐ Le esenzioni documentate includono **una `RTCPeerConnection` con `RTCDataChannel` aperto o una
  `MediaStreamTrack` viva**. Se REMOTIX tiene aperto un DataChannel per l'input, **rientra
  nell'esenzione**. Non è fortuna, è una leva di progetto.
- `[S]` I `VideoDecoder` inattivi in schede in background vengono **reclamati**, con
  `QuotaExceededError` alla ripresa (w3c/webcodecs#889, #363). `[R]` Il meccanismo si vede nel
  codice: `decoder_template.cc:705`, `if (decoder()->IsPlatformDecoder()) ApplyCodecPressure();`.
- `[S]` Chrome Android congela le schede in background dopo 5 minuti da Chrome 77; al ritorno non
  scatta `visibilitychange` ma l'evento `resume`.
- `[S]` iOS/Safari: rAF limitato a **30 fps** in Low Power Mode; WebRTC e Web Audio sospesi appena
  lo schermo si blocca. `[?]` Per WebCodecs su iOS **non ho trovato documentazione specifica**.
- `[S]` Bug noto (issues.chromium.org/404905689): su macOS, non chiamare `decoder.close()` al
  passaggio in `hidden` causa una perdita di memoria in `VTDecoderXPCService`. **Chiudere sempre.**

**Consumo e calore.** `[S]` Studio comparativo HEVC hardware vs software: la decodifica software
consuma meno del 50% della potenza totale di piattaforma, l'hardware meno del 30%; ma la cosa che
conta è **come scalano**: passando da 720p a 2160p l'energia del software cresce **13,76×**, quella
dell'hardware **2,14×**. `[?]` Quel fattore ~6,4× di divergenza è la ragione per cui il banco del §4
deve girare **al carico bersaglio e per minuti**: è lì che il software non riesce più a fingere.

### 3.9 AV1 come alternativa — no, e per due ragioni indipendenti

`[S]` **Lato server è già chiuso**: nessuna delle nostre due schede codifica AV1 in hardware.
Codificare AV1 in software a 4K60 è fuori discussione per il tetto di 50 ms.

`[S]` **Lato client sarebbe comunque una trappola.** Dataset 2026: AV1 Profile 0 in decodifica ≈
**91,5%**, e — dettaglio interessante — **il 10 bit resta a ~91%, identico all'8 bit** (crolla solo
la codifica, a ~8%). Ma quel 91% è capability, non silicio: `[S]` Chrome Android riproduce AV1 via
**dav1d in software** da Android 10 su tutto il parco senza decodificatore hardware, e Qualcomm ha
aggiunto AV1 hardware solo con **Snapdragon 8 Gen 2** (2023); MediaTek dal Dimensity 1000 (2020),
Exynos 2200, Tensor G2/G3. Apple: AV1 solo da **A17 Pro / M3** in poi, e senza alcun decodificatore
software di riserva (Safari macOS ≈ 24%, Safari iOS ≈ 33%).
`[S]` `[?]` A 4K60 in software AV1 non regge: i benchmark dav1d su mobile arrivano a 1080p30 sulla
fascia alta e a 4K30 su A12X — **manca un fattore ~2, e il 10 bit costa di più**.

⚠ **Correzione a un dettaglio del mandato**: la stringa `av01.0.05M.10` **non** descrive 4K60.
`[S]` In `av01.P.LLT.DD` il campo `LL` è il `seq_level_idx`, non il livello: livello =
`2 + (idx >> 2)`. Quindi `05` = **livello 3.1** (~720p60), del tutto insufficiente. Per 4K60
servirebbe `[?]` **`av01.0.13M.10`** (idx 13 → livello 5.1, max 4096×2176).
`[S]` E AV1 **non usa `description`**: la registrazione W3C dice testualmente *«description is not
used for this codec»*, e il chunk deve essere nel *low-overhead bitstream format* (OBU con
`obu_has_size_field`), non Annex-B.

⭐ **Verdetto**: AV1 è chiuso da entrambi i lati. Non è un ripiego, è un vicolo cieco.

### 3.10 Prassi altrui — che cosa scelgono e perché

| Progetto | Trasporto | Codec | `description`? | Osservazione |
|---|---|---|---|---|
| **Xpra html5** `[R]` | WebSocket / WebTransport (protocollo Xpra) | **solo** `avc1.42C01E` (H.264 **baseline**), vp8, vp9 | **no**, Annex-B | Spinge il server verso il profilo più facile del mondo: `profile: "baseline", level: "2.1", cabac: false, deblocking-filter: false, fast-decode: true`, e **solo YUV420P 8 bit** (`Client.js:198-214`). HEVC assente (grep verificato: una sola riga, un colore di debug). |
| **scrcpy / Tango** `[R]` | WebSocket su adb | H.264, H.265, AV1 | **no**, Annex-B; VPS/SPS/PPS concatenati davanti al primo keyframe | La stringa codec è **derivata parsando l'SPS** (`media-codec/src/h265.ts:1375`). |
| **moonlight-web** `[R]` | **WebRTC** (RTP + DataChannel), ma il video **non** va in `<video>`: WebCodecs in un worker → WebGPU | H.264 e **HEVC incl. Main10** (`hvc1.2.4.L153.B0`) | HEVC: **Annex-B per primo**, hvcC come ripiego. H.264: il contrario | È il progetto più vicino a noi. Usa `optimizeForLatency: true` e prova `prefer-hardware` (`VideoDecodeWorker.js:368, 411`). |
| **GeForce NOW** `[S]` | proprietario | **AV1** dove il dispositivo lo decodifica, ripiego H.265/H.264 | — | Conferma che AV1 si usa **solo** dove c'è hardware. |
| **WebRTC in Chrome** `[S]` | — | HEVC in WebRTC da **Chrome 136**, e — testuale nell'Intent to Ship — *«we will not provide a software implementation to fall back to»* | — | ⭐ In WebRTC Google ha scelto **hardware o niente**. In WebCodecs no. La differenza è precisamente il nostro problema. |

`[S]` `[?]` Perché scegliere WebCodecs invece di WebRTC: WebRTC impone un jitter buffer e una logica
di riproduzione non controllabili dall'applicazione. Con WebTransport+WebCodecs l'applicazione
riprende il controllo di pacchettizzazione, priorità e buffering. Le cifre citate (20-30 ms in meno)
vengono da un blog, non da uno standard: ordine di grandezza, non misura.

⭐ **La lezione**: tre progetti su tre passano **Annex-B senza `description`**, e nessuno tranne
moonlight-web supera gli 8 bit lato client. Non è pigrizia: è la strada con meno parti mobili.

---

## 4. ⛔ Il banco: come si misura S2 sul telefono vero

**Regola d'ingaggio.** Il banco non deve dire «hardware» o «software». Deve produrre **numeri**, e
dichiarare la propria sensibilità *prima* di dare un verdetto. Un banco che non ha dimostrato di
saper riconoscere un decodificatore software non ha il diritto di dichiarare «hardware».

### 4.1 Che cosa si dà in pasto

Cinque sequenze, tutte prodotte dal **nostro** `hevc_vaapi` (perché è il flusso vero che dovremo
mandare), in **Annex-B con VPS/SPS/PPS ripetuti a ogni IDR**, servite come array di
`EncodedVideoChunk` precaricati in memoria — **niente rete nel banco**, la rete si misura altrove:

| | Sequenza | Codec string | Scopo |
|---|---|---|---|
| **A** | HEVC **Main10** 3840×2160 @60, 900 chunk (15 s), 1 IDR ogni 300 | `hev1.2.4.L153.B0` | **Il bersaglio.** |
| **B** | HEVC **Main 8 bit** 3840×2160 @60, identica per struttura | `hev1.1.6.L153.B0` | Isola il costo dei 10 bit dal costo del 4K. |
| **C** | HEVC Main10 1920×1080 @60 | `hev1.2.4.L120.B0` | Il ripiego realistico, se A cade. |
| **D** | **VP9 Profile 0** 1920×1080 @60, 8 bit | `vp09.00.10.08` | ⭐ **Il controllo positivo** (§4.4). |
| **E** | Rampa di grigio a passo 1/1023, Main10 · e la **stessa rampa quantizzata a 8 bit**, sempre in Main10 | `hev1.2.4.L153.B0` | La prova dei 10 bit (§3.7 punto 2), con il proprio controllo interno. |

Ogni sequenza si prova con **tre configurazioni**: `hardwareAcceleration` a `no-preference`,
`prefer-hardware`, `prefer-software`. Tutte con `optimizeForLatency: true`.

### 4.2 Che cosa si conta

Tutto in un `Worker` dedicato, in modo che il thread principale resti libero e misurabile.

1. **Portata a saturazione** — la misura principale.
   Si accodano tutti i chunk **senza aspettare** (`decode()` a raffica finché
   `decodeQueueSize` < 8), si conta il numero di `VideoFrame` in uscita al secondo a regime, e si
   chiude ogni frame subito (`frame.close()`, obbligatorio: §3.8, la perdita di
   `VTDecoderXPCService`).
   *Il numero che decide*: **≥ 90 fotogrammi/s sostenuti a 3840×2160 Main10 ⇒ hardware.
   ≤ 30 ⇒ software. Fra i due ⇒ verdetto sospeso**, si guardano gli altri numeri.
2. **La canarina di CPU** — il segnale JS più onesto.
   Un secondo `Worker` gira un ciclo aritmetico stretto e conta le iterazioni per 100 ms.
   Si misura *a riposo* (`I₀`) e *durante la decodifica* (`I₁`). Si riporta **`I₁/I₀`**.
   *Il numero che decide*: una decodifica hardware lascia la canarina sopra **0,85**; una
   decodifica software 4K a 10 bit occupa quasi tutti i core e la porta sotto **0,4**.
3. **Latenza uno-dentro-uno-fuori.** Un solo chunk, si attende l'uscita, 200 ripetizioni,
   si riporta la mediana e il 95° percentile. Segnale debole (anche l'hardware ha una pipeline),
   ma il 95° percentile smaschera i cali.
4. **Decadimento su dieci minuti** — ⭐ la firma più difficile da falsificare.
   Si ripete la misura 1 ogni 30 secondi per 10 minuti e si traccia la curva.
   *Il numero che decide*: **portata finale / portata iniziale**. Una decodifica hardware resta
   sopra **0,9**. Una decodifica software su un telefono va in throttling termico e scende sotto
   **0,6** (§3.8, energia software × 13,76 passando a 2160p).
5. **I 10 bit** (sequenza E): rapporto fra il numero di bande contate in E-a-10-bit e in
   E-quantizzata-a-8-bit, sullo stesso canvas. **≈ 1 ⇒ troncato. ≈ 4 ⇒ arrivato.**
6. **Il ground truth, fuori dal browser** — solo su Android.
   Da PC: `chrome://inspect` → debug remoto → **`chrome://media-internals`**, si legge la riga
   `[R]` `Created MediaCodec <nome>, is_software_codec=<bool>`. Se il nome comincia per
   `c2.android.` o `omx.google.`, **è software, punto**.
   `[?]` `adb shell dumpsys media.metrics` dovrebbe dare la stessa informazione; da confermare.
   ⛔ **Su iPhone questo canale non esiste**: Safari Web Inspector non ha un equivalente di
   media-internals. Sull'iPhone il verdetto **poggia interamente sui numeri 1-4**, e questo va
   scritto nel rapporto del banco come limite dichiarato, non nascosto.
7. **I segnali JS, raccolti ma mai creduti da soli**: `isConfigSupported().supported`,
   `MediaCapabilities.decodingInfo(...).powerEfficient`, esito di `configure({prefer-hardware})`,
   `VideoFrame.format`, `VideoFrame.codedWidth/Height`, `navigator.hardwareConcurrency`,
   user agent. Si registrano per costruire la tabella «che cosa avrebbe detto l'API» accanto a
   «che cosa dicono i numeri» — è quella tabella la vera consegna di S2.

### 4.3 ⛔ Come apparirebbe un decodificatore software che finge bene

Va scritto per esteso, perché è il cuore della questione:

| Prova | Un `c2.android.hevc.decoder` la supera? |
|---|---|
| `isConfigSupported()` → `supported: true` | **Sì, sempre** `[R]` §3.1 |
| `configure({prefer-hardware})` riesce | **Sì su Android** `[R]` §3.3 |
| `MediaCapabilities.powerEfficient === true` | **Sì su Android** `[R]` §3.4 — il filtro software manca nel ramo HEVC |
| Produce `VideoFrame` corretti, senza errori | **Sì** |
| Latenza uno-dentro-uno-fuori accettabile a 1080p | **Probabilmente sì** `[?]` |
| **Portata ≥ 90 fps a 4K Main10** | **No** `[?]` — è un ordine di grandezza fuori portata per una CPU di telefono |
| **Canarina di CPU sopra 0,85** | **No** `[?]` — la decodifica software prende tutti i core |
| **Portata stabile su 10 minuti** | **No** `[?]` — throttling termico, §3.8 |

⭐ **La conclusione operativa**: le prime cinque righe sono tutte «sì». **Chi si ferma lì ripete
esattamente l'errore della v1**, questa volta con il conforto apparente di un'API che dice
`prefer-hardware`. Il banco deve girare **al carico bersaglio** (4K60 Main10) e **per minuti**,
perché è solo lì che le ultime tre righe diventano «no».

### 4.4 ⭐ Il controllo positivo: come so che il banco vedrebbe il software

Il banco deve dimostrare di discriminare **in tutte e due le direzioni**, sullo stesso telefono,
nella stessa pagina, con lo stesso codice di misura.

**Controllo A — falso negativo (il banco riconosce il software?).**
Si decodifica la sequenza **D** (VP9 Profile 0) con `hardwareAcceleration: 'prefer-software'`.
`[R]` Questa combinazione è **software garantito per costruzione**: `video_decoder_broker.cc:204-209`
mostra che con `kPreferSoftware` la fabbrica esterna non viene nemmeno creata, e resta la sola
`DefaultDecoderFactory`, cioè libvpx compilato dentro Chromium.
👉 **Il banco deve dichiarare questo caso «software».** Se non ci riesce — se la canarina resta alta
e la portata pure — il banco è cieco, e il suo «hardware» su HEVC va buttato.
`[?]` Su Safari `prefer-software` potrebbe essere ignorato (la specifica lo permette): in quel caso
il controllo A su iPhone va fatto con **AV1 4K60 su un iPhone senza decodificatore AV1**
(pre-A17 Pro), che `[S]` non ha ripiego software Apple e quindi **fallisce del tutto** —
un fallimento è comunque un esito dichiarabile.

**Controllo B — falso positivo (il banco non chiama hardware tutto?).**
La stessa sequenza **D**, ma con `prefer-hardware`. VP9 8 bit 1080p ha un decodificatore hardware su
praticamente ogni telefono.
👉 **Il banco deve dichiarare questo caso «hardware».** Se dichiara software anche questo, la sua
soglia è tarata male e sta solo misurando un telefono lento.

**Controllo C — la trappola della v1, verificata sul campo.**
Su Android, sequenza **A** con `prefer-hardware`, **e in parallelo** la lettura di
`is_software_codec` da media-internals (§4.2 punto 6).
👉 Se **anche un solo dispositivo** mostra `is_software_codec=true` mentre `prefer-hardware` è
riuscito, è la conferma sul campo del `[R]` di §3.3, e va scritta in `DECISIONI.md` come fatto
misurato del progetto, non come curiosità.

**Il criterio di validità del banco, in una riga**: *il banco è valido se, sullo stesso telefono,
dichiara software il controllo A e hardware il controllo B.* Finché non lo fa, non pubblica verdetti.

---

## 5. Che cosa decide questa risposta

| Esito di S2 | Che cosa cambia nel prodotto |
|---|---|
| **A — HEVC Main10 4K60 in hardware su Chrome Android e Safari iOS** | Il traguardo è confermato. Il server resta su `hevc_vaapi` Main10, il client parla solo HEVC. Resta comunque da chiudere §3.7: che i 10 bit non siano troncati **dopo** il decodificatore. |
| **B — hardware sì, ma i 10 bit escono troncati a 8** | Si declassa a **Main 8 bit** sul telefono e si tengono i 10 bit solo dove sono verificabili (desktop). Si dichiara il limite in `SPECIFICHE.md` — non è un difetto nostro, è un fatto del percorso. Costo per noi: `hevc_vaapi` deve saper produrre entrambi i profili a runtime. |
| **C — su una fascia di telefoni è software** | Serve un **negoziato all'avvio**: il client esegue una versione ridotta del banco §4 (10-15 secondi, sequenza C invece che A), dichiara il proprio profilo misurato, e il server scala risoluzione, cadenza e profondità. ⭐ **Questo è il vero rimedio all'errore della v1**: non è una diagnosi da fare una volta in laboratorio, è **una autodiagnosi che vive nel prodotto**. |
| **D — Safari non regge l'Annex-B, o Chromium rifiuta `hev1`** | Il server deve saper produrre **entrambe** le forme: Annex-B così com'è, e hvcC costruito a mano (con la de-emulazione del PTL, §3.5). È lavoro noto, ~60 righe di C, con `mediabunny/src/codec-data.ts:1462` come riferimento. Il client prova le configurazioni in ordine, come fa moonlight-web. |
| **E — nemmeno HEVC hardware su una parte del parco** | Si aggiunge **H.264** come piano di riposo: `[S]` copertura di campo ≈ 99,94% in decodifica, e `hevc_vaapi` ha il gemello `h264_vaapi` sullo stesso silicio. Si perde il 10 bit (H.264 High10 non è decodificato in hardware quasi da nessuno `[?]`), si perde efficienza, si conserva il prodotto. |
| **Trasversale, in ogni esito** | ⭐ **AV1 è chiuso** (§3.9): non lo codifichiamo e su Android sarebbe software. Non va tenuto nel piano nemmeno come opzione. |
| **Trasversale, in ogni esito** | ⭐ Se il client tiene aperto un `RTCDataChannel` per l'input, **rientra nell'esenzione dal congelamento** di Chrome (§3.8). Questa è una decisione di architettura che va presa *adesso*, non quando ci accorgeremo che la sessione muore dopo cinque minuti. |
| **Trasversale, in ogni esito** | ⭐ L'abbandono selettivo di fotogrammi (§3.6) **non è gratis**: senza sotto-livelli temporali ogni fotogramma abbandonato costa un IDR. Da verificare su `EncSliceLP` della UHD 730 prima di scrivere la logica di scarto. |

---

## 6. Le fonti

**Specifiche W3C**
- WebCodecs — https://www.w3.org/TR/webcodecs/ · editor's draft https://w3c.github.io/webcodecs/
- HEVC (H.265) WebCodecs Registration — https://www.w3.org/TR/webcodecs-hevc-codec-registration/
- AVC (H.264) WebCodecs Registration — https://www.w3.org/TR/webcodecs-avc-codec-registration/
- AV1 WebCodecs Registration — https://www.w3.org/TR/webcodecs-av1-codec-registration/
- Media Capabilities — https://www.w3.org/TR/media-capabilities/
- AV1 ISOBMFF (stringa codec) — https://aomediacodec.github.io/av1-isobmff/
- AV1 livelli — https://github.com/AOMediaCodec/av1-spec/blob/master/annex.a.levels.md

**Discussioni e issue di specifica**
- Esporre o no `HardwareAcceleration` (w3c/webcodecs#239) — https://github.com/w3c/webcodecs/issues/239
- 10 bit YUV e accesso ai pixel (w3c/webcodecs#631) — https://github.com/w3c/webcodecs/discussions/631
- Supporto HDR (w3c/webcodecs#384, aperta) — https://github.com/w3c/webcodecs/issues/384
- Punti di ripristino SEI (w3c/webcodecs#650) — https://github.com/w3c/webcodecs/issues/650
- Reclamation dei codec in background (#889, #363) — https://github.com/w3c/webcodecs/issues/889
- 1-dentro-1-fuori (#732) — https://github.com/w3c/webcodecs/issues/732

**Sorgente Chromium** (branch `main`, scaricato il 9 agosto 2026)
- `third_party/blink/renderer/modules/webcodecs/video_decoder.cc` — https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/modules/webcodecs/video_decoder.cc
- `third_party/blink/renderer/modules/webcodecs/video_decoder_broker.cc` — https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/modules/webcodecs/video_decoder_broker.cc
- `third_party/blink/renderer/modules/webcodecs/decoder_template.cc`
- `third_party/blink/renderer/modules/media_capabilities/media_capabilities.cc`
- `media/gpu/android/media_codec_video_decoder.cc` — https://github.com/chromium/chromium/blob/main/media/gpu/android/media_codec_video_decoder.cc
- `media/base/android/media_codec_util.cc`

**Sorgente WebKit** (branch `main`)
- `Source/WebCore/Modules/webcodecs/WebCodecsVideoDecoder.cpp` — https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/webcodecs/WebCodecsVideoDecoder.cpp
- Commit `8555adf` (Annex-B HEVC, `nalu_rewriter.cc`) — https://github.com/WebKit/WebKit/commit/8555adfc8a29c5d85caff1f9d6c7f9c0dc8eb0b2
- Bug 262950 — https://bugs.webkit.org/show_bug.cgi?id=262950

**Progetti di riferimento**
- Xpra html5 — https://github.com/Xpra-org/xpra-html5/blob/master/html5/js/VideoDecoder.js e `.../Client.js`
- Tango ADB / scrcpy — https://tangoadb.dev/scrcpy/video/web-codecs/ · https://github.com/yume-chan/ya-webadb/blob/main/libraries/scrcpy-decoder-webcodecs/src/video/codec/h26x.ts
- moonlight-web — https://github.com/linckosz/moonlight-web/blob/main/frontend/js/util/Mp4Muxer.js
- mediabunny (hvcC conforme) — https://github.com/Vanilagy/mediabunny/blob/main/src/codec-data.ts
- mpv-android issue #462 (10 bit troncati) — https://github.com/mpv-android/mpv-android/issues/462

**Matrici di supporto e dati di campo**
- StaZhu, *enable-chromium-hevc-hardware-decoding* — https://github.com/StaZhu/enable-chromium-hevc-hardware-decoding
- WebCodecs Fundamentals, dataset 2026 (363 M prove, 1,14 M sessioni) — https://webcodecsfundamentals.org/datasets/codec-analysis-2026/
- WebCodecs Fundamentals, HEVC — https://webcodecsfundamentals.org/codecs/hevc.html
- MDN, parametro `codecs` (grammatica HEVC) — https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/codecs_parameter
- MDN, `VideoFrame.format` — https://developer.mozilla.org/en-US/docs/Web/API/VideoFrame/format
- MDN, `VideoDecoder.configure()` — https://developer.mozilla.org/en-US/docs/Web/API/VideoDecoder/configure
- WebKit Features in Safari 16.4 — https://webkit.org/blog/13966/webkit-features-in-safari-16-4/
- WebKit Features in Safari 26.0 — https://webkit.org/blog/17333/webkit-features-in-safari-26-0/
- Firefox 130 (WebCodecs desktop) — https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/130
- Bugzilla 1944991 (H265 WebCodecs macOS), 1949917 (H265 WebCodecs Linux)
- Intent to Ship: HEVC in WebRTC, Chrome 136 — https://groups.google.com/a/chromium.org/g/blink-dev/c/3h8lL8a377c

**Piattaforma**
- Android 16 CDD — https://source.android.com/docs/compatibility/16/android-16-cdd
- `MediaCodecInfo.VideoCapabilities` — https://developer.android.com/reference/android/media/MediaCodecInfo.VideoCapabilities
- Chrome, background tabs — https://developer.chrome.com/blog/background_tabs
- Chrome, Freezing on Energy Saver — https://developer.chrome.com/blog/freezing-on-energy-saver
- DevTools Media panel — https://developer.chrome.com/docs/devtools/media-panel
- Chromium, hardware decode su Linux — https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/linux/hw_video_decode.md
- Energia decodifica HEVC hardware vs software — https://www.sciencedirect.com/science/article/abs/pii/S1383762121000199
- WebCodecs/WebTransport vs WebRTC — https://webrtchacks.com/webcodecs-webtransport-and-webrtc/
- GeForce NOW e AV1 — https://nvidia.custhelp.com/app/answers/detail/a_id/5824

---

## 7. Che cosa non ho verificato — dichiarato

Distinzione obbligatoria fra «non l'ho trovato» e «ho verificato che non c'è».

**Ho verificato che non c'è** (con controllo positivo):
- Nessuna API JS espone se il decodificatore è hardware. Controllo positivo: il dato *esiste* in
  Chromium (`IsPlatformDecoder()`, `GetDecoderType()`, letti in `video_decoder_broker.cc:271-272`)
  ma non è esposto in nessun IDL.
- Xpra html5 non usa `description` e non supporta HEVC. Controllo positivo: grep di `description`
  su `html5/js/*.js` → 0; grep di `hevc|h265|hvc1|hev1` su tutto il repo → 1 riga, un colore di
  debug in `Constants.js:19`.
- Tango/scrcpy non costruisce hvcC/avcC. Controllo positivo: grep di `description:` sui `.ts` → 0;
  grep di `hvcC|avcC` → 2 stringhe letterali di prefisso codec.
- `P010` non è un valore di `VideoPixelFormat`. Controllo positivo: l'enumerazione contiene
  `I420P10` e `I420P12`, quindi i formati a 10 bit ci sono — `P010` specificamente no.

**Non l'ho trovato** (assenza non dimostrata):
- Lo stato preciso, ad agosto 2026, dell'esposizione di `I420P10` per fotogrammi decodificati in
  hardware in Chrome. L'ultima fonte datata è del 2023 e l'issue #384 risulta aperta.
- Una tabella Apple che dichiari il livello HEVC massimo per modello di iPhone.
- Come WebKit calcoli `powerEfficient` in `MediaCapabilities`.
- Se Chromium accetti il prefisso `hev1.` con Annex-B in WebCodecs (lo accetta WebKit `[R]`; per
  Chromium l'ho dedotto dalla prassi di Xpra e Tango con `avc1.`, non letto).
- Il comportamento di `VideoDecoder` su iOS quando la scheda va in background.
- Se `EncSliceLP` sulla UHD 730 sappia produrre sotto-livelli temporali (§3.6).
