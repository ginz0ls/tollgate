## Letto nel progetto
- ai/summary.py
- .tollgate-run/1/task-1.md

## Documentazione
- https://platform.claude.com/docs/en/models/overview — tabella "Compare models": Claude Haiku 5.5 e' un modello corrente, ID API `claude-haiku-5-5` (dateless, snapshot fissato), ritiro non prima del 7 ottobre 2027; Haiku e' la linea per compiti ad alto volume e bassa latenza.
- https://platform.claude.com/docs/en/about-claude/model-deprecations — tabella "Model status": `claude-haiku-5-5` e' Active, nessuna deprecazione; `claude-haiku-4-5-20251001` Active ma piu' vecchio.

## Cosa ho trovato
Il progetto non usa librerie nel nuovo file: ai/models.py contiene solo una costante stringa (nessun file delle dipendenze toccato). L'ultimo Haiku stabile e' claude-haiku-5-5 (Active), quindi lo uso. L'ID non ha data a 8 cifre, coerente col test. Nel file metto l'indirizzo della pagina modelli e la data 2026-11-02 accanto alla costante, e la docstring di modulo nello stile di ai/summary.py. Il codice esistente (riassumi) riceve il modello come parametro e non cambia.
esito: valida
