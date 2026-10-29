"""Reversible native CHOMS links. Preflight all collisions; never overwrite a path."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'tools/choms-skills'


def entries():
    profile = json.loads((ROOT / 'PROFILE.json').read_text())
    by_name = {entry['name']: ROOT / entry['path'] for entry in profile['skills']}
    result = {name: by_name[name].parent for name in profile['activation']['selected']}
    result.update({entry['name']: (ROOT / entry['path']).parent for entry in profile['modular_profiles'].values()})
    return result


def activate(roots, receipt):
    targets = entries()
    plans = [(root / name, target.resolve()) for root in roots for name, target in targets.items()]
    for path, target in plans:
        if path.exists() or path.is_symlink():
            if not path.is_symlink() or path.resolve() != target:
                raise ValueError('native_skill_collision:' + path.name)
    if receipt.exists():
        raise ValueError('activation_receipt_exists; verify or rollback before reactivation')
    created = []
    try:
        for path, target in plans:
            if not path.is_symlink():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(target, target_is_directory=True)
                created.append({'path': str(path), 'target': str(target)})
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with receipt.open('x') as output:
            os.chmod(receipt, 0o600)
            json.dump({'schema': 1, 'created': created, 'names': sorted(targets)}, output, indent=2)
            output.write('\n')
    except Exception:
        for entry in reversed(created):
            path = Path(entry['path'])
            if path.is_symlink() and path.resolve() == Path(entry['target']):
                path.unlink()
        raise
    return {'status': 'PASS', 'skills_per_runtime': len(targets), 'created_links': len(created), 'overwritten': 0}


def rollback(receipt):
    value = json.loads(receipt.read_text())
    for entry in value['created']:
        path = Path(entry['path'])
        if not path.is_symlink() or path.resolve() != Path(entry['target']):
            raise ValueError('rollback_target_changed:' + path.name)
    for entry in reversed(value['created']):
        Path(entry['path']).unlink()
    receipt.rename(receipt.with_suffix('.rolled-back.json'))
    return {'status': 'PASS', 'removed_links': len(value['created'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-root', type=Path, default=Path.home() / '.agents/skills')
    parser.add_argument('--hermes-root', type=Path, default=Path.home() / '.hermes/skills')
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    print(json.dumps(rollback(args.receipt) if args.rollback else activate([args.codex_root, args.hermes_root], args.receipt), sort_keys=True))
