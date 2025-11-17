import exp_engine.src.eexp_engine.executionware.local_helper as ph
variables = {'PREVIOUS_PROCESS_ID': None, 'task_name': 'Task1', 'workflow_id': '-fP0WZoBYAWZyMn0cZCO', 'TestDatasetManagementTask1InputFile': 'exp_engine/library-datasets\\demo_datasets/titanic.csv', 'TestDatasetManagementTask1OutputFile': None}
resultMap = {}


print("Running TestDatasetManagementTask1")

dataset = ph.load_dataset(variables, resultMap, "TestDatasetManagementTask1InputFile")

# print("dataset")
# print(dataset)

ph.save_dataset(variables, resultMap, "TestDatasetManagementTask1OutputFile", dataset.to_csv(index=False))
ph.save_result(resultMap)
