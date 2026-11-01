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

**Sunday, for lab 2b only:** `pip install -r requirements-graph.txt` adds LangGraph and its MCP adapter. Every other lab stays framework-free. The install moves the `mcp` package back a major version; the kit handles both, and `python labs/lab_0_setup.py` afterwards proves it.

## The labs

| Day | Lab | Session | What you leave with |
|---|---|---|---|
| Fri | `lab_1_discovery.py` | the discovery interview · ROI · the brief | **Deliverable I — Engagement Brief**, signed by your simulated customer |
| Sat | `lab_1a_cost.py` | the fifteen-minute cost estimate, before the wedge | the ROI line in Deliverable I, with a cost you can defend |
| Sat | `lab_2_wedge.py` | integration over MCP · build the wedge | **Deliverable II — Integration Map** |
| Sat | `lab_2a_layers.py` | your customer's requirements → the questions the map needs → the eight layers and the flow | **Deliverable II for your own customer**, plus their flow on the kit's sheet |
| Sat | `lab_3_eval_contract.py` | evals as the contract · the calibrated judge | **Deliverable III — Eval Contract** |
| Sun | `lab_2b_multiagent.py` | the LangGraph taste: a router, three specialists, one gate, over the same MCP server | the three decisions filled in (routing rules, the gate, the budget), a chat you can deploy |
| Sun | `lab_4_security.py` | the security review · red-team | **Deliverable IV — Security Review Pack** |
| Sun | `lab_5_hitl_operate.py` | humans in the loop · deploy & operate | **Deliverables V–VI — Governance Canvas · Go-live & Handover** |

Most labs run two ways: `python labs/lab_N_….py` for a guided walkthrough in the terminal, or add `--web` for a page with the lab's knobs on it. Same code either way; the page is served by Python's standard library, nothing to install. Lab 1a is a calculator and lab 2a an interview, so both are terminal only.

| `--web` | 1 | 2 | 3 | 4 | 5 | 2b |
|---|---|---|---|---|---|---|
| port | 7861 | 7862 | 7863 | 7864 | 7865 | 7866 (the chat page) |

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
| `docs/WEDGE.md` · `docs/wedge/` | lab 2 stage by stage as one sheet: what they do, the point to land, what to watch for, with the Oct 28 reference numbers |
| `docs/COST.md` · `labs/lab_1a_cost.py` | lab 1a, the fifteen-minute cost estimate: four lines (model calls, embeddings, evals, fixed + people), a worksheet, and a calculator that later reads your own traces. Prices come from your provider's page, not from the kit |
| `docs/SCHEDULE.md` · `docs/schedule/` | Saturday and Sunday hour by hour, as one sheet |
| `labs/lab_2a_layers.py` | lab 2a: give it a brief (yours from lab 1, or any text), answer the questions it asks for the open layers, and it writes the Integration Map, the eight-layer sheet and the flow sheet for that customer into `reports/` |
| `docs/GRAPH.md` · `labs/lab_2b_multiagent.py` · `Dockerfile` | lab 2b: a small multi-agent chat in LangGraph over the estate, the scaffold and the chat page given, three blanks left for you; one container to deploy it on a box you own. `pip install -r requirements-graph.txt` first |
| `docs/FLOWS.md` · `docs/flows/` | the five reference flows as SVG sheets (open `docs/flows/index.html` in a browser): trigger, fixed steps, where the model judges, the write, the gate. Saturday starts by picking one |

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

### Lab 2b: the LangGraph chat, and shipping it

A router, three specialists (orders, policy, desk) and a person at the gate, over the same MCP server. The scaffold, the chat page and the container are given; three decisions are yours, each with a check that says when it is done. Read [`docs/GRAPH.md`](./docs/GRAPH.md) first.

| Blank | Ships as | Done when |
|---|---|---|
| `ROUTING_RULES` | empty: the router guesses | five questions reach the specialist you intended, first hop, three runs out of three |
| `needs_person()` | stops every write | an internal note runs, "mark resolved" stops, anything that moves money stops |
| `MAX_HOPS` | one | a question needing the order and the policy gets both in one turn |

```bash
python labs/lab_2b_multiagent.py            # chat in the terminal, as agent.priya
python labs/lab_2b_multiagent.py --web      # the chat page, http://127.0.0.1:7866
docker build -t fde-chat .                  # the same page as one container
```

The container takes the key and a `CHAT_SECRET` from the environment and refuses to start on `0.0.0.0` without the secret. Nothing secret goes in the image; `.dockerignore` keeps `.env` out. The AWS steps are at the end of `docs/GRAPH.md`.

## For the business track

Half the room runs engagements without writing code. Your wedge is the same wedge — configured on the agent canvas during the Saturday lab, judged on the same eval contract, defended in the same readout on Sunday. The discovery lab, the artefact templates and the golden set are yours as much as the engineers'; the Python labs are there to read, and your pair runs them with you.

## Getting updates

```bash
git pull
```

Run it at the start of every session. Fixes and the later labs land during the weekend.

- **Lab 3 refused the golden set on Windows?** `git pull` fixes it: the freeze check now ignores line endings. Do not run `--unfreeze` to get past it; that re-freezes on the wrong hash with your name on it. If you already did, run `git checkout -- golden/frozen.sha256 golden/FREEZE_LOG.md` before you pull.
- **Starting lab 2b?** `pip install -r requirements-graph.txt` once, after the pull.

## Stuck?

Read [`FAQ.md`](./FAQ.md) first — it covers the common errors verbatim. Then ask in the cohort room at [study.modernaipro.com](https://study.modernaipro.com). If Python itself is fighting you, the browser **Lab Bench** at [study.modernaipro.com/learn/lab](https://study.modernaipro.com/learn/lab) runs the same files with nothing to install.
