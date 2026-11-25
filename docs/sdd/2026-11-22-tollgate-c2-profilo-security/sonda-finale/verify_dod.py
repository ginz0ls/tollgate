"""`<programma> verify` esegue i comandi di `gate`, non quelli di `dod` di un profilo (sonda della revisione finale)."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
code = Path(sys.argv[1]); sys.path.insert(0, str(code / "bin"))
from tollgate_core import config, runner
base = (code / "templates" / "tollgate.toml").read_text(encoding="utf-8").replace("__MODE__", "detect")
base = base.replace('verify = ""', 'verify = "python3 -m unittest"') if 'verify = ""' in base else base
toml = base + '''
[profiles.security]
paths = ["app/auth/**"]
commands = { denied = "python3 -m unittest discover -s tests -k denied" }
dod = ["denied"]
'''
cfg = config.load_config_text(toml)
files = ["app/auth/tokens.py"]
print("gate (ciò che esegue `verify`):", [c.name for c in runner.gate_commands(cfg, files)])
print("dod (solo `finish check` e `open-pr`):", [c.name for c in runner.dod_commands(cfg, files)])
toml2 = toml.replace('dod = ["denied"]', 'dod = ["denied"]\ngate = ["denied"]')
cfg2 = config.load_config_text(toml2)
print("con gate = [\"denied\"] nel profilo, `verify` esegue:", [c.name for c in runner.gate_commands(cfg2, files)])
