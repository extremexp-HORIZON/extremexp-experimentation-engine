
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
    resultMap = {}
    if prev_task_id:
        pulled_val = ti.xcom_pull(task_ids=prev_task_id)
        if isinstance(pulled_val, dict):
            resultMap = pulled_val

    # Setup Python Path
    sys.path.append("C:\Users\quinn\Documents\GitHub\extremexp-experimentation-engine\exp_engine\src\eexp_engine\executionware")
    for dep in task_obj_data.get("dependent_modules", []):
        dep_path = dep.split("/**")[0] if "/**" in dep else dep
        sys.path.append(str(Path(runner_folder) / dep_path))

    # Construct variables dictionary safely
    variables = {
        "wf_id": wf_id,
        "exp_id": exp_id,
        "task_name": task_name,
    }

    # Update with resultMap and params
    variables.update(resultMap)
    variables.update(task_obj_data.get('params', {}))

    # Apply engine mapping
    task_mapping = mapping.get(task_name, {})
    for target_key, source_key in task_mapping.items():
        if source_key in resultMap:
            variables[target_key] = resultMap[source_key]

    # Load implementation script
    impl_file = task_obj_data.get('impl_file')
    with open(impl_file, "r") as f:
        lines = f.readlines()

    script_lines = (
        ["import local_helper as ph\n", f"variables = {variables}\n"] 
        + rewrite_resultmap(lines) 
        + ["\nph.save_result(resultMap)\n"]
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.writelines(script_lines)
        tmp_path = tmp.name

    try:
        runpy.run_path(tmp_path, run_name="__main__", init_globals={"resultMap": resultMap})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return resultMap

with DAG(
    dag_id="AssembledUserInteraction_q6U5XJ4BD4IGUmABU90N",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:
    tasks_operators = {}
    
    tasks_operators['Task1'] = PythonOperator(
        task_id='Task1',
        python_callable=execute_task_logic,
        op_kwargs={
            'task_obj_data': {"name": "Task1", "impl_file": "playground/tasks\\UserInteraction/Task1/task.py", "params": {}, "dependent_modules": [], "prev_task_id": null},
            'wf_id': "q6U5XJ4BD4IGUmABU90N",
            'exp_id': "qqU5XJ4BD4IGUmABSt1Y",
            'mapping': {"Task1": {}, "Task2": {}, "Task3": {}},
            'runner_folder': r"C:\Users\quinn\Documents\GitHub\extremexp-experimentation-engine\playground\experiments\tests\user_interaction"
        },
    )

    tasks_operators['Task2'] = PythonOperator(
        task_id='Task2',
        python_callable=execute_task_logic,
        op_kwargs={
            'task_obj_data': {"name": "Task2", "impl_file": "playground/tasks\\UserInteraction/Task2/task.py", "params": {}, "dependent_modules": [], "prev_task_id": "Task1"},
            'wf_id': "q6U5XJ4BD4IGUmABU90N",
            'exp_id': "qqU5XJ4BD4IGUmABSt1Y",
            'mapping': {"Task1": {}, "Task2": {}, "Task3": {}},
            'runner_folder': r"C:\Users\quinn\Documents\GitHub\extremexp-experimentation-engine\playground\experiments\tests\user_interaction"
        },
    )

    tasks_operators['Task3'] = PythonOperator(
        task_id='Task3',
        python_callable=execute_task_logic,
        op_kwargs={
            'task_obj_data': {"name": "Task3", "impl_file": "playground/tasks\\UserInteraction/Task3/task.py", "params": {}, "dependent_modules": [], "prev_task_id": "Task2"},
            'wf_id': "q6U5XJ4BD4IGUmABU90N",
            'exp_id': "qqU5XJ4BD4IGUmABSt1Y",
            'mapping': {"Task1": {}, "Task2": {}, "Task3": {}},
            'runner_folder': r"C:\Users\quinn\Documents\GitHub\extremexp-experimentation-engine\playground\experiments\tests\user_interaction"
        },
    )
    tasks_operators['Task1'] >> tasks_operators['Task2']
tasks_operators['Task2'] >> tasks_operators['Task3']
