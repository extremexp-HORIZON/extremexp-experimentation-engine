import os
import sys
import pickle

def save_dataset_local(variables, resultMap, key, value):
    value_size = sys.getsizeof(value)
    print(f"Saving output data of size {value_size} with key {key}")
    if key in variables:
        output_file_path = variables.get(key)
        folder_path = output_file_path.rsplit("/", 1)[0]
        _create_folder(folder_path)
        with open(output_file_path, "wb") as outfile:
            outfile.write(value)
    else:
        workflow_id = variables.get("exp_engine_metadata").get("wf_id")
        task_id = variables.get("task_name")
        print(workflow_id, task_id)
        task_folder = os.path.join("/shared", workflow_id, task_id)
        os.makedirs(task_folder, exist_ok=True)
        output_file_path = os.path.join(task_folder, key)
        with open(output_file_path, "wb") as outfile:
            pickle.dump(value, outfile)
        print(f"Saved output data to {output_file_path}")
    if resultMap is not None:
        print(f"Adding file {output_file_path} path for file {key} to job results")
        resultMap[key] = output_file_path


def load_dataset_local(variables, key):
    print(f"Loading input data with key {key}")
    
    if key in variables:
        # External file path
        input_filename = variables.get(key)
        return load_dataset_by_path(input_filename)
    else:
        # Intermediate file - use mapping to find source task
        workflow_id = variables.get("exp_engine_metadata").get("wf_id")
        current_task_name = variables.get("task_name")
        mapping = variables.get("mapping", {})
        # Look up the source task from mapping
        if current_task_name in mapping:
            if key in mapping[current_task_name]:
                mapping_info = mapping[current_task_name][key]
                source_task = mapping_info["source_task"]
                output_name = mapping_info["file_name"]
                
                # Build path using source task name
                task_folder = os.path.join("/shared", workflow_id, source_task)
                input_filename = os.path.join(task_folder, output_name)
                return load_pickled_dataset_by_path(input_filename)
        
        raise Exception(f"Could not resolve input '{key}' for task '{current_task_name}'")
    
def load_pickled_dataset_by_path(file_path):
    with open(file_path, "rb") as f:
        file_contents = pickle.load(f)
    return file_contents