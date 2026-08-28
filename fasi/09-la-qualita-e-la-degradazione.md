# Fase 9 — La qualità e la degradazione
Aperta il **23 agosto 2026** · ✅ **Chiusa il 24 agosto 2026**, sul giudizio dell'utente:
*«il prodotto cambia in meglio; questa fase era per rendere più solido il funzionamento di remotix su
reti degradate, senza pretendere di fare miracoli»*

> ⛔ **Questo documento si riempie strada facendo** (`PIANO.md` §0.1). Le misure hanno l'ora
> accanto perché sono state scritte quando sono state prese.

> ## 📖 DOVE SONO FINITI I SETTE DOCUMENTI DEL 23 AGOSTO
>
> ⛔ **Sono stati accorpati qui e cancellati**, ed è la regola del progetto: *pochi documenti
> grossi; i rapporti degli agenti non si conservano.* ⚠ **Alcuni commenti in `src/` e in `banchi/`
> li citano ancora per nome** — questa tabella è quel che serve per seguire quei rimandi.
>
> | il file che non c'è più | dove sta adesso |
> |---|---|
> | `09-il-crollo.md` §1 · §2 (la prova, il registro) | **§4.2** |
> | `09-il-crollo.md` §3 (i sospetti esclusi) | **§4.3** |
> | `09-il-crollo.md` §4 (la causa) | **§4.1** e **§4.4** |
> | `09-il-crollo.md` §5 (come si riproduce) | **§4.5** e **P1** |
> | `09-il-crollo.md` §6 (la trappola) · §7 (la cura) · §8 (`[?]`) | **§4.7** · **§4.6** · **§4.8** |
> | `09-proposta-sgombra.md` §1-§4 (il meccanismo, la soglia, i casi limite) | **§5.2** |
> | `09-proposta-sgombra.md` §5 (la previsione) · §6 (il rifiuto parziale) | **P2**/**P3** · fine di **§5.2** e **§10.2** |
> | `09-proposta-cricchetto.md` §1-§3 (il difetto, la cura) · §4 (il banco) | **§5.3** · **§7.3** e **P5** |
> | `09-proposta-riordino.md` §1-§5 · §7 · §8 (la frontiera, il prezzo, la domanda onesta) | **§5.4** |
> | `09-proposta-riordino.md` §6 (la previsione) | **P6** |
> | `09-studio-bitrate.md` §0-§3 (i modi, il tetto) · §4 (il livello) | **§5.5** e **§10.1** |
> | `09-studio-bitrate.md` §5 (la previsione) | **P4** e **§10.1** |
> | `09-disegno-regolatore.md` (tutto) | **§6**; la previsione in **P7**/**P8**, e §5.3 in **§6.5** |
> | `09-il-registro-delle-discese.md` (tutto) | **§7** |
>
> ⭐ E dove il documento ripeteva un commento del codice, **è rimasto il codice**: la sede della
> ragione è `src/`, e qui c'è il `file:riga`.

---

## Che cosa deve produrre

Il **controllo del ritmo**, la **scala di degradazione**, il comportamento su **rete cattiva**.

> ## ⛔⭐⭐⭐ IL BERSAGLIO È STATO CORRETTO DAL REGISTA — *23 agosto 2026, sera* → **§17**
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
> perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».* — `DECISIONI.md`
> **§3.1-ter**.
>
> ⛔ **La banda esce dal corpo della fase**, e la ragione è una misura di questa stessa fase: §16,
> sul **percorso vero**, il caso peggiore chiede 21,5-23,1 Mbit/s e il prodotto lo regge **senza
> degradare e con tutte le cure spente**. Un banco che non riesce a far cedere quel che misura non
> sta misurando la grandezza giusta.
>
> ⭐⭐⭐ **E sulla grandezza giusta il prodotto cede, e cede prestissimo** (§17.1, §17.11):
> ⛔⛔ **il gradino è DOPPIO** — la spirale di chiavi parte **al primo pacchetto perso**
> (0,00-0,10 % di perdita vera), il calo che l'utente **vede** casca cinque volte più in là
> (0,53-0,75 %): ⇒ fra i due c'è mezzo punto percentuale in cui il prodotto **sta già degenerando e
> i fotogrammi al secondo dicono ancora che va tutto bene**. ⚠ E vicino al bordo è **bistabile**:
> stesso ingresso, `0 chiavi · 40,16/s` **oppure** `24 chiavi · 33,84/s`; con **zero perdita** e ±15 ms di sfarfallio **16,6/s e il DOPPIO dei byte sul
> filo**, che è la prova diretta che il disordine viene scambiato per perdita; al **13 %** a
> raffiche ⛔⛔ **la sessione si stacca dopo 0,3 s**, e *«mai staccare»* è l'unico obbligo che vale
> ovunque.
>
> ⭐⭐⭐ **E LA CURA FUNZIONA** (§17.6, appaiata a tre bracci): la quota di chiavi passa da
> **51,7-88,1 %** a **0,0-5,6 %**, il ritmo torna **da 1,7 a 2,8 volte**, e i byte sul filo
> **salgono** — ⇒ la linea non era satura, **era sprecata**. ⛔ Ma servono **tutt'e due** le cure: la
> sola soglia lascia il 12,8-33,6 % di chiavi. ⚠ **La linea sana non paga niente** (39,85 / 40,19 /
> 39,63 fotogrammi/s, zero chiavi), e il prezzo è **da −38 a +161 ms** di ritardo sui profili
> ordinari — **4,5 s** su `raffica-forte`, dove *«immagine che si muove con cinque secondi di
> ritardo»* contro *«immagine ferma»* **non è una scelta che spetti a una misura**.
> ⇒ ❓ **Le cure restano SPENTE**: I6, e la decisione è dell'utente.
>
> ⭐⭐ **E la cura del riordino dell'audio MORDE** (§17.2): purezza da 0,40-0,80 a **1,0000** su
> tutti e cinque i profili che riordinano, sei su sei verdi.

**Che cosa l'utente vede e giudica alla fine**: ⛔ **l'immagine, e basta.** In v1 la fase omologa
fu validata con PSNR e SSIM, il giudizio dell'utente sul desktop vero fu *«siamo tornati
indietro»*, e la fase fu **azzerata**.

---

# ⭐⭐⭐ LA SINTESI — *la giornata del 23 agosto 2026*

> ⛔ **Questa è la testa del documento: risponde in fretta alle quattro domande che si porranno
> domani.** I dettagli, con le ore e le scene, stanno sotto: §0 lo studio d'apertura, §1 il banco,
> §3 e §3-bis le misure, §4 il crollo, §5 le cure, §6 il lavoro che resta, §7 le previsioni,
> §8 quel che non ha funzionato, §10 le contraddizioni.
>
> ⛔⛔ **E LA SERA DEL 23 AGOSTO LE CURE SONO STATE MISURATE: sta in §13, e cambia sei righe di
> questa sintesi.** In due parole, e i dettagli là:
> ⭐⭐⭐ **la cura della memoria REGGE** e il crollo si riproduce **due volte su due**, con la pila
> letta dal core (§13.1) · ⭐⭐⭐ **il regolatore del ritmo spegne la spirale**: zero chiavi e zero
> abbandoni dove prima ce n'erano 18 e 24 (§13.3) · ⛔ **la soglia da sola NON mantiene quel che
> P3 prometteva**, e va tarata **al contrario** di come P3 diceva (§13.2) · ⭐⭐ **il tetto di
> banda sopravvive ai suoi due rossi** (§13.4) · ⛔⛔ **tutti i numeri di banda di §3.8 sono
> HEVC, e il prodotto manda H.264**: stessa scena, **21,18 contro 7,92 Mbit/s** (§13.5) ·
> ⛔⛔ **il 4K regge 41 fot/s, non 60**, e il livello prodotto **sfora** quello del client
> (§13.6) · ⭐⭐⭐ **§10.2 è decisa: la spirale sul desktop vero non morde fino a 10 Mbit/s**
> (§13.8).
>
> ⛔⛔⛔ **E LA NOTTE DEL 23 AGOSTO IL METRO È CAMBIATO: §14, e da lì in giù i numeri sono
> H.264.** ⛔ Il cliente di prova negoziava HEVC per una riga rimasta indietro di tre giorni;
> adesso negozia **quel che negozia Firefox**, verificato sulle righe di `pagina.html` (§14.1).
> In due parole: ⛔⛔ **il caso duro in H.264 chiede ancora 44,6 Mbit/s = 223 % del pavimento** —
> il tetto serve (§14.2, §14.3) · ⛔ **il rapporto HEVC/H.264 NON è una costante**: 0,36× sul
> retinato, 0,76× sulla grana, ⛔ **1,7× in su** sul desktop vero (§14.2) · ⛔ **la soglia da sola
> non mantiene la promessa a NESSUN valore**, e a 800 ms paga **1 321 ms** di coda; ⭐ la leva è la
> **coppia** con `--ritmo-adattivo` (§14.4) · ⭐⭐⭐ **P8 è VERDE**, a coppie ferma/mossa nello
> stesso giro (§14.5) · ⭐ **il 4K in H.264** e ⛔ **l'audio** in §14.6 e §14.7.

## S.1 · ⛔ Il fatto più grave della giornata: **il prodotto è morto, e la causa è provata**

Alle **08:28:09** il server della 7900 è morto di `SEGV` sul fotogramma **185**, un delta da
**525 298 byte**. ⭐ **La causa è stata trovata riga per riga**: `wt_scrivi()` liberava i byte di
un fotogramma appena ngtcp2 li aveva **serializzati**, mentre il contratto di
`ngtcp2_conn_writev_stream()` obbliga a tenerli **fino all'ack**. ⇒ **Uso dopo la liberazione**, e
il difetto c'era **a ogni fotogramma ritrasmesso, da sempre**: quello da 525 KB è stato solo il
primo abbastanza **grosso** perché `free()` restituisse davvero le pagine al kernel
(`1` blocco `mmap` su **45 005** in quel giro). Sotto i 128 KiB lo stesso errore mandava al client
**byte di spazzatura in silenzio**. ⇒ §4.

⭐ **La cura è applicata** (`src/webtransport.c:745-870` e `:5929`): a `wt_scrivi()` non si libera
più — si marca `consegnato`, e a liberare è l'ack (`coda_conferma()`) o la chiusura dello stream.
⛔ **Non è dietro un interruttore**: non cambia quel che si vede, corregge un modo di morire.

## S.2 · Che cosa è stato misurato, e quanto vale

| | `[M]` 23 agosto | dove |
|---|---|---|
| ⛔ **a scena ferma il ritmo non cala: SI FERMA** — 1 fotogramma in 30 s, poi zero. E **non è nostro**: Mutter consegna solo sul cambiamento (123 attese a vuoto/s) | 0,03 fot/s, ripetuto 2 volte, riconfermato a 2560x1080 | §3.1 |
| ⭐⭐⭐ **e il risveglio da fermo NON costa niente** — 180 colpi, quiete da 0,2 a 15 s | **13 ms** di mediana, **tutte** le 180 misure fra **12,3 e 14,3** | §3.6 |
| ⇒ e **l'80 % di quei 13 ms è attesa del compositore**; la codifica, che è nostra, ne vale 2,7 | 10,2-10,9 · **2,6-2,7** · 0,0 | §3.6 |
| ⭐ **il desktop VERO dell'utente, a schermo intero e in movimento, costa l'1 % del pavimento** | **0,204 Mbit/s**, ritrovato due volte (0,193 · 0,195) | §3.8 · §3.15 |
| ⛔ **ma il caso duro chiede TRE VOLTE il pavimento** — film con la grana a schermo intero | **58,668 Mbit/s = 293 %** di 20 | §3.8 |
| ⛔ **e «quanti pixel cambiano» non predice niente**: la banda dipende dal CONTENUTO | `pieno` 1,2 · `barra` retinato **21** · grana **59** Mbit/s, a parità di pixel mossi | §3.8 |
| ⛔⭐ **basta un buco di 3 secondi** per portare il ritmo da 40 a 13/s e fare metà chiavi | e `abbandoni §5.1` = `chiavi`, **uno a uno**, a ogni livello | §3.10 |
| ⭐ **ma il ritorno è immediato e non c'è isteresi**: regime pieno al secondo dopo | 42 fot/s, **0 chiavi**, nessuno strascico in 17 s | §3.10 |
| ⭐ **le tre cure del mattino non hanno cambiato niente dove non dovevano** — confronto appaiato 7900/7910 | risveglio ±0,5 ms · `pieno` **164 byte su 3,62 MB = 0,005 %** | §3-bis |

## S.3 · Che cosa è cambiato nel codice, e dietro quale interruttore

⛔ **Sei cure, e quattro di loro sono SPENTE di nascita (I6).** Il diff non sta qui: sta in `src/`,
e i commenti nel codice sono la sede della ragione.

| # | la cura | dove | interruttore | verificata? |
|---|---|---|---|---|
| **1** | ⛔⭐ **il crollo**: si libera all'**ack**, non alla serializzazione | `webtransport.c:745-870`, `:5929` | ⛔ **nessuno** — è la correzione di un difetto | ⛔ **no**: la ricetta di §4.5 non è stata eseguita |
| **2** | **la soglia sulla coda** in `video_sgombra()`: un delta si abbandona solo se la coda non si svuota entro la soglia | `webtransport.c:2705-2800` | `--sgombra-soglia-ms N`, **0 = spenta** | ⛔ no |
| **3** | **la risalita della qualità**: `qualita_corrente` era un cricchetto a senso unico | `codificatore.c:3446` (`risali_qualita()`), `:141-143` | `--qualita-risale`, **spenta** | ⛔ no |
| **4** | **il riordino dell'audio**: si scarta sul *«già consumato»* (§6.3), non sul *«già arrivato»* | `pagina.html:5882` (`audio_posto_passato`), `:5992`, `:6507` | ⛔ **nessuno** — è un allentamento puro, non aggiunge un ms | ⛔ **no, e il banco NON PUÒ vederla** — §3.16 |
| **5** | **il tetto di banda**: `QVBR` con filo, punto di lavoro e serbatoio derivati dal pavimento | `codificatore.c:200-340`, `:1786-1800` | `--tetto-banda-mbit N`, **0 = spento** | ⛔ no sulla macchina di prova (sì sul portatile) |
| **6** | ⭐⭐ **il regolatore del ritmo**: un fotogramma non parte quando **2 delta** in volo hanno ancora byte nella nostra coda | `webtransport.c` — `ritmo_frena()`, `ritmo_ciclo()`, `wt_ritmo_adattivo()`; la chiamata è in `video_a_una()` **prima** di `video_sgombra()` | `--ritmo-adattivo`, **spento** ⛔ **e non basta da solo: vedi qui sotto** | ⛔ no — nessuna misura, solo la previsione scritta nel codice |

⛔⛔ **E LE CURE 2 E 6 SONO DUE INTERRUTTORI CHE DIPENDONO L'UNO DALL'ALTRO — sta scritto qui
perché è il fatto più facile da misurare male di tutta la fase.**

Con `--sgombra-soglia-ms 0` (il predefinito) `video_sgombra()` abbandona ogni delta che ha ancora
byte in coda, a ogni fotogramma più recente. ⇒ Quando arriva il fotogramma N+1, l'unico delta che
può avere ancora byte nostri è N: **`arretrato` vale 0 o 1, mai 2, per costruzione** — e con
`WT_RITMO_POSTI = 2` il regolatore **non scatta mai**.

⛔ Un banco che accendesse solo `--ritmo-adattivo` misurerebbe **zero discese** e leggerebbe *«la
linea porta»*. Sono due fatti con la stessa faccia. ⇒ Il regolatore si prova **con tutt'e due
accesi**:

```
remotix --sgombra-soglia-ms 100 --ritmo-adattivo
```

⭐ E il server lo **dice all'avvio** invece di lasciarlo dedurre: `wt_ritmo_adattivo()` è chiamata
*dopo* `wt_sgombra_soglia()` apposta, così legge il valore **in vigore**, e con la soglia spenta
scrive `⛔⛔ MA LA SOGLIA DELLA CODA VIDEO E' SPENTA … questo regolatore NON SCATTERA' MAI`.
⚠ L'ordine delle due chiamate in `main.c` è parte della cura: invertirle farebbe leggere zero, e
quella riga direbbe il falso proprio nel giro in cui serve.

⭐ **E una sesta cosa, che non è una cura ma si vede nel registro**: i valori **in vigore** adesso
si scrivono all'avvio — `PARAMETRI IN VIGORE`, `la scala della degradazione` (26 → 35 → 44 → 51),
`risalita della qualita' SPENTA`, `LIVELLO PRODOTTO`, `il client dichiara video.livello`. ⛔ Fino a
stamattina il confronto di `RCP.md` §4.3 **non si poteva fare da fuori**: uno dei due numeri non
era scritto da nessuna parte. Il controllo è in §3.12, e la 7900 non ha nessuna di quelle righe.

## S.4 · ⛔ Che cosa è stato provato e NON funziona

1. ⛔⛔ **Il banco prescritto per l'audio non può vedere la cura 4, e il numero lo dimostra.**
   `07-b64-rete.py` misura il **trasporto**; la cura vive nella **pagina**. Il cliente di prova ha
   la **sua** copia della regola vecchia (`01-b3-cliente.py:743`), identica byte per byte nei due
   alberi (`md5 13e68d19…`). ⇒ La previsione *«0,175 → ≥ 0,95»* è uscita **0,1149 → 0,1235**, cioè
   niente — ⛔ **e non smentisce la cura: smentisce il banco.** §3.16;
2. ⛔ **`VBR` è fuori, e non per opinione**: sotto VBR il `qp` è **ignorato** — con e senza `qp=26`
   escono **gli stessi identici byte**, due volte su due. ⇒ Tutta la scala della degradazione e la
   risalita scritta stamattina diventerebbero **no-op silenziosi**. Si è scelto **QVBR**, dove la
   scala regge (`codificatore.c:200-215`);
3. ⛔ **Il banco di stamattina misurava una VISTA D'INSIEME.** La sessione headless di GNOME sta
   nell'Overview e ci resta: *«a schermo intero»* era **un'anteprima rimpicciolita**, e i byte di
   §3.1–§3.3 sono quelli di **una frazione dello schermo**. Trovato **guardando i pixel**, non un
   contatore. §3.7;
4. ⛔⛔ **Otto inciampi del banco in un giorno, e sei su otto hanno prodotto «un numero
   plausibile», non un rosso** — il palco orfano che accusava tre cure innocenti, l'`ESC` che
   spegne quel che doveva accendere, il `UID_B` che ammazza il Firefox dell'altro utente, il
   `wc -l <` che legge zero. §8;
5. ⛔ **La strada spiccia per il crollo è sbagliata**: `shutdown_stream_write()` prima del `free`,
   come fa `video_sgombra()`, *azzera* lo stream — e §6.2 vuole il fotogramma **completo**.
   Sarebbe barattare un crollo raro con un fotogramma rotto **sempre**. §4.6.

## S.5 · ⏳ Che cosa resta, in che ordine, e **perché quell'ordine**

| | perché prima di quel che segue |
|---|---|
| **1.** ⛔ **riprodurre il crollo con la ricetta di §4.5** (`MALLOC_MMAP_THRESHOLD_=32768` + client congelato), e armare la trappola di §4.7 | ⛔ La causa è *probabile con la riga*, **non vista in volo**. E finché non si riproduce, non si può nemmeno dimostrare che la cura l'abbia curata: si starebbe misurando un'assenza |
| **2.** ⭐ **misurare le cinque cure sul ferro vero**, una per volta, appaiate | ⛔ Sono **cinque variabili**. Il metodo di §3-bis (due server, «prima» vivo accanto al «dopo») è già scritto e ha già preso un falso allarme per la coda |
| **3.** ⛔ **scrivere il banco che fa girare la PAGINA** per la cura 4 | Senza, la cura dell'audio resta **non verificabile**: il banco di oggi misura se stesso. La forma del banco è già scritta in §3.16 |
| **4.** ✅ **il regolatore del ritmo** — **scritto** il 23 agosto 2026, cura 6 di S.3, ⏳ **non misurato** | ⛔ L'ordine obbligato è stato rispettato: la cura 2 (`--sgombra-soglia-ms`) è il suo prerequisito ed è arrivata prima. ⚠ **E resta la trappola**: acceso da solo non scatta mai, e il server lo scrive all'avvio — vedi S.3 |
| **5.** ✅ **il registro delle discese**, §7 | Nasce insieme al regolatore, non dopo: **due righe per episodio** (`il ritmo SCENDE` / `il ritmo RISALE`), mai una per fotogramma; ogni discesa porta **la misura accanto alla soglia** (`arretrato N contro 2 posti`), più `cwnd`, `cwnd_left`, byte in volo e la coda dentro la rete in ms. ⏳ Resta la **taratura di `POSTI`** sul banco |
| **6.** ⛔ **il giudizio dell'utente sulle due cose che cambiano quel che si VEDE** | È l'unica cosa che chiude la fase, ed è la lezione pagata con l'azzeramento della fase 10 di v1 |

⛔⛔ **E le TRE cose che aspettano lui, esplicitamente:**

| | il prezzo, quantificato |
|---|---|
| **la soglia sulla coda** (`--sgombra-soglia-ms 100`) | trascinando una finestra mentre la linea cala, la finestra segue il puntatore con fino a **~150 ms** di ritardo per un attimo (**~205 ms** dal gesto al pixel, sommando l'anello di fase 8) — ⛔ **invece di scattare da un'immagine all'altra a ritmo di chiave**, che è quel che fa oggi. ⚠ Quale delle due sia peggio **non lo decide una misura** |
| **il tetto di banda** (`--tetto-banda-mbit 20`) | sul **caso duro** l'immagine diventa più brutta: è il suo mestiere. ⭐ Sul **contenuto vero** la previsione è che **non succeda niente** (0,204 Mbit/s, l'1 % del pavimento) — e se il desktop vero costasse **meno** di prima, il tetto sta risparmiando dove non deve e **la cura si butta** |
| **il regolatore del ritmo** (`--ritmo-adattivo`, con la soglia accesa) | durante un calo di linea **si vedono meno fotogrammi**: il movimento diventa a scatti invece che vecchio. ⭐ La previsione è che **a 20 Mbit/s non faccia niente** — è un **parapetto**, e il suo comportamento corretto è non fare nulla. ⛔ Se un giorno la scena consegnata scende **sotto 25/s su una linea da 20 Mbit/s**, il registro lo dichiara **difetto** e non lo combatte: forzare un fotogramma dentro una coda che non si svuota peggiora la coda |

## S.6 · ⛔⛔ LE DUE CONTRADDIZIONI, dichiarate e non lisciate

⚠ **Stanno per esteso in §10, con quel che le deciderebbe.** In breve:

1. ⛔ **«Non serve nessun tetto di banda» (mattina) contro «ne chiede il 293 %» (pomeriggio).**
   Lo studio delle 09:07 concluse *«sul contenuto misurato, a 20 Mbit/s, il CQP 26 va benissimo»*
   sulla base di `[M]` fase 8 (24 956 byte per chiave, 4,17 Mbit/s nel regime peggiore). Alle 08:35
   UTC il film con la grana a schermo intero ha dato **58,668 Mbit/s**. ⇒ ⭐ **Non si contraddicono
   sul numero: misurano due contenuti diversi**, e lo studio lo aveva scritto (*«il desktop
   dell'utente NON contiene quella scena»*). ⛔ **Quel che è stato smentito è la sua stima**: ~19,9
   Mbit/s estrapolati da v1, **ottimista di tre volte**;
2. ⛔ **Quanto morde la spirale sopra il pavimento — due posizioni.** La proposta della soglia
   (§5.2) sostiene che il difetto **vive sotto il pavimento** e che sopra la cura è **inerte**
   (`[M]` a 15 Mbit/s: 2 chiavi su 1 019). Il gradino di §3.10 mostra abbandoni e chiavi **anche
   sulla linea larga** (3↔3, 1↔1 a 22-26 Mbit/s). ⇒ Le due posizioni non sono ancora decise, e
   §10.2 dice con quale misura si decidono.

---

## §0 · LO STUDIO DI APERTURA — *23 agosto 2026*

Letti per intero `RCP.md`, `SPECIFICHE.md`, `DECISIONI.md`, `LEZIONI.md`, `STUDI.md`, `PIANO.md`,
`CODER.md`, i tre documenti di fase 6/7/8, i documenti di v1 e il codice del ritmo. Quattro agenti
in parallelo, mandato di estrazione. Quel che segue è il **risultato**, non il racconto.

### 0.1 ⛔⛔ UNA CORREZIONE DI NOMENCLATURA, prima di tutto

**In v1 le ferite sono DUE fasi diverse, e i documenti di V2 le confondono.**

| | v1 fase **9** | v1 fase **10** |
|---|---|---|
| che cosa era | la copia zero, i millisecondi di CPU per fotogramma | **la qualità e la banda** |
| l'errore | ottimizzata la CPU (41→6 ms) mentre i fotogrammi consegnati **calavano** (29→22,7) | validata con **PSNR/SSIM** invece che con l'occhio dell'utente |
| l'esito | una lezione | ⛔ **AZZERATA**, codice riportato indietro, banchi rimossi |

⇒ ⭐ **La fase 9 di V2 è l'erede della fase 10 di v1.** `PIANO.md:1180` scrive *«in v1 questa fase
era stata validata con PSNR»*: è vero come *fase omologa*, ⚠ ma chi cercasse «fase 9» in
`LEZIONI.md` troverebbe **la ferita sbagliata** (la CPU). `LEZIONI.md` §2.4 e §7.2 e
`DECISIONI.md` §3.2 dicono correttamente **fase 10**.

### 0.2 ⛔ Il racconto esatto dell'azzeramento — `fondamenta/documenti/PIANO.md:1410-1442`

> *«La fase 10 va azzerata e ricominciare da zero.»* — Il codice è tornato allo stato di chiusura
> della fase 9. **I banchi sono stati rimossi.**

⛔ **`fondamenta/documenti/PIANO.md:1418`: «l'errore non è stato tecnico».** Le tre ragioni, testuali:

1. **Si è spedita a chi guarda una modifica a quel che si vede, validata solo sul banco.** Il
   passaggio a **VBR** aveva PSNR, SSIM e un fotogramma fermo guardato a occhio; **non aveva il
   giudizio dell'utente sul desktop vero, che è il metro**;
2. **Si è ottimizzato nella direzione sbagliata.** «Spendere meno banda» era un guadagno; per il
   prodotto la banda è un **pavimento**, non un budget. ⇒ ⛔ **Metà delle misure erano giuste e
   rispondevano alla domanda sbagliata**;
3. **Non si è controllato lo stato della macchina prima di cominciare** — l'utente si è preso in
   faccia un difetto noto a metà giornata.

⭐ **Il fatto tecnico che innescò tutto** (`fondamenta/documenti/SPECIFICA.md:93-96`): il controllo di
bitrate spedito *«su un desktop poco mosso scendeva a 2–6 Mbit/s, contento di risparmiare»*. ⚠ E
il testo della specifica **si prestava alla lettura opposta** — cioè una fase è stata azzerata
anche per **l'ambiguità di una riga di specifica**.

⭐⭐ **Che cosa NON fu buttato**: le misure con data e fonte, e le decisioni dell'utente —
risoluzione adattiva **fuori**, AVC444 **fuori**, codifica per regioni **fuori**.

### 0.3 ⛔ IL FATTO PIÙ GRAVE — **oggi la qualità non si governa affatto**

`[R]` 23 agosto 2026, letto nel codice:

| | oggi |
|---|---|
| controllo di **bitrate** del video | ⛔ **non esiste**: `grep bit_rate\|maxrate\|bufsize codificatore.c` → **zero occorrenze** |
| **QP** | `figlio.c:4052` `QP_HARDWARE 26` **fisso**, `rc_mode = CQP` — e il commento lo dichiara: *«il valore è di comodo: il punto di lavoro fra qualità e banda è la fase 9»* |
| algoritmo di **congestione** | ⛔ **mai scelto**: `grep cc_algo\|NGTCP2_CC` → **zero**. Si prende il default di ngtcp2 |
| l'**unico** anello di reazione alla banda | `webtransport.c:2459` `chiave_intervallo_ms()` — regola **ogni quanto si può CHIEDERE una chiave**, non quanto costa un fotogramma |
| la degradazione che il prodotto **ha davvero** | `webtransport.c:2339` `video_sgombra()` |

⛔⛔ **E `video_sgombra()` va all'incontrario di quel che §3.3 chiede.** Chiamata a **ogni**
fotogramma (`webtransport.c:2759`): su linea stretta un delta non esce in 33 ms, quindi viene
abbandonato **sempre**; ogni abbandono riaccende il debito di `RCP.md` §5.2 (`rcp.c:3358` →
`:3382`) ⇒ il flusso degenera in **sole chiavi**. ⇒ **Degrada nello spazio E nel tempo insieme**,
invece di calare il ritmo tenendo i delta. ⭐ La cura è **nominata nel codice**, permessa da §5.1,
e **non è mai stata scritta**: abbandonare un delta solo quando è *davvero senza speranza* — una
soglia sulla coda.

### 0.4 Le regole che vincolano, e che non si rimettono in discussione

| | |
|---|---|
| **I1** (`SPECIFICHE.md` §8.2) | *«Il ritmo non cala mai per prudenza, per risparmio o perché la scena è ferma. Cala solo quando la misura dimostra che la linea non porta, e ogni discesa è dichiarata nel registro.»* |
| **§8.3** | ⭐ **si calano i FOTOGRAMMI. Mai sgranare, mai staccare.** Degradare nel tempo, non nello spazio: il testo resta leggibile. E a ritmo basso si spendono **più** bit per fotogramma |
| **I6** | ciò che cambia quel che si VEDE sta **dietro un interruttore spento** finché l'utente non l'ha guardato — ⛔ è la lezione pagata con l'azzeramento |
| ⛔ **il ritardo pesa più dei fotogrammi** (`SPECIFICHE.md:128`) | *«ogni memoria intermedia compra fluidità e vende risposta»* ⇒ **ogni cuscino che questa fase volesse aggiungere va giustificato contro questa riga** |
| **§3.1-bis** (nuova, 23 agosto) | ⭐ **il pavimento della linea è 20 Mbit/s** |
| **§2.1** (confermata il 23 agosto) | ⭐ **il pavimento dell'immagine è 480p · 25 fps**, ed è ora il **fondo della scala**: sotto, il regolatore non ha il permesso di scendere |

⛔ **La scala è unidimensionale per decisione**: le altre leve sono chiuse, ciascuna con la sua
riga — la **risoluzione** (`DECISIONI.md` §5.0-ter, volutamente fuori), **la tela** (non si tocca
a sessione viva, §5.1-bis), il **4:4:4** (rinviato a RCP/2), la **profondità** (si negozia, non si
degrada). Resta il **qp**, di cui non esiste nessuna scala definita.

### 0.5 ⭐ I numeri già in mano — non si riparte da zero

| | `[M]` |
|---|---|
| a **3 Mbit/s con desktop MOSSO** l'audio passa 397 blocchi su 6 458 — purezza **0,18** | 21 ago |
| a **3 Mbit/s con desktop FERMO** — purezza **1,000** ⇒ ⛔ **non è la banda: è il video** | 21 ago |
| con **Opus** (1/32 della banda dell'audio) si perde comunque il **58 %** ⇒ ridurre quel che l'audio chiede **non lo salva** | 21 ago |
| sui giri stretti i fotogrammi consegnati sono **tutti chiavi** (144/144, 149/149) contro **2 su 1 019** a 15 Mbit/s | 21 ago |
| una chiave da 60 KB a 3 Mbit/s occupa la finestra **160 ms**, e `WT_CHIAVE_RICHIESTA_MS` ne concede una ogni **150** | 21 ago |
| ⛔ **quattro varianti del trasporto non cambiano niente** (397 · 278 · 406 · 514 · 371) ⇒ *«la finestra non è contesa: è già piena»* | 21 ago |
| il **pavimento del codificatore hardware** (v1, R31): chiedendo 2 000 kbit/s a 1440p mosso ne escono **3 702 (VBR) · 3 966 (CBR) · 4 111 (QVBR)**; `libx264` tiene 1 992 ⇒ **c'è un fondo attorno ai 4 Mbit/s, e da lì in giù l'unica leva sono meno pixel o meno fotogrammi** | v1 |
| ⛔ **il modo di controllo del bitrate non si sceglie: lo DEDUCE il driver** (`rc_max_rate == bit_rate` ⇒ CBR, e nessuno l'aveva scelto) | v1, R31 |
| su desktop fermo il CBR spendeva **9 875 kbit/s contro 277 del QVBR, per 1,8 dB** ⇒ *«la scelta non si gioca sulla scena dura: si gioca su quanto si spende quando non serve»* | v1, R31 |
| il ritmo del **contenuto vero dell'utente**: **20,9 fotogrammi/s**, 31 % identici | fase 8 |
| il peso vero delle chiavi sulla tela dell'utente: max **21 433 byte = 0,13 %** del tetto di 16 MiB | fase 8 |

---

## §1 · IL BANCO — *scritto PRIMA di sviluppare*

*Le regole, fissate prima di misurare. I tre banchi che ne sono nati stanno in §1.1 e §1.2.*

- ⭐ **il punto di lavoro è 20 Mbit/s e sopra** — `DECISIONI.md` §3.1-bis. Sotto, si può *guardare*
  ma non si *promette*;
- ⭐ **si strozza il percorso VERO, non `lo`**: `wondershaper` è in `~/.local/bin` sul tablet
  dell'utente. ⚠ È il limite dichiarato di `banchi/07-b64-rete.py`, la cui metà `netem` gira su
  `lo`, dove la MTU è 65536;
- ⛔ **il controllo che decide c'è già**: `banchi/07-b65-datagram.py --scena no`. Un banco che a
  scena ferma non dà purezza 1,000 non ha misurato niente;
- ⛔ **il primo controllo della fase è l'INVARIANTE I1**: che il ritmo **non** cali a scena ferma;
- ⛔ **si misurano tutte e tre le grandezze** — ms di CPU · fotogrammi/s · **ritardo** — **più i
  byte in uscita**, e il lavoro si fissa prima del confronto (`LEZIONI.md` §6.2, §1.26);
- ⚠ **PSNR/SSIM si possono usare come strumento di lavoro, mai come verdetto**, e prima si
  certificano contro le tre trappole di `fondamenta/documenti/REFERENCE.md:2437` (l'fps del muxer, la
  scena che finisce prima del filmato, il croma non esercitato).

⚠ **Pulizia prima di misurare**: quattro server di prova degli agenti sono rimasti accesi da root
(**7746, 7752, 7765-67, 7775**), e ⛔ **non si misura in due sulla stessa macchina**
(`LEZIONI.md` §1.26: non dà un rosso, dà **un numero plausibile**).
✅ *Chiusa il 23 agosto*: dopo il riavvio e la riprovisione la macchina ha **una sola porta 7xxx
aperta, la 7900** — verificato con `ss -tuln` prima di misurare.

### 1.1 ⭐ IL PRIMO BANCO — `banchi/09-b68-ritmo.py`, *23 agosto 2026*

**La domanda, una sola**: su **linea larga** — nessuna strozzatura, il caso in cui I1 non ha
nessuna scusa — **il ritmo cala quando la scena è ferma?**

| | |
|---|---|
| **la sessione** | `banchi/01-b3-cliente.py` **dentro il contenitore** (`enter.sh --root`): `aioquic` sta lì, non fuori. È il mestiere di `07-b65-datagram.py`, non una strada nuova |
| **la scena** | `04-b30-scena` già costruita, in tre stati: **ferma** (nessuna scena) · **barra** (una barra che scorre) · **pieno** (bande a schermo intero). ⛔ Vuole il monitor **per nome**, e il nome lo dice il registro (`monitor «Meta-0»`) |
| **il palco** | nasce col **primo** cliente e sopravvive al distacco (I4) ⇒ senza una sessione aperta prima, `--uscita` non trova nessun monitor |
| **i fotogrammi, chiave contro delta** | dalla riga per fotogramma `rcp.c:3711` — `fotogramma N SPEDITO: CHIAVE 0x0301 \| delta 0x0302 … B byte di dati` |
| **il ritmo al secondo** | dalla riga `figlio.c:6841`, che il figlio scrive **ogni secondo** e che porta anche le **attese a vuoto** |
| **gli abbandoni** | `§5.1` `rcp.c:3376` · la chiave trattenuta `§5.2` `webtransport.c:2360` · `RICHIEDI_CHIAVE … accolta (§5.2)` `rcp.c:5470` |
| ⭐ **i byte sul filo** | **si contano, non si deducono**: `/proc/net/dev` su `lo`. `[M]` `lo` **a riposo fa 0 byte in 5 s** su questa macchina (l'ssh passa da `enp7s0`, il resto è su socket unix) ⇒ contatore pulito, e **non serve toccare `tc`**. ⚠ È un vantaggio del momento, non una legge: si rimisura il riposo a ogni giro |

⛔ **I byte del filo NON sono i byte dei fotogrammi**: la riga `SPEDITO` conta il **carico utile**,
`lo` conta anche QUIC, l'audio PCM e i riscontri. Si riportano **tutt'e due**, e la differenza è
un fatto, non un errore.

#### ⛔⛔ I DUE CONTROLLI POSITIVI — *e senza di loro i numeri di §3 non valgono*

Su linea larga *«abbandoni 0»* e *«`RICHIEDI_CHIAVE` 0»* hanno **la stessa faccia** di *«il banco
non guarda quei contatori»* (`LEZIONI.md` §1.9: vuoto e giusto si somigliano). ⇒ Due giri fatti
apposta per far **muovere** quei contatori:

| | come | esito, 23 ago |
|---|---|---|
| **§5.2** `09-b68-ritmo.py controllo` | il cliente **chiede** una chiave a metà giro | ✅ accolte **1**, girate al palco **1**, delta buttati **1** |
| **§5.1** `09-b68-ritmo.py stretto` | la linea si stringe a **2 Mbit/s** (`netem` su `lo`, solo la 7900), una volta sola, poi si rimette | ✅ abbandoni **151**, chiave trattenuta **86** |

⛔ **La rete si tocca con la disciplina di `07-b64`/`07-b65`**: solo `lo`, solo la porta 7900,
`enp7s0` (ssh + la 7730 dell'utente) **mai**, guardiano staccato che rimette la disciplina anche se
il copione muore. `[M]` verificato dopo: `lo` → `noqueue`, `enp7s0` → `mq`, intatta.

### 1.2 ⭐⭐ IL SECONDO BANCO — `banchi/09-b71-risveglio.py`, *23 agosto 2026, pomeriggio*

**La domanda**: §3.1 ha misurato che a scena ferma il ritmo **si ferma**, e che il prezzo per chi
guarda è zero *finché nessuno tocca niente*. ⇒ ⛔ **quanto passa fra il primo pixel che cambia e
il primo fotogramma che esce?**

| | |
|---|---|
| **il colpo** | la scena `04-b30-scena` si **congela** (`SIGSTOP`) e si **risveglia** (`SIGCONT`). ⛔ Non si spegne e si riaccende il processo: l'avvio di un client Wayland (connessione, superficie, primo buffer) costa decine di ms che **non sono il risveglio del prodotto** e si sommerebbero al numero senza che nessuno se ne accorga |
| ⭐ **l'istante del pixel** | **si legge, non si deduce**: `ultimo_disegno_us` nel blocco condiviso della scena (CLOCK_MONOTONIC, scritto al commit, `04-b30-scena.c:1367`). Il colpo **non è** il momento in cui il pixel cambia: in mezzo c'è il risveglio della scena, e si riporta a parte |
| **il battitore sta sulla macchina** | `banchi/09-b71-agente.py`, da root: batte il colpo e sorprende il primo disegno leggendo `/dev/shm` a ~2 kHz. ⛔ Da `ssh` non si può: il giro di rete è **cento volte** il numero cercato |
| ⭐ **i due orologi si ancorano** | il registro scrive `HH:MM:SS.mmm` **senza data e senza fuso**. L'agente misura lo stesso istante nei due modi (epoch + locale) e il banco **ricava** lo scarto invece di indovinarlo. ⛔ Se fosse sbagliato i risvegli uscirebbero negativi o di ore: si vedrebbe, non si insinuerebbe |
| **che cosa è misurato** | `SPECIFICHE.md` §2.4: il tratto **primo pixel → byte fuori dal server**. ⚠ **Non** l'anello intero — mancano il volo sul filo, la decodifica e la pittura sulla pagina, che sono fase 8 e **si sommano, non si confondono** |
| ⭐⭐ **il confronto** | non un numero, una **scala**: lo stesso risveglio con quieti da 0,2 a 15 s. Se il risveglio dopo 15 s di fermo costa quanto quello dopo 0,2 s, **l'arresto non costa niente** |
| **la premessa si controlla** | durante ogni quiete il banco conta i fotogrammi usciti: se ne esce anche uno, il desktop **non era fermo** e la misura non è quella che dice di essere |

#### ⛔⛔ IL CONTROLLO POSITIVO — *e ci sono voluti tre tentativi, tutti istruttivi*

Si inietta un ritardo **noto** di 200 ms congelando dei processi, e il banco deve ritrovarlo.

| tentativo | dove cade il ritardo | esito |
|---|---|---|
| congelo il **figlio** (cattura+codifica) al colpo | ⛔ `colpo → pixel` **0,5 → 191,8 ms** | il ritardo finisce **prima** del pixel: non prova niente sul tratto misurato |
| congelo il **padre** (trasporto) al colpo | ⛔ `colpo → pixel` **1,1 → 192,0 ms** | **uguale**: lo stimolo si sposta insieme allo strumento |
| ⭐ congelo il padre **dopo che il pixel è cambiato** | ✅ risveglio **12,8 → 204,0 ms**, e `colpo → pixel` resta **1,2 ms** | il ritardo cade **dentro** il tratto misurato, e il banco lo vede tutto |

⭐⭐ **E i due tentativi falliti hanno misurato una cosa che non cercavo, e non è piccola**:
congelare **qualunque** anello della nostra catena — figlio *o* padre — ferma il **disegno
dell'applicazione**. `[M]` 191,8 e 192,0 ms su 200 iniettati, con dispersione di **0,6 ms**.
⇒ ⛔ **Mutter concede il `wl_surface.frame` al ritmo di chi consuma il monitor virtuale**: se il
prodotto non consuma, l'applicazione dentro la sessione **non disegna**. È la stessa riga
letta dall'altro capo in §3.2 (*«il collo non è il codificatore: è la consegna»*), e spiega
perché i 40/s su 60 chiesti non si spostano.

---

## §2 · Che cosa è stato sviluppato

> ⚠ **Questa riga diceva *«del prodotto, niente»* fino alle 09:00 del 23 agosto**, e allora era
> vera. Nel corso della giornata sono entrate **cinque cure**: l'elenco con l'interruttore sta in
> **S.3**, il perché di ciascuna in **§5**, e ⛔ **la sede della ragione è il commento nel codice**,
> non questo documento.

### 2.1 Nel prodotto — *le cinque cure del 23 agosto*

| dove | che cosa |
|---|---|
| `src/webtransport.c` | ⛔⭐ **la cura del crollo**: i byte di un fotogramma si liberano all'**ack** (`coda_conferma()`, `:840-870`) o alla chiusura dello stream, non alla serializzazione. A `:5929` c'è la riga che uccise il server, e il commento la nomina. ⭐ **la soglia sulla coda** in `video_sgombra()` (`:2705-2800`), con i due conti `sgombra_tenuti` / `sgombra_abbandoni` — perché *«zero abbandoni»* e *«la cura è spenta»* non abbiano la stessa faccia |
| `src/codificatore.c` | ⭐ **la risalita della qualità** (`risali_qualita()`, `:3446`): si conta alla consegna, si risale **all'ingresso del fotogramma dopo**, uno scalino per volta, con l'attesa che **raddoppia** a ogni ricaduta. ⭐ **il tetto di banda** (`:200-340`, `:1786-1800`): `QVBR`, con filo · punto di lavoro · serbatoio **derivati dal pavimento** in un posto solo |
| `src/pagina.html` | ⭐ **il riordino dell'audio**: `audio_posto_passato()` (`:5882`) calcola la **frontiera del consumo** da `a.base` e `ctx.currentTime`; `a.ist_max_us` (`:5669`) separa *«un blocco sorpassato»* da *«tutta la riproduzione in ritardo»* — ⛔ senza, un sorpasso da 1 ms costerebbe un riarmo, cioè **250 ms regalati** |
| `src/main.c` · `src/figlio.c` | i **tre interruttori** (`:994`, `:999`, `:1005`), passati al figlio nell'`argv` (`figlio.c:1162-1165`), e ⭐ **i valori in vigore scritti all'avvio in tutt'e due i casi** — acceso e spento |

⭐ E una cosa che vale oltre la giornata: **la riga dei parametri dice i VALORI, non le parole** —
*«QP 26»*, non *«QP costante»*. Il controllo è §3.12.

### 2.2 Nei banchi

| | |
|---|---|
| `banchi/09-b68-ritmo.py` | il banco dell'**invariante I1** — §1.1 qui sopra |
| `banchi/09-b68-scena.sh` | accende `04-b30-scena` dentro la sessione di «prova». ⛔ Esiste perché **un file non ha livelli di virgolette** — vedi §4 |
| ⭐ `banchi/09-b71-risveglio.py` | il banco del **risveglio** — §1.2. Non riscrive il mestiere: **importa** `09-b68` per ssh, sudo, `lo`, registro, scena e `tc` |
| `banchi/09-b71-agente.py` | il **battitore**, gira sulla macchina: `SIGCONT` e `/dev/shm` a 2 kHz |
| `banchi/09-b71-sessione.sh` | apre una sessione **lunga e in sottofondo** dentro il contenitore. ⛔ Stessa ragione dello script della scena: quattro strati di apici e un redirect verso una cartella di root |
| `banchi/09-b72-banda.py` | il banco della **banda**: i tre punti a 2560x1080 e il **gradino** |
| `banchi/09-b72-agente.py` | il **direttore del gradino**: cambia il `rate` e guarda il filo dalla macchina, perché il gradino dura 3 s e un giro di `ssh` ne costa 0,3 |
| `banchi/09-b72-video.sh` | un **video vero** a schermo intero dentro la sessione. ⛔ Esiste perché le bande di `--movimento pieno` sono **tinte piatte**: misurare lì il costo di un video darebbe un numero basso e falso |

---

## §3 · Le misure

> Tutte del **23 agosto 2026**, macchina 192.168.0.2, porta **7900**, utente **`prova`**, tela
> **1920x1080**, codec **HEVC** (`codec 1`), audio **PCM**, **30 s per giro**, **linea larga**
> (nessuna strozzatura, `lo`).
> ⚠ **Le ore sono quelle della macchina, che è UTC e sta due ore indietro** rispetto al portatile:
> `07:02 UTC` = `09:02 CEST`.

### 3.1 ⛔⭐⭐ I1 — A SCENA FERMA IL RITMO NON CALA: **SI FERMA**

> ⚠⚠ **DA LEGGERE CON §3.7 ACCANTO** (scritto il pomeriggio dello stesso giorno): queste misure
> sono state prese con la sessione nella **vista d'insieme** di GNOME, dove una finestra «a schermo
> intero» è in realtà **un'anteprima rimpicciolita**. ⇒ la forma del risultato regge (a scena ferma
> escono zero fotogrammi, rimisurato a 2560x1080), ⛔ **ma i byte di `barra` e `pieno` qui sotto
> sono quelli di una frazione dello schermo, non dello schermo.** I byte veri sono in §3.8.

| scena | ora | fotogrammi/s | CHIAVE | delta | carico video | byte sul filo (`lo`) |
|---|---|---|---|---|---|---|
| **ferma** | 07:02:27 | ⛔ **0,03** | 1 | **0** | 10 147 B · **2,7 kbit/s** | 9 119 569 B · **2,432 Mbit/s** |
| **barra** | 07:03:32 | **39,67** | 1 | 1 189 | 2 171 824 B · **579 kbit/s** | 11 771 322 B · **3,139 Mbit/s** |
| **pieno** | 07:04:09 | **39,00** | 1 | 1 169 | 10 196 190 B · **2 719 kbit/s** | 20 121 206 B · **5,366 Mbit/s** |
| **ferma** *(ripetuta)* | 07:04:44 | ⛔ **0,03** | 1 | **0** | 10 143 B · **2,7 kbit/s** | 9 118 304 B · **2,432 Mbit/s** |

⛔⛔ **A scena ferma, in 30 secondi, esce UN fotogramma solo — la chiave d'apertura — e poi più
niente.** Ripetuto due volte, **identico**: 1 e 1. Non è un calo: è un **arresto**.

⭐ **E il ritmo al secondo lo dice senza mediarlo** (`fotogrammi al secondo`, dalla riga del figlio):

```
ferma   1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
barra  40 40 40 40 39 41 40 40 40 40 41 40 40 38 39 38 38 40 40 40 41 39 40 40 40 40 40 40 41
pieno  40 39 40 40 38 38 37 38 38 39 37 40 37 40 40 39 40 40 39 39 40 40 39 40 40 41 39 41 40
```

⭐⭐ **E LA CAUSA È SCRITTA NEL REGISTRO DAL PRODOTTO STESSO**, `figlio.c:6841`, ogni secondo:

> *«N fotogrammi consegnati (K chiavi), **M attese a vuoto (scena ferma: Mutter consegna solo
> quando qualcosa cambia)**»*

| scena | attese a vuoto al secondo | fotogrammi al secondo | somma |
|---|---|---|---|
| **ferma** | **123** | 0 | ~123 |
| **barra** | 80 | 40 | ~120 |
| **pieno** | 81 | 39 | ~120 |

⇒ ⭐ **Il ciclo del figlio gira sempre a ~120 Hz**: non rallenta, non si risparmia, non decide
niente. A cambiare è **quante volte Mutter gli mette qualcosa in mano** — 40 su 120 quando la
scena si muove, **0 su 123** quando è ferma.

⛔ **Quindi la discesa NON è nostra, e non è nemmeno una decisione**: nessuno la prende. Il
prodotto **non ha un regolatore del ritmo** (§0.3: il controllo di bitrate *non esiste*), e la
sorgente — `RecordVirtual` di Mutter — consegna **solo sul cambiamento**. ⇒ Il ritmo del prodotto
è, oggi, **il ritmo con cui il compositore si degna di consegnare**.

⚠ **Che cosa questo NON dice ancora**, e va detto perché sono due domande diverse:
- **l'immagine di chi guarda non si rompe**: la pagina tiene l'ultimo fotogramma buono, e su un
  desktop fermo l'ultimo fotogramma buono **è giusto**. ⇒ ⭐ Letteralmente I1 è violata
  (*«il ritmo non cala mai … perché la scena è ferma»*), ma **il prezzo per chi guarda è zero
  finché nessuno tocca niente**;
- ⛔ **il prezzo vero è al RISVEGLIO**, e questo banco **non l'ha ancora misurato**: quanto passa
  fra il primo pixel che cambia e il primo fotogramma che esce. È la misura che segue.

### 3.2 Il ritmo a scena mossa: **40/s su 60 chiesti**

`[M]` Il figlio chiede **60/s** alla cattura (`60/s chiesti`) e ne riceve **39–41**. Il tetto non è
la nostra codifica: il tratto **cattura → byte fuori** ha mediana **8,12 ms** (barra) e **8,87 ms**
(pieno) su 1920x1080 — cioè ~115/s di capienza. ⇒ ⭐ **Il collo non è il codificatore: è la
consegna.** `[?]` Da capire in questa fase se i 40 sono un tetto di Mutter o della scena.

### 3.3 I byte, e ⛔ quanto costa il silenzio

> ⚠ **Vale l'avvertenza di §3.1**: `barra` e `pieno` erano anteprime, non schermo intero — §3.7.
> La riga **ferma** invece regge, ed è confermata a 2560x1080 in §3.8.

| scena | carico video | filo totale | ⇒ overhead + audio |
|---|---|---|---|
| ferma | 2,7 kbit/s | 2,432 Mbit/s | ⛔ **il 99,9 % del filo non è video** |
| barra | 579 kbit/s | 3,139 Mbit/s | |
| pieno | 2 719 kbit/s | 5,366 Mbit/s | |

⛔⛔ **A desktop fermo il prodotto spende 2,4 Mbit/s per non mostrare niente**: sono l'audio PCM
(5 995 blocchi × 960 B = 1,53 Mbit/s di carico) più QUIC. ⭐ È l'osservazione di v1 R31 rovesciata
(*«la scelta si gioca su quanto si spende quando non serve»*), e stavolta chi spende **non è il
video**.

### 3.4 Gli abbandoni e le richieste di chiave — **tutti a zero, e il perché è buono**

| | ferma | barra | pieno | ⭐ controllo a **2 Mbit/s** |
|---|---|---|---|---|
| abbandoni **§5.1** | 0 | 0 | 0 | **151** |
| chiave trattenuta **§5.2** | 0 | 0 | 0 | **86** |
| `RICHIEDI_CHIAVE` accolte | 0 | 0 | 0 | 0 |
| richieste **girate al palco** | 0 | 0 | 0 | **151** |
| delta buttati perché §5.2 vuole una chiave | 0 | 0 | 0 | **538** |
| audio buttati / rifiutati | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 3 018** |

⇒ Su linea larga **niente si mette in coda, quindi niente può essere abbandonato**: gli zeri sono
la risposta giusta, e i due controlli positivi di §1.1 dimostrano che quei contatori **sanno
muoversi**.

### 3.5 ⛔⭐ E LA SPIRALE DI §0.3 SI RIPRODUCE ALLA PRIMA STRETTA — 07:09:38, **2 Mbit/s**, scena `pieno`

| | |
|---|---|
| fotogrammi spediti | 690 in 30 s = **23,0/s** (contro 39,0 su linea larga) |
| di cui **CHIAVE** | ⛔ **152 su 690** — contro **1 su 1 170** |
| abbandoni §5.1 | **151** ⇒ ⭐ **un abbandono, una chiave**: la corrispondenza è quasi esatta |
| delta buttati perché serve una chiave | **538** ⇒ cioè **tutti** i delta consegnati |
| quel che arriva a chi guarda | **367 fotogrammi, 128 chiavi** — su 690 spediti |
| l'audio | **3 018 datagram rifiutati da ngtcp2** (su linea larga: 0) |

⇒ ⛔ **È esattamente la spirale che §0.3 aveva letto nel codice, qui misurata sul prodotto della
fase 9**: `video_sgombra()` abbandona il delta ⇒ §5.2 apre il debito ⇒ esce una chiave ⇒ la chiave
riempie la finestra ⇒ il delta dopo non esce ⇒ si ricomincia. ⭐ E il flusso **degrada nello
spazio E nel tempo insieme** (23/s **e** sole chiavi) invece di calare il ritmo tenendo i delta,
che è quel che §8.3 chiede.

⚠ **Questo è un CONTROLLO, non una misura della fase**: 2 Mbit/s è un decimo del pavimento
dichiarato (§3.1-bis, 20 Mbit/s). Serve a sapere che i contatori vedono; il punto di lavoro va
misurato a 20 Mbit/s e sopra.

---

### 3.6 ⭐⭐⭐ IL RISVEGLIO **NON COSTA** — *23 agosto, 07:46–08:00 (UTC macchina)*

> Porta **7900**, utente **`prova`**, tela **1920x1080**, codec HEVC, audio PCM, linea **larga**.
> Scena `04-b30-scena --movimento pieno`, congelata (`SIGSTOP`) e risvegliata (`SIGCONT`).
> **180 risvegli**, 30 per ogni durata di quiete. Banco `banchi/09-b71-risveglio.py` — §1.2.

⛔ **La domanda**: §3.1 ha misurato che a scena ferma il ritmo **si ferma**. Il prezzo per chi
guarda è zero finché nessuno tocca niente — ⛔ **ma quanto costa ricominciare?**

| quiete prima del colpo | n | **mediana** | min | max | **p95** |
|---|---|---|---|---|---|
| **0,2 s** | 30 | **13,3 ms** | 12,7 | 13,8 | 13,8 |
| **0,5 s** | 30 | **13,0 ms** | 12,6 | 13,5 | 13,5 |
| **1,0 s** | 30 | **13,6 ms** | 13,0 | 14,3 | 14,2 |
| **2,0 s** | 30 | **13,2 ms** | 12,6 | 13,8 | 13,7 |
| **5,0 s** | 30 | **13,0 ms** | 12,3 | 13,6 | 13,5 |
| **15,0 s** | 30 | **13,2 ms** | 12,6 | 13,8 | 13,8 |

⭐⭐ **La risposta è secca: il risveglio da fermo NON costa niente.** Fra 0,2 s di quiete e 15 s
di quiete la differenza è **0,3 ms su 13** — dentro il rumore. ⛔ E non è una mediana che nasconde
una coda: **tutte e 180 le misure stanno fra 12,3 e 14,3 ms**, cioè la coda è larga **2 ms**.
`LEZIONI.md` §6.5 chiede la coda perché *«il regime è cieco alla coda»*: qui la coda è stata
guardata e **non c'è**.

⇒ ⭐ **L'arresto a scena ferma non è un difetto della fase.** Il ritmo si ferma perché Mutter non
consegna, e riparte al primo pixel come se non si fosse mai fermato.

**Che cosa è misurato** (`SPECIFICHE.md` §2.4): **primo pixel → byte fuori dal server**.
⚠ **Non** l'anello intero: mancano il volo sul filo, la decodifica e la pittura, che sono di
fase 8 e **si sommano**. ⭐ Il tratto della *scena* è dichiarato a parte e vale **0,3–0,4 ms**
(il `SIGCONT` e il disegno): non è nostro e non è dentro i 13.

⭐ **E dove vanno quei 13 millisecondi** — dalle righe per fotogramma del registro:

| | mediana |
|---|---|
| pixel → inizio della codifica (**Mutter compone e ci consegna, più la nostra cattura**) | **10,2–10,9 ms** |
| **la codifica**, che è nostra | **2,6–2,7 ms** |
| fine codifica → `SPEDITO` (consegna al trasporto) | **0,0 ms** (sotto il millisecondo del registro) |

⇒ ⛔ **L'80 % del risveglio è attesa del compositore, non lavoro nostro**, ed è coerente con un
monitor virtuale a 60 Hz (mezzo periodo medio = 8,3 ms). ⭐ **Non c'è niente da ottimizzare qui
dentro**: la parte che possiamo toccare sono 2,7 ms su 13.

**Il primo fotogramma che esce è sempre un `delta`** (180 su 180), mediana **2,9–3,1 KB**: il
risveglio **non costa una chiave**.

### 3.7 ⛔⭐⭐ E IL BANCO DI STAMATTINA MISURAVA UNA VISTA D'INSIEME — *08:08*

`[M]` **Guardato nei pixel della cattura**: la sessione headless di GNOME sta nella **vista
d'insieme** (l'Overview di *Attività*) e ci resta, perché nessuno ha mai premuto un tasto dentro.
⇒ le finestre non sono finestre, sono **anteprime rimpicciolite** in mezzo allo schermo, con la
barra in alto e il cassetto in basso.

⛔⛔ **Quindi «a schermo intero» nei banchi di stamattina non era a schermo intero**, e i numeri di
§3.1–§3.3 sono quelli di **una frazione dello schermo**. La forma del risultato di §3.1 non cambia
(a scena ferma escono zero fotogrammi: rimisurato a 2560x1080, **0 in 30 s**), ⚠ **ma i byte sì**.

⭐ **La cura, e non è un trucco**: si manda un **ESC** per la porta che usa il prodotto stesso —
`org.gnome.Mutter.RemoteDesktop` (`banchi/09-b72-tasto.py`). Cioè si fa **quel che succede quando
l'utente preme un tasto**. Le due strade più comode sono chiuse e le ho provate:
`org.gnome.Shell.Eval` → `(false, '')`; `org.gnome.Shell.FocusApp` → `AccessDenied`.

### 3.8 ⭐⭐⭐ LA BANDA A 2560x1080 — **il video a schermo intero chiede il 293 % del pavimento**

> Utente **`prova2`** (palco nuovo), tela **2560x1080**, 30 s per punto (25 s per la grana),
> linea **larga**, `08:22–08:35`. Banco `banchi/09-b72-banda.py`. ⭐ Ogni scena è stata
> **guardata nei pixel** prima di essere creduta.

| scena | fot/s | chiavi | **carico video** | **% di 20 Mbit/s** | filo `lo` |
|---|---|---|---|---|---|
| **ferma** (niente) | **0,00** | 0 | **0** | **0 %** | 2,426 Mbit/s |
| **video: il desktop vero dell'utente, a schermo intero** | 23,10 | 0 | **0,204 Mbit/s** | **1,0 %** | 2,678 |
| **pieno**: bande a tinta piatta, tutto lo schermo | 40,57 | 0 | **1,179 Mbit/s** | 5,9 % | 3,730 |
| **barra**: gradiente **retinato** su tutto lo schermo + barra | 34,93 | 1 | **21,356 Mbit/s** | ⛔ **106,8 %** | 24,219 |
| ⛔ **video con la grana, a schermo intero** | 23,44 | 0 | ⛔ **58,668 Mbit/s** | ⛔ **293,3 %** | **61,671** |

⛔⛔ **La risposta alla domanda di §0.3 è sì: serve un controllo del bitrate.** Con **QP 26 fisso**
e **nessun tetto**, un contenuto duro a schermo intero chiede **tre volte il pavimento dichiarato**
— 312 861 byte per fotogramma di media, 23 al secondo. ⚠ E il `[?]` di stamattina (**~19,9
Mbit/s**, riscalato da v1) era **ottimista di tre volte**.

⭐⭐ **E i tre punti insieme dicono la cosa che un numero solo non direbbe**: la banda non dipende
dalla *superficie* che si muove, dipende dal **contenuto**. `pieno` muove **tutti** i pixel e costa
**1,2 Mbit/s**; `barra` muove gli stessi pixel con un **retino** e costa **21**; il film con la
grana costa **59**. ⇒ ⛔ **«quanti pixel cambiano» non predice niente**, e un regolatore costruito
su quella grandezza sbaglierebbe di due ordini di grandezza.

⭐ **Il desktop vero dell'utente, a schermo intero e in movimento, costa l'1 % del pavimento**
(0,204 Mbit/s). ⇒ Sul contenuto per cui il prodotto esiste, oggi **non c'è nessun problema di
banda**: il problema è il caso duro, ed è per il caso duro che il tetto va scritto.

⚠ **Il filmato e il lettore si dichiarano**, perché un altro lettore darebbe un altro ritmo:
`scena-utente.webm` (2560x1080, VP8, 17,5 s, 404 fotogrammi a ~23/s — **lo stesso file** su cui la
fase 8 ha misurato 24 956 byte per chiave), riprodotto da **firefox-esr** a schermo intero.
⛔ Sulla macchina non esistono mpv, ffplay, gst-launch, totem, vlc né ffmpeg: Firefox è **l'unico
lettore**, ed è anche quello vero dell'utente.

### 3.9 ⛔⛔ IL PRODOTTO È MORTO DI SEGV SUL FOTOGRAMMA DA 525 KB — *08:28:09*

`[M]` `journalctl -u remotix-7900.service`:
> `Main process exited, code=killed, status=11/SEGV`

⭐ **L'ultima riga del suo registro, allo stesso secondo**:
> `08:28:09.894 figlio  codec 1: 525298 byte, delta, caricamento 0 us, codifica 2597 us`
> `08:28:09.895 rcp     fotogramma 185 SPEDITO: delta 0x0302, codec 1, 2560x1080, 525298 byte…`

Era il primo fotogramma del **film con la grana**. ⚠ **Non riprodotto**: il giro dopo, con lo
stesso filmato, ha retto 25 secondi e 586 fotogrammi (mediana 313 KB, punte oltre 500 KB).
⛔ Nessun `core` (coredump disabilitato) e nessun OOM in `dmesg`: la memoria di picco dell'unità
era **41,2 MiB**.

> ⭐⭐⭐ **E nel pomeriggio la causa è stata trovata, riga per riga: §4.** Questo riquadro resta
> com'era scritto la mattina — *«`[?]` la causa non è nominata»* — perché è il verbale di quel che
> si sapeva alle 08:28, e §4 è quel che si è saputo dopo. ⭐ E la frase *«non si è ripetuto»*, che
> allora sembrava un'attenuante, è diventata **la prova**: §4.4 spiega **perché** il giro dopo non
> poteva morire.

### 3.10 ⭐⭐⭐ IL GRADINO — **basta un buco di 3 secondi, e il ritorno è immediato**

> Scena **`barra`** (quella che chiede 21 Mbit/s: sotto i 10 del buco c'è un **deficit vero**),
> tela 2560x1080. `netem` su `lo`, solo la porta 7900, `delay 15ms` **in tutte e tre le fasi** —
> cambia solo il `rate`, così il transitorio è della banda e non dell'RTT. `08:32`.
> ⭐ Il cambio di disciplina costa **4,0–4,7 ms**, misurato: su un buco di 3 s è l'0,15 %.

| s | fot/s | **chiavi** | delta | abbandoni §5.1 | filo Mbit/s | fase |
|---|---|---|---|---|---|---|
| 5 | 32 | 3 | 29 | 3 | 22,1 | larga |
| 6 | 38 | 1 | 37 | 1 | 26,3 | larga |
| 7 | **40** | **0** | 40 | **0** | 28,2 | larga |
| **8** | ⛔ **14** | ⛔ **6** | 8 | **7** | **8,5** | **stretta** |
| **9** | ⛔ **14** | ⛔ **7** | 7 | **6** | **8,3** | **stretta** |
| **10** | ⛔ **13** | ⛔ **7** | 6 | **7** | **8,0** | **stretta** |
| 11 | 32 | 2 | 30 | 2 | 24,1 | *la linea si riapre a +11,1 s* |
| **12** | ⭐ **42** | ⭐ **0** | 42 | **0** | **29,2** | larga |
| 13…28 | 39–41 | **0** | | **0** | 27,6–29,0 | larga |

⛔⛔ **Sì: basta un buco.** Non serve una linea povera sostenuta — **tre secondi** portano il ritmo
da 40 a 13/s e fanno diventare **metà dei fotogrammi delle chiavi** (7 su 13). È la spirale di
§0.3, identica a quella vista a 2 Mbit/s costanti, innescata da un transitorio.

⭐⭐ **E la corrispondenza è esatta, a ogni livello**: `abbandoni §5.1` = `chiavi`, uno a uno —
7↔6, 6↔7, 7↔7 nel buco, e anche **sulla linea larga** (3↔3, 1↔1). ⇒ ⛔ Non è «la linea povera fa
uscire chiavi»: è **`video_sgombra()` che abbandona un delta, e ogni abbandono compra una chiave**.
La linea povera non fa che aumentare gli abbandoni.

⭐⭐⭐ **Ma il ritorno è immediato, e questa è la notizia buona**: la linea si riapre a +11,1 s, il
secondo 11 è di transizione (32 fot, 2 chiavi) e **il secondo 12 è già regime pieno** — 42
fotogrammi, **zero chiavi**, 29,2 Mbit/s. ⇒ **meno di un secondo**, e nessuno strascico nei 17
secondi successivi. ⛔ **Non c'è isteresi**: il prodotto non ha un regolatore che «si ricorda» di
essere sceso, quindi non ha nemmeno niente da far risalire.

#### ⛔ IL CONTROLLO, e senza di lui il gradino non dimostra niente

Stesso gradino, scena **`pieno`** (3,7 Mbit/s sul filo, cioè **sotto** il buco):

| s | 8 | 9 | 10 | 11 |
|---|---|---|---|---|
| fot/s | 40 | 39 | 39 | 40 |
| chiavi | **0** | **0** | **0** | **0** |
| abbandoni | **0** | **0** | **0** | **0** |

⇒ ⭐ Quando la banda chiesta sta sotto il buco **non succede assolutamente niente**. Il banco non
spara a vuoto: spara quando c'è un deficit, e solo allora. ⛔ E questo dice anche l'altra metà:
**strozzare a 20 Mbit/s costante non avrebbe mostrato nulla**, esattamente come previsto.

---

## §3-bis · ⭐⭐ IL CONFRONTO APPAIATO — *le tre cure del 23 agosto, misurate*

> ⛔ **La domanda, una sola**: le tre cure applicate stamattina sono **in vigore**, e il
> comportamento è cambiato **dove doveva e solo lì**?
>
> ⚠ **Le ore sono quelle della macchina, che è UTC** e sta due ore indietro rispetto al portatile.
>
> ⛔⛔ **E «le tre cure» di questo capitolo NON sono «le cinque cure» di S.3** — è una collisione di
> nomi, e va sciolta qui o fra un'ora nessuno la scioglie più. Le tre di stamattina sono:
> **cura 1** = il **riordino dell'audio** in `pagina.html` (= la **cura 4** di S.3, §5.4) ·
> **cura 2** = la riga del codificatore che dice **i valori** (*«QP 26»*, non *«QP costante»*) ·
> **cura 3** = le **dichiarazioni** del livello e dei parametri in vigore. ⇒ Le cure 2 e 3 sono la
> *«sesta cosa»* di S.3: non cambiano un pixel, cambiano che cosa il registro sa dire.
> ⚠ Le altre quattro di S.3 — il crollo, la soglia della coda, la risalita, il tetto di banda —
> sono state scritte **dopo** queste misure, e **non sono state misurate qui**.

### 3.11 ⭐ IL «DOPO» ESISTE, E IL «PRIMA» È RIMASTO VIVO — *08:45 – 08:48*

| | |
|---|---|
| l'albero del **dopo** | `/media/REMOTIX/src/09b-src` — ⛔ **non** `09-src`, che è quello che gira sulla 7900: se la costruzione fosse fallita si tornava indietro senza ricostruire niente |
| la costruzione | `enter.sh --root 'bash /srv/src/09b-src/src/costruisci.sh'`, **08:47** · `make` uscito **0** · binario `/media/REMOTIX/src/09b-src/src/remotix` |
| ⛔ le due copie di `rcp.c` | `md5 eed49ac7bf007796f051e5db5bb425c7` — **identiche**, `src/` e `banchi/rcp/`, o il Makefile rifiuta |
| il server del dopo | porta **7910**, unità `remotix-7910.service`, lavoro `/media/REMOTIX/tmp/09b`, acceso **08:47:46** |
| ⭐ l'attrezzo sta nel deposito | `banchi/09-riavvia-7910.sh` — *«un attrezzo fuori dal deposito è un attrezzo che nessuno rilegge»* |
| A6 verificato | `⭐ VERIFICATO: il server e' fuori da ogni sessione utente (0::/system.slice/remotix-7910.service)` |
| il **prima** | 7900 **viva e intatta**, binario di stamattina, albero `09-src` — è il termine di paragone |

⛔⛔ **E IL «DOPO» È UN'ISTANTANEA DELLE 08:45, non «il codice di adesso»** — va scritto qui o fra
un'ora nessuno saprà più che cosa è stato misurato. Sulla 7910 gira **esattamente** questo:

| file | `md5` di quel che gira sulla 7910 |
|---|---|
| `src/codificatore.c` | `a35938a8c1fe8f22c4d9bf4c064bc13e` |
| `src/codificatore.h` | `bfb22009e166c23556e1a302f32b2395` |
| `src/figlio.c` | `f300a36ca2b07bfdffe1e72867b5edfd` |
| `src/pagina.html` | `e010d615f10643d5c6e2a2c01ae5ff25` |
| `src/rcp.c` = `banchi/rcp/rcp.c` | `eed49ac7bf007796f051e5db5bb425c7` |

⚠ Nel pomeriggio altri hanno continuato a lavorare sul deposito: alle 09:55 `codificatore.c`,
`codificatore.h`, `figlio.c`, `webtransport.c`, `main.c` e `figlio.h` **non combaciano più** con
questa istantanea (`pagina.html` e `rcp.c` sì). ⇒ ⛔ **Questi numeri valgono per le tre cure come
erano alle 08:45, e per niente altro**: chi vuole giudicare il lavoro del pomeriggio deve
ricostruire e rimisurare.

⚠ **E i banchi hanno preso porta, albero e cartella dall'ambiente** (`LAV`, `DENTRO_ALB`,
`DENTRO_LAV`, `ALB_NOME`, `PORTE_AMMESSE`), coi **difetti invariati**: ogni giro di stamattina si
rifà identico senza scrivere niente. ⛔ E `pulizia()` adesso **dichiara** le porte che tollera
invece di pretenderne una sola: due server accesi non sono sporcizia, misurare in due lo è.

### 3.12 ⛔⭐⭐ LE TRE CURE SONO IN VIGORE — le righe, **testuali** — *08:51:26 – 08:51:29*

⛔ È la lezione **E1**, *«scritto non è in vigore»*: le righe si riportano come sono uscite, e
accanto c'è il **controllo** — la stessa sessione sulla 7900 non le ha.

**Cura 2 — il codificatore** (`08:51:29.083`, canale `video`):

> `aperto: HEVC 8 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD driver … ⚠ EncSliceLP, bassa potenza — NON e' la codifica piena) · 1920x1080 · **QP 26 costante** · chiavi solo su richiesta`
>
> `la scala della degradazione, coi valori in vigore: **QP 26 → QP 35 → QP 44 → QP 51** — passo 9 (CRF_PASSO), fondo 51, uscita dal senza-perdita a CRF 24 (CRF_DI_EMERGENZA), e un DELTA si abbandona dopo 3 ricodifiche (RICODIFICHE_MASSIME).  ⚠ Una CHIAVE non si abbandona mai (RCP.md §5.2): per lei la scala si percorre fino in fondo`
>
> `la risalita della qualita' e' **SPENTA** (invariante I6): scesa una volta, la qualita' resta giu' per tutta la sessione — e questa riga e' il perche', non «non ha mai dovuto scattare».  ⚠ Si accende con \`codificatore_qualita_risale(true)\`, e da spenta questi numeri (**120 fotogrammi, 2097152 byte, scalino 9, punto di lavoro QP 26 costante, tetto d'attesa 3840**) non hanno nessun effetto`

⭐ **La riga dei parametri dice i VALORI, non le parole**: «QP 26», non «QP costante». ⛔ Il
controllo: la stessa riga sulla **7900** dice `… · 2560x1080 · **QP costante** · chiavi solo su
richiesta` — il numero non c'è.

**Cura 3 — le dichiarazioni** (`08:51:26.861` `rcp`, `08:51:26.961` e `08:51:29.097` `figlio`):

> `il client dichiara video.livello=5.1 (= 5.1, cioe' level_idc 51 in H.264 e L153 in HEVC): §4.3 vieta al server di emettere un flusso PIU' ALTO di questo`
>
> `⚠ e il livello PRODOTTO non si legge da qui: sta nella riga «PRIMO fotogramma codificato» del figlio, campo «livello» (§4.3 riga 701) — il confronto lo fa chi legge il registro, il programma NON lo fa ancora`
>
> `⭐⛔ PARAMETRI IN VIGORE (fase 9), quel che il figlio CHIEDE: cadenza **60/s** · tela alla nascita **1920x1080** · GOP INFINITO (chiavi_ogni = 0: chiavi solo a richiesta, §5.2 — e' una scelta, non una dimenticanza)`
>
> `⭐⛔ PARAMETRI IN VIGORE (fase 9), qualita' e codificatore CHIESTI: **QP 26** in hardware · **CRF 20** sul ripiego in software (due grandezze diverse, non si confrontano) · nodo **/dev/dri/renderD128** · entrypoint **EncSliceLP (bassa potenza)**`
>
> `⭐⛔ §4.3 — LIVELLO PRODOTTO: **4.0** (nell'SPS e' 120, cioe' general_level_idc, che e' il triplo) · stringa per il decodificatore «hev1.1.6.L120.B0».  ⛔ §4.3 vieta di superare il \`video.livello\` del client: il numero CHIESTO sta nella riga «il client dichiara video.livello=…» di \`rcp\`, e il confronto fra le due righe lo fa CHI LEGGE — il programma NON lo fa`

⭐⭐ **E il confronto, fatto da chi legge, dà il verde al primo colpo**: il client chiede **5.1**,
il server produce **4.0** ⇒ §4.3 è rispettata. ⛔ Fino a stamattina quel confronto **non si poteva
fare da fuori**: uno dei due numeri non era scritto da nessuna parte.

**Il controllo — la 7900 non ha nessuna di queste righe.** `grep -c` sul suo registro:

| riga | 7910 (dopo) | 7900 (prima) |
|---|---|---|
| `PARAMETRI IN VIGORE` | 2 | **0** |
| `la scala della degradazione` | 1 | **0** |
| `risalita della qualita` | 1 | **0** |
| `LIVELLO PRODOTTO` | 1 | **0** |
| `il client dichiara video.livello` | 1 | **0** |

**Cura 1 — i contatori dell'audio** (letti **sulla pagina servita**, non nel sorgente):

| | 7910 (dopo) | 7900 (prima) |
|---|---|---|
| `audio_posto_passato` (la frontiera calcolata) | **2** occorrenze | **0** |
| `" tardivi " + c.scartati_tardivi` sulla riga di stato | **1** | **0** |

⇒ ⭐ La pagina curata **è quella che il server del dopo consegna**: `curl https://192.168.0.2:7910/`
la porta, `…:7900/` no. ⚠ La pagina si legge **una volta all'avvio** (`pagina.c:627`) — questo è
il controllo che quel riavvio è servito.

### 3.13 ⭐⭐⭐ IL RISVEGLIO: **identico** — *7900 alle 09:07–09:09, 7910 alle 09:18–09:20*

> Stessa scena (`04-b30-scena --movimento pieno`), stesso utente `prova`, tela 1920x1080,
> **30 colpi per punto**, linea larga. ⛔ **Uno per volta**: fra i due giri la macchina è stata
> rimessa a zero (nessun palco vivo, nessuna disciplina).

| quiete | **7900 · mediana** | p95 | primo fotogramma | **7910 · mediana** | p95 | primo fotogramma |
|---|---|---|---|---|---|---|
| **0,2 s** | **12,4 ms** | 12,9 | 2 988 B | **12,0 ms** | 12,5 | 2 981 B |
| **2,0 s** | **11,9 ms** | 12,4 | 2 880 B | **12,4 ms** | 13,2 | 2 889 B |
| **15,0 s** | **12,1 ms** | 12,7 | 2 928 B | **12,7 ms** | 13,2 | 2 878 B |

⭐⭐ **Identico**: la differenza fra i due server è **0,4–0,6 ms su 12**, cioè meno della
differenza fra due quieti dello stesso server. ⛔ E non è una mediana che nasconde una coda: i
p95 stanno fra 12,4 e 13,2 su tutt'e sei i punti. ⭐ Il **primo fotogramma** è `delta` 180 volte
su 180 e pesa **2 878 – 2 988 byte**: i due server si discostano di **meno dello 0,5 %**.

⚠ E i 13 ms di stamattina (§3.6) sono diventati 12: la macchina è la stessa, la sessione è nuova.
⛔ **Per questo il «prima» è stato rimisurato adesso invece di credere al numero delle 07:46** —
un confronto appaiato si fa con due misure vicine, non con una di tre ore fa.

**Dove vanno**: pixel→codifica **9,2–9,9 ms** · la codifica **2,5–2,6 ms** · codifica→`SPEDITO`
**0,0 ms**, sui due server allo stesso modo.

### 3.14 ⭐⭐ I1 — A SCENA FERMA, **identico** — *7910 alle 09:31–09:33, 7900 alle 09:35–09:38*

> Banco `09-b68-ritmo.py tutto --secondi 30`, utente `prova`, tela 1920x1080, linea larga.

| scena | **7900** fot/s | K + Δ | carico video | filo `lo` | **7910** fot/s | K + Δ | carico video | filo `lo` |
|---|---|---|---|---|---|---|---|---|
| **ferma** | **0,07** | 1 + 1 | 5 559 B · 1,5 kbit/s | **2,429** Mbit/s | **0,07** | 1 + 1 | 5 565 B · 1,5 kbit/s | **2,431** Mbit/s |
| **barra** | 37,03 | 1 + 1 110 | 62 036 040 B · 16 543 kbit/s | 19,925 | 34,60 | 1 + 1 037 | 58 005 654 B · 15 468 kbit/s | 18,790 |
| **pieno** | 39,97 | 1 + 1 198 | 4 936 055 B · 1 316 kbit/s | 3,920 | 40,17 | 1 + 1 204 | 5 038 472 B · 1 344 kbit/s | 3,947 |
| **ferma** *(ripetuta)* | **0,07** | 1 + 1 | 5 556 B | 2,431 | **0,07** | 1 + 1 | 5 551 B | 2,431 |
| abbandoni §5.1 · chiave trattenuta §5.2 | **0 · 0** | | | | **0 · 0** | | | |
| audio `vecchi` del cliente | **0** | | | | **0** | | | |

⭐⭐ **La misura che conta è il costo PER FOTOGRAMMA, non il conto dei fotogrammi**: su `barra`
sono **55 838** byte (7900) contro **55 882** (7910), cioè **lo 0,08 % di differenza**. ⇒ Il
codificatore fa la stessa cosa; a ballare del 6 % è **quante volte Mutter consegna**, che è la
stessa grandezza di §3.1 e non è nostra.

⛔ **E l'audio sul percorso locale conferma la premessa della cura 1**: `vecchi` **0** su
tutt'e due, in tutt'e quattro i giri. Non c'era niente da curare, e infatti non è cambiato niente.

⚠ `barra` qui costa **16–20 Mbit/s** contro i 579 kbit/s di §3.1: quelle erano anteprime della
vista d'insieme (§3.7), queste no. ⛔ Il confronto che vale è **colonna contro colonna**, non
contro stamattina.

### 3.15 ⭐⭐⭐ LA BANDA A 2560x1080: **identica al byte** — *7910 alle 09:44 e 09:51, 7900 alle 09:47*

> Banco `09-b72-banda.py punti`, utente **`prova2`**, tela **2560x1080**, **25 s** per punto,
> linea larga. Il punto «video» è il **desktop vero dell'utente**: `scena-utente.webm` a schermo
> intero in `firefox-esr`, cioè il contenuto per cui il prodotto esiste.

| punto | **7900** fot/s | **carico video** | % di 20 Mbit/s | B/fotogramma | filo `lo` | **7910** fot/s | **carico video** | % | B/fot | filo |
|---|---|---|---|---|---|---|---|---|---|---|
| **ferma** | 0,00 | **0** | 0 % | — | 2,427 | 0,04 | **632 B** | 0 % | 632 | 2,427 |
| **pieno** | 41,00 | **1,159 Mbit/s** | 5,8 % | 3 532 | 3,683 | 41,28 | **1,159 Mbit/s** | 5,8 % | 3 508 | 3,687 |
| **video** *(desktop vero)* | 21,96 | **0,193 Mbit/s** | **1,0 %** | 1 099 | 2,666 | 21,92 | **0,195 Mbit/s** | **1,0 %** | 1 112 | 2,667 |

⭐⭐⭐ **`pieno`: 3 620 466 byte contro 3 620 630, su 25 secondi e ~1 030 fotogrammi.** Sono
**164 byte di differenza su 3,62 MB — lo 0,005 %.** ⛔ Non «simile»: lo stesso codificatore che
fa la stessa cosa.

⭐ **E il desktop vero costa l'1,0 % del pavimento su tutt'e due** — 0,193 contro 0,195 Mbit/s,
cioè il numero di §3.8 (0,204) ritrovato due volte a distanza di quattro minuti.

⚠ Il punto `pieno` sulla 7910 è stato **rifatto alle 09:51**: al primo giro la scena non era
partita — `⛔ shm_open(//09-b68): Permission denied`, il segmento di memoria condivisa era rimasto
di `prova` (uid 1001) dal banco di I1 e `prova2` (1002) non poteva aprirlo. ⛔ **Difetto del
banco**, non del prodotto: `09-b68-scena.sh` non ripulisce `/dev/shm/09-b68` fra due utenti
diversi, e il sintomo è «la scena non parte», che è muto sul perché.

### 3.16 ⛔⛔ L'AUDIO SOTTO `netem` — **e qui mi fermo: il banco prescritto NON PUÒ vedere la cura 1**

> `banchi/07-b64-rete.py netem --solo 2-jitter --secondi 25` — `netem delay 20ms 2ms` su `lo`,
> **solo la porta misurata**, `enp7s0` mai toccata, guardiano armato. Uno per volta:
> 7900 alle **09:41**, 7910 alle **09:45**.

| | **7900 · il PRIMA** | **7910 · il DOPO** |
|---|---|---|
| spediti dal server | 5 005 | 5 005 |
| ricevuti | 3 966 | 4 006 |
| **`vecchi` (scartati §6.3)** | **1 024** | **980** |
| **purezza** | **0,1149** | **0,1235** |
| resa campioni | 0,79495 | 0,80281 |
| buchi d'istante · scoppiettii/s | 938 · 42,31 | 917 · 41,24 |

⛔⛔ **La previsione era «0,175 → ≥ 0,95». È uscito 0,1149 → 0,1235, cioè NIENTE. E il numero
non smentisce la cura: smentisce il banco.**

⭐ **La ragione, e si legge nel codice del banco, non nel prodotto.** Chi scarta i datagram
sorpassati in questo giro **non è `pagina.html`**: è il cliente di prova, `banchi/01-b3-cliente.py`
riga **743**, che ha la **sua** copia della regola di §6.3 —

```python
if self.a_ultimo_istante is not None and istante <= self.a_ultimo_istante:
    self.a_vecchi += 1
    return
self.a_ultimo_istante = istante
```

— cioè **esattamente la riga vecchia**, quella che confronta con l'**ultimo arrivato**. La cura è
stata scritta in `src/pagina.html`, che in questo banco **non gira mai**. ⇒ `vecchi` e `purezza`
qui **devono** essere uguali sui due server, e lo sono.

⭐⭐ **E la prova che è così, non l'argomento**: `md5sum` di `01-b3-cliente.py` nei due alberi —
`13e68d19ed44298b7926cded53affdda` in `09-src` **e** in `09b-src`. **Lo stesso file, byte per
byte.** Un banco che misura se stesso non può dare che lo stesso numero.

⛔ **Quindi mi fermo su questa cura, e dico perché**: `07-b64-rete.py` è un banco del **trasporto**
— misura quanti datagram passano il filo e quanto è puro il tono che ne esce — e la cura 1 vive
nel **cliente vero**, cioè nella pagina. Le due metà non si toccano.

**Che cosa È stato verificato della cura 1**, e che cosa **no**:

| | |
|---|---|
| ✅ la pagina curata è **consegnata** dalla 7910 e non dalla 7900 | §3.12, letto con `curl` sulla porta |
| ✅ i quattro contatori nuovi (`tardivi`, `fuori`, `rec`, `dop`) sono **sulla riga di stato** e **escono da `audio_conti()`** verso `/diario` | letto nella pagina servita |
| ✅ sul **percorso locale** i `vecchi` sono **0**, come previsto ⇒ non c'era niente da allentare | §3.14 |
| ⛔ **NON verificato**: che sotto riordino vero la purezza salga a ≥ 0,95 | serve un banco che faccia girare **la pagina**, non il cliente di prova |

⭐ **Che forma avrebbe quel banco**, perché la prossima volta non si ricominci da capo: un
**browser vero** che apre `https://192.168.0.2:PORTA`, entra come `prova`, e i cui contatori si
leggono **senza chiedere niente all'utente** — la pagina li manda già da sé al server ogni 5 s
(`pagina.html:6402`, `fetch("/diario?" + riga)`), e la riga porta tutt'e quattro i numeri nuovi.
⇒ Il registro del server diventa il verbale. ⛔ **Il pezzo che manca è dove far girare il
browser**: sulla macchina Firefox 140 ESR c'è, ma vive **solo dentro una sessione di REMOTIX**
(non c'è `Xvfb`), e puntarlo al server che lo sta catturando è uno specchio; e il `netem` deve
restare su `lo`, perché **`enp7s0` non si strozza mai**. ⚠ È una scelta di banco, e va fatta
prima di scriverlo — non dopo.

### 3.17 ⛔⛔ DUE FALSI ALLARMI DEL BANCO, E VALGONO PIÙ DI UN NUMERO

**1. «Il dopo è più lento e i suoi fotogrammi pesano il doppio» — *08:52, e non era vero*.**
Il primo giro del risveglio sulla 7910 ha dato mediana **13,4 / 14,0 / 13,8 ms** contro i
**12,4 / 11,9 / 12,1** della 7900, e primo fotogramma **6 141 / 5 872 / 5 812 byte** contro
**2 988 / 2 880 / 2 928**: il **doppio**, sistematico su 90 colpi, con la stessa scena.

⛔ La causa non era il prodotto: era **un palco orfano di stamattina** — il figlio di `prova2`
rimasto vivo sulla 7900 dopo il banco della banda delle 08:30 (invariante I4: il palco sopravvive
al distacco) — che continuava a catturare e codificare sulla **stessa GPU integrata**. Chiuso
quello e rifatta la misura sulla macchina pulita, il dopo ha dato **12,0 / 12,4 / 12,7** e primo
fotogramma **2 981 / 2 889 / 2 878**: identico al prima.

⇒ ⭐⭐ È `LEZIONI.md` §1.26 preso in flagrante: **non ha dato un rosso, ha dato un numero
plausibile** — e quel numero, creduto, avrebbe accusato tre cure innocenti. ⚠ E la riga che lo
denunciava era stampata dal banco stesso e non l'avevo pesata: *«fotogrammi usciti DURANTE le
quieti: **1 · 1 · 7**»* contro *«0 · 0 · 0 (il desktop era davvero fermo)»* del giro pulito.

**2. «Il dopo non spedisce quasi niente» — *09:29, e non era vero*.**
Il primo giro di I1 sulla 7910 ha dato `barra` a **0,17 fot/s** e **13 kB** sul filo in 30 s. Nel
registro la causa, testuale:

> `09:29:05.841 rcp     posto NEGATO a prova da [192.168.0.2]:55729: lo occupa un altro client di questo stesso utente (occupati: 1)`
>
> `09:29:12.006 rcp     STACCATO per silenzio: 30002 ms senza un PACCHETTO da [192.168.0.2]:33357 — e l'ultimo byte di RCP e' di 657637 ms fa`

⇒ Il cliente del banco precedente era stato **ucciso** invece che congedato, e il server ha tenuto
il suo posto fino ai **30 secondi di silenzio** di §5.3 — cioè per tutto il primo giro. È lo stesso
difetto già scritto in `banchi/09-b71-sessione.sh` (`[M]` 23 ago 08:06), che lì è curato mandando
`TERM` e aspettando; ⛔ **ma fra un banco e il successivo l'attesa non c'è**, e nessuno la fa.

⚠ **Regola operativa che ne esce**: fra due banchi sullo stesso utente si **verifica che il posto
sia libero** (nessun `01-b3-cliente.py` vivo **e** nessun palco), non si conta il tempo.

---

## §4 · ⛔⛔⛔ IL CROLLO DELLE 08:28:09 — la causa, provata riga per riga

> **Diagnosi del 23 agosto 2026, pomeriggio.** ⭐ La cura è stata **applicata lo stesso giorno**
> (§5.1). ⚠ Quel che segue è la *causa*, non il racconto della caccia.

### 4.1 ⭐⭐⭐ La causa, in una riga

`src/webtransport.c` (albero `09-src`, quello che ha girato) **liberava** i byte di un fotogramma
appena ngtcp2 li aveva *serializzati*. Il contratto di `ngtcp2_conn_writev_stream()`
(`/media/REMOTIX/src/b2/ngtcp2/lib/includes/ngtcp2/ngtcp2.h:5246-5250`) dice l'opposto:

> *«The caller must keep the portion of data covered by `*pdatalen` bytes **in tact** until
> `ngtcp2_callbacks.acked_stream_data_offset` indicates that they are acknowledged by a remote
> endpoint or the stream is closed.»*

⇒ **Uso dopo la liberazione.** `ndatalen` dice quanti byte sono finiti **in un pacchetto**, non
quanti sono **confermati**. La callback dell'ack **esisteva** (`trasporto.c:506`) ma inoltrava a
nghttp3 e basta: nessuno la consultava prima del `free`.

⭐⭐ **E il difetto c'era a OGNI fotogramma ritrasmesso, da sempre.** Quello da 525 298 byte è
stato solo il primo abbastanza **grosso** da farlo diventare rumoroso.

### 4.2 La prova che è rimasta sulla macchina — ⭐ `dmesg` ha salvato la giornata

⛔ Nessun core: `coredumpctl` non è installato e `core_pattern` vale `core` (nome relativo) nella
cartella di lavoro del servizio (`/`), dove non c'è. ⭐ Ma `dmesg -T`:

```
[Sun Aug 23 08:28:10 2026] remotix[14739]: segfault at 7f148e056fc2 ip 00007f1495a88b49
    sp 00007ffc182131f8 error 4 in libc.so.6[162b49,7f149594e000+163000]
```

| pezzo | che cosa dice |
|---|---|
| `error 4` | **lettura** in spazio utente di una pagina **non presente** — non una scrittura, non un permesso |
| `segfault at 0x7f148e05…` | zona **`mmap`**: non è la pila (`sp` è `0x7ffc…`), non è il mucchio `brk` di un PIE (`0x55…`) |
| `ip` a **scarto 0x162B49** in libc | `objdump`: `vmovdqu (%rsi),%ymm0` dentro `__memmove_avx_unaligned_erms` — la **primissima lettura di 32 byte dalla SORGENTE** |

⇒ `%rsi = 0x7f148e056fc2` **non è spazzatura** (non `NULL`, non `0xdead…`): è un puntatore
**verosimile** in una regione **non più mappata**. ⭐ **È la firma esatta dell'uso dopo la
liberazione di un blocco `mmap`.**

⭐ Il registro conferma la sequenza: il fotogramma **era stato copiato con successo**
(`coda_metti()` copia i byte prima che `SPEDITO` esca), fra `.895` e la morte (`.9237`) passano
**~28 ms** e **non succede altro che scrivere su QUIC** — nessun fotogramma 186, nessuna
ricodifica, nessun cambio di scena. E il salto è **146 → 525 298 byte**, ×3 600 in un fotogramma.

### 4.3 ⛔ I sei sospetti, ciascuno chiuso con la sua riga

| sospetto | la riga che decide |
|---|---|
| tetto **16 MiB** / ciclo delle **ricodifiche** | 525 298 byte è il **3,1 %** di 16 MiB, e *«si RICODIFICA»* compare **0 volte** nel giro morto |
| `abbassa_qualita()` / `chiudi_contesto()` con un pacchetto in mano | si chiama **solo** dal ramo del tetto, **mai preso**. ⚠ `fuori->dati = c->pacchetto->data` resta un difetto **reale in attesa** — ma non è quello del 23 agosto |
| **coda d'uscita** `WT_CODA_MAX` (17 MiB) | 525 KB entrano larghi; *«NON entrano in coda»* e *«la coda ha toccato il tetto»*: **0 volte** |
| `video_sgombra()` / `WT_INVOLO_MAX` | ⭐ **ed è escluso per la ragione buona**: fa `shutdown_stream_write()` **prima** di buttare i byte, ed è **corretto**. ⛔ Il suo commento — *«PRIMA si azzera lo stream, POI si buttano i byte»* — dimostra che **la regola era conosciuta**, e rende più netto che l'altro punto quella protezione non ce l'avesse. Inoltre non è stata nemmeno chiamata: nessun fotogramma è arrivato dopo il 185 |
| **copia zero** (fase 8), passo multiplo di 64 | 2560 px → passo 10 240 = 64 × 160 ✔; e comunque è la strada d'**ingresso**, già finita bene alle `.894` |
| il **magazzino** dei fotogrammi | è quello delle **superfici VAAPI**, di misura fissa e aperto una volta col contesto |

### 4.4 ⭐⭐⭐ Perché **quel** fotogramma e non gli altri 45 004 — e perché il giro dopo non è morto

L'allocazione della coda raddoppia da 64: per 525 298 byte la capacità sale a **1 MiB**. Sopra i
**128 KiB** (`M_MMAP_THRESHOLD` di serie) glibc serve con `mmap`, e `free()` fa `munmap`: **la
regione sparisce**. Sotto, il blocco resta nel mucchio e la lettura sbagliata **legge spazzatura
senza far rumore**.

| classe di capacità, nel giro morto | quanti |
|---|---|
| **> 512 KiB** ⇒ capacità 1 MiB, `mmap` | **1** ← il fotogramma 185 |
| > 128 KiB | 0 |
| ≤ 128 KiB (mucchio, **silenzioso**) | **45 004** |

⇒ **L'unico `free()` che abbia davvero smappato una regione in 1 h 50 min**, dunque l'unica volta
in cui il puntatore penzolante di ngtcp2 ha trovato una pagina assente invece di mucchio riciclato.
⭐ E il secondo moltiplicatore: 525 298 byte sono **~370 pacchetti** a raffica — che almeno uno sia
dichiarato perduto (o che scatti una sonda PTO) nei 28 ms successivi è **quasi certo**. Con un
delta da 146 byte il pacchetto è **uno**.

⭐⭐ **E il giro dopo — 586 fotogrammi, punte oltre 500 KB — non è morto per la stessa ragione
letta al contrario: la soglia di `mmap` di glibc è dinamica.** Liberando un blocco `mmap`,
`munmap_chunk()` **alza** `mp_.mmap_threshold` alla misura di quel blocco. ⇒ Dopo il **primo**
buffer da 1 MiB liberato, i successivi arrivano dal mucchio e l'uso dopo la liberazione torna
**silenzioso**: byte di spazzatura sul filo invece di un `SEGV`.

⇒ ⛔ **Non è la dimensione da sola.** È: *la prima volta che un blocco grosso viene liberato mentre
ngtcp2 lo tiene ancora per la ritrasmissione.*

### 4.5 ⏳ Come si riproduce — ⛔ **non eseguito**, e la previsione è falsificabile

| ricetta | come | **previsione** |
|---|---|---|
| ⭐ **A** — deterministica, senza rete e senza root | `Environment=MALLOC_MMAP_THRESHOLD_=32768` nell'unità (⭐ dall'ambiente **spegne l'adattamento dinamico**: ogni fotogramma sopra i 32 KiB diventa `mmap`/`munmap`, e il difetto smette di essere silenzioso **per sempre**), poi un fotogramma grosso e `kill -STOP` al browser per ~1 s ⇒ nessun ack ⇒ PTO ⇒ ritrasmissione | `SEGV`, `error 4`, `ip` in libc, sempre in `__memmove_avx_unaligned_erms`. ⛔ **Se non muore, questa diagnosi è sbagliata** |
| **B** — la perdita vera | come A al punto 1, poi `netem loss 5%` e il film che scorre | muore in pochi secondi |
| ⭐ **C** — la prova che nomina la riga | ricostruire con `-fsanitize=address -g -fno-omit-frame-pointer` e rifare A o B | `heap-use-after-free READ` con **due** pile: quella che legge (`ngtcp2_pkt_encode_stream_frame`) e quella che ha liberato (`coda_uccidi` ← `wt_scrivi`). ⭐ **Chiude il caso senza margine** |

### 4.6 ⛔ La cura: perché la (a) e non la (b)

- ⭐ **(a) la sobria — quella applicata**: non si libera alla serializzazione; si marca
  `consegnato`, si toglie dalla scelta di `coda_scegli()`, e il `free` lo fa l'ack quando l'offset
  confermato copre `dati.n`, oppure la chiusura/reset dello stream. ⚠ **Costo**: la memoria di un
  fotogramma resta impegnata per un giro di rete in più, e `WT_CODA_MAX` va riletto con quel conto
  in mano — 16 sessioni × un fotogramma in più in volo;
- ⛔ **(b) la spiccia — rifiutata**: `ngtcp2_conn_shutdown_stream_write()` prima del `free`, come fa
  `video_sgombra()`. **Non va bene qui**: quello *azzera* lo stream, e §6.2 vuole il fotogramma
  **completo**. Sarebbe **barattare un crollo raro con un fotogramma rotto sempre**.

### 4.7 ⏳ La trappola da armare comunque — ⛔ non armata

Anche con la causa in mano, **la macchina non era attrezzata per farsi raccontare una morte**.

1. ⛔ **nessun core dump** ⇒ installare `systemd-coredump`, **oppure**
   `core_pattern = /media/REMOTIX/tmp/09/core.%e.%p.%t` (**assoluto**). `LimitCORE=infinity` c'è già;
2. ⛔ **il registro è condiviso e viene sepolto**: la coda del 08:28 sta a metà di un file da 22 MB
   e i giri successivi ci scrivono sopra ⇒ un `ExecStopPost=` che, se il codice d'uscita non è 0,
   copia le ultime ~2 000 righe in `morte-%t.log` **insieme a `dmesg -T | tail -50`**;
3. ⭐ **`dmesg` va raccolto SEMPRE allo spegnimento**, non solo quando qualcuno se lo ricorda: è
   quello che ha salvato la giornata;
4. ⭐⭐ **`MALLOC_MMAP_THRESHOLD_=32768` + `MALLOC_PERTURB_=165` sul banco.** Il primo trasforma
   ogni uso-dopo-liberazione **grosso** da silenzioso a fatale; il secondo riempie di `0x92…` la
   memoria liberata, così anche i casi piccoli smettono di sembrare dati buoni. ⛔ **Sul banco, non
   nel prodotto**: sono lenti.

### 4.8 ⛔ Che cosa di questa diagnosi resta `[?]`

`[?]` **La ritrasmissione non è stata vista con gli occhi.** Il registro non conta i pacchetti
perduti e il core non c'è. La catena — contratto violato → `frame_chain` che conserva il puntatore
→ `rtb_on_pkt_lost` → `streamfrq_push` → `ngtcp2_pkt.c:1619 ngtcp2_cpymem()` — è letta **riga per
riga nel codice di ngtcp2 presente sulla macchina**, non osservata in volo. ⇒ Finché non gira §4.5,
è una **causa probabile con la riga**, non una causa vista.

⭐ `[M]` **Tutto il resto è misurato**: la riga di `dmesg`, l'istruzione a `0x162B49`, il contratto
in `ngtcp2.h:5246-5250`, il `cpymem` a `ngtcp2_pkt.c:1619`, e il conto **1 su 45 005**.

---

## §5 · ⭐⭐ LE CINQUE CURE — il perché, il prezzo, e quel che ciascuna NON fa

> ⛔ **Il diff non sta qui.** È in `src/`, e i commenti nel codice sono la sede della ragione: dove
> questo documento ripeterebbe un commento, cita `file:riga` e si ferma. Quel che resta qui è **il
> perché della scelta**, **il prezzo** e **quel che è stato scartato**.

### 5.1 ⛔⭐ Cura 1 — il crollo · `webtransport.c:745-870`, `:5929`

Vedi §4 per intero. ⛔ **Nessun interruttore**: non cambia quel che si vede, corregge un modo di
morire. ⚠ **Non verificata**: la ricetta di §4.5 non è stata eseguita.

### 5.2 Cura 2 — la soglia sulla coda in `video_sgombra()` · `webtransport.c:2705-2800`

**Il difetto**: non c'era nessuna condizione fra *«esiste un fotogramma più recente»* e
*«abbandona»*. Su linea stretta un delta non esce in 33 ms ⇒ la condizione è **sempre vera** ⇒
l'abbandono è **sempre**, e ogni abbandono riaccende il debito di §5.2.

⭐ **La regola nuova, e sta tutta in una parola di `RCP.md`**: `:1156` dice che il server **PUÒ**
chiamare `RESET_STREAM`, non che **DEVE**. ⇒ un delta si abbandona **solo se la coda del video non
si svuota entro la soglia**. Sotto la soglia si **tiene**: gli stream sono indipendenti
(`RCP.md:1155`), quindi tenerlo **non blocca** quelli dopo.

⛔ **La soglia è 100 ms, e i quattro vincoli che la derivano** *(⚠ derivata, non dimostrata: il
banco la spazza a 50 · 100 · 200 e chi sceglie è l'utente, perché è un prezzo che si VEDE)*:

1. **più di un periodo di fotogramma**, o è la regola di oggi con un nome nuovo: `[M]` fase 8, il
   contenuto vero va a **20,9 fot/s = 47,8 ms**;
2. **meno del fondo con cui già si richiede una chiave** — `WT_CHIAVE_RICHIESTA_MS` = 150;
3. deve **lasciar passare una CHIAVE più qualche delta** dove il difetto morde: `[M]` una chiave
   sulla tela dell'utente misura **20 817 byte**; a 3 Mbit/s esce in **56 ms**, e nei 44 che
   restano ci stanno **tre delta**;
4. il prezzo si somma all'anello: `[M]` fase 8, l'anello intero è **55,20 ms**, e 100 + 55 sta
   sotto il quinto di secondo.

⚠ **Il ripiego dichiarato**: finché ngtcp2 non ha né `smoothed_rtt` né `cwnd` si assume **il
pavimento**, 20 Mbit/s = 2 500 byte/ms — e **la riga di registro dice quale dei due casi è**, invece
di far passare un numero inventato per misurato.

⚠ **E quel che la cura NON cambia**: `RCP.md:1165-1203` dà **tre forme** all'abbandono — **A**
(stream azzerato, se era già uscito un byte) · **B** (buco nei `numero`, se nessun byte era uscito)
· ⛔ **C** (il credito mancato: **nessuno stream, nessun buco, nessun segnale**, difetto B-18).
⛔ **Quale fra A e B il client veda non lo decide nessuno dei due lati**: dipende dal fatto che un
byte fosse uscito. ⇒ La cura **non tocca questo**: cambia **quante volte** succede, e **la forma C
non la tocca affatto**.

#### ⛔ I casi limite, nominati perché non si scoprano dopo

| caso | che cosa succede |
|---|---|
| **una CHIAVE in coda** | non si abbandona **mai** (`RCP.md:1256`). ⚠ Ma i suoi byte **contano nella somma**: con una chiave in coda la soglia si supera prima e i delta **dietro** di lei se ne vanno per primi — **che è giusto**, arriverebbero dopo di lei comunque |
| **nessuna stima** | ripiego a 20 Mbit/s: se la linea vera è più stretta il ripiego **sottostima** l'attesa e si tiene un delta di troppo, per un giro di rete |
| **elenco pieno** (32 posti) | un fotogramma fuori elenco non è abbandonabile **e i suoi byte non entrano nella somma** ⇒ coda sottostimata. ⚠ Oggi non può succedere: §2.3 concede 16 stream uni, il credito finisce prima |
| ⛔ **il momento dell'attraversamento** | si abbandona un delta **e** quello appena arrivato è a sua volta un delta ⇒ `rcp_video_apri()` lo rifiuta e **se ne perdono due**. ⏳ `[?]` Il rimedio — chiedere la chiave **prima** e abbandonare quando arriva — non è in questa cura e va misurato prima di scriverlo |
| **la scena si ferma** | `video_sgombra()` gira solo all'arrivo di un fotogramma ⇒ a desktop fermo non gira, ⭐ **e non serve**: senza fotogrammi nuovi non c'è niente da abbandonare |

#### ⛔⛔ E il rifiuto parziale, che è la parte più importante

**«Calare i fotogrammi tenendo i delta» — `RCP.md:1284` e `SPECIFICHE.md` §8.3 — NON si può fare in
`webtransport.c`, e questa cura non lo fa.** Il codificatore gira a **GOP infinito**
(`chiavi_ogni = 0`, `figlio.c:4146` — ⚠ `[R]` `rcp.c:3431` lo cita ancora come `figlio.c:1568`, che
oggi è un'altra funzione: **riferimento scaduto**): ogni delta predice dal fotogramma **codificato**
prima, non da quello **spedito**. ⇒ Qualunque fotogramma il trasporto salti — abbandonandolo (forme
A/B) o non accettandolo (forma C) — **rompe la catena e costa una chiave lo stesso**.

⭐ **L'unico posto dove si cala il ritmo senza rompere la catena è il palco**: si cattura e si
codifica meno spesso. ⚠ E la strada vicina è già chiusa da una misura: i **sotto-livelli
temporali** l'Intel non li produce (`EncRateControlExt` assente su **7 profili su 7**,
`sps_max_sub_layers = 1` su **6 celle su 6**).

⇒ ⭐ **Questa cura è un prerequisito, non la cura della fase.** Senza di lei il regolatore di §6
nascerebbe sopra un trasporto che abbandona comunque a ogni fotogramma, e non si potrebbe misurare
che cosa ha fatto.

### 5.3 Cura 3 — la risalita della qualità · `codificatore.c:3446`, `:141-143`

**Il difetto** `[R]`: `qualita_corrente` era **monotòna nel verso peggiore**. Quattro scritture in
tutto (`:1880` la semina, e le tre dentro `abbassa_qualita()`), **tutte in discesa**. Cercata e non
trovata la risalita in sei posti — `codificatore_ridimensiona()` riapre il contesto e **conserva**
il valore; `chiudi_contesto()`/`apri_contesto()` lo **leggono**; nessun `alza_qualita()` in tutto
`src/`; la `struct` è privata del file. ⇒ **La degradazione durava quanto la sessione.**

⛔ **E per un DELTA non è un gradino: sono tre in un colpo solo.** `abbassa_qualita()` è chiamata
**prima** del controllo dei tentativi ⇒ il delta che alla fine viene abbandonato ha comunque già
fatto scendere la scala **26 → 35 → 44 → 51**. ⇒ Un solo delta granuloso portava il codificatore a
QP 51 **e ce lo lasciava per sempre**, e l'abbandono del delta era dichiarato nel registro mentre la
degradazione permanente **no**.

⭐ **Dove è raggiungibile, misurato** — ed è la ragione per cui la cura è piccola e non urgente:

| | il cricchetto scatta? |
|---|---|
| `[M]` tela dell'utente 2560×1080, QP 26, 404 chiavi vere: max **21 433 byte = 0,13 %** del tetto, margine **782×** | ⛔ **no** — nemmeno il rumore uniforme ci arriva (15,1 %) |
| `[M]` 7680×4320 in hardware, desktop vero | ⛔ no (1,5 %) |
| `[M]` 7680×4320, grana `alls=60` in hardware | ⚠ **94,9 %** — **al confine** |
| `[M]` 7680×4320, rumore uniforme in hardware | ⛔ **sì**, 8 su 8 |
| ⛔ `[M]` **ripiego software `libx264` CRF 20, 7680×4320, filmato granuloso: 18,733 MiB, 1 su 8** | ⛔ **sì, con contenuto plausibile** |

⇒ Raggiungibile per **una via sola e stretta**: la tela grande **più** il ripiego software. E le due
si tengono per mano: `[M]` `h264_vaapi` su questo chip si ferma a **4096 px per lato**, e la tela
legale di `RCP.md` §4.5 arriva a 7680 ⇒ **oltre i 4096 il ripiego software non è un'eventualità, è
la regola**.

⛔ **Il morso vero non è il fotogramma perso: è quel che resta dopo.** Il fotogramma granuloso dura
un secondo; da lì in poi il desktop — testo, finestre, scena ferma — usciva a **CRF 47** o **QP 51**
**per ore**, e nessuna riga diceva perché. ⇒ È il *«mai sgranare»* di `DECISIONI.md` §3.3 perso
**per inerzia** invece che per decisione.

**Il vincolo che decide DOVE va il codice**: `chiudi_contesto()` fa `av_packet_free()` ⇒ la risalita
**non può** stare dopo `break`, dove `fuori->dati` punta dentro il pacchetto: sarebbe lo stesso
difetto di §4. ⇒ **si conta alla consegna, si risale all'ingresso del fotogramma dopo**, e come
effetto secondario il costo della riapertura (`[M]` **91-108 ms** in hardware, **1,8-3,3 s** in
software) cade **fra** due fotogrammi.

⛔ **E non è simmetrica alla discesa, di proposito**: si scende di tre scalini in un fotogramma, si
risale di **UNO** ogni `RISALITA_ATTESA`, con l'attesa che **raddoppia** a ogni ricaduta
(`RISALITA_ATTESA_MAX` ≈ 64 s). ⚠ I tre numeri sono `[?]` **sufficienti, non giusti**, come
`CRF_PASSO` = 9.

⭐ **Perché non viola I1**: I1 parla del **ritmo**, questa cura della **qualità** — e le due leve le
ha già separate l'utente (§3.3: *«si calano i fotogrammi. Mai sgranare»*). ⇒ La cura non tocca la
leva di I1: **restituisce** quella di §3.3. ⛔ L'unico punto in cui potrebbe toccare il ritmo è la
**riapertura**, ed è per questo che l'attesa raddoppia — senza, una scena al confine farebbe una
riapertura ogni 2 secondi, **e quello sì sarebbe I1**.

⛔ **Il guasto che ucciderebbe questa cura si chiama SBATTIMENTO, e non è ipotetico**: la grana
`alls=60` a 7680×4320 sta al **94,9 %** del tetto, cioè è una scena che vive **esattamente sul
confine**. In software basterebbero pochi giri (1,8-3,3 s ciascuno) perché **la cura costi più del
difetto**, e a pagare sarebbe il **ritmo**. ⇒ Il banco che decide è in §7.3.

### 5.4 Cura 4 — il riordino dell'audio · `pagina.html:5882`, `:5992`, `:6507`

**Il difetto**: `pagina.html` scartava confrontando con l'**ultimo datagram ARRIVATO**, mentre
`RCP.md` §6.3 dice *«già **consumati**»*. ⇒ **si buttava materiale che ci starebbe cinquanta volte
dentro il cuscino già pagato**: un datagram sorpassato di **1 ms** distrutto mentre **250 ms** di
memoria stanno fermi a non fare niente. Lo squilibrio fra il danno e la riserva è di **1 a 250**.
⚠ Lo scarto costa un buco di **5 ms** (PCM) o **20 ms** (Opus), **udibile**.

`[M]` **La misura che lo dimostra**, col `netem`: ritardo di **30 ms fissi** (che non riordina) ⇒
purezza **1,000**; **jitter ±2 ms** ⇒ purezza **0,175**, con **1 004 datagram scartati su 4 989**
(il 20 %). ⇒ ⭐ **Non era il ritardo: era il riordino**, e la cura è **gratis**.

⭐ **La frontiera esisteva già e non andava aggiunta: andava CALCOLATA.** `a.base` porta un
`istante` del server nell'orologio dell'`AudioContext`, `ctx.currentTime` è la testina ⇒
`frontiera_us = (ctx.currentTime − a.base) × 1e6`, e un blocco è *già consumato* **se e solo se**
`istante < frontiera_us`. ⛔ **Costa zero memoria e zero ritardo**: è una sottrazione su numeri che
esistevano da prima.

⚠ **E `a.ult_ist_us` non poteva fare da confine** anche se era il candidato naturale: si scrive in
`onended`, sul thread principale — quello che si ferma a decodificare i fotogrammi — non è monotòno
appena si accettano i fuori ordine, e ci sono appesi sopra `ult_quando_perf`/`aoff`, cioè **il metro
della distanza audio-video**. ⇒ Farne il confine vorrebbe dire far dipendere il metro dal riordino.

⛔ **Il secondo pezzo è necessario, e senza di lui la cura sarebbe peggio del difetto**: la pagina
trattava *«il posto di questo blocco è passato»* come **un caso solo** e riarmava l'ancora, cioè
spostava tutta la riproduzione avanti di **250 ms**. Giusto quando è **la riproduzione** a essere in
ritardo, sbagliatissimo quando è **un singolo blocco** ad arrivare dietro a uno più nuovo: si
pagherebbero **250 ms per un blocco da 5**, a ogni sorpasso. ⇒ `a.ist_max_us` separa i due casi.

⭐⭐ **E per strada si è trovato un difetto che non era nel mandato**: la sentinella
dell'*«ancora finta»* confrontava con `a.ult_ist_us` — l'ultimo blocco **FINITO**, vecchio di un
cuscino intero. A regime `salto ≈ 250 000 µs` e `passo_us = 5 000` ⇒ `salti_suono` guadagnava **~49
punti a ogni blocco sano** ⇒ la condizione `salti_suono === 0` **non poteva essere vera mai**, e la
riga che sorveglia l'ipotesi su cui poggia tutta la cura dell'ancora **era morta**. Riparata con la
stessa variabile che la cura introduce.

⛔ **E il prezzo è ZERO, con il segno al contrario di quel che `SPECIFICHE.md:128` teme**: nessuna
memoria intermedia, nessuna coda di riordino, `AUDIO_CUSCINO_MS` **non si tocca**, 4 interi per
sessione. ⭐ Ogni sorpasso curato è un riarmo **risparmiato**, e un riarmo costa `+250 ms` ⇒ sotto
riordino la cura **abbassa** il ritardo medio.

⭐ **E la cura comoda che questo vincolo uccide, scritta perché nessuno la ripeschi**: *«teniamo i
datagram in una coda ordinata per `istante` e li consegniamo con un ritardo fisso»*. È il jitter
buffer classico, è quello che tutti scrivono, e **venderebbe X ms di risposta per comprare la
fluidità che l'ancora dà già gratis** — l'ancora *è già* la de-jitterizzazione. ⇒ Sarebbero **250 ms
pagati due volte**.

#### ⚠ La domanda onesta: morde davvero, o solo sotto `netem`?

⭐ `[M]` **Su WiFi vero i «vecchi» sono zero.** ⇒ **Sul percorso di oggi dell'utente questo difetto
NON morde, e chi presentasse questa cura come un miglioramento di quel che lui sente adesso
mentirebbe.** E la ragione è meccanica, non fortuna: **802.11 riordina già lui** (un flusso QUIC sta
in un solo TID, il ricevitore tiene una finestra di block-ack con riordino) ⇒ il WiFi **perde** e
**ritarda**, ma **non sorpassa**. Lo stesso per un cavo e per il loopback.

⚠ E `netem` sorpassa tanto per una ragione che va scritta o il banco sembra più severo della realtà:
`delay X Y` dà a **ogni pacchetto** un'ora di consegna indipendente, e il figlio spedisce i datagram
**a raffiche**, a microsecondi l'uno dall'altro ⇒ **dentro una raffica, qualunque jitter riordina.**

**Allora perché curarlo lo stesso**, in tre argomenti e non un'opinione:

1. ⛔ **il percorso dichiarato del progetto non è il WiFi**: la **migrazione QUIC** è, per
   costruzione, pacchetti in volo su **due percorsi contemporaneamente** che arrivano intrecciati —
   è `netem` fatto dal protocollo stesso. E il datagram audio su rete non locale non è mai stato
   misurato;
2. ⛔ **il modo di fallire è sproporzionato**: 20 % di scarto ⇒ purezza **0,175**, cioè audio
   distrutto. Un difetto che sta a zero finché il percorso è pulito e poi **toglie il suono di
   colpo** alla prima rete che sorpassa arriva senza preavviso, e arriva sul telefono dell'utente,
   **cioè dove non c'è il banco**;
3. ⭐ **il prezzo è zero**. Un'assicurazione gratis contro un modo di fallire **totale** si compra.

⇒ ⛔ **Si dichiara per quel che è: una conformità a §6.3 e un'assicurazione sui percorsi non ancora
misurati, NON un miglioramento di quel che l'utente sente oggi.** La misura di controllo su WiFi
vero deve dare **identica a prima**, e se desse diverso sarebbe la cura ad avere un difetto.

⚠ **E l'avvertenza già pagata resta**: la misura è in **PCM da 5 ms**. Con Opus (20 ms) la soglia di
sorpasso è **quattro volte più alta** e il difetto morde quattro volte meno ⇒ il percorso vero è
Opus, e su Opus il numero `[M]` **non c'è**.

⛔ **Che cosa È verificato di questa cura, e che cosa no**: §3.16.

#### ⛔ Le quattro cure d'audio **scartate**, e perché — *scritte perché nessuno le ripeschi*

| cura scartata | perché |
|---|---|
| **abbassare `AUDIO_CUSCINO_MS`** | il codice lo vieta espressamente **qui e ora**: prima si misura **il jitter d'arrivo**, che nessuno ha misurato. ⭐ E questa cura **produce quella misura** (`fuori_ordine` + gli scarti) ⇒ è il passo che va **prima**, non al posto |
| **una coda di riordino con ritardo fisso** | 250 ms pagati due volte, e vende risposta |
| **togliere del tutto lo scarto** | §6.3 lo impone, e senza confine un blocco davvero vecchio **si sovrapporrebbe a quel che sta suonando** — il rilievo 3 del 17 agosto rifatto |
| **l'`AudioWorklet`** | è un'altra cosa, ed è già dichiarata: i numeri del 21 agosto dicono che non è **questo** il problema |

⚠ **E una falsificazione che vale per il banco intero**: se dopo la cura la purezza sale ma
`usciti` **non** sale con lei, ⛔ **il suono non c'è** — ed è già successo in questo file: una
sessione **muta con tutti i contatori verdi**.

### 5.5 Cura 5 — il tetto di banda · `codificatore.c:200-340`, `:1786-1800`

**La misura che la obbliga**: §3.8 — con **QP 26 fisso e nessun tetto**, un contenuto duro a schermo
intero chiede **58,668 Mbit/s = il 293 % del pavimento**, e nessuno gli dice di no.

⭐⭐ **E il modo si è scelto con i byte, non con una preferenza** — misurato sul portatile il 23
agosto pomeriggio, il dettaglio in `codificatore.c:200-260`:

| modo | esito |
|---|---|
| ⛔ **VBR** | **fuori**, e la prova non è un ragionamento: con e senza `qp=26` escono **gli stessi identici byte** (8 350 170 e 514 142, due volte su due) ⇒ **sotto VBR il `qp` è ignorato**, e tutta la scala della degradazione **più la risalita scritta stamattina** diventerebbero **no-op silenziosi** |
| ⛔ **CBR** | **smascherato sul ferro nostro**: a scena ferma spende **15,98 Mbit/s contro 0,193** del CQP — **83 volte** per niente (R31 di v1 diceva 42× a 1440p: **qui è peggio**) |
| ⛔ **ICQ / AVBR** | fuori: mai misurati, mai visti in v1, e `AVBR` converge *«in N frames»* — un modo che si assesta su una finestra sbaglia **proprio nell'istante in cui la scena cambia** |
| ⭐ **QVBR** — **scelto** | la scala **REGGE**: `[M]` scena ferma QP 26 → **0,218** · QP 35 → **0,125** · QP 44 → **0,076** Mbit/s. ⚠ E a scena **dura** la scala non morde più (11,14 · 11,31 · 11,19): **quando il tetto è in presa la qualità la decide il tetto, non il QP** — va detto, o un banco che cercasse lì l'effetto del QP non lo troverebbe e concluderebbe male |

⛔ **I tre numeri si derivano dal pavimento, nessuno è scritto a mano**: `rc_max_rate` = **80 %** del
pavimento (16 Mbit/s ⇒ 16 + i **2,426** `[M]` misurati di audio/input/QUIC = **il 92 %** del
pavimento: il margine ha un numero sotto invece di essere prudenza) · `bit_rate` = **75 % del filo**,
⛔ **mai uguale al filo, è R31 alla lettera** · `rc_buffer_size` = filo × **40 ms**.

⛔⛔ **E quella terza riga è quella che v1 sbagliò senza che nessuno se ne accorgesse**:
`fondamenta/remotix-c/src/codificatore.c:256` metteva `rc_buffer_size = bit_rate / 2`, che **non è «metà»:
è mezzo SECONDO** — un VBV si misura in bit, e `bit_rate/2` bit a `bit_rate` bit/s fanno **500 ms**,
cioè **dieci volte** il tetto di 50 ms che `CODER.md` §1-bis dà a **tutto** il pezzo nostro.
⭐ Qui sono **40**, cioè il *traguardo* e non il *tetto*: si sbaglia nel verso scomodo. ⚠ E il
numero non è dedotto, è **stampato da ffmpeg**: `[M]` *«RC target: 75 % of 16000000 bps over 40 ms»*.

⭐ **E un rosso previsto dallo studio è già CADUTO**: dichiarando 16 Mbit/s ffmpeg stampa
`Using level 5`, cioè **5.0** ⇒ **la banda non fa salire `level_idc`** e `avc1.640033` regge.

#### ⛔⛔ E i TRE testimoni, perché uno solo non basta — *R31 non dice «scrivi una riga di registro»*

R31 dice ***«si chiede per nome e si verifica che abbia obbedito»***, e verificare vuol dire **tre
testimoni indipendenti**:

| # | testimone | che cosa prova | ⛔ che cosa **NON** prova |
|---|---|---|---|
| **1** | **il driver, prima di aprire** — `VAConfigAttribRateControl` sulla coppia (profilo, entrypoint) | che il modo **esiste** su quella coppia | non che verrà usato |
| **2** | **il contesto, dopo `avcodec_open2`** — `rc_mode`, `bit_rate`, `rc_max_rate`, `rc_buffer_size` **riletti** | che **libavcodec** ha tenuto quel che gli si è chiesto | ⛔ **non che il driver l'abbia applicato** |
| **3** ⭐⭐ | **I BYTE** — byte/s a scena ferma contro byte/s a scena mossa | **quale modo è in vigore davvero** | — |

⛔⛔ **Il terzo è l'unico che avrebbe preso R31.** In v1 i testimoni 1 e 2 sarebbero stati **tutti
verdi**: `bit_rate` e `rc_max_rate` erano esattamente i numeri chiesti, e **nessuno aveva chiesto
CBR** — il CBR era **il nome che il driver dava a quella coppia di numeri**. ⇒ **Solo la bolletta lo
diceva.**

⛔ **E la domanda al driver ha TRE esiti, non due**: *«non ho potuto guardare»* ≠ *«il driver non lo
dichiara»* ≠ *«ecco la maschera»* — ⛔⛔ e il secondo **non vuol dire «c'è solo il CQP»**. `[M]` La
trappola è **già armata dentro ffmpeg**, ed è una stringa nel binario: *«Driver does not report any
supported rate control modes: **assuming CQP only**»*. ⇒ Se il driver tace, **libavcodec decide da
sé** e va avanti: è R31 in una forma nuova — non *«il driver deduce»*, ma *«ffmpeg deduce per conto
del driver»*, **con lo stesso silenzio**.

⭐ **E chiedere per nome non è prudenza: è l'unico modo di ottenere un rosso invece di una
bolletta.** Con `rc_mode = auto` si sceglie qualcos'altro **in silenzio**; col nome `avcodec_open2`
**fallisce**, e la parentesi dell'errore *«(supported modes: …)»* **elenca quel che c'è**.

⚠ **E la regola del banco che ne esce, in una riga**: ⛔ **il controllo del modo si fa a schermo
FERMO** — `[M]` a scena ferma i modi differiscono di **83×** (CQP 0,193 contro CBR 15,98 Mbit/s), a
scena dura stanno tutti dentro l'1 % l'uno dall'altro ⇒ **un banco che misurasse solo la scena dura
non misurerebbe niente**. ⛔ **Ma sul prodotto «fermo» vuol dire ZERO fotogrammi** (§3.8: 0,00
fot/s), quindi la scena che fa da controllo è **la seconda: il desktop vero**, che si muove e costa
l'1 %.

⚠ **Quel che NON si tocca, e va detto**: `max_frame_size`. `[M]` ffmpeg lo rifiuta sotto CQP e lo
accetta sotto QVBR — darebbe **in un passaggio** quel che oggi costa fino a 3 riaperture da
91-108 ms. ⛔ Non si accende oggi: è una **seconda leva sulla stessa grandezza**, e due leve accese
insieme al primo giro darebbero **due misure sotto la stessa etichetta**.

#### ⛔ E il difetto trovato strada facendo, che non era il bersaglio dello studio

`[R]` **Il server non legge mai `video.livello`.** `rcp.c:1823` lo elenca fra i nomi noti, e il ciclo
cattura `c_codec`, `c_prof`, `c_audio`, `c_misura` — **non il livello**. `RCP.md:701` dice che il
server **DEVE** emettere un flusso di livello non superiore: **quel DEVE non era implementato**. Il
resto della catena c'era già (il livello **vero** letto dai byte a `codificatore.c:384`, stampato al
primo fotogramma) ⇒ ⭐ **mancava UN confronto fra due numeri che il prodotto ha già in mano.**
Dal 23 agosto **le due righe si scrivono** (§3.12) — ⛔ ma **il confronto lo fa ancora chi legge, non
il programma**.

⚠ **E il sintomo, se mordesse, è quello che `RCP.md` scrive**: un livello dichiarato troppo basso
**non dà un errore di rete, fa rifiutare la configurazione dal decodificatore** — cioè **schermo che
non parte, senza un rosso da nessuna parte**. Stessa famiglia di R31.

#### ⭐ E il livello morde davvero, ma **sui pixel e sui fotogrammi**, non sulla banda

`[R]` Due correzioni che valgono oltre la fase:

- ⛔ **`SPECIFICHE.md:1087` parla di un altro codec**: *«tier High»* e *«40 Mbit/s»* sono **HEVC**
  (Tabella A.9, livello 5.1 Main tier = 40 000 kbit/s). **H.264 non ha tier affatto.** La riga era
  corretta **per il codec che il prodotto aveva quando fu scritta**, e non ha seguito il cambio del
  17 agosto (*«AV1 esce, entra H.264»*);
- ⛔ **sul bitrate la riga non morde a nessun valore che questo prodotto possa produrre**: per
  `avc1.6400xx` (High) il tetto è **168,75 Mbit/s a 5.0** e **300 a 5.1** — 8,4 volte il pavimento;
- ⭐⭐ **ma `MaxFS` e `MaxMBPS` mordono**: 2560×1080 (la tela dell'utente) richiede il **5.0** come
  minimo — è la ragione, mai scritta, per cui il banco `07-b48` verificò proprio `avc1.640032`.
  ⛔ E **a 3840×2160 il 5.0 non ci sta affatto**: serve il 5.1, che concede `[?]` **30,3 fot/s**
  ⇒ **il «60 fps» del desiderato non è raggiungibile a 4K nemmeno con banda infinita**;
- ⚠ `[R]` **il prodotto dichiara 5.1, non 5.0** (`pagina.html:829`) ⇒ `avc1.640033`. Il 5.0 vive in
  **due commenti**, e uno dei due (`codificatore.c:1559-1560`) è **stantìo**.

---

## §6 · ⏳ IL REGOLATORE DEL RITMO — **disegnato, NON scritto**

> ⛔ **È il lavoro che resta**, ed è il pezzo per cui la fase esiste. Nessuna riga è stata applicata.

### 6.1 Il disegno in una pagina

| | |
|---|---|
| **la grandezza** | ⭐ **`arretrato`** — quanti fotogrammi **delta** in volo hanno ancora byte **nella nostra coda d'uscita**, letto all'arrivo di un fotogramma nuovo, **prima** di `video_sgombra()` |
| **la regola** | `arretrato == 0` ⇒ si spedisce · `arretrato >= POSTI` ⇒ **questo fotogramma non parte**. Nessun'altra leva |
| **la discesa** | non è un numero che si abbassa: è **un fotogramma che non parte**. Il ritmo cala da sé, tanto quanto la coda non si svuota |
| ⭐ **la risalita** | **non esiste, e questo è il pregio**: `arretrato` si rilegge a ogni fotogramma, non si ricorda. ⛔ Niente cricchetto — cioè niente `qualita_corrente`, che è il difetto misurato di §5.3 |
| **il fondo** | 480p·25 **non è un freno, è un verdetto**: se il ritmo consegnato scende sotto 25/s su 20 Mbit/s, il registro lo dichiara **difetto**. Forzare un fotogramma dentro una coda che non si svuota peggiora la coda |
| **il registro** | una riga all'**inizio** e una alla **fine** di ogni episodio, mai una per fotogramma; più un contatore suo, `video_ritmo_scesi` |
| **l'interruttore** | `--ritmo-adattivo`, **spento di suo** (I6), e il valore in vigore **scritto all'avvio in tutt'e due i casi** |
| **dove** | `webtransport.c`, dentro `video_a_una()`, tre righe sopra `video_sgombra()` |
| ⛔ **l'ordine obbligato** | **prima la cura di `video_sgombra()`, poi il regolatore** — §6.5 |

`POSTI = 2`, e ⛔ **non è un orologio travestito**: è la profondità del tubo. Con `POSTI = 1` si
salterebbe ogni volta che il fotogramma di prima non è uscito **interamente** entro l'arrivo del
successivo — a 60/s sono 16 ms, e un delta da 10 KB su una linea sana ne impiega di più: sarebbe
**euristica prudente**, cioè **I1 rotta**. ⚠ `[?]` Il valore si tara sul banco.

### 6.2 ⛔ Perché `arretrato` non ricade in P13 e in P20

- **P13**: la tolleranza diceva *«per un secondo»*, e fu corretta due ore dopo — *«il secondo era la
  grandezza sbagliata: quel che deve svuotarsi è una **coda**, e quanto ci mette un fotogramma già
  in volo dipende dalla **banda**, non dall'orologio»*. ⇒ `arretrato` **è la coda**, contata in
  fotogrammi: non si chiede *«è passato troppo tempo?»*, si chiede *«i byte di prima sono ancora
  qui?»*;
- **P20**: la cura fu **quel che il client ha spedito lui — locale, monotono, indipendente dalla
  consegna**. ⇒ `arretrato` ha esattamente quella forma dal **nostro** lato: byte prodotti da noi e
  ancora in casa nostra. **Nessun pacchetto perso, nessun riordino e nessun silenzio del client può
  falsarlo**, perché non si guarda niente che venga da fuori.

⭐ E la frase è **già nel codice**, scritta per la stessa ragione: *«una stima può sbagliare, un byte
in coda no»*.

⚠ **E le tre cose che `arretrato` NON è**: non è un **ritmo target** (se esistesse dovrebbe
risalire, e qualcuno un giorno dimenticherebbe di farlo risalire — **è già successo**, §5.3); non è
la **banda** (`cwnd/rtt` è una stima, e come ingresso di un anello che decide se un fotogramma parte
sarebbe un numero calcolato al posto di un fatto); ⛔ **non è un ack del client** — §6.6.

### 6.3 ⭐ Che cosa ngtcp2 ci dà già misurato e che oggi non guardiamo

`ngtcp2_conn_get_conn_info()` riempie **sette** campi. Oggi la si chiama in **un solo punto** e se
ne leggono **due**.

| campo | oggi | che cosa direbbe |
|---|---|---|
| `smoothed_rtt` · `cwnd` | ✅ | il giro di rete e la finestra concessa |
| `bytes_in_flight` | ⛔ **mai letto** | ⭐ è **il pezzo di arretrato che la nostra coda non vede più** — il codice lo dichiara già come buco |
| `min_rtt` | ⛔ mai letto | ⭐ `smoothed_rtt − min_rtt` **è la coda dentro la rete, in millisecondi**: è il numero con cui si **onora** `SPECIFICHE.md:128` invece di citarlo |
| `ssthresh` | ⛔ mai letto | distingue *«la linea sta salendo»* da *«la linea ha ceduto»* |
| `latest_rtt` · `rttvar` | ⛔ mai letti | il tremolio, per l'audio |

⛔ **E l'algoritmo di congestione non è mai stato scelto**: si prende il predefinito di ngtcp2
(CUBIC). ⚠ **Non si cambia dentro questo disegno** — sarebbe una seconda variabile nello stesso
banco — **ma la voce va aperta**: su WiFi, CUBIC legge **una perdita da radio** come una congestione
e dimezza la finestra; BBR, che ngtcp2 offre, lavora su banda di collo di bottiglia e `min_rtt`, cioè
su due numeri che questo disegno vuole comunque leggere. `[?]` **da misurare come esperimento
separato, dietro il suo interruttore.**

⚠ E un limite che non è nostro: quanto possiamo spedire su uno stream lo decide il **client** con
`initial_max_stream_data_uni` / `initial_max_data`. ⇒ **Una coda che cresce con `cwnd_left` ALTO non
è la linea: è la finestra del browser**, e la cura è un'altra.

### 6.4 ⚠ Il prezzo dichiarato: si taglia **a valle** del codificatore

Il fotogramma saltato **è già costato la GPU del figlio**. La leva vera — non catturarlo affatto —
sta nel figlio, e il tubo per arrivarci **esiste già** (`figli_video()` porta già codec, profondità e
chiave attraverso il confine di processo).

⛔ **Ma non si fa in fase 9, e la ragione è d'architettura**: il palco è **uno per utente**, le
sessioni sono **N**. Un ritmo imposto al palco lo imporrebbe a tutte, **e la sessione sulla linea
buona pagherebbe per quella sulla linea cattiva.** ⇒ `[?]` aperta, e vale la pena riaprirla solo con
la misura di quanto costa davvero un fotogramma sprecato — che con la copia zero potrebbe essere
poco. ⚠ E una differenza a nostro svantaggio, dichiarata: **GNOME regola prima di codificare, noi
dopo.** Sul consumo di GPU il loro è migliore.

### 6.5 ⛔⛔ IL CONTROLLO CHE INVALIDA TUTTO IL BANCO, e viene prima degli altri

**`video_sgombra()` svuota la coda dei delta a OGNI fotogramma.** Finché è così, `arretrato` **è zero
per costruzione**: quando il fotogramma N+1 arriva, i byte di N sono già stati buttati dal giro
precedente.

⇒ ⛔ **Un regolatore installato oggi non scatterebbe mai, e il banco lo leggerebbe come «la linea
porta».** Sono due fatti con la stessa faccia.

⭐ E le due modifiche sono **una modifica sola guardata da due lati**: `video_sgombra()` smette di
buttare il delta precedente solo perché ne è arrivato uno più recente (cura 2, §5.2), e il regolatore
smette di produrne di nuovi nello stesso istante. ⛔ **Ordine obbligato: prima la cura, poi il
regolatore.**

### 6.6 ⛔ Che cosa del regolatore di GNOME si rifiuta — e che cosa si copia

⭐ **La forma si copia**: posti fotogramma, nessun controllo di bitrate, nessuna risoluzione
adattiva, l'anello che si auto-cadenza invece di inseguire un target. ⛔ **La grandezza no**, per tre
ragioni indipendenti:

1. **`ack_rate` da noi non esiste.** La tabella dei messaggi di `RCP.md` non contiene nessun
   riscontro di fotogramma. Copiarlo vorrebbe dire un tipo nuovo, un obbligo nuovo per il client, e
   **un giro di rete dentro l'anello di controllo** — cioè comprare la reazione con il ritardo.
   `arretrato` costa **zero ms**: è già in memoria nostra;
2. ⛔ **`ack_rate` dipende dalla consegna e dalla cooperazione del pari**, cioè è *precisamente* la
   famiglia P8→P20. Il client può sospendere i riscontri con `queueDepth == 0xFFFFFFFF` e **un
   regolatore che non lo gestisce si ferma per sempre**. ⚠ E la trappola **non si disinnesca con un
   `if`**: un anello che il pari **può** congelare non diventa sicuro perché si aggiunge un caso
   speciale. Non chiedendo niente al pari, la trappola **non esiste**.
   ⇒ ⭐ Conseguenza da scrivere perché nessuno la cerchi: il controllo **M1** di `STUDI.md:1173`
   (*«il nostro regolatore regge `queueDepth == 0xFFFFFFFF`»*) diventa **vacuo** — va marcato **non
   applicabile**, non lasciato aperto;
3. ⛔ **La soglia di GNOME è un orologio travestito**: `delayed_frames = rtt_us × refresh_rate / 1e6`
   converte un RTT in un numero di fotogrammi. È **P13 in un altro vestito**, e si rompe nello stesso
   punto: una chiave da 60 KB non impiega un RTT, impiega `byte × rtt / cwnd`.

### 6.7 ⚠ La domanda onesta: a 20 Mbit/s serve davvero?

**In regime, no**, ed è la previsione di §7.4. ⇒ ⭐ **Va giudicato per quel che è: un parapetto.** Il
suo comportamento corretto è **non fare niente**, e un banco che dimostrasse solo che non scatta
avrebbe dimostrato **metà** del lavoro.

**Dove morde davvero**, in ordine di probabilità:

| | perché |
|---|---|
| ⭐⭐ **la migrazione WiFi → rete mobile** | il percorso cambia, ngtcp2 **riazzera il controllo di congestione**: `cwnd` torna alla finestra iniziale, ~10 pacchetti ≈ 14 KB. ⛔ **Una chiave da 60 KB non ci sta**, e la coda si forma con certezza. È *«la ragione migliore per cui QUIC è stato scelto»*, e oggi non c'è niente che lo governi |
| ⭐ **il calo temporaneo del WiFi** | un fallback di modulazione porta 200 Mbit/s a 15 per uno o due secondi — ⭐ **ed è esattamente il gradino misurato in §3.10** |
| **il traffico altrui sulla stessa linea** | la finestra si stringe senza che la linea cambi |
| ⚠ **più sessioni dello stesso utente** | il palco è uno, le sessioni N; e a valle c'è il budget di rete (dieci × 20 = **200 Mbit/s**) |
| ⛔ **NON in regime su una linea sana da 20 Mbit/s** | ed è la previsione che questa fase deve confermare per prima |

⇒ ⭐ **Conseguenza sul banco, e non è un dettaglio**: **strozzare a 20 Mbit/s costante non prova
questo disegno.** Serve un **gradino** — ed è la ragione per cui §3.10 è stato misurato così. ⭐ E il
controllo di §3.10 (`pieno`, che chiede meno del buco: **niente si muove**) dimostra che il banco non
spara a vuoto.

### 6.8 Che cosa il disegno **non** tocca, dichiarato

il **QP** (resta 26 fisso: farlo qui vorrebbe dire due variabili nello stesso banco) · l'**algoritmo
di congestione** (§6.3 apre la voce e non la chiude) · la **risoluzione** (fuori per decisione) · il
**cuscino audio** (non c'entra con la banda) · ⚠ e **nessuna memoria intermedia nuova**: è l'unico
modo in cui `SPECIFICHE.md:128-131` si onora senza doverlo giustificare in millisecondi.

---

## §7 · ⛔ IL REGISTRO DELLE DISCESE — e le previsioni in attesa di misura

> ⛔ **Perché il registro è di questa fase e non un accessorio.** I1 non dice solo *quando* si può
> calare: dice che **«ogni discesa è dichiarata nel registro»**. ⇒ ⭐ **Un regolatore che scende
> senza dirlo è indistinguibile da un difetto.**

### 7.1 ⏳ La forma della riga — ⛔ progettata, **non applicata**

`[R]` Non esiste nessun regolatore del ritmo, quindi la riga va **progettata prima**, o nascerà come
prosa. ⛔ **Non prosa**: una riga sola, campi in ordine fisso, `chiave=valore`, così che un banco la
legga con `split()` e non con una regex sulla prosa italiana.

```
🔻 RITMO  chi=nic/198.51.100.7  da=60  a=40  unita=fps
          causa=coda_video  misura=1843210  soglia=1500000  unita_misura=byte
          per=I1/§8.2  attivo_da_ms=0
```

| campo | perché non si può togliere |
|---|---|
| `🔻`/`🔺` | ⭐ la **risalita** è metà dell'invariante: un regolatore che scende e non risale **ha calato per prudenza col ritardo di un'ora**. Il cricchetto di §5.3 era già questo difetto, misurato |
| `da=` / `a=` | senza il **prima**, «40 fps» non è una discesa: è un numero |
| ⛔ `misura=` **e** `soglia=` | **è il campo che rende I1 verificabile senza fidarsi del codice**: se `misura < soglia`, quella discesa è **per prudenza**, e la riga stessa lo dimostra |
| `causa=` **etichetta chiusa**, non frase | un banco conta le discese per causa; una frase italiana non si conta |
| `unita_misura=` | *«il numero giusto e la parola sbagliata accanto»*: byte e kbit/s convivono già in questo file |
| `attivo_da_ms=` | ⭐ senza, una discesa e risalita che si alternano 20 volte al secondo (**pendolamento**) hanno lo stesso registro di una discesa stabile |
| `chi=` | quattro sessioni sullo stesso file di registro |

⭐ **La stessa forma vale per la qualità** — `🔻 QUALITA modo=QP da=26 a=35 causa=tetto_16MiB …` — ed
è la riga che `abbassa_qualita()` **non scrive**: scrive solo i due *fallimenti*. ⇒ Per un **delta**
la scala scende **26 → 35 → 44 in silenzio**.

⛔ **E la riga si scrive solo quando il valore CAMBIA**, non a ogni fotogramma: così il registro *è*
la curva del ritmo, e il costo è il numero di discese, non il numero di fotogrammi. ⚠ Con un **fondo
di pendolamento**: se cambia più di *N* volte al secondo, la riga diventa *«🔻🔺 RITMO PENDOLA»*, che
è **un difetto del regolatore** e va detto come tale.

### 7.2 ⛔ I buchi che l'inventario ha trovato — e uno era già chiuso

`[M]` **Quanto costa una riga**, misurato il 23 agosto su Intel N100 (il ferro **più lento** dei due,
quindi è un tetto): **0,63 µs** e **98 byte**.

| | |
|---|---|
| ⭐⭐ **una parte del mandato è RIFIUTATA**: la **terza forma** dell'abbandono (il credito mancato, difetto B-18) **è scritta nel registro**, sempre accesa, con la cura del debito accanto | ⇒ Il buco non c'è. Restano **due riserve di forma**: la riga **non ha fondo** (sotto carestia scrive 60 righe/s per sessione, ⚠ ed è la forma dei **30,8 GB**), e il conto esce **solo a fine sessione** |
| ⛔ **il debito della chiave: sette ragioni in nove punti, non cinque.** Il commento dichiara *«CINQUE punti»* e porta già la cicatrice della volta precedente (*«diceva tre e i punti erano quattro»*) | ⭐ La cosa notevole non è il numero: è che `serve_chiave_perche` **esiste e porta la ragione fino alla riga** ⇒ **la grandezza che serve al banco è già lì, e ha già la forma giusta** |
| ⛔ **quattro discese esistono GIÀ nel prodotto, e tre sono silenziose** | `abbassa_qualita()` su un delta (26→35→44, **senza il numero**) · il **cricchetto** (nessun accessore per leggerlo da fuori) · il blocco d'audio più vecchio buttato perché la coda è piena (⚠ **il gemello tre righe sopra la riga ce l'ha**, e il commento dice perché) · ⭐ il **ritmo a zero** quando il codificatore non apre, che **sì**, è dichiarata col numero |
| ⛔ **`*come` di `chiave_intervallo_ms()` finisce in parlantina** | Il commento sopra la funzione dichiara che *«è l'unica cosa che distingue "la cura sta lavorando" da "la cura non è ancora accesa"»* — **e poi la scrive in parlantina** ⇒ in ogni installazione normale le due hanno esattamente la stessa faccia. **È il principio 2 violato dentro la funzione che lo cita** |
| ✅ **i valori in vigore all'avvio** | ⭐ **applicato il 23 agosto**: §3.12. ⛔ Ma il **pavimento** (480p·25 e 20 Mbit/s) **non esiste ancora nel codice**, e va scritto **anche se il regolatore non c'è**: è il numero sotto cui la fase non ha il permesso di scendere |

### 7.2-bis ⚠ IL PREZZO — e ⛔ **non serve un livello intermedio: serve un FONDO**

`[M]` 0,63 µs e 98 byte per riga. `[R]` A regime, **una** sessione a 60 fps, le righe **per
fotogramma** sono due (`stream uni aperto` e `codec N: … byte`):

| | righe/s | byte/s | in un'ora | CPU |
|---|---|---|---|---|
| **una sessione, con `--parlantina`** | **120** | **11,8 kB/s** | **42 MB** | **0,0076 % di un nucleo** |
| quattro sessioni | 480 | 47 kB/s | 170 MB | 0,03 % |

⇒ ⭐ **La CPU non è il prezzo: è tre centesimi di millesimo di nucleo.** Il prezzo è il **disco** e
la **leggibilità** — un registro in cui le due righe per fotogramma seppelliscono tutto il resto in
rapporto **120 : 1**.

⛔⛔ **E sotto congestione il prezzo lo paga anche il registro SPENTO.** `[M]` 21 agosto: a 3 Mbit/s
la riga *«FOTOGRAMMA NON SPEDITO»* esce **28 volte al secondo**, e ogni abbandono ne genera un'altra
⇒ ~**60 righe/s = 21 MB/ora senza `--parlantina`**, e **nessuna delle due ha un fondo**.
⇒ ⛔ **Il registro è più rumoroso quando la linea è peggiore, cioè quando serve leggerlo.**

⛔ **Un terzo livello (`--parlantina-ritmo`) è la strada sbagliata**: metterebbe le righe di I1
dietro un interruttore spento di serie, e ⛔ **una discesa dichiarata solo quando qualcuno ha acceso
un interruttore NON è dichiarata**. ⇒ Il principio 2 e I1 impongono `registro_dice()` per ogni riga
`🔻`/`🔺`. ⭐ **Quel che serve è il fondo**, e il prodotto ne ha già **quattro forme funzionanti**,
tutte con la motivazione scritta accanto: *una volta sola* (`bool detto`) · *ogni N*
(`== 1 || % 100 == 0`) · ⭐ *quando cambia di ≥ soglia* (**la forma delle righe `🔻`/`🔺`**) ·
⭐ *una volta al secondo, con dentro gli ZERO* (**la forma della riga periodica del ritmo**).

⇒ **La proposta, in quattro punti e senza un livello nuovo:**

1. le righe `🔻`/`🔺` a `registro_dice()`, **solo quando il valore cambia** ⇒ su una sessione sana:
   **zero righe**;
2. una riga `ritmo:` **una volta al secondo, sempre, con dentro gli zero** — fotogrammi consegnati ·
   saltati per credito · abbandonati · byte in coda · valore in vigore. **98 byte/s per sessione =
   0,35 MB/ora**: **120 volte meno** della parlantina;
3. ⛔ **un fondo sulle tre righe che sotto congestione escono a 28-60/s.** ⚠ E non si può mettere
   **prima** della riga periodica del punto 2, perché oggi il conto esce solo a fine sessione: sono
   **una cura sola in due pezzi**;
4. ⚠ e, **fuori dal mandato di questa fase**, il **filtro per area** (`--parlantina wt,rcp`): oggi
   la parlantina è un interruttore unico su **undici** aree, e chi indaga il ritmo si porta dietro
   gli appunti, la tastiera e il cursore.

### 7.3 ⛔ I controlli che decidono — *quale guasto fa cadere ciascuna cosa*

⭐ *«Un controllo deve leggere una cosa che si può **SBAGLIARE**, non una che si può mediare.»*

| la cosa | il guasto che la fa cadere |
|---|---|
| `🔻 RITMO` esiste | ⛔ **il ritmo cala a scena ferma**: **una sola** riga `🔻` in 60 s di scena ferma ⇒ rosso |
| `🔺 RITMO` esiste | ⛔ **il cricchetto**: strozza 10 s, togli la strozzatura, aspetta 10 s — nessun `🔺` ⇒ rosso. ⚠ **Oggi la qualità fallirebbe questo banco** *(finché `--qualita-risale` è spenta)* |
| `misura=` / `soglia=` | ⛔ `misura < soglia` in una qualsiasi riga `🔻` ⇒ **rosso, e non serve altro** |
| `attivo_da_ms=` | ⛔ **il pendolamento**: > 4 cambi/s ⇒ rosso |
| riga d'avvio coi valori | ⛔ **forma E1**: avvia con `--qp 40`, leggi la riga — se dice 26, l'interruttore non arriva al codificatore |
| **la risalita** (cura 3) | ⛔⛔ **lo SBATTIMENTO**: grana `alls=60` a 7680×4320 per 60 s continui — più di **3 riaperture al minuto** dopo il primo minuto ⇒ rosso. ⭐ **È il controllo che decide**: se l'attesa che raddoppia non lo spegne, i tre numeri sono sbagliati. ⚠ E il caso a cui credere è **I1 appaiato**: i fotogrammi/s **con** la cura più bassi di quelli **senza** ⇒ rosso |
| il **pavimento** della risalita | ⛔ 10 000 fotogrammi vuoti: se la qualità scende **sotto** `richiesta.qualita` anche di uno scalino ⇒ rosso |
| il **senza-perdita** | ⛔ si rientra in LOSSLESS ⇒ rosso: sarebbe il cambio di grandezza a metà sessione |
| ⛔ la **memoria** | 10 000 discese e risalite di fila: `valgrind` trova una superficie della GPU non restituita ⇒ è il difetto *«che si vede solo dopo mezz'ora»* |

### ⛔ E una riga che si RIFIUTA, per la stessa regola

*«banda stimata = N kbit/s»*, scritta una volta al secondo. **Non c'è nessun guasto che la fa
cadere**: `cwnd/rtt` è una grandezza **mediata**, plausibile in ogni condizione, e un banco che la
legge non può dire se sia giusta. ⇒ ⭐ **Non va scritta.** Quel che va scritto è il **byte in coda**
— che si può sbagliare — e la banda solo **dentro** una riga `🔻`, come *prova della soglia*.

### 7.4 ⛔⛔ LE PREVISIONI FALSIFICABILI IN ATTESA — **il patto della fase**

> ⚠ **Si conservano tutte.** Dicono che cosa ci aspettiamo e che cosa ci smentirebbe, e servono al
> giorno in cui si misura. ⭐ Dove la previsione sta anche nel codice, il codice è la sede: qui c'è
> la riga sola, con il `file:riga` accanto.

| # | la previsione | ⛔ che cosa la smentirebbe | dove per esteso |
|---|---|---|---|
| **P1** | ⛔ **il crollo si riproduce** con `MALLOC_MMAP_THRESHOLD_=32768` + client congelato: `SEGV`, `error 4`, sempre in `__memmove_avx_unaligned_erms` | **se non muore, la diagnosi di §4 è sbagliata** | §4.5 |
| **P2** | **la soglia sulla coda è INERTE a 20 Mbit/s**: `abbandonati per soglia` = 0, ritardo dell'anello = 55,20 ms | ⛔ **molti abbandoni al secondo con l'interruttore spento a 20 Mbit/s** ⇒ il difetto morde **sopra** il pavimento, la cura non è una robustezza, e **cambia la priorità della fase** — §10.2 | `webtransport.c:2738-2790` |
| **P3** | **sul gradino** (3 s a 10 Mbit/s, `barra`): fot/s nei secondi 8-10 da 13-14 a **≥ 25**, chiavi/s da 6-7 a **≤ 2**, abbandoni/s **≤ 2**, secondi 7 e 12 **identici** | ⛔ **4 rossi**: (1) chiavi ferme mentre gli abbandoni scendono ⇒ il debito lo accende **un'altra** delle sette cause, quasi certamente il **credito mancato** (forma C, invisibile al ricevente); (2) i fot/s non salgono ⇒ soglia troppo alta, si scende a 50; (3) ⭐ **l'anello supera 55 + soglia** ⇒ la stima **sottostima**, ed è il rosso più importante perché sarebbe **un numero che sembra misurato**; (4) il ritorno smette di essere sotto il secondo ⇒ la cura paga il transitorio col ritorno, e va **spenta** invece che tarata | `webtransport.c:2738-2790` |
| **P4** | **il tetto di banda**: `ferma` 0 · **desktop vero 0,20-0,45** · tinta piatta 1,1-1,6 · retinato **11-16** · grana **11-16**, e **MAI sopra 16** | ⛔ **2 cambiano la conclusione**: (1) ⭐⭐ **il desktop vero costa MENO di 0,204** ⇒ il tetto **risparmia dove non deve**, è v1 che si ripete, **e questa cura si butta** (la previsione è *«non scende»*, ed è secca: `[M]` sul portatile QVBR spende il **13 % in più** del CQP a scena ferma); (2) ⭐⭐ **il retinato resta sopra 20** ⇒ il driver **non ha obbedito**, R31 vale **anche contro la richiesta esplicita**, e lo coglie **solo il terzo testimone, i byte** | `codificatore.c:252-300` |
| **P5** | **la risalita della qualità**: dopo una raffica granulosa e 600 fotogrammi fermi, la confessione torna **esattamente** a 26 (o 20) e c'è la riga `RISALITA` | ⛔ **lo sbattimento**: > 3 riaperture/minuto sulla scena al **94,9 %** del tetto ⇒ i tre numeri sono sbagliati; e ⛔ **i fot/s con la cura più bassi di quelli senza** (appaiato, stessa scena) ⇒ il prezzo lo paga I1 | §7.3 · `codificatore.c:100-145` |
| **P6** | **il riordino dell'audio**, sui profili `netem`: ±2 ms **0,175 → ≥ 0,95** · ±5 ms ≥ 0,95 · ±10 ms ≥ 0,90; `vecchi` da **1 004 a ~0**, e `fuori` deve **prendersi quel numero** ⭐ *(la previsione più forte: se la somma non si conserva, è sbagliata)* | ⛔ **blocchi sovrapposti** ⇒ la purezza **peggiora** e il giudice sente **distorsione, non buchi** (⚠ è il modo peggiore di fallire, ed **è già successo** in questo file: il rilievo 3 del 17 agosto) · **confine troppo permissivo** ⇒ `tardivi ≈ vecchi di prima`, la cura non ha curato niente · **confine troppo severo** ⇒ `vecchi` alto **con `fuori` a zero**, l'ancora è alla deriva (sintomo distintivo: `pieni` sale insieme) · `[?]` **Opus non tollera i timestamp non monotòni** ⇒ `errori` sale sul percorso Opus e resta **zero sul PCM**: **non verificato**, e il banco va fatto su tutt'e due i codec | §5.4 |
| **P7** | **il regolatore, scena MOSSA a 20 Mbit/s**: 20-37 fot/s (quelli che la scena produce), `arretrato` **0, ogni tanto 1, mai 2**, `video_ritmo_scesi` ⭐ **0** | ⛔ **discese con un desktop normale** ⇒ `POSTI = 2` è troppo stretto o un fotogramma costa più del misurato (**la riga di registro dice da sé quale dei due**) · **discese con `cwnd_left` ALTO** ⇒ non è la linea, è **la finestra del browser** · `video_saltati` che cresce con `arretrato` a 0 ⇒ il collo è **il credito di stream** · ⛔ **zero discese E zero letture di `arretrato`** ⇒ non è una previsione confermata, **è un anello mai percorso** — §6.5 | §6 |
| **P8** | **il regolatore, scena FERMA**: `video_ritmo_scesi` **invariato**. ⭐ La dimostrazione è **strutturale prima che sperimentale**: a desktop fermo Mutter non consegna, `video_a_una()` non viene chiamata, **il ramo non è raggiungibile** | ⛔ **e il controllo non può essere «il contatore è zero»**: vuoto e proibito hanno la stessa faccia. ⇒ **si fa a coppie nello stesso giro** — metà ferma e metà mossa alternate, `arretrato` **letto** in tutt'e due le metà. Un giro che non lo soddisfa **non ha misurato niente, e va buttato invece che interpretato** | §6 |
| **P9** | ⭐ **il confronto di `RCP.md` §4.3 lo farà il programma**, non chi legge: oggi le due righe ci sono ma il confronto è manuale | ⛔ un livello troppo basso **non dà un errore di rete**: **fa rifiutare la configurazione**, cioè schermo che non parte senza un rosso | §5.5 |

---

## §8 · ⛔ Che cosa NON ha funzionato

**23 agosto 2026 — tre inciampi, e tutt'e tre del BANCO, nessuno del prodotto.**

1. ⛔ **`wc -l < registro.log`: il `<` lo apre la shell di `nicfio`, non `sudo`.** Il registro è di
   root ⇒ uscita **vuota** ⇒ `riga0 = 0` ⇒ lo spoglio si prendeva **anche le sessioni di prima**.
   `[M]` Il primo giro contava **413** fotogrammi dove il server ne dichiarava **398**. ⚠ È la
   forma cattiva: non un rosso, **un numero plausibile**. ⇒ Cura: il file lo apre `wc`, che gira
   da root.
2. ⛔ **La scena lanciata con `ssh → sudo → setsid … > $LAV/scena.log`**: stessa famiglia — il
   redirect verso una cartella di root lo faceva `nicfio`, la scena moriva e **il suo registro era
   vuoto**, cioè *«non partita»* senza dire perché. ⇒ Cura: **uno script**,
   `banchi/09-b68-scena.sh` — *un file non ha livelli di virgolette*. ⚠ È la trappola già scritta
   in `07-b65-datagram.py` per il guardiano, ripagata.
3. ⛔⛔ **Il controllo positivo aveva bisogno, lui, di essere controllato.** Il primo giro di
   controllo ha stampato *«il contatore delle `RICHIEDI_CHIAVE` non si muove: il banco è cieco»* —
   e accusava il banco, mentre a non essere avvenuto era lo **stimolo**: nel cliente
   `--chiave-dopo` vive **dentro il ramo di `--puntatore-vecchia`**
   (`01-b3-cliente.py:1463`), e senza il puntatore la richiesta non parte mai. ⇒ Cura: la tela va
   prima **rimpicciolita** (`--adatta 1280x720@3 --puntatore-vecchia 0.3 --chiave-dopo 2`).
   ⭐ **La lezione**: un controllo positivo che dà rosso ha *due* imputati, e il primo da guardare
   è se il colpo è stato battuto.

⚠ **E una cosa che NON è un difetto ma va dichiarata**: la `scena ferma` è un GNOME **headless
senza finestre aperte**. Un desktop vero con un orologio in barra darebbe qualche fotogramma al
minuto invece di zero — la forma del risultato non cambia, l'ordine di grandezza sì.
⇒ ⛔ **Il giudizio finale resta di chi guarda, con un lavoro vero dentro.**

**Pomeriggio — altri cinque, e ⛔ quattro su cinque hanno prodotto «un numero plausibile».**
⭐ È la stessa forma tutte le volte (`LEZIONI.md` §1.9), e per questo vale la pena elencarli.

4. ⛔ **`pgrep -f 01-b3-cliente.py` trova sé stesso.** Il `bash -c` che porta quel testo nella
   propria riga di comando viene contato come una sessione. `[M]` 07:29: *«una sessione è già
   aperta (pid 18170)»* mentre di sessioni non ce n'era **nessuna**. ⇒ Cura: `01-b3-cliente[.]py`
   — la classe di caratteri non compare mai nella riga vera e compare sempre in quella
   dell'involucro.
5. ⛔⛔ **«C'è un processo» non è «c'è una sessione», e sono costati quattro bracci su sei.**
   Il banco ha visto vivo il cliente che il comando precedente aveva appena ucciso, non ne ha
   aperto uno nuovo, e trenta secondi dopo il cliente è morto davvero: da lì in poi **nessun
   `SPEDITO`**. Il banco non se n'è accorto. ⇒ Due cure: (a) la sessione la dichiara il **prodotto**
   nel suo registro (*canale video ACCESO* senza distacco dopo); (b) un braccio con **zero
   fotogrammi** esce come **guasto**, non come mediana vuota in mezzo agli altri.
6. ⛔ **`kill -9` dopo un secondo è un guasto, non una prudenza.** Il cliente ucciso di forza non
   manda il `CONGEDO`: il server tiene la sessione fino allo scadere dell'inattività QUIC e il giro
   dopo si becca `CONGEDO invece di SESSIONE: 0x0f GIA_ATTIVA_REMOTA`. ⇒ Cura: `TERM`, e **si
   aspetta**.
7. ⛔⛔ **L'`ESC` che apre la porta è lo stesso che la chiude.** `ESC` fa uscire dalla vista
   d'insieme di GNOME — ed è anche il tasto che fa uscire dallo **schermo intero del browser**.
   Mandato *dopo* aver acceso il video, spegneva il video che doveva accendere: `[M]` 08:13, il
   punto «video» ha dato **0,202 Mbit/s**, cioè lo stesso di «ferma». ⇒ Cura: l'ESC **prima**, e la
   pagina richiede lo schermo intero **ogni secondo** invece di una volta sola.
8. ⛔⛔ **`UID_B` va passato anche per spegnere.** `09-b72-video.sh -- spegni` senza `UID_B` prende
   il riposo **1001** e ammazza il Firefox di «prova», non quello di «prova2». ⇒ nei quattro punti
   del giro delle 08:11 **il video è rimasto acceso sotto tutti gli altri**, e «ferma» ha dato
   **25,9 fotogrammi/s e 0,235 Mbit/s**: un desktop fermo che non era fermo. ⇒ Cura: si spegne
   **e si verifica**, e chi non muore lo si dice.

⭐⭐ **La lezione del pomeriggio, e non è nuova**: cinque guasti su sei non hanno dato un rosso —
hanno dato **un numero che si poteva scrivere in tabella**. ⛔ Le due cose che li hanno trovati
tutti sono le stesse due: **guardare i pixel** (§3.7 è nato da un'immagine, non da un contatore) e
**pretendere che un contatore a zero sappia muoversi**.

---

## §9 · Le decisioni prodotte

- **`DECISIONI.md` §2.2**, riquadro del 23 agosto — ✅ **il 4K è un limite superiore, non una
  promessa al pavimento**: *«non pretendo di averlo su connessioni a 20 mbps»*. ⚠ E la riga di
  §3.1 *«fisso buono, 30+ ⇒ punta al desiderato»* non regge nemmeno a 30 per il 4K **mosso**.
  ⛔ Ne esce una misura obbligata per questa fase: **a quale banda il 4K in movimento diventa
  servibile** — si dichiara, non si promette. ⛔ E un vincolo che non è di banda: il livello H.264
  in vigore concede a 3840×2160 `[?]` **30,3 fotogrammi/s**, non 60 ⇒ **il «60 fps» del desiderato
  non è raggiungibile a 4K nemmeno con banda infinita.**
- **`DECISIONI.md` §2.1**, riquadro del 23 agosto — ✅ **480p · 25 fps resta**, ma come **fondo
  della scala**: sotto i 25/s su una linea da 20 Mbit/s è **un difetto**, non una degradazione.
- **`DECISIONI.md` §3.1-bis** — ✅ la rete minima è **20 Mbit/s**, pavimento dichiarato
  (23 agosto 2026). Conseguenze applicate lo stesso giorno in `SPECIFICHE.md` §8.1,
  `CODER.md` §1-bis, `PIANO.md` fase 9, e `DECISIONI.md` §3.1 marcata superata in parte.

### 9.1 ⭐⭐ Quel che le misure del pomeriggio mettono sul tavolo — *da decidere*

⛔ **Non sono decisioni prese: sono decisioni che adesso hanno i numeri per essere prese.**
`I6` vuole che ciò che cambia quel che si VEDE stia dietro un interruttore spento finché l'utente
non l'ha guardato.

> ⚠ **Questa tabella fu scritta a metà pomeriggio, quando ancora *«non era stata toccata una riga
> del prodotto»*.** ⭐ Poi le cure sono state scritte — §5 — **tutte dietro un interruttore spento**,
> tranne le due che non cambiano quel che si vede. ⛔ **Il giudizio dell'utente resta il passo che
> manca**, e la tabella resta perché è il verbale dei numeri che l'hanno obbligato.

| | il numero che la obbliga |
|---|---|
| ⛔ **il tetto di banda va scritto** — §0.3 lo chiamava «non esiste» | §3.8: un video con la grana a schermo intero chiede **58,7 Mbit/s = 293 %** del pavimento, e nessuno gli dice di no |
| ⭐ **ma NON per il contenuto vero** | §3.8: il desktop dell'utente a schermo intero costa **0,204 Mbit/s = 1 %**. ⇒ il tetto è per il **caso duro**, e un regolatore che si accendesse sul contenuto normale ripeterebbe **l'errore di v1** (*«contento di risparmiare»*, §0.2) |
| ⛔ **il regolatore NON può guardare quanti pixel cambiano** | §3.8: `pieno` muove **tutti** i pixel e costa 1,2 Mbit/s; `barra` muove gli stessi pixel con un retino e costa **21**. Due ordini di grandezza a parità di superficie |
| ⛔ **la cura di `video_sgombra()` è la leva giusta** | §3.10: `abbandoni §5.1` = `chiavi`, **uno a uno**, a ogni livello di banda. Togliere un abbandono toglie una chiave |
| ⭐ **e NON serve isteresi né memoria della discesa** | §3.10: dopo la riapertura il regime torna pieno in **meno di un secondo**, senza strascichi |
| ✅ **l'arresto a scena ferma NON è un difetto** | §3.6: 180 risvegli, **13 ms** da 0,2 s a 15 s di quiete, coda larga 2 ms. ⇒ §3.1 resta una violazione **letterale** di I1 che **non costa niente a chi guarda** |
| ⛔ **e non c'è niente da ottimizzare nel nostro tratto** | §3.6: dei 13 ms, **10 sono attesa del compositore** e **2,7** sono la codifica |

---

## §10 · ⛔⛔ LE CONTRADDIZIONI — dichiarate, **non lisciate**

> ⛔ **Due documenti della giornata dicono cose diverse.** Qui stanno tutt'e due le posizioni e
> **che cosa deciderebbe la questione**. ⚠ Chi legge non deve scegliere sulla fiducia: deve sapere
> quale misura manca.

### 10.1 ⛔ «Non serve nessun tetto di banda» **contro** «ne chiede il 293 %»

| | la posizione | su che cosa poggia |
|---|---|---|
| **la mattina** | *«Sul contenuto misurato, a 20 Mbit/s, il CQP 26 va benissimo, e non serve nessun controllo di bitrate.»* | `[M]` fase 8: sul contenuto **vero** dell'utente, **ogni fotogramma una chiave** — il regime peggiore che esista — la mediana è **24 956 byte** ⇒ a 20,9 fps sono **4,17 Mbit/s = il 21 %** del pavimento. **Quattro volte sotto**, perfino nello stato in cui il difetto di `video_sgombra()` lo fa cadere |
| **il pomeriggio** | ⛔ *«Serve un controllo del bitrate»* | `[M]` §3.8: un film con la grana a schermo intero, 2560×1080, QP 26, **58,668 Mbit/s = il 293 %** del pavimento |

⭐⭐ **E le due misure non si contraddicono sul numero: misurano due contenuti diversi** — e lo
studio della mattina lo aveva **scritto lui stesso**: *«il desktop dell'utente misurato in fase 8 NON
contiene quella scena»*. ⇒ La contraddizione vera è più stretta e va nominata:

⛔ **Quel che è stato SMENTITO è la stima del pomeriggio dello studio**: `[?]` **~19,9 Mbit/s**,
estrapolati da R31 di v1 riscalando pixel e scalini di QP, contro **58,7** misurati.
**Ottimista di tre volte.** ⇒ ⭐ L'estrapolazione da un ferro all'altro **non regge**, e questa è la
lezione che sopravvive alla giornata più della conclusione.

⚠ **E lo studio aveva scritto il suo stesso falsificatore, con la soglia**: *«sotto 10 Mbit/s ⇒ si
chiude tutto · fra 15 e 25 ⇒ serve un tetto, dietro l'interruttore spento · **sopra 30 ⇒ R31 è
confermata sul ferro nostro, e il tetto non è più un'opzione**»*. ⇒ **58,7 sta nel terzo ramo**, ed è
per questo che la cura 5 è stata scritta.

⇒ ⭐ **La sintesi che regge tutt'e due**: *il tetto è per il **caso duro**, e per il contenuto vero
deve essere inerte* — ⛔ **e un regolatore che si accendesse sul contenuto normale ripeterebbe
esattamente l'errore di v1** (*«contento di risparmiare»*). **È il rosso n° 1 della previsione P4**,
e la misura che lo decide c'è già: il desktop vero a tetto acceso deve costare **almeno** 0,204
Mbit/s.

### 10.2 ⛔ Quanto morde la spirale **sopra** il pavimento — due posizioni, e nessuna è decisa

| | la posizione | su che cosa poggia |
|---|---|---|
| **A** — *«il difetto vive SOTTO il pavimento; sopra, la cura è inerte»* | la soglia è **una robustezza sui transitori**, non la cura della fase | `[M]` **a 15 Mbit/s: 2 fotogrammi chiave su 1 019** ⇒ la catena dei delta era **intatta**, e 15 sta **sotto** il pavimento di 20. E `DECISIONI.md` §3.1-bis dice testualmente che sotto i 20 il prodotto *«non promette niente e non misura niente come requisito»* |
| **B** — *«morde anche sopra il pavimento»* | la spirale scatta anche su una linea larga | `[M]` §3.10, il gradino a 2560×1080 con `barra`: **abbandoni e chiavi anche nei secondi «larga»** — 3↔3 al secondo 5 (22,1 Mbit/s sul filo) e 1↔1 al secondo 6 (26,3). ⇒ `video_sgombra()` abbandona **anche quando la linea porta** |

⛔ **Non si sceglie qui, e la ragione è che le due misure non sono confrontabili**: `barra` è un
gradiente **retinato** sintetico che chiede **21 Mbit/s** da solo, cioè **cento volte** il desktop
vero (0,204). Un contenuto che consuma tutto il pavimento produce una coda anche su linea larga;
il contenuto per cui il prodotto esiste no.

⭐⭐ **CHE COSA DECIDEREBBE LA QUESTIONE — una misura sola, e si può fare domani:**

> **`abbandoni §5.1` al secondo, con l'interruttore SPENTO, a 20 Mbit/s strozzati sul percorso
> vero, sul DESKTOP VERO dell'utente** — non su `barra`, non su `pieno`, non a 2 Mbit/s.

| esito | ⇒ chi ha ragione |
|---|---|
| **≈ 0 abbandoni/s** | ⭐ **A**: la soglia è un parapetto sui transitori, la fase 9 spende il suo tempo sul regolatore, e la cura 2 resta un **prerequisito** |
| **abbandoni al secondo in regime** | ⛔ **B**: il difetto morde **sopra** il pavimento ⇒ la soglia **non è una robustezza, è una cura di prodotto**, e ⛔ **cambia la priorità della fase** |

⚠ **E l'altra metà della domanda è già decisa**: `[M]` §3.10 dimostra che **strozzare a 20 Mbit/s
costante non avrebbe mostrato nulla** — serve il **gradino**. ⇒ La misura sopra si fa **in regime**
per rispondere ad A/B, e **col gradino** per misurare la cura: sono **due giri, non uno**.

---

## §11 · Che cosa resta `[?]`

| | dove |
|---|---|
| ✅ **il SEGV sul fotogramma da 525 KB — CHIUSO il 23 agosto pomeriggio**: la causa è provata riga per riga e ⭐ **la cura è applicata**. ⛔ Resta `[?]` **una cosa sola: la riproduzione**, che non è stata eseguita ⇒ finché la ricetta non gira, è una **causa probabile con la riga**, non una causa vista — e la cura non ha una prova di aver curato | §4 · §4.5 · §4.8 |
| ⏳ ⛔ **la trappola non è armata**: niente core dump, il registro è condiviso e viene sepolto, `dmesg` non si raccoglie allo spegnimento | §4.7 |
| ✅ **il tetto di banda: quale, e su che grandezza — DECISO il 23 agosto**: `QVBR`, con filo · punto di lavoro · serbatoio derivati dal pavimento, `--tetto-banda-mbit`, **spento**. ⛔ Resta `[?]` la misura sulla macchina di prova (P4) | §5.5 · `codificatore.c:200-340` |
| ⏳ `[?]` **il film con la grana non si misura oltre i 25 s su questa macchina**: la decodifica VP8 software a 2560x1080 affama il **cliente**, che sta sulla stessa macchina, e QUIC cade per *idle timeout*. ⇒ il numero di §3.8 è buono, ma un giro lungo vuole un cliente su un'altra macchina | §3.8 |
| ✅ la cura di **`video_sgombra()`** — ⭐ **scritta il 23 agosto**, dietro `--sgombra-soglia-ms`, **spenta**. ⛔ Resta `[?]` la misura (P3) e ⛔⛔ **il prezzo, che lo giudica l'utente**: ~150 ms di immagine leggermente vecchia sotto congestione | §5.2 · `webtransport.c:2705-2800` |
| ✅ la **finestra di riordino dell'audio** — ⭐ **scritta il 23 agosto**, senza interruttore (allentamento puro). ⛔ Resta `[?]` **la verifica, e il banco prescritto NON PUÒ farla**: misura se stesso — serve un banco che faccia girare **la pagina** | §5.4 · §3.16 · `pagina.html:5882` |
| ⏳ `[?]` **il riordino su Opus**: la misura è in **PCM da 5 ms**, con Opus la soglia di sorpasso è **4 volte più alta** e il difetto morde 4 volte meno ⇒ il percorso vero è Opus, e su Opus il numero non c'è. ⚠ E `[?]` se il decodificatore Opus tolleri i timestamp non monotòni: **non verificato** | §5.4 · P6 |
| ⏳ `[?]` la qualità di **`EncSliceLP`** contro l'entrypoint pieno a parità di banda — **mai misurata**, e ⚠ **sul ferro di casa non si può fare**: serve l'AMD | `PIANO.md:1197` |
| ⏳ `[?]` i **sotto-livelli temporali** su `EncSliceLP` — `[M]` il driver non dichiara `EncRateControlExt` su 7 profili su 7 ⇒ *«ogni abbandono costa una chiave» resta in vigore* | `RCP.md:1261` |
| ✅ `[R]` **`qualita_corrente` era un cricchetto a senso unico** — ⭐ **curato il 23 agosto** (`risali_qualita()`), dietro `--qualita-risale`, **spenta**. ⛔ Resta `[?]` la misura, e il controllo che decide è lo **SBATTIMENTO** (P5) | §5.3 · `codificatore.c:3446` |
| ⏳ ⛔ **il regolatore del ritmo — disegnato, NON scritto**: è il lavoro che resta, e ⛔ **l'ordine è obbligato** (prima la soglia della coda, o `arretrato` è zero per costruzione) | §6 |
| ⏳ ⛔ **il registro delle discese** (`🔻`/`🔺 RITMO`) — progettato, non applicato. E ⛔ **il pavimento (480p·25 e 20 Mbit/s) non esiste ancora nel codice** | §7.1 · §7.2 |
| ⏳ `[?]` **l'algoritmo di congestione non è mai stato scelto**: si prende CUBIC di ngtcp2. ⚠ Su WiFi CUBIC legge una perdita **da radio** come congestione; BBR lavora su banda di collo di bottiglia e `min_rtt`. ⛔ **Esperimento separato, dietro il suo interruttore** — non due variabili nello stesso banco | §6.3 |
| ⏳ `[R]` il **confronto `livello_flusso` ≤ `video.livello`**: le due righe adesso ci sono, ⛔ **ma il confronto lo fa chi legge, non il programma** | §5.5 · P9 |
| ⏳ `[?]` il valore di **`CRF_PASSO`** (9 è *sufficiente, non giusto*); la scala effettiva è **26 → 35 → 44 → 51** | `codificatore.c:84` |
| ⏳ **`AUDIO_CUSCINO_MS = 250`** non abbassato: deve coprire **il jitter d'arrivo, che nessuno ha misurato**. ⚠ E **non c'entra con la banda**: è un problema di thread | `pagina.html:5543` |
| ⏳ la **migrazione QUIC** da WiFi a rete mobile — *«la ragione migliore per cui QUIC è stato scelto»* | `PIANO.md:1437` |
| ⏳ il **datagram audio su rete non locale**, mai misurato (sonda `banchi/07-b40`) | `RCP.md:1329` |
| ✅ *chiusa il 23 ago* — **§2.1, il minimo resta 480p · 25 fps**: *«480p/25fps è il pavimento»*. ⛔ Cambia la ragione: è **il fondo della scala di degradazione**, non più il livello a cui una linea povera costringe ⇒ **un ritmo sotto i 25 su una linea da 20 Mbit/s è un DIFETTO** | `DECISIONI.md` §2.1 |
| ❓ il **budget di rete** accanto a quello di GPU: dieci sessioni × 20 Mbit/s = **200 Mbit/s** sul filo. Da misurare in fase 10 | `DECISIONI.md` §4.6 |
| ⚠ il **livello H.264 dichiarato** è `avc1.640032` (High **5.0**), ma oltre i 40 Mbit/s serve **5.1**: un livello troppo basso non dà errore, **fa rifiutare la configurazione** | `SPECIFICHE.md:1087` |

---

## §12 · Il giudizio dell'utente

⏳ *La fase non è arrivata al giudizio.*

⛔ **E ci sono due cose precise che aspettano lui**, elencate in **S.5** con il prezzo accanto: la
**soglia sulla coda** (`--sgombra-soglia-ms`) e il **tetto di banda** (`--tetto-banda-mbit`). ⚠ Tutte
e due cambiano quel che si VEDE, tutte e due nascono spente, e ⛔ **quale sia il male minore non lo
decide una misura**: è esattamente la lezione dell'azzeramento della fase 10 di v1.

---

# §13 · ⭐⭐ IL SECONDO GIRO DI MISURE — *23 agosto 2026, pomeriggio-sera*

> ⛔ **Questa sezione si riempie strada facendo**, un numero alla volta con l'ora accanto.
> Le previsioni sono quelle di **§7.4 (P1…P9)** e della sintesi **S.5**: qui, accanto a ogni
> numero, c'è **l'atteso**.

## 13.0 ⛔ DA CHE CODICE VENGONO QUESTI NUMERI — gli `md5`, e perché stanno in testa

⛔ **Il primo fatto della sera è che l'albero della 7920 era VECCHIO.** `/media/REMOTIX/src/09c-src`
portava un `webtransport.c` del 23 agosto **09:23** (`md5 958170e2…`) — cioè **senza il regolatore
del ritmo** (cura 6): mancavano `video_ritmo_scesi`, `ritmo_frena()`, `ritmo_ciclo()`,
`wt_ritmo_adattivo()`, **506 righe di diff**. ⇒ Ogni misura presa su quel binario con
`--ritmo-adattivo` avrebbe dato *«zero discese»* **perché l'opzione non esisteva**, non perché il
regolatore non scattava. ⚠ È esattamente il difetto D5 di questa fase, con un'altra faccia.

⭐ **Rifatti tutt'e due gli alberi dal codice committato `f90eb21`**, alle **15:05-15:20 locali**:

| albero | `webtransport.c` | che cos'è |
|---|---|---|
| `/media/REMOTIX/src/09c-src` | `md5 4785abf10e50bf4d86ce638a21bd685b` | ⭐ **il CURATO** — identico byte per byte a `src/webtransport.c` di `f90eb21` |
| `/media/REMOTIX/src/09c-mal-src` | `md5 69e2d57fac73f48ce9e0ef6c0e628add` | ⛔ **il MALATO** — l'unica differenza è `coda_uccidi()` al posto di `coda_consegna()` (`:6421`), cioè il difetto delle 08:28:09 rimesso apposta: **è il controllo positivo** |

Gli altri sorgenti sono identici nei due alberi e al commit:
`codificatore.c md5 5a29b80787042b0c6511c74d159c1bd0` · `main.c md5 2aa34655c19e20b5f0acf35c9c0af484` ·
`pagina.html md5 e010d615f10643d5c6e2a2c01ae5ff25`.

⚠ **E `--pagina` adesso punta al PROPRIO albero**: il server acceso a metà pomeriggio serviva
`/media/REMOTIX/src/09-src/src/pagina.html`, cioè la pagina **prima** della cura 4.

## 13.0-bis ⛔ DUE INCIAMPI DELLA RICOSTRUZIONE — *15:05-15:20*, e il primo è **la trappola di questa fase**

1. ⛔⛔ **`enter.sh` è rimasto appeso 13 minuti su `sudo`, e la causa non è quella che sembra.**
   Il copione dava la parola **una volta** (`printf 'nicfio\n' | sudo -S -v`) e poi chiamava
   `bash /media/REMOTIX/enter.sh --root '…'`, contando che la credenziale fosse in cassa.
   ⛔ **Non lo è**: `enter.sh` fa il suo `sudo -n true`, che **fallisce**, e ricade su
   `sudo -v -S -p 'Password sudo: '` — che si mette a leggere dal proprio standard input, cioè da
   una pipe di `ssh` **aperta e vuota**. ⇒ processo in `do_wait`, **zero righe di registro, zero
   figli, carico 0,08**: la faccia di un compilatore lento.
   ⭐ **Perché la credenziale non si eredita**: `sudo` di serie tiene il segno **per terminale**
   (`timestamp_type=tty`), e **senza tty ricade sul processo padre**. Due processi fratelli sono
   due padri diversi ⇒ due casse diverse. ⛔ **La forma che funziona è quella scritta in `enter.sh`
   stesso, riga 17**: `printf '%s\n' "$PASSWORD" | bash /media/REMOTIX/enter.sh "…"` — la parola va
   data **a `enter.sh`**, non a un `sudo` di prima.
   ⇒ Rifatto così, **i due alberi si sono costruiti in 7 secondi l'uno**, `make -j` e tutto
   (`13:18:16 → 13:18:30` UTC), con `OK make e' uscito 0` e le dodici marche dentro il binario.
2. ⚠ **Il `tar` del codice non basta a far girare un banco.** `src` + `banchi/rcp` costruisce, ma
   la sessione di prova la apre `banchi/01-b3-cliente.py`, che non c'era ⇒
   `SESSIONE MORTA prima di aprirsi — python3: can't open file …`. ⭐ Rosso **immediato e
   onesto**, in 20 secondi: il banco ha detto *quale* file mancava. ⇒ copiato tutto `banchi/*.py`
   `*.sh` in tutt'e due gli alberi (`01-b3-cliente.py md5 13e68d19ed44298b7926cded53affdda`,
   **lo stesso** dei due alberi del mattino: il metro non è cambiato).

## 13.1 ⛔⭐⭐ P1 — LA CURA DELLA MEMORIA: i due binari appaiati

⛔ **La forma della prova**, e non è negoziabile: *«il curato non è morto»* non è un risultato — ha
la stessa faccia di uno stimolo che non stimola. ⇒ **stessa porta, stessa cartella di lavoro,
stessa scena, stessa perdita**, e l'unica variabile è la riga `webtransport.c:6421`.

⭐ **La trappola di glibc è verificata nel processo VIVO**, non nel copione:
`MALLOC_MMAP_THRESHOLD_=32768 MALLOC_PERTURB_=165` letti da `/proc/PID/environ`.

### 13.1.1 ⛔⭐⭐⭐ IL MALATO È MORTO — *23 agosto 2026, 13:21:11 UTC*, e **il caso è chiuso senza margine**

`[M]` **Braccio MALATO** (`09c-mal-src`, `remotix md5 53a7e3be82f2a1f43afe6ead4398012d`), scena
**film con la grana a schermo intero, 2560×1080**, sessione di `prova2`, trappola glibc armata e
verificata nel processo vivo.

| | atteso (**P1**) | `[M]` misurato |
|---|---|---|
| muore? | ⛔ **sì, o la diagnosi di §4 è sbagliata** | ⭐ **SÌ**, alle **13:21:11** |
| il segnale | `SEGV`, `error 4` | ⭐ `segfault at 7fc39818e4ca ip 00007fc39f338b49 **error 4** in libc.so.6[**162b49**…]` |
| dove | sempre in `__memmove_avx_unaligned_erms` | ⭐ **lo stesso identico scostamento `162b49`** del crollo delle 08:28:10 |
| il core | §4.7 punto 1 lo voleva **assoluto** | ⭐ **c'è**: `core.remotix.86418…`, **48 529 408 byte** |

⭐⭐⭐ **E il core ha dato la pila, cioè quel che §4.8 dichiarava `[?]` — «la ritrasmissione non è
stata vista con gli occhi».** Adesso lo è:

```
#0  __memmove_avx_unaligned_erms          ← libc, rip 0x…b49
#1  ngtcp2_cpymem                          ← ngtcp2_pkt.c:1619
#2  ngtcp2_pkt_encode_stream_frame
#3  ngtcp2_ppe_encode_frame
#4  conn_write_pkt
#5  ngtcp2_conn_write_vmsg
#6  ngtcp2_conn_writev_stream_versioned
#7  wt_scrivi (…) at webtransport.c:6314   ← NOSTRO
#9  scrivi_connessione at trasporto.c:422
#12 main at main.c:1395
```

⛔ **È la catena scritta a mano in §4.8, riga per riga, adesso letta dal core.** ⇒ il `[?]` di §4.8
**si chiude**: la causa non è più *«probabile con la riga»*, è **vista**.

⭐⭐ **E c'è di più — e cambia la ricetta.** L'ultima riga del registro, 300 ms prima della morte:

```
13:21:10.776 rcp  fotogramma 27 SPEDITO: delta 0x0302, codec 1, 2560x1080, 516782 byte di dati, stream 119, FIN
```

⛔ **`516 782` byte — il gemello del `525 298` delle 08:28:09.** ⇒ **basta un fotogramma grosso: la
perdita non serve.** Il server è morto **al fotogramma 27, in 13 secondi di sessione**, e
⛔ **`netem loss 5%` non era ancora stato applicato** (arriva 13 s dopo, alle 13:21:24). ⚠ La
ricetta **B** di §4.5 chiedeva la perdita vera; la **A** chiedeva il client congelato: `[M]`
**non serve né l'una né l'altra**. Con `MALLOC_MMAP_THRESHOLD_=32768` bastano **un mezzo mega di
delta e loopback pulito** — perché un fotogramma da 516 KB non entra in un pacchetto e ngtcp2
rilegge **il nostro puntatore** al pacchetto dopo, che nel malato è già `munmap`-ato.
⇒ **La ricetta più corta di tutte, e la più severa**: 27 fotogrammi contro **45 005**.

### 13.1.2 ⭐⭐⭐ IL CURATO HA RETTO — *13:22:35 → 13:25:03*, e lo stimolo era **più duro**

`[M]` **Braccio CURATO** (`09c-src`, `remotix md5 162d2d105cbe930e7921a7041053f5e7`), **identico in
tutto** al braccio malato: stessa porta 7920, stessa cartella `tmp/09c`, stessa sessione di
`prova2` a 2560×1080, stesso film con la grana, stessa trappola glibc verificata nel processo vivo.

| | MALATO `09c-mal-src` | ⭐ CURATO `09c-src` |
|---|---|---|
| fotogrammi spediti | ⛔ **27**, poi morto | ⭐ **1 463** |
| taglia mediana | — | **302 984** byte |
| **taglia massima** | 516 782 (l'ultimo) | ⭐⭐ **537 063** byte — ⛔ **più grosso dei 525 298 che l'avevano ucciso stamattina** |
| fotogrammi sopra i 32 KiB nei primi 6 s | 0 letti (morto prima) | ⭐ **173 su 173** — cioè **ogni** fotogramma passava dalla trappola |
| `netem loss 5%` | ⛔ **non è nemmeno servito** | ⭐ **120 s interi** con la perdita addosso |
| esito | ⛔ `SEGV` a 13:21:11 | ⭐ **VIVO**, nessun core, nessuna riga in `dmesg` |

⛔⛔ **E lo stimolo del curato è stato PIÙ severo di quello che ha ucciso il malato**, non meno: più
fotogrammi (1 463 contro 27), più grossi (fino a 537 063 byte), e per giunta **con il 5 % di
perdita**. ⇒ *«il curato non è morto»* qui **non** ha la faccia di uno stimolo che non stimola.

### 13.1.3 ⭐ LA GRANDEZZA CHE DICE SE LA CURA PERDE MEMORIA — e non ne perde

La riga della chiusura, `13:25:35.869` (`webtransport.c:5789`):

```
⭐ FASE 9, i byte TENUTI per la ritrasmissione (contratto di ngtcp2_conn_writev_stream):
   punta 537063 byte, residuo alla chiusura 31, e 1185696 byte ancora da spedire in coda
```

| grandezza | atteso | `[M]` |
|---|---|---|
| `byte_in_volo_max` (la punta) | ⭐ **oscilla**, non cresce | **537 063** byte = **esattamente un fotogramma**, il più grosso della sessione. ⛔ In 1 463 fotogrammi sono passati **~443 MB**: se trattenesse senza liberare, la punta sarebbe quella. ⇒ **la cura libera** |
| residuo alla chiusura | **zero** | ⚠ **31 byte** — non zero, ma **31**: la coda di uno stream ancora non riscontrato nell'istante di uno strappo brutale (il cliente ucciso, col 5 % di perdita addosso). ⛔ **Lo dichiaro invece di arrotondarlo**: è il verde, non il pieno verde |
| byte ancora in coda | — | 1 185 696 — quel che non era ancora partito quando il cliente è sparito |

⭐ **E la stessa riga di chiusura porta il numero che serve a P2**, con l'interruttore **spento**:

```
⭐ FASE 9, la soglia della coda video: spenta (I6) (0 ms) — delta TENUTI 0,
   abbandonati per soglia 594, e NON ACCETTATI per credito mancato 0
```

⇒ ⛔ **594 delta abbandonati** in 178 s di film duro col 5 % di perdita, e **`credito mancato` = 0**:
il debito **non** viene dalla causa 4 di §2.3.

### 13.1.4 ⛔ VERDETTO SU P1 — **la previsione ha retto, e più di quanto chiedeva**

| | |
|---|---|
| **il crollo si riproduce** | ⭐ **SÌ** — e con una ricetta **più corta** di tutt'e tre quelle di §4.5 |
| **la cura regge** | ⭐ **SÌ**, appaiata, sullo stesso ferro e con lo stimolo più duro |
| **la causa è vista, non dedotta** | ⭐ **SÌ** — la pila dal core chiude il `[?]` di §4.8 |
| **la memoria non si perde** | ⭐ **SÌ** — la punta vale un fotogramma su ~443 MB passati |

⚠ **E i due difetti del banco che vanno detti** (nessuno cambia l'esito, tutt'e due cambiano il
banco):
1. `09-b73-memoria.py` **legge la riga `byte TENUTI` troppo presto** — la cerca 3 s dopo la morte del
   cliente, e il server la scrive quando smonta la sessione WebTransport. ⇒ il banco ha stampato
   *«(nessuna riga «byte TENUTI»)»* mentre la riga **c'era**, scritta 3 secondi dopo. ⛔ È la forma
   cattiva: **un'assenza che sembra un risultato**;
2. `b71.pulizia()` **non guarda Firefox**. Il suo `pgrep` copre `04-b30-scena`, `01-b3-cliente`,
   `b70-ritmo`, `b65-datagram` — ⛔ **non `firefox`**. ⇒ per tutt'e due i bracci è rimasto vivo un
   Firefox orfano del banco `09-b74` nella sessione di `prova` (uid 1001), e il banco ha detto
   *«altri banchi vivi: nessuno»*. ⚠ Non tocca l'esito (è la **stessa** sporcizia nei due bracci, ed
   era su un'altra sessione), ma è **precisamente il difetto che ha già prodotto oggi numeri
   plausibili e sbagliati**.

### 13.1.5 ⭐⭐ IL CROLLO SI RIPRODUCE **DUE VOLTE SU DUE** — e il terzo inciampo del banco

⛔ **Il core di 13.1.1 non c'è più, e l'ho cancellato io senza volerlo.** `09-b73-memoria.py`
comincia ogni braccio con `rm -f registro.log core.*` — serve a non mescolare i due giri, ⛔ **ma
butta anche la prova del braccio prima.** ⇒ Facendo girare il braccio *curato* ho distrutto il core
del *malato*. ⭐ La **pila** era già stata letta e sta qui sopra: quel che si è perso è il file.

⭐⭐ **E rifarlo è costato due minuti, con un guadagno**: il crollo si è riprodotto **una seconda
volta, identico**.

| | primo giro | ⭐ secondo giro |
|---|---|---|
| ora | **13:21:11** | **14:03:24** |
| segnale | `segfault … error 4 in libc.so.6[**162b49**…]` | `segfault … error 4 in libc.so.6[**162b49**…]` |
| tempo per morire | **0,3 s** dall'inizio dell'attesa | **0,3 s** |
| core | (cancellato) | ⭐ `core.remotix.110832.1787493803`, **48 525 312 byte** |

⇒ ⛔ **Due su due, stesso scostamento in libc, stesso codice d'errore.** Non è un caso raro da
1 su 45 005: **con la trappola armata è deterministico.**

⚠ **La correzione da fare al banco** (non l'ho fatta: `src/` e i banchi non si toccano stasera):
`09-b73` deve cancellare **solo il registro**, e mettere i core in una cartella per braccio.

## 13.2 ⭐⭐ P2/P3 — LA SOGLIA SULLA CODA, sul gradino, appaiata

**Il giro**: 8 s larga → **3 s a 10 Mbit/s** → 17 s larga, scena `barra`, **1920×1080**, sessione di
`prova2`, `netem` solo sulla 7920 di `lo` col guardiano armato. ⛔ Trappola glibc **spenta**
(`MALLOC=no`) in tutt'e due i bracci: `MALLOC_MMAP_THRESHOLD_` è lenta, e lasciarla accesa
avrebbe misurato **lei** invece della soglia.

### 13.2.1 `[M]` IL BRACCIO A INTERRUTTORE SPENTO — *13:27:20 → 13:28:0x*, e serve da metro

`⭐ FASE 9, la soglia della coda video: **spenta (I6) (0 ms)**` — letto dal registro del server.

| s | fot | chiavi | abbandoni §5.1 | filo Mbit/s | fase |
|---|---|---|---|---|---|
| 5-7 | 40-41 | **0** | **0** | 21,1-21,5 | larga |
| **8** | 21 | ⛔ **6** | ⛔ **6** | 9,87 | **stretta** |
| **9** | 25 | ⛔ **6** | ⛔ **6** | 9,14 | **stretta** |
| **10** | 22 | ⛔ **6** | ⛔ **7** | 9,87 | **stretta** |
| 11 | 28 | 4 | 3 | 16,87 | (ritorno) |
| 12-27 | 39-42 | **0** | **0** | 20,4-23,0 | larga |

⭐ **`abbandoni` = `chiavi`, uno a uno, a ogni secondo** (6↔6, 6↔6, 7↔6): §3.10 si riproduce
**identico**, ed è il meccanismo della spirale visto in diretta.
⭐ **E il ritorno è immediato**: dal secondo 12 si è già a 40/s con **zero** chiavi — nessuna
isteresi, nessuno strascico in 16 s.
⚠ **Un numero che NON coincide col «prima» citato**: `[M]` di stamattina dava **13-14 fot/s** nei
secondi 8-10; qui sono **21-25**. ⛔ Lo dichiaro invece di lisciarlo — il metro del *prima* e quello
di adesso non sono lo stesso giro, e **il paragone che vale è quello appaiato di qui sotto**, preso
a mezz'ora di distanza sulla stessa porta, stessa scena, stessa tela, stesso binario.

### 13.2.2 ⛔⭐ IL BRACCIO CON `--sgombra-soglia-ms 100` — *13:28:26 → 13:29:1x*: **il meccanismo gira, l'effetto promesso NON arriva**

`⭐ FASE 9, soglia della coda video (§5.1): **100 ms** … Impostata da: main.c, dalla riga di comando`
— letto dal registro del server, non dedotto dal comando.

| s | fot **spenta → 100 ms** | chiavi **spenta → 100** | abbandoni **spenta → 100** |
|---|---|---|---|
| 5-7 (larga) | 39-41 → **39-40** | 0 → **0** | 0 → **0** |
| **8** | 21 → **29** | 6 → **4** | 6 → **6** |
| **9** | 25 → **26** | 6 → **5** | 6 → ⛔ **9** |
| **10** | 22 → **21** | 6 → **5** | 7 → **5** |
| 11 (ritorno) | 28 → **34** | 4 → **3** | 3 → **3** |
| 12-27 (larga) | 39-42 → **39-42** | 0 → **0** | 0 → **0** |

| la previsione (**P3** e S.5) | `[M]` | esito |
|---|---|---|
| fot/s nei sec 8-10 **≥ 25** | **29 · 26 · 21** | ⚠ **due su tre** |
| chiavi/s **≤ 2** | **4 · 5 · 5** | ⛔ **NO** |
| abbandoni/s **≤ 2** | **6 · 9 · 5** | ⛔ **NO** — e al secondo 9 sono **saliti** |
| secondi 7 e 12 **identici** a interruttore spento | 40/39 e 40/39, **0 chiavi** in tutt'e quattro | ⭐ **SÌ — la cura è INERTE sulla linea larga** |
| ritorno **≥ 32/s** entro un secondo | sec 11 **34/s**, sec 12 **39/s** | ⭐ **SÌ**, e meglio del braccio spento (28) |
| ⭐ **`arretrato` deve salire a 2-3** (oggi zero per costruzione) | **2 (14 volte) · 3 (19) · 4 (6)** | ⭐⭐ **SÌ, e arriva a 4** |

⭐⭐ **E il meccanismo si vede lavorare, riga per riga**: **17 attraversamenti SOPRA** la soglia e
**17 ritorni SOTTO** nei 3 secondi di stretta, con le righe che dicono da sé che cosa hanno fatto:

```
⛔ la coda del video passa SOPRA la soglia (135475 byte = 114 ms, soglia 100 ms,
   dalla banda misurata (cwnd/rtt)), arretrato 2 delta: da qui i piu' vecchi si abbandonano
⭐ la coda del video torna SOTTO la soglia (100369 byte = 84 ms, soglia 100 ms):
   i 2 delta arretrati si TENGONO — §5.1 dice PUO', non DEVE
```

### 13.2.3 ⛔⛔ LA DIAGNOSI, E LA CURA VA TARATA NEL VERSO **OPPOSTO** A QUELLO PREVISTO

⛔ **P3 aveva già scritto il rimedio per questo caso, e lo scriveva al contrario**: *«i fot/s non
salgono ⇒ soglia troppo alta, **si scende a 50**»*. ⭐ **I byte dicono di salire.** Ecco perché — i
**17** valori a cui la coda ha attraversato la soglia, in ms:

```
101 · 103 · 106 · 109 · 113 · 114 · 116 · 117 · 117 · 120 · 125 · 126 · 126 · 128 · 134 · 135 · 138
```

⛔ **Sono TUTTI fra 101 e 138.** Durante la stretta la coda del video **oscilla proprio attorno ai
100 ms**: la soglia è piantata **in mezzo all'oscillazione**, e ogni mezzo respiro la fa
attraversare. ⇒ La cura passa metà del tempo a **tenere** e metà ad **abbandonare**, e il totale
degli abbandoni resta **23 contro 24** — cioè **nessuna differenza**.
⛔ **Con la soglia a 50 ms l'attraversamento sarebbe sempre in corso e la cura tornerebbe a
`sgombra` puro**, cioè peggio. ⇒ **il verso giusto è ALZARLA**, e la previsione da falsificare
adesso è: *a 200 ms gli attraversamenti crollano, chiavi e abbandoni con loro*.

### 13.2.4 ⭐⭐⭐ LA PROVA CHE DECIDE — *a 200 ms gli attraversamenti NON crollano: si spostano*

`[M]` 13:30. Stesso giro, `--sgombra-soglia-ms 200`. I **14** valori a cui la coda ha attraversato:

```
204 · 206 · 209 · 211 · 211 · 212 · 219 · 221 · 222 · 222 · 224 · 225 · 227 · 236 ms
```

⛔⛔ **Di nuovo tutti appena SOPRA la soglia, come a 100 erano tutti fra 101 e 138.**

⭐⭐⭐ **E questa è la scoperta della sera, e cambia il modo di leggere la cura 2**: la soglia
**non è un filtro, è il PUNTO DI LAVORO della coda.** `video_sgombra()` abbandona non appena la
coda supera la soglia ⇒ **la coda non può mai andare molto sopra**, qualunque numero si scelga: si
assesta appena oltre. ⇒ Il numero degli abbandoni **non lo decide la soglia**: lo decide lo scarto
fra quanto entra e quanto esce. La soglia decide **quanto in profondità si accumula prima di
abbandonare**, cioè **quanto ritardo si paga**.

| | spenta | **100 ms** | **200 ms** |
|---|---|---|---|
| fotogrammi nei 3 s | 68 | 76 | **79** |
| ⛔ **chiavi** nei 3 s | **18** | 14 | **11** |
| abbandoni §5.1, tutto il giro | 24 | 23 | **18** |
| kbyte consegnati nei 3 s | 3 896 | 4 300 | **4 476** (+15 %) |
| ⚠ **`arretrato`** (il prezzo) | 0-1 per costruzione | 2 (14×) · 3 (19×) · **4** (6×) | 3 · **4** (15×) · **5** (10×) · **6** (6×) |
| ⚠ **il ritardo pagato** | — | 101-138 ms | ⛔ **204-236 ms** |

⭐ **C'è un miglioramento, ed è monotòno**: più alta la soglia, più fotogrammi e meno chiavi.
⛔ **Ma è LONTANO da quel che P3 prometteva** — *chiavi ≤ 2/s* è uscito **3-5/s**, e *abbandoni
≤ 2/s* è uscito **5-6/s**. ⇒ **P3 è SMENTITA sui due numeri che contavano**, e confermata su quelli
di contorno (inerzia sulla linea larga, ritorno sotto il secondo).

⛔⛔ **E il prezzo per l'utente va corretto verso l'alto.** S.5 dichiarava *«fino a ~150 ms di
ritardo per un attimo (~205 ms dal gesto al pixel)»*. `[M]` a soglia 100 la coda arriva a **138 ms**
(⇒ ~193 ms d'anello) e **a soglia 200 arriva a 236 ms** (⇒ **~291 ms d'anello**). ⚠ La stima di
S.5 era **giusta per 100 ms e sbagliata per qualunque taratura più generosa**, e la taratura più
generosa è proprio quella che dà l'immagine migliore. ⛔ **È il compromesso che decide lui, e adesso
ha i due numeri.**

⭐ **E una cosa la soglia l'ha fatta bene, ed è il suo prerequisito**: ha portato `arretrato` da
**0-1 per costruzione** a **2-6**. ⇒ `WT_RITMO_POSTI = 2` è **superato di continuo**, e il
regolatore del ritmo — che senza la soglia non scatterebbe mai — adesso **può** scattare.

## 13.3 ⭐⭐⭐ P7 — IL REGOLATORE DEL RITMO: **la spirale si spegne, e i due contatori vanno a ZERO**

**Il giro**: identico ai tre di sopra — 8 s larga → 3 s a 10 Mbit/s → 17 s larga, `barra`,
1920×1080 — con `--sgombra-soglia-ms 100 --ritmo-adattivo`. Le due righe d'avvio, **testuali**:

```
⭐ FASE 9, soglia della coda video (§5.1): 100 ms … Impostata da: main.c, dalla riga di comando
⭐ FASE 9: il regolatore del ritmo e' ACCESO (`--ritmo-adattivo`): un fotogramma NON parte
   quando 2 delta in volo hanno ancora byte nella mia coda d'uscita
```

### 13.3.1 ⛔⭐⭐⭐ I QUATTRO BRACCI, AFFIANCATI — *e il quarto non somiglia agli altri tre*

| nei 3 s di stretta | spenta | soglia 100 | soglia 200 | ⭐⭐ **100 + ritmo** |
|---|---|---|---|---|
| fotogrammi/s | 21 · 25 · 22 | 29 · 26 · 21 | 31 · 23 · 25 | 26 · 23 · **20** |
| ⛔ **CHIAVI/s** | **6 · 6 · 6** | 4 · 5 · 5 | 3 · 5 · 3 | ⭐⭐⭐ **0 · 0 · 0** |
| ⛔ **abbandoni §5.1/s** | **6 · 6 · 7** | 6 · 9 · 5 | 5 · 6 · 5 | ⭐⭐⭐ **0 · 0 · 0** |
| chiavi in tutto il giro | 18 | 14 | 11 | ⭐ **0** |
| abbandoni in tutto il giro | 24 | 23 | 18 | ⭐ **0** |
| sulla linea larga (sec 0-7, 12-28) | 39-42 fot/s, 0 chiavi | idem | idem | ⭐ **idem: 37-41 fot/s, 0 chiavi** |

⛔⛔ **La spirale non è stata attenuata: è stata SPENTA.** Zero chiavi e zero abbandoni in tutto il
giro — e non perché la soglia abbia lavorato meglio, ⭐ **ma perché non ha dovuto lavorare affatto**:
`passa SOPRA la soglia` **0 volte**, `torna SOTTO` **0 volte**. Il regolatore tiene `arretrato`
inchiodato a **2**, e la coda non arriva mai ai 100 ms che sveglierebbero `video_sgombra()`.
⇒ **Le due cure non si sommano: la 6 rende la 2 inutile sul gradino.**

### 13.3.2 ⭐⭐ IL CONTROLLO DI §6.5, quello *«che invalida tutto il banco»* — **superato**

`LEZIONI.md` §1.9: un contatore a zero su un ramo mai percorso non dimostra niente. La riga di
`ritmo_ciclo()` risponde, **una al secondo**:

| ora | `arretrato` LETTO | massimo | discese nel secondo | in tutto |
|---|---|---|---|---|
| 13:32:19-27 (larga) | ⭐ **36-42 volte/s** | **0** | **0** | 0 |
| **13:32:28** | 40 | **2** | ⛔ **13** | 13 |
| **13:32:29** | 40 | **2** | ⛔ **17** | 30 |
| **13:32:30** | 38 | **2** | ⛔ **17** | 47 |
| **13:32:31** (ritorno) | 38 | **2** | 10 | **57** |
| 13:32:32-48 (larga) | ⭐ **38-42 volte/s** | **0** | **0** | ⭐ **57, e resta 57** |

⭐⭐ **Le letture ci sono — 36-42 al secondo — e valgono ZERO.** ⇒ Non è *«un anello mai
percorso»* (il rosso **d** di `ritmo_frena()`): è **percorso 40 volte al secondo, e la risposta è
«non c'è niente da fare»**. È esattamente il comportamento che S.5 chiamava *parapetto*.

### 13.3.3 ⭐ DUE RIGHE PER EPISODIO, non una per fotogramma — e il RISALE arriva

`[M]` **5 discese e 5 risalite**, 10 righe in tutto per **57** fotogrammi trattenuti (il difetto dei
30,8 GB di registro non si ripete):

| episodio | durata | fotogrammi restati indietro | `cwnd_left` alla discesa |
|---|---|---|---|
| 1 | 158 ms | 4 | **0** |
| 2 | 841 ms | 16 | 51 466 |
| 3 | 607 ms | 10 | 12 117 |
| 4 | ⚠ **1 385 ms** | 25 | **0** |
| 5 | 68 ms | 2 | 264 318 |

⭐ **Il RISALE dopo il ritorno della linea è dentro il secondo**: l'episodio 4 è cominciato alle
`13:32:30.071`, **dentro** la stretta, e si è chiuso alle `13:32:31.455` — la linea si era riaperta
a `13:32:31.1`, quindi **355 ms dopo**. ⚠ *«durato 1 385 ms»* **non** smentisce *«RISALE entro 1 s»*:
il cronometro giusto parte dal ritorno della linea, non dall'inizio dell'episodio.

⭐ **E il rosso (b) di `ritmo_frena()` — il più importante — NON è caduto**: `cwnd_left` è **0** in
due discese su cinque e piccolo in una terza ⇒ **è la linea a frenare, non la finestra del
browser**. ⚠ L'unica discesa con `cwnd_left` largo (264 318) è la **quinta**, quella da 68 ms,
scattata quando la linea si era già riaperta e `cwnd` stava ricrescendo: coerente.

### 13.3.4 ⚠ IL PREZZO, misurato — **e il numero da portare a lui**

⛔ Il prezzo è quello dichiarato in S.5, e adesso ha una cifra: nei 3 secondi di stretta si vedono
**20-26 fotogrammi/s invece di 21-25** — cioè **praticamente gli stessi**, ma **fatti tutti di
delta**, senza le 18 chiavi. ⭐ In byte, la 100+ritmo consegna nei 3 s **4 349 kbyte** contro i
**3 896** del braccio spento: **più immagine, non meno**.

⚠ **E l'unico numero che si avvicina a un limite**: al secondo 10 si scende a **20 fot/s**, sotto i
25 che `DECISIONI.md` §2.1 chiama pavimento. ⛔ **Non è il difetto che S.5 dichiarava**: quella riga
parla di *«sotto 25/s su una linea da 20 Mbit/s»*, e qui la linea è **10 Mbit/s**, cioè **metà del
pavimento**. ⇒ Va riguardato il giorno in cui si misura a 20.

## 13.4 ⭐⭐⭐ P4 — IL TETTO DI BANDA: **i due rossi che chiudevano la cura NON sono caduti**

**Il giro**: cinque scene a **2560×1080**, 30 s l'una, sessione di `prova2`, `tc` mai toccato.
⛔ **E l'ordine delle scene è parte della misura, ed è stato corretto strada facendo** — vedi 13.4.3.

### 13.4.1 `[M]` I DIECI NUMERI, appaiati — *tetto spento 13:38, tetto 20 alle 13:41*

| scena | ⛔ **tetto SPENTO** | ⭐ **`--tetto-banda-mbit 20`** | |
|---|---|---|---|
| **ferma** (nessuna scena) | 0 fot/s · **0,000** Mbit/s · filo **2,427** | 0 fot/s · **0,000** · filo **2,427** | ⭐ identico al terzo decimale |
| **tinta piatta** (`pieno`) | 41,10 fot/s · **1,151** Mbit/s | 41,23 fot/s · **1,219** | ⚠ **+5,9 %** |
| ⛔⛔ **desktop VERO** (`video`) | 23,13 fot/s · **0,208** = **1,0 %** | 23,13 fot/s · ⭐⭐ **0,249** = **1,2 %** | ⭐⭐⭐ **SALE del 19,7 %, NON scende** |
| ⛔⛔ **gradiente retinato** (`barra`) | 34,67 fot/s · **21,183** = **105,9 %** | ⭐⭐ **40,70** fot/s · ⭐⭐⭐ **8,287** = **41,4 %** | ⭐ **il driver HA obbedito** |
| **film con la grana** | 23,17 fot/s · **54,302** = 271,5 % · filo **58,414 = 292,1 %** | 23,30 fot/s · ⭐ **4,794** = **24,0 %** · filo **7,419 = 37,1 %** | ⭐ da **293 %** a **37 %** |

⭐ **E il metro è buono**: i cinque numeri a tetto spento riproducono §3.8 entro l'1-2 %
(0,208 contro 0,204 · 1,151 contro 1,179 · 21,183 contro 21,36 · 58,414 contro 58,668).

### 13.4.2 ⛔⛔ I DUE ROSSI CHE CHIUDEVANO LA CURA, uno per uno

| il rosso di **P4** | che cosa sarebbe successo | `[M]` |
|---|---|---|
| ⭐⭐ **il desktop vero costa MENO di 0,204** ⇒ *«il tetto risparmia dove non deve, è v1 che si ripete, e questa cura si butta»* | 0,208 → qualcosa sotto 0,204 | ⭐⭐⭐ **NON è caduto**: 0,208 → **0,249**, cioè **+19,7 %**. ⚠ È il **prezzo del QVBR** già previsto (`[M]` sul portatile: *«spende il 13 % in più del CQP a scena ferma»*), misurato qui al **19,7 %** — ⇒ **la cura VIVE** |
| ⭐⭐ **il retinato resta sopra 20** ⇒ *«il driver non ha obbedito, e lo coglie solo il terzo testimone»* | 21,18 → ancora ≥ 20 | ⭐⭐⭐ **NON è caduto**: **8,287** Mbit/s, cioè il **39 %** di prima |

⚠ **E c'è uno scarto dalla previsione che va detto, ed è nel verso opposto a un rosso**: P4 diceva
*«retinato 11-16 · grana 11-16, e MAI sopra 16»*. `[M]` sono usciti **8,287** e **4,794** —
⛔ **sotto la forchetta, non sopra.** ⇒ Il tetto **stringe più del previsto**: il filo è
**16 000 kbit/s** e il caso duro ne usa il **24-62 %**. ⚠ Vuol dire che sul caso duro l'immagine è
più brutta di quanto il tetto obbligherebbe: `[?]` **da tarare**, non un difetto — e **non lo decide
una misura, lo decide l'occhio**.

⭐ **E i fotogrammi non li paga nessuno, anzi**: sul retinato il tetto acceso ne consegna **40,70/s
contro 34,67** — perché fotogrammi più piccoli escono più in fretta.

### 13.4.3 ⭐⭐ I TRE TESTIMONI, letti tutti e tre — *e sono le righe che il prodotto scrive da sé*

| # | la riga, testuale |
|---|---|
| **1** · il driver | `controllo del bitrate su «/dev/dri/renderD128» (Intel iHD driver … 25.2.3), profilo 17, EncSliceLP: il driver DICHIARA [CBR\|VBR\|VCM\|CQP\|MB\|QVBR\|TCBRC] (0x149e) · chiesto QVBR (0x400) · c'e'` |
| **2** · il contesto | `PARAMETRI IN VIGORE (fase 9) … tetto di banda ACCESO (pavimento 20 Mbit/s)` + `codificatore 1 APERTO e TENUTO VIVO … 2560x1080 a 60/s` |
| **3** ⭐⭐ · **i BYTE** | `banda del video: 5581 kbit/s su 10001 ms — 283 fotogrammi …, modo QVBR · TETTO ACCESO: filo 16000 kbit/s, **ne usa il 34 %**` — una riga ogni 10 s |

⭐ **Il terzo è quello che decide, e dice che il tetto è in presa**: nei dieci intervalli letti il
consumo va dall'**1 %** (desktop fermo) al **62 %** del filo, e **non lo supera mai**.

### 13.4.4 ⛔ IL DIFETTO DEL BANCO CHE HO TROVATO E CORRETTO — *e avrebbe dato «un numero plausibile»*

`09-b72-banda.py` `scena()`: quando il punto dopo **non** è un video, **non spegne il Firefox del
punto prima**. ⇒ Col mio primo ordine (`ferma,video,pieno,barra,video-grana`) il punto `pieno` è
stato misurato **col film ancora vivo sotto**. ⛔ È la famiglia di difetti di §8, quarta volta oggi.
⭐ **Rifatto tutto con le scene video IN FONDO** (`ferma,pieno,barra,video,video-grana`): fra due
video ci pensa `09-b72-video.sh`, che fa `pkill`.
⚠ **E l'esito del controllo va detto**: il `pieno` contaminato aveva dato **1,162** Mbit/s, quello
pulito **1,151** — cioè **lo stesso numero**. ⇒ In *questo* caso la contaminazione non ha morso
(la finestra della scena copre il film e Mutter non consegna quel che è nascosto). ⛔ **Ma la misura
buona è quella dell'ordine giusto**, e il banco va corretto: un difetto che non morde oggi morde
domani.

## 13.5 ⛔⛔⛔ IL FATTO CHE RIMETTE IN DISCUSSIONE §3.8, §10.1 E TUTTA LA BOLLETTA: **si stava misurando HEVC**

⭐ Trovato **leggendo il registro del tetto**, non cercandolo. La riga che nessuno aveva guardato:

```
13:41:53.152 rcp   negoziato video.codec=hevc video.profondita=8 audio.codec=pcm
13:41:54.365 video primo fotogramma: hev1.1.6.L150.B0 · … HEVC 8 bit via hevc_vaapi
```

⛔ **`banchi/01-b3-cliente.py` · `--video-codec` dichiara `--video-codec` con predefinito `hevc,av1`**, e il
server sceglie **HEVC**. ⇒ **Tutti i numeri di banda di §3.8 e della prima parte di questa sezione —
0,204 · 1,179 · 21,36 · 58,668 Mbit/s — sono numeri HEVC.**

⛔⛔ **E il prodotto a Firefox Android NON manda HEVC**: `MEMORY.md`, *«AV1 esce, entra H.264 —
Firefox Android non ha né HEVC né AV1; `avc1.640032` è già verificato»*.

### 13.5.1 `[M]` QUANTO CAMBIA — *stessa scena, stessa tela, stesso QP 26, 13:47*

| `barra`, 2560×1080, tetto spento | HEVC | ⭐ **H.264** |
|---|---|---|
| fotogrammi/s | 34,67 | ⭐ **41,80** |
| carico video | **21,183** Mbit/s = **105,9 %** | ⭐⭐ **7,920** Mbit/s = **39,6 %** |
| filo | 24,052 = 120,3 % | ⭐ **10,511** = **52,6 %** |
| byte medi per fotogramma | 61 100 | **23 683** |

⛔⛔ **H.264 costa QUI un terzo di HEVC**, non di più. ⚠ Non è la teoria dei codec: è che **`QP 26`
non vuol dire la stessa qualità nei due**, e sul `hevc_vaapi` di questo driver, a QP 26 e
`EncSliceLP`, esce **molta più roba**. ⇒ ⛔ **La scala della degradazione (26 → 35 → 44 → 51) è
tarata su un numero che nei due codec significa due cose diverse**, e finora è stata provata sul
codec sbagliato.

⇒ ⭐⭐ **La contraddizione §10.1 va riscritta.** *«Ne chiede il 293 %»* è HEVC. Sul codec che il
prodotto manda davvero, la stessa scena dura chiede **il 39,6 %** del pavimento. ⛔ `[?]` **Il caso
duro vero (film con la grana) sotto H.264 NON è stato misurato**: è il primo numero da prendere.

### 13.5.2 ⛔ `[R]` E UN DIFETTO CHE ESCE DALLA STESSA RIGA: **sotto H.264 la stringa per il decodificatore è VUOTA**

```
HEVC   → primo fotogramma: hev1.1.6.L150.B0 …   stringa per il decodificatore «hev1.1.6.L150.B0»
H.264  → primo fotogramma: (non letto)      …   stringa per il decodificatore «»
```

⛔ Sotto H.264 il server **non compone** la stringa `avc1.<profilo><vincoli><livello>` (il commento
che la descrive sta in `codificatore.c:715`), e scrive `(non letto)`. ⚠ **Il livello lo legge lo
stesso** (`livello 51`, poi `52`): manca la **stringa**. `[?]` Se è quella che va al browser, è la
famiglia di R31 — *«non dà un errore di rete, fa rifiutare la configurazione»*.

## 13.6 ⛔⛔⛔ IL 4K — *13:50-13:52*: **41 fotogrammi/s, non 60 — e il livello prodotto SFORA quello del client**

**Il giro**: tela **3840×2160** verificata **nel registro del prodotto** (`TELA NUOVA DAL PALCO:
1920x1080 → 3840x2160`), scena `barra`, 20 s, tetto spento, `tc` mai toccato.

| a 3840×2160 | ⭐ **H.264** (quel che il browser riceve) | HEVC |
|---|---|---|
| **fotogrammi/s** | ⛔ **41,25** | 38,75 |
| carico video | **24,055** Mbit/s = **120,3 %** del pavimento | ⛔ **74,390** = **372,0 %** |
| filo | 26,711 = 133,6 % | ⛔ **78,018** = **390,1 %** |
| byte medi per fotogramma | 72 895 | 239 968 |
| chiavi / abbandoni in 20 s | ⭐ **0 / 0** | ⛔ **19 / 20** |
| ⛔ **LIVELLO PRODOTTO** | ⛔⛔ **5.2** (`level_idc` 52 nell'SPS) | 5.0 (`general_level_idc` 150) |

### 13.6.1 ⛔ LA RISPOSTA ALLA DOMANDA: **il 4K·60 che il prodotto promette non c'è, e il tetto non è la linea**

⭐ **41,25 fot/s con la linea LIBERA** (nessun `tc`, nessuna perdita, zero abbandoni, zero chiavi).
⇒ ⛔ **Non è la banda a fermarlo**: è la catena cattura → conversione → codifica.
`[M]` la riga del primo fotogramma a 4K: **conversione 11 466 µs** + **codifica 8 895 µs** = **20,4
ms per fotogramma**, cioè **un tetto di ~49/s** prima ancora di uscire di casa. ⚠ A 2560×1080 erano
6 652 + 3 827 = 10,5 ms (⇒ ~95/s), e infatti lì si vedono 41,8/s perché comanda il compositore.
⇒ **`DECISIONI.md` va corretto: a 3840×2160 il prodotto regge ~41/s, non 60.**

### 13.6.2 ⛔⛔ E IL ROSSO DI **P9** È CADUTO, con un innesco concreto

```
rcp    il client dichiara video.livello=5.1 … §4.3 vieta al server di emettere un flusso PIU' ALTO
figlio §4.3 — LIVELLO PRODOTTO: 5.2 (nell'SPS e' 52) … il confronto fra le due righe lo fa CHI
       LEGGE — il programma NON lo fa
```

⛔⛔ **Il server ha emesso 5.2 dove il client ammetteva 5.1, e nessuno ha detto niente.** È
esattamente il difetto che §5.5 aveva trovato leggendo il codice (`rcp.c:1823` non cattura il
livello) e che **P9** prevedeva: *«un livello troppo basso non dà un errore di rete: fa rifiutare la
configurazione, cioè schermo che non parte senza un rosso»*. ⭐ Adesso non è più una lettura del
codice: **è successo, alle 13:50:48, e le due righe sono nel registro.**

⚠ **E la stima di §5.5 era sbagliata in un altro modo ancora**: diceva *«a 4K serve il 5.1, che
concede `[?]` 30,3 fot/s»*. `[M]` L'`h264_vaapi` non ha scelto 5.1: **ha scelto 5.2**. ⇒ il numero
da mettere in `pagina.html:829` non è `avc1.640033` (5.1) ma `avc1.640034` (5.2) **se si vuole
davvero il 4K** — ⛔ e va verificato che Firefox Android accetti il 5.2, perché altrimenti la scelta
è **fra il 4K e quel browser**.

## 13.7 ⛔ L'AUDIO — **saltata, e dichiaro perché**: il banco non riesce ad aprire Marionette

⭐ Il banco `banchi/09-b74-audio-firefox.py` (scritto oggi) è **la forma giusta** e risolve il
difetto di §3.16: il *prima* e il *dopo* sono **due file `pagina.html`**, serviti dallo **stesso
binario**, e il verbale è la riga `/diario` che **la pagina manda da sola** al server ogni 5 s.
⭐ E il servizio è partito bene: `pagina: /media/REMOTIX/src/09-src/src/pagina.html ·
md5 d387c166…` per il *prima* — cioè **la pagina VECCHIA, e si vede dall'`md5`**, non dal nome.

⛔ **Ma Firefox non apre mai la porta 2829 di Marionette.** Due tentativi (13:53 e 13:55), più una
diagnosi: **80 s di attesa, la porta non compare mai**. ⇒ Il braccio non parte, e **senza il
braccio «prima» non c'è controllo positivo**: un *dopo* pulito da solo non dimostrerebbe niente.

⚠ **E la diagnosi si è fermata su un difetto del banco dentro il banco**: `b74-ff.log` è creato in
`$LAV`, che è **di root**, mentre Firefox gira come `prova` ⇒ ⛔ **il registro di Firefox è di ZERO
byte**, e quando si chiede *«perché non è partito»* non c'è niente da leggere. È lo **stesso difetto
del `user.js` vuoto** che il commento del banco racconta di aver già pagato alle 12:47, in un altro
punto dello stesso file.

⇒ **La cura 4 (il riordino dell'audio) resta NON VERIFICATA.** ⛔ E resta *«il banco misura se
stesso»* di §3.16, perché `01-b3-cliente.py` ha ancora la sua copia della regola vecchia
(`md5 13e68d19ed44298b7926cded53affdda`, invariato). ⭐ **Ma la strada è corta**: la pagina il
verbale lo manda da sola, quindi **basta che Nic apra la pagina col suo browser** e il registro del
server porta i tre contatori (`vecchi` · `tardivi` · `fuori`). Non serve Marionette per il giudizio:
serve per l'automazione.

## 13.8 ⭐⭐⭐ §10.2 DECISA — **il confine della spirale sta fra 10 e 5 Mbit/s**, e sopra non morde

⛔ La domanda di §10.2 era: *«sopra il pavimento la spirale morde o no?»*, con **due posizioni** in
campo — §5.2 (*«il difetto vive sotto il pavimento, sopra la cura è inerte»*) contro §3.10
(*«abbandoni e chiavi anche sulla linea larga, 3↔3 a 22-26 Mbit/s»*).

**Il giro che la decide**: ⛔ **sul DESKTOP VERO**, non su `barra` — ⭐ e col **codec che il browser
riceve davvero, H.264** (`negoziato video.codec=h264`, letto dal registro). Una **sola** sessione a
2560×1080 per tutti i gradini, così l'unica variabile è la stretta. Soglia e regolatore **spenti**,
cioè il prodotto com'è oggi. Gradino: 8 s larga → **3 s stretti** → 6 s larga.

| la stretta | fotogrammi spediti | ⛔ **CHIAVI** | ⛔ **abbandoni §5.1** |
|---|---|---|---|
| **30 Mbit/s** (150 % del pavimento) | 421 | ⭐ **0** | ⭐ **0** |
| **25 Mbit/s** (125 %) | 429 | ⭐ **0** | ⭐ **0** |
| ⭐ **20 Mbit/s** (**il pavimento**) | 426 | ⭐ **0** | ⭐ **0** |
| **15 Mbit/s** (75 %) | 406 | ⭐ **0** | ⭐ **0** |
| **10 Mbit/s** (50 %) | 426 | ⭐ **0** | ⭐ **0** |
| ⛔ **5 Mbit/s** (25 %) | 424 | ⛔ **3** | ⛔ **3** |

### ⭐ IL VERDETTO, secco

⛔⛔ **Sul contenuto vero la spirale NON esiste fino a 10 Mbit/s compresi**, cioè fino a **metà
pavimento**. Il primo segno arriva a **5 Mbit/s**, ed è **3 chiavi su 424 fotogrammi = lo 0,7 %**.
⇒ **§5.2 aveva ragione e §3.10 misurava un'altra cosa**: i suoi abbandoni a 22-26 Mbit/s erano su
**`barra`**, il gradiente retinato — una scena **sintetica** che a 2560×1080 costa **21 Mbit/s da
sola** (105,9 % del pavimento). ⛔ **Non è il desktop di nessuno**: è un caso di prova che vive
*sopra* il pavimento anche a riposo, e sotto quel carico qualunque stretta produce coda.

⇒ ⭐⭐ **La soglia sulla coda e il regolatore del ritmo sono ROBUSTEZZE, non correzioni di un
difetto che l'utente vede.** Sul suo desktop, a 20 Mbit/s, **non hanno niente da fare** — ed è quel
che P2 e P7 prevedevano. ⚠ Servono quando la linea cala **sotto la metà**, oppure quando il
contenuto è un caso duro (video a schermo intero), e lì lavorano bene: §13.3.

⚠ **Il difetto del mio copione, dichiarato**: la tabella per-secondo che avevo stampato dava
`fot [0,0,0]` in tutt'e sei i giri — un errore mio nel raggruppare per secondo, **non una misura**.
⛔ I numeri qui sopra **non vengono da quella tabella**: vengono dal **conto diretto sui registri
salvati** (`grep -c SPEDITO`, `grep -c 'SPEDITO: CHIAVE'`, `grep -c ABBANDONATO`), che è la
grandezza che il prodotto scrive. ⚠ Se avessi riportato la tabella, avrei detto *«zero fotogrammi»*
dove ce n'erano **424**.

## 13.9 ⭐⭐⭐ IL VERDETTO DELLA SERA — le nove previsioni, una per riga

| # | la previsione | esito | dove |
|---|---|---|---|
| **P1** | il crollo si riproduce; con la cura regge | ⭐⭐⭐ **CONFERMATA, e oltre**: il malato muore al fotogramma **27** (516 782 byte), il curato regge **1 463** fotogrammi fino a **537 063** byte col 5 % di perdita. ⭐ **La pila dal core chiude il `[?]` di §4.8** | 13.1 |
| **P2** | la soglia è **inerte** a 20 Mbit/s | ⭐ **CONFERMATA**, e non solo a 20: sul desktop vero **niente da fare fino a 10 Mbit/s** | 13.2.2 · 13.8 |
| **P3** | sul gradino: chiavi ≤ 2/s, abbandoni ≤ 2/s, fot ≥ 25 | ⛔ **SMENTITA sui due numeri che contavano**: chiavi **4-5/s**, abbandoni **5-9/s**. ⭐ Confermata su inerzia e ritorno. ⛔ **E il rimedio scritto in P3 era nel verso sbagliato** | 13.2.2 · 13.2.3 |
| **P4** | il tetto: desktop vero **non scende**, retinato **sotto il pavimento** | ⭐⭐⭐ **CONFERMATA — i due rossi che buttavano la cura NON sono caduti**: 0,208 → **0,249** (+19,7 %), retinato 21,18 → **8,29**. ⚠ Stringe **più** del previsto (fuori forchetta in basso) | 13.4 |
| **P5** | la risalita della qualità | ⛔ **NON PROVATA** — vedi 13.10 | 13.10 |
| **P6** | il riordino dell'audio | ⛔ **NON PROVATA**: Marionette non apre la porta | 13.7 |
| **P7** | il regolatore: **zero discese** a desktop normale; discese sul gradino, RISALE entro 1 s | ⭐⭐⭐ **CONFERMATA IN PIENO**: `arretrato` **LETTO 36-42 volte/s** sulla linea larga con **massimo 0** e **zero discese**; **57** discese concentrate nei 3 s; RISALE **355 ms** dopo il ritorno. ⛔ E il rosso *«è la finestra del browser»* **non è caduto**: `cwnd_left` = 0 | 13.3 |
| **P8** | a scena ferma il ritmo non cala | ⚠ **NON misurata a coppie** (mezza ferma / mezza mossa). ⭐ Ma la metà del controllo c'è: le righe `arretrato LETTO N volte` esistono e distinguono *vuoto* da *proibito* | 13.3.2 |
| **P9** | il livello prodotto contro quello del client, e nessuno li confronta | ⛔⛔ **CADUTA, con l'innesco**: a 4K H.264 il server emette **5.2** mentre il client dichiara **5.1**, e **il programma non se ne accorge** | 13.6.2 |

### ⭐⭐ E LE TRE COSE NUOVE, che nessuna previsione aveva previsto

1. ⛔⛔⛔ **Si stava misurando HEVC.** Il cliente di prova negozia `hevc`, il prodotto manda H.264 a
   Firefox. Stessa scena: **21,18** Mbit/s in HEVC contro **7,92** in H.264 — ⇒ **§10.1 va
   riscritta e la bolletta rifatta** — 13.5;
2. ⭐⭐⭐ **La soglia non è un filtro: è il punto di lavoro della coda.** A 100 ms la coda si assesta
   a 101-138; a 200 ms a 204-236. ⇒ alzarla **compra immagine e paga ritardo**, e non cambia il
   numero degli abbandoni — 13.2.3;
3. ⭐⭐⭐ **Il regolatore rende la soglia inutile sul gradino**: tiene `arretrato` a 2, la coda non
   arriva mai ai 100 ms, e `video_sgombra()` **non scatta nemmeno una volta** — 13.3.1.

## 13.10 ⛔ `--qualita-risale` — **non l'ho fatta scattare, e dichiaro perché**

⭐ **Non è un tentativo fallito: è un esito, e si legge nel codice prima che sul ferro.** La riga che
il prodotto scrive da sé a ogni apertura del codificatore:

```
la risalita della qualita' e' SPENTA (invariante I6) … da spenta questi numeri
(120 fotogrammi, 2097152 byte, scalino 9, punto di lavoro QP 26 costante, tetto d'attesa 3840)
non hanno nessun effetto
```

⛔ **`2 097 152` byte = 2 MiB è la soglia che fa SCENDERE la qualità.** Perché la risalita abbia
qualcosa da risalire, la qualità deve prima essere scesa, cioè serve un fotogramma **sopra i 2 MiB**.
`[M]` di stasera, il fotogramma **più grosso mai visto in tutta la giornata**: **537 063 byte** — un
**quarto** della soglia, e su un **film con la grana a schermo intero**, che è il caso più duro che
questa fase abbia. A 4K HEVC la media è **239 968** byte, la punta resta lontana.
⇒ ⛔ **Sulla tela dell'utente non succede mai**, ed è la stessa cosa che §5.3 aveva scritto.

⚠ **La strada per farla scattare c'è ed è quella dichiarata nel mandato** — tela enorme + ripiego
software (`h264_vaapi` si ferma a 4096 px per lato) — ⛔ **ma è un giro che non misura il prodotto**:
misurerebbe il codificatore software su una tela che nessun utente ha. ⇒ **Non l'ho fatto**, e la
cura 3 resta **non verificata sul ferro**. ⭐ Quel che è verificato è che **è spenta e lo dice**, e
che da spenta **non tocca niente**: i numeri del confronto appaiato di §3-bis lo mostravano già.

## 13.11 ⭐ COM'È RIMASTA LA MACCHINA — *verificato alle 14:01 UTC, non dichiarato a memoria*

| | |
|---|---|
| `tc` su **`lo`** | ⭐ `qdisc noqueue 0: root` — **nessuna disciplina** |
| `tc` su **`enp7s0`** | ⭐ `qdisc mq 0: root` — **mai toccata**, come da regola |
| il **guardiano** di `tc` | ⭐ nessuno: `.b68-guardiano.pid` non c'è |
| **scene, clienti, browser** | ⭐ **nessuno** — né `04-b30-scena`, né `01-b3-cliente`, né `firefox` |
| **`core_pattern`** | `/media/REMOTIX/tmp/09c/core.%e.%p.%t` — ⚠ **era già così prima che cominciassi** (`core_pattern.prima` dice lo stesso), ed è quel che §4.7 punto 1 chiedeva: **assoluto**. ⛔ Non è il valore di fabbrica (`core`): **lo lascio**, perché è la trappola armata, ⚠ e lo dichiaro perché è uno stato della macchina, non del progetto |

**Le tre porte che restano accese, e perché:**

| porta | albero | perché resta |
|---|---|---|
| **7900** | `09-src` | ⭐ il **PRIMA** di stamattina — il termine di paragone di §3-bis. ⛔ Spegnerlo renderebbe non ripetibili tutte le misure appaiate già scritte |
| **7910** | `09b-src` | le tre cure del mattino, l'altra metà dello stesso confronto |
| **7920** | `09c-src` (`remotix md5 162d2d105cbe930e7921a7041053f5e7`) | ⭐ il **curato di stasera**, ricostruito da `f90eb21`, **senza nessun interruttore acceso** e con la **trappola glibc spenta** — cioè il prodotto com'è |

⭐ **E il corpo del reato si conserva**: `/media/REMOTIX/tmp/09c/core.remotix.110832.1787493803`,
**48 525 312 byte** — il core del binario malato. ⛔ **Non si cancella**: è la prova *vista* del
crollo del 23 agosto. ⚠ **E non è quello di 13.1.1**: vedi 13.1.5 qui sotto, che racconta perché.

---

# §14 · ⛔⛔⛔ IL METRO CAMBIATO — *23 agosto 2026, sera tardi*

> ⛔⛔ **HO CAMBIATO IL METRO, E LO DICO PRIMA DEI NUMERI.**
> Fino alle 14:22 di oggi ogni giro di banco di questa fase ha misurato **HEVC**; da qui in giù
> misura **H.264**, che è il codec che il browser dell'utente riceve davvero. ⇒ ⛔ **I numeri di
> banda di §3.8, §3.15, §13.4 e §13.5 non si confrontano con quelli di §14.** Sono due scale.
> ⭐ Il vecchio metro si rifà quando serve: `--video-codec hevc`.

## 14.1 ⭐⭐ LA CURA DEL CLIENTE DI PROVA — e **come lo decide il browser vero**, verificato

### La riga cambiata

`banchi/01-b3-cliente.py` — il predefinito di `--video-codec` era **`hevc,av1`**, adesso è
**`h264`**. ⛔ **La causa non è una svista di stasera: è una riga rimasta indietro di tre giorni.**
Il 20 agosto AV1 è uscito dal prodotto (`DECISIONI.md` §1.13-ter) e il cliente di prova ha
continuato a dichiarare `hevc,av1` — ⇒ il server sceglieva **HEVC** in ogni giro, per tre giorni.

### ⛔ E LO DECIDE IL BROWSER? — verificato, non assunto

⭐ `pagina.html` **non** chiede il codec alle API, e lo dichiara in testa al file: `[M]` 12 agosto,
su tutte e sette le stringhe HEVC `mediaCapabilities.decodingInfo()` e `canPlayType()` dicono di
**sì** e il pixel non arriva. ⇒ La pagina **dipinge una sonda vera e rilegge i pixel**, e nel `CIAO`
ci finisce solo quel che ha dipinto:

```
pagina.html:818   const PREFERENZA = ["hevc", "h264"];        ⛔ AV1 non c'è più
pagina.html:4672  const codec_buoni = PREFERENZA.filter((n) => …sondaggio…arriva);
pagina.html:4725  ["video.codec", codec_buoni.join(",")]
```

⇒ **Su Firefox HEVC non dipinge ⇒ la pagina manda `video.codec=h264` e basta.** Il predefinito
nuovo del cliente è **esattamente quello**, non un'approssimazione.

### `[M]` LA PROVA CHE IL METRO È CAMBIATO — *14:22:06-07 UTC*, righe testuali dal registro

```
14:22:06.637 rcp     negoziato video.codec=h264 video.profondita=8 audio.codec=pcm
14:22:07.782 video   primo fotogramma: (non letto) · 25450 byte · … livello 51, 2560x1080 ·
                     conversione 6308 µs, … codifica 3815 µs · H.264 8 bit via h264_vaapi
```

⚠ Il giro delle 14:03, con lo stesso binario e il cliente vecchio, diceva
`hev1.1.6.L150.B0 … HEVC 8 bit via hevc_vaapi`. **Stesso server, stesso minuto, due codec.**

### 14.1.1 ⛔ LA STRINGA VUOTA — **è un difetto del PRODOTTO, non del banco**, e vale meno di quanto sembrava

`[R]` di §13.5.2 verificato riga per riga sull'albero congelato `09c-src`:

```
codificatore.c:953   snprintf(c->stringa_codec, …, "hev1.%s%u.%X.%c%u%s", …)   ← HEVC
codificatore.c:1152  snprintf(c->stringa_codec, …, "av01.%u.%02u%c.%02d", …)   ← AV1 (codice morto)
                     ⛔ e per H.264 NON C'E' NESSUNA RIGA: `avc1.` non si compone da nessuna parte
codificatore.c:4065  c->conf.stringa_codec[0] ? … : "(non letto)"
```

⇒ ⛔ **Difetto del prodotto**: `stringa_codec` non viene mai composta sotto H.264, e il registro
scrive `(non letto)` e `«»`.

⭐⭐ **Ma NON è la famiglia di R31, e questo cambia la sua gravità.** L'unico uso di
`stringa_codec` fuori dal codificatore è `figlio.c:4735` e `:4780`, e sono **due righe di
registro**: la stringa **non parte mai verso il browser**. Quella che il browser usa davvero se la
compone la pagina da sé, dal livello che **lei** dichiara:

```
pagina.html:1182   return ["avc1.6400" + esa(idc), "avc1.64001f"];   /* idc da LIVELLO_DICHIARATO */
```

⇒ ⭐ **Il difetto è una CECITÀ DELLA DIAGNOSI, non uno schermo nero**: sotto H.264 il registro non
sa dire quale stringa servirebbe, e chi legge non può confrontarla con quella che la pagina
manda. ⛔ **E la cecità morde proprio dove serve**: a 4K il server produce il livello **5.2**
(§13.6.2) mentre la pagina configura `avc1.640033`, cioè **5.1** — e la riga che avrebbe reso
visibile lo scarto è quella vuota.

## 14.2 ⭐⭐⭐ LE CINQUE SCENE A 2560×1080 IN H.264 — *14:23:08 → 14:26:26 UTC*

**Il giro**: porta **7920**, binario `md5 162d2d10…` (`f90eb21`, nessun interruttore, trappola
glibc spenta), utente **`prova2`**, tela **2560×1080**, **una sola sessione** per tutti e cinque i
punti — così l'unica variabile è la scena. Tetto **spento**, `tc` **mai toccato** (`lo` verificata
`noqueue` prima e dopo, `enp7s0` mai sfiorata). 30 s per punto.

| scena | ora | fot/s | ⭐ **carico video H.264** | % di 20 | filo `lo` | byte/fotogramma | chiavi | abbandoni |
|---|---|---|---|---|---|---|---|---|
| **ferma** (nessuna scena) | 14:23:08 | 0,00 | **0,000** Mbit/s | 0 % | 2,427 | — | 0 | 0 |
| ⭐ **desktop VERO** (`scena-utente.webm` a schermo intero) | 14:23:52 | 23,10 | **0,356** Mbit/s | **1,8 %** | 2,842 | 1 924 | 0 | 0 |
| **tinta piatta** (`pieno`) | 14:24:31 | 41,03 | **1,190** Mbit/s | 5,9 % | 3,717 | 3 624 | 0 | 0 |
| **gradiente retinato** (`barra`) | 14:25:10 | 40,77 | **7,728** Mbit/s | 38,6 % | 10,45 | 23 695 | 0 | 0 |
| ⛔ **film con la GRANA** (il caso duro) | 14:25:55 | 23,30 | ⛔ **44,574** Mbit/s | ⛔ **222,9 %** | 48,42 | 239 129 | 0 | 0 |

### ⛔⭐ LA RISPOSTA ALLA DOMANDA CHE DECIDE

> **Il caso duro in H.264 supera i 20 Mbit/s?** ⇒ ⛔ **SÌ. 44,574 Mbit/s, cioè 2,2 volte il
> pavimento.**

### `[M]` I DUE METRI AFFIANCATI — e la distanza **non** è un fattore costante

| a 2560×1080, tetto spento | HEVC (§3.8, mattina) | ⭐ **H.264** (14:2x) | rapporto |
|---|---|---|---|
| ferma | 0 | 0 | — |
| desktop vero | 0,204 | ⚠ **0,356** | ⛔ **1,7× in SU** |
| tinta piatta | 1,179 | 1,190 | 1,01× |
| gradiente retinato | 21,36 | ⭐ **7,728** | **0,36×** |
| film con la grana | 58,668 | **44,574** | **0,76×** |

⛔⛔ **E questa riga è il fatto nuovo della tabella**: H.264 **non** costa «un terzo di HEVC», come
§13.5.1 lasciava credere misurando una scena sola. Costa **il 36 %** sul gradiente retinato, il
**76 %** sul film con la grana e ⛔ **il 170 %** — cioè **di più** — sul desktop vero.
⇒ ⭐ **Il rapporto fra i due codec dipende dal CONTENUTO**, ed è la stessa lezione di §3.8 («quanti
pixel cambiano non predice niente») applicata al codec. ⚠ Un fattore di conversione da HEVC a
H.264 **non esiste**: i numeri vecchi non si convertono, si **rifanno**.

### ⭐ Il controllo positivo, e sta dentro la tabella

I cinque punti coprono **tre ordini di grandezza** (0 → 0,356 → 1,19 → 7,73 → 44,57): se il banco
fosse cieco darebbero lo stesso numero. ⭐ E `barra` ritrovato a **7,728** contro i **7,920** di
§13.5.1, preso trentacinque minuti prima con un'altra sessione: **2,4 % di scarto**, cioè la misura
si ripete.
⚠ **La riga `ferma` dice un'altra cosa che vale la pena leggere**: **zero** video e **2,427
Mbit/s sul filo**. ⇒ A desktop fermo il **100 %** di quel che passa è QUIC + **l'audio PCM**, che da
solo chiede 1,536 Mbit/s. `[?]` **A linea stretta è l'audio a mangiare il video, non il contrario** —
vedi 14.4.1, dove a 3 Mbit/s il video scende a 5 fot/s e il filo resta a 2,4.

## 14.3 ⭐⭐⭐ §10.1 RIFATTA COL NUMERO GIUSTO — la contraddizione **non cade, si dimezza**

§10.1 metteva a confronto due frasi: lo studio diceva *«non serve nessun tetto»* sul contenuto vero,
la misura diceva *«293 % del pavimento»* sul caso duro. ⛔ Erano tutt'e due **numeri HEVC**.

| | HEVC (quel che diceva §10.1) | ⭐ **H.264** (quel che l'utente riceve) |
|---|---|---|
| il **contenuto vero** dell'utente | 0,204 Mbit/s = **1,0 %** | **0,356** Mbit/s = **1,8 %** |
| il **caso duro** (film con la grana) | 58,668 = **293 %** | ⛔ **44,574** = **223 %** |
| la distanza fra i due | **288×** | **125×** |

### ⭐ LA CONCLUSIONE, col numero e non con l'opinione

1. ⭐ **La prima frase regge, e regge meglio di prima**: sul desktop vero il prodotto chiede
   **l'1,8 % del pavimento**. Un tetto a 20 Mbit/s lì **non ha niente da fare**, e §13.4 l'ha già
   misurato (0,208 → 0,249, e la cura non è caduta);
2. ⛔ **La seconda frase regge anche lei, e il cambio di codec NON la salva**: il caso duro chiede
   **223 %** invece di 293 %. ⇒ ⛔ **Passare a H.264 toglie 70 punti percentuali e lascia il
   problema in piedi**: 44,6 contro 20 è ancora **più del doppio**;
3. ⇒ ⭐⭐ **LA CONTRADDIZIONE NON ERA UNA CONTRADDIZIONE, ed è deciso**: le due frasi parlano di due
   contenuti diversi, e tutt'e due sono vere **sullo stesso codec**. **Il tetto serve, e serve solo
   per il caso duro** — cioè è esattamente quel che §5.5 aveva progettato: un parapetto che sul
   desktop vero non si accorge di esistere.
   ⛔ **E chi volesse buttare il tetto adesso deve rispondere a questa riga**: *con quale numero il
   film a schermo intero sta dentro i 20 Mbit/s senza di lui?*

## 14.4 ⛔⭐⭐ LA SOGLIA SULLA CODA, tarata nel verso giusto — *14:27 → 14:35 UTC*

### 14.4.1 ⛔⛔ IL BANCO CHIESTO NON HA UN CONTROLLO POSITIVO, e lo dico prima dei numeri

Il mandato chiedeva lo spazzamento **sul desktop vero**, e ha ragione: `barra` è sintetico.
⛔ **Ma sul desktop vero non c'è niente da tarare, e l'ho misurato invece di dedurlo.**

`[M]` **14:27:48**, gradino sul desktop vero in H.264, soglia **spenta**, stretta a **3 Mbit/s** —
cioè **un terzo** di quel che §13.8 aveva già provato a 10:

| s | 5-7 (larga) | **8** | **9** | **10** | **11** | 13-25 (larga) |
|---|---|---|---|---|---|---|
| fotogrammi | 29 | 21 | 13 | **5** | 5 | 27-29 |
| ⛔ **chiavi** | 0 | **0** | **0** | **0** | **0** | 0 |
| ⛔ **abbandoni** | 0 | **0** | **0** | **0** | **0** | 0 |

⇒ ⭐⭐ **A 3 Mbit/s — il 15 % del pavimento — sul desktop vero il ritmo crolla da 29 a 5 fot/s e
la spirale NON PARTE LO STESSO: zero chiavi, zero abbandoni.** §13.8 si fermava a 5 Mbit/s e ne
trovava 3; qui, più in basso ancora, ce ne sono **zero**.
⇒ ⛔ **Uno spazzamento della soglia su questa scena misurerebbe zero contro zero contro zero**, cioè
niente. Il banco non ha lo stimolo, e un banco senza stimolo dà *«la cura funziona»* per ogni
valore. **Non l'ho fatto lì.**

⭐ **E c'è un secondo motivo, e viene dal metro nuovo**: l'obiezione di §13.8 contro `barra`
(*«a 2560×1080 costa 21 Mbit/s da sola, non è il desktop di nessuno»*) era un'obiezione **HEVC**.
In H.264 `barra` costa **7,73 Mbit/s** (14.2), cioè il 39 % del pavimento. ⚠ Ma il caso che
**chiede** la cura è un altro, ed è quello vero: il **film con la grana**, 44,6 Mbit/s.

### 14.4.2 `[M]` LO SPAZZAMENTO, sul CASO DURO — film con la grana, 2560×1080, H.264

**Il giro**, identico sei volte: 8 s larga → **3 s a 10 Mbit/s** → 17 s larga, `tc` solo su `lo`
e solo sulla 7920, guardiano armato, `enp7s0` mai toccata (verificato dopo ogni braccio).
Server riavviato a ogni braccio, `md5 162d2d10…`, trappola glibc spenta. Le righe qui sotto sono
**i 3 secondi di stretta**, e i millisecondi sono quelli che il prodotto scrive da sé nella riga
*«la coda del video passa SOPRA la soglia (… byte = N ms …)»*.

| braccio | ora | fot/s nei 3 s | ⛔ chiavi | ⛔ abbandoni | kbyte | attrav. | ⚠ **ms di coda pagati** | `arretrato` max |
|---|---|---|---|---|---|---|---|---|
| **spenta** | 14:29 | 6,0 | **8** | **8** | 6 111 | — | — | 0-1 per costruzione |
| **100 ms** | 14:30 | 6,7 | 8 | 10 | 6 507 | 8 | **136 – 397** | 3 |
| **200 ms** | 14:31 | 7,7 | 8 | 14 | 7 216 | 8 | **222 – 942** | 6 |
| **400 ms** | 14:32 | 5,7 | 6 | 8 | 5 930 | 7 | **414 – 643** | 8 |
| **800 ms** | 14:33 | 7,3 | **5** | 14 | 6 738 | 6 | ⛔ **856 – 1 321** | 7 |
| ⭐ **200 + `--ritmo-adattivo`** | 14:34 | 5,3 | 6 | ⭐ **6** | 5 521 | 7 | ⭐ **209 – 323** | ⭐ **2** |

### ⭐ LA COPPIA CHE L'UTENTE DEVE GIUDICARE, e la risposta secca

> **A quale valore la soglia mantiene la promessa di P3, e a che prezzo in ms?**
> ⇒ ⛔ **NESSUNO. Da sola non ci arriva a nessun valore.** P3 chiedeva *chiavi ≤ 2/s*,
> *abbandoni ≤ 2/s* e *fot ≥ 25/s*: ⭐ le chiavi scendono nella promessa a **400 ms** (2,0/s) e a
> **800** (1,7/s), ⛔ gli **abbandoni non ci arrivano a nessun valore** (2,7 – 4,7/s), e ⛔ i
> **fotogrammi non ci si avvicinano nemmeno** (5,3 – 7,7/s contro 25).
> ⭐⭐ **L'unico braccio che porta gli abbandoni dentro la promessa è la COPPIA**
> `--sgombra-soglia-ms 200 --ritmo-adattivo`: **6 abbandoni in 3 s = 2,0/s**, e li paga con
> **209-323 ms** di coda, cioè **~264-378 ms dal gesto al pixel** sommando i 55 ms dell'anello di
> fase 8.

### ⛔⛔ E TRE COSE CHE SMENTISCONO QUEL CHE §13.2.4 AVEVA CONCLUSO

1. ⛔ **«Il miglioramento è monòtono» NON regge sul caso duro.** Le chiavi calano piano
   (8 · 8 · 8 · 6 · 5) ma gli **abbandoni ballano** (8 · 10 · 14 · 8 · 14) e i fotogrammi pure
   (6,0 · 6,7 · 7,7 · 5,7 · 7,3). ⚠ Un solo giro per braccio: **una differenza di una o due chiavi
   è dentro il rumore, e non la riporto come un effetto.** Quel che è **fuori** dal rumore è una
   cosa sola, ed è il prezzo;
2. ⛔⛔ **IL PREZZO CRESCE PIÙ IN FRETTA DI QUEL CHE COMPRA, e a 800 ms è fuori scala**:
   397 → 942 → 643 → **1 321 ms**. ⭐ Il punto di lavoro di §13.2.4 è confermato una seconda volta e
   su un'altra scena (la coda si assesta **appena sopra** la soglia, qualunque numero si scelga) —
   ⛔ ma la conseguenza è che **alzare la soglia compra 3 chiavi e vende un secondo e tre decimi di
   ritardo.** ⇒ **Il verso «alzala» di §13.2.3 è giusto solo fino a ~200-400 ms**: sopra, il
   commercio è quello che `SPECIFICHE.md` §3.2 vieta in una riga;
3. ⭐⭐⭐ **E IL REGOLATORE È LA LEVA, NON LA SOGLIA.** `arretrato` massimo: **3 · 6 · 8 · 7** con la
   sola soglia, ⭐ **2** con la coppia — cioè `WT_RITMO_POSTI = 2` **tiene**, e la coda smette di
   approfondirsi. ⇒ Alla stessa soglia di 200 ms, accendere il regolatore **dimezza gli abbandoni
   (14 → 6)** e **taglia il ritardo di massimo da 942 a 323 ms**. ⛔ **La soglia da sola non è la
   leva giusta; la coppia sì**, ed è quel che il mandato sospettava.

⚠ **Il rosso di §2 del mandato resta in piedi e lo dichiaro**: se il ritardo dell'anello superasse
55 ms + la soglia, la stima dello svuotamento sottostima. `[M]` qui la coda misurata arriva a
**1 321 ms** contro una soglia di 800: ⇒ ⛔ **a 800 ms la stima È già fuori dal suo campo di
validità**, ed è una ragione in più per non salire lì.

## 14.5 ⭐⭐⭐ P8 — IL RITMO A SCENA FERMA, A COPPIE: **VERDE** — *14:40:00 → 14:41:00 UTC*

**Il giro**: `banchi/09-b75-p8.py` (nuovo), porta 7920 con **tutt'e due gli interruttori**
(`--sgombra-soglia-ms 100 --ritmo-adattivo`, letti dalla riga d'avvio del prodotto, non dedotti dal
comando), tela 2560×1080, H.264, linea **larga**, **tre coppie** ferma/mossa da 8 s **alternate
nello stesso giro**. Il verbale è la riga che `ritmo_ciclo()` scrive **col battito e non coi
fotogrammi**, una al secondo.

| | secondi | ⭐ **`arretrato` LETTO** | secondi con **ZERO** letture | massimo | ⛔ **discese** |
|---|---|---|---|---|---|
| ⛔ **metà FERMA** | 16 | **0 in tutto** | ⭐ **16 su 16** | 0 | ⭐ **0** |
| ⭐ **metà MOSSA** | 27 | **1 072** = **39,7 al secondo** | ⭐ **0 su 27** | 0 | ⭐ **0** |

⇒ ⭐⭐⭐ **VERDE, e sui due punti insieme**: nella metà ferma il ramo **non è stato percorso**
(«LETTO 0 volte», 16 righe su 16) e il ritmo **non è sceso**; nella metà mossa l'anello è stato
percorso **1 072 volte** e il ritmo **non è sceso lo stesso**.
⛔ **E questo è quel che «il contatore è zero» non poteva dire**: le due metà danno lo stesso zero
di discese, e le righe `LETTO` dicono che **una l'ha guadagnato e l'altra no**. Vuoto e proibito
sono distinti, che è tutto il punto di P8.

⭐ **E `massimo 0` nella metà mossa è il secondo fatto**: su linea larga `arretrato` non arriva
neanche a 1. ⇒ Il regolatore è **un parapetto che non tocca niente**, com'era previsto (P7, S.5).

### ⛔ DUE DIFETTI DEL BANCO TROVATI STRADA FACENDO — e tutt'e due davano «un numero plausibile»

1. ⛔ **La tappa «mossa» era segnata DOPO l'accensione.** `09-b68-scena.sh` lancia la scena e poi
   **dorme 2 s** per verificare che sia viva: quei 2,3 secondi, in cui la scena **dipinge già**,
   finivano nella metà **ferma**. `[M]` 14:37 — la metà ferma usciva con **26 righe invece di 18** e
   **147 letture**, e il banco diceva **GIALLO su un giro sano**;
2. ⛔ **Il primo secondo dopo la morte della scena porta ancora 22-40 letture.** Non è il prodotto
   che non si ferma: **uccidere il processo della scena non ferma Mutter**, e i fotogrammi già
   composti continuano ad arrivare per circa un secondo. ⇒ Si butta **2,5 s di guardia** dopo ogni
   cambio, **e si dichiara**: contarli da una parte o dall'altra sarebbe attribuire al prodotto un
   transitorio del compositore. ⚠ **E la guardia non può nascondere il rosso che conta**: una
   discesa a scena ferma cadrebbe nei secondi **centrali**, non sul bordo.

## 14.6 ⭐⭐ IL 4K IN H.264 — *14:45:42 → 14:48:15 UTC*: **il numero che mancava, e il tetto SI MUOVE**

**Il giro**: stessa 7920, stesso binario, **nessun interruttore**, tela **3840×2160** verificata nel
registro del prodotto (`SESSIONE: stato=1 tela=3840x2160`), `tc` mai toccato, 30 s per punto,
una sola sessione.

| a **3840×2160**, H.264, tetto spento | fot/s | ⭐ **carico video** | % di 20 | filo | byte/fotogramma | chiavi | abb. |
|---|---|---|---|---|---|---|---|
| ⭐ **desktop VERO** | 23,10 | **0,852** Mbit/s | ⭐ **4,3 %** | 3,351 | 4 607 | 0 | 0 |
| **tinta piatta** (`pieno`) | ⚠ **33,37** | 2,716 | 13,6 % | 5,259 | 10 174 | 0 | 0 |
| **gradiente retinato** (`barra`) | **40,40** | 23,564 | **117,8 %** | 26,641 | 72 908 | 0 | 0 |
| ⛔ **film con la GRANA** | 23,27 | ⛔ **74,699** | ⛔ **373,5 %** | 79,279 | 401 320 | ⛔ **2** | ⛔ **2** |

### ⭐ 1. IL TETTO DEI 41 FOT/S **SI MUOVE CON LA SCENA** — e §13.6 non poteva vederlo

§13.6 aveva misurato **41,25 fot/s** su `barra` e ne aveva concluso *«a 3840×2160 il prodotto regge
~41/s»*. ⭐ Con quattro scene invece di una si vede che **non è un tetto, è un punto**: `barra`
**40,40**, ⚠ `pieno` **33,37** — cioè **7 fotogrammi in meno su una scena che costa NOVE VOLTE
MENO banda** (2,7 contro 23,6 Mbit/s).
⇒ ⛔ **Non è la banda a decidere il ritmo a 4K**, e non è neanche il costo della codifica: è quel
che **il compositore consegna**, ed è la stessa lezione di §3.1. ⚠ I due punti `video` (23,1 e
23,27) **non dicono niente sul tetto**: è il filmato stesso che gira a ~23/s.
⇒ **`DECISIONI.md` va corretto così**: a 3840×2160 il prodotto regge **33-41 fot/s a seconda della
scena**, non 60 e nemmeno «41».

### ⭐ 2. QUANTO COSTA IL 4K, e cresce **quasi coi pixel** (ma non sul caso duro)

I pixel a 4K sono **3,0×** quelli di 2560×1080. `[M]` la banda:

| scena | 2560×1080 | 3840×2160 | rapporto |
|---|---|---|---|
| desktop vero | 0,356 | 0,852 | **2,4×** |
| tinta piatta | 1,190 | 2,716 | **2,3×** |
| gradiente retinato | 7,728 | 23,564 | **3,05×** |
| ⛔ film con la grana | 44,574 | 74,699 | ⚠ **1,68×** |

⭐ **La riga che conta per l'utente**: a **4K** il suo desktop vero costa **0,852 Mbit/s, il 4,3 %
del pavimento**. ⇒ ⛔ **Il 4K non è un problema di banda**: è un problema di **fotogrammi**.
⚠ E il caso duro cresce **meno** degli altri (1,68× invece di 3×) perché a 2560 era **già** al
limite di quel che la catena riesce a produrre.

### ⛔ 3. IL PRIMO SEGNO DI CEDIMENTO SU LINEA LIBERA

Il film con la grana a 4K è l'**unico** punto di tutta la sera che ha prodotto **chiavi e abbandoni
con `tc` mai toccato**: 2 chiavi, 2 abbandoni, 1 chiave trattenuta da §5.2 in 30 s.
⇒ ⭐ A **79,3 Mbit/s sul filo** la coda comincia a non svuotarsi **anche senza nessuna
strozzatura**. ⚠ È il punto in cui «linea larga» smette di essere larga.

### ⛔⛔ 4. E P9 SI RIPRODUCE COL METRO NUOVO — *14:42:50-51*, due righe a un secondo di distanza

```
14:42:50.068 rcp     il client dichiara video.livello=5.1 … §4.3 vieta al server di emettere
                     un flusso PIU' ALTO di questo
14:42:51.328 figlio  §4.3 — LIVELLO PRODOTTO: 5.2 (nell'SPS e' 52) · stringa per il
                     decodificatore «»
```

⛔ **Il server emette 5.2 dove il client ammette 5.1, e il programma non se ne accorge** — §13.6.2
non era un caso del giro di allora: si ripete **ogni volta** che la tela è 4K.
⚠ `[M]` conversione **11 941 µs** + codifica **8 924 µs** = **20,9 ms** per fotogramma ⇒ un tetto
di **~48/s** prima di uscire di casa, e i 40,40 di `barra` ci stanno sotto.

## 14.7 ⛔ L'AUDIO — **ancora NON verificata**, ma la causa di due sere è trovata e curata

⭐ **§13.7 accusava il browser, e sbagliava imputato.** La riga che chiude il caso, `[M]` 23 agosto
**14:49**, col registro creato **prima**, con l'uid giusto e i permessi giusti:

```
⛔ Marionette non ha aperto la 2829 in 40 s.
   firefox vivo? ⛔ NESSUN PROCESSO
   il suo registro (/tmp/b74-ff.log): ⛔ VUOTO
```

⇒ ⛔⛔ **Non era Marionette a non aprire la porta: era Firefox a non partire affatto.**

### ⛔ 14.7.1 LA CAUSA, e sono TRE difetti in fila — due miei, uno del sistema

1. ⛔⛔ **Il lanciatore era una riga di comando invece di un file.**
   `root("bash -c \"setsid nohup setpriv … firefox … &\"")`: `bash -c` mette il lavoro in
   sottofondo ed **esce nello stesso istante**, `sudo` esce dietro di lui e `ssh` chiude la
   sessione — il processo **muore nella corsa** prima che `setsid` l'abbia staccato.
   ⭐ **Curato**: `banchi/09-b74-ff.sh`, la stessa forma di `09-b72-video.sh` che funziona dal
   mattino — un **FILE**, e il padre resta vivo mentre il figlio si stacca. ⚠ È la terza volta
   oggi che la cura è *«un copione lungo si spedisce come file»*;
2. ⛔ **`fs.protected_regular = 2`** (verificato con `sysctl`): in una cartella **sticky** come
   `/tmp`, **nemmeno root** può aprire in scrittura un file **world-writable** che appartiene a un
   altro utente — ed era esattamente quel che il tentativo precedente aveva lasciato lì.
   `[M]` `cannot create /tmp/b74-ff.log: Permission denied` **da root**.
   ⭐ **Curato**: si **cancella** e si ricrea (il permesso è della cartella, non del file);
3. ⛔ **E adesso Firefox parte, resta vivo — e la prova NON si chiude lo stesso.** `[M]` 14:52:
   `firefox-esr 140.14.0esr`, tre processi vivi con `--profile /tmp/b74-ff --marionette`,
   `MOZ_MARIONETTE=1` **letto da `/proc/PID/environ`**, `marionette.port = 2829` in un `user.js`
   di **487 byte** — e ⛔ **`ss -tlnp` non mostra NESSUN socket in ascolto del processo Firefox**,
   né sulla 2829 né sulla 2828.

### ⛔⛔ 14.7.2 E C'È UN SECONDO MURO DIETRO IL PRIMO, che il registro del prodotto dimostra

Nel registro della 7920 **non c'è nessuna richiesta della pagina da parte del browser**: dopo
`ascolto TCP su 0.0.0.0:7920` l'unica stretta di mano è quella del cliente di prova.
⇒ ⛔ **Firefox non ha mai chiesto la pagina.** Il certificato è **autofirmato**, e senza
`acceptInsecureCerts` — che è una funzione **di Marionette** — il browser si ferma
all'avviso e non emette la richiesta.

⇒ ⛔ **I due muri sono lo stesso muro**: senza Marionette non si accetta il certificato, e senza
certificato accettato non c'è pagina. **Mi fermo qui e lo dichiaro**, come dice la regola: due
tentativi, poi si passa.

### ⭐ CHE COSA RESTA DA FARE, e la strada corta non ha bisogno di Marionette

⭐ **La forma del banco è giusta e adesso è anche dimostrata**: il *prima* e il *dopo* sono **due
file `pagina.html`** serviti dallo **stesso binario** (`md5 162d2d10…`), e il `md5` della pagina si
legge nel registro (`d387c166…` per il vecchio, `e010d615…` per il nuovo). Il verbale lo manda la
**pagina stessa** ogni 5 s.

⇒ **Basta che la pagina si apra e si entri.** Due strade, in ordine di costo:

1. ⭐⭐ **Nic apre la pagina col suo browser** (`https://192.168.0.2:7920/`, utente `prova2`),
   accetta il certificato come fa sempre, e il registro del server porta i tre contatori
   `vecchi` · `tardivi` · `fuori` da sé. ⛔ **Non serve nessuno strumento nuovo**;
2. ⚠ Oppure si toglie il certificato di mezzo prima del browser: `cert_override.txt` nel profilo,
   o un certificato che il profilo già conosce. `[?]` **Non provato.**

⛔ **Finché non succede una delle due, la cura 4 (il riordino dell'audio) resta NON VERIFICATA**, ed
è l'ultima delle sei cure del 23 agosto senza un numero.

---

# §15 · ⛔ COM'È RIMASTA LA MACCHINA — *verificato alle 14:56 UTC, non dichiarato a memoria*

| | |
|---|---|
| `tc` su **`lo`** | ⭐ `qdisc noqueue 0: root` — **nessuna disciplina** |
| `tc` su **`enp7s0`** | ⭐ `qdisc mq 0: root` — **mai toccata**, come da regola |
| il **guardiano** di `tc` | ⭐ nessuno: `.b68-guardiano.pid` non c'è |
| **scene, clienti, browser** | ⭐ **nessuno** — né `04-b30-scena`, né `01-b3-cliente`, né `firefox` |
| **porte** | ⭐ **7900 · 7910 · 7920**, le tre di prima, nessuna in più |
| ⚠ **e alle 15:0x una QUARTA** | ⛔ **`7932` — NON è mia.** È comparsa **dopo** che avevo finito, insieme a `banchi/09-b78-apertura.py` sul portatile: è il banco di **un altro agente**. ⭐ Non l'ho toccata. ⚠ La scrivo perché «la macchina è rimasta così» invecchia male: ⛔ **i numeri di §14 non ne sono sporcati** — l'ultimo controllo `pulizia()` di ogni mio giro, fino alle 14:52:35, elencava **solo 7900 · 7910 · 7920** |
| **`core_pattern`** | `/media/REMOTIX/tmp/09c/core.%e.%p.%t` — **lasciato**, è la trappola armata di §4.7 |
| ⭐ **il registro della sera** | salvato in `/media/REMOTIX/tmp/09c/registro-fase9-sera-PRIMA-DI-B74.log` (9 216 437 byte) ⛔ **prima** che `09-b74` cancellasse `registro.log`: senza quella copia i numeri di §14.2-§14.6 non sarebbero più rileggibili |

⭐ **E la 7920 è tornata esattamente com'era**, verificato sulle righe che scrive lei stessa:
binario `md5 162d2d10…` (`f90eb21`), pagina **`md5 e010d615…`** (quella del prodotto, non quella
del *prima* dell'audio), **soglia della coda 0 ms (SPENTA)**, **regolatore SPENTO**, trappola glibc
spenta, fuori da ogni sessione utente.

⚠ **Quel che ho cambiato e non rimetto, perché è il lavoro**: `banchi/01-b3-cliente.py` adesso
negozia **H.264** (§14.1). ⛔ È il metro nuovo, e chi rilegge un numero vecchio deve guardare
**quale codec** dice il registro di quel giro.

---

## §16 · ⭐⭐⭐ IL CASO DURO SUL PERCORSO VERO — *23 agosto 2026, 15:20-15:30, col browser dell'utente*

⛔ **La prima misura della fase presa con un browser vero, sulla tela vera, sulla rete vera.** Tutte
quelle di prima venivano dal cliente di prova su `lo`.

**La scena**: un filmato di **grana pura** 2560×1080 a 30/s (`ffmpeg noise=alls=40:allf=t+u`, CRF 32,
90 s in ciclo), riprodotto con `mpv --fullscreen` dentro la sessione di `prova` sulla **7920**
(prodotto di `f90eb21`+, **nessun interruttore acceso**, tetto di banda SPENTO). Il client è
**Chrome** dell'utente da 192.168.0.3. ⇒ È il caso peggiore che un desktop possa produrre.

### 16.1 ⭐⭐ La banda: **21,5 – 23,1 Mbit/s**, cioè il **107-115 %** del pavimento

| | kbit/s | fotogrammi in 10 s | il più grosso |
|---|---|---|---|
| `[M]` 15:2x | **21 542** | 306 | 365 133 byte |
| `[M]` 15:2x | **23 092** | 299 | 355 169 byte |

⛔ **E questo corregge §14.2 nel verso che conta**: il banco, con la sua scena sintetica, dava
**44,574 Mbit/s = 223 %** del pavimento. Il caso duro **vero** ne chiede **la metà**.
⇒ ⭐ **Il tetto di banda serve ancora — ma il margine da recuperare è di 2-3 Mbit/s, non di 25.**
⚠ E resta `[?]` **quanto sia duro il caso più duro possibile**: la grana pura è un limite superiore
sintetico anche lei; un film vero comprime meglio.

### 16.2 ⭐⭐⭐ E il prodotto TIENE, senza nessuna cura accesa

`[M]` dal verbale che la pagina manda da sé ogni 5 s, e dal registro del figlio:

| | |
|---|---|
| fotogrammi | **7 125 consegnati → 7 125 dipinti** · `salt 0` · `buchi 0` · `ord 0` |
| chiavi | ⭐ **1** in tutto il giro |
| audio | **35 169 ricevuti → 35 169 suonati** · `vecchi 0 · tardivi 0 · fuori 0 · rec 0 · dop 0` |
| coda audio | 238 ms |

⇒ ⛔ **Nessuna spirale, nessun abbandono, nessuna degradazione** — a **interruttori tutti spenti**,
sul caso peggiore, appena sopra il pavimento. ⭐ È la conferma più forte che la fase 9 potesse
ricevere sul verso della decisione §3.1-bis: **a 20 Mbit/s il prodotto non ha bisogno di degradare.**

### 16.3 ⭐ La cura del riordino audio (cura 4): **inerte sul percorso dell'utente, come previsto**

`[M]` `vecchi 0 · tardivi 0 · fuori 0` sia a riposo (4 936/4 936) sia sotto il caso duro
(35 169/35 169). ⇒ ⭐ **La metà che conta per il prodotto è dimostrata**: la cura **non ha cambiato
niente per l'utente**. ⚠ **La metà che morde — la purezza sotto riordino ≥ 0,95 — resta `[?]`**: si
può fare solo sporcando `enp7s0`, che è l'interfaccia dell'ssh e della sessione dell'utente, e non
è stata toccata.

### 16.4 ⛔⛔ LA DESINCRONIA AUDIO-VIDEO CRESCE SOTTO CARICO — ma **NON è giudicabile a occhio**

`[M]` il campo `AV` del verbale della pagina: **+331 ms** a riposo → **+690 ms** sotto il caso duro.
⇒ Il suono precede l'immagine di quasi **sette decimi di secondo**.

⛔ **E qui il banco è stato l'occhio dell'utente, per due volte, e ha detto NO:**

> *«non posso sapere se c'è disallineamento se il video è incomprensibile»* — sulla grana pura, che
> non offre **nessun riferimento** fra quel che si vede e quel che si sente.
>
> *«ancora difficile giudicare il sync»* — sulla stessa scena con un **riferimento innestato**: tutto
> lo schermo lampeggia in bianco per 0,12 s **una volta al secondo**, e nello stesso istante c'è un
> **bip** (`sine=frequency=440:beep_factor=4`).

⛔ **Due letture, e vanno tenute tutt'e due invece di scegliere quella comoda:**

| | |
|---|---|
| ⭐ **una desincronia che non si riesce a giudicare è una desincronia che non morde** | ed è il metro del prodotto: `LEZIONI.md` §7.3, *«quando l'utente dice che va bene, va bene»* |
| ⛔ **oppure lo STRUMENTO non serve, e allora il numero non è ancora stato messo alla prova** | 690 ms su un lampo a schermo intero **dovrebbero** vedersi. Se non si vedono, o `AV` non misura quel che crediamo, o il lampo si perde nella grana, o il bip non cade dove credo |

⇒ ⏳ **Resta `[?]`, e la strada è una misura OGGETTIVA, non un altro giro d'occhio**: un riferimento
che si possa **leggere** invece che giudicare — un lampo su fondo **calmo** (non grana), catturato
insieme al suono, e i due istanti confrontati sul filo. ⛔ E prima di misurarlo va **certificato lo
strumento**: `AV` va confrontato con un ritardo **noto e innestato**, o è un numero che nessuno ha
mai verificato. ⚠ È la stessa forma di `DECISIONI.md` §7.19, dove la desincronia ~400 ms è aperta
**da agosto** e non è mai stata chiusa.

⚠ **E un difetto del metodo, dichiarato**: la scena di prova era **grana pura**, cioè il caso in cui
l'occhio ha **meno** appigli possibili. Chiedere un giudizio di sincronia lì è stato un errore mio,
e la seconda scena non l'ha corretto abbastanza.

### 16.5 Che cosa resta acceso

`[M]` la scena e `mpv` **fermati** alle 15:30. I due filmati restano in
`/media/REMOTIX/tmp/09-scena/` (`duro.mp4` 209 MB, `duro-sync.mp4` 208 MB) — ⚠ su NVMe, **non** sul
rootfs in RAM: il primo tentativo li aveva scritti in `/home/prova`, che vive in RAM, e a CRF 18
faceva **4,1 GB**. Cancellato subito.
⚠ Installati sulla macchina `mpv` e `ffmpeg` (il rootfs vive in RAM: dopo un riavvio vanno rimessi).
⛔ **Firefox sulla macchina di prova NON parte** per l'utente `prova`: il profilo non viene mai
creato (`~/.mozilla/firefox/` ha solo `Crash Reports` e `Pending Pings`). È lo stesso muro su cui si
è fermato il banco dell'audio. ⏳ Non diagnosticato.

---

# §17 · ⭐⭐⭐ LA RETE CATTIVA — *23 agosto 2026, sera*, e **il bersaglio della fase è stato corretto dal regista**

> *«Comunque voglio farti notare una cosa: 30 mbps sono una connessione da metà anni 90. La vera
> sfida è misurare performance con reti che perdono pacchetti o pacchetti fuori sequenza, o
> presentano fenomeni di jitter».*
> — ⇒ `DECISIONI.md` **§3.1-ter**, `PIANO.md` fase 9.

⛔ **E la correzione arriva a fase mezza misurata, con la prova che serviva.** §16 aveva appena
mostrato che sul **percorso vero** il caso peggiore chiede 21,5-23,1 Mbit/s e il prodotto lo regge
**senza degradare e con tutte le cure spente**: 7 125 consegnati → 7 125 dipinti, **una** chiave,
zero abbandoni. ⇒ Un banco che non riesce a far cedere quel che misura **non sta misurando la
grandezza giusta**. Le pagine che seguono sono la grandezza giusta.

## 17.0 ⛔ Le tre grandezze non sono la stessa cosa — e confonderle è il modo facile di misurare male

| | che cos'è | che cosa tocca da noi |
|---|---|---|
| **perdita** | il pacchetto non arriva | il **video** va su stream QUIC, che ritrasmettono ⇒ `[?]` si dovrebbe pagare in **ritardo**, non in fotogrammi. L'**audio** va su datagram ⇒ si paga in **buchi** |
| **fuori sequenza** | arriva, ma dietro a uno più nuovo | ⭐ è la condizione mancante della **cura del riordino dell'audio** del 23 agosto, l'unica cura della giornata la cui metà utile non era mai stata verificata |
| **jitter** | arriva a intervalli irregolari | `[?]` QUIC può **scambiarlo per perdita** e stringere la finestra senza motivo. Se succede, il calo è **nostro** |

⭐ **E il `netem` su `lo` è diventato una risorsa unica con un lucchetto** (`banchi/09-lucchetto.py`):
la disciplina si mette sulla **radice** dell'interfaccia, quindi due banchi che guastano insieme
non si dividono il lavoro — **il secondo cancella il guasto del primo, e il primo continua a
misurare credendo di averlo**. ⚠ Non darebbe rosso: darebbe un numero plausibile. Il possesso si
prende con `mkdir` (atomico anche su ssh), porta una **scadenza scritta dentro**, e chi scassina un
lucchetto scaduto **lo dichiara**.

## 17.1 ⛔⛔⛔ IL VIDEO — la griglia, e **non è una degradazione: è un dirupo**

`banchi/09-b76-rete-cattiva.py` · `[M]` 23 agosto 2026 · 25 s per profilo · 1920×1080 · h264 ·
**banda libera** · ⛔ **tutte le cure ai predefiniti, cioè SPENTE** · binario `51b5994`.

| profilo | persi % (sonda) | raffica | fuori ord. % | **fps** | peggior s | chiavi/tot | deriva max | Mbit/s sul filo |
|---|---|---|---|---|---|---|---|---|
| `liscio` | 0,00 | – | 0,0 | **39,97** | 38 | 0/878 | 6 ms | 3,18 |
| `ritardo-30` ⭐**rif.** | 0,00 | – | 0,0 | **40,11** | 37 | 0/881 | 1 ms | 3,13 |
| `perdita-0,5` | 0,36 | 1,00 | 0,0 | **40,06** | 37 | 0/881 | 46 ms | 3,14 |
| ⛔ `perdita-1` | 0,94 | 1,01 | 0,0 | **9,56** | 4 | 117/209 | 142 ms | 4,00 |
| ⛔ `perdita-3` | 2,96 | 1,03 | 0,0 | **4,03** | 2 | **87/87** | 180 ms | 2,56 |
| ⚠ `perdita-5` | 4,78 | 1,04 | 0,0 | **3,35** | 2 | 73/73 | 157 ms | 2,01 |
| ⭐ `raffica-1` | 1,07 | **6,14** | 0,0 | **23,94** | **0** | 38/526 | **3 707 ms** | 2,99 |
| ⛔⛔ `raffica-forte` | 13,03 | 5,03 | 0,0 | **sessione STACCATA a 0,3 s su 25** | – | – | – | – |
| ⭐ `riordino-25` | 0,00 | – | **68,0** | **40,03** | 38 | 0/880 | 11 ms | 3,27 |
| `jitter-5` | 0,00 | – | 85,3 | **39,30** | 32 | 2/864 | 17 ms | 3,52 |
| ⛔ `jitter-15` | 0,00 | – | 86,3 | **16,62** | 4 | 102/364 | 312 ms | **6,93** |
| ⛔ `jitter-30` | 0,00 | – | 73,2 | **8,07** | 2 | 110/175 | 475 ms | **6,26** |
| `duplicazione-1` | 0,00 (1,02 % dup) | – | 0,0 | **39,96** | 37 | 0/878 | 2 ms | 3,20 |
| ⛔ `casa-cattiva` | 1,71 | 1,02 | 93,8 | **7,78** | **0** | 73/169 | 609 ms | 3,51 |

⛔ **Tredici predicati rossi**, e nessuno muto. Il guasto è stato **verificato messo** su tutti e 14
i profili, con **due gambe che concordano**: il `dropped` del qdisc e una sonda indipendente
(`[M]` `loss 5%`: `dropped 101`, sonda 101 su 2000).

### 17.1-bis ⭐⭐ Le tre cose che i numeri dicono, e nessuna era attesa

1. ⛔⛔ **C'è un dirupo dentro il primo punto percentuale di perdita**: dal 100 % del riferimento al
   **24 %**. Non è una curva, è un **gradino**. ⚠ E nessuna prova di banda l'avrebbe mai trovato: a
   `perdita-1` il filo porta **4,00 Mbit/s**, cioè il **20 % del pavimento dichiarato**. La linea è
   vuota, e il prodotto è in ginocchio.
   ⛔ ⚠ **La forbice «0,36 %-0,94 %» che questa riga portava è SBAGLIATA, e §17.11 la ritira**:
   nasceva da una casella (`perdita-0,5` a *40,06 · zero chiavi*) che **non si riproduce**.
2. ⭐⭐⭐ **A `jitter-15/30` il filo porta il DOPPIO dei byte (6,9 contro 3,1 Mbit/s) per UN QUINTO
   dei fotogrammi, su una rete che non perde un pacchetto.** `[M]` perdita misurata **0,00**.
   ⇒ È la prova diretta che **il disordine viene scambiato per perdita**: ritrasmissioni e chiavi
   che nessuna perdita ha chiesto. Il calo **è nostro**, non della rete — e §3.1-ter lo aveva
   scritto come `[?]` prima di misurarlo.
3. ⚠ **La stessa perdita media fa MENO danno a grappoli che sparsa**: `raffica-1` (1,07 %, grappoli
   da 6) tiene 23,94/s contro i 9,56/s di `perdita-1` (0,94 %, uno alla volta). ⛔ **Ma il prezzo si
   sposta e peggiora**: un secondo intero a **zero fotogrammi**, e la deriva a **3,7 secondi**.

### 17.1-ter ⭐⭐ IL MECCANISMO — letto nel registro del server, non dedotto

`[M]` sugli stessi giri: `abbandonato_in_coda` = `abbandonati` = `chiave_aspetta` **a ogni profilo
rosso** (129 · 102 · 116 · 125 · 83), con `delta_non_spedito` a 550-800. E i **buchi nella
successione dei `numero`** — la seconda gamba, contata dal lato che riceve e indipendente dal
registro del server — concordano: 116, 86, 102, 109, 72.

⇒ **La catena è la spirale di §5.1→§5.2**, ed è la stessa faccia del difetto del 21 agosto:

> il filo ritarda → la coda di spedizione cresce → §5.1 abbandona i delta → §5.2 accende il debito
> → si chiede una **chiave** → la chiave riempie la finestra → **ricomincia**

⛔ A `perdita-3` fa **87 chiavi su 87 fotogrammi**: identica al 144/144 del 21 agosto.

⭐⭐ **E la cura di questa catena era già scritta, collaudata e SPENTA** — `--sgombra-soglia-ms` e
`--ritmo-adattivo`, dietro interruttore per l'invariante I6. ⇒ La griglia qui sopra è girata **con
gli interruttori spenti**, ed è la ragione per cui la prova appaiata delle cure (§17.6) è il
seguito obbligato di questa pagina e non un di più.

### 17.1-quater ⛔⛔ `raffica-forte` — **NESSUNO si stacca: si ferma la CONSEGNA**

⚠ La prima lettura di questa casella diceva *«la sessione muore dopo 0,3 s su 25»*. ⛔ **La parola
era sbagliata, e una parola sbagliata su un rosso è peggio di un rosso mancato**: manda a cercare la
causa dove non è — qui, un congedo che non esiste.

`[M]` 23 agosto, **quattro testimoni** (`banchi/09-b79-cure.py`): il cliente stampa *«ancora
attaccato dopo 25,0 s: niente è caduto»* e chiude **lui** a fine finestra · l'audio arriva per tutto
il giro (**696 datagram, purezza 1,0000**) · il registro del server non ha **nessun** `CONGEDO`,
nessun `posto NEGATO`, nessun ban · la sessione si era aperta normalmente (`AMMESSO dopo 1 837 ms`),
il che esclude anche *«la stretta di mano non si completa»* — coerente con §17.4. `IDLE_MS` è
30 000 ms e infatti non c'entra.

⇒ **A fermarsi è la sola consegna dei fotogrammi**: `[M]` **121 spediti su 981 catturati, 860 NON
SPEDITI**, con `cwnd` inchiodata a **~10 KB** e il pacer che rifiuta.

⛔ **Il fatto resta grave, e non va declassato**: una sessione **viva e muta** è uno schermo fermo, e
per chi guarda è indistinguibile da un filo caduto. ⚠ Ma ha **un altro nome e un'altra causa** — non
viola *«mai staccare»*, viola il pavimento della scala (`DECISIONI.md` §2.1: 25 fotogrammi/s).
⇒ Il predicato `p_niente_stacco` di `09-b76` misurava **quanto è durata la consegna**, non **se la
connessione è caduta**: il numero era giusto, la parola no. ⏳ In cura: il predicato si spezza in
due, perché sono due fatti con due cause.

⭐⭐ **E le cure lo cambiano**: in B e in C la consegna dura **tutti i 25 secondi** (§17.6).

## 17.2 ⭐⭐⭐ L'AUDIO NEL RIORDINO — **la cura morde**, e adesso è misurato

⛔ Era la sola cura del 23 agosto la cui metà utile fosse rimasta `[?]`, e per una ragione detta:
*«per verificarla bisogna sporcare la rete e non l'ho fatto»*. La correzione del regista **è la
condizione mancante di quella verifica**.

⛔ **E prima è stato necessario portare la cura nel cliente dei banchi**: era stata scritta **solo
in `src/pagina.html`**, mentre `banchi/01-b3-cliente.py` aveva ancora la regola vecchia. ⇒ Fino a
stasera **nessun banco poteva misurarla**. Adesso c'è `--audio-regola vecchia|nuova`, ⛔ col
predefinito **`vecchia`** e la verifica che con quello i contatori e la **lista** dei blocchi
consegnati sono identici a una trascrizione letterale del codice del 22 agosto su cinque
successioni: un cliente che cambia i numeri già scritti non è uno strumento, è una variabile.

`banchi/09-b77-audio-riordino.py` · `[M]` 23 agosto 2026 · porta 7931 · 25 s per giro · **due giri
identici in tutto tranne la regola**:

| profilo | regola | **PUREZZA** | tono | copertura | sul filo | conseg. | vecchi | fuori | rec | dop | srv `dgram_falsi` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `liscio` | vecchia | 1,0000 | 1,000 | 1,0000 | 4993 | 4993 | 0 | 0 | 0 | 0 | 0 |
| `liscio` | **nuova** | 1,0000 | 1,000 | 1,0000 | 4992 | 4992 | 0 | 0 | 0 | 0 | 0 |
| `jitter-2` | vecchia | 0,7992 | 0,804 | 0,7993 | 4989 | 3987 | **1002** | 0 | 0 | 0 | 1062 |
| `jitter-2` | **nuova** | **1,0000** | 1,000 | 0,9982 | 4983 | 4983 | 0 | 1028 | 1028 | 0 | 115 |
| `jitter-5` | vecchia | 0,6877 | 0,683 | 0,6854 | 4970 | 3418 | 1552 | 0 | 0 | 0 | 698 |
| `jitter-5` | **nuova** | **1,0000** | 0,995 | 0,9954 | 4970 | 4970 | 0 | 1620 | 1620 | 0 | 732 |
| `jitter-15` | vecchia | 0,4350 | 0,370 | 0,3670 | 4214 | 1833 | 2381 | 0 | 0 | 0 | 1458 |
| `jitter-15` | **nuova** | **1,0000** | 0,846 | 0,8361 | 4177 | 4177 | 0 | 2392 | 2392 | 0 | 1458 |
| `riordino-25` | vecchia | 0,8912 | 0,895 | 0,8912 | 4990 | 4447 | 543 | 0 | 0 | 0 | 1415 |
| `riordino-25` | **nuova** | **1,0000** | 1,000 | 0,9982 | 4982 | 4982 | 0 | 550 | 550 | 0 | 450 |
| `casa-cattiva` | vecchia | 0,4013 | 0,261 | 0,2585 | 3192 | 1281 | 1911 | 0 | 0 | 0 | 1190 |
| `casa-cattiva` | **nuova** | **1,0000** | 0,648 | 0,6264 | 3120 | 3120 | 0 | 1837 | 1836 | 0 | 1190 |

**Sei profili su sei verdi, zero rossi, zero non giudicati.** `doppioni` **0** dappertutto (un
doppione qui vorrebbe dire che l'ha spedito il server); `scartati_tardivi` **0** dappertutto (la
rete di sicurezza dopo il decodificatore non ha mai dovuto scattare); `recuperati` ripaga i
`mancati` **uno a uno** (1028/1028, 1620/1620, 2392/2392) — cioè la cura **non si accusa da sola**
di perdite che ha invece recuperato.

⭐ **E la cura resta onesta**: `--certifica` porta due casi che le darebbero **rosso** se lo fosse —
purezza 0,999 **con** `fuori_ordine` a zero (vorrebbe dire che il profilo non morde e il verde è un
caso), e la controprova che la regola nuova **butta comunque** il blocco arrivato davvero troppo
tardi. Una cura che tenesse tutto non sarebbe una cura: sarebbe la rimozione di un controllo.

### 17.2-bis ⛔⛔ IL `[M]` DEL «0,175» — il conteggio regge, **la sua purezza no**

`src/pagina.html:6474` portava: *«jitter ±2 ms ⇒ purezza 0,175, 1 004 scartati su 4 989»*.
`[M]` stasera, stesso profilo: **1 002 buttati su 4 989 sul filo**. ⇒ Lo **stesso denominatore**,
due blocchi di differenza: il **conteggio** di quel `[M]` è solido.

⛔ **Ma la sua «purezza 0,175» non è confrontabile con niente**, ed è stato fermato prima che
diventasse un trionfo. La frazione che usano i banchi della pagina è `suonati/ricevuti`
(`09-b74:300`), e `a.ricevuti++` sta **dopo** i rami di scarto (`pagina.html:6574`): il denominatore
conta **solo i sopravvissuti**, quindi quel rapporto vale ~1,000 **con tutt'e due le regole**, su
una successione anche distrutta. ⚠ È vero nel codice **prima** e **dopo** la cura, verificato su
`f90eb216^`: da dove venisse quello 0,175 **non si sa**, ed è un numero di cui non si conosce la
definizione.

⭐ ⇒ La grandezza del banco è **`purezza = consegnati / sul filo`**, col denominatore contato
**prima** del vaglio, e l'atteso è un **confine dichiarato** (0,90 / 0,80 / 0,60), non quel punto.
`purezza_pagina` si stampa accanto **solo per confronto**, con scritto che è cieca.

### 17.2-ter ⛔⭐ IL ROSSO CHE ERA DEL BANCO — e la cura del predicato

`casa-cattiva` dava rosso: il cliente contava **2 183 `mancati` su 4 996, il 43,7 %**, con `netem`
al **2 %**. ⛔ Non era la rete: il registro del server diceva **1 823 blocchi RIFIUTATI da ngtcp2** —
mai messi sul filo, finestra di congestione chiusa a 40 ms di ritardo. `mancati` si costruisce sui
salti di `istante`, e **un blocco mai spedito lascia lo stesso salto di uno perso**.

⇒ Il predicato è stato riscritto **sui due capi**: `spediti dal server − sul filo del cliente` =
**67 perduti sulla rete, il 2,10 %**, contro il 2 % chiesto a `netem`. ⭐ È R13 in forma pura — un
numero che sembrava misurare la rete e misurava noi.

### 17.2-quater ⚠⚠ E DIETRO C'È UN FATTO DEL PRODOTTO CHE NON C'ENTRA CON LA CURA

`[M]` i blocchi audio **rifiutati da ngtcp2**, cioè prodotti e mai messi sul filo: **4** su
`jitter-2`, **819** su `jitter-15`, **1 823** su `casa-cattiva` — ⛔ **il 36 % dell'audio prodotto
non raggiunge il filo**. ⇒ È anche il motivo per cui su `jitter-15` e `casa-cattiva` la *copertura*
resta 0,84 e 0,63 **pur avendo purezza 1,0000**: il ricevente consegna tutto quel che gli arriva,
ma **il trasporto non gli fa arrivare tutto**. ⏳ Aperto, e non è un difetto della cura: è la stessa
finestra di congestione che nel video produce la spirale.

## 17.3 ⭐⭐⭐ DUE TESTIMONI NUOVI NEL SERVER — e uno misura il RIORDINO

⛔ Prima di stasera il registro **non sapeva dire di chi fosse la colpa**. Un fotogramma in ritardo
poteva essere un pacchetto perso e rimandato, la finestra chiusa, noi che l'abbiamo tenuto o noi
che l'abbiamo abbandonato: le ultime due si contavano, **le prime due no**.

**1 · la riga `rete-quic`** (`src/webtransport.c`, `rete_ciclo()`) — al più una al secondo, e
**tace se i contatori sono fermi e il giudizio non è cambiato**:

```
rete-quic 192.168.1.9:52344 da_ms=1002 persi=7 persi_d=3 byte_persi=9856 ... cwnd=48000
cwnd_left=0 ssthresh=32000 involo=47180 srtt_us=41230 latest_us=52980 rttvar_us=11400
min_rtt_us=22100 coda_rete_us=19130 pto_us=132000 dgram_persi=… giudizio=⛔ la linea perde
```

⚠ Tre scelte che un banco deve sapere: `giudizio=` è **l'ultimo campo** e il suo valore arriva a
fine riga; l'rtt è in **microsecondi** (in rete locale `rttvar` arrotondato ai ms varrebbe 0, e
nasconderebbe proprio il jitter che è il bersaglio); `da_ms` è l'intervallo **vero**, e i campi `_d`
valgono su quello — chiamarli `_1s` sarebbe stato un numero che sembra misurato e non lo è.

Il **giudizio** ha tre valori e la regola è scritta: `persi_d > 0` ⇒ `⛔ la linea perde` (per primo,
perché la finestra chiusa è quasi sempre la **conseguenza** della perdita, e invertendo la causa si
nasconderebbe dietro il suo effetto); altrimenti `cwnd_left == 0 && cwnd > 0` ⇒ `⚠ la finestra e'
chiusa`; altrimenti `-- niente da segnalare`. ⛔ Il giudizio **non parla di jitter né di riordino**,
apposta: quei numeri ngtcp2 non li dà, e dedurli da `rttvar` avrebbe voluto una **soglia**, cioè una
decisione.

**2 · ⭐⭐⭐ `dgram_falsi` — il riordino, misurato dal lato del server.**
`[S]` `ngtcp2.h:3442`, sul callback `lost_datagram`: *«Note that the loss might be spurious, and
DATAGRAM frame might be acknowledged later»*. ⇒ Stesso `dgram_id` visto prima come **perso** e poi
come **riscontrato** = pacchetto **arrivato fuori sequenza**, dichiarato perduto dalla soglia dei
tre pacchetti e riscontrato dopo.

⛔ Fino a stasera `ngtcp2_callbacks` (`src/trasporto.c` · `ngtcp2_callbacks`) registrava `recv_datagram` **e basta**:
i datagram in arrivo si contavano (rilievo B-10), quelli in **partenza** — cioè l'audio — sparivano
nel filo senza lasciare traccia. *«L'audio non è arrivato»* e *«è arrivato e il cliente l'ha
buttato»* avevano la stessa faccia, ed è lo stesso difetto di allora dall'altro verso.
⛔ E si registrano **in coppia**: `lost_datagram` da sola conterebbe i riordini come **perdite**,
cioè darebbe un numero **più alto del vero** e senza dirlo.

⚠ **Il prezzo, dichiarato**: vale **sui datagram soltanto**, cioè sull'audio. Gli stream QUIC non
hanno un identificativo per pezzo, e questa strada lì **non c'è** — sul video il riordino resta
senza testimone diretto.

### 17.3-bis ⛔ Quel che ngtcp2 1.25 NON dà, detto forte

- **i ritrasmessi non esistono** `[S]`: QUIC non ritrasmette pacchetti, ritrasmette i *frame*
  dentro pacchetti nuovi, e non c'è nessun contatore di rimandi. `pkt_lost` (i pacchetti
  **dichiarati** perduti) è quanto ci si avvicina;
- **il riordino sugli stream non si conta** `[S]`: nessun campo, nessun callback, e la soglia dei
  tre pacchetti ngtcp2 la usa al suo interno senza esporla. ⇒ Lì `rttvar` resta l'unico indizio;
- **`delivery_rate` non esiste** `[S]`: la banda resta stimata da `cwnd`/`smoothed_rtt`;
- ⛔ **il contatore `reordered` di `tc` non esiste su questa macchina** `[M]`: iproute2 6.15.0, il
  blocco `netem` stampa solo `Sent/dropped/overlimits/requeues/backlog`, e con `reorder 25% 50%`
  acceso si muove solo `requeues`. ⇒ Il riordino è stato misurato con **tre testimoni concordi** —
  una sonda UDP numerata attraverso lo stesso `netem`, i sorpassi contati sul JSONL del cliente, e
  `dgram_falsi` dal server — non dedotto.

## 17.4 ⭐⭐ LA STRETTA DI MANO SOTTO PERDITA — **il `[M]` del 10 % era un difetto del banco**

`banchi/09-b78-apertura.py` · `[M]` 23 agosto 2026 · 10 giri per gradino · perdita **letta** da
`tc -s qdisc` · fino ad `AMMESSO` (QUIC + CONNECT estesa + `CIAO/ECCOMI` + `CREDENZIALI/AMMESSO`):

| perdita chiesta | perdita vera | aperte | QUIC mediana | totale mediana | totale max |
|---|---|---|---|---|---|
| 0 % | – | **10/10** | 7,8 ms | 1 014 ms | 1 116 ms |
| 5 % | 8,2 % | **10/10** | 7,8 ms | 1 078 ms | 1 318 ms |
| 10 % | 9,5 % | **10/10** | 10,9 ms | 1 103 ms | 1 219 ms |
| 15 % | 15,2 % | **10/10** | 111,5 ms | 1 281 ms | 1 708 ms |
| 25 % | 24,3 % | **10/10** | 211,9 ms | 1 299 ms | 1 738 ms |

⭐ **La sessione si apre sempre**, anche al 25 %. **La rete costa 285 ms fra lo 0 e il 25 %**; il
secondo che si vede **non è la rete**, è il ritardo fisso di §4.4-bis contro chi prova le password.
I massimi della stretta di mano stanno a 212 e 613 ms — **uno e due PTO**.

Le cinque ipotesi, tutte smentite una per una: il cliente non si arrende (**0 giri su 70** hanno
superato il suo tetto di 8 s); il ban non c'entra (`src/rcp.c` · il conteggio dei verdetti PAM conta solo verdetti PAM su
`CREDENZIALI`, e una stretta di mano non ci arriva); ngtcp2 riprova (`handshake_timeout` resta
`UINT64_MAX`, `trasporto.c:544`); il `netem` non è applicato due volte (i due filtri prendono i due
**versi**, quindi un **giro** paga `1-(1-p)²` e un **datagram**, che fa un verso solo, paga `p` —
`[M]` 3 235/3 607 = 89,7 %).

### 17.4-bis ⛔ IL PREDICATO CHE NON POTEVA DARE ROSSO — R13 di nuovo, in `07-b64-rete.py`

```python
def a_non_si_apre(n):
    return _p(n["ricevuti"] == 0, "nessun datagram: la sessione non si apre")
```

⛔ `01-b3-cliente.py:1286` stampa `[audio] ricevuti 0` **anche dal ramo `except`**, prima di
rilanciare. ⇒ **Ogni** modo di fallire — un `CONGEDO`, un tetto scaduto, un `NameError` del banco —
faceva passare quel gradino di **verde**. Il banco non misurava *«non si apre»*: misurava *«non ho
ricevuto»*, e le due cose hanno la stessa faccia.

⛔ **E un secondo difetto nello stesso file**: `guasta([])` chiama `rimetti(False)`, che chiama
`guardiano_disarma()`. Il profilo `0-liscio` è **il primo**, quindi disarmava il guardiano armato
due righe prima, e gli **otto profili successivi giravano senza rete di sicurezza**.

⏳ **Le due cure sono scritte e NON applicate**: `07-b64-rete.py` è importato dai banchi che stanno
girando in questo momento, e cambiargli una firma a metà misura sarebbe il difetto che questa
sezione descrive.

## 17.5 ⛔⛔ IL FANTASMA — *«hai già una sessione attiva altrove»*, e per l'utente è **falso**

⭐ È il fatto di prodotto trovato dietro §17.4, e sul bersaglio della fase.

L'unico modo in cui un'apertura fallisce davvero sotto perdita è `ATTACCA` → `CONGEDO(0x0F)
GIA_ATTIVA_REMOTA` (`[M]` 5/10 al 10 % di perdita). Il registro dice: *«posto NEGATO … lo occupa un
altro client di questo stesso utente»*.

⛔ **Il conto si chiude senza `netem`**, perché un addio **perso** e un addio **mai detto** sono lo
stesso fatto: ucciso il cliente con `-9`, `[M]` **11 rifiuti di fila, e il posto torna libero a
+30,5 s** — cioè `SILENZIO` (`src/rcp.c` · `SILENZIO`, 30 000 ms).

⚠ **La frase che il client costruisce è falsa per chi la legge**: quella sessione è **la sua**, ed è
morta un attimo prima. E il riquadro di `src/rcp.c:229-233` dichiara che quell'orologio *«fa
sparire il caso "il telefono è morto in galleria"»* — ⛔ non lo fa sparire: lo **dura trenta
secondi**, e la perdita di pacchetti è precisamente quel che lo rende **normale** invece che raro.

**La cura proposta, NON scritta — è un cambio di politica di §8.2 e la decide l'utente:** in
`src/rcp.c`, ramo `POSTO_OCCUPATO` di `rcp_attacca()` (righe 2605-2616), prima di congedare con
`0x0F` guardare l'`ultima_vita` dell'occupante: se tace da più di una soglia breve (~3 s) **mentre
un altro client dello stesso utente sta chiedendo il posto**, sfrattarlo. §8.2 dice *«nessun client
attaccato e **vivo** viene mai spodestato»* — l'occupante qui è attaccato ma **non vivo**, e oggi
l'unico orologio che lo distingue è quello da 30 s. `torna_a_parlare()` (`rcp.c:6921`) gestisce già
lo sfrattato che torna. ⛔ Non toccherebbe `SILENZIO`, che resta 30 s per tutto il resto.

## 17.6 ⭐⭐⭐ LE DUE CURE, APPAIATE — **la spirale si spegne, e solo con tutt'e due**

`banchi/09-b79-cure.py` · `[M]` 23 agosto 2026 · binario `eee17f40…` dall'**albero di lavoro** ·
25 s per casella · 1920×1080 · h264 · un giro per casella. ⛔ Ogni braccio verificato dalle **righe
d'avvio del prodotto**, non dalla riga di comando (un interruttore che si crede acceso e non lo è
darebbe un appaiamento senza differenza, cioè un verde). Il guasto verificato dalla sonda a **ogni**
casella.

- **A** = i predefiniti, cioè **cure spente**. ⛔ Rimisurato, non ripreso da §17.1: quei numeri
  vengono da un altro binario e da un'altra ora.
- **B** = `--sgombra-soglia-ms 100` — la sola soglia sulla coda.
- **C** = `--sgombra-soglia-ms 100 --ritmo-adattivo` — soglia **più** regolatore del ritmo.

| profilo | br | fps | peggior s | **chiavi %** | deriva fin. | **deriva max** | Mbit/s filo |
|---|---|---|---|---|---|---|---|
| `ritardo-30` ⭐**sana** | A | 39,85 | 36 | 0,0 | 0,1 | 8,9 | 7,55 |
| | B | 40,19 | 37 | 0,0 | 0,2 | 5,8 | 7,60 |
| | C | 39,63 | 36 | 0,0 | 0,9 | 6,1 | 7,53 |
| `perdita-1` | A | 11,96 | 5 | **51,7** | −2,4 | 76,5 | 3,43 |
| | B | 32,13 | 17 | 6,4 | 23,2 | 107,8 | 4,84 |
| | **C** | **32,85** | 21 | **0,0** | −1,6 | 99,3 | 5,11 |
| `perdita-3` | A | 7,34 | 5 | **88,1** | −40,0 | 53,4 | 2,17 |
| | B | 20,63 | 11 | ⛔ 23,8 | 32,9 | 139,3 | 2,90 |
| | **C** | 19,63 | 11 | **0,2** | −62,2 | 165,7 | 2,79 |
| `jitter-15` | A | 10,76 | 6 | **59,2** | 11,7 | 102,1 | 3,48 |
| | B | 25,88 | 9 | ⛔ 12,8 | −65,7 | 64,0 | 8,06 |
| | **C** | 21,48 | 15 | **0,0** | 53,8 | 168,4 | 6,63 |
| `jitter-30` | A | 8,56 | 5 | **73,1** | 6,7 | 115,6 | 2,55 |
| | B | 20,25 | 10 | ⛔ 19,9 | −5,0 | 277,0 | 5,77 |
| | **C** | 16,68 | 12 | **0,0** | −116,0 | 180,8 | 4,96 |
| `casa-cattiva` | A | 8,28 | 3 | **72,0** | −71,5 | 295,3 | 2,21 |
| | B | 14,37 | 6 | ⛔ 33,6 | 152,7 | 238,4 | 3,01 |
| | **C** | 13,86 | 4 | **5,6** | 102,2 | 284,2 | 3,38 |
| ⚠ `raffica-forte` | A | *la consegna muore a **4,4 s** su 25* | | | | | |
| | B | 4,25 | **0** | 44,6 | 24,9 | **7 756** | 0,59 |
| | C | 4,18 | **0** | 4,4 | 2,1 | **4 521** | 0,78 |

### 17.6-bis ⭐⭐ I quattro fatti

1. ⭐⭐⭐ **La spirale si spegne — ma solo col braccio C.** La quota di chiavi passa da **51,7-88,1 %**
   a **0,0-5,6 %** su tutti e cinque i profili rossi. ⛔ **La sola soglia (B) non basta**: lascia
   12,8-33,6 % di chiavi in quattro profili su cinque.
   ⭐ **E il perché si legge nei contatori del server**: in C, su `raffica-forte`,
   `delta_non_spedito` **988 → 6** e `chiave_aspetta` **32 → 0**. La soglia smette di *buttare*, ma
   il debito di §5.2 continua ad **accendersi**; il regolatore lo previene perché il fotogramma
   **non parte affatto**. ⇒ È la conferma sperimentale dell'ordine obbligato dichiarato in §6: la
   soglia è il **prerequisito** del regolatore, non un'alternativa.
2. ⛔⭐ **La linea sana non paga niente** — ed era il predicato che valeva più di tutti.
   39,85 / 40,19 / 39,63 fps (un punto percentuale, dentro il rumore dichiarato del 5 %), **zero
   chiavi** in tutt'e tre i bracci, deriva finale 0,1 / 0,2 / 0,9 ms. ⇒ Le cure **non hanno un
   costo di regime**: sono mute finché non servono, che è precisamente quel che I1 pretende.
3. ⭐ **Il ritmo torna da 1,7 a 2,8 volte** su ogni profilo rosso. ⚠ E B dà quasi sempre **più**
   fotogrammi/s di C: ⛔ non sono «peggio e meglio», sono **più fotogrammi con più chiavi** contro
   **meno fotogrammi tutti delta**. Chi confrontasse la sola colonna dei fotogrammi/s sceglierebbe B
   e prenderebbe la spirale in casa.
4. ⭐⭐ **E i byte sul filo SALGONO** (3,48 → 8,06 Mbit/s a `jitter-15`): ⇒ **la linea non era satura,
   era sprecata.** È l'altra faccia di §17.1-bis punto 2 — lì il doppio dei byte per un quinto dei
   fotogrammi, qui il doppio dei byte per **il doppio** dei fotogrammi.

### 17.6-ter ⚠ IL PREZZO, e i due numeri si danno senza scegliere

**Deriva massima**, sui cinque profili ordinari: da **−38 a +161 ms** rispetto ad A (⭐ su
`casa-cattiva` e `jitter-15` il braccio B la fa perfino **calare**). **Zero sulla linea sana.**

⛔ **Su `raffica-forte` il prezzo esplode: 4,5-7,8 secondi.** Lì C **non è ovviamente meglio di A**:
è *un'immagine che si muove con cinque secondi di ritardo* contro *un'immagine ferma*. ⚠ Questo
documento dà i due numeri e **non sceglie**: la scelta fra immagine e ritardo è dell'utente
(`DECISIONI.md` §0.1, invariante I6), non di una misura.

## 17.7 ⛔ I DIFETTI DI BANCO TROVATI STASERA — tutti della forma «silenzio invece di rosso»

| dove | che cosa | esito |
|---|---|---|
| `07-b64-rete.py` | `a_non_si_apre` verde su qualunque modo di fallire | ⭐ **curato** e rifatto girare (§17.4-bis, §17.9-bis) |
| `07-b64-rete.py` | `0-liscio` disarma il guardiano per gli otto profili dopo | ⭐ **curato**, `[M]` guardiano ancora vivo dopo `guasta([])` |
| `07-b64-rete.py` | `spediti_dal_server` a `None`: `None == 0` è falso ⇒ verde su un giro in cui il capo del server non era stato letto | ⭐ **curato**: adesso è muto (§17.9-bis) |
| ⛔ `07-b64-rete.py` | la riga di «conto finale» arriva **29 s tardi** quando il pacer ha coda ⇒ il giro dopo legge **il conto del giro prima** — e il posto ancora occupato lo fa morire di `GIA_ATTIVA_REMOTA` | ⭐ **curato** con `registro_posato()` (§17.9-bis) |
| `09-b70-ritmo.py` | `sudo -S` copre solo il **primo** comando della catena ⇒ il lettore §11.1 non si scriveva | ⭐ **curato** con `catena_root()` (§17.9-ter) |
| `09-b70-ritmo.py` | un `< file` in coda **ruba lo stdin a `sudo -S`** ⇒ `righe_registro()` torna 0 in silenzio, e `attese_a_vuoto` diventa cumulativo dall'accensione — cioè la colonna su cui I1 decide se rifiutarsi di giudicare | ⭐ **curato**, `[M]` 1 604 del giro contro 4 041 cumulativi |
| `09-b70-ritmo.py` | `01-b4-validatore.py` non viene spedito dal terreno ⇒ giornale vuoto ⇒ **rosso a «non stacca» su una sessione viva da 797 fotogrammi** | ⭐ **curato**: il terreno lo verifica, il banco si rifiuta |
| `09-b76` | ⛔ `p_niente_stacco` misurava **la durata della consegna** e la chiamava **stacco** | ⭐ **spezzato in due** (§17.9-quater) |
| `09-b79-cure.py` | l'avvolgimento di `root()` saltava la cura del sottostante | ⭐ **curato**, e `[M]` **nessun numero era sporcato** (§17.9-sexies) |
| `09-b76` (in corso d'opera) | ⛔ **`tc qdisc change` è appiccicoso**: un `reorder` messo per un profilo restava acceso nei quattro dopo | curato: il banco **rilegge** la regola installata e dà rosso se porta un verbo non chiesto |
| `09-b77` (in corso d'opera) | le regex cercavano i nomi **interni** dei contatori mentre il cliente stampa altri nomi ⇒ `None` su tutto, nessun errore | curato, e `--certifica` ora prova le regex sull'**uscita vera** del cliente |
| `09-b77` (in corso d'opera) | `mancati` conta come perduti anche i blocchi **mai spediti** | curato: il predicato lavora **sui due capi** (§17.2-ter) |

## 17.9 ⭐⭐ LA TORNATA DELLE CURE AI BANCHI — *23 agosto, notte*, e ne sono usciti altri quattro

⛔ **Sette difetti di banco su nove trovati stasera, e tutti della stessa forma: «silenzio invece di
rosso».** Le cure sono state applicate e **ogni banco è stato rifatto girare**. Quel che segue è il
seguito, e vale la pena leggerlo perché **due dei quattro nuovi sono usciti facendo girare il banco
curato**, non leggendolo.

### 17.9-bis ⛔⛔ IL TERZO E IL QUARTO DI `07-b64-rete.py` — e il quarto è il più grosso

**Terzo.** `spediti_dal_server` a `None`: `conti_del_server` torna `{"esito": "NIENTE DA LEGGERE"}`,
e `None == 0` è **falso** ⇒ il gradino filava dritto al predicato. I predicati che non guardano il
server (`a_pulito`, `a_sorpassi`) davano **verde su un giro in cui il capo del server non era stato
letto affatto**. ⇒ Adesso è **muto**.

**Quarto — ⛔ e questo sporca i numeri, non solo i verdetti.**
`[M]` **la chiusura di una sessione è lenta quando il pacer ha coda**: il profilo al 10 % di perdita
ha impiegato **29 secondi in più** degli altri a scrivere la sua riga di «conto finale». ⇒ Il giro
**successivo** prendeva la sua `riga0` **prima** che quella riga esistesse, e `conti_del_server()`
leggeva **il conto del giro precedente**.

⭐ **La firma è inconfondibile**: `[M]` tre profili di fila hanno riferito gli **stessi identici
numeri** («spediti 4999 · rifiutati 3 · rimandati 7410»), che erano il conto del **primo** dei tre.
Il conto vero del secondo era **4 632**. ⇒ Il predicato nuovo ha dato **rosso su un denominatore
altrui** (4 152/4 999 = 0,831), mentre col denominatore giusto era 4 152/4 632 = **0,896**, verde.

⚠ **E lo stesso ritardo produce un secondo effetto, peggiore**: il gradino dopo è morto con
`CONGEDO 0x0F GIA_ATTIVA_REMOTA` — il posto del precedente era **ancora occupato**, ed è la
serratura di 30 s di **§17.5**. ⇒ **Un giro può fallire per colpa del giro prima**, e l'`[audio]
ricevuti 0` che ne usciva è **esattamente il numero che il vecchio `a_non_si_apre` avrebbe chiamato
verde**. ⭐ I due difetti di §17.4-bis e il fantasma di §17.5 si nutrivano a vicenda.

**La cura**: `registro_posato()` — si aspetta che il conto delle righe «conto finale» stia **fermo
3 s** prima di cominciare un gradino — e `conti_del_server(riga0, n0)` **pretende una riga sua**,
altrimenti resta muto.

**Il giro nuovo di `07-b64`** `[M]` 23 agosto, porta 7801, 25 s per profilo: **9 gradini · 0 rossi ·
0 muti**, e il controllo positivo (`--controllo-rosso`) dà rosso con uscita 1 — il verdetto sa
ancora fallire. ⭐ Il gradino al 10 % conferma il conto dei due versi: **4 077/4 504 = 0,905** contro
`1-p` = 0,901. **È `1-p`, non `1-(1-p)²`**: un datagram fa **un verso solo**.

### 17.9-ter ⭐ LE TRE CURE DI `09-b70-ritmo.py`, e il numero che dimostra la seconda

`sudo -S` che copre solo il primo anello ⇒ nuova `catena_root()`, un solo `sudo -S bash -c` con la
catena dentro. `[M]` il lettore di §11.1 adesso **si scrive davvero** (4 130 byte) e riduce
**794 fotogrammi** per giro; la forma vecchia sullo stesso comando dava `Permission denied`.

Il `< file` che ruba lo stdin ⇒ `righe_registro()` torna **`None`**, non 0, e la guardia sta dove il
numero **si consuma**. ⭐ **Il numero che dimostra la cura:**

| | riga di partenza | righe `ciclo:` | `attese_a_vuoto` |
|---|---|---|---|
| giro mosso | 327 | 21 | **1 607** |
| giro fermo | 3 711 | 21 | **1 604** |
| ⛔ forma vecchia (`riga0` = 0) | 1 | 49 | **4 041** |

⇒ Col difetto, il giro fermo avrebbe dichiarato **4 041 invece di 1 604** — **2,5 volte**, e in
salita a ogni giro. ⛔ Ed è precisamente la colonna con cui `p_I1` decide **se rifiutarsi di
giudicare**.

**E la premessa falsa di I1**: la gamba «zero abbandoni a scena ferma» ora è **condizionata alla
perdita letta dal `qdisc` installato**, non assunta zero. Con perdita > 0 il predicato **si rifiuta**
invece di accusare il prodotto (era il falso rosso di `casa-cattiva`).

**Quarta cura, trovata dal giro vero**: il lettore §11.1 non partiva perché `01-b4-validatore.py`
non è fra i file che `07-b64-terreno.sh porta` spedisce ⇒ giornale vuoto ⇒ il banco dava **rosso a
«non stacca» su una sessione viva da 797 fotogrammi**.

### 17.9-quater ⭐⭐ `09-b76` — IL NOME GIUSTO, e la griglia rifatta

`p_niente_stacco` è **spezzato in due**, perché sono due fatti con due cause:

- **`p_connessione_viva()`** — vale su **tutti** i profili (§3.3/§8.3, anche sotto il pavimento) e
  interroga i **testimoni della connessione**, non i fotogrammi: il cliente (*«ancora attaccato dopo
  N s»*) e il registro (`congedo motivo=`, `posto NEGATO`, ban), **col motivo stampato**. ⚠ La terza
  possibilità — *«non si è mai aperta»* — è **muta** per costruzione, non rossa.
- **`p_consegna_non_si_ferma()`** — copertura ≥ 0,90 dei secondi che hanno visto almeno un
  fotogramma, e ⛔ **nessun buco ≥ 1,0 s**, **coda compresa**. ⚠ La soglia 0,90 **non è nuova**: è la
  stessa che usava il predicato vecchio. **Il numero non cambia: cambia la parola, ed è tutta la
  cura.** Il buco di 1 s ha la sua ragione: §2.1 mette il pavimento a 25 fotogrammi/s, quindi un
  secondo a **zero** è fuori scala, non «un ritmo basso».
- ⚠ Prezzo dichiarato: `[M]` sui tredici profili sani il buco massimo va da **0,04 a 0,35 s**,
  contro **14,26 s** a `raffica-forte` — più di un ordine di grandezza di margine, **zero falsi
  rossi**, diagnosi compresi.

⭐ E `--certifica` porta ora il caso che aveva ingannato il banco: **lo stesso giro dà rosso sulla
consegna e verde sulla connessione**. 49 casi su 49.

**`raffica-forte`, col nome giusto e i numeri** `[M]` (sonda: **11,10 %** di perdita in 197 raffiche,
media 4,51, max 27): **nessuno ha staccato** — cliente attaccato per tutti i 25 s, zero congedi. A
fermarsi è la **sola consegna**: **7 secondi su 25** hanno visto un fotogramma, **14,26 s di schermo
fermo di fila**, 952 righe `FOTOGRAMMA NON SPEDITO`, `cwnd` mediana **8 948 B** contro **105 616 B**
del riferimento (**12 volte meno**), `cwnd_left` mediana **0**. ⭐⭐ **E il server lo dice da sé**:
`⚠ la finestra e' chiusa` su **10 righe `rete-quic` su 18** — è il testimone di §17.3 che dà la
risposta senza che nessuno debba dedurla.

### 17.9-quinquies ⛔⛔ E DUE GRIGLIE DELLO STESSO BANCO NON COINCIDONO — dichiarato, non lisciato

Il giro di `09-b76` rifatto stanotte **non riproduce** quello di §17.1 su due profili:

| profilo | §17.1 (binario `51b5994`) | giro nuovo (binario da HEAD) |
|---|---|---|
| `perdita-0,5` | 40,06 fps · 0 chiavi | ⛔ **19,27** fps · spirale rossa |
| `jitter-5` | 39,30 fps | **31,45** fps |
| `perdita-1` | 9,56 | 12,32 |
| `raffica-1` | 23,94 | 29,47 |

⛔ **Non lo liscio, e non scelgo quale sia buono.** Le differenze note fra i due giri sono almeno
tre — binario diverso (HEAD porta le righe `rete-quic`, cioè **una `registro_dice` in più al
secondo**), macchina **riavviata** in mezzo, e il terreno ricostruito. ⇒ `[?]` **Non so quale delle
tre.**

⭐ **Che cosa sopravvive comunque, perché non dipende dal punto esatto:** la forma è la stessa in
tutt'e due i giri — una linea sana a ~40 fotogrammi/s, un **dirupo** entro il primo punto
percentuale di perdita, la spirale di chiavi come meccanismo, e il jitter che morde **senza perdere
un pacchetto**. ⛔ Quel che **non** si poteva più dire era **dove** stesse il gradino.
⇒ ⭐ **Sciolta da §17.11**, e la risposta è più interessante della domanda.

### 17.9-sexies ⭐ LA RIVERIFICA DI `09-b79` — **nessun numero era sporcato**, e sono tre prove lette

`09-b79-cure.py:379` avvolgeva `RETE.root` invece della catena curata. ⚠ E **non bastava scrivere
`B70.root`**: quando b79 arriva, `B70.root` è **già** stato sostituito da `09-b76:416` con un
avvolgimento che a sua volta chiama `RETE.root`. ⇒ La catena si ricostruisce dai pezzi
(`RETE.rem(B70.catena_root(c))`), e se `catena_root` non c'è **il banco si ferma invece di
misurare**.

⛔ Ma i numeri di §17.6 **reggono**, e non per fiducia:

1. `[R]` **il difetto era ancora da riscuotere**: alle 19:00 `09-b70.root()` faceva ancora
   `return RETE.root(...)`; la cura è delle **19:41**, dopo. Avvolgere `RETE.root` era allora
   *identico*. Il difetto era **prospettico**;
2. `[R]` **la `riga0` c'era**: `09-b76` sostituiva già `righe_registro` con la sua, col redirect
   **dentro** `bash -c`. `[M]` E la firma nei dati lo conferma: su tutte e **36** le caselle
   `attese_a_vuoto` sta fra 1 973 e 2 156 — **costante, non in salita** (su `ritardo-30` A/B/C:
   2 015 / 2 006 / 2 016). Il cumulativo di b70 era 4 041 contro 1 604, **in salita**: qui non c'è;
3. `[R]` **il conto di un altro giro è strutturalmente impossibile**: `07-b64-terreno.sh:106` fa
   `: > registro.log` a ogni `accendi`, e questo banco **riaccende il server a ogni braccio**.
   `[M]` Controprova: nessuna coppia di caselle porta numeri identici dal registro, e tre caselle
   hanno detto «NIENTE DA LEGGERE» invece del numero del vicino — ⭐ prova che **nella finestra non
   c'era niente da rubare**.

⭐⭐ **E la divisione che conta**: `[R]` i predicati sulla spirale, sul ritmo e sulla linea sana
leggono **solo** dalla traccia §11.1 del cliente; dal registro vengono solo quattro numeri di
**corroborazione**. ⇒ *«la spirale si spegne solo col braccio C: 51,7-88,1 % → 0,0-5,6 %»*
**non passa dal registro**, e i cinque profili rossi non si rifanno.

**Rimisurato `ritardo-30` a tre bracci** — il predicato che vale più di tutti:

| braccio | fps | chiavi | deriva fine | deriva max |
|---|---|---|---|---|
| A | 39,94 | 0,0 % | 0,0 ms | 10,1 ms |
| B | 39,94 | 0,0 % | 0,2 ms | 11,0 ms |
| C | 39,32 | 0,0 % | −0,1 ms | 6,2 ms |

**S′ verde**, e regge il confronto con le 19:00 (39,85 / 40,19 / 39,63). ⭐ E le righe della spirale
del braccio A tornano **identiche** (`chiave_aspetta` 1, `delta_non_spedito` 5,
`abbandonato_in_coda` 1): **un numero cumulativo non si riproduce, questi sì.**

## 17.11 ⭐⭐⭐ DOV'È IL DIRUPO — *23 agosto, notte fonda*: **il gradino è DOPPIO**, e il prodotto è **bistabile**

`banchi/09-b80-dirupo.py` · **42 giri** · perdita **letta** da una sonda a **20 000 pacchetti** a
ogni casella (⛔ a 0,1 % otto pacchetti non misurano un decimo di punto) · denominatore girato in
**apertura e chiusura** (39,95 → 39,93, **0,1 %**: la macchina non è derivata) · macchina messa
ferma per nome prima di cominciare · cure spente per tutti e 42 i giri.

### 17.11-bis ⛔ Prima il metro, poi la misura — e il metro è grosso

⛔ **Non ha senso confrontare due giri se non si sa quanto vale il rumore fra due giri identici.**

| profilo | giri | escursione | semi-escursione |
|---|---|---|---|
| perdita **0,00 %** | 3 | 39,89-40,17 | **0,4 %** |
| perdita **0,50 %** | 3 | 28,16-36,70 | **14,8 %** |
| perdita **0,50 %** | 5 | 20,79-36,70 | **27,6 %** |
| perdita **0,75 %** | — | — | **46,6 %** |

⇒ La contraddizione di §17.9-quinquies vale il **35,0 %**: il rumore **non la spiega tutta, ma ne
copre i quattro quinti**.

⭐⭐ **E il fatto vero è qui**: la dispersione **cresce con la perdita** (0,2 → 8,5 → 23,8 → 46,6 %)
e **non col carico**. `[M]` la CPU è stata **3,7-4,7 %** in *ognuno* dei 42 giri, il carico 0,3-0,8
su 20 core. ⇒ L'ipotesi «macchina carica» è **esclusa**, e quel che resta è del prodotto:

> ⛔⛔ **vicino al bordo la spirale è BISTABILE.** `[M]` a **0,20 %** di perdita, stesso binario,
> stesso terreno, a venti minuti di distanza: **`0 chiavi · 40,16/s`** e **`24 chiavi · 33,84/s`**.

⇒ Non è una soglia: è un **punto di biforcazione**. Lo stesso ingresso dà due uscite, e quale delle
due dipende da come è andata la prima manciata di secondi.

> ⛔⭐⭐ **«BISTABILE» È LA PAROLA SBAGLIATA, e la correzione è in §21.2** — *24 agosto*. Non sono due
> rami fra cui il prodotto sceglie: è **un innesco a senso unico**, con una probabilità **costante**
> ogni secondo. I giri da 25 s non erano una moneta lanciata sul prodotto: erano **una moneta
> lanciata su quanto a lungo avevamo guardato**.

### 17.11-ter ⭐⭐⭐ IL GRADINO È DOPPIO, e le due metà stanno lontanissime

| | dove casca | che cos'è |
|---|---|---|
| **il MECCANISMO** — la spirale di chiavi (§3.3) | ⛔ fra **0,00 % e 0,10 %** di perdita vera, **su tutt'e due i binari** | cioè **al primo pacchetto perso** |
| **il SINTOMO** — sotto il pavimento di 25/s (§2.1) | fra **0,53 % e 0,75 %** (HEAD) · fra **0,27 % e 0,47 %** (`51b5994`) | cioè **cinque volte più in là** |

⛔⛔ **Questa è la scoperta, e cambia il modo di leggere tutta §17.1**: il difetto **non comincia
dove si vede**. Fra il primo pacchetto perso e il momento in cui l'utente se ne accorge c'è mezzo
punto percentuale di perdita in cui **il prodotto sta già degenerando in chiavi** — e la degradazione
è già *nello spazio e nel tempo insieme*, che §3.3 vieta — **mentre i fotogrammi al secondo dicono
ancora che va tutto bene**.

⇒ ⭐ **Un banco che avesse guardato solo i fotogrammi/s avrebbe dato verde fino allo 0,5 %.** La
colonna che dà l'allarme cinque volte prima è **la quota di chiavi**, ed è la ragione per cui §17.1
la porta accanto ai fotogrammi/s invece che al posto loro.

**La griglia fine (HEAD)** `[M]`:

| perdita vera | fps | chiavi | peggior secondo |
|---|---|---|---|
| 0,000 % | 39,95 | **0** | 37,5 |
| 0,100 % | 39,44 | 2,5 | 23,5 |
| 0,195 % | 37,00 | 12 | 21 |
| 0,253 % | 34,83 | 20,5 | 5 |
| 0,532 % | 27,29 | 48 | 4 |
| **0,748 %** | ⛔ **13,50** | 101,5 | 4 |
| 0,998 % | 7,23 | 119,5 | 3,5 |
| 1,475 % | 5,52 | 112,5 | 3 |

⭐ **E niente si è mai staccato, e la consegna non si è mai fermata** — copertura 1,00 e buco massimo
≤ 0,37 s **ovunque**, nemmeno a 1,5 %. ⇒ Il divieto di §3.3 regge; a cedere è la scala, non il filo.

### 17.11-quater ⛔ La forbice del primo giro è ritirata, e il binario non c'entra

**La forbice «0,36-0,94 %» di §17.1-bis è sbagliata** e §17.11 la ritira. Nasceva da un
`perdita-0,5` che aveva dato *40,06 fotogrammi/s con **zero** chiavi*. `[M]` **In 7 giri a ~0,5 % di
perdita vera, su tutt'e due i binari, le chiavi sono state 11, 47, 44, 72, 24, 112, 129 — mai zero.**
⇒ Quel numero **non si riproduce**: era il ramo fortunato della bistabilità, preso una volta e
scambiato per la regola.

**Il binario** — `HEAD` (`2954bf0`) md5 `dae98670…` contro `51b5994` md5 `760c6fd7…`, e fra i due
`src/` cambia in **un commit solo** (+412 righe, 0 tolte):
- ⛔ **sulla linea pulita non conta**: 39,95 contro 39,25 = **1,8 %**, dentro il metro.
  ⇒ `[M]` **il sospetto «la riga `rete-quic` costa» è REFUTATO**: una `registro_dice` in più al
  secondo non si misura;
- conta **solo dove c'è perdita**, e ⭐ **si incrocia**: HEAD rende di più sotto lo 0,5 % (37,0 contro
  29,1 a 0,2 %), meno sopra lo 0,75 %. ⚠ **Ma i rossi sopra lo 0,75 % poggiano su caselle la cui
  dispersione interna (46,6 %) supera il metro**: sono **indizi, non numeri**. Quelli a 0,2/0,3/0,5 %
  sono solidi e dicono tutti la stessa cosa;
- ⭐ e `51b5994` è **già dentro la spirale a ogni casella** (55-142 chiavi): per questo è *stabile* —
  **non ha un bordo su cui oscillare**.

## 17.10 Che cosa resta aperto dopo questa sezione

1. ⭐ **le cure contro la spirale sono MISURATE** (§17.6) e restano **spente**: I6 le tiene dietro
   l'interruttore finché l'utente non le ha guardate. ⇒ ❓ **decisione dell'utente**, e ha i due
   numeri che le servono — il ritmo guadagnato (1,7-2,8 volte) e il ritardo pagato (−38/+161 ms sui
   profili ordinari, 4,5 s su `raffica-forte`);
2. ⛔ **il 36 % di audio rifiutato da ngtcp2** su `casa-cattiva` (§17.2-quater): stessa finestra di
   congestione che nel video produce la spirale, e non è un difetto della cura del riordino;
3. ⭐ **`raffica-forte` è spiegato** (§17.1-quater): non si stacca nessuno, si ferma la consegna —
   `cwnd` a ~10 KB e 860 fotogrammi mai spediti. ⛔ Resta grave (schermo fermo) e **le cure lo
   curano**, ma il nome era sbagliato e il predicato è in cura;
4. ❓ **il fantasma di §17.5**: decisione dell'utente, non di una misura;
5. ⭐ **le cure ai banchi sono applicate e i banchi rifatti girare** (§17.9): nove difetti in tutto,
   ⛔ **tutti della forma «silenzio invece di rosso»**;
5-bis. ⭐ **la contraddizione fra le due griglie è sciolta** (§17.11): non erano due binari, era il
   prodotto che **vicino al bordo è bistabile**. ⛔ E ne è uscito il fatto più importante della
   sezione: **il gradino è doppio** — il meccanismo parte al **primo pacchetto perso**, il sintomo
   si vede **cinque volte più in là**;
5-ter. ⏳ **e la bistabilità non ha una spiegazione**: `[?]` perché lo stesso ingresso dia
   `0 chiavi · 40,16/s` oppure `24 chiavi · 33,84/s` non è stato indagato. È la prima cosa da
   guardare se si vuole curare il difetto **dove comincia** invece che dove si vede;
6. ⚠ **il riordino sugli stream resta senza testimone diretto** (§17.3): `dgram_falsi` vale
   sull'audio soltanto.

---

# §18 · ⭐⭐⭐ LE DUE CURE DECISE DAL REGISTA — *23-24 agosto 2026, notte*

> *«Ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps. Se in 10 secondi non
> arrivano più pacchetti è chiaro che la connessione è morta. […] se all'interno di un intervallo di
> 1-2 secondi c'è una perdita di pacchetti piuttosto copiosa direi di trattarla come il caso in cui
> la connessione è caduta.»*
> — ⇒ `DECISIONI.md` **§3.1-quater**, **§3.1-quinquies**, **§3.1-sexies**.

⛔ **Da dove nasce**: la scelta fra **due mali misurati** (§17.1, §17.6). Con perdita a raffiche
pesanti, **senza** le cure lo schermo si congela **14,26 s**; **con** le cure si muove ma con
**4,5 s di ritardo**. ⇒ L'utente ha deciso che **nessuno dei due va servito**: una linea così non è
lenta, è **rotta**. E alla domanda su che cosa veda, ha scelto fra tre: ✅ **il filo cade e si
rientra a mano** — non un riattacco automatico, non un ripristino invisibile.

⚠ **L'obiezione è stata fatta e superata**: *«su rete cattiva la diagnosi "è caduta la linea" è
frequente, e farla pagare con un accesso a mano rende il prodotto inusabile proprio dove serve»*.
⇒ Da lì nasce il prerequisito: **§18.3, il fantasma**.

## 18.1 ⛔⛔⛔ LA PRIMA GRANDEZZA ERA SBAGLIATA — e il banco l'ha refutata prima che uscisse

La cura fu scritta su `pkt_lost / pkt_sent` di ngtcp2 dentro una finestra: una frazione di perdita,
soglia **50‰ (5,0 %)**, tarata con due margini apparentemente comodi — 2,9× sopra il peggiore che
regge (`casa-cattiva`, 1,71 %) e 2,2× sotto quello che non serve nessuno (`raffica-forte`, 11,10 %).

⛔ **`banchi/09-b81-linea-morta.py` l'ha uccisa in dieci minuti** `[M]`:

| profilo | perdita **iniettata** (sonda) | perdita **DICHIARATA** da ngtcp2 | la linea |
|---|---|---|---|
| `casa-cattiva` | 1,86-2,15 % | ⛔ **512‰** (51,2 %) | **REGGE 10 minuti** — 9,60 fotogrammi/s, copertura 1,00, buco max 0,50 s, cliente attaccato a 599,99 s |
| `raffica-forte` | 12,28-14,00 % | **123‰** (12,3 %) | **non regge** — copertura 0,20, buco 30,06 s |

⛔⛔ **La grandezza ordina i due casi AL CONTRARIO**: la linea che **funziona** dichiara **quattro
volte più perdita** di quella che non funziona. ⇒ **Nessuna soglia le separa** — qualunque valore
lasci passare `casa-cattiva` (≥ 512‰) lascia passare anche `raffica-forte`; qualunque valore fermi
`raffica-forte` (≤ 123‰) ferma **prima** `casa-cattiva`. **Non era una taratura da rifare: era la
grandezza sbagliata.**

⭐⭐ **E la causa è il fatto centrale di questa fase, tornato addosso a noi.** `casa-cattiva` porta
`delay 40ms 20ms distribution normal`, e la sonda ci misura il **93,5 % di pacchetti fuori ordine**
con l'1,9 % di perdita vera. **ngtcp2 conta un pacchetto sorpassato come perso.** ⇒ `pkt_lost` su
una linea che riordina **misura il riordino**, non la perdita — ed è §3.1-ter che ci presenta il
conto: *avevamo scritto che il disordine viene scambiato per perdita, e poi ci abbiamo costruito
sopra una decisione*.

⚠ E non era l'avvio della connessione: tolte le prime dieci finestre, **399 su 399** restano sopra
soglia, mediana **524‰**, ininterrotto per dieci minuti.

⭐ **Il falsificatore era stato dichiarato `[?]` da chi ha scritto la cura**, prima che il banco
girasse: *«la soglia è sulla frazione **dichiarata**, mentre i due estremi sono la perdita
**iniettata** — con jitter e riordino la dichiarata può essere più alta»*. ⇒ È servito: il banco
sapeva **che cosa andare a rompere**, e l'ha rotto al primo giro.

## 18.2 ⭐⭐⭐ LA GRANDEZZA GIUSTA — **lo stallo dell'uscita**

⭐ **I dati la indicavano da soli**: `casa-cattiva` buco massimo **0,50 s**, `raffica-forte`
**30,06 s** — **sessanta volte**. ⇒ Quel che separa i due casi non è **quanto si perde**: è **se i
fotogrammi escono**.

> **la grandezza è: da quanto tempo non esce un fotogramma pur avendone da mandare**

Due contatori **locali e monotoni** (forma P8→P20 di `RCP.md`: un fatto osservabile, mai un
orologio) più un istante:

| | come si calcola |
|---|---|
| **«è uscito»** | i **byte di video consegnati a ngtcp2** in `coda_consegna()` — l'unico punto in cui i byte sono davvero dentro un pacchetto |
| **«avevo da mandare»** | coda video non vuota **oppure** `lm_offerti` salito (in `video_a_una()`, **prima** di freno, sgombero e rifiuto) |

⛔⭐ **Il secondo termine non è un di più, ed è la riga che rende la cura onesta**: senza
`lm_offerti`, **il regolatore del ritmo nasconderebbe lo stallo** — smette di produrre,
`video_sgombra()` abbandona i delta, la coda si svuota, e *«non ho niente da mandare»* diventa vero
**mentre lo schermo è fermo**. La cura si assolverebbe da sola proprio nel caso che deve prendere.

⛔ **E se non c'è niente da mandare il conto non parte nemmeno**: `[M]` in questa fase la scena ferma
consegna **1 fotogramma in 30 s e poi zero** — e non è un difetto, è `RecordVirtual` di Mutter che
consegna solo sul cambiamento (§13, il risveglio costa 13 ms). ⇒ Una cura che partisse lì
**butterebbe fuori chi guarda un desktop fermo**, che è il modo peggiore in cui potrebbe fallire.

⚠ **Si contano i byte, non i fotogrammi interi**, e la ragione è dichiarata: una chiave da ~60 000
byte su linea stretta può metterci secondi a uscire tutta, e a fotogrammi quei secondi sarebbero uno
«stallo» **mentre il filo lavora**. Un byte che parte è un filo che porta.

### 18.2-bis La soglia — **5 000 ms**, e i due margini col caso intermedio

| | stallo/buco più lungo | |
|---|---|---|
| tredici profili sani | 0,04-0,35 s | reggono |
| `casa-cattiva` | **0,50 s** | ⛔ **REGGE — non va dichiarata morta** |
| ⚠ `raffica-1` | **un secondo intero a zero** | ma consegna **23,94 fotogrammi/s**: regge benissimo |
| `raffica-forte` | **14,26 s** (30,06 nell'altro giro) | non regge |

⇒ intervallo **1,00-14,26 s**, centro geometrico **3,78 s**, scelta **5,0 s** — ⭐ **sopra** il
centro, apposta. Margine **5,0×** sopra il peggiore che regge, **2,9×** sotto quello che non serve.

⛔ **Il lato stretto usa il PIÙ CORTO dei due stalli di `raffica-forte`**, non il più lungo: un
margine scritto sul numero fortunato non è un margine.
⛔ **E l'asimmetria è voluta**: i due errori **non costano uguale**. Sbagliare in alto = qualche
secondo di schermo fermo in più. Sbagliare in basso = **buttare fuori uno che stava lavorando**, e
non si rimedia.
⚠ **Anche il campionamento sbaglia dalla parte buona**: il conto riparte dall'istante del giro
(≤ 1/s), non da quando i byte sono usciti davvero ⇒ lo `stallo_ms` misurato può essere fino a ~1 s
**più corto** del vero. Si scatta più tardi, mai più presto.

### 18.2-ter ⭐⭐ LA PROVA — *24 agosto 2026*, e il margine è **misurato**, non «non è scattato»

⛔ La riga esce **solo allo scatto**. ⇒ Un «non è scattato» non dice **quanto ci è mancato**: il
banco ribatte lo stesso profilo **con soglie sempre più basse** finché una scatta, e allora il
prodotto stampa il suo `stallo_ms`.

| profilo | stallo massimo | margine sulla soglia di 5 000 ms | buco al client |
|---|---|---|---|
| `ritardo-30` (sano) | < 500 ms | **> 10×** | 0,157-0,175 s |
| ⭐ `casa-cattiva` | < 500 ms | **> 10×** | 0,359-0,479 s |
| ⚠ `raffica-1` | **1 001 ms** | **5,0×** | 0,52-3,73 s |
| ⛔ scena **ferma** | *il conto non parte* | — | 1 e 3 fotogrammi in 90 s |

⭐ **`raffica-1` conferma la derivazione con un numero indipendente**: il lato stretto vale
**1,00 s**, esattamente quello del riquadro, e il margine sono i **5,0×** dichiarati.

**`casa-cattiva`, dieci minuti, cura accesa: ZERO SCATTI** — 9,71 fotogrammi/s, copertura **1,00**
(600 s su 600), buco massimo **0,479 s**, cliente attaccato a 599,88 s, nessun congedo.

⭐⭐ **E il confronto che chiude la refuta**, nello **stesso** giro: il **testimone** dice `permille`
mediana **529‰**, con **392 finestre su 392** sopra i vecchi 50‰. ⇒ **La cura vecchia avrebbe ucciso
questa identica sessione; la nuova non la tocca.** Stesso profilo, stesso banco, stessi dieci
minuti: cambia **solo la grandezza su cui si decide**. E dall'altro lato `raffica-forte` — quella
che *non* regge — dichiara `permille=133`, cioè **meno**.

**Lo scatto vero** `[M]`: `raffica-forte` (13,19 % iniettato) scatta a **18,95 s**, con
`causa=stallo stallo_ms=5008 · offerti=198 · usciti_byte=0 · coda_video=31146` — ⭐ **le due metà
tutt'e due vere**: avevamo da mandare, e non è uscito niente. E il filo cade.

**Il silenzio** `[M]`: `kill -9` ⇒ `silenzio_ms=10006`, `prove=12`, **10,24 s** dopo il colpo, e
nella stessa riga `stallo_ms=8 offerti=0` — ⭐ **le due cause restano separate**. A cura spenta,
zero scatti.

**La scena ferma** `[M]`: 90 s di desktop che non cambia, zero scatti alla soglia in vigore **e a
1 000 ms**, cioè cinque volte più stretta. ⭐ E la scena era ferma **davvero, verificato e non
sperato**: il conto del server dice 1 e 3 fotogrammi in 90 s, tutti spediti.

**I predefiniti (I6)** `[M]`: senza `--linea-morta`, zero scatti e zero sfratti, e i due profili
stanno nella griglia di §17.

⚠ **Una cosa da dire, e va nel verso prudente**: lo **stallo** (server: byte usciti) e il **buco**
(client: fotogrammi arrivati) **non sono la stessa grandezza**, e la soglia è derivata dal secondo
mentre la cura misura il primo. `[M]` su `raffica-1` un giro ha dato buco **3,73 s** con lo stallo
che non scattava nemmeno a 1 000 ms: **i byte partono, a mancare è la ritrasmissione**. ⇒ L'errore
va dalla parte buona, ma il numero della derivazione è **prudente, non esatto**.

### 18.2-quater ⛔ Che fine ha fatto il `permille` — da **giudice** a **testimone**

`--linea-morta-permille` è **tolta**: un'opzione che accetta un numero **senza usarlo** è peggio di
un'opzione che non c'è, perché chi la batte crede di aver tarato qualcosa. ⇒ Adesso si becca aiuto e
uscita 2.
⭐ Ma `permille=` **resta nella riga come testimone**: è la miglior misura di **riordino** che il
server abbia **sugli stream**, dove `dgram_falsi` (§17.3) non arriva. ⚠ E il banco verifica
l'**assenza** dell'opzione **battendola**, non con un `grep`: `[M]` la stringa nel binario c'è
eccome — sta nel testo d'aiuto — e il primo giro di quel controllo **ha dato rosso su un binario
giusto**.

## 18.3 ⭐⭐ LO SFRATTO DEL FANTASMA — e abbassare `SILENZIO` è stato scartato **su una misura**

⛔ La strada ovvia — portare `SILENZIO` da 30 s a 10 — **si rompe**, `[M]` 16 agosto: fra due
pacchetti autenticati di un **browser fermo ma VIVO** passano **15 004 / 15 005 / 15 002 ms**. È il
keep-alive del browser, non nostro. ⇒ A 10 s **ogni client che guarda e non tocca perde il posto a
ogni giro di keep-alive** — è la regressione già pagata il 16 agosto (*«una seconda scheda è entrata
e ha preso il desktop del primo»*).

⚠ **E `SILENZIO` ne governa altri quattro**: l'avviso a `SILENZIO/2` (passerebbe da «mai su una
sessione sana» a «su tutte»), il rilascio dei tasti premuti (⛔ un `Ctrl` tenuto giù durante una
pausa di rete di 12 s verrebbe rilasciato **sotto le dita**), l'ordine silenzio→inattività, e **tre
documenti** che dichiarano il numero all'utente.

⇒ **La strada scelta è più stretta e più mirata**: `--sfratto-ms N` (**0 = spento**, predefinito;
consigliato **15 000**). Scatta **solo quando qualcuno chiede quel posto**, mai da solo, e **solo fra
client dello stesso utente**.

⛔ **§8.2 non è violata, è applicata**: *«nessun client attaccato e **vivo** viene mai spodestato»* —
l'occupante qui è attaccato ma **non vivo**, e finora l'unico orologio che li distinguesse era quello
da 30 s. ⭐ `torna_a_parlare()` riparte **solo da `S_STACCATA`**: per questo lo sfratto cambia lo
**stato** e non si limita a togliere il posto, o il fantasma resterebbe `S_ATTIVA` senza posto.

`[M]` **Il fantasma scende del 48 %**: da **32,13 s e 14 rifiuti** a **16,83 s e 7 rifiuti**. ⭐ E con
la linea morta accesa scende a **~10 s con zero rifiuti** — il posto torna libero al primo tentativo.

**Due utenti diversi** `[M]`: zero sfratti, il secondo utente entra sul **proprio** posto con zero
rifiuti. ⚠ La riga `⛔ SFRATTO NEGATO` **non esce**, ed era previsto `[R]` prima di girare: il
registro dei posti è indicizzato per nome, quindi `POSTO_OCCUPATO` implica già «stesso utente» e quel
ramo non è raggiungibile. **La protezione la fa la struttura; il controllo esplicito resta come
rete** — il giorno in cui `MAX_ATTACCATE` diventa la tabella di un server multi-tenant sarebbe
l'unica cosa a reggere.

## 18.4 ⛔ E LA FRASE CHE MENTIVA

*«Quell'utente è già collegato da un altro dispositivo»* (`src/pagina.html`, `MOTIVO[0x0F]`) è una
**diagnosi che il server non è in grado di fare**: non sa se l'altro client è un altro apparecchio o
è lo stesso utente appena caduto. ⇒ Adesso dice **quel che sa** e dà il gesto:

> *«il posto di questa sessione risulta occupato da un altro client — se eri tu e sei appena caduto,
> riprova fra qualche secondo»*

⚠ **E conta più di prima**: dopo §3.1-quater **si rientra a mano**, quindi è la **prima frase che
l'utente incontra rientrando**.

## 18.5 ⚠ E un prezzo dichiarato per un caso che non esiste — corretto

I PING passano a metà della soglia quando la cura è accesa, e il costo era stato dichiarato in
**0,21 kbit/s** per sessione. ⛔ Il banco **non ha potuto isolarlo, e si è rifiutato di dare un verde
vuoto**: `[M]` una sessione «ferma» costa comunque **2 463 kbit/s** di audio PCM (§4.3, che non si
spegne — un `CIAO` senza codec audio comune si becca `0x09 NIENTE_IN_COMUNE`), cioè **11 727 volte**
quel numero; la differenza acceso−spento è **+0,539 kbit/s**, dentro il rumore.

⭐ **E il fatto vero**: `[M]` su una sessione viva il contatore **non si ferma mai per 0,6 s** ⇒ il
keep-alive **non ha mai occasione di scattare**, e quei 0,21 kbit/s descrivevano **un caso in cui il
prodotto non entra**. Un prezzo dichiarato per un caso che non esiste **è peggio di nessun prezzo**.

## 18.6 Che cosa resta, dopo §18

1. ⭐ **le due cure sono provate e restano SPENTE** (I6): `--linea-morta` e `--sfratto-ms`.
   ❓ **La decisione di accenderle è dell'utente**, e ora ha i numeri;
2. ⏳ **le cure contro la spirale** (§17.6) restano spente e aspettano **i suoi occhi**, che è l'unica
   cosa che non si può delegare a una misura;
3. ⏳ **la bistabilità** di §17.11 non ha ancora una spiegazione;
4. ⛔ **il 36 % di audio rifiutato da ngtcp2** su `casa-cattiva` (§17.2-quater) non ha ancora una cura;
5. ⚠ **lo stallo e il buco non sono la stessa grandezza** (§18.2-ter): la derivazione è prudente, non
   esatta, e un giro che le misuri **insieme** la renderebbe esatta.

---

# §19 · ⭐⭐⭐ IL GIUDIZIO DELL'UTENTE SUL PERCORSO VERO — *24 agosto 2026, mattina*

⛔ **È la sezione che conta più di tutte le altre**, e per la ragione scritta in testa al documento: in
v1 la fase omologa fu validata con PSNR, SSIM e l'occhio dello sviluppatore, e il giudizio
dell'utente sul desktop vero fu *«siamo tornati indietro»*. **La fase fu azzerata.**

**Il banco**: sessione vera dell'utente, browser sul **portatile** (192.168.0.3, WiFi `wlo1`), server
sulla macchina di prova, porta **7920**, binario `2792271f…` dall'albero di lavoro, tela
**2544×926**, ⛔ **tutte le cure spente**, trappola di glibc **spenta** (il server gira alla velocità
vera).

⭐ **E la rete si è sporcata dal lato del CLIENTE**, non del server: il video arriva in **ingresso**
su `wlo1`, quindi il guasto sta su un `ifb0` con `netem`, alimentato da un filtro `u32` sulla **sola
porta UDP 7920 in arrivo**. ⛔ Sulla macchina di prova lo stesso traffico passerebbe da `enp7s0`,
dove passa l'ssh, e quella non si tocca. L'ssh è TCP sulla 22 e non è filtrato.
⚠ E il guasto **si disarma da sé** dopo N secondi, con un guardiano staccato: la stessa disciplina
già usata su `lo`.

## 19.1 ⭐⭐⭐ LA SCALA, E VIENE DAI SUOI OCCHI

| perdita **misurata sul filo** | il suo giudizio |
|---|---|
| 1 % | *«mi sembra ok»* |
| **5,6 %** | *«è tutto fluido»* |
| ⛔ **10 %** | *«adesso si è bloccato»* |

> ⇒ **Il confine dell'uso reale sta fra il 5 e il 10 per cento di perdita.**

⛔⛔ **E questo CONTRADDICE il banco, di un ordine di grandezza.** §17.11 mette il dirupo dentro il
primo punto percentuale: la spirale di chiavi parte allo **0,10 %** e il ritmo casca sotto il
pavimento allo **0,53-0,75 %**. `[M]` Sul percorso vero, al **5,6 %** — cioè da **sette a
cinquantasei volte** più perdita — l'utente non se ne accorge.

## 19.2 ⛔ E LA PROVA È STATA RIFATTA DUE VOLTE, PERCHÉ LA PRIMA NON MORDEVA

⚠ **Va scritto perché è un errore di metodo mio, ed è il terzo della stessa famiglia** (dopo il
video pieno di grana di §16.4 e i nove «attesi» mai confrontati di R13): un giudizio su una prova che
non sollecita non è un giudizio.

`[M]` **Primo giro, e non valeva**: perdita all'1 % accesa e verificata (il server la vedeva:
*«la linea perde»*, 27 pacchetti dichiarati persi, 22 datagram audio perduti), **zero fotogrammi
abbandonati su 920**, **due chiavi in tutto**. ⇒ Nessuna spirale — ma la ragione era nel numero che
non stavo guardando: ⛔ **i suoi fotogrammi pesavano 242-283 byte.** Duecento byte. Il banco crollava
su una scena che riempiva il filo con 3 Mbit/s; qui la perdita **non aveva niente da rompere**.

`[M]` **Secondo tentativo, il trascinamento di una finestra**: fotogrammi fino a **3 801 byte**,
**zero chiavi** su 400, **2 abbandoni su 2 181**. ⇒ Ancora insufficiente: il banco lavorava su
fotogrammi **sette volte più grossi**.

`[M]` **E al 5 % il primo giudizio è stato RITIRATO prima di scriverlo**, contando i pacchetti
passati davvero dentro il guasto: **221, con 18 buttati**. ⛔ Diciotto pacchetti non sono una prova.
⇒ Rifatto con **trenta secondi senza mai fermarsi**, e allora sì: **7 596 pacchetti nel guasto, 423
buttati = 5,6 % reale**.

⭐ **Il numero che rende valido il giro buono** — e che mancava ai due precedenti: fotogrammi fino a
**77 304 byte**, cioè ⭐ **tre volte più grossi di quelli su cui il banco crollava**. Con quelli:
**chiavi 3,8 %** (23 su 600), **abbandoni 11 su 3 017** (0,36 %), e il giudizio *«è tutto fluido»*.

⛔ **La lezione, e vale oltre questa fase**: il gradino non lo decide la perdita, lo decide **quanto
la scena chiede**. Il banco produce una sollecitazione che pretende **quaranta fotogrammi al secondo
di cambiamento continuo**; un desktop vero — anche mentre si trascina una finestra — cambia **a
strappi**. ⇒ **Non è la stessa sollecitazione**, e le previsioni del banco **non si applicano al
prodotto così com'è usato**.

## 19.3 ⭐⭐ IL BLOCCO AL 10 %, COLTO NELL'ISTANTE — e il meccanismo è quello di §17.1-ter

`[M]` Nel momento in cui l'utente ha detto *«si è bloccato»*, il registro del server diceva:

| | |
|---|---|
| **`cwnd = 2 888 byte`** | ⛔ la finestra di congestione **collassata a due pacchetti** — dieci volte meno del minuto prima |
| `cwnd_left = 2 888` · **in volo = 0** | ⛔⭐ **non è che il filo sia pieno: non c'è NIENTE in volo.** Il server *potrebbe* mandare, e non manda |
| **27 fotogrammi `NON SPEDITO`** | e il contatore dei consegnati **fermo a 3 117** su tre letture di fila |
| chiavi | salite da 4 a **16** |
| `persi=664` · `dgram_persi=493` | `giudizio=⛔ la linea perde` |

⇒ ⭐ **È esattamente la catena di §17.1-ter, vista sul percorso vero**: la finestra si chiude → i
fotogrammi non partono → si chiedono chiavi → lo schermo si ferma. Il meccanismo del banco **è
giusto**; sbagliato era **dove** lo collocava.

⭐⭐ **E `cwnd_left = cwnd` con «in volo = 0» è la firma che assolve il filo e accusa noi**: non è
congestione osservata, è il pacer che rifiuta. È lo stesso quadro di `raffica-forte` (§17.9-quater,
`cwnd` mediana 8 948 B, `cwnd_left` mediana 0) su una linea vera.

## 19.4 ⚠ E DUE COSE CHE QUESTA SESSIONE NON HA POTUTO PROVARE

1. ⛔⛔ ~~**Le applicazioni che il coordinatore avvia non arrivano sullo schermo dell'utente.**~~
   → **ERRATA, e la correzione è in §20.1.** `[M]` `mpv` **arriva eccome** — 241 fotogrammi in 8 s
   su un banco controllato. Quando l'ho giudicato *«non arriva»* ⛔ **non c'era nessun cliente
   attaccato**: il server non spediva, e il contatore era fermo **per costruzione**. I «167 byte»
   erano gli ultimi valori di prima.
   ⚠ **Ho giudicato con un metro che in quella scena non poteva dire niente**, ed è la stessa ferita
   di §19.2 — la terza volta in due giorni. **Firefox** invece è rotto davvero, ma `[M]` **anche
   fuori da REMOTIX**: non è nostro (§20.1).
2. ⭐ **Le cure sono state provate a occhio** ⇒ **§19.6**, e il verdetto è che **fanno quel che
   promettevano e non basta**.

## 19.6 ⭐⭐⭐ LE CURE, GUARDATE — **fanno quel che promettevano, e non basta**

`[M]` 24 agosto, stessa sessione, stesso binario, **stesso 10 % di perdita**, e a cambiare **solo
gli interruttori del server** — verificati dalle righe d'avvio, non dalla riga di comando: soglia
della coda **100 ms**, regolatore del ritmo **ACCESO**, ⛔ **linea morta e sfratto SPENTI di
proposito** (se il filo cadesse non si saprebbe se è merito o colpa delle cure).

Perdita **misurata sul filo**: 8 597 pacchetti passati, **905 buttati = 10,5 %**.

| | **senza** cure | **con** le cure |
|---|---|---|
| fotogrammi consegnati | ⛔ **fermi** — stesso numero su tre letture di fila | ⭐ **continuano**: 1533 → 1552 → 1557 |
| fotogrammi mai spediti | **27**, in una raffica | ⭐ **1** |
| `cwnd` | 2 888 B | 3 652 B |
| chiavi | 16 | 17 |
| **il giudizio dell'utente** | *«si è bloccato»* | ⛔ *«si è bloccato»* |

⭐ **Le cure fanno esattamente quel che il banco prometteva**: senza, la consegna si **ferma**; con,
va avanti a **cinque-venti fotogrammi al secondo**, e i fotogrammi mai spediti passano da 27 a **1**.
Il meccanismo è curato.

⛔⛔ **E non basta.** Per chi guarda, cinque fotogrammi al secondo con quel ritardo **sono un blocco
lo stesso**. ⇒ Il numero migliora e **l'esperienza no**, ed è precisamente la distinzione che questa
fase esisteva per proteggere (v1: *«siamo tornati indietro»* su numeri che erano migliorati).

⭐⭐⭐ **E questo è l'argomento più forte a favore di §3.1-quater**, la decisione presa dall'utente
la notte prima **senza avere questo numero**: al 10 % di perdita **non esiste una versione buona** —
o lo schermo si ferma, o si muove in un modo che l'utente chiama **comunque bloccato**. ⇒ *«Nessuno
dei due va servito»* non era una preferenza: era la lettura giusta, e adesso ha la prova.

**La scala completa, tutta dai suoi occhi:**

| perdita reale | **senza** cure | **con** cure |
|---|---|---|
| 1 % | *«mi sembra ok»* | — |
| 5,6 % | *«è tutto fluido»* | — |
| **10 %** | ⛔ *«bloccato»* | ⛔ *«bloccato lo stesso»* |

### 19.6-bis ⚠ E DUE COSE VISTE DI PASSAGGIO, che non erano nel programma

1. ⭐ **La regola dei sessanta minuti ha scattato su una sessione vera, ed è la prima volta.**
   `[M]` *«prova2 non tocca niente da 3 600 012 ms (tetto 3 600 000) — CHIUDO la sessione grafica»*
   (`DECISIONI.md` §4.8). Ha chiesto l'uscita gentilmente e, **dopo dieci secondi**, l'ha chiusa a
   forza (`Logout 1` → `Logout 2`). ⚠ E ha prodotto un falso allarme: l'utente ha visto lo schermo
   fermo e ha detto *«il server è ancora bloccato»* — ⛔ **non lo era**: `NRestarts=0`, acceso da
   un'ora e mezza, e il solo core presente era di **ieri**.
2. ⛔⭐ **«Sessione viva e muta» è indistinguibile da «programma morto», e l'utente l'ha dimostrato
   di persona** — due volte, dicendo *«si è bloccato»* e *«il server è ancora bloccato»* di un
   server che stava benissimo. ⇒ È lo stesso fatto di §17.1-quater e §17.9-quater visto **dall'altro
   lato**: là il banco chiamava «stacco» una consegna ferma, qui l'utente chiama «server bloccato»
   la stessa cosa. ⭐ **Ed è la ragione per cui la cura della linea morta serve**: non perché
   migliori l'immagine — non può — ma perché **dice la verità** invece di lasciare uno schermo fermo
   che sembra un guasto del programma.
   ⚠ E la sessione **si riprende da sé**: `[M]` tolta la perdita, `cwnd` risale da 2 888 a
   **46 412 byte** (sedici volte) senza che nessuno tocchi niente.

## 19.5 ⭐ Che cosa questa sezione cambia nelle decisioni

1. ⭐⭐ **Le cure servono, ma non per il lavoro quotidiano dell'utente.** `[M]` Fino al 5,6 % di
   perdita il prodotto **così com'è** è giudicato fluido. ⇒ Le cure servono al **caso a raffiche** e a
   **chi guarda video**, non a chi lavora. ⚠ È un buon motivo per accenderle **con calma**, e non di
   corsa — e I6 resta rispettata senza costi;
1-bis. ⛔ **E al 10 % non salvano l'esperienza** (§19.6): curano il meccanismo — consegna che continua
   invece di fermarsi, fotogrammi mai spediti da 27 a 1 — ma il giudizio dell'utente **non cambia**.
   ⇒ Sopra una certa perdita **la scala di degradazione non ha più niente da offrire**, e l'unica
   risposta onesta è §3.1-quater: dichiarare la linea morta;
2. ⛔ **Il pavimento di banda (§3.1-sexies, 30 Mbit/s) non c'entra niente con tutto questo.** `[M]`
   Nel giro buono i fotogrammi grossi arrivavano a 77 KB e la linea non era mai satura: quel che si
   chiudeva era la **finestra di congestione**, non la banda. ⇒ ⭐ **§3.1-ter riceve la sua conferma
   più forte**: la banda è una premessa, la grandezza che decide è la **qualità** del filo;
3. ⚠ **e le soglie del banco vanno lette per quel che sono**: `[M]` misure su una sollecitazione
   **dieci volte più severa** dell'uso reale. Non sono sbagliate — sono un **caso peggiore**, e va
   scritto accanto a ogni numero di §17 che qualcuno potrebbe prendere per una promessa.

---

# §20 · ⭐⭐⭐ I PUNTI APERTI, CHIUSI — *24 agosto 2026*

⛔ **E due dei quattro hanno demolito una premessa che questo documento dava per buona.** Si scrive
la correzione, non si liscia.

## 20.1 ⛔⛔ «LE APPLICAZIONI NON ARRIVANO SULLO SCHERMO» — **era falso, ed era mio**

`banchi/09-b82-mostra.sh` · binario `b86cf6df…` dall'albero di lavoro.

⭐ **`mpv` arriva eccome.** `[M]` Con **solo** `XDG_RUNTIME_DIR` + `WAYLAND_DISPLAY`: **241
fotogrammi in 8 s, 38 513 byte medi**. Con `systemd-run --user` (la strada del menu): **317**. E
`WAYLAND_DISPLAY` **c'era già** nell'ambiente del gestore d'utente — ce lo scrive GNOME.

⇒ ⛔ **La causa vera del caso di stamattina: non c'era nessuno che guardava.** `[M]` Il registro
della 7920, minuto per minuto:

```
08:33   765 fotogrammi ·  49 battiti rete-quic
08:34   708 fotogrammi ·  59 battiti
08:35   228 fotogrammi ·  60 battiti
08:36    13 fotogrammi ·  31 battiti   ← il cliente se ne va
poi     NIENTE, solo «il legame regge» ogni minuto
```

Senza un cliente attaccato il server **non spedisce**, il contatore è fermo **per costruzione**, e i
«167 byte» erano gli ultimi valori di prima. ⚠ **Ho giudicato in una scena in cui il metro non
poteva dire niente** — la terza volta in due giorni (§19.2, §16.4).

**Le tre ipotesi che avevo scritto sono tutte cadute** `[M]`: un solo compositore e un solo
`wayland-0` (⚠ la data del 23 agosto che avevo letto era quella di `bus`, non del socket); **un
monitor solo**, `Meta-0` «Virtual remote monitor» 2544×926 scala 1,000; l'ambiente **non** era
incompleto.

### 20.1-bis ⛔ E ANCHE IL METRO ERA SBAGLIATO — i byte non dicono quel che credevo

`[M]` Calibrazione su finestre di 8 s:

| scena | fotogrammi | byte medi |
|---|---|---|
| desktop fermo | 0-1 | 238-283 |
| ⛔ una **bandiera a schermo intero** | **321** | **268** |
| `film-grana.webm` | 226 | 18 600 |
| `duro.mp4` | 240 | 37 081 |

⇒ **Una finestra viva a schermo intero può produrre fotogrammi da 268 byte, cioè quanto un desktop
fermo.** ⭐ **Il verdetto è il CONTO, non i byte**: i byte dicono *quanto* cambia, il conto dice *se*
cambia. ⚠ E in §19.2 avevo usato i byte come metro: quel ragionamento regge sul merito (i suoi
fotogrammi *erano* piccoli) ma il metro giusto era un altro.

### 20.1-ter ⛔⛔⛔ ~~Firefox è rotto — e non è nostro~~ → **REFUTATA il 25 agosto 2026**

> ## ⛔⛔⛔ QUESTA SEZIONE È SBAGLIATA, E LA PROVA CHE LA CHIUDEVA ERA VIZIATA
>
> *Refutata nella fase 10, `fasi/10-multi-tenant-e-il-budget.md` §5.10.* ⭐ **Firefox non è mai stato
> rotto su questa macchina.**
>
> ⛔ **La causa vera**: `~/.cache` è un **collegamento a `/tmp`** (da `/etc/skel`, immagine base del
> 30 luglio). Firefox tiene il profilo *locale* sotto `$HOME/.cache/mozilla` = **`/tmp/mozilla`**, e
> `[M]` **`/tmp/mozilla` appartiene a `prova2`, modo `0700`, creata il 23 agosto alle 08:03** — cioè
> **prima** di tutte le misure di questa sezione. ⇒ Per ogni altro utente il profilo **non nasce**.
>
> ### ⛔⛔ E il difetto di METODO è nel «controllo che chiude la questione»
>
> Diceva: *«`firefox --headless --screenshot` come **`nicfio`** — nessuna sessione REMOTIX, nessun
> Wayland, nessun monitor — **si pianta uguale**»*.
>
> ⇒ ⛔ **Ma `nicfio` ha lo STESSO `~/.cache -> /tmp`**, e quindi lo stesso `/tmp/mozilla` di
> `prova2`. `[M]` Verificato il 25 agosto: `lrwxrwxrwx nicfio -> /tmp`, e dentro
> `drwx------ prova2 prova2`.
>
> ⭐⭐ **Il controllo CONDIVIDEVA il fattore che avrebbe dovuto escludere** — e un controllo così non
> controlla niente: mostra lo stesso guasto per la stessa ragione, e chi lo legge conclude *«allora
> non è la sessione»* quando invece **non era mai stata in prova la sessione**.
>
> ### ⭐ La rimisura, con la sola cosa cambiata
>
> `~/.cache` di `nicfio` rifatta **cartella vera**, e **niente altro** — stesso comando, stessa
> macchina, stesso Firefox:
>
> | | fase 9, 24 agosto | ⭐ 25 agosto, dopo |
> |---|---|---|
> | `firefox --headless --screenshot` come `nicfio` | ⛔ **si pianta**, ucciso a **60 s**, profilo vuoto | ⭐ **`rc=0`**, e uno scatto da **5,5 MB** |
>
> ⚠ **Restano veri i due indizi in fondo alla sezione** (*«More than 1 GPU vendor detected»*, la
> Radeon recintata): ⛔ **sono avvertimenti, non la causa** — la stessa riga esce anche adesso, col
> browser che funziona.
>
> ⭐ **E quel che resta di giusto**: *«il difetto c'è, la diagnosi no»*, scritto qui in fondo il 24
> agosto. ⇒ **Era la frase esatta**, ed è quella che andava seguita invece di chiudere con un ✅.

### ~~20.1-ter~~ *(il testo originale, conservato)* ✅ Firefox è rotto — **e non è nostro**

`[M]` Firefox `140.14.0esr`: vivo (80 thread, 126 MB), **zero fotogrammi dopo 90 s**, mai attaccato
al socket Wayland. Fallisce identico da `systemd-run --user`, con `--profile` esplicito, con
`MOZ_CRASHREPORTER_DISABLE`, `MOZ_DISABLE_GPU_PROCESS`, `LIBGL_ALWAYS_SOFTWARE`,
`MOZ_ENABLE_WAYLAND=0`, sandbox spente.

⭐⭐ **Il controllo che chiude la questione**: `firefox --headless --screenshot` come **`nicfio`** —
nessuna sessione REMOTIX, nessun Wayland, nessun monitor — **si pianta uguale** e viene ucciso a
60 s col profilo vuoto. ⇒ **Firefox è rotto su questa macchina per tutti, dentro e fuori REMOTIX.**
Non è un difetto del prodotto, e §14.7/§16.5 vanno lette così.

⚠ Due indizi per chi lo riprenderà: `[GFX1-]: More than 1 GPU vendor detected via PCI, cannot deduce
vendor` (Intel `0x8086/0x4680` + AMD `0x1002/0x73bf`), e `/dev/dri/renderD129` è del gruppo
`remotix-nogpu` — la scheda AMD è recintata **apposta** (§4.6-ter).
⭐ E il `[M]` del 23 agosto (*«il profilo non viene mai creato in `~/.mozilla/firefox/`»*) guardava
**il posto sbagliato**: Debian `firefox-esr` usa `~/.mozilla/firefox-esr/`. ⚠ Anche quella resta
vuota — il difetto c'è, la diagnosi no.

### 20.1-quater ⭐ Lo strumento che mancava — `banchi/09-b82-mostra.sh`

Lancia un comando dentro la sessione di un utente con `systemd-run --user` (cioè in `app.slice`,
dove finirebbe scegliendolo dal menu), poi **conta i fotogrammi prima e dopo e dà il verdetto su quel
numero** — ⛔ mai su *«il processo è vivo»*. Quattro guardie: un compositore solo · un monitor solo e
nostro · l'ambiente **letto** da `systemctl --user show-environment` invece che inventato · e
⭐⭐ **G4: c'è qualcuno che guarda?** — zero battiti `rete-quic` ⇒ **nessun verdetto**.

⭐ **G4 è nata da un rosso su codice giusto**, ed è la guardia che avrebbe evitato le tre prove
bloccate di stamattina. Provata nei tre versi: `mpv` 240 contro 0 (verde) · `gnome-terminal` 40
contro 1 (verde) · `firefox` 0 contro 1 (rosso) · senza cliente, **si rifiuta di giudicare**.

⛔ **E non c'era niente da curare in `src/`**: il figlio prepara la sessione bene — un compositore, un
monitor, scala 1,0, ambiente completo. La cura era **nel modo di giudicare**.

## 20.2 ⛔⛔⛔ L'AUDIO — la premessa era falsa, e sotto c'era di peggio

### 20.2-bis ⛔ «Il 36 % dell'audio non raggiunge il filo» era una proprietà **del banco**

`[M]` Il registro della 7920, **quattro attacchi su quattro** della sessione vera dell'utente:
`negoziato … audio.codec=opus` → `canale audio ACCESO — codec 1 (Opus)`.

⇒ ⛔ **L'utente non è mai stato su PCM.** `[R]` Il PCM lo impongono **i banchi**: `09-b68:191`,
`09-b70:1890`, `09-b71:144`, `09-b77:978`, `09-b81:2294` passano tutti `--audio-codec pcm`.
⇒ **§17.2-quater e §18.5 vanno lette così**: il 36 % di rifiutati e i 2 463 kbit/s sono proprietà di
una **configurazione di banco**, non del prodotto in uso.

### 20.2-ter ⭐⭐⭐ E QUEL CHE C'ERA SOTTO: **si spendono 589 kbit/s per portare 1,2 kbit/s di silenzio**

`[M]` Che cosa viene rifiutato, sulla sessione **vera**: `datagram di 16 byte` = 1 (prefisso) + 12
(§6.3) + **3 di carico**. Riprodotto sul banco: `codec 1 (Opus), 3 byte di carico`, 1 248 su 1 248, e
`suono.c` dice **`PICCO 0 su 32767`**. ⇒ **Si rifiuta il silenzio digitale.**

`[M]` A desktop fermo, Opus: **48,0 datagram al secondo su 48,4 pacchetti** — il filo è *tutto*
audio — e ogni pacchetto è **pieno**, 1 441 byte su 1 452, per il `PADDING`.

**La cura** (`src/audio.c`, ⛔ nasce **spenta**, I6): un blocco in cui **tutti** i campioni sono
esattamente zero **non diventa un datagram**. ⭐ La ragione per cui è lecito: §6.3 mette l'`istante`
in ogni blocco e chi riceve lo rimette al posto assoluto ⇒ **un blocco non spedito è un buco, e un
buco è silenzio** — che è esattamente quel che quel blocco conteneva. ⛔ Nessuna soglia: **solo lo
zero digitale**, l'unico caso in cui «spedito» e «non spedito» suonano identici.

| desktop fermo, Opus | sul filo | pacchetti/s | datagram/s | byte/pacchetto | carico utile |
|---|---|---|---|---|---|
| **spenta** | 557,6 kbit/s | 48,4 | 48,0 | 1 441 | 1,18 kbit/s |
| ⭐ **accesa** | **5,5 kbit/s** | 0,5 | 0,0 | — | 0,00 |

⇒ ⭐⭐ **102,1 volte**, e 1 248 blocchi taciuti su 1 248. **Oggi una sessione ferma spende 589 kbit/s
per portare 1,2 kbit/s di silenzio: il 99,8 % è riempimento.**

**Il controllo che protegge l'utente** (tono a 440 Hz nel sink, giudice di `07-b42`): copertura
**1,0000 → 0,9996**, purezza del tono **1,000 → 1,000**, blocchi taciuti **1 su 5 001** — e quell'uno
precede i primi campioni. ⚠ Prezzo dichiarato: i `mancati` del cliente vanno da 0 a 2 (un buco voluto
lascia lo stesso salto di `istante` di uno perso).

⚠ L'interruttore oggi è **di compilazione** (`-DAUDIO_SILENZIO_PREDEFINITO=1`): il codificatore vive
nel figlio, che è un `execve` con l'ambiente composto **da zero** (`figlio.c:1145`). ⏳ La riga di
comando che manca (`main.c` → coda di `argv` in `figlio.c`) è **descritta e non scritta**.

### 20.2-quater ⛔ DUE DIFETTI TROVATI STRADA FACENDO, e nessuno dei due era cercato

1. ⛔⭐ **`WT_DGRAM_RIMANDI_MAX` non misura quel che il suo commento dichiara.** `[R]`
   `w->dgram_rimandi` è un campo di `struct wt`, cioè **della connessione**: sale a ogni passata
   rifiutata e torna a zero solo su un successo. Il commento accanto dice *«quante passate di fila
   **il blocco in testa** è stato rimandato»* — ⛔ ma la testa nel frattempo è stata sostituita
   decine di volte. ⇒ **Non misura l'età del blocco: misura da quanto la connessione non spedisce
   nulla.** `[M]` Ed è per questo che il primo rifiuto è avvenuto **a finestra aperta**
   (`cwnd_left = 7 424`, e la riga stessa dice *«NON è la congestione»*).
   ⭐ E i rifiuti sono **a raffica, non sparsi**: fuori dalla raffica 0,004 %, **dentro 100 %** — 100
   rifiuti ogni 2,00 s = ogni blocco prodotto, per venti secondi. Non click sparsi: **venti secondi
   di niente**.
2. ⛔ **«L'audio non dev'essere affamato dal video» NON È SCRITTO DA NESSUNA PARTE.** `[R]` Cercato
   in `SPECIFICHE.md` (§10 e gli invarianti), `RCP.md` §6.3, `DECISIONI.md`, `CODER.md`: **niente**.
   L'unico posto in cui la domanda è decisa è il codice — `wt_scrivi():7286`, *«I DATAGRAM PRIMA
   DEGLI STREAM»*. ⇒ ⚠ **Una decisione presa nel codice e mai messa a verbale**, ed è precisamente
   il genere di cosa che questa fase esiste per scoprire.
   `[M]` E oggi vince **l'audio**: a desktop fermo il filo è tutto suo; sulla sessione vera col
   desktop in movimento tocca il **25-33 %** dei pacchetti.

### 20.2-quinquies ⛔ E UNA PREVISIONE DELL'AGENTE CHE NON HA RETTO — scritta com'è

`casa-cattiva`, scena col tono, stesso `netem`, cura spenta:

| codec | sul filo | spediti | rifiutati | ‰ | **copertura** |
|---|---|---|---|---|---|
| PCM | 1 024,5 kbit/s | 3 135 | **1 880** | **375‰** | 0,6088 |
| Opus | 366,3 kbit/s | 1 127 | **126** | **101‰** | **0,8803** |

⭐ La copertura sale **0,61 → 0,88** (+27 punti di audio che arriva davvero). ⛔ Ma il predicato
chiedeva *«Opus sotto 20‰»* e ha dato **rosso**: Opus divide il rifiuto per 3,7, **non lo toglie**.
⇒ **Il codec è la cura del costo, non del rifiuto.** Il confine è stato lasciato dov'era e il rosso
scritto nel banco, invece di ritarare la soglia dopo aver visto il numero.

### 20.2-sexies ⏳ La mezza cura descritta e non scritta — il `PADDING`

`dgram_scrivi_uno()`, righe **1613** e **1647**: `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING` va
**condizionato** al fatto che ci sia davvero un lotto da comporre (più di un datagram in coda, o byte
di video da infilare). Con **un** datagram solo e la coda video vuota il lotto GSO è di un pacchetto
e il riempimento **non compra niente** — costa 1 425 byte su 1 441. ⛔ **Non si toglie, si
condiziona**: il riquadro di `:1581` spiega perché c'è (un primo pacchetto corto fa collassare il
lotto GSO).

## 20.3 ⭐⭐⭐ IL DISALLINEAMENTO AUDIO-VIDEO — il numero regge, **la lettura no**, e si sente

`banchi/09-b85-*` · binario `64258ca4…`. ⛔ **E il metro è stato certificato prima di misurare
qualunque cosa**, in tre gradini, nessuno saltato.

**(a) sul file**, 7 sfalsi noti iniettati con `-itsoffset`: ritrovati **−700,0 · −300,0 · −100,0 ·
−0,0 · +100,0 · +300,0 · +700,0**. **(b) ricampionato a 40/s**, 4 fasi: bias **−2,3 ms**, ampiezza
**4,0 ms**. **(c) ⭐⭐ attraverso il prodotto vero**, lo stesso film con l'audio spostato di ±300 ms
noti, suonato nella sessione e ripreso dal filo:

| messo | ritrovato (n=23) | errore |
|---|---|---|
| **+300** | **+288,5** | −11,5 |
| **0** | **−12,6** | −12,6 |
| **−300** | **−310,8** | −10,8 |

⇒ **pendenza 0,9988, costante −11,6 ms.** Il metro ritrova quel che si sa di aver messo, col segno
giusto, su tutta la catena.

### 20.3-bis ⭐⭐ IL PRODOTTO È PULITO — **niente +331, niente +690, in nessun caso**

`[M]` 24 agosto (segno: **positivo = il suono esce DOPO l'immagine**, la convenzione di
`pagina.html:6398`):

| caso | fps | Mbit/s video | **sfalso alla sorgente** | **sfalso in rete** | rete p90 |
|---|---|---|---|---|---|
| fermo | 40,1 | 0,30 | **−12,6** (n=23) | −5,8 | −3,9 |
| sotto carico | 35,1 | **106,5** | **−7,8** (n=22) | −14,7 | −16,6 |
| perdita 1 % | 36,5 | 0,30 | **−12,7** (n=22) | −6,1 | −9,8 |
| perdita 5 % | 16,2 | 0,60 | **−17,2** (n=10) | −19,1 | **−94,9** |

⇒ **Tutti e quattro entro ±6 ms dalla costante certificata.** Il prodotto marca i due flussi con lo
stesso orologio e li marca bene: **lo sfalso non nasce prima del browser.**

⭐ **E l'ipotesi «con la perdita peggiora» è smentita sulla mediana**, confermata solo sulla coda: a
5 % la latenza video p90 va a **118,5 ms** contro 23,6 dell'audio (gli stream ritrasmettono, i
datagram no) ⇒ **−94,9 ms**, cioè **l'audio che corre avanti**, non l'audio che resta indietro.
⚠ E metà delle claquette sparisce: **11 lampi su 20 click**.

### 20.3-ter ⭐⭐⭐ IL +331 NON È UN ARTEFATTO: **è il cuscino dell'audio, ed è scritto nel prodotto**

`[R]` `src/pagina.html:5563` `AUDIO_CUSCINO_MS = 250` · `:5564` `AUDIO_CUSCINO_MAX_MS = 600` ·
`:5761` `aoff = (perf − ist/1000) + CUSCINO + u`.

> ⇒ `AV ≈ cuscino + latenza d'uscita − ritardo di pittura`

A riposo 250 → **~331**; sotto carico la coda supera i 600 e `a.base` **si riàncora** (`:6152`) →
**~690**. ⭐ **I due numeri di §16.4 sono le due tacche del cuscino**, non due misure di un difetto.

⛔⛔ **E §16.4 legge il segno alla rovescia.** Scrive *«il suono precede l'immagine»*; il prodotto
dice *«positivo = il suono esce DOPO»*. ⇒ **L'audio è in RITARDO, non in anticipo** — e le due cose
hanno soglie percettive **diversissime**.

⚠ **E `AV` non può vedere la metà misurata qui**: elide l'`istante` del server da tutti e due gli
addendi. ⇒ Un prodotto con `AV` verde può essere desincronizzato, e viceversa. Le due misure **non si
sovrappongono**, e insieme dicono che lo sfalso vive **tutto dentro la pagina** — che è il posto dove
costa meno curarlo.

### 20.3-quater ⛔ SI SENTE — e la fonte è citata

**Rec. ITU-R BT.1359-1** (*Relative timing of sound and vision for broadcasting*, 1998), clausola g)
e Nota 1: *«detectability thresholds are about +45 ms to −125 ms and acceptability thresholds are
about +90 ms to −185 ms on the average, a positive value indicates that sound is advanced with
respect to vision»*.

⚠ **Il segno dell'ITU è l'opposto del nostro**: per loro positivo = suono in **anticipo**. Il nostro
+331 (audio **in ritardo**) è l'ITU **−331 ms**.

| | soglia ITU (audio in ritardo) | §16.4 a riposo (−331) | §16.4 sotto carico (−690) |
|---|---|---|---|
| **si nota** | −125 ms | ⛔ **2,6× oltre** | ⛔ **5,5× oltre** |
| **è accettabile** | −185 ms | ⛔ **1,8× oltre** | ⛔ **3,7× oltre** |

⇒ ⛔⛔ **Se il +331 è quel che l'utente riceve, si nota e non è accettabile.** ⚠ Che l'utente non
l'abbia giudicato sulla grana **non dice che non morde**: dice che quella scena non permetteva di
giudicarlo — ed è la **seconda** delle due letture tenute aperte in §16.4, non la prima.

⏳ **Che cosa resta**: la metà `AV` non è stata rimisurata (vuole il browser, e su quella macchina
Firefox non parte — §20.1-ter). Tutto quel che sta **prima** del browser è pulito; la conferma
diretta del 331 aspetta quello strumento.

> ### ⭐⭐⭐ E IL GIUDIZIO È ARRIVATO — **25 agosto 2026, fase 10**
>
> ⛔ *Il motivo per cui questo `[?]` era rimasto aperto era falso*: Firefox **non era rotto**, era
> `~/.cache -> /tmp` (§20.1-ter, **refutata**). ⇒ Tolto quello, il browser parte, e la prova si è
> potuta fare.
>
> ⭐ **E l'utente l'ha giudicata sulla scena più dura che ci sia** — un video **4K** dentro il
> desktop remoto, con la banda del suo tablet strozzata a **10 Mbit/s**, cioè **sotto il pavimento
> dichiarato**:
>
> > *«Il video mostra degli artefatti, ma è normale: siamo sotto le specifiche. Però **audio e video
> > fluidi e in sync**.»*
>
> ⇒ ⭐ **La metà `AV` del sincronismo ha il suo giudizio.** ⚠ **Non un numero**: un giudizio — il
> `[M]` dei **331 ms** e il termine di Opus restano `[?]`, e per quelli serve ancora lo strumento.
> ⭐ Ma la domanda che contava — *«all'orecchio e all'occhio, stanno insieme?»* — ha una risposta, ed
> è **sì**, presa dove il metro è l'utente (**I8**).
>
> `[M]` E accanto al giudizio ci sono i numeri della stessa scena, letti dal registro senza toccarla:
> **37,4 fot/s**, **3,20 Mbit/s**, ⭐ **coda vuota** — la banda **dimezzata senza perdere un
> fotogramma**. ⇒ `fasi/10-multi-tenant-e-il-budget.md` §10. ⚠ E il giro è a **PCM**: il termine di Opus non c'è dentro
(nel repo non esiste un decodificatore Opus, `07-b42-giudice.py:121`).

⭐ **Il filmato c'è, ed è quel che serve all'utente per dare il suo giudizio**:
`/media/REMOTIX/tmp/09nr10/film/09-b85-claquette-calma-p000.mp4` (70 s, **34 attacchi**), coi gemelli
`-p300`/`-m300` a sfalso noto, e `-dura-` per il caso sotto carico. Il server **7973 è acceso**.

---

# §21 · ⭐⭐⭐ LA CHIUSURA — *24 agosto 2026*: le cure si accendono, e la parola «bistabile» cade

## 21.1 ⭐⭐ IL GIUDIZIO DELL'UTENTE SUL SINCRONISMO — **alla cieca, e il metro era il suo orecchio**

⛔ **La prova di §16.4 era fallita per un errore di disegno mio**: avevo chiesto un giudizio sul
sincronismo guardando **pura grana**, cioè l'immagine con meno appigli possibili. ⇒ Rifatta con la
claquette di §20.3 — un cartello che sbatte, **34 volte in 70 s** — e ⭐ **alla cieca, con tre
gemelli**, senza dire all'utente quale fosse quale.

| ordine | che cosa c'era **nel file** | il suo giudizio |
|---|---|---|
| 1° | audio **321 ms in anticipo** | *«perfetto»* |
| 2° | **allineato** (21 ms) | *«perfetto»* · *«il bip è in sincrono con il flash»* |
| 3° | audio **279 ms in ritardo** | ⭐ *«il flash è in anticipo rispetto al bip»* |

⭐⭐ **Ha riconosciuto il ritardo vero, con la direzione giusta, senza saperlo.** ⇒ Il suo orecchio è
**tarato** su questa scala, e i suoi giudizi valgono — che è precisamente quel che mancava a §16.4.

⛔ **E il verdetto è che il difetto non arriva.** Il filmato **allineato** gli è arrivato **in
sincrono**. Se il prodotto aggiungesse davvero i **+331 ms** di §16.4, quel filmato gli sarebbe
suonato **come il terzo** — riconoscibile, perché ha appena dimostrato di riconoscere 279 ms.
⇒ **Il ritardo che raggiunge l'orecchio è sotto la soglia che lui sa riconoscere**, cioè **< ~280 ms**,
e probabilmente molto meno.

⚠ **Che cosa questo NON dice**, e va scritto: fra il 1° e il 2° non ha visto differenza, e sono
distanti **321 ms**. ⇒ Dalla parte dell'**anticipo** la sua risoluzione è più grossa di 300 ms. Ma il
cuscino spinge dalla parte del **ritardo**, ed è lì che discrimina. ⚠ E il giro è a PCM: il termine
di Opus non c'è dentro.

⇒ ⭐ **§20.3-quater va letta con questo accanto**: il conto con la soglia ITU dice *«si sentirebbe»*
**se** i 331 ms arrivassero. `[M]` L'orecchio dice che **non arrivano**. Le due cose non si
contraddicono: §20.3 misura il cuscino **dentro la pagina**, e la latenza di pittura del video lo
compensa in gran parte — la parte che **nessuna delle due misure di ieri poteva vedere da sola**.

⛔ **E una correzione mia, presa e ritirata in tre minuti**: dopo i primi due *«perfetto»* avevo
concluso che `mpv` rimettesse in sincrono i flussi e che la prova fosse **nulla**. ⚠ Era una
conclusione affrettata su due dati: **il terzo giudizio l'ha smentita**. Lo scrivo perché la fretta di
dichiarare nullo uno strumento è lo stesso difetto della fretta di dichiararlo buono.

## 21.2 ⭐⭐⭐ «BISTABILE» ERA LA PAROLA SBAGLIATA — è **un innesco a rischio costante**

`banchi/09-b83-biforcazione.py` · `[M]` 24 agosto · casella `perdita-0,20` · **40 giri** a due durate
· binario `56c62bb0…` · cure spente.

**Prima campagna** (20 giri da 25 s): spirale **13 volte su 20**. Chiavi **0** in 7 giri, **≥ 5** in
13, ⛔ **nessun giro fra 1 e 4**: due rami, non una distribuzione larga.

⛔ **E il fatto che li distingue nei primi dieci secondi NON C'È: 43 prove su 43 negative**
(soglia Bonferroni 0,05/43, permutazione esatta sulla somma dei ranghi). ⭐ **E si è capito perché** —
gli istanti d'accensione (primo abbandono §5.1 a regime):

> **3,1 · 3,2 · 4,3 · 4,5 · 5,3 · 8,0 · 8,8 · 9,5 · 10,5 · 11,4 · 18,4 · 18,6 · 24,9 s**

⇒ **5 accensioni su 13 cadono DOPO i dieci secondi.** In quella finestra non c'era niente da trovare
perché in quei giri la spirale **non era ancora partita**. ⚠ La finestra corta era un limite del
**disegno**, dichiarato come tale e non attribuito al prodotto.

### 21.2-bis ⭐⭐ LA PROVA A DUE DURATE — la previsione regge

| durata del giro | spirale **osservata** | **attesa** dal rischio costante |
|---|---|---|
| **10 s** | **35 %** (7 su 20) | 31 % |
| **50 s** | **90 %** (18 su 20) | 92 % |

`[M]` λ = **0,0529 al secondo**. Le prove pre-registrate: **T3** — un solo λ spiega tutte e tre le
durate? **p = 0,53**, non si rifiuta. **T4** — c'è una forma nel tempo? **p = 0,055**, sopra la
soglia di 0,0125: nessuna forma.

> ⇒ ⭐⭐⭐ **Non sono due comportamenti fra cui il prodotto sceglie. È un innesco A SENSO UNICO: ogni
> secondo ha la stessa probabilità (~5 %) di accendersi, e una volta acceso non si spegne più.**

⛔⛔ **E la conseguenza è la cosa che conta**, perché tocca ogni numero di §17:

- tempo **mediano** perché si accenda: **13 secondi**;
- in **un minuto** di lavoro su quella linea è quasi certo;
- in **un'ora** — che è la durata vera di una sessione — è **certo**.

⇒ ⚠ **I nostri banchi girano venticinque secondi; le sessioni durano ore.** Ogni misura presa vicino
al bordo della perdita **sottostima, e non di poco**: quel che al banco appare come *«a volte
succede»* sul desktop vero è **succede sempre, aspetta solo il momento**.
⭐ E rilegge anche il *«è tutto fluido»* di §19.1: quei trenta secondi stavano dentro la finestra in
cui, statisticamente, spesso non si è ancora acceso. ⛔ **Non lo smentisce** — ma dice che **una
sessione lunga su quella linea andrebbe guardata prima di concludere**.

**Le ipotesi, una per una** `[M]`: la perdita non era la stessa ⇒ **esclusa** (0,165-0,255 % in
entrambe le famiglie) · l'avvio lento di CUBIC ⇒ **non verificata** (`ssthresh` lascia l'infinito a
~2 s in tutt'e due) · la scena ⇒ **esclusa** (prima chiave 58,44-58,88 kB in entrambe) · la soglia
dei tre pacchetti ⇒ **non verificata** · macchina carica ⇒ **esclusa** (CPU 5,1-6,5 % in tutti e 20).
`[R]` L'algoritmo è **CUBIC** (ngtcp2 1.25, `trasporto.c:628` non tocca `cc_algo`) — ⚠ e la prova per
contrasto **non è stata fatta**: non è esposto da nessuna opzione.

⚠ **Che cosa non si sarebbe potuto vedere**, scritto prima: una separazione più piccola della
dispersione interna; una terza modalità rara (36 % di probabilità di non incontrarla); e ⛔ **niente
fra un secondo e l'altro** — `webtransport.c:4573` frena `rete_ciclo()` a una riga al secondo, quindi
dell'avvio lento si vede il punto d'arrivo, **non la corsa**.

## 21.3 ⭐⭐⭐ LE CURE SI ACCENDONO — e sulla linea sana **non peggiora niente**

*⇒ `DECISIONI.md` §3.1-septies. «Il prodotto cambia in meglio; questa fase era per rendere più solido
il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli.»*

**Il contratto — e per ciascuna una strada sola:**

| cura | predefinito | **unica** strada per spegnerla |
|---|---|---|
| soglia sulla coda video | **100 ms** | `--sgombra-soglia-ms 0` |
| regolatore del ritmo | **acceso** | `--niente-ritmo-adattivo` |
| linea morta | **accesa** (stallo 5 000 ms · silenzio 10 s) | `--niente-linea-morta` |
| sfratto del fantasma | **15 000 ms** | `--sfratto-ms 0` |
| silenzio dell'audio | **acceso** | `--niente-audio-silenzio` |

⛔ `--ritmo-adattivo` e `--linea-morta` **non esistono più**: chi li batte riceve un messaggio che
spiega il cambio e **uscita 2**, non un aiuto generico. ⛔ E il `-D AUDIO_SILENZIO_PREDEFINITO` è
**tolto**: due strade per accendere la stessa cura sono due numeri che divergono.
⭐ L'opzione dell'audio viaggia **negata** in coda all'`argv` del figlio — la strada di `--parlantina`
— perché il figlio è un `execve` con l'ambiente composto **da zero**.

⛔⛔ **Le righe d'avvio sono il verbale, e nessuna dice più «SPENTO (I6)».** Ognuna dichiara **stato ·
numero in vigore · che è il predefinito dal 24 agosto per decisione dell'utente · come si spegne**, e
`[M]` **il prezzo accanto**. Spente dicono *«SPENTA a mano … e NON è il predefinito»*.

### 21.3-bis ⭐⭐ LA PROVA CHE CONTA — la ferita di v1, cercata apposta

`banchi/09-b86-predefiniti.py` · porta 7980 · binario `14561dce…` · **29 casi di `--certifica`**.

- **(a) acceso di suo** ✅ — server lanciato **senza nessuna opzione**, e le cinque cure risultano
  attive ⛔ **lette dalle righe d'avvio del prodotto**, non dalla riga di comando;
- **(b) ognuna si spegne ancora** ✅ — cinque riavvii, una per volta; e i due nomi vecchi **rifiutati**;
- **(c) ⭐ il prodotto funziona acceso**, giro appaiato di 25 s a 1920×1080:

| braccio | fotogrammi/s | chiavi | quota delta | deriva finale |
|---|---|---|---|---|
| tutte **spente** | 39,60 | **0** | 1,0000 | 0,0 ms |
| ⭐ **predefiniti** | **39,69** | **0** | 1,0000 | 0,4 ms |
| `[M]` l'ancora di §17.6 | 39,85 | 0 | — | 0,1 ms |

⇒ **Nessun peggioramento**: −0,2 % contro le cure spente, −0,4 % contro l'ancora, **dentro il rumore
dichiarato del 5 %**. Zero chiavi, zero buchi, **zero scatti della linea morta, zero sfratti**.
⭐⭐ **Era la prova che poteva far ritirare tutto** — la ferita di v1 è esattamente «i numeri
migliorano e l'esperienza peggiora» — ed è verde.

⚠ **E due banchi si rompono per costruzione**, il che è voluto e va detto: `09-b79-cure.py` batteva
`--ritmo-adattivo`, `09-b84-audio-silenzio.py` appaiava **due binari** compilati diversi. ⭐ Adesso
il braccio spento si fa **dalla riga di comando sullo stesso identico binario**: un imputato in meno.
⏳ In cura.

## 21.4 ⭐⭐ LE CODE — e due delle tre si chiudono con un **no**

### 21.4-bis I due banchi rotti dalla modifica, e un difetto trovato rimettendoli a posto

`09-b79-cure.py`: bracci **rovesciati** — **A** = cure spente **a mano**, **C** = *nessuna opzione*.
⭐ Il guadagno è scritto nel commento: **il braccio che rappresenta il prodotto adesso è quello a cui
non si chiede niente**, e quindi non può promettere niente. `[M]` `--certifica` 21/21; giro vero su
`ritardo-30`: fps **38,15 / 39,61 / 39,78**, chiavi 0,2 / 0,0 / 0,0 %, **S′ verde**.

`09-b84-audio-silenzio.py`: da **due binari** a **uno**. ⭐ Due binari erano **due imputati** — se i
bracci davano numeri uguali le spiegazioni erano due (*«la cura non serve»* oppure *«i binari non
erano quelli che credevo»*); uno solo ne lascia una.
⛔⭐ **E semplificandolo è saltato fuori un difetto vero**: la riga del braccio **spento** adesso
contiene *«dal 24 agosto nasce ACCESA»*, e il banco cercava `"ACCESA" in dett` ⇒ **avrebbe letto
«accesa» su un braccio spento**, dando verde a due bracci sbagliati **proprio ora che quel predicato
è l'unica cintura**. Curato ancorandolo alle due frasi di stato.
`[M]` `--certifica` 31/31; giro `muto` (Opus, fermo): **557,5 → 5,7 kbit/s = 97,3×**, 1 248 blocchi
taciuti; giro `tono` (PCM): copertura **1,0000 → 1,0000**, purezza **1,000 → 1,000**, taciuti **1 su
5 002**.

### 21.4-ter ⛔⭐ `WT_DGRAM_RIMANDI_MAX` — **si tiene la grandezza, si cambia l'unità**

`[M]` Il numero che spiega tutto: `casa-cattiva`, 25 s ⇒ **2,2 milioni di rimandi**, cioè **~85 000
passate di scrittura al secondo** sotto carico contro **~200** a riposo. ⇒ Il tetto `4096` valeva
**~48 ms** in un caso e **decine di secondi** nell'altro. ⛔ E non era un fusibile, **era la
politica**: 2 258 blocchi buttati da quel tetto contro **9** dalla coda piena — il **99,6 %**.

⭐⭐ **La strada ovvia è stata provata e la misura l'ha rifiutata.** Timbrare ogni blocco e buttarlo
sull'**età vera**: `[M]` a 50 ms non scatta più di quanto scatti a 250, perché la coda tiene 8
blocchi = 40 ms di PCM e **la testa non è quasi mai più vecchia di 40 ms**. Prezzo di quel «non tocca
niente»: **+30 % di byte sul filo** (1 415 → 1 840 kbit/s, **rubati alla finestra del video**) per
**+11 % di blocchi utili** — il resto arriva già vecchio e **lo butta il cliente**.

⇒ Il campo diventa **`dgram_zitto_da`** («da quanto la connessione non mette un datagram in un
pacchetto») e il tetto **`WT_DGRAM_ZITTO_MAX_MS`**, in millisecondi. ⛔ E `4096` **non si converte con
una divisione**: è auto-referenziale — quante passate si fanno dipende da quanto si butta. `[M]` Col
prodotto 2,1 M rimandi, col tetto a 50 ms **20 M**. ⇒ Il valore si è **tarato sulla misura**, e il
verde è *«indistinguibile dal prodotto»*:

| tetto | spediti | butt. (coda) | rifiutati | kbit/s | utili | utili/filo |
|---|---|---|---|---|---|---|
| **il prodotto** (5 giri) | 2 912-3 242 | 14-16 | 1 753-2 084 | 1 312-1 447 | 1 223-1 315 | 0,40-0,44 |
| ⭐ **10 ms** | 2 947 | 16 | 2 039 | 1 286 | 1 246 | 0,435 |
| 5 ms | 2 999 | 15 | 1 995 | 1 327 | 1 246 | 0,424 |
| 50 ms | 3 955 | **797** | 263 | 1 743 | 1 390 | 0,360 |

**10 ms** (= due blocchi di PCM) sta **dentro la dispersione del prodotto su ogni colonna**.
⇒ ⭐ **La cura cambia quel che il numero vuol dire, non quel che il prodotto fa.** L'età vera del
blocco resta registrata (`dgram[].nato`) ma ⛔ **non decide**: finisce nella riga di registro accanto
al silenzio, **apposta per farsi smentire**.
⏳ Da riportare in `rcp.c`: il «conto finale» dice ancora *«rifiutati da ngtcp2»*, e adesso sono
*«buttati perché il filo era muto da N ms»*.

### 21.4-quater ⛔ IL `PADDING` — **NON fatta, e la diagnosi era sbagliata**

Scritta, costruita e misurata appaiata (desktop fermo col tono, `lo` liscio, stesso binario a meno di
quella riga):

| codec | riempimento | kbit/s | byte per pacchetto |
|---|---|---|---|
| Opus | sempre | 557,7 / 556,5 | 1 441 |
| Opus | condizionato | 556,9 / 555,8 | 1 441 |
| Opus | ⛔ **mai** | 556,4 | ⛔ **1 441** |
| PCM | sempre | 2 221,7 | 1 443 |
| PCM | condizionato | 1 988,0 | 1 292 |

⛔⛔ **Su Opus il guadagno è ZERO, non «piccolo»**: col riempimento **mai chiesto** il pacchetto resta
di **1 441 byte**. `[R]` **A riempirlo è `wt_scrivi()`**, che chiede il riempimento a *ogni* scrittura
di stream e chiude il pacchetto che il datagram aveva lasciato aperto con `WRITE_MORE`. ⇒ **Il
riempimento di una sessione ferma è dello STREAM, non del datagram**, e chi lo volesse togliere deve
andare lì.

⚠ Su PCM la condizione morde (**−10,5 %**) solo perché a 200 blocchi/s il datagram chiude il pacchetto
da solo — ma il PCM **non è quel che il prodotto negozia**, e col silenzio acceso a desktop fermo i
datagram sono **0,0/s**. ⇒ **Codice revertito**, e il verbale coi numeri resta nel riquadro
`MORE`/`PADDING` di `webtransport.c`: ⭐ una cura che non compra niente è **codice in più da
mantenere**, e va rifiutata con i numeri accanto invece che dimenticata.

### 21.4-quinquies ✅ E la decisione mai messa a verbale è ora in `SPECIFICHE.md` §10.1

⛔ *«Quando la finestra si stringe, l'audio passa davanti al video»* era una politica del prodotto
presa **nel codice** (`wt_scrivi()`) e **scritta in nessun documento**. ⇒ Adesso è `SPECIFICHE.md`
**§10.1**, con la ragione (i due carichi non si degradano allo stesso modo), il prezzo (banda tolta
al video proprio quando ce n'è poca) e il limite **per costruzione** (la coda dei datagram è lunga
otto ⇒ al massimo otto pacchetti passano davanti).
