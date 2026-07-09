import json
import os
import re
import runpy
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Airflow 3.x import path
try:
    from airflow.sdk import dag, task, get_current_context
except ImportError:
    # Airflow 2.x fallback
    from airflow.decorators import dag, task
    from airflow.operators.python import get_current_context

from exp_engine.src.eexp_engine.executionware.kubeflow_utils import (
    _create_exp_engine_metadata,
)

# Reuse the existing helper because this mapping logic is not Prefect-specific.
# If you later rename/move it, only change this import.
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
    Replicates ProActive resultMap.put behavior.
    """
    out = []
    for line in lines:
        if "resultMap.put" in line:
            out.append(line.replace("resultMap.put", "resultMap.__setitem__"))
        else:
            out.append(line)
    return out


def to_dict(obj):
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj

    if isinstance(obj, (list, tuple, set)):
        return [to_dict(x) for x in obj]

    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}

    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in vars(obj).items()}

    return str(obj)


def safe_airflow_id(value, fallback="task"):
    """
    Airflow task_id / dag_id values should be simple and stable.
    """
    value = str(value or fallback)
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    value = value.strip("._-")
    return value or fallback


def get_dep_name(dep):
    """
    Dependencies may be stored as names or as task-like objects.
    Your Prefect code assumes names, but this keeps the Airflow layer safer.
    """
    return dep.name if hasattr(dep, "name") else str(dep)


def make_unique_task_ids(sorted_tasks):
    """
    Airflow task IDs must be unique after sanitization.
    """
    used = set()
    result = {}

    for index, task_obj in enumerate(sorted_tasks):
        base = safe_airflow_id(task_obj.name, fallback=f"task_{index}")
        task_id = base
        counter = 2

        while task_id in used:
            task_id = f"{base}_{counter}"
            counter += 1

        used.add(task_id)
        result[task_obj.name] = task_id

    return result


def should_run_synchronously(config):
    """
    For compatibility with your existing runner call, this defaults to local
    synchronous execution through dag.test().

    Set EXP_ENGINE_AIRFLOW_SYNC=0 when exposing the DAG to the Airflow UI/scheduler.
    """
    if isinstance(config, dict) and "airflow_sync" in config:
        return bool(config["airflow_sync"])

    return os.environ.get("EXP_ENGINE_AIRFLOW_SYNC", "1").lower() in {
        "1",
        "true",
        "yes",
        "sync",
        "local",
        "test",
    }


# -------------------------
# Airflow TaskFlow task builder
# -------------------------
def build_airflow_task(
    task_obj,
    wf_id,
    exp_id,
    mapping,
    runner_folder,
    dependency_task_ids,
    airflow_task_id,
):
    impl_file = task_obj.impl_file
    task_name = task_obj.name

    @task(task_id=airflow_task_id)
    def airflow_task():
        print(f"[{task_name}] ▶ START")

        context = get_current_context()
        ti = context["ti"]

        # Pull dependency outputs from XCom and merge them into one resultMap.
        # This mimics your Prefect layer:
        #
        # prev_result_map = {}
        # for dep in deps:
        #     prev_result_map.update(results[dep])
        resultMap = {}

        for dep_task_id in dependency_task_ids:
            dep_result = ti.xcom_pull(task_ids=dep_task_id)

            if dep_result:
                print(f"[{task_name}] pulled resultMap from dependency {dep_task_id}")
                resultMap.update(dep_result)

        # Set PYTHONPATH for dependent modules.
        original_sys_path = list(sys.path)

        paths = [LOCAL_HELPER_FULL_PATH]

        for dep in getattr(task_obj, "dependent_modules", []):
            dep_path = dep.split("/**")[0] if "/**" in dep else dep
            paths.append(str(Path(runner_folder) / dep_path))

        sys.path = paths + sys.path

        try:
            # Variables
            variables = {
                "wf_id": wf_id,
                "exp_id": exp_id,
                "task_name": task_name,
                "exp_engine_metadata": mapping.get("exp_engine_metadata"),
                "mapping": mapping.get("mapping"),
            }

            for k, v in resultMap.items():
                variables[k] = v

            # Apply execution engine mapping
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
                        f"'{source_file_name}' -> '{target_key}' "
                        f"with value '{value}'"
                    )

            # Prototypical inputs
            for input_name in getattr(task_obj, "prototypical_inputs", []):
                if input_name not in variables or variables.get(input_name) is None:
                    variables[input_name] = resultMap.get(input_name)

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

            print(f"[{task_name}] Variables:")
            print(variables)

            # Execute task implementation
            with open(impl_file, "r") as f:
                lines = f.readlines()

            script_lines = (
                ["import local_helper as ph\n"]
                + [f"variables = {variables!r}\n"]
                + rewrite_resultmap(lines)
                + ["\nph.save_result(resultMap)\n"]
            )

            tmp_path = None

            try:
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
                    tmp.writelines(script_lines)
                    tmp_path = tmp.name

                globals_after_run = runpy.run_path(
                    tmp_path,
                    run_name="__main__",
                    init_globals={"resultMap": resultMap},
                )

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

            executed_variables = globals_after_run.get("variables", {})

            # Capture declared logical/prototypical outputs written into variables
            for output_name in getattr(task_obj, "prototypical_outputs", []):
                if output_name in resultMap and resultMap[output_name] is not None:
                    print(
                        f"[{task_name}] kept prototypical output "
                        f"'{output_name}' from resultMap: {resultMap[output_name]}"
                    )

                elif (
                    output_name in executed_variables
                    and executed_variables[output_name] is not None
                ):
                    resultMap[output_name] = executed_variables[output_name]
                    print(
                        f"[{task_name}] captured prototypical output "
                        f"'{output_name}' from variables into resultMap"
                    )

            print(f"[{task_name}] ✔ DONE")
            return resultMap

        finally:
            sys.path = original_sys_path

    return airflow_task


# -------------------------
# Airflow workflow entry point
# -------------------------
def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config):
    print("[Airflow runner] workflow object:")
    import pprint

    pprint.pprint(to_dict(w))

    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)

    exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)

    exp_engine_runtime_config = {
        "exp_engine_metadata": exp_engine_metadata,
    }

    mapping = _create_execution_engine_mapping(
        sorted_tasks,
        exp_engine_runtime_config,
    )

    if not os.path.exists("intermediate_files"):
        os.makedirs("intermediate_files")

    with open(EXECUTION_ENGINE_MAPPING_FILE, "w") as f:
        json.dump(mapping, f)

    with open(VARIABLES, "w") as f:
        json.dump({}, f)

    with open(RESULT, "w") as f:
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

    airflow_task_ids = make_unique_task_ids(sorted_tasks)

    dag_id = safe_airflow_id(f"{w.name}_{wf_id}", fallback=f"workflow_{wf_id}")

    @dag(
        dag_id=dag_id,
        schedule=None,
        start_date=datetime(2024, 1, 1),
        catchup=False,
        tags=["exp_engine", "airflow"],
    )
    def dynamic_airflow_dag():
        task_outputs = {}

        # Create TaskFlow tasks
        for task_obj in sorted_tasks:
            deps = getattr(task_obj, "dependencies", [])
            dependency_names = [get_dep_name(dep) for dep in deps]

            dependency_task_ids = [
                airflow_task_ids[dep_name]
                for dep_name in dependency_names
                if dep_name in airflow_task_ids
            ]

            task_factory = build_airflow_task(
                task_obj=task_obj,
                wf_id=wf_id,
                exp_id=exp_id,
                mapping=mapping,
                runner_folder=runner_folder,
                dependency_task_ids=dependency_task_ids,
                airflow_task_id=airflow_task_ids[task_obj.name],
            )

            task_outputs[task_obj.name] = task_factory()

        # Explicit Airflow dependencies
        for task_obj in sorted_tasks:
            deps = getattr(task_obj, "dependencies", [])
            dependency_names = [get_dep_name(dep) for dep in deps]

            for dep_name in dependency_names:
                if dep_name in task_outputs:
                    task_outputs[dep_name] >> task_outputs[task_obj.name]

        @task(task_id="collect_final_result")
        def collect_final_result(task_ids_in_order):
            """
            Merge all task resultMaps in workflow order and write results.json.
            This gives you a stable final output file even when Airflow executes
            independent tasks in parallel.
            """
            context = get_current_context()
            ti = context["ti"]

            final_result = {}

            for task_id in task_ids_in_order:
                task_result = ti.xcom_pull(task_ids=task_id)

                if task_result:
                    final_result.update(task_result)

            with open(RESULT, "w") as f:
                json.dump(final_result, f)

            print("[Airflow runner] final resultMap:")
            print(final_result)
            print(f"[Airflow runner] wrote {RESULT}")

            return final_result

        final = collect_final_result(
            [airflow_task_ids[task_obj.name] for task_obj in sorted_tasks]
        )

        # Make final collector wait for every task.
        for task_obj in sorted_tasks:
            task_outputs[task_obj.name] >> final

    dag_obj = dynamic_airflow_dag()

    # Makes the DAG discoverable if this function is called from a DAG wrapper file.
    globals()[dag_id] = dag_obj

    if should_run_synchronously(config):
        print("[Airflow runner] Running DAG locally with dag.test()")
        dag_obj.test()

        if os.path.exists(RESULT):
            with open(RESULT, "r") as f:
                return json.load(f)

        return None

    print("[Airflow runner] Built DAG object without running it")
    return dag_obj