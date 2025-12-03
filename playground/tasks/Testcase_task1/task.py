from eexp_engine_utils import utils

print("I'm Testcase_task1")
param1 = variables.get("param1")
print(f"and here is my param1: {param1}")
resultMap.put("output", int(param1) * 10)