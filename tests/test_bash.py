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

    def test_git_push_behind_env_loader_unchanged(self):
        # Limite scritto (spec 8.5): i controlli su `argv[0]` non vedono dietro un involucro.
        for text in ["dotenv -- git push", "dotenv -- git push --force origin x"]:
            with self.subTest(text=text):
                self.assertEqual([c for c in cmds(text) if bash.is_push(c)], [])
                self.assertEqual([c for c in cmds(text) if bash.push_is_force(c)], [])
                self.assertIsNone(bash.effect_reason(one(text), bash.EffectsCfg()))
        self.assertIsNone(bash.destructive(one("dotenv -- rm -rf /tmp/x")))
        self.assertEqual(bash.rm_rf_targets(one("dotenv -- rm -rf /tmp/x")), [])


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

    def check_effects(self, texts, expected):
        for text in texts:
            with self.subTest(text=text):
                got = self.eff(text)
                self.assertTrue((got is not None) == expected, f"{text!r}: {got!r}")

    def test_launcher_wrapped_effects(self):
        self.check_effects([
            "npx wrangler deploy", "npx --yes wrangler deploy", "npx -y wrangler@3 deploy",
            "npx --package=wrangler wrangler deploy", "npx -p wrangler wrangler deploy",
            "npx --registry https://r.invalid wrangler deploy", "npx --strano x wrangler deploy",
            "bunx wrangler deploy", "pnpx vercel --prod", "pnpm dlx vercel deploy",
            "pnpm exec wrangler deploy", "pnpm wrangler deploy", "pnpm -w wrangler deploy",
            "pnpm --filter web exec wrangler deploy", "pnpm -C infra wrangler deploy",
            "yarn wrangler deploy", "yarn workspace web wrangler deploy",
            "npm exec -- wrangler deploy", "npm --prefix x exec wrangler deploy",
            "npm x wrangler deploy", "bun x wrangler deploy", "bun run wrangler deploy",
            "yarn dlx vercel", "yarn exec wrangler publish", "npx vercel@latest build",
            "npx @cloudflare/wrangler@3 deploy", "npx pnpm dlx wrangler deploy",
            "pnpm --filter docs exec wrangler deploy", "pnpm -C docs wrangler deploy",
            "yarn workspace docs wrangler deploy"], True)

    def test_launcher_call_text_effects(self):
        self.check_effects([
            'npx -c "wrangler deploy"', 'npx -c "npx wrangler@3 deploy"',
            "npx -c \"wrangler deploy; echo 'x\"", 'npx --call "vercel --prod"',
            'npx --call="wrangler secret put K"', "npx --call=vercel",
            "npm exec --call=vercel"], True)
        self.check_effects(['npx -c "eslint ."'], False)

    def test_launcher_supabase_and_package_names(self):
        self.check_effects(["npx supabase db push", "npx firebase-tools deploy",
                            "npx netlify-cli deploy"], True)
        self.check_effects(["npx supabase status", "npx supabase migration list"], False)

    def test_launcher_local_service_commands_ask(self):
        self.check_effects(["npx vercel dev", "npx vercel --version",
                            "npx vitest run vercel"], True)

    def test_launcher_supabase_local_commands_pass(self):
        self.check_effects(["npx supabase migration new x", "npx supabase functions serve",
                            "pnpm exec supabase start", "bunx supabase db reset"], False)

    def test_launcher_double_dash_before_service_args(self):
        # Il `--` dopo il programma separa gli argomenti del lanciatore: non conta per il programma.
        self.check_effects([
            "npm exec prisma -- migrate deploy", "npx prisma -- migrate deploy",
            "pnpm exec prisma -- migrate deploy", "npm run prisma -- migrate deploy",
            "npm exec drizzle-kit -- push", "npx drizzle-kit -- push",
            "npm exec wrangler -- deploy", "npm exec wrangler -- d1 execute DB --remote"], True)
        self.check_effects(["npm exec supabase -- start"], False)
        self.check_effects(["supabase -- db push"], True)
        self.check_effects(["npm exec prisma -- -- migrate deploy",
                            "npx prisma -- -- -- migrate deploy"], True)
        self.assertEqual(bash.launcher_candidates(["npm", "exec", "prisma", "--", "migrate"]),
                         [["prisma", "migrate"]])

    def test_launcher_word_supabase_as_argument(self):
        # Costo noto (decisione 6): un'opzione dopo `supabase` e' sconosciuta e chiede.
        self.check_effects(["npx eslint supabase --fix"], True)
        self.check_effects(["npx eslint supabase", "npx tsc -p supabase"], False)

    SUPA_LOCAL = ["supabase init", "supabase start", "supabase migration new x",
                  "supabase functions new f", "supabase functions serve", "supabase db reset",
                  "supabase db lint", "supabase db diff -f x", "supabase gen types typescript",
                  "supabase test db", "supabase inspect db bloat", "supabase db push --help",
                  "supabase stop", "supabase status", "supabase db start", "supabase services",
                  "supabase help", "supabase completion bash", "supabase test new x",
                  "supabase gen signing-key", "supabase gen bearer-jwt", "supabase --version",
                  "supabase db query 'select 1'", "supabase db advisors", "supabase db dump",
                  "supabase migration list", "supabase migration squash", "supabase seed buckets",
                  "supabase inspect report", "supabase", "supabase --debug"]

    def test_supabase_local_commands_pass(self):
        for prefix in ("", "npx ", "pnpm exec ", "bunx "):
            self.check_effects([prefix + t for t in self.SUPA_LOCAL], False)

    def test_supabase_remote_flag_asks(self):
        base = ["db reset", "db lint", "db query 'select 1'", "db advisors", "db diff",
                "db dump", "migration list", "migration squash", "gen types typescript",
                "test db", "inspect db bloat", "inspect report", "seed buckets"]
        flags = ["--remote", "--remote=abc", "--linked", "--db-url postgres://x",
                 "--project-ref x", "--project-id x"]
        self.check_effects([f"supabase {b} {f}" for b in base for f in flags], True)
        self.check_effects(["supabase gen types typescript --project-id x",
                            "supabase inspect db bloat --remote",
                            "npx supabase db diff --linked"], True)
        # pflag non conosce il `false` di yargs: l'opzione c'e', il comando va sul servizio.
        self.check_effects(["supabase db reset --linked false", "supabase db reset --remote false",
                            "supabase db reset --remote=false", "supabase db dump --linked false",
                            "supabase db reset --linked=false"], True)

    def test_supabase_unknown_group_asks(self):
        self.check_effects([
            "supabase postgres-config update", "supabase network-restrictions update",
            "supabase ssl-enforcement update", "supabase domains activate", "supabase sso add",
            "supabase pull", "npx supabase postgres-config update", "npx supabase sso add",
            "pnpm exec supabase pull", "supabase network-bans remove", "supabase encryption x",
            "supabase vanity-subdomains activate", "supabase nuovo-gruppo x"], True)

    def test_supabase_unless_local(self):
        base = ["db push", "db pull", "migration up", "migration down",
                "migration repair --status applied 1", "migration fetch"]
        self.check_effects([f"supabase {b}" for b in base], True)
        self.check_effects([f"npx supabase {b}" for b in base], True)
        self.check_effects([f"supabase {b} --local" for b in base], False)
        self.check_effects([f"supabase {b} --local=true" for b in base], False)
        self.check_effects([f"supabase {b} --local --remote" for b in base], True)
        self.check_effects([f"supabase {b} --local --linked" for b in base], True)
        self.check_effects([f"supabase {b} --local=false" for b in base], True)
        self.check_effects([f"supabase {b} --local --db-url postgres://x" for b in base], True)
        self.check_effects(["supabase db push --local --project-ref x"], True)

    def test_supabase_always_asks(self):
        self.check_effects([
            "supabase functions deploy f", "supabase functions delete f",
            "supabase secrets set A=b", "supabase secrets unset A", "supabase link",
            "supabase config push", "supabase branches create", "supabase storage cp a b",
            "supabase functions deploy f --local", "supabase config push --local",
            "supabase unlink", "supabase bootstrap", "supabase storage ls", "supabase login",
            "supabase logout", "supabase branches get", "supabase projects create x",
            "supabase projects delete x", "supabase projects api-keys", "supabase orgs create",
            "supabase backups restore", "supabase snippets download x", "supabase config pull",
            "supabase config diff", "supabase whoami", "npx supabase functions deploy f"], True)

    def test_supabase_reads_pass(self):
        self.check_effects([
            "supabase functions download f", "supabase functions list", "supabase secrets list",
            "supabase migration list", "supabase projects list", "supabase branches list",
            "supabase orgs list", "supabase snippets list", "npx supabase functions list",
            "supabase secrets list --workdir x"], False)
        self.check_effects(["supabase branches get"], True)

    def test_supabase_global_option_before_subcommand(self):
        self.check_effects(["supabase --debug db push", "supabase --workdir x db push",
                            "supabase --workdir=x db push", "supabase --sconosciuta db reset",
                            "supabase -o json db push", "npx supabase --debug db push",
                            "supabase --yes db push", "supabase --experimental functions deploy f",
                            "supabase --agent no db pull", "supabase --profile p db push",
                            "supabase --dns-resolver native db push",
                            "supabase --network-id n db push",
                            "supabase --output-format x db push",
                            "supabase --workdir x --debug db push", "supabase -x db reset"], True)
        self.check_effects(["supabase --debug migration new x", "supabase -o json migration list",
                            "supabase --workdir x db reset", "supabase --output=json status",
                            "supabase --workdir=x --debug functions serve",
                            "npx supabase --debug start"], False)

    def test_supabase_help_only_outside_option_values(self):
        self.check_effects(["supabase --workdir --help db push --db-url postgres://x",
                            "supabase --profile -h db push --linked",
                            "supabase db push -- --help",
                            "supabase db push --linked -- --help"], True)
        self.check_effects(["supabase db push --help", "supabase -h", "supabase --help",
                            "supabase functions deploy -h", "supabase --debug db push --help",
                            "supabase db push --linked --help"], False)

    def test_supabase_reason_names_command(self):
        self.assertIn("supabase db push", self.eff("supabase db push"))
        self.assertIn("supabase functions deploy", self.eff("supabase functions deploy f"))
        self.assertIn("supabase", self.eff("supabase postgres-config update"))
        self.assertIn("--linked", self.eff("supabase db reset --linked"))
        self.assertIn("supabase", self.eff("supabase --sconosciuta db reset"))

    def test_supabase_tables(self):
        self.assertNotIn(("login",), bash.SUPABASE_LOCAL)
        self.assertNotIn(("logout",), bash.SUPABASE_LOCAL)
        self.assertNotIn(("snippets", "download"), bash.SUPABASE_READS)
        self.assertNotIn(("branches", "get"), bash.SUPABASE_READS)
        self.assertEqual(bash.REMOTE_FLAGS["wrangler"], ("--remote", "--preview"))

    def test_supabase_local_flag_hidden_as_option_value_asks(self):
        base = ["db push", "db pull", "migration up", "migration down",
                "migration repair --status applied 1", "migration fetch"]
        for opt in ("--network-id", "--profile", "--output-format", "-o", "--output",
                    "--agent", "--dns-resolver", "--workdir"):
            self.check_effects([f"supabase {b} {opt} --local" for b in base], True)
        self.check_effects(["supabase db push --network-id=x --local",
                            "supabase db push --network-id n --local",
                            "supabase db push --local --profile p",
                            "supabase db pull -o json --local",
                            "supabase --workdir x db push --local"], False)

    def test_supabase_local_value_only_when_true(self):
        for value in ("true", "1", "t", "T", "TRUE", "True"):
            self.check_effects([f"supabase db push --local={value}"], False)
        for value in ("0", "false", "f", "False", "FALSE", "F", "x", ""):
            self.check_effects([f"supabase db push --local={value}",
                                f"supabase db pull --local={value}"], True)

    def test_wrangler_flag_semantics_unchanged(self):
        self.check_effects(["wrangler kv key put K V --local --remote"], True)
        self.check_effects(["wrangler kv key put K V --local=0",
                            "wrangler d1 execute DB --remote=false --file x",
                            "wrangler d1 execute DB --remote false --file x",
                            "wrangler kv key put K V --local=true"], False)

    PRISMA_DRIZZLE_ASK = [
        "prisma migrate dev", "prisma migrate deploy", "prisma migrate reset",
        "prisma migrate resolve --applied x", "prisma db push", "prisma db execute --file x",
        "prisma db seed", "prisma studio", "prisma db init", "prisma db update",
        "prisma db migrate", "prisma db sign", "drizzle-kit push", "drizzle-kit migrate",
        "drizzle-kit studio", "drizzle-kit push:pg", "drizzle-kit push:mysql",
        "drizzle-kit push:sqlite", "drizzle-kit push --config x.ts"]
    PRISMA_DRIZZLE_PASS = [
        "prisma generate", "prisma format", "prisma validate", "prisma init", "prisma version",
        "prisma debug", "prisma db pull", "prisma migrate status", "prisma migrate diff",
        "prisma db verify", "drizzle-kit generate", "drizzle-kit check", "drizzle-kit pull",
        "drizzle-kit introspect", "drizzle-kit up", "drizzle-kit export"]

    def test_prisma_drizzle_writes_ask(self):
        self.check_effects(self.PRISMA_DRIZZLE_ASK, True)
        self.check_effects(["npx " + t for t in self.PRISMA_DRIZZLE_ASK], True)
        self.check_effects(["pnpm exec prisma migrate dev", "bunx drizzle-kit push",
                            "npx prisma@5 migrate dev", "yarn prisma db push",
                            "pnpm dlx drizzle-kit migrate"], True)

    def test_prisma_drizzle_no_db_pass(self):
        self.check_effects(self.PRISMA_DRIZZLE_PASS, False)
        self.check_effects(["npx " + t for t in self.PRISMA_DRIZZLE_PASS], False)
        self.check_effects(["pnpm add prisma", "npm install drizzle-kit"], False)

    def test_text_effect_supabase_lists(self):
        for text in ("x; supabase migration new x", "x; supabase functions list",
                     "x; supabase status", "x; supabase db reset", "x; supabase gen types ts",
                     "x; supabase snippets list", "x; supabase inspect db bloat"):
            with self.subTest(text=text):
                self.assertIsNone(bash.text_effect(text))
        for text in ("echo 'a; supabase db push", "echo 'a; supabase --debug migration new x",
                     "echo 'a; supabase nuovo-gruppo x", "echo 'a; supabase db reset --linked",
                     "echo 'a; supabase gen types --db-url x", "echo 'a; supabase login",
                     "echo 'a; supabase functions deploy f", "echo 'a; supabase db pull --local",
                     "echo 'a; supabase migration list --remote", "echo 'a; supabase pull",
                     "echo 'a; npx supabase db push", "echo 'a; supabase branches get",
                     "echo 'a; supabase test db --project-ref x"):
            with self.subTest(text=text):
                self.assertIsNotNone(bash.text_effect(text))

    def test_text_effect_prisma_drizzle(self):
        self.assertIsNotNone(bash.text_effect("echo 'a; prisma migrate dev"))
        self.assertIsNotNone(bash.text_effect("echo 'a; npx drizzle-kit push:pg"))
        self.assertIsNone(bash.text_effect("echo 'a; prisma generate"))

    def test_wrangler_new_entries_in_config(self):
        cfg = bash.EffectsCfg(allow=["wrangler kv key put K V --local"],
                              commands=["wrangler r2 bucket *", "wrangler d1 create *",
                                        "wrangler kv key put *"])

        def reason(text):
            return bash.effect_reason(one(text), cfg)

        self.assertIn("[external_effects] commands", reason("wrangler r2 bucket list"))
        self.assertIn("[external_effects] commands", reason("wrangler d1 create DB"))
        self.assertIn("[external_effects] commands", reason("wrangler kv key put K2 V --local"))
        allow = bash.EffectsCfg(allow=["wrangler kv namespace create *",
                                       "wrangler r2 object put *", "wrangler d1 execute *"])
        for text in ("wrangler kv namespace create NS", "wrangler r2 object put b/k",
                     "wrangler d1 execute DB --remote"):
            with self.subTest(text=text):
                self.assertIsNone(bash.effect_reason(one(text), allow))
        self.assertIsNotNone(bash.effect_reason(one("wrangler kv key delete K"), allow))

    def test_text_effect_kv_namespace_and_remote_false(self):
        # Il ripiego testuale non legge i valori ne' distingue le letture: chiede (parte sicura).
        self.assertIsNotNone(bash.text_effect("x; wrangler kv:namespace create NS"))
        self.assertIsNotNone(bash.text_effect("x; wrangler kv:namespace list"))
        self.assertIsNotNone(bash.text_effect("x; wrangler d1 execute DB --remote=false --file y"))

    def test_launcher_without_effect_passes(self):
        self.check_effects([
            "npx prettier --write .", "npx tsc", "npm exec -- eslint .", "pnpm dlx create-vite",
            "pnpm install", "yarn add vercel", "npm install -g wrangler", "npm i vercel",
            "yarn workspace web add vercel", "pnpm -w add -D vercel",
            "pnpm --filter web add vercel", "npm -w web install vercel",
            "npx eslint infra/aws", "npx tsc -p infra/aws", "npm --prefix infra/aws run build",
            "npm run build --workspace=apps/vercel", "pnpm --filter ./apps/vercel build",
            "yarn workspace @acme/aws build", "pnpm --filter @acme/vercel build",
            "npx pnpm add vercel", "npx pnpm@8 add vercel", "npx npm install vercel",
            'npx jest -t "vercel headers"',
            'npm run commit -- -m "chore: update vercel config"',
            "npm search vercel", "npm explain vercel"], False)

    def test_wrangler_live_commands_are_effects(self):
        self.check_effects([
            "wrangler secret put KEY", "wrangler secret delete KEY", "wrangler secret bulk f",
            "wrangler rollback", "wrangler delete", "wrangler triggers deploy",
            "wrangler versions deploy", "wrangler pages deploy dist",
            "wrangler pages project create x", "wrangler pages project delete x",
            "wrangler pages deployment delete x", "wrangler pages secret put K",
            "wrangler pages secret bulk f", "wrangler pages secret delete K",
            "wrangler pages publish dist", "npx wrangler secret put KEY"], True)

    def test_wrangler_read_and_upload_are_not_effects(self):
        self.check_effects([
            "wrangler versions upload", "wrangler versions secret put KEY",
            "wrangler versions list", "wrangler versions view x", "wrangler secret list",
            "wrangler pages dev", "wrangler pages deployment list"], False)

    def test_docker_push_forms(self):
        self.check_effects(["docker image push img", "docker compose push", "docker-compose push"], True)

    def test_node_modules_bin_effect(self):
        self.check_effects(["./node_modules/.bin/wrangler deploy"], True)

    def test_allow_still_wins_with_launcher(self):
        cfg = bash.EffectsCfg(allow=["npx wrangler deploy --dry-run"])
        self.assertIsNone(bash.effect_reason(one("npx wrangler deploy --dry-run"), cfg))

    def test_npm_project_scripts_unchanged(self):
        self.assertEqual(self.eff("npm run deploy"), "script del progetto: deploy")

    def test_wrangler_data_writes_are_effects(self):
        self.check_effects([
            "wrangler kv key put K V", "wrangler kv key put K V --remote",
            "wrangler kv key put K V --preview", "wrangler kv key put K V --local --remote",
            "wrangler kv key put K V --local false",
            "wrangler kv key delete K --namespace-id x",
            "wrangler kv bulk put f.json --binding KV", "wrangler kv bulk delete f.json",
            "wrangler kv:key put --binding KV k v", "wrangler kv:bulk delete f.json",
            "wrangler kv:namespace create NS", "wrangler kv namespace create NS",
            "wrangler kv namespace delete --binding KV",
            "wrangler kv namespace rename a --new-name b",
            "wrangler r2 object put b/k --file x", "wrangler r2 object delete b/k --remote",
            "wrangler r2 object put b/k --file x --local=false",
            "wrangler r2 bucket create b", "wrangler r2 bucket create list",
            "wrangler r2 bucket delete b", "wrangler r2 bucket cors set b --file c.json",
            "wrangler r2 bucket lifecycle add b r", "wrangler r2 bucket domain add b --domain x",
            'wrangler d1 execute DB --remote --command "select 1"',
            "wrangler d1 execute DB --remote=true --file x.sql",
            "wrangler d1 execute DB --preview --file x.sql",
            "wrangler d1 migrations apply DB --remote",
            "wrangler d1 migrations apply DB --preview", "wrangler d1 create DB",
            "wrangler d1 delete DB", "wrangler d1 time-travel restore DB --timestamp t",
            "wrangler kv key put K V --local --remote=true",
            "wrangler kv key put K V --local --preview=true",
            "wrangler d1 execute DB --preview=true --file x",
            "wrangler d1 execute DB --remote true --file x",
            "wrangler kv key put K -- --local", "wrangler d1 execute DB --remote -- --local"],
            True)

    def test_wrangler_local_writes_pass(self):
        self.check_effects([
            "wrangler kv key put K V --local", "wrangler kv bulk put f.json --local=true",
            "wrangler kv:key put --binding KV k v --local",
            "wrangler r2 object put b/k --file x --local",
            'wrangler d1 execute DB --command "select 1"',
            "wrangler d1 execute DB --local --file x.sql",
            "wrangler d1 execute DB --remote=false --file x.sql",
            "wrangler d1 execute DB --remote false --file x.sql",
            "wrangler d1 migrations apply DB", "wrangler d1 migrations apply DB --local",
            "wrangler d1 migrations create DB init",
            "wrangler kv key put K V --local -- x"], False)

    def test_wrangler_data_reads_pass(self):
        self.check_effects([
            "wrangler kv key get K", "wrangler kv key list", "wrangler kv bulk get f.json",
            "wrangler kv namespace list", "wrangler kv:namespace list", "wrangler d1 list",
            "wrangler d1 info DB", "wrangler d1 export DB --output x.sql",
            "wrangler d1 migrations list DB", "wrangler d1 time-travel info DB",
            "wrangler r2 object get b/k", "wrangler r2 bucket list", "wrangler r2 bucket info b",
            "wrangler r2 bucket cors list b"], False)

    def test_flag_effects_behind_launchers(self):
        self.check_effects([
            "npx wrangler kv key put K V", "pnpm exec wrangler d1 execute DB --remote --file x.sql",
            'npx -c "wrangler r2 object delete b/k"', "npx wrangler r2 bucket create b"], True)
        self.check_effects(["npx wrangler kv key put K V --local",
                            "pnpm dlx wrangler d1 migrations apply DB"], False)

    def test_flag_effect_reason_names_prefix(self):
        self.assertIn("wrangler kv key put", self.eff("wrangler kv key put K V"))
        self.assertIn("--remote", self.eff("wrangler d1 execute DB --remote"))

    def test_text_effect_flag_entries(self):
        self.assertIsNotNone(bash.text_effect("x; wrangler kv key put K V --local"))
        self.assertIsNotNone(bash.text_effect("x; wrangler r2 bucket create b"))
        self.assertIsNotNone(bash.text_effect("x; wrangler d1 execute DB --remote --file y"))
        self.assertIsNone(bash.text_effect("x; wrangler d1 execute DB --file y"))

    def test_script_name(self):
        for text, expected in [
                ("npm -w web run deploy", "deploy"), ("npm run -w web deploy", "deploy"),
                ("pnpm --filter web deploy", "deploy"), ("yarn workspace web run deploy", "deploy"),
                ("yarn workspace web deploy", "deploy"), ("bun run --filter web deploy", "deploy"),
                ("npm run --workspace=web release", "release"),
                ("pnpm -w release", "release"), ("npm run-script deploy", "deploy"),
                ("npm -C web run deploy", "deploy"), ("npm --dir web run deploy", "deploy"),
                ("npm --prefix web run deploy", "deploy"), ("pnpm -C web deploy", "deploy"),
                ("pnpm --dir web run deploy", "deploy"),
                ("yarn workspace deploy build", "build"), ("npm --prefix deploy run build", "build"),
                ("pnpm -C deploy build", "build"), ("pnpm --dir release build", "build"),
                ("pnpm vitest run deploy", "vitest"), ("npm exec vitest run release", "exec")]:
            with self.subTest(text=text):
                self.assertEqual(bash.script_name(one(text).argv), expected)

    def test_monorepo_deploy_scripts(self):
        cfg = bash.EffectsCfg(project_scripts=["deploy", "release"])

        def reason(text):
            return bash.effect_reason(one(text), cfg)

        for text in ["npm -w web run deploy", "npm run -w web deploy",
                     "npm --workspace=web run release", "npm run --workspace=web release",
                     "pnpm -F web run deploy", "pnpm --filter web run deploy",
                     "pnpm run --filter web deploy", "pnpm -F web deploy",
                     "yarn workspace web run deploy", "yarn workspace web deploy",
                     "bun --filter web run deploy", "bun run --filter web deploy",
                     "pnpm -w release", "npm run-script deploy", "npm -C web run deploy",
                     "npm --dir web run deploy", "npm --prefix web run deploy",
                     "pnpm --dir web run deploy"]:
            with self.subTest(text=text):
                self.assertIsNotNone(reason(text))
        for text in ["npm -w web run build", "yarn workspace web build",
                     "pnpm vitest run deploy", "npm exec vitest run release",
                     "yarn vitest run deploy", "yarn workspace deploy build",
                     "npm --prefix deploy run build", "pnpm -C deploy build",
                     "pnpm --dir release build"]:
            with self.subTest(text=text):
                self.assertIsNone(reason(text))

    def test_commands_config_matches_launcher_text(self):
        cfg = bash.EffectsCfg(commands=["npx mytool"])
        self.assertIsNotNone(bash.effect_reason(one("npx mytool run"), cfg))

    def test_curl_and_gh_stay_on_original_argv(self):
        self.check_effects(["npx curl https://x.invalid", "npx gh pr list"], False)

    # --- involucri dell'ambiente (B8, decisione 1) ----------------------------------------------

    REL = bash.EffectsCfg(project_scripts=["deploy", "release"])

    def eff_rel(self, text):
        return bash.effect_reason(one(text), self.REL)

    def test_env_loaders_scan_for_effects(self):
        self.check_effects([
            "dotenv -e .env.production -- prisma migrate deploy",
            "dotenv -e .env.production -- npm run deploy",
            "cross-env NODE_ENV=production drizzle-kit push",
            "cross-env NODE_ENV=production prisma migrate deploy",
            "doppler run -- npx supabase db push",
            "doppler run --command 'prisma migrate deploy'",
            "doppler run --command='prisma migrate deploy'",
            "op run -- supabase db push",
            "infisical run --env=prod -- prisma db push",
            "dotenvx run -f .env -- prisma db push",
            "env-cmd -f .env prisma db push",
            "env-cmd -f .env /usr/local/bin/vercel --prod",
            "dotenv -- wrangler deploy", "dotenv -e .env -- npx supabase db push",
            "dotenv -- gh pr create", "dotenv -- make deploy",
            "npx dotenv -e .env -- prisma migrate deploy",
            "dotenv -e .env -- npx dotenv -- prisma migrate deploy"], True)

    def test_env_loaders_without_effect_pass(self):
        self.check_effects([
            "dotenv -- python3 -m unittest", "dotenv -- npm i -g vercel",
            "dotenv -- python3 manage.py check", "cross-env CI=1 python3 tools/build.py",
            "cross-env CI=1 python3 -m pytest tests/vercel", "dotenv -e .env -- npm test",
            "doppler run -c prd -- jest", "op run -- echo ok", "dotenv", "cross-env A=1",
            "infisical run -- npm test", "dotenvx run -- node server.js"], False)

    def test_env_loader_value_equal_to_program_asks(self):
        # Costo noto (decisione 1): un valore con il nome di un programma chiede, senza motivo.
        self.check_effects(["dotenv -e vercel -- echo x", "dotenv -e vercel echo x",
                            "cross-env vercel echo x", "cross-env NODE_ENV=test jest aws",
                            "doppler run --project supabase --config prd -- npm run dev"], True)

    def test_env_loader_inner_double_dash(self):
        # Il `--` e' del comando interno: il comando interno va guardato anche prima del `--`.
        for text in ["cross-env NODE_ENV=production npm run deploy -- --prod",
                     "env-cmd -f .env npm run release -- --tag x",
                     "dotenv -e .env.production npm run deploy -- --prod",
                     "cross-env NODE_ENV=production prisma migrate deploy -- --x"]:
            with self.subTest(text=text):
                self.assertIsNotNone(self.eff_rel(text))

    def test_env_loader_first_token_path(self):
        self.check_effects(["cross-env A=1 /usr/local/bin/vercel --prod"], True)

    def test_env_loader_allow_on_outer_text(self):
        cfg = bash.EffectsCfg(allow=["dotenv -e .env -- prisma migrate deploy"])
        self.assertIsNone(bash.effect_reason(
            one("dotenv -e .env -- prisma migrate deploy"), cfg))
        self.assertIsNotNone(bash.effect_reason(
            one("dotenv -e .env2 -- prisma migrate deploy"), cfg))
        cfg = bash.EffectsCfg(commands=["dotenv -e .env*"])
        self.assertIn("[external_effects] commands",
                      bash.effect_reason(one("dotenv -e .env -- jest"), cfg))

    def test_env_loader_nesting_depth(self):
        self.check_effects(["dotenv -- doppler run -- prisma migrate deploy",
                            "dotenv -- doppler run -- cross-env A=1 echo ok",
                            "dotenv -- doppler run -- op run -- echo ok"], True)
        self.check_effects(["dotenv -- doppler run -- echo ok"], False)

    def test_env_loader_inner_command_is_parsed(self):
        self.check_effects([
            "dotenv -- bash -c 'prisma migrate deploy'",
            "dotenv -- sh -c 'curl -X POST https://x'", "dotenv -- env X=1 prisma migrate deploy",
            "dotenv -- sudo prisma migrate deploy", "dotenv -- timeout 60 supabase db push",
            "dotenv -- FOO=1 prisma migrate deploy", "dotenv -- time npm run deploy",
            "dotenv -- curl -X POST https://x", "dotenv -- eval 'prisma db push'"], True)
        self.check_effects(["dotenv -- env X=1 echo ok", "dotenv -- bash -c 'echo ok'"], False)

    def test_env_loader_inner_command_in_one_word(self):
        self.check_effects(['dotenv -- "supabase db push"', 'op run -- "prisma migrate deploy"',
                            'npx dotenv -- "npm run deploy"',
                            # Costo noto, dalla parte sicura: una parola con spazi si legge anche
                            # a pezzi, quindi il filtro dei test chiede.
                            'dotenv -- jest -t "vercel deploy"'], True)
        self.check_effects(['dotenv -- "python3 -m unittest"'], False)

    def test_env_loader_behind_launcher(self):
        for text in ["npx dotenv -e .env -- npm run release",
                     "npx dotenv -- curl -X POST https://x",
                     "npx dotenv@16 -e .env -- npm run release",
                     "npx dotenv-cli -e .env -- npm run release",
                     "npx @dotenvx/dotenvx run -- npm run release",
                     "npx cross-env NODE_ENV=production npm run release",
                     "pnpm exec dotenv -- gh pr create"]:
            with self.subTest(text=text):
                self.assertIsNotNone(self.eff_rel(text))
        self.check_effects(["npm i -D cross-env vercel", "pnpm add -D dotenv vercel",
                            "npx dotenv -- echo ok"], False)
        # Nessuna pagina ufficiale per `@infisical/cli`: resta l'esito di oggi, dato dal
        # `prisma` dopo il `--`.
        self.check_effects(["npx @infisical/cli run -- prisma migrate deploy"], True)
        self.check_effects(["npx @infisical/cli run -- echo ok"], False)

    def test_env_loader_command_options(self):
        self.check_effects(["infisical run -c 'prisma migrate deploy'",
                            "infisical run --command 'prisma migrate deploy'",
                            "infisical run --command='prisma migrate deploy'",
                            "infisical sm run -- prisma migrate deploy",
                            "infisical secrets-manager run -- prisma migrate deploy"], True)
        self.check_effects(["doppler run -c prd -- jest", "doppler run --config prd -- jest",
                            "infisical run -e dev -- jest"], False)

    def test_env_loader_shell_forms(self):
        self.check_effects(["cross-env-shell \"prisma migrate deploy && echo ok\"",
                            "env-cmd -f .env --use-shell -- \"npm run build && supabase db push\"",
                            "cross-env-shell NODE_ENV=test \"jest && prisma db push\""], True)
        self.check_effects(["cross-env-shell \"jest && echo ok\"",
                            "env-cmd -f .env --use-shell -- \"jest && echo ok\""], False)

    def test_env_loader_shell_text_with_paths_and_assignments(self):
        # Una parola con spazi e' testo di shell: i filtri per token (percorsi, assegnazioni)
        # non la riguardano (revisione finale F1).
        self.check_effects([
            'cross-env-shell "cd apps/web && vercel deploy --prod"',
            'env-cmd --use-shell "cd apps/web && vercel deploy --prod"',
            'cross-env-shell "curl -X POST https://api.example.com"',
            'cross-env-shell "prisma migrate deploy --schema=db/schema.prisma"',
            'cross-env-shell "./scripts/build && vercel --prod"',
            'cross-env-shell "supabase db push --workdir ./supa"',
            'cross-env-shell "DEBUG=1 vercel --prod"',
            'env-cmd --use-shell "NODE_ENV=production prisma migrate deploy"'], True)
        self.check_effects(['cross-env-shell "jest && echo ok"',
                            "cross-env NODE_ENV=test jest src/aws"], False)

    def test_true_inner_commands_of_shell_text(self):
        got = [c.argv for c in bash.true_inner_commands(
            one('cross-env-shell "./deploy.sh && echo ok"'))]
        self.assertIn(["./deploy.sh"], got)

    def test_inner_commands_forms(self):
        def inner(text):
            return bash.inner_commands(one(text))

        def argvs(items):
            return [c.argv for c in items if isinstance(c, bash.Cmd)]

        self.assertEqual(bash.inner_commands(one("ls -la")), [])
        self.assertIn(["prisma", "migrate", "deploy"],
                      argvs(inner("dotenv -e .env -- prisma migrate deploy")))
        self.assertIn(["prisma", "migrate", "deploy"],
                      argvs(inner("dotenv -e .env prisma migrate deploy")))
        self.assertIn(["prisma", "migrate", "deploy"],
                      argvs(inner("doppler run --command 'prisma migrate deploy'")))
        self.assertIn(["prisma", "migrate", "deploy"],
                      argvs(inner("doppler run --command='prisma migrate deploy'")))
        # Un candidato che parse non legge arriva come testo e passa da text_effect.
        items = inner('dotenv -- bash -c "it\'s; curl -X POST https://x"')
        self.assertTrue(any(isinstance(c, str) and "curl" in c for c in items))
        self.check_effects(['dotenv -- bash -c "it\'s; curl -X POST https://x"'], True)

    def test_inner_commands_unreadable_without_reason_asks(self):
        self.check_effects(['dotenv -- bash -c "it\'s fine"'], True)

    def test_true_inner_commands(self):
        def true(text):
            return [c.argv for c in bash.true_inner_commands(one(text))]

        self.assertEqual(bash.true_inner_commands(one("ls -la")), [])
        self.assertIn(["node", "x.js"], true("dotenv -e .env -e .env.local node x.js"))
        self.assertIn(["node", "x.js"], true("dotenv --debug node x.js"))
        got = true("cross-env NODE_ENV=test c8 -r text node --test x")
        self.assertEqual(got, [["c8", "-r", "text", "node", "--test", "x"]])
        self.assertFalse(any(a[:2] == ["node", "--test"] for a in got))
        self.assertIn(["node", "x.js"], true("dotenv -e .env -- node x.js"))
        self.assertIn(["node", "x.js"], true("doppler run --command 'node x.js'"))
        self.assertIn(["node", "x.js"], true("infisical sm run -- node x.js"))
        self.assertIn(["node", "scripts/new.js"], true("dotenv --debug node scripts/new.js"))
        # Dietro un lanciatore e a ogni livello.
        self.assertIn(["./deploy.sh"], true("npx dotenv -- ./deploy.sh"))
        self.assertIn(["./deploy.sh"], true("dotenv -- doppler run -- ./deploy.sh"))
        self.assertIn(["./deploy"], true("cross-env A=1 ./deploy"))
        self.assertIn(["./scripts/env.sh", "jest"], true("env-cmd -f ./scripts/env.sh jest"))
        self.assertNotIn(["./test/.env", "mocha", "-R", "spec"],
                         true("env-cmd -f ./test/.env mocha -R spec"))
        self.assertEqual([], [a for a in true("cross-env A=1 scripts/deploy")
                              if a[0] == "scripts/deploy"])

    def test_env_loader_paths_not_scanned(self):
        self.check_effects([
            "cross-env NODE_ENV=test jest src/aws", "cross-env CI=1 python3 -m pytest tests/vercel",
            "env-cmd -f ./test/.env mocha -R spec", "env-cmd -f ./config/.env.test jest",
            "dotenv -e ./.env.test -- jest", "dotenv -e ./envs/.env.local -- next dev",
            "cross-env NODE_ENV=test mocha 'test/**/*.spec.js'",
            "cross-env NODE_ENV=test ava test/*.js", "cross-env NODE_ENV=test jest ./src/aws",
            "cross-env CI=1 pytest ./tests/vercel"], False)

    def test_env_loader_command_by_path(self):
        self.check_effects([
            "env-cmd -f .env /usr/local/bin/vercel --prod",
            "cross-env A=1 /usr/bin/curl -X POST https://x", "cross-env A=1 /usr/bin/gh pr create",
            "cross-env A=1 /bin/bash -c 'curl -X POST https://x'",
            "cross-env A=1 /usr/bin/make deploy",
            "cross-env A=1 ./node_modules/.bin/prisma migrate deploy",
            "cross-env A=1 node_modules/.bin/prisma migrate deploy"], True)
        # `./deploy` e `dotenv -e .env ./scripts/deploy.sh` sono file da guardare: li vede
        # `_script_reason` (tests/test_check_effects.py), non `effect_reason`.
        self.check_effects(["cross-env A=1 ./deploy", "dotenv -e .env ./scripts/deploy.sh"], False)
        # Un programma locale con il nome di un servizio passa (limite scritto, giro 7 m2).
        self.check_effects(["cross-env A=1 ./vercel --prod"], False)
        self.check_effects(["./vercel --prod"], True)

    # --- opzioni con valore dei sottocomandi di Supabase (B8, decisione 2) -----------------------

    def test_supabase_value_table_has_no_local_or_remote_flags(self):
        table = bash.SUPABASE_COMMAND_VALUE_OPTIONS
        for key, options in table.items():
            for opt in options:
                with self.subTest(key=key, opt=opt):
                    self.assertNotEqual(opt, "--local")
                    self.assertNotIn(opt, bash.REMOTE_FLAGS["supabase"])
        for prefix, _mode in bash.FLAG_EFFECTS:
            if prefix[0] == "supabase":
                with self.subTest(prefix=prefix):
                    self.assertIn(prefix[1:3], table)
        self.check_effects(["supabase db push --db-url postgres://prod --local"], True)

    def test_supabase_version_only_without_subcommand(self):
        self.check_effects(["supabase --version", "supabase --debug --version"], False)
        self.check_effects(["supabase db reset --linked --version 20240101"], True)

    def test_supabase_command_value_options(self):
        self.check_effects([
            "supabase db push -p --local", "supabase db push --password --local",
            "supabase db pull --schema --local", "supabase db pull -s --local",
            "supabase migration down --last --local",
            "supabase migration repair -p --local --status applied 1",
            "supabase db pull --diff-engine --local",
            "npx supabase db push -p --local", "pnpm exec supabase db pull -s --local",
            "npx supabase migration down --last --local"], True)
        self.check_effects([
            "supabase db push -p x --local", "supabase db push --password=x --local",
            "supabase migration repair --status applied 1 --local",
            "supabase db dump -f --linked", "supabase db dump --file out.sql",
            "npx supabase db push -p x --local",
            "supabase migration repair --status applied 1 --local"], False)

    def test_supabase_help_as_command_option_value_asks(self):
        self.check_effects(["supabase db push -p --help", "supabase db pull --schema -h"], True)
        self.check_effects(["supabase db push --help", "supabase db pull -h"], False)

    def test_text_effect_supabase_value_options_still_ask(self):
        self.assertIsNotNone(bash.text_effect("supabase db push -p x --local"))
        self.assertIsNotNone(bash.text_effect("supabase db push --password x --local"))

    def test_launcher_candidates(self):
        self.assertEqual(bash.launcher_candidates(["ls", "wrangler", "deploy"]), [])
        self.assertEqual(bash.launcher_candidates(["npx", "-y", "wrangler@3", "deploy"]),
                         [["wrangler", "deploy"]])
        self.assertEqual(bash.launcher_candidates(["npm", "exec", "prisma", "--", "--", "x"]),
                         [["prisma", "x"]])
        # Gli involucri non cambiano i candidati del lanciatore.
        self.assertEqual(bash.launcher_candidates(["npx", "dotenv", "--", "echo", "x"]), [])

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

    def test_mv_source_is_a_target(self):
        self.assertEqual(bash.write_targets(one("mv a b")), ["a", "b"])
        self.assertEqual(bash.write_targets(one("mv a b dir")), ["a", "b", "dir"])
        self.assertEqual(sorted(bash.write_targets(one("mv -t dir a b"))), ["a", "b", "dir"])
        self.assertEqual(sorted(bash.write_targets(one("mv --target-directory=dir a"))),
                         ["a", "dir"])
        self.assertEqual(bash.write_targets(one("cp a b")), ["b"])
        self.assertEqual(bash.write_targets(one("cp --remove-source-files a b")), ["a", "b"])
        self.assertEqual(bash.write_targets(one("cp -t dir a")), ["dir"])

    def test_removal_targets(self):
        self.assertEqual(bash.removal_targets(one("rm -rf a b")), ["a", "b"])
        self.assertEqual(bash.removal_targets(one("rmdir d")), ["d"])
        self.assertEqual(bash.removal_targets(one("mv a b dir")), ["a", "b"])
        self.assertEqual(sorted(bash.removal_targets(one("mv -t dir a b"))), ["a", "b"])
        self.assertEqual(bash.removal_targets(one("cp a b")), [])
        self.assertEqual(bash.removal_targets(one("touch a")), [])

    def test_other_removal_commands(self):
        self.assertEqual(bash.removal_targets(one("git rm -r a b")), ["a", "b"])
        self.assertEqual(bash.removal_targets(one("git rm --cached -- a")), ["a"])
        self.assertEqual(bash.removal_targets(one("unlink f")), ["f"])
        self.assertEqual(bash.removal_targets(one("find . -name '*.pyc' -delete")), ["."])
        self.assertEqual(bash.removal_targets(one("find a b -type f -delete")), ["a", "b"])
        self.assertEqual(bash.removal_targets(one("find -delete")), ["."])
        self.assertEqual(bash.removal_targets(one("find a -exec rm -rf {} +")), ["a"])
        self.assertEqual(bash.removal_targets(one("find a -execdir mv {} /t \\;")), ["a"])
        self.assertEqual(bash.removal_targets(one("find a -name x")), [])
        self.assertEqual(bash.removal_targets(one("find a -exec cat {} \\;")), [])
        self.assertEqual(bash.removal_targets(one("git status")), [])

    def test_removal_recursive(self):
        for text in ("rm -rf a", "rm -r a", "rm -R a", "rm --recursive a", "rmdir a",
                     "find a -delete", "git rm -r a"):
            with self.subTest(text=text):
                self.assertTrue(bash.removal_recursive(one(text)))
        for text in ("rm a", "rm -f a", "mv a b", "unlink a", "git rm a"):
            with self.subTest(text=text):
                self.assertFalse(bash.removal_recursive(one(text)))

    def test_compact_c_option_sets_hooks_path(self):
        self.assertTrue(bash.hooks_path_override(one("git -ccore.hooksPath=/tmp status")))
        self.assertFalse(bash.hooks_path_override(one("git -cuser.name=x status")))

    def test_force_if_includes_alone_is_not_force(self):
        self.assertFalse(bash.push_is_force(one("git push --force-if-includes origin x")))
        self.assertTrue(bash.push_is_force(one("git push --force --force-if-includes origin x")))
        self.assertTrue(bash.push_is_force(one("git push --force-with-lease origin x")))
        self.assertTrue(bash.push_is_force(one("git push -f --force-if-includes origin x")))
        self.assertTrue(bash.push_is_force(one("git push --force-with-lease "
                                               "--force-if-includes origin x")))

    def test_tag_listing_forms_are_reads(self):
        for text in ("git tag -n", "git tag -n5", "git tag --contains abc", "git tag --list",
                     "git tag -l", "git tag --merged main", "git tag --points-at HEAD",
                     "git tag -l 'v*'", "git tag --sort=-v:refname"):
            with self.subTest(text=text):
                self.assertFalse(bash.writes(one(text)))
        for text in ("git tag v1", "git tag -a v1 -m x", "git tag -d v1", "git tag -f v1",
                     "git tag --delete v1", "git tag -s v1"):
            with self.subTest(text=text):
                self.assertTrue(bash.writes(one(text)))

    def test_hooks_path_override(self):
        for text in ("git -c core.hooksPath=/x commit -m y", "git -c core.hookspath=/x status",
                     "git config core.hooksPath /x", "git config --global core.hooksPath /x",
                     "git config --system core.hooksPath /x", "git config --unset core.hooksPath",
                     "git config --file f core.hooksPath /x", "git --config-env=core.hooksPath=V st",
                     "GIT_CONFIG_KEY_0=core.hooksPath git status"):
            with self.subTest(text=text):
                self.assertTrue(bash.hooks_path_override(one(text)))
        for text in ("git config --get core.hooksPath", "git config user.name x",
                     "git -c user.name=x commit -m y", "git status", "echo core.hooksPath"):
            with self.subTest(text=text):
                self.assertFalse(bash.hooks_path_override(one(text)))

    def test_text_effect_fallback(self):
        for text in ("echo 'x; ssh host", "echo 'a && psql -c x", "echo 'a; npm  publish",
                     "echo 'a; gh pr create --fill", "echo 'a; curl -X POST http://x",
                     "echo 'a; curl -d x http://x", "echo 'a; docker push img",
                     "echo 'a; supabase db push", "echo 'a; gh pr merge 3",
                     "x; wrangler pages deploy dist"):
            with self.subTest(text=text):
                self.assertIsNotNone(bash.text_effect(text))
        for text in ("echo 'ciao", "echo 'a; sshd -t", "echo 'a; curl http://x",
                     "echo 'a; gh pr view 3", "echo 'a; cat essh"):
            with self.subTest(text=text):
                self.assertIsNone(bash.text_effect(text))

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


class AbbreviationAndAliasTest(unittest.TestCase):
    """I3 della revisione finale: git accetta il prefisso univoco di un'opzione lunga e gli
    alias definiti con `-c`; le regole di 7.4 devono vederli."""

    def test_abbreviated_force_options(self):
        for opt in ("--forc", "--for", "--force-w", "--force-with", "--force-with-lease=x",
                    "--mirro", "--mir", "--force-"):
            with self.subTest(opt=opt):
                self.assertTrue(bash.push_is_force(one(f"git push {opt} origin x")))

    def test_abbreviated_no_verify_and_hard(self):
        for opt in ("--no-verif", "--no-ver", "--no-v"):
            with self.subTest(opt=opt):
                self.assertEqual(bash.destructive(one(f"git commit {opt} -m x")), "--no-verify")
        for opt in ("--har", "--hard"):
            with self.subTest(opt=opt):
                self.assertEqual(bash.destructive(one(f"git reset {opt} HEAD~1")),
                                 "git reset --hard")

    def test_short_or_unrelated_options_are_not_dangerous(self):
        self.assertFalse(bash.push_is_force(one("git push --follow-tags origin x")))
        self.assertFalse(bash.push_is_force(one("git push --force-if-includes origin x")))
        self.assertFalse(bash.push_is_force(one("git push --fo origin x")))
        self.assertIsNone(bash.destructive(one("git commit --no-edit")))
        self.assertIsNone(bash.destructive(one("git reset --soft HEAD~1")))
        # dopo `--` ciò che segue è un percorso
        self.assertIsNone(bash.destructive(one("git checkout -- --har")))

    def test_alias_with_dash_c_replaces_the_subcommand(self):
        c = one("git -c alias.p=push p origin main")
        self.assertEqual(bash.git_call(c), ("push", ["origin", "main"], None))
        self.assertTrue(bash.is_push(c))
        self.assertEqual(bash.push_targets(c), ["main"])
        self.assertEqual(bash.branch_change(one("git -c alias.s=switch s main")), "git switch")
        self.assertTrue(bash.push_is_force(one("git -c 'alias.pf=push --force' pf origin x")))
        self.assertTrue(bash.push_is_force(one("git -calias.pf=push pf -f origin x")))
        self.assertEqual(bash.destructive(one("git -c alias.rh='reset --hard' rh")),
                         "git reset --hard")
        self.assertTrue(bash.is_push(one("git -c alias.a=b -c alias.b=push a origin x")))

    def test_alias_shadowing_a_builtin_is_ignored(self):
        # Git ignora gli alias che coprono un comando integrato: il push parte davvero.
        c = one("git -c alias.push=status push origin main")
        self.assertTrue(bash.is_push(c))
        self.assertEqual(bash.push_targets(c), ["main"])
        c = one("git -c alias.commit=status commit --no-verify -m x")
        self.assertEqual(bash.destructive(c), "--no-verify")
        c = one("git -c alias.reset=status reset --hard")
        self.assertEqual(bash.destructive(c), "git reset --hard")
        c = one("git -c alias.PUSH=status push origin main")
        self.assertTrue(bash.is_push(c))
        self.assertIsNone(bash.shell_alias_command(one("git -c 'alias.push=!echo' push")))
        self.assertTrue(bash.is_push(one("git -c alias.p=push p origin main")))

    def test_shell_alias_is_parsed_as_shell(self):
        out = cmds("git -c 'alias.p=!git push -f' p origin x")
        self.assertTrue(any(bash.push_is_force(c) and c.nested for c in out))
        out = cmds("git -c 'alias.z=!rm -rf /tmp/zz' z")
        self.assertTrue(any(bash.rm_rf_targets(c) for c in out))

    def test_non_alias_subcommands_are_untouched(self):
        self.assertEqual(bash.git_call(one("git -c user.name=x push origin main"))[0], "push")
        self.assertEqual(bash.git_call(one("git -c alias.p=push status"))[0], "status")


class GitRestoreTargetsTest(unittest.TestCase):
    """M2: checkout e restore riscrivono i file indicati."""

    def test_checkout_paths_after_double_dash(self):
        self.assertEqual(bash.write_targets(one("git checkout origin/main -- tollgate.toml a/b")),
                         ["tollgate.toml", "a/b"])
        self.assertEqual(bash.write_targets(one("git checkout -- src/a.py")), ["src/a.py"])
        self.assertEqual(bash.write_targets(one("git checkout altro")), [])

    def test_restore_positionals(self):
        self.assertEqual(bash.write_targets(one("git restore .tollgate/waivers/7.toml")),
                         [".tollgate/waivers/7.toml"])
        self.assertEqual(bash.write_targets(one("git restore --staged --source=HEAD~1 f g")),
                         ["f", "g"])
        self.assertEqual(bash.write_targets(one("git restore -s HEAD~1 -- f")), ["f"])
        self.assertEqual(bash.write_targets(one("git restore --source HEAD~1 f")), ["f"])


class TextDangerFallbackTest(unittest.TestCase):
    def test_new_patterns(self):
        for text, label in (("bash <<EOF\nrm -rf /tmp/x\n", "rm -r"),
                            ("bash <<EOF\nrm -fR /tmp/x\n", "rm -r"),
                            ("bash <<EOF\ngit -c core.hooksPath=/x commit\n", "core.hooksPath"),
                            ("bash <<EOF\ngit -c CORE.HOOKSPATH=/x commit\n", "core.hooksPath"),
                            ("bash <<EOF\necho x > tollgate.toml\n", "tollgate.toml"),
                            ("bash <<EOF\necho x > .tollgate/waivers/7.toml\n", ".tollgate/"),
                            ("bash <<EOF\necho {} > .claude/settings.json\n", "settings.json"),
                            ("bash <<EOF\necho {} > settings.local.json\n", "settings.json")):
            with self.subTest(text=text):
                self.assertEqual(bash.text_danger(text), label)
        self.assertIsNone(bash.text_danger("bash <<EOF\nls -la\n"))
        self.assertIsNone(bash.text_danger("bash <<EOF\nrm file.txt\n"))


class ScriptIndexTest(unittest.TestCase):
    def test_skips_interpreter_options(self):
        for argv, k in ((["python3", "s.py", "x"], 1), (["python3", "-B", "s.py"], 2),
                        (["python3.11", "-W", "error", "-B", "s.py"], 4),
                        (["python3", "-X", "dev", "s.py"], 3)):
            with self.subTest(argv=argv):
                self.assertEqual(bash.script_index(argv), k)

    def test_no_script(self):
        for argv in (["git", "status"], ["python3"], ["python3", "-B"],
                     ["python3", "-c", "print(1)"], ["python3", "-m", "http.server"], []):
            with self.subTest(argv=argv):
                self.assertIsNone(bash.script_index(argv))


class ReadTargetsTest(unittest.TestCase):
    def test_read_targets(self):
        for text, want in (("cat a b", ["a", "b"]), ("sed -n 1,20p f", ["f"]),
                           ("sed -i s/x/y/ f", []), ("grep -n foo src/a.py", ["src/a.py"]),
                           ("rg foo", []), ("head -n 5 f", ["f"]), ("wc -l f", []),
                           ("echo f", []), ("grep -A 3 foo f", ["f"]),
                           ("tail -n +3 f g", ["f", "g"]), ("head -c 10 -- f", ["f"]),
                           ("head -n5 f", ["f"]), ("head --lines 5 f", ["f"]),
                           ("grep -e foo -e bar f", ["f"]), ("grep -f pats f", ["f"]),
                           ("grep -rn foo src tests", ["src", "tests"]),
                           ("rg -g '*.py' foo src", ["src"]), ("rg -e foo a b", ["a", "b"]),
                           ("sed -n -e 1p f", ["f"]), ("sed -ne 1p f", ["f"]),
                           ("sed -n -f s.sed f", ["f"]), ("sed 1p f", []),
                           ("cat -", []), ("cat -n a - b", ["a", "b"]),
                           ("less +G f", ["f"]), ("/usr/bin/cat a", ["a"]),
                           ("grep --color foo f", ["f"]), ("grep --colour=auto foo f", ["f"]),
                           ("grep -l foo f", []), ("grep -c foo f", []), ("rg -l foo f", [])):
            with self.subTest(text=text):
                self.assertEqual(bash.read_targets(one(text)), want)

    def test_read_targets_pipeline(self):
        a, b = cmds("cat a | head -n 5")
        self.assertEqual(bash.read_targets(a), ["a"])
        self.assertEqual(bash.read_targets(b), [])

    def test_read_targets_stdin_redirect_not_in_redirects(self):
        # `<` non arriva in Cmd.redirects (solo le uscite): nessun bersaglio, né falso.
        self.assertEqual(bash.read_targets(one("cat < f > out")), [])
        self.assertEqual(bash.read_targets(one("cat a > out")), ["a"])

    def test_read_targets_empty(self):
        self.assertEqual(bash.read_targets(bash.Cmd([], "/r")), [])


if __name__ == "__main__":
    unittest.main()
