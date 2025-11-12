import eexp_engine.functions as functions
from eexp_engine import client
from eexp_engine.data_abstraction_layer.data_abstraction_api import DataAbstractionClient
import logging
import importlib
import os
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiHandler:

    def __init__(self):
        self.config = importlib.import_module("eexp_config")
        self.data = DataAbstractionClient(self.config)

    def run_exp(self, exp_name):
        try:
            exp_id = client.run(__file__, exp_name, self.config, async_execution=True)
            body = {
                "experiment": {
                    "id": exp_id,
                    "name": exp_name,
                    "status": "scheduled"
                },
                "message": "experiment scheduled."
            }
            return body, 202, {'Location': f'/exp/experiment/status/{exp_id}'}
        except FileNotFoundError as e:
            return {"error": {"code": "SPEC_NOT_FOUND", "exp_name": exp_name, "message": str(e)}}, 404
        except Exception as e:
            return {"error": {"code": "INTERNAL_ERROR", "message": str(e)}}, 500
    
    def get_experiment_status(self, exp_id):
        ERROR_LOG_DIR = "/error_logs"
        exp = self.data.get_experiment(exp_id)
        exp_status = exp.get("status", "unknown") if exp else "not_found"

        # Get queue position if experiment is scheduled or running (only if queue is initialized)
        queue_position = None
        if exp_status in ("scheduled", "running"):
            try:
                # Check if queue exists without initializing it
                from eexp_engine.experiment_queue import _experiment_queue
                if _experiment_queue is not None:
                    queue_position = _experiment_queue.get_experiment_position(exp_id)
            except Exception as e:
                logger.warning(f"Failed to get queue position for experiment {exp_id}: {e}")

        if exp_status == "not_found":
            return {"error": {"code": "NOT_FOUND", "message": f"Experiment with id {exp_id} not found"}}, 404
        elif exp_status == "failed":
            # Look for error log file
            log_pattern = os.path.join(ERROR_LOG_DIR, f"error_{exp_id}_*.log")
            log_files = glob.glob(log_pattern)
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                with open(latest_log, 'r') as f:
                    # Read the last 100 lines to avoid huge logs
                    lines = f.readlines()
                    error_log_content = '\n'.join(lines[-100:])
                return {
                    "experiment": {
                        "id": exp_id,
                        "status": exp_status,
                        "error_log": error_log_content
                    }
                }, 500
        else:
            response_data = {
                "id": exp_id,
                "status": exp_status
            }
            if queue_position is not None:
                if queue_position == 0:
                    response_data["queue_status"] = "running"
                else:
                    response_data["queue_status"] = "queued"
                    response_data["queue_position"] = queue_position

            return {"experiment": response_data}, 200
        
    def kill_workflow(self, wf_id):
        wf = self.data.get_workflow(wf_id)
        if not wf:
            return {"message": f"workflow with id {wf_id} not found"}, 404
        status = wf.get("status")
        if status == "running" or status == "pending_input" or status == "paused":
            job_id = wf.get("metadata", {}).get("proactive_job_id")
            if job_id:
                client.kill_job(job_id, self.config)
            else:
                return {"message": f"Job ID not found for workflow {wf_id}"}, 500
            self.data.update_workflow(wf_id, {"status": "killed"})
        elif status == "scheduled":
            self.data.update_workflow(wf_id, {"status": "cancelled"})
        return {"message": f"workflow with id {wf_id} is killed"}, 204

    def pause_workflow(self, wf_id):
        wf = self.data.get_workflow(wf_id)
        if not wf:
            return {"message": f"workflow with id {wf_id} not found"}, 404
        if wf.get("status") == "running" or wf.get("status") == "pending_input":
            job_id = wf.get("metadata", {}).get("proactive_job_id")
            if job_id:
                client.pause_job(job_id, self.config)
            else:
                return {"message": f"Job ID not found for workflow {wf_id}"}, 500
            self.data.update_workflow(wf_id, {"status": "paused"})
            return {"message": f"workflow with id {wf_id} is paused"}, 204

    def resume_workflow(self, wf_id):
        wf = self.data.get_workflow(wf_id)
        if not wf:
            return {"message": f"workflow with id {wf_id} not found"}, 404
        if wf.get("status") == "paused":
            job_id = wf.get("metadata", {}).get("proactive_job_id")
            if job_id:
                client.resume_job(job_id, self.config)
            else:
                return {"message": f"Job ID not found for workflow {wf_id}"}, 500
            self.data.update_workflow(wf_id, {"status": "running"})
            return {"message": f"workflow with id {wf_id} is resumed"}, 204

    def kill_experiment(self, exp_id):
        exp = self.data.get_experiment(exp_id)
        if not exp:
            return {"message": f"experiment with id {exp_id} not found"}, 404
        if exp.get("status") == "killed":
            return {"message": f"experiment with id {exp_id} is already killed"}, 204

        # Kill the experiment execution thread
        thread_killed = client.kill_experiment_thread(exp_id)
        if not thread_killed:
            logger.warning(f"Experiment thread {exp_id} not found in registry (may have already completed)")

        # Kill all running/scheduled workflows
        for wf_id in exp.get("workflow_ids", []):
            wf = self.data.get_workflow(wf_id)
            if not wf:
                continue
            status = wf.get("status")
            if status == "completed":
                continue
            if status == "running" or status == "pending_input" or status == "paused":
                # Find and kill the ProActive job
                job_id = wf.get("metadata", {}).get("proactive_job_id")
                if job_id:
                    client.kill_job(job_id, self.config)
                self.data.update_workflow(wf_id, {"status": "killed"})
            elif status == "scheduled":
                self.data.update_workflow(wf_id, {"status": "cancelled"})

        # Update experiment status in database
        self.data.update_experiment(exp_id, {"status": "killed"})
        return {"message": f"experiment with id {exp_id} is killed"}, 204

    def pause_experiment(self, exp_id):
        exp = self.data.get_experiment(exp_id)
        if not exp:
            return {"message": f"experiment with id {exp_id} not found"}, 404
        for wf_id in exp.get("workflow_ids", []):
            wf = self.data.get_workflow(wf_id)
            if not wf:
                continue
            status = wf.get("status")
            if status in ("scheduled", "completed"):
                continue
            if status == "running" or status == "pending_input":
                job_id = wf.get("metadata", {}).get("proactive_job_id")
                if job_id:
                    client.pause_job(job_id, self.config)
                self.data.update_workflow(wf_id, {"status": "paused"})
        self.data.update_experiment(exp_id, {"status": "paused"})
        return {"message": f"experiment with id {exp_id} is paused"}, 204

    def resume_experiment(self, exp_id):
        exp = self.data.get_experiment(exp_id)
        if not exp:
            return {"message": f"experiment with id {exp_id} not found"}, 404
        for wf_id in exp.get("workflow_ids", []):
            wf = self.data.get_workflow(wf_id)
            if not wf:
                continue
            status = wf.get("status")
            if status == "completed":
                continue
            if status == "paused":
                job_id = wf.get("metadata", {}).get("proactive_job_id")
                if job_id:
                    client.resume_job(job_id, self.config)
                self.data.update_workflow(wf_id, {"status": "scheduled"})
        self.data.update_experiment(exp_id, {"status": "running"})
        return {"message": f"experiment with id {exp_id} is resumed"}, 204

    def get_queue_status(self):
        """Get the current status of the experiment queue."""
        try:
            # Check if queue exists without initializing it
            from eexp_engine.experiment_queue import _experiment_queue
            if _experiment_queue is not None:
                status = _experiment_queue.get_queue_status()
                return {
                    "queue": status
                }, 200
            else:
                return {
                    "queue": {
                        "status": "not_initialized",
                        "message": "Queue is only initialized for async execution (Docker/service mode)"
                    }
                }, 200
        except Exception as e:
            logger.exception(f"Failed to get queue status: {e}")
            return {"error": {"code": "INTERNAL_ERROR", "message": str(e)}}, 500


apiHandler = ApiHandler()
