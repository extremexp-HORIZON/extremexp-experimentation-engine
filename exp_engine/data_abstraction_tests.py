from data_abstraction_layer.data_abstraction_api import *

# r = get_all_experiments()
# import pprint as pp
# pp.pprint(r)
# print(f"There are {len(r)} executed experiments so far.")


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


m_id = create_series_metric(wf_id, "CPU Load")
print(m_id)


data = [11, 99, 17]
add_data_to_metric(m_id, data)

body = {
    "value": "120",
    "type": "scalar"
}
update_metric(m_id, body)

add_value_to_metric(m_id, 130)

results = {
    'CPU Load': 0.5,
}
update_metrics_of_workflow(wf_id, results)
