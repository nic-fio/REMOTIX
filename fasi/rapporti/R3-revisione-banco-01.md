# R3 — Revisione avversariale del banco della fase 1

**9 agosto 2026** · oggetto: [`fasi/01-filo-nudo.md`](../01-filo-nudo.md), il documento della fase 1
aperto oggi, con dentro i dodici banchi e nessuna riga di prodotto scritta.

**La lente**: il banco come **strumento di misura**. Non la conformità a `RCP.md` — quella la guarda
un'altra revisione — ma una domanda sola, ripetuta ventotto volte: *questi banchi sanno vedere il
difetto che cercano?* Cioè, per ciascuno: **che aspetto avrebbe il caso in cui il banco è verde e il
difetto è vivo?**

> ⛔ **Non ho ricevuto il ragionamento di chi l'ha scritto** (`PIANO.md` §0.4, pratica 1). Ho letto il
> documento, `REVIEWER.md`, `LEZIONI.md` §1 e §2, `PIANO.md` §0, `RCP.md`, `web.md`, i rapporti
> `S1`-`S4` e `R2`, `fasi/00-ambiente.md` e i tre banchi in `banchi/`. Non ho misurato niente e non ho
> toccato nessun file del progetto: questo rapporto è l'unico che scrivo (`REVIEWER.md` §5).

---

## 1. I rilievi, in ordine di gravità

*«Gravità» = quanto costerebbe costruirci sopra prima di accorgersene. Un banco cieco costa più di
un banco assente, perché **dà fiducia** (`LEZIONI.md` §10).*

| # | Dove | Il rilievo, in una riga | Marca |
|---|---|---|---|
| **R3.1** | B1, righe S1a, S2 e S4 | ⛔ **delle undici prove di controllo che i rapporti prescrivono ne sopravvivono tre**: il controllo **negativo** manca in tutt'e tre le righe, e due delle amputazioni `R2` le aveva già bocciate `[R]` mandandole a curare *«prima di scrivere una riga di banco»* | `[R]` |
| **R3.2** | B8 | ⛔ **«≥ 1 s nei tre casi» è verde con il canale del tempismo aperto**: un `sleep(1)` dopo PAM passa tutt'e tre le righe e lascia vivo esattamente il difetto che B8 esiste per vedere | `[R]` |
| **R3.3** | B5 | ⛔ **«cade sempre» non distingue «il server ha rifiutato» da «il server è morto»** — e la violazione che lo produce (la lunghezza annunciata enorme) non è nell'elenco | `[R]` |
| **R3.4** | B1 vs B2 | ⛔ **l'ordine dichiarato è circolare**: S1a, S4 e S6 hanno bisogno del server WebTransport che è il *prodotto* di B2, e B1 si dichiara «nessuna riga di prodotto» e viene prima | `[R]` |
| **R3.5** | B4 | ⛔ **il validatore non ha un controllo negativo**: «6 su 6» è compatibile con un validatore che boccia **tutto**, registrazioni conformi comprese | `[R]` |
| **R3.6** | B4 | ⛔ **la registrazione dei byte decifrati contiene la parola d'ordine**, che `RCP.md` §4.4 vieta in ogni registro; redigerla rompe la `lunghezza` di §6.1 e fa fallire il validatore su ogni traccia | `[R]` |
| **R3.7** | B11 C1 | ⛔ **quattro guasti costruiti a mano su dodici banchi**: B3, B4, B7 e B9 non sono certificati — e B3 e B7 sono i banchi dei due difetti più cari di v1 | `[R]` |
| **R3.8** | B8 → B3, B6, B10 | ⛔ **il limitatore per indirizzo di §4.4-bis avvelena gli altri banchi nello stesso giro**: C3 vede la sopravvivenza *fra* i giri e non l'interferenza *dentro* il giro | `[R]` |
| **R3.9** | B8, ultima riga | ⛔ **il controllo positivo del limitatore non distingue «il successo azzera» da «la finestra è scaduta»** — le due cose hanno lo stesso aspetto | `[R]` |
| **R3.10** | B1, riga S5 | ⛔ **il controllo «i due numeri devono differire» è rosso sul codice giusto**, o misura un'altra grandezza: le due letture producono due banchi diversi | `[R]` |
| **R3.11** | B1, riga S3a | ⛔ **lo stato peggiore dei tre di O8 non è registrabile**: quando il browser esegue il suo comando la scheda muore e porta con sé il registro della prova | `[R]` |
| **R3.12** | B1, riga S3b | ⛔ **la misura non è eseguibile nella configurazione della fase**: dietro l'eccezione del certificato il Service Worker non si installa `[R]`, quindi la PWA non esiste | `[R]` |
| **R3.13** | B1, riga S2 | ⛔ **l'unico canale che risponde davvero è stato omesso** (`is_software_codec` da `media-internals`), e l'atteso in tabella importa **E1** nella colonna dell'atteso | `[R]` |
| **R3.14** | B1, tutte le righe | ⛔ **i dispositivi non sono dichiarati** — Mac, iPhone, telefono, DeX — e `fasi/00-ambiente.md` dichiara quell'ambiente **non toccato e rimandato alla fase 2** | `[R]` |
| **R3.15** | B1, colonna «controllo positivo» | ⛔ **tre caselle su nove non contengono un controllo positivo**: contengono l'atteso (S1b) o il metodo della misura (S3a, S3b) | `[R]` |
| **R3.16** | B1, righe S1a e S1b | ⛔ **lo stato che misurano sopravvive al giro** — l'eccezione concessa resta concessa — e non è nella lista di quel che C3 dichiara di sapere | `[R]` |
| **R3.17** | B11 C2 | ⛔ **«una porta dove non c'è nessuno» non copre il modo di fallire già pagato in casa**: UDP filtrato con il TCP che risponde (`R2` rilievo R1) | `[R]` |
| **R3.18** | B11 C5 | ⛔ **cita come modello un file il cui difetto è dichiarato aperto** in `fasi/00-ambiente.md`: l'atteso di `00-c1-kwin.sh` è **stampato e non confrontato** | `[R]` |
| **R3.19** | B3, ultima riga | ⛔ **la riga dei 30 secondi è indistinguibile da `max_idle_timeout`**: resta verde con il meccanismo assente del tutto | `[R]` |
| **R3.20** | B7 | ⛔ **«8 su 8» non dice che cosa fa passare una riga**: una frase predefinita «Errore 14» soddisfa il criterio e viola `RCP.md` §8.2 | `[R]` |
| **R3.21** | B9 | ⛔ **la separazione che dà valore al cliente di prova è affidata a una regola, non a un meccanismo** — è **I7** al contrario, e la fase 0 l'ha già pagata così | `[R]` |
| **R3.22** | B1, riga S6 | ⛔ **attribuisce al motore una grandezza del percorso**: due misure diverse sotto la stessa etichetta, forma **E2** | `[R]` |
| **R3.23** | «Le misure», tabella del filo | ⛔ **quattro righe su dieci hanno l'atteso vuoto**, contro C5 e contro il difetto 11 della fase 0 | `[R]` |
| **R3.24** | l'insieme dei dodici | ⛔ **sei cose che la fase 1 produce non le guarda nessun banco**, e tre di esse hanno un ⛔ scritto in `RCP.md` | `[R]` |
| **R3.25** | B1, riga S7 | ⚠ il segno della rotella potrebbe essere una proprietà di **una riga di configurazione del desktop**, e si misura su un compositore solo per chiudere una riga di protocollo che vale per cinque | `[?]` |
| **R3.26** | B10 | ⚠ «credenziali errate» ha più di una causa, e il banco ne nomina una: chi possiede il processo del server non è dichiarato da nessuna parte | `[?]` |
| **R3.27** | B6, prima riga | ⚠ **«TLS finito» non è un istante che i due lati condividono** in WebTransport su HTTP/3 | `[?]` |
| **R3.28** | B1, le nove etichette | ⚠ **le etichette S1a…S7 non esistono in nessuno dei quattro rapporti**, dove le procedure vivono — e due rapporti usano `P1…Pn` per cose diverse | `[R]` |

**Conto**: **25 `[R]`**, **3 `[?]`**, **0 `[M]`** (non posso misurare).

---

## 2. ⭐ Il caso «verde col difetto vivo», banco per banco

*È la domanda 1 del mandato, e la risposta va data per intero perché dove **non** sono riuscito a
costruire il caso è informazione quanto dove ci sono riuscito (`PIANO.md` §0.4, pratica 2).*

| Banco | Il caso in cui il banco è **verde** e il difetto è **vivo** | Costruito? |
|---|---|---|
| **S1a** | la pagina guarda **la promessa sbagliata** — per esempio considera «riuscito» il fatto che l'oggetto `WebTransport` si costruisca senza eccezione, invece di attendere `ready`: la prova con l'impronta riesce, il controllo è verde, e **anche una prova con l'impronta sbagliata di un byte riuscirebbe** | ✅ R3.1 |
| **S1b** | l'eccezione sparisce al quinto giorno perché il profilo è stato ripulito o il certificato **della pagina** è stato rigenerato: il banco scrive «meno di sette giorni» e attribuisce la differenza al bypass | ✅ R3.15 |
| **S2** | il telefono decodifica HEVC **in software con MediaCodec** — cioè il caso `[R]` che S2 dichiara essere quel che Chromium sceglie di proposito — e regge la soglia tarata su **VP9** software | ✅ R3.1, R3.13 |
| **S3a** | `Ctrl+W` arriva alla pagina **e** chiude la scheda: il registro muore con la scheda, il banco legge «non consegnata», che è lo stato **opposto** a quello vero | ✅ R3.11 |
| **S3b** | la PWA non si installa affatto, il banco misura Chrome per Android **non** in PWA e scrive il numero nella riga della PWA | ✅ R3.12 |
| **S4** | `t1` è preso alla **consegna del chunk** invece che nella callback del decodificatore: il ritardo iniettato di N ms fa salire la mediana di esattamente N, e il controllo passa | ✅ R3.1 |
| **S5** | la pagina legge i pixel logici: a zoom 100 % e 150 % i due numeri differiscono, il controllo è **verde**, e la tela dichiarata è sbagliata per tutta la sessione | ✅ R3.10 |
| **S6** | il numero è misurato in LAN a MTU 1500: il banco benedice 1200 byte, e sul percorso vero dell'utente i datagram non arrivano | ✅ R3.22 |
| **S7** | la sessione di prova ha `natural-scroll` all'opposto della predefinita: `+120` e `-120` vanno da parti opposte — il controllo passa — e il segno scritto in `RCP.md` §7.3 è quello di una gsetting | ⚠ R3.25 (`[?]`) |
| **B2** | UDP 7447 è filtrato: **entrambe** le candidate falliscono su **tutti e tre** i motori, e `DECISIONI.md` §6.4 si chiude con «nessuna delle due porta WebTransport» | ✅ R3.4, R3.17 |
| **B3** | la seconda connessione entra dopo 30 s perché `max_idle_timeout` ha ucciso la prima, e il server non ha **nessun** orologio del silenzio | ✅ R3.19 |
| **B4** | il validatore legge la `lunghezza` come `u16`: boccia le sei registrazioni guaste **e tutte quelle conformi**. Sei rossi su sei, e il banco è certificato | ✅ R3.5 |
| **B5** | il server muore di allocazione su una `lunghezza` annunciata di 4 GiB: la connessione **cade**, e cadere è il criterio | ✅ R3.3 |
| **B6** | — | ⭐ **no**: il controllo che guarda **il motivo** (`TEMPO_SCADUTO` a 60 contro una morte muta a 30) distingue davvero i due casi. Vedi §4 |
| **B7** | la pagina ha un ramo predefinito `"Errore " + codice`: otto motivi, otto frasi, otto su otto | ✅ R3.20 |
| **B8** | l'implementazione dorme un secondo **dopo** PAM: tutte le risposte sono ≥ 1 s, e le mediane dei tre casi differiscono di cinquanta millisecondi | ✅ R3.2 |
| **B9** | chi scrive il cliente di prova eredita il fraintendimento perché nessun meccanismo gli impedisce di leggere il C, e i due si capiscono | ✅ R3.21 |
| **B10** | il secondo utente non entra perché il contatore per **indirizzo** di §4.4-bis è nella sua finestra da quando è girato B5: il banco legge il difetto che cercava dove non c'è | ✅ R3.8, R3.26 |
| **B11** | C1 dà quattro rossi su quattro e B3, B4, B7 e B9 restano non certificati: il documento scrive «i banchi si certificano» | ✅ R3.7 |
| **B12** | — | ⭐ **no**: è un elenco di rimandi, non una misura. Il conto con `RCP.md` §11 torna. Vedi §4 |

---

## 3. I rilievi, uno per uno

### R3.1 — Delle undici prove di controllo che i rapporti prescrivono ne sopravvivono tre, e il controllo NEGATIVO non c'è in nessuna delle tre righe

```
DOVE:             fasi/01-filo-nudo.md, B1, colonna «il controllo positivo»,
                  righe S1a, S2 e S4
COSA CONTRADDICE: S1 §4.2 (P3 e P4) e §4.4 («Solo con P2 verde e P3 rosso il
                  risultato di P1 significa qualcosa»);
                  S2 §4.4 (controlli A, B, C e «criterio di validità»);
                  S4 §4.2 (P2, P3, P5, P6, P7);
                  web/rapporti/R2-revisione-web.md rilievi R15 e R16, entrambi [R],
                  e R2 §5 che li manda da curare «⛔ prima di scrivere una riga di
                  banco […] senza di esse la fase 1 misura male»;
                  LEZIONI.md §1.9 regola 2 e §1.11 regola 1; REVIEWER.md §1 punto 5
```

**Come si dimostra.** Il conto, riga per riga, fra quel che i rapporti prescrivono e quel che è
arrivato nella casella «Il controllo positivo» del banco:

| Riga | Che cosa prescrive il rapporto | Che cosa c'è nel banco |
|---|---|---|
| **S1a** | **P2** l'impronta deve riuscire · **P3** l'impronta **sbagliata di un byte** deve **fallire** · **P4** il certificato a 30 giorni deve fallire **per durata** | ⛔ **solo P2** |
| **S2** | **A** VP9 `prefer-software` dev'essere dichiarato **software** · **B** VP9 `prefer-hardware` dev'essere dichiarato **hardware** · **C** `is_software_codec` letto in parallelo | ⛔ **solo A** |
| **S4** | **P1** ritardo iniettato · **P2** il rilevatore trova il colore che c'è · **P3** **non** trova quello che non c'è · **P5** il fuori ordine · **P6** la grana dell'orologio · **P7** il ritmo come controllo del percorso | ⛔ **solo P1** |

⛔ **La forma è la stessa in tutt'e tre**: sopravvive il controllo che dice **sì**, cade quello che
dice **no**. E i tre rapporti l'avevano scritto, ciascuno con le sue parole:

- S1 §4.4: *«**Solo con P2 verde e P3 rosso il risultato di P1 significa qualcosa**»*, e su P3:
  *«**Se riesce, il banco non distingue nulla**»*;
- S2 §4.4: *«il banco è valido se, sullo stesso telefono, dichiara **software** il controllo A **e
  hardware** il controllo B. Finché non lo fa, **non pubblica verdetti**»*;
- S4 §4.2 su P3: *«**se dice sempre sì, si sta misurando zero e si è felici a torto**»*.

I tre ingressi concreti:

- **S1a** — la pagina considera «riuscita» la costruzione dell'oggetto `WebTransport` invece
  dell'attesa di `ready`, oppure guarda la promessa sbagliata. La prova con l'impronta **riesce**
  (controllo verde), la prova senza impronta **riesce anch'essa**, e il banco scrive `[M]`
  *«su Safari l'eccezione copre WebTransport»* — un `[M]` falso contro due `[R]` letti nel codice
  di Chromium e di Gecko. **P3 esiste apposta per questo**: con l'impronta storpiata di un byte la
  connessione **deve** fallire, e se riesce il difetto è nel banco;
- **S2** — la soglia è tarata larga (o il telefono è lento): il controllo A passa, e HEVC **software
  di MediaCodec** — che è quel che Chromium sceglie di proposito su Android quando non trova
  hardware `[R]` — passa per hardware, perché la calibrazione era stata fatta su **VP9**, un altro
  codec con un altro costo in CPU. ⚠ E fra le due soglie che S2 propone (≥ 90 fps ⇒ hardware,
  ≤ 30 ⇒ software) c'è una banda dichiarata **«verdetto sospeso»** che nel banco della fase 1 non
  compare: le uscite sono due dove il rapporto ne prevede tre;
- **S4** — un rilevatore che dice **sempre** «ho visto la marca» fa salire la mediana di N insieme al
  ritardo iniettato, quindi **passa il controllo decisivo**. Idem per `t1` preso alla consegna del
  chunk invece che nella prima riga della callback: i N ms si sommano identici. E senza **P6** — la
  grana dell'orologio — su Firefox e Safari senza isolamento fra origini i campioni cadono su una
  griglia da **1 ms** su un tetto di **50**, e S4 avverte che *«una misura singola non vale nulla, si
  lavora a distribuzioni»*.

⛔ **Il costo, e va detto**: due di queste tre amputazioni erano già state trovate. `R2` §5 le mette
in cima alla lista con la ragione scritta — *«sono correzioni di testo, costo zero, e senza di esse la
fase 1 misura male»*. Sono passate **poche ore** e il documento che le doveva ereditare curate le ha
ereditate intatte; la terza (S1a) è nuova, ed è nata dalla **cura parziale** del rilievo R1 di `R2`,
che aveva rimesso il controllo positivo e non quello negativo. È la stessa forma della voce 6 di
`fasi/00-ambiente.md`: *«la lezione era già scritta. La cura non è mai stata applicata: è rimasta una
nota in un documento»*.

```
MARCA: [R]
```

---

### R3.2 — B8: «≥ 1 s nei tre casi» è verde con il canale del tempismo aperto

```
DOVE:             fasi/01-filo-nudo.md, B8, tabella (le tre righe «≥ 1 s») e
                  «Le misure» → «B8 — il secondo fisso, nei tre casi | ≥ 1 s»
COSA CONTRADDICE: RCP.md §4.4-bis, che dichiara lo scopo della regola —
                  «serve a togliere il tempismo come canale»;
                  LEZIONI.md §1.3 (un banco che non riproduce non assolve);
                  REVIEWER.md §1 punto 3
```

**Come si dimostra.** `RCP.md` §4.4-bis è scritta come **scadenza**: *«non prima che sia passato un
secondo **dalla ricezione**»*. Un'implementazione che invece dorme un secondo **dopo** che PAM ha
risposto è diversa, e la differenza è tutta la proprietà di sicurezza.

L'ingresso concreto: si scrive il server con `pam_authenticate(...); sleep(1); rispondi();`. Su questo
ferro `pam_unix` impiega ~1 ms a rifiutare un utente inesistente e ~50 ms a rifiutare una parola
d'ordine sbagliata (è il costo della funzione di hash, ed è la ragione per cui §4.4-bis esiste).

| Caso | Che cosa misura il banco | Che cosa scrive |
|---|---|---|
| utente inesistente | 1,001 s | ✅ ≥ 1 s |
| parola sbagliata | 1,050 s | ✅ ≥ 1 s |
| credenziali giuste | 1,300 s | ✅ ≥ 1 s |

**Tre righe verdi, e la distinzione che §4.4 vieta di scrivere nel motivo si legge col cronometro
esattamente come prima.** Il banco che B8 stesso dichiara *«una proprietà di sicurezza che nessun
altro banco vede»* non la vede nemmeno lui.

⛔ **E il criterio giusto è di forma diversa, non di soglia diversa**: non «≥ 1 s», ma *«le mediane
dei tre casi differiscono meno del rumore della misura»* — cioè molti campioni per caso, non uno, e
un confronto fra distribuzioni. Il documento non dice quanti campioni si prendono, e con un campione
per caso la differenza di cinquanta millisecondi non è nemmeno visibile.

⚠ **E la certificazione non lo copre**: C1 costruisce il guasto *«si toglie il ritardo fisso»*, che
porta la risposta a 50 ms e fa diventare il banco rosso. Il guasto che il banco **non** vede — il
ritardo messo dalla parte sbagliata di PAM — non è fra i quattro.

```
MARCA: [R]
```

---

### R3.3 — B5: «cade sempre» non distingue il rifiuto dalla morte del server

```
DOVE:             fasi/01-filo-nudo.md, B5 (l'intestazione «la connessione DEVE cadere
                  ogni volta») e «Le misure» → «B5 — le violazioni, motivo per motivo |
                  cade sempre»
COSA CONTRADDICE: RCP.md §3.1 (chiudere è tre atti, non «cadere»);
                  RCP.md §6.1 «⛔ la lunghezza si controlla PRIMA di allocare»;
                  LEZIONI.md §1.9 (due esiti opposti sotto la stessa faccia);
                  LEZIONI.md §2.1, forma «sul numero di connessioni»
```

**Come si dimostra.** Due cose, e la seconda è quella che manca del tutto.

**(a) Il criterio in tabella è «cade sempre», e un server che muore soddisfa il criterio.** L'ingresso
concreto: si manda sul canale di controllo un'inquadratura di §6.1 con `tipo = 0x0001` e
`lunghezza = 0xFFFFFFFF`. Un server che alloca prima di controllare — cioè quello che §6.1 vieta con
un ⛔ — chiede quattro gigabyte, viene ucciso dal nucleo, e **la connessione cade**. Il banco scrive
✅. E il difetto vivo non è «una violazione non gestita»: è che **chiunque sappia scrivere sei byte
spegne il server**, cioè anche tutte le altre sessioni degli altri utenti (`SPECIFICHE.md` §5.5,
multi-tenant).

Il criterio giusto ha una riga in più, e costa niente: dopo ogni violazione **il server deve essere
ancora lì**, e la verifica è una connessione nuova che arriva fino a `SESSIONE`. È la stessa forma
che B3 applica già alla seconda connessione — *«se il server muore, il difetto è suo»* — e che B5
non applica.

**(b) La violazione che produce quel caso non è nell'elenco.** Le dodici righe di B5 contengono *«una
lunghezza sbagliata (in più e in meno)»*, che è la lunghezza **incoerente col tipo** (§6.1, prima
riga). Non contengono **il tetto di 1 MiB annunciato** né il messaggio **da 16 MiB** di §6.2 — che è
la seconda metà dello stesso obbligo — e sono le due righe di `RCP.md` scritte con un ⛔ apposta
perché *«chi ne annuncia uno più grande viola il protocollo»*.

⚠ **E una terza, minore, dentro la stessa sezione**: B5 chiude con *«la chiusura si verifica in
tutt'e tre i punti di §3.1»*, mentre §3.1 rende il secondo punto **condizionale** — *«DEVE mandare
`CONGEDO` […] se il canale di controllo è ancora utilizzabile»*. Un banco che pretende tutt'e tre
sempre dà **rosso sul codice giusto** nei casi in cui la violazione arriva su uno stream
unidirezionale e il canale di controllo non è utilizzabile (`LEZIONI.md` §2.3).

```
MARCA: [R]
```

---

### R3.4 — L'ordine dichiarato fra B1 e B2 è circolare, e «nessuna riga di prodotto» non è vero

```
DOVE:             fasi/01-filo-nudo.md, la tabella dei tre gruppi («B1 … Nessuna riga di
                  prodotto» · «B2 … senza di esso il resto non ha su che cosa girare» ·
                  «l'ordine non è decorativo»), e B12 riga «l'anello del ritardo»
COSA CONTRADDICE: sé stesso; e web.md §7 («Nessuna richiede una riga di prodotto»)
```

**Come si dimostra.** Tre delle nove misure di B1 hanno bisogno di **un server che parli
WebTransport**, cioè della cosa che B2 costruisce:

| Misura | Che cosa le serve, testualmente dal documento |
|---|---|
| **S1a** | *«si prova l'eccezione da sola **e** la connessione con l'impronta pubblicata. La seconda **deve riuscire**»* — due sessioni WebTransport verso un server, e una pagina che pubblica l'impronta |
| **S6** | *«si spedisce un datagram di quella misura esatta e **si verifica che arrivi**»* — arrivi **dove**? Serve un ricevente, cioè un server con i datagram abilitati sulla connessione HTTP/3 (`RCP.md` §2.2) |
| **S4** | *«`t0` prima di **spedire**»*, e *«il **server** ritarda di N ms noti»* — serve un server che spedisca fotogrammi codificati, e un decodificatore che li accetti |

E B2, a sua volta, dichiara che *«la prova vale solo se **tutti e tre i motori** aprono la sessione»*
— cioè ha bisogno di sapere che **Safari** sa aprirla, che è la domanda di S1a. **B1 ha bisogno di
B2, e B2 ha bisogno di B1**, e il documento scrive che l'ordine «non è decorativo».

L'ingresso concreto che rompe l'ordine scritto: si comincia da B1 come dice il documento, si apre la
pagina su Safari, non c'è niente su UDP 7447 perché il server minimo non è ancora scritto, la
connessione con l'impronta fallisce, e il controllo positivo di S1a — quello curato da `R2` — dice
**giustamente** «non stai misurando l'eccezione, stai misurando un server che non risponde». Il banco
non è cieco: è **inavviabile**. E S4 non è nemmeno inavviabile — è irrealizzabile senza codifica,
trasporto e decodifica, cioè senza le fasi 2 e 3, mentre B12 lo dichiara *«senza prodotto»*.

⛔ **E S4 chiede di più di un server: chiede una riga di protocollo.** S4 §5.3 lo dichiara:
*«la marca del banco è un'estensione di protocollo. Il rettangolo di 16×16 e il comando che lo cambia
(con il ritardo `N` iniettabile del controllo P1) vanno scritti in `RCP.md` come **funzione di
banco**, non improvvisati nel codice di prova»*. Cioè la misura che il documento colloca fra quelle
«senza prodotto» vuole **un messaggio nuovo in `RCP.md`** — e `RCP.md` §9 avverte che la finestra per
aggiungere tipi si chiude *«dal primo byte scritto in poi»*. Se quel messaggio non entra adesso,
entrerà come deroga.

⭐ **L'ordine onesto è l'inverso, e cambia il documento in un punto solo**: B2 per primo, con il
server minimo da cinquanta righe che si butta; poi S1a e S6 sopra quel server; **S4 alla fase 3**,
con la sua riga di protocollo dichiarata adesso; e S1b, S2, S3a, S3b, S5 e S7, che sono le uniche sei
davvero indipendenti dal filo.

```
MARCA: [R]
```

---

### R3.5 — B4: il validatore non ha il controllo che serve, cioè quello negativo

```
DOVE:             fasi/01-filo-nudo.md, B4 (il riquadro «Il controllo positivo») e
                  «Le misure» → «B4 — le sei registrazioni guaste viste dal validatore |
                  6 su 6»
COSA CONTRADDICE: LEZIONI.md §2.3 («una prova che boccia il codice giusto costa quanto
                  una che promuove quello sbagliato»); LEZIONI.md §1.9 regola 1;
                  e B4 stesso, che chiede al validatore di dire «QUALE byte»
```

**Come si dimostra.** Il controllo positivo c'è ed è quello giusto: sei registrazioni guaste,
il validatore deve vederle. **Manca il rovescio**, e senza il rovescio «6 su 6» non dimostra niente.

L'ingresso concreto: il validatore legge il campo `lunghezza` di §6.1 come `u16` invece che `u32` —
è un difetto di due caratteri, e le due letture producono uno scarto di due byte su **ogni** messaggio
del canale di controllo. Effetto: le sei registrazioni guaste risultano non conformi (✅ 6 su 6, banco
certificato) **e anche tutte quelle conformi**, che però nessuno gli dà mai. Da quel momento il
validatore — *«l'unico arbitro meccanico che avremo»* (`PIANO.md` §0.4) — dichiara non conforme ogni
traccia che vedrà, e il primo giro del filo produrrà una diagnosi che punta su `RCP.md` §6.1 mentre
il difetto è nello strumento.

**Il controllo che manca, in una riga**: una **settima** registrazione, conforme, che il validatore
**deve accettare**. Costa quanto le altre sei e chiude il caso.

⚠ **E un secondo pezzo, dalla stessa parte**: il criterio in tabella è «6 su 6», cioè conta i rossi.
B4 chiede al validatore di dire **quale byte** non è conforme — e nulla verifica che lo dica giusto.
L'ingresso concreto è la sesta registrazione, quella del *«corpo giusto ma allineato»*: un validatore
che non conosce il divieto di riempimento di §6.0 non vede il byte in più, ma legge di traverso il
**messaggio successivo**, lo trova con un `tipo` sconosciuto e dichiara **quello** non conforme. Rosso
giusto, byte sbagliato — e su una traccia vera manderebbe la diagnosi a leggere il messaggio sbagliato.

```
MARCA: [R]
```

---

### R3.6 — B4: la registrazione dei byte decifrati contiene la parola d'ordine, e redigerla rompe il validatore

```
DOVE:             fasi/01-filo-nudo.md, B4, ultimo riquadro: «serve un modo di registrare
                  i byte decifrati dai due lati: si scrive qui, e va scritto sapendo che
                  ⛔ la parola d'ordine non deve comparire in nessun registro a nessun
                  livello (RCP.md §4.4)»
COSA CONTRADDICE: RCP.md §4.4 (nota finale) contro RCP.md §6.1 («lunghezza DEVE essere
                  il numero esatto dei byte del corpo»); e B4 stesso, che fra le sei
                  registrazioni guaste ne vuole una con «un messaggio nello stato
                  sbagliato — ATTACCA prima di CREDENZIALI»
```

**Come si dimostra.** Il documento vede il problema — lo scrive con un ⛔ — e poi lascia le due
regole a contraddirsi senza dire quale vince. Le tre uscite possibili sono tutte guaste, e questo è
il punto:

| Che cosa fa il registratore | Che cosa succede |
|---|---|
| registra i byte **come sono passati** | la parola d'ordine in chiaro finisce in un file che vive su disco e che si passa a uno strumento — ⛔ vietato da `RCP.md` §4.4 *«a nessun livello»* |
| **sostituisce** la parola con `***` e lascia la `lunghezza` | il corpo non ha più la lunghezza dichiarata ⇒ il validatore chiude con `ERRORE_PROTOCOLLO` su **ogni** traccia che contenga una stretta di mano riuscita: **falso rosso perpetuo** |
| sostituisce la parola **e riscrive la lunghezza** | la registrazione non è più i byte che sono passati: il validatore convalida un documento che il banco ha riscritto, cioè **non è più un arbitro** |

L'ingresso concreto è la prima registrazione buona che qualcuno produrrà: la stretta di mano completa
di un utente vero, con `CREDENZIALI(utente="nicfio", parola=…)`. Qualunque delle tre strade si
prenda, o si viola §4.4 o si rompe il validatore.

⭐ **La quarta strada esiste e va scelta prima di scrivere il registratore, non dopo**: si registra
la **lunghezza** e un'**impronta** del corpo per i soli campi segreti, dichiarando nel formato della
registrazione che quel corpo è oscurato — così la lunghezza torna, il validatore sa che non deve
guardarci dentro, e la parola non c'è. Ma è una decisione di formato, e oggi il formato della
registrazione **non è definito da nessuna parte** — il che è il secondo pezzo di questo rilievo: due
registratori, uno nel C e uno nella pagina, che scrivono lo stesso fatto in due modi, sono
esattamente il difetto muto contro cui `RCP.md` §0 è stato scritto.

```
MARCA: [R]
```

---

### R3.7 — B11 C1: quattro guasti costruiti su dodici banchi, e mancano proprio i due che portano i difetti di v1

```
DOVE:             fasi/01-filo-nudo.md, B11 riga C1 («un guasto per banco: si toglie il
                  PING (B6), si toglie il ritardo fisso (B8), si accetta un nome di
                  capacità ripetuto (B5), si rimette autenticazione_utente_atteso()
                  (B10)») e «Le misure» → «C1 — i quattro guasti costruiti a mano |
                  4 rossi su 4»
COSA CONTRADDICE: l'intestazione di B11 («Come QUESTI banchi si certificano»);
                  PIANO.md §0.3 regola 4; LEZIONI.md §1.2 e §1.3
```

**Come si dimostra.** «Un guasto per banco» e quattro guasti danno quattro banchi. I banchi sono
dodici. Restano fuori **B3** (la stretta di mano su due connessioni), **B4** (il validatore), **B7**
(il congedo dal lato che riceve) e **B9** (il cliente di prova) — e i primi due della lista sono i
banchi dei due difetti che v1 ha pagato più cari:

- **B3** esiste perché *«in v1 un certificato condiviso uccideva il server alla seconda connessione»*
  (`LEZIONI.md` §2.1). Il guasto da costruire è una riga: si tiene in vita una struttura per
  connessione e non la si libera alla chiusura. **Il banco diventa rosso?** Solo se la seconda
  connessione viene fatta **dopo** una chiusura vera e verificata; se il banco chiude la prima e
  riapre subito, il difetto può presentarsi alla terza o alla decima. Non lo sappiamo, perché nessuno
  lo costruisce;
- **B7** esiste perché *«per tre fasi il server scriveva «congedo il client» mentre il client scriveva
  «errore di rete»: mancava una seconda chiamata di libreria»* (`LEZIONI.md` §1.7). Il guasto da
  costruire è **esattamente quella riga**: si toglie la spedizione del `CONGEDO` e si lascia solo il
  codice nella chiusura della sessione. ⛔ **E qui il caso verde è costruibile**: `RCP.md` §3.1 rende
  il `CONGEDO` condizionale — *«se il canale di controllo è ancora utilizzabile»* — quindi un banco
  che accetti «uno dei due è arrivato» resta verde su **tutti e otto** i motivi con la spedizione del
  congedo tolta del tutto. B7 scrive «il `CONGEDO` **e** il codice», che è la congiunzione giusta; ma
  senza il guasto costruito **nessuno saprà mai se il codice del banco fa la congiunzione o
  l'alternativa**, e la differenza fra le due è una `&&` scambiata per una `||`.

```
MARCA: [R]
```

---

### R3.8 — Il limitatore per indirizzo avvelena gli altri banchi dentro lo stesso giro

```
DOVE:             fasi/01-filo-nudo.md, B8 (riga «il limitatore»), B7 (gli otto motivi),
                  B5 (riga «CREDENZIALI con utente vuoto»), B10, e B11 riga C3
COSA CONTRADDICE: RCP.md §4.4-bis, che tiene «due contatori […] uno per nome utente e
                  uno per INDIRIZZO DI PROVENIENZA, e applica il più severo dei due»;
                  LEZIONI.md §2.3-quinquies, corollario («quel che resta dal giro prima
                  va svuotato all'inizio»)
```

**Come si dimostra.** C3 vede metà del problema e la scrive: *«⚠ Qui morde davvero: i contatori dei
tentativi di §4.4-bis **sopravvivono al giro precedente**»*. L'altra metà è che **sopravvivono anche
dentro il giro**, e tutti i banchi partono dallo stesso indirizzo — la macchina del banco.

La sequenza concreta, con i banchi eseguiti nell'ordine in cui il documento li elenca:

1. **B7** deve produrre `CREDENZIALI_ERRATE` per la sua tabella degli otto motivi: **1 tentativo
   fallito** dall'indirizzo del banco;
2. **B8** prova il limitatore: *«5 tentativi falliti in 5 minuti»* — **6 tentativi falliti in totale**,
   soglia superata, e la finestra parte da 30 secondi e **raddoppia a ogni tentativo fino a 15
   minuti**. B8 stesso, provando il raddoppio, porta la finestra a diversi minuti;
3. **B10** apre la connessione del secondo utente, dallo **stesso indirizzo**, con credenziali
   **giuste**. Il server risponde `RESPINTO(TROPPI_TENTATIVI)` *«subito e senza interrogare PAM»*,
   come §4.4-bis gli impone;
4. il banco legge «il secondo utente non entra» e scrive nel documento che
   `autenticazione_utente_atteso()` è ancora lì.

⛔ **È un falso rosso che punta esattamente sul difetto che B10 esiste per vedere**, cioè il caso
peggiore: non un rumore, ma una conferma sbagliata. E il rovescio è altrettanto costruibile — se
qualcuno «cura» il problema azzerando i contatori fra un banco e l'altro, allora **B8 non prova più
niente**, perché il limitatore che sta misurando viene azzerato dal banco stesso.

⚠ **E lo stesso meccanismo tocca B3 e B6**: B3 apre quattro connessioni che devono arrivare a
`SESSIONE`, B6 ne apre tre che devono restare in silenzio. Tutte dallo stesso indirizzo, tutte dopo
B5 e B7. Il documento non dichiara né l'ordine di esecuzione né una regola di isolamento — e
`RCP.md` §4.4-bis dichiara apposta che il contatore per indirizzo *«scade da sé dopo 30 minuti di
quiete»*, cioè che **il banco intero dovrebbe fermarsi mezz'ora** fra due sezioni.

```
MARCA: [R]
```

---

### R3.9 — B8: il controllo positivo del limitatore non distingue le due cause

```
DOVE:             fasi/01-filo-nudo.md, B8, ultima riga: «il controllo positivo del
                  limitatore | ⛔ un'autenticazione riuscita azzera il contatore di quel
                  nome: si prova, o non si sta provando il limitatore ma un blocco
                  permanente»
COSA CONTRADDICE: RCP.md §4.4-bis, che nella finestra fa rifiutare OGNI tentativo
                  «subito e senza che PAM venga interrogata»;
                  LEZIONI.md §1.9 regola 2; REVIEWER.md §1 punto 5
```

**Come si dimostra.** Il controllo chiede una **autenticazione riuscita** per far vedere che azzera il
contatore. Ma dentro la finestra un'autenticazione **non può riuscire**: §4.4-bis dice che ogni nuovo
tentativo riceve `RESPINTO(TROPPI_TENTATIVI)` senza nemmeno interrogare PAM. Quindi la sequenza
eseguibile è una sola: cinque fallimenti → finestra → **si aspetta che scada** → si autentica con le
credenziali giuste → riesce.

L'ingresso concreto che mostra la cecità: si scrive un server **senza** l'azzeramento sul successo —
cioè con il contatore che decade solo per scadenza della finestra. La sequenza qui sopra dà
esattamente lo stesso esito: cinque rossi, un'attesa, un verde. **Il controllo è verde con il
difetto vivo.**

⭐ **Il controllo che distingue esiste ed è di forma diversa**: quattro fallimenti (sotto soglia), un
successo, **altri quattro fallimenti**, e si verifica che l'ottavo non sia bloccato. Se il contatore è
stato azzerato dal successo, il nono è il quinto; se non lo è stato, il quinto è arrivato prima e il
blocco è già scattato. Due esiti diversi per due implementazioni diverse — che è la definizione di
controllo.

⚠ **E una seconda riga, nella stessa tabella, che farà dare rosso al codice giusto**: B8 scrive che
oltre la soglia si risponde *«subito e senza interrogare PAM»*. Chi scrive il banco cronometra
«subito» — e trova **un secondo**, perché il ritardo fisso della riga sopra vale *«anche quando la
risposta è `AMMESSO`»*, quindi a maggior ragione quando è un rifiuto. Due righe della stessa tabella
chiedono al cronometro due cose opposte. È la stessa forma del rilievo **R1.13** di `RCP.md`, dove
«l'attesa» era stata scambiata per un ritardo della risposta.

```
MARCA: [R]
```

---

### R3.10 — S5: il controllo «i due numeri devono differire» è rosso sul codice giusto

```
DOVE:             fasi/01-filo-nudo.md, B1 riga S5, colonna «il controllo positivo»:
                  «si misura a zoom 100 % e poi a 150 %, sullo stesso dispositivo, nello
                  stesso giro: i due numeri devono differire, o non si sta leggendo il
                  fattore che si crede»
COSA CONTRADDICE: DECISIONI.md §5.0-quater, che dichiara il difetto da evitare —
                  «l'utente che ha premuto Ctrl + prima di collegarsi dichiarerebbe una
                  tela sbagliata, e resterebbe per tutta la sessione»;
                  SPECIFICHE.md §6.1-bis («lo schermo del dispositivo, in pixel fisici»);
                  LEZIONI.md §2.3
```

**Come si dimostra.** «I due numeri» non è definito, e le due letture possibili producono **due
banchi diversi** — che è precisamente la forma di difetto che `RCP.md` §0 esiste per togliere,
applicata al banco invece che al protocollo.

**Lettura A — «i due numeri» sono la tela dichiarata.** Allora il controllo pretende che la tela
cambi con lo zoom. Ma la tela **giusta** è lo schermo in pixel fisici, che con lo zoom **non cambia**:
`screen.width` cala di un terzo e `devicePixelRatio` sale di un mezzo, e il prodotto resta lo stesso.
L'ingresso concreto: una pagina scritta bene, che moltiplica i due, misurata a 100 % e a 150 %,
produce **1920 e 1920** — il controllo dà **rosso sul codice giusto**, e chi lo legge concluderà «non
sto leggendo il fattore» e andrà a rompere la pagina finché il numero non si muove, cioè finché non
avrà scritto il difetto che `DECISIONI.md` §5.0-quater voleva evitare.

**Lettura B — «i due numeri» sono il fattore di scala.** Allora il controllo è giusto ma **misura
un'altra cosa**: certifica che lo strumento vede lo zoom, e non dice niente sulla tela. E la tela —
che è la grandezza per cui S5 esiste, e che *«resta sbagliata per tutta la sessione»* — resta **senza
controllo positivo**.

⭐ **Il controllo che chiude tutt'e due i casi è di una riga, e va nella stessa casella**: la tela
dichiarata a 100 % e a 150 % **deve essere la stessa**, e **deve coincidere con la risoluzione fisica
dello schermo letta fuori dal browser** (le impostazioni del dispositivo). Due strumenti diversi sullo
stesso fatto: è il controllo positivo di `LEZIONI.md` §1.9 regola 2, e qui è disponibile gratis.

⚠ **E la terza domanda di S5 non è chiudibile con una misura**: *«se l'arrotondamento anti-impronta
possa produrre un numero dispari»*. Su un dispositivo si osserva un numero; se è pari, non se ne
ricava che i dispari non esistano — la casella «Che cosa decide» promette invece che *«un numero
dispari `RCP.md` §4.5 lo rifiuta»*, come se la misura potesse chiudere la questione. Non può: è
`LEZIONI.md` §1.3, un banco che non riproduce non assolve. La protezione va nel programma, dove **I7**
la vuole — la pagina arrotonda al pari per difetto — e la misura può solo trovare un positivo.

```
MARCA: [R]
```

---

### R3.11 — S3a: lo stato peggiore dei tre non è registrabile, e il controllo chiede un canale della fase 4

```
DOVE:             fasi/01-filo-nudo.md, B1 riga S3a, colonna «il controllo positivo»:
                  «si batte la combinazione e si guarda da tutt'e due le parti: che la
                  SESSIONE l'abbia ricevuta e che il browser non abbia fatto anche la sua»
COSA CONTRADDICE: SPECIFICHE.md §7.3-bis (i tre stati, O8: «una prova che guarda solo il
                  lato della sessione dichiara verde proprio il caso peggiore»);
                  B12 dello stesso documento, che manda il canale di input alla fase 4;
                  LEZIONI.md §1.9 (zero e fallimento con lo stesso aspetto)
```

**Come si dimostra.** Due difetti, e il primo è quello che rende la misura non solo incompleta ma
**invertita**.

**(a) Quando il browser esegue il suo comando, il testimone muore con lui.** L'ingresso concreto è
`Ctrl+W` su DeX. Lo stato vero è *«consegnata **e** riservata»* — la pagina riceve il `keydown` **e**
il browser chiude la scheda. Se il registro della prova vive nella pagina (una `<div>`, una variabile,
la console), **la chiusura della scheda porta via il registro**: il banco non trova traccia della
battuta e scrive «non consegnata», cioè lo stato **opposto**. E O8 dichiara che il secondo è *«il
peggiore»* proprio perché la sessione riceve la battuta e la scheda si chiude: un banco che lo
classifica come «non consegnata» dichiara innocuo il caso pericoloso.

Il registro deve **uscire dal dispositivo prima che la scheda muoia**, o non esiste. ⭐ **E la cura è
già scritta nel rapporto**: S3 §4.3 ordina le undici combinazioni *«dalla meno rischiosa alla più
rischiosa … **in quest'ordine, e una per volta**, perché quelle in fondo chiudono la scheda e portano
via il registro»*, e mette `Ctrl+T`, `Ctrl+N` e `Ctrl+W` **ultime**, *«e con il registro già copiato
fuori»*. Nel documento di fase non c'è né l'ordine né la copia — cioè è caduta la sola riga che rende
la misura possibile. ⚠ E con essa sono caduti i **quattro controlli positivi** che S3 §4.2 impone
*«prima di ogni sessione di misura»* e *«da rifare a ogni motore»*: che una battuta nuda arrivi (*«senza
questo, ogni «non è arrivata» è ambiguo fra «il browser se l'è tenuta» e «il banco era sordo»»*), che
arrivi una combinazione con modificatori, che gli appunti in uscita funzionino, e che lo schermo
intero **non** sia entrato con `F11` — perché con `F11` *«la keyboard lock non esiste, e non lo dice»*,
e tutte le prove che seguono non valgono niente.

**(b) «Che la sessione l'abbia ricevuta» chiede una sessione che riceva.** Alla fase 1 **non c'è
canale di input**: B12 lo scrive, mandando *«il rilascio dei tasti al distacco»* alla fase 4 perché
*«nasce col canale di input»*. Quindi o «la sessione» qui vuol dire «la pagina» — e allora la
formulazione è sbagliata e induce chi scrive il banco a cercare qualcosa che non esiste — oppure S3a
non è misurabile in questa fase.

```
MARCA: [R]
```

---

### R3.12 — S3b: la PWA non si può installare nella configurazione della fase

```
DOVE:             fasi/01-filo-nudo.md, B1 riga S3b («la PWA su Chrome per Android»), e
                  «Che cosa deve produrre» («apre https://192.168.0.2:7447 nel browser»)
COSA CONTRADDICE: web.md §1.2 B e §3.2 — «dietro un'eccezione di certificato, su Chrome
                  il Service Worker NON si installa [R] ⇒ niente PWA»;
                  SPECIFICHE.md §7.3-bis — «una PWA vuole un certificato fidato»
```

**Come si dimostra.** La fase serve la pagina da `https://192.168.0.2:7447` con un certificato che il
server si genera da sé (`RCP.md` §4.1). Su quell'indirizzo il browser mostra l'avviso e l'utente
concede l'eccezione — ed è la strada dichiarata dal documento stesso, che ne misura la durata in S1b.

Dietro quell'eccezione, su Chrome, **il Service Worker non si installa** `[R]`. Senza Service Worker
non c'è PWA installabile. Quindi l'ingresso concreto è: si apre la pagina sul telefono, non compare
nessuna offerta di installazione, e S3b non ha **niente** su cui provare i tasti.

Le uscite sono due, e nessuna delle due è nel documento: o si procura un **certificato vero con un
dominio** per il solo scopo di misurare S3b — che è una dipendenza pesante e va dichiarata — oppure
**S3b non è una misura della fase 1** e va dove va la sua dipendenza. ⚠ Terza uscita: si dichiara che
S3b si misura **su Chrome desktop**, ma allora è la forma d'errore **E10** con il travestimento che
lo stesso documento vieta due righe più su — *«il Chrome del portatile lo fa» non dice niente del
Chrome del telefono*.

⭐ **E la posta in gioco è già scritta e non è alta**: `web.md` §1.2 B, corretto da `R2`, conclude che
fra schermo intero + lock e PWA *«ballano `F11` e poco altro»*, e che è *«un vantaggio, non una
categoria diversa»*. Una misura che costa un dominio per guadagnare `F11` va pesata con quel numero
davanti.

```
MARCA: [R]
```

---

### R3.13 — S2: l'unico canale che risponde davvero è stato omesso, e l'atteso in tabella importa E1

```
DOVE:             fasi/01-filo-nudo.md, B1 riga S2, e «Le misure» → riga S2,
                  colonna «Atteso»: «[S] sì da Chrome 108»
COSA CONTRADDICE: LEZIONI.md §1.11 regola 2 («se il componente sa rispondere, gli si
                  chiede»); web/rapporti/S2-decodifica.md §4.4 controllo C
                  (media-internals, «il ground truth del banco su Android»);
                  web.md §4.1 («prefer-hardware riuscito, powerEfficient: true e
                  fotogrammi corretti sono TUTTI compatibili con la CPU»)
```

**Come si dimostra.** Due cose.

**(a) Il canale diretto esiste su Android e non è nel banco.** S2 lo scrive: su Chromium
`media_codec_video_decoder.cc` registra `is_software_codec` con il **nome** che arriva da
`MediaCodec.getName()`, ed è raggiungibile su Android via `chrome://inspect` e debug remoto. Non è
una interfaccia JavaScript — `web.md` §9 punto 2 ha ragione a dire che *«il browser sa e non
risponde»* **da JavaScript** — ma il banco non è JavaScript: il banco è chi guarda. `LEZIONI.md`
§1.11 regola 2 è nata su mezza giornata di prove indirette per un dato che il compositore regalava
via D-Bus; qui il dato lo regala il browser via `chrome://inspect`, e il banco della fase 1 sceglie
**tre prove indirette** al suo posto (saturazione, canarina, decadimento). ⛔ Che le tre indirette
servano lo stesso — su iPhone quel canale non esiste, e S2 lo dichiara — non toglie che **su Android,
che è l'uso primario, si stia rinunciando alla risposta diretta**.

L'ingresso concreto: il telefono regge 4K60 con la canarina appena scalfita, il banco scrive
«hardware», e `chrome://inspect` avrebbe stampato `is_software_codec=true` su un chip recente che
decodifica HEVC software a quella portata. Il verdetto va nel prodotto (`DECISIONI.md` §2.7) e ci
resta.

**(b) L'atteso in tabella è la forma d'errore che tutto S2 esiste per denunciare.** La colonna
«Atteso» della riga S2 dice `[S] sì da Chrome 108`. Chrome 108 documenta il **supporto a HEVC Main10
in WebCodecs**, non la decodifica **in hardware** — ed è esattamente la distinzione su cui `web.md`
§1.1 punto 2 costruisce la seconda delle cinque cose che lo studio ha cambiato. Scrivere quel `[S]`
come atteso di una misura di *hardware* mette **E1 nella casella dell'aspettativa**: chi misura parte
sapendo che «dovrebbe essere sì», e le tre prove indirette sono di quelle che si leggono con
indulgenza quando l'atteso è già scritto.

```
MARCA: [R]
```

---

### R3.14 — I dispositivi di misura non sono dichiarati, e il documento della fase 0 li rimanda alla fase 2

```
DOVE:             fasi/01-filo-nudo.md, B1 (tutte le nove righe) e «Le misure» →
                  «la sonda del browser», colonna «Dispositivo e motore», vuota o
                  generica in tutte e nove le righe
COSA CONTRADDICE: fasi/00-ambiente.md, «Quel che resta fuori da questa fase, per scelta»
                  — «adb, Desktop AVD, il telefono vero | l'ambiente Android serve alla
                  sonda della FASE 2, e l'utente ha chiesto di lasciarlo stare per ora» —
                  e «Che cosa resta [?]» → «⏳ l'ambiente Android: non ancora toccati.
                  Servono alla sonda della fase 2, NON PRIMA»;
                  LEZIONI.md §2.5-bis («i banchi dipendono da cose che il provisioning
                  non installa»)
```

**Come si dimostra.** La sonda è stata spostata alla **fase 1** (`PIANO.md` §1.2: *«prima di tutto»*),
e il documento della **fase 0**, chiuso ieri, dichiara che l'ambiente che le serve non è stato toccato
perché *«serve alla sonda della fase 2, non prima»*. **Le due frasi non possono essere vere insieme**,
e quella che vince decide se sei delle nove misure si fanno.

Il censimento delle dipendenze, che il documento non fa:

| Misura | Che cosa richiede | C'è? |
|---|---|---|
| **S1a** | un **Mac** (Safari 26.4), un **iPhone o iPad**, e — lo scrive S1 §4.3 — **l'iPhone collegato al Mac** con il Web Inspector, perché su Safari non esiste `net-export`; più **due certificati distinti**, generati con i comandi di S1 §4.1, e una **pagina sonda a quattro pulsanti** con un `/sw.js` da servire | ⛔ non nominati in nessun documento del progetto come ferro disponibile |
| **S2** | il **telefono vero**; **cinque sequenze di prova** prodotte dal nostro `hevc_vaapi` (S2 §4.1: 4K60 Main10, 4K60 Main 8 bit, 1080p60 Main10, VP9 per i controlli, e la rampa di grigio per i 10 bit); e un **PC collegato** per `chrome://inspect` | ⛔ telefono dichiarato non toccato; le sequenze non sono nominate, e dipendono dal codificatore |
| **S3a** | un dispositivo **DeX** (Android 16 QPR1: la lock esiste solo da lì) — e S3 §4.4 non chiede «DeX», chiede **sei combinazioni motore-sistema**: Chrome/Linux-Wayland, Firefox ≥ 151/Linux, Chrome/Windows, Chrome/DeX, Safari ≥ 26.4/macOS, Safari/**iPadOS con tastiera fisica** | ⛔ non nominati |
| **S3b** | telefono Android **e** un certificato fidato (R3.12) | ⛔ |
| **S5** | telefono **e** DeX (*«che cosa risponde `screen` su DeX»*) | ⛔ |
| **B2** | tutti e tre i motori ⇒ di nuovo il **Mac** | ⛔ |
| **B10** | un **secondo utente** sul server, con una parola d'ordine, che PAM sappia autenticare | ⛔ non nominato, e non è in `provision-server.sh` |
| **S7** | sessione GNOME e `libei` | ✅ `banchi/00-sessione-gnome.sh`, `libei1` 1.3.901 `[M]` |
| **B9** | `python3-aioquic` 1.2 | ✅ `[M]`, ⚠ ma vedi R3.21 |

⛔ **Una dipendenza non dichiarata è una misura che non si fa** — e la forma è già stata pagata due
volte in questo progetto nello stesso giorno: `weston` che non era in `provision-server.sh`, e i
gruppi `adm`/`systemd-journal` che nessuno aveva chiesto (`fasi/00-ambiente.md`, voci 5 e 7).
`LEZIONI.md` §2.5-bis lo dice con queste parole: *«le dipendenze installate a mano diventano
invisibili nel giro di un giorno»*. Qui non sono nemmeno installate a mano: **non esistono**, e il
documento le dà per esistenti scrivendo nove righe di tabella con la colonna «Misurato» vuota.

⭐ **E il conto va fatto adesso perché cambia il piano**: se il Mac e l'iPhone non ci sono, **S1a non
si misura**, `B2` non può applicare il suo criterio dei tre motori, e la riga di `DECISIONI.md` §1.7
resta aperta. Dichiararlo costa una riga; scoprirlo a metà lavoro costa la fase.

```
MARCA: [R]
```

---

### R3.15 — Tre caselle «controllo positivo» su nove non contengono un controllo positivo

```
DOVE:             fasi/01-filo-nudo.md, B1, colonna «Il controllo positivo»,
                  righe S1b, S3a e S3b
COSA CONTRADDICE: REVIEWER.md §1 punto 5; LEZIONI.md §1.9 regola 2
                  («lo strumento sa trovare qualcosa che c'è di sicuro?»)
```

**Come si dimostra.** Riga per riga, testualmente:

| Riga | Che cosa c'è nella casella | Che cos'è davvero |
|---|---|---|
| **S1b** | *«`[R]` l'attesa è **una settimana** (`kCertErrorBypassExpirationInSeconds = 604800`): si guarda l'orologio, non il ricordo»* | ⛔ è **l'atteso**, più una raccomandazione di metodo. Non dice come lo strumento dimostra di saper vedere la scadenza |
| **S3a** | *«si batte la combinazione e si guarda da tutt'e due le parti»* | ⛔ è **la procedura della misura**, cioè la definizione dei tre stati di O8 |
| **S3b** | *«la lista riservata si legge provando i tasti, non fidandosi del `[R]` su Chromium desktop»* | ⛔ è **il metodo**, ed è un avvertimento contro E10. Non è un controllo |

L'ingresso concreto che mostra perché conta, su S1b: si concede l'eccezione lunedì; giovedì il
certificato **della pagina** viene rigenerato perché qualcuno ha riavviato il server e la
generazione non era idempotente; venerdì l'avviso ricompare. Il banco scrive «l'eccezione è durata
quattro giorni», e la frase che si dirà all'utente nasce sbagliata. Il controllo mancante è quello
che distingue le due cause: **l'impronta del certificato della pagina, letta all'inizio e alla fine
della prova, deve essere la stessa**. Costa due righe.

⚠ **E una nota sul calendario, che non è un rilievo ma va detta**: S1b è l'unica misura di questa
fase che richiede **sette giorni di tempo reale**, e la fase non può chiudersi prima. O si dichiara
come misura a cavallo delle fasi, o si dichiara come si accelera (l'orologio della macchina), e
allora il controllo positivo diventa *«spostando l'orologio di sei giorni l'eccezione c'è ancora»* —
che è un controllo vero.

```
MARCA: [R]
```

---

### R3.16 — S1a e S1b misurano uno stato che sopravvive al giro, e C3 non lo sa

```
DOVE:             fasi/01-filo-nudo.md, B1 righe S1a e S1b, e B11 riga C3
                  («si esegue tutto due volte di fila, senza rimettere niente […]
                  ⚠ Qui morde davvero: i contatori dei tentativi di §4.4-bis
                  sopravvivono al giro precedente»)
COSA CONTRADDICE: LEZIONI.md §2.3-quinquies, corollario («quel che resta dal giro prima
                  va svuotato all'inizio»); LEZIONI.md §2.3-ter
```

**Come si dimostra.** C3 elenca **una** cosa che sopravvive fra i giri. Ne sopravvivono almeno
quattro, e tre stanno nel banco che il documento mette per primo:

1. **l'eccezione concessa sul certificato della pagina** — è lo stato che S1a e S1b *misurano*. Al
   secondo giro non c'è più nessun avviso da concedere: S1a misura una connessione su un certificato
   già fidato e conclude che l'eccezione copre WebTransport, che è la conclusione **opposta** a quella
   di `web.md` §3.1 e sarebbe un `[M]` falso contro due `[R]`;
2. **il certificato della sessione già ruotato** dalla terza riga di B3: al giro dopo l'impronta nella
   pagina è già quella nuova, e la prova *«della scheda lasciata aperta due settimane»* non ha più
   niente da mostrare;
3. **la sessione creata al giro prima**, che `SPECIFICHE.md` §5.2 fa sopravvivere al client. L'ingresso
   concreto: il secondo giro parte **entro trenta secondi** dal primo, la prima connessione di B3
   trova una sessione ancora viva per quell'utente e riceve `CONGEDO(GIA_ATTIVA_REMOTA)`. La riga «1ª
   connessione: stretta di mano completa fino a `SESSIONE`» dà **rosso su codice giusto**, e chi
   guarda penserà di aver rotto la stretta di mano;
4. **il permesso `clipboard-read`** — S3 §4.6 lo scrive: *«la prima esecuzione mostra la richiesta, la
   seconda no — e i due esiti sono **diversi**. Il banco deve dire quale dei due sta misurando, e deve
   saper ripartire da permesso revocato»*;
5. i contatori di §4.4-bis, gli unici dichiarati.

⚠ **E S1 §4.5 ha già un elenco di «errori che rovinano la misura» che il documento di fase non
riporta**, e sono tutti di questa famiglia: finestra normale contro navigazione privata (che è uno
stato diverso dell'eccezione), lo stesso certificato usato per i due scopi, `localhost` invece di un
indirizzo di rete, `Alt-Svc` acceso, e — la più semplice — **non annotare la versione esatta del
browser**: *«un risultato senza versione, fra sei mesi, non vale niente»*. La tabella «Le misure» ha
la colonna «Dispositivo e motore» e non ha la versione.

⭐ **La cura non è ricordarsi**: è che il banco **dichiari il proprio stato iniziale** e lo verifichi,
come `00-c1-kwin.sh` verifica che il socket di KWin non ci sia più prima di partire. Un banco che non
sa da che stato parte misura la storia della macchina.

```
MARCA: [R]
```

---

### R3.17 — C2 non copre il modo di fallire che questo progetto ha già pagato

```
DOVE:             fasi/01-filo-nudo.md, B11 riga C2: «si punta il banco su una porta dove
                  non c'è nessuno | ⛔ deve dire «sono fallito», non «zero»»
COSA CONTRADDICE: web/rapporti/R2-revisione-web.md rilievo R1 e web.md §3.3 — il caso
                  concreto è testualmente «il firewall del server blocca UDP 7447»;
                  LEZIONI.md §1.9
```

**Come si dimostra.** C2 prova **il caso facile**: nessuno in ascolto ⇒ rifiuto immediato ⇒ il banco
deve dichiararsi fallito. È giusto e va tenuto. Ma la configurazione di questa fase ha **due
ascoltatori sulla stessa porta** (`RCP.md` §2.4: TCP per la pagina, UDP per WebTransport), e il modo
di fallire che conta è quello **asimmetrico**:

| Il guasto | Che cosa vede il banco |
|---|---|
| ⛔ **UDP 7447 filtrato, TCP 7447 risponde** | la pagina **si carica**, il banco parte, la sessione WebTransport non si apre mai. Nessun rifiuto: un'attesa |
| il certificato della sessione ha 15 giorni | `serverCertificateHashes` rifiuta `[S]`, e il sintomo è identico al precedente |
| l'impronta nella pagina non è quella corrente | idem |

⛔ **Sono tre cause con lo stesso aspetto**, e sono precisamente le tre che rendono rossa **ogni**
misura di B1 e di B2 insieme. Il caso del firewall non è un'invenzione mia: è il caso concreto con cui
`R2` ha dimostrato che il primo controllo positivo del progetto era cieco, e la sua conclusione era
*«il banco scrive «l'eccezione di Safari non copre», che è la conclusione sbagliata sul dato
mancante»*. La cura è entrata in S1a (ed è quella giusta) **e non è entrata in C2**, che è il posto
dove vale per tutti i dodici banchi.

⭐ **La forma che C2 dovrebbe avere, e costa una riga per ciascuna**: si guasta il collegamento in
**tre** modi diversi — nessuno in ascolto, UDP filtrato con TCP vivo, impronta sbagliata — e si
verifica che il banco dia **tre diagnosi diverse**. Un banco che le confonde dirà «il server non
risponde» il giorno in cui il certificato è scaduto.

```
MARCA: [R]
```

---

### R3.18 — C5 cita come modello un file il cui difetto è dichiarato aperto nella fase precedente

```
DOVE:             fasi/01-filo-nudo.md, B11 riga C5: «ogni banco stampa l'atteso prima
                  della misura, come banchi/00-c1-kwin.sh»
COSA CONTRADDICE: fasi/00-ambiente.md, «I sedici rilievi non ancora curati» —
                  «l'atteso di 00-c1-kwin.sh è STAMPATO E NON CONFRONTATO, ed è scritto
                  con la virgola mentre il misuratore stampa il punto | prossimo giro»;
                  invariante I7
```

**Come si dimostra.** `00-c1-kwin.sh` stampa `atteso da kde.md §5.7: 59,2 fps` e poi lascia il
confronto a chi guarda: lo stato d'uscita è quello del misuratore, non del confronto. La revisione
della fase 0 l'ha trovato e la cura è dichiarata **non fatta**, rimandata al «prossimo giro».

L'ingresso concreto, sul banco di questa fase: B6 stampa `atteso: 60 s`, il server sbaglia e chiude a
30 s per la mancanza dei PING, il misuratore stampa `59,8` — no, stampa `30,1` — e **esce con zero**,
perché nessuno confronta. Nella tabella «Le misure» finisce un numero, e chi la riempie a fine
giornata legge la colonna «Atteso» e la colonna «Misurato» e le confronta **a memoria**. È la voce 11
della fase 0, alla lettera: *«Confrontato con la colonna sbagliata, il banco sembrava sbagliare di
dieci fotogrammi»*, la cui cura è scritta così — *«la cura è nel banco, non nella memoria di chi
legge»* — e qui viene citata **prendendo il file che la cura a metà**.

⛔ **E il difetto della virgola contro il punto è quello che morde per primo**: se qualcuno scrive il
confronto copiando la forma del modello, confronta `"60"` con `"60,0"` e ottiene un rosso su un
codice giusto. Che è `LEZIONI.md` §2.3, il banco della rotella che cercava `asse dy=-10` mentre il
registro scriveva `asse dx=0 dy=-10`.

```
MARCA: [R]
```

---

### R3.19 — B3: la riga dei trenta secondi è indistinguibile dal tempo di inattività di QUIC

```
DOVE:             fasi/01-filo-nudo.md, B3, ultima riga: «la 2ª dopo 30 secondi di
                  silenzio della 1ª | ⭐ entra: un client silenzioso non è più attaccato,
                  e il discrimine è l'orologio del silenzio»
COSA CONTRADDICE: RCP.md §2.2, «max_idle_timeout | 30 s, imposto dal server | è
                  l'orologio del silenzio»; DECISIONI.md §4.4 e §4.5;
                  LEZIONI.md §1.3
```

**Come si dimostra.** I due orologi sono lo stesso numero, e uno dei due lo fa girare il trasporto
senza che nessuno scriva una riga. L'ingresso concreto: si scrive un server che **non ha nessuna
nozione di sessione staccata** — nessun orologio del silenzio, nessuna liberazione, niente. Dopo
trenta secondi di silenzio della prima connessione, QUIC la chiude da sé per `max_idle_timeout`; il
server vede la connessione morire e libera tutto perché la sua struttura è legata alla connessione; la
seconda arriva e **entra**. ✅ La riga di B3 è verde, e il meccanismo che dichiara di misurare **non
esiste**.

⛔ **E il difetto vivo non è teorico**: legare la sessione alla connessione è esattamente quel che
l'invariante **I4** vieta (*«il palco appartiene alla sessione»*), ed è il difetto che in v1 *«rendeva
la sessione inutilizzabile dopo il primo distacco»* (`SPECIFICHE.md` §5.2). Il banco che dovrebbe
sorvegliare il confine fra i due lo attraversa senza accorgersene.

⭐ **Il caso che distingue esiste e costa una riga**: la prima connessione **tace 25 secondi** — sotto
i trenta — e la seconda arriva. Un server con l'orologio del silenzio la rifiuta con
`GIA_ATTIVA_REMOTA`; un server che si affida a QUIC ha ancora la prima viva e la rifiuta anche lui…
⚠ e infatti nemmeno questo distingue. Il caso che distingue davvero è **35 secondi con
`max_idle_timeout` alzato a 120** nel banco: se il server ha l'orologio suo, la seconda entra; se non
ce l'ha, la prima è ancora viva e la seconda è rifiutata. Il che vuol dire che **il banco deve poter
cambiare un parametro di trasporto**, e questo è il tipo di cosa che va deciso quando si sceglie la
libreria (B2), non quando si scrive B3.

⚠ **E la riga della chiave ruotata ha lo stesso problema, in piccolo**: *«il banco cambia la chiave e
riprova»*. Nel prodotto la chiave cambia perché *«il server rigenera il certificato prima che
scada»* (`RCP.md` §4.1-bis) — cioè per un orologio a quattordici giorni. Un banco che la cambia a mano
prova che la pagina sa ritirare l'impronta corrente, e **non prova che la rotazione automatica
avvenga**: quella resta senza banco, e il suo sintomo — *«non si collega più e non dice perché»* —
arriva quattordici giorni dopo la consegna.

```
MARCA: [R]
```

---

### R3.20 — B7: «8 su 8» non dice che cosa fa passare una riga

```
DOVE:             fasi/01-filo-nudo.md, B7 (ultimo riquadro: «Ogni motivo si mostra
                  all'utente in una frase comprensibile […] Il banco guarda lo schermo,
                  non il codice numerico») e «Le misure» → «B7 — gli otto motivi, dal
                  lato che riceve | 8 su 8»
COSA CONTRADDICE: RCP.md §8.2 — «⛔ Ogni motivo DEVE essere mostrabile all'utente in una
                  frase comprensibile. BUDGET_PIENO non è «errore 6»»;
                  invariante I8; LEZIONI.md §2.2
```

**Come si dimostra.** L'ingresso concreto è una `switch` con il ramo predefinito, che è la cosa che
chiunque scrive per prima:

```
default: mostra("Errore " + codice);
```

Il banco stacca otto volte, otto volte trova nel DOM una stringa non vuota, e scrive **8 su 8**.
L'utente legge *«Errore 14»* per `SESSIONE_NON_SERVIBILE`, che è la frase che `RCP.md` §8.2 vieta con
un ⛔ e un esempio quasi identico.

`LEZIONI.md` §2.2 è la lezione esatta: *«un banco che conta non basta»*. Qui conta otto.

⭐ **I due criteri che rendono la riga misurabile, e non costano niente**: le otto frasi devono essere
**distinte fra loro** (una `switch` senza rami dà otto stringhe uguali), e **nessuna deve contenere il
numero del motivo** né la parola «errore» seguita da una cifra. Un `grep` di due righe.

⚠ **E «il banco guarda lo schermo» non è eseguibile da un banco.** O si legge il DOM — che è
guardare il codice della pagina, ed è l'unica cosa che una prova automatica può fare — o si guarda
davvero, e allora è **l'utente** (I8) e va nella sezione del giudizio, non in una tabella con «8 su
8». Il documento promette la seconda e potrà fare solo la prima: dichiararlo evita che qualcuno legga
la riga come già coperta.

```
MARCA: [R]
```

---

### R3.21 — B9: la separazione che dà valore al cliente di prova è una regola, non un meccanismo

```
DOVE:             fasi/01-filo-nudo.md, B9: «⛔ Chi lo scrive non guarda il C né la
                  pagina. Se li guardasse ne erediterebbe i fraintendimenti, e non
                  servirebbe più a niente»
COSA CONTRADDICE: invariante I7 («la protezione sta nel programma»);
                  fasi/00-ambiente.md voce 6 («è rimasta una nota in un documento.
                  È l'invariante I7 al contrario»);
                  PIANO.md §0.4 («due programmi scritti dalla stessa mano che vanno
                  d'accordo non confermano niente»)
```

**Come si dimostra.** Il valore intero di B9 — l'unico sostituto rimasto dell'arbitro perduto,
insieme a `RCP.md` e al validatore — poggia su una frase che chiede a qualcuno di **non guardare** un
file che ha davanti. Non c'è nessun meccanismo: nessun ambiente separato, nessuna copia del solo
`RCP.md`, nessuna regola su chi lo scrive e con quale contesto.

L'ingresso concreto, ed è quello che questo progetto ha già pagato: la fase 0 aveva scritto in
`LEZIONI.md` §2.5-bis, il 7 agosto, che `/media` non si monta da sola. Il 9 agosto il riavvio ha
trovato la macchina irrecuperabile, e il documento lo scrive così: *«la lezione era già scritta […] la
cura non è mai stata applicata: è rimasta una nota in un documento. È l'invariante **I7** al
contrario — la protezione di un difetto noto non stava in una riga di configurazione che si può
perdere, stava in una **memoria**, che è peggio»*. B9 sta scommettendo l'unico arbitro esterno del
progetto su una memoria.

⭐ **Il meccanismo esiste e costa poco**: chi scrive il cliente di prova riceve `RCP.md` e i suoi
riferimenti, e **non** l'albero del server e della pagina; e la cosa si dichiara nel documento, così
che il giorno in cui il cliente di prova concorderà col server si sappia se quella concordanza vale
qualcosa. Senza, il verde di B9 è indistinguibile da un verde ereditato.

⚠ **E una dipendenza da verificare, che è il criterio di B2 non riapplicato a B9**: il documento dà
`python3-aioquic` 1.2 come *«quel che serve esattamente a questo»*. Ma B2 dichiara, due sezioni sopra,
che il criterio è cambiato — *«non basta più che la libreria parli QUIC, deve portare HTTP/3 e
WebTransport»*. Che `aioquic` 1.2 porti **WebTransport lato client** non è `[M]` da nessuna parte, e
se non lo porta il cliente di prova non esiste — cioè cade l'arbitro, e ce ne si accorge dopo aver
scritto il server. È la stessa domanda di B2, non fatta al pezzo che ci si è già fidati di avere.

```
MARCA: [R]
```

---

### R3.22 — S6: attribuisce al motore una grandezza del percorso

```
DOVE:             fasi/01-filo-nudo.md, B1 riga S6: «quanto porta davvero un datagram
                  SU CIASCUN MOTORE», e «Le misure» → riga S6, «Dispositivo e motore:
                  tre motori»
COSA CONTRADDICE: RCP.md §5.3, che dice «su un PERCORSO vero il carico utile disponibile
                  è ~1200 byte [S]»; forma d'errore E2 (due misure diverse sotto la
                  stessa etichetta)
```

**Come si dimostra.** Quanto porti un datagram QUIC lo decide il **cammino** — la MTU più piccola fra i
due estremi, meno le intestazioni IP/UDP/QUIC — non il motore del browser. Il motore decide solo che
cosa **dichiara** l'API, che è la cosa che la riga stessa dice di non credere (*«il numero dichiarato
dall'API non è il numero che passa sul percorso»*).

L'ingresso concreto: si misura in laboratorio, telefono e server sulla stessa LAN a MTU 1500. Tutti e
tre i motori portano ~1350 byte. Il banco scrive «1350 su tre motori su tre» e la casella «Che cosa
decide» autorizza a **tenere i 972 del PCM, o ad alzarli**. L'utente si collega da fuori attraverso
una VPN a MTU 1400 — o da LTE, che è lo scenario dichiarato — e i datagram da 1350 non arrivano più.
`RCP.md` §5.3 dice che il danno è doppio, perché il PCM è **il controllo positivo di Opus**: il giorno
in cui Opus non si negozia si ripiega su una strada che non esiste.

⭐ **La misura giusta ha la stessa forma e un'etichetta diversa**: si dichiara **il percorso** accanto
al numero, esattamente come la fase 0 dichiara la scena accanto a ogni fotogramma al secondo
(`LEZIONI.md` §1.1), e si misura sul percorso **peggiore** che si intende servire, non su quello
comodo. E se il numero deve essere un tetto di protocollo, allora non si misura affatto: si prende il
minimo garantito da QUIC, che è quel che i 972 byte già fanno.

```
MARCA: [R]
```

---

### R3.23 — Quattro righe della tabella delle misure hanno l'atteso vuoto

```
DOVE:             fasi/01-filo-nudo.md, «Le misure» → «Il filo»: le righe B2, B3, B9 e
                  B10 hanno la colonna «Atteso» vuota
COSA CONTRADDICE: B11 riga C5 dello stesso documento («ogni banco stampa l'atteso PRIMA
                  della misura […] il banco dice da sé se ha risposto o no, invece di
                  lasciarlo giudicare a memoria»);
                  fasi/00-ambiente.md, difetto 11
```

**Come si dimostra.** Sei righe su dieci hanno l'atteso (`6 su 6`, `cade sempre`, `5 s · 60 s · 10 s`,
`8 su 8`, `≥ 1 s`, `4 rossi su 4`). Quattro no — e sono le quattro in cui l'esito è un giudizio, non
un numero:

- **B2**: che cosa vuol dire che la prova è passata? *«tutti e tre i motori aprono la sessione»* sta
  nel testo di B2 e non nella tabella; e il criterio vero — *«il numero di righe che restano a noi»* —
  non ha né un atteso né una soglia, quindi la scelta fra `quiche` e `ngtcp2` si farà **a giudizio**;
- **B3**: quattro esiti in una riga sola, e tre di essi sono opposti fra loro (passa, passa,
  **rifiutata**, passa). Un `✅` in quella casella non dirà quale dei quattro;
- **B9**: *«il cliente di prova completa la stretta di mano»* — e B9 dichiara nel suo testo che
  *«il suo esito più prezioso **non** è «passa»»*, cioè che la casella misura la cosa meno
  interessante;
- **B10**: *«un secondo utente entra»*, senza dire da dove, con quale nome, e con quale controllo che
  non sia entrato per un'altra ragione (R3.26).

Il difetto 11 della fase 0 è nato esattamente da qui, e la sua cura è citata da C5: *«un banco che
conosce il proprio atteso non lascia il confronto a chi guarda»*. Quattro righe su dieci lo lasciano
a chi guarda, in un documento che chiude C5 con quella frase.

```
MARCA: [R]
```

---

### R3.24 — Che cosa questi dodici banchi non coprono affatto, di quel che la fase 1 produce

```
DOVE:             fasi/01-filo-nudo.md, l'insieme dei dodici banchi, letto contro
                  «Che cosa deve produrre» e contro PIANO.md fase 1
COSA CONTRADDICE: RCP.md §4.1-bis (due certificati), §4.4 nota finale (la parola
                  d'ordine), §2.3 (0-RTT e migrazione), §2.2 (max_idle_timeout),
                  §6.1 (il tetto di 1 MiB); PIANO.md fase 1 («il server acquista qui il
                  suo secondo mestiere: servire la pagina»)
```

**Come si dimostra.** Sei cose che la fase produce e che nessuno dei dodici banchi guarda. Tre hanno
un ⛔ scritto in `RCP.md`.

| # | Che cosa non è misurato | Il caso concreto, e quando morde |
|---|---|---|
| **1** | ⛔ **che i due certificati siano due** (`RCP.md` §4.1-bis) | il server ne genera uno solo, a scadenza breve, e lo usa per la pagina **e** per la sessione. Tutti i dodici banchi passano — la stretta di mano funziona, l'impronta torna, l'eccezione si concede. Il sintomo arriva **quattordici giorni dopo**: l'avviso ricompare, e §4.1-bis dichiara che *«nessuno collegherebbe le due cose»*. B3 tocca la rotazione ma non la **distinzione** |
| **2** | ⛔ **che la parola d'ordine non compaia in nessun registro** (`RCP.md` §4.4) | la fase riusa `registro.c` (140 righe), che in v1 è *«un registratore di battitura»*, e aggiunge un registratore di byte decifrati (R3.6). Un `grep` della parola di prova su tutti i file prodotti dal giro costa una riga e non c'è |
| **3** | ⛔ **che il server non offra 0-RTT e non disabiliti la migrazione** (`RCP.md` §2.3) | sono due proprietà della **libreria scelta da B2**, e le librerie QUIC offrono 0-RTT per impostazione predefinita. Il sintomo di 0-RTT acceso è che `CREDENZIALI` si può **ripetere** — cioè un difetto di sicurezza che non produce nessun sintomo funzionale, mai |
| **4** | **che `max_idle_timeout` sia davvero 30 s e sia imposto dal server** (`RCP.md` §2.2) | è il numero da cui dipendono B3 (R3.19), B6 e l'intero modello del client staccato. Nessuno lo legge |
| **5** | **la pagina servita in TCP**, che è il secondo mestiere che il server acquista in questa fase | nessun banco verifica che la pagina si carichi, che pubblichi l'impronta **corrente**, e che l'endpoint da cui si ritira l'impronta aggiornata (§4.1-bis) esista. B3 lo presuppone in una riga |
| **6** | **il campo `desktop` di `SESSIONE`** | sul ferro c'è solo GNOME: un server che risponde `gnome` costante passa. Il valore `sconosciuto` — e i quattro desktop che le fasi dei desktop nuovi (11-12) aggiungeranno — non hanno controllo positivo, e `RCP.md` §4.5 vieta al client di cambiare comportamento su quel campo proprio perché è per la diagnosi |

⚠ **E una settima che non è un buco ma un confine da rileggere**: la fase dichiara che `stato` vale
sempre `NUOVA`. Nessun banco verifica che valga **sempre** `NUOVA` — cioè che nessuno abbia scritto
per prudenza un ramo che risponde `RIPRESA` e che nessuno proverà fino alla fase 5. Un `[?]`
implementato a metà e non provato è quel che il riquadro del confine dice di voler evitare.

```
MARCA: [R]
```

---

### R3.25 — S7: il segno della rotella potrebbe essere di una riga di configurazione, e si misura su un compositore solo

```
DOVE:             fasi/01-filo-nudo.md, B1 riga S7 e il riquadro sotto («Si misura sul
                  server, con libei e una sessione GNOME di quelle che la fase 0 sa già
                  avviare»)
COSA CONTRADDICE: forma d'errore E11 (una dipendenza presa dal contorno del desktop, la
                  cui cura è una riga di configurazione diversa su ciascun desktop);
                  RCP.md §7.3, che è normativa per tutti e cinque i desktop
```

**Come si dimostra.** Due dubbi, e li dichiaro come dubbi perché non li ho misurati.

**(a) Lo scorrimento naturale.** Se il compositore applica ai dispositivi emulati di `libei` le stesse
trasformazioni che applica a un mouse vero — e `org.gnome.desktop.peripherals.mouse natural-scroll`
è una di quelle — allora `+120` iniettato in una sessione con lo scorrimento naturale **acceso** e
`+120` con lo scorrimento **spento** muovono la pagina in due versi opposti. Il controllo dichiarato
(`-120`) non se ne accorge: distingue il segno, non l'origine del segno. Il numero che finirebbe in
`RCP.md` §7.3 sarebbe **il segno di una gsetting della sessione di prova**, e il sintomo dalla parte
dell'utente sarebbe *«la rotella va al contrario»* su metà delle installazioni. ⭐ **Il controllo che
lo chiuderebbe costa un comando**: si misura con la gsetting nei due stati e si verifica che il segno
**non** cambi; se cambia, si dichiara quale stato si assume e dove il server lo neutralizza.

**(b) Un compositore per una riga che ne vincola cinque.** `RCP.md` §7.3 vale per GNOME, KDE, XFCE,
LXQt e Cinnamon. La misura è su Mutter. Se `libei` normalizza, il numero vale ovunque; se la
normalizzazione è del compositore, la fase di KDE (la 11) troverà un segno diverso su KWin e non saprà se
correggere il protocollo o il server. ⚠ La fase 0 ha già fatto la cosa giusta in un caso identico —
ha misurato **tre** famiglie di compositori nello stesso pomeriggio, e ha scritto che la riga di sway
*«vale doppio, perché il modello è l'opposto»*. Qui la stessa domanda ha una sola risposta.

⭐ **E va detto quel che il controllo di S7 fa bene**: il `-120` è un controllo vero, del tipo che
`LEZIONI.md` §1.11 regola 1 chiede — dice che aspetto avrebbe il caso opposto — ed è meglio scritto
della maggior parte delle altre otto caselle di B1.

```
MARCA: [?]
```

---

### R3.26 — B10: «credenziali errate» ha più di una causa, e il banco ne nomina una

```
DOVE:             fasi/01-filo-nudo.md, B10 («Il banco autentica un utente DIVERSO da
                  quello che possiede il processo del server […] ⚠ E il sintomo, per
                  tutti gli altri, è «credenziali errate»»)
COSA CONTRADDICE: LEZIONI.md §1.6 («non si deduce: si chiede») e §1.9 regola 3;
                  forma d'errore E2; SPECIFICHE.md §5.5, che vuole un servizio di
                  sistema per dieci utenti
```

**Come si dimostra.** B10 è giusto nel puntare `autenticazione_utente_atteso()` — quello è un difetto
`[R]`, letto nel codice. Il rilievo è sul **banco**: il suo unico segnale è «entra / non entra», e
«non entra» ha almeno quattro cause, tre delle quali non sono il difetto cercato:

1. `autenticazione_utente_atteso()` è ancora lì — il difetto;
2. il contatore per indirizzo di §4.4-bis è nella sua finestra (R3.8);
3. il processo del server non riesce a verificare la parola d'ordine di **un altro** utente: dipende
   da come è composta la pila PAM del servizio e da chi possiede il processo. ⛔ **E chi possiede il
   processo del server non è scritto da nessuna parte in questo documento** — B10 si definisce
   *«un utente DIVERSO da quello che possiede il processo»* senza dire chi sia, mentre
   `SPECIFICHE.md` §5.5 lo vuole di sistema;
4. il secondo utente non esiste sulla macchina, o non ha una parola d'ordine (R3.14).

L'ingresso concreto: si toglie la guardia, si crea `prova`, si prova, il server risponde
`CREDENZIALI_ERRATE`. Il documento dice che *«il sintomo, per tutti gli altri, è «credenziali
errate»»* — quindi chi legge quel rosso concluderà che la guardia non è stata tolta bene, e andrà a
cercare nel posto sbagliato. È la forma di `LEZIONI.md` §1.6: tre diagnosi sbagliate su chi uccideva
il server perché il mittente non era mai stato **chiesto**.

⭐ **Il controllo che manca è di quelli che costano dieci secondi**: prima di credere al rosso, si
verifica che la stessa parola d'ordine **funzioni fuori dal server** — un `su - prova`, o
`pamtester` sullo stesso servizio PAM. Se fallisce anche lì, non si sta misurando il server. È il
controllo positivo di `LEZIONI.md` §1.9 regola 2, applicato allo strumento «PAM» invece che al banco.

```
MARCA: [?]
```

---

### R3.27 — B6: «TLS finito» non è un istante che i due lati condividono

```
DOVE:             fasi/01-filo-nudo.md, B6, prima riga della tabella:
                  «TLS finito | CIAO | 5 s, poi TEMPO_SCADUTO 0x0D»
COSA CONTRADDICE: RCP.md §4.6 (stessa riga) letta insieme a §2 (WebTransport su HTTP/3)
                  e §4.2 (il canale di controllo è il primo stream bidirezionale
                  DELLA SESSIONE)
```

**Come si dimostra.** In WebTransport la connessione HTTP/3 e la **sessione** sono due cose separate:
il browser completa il TLS, poi manda la richiesta di CONNECT estesa che stabilisce la sessione, e
solo dopo la pagina può aprire lo stream di controllo. Fra i due istanti passa almeno un giro di rete,
e il browser può aver stabilito la connessione H3 molto prima che la pagina chiami l'API.

L'ingresso concreto: il server fa partire il suo cronometro alla fine del TLS; la pagina — che è il
banco — lo fa partire quando la sessione è pronta. Il banco tace cinque secondi e si aspetta
`TEMPO_SCADUTO`; il server l'ha già mandato a 4,7 secondi del **suo** orologio. Il banco lo legge come
un tetto di 4,7 e scrive che il server sbaglia. Oppure il contrario, e la tolleranza va dichiarata.

⚠ **E c'è un caso peggiore, che non è del banco ma che il banco è nella posizione di vedere per
primo**: se il server fa partire il cronometro alla fine del TLS della connessione H3, **una seconda
sessione sulla stessa connessione** — o una connessione riusata dal browser — parte con il budget già
consumato. Il tetto giusto si misura dall'**apertura della sessione**, e la riga di `RCP.md` §4.6 dice
«stretta di mano TLS finita».

```
MARCA: [?]
```

---

### R3.28 — Le nove etichette della sonda non esistono nei rapporti dove vivono le procedure

```
DOVE:             fasi/01-filo-nudo.md, B1, la colonna «#»: S1a, S1b, S2, S3a, S3b,
                  S4, S5, S6, S7
COSA CONTRADDICE: web/rapporti/S1-certificato.md §4.2 (P1…P5),
                  S2-decodifica.md §4.2 (misure 1…7) e §4.4 (controlli A, B, C),
                  S3-tastiera-appunti.md §4.3 (gruppi A…E) e §4.2 (quattro controlli),
                  S4-ritardo-disegno.md §4.2 (P1…P7);
                  LEZIONI.md §2.3 (un banco che cerca la stringa sbagliata dà rosso
                  sul codice giusto)
```

**Come si dimostra.** Le etichette `S1a`, `S1b`, `S3a`, `S3b`, `S5`, `S6`, `S7` **non compaiono in
nessuno dei quattro rapporti**: sono nate in `web.md` §7 e sono state ereditate qui. Nei rapporti —
che sono il posto dove stanno le procedure, i comandi `openssl`, le sequenze di prova e i controlli —
le prove si chiamano in **quattro modi diversi e incompatibili**, e due rapporti usano `P1…Pn` per
cose di natura opposta: in S1 `P1`-`P5` sono prove **del prodotto**, in S4 `P1`-`P7` sono controlli
**del banco**.

L'ingresso concreto: chi scrive il banco legge nel documento di fase *«S4 … ⛔ decisivo: il server
ritarda di N ms noti»*, va in S4 a cercare «S4», non lo trova, e ricostruisce la procedura a memoria
— cioè fa esattamente quel che la fase 0 ha pagato con *«le righe di comando si copiano da un banco
che funziona, non si ricordano»* (`fasi/00-ambiente.md` B3 punto 2). Oppure va a cercare «P3» e trova
**due P3 diversi**, uno per rapporto.

⭐ **La cura è una colonna in più**, e vale finché i rapporti restano la fonte: accanto a ogni riga
della sonda, il rimando puntuale — `S1a → S1 §4.2 P1, controlli P2-P4`; `S2 → S2 §4.2 misure 1,2,4 e
§4.4 controlli A-C`; `S4 → S4 §4.1 e §4.2 P1-P7`. Costa nove celle e toglie di mezzo la
ricostruzione a memoria di nove procedure.

⚠ **E un rimando rotto già esistente**, trovato leggendo: S1 riga 356 manda a *«§4, passo 7»* e il §4
di S1 ha cinque prove. Non è di questo documento, ma chi seguirà quel rimando durante la fase 1 non
troverà niente.

```
MARCA: [R]
```

---

## 4. ⭐ Quel che ho provato a rompere e non ci sono riuscito

*Va scritto perché è informazione quanto i rilievi (`PIANO.md` §0.4, pratica 2).*

1. **Il controllo positivo di S1a, per la metà che c'è.** Ho provato a costruire il caso in cui la
   prova con l'impronta riesce e la conclusione è comunque sbagliata **per una causa di ambiente**:
   non ci sono riuscito. Con UDP filtrato la prova con l'impronta fallisce e il controllo diventa
   rosso, che è quel che deve fare; con il server muto, idem. **Per quel che riguarda «vuoto contro
   proibito», il controllo curato da `R2` distingue davvero.** ⛔ Il caso che invece **ho** costruito
   è di un'altra famiglia — il banco che guarda la promessa sbagliata — e lo chiude solo il controllo
   **negativo** che non c'è (R3.1).

2. **Il controllo del motivo in B6.** *«`TEMPO_SCADUTO` a 60 s è il server che fa il suo mestiere; una
   connessione che muore a 30 s senza motivo è il PING che manca»*. Ho cercato un terzo caso che
   producesse una morte a 30 s **con** motivo, o un `TEMPO_SCADUTO` che arrivasse per un'altra
   ragione. Non l'ho trovato: `RCP.md` §3.1 vieta il codice 0 e obbliga il motivo su ogni chiusura,
   quindi «muore senza motivo» ha una causa sola. È il controllo meglio costruito del documento.

3. **Il controllo di S7 (`-120`).** Distingue il segno da «qualcosa si muove», che è precisamente la
   forma di `LEZIONI.md` §1.11 regola 1. Il dubbio che ho è sull'**origine** del segno (R3.25), non
   sul controllo.

4. **La riga `GIA_ATTIVA_REMOTA` di B3.** Ho cercato un caso verde col difetto vivo: un server che
   rifiuta la seconda connessione per un'altra ragione e manda comunque `0x0F`. Non l'ho costruito —
   il codice del motivo, la verifica **dal lato che riceve** e il vincolo *«chi viene rifiutato è chi
   arriva»* insieme chiudono il caso, purché il banco controlli **quale** delle due connessioni
   sopravvive, e la riga lo dice.

5. **Le sei registrazioni guaste di B4.** Ho confrontato l'elenco con le forme di guasto già pagate dal
   progetto: la lunghezza incoerente c'è, l'UTF-8 non valido c'è, il nome ripetuto c'è, il canale fuori
   dai cinque c'è, lo stato sbagliato c'è, e **il riempimento «che fa tornare i conti» c'è** — che è la
   forma esatta del difetto corretto in `RCP.md` §6.2 il 9 agosto, cioè la più difficile da inventare.
   L'unica forma che manca è la lunghezza **oltre il tetto**, che però è di B5 (R3.3). **Sei su sette,
   e le sei scelte sono quelle giuste.**

6. **Il conto di B12 con `RCP.md` §11.** Ho verificato riga per riga i dodici banchi di §11 contro i
   sei che questa fase prende e i sei che rimanda. **Il conto torna**, ciascun rimando ha la sua fase,
   e la nota su `CREDENZIALI_ERRATE`/`TROPPI_TENTATIVI` che viaggiano in `RESPINTO` (rilievo R1.18) è
   riportata **giusta** in B7, con la ragione — che è il tipo di riga che di solito si perde.

7. **Una degradazione silenziosa proposta dal banco (I1)** e **un percorso che chiuda invece di
   calare**: non ho trovato niente. La fase non ha ancora video, e la sezione delle violazioni chiede
   la caduta della connessione solo dove `RCP.md` §3 la impone.

8. **Una `[?]` promossa a fatto in silenzio (E5)**: non ho trovato niente. Le `[?]` sono marcate, la
   sezione «Che cosa resta `[?]`» c'è ed è coerente con `web.md` §8, e il riquadro sul confine della
   fase — *«chi legge `stato = NUOVA` qui non deve credere che la ripresa sia implementata e non
   provata: **non è implementata**»* — è la forma giusta di dichiarare un confine, ed è il pezzo
   migliore del documento.

9. **C4 (marcatori invece di `sleep`)**: non ho trovato modo di romperlo, ed è la lezione
   `LEZIONI.md` §2.3-quinquies applicata dove morde — un banco a due lati. ⚠ Con l'avvertenza che la
   fase 0 dichiara ancora aperto lo stesso difetto in `banco.sh` (`sleep 2.5`), quindi il precedente
   in casa **non** è un esempio da copiare.

---

## 5. Il verdetto

⛔ **Non ho trovato niente** è quel che si scrive quando una revisione è verde. **Questa non lo è.**

**Ventotto rilievi: 25 `[R]`, 3 `[?]`, 0 `[M]`.** I `[R]` contraddicono una regola già scritta —
`LEZIONI.md`, `RCP.md`, `REVIEWER.md`, gli invarianti, o un'altra riga dello stesso documento — e si
correggono. I `[?]` si passano al coder perché li misuri: la misura chiude il cerchio, non la review.

**Le tre che pesano più di tutte, e la ragione è la stessa per tutte e tre**: un banco cieco messo
**prima** avvelena quel che viene dopo, perché dà fiducia (`LEZIONI.md` §10).

| | |
|---|---|
| **R3.1** | delle **undici** prove di controllo che i rapporti prescrivono per S1a, S2 e S4 **ne sopravvivono tre**, e in tutt'e tre le righe è caduto il controllo che dice **no**. Due delle tre amputazioni `R2` le aveva già bocciate `[R]`, poche ore fa, mandandole a curare *«prima di scrivere una riga di banco»* |
| **R3.2** | **B8 è verde con il canale del tempismo aperto**: un `sleep(1)` dopo PAM passa tutte e tre le righe, e B8 è il banco che il documento dichiara *«una proprietà di sicurezza che nessun altro banco vede»* |
| **R3.4** | **l'ordine dichiarato fra B1 e B2 è circolare**: tre delle nove misure della sonda hanno bisogno del server che B2 costruisce, e B1 si dichiara «nessuna riga di prodotto» e viene prima |

⚠ **E l'ordine in cui vanno prese**, perché non tutte costano uguale:

| Quando | Che cosa |
|---|---|
| ⛔ **prima di scrivere una riga di banco** | R3.1, R3.4, R3.14, R3.28 — sono correzioni di testo, un censimento di dispositivi e nove rimandi, e senza di esse la fase misura male o non misura affatto |
| ⛔ **prima di scrivere il registratore** | R3.6 — è una decisione di formato, e dopo costa una riscrittura |
| ⛔ **prima di scrivere il primo byte di `RCP.md` in codice** | la marca 16×16 di S4 con il ritardo `N` iniettabile è **un messaggio in più** (R3.4), e `RCP.md` §9 chiude la finestra *«dal primo byte scritto in poi»* |
| **mentre si scrivono i banchi** | R3.2, R3.3, R3.5, R3.9, R3.10, R3.11, R3.15, R3.17, R3.18, R3.20, R3.22, R3.23 — sono righe in più nei criteri, non impianti nuovi |
| **prima di eseguire il primo giro** | R3.8, R3.16 — l'isolamento fra banchi e lo stato iniziale dichiarato |
| **prima di credere a un numero** | R3.7, R3.19, R3.21, R3.24 |
| **da misurare** | R3.25, R3.26, R3.27 — `[?]`, e sono del coder |

⛔ **E questa non è un'assoluzione di quel che non ho toccato.** Ho letto i dodici banchi contro
`RCP.md`, `LEZIONI.md` §1 e §2, `web.md` e i quattro rapporti; della conformità del banco al
protocollo si occupa un'altra revisione, e di quel che nessuno dei due ha guardato **non ho trovato
niente**, che non è «è giusto» (`REVIEWER.md` §0 e §5).
