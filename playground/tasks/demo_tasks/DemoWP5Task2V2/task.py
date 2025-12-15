from eexp_engine_utils import utils

print("Running DemoWP5Task2V2")

dataset = utils.load_dataset(variables, resultMap, "DemoWP5Task2InputFile")

utils.save_dataset(variables, resultMap, "DemoWP5Task2OutputFile", dataset)