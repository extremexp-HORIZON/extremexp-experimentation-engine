print("Running TestDatasetManagementTask1")

from eexp_engine_utils import utils


dataset = utils.load_dataset(variables, resultMap, "TestDatasetManagementTask1InputFile")

# print("dataset")
# print(dataset)

utils.save_dataset(variables, resultMap, "TestDatasetManagementTask1OutputFile", dataset)