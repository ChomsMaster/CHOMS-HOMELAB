import subprocess


class Fail2banCheck:

    @staticmethod
    def get_info():
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "fail2ban"],
                capture_output=True,
                text=True,
                check=False,
            )

            status = result.stdout.strip()

            return {
                "installed": status != "unknown",
                "active": status == "active",
                "status": status,
            }

        except FileNotFoundError:
            return {
                "installed": False,
                "active": False,
                "status": "systemctl not found",
            }
