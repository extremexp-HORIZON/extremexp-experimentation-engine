# Setup paths for dependent modules
print("loading Task Dependencies...")

dependent_folders = variables.get("dependent_modules_folders", "")
if dependent_folders:
    import os
    import sys
    for folder in dependent_folders.split(","):
        if folder and folder not in sys.path:
            folder_path = os.path.join(os.getcwd(), folder)
            sys.path.append(folder_path)

print("Task Dependencies loaded.")