import socket
import psutil


class NetworkCheck:

    @staticmethod
    def get_info():
        interfaces = []

        for name, addresses in psutil.net_if_addrs().items():
            ip_addresses = []

            for address in addresses:
                if address.family == socket.AF_INET:
                    ip_addresses.append(address.address)

            if ip_addresses:
                interfaces.append({
                    "name": name,
                    "ips": ip_addresses,
                })

        return interfaces
