from eexp_engine import client
import eexp_config
from pathlib import Path


if __name__ == "__main__":
    base_path = Path.cwd() / eexp_config.EXPERIMENT_LIBRARY_PATH

    print(base_path)
    experiment_file = base_path / "/tests/simple_configurations/demo_wp5.xxp"
    experiment_name = "tests/simple_configurations/demo_wp5"

    client.run(experiment_file, experiment_name, eexp_config)
