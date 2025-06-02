[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("Running TestDatasetManagementTaskReadFromFolder")

datasets = ph.load_datasets(variables, resultMap, "TestDatasetManagementTaskReadFromFolderInputFolder")

print("datasets")
print(len(datasets))

ph.save_dataset(variables, resultMap, "TestDatasetManagementTaskReadFromFolderOutputFile", datasets[1])