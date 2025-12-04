[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("Running TestDatasetManagementTask2")

dataset = ph.load_dataset(variables, resultMap, "TestDatasetManagementTask2InputFile")

ph.save_dataset(variables, resultMap, "TestDatasetManagementTask2OutputFile", dataset)