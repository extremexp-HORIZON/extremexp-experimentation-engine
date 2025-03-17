import src.eexp_engine.functions as functions
from src.eexp_engine import client
from src.eexp_engine.data_abstraction_layer.data_abstraction_api import *
import eexp_config
import logging
import importlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
set_data_abstraction_config(eexp_config)


class ApiHandler(object):

    EXPERIMENTS_FOLDER = 'workflows/'

    def __init__(self):
        print("ApiHandler created")

    def run_exp(self,exp_name):
       config = importlib.import_module("eexp_config")
       client.run(__file__, exp_name, config)

    def kill_workflow(self, wf_id):
        wf = get_workflow(wf_id)
        job_status = wf["status"]

        if job_status == "running":
            print(f"Killing workflow with id: {wf_id}")
            job_id  = get_workflow(wf_id)["metadata"]["proactive_job_id"]
            print(f"Killing proactive job with id: {job_id}")
            client.kill_job(job_id, eexp_config)
            update_workflow(wf_id, {"status": "killed"})

        elif job_status == "scheduled":
            update_workflow(wf_id, {"status": "cancelled"})


    def pause_workflow(self, wf_id):
        wf = get_workflow(wf_id)
        job_status = wf["status"]

        if job_status == "running":
            print(f"Pausing workflow with id: {wf_id}")
            job_id  = get_workflow(wf_id)["metadata"]["proactive_job_id"]
            print(f"Pausing proactive job with id: {job_id}")
            client.pause_job(job_id, eexp_config)
            update_workflow(wf_id, {"status": "paused"})

    def resume_workflow(self, wf_id):
        wf = get_workflow(wf_id)
        job_status = wf["status"]

        if job_status == "resumed":
            print(f"Resuming workflow with id: {wf_id}")
            job_id  = get_workflow(wf_id)["metadata"]["proactive_job_id"]
            print(f"Resuming proactive job with id: {job_id}")
            client.resume_job(job_id, eexp_config)
            update_workflow(wf_id, {"status": "resumed"})


    def kill_experiment(self, exp_id):
        print(f"Killing an experiment with id: {exp_id}")
        wfs_ids = get_experiment(exp_id)["workflow_ids"]

        exp_status = get_experiment(exp_id)["status"]

        if exp_status == "killed":
            print(f"The experiment has already been killed")

        else:
            for i in wfs_ids:
                wf = get_workflow(i)
                job_status = wf["status"]

                if job_status == "completed":
                    continue

                elif job_status == "running":
                    job_id = wf["metadata"]["proactive_job_id"]
                    print(f"Killing proactive job with id: {job_id}")
                    update_workflow(i, {"status": "killed"})
                    client.kill_job(job_id, eexp_config)

                elif job_status == "scheduled":
                    update_workflow(i, {"status": "cancelled"})

            update_experiment(exp_id, {"status": "killed"})

    def pause_experiment(self, exp_id):
        print(f"Pausing an experiment with id: {exp_id}")
        wfs_ids = get_experiment(exp_id)["workflow_ids"]

        for i in wfs_ids:
            wf = get_workflow(i)
            job_status = wf["status"]

            if job_status == "scheduled" or job_status=="completed":
                continue

            elif job_status == "running":
                job_id = wf["metadata"]["proactive_job_id"]
                update_workflow(i, {"status": "paused"})
                print(f"Pausing proactive job with id: {job_id}")
                client.pause_job(job_id, eexp_config)

        update_experiment(exp_id, {"status": "paused"})

    def resume_experiment(self, exp_id):
        print(f"Resuming an experiment with id: {exp_id}")
        wfs_ids = get_experiment(exp_id)["workflow_ids"]

        for i in wfs_ids:
            wf = get_workflow(i)
            job_status = wf["status"]

            if job_status == "completed":
                continue

            elif job_status == "paused":
                job_id = wf["metadata"]["proactive_job_id"]
                update_workflow(i, {"status": "scheduled"})
                print(f"Resuming proactive job with id: {job_id}")
                client.resume_job(job_id, eexp_config)


        update_experiment(exp_id, {"status": "resumed"})

apiHandler = ApiHandler()
