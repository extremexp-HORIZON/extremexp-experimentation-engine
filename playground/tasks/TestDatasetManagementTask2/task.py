import exp_engine.src.eexp_engine.executionware.local_helper as ph
variables = {'PREVIOUS_PROCESS_ID': 'Task1', 'task_name': 'Task2', 'workflow_id': '-fP0WZoBYAWZyMn0cZCO', 'TestDatasetManagementTask2InputFile': None, 'TestDatasetManagementTask2OutputFile': 'exp_engine/library-datasets\\output/test_local/titanic_once_more.csv'}
resultMap = {}

print("Running TestDatasetManagementTask2")

dataset = ph.load_dataset(variables, resultMap, "TestDatasetManagementTask2InputFile")


ph.save_dataset(variables, resultMap, "TestDatasetManagementTask2OutputFile", dataset)


