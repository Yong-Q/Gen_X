"""Optional local Firefox QA; uses the host's existing websocket-client package.

This is validation tooling, not a dependency of the static site or its builder.
It never follows external links, executes shell examples, or submits jobs.
"""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid
import websocket

SITE = Path(__file__).resolve().parents[1]
QA = SITE / "qa" / ("browser-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
QA.mkdir()
profile = QA / ".browser-profile"
profile.mkdir(exist_ok=False)
log = (QA / "browser-process.log").open("x")
process = subprocess.Popen(["/usr/bin/firefox", "--headless", "--no-remote", "--profile", str(profile),
                            "--remote-debugging-port", "9237", "about:blank"], stdout=log, stderr=subprocess.STDOUT)
connection = None
events = []
serial = 0


def command(method, params):
    global serial
    serial += 1
    connection.send(json.dumps({"id": serial, "method": method, "params": params}))
    while True:
        message = json.loads(connection.recv())
        if message.get("id") == serial:
            if message.get("type") == "error":
                raise RuntimeError(message)
            return message.get("result", {})
        events.append(message)


def evaluate(expression, context):
    result = command("script.evaluate", {"expression": expression, "target": {"context": context}, "awaitPromise": True})
    if result.get("type") == "exception":
        raise RuntimeError(result)
    return result.get("result", {}).get("value")


try:
    for attempt in range(40):
        try:
            connection = websocket.create_connection("ws://127.0.0.1:9237/session", timeout=15, suppress_origin=True)
            break
        except OSError:
            if process.poll() is not None:
                raise RuntimeError("Firefox exited: " + str(process.returncode))
            time.sleep(.25)
    if connection is None:
        raise RuntimeError("Firefox remote endpoint unavailable")
    browser = command("session.new", {"capabilities": {}})
    command("session.subscribe", {"events": ["log.entryAdded"]})
    context = command("browsingContext.getTree", {})["contexts"][0]["context"]
    checks = []
    for width, height in [(1440, 1000), (390, 844)]:
        command("browsingContext.setViewport", {"context": context, "viewport": {"width": width, "height": height}, "devicePixelRatio": 1})
        for name in sorted(page.stem for page in SITE.glob('*.html')):
            command("browsingContext.navigate", {"context": context, "url": (SITE / (name + ".html")).as_uri(), "wait": "complete"})
            data = json.loads(evaluate("JSON.stringify({width:innerWidth,documentWidth:document.documentElement.scrollWidth,title:document.title,h1:document.querySelectorAll('h1').length,active:document.querySelector('.primary-nav [aria-current=page]').getAttribute('href'),copyButtons:document.querySelectorAll('.copy-button').length,math:document.querySelectorAll('math').length,tableWrappers:document.querySelectorAll('.table-scroll').length,navHidden:getComputedStyle(document.getElementById('sidebar')).display==='none'})", context))
            assert data["documentWidth"] <= width, (name, width, data)
            assert data["h1"] == 1 and data["active"] == name + ".html", data
            assert data["navHidden"] == (width <= 800), data
            if name == "theory":
                scroll = json.loads(evaluate("JSON.stringify((() => {const all=[...document.querySelectorAll('.math-scroll')];const wide=all.filter(e=>e.scrollWidth>e.clientWidth+1);let reachable=true;for(const e of wide){e.scrollLeft=50;reachable=reachable&&e.scrollLeft>0;e.scrollLeft=0;}return {displayEquations:all.length,scrollableEquations:wide.length,contentReachable:reachable};})())", context))
                assert scroll["displayEquations"] >= 26 and scroll["contentReachable"], scroll
                data["formula_scroll"] = scroll
            data.update({"page": name, "viewport": [width, height]})
            checks.append(data)
            if name in ("index", "research", "documentation") or (name == "tutorial" and width == 1440):
                shot = command("browsingContext.captureScreenshot", {"context": context, "origin": "viewport"})
                (QA / (name + "-" + str(width) + ".png")).write_bytes(base64.b64decode(shot["data"]))
            if name == "theory":
                evaluate("(() => {const all=[...document.querySelectorAll('.math-scroll')];const e=all.find(e=>e.scrollWidth>e.clientWidth+1)||all[0];e.scrollIntoView({block:'center'});return true;})()", context)
                shot = command("browsingContext.captureScreenshot", {"context": context, "origin": "viewport"})
                (QA / (name + "-formula-" + str(width) + ".png")).write_bytes(base64.b64decode(shot["data"]))
            if name == "tutorial":
                result = evaluate("(() => {const s=document.getElementById('search-input');s.value='反馈';s.dispatchEvent(new Event('input'));return document.querySelectorAll('#search-results a').length})()", context)
                assert result > 0, "Heading search produced no results"
                evaluate("document.getElementById('search-input').value='';document.getElementById('search-input').dispatchEvent(new Event('input'));true", context)
                if width <= 800:
                    assert evaluate("document.getElementById('menu-toggle').click();document.getElementById('menu-toggle').getAttribute('aria-expanded')", context) == "true"
                    assert evaluate("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));document.getElementById('menu-toggle').getAttribute('aria-expanded')", context) == "false"
                assert evaluate("document.querySelector('.copy-button').click();true", context)
                evaluate("new Promise(resolve=>setTimeout(()=>resolve(document.querySelector('.copy-button').textContent),100))", context)
    errors = [event for event in events if event.get("method") == "log.entryAdded" and event.get("params", {}).get("level") == "error"]
    assert not errors, errors
    report = {"status": "passed", "browser": browser.get("capabilities", {}).get("browserVersion"),
              "checked_utc": datetime.now(timezone.utc).isoformat(), "url_mode": "file://",
              "checks": checks, "console_errors": errors,
              "interactions": ["heading search returns matching links", "mobile menu opens and Escape closes it", "copy button handler runs without errors; clipboard permission may require manual fallback"],
              "scope": "All current HTML pages at desktop and mobile widths; no page overflow, active nav, MathML presence, local JS, menu/search/copy handler checks. Not scientific validation."}
    (QA / "browser-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "passed", "page_viewport_checks": len(checks), "console_errors": len(errors), "report_directory": str(QA)}))
finally:
    if connection:
        try:
            command("browser.close", {})
        except Exception:
            pass
        connection.close()
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    log.close()
    if profile.parent == QA and profile.name == ".browser-profile":
        shutil.rmtree(profile)
