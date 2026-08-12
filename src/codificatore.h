/*
 * codificatore.h — dal fotogramma catturato ai byte che un browser decodifica.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COS'E', E CHE COSA NON E'
 *
 * E' il terzo anello della fase 2 (`fasi/02-primo-fotogramma.md`): prende i
 * pixel che la cattura consegna e produce **un flusso che F2.4 mette sul filo e
 * F2.5 da' a `VideoDecoder`**.
 *
 * ⛔ **In software, di proposito.**  L'accelerazione e' la fase 8, e metterla
 *    prima significherebbe non sapere quale dei due pezzi sbaglia
 *    (`PIANO.md` §«Fase 2»).  Qui non si tocca ne' VA-API ne' QSV ne' NVENC.
 *
 * ⛔ **E questo file NON e' `codificatore.c` di v1 riportato.**  Quello e' un
 *    codificatore H.264/AVC420 per RDP: 889 righe, **77** nominano H.264/AVC,
 *    **47** nominano RDP/FreeRDP, e *HEVC*, *265*, *10 bit* compaiono **zero**
 *    volte (`[M]`, `fasi/rapporti/F2-3-codifica.md` §4.1).  Di quel file
 *    sopravvive **la forma** — il componente chiesto per nome, il divieto di
 *    ripiego silenzioso, il conto dei tempi, il divieto di `GLOBAL_HEADER` — e
 *    quasi nessuna riga.  E' la decisione **D5** di `fasi/02-primo-fotogramma.md`.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ I CODEC SONO DUE, E LO SONO PER DECISIONE DELL'UTENTE
 *
 * `DECISIONI.md` §1.13, 12 agosto 2026, presa davanti alla misura:
 *
 *     | `[M]` F2.5     | Chrome, GPU | Chrome, senza GPU | Firefox |
 *     |----------------|-------------|-------------------|---------|
 *     | **HEVC Main10**| 8 celle / 8 | ⛔ zero            | ⛔ zero  |
 *     | **AV1 8 e 10** | 8 / 8       | ⭐ 8 / 8           | ⭐ 8 / 8 |
 *
 * ⇒ HEVC **non arriva al pixel su Firefox**, e su Chrome esiste **solo via
 *   VA-API** (con `prefer-software` Chrome dice `Unsupported`).  AV1 dipinge su
 *   tutte e quattro le caselle **anche in software**.
 *
 * ⛔ Da cui: **non si dichiara un requisito** *«serve Chrome con VA-API»*.  Il
 *    codec **si negozia** (`RCP.md` §4.3, capacita' `video.codec`) e **il
 *    ripiego si dichiara** (`CODER.md` §4.2).  L'ordine di preferenza resta
 *    **`hevc,av1`**: HEVC e' ancora il primo, perche' e' quello che il telefono
 *    decodifica in hardware.
 *
 * ⛔ Il numero che finisce nell'intestazione del fotogramma (`RCP.md` §6.2,
 *    campo `codec`) e' **1 = HEVC, 2 = AV1**, ed e' proprio il valore di
 *    `CodecVideo` qui sotto: un'enumerazione che non coincide col protocollo
 *    obbliga a una tabella di conversione, e una tabella di conversione e' un
 *    posto dove sbagliare in silenzio.
 *
 * ---------------------------------------------------------------------------
 * ⛔ LA FORMA DEI BYTE, CHE E' UNA DECISIONE E NON UN DETTAGLIO
 *
 * Decisione **D1** (`fasi/02-primo-fotogramma.md`, quattro ragioni lette in
 * `F2-3-codifica.md` §3.2): **Annex-B puro, e NESSUNA `description`**.
 *
 *     [00 00 00 01] VPS (32)
 *     [00 00 00 01] SPS (33)      ← profilo 2 = Main10, bit_depth = 10
 *     [00 00 00 01] PPS (34)
 *     [00 00 01]    PREFIX_SEI (39)
 *     [00 00 01]    IDR_N_LP (20) ← il primo fotogramma e' SEMPRE una chiave
 *
 * ⛔ In concreto, e in questo file: **non si accende mai
 *    `AV_CODEC_FLAG_GLOBAL_HEADER`** — e non ci si fida di non averlo acceso:
 *    `codificatore_nuovo()` **verifica** che sia spento dopo l'apertura, e
 *    `codificatore_comprimi()` verifica **sui byte** che i parameter set siano
 *    davanti a ogni chiave.  E' lo stesso divieto che v1 aveva gia' pagato
 *    (`v1/remotix-c/src/codificatore.c:268-272`, *«su RDP i parametri di
 *    sequenza devono viaggiare NEL flusso, davanti all'IDR»*): li' la ragione
 *    era RDP, qui e' `VideoDecoder`, e il **sintomo e' identico** — schermo nero
 *    con i fotogrammi che arrivano.
 *
 * ⚠ Per **AV1** non si pone: non esiste un `hvcC`, e le unita' temporali di OBU
 *   si spediscono cosi' come sono (`DECISIONI.md` §1.13: *«nessuna
 *   description: una cucitura in meno»*).  Quel che si verifica e' l'analogo:
 *   la **sequence header OBU** davanti a ogni fotogramma chiave.
 *
 * ---------------------------------------------------------------------------
 * ⚠ E LA COSA CHE VA DETTA PRIMA DI TUTTO IL RESTO: OTTO BIT, NON DIECI
 *
 * `[M]` 12 agosto 2026, F2.2: **Mutter consegna solo BGRx/BGRA**, cioe' **8 bit
 * per canale** (255/256/255 livelli distinti, multipli di 4 a 0,259/0,259/0,249
 * — otto bit veri, tutti e otto).
 *
 * ⇒ ⛔ **Main10 da questa strada sono otto bit PROMOSSI a dieci**, e l'etichetta
 *   del flusso continua a dire «10 bit» per tutta la catena — che e' esattamente
 *   il guasto **F2.3-A** che il banco riproduce.  `SPECIFICHE.md` §3.1 mette i
 *   10 bit nel **desiderato**, e da questa sorgente **non e' raggiungibile**.
 *
 * ⛔ Da cui `confessione.promozione_8_a_10`: la promozione **si dichiara**, e
 *    finisce nel registro alla prima codifica.  `DECISIONI.md` §2.7 riga 2 —
 *    *«un ripiego silenzioso resta vietato anche quando la colpa non e'
 *    nostra»*.  Un codificatore che tacesse produrrebbe due misure sotto la
 *    stessa etichetta, che e' la forma **E2** di `REVIEWER.md` §2.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E2 — IL COMPONENTE CHE DECIDE DA SE': SI CHIEDE PER NOME, E SI VERIFICA
 *
 * `CODER.md` §3.9.  E la riga che v1 aveva scritto dopo averlo pagato
 * (`v1/remotix-c/src/codificatore.c:550-566`):
 *
 *     ⛔ *«CHIESTO PER NOME, NESSUN RIPIEGO.  Chi indica un codificatore sta
 *        misurando: ripiegare su un altro darebbe due misure diverse con la
 *        stessa etichetta, che e' peggio di non misurare.»*
 *
 * Qui la regola vale **due volte**, perche' i modi di disobbedire misurati il
 * 12 agosto 2026 sono due e nessuno dei due grida:
 *
 *   ⛔ `-c:v hevc` invece di `libx265` lascia scegliere a libavcodec, che ha
 *      cinque codificatori HEVC in canna — e quattro sono in hardware, cioe'
 *      la fase 8 entrata di soppiatto nella fase 2;
 *   ⛔ `[M]` **libsvtav1 ignora un'opzione che non conosce e continua**:
 *      `-svtav1-params pippo=1` stampa *«Error parsing option»* ed **esce 0**.
 *      Un'opzione chiesta e non applicata ha lo stesso aspetto di un'opzione
 *      applicata.
 *
 * ⇒ Da cui i **due testimoni** di `codificatore_confessione()`, e il secondo non
 *   dipende dal primo:
 *
 *     il contesto  quel che `libavcodec` dice di aver aperto (nome del
 *                  componente, formato dei pixel, profilo, fotogrammi B)
 *     ⭐ I BYTE     quel che c'e' scritto **nel flusso**: l'SPS di HEVC e la
 *                  sequence header OBU di AV1 si leggono e si confrontano con
 *                  quel che si era chiesto.  Non e' una deduzione: e' il
 *                  prodotto che si rilegge.
 *
 * ⭐ E dai byte esce anche **il livello**, che serve e non si indovina:
 *    `RCP.md` §4.3 dice che il server **DEVE** emettere un flusso di livello non
 *    superiore a quello dichiarato dal client, e ⛔ `[M]` F2.5 ha misurato che
 *    **il browser non lo controlla** (Chrome accetta `L30` su un flusso di
 *    livello 3.0 e dipinge lo stesso) ⇒ decisione **D4**: *il controllo del
 *    livello sta dal lato server*.  Qui.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL RITARDO, E I DUE DEFAULT CHE NESSUNO AVEVA CHIESTO
 *
 * `SPECIFICHE.md` §3.2: **50 ms di tetto**, e `CODER.md` §1-bis — *«il ritardo
 * pesa piu' dei fotogrammi»*.  `[M]` 12 agosto 2026, letti nella confessione dei
 * due codificatori:
 *
 *     x265        `bframes=4` e `open-gop`   — nessuno li aveva chiesti
 *     SVT-AV1     `pred struct: random access` — idem
 *
 * Tutti e due comprano compressione **vendendo risposta**: un fotogramma che
 * aspetta il successivo e' un fotogramma di ritardo in piu'.  ⛔ Vanno
 * **decisi, non ereditati** — e qui si decide `bframes=0`, `open-gop=0`,
 * `pred-struct=1`, con la ragione accanto a ciascuno in `codificatore.c`.
 *
 * ⭐ E la verifica non e' l'opzione: e' **`dts == pts` su ogni pacchetto**.  Un
 *    codificatore che riordina lo dichiara li', qualunque cosa abbia fatto delle
 *    opzioni che gli abbiamo passato — ed e' un testimone che vale identico per
 *    tutt'e due i codec.
 */
#ifndef REMOTIX_CODIFICATORE_H
#define REMOTIX_CODIFICATORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ⛔ I valori sono quelli di `RCP.md` §6.2, campo `codec`: non si convertono. */
typedef enum {
	CODIFICATORE_HEVC = 1,
	CODIFICATORE_AV1 = 2,
} CodecVideo;

/*
 * Il formato dei pixel in ingresso.
 *
 * ⚠ Sono due perche' i due ingressi VERI del progetto sono due, e non per
 *   generalita': `BGRX` e' quel che consegna la cattura di GNOME (F2.2, `[M]`
 *   BGRx a 8 bit, stride 7680 letto dal manifesto), `YUV420P10LE` e' quel che
 *   consegna il banco — un'immagine nota gia' in YCbCr, che permette di misurare
 *   il codificatore **senza** misurare insieme la conversione di colore.
 */
typedef enum {
	CODIFICATORE_PIXEL_BGRX,       /* 4 byte per pixel, B G R x */
	CODIFICATORE_PIXEL_YUV420P10LE /* tre piani, 2 byte per campione */
} FormatoPixel;

/*
 * Come si chiede la qualita'.
 *
 * ⛔ `LOSSLESS` non e' un vezzo: e' l'unico regime in cui i **10 bit veri** si
 *    distinguono dai 10 bit dichiarati.  A un bitrate realistico HEVC distrugge
 *    una rampa a 1 LSB **per costruzione**, e un conteggio basso non
 *    distinguerebbe *«la catena e' a 8 bit»* da *«il bitrate era basso»*: due
 *    diagnosi opposte sotto la stessa etichetta (`F2-3-codifica.md` §2.4).
 */
typedef enum {
	CODIFICATORE_QUALITA_LOSSLESS, /* ⚠ HEVC si'; AV1 vedi la nota in .c */
	CODIFICATORE_QUALITA_CRF,      /* qualita' costante, `valore` = CRF */
} ModoQualita;

typedef struct {
	CodecVideo codec;
	/*
	 * ⛔ Il componente si chiede PER NOME e non si ripiega.
	 * NULL = il nome predefinito per quel codec in fase 2 (`libx265` /
	 * `libsvtav1`), che e' comunque un nome e non una scelta di libavcodec.
	 */
	const char *componente;
	uint32_t larghezza, altezza;
	uint32_t fotogrammi_al_secondo;
	ModoQualita modo;
	int qualita;                 /* CRF, quando `modo` e' CRF */
	int profondita;              /* 8 o 10 — quel che si CHIEDE al codificatore */
	FormatoPixel formato;
	/*
	 * Chiavi periodiche ogni N fotogrammi; **0 = solo su richiesta**.
	 * ⚠ Lo zero e' la scelta della fase 2 e la ragione sta in `RCP.md` §5.2:
	 *   le chiavi si chiedono (`RICHIEDI_CHIAVE`), e mandarne a orologio su una
	 *   linea cattiva e' *«la spirale»* che quel paragrafo vieta.  Il punto di
	 *   lavoro e' della fase 9.
	 */
	uint32_t chiavi_ogni;
} CodificatoreRichiesta;

/*
 * ⭐ LA CONFESSIONE — quel che il codificatore ha fatto DAVVERO.
 *
 * ⛔ I campi `*_flusso` sono letti **dai byte prodotti**, non dagli argomenti
 *    che gli abbiamo passato: sono il secondo testimone di E2, e sono l'unico
 *    che sopravvive a un componente che ignora un'opzione senza dirlo.
 */
typedef struct {
	CodecVideo codec;
	const char *componente;       /* il nome vero, chiesto a libavcodec */
	bool ha_obbedito;             /* ⛔ falso ⇒ non si spedisce niente */
	char perche_no[256];          /* la ragione, quando non ha obbedito */

	/* dal contesto */
	int profondita_chiesta;
	int fotogrammi_b;
	bool global_header;           /* ⛔ deve essere falso, sempre */

	/* ⭐ dai BYTE del flusso */
	bool letto_dal_flusso;
	int profondita_flusso;        /* bit per campione, dall'SPS / seq header */
	int profilo_flusso;           /* HEVC: profile_idc · AV1: seq_profile */
	int livello_flusso;           /* HEVC: general_level_idc · AV1: seq_level_idx */
	bool tier_alto;               /* HEVC: general_tier_flag · AV1: seq_tier */
	uint32_t larghezza_flusso, altezza_flusso;
	int croma_flusso;             /* 1 = 4:2:0 */
	char stringa_codec[64];       /* `hev1.2.4.L93.B0` / `av01.0.04M.10` */

	/* ⚠ la promozione, dichiarata invece che subita */
	bool promozione_8_a_10;

	/* ⚠ il ritardo, misurato invece che dedotto */
	bool riordina;                /* un pacchetto con dts != pts */
	uint32_t fotogrammi_in_volo;  /* quanti ne ha trattenuti prima del primo */
} CodificatoreConfessione;

/* Un fotogramma pronto da spedire.  I byte appartengono al codificatore fino a
 * `codificatore_rilascia()`. */
typedef struct {
	const uint8_t *dati;
	size_t byte;
	bool chiave;                  /* `RCP.md` §6.2: 0x0301 chiave, 0x0302 delta */
	uint64_t us_conversione;      /* ⭐ i tre tempi separati: senza, «il ritmo e' */
	uint64_t us_codifica;         /*    calato» non si attribuisce a niente */
	uint32_t ricodifiche;         /* ⛔ >0 ⇒ il tetto dei 16 MiB ha morso */
	bool trattenuto;              /* ⚠ il codificatore non l'ha consegnato subito */
} CodificatoreFotogramma;

typedef struct Codificatore Codificatore;

/*
 * Apre il codificatore, o **fallisce dicendo perche'**.
 *
 * ⛔ Non ripiega mai: ne' su un altro componente, ne' su un altro profilo, ne'
 *    su 8 bit.  Un ripiego silenzioso darebbe due misure sotto la stessa
 *    etichetta (`CODER.md` §3.9, §4.2 seconda meta').
 */
Codificatore *codificatore_nuovo(const CodificatoreRichiesta *richiesta,
                                 char *errore, size_t errore_byte);
void codificatore_libera(Codificatore *cod);

/* Per il registro: «HEVC Main10 via libx265 (in software)». */
const char *codificatore_nome(const Codificatore *cod);

/* ⭐ Vale dopo il primo `codificatore_comprimi()` per i campi letti dai byte. */
const CodificatoreConfessione *codificatore_confessione(const Codificatore *cod);

/*
 * Comprime un fotogramma.
 *
 * `pixel` e `passo` sono quel che consegna la cattura: ⛔ il passo si passa, non
 * si calcola come `larghezza × 4` — F2.2 lo legge dal manifesto di PipeWire e
 * dice di fare altrettanto anche quando oggi coincide.
 *
 * Restituisce `false` e non consegna niente se il codificatore non ha obbedito,
 * se il fotogramma supera i 16 MiB anche dopo le ricodifiche (`RCP.md` §6.2), o
 * se la forma dei byte non e' quella promessa a F2.5.
 */
bool codificatore_comprimi(Codificatore *cod, const uint8_t *pixel, uint32_t passo,
                           CodificatoreFotogramma *fuori);
void codificatore_rilascia(Codificatore *cod);

/*
 * ⛔ La prossima codifica sara' una chiave VERA — coi parameter set davanti.
 *
 * Serve a `RICHIEDI_CHIAVE` (`RCP.md` §7.1) e a ogni abbandono di un delta
 * (§5.2: *«il server DEVE mandare una chiave appena puo', senza aspettare che il
 * client la chieda»*).
 */
void codificatore_chiedi_chiave(Codificatore *cod);

/*
 * ⛔ Il cambio di tela: si riapre alla misura nuova, e il primo fotogramma dopo
 *    e' una **chiave vera**.
 *
 * `RCP.md` §5.2, riga entrata la sera del 12 agosto 2026 con la misura accanto:
 * su HEVC in Chrome un delta alla misura nuova **non solleva niente** — il
 * decodificatore continua a emettere fotogrammi alla misura **vecchia** e
 * dipinge un'immagine sfasciata, diversa a ogni giro.  ⇒ Il sintomo sarebbe
 * *«il desktop si strappa quando ridimensiono la finestra»*, e non nominerebbe
 * ne' il protocollo ne' la tela.
 */
bool codificatore_ridimensiona(Codificatore *cod, uint32_t larghezza, uint32_t altezza,
                               char *errore, size_t errore_byte);

#endif
