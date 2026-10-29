"""Exercise both browser CLIs against a disposable loopback-only fixture."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[2]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run(tool_root, node):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'tools/choms-skills/fixtures')))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    browser = next((tool_root / 'browsers').glob('chromium-1247/chrome-linux64/chrome'))
    env = os.environ | {'PATH': str(node.parent) + os.pathsep + os.environ['PATH'],
                        'PLAYWRIGHT_BROWSERS_PATH': str(tool_root / 'browsers')}
    url = f'http://127.0.0.1:{server.server_port}/browser.html'
    with tempfile.TemporaryDirectory(prefix='choms-cli-fixtures-') as tmp:
        work = Path(tmp)
        env |= {'AGENT_BROWSER_SOCKET_DIR': os.environ.get('AGENT_BROWSER_SOCKET_DIR', str(work / 's')), 'XDG_CACHE_HOME': str(work / 'cache')}
        (work / 's').mkdir()
        (work / 'agent.json').write_text('{}')
        env['AGENT_BROWSER_CONFIG'] = str(work / 'agent.json')
        (work / 'cli.json').write_text(json.dumps({'browser': {'browserName': 'chromium', 'isolated': True,
            'launchOptions': {'executablePath': str(browser), 'headless': True, 'chromiumSandbox': False}}}))
        cli = [str(node), str(tool_root / 'node_modules/@playwright/cli/playwright-cli.js'), '-s=choms-synthetic']
        agent = [str(tool_root / 'node_modules/agent-browser/bin/agent-browser-linux-x64'),
                 '--namespace', 'ch' + work.name[-6:], '--session', 't',
                 '--executable-path', str(browser), '--args', '--no-sandbox']

        def command(prefix, args):
            result = subprocess.run(prefix + args, cwd=work, env=env, capture_output=True, text=True, timeout=45)
            if result.returncode:
                raise RuntimeError('CLI fixture failed: ' + result.stderr[:400] + result.stdout[:400])
            return result.stdout
        try:
            command(cli, ['open', url, '--config', str(work / 'cli.json')])
            snapshot = command(cli, ['snapshot'])
            assert 'Nombre del fixture' in snapshot, 'CLI snapshot'
            command(cli, ['eval', '() => { document.querySelector("#name").value = "sintético"; document.querySelector("button").click(); }'])
            status = command(cli, ['eval', '() => document.querySelector("#status").textContent'])
            assert 'Fixture válido' in status, 'CLI form'
        finally:
            command(cli, ['close'])
        try:
            command(agent, ['open', url])
            assert 'Nombre del fixture' in command(agent, ['snapshot']), 'Agent snapshot'
            command(agent, ['fill', '#name', 'sintético'])
            command(agent, ['click', 'button'])
            command(agent, ['wait', '--text', 'Fixture válido'])
            assert 'Fixture válido' in command(agent, ['get', 'text', '#status']), 'Agent form'
        finally:
            command(agent, ['close'])
    server.shutdown(); server.server_close(); thread.join(timeout=3)
    return {'status': 'PASS', 'playwright_cli': ['open', 'snapshot', 'eval', 'form', 'close'],
            'agent_browser': ['open', 'snapshot', 'fill', 'click', 'get', 'close'], 'inferences': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-root', type=Path, required=True); parser.add_argument('--node', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(run(args.tool_root.resolve(), args.node.resolve()), sort_keys=True))
