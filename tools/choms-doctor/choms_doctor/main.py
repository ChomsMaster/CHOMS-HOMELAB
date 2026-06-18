from choms_doctor.checks.system import SystemCheck
from choms_doctor.checks.storage import StorageCheck
from choms_doctor.checks.docker import DockerCheck
from choms_doctor.checks.network import NetworkCheck
from choms_doctor.report import render_report


def main():
    system_info = SystemCheck.get_info()
    storage_info = StorageCheck.get_info()
    docker_info = DockerCheck.get_info()
    network_info = NetworkCheck.get_info()

    render_report(system_info, storage_info, docker_info, network_info)


if __name__ == "__main__":
    main()
