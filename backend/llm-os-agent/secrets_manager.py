#!/usr/bin/env python3
"""
Secrets management for Ping AI Agent
Handles encryption/decryption of sensitive data like SSH credentials
"""

from cryptography.fernet import Fernet
import base64
import os
import json
from typing import Dict, Any, Optional

class SecretsManager:
    def __init__(self):
        # Get encryption key from environment
        encryption_key = os.getenv("PING_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate new key if not exists (for development)
            encryption_key = Fernet.generate_key().decode()
            print(f"⚠️  Generated new encryption key. Set PING_ENCRYPTION_KEY={encryption_key} in production")
        
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt SSH credentials for storage"""
        try:
            # Convert credentials to JSON string
            credentials_json = json.dumps(credentials)
            
            # Encrypt the credentials
            encrypted_data = self.cipher.encrypt(credentials_json.encode())
            
            # Return base64 encoded string for database storage
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"Failed to encrypt credentials: {str(e)}")
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt SSH credentials from storage"""
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_credentials.encode())
            
            # Decrypt the credentials
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Parse JSON and return
            return json.loads(decrypted_data.decode())
        except Exception as e:
            raise Exception(f"Failed to decrypt credentials: {str(e)}")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API keys for storage"""
        try:
            encrypted_data = self.cipher.encrypt(api_key.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"Failed to encrypt API key: {str(e)}")
    
    def decrypt_api_key(self, encrypted_api_key: str) -> str:
        """Decrypt API keys from storage"""
        try:
            encrypted_data = base64.b64decode(encrypted_api_key.encode())
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise Exception(f"Failed to decrypt API key: {str(e)}")
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt any text data"""
        try:
            encrypted_data = self.cipher.encrypt(text.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"Failed to encrypt text: {str(e)}")
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt any text data"""
        try:
            encrypted_data = base64.b64decode(encrypted_text.encode())
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise Exception(f"Failed to decrypt text: {str(e)}")
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()
