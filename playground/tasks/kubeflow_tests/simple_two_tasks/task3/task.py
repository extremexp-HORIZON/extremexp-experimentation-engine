from eexp_engine_utils import types, utils
variables, resultMap = types.get_runtime_context()
    
print("hello world")

[ok] = utils.load_datasets_ddm(variables, "input3", resultMap)
print("Loaded data from task1:", ok)