from eexp_engine import client
import eexp_config

if __name__ == "__main__":
    experiment_name = "tests/simple_configurations/exp_test_wp5"
    client.run(__file__, experiment_name, eexp_config)