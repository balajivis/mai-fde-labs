# -*- coding: utf-8 -*-
"""Generate docs/schedule/weekend.svg — Saturday and Sunday, hour by hour.

    python docs/schedule/build_schedule.py

Edit DAYS, re-run, commit. The same file is served on the study platform
(public/guides/fde-weekend.svg); copy it there after regenerating.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
W = 1180
PAD = 28
DAY_W = (W - 2 * PAD - 30) / 2
PX_PER_MIN = 2.1           # 7 hours → ~880 px
T0 = 8 * 60 + 30           # 8:30
TOP = 112

KIND = {
    "guest": dict(fill="#e4e8e7", stroke="#3a4442", tag="GUEST"),
    "teach": dict(fill="#f7ebda", stroke="#b86e12", tag="TEACH"),
    "lab":   dict(fill="#e2f0ee", stroke="#0e6b66", tag="LAB"),
    "close": dict(fill="#f6e4e7", stroke="#a33d4b", tag="CLOSE"),
    "break": dict(fill="#eef2f0", stroke="none", tag=""),
}

DAYS = [
    ("Saturday · Build the agent", "Sat Oct 31 · 8:30 AM – 3:30 PM PT", [
        ("8:30", "9:30", "guest", "Advancements in AI", "Arvind · guest hour", ""),
        ("9:30", "10:15", "teach", "B1 · The flow walk", "the eight layers, the five reference flows, then each student's own: trigger, the amber box, the write, the gate", "docs/FLOWS.md · flows/index.html"),
        ("10:15", "10:30", "lab", "Lab 1a · What does a ticket cost?", "four lines on paper, then the calculator; prices from your provider's page", "labs/lab_1a_cost.py · docs/COST.md"),
        ("10:30", "10:45", "break", "Coffee", "", ""),
        ("10:45", "12:30", "lab", "B2 · Lab 2 · Build the wedge", "stages 1–5: who are you, one ticket, the mess, scope before search, the batch with the cost line measured", "labs/lab_2_wedge.py · docs/WEDGE.md"),
        ("12:30", "13:15", "break", "Lunch", "", ""),
        ("13:15", "14:30", "lab", "B3 · The Map, then the Eval Contract", "lab 2 stage 6: Integration Map signed → Deliverable II · lab 3 stages 1–3: the frozen set, the suites, the calibrated judge", "labs/lab_3_eval_contract.py · artefacts/02 · 03"),
        ("14:30", "14:45", "break", "Coffee", "", ""),
        ("14:45", "15:30", "close", "B4 · The regression gate, the contract signed", "lab 3 stages 4–5: the gate on a degraded copy; Eval Contract → Deliverable III · homework: finish the contract, bring one attack", "reports/eval-contract.md"),
    ]),
    ("Sunday · Make it trustworthy", "Sun Nov 1 · 8:30 AM – 3:30 PM PT", [
        ("8:30", "9:30", "guest", "Enterprise readiness checklist", "Moring AI · guest hour", ""),
        ("9:30", "10:30", "lab", "B5 · Lab 4 · Security review and red-team", "nine planted injections, six PII plants, four access traps; every success becomes a frozen case → Deliverable IV", "labs/lab_4_security.py · artefacts/04"),
        ("10:30", "10:45", "break", "Coffee", "", ""),
        ("10:45", "12:30", "lab", "B6 · Governance Canvas and the approval dial", "lab 5, the HITL half: risk tags, the queue with a named second person, fail-closed, the four autonomy rungs → Deliverable V", "labs/lab_5_hitl_operate.py · artefacts/05"),
        ("12:30", "13:15", "break", "Lunch", "", ""),
        ("13:15", "14:30", "lab", "B7 · Operate: SLO, cost, runbook, go-live", "lab 5, the operate half: p50/p95 and cost per ticket from traces, the load test, the runbook → Deliverable VI", "artefacts/06 · reports/"),
        ("14:30", "14:45", "break", "Coffee", "", ""),
        ("14:45", "15:30", "close", "B8 · Walkthroughs", "your agent and its one-page architecture, the way you would with a hiring manager; six artefacts together is the portfolio", "all six, signed"),
    ]),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mins(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def fmt(t: str) -> str:
    h, m = t.split(":")
    h = int(h)
    return f"{h - 12 if h > 12 else h}:{m}"


def text(x, y, s, size=12, color="#1a1713", weight="400", anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{esc(s)}</text>')


def main() -> None:
    H = TOP + int(7 * 60 * PX_PER_MIN) + 96
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="#f6f4ef"/>',
           text(PAD, 40, "The FDE weekend, hour by hour", 20, "#1a1713", "700"),
           text(PAD, 64, "All times Pacific · Friday was the job, the map and the discovery interview (Deliverable I) · every block ends with something added to your agent", 11.5, "#6b6358"),
           text(W - PAD, 40, "Modern AI Pro · FDE Field Kit", 11, "#a29b8c", anchor="end")]
    for di, (title, sub, blocks) in enumerate(DAYS):
        x = PAD + di * (DAY_W + 30)
        out.append(text(x, TOP - 26, title, 15, "#1a1713", "700"))
        out.append(text(x, TOP - 10, sub, 11, "#6b6358"))
        for start, end, kind, name, detail, files in blocks:
            y = TOP + (mins(start) - T0) * PX_PER_MIN
            h = (mins(end) - mins(start)) * PX_PER_MIN
            k = KIND[kind]
            if kind == "break":
                out.append(f'<rect x="{x}" y="{y + 1}" width="{DAY_W}" height="{h - 2}" fill="{k["fill"]}"/>')
                out.append(text(x + 62, y + h / 2 + 4, f"{name} · {fmt(start)}–{fmt(end)}", 11, "#6b6358"))
                continue
            out.append(f'<rect x="{x + 52}" y="{y + 2}" width="{DAY_W - 52}" height="{h - 4}" rx="8" fill="{k["fill"]}" stroke="{k["stroke"]}" stroke-width="1.5"/>')
            out.append(text(x, y + 16, fmt(start), 11.5, "#1a1713", "600"))
            out.append(text(x, y + 30, fmt(end), 10.5, "#a29b8c"))
            out.append(text(x + 64, y + 20, name, 13.5, "#1a1713", "700"))
            out.append(text(x + DAY_W - 10, y + 18, k["tag"], 9.5, k["stroke"], "600", anchor="end"))
            yy = y + 38
            room = max(0, int((h - 44 - (16 if files else 0)) / 15))
            for line in textwrap.wrap(detail, width=int((DAY_W - 80) / 6.3))[:room]:
                out.append(text(x + 64, yy, line, 11.5, "#1a1713"))
                yy += 15
            if files and h > 58:
                out.append(text(x + 64, y + h - 12, files, 10.5, "#6b6358"))
    # legend
    ly = H - 48
    lx = PAD
    for kind in ("guest", "teach", "lab", "close"):
        k = KIND[kind]
        out.append(f'<rect x="{lx}" y="{ly - 10}" width="22" height="13" rx="3" fill="{k["fill"]}" stroke="{k["stroke"]}" stroke-width="1.5"/>')
        label = {"guest": "guest hour", "teach": "taught, from the sheets", "lab": "hands-on, from the kit", "close": "the hinge: something signed"}[kind]
        out.append(text(lx + 30, ly, label, 11, "#6b6358"))
        lx += 220
    out.append(text(PAD, H - 22, "Deliverables: I Brief (Fri) · II Map · III Eval Contract (Sat) · IV Security · V Governance · VI Go-live (Sun)", 11.5, "#1a1713", "600"))
    out.append("</svg>")
    (HERE / "weekend.svg").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote weekend.svg", W, "x", H)


if __name__ == "__main__":
    main()
