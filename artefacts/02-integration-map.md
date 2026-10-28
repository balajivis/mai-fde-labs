# Integration Map — Deliverable II

*Calder & Rowe · service-desk wedge · filled in during Lab 2*

The eight layers of a production agent, laid over the customer's estate. For each layer, one of three words: **build** (we write it), **connect** (it exists; we integrate over MCP), **never** (we do not touch it, and here is why). A layer with no owner is the one that stalls the pilot.

| Layer | Build / connect / never | What it is at Calder & Rowe | Owner on their side |
|---|---|---|---|
| UI | | where the desk agent sees the draft (ticket comment? side panel?) | |
| Graph | | the triage flow: read → look up → policy → draft → propose → write back → escalate | |
| Integrations | | ticketing (on-prem), orders, customers — over MCP, scoped per user | |
| Knowledge | | the policy library; retrieval filtered by scope before search | |
| Memory | | what the agent keeps between tickets, if anything | |
| HITL | | which actions stop for a named person (credits, replacements) | |
| Eval | | the frozen golden set, the judge, the regression gate | |
| Observability | | the audit log, traces, cost per ticket | |

## Identity and scope

| Who calls the agent | Role | Regions | Sees PII | Can write |
|---|---|---|---|---|
| | | | | |

## What we never touch, and why

-

## Every call is audited

Where the audit log lives, who can read it, how long it is kept: 

*Sign-off:* Customer IT owner ____________ · FDE ____________ · date ________
