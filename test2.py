from pathlib import Path
from datetime import datetime
import asyncio
import csv
import statistics
import time
import traceback

from prefect.client.orchestration import get_client

from eexp_engine import client
import eexp_config


# ============================================================
# Configuration
# ============================================================

REPEATS = 3

EXPERIMENTS = [
    "tests/simple_configurations/demo_wp5.xxp",
    "tests/simple_configurations/exp_test_wp5.xxp",
]

OUTPUT_FILE = "prefect_benchmark_results.csv"


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
            return None

        flow_run = flow_runs[0]

        try:
            task_runs = await prefect_client.read_task_runs(
                flow_run_filter={
                    "id": {
                        "any_": [flow_run.id]
                    }
                }
            )
        except Exception:
            task_runs = []

        return flow_run, task_runs


def extract_metrics(flow_run, task_runs):

    flow_runtime = None

    if flow_run.start_time and flow_run.end_time:
        flow_runtime = (
            flow_run.end_time - flow_run.start_time
        ).total_seconds()

    task_durations = []

    failed_tasks = 0

    for task in task_runs:

        if task.state_name == "Failed":
            failed_tasks += 1

        if task.start_time and task.end_time:

            duration = (
                task.end_time - task.start_time
            ).total_seconds()

            task_durations.append(duration)

    total_task_runtime = sum(task_durations)

    avg_task_runtime = (
        statistics.mean(task_durations)
        if task_durations
        else 0
    )

    longest_task_runtime = (
        max(task_durations)
        if task_durations
        else 0
    )

    orchestration_overhead = None

    if flow_runtime is not None:
        orchestration_overhead = (
            flow_runtime - total_task_runtime
        )

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

    start_wall_time = time.perf_counter()

    status = "SUCCESS"
    error = ""

    try:

        client.run(
            experiment_file,
            experiment_name,
            eexp_config
        )

    except Exception as e:

        status = "FAILED"
        error = str(e)

        print(f"\nExperiment failed: {experiment_name}")
        traceback.print_exc()

    wall_runtime = (
        time.perf_counter() - start_wall_time
    )

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

    except Exception as e:

        print(
            f"Could not retrieve Prefect metrics: {e}"
        )

    return {
        "timestamp": datetime.now().isoformat(),
        "experiment": experiment_name,
        "status": status,
        "wall_runtime_seconds": round(
            wall_runtime,
            3
        ),
        "error": error,
        **metrics,
    }


# ============================================================
# Main
# ============================================================

def main():

    base_path = (
        Path.cwd()
        / eexp_config.EXPERIMENT_LIBRARY_PATH
    )

    results = []

    for experiment in EXPERIMENTS:

        experiment_path = (
            base_path
            / experiment
        )

        experiment_name = (
            experiment
            .replace(".xxp", "")
            .replace("\\", "/")
        )

        for run_number in range(1, REPEATS + 1):

            print(
                f"\nRunning "
                f"{experiment_name} "
                f"({run_number}/{REPEATS})"
            )

            result = run_single_experiment(
                experiment_path,
                experiment_name
            )

            result["run_number"] = run_number

            results.append(result)

            print(
                f"Finished "
                f"{result['status']} "
                f"in "
                f"{result['wall_runtime_seconds']:.2f}s"
            )

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

    print(
        f"\nBenchmark results written to:"
        f"\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()