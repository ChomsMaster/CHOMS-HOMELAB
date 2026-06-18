from choms_doctor.checks import SystemCheck, StorageCheck, DockerCheck
from choms_doctor.report import render_report


def main():
    system_info = SystemCheck.get_info()
    storage_info = StorageCheck.get_info()
    docker_info = DockerCheck.get_info()

    render_report(system_info, storage_info, docker_info)


if __name__ == "__main__":
    main()
