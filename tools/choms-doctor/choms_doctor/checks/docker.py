import docker


class DockerCheck:

    @staticmethod
    def get_info():
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)

            return [
                {
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                }
                for container in containers
            ]

        except Exception as exc:
            return [
                {
                    "name": "docker",
                    "image": "unknown",
                    "status": f"error: {exc}",
                }
            ]
