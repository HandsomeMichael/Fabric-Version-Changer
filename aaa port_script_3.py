import zipfile
import json
import os
import shutil
import argparse
from datetime import datetime
import tempfile

# Define the output directory for ready mods
READY_FOLDER = "ready"

# Logging function
def log_message(message):
    with open(os.path.join(READY_FOLDER, "patchlog.txt"), "a") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")

def patch_fabric_mod(jar_path, target_minecraft_version="1.21.3"):
    try:
        if not os.path.isfile(jar_path) or not jar_path.endswith('.jar'):
            return f"Error: {jar_path} is not a valid .jar file."

        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                jar.extractall(extract_dir)

            mod_json_path = os.path.join(extract_dir, 'fabric.mod.json')
            if not os.path.exists(mod_json_path):
                return f"Error: fabric.mod.json not found in {jar_path}."

            with open(mod_json_path, 'r') as mod_json_file:
                mod_data = json.load(mod_json_file)

            if "depends" not in mod_data or "minecraft" not in mod_data["depends"]:
                return f"Already compatible: {jar_path} (no Minecraft version dependency)"

            mod_data["depends"]["minecraft"] = target_minecraft_version

            warning_message = None
            if "name" in mod_data:
                if not mod_data["name"].startswith("[PATCHED]"):
                    mod_data["name"] = f"[PATCHED] {mod_data['name']}"
            else:
                warning_message = f"Warning: 'name' field not found in fabric.mod.json of {jar_path}."

            with open(mod_json_path, 'w') as mod_json_file:
                json.dump(mod_data, mod_json_file, indent=4)

            patched_jar_path = os.path.join(READY_FOLDER, f"_patched_{os.path.basename(jar_path)}")
            with zipfile.ZipFile(patched_jar_path, 'w') as patched_jar:
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_name = os.path.relpath(file_path, extract_dir)
                        patched_jar.write(file_path, archive_name)

            log_message(f"Successfully patched {jar_path} and saved as {patched_jar_path}")
            return (f"Patched mod saved as {patched_jar_path}", warning_message)

    except Exception as e:
        log_message(f"Error patching {jar_path}: {e}")
        return f"Error patching {jar_path}: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch Minecraft Fabric mods to a specified Minecraft version.")
    parser.add_argument("jar_files", nargs='*', help="Paths to mod JAR file(s).")
    args = parser.parse_args()
    
    # Check if the user provided jar files or not
    if not args.jar_files:
        # Automatically use all .jar files in the current directory if no files were provided
        jar_files = [f for f in os.listdir() if f.endswith('.jar')]
        if jar_files:
            print("No JAR files provided. Detected the following JAR files in the current directory:")
            for file in jar_files:
                print(f"  - {file}")
            user_input = input("Would you like to patch all detected JAR files? (y/n): ")
            if user_input.lower() != 'y':
                print("No files selected. Exiting...")
                exit()
        else:
            print("No JAR files found in the current directory.")
            exit()
    else:
        jar_files = args.jar_files

    # Prompt for Minecraft version if the user wants a custom one
    default_version = "1.21.3"
    target_version = input(f"Enter the target Minecraft version (or press Enter for default {default_version}): ") or default_version
    print(f"\nTarget Minecraft version set to {target_version}.\n")

    # Initialize lists for success, warning, and error messages
    success_messages = []
    warning_messages = []
    error_messages = []
    compatibility_messages = []

    # Create the "ready" folder if it doesn't exist
    os.makedirs(READY_FOLDER, exist_ok=True)

    total_files = len(jar_files)
    for i, jar_file in enumerate(jar_files, start=1):
        print(f"Processing file {i}/{total_files}: {os.path.basename(jar_file)}")

        log_message(f"Starting patch for {jar_file}...")
        result = patch_fabric_mod(jar_file, target_version)
        
        # Handle the result of patching
        if isinstance(result, tuple):
            success_message, warning = result
            success_messages.append(success_message)
            log_message(success_message)
            if warning:
                warning_messages.append(warning)
                log_message(warning)
        elif "Already compatible" in result:
            ready_path = os.path.join(READY_FOLDER, os.path.basename(jar_file))
            shutil.copy(jar_file, ready_path)
            compatibility_messages.append(result)
            log_message(result)
        elif "Error" in result:
            error_messages.append(result)
            log_message(result)

    # Display summary
    print("\n--- Summary ---")
    if success_messages:
        print("Successfully patched files:")
        for message in success_messages:
            print(f"  - {message}")
    if compatibility_messages:
        print("\nAlready compatible files (no Minecraft dependency found):")
        for message in compatibility_messages:
            print(f"  - {message}")
    if warning_messages:
        print("\nFiles with warnings:")
        for message in warning_messages:
            print(f"  - {message}")
    if error_messages:
        print("\nFiles with errors:")
        for message in error_messages:
            print(f"  - {message}")

    log_message("Patching completed.\n")
    print(f"\nAll processed mods are available in the '{READY_FOLDER}' directory.")
    input("\nPress any key to exit...")
