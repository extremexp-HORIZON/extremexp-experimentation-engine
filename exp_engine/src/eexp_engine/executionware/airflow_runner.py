import os
import json
import sys
from pathlib import Path

DAG_TEMPLATE = """
import os
import sys
import json
import runpy
import tempfile
from pathlib import Path
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

def normalize_path(p):
    return str(Path(p).as_posix()) if p else None

def rewrite_resultmap(lines):
    return [l.replace("resultMap.put", "resultMap.__setitem__") if "resultMap.put" in l else l for l in lines]

def execute_task_logic(task_obj_data, wf_id, exp_id, mapping, runner_folder, **context):
    # Ensure task_name is safely retrieved from the passed dict
    task_name = task_obj_data.get('name', 'unknown_task')
    ti = context['ti']

    # Pull from the specific predecessor via XCom
    prev_task_id = task_obj_data.get('prev_task_id')
    resultMap = {{}}
    if prev_task_id:
        pulled_val = ti.xcom_pull(task_ids=prev_task_id)
        if isinstance(pulled_val, dict):
            resultMap = pulled_val

    # Setup Python Path
    sys.path.append("{local_helper_path}")
    for dep in task_obj_data.get("dependent_modules", []):
        dep_path = dep.split("/**")[0] if "/**" in dep else dep
        sys.path.append(str(Path(runner_folder) / dep_path))

    # Construct variables dictionary safely
    variables = {{
        "wf_id": wf_id,
        "exp_id": exp_id,
        "task_name": task_name,
    }}

    # Update with resultMap and params
    variables.update(resultMap)
    variables.update(task_obj_data.get('params', {{}}))

    # Apply engine mapping
    task_mapping = mapping.get(task_name, {{}})
    for target_key, source_key in task_mapping.items():
        if source_key in resultMap:
            variables[target_key] = resultMap[source_key]

    # Load implementation script
    impl_file = task_obj_data.get('impl_file')
    with open(impl_file, "r") as f:
        lines = f.readlines()

    script_lines = (
        ["import local_helper as ph\\n", f"variables = {{variables}}\\n"] 
        + rewrite_resultmap(lines) 
        + ["\\nph.save_result(resultMap)\\n"]
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.writelines(script_lines)
        tmp_path = tmp.name

    try:
        runpy.run_path(tmp_path, run_name="__main__", init_globals={{"resultMap": resultMap}})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return resultMap

with DAG(
    dag_id="{dag_id}",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:
    tasks_operators = {{}}
    {task_definitions_block}
    {dependencies_block}
"""


def create_airflow_dag(w, exp_id, exp_name, wf_id, runner_folder):
    task_defs = []
    deps = []

    from exp_engine.src.eexp_engine.executionware.proactive_runner import _create_execution_engine_mapping
    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)
    mapping = _create_execution_engine_mapping(sorted_tasks)

    prev_task_name = None

    for t in sorted_tasks:
        # Standardize data structure for the template
        t_data = {
            "name": str(t.name),
            "impl_file": str(t.impl_file),
            "params": getattr(t, "params", {}),
            "dependent_modules": getattr(t, "dependent_modules", []),
            "prev_task_id": prev_task_name
        }

        task_str = f"""
    tasks_operators['{t.name}'] = PythonOperator(
        task_id='{t.name}',
        python_callable=execute_task_logic,
        op_kwargs={{
            'task_obj_data': {json.dumps(t_data)},
            'wf_id': "{wf_id}",
            'exp_id': "{exp_id}",
            'mapping': {json.dumps(mapping)},
            'runner_folder': r"{runner_folder}"
        }},
    )"""
        task_defs.append(task_str)

        if prev_task_name:
            deps.append(f"tasks_operators['{prev_task_name}'] >> tasks_operators['{t.name}']")
        prev_task_name = t.name

    full_dag_code = DAG_TEMPLATE.format(
        local_helper_path=os.path.dirname(os.path.abspath(__file__)),
        dag_id=f"{w.name}_{wf_id}",
        task_definitions_block="\n".join(task_defs),
        dependencies_block="\n".join(deps)
    )

    output_path = os.path.join(os.getcwd(), f"airflow_dag_{wf_id}.py")
    with open(output_path, "w") as f:
        f.write(full_dag_code)

    return output_path