import docker


class ServiceCheck:

    REQUIRED_CONTAINERS = [
        "choms-postgres",
        "pihole",
        "choms-nginx",
    ]

    @staticmethod
    def get_info():
        try:
            client = docker.from_env()
            containers = {
                container.name: container.status
                for container in client.containers.list(all=True)
            }

            return [
                {
                    "name": name,
                    "installed": name in containers,
                    "active": containers.get(name) == "running",
                    "status": containers.get(name, "missing"),
                }
                for name in ServiceCheck.REQUIRED_CONTAINERS
            ]

        except Exception as exc:
            return [
                {
                    "name": "docker",
                    "installed": False,
                    "active": False,
                    "status": str(exc),
                }
            ]
