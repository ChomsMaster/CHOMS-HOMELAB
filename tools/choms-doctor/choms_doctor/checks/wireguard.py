import subprocess


class WireGuardCheck:

    @staticmethod
    def get_info():
        try:
            result = subprocess.run(
                ["wg", "show"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                return {
                    "installed": True,
                    "active": True,
                    "output": result.stdout.strip(),
                }

            return {
                "installed": True,
                "active": False,
                "output": "WireGuard installed but no active interface detected.",
            }

        except FileNotFoundError:
            return {
                "installed": False,
                "active": False,
                "output": "WireGuard command not found.",
            }
