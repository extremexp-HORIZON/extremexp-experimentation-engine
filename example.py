from eexp_engine import client
import eexp_config

# exp_name = 'IDEKO_main'
# exp_name = 'parallel_nodes'
# exp_name = 'complex_control1'
# exp_name = 'moby-exp1'
# exp_name = 'user_interaction_in_experiment'
# exp_name = 'user_interaction_in_workflow'
exp_name = 'test_ddm'
# exp_name = 'test_ddm_folders'
# exp_name = 'test_local'

client.run(__file__, exp_name, eexp_config)
