from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def render_report(data):
    system_info = data["system"]
    storage_info = data["storage"]
    docker_info = data["docker"]
    network_info = data["network"]
    services_info = data["services"]
    compliance_info = data["compliance"]
    backup_info = data["backup"]
    updates_info = data["updates"]
    health_info = data["health"]

    console.print(
        Panel.fit(
            f"CHOMS Doctor v0.2\nHealth Score: {health_info['score']}%",
            style="bold cyan",
        )
    )

    health_table = Table(title="Health Details")
    health_table.add_column("Check")
    health_table.add_column("Status")
    health_table.add_column("Details")

    for check in health_info["checks"]:
        health_table.add_row(
            check["name"],
            "PASS" if check["passed"] else "FAIL",
            check["details"],
        )

    console.print(health_table)

    console.print("\n[bold]System[/bold]")
    console.print(f"Hostname: {system_info['hostname']}")
    console.print(f"OS: {system_info['system']} {system_info['release']}")
    console.print(f"Architecture: {system_info['architecture']}")
    console.print(f"CPU: {system_info['cpu']}%")
    console.print(f"Memory: {system_info['memory']}%")

    console.print("\n[bold]Backup[/bold]")
    console.print(f"Status: {backup_info['status']}")
    console.print(f"Latest: {backup_info['latest_backup']}")
    console.print(f"Age (days): {backup_info['age_days']}")

    console.print("\n[bold]Updates[/bold]")
    console.print(f"Pending updates: {updates_info['pending_updates']}")
    console.print(f"Status: {updates_info['status']}")

    network_table = Table(title="Network Interfaces")
    network_table.add_column("Interface")
    network_table.add_column("IP Addresses")

    for interface in network_info:
        network_table.add_row(interface["name"], ", ".join(interface["ips"]))

    console.print(network_table)

    services_table = Table(title="Required Services")
    services_table.add_column("Service")
    services_table.add_column("Installed")
    services_table.add_column("Active")
    services_table.add_column("Status")

    for service in services_info:
        services_table.add_row(
            service["name"],
            "yes" if service["installed"] else "no",
            "yes" if service["active"] else "no",
            service["status"],
        )

    console.print(services_table)

    compliance_table = Table(title="Compliance")
    compliance_table.add_column("Area")
    compliance_table.add_column("Name")
    compliance_table.add_column("Expected")
    compliance_table.add_column("Actual")
    compliance_table.add_column("Compliant")

    for item in compliance_info:
        compliance_table.add_row(
            item["area"],
            item["name"],
            item["expected"],
            item["actual"],
            "yes" if item["compliant"] else "no",
        )

    console.print(compliance_table)

    storage_table = Table(title="Storage")
    storage_table.add_column("Mount")
    storage_table.add_column("Total GB")
    storage_table.add_column("Used GB")
    storage_table.add_column("Free GB")
    storage_table.add_column("Used %")

    for disk in storage_info:
        storage_table.add_row(
            disk["mount"],
            str(disk["total"]),
            str(disk["used"]),
            str(disk["free"]),
            f"{disk['percent']}%",
        )

    console.print(storage_table)

    docker_table = Table(title="Docker Containers")
    docker_table.add_column("Name")
    docker_table.add_column("Image")
    docker_table.add_column("Status")

    for container in docker_info:
        docker_table.add_row(
            container["name"],
            container["image"],
            container["status"],
        )

    console.print(docker_table)
