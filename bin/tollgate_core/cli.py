"""Sottocomandi di bin/tollgate (spec 3.1). P1: status, stats, events, db restore."""
from __future__ import annotations

import argparse

from . import VERSION


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tollgate")
    p.add_argument("--version", action="version", version=f"tollgate {VERSION}")
    p.add_subparsers(dest="cmd")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd is None:
        build_parser().print_help()
    return 0
