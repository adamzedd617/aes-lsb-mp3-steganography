import os
import wave
import base64
import secrets
import numpy as np
import soundfile as sf
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from utils.logging_util import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# ========================== AES-256 ENCRYPTION ============================
def get_aes_key():
    """Ensure AES key persistence for consistent encryption and decryption"""
    key_file = "aes_key.bin"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = secrets.token_bytes(32)
        with open(key_file, "wb") as f:
            f.write(key)
        return key


# Secure AES Key (Should be stored securely)
AES_KEY = get_aes_key()


def encrypt_message(message, key):
    """Encrypts a message using AES-256 in CBC mode."""
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).encryptor()
    
    if isinstance(message, str):
        message = message.encode()
    
    padder = padding.PKCS7(128).padder()
    padded_message = padder.update(message) + padder.finalize()
    ciphertext = cipher.update(padded_message) + cipher.finalize()
    return iv + ciphertext


def decrypt_message(encrypted_message, key):
    """Decrypts an AES-256 encrypted message."""
    try:
        if len(encrypted_message) < 16:
            raise ValueError("Decryption error: Message too short.")
        
        iv, ciphertext = encrypted_message[:16], encrypted_message[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).decryptor()
        decrypted_padded = cipher.update(ciphertext) + cipher.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
        return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        return "[DECRYPTION ERROR]"


# ========================== LSB Encoding & Decoding ============================
def lsb_encode(input_audio, output_audio, message):
    encrypted_message = encrypt_message(message, AES_KEY)  # Now returns bytes
    encrypted_message += b'###'  # Append delimiter in bytes

    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))

    # Convert encrypted message bytes to bits
    message_bits = ''.join(format(byte, '08b') for byte in encrypted_message)

    if len(message_bits) > len(frame_bytes):
        raise ValueError("Message is too long to encode!")

    for i in range(len(message_bits)):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(message_bits[i])

    with wave.open(output_audio, 'wb') as new_audio:
        new_audio.setparams(audio.getparams())
        new_audio.writeframes(bytes(frame_bytes))

    logger.info("Encoding Complete!")


def lsb_decode(input_audio):
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))

    message_bits = ''.join(str(byte & 1) for byte in frame_bytes)
    extracted_bytes = bytes(int(message_bits[i:i+8], 2) for i in range(0, len(message_bits), 8))

    # Ensure extracted bytes contain the delimiter
    if b'###' in extracted_bytes:
        encrypted_message = extracted_bytes.split(b'###')[0]  # Extract encrypted bytes
    else:
        logger.error("Decoding error: Delimiter not found.")
        return "[DECODING ERROR]"

    decrypted_message = decrypt_message(encrypted_message, AES_KEY)  # Ensure correct decryption

    #print(f"\n🔹 Decoded Message: {decrypted_message}")  # Print decoded message
    return decrypted_message
    
def fix_lsb_decoding(input_audio):
    """Improves LSB decoding for more accurate message retrieval."""
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))
    
    message_bits = ''.join(str(byte & 1) for byte in frame_bytes)
    extracted_bytes = bytes(int(message_bits[i:i+8], 2) for i in range(0, len(message_bits), 8))
    
    if b'###' in extracted_bytes:
        encrypted_message = extracted_bytes.split(b'###')[0]
        return decrypt_message(encrypted_message, AES_KEY)
    else:
        return "[DECODING ERROR]"    

# ========================== Advanced LSB Encoding & Decoding ============================
def lsb_advanced_encode(input_audio, output_audio, message):
    encrypted_message = encrypt_message(message, AES_KEY)  # Returns bytes
    encrypted_message += b'###'  # Convert delimiter to bytes

    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))

    # Convert encrypted bytes to bits
    message_bits = ''.join(format(byte, '08b') for byte in encrypted_message)

    if len(message_bits) > len(frame_bytes):
        raise ValueError("Message is too long to encode!")

    for i in range(0, len(message_bits), 2):  # Encode in pairs for better robustness
        frame_bytes[i] = (frame_bytes[i] & 254) | int(message_bits[i])
        if i + 1 < len(message_bits):
            frame_bytes[i + 1] = (frame_bytes[i + 1] & 254) | int(message_bits[i + 1])

    with wave.open(output_audio, 'wb') as new_audio:
        new_audio.setparams(audio.getparams())
        new_audio.writeframes(bytes(frame_bytes))

    logger.info("Advanced Encoding Complete!")


def lsb_advanced_decode(input_audio):
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))

    message_bits = ''.join(str(byte & 1) for byte in frame_bytes)
    extracted_bytes = bytes(int(message_bits[i:i+8], 2) for i in range(0, len(message_bits), 8))

    # Ensure extracted bytes contain the delimiter
    if b'###' in extracted_bytes:
        encrypted_message = extracted_bytes.split(b'###')[0]  # Extract encrypted bytes
    else:
        logger.error("Decoding error: Delimiter not found.")
        return "[DECODING ERROR]"

    decrypted_message = decrypt_message(encrypted_message, AES_KEY)  # Ensure correct decryption

    #print(f"\n🔹 Decoded Message: {decrypted_message}")  # Print decoded message
    return decrypted_message


# ========================== ALGORITHM REGISTRY ============================
lsb_algorithms = [
    {"name": "Basic LSB with AES", "encode": lsb_encode, "decode": lsb_decode},
    {"name": "Advanced LSB with AES", "encode": lsb_advanced_encode, "decode": lsb_advanced_decode},
]

logger.info("AES-256 encryption integrated into both Basic and Advanced LSB encoding!")
