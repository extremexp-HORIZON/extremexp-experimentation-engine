[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("I'm Testcase_task2_v1")

ph.save_dataset(variables, "Task2v1OutputFile", "contents of file Task2v1OutputFile", resultMap)