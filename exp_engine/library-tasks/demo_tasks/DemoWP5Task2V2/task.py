[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("Running DemoWP5Task2V2")

dataset = ph.load_dataset(variables, resultMap, "DemoWP5Task2InputFile")

ph.save_dataset(variables, resultMap, "DemoWP5Task2OutputFile", dataset)