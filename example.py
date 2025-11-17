import eexp_config
from exp_engine.src.eexp_engine import client

# exp_name = 'IDEKO_main'
# exp_name = 'IDEKO_example'
# exp_name = 'parallel_nodes'
# exp_name = 'complex_control1'
# exp_name = 'moby-exp1'
# exp_name = 'user_interaction_in_experiment'
# exp_name = 'user_interaction_in_workflow'
# exp_name = 'user_interaction_in_experiment'
# exp_name = 'test_ddm_folders'
exp_name = 'test_local'
# exp_name = 'tests/simple_configurations/demo_wp5'
# exp_name = 'tests/advanced_configurations/complex_experiment_control'
# exp_name = 'tests/advanced_configurations/space_configuration_validation'

if __name__ == "__main__":
    client.run(__file__, exp_name, eexp_config)
