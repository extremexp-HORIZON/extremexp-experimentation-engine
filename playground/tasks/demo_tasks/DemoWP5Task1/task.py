from eexp_engine_utils import utils

print("Running DemoWP5Task1")
dataset = utils.load_dataset(variables, resultMap, "DemoWP5Task1InputFile")

demo_param = variables.get("demo_param")
print(f"with value of demo_param: {demo_param}")

increment = 5
metric_name = "ParamIncreasedBy5"

print(f"Increasing this parameter by {increment} and adding the result to the metric {metric_name}")
resultMap.put(metric_name, int(demo_param) + increment)


utils.save_dataset(variables, resultMap, "DemoWP5Task1OutputFile", dataset)