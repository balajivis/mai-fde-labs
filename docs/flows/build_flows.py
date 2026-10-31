# -*- coding: utf-8 -*-
"""Generate the five reference-flow diagrams in docs/flows/*.svg.

    python docs/flows/build_flows.py

Hand-drawn SVGs drift apart; a generator keeps the five shapes in one visual
language so a student can compare them at a glance. Edit SHAPES, re-run, commit.

Legend (same on every sheet):
    grey box        a fixed step — plain code, no model, same every run
    amber box       the model judges here — the ONLY places it decides anything
    red-edged box   a write into the customer's system, behind the gate
    person          a named human; the arrow waits for them
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent

W, H = 1180, 420
BOX_W, BOX_H, GAP = 148, 64, 26
Y = 130
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

STYLE = {
    "trigger": dict(fill="#1a1713", stroke="#1a1713", text="#f6f4ef"),
    "step":    dict(fill="#ece9e1", stroke="#c9c3b5", text="#1a1713"),
    "model":   dict(fill="#f4be3e", stroke="#b8860b", text="#1a1713"),
    "write":   dict(fill="#fff6f4", stroke="#c0392b", text="#1a1713"),
    "end":     dict(fill="#ffffff", stroke="#1a1713", text="#1a1713"),
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_lines(x: float, y: float, lines: list[str], size: int, color: str, weight: str = "400", anchor: str = "middle") -> str:
    out = []
    n = len(lines)
    start = y - (n - 1) * (size + 3) / 2
    for i, line in enumerate(lines):
        out.append(f'<text x="{x:.1f}" y="{start + i * (size + 3):.1f}" font-family="{FONT}" font-size="{size}" '
                   f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}" dominant-baseline="middle">{esc(line)}</text>')
    return "\n".join(out)


def box(x: float, kind: str, lines: list[str], tool: str | None) -> str:
    st = STYLE[kind]
    rx = 32 if kind == "trigger" else 10
    dash = ' stroke-dasharray="6 4"' if kind == "write" else ""
    sw = 2.5 if kind in ("write", "model") else 1.5
    s = (f'<rect x="{x}" y="{Y}" width="{BOX_W}" height="{BOX_H}" rx="{rx}" fill="{st["fill"]}" '
         f'stroke="{st["stroke"]}" stroke-width="{sw}"{dash}/>\n')
    s += text_lines(x + BOX_W / 2, Y + BOX_H / 2, lines, 13, st["text"], "600" if kind != "step" else "500")
    if kind == "model":
        s += text_lines(x + BOX_W / 2, Y - 14, ["the model judges"], 11, "#8a6508", "600")
    if tool:
        s += text_lines(x + BOX_W / 2, Y + BOX_H + 16, [tool], 11, "#6b6358", "400")
    return s


def arrow(x1: float, x2: float, y: float = Y + BOX_H / 2, label: str | None = None) -> str:
    s = f'<line x1="{x1}" y1="{y}" x2="{x2 - 9}" y2="{y}" stroke="#1a1713" stroke-width="1.6" marker-end="url(#arr)"/>'
    if label:
        s += text_lines((x1 + x2) / 2, y - 12, [label], 10, "#6b6358")
    return s


def person(cx: float, cy: float, label: list[str]) -> str:
    s = (f'<circle cx="{cx}" cy="{cy - 14}" r="8" fill="none" stroke="#1a1713" stroke-width="1.8"/>'
         f'<path d="M{cx - 14},{cy + 10} a14,14 0 0 1 28,0" fill="none" stroke="#1a1713" stroke-width="1.8"/>')
    s += text_lines(cx, cy + 28, label, 11, "#1a1713", "600")
    return s


def gate(x_from: float, label: list[str], who: list[str], back_to: float | None) -> str:
    """A side branch below the flow: a write stops and asks a named person."""
    gx, gy = x_from + BOX_W / 2, Y + BOX_H
    py = gy + 104
    s = f'<line x1="{gx}" y1="{gy + 2}" x2="{gx}" y2="{py - 44}" stroke="#c0392b" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#arr-red)"/>'
    s += text_lines(gx + 12, gy + 42, label, 10, "#c0392b", "600", anchor="start")
    s += person(gx, py, who)
    if back_to is not None:
        s += (f'<path d="M{gx + 18},{py - 6} C {gx + 90},{py - 6} {back_to - 60},{py - 6} {back_to},{Y + BOX_H + 2}" '
              f'fill="none" stroke="#1a1713" stroke-width="1.4" stroke-dasharray="3 4" marker-end="url(#arr)"/>')
        s += text_lines((gx + back_to) / 2 + 30, py - 40, ["approved"], 10, "#6b6358")
    return s


def legend(x: float, y: float) -> str:
    items = [("step", "fixed step · plain code"), ("model", "the model judges"), ("write", "a write, behind the gate")]
    s = ""
    for i, (kind, lab) in enumerate(items):
        st = STYLE[kind]
        xx = x + i * 190
        dash = ' stroke-dasharray="6 4"' if kind == "write" else ""
        s += f'<rect x="{xx}" y="{y}" width="22" height="14" rx="3" fill="{st["fill"]}" stroke="{st["stroke"]}" stroke-width="1.5"{dash}/>'
        s += text_lines(xx + 30, y + 7, [lab], 11, "#6b6358", anchor="start")
    xx = x + 3 * 190
    s += f'<circle cx="{xx + 11}" cy="{y + 4}" r="4" fill="none" stroke="#1a1713" stroke-width="1.5"/><path d="M{xx + 4},{y + 15} a7,7 0 0 1 14,0" fill="none" stroke="#1a1713" stroke-width="1.5"/>'
    s += text_lines(xx + 30, y + 7, ["a named person · the arrow waits"], 11, "#6b6358", anchor="start")
    return s


def render(shape: dict) -> str:
    nodes = shape["nodes"]
    n = len(nodes)
    total = n * BOX_W + (n - 1) * GAP
    x0 = (W - total) / 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
        '<defs>'
        '<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1a1713"/></marker>'
        '<marker id="arr-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#c0392b"/></marker>'
        '</defs>',
        f'<rect width="{W}" height="{H}" fill="#f6f4ef"/>',
        text_lines(28, 34, [f'{shape["n"]} · {shape["title"]}'], 20, "#1a1713", "700", anchor="start"),
        text_lines(28, 60, [shape["one_liner"]], 13, "#6b6358", anchor="start"),
        text_lines(W - 28, 34, ["Modern AI Pro · FDE Field Kit · reference flows"], 11, "#a29b8c", anchor="end"),
    ]
    xs = []
    for i, node in enumerate(nodes):
        x = x0 + i * (BOX_W + GAP)
        xs.append(x)
        parts.append(box(x, node["kind"], node["lines"], node.get("tool")))
        if i:
            parts.append(arrow(xs[i - 1] + BOX_W, x, label=node.get("edge")))
    g = shape.get("gate")
    if g:
        back = xs[g["back_to"]] + BOX_W / 2 if g.get("back_to") is not None else None
        parts.append(gate(xs[g["at"]], g["label"], g["who"], back))
    parts.append(text_lines(28, H - 62, [shape["rule"]], 12, "#1a1713", "600", anchor="start"))
    parts.append(legend(28, H - 32))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


SHAPES = [
    dict(
        file="01-ticket-triage.svg", n="1", title="Ticket triage — classify, route, draft",
        one_liner="The kit's wedge. A ticket arrives; the agent reads, looks up, drafts, proposes, writes back. Anything that moves money waits for a person.",
        nodes=[
            dict(kind="trigger", lines=["New ticket", "in the desk"], tool="list_tickets · get_ticket"),
            dict(kind="step", lines=["Look up order", "and customer"], tool="get_order · get_customer"),
            dict(kind="step", lines=["Search policies", "scope first"], tool="search_policies"),
            dict(kind="model", lines=["Classify, set", "priority, draft"], tool="one JSON object"),
            dict(kind="write", lines=["Write back:", "comment + fields"], tool="add_comment · set_ticket"),
            dict(kind="end", lines=["Desk agent", "sends the reply"], tool="never the agent"),
        ],
        gate=dict(at=4, label=["credit / refund /", "replacement?"], who=["admin.ruth", "approves"], back_to=5),
        rule="The model decides at exactly one box. Everything else is code, and the permission check lives inside the customer's system.",
    ),
    dict(
        file="02-inbox-agent.svg", n="2", title="Inbox agent — shared mailbox, replies queued",
        one_liner="Same shape as triage, different trigger and a harder rule: email is untrusted input, and the agent never holds the send button.",
        nodes=[
            dict(kind="trigger", lines=["New message in", "the shared inbox"], tool="the mail system, read only"),
            dict(kind="step", lines=["Thread + sender", "+ their account"], tool="find_customers · list_orders"),
            dict(kind="step", lines=["Retrieve policy", "and history"], tool="search_policies"),
            dict(kind="model", lines=["Draft the reply", "flag anything odd"]),
            dict(kind="write", lines=["Queue the draft", "never send"], tool="add_comment(internal=True)"),
            dict(kind="end", lines=["Sent from the", "person's account"], tool="their name on it"),
        ],
        gate=dict(at=4, label=["every draft", "is reviewed"], who=["the owner of", "the inbox"], back_to=5),
        rule="Nothing written in an email can change which tools the agent calls. The text is data; the flow is fixed.",
    ),
    dict(
        file="03-scheduled-ops.svg", n="3", title="Scheduled ops agent — report, reconcile, alert",
        one_liner="A clock starts it, not a person. It reads a lot, changes nothing, and the only judgement is explaining what the arithmetic found.",
        nodes=[
            dict(kind="trigger", lines=["Clock:", "nightly at 02:00"], tool="cron · scheduler"),
            dict(kind="step", lines=["Pull the records", "in scope"], tool="list_tickets · list_orders"),
            dict(kind="step", lines=["Reconcile by code", "totals, gaps, aging"], tool="no model here"),
            dict(kind="model", lines=["Explain the", "anomalies only"]),
            dict(kind="write", lines=["Write the report", "to one place"], tool="a file · a ticket"),
            dict(kind="end", lines=["Alert if over", "the threshold"], tool="the threshold is code"),
        ],
        gate=dict(at=5, label=["anomaly above", "the line?"], who=["on-call person", "reads it"], back_to=None),
        rule="Reconcile with arithmetic, explain with the model. If the model is doing the sums, the shape is wrong.",
    ),
    dict(
        file="04-knowledge-writeback.svg", n="4", title="Knowledge Q&A with write-back",
        one_liner="A person asks; the agent answers from what that person is allowed to see, cites it, and may propose one small write — which still goes through the gate.",
        nodes=[
            dict(kind="trigger", lines=["A person asks", "a question"], tool="whoami → role, regions"),
            dict(kind="step", lines=["Filter by scope", "before search"], tool="inside the estate"),
            dict(kind="step", lines=["Retrieve top-k", "policies, records"], tool="search_policies · get_policy"),
            dict(kind="model", lines=["Answer with", "citations"]),
            dict(kind="model", lines=["Propose a write", "or say none"]),
            dict(kind="write", lines=["Apply the write", "if the role allows"], tool="set_ticket · add_comment"),
        ],
        gate=dict(at=5, label=["needs a role the", "asker lacks?"], who=["DENIED, and", "audited"], back_to=None),
        rule="A viewer gets a correct answer and a refused write. The refusal is the feature; the audit line is the evidence.",
    ),
    dict(
        file="05-planner-workers.svg", n="5", title="Multi-agent workflow — planner + workers",
        one_liner="For the case one flow cannot hold. The planner decides the plan; each worker is one of the fixed flows above; every write still meets one gate.",
        nodes=[
            dict(kind="trigger", lines=["A complex case", "many sub-tasks"], tool="e.g. a multi-site warranty claim"),
            dict(kind="model", lines=["Planner:", "split into tasks"]),
            dict(kind="step", lines=["Order worker", "flow 1, read only"], tool="get_order · list_orders"),
            dict(kind="step", lines=["Policy worker", "flow 4, cited"], tool="search_policies"),
            dict(kind="model", lines=["Merge, draft,", "name the writes"]),
            dict(kind="write", lines=["One gate for", "every write"], tool="add_comment · set_ticket"),
        ],
        gate=dict(at=5, label=["any destructive", "action?"], who=["a named", "approver"], back_to=None),
        rule="Only earn this shape with an ablation: the single flow, well prompted, is the baseline it has to beat on the golden set.",
    ),
]


def main() -> None:
    for shape in SHAPES:
        (HERE / shape["file"]).write_text(render(shape), encoding="utf-8")
        print("wrote", shape["file"])


if __name__ == "__main__":
    main()
