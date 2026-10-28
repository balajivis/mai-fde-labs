# Modern AI Pro — the FDE Field Kit

The lab kit for the **Forward Deployed Engineer** weekend. Every hands-on session runs from this repo, against one simulated customer, from the first discovery interview on Friday to the go-live readout on Sunday. Clone once, `git pull` each morning.

The builder levels taught you to build an agent. This weekend is about deploying one **inside someone else's company** — their identity, their data, their ticketing, their security review, their sign-off. So the kit is not a set of exercises; it is a customer.

## The customer: Calder & Rowe

A commercial kitchen-equipment distributor. Three regions, ~180 accounts, ~600 orders, ~600 service-desk tickets and a 40-document policy library — with the mess a real estate has: duplicate customers, orders that point nowhere, tickets with no category, a card number in a free-text field, and nine prompt injections hidden in tickets, policy documents and order notes.

Their service desk takes 600 tickets a quarter and the first reply takes 19 hours. **The wedge you build:** read the ticket, find the order and the governing policy, draft the reply, propose category and priority, write the draft back — and escalate anything that moves money to a human.

You are not the only person in that estate. `ESTATE_USER` in your `.env` is who you are — `viewer.sam` can only read west, `agent.priya` can write but cannot see PII, `admin.ruth` can do everything. The permission check lives inside the customer's system, not in your prompt. Most of what the weekend teaches follows from that one sentence.

## Setup (~10 minutes, before Friday)

```bash
git clone https://github.com/balajivis/mai-fde-labs.git
cd mai-fde-labs
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt                      # small — no local models
cp .env.example .env
```

Paste the **FDE practice key** from Mahalakshmi's email into `OPENAI_API_KEY`. It is shown once, and it only works with the `OPENAI_BASE_URL` already in the file — the key and the address travel together; a `mai_` key without the base URL returns a 401 that looks exactly like a bad key.

Then prove the whole chain in one command:

```bash
python labs/lab_0_setup.py
```

Four checks — Python and the packages, your key with one tiny model call, the estate loading as you, and the estate answering over MCP — each with its fix printed beside it.

## The labs

| Day | Lab | Session | What you leave with |
|---|---|---|---|
| Fri | `lab_1_discovery.py` | the discovery interview · ROI · the brief | **Deliverable I — Engagement Brief**, signed by your simulated customer |
| Sat | `lab_2_wedge.py` | integration over MCP · build the wedge | **Deliverable II — Integration Map** |
| Sat | `lab_3_eval_contract.py` | evals as the contract · the calibrated judge | **Deliverable III — Eval Contract** |
| Sun | `lab_4_security.py` | the security review · red-team | **Deliverable IV — Security Review Pack** |
| Sun | `lab_5_hitl_operate.py` | humans in the loop · deploy & operate | **Deliverables V–VI — Governance Canvas · Go-live & Handover** |

Every lab runs two ways: `python labs/lab_N_….py` for a guided walkthrough in the terminal, or add `--web` for a page at `localhost:786N` with the lab's knobs on it. Same code either way; the page is served by Python's standard library, nothing to install.

The templates for all six artefacts are in [`artefacts/`](./artefacts). The labs fill the parts they can; you fill the parts that need a judgement.

## What is in the box

| | |
|---|---|
| `estate/data/` | Calder & Rowe: customers, orders, tickets, policies, identity. Generated deterministically by `estate/build_estate.py` (seed 2026); `plants.json` lists every piece of planted mess so a red-team can check its coverage |
| `labs/_estate.py` | the estate API. Every function takes the acting user first and enforces scope **inside** — region filtered before retrieval, PII masked by role, writes refused by role, every call (and every denial) written to `estate/data/audit.jsonl` |
| `labs/estate_mcp.py` | the same API as an **MCP server** over stdio. The labs talk to the estate the way you will talk to a real ticketing system; so can your editor (below) |
| `golden/` | the frozen golden set: 180 cases, two human labellers, the disagreements written down, and the hash it was frozen at |
| `labs/_kit.py` · `_web.py` | the plumbing from the builder kits, unchanged: `client()`, `chat()` with the meter and the JSONL tracer, the knob panel |
| `docs/CONTRACT.md` | the spec every file above is written against — read it when you want to know *why* something is shaped the way it is |

Your writes to the estate go to `estate/data/state.json` (gitignored), so `git pull` never clobbers your run and `_estate.reset()` returns to a clean customer.

### Talk to the estate from your editor

The server is plain MCP, so Claude Desktop, VS Code and Cursor can use it directly. Add this (adjust the paths) and you can ask your assistant "what open warranty tickets does agent.priya have?" — and watch it get denied on anything out of scope.

```json
{
  "mcpServers": {
    "calder-rowe": {
      "command": "/absolute/path/to/mai-fde-labs/.venv/bin/python",
      "args": ["/absolute/path/to/mai-fde-labs/labs/estate_mcp.py", "--as", "agent.priya"]
    }
  }
}
```

## For the business track

Half the room runs engagements without writing code. Your wedge is the same wedge — configured on the agent canvas during the Saturday lab, judged on the same eval contract, defended in the same readout on Sunday. The discovery lab, the artefact templates and the golden set are yours as much as the engineers'; the Python labs are there to read, and your pair runs them with you.

## Getting updates

```bash
git pull
```

Run it at the start of every session. Fixes and the later labs land during the weekend.

## Stuck?

Read [`FAQ.md`](./FAQ.md) first — it covers the common errors verbatim. Then ask in the cohort room at [study.modernaipro.com](https://study.modernaipro.com). If Python itself is fighting you, the browser **Lab Bench** at [study.modernaipro.com/learn/lab](https://study.modernaipro.com/learn/lab) runs the same files with nothing to install.
