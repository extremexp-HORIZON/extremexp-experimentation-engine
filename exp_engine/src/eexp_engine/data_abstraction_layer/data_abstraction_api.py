import requests
import logging
import datetime
import json
import warnings

logger = logging.getLogger(__name__)


class DataAbstractionClient:
    """Stateless client wrapper (per experiment) eliminating global mutable CONFIG."""
    def __init__(self, config):
        self._base = config.DATA_ABSTRACTION_BASE_URL
        self._headers = {'access-token': config.DATA_ABSTRACTION_ACCESS_TOKEN}

    # ----- Experiments -----
    def get_all_experiments(self):
        url = f"{self._base}/executed-experiments"
        r = requests.get(url, headers=self._headers)
        logger.info(f"GET {url} -> {r.status_code}")
        return r.json().get('executed_experiments', [])

    def create_experiment(self, body, creator_name):
        body = dict(body)
        body["status"] = "scheduled"
        body["creator"] = {"name": creator_name}
        url = f"{self._base}/experiments"
        r = requests.put(url, json=body, headers=self._headers)
        logger.info(f"PUT {url} -> {r.status_code}")
        if r.status_code == 201:
            exp_id = r.json()['message']['experimentId']
            logger.info(f"New experiment created id={exp_id}")
            return exp_id
        logger.error(r.text)
        return None

    def get_experiment(self, exp_id):
        url = f"{self._base}/experiments/{exp_id}"
        r = requests.get(url, headers=self._headers)
        logger.info(f"GET {url} -> {r.status_code}")
        return r.json().get('experiment')

    def update_experiment(self, exp_id, body):
        url = f"{self._base}/experiments/{exp_id}"
        r = requests.post(url, json=body, headers=self._headers)
        logger.info(f"POST {url} -> {r.status_code}")
        return r.json()

    def query_experiments(self, query_body):
        url = f"{self._base}/experiments-query"
        r = requests.post(url, json=query_body, headers=self._headers)
        logger.info(f"POST {url} -> {r.status_code}")
        if r.status_code == 200:
            return r.json()
        logger.error(f"Failed to query experiments: {r.text}")
        return []

    # ----- Workflows -----
    def create_workflow(self, exp_id, body):
        url = f"{self._base}/workflows"
        body = dict(body)
        body["experimentId"] = exp_id
        body["status"] = "scheduled"
        r = requests.put(url, json=body, headers=self._headers)
        logger.info(f"PUT {url} -> {r.status_code}")
        if r.status_code == 201:
            wf_id = r.json()['workflow_id']
            logger.info(f"New workflow created id={wf_id}")
            return wf_id
        logger.error(r.text)
        return None

    def get_workflow(self, wf_id):
        url = f"{self._base}/workflows/{wf_id}"
        r = requests.get(url, headers=self._headers)
        logger.info(f"GET {url} -> {r.status_code}")
        return r.json().get('workflow')

    def update_workflow(self, wf_id, body):
        url = f"{self._base}/workflows/{wf_id}"
        r = requests.post(url, json=body, headers=self._headers)
        logger.info(f"POST {url} -> {r.status_code}")
        return r.json()

    # ----- Metrics -----
    def create_metric(self, wf_id, task, name, semantic_type, kind, data_type):
        body = {
            "name": name,
            "producedByTask": task,
            "type": data_type,
            "kind": kind,
            "parent_id": wf_id,
            "parent_type": "workflow"
        }
        if semantic_type:
            body["semantic_type"] = semantic_type
        url = f"{self._base}/metrics"
        r = requests.put(url, json=body, headers=self._headers)
        logger.info(f"PUT {url} -> {r.status_code}")
        if r.status_code != 201:
            logger.error(r.text)

    def update_metric(self, m_id, body):
        url = f"{self._base}/metrics/{m_id}"
        r = requests.post(url, json=body, headers=self._headers)
        logger.info(f"POST {url} -> {r.status_code}")
        return r.json()

    def add_value_to_metric(self, m_id, value):
        return self.update_metric(m_id, {"value": str(value)})

    def add_data_to_metric(self, m_id, data):
        records = [{"value": d} for d in data]
        url = f"{self._base}/metrics-data/{m_id}"
        r = requests.put(url, json={"records": records}, headers=self._headers)
        logger.info(f"PUT {url} -> {r.status_code}")

    # ----- Helpers for workflow updates -----
    def update_metrics_of_workflow(self, wf_id, result):
        wf = self.get_workflow(wf_id)
        if not wf:
            return
        if "metrics" in wf:
            for m in wf["metrics"]:
                m_id = next(iter(m))
                name = m[m_id]["name"]
                if name in result:
                    value = result[name]
                    self.add_value_to_metric(m_id, value)
                else:
                    logger.debug(f"No value for metric {name}")

    def update_files_of_workflow(self, wf_id, result):
        wf = self.get_workflow(wf_id)
        if not wf:
            return
        file_keys = [key for key in result if key.startswith("file:")]
        tasks_updates = {}
        for k in file_keys:
            file_metadata_list = json.loads(result[k])
            file_keys_parts = k.split(":")
            task_name = file_keys_parts[1]
            input_or_output = file_keys_parts[2]
            file_key = file_keys_parts[3]
            task_dict = tasks_updates.get(task_name, {})
            tasks_updates[task_name] = task_dict
            if input_or_output == "input":
                inputs_or_outputs_dict = task_dict.get("inputs", {})
                task_dict["inputs"] = inputs_or_outputs_dict
            else:
                inputs_or_outputs_dict = task_dict.get("outputs", {})
                task_dict["outputs"] = inputs_or_outputs_dict
            inputs_or_outputs_dict[file_key] = file_metadata_list
        new_tasks = []
        for task in wf.get("tasks", []):
            new_tasks.append(task)
            task_name = task["name"]
            task_update = tasks_updates.get(task_name, {})
            if "inputs" in task_update:
                new_input_datasets = []
                for d in task.get("input_datasets", []) or []:
                    new_input_datasets += self._create_new_dataset_entry(d, task_update, "inputs")
                task["input_datasets"] = new_input_datasets
            if "outputs" in task_update:
                new_output_datasets = []
                for d in task.get("output_datasets", []) or []:
                    new_output_datasets += self._create_new_dataset_entry(d, task_update, "outputs")
                task["output_datasets"] = new_output_datasets
        self.update_workflow(wf_id, {"tasks": new_tasks})

    def _create_new_dataset_entry(self, d, task_update, inputs_or_outputs):
        file_name = d["name"]
        if inputs_or_outputs not in task_update:
            return []
        updates = task_update[inputs_or_outputs]
        datasets = []
        if file_name in updates:
            update_metadata_list = updates[file_name]
            for update_metadata in update_metadata_list:
                new_d = d.copy()
                new_d["uri"] = update_metadata["file_url"]
                new_metadata = new_d.get("metadata", {}).copy()
                new_d["metadata"] = new_metadata
                new_metadata["file_name"] = update_metadata["file_name"]
                new_metadata["project_id"] = update_metadata["project_id"]
                new_metadata["file_type"] = update_metadata["file_type"]
                datasets.append(new_d)
        return datasets

    @staticmethod
    def get_current_time():
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
