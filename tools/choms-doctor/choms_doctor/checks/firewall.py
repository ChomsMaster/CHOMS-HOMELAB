import subprocess


class FirewallCheck:

    @staticmethod
    def get_info():
        commands = [
            ["ufw", "status"],
            ["sudo", "-n", "ufw", "status"],
            ["/usr/sbin/ufw", "status"],
            ["sudo", "-n", "/usr/sbin/ufw", "status"],
        ]

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                output = result.stdout.strip()

                if "Status: active" in output:
                    return {
                        "installed": True,
                        "active": True,
                        "output": output,
                    }

                if "Status: inactive" in output:
                    return {
                        "installed": True,
                        "active": False,
                        "output": output,
                    }

            except FileNotFoundError:
                continue

        return {
            "installed": False,
            "active": False,
            "output": "UFW command not found or not accessible.",
        }
