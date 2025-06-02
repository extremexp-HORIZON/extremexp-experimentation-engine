[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("Running TestDatasetManagementTaskWriteMultiple")

dataset = ph.load_dataset(variables, resultMap, "TestDatasetManagementTaskWriteMultipleInputFile")

ph.save_datasets(variables, resultMap, "TestDatasetManagementTaskWriteMultipleOutputFolder", [dataset, dataset])