"""Bounded no-inference JSONL MCP probe. Runs only the explicitly supplied command."""
import argparse
import json
from pathlib import Path
import selectors
import subprocess
import tempfile


def probe(command, browser=False):
    temp = tempfile.TemporaryDirectory(prefix='choms-mcp-browser-') if browser else None
    process = subprocess.Popen(command, cwd=temp.name if temp else None, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, bufsize=1)
    selector = selectors.DefaultSelector(); selector.register(process.stdout, selectors.EVENT_READ)
    counter = 0

    def call(method, params):
        nonlocal counter
        counter += 1
        process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': counter, 'method': method, 'params': params}) + '\n')
        process.stdin.flush()
        while True:
            if not selector.select(20):
                raise RuntimeError('MCP timeout')
            line = process.stdout.readline()
            if not line:
                raise RuntimeError('MCP closed')
            value = json.loads(line)
            if value.get('id') == counter:
                return value

    try:
        init = call('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                                 'clientInfo': {'name': 'choms-offline-probe', 'version': '1.0.0'}})
        assert 'result' in init, 'initialize'
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n'); process.stdin.flush()
        tools = call('tools/list', {})['result']['tools']
        assert len({t['name'] for t in tools}) == len(tools) > 0, 'tool_names'
        assert all(t['inputSchema']['type'] == 'object' for t in tools), 'schemas'
        if browser:
            names = {t['name'] for t in tools}
            assert 'browser_navigate' in names, 'browser_tool'
            # No external navigation. about:blank has no user data or remote assets.
            reply = call('tools/call', {'name': 'browser_navigate', 'arguments': {'url': 'about:blank'}})
            assert not reply.get('error') and not reply['result'].get('isError'), 'browser_navigation'
            close = call('tools/call', {'name': 'browser_close', 'arguments': {}})
            assert not close.get('error') and not close['result'].get('isError'), 'browser_close'
        else:
            brief = json.loads((Path(__file__).resolve().parents[2] / 'tools/choms-skills/fixtures/design-brief.json').read_text())
            valid = call('tools/call', {'name': 'validate_design_brief', 'arguments': brief})
            assert valid['result']['isError'] is False, 'valid_call'
            invalid = call('tools/call', {'name': 'validate_design_brief', 'arguments': {}})
            assert invalid['result']['isError'] is True, 'invalid_call'
            assert call('choms/unknown', {})['error']['code'] == -32601, 'unknown_method'
        return {'status': 'PASS', 'tools': len(tools), 'protocol': init['result']['protocolVersion'],
                'inferences': 0, 'scope': 'Playwright about:blank' if browser else 'local design fixture'}
    finally:
        selector.close()
        process.stdin.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)
        process.stdout.close()
        if temp:
            temp.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('explicit command required after --')
    print(json.dumps(probe(command, args.browser), sort_keys=True))
