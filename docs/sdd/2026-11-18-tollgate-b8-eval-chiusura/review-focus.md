## Review Focus

1. **Un comando che scrive sul servizio vero passa ancora, o uno innocuo chiede.**
   - Devono chiedere: `dotenv -e .env.production -- prisma migrate deploy`, `dotenv -e .env.production -- npm run deploy`, `cross-env NODE_ENV=production drizzle-kit push`, `doppler run -- npx supabase db push`, `doppler run --command 'prisma migrate deploy'`, `op run -- supabase db push`, `infisical run --env=prod -- prisma db push`, `dotenv -- curl -X POST https://x`, `dotenv -- bash -c 'prisma migrate deploy'`, `npm exec prisma -- -- migrate deploy`, `supabase db push -p --local`, `supabase db pull --schema --local`, `supabase db push -p --help`.
   - Devono passare: `dotenv -- python3 -m unittest`, `dotenv -- npm i -g vercel`, `supabase db push -p x --local`, `cross-env CI=1 python3 tools/build.py`.
   - Test: Task 1, Step 1.
2. **Un eval che consuma il tetto sbagliato o lo supera.**
   - Una corsa di B8 che scrive nel registro di P5, un residuo calcolato su 80, un `--max-cost-usd` sopra il residuo di `b8`.
   - Test: Task 3 `test_default_campaign_is_b8`, `test_p5_registry_untouched_by_b8`, `test_cap_message_names_campaign`, e i test di P5 riscritti con `--campagna p5`.
3. **Un caso che passa senza misurare niente.**
   - Un grader che combacia con il testo del prompt o del brief.
   - Un grader che passa da solo nel braccio senza plugin, come il file intatto quando il modello non fa nulla.
   - Un cammino sbagliato sopra soglia.
   - Test: Task 4 `ExtraCasesTest`-style `test_new_case_patterns_do_not_match_prompt_or_brief`, `assertWrongPath` per «non fa nulla» e per «scorciatoia», `ScoreTest`.
4. **Testo di terzi o dati privati nelle evidenze.**
   - Una trace con il risultato di `WebFetch` o `WebSearch` committata così com'è; il nome utente o l'host in una trace, in `settings.json` o in `events.host` dello stato copiato.
   - Test: Task 3 `test_run_strips_web_results_from_traces`, `test_anonymize_text_and_db`; `test_committed_evidence_has_no_long_web_results` verde dopo i Task 6 e 7; `grep -raF` del controller e verifica a mano nel rapporto.
5. **Una nota con una pagina aperta che tollgate non conta.**
   - Un `WebFetch` riuscito non registrato, quindi l'implementatore che ha fatto la cosa giusta viene rifiutato.
   - Test: Task 3, passo `fetch` della prova a secco con s10 (nota valida con l'indirizzo dopo il `fetch`, rifiuto senza); Task 6, sonda dal vivo sulla tabella `lookups`.

