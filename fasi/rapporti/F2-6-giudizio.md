# F2.6 — Il giudizio: i pixel a confronto, e la sonda sul dispositivo vero

*Aperta e consegnata il 12 agosto 2026. Sotto-fase di «Fase 2 — Il primo fotogramma».
Mandato: `fasi/rapporti/MANDATO-12-agosto-fase2.md`. Porta assegnata: **7516**.*

⛔ **Questo giro non ha scritto una riga di prodotto.** `src/` non è stato toccato: è il giro
del banco prima del prodotto (`MANDATO` §1, `PIANO.md` §0.4 momento 1).

---

## Che cosa deve produrre

**Il metro della fase 2**: lo strumento che dice se il fotogramma dipinto sulla tela è quello
catturato dal desktop — **i pixel**, non «il programma non è crollato» — e la sonda che chiede al
**dispositivo vero** se decodifica HEVC Main10 in hardware e che profondità restituisce.

**Che cosa misura il banco**: dodici guasti che il metro **deve** bocciare, ciascuno con lo
strumento che lo deve prendere, e il conto — misurato — di quanti di essi un PSNR da solo
promuoverebbe.

---

## ⛔ Il metro — la grandezza, la soglia, la ragione della soglia

### Il problema, scritto prima della soluzione

La codifica è **con perdita**. Questo mette il metro fra due criteri che sono tutti e due inutili:

| | |
|---|---|
| **«identici»** | fallisce **sempre**, anche a catena perfetta. Un metro che boccia sempre non viene guardato da nessuno dopo la seconda volta |
| **«si somigliano»** | non fallisce **mai**. ⛔ Un metro che promuove tutto non è un metro: è un verde che dà fiducia, cioè la cosa che `REVIEWER.md` §1 dichiara peggiore di nessuna misura |

### ⭐ La soluzione: due piani, e la perdita sta tutta in uno solo

La perdita è del **codificatore**, che è un anello che questa fase non sta giudicando. Quel che la
fase 2 giudica è la catena **dal byte al pixel dipinto**. E su quella la perdita ammessa non è
«poca»: è **zero**, perché **la decodifica HEVC è normativa** — due decodificatori conformi, dato
lo stesso flusso, producono lo stesso YUV.

| Piano | Che cosa confronta | Perdita ammessa |
|---|---|---|
| **1 — la catena senza perdita** | `pagina` ⟷ `riferimento` (lo stesso flusso decodificato da **ffmpeg**) | solo la conversione di colore e l'arrotondamento a 8 bit della tela ⇒ **soglia stretta** |
| **2 — la catena intera** | `pagina` ⟷ `cattura`, **meno** `riferimento` ⟷ `cattura` | ⭐ è una **differenza**: la perdita del codificatore si cancella e la soglia si tara da sé sul QP che sceglie F2.3 |

⭐ E il `riferimento` è il **secondo lettore** che `PIANO.md` §0.4 dice che ci manca: ffmpeg è
scritto da gente che non ci conosce. Se il nostro server e la nostra pagina condividessero lo
stesso fraintendimento, questo confronto lo vedrebbe e nessun altro banco della fase lo vedrebbe.

### Gli strumenti, le soglie, e la ragione di ciascuna

| # | Grandezza | Soglia | La ragione, e non è «mi sembra giusto» |
|---|---|---|---|
| **M-V** | vitalità della scena: deviazione di Y, livelli distinti, **e i 4 marcatori d'angolo al loro posto** | dev ≥ 0,02 · ≥ 32 livelli · marcatori: **nessuna soglia**, è un confronto | separa «c'è un'immagine» da «non c'è niente». ⛔ **È una porta, e viene prima di tutto** |
| **M-C** | matrice, gamma e primarie **dichiarate** da cattura, codifica, riferimento e pagina | devono coincidere fra chi scrive e chi legge | ⛔ un confronto fatto con la matrice sbagliata **misura la matrice** (cucitura F2.3) |
| **M0** | allineamento: il migliore fra 25 scorrimenti in [−2,+2] | dev'essere **(0,0)**, con ≥ 3 dB sul secondo | ⭐ **relativo**: nessun numero magico in dB, quindi regge a qualunque QP |
| **M1a** | PSNR-Y(pagina, riferimento) | ≥ **45 dB** | la decodifica è normativa e Y non è toccata dal ricampionamento della crominanza: resta solo l'arrotondamento a 8 bit della tela. ±0,5 LSB ⇒ RMSE 0,29 ⇒ **≈ 59 dB**; un LSB pieno ⇒ **≈ 48 dB**. 45 lascia margine e boccia tutto il resto |
| **M1b** | PSNR-RGB(pagina, riferimento) | ≥ **38 dB** | qui entra il ricampionamento 4:2:0, che i decodificatori fanno con filtri **legittimamente diversi**. È la soglia più lasca, e non è quella che porta il verdetto |
| **M2** | PSNR(pagina,cattura) − PSNR(riferimento,cattura) | ≥ **−0,5 dB**, e **applicabile** solo se la perdita del codificatore sta ≥ 10 dB sotto il fondo della tela | ⭐ è una differenza: il QP si cancella. I 10 dB non sono a occhio, sono **legati** alla soglia: Δ atteso = −10·log₁₀(1+10^(−m/10)), che a m=6 dB vale −0,97 (un rosso su catena sana) e a m=10 vale −0,41 |
| **M3** | PSNR-Y del **blocco 64×64 peggiore** | ≥ **30 dB** | un blocco è 1/506 dell'immagine: può essere spazzatura pura e spostare il PSNR globale di **0,03 dB**. La media lo annega |
| **M4** | errore quadratico fra canali, **sui tre riquadri a luminanza uguale** | il proprio dev'essere ≥ **4×** migliore del miglior altro | nessuna soglia assoluta, è un confronto. ⛔ E si misura **solo dove il segnale esiste** (vedi sotto) |
| **M5** | guadagno e scarto per canale (minimi quadrati) | guadagno ∈ [0,98; 1,02] · scarto ≤ 2/255 | prende la gamma limitata letta come piena, che è un guadagno di **255/219 = 1,164** — dodici volte fuori soglia — e la matrice sbagliata, che sposta gli scarti in versi diversi |
| **M6** | PSNR(pagina, cattura ora) − PSNR(pagina, cattura prima) | ≥ **+3 dB** | relativo. ⛔ Pretende che **la scena sia cambiata**: `CODER.md` §3.2 diventa una condizione di validità invece di un consiglio |
| **M7** | i **due bit bassi** del piano Y decodificato, **sulle zone sfumate** | casella più piena ≤ **0,50** e tutte e quattro ≥ 0,05 | 0,50 è **il confine esatto** fra «almeno tre caselle portano informazione» e «al massimo due», che è la firma aritmetica del troncamento |
| **M8** | l'identità del fotogramma dichiarata dalla pagina (FIN / RESET / giro) | nessun RESET su un fotogramma dipinto | cucitura F2.4. ⛔ Anello **debole per costruzione**: crede a chi è sotto esame, e vale solo insieme al registro di F2.4 |

### ⛔ L'elenco dei guasti che il metro DEVE bocciare — e chi li prende

⭐ **Questa tabella è il cuore della sotto-fase**, ed è scritta prima delle soglie apposta: la
colonna di mezzo dice quanti guasti un PSNR da solo promuoverebbe.

| Il guasto | Il PSNR globale lo vede? | Chi lo prende | Esito atteso |
|---|---|---|---|
| fotogramma **nero** | sì, crolla | M1, M3 | 1 |
| ⛔ **cattura E pagina nere** | ⛔ **NO — PSNR infinito** | **M-V** | **2** |
| spostato di **una riga** | ⛔ solo se la scena ha alta frequenza | **M0** | 1 |
| spostato di **una colonna** | idem | **M0** | 1 |
| del **giro precedente** | ⛔ solo se la scena è cambiata | **M6** | 1 |
| **8 bit** al posto di 10 | ⛔ **NO — resta sopra 55 dB** | **M7** | 1 |
| **piani del colore scambiati** | ⛔ **NO sulla luminanza** | **M4** | 1 |
| gamma limitata letta come piena | in parte | M5 | 1 |
| un **blocco 64×64** corrotto | ⛔ **NO — la media lo annega** | **M3** | 1 |
| matrice dichiarata **BT.601** contro BT.709 | ⛔ **NO — non è nei pixel** | **M-C** | 1 |
| fotogramma consegnato **dopo un RESET** | ⛔ **NO — i pixel sono giusti** | **M8** | 1 |
| immagine **ribaltata** | sì, ma senza dire *perché* | M-V (marcatori) | 1 |

⛔ **Sei guasti su dodici sono invisibili al PSNR**, e cinque di essi sono esattamente quelli che il
mandato nomina. Un metro fatto del solo PSNR li promuoverebbe, in verde.

### ⛔ E la scena non è un contorno: senza, tre strumenti non esistono

`02-giudizio-mira.py` costruisce la scena dichiarata, e ogni sua zona esiste per un guasto preciso:

| Zona | Senza di lei |
|---|---|
| due **pettini a passo 1 px** | uno scorrimento di una riga su una sfumatura vale un millesimo di LSB: M0 non distingue |
| tre riquadri **a luminanza uguale** — (87,0,0) · (0,26,0) · (0,0,255), tutti Y=18,4/255 | scambiare R e B **non muove Y di un LSB**: M1a, M2 e M3 promuovono il guasto, e solo M4 lo prende |
| **rampa a 1/1023** e la stessa **già quantizzata a 8 bit** | non c'è il controllo interno della profondità |
| ⛔ una **sfumatura dichiarata** | M7 misurato su una zona piatta dà 0,954 — «troncato» su una catena sana |
| **rumore seminato sul nome del giro** | due giri sono identici e M6 non ha risposta |
| quattro **marcatori d'angolo** asimmetrici | un'immagine ribaltata dice «i pixel non coincidono» invece di «è ribaltata», e manda a cercare dalla parte sbagliata |

---

## ⛔ Il banco — scritto prima del prodotto, e già certificato

### La scena dichiarata, e che cosa è finto

`banchi/02-giudizio-confronto.sh`, modi `sano` e `certifica`. F2.2, F2.3 e F2.5 non esistono ancora,
quindi la catena è **finta**, e lo si scrive invece di lasciarlo capire:

```
cattura      = la MIRA di 02-giudizio-mira.py       (invece del buffer di Mutter)
flusso       = libx265 Main10 tutto-intra, QP 40    (invece di hevc_vaapi)
riferimento  = ffmpeg che decodifica lo stesso flusso, a 16 bit e in yuv420p10le
pagina       = lo stesso flusso decodificato a RGB 8 bit  (invece della tela riletta)
```

⛔ **Questo giro certifica LO STRUMENTO, non il prodotto.** Nessun numero che esce di qui è una
misura della fase 2. Il modo `giudica` punta il metro sui file veri.

⚠ E una cosa che la catena finta fa **peggio** del vero, dichiarata: qui `riferimento` e `pagina`
escono dallo **stesso** decodificatore, quindi M1 è quasi regalato. Nel giro vero escono da due
decodificatori diversi, ed è lì che M1 diventa lo strumento centrale.

⚠ **QP 40 non è una scelta di qualità**: è la scelta che mette la perdita del codificatore
abbastanza sopra il rumore della tela perché M2 abbia senso. `[M]` a QP 20 il riferimento dista
60,4 dB dalla cattura e la tela ne introduce 55,6 — la codifica perde **meno** della tela, e M2 si
dichiara *non applicabile*. A QP 40 i due numeri sono 42,2 e 56,8: **14,5 dB di margine**.

### I controlli positivi — sono quattro, e girano a ogni esecuzione

| | |
|---|---|
| **C1 — il canale di lettura** | ogni ingresso stampato con dimensione e impronta; ⛔ e **due ingressi con la stessa impronta fermano il giro**: confrontare un file con sé stesso dà PSNR infinito, ed è un errore che si fa da soli sulla riga di comando |
| **C2 — lo strumento sa bocciare** | a ogni giro si innestano **in memoria** uno scorrimento, un blocco azzerato e i piani scambiati, e se non li boccia il metro si dichiara **rotto** (stato 3). ⭐ E il rovescio: sulla coppia sana gli stessi tre devono dire di sì |
| **C3 — il flusso è davvero a 10 bit?** | letto con `ffprobe`: su un flusso a 8 bit tutta la certificazione di M7 varrebbe zero |
| **C4 — il canale della sonda** | ⭐ lo script si spedisce da solo un gettone con `POST /prova` e lo rilegge dal registro. È il controllo n. 4 di `01-s1b-eccezione.sh` (rilievo A27): senza, «il telefono non ha risposto» e «il registro non si legge» sono la stessa frase |

⛔ **Zero e fallimento sono quattro cose, non due.** Il metro esce con
**0** promosso · **1** bocciato · **2 non misurato** · **3 metro rotto**. E la certificazione di un
guasto pretende lo stato **esatto**: un guasto che facesse uscire 2 o 3 non certifica niente.

⭐ **E la distinzione che è costata un giro di riscrittura**: la scena morta **a monte** (cattura o
riferimento) è stato 2 — non si giudica il client su un ingresso che non c'è, ed è il caso della
sessione GNOME nera senza `--virtual-monitor`. La scena morta **a valle** (la pagina) con la cattura
viva è stato **1**: la misura c'è stata, e dice che il client ha dipinto il nulla.

### ⛔ Come questo banco si certifica — e il giro è già stato fatto

**sano → guasto → risanato**, con l'atteso scritto prima e verificato dopo.
`[M]` 12 agosto 2026, `banchi/02-giudizio-esiti.jsonl`, 14 righe:

| | atteso, scritto prima | misurato |
|---|---|---|
| sano (prima) | stato **0** | **0** ✅ |
| i **dodici guasti** | lo stato dichiarato in catalogo, **e la marca dello strumento giusto** | **12 su 12** ✅ |
| sano (dopo) | stato **0** | **0** ✅ |

```
nero         stato 1 · M-V,M0,M1,M3,M4,M5,M6     matrice     stato 1 · M-C
nero-doppio  stato 2 · M-V a monte: cattura      dopo-reset  stato 1 · M8
riga         stato 1 · M0,M1,M3,M5,M6            piani       stato 1 · M1,M3,M4,M5
colonna      stato 1 · M0,M1,M3,M5,M6            gamma       stato 1 · M1,M3,M5
precedente   stato 1 · M0,M1,M3,M5,M6            blocco      stato 1 · M1,M3
otto-bit     stato 1 · M7                        ribaltato   stato 1 · M-V,M0,…
```

⭐ **Il terzo giro è quello che ci si dimentica**: senza il «risanato», «il metro vede il guasto» e
«il metro è rimasto rotto» hanno lo stesso aspetto.

### §3.3 — Le righe per il catalogo delle certificazioni

Emesse in forma leggibile a macchina da **`bash banchi/02-giudizio-confronto.sh catalogo`**, nella
forma di `01-b12-guasti.py`: `nome`, `comando`, `atteso_sano`, `guasto_da_innestare`,
`atteso_guasto`, `marca`. Dodici righe, una per guasto. In sintesi:

| nome | atteso sano | guasto da innestare | atteso guasto (marca) |
|---|---|---|---|
| `F2.6/nero` | 0, con M1+M3 fra gli OK | la pagina tutta nera | 1, fra i bocciati **M1+M3** |
| `F2.6/nero-doppio` | 0, con M-V fra gli OK | **cattura e pagina** nere | **2**, marca **M-V a monte** |
| `F2.6/riga` | 0, con M0 fra gli OK | scorrimento di 1 riga | 1, **M0** |
| `F2.6/colonna` | 0, con M0 fra gli OK | scorrimento di 1 colonna | 1, **M0** |
| `F2.6/precedente` | 0, con M6 fra gli OK | il fotogramma del giro prima | 1, **M6** |
| `F2.6/otto-bit` | 0, con M7 fra gli OK | i 2 bit bassi del piano Y spenti | 1, **M7** |
| `F2.6/piani` | 0, con M4 fra gli OK | R ⟷ B | 1, **M4** |
| `F2.6/gamma` | 0, con M5 fra gli OK | 16-235 steso su 0-255 | 1, **M5** |
| `F2.6/blocco` | 0, con M3 fra gli OK | un blocco 64×64 azzerato | 1, **M3** |
| `F2.6/matrice` | 0, con M-C fra gli OK | la pagina dichiara BT.601 | 1, **M-C** |
| `F2.6/dopo-reset` | 0, con M8 fra gli OK | `reset_ricevuto` + `dipinto` | 1, **M8** |
| `F2.6/ribaltato` | 0, con M-V fra gli OK | ribaltamento orizzontale | 1, **M-V (marcatori)** |

⛔ E vale la regola della marca in **due metà** (rilievo R12-A.3): il giro guasto deve portare la
marca **e il giro sano non la doveva già portare**. Uno strumento che dice no sempre non è uno
strumento.

### ⛔ Quattro difetti che il banco ha trovato **nel banco stesso**, girando

Sono scritti perché il capitolo utile è questo (`PIANO.md` §0.3 regola 2).

1. **M4 correlava i canali su tutta l'immagine**, e il primo giro sano è uscito **rosso**: su una
   scena naturale R, G e B sono correlati fra loro a **0,978**, e nessun margine sensato separa
   1,000 da 0,978. ⇒ M4 guarda solo dove il segnale esiste per costruzione — i tre riquadri.
2. **M2 sottraeva un PSNR a 8 bit da uno a 16 bit**, accusando il client di una perdita che è
   **della tela**: `[M]` Δ = −3,18 dB su una catena perfetta.
3. **C2 innestava il guasto sulla pagina**: sul guasto «piani scambiati» ri-scambiava una pagina
   già scambiata, la **rimetteva a posto**, e il metro si dichiarava rotto mentre stava facendo il
   suo mestiere. ⛔ Un controllo che poggia sull'imputato non è un controllo.
4. **M7 aggregava `None` con un `is not False`**, cioè **promuoveva** un giro senza
   `--riferimento-10`: il modo più silenzioso di perdere la domanda dei 10 bit.

### ⭐ E una correzione a un rapporto della fase 1

`web/rapporti/S2-decodifica.md` §3.7 punto 2 propone di misurare i 10 bit **contando le bande** su
due rampe. ⛔ `[M]` 12 agosto 2026: **quella prova non sopravvive alla codifica con perdita.**
Prima di codificare, lo scarto dalla retta vale 0,289 sulla rampa a 10 bit e 1,193 su quella a 8 —
rapporto **4,13**, quel che S2 si aspetta. Dopo un `libx265` Main10 a QP 20: 0,604 e 0,792, rapporto
**1,31**. Il codificatore **liscia la scaletta**, cioè cancella il segnale su cui la prova poggia.
Una soglia a 2,5 boccerebbe ogni giro sano.

⇒ La prova sostituita sono **i due bit bassi del piano Y**, che il codificatore non cancella.
⭐ E il numero coincide, da due strumenti diversi: F2.3 ha misurato **0,25 di multipli di 4** su un
fotogramma a 10 bit veri contro **1,000** su uno passato per 8 bit; qui la stessa grandezza dà
**[0,26 0,25 0,25 0,24]** sano e **[1 0 0 0]** troncato. La soglia di 0,50 sta a metà fra due valori
**misurati**, non fra due valori dedotti.

---

## La sonda sul dispositivo vero (S2)

`banchi/02-giudizio-telefono.sh` + `02-giudizio-pagina.html` + `02-giudizio-raccogli.py`, porta
**7516**, servita **da CHUWI**. ⛔ Non tocca NIC-OS e non riusa il sito di S1b sulla 7452: quello è
un orologio da sette giorni con un certificato che non si rigenera.

### Le due domande, e la seconda ha un'indicazione contraria già raccolta

1. il browser del telefono decodifica **HEVC Main10 in hardware**? `[S]` Chrome lo documenta dalla
   108 — ⛔ ma quel `[S]` riguarda il **supporto in WebCodecs**, non l'hardware.
2. ⛔ **e restituisce davvero 10 bit?** `[?]` — e `DECISIONI.md` §2.3-bis dice che sul percorso
   `mediacodec` di Android il supporto a 10 bit è **limitato e l'uscita torna a 8 bit**, con
   mpv-android #462 che mostra HEVC 10 bit **verdi e distorti** su Pixel 6. ⚠ Non è una prova, ma
   **non si tace**: è la prima cosa che punta contro il desiderato, e viene dal lato dove non
   abbiamo margine. ⚠ E se la risposta fosse no **non è un muro** (§2.7): è un fatto da misurare e
   **dichiarare** — un ripiego silenzioso resta vietato anche quando la colpa è di qualcun altro.

### ⛔ Il caso opposto, scritto prima (`LEZIONI.md` §1.11)

Un `c2.android.hevc.decoder` **in puro software** supera cinque prove su otto: `isConfigSupported`
→ true · `configure({prefer-hardware})` → riesce · `powerEfficient` → true · fotogrammi corretti ·
latenza accettabile a 1080p. Le tre che dicono **no** sono la portata al carico bersaglio, la
canarina di CPU e la tenuta su dieci minuti. Le letture sono **TRE**: ≥ 90 fps ⇒ hardware · ≤ 30 ⇒
software · **in mezzo: verdetto sospeso**.

⛔ E i **due controlli** rendono valido il banco prima di ogni verdetto: A (VP9 `prefer-software`)
deve risultare software, B (VP9 `prefer-hardware`) deve risultare hardware. Finché non passano, il
campo del verdetto dice **BANCO NON VALIDO**.

### ⭐ Il pezzo nuovo: il confronto dei pixel si chiude SUL DISPOSITIVO

La pagina rilegge la tela con `getImageData` e **spedisce i pixel grezzi** al raccoglitore, che ne
fa il file che il metro giudica. ⇒ la metà (a) e la metà (b) di F2.6 si incontrano nello stesso
giro, e il confronto dei pixel della fase 2 **non si fa sul Chrome del portatile** — che sarebbe la
forma d'errore **E10**.

### ⛔ D16 e D17 — i due difetti che l'utente ha trovato prima di noi, col telefono in mano

*12 agosto 2026, ore 19.58. L'utente ha aperto la sonda **dal telefono in Samsung DeX**, ha premuto
i bottoni 1 e 2, e ha visto «tutti esiti negativi». **Nessuno dei due era una misura del telefono**,
e i dieci minuti li ha spesi lui.*

| | Il difetto | La forma | La cura |
|---|---|---|---|
| **D16** | `serve` accendeva il sito **senza costruire il flusso**: `GET /flusso-20260812-1958.json` → **404**. Gli esiti «negativi» erano **la sonda che non aveva niente in mano** | **E8** — «non è arrivato» e «è arrivato e non aveva niente da decodificare» avevano la stessa faccia. ⛔ Il peggiore dei due: con un riconoscimento funzionante avrebbe prodotto **un verdetto falso** («il telefono non decodifica») che nessuno avrebbe messo in dubbio | `02-giudizio-flusso.py` impacchetta **quattro sequenze già certificate da F2.5** (HEVC **e** AV1, **8 e 10 bit**); `serve` le costruisce **prima** di accendere e, se non ci riesce, **non accende**; poi **rilegge il flusso dal server con `curl`** — il 404 era HTTP, e un controllo sul disco non l'avrebbe visto; e la pagina se ne accorge **da sé** e spedisce `FLUSSO_ASSENTE` invece di un esito che somiglia a una misura |
| **D17** | il riconoscimento era sulla **stringa** dello user agent. Chrome in DeX manda `X11; Linux x86_64 … Chrome/150`, **indistinguibile da un desktop** ⇒ «NESSUNA riga viene da un dispositivo mobile» **mentre il telefono era lì** | **E10 al rovescio**: la difesa contro il client sbagliato ha rifiutato il client **giusto** | `02-giudizio-dispositivo.py`, su **due assi**: la **provenienza** (l'indirizzo IP, che il browser non può scrivere) e la **natura** (`userAgentData.getHighEntropyValues`, GPU letta da WebGL, tocco, puntatore, memoria, nuclei, schermo). ⛔ Nessun segnale da solo basta — «Android» vuole **due** segnali d'accordo, di cui almeno uno che **non** sia lo user agent — e **ogni riga dichiara quali ha usato** |

⭐ **Le quattro caselle del flusso sono lo strumento, non un lusso**: con la sola HEVC 10 bit, «non
dipinge» ha tre cause che si somigliano (manca il codec, manca la profondità, il flusso è storto);
con HEVC/AV1 × 8/10 bit il rosso dice **dove**.

⭐ **E DeX è un caso a sé, che il registro deve poter DIRE invece di scegliere.** Le etichette della
natura sono cinque: `ANDROID-MANO`, `ANDROID-DEX`, `ANDROID-SITO-DESKTOP`, `DESKTOP`, `INCERTA`. Per
S2 DeX **vale** (MediaCodec è quello del telefono); per calore e consumo vale meno (dock, spesso in
carica) — e si dichiara. ⛔ La distinzione DeX / «sito desktop» è `[?]`: poggia su puntatore e
schermo, perché nel browser **una dichiarazione del sistema non esiste**.

⛔ **La difesa E10 non si è indebolita: la provenienza ha diritto di veto.** Qualunque cosa la pagina
dichiari, un giro che nasce su questa macchina è **RIFIUTATO**.

#### La certificazione, con l'atteso scritto prima — `bash banchi/02-giudizio-telefono.sh certifica`

| | atteso, scritto prima | misurato `[M]` 12 ago 2026 |
|---|---|---|
| il riconoscimento, **7 casi** | DeX **ACCETTATO**, portatile **RIFIUTATO**, portatile travestito da Android **RIFIUTATO**, altro portatile in casa **RIFIUTATO**, la riga vera del 12 agosto **SOSPESO** | **7 su 7** ✅ |
| ⛔ **il guasto su D16** | senza sequenze `serve` esce ≠ 0 **e non accende niente** | stato **2**, nessun ascolto sulla 7537 ✅ |
| la catena, **prima** del verdetto | pagina 200 · flusso 200 · sequenze dipinte > 0 · pixel arrivati | Chrome 151: **4 su 4** dipinte, 3 686 400 byte di pixel · Firefox 140: **2 su 4** (HEVC `NotSupportedError`, coerente con F2.5), 1 843 200 byte ✅ |
| ⛔ **il verdetto** | **RIFIUTATO** su tutti e tre i motori | **RIFIUTATO** ✅ — su una catena che ha funzionato in ogni suo pezzo, che è l'unico modo in cui un «rifiutato» certifica qualcosa |
| ⭐ la differenza, **misurata** | — | **10 righe** su cui il riconoscimento per user agent dava un'altra risposta: il Chrome travestito lo **accettava** |

⭐ **E un difetto trovato certificando** (`LEZIONI.md` §1.2): il raccoglitore era a **un filo solo**
con `HTTP/1.1` keep-alive, e una connessione lasciata aperta da una scheda bloccava il servitore.
`[M]` un `POST /esito` partito alle 20.31.00 è arrivato alle **20.32.57** — due minuti. ⛔ Sul
telefono il sintomo sarebbe «la pagina si è piantata» e la diagnosi ovvia «il dispositivo non ce la
fa»: **un'altra accusa al componente innocente**. Curato con `ThreadingHTTPServer` e un lucchetto
sulla scrittura del registro.

⛔ **E il registro ora porta l'indirizzo e le letture.** Ogni riga ha `ip`; ogni `GET` è una riga col
codice. Le righe di prima di stasera restano senza indirizzo, e per quelle il verdetto è **SOSPESO**
con la ragione scritta: *«il raccoglitore non lo scriveva»*. ⛔ Non si sono riscritte: un registro di
misure non si corregge a posteriori.

⛔ **E i pixel non si prendono più «i più recenti».** `analizza` accetta solo i `pagina-*.rgb24`
spediti da una riga il cui dispositivo è **ACCETTATO**: bastava un giro di `certifica` sul portatile
per lasciare in cartella un file più fresco di quello del telefono, ed era **E10 dalla porta di
servizio**.

### Che cosa è già stato certificato della sonda, e che cosa no

| | |
|---|---|
| ✅ `[M]` il canale di lettura | il gettone spedito torna dal registro; a raccoglitore spento il controllo dice **rotto** e non dà verdetti |
| ✅ `[M]` la guardia E10 | con solo `curl` nel registro, `analizza` dice **«il dispositivo non è arrivato»**, non «ha fallito» |
| ✅ `[M]` **la strada «BANCO NON VALIDO»** | Chrome 151 su CHUWI, finestra vera su Xvfb: sequenza D costruita (60 pezzi VP9), A `prefer-software` = **516,4 fps**, B `prefer-hardware` = **configurazione non supportata** ⇒ la pagina rifiuta di pubblicare verdetti su HEVC. ⭐ È il comportamento giusto, certificato nella direzione che conta |
| ⛔ `[M]` **in Chrome headless il giro non completa** | `--headless=new` e `--headless=old`, `--disable-gpu`: la pagina si carica e lo script parte, ma `VideoEncoder.flush()` non ritorna entro 40 s. ⇒ **la sonda si esegue in una finestra vera**, ed è un limite da sapere prima di essere sul posto col telefono in mano |
| ⛔ **non certificato**: le misure su HEVC | vogliono le sequenze di F2.3 (§«Le cuciture»). Il banco le **dichiara assenti** e non le sostituisce con una più facile: una sequenza più facile non misura «un po' meno», misura un'altra cosa |
| ⛔ **non misurato**: tutto ciò che riguarda il telefono | non c'è telefono. Nessun numero di S2 è stato prodotto, e nessuno è stato dedotto |

---

## ⚠ Che cosa serve dall'utente — la sonda sul telefono non si fa da soli

*Da leggere così com'è: è l'elenco che il coordinatore può girargli in una riga sola.*

| | |
|---|---|
| **dispositivo** | un **telefono Android** con Chrome aggiornato (≥ 108; si legge in `chrome://version` e **si scrive accanto al numero**). ⛔ Non il Chrome del portatile. ⭐ Se c'è anche un **iPhone** con Safari ≥ 16.4, si fa due volte: sono due silici diversi |
| **rete** | telefono sulla **stessa rete WiFi** del portatile. Niente rete mobile: qui si misura la decodifica, non la linea |
| **cavo** | ⭐ un **cavo USB** con il **debug USB acceso**, per il controllo C: `chrome://inspect` → la scheda del telefono → «inspect» → `chrome://media-internals`, e si cerca `Created MediaCodec <nome>, is_software_codec=<bool>`. ⛔ Se il nome comincia per `c2.android.` o `omx.google.` è **software, punto** — anche se `prefer-hardware` era riuscito. ⚠ Su iPhone questo canale **non esiste**, e il limite va scritto |
| **gesto** | 1. sul portatile `bash banchi/02-giudizio-telefono.sh serve`; 2. sul telefono si apre l'indirizzo stampato **per intero, col `?giro=…` in fondo** e **si accetta l'avviso del certificato una volta** («Avanzate» → «Procedi»); 3. si preme il bottone 1 e si aspetta; 4. si preme il bottone 2; 5. ⛔ **schermo acceso e scheda in primo piano** per tutta la misura — una scheda in secondo piano si congela dopo cinque minuti e il banco misurerebbe il congelamento invece del calore |
| ⛔ **l'indirizzo non si accorcia** | il flusso si chiama `flusso-<giro>.json`: un indirizzo senza giro, o con un giro vecchio, finisce in un **404** — ed è esattamente quel che è successo il 12 agosto. Per un secondo tentativo: `bash banchi/02-giudizio-telefono.sh flusso`, che **non spegne niente** e **non fa ricomparire l'avviso del certificato** |
| ⭐ **in DeX** | vale per S2 (MediaCodec è quello del telefono), vale meno per calore e consumo (dock, spesso in carica) — e si dichiara. ⛔ **Il cavo USB è l'unico canale che dice «hardware» con certezza**, e **in DeX la porta può essere occupata**: se DeX gira via cavo verso un monitor, quella è l'unica USB-C del telefono. Tre strade, in ordine: **DeX senza fili** col cavo libero per `chrome://inspect`; un **hub USB-C** con presa dati; oppure ⚠ si rinuncia al controllo C **e lo si dichiara** — il verdetto sull'hardware resta `[?]`, e i numeri della portata da soli **non** lo chiudono |
| **tempo** | **~10 minuti** per i bottoni 1, 2 e 4 — ⭐ e il **secondo tentativo costa due minuti**: l'indirizzo nuovo si apre e basta. ⏳ **+10 minuti di fila** per il decadimento, quando le sequenze di F2.3 ci sono |
| ⛔ **e che cosa NON gli si chiede** | di dire se «si vede bene». Questa sonda produce **numeri**. Il giudizio di I8 arriva alla fine della fase, sul desktop suo |

---

## Che cosa si riusa da v1

⛔ **Dal codice di v1: niente, e non è una svista.** Cercato: in `v1/remotix-c/` non esiste nessun
confronto di pixel, nessun PSNR, nessun banco che guardi un fotogramma decodificato. Il metro della
fase 2 di v1 era «il programma non è crollato», ed è precisamente quel che `PIANO.md` vieta qui.

⚠ **I file che il piano dà per riusati in fase 2 non sono di questa sotto-fase**, ma le righe vere
contate oggi tornano: `cattura.c` **1060**, `mutter.c` **353**, `superficie.c` **675**,
`immagine.c` **273**, `codificatore.c` **889** — cinque su cinque uguali al piano. `palco.c`, che il
piano cita senza numero, ne ha **1545**.

**Si riusa invece la forma dei banchi della fase 1**, che è la parte che è costata:

| Da | Che cosa | Righe vere |
|---|---|---|
| `01-s1b-eccezione.sh` | ⭐ il **controllo positivo del canale di lettura** (rilievo A27): dimostrare che «NO» vuol dire «non è arrivato» e non «non ho potuto guardare» | 985 |
| `01-b12-guasti.py` | la forma della certificazione: **la marca**, l'atteso scritto prima, e il giro **sano → guasto → risanato** | 2237 |
| `01-s2-pagina.html` | la struttura dei controlli A e B, e la regola «il banco non pubblica verdetti finché non passano» | 442 |
| `01-s-telefono.sh` | la forma del banco pronto a girare quando il dispositivo arriva | 328 |

**Scritto in questo giro**: 3067 righe in 7 file (`02-giudizio-metro.py` 1271, `confronto.sh` 414,
`pagina.html` 358, `telefono.sh` 302, `guasti.py` 296, `mira.py` 282, `raccogli.py` 142).

---

## ⛔ Le trappole già pagate che mordono qui

| Dove sta scritto | Come morde in F2.6 |
|---|---|
| **E1** — necessario per sufficiente (`REVIEWER.md` §2) | «i pixel coincidono ⇒ 10 bit ok». ⛔ Su una tela a 8 bit la profondità **non è misurabile**, e il metro lo dichiara invece di promuovere |
| **E10** — una prova verde sul client sbagliato | «il Chrome del portatile decodifica in hardware». ⇒ il registro della sonda controlla lo user agent e dice **«il dispositivo non è arrivato»** |
| **E8** — il silenzio scambiato per zero | «il registro è vuoto» ⇒ prima si prova che il canale scrive e legge |
| **E2** — un componente che decide da sé | il decodificatore che ripiega in software senza dirlo: è tutta la ragione dei controlli A e B |
| **E5** — un fatto che era una deduzione | il banco della sonda **non produce numeri** finché non c'è il dispositivo |
| `LEZIONI.md` §1.11 | ogni prova indiretta ha il **caso opposto scritto prima**: l'elenco dei dodici guasti, e la descrizione del decodificatore software che finge bene |
| `LEZIONI.md` §1.9 | zero ≠ fallimento: **quattro** stati d'uscita, e la distinzione fra scena morta a monte e a valle |
| `LEZIONI.md` §1.2 | il banco si certifica prima di essere creduto: 12 guasti su 12, **nello stesso giro** in cui è stato scritto |
| `LEZIONI.md` §1.1 · `CODER.md` §3.2 | la scena si dichiara **e si muove**: senza il rumore seminato sul giro, M6 non esiste |
| `PIANO.md` fase 2 · `gnome.md` §13 M9 | la sessione **viva, completa e nera**: due neri hanno PSNR **infinito**, e senza M-V il metro darebbe verde pieno su un desktop che non c'è |
| `web.md` §4.1 · S2 §4.3 | cinque «sì» di fila da un decodificatore software puro |

---

## Le `[?]` da misurare

| # | Che cosa non si sa | Chi la chiude |
|---|---|---|
| **?1** | ⛔ **il telefono decodifica HEVC Main10 in hardware?** Nessun numero prodotto: non c'è dispositivo | l'utente, con la procedura qui sopra |
| **?2** | ⛔ **e restituisce 10 bit?** `[?]`, con l'indicazione contraria di §2.3-bis dichiarata | idem, canale `VideoFrame.format`/`copyTo` + controllo C |
| **?3** | il valore **sano** di M1a sulla catena vera. Atteso ≥ 55 dB; ⚠ un misurato fra 45 e 55 è **un difetto da guardare**, non un promosso comodo | F2.5 + questo banco, modo `giudica` |
| **?4** | se M2 sarà **applicabile** sulla catena vera (dipende dal QP di F2.3 e dalla profondità della cattura) | il primo giro vero |
| **?5** | se `getImageData` sarà leggibile sul telefono, o la tela sarà «sporcata» | il primo giro sul dispositivo |
| **?6** | ⛔ perché in Chrome **headless** `VideoEncoder.flush()` non ritorna. Aggirato (finestra vera), **non capito** | nessuno, per ora: è dichiarato |
| **?7** | le soglie di M1b (38 dB) e M3 (30 dB) sono **calcolate, non tarate sul campo**: reggono su una catena vera con due decodificatori diversi? | il primo giro vero |
| **?8** | i 10 bit **veri** sulla strada **DMA-BUF**, che F2.2 dichiara non provata | F2.2, non questo banco |

---

## Le cuciture

### ⛔ Che cosa CHIEDO — e senza queste il confronto non esiste

**A F2.2 (la cattura):**

| | |
|---|---|
| ⛔ **il fotogramma su file**, con il formato del buffer **dichiarato** | `BGRx`, `BGRA`, stride, larghezza, altezza. Interpretare BGRx come RGBx **è** il guasto «piani scambiati» prodotto da noi |
| ⛔ **la gamma misurata, non dedotta** | ⭐ è già arrivata: RGB, 0-255, 8 bit veri. Va **negli esiti**, accanto al file |
| ⛔ **due giri con scene DIVERSE** | M6 (freschezza) non esiste su una scena ferma, ed è l'unico strumento che vede «il fotogramma del giro prima» |
| ⭐ **la mira come scena della sessione** | `02-giudizio-mira.py` la produce. Senza le sue zone, M0, M4 e M7 non hanno dove guardare — e M-V non ha i marcatori con cui dire «è ribaltata» |
| ⚠ e la **conferma** che l'applicazione si apre **dopo** la creazione dei dispositivi di input (`PIANO.md` fase 2, S.4) | o si misura una scena che il prodotto non avrà mai |

**A F2.3 (la codifica):** ⛔ il **flusso Annex-B su file**, la **stringa del codec**, e ⛔ il **VUI
scritto** — `colour_primaries`, `matrix_coeffs`, `transfer`, `video_full_range_flag`. Senza il VUI
il browser **indovina**, e la firma dell'indovinato sbagliato (guadagno 1,164) è indistinguibile da
un difetto del client: M5 diventa un rosso senza imputato. E la matrice scelta va **dichiarata**
negli esiti, per M-C.

**A F2.5 (la pagina):** ⛔ la tela **riletta** con `getImageData` e spedita **grezza**
(`02-giudizio-pagina.html` lo fa già); `VideoFrame.format`, `codedWidth/Height`, `visibleRect` e
`colorSpace` **come li ha visti**; e — dove il browser lo consente — il `copyTo()` del fotogramma,
che è **l'unico canale** che risponde sui 10 bit. ⛔ E la tela **non si ridimensiona**: il metro
rifiuta di scalare un ingresso, perché ridimensionare significa confrontare due immagini che nessuno
ha prodotto.

**A F2.4 (il filo):** ⛔ il registro di **FIN e RESET per stream**. La pagina dichiara che cosa ha
dipinto e M8 lo legge, ma è un anello **debole per costruzione**: crede a chi è sotto esame. ⛔ E va
detto chiaro — **un fotogramma consegnato dopo un RESET, se i pixel sono giusti, è invisibile a
M0..M7 e lo deve essere**: i pixel non portano l'identità dello stream. Quella metà è di F2.4.

**A F2.1 (la sessione):** ⛔ che `--virtual-monitor` ci sia. Se manca, la sessione parte **viva e
nera**, e il mio metro esce **stato 2 — non misurato** con la ragione «la scena non è viva a monte»:
non accuserà il client, ma **non darà nessun verdetto**.

### Che cosa PROMETTO

| | |
|---|---|
| **il metro, certificato** | `02-giudizio-metro.py`, 12 guasti su 12, con il giro sano→guasto→risanato già chiuso e scritto in `02-giudizio-esiti.jsonl` |
| **quattro stati d'uscita** | chiunque chiami il metro sa distinguere «bocciato» da «non ho potuto guardare» |
| **la scena** | `02-giudizio-mira.py`, con le zone in un JSON, a qualunque risoluzione ≥ 640×480 |
| **la sonda pronta** | il giorno che il telefono c'è, la misura costa un pomeriggio invece di una settimana |
| ⛔ **e un limite dichiarato** | il metro **non** dice se i 10 bit veri arrivano al telefono, e **non** vede un fotogramma consegnato dopo un RESET con i pixel giusti. Sono due buchi **con un nome e un proprietario**, non due silenzi |

---

## Le decisioni prodotte

Piccole, prese qui e dichiarate — nessuna tocca `DECISIONI.md`, che resta del coordinatore:

1. la soglia di M2 è **relativa al riferimento** invece che assoluta in dB, per non invecchiare a
   ogni cambio di QP;
2. M7 misura **i due bit bassi sulle zone sfumate**, non le bande, e non sulla tela;
3. la sonda gira **da CHUWI sulla 7516** con un certificato proprio in `~/.remotix-f26/`, fuori dal
   deposito: NIC-OS non viene toccato e il certificato di S1b non viene sfiorato;
4. il guasto «blocco corrotto» si innesta **sui pixel**, non sul flusso — F2.3 ha misurato che una
   corruzione del flusso può uscire **identica bit per bit**, e un guasto che può non esserci non
   certifica niente.

---

## Il giudizio dell'utente

⏳ **Non ancora dato, e questa sotto-fase non lo può dare.** L'invariante I8 — «il metro è quel che
l'utente vede» — si chiude alla fine della fase 2, sul suo desktop dentro la sua scheda. Quel che
questo giro consegna è lo strumento che gli evita di guardare **un fotogramma che sembra giusto**.
