import numpy as np
import os
import wave
from pydub import AudioSegment
from Levenshtein import distance as levenshtein_distance
from utils.logging_util import setup_logger
import soundfile as sf
from aes import lsb_encode, lsb_decode, encrypt_message, decrypt_message, AES_KEY

# Initialize logger
logger = setup_logger(__name__)

# ========================== LSB ENCODING ALGORITHMS ============================
def lsb_basic_encode(input_audio, output_audio, message):
    """Performs basic LSB encoding of a message into an audio file."""
    if isinstance(message, bytes):
        message = message.decode()  # Convert bytes to string

    message += '###'  # Delimiter to signal end
    message_bits = ''.join(format(ord(char), '08b') for char in message)
    
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))

    if len(message_bits) > len(frame_bytes):
        raise ValueError("Message is too long to encode!")

    for i in range(len(message_bits)):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(message_bits[i])

    with wave.open(output_audio, 'wb') as new_audio:
        new_audio.setparams(audio.getparams())
        new_audio.writeframes(bytes(frame_bytes))
    
    logger.info("Basic LSB encoding complete!")


def lsb_basic_decode(input_audio):
    """Decodes a message from an LSB-encoded audio file."""
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))

    message_bits = ''.join(str(byte & 1) for byte in frame_bytes)
    # Convert bits back into bytes (avoiding incorrect string conversion)
    extracted_bytes = bytes(int(message_bits[i:i+8], 2) for i in range(0, len(message_bits), 8))
    # Debug: Print extracted bytes for verification
    print(f"DEBUG: Extracted Encrypted Bytes (First 32 bytes): {extracted_bytes[:32]}")

    if b'###' in extracted_bytes:
        encrypted_message = extracted_bytes.split(b'###')[0]  # Extract encrypted bytes
    else:
        logger.error("Decoding error: Delimiter not found.")
        return "[DECODING ERROR]"

    decoded_message = decrypt_message(encrypted_message, AES_KEY)
    #print(f"\n🔹 Decoded Message: {decoded_message}")  # Print decoded message
    return decoded_message


def lsb_enhanced_encode(input_audio, output_audio, message):
    """ Enhanced LSB Encoding (Replace with actual implementation) """
    print(f"Enhanced LSB Encoding into {output_audio}")
    # TODO: Implement enhanced LSB encoding logic


def lsb_enhanced_decode(input_audio):
    """ Enhanced LSB Decoding (Replace with actual implementation) """
    print(f"Decoding from {input_audio}")
    return "decoded_message"  # Simulate decoded message


# === Define Algorithm Variants ===
lsb_algorithms = [
    {"name": "Basic LSB", "encode": lsb_basic_encode, "decode": lsb_basic_decode},
    {"name": "Enhanced LSB", "encode": lsb_enhanced_encode, "decode": lsb_enhanced_decode},
]


# ========================== ACCURACY & ROBUSTNESS TESTS ============================
def calculate_accuracy(original_message, algorithm, input_file_path, output_file_path):
    """Calculates message accuracy, PSNR, and BER after encoding and decoding."""
    try:
        if isinstance(original_message, bytes):
            original_message = original_message.decode(errors='ignore')  # Ensure it's a string

        algorithm['encode'](input_file_path, output_file_path, original_message)
        decoded_message = algorithm['decode'](output_file_path)

        if decoded_message is None or decoded_message == "[DECODING ERROR]":
            logger.error("Decoding failed. Accuracy is 0%.")
            return {"accuracy": 0.0, "psnr": 0.0, "ber": 1.0}

        if isinstance(decoded_message, bytes):
            decoded_message = decoded_message.decode(errors='ignore')  # Ensure it's a string

        # Calculate Levenshtein Distance for accuracy
        max_length = max(len(original_message), len(decoded_message))
        padded_original = original_message.ljust(max_length)
        padded_decoded = decoded_message.ljust(max_length)
        distance = levenshtein_distance(padded_original, padded_decoded)
        accuracy = ((max_length - distance) / max_length) * 100

        psnr = calculate_psnr(input_file_path, output_file_path)
        ber = calculate_ber(original_message, decoded_message)

        # Logging detailed accuracy info in the requested format
        logger.info(f"Original Message: {original_message}")
        logger.info(f"Decoded Message: {decoded_message}")
        #logger.info(f"Levenshtein Distance: {distance}")
        logger.info(f"Max Length: {max_length}")
        logger.info(f"PSNR Calculation: {psnr:.2f} dB")
        logger.info(f"BER Calculation: {ber:.6f} (Bit Errors: {int(distance * 8)})")
        logger.info(f"{algorithm['name']} -> Accuracy: {accuracy:.2f}%, PSNR: {psnr:.2f} dB, BER: {ber:.6f}")

        return {"accuracy": accuracy, "psnr": psnr, "ber": ber}

    except Exception as e:
        logger.error(f"Error in accuracy calculation for {algorithm['name']}: {e}")
        return {"accuracy": 0.0, "psnr": 0.0, "ber": 1.0}



def calculate_psnr(original_audio_path, modified_audio_path):
    """Calculates the PSNR between the original and modified audio files."""
    try:
        orig_data, orig_sr = sf.read(original_audio_path)
        mod_data, mod_sr = sf.read(modified_audio_path)

        if orig_sr != mod_sr:
            logger.error("Sampling rates do not match.")
            return 0.0

        # Convert stereo to mono if needed
        if orig_data.ndim > 1:
            orig_data = np.mean(orig_data, axis=1)
        if mod_data.ndim > 1:
            mod_data = np.mean(mod_data, axis=1)

        # Normalize data
        orig_data = orig_data / np.max(np.abs(orig_data), initial=1)
        mod_data = mod_data / np.max(np.abs(mod_data), initial=1)

        # Ensure both arrays have the same length
        min_length = min(len(orig_data), len(mod_data))
        orig_data, mod_data = orig_data[:min_length], mod_data[:min_length]

        mse = np.mean((orig_data - mod_data) ** 2)
        if mse == 0:
            return float('inf')

        psnr = 10 * np.log10(1 / mse)
        logger.info(f"PSNR Calculation: {psnr:.2f} dB")
        return psnr

    except Exception as e:
        logger.error(f"Error calculating PSNR: {e}")
        return 0.0


def calculate_ber(original_message, decoded_message):
    """Calculates the Bit Error Rate (BER) between the original and decoded messages."""
    try:
        if not decoded_message or decoded_message == "[DECODING ERROR]":
            logger.error("Decoded message is empty or corrupted. Setting BER to 1.0")
            return 1.0  # Maximum BER if decoding fails

        original_bits = ''.join(format(ord(c), '08b') for c in original_message)
        decoded_bits = ''.join(format(ord(c), '08b') for c in decoded_message)

        # print(f"Original Bits: {original_bits}")
        # print(f"Decoded Bits:  {decoded_bits}")

        # Ensure both bit sequences have the same length
        max_length = max(len(original_bits), len(decoded_bits))
        original_bits = original_bits.ljust(max_length, '0')
        decoded_bits = decoded_bits.ljust(max_length, '0')

        bit_errors = sum(a != b for a, b in zip(original_bits, decoded_bits))
        ber = bit_errors / max_length if max_length else 1.0

        logger.info(f"BER Calculation: {ber:.6f} (Bit Errors: {bit_errors})")
        return ber

    except Exception as e:
        logger.error(f"Error calculating BER: {e}")
        return 1.0


def compress_audio(input_path, output_path, bitrate):
    """Compresses an audio file to a specified bitrate."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate=bitrate)
    except Exception as e:
        print(f"Error during MP3 compression: {e}")


def decompress_audio(input_path, output_path):
    """Decompresses an MP3 file back to WAV format."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
    except Exception as e:
        print(f"Error during MP3 decompression: {e}")


def evaluate_robustness(original_message, algorithm, input_file_path, bitrates):
    """Evaluates LSB robustness under different compression bitrates."""
    results = {}
    for bitrate in bitrates:
        compressed_path = f"compressed_{bitrate}.mp3"
        decompressed_path = f"decompressed_{bitrate}.wav"

        compress_audio(input_file_path, compressed_path, bitrate)
        decompress_audio(compressed_path, decompressed_path)

        decoded_message = algorithm['decode'](decompressed_path)

        if decoded_message is None or decoded_message == "[DECODING ERROR]":
            ber = 1.0  # Maximum BER if decoding fails
        else:
            ber = calculate_ber(original_message, decoded_message)

        print(f"{algorithm['name']} - Bitrate: {bitrate}, BER: {ber:.6f}")
        results[bitrate] = ber

        os.remove(compressed_path) if os.path.exists(compressed_path) else None
        os.remove(decompressed_path) if os.path.exists(decompressed_path) else None

    return results


