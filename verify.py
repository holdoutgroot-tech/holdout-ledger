#!/usr/bin/env python3
"""Verify the Holdout ledger yourself. Python 3.8+, standard library only.

    python3 verify.py            # chains, revealed hashes, anchor heads
    python3 verify.py --ots      # also run `ots verify` on every anchor (pip install opentimestamps-client)

Checks
  1. Chain: every entry's `prev` equals the previous entry's `commit` (first = 64 zeros), dates strictly increase.
  2. Reveals: for every revealed session, SHA256(date \\0 positions \\0 salt \\0 prev \\0) equals the published commit.
     positions = JSON with sorted keys, values rounded to 8 decimals, no spaces.
  3. Anchors: every chain head listed in anchors/*.txt is an entry of that chain.
     With --ots, each anchor file is checked against its Bitcoin timestamp.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger")
GENESIS = "0" * 64


def canonical(p):
    return json.dumps({str(k): round(float(v), 8) for k, v in p.items()}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def commit_hash(date, positions, salt, prev):
    m = hashlib.sha256()
    for part in (date, canonical(positions), salt, prev):
        m.update(part.encode("utf-8"))
        m.update(b"\x00")
    return m.hexdigest()


def main():
    ots = "--ots" in sys.argv
    bad = 0
    chains = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "*", "commits.jsonl"))):
        name = os.path.basename(os.path.dirname(path))
        cs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
        chains[name] = cs
        prev, last, ok = GENESIS, "", True
        for c in cs:
            if c["prev"] != prev or c["date"] <= last:
                print(f"FAIL chain {name} at {c['date']}")
                ok = False
            prev, last = c["commit"], c["date"]
        rev = {}
        for f in sorted(glob.glob(os.path.join(ROOT, name, "reveals", "*.jsonl"))):
            for l in open(f, encoding="utf-8"):
                if l.strip():
                    r = json.loads(l)
                    rev[r["date"]] = r
        by = {c["date"]: c for c in cs}
        match = 0
        for d, r in rev.items():
            c = by.get(d)
            if c and commit_hash(d, r["positions"], r["salt"], c["prev"]) == c["commit"]:
                match += 1
            else:
                print(f"FAIL reveal {name} {d}")
                ok = False
        bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {name}: {len(cs)} sealed, {match}/{len(rev)} revealed hashes match")
    anchors = sorted(glob.glob(os.path.join(ROOT, "anchors", "*.txt")))
    for a in anchors:
        for l in open(a, encoding="utf-8"):
            if l.startswith("holdout-anchor "):
                parts = dict(x.split("=", 1) for x in l.split()[2:] if "=" in x)
                name, head = l.split()[1], parts.get("head")
                if head != GENESIS and head not in {c["commit"] for c in chains.get(name, [])}:
                    print(f"FAIL anchor {os.path.basename(a)}: head of {name} not in chain")
                    bad += 1
        if ots and os.path.exists(a + ".ots"):
            r = subprocess.run(["ots", "verify", a + ".ots"], capture_output=True, text=True)
            msg = (r.stdout + r.stderr).strip().splitlines()
            print(f"ots  {os.path.basename(a)}: {msg[-1] if msg else r.returncode}")
    print(f"{len(anchors)} anchor files checked.")
    print("ALL CHECKS PASSED" if bad == 0 else f"{bad} PROBLEM(S)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
