from eexp_engine import client
import eexp_config

# exp_name = 'IDEKO_main'
exp_name = 'user_interaction_example'
# exp_name = 'moby-exp1'
client.run(__file__, exp_name, eexp_config)
