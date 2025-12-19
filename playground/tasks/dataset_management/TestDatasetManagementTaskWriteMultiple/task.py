from eexp_engine_utils import utils

print("Running TestDatasetManagementTaskWriteMultiple")

dataset = utils.load_dataset(variables, resultMap, "TestDatasetManagementTaskWriteMultipleInputFile")

utils.save_datasets(variables, resultMap, "TestDatasetManagementTaskWriteMultipleOutputFolder", [dataset, dataset])
# One can optionally add a list of files names as an extra arguments, like this:
# ph.save_datasets(variables, resultMap, "TestDatasetManagementTaskWriteMultipleOutputFolder", [dataset, dataset], ["test_data1", "test_data2"])