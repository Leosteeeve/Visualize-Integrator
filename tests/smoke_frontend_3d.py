from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

try:
    import websocket
except Exception as exc:  # pragma: no cover - optional local smoke dependency
    raise SystemExit(f"skip - websocket module unavailable: {exc}")


ROOT = Path(__file__).resolve().parents[1]
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
URL = "http://127.0.0.1:8000"


def request_json(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    if not EDGE.exists():
        raise SystemExit("skip - Microsoft Edge not found")

    user_data = Path(tempfile.mkdtemp(prefix="calculus-edge-", dir=str(ROOT)))
    process = subprocess.Popen(
        [
            str(EDGE),
            "--headless=new",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--remote-debugging-port=9333",
            "--remote-allow-origins=http://127.0.0.1:9333",
            f"--user-data-dir={user_data}",
            "--window-size=1440,1000",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    counter = 0

    def call(method: str, params: dict | None = None):
        nonlocal counter
        counter += 1
        ws.send(json.dumps({"id": counter, "method": method, "params": params or {}}))
        while True:
            message = json.loads(ws.recv())
            if message.get("id") == counter:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    try:
        for _ in range(40):
            try:
                tabs = request_json("http://127.0.0.1:9333/json")
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("Edge debugging endpoint did not start")

        page = next(
            (
                tab
                for tab in tabs
                if tab.get("type") == "page" and not str(tab.get("url", "")).startswith("chrome-extension:")
            ),
            None,
        )
        if page is None:
            raise RuntimeError(f"No debuggable page target found: {tabs!r}")

        ws_url = page["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url, timeout=35)
        try:
            call("Runtime.enable")
            call("Page.enable")
            call("Page.navigate", {"url": URL})
            time.sleep(2.0)
            expression = """
            (async () => {
              const waitFor = async (selector, timeout = 10000) => {
                const start = Date.now();
                while (Date.now() - start < timeout) {
                  const node = document.querySelector(selector);
                  if (node) return node;
                  await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error(`Timed out waiting for ${selector}`);
              };
              const waitUntil = async (predicate, timeout = 15000, label = 'condition') => {
                const start = Date.now();
                while (Date.now() - start < timeout) {
                  if (predicate()) return;
                  await new Promise((resolve) => setTimeout(resolve, 150));
                }
                throw new Error(`Timed out waiting for ${label}`);
              };
              try {
                const cases = [
                  { preset: 'washer_x', expression: 'x', inner: '0' },
                  { preset: 'shell_y', expression: '1-x', inner: '0' },
                ];
                const results = [];
                await waitFor('[data-mode="solid_revolution"]');
                document.querySelector('[data-mode="solid_revolution"]').click();
                for (const item of cases) {
                  document.querySelector('#solidPreset').value = item.preset;
                  document.querySelector('#solidPreset').dispatchEvent(new Event('change', { bubbles: true }));
                  document.querySelector('#expression').value = item.expression;
                  document.querySelector('#solidInnerExpression').value = item.inner;
                  document.querySelector('#lower').value = '0';
                  document.querySelector('#upper').value = '1';
                  await waitUntil(() => !document.querySelector('#calculate').disabled, 15000, 'calculate button');
                  document.querySelector('#calculate').click();
                  await waitUntil(() => !document.querySelector('#calculate').disabled, 20000, 'solid calculation');
                  await new Promise((resolve) => setTimeout(resolve, 1200));
                  const host = document.querySelector('#threePlot');
                  const canvas = host?.querySelector('canvas');
                  const rect = canvas?.getBoundingClientRect();
                  results.push({
                    preset: item.preset,
                    hasCanvas: Boolean(canvas),
                    hidden: host?.hidden,
                    width: rect?.width || 0,
                    height: rect?.height || 0,
                    title: document.querySelector('#plotTitle')?.textContent || '',
                    status: document.querySelector('#statusResult')?.textContent || '',
                    exact: document.querySelector('#exactResult')?.textContent || '',
                    messages: document.querySelector('#messages')?.textContent || '',
                  });
                }
                return {
                  results,
                  bodyStart: document.body.innerText.slice(0, 200),
                };
              } catch (error) {
                return {
                  error: String(error && error.message ? error.message : error),
                  url: location.href,
                  readyState: document.readyState,
                  bodyStart: document.body.innerText.slice(0, 300),
                };
              }
            })()
            """
            result = call("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True})
            if "exceptionDetails" in result:
                raise RuntimeError(result["exceptionDetails"])
            value = result["result"].get("value")
            print(json.dumps(value, ensure_ascii=False))
            if value and value.get("error"):
                raise RuntimeError(value["error"])
            for item in value["results"]:
                assert item["hasCanvas"], f"Three.js canvas was not created for {item['preset']}"
                assert item["hidden"] is False, f"3D host is hidden for {item['preset']}"
                assert item["width"] >= 300 and item["height"] >= 260, f"3D canvas size is too small for {item['preset']}"
                assert "pi" in item["exact"].lower() or "π" in item["exact"], f"solid result did not render for {item['preset']}"

            screenshot = call("Page.captureScreenshot", {"format": "png"})
            image_path = ROOT / "solid-3d-smoke.png"
            image_path.write_bytes(base64.b64decode(screenshot["data"]))
            print(f"screenshot={image_path}")
        finally:
            ws.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(user_data, ignore_errors=True)


if __name__ == "__main__":
    main()
