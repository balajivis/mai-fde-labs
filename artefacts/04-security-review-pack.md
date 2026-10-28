# Security Review Pack — Deliverable IV

*Calder & Rowe · service-desk wedge · filled in during Lab 4*

What their CISO will ask, answered in writing.

## Threat model

| Threat | Where it enters | Control | Evidence |
|---|---|---|---|
| Prompt injection through a ticket body | customer email text | | red-team case ids: |
| Prompt injection through a policy document | the knowledge layer | | |
| Prompt injection through a tool result | order notes | | |
| Data leakage across regions | retrieval | scope filtered **before** search | |
| PII reaching a draft reply | ticket bodies | masked at the tool, not the prompt | |
| Privilege escalation (agent issuing a credit) | tool layer | role check inside the function; destructive = human | |

## Red-team results

| Attempt | Succeeded? | Now a frozen case? | Case id |
|---|---|---|---|
| | | | |

Coverage against the planted injections (`estate/data/plants.json`): __ of 9 found.

## Access and residency

| Question | Answer |
|---|---|
| Who can the agent act as? | |
| Scoped tokens per user, or one service account? | |
| Where does customer data go? (model calls, logs, traces) | |
| Data residency constraint | US only (Ruth) — how is it met? |
| Audit log: where, who reads it, retention | |

*Sign-off:* Customer security owner ____________ · FDE ____________ · date ________
