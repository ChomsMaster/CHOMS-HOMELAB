#!/usr/bin/env bash
# Optional public downloads to ignored local cache; no cluster or cloud access.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cache="$repo_root/.cache/devops"
mkdir -p "$cache/bin" "$cache/downloads" "$cache/charts"
export HELM_CONFIG_HOME="$cache/helm/config"
export HELM_CACHE_HOME="$cache/helm/cache"
export HELM_DATA_HOME="$cache/helm/data"
export KUBECONFIG=/dev/null
fetch_tar() {
  local name="$1" version="$2" url="$3" binary="$4"
  if [[ ! -s $cache/downloads/$name-$version.tar.gz ]]; then
    curl -fsSL --retry 2 "$url" -o "$cache/downloads/$name-$version.tar.gz"
  fi
  tar -xf "$cache/downloads/$name-$version.tar.gz" -C "$cache/downloads" "$binary"
  install -m 0755 "$cache/downloads/$binary" "$cache/bin/$name"
}
fetch_tar helm 3.17.3 https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz linux-amd64/helm
fetch_tar kubeconform 0.7.0 https://github.com/yannh/kubeconform/releases/download/v0.7.0/kubeconform-linux-amd64.tar.gz kubeconform
fetch_tar shellcheck 0.10.0 https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck-v0.10.0.linux.x86_64.tar.xz shellcheck-v0.10.0/shellcheck
fetch_tar gitleaks 8.24.2 https://github.com/gitleaks/gitleaks/releases/download/v8.24.2/gitleaks_8.24.2_linux_x64.tar.gz gitleaks
fetch_tar trivy 0.69.3 https://github.com/aquasecurity/trivy/releases/download/v0.69.3/trivy_0.69.3_Linux-64bit.tar.gz trivy
python3 -m venv "$cache/venv"
"$cache/venv/bin/pip" --disable-pip-version-check install 'yamllint==1.37.1' 'PyYAML==6.0.2'
export PATH="$cache/bin:$cache/venv/bin:$PATH"
python3 - "$repo_root" "$cache/charts" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
root, charts = map(Path, sys.argv[1:])
for release in json.loads((root / 'stacks/kubernetes/helm/releases.json').read_text()).values():
    subprocess.run(['helm', 'pull', release['chart'], '--repo', release['repository'],
                    '--version', release['version'], '--destination', str(charts)], check=True)
PY
echo "Tools cached. Run: PATH=\"$cache/bin:$cache/venv/bin:\$PATH\" ./scripts/validate.sh"
