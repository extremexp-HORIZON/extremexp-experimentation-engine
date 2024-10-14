import os
import textx

main_file_path = 'IDEKO-experiment1/IDEKO_main.xxp'
task_library_path = 'IDEKO-task-library'
experiment1_path = 'IDEKO-experiment1'
mltask_library_path = 'extremexp-mltask-library'

def get_task_implementation_path(implementation):
    parts = implementation.split('.')
    if parts[0] == 'IDEKO-task-library':
        return os.path.join(task_library_path, parts[1], 'task.xxp')
    elif parts[0] == 'IDEKO-experiment1':
        return os.path.join(experiment1_path, parts[1] + '.xxp')
    elif parts[0] == 'extremexp-mltask-library':
        return os.path.join(mltask_library_path, parts[1], 'task.xxp')
    else:
        return None

def read_task_file(implementation):
    task_file_path = get_task_implementation_path(implementation)
    if task_file_path and os.path.exists(task_file_path):
        with open(task_file_path, 'r') as task_file:
            return task_file.read()
    return None

def parse_workflow(dsl):
    workflow_metamodel = textx.metamodel_from_file('workflow_grammar_new.tx')
    workflow_model = workflow_metamodel.model_from_str(dsl)
    return workflow_model


def parse_task(dsl):
    workflow_metamodel = textx.metamodel_from_file('task_grammar.tx')
    workflow_model = workflow_metamodel.model_from_str(dsl)
    return workflow_model


def parse_implementation(main_dsl):
    lines = main_dsl.splitlines()

    for line in lines:
        if 'implementation' in line:
            implementation = line.split('"')[1]
            print(f"\nParsing {implementation} implementation...")
            task_content = read_task_file(implementation)
            if task_content:
                task_dsl = task_content
                print(task_dsl)
                if 'IDEKO-experiment1' in implementation:
                    workflow_model = parse_workflow(task_dsl)
                else:
                    workflow_model = parse_task(task_dsl)
                if workflow_model:
                    print("Successfully Parsed!")
            else:
                print(f"No content found for {implementation}")
        else:
            continue

with open(main_file_path, 'r') as main_file:
    main_dsl = main_file.read()
    parse_workflow(main_dsl)
    parse_implementation(main_dsl)
