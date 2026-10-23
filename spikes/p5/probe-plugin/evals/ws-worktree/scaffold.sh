#!/usr/bin/env bash
# Scaffold della sonda, variante VE12: il workspace stesso è un worktree git di un checkout principale creato fuori dal
# workspace, sotto la HOME della corsa ($HOME/proj). Scrive in sonda-scaffold.txt cartella corrente, HOME, il contenuto
# del file .git (il gitdir sta fuori dal workspace) e i SOLI NOMI delle variabili d'ambiente.
set -u
t0="$(date +%s)"
if [ -e "$HOME/.claude/settings.json" ] || [ -e "$HOME/.local/state/tollgate" ]; then
  echo "sonda scaffold: la HOME sembra quella vera: mi fermo" >&2
  exit 1
fi
[ -z "$(ls -A . 2>/dev/null)" ] || { echo "sonda scaffold: il workspace non è vuoto" >&2; exit 1; }
ws="$(pwd)"
mkdir -p "$HOME/proj"
git init -q -b main "$HOME/proj" || exit 1
printf 'sonda\n' > "$HOME/proj/README.md"
git -C "$HOME/proj" add README.md
git -C "$HOME/proj" -c user.name=sonda -c user.email=sonda@example.invalid commit -q -m "sonda: commit iniziale" || exit 1
git -C "$HOME/proj" worktree add -q "$ws" -b tg/1-sonda || { echo "sonda scaffold: git worktree add fallito" >&2; exit 1; }
mkdir -p "$HOME/.claude/plugins" "$HOME/.sonda-eval/superpowers"
cat > "$HOME/.claude/plugins/installed_plugins.json" <<JSON
{"version": 2, "plugins": {"superpowers@claude-plugins-official": [{"scope": "user", "installPath": "$HOME/.sonda-eval/superpowers", "version": "7.0.0"}]}}
JSON
{
  echo "PWD=$ws"
  echo "HOME=${HOME:-UNSET}"
  echo "CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-UNSET}"
  echo "DOT_GIT_IS_FILE=$([ -f .git ] && echo yes || echo no)"
  echo "DOT_GIT_CONTENT=$(head -n 1 .git 2>/dev/null)"
  echo "GITDIR_OUTSIDE_WORKSPACE=$(case "$(git rev-parse --absolute-git-dir 2>/dev/null)" in "$ws"/*) echo no ;; *) echo yes ;; esac)"
  echo "BRANCH=$(git branch --show-current)"
  echo "WORKTREE_LIST=$(git worktree list | wc -l)"
  echo "ENV_NAMES=$(compgen -e | sort | paste -sd, -)"
  echo "INSTALLED_PLUGINS_SHA256=$(sha256sum "$HOME/.claude/plugins/installed_plugins.json" | cut -d' ' -f1)"
  echo "SCAFFOLD_SECONDS=$(( $(date +%s) - t0 ))"
} > sonda-scaffold.txt
