def build_health_checks(
    wireguard_info,
    firewall_info,
    fail2ban_info,
    services_info,
    compliance_info,
    backup_info,
    updates_info,
):
    checks = []

    checks.append({
        "name": "WireGuard",
        "passed": wireguard_info["installed"] and wireguard_info["active"],
        "details": "active" if wireguard_info["active"] else "not active",
    })

    checks.append({
        "name": "Firewall",
        "passed": firewall_info["installed"] and firewall_info["active"],
        "details": "active" if firewall_info["active"] else "not installed or inactive",
    })

    checks.append({
        "name": "Fail2ban",
        "passed": fail2ban_info["installed"] and fail2ban_info["active"],
        "details": fail2ban_info["status"],
    })

    checks.append({
        "name": "Backup",
        "passed": backup_info["available"] and backup_info["status"] == "ok",
        "details": backup_info["status"],
    })

    checks.append({
        "name": "System updates",
        "passed": updates_info["pending_updates"] == 0,
        "details": f"{updates_info['pending_updates']} pending updates",
    })

    for service in services_info:
        checks.append({
            "name": f"Service: {service['name']}",
            "passed": service["installed"] and service["active"],
            "details": service["status"],
        })

    for item in compliance_info:
        checks.append({
            "name": f"Compliance: {item['area']} / {item['name']}",
            "passed": item["compliant"],
            "details": item["actual"],
        })

    score = round((sum(check["passed"] for check in checks) / len(checks)) * 100)

    return {
        "score": score,
        "checks": checks,
    }
