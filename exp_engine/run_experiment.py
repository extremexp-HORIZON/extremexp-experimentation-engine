import textx
import exp_engine_functions as functions
import exp_engine_classes as classes
import exp_engine_exceptions
import itertools
import os
import pprint
import random

EXPERIMENTS_FOLDER = '../dsl/mid-term/'
EXECUTIONWARE = "PROACTIVE"

printexperiments = []
nodes = set()
automated_events = set()
manual_events = set()
spaces = set()
space_configs = []
automated_dict = {}
manual_dict = {}
parsed_manual_events = []
parsed_automated_events = []

results = {}

def execute_automated_event(node):
    print("executing automated event")
    e = next((e for e in parsed_automated_events if e.name == node), None)

    print(e.task)

    module = __import__('IDEKO_events')
    func = getattr(module, e.task)
    ret = func(results)
    print("--------------------------------------------------------------------")
    return ret

def execute_manual_event(node):
    print("executing manual event")
    e = next((e for e in parsed_manual_events if e.name == node), None)

    # print(e.task)

    module = __import__('IDEKO_events')
    func = getattr(module, e.task)
    ret = func(automated_dict,space_configs,e.name)
    print("--------------------------------------------------------------------")
    return ret


def execute_space(node):
    print("executing space")

    space_config = next((s for s in space_configs if s['name'] == node), None)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(space_config)
    print('-------------------------------------------------------------------')
    print(f"Running experiment of espace '{space_config['name']}' of type '{space_config['strategy']}'")
    method_type = space_config["strategy"]

    if method_type == "gridsearch":
        run_grid_search(space_config)

    if method_type == "randomsearch":
        run_random_search(space_config)

    print("node executed")
    print("Results so far")
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(results)

    return 'True'

def run_grid_search(space_config):
     grid_search_combinations = []
     VPs = space_config["VPs"]
     vp_combinations = []

     for vp_data in VPs:
         if vp_data["type"] == "enum":
             vp_name = vp_data["name"]
             vp_values = vp_data["values"]
             vp_combinations.append([(vp_name, value) for value in vp_values])

         elif vp_data["type"] == "range":
             vp_name = vp_data["name"]
             min_value = vp_data["min"]
             max_value = vp_data["max"]
             step_value = vp_data.get("step", 1) if vp_data["step"] != 0 else 1
             vp_values = list(range(min_value, max_value + 1, step_value))
             vp_combinations.append([(vp_name, value) for value in vp_values])

         # Generate combinations
     combinations = list(itertools.product(*vp_combinations))
     grid_search_combinations.extend(combinations)

     print(f"\nGrid search generated {len(combinations)} configurations to run.\n")
     for combination in combinations:
         print(combination)

     space_results = {}
     results[space_config['name']] = space_results
     run_count = 1
     for c in combinations:
         print(f"Run {run_count}")
         workflow_to_run = get_workflow_to_run(space_config, c)
         result = functions.execute_wf(workflow_to_run, EXECUTIONWARE)
         workflow_results = {}
         workflow_results["configuration"] = c
         workflow_results["result"] = result
         space_results[run_count] = workflow_results
         print("..........")
         run_count += 1


def get_workflow_to_run(space_config, c):
    c_dict = dict(c)
    w = next(w for w in assembled_flat_wfs if w.name == space_config["assembled_workflow"])
    for t in w.tasks:
        if t.name in space_config["tasks"].keys():
            task_config = space_config["tasks"][t.name]
            for param_name, param_vp in task_config.items():
                alias = param_vp
                print(f"Setting param '{param_name}' of task '{t.name}' to '{c_dict[alias]}'")
                t.set_param(param_name, c_dict[alias])
    return w

def  run_random_search(space_config):
    random_combinations = []

    vps = space_config['VPs']
    runs = space_config['runs']

    for i in range(runs):
        combination = []
        for vp in vps:
            vp_name = vp['name']
            min_val = vp['min']
            max_val = vp['max']

            value = random.randint(min_val, max_val)

            combination.append((vp_name, value))

        random_combinations.append(tuple(combination))

    print(f"\nRandom search generated {len(random_combinations)} configurations to run.\n")
    for c in random_combinations:
        print(c)


    run_count = 1
    space_results = {}
    results[space_config['name']] = space_results
    for c in random_combinations:
        print(f"Run {run_count}")
        workflow_to_run = get_workflow_to_run(space_config, c)
        result = functions.execute_wf(workflow_to_run, EXECUTIONWARE)
        workflow_results = {}
        workflow_results["configuration"] = c
        workflow_results["result"] = result
        space_results[run_count] = workflow_results
        print("..........")
        run_count += 1





def execute_node(node):
    print(node)

    if node in spaces:
        return execute_space(node)

    elif node in automated_events:
        return  execute_automated_event(node)

    elif node in manual_events:
        return execute_manual_event(node)


dsl_file = input("Please provide the name of the DSL file (without the extension):")

with open(EXPERIMENTS_FOLDER + dsl_file + '.dsl', 'r') as file:
    experiment_specification = file.read()

experiments_metamodel = textx.metamodel_from_file('../dsl/workflow_grammar_new.tx')
experiment_model = experiments_metamodel.model_from_str(experiment_specification)


print("*********************************************************")
print("***************** PARSE WORKFLOWS ***********************")
print("*********************************************************")

parsed_workflows = []
for component in experiment_model.component:
    if component.__class__.__name__ == 'Workflow':
        wf = classes.Workflow(component.name)
        parsed_workflows.append(wf)

        task_dependencies = {}

        for e in component.elements:
            if e.__class__.__name__ == "DefineTask":
                task = classes.WorkflowTask(e.name)
                wf.add_task(task)

            if e.__class__.__name__ == "DefineData":
                ds = classes.WorkflowDataset(e.name)
                wf.add_dataset(ds)

            if e.__class__.__name__ == "ConfigureTask":
                task = wf.get_task(e.alias.name)
                if e.workflow:
                    task.add_sub_workflow_name(e.workflow.name)
                elif e.filename:
                    if not os.path.exists(e.filename):
                        raise exp_engine_exceptions.ImplementationFileNotFound(f"{e.filename} in task {e.alias.name}")
                    task.add_implementation_file(e.filename)
                if e.dependency:
                    task.add_dependent_module(e.dependency)

            if e.__class__.__name__ == "ConfigureData":
                ds = wf.get_dataset(e.alias.name)
                ds.add_path(e.path)

            if e.__class__.__name__ == "StartAndEndEvent":
                functions.process_dependencies(task_dependencies, e.nodes, "StartAndEndEvent")

            if e.__class__.__name__ == "StartEvent":
                functions.process_dependencies(task_dependencies, e.nodes, "StartEvent")

            if e.__class__.__name__ == "EndEvent":
                functions.process_dependencies(task_dependencies, e.nodes, "EndEvent")

            if e.__class__.__name__ == "TaskLink":
                functions.process_dependencies(task_dependencies, [e.initial_node] + e.nodes, "TaskLink")

            if e.__class__.__name__ == "DataLink":
                functions.add_input_output_data(wf, [e.initial] + e.rest)

            if e.__class__.__name__ == "ConditionLink":
                condition = e.condition
                fromNode = e.from_node
                ifNode = e.if_node
                elseNode = e.else_node
                contNode = e.continuation_Node

                conditional_task = wf.get_task(e.from_node.name)
                conditional_task.set_conditional_tasks(ifNode.name, elseNode.name, contNode.name, condition)

functions.apply_task_dependencies_and_set_order(wf, task_dependencies)

functions.set_is_main_attribute(parsed_workflows)

for wf in parsed_workflows:
            wf.print()


print("*********************************************************")
print("********** PARSE ASSEMBLED WORKFLOWS DATA ***************")
print("*********************************************************")

assembled_workflows_data = []
for component in experiment_model.component:
    if component.__class__.__name__ == 'AssembledWorkflow':
        assembled_workflow_data = {}
        assembled_workflows_data.append(assembled_workflow_data)
        assembled_workflow_data["name"] = component.name
        assembled_workflow_data["parent"] = component.parent_workflow.name
        assembled_workflow_tasks = {}
        assembled_workflow_data["tasks"] = assembled_workflow_tasks

        configurations = component.tasks

        while configurations:
            for config in component.tasks:
                assembled_workflow_task = {}
                if config.workflow:
                    assembled_workflow_task["workflow"] = config.workflow
                    assembled_workflow_tasks[config.alias.name] = assembled_workflow_task
                elif config.filename:
                    if not os.path.exists(config.filename):
                        raise exp_engine_exceptions.ImplementationFileNotFound(f"{config.filename} in task {config.alias.name}")
                    assembled_workflow_task["implementation"] = config.filename
                    assembled_workflow_tasks[config.alias.name] = assembled_workflow_task
                configurations.remove(config)
                configurations += config.subtasks

import pprint
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(assembled_workflows_data)


print("*********************************************************")
print("************ GENERATE ASSEMBLED WORKFLOWS ***************")
print("*********************************************************")

assembled_wfs = functions.generate_final_assembled_workflows(parsed_workflows, assembled_workflows_data)


for wf in assembled_wfs:
    wf.print()



print("*********************************************************")
print("************ GENERATE ASSEMBLED FLAT WORKFLOWS ***************")
print("*********************************************************")

assembled_flat_wfs = []

for wf in assembled_wfs:
    flat_wf = functions.flatten_workflows(wf)
    assembled_flat_wfs.append(flat_wf)
    flat_wf.print()

print("************")


for component in experiment_model.component:
    if component.__class__.__name__ == 'Experiment':
        # experiments.append(component.name)
        print("Experiment name: ", component.name)
        print("Experiment intent: ", component.intent_name)

        for node in component.experimentNode:
            if node.__class__.__name__ == 'Event':
                print(f"Event: {node.name}")
                print(f"    Type: {node.eventType}")
                if node.eventType == 'automated':
                    automated_events.add(node.name)
                    parsed_event = classes.AutomatedEvent(node.name,node.validation_task, node.condition)
                    parsed_automated_events.append(parsed_event)

                if node.eventType == 'manual':
                    manual_events.add(node.name)
                    parsed_event = classes.ManualEvent(node.name, node.validation_task, node.restart)
                    parsed_manual_events.append(parsed_event)

                if node.condition:
                    print(f"    Condition: {node.condition}")
                print(f"    Task: {node.validation_task}")
                if node.restart:
                    print(f"    Restart: {node.restart}")
                print()





            elif node.__class__.__name__ == 'SpaceConfig':
                print(f"  Space: {node.name}")
                print(f"    Assembled Workflow: {node.assembled_workflow.name}")
                print(f"    Vairbality : {node.strategy_name}")

                spaces.add(node.name)

                space_config_data = {
                    "name": node.name,
                    "assembled_workflow": node.assembled_workflow.name,
                    "strategy": node.strategy_name,
                    "tasks": {},
                    "VPs": [],
                    "runs":node.runs
                }

                if node.tasks:
                    for task_config in node.tasks:
                            print(f"    Task: {task_config.task.name}")
                            task_name = task_config.task.name
                            task_data = {}


                            for param_config in task_config.config:
                                print(f"        Param: {param_config.param_name} = {param_config.vp}")
                                param_name = param_config.param_name
                                param_vp = param_config.vp

                                task_data[param_name] = param_vp

                            space_config_data["tasks"][task_name] = task_data



                if node.vps:
                    for vp in node.vps:
                        if hasattr(vp.vp_values, 'values'):
                            print(f"        {vp.vp_name} = enum{vp.vp_values.values};")
                            vp_data = {
                                "name": vp.vp_name,
                                "values": vp.vp_values.values,
                                "type": "enum"
                            }
                            space_config_data["VPs"].append(vp_data)

                        elif hasattr(vp.vp_values, 'minimum') and hasattr(vp.vp_values, 'maximum'):
                            min_value = vp.vp_values.minimum
                            max_value = vp.vp_values.maximum
                            step_value = getattr(vp.vp_values, 'step', 1)
                            print(f"        {vp.vp_name} = range({min_value}, {max_value}, {step_value});")

                            vp_data = {
                                "name": vp.vp_name,
                                "min": min_value,
                                "max": max_value,
                                "step": step_value,
                                "type": "range"
                            }
                            space_config_data["VPs"].append(vp_data)


                if(node.runs!=0):
                    print(f"        Runs: ", {node.runs})

                space_configs.append(space_config_data)



            print()

        nodes = automated_events | manual_events | spaces

        if component.control:
                print("Control exists")
                print('------------------------------------------')
                print("Automated Events")
                for control in component.control:
                    for explink in control.explink:
                        if explink.__class__.__name__ == 'RegularExpLink':
                            if explink.initial_space and explink.spaces:
                                initial_space_name = explink.initial_space.name

                                if any(event in initial_space_name or any(
                                        event in space.name for space in explink.spaces) for event in automated_events):
                                    for event in automated_events:
                                        if event in initial_space_name or any(
                                                event in space.name for space in explink.spaces):
                                            print(f"Event: {event}")
                                            link = f"  Regular Link: {initial_space_name}"
                                            for space in explink.spaces:
                                                link += f" -> {space.name}"
                                                # if space.name in nodes:
                                                #     nodes.remove(space.name)
                                            print(link)

                                if initial_space_name not in automated_dict:
                                    automated_dict[initial_space_name] = {}

                                for space in explink.spaces:
                                    if space is not None:
                                        automated_dict[initial_space_name]["True"] = space.name
                                        if space.name in nodes:
                                            nodes.remove(space.name)


                        elif explink.__class__.__name__ == 'ConditionalExpLink':
                            if explink.fromspace and explink.tospace:
                                if any(event in explink.fromspace.name or event in explink.tospace.name for event in
                                       automated_events):
                                    line = f"  Conditional Link: {explink.fromspace.name}"
                                    line += f" ?-> {explink.tospace.name}"
                                    line += f"  Condition: {explink.condition}"
                                    print(line)

                                    if explink.tospace.name in nodes:
                                        nodes.remove(explink.tospace.name)

                                if explink.fromspace.name not in automated_dict:
                                    automated_dict[explink.fromspace.name] = {}

                                automated_dict[explink.fromspace.name][explink.condition] = explink.tospace.name



                        # if explink.initial_space.name in automated_events or any(space.name in automated_events for space in explink.spaces):
                            #     for event in automated_events:
                            #         if event in explink.initial_space.name or any(event in space.name for space in explink.spaces):
                            #             print()
                            #             print(f"Event: {event}")
                            #             link = f"  Regular Link: {explink.initial_space.name}"
                            #             for space in explink.spaces:
                            #                 link += f" -> {space.name}"
                            #             print(link)
                            #
                            #             automated_queue.append(explink.initial_space.name)
                            #             for space in explink.spaces:
                            #                 automated_queue.append(space.name)


                print('------------------------------------------')
                print("Manual Events")
                for control in component.control:
                    for explink in control.explink:
                        if explink.__class__.__name__ == 'RegularExpLink':
                            if explink.initial_space and explink.spaces:
                                initial_space_name = explink.initial_space.name
                                if initial_space_name == "START":
                                    initial_space_name = explink.start.name

                                if any(event in initial_space_name or any(
                                        event in space.name for space in explink.spaces) for event in manual_events):
                                    for event in manual_events:
                                        if event in initial_space_name or any(
                                                event in space.name for space in explink.spaces):
                                            print(f"Event: {event}")
                                            link = f"  Regular Link: {initial_space_name}"
                                            for space in explink.spaces:
                                                link += f" -> {space.name}"
                                            print(link)

                                if initial_space_name not in manual_dict:
                                    manual_dict[initial_space_name] = {}

                                for space in explink.spaces:
                                    if space is not None:
                                        manual_dict[initial_space_name]["True"] = space.name

                        elif explink.__class__.__name__ == 'ConditionalExpLink':
                            if explink.fromspace and explink.tospace:
                                if any(event in explink.fromspace.name or event in explink.tospace.name for event in
                                       manual_events):
                                    line = f"  Conditional Link: {explink.fromspace.name}"
                                    line += f" ?-> {explink.tospace.name}"
                                    line += f"  Condition: {explink.condition}"
                                    print(line)

                                if explink.fromspace.name not in manual_dict:
                                    manual_dict[explink.fromspace.name] = {}

                                manual_dict[explink.fromspace.name][explink.condition] = explink.tospace.name
                print('------------------------------------------')

# print("Nodes: ",nodes)
# print("Automated Events:", automated_events)
# print("Manual Events",manual_events)
# print("Spaces: ", spaces)


# print("Spaces Config: ")
# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(space_configs)
# #
# print("Automated Dictionary:")
# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(automated_dict)
#
# print("Manual Dictionary:")
# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(manual_dict)

# print("Parsed Automated Events")
# for e in parsed_automated_events:
#     print(e.name)
#     print()
#
# print("Parsed Manual Events")
# for e in parsed_manual_events:
#     print(e.name)
#     print()


#
# for space_config in space_configs:
#     pp.pprint(space_config)
#     print()

# print("\n*********************************************************")
# print("***************** RUNNING WORKFLOWS ***********************")
# print("*********************************************************")
# start_node = list(nodes)[0]
# print("Start Node: ", start_node)
# node = start_node
#
# result = execute_node(node)
# while node in automated_dict:
#     next_action = automated_dict[node]
#     node = next_action[result]
#     result = execute_node(node)
#
#



