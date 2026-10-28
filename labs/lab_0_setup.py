# -*- coding: utf-8 -*-
"""Lab 0 — DOES IT WORK?

Modern AI Pro · FDE Field Kit · run this before Friday

Four checks, one command, and the fix printed next to anything that fails:

    1  Python and the install     the version, and the packages the labs import
    2  Your key                   what .env actually loaded, then one tiny call
    3  The customer's estate      Calder & Rowe loads; you are who .env says you are
    4  The estate over MCP        the server starts, lists its tools, answers one call

    python labs/lab_0_setup.py

Nothing here is a lesson. It exists because the worst moment to discover a
broken laptop is Saturday morning, in a room of forty people, with the wedge
lab already started.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROWS: list[tuple[str, bool, str]] = []


def row(name: str, ok: bool, detail: str = "") -> None:
    ROWS.append((name, ok, detail))
    mark = "\033[32m✓\033[0m" if ok else "\033[31m✗\033[0m"
    print(f"  {mark} {name}" + (f"  —  {detail}" if detail else ""))


# ── 1 · python and the install ───────────────────────────────────────────────

def check_python() -> bool:
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 10)
    row("Python 3.10+", ok, f"{v.major}.{v.minor}.{v.micro} at {sys.executable}"
        + ("" if ok else "  → install 3.12 from python.org"))
    missing = []
    for mod in ("openai", "dotenv", "rich", "mcp"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    row("packages installed", not missing,
        "openai · python-dotenv · rich · mcp" if not missing
        else f"missing {', '.join(missing)}  → activate the venv, then: pip install -r requirements.txt")
    return ok and not missing


# ── 2 · the key ──────────────────────────────────────────────────────────────

def check_key() -> bool:
    from dotenv import load_dotenv
    load_dotenv()
    key = (os.environ.get("OPENAI_API_KEY", "") or os.environ.get("MAI_API_KEY", "")).strip()
    base = os.environ.get("OPENAI_BASE_URL", "").strip()
    if not key or key.startswith("paste-your"):
        row("key in .env", False, "no key loaded  → cp .env.example .env and paste the key from Mahalakshmi's email")
        return False
    shape = f"{key[:4]}…{key[-3:]} ({len(key)} chars)"
    if key.startswith("mai_") and not base:
        row("key + base URL travel together", False,
            f"{shape} is a class key but OPENAI_BASE_URL is empty  → restore the line from .env.example")
        return False
    if not key.startswith("mai_") and base:
        row("key + base URL travel together", False,
            f"{shape} is a personal key but OPENAI_BASE_URL is set  → remove that line, or use the class key")
        return False
    row("key in .env", True, f"{shape} · base {base or '(OpenAI default)'}")
    try:
        from openai import OpenAI
        os.environ["OPENAI_API_KEY"] = key
        r = OpenAI().chat.completions.create(model="mai", messages=[{"role": "user", "content": "Reply with the single word OK."}], max_tokens=5)
        text = (r.choices[0].message.content or "").strip()
        row("one call to the class model", True, f"it said {text!r} · {r.usage.total_tokens} tokens")
        return True
    except Exception as e:  # noqa: BLE001 — the message IS the diagnosis here
        msg = str(e)
        hint = ""
        if "401" in msg and "window has ended" in msg:
            hint = "  → this key has expired; use the FDE key from Mahalakshmi's email"
        elif "401" in msg:
            hint = "  → check the key was pasted whole, and that the base URL line is present"
        row("one call to the class model", False, msg[:140] + hint)
        return False


# ── 3 · the estate ───────────────────────────────────────────────────────────

def check_estate() -> bool:
    try:
        import _estate
    except Exception as e:  # noqa: BLE001
        row("estate loads", False, f"{type(e).__name__}: {e}  → git pull, then pip install -r requirements.txt")
        return False
    user = os.environ.get("ESTATE_USER", "viewer.sam")
    try:
        me = _estate.whoami(user)
        row("estate loads", True, f"you are {me['id']} · role {me['role']} · regions {', '.join(me['regions'])}")
    except Exception as e:  # noqa: BLE001
        row("estate loads", False, f"ESTATE_USER={user!r}: {e}  → pick an id from estate/data/identity.json")
        return False
    try:
        tickets = _estate.list_tickets(user, limit=3)
        row("you can see tickets in your regions", bool(tickets),
            f"{len(tickets)} shown · first: {tickets[0]['id']} · {tickets[0]['subject'][:50]}" if tickets else "none returned")
        return bool(tickets)
    except Exception as e:  # noqa: BLE001
        row("you can see tickets in your regions", False, f"{type(e).__name__}: {e}")
        return False


# ── 4 · the estate over MCP ──────────────────────────────────────────────────

async def _mcp_probe(user: str) -> tuple[int, str]:
    from _mcp_client import call, estate_session
    async with estate_session(user) as session:
        listed = await session.list_tools()
        tools = listed.tools
        text = await call(session, "whoami", {})
        return len(tools), text


def check_mcp() -> bool:
    user = os.environ.get("ESTATE_USER", "viewer.sam")
    try:
        n, text = asyncio.run(asyncio.wait_for(_mcp_probe(user), timeout=40))
        row("estate server over MCP", True, f"{n} tools listed · whoami → {text[:60]}")
        return True
    except Exception as e:  # noqa: BLE001
        row("estate server over MCP", False, f"{type(e).__name__}: {str(e)[:120]}  → pip install -r requirements.txt; then ask in the cohort room with this line")
        return False


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    os.chdir(Path(__file__).resolve().parent.parent)   # .env and estate/ are repo-relative
    print("\nFDE Field Kit · setup check\n")
    ok = check_python()
    ok = check_key() and ok
    ok = check_estate() and ok
    ok = check_mcp() and ok
    print()
    if ok:
        print("  \033[32mAll four pass. You are set for Friday.\033[0m  Next: python labs/lab_1_discovery.py\n")
        return 0
    failed = [n for n, k, _ in ROWS if not k]
    print(f"  \033[31m{len(failed)} to fix:\033[0m " + " · ".join(failed))
    print("  Each line above says what to do. Still stuck? Reply to the setup email with this whole output.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
