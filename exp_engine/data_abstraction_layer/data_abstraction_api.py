import requests
import data_abstraction_layer.data_abstraction_config as config
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_all_experiments():
    url = f"{config.BASE_URL}/executed-experiments"
    r = requests.get(url, headers=config.HEADERS)
    print(f"GET request to {url} return status code: {r.status_code}")
    return r.json()['executed_experiments']


def create_experiment(body):
    url = f"{config.BASE_URL}/executed-experiments"
    r = requests.put(url, json=body, headers=config.HEADERS)
    logger.info(f"PUT request to {url} return status code: {r.status_code}")
    if r.status_code == 201:
        exp_id = r.json()['message']['experimentId']
        print(f"New experiment created with id {exp_id}")
        return exp_id
    else:
        return "something went wrong when creating experiment"


def get_experiment(exp_id):
    url = f"{config.BASE_URL}/executed-experiments/{exp_id}"
    r = requests.get(url, headers=config.HEADERS)
    print(f"GET request to {url} return status code: {r.status_code}")
    return r.json()['experiment']


def update_experiment(exp_id, body):
    url = f"{config.BASE_URL}/executed-experiments/{exp_id}"
    r = requests.post(url, json=body, headers=config.HEADERS)
    print(f"POST request to {url} return status code: {r.status_code}")
    return r.json()


def create_workflow(exp_id, body):
    url = f"{config.BASE_URL}/executed-workflows"
    body["experimentId"] = exp_id
    r = requests.put(url, json=body, headers=config.HEADERS)
    print(f"PUT request to {url} return status code: {r.status_code}")
    if r.status_code == 201:
        wf_id = r.json()['workflowId']
        print(f"New workflow created with id {wf_id}")
        return wf_id
    else:
        print(r.json())
        return "something went wrong when creating experiment"


def get_workflow(wf_id):
    url = f"{config.BASE_URL}/executed-workflows/{wf_id}"
    r = requests.get(url, headers=config.HEADERS)
    print(f"GET request to {url} return status code: {r.status_code}")
    return r.json()['workflow']


def update_workflow(wf_id, body):
    url = f"{config.BASE_URL}/executed-workflows/{wf_id}"
    r = requests.post(url, json=body, headers=config.HEADERS)
    print(f"POST request to {url} return status code: {r.status_code}")
    return r.json()
