# -*- coding: utf-8 -*-
"""The chat page for lab 2b, in the standard library — given, so the lab's
tokens go on the agents and not on a UI.

    from _chat_web import serve
    serve(runner, host="127.0.0.1", port=7866, title="...")

Two JSON endpoints, both POST: /api/chat {thread, text} and /api/resume
{thread, decision}. The page keeps the thread id; the graph keeps the state.

Binding: 127.0.0.1 by default. Any other host (Docker, a cloud box) requires
CHAT_SECRET in the environment, sent back as the X-Chat-Secret header; the page
reads it from ?k=... once and keeps it in memory, never in the URL it shows.
A chat that holds a live key, reachable without a secret, is somebody else's
token bill by Monday.
"""
from __future__ import annotations

import hmac
import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>__TITLE__</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#f6f4ef;color:#1a1713;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:860px;margin:0 auto;padding:24px 16px 120px}
h1{font-size:20px;margin:0 0 2px}.sub{color:#6b6358;font-size:13px;margin:0 0 18px}
.msg{padding:12px 14px;border-radius:12px;margin:8px 0;max-width:80%;white-space:pre-wrap}
.you{background:#1a1713;color:#f6f4ef;margin-left:auto}
.desk{background:#fff;border:1px solid #c9c3b5}
.hop{font-size:12px;color:#6b6358;margin:4px 0 4px 8px}
.hop b{color:#8a6508}
.gate{background:#fff6f4;border:1px solid #c0392b;border-radius:12px;padding:12px 14px;margin:10px 0}
.gate code{display:block;font-size:12px;white-space:pre-wrap;margin:6px 0}
button{font:inherit;border-radius:8px;border:1px solid #1a1713;background:#1a1713;color:#f6f4ef;padding:7px 14px;cursor:pointer}
button.no{background:#fff;color:#1a1713}
form{position:fixed;left:0;right:0;bottom:0;background:#f6f4ef;border-top:1px solid #c9c3b5;padding:12px 16px}
form div{max-width:860px;margin:0 auto;display:flex;gap:8px}
input{flex:1;font:inherit;padding:10px 12px;border:1px solid #c9c3b5;border-radius:8px;background:#fff}
.err{color:#c0392b;font-size:13px}
</style></head><body><div class="wrap">
<h1>__TITLE__</h1><p class="sub">Modern AI Pro · FDE Field Kit · lab 2b · a router, three specialists, one gate. Every write pauses here until you answer.</p>
<div id="log"></div></div>
<form id="f"><div><input id="t" autocomplete="off" placeholder="Ask the desk — e.g. what is the status of T-30535?"><button>Send</button></div></form>
<script>
const thread = Math.random().toString(16).slice(2,10);
const key = new URLSearchParams(location.search).get('k') || '';
if (key) history.replaceState(null, '', location.pathname);
const log = document.getElementById('log');
function add(cls, text){const d=document.createElement('div');d.className=cls;d.textContent=text;log.appendChild(d);window.scrollTo(0,document.body.scrollHeight);return d}
function render(out){
  for (const m of out.messages){
    if (m.role==='ai' && m.tool_calls.length) add('hop', (m.name||'agent')+' → '+m.tool_calls.join(', '));
    else if (m.role==='tool') add('hop', '← '+m.text.slice(0,140));
    else if (m.role==='ai' && m.name==='answer') add('msg desk', m.text);
    else if (m.role==='ai' && m.text) {const d=add('hop',''); d.innerHTML='<b>'+m.name+'</b>: '+m.text.slice(0,300).replace(/</g,'&lt;')}
  }
  if (out.pending){
    const g=document.createElement('div');g.className='gate';
    g.innerHTML='<b>GATE</b> — '+out.pending.tool+' wants to run as you.<code>'+JSON.stringify(out.pending.args,null,1).replace(/</g,'&lt;')+'</code>';
    const y=document.createElement('button');y.textContent='Approve';const n=document.createElement('button');n.textContent='Reject';n.className='no';n.style.marginLeft='8px';
    y.onclick=()=>decide(g,'approve');n.onclick=()=>decide(g,'reject');g.appendChild(y);g.appendChild(n);log.appendChild(g);window.scrollTo(0,document.body.scrollHeight);
  }
}
async function post(path, body){
  const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Chat-Secret':key},body:JSON.stringify(body)});
  if(!r.ok){add('err','server said '+r.status+': '+(await r.text()).slice(0,200));return null}
  return r.json();
}
async function decide(g, d){g.querySelectorAll('button').forEach(b=>b.disabled=true);add('hop','you → '+d);const out=await post('/api/resume',{thread,decision:d});if(out)render(out)}
document.getElementById('f').onsubmit=async e=>{e.preventDefault();const t=document.getElementById('t');const text=t.value.trim();if(!text)return;t.value='';add('msg you',text);const out=await post('/api/chat',{thread,text});if(out)render(out)};
</script></body></html>"""


def serve(runner, host: str = "127.0.0.1", port: int = 7866, title: str = "the desk") -> None:
    secret = os.environ.get("CHAT_SECRET", "")
    if host != "127.0.0.1" and not secret:
        sys.exit("refusing to bind " + host + " without CHAT_SECRET in the environment (see docs/GRAPH.md)")
    page = PAGE.replace("__TITLE__", title).encode()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str = "application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.split("?")[0] != "/":
                return self._send(404, b"not found", "text/plain")
            self._send(200, page, "text/html")

        def do_POST(self):
            if secret and not hmac.compare_digest(self.headers.get("X-Chat-Secret", ""), secret):
                return self._send(401, b"secret missing or wrong", "text/plain")
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or b"{}"))
                thread = str(body.get("thread", ""))[:32] or "default"
                if self.path == "/api/chat":
                    out = runner.turn(thread, text=str(body.get("text", ""))[:4000])
                elif self.path == "/api/resume":
                    out = runner.turn(thread, resume=str(body.get("decision", "reject"))[:16])
                else:
                    return self._send(404, b"not found", "text/plain")
                self._send(200, json.dumps(out, ensure_ascii=False, default=str).encode())
            except Exception as e:  # noqa: BLE001 — show the student the error, not a blank page
                self._send(500, f"{type(e).__name__}: {e}".encode(), "text/plain")

    srv = ThreadingHTTPServer((host, port), H)
    url = f"http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}/" + (f"?k={secret}" if secret else "")
    print(f"  chat page → {url if not secret else url.split('?')[0] + '?k=<CHAT_SECRET>'}   (Ctrl-C to stop)")
    if host == "127.0.0.1":
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
