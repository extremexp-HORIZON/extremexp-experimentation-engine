from pathlib import Path
from datetime import datetime
import asyncio
import csv
import statistics
import time
import traceback

from prefect.client.orchestration import get_client

# Depending on your Prefect version this import may work.
# If not, the code below falls back automatically.
try:
    from prefect.client.schemas.filters import TaskRunFilter
    HAS_TASK_FILTER = True
except Exception:
    HAS_TASK_FILTER = False

from eexp_engine import client
import eexp_config


# ============================================================
# Configuration
# ============================================================

REPEATS = 1

EXPERIMENTS = [
    "tests/simple_configurations/demo_wp5.xxp",
    "tests/simple_configurations/exp_test_wp5.xxp",
]

OUTPUT_FILE = "prefect_benchmark_results.csv"

# Wait for Prefect API to finish persisting task runs
PREFECT_SYNC_DELAY = 2


# ============================================================
# Prefect Metrics
# ============================================================

async def get_latest_flow_run():

    async with get_client() as prefect_client:

        flow_runs = await prefect_client.read_flow_runs(
            sort="START_TIME_DESC",
            limit=1,
        )

        if not flow_runs:
            print("No flow runs found.")
            return None

        flow_run = flow_runs[0]

        print("\n========== FLOW ==========")
        print(f"Flow ID     : {flow_run.id}")
        print(f"Name        : {flow_run.name}")
        print(f"State       : {flow_run.state_name}")
        print(f"Start       : {flow_run.start_time}")
        print(f"End         : {flow_run.end_time}")

        task_runs = []

        try:

            if HAS_TASK_FILTER:

                task_runs = await prefect_client.read_task_runs(
                    task_run_filter=TaskRunFilter(
                        flow_run_id={
                            "any_": [flow_run.id]
                        }
                    )
                )

            else:
                # Older Prefect versions
                task_runs = await prefect_client.read_task_runs(
                    flow_run_filter={
                        "id": {
                            "any_": [flow_run.id]
                        }
                    }
                )

        except Exception as e:

            print("\nTask filter failed.")
            print(e)

            print("\nTrying to retrieve ALL task runs...")

            try:
                task_runs = await prefect_client.read_task_runs()
            except Exception:
                task_runs = []

        print(f"\nTask runs found: {len(task_runs)}")

        for task in task_runs:

            print("--------------------------------")
            print(f"Task : {task.name}")
            print(f"ID   : {task.id}")
            print(f"State: {task.state_name}")
            print(f"Flow : {task.flow_run_id}")
            print(f"Start: {task.start_time}")
            print(f"End  : {task.end_time}")

        return flow_run, task_runs


def extract_metrics(flow_run, task_runs):

    flow_runtime = None

    if flow_run.start_time and flow_run.end_time:
        flow_runtime = (
            flow_run.end_time -
            flow_run.start_time
        ).total_seconds()

    task_durations = []

    failed_tasks = 0

    for task in task_runs:

        if task.state_name == "Failed":
            failed_tasks += 1

        if task.start_time and task.end_time:

            duration = (
                task.end_time -
                task.start_time
            ).total_seconds()

            task_durations.append(duration)

    total_task_runtime = sum(task_durations)

    avg_task_runtime = (
        statistics.mean(task_durations)
        if task_durations else None
    )

    longest_task_runtime = (
        max(task_durations)
        if task_durations else None
    )

    orchestration_overhead = None

    if flow_runtime is not None:
        orchestration_overhead = (
            flow_runtime -
            total_task_runtime
        )

    if len(task_runs) == 0:
        print("\nWARNING: No task runs were returned by Prefect.")
        print("This usually means either:")
        print("  - the flow contains no @task decorated functions")
        print("  - the wrong flow is being queried")
        print("  - task runs have not yet been written")
        print("  - client.run() is waiting outside the Prefect flow")

    return {

        "flow_run_id": str(flow_run.id),
        "flow_name": flow_run.name,
        "flow_state": flow_run.state_name,
        "flow_runtime_seconds": flow_runtime,

        "num_tasks": len(task_runs),
        "failed_tasks": failed_tasks,

        "avg_task_runtime_seconds": avg_task_runtime,
        "longest_task_runtime_seconds": longest_task_runtime,
        "total_task_runtime_seconds": total_task_runtime,

        "orchestration_overhead_seconds": orchestration_overhead,
    }


# ============================================================
# Experiment Execution
# ============================================================

def run_single_experiment(
    experiment_file: Path,
    experiment_name: str
):

    start_wall = time.perf_counter()

    status = "SUCCESS"
    error = ""

    try:

        client.run(
            experiment_file,
            experiment_name,
            eexp_config
        )

    except Exception as e:

        traceback.print_exc()

        status = "FAILED"
        error = str(e)

    wall_runtime = (
        time.perf_counter() -
        start_wall
    )

    print(f"\nWaiting {PREFECT_SYNC_DELAY}s for Prefect...")

    time.sleep(PREFECT_SYNC_DELAY)

    metrics = {
        "flow_run_id": "",
        "flow_name": "",
        "flow_state": "",
        "flow_runtime_seconds": "",
        "num_tasks": "",
        "failed_tasks": "",
        "avg_task_runtime_seconds": "",
        "longest_task_runtime_seconds": "",
        "total_task_runtime_seconds": "",
        "orchestration_overhead_seconds": "",
    }

    try:

        latest = asyncio.run(
            get_latest_flow_run()
        )

        if latest:

            flow_run, task_runs = latest

            metrics = extract_metrics(
                flow_run,
                task_runs
            )

    except Exception:

        traceback.print_exc()

    return {

        "timestamp": datetime.now().isoformat(),
        "experiment": experiment_name,
        "status": status,
        "wall_runtime_seconds": round(wall_runtime, 3),
        "error": error,

        **metrics,
    }


# ============================================================
# Main
# ============================================================

def main():

    base_path = (
        Path.cwd() /
        eexp_config.EXPERIMENT_LIBRARY_PATH
    )

    results = []

    for experiment in EXPERIMENTS:

        experiment_path = base_path / experiment

        experiment_name = (
            experiment
            .replace(".xxp", "")
            .replace("\\", "/")
        )

        for run in range(1, REPEATS + 1):

            print("\n===================================")
            print(f"Running {experiment_name}")
            print(f"Run {run}/{REPEATS}")
            print("===================================")

            result = run_single_experiment(
                experiment_path,
                experiment_name
            )

            result["run_number"] = run

            results.append(result)

    columns = [

        "timestamp",
        "experiment",
        "run_number",
        "status",

        "wall_runtime_seconds",

        "flow_run_id",
        "flow_name",
        "flow_state",
        "flow_runtime_seconds",

        "num_tasks",
        "failed_tasks",

        "avg_task_runtime_seconds",
        "longest_task_runtime_seconds",
        "total_task_runtime_seconds",

        "orchestration_overhead_seconds",

        "error",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()