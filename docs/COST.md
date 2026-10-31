# What does a ticket cost? The fifteen-minute estimate

Every CFO asks it, and the honest answer has four lines. Do them now on paper, then let lab 2's batch replace the first line's guess with a measured number, and Sunday's traces replace the rest.

Prices are deliberately not printed here. They move every quarter; the arithmetic does not. Open your provider's price page, take today's price per million tokens for input, output and embeddings, and write them at the top of your sheet with the date.

## The four lines

| Line | The arithmetic | What people forget |
|---|---|---|
| **Model calls** | tasks × (tokens in × price in + tokens out × price out) | Input dominates. The system prompt and every tool result come back on every round; a 5-round wedge sends its context five times. The kit's wedge: ~11.4k tokens per ticket, about 95% input |
| **Embeddings** | the corpus once, plus the slice that changes each month, plus one query embedding per task | Re-embedding the whole corpus on every edit; keyword search (what the kit uses) costs nothing here |
| **Evals** | golden cases × judge tokens × how often you change anything | A 180-case rerun on every prompt tweak is often more model spend than the tickets themselves |
| **Fixed** | hosting, tracing, the proxy, licences — and the people | The hours a named person spends approving. A design that queues every draft has a people line, and it is the biggest one |

Then two more lines that are not costs but are what the CFO compares against:

- **Retries.** 429s, timeouts, a judge that re-asks. Add 5% until you have measured it.
- **Today's number.** Cost per task today, loaded. For Calder & Rowe it is $31. That is the only number on the sheet the customer gives you; the rest you must be able to show.

## The worksheet

```
Customer:                         Date:            Prices from:            (per 1M tokens: in ___  out ___  embed ___)

tasks a month                     ______
tokens in per task                ______   (lab 2 stage 5 prints this; until then, the kit's 10,800)
tokens out per task               ______   (the kit's 600)
retry %                           ______   (5 until measured)
corpus tokens, embedded once      ______   (0 for keyword search)
% of corpus that changes a month  ______
golden cases × judge tokens       ______   (180 × ~1,500)
changes a month that rerun them   ______
fixed $ a month                   ______
people hours a month × loaded $   ______

per task, AI calls only           ______
per task, all-in                  ______
per task today                    ______   ← from the brief
```

Or let the kit do the arithmetic:

```bash
python labs/cost_estimate.py --tasks 200 --tokens-in 10800 --tokens-out 600 \
    --price-in <in> --price-out <out> --fixed 350 --people-hours 20 --loaded-rate 38
```

After lab 2, the measured version reads your own traces:

```bash
python labs/cost_estimate.py --from-traces traces.jsonl --calls-per-task 5 --tasks 200 --price-in <in> --price-out <out>
```

## The exercise (15 minutes)

1. **Five minutes, alone.** Fill the worksheet for the workflow in your Engagement Brief. Use the kit's token numbers if you have none of your own; use your provider's prices, today's.
2. **Five minutes, with your pair.** Swap sheets. Find the line the other person left out. It is almost always people or evals.
3. **Five minutes, the room.** Three sheets read aloud: per task AI-only, per task all-in, per task today. The gap between the first two is the conversation with the CFO. The gap between the last two is the ROI line in the brief, now with a cost you can defend.

## What makes it 10× worse, so you can say so before it happens

- A planner-and-workers shape where one fixed flow would do: every worker re-reads the context.
- A system prompt that carries the whole policy library instead of retrieving three documents.
- Re-embedding the corpus on every edit, or embedding past tickets nobody retrieves.
- Running the full golden set on every commit instead of on every change that reaches the gate.
- A queue that asks a person to approve drafts that never move money. The people line, not the model line, is where pilots become unaffordable.

Write the measured number on the Integration Map's Observability row. Sunday's go-live sheet asks for it again, from traces.
