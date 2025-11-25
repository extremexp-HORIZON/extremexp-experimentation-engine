from eexp_engine_helpers import proactive_helper as ph
from eexp_engine_helpers.types import get_runtime_context
variables, resultMap = get_runtime_context()
import os
import sys
[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]

print("Running DemoWP5Task1")

dataset = ph.load_dataset(variables, resultMap, "DemoWP5Task1InputFile")

demo_param = variables.get("demo_param")
print(f"with value of demo_param: {demo_param}")

increment = 5
metric_name = "ParamIncreasedBy5"

print(f"Increasing this parameter by {increment} and adding the result to the metric {metric_name}")
resultMap.put(metric_name, int(demo_param) + increment)

# print("dataset")
# print(dataset)

ph.save_dataset(variables, resultMap, "DemoWP5Task1OutputFile", dataset)