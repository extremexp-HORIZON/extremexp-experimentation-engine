from eexp_engine import client
from eexp_engine.runner import select_file
import eexp_config

if __name__ == "__main__":
    selected_file, exp_name = select_file()
    if selected_file and exp_name:
        client.run(selected_file, exp_name, eexp_config)
