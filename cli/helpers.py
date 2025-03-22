import os
from utils.logging_util import setup_logger
from cli.config import ALGORITHMS, STANDARD_INPUT_FILE_PATH

# Initialize logger
logger = setup_logger(__name__)

# ========================== MENU DISPLAY FUNCTIONS ============================

def display_menu(options, header):
    """Displays a menu with a header and a list of options."""
    logger.info(f"Displaying {header} menu to the user.")
    print(f"\n{header}:")
    for idx, option in enumerate(options, 1):
        print(f"{idx}) {option}")

def display_algorithm_menu():
    """Displays the algorithm selection menu based on the ALGORITHMS dictionary."""
    options = [algo["name"] for algo in ALGORITHMS.values()]
    display_menu(options, "Select an algorithm")

# ========================== USER INPUT HANDLING ============================

def get_user_choice(num_options):
    """Gets a validated user choice for a menu."""
    try:
        choice = int(input("\nChoice: "))
        if 1 <= choice <= num_options:
            return choice
        else:
            logger.warning("Choice out of range.")
            print("\nInvalid choice, please select a valid option.")
    except ValueError:
        logger.error("Invalid input; not a number.")
        print("\nPlease enter a valid number!")
    return None

def get_file_path(algo_choice, is_input=True):
    """Gets the file path from the user or uses the standard path, limiting attempts to 3."""
    prompt = "input audio file: " if is_input else "output audio file: "
    standard_path = STANDARD_INPUT_FILE_PATH if is_input else ALGORITHMS[algo_choice]["output_file"]

    use_standard = input(f"\nUse standard file path ({standard_path}) for the {prompt} file? (y/n): ")
    if use_standard.lower() == "y":
        if os.path.exists(standard_path):
            logger.info(f"Using standard file path: {standard_path}")
            return standard_path
        else:
            logger.error("Standard file not found. Returning to main menu.")
            return None

    attempts = 0
    while attempts < 3:
        file_path = input(f"Enter the path to the custom {prompt}")
        if os.path.exists(file_path):
            logger.info(f"User entered file path: {file_path}")
            return file_path
        else:
            attempts += 1
            logger.warning(f"File not found: {file_path} ({3 - attempts} attempts left)")

    logger.error("Too many invalid attempts. Returning to the main menu.")
    return None  # Returning None will take the user back to the main menu
