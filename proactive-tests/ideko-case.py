from proactive_interface import *
import credentials

gateway = create_gateway_and_connect_to_it(credentials.proactive_username, credentials.proactive_password)

job = create_job(gateway, "IDEKO")

fork_env = create_fork_env(gateway, job)

# input_data_folder = "library-datasets/ideko"
input_data_folder = "library-datasets/ideko-subset"
tasks_folder = "tasks/IDEKO/"
tasks_folder_src_all = tasks_folder + "src/**"

read_data_task = create_python_task(gateway, "read_data", fork_env, tasks_folder + 'read_data.py', [input_data_folder+"/**", tasks_folder_src_all])
add_padding_task = create_python_task(gateway, "add_padding", fork_env, tasks_folder + 'add_padding.py', [tasks_folder_src_all], [read_data_task])
split_data_task = create_python_task(gateway, "split_data", fork_env, tasks_folder + 'split_data.py', [tasks_folder_src_all], [add_padding_task])
train_nn = create_python_task(gateway, "train_nn", fork_env, tasks_folder + 'train_nn.py', [tasks_folder_src_all], [split_data_task])
train_rn = create_python_task(gateway, "train_rnn", fork_env, tasks_folder + 'train_rnn.py', [tasks_folder_src_all], [split_data_task])

configure_task(read_data_task, {"text_to_print":"hello world!"})

print("Adding tasks to the job...")
job.addTask(read_data_task)
job.addTask(add_padding_task)
job.addTask(split_data_task)
# job.addTask(train_nn)
job.addTask(train_rn)

print("Tasks added.")

print("Submitting the job to the proactive scheduler...")
# job_id = gateway.submitJob(job, debug=False)
job_id = gateway.submitJobWithInputsAndOutputsPaths(job, debug=False)
print("job_id: " + str(job_id))

print("Getting job results...")
job_result = gateway.getJobResult(job_id)
print(job_result)

print("Getting job outputs...")
job_outputs = gateway.printJobOutput(job_id)
print(job_outputs)

teardown(gateway)
