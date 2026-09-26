# Holdout Ledger

A forward record of rule-based trading strategies where **every position is sealed before the trade** and **nothing can be edited afterwards**. You do not need to trust the operator. Check it yourself.

## What is in this repository

| Path | What it is |
|---|---|
| `ledger/<strategy>/commits.jsonl` | One line per session: `{date, commit, prev, ts}`. `commit` is a SHA-256 of the position, a random salt and the previous entry. Published **before** the entry time. |
| `ledger/<strategy>/reveals/<YYYY-MM>.jsonl` | Positions and salts, published after each month ends. |
| `ledger/anchors/*.txt` + `.ots` | Chain heads, stamped with [OpenTimestamps](https://opentimestamps.org) into the Bitcoin blockchain. Proves each chain existed at that time. |
| `ledger/prices/` | The public prices used to score results, captured daily and never overwritten. Their hash is in every anchor. |
| `verify.py` | Recomputes everything above. Standard library only. |

## Verify

```
python3 verify.py          # chains, revealed hashes, anchor heads
python3 verify.py --ots    # plus Bitcoin timestamps (pip install opentimestamps-client)
```

The hash of each entry:
```
commit = SHA256( date \0 canonical(positions) \0 salt \0 prev \0 )
canonical = JSON, keys sorted, values rounded to 8 decimals, no spaces
```
Because every entry contains the previous `commit`, changing any past entry changes every hash after it. Those hashes are already timestamped in Bitcoin blocks.

## What is not here, and why

The exact trading rules (spec files and code) are **not published**. Their SHA-256 hashes **are**: see the `[specs]` and `[code]` sections of every anchor file. The rules were frozen before recording started, and any change would show up as a new hash. They can be published later and checked against these anchors.

## Strategies

| Ledger | Market | Recording since |
|---|---|---|
| `mnq_night-v1` | Nasdaq-100 futures | 2026-09-24 |
| `qqq_gap-v1` | QQQ | 2026-09-24 |
| `ibs_mr-*` (3) | QQQ, XLK | 2026-09-21 (externally anchored from 2026-09-24) |
| `blend-v1` | Futures basket | 2026-09-28 |

Every ledger is published, including the ones that do badly. No ledger is ever deleted. A changed rule gets a new name (`-v2`) and a new chain.

## Limits

- **Paper record.** Results use public prices and stated costs, not broker fills.
- Sessions sealed before the first external anchor (2026-09-24) have no third-party timestamp.
- A Bitcoin confirmation can occasionally take hours. The time bound of a commit is the block time of the first anchor that contains it.

Paper-traded forward record. Not investment advice.
