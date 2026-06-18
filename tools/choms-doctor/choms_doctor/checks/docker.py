import docker


class DockerCheck:

    @staticmethod
    def get_info():
        try:
            client = docker.from_env()
            return client.containers.list(all=True)
        except Exception:
            return []
