import platform
import socket
import psutil


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
