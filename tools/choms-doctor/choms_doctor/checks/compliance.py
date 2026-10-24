from choms_doctor.config import load_desired_state


class ComplianceCheck:

    @staticmethod
    def get_info(real_data):
        desired = load_desired_state()
        results = []

        required_containers = desired.get("services", {}).get("required_containers", [])
        real_containers = [container["name"] for container in real_data.get("docker", [])]

        for container in required_containers:
            results.append({
                "area": "services",
                "name": container,
                "expected": "present",
                "actual": "present" if container in real_containers else "missing",
                "compliant": container in real_containers,
            })

        required_mounts = desired.get("infrastructure", {}).get("required_mounts", [])
        real_mounts = [disk["mount"] for disk in real_data.get("storage", [])]

        for mount in required_mounts:
            results.append({
                "area": "storage",
                "name": mount,
                "expected": "mounted",
                "actual": "mounted" if mount in real_mounts else "missing",
                "compliant": mount in real_mounts,
            })

        return results
