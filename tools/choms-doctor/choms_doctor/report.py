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
):
    checks = [
        wireguard_info["installed"] and wireguard_info["active"],
        firewall_info["installed"] and firewall_info["active"],
        fail2ban_info["installed"] and fail2ban_info["active"],
    ]

    for service in services_info:
        checks.append(service["installed"] and service["active"])

    health_score = round((sum(checks) / len(checks)) * 100)
    console.print(Panel.fit(f"CHOMS Doctor v0.1\nHealth Score: {health_score}%", style="bold cyan"))
    console.print("\n[bold]System[/bold]")
    console.print(f"Hostname: {system_info['hostname']}")
    console.print(f"OS: {system_info['system']} {system_info['release']}")
    console.print(f"Architecture: {system_info['architecture']}")
    console.print(f"CPU: {system_info['cpu']}%")
    console.print(f"Memory: {system_info['memory']}%")

    network_table = Table(title="Network Interfaces")
    network_table.add_column("Interface")
    network_table.add_column("IP Addresses")

    for interface in network_info:
        network_table.add_row(interface["name"], ", ".join(interface["ips"]))

    console.print(network_table)

    console.print("\n[bold]WireGuard[/bold]")
    if wireguard_info["installed"] and wireguard_info["active"]:
        console.print("[green]WireGuard active[/green]")
    elif wireguard_info["installed"]:
        console.print("[yellow]WireGuard installed but inactive[/yellow]")
    else:
        console.print("[red]WireGuard not installed[/red]")

    console.print("\n[bold]Firewall[/bold]")
    if firewall_info["installed"] and firewall_info["active"]:
        console.print("[green]UFW active[/green]")
    elif firewall_info["installed"]:
        console.print("[yellow]UFW installed but inactive[/yellow]")
    else:
        console.print("[red]UFW not installed[/red]")

    console.print("\n[bold]Fail2ban[/bold]")
    if fail2ban_info["installed"] and fail2ban_info["active"]:
        console.print("[green]Fail2ban active[/green]")
    elif fail2ban_info["installed"]:
        console.print(f"[yellow]Fail2ban installed but not active: {fail2ban_info['status']}[/yellow]")
    else:
        console.print("[red]Fail2ban not installed[/red]")

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

    storage_table = Table(title="Storage")
    storage_table.add_column("Mount")
    storage_table.add_column("Total GB")
    storage_table.add_column("Used GB")
    storage_table.add_column("Free GB")
    storage_table.add_column("Used %")

    for disk in storage_info:
        if "error" in disk:
            storage_table.add_row(disk["mount"], "-", "-", "-", disk["error"])
        else:
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
        image = container.image.tags[0] if container.image.tags else "unknown"
        docker_table.add_row(container.name, image, container.status)

    console.print(docker_table)
