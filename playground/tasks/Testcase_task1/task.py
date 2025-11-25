from eexp_engine_helpers import proactive_helpers as ph

print("I'm Testcase_task1")
param1 = variables.get("param1")
print(f"and here is my param1: {param1}")
ph.save_dataset()
resultMap.put("output", int(param1) * 10)