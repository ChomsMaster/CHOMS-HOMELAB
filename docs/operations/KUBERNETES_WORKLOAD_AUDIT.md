# Kubernetes Workload Audit

## Executive Summary

This audit records the desired and observed workload state of CHOMS Platforms
before further infrastructure hardening. It is a read-only snapshot taken on
2026-08-16 against the `default` Kubernetes context.

The cluster is healthy: all three K3s nodes are Ready, every controller has its
desired replicas, all persistent volume claims are Bound, the platform
certificate is Ready, and there are no failed or pending Pods.

The inventory contains 35 active workloads: 17 direct manifests, 15
Helm-managed workloads, and 3 K3s-managed system Deployments. There are no
active Jobs or CronJobs. No direct workload is missing from runtime and no
unattributed runtime workload was found.

No critical finding is open. The first remediation should be Redis because it
combines a single replica, persistent storage, the default `RollingUpdate`
strategy, no probes, no resource controls, root execution, and image drift.
Jellyfin and Scrutiny require separate security design because their current
privileged device access is high risk but functionally intentional.

## Scope and Cluster State

| Item | Observed state |
|---|---|
| Audit date | 2026-08-16 (Europe/Madrid) |
| Kubernetes | K3s `v1.36.2+k3s1` |
| Nodes | `choms-node-01`, `choms-node-02`, `choms-node-03`: Ready |
| Active namespaces | 17 |
| Deployments | 27 |
| StatefulSets | 3 |
| DaemonSets | 5 |
| Jobs / CronJobs | 0 / 0 |
| Non-running/non-succeeded Pods | 0 |
| Git | `main`, clean, `HEAD == origin/main` at audit start |
| E2E residue | 0 users, 0 shares, 0 files, 0 temporary Secrets |

Namespaces observed: `apps`, `cert-manager`, `databases`, `default`,
`diagnostics`, `filebrowser`, `kube-node-lease`, `kube-public`, `kube-system`,
`logging`, `media`, `metallb-system`, `monitoring`, `nfs-provisioner`,
`qbittorrent`, `security`, and `traefik`.

## Classification Rules

- **Critical**: active compromise, data-loss condition, or unavailable service.
- **High**: credible data-loss or host-compromise path requiring planned work.
- **Medium**: material hardening, reproducibility, or availability gap.
- **Low**: normalization, observability, or low-impact drift.
- **Correct**: desired and runtime state agree with the current standard.
- **Helm-managed / do not edit directly**: change chart version or versioned
  values, then use the locked Helm workflow.

## Complete Workload Inventory

Image references are abbreviated here only when a separate image table contains
the exact value. `R/L/S` means readiness/liveness/startup probe.

| Namespace | Kind | Workload | Owner | Replicas | Strategy | Images | R/L/S | PVC or host storage | Classification |
|---|---|---|---|---:|---|---|---|---|---|
| apps | Deployment | choms-controller | Direct Git | 1 | Recreate | controller digest | Y/Y/Y | none | Correct |
| apps | Deployment | home | Direct Git | 2 | RollingUpdate | `nginx:stable-alpine` | Y/Y/Y | none | Medium: mutable tag/root |
| apps | Deployment | nextcloud | Direct Git | 1 | Recreate | BusyBox + Nextcloud digests | Y/Y/Y | `nextcloud-storage` | Correct; main container root |
| apps | Deployment | portainer | Direct Git | 1 | Recreate | Portainer digest | Y/Y/Y | `portainer-data` | Low: registry-prefix drift |
| apps | Deployment | uptime-kuma | Direct Git | 1 | Recreate | Uptime Kuma digest | Y/Y/Y | `uptime-kuma-data` | Low: registry-prefix drift/root |
| cert-manager | Deployment | cert-manager | Helm `cert-manager` | 1 | RollingUpdate | controller tag | N/Y/N | none | Helm-managed / do not edit directly |
| cert-manager | Deployment | cert-manager-cainjector | Helm `cert-manager` | 1 | RollingUpdate | cainjector tag | N/N/N | none | Helm-managed / do not edit directly |
| cert-manager | Deployment | cert-manager-webhook | Helm `cert-manager` | 1 | RollingUpdate | webhook tag | Y/Y/N | none | Helm-managed / do not edit directly |
| databases | Deployment | mariadb | Direct Git | 1 | Recreate | MariaDB digest | Y/Y/Y | `mariadb-data` | Medium: no resources/root |
| databases | Deployment | postgres | Direct Git | 1 | Recreate | Git digest; runtime `postgres:17` | Y/Y/Y | `postgres-data` | Medium: image drift/root |
| databases | Deployment | redis | Direct Git | 1 | RollingUpdate | Git digest; runtime `redis:7` | N/N/N | `redis-data` | **High** |
| filebrowser | Deployment | filebrowser | Direct Git | 1 | Recreate | `filebrowser:s6` | Y/Y/N | none | Medium: tag/root/no CPU limit |
| kube-system | Deployment | coredns | K3s system | 1 | RollingUpdate | `1.14.4` tag | Y/Y/N | none | K3s-managed |
| kube-system | Deployment | local-path-provisioner | K3s system | 1 | RollingUpdate | `v0.0.36` tag | N/N/N | none | K3s-managed; one restart |
| kube-system | Deployment | metrics-server | K3s system | 1 | RollingUpdate | `v0.8.1` tag | Y/Y/N | none | K3s-managed |
| logging | Deployment | choms-loki-gateway | Helm `choms-loki` | 1 | RollingUpdate | nginx + exporter tags | Y(partial)/Y(partial)/N | none | Helm-managed / do not edit directly |
| logging | StatefulSet | choms-loki | Helm `choms-loki` | 1 | RollingUpdate | Loki + sidecar tags | Y/Y/N | `storage-choms-loki-0` | Helm-managed / do not edit directly |
| logging | DaemonSet | choms-alloy | Helm `choms-alloy` | 3 | RollingUpdate | Alloy tag + reloader digest | Y(partial)/N/N | none | Helm-managed / do not edit directly |
| logging | DaemonSet | choms-loki-canary | Helm `choms-loki` | 2 | RollingUpdate | canary tag | Y/Y/N | none | Helm-managed / do not edit directly |
| media | Deployment | jellyfin | Direct Git | 1 | Recreate | Jellyfin digest | Y/Y/N | hostPath config/cache/media/DRI | **High: privileged host access** |
| media | Deployment | threadfin | Direct Git | 1 | Recreate | Threadfin digest | Y/Y/N | `threadfin-config` | Medium: root/securityContext |
| metallb-system | Deployment | controller | Direct vendored manifest | 1 | RollingUpdate | Git digest; runtime `v0.15.2` | Y/Y/N | none | Medium: image drift/no resources |
| metallb-system | DaemonSet | speaker | Direct vendored manifest | 3 | RollingUpdate | Git digest; runtime `v0.15.2` | Y/Y/N | hostNetwork | Medium: required `NET_RAW`, drift |
| monitoring | Deployment | Grafana | Helm `choms-monitoring` | 1 | RollingUpdate | four tagged images | Y(partial)/Y(partial)/N | `choms-monitoring-grafana` | Helm-managed; root init container |
| monitoring | Deployment | kube-state-metrics | Helm `choms-monitoring` | 1 | RollingUpdate | tagged image | Y/Y/N | none | Helm-managed / do not edit directly |
| monitoring | Deployment | Prometheus operator | Helm `choms-monitoring` | 1 | RollingUpdate | tagged image | Y/Y/N | none | Helm-managed / do not edit directly |
| monitoring | StatefulSet | Alertmanager | Helm `choms-monitoring` | 1 | RollingUpdate | three tagged images | Y(partial)/Y(partial)/N | none | Helm-managed / do not edit directly |
| monitoring | StatefulSet | Prometheus | Helm `choms-monitoring` | 1 | RollingUpdate | three tagged images | Y(partial)/Y(partial)/Y(partial) | Prometheus PVC | Helm-managed / do not edit directly |
| monitoring | DaemonSet | node-exporter | Helm `choms-monitoring` | 3 | RollingUpdate | tagged image | Y/Y/N | host `/proc`, `/sys`, `/` | Helm-managed; hostNetwork/hostPID |
| monitoring | Deployment | scrutiny | Direct Git | 1 | Recreate | Scrutiny digest | Y/Y/N | hostPath config/DB/udev/dev | **High: privileged host access** |
| monitoring | DaemonSet | scrutiny-collector | Direct Git | 2 | RollingUpdate | collector tag | N/N/N | host `/run/udev`, `/dev` | **High: privileged, no controls** |
| nfs-provisioner | Deployment | NFS provisioner | Helm `choms-nfs` | 1 | Recreate | tagged image | N/N/N | NFS volume | Helm-managed / do not edit directly |
| qbittorrent | Deployment | qbittorrent | Direct Git | 1 | Recreate | qBittorrent digest | Y/Y/N | hostPath config | Medium: root/no CPU limit |
| security | Deployment | authelia | Direct Git | 1 | Recreate | `authelia:4.39.20` | Y/Y/Y | `authelia-data` | Medium: tag/root |
| traefik | Deployment | traefik-k8s | Helm `traefik-k8s` | 2 | RollingUpdate | `traefik:v3.7.9` | Y/Y/N | none | Helm-managed / do not edit directly |

## Declarative Drift

`kubectl diff` was executed per direct workload manifest. Exit code zero means
no drift. Generated metadata differences were not classified as functional.

| Severity | Resource | Git | Runtime | Assessment |
|---|---|---|---|---|
| Medium | `databases/Deployment/postgres` | `docker.io/library/postgres@sha256:a426e44bac0b759c95894d68e1a0ac03ecc20b619f498a91aae373bf06d8508d` | `postgres:17` | Same effective digest, declarative tag remains live |
| High | `databases/Deployment/redis` | `docker.io/library/redis@sha256:595cc6f2bb3af6e03347b90deb6123c6aa2c81dea05ce08128de8a174b6ac67b` | `redis:7` | Same effective digest, but rollout safety also deficient |
| Medium | `metallb-system/Deployment/controller` | controller digest | `quay.io/metallb/controller:v0.15.2` | Runtime not reconciled to vendored digest |
| Medium | `metallb-system/DaemonSet/speaker` | speaker digest | `quay.io/metallb/speaker:v0.15.2` | Runtime not reconciled to vendored digest |
| Low | `apps/Deployment/portainer` | `docker.io/portainer/...@sha256:f6bc…` | `portainer/...@sha256:f6bc…` | Registry-prefix normalization only; apply would roll Pod |
| Low | `apps/Deployment/uptime-kuma` | `docker.io/louislam/...@sha256:3d63…` | `louislam/...@sha256:3d63…` | Registry-prefix normalization only; apply would roll Pod |
| Low | `apps/ConfigMap/public-content` | Versioned embedded content | Runtime differs | Non-workload content drift in `home.yaml`; inspect separately |

No workload drift was found for choms-controller, Nextcloud, MariaDB,
Authelia, Filebrowser, Jellyfin, qBittorrent, Scrutiny, Threadfin, or the
Scrutiny collectors. Direct Git workloads all exist at runtime. No direct
runtime workload lacks an apparent manifest.

## Images Without a Digest

### Direct or system-managed

| Workload | Container | Runtime declaration | Effective imageID | Classification |
|---|---|---|---|---|
| home | nginx | `nginx:stable-alpine` | `docker.io/library/nginx@sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46` | Medium |
| authelia | authelia | `authelia/authelia:4.39.20` | `docker.io/authelia/authelia@sha256:1b363e9279e742397966333f364e0876ae02bf5c876de73e83af6d48c57ff51b` | Medium |
| filebrowser | filebrowser | `filebrowser/filebrowser:s6` | `docker.io/filebrowser/filebrowser@sha256:ee4ac79e52966a5f6247f99c7d667c1debfb277a3a61ab829f505aa8f4c74b21` | Medium |
| scrutiny-collector | collector | `ghcr.io/analogj/scrutiny:v0.8.2-collector` | `ghcr.io/analogj/scrutiny@sha256:3274a8c1e4b48bcc42089f9431f89604d4b3a661aeeaa2029c59c352d41762c2` | High with other controls |
| postgres | postgres | `postgres:17` | `docker.io/library/postgres@sha256:a426e44bac0b759c95894d68e1a0ac03ecc20b619f498a91aae373bf06d8508d` | Drift; Git already pinned |
| redis | redis | `redis:7` | `docker.io/library/redis@sha256:595cc6f2bb3af6e03347b90deb6123c6aa2c81dea05ce08128de8a174b6ac67b` | High; Git already pinned |
| MetalLB controller | controller | `quay.io/metallb/controller:v0.15.2` | `quay.io/metallb/controller@sha256:417cdb6d6f9f2c410cceb84047d3a4da3bfb78b5ddfa30f4cf35ea5c667e8c2e` | Drift; Git already pinned |
| MetalLB speaker | speaker | `quay.io/metallb/speaker:v0.15.2` | `quay.io/metallb/speaker@sha256:260c9406f957c0830d4e6cd2e9ac8c05e51ac959dd2462c4c2269ac43076665a` | Drift; Git already pinned |
| K3s system | three containers | version tags | Exact imageIDs recorded by script | K3s-managed |

There is no `latest` in any current workload template. Pod status still reports
historical tag names including `latest` for Portainer, Uptime Kuma, Jellyfin,
qBittorrent, and Scrutiny, but their current controller templates use digests
and their effective `imageID` matches Git. Pod status display names must not be
mistaken for current desired declarations.

All Helm workloads except the Alloy config-reloader use one or more version
tags rather than digests. They are listed in the script output with exact
effective imageIDs and must be changed through chart values, not by editing
rendered controllers.

### Exact effective image inventory

This table is container-oriented where a workload has multiple images. Repeated
DaemonSet/Deployment replicas resolved to the same imageID.

| Workload | Container | Runtime declaration | Effective imageID |
|---|---|---|---|
| choms-controller | controller | controller digest | `ghcr.io/chomsmaster/choms-controller@sha256:a981c26c03602e208d0256cdd95dc3f699dad46eb60d029e1f79e5aeb8b168cd` |
| home | nginx | `nginx:stable-alpine` | `docker.io/library/nginx@sha256:97d490c12ba55b4946b01546d1c3ed324e8d41ab1c9fcb2a616aa470620e5b46` |
| nextcloud | prepare-storage | BusyBox digest | `docker.io/library/busybox@sha256:9db7b59979c38555a39def84a31fb98b5296952f9e3afd4f6f11f05b07adfab0` |
| nextcloud | nextcloud | Nextcloud digest | `docker.io/library/nextcloud@sha256:07ec73cc816e58d6f45a162cd53ef886462c29271a23fc68d0124cec276e3767` |
| portainer | portainer | Portainer digest | `docker.io/portainer/portainer-ce@sha256:f6bc23d1695530a609563fd65c180aaafec0fc02e019d5fc63d16b6fbe83addd` |
| uptime-kuma | uptime-kuma | Uptime Kuma digest | `docker.io/louislam/uptime-kuma@sha256:3d632903e6af34139a37f18055c4f1bfd9b7205ae1138f1e5e8940ddc1d176f9` |
| cert-manager | controller | `v1.21.1` | `quay.io/jetstack/cert-manager-controller@sha256:416a2d76870d996460e62bd7f521bf14fa017be9e3e904aab92163a331fcb61a` |
| cert-manager-cainjector | cainjector | `v1.21.1` | `quay.io/jetstack/cert-manager-cainjector@sha256:ccf6b919ec0500745a47a910118f834f9636d0aac1ff221245cd2557ed8c7c98` |
| cert-manager-webhook | webhook | `v1.21.1` | `quay.io/jetstack/cert-manager-webhook@sha256:d8b3961b51c8c7320633f8208dc46bf88aa13804d0f7cbe48a096b2c523cee42` |
| mariadb | mariadb | MariaDB digest | `docker.io/library/mariadb@sha256:efb4959ef2c835cd735dbc388eb9ad6aab0c78dd64febcd51bc17481111890c4` |
| postgres | postgres | `postgres:17` | `docker.io/library/postgres@sha256:a426e44bac0b759c95894d68e1a0ac03ecc20b619f498a91aae373bf06d8508d` |
| redis | redis | `redis:7` | `docker.io/library/redis@sha256:595cc6f2bb3af6e03347b90deb6123c6aa2c81dea05ce08128de8a174b6ac67b` |
| filebrowser | filebrowser | `filebrowser/filebrowser:s6` | `docker.io/filebrowser/filebrowser@sha256:ee4ac79e52966a5f6247f99c7d667c1debfb277a3a61ab829f505aa8f4c74b21` |
| CoreDNS | coredns | `1.14.4` | `docker.io/rancher/mirrored-coredns-coredns@sha256:3e98f280fd601b37411c5fb7075fd9f337833c480f1644970b727ae0af067782` |
| local-path-provisioner | provisioner | `v0.0.36` | `docker.io/rancher/local-path-provisioner@sha256:1eba82e9c386038b4af6d69cca7519fac738c28c42735ed48ce70c882ad0d80f` |
| metrics-server | metrics-server | `v0.8.1` | `docker.io/rancher/mirrored-metrics-server@sha256:b2d2efaf5ac3b366ed0f839d2412a2c4279d4fc2a2a733f12c52133faed36c41` |
| choms-loki-gateway | nginx | `1.31-alpine` | `docker.io/nginxinc/nginx-unprivileged@sha256:59ccf0943b0b8e8d9e6ea9039a39555730f544701a655c596f7df7d096c593f5` |
| choms-loki-gateway | exporter | `0.4.9` | `ghcr.io/jkroepke/access-log-exporter@sha256:2a16e4ebc23d8410161edcc90b90e6ba3021f71f038dc121013e61dd3794f1ea` |
| choms-loki | loki | `3.7.4` | `docker.io/grafana/loki@sha256:87f0a067673756a3cede1bcbf0c74875f7df9b09fddb53e399d0c576f756cfcc` |
| choms-loki | sidecar | `2.10.0` | `docker.io/kiwigrid/k8s-sidecar@sha256:21b9fe7bb29d65caf2445ccbf96ff6eda5e589a92bd8f5188f957fe75b551d72` |
| choms-alloy | alloy | `v1.18.0` | `docker.io/grafana/alloy@sha256:491b0578c04983fd54fe99b587b6fab4404dc46d0dc16677bd6b00cc1140b308` |
| choms-alloy | config-reloader | reloader digest | `quay.io/prometheus-operator/prometheus-config-reloader@sha256:7d9e4eea5f1139e602508871f422b0116c60e87c662f3dcd234d5ab60cd0d8c1` |
| choms-loki-canary | canary | `3.7.4` | `docker.io/grafana/loki-canary@sha256:a43caf77ddd5df9621f2812e4621829e6e152dd8005b09896441b99e1f47da15` |
| jellyfin | jellyfin | Jellyfin digest | `docker.io/jellyfin/jellyfin@sha256:aefb67e6a7ff1debdd154a78a7bbb780fd0c873d8639210a7f6a2016ad2b35db` |
| threadfin | threadfin | Threadfin digest | `docker.io/fyb3roptik/threadfin@sha256:863fb0c2945617b4aa48b79eaa655954df72d68fbee6e49a1465934ceb3f057e` |
| MetalLB controller | controller | `v0.15.2` | `quay.io/metallb/controller@sha256:417cdb6d6f9f2c410cceb84047d3a4da3bfb78b5ddfa30f4cf35ea5c667e8c2e` |
| MetalLB speaker | speaker | `v0.15.2` | `quay.io/metallb/speaker@sha256:260c9406f957c0830d4e6cd2e9ac8c05e51ac959dd2462c4c2269ac43076665a` |
| Grafana | init-chown-data | `busybox:1.38.0` | `docker.io/library/busybox@sha256:dc2d74b28e4cf8984fa52af1f39bc7c3d9c73760b41a74d629f5d11b1ab28616` |
| Grafana | two sidecars | `2.10.0` | `quay.io/kiwigrid/k8s-sidecar@sha256:21b9fe7bb29d65caf2445ccbf96ff6eda5e589a92bd8f5188f957fe75b551d72` |
| Grafana | grafana | `13.1.1` | `docker.io/grafana/grafana@sha256:7cb8c64c4d57a57e734073f3cc94620adb24a0acb929bd80ba9f14017e3a975b` |
| kube-state-metrics | main | `v2.19.1` | `registry.k8s.io/kube-state-metrics/kube-state-metrics@sha256:85108987d044b18a098126732f98602df408888c0f7d456241f5abefb9744bc1` |
| Prometheus operator | operator | `v0.93.0` | `quay.io/prometheus-operator/prometheus-operator@sha256:a001ed10a3823bbf2410ea347796d0e35ff8decd24fb98acbe7ab9e98d431c39` |
| Alertmanager | alertmanager | `v0.33.1` | `quay.io/prometheus/alertmanager@sha256:9e082985f56f4c8c9f724e18f2288c6708f472e56a5286b8863d080434ea065d` |
| Alertmanager/Prometheus | reloaders | `v0.93.0` | `quay.io/prometheus-operator/prometheus-config-reloader@sha256:0ccb22ca9f3f6fd9f76ce95585d18bd2e363d421c534dde710be4bd13caa551d` |
| Prometheus | prometheus | `v3.13.2-distroless` | `quay.io/prometheus/prometheus@sha256:64f71bb84e03c855948418b0fc5dea53e9543d8e3fc9931598f583805507f05e` |
| node-exporter | node-exporter | `v1.12.1-distroless` | `quay.io/prometheus/node-exporter@sha256:8c9bac11973b94b59be88d6e11fee4429aa743c8846cdc75d65b18db33f6a106` |
| scrutiny | scrutiny | Scrutiny digest | `ghcr.io/analogj/scrutiny@sha256:18689773150d6b8b53c94a435f40f7b6e946fd4a6d40b44c64fa2154a5b38941` |
| scrutiny-collector | collector | `v0.8.2-collector` | `ghcr.io/analogj/scrutiny@sha256:3274a8c1e4b48bcc42089f9431f89604d4b3a661aeeaa2029c59c352d41762c2` |
| NFS provisioner | provisioner | `v4.0.2` | `registry.k8s.io/sig-storage/nfs-subdir-external-provisioner@sha256:63d5e04551ec8b5aae83b6f35938ca5ddc50a88d85492d9731810c31591fa4c9` |
| qbittorrent | qbittorrent | qBittorrent digest | `lscr.io/linuxserver/qbittorrent@sha256:b024436f8ca665d16d9a997d26fd27fdf867ee5566ba09f32764e7b2976d3e02` |
| authelia | authelia | `4.39.20` | `docker.io/authelia/authelia@sha256:1b363e9279e742397966333f364e0876ae02bf5c876de73e83af6d48c57ff51b` |
| traefik-k8s | traefik | `v3.7.9` | `docker.io/library/traefik@sha256:652929a140a32d7cafafb13c6cdfab5376cfeff800f51397b87b524501ed02a8` |

## Probe Coverage

| Group | Full R/L/S | Missing startup only | Material gaps |
|---|---|---|---|
| Direct | choms-controller, Nextcloud, Portainer, Uptime Kuma, MariaDB, PostgreSQL, Authelia, home | Filebrowser, Jellyfin, Threadfin, MetalLB controller/speaker, qBittorrent, Scrutiny | Redis and scrutiny-collector have none |
| Helm | none consistently across all containers | Several primary containers have R/L but no S | cert-manager cainjector, NFS provisioner; Alloy lacks liveness/startup; sidecars often lack probes |
| K3s | none with all three | CoreDNS and metrics-server lack startup | local-path-provisioner has none |

Startup probes are not mandatory for every fast-starting stateless component.
The priority is Redis and device collectors, followed by persistent or
slow-starting services.

## CPU and Memory Resources

| Classification | Workloads/containers |
|---|---|
| No requests or limits | MariaDB, Redis, MetalLB controller, MetalLB speaker, scrutiny-collector; multiple Helm sidecars/controllers; local-path-provisioner |
| Requests but incomplete limits | Filebrowser (no CPU limit), Jellyfin (no CPU limit), qBittorrent (no CPU limit), Scrutiny (no CPU limit), metrics-server (no limits), Alloy reloader (no limits) |
| Init container without controls | Nextcloud `prepare-storage`, Grafana `init-chown-data`, Prometheus/Alertmanager config reload init containers |
| Complete for main direct container | choms-controller, home, Nextcloud, Portainer, Uptime Kuma, PostgreSQL, Threadfin, Authelia |

Resource sizing must be based on observed metrics before enforcement. Database
limits need particular care to avoid OOM-induced recovery events.

## Security Review

| Severity | Workload | Observed setting | Effective UID where determined | Assessment |
|---|---|---|---:|---|
| High | Jellyfin | privileged; hostPath config/cache/media and `/dev/dri` | 0 | Excess privilege; redesign device access before changing |
| High | Scrutiny server | privileged; hostPath config, DB, `/run/udev`, `/dev` | 0 | Broad host/device access |
| High | scrutiny-collector | privileged; host `/run/udev` and `/dev`; no probes/resources | 0 | Highest hardening priority after Redis |
| Medium | MetalLB speaker | hostNetwork and `NET_RAW` | undetermined | Expected for L2 operation; retain only required capability |
| Helm | node-exporter | hostNetwork, hostPID, host `/proc`, `/sys`, `/` | non-root declared | Expected monitoring access; chart-managed |
| Helm | Grafana init | root with `CHOWN`, `DAC_OVERRIDE` | 0 | PVC ownership init; chart-managed |
| Medium | home, Nextcloud, Uptime Kuma, MariaDB, PostgreSQL, Redis, Filebrowser, Threadfin, qBittorrent, Authelia | no non-root enforcement | 0 observed | Add per-image security design, not a blanket UID |
| Correct | choms-controller | non-root 10001, drop ALL, read-only rootfs, no escalation | 10001 | Strong baseline |
| Correct | Traefik and most monitoring control-plane containers | non-root, seccomp, reduced capabilities | declared non-root | Helm-managed baseline |

No direct workload uses hostPID. Only MetalLB speaker uses hostNetwork among
direct manifests. No sensitive Secret values were read; only `secretKeyRef`
metadata present in workload specs was within scope.

## Helm Releases

| Namespace | Release | Chart | App version | Status |
|---|---|---|---|---|
| cert-manager | cert-manager | `cert-manager-v1.21.1` | `v1.21.1` | deployed |
| logging | choms-alloy | `alloy-1.11.0` | `v1.18.0` | deployed |
| logging | choms-loki | `loki-18.7.1` | `3.7.4` | deployed |
| monitoring | choms-monitoring | `kube-prometheus-stack-88.0.1` | `v0.93.0` | deployed |
| nfs-provisioner | choms-nfs | `nfs-subdir-external-provisioner-4.0.18` | `4.0.2` | deployed |
| traefik | traefik-k8s | `traefik-41.1.0` | `v3.7.9` | deployed |

Changes to these workloads must be made in the corresponding versioned values
under `stacks/kubernetes/` and applied using the locked Helm workflow. Rendered
Deployments, StatefulSets, and DaemonSets must not be edited directly.

## Orphan and Attribution Review

| Category | Result |
|---|---|
| Runtime direct workload without apparent Git manifest | None |
| Git workload manifest without runtime resource | None |
| Helm workload without known release | None |
| K3s system workload | CoreDNS, local-path-provisioner, metrics-server |
| Empty namespace | `diagnostics` has no audited workload; retained from prior diagnostics |
| Manual field-manager evidence | Not available because managedFields are omitted; attribution instead uses Helm metadata, K3s namespace, exact names, and `kubectl diff` |

The absence of managedFields prevents proving that no historical manual edit
ever occurred. Current functional drift is captured by `kubectl diff`.

## Prioritized Risks

1. **High — Redis rollout/data safety.** One replica and a PVC use
   `RollingUpdate`; no probes or resource controls exist, and runtime still
   declares a tag. A rollout can briefly create concurrent writers to shared
   storage.
2. **High — privileged device workloads.** Jellyfin, Scrutiny, and its
   collectors run privileged with broad host paths. Compromise can reach host
   devices; remediation requires testing hardware access.
3. **Medium — remaining direct mutable images.** Home, Authelia, Filebrowser,
   and scrutiny-collector are not reproducible by digest.
4. **Medium — unreconciled published digests.** PostgreSQL, Redis, and MetalLB
   execute the expected bytes but declare tags at runtime.
5. **Medium — missing probes/resources.** Redis and collectors are the largest
   gaps; MariaDB lacks resource controls despite correct probes and strategy.
6. **Low — canonical registry drift.** Portainer and Uptime Kuma differ only by
   an explicit `docker.io/` prefix.
7. **Low — home content drift.** `public-content` differs from Git and requires
   a separate content review before reconciliation.

## Remediation Plan and Recommended Order

| Phase/order | Workload | Change class | Expected downtime/risk |
|---:|---|---|---|
| 1 | Redis | Backup/validation; change to Recreate; add startup/readiness/liveness; size resources; reconcile existing digest | Brief cache outage; low persistent-data risk only after backup and consumer checks |
| 2 | PostgreSQL | Reconcile already-published digest; verify database and consumers | Brief outage because Recreate; no image-byte change expected |
| 3 | MetalLB controller/speaker | Reconcile vendored digests one component at a time | Edge/L2 interruption possible; maintain speaker quorum and validate VIP |
| 4 | scrutiny-collector | Pin digest; add resources/probes where supported; minimize privileges and device paths | SMART telemetry gap; possible device discovery failure |
| 5 | Scrutiny server | Reduce privilege/host paths after backup; add CPU limit/startup probe | Monitoring outage; database/config risk if paths change |
| 6 | Jellyfin | Test non-privileged `/dev/dri` access and narrower device mapping | Media interruption; hardware transcoding may fail |
| 7 | Home, Authelia, Filebrowser | Pin currently running digests one service per commit | Brief Recreate outages for stateful apps; home remains available with two replicas |
| 8 | MariaDB and remaining direct apps | Metrics-based resources and securityContext hardening | OOM or permission risk if limits/UIDs are guessed |
| 9 | Helm releases | Evaluate digest overrides, probes, and resources in versioned values per release | Chart rollout risk; use atomic locked Helm flow |
| 10 | K3s system workloads | Address only through a planned K3s configuration/version lifecycle | Cluster DNS/metrics/storage impact; never patch ad hoc |

No remediation is authorized by this audit.

## Acceptance Criteria

- Git is clean and synchronized before every service-specific change.
- A current backup exists for persistent workloads.
- Runtime `image` equals the reviewed Git or Helm desired reference.
- Effective `imageID` equals the pinned digest.
- Single-replica databases with persistent storage do not use concurrent-writer
  rollout strategies.
- Required probes pass through startup and steady state.
- Requests and limits are based on measured consumption.
- Privilege, host namespaces, capabilities, and host paths are minimal and
  explicitly justified.
- `kubectl diff` is empty after each direct-manifest change.
- Helm changes reconcile through versioned values and the locked atomic flow.
- Workload, storage, routes, certificates, and consumers remain healthy.
- Secrets, dumps, credentials, and user data never enter logs or Git.

## Reproducible Read-only Commands

The versioned collector provides stable, non-sensitive output:

```bash
./stacks/kubernetes/audit/choms-kubernetes-workload-audit.sh \
  --context default
```

An explicit kubeconfig is also supported:

```bash
./stacks/kubernetes/audit/choms-kubernetes-workload-audit.sh \
  --kubeconfig /path/to/read-only-kubeconfig \
  --context default
```

Core commands used by the audit:

```bash
kubectl get nodes
kubectl get namespaces
kubectl get deployment,statefulset,daemonset,job,cronjob -A -o json
kubectl get pods -A -o json
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded
kubectl get pvc -A
kubectl get certificate -A
helm list -A -o json
kubectl diff -f <direct-workload-manifest>
```

The collector does not request Secret objects. During E2E cleanup validation,
only aggregate counts and Secret names matching the temporary prefix were
examined; no Secret values were read.
