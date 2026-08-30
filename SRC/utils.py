import hashlib

def generate_fingerprint(uri):
return hashlib.sha256(uri.encode('utf-8')).hexdigest()

def log_result(protocol, host, port, result):
if result['status'] == 'WORKING':
print(f"\n[+] Protocol: {protocol.upper()}")
print(f"Host: {host}")
print(f"Port: {port}")
print(f"VPN IP: {result['ip']}")
print(f"Country: {result['country']}")
print(f"Latency: {result['latency']} ms")
print("YouTube: OK")
print("Status: WORKING")

utils.py
