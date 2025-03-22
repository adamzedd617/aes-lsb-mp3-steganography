# Configuration constants
STANDARD_INPUT_FILE_PATH = "input/original_sample.wav"
OUTPUT_BASIC_LSB = "output/basic_lsb_encoded.wav"
OUTPUT_ENHANCED_LSB = "output/enhanced_lsb_encoded.wav"

# Import algorithm modules
from aes import lsb_encode, lsb_decode, lsb_advanced_encode, lsb_advanced_decode

# Dictionary to store algorithms
ALGORITHMS = {
    1: {
        "name": "Basic LSB Steganography with AES",
        "encode": lsb_encode,
        "decode": lsb_decode,
        "output_file": OUTPUT_BASIC_LSB
    },
    2: {
        "name": "Advanced LSB Steganography with AES",
        "encode": lsb_advanced_encode,
        "decode": lsb_advanced_decode,
        "output_file": OUTPUT_ENHANCED_LSB
    }
}