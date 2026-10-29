#!/usr/bin/env python3
"""User-only pinned Skills runtime. No sudo, credentials, inference or services."""
import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid
import zipfile

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = REPO / 'tools/choms-skills/runtime/RUNTIME.lock.json'
DEFAULT_ROOT = Path.home() / '.local/share/choms-skills/runtime'


def digest(path, algorithm='sha256'):
    with path.open('rb') as source:
        return hashlib.file_digest(source, algorithm).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.new-' + uuid.uuid4().hex)
    with temporary.open('x') as out:
        os.chmod(temporary, 0o600)
        json.dump(value, out, ensure_ascii=False, sort_keys=True, indent=2); out.write('\n')
        out.flush(); os.fsync(out.fileno())
    temporary.replace(path)


def inside(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('unsafe_path')
    return path


def atomic_link(path, target):
    temporary = path.with_name(path.name + '.new-' + uuid.uuid4().hex)
    temporary.symlink_to(target)
    temporary.replace(path)


def manifest(root):
    result = {}
    for path in sorted(root.rglob('*')):
        name = str(path.relative_to(root))
        if name == 'MANIFEST.json':
            continue
        if path.is_symlink():
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError('external_symlink:' + name)
            result[name] = {'link': os.readlink(path)}
        elif path.is_file():
            result[name] = {'sha256': digest(path), 'mode': stat.S_IMODE(path.stat().st_mode)}
        elif not path.is_dir():
            raise ValueError('unsupported_file_type:' + name)
    return result


class Runtime:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = root.resolve()
        for name in ('downloads', 'releases', 'seals', 'receipts', 'work', 'sockets', 'bin'):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        with (self.root / '.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def release(self, ident):
        if not re.fullmatch('[0-9a-f]{32}', ident):
            raise ValueError('invalid_release_id')
        return self.root / 'releases' / ident

    def current(self, pointer='current'):
        path = self.root / pointer
        if not path.is_symlink():
            raise ValueError('no_' + pointer + '_release')
        ident = path.resolve().name
        if path.resolve() != self.release(ident):
            raise ValueError('pointer_outside_managed_releases')
        return ident

    def fetch(self, url, expected, algorithm, offline):
        lengths={'sha256':64,'sha512':128}
        if algorithm not in lengths or not re.fullmatch('[0-9a-f]{'+str(lengths.get(algorithm,0))+'}',expected):
            raise ValueError('invalid_expected_digest')
        if not url.startswith('https://'):
            raise ValueError('https_required')
        path = self.root / 'downloads' / expected
        if path.exists():
            if digest(path, algorithm) != expected:
                raise ValueError('corrupt_cached_artifact')
            return path
        if offline:
            raise ValueError('offline_artifact_missing')
        temporary = path.with_name(path.name + '.partial-' + uuid.uuid4().hex)
        try:
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open('xb') as out:
                while block := response.read(1024 * 1024):
                    out.write(block)
            if digest(temporary, algorithm) != expected:
                raise ValueError('download_checksum_mismatch')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def unpack(self, archive, destination, kind):
        destination.mkdir(parents=True, exist_ok=True)
        if kind == 'zip':
            with zipfile.ZipFile(archive) as source:
                for member in source.infolist():
                    target = inside(destination, member.filename)
                    if stat.S_ISLNK(member.external_attr >> 16):
                        raise ValueError('zip_symlink_not_supported')
                    if member.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with source.open(member) as src, target.open('xb') as out:
                            shutil.copyfileobj(src, out)
                        target.chmod(0o755 if member.external_attr >> 16 & 0o111 else 0o644)
        else:
            with tarfile.open(archive) as source:
                members = source.getmembers()
                if kind == 'npm':
                    for member in members:
                        if not member.name.startswith('package/'):
                            raise ValueError('unexpected_npm_archive_root')
                        member.name = member.name[len('package/'):]
                for member in members:
                    inside(destination, member.name)
                source.extractall(destination, members=members, filter='data')

    def prepare(self, lock_path, offline=False):
        raw = lock_path.read_bytes(); lock = json.loads(raw)
        if sys.version_info < tuple(map(int,lock['python_minimum'].split('.'))):
            raise ValueError('host_python_too_old')
        if lock['schema_version'] != 1 or lock['platform'] != 'linux-x86_64' or platform.machine() != 'x86_64' or sys.platform != 'linux':
            raise ValueError('unsupported_platform_or_schema')
        ident = hashlib.sha256(raw).hexdigest()[:32]; final = self.release(ident)
        if final.exists():
            self.verify(ident)
            return ident
        package_lock = REPO / 'tools/choms-skills/toolchain/package-lock.json'
        package_json = REPO / 'tools/choms-skills/toolchain/package.json'
        if digest(package_lock) != lock['npm_package_lock_sha256'] or digest(package_json) != lock['npm_package_json_sha256']:
            raise ValueError('npm_lock_changed')
        for name, sha in lock['helpers'].items():
            if digest(inside(REPO, name)) != sha:
                raise ValueError('helper_changed:' + name)
        # Failed stages remain under the managed root for diagnosis, never promoted.
        stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=self.root / 'releases'))
        for artifact in lock['artifacts']:
            source = self.fetch(artifact['url'], artifact['sha256'], 'sha256', offline)
            target = inside(stage, artifact['destination'])
            if artifact['kind'] == 'file':
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target); target.chmod(0o755)
            else:
                self.unpack(source, target, artifact['kind'])
        packages = json.loads(package_lock.read_text())['packages']
        for name, entry in packages.items():
            if not name:
                continue
            if not name.startswith('node_modules/') or not entry['resolved'].startswith('https://registry.npmjs.org/'):
                raise ValueError('unexpected_npm_source')
            algorithm, encoded = entry['integrity'].split('-', 1)
            if algorithm != 'sha512':
                raise ValueError('npm_sha512_required')
            source = self.fetch(entry['resolved'], base64.b64decode(encoded, validate=True).hex(), algorithm, offline)
            self.unpack(source, inside(stage, name), 'npm')
        shutil.copyfile(package_json, stage / 'package.json'); shutil.copyfile(package_lock, stage / 'package-lock.json')
        (stage / 'package.json').chmod(0o644); (stage / 'package-lock.json').chmod(0o644)
        (stage / 'node_modules/agent-browser/bin/agent-browser-linux-x64').chmod(0o755)
        for name in lock['helpers']:
            target = inside(stage / 'app', name); target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, target); target.chmod(0o644)
        (stage / 'bin').mkdir()
        for name, target in {'node': '../' + lock['node_directory'] + '/bin/node', 'ffmpeg': '../ffmpeg-linux-x64', 'ffprobe': '../ffprobe-linux-x64'}.items():
            (stage / 'bin' / name).symlink_to(target)
        (stage / 'LOCK.json').write_bytes(raw); (stage / 'LOCK.json').chmod(0o644)
        # Playwright writes this host-dependency marker on first launch. Perform
        # the real probe before sealing; do not exempt unexpected post-seal files.
        node = stage / lock['node_directory'] / 'bin/node'
        code = "const {chromium}=require('@playwright/test'); (async()=>{const b=await chromium.launch({headless:true}); await b.close();})().catch(e=>{console.error(e.message);process.exit(1);});"
        probe = subprocess.run([str(node), '-e', code], cwd=stage, env=self.environment(stage), capture_output=True, text=True, timeout=60)
        if probe.returncode:
            raise ValueError('host_browser_probe_failed:' + probe.stderr[:400])
        for marker in (stage / 'browsers').glob('*/DEPENDENCIES_VALIDATED'):
            if marker.read_bytes() != b'':
                raise ValueError('unexpected_dependency_marker_content')
            marker.chmod(0o644)
        write_json(stage / 'MANIFEST.json', manifest(stage))
        seal = {'manifest_sha256': digest(stage / 'MANIFEST.json'), 'lock_sha256': hashlib.sha256(raw).hexdigest()}
        stage.rename(final); write_json(self.root / 'seals' / (ident + '.json'), seal)
        self.verify(ident)
        return ident

    def verify(self, ident):
        release = self.release(ident)
        seal = json.loads((self.root / 'seals' / (ident + '.json')).read_text())
        if digest(release / 'MANIFEST.json') != seal['manifest_sha256'] or digest(release / 'LOCK.json') != seal['lock_sha256'] or seal['lock_sha256'][:32] != ident:
            raise ValueError('release_seal_mismatch')
        expected = json.loads((release / 'MANIFEST.json').read_text())
        if manifest(release) != expected:
            raise ValueError('release_integrity_mismatch')
        return {'status': 'PASS', 'release': ident, 'files_and_links': len(expected)}

    def environment(self, release):
        lock = json.loads((release / 'LOCK.json').read_text())
        env = os.environ.copy()
        for name in list(env):
            if name.startswith(('AGENT_BROWSER_', 'PLAYWRIGHT_CLI_')):
                del env[name]
        agent_config = self.root / 'work/agent-default.json'
        if not agent_config.exists():
            write_json(agent_config, {})
        if json.loads(agent_config.read_text()) != {}:
            raise ValueError('managed_agent_config_changed')
        env.update({'PATH': str(release / 'bin') + os.pathsep + str(release / lock['node_directory'] / 'bin') + os.pathsep + env['PATH'],
            'PLAYWRIGHT_BROWSERS_PATH': str(release / 'browsers'), 'TMPDIR': str(self.root / 'work'),
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(release / 'vendor/pyyaml-6.0.3/lib'),
            'AGENT_BROWSER_SOCKET_DIR': str(self.root / 'sockets'), 'AGENT_BROWSER_CONFIG': str(agent_config),
            'AGENT_BROWSER_EXECUTABLE_PATH': str(release / lock['browser_executable']), 'XDG_CACHE_HOME': str(self.root / 'work/cache')})
        return env

    def command(self, ident, tool, args):
        release = self.release(ident); lock = json.loads((release / 'LOCK.json').read_text())
        node = str(release / lock['node_directory'] / 'bin/node')
        app = release / 'app/scripts/skills'
        commands = {'node': [node], 'playwright-cli': [node, str(release / 'node_modules/@playwright/cli/playwright-cli.js')],
            'playwright-mcp': [node, str(release / 'node_modules/@playwright/mcp/cli.js'), '--headless', '--isolated', '--executable-path', str(release / lock['browser_executable']), '--allowed-origins', 'http://127.0.0.1:*'],
            'agent-browser': [str(release / 'node_modules/agent-browser/bin/agent-browser-linux-x64')],
            'ffmpeg': [str(release / 'ffmpeg-linux-x64')], 'ffprobe': [str(release / 'ffprobe-linux-x64')],
            'gitleaks': [str(release / 'gitleaks/gitleaks')],
            'local-tools': [sys.executable, str(app / 'local_tools.py')],
            'design-mcp': [sys.executable, str(app / 'design_mcp.py')],
            'mcp-probe': [sys.executable, str(app / 'mcp_probe.py')],
            'browser-qa': [node, str(app / 'browser_qa.cjs'), '--tool-root', str(release)],
            'cli-smoke': [sys.executable, str(app / 'cli_smoke.py'), '--tool-root', str(release), '--node', node],
            'validate-profile': [sys.executable, str(app / 'validate_profile.py'), '--root', str(REPO / 'tools/choms-skills')]}
        if tool not in commands:
            raise ValueError('unknown_runtime_tool')
        return commands[tool] + args

    def test(self, ident):
        checked = self.verify(ident); release = self.release(ident)
        write_json(self.root / 'receipts' / (ident + '.json'), {'status': 'RUNNING', 'manifest_sha256': digest(release / 'MANIFEST.json')})
        env = self.environment(release)
        work = Path(tempfile.mkdtemp(prefix='qa-', dir=self.root / 'work'))
        app = release / 'app/tools/choms-skills'
        def invoke(tool, args=()):
            result = subprocess.run(self.command(ident, tool, list(args)), cwd=work, env=env, capture_output=True, text=True, timeout=180)
            if result.returncode:
                raise ValueError('acceptance_failed:' + tool + ':' + result.stderr[:500] + result.stdout[:300])
            return result.stdout.strip()
        versions = {tool: invoke(tool, ['--version']).splitlines()[0] for tool in ('node', 'playwright-cli', 'playwright-mcp', 'agent-browser')}
        versions['chromium'] = subprocess.check_output([str(release / json.loads((release / 'LOCK.json').read_text())['browser_executable']), '--version'], env=env, text=True).strip()
        versions.update({tool: invoke(tool, ['-version']).splitlines()[0] for tool in ('ffmpeg', 'ffprobe')})
        frontend = json.loads(invoke('local-tools', ['brief', str(app / 'fixtures/design-brief.json')]))
        html = json.loads(invoke('local-tools', ['html', str(app / 'fixtures/browser.html')]))
        browser = json.loads(invoke('browser-qa', ['--output', str(work / 'screenshots')]))
        clis = json.loads(invoke('cli-smoke'))
        mcp = json.loads(invoke('mcp-probe', ['--browser', '--', *self.command(ident, 'playwright-mcp', ['--no-sandbox'])]))
        design_mcp = json.loads(invoke('mcp-probe', ['--', *self.command(ident, 'design-mcp', [])]))
        invoke('ffmpeg', ['-nostdin', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=360x640:r=25', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-n', str(work / 'input.mp4')])
        probe = str(release / 'ffprobe-linux-x64'); ffmpeg = str(release / 'ffmpeg-linux-x64')
        measured = json.loads(invoke('local-tools', ['measure', str(work / 'input.mp4'), '--genre', 'synthetic-blue', '--ffmpeg', ffmpeg, '--ffprobe', probe]))
        exported = json.loads(invoke('local-tools', ['export', str(work / 'input.mp4'), str(work / 'square.mp4'), '--width', '640', '--height', '640', '--ffmpeg', ffmpeg, '--ffprobe', probe]))
        if not frontend['valid'] or html['findings'] or browser['checks'] != 20 or exported['width'] != 640 or exported['height'] != 640:
            raise ValueError('acceptance_assertion_failed')
        report = {'status': 'PASS', 'release': ident, 'manifest_sha256': digest(release / 'MANIFEST.json'), 'versions': versions,
            'frontend': frontend, 'html': html, 'browser': browser, 'cli_smoke': clis, 'playwright_mcp': mcp,
            'design_mcp': design_mcp, 'video_measurement': measured, 'video_export': exported, 'fresh_processes': True,
            'temporary_root': 'managed runtime/work; no /tmp dependency', 'files_verified': checked['files_and_links']}
        write_json(self.root / 'receipts' / (ident + '.json'), report)
        return report

    def activate(self, ident):
        self.verify(ident)
        report = json.loads((self.root / 'receipts' / (ident + '.json')).read_text())
        if report['status'] != 'PASS' or report['manifest_sha256'] != digest(self.release(ident) / 'MANIFEST.json'):
            raise ValueError('acceptance_receipt_required')
        old = self.current() if (self.root / 'current').is_symlink() else None
        if old == ident:
            return {'status': 'PASS', 'current': ident, 'changed': False}
        if old:
            self.verify(old)
        launcher = self.root / 'bin/choms-runtime'
        controller = Path(__file__).resolve()
        if launcher.exists() or launcher.is_symlink():
            if not launcher.is_symlink() or launcher.resolve() != controller:
                raise ValueError('launcher_collision')
        else:
            launcher.symlink_to(controller)
        if old:
            atomic_link(self.root / 'previous', 'releases/' + old)
        atomic_link(self.root / 'current', 'releases/' + ident)
        write_json(self.root / 'activation.json', {'current': ident, 'previous': old})
        return {'status': 'PASS', 'current': ident, 'previous': old, 'changed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('prepare', 'bootstrap'):
        prepare = sub.add_parser(name); prepare.add_argument('--lock', type=Path, default=DEFAULT_LOCK); prepare.add_argument('--offline', action='store_true')
    for name in ('verify', 'test', 'activate'):
        entry = sub.add_parser(name); entry.add_argument('--release')
    sub.add_parser('rollback'); sub.add_parser('status')
    run = sub.add_parser('run'); run.add_argument('tool'); run.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if os.geteuid() == 0 or not args.root.resolve().is_relative_to((Path.home() / '.local/share').resolve()):
        parser.error('user-owned ~/.local/share root required; no sudo')
    runtime = Runtime(args.root)
    if args.action == 'run':
        with runtime.locked():
            ident=runtime.current(); runtime.verify(ident)
            command=runtime.command(ident,args.tool,args.args)
            env=runtime.environment(runtime.release(ident))
        # Immutable release paths keep running clients stable during promotion.
        # Do not hold the management lock while an on-demand MCP client serves.
        return subprocess.call(command,env=env)
    with runtime.locked():
        if args.action in ('prepare', 'bootstrap'):
            ident = runtime.prepare(args.lock, args.offline)
            if args.action == 'bootstrap':
                runtime.test(ident)
                result = runtime.activate(ident)
            else:
                result = {'status': 'PASS', 'release': ident, 'activated': False}
        elif args.action == 'status':
            result = {'current': runtime.current(), 'previous': runtime.current('previous') if (runtime.root / 'previous').is_symlink() else None}
        elif args.action == 'rollback':
            result = runtime.activate(runtime.current('previous'))
        else:
            ident = args.release or runtime.current()
            result = getattr(runtime, args.action)(ident)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status': 'FAIL', 'reason': str(exc)}), file=sys.stderr)
        sys.exit(1)
