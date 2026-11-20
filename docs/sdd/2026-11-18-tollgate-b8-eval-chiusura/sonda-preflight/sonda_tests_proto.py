import os, sys, unittest
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, WT)
os.chdir(WT)
import proto_b8
suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_bash")
res = unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0).run(suite)
print("run", res.testsRun, "fail", len(res.failures), "err", len(res.errors))
for t, tb in res.failures + res.errors:
    print("ROSSO", t.id()); print("   ", tb.strip().splitlines()[-1][:300])
