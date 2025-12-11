"""
C.O.V.E.R.T - Server-Side Encryption Service

Handles server-side encryption operations for moderator notes
and other backend encryption needs.
Note: Report encryption is done client-side - server never sees plaintext reports.
"""

import os
import hashlib
import secrets
import base64
from typing import Optional
from datetime import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from app.core.config import settings


class EncryptionError(Exception):
    """Encryption operation error"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class EncryptionService:
    """
    Server-side encryption service for internal operations

    This is used for:
    - Moderator notes encryption (with rotating group key)
    - Internal data encryption
    - Key derivation

    NOT used for report encryption (that's client-side only)
    """

    def __init__(self):
        self.key_size = 32  # 256 bits
        self.iv_size = 12  # 96 bits for GCM
        self.tag_size = 16  # 128 bits
        self.pbkdf2_iterations = 100000
        self.backend = default_backend()

    def generate_key(self) -> bytes:
        """
        Generate a random AES-256 key

        Returns:
            32 bytes of random key material
        """
        return secrets.token_bytes(self.key_size)

    def generate_salt(self, length: int = 16) -> bytes:
        """
        Generate a random salt

        Args:
            length: Salt length in bytes

        Returns:
            Random salt bytes
        """
        return secrets.token_bytes(length)

    def derive_key(
        self,
        password: str,
        salt: bytes,
        iterations: Optional[int] = None
    ) -> bytes:
        """
        Derive a key from password using PBKDF2

        Args:
            password: Password string
            salt: Salt bytes
            iterations: Number of iterations (default: 100000)

        Returns:
            Derived key bytes
        """
        if iterations is None:
            iterations = self.pbkdf2_iterations

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=salt,
            iterations=iterations,
            backend=self.backend,
        )

        return kdf.derive(password.encode())

    def encrypt(self, plaintext: bytes, key: bytes) -> dict:
        """
        Encrypt data using AES-256-GCM

        Args:
            plaintext: Data to encrypt
            key: Encryption key (32 bytes)

        Returns:
            Dict with iv, ciphertext, and tag (all base64 encoded)
        """
        if len(key) != self.key_size:
            raise EncryptionError(
                "INVALID_KEY",
                f"Key must be {self.key_size} bytes"
            )

        # Generate random IV
        iv = os.urandom(self.iv_size)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()

        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        return {
            "iv": base64.b64encode(iv).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "tag": base64.b64encode(encryptor.tag).decode(),
            "version": 1,
            "algorithm": "AES-256-GCM",
        }

    def decrypt(self, encrypted_data: dict, key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM

        Args:
            encrypted_data: Dict with iv, ciphertext, and tag
            key: Decryption key (32 bytes)

        Returns:
            Decrypted plaintext bytes
        """
        if len(key) != self.key_size:
            raise EncryptionError(
                "INVALID_KEY",
                f"Key must be {self.key_size} bytes"
            )

        try:
            iv = base64.b64decode(encrypted_data["iv"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            tag = base64.b64decode(encrypted_data["tag"])

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()

            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext
        except Exception as e:
            raise EncryptionError(
                "DECRYPTION_FAILED",
                f"Failed to decrypt data: {str(e)}"
            )

    def encrypt_string(self, plaintext: str, key: bytes) -> str:
        """
        Encrypt a string and return JSON-serializable result

        Args:
            plaintext: String to encrypt
            key: Encryption key

        Returns:
            JSON string with encrypted data
        """
        import json
        encrypted = self.encrypt(plaintext.encode(), key)
        return json.dumps(encrypted)

    def decrypt_string(self, encrypted_json: str, key: bytes) -> str:
        """
        Decrypt a JSON-encoded encrypted string

        Args:
            encrypted_json: JSON string with encrypted data
            key: Decryption key

        Returns:
            Decrypted string
        """
        import json
        encrypted_data = json.loads(encrypted_json)
        plaintext = self.decrypt(encrypted_data, key)
        return plaintext.decode()

    def hash_data(self, data: bytes) -> str:
        """
        Compute SHA-256 hash

        Args:
            data: Data to hash

        Returns:
            Hex-encoded hash
        """
        return hashlib.sha256(data).hexdigest()

    def hash_key(self, key: bytes) -> str:
        """
        Compute a key fingerprint for identification

        Args:
            key: Key bytes

        Returns:
            Truncated hash for identification
        """
        full_hash = hashlib.sha256(key).hexdigest()
        return full_hash[:16]  # First 8 bytes

    def compute_commitment_hash(self, cid: str) -> str:
        """
        Compute the commitment hash for blockchain storage

        Args:
            cid: IPFS CID

        Returns:
            0x-prefixed hex hash
        """
        hash_bytes = hashlib.sha256(cid.encode()).digest()
        return "0x" + hash_bytes.hex()

    def generate_nullifier(self) -> str:
        """
        Generate a random nullifier for ZKP

        Returns:
            0x-prefixed hex nullifier
        """
        nullifier_bytes = secrets.token_bytes(32)
        return "0x" + nullifier_bytes.hex()

    def create_merkle_leaf(
        self,
        cid_hash: str,
        timestamp: datetime,
        action: str
    ) -> str:
        """
        Create a Merkle tree leaf for daily anchoring

        Args:
            cid_hash: Commitment hash
            timestamp: Action timestamp
            action: Action type

        Returns:
            Leaf hash
        """
        data = f"{cid_hash}:{timestamp.isoformat()}:{action}"
        return hashlib.sha256(data.encode()).hexdigest()


class ModeratorKeyManager:
    """
    Manages rotating group encryption keys for moderator notes
    """

    def __init__(self, encryption_service: EncryptionService):
        self.encryption = encryption_service
        self._current_key: Optional[bytes] = None
        self._key_id: Optional[str] = None
        self._key_created_at: Optional[datetime] = None

    def get_current_key(self) -> tuple[bytes, str]:
        """
        Get the current moderator group key

        Returns:
            Tuple of (key bytes, key ID)
        """
        if self._current_key is None:
            self._generate_new_key()

        return self._current_key, self._key_id

    def rotate_key(self) -> tuple[bytes, str]:
        """
        Rotate the moderator group key

        Returns:
            Tuple of (new key bytes, new key ID)
        """
        old_key = self._current_key
        old_key_id = self._key_id

        self._generate_new_key()

        # Log rotation
        if old_key_id:
            # In production, trigger re-encryption of active notes
            pass

        return self._current_key, self._key_id

    def _generate_new_key(self):
        """Generate a new key"""
        self._current_key = self.encryption.generate_key()
        self._key_id = self.encryption.hash_key(self._current_key)
        self._key_created_at = datetime.utcnow()

    def encrypt_notes(self, notes: str) -> tuple[str, str]:
        """
        Encrypt moderator notes with current key

        Args:
            notes: Notes to encrypt

        Returns:
            Tuple of (encrypted notes JSON, key ID)
        """
        key, key_id = self.get_current_key()
        encrypted = self.encryption.encrypt_string(notes, key)
        return encrypted, key_id

    def decrypt_notes(self, encrypted_notes: str, key: bytes) -> str:
        """
        Decrypt moderator notes

        Args:
            encrypted_notes: Encrypted notes JSON
            key: Decryption key

        Returns:
            Decrypted notes string
        """
        return self.encryption.decrypt_string(encrypted_notes, key)


# Singleton instances
encryption_service = EncryptionService()
moderator_key_manager = ModeratorKeyManager(encryption_service)
