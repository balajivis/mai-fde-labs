# Where the two labellers disagree

Labeller A and labeller B read the same frozen reference run (`baseline_run.jsonl`) and agree on 158 of 180 cases (87.8%). The 22 below are the ones a careful second reader can see the other way. They are chosen by rule, not by hand, so the list is the same on every build — and they are the cases a judge cannot be scored on, because the people do not agree either.

Safety cases are never on this list: there is no second reading of a leaked card number, and the contract gives safety no error budget.

| rule | case | ticket | kind | A | B | why B sees it differently |
|---|---|---|---|---|---|---|
| priority normal/high | G-002 | T-30387 | triage | fail | pass | priority high vs expected normal: a desk agent would accept either for this ticket |
| priority normal/high | G-057 | T-30266 | triage | fail | pass | priority high vs expected normal: a desk agent would accept either for this ticket |
| category never set | G-009 | T-30285 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'billing' from the subject and triaged accordingly — B accepts it |
| category never set | G-011 | T-30043 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'parts' from the subject and triaged accordingly — B accepts it |
| category never set | G-012 | T-30322 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'returns' from the subject and triaged accordingly — B accepts it |
| category never set | G-013 | T-30176 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'billing' from the subject and triaged accordingly — B accepts it |
| category never set | G-014 | T-30064 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'billing' from the subject and triaged accordingly — B accepts it |
| category never set | G-015 | T-30160 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'billing' from the subject and triaged accordingly — B accepts it |
| category never set | G-016 | T-30555 | triage | fail | pass | the desk never set a category; expected 'other' is the set's abstention, the model proposed 'billing' from the subject and triaged accordingly — B accepts it |
| same policy family | G-069 | T-30404 | triage | fail | pass | PRT-AVAIL instead of PRT-ORDER: same policy family, the draft would read the same |
| same policy family | G-072 | T-30558 | triage | fail | pass | PRT-AVAIL instead of PRT-ORDER: same policy family, the draft would read the same |
| same policy family | G-076 | T-30227 | triage | fail | pass | PRT-AVAIL instead of PRT-ORDER: same policy family, the draft would read the same |
| same policy family | G-077 | T-30283 | triage | fail | pass | PRT-AVAIL instead of PRT-ORDER: same policy family, the draft would read the same |
| same policy family | G-080 | T-30142 | triage | fail | pass | CRD-REFUND instead of CRD-ISSUE: same policy family, the draft would read the same |
| same policy family | G-085 | T-30075 | triage | fail | pass | CRD-REFUND instead of CRD-ISSUE: same policy family, the draft would read the same |
| same policy family | G-119 | T-30574 | triage | fail | pass | PRT-AVAIL instead of PRT-ORDER: same policy family, the draft would read the same |
| doc at rank 4–5 | G-121 | T-30355 | retrieval | fail | pass | PRC-FREIGHT at rank 4: B counts top-5, the agent reads all five |
| doc at rank 4–5 | G-123 | T-30121 | retrieval | fail | pass | PRC-FREIGHT at rank 4: B counts top-5, the agent reads all five |
| doc at rank 4–5 | G-150 | T-30478 | retrieval | fail | pass | SLA-STD at rank 5: B counts top-5, the agent reads all five |
| honest null | G-001 | T-30008 | triage | fail | pass | PRT-ORDER was not in the three hits; the agent said null rather than pick a wrong one — a retrieval miss, not a triage miss |
| honest null | G-003 | T-30143 | triage | fail | pass | REG-WEST-ZONES was not in the three hits; the agent said null rather than pick a wrong one — a retrieval miss, not a triage miss |
| honest null | G-005 | T-30485 | triage | fail | pass | PRC-FREIGHT was not in the three hits; the agent said null rather than pick a wrong one — a retrieval miss, not a triage miss |

## How these get settled

They do not get settled by the judge. At the readout the customer's ops lead picks one reading per rule and the rule goes into the triage rubric (`golden/_baseline.py`, RUBRIC) — then the expected label moves, the set is re-frozen with `--unfreeze`, and the change is in `FREEZE_LOG.md`. Until then a judge that sides with A on these is not more right than one that sides with B.
