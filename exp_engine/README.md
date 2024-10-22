# ExtremeXP Experimentation Engine (eexp_engine)

This is a Python module for interfacing with the experimentation engine built in the [ExtremeXP](https://extremexp.eu) EU project. 

## Instructions
1. Install the module (in development mode) via ```pip install -e <relative path to exp_engine folder>``` or grab the 
latest stable version on PyPI via ```pip install eexp_engine```.

2. Add your credentials and library paths to the ```eexp_config.py``` file. 

3. Use the module in a Python file:
    ```
    from eexp_engine import runner
    import eexp_config

    runner.run(__file__, <exp_name>, eexp_config)
    ```
