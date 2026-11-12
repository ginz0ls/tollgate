# Report Task 6

## RED (test_manifest, prima degli agenti)
```
ERROR: test_area_agents_attribution (tests.test_manifest.ManifestTest.test_area_agents_attribution) (agent='implementer-frontend')
ERROR: test_area_agents_attribution (tests.test_manifest.ManifestTest.test_area_agents_attribution) (agent='reviewer-frontend')
ERROR: test_area_agents_derive_from_generic (tests.test_manifest.ManifestTest.test_area_agents_derive_from_generic) (agent='implementer-frontend')
ERROR: test_area_agents_derive_from_generic (tests.test_manifest.ManifestTest.test_area_agents_derive_from_generic) (agent='reviewer-frontend')
ERROR: test_area_agents_name_area_rules (tests.test_manifest.ManifestTest.test_area_agents_name_area_rules) (agent='implementer-frontend')
ERROR: test_area_agents_name_area_rules (tests.test_manifest.ManifestTest.test_area_agents_name_area_rules) (agent='reviewer-frontend')
ERROR: test_code_agents_preload_rules_base (tests.test_manifest.ManifestTest.test_code_agents_preload_rules_base) (agent='implementer-frontend')
ERROR: test_code_agents_preload_rules_base (tests.test_manifest.ManifestTest.test_code_agents_preload_rules_base) (agent='reviewer-frontend')
ERROR: test_real_frontend_agent_names_forbidden_tools (tests.test_manifest.ManifestTest.test_real_frontend_agent_names_forbidden_tools)
FAIL: test_final_reviewers_leave_report_rules_of_areas (tests.test_manifest.ManifestTest.test_final_reviewers_leave_report_rules_of_areas) (agent='final-reviewer')
FAIL: test_final_reviewers_leave_report_rules_of_areas (tests.test_manifest.ManifestTest.test_final_reviewers_leave_report_rules_of_areas) (agent='finding-verifier')
Ran 56 tests in 0.666s
FAILED (failures=2, errors=9)
```
## RED elenchi (agenti presenti, hooks/run e config.py come in HEAD)
```
FAIL: test_readonly_list_matches_config_and_agents (tests.test_wrapper.WrapperTest.test_readonly_list_matches_config_and_agents)
Ran 78 tests in 17.946s
FAILED (failures=1)
```
## GREEN
- file di test mirati (manifest, wrapper, config, taskcmd, profiles, check_task_verdict): 284 test OK
- claude plugin validate --strict .: Validation passed, exit 0
- PYTHONWARNINGS=error::ResourceWarning tests/run: 3882 test su 3.11 e 3.13, exit 0 (suite-task-6.log)
