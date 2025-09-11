import eexp_engine.functions as functions
from eexp_engine import client
from eexp_engine.data_abstraction_layer.data_abstraction_api import DataAbstractionClient
import eexp_config
import logging
import importlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiHandler:

    def __init__(self):
        self.config = importlib.import_module("eexp_config")
        self.data = DataAbstractionClient(self.config)

    def run_exp(self, exp_name, async_execution=False):
        return client.run(__file__, exp_name, self.config, async_execution=async_execution)

    def kill_workflow(self, wf_id):
        wf = self.data.get_workflow(wf_id)
        if not wf:
            return
        status = wf.get("status")
        if status == "running":
            job_id = wf.get("metadata", {}).get("proactive_job_id")
            if job_id:
                client.kill_job(job_id, self.config)
            self.data.update_workflow(wf_id, {"status": "killed"})
        elif status == "scheduled":
            self.data.update_workflow(wf_id, {"status": "cancelled"})

    def pause_workflow(self, wf_id):
        wf = self.data.get_workflow(wf_id)
        if not wf:
            return
        if wf.get("status") == "running":
            job_id = wf.get("metadata", {}).get("proactive_job_id")
            if job_id:
                client.pause_job(job_id, self.config)
            self.data.update_workflow(wf_id, {"status": "paused"})

    def resume_workflow(self, wf_id):
        wf = self.data.get_workflow(wf_id)
        if not wf:
            return
        if wf.get("status") == "resumed":
            job_id = wf.get("metadata", {}).get("proactive_job_id")
            if job_id:
                client.resume_job(job_id, self.config)
            self.data.update_workflow(wf_id, {"status": "resumed"})

    def kill_experiment(self, exp_id):
        exp = self.data.get_experiment(exp_id)
        if not exp:
            return
        if exp.get("status") == "killed":
            return
        for wf_id in exp.get("workflow_ids", []):
            wf = self.data.get_workflow(wf_id)
            if not wf:
                continue
            status = wf.get("status")
            if status == "completed":
                continue
            if status == "running":
                job_id = wf.get("metadata", {}).get("proactive_job_id")
                if job_id:
                    client.kill_job(job_id, self.config)
                self.data.update_workflow(wf_id, {"status": "killed"})
            elif status == "scheduled":
                self.data.update_workflow(wf_id, {"status": "cancelled"})
        self.data.update_experiment(exp_id, {"status": "killed"})

    def pause_experiment(self, exp_id):
        exp = self.data.get_experiment(exp_id)
        if not exp:
            return
        for wf_id in exp.get("workflow_ids", []):
            wf = self.data.get_workflow(wf_id)
            if not wf:
                continue
            status = wf.get("status")
            if status in ("scheduled", "completed"):
                continue
            if status == "running":
                job_id = wf.get("metadata", {}).get("proactive_job_id")
                if job_id:
                    client.pause_job(job_id, self.config)
                self.data.update_workflow(wf_id, {"status": "paused"})
        self.data.update_experiment(exp_id, {"status": "paused"})

    def resume_experiment(self, exp_id):
        exp = self.data.get_experiment(exp_id)
        if not exp:
            return
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
        self.data.update_experiment(exp_id, {"status": "resumed"})


apiHandler = ApiHandler()
