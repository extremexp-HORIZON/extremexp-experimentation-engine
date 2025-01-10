
import requests


def get_workflow(wf_id, data_abstraction_base_url, data_abstraction_access_token):
    url = f"{data_abstraction_base_url}/workflows/{wf_id}"
    r = requests.get(url, headers={'access-token': data_abstraction_access_token})
    return r.json()['workflow']


def update_workflow_with_status(wf_id, data_abstraction_base_url, data_abstraction_access_token):
    new_status = "running"
    print(f"Changing status of workflow with id {wf_id} to {new_status}")
    url = f"{data_abstraction_base_url}/workflows/{wf_id}"
    wf = get_workflow(wf_id, data_abstraction_base_url, data_abstraction_access_token)
    wf["status"] = new_status
    r = requests.post(url, json=wf, headers={'access-token': data_abstraction_access_token})
    return r.json()


wf_id = variables.get("wf_id")
data_abstraction_base_url = variables.get("data_abstraction_base_url")
data_abstraction_access_token = variables.get("data_abstraction_access_token")

update_workflow_with_status(wf_id, data_abstraction_base_url, data_abstraction_access_token)
