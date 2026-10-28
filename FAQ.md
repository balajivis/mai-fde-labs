# FAQ — FDE Field Kit

**401, and the key looks right.** The key and the base URL travel together. A `mai_` key needs `OPENAI_BASE_URL` set to the class proxy; a personal `sk-` key needs that line absent. Both mixed combinations return a 401 that looks exactly like a bad key. Run `python labs/lab_0_setup.py` — it prints what Python actually loaded before you change anything.

**"This key's practice window has ended."** The FDE key covers the two weeks from Friday. A key from an earlier level does not work here; the FDE key arrived by email from Mahalakshmi before the weekend. Can't find it? Reply to that email.

**`Denied: agent.priya cannot issue_credit`.** Correct behaviour, not a bug. The permission check lives inside the estate function, not in the prompt, and `agent.priya` is an agent, not an admin. The lab that needs a credit issued is the lab about *approval queues* — a named person approves it, the agent never does.

**A west user can't see an east ticket, even by id.** Also correct. Scope is filtered before retrieval, so an out-of-scope id is indistinguishable from a missing one. That is the whole point of the access-trap cases in the golden set.

**The estate looks wrong — a ticket points at an order that doesn't exist.** It is meant to. About fifteen tickets reference orders that are not there, eight orders carry unknown SKUs, a dozen customers exist twice. Real estates look like this; the wedge has to cope. The full list of planted mess is in `estate/data/plants.json`.

**I changed the estate by accident.** `python -c "import sys; sys.path.insert(0,'labs'); import _estate; _estate.reset()"` — writes live in `estate/data/state.json` (gitignored), the generated files are never modified. `git pull` never clobbers your run.

**The eval lab refuses to run: "golden set changed since freeze".** Also on purpose. A golden set that moves is not a contract. If you added a case deliberately (Lab 4 does this), run with `--unfreeze` once and it re-freezes and logs the change.

**The lab dumps every stage at once instead of pausing.** You are piping input, so it runs non-interactively by design. Run it directly in a terminal to step with Enter.

**The approval prompt never appears and everything is denied.** Same cause — non-interactive runs fail closed on purpose.

**`ModuleNotFoundError: mcp`.** Re-run `pip install -r requirements.txt` inside the activated venv. The estate is served over MCP, so that package is not optional.

**The MCP server "hangs" when I run it by hand.** `python labs/estate_mcp.py` speaks MCP over stdin/stdout and waits for a client. That is normal. The labs spawn it for you; to talk to it from your editor, use the `mcp.json` snippet in the README.

**429 / burst limit.** The class lane is shared. The kit waits and retries once — let it.

**Python on this laptop is a lost cause.** Use the browser Lab Bench at [study.modernaipro.com/learn/lab](https://study.modernaipro.com/learn/lab).
