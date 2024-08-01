import re
import json

def dsl_to_json(dsl):
    json_data = {
        "edges": [],
        "nodes": []
    }

    task_def_re = re.compile(r'define task (\w+);')
    task_config_re = re.compile(r'configure task (\w+)\s*\{(?:[^}]*implementation\s+"([^"]+)";)?[^}]*\}')
    data_def_re = re.compile(r'define input data (\w+);')
    data_config_re = re.compile(r'configure data (\w+)\s*\{\s*path\s*"([^"]+)"\s*\};')
    connection_re = re.compile(r'START -> (.+?) -> END;')
    variant_re = re.compile(r'workflow (\w+) from (\w+) \{\s*configure task (\w+) \{\s*implementation\s+"([^"]+)";\s*\}\s*\}')

    task_names = task_def_re.findall(dsl)
    task_configs = task_config_re.findall(dsl)
    data_names = data_def_re.findall(dsl)
    data_configs = data_config_re.findall(dsl)
    connections = connection_re.search(dsl)
    variants = variant_re.findall(dsl)

    if not connections:
        raise ValueError("Invalid DSL format: Missing connections")

    connection_sequence = connections.group(1).split(' -> ')

    if set(task_names) != set(name for name, _ in task_configs):
        raise ValueError("Invalid DSL format: Task definitions and configurations mismatch")
    if set(connection_sequence) != set(task_names):
        raise ValueError("Invalid DSL format: Task connections mismatch with task names")

    # Add start node
    start_node = {
        "data": {},
        "dragging": False,
        "height": 36,
        "id": "start-node",
        "position": {"x": 135, "y": 0},
        "positionAbsolute": {"x": 100, "y": 0},
        "selected": False,
        "type": "start",
        "width": 31
    }
    json_data["nodes"].append(start_node)

    # Map task implementations
    task_implementation_map = {}
    for name, impl in task_configs:
        impl_parts = impl.split('.')
        if len(impl_parts) > 1:
            task_implementation_map[name] = impl_parts[1]
        else:
            task_implementation_map[name] = impl

    # Add task variants
    task_variant_map = {}
    for variant_name, main_workflow, task, implementation in variants:
        impl_parts = implementation.split('.')
        implementation_ref = impl_parts[1] if len(impl_parts) > 1 else ""
        if task not in task_variant_map:
            task_variant_map[task] = []
        task_variant_map[task].append({
            "description": "no description",
            "graphical_model": {
                "edges": [],
                "nodes": []
            },
            "id_task": f"{variant_name}-{task}",
            "implementationRef": implementation_ref,
            "isAbstract": False,
            "is_composite": False,
            "name": task,
            "parameters": [],
            "variant": variant_name
        })

    # Add tasks
    y_pos = 100
    y_increment = 150

    for task in connection_sequence:
        implementation = task_implementation_map.get(task, "")
        is_abstract = not bool(implementation)
        variants_list = task_variant_map.get(task, [])
        if not variants_list:
            variants_list.append({
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
            })

        node = {
            "data": {
                "currentVariant": variants_list[0]["id_task"],
                "variants": variants_list
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

    # Add end node
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

    # Add edges for tasks
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

    end_edge = {
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
    json_data["edges"].append(end_edge)

    # Add data nodes
    data_path_map = {name: path for name, path in data_configs}
    x_pos_data = -200
    y_pos_data = 100

    for data in data_names:
        path = data_path_map.get(data, "")
        node = {
            "data": {
                "name": data,
                "path": path
            },
            "dragging": False,
            "height": 57,
            "id": f"data-{data}",
            "position": {"x": x_pos_data, "y": y_pos_data},
            "positionAbsolute": {"x": x_pos_data, "y": y_pos_data},
            "selected": False,
            "type": "data",
            "width": 122
        }
        json_data["nodes"].append(node)

    # Add edges for data connections
    data_connection_re = re.compile(r'(\w+) --> (\w+)\.(\w+);')
    data_connections = data_connection_re.findall(dsl)

    for data_src, task, data_tgt in data_connections:
        edge = {
            "animated": True,
            "data": {},
            "id": f"edge-{data_src}-task-{task}-{data_tgt}",
            "markerEnd": {
                "color": "#000",
                "height": 20,
                "type": "arrow",
                "width": 20
            },
            "source": f"data-{data_src}",
            "sourceHandle": None,
            "style": {"stroke": "#000", "strokeWidth": 1.5},
            "target": f"task-{task}",
            "targetHandle": None,
            "type": "dataflow"
        }
        json_data["edges"].append(edge)

    return json.dumps(json_data, indent=2)

def export_json_to_file(json_data, file_path):
    try:
        with open(file_path, 'w') as file:
            file.write(json_data)
        print(f"JSON data successfully exported to '{file_path}'.")
    except Exception as e:
        print(f"Error occurred while exporting JSON data to '{file_path}': {e}")



with open('IDEKO_main.xxp', 'r') as file:
    dsl = file.read()

print(dsl)

json_output = dsl_to_json(dsl)
print(json_output)

output_file_path = "exported-experiment.json"
export_json_to_file(json_output, output_file_path)
