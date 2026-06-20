import subprocess


class FirewallCheck:
    @staticmethod
    def get_info():
        commands = [
            ["ufw", "status"],
            ["/usr/sbin/ufw", "status"],
            ["sudo", "-n", "ufw", "status"],
            ["sudo", "-n", "/usr/sbin/ufw", "status"],
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

                output = result.stdout.strip()

                if result.returncode == 0:
                    installed = True

                if result.returncode == 0 and "Status: active" in output:
                    return {
                        "installed": True,
                        "active": True,
                        "status": "PASS",
                        "details": "active",
                        "output": output,
                    }

                if result.returncode == 0 and "Status: inactive" in output:
                    return {
                        "installed": True,
                        "active": False,
                        "status": "FAIL",
                        "details": "inactive",
                        "output": output,
                    }

            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        return {
            "installed": installed,
            "active": False,
            "status": "FAIL",
            "details": "not installed or inactive",
            "output": "UFW not accessible or not active.",
        }
