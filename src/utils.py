import hashlib


def generate_fingerprint(uri: str) -> str:
    """
    Generate SHA-256 fingerprint for a normalized VPN URI.
    """
    normalized = uri.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def mask_uri(uri: str) -> str:
    """
    Hide sensitive credentials from logs.
    The full URI is never printed.
    """
    if "://" not in uri:
        return "[REDACTED]"

    protocol, rest = uri.split("://", 1)

    if "@" in rest:
        _, server_part = rest.rsplit("@", 1)
        return f"{protocol}://***@{server_part}"

    return f"{protocol}://[REDACTED]"


def log_result(protocol: str, host: str, port: int, result: dict) -> None:
    """
    Print a safe result summary without exposing credentials.
    """
    status = result.get("status", "FAILED")

    print(f"\n[{status}] Protocol: {protocol.upper()}")
    print(f"Host: {host}")
    print(f"Port: {port}")

    if status == "WORKING":
        print(f"VPN IP: {result.get('ip', 'Unknown')}")
        print(f"Country: {result.get('country', 'Unknown')}")
        print(f"Latency: {result.get('latency', 'Unknown')} ms")
        print("YouTube: OK")
        print("Status: WORKING")
    else:
        reason = result.get("reason", "Unknown error")
        print(f"Reason: {reason}")
