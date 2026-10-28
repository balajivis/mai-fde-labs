# -*- coding: utf-8 -*-
"""Lab 1 — THE DISCOVERY INTERVIEW

Modern AI Pro · FDE Field Kit · Day 1 · sessions ii–iv

Before you build anything for a customer you have to find out what is actually
wrong, and the people who know are busy, guarded, and will not volunteer the
thing that sinks the project. This lab makes you practise that.

The customer is Calder & Rowe, a commercial kitchen-equipment distributor.
Three people have agreed to thirty minutes each:

    Dana Okafor         runs the service desk. Three agents, 19 hours to a
                        first reply, and she is losing people.
    Marcus Lindqvist    the CFO. Knows what a ticket costs to the dollar and
                        thinks credits are leaking out the door.
    Ruth Castellanos    owns IT security. Cares who can see what, and whether
                        there is a record of it.

Each of them is holding one thing back. Not lying — they just will not say it
unless you ask a question that touches it. A real stakeholder does the same.

    SESSION ii   The interview.      You ask, they answer, the kit keeps the transcript.
    SESSION iii  ROI and the wedge.  Four cells (job, workflow, data, constraint)
                                     pulled from YOUR transcript — not the facts, what
                                     you actually asked. Then one line of arithmetic:
                                     ΔNorth Star × $ coefficient ÷ cost. If the payback
                                     is over 18 months the lab tells you to say so.
    SESSION iv   The engagement brief. One page, filled from the transcript and the
                                     number, saved to reports/. The thing you sign.

    python labs/lab_1_discovery.py          interview in the terminal
    python labs/lab_1_discovery.py --web    the same in the browser (port 7861)

Piped input (CI, `echo "" | python ...`) runs a scripted six-question interview
so the file always exercises every stage without a person at the keyboard.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.markup import escape                                        # noqa: E402
from rich.panel import Panel as RichPanel                             # noqa: E402

from _kit import banner, chat, client, meter, rule, say               # noqa: E402
from _web import (Knob, Panel, answer, note, port_from, presets,      # noqa: E402
                  section, serve, step, table, verdict, wants_web)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "artefacts" / "01-engagement-brief.md"
REPORTS = ROOT / "reports"                     # gitignored — your output, not the kit's


# ── the customer ─────────────────────────────────────────────────────────────
# Everything every persona knows. This is the public story — the kind of thing
# you would get from the sales handover. The interesting facts are further down,
# split by who holds them, because in a real company nobody holds all of it.

COMPANY = """\
You work at Calder & Rowe, a commercial kitchen-equipment distributor based in Dallas,
founded 1987, about 60 staff. You sell ovens, refrigeration, dishwashers and small wares
to restaurants, hotels and school kitchens across three sales regions: west, central and
east. About 180 active customer accounts; roughly 600 orders in the last 14 months. There
is a policy library of about 40 documents: warranty terms per manufacturer, the returns
policy, service SLAs, pricing tiers, data handling, the credit policy, installation guides.

The service desk takes about 600 tickets a quarter. Three agents work it: Tomas, Keisha
and Bill. First response averages 19 hours; the target in the SLA you sell is 4. Most of a
ticket is spent finding the order, the warranty terms and the right policy before anyone
can write a reply. The ticketing system is called HelpTrack. Busiest day is Monday, because
restaurant equipment breaks on weekends.
"""

# How every persona behaves, whoever they are. The two rules in capitals are the
# point of the lab: a stakeholder answers the question you asked, not the one
# you should have asked.
MANNER = """\
You are being interviewed by a forward-deployed engineer who may build something for
your company. You are busy and this is one of several meetings today. Answer like a real
person: first person, 2 to 5 sentences, plain speech, no bullet points, no headings.
Stay in character; never mention being an AI or a persona.

Answer the question that was asked. DO NOT VOLUNTEER NUMBERS THE INTERVIEWER HAS NOT
ASKED FOR. If asked something outside what you know, say who would know instead.

There is one thing you have not said yet (below, "What you only say when asked"). It is
not a secret and you are not hiding it on purpose — it simply has not come up. Reveal it
ONLY when a question touches that topic directly. Never raise it yourself, never hint at
it, and do not reveal it because the interviewer is being friendly or asks "anything else?".
"""

PERSONAS = {
    "dana": {
        "name": "Dana Okafor",
        "title": "Operations lead, service desk",
        "cares": "first-response time, agent burnout, her three agents",
        "facts": """\
You are Dana Okafor, operations lead. The desk is yours and so are the three agents.
What you know: a ticket takes an agent about 40 minutes of actual work, and 25 of those
minutes are hunting — opening the order in the sales system, finding which manufacturer's
warranty applies, finding the paragraph in the policy that governs it. Roughly 40% of
tickets are warranty questions, 25% are delivery or damage, the rest returns, pricing and
how-do-I questions. You tried canned replies in HelpTrack last year; nobody uses them
because the hard part is not the writing, it is the looking up. Keisha has told you she is
thinking of leaving, and you cannot hire at the rate you are losing people. You would
count a win as first response under 4 hours without adding a fourth agent. You do not
know what a ticket costs in dollars — Marcus does. You do not know where HelpTrack is
hosted or what the security rules are — Ruth does.
""",
        "hidden": "About half of the tickets arrive by PHONE, not email. The agent takes "
                  "the call, promises to follow up, and types it into HelpTrack afterwards — "
                  "usually badly: a line or two, often just 'see phone notes', no order "
                  "number. So half the tickets in the system have almost no text in them.",
        "triggers": "how tickets arrive (channels: email, phone, portal) · what a ticket looks "
                    "like when an agent opens it · why bodies are short or empty · data quality",
    },
    "marcus": {
        "name": "Marcus Lindqvist",
        "title": "CFO",
        "cares": "cost per ticket, credits leaking out the door, payback",
        "facts": """\
You are Marcus Lindqvist, CFO. You have run the numbers on the desk and you like numbers.
What you know: a ticket costs $31 in desk labour — about 40 minutes of agent time at a
loaded $46 an hour — which comes to roughly $75,000 a year across the 2,400 tickets. The
number that actually bothers you is credits: the desk issued about $180,000 of goodwill
credits last year, and you believe 10 to 15 percent of that was given because the agent
could not find the warranty terms and took the easy way out. You would fund a pilot from
the ops budget if it pays back inside a year. You are sceptical of anything sold as "AI";
you want to see the arithmetic. You do not know the technical setup — Ruth does — and you
do not know the desk's day-to-day — Dana does.
""",
        "hidden": "The board tightened spending after a CRM contract overran: this year, no "
                  "new software or SaaS contract above $25,000 a year can be signed without "
                  "board sign-off, and the board meets quarterly. Under $25,000 you can sign "
                  "it yourself.",
        "triggers": "how a purchase gets approved · procurement · who signs · contract size · "
                    "budget ceilings · what it would take to buy this",
    },
    "ruth": {
        "name": "Ruth Castellanos",
        "title": "IT security owner",
        "cares": "customer PII, who can see what, the audit trail",
        "facts": """\
You are Ruth Castellanos and you own IT security. What you know: tickets contain customer
PII — contact names, delivery addresses, and customers paste card numbers into emails more
often than anyone would like. Agents are regional: a west agent should never see an east
customer's tickets, and today that is enforced by HelpTrack's roles (viewer, agent, admin)
behind single sign-on. You want every read and every write logged with who did it; the
current audit log in HelpTrack is thin and you have been meaning to fix it. You were
burned two years ago by a vendor who asked for a full export of the ticket database "to
train on", and you said no; you will say no again to any tool that needs a copy of the
data. Credits and refunds should always need a named human. You do not know the cost
numbers — Marcus does.
""",
        "hidden": "HelpTrack is ON-PREMISE — it runs on a server in the Dallas office, not in "
                  "the cloud — and under contracts with two hotel groups and a school district, "
                  "customer data cannot leave the United States. Any model or service that "
                  "touches ticket text has to run in a US region, and nothing gets a bulk copy.",
        "triggers": "where HelpTrack runs / hosting · where data goes · which model provider or "
                    "cloud · region / data residency · integration (API vs export)",
    },
}

ORDER = ["dana", "marcus", "ruth"]


def system_prompt(key: str) -> str:
    p = PERSONAS[key]
    return (f"{COMPANY}\n{MANNER}\n{p['facts']}\n"
            f"What you only say when asked: {p['hidden']}\n")


# ── state that lives for the whole run ───────────────────────────────────────
# The transcript is a module-level list on purpose: the --web panel is
# stateless per request, and the student needs the interview to survive
# between clicks. Each persona also keeps its own history so follow-ups work
# ("you said 25 minutes — where does it go?").

TRANSCRIPT: list[dict] = []                       # {persona, q, a}
HISTORY: dict[str, list[dict]] = {k: [] for k in PERSONAS}


def ask_persona(cli, key: str, question: str) -> str:
    """One interview turn, through the kit's chat() so it is metered and traced."""
    HISTORY[key].append({"role": "user", "content": question})
    msgs = [{"role": "system", "content": system_prompt(key)}, *HISTORY[key]]
    reply = chat(cli, msgs, label=f"interview:{key}", max_tokens=300)
    HISTORY[key].append({"role": "assistant", "content": reply})
    TRANSCRIPT.append({"persona": key, "q": question, "a": reply})
    return reply


def transcript_text() -> str:
    if not TRANSCRIPT:
        return "(no interview yet)"
    lines = []
    for t in TRANSCRIPT:
        lines.append(f"FDE: {t['q']}\n{PERSONAS[t['persona']]['name']}: {t['a']}\n")
    return "\n".join(lines)


# ── session iii · the four cells ─────────────────────────────────────────────
# The four discovery cells are filled FROM THE TRANSCRIPT, not from the persona
# facts. If you never asked, the cell says so. That is the lesson: your notes are
# only as good as your questions.

CELLS = {
    "job": "the job to be done — what outcome the customer is paying for, in their words",
    "workflow": "the workflow today — who does what, in what order, how long it takes",
    "data": "the data — what systems and documents the work touches, and their condition",
    "constraint": "the constraints — budget, security, residency, approvals, anything that "
                  "bounds the solution",
}


def extract_cells(cli) -> dict:
    """Four cells, JSON, strictly from the transcript. 'not asked' is a valid answer."""
    msgs = [
        {"role": "system", "content":
            "You are an FDE's note-taker. You fill a discovery sheet ONLY from the interview "
            "transcript you are given. Never add facts you know about service desks in "
            "general. If the transcript does not cover a cell, write exactly 'not asked'. "
            "Quote numbers the stakeholders gave; attribute each to the person who said it. "
            "Return JSON with keys job, workflow, data, constraint — each a string of 1 to 4 "
            "sentences — and a key gaps: a list of short questions the FDE should have "
            "asked and did not."},
        {"role": "user", "content":
            "Cells:\n" + "\n".join(f"- {k}: {v}" for k, v in CELLS.items()) +
            "\n\nTranscript:\n" + transcript_text()},
    ]
    out = chat(cli, msgs, label="extract-cells", response_format={"type": "json_object"})
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {k: "(model returned non-JSON)" for k in CELLS} | {"gaps": []}


def check_surfaced(cli) -> dict:
    """Did the interview surface each hidden constraint? A grader call, not a keyword
    search — 'phone' in the transcript proves nothing if Dana was talking about
    customers phoning to chase. The grader is told what the constraints are; the
    student was not."""
    msgs = [
        {"role": "system", "content":
            "You grade an interview transcript. For each listed constraint decide whether "
            "the stakeholder actually STATED it in the transcript (not whether the FDE "
            "asked near it). Return JSON: an object keyed by persona id, each value "
            "{\"surfaced\": true|false, \"evidence\": \"the sentence from the transcript, "
            "or empty\"}."},
        {"role": "user", "content":
            "Constraints:\n" +
            "\n".join(f"- {k} ({PERSONAS[k]['name']}): {PERSONAS[k]['hidden']}" for k in ORDER) +
            "\n\nTranscript:\n" + transcript_text()},
    ]
    out = chat(cli, msgs, label="check-surfaced", response_format={"type": "json_object"})
    try:
        got = json.loads(out)
    except json.JSONDecodeError:
        got = {}
    return {k: got.get(k) or {"surfaced": False, "evidence": ""} for k in ORDER}


# ── session iii · ROI ────────────────────────────────────────────────────────
# One line: ΔNorth Star × $ coefficient ÷ cost. Three numbers, all of which the
# student should be able to defend with a sentence from the transcript. The
# defaults are what Dana and Marcus will tell you if you ask.

TICKETS_PER_YEAR = 2400           # Dana: ~600 a quarter
MINUTES_HUNTING = 25              # Dana: 25 of the 40 minutes is looking things up
LOADED_RATE = 46.0                # Marcus: $31 a ticket ≈ 40 min at $46/h loaded
DEFAULT_COST = 36_000.0           # build ~$30k + first-year run ~$6k — a guess, say so
BOARD_CAP = 25_000.0              # Marcus's hidden constraint, if you found it
HONEST_LINE_MONTHS = 18


def roi(delta_hours: float, rate: float, cost: float) -> dict:
    """Payback in months. The formula is deliberately too simple to hide behind."""
    annual = delta_hours * rate
    months = (cost / annual * 12) if annual > 0 else float("inf")
    return {"delta_hours": delta_hours, "rate": rate, "cost": cost,
            "annual_benefit": annual, "payback_months": months,
            "worth_it": months <= HONEST_LINE_MONTHS}


def roi_lines(r: dict) -> list[str]:
    out = [f"ΔNorth Star  {r['delta_hours']:,.0f} agent-hours a year "
           f"({TICKETS_PER_YEAR:,} tickets × {MINUTES_HUNTING} min, if you used the defaults)",
           f"× coefficient  ${r['rate']:,.0f}/hour loaded  =  ${r['annual_benefit']:,.0f} a year",
           f"÷ cost  ${r['cost']:,.0f} first year  →  payback {r['payback_months']:,.1f} months"]
    if r["worth_it"]:
        out.append(f"Under {HONEST_LINE_MONTHS} months. Worth proposing — on these numbers, "
                   "which you will have to defend.")
    else:
        out.append(f"Over {HONEST_LINE_MONTHS} months. This workflow may not be worth "
                   "automating — say so to the customer. An FDE who says 'don't build "
                   "this' gets the next call; one who sells it anyway does not.")
    if r["cost"] > BOARD_CAP:
        out.append(f"Note: ${r['cost']:,.0f} is above $25,000. If that is a SaaS contract, "
                   "Marcus cannot sign it alone this year — did he tell you that?")
    return out


# ── session iv · the brief ───────────────────────────────────────────────────

def draft_brief(cli, cells: dict, r: dict, fde_name: str = "(your name)") -> str:
    """Fill artefacts/01-engagement-brief.md from the transcript, the cells and the
    ROI line, in one call. The template's {{placeholders}} are the contract: the
    model fills them, it does not restructure the page."""
    template = TEMPLATE.read_text(encoding="utf-8")
    who = sorted({PERSONAS[t["persona"]]["name"] for t in TRANSCRIPT}) or ["nobody yet"]
    msgs = [
        {"role": "system", "content":
            "You are an FDE writing a one-page engagement brief. Fill EVERY {{placeholder}} "
            "in the template with content drawn from the transcript, the discovery cells and "
            "the ROI numbers. Keep the template's headings, tables, the blockquote and the "
            "closing sign-off sentence exactly as they are; replace only the placeholders. "
            "Where the transcript is silent, write 'not established in discovery' rather "
            "than inventing. Quote the customer where the template asks for their words. "
            "Return the completed markdown and nothing else."},
        {"role": "user", "content":
            f"customer: Calder & Rowe\nfde_name: {fde_name}\ndate: {date.today().isoformat()}\n"
            f"interviewees: {', '.join(who)}\n\n"
            f"Discovery cells:\n{json.dumps(cells, indent=2)}\n\n"
            f"ROI: {' | '.join(roi_lines(r))}\n\n"
            f"Transcript:\n{transcript_text()}\n\nTemplate:\n{template}"},
    ]
    brief = chat(cli, msgs, label="draft-brief", max_tokens=1800)
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "engagement-brief.md").write_text(brief + "\n", encoding="utf-8")
    (REPORTS / "interview-transcript.md").write_text(
        "# Interview transcript — Calder & Rowe\n\n" + transcript_text(), encoding="utf-8")
    return brief


# ── the scripted interview (piped input) ─────────────────────────────────────
# Six questions, two per person. Each second question is the one that touches
# the constraint; each first one is a fair opener that does not. Running this
# in CI measures the thing the lab claims: they hold it back until asked.

SCRIPTED = [
    ("dana", "Walk me through what happens from the moment a ticket comes in to the "
             "moment the first reply goes out."),
    ("dana", "How do tickets actually reach the desk — email, a web form, phone? And "
             "what does one look like when an agent opens it?"),
    ("marcus", "What does a ticket cost you today, and where does that money go?"),
    ("marcus", "If we proposed a tool for this, how would it get bought — who signs, "
               "and is there a ceiling?"),
    ("ruth", "What is in a ticket that you would consider sensitive, and who can see "
             "it today?"),
    ("ruth", "Where does HelpTrack run, and are there rules about where its data can go?"),
]


# ── terminal ─────────────────────────────────────────────────────────────────

def _say_reply(key: str, text: str) -> None:
    say(f"  [bold cyan]{PERSONAS[key]['name']}:[/bold cyan] {escape(text)}\n")


def _ask(prompt: str, default: str) -> str:
    """Prompt with a default; piped input takes the default (CI-safe)."""
    if not sys.stdin.isatty():
        return default
    got = input(f"  {prompt} [{default}] > ").strip()
    return got or default


def _pick_persona(current: str | None = None) -> str | None:
    say("  [dim]who:[/dim] " + " · ".join(
        f"[bold]{k}[/bold] — {PERSONAS[k]['name']}, {PERSONAS[k]['title'].lower()}"
        for k in ORDER))
    got = input("  pick one (or Enter to keep) > ").strip().lower()
    if not got and current:
        return current
    for k in ORDER:
        if got.startswith(k) or got.startswith(PERSONAS[k]["name"].split()[0].lower()):
            return k
    say("  [red]didn't catch that[/red]")
    return current


def interview(cli) -> None:
    rule("Session ii · The discovery interview")
    say(RichPanel(
        "You have three people and thirty minutes each. Ask about the work, not about AI. "
        "Each of them is holding one thing back that would change what you build — "
        "not hiding it, just waiting for the question that touches it.\n\n"
        "[bold]switch[/bold] changes who you are talking to · [bold]done[/bold] ends the "
        "interview · anything else is a question.",
        title="[bold]why[/bold]", title_align="left", border_style="blue", padding=(0, 2)))

    if not sys.stdin.isatty():
        say("[dim](no terminal — running the scripted six-question interview)[/dim]\n")
        for key, q in SCRIPTED:
            say(f"  [yellow]you → {PERSONAS[key]['name'].split()[0]}:[/yellow] {q}")
            _say_reply(key, ask_persona(cli, key, q))
        return

    key = _pick_persona("dana") or "dana"
    say(f"\n  [dim]talking to {PERSONAS[key]['name']} ({PERSONAS[key]['title']}) — "
        f"cares about {PERSONAS[key]['cares']}[/dim]\n")
    while True:
        try:
            q = input("  you > ").strip()
        except EOFError:
            break
        if not q:
            continue
        low = q.lower()
        if low in ("done", "quit", "q", "exit"):
            break
        if low.startswith("switch"):
            rest = low.replace("switch", "", 1).strip()
            key = (_pick_persona(key) if not rest else
                   next((k for k in ORDER if rest.startswith(k)), key)) or key
            say(f"  [dim]now talking to {PERSONAS[key]['name']} — "
                f"cares about {PERSONAS[key]['cares']}[/dim]\n")
            continue
        if low == "help":
            say("  [dim]ask a question · switch [dana|marcus|ruth] · done[/dim]")
            continue
        _say_reply(key, ask_persona(cli, key, q))
    if not TRANSCRIPT:
        say("  [yellow]No questions asked — running the scripted interview so the rest "
            "of the lab has something to work from.[/yellow]\n")
        for k, q in SCRIPTED:
            _say_reply(k, ask_persona(cli, k, q))


def discovery_cells(cli) -> dict:
    rule("Session iii · The four cells — from YOUR transcript")
    say(RichPanel(
        "Job · workflow · data · constraint. The model fills them from the transcript "
        "only — what the stakeholders said to you, not what is true about the company. "
        "A cell that reads 'not asked' is the honest score of your interview.",
        title="[bold]why[/bold]", title_align="left", border_style="blue", padding=(0, 2)))
    cells = extract_cells(cli)
    for k in CELLS:
        say(f"  [bold]{k:<11}[/bold] {escape(str(cells.get(k, '')))}")
    gaps = cells.get("gaps") or []
    if gaps:
        say("\n  [dim]questions you did not ask:[/dim]")
        for g in gaps[:5]:
            say(f"    · {escape(str(g))}")

    say("\n  [bold]The three things they were holding back:[/bold]")
    found = check_surfaced(cli)
    for k in ORDER:
        f = found[k]
        if f.get("surfaced"):
            say(f"  [green]✓ {PERSONAS[k]['name']:<18}[/green] {escape(str(f.get('evidence', ''))[:160])}")
        else:
            say(f"  [red]✗ {PERSONAS[k]['name']:<18}[/red] never surfaced — you would have "
                f"found it by asking about: [dim]{PERSONAS[k]['triggers']}[/dim]")
    n = sum(1 for k in ORDER if found[k].get("surfaced"))
    say(RichPanel(
        f"{n} of 3 surfaced. Each one you missed would have come out in week three of the "
        "build instead — as a rewrite (half the tickets have no text), a stalled contract "
        "(the board cap), or a cancelled project (data residency). Discovery is cheaper.",
        title="[bold]the logic[/bold]", title_align="left", border_style="green", padding=(0, 2)))
    meter.show()
    return cells


def price_the_wedge(cli) -> dict:
    rule("Session iii · ROI — one line of arithmetic")
    say(RichPanel(
        "ΔNorth Star × $ coefficient ÷ cost. The North Star here is agent hours spent "
        "hunting; the coefficient is what an hour costs; the cost is yours to estimate. "
        "Defaults come from what Dana and Marcus say if you ask — change any you can "
        "defend with a better number from your transcript.",
        title="[bold]why[/bold]", title_align="left", border_style="blue", padding=(0, 2)))
    default_hours = TICKETS_PER_YEAR * MINUTES_HUNTING / 60
    say(f"  [dim]default ΔNorth Star: {TICKETS_PER_YEAR:,} tickets/yr × {MINUTES_HUNTING} min "
        f"hunting (Dana) = {default_hours:,.0f} h[/dim]")
    say(f"  [dim]default coefficient: ${LOADED_RATE:.0f}/h loaded (Marcus: $31/ticket ≈ 40 min)[/dim]")
    say(f"  [dim]default cost: ${DEFAULT_COST:,.0f} first year — a guess; replace it with yours[/dim]\n")

    def num(prompt: str, default: float) -> float:
        got = _ask(prompt, f"{default:g}")
        try:
            return float(got.replace(",", "").replace("$", ""))
        except ValueError:
            say(f"  [dim](not a number — using {default:g})[/dim]")
            return default

    r = roi(num("ΔNorth Star — agent-hours saved per year", default_hours),
            num("$ coefficient — loaded cost per hour", LOADED_RATE),
            num("cost — build + first-year run, $", DEFAULT_COST))
    say()
    for line in roi_lines(r):
        colour = "red" if line.startswith("Over") else "green" if line.startswith("Under") else "white"
        say(f"  [{colour}]{escape(line)}[/{colour}]")
    say(RichPanel(
        "The formula is simple on purpose. If the three inputs are right, nobody argues "
        "with the division. If they are wrong, a spreadsheet with forty rows would only "
        "hide it better. Marcus will ask where each number came from — the answer should "
        "be a name and a sentence from the interview.",
        title="[bold]the logic[/bold]", title_align="left", border_style="green", padding=(0, 2)))
    return r


def engagement_brief(cli, cells: dict, r: dict) -> None:
    rule("Session iv · The engagement brief")
    say(RichPanel(
        "One page, filled from your transcript and your ROI line. The customer signs that "
        "this is the problem and this is the metric; you sign that you will show the metric "
        "moving — or say in writing that it did not. Everything after Day 1 is built "
        "against this page.",
        title="[bold]why[/bold]", title_align="left", border_style="blue", padding=(0, 2)))
    who = _ask("your name for the sign-off line", "(your name)")
    brief = draft_brief(cli, cells, r, who)
    say(escape(brief))
    say(f"\n  [green]saved →[/green] {REPORTS / 'engagement-brief.md'}  "
        f"[dim](and the transcript beside it; reports/ is gitignored)[/dim]")
    say(RichPanel(
        "Read section 1 again. If the problem is in your words and not the customer's, "
        "go back and ask Dana to say it. A brief the customer recognises as their own "
        "problem gets signed; one that reads like a proposal gets 'we'll think about it'.",
        title="[bold]the logic[/bold]", title_align="left", border_style="green", padding=(0, 2)))
    meter.show()


def main(cli) -> None:
    banner("FDE Field Kit · Day 1 · sessions ii–iv", "Lab 1 · The discovery interview")
    say("[dim]The customer: Calder & Rowe. Three stakeholders, each holding one thing back.[/dim]\n")
    interview(cli)
    cells = discovery_cells(cli)
    r = price_the_wedge(cli)
    engagement_brief(cli, cells, r)
    say()
    say(RichPanel.fit("[bold green]Lab complete.[/bold green] Tomorrow you build the wedge "
                      "you just priced.", border_style="green"))


# ── web ──────────────────────────────────────────────────────────────────────
# Same stages as buttons. The transcript lives in TRANSCRIPT above, so it
# survives between clicks for as long as the server runs.

def _web_transcript() -> str:
    if not TRANSCRIPT:
        return note("No questions yet. Pick someone, type a question, Run.")
    rows = ""
    for t in TRANSCRIPT:
        rows += step(f"you → {PERSONAS[t['persona']]['name'].split()[0]}", t["q"], "warn")
        rows += answer(t["a"])
    return rows


def run_web(cli, v: dict) -> str:
    action = str(v.get("action") or "ask")
    key = str(v.get("persona") or "dana")
    if key not in PERSONAS:
        key = "dana"

    if action == "ask":
        q = str(v.get("question") or "").strip()
        if not q:
            return section("transcript so far", _web_transcript()) + \
                note("Type a question first.", "warn")
        ask_persona(cli, key, q)
        return section("transcript so far", _web_transcript()) + \
            note(f"{len(TRANSCRIPT)} turns. Switch persona and keep going, or press "
                 "'extract the four cells' when you think you have enough.")

    if action == "clear":
        TRANSCRIPT.clear()
        for k in HISTORY:
            HISTORY[k].clear()
        return note("Transcript cleared.", "good")

    if action == "extract":
        if not TRANSCRIPT:
            return note("Interview someone first.", "warn")
        cells = extract_cells(cli)
        found = check_surfaced(cli)
        body = section("the four cells — from your transcript only",
                       table(["cell", "what you learned"],
                             [[k, str(cells.get(k, ""))] for k in CELLS]))
        gaps = cells.get("gaps") or []
        if gaps:
            body += section("questions you did not ask",
                            "".join(step(str(g), "", "") for g in gaps[:5]))
        rows = []
        for k in ORDER:
            f = found[k]
            rows.append([PERSONAS[k]["name"], "surfaced" if f.get("surfaced") else "never came up",
                         str(f.get("evidence") or "")[:140] if f.get("surfaced")
                         else f"ask about: {PERSONAS[k]['triggers']}"])
        n = sum(1 for k in ORDER if found[k].get("surfaced"))
        body += section("the three things they were holding back", table(["who", "status", "detail"], rows))
        body += verdict(f"{n} of 3 surfaced.",
                        "Each one you missed shows up in week three of the build instead — "
                        "as a rewrite, a stalled contract, or a cancelled project.", ok=(n == 3))
        return body

    if action == "roi":
        def num(k: str, default: float) -> float:
            try:
                return float(str(v.get(k) or "").replace(",", "").replace("$", "") or default)
            except ValueError:
                return default
        r = roi(num("delta_hours", TICKETS_PER_YEAR * MINUTES_HUNTING / 60),
                num("rate", LOADED_RATE), num("cost", DEFAULT_COST))
        lines = roi_lines(r)
        body = section("ΔNorth Star × $ coefficient ÷ cost",
                       "".join(step(ln, "", "good" if ln.startswith("Under") else
                                    "bad" if ln.startswith("Over") else
                                    "warn" if ln.startswith("Note") else "") for ln in lines))
        body += verdict("Worth proposing — on these numbers." if r["worth_it"]
                        else "Say so to the customer.",
                        "Marcus will ask where each number came from. The answer should be "
                        "a name and a sentence from the interview.", ok=r["worth_it"])
        return body

    if action == "brief":
        if not TRANSCRIPT:
            return note("Interview someone first.", "warn")
        cells = extract_cells(cli)

        def num(k: str, default: float) -> float:
            try:
                return float(str(v.get(k) or "").replace(",", "").replace("$", "") or default)
            except ValueError:
                return default
        r = roi(num("delta_hours", TICKETS_PER_YEAR * MINUTES_HUNTING / 60),
                num("rate", LOADED_RATE), num("cost", DEFAULT_COST))
        brief = draft_brief(cli, cells, r, str(v.get("fde") or "(your name)"))
        return section("the engagement brief", answer(brief)) + \
            note(f"saved → {REPORTS / 'engagement-brief.md'}", "good")

    return note(f"unknown action {action}", "bad")


def web(cli, port: int) -> None:
    serve(Panel(
        title="The discovery interview",
        subtitle="Three stakeholders at Calder & Rowe, each holding one thing back. "
                 "Ask, extract the four cells, price the wedge, draft the brief.",
        intro="Pick a person, type a question, <b>Run</b>. The transcript keeps between "
              "clicks. When you think you have enough, use the buttons above the knobs: "
              "<code>extract the four cells</code> shows what you learned and what never "
              "came up; <code>price the wedge</code> does the one line of arithmetic; "
              "<code>draft the brief</code> fills the one-page template into "
              "<code>reports/</code>.",
        knobs=[
            Knob("action", "What to do", "select", default="ask",
                 options=[("ask", "ask the question"), ("extract", "extract the four cells"),
                          ("roi", "price the wedge"), ("brief", "draft the brief"),
                          ("clear", "clear the transcript")]),
            Knob("persona", "Who you are talking to", "select", default="dana",
                 options=[(k, f"{PERSONAS[k]['name']} — {PERSONAS[k]['title']}") for k in ORDER],
                 help="Each cares about something different, and each knows things the others don't."),
            Knob("question", "Your question", "textarea",
                 default="Walk me through what happens from the moment a ticket comes in.",
                 help="Ask about the work. 'What would you do with AI?' is a wasted turn."),
            Knob("delta_hours", "ΔNorth Star — agent-hours saved per year", "text",
                 default=f"{TICKETS_PER_YEAR * MINUTES_HUNTING / 60:g}",
                 help=f"default: {TICKETS_PER_YEAR:,} tickets × {MINUTES_HUNTING} min hunting (Dana)"),
            Knob("rate", "$ coefficient — loaded cost per hour", "text", default=f"{LOADED_RATE:g}",
                 help="default: Marcus's $31/ticket ≈ 40 min at $46/h"),
            Knob("cost", "Cost — build + first-year run, $", "text", default=f"{DEFAULT_COST:g}",
                 help="a guess; replace it with yours"),
            Knob("fde", "Your name (sign-off line)", "text", default="(your name)"),
        ],
        run=run_web, button="Run",
    ), cli, port=port, presets_html=presets("action", [
        ("ask the question", "ask"),
        ("extract the four cells", "extract"),
        ("price the wedge", "roi"),
        ("draft the brief", "brief"),
    ]))


if __name__ == "__main__":
    cli = client()
    if wants_web():
        web(cli, port_from(default=7861))
        sys.exit(0)
    main(cli)
