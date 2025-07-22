# ExtremeXP Kubeflow Converter

A converter for transforming ExtremeXP .xxp DSL files into Kubeflow Pipelines.

## Installation

### Install Dependencies

```bash
pip install kfp>=2.0.0 click>=8.0.0 pyyaml>=6.0
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Convert a .xxp file to Kubeflow Pipeline

```bash
python xxp_to_kubeflow.py convert experiment.xxp --output ./pipelines
```

With custom configuration:

```bash
python xxp_to_kubeflow.py convert experiment.xxp --output ./pipelines --config eexp_config.py
```

#### Validate setup

```bash
python xxp_to_kubeflow.py validate --check-kfp --check-config
```

#### Install dependencies

```bash
python xxp_to_kubeflow.py install-deps
```

#### Submit pipeline to Kubeflow

```bash
python xxp_to_kubeflow.py submit pipeline.yaml --endpoint http://your-kubeflow-endpoint
```

### Programmatic Usage

```python
from eexp_engine.kubeflow import KubeflowConverter
import eexp_config

# Create converter
converter = KubeflowConverter(eexp_config)

# Read .xxp file
with open('experiment.xxp', 'r') as f:
    xxp_content = f.read()

# Convert to Kubeflow Pipeline
converter.convert_xxp_to_kubeflow(xxp_content, './output/pipelines')
```

## Features

- **Seamless Integration**: Reuses existing ExtremeXP parsing infrastructure
- **Task Conversion**: Converts ExtremeXP tasks to Kubeflow ContainerOps
- **Data Flow**: Preserves input/output data dependencies between tasks
- **Script Adaptation**: Automatically adapts ProActive-specific code for Kubeflow
- **Dependency Management**: Maintains task execution order and dependencies
- **Configuration Support**: Uses existing ExtremeXP configuration files

## Architecture

The converter consists of several key components:

1. **converter.py**: Main conversion logic
2. **kubeflow_helper.py**: Kubeflow equivalents of ProActive helper functions
3. **cli.py**: Command-line interface
4. **xxp_to_kubeflow.py**: Standalone script

## Generated Files

The converter generates:

1. **Pipeline YAML**: Compiled Kubeflow Pipeline specification
2. **Python Pipeline**: Editable Python file with pipeline definition
3. **Helper Functions**: Kubeflow-compatible helper functions

## Adaptation Process

The converter automatically adapts ProActive-specific code:

- Replaces `proactive_helper` imports with Kubeflow equivalents
- Converts `variables.get()` calls to `os.environ.get()`
- Adapts data loading/saving functions
- Maintains script functionality in Kubeflow environment

## Examples

See the `examples/` directory for sample .xxp files and their converted Kubeflow Pipelines.

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Run `python xxp_to_kubeflow.py install-deps`
2. **Configuration Not Found**: Specify config with `--config` option
3. **Import Errors**: Ensure you're in the correct directory

### Debug Mode

Enable verbose logging:

```bash
python xxp_to_kubeflow.py convert experiment.xxp --verbose
```
