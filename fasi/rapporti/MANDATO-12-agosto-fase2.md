# MANDATO — Fase 2 «Il primo fotogramma», divisa in sei sotto-fasi

*Scritto il 12 agosto 2026, su richiesta dell'utente: «la fase 2 suddividila in sotto-fasi e assegna
ognuna a un sottoagente».*

⛔ **Questo è il documento che ogni sottoagente legge per primo.** Contiene le regole che valgono
per tutti e sei; quel che cambia da un mandato all'altro è **soltanto** l'area e i file.

---

## 0. Che cosa produce la fase 2, per intero

`PIANO.md` §«Fase 2 — Il primo fotogramma»:

> cattura da una sessione GNOME vera → codifica → filo → `VideoDecoder` → tela della pagina.
> **Un'immagine ferma.**
>
> **L'utente vede**: il proprio desktop, dentro una scheda del browser. Fermo, ma suo.
>
> **Il banco**: il fotogramma decodificato confrontato con quello catturato. Non «il programma non
> è crollato»: **i pixel**.

---

## 1. ⛔ LA REGOLA CHE ORDINA QUESTO GIRO — il banco prima del prodotto

`PIANO.md` §0.4, momento 1: **il revisore interviene appena il banco esiste, PRIMA che il prodotto
sia scritto**, perché *«un difetto nel prodotto lo trova un banco buono; un difetto nel banco non lo
trova niente, e avvelena ogni misura successiva perché dà fiducia»* (`REVIEWER.md` §1).

⇒ **Questo giro di sottoagenti NON scrive prodotto.** Nessuno tocca `src/`. Si scrive **il banco**,
e si scrive lo **studio** che dice al prodotto che forma deve avere.

⚠ Chi trovasse questa regola scomoda ricordi che la fase 1 l'ha pagata tre volte: tre rossi puntati
sull'imputato sbagliato, e una volta un **verde** che assolveva un difetto vivo (`README.md`,
riquadro «un'accusa al prodotto che invece era davvero del banco»).

---

## 2. Le sei sotto-fasi, e chi tocca che cosa

| # | Sotto-fase | Possiede questi file di banco | Porta sua |
|---|---|---|---|
| **F2.1** | **La sessione GNOME headless** — la sessione grafica nasce, e nasce con un monitor virtuale | `banchi/02-sessione-*` | 7511 |
| **F2.2** | **La cattura** — da Mutter a un buffer nostro, con il tipo di buffer dichiarato | `banchi/02-cattura-*` | 7512 |
| **F2.3** | **La codifica HEVC in software** — un fotogramma chiave, Main10, e i 10 bit veri | `banchi/02-codifica-*` | 7513 |
| **F2.4** | **Il filo** — RCP porta un fotogramma: messaggi, canale, e il validatore che sa giudicarlo | `banchi/02-filo-*` | 7514 |
| **F2.5** | **La pagina** — `VideoDecoder` e la tela: dal byte al pixel dipinto | `banchi/02-pagina-*` | 7515 |
| **F2.6** | **Il giudizio** — i pixel a confronto, e la sonda sul telefono vero | `banchi/02-giudizio-*` | 7516 |

⛔ **Nessuno scrive fuori dai propri file.** Se una sotto-fase ha bisogno di qualcosa da un'altra, lo
scrive nel proprio rapporto sotto **«Le cuciture»** — non lo va a prendere.

---

## 3. Che cosa consegna ciascun sottoagente

### 3.1 Un rapporto: `fasi/rapporti/F2-<n>-<area>.md`

Con queste sezioni, in quest'ordine — è il modello di `PIANO.md` §0.2 ristretto a una sotto-fase:

| Sezione | Che cosa ci va |
|---|---|
| **Che cosa deve produrre** | in una frase, e in termini di cosa l'utente vede o di cosa il banco misura |
| ⛔ **Il banco** | **scritto prima del prodotto**: la scena dichiarata, che cosa si conta, il **controllo positivo** («lo strumento sa trovare qualcosa che c'è di sicuro?»), il **caso opposto** («che aspetto avrebbe il contrario?»), e **come questo banco si certifica** — sano N → guasto M → risanato N, con i numeri attesi **scritti prima del giro** |
| **Che cosa si riusa da v1** | file e **righe vere**, contate — non le cifre del piano ricopiate. Se il piano dice 1060 righe e il file ne ha altre, si scrive quel che c'è e si segnala |
| ⛔ **Le trappole già pagate che mordono qui** | citate con il paragrafo: `LEZIONI.md`, `gnome.md`, `web.md`, `REVIEWER.md` §2 (le forme E1-E11). Non se ne inventano: si vanno a leggere |
| **Le `[?]` da misurare** | quel che non si sa, scritto come non saputo |
| **Le cuciture** | che cosa questa sotto-fase **chiede** alle altre cinque e che cosa **promette** loro. È la sezione che il coordinatore userà per rimettere insieme il lavoro |

### 3.2 Gli script di banco, in `banchi/02-<area>-*`

Eseguibili, e nello stile di casa — si guardi `banchi/01-b5-lancia.sh` o `banchi/01-b13-sera-certifica.sh`:

- ⛔ **un'intestazione lunga che dice PERCHÉ lo script esiste**, non che cosa fa: quale difetto già
  pagato impedisce, quale misura sbagliata sarebbe possibile senza di lui;
- ⛔ **zero e fallimento sono due cose diverse** (`REVIEWER.md` §1 punto 4): niente `2>/dev/null`,
  niente stato d'uscita buttato in una catena di `|`;
- ⛔ **un controllo positivo in coda a ogni esecuzione**, come la diagnosi di `lsquic` in B2;
- gli esiti in `banchi/02-<area>-esiti.jsonl`, una riga per giro, con l'ora e la scena.

### 3.3 Una riga per il catalogo delle certificazioni

Nella forma che usa `banchi/01-b12-guasti.py`: nome, comando, **atteso sano**, **guasto da innestare**,
**atteso guasto**. ⭐ E vale la regola nata l'11 agosto: *chi scrive un banco lo certifica nello
stesso giro*, o il conto non cala mai.

---

## 4. ⛔ I divieti, e non sono formalità

| | |
|---|---|
| ⛔ **non si tocca `src/`** | il prodotto è del giro dopo, e va scritto contro un banco già revisionato |
| ⛔ **niente `git commit`, `git add`, `git checkout`** | sei agenti che scrivono nello stesso deposito si sovrascrivono il lavoro. Committa il coordinatore, alla fine |
| ⛔ **non si spegne e non si riaccende niente su NIC-OS** | sulla **7448** gira il prodotto di casa e sulla **7501** il bersaglio di P5: sono accesi apposta. Si guarda (`ss`, `ls`, i registri), non si tocca |
| ⛔ **ognuno usa la porta sua** | l'elenco è in §2. Due banchi sulla stessa porta si fermano a vicenda, ed è già successo |
| ⛔ **mai una redirezione ATTORNO a `enter.sh` o a `ssh`** | la richiesta di parola d'ordine di `sudo` va sullo stderr, e una redirezione la mangia: il comando resta **appeso per sempre, in silenzio**. Dentro le virgolette sì, attorno no. `fasi/00-ambiente.md` B3.3 — pagata **quattro volte**, due delle quali nella sola notte dell'11 agosto |
| ⚠ **si scrive in italiano** | documenti, commenti, messaggi. Con le marche `[M]` misurato · `[R]` letto nel codice altrui · `[S]` letto nella specifica · `[?]` ipotizzato, e i segni ⭐ ⛔ ⚠ ⏳ come nel resto del progetto |
| ⛔ **una cosa non misurata non si scrive come misurata** | è la regola che tiene in piedi tutto il resto: `[?]` resta `[?]` finché qualcuno non la misura sul ferro |

---

## 5. I documenti che si leggono prima di cominciare

⛔ Non si scrive una riga senza aver letto, **per intero**, i primi due:

| Documento | Perché |
|---|---|
| `CODER.md` | le regole di chi scrive. §1 i numeri dell'utente, §2 gli invarianti I1-I8, §3 le regole di misura |
| `REVIEWER.md` | perché il banco si scrive sapendo come verrà attaccato. §2 il catalogo delle forme d'errore E1-E11 |
| `PIANO.md` §0.2, §0.4, «Fase 2» | il modello del documento di fase, il metodo, e il mandato della fase |
| `LEZIONI.md` | il metodo di misura. Si legge **la parte che riguarda la propria area**, e si cita col paragrafo |
| `SPECIFICHE.md` | che cosa il prodotto promette all'utente |
| `RCP.md` | l'arbitro del filo. Obbligatorio per **F2.4**, utile a **F2.3** e **F2.5** |
| il documento d'area | `gnome.md` per F2.1, `web.md` per F2.5 e F2.6, `cinnamon.md`/`kde.md` solo se serve un confronto |
| `fasi/01-filo-nudo.md` | com'è fatto un documento di fase quando è finito, e le trappole della fase appena chiusa |

---

## 6. La macchina, in due righe

| | |
|---|---|
| **CHUWI** | il portatile: qui stanno il deposito, i browser, e da qui si lanciano i banchi che guardano il browser |
| **NIC-OS** | `192.168.0.2`: il server, con le due GPU e la sessione grafica. Ci si arriva con `python3 v1/strumenti/sshpw.py` (che porta la parola d'ordine) oppure `ssh nicfio@192.168.0.2`; il codice del prodotto vive in `/media/REMOTIX/src`, e dentro il contenitore ci si entra con `/media/REMOTIX/enter.sh` |

⏳ **Una cosa con una scadenza, che non è di nessuno dei sei ma non va disturbata**:
`banchi/01-s1b-eccezione.sh oggi` gira una volta al giorno fino al 18 agosto e usa la **7452** e il
certificato di `/media/REMOTIX/s1b-certificato/`, che ⛔ **non si rigenera per nessun motivo**.
