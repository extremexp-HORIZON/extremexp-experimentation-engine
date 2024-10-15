import textx
import json

def json_to_dsl(json_data):
    dsl_lines = []

    nodes = {node['id']: node for node in json_data['nodes']}
    edges = json_data['edges']

    dsl_lines.append(define_workflow(nodes, edges))
    dsl_lines.append(define_tasks(nodes))
    dsl_lines.append(task_connections(nodes, edges))
    dsl_lines.append('')
    dsl_lines.append(configure_tasks(nodes))
    dsl_lines.append(define_input_data(nodes))
    dsl_lines.append(data_connection(nodes))
    dsl_lines.append(configure_input_data(nodes))
    dsl_lines.append('}')
    dsl_lines.append(define_variant_workflows(nodes))
    dsl_lines.append(define_experiment(nodes))
    return '\n'.join(dsl_lines)


def define_workflow(nodes, edges):
    lines = ["package TESTCASE;", '\nworkflow test_case_main {']
    return '\n'.join(lines)

def define_subworkflow(nodes, edges):
    lines = ["workflow task2_main{"]
    return '\n'.join(lines)


def define_tasks(nodes):
    lines = []
    for node in nodes.values():
        if node['type'] == 'task':
            task_name = node['data']['variants'][0]['name'].replace(" ", "")
            lines.append(f'  define task {task_name};')
    lines.append('')
    return '\n'.join(lines)


def task_connections(nodes, edges):
    lines = ['  // Task CONNECTIONS\n  START']
    try:
        current_node = next(node for node in nodes.values() if node['type'] == 'start')
        end_node = next(node for node in nodes.values() if node['type'] == 'end')

        while current_node['id'] != end_node['id']:
            next_edges = [edge for edge in edges if edge['source'] == current_node['id']]
            for next_edge in next_edges:
                if next_edge is None:
                    raise ValueError(f"No outgoing edge found for node {current_node['id']}")
                next_node = nodes[next_edge['target']]
                if next_node['type'] == 'data':
                    continue
                if next_node['type'] == 'task':
                    task_name = next_node['data']['variants'][0]['name'].replace(" ", "")
                    lines.append(f' -> {task_name}')
                current_node = next_node

        lines.append(' -> END;')
    except StopIteration:
        lines.append('  // No start or end node found.')
    except ValueError as e:
        lines.append(f'  // Error: {e}')

    lines.append('')
    return ''.join(lines)


def configure_tasks(nodes):
    lines = []
    for node in nodes.values():
        if node['type'] == 'task':
            task_name = node['data']['variants'][0]['name'].replace(" ", "")
            implementation = node['data']['variants'][0]['implementationRef']

            if len(node['data']['variants']) == 1 and implementation != "":
                lines.append(f'  configure task {task_name} {{')
                lines.append(f'    implementation "testcase_task_library.{implementation}";')
                lines.append(f'    dependency "tasks/src/**";')
                lines.append(f'  }}\n')
            elif len(node['data']['variants']) == 1 and implementation == "":
                lines.append(f'  configure task {task_name} {{')
                lines.append(f'    implementation "testcase_experiment.{task_name}";')
                lines.append(f'  }}\n')
    return '\n'.join(lines)


def define_input_data(nodes):
    lines = []
    for node in nodes.values():
        if node['type'] == 'data':
            data_name = node['data']['name'].replace(" ", "")
            lines.append(f'\n  // DATA')
            lines.append(f'  define input data {data_name};')
    return '\n'.join(lines)


def configure_input_data(nodes):
    lines = []
    for node in nodes.values():
        if node['type'] == 'data':
            if 'name' in node['data'] and node['data']['name']:
                data_name = node['data']['name'].replace(" ", "")
                lines.append(f'\n  configure data {data_name} {{')

            if 'path' in node['data'] and node['data']['path'] != "":
                path = node['data']['path'].replace(" ", "")
                lines.append(f'    path "{path}";')
            lines.append('  }')
    return '\n'.join(lines)

def data_connection(nodes):
    lines = []
    for node in nodes.values():
        if node['type'] == 'data':
            lines.append(f'\n  // DATA CONNECTIONS')
            data_name = node['data']['name'].replace(" ", "")
            lines.append(f'  {data_name} --> Task1.{data_name};')
    return '\n'.join(lines)

def define_variant_workflows(nodes):
    lines = []
    for node in nodes.values():
        if node['type'] == 'task' and 'variants' in node['data']:
            if len(node['data']['variants']) > 1:
                for variant in node['data']['variants']:
                    workflow_name = variant['implementationRef']
                    lines.append(f'\nworkflow {workflow_name} from test_case_main {{')
                    lines.append(f'  configure task {variant["name"].replace(" ", "")} {{')
                    lines.append(f'    implementation "testcase_task_library.{variant["implementationRef"]}";')
                    lines.append('  }')
                    lines.append('}')
    return '\n'.join(lines)


def define_experiment(nodes):
    lines = ['\nexperiment EXP {']
    lines.append('  control {')
    lines.append('    S1;')

    lines.append('  }')

    for node in nodes.values():
        if node['type'] == 'task' and 'variants' in node['data']:
            if len(node['data']['variants']) > 1:
                flag=0
                for variant in node['data']['variants']:
                    workflow_name = variant['implementationRef']
                    lines.append(f'\n  space S{variant["variant"]} of {workflow_name} {{')
                    lines.append('    strategy gridsearch;')
                    for param in variant['parameters']:
                        param_name = param['name']
                        param_values = ', '.join(map(str, param['values']))
                        param_type = 'enum' if len(param['values']) == 1 else 'range'
                        lines.append(f'    param {param_name}_vp = {param_type}({param_values});')

                    lines.append(f'    configure task {variant["name"].replace(" ", "")} {{')
                    for param in variant['parameters']:
                        param_name = param['name']
                        lines.append(f'      param {param_name} = {param_name}_vp;')
                    lines.append('    }')
                    lines.append('  }')

            else:
                flag=1

    if flag==1:
            lines.append('''   \n   space S1 of test_case_main {
       strategy singlerun;
   } ''')

    lines.append('}')
    return '\n'.join(lines)

import json

def extract_and_save_composite_node_details(nodes):
    dsl_lines = []

    composite_nodes = [
        node for node in nodes.values()
        if isinstance(node, dict) and 'data' in node and 'variants' in node['data']
        and any(variant.get('is_composite', False) for variant in node['data']['variants'])
    ]

    if composite_nodes:
        composite_node = composite_nodes[0]
        variant = composite_node['data']['variants'][0]
        composite_node_details = {
            'id': composite_node['id'],
            'name': variant['name'],
            'description': variant.get('description', ''),
            'nodes': variant['graphical_model']['nodes'],
            'edges': variant['graphical_model']['edges']
        }

        nodes = {node['id']: node for node in composite_node_details['nodes']}
        edges = composite_node_details['edges']

        dsl_lines.append(define_subworkflow(nodes, edges))
        dsl_lines.append(define_tasks(nodes))
        dsl_lines.append(task_connections(nodes, edges))
        dsl_lines.append('')
        dsl_lines.append(configure_tasks(nodes))
        dsl_lines.append('}')

    return '\n'.join(dsl_lines)

def parse_dsl(dsl):
    workflow_metamodel = textx.metamodel_from_file('testcase_translation/workflow_grammar_new_v2.tx')
    workflow_model = workflow_metamodel.model_from_str(dsl)

    if workflow_model:
        print("Successfully Parsed!")

