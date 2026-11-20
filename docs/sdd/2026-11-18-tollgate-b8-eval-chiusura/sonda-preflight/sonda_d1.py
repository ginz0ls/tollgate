"""Sonda decisione 1-3 su bash.effect_reason (solo testo, nessun programma lanciato)."""
import sys, os
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, os.path.join(WT, "bin"))
sys.dont_write_bytecode = True
from tollgate_analysis import bash

CFG = bash.EffectsCfg(commands=[], project_scripts=["deploy", "release"], allow=[])


def asks(text):
    try:
        cmds = bash.parse(text, "/r/wt")
    except bash.BashParseError:
        return bash.text_effect(text)
    for c in cmds:
        r = bash.effect_reason(c, CFG)
        if r:
            return r
    return None

A, P = True, False  # chiede, passa
FORMS = [
 # Review Focus 1 - devono chiedere
 ("RF1", "dotenv -e .env.production -- prisma migrate deploy", A),
 ("RF1", "dotenv -e .env.production -- npm run deploy", A),
 ("RF1", "cross-env NODE_ENV=production drizzle-kit push", A),
 ("RF1", "doppler run -- npx supabase db push", A),
 ("RF1", "doppler run --command 'prisma migrate deploy'", A),
 ("RF1", "op run -- supabase db push", A),
 ("RF1", "infisical run --env=prod -- prisma db push", A),
 ("RF1", "dotenv -- curl -X POST https://x", A),
 ("RF1", "dotenv -- bash -c 'prisma migrate deploy'", A),
 ("RF1", "npm exec prisma -- -- migrate deploy", A),
 ("RF1", "supabase db push -p --local", A),
 ("RF1", "supabase db pull --schema --local", A),
 ("RF1", "supabase db push -p --help", A),
 # Review Focus 1 - devono passare
 ("RF1", "dotenv -- python3 -m unittest", P),
 ("RF1", "dotenv -- npm i -g vercel", P),
 ("RF1", "supabase db push -p x --local", P),
 ("RF1", "cross-env CI=1 python3 tools/build.py", P),
 # decisione 1 esempi
 ("D1", "cross-env A=1 /usr/local/bin/vercel --prod", A),
 ("D1", "env-cmd -f .env /usr/local/bin/vercel --prod", A),
 ("D1", "cross-env A=1 /usr/bin/curl -X POST https://x", A),
 ("D1", "cross-env A=1 /usr/bin/make deploy", A),
 ("D1", "cross-env A=1 ./deploy.sh", P),  # script: _script_reason, non effect_reason
 ("D1", "cross-env A=1 ./deploy", P),     # idem
 ("D1", "dotenv -e .env ./scripts/deploy.sh", P),  # idem
 ("D1", "env-cmd -f ./test/.env mocha -R spec", P),
 ("D1", "dotenv -e ./.env.test -- jest", P),
 ("D1", "cross-env NODE_ENV=test jest src/aws", P),
 ("D1", "cross-env NODE_ENV=test mocha 'test/**/*.spec.js'", P),
 ("D1", "npx dotenv -e .env -- npm run deploy", A),
 ("D1", "npx dotenv@16 -e .env -- npm run deploy", A),
 ("D1", "npx dotenv-cli -e .env -- npm run deploy", A),
 ("D1", "npx @dotenvx/dotenvx run -- npm run deploy", A),
 ("D1", "npx cross-env NODE_ENV=production npm run release", A),
 ("D1", "pnpm exec dotenv -- gh pr create", A),
 ("D1", "npm i -D cross-env vercel", P),
 ("D1", "pnpm add -D dotenv vercel", P),
 ("D1", "cross-env NODE_ENV=production prisma migrate deploy", A),
 ("D1", "dotenv -- env X=1 prisma migrate deploy", A),
 ("D1", "dotenv -- sudo prisma migrate deploy", A),
 ("D1", "dotenv -- timeout 60 supabase db push", A),
 ("D1", "dotenv -- python3 manage.py check", P),
 ("D1", "cross-env CI=1 python3 -m pytest tests/vercel", P),
 ("D1", "dotenv -e vercel -- echo x", A),
 ("D1", "dotenv -e vercel echo x", A),
 ("D1", "cross-env vercel echo x", A),
 ("D1", "cross-env NODE_ENV=test jest aws", A),
 ("D1", "cross-env NODE_ENV=production npm run deploy -- --prod", A),
 ("D1", "env-cmd -f .env npm run release -- --tag x", A),
 ("D1", "dotenv -e .env.production npm run deploy -- --prod", A),
 ("D1", "cross-env NODE_ENV=production prisma migrate deploy -- --x", A),
 ("D1", "dotenv -- doppler run -- prisma migrate deploy", A),
 ("D1", "dotenv -- doppler run -- infisical run -- prisma migrate deploy", A),
 ("D1", "dotenv -- sh -c 'curl -X POST https://x'", A),
 ("D1", "dotenv -- FOO=1 prisma migrate deploy", A),
 ("D1", "dotenv -- time npm run deploy", A),
 ("D1", "doppler run --command='prisma migrate deploy'", A),
 ("D1", "doppler run --project supabase --config prd -- npm run dev", A),
 ("D1", "dotenv -- git push", P),
 ("D1", "cross-env A=1 scripts/deploy", P),
 ("D1", "cross-env A=1 ./vercel --prod", P),
 ("D1", "dotenv -- bash -c \"it's; curl -X POST https://x\"", A),
 ("D1", "dotenv --debug node x.js", P),
 ("D1", "dotenv -- node scripts/migrate.js", P),
 ("D1", "cross-env NODE_ENV=test c8 -r text node --test 'test/**/*.test.js'", P),
 # oggi gia' noti da fatti verificati
 ("F", "env-cmd -f .env prisma migrate deploy", A),
 ("F", "infisical run -- prisma migrate deploy", A),
 ("F", "doppler run -- prisma migrate deploy", A),
 ("F", "op run -- supabase db push", A),
 ("F", "npx dotenv -e .env -- prisma migrate deploy", A),
 ("F", "npx -- prisma migrate deploy", A),
 ("F", "env FOO=1 prisma migrate deploy", A),
 # decisione 2 supabase
 ("D2", "supabase db push --password --local", A),
 ("D2", "supabase db push -p --local", A),
 ("D2", "supabase db pull --schema --local", A),
 ("D2", "supabase db pull -s --local", A),
 ("D2", "supabase db pull --schema -h", A),
 ("D2", "supabase db push --help", P),
 ("D2", "supabase db push -p x --local", P),
 ("D2", "supabase db push -p segreto --local", P),
 ("D2", "supabase --version", P),
 ("D2", "supabase db reset --linked --version 20240101", A),
 ("D2", "supabase db reset --version 20240101 --local", P),
 ("D2", "supabase migration down --last --local", A),
 ("D2", "supabase migration down --last 1 --local", P),
 ("D2", "supabase migration repair --status applied 1 --local", P),
 ("D2", "supabase db push --db-url postgres://prod --local", A),
 ("D2", "npx supabase db push -p --local", A),
 ("D2", "npx supabase db push -p x --local", P),
 ("D2", "npx supabase migration down --last --local", A),
 ("D2", "npx supabase db pull --schema --local", A),
 # decisione 3
 ("D3", "npm exec prisma -- -- migrate deploy", A),
 ("D3", "npm exec prisma -- migrate deploy", A),
 ("D3", "npx prisma -- migrate deploy", A),
 ("D3", "supabase -- db push", A),
]
if __name__ == "__main__":
    for tag, text, want in FORMS:
        r = asks(text)
        now = r is not None
        mark = "ok" if now == want else "DIFF"
        print(f"{mark}\t{tag}\t{'chiede' if now else 'passa'}\tvoluto {'chiede' if want else 'passa'}\t{text}\t{r or ''}")
