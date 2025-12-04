import base64
import os
import time
from fastapi import FastAPI, Response
from pydantic import BaseModel
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import pyotp

app = FastAPI()
SEED_FILE = "/data/seed.txt"
PRIVATE_KEY_FILE = "student_private.pem"

class SeedRequest(BaseModel):
    encrypted_seed: str

class VerifyRequest(BaseModel):
    code: str

def get_totp():
    if not os.path.exists(SEED_FILE): return None
    with open(SEED_FILE, "r") as f: hex_seed = f.read().strip()
    # Convert Hex -> Bytes -> Base32
    b32_seed = base64.b32encode(bytes.fromhex(hex_seed)).decode('utf-8')
    return pyotp.TOTP(b32_seed, digits=6, interval=30)
@app.post("/decrypt-seed")
async def decrypt_seed(req: SeedRequest):
    try:
        with open(PRIVATE_KEY_FILE, "rb") as k:
            priv_key = serialization.load_pem_private_key(k.read(), password=None)
        
        decrypted = priv_key.decrypt(
            base64.b64decode(req.encrypted_seed),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        hex_seed = decrypted.decode('utf-8')
        if len(hex_seed) != 64: raise ValueError("Invalid Seed")
        
        os.makedirs("/data", exist_ok=True)
        with open(SEED_FILE, "w") as f: f.write(hex_seed)
        return {"status": "ok"}
    except Exception as e:
        print(f"Decryption Error: {e}")
        return Response('{"error": "Decryption failed"}', 500)

@app.get("/generate-2fa")
async def gen_2fa():
    totp = get_totp()
    if not totp: return Response('{"error": "Seed not decrypted yet"}', 500)
    return {"code": totp.now(), "valid_for": 30 - (int(time.time()) % 30)}

@app.post("/verify-2fa")
async def verify_2fa(req: VerifyRequest):
    if not req.code: return Response('{"error": "Missing code"}', 400)
    totp = get_totp()
    if not totp: return Response('{"error": "Seed not decrypted yet"}', 500)
    return {"valid": totp.verify(req.code, valid_window=1)}