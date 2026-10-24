#!/usr/bin/env bash
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/evals/_kit/scaffold.py" l2-task2-pending
