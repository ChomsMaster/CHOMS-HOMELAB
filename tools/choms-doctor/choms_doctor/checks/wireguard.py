import subprocess


class WireGuardCheck:
    @staticmethod
    def get_info():
        checks = [
            [["wg", "show"], lambda r: "interface: wg0" in r.stdout],
            [["/usr/bin/wg", "show"], lambda r: "interface: wg0" in r.stdout],
            [["ip", "link", "show", "wg0"], lambda r: r.returncode == 0],
            [["systemctl", "is-active", "wg-quick@wg0"], lambda r: r.stdout.strip() == "active"],
        ]

        installed = False

        for command, validator in checks:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    installed = True

                if result.returncode == 0 and validator(result):
                    return {
                        "installed": True,
                        "active": True,
                        "status": "PASS",
                        "details": "active",
                        "output": (result.stdout or result.stderr).strip(),
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
