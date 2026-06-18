from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def render_report(system_info, storage_info, docker_info):
    console.print(Panel.fit("CHOMS Doctor v0.1", style="bold cyan"))

    console.print("\n[bold]System[/bold]")
    console.print(f"Hostname: {system_info['hostname']}")
    console.print(f"OS: {system_info['system']} {system_info['release']}")
    console.print(f"Architecture: {system_info['architecture']}")
    console.print(f"CPU: {system_info['cpu']}%")
    console.print(f"Memory: {system_info['memory']}%")

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
        image = container.image.tags[0] if container.image.tags else "unknown"
        docker_table.add_row(
            container.name,
            image,
            container.status,
        )

    console.print(docker_table)
