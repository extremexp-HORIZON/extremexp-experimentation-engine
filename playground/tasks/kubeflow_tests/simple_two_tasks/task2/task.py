print("hello world")
from kubeflow_helper import load_datasets_ddm
import pandas as pd
    
[ok] = load_datasets_ddm(variables, "input2", resultMap)
df = pd.read_csv(ok)
print("Loaded data from task1:", df.head())