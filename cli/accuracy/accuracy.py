import numpy as np
import os
from pydub import AudioSegment
from Levenshtein import distance as levenshtein_distance
from utils.logging_util import setup_logger
import soundfile as sf

logger = setup_logger(__name__)

# === Define Multiple LSB Algorithms ===
def lsb_basic_encode(input_audio, output_audio, message):
    """ Basic LSB Encoding """
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))
    
    message += '###'  # Delimiter to signal end
    message_bits = ''.join(format(ord(char), '08b') for char in message)
    
    if len(message_bits) > len(frame_bytes):
        raise ValueError("Message is too long to encode!")

    for i in range(len(message_bits)):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(message_bits[i])

    with wave.open(output_audio, 'wb') as new_audio:
        new_audio.setparams(audio.getparams())
        new_audio.writeframes(bytes(frame_bytes))
    
    print("Encoding Complete!")

def lsb_basic_decode(input_audio):
    """ Basic LSB Decoding """
    with wave.open(input_audio, 'rb') as audio:
        frame_bytes = bytearray(audio.readframes(audio.getnframes()))
    
    message_bits = ''.join(str(byte & 1) for byte in frame_bytes)
    message_bytes = [message_bits[i:i+8] for i in range(0, len(message_bits), 8)]
    message = ''.join(chr(int(byte, 2)) for byte in message_bytes)
    
    message = message.split('###')[0]  # Stop at delimiter
    return message

lsb_algorithms = [
    {"name": "Basic LSB", "encode": lsb_basic_encode, "decode": lsb_basic_decode},
]

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

def calculate_accuracy(original_message, algorithm, input_file_path, output_file_path):
    try:
        algorithm['encode'](input_file_path, output_file_path, original_message)
        decoded_message = algorithm['decode'](output_file_path)

        if decoded_message is None:
            return {"accuracy": 0.0, "psnr": 0.0, "ber": 1.0}

        max_length = max(len(original_message), len(decoded_message))
        padded_original = original_message.ljust(max_length)
        padded_decoded = decoded_message.ljust(max_length)

        # Levenshtein Distance for accuracy
        distance = levenshtein_distance(padded_original, padded_decoded)
        accuracy = ((max_length - distance) / max_length) * 100

        psnr = calculate_psnr(input_file_path, output_file_path)
        ber = calculate_ber(original_message, decoded_message)

        print(f"{algorithm['name']} -> Accuracy: {accuracy:.2f}%, PSNR: {psnr:.2f} dB, BER: {ber:.6f}")
        return {"accuracy": accuracy, "psnr": psnr, "ber": ber}

    except Exception as e:
        print(f"Error in accuracy calculation for {algorithm['name']}: {e}")
        return {"accuracy": 0.0, "psnr": 0.0, "ber": 1.0}

def calculate_psnr(original_audio_path, modified_audio_path):
    try:
        orig_data, orig_sr = sf.read(original_audio_path)
        mod_data, mod_sr = sf.read(modified_audio_path)

        if orig_sr != mod_sr:
            return 0.0

        if orig_data.ndim > 1:
            orig_data = np.mean(orig_data, axis=1)
        if mod_data.ndim > 1:
            mod_data = np.mean(mod_data, axis=1)

        min_length = min(len(orig_data), len(mod_data))
        orig_data, mod_data = orig_data[:min_length], mod_data[:min_length]

        orig_data = orig_data / np.max(np.abs(orig_data), initial=1)
        mod_data = mod_data / np.max(np.abs(mod_data), initial=1)

        mse = np.mean((orig_data - mod_data) ** 2)
        if mse == 0:
            return float('inf')

        return 10 * np.log10(1 / mse)

    except Exception as e:
        print(f"Error calculating PSNR: {e}")
        return 0.0

def calculate_ber(original_message, decoded_message):
    try:
        original_bits = ''.join(format(ord(c), '08b') for c in original_message)
        decoded_bits = ''.join(format(ord(c), '08b') for c in decoded_message)

        max_length = max(len(original_bits), len(decoded_bits))
        original_bits = original_bits.ljust(max_length, '0')
        decoded_bits = decoded_bits.ljust(max_length, '0')

        bit_errors = sum(a != b for a, b in zip(original_bits, decoded_bits))
        return bit_errors / max_length if max_length else 1.0

    except Exception as e:
        print(f"Error calculating BER: {e}")
        return 1.0

def compress_audio(input_path, output_path, bitrate):
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate=bitrate)
    except Exception as e:
        print(f"Error during MP3 compression: {e}")

def decompress_audio(input_path, output_path):
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
    except Exception as e:
        print(f"Error during MP3 decompression: {e}")

def evaluate_robustness(original_message, algorithm, input_file_path, bitrates):
    results = {}
    for bitrate in bitrates:
        compressed_path = f"compressed_{bitrate}.mp3"
        decompressed_path = f"decompressed_{bitrate}.wav"

        compress_audio(input_file_path, compressed_path, bitrate)
        decompress_audio(compressed_path, decompressed_path)

        decoded_message = algorithm['decode'](decompressed_path)
        ber = calculate_ber(original_message, decoded_message) if decoded_message else 1.0

        print(f"{algorithm['name']} - Bitrate: {bitrate}, BER: {ber:.6f}")
        results[bitrate] = ber

        os.remove(compressed_path) if os.path.exists(compressed_path) else None
        os.remove(decompressed_path) if os.path.exists(decompressed_path) else None

    return results


