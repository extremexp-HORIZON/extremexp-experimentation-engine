import exp_engine_functions as functions
import testcase_translation.json_to_test_case_dsl as translation
from data_abstraction_layer.data_abstraction_api import create_experiment
import json


def read_json_file (testcase_number):
    filepath= f'testcase_translation/test-case-json-files/experiment-testcase-{testcase_number}.json'
    with open(filepath, 'r') as file:
        json_data = json.load(file)

    translate_json_to_dsl(json_data,testcase_number)

def translate_json_to_dsl(json_data,testcase_number):
    dsl_output = translation.json_to_dsl(json_data)
    filepath = f'testcase_translation/test-case-dsl-files/testcase{testcase_number}.xxp'
    with open(filepath, "w") as file: file.write(dsl_output)
    parsing_test_case(filepath)

    if testcase_number=='5':
        nodes = {node['id']: node for node in json_data['nodes']}
        edges = json_data['edges']
        dsl_lines = translation.extract_and_save_composite_node_details(nodes)
        subfilepath = f'testcase_translation/test-case-dsl-files/testcase{testcase_number}-sub.xxp'
        with open(subfilepath, 'w') as file: file.write(dsl_lines)
        parsing_test_case(subfilepath)

def parsing_test_case(testcase_dsl):
    with open(testcase_dsl, 'r') as file:
        testcase_specification = file.read()

    print(f"Parsing the test case: ")
    translation.parse_dsl(testcase_specification)

    run_test_case(testcase_specification)

def run_test_case(testcase_specification):
    # print(testcase_specification)

    new_exp = {
        'name': "TestExperiment",
        'model': str(testcase_specification),
    }

    exp_id = create_experiment(new_exp)
    print(exp_id)
    functions.run_experiment(testcase_specification,exp_id)


testcase_number = input("Enter the test case number (e.g., 1, 2, etc.): ")
read_json_file(testcase_number)



