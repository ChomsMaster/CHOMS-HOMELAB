import subprocess


class FirewallCheck:

    @staticmethod
    def get_info():
        try:
            result = subprocess.run(
                ["ufw", "status"],
                capture_output=True,
                text=True,
                check=False,
            )

            output = result.stdout.strip()

            return {
                "installed": True,
                "active": "Status: active" in output,
                "output": output,
            }

        except FileNotFoundError:
            return {
                "installed": False,
                "active": False,
                "output": "UFW command not found.",
            }
