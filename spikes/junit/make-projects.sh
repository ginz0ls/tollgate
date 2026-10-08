#!/usr/bin/env bash
# spikes/junit/make-projects.sh — crea ed esegue tre progetti giocattolo
set -uo pipefail
J=/tmp/tollgate-p0/junit; rm -rf "$J"; mkdir -p "$J"/{vitest,jest,pytest}

cd "$J/vitest" && npm init -y >/dev/null && npm i -D vitest@2 >/dev/null 2>&1
cat > sample.test.js <<'JS'
import { describe, it, expect } from 'vitest'
describe('group', () => {
  it('passes', () => expect(1).toBe(1))
  it.skip('skipped', () => expect(1).toBe(2))
  it('fails', () => expect(1).toBe(2))
})
JS
for r in 1 2; do npx vitest run --reporter=junit --outputFile="run$r.xml" >/dev/null 2>&1; done

cd "$J/jest" && npm init -y >/dev/null && npm i -D jest@29 jest-junit@16 >/dev/null 2>&1
cat > sample.test.js <<'JS'
describe('group', () => {
  it('passes', () => expect(1).toBe(1))
  it.skip('skipped', () => expect(1).toBe(2))
  it('fails', () => expect(1).toBe(2))
})
JS
for r in 1 2; do JEST_JUNIT_OUTPUT_NAME="run$r.xml" npx jest --reporters=default --reporters=jest-junit >/dev/null 2>&1; done

cd "$J/pytest" && python3 -m venv .venv && .venv/bin/pip -q install pytest >/dev/null 2>&1
cat > test_sample.py <<'PY'
import pytest
class TestGroup:
    def test_passes(self): assert 1 == 1
    @pytest.mark.skip(reason="probe")
    def test_skipped(self): assert 1 == 2
    def test_fails(self): assert 1 == 2
PY
for r in 1 2; do .venv/bin/pytest -q --junitxml="run$r.xml" >/dev/null 2>&1; done
ls "$J"/*/run*.xml
