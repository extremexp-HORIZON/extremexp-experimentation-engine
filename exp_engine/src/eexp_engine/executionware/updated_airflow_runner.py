import json
import os
import pprint
from pathlib import Path

from exp_engine.src.eexp_engine.executionware.kubeflow_utils import _create_exp_engine_metadata
from exp_engine.src.eexp_engine.executionware.prefect_utils import (
    _create_execution_engine_mapping,
)


LOCAL_HELPER_FULL_PATH = os.path.dirname(os.path.abspath(__file__))
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"


def normalize_path(p):
    return str(Path(p).as_posix()) if p else None


def to_dict(obj):
    """Convert workflow/task objects into JSON/Python-literal-safe structures."""
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj

    if isinstance(obj, Path):
        return normalize_path(obj)

    if isinstance(obj, (list, tuple, set)):
        return [to_dict(x) for x in obj]

    if isinstance(obj, dict):
        return {str(k): to_dict(v) for k, v in obj.items()}

    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in vars(obj).items()}

    return str(obj)


def _dep_name(dep):
    """Dependency entries can be task names or task-like objects."""
    return str(getattr(dep, "name", dep))


def _serialize_file_ref(file_obj):
    return {
        "name_in_task_signature": getattr(file_obj, "name_in_task_signature", None),
        "path": normalize_path(getattr(file_obj, "path", None)),
    }


def _serialize_task(task_obj):
    return {
        "name": str(task_obj.name),
        "impl_file": normalize_path(task_obj.impl_file),
        "params": to_dict(getattr(task_obj, "params", {})),
        "dependent_modules": to_dict(getattr(task_obj, "dependent_modules", [])),
        "dependencies": [_dep_name(d) for d in getattr(task_obj, "dependencies", [])],
        "prototypical_inputs": to_dict(getattr(task_obj, "prototypical_inputs", [])),
        "prototypical_outputs": to_dict(getattr(task_obj, "prototypical_outputs", [])),
        "input_files": [_serialize_file_ref(f) for f in getattr(task_obj, "input_files", [])],
        "output_files": [_serialize_file_ref(f) for f in getattr(task_obj, "output_files", [])],
    }


def _py_literal(value):
    """Pretty Python literal for generated DAG source. Avoids JSON null/true/false issues."""
    return pprint.pformat(value, width=120, sort_dicts=False)


DAG_TEMPLATE = r'''
import os
import sys
import runpy
import tempfile
from pathlib import Path
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


LOCAL_HELPER_FULL_PATH = {local_helper_path!r}


def normalize_path(p):
    return str(Path(p).as_posix()) if p else None


def rewrite_resultmap(lines):
    """Replicates ProActive resultMap.put behavior."""
    out = []
    for line in lines:
        if "resultMap.put" in line:
            out.append(line.replace("resultMap.put", "resultMap.__setitem__"))
        else:
            out.append(line)
    return out


def execute_task_logic(task_obj_data, wf_id, exp_id, mapping, runner_folder, **context):
    task_name = task_obj_data.get("name", "unknown_task")
    print(f"[{task_name}] ▶ START")

    ti = context["ti"]

    # Merge all dependency outputs, matching the Prefect runner behavior.
    resultMap = {}
    for dep_task_id in task_obj_data.get("dependencies", []):
        pulled_val = ti.xcom_pull(task_ids=dep_task_id)
        if isinstance(pulled_val, dict):
            resultMap.update(pulled_val)
        elif pulled_val is not None:
            print(f"[{task_name}] ignored non-dict XCom from {dep_task_id}: {type(pulled_val).__name__}")

    # Make local_helper and dependent modules importable for the task implementation.
    paths = [LOCAL_HELPER_FULL_PATH]
    for dep in task_obj_data.get("dependent_modules", []):
        dep_path = dep.split("/**")[0] if isinstance(dep, str) and "/**" in dep else dep
        paths.append(str(Path(runner_folder) / dep_path))
    sys.path = paths + sys.path

    variables = {
        "wf_id": wf_id,
        "exp_id": exp_id,
        "task_name": task_name,
        "exp_engine_metadata": mapping.get("exp_engine_metadata"),
        "mapping": mapping.get("mapping"),
    }
    variables.update(resultMap)

    # Apply execution engine mapping exactly like the Prefect runner.
    engine_mapping = mapping.get("mapping", mapping)
    task_mapping = engine_mapping.get(task_name, {})
    inputs_mapping = task_mapping.get("inputs", {})

    for target_key, meta in inputs_mapping.items():
        file_type = meta.get("file_type")

        if file_type == "local":
            variables[target_key] = normalize_path(meta.get("file_path"))

        elif file_type == "intermediate":
            source_file_name = meta.get("file_name")
            source_task = meta.get("source_task")
            value = resultMap.get(source_file_name)

            if value is None and source_task:
                value = resultMap.get(source_task, {}).get(source_file_name)

            variables[target_key] = value
            print(
                f"[{task_name}] mapped intermediate "
                f"'{source_file_name}' -> '{target_key}' with value '{value}'"
            )

    for input_name in task_obj_data.get("prototypical_inputs", []):
        if input_name not in variables or variables.get(input_name) is None:
            variables[input_name] = resultMap.get(input_name)

    for file_ref in task_obj_data.get("input_files", []):
        key = file_ref.get("name_in_task_signature")
        value = normalize_path(file_ref.get("path"))
        if key and (key not in variables or variables.get(key) is None):
            variables[key] = value

    for file_ref in task_obj_data.get("output_files", []):
        key = file_ref.get("name_in_task_signature")
        if key:
            variables[key] = normalize_path(file_ref.get("path"))

    for key, value in task_obj_data.get("params", {}).items():
        variables[key] = value

    print(f"[{task_name}] Variables:")
    print(variables)

    impl_file = task_obj_data.get("impl_file")
    with open(impl_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    script_lines = (
        ["import local_helper as ph\n"]
        + [f"variables = {variables!r}\n"]
        + rewrite_resultmap(lines)
        + ["\nph.save_result(resultMap)\n"]
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.writelines(script_lines)
        tmp_path = tmp.name

    try:
        globals_after_run = runpy.run_path(
            tmp_path,
            run_name="__main__",
            init_globals={"resultMap": resultMap},
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    executed_variables = globals_after_run.get("variables", {})

    # Capture declared logical/prototypical outputs written into variables.
    for output_name in task_obj_data.get("prototypical_outputs", []):
        if output_name in resultMap and resultMap[output_name] is not None:
            print(
                f"[{task_name}] kept prototypical output "
                f"'{output_name}' from resultMap: {resultMap[output_name]}"
            )
        elif output_name in executed_variables and executed_variables[output_name] is not None:
            resultMap[output_name] = executed_variables[output_name]
            print(
                f"[{task_name}] captured prototypical output "
                f"'{output_name}' from variables into resultMap"
            )

    print(f"[{task_name}] ✔ DONE")
    return resultMap


with DAG(
    dag_id={dag_id!r},
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    tasks_operators = {}
{task_definitions_block}

{dependencies_block}
'''


def create_airflow_dag(w, exp_id, exp_name, wf_id, runner_folder, config=None, output_dir=None):
    """
    Generate an Airflow DAG that executes the same task logic/data propagation as the Prefect runner.

    The generated DAG uses XCom to pass each task's resultMap to downstream tasks.
    For tasks with multiple dependencies, result maps are merged in dependency order.
    """
    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)

    exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)
    exp_engine_runtime_config = {
        "exp_engine_metadata": exp_engine_metadata,
    }
    mapping = _create_execution_engine_mapping(sorted_tasks, exp_engine_runtime_config)

    os.makedirs("intermediate_files", exist_ok=True)

    with open(EXECUTION_ENGINE_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f)
    with open(VARIABLES, "w", encoding="utf-8") as f:
        json.dump({}, f)
    with open(RESULT, "w", encoding="utf-8") as f:
        json.dump({}, f)

    runtime_config_path = f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"
    with open(runtime_config_path, "w", encoding="utf-8") as f:
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

    serialized_tasks = [_serialize_task(t) for t in sorted_tasks]

    task_defs = []
    for t_data in serialized_tasks:
        task_defs.append(
            f"""
    tasks_operators[{t_data['name']!r}] = PythonOperator(
        task_id={t_data['name']!r},
        python_callable=execute_task_logic,
        op_kwargs={{
            'task_obj_data': {_py_literal(t_data)},
            'wf_id': {wf_id!r},
            'exp_id': {exp_id!r},
            'mapping': {_py_literal(mapping)},
            'runner_folder': {str(runner_folder)!r},
        }},
    )"""
        )

    deps = []
    task_names = {t["name"] for t in serialized_tasks}
    for t_data in serialized_tasks:
        current = t_data["name"]
        for dep in t_data.get("dependencies", []):
            if dep not in task_names:
                raise ValueError(f"Task {current!r} depends on unknown task {dep!r}")
            deps.append(f"    tasks_operators[{dep!r}] >> tasks_operators[{current!r}]")

    full_dag_code = DAG_TEMPLATE.format(
        local_helper_path=LOCAL_HELPER_FULL_PATH,
        dag_id=f"{w.name}_{wf_id}",
        task_definitions_block="\n".join(task_defs),
        dependencies_block="\n".join(deps) if deps else "    # No task dependencies declared.",
    )

    target_dir = output_dir or os.getcwd()
    output_path = os.path.join(target_dir, f"airflow_dag_{wf_id}.py")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_dag_code)

    return output_path


# Compatibility wrapper for the execution engine.
def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config=None):
    """
    Generate the Airflow DAG and return a dict-shaped payload.

    The experiment execution wrapper appears to expect subprocess results to be
    dict-like and to contain a `task_name` key. Returning only the DAG path can
    therefore cause a KeyError: 'task_name' even though DAG generation succeeded.
    """
    print("USING UPDATED AIRFLOW RUNNER V2")

    dag_path = create_airflow_dag(
        w=w,
        exp_id=exp_id,
        exp_name=exp_name,
        wf_id=wf_id,
        runner_folder=runner_folder,
        config=config,
    )

    print("AIRFLOW RUNNER RETURNING:")
    print({
        "task_name": getattr(w, "name", wf_id),
        "result": {},
        "dag_path": dag_path,
    })

    return {
        "task_name": getattr(w, "name", wf_id),
        "wf_id": wf_id,
        "exp_id": exp_id,
        "dag_path": dag_path,
        "result": {
            "dag_path": dag_path,
            "dag_id": f"{getattr(w, 'name', 'workflow')}_{wf_id}",
        },
    }
