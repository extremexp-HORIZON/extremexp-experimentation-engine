[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("I'm ExpTask1")
results = ph.get_experiment_results()
print(f"and here the results so far: {results}")

S1_results = results["S1"]["1"]["result"]
file_path = S1_results["Task1OutputFile"]

file_contents = ph.load_dataset_by_path(file_path)
print(file_contents)