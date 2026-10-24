"""Single local/CI validation entry point; stage source, never runtime files."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
FAILED = []
SKIPPED = []
DETAILS = []
ADVISORY = []


def run(name, args, cwd=None, env=None, blocking=True):
    # Redact scanners and bound all other output. Deployment scripts are parsed only.
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    status = ('PASS' if result.returncode == 0 else 'FAIL') if blocking else 'INFO'
    print(f"{status} {name} (exit={result.returncode})", flush=True)
    if name.startswith('kubeconform'):
        print('\n'.join(result.stdout.splitlines()[-3:]))
    if name in ('shellcheck', 'trivy config'):
        try:
            data = json.loads(result.stdout)
            if name == 'shellcheck':
                for item in data:
                    DETAILS.append({'tool': name, 'file': item['file'].split('/source/')[-1],
                                    'line': item['line'], 'id': 'SC' + str(item['code']),
                                    'message': item['message']})
            else:
                for group in data.get('Results', []):
                    for item in group.get('Misconfigurations', []):
                        DETAILS.append({'tool': name, 'file': group['Target'].split('/source/')[-1],
                                        'line': item.get('CauseMetadata', {}).get('StartLine'),
                                        'id': item['ID'], 'severity': item['Severity'], 'message': item['Title']})
        except (ValueError, KeyError):
            DETAILS.append({'tool': name, 'message': 'No machine-readable diagnostics; raw output withheld.'})
    if result.returncode:
        (FAILED if blocking else ADVISORY).append(name)
        if name not in ('gitleaks', 'trivy config', 'shellcheck'):
            print('\n'.join((result.stdout + result.stderr).splitlines()[-18:]))
        else:
            print('Findings withheld: review locally using redacted scanner output.')
    return result.returncode == 0


def available(tool):
    if shutil.which(tool):
        return True
    (ADVISORY if tool == 'trivy' else SKIPPED).append(tool)
    print(f'SKIP {tool}: herramienta no instalada', flush=True)
    return False


def safe_source(name):
    path = Path(name)
    if any(p in ('.git', '.terraform', '.cache', 'private', 'node_modules') for p in path.parts):
        return False
    lower = path.name.lower()
    recovery_inputs = {
        'kubernetes-secrets.json', 'k3s-token', 'k3s-snapshot', 'k3s-snapshot-meta.json',
        'k3s-encryption-config.json', 'authelia-configuration.yml', 'authelia-users.yml',
        'restic-password', 'ansible-vars.yml', 'network-dns.md'
    }
    if (lower in recovery_inputs or lower.endswith(('.enc.json', '.agekey'))
            or lower.startswith('age-identity')
            or any(p in ('recovery-input', 'recovery-plaintext', 'recovery-kits',
                         'choms-recovery-private') for p in path.parts)):
        return False
    if ('tfstate' in lower or 'kubeconfig' in lower or lower.endswith(('.pem', '.key', '.tfplan'))
            or lower.startswith('.env') or lower.endswith(('.env', '.tfvars', '.auto.tfvars.json'))):
        return False
    if 'secrets' in path.parts and path.suffix not in ('.sh', '.md', '.example'):
        return False
    return path.suffix in ('.sh', '.py', '.yaml', '.yml', '.json', '.tf', '.md', '.toml') or path.name in ('.yamllint', '.gitleaks.toml')


def main():
    if sys.argv[1:] == ['--local-changes']:
        return validate_local_changes()
    if sys.argv[1:]:
        print('Usage: scripts/validate.sh [--local-changes]')
        return 2
    os.environ['KUBECONFIG'] = '/dev/null'
    names = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT
    ).decode().split('\0')
    with tempfile.TemporaryDirectory(prefix='choms-validate-') as temp:
        stage = Path(temp) / 'source'
        stage.mkdir()
        for name in sorted(set(filter(None, names))):
            source = ROOT / name
            if safe_source(name) and source.is_file() and not source.is_symlink():
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        manifests = []
        yamls = sorted(stage.rglob('*.yaml')) + sorted(stage.rglob('*.yml'))
        # Read only staged declarative YAML. Values/ConfigMaps are never executed.
        import yaml
        for file in (stage / 'stacks/kubernetes').rglob('*.yaml'):
            try:
                docs = list(yaml.safe_load_all(file.read_text()))
            except yaml.YAMLError:
                FAILED.append('YAML parsing: ' + str(file.relative_to(stage)))
                continue
            objects = [d for d in docs if isinstance(d, dict) and 'apiVersion' in d and 'kind' in d]
            if any(d.get('kind') == 'Secret' and ('data' in d or 'stringData' in d) for d in objects):
                FAILED.append('Secret values present in source: ' + str(file.relative_to(stage)))
                continue
            if objects:
                manifests.append(str(file))
        if available('yamllint'):
            run('yamllint', ['yamllint', '-c', str(stage / '.yamllint'), *map(str, yamls)])
        if available('helm'):
            charts = Path(os.environ.get('CHOMS_CHART_CACHE', ROOT / '.cache/devops/charts'))
            for name, release in json.loads((stage / 'stacks/kubernetes/helm/releases.json').read_text()).items():
                chart = charts / f"{release['chart']}-{release['version']}.tgz"
                if not chart.exists():
                    chart = charts / f"{release['chart']}-{release['version'].removeprefix('v')}.tgz"
                if not chart.exists():
                    SKIPPED.append('helm lint ' + name)
                    print(f'SKIP helm lint {name}: chart fijado ausente en {chart}', flush=True)
                    continue
                args = ['helm', 'lint', str(chart), '--namespace', release['namespace']]
                for values in release['values']:
                    args += ['--values', str(stage / values)]
                run('helm lint ' + name, args)
            for chart in stage.rglob('Chart.yaml'):
                run('helm lint ' + str(chart.parent.relative_to(stage)), ['helm', 'lint', str(chart.parent)])
        if available('kubeconform'):
            run('kubeconform', ['kubeconform', '-strict', '-summary', '-ignore-missing-schemas',
                               '-kubernetes-version', '1.36.0', *manifests])
            netpols = sorted((stage / 'stacks/kubernetes/networkpolicies').rglob('*.yaml'))
            run('kubeconform NetworkPolicies (no schema skips)',
                ['kubeconform', '-strict', '-summary', '-kubernetes-version', '1.36.0', *map(str, netpols)])
        scripts = sorted((stage / 'scripts').glob('*.sh'))
        for script in scripts:
            run('bash -n ' + script.name, ['bash', '-n', str(script)])
        if available('shellcheck'):
            run('shellcheck', ['shellcheck', '--format=json', '--external-sources', '--source-path=SCRIPTDIR', *map(str, scripts)])
        if available('terraform'):
            # Provider downloads only, isolated scratch roots, no backend/state/auth files.
            keys = ('PATH', 'TMPDIR', 'SSL_CERT_FILE', 'SSL_CERT_DIR', 'TF_PLUGIN_CACHE_DIR')
            env = {k: os.environ[k] for k in keys if k in os.environ}
            env.update(HOME=temp, TF_IN_AUTOMATION='1', TF_INPUT='0', CHECKPOINT_DISABLE='1')
            run('terraform fmt', ['terraform', 'fmt', '-check', '-recursive', 'terraform'], cwd=stage, env=env)
            for root in ['terraform/environments/homelab']:
                directory = stage / root
                if run('terraform init -backend=false ' + root,
                       ['terraform', 'init', '-backend=false', '-input=false', '-no-color'], cwd=directory, env=env):
                    run('terraform validate ' + root, ['terraform', 'validate', '-no-color'], cwd=directory, env=env)
        if available('gitleaks'):
            run('gitleaks', ['gitleaks', 'dir', str(stage), '--redact=100', '--no-banner'])
        if available('trivy'):
            run('trivy config', ['trivy', 'config', '--exit-code', '1', '--severity', 'HIGH,CRITICAL',
                                 '--format', 'json', '--quiet', str(stage)], blocking=False)
    detail_file = ROOT / '.cache/devops/validation-findings.json'
    detail_file.parent.mkdir(parents=True, exist_ok=True)
    detail_file.write_text(json.dumps(DETAILS, indent=2) + '\n')
    print(f'RESULT failures={len(FAILED)} omissions={len(SKIPPED)}')
    if ADVISORY:
        print('INFORMATIVO: ' + ', '.join(ADVISORY))
    if SKIPPED:
        print('OMITIDO: ' + ', '.join(SKIPPED))
    # Local missing tools are visible; CI cannot go green with an incomplete suite.
    return 1 if FAILED or (SKIPPED and os.environ.get('CI') == 'true') else 0


def validate_local_changes():
    """Offline checks for changed public source; no downloads or live tooling."""
    import re
    import yaml

    names = subprocess.check_output(
        ['git', 'diff', 'HEAD', '--name-only', '-z'], cwd=ROOT
    ).decode().split('\0')
    names += subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().split('\0')
    selected = [ROOT / name for name in sorted(set(filter(None, names)))
                if safe_source(name) and (ROOT / name).is_file()]
    for file in selected:
        if file.suffix in ('.yaml', '.yml'):
            try:
                list(yaml.safe_load_all(file.read_text()))
            except yaml.YAMLError:
                FAILED.append('YAML parsing: ' + str(file.relative_to(ROOT)))
        elif file.suffix == '.py':
            try:
                compile(file.read_bytes(), str(file), 'exec')
            except SyntaxError:
                FAILED.append('Python syntax: ' + str(file.relative_to(ROOT)))

    scripts = [str(file) for file in selected if file.suffix == '.sh']
    for script in scripts:
        run('bash -n ' + str(Path(script).relative_to(ROOT)), ['bash', '-n', script])
    if scripts and available('shellcheck'):
        result = subprocess.run(['shellcheck', '--norc', '--format=json', *scripts],
                                capture_output=True, text=True)
        # This mode validates the diff; inherited findings remain visible without
        # broadening a scoped separation into an unrelated hardening task.
        changed_lines = {}
        for script in scripts:
            relative = str(Path(script).relative_to(ROOT))
            patch = subprocess.check_output(
                ['git', 'diff', 'HEAD', '--unified=0', '--', relative], cwd=ROOT, text=True)
            lines = set()
            for start, length in re.findall(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', patch):
                lines.update(range(int(start), int(start) + int(length or '1')))
            changed_lines[script] = lines if patch else None
        try:
            findings = json.loads(result.stdout)
            relevant = []
            for item in findings:
                lines = changed_lines.get(item['file'])
                if lines is None or any(line in lines for line in range(item['line'], item.get('endLine', item['line']) + 1)):
                    relevant.append(item)
                DETAILS.append({'tool': 'shellcheck', 'file': item['file'],
                                'line': item['line'], 'id': 'SC' + str(item['code']),
                                'message': item['message']})
            if relevant:
                FAILED.append('shellcheck affected lines')
            if len(findings) > len(relevant):
                ADVISORY.append('Inherited ShellCheck findings outside changed lines: ' + str(len(findings) - len(relevant)))
            if result.returncode not in (0, 1):
                FAILED.append('shellcheck execution')
        except (ValueError, KeyError):
            FAILED.append('shellcheck diagnostics')

    # Check public policy contracts locally, without downloading CRD/API schemas.
    policy_root = ROOT / 'stacks/kubernetes/networkpolicies'
    namespaces = {folder.name for folder in policy_root.iterdir() if folder.is_dir()
                  and (folder / 'policies.yaml').is_file()}
    count = 0
    affected_namespaces = {file.parent.name for file in selected
                           if file.parent.parent == policy_root}
    for ns in sorted(affected_namespaces):
        try:
            policies = list(yaml.safe_load_all((policy_root / ns / 'policies.yaml').read_text()))
            identities = set()
            deny = False
            for obj in policies:
                assert obj['apiVersion'] == 'networking.k8s.io/v1' and obj['kind'] == 'NetworkPolicy'
                assert obj['metadata']['namespace'] == ns
                name = obj['metadata']['name']
                assert name not in identities
                identities.add(name)
                spec = obj['spec']
                assert isinstance(spec['podSelector'], dict)
                assert set(spec['policyTypes']) <= {'Ingress', 'Egress'}
                if name == 'choms-default-deny':
                    deny = spec['podSelector'] == {} and set(spec['policyTypes']) == {'Ingress', 'Egress'}
                    assert not spec.get('ingress') and not spec.get('egress')
                for direction, peers in [('ingress', 'from'), ('egress', 'to')]:
                    for rule in spec.get(direction, []):
                        for port in rule.get('ports', []):
                            value = port['port']
                            assert port.get('protocol', 'TCP') in ('TCP', 'UDP', 'SCTP')
                            assert (isinstance(value, int) and 1 <= value <= 65535) or isinstance(value, str)
                        for peer in rule.get(peers, []):
                            target = peer.get('namespaceSelector', {}).get('matchLabels', {}).get('kubernetes.io/metadata.name')
                            assert target is None or target in namespaces or target == 'kube-system'
                count += 1
            assert deny
        except (AssertionError, KeyError, TypeError, yaml.YAMLError):
            FAILED.append('NetworkPolicy contract: ' + ns)
    tf = (ROOT / 'terraform/environments/homelab/locals.tf').read_text()
    declared = set(re.findall(r'"([a-z0-9-]+)"', tf.split('releases =')[0]))
    if declared != namespaces:
        FAILED.append('Public namespace ownership mismatch')
    rollout = (ROOT / 'scripts/netpol-rollout.sh').read_text()
    for ns in namespaces:
        if ns not in rollout:
            FAILED.append('Public rollout namespace missing')
    print(f'LOCAL YAML/Python and affected policy contracts: {count} policies, '
          f'{len(affected_namespaces)} affected / {len(namespaces)} public namespaces')
    # Scan only source in the selected change set; redact all scanner output.
    with tempfile.TemporaryDirectory(prefix='choms-local-check-') as temp:
        snapshot = Path(temp)
        for file in selected:
            target = snapshot / file.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
        if available('gitleaks'):
            run('gitleaks', ['gitleaks', 'dir', str(snapshot), '--redact=100', '--no-banner'])
    detail_file = ROOT / '.cache/devops/local-change-findings.json'
    detail_file.parent.mkdir(parents=True, exist_ok=True)
    detail_file.write_text(json.dumps(DETAILS, indent=2) + '\n')
    print(f'LOCAL RESULT failures={len(FAILED)} omissions={len(SKIPPED)}')
    if FAILED:
        print('LOCAL FAILURES: ' + ', '.join(FAILED))
    if ADVISORY:
        print('LOCAL INFORMATIVO: ' + ', '.join(ADVISORY))
    return 1 if FAILED or SKIPPED else 0


if __name__ == '__main__':
    raise SystemExit(main())
