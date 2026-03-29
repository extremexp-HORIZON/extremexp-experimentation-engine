import json
import runpy
import sys
import tempfile
from pathlib import Path
from prefect import flow, task
import os
from functools import partial

from exp_engine.src.eexp_engine.executionware.kubeflow_utils import _create_exp_engine_metadata
# from exp_engine.src.eexp_engine.executionware.proactive_runner import (
#     _create_execution_engine_mapping,
# )

from exp_engine.src.eexp_engine.executionware.prefect_utils import (
    _create_execution_engine_mapping,
)


# -------------------------
# Constants
# -------------------------
LOCAL_HELPER_FULL_PATH = os.path.dirname(os.path.abspath(__file__))
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"
# -------------------------
# Helpers
# -------------------------
def normalize_path(p):
    return str(Path(p).as_posix()) if p else None


def rewrite_resultmap(lines):
    """
    Replicates ProActive resultMap.put behavior
    """
    out = []
    for l in lines:
        if "resultMap.put" in l:
            out.append(l.replace("resultMap.put", "resultMap.__setitem__"))
        else:
            out.append(l)
    return out

# -------------------------
# Top-level Prefect task
# -------------------------
def build_prefect_task(task_obj, wf_id, exp_id, mapping, runner_folder):
    impl_file = task_obj.impl_file

    @task(name=task_obj.name, log_prints=True)
    def prefect_task(prev_result_map=None):
        print(f"[{task_obj.name}] ▶ START")
        resultMap = dict(prev_result_map or {})

        # Set PYTHONPATH for dependent modules
        paths = [LOCAL_HELPER_FULL_PATH]
        for dep in getattr(task_obj, "dependent_modules", []):
            dep_path = dep.split("/**")[0] if "/**" in dep else dep
            paths.append(str(Path(runner_folder) / dep_path))
        sys.path = paths + sys.path

        # Variables
        variables = {
            "wf_id": wf_id,
            "exp_id": exp_id,
            "task_name": task_obj.name,
            "exp_engine_metadata": mapping.get("exp_engine_metadata"),
            "mapping": mapping.get("mapping"),
        }
        for k, v in resultMap.items():
            variables[k] = v

        # Apply execution engine mapping
        task_mapping = mapping.get(task_obj.name, {})
        for target_key, source_key in task_mapping.items():
            if isinstance(source_key, dict):
                source_key = source_key.get("file_name")

            value = resultMap.get(source_key)
            variables[target_key] = value

            if source_key in resultMap:
                variables[source_key] = resultMap[source_key]

        # Input files
        for f in getattr(task_obj, "input_files", []):
            key = f.name_in_task_signature
            value = normalize_path(f.path)
            if key not in variables or variables[key] is None:
                variables[key] = value

        # Output files
        for f in getattr(task_obj, "output_files", []):
            variables[f.name_in_task_signature] = normalize_path(f.path)

        # Params
        for k, v in getattr(task_obj, "params", {}).items():
            variables[k] = v

        print(f"[{task_obj.name}] Variables:")
        print("banaan1234")
        print(variables)

        # Execute task implementation
        with open(impl_file, "r") as f:
            lines = f.readlines()

        script_lines = (
            ["import local_helper as ph\n"]
            + [f"variables = {variables}\n"]
            + rewrite_resultmap(lines)
            + ["\nph.save_result(resultMap)\n"]
        )

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.writelines(script_lines)
            tmp_path = tmp.name

        runpy.run_path(
            tmp_path,
            run_name="__main__",
            init_globals={"resultMap": resultMap},
        )

        print(f"[{task_obj.name}] ✔ DONE")
        return resultMap

    return prefect_task

# -------------------------
# Prefect flow
# -------------------------
def to_dict(obj):
    # basic types
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj

    # lists / tuples
    if isinstance(obj, (list, tuple, set)):
        return [to_dict(x) for x in obj]

    # dicts
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}

    # objects with __dict__
    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in vars(obj).items()}

    # fallback (e.g. external objects)
    return str(obj)

def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config):

    print("chef123")
    import pprint
    pprint.pprint(to_dict(w))
    print("chef1234")
    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)

    exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)
    exp_engine_runtime_config = {
        "exp_engine_metadata": exp_engine_metadata,
    }

    mapping = _create_execution_engine_mapping(sorted_tasks, exp_engine_runtime_config)

    if not os.path.exists("intermediate_files"):
        os.makedirs("intermediate_files")
    with open(EXECUTION_ENGINE_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)
    with open(VARIABLES, 'w') as f:
        json.dump({}, f)
    with open(RESULT, 'w') as f:
        json.dump({}, f)
    runtime_config_path = f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"
    with open(runtime_config_path, "w") as f:
        json.dump(
            {
                "EXECUTIONWARE": "LOCAL",
                "mapping": mapping,
                "exp_engine_metadata": {
                    "exp_id": exp_id,
                    "exp_name": exp_name,
                    "wf_id": wf_id,
                },
            },
            f,
        )

    # Build top-level tasks
    task_funcs = {
        t.name: build_prefect_task(
            task_obj=t,
            wf_id=wf_id,
            exp_id=exp_id,
            mapping=mapping,
            runner_folder=runner_folder,
        )
        for t in sorted_tasks
    }

    @flow(name=f"{w.name}_{wf_id}", log_prints=True)
    def dynamic_flow():
        prev_result_map = None
        results_futures = {}

        # Schedule each task as a Prefect future
        for t in sorted_tasks:
            print(f"🧩 Scheduling task {t.name}")
            future = task_funcs[t.name].submit(prev_result_map)
            results_futures[t.name] = future
            prev_result_map = future  # pass future downstream

        # Resolve all futures
        results = {k: v.result() for k, v in results_futures.items()}
        return results

    return dynamic_flow()
