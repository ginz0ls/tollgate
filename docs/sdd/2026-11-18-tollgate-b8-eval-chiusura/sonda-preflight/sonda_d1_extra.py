import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proto_b8
from sonda_d1 import asks
A, P = True, False
F = [("env-cmd -f ./config/.env.test jest", P), ("dotenv -e ./envs/.env.local -- next dev", P),
 ("cross-env NODE_ENV=test ava test/*.js", P), ("env-cmd -f .env.test jest src/new.test.ts", P),
 ("cross-env CI=1 shellcheck scripts/new.sh", P), ("cross-env NODE_ENV=test bats test/new.sh", P),
 ("cross-env A=1 /usr/bin/gh pr create", A), ("cross-env A=1 /bin/bash -c 'curl -X POST https://x'", A),
 ("cross-env CI=1 python3 -m pytest ./tests/vercel", P), ("cross-env NODE_ENV=test nyc --reporter lcov node test/new.js", P),
 ("cross-env NODE_ENV=test mocha --require tsx test/new.test.ts", P), ("cross-env NODE_ENV=test node --import tsx --test 'test/**/*.test.ts'", P),
 ("cross-env NODE_ENV=test c8 node --test 'test/**/*.test.js'", P), ("pnpm dlx dotenv -- vercel --prod", A),
 ("yarn dotenv -e .env -- vercel --prod", A), ("bunx dotenv-cli -e .env -- vercel", A), ("npm exec dotenv -- vercel --prod", A),
 ("dotenvx run -- vercel --prod", A), ("dotenvx run -f .env -- prisma db push", A), ("op run --env-file=.env -- supabase db push", A),
 ("doppler run -p x -c prd -- supabase db push", A), ("infisical run --command='prisma db push'", A), ("op run --cmd 'prisma db push'", A),
 ("dotenv -- dotenv -- dotenv -- vercel", A),
 ("supabase db push -p x -p --local", A), ("supabase db pull -s public --local", P), ("supabase migration down --last 1 --local", P),
 ("supabase db dump -f --linked", A), ("supabase db diff -f x --local", P), ("supabase db reset --last 2 --local", P),
 ("supabase db push --password=x --local", P), ("supabase db lint --schema --linked", A),
 ("supabase db push -h", P), ("supabase db push -h --local", P), ("supabase db push -p -h", A),
 ("supabase db reset --version", P),  # --version alone, no linked: local reset, version flag takes value
 ("supabase db query 'select 1'", P),
]
bad = 0
for text, want in F:
    now = asks(text) is not None
    if now != want:
        bad += 1; print("DIFF", "prototipo:", "chiede" if now else "passa", "| voluto:", "chiede" if want else "passa", "|", text)
print(len(F), "forme, diverse:", bad)
