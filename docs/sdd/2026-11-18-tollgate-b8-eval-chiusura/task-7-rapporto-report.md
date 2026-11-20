# Task 7, Step 3-4: report

Scritto `docs/verifiche/2026-11-18-b8-eval.md` (forma di P5).

## Numeri
- Tabella dei 16 casi e delle due sonde: da `tabella.md` di ogni cartella; costi e durate da `tabella.md` e `budget.tsv`.
- Costo: `awk` sulla colonna 3 di `budget.tsv`: totale 11.5854, 16 casi 10.8824, sonde 0.7030 (0.2633 + 0.4397), residuo 8.41.
- Conteggi della nota: somma delle righe `| claude-eval-` di `nota.md` dei 16 casi (non le sonde). Le righe del braccio senza plugin sono a zero, quindi la somma di tutte le righe è il braccio con plugin.
  - valide 23 = s10 3, s11 3, s12 3, s1 3, s3 3, s6 3, e4 3, e5 2
  - rifiutate 2 (s10); promemoria 3 (s5, uno per corsa); cambi illeggibili 0; veti 0
  - read 100, bash_read 10 (e5), fetch 12 (s10 9, s11 3), grep/search/docs 0
- «2 riconsegne su 24 corse in cui la nota era dovuta»: 24 = 8 casi con nota attesa per 3 corse; le due rifiutate sono in s10.

## Dubbi
- Nelle sezioni del limite della piattaforma ho dedotto dal ledger che s10, s11, s12 restano BLOCKED ma i loro grader non chiedono il commit, e che s5 guarda i file scritti: coerente col ledger, non riletto nei grader.
- «Prima delle sonde: git pulito, chiave non impostata» viene dal ledger solo per le sonde.
- Il rapporto cita i commit 2bb649c, c1108aa, 20eee79; il difetto 1 ha il commit 2bb649c insieme al 2 e al 3 (non separati nel ledger).
- Non ho aperto trace né evidenze oltre `tabella.md`, `nota.md`, `budget.tsv`.
