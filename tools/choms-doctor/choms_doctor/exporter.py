import json
from pathlib import Path


def export_json(data, output_path="health-report.json"):
    path = Path(output_path)

    with path.open("w") as file:
        json.dump(data, file, indent=2)

    return path
