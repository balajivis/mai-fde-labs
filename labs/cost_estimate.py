# -*- coding: utf-8 -*-
"""COST ESTIMATE — the fifteen-minute version

Modern AI Pro · FDE Field Kit · Day 2 · before the wedge

The CFO asks one question on Friday and again on Sunday: what does a ticket
cost? Estimate it now with four lines of arithmetic, then let lab 2's batch
replace the guess with a measured number. The worksheet is docs/COST.md.

Four lines, nothing else:

    model calls     tasks × (tokens in × price in + tokens out × price out)
    embeddings      corpus once, plus the slice that changes, plus one per query
    evals           golden cases × judge tokens × how often you change anything
    fixed           hosting, tracing, the proxy — and the people, written down

Prices are NOT in this file. They move; the arithmetic does not. Take today's
input and output price per million tokens from your provider's price page and
pass them in. Without prices the tool still prints the token totals, which is
the half of the estimate that is yours to defend.

    python labs/cost_estimate.py --tasks 200 --tokens-in 10000 --tokens-out 600 \
        --price-in 2.50 --price-out 10.00 --fixed 350

    python labs/cost_estimate.py --from-traces traces.jsonl --tasks 200 --price-in 2.50 --price-out 10.00
        (tokens per task come from the traced calls of your lab 2 run)

Numbers to start from, measured 2026-10-28 on the kit's own wedge (lab 2, stage 5):
11.4k tokens per ticket, of which roughly 95% were input — the tool results and
the system prompt come back on every round. Calder & Rowe: 600 tickets a
quarter, 200 a month, $31 a ticket today.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def money(x: float | None) -> str:
    return "—" if x is None else f"${x:,.2f}"


def per_m(tokens: float, price_per_m: float | None) -> float | None:
    return None if price_per_m is None else tokens / 1_000_000 * price_per_m


def from_traces(path: Path, label: str | None) -> tuple[float, float, int, dict]:
    """Mean prompt/completion tokens per traced call, grouped by label.
    A wedge run is several calls per ticket; multiply by --calls-per-task."""
    by = defaultdict(lambda: [0, 0, 0])
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not r.get("ok", True) or r.get("prompt_tokens") is None:
                continue
            if label and r.get("label") != label:
                continue
            row = by[r.get("label", "call")]
            row[0] += r["prompt_tokens"] or 0
            row[1] += r.get("completion_tokens") or 0
            row[2] += 1
    n = sum(v[2] for v in by.values())
    if not n:
        sys.exit(f"no usable traced calls in {path}" + (f" with label {label!r}" if label else ""))
    pin = sum(v[0] for v in by.values()) / n
    pout = sum(v[1] for v in by.values()) / n
    return pin, pout, n, {k: (v[0] / v[2], v[1] / v[2], v[2]) for k, v in by.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", type=float, default=200, help="tasks (tickets) per month")
    ap.add_argument("--tokens-in", type=float, default=None, help="input tokens per task, all rounds added up")
    ap.add_argument("--tokens-out", type=float, default=None, help="output tokens per task")
    ap.add_argument("--calls-per-task", type=float, default=1.0, help="with --from-traces: model calls one task takes (lab 2 stage 2: about 5)")
    ap.add_argument("--from-traces", type=Path, help="read tokens per call from a traces.jsonl written by the labs")
    ap.add_argument("--label", help="with --from-traces: only calls with this label (e.g. wedge)")
    ap.add_argument("--price-in", type=float, help="$ per million input tokens — from your provider's price page")
    ap.add_argument("--price-out", type=float, help="$ per million output tokens")
    ap.add_argument("--retry-pct", type=float, default=5, help="percent of tasks that run twice (429s, timeouts, a judge re-ask)")
    ap.add_argument("--embed-corpus", type=float, default=0, help="tokens in the corpus you embed once (policies, past tickets)")
    ap.add_argument("--embed-change-pct", type=float, default=10, help="percent of the corpus re-embedded each month")
    ap.add_argument("--embed-query-tokens", type=float, default=200, help="tokens embedded per task for the query (0 if keyword search)")
    ap.add_argument("--price-embed", type=float, help="$ per million embedding tokens")
    ap.add_argument("--judge-cases", type=float, default=180, help="golden cases rerun on every change")
    ap.add_argument("--judge-tokens", type=float, default=1500, help="tokens per judge call (mostly input)")
    ap.add_argument("--changes", type=float, default=8, help="prompt/model/retrieval changes per month, each reruns the set")
    ap.add_argument("--fixed", type=float, default=0, help="$ per month: hosting, tracing, proxy, licences")
    ap.add_argument("--people-hours", type=float, default=0, help="hours a month of human review/approval the design needs")
    ap.add_argument("--loaded-rate", type=float, default=0, help="$ per hour, loaded, for those hours")
    ap.add_argument("--today", type=float, default=31, help="$ per task today, the number from the brief")
    a = ap.parse_args()

    groups = None
    if a.from_traces:
        pin, pout, n, groups = from_traces(a.from_traces, a.label)
        a.tokens_in = pin * a.calls_per_task
        a.tokens_out = pout * a.calls_per_task
        print(f"\nfrom {a.from_traces}: {n} traced calls · mean {pin:,.0f} in / {pout:,.0f} out per call · × {a.calls_per_task:g} calls per task")
        for k, (i, o, c) in sorted(groups.items()):
            print(f"    {k:<12} ×{c:<4} {i:>8,.0f} in  {o:>6,.0f} out")
    if a.tokens_in is None or a.tokens_out is None:
        sys.exit("need --tokens-in and --tokens-out (or --from-traces). Lab 2 stage 5 prints them per ticket.")

    mult = 1 + a.retry_pct / 100
    tin = a.tasks * a.tokens_in * mult
    tout = a.tasks * a.tokens_out * mult
    model_cost = None if a.price_in is None or a.price_out is None else per_m(tin, a.price_in) + per_m(tout, a.price_out)

    embed_tokens = a.embed_corpus * a.embed_change_pct / 100 + a.tasks * a.embed_query_tokens
    embed_once = a.embed_corpus
    embed_cost = per_m(embed_tokens, a.price_embed) if a.embed_corpus or a.embed_query_tokens else 0.0
    embed_once_cost = per_m(embed_once, a.price_embed) if a.embed_corpus else 0.0

    judge_tokens = a.judge_cases * a.judge_tokens * a.changes
    judge_cost = None if a.price_in is None else per_m(judge_tokens * 0.9, a.price_in) + per_m(judge_tokens * 0.1, a.price_out or a.price_in)

    people = a.people_hours * a.loaded_rate

    print(f"\nCOST ESTIMATE · {a.tasks:,.0f} tasks a month · retries {a.retry_pct:g}%\n")
    print(f"  {'line':<34}{'tokens / month':>16}{'$ / month':>12}")
    print(f"  {'model calls — input':<34}{tin:>16,.0f}{money(per_m(tin, a.price_in)):>12}")
    print(f"  {'model calls — output':<34}{tout:>16,.0f}{money(per_m(tout, a.price_out)):>12}")
    print(f"  {'embeddings — changes + queries':<34}{embed_tokens:>16,.0f}{money(embed_cost):>12}")
    print(f"  {'evals — judge reruns':<34}{judge_tokens:>16,.0f}{money(judge_cost):>12}")
    print(f"  {'fixed — hosting, tracing, proxy':<34}{'':>16}{money(a.fixed):>12}")
    print(f"  {'people — review hours':<34}{'':>16}{money(people):>12}")
    if embed_once:
        print(f"  {'(one-off: embed the corpus)':<34}{embed_once:>16,.0f}{money(embed_once_cost):>12}")
    known = [v for v in (model_cost, embed_cost, judge_cost) if v is not None] + [a.fixed, people]
    total = sum(known)
    print(f"  {'-' * 62}")
    if model_cost is None:
        print(f"  {'total':<34}{'':>16}{'add prices':>12}")
        print("\n  Pass --price-in and --price-out (and --price-embed) from your provider's price page.")
        print("  The token totals above are the half of the estimate that is yours either way.\n")
        return 0
    print(f"  {'total':<34}{'':>16}{money(total):>12}")
    per_task = total / a.tasks if a.tasks else 0
    ai_only = (model_cost + (embed_cost or 0) + (judge_cost or 0)) / a.tasks if a.tasks else 0
    print(f"\n  per task: {money(per_task)} all-in · {money(ai_only)} AI calls only · {money(a.today)} today")
    if a.today and per_task:
        print(f"  the AI line is {100 * ai_only / a.today:.1f}% of today's cost; the rest of the saving is the people and the process")
    print(f"\n  share of model spend that is input tokens: {100 * tin / (tin + tout):.0f}%  — the system prompt and tool results, every round\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
