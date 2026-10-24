from pathlib import Path
import yaml


def load_desired_state():
    config_path = Path("desired_state.yaml")

    if not config_path.exists():
        return {}

    with config_path.open("r") as file:
        return yaml.safe_load(file)
