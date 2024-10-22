# ExtremeXP Experimentation Engine

Allows the specification and execution of ExtremeXP experiments, 
including interactions with data storage and database backends and users.  

## Instructions
```
python3 -m venv env
source ./env/bin/activate
python3 -m pip install --upgrade pip setuptools wheel python-dotenv
```
and then either install the latest version published to PyPI via
```
pip install eexp_engine
```
or install from sources ("development" installation) via
```
pip install -e exp_engine
```

#### Deprecated Instructions (to clean up)
(See email from Caroline Pacheco on 31.12.2023)
```
python3 -m venv env
source ./env/bin/activate
python3 -m pip install --upgrade pip setuptools wheel python-dotenv
pip install --upgrade --pre proactive
cd exp_engine
pip install -r requirements.txt
```

## Configure credentials
1. Create `eexp_config.py` file via copying the template, e.g. by:
    ```
    cp eexp_config_TEMPLATE.py eexp_config.py
    ``` 
2. Verify that the `eexp_config.py` is git ignored (check `.gitignore`)
3. Add/modify the necessary paths in the config file. 
4. Add your proactive account name and password to the config file.
5. Add your data abstraction layer access token to the config file.

## Test
This should run a single workflow of the IDEKO case.
```
python example.py
```

## Notes
The `exp_config/src/eexp_config/scripts` folder is copied over for convenience from the `proactive-python-client` project. 

## Instructions for publishing Python module to PyPI
1. Build via 
```
python -m build
```
2. Deploy via 
```
python -m twine upload dist/*
```
