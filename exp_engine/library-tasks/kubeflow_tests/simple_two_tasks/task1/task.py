from classes.ok import print_if_i_want
from kubeflow_helper import save_dataset_local

print("hello world")
print("variables", variables)

save_dataset_local(variables, resultMap, "output1", "I am here from task1")

print_if_i_want("Auto egine print apo to dependency file")