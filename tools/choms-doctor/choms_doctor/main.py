from choms_doctor.checks.system import SystemCheck
from choms_doctor.checks.storage import StorageCheck
from choms_doctor.checks.docker import DockerCheck
from choms_doctor.checks.network import NetworkCheck
from choms_doctor.checks.wireguard import WireGuardCheck
from choms_doctor.checks.firewall import FirewallCheck
from choms_doctor.report import render_report


def main():
    system_info = SystemCheck.get_info()
    storage_info = StorageCheck.get_info()
    docker_info = DockerCheck.get_info()
    network_info = NetworkCheck.get_info()
    wireguard_info = WireGuardCheck.get_info()
    firewall_info = FirewallCheck.get_info()

    render_report(
        system_info,
        storage_info,
        docker_info,
        network_info,
        wireguard_info,
        firewall_info,
    )


if __name__ == "__main__":
    main()
