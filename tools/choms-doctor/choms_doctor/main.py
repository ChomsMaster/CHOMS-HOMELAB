import sys

from choms_doctor.checks.system import SystemCheck
from choms_doctor.checks.storage import StorageCheck
from choms_doctor.checks.docker import DockerCheck
from choms_doctor.checks.network import NetworkCheck
from choms_doctor.checks.wireguard import WireGuardCheck
from choms_doctor.checks.firewall import FirewallCheck
from choms_doctor.checks.fail2ban import Fail2banCheck
from choms_doctor.checks.services import ServiceCheck
from choms_doctor.checks.compliance import ComplianceCheck
from choms_doctor.report import render_report
from choms_doctor.exporter import export_json


def collect_data():
    data = {
        "system": SystemCheck.get_info(),
        "storage": StorageCheck.get_info(),
        "docker": DockerCheck.get_info(),
        "network": NetworkCheck.get_info(),
        "wireguard": WireGuardCheck.get_info(),
        "firewall": FirewallCheck.get_info(),
        "fail2ban": Fail2banCheck.get_info(),
        "services": ServiceCheck.get_info(),
    }

    data["compliance"] = ComplianceCheck.get_info(data)

    return data


def main():
    data = collect_data()

    if "--json" in sys.argv:
        export_json(data)
        print("JSON report generated: health-report.json")
        return

    render_report(
        data["system"],
        data["storage"],
        data["docker"],
        data["network"],
        data["wireguard"],
        data["firewall"],
        data["fail2ban"],
        data["services"],
        data["compliance"],
    )


if __name__ == "__main__":
    main()
