# fasi/ — i documenti di chiusura, uno per fase

Ogni fase di [`../PIANO.md`](../PIANO.md) ha qui il suo documento, con il nome
`NN-nome.md` (`A1-nome.md` per il binario Android).

⛔ **Il documento si apre quando si apre la fase, non quando si chiude.** Un documento
scritto dopo è un resoconto, e in un resoconto le misure si *ricordano* invece di essere
*registrate*.

Il modello sta in `../PIANO.md` §0.2. Le quattro regole, in breve:

1. le **decisioni** stanno in `../DECISIONI.md`, una sola volta: qui si **rimanda**, non si copia;
2. **«che cosa non ha funzionato»** si riempie anche quando fa una brutta figura;
3. la fase si chiude su **una misura giudicata dall'utente**, non su un documento completo;
4. il **banco si certifica** prima di essere creduto.

---

> # ⛔⛔ I RAPPORTI DEGLI AGENTI NON SONO PIÙ SU DISCO — *16 agosto 2026*
>
> *Decisione dell'utente: «elimina i rapporti degli agenti: non dovrebbero servire più».*
>
> `fasi/rapporti/` e `web/rapporti/` — **94 file, 42 900 righe**, il 63 % di tutto quel che il
> progetto aveva scritto — sono stati tolti.
>
> ## ⭐ Ma NON sono persi, e questo è il punto: come si recupera uno
>
> Sono usciti con `git rm`, quindi la storia li ha per intero. **L'ultimo commit in cui vivono è
> `0c85e5c`**, e da lì si tira fuori qualunque rapporto senza rimetterlo su disco:
>
> ```
> git show 0c85e5c:fasi/rapporti/F3-E-anello-rimisurato.md | less     # leggerne uno
> git show 0c85e5c --stat -- fasi/rapporti | head -100                # vedere l'elenco
> git checkout 0c85e5c -- fasi/rapporti/F4-O2-anello-input.md         # riportarne uno su disco
> ```
>
> ## ⚠ E il prezzo, misurato prima di toglierli invece che scoperto dopo
>
> ⛔ **169 rimandi** dai documenti che restano puntavano dentro quei rapporti, verso **50 file
> diversi**. Quei rimandi adesso nominano un file che su disco non c'è — ⭐ **e restano risolvibili**
> con le tre righe qui sopra, perché il nome nel rimando è ancora il nome nella storia.
>
> ⚠ **I tre più citati**, perché sono quelli che qualcuno cercherà per primo:
> `web/rapporti/S-esiti-sonda.md` (18 rimandi — ⛔ e non era un rapporto, erano **gli esiti misurati
> della sonda del browser**, con la scena accanto a ogni numero), `F5-desktop-vero.md` e
> `F2-6-giudizio.md` (9 ciascuno).
>
> ⇒ ⛔ **La regola che questo tocca è `LEZIONI.md` §9.8**, *«la fonte sta accanto alla misura»*: la
> fonte **c'è ancora**, ma adesso sta in un commit invece che in un file. Chi cita un numero
> misurato da qui in avanti lo sappia — e il posto giusto per un numero che deve sopravvivere è **il
> documento di fase**, non il rapporto che lo ha prodotto.

---

## ✅ Il `05` c'è, ed è chiuso — 16 agosto 2026

`fasi/05-la-sessione.md`, aperto il 15 agosto **col suo documento e prima di una riga di codice**, e
chiuso il 16 **sul giudizio dell'utente** (§7 raccoglie le sue parole, con la data — non un verdetto
scritto da noi).

⭐ **E la prova che l'ha chiusa l'ha fatta l'utente**, con un lavoro vero dentro: un ciclo infinito
in un terminale, il browser chiuso, la finestra rimpicciolita, il rientro — e il ciclo girava
ancora. ⛔ Tutte le prove nostre avevano un desktop **vuoto**, che appena rinato è identico a com'era:
il testimone peggiore possibile per la domanda «è sopravvissuta?».

⏳ **E la fase 6 non si apre subito**: l'utente ha chiesto prima una revisione di `PIANO.md`, *«che ha
alcuni punti secondo me fuori sequenza»*.

> ### ✅ ⭐ La revisione è stata fatta il 16 agosto 2026, e ha cambiato due cose
>
> | | |
> |---|---|
> | ⭐ **la fase 8 non è più «l'accelerazione»: è «la copia zero»** | la codifica in hardware era già entrata nel prodotto il **13 agosto**, e i 10 bit sono un muro **a monte** (la cattura). Restava la copia zero, ed è tutta la fase |
> | ⭐⭐ **il multi-tenant passa davanti ai desktop nuovi** — *«PRIMA si chiude lo sviluppo anche con il multi-tenant, e solo dopo si pensa agli altri DE»* | **era la fase 12, è la fase 10**; KDE 10 → **11**, XFCE/LXQt 11 → **12**. La 9 e la 13 restano dove sono (`DECISIONI.md` §4.6-sexies) |
>
> ⇒ **L'ordine di adesso**: 6 · 7 · 8 la copia zero · 9 la qualità · **10 il multi-tenant** ·
> 11 KDE · 12 XFCE e LXQt · 13 il servizio.
>
> ⛔ **Trappola di lettura, e vale per chi cerca all'indietro**: `STUDI.md` §kde, `STUDI.md` §gnome, `STUDI.md` §xfce e
> `STUDI.md` §lxqt dicono in testa *«per la fase 11»*, ma quella è **la fase 11 di v1** — sono studi del
> 7-8 agosto 2026, scritti prima che questo piano esistesse. Quei numeri **non sono questi numeri**,
> e infatti non sono stati toccati.

---

## ⚠ ~~Manca il `05`~~ — com'era scritto il 15 agosto, e si conserva

*15 agosto 2026.* La fase 5 non è ancora stata aperta. ⛔ E la **coda della fase 4** — la notte in
cui la tela è diventata la finestra del browser — sta **dentro `04-si-comanda.md`**, non in un
documento suo: il numero della fase lo dà il **perché** si è fatto il lavoro, non l'elenco delle
cose prodotte. Quel lavoro tocca contenuto della fase 6, e `PIANO.md` dice quali sue parti si
trovano già fatte.

⚠ Quella coda porta in testa la sua riserva di forma: è stata scritta **alla chiusura**, contro la
regola qui sopra. Le misure però non sono ricordate — vengono dai registri del server e dai giri di
banco, con l'ora accanto. ⛔ La regola resta: **la fase 5 si apre col suo documento**.
