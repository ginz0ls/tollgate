# Ri-revisione Task 15, giro 1 (84c8dc3..62a6220)

### Verdetti sui rilievi
- **I-1, `test_options_exist_in_parser` mancante**: INDIRIZZATO. `tests/test_skill_contract.py` ripristina il test, che usa `call_problems`. Prova mirata: `<programma> init --nope` e `<programma> gate sentinel --nope` danno «opzione sconosciuta»; `gate sentinel --propose` è rifiutata (opzione del nucleo su riga gate); `gate sentinel --event x` passa. I due parser sono davvero controllati (`_options(gate if on_gate else core)`), 27 opzioni nel nucleo e 10 nel gate: il test non passa a vuoto.
- **M-2, `not_tg_branch` nel gruppo sbagliato e nessun test**: INDIRIZZATO. `skills/finish/SKILL.md` elenca per gruppo le chiavi di `attention.GROUPS`. `test_finish_attention_groups_match_the_code` ricava l'insieme atteso da `attention.GROUPS` filtrando per `READ`/`INFO`, nessuna lista copiata. Elenchi della skill verificati a mano contro `bin/tollgate_gate/attention.py:8-20`: coincidono (23 e 9 chiavi).
- **M-3, servizi solo in `head`**: INDIRIZZATO. Skill `init` e README di `init.py` nominano `head` e `base` di `tollgate-run` e `ids` di `tollgate-base`. Il test asserisce `install.SERVICES_WORKFLOWS == {"run": 2, "base": 1}` e cerca i nomi dei job nei due testi. Il legame è parziale: gli aghi dei job sono scritti nel test, quindi se `SERVICES_WORKFLOWS` cambia fallisce l'asserzione sul valore e chi la aggiorna deve rivedere i testi. Accettabile.
- **M-4, controllo D18a duplicato e ramo gate non esercitato**: INDIRIZZATO. `call_problems` è unica, usata da entrambi i test reali e da `test_call_check_handles_gate_and_core_calls`, che copre casi validi e inventati (sottocomando gate, opzione del nucleo su gate, opzione gate sul nucleo, sottocomandi inventati).

### Danni nuovi nel diff della correzione
Nessuno. `python3 -B -m unittest tests.test_skill_contract`: 13 test OK.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
