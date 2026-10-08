# Evidenza GitHub di P0, recuperata il 2026-10-08 con sole letture (le uscite originali in /tmp sono andate perse)

## G1: GET di protezione sul privato
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","documentation_url":"https://docs.github.com/rest/branches/branch-protection#get-branch-protection","status":"403"}gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)

## G1: GET dei rulesets sul privato
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","documentation_url":"https://docs.github.com/rest/repos/rules#get-all-repository-rulesets","status":"403"}gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)

## G2 privato: probe-verdict (actions: read) run 37826814448 (log del job dall'API)
Actions: read
Artifact download completed successfully.
head=212ad7df7d9e5c11771d2dcebe718ca9e4607d83

## G2 privato: probe-verdict-noactions run 37826814500 (log del job dall'API)
##[error]Unable to download artifact(s): Resource not accessible by integration

## G2 pubblico: probe-verdict-noactions run 37826573007 (log del job dall'API)
Artifact download completed successfully.
head=12bc887b87607a7f094912464d6f4e5a8819b5e3

## G3: probe-target feature3 run 37826779361
echo "base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0"
base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0
Contents: read
##[endgroup]
Metadata: read
Secret source: Actions
shell: /usr/bin/bash -e {0}
t	Run echo "base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0"	2026-10-08T18:45:50.6328368Z ##[group]Run echo "base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0"

## G3: probe-target feature4 run 37826787737
echo "base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0"
base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0
Contents: read
##[endgroup]
Metadata: read
Secret source: Actions
shell: /usr/bin/bash -e {0}
t	Run echo "base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0"	2026-10-08T18:45:54.4773061Z ##[group]Run echo "base=other workflow_sha=65b580f62c05393785b1c28d497c1e759fe180b0"

## G3: SHA di main e di other
65b580f62c05393785b1c28d497c1e759fe180b0
b89e454862ea83af1aad85977ee241193ff1e7f3

## G4: protezione attuale del pubblico
Nota: la protezione usata per G4 è stata tolta dopo l'esperimento, quindi gli stati BLOCKED/CLEAN con `app_id` 15368 e -1 non si possono rileggere ora. Restano: lo stato `tollgate/verdict` di `github-actions[bot]` sulla PR #1 (sotto) e l'avatar `in/15368` dell'app GitHub Actions negli stati (sezione G5). La risposta qui sotto riconferma il caso 404 «Branch not protected» di 9.3.
{"message":"Branch not protected","documentation_url":"https://docs.github.com/rest/branches/branch-protection#get-branch-protection","status":"404"}gh: Branch not protected (HTTP 404)

## G4: PR del pubblico, stato di merge e stati della testa
PR #3 Bump left-pad from 1.1.0 to 1.3.0 head=edee80e9a72d4b367680ffaa8cd8aefd4aa58901 merge=CLEAN
  stato probe/dbt=success creator=github-actions[bot]
PR #2 controllo-g5 head=3c52bc231bfc29b7880cdfba6dd55a1da1222208 merge=CLEAN
  stato probe/dbt=success creator=github-actions[bot]
PR #1 g4 head=12bc887b87607a7f094912464d6f4e5a8819b5e3 merge=UNKNOWN
  stato tollgate/verdict=success creator=github-actions[bot]

## G5: probe-run sulla PR di Dependabot, run 37827197613
echo "head=edee80e9a72d4b367680ffaa8cd8aefd4aa58901" > result.txt
Artifact probe-result has been successfully uploaded! Final size is 181 bytes. Artifact ID is 11572560804
Artifact probe-result.zip successfully finalized. Artifact ID 11572560804
Contents: read
##[endgroup]
Metadata: read
run	Run echo "head=edee80e9a72d4b367680ffaa8cd8aefd4aa58901" > result.txt	2026-10-08T18:49:09.6450291Z ##[group]Run echo "head=edee80e9a72d4b367680ffaa8cd8aefd4aa58901" > result.txt
Secret source: Dependabot
shell: /usr/bin/bash -e {0}

## G5: probe-dbt (workflow_run), run 37827222268
echo "actor=dependabot[bot] triggering_actor=dependabot[bot] run_actor=dependabot[bot]"
echo "secret_presente=true"
gh api -X POST "repos/ginz0ls/tollgate-probe-public/statuses/edee80e9a72d4b367680ffaa8cd8aefd4aa58901" -f state=success -f context=probe/dbt && echo "STATUS_SCRITTO" || echo "STATUS_NEGATO"
Actions: read
actor=dependabot[bot] triggering_actor=dependabot[bot] run_actor=dependabot[bot]
Contents: read
d	Run echo "actor=dependabot[bot] triggering_actor=dependabot[bot] run_actor=dependabot[bot]"	2026-10-08T18:49:20.2403584Z ##[group]Run echo "actor=dependabot[bot] triggering_actor=dependabot[bot] run_actor=dependabot[bot]"
##[endgroup]
env:
  GH_TOKEN: ***
Metadata: read
secret_presente=true
Secret source: Actions
shell: /usr/bin/bash -e {0}
Statuses: write
{"url":"https://api.github.com/repos/ginz0ls/tollgate-probe-public/statuses/edee80e9a72d4b367680ffaa8cd8aefd4aa58901","avatar_url":"https://avatars.githubusercontent.com/in/15368?v=4","id":55922603665,"node_id":"SC_kwDOVBc5Cc8AAAANBT82kQ","state":"success","description":null,"target_url":null,"context":"probe/dbt","created_at":"2026-10-08T18:49:20Z","updated_at":"2026-10-08T18:49:20Z","creator":{"login":"github-actions[bot]","id":41898282,"node_id":"MDM6Qm90NDE4OTgyODI=","avatar_url":"https://avatars.githubusercontent.com/in/15368?v=4","gravatar_id":"","url":"https://api.github.com/users/github-actions%5Bbot%5D","html_url":"https://github.com/apps/github-actions","followers_url":"https://api.github.com/users/github-actions%5Bbot%5D/followers","following_url":"https://api.github.com/users/github-actions%5Bbot%5D/following{/other_user}","gists_url":"https://api.github.com/users/github-actions%5Bbot%5D/gists{/gist_id}","starred_url":"https://api.github.com/users/github-actions%5Bbot%5D/starred{/owner}{/repo}","subscriptions_url":"https://api.github.com/users/github-actions%5Bbot%5D/subscriptions","organizations_url":"https://api.github.com/users/github-actions%5Bbot%5D/orgs","repos_url":"https://api.github.com/users/github-actions%5Bbot%5D/repos","events_url":"https://api.github.com/users/github-actions%5Bbot%5D/events{/privacy}","received_events_url":"https://api.github.com/users/github-actions%5Bbot%5D/received_events","type":"Bot","user_view_type":"public","site_admin":false}}STATUS_SCRITTO
