import json
import os
import sys
import tempfile
import runpy
from pathlib import Path
from datetime import datetime

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

from exp_engine.src.eexp_engine.executionware.proactive_runner import (
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
# Airflow task callable
# -------------------------
def airflow_task_callable(
    task_obj,
    wf_id,
    exp_id,
    mapping,
    runner_folder,
    **context,
):
    ti = context["ti"]

    print(f"[{task_obj.name}] ▶ START")

    # Pull previous resultMap
    prev_result_map = {}
    if context["params"].get("upstream_task"):
        prev_result_map = ti.xcom_pull(
            task_ids=context["params"]["upstream_tasfk"]
        ) or {}

    resultMap = dict(prev_result_map)

    # PYTHONPATH
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
    }
    variables.update(resultMap)

    # Execution engine mapping
    task_mapping = mapping.get(task_obj.name, {})
    for target_key, source_key in task_mapping.items():
        value = resultMap.get(source_key)
        variables[target_key] = value
        if source_key in resultMap:
            variables[source_key] = resultMap[source_key]

    # Input files
    for f in getattr(task_obj, "input_files", []):
        key = f.name_in_task_signature
        if key not in variables:
            variables[key] = normalize_path(f.path)

    # Output files
    for f in getattr(task_obj, "output_files", []):
        variables[f.name_in_task_signature] = normalize_path(f.path)

    # Params
    for k, v in getattr(task_obj, "params", {}).items():
        variables[k] = v

    print(f"[{task_obj.name}] Variables:")
    print(variables)

    # Execute implementation
    with open(task_obj.impl_file, "r") as f:
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

    # Push resultMap to XCom
    ti.xcom_push(key="result", value=resultMap)
    return resultMap


# -------------------------
# DAG factory (Prefect execute_wf equivalent)
# -------------------------
def create_airflow_dag(w, exp_id, exp_name, wf_id, runner_folder):

    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)
    mapping = _create_execution_engine_mapping(sorted_tasks)

    os.makedirs("intermediate_files", exist_ok=True)
    with open(EXECUTION_ENGINE_MAPPING_FILE, "w") as f:
        json.dump(mapping, f)

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

    dag = DAG(
        dag_id=f"{w.name}_{wf_id}",
        start_date=datetime(2024, 1, 1),
        schedule_interval=None,
        catchup=False,
    )

    airflow_tasks = {}

    for i, t in enumerate(sorted_tasks):
        airflow_tasks[t.name] = PythonOperator(
            task_id=t.name,
            python_callable=airflow_task_callable,
            op_kwargs={
                "task_obj": t,
                "wf_id": wf_id,
                "exp_id": exp_id,
                "mapping": mapping,
                "runner_folder": runner_folder,
            },
            params={
                "upstream_task": sorted_tasks[i - 1].name if i > 0 else None
            },
            dag=dag,
        )

    # Linear chaining (same as Prefect future passing)
    for i in range(len(sorted_tasks) - 1):
        airflow_tasks[sorted_tasks[i].name] >> airflow_tasks[sorted_tasks[i + 1].name]

    return dag
