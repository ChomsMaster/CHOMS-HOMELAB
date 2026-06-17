# Security

## Security Philosophy

Security has been considered a core design principle since the beginning of the project.

Rather than exposing multiple services directly to the Internet, the infrastructure follows a layered security approach where only essential services are publicly accessible.

The objective is to reduce the attack surface while maintaining secure remote administration.

---

# Security Layers

The current platform is protected using multiple security mechanisms.

## Firewall

UFW (Uncomplicated Firewall) controls inbound traffic.

Only explicitly required ports are allowed.

Current allowed services include:

* SSH
* WireGuard
* HTTP (internal testing)

---

## Fail2ban

Fail2ban monitors authentication attempts and automatically blocks IP addresses showing malicious behaviour.

This provides protection against brute-force attacks targeting SSH and future exposed services.

---

## WireGuard VPN

Remote administration is performed exclusively through WireGuard.

Administrative interfaces are never exposed directly to the Internet whenever VPN access is possible.

---

## Docker Isolation

Services run inside isolated Docker containers whenever appropriate.

This reduces dependency conflicts and simplifies maintenance and upgrades.

---

# Security Principles

The infrastructure follows these principles:

* Least privilege.
* Minimize exposed services.
* Keep software updated.
* Document every security-related change.
* Prefer VPN over public administration.

---

# Future Improvements

The following security enhancements are planned:

* HTTPS certificates
* Reverse proxy
* Security headers
* Automatic backups
* Intrusion monitoring
* Multi-factor authentication where applicable

