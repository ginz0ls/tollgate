#!/bin/bash
# Custom Claude Code statusline - Modified: 2026-03-02
# Fix: context from input JSON directly, always-visible usage, auto-wrap, weekly array bug

input=$(cat)

# ---- setup ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/statusline.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then HAS_JQ=1; fi

# ---- terminal width ----
TERM_COLS=0
if [ -n "$COLUMNS" ] && [ "$COLUMNS" -gt 0 ]; then
  TERM_COLS="$COLUMNS"
elif command -v tput >/dev/null 2>&1; then
  TERM_COLS=$(tput cols 2>/dev/null || echo 0)
fi
# Fallback: leggi da /dev/tty (funziona anche senza TTY su stdin)
if [ "$TERM_COLS" -eq 0 ] 2>/dev/null; then
  TERM_COLS=$(stty size < /dev/tty 2>/dev/null | awk '{print $2}')
fi
# Ultimo fallback: 80 (standard ANSI) — conservativo per prevenire wrap nativo nel terminale
[ "${TERM_COLS:-0}" -eq 0 ] 2>/dev/null && TERM_COLS=80

# ---- color helpers ----
use_color=1
[ -n "$NO_COLOR" ] && use_color=0

dir_color()    { [ "$use_color" -eq 1 ] && printf '\033[38;5;117m'; }   # sky blue
git_color()    { [ "$use_color" -eq 1 ] && printf '\033[38;5;150m'; }   # soft green
model_color()  { [ "$use_color" -eq 1 ] && printf '\033[38;5;147m'; }   # light purple
cc_ver_color() { [ "$use_color" -eq 1 ] && printf '\033[38;5;249m'; }   # light gray
style_color()  { [ "$use_color" -eq 1 ] && printf '\033[38;5;245m'; }   # gray
cost_color()   { [ "$use_color" -eq 1 ] && printf '\033[38;5;222m'; }   # light gold
burn_color()   { [ "$use_color" -eq 1 ] && printf '\033[38;5;220m'; }   # bright gold
usage_color()  { [ "$use_color" -eq 1 ] && printf '\033[38;5;189m'; }   # lavender
weekly_color() { [ "$use_color" -eq 1 ] && printf '\033[38;5;183m'; }   # light violet
rst()          { [ "$use_color" -eq 1 ] && printf '\033[0m'; }

# context color depends on remaining %
ctx_color() {
  local pct="${1:-100}"
  if [ "$use_color" -eq 1 ]; then
    if   [ "$pct" -le 20 ]; then printf '\033[38;5;203m'   # coral red
    elif [ "$pct" -le 40 ]; then printf '\033[38;5;215m'   # peach
    else                         printf '\033[38;5;158m'   # mint green
    fi
  fi
}

# session reset color depends on elapsed %
session_color() {
  local elapsed_pct="${1:-0}"
  local rem=$(( 100 - elapsed_pct ))
  if [ "$use_color" -eq 1 ]; then
    if   [ "$rem" -le 10 ]; then printf '\033[38;5;210m'   # light pink
    elif [ "$rem" -le 25 ]; then printf '\033[38;5;228m'   # light yellow
    else                         printf '\033[38;5;194m'   # light green
    fi
  fi
}

# ---- helpers ----
progress_bar() {
  local pct="${1:-0}" width="${2:-10}"
  [[ "$pct" =~ ^[0-9]+$ ]] || pct=0
  (( pct < 0 ))   && pct=0
  (( pct > 100 )) && pct=100
  local filled=$(( pct * width / 100 ))
  local empty=$(( width - filled ))
  printf '%*s' "$filled" '' | tr ' ' '='
  printf '%*s' "$empty"  '' | tr ' ' '-'
}

to_epoch() {
  local ts="$1"
  if command -v gdate >/dev/null 2>&1; then gdate -d "$ts" +%s 2>/dev/null && return; fi
  date -u -j -f "%Y-%m-%dT%H:%M:%S%z" "${ts/Z/+0000}" +%s 2>/dev/null && return
  python3 - "$ts" <<'PY' 2>/dev/null
import sys, datetime
s=sys.argv[1].replace('Z','+00:00')
print(int(datetime.datetime.fromisoformat(s).timestamp()))
PY
}

fmt_time_hm() {
  local epoch="$1"
  if date -r 0 +%s >/dev/null 2>&1; then date -r "$epoch" +"%H:%M"
  else date -d "@$epoch" +"%H:%M"; fi
}

# Strip ANSI escape codes e misura la larghezza visiva in colonne.
# Gli emoji wide (U+1F000+) occupano 2 colonne — Python3 gestisce correttamente.
visible_len() {
  printf '%s' "$1" | python3 -c "
import sys, re, unicodedata
t = re.sub(r'\x1b\[[0-9;]*m', '', sys.stdin.read())
print(sum(2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in t))
" 2>/dev/null || printf '%s' "$1" | sed 's/\x1b\[[0-9;]*m//g' | wc -m
}

# Abbrevia il path se supera max_chars: mostra ~/…/basename
shorten_path() {
  local p="$1" max="${2:-35}"
  if [ "${#p}" -le "$max" ]; then
    echo "$p"
  else
    local base
    base=$(basename "$p")
    local short="~/…/${base}"
    if [ "${#short}" -le "$max" ]; then
      echo "$short"
    else
      # basename stesso troppo lungo: tronca dalla destra
      echo "…${base: -$(( max - 1 ))}"
    fi
  fi
}

# ---- logging ----
{
  echo "[$TIMESTAMP] Status line triggered — TERM_COLS=${TERM_COLS} COLUMNS=${COLUMNS:-unset}"
  echo "[$TIMESTAMP] Input:"
  if [ "$HAS_JQ" -eq 1 ]; then
    echo "$input" | jq . 2>/dev/null || echo "$input"
    echo "[$TIMESTAMP] Using jq"
  else
    echo "$input"
    echo "[$TIMESTAMP] WARNING: jq not found"
  fi
  echo "---"
} >> "$LOG_FILE" 2>/dev/null

# ---- extract basics ----
if [ "$HAS_JQ" -eq 1 ]; then
  current_dir=$(echo "$input"  | jq -r '.workspace.current_dir // .cwd // "unknown"' 2>/dev/null | sed "s|^$HOME|~|g")
  model_name=$(echo "$input"   | jq -r '.model.display_name // "Claude"' 2>/dev/null)
  cc_version=$(echo "$input"   | jq -r '.version // ""' 2>/dev/null)
  output_style=$(echo "$input" | jq -r '.output_style.name // ""' 2>/dev/null)

  # ---- context window — read directly from input JSON (FIX: was parsing .jsonl file) ----
  ctx_remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty' 2>/dev/null)
  ctx_used=$(echo "$input"      | jq -r '.context_window.used_percentage // empty' 2>/dev/null)

  # ---- cost from input ----
  cost_usd=$(echo "$input"          | jq -r '.cost.total_cost_usd // empty' 2>/dev/null)
  total_duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // empty' 2>/dev/null)

  # ---- session token totals (cumulative per sessione) ----
  ctx_window_size=$(echo "$input"  | jq -r '.context_window.context_window_size // 200000' 2>/dev/null)
  ctx_total_in=$(echo "$input"     | jq -r '.context_window.total_input_tokens // 0' 2>/dev/null)
  ctx_total_out=$(echo "$input"    | jq -r '.context_window.total_output_tokens // 0' 2>/dev/null)
  ctx_cache_create=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0' 2>/dev/null)
  ctx_cache_read=$(echo "$input"   | jq -r '.context_window.current_usage.cache_read_input_tokens // 0' 2>/dev/null)
  ctx_cur_input=$(echo "$input"    | jq -r '.context_window.current_usage.input_tokens // 0' 2>/dev/null)
  session_tok_total=$(( ctx_total_in + ctx_total_out ))
else
  # bash fallback
  current_dir=$(echo "$input" | grep -o '"current_dir"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:"\([^"]*\)".*/\1/' | sed "s|^$HOME|~|g")
  [ -z "$current_dir" ] && current_dir=$(echo "$input" | grep -o '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:"\([^"]*\)".*/\1/' | sed "s|^$HOME|~|g")
  [ -z "$current_dir" ] && current_dir="unknown"
  model_name=$(echo "$input" | grep -o '"display_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:"\([^"]*\)".*/\1/')
  [ -z "$model_name" ] && model_name="Claude"
  cc_version=$(echo "$input" | grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:"\([^"]*\)".*/\1/')
  output_style=$(echo "$input" | grep -o '"output_style"[[:space:]]*:[[:space:]]*{[^}]*"name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
  ctx_remaining=$(echo "$input" | grep -o '"remaining_percentage"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*\([0-9]*\).*/\1/')
  ctx_used=$(echo "$input"      | grep -o '"used_percentage"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*\([0-9]*\).*/\1/')
  cost_usd=$(echo "$input" | grep -o '"total_cost_usd"[[:space:]]*:[[:space:]]*[0-9.]*' | sed 's/.*:[[:space:]]*\([0-9.]*\).*/\1/')
  total_duration_ms=$(echo "$input" | grep -o '"total_duration_ms"[[:space:]]*:[[:space:]]*[0-9]*' | sed 's/.*:[[:space:]]*\([0-9]*\).*/\1/')
fi

# ---- git ----
git_branch=""
git_dirty=""
git_ahead_behind=""
if git rev-parse --git-dir >/dev/null 2>&1; then
  git_branch=$(git branch --show-current 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
  dirty_count=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  [ "${dirty_count:-0}" -gt 0 ] && git_dirty=" ✎${dirty_count}"
  # Ahead/behind rispetto al remote tracking branch
  ab=$(git rev-list --left-right --count HEAD...@{u} 2>/dev/null)
  if [ -n "$ab" ]; then
    ahead=$(echo "$ab" | awk '{print $1}')
    behind=$(echo "$ab" | awk '{print $2}')
    [ "${ahead:-0}" -gt 0 ]  && git_ahead_behind="${git_ahead_behind} ⬆${ahead}"
    [ "${behind:-0}" -gt 0 ] && git_ahead_behind="${git_ahead_behind} ⬇${behind}"
  fi
fi

# ---- account (email + displayName da ~/.claude.json) ----
account_display=""
CLAUDE_JSON="$HOME/.claude.json"
if [ -f "$CLAUDE_JSON" ] && [ "$HAS_JQ" -eq 1 ]; then
  acct_name=$(jq -r '.oauthAccount.emailAddress // empty' "$CLAUDE_JSON" 2>/dev/null)
  acct_plan=$(jq -r '.oauthAccount.billingType // empty' "$CLAUDE_JSON" 2>/dev/null)
  # Normalizza plan name
  case "$acct_plan" in
    stripe_subscription) acct_plan="Pro" ;;
    free*)               acct_plan="Free" ;;
    *)                   acct_plan="" ;;
  esac
  [ -n "$acct_name" ] && account_display="${acct_name}"
  [ -n "$acct_plan" ] && account_display="${account_display} (${acct_plan})"
fi

# ---- cost per hour ----
cost_per_hour=""
if [ -n "$cost_usd" ] && [ -n "$total_duration_ms" ] && [ "$total_duration_ms" -gt 0 ] 2>/dev/null; then
  cost_per_hour=$(echo "$cost_usd $total_duration_ms" | awk '{printf "%.2f", $1 * 3600000 / $2}')
fi

# ---- session duration ----
session_duration=""
if [ -n "$total_duration_ms" ] && [ "$total_duration_ms" -gt 0 ] 2>/dev/null; then
  total_sec=$(( total_duration_ms / 1000 ))
  dur_h=$(( total_sec / 3600 ))
  dur_m=$(( (total_sec % 3600) / 60 ))
  if [ "$dur_h" -gt 0 ]; then
    session_duration="${dur_h}h ${dur_m}m"
  else
    session_duration="${dur_m}m"
  fi
fi

# ---- cache efficiency (% input servito da cache) ----
cache_eff_pct=""
cur_turn_total=$(( ${ctx_cache_read:-0} + ${ctx_cache_create:-0} + ${ctx_cur_input:-0} ))
if [ "$cur_turn_total" -gt 0 ]; then
  cache_eff_pct=$(( ${ctx_cache_read:-0} * 100 / cur_turn_total ))
fi

# ---- Anthropic usage API: session (5h) e weekly (7d) percentuali reali ----
# Endpoint: https://api.anthropic.com/api/oauth/usage
# Credenziali: ~/.claude/.credentials.json (Linux) — equivalente macOS Keychain
USAGE_API_CACHE="/tmp/.cc_statusline_usage_api.json"
USAGE_API_TTL=60  # 60 secondi

quota_5h_pct=""; quota_5h_reset=""; quota_5h_remaining_min=""
quota_7d_pct=""; quota_7d_reset=""; quota_7d_remaining_min=""

if [ "$HAS_JQ" -eq 1 ]; then
  CREDS_FILE="$HOME/.claude/.credentials.json"

  # Calcola età cache
  api_cache_age=999999
  if [ -f "$USAGE_API_CACHE" ]; then
    api_mtime=$(stat -c %Y "$USAGE_API_CACHE" 2>/dev/null || stat -f %m "$USAGE_API_CACHE" 2>/dev/null || echo 0)
    api_cache_age=$(( $(date +%s) - api_mtime ))
  fi

  # Aggiorna cache se scaduta (in background per non bloccare)
  if [ "$api_cache_age" -gt "$USAGE_API_TTL" ] && [ -f "$CREDS_FILE" ]; then
    (
      token=$(jq -r '.claudeAiOauth.accessToken // empty' "$CREDS_FILE" 2>/dev/null)
      if [ -n "$token" ]; then
        body=$(curl -sf --max-time 5 \
          -H "Authorization: Bearer $token" \
          -H "anthropic-beta: oauth-2025-04-20" \
          "https://api.anthropic.com/api/oauth/usage" 2>/dev/null)
        [ -n "$body" ] && echo "$body" > "$USAGE_API_CACHE"
      fi
    ) &
    disown
  fi

  # Leggi dalla cache se disponibile
  if [ -f "$USAGE_API_CACHE" ]; then
    api_data=$(cat "$USAGE_API_CACHE" 2>/dev/null)
    if [ -n "$api_data" ]; then
      quota_5h_pct=$(echo "$api_data"    | jq -r '.five_hour.utilization // empty' 2>/dev/null)
      quota_5h_reset=$(echo "$api_data"  | jq -r '.five_hour.resets_at // empty' 2>/dev/null)
      quota_7d_pct=$(echo "$api_data"    | jq -r '.seven_day.utilization // empty' 2>/dev/null)
      quota_7d_reset=$(echo "$api_data"  | jq -r '.seven_day.resets_at // empty' 2>/dev/null)
      # Converti pct in intero
      [ -n "$quota_5h_pct" ] && quota_5h_pct=$(echo "$quota_5h_pct" | awk '{printf "%d", $1}')
      [ -n "$quota_7d_pct" ] && quota_7d_pct=$(echo "$quota_7d_pct" | awk '{printf "%d", $1}')
      # Calcola minuti rimanenti al reset
      if [ -n "$quota_5h_reset" ]; then
        end5=$(to_epoch "$quota_5h_reset")
        quota_5h_remaining_min=$(( (end5 - $(date +%s)) / 60 ))
        (( quota_5h_remaining_min < 0 )) && quota_5h_remaining_min=0
      fi
      if [ -n "$quota_7d_reset" ]; then
        end7=$(to_epoch "$quota_7d_reset")
        quota_7d_remaining_min=$(( (end7 - $(date +%s)) / 60 ))
        (( quota_7d_remaining_min < 0 )) && quota_7d_remaining_min=0
      fi
    fi
  fi
fi

# ---- Platform status (status.claude.com) — cache 15s, sync refresh at 5min ----
STATUS_CACHE="/tmp/.cc_statusline_platform_status.txt"
STATUS_TTL=15
STATUS_SYNC_AGE=300  # 5 minuti — se cache più vecchia, fetch sincrono (non bg)
platform_alert=""

_fetch_status() {
  local body indicator
  body=$(curl -sf --max-time 3 "https://status.claude.com/api/v2/status.json" 2>/dev/null)
  if [ -n "$body" ] && [ "$HAS_JQ" -eq 1 ]; then
    indicator=$(echo "$body" | jq -r '.status.indicator // "none"' 2>/dev/null)
    case "$indicator" in
      minor)    echo "⚠️ degraded" > "$STATUS_CACHE" ;;
      major)    echo "🔶 major outage" > "$STATUS_CACHE" ;;
      critical) echo "🔴 critical outage" > "$STATUS_CACHE" ;;
      *)        echo "🟢 operational" > "$STATUS_CACHE" ;;
    esac
  fi
}

status_cache_age=999999
if [ -f "$STATUS_CACHE" ]; then
  status_mtime=$(stat -c %Y "$STATUS_CACHE" 2>/dev/null || stat -f %m "$STATUS_CACHE" 2>/dev/null || echo 0)
  status_cache_age=$(( $(date +%s) - status_mtime ))
fi

if [ "$status_cache_age" -gt "$STATUS_SYNC_AGE" ]; then
  # Cache molto vecchia o inesistente: fetch sincrono (max 3s) per avere dati subito
  _fetch_status
elif [ "$status_cache_age" -gt "$STATUS_TTL" ]; then
  # Cache scaduta ma recente: refresh in background (non blocca la statusline)
  ( _fetch_status ) & disown
fi
[ -f "$STATUS_CACHE" ] && platform_alert=$(cat "$STATUS_CACHE" 2>/dev/null | tr -d '\n')

# ---- ccusage: weekly cost/token (cache) ----
session_txt=""; session_pct=0; session_bar=""
weekly_cost=""; weekly_tokens=""

if command -v ccusage >/dev/null 2>&1 && [ "$HAS_JQ" -eq 1 ]; then

  # Weekly usage — cached (ccusage weekly è lento ~14s, si aggiorna in background)
  WEEKLY_CACHE="/tmp/.cc_statusline_weekly.json"
  WEEKLY_CACHE_TTL=300  # 5 minuti

  # Calcola età cache
  cache_age=999999
  if [ -f "$WEEKLY_CACHE" ]; then
    cache_mtime=$(stat -c %Y "$WEEKLY_CACHE" 2>/dev/null || stat -f %m "$WEEKLY_CACHE" 2>/dev/null || echo 0)
    now_s=$(date +%s)
    cache_age=$(( now_s - cache_mtime ))
  fi

  # Se cache scaduta → aggiorna in background (non blocca la statusline)
  if [ "$cache_age" -gt "$WEEKLY_CACHE_TTL" ]; then
    (ccusage weekly --json > "${WEEKLY_CACHE}.tmp" 2>/dev/null && mv "${WEEKLY_CACHE}.tmp" "$WEEKLY_CACHE") &
    disown
  fi

  # Leggi sempre dalla cache (se esiste)
  weekly_output=""
  [ -f "$WEEKLY_CACHE" ] && weekly_output=$(cat "$WEEKLY_CACHE" 2>/dev/null)
  if [ -n "$weekly_output" ]; then
    # ccusage weekly --json returns {"weekly": [...]} — legge l'ultima settimana
    weekly_cost=$(echo "$weekly_output"   | jq -r '(.weekly // []) | last | .totalCost // empty' 2>/dev/null)
    weekly_tokens=$(echo "$weekly_output" | jq -r '(.weekly // []) | last | .totalTokens // empty' 2>/dev/null)
  fi
fi

# ---- log ----
{
  echo "[$TIMESTAMP] Extracted: dir=${current_dir:-}, model=${model_name:-}, git=${git_branch:-}, ctx_remaining=${ctx_remaining:-}, ctx_used=${ctx_used:-}, cost=${cost_usd:-}, cost_ph=${cost_per_hour:-}, session_tok=${session_tok_total:-}, weekly_cost=${weekly_cost:-}, weekly_tok=${weekly_tokens:-}, session_pct=${session_pct:-}"
} >> "$LOG_FILE" 2>/dev/null

# =========================================================
# RENDER — auto-wrap based on terminal width
# =========================================================

# print_segment: appends a segment to the current line, wrapping if needed.
# CUR_LEN tracks the visible character count of the current line.
CUR_LEN=0

print_segment() {
  local text="$1"
  local sep="${2:-  }"
  local vis_text vis_with_sep

  vis_text=$(visible_len "$text")

  if [ "$CUR_LEN" -eq 0 ]; then
    # First item on line — no separator
    printf '%s' "$text"
    CUR_LEN=$vis_text
  else
    vis_with_sep=$(( CUR_LEN + ${#sep} + vis_text ))
    if [ "$TERM_COLS" -gt 0 ] && [ "$vis_with_sep" -gt "$TERM_COLS" ]; then
      # Wrap to new line
      printf '\n%s' "$text"
      CUR_LEN=$vis_text
    else
      printf '%s%s' "$sep" "$text"
      CUR_LEN=$vis_with_sep
    fi
  fi
}

# ---- Line 1: directory, git (+dirty), model, cc version, output style ----
# Abbrevia il path se lungo — garantisce che la riga 1 non faccia wrap nativo nel terminale
display_dir=$(shorten_path "$current_dir" 35)
print_segment "📁 $(dir_color)${display_dir}$(rst)" ""

if [ -n "$git_branch" ]; then
  git_seg="🌿 $(git_color)${git_branch}$(rst)"
  [ -n "$git_dirty" ] && git_seg="${git_seg}$(git_color)${git_dirty}$(rst)"
  [ -n "$git_ahead_behind" ] && git_seg="${git_seg}$(git_color)${git_ahead_behind}$(rst)"
  print_segment "$git_seg"
fi

print_segment "🤖 $(model_color)${model_name}$(rst)"

[ -n "$cc_version" ] && [ "$cc_version" != "null" ] && \
  print_segment "📟 $(cc_ver_color)v${cc_version}$(rst)"

[ -n "$output_style" ] && [ "$output_style" != "null" ] && \
  print_segment "🎨 $(style_color)${output_style}$(rst)"

printf '\n'

# ---- Line 2: account + platform alert ----
CUR_LEN=0

if [ -n "$account_display" ]; then
  print_segment "👤 $(cc_ver_color)${account_display}$(rst)" ""
fi

[ -n "$platform_alert" ] && print_segment "$platform_alert"

printf '\n'

# ---- Line 3: context window (soglia autocompact = 85%) ----
CUR_LEN=0

AUTOCOMPACT_THRESHOLD=85

if [ -n "$ctx_used" ] && [[ "$ctx_used" =~ ^[0-9]+$ ]]; then
  # "until autocompact" = quanto manca alla soglia di compressione automatica
  until_compact=$(( AUTOCOMPACT_THRESHOLD - ctx_used ))
  (( until_compact < 0 )) && until_compact=0
  ctx_bar=$(progress_bar "$ctx_used" 10)
  # Colore: rosso se already oltre soglia, arancio se < 10% to compact, verde altrimenti
  if   [ "$until_compact" -eq 0 ];   then ctx_col='\033[38;5;203m'
  elif [ "$until_compact" -le 10 ];  then ctx_col='\033[38;5;215m'
  else                                    ctx_col='\033[38;5;158m'
  fi
  [ "$use_color" -eq 1 ] && printf "${ctx_col}" || true
  ctx_colored_val="${ctx_col}${ctx_used}%$(printf '\033[0m')"
  ctx_seg="🧠 $([ "$use_color" -eq 1 ] && printf "${ctx_col}")${ctx_used}% used$(rst) [${ctx_bar}] $([ "$use_color" -eq 1 ] && printf "${ctx_col}")${until_compact}% to compact$(rst)"
  # Cache efficiency: quanto input è servito da cache (più alto = più economico)
  if [ -n "$cache_eff_pct" ] && [ "$cache_eff_pct" -gt 0 ] 2>/dev/null; then
    ctx_seg="${ctx_seg}  $(usage_color)💾 ${cache_eff_pct}% cache$(rst)"
  fi
  print_segment "$ctx_seg" ""
else
  print_segment "🧠 ctx: ?" ""
fi

printf '\n'

# ---- Line 3: quota sessione (5h) e settimanale (7d) — come /usage ----
CUR_LEN=0

# helper: colore quota in base alla %
quota_color() {
  local pct="${1:-0}"
  if [ "$use_color" -eq 1 ]; then
    if   [ "$pct" -ge 80 ]; then printf '\033[38;5;203m'   # rosso
    elif [ "$pct" -ge 50 ]; then printf '\033[38;5;215m'   # arancio
    else                         printf '\033[38;5;158m'   # verde
    fi
  fi
}

# helper: formatta minuti in "2h 14m" o "4d 17h"
fmt_min() {
  local m="${1:-0}"
  if [ "$m" -le 0 ]; then echo "ora"; return; fi
  local d=$(( m / 1440 )) h=$(( (m % 1440) / 60 )) mm=$(( m % 60 ))
  if [ "$d" -gt 0 ]; then echo "${d}g ${h}h"
  elif [ "$h" -gt 0 ]; then echo "${h}h ${mm}m"
  else echo "${mm}m"
  fi
}

# rate_indicator: confronta usage% con tempo elapsed% per valutare la velocità di consumo
# 🟢 on track | 🟡 +1-5% | 🟠 +6-15% | 🔴 >15% ahead
rate_indicator() {
  local usage_pct="${1:-0}" remaining_min="${2:-0}" total_min="${3:-300}"
  (( total_min < 1 )) && total_min=1
  local elapsed=$(( total_min - remaining_min ))
  (( elapsed < 0 )) && elapsed=0
  local time_pct=$(( elapsed * 100 / total_min ))
  local diff=$(( usage_pct - time_pct ))
  if   [ "$diff" -le 0  ]; then echo "🟢"
  elif [ "$diff" -le 5  ]; then echo "🟡"
  elif [ "$diff" -le 15 ]; then echo "🟠"
  else                          echo "🔴"
  fi
}

if [ -n "$quota_5h_pct" ] && [[ "$quota_5h_pct" =~ ^[0-9]+$ ]]; then
  bar_5h=$(progress_bar "$quota_5h_pct" 10)
  ri_5h=$(rate_indicator "$quota_5h_pct" "${quota_5h_remaining_min:-0}" 300)
  reset_5h=""
  [ -n "$quota_5h_remaining_min" ] && reset_5h=" $(fmt_min "$quota_5h_remaining_min")"
  # ETA al 100%: proiezione basata su rate attuale (solo se 🟠 o 🔴)
  eta_5h=""
  if [ "$ri_5h" = "🟠" ] || [ "$ri_5h" = "🔴" ]; then
    elapsed_5h=$(( 300 - ${quota_5h_remaining_min:-0} ))
    if [ "$elapsed_5h" -gt 0 ] && [ "$quota_5h_pct" -gt 0 ]; then
      remaining_cap=$(( 100 - quota_5h_pct ))
      if [ "$remaining_cap" -gt 0 ]; then
        eta_min=$(( remaining_cap * elapsed_5h / quota_5h_pct ))
        eta_5h=" ⏳$(fmt_min "$eta_min")"
      else
        eta_5h=" ⏳ora!"
      fi
    fi
  fi
  print_segment "${ri_5h} 5h: $(quota_color "$quota_5h_pct")${quota_5h_pct}%$(rst) [${bar_5h}]${reset_5h}${eta_5h}" ""
else
  print_segment "⏱ 5h: $(quota_color 0)?$(rst)" ""
fi

if [ -n "$quota_7d_pct" ] && [[ "$quota_7d_pct" =~ ^[0-9]+$ ]]; then
  bar_7d=$(progress_bar "$quota_7d_pct" 10)
  ri_7d=$(rate_indicator "$quota_7d_pct" "${quota_7d_remaining_min:-0}" 10080)
  reset_7d=""
  [ -n "$quota_7d_remaining_min" ] && reset_7d=" $(fmt_min "$quota_7d_remaining_min")"
  print_segment "${ri_7d} 7d: $(quota_color "$quota_7d_pct")${quota_7d_pct}%$(rst) [${bar_7d}]${reset_7d}"
else
  print_segment "📅 7d: $(quota_color 0)?$(rst)"
fi

printf '\n'

# ---- Line 4: session cost + weekly ccusage ----
CUR_LEN=0

# ---- fmt_tokens: formatta token count in K/M ----
fmt_tokens() {
  local n="${1:-0}"
  [[ "$n" =~ ^[0-9]+$ ]] || { echo "?"; return; }
  if   [ "$n" -ge 1000000 ]; then awk -v v="$n" 'BEGIN{printf "%.1fM", v/1000000}'
  elif [ "$n" -ge 1000 ];    then awk -v v="$n" 'BEGIN{printf "%.0fK", v/1000}'
  else echo "${n}"
  fi
}

# Session cost + token count — always visible
sess_cost_seg=""
if [ -n "$cost_usd" ] && [[ "$cost_usd" =~ ^[0-9.]+$ ]]; then
  cost_fmt=$(LC_NUMERIC=C printf '%.2f' "$cost_usd")
  sess_cost_seg="$(cost_color)\$${cost_fmt}$(rst)"
  # add burn rate if meaningful
  if [ -n "$cost_per_hour" ] && [[ "$cost_per_hour" =~ ^[0-9.]+$ ]]; then
    ph_val=$(echo "$cost_per_hour" | awk '{print ($1 > 0.005) ? 1 : 0}')
    [ "$ph_val" = "1" ] && sess_cost_seg="${sess_cost_seg} $(burn_color)@\$${cost_per_hour}/h$(rst)"
  fi
else
  cost_fmt="0.00"
  sess_cost_seg="$(cost_color)\$0.00$(rst)"
fi
# add session token count
if [ -n "$session_tok_total" ] && [ "$session_tok_total" -gt 0 ] 2>/dev/null; then
  tok_fmt=$(fmt_tokens "$session_tok_total")
  sess_cost_seg="${sess_cost_seg} $(usage_color)(${tok_fmt} tok)$(rst)"
fi
# Session duration
sess_dur_seg=""
if [ -n "$session_duration" ]; then
  sess_dur_seg="  $(cc_ver_color)⏱ ${session_duration}$(rst)"
fi
print_segment "💰 sess: ${sess_cost_seg}${sess_dur_seg}" ""

# Weekly cost + token count — always visible
if [ -n "$weekly_cost" ] && [[ "$weekly_cost" =~ ^[0-9.]+$ ]]; then
  wk_fmt=$(LC_NUMERIC=C printf '%.2f' "$weekly_cost")
  wk_seg="📅 wk: $(weekly_color)\$${wk_fmt}$(rst)"
  if [ -n "$weekly_tokens" ] && [[ "$weekly_tokens" =~ ^[0-9]+$ ]]; then
    tok_fmt=$(fmt_tokens "$weekly_tokens")
    wk_seg="${wk_seg} $(usage_color)(${tok_fmt} tok)$(rst)"
  fi
else
  wk_seg="📅 wk: $(weekly_color)?$(rst)"
fi
print_segment "$wk_seg"

printf '\n'
