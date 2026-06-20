import subprocess


class WireGuardCheck:
    @staticmethod
    def get_info():
        commands = [
            ["wg", "show"],
            ["/usr/bin/wg", "show"],
            ["sudo", "-n", "wg", "show"],
            ["sudo", "-n", "/usr/bin/wg", "show"],
        ]

        installed = False

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0:
                    installed = True

                if result.returncode == 0 and "interface: wg0" in result.stdout:
                    return {
                        "installed": True,
                        "active": True,
                        "status": "PASS",
                        "details": "active",
                        "output": result.stdout.strip(),
                    }

            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        return {
            "installed": installed,
            "active": False,
            "status": "FAIL",
            "details": "not active",
            "output": "WireGuard not accessible or wg0 not active.",
        }
