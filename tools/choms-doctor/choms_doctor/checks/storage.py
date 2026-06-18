import shutil


class StorageCheck:

    @staticmethod
    def get_info():
        disks = []

        for mount in ["/", "/data"]:
            try:
                usage = shutil.disk_usage(mount)

                disks.append({
                    "mount": mount,
                    "total": round(usage.total / (1024**3), 2),
                    "used": round(usage.used / (1024**3), 2),
                    "free": round(usage.free / (1024**3), 2),
                    "percent": round((usage.used / usage.total) * 100, 2),
                })

            except FileNotFoundError:
                disks.append({
                    "mount": mount,
                    "error": "mount not found",
                })

        return disks
