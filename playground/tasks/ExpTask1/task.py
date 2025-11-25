from eexp_engine_utils import utils as ph

print("I'm ExpTask1")
results = ph.get_experiment_results()
print(f"and here the results so far: {results}")

S1_results = results["S1"]["1"]["result"]
file_path = S1_results["Task1OutputFile"]

file_contents = ph.load_dataset_by_path(file_path)
print(file_contents)

input_file = variables.get("T1InputFile")
with open(input_file, "r") as f:
    content = f.readlines()
    print(content)