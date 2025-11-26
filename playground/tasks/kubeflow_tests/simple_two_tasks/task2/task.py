from eexp_engine_utils import types, utils
import pandas as pd
    
variables, resultMap = types.get_runtime_context()

print("hello world")

[ok] = utils.load_datasets_ddm(variables, "input2", resultMap)
df = pd.read_csv(ok)
print("Loaded data from task1:", df.head())