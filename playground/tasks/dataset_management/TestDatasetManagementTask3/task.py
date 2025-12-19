from eexp_engine_utils import utils

print("Running TestDatasetManagementTask3")

dataset = utils.load_dataset(variables, resultMap, "TestDatasetManagementTask3InputFile")
utils.save_dataset(variables, resultMap, "TestDatasetManagementTask3OutputFile", dataset)