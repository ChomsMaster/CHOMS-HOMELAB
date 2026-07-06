# CHOMS Changelog

## 2026-07-06

### Added

- Application Node bootstrap
- PostgreSQL stack
- Redis stack
- CHOMS deploy command
- Project documentation structure
- AI handoff document

### Changed

- Git repository is now the source of truth.
- Runtime directory is treated as generated deployment output.

### Fixed

- qBittorrent was incorrectly using NAS system SSD paths.
- qBittorrent now mounts:
  - /downloads → /srv/storage/downloads/torrents
  - /config → /srv/storage/docker/qbittorrent/config
  - /logs → /srv/storage/logs
  - /movies → /srv/media/Movies
  - /series → /srv/media/Series

### Current State

- Node-02 runs PostgreSQL and Redis.
- Deployment engine v1 is working.
