from . import parsing
from .execution import Execution


def run_experiment(exp_id, experiment_specification, runner_folder, config):
    parsing.CONFIG = config

    print("*********************************************************")
    print("***************** PARSE WORKFLOWS ***********************")
    print("*********************************************************")
    parsed_workflows, task_dependencies = parsing.parse_workflows(experiment_specification)

    print("*********************************************************")
    print("********** PARSE ASSEMBLED WORKFLOWS DATA ***************")
    print("*********************************************************")
    assembled_workflows_data = parsing.parse_assembled_workflow_data(experiment_specification)

    assembled_flat_wfs = []
    if assembled_workflows_data:
        print("*********************************************************")
        print("************ GENERATE ASSEMBLED WORKFLOWS ***************")
        print("*********************************************************")
        assembled_wfs = parsing.generate_final_assembled_workflows(parsed_workflows, assembled_workflows_data)
        for wf in assembled_wfs:
            wf.print()

        print("*********************************************************")
        print("********** GENERATE ASSEMBLED FLAT WORKFLOWS ************")
        print("*********************************************************")
        parsing.generate_assembled_flat_workflows(assembled_wfs, assembled_flat_wfs)

    print("*********************************************************")
    print("************** EXPERIMENT SPECIFICATION *****************")
    print("*********************************************************")
    nodes, automated_dict, spaces, automated_events, parsed_automated_events, \
    manual_events, parsed_manual_events, space_configs = \
        parsing.generate_experiment_specification(experiment_specification)

    print("\n*********************************************************")
    print("***************** RUNNING WORKFLOWS ***********************")
    print("*********************************************************")
    execution = Execution(exp_id, nodes, automated_dict, spaces,
                          automated_events, parsed_automated_events,
                          manual_events, parsed_manual_events,
                          space_configs, assembled_flat_wfs,
                          runner_folder, config)
    execution.start()
