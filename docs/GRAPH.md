# Lab 2b — a small multi-agent chat, in LangGraph

One hour. The kit's wedge is one loop and stays one loop; this is the other shape the syllabus promised, "a graph outside, agents inside the nodes", built small enough to read in one sitting. You get the scaffold, the chat page and the container. You write the three decisions.

**Before anything: the poll.** Hands up if you have an AWS (or any cloud) account with a card on file, the CLI configured and a region picked. Fewer than half the room → the deploy is demonstrated once on screen in the go-live block and you ship yours after class from the recording. More than half → the deploy is the last fifteen minutes of this hour.

## Setup (five minutes)

```
git pull
pip install -r requirements-graph.txt
python labs/lab_2b_multiagent.py            # terminal chat, as agent.priya
python labs/lab_2b_multiagent.py --web      # the chat page at http://127.0.0.1:7866
```

Same key, same proxy, same estate server as every other lab. Three packages are added: `langgraph`, `langchain-openai`, `langchain-mcp-adapters`. The last one turns the MCP session's tool listing into LangChain tools, so the specialists use the customer's tools exactly as the customer describes them.

## What is in the box

```
          ┌──────────┐
   you ──▶│  router  │──▶ orders   get_order · list_orders · get_customer · find_customers
          │ (1 call) │──▶ policy   search_policies · get_policy
          │          │──▶ desk     get_ticket · list_tickets · add_comment · set_ticket  ← writes, gated
          │          │──▶ answer   no tools: reply with what the specialists found
          └──────────┘
      specialists hand back to the router; the router counts hops against MAX_HOPS
```

| Piece | Where | Given or yours |
|---|---|---|
| The graph: router, three ReAct specialists, answer node, conditional edges | `labs/lab_2b_multiagent.py` · `build_graph` | given |
| The gate: a LangGraph `interrupt` inside every write tool, resumed by a person | `labs/lab_2b_multiagent.py` · `_gated` | given |
| The runner: one MCP session, one event loop, a checkpointer per thread | `labs/lab_2b_multiagent.py` · `Runner` | given |
| The chat page: messages, hops, the gate card with Approve / Reject | `labs/_chat_web.py` | given |
| The container | `Dockerfile` · `.dockerignore` | given |
| **Blank 1 · the routing rules** | `ROUTING_RULES` | yours |
| **Blank 2 · which tool calls stop for a person** | `needs_person()` | yours |
| **Blank 3 · the hop budget** | `MAX_HOPS` | yours |

Scope is still the server's job. Ask the chat about T-30272 as `agent.priya` and the desk specialist is denied exactly as the wedge was. Nothing in the graph decides who may do what, and nothing you write in the blanks should try to.

## The three blanks

Fill them by hand, or with the assistant you use for code. Each has a check; the check is what "done" means.

### Blank 1 · `ROUTING_RULES`

The scaffold ships with no rules, so the router guesses. Ask it "can we credit the customer on T-30535?" and watch where it goes. Write the rules as sentences for the model: what goes to orders, what goes to policy, when the desk is needed (it is the only specialist that can read a ticket or write to one), when to answer at once, and what to do with a question nobody on the desk should answer.

**Check:** these five questions each reach the specialist you intended, first hop, three runs out of three.

| Question | Should reach |
|---|---|
| what is the status of T-30535? | desk |
| which orders does customer C-1041 have? | orders |
| what does the warranty policy say about walk-in coolers? | policy |
| thanks, that is all | answer |
| what is the card number on O-27595? | answer, with a refusal, no tool call |

### Blank 2 · `needs_person()`

The scaffold stops every write. Safe, slow, and the desk will switch it off within a week. Decide on three things: the risk tag (`_estate.RISK`: read, write, destructive), the arguments (an internal note is not a status change to resolved), and money. Anything destructive stops, always; that is not yours to relax.

**Check:** "add an internal note to T-30535 saying the customer called" runs without a gate. "mark T-30535 resolved" stops. Anything that would move money or goods stops, and the chat says who decides.

### Blank 3 · `MAX_HOPS`

One hop means a question that needs the order and the policy never gets both. Ten means a confused router runs up a bill. Pick the number, then justify it with the meter: `traces.jsonl` has every call.

**Check:** "is the cooler on O-27612 still under warranty?" needs orders and policy; it gets both and answers in one turn. The total tokens for that turn, from your traces, is a number you can say out loud.

## Why a graph here, and a loop in the wedge

The syllabus's coordination scorecard, in one table. Enterprises buy audit, control and debuggability before they buy cleverness; pick the smallest shape that gives those.

| Shape | Known in advance | Who decides the next step | Auditable as | Use it when |
|---|---|---|---|---|
| Loop (the wedge, lab 2) | the steps | code, with the model in one box | one trace per task | the process is known and the same every time |
| Graph, agents in nodes (this lab) | the nodes and edges | the router, within the edges you drew | one path through a drawn graph | several skills, one conversation, a person at the gate |
| Workflow engine | the stages | the engine, over days | a state machine with retries | runs that outlive a request: approvals, SLAs, escalation clocks |
| Events | the parties | nobody; each reacts | a log of events | many independent systems, no single owner of the flow |

Earn the bigger shape. If this chat does not beat the wedge on the golden set for the questions the desk actually asks, the wedge ships.

## Deploy (the last fifteen minutes, or after class)

One container, the key from the environment, a secret on the page.

```
docker build -t fde-chat .
docker run --rm -p 7866:7866 \
  -e OPENAI_API_KEY=<your practice key> \
  -e OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1 \
  -e CHAT_SECRET=$(openssl rand -hex 24) \
  fde-chat
```

Open `http://127.0.0.1:7866/?k=<CHAT_SECRET>`. The page keeps the secret in memory and strips it from the address bar.

On AWS the same image runs on App Runner (push to ECR, create a service from the image, set the three environment variables, port 7866) or on a small EC2 instance with Docker installed. Either way:

- **The key never goes in the image, the repo, or a Dockerfile `ENV` line.** `.dockerignore` already excludes `.env`; keep it that way.
- **No `CHAT_SECRET`, no page.** The server refuses to bind `0.0.0.0` without one. A chat on a practice key, reachable by anyone, is somebody else's token bill by Monday.
- **Scope travels with the container.** `ESTATE_USER` picks who the container acts as; a deployed chat as `admin.ruth` can issue credits if someone approves them. Deploy as the least user that does the job.
- **State is ephemeral.** `MemorySaver` and the estate's `state.json` live in the container; restart and they are gone. That is right for a demo and wrong for a pilot; a checkpointer on Postgres is the first change a real deploy makes.

## What to bring to the go-live block

The three blanks filled, the three checks passing, and one number: the tokens for the two-hop question. That is the chat's first line in the cost estimate from lab 1a.
