from eexp_engine_utils import utils

print("Running TestDatasetManagementTaskReadFromFolder")

datasets = utils.load_datasets(variables, resultMap, "TestDatasetManagementTaskReadFromFolderInputFolder")

print("datasets")
print(len(datasets))

utils.save_dataset(variables, resultMap, "TestDatasetManagementTaskReadFromFolderOutputFile", datasets[1])