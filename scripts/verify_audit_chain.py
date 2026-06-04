#!/usr/bin/env python3
"""
AION OS audit-chain verifier.

Walks logs/audit.log (or a path passed as argv[1]) and recomputes the
sha256 hash chain. Exits 0 if the chain is intact, 1 otherwise.

This script depends only on the stdlib so it can be shipped to a buyer
who wants to verify the log on their own machine without installing
AION OS. The verification rule is:

    row_hash = sha256(canonical_json({...row..., "prev_hash": prev}))

Genesis prev_hash is 64 zeros. Any edit, insert, delete, or reorder
inside the file breaks the chain at exactly the offending row.

Usage:
    python scripts/verify_audit_chain.py [path/to/audit.log]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

GENESIS_HASH = "0" * 64


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _row_hash(row_without_row_hash: dict) -> str:
    return hashlib.sha256(_canonical_json(row_without_row_hash).encode("utf-8")).hexdigest()


def verify(path: Path) -> int:
    if not path.exists():
        print(f"[verify] no audit log at {path} \u2014 nothing to verify.")
        return 0
    if path.stat().st_size == 0:
        print(f"[verify] {path} is empty \u2014 chain trivially valid.")
        return 0

    prev = GENESIS_HASH
    total = 0
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"[FAIL] line {lineno}: malformed JSON: {e}")
                return 1
            if entry.get("prev_hash") != prev:
                print(f"[FAIL] line {lineno}: prev_hash mismatch")
                print(f"       expected   {prev}")
                print(f"       found      {entry.get('prev_hash')}")
                return 1
            claimed = entry.get("row_hash")
            if not claimed:
                print(f"[FAIL] line {lineno}: missing row_hash")
                return 1
            body = {k: v for k, v in entry.items() if k != "row_hash"}
            recomputed = _row_hash(body)
            if recomputed != claimed:
                print(f"[FAIL] line {lineno}: row contents tampered")
                print(f"       claimed     {claimed}")
                print(f"       recomputed  {recomputed}")
                return 1
            prev = claimed

    print(f"[OK] audit chain intact across {total} row(s) in {path}")
    print(f"     final row_hash: {prev}")
    return 0


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("logs/audit.log")
    return verify(path)


if __name__ == "__main__":
    sys.exit(main())
