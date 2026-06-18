import platform
import socket
import shutil
import psutil
import docker


class SystemCheck:

    @staticmethod
    def get_info():

        return {

            "hostname": socket.gethostname(),

            "system": platform.system(),

            "release": platform.release(),

            "architecture": platform.machine(),

            "cpu": psutil.cpu_percent(interval=1),

            "memory": psutil.virtual_memory().percent,

        }


class StorageCheck:

    @staticmethod
    def get_info():

        disks = []

        for mount in ["/", "/data"]:

            try:

                usage = shutil.disk_usage(mount)

                disks.append({

                    "mount": mount,

                    "total": round(usage.total / (1024**3),2),

                    "used": round(usage.used / (1024**3),2),

                    "free": round(usage.free / (1024**3),2),

                    "percent": round((usage.used/usage.total)*100,2)

                })

            except:

                pass

        return disks


class DockerCheck:

    @staticmethod
    def get_info():

        try:

            client = docker.from_env()

            containers = client.containers.list(all=True)

            return containers

        except Exception:

            return []
