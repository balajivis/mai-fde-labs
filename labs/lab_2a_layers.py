# -*- coding: utf-8 -*-
"""Lab 2a — FROM REQUIREMENTS TO THE EIGHT LAYERS

Modern AI Pro · FDE Field Kit · Day 2 · after the wedge (thirty minutes)

Lab 2 stage 6 hands you Calder & Rowe's Integration Map pre-marked, because
the kit knows that customer. Your customer is not in the kit. This lab takes
the business requirements you actually have — your Engagement Brief from
Friday, or a brief pasted in — asks the questions a map needs that the brief
does not answer, and then writes the map and the workflow for you to argue
with. The model drafts; you own every cell.

    STAGE 1   THE BRIEF       read the requirements; for each of the eight layers,
                              what the brief already settles and what it leaves open
    STAGE 2   THE INTERVIEW   the model asks only for the open layers (six questions
                              at most). You answer as the customer, or from your notes.
                              An empty answer is recorded as an open question — honestly.
    STAGE 3   THE MAP         build / connect / never for all eight layers, the identity
                              table, what we never touch → reports/<customer>-integration-map.md
                              and the eight-layer sheet reports/<customer>-layers.svg
    STAGE 4   THE WORKFLOW    one of the five reference shapes, its boxes named for this
                              customer: trigger, fixed steps, where the model judges, the
                              write, the gate, the rule → reports/<customer>-flow.svg
                              (rendered by docs/flows/build_flows.py, so it matches the sheets)

    python labs/lab_2a_layers.py                              uses reports/engagement-brief.md if lab 1 wrote one
    python labs/lab_2a_layers.py --brief my-customer.md       any Markdown or text file
    python labs/lab_2a_layers.py --text "We run a ..."        a one-paragraph brief
    python labs/lab_2a_layers.py --answers answers.json       {"HITL": "...", "Knowledge": "..."} skips the typing
    python labs/lab_2a_layers.py --questions 4                fewer questions

Piped input (CI, `echo "" | python ...`) runs on the kit's Calder & Rowe brief with
the kit's answers, so the instructor and the student see the same map.

Two things the model is told it may not do, and a check that it did not:
every layer gets exactly one of the three words, and "build" needs a reason the
customer does not already have it. A map with eight "build"s is a product
pitch, not an integration map. The flow must have one or two amber boxes and
at least one gated write, or the file is not written and the lab says why.

Nothing here is specific to Calder & Rowe except the fallback data. Point it at
your own brief on Monday.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.markup import escape                                        # noqa: E402
from rich.table import Table                                          # noqa: E402

from _kit import Stage, banner, chat, client, say, stages              # noqa: E402


def P(s: str) -> str:
    """One paragraph: collapse the source indentation so rich wraps it cleanly."""
    return " ".join(s.split())

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "artefacts" / "02-integration-map.md"
REPORTS = ROOT / "reports"                     # gitignored — your output, not the kit's
DEFAULT_BRIEF = REPORTS / "engagement-brief.md"
FLOWS_DIR = ROOT / "docs" / "flows"

LAYERS = ["UI", "Graph", "Integrations", "Knowledge", "Memory", "HITL", "Eval", "Observability"]
MARKS = ("build", "connect", "never")
KINDS = ("trigger", "step", "model", "write", "end")

LAYER_MEANING = """\
UI             where a person sees what the agent did (a ticket comment, a side panel, a queue, a dashboard). Slack and email are triggers out, not UI.
Graph          the flow: trigger → fixed steps → the one or two boxes where the model judges → the write → who finishes.
Integrations   the customer's systems the agent calls, over MCP, scoped per user. Who exposes them and as which identity.
Knowledge      what it reads but never edits (policies, past tickets, docs); how retrieval is scoped before search.
Memory         what it keeps between runs, and about whom. "Nothing" is a valid and often right answer for a pilot.
HITL           which actions stop for a named person, and who that person is.
Eval           the golden set, the judge, the regression gate — does the customer have one, or do we build it.
Observability  traces, the audit log, cost per task: where they live, who reads them, how long they are kept."""

# ── fallback data: the kit's own customer ────────────────────────────────────
# Used when no brief is given and lab 1 has not written one, and for every
# piped run. Facts match estate/data and the lab 2 header, so the map this
# produces can be checked against lab 2 stage 6.

FALLBACK_BRIEF = """\
# Engagement Brief — Calder & Rowe

Calder & Rowe distributes commercial kitchen equipment to restaurants and institutions across
three regions (west, central, east). The service desk handles about 600 tickets a quarter in
HelpTrack, their on-prem ticketing system. Dana Okafor runs operations; Marcus Lindqvist is the
CFO; Ruth Castellanos owns IT security.

Problem, in Dana's words: "Every ticket waits for a senior agent to read the warranty terms before
anyone replies. Our first response is slow and our juniors guess the category."

Workflow today: a ticket arrives, an agent opens the order and the customer record, finds the policy
on the shared drive, drafts a reply, sets the category and priority, and escalates anything involving
money to Ruth or Marcus.

The wedge: first-response drafting and triage. The system reads the ticket, looks up the order and
customer, finds the governing policy, drafts a reply, proposes category and priority, and writes the
draft back as an internal comment. A desk agent sends the reply. Credits, refunds and replacements
stay with a named person.

North star: first-response time, 26 hours today, target 4 hours. ROI: $31 a ticket today.

Constraints: data stays on-prem (US); the east region's policy addendum is restricted; HelpTrack
has no API beyond what IT exposes; there is no labelled dataset today.
"""

FALLBACK_ANSWERS = {
    "UI": "Agents live in the HelpTrack ticket view. The draft should appear as an internal comment there; "
          "no new screens in the pilot. Supervisors would want a daily list of escalations, which can be a saved filter.",
    "Graph": "New ticket → read it → order and customer → policy for the region → draft + category + priority → "
             "internal comment → escalate anything with money. One ticket at a time, then the morning backlog as a batch.",
    "Integrations": "HelpTrack tickets, the order book and customer records are all on-prem. Ruth will expose read, "
                    "add_comment and set_ticket through a service account per desk agent, scoped to that agent's regions. "
                    "No direct database access.",
    "Knowledge": "About forty policy documents as PDFs on a share, owned by Dana's team. The east addendum must only "
                 "be visible to east staff. Retrieval has to filter by region before it searches.",
    "Memory": "Nothing between tickets in the pilot. Ruth does not want a second store of customer data.",
    "HITL": "Credits, refunds and replacements need Ruth or Marcus to approve; the agent may only propose and name the "
            "policy. Ticket status stays with the desk agent. The agent never sends anything to a customer.",
    "Eval": "No labelled set today. Dana can give two senior agents for a day to label about 180 past tickets. "
            "They want a weekly check before any prompt change goes live.",
    "Observability": "HelpTrack keeps an append-only audit log that only admins read. Marcus wants cost per ticket "
                     "monthly. Retention follows their DAT-RETENTION policy; Ruth will confirm the number of days.",
    "Identity": "viewer.sam (viewer, west, no PII, read only); agent.priya (agent, west and central, sees PII, "
                "can comment and set fields); agent.jonah (agent, east); admin.ruth (admin, all regions, "
                "plus credits and replacements).",
}

STATE: dict = {"brief": "", "coverage": {}, "answers": {}, "map": {}, "flow": {}, "slug": "customer"}


# ── helpers ──────────────────────────────────────────────────────────────────

def read_brief(args) -> str:
    if args.text:
        return args.text.strip()
    if args.brief:
        return Path(args.brief).read_text(encoding="utf-8")
    if DEFAULT_BRIEF.exists():
        say(f"  [dim]using {DEFAULT_BRIEF.relative_to(ROOT)} (lab 1 wrote it)[/dim]")
        return DEFAULT_BRIEF.read_text(encoding="utf-8")
    say("  [dim]no brief given and lab 1 has not written one — using the kit's Calder & Rowe brief[/dim]")
    return FALLBACK_BRIEF


def ask_json(cli, system: str, user: str, label: str) -> dict:
    out = chat(cli, [{"role": "system", "content": system}, {"role": "user", "content": user}],
               label=label, response_format={"type": "json_object"})
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        say(f"  [red]the model did not return JSON for {label}; raw output below[/red]\n{escape(out[:600])}")
        return {}


def slugify(name: str) -> str:
    keep = "".join(ch.lower() if ch.isalnum() else "-" for ch in name.strip())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-") or "customer"


def ask_student(question: str) -> str:
    try:
        return input("    you > ").strip()
    except EOFError:
        return ""


# ── stage 1 · the brief ──────────────────────────────────────────────────────

def stage_brief(cli) -> None:
    brief = STATE["brief"]
    shown = brief if len(brief) <= 1400 else brief[:1400] + "\n…"
    say(f"[dim]{escape(shown)}[/dim]\n")
    system = ("You are a forward deployed engineer reading a customer's engagement brief before drawing their "
              "integration map. The eight layers of a production agent are:\n\n" + LAYER_MEANING +
              "\n\nFor each layer say whether the brief SETTLES it (enough to write build/connect/never and "
              "say what it is) or leaves it OPEN, and quote or closely paraphrase what the brief says. "
              "Also name the customer and the wedge in one line each. Return JSON only:\n"
              '{"customer": "...", "wedge": "...", "layers": {"UI": {"settled": true, "from_brief": "..."}, ...}} '
              "with all eight layer names as keys. Do not invent facts the brief does not contain.")
    out = ask_json(cli, system, brief, "coverage")
    layers = out.get("layers", {}) if isinstance(out, dict) else {}
    STATE["coverage"] = {k: layers.get(k, {"settled": False, "from_brief": ""}) for k in LAYERS}
    STATE["customer"] = out.get("customer", "the customer")
    STATE["wedge"] = out.get("wedge", "")
    STATE["slug"] = slugify(STATE["customer"])
    t = Table(title=f"{STATE['customer']} · what the brief settles", show_lines=False)
    t.add_column("layer", style="bold")
    t.add_column("settled")
    t.add_column("from the brief", max_width=90)
    for k in LAYERS:
        row = STATE["coverage"][k]
        mark = "[green]yes[/green]" if row.get("settled") else "[yellow]open[/yellow]"
        t.add_row(k, mark, escape(str(row.get("from_brief", ""))))
    say(t)
    open_n = sum(1 for k in LAYERS if not STATE["coverage"][k].get("settled"))
    say(f"  wedge: [italic]{escape(STATE['wedge'])}[/italic]\n  {open_n} of 8 layers open → stage 2 asks about those.")


# ── stage 2 · the interview ──────────────────────────────────────────────────

def stage_interview(cli) -> None:
    open_layers = [k for k in LAYERS if not STATE["coverage"][k].get("settled")]
    n = STATE["max_q"]
    system = ("You are a forward deployed engineer in a discovery call. The eight layers:\n\n" + LAYER_MEANING +
              f"\n\nAsk at most {n} questions, each one aimed at ONE layer that the brief leaves open, plus one "
              "question about identity (who will call the agent, their roles, regions, whether they may see PII "
              "and write) if the brief does not say. Short, concrete, answerable by an operations manager — "
              "not a questionnaire. Return JSON only: "
              '{"questions": [{"layer": "HITL", "question": "..."}]} where layer is one of the eight names or "Identity".')
    user = (f"Customer: {STATE['customer']}\nWedge: {STATE['wedge']}\n"
            f"Open layers: {', '.join(open_layers) or 'none'}\n\nBrief:\n{STATE['brief']}")
    out = ask_json(cli, system, user, "questions")
    questions = [q for q in out.get("questions", []) if isinstance(q, dict) and q.get("question")][:n]
    if not questions:
        say("  [dim]the model had nothing to ask; the brief settles every layer[/dim]")
        return
    interactive = sys.stdin.isatty()
    preset = STATE["preset_answers"]
    say(f"  {len(questions)} questions. Answer as the customer would, or from your notes. "
        "Enter on an empty line records it as an open question.\n")
    for i, q in enumerate(questions, 1):
        layer = q.get("layer", "?")
        say(f"  [bold]{i}. [{escape(str(layer))}][/bold] {escape(q['question'])}")
        if preset and layer in preset:
            ans = preset[layer]
            say(f"    [dim]you > {escape(ans[:160])}{'…' if len(ans) > 160 else ''}[/dim]")
        elif interactive:
            ans = ask_student(q["question"])
        else:
            ans = FALLBACK_ANSWERS.get(layer, "")
            say(f"    [dim]you > {escape(ans[:160]) if ans else '(no answer on file)'}[/dim]")
        STATE["answers"][q["question"]] = {"layer": layer, "answer": ans or "OPEN — not answered; ask the customer"}
    unanswered = sum(1 for a in STATE["answers"].values() if a["answer"].startswith("OPEN"))
    say(f"\n  recorded {len(STATE['answers'])} answers, {unanswered} left open")


# ── stage 3 · the map ────────────────────────────────────────────────────────

def validate_map(m: dict) -> list[str]:
    problems = []
    rows = {r.get("layer"): r for r in m.get("layers", []) if isinstance(r, dict)}
    for k in LAYERS:
        r = rows.get(k)
        if not r:
            problems.append(f"layer {k} missing")
            continue
        if r.get("mark") not in MARKS:
            problems.append(f"{k}: mark {r.get('mark')!r} is not build/connect/never")
        if not r.get("what"):
            problems.append(f"{k}: no description")
    builds = [k for k, r in rows.items() if r.get("mark") == "build"]
    if len(builds) == 8:
        problems.append("eight builds — that is a product pitch, not an integration map")
    return problems


def write_map_md(m: dict) -> Path:
    rows = {r["layer"]: r for r in m["layers"]}
    lines = []
    for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        replaced = False
        for k in LAYERS:
            if line.startswith(f"| {k} | |"):
                r = rows[k]
                owner = r.get("owner") or "_unknown_"
                openq = f" · open: {r['open_question']}" if r.get("open_question") else ""
                lines.append(f"| {k} | **{r['mark']}** | {r['what']}{openq} | {owner} |")
                replaced = True
                break
        if replaced:
            continue
        if line.startswith("*Calder & Rowe"):
            lines.append(f"*{m.get('customer', STATE['customer'])} · {m.get('wedge', STATE['wedge'])} · "
                         f"drafted by lab_2a_layers.py on {date.today().isoformat()} — every cell is yours to overrule*")
        elif line.strip() == "| | | | | |":
            ident = m.get("identity") or []
            if not ident:
                lines.append("| _not yet known_ | | | | |")
            for u in ident:
                lines.append(f"| {u.get('who', '')} | {u.get('role', '')} | {u.get('regions', '')} | "
                             f"{u.get('sees_pii', '')} | {u.get('can_write', '')} |")
        elif line.strip() == "-" :
            for item in m.get("never") or ["_nothing recorded — that itself is a finding_"]:
                lines.append(f"- {item}")
        elif line.startswith("Where the audit log lives"):
            lines.append(line + (m.get("audit") or "_open — ask IT_"))
        elif line.startswith("*Sign-off:*"):
            openqs = [f"- **{r['layer']}** — {r['open_question']}" for r in m["layers"] if r.get("open_question")]
            openqs += [f"- {q} ({a['layer']})" for q, a in STATE["answers"].items() if a["answer"].startswith("OPEN")]
            if openqs:
                lines.append("## Open questions for the customer\n")
                lines.extend(openqs)
                lines.append("")
            lines.append(line)
        else:
            lines.append(line)
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"{STATE['slug']}-integration-map.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# the eight-layer sheet: same palette as docs/flows and docs/wedge
_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
_MARK_STYLE = {
    "build":   dict(fill="#f4be3e", stroke="#b8860b", text="#1a1713", word="BUILD"),
    "connect": dict(fill="#e2f0ee", stroke="#2f6f68", text="#1a1713", word="CONNECT"),
    "never":   dict(fill="#fff6f4", stroke="#c0392b", text="#c0392b", word="NEVER"),
}


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _wrap(s: str, chars: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(" ".join(str(s).split()), chars)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max(0, chars - 1)] + "…"
    return lines


def write_layers_svg(m: dict) -> Path:
    W, cols, card_w, card_h, gap, top, left = 1180, 4, 265, 236, 20, 96, 28
    rows_n = 2
    H = top + rows_n * card_h + (rows_n - 1) * gap + 70
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{_FONT}">',
         f'<rect width="{W}" height="{H}" fill="#f6f4ef"/>',
         f'<text x="{left}" y="38" font-size="20" font-weight="700" fill="#1a1713">{_esc(m.get("customer", STATE["customer"]))} · the eight layers</text>',
         f'<text x="{left}" y="62" font-size="13" fill="#6b6358">{_esc(m.get("wedge", STATE["wedge"]))}</text>',
         f'<text x="{W - 28}" y="38" font-size="11" fill="#a29b8c" text-anchor="end">Modern AI Pro · FDE Field Kit · lab 2a · {date.today().isoformat()}</text>']
    rows = {r["layer"]: r for r in m["layers"]}
    for i, k in enumerate(LAYERS):
        r = rows[k]
        st = _MARK_STYLE[r["mark"]]
        x = left + (i % cols) * (card_w + gap)
        y = top + (i // cols) * (card_h + gap)
        p.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="10" fill="#ffffff" stroke="#c9c3b5"/>')
        p.append(f'<text x="{x + 16}" y="{y + 30}" font-size="16" font-weight="700" fill="#1a1713">{_esc(k)}</text>')
        pill_w = 20 + 8 * len(st["word"])
        p.append(f'<rect x="{x + card_w - 16 - pill_w}" y="{y + 14}" width="{pill_w}" height="22" rx="11" fill="{st["fill"]}" stroke="{st["stroke"]}"/>')
        p.append(f'<text x="{x + card_w - 16 - pill_w / 2}" y="{y + 29}" font-size="11" font-weight="700" fill="{st["text"]}" text-anchor="middle">{st["word"]}</text>')
        yy = y + 56
        for ln in _wrap(r.get("what", ""), 36, 5):
            p.append(f'<text x="{x + 16}" y="{yy}" font-size="12" fill="#1a1713">{_esc(ln)}</text>')
            yy += 17
        yy = y + card_h - 54
        p.append(f'<line x1="{x + 16}" y1="{yy - 14}" x2="{x + card_w - 16}" y2="{yy - 14}" stroke="#ece9e1"/>')
        for ln in _wrap(f"owner · {r.get('owner') or 'unknown'}", 38, 1):
            p.append(f'<text x="{x + 16}" y="{yy}" font-size="11" font-weight="600" fill="#6b6358">{_esc(ln)}</text>')
        if r.get("open_question"):
            for j, ln in enumerate(_wrap("open · " + r["open_question"], 40, 2)):
                p.append(f'<text x="{x + 16}" y="{yy + 17 + j * 15}" font-size="11" fill="#8a6508">{_esc(ln)}</text>')
    # legend
    ly = H - 30
    lx = left
    for key in MARKS:
        st = _MARK_STYLE[key]
        p.append(f'<rect x="{lx}" y="{ly - 11}" width="14" height="14" rx="3" fill="{st["fill"]}" stroke="{st["stroke"]}"/>')
        label = {"build": "build — we write it", "connect": "connect — it exists; we integrate over MCP",
                 "never": "never — we do not touch it, and the map says why"}[key]
        p.append(f'<text x="{lx + 20}" y="{ly}" font-size="11" fill="#6b6358">{label}</text>')
        lx += 60 + 6.2 * len(label)
    p.append("</svg>")
    out = REPORTS / f"{STATE['slug']}-layers.svg"
    out.write_text("\n".join(p) + "\n", encoding="utf-8")
    return out


def stage_map(cli) -> None:
    qa = "\n".join(f"- [{a['layer']}] Q: {q}\n  A: {a['answer']}" for q, a in STATE["answers"].items()) or "(none)"
    system = ("You are a forward deployed engineer writing the Integration Map (Deliverable II) for a pilot. "
              "The eight layers:\n\n" + LAYER_MEANING + "\n\n"
              "For EACH of the eight layers give exactly one of three marks — build (we write it; say why the customer "
              "does not already have it), connect (it exists; we integrate over MCP), never (we do not touch it, and why) — "
              "plus what it is at this customer in their words, the owner on their side if named, and one open question "
              "if something is still unknown. Then the identity table (who calls the agent, role, regions, sees PII, can write), "
              "the list of things we never touch and why, and where the audit log lives. "
              "Do not invent owners, systems or numbers that neither the brief nor the answers contain; write null or an "
              "open question instead. Return JSON only:\n"
              '{"customer": "...", "wedge": "...", '
              '"layers": [{"layer": "UI", "mark": "connect", "what": "...", "owner": "... or null", "open_question": "... or null"}, ... all eight in order], '
              '"identity": [{"who": "...", "role": "...", "regions": "...", "sees_pii": "yes/no/unknown", "can_write": "yes/no/unknown"}], '
              '"never": ["..."], "audit": "..."}')
    user = f"Customer: {STATE['customer']}\nWedge: {STATE['wedge']}\n\nBrief:\n{STATE['brief']}\n\nInterview:\n{qa}"
    m = ask_json(cli, system, user, "map")
    problems = validate_map(m)
    if problems:
        say("  [red]the draft map fails the kit's checks; nothing written:[/red]")
        for pr in problems:
            say(f"    ✗ {escape(pr)}")
        say("  re-run the stage; if it fails twice, the brief is the problem, not the model")
        return
    for r in m["layers"]:
        for key in ("owner", "open_question"):
            if r.get(key) in (None, "null", "None"):
                r[key] = ""
    STATE["map"] = m
    t = Table(title="the map — argue with every row")
    t.add_column("layer", style="bold")
    t.add_column("mark")
    t.add_column("what it is here", max_width=70)
    t.add_column("owner", max_width=22)
    colour = {"build": "yellow", "connect": "cyan", "never": "red"}
    for r in m["layers"]:
        t.add_row(r["layer"], f"[{colour[r['mark']]}]{r['mark']}[/{colour[r['mark']]}]",
                  escape(r["what"]), escape(r.get("owner") or "—"))
    say(t)
    marks = [r["mark"] for r in m["layers"]]
    say(f"  build ×{marks.count('build')} · connect ×{marks.count('connect')} · never ×{marks.count('never')}")
    md = write_map_md(m)
    svg = write_layers_svg(m)
    say(f"  [green]saved →[/green] {md.relative_to(ROOT)}\n  [green]saved →[/green] {svg.relative_to(ROOT)}  (open it in a browser)")


# ── stage 4 · the workflow ───────────────────────────────────────────────────

def validate_flow(f: dict) -> list[str]:
    problems = []
    nodes = f.get("nodes") or []
    if not 4 <= len(nodes) <= 7:
        problems.append(f"{len(nodes)} boxes; a flow has 4 to 7")
    kinds = [n.get("kind") for n in nodes if isinstance(n, dict)]
    if any(k not in KINDS for k in kinds):
        problems.append(f"unknown box kind in {kinds}")
    if kinds and kinds[0] != "trigger":
        problems.append("the first box must be the trigger")
    if not 1 <= kinds.count("model") <= 2:
        problems.append(f"{kinds.count('model')} amber boxes; the model judges in one or two, never zero, never more")
    if "write" not in kinds:
        problems.append("no write box — then what does the agent change? (a report counts as a write)")
    g = f.get("gate")
    if not g:
        problems.append("no gate — every write meets one (rule 4)")
    elif not isinstance(g.get("at"), int) or not 0 <= g["at"] < len(nodes):
        problems.append("gate.at must index a box")
    if not f.get("rule"):
        problems.append("no one-line rule (what the model never does)")
    if f.get("shape") not in (1, 2, 3, 4, 5):
        problems.append("shape must be 1–5")
    return problems


def stage_flow(cli) -> None:
    flows_md = (ROOT / "docs" / "FLOWS.md").read_text(encoding="utf-8")
    table = flows_md.split("## The map the five sit on")[0]
    system = ("You are a forward deployed engineer choosing the workflow shape for a pilot. The five reference shapes "
              "and the rules they share:\n\n" + table + "\n\nRules: the model decides in one or two boxes and everything "
              "else is code; scope before search; untrusted input never chooses a tool; every write meets a gate with a "
              "named person for anything that moves money or goods; earn the bigger shape — pick 5 only if the brief "
              "honestly needs it.\n\nPick ONE shape (1–5) and draw it for this customer as 4 to 7 boxes in order. "
              'kind is one of trigger, step, model, write, end; "lines" is the box label as one or two short lines '
              '(max 18 characters each); "tool" is the system or tool under the box (max 32 chars); "edge" is an optional '
              "arrow label. The gate sits at the index of the write box, names the condition (two short lines) and the "
              "person (two short lines), and back_to is the index of the box that resumes after approval. "
              "Return JSON only:\n"
              '{"shape": 1, "title": "...", "one_liner": "...", "nodes": [{"kind": "trigger", "lines": ["...", "..."], '
              '"tool": "...", "edge": null}, ...], "gate": {"at": 4, "label": ["...", "..."], "who": ["...", "..."], '
              '"back_to": 5}, "rule": "one sentence: what the model never does here"}')
    m = STATE["map"]
    graph = next((r["what"] for r in m.get("layers", []) if r["layer"] == "Graph"), "")
    user = (f"Customer: {STATE['customer']}\nWedge: {STATE['wedge']}\nGraph layer from the map: {graph}\n"
            f"HITL layer: {next((r['what'] for r in m.get('layers', []) if r['layer'] == 'HITL'), '')}\n\n"
            f"Brief:\n{STATE['brief']}")
    f = ask_json(cli, system, user, "flow")
    problems = validate_flow(f)
    if problems:
        say("  [red]the draft flow breaks the rules the five share; nothing written:[/red]")
        for pr in problems:
            say(f"    ✗ {escape(pr)}")
        return
    for n in f["nodes"]:
        n["lines"] = [str(x)[:20] for x in (n.get("lines") or [""])[:2]]
        if n.get("tool") is None:
            n.pop("tool", None)
        if n.get("edge") in (None, "null"):
            n.pop("edge", None)
    f["gate"]["label"] = [str(x)[:20] for x in f["gate"].get("label", [])[:2]]
    f["gate"]["who"] = [str(x)[:20] for x in f["gate"].get("who", [])[:2]]
    STATE["flow"] = f
    say(f"  shape [bold]{f['shape']}[/bold] · {escape(f['title'])}\n  [italic]{escape(f['one_liner'])}[/italic]\n")
    colour = {"trigger": "white", "step": "dim", "model": "yellow", "write": "red", "end": "green"}
    for i, n in enumerate(f["nodes"]):
        tag = f"[{colour[n['kind']]}]{n['kind']:7}[/{colour[n['kind']]}]"
        say(f"    {i}  {tag} {escape(' / '.join(n['lines'])):28} [dim]{escape(n.get('tool', ''))}[/dim]")
    g = f["gate"]
    say(f"    gate at {g['at']}: {escape(' '.join(g['label']))} → {escape(' '.join(g['who']))}"
        f"{' → resumes at ' + str(g['back_to']) if g.get('back_to') is not None else ''}")
    say(f"  rule: [bold]{escape(f['rule'])}[/bold]")
    sys.path.insert(0, str(FLOWS_DIR))
    from build_flows import render  # noqa: PLC0415 — the sheets' own renderer, so this matches them
    shape = dict(n=str(f["shape"]), title=f["title"], one_liner=f["one_liner"], nodes=f["nodes"],
                 gate=f["gate"], rule=f["rule"])
    out = REPORTS / f"{STATE['slug']}-flow.svg"
    out.write_text(render(shape), encoding="utf-8")
    dump = REPORTS / f"{STATE['slug']}-flow.json"
    dump.write_text(json.dumps(shape, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say(f"\n  [green]saved →[/green] {out.relative_to(ROOT)}\n  [green]saved →[/green] {dump.relative_to(ROOT)}  "
        "(the dict for docs/flows/build_flows.py SHAPES, if you want it on the shared sheet)")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Lab 2a — from requirements to the eight layers")
    ap.add_argument("--brief", help="a Markdown/text brief (default: reports/engagement-brief.md if lab 1 wrote one)")
    ap.add_argument("--text", help="the brief as one string")
    ap.add_argument("--answers", help='JSON file {"HITL": "...", "Identity": "..."} answering by layer')
    ap.add_argument("--questions", type=int, default=6, help="max questions in stage 2 (default 6)")
    args = ap.parse_args()

    banner("Modern AI Pro · FDE Field Kit · Lab 2a", "From requirements to the eight layers")
    cli = client()
    STATE["brief"] = read_brief(args)
    STATE["max_q"] = max(1, args.questions)
    STATE["preset_answers"] = json.loads(Path(args.answers).read_text(encoding="utf-8")) if args.answers else {}
    if not sys.stdin.isatty() and not args.answers and STATE["brief"] == FALLBACK_BRIEF:
        STATE["preset_answers"] = FALLBACK_ANSWERS

    stages(cli, [
        Stage("THE BRIEF — what the requirements already settle",
              P("""A brief is written for the buyer; a map is written for the builder. The same page that
              nails the ROI line usually says nothing about who may see PII or whether anyone keeps a
              golden set. Before you ask a single question, find out which of the eight layers the brief
              already answers, so the customer's time goes only on the gaps."""),
              stage_brief,
              P("""Every 'open' row is a question for the customer, not a guess for you to make. The
              layers a brief most often leaves open are Memory, Eval and Observability — the three
              nobody is selling and everybody is billed for later.""")),
        Stage("THE INTERVIEW — ask only for the gaps",
              P("""One question per open layer, plus identity. The discipline is to let an empty answer stand
              as an open question instead of filling it with something plausible: a map that says 'unknown'
              in the Eval row is honest, and the customer can fix it on Monday. A map that says 'build' in
              every row cannot be argued with and will not be read."""),
              stage_interview,
              P("""The answers you just gave are the only facts the next stage may use beyond the brief.
              Watch whether it stays inside them — that is also the test you will run on every agent
              you ship: did it say anything the inputs do not support?""")),
        Stage("THE MAP — build, connect or never, eight times",
              P("""Deliverable II is the picture in docs/flows/00-eight-layers.svg with this customer's
              systems written into each layer and one of three words beside each. The kit checks the
              draft before it is written: all eight layers, a legal mark on each, and not eight builds.
              Then it fills artefacts/02-integration-map.md and draws the sheet."""),
              stage_map,
              P("""'connect' and 'never' are where the pilot's speed comes from: every system you do not
              have to build is one the customer already trusts. A 'build' row needs a sentence on why
              they do not have it; if you cannot write that sentence, it is a 'connect' you have not
              found the owner for yet.""")),
        Stage("THE WORKFLOW — one of the five shapes, in their words",
              P("""The Graph row of the map says what happens; the flow sheet says where. One of the five
              reference shapes, its boxes renamed for this customer, drawn by the same generator as
              docs/flows so you can hold it next to the kit's wedge. The check: one or two amber boxes,
              at least one write, a gate with a named person, a one-line rule."""),
              stage_flow,
              P("""If the model chose shape 5, ask it why shape 1 would lose; if you cannot answer with a
              number from the golden set, ship shape 1. On Monday, paste this JSON into
              docs/flows/build_flows.py and the customer's flow sits on the same page as the five.""")),
    ])


if __name__ == "__main__":
    main()
