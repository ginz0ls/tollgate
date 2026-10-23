#!/usr/bin/env bash
# Scaffold della sonda (VE4, VE10): gira nel workspace vuoto, con la HOME della corsa. Scrive in sonda-scaffold.txt
# cartella corrente, HOME, CLAUDE_CONFIG_DIR, come trova la propria cartella (BASH_SOURCE) e la radice del plugin,
# i SOLI NOMI delle variabili d'ambiente; crea un repo git e un worktree in .claude/worktrees/ e scrive
# $HOME/.claude/plugins/installed_plugins.json come farà il banco di tollgate.
set -u
t0="$(date +%s)"
# sicurezza: la HOME della corsa deve essere temporanea; se sembra quella vera, non si scrive niente
if [ -e "$HOME/.claude/settings.json" ] || [ -e "$HOME/.local/state/tollgate" ]; then
  echo "sonda scaffold: la HOME sembra quella vera: mi fermo" >&2
  exit 1
fi
out=sonda-scaffold.txt
script="${BASH_SOURCE[0]}"
script_dir="$(cd "$(dirname "$script")" 2>/dev/null && pwd)"
root_guess="$(cd "$script_dir/../.." 2>/dev/null && pwd)"
{
  echo "PWD=$(pwd)"
  echo "HOME=${HOME:-UNSET}"
  echo "CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-UNSET}"
  echo "TMPDIR=${TMPDIR:-UNSET}"
  echo "BASH_SOURCE_0=$script"
  echo "DOLLAR_0=$0"
  echo "SCRIPT_DIR=${script_dir:-UNSET}"
  echo "ROOT_GUESS=${root_guess:-UNSET}"
  if [ -n "$root_guess" ] && [ -f "$root_guess/.claude-plugin/plugin.json" ]; then echo "ROOT_GUESS_IS_PLUGIN=yes"; else echo "ROOT_GUESS_IS_PLUGIN=no"; fi
  echo "ENV_NAMES=$(compgen -e | sort | paste -sd, -)"
  echo "WHICH_PYTHON3=$(command -v python3 || echo none)"
  echo "WHICH_GIT=$(command -v git || echo none)"
  echo "WHICH_SONDA_SHIM=$(command -v sonda-shim || echo none)"
} > "$out"

git init -q -b main . || { echo "sonda scaffold: git init fallito" >&2; exit 1; }
printf 'sonda\n' > README.md
git add README.md
git -c user.name=sonda -c user.email=sonda@example.invalid commit -q -m "sonda: commit iniziale" || exit 1
mkdir -p .claude/worktrees
git worktree add -q .claude/worktrees/sonda-wt -b sonda-wt || { echo "sonda scaffold: git worktree add fallito" >&2; exit 1; }

mkdir -p "$HOME/.claude/plugins" "$HOME/.sonda-eval/superpowers"
cat > "$HOME/.claude/plugins/installed_plugins.json" <<JSON
{"version": 2, "plugins": {"superpowers@claude-plugins-official": [{"scope": "user", "installPath": "$HOME/.sonda-eval/superpowers", "version": "7.0.0"}]}}
JSON
{
  echo "INSTALLED_PLUGINS_SHA256=$(sha256sum "$HOME/.claude/plugins/installed_plugins.json" | cut -d' ' -f1)"
  echo "INSTALLED_PLUGINS_MTIME=$(stat -c %Y "$HOME/.claude/plugins/installed_plugins.json")"
  echo "WORKTREE_LIST=$(git worktree list | wc -l)"
  echo "SCAFFOLD_SECONDS=$(( $(date +%s) - t0 ))"
} >> "$out"
