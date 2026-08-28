---
name: remotix-lezioni
description: "REMOTIX — LEZIONI.md, scritto il 7 agosto 2026: le lezioni del supporto a GNOME nella forma che serve a chi apre il prossimo desktop. Da leggere prima della fase 11"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1aac11ab-166c-4641-9520-e34064b18f20
  modified: 2026-08-07T21:12:00.405Z
---

Dal 7 agosto 2026 il progetto ha un quinto documento: **`LEZIONI.md`**, chiesto dall'utente
chiudendo GNOME — *«mettere in un documento tutte le lezioni apprese… potrebbe tornarci utile per i
prossimi DE»*.

**La divisione con `REFERENCE.md` è netta e va tenuta**: lì **che cosa fare con Mutter** (e metà di
quelle regole cadrà cambiando compositore), qui **quel che resta vero quando il compositore cambia**,
con accanto **quanto è costato impararlo**.

Le tre sezioni che si usano per prime aprendo un desktop nuovo:

| | |
|---|---|
| **§3** | le **undici domande** da fare a un compositore nuovo, con le risposte già note per Mutter, KWin e wlroots — e gli strumenti del banco che le rispondono |
| **§9** | la **ricetta** in otto passi per aprire il supporto a un desktop |
| **§8** | i **vicoli ciechi già percorsi**, da non rifare |

`PIANO.md` fase 11 lo dichiara **vincolante** come §7.0 di `SPECIFICA.md`: si legge prima di
scrivere una riga.

**La lezione che il documento mette per ultima, e che le riassume tutte**: il progetto non si è mai
fermato su un problema difficile — si è fermato ogni volta su **una misura che non misurava quello
che credevamo**.

⭐ **E la sera del 7 agosto il primo banco di KDE ne ha aggiunte due, §1.9 e §1.10**, che sono la
prova della lezione di sopra:

- **una lettura negata non è una lettura che dice zero.** `ls /proc/<pid>/fd | grep dri` non stampava
  niente e l'abbiamo letto come «zero nodi DRM»: il kernel negava la directory. Da cui: una misura che
  può dire «zero» deve distinguere lo zero dal fallimento; **ogni strumento vuole un controllo
  positivo**; e quando codice letto e misura si contraddicono, **il sospetto va prima sulla misura** —
  il codice non ha un ambiente.
- **un permesso può dipendere da una variabile d'ambiente che nessuno documenta**, e prima di provare
  varianti del proprio file si accende il registro del componente che nega.

Vedi [[remotix-prossimo-kde]] per il caso concreto.

Vedi [[remotix-metodo-documentazione]] e [[remotix-requisito-prestazione]].
