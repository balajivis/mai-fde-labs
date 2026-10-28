# The Eval Contract — Deliverable III

*Calder & Rowe · service-desk wedge · filled in during Lab 3*

The definition of "done" both sides sign **before the system is good**, so it cannot move.

## The golden set

| | |
|---|---|
| Source | the customer's own tickets, labelled by two people on their team |
| Size | 180 cases: 120 triage · 30 retrieval · 30 safety |
| Frozen on | (date) · sha256 of `golden/cases.jsonl`: |
| Who owns it after go-live | |
| How a complaint becomes a case | |

## The judge

| | |
|---|---|
| Judge model and prompt | |
| Agreement with labeller A | % |
| Agreement with labeller B | % |
| Labeller A vs labeller B | % (the ceiling: a judge cannot be more right than the people) |
| Cases the labellers disagreed on | listed in `golden/DISAGREEMENTS.md` — settled how? |

## Acceptance criteria

| Suite | Today | Must reach | Error budget |
|---|---|---|---|
| Triage (category + priority + policy + escalate) | % | % | |
| Retrieval (right policy in top-3) | % | % | |
| Safety (injection · PII · access) | % | **100%** | **none** |

## The regression gate

A change ships only if every suite holds or improves on the frozen set. Who runs it, where it runs, what happens on a fail:

*Sign-off:* Customer ops lead ____________ · FDE ____________ · date ________
