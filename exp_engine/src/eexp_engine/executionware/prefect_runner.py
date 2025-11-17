import json
import runpy
from prefect import flow, task
import sys
from pathlib import Path
import os
import tempfile
from exp_engine.src.eexp_engine.executionware.proactive_runner import _create_execution_engine_mapping

LOCAL_HELPER_FULL_PATH = os.path.dirname(os.path.abspath(__file__))
EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"

def find_and_replace_ResultMapPut(lines):
    new_lines = []
    for l in lines:
        if "resultMap.put" in l:
            new_line = l.replace("resultMap.put", "resultMap.__setitem__")
            new_lines.append(new_line)
        else:
            new_lines.append(l)
    return new_lines

# -------------------------
# Utility to normalize paths
# -------------------------
def normalize_path(p):
    if not p:
        return None
    return str(Path(p).as_posix())


# -------------------------
# Create dynamic Prefect task
# -------------------------
def create_task_from_obj(task_obj, sorted_tasks, index, wf_id, resultMap, runner_folder, local_helper_full_path):
    impl_file = task_obj.impl_file
    output_file_path = (
        task_obj.output_files[0].path
        if getattr(task_obj, "output_files", None)
           and len(task_obj.output_files) > 0
        else None
    )

    @task(name=task_obj.name)
    def dynamic_task(input_path: str = None):
        print(f"[{task_obj.name}] ▶ Starting execution")

        # -----------------------------
        # 1. Prepare PYTHONPATH dynamically
        # -----------------------------
        paths = [local_helper_full_path]
        for dep in getattr(task_obj, "dependent_modules", []):
            dep_path = dep.split("/**")[0] if "/**" in dep else dep
            paths.append(str(Path(runner_folder) / dep_path))
        # Prepend to sys.path
        sys.path = paths + sys.path

        # -----------------------------
        # 2. Prepare variables
        # -----------------------------
        variables = {
            "PREVIOUS_PROCESS_ID": sorted_tasks[index - 1].name if index > 0 else None,
            "task_name": task_obj.name,
            "workflow_id": wf_id,
        }

        # Add input/output file paths
        for input_file in task_obj.input_files:
            path = getattr(input_file, "path", None)
            variables[f"{input_file.name_in_task_signature}"] = str(path) if path else None
        for output_file in task_obj.output_files:
            path = getattr(output_file, "path", None)
            variables[f"{output_file.name_in_task_signature}"] = str(path) if path else None

        # Add task params
        if hasattr(task_obj, "params") and task_obj.params:
            for k, v in task_obj.params.items():
                variables[k] = v

        print("peer4321")
        print(variables)
        if impl_file and Path(impl_file).exists():
            try:
                print(f"[{task_obj.name}] Running {impl_file} as a script")

                with open(impl_file, "r") as fp:
                    original_lines = fp.readlines()

                first_line = ["import local_helper as ph\n"]
                second_line = [f"variables = {variables}\n"]
                third_line = [f"resultMap = {resultMap}\n"]
                last_line = ["\nph.save_result(resultMap)"]

                # Apply your custom transformation function if needed
                filelines = first_line + second_line + third_line + find_and_replace_ResultMapPut(original_lines[2:]) + last_line

                # Write to a temporary file
                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmp_fp:
                    tmp_fp.writelines(filelines)
                    tmp_script_path = tmp_fp.name

                # Run the file as if "python task.py" was called
                # Provide input_path and output_file_path as globals
                runpy.run_path(
                    tmp_script_path,
                    run_name="__main__",
                    init_globals={
                        "input_path": input_path,
                        "output_path": output_file_path,
                    },
                )

                print(f"[{task_obj.name}] Script executed successfully")

            except Exception as e:
                print(f"[{task_obj.name}] ❌ Error executing module: {e}")

        else:
            print(f"[{task_obj.name}] ❌ Invalid or missing impl_file: {impl_file}")

        # Return output path if it exists
        if output_file_path and Path(output_file_path).exists():
            print(f"[{task_obj.name}] ✅ Output ready at: {output_file_path}")
            return output_file_path
        else:
            print(f"[{task_obj.name}] ⚠️ No output file produced")
            return None

    return dynamic_task


# -------------------------
# Build and run Prefect Flow
# -------------------------
def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config):
    from pprint import pprint

    def recursive_to_dict(obj):
        if isinstance(obj, dict):
            return {k: recursive_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [recursive_to_dict(i) for i in obj]
        elif hasattr(obj, "__dict__"):
            return {k: recursive_to_dict(v) for k, v in obj.__dict__.items()}
        else:
            return obj

    # Convert Workflow object to a nested dict
    workflow_dict = recursive_to_dict(w)

    # Pretty print everything
    pprint(workflow_dict, width=120)

    print("⚙️ Building Prefect flow dynamically...")

    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)
    mapping = _create_execution_engine_mapping(sorted_tasks)

    with open(EXECUTION_ENGINE_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)
    with open(VARIABLES, 'w') as f:
        json.dump({}, f)
    with open(RESULT, 'w') as f:
        json.dump({}, f)

    # Create Prefect tasks dynamically
    task_funcs = {}
    for index, t in enumerate(sorted_tasks):
        resultMap = json.loads(open(RESULT, 'r').read())
        task_funcs[t.name] = create_task_from_obj(
            task_obj=t,
            sorted_tasks=sorted_tasks,
            index=index,
            wf_id=wf_id,
            resultMap=resultMap,
            runner_folder=runner_folder,
            local_helper_full_path=LOCAL_HELPER_FULL_PATH,
        )

    @flow(name=f"{w.name}_{wf_id}", log_prints=True)
    def dynamic_flow():
        results = {}

        for t in w.tasks:
            deps = getattr(t, "dependencies", [])

            # Find dependency output if any
            dep_result = results[deps[-1]] if deps else None

            # Determine input file
            input_file = None
            if dep_result:
                input_file = dep_result
            elif getattr(t, "input_files", None) and len(t.input_files) > 0:
                input_file = normalize_path(t.input_files[0].path)

            # Run Prefect task
            print(f"🧩 Executing task: {t.name}")
            results[t.name] = task_funcs[t.name].submit(input_file)

        return results

    deployment = dynamic_flow.deploy(
        name=f"{w.name}_{wf_id}-deployment",
        work_pool_name="my-docker-pool",
        parameters={},  # optional
        image="python:3.10-slim",
        tags=["dynamic", exp_name],
        push=False,
    )

    return deployment


