35:Task 1: minor (deferred): fragments.py:16-17 il segmento di cartella ammette il newline (`a\n/**` → root_folder "a\n"), come la vecchia regex.
36:Task 1: minor (deferred): fragments.py:82-83 il ramo `[None]` per `paths` non lista è contorto; basterebbe un `isinstance` prima della comprensione.
41:Task 3: minor (deferred): `docker compose -f a.yml push` → None (opzione prima di `push`): da aggiungere ai buchi di D3 nel Task 10.
42:Task 3: minor (deferred): mancano test che fissino `[external_effects] commands` con un lanciatore e `curl`/`gh` sull'argv originale (corretti per lettura) — li aggiunge il giro 1, costo basso.
43:Task 3: minor (deferred): falsi positivi rimasti `npm cache clean vercel`, `npm run docker push`, `npm test -- -c vercel` (classe già nel costo della decisione 17).
45:Task 2: minor (deferred): processo — codice scritto prima dei test; il RED è stato ricostruito rimettendo l'init.py di HEAD (11 failure, 3 errori in ProfileBlocksTest). Nessun effetto sul prodotto.
47:Task 2: minor (deferred): tests/test_init.py test_name_pattern_exact_paths usa `.__len__()` invece di `len()`.
48:Task 2: minor (deferred): init._match ricalcola gli insiemi `folders` e `roots` per ogni file.
49:Task 2: minor (deferred): concrete_for su un prefisso escluso senza test diretto (coperto da test_name_pattern_skips_excluded_prefixes).
58:Task 4: minor (deferred): R-INFRA-05 — un valore `"@nome"` in `env` di Vercel è un riferimento a un segreto, non un segreto: la pagina del Task 5 lo dice.
59:Task 4: minor (deferred): R-INFRA-02 — per `docker`/`docker compose` nessuna pagina dei comandi tra le fonti né in «Dove informarsi»: lo giudica il verificatore del Task 5.
60:Task 4: minor (deferred): R-INFRA-01 — la Fonte nomina 3.4 e 11, non «progetto 1» come la bozza.
61:Task 4: minor (deferred): R-INFRA-07 — «data del giorno» giudicabile sul diff solo conoscendo la data del commit (non blocca).
62:Task 4: minor (deferred): test_no_long_quotations guarda solo le «»; il controllo del testo copiato resta del verificatore.
75:Task 5: minor (deferred): `pages project create/delete` senza una riga ok propria nel rapporto delle fonti.
76:Task 5: minor (deferred): i numeri «dodici», «N punti», «quattro fonti» della pagina non sono coperti da un test.
77:Task 5: minor (deferred): test_page_has_no_private_data controlla solo `/home/`.
80:Task 5: minor (deferred): nella pagina la regola 5 nomina solo `env` per l'eccezione `"@nome"`, la skill `env` o `build.env`.
88:Task 7: minor (deferred): processo — il rosso di test_readonly_list_matches_config_and_agents non è stato visto (agenti ed elenchi scritti insieme).
94:Task 7: minor (deferred): nessun test fissa che implementer-infra nomini `wrangler kv`/`d1`/`r2` e le build Docker con push (testo presente a agents/implementer-infra.md:53).
95:Task 7: minor (deferred): agents/implementer-infra.md:53 «la sua configurazione elenca» approssimativo; non dice che anche la prova di R-INFRA-12 (dry-run di wrangler, vercel build) è fermata da tollgate finché l'utente non approva.
100:Task 8: minor (deferred): la grep di `registra` non segna `(yarn)` nudo né i comandi dopo un backtick; falsi positivi tipo `echo "npm …"` (limiti già scritti per `VAR=x npm`, `xargs npm`).
101:Task 8: minor (deferred): test_registra_flags_deploy_clis non copre `command`/`env`, `;` e la forma `bash (subagente):`.
102:Task 8: minor (deferred): spikes/b4/flow/.gitignore non esclude `.vercel/`, `.env*`, `.dev.vars*`, `.wrangler/`.
103:Task 8: minor (deferred): processo — RED non osservato a parte.
104:Task 8: minor (deferred): due test leggono i file veri di rules-infra senza il prefisso test_real_ (come già per ai).
119:Task 9: minor (deferred): il piano di B4 nomina R-INFRA-11 per «non pubblicare» (decisioni 7, 14, Task 9): vale R-INFRA-12 (carry); la spec rev 31 lo dice.
124:Task 10: minor (deferred): due righe fuori colonna nella sezione 20 della spec (revisioni 14 e 24), preesistenti su main.
