import sys
sys.path.insert(0,"evals"); sys.path.insert(0,"bin")
import scrub
for c in ["tollgate research submit 1 <<'N'\nhttps://vercel.com/docs\nN",
 "python3 /x/bin/tollgate research submit 1 <<'N'\nhttps://vercel.com/docs\nN",
 "\"$CLAUDE_PLUGIN_ROOT/bin/tollgate\" research submit 1 <<'N'\nhttps://vercel.com/docs\nN",
 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate research submit 1 <<'N'\nx\nN",
 "cd /x && /x/bin/tollgate research submit 3 --fail",
 "python3 -B /x/bin/tollgate research submit 1 <<'N'\nx\nN",
 "TOLLGATE_X=1 /x/bin/tollgate research submit 1",
 "/x/bin/tollgate --json research submit 1",
 "curl -s https://vercel.com/docs research submit",
 "/x/bin/tollgate research submit 1 && curl https://vercel.com/docs"]:
    print(scrub._is_exempt(c), repr(c[:70]))
