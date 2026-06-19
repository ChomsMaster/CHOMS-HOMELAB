from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def render_report(
    system_info,
    storage_info,
    docker_info,
    network_info,
    wireguard_info,
    firewall_info,
    fail2ban_info,
    services_info,
    compliance_info,
    backup_info,
    updates_info,
):

    checks = [
        wireguard_info["installed"] and wireguard_info["active"],
        firewall_info["installed"] and firewall_info["active"],
        fail2ban_info["installed"] and fail2ban_info["active"],
        backup_info["available"],
        updates_info["pending_updates"] == 0,
    ]

    for service in services_info:
        checks.append(service["installed"] and service["active"])

    for item in compliance_info:
        checks.append(item["compliant"])

    health_score = round((sum(checks) / len(checks)) * 100)

    console.print(
        Panel.fit(
            f"CHOMS Doctor v0.2\nHealth Score: {health_score}%",
            style="bold cyan",
        )
    )

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

