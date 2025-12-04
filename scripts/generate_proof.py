import subprocess
import base64
import os
import sys

# Try to import cryptography. If this fails, you need to run: pip install cryptography
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:
    print("❌ Error: 'cryptography' library is missing.")
    print("👉 Run this command first: pip install cryptography")
    sys.exit(1)

def main():
    print("------------------------------------------------")
    print("🔐 Generating Submission Proof...")
    
    # 1. Get the current Commit Hash from Git
    try:
        # This gets the hash of the commit you just pushed (91fcec2...)
        commit_hash = subprocess.check_output(['git', 'log', '-1', '--format=%H']).decode().strip()
        print(f"✅ Commit Hash: {commit_hash}")
    except Exception as e:
        print("❌ Error getting git hash. Make sure you are running this from the repo folder.")
        print(f"Error details: {e}")
        return

    # 2. Load Your Private Key
    # We look in the parent directory (root of repo)
    key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "student_private.pem")
    
    if not os.path.exists(key_path):
        # Fallback for running from root
        key_path = "student_private.pem"

    try:
        with open(key_path, "rb") as f:
            student_private_key = serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        print(f"❌ Error: Could not find 'student_private.pem' at {key_path}")
        return

    # 3. Sign the Hash (RSA-PSS)
    # The instructions require signing the ASCII bytes of the hash string
    signature = student_private_key.sign(
        commit_hash.encode('utf-8'), 
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # 4. Load Instructor Public Key
    inst_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instructor_public.pem")
    
    if not os.path.exists(inst_key_path):
        inst_key_path = "instructor_public.pem"

    try:
        with open(inst_key_path, "rb") as f:
            instructor_public_key = serialization.load_pem_public_key(f.read())
    except FileNotFoundError:
        print(f"❌ Error: Could not find 'instructor_public.pem' at {inst_key_path}")
        return

    # 5. Encrypt the Signature (RSA-OAEP)
    encrypted_signature = instructor_public_key.encrypt(
        signature,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 6. Output the result
    final_proof = base64.b64encode(encrypted_signature).decode('utf-8')
    
    print("\n📋 SUBMISSION DATA (Copy these exact values):")
    print(f"1. Commit Hash:             {commit_hash}")
    print(f"2. Encrypted Signature:     {final_proof}")
    print("------------------------------------------------")

if __name__ == "__main__":
    main()