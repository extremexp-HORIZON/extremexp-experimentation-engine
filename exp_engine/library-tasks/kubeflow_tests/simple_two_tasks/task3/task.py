print("hello world")
from kubeflow_helper import load_dataset_local
    
ok = load_dataset_local(variables, "input3")
print("Loaded data from task1:", ok)