import hashlib
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def generate_salt():
    return os.urandom(16)

def hash_master_password(password, salt):
    # SHA256(password + salt)
    salted_password = password.encode() + salt
    hash_obj = hashlib.sha256(salted_password)
    return base64.b64encode(hash_obj.digest())

def derive_aes_key(master_password, salt):
    # PBKDF2 avec 100000 itérations
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(master_password.encode())

def encrypt_password(password, aes_key):
    # AES-256 encryption
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Padding du mot de passe à 16 bytes
    padded_password = password.encode().ljust(16, b'\0')
    encrypted = encryptor.update(padded_password) + encryptor.finalize()
    
    return base64.b64encode(iv + encrypted)

def decrypt_password(encrypted_data, aes_key):
    # AES-256 decryption
    data = base64.b64decode(encrypted_data)
    iv = data[:16]
    encrypted = data[16:]
    
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    return decrypted.decode().rstrip('\0')