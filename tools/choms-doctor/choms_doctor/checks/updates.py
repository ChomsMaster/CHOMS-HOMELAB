import subprocess


class UpdateCheck:

    @staticmethod
    def get_info():
        try:
            result = subprocess.run(
                ["apt", "list", "--upgradable"],
                capture_output=True,
                text=True,
                check=False,
            )

            lines = [
                line for line in result.stdout.splitlines()
                if line and not line.startswith("Listing")
            ]

            return {
                "pending_updates": len(lines),
                "status": "ok" if len(lines) == 0 else "updates available",
            }

        except FileNotFoundError:
            return {
                "pending_updates": None,
                "status": "apt not found",
            }
