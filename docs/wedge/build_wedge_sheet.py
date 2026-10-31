# -*- coding: utf-8 -*-
"""Generate docs/wedge/lab2-stages.svg — the six stages of lab 2 on one sheet.

    python docs/wedge/build_wedge_sheet.py

Same visual language as docs/flows: cream sheet, amber for the point to land,
red for the thing to watch for. Edit STAGES, re-run, commit.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
W = 1180
PAD = 28
COLS = [("Stage", 150), ("What they do", 300), ("The point to land", 300), ("Watch for", 346)]
SIZE, LH = 12.5, 17
TITLE = "Lab 2 · Build the wedge — the six stages, what to say over each"
SUB = "Terminal: python labs/lab_2_wedge.py (Enter between stages) · Web: --web, port 7862 · Oct 28 numbers are the reference; yours will differ, and that is the point"

STAGES = [
    ("1 · Who are you",
     "Connect as viewer.sam: 15 tools listed, the first write is DENIED. Reconnect as agent.priya — same prompt, same code — and the write goes through.",
     "The permission check lives inside the customer's system, not in the prompt. Identity is the first layer, not the last.",
     "Someone “fixing” the denial by editing the prompt. That is the wrong fix, and worth saying out loud."),
    ("2 · One ticket",
     "T-30535, a walk-in cooler fault in the west. Read → order → customer → policy → draft → one JSON object → write back a comment, set category and priority.",
     "The six boxes from the flow sheet are now code. One amber box. The desk agent still sends the reply.",
     "Oct 28 run: 6 tool calls, warranty_claim / high / WAR-WALKIN, 18.6k tokens, 9.9 s."),
    ("3 · The mess",
     "T-30485, its order does not exist · T-30428, body is “see phone notes” · T-30272, east, outside priya's scope.",
     "What a good wedge does with bad data: escalate and ask, never invent. Dana's hidden constraint from Friday (phone tickets typed up badly) shows up here.",
     "The orphan ticket is the teachable failure: the Oct 28 model wrote “reviewing with the carrier”, which nothing returned. The judge says INVENTED. Fixing the prompt so it says “I could not find order O-27595” is the exercise."),
    ("4 · Scope before search",
     "The same policy query as priya and as admin.ruth, side by side.",
     "Retrieval is filtered by scope before ranking, so the east addendum never reaches priya. Ruth's constraint from Friday, who sees what, made concrete.",
     "This is the row IT reads first on the Integration Map."),
    ("5 · The batch",
     "--n 8 or --n 12 open tickets in priya's scope. Tokens, latency and escalations per ticket.",
     "The cost line from lab 1a, now measured: tokens per ticket × today's price, against $31 a ticket today.",
     "Oct 28: p50 7.1 s, p95 12.7 s, 11.4k tokens per ticket, about 95% input, 1 escalation. The meter is the point."),
    ("6 · The map",
     "reports/integration-map.md is written with the identity table and the eight layers pre-marked build / connect / never.",
     "They fill the owner column and “we never touch”, and sign it as their IT persona. Deliverable II.",
     "A layer with no owner is where the pilot stalls. Then open estate/data/audit.jsonl: one file Ruth can read."),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(s: str, width_px: int) -> list[str]:
    return textwrap.wrap(s, width=max(10, int(width_px / 6.6)))


def text(x, y, s, size=SIZE, color="#1a1713", weight="400", anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{esc(s)}</text>')


def main() -> None:
    xs = []
    x = PAD
    for _, w in COLS:
        xs.append(x)
        x += w + 18
    rows = []
    y = 118
    body = []
    for stage, do, point, watch in STAGES:
        cells = [[stage], wrap(do, COLS[1][1]), wrap(point, COLS[2][1]), wrap(watch, COLS[3][1])]
        h = max(len(c) for c in cells) * LH + 22
        rows.append((y, h))
        body.append(f'<rect x="{PAD - 10}" y="{y}" width="{W - 2 * PAD + 20}" height="{h}" rx="8" fill="#ffffff" stroke="#e6e2d6"/>')
        for ci, lines in enumerate(cells):
            color = ["#1a1713", "#1a1713", "#8a6508", "#c0392b"][ci]
            weight = ["700", "400", "500", "400"][ci]
            for li, line in enumerate(lines):
                body.append(text(xs[ci], y + 20 + li * LH, line, SIZE if ci else 13.5, color, weight))
        y += h + 10
    H = y + 56
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="#f6f4ef"/>',
           text(PAD, 40, TITLE, 20, "#1a1713", "700"),
           text(PAD, 64, SUB, 11.5, "#6b6358"),
           text(W - PAD, 40, "Modern AI Pro · FDE Field Kit · Saturday", 11, "#a29b8c", anchor="end")]
    for ci, (name, _) in enumerate(COLS):
        out.append(text(xs[ci], 100, name.upper(), 11, "#6b6358", "600"))
    out.append(f'<line x1="{PAD - 10}" y1="108" x2="{W - PAD + 10}" y2="108" stroke="#c9c3b5"/>')
    out += body
    out.append(text(PAD, H - 24, "Timing from 10:40 — stages 1–2 by 11:15 · stage 3 with the fix by 11:50 · 4–5 by 12:15 · the map and the cost line to 12:30", 11.5, "#1a1713", "600"))
    out.append("</svg>")
    (HERE / "lab2-stages.svg").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote lab2-stages.svg", W, "x", H)


if __name__ == "__main__":
    main()
