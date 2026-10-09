import unittest

from tollgate_analysis import bash

CWD = "/r/wt"


def cmds(text, cwd=CWD):
    return bash.parse(text, cwd)


def one(text):
    out = cmds(text)
    return out[-1]


class ParseTest(unittest.TestCase):
    def test_chain_and_cd(self):
        out = cmds("cd /r/main && git status; ls")
        self.assertEqual([c.argv[0] for c in out], ["cd", "git", "ls"])
        self.assertEqual(out[1].cwd, "/r/main")

    def test_git_c(self):
        c = one("git -C ../main commit -am x")
        self.assertEqual(bash.git_call(c)[0], "commit")
        self.assertEqual(bash.effective_dir(c), "/r/main")
        self.assertTrue(bash.commit_all(c))

    def test_redirects_and_env(self):
        c = one("FOO=1 echo x > src/a.py 2>&1")
        self.assertEqual(c.env, {"FOO": "1"})
        self.assertEqual(c.redirects, ["src/a.py"])
        self.assertEqual(bash.write_targets(c), ["src/a.py"])

    def test_heredoc_body_ignored(self):
        out = cmds("cat > notes.txt <<'EOF'\ngit push --force\nEOF\necho ok")
        self.assertEqual([c.argv[0] for c in out], ["cat", "echo"])
        self.assertEqual(out[0].redirects, ["notes.txt"])

    def test_nested_shell_and_substitution(self):
        out = cmds("bash -c 'git push origin main'")
        self.assertTrue(any(bash.is_push(c) and c.nested for c in out))
        out = cmds("echo $(gh pr create --fill)")
        self.assertTrue(any(bash.is_gh_pr_create(c) for c in out))

    def test_wrappers_stripped(self):
        self.assertEqual(one("env A=1 sudo git push").argv[:2], ["git", "push"])

    def test_unparsable_falls_back_to_text(self):
        # Un comando illeggibile solleva BashParseError: il chiamante ripiega sul testo.
        with self.assertRaises(bash.BashParseError):
            cmds("echo 'non chiuso")
        self.assertIsNotNone(bash.text_danger("echo 'x; git push --force"))
        self.assertIsNone(bash.text_danger("echo 'ciao"))
        # Heredoc senza delimitatore di chiusura, backslash finale, virgolette aperte.
        for text in ["cat <<EOF\ngit push --force\n", "echo a \\", 'echo "aperta git push']:
            with self.subTest(text=text):
                with self.assertRaises(bash.BashParseError):
                    cmds(text)
        self.assertEqual(bash.text_danger("cat <<EOF\ngit push --force\n"), "git push")

    def test_parsable_edge_cases_do_not_fall_back_silently(self):
        # Righe continuate con \ e $(...) annidati si leggono davvero, non sfuggono.
        self.assertTrue(bash.push_is_force(one("git push \\\n --force origin x")))
        out = cmds("echo $(echo $(git push --force origin x))")
        self.assertTrue(any(bash.push_is_force(c) for c in out))


class ParseCarryTest(unittest.TestCase):
    """Decisioni del controller in carry.md, sezione Task 7."""

    def test_c_flag_in_combined_shell_flags(self):
        for text in ["bash -lc 'git push origin main'", "sh -ec 'git push origin main'",
                     "bash -ic 'git push origin main'"]:
            with self.subTest(text=text):
                out = cmds(text)
                self.assertTrue(any(bash.is_push(c) and c.nested for c in out))

    def test_shell_without_c_is_not_a_command_string(self):
        out = cmds("bash script.sh git push")
        self.assertFalse(any(c.nested for c in out))

    def test_commit_n_is_no_verify(self):
        self.assertEqual(bash.destructive(one("git commit -n -m x")), "--no-verify")
        self.assertEqual(bash.destructive(one("git commit -nm x")), "--no-verify")
        self.assertIsNone(bash.destructive(one("git commit -am x")))

    def test_numbered_redirects_leave_no_spurious_argument(self):
        c = one("cp a b 2>&1")
        self.assertEqual(c.argv, ["cp", "a", "b"])
        self.assertEqual(bash.write_targets(c), ["b"])
        c = one("rm -rf build 2>/dev/null")
        self.assertEqual(c.argv, ["rm", "-rf", "build"])
        self.assertEqual(bash.rm_rf_targets(c), ["/r/wt/build"])
        c = one("echo hi 1>out.txt")
        self.assertEqual(c.argv, ["echo", "hi"])
        self.assertEqual(bash.write_targets(c), ["out.txt"])


class ClassifyTest(unittest.TestCase):
    def test_push(self):
        self.assertTrue(bash.push_is_force(one("git push -f origin tg/1-x")))
        self.assertTrue(bash.push_is_force(one("git push origin +tg/1-x")))
        self.assertEqual(bash.push_targets(one("git push origin HEAD:refs/heads/main")), ["main"])
        self.assertEqual(bash.push_targets(one("git push")), [])

    def test_branch_change(self):
        for text in ["git switch -c altro", "git checkout -B altro", "git branch -m nuovo",
                     "git switch main"]:
            with self.subTest(text=text):
                self.assertIsNotNone(bash.branch_change(one(text)))
        self.assertIsNone(bash.branch_change(one("git checkout -- src/a.py")))
        self.assertEqual(bash.checkout_args(one("git checkout altro")), ["altro"])

    def test_destructive(self):
        self.assertIsNotNone(bash.destructive(one("git reset --hard HEAD~1")))
        self.assertIsNotNone(bash.destructive(one("git commit --no-verify -m x")))
        self.assertEqual(bash.rm_rf_targets(one("rm -rf /tmp/x build")), ["/tmp/x", "/r/wt/build"])
        self.assertEqual(bash.rm_rf_targets(one("rm -r x")), [])

    def test_writes(self):
        self.assertEqual(bash.write_targets(one("sed -i 's/a/b/' src/a.py")), ["src/a.py"])
        self.assertEqual(bash.write_targets(one("cp a.txt dest/b.txt")), ["dest/b.txt"])
        self.assertEqual(bash.write_targets(one("echo x | tee -a out.txt")), ["out.txt"])
        self.assertTrue(bash.writes(one("git add -A")))
        self.assertFalse(bash.writes(one("git status")))

    def test_claude_and_tollgate(self):
        self.assertTrue(bash.is_claude(one("claude -p ciao")))
        self.assertTrue(bash.is_claude(one("npx @anthropic-ai/claude-code -p x")))
        self.assertTrue(bash.is_tollgate_hook(one("/p/bin/tollgate hook PreToolUse")))
        self.assertFalse(bash.is_tollgate_hook(one("/p/bin/tollgate verify")))

    def test_worktree_merge_branch_delete(self):
        self.assertEqual(bash.worktree_op(one("git worktree add ../x -b tg/2-y")),
                         ("add", "/r/x", "tg/2-y"))
        self.assertEqual(bash.worktree_op(one("git worktree remove ../x")), ("remove", "/r/x", None))
        self.assertEqual(bash.merge_args(one("git merge --no-ff tg/1-x")), ["tg/1-x"])
        self.assertEqual(bash.branch_deletes(one("git branch -D tg/1-x")), ["tg/1-x"])


class EffectsTest(unittest.TestCase):
    CFG = bash.EffectsCfg(commands=["make prod*"], project_scripts=["deploy"],
                          allow=["kubectl get *"])

    def eff(self, text):
        return bash.effect_reason(one(text), self.CFG)

    def test_effects(self):
        for text in ["ssh host ls", "docker push img", "terraform apply", "npm publish",
                     "curl -X POST https://x", "curl -d a=1 https://x", "wget --post-data=a https://x",
                     "gh pr edit 3 --title x", "gh api -X PATCH repos/o/r", "gh api repos/o/r -f a=b",
                     "gh api graphql -f query='mutation { x }'", "gh issue create -t x",
                     "npm run deploy", "make production", "supabase db push",
                     "wrangler deploy", "gh release create v1"]:
            with self.subTest(text=text):
                self.assertIsNotNone(self.eff(text))

    def test_not_effects(self):
        for text in ["curl https://x", "gh pr view 3", "gh api repos/o/r",
                     "gh api graphql -f query='query { x }'", "kubectl get pods", "npm test",
                     "git push", "supabase status"]:
            with self.subTest(text=text):
                self.assertIsNone(self.eff(text))

    def test_script_path(self):
        self.assertEqual(bash.script_path(one("./scripts/x.sh a")), "/r/wt/scripts/x.sh")
        self.assertEqual(bash.script_path(one("python3 tools/y.py")), "/r/wt/tools/y.py")
        self.assertIsNone(bash.script_path(one("python3 -m pytest")))
        self.assertIsNone(bash.script_path(one("ls -la")))


def pushes_forced(text):
    return [c for c in cmds(text) if bash.push_is_force(c)]


class FixRound1Test(unittest.TestCase):
    """Giro di correzione 1 del controller."""

    COMMIT_HEREDOC = "git commit -m \"$(cat <<'EOF'\nmsg\nEOF\n)\""

    def test_commit_with_heredoc_in_substitution_parses(self):
        out = cmds(self.COMMIT_HEREDOC)
        self.assertTrue(any(bash.is_commit(c) for c in out))

    def test_commit_heredoc_then_forced_push_is_seen(self):
        out = cmds(self.COMMIT_HEREDOC + " && git push --force")
        pushes = [c for c in out if bash.push_is_force(c)]
        self.assertTrue(pushes)
        self.assertFalse(pushes[0].nested)
        self.assertTrue(any(bash.is_commit(c) for c in out))

    def test_quoted_heredoc_body_is_data_not_command(self):
        out = cmds("cat <<'EOF'\n$(git push -f origin x)\nEOF\necho ok")
        self.assertFalse(any(bash.push_is_force(c) for c in out))
        self.assertEqual([c.argv[0] for c in out], ["cat", "echo"])

    def test_punctuation_tokens_are_split(self):
        for text in ["(true);git push -f", "true&&(git push -f)", "true;(git push -f)",
                     "(git status)&&git push -f", "echo $(date); git push -f",
                     "echo $(date)&& git push -f", "echo $(( 1 + 2 )); git push -f"]:
            with self.subTest(text=text):
                self.assertTrue(pushes_forced(text))

    def test_wrapper_options_with_argument(self):
        for text in ["sudo -u bob git push -f", "env -u X git push -f", "env -C /d git push -f"]:
            with self.subTest(text=text):
                c = one(text)
                self.assertEqual(c.argv[:2], ["git", "push"])
                self.assertTrue(bash.push_is_force(c))

    def test_leading_keywords_are_dropped(self):
        for text in ["if true; then git push -f; fi", "for i in a; do git push -f; done",
                     "{ git push -f; }", "! git push -f"]:
            with self.subTest(text=text):
                self.assertTrue(pushes_forced(text))

    def test_short_flag_cluster_contains_f(self):
        self.assertTrue(bash.push_is_force(one("git push -fu origin x")))
        self.assertTrue(bash.push_is_force(one("git push -uf origin x")))
        self.assertFalse(bash.push_is_force(one("git push -u origin x")))

    def test_gh_and_curl_flags(self):
        for text in ["gh api -XPOST x", "gh api x -XDELETE", "curl --request=POST u",
                     "gh -R o/r pr create", "gh --repo o/r pr merge"]:
            with self.subTest(text=text):
                self.assertIsNotNone(bash.effect_reason(one(text), bash.EffectsCfg()))
        self.assertIsNone(bash.effect_reason(one("gh -R o/r pr view 3"), bash.EffectsCfg()))

    def test_shell_receiving_heredoc_falls_back(self):
        for text in ["bash <<EOF\ngit push -f\nEOF", "cat <<EOF | bash\ngit push -f\nEOF"]:
            with self.subTest(text=text):
                with self.assertRaises(bash.BashParseError):
                    cmds(text)
                self.assertEqual(bash.text_danger(text), "git push")

    def test_text_danger_options_between(self):
        self.assertEqual(bash.text_danger("git reset -q --hard"), "reset --hard")
        self.assertIsNotNone(bash.text_danger("git commit -an -m x"))
        self.assertIsNotNone(bash.text_danger("git commit -n -m x"))

    def test_write_targets_perl_and_cp_target_dir(self):
        self.assertEqual(bash.write_targets(one("perl -pi -e 's/a/b/' f")), ["f"])
        self.assertEqual(bash.write_targets(one("sed -i -e 's/a/b/' f")), ["f"])
        self.assertEqual(bash.write_targets(one("cp -t dir a b")), ["dir"])

    def test_extra_mutating_git_subcommands(self):
        for text in ["git update-ref refs/x abc", "git config user.name x", "git remote add o u",
                     "git filter-branch --all", "git symbolic-ref HEAD refs/heads/x",
                     "git submodule update", "git gc"]:
            with self.subTest(text=text):
                self.assertTrue(bash.writes(one(text)))
        for text in ["git config --get user.name", "git config --list", "git status"]:
            with self.subTest(text=text):
                self.assertFalse(bash.writes(one(text)))

    def test_listing_forms_are_not_writes(self):
        for text in ["git branch", "git branch -a", "git branch -vv", "git branch --list 'tg/*'",
                     "git worktree list", "git stash list", "git tag", "git tag -l 'v*'",
                     "git remote -v", "git remote show origin", "git submodule status"]:
            with self.subTest(text=text):
                self.assertFalse(bash.writes(one(text)))
        for text in ["git branch nuovo", "git branch -D x", "git branch -m a b", "git tag v1",
                     "git tag -d v1", "git worktree add ../x", "git stash", "git stash pop",
                     "git remote add o u", "git remote remove o"]:
            with self.subTest(text=text):
                self.assertTrue(bash.writes(one(text)))

    def test_git_config_write_target(self):
        self.assertEqual(bash.git_config_write(one("git config core.hooksPath /x")), "local")
        self.assertEqual(bash.git_config_write(one("git config --unset user.name")), "local")
        self.assertEqual(bash.git_config_write(one("git -C ../r config a b")), "local")
        self.assertEqual(bash.git_config_write(one("git config --file /r/.git/config a b")),
                         "/r/.git/config")
        self.assertEqual(bash.git_config_write(one("git config --file=/x/c a b")), "/x/c")
        for text in ("git config --global a b", "git config --system a b", "git config --get a",
                     "git config --list", "git config -l", "git status"):
            with self.subTest(text=text):
                self.assertIsNone(bash.git_config_write(one(text)))
        self.assertTrue(bash.git_mutating(one("git config a b")))
        self.assertFalse(bash.git_mutating(one("echo x > f")))

    def test_command_patterns_cross_slash_and_allow_applies(self):
        cfg = bash.EffectsCfg(commands=["./scripts/deploy.sh *"])
        self.assertIsNotNone(bash.effect_reason(one("./scripts/deploy.sh a"), cfg))
        cfg = bash.EffectsCfg(commands=["deploy https://h/*"], allow=["deploy https://h/ok*"])
        self.assertIsNone(bash.effect_reason(one("deploy https://h/ok1"), cfg))
        self.assertIsNotNone(bash.effect_reason(one("deploy https://h/x"), cfg))
        cfg = bash.EffectsCfg(allow=["kubectl get *"])
        self.assertIsNone(bash.effect_reason(one("kubectl get pods/x"), cfg))


class FixRound2Test(unittest.TestCase):
    """Giro di correzione 2 del controller."""

    def test_assignment_with_substitution_keeps_command(self):
        for text in ["X=$(cmd) git push -f", "TOKEN=$(cat f) git push -f",
                     "A=1 B=$(x) git push -f"]:
            with self.subTest(text=text):
                pushes = pushes_forced(text)
                self.assertTrue(pushes)
                self.assertEqual(pushes[0].argv, ["git", "push", "-f"])

    def test_redirect_after_semicolon_is_not_a_command(self):
        out = cmds("true;>f")
        self.assertEqual([c.argv for c in out if c.argv], [["true"]])
        self.assertTrue(any(bash.write_targets(c) == ["f"] for c in out))

    def test_subshell_then_redirect_targets_log(self):
        out = cmds("(git push -f)>log")
        self.assertTrue(any(bash.push_is_force(c) for c in out))
        self.assertTrue(any(bash.write_targets(c) == ["log"] for c in out))

    def test_time_is_a_wrapper_with_p_flag(self):
        c = one("time -p git push -f")
        self.assertEqual(c.argv[:2], ["git", "push"])
        self.assertTrue(bash.push_is_force(c))

    def test_unquoted_heredoc_body_substitutions_run(self):
        for text in ["cat <<EOF\n$(git push -f)\nEOF", "cat <<EOF\n`git push -f`\nEOF"]:
            with self.subTest(text=text):
                self.assertTrue(pushes_forced(text))

    def test_quoted_heredoc_body_substitutions_are_data(self):
        for text in ["cat <<'EOF'\n$(git push -f)\nEOF", 'cat <<"EOF"\n$(git push -f)\nEOF']:
            with self.subTest(text=text):
                self.assertFalse(pushes_forced(text))


if __name__ == "__main__":
    unittest.main()
