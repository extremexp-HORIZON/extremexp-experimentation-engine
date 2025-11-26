from eexp_engine_utils import utils, types
variables, resultMap = types.get_runtime_context()

print("I'm Testcase_task1")
param1 = variables.get("param1")
print(f"and here is my param1: {param1}")
utils.save_datasets(variables, resultMap, "Task1OutputFile", [str(int(param1) * 10).encode('utf-8')])
resultMap.put("output", int(param1) * 10)