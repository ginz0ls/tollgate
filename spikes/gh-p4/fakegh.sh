#!/usr/bin/env bash
# gh finto del modo controlla di run-p4-gate.sh: registra gli argomenti, nessuna rete.
# Le risposte con --jq sono già nella forma filtrata (il finto non valuta jq).
printf '%s\t' "$@" >> "$P4_FAKE_LOG"; printf '\n' >> "$P4_FAKE_LOG"
st="$P4_FAKE_STATE"; mkdir -p "$st"
counter() { local n; n="$(cat "$st/$1" 2>/dev/null || echo "$2")"; n=$((n + 1)); echo "$n" > "$st/$1"; echo "$n"; }
ident=(-c user.name=fake -c user.email=fake@example.invalid)
has() { local a; for a in "${@:2}"; do [ "$a" = "$1" ] && return 0; done; return 1; }
seed() { [ -n "${P4_FAKE_SEED:-}" ] && [ -f "$P4_FAKE_SEED.$1" ] && cat "$P4_FAKE_SEED.$1"; }
case "${1:-}" in
  --version) echo "gh version 2.46.0 (finto)"; exit 0 ;;
  auth) echo "Logged in to github.com account ginz0ls (finto)"; exit 0 ;;
  repo)
    case "$2" in
      clone) git clone -q "$P4_GIT_BASE/$3.git" "$4"; exit $? ;;
    esac ;;
  api)
    ep=""; incl=0; jq=0; method=GET; skip=0; input=""
    args=("${@:2}")
    for ((i = 0; i < ${#args[@]}; i++)); do
      a="${args[$i]}"
      case "$a" in
        --include) incl=1 ;;
        --jq|-q) jq=1; i=$((i + 1)) ;;
        --method|-X) method="${args[$((i + 1))]}"; i=$((i + 1)) ;;
        --input) input="${args[$((i + 1))]}"; i=$((i + 1)) ;;
        -f) i=$((i + 1)) ;;
        -*) ;;
        *) [ -n "$ep" ] || ep="$a" ;;
      esac
    done
    [ -n "$input" ] && cp "$input" "$st/put-body-$(counter put 0).json"
    case "$method:$ep" in
      PUT:*/branches/main/protection) touch "$st/protected-done"; echo '{}'; exit 0 ;;
      POST:*/statuses/*) echo '{}'; exit 0 ;;
    esac
    case "$ep" in
      repos/*/*/branches/main/protection)
        if [[ "$ep" == *detect* ]]; then
          [ "$incl" = 1 ] && printf 'HTTP/2.0 403 Forbidden\r\n\r\n'
          echo '{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","status":"403"}'
          echo "gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)" >&2
        elif [ -f "$st/protected-done" ]; then
          [ "$incl" = 1 ] && printf 'HTTP/2.0 200 OK\r\n\r\n'
          echo '{"required_status_checks":{"strict":true,"checks":[]}}'
          exit 0
        else
          [ "$incl" = 1 ] && printf 'HTTP/2.0 404 Not Found\r\n\r\n'
          echo '{"message":"Branch not protected","status":"404"}'
          echo "gh: Branch not protected (HTTP 404)" >&2
        fi
        exit 1 ;;
      repos/*/*/commits/*/check-runs*)
        if [ "$jq" = 1 ]; then printf 'completed\tsuccess\t15368\n'; else echo '{"check_runs":[]}'; fi; exit 0 ;;
      repos/*/*/commits/*/statuses*)
        if [ -n "${P4_FAKE_SEED:-}" ] && [ -f "$P4_FAKE_SEED.statuses" ]; then cat "$P4_FAKE_SEED.statuses"
        else echo '{"context":"tollgate/base","state":"success","creator":"github-actions[bot]","description":"finto","created_at":"2099-01-01T00:00:00Z"}'; fi
        exit 0 ;;
      repos/*/*/issues/*/comments*)
        while read -r p; do
          p="${p%\"}"; p="${p#\"}"
          printf '{"id":1,"user":"github-actions[bot]","body":"%s sha=%s -->\\ntesto"}\n' "$p" "${P4_WAIT_SHA:-x}"
        done < <(seed comments)
        exit 0 ;;
      repos/*/*/pulls/*) echo '{"number":1,"head":{"sha":"x","ref":"x","repo":{"full_name":"ginz0ls/x"}},"base":{"ref":"main"},"body":"x","state":"open"}'; exit 0 ;;
      repos/*/*/actions/runs/*/timing) echo '{"billable":{"UBUNTU":{"total_ms":60000}},"run_duration_ms":60000}'; exit 0 ;;
      repos/*/*/actions/runs/*)
        printf '{"id":1,"event":"pull_request","status":"completed","conclusion":"success","run_started_at":"2098-12-31T23:59:00Z","updated_at":"2099-01-01T00:01:00Z","pull_requests":[{"number":%s}]}\n' "$(cat "${P4_FAKE_SEED:-/dev/null}.pr" 2>/dev/null || echo 1)"
        exit 0 ;;
      repos/*/*) echo '{"full_name":"x"}'; exit 0 ;;
      *) echo '{}'; exit 0 ;;
    esac ;;
  issue)
    case "$2" in
      create) n="$(counter issue 0)"; echo "https://github.com/ginz0ls/tollgate-p4-protected/issues/$n"; exit 0 ;;
      close|comment) exit 0 ;;
      list) echo '[{"number":1,"title":"tollgate: merge non verificato"}]'; exit 0 ;;
      view) echo '{"number":1,"title":"tollgate: merge non verificato","comments":[{"body":"x"}]}'; exit 0 ;;
    esac ;;
  pr)
    case "$2" in
      create)
        n="$(counter pr 0)"; head=""
        for ((i = 1; i <= $#; i++)); do [ "${!i}" = --head ] && { j=$((i + 1)); head="${!j}"; }; done
        echo "$head" > "$st/pr-$n"
        echo "https://github.com/ginz0ls/tollgate-p4-protected/pull/$n"; exit 0 ;;
      merge)
        br="$(cat "$st/pr-$3")"; tmp="$(mktemp -d)"; bare="$P4_GIT_BASE/ginz0ls/tollgate-p4-detect.git"
        git clone -q "$bare" "$tmp/m" && git -C "$tmp/m" fetch -q origin "$br" \
          && git -C "$tmp/m" merge -q --squash FETCH_HEAD && git -C "$tmp/m" "${ident[@]}" commit -qm "squash $br" \
          && git -C "$tmp/m" push -q origin HEAD:main || exit 1
        touch "$st/merged-$3"; exit 0 ;;
      view)
        if [ -f "$st/merged-$3" ]; then echo '{"state":"MERGED","mergedAt":"2099-01-01T00:00:00Z"}'; exit 0; fi
        m="$(cat "${P4_FAKE_SEED:-/dev/null}.merge" 2>/dev/null)"
        echo "{\"state\":\"OPEN\",\"mergedAt\":null,\"mergeStateStatus\":\"${m:-CLEAN}\",\"headRefOid\":\"x\"}"; exit 0 ;;
      edit) exit 0 ;;
      list)
        head=""
        for ((i = 1; i <= $#; i++)); do [ "${!i}" = --head ] && { j=$((i + 1)); head="${!j}"; }; done
        if [ -n "$head" ]; then
          sha="$(git --git-dir "$P4_GIT_BASE/ginz0ls/tollgate-p4-protected.git" rev-parse -q --verify "refs/heads/$head" 2>/dev/null)"
          if [ -n "$sha" ]; then
            n="$(grep -lx -- "$head" "$st"/pr-* 2>/dev/null | head -n 1 | sed 's/.*pr-//')"
            printf '[{"number":%s,"state":"OPEN","url":"https://github.com/ginz0ls/tollgate-p4-protected/pull/%s","headRefOid":"%s","mergedAt":null,"isCrossRepository":false}]\n' "${n:-1}" "${n:-1}" "$sha"
            exit 0
          fi
        fi
        echo '[]'; exit 0 ;;
      close) exit 0 ;;
    esac ;;
  run)
    case "$2" in
      list)
        n="$(counter run 100)"
        printf '[{"databaseId":%s,"headSha":"%s","headBranch":"x","event":"push","status":"completed","conclusion":"success","createdAt":"2099-01-01T00:00:00Z"}]\n' "$n" "$P4_WAIT_SHA"
        exit 0 ;;
      watch) echo "Run completed (finto)"; exit 0 ;;
      view) echo '{"databaseId":1,"status":"completed","conclusion":"success","jobs":[{"name":"tollgate-base","conclusion":"success"}]}'; exit 0 ;;
    esac ;;
esac
echo "gh finto: comando non previsto: $*" >&2
exit 2