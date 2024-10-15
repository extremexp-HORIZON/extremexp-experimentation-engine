import json
import itertools
import pprint

experiment_name = "IDEKO"

with open('intent_to_dsl.json', 'r') as file:
    spec = json.load(file)

# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(spec)

intent_name = spec["intent_name"]
tasks = spec["tasks"]
workflows = spec["workflows"]

output = f"experiment {intent_name}_EXPERIMENT "
output += "{ \n\n"

output += f"\tintent {intent_name};\n\n"

output += "\tcontrol {\n"

for w1, w2 in zip(workflows[::1], workflows[1::1]):
    output += f"\t\t{w1['experiment_space_name']} -> {w2['experiment_space_name']};\n"
output += "\t}"

output += "\n\n"

for w in workflows:
    output += f"\tspace {w['experiment_space_name']} of {w['workflow_name']}"
    output += " { } \n"

output += "\n}\n\n"

main_workflow_name = f"{intent_name}_WORKFLOW"
output += f"workflow {main_workflow_name} "
output += "{\n\n"

for t in tasks:
    output += f"\tdefine task {t};\n"
output += "\n"

output += "\tSTART -> "
for t in tasks:
    output += f"{t} -> "
output += "END;\n\n"

implementations = {}
for t in tasks:
    implementations[t] = []

for w in workflows:
    task_implementations = w["task_implementations"]
    for t in task_implementations:
        implementations[t].append(task_implementations[t])

unique_implementations = {}
for t in tasks:
    unique_implementations[t] = set(implementations[t])

concrete_tasks = {}
for t in unique_implementations:
    if len(unique_implementations[t]) == 1:
        concrete_tasks[t] = unique_implementations[t].pop()

for ct in concrete_tasks:
    output += f"\tconfigure task {ct} "
    output += "{\n"
    output += f"\t\timplementation '{concrete_tasks[ct]}';\n"
    output += "\t}\n\n"

output += "}\n\n"

concrete_tasks_keys = concrete_tasks.keys()
for w in workflows:
    name = w["workflow_name"]
    task_implementations = w["task_implementations"]
    output += f"workflow {name} from {main_workflow_name}"
    output += "{\n\n"
    for t in task_implementations:
        if t not in concrete_tasks_keys:
            output += f"\tconfigure task {t}"
            output += "{\n"
            output += f"\t\timplementation '{task_implementations[t]}';\n"
            output += "\t}\n\n"
    output += "}\n\n"


pp = pprint.PrettyPrinter(indent=4)
pp.pprint(unique_implementations)

with open('result.dsl', 'w') as file:
    file.write(output)

print("Done.")
