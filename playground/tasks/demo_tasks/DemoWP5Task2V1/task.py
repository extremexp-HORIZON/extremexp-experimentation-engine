from eexp_engine_utils import utils, types

print("Running DemoWP5Task2V1")

dataset = utils.load_dataset(variables, resultMap, "DemoWP5Task2InputFile")

# utils.save_dataset(variables, resultMap, "DemoWP5Task2OutputFile", dataset.to_csv(index=False))
utils.save_dataset(variables, resultMap, "DemoWP5Task2OutputFile", dataset)