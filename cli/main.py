import os
import sys
from tqdm import tqdm

# Ensure the project root is in the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Import necessary modules
from utils.logging_util import setup_logger
from cli.helpers import display_menu, get_user_choice, get_file_path, display_algorithm_menu
from cli.config import ALGORITHMS
from cli.accuracy import calculate_accuracy
from cli.aes import encrypt_message, decrypt_message, get_aes_key

# Initialize logger
logger = setup_logger(__name__)

# Ensure AES key persistence
AES_KEY = get_aes_key()

def handle_algorithm_choice(encode=True):
    """Handles the user's choice of algorithm for encoding or decoding."""
    display_algorithm_menu()
    algo_choice = get_user_choice(len(ALGORITHMS))
    
    if algo_choice is None or algo_choice not in ALGORITHMS:
        logger.warning("Invalid algorithm choice. Returning to main menu.")
        return

    input_file = get_file_path(algo_choice, is_input=True)
    if input_file is None:
        logger.warning("Input file selection failed. Returning to main menu.")
        return  # Return to main menu if file selection fails

    output_file = get_file_path(algo_choice, is_input=False)
    
    if encode:
        logger.info(f"User selected encoding with {ALGORITHMS[algo_choice]['name']}")
        secret_message = input("Enter the secret message to encode: ")
        handle_encode(algo_choice, input_file, output_file, secret_message)
    else:
        logger.info(f"User selected decoding with {ALGORITHMS[algo_choice]['name']}")
        handle_decode(algo_choice, output_file)



def handle_encode(algo_choice, input_file, output_file, secret_message):
    """Encodes a message using the selected algorithm."""
    algorithm = ALGORITHMS[algo_choice]
    logger.info(f"Encoding using {algorithm['name']} -> Output file: {output_file}")
    
    for _ in tqdm(range(1), desc="Encoding Progress"):
        algorithm['encode'](input_file, output_file, secret_message)

def handle_decode(algo_choice, output_file):
    """Decodes a message using the selected algorithm and decrypts it."""
    algorithm = ALGORITHMS[algo_choice]
    logger.info(f"Decoding using {algorithm['name']} -> Output file: {output_file}")
    
    for _ in tqdm(range(1), desc="Decoding Progress"):
        encrypted_message = algorithm['decode'](output_file)
    
    if encrypted_message:
        decrypted_message = decrypt_message(encrypted_message, AES_KEY)
        print(f"\n🔹 Decoded Message ({algorithm['name']}): {decrypted_message}")
        logger.info(f"Decoded Message: {decrypted_message}")
    else:
        print("\n❌ Decoding failed. No message extracted.")
        logger.error("Decoding failed. No message extracted.")

def handle_accuracy_check():
    """Calculates and displays the accuracy of the decoded message."""
    original_message = input("Enter the original secret message for accuracy calculation: ")
    display_algorithm_menu()
    algo_choice = get_user_choice(len(ALGORITHMS))
    
    if algo_choice is None or algo_choice not in ALGORITHMS:
        logger.warning("Invalid algorithm choice.")
        print("\nInvalid algorithm choice!")
        return

    input_file = get_file_path(algo_choice, is_input=True)
    output_file = get_file_path(algo_choice, is_input=False)
    algorithm = ALGORITHMS[algo_choice]
    
    for _ in tqdm(range(1), desc="Accuracy Calculation Progress"):
        calculate_accuracy(original_message, algorithm, input_file_path=input_file, output_file_path=output_file)

def handle_main_choice(choice):
    """Processes the user's main menu selection."""
    logger.info(f"User selected menu choice: {choice}")
    
    if choice == 1:
        handle_algorithm_choice(encode=True)
    elif choice == 2:
        handle_algorithm_choice(encode=False)
    elif choice == 3:
        handle_accuracy_check()
    elif choice == 4:
        logger.info("Exiting the program.")
        sys.exit(0)
    else:
        logger.warning("Invalid menu choice.")
        print("\nPlease enter a valid choice!")

def main():
    """Main function to run the CLI program."""
    while True:
        display_menu(["Encode a message", "Decode a message", "Calculate accuracy", "Exit"], "Select an option")
        choice = get_user_choice(4)
        if choice is not None:
            handle_main_choice(choice)

if __name__ == "__main__":
    main()
