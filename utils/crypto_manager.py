import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoManager:
    def __init__(self):
        self.fernet = None

    def initialize_from_password(self, password: str, salt: bytes = b'shark_contabilidad_salt'):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        if not self.fernet:
            return data
        # Prefix with 'ENC:' to know it's encrypted internally
        token = self.fernet.encrypt(str(data).encode('utf-8'))
        return "ENC:" + token.decode('utf-8')

    def decrypt(self, data: str) -> str:
        if not self.fernet or not str(data).startswith("ENC:"):
            return data
        token = data[4:].encode('utf-8')
        try:
            return self.fernet.decrypt(token).decode('utf-8')
        except Exception:
            return "ERROR_DECRYPTING"
