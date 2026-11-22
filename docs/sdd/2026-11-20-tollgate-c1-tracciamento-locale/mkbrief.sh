#!/bin/bash
# uso: mkbrief.sh N  → scrive W/task-N-brief.md (testo del task + voci di carry + cautele)
set -e
cd "/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/c1"
W=.superpowers/sdd/2026-11-20-tollgate-c1-tracciamento-locale
N=$1
OUT=$(bash /home/USER/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/subagent-driven-development/scripts/task-brief docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md $N)
P="${OUT#wrote }"; P="${P%%: *}"; mv "$P" "$P.tmp"; P="$P.tmp"
{
  cat "$P"
  echo
  echo "## Decisioni del controller per questo task (da carry.md, prevalgono sul testo del piano)"
  echo
  awk -v h="## Task $N" '$0==h{f=1;next} /^## /{f=0} f' $W/carry.md
  if [ -n "$2" ]; then echo; awk '/^## Revisioni in parallelo/{f=1} f' $W/carry.md; fi
  echo
  cat $W/cautele.md
} > $W/task-$N-brief.md
rm -f "$P"
echo "$W/task-$N-brief.md"
