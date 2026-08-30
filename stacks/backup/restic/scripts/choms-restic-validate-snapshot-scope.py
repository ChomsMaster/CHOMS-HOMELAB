#!/usr/bin/env python3
import json
import re
import sys


EXPECTED = {
    ("choms-node-01", "node-01", "type-k3s"): "k3s",
    ("choms-node-01", "node-01", "type-secrets"): "stdin-secrets",
    ("choms-node-01", "node-01", "type-platform"): "platform",
    ("choms-node-01", "node-01", "type-nextcloud"): "nextcloud",
    ("choms-node-02", "node-02", "type-jellyfin"): "jellyfin",
    ("choms-node-03", "node-03", "type-qbittorrent"): "qbittorrent",
}

PLATFORM_ROOTS = (
    "/data/backups/kubernetes/20260830-031918",
    "/mnt/choms-storage/kubernetes/apps-portainer-data-pvc-50b7d8c5-8cc1-46d5-9e0f-35407a4e3dfc",
    "/mnt/choms-storage/kubernetes/apps-uptime-kuma-data-pvc-db048d0d-5ab9-4cb8-b28b-eccb8b980dc1",
    "/mnt/choms-storage/kubernetes/security-authelia-data-pvc-7e6356ce-8166-4ac7-a829-9a0f2283e9ed",
    "/mnt/choms-storage/kubernetes/media-threadfin-config-pvc-292bb31c-e3c5-42d2-87d5-a771825fedd3",
    "/mnt/choms-storage/kubernetes/monitoring-choms-monitoring-grafana-pvc-233ae869-8985-4ec5-8efd-49c90251df66",
    "/mnt/choms-storage/docker/filebrowser/config",
    "/mnt/choms-storage/docker/filebrowser/database",
    "/mnt/choms-backups/scrutiny/logical/daily/latest",
)
NEXTCLOUD_ROOT = "/mnt/choms-storage/kubernetes/apps-nextcloud-storage-pvc-2fbee8b2-917a-43ea-89e4-cf8d703ae466"
NEXTCLOUD_SUBTREES = tuple(
    f"{NEXTCLOUD_ROOT}/{name}" for name in ("config", "custom_apps", "themes")
)
JELLYFIN_ROOT = "/data/docker/jellyfin-node02/config"
QBITTORRENT_ROOT = "/data/docker/qbittorrent/config"
K3S_ROOTS = (
    "/var/lib/rancher/k3s/server/tls",
    "/var/lib/rancher/k3s/server/token",
    "/etc/rancher/k3s",
    "/etc/choms-backup/recovery-sample.txt",
)


def within(path, root):
    return path == root or path.startswith(root + "/")


def structural_ancestor(path, roots, node_type):
    if node_type != "dir":
        return False
    prefix = "/" if path == "/" else path.rstrip("/") + "/"
    return any(root.startswith(prefix) for root in roots)


def generic_excluded_category(path):
    folded = path.casefold()
    parts = tuple(part for part in folded.split("/") if part)
    if "colegio" in parts:
        return "colegio"
    if any(part in {"personal", "personales", "historical", "historico", "historicos", "history"} for part in parts):
        return "personal_backups"
    if folded == "/srv/storage" or folded.startswith("/srv/storage/"):
        return "personal_backups"
    if folded == "/mnt/choms-storage/backups" or folded.startswith("/mnt/choms-storage/backups/"):
        return "personal_backups"
    if any("prometheus" in part for part in parts):
        return "prometheus_tsdb"
    if any("loki" in part for part in parts):
        return "loki"
    if any(part in {"media", "multimedia", "movies", "music", "videos", "tv"} for part in parts):
        return "multimedia"
    return "unauthorized_scope"


def validate_path(kind, path, node_type, logical_name):
    if kind == "stdin-secrets":
        accepted = {logical_name, f"/{logical_name}"}
        if path in accepted or (path == "/" and node_type == "dir"):
            return None
        return "stdin_logical_name"

    if kind == "k3s":
        dynamic_state = bool(re.match(r"^/run/choms-restic\.[^/]+/state\.db$", path))
        dynamic_ancestor = node_type == "dir" and (
            path == "/run" or bool(re.match(r"^/run/choms-restic\.[^/]+$", path))
        )
        allowed = (
            dynamic_state
            or dynamic_ancestor
            or any(within(path, root) for root in K3S_ROOTS)
            or structural_ancestor(path, K3S_ROOTS, node_type)
        )
        return None if allowed else generic_excluded_category(path)

    if kind == "platform":
        allowed = any(within(path, root) for root in PLATFORM_ROOTS) or structural_ancestor(
            path, PLATFORM_ROOTS, node_type
        )
        return None if allowed else generic_excluded_category(path)

    if kind == "nextcloud":
        if path == NEXTCLOUD_ROOT or structural_ancestor(path, (NEXTCLOUD_ROOT,), node_type):
            return None
        relative = path.removeprefix(NEXTCLOUD_ROOT + "/") if path.startswith(NEXTCLOUD_ROOT + "/") else None
        if relative is not None and relative.split("/", 1)[0].casefold() == "data":
            return "nextcloud_data"
        if any(within(path, root) for root in NEXTCLOUD_SUBTREES):
            return None
        if relative is not None and "/" not in relative and node_type != "dir":
            return None
        return generic_excluded_category(path)

    if kind == "jellyfin":
        parts = tuple(part.casefold() for part in path.split("/") if part)
        if any(part in {"cache", "transcodes"} for part in parts):
            return "multimedia"
        allowed = within(path, JELLYFIN_ROOT) or structural_ancestor(path, (JELLYFIN_ROOT,), node_type)
        return None if allowed else "multimedia"

    if kind == "qbittorrent":
        parts = tuple(part.casefold() for part in path.split("/") if part)
        if "downloads" in parts:
            return "downloads"
        allowed = within(path, QBITTORRENT_ROOT) or structural_ancestor(path, (QBITTORRENT_ROOT,), node_type)
        return None if allowed else generic_excluded_category(path)

    return "technical"


def main():
    if len(sys.argv) != 5:
        print("scope_validation=error category=technical", file=sys.stderr)
        return 30
    hostname, host_tag, type_tag, logical_name = sys.argv[1:]
    kind = EXPECTED.get((hostname, host_tag, type_tag))
    if kind is None:
        print("scope_validation=error category=technical", file=sys.stderr)
        return 30
    if kind == "stdin-secrets" and logical_name != "recovery-secrets.json":
        print("scope_validation=failed category=stdin_logical_name", file=sys.stderr)
        return 20
    if kind != "stdin-secrets" and logical_name != "-":
        print("scope_validation=error category=technical", file=sys.stderr)
        return 30

    seen = 0
    try:
        for line in sys.stdin:
            item = json.loads(line)
            if item.get("struct_type") != "node":
                continue
            path = item.get("path")
            node_type = item.get("type")
            if not isinstance(path, str) or not isinstance(node_type, str):
                raise ValueError("malformed node")
            seen += 1
            category = validate_path(kind, path, node_type, logical_name)
            if category is not None:
                if category == "technical":
                    print("scope_validation=error category=technical", file=sys.stderr)
                    return 30
                print(f"scope_validation=failed category={category}", file=sys.stderr)
                return 20
    except (json.JSONDecodeError, TypeError, ValueError):
        print("scope_validation=error category=technical", file=sys.stderr)
        return 30
    if seen == 0:
        print("scope_validation=error category=technical", file=sys.stderr)
        return 30
    print(f"scope_validation=passed hostname={hostname} tags={host_tag},{type_tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
