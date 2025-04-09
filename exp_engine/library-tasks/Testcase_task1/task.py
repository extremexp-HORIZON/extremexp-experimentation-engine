[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("I'm Testcase_task1")
param1 = variables.get("param1")
print(f"and here is my param1: {param1}")
resultMap.put("output", int(param1) * 10)

ph.save_dataset(variables, "Task1OutputFile", "contents of file Task1OutputFile", resultMap)