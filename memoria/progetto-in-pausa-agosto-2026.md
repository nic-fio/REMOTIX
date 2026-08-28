---
name: progetto-in-pausa-agosto-2026
description: in pausa dal 27 ago 2026 (intervento); il 28 il progetto e' passato su GitHub e la documentazione e' stata bonificata. Si riprende da KDE, col server che torna dall'assistenza
metadata:
  type: project
---

**REMOTIX e' in pausa dal 27 agosto 2026** — Nic ha un intervento chirurgico. Si
riprende fra qualche settimana. ⛔ Non c'e' niente lasciato a meta': la fase 11 e'
chiusa, e il punto d'ingresso e' il riquadro ⏸ in testa a `README.md`.

## Che cosa e' successo il 28 agosto, a progetto fermo

⭐ Due cose, e Nic le ha chiamate *«un compito non piu' rimandabile»*:

1. **Il progetto e' uscito dal tablet.** Vive su `github.com/nic-fio/REMOTIX`,
   privato. Il tablet e' stato svuotato: v1 cancellato, credenziali cancellate,
   41 → 33 GB. Vedi [[deposito-su-github]] e [[credenziali-da-rigenerare]].

2. **La documentazione e' stata bonificata.** 272 coordinate di riga marce, 78
   rimandi ciechi, 36 link rotti, 2 documenti vincolanti che mandavano alla
   specifica di v1, 4 affermazioni che il codice aveva gia' smentito, e una
   sezione (`DECISIONI.md` §4.6-septies) citata da cinque documenti e **mai
   scritta**. ⇒ Tutto chiuso, e ⭐ **la rete adesso ha `C16`**, che da' rosso da
   sola se una carta ricomincia a mentire — anche su un commit di soli documenti,
   che prima non faceva scattare niente.

## Quando il server torna dall'assistenza, nell'ordine

1. Rifare le credenziali — [[credenziali-da-rigenerare]]. ⛔ Finche' non ci sono,
   i 46 richiami di `sshpw.py` non raggiungono la macchina: **e' voluto, non e' un
   guasto**.
2. Nello stesso giro, togliere la parola d'ordine `sudo` in chiaro dai 9 banchi —
   e' l'unica cosa che tiene il deposito privato per forza.
3. ⭐ Il primo giro della rete anti-regressione vale anche come **collaudo del
   rebranding e della bonifica**: nessuna delle due e' stata riprovata sul ferro.
4. Poi si riprende il lavoro vero: **la fase 12, KDE** — i tre rossi di `C1` su
   kde/xfce/lxqt non sono un difetto, sono il mandato.

⚠ Resta aperto, e non e' urgente: 23 banchi della fase 8 non sono mai stati
committati ⇒ quelle misure non sono riproducibili. ⭐ Decisione di Nic: *«le
misure tienile come stanno»*. Sta scritto in `banchi/11-scatole/11-c16-eccezioni.txt`.
