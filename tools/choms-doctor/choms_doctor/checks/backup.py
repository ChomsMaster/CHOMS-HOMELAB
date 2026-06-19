from pathlib import Path
from datetime import datetime


class BackupCheck:

    BACKUP_DIR = Path("/data/backups")

    @staticmethod
    def get_info():
        if not BackupCheck.BACKUP_DIR.exists():
            return {
                "available": False,
                "latest_backup": None,
                "age_days": None,
                "status": "backup directory not found",
            }

        backups = sorted(
            BackupCheck.BACKUP_DIR.glob("choms-homelab_*.tar.gz"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            return {
                "available": False,
                "latest_backup": None,
                "age_days": None,
                "status": "no backups found",
            }

        latest = backups[0]
        modified = datetime.fromtimestamp(latest.stat().st_mtime)
        age_days = (datetime.now() - modified).days

        return {
            "available": True,
            "latest_backup": str(latest),
            "age_days": age_days,
            "status": "ok" if age_days <= 7 else "old backup",
        }
