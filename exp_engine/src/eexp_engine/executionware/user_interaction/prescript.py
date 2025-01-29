
import requests


def get_external_ip_and_port():
    try:
        # Use an external service to fetch the external IP address
        response = requests.get('https://ifconfig.me')
        if response.status_code == 200:
            return response.text.strip() + ":5000"
        else:
            return f"Failed to fetch IP. Status code: {response.status_code}"
    except Exception as e:
        return f"Error fetching IP: {e}"


def get_workflow(wf_id, data_abstraction_base_url, data_abstraction_access_token):
    url = f"{data_abstraction_base_url}/workflows/{wf_id}"
    r = requests.get(url, headers={'access-token': data_abstraction_access_token})
    return r.json()['workflow']


def update_workflow_with_status_and_external_ip(wf_id, task_name, data_abstraction_base_url, data_abstraction_access_token, URL):
    new_status = "pending_input"
    print(f"Changing status of workflow with id {wf_id} to {new_status}")
    print(f"Adding {URL} to workflow with id {wf_id}")
    url = f"{data_abstraction_base_url}/workflows/{wf_id}"
    wf = get_workflow(wf_id, data_abstraction_base_url, data_abstraction_access_token)
    tasks = wf["tasks"]
    for t in tasks:
        if t["name"]==task_name:
            t["metadata"]["URL"] = URL
    updates = {"status": new_status, "tasks": tasks}
    try:
        r = requests.post(url, json=updates, headers={'access-token': data_abstraction_access_token})
        return r.json()
    except Exception as e:
        return f"Error updating workflow: {e}"


wf_id = variables.get("wf_id")
task_name = variables.get("task_name")
data_abstraction_base_url = variables.get("data_abstraction_base_url")
data_abstraction_access_token = variables.get("data_abstraction_access_token")
URL = get_external_ip_and_port()

update_workflow_with_status_and_external_ip(wf_id, task_name, data_abstraction_base_url, data_abstraction_access_token, URL)
