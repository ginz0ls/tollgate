import sys
sys.path.insert(0,"bin")
from tollgate_analysis import bash
cfg=bash.EffectsCfg()
forms=[
 'cross-env-shell "cd apps/web && vercel deploy --prod"',
 'env-cmd --use-shell "cd apps/web && vercel deploy --prod"',
 'cross-env-shell "curl -X POST https://api.example.com"',
 'cross-env-shell "prisma migrate deploy --schema=db/schema.prisma"',
 'cross-env-shell "./scripts/build && vercel --prod"',
 'cross-env-shell "supabase db push --workdir ./supa"',
 'cross-env-shell "DEBUG=1 vercel --prod"',
 'env-cmd --use-shell "NODE_ENV=production prisma migrate deploy"',
 '--- innocui',
 'cross-env NODE_ENV=test jest -t "src/aws parse"',
 'cross-env NODE_ENV=test jest src/aws',
 'cross-env-shell "jest && echo ok"',
 'cross-env NODE_ENV=test jest -t "tests/vercel deploy"',
 'cross-env NODE_ENV=test jest --testNamePattern "a=b c"',
 'dotenv -- jest -t "src/vercel deploy works"',
 'cross-env NODE_ENV=test jest --config "my cfg/vercel.json"',
 'cross-env NODE_ENV=test jest -t "wrangler deploy"',
 'cross-env X=1 mocha --grep "supabase db push handles"',
 'cross-env X=1 jest -t "FOO=1 bar baz"',
 'cross-env X=1 vitest run -t "does the deploy thing"',
 'cross-env X=1 playwright test --grep "vercel --prod flow"',
]
for f in forms:
    if f.startswith('---'): print(f); continue
    try:
        cmds=bash.parse(f,"/r/wt")
        r=[bash.effect_reason(c,cfg) for c in cmds]
    except Exception as e:
        r=repr(e)
    print(("ASK " if any(r) else "pass"),f,"|",[x for x in r if x] if not isinstance(r,str) else r)
