import sys
sys.path.insert(0,"bin")
from tollgate_analysis import bash
cfg=bash.EffectsCfg()
for f in ['doppler secrets set A=1','infisical secrets set A=1','op item create --title x','infisical sm run -- vercel --prod','infisical secrets-manager run -- vercel --prod','infisical run -- vercel --prod','infisical sm run --command "vercel --prod"']:
    r=[bash.effect_reason(c,cfg) for c in bash.parse(f,"/r/wt")]
    print(f,r)
print([c.argv for c in bash.true_inner_commands(bash.parse('infisical sm run -- ./deploy.sh',"/r/wt")[-1])])
