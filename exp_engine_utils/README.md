# eexp_engine_utils

Helper utilities for the ExtremeXP Experimentation Engine that automatically adapt to different execution environments (Kubeflow, ProActive, Local).

## Overview

This package provides a **transparent proxy** that automatically routes function calls to the appropriate implementation based on your execution environment. No more manual environment checking or conditional imports!

## Installation

```bash
pip install eexp_engine_utils
```

## Quick Start

```python
from eexp_engine_utils import utils

# Load a dataset
data = utils.load_dataset(variables, resultMap, "input_data")

# Process your data
processed_data = your_processing_function(data)

# Save the result
utils.save_dataset(variables, resultMap, "output_data", processed_data)
```

That's it! The `utils` proxy automatically detects your execution environment and routes calls to the correct implementation.

## Available Functions

### Dataset Management
- `load_dataset(variables, resultMap, key)` - Load a single dataset
- `load_datasets(variables, resultMap, key)` - Load multiple datasets
- `save_dataset(variables, resultMap, key, value)` - Save a single dataset
- `save_datasets(variables, resultMap, key, values, file_names)` - Save multiple datasets

### Helpers
- `get_experiment_results(variables)` - Get experiment results
- `load_dataset_by_path(file_path)` - Load from specific path
- `load_pickled_dataset_by_path(file_path)` - Load pickled data

## Requirements

- Python >= 3.8
- requests >= 2.25.0
- fsspec >= 2021.0.0
- s3fs >= 2021.0.0
- minio >= 7.0.0

## License

Apache License 2.0

## Links

- Homepage: https://github.com/extremexp-HORIZON/extremexp-experimentation-engine
- Issues: https://github.com/extremexp-HORIZON/extremexp-experimentation-engine/issues
