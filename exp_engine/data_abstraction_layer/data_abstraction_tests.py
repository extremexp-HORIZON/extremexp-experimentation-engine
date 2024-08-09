from data_abstraction_api import *

r = get_all_experiments()
import pprint as pp
pp.pprint(r)
print(f"There are {len(r)} executed experiments so far.")


new_exp = {
    "name": "Experiment from Python - testing1",
    "intent": "example intent"
}
exp_id = create_experiment(new_exp)


r = get_experiment(exp_id)
print(r)


data = {
    "status": "running"
}
r = update_experiment(exp_id, data)
print(r)


body = {
    "name": "w1",
}
wf_id = create_workflow(exp_id, body)

r = get_workflow(wf_id)
print(r)


data = {
    "name": "w1-v2"
}
r = update_workflow(wf_id, data)
print(r)


r = get_workflow(wf_id)
print(r)
