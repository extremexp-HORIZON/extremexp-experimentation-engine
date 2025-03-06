[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("I'm ExpTask1")
results = ph.get_experiment_results()
print(f"and here the results so far: {results}")
