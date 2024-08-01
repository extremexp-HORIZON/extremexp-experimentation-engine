import re
import json


def dsl_to_json(dsl):
    json_data = {
        "edges": [],
        "nodes": []
    }

    task_def_re = re.compile(r'define task (\w+);')
    task_config_re = re.compile(r'configure task (\w+)\s*\{(?:[^}]*implementation\s+"([^"]+)";)?[^}]*\}')
    connection_re = re.compile(r'START -> (.+) -> END;')

    task_names = task_def_re.findall(dsl)
    task_configs = task_config_re.findall(dsl)
    connections = connection_re.search(dsl)

    if not connections:
        raise ValueError("Invalid DSL format: Missing connections")

    connection_sequence = connections.group(1).split(' -> ')

    if set(task_names) != set(name for name, _ in task_configs):
        raise ValueError("Invalid DSL format: Task definitions and configurations mismatch")
    if set(connection_sequence) != set(task_names):
        raise ValueError("Invalid DSL format: Task connections mismatch with task names")

    start_node = {
        "data": {},
        "dragging": False,
        "height": 36,
        "id": "start-node",
        "position": {"x": 135, "y": 0},
        "positionAbsolute": {"x": 100, "y": 0},
        "selected": True,
        "type": "start",
        "width": 31
    }
    json_data["nodes"].append(start_node)

    x_pos = 100
    y_pos = 100
    y_increment = 150

    task_implementation_map = {name: impl for name, impl in task_configs}

    for task in connection_sequence:
        implementation = task_implementation_map.get(task, "")
        is_abstract = not bool(implementation)
        node = {
            "data": {
                "currentVariant": f"variant-1-{task}",
                "variants": [
                    {
                        "description": "no description",
                        "graphical_model": {
                            "edges": [],
                            "nodes": []
                        },
                        "id_task": f"variant-1-{task}",
                        "implementationRef": implementation,
                        "isAbstract": is_abstract,
                        "is_composite": False,
                        "name": task,
                        "parameters": [],
                        "variant": 1
                    }
                ]
            },
            "dragging": False,
            "height": 44,
            "id": f"task-{task}",
            "position": {"x": 100, "y": y_pos},
            "positionAbsolute": {"x": 100, "y": y_pos},
            "selected": False,
            "type": "task",
            "width": 102
        }
        json_data["nodes"].append(node)
        y_pos += y_increment

    end_node = {
        "data": {},
        "dragging": False,
        "height": 37,
        "id": "end-node",
        "position": {"x": 135, "y": y_pos},
        "positionAbsolute": {"x": 120, "y": y_pos},
        "selected": False,
        "type": "end",
        "width": 32
    }
    json_data["nodes"].append(end_node)

    prev_node_id = "start-node"
    for task in connection_sequence:
        task_node_id = f"task-{task}"
        edge = {
            "data": {},
            "id": f"edge-{prev_node_id}-{task_node_id}",
            "markerEnd": {
                "color": "#000",
                "height": 20,
                "type": "arrow",
                "width": 20
            },
            "source": prev_node_id,
            "sourceHandle": None,
            "style": {"stroke": "#000", "strokeWidth": 1.5},
            "target": task_node_id,
            "targetHandle": "t-top",
            "type": "regular"
        }
        json_data["edges"].append(edge)
        prev_node_id = task_node_id

    edge_to_end = {
        "data": {},
        "id": f"edge-{prev_node_id}-end-node",
        "markerEnd": {
            "color": "#000",
            "height": 20,
            "type": "arrow",
            "width": 20
        },
        "source": prev_node_id,
        "sourceHandle": None,
        "style": {"stroke": "#000", "strokeWidth": 1.5},
        "target": "end-node",
        "targetHandle": None,
        "type": "regular"
    }
    json_data["edges"].append(edge_to_end)

    return json.dumps(json_data, indent=2)


def export_json_to_file(json_data, file_path):
    try:
        with open(file_path, 'w') as file:
            file.write(json_data)
        print(f"JSON data successfully exported to '{file_path}'.")
    except Exception as e:
        print(f"Error occurred while exporting JSON data to '{file_path}': {e}")



with open('example.dsl', 'r') as file:
    dsl = file.read()

json_output = dsl_to_json(dsl)
print(json_output)

output_file_path = "complex-json.json"
export_json_to_file(json_output, output_file_path)


# dsl = """
# workflow simple {
#     define task ReadData;
#     define task AddPadding;
#     define task SplitData;
#     define task TrainModel;
#
#     configure task ReadData{}
#     configure task AddPadding{}
#     configure task SplitData{}
#     configure task TrainModel{}
#
#     START -> ReadData -> AddPadding -> SplitData -> TrainModel -> END;
# }
# """
