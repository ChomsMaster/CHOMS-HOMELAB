import subprocess


class WireGuardCheck:

    @staticmethod
    def get_info():
        commands = [
            ["wg", "show"],
            ["sudo", "-n", "wg", "show"],
        ]

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode == 0 and "interface: wg0" in result.stdout:
                    return {
                        "installed": True,
                        "active": True,
                        "output": result.stdout.strip(),
                    }

            except FileNotFoundError:
                continue

        return {
            "installed": True,
            "active": False,
            "output": "WireGuard not accessible or wg0 not active.",
        }
