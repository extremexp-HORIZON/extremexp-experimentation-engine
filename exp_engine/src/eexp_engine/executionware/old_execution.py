import json
import runpy
import sys
import tempfile
from pathlib import Path
from prefect import flow, task
import os

from exp_engine.src.eexp_engine.executionware.proactive_runner import (
    _create_execution_engine_mapping,
)

# -------------------------
# Constants
# -------------------------
LOCAL_HELPER_FULL_PATH = os.path.dirname(os.path.abspath(__file__))
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"

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
# Dynamic Prefect Task
# -------------------------
def create_task_from_obj(
    task_obj,
    wf_id,
    exp_id,
    mapping,
    runner_folder,
):
    impl_file = task_obj.impl_file

    @task(name=task_obj.name, log_prints=True)
    def prefect_task(prev_result_map=None):
        print(f"[{task_obj.name}] ▶ START")

        # ✅ ProActive-style shared resultMap
        resultMap = dict(prev_result_map or {})

        # -----------------------------
        # PYTHONPATH (dependent modules)
        # -----------------------------
        paths = [LOCAL_HELPER_FULL_PATH]
        for dep in getattr(task_obj, "dependent_modules", []):
            dep_path = dep.split("/**")[0] if "/**" in dep else dep
            paths.append(str(Path(runner_folder) / dep_path))
        sys.path = paths + sys.path

        # -----------------------------
        # Variables (ProActive-style)
        # -----------------------------
        variables = {
            "wf_id": wf_id,
            "exp_id": exp_id,
            "task_name": task_obj.name,
        }

        # 🔥 CRITICAL: inject previous outputs like ProActive
        for k, v in resultMap.items():
            variables[k] = v

        # ----------------------------------
        # Apply execution engine mapping
        # ----------------------------------
        task_mapping = mapping.get(task_obj.name, {})

        for target_key, source_key in task_mapping.items():
            if source_key in resultMap:
                value = resultMap[source_key]
                variables[source_key] = value   # 🔥 REQUIRED
                variables[target_key] = value
            else:
                variables[target_key] = None

        # Input files
        for f in getattr(task_obj, "input_files", []):
            key = f.name_in_task_signature
            value = normalize_path(f.path)

            # 🔥 Do NOT overwrite mapped values
            if key not in variables or variables[key] is None:
                variables[key] = value

        # Output files
        for f in getattr(task_obj, "output_files", []):
            variables[f.name_in_task_signature] = normalize_path(f.path)

        # Params
        for k, v in getattr(task_obj, "params", {}).items():
            variables[k] = v

        print(f"[{task_obj.name}] Variables:")
        print(variables)

        # -----------------------------
        # Execute task implementation
        # -----------------------------
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
            init_globals={
                "resultMap": resultMap,
            },
        )

        print(f"[{task_obj.name}] ✔ DONE")
        return resultMap

    return prefect_task


# -------------------------
# Prefect Flow
# -------------------------
def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config):
    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)
    mapping = _create_execution_engine_mapping(sorted_tasks)

    # Runtime config (compatibility only)
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

    # Create Prefect tasks
    task_funcs = {
        t.name: create_task_from_obj(
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
        results = {}

        for t in sorted_tasks:
            print(f"🧩 Running task {t.name}")
            prev_result_map = task_funcs[t.name](prev_result_map)
            results[t.name] = prev_result_map

        return results

    return dynamic_flow()
