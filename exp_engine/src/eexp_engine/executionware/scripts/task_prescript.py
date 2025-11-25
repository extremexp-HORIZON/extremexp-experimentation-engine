import sys
import os

# Setup paths for dependent modules
dependent_folders = variables.get("dependent_modules_folders", "")
if dependent_folders:
    for folder in dependent_folders.split(","):
        if folder and folder not in sys.path:
            folder_path = os.path.join(os.getcwd(), folder)
            sys.path.append(folder_path)