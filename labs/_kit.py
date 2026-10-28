"""Shared plumbing for the FDE Field Kit — carried over from the Level 2/3 kits unchanged, deliberately small and readable.

Everything here is glass-box: open it. The labs import four things —

    client()   an OpenAI client pointed at the class proxy (your .env)
    stages()   the interactive tutor loop: Enter runs a stage, s skips, q quits;
               piped/non-interactive input auto-runs everything (CI-safe)
    say/rule   rich console helpers
    meter      running token/call tally for the session (the cost habit)
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

console = Console()
say = console.print


def rule(title: str) -> None:
    say(Rule(f"[bold]{title}[/bold]", style="yellow"))


def banner(course_line: str, title: str) -> None:
    say(Panel.fit(f"[bold]{course_line}[/bold]\n{title}", border_style="yellow"))


# ── env + client ─────────────────────────────────────────────────────────────

def client() -> OpenAI:
    """Load .env and return a client on the class proxy. Fails with the fix, not a trace.

    MAI_API_KEY is accepted as an alias: the Practice page names that variable
    (it's what the Level 1 kit reads), so a student who follows the page instead
    of the .env comment still works rather than hitting a confusing error."""
    load_dotenv()
    key = (os.environ.get("OPENAI_API_KEY", "") or os.environ.get("MAI_API_KEY", "")).strip()
    if not key or key.startswith("paste-your"):
        say(
            "\n[red]✗ No key found.[/red] Copy .env.example to .env, mint your key at\n"
            "  [bold]https://study.modernaipro.com/practice[/bold] "
            "(button: 'Get my practice key')\n  and paste it into OPENAI_API_KEY.\n"
        )
        sys.exit(1)
    os.environ["OPENAI_API_KEY"] = key  # the SDK reads this one
    if not os.environ.get("OPENAI_BASE_URL", "").strip():
        os.environ["OPENAI_BASE_URL"] = "https://learn.modernaipro.com/api/llm/v1"
        say("[dim](no OPENAI_BASE_URL in .env — defaulting to the class proxy)[/dim]")
    return OpenAI()


MODEL = "mai"  # the proxy picks the class model; this value is ignored by design


# ── the session meter ────────────────────────────────────────────────────────

@dataclass
class Meter:
    """Running cost awareness. Every helper below feeds it; print it any time."""
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    by_label: dict = field(default_factory=dict)

    def add(self, usage, label: str = "call") -> None:
        if not usage:
            return
        self.calls += 1
        self.prompt_tokens += usage.prompt_tokens or 0
        self.completion_tokens += usage.completion_tokens or 0
        row = self.by_label.setdefault(label, [0, 0])
        row[0] += 1
        row[1] += (usage.total_tokens or 0)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def show(self) -> None:
        parts = " · ".join(f"{k} ×{v[0]} ({v[1]} tok)" for k, v in self.by_label.items())
        say(f"[dim]meter: {self.calls} calls · {self.total_tokens} tokens — {parts}[/dim]")


meter = Meter()


# ── observability: one JSON line per request ─────────────────────────────────
# The meter answers "what did this session cost?". A trace answers the questions
# you get asked AFTER something goes wrong: which call was slow, what did we
# actually send, what came back, which one errored. Same idea as Langfuse or
# OpenTelemetry — one span per LLM call — minus everything you don't need yet.
#
#   file    traces.jsonl in the working directory (MAI_TRACE_FILE to move it)
#   format  JSON Lines: one self-contained JSON object per line, append-only,
#           so a crash never corrupts it and `tail -f` shows calls live
#   off     MAI_TRACE=0
#
# Read it with:  python labs/traces.py        (or jq, pandas, DuckDB, …)

TRACE_FILE = Path(os.environ.get("MAI_TRACE_FILE", "traces.jsonl"))
SESSION_ID = uuid.uuid4().hex[:8]   # groups the calls of one process run
_PREVIEW = 300                      # chars of text kept per message


def _clip(text: str) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= _PREVIEW else text[:_PREVIEW] + "…"


def trace(record: dict) -> None:
    """Append one JSON object to the trace file. Never raises — observability
    that can break the app it observes is worse than none."""
    if os.environ.get("MAI_TRACE", "1") == "0":
        return
    try:
        record = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "session": SESSION_ID, **record}
        with TRACE_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:  # noqa: BLE001 — a full disk must not kill the lab
        pass


def _classify_request(messages: list[dict]) -> dict | None:
    """Tag the last user message with a local HF zero-shot model (labs/classify.py).

    Opt-out with MAI_CLASSIFY=0. Imported lazily and only when enabled, because
    importing torch costs ~2s — a lab that isn't using this should not pay it."""
    if os.environ.get("MAI_CLASSIFY", "1") == "0":
        return None
    last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if not last_user:
        return None
    try:
        from classify import classify  # noqa: PLC0415 — deliberately lazy
        return classify(last_user.get("content", ""))
    except Exception:  # noqa: BLE001 — never let tagging break the traced call
        return None


def _traced(label: str, messages: list[dict], kw: dict, started: float,
            *, output: str = "", usage=None, error: Exception | None = None,
            streamed: bool = False) -> None:
    """Build the span for one call and write it."""
    # Stop the clock BEFORE classifying: tagging is our own bookkeeping, and
    # folding its ~110ms (plus a ~2s one-time model load) into latency_ms would
    # make every traced call look slower than the LLM actually was. A metric
    # that measures the measurer is worse than no metric.
    latency_ms = round((time.perf_counter() - started) * 1000)
    classify_started = time.perf_counter()
    tag = _classify_request(messages)
    trace({
        "category": tag["category"] if tag else None,
        "category_score": tag["score"] if tag else None,
        "category_low_confidence": tag["low_confidence"] if tag else None,
        "classify_ms": round((time.perf_counter() - classify_started) * 1000) if tag else None,
        "label": label,
        "model": MODEL,
        "streamed": streamed,
        "latency_ms": latency_ms,
        "ok": error is None,
        "error": f"{type(error).__name__}: {error}" if error else None,
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
        "params": {k: v for k, v in kw.items() if k != "messages"},
        "messages": [{"role": m.get("role"), "content": _clip(m.get("content", ""))}
                     for m in messages],
        "output": _clip(output),
    })


def chat(cli: OpenAI, messages: list[dict], label: str = "chat", **kw) -> str:
    """One metered, traced chat call. kw passes through (max_tokens, response_format, ...).
    Waits out a burst-limit 429 once — eval suites are bursty by nature."""
    started = time.perf_counter()
    for attempt in (1, 2):
        try:
            resp = cli.chat.completions.create(model=MODEL, messages=messages, **kw)
            break
        except Exception as e:  # noqa: BLE001
            if attempt == 1 and "429" in str(e):
                say("[dim](burst limit — waiting 25s, this is the shared classroom lane)[/dim]")
                time.sleep(25)
                continue
            _traced(label, messages, kw, started, error=e)
            raise
    meter.add(resp.usage, label)
    out = (resp.choices[0].message.content or "").strip()
    _traced(label, messages, kw, started, output=out, usage=resp.usage)
    return out


def stream_chat(cli: OpenAI, messages: list[dict], label: str = "stream",
                on_delta=None, **kw) -> str:
    """Streamed chat that degrades honestly.

    Two ways a proxy can fail to stream, and we handle BOTH: it can raise, or it
    can quietly answer a stream request with a normal JSON body (the SDK then
    iterates zero chunks and you'd see a blank screen). If no text arrives, we
    say so and re-ask without streaming — the lesson survives either way."""
    out: list[str] = []
    started = time.perf_counter()
    try:
        stream = cli.chat.completions.create(model=MODEL, messages=messages,
                                             stream=True, **kw)
        usage = None
        for part in stream:
            if getattr(part, "usage", None):
                usage = part.usage
            delta = part.choices[0].delta.content if (part.choices and part.choices[0].delta) else None
            if delta:
                out.append(delta)
                if on_delta:
                    on_delta(delta)
        if out:
            meter.add(usage, label) if usage else setattr(meter, "calls", meter.calls + 1)
            text = "".join(out)
            _traced(label, messages, kw, started, output=text, usage=usage, streamed=True)
            return text
    except Exception as e:  # noqa: BLE001 — transport hiccup, or a proxy that rejects stream=
        _traced(label, messages, kw, started, error=e, streamed=True)
    # the retry below goes through chat(), which writes its own trace line
    say("\n  [dim](this proxy build answered without streaming — same text, "
        "delivered all at once)[/dim]\n  ")
    text = chat(cli, messages, label=label, **kw)
    if on_delta:
        on_delta(text)
    return text


# ── the tutor loop ───────────────────────────────────────────────────────────
# Every stage teaches in the same shape, on purpose:
#
#   WHY        the reasoning — what problem exists and why you should care,
#              BEFORE any code runs (so you know what to watch for)
#   the demo   the fn — code + live model calls you can read and rerun
#   THE LOGIC  what the observation you just made PROVES, and the rule
#              you can carry to your own systems
#
# Claim → evidence → conclusion. If a stage can't fill all three, it isn't
# teaching — that's the bar for adding one.

@dataclass
class Stage:
    title: str
    why: str          # the reasoning, shown before the demo
    fn: object        # callable(cli) — the demonstration
    logic: str        # the conclusion the evidence supports, shown after


def stages(cli: OpenAI, steps: list[Stage]) -> None:
    """Run Stage(title, why, fn, logic) steps. Interactive: Enter/s/q. Piped: auto-run."""
    interactive = sys.stdin.isatty()
    for i, st in enumerate(steps, 1):
        rule(f"Stage {i}/{len(steps)} · {st.title}")
        say(Panel(st.why.strip(), title="[bold]why[/bold]", title_align="left",
                  border_style="blue", padding=(0, 2)))
        if interactive:
            ans = input("  Enter to run · s skip · q quit > ").strip().lower()
            if ans == "q":
                break
            if ans == "s":
                continue
        st.fn(cli)
        say(Panel(st.logic.strip(), title="[bold]the logic[/bold]", title_align="left",
                  border_style="green", padding=(0, 2)))
        meter.show()
    say()
    say(Panel.fit("[bold green]Lab complete.[/bold green] git pull before the next session.",
                  border_style="green"))


def ask_yn(prompt: str, default: bool = True) -> bool:
    """Interactive yes/no; piped input takes the default (CI-safe)."""
    if not sys.stdin.isatty():
        return default
    ans = input(f"  {prompt} [{'Y/n' if default else 'y/N'}] > ").strip().lower()
    if not ans:
        return default
    return ans.startswith("y")
