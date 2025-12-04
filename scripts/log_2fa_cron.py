import datetime, base64, os, sys, pyotp
from cryptography.hazmat.primitives import hashes

try:
    with open("/data/seed.txt", "r") as f: 
        hex_seed = f.read().strip()
    
    b32_seed = base64.b32encode(bytes.fromhex(hex_seed)).decode('utf-8')
    totp = pyotp.TOTP(b32_seed, digits=6, interval=30)
    
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} - 2FA Code: {totp.now()}")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)