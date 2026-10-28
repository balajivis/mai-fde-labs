# -*- coding: utf-8 -*-
"""The Calder & Rowe estate API — the customer's systems, as the wedge sees them.

Fifteen functions over six JSON files in `estate/data/`. No network, no
database, no model. Every function takes the acting `user` first, and the
permission check lives INSIDE the function, not in the caller and not in the
prompt. That is the whole argument of this file, so here is why:

A prompt that says "only show west tickets to west agents" is a request. The
model can be talked out of it by a ticket body (nine of them in this estate
try), it can forget it after a long context, and it can simply be wrong. A
`region in user.regions` check on line N of `list_tickets` cannot be talked out
of anything. It also does not care whether the caller is a model, a student,
a test, or Ruth with a shell — which is why the MCP server in `estate_mcp.py`
is a thin wrapper and adds no checks of its own. If a check is not here, it
does not exist.

Three mechanisms, each in the function that needs it:

    scope   the user's regions filter the rows BEFORE any search or ranking;
            an out-of-scope id raises Denied (the id is not confirmed to exist)
    role    viewer < agent < admin; writes need agent, money needs admin
    PII     contact details are masked unless the user has `can_see_pii`

Everything is audited to `estate/data/audit.jsonl` — denials too, because the
denial IS the interesting line when something goes wrong. Writes go to
`estate/data/state.json`, layered over the generated files, so a `git pull`
never clobbers your run and `reset()` takes you back to a clean estate.

What this layer does NOT do: it does not look inside free text. Six tickets
carry a card number or a home address in the body; the body is returned as
written, because deciding "is this a card number" is classification, and
classification is the wedge's job (with a model), not a string check in a data
layer. The structural fields it can mask, it masks.

    from _estate import *            # or: import _estate as E
    me = whoami("agent.priya")
    t = get_ticket("agent.priya", "T-30207")
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "estate" / "data"
# ESTATE_STATE_DIR moves the two mutable files (a lab's own sandbox, a test run)
# without touching the generated data, which is never written to.
_MUT = Path(os.environ.get("ESTATE_STATE_DIR", "") or DATA)
AUDIT = _MUT / "audit.jsonl"
STATE = _MUT / "state.json"
DEFAULT_USER = "viewer.sam"            # least privilege when nobody says who they are

ROLE_RANK = {"viewer": 0, "agent": 1, "admin": 2}
STATUSES = {"open", "pending", "resolved", "closed"}
PRIORITIES = {"low", "normal", "high", "urgent"}
CATEGORIES = {"warranty_claim", "delivery", "installation", "parts", "billing",
              "returns", "training", "other"}
PII_FIELDS = ("contact_name", "email", "phone", "address")

# ── the risk register ────────────────────────────────────────────────────────
# read         safe to run unattended
# write        reversible, but someone should be able to see it happened
# destructive  moves money or goods — a human decides, every time
RISK: dict[str, str] = {
    "whoami": "read", "get_customer": "read", "find_customers": "read", "get_order": "read",
    "list_orders": "read", "get_ticket": "read", "list_tickets": "read", "search_policies": "read",
    "get_policy": "read", "add_comment": "write", "set_ticket": "write", "open_ticket": "write",
    "issue_credit": "destructive", "authorise_replacement": "destructive", "read_audit": "read",
}


class Denied(Exception):
    """Raised, never returned: a denied call must not look like an empty result."""


# ── loading ──────────────────────────────────────────────────────────────────

_CACHE: dict[str, object] = {}


def _table(name: str) -> list[dict]:
    """The generated file, loaded once per process."""
    if name not in _CACHE:
        _CACHE[name] = json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))
    return _CACHE[name]                                         # type: ignore[return-value]


def _state() -> dict:
    """Student writes, layered over the generated files. Read fresh every time so
    two processes (a lab and the MCP server) see each other's writes."""
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"tickets": {}, "credits": [], "replacements": []}


def _save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _tickets() -> list[dict]:
    """Generated tickets with state overrides applied, plus tickets opened in state."""
    st = _state()
    rows = [st["tickets"].get(t["id"], t) for t in _table("tickets")]
    rows += [t for tid, t in st["tickets"].items() if tid.startswith("T-9")]   # opened at runtime
    return rows


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_user(user_id: str | None = None) -> str:
    """Who is acting: an explicit id, else ESTATE_USER, else the least-privileged user."""
    return (user_id or os.environ.get("ESTATE_USER", "") or DEFAULT_USER).strip()


# ── the three checks ─────────────────────────────────────────────────────────

def _user(user) -> dict:
    """Accepts an id or an identity record; an unknown id is a denial, not a KeyError."""
    uid = user["id"] if isinstance(user, dict) else str(user)
    for rec in _table("identity"):
        if rec["id"] == uid:
            return rec
    _audit(uid, "whoami", {}, allowed=False, reason="unknown user")
    raise Denied(f"unknown user {uid!r}")


def _require(u: dict, role: str, tool: str, args: dict) -> None:
    """Role gate. The denial names the role the caller needed, so an agent can
    re-plan ("escalate to an admin") instead of retrying the same call."""
    if ROLE_RANK[u["role"]] < ROLE_RANK[role]:
        reason = f"{tool} needs role {role}; {u['id']} is {u['role']}"
        _audit(u["id"], tool, args, allowed=False, reason=reason)
        raise Denied(reason)


def _in_scope(u: dict, region: str | list[str]) -> bool:
    """A record is visible if its region is one of the user's. Policies carry a
    list (or ["all"]); everything else carries one region."""
    if isinstance(region, list):
        return "all" in region or any(r in u["regions"] for r in region)
    return region in u["regions"]


def _scoped(u: dict, rec: dict | None, tool: str, args: dict, what: str) -> dict:
    """One answer for 'missing' and 'out of scope', on purpose: a different error
    for each would confirm that an id exists outside the caller's region."""
    if rec is None or not _in_scope(u, rec.get("regions", rec.get("region"))):
        reason = f"{what} not found in your scope ({', '.join(u['regions'])})"
        _audit(u["id"], tool, args, allowed=False, reason=reason)
        raise Denied(reason)
    return rec


def _mask(u: dict, cust: dict) -> dict:
    """Structural PII masking. Last four of the phone survive (it is how a desk
    confirms a caller); everything else becomes a placeholder."""
    if u["can_see_pii"]:
        return dict(cust)
    out = dict(cust)
    first = cust["contact_name"].split(" ")[0]
    out["contact_name"] = f"{first} {cust['contact_name'].split(' ')[-1][:1]}."
    out["email"] = "***@" + cust["email"].split("@")[-1]
    out["phone"] = "(***) ***-" + cust["phone"][-4:]
    out["address"] = "*** (masked)"
    return out


# ── audit ────────────────────────────────────────────────────────────────────

def _audit(user: str, tool: str, args: dict, *, allowed: bool, reason: str | None = None,
           rows_returned: int | None = None) -> None:
    """One JSON line per call, append-only. `args` is logged as given — the
    audit answers "what was asked", and a masked log cannot answer it."""
    line = {"ts": _now(), "user": user, "tool": tool, "args": args, "allowed": allowed}
    if reason is not None:
        line["reason"] = reason
    if rows_returned is not None:
        line["rows_returned"] = rows_returned
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


# ── reads ────────────────────────────────────────────────────────────────────

def whoami(user) -> dict:
    """The identity record: role, regions, can_see_pii. Start here."""
    u = _user(user)
    _audit(u["id"], "whoami", {}, allowed=True, rows_returned=1)
    return dict(u)


def get_customer(user, customer_id: str) -> dict:
    u = _user(user)
    args = {"customer_id": customer_id}
    rec = next((c for c in _table("customers") if c["id"] == customer_id), None)
    rec = _scoped(u, rec, "get_customer", args, f"customer {customer_id}")
    _audit(u["id"], "get_customer", args, allowed=True, rows_returned=1)
    return _mask(u, rec)


def find_customers(user, name: str) -> list[dict]:
    """Fuzzy on name, in scope. Returns the duplicates too — that is the point:
    the wedge has to notice 'Ltd' and 'Limited' are one business."""
    u = _user(user)
    args = {"name": name}
    q = " ".join(name.lower().split())
    scored = []
    for c in _table("customers"):
        if not _in_scope(u, c["region"]):
            continue                                   # filtered BEFORE scoring
        n = " ".join(c["name"].lower().split())
        score = SequenceMatcher(None, q, n).ratio()
        if q in n:
            score = max(score, 0.9)
        if score >= 0.6:
            scored.append((score, c))
    scored.sort(key=lambda s: (-s[0], s[1]["id"]))
    rows = [_mask(u, c) for _, c in scored[:20]]
    _audit(u["id"], "find_customers", args, allowed=True, rows_returned=len(rows))
    return rows


def get_order(user, order_id: str) -> dict:
    u = _user(user)
    args = {"order_id": order_id}
    rec = next((o for o in _table("orders") if o["id"] == order_id), None)
    rec = _scoped(u, rec, "get_order", args, f"order {order_id}")
    _audit(u["id"], "get_order", args, allowed=True, rows_returned=1)
    return dict(rec)


def list_orders(user, customer_id: str) -> list[dict]:
    u = _user(user)
    args = {"customer_id": customer_id}
    cust = next((c for c in _table("customers") if c["id"] == customer_id), None)
    _scoped(u, cust, "list_orders", args, f"customer {customer_id}")
    rows = [dict(o) for o in _table("orders")
            if o["customer_id"] == customer_id and _in_scope(u, o["region"])]
    rows.sort(key=lambda o: o["ordered"], reverse=True)
    _audit(u["id"], "list_orders", args, allowed=True, rows_returned=len(rows))
    return rows


def get_ticket(user, ticket_id: str) -> dict:
    """The ticket with its comments. An east id asked for by a west user raises
    Denied — and the audit line is the one Ruth will ask to see."""
    u = _user(user)
    args = {"ticket_id": ticket_id}
    rec = next((t for t in _tickets() if t["id"] == ticket_id), None)
    rec = _scoped(u, rec, "get_ticket", args, f"ticket {ticket_id}")
    _audit(u["id"], "get_ticket", args, allowed=True, rows_returned=1)
    return json.loads(json.dumps(rec))                 # a copy; callers mutate


def list_tickets(user, status: str | None = None, region: str | None = None,
                 limit: int = 50) -> list[dict]:
    """Newest first (ids are chronological). Asking for a region you do not hold
    is a denial, not an empty list: an empty list would teach the agent that
    'east' is a valid thing to ask for and just happens to be quiet today."""
    u = _user(user)
    args = {"status": status, "region": region, "limit": limit}
    if region is not None and region not in u["regions"]:
        reason = f"region {region!r} is outside your scope ({', '.join(u['regions'])})"
        _audit(u["id"], "list_tickets", args, allowed=False, reason=reason)
        raise Denied(reason)
    rows = [t for t in _tickets() if _in_scope(u, t["region"])]      # scope first
    if region is not None:
        rows = [t for t in rows if t["region"] == region]
    if status is not None:
        rows = [t for t in rows if t["status"] == status]
    rows.sort(key=lambda t: t["id"], reverse=True)
    rows = [json.loads(json.dumps(t)) for t in rows[:max(0, int(limit))]]
    _audit(u["id"], "list_tickets", args, allowed=True, rows_returned=len(rows))
    return rows


# ── policy search: a small BM25 in the open ──────────────────────────────────
# No embeddings, no package. Forty documents do not need a vector database, and
# a ranking you can read is a ranking you can explain to a customer's security
# owner. The important line is the scope filter: the corpus is cut to the
# user's regions BEFORE the index is built, so an out-of-scope addendum cannot
# even influence the IDF, let alone appear in the results.

def _tokens(text: str) -> list[str]:
    return "".join(ch if ch.isalnum() else " " for ch in text.lower()).split()


def _bm25(query: str, docs: list[dict], k1: float = 1.5, b: float = 0.75) -> list[tuple[float, dict]]:
    corpus = [_tokens(d["title"] + " " + d["text"]) for d in docs]
    avg = sum(len(c) for c in corpus) / max(1, len(corpus))
    n = len(corpus)
    df: dict[str, int] = {}
    for toks in corpus:
        for term in set(toks):
            df[term] = df.get(term, 0) + 1
    out = []
    for d, toks in zip(docs, corpus):
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for term in _tokens(query):
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            num = tf[term] * (k1 + 1)
            den = tf[term] + k1 * (1 - b + b * len(toks) / avg)
            score += idf * num / den
        if score > 0:
            out.append((score, d))
    out.sort(key=lambda s: (-s[0], s[1]["doc_id"]))
    return out


def search_policies(user, query: str, k: int = 5) -> list[dict]:
    """Top-k policy documents for a keyword query, scope-filtered before ranking.
    Returns the whole document (text included): forty documents of 2–6
    paragraphs is small enough that the agent should read, not skim."""
    u = _user(user)
    args = {"query": query, "k": k}
    docs = [d for d in _table("policies") if _in_scope(u, d["regions"])]   # scope first
    ranked = _bm25(query, docs)[:max(0, int(k))]
    rows = [dict(d, score=round(s, 3)) for s, d in ranked]
    _audit(u["id"], "search_policies", args, allowed=True, rows_returned=len(rows))
    return rows


def get_policy(user, doc_id: str) -> dict:
    u = _user(user)
    args = {"doc_id": doc_id}
    rec = next((d for d in _table("policies") if d["doc_id"] == doc_id), None)
    rec = _scoped(u, rec, "get_policy", args, f"policy {doc_id}")
    _audit(u["id"], "get_policy", args, allowed=True, rows_returned=1)
    return dict(rec)


# ── writes (agent+) ──────────────────────────────────────────────────────────

def add_comment(user, ticket_id: str, body: str, *, internal: bool = True) -> dict:
    """Append a comment. Internal by default: a draft reply is a proposal until a
    person flips it to customer-visible."""
    u = _user(user)
    args = {"ticket_id": ticket_id, "body": body, "internal": internal}
    _require(u, "agent", "add_comment", args)
    rec = next((t for t in _tickets() if t["id"] == ticket_id), None)
    rec = _scoped(u, rec, "add_comment", args, f"ticket {ticket_id}")
    rec = json.loads(json.dumps(rec))
    comment = {"by": u["id"], "at": _now(), "body": body, "internal": bool(internal)}
    rec["comments"].append(comment)
    st = _state()
    st["tickets"][ticket_id] = rec
    _save_state(st)
    _audit(u["id"], "add_comment", args, allowed=True, rows_returned=1)
    return comment


def set_ticket(user, ticket_id: str, *, status: str | None = None, priority: str | None = None,
                category: str | None = None) -> dict:
    """Set any of status / priority / category. Values are validated against the
    closed lists above — a typo'd category is a data-quality bug, not a feature."""
    u = _user(user)
    args = {"ticket_id": ticket_id, "status": status, "priority": priority, "category": category}
    _require(u, "agent", "set_ticket", args)
    for value, allowed, name in ((status, STATUSES, "status"), (priority, PRIORITIES, "priority"),
                                 (category, CATEGORIES, "category")):
        if value is not None and value not in allowed:
            raise ValueError(f"{name} must be one of {sorted(allowed)}, not {value!r}")
    rec = next((t for t in _tickets() if t["id"] == ticket_id), None)
    rec = _scoped(u, rec, "set_ticket", args, f"ticket {ticket_id}")
    rec = json.loads(json.dumps(rec))
    for name, value in (("status", status), ("priority", priority), ("category", category)):
        if value is not None:
            rec[name] = value
    st = _state()
    st["tickets"][ticket_id] = rec
    _save_state(st)
    _audit(u["id"], "set_ticket", args, allowed=True, rows_returned=1)
    return rec


def open_ticket(user, customer_id: str, subject: str, body: str) -> dict:
    """A new ticket in the customer's region. Ids from T-90001 so they can never
    collide with the generated range (T-30001..T-30600)."""
    u = _user(user)
    args = {"customer_id": customer_id, "subject": subject, "body": body}
    _require(u, "agent", "open_ticket", args)
    cust = next((c for c in _table("customers") if c["id"] == customer_id), None)
    cust = _scoped(u, cust, "open_ticket", args, f"customer {customer_id}")
    st = _state()
    n = 90001 + sum(1 for tid in st["tickets"] if tid.startswith("T-9"))
    rec = {"id": f"T-{n}", "customer_id": customer_id, "order_id": None, "subject": subject,
           "body": body, "status": "open", "priority": None, "category": None,
           "region": cust["region"], "created": _now(), "comments": []}
    st["tickets"][rec["id"]] = rec
    _save_state(st)
    _audit(u["id"], "open_ticket", args, allowed=True, rows_returned=1)
    return rec


# ── destructive (admin only) ─────────────────────────────────────────────────

def issue_credit(user, customer_id: str, amount: float, reason: str) -> dict:
    """Money leaves the building. Admin only — and in the labs, behind a human
    approval as well. The role check is the floor, not the ceiling."""
    u = _user(user)
    args = {"customer_id": customer_id, "amount": amount, "reason": reason}
    _require(u, "admin", "issue_credit", args)
    if not (isinstance(amount, (int, float)) and amount > 0):
        raise ValueError("amount must be a positive number")
    cust = next((c for c in _table("customers") if c["id"] == customer_id), None)
    _scoped(u, cust, "issue_credit", args, f"customer {customer_id}")
    st = _state()
    rec = {"credit_id": f"CR-{len(st['credits']) + 1:04d}", "customer_id": customer_id,
           "amount": round(float(amount), 2), "reason": reason, "by": u["id"], "at": _now()}
    st["credits"].append(rec)
    _save_state(st)
    _audit(u["id"], "issue_credit", args, allowed=True, rows_returned=1)
    return rec


def authorise_replacement(user, order_id: str, reason: str) -> dict:
    """A unit ships at no charge. Same shape as issue_credit, same rules."""
    u = _user(user)
    args = {"order_id": order_id, "reason": reason}
    _require(u, "admin", "authorise_replacement", args)
    order = next((o for o in _table("orders") if o["id"] == order_id), None)
    order = _scoped(u, order, "authorise_replacement", args, f"order {order_id}")
    st = _state()
    rec = {"replacement_id": f"RP-{len(st['replacements']) + 1:04d}", "order_id": order_id,
           "sku": order["sku"], "item": order["item"], "reason": reason, "by": u["id"], "at": _now()}
    st["replacements"].append(rec)
    _save_state(st)
    _audit(u["id"], "authorise_replacement", args, allowed=True, rows_returned=1)
    return rec


def read_audit(user, limit: int = 100) -> list[dict]:
    """The last `limit` audit lines, newest last. Admin only: the log says who
    looked at what, which is itself sensitive."""
    u = _user(user)
    args = {"limit": limit}
    _require(u, "admin", "read_audit", args)
    lines = AUDIT.read_text(encoding="utf-8").splitlines() if AUDIT.exists() else []
    rows = [json.loads(ln) for ln in lines[-max(0, int(limit)):] if ln.strip()]
    _audit(u["id"], "read_audit", args, allowed=True, rows_returned=len(rows))
    return rows


def reset() -> None:
    """Back to the generated estate: drop every write. The audit log is left
    alone — an audit you can reset is not an audit."""
    if STATE.exists():
        STATE.unlink()


__all__ = ["Denied", "RISK", "resolve_user", "whoami", "get_customer", "find_customers", "get_order",
           "list_orders", "get_ticket", "list_tickets", "search_policies", "get_policy",
           "add_comment", "set_ticket", "open_ticket", "issue_credit", "authorise_replacement",
           "read_audit", "reset"]
