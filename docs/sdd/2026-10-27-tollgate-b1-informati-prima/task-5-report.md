# Report Task 5

Implementato: `effects.decide` restituisce `[]` per `research.is_doc_tool(name)` prima di `mcp_allow`; `agents/implementer.md` con tools `Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch` (nessuna voce MCP, ruling B1-V2) e sezione «Informati prima di scrivere» (WebFetch sulla doc ufficiale, context7 solo se disponibile, frase sulle pagine scaricate, modello della nota con HEREDOC_END, L0 senza nota); `skills/setup/SKILL.md` punto 4 sui permessi di WebFetch/WebSearch (l'utente le aggiunge da sé) e `description` aggiornata (D7).

Test: test_doc_mcp_not_an_effect, test_other_mcp_still_effect, test_implementer_tools, test_implementer_mentions_untrusted_pages, test_implementer_mentions_research_submit, test_setup_proposes_web_permissions; aggiornato test_agents_frontmatter.
RED: 6 fallimenti su test_check_effects/test_manifest/test_skill_contract. GREEN: 74 test OK (python3.11 -B -m unittest dei tre file).

Scostamento: `tests/test_b1_scripts.py::LatencyTest` asseriva che la sonda B1-V3 con il nome context7 fosse negata («effetto esterno»); ora non lo è, test aggiornato (denied False).
Suite: tests/run su python3.11 3030 test con 1 solo fallimento (quello sopra, poi corretto e rilanciato il file: OK); python3 (3.13.5) 3030 test OK dopo la correzione. Il 3.11 completo non è stato rilanciato dopo la correzione (solo tests.test_b1_scripts, 19 OK).
`claude plugin validate` non lanciato (controllo del controller).
