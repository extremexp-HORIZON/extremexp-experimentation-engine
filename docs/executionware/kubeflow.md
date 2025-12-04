# Kubeflow ExecutionWare

Kubeflow ExecutionWare provides a cloud-native execution environment for workflows running on Kubernetes clusters. It leverages Kubeflow Pipelines for orchestration and MinIO for artifact storage, making it ideal for large-scale, distributed experiments in cloud and on-premise Kubernetes deployments.

## Overview

Kubeflow ExecutionWare transforms workflows into Kubeflow Pipelines, where each task becomes a containerized pipeline component. It provides robust resource management, scalability, and integration with the Kubernetes ecosystem.

## Configuration

Kubeflow ExecutionWare requires the following configuration in `eexp_config.py`:

```python
EXECUTIONWARE = "KUBEFLOW"
KUBEFLOW_URL = "http://your-kubeflow-server"
KUBEFLOW_USERNAME = "your-username"
KUBEFLOW_PASSWORD = "your-password"
KUBEFLOW_MINIO_ENDPOINT = "your-minio-endpoint:9000"
KUBEFLOW_MINIO_USERNAME = "minio-user"
KUBEFLOW_MINIO_PASSWORD = "minio-password"
```

### Data Management Modes

#### MinIO S3 Storage (Default)

- Uses MinIO for artifact and intermediate file storage
- Automatic bucket creation and lifecycle management
- S3-compatible API for data access
- Supports large dataset handling

#### DDM Integration

- Optional distributed data management via DDM
- Seamless integration with other ExtremeXP components
- Set `DATASET_MANAGEMENT: "DDM"` for distributed datasets

## Helper Functions

Import the utilities in your tasks:
```python
from eexp_engine_utils import utils
```

!!! info "Universal Interface"
    The `utils` module automatically detects the ExecutionWare backend and routes function calls appropriately. The same import works for Local, Proactive, and Kubeflow ExecutionWare.

### Data Loading Functions

#### load_dataset()
Load a single dataset:
```python
dataset = utils.load_dataset(variables, resultMap, "input_key")
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping for tracking data flow
- `key`: Data key to load

**Returns:**

- Dataset content as bytes

#### load_datasets()
Load multiple datasets:
```python
datasets = utils.load_datasets(variables, resultMap, "input_key")
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping for tracking data flow
- `key`: Data key to load

**Returns:**

- List of dataset contents

### Data Saving Functions

#### save_dataset()
Save a single dataset:
```python
utils.save_dataset(variables, resultMap, "output_key", data)
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping for tracking data flow
- `key`: Data key for saving
- `value`: Data to save (will be uploaded to MinIO)

#### save_datasets()
Save multiple datasets with optional filenames:
```python
utils.save_datasets(variables, resultMap, "output_key",
                   [data1, data2],
                   ['file1.csv', 'file2.csv'])
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping for tracking data flow
- `key`: Data key for saving
- `values`: List of data to save
- `file_names`: Optional list of filenames

### Additional Helper Functions

#### get_experiment_results()
Load experiment results from previous runs:
```python
results = utils.get_experiment_results()
```

#### load_dataset_by_path()
Load data directly from a file path or MinIO URI:
```python
data = utils.load_dataset_by_path("s3://bucket/path/to/file.csv")
```

### MinIO-Specific Operations

When working with Kubeflow ExecutionWare, datasets are automatically:

- Uploaded to MinIO S3 storage
- Tagged with workflow and task metadata
- Accessible via S3-compatible URIs
- Cached for performance optimization

## Task Implementation Examples

### Basic Data Processing Task

```python
import os
import sys
from eexp_engine_utils import utils
import pandas as pd
from io import BytesIO

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

# Load input data
print("Loading dataset...")
dataset_bytes = utils.load_dataset(variables, resultMap, "dataset")

# Convert bytes to DataFrame
dataset = pd.read_csv(BytesIO(dataset_bytes))

# Process the data
print(f"Processing {len(dataset)} rows...")
processed_data = dataset.dropna()
processed_data['new_column'] = processed_data['existing_column'] * 2

# Convert back to bytes
output_bytes = processed_data.to_csv(index=False).encode('utf-8')

# Save output data (automatically uploaded to MinIO)
utils.save_dataset(variables, resultMap, "processed_data", output_bytes)

print(f"Saved {len(processed_data)} processed rows")
```

### ML Training Task with Model Artifacts

```python
import os
import sys
from eexp_engine_utils import utils
import pandas as pd
import pickle
import json
from io import BytesIO
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

# Load training and test data
print("Loading datasets...")
train_data_bytes = utils.load_dataset(variables, resultMap, "train_data")
test_data_bytes = utils.load_dataset(variables, resultMap, "test_data")

# Convert to DataFrames
train_df = pd.read_csv(BytesIO(train_data_bytes))
test_df = pd.read_csv(BytesIO(test_data_bytes))

# Prepare features and labels
X_train = train_df.drop('label', axis=1)
y_train = train_df['label']
X_test = test_df.drop('label', axis=1)
y_test = test_df['label']

# Train model
print("Training model...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42
)
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
report = classification_report(y_test, predictions, output_dict=True)

print(f"Model accuracy: {accuracy:.4f}")

# Serialize model
model_bytes = pickle.dumps(model)

# Create predictions output
predictions_df = pd.DataFrame({
    'actual': y_test,
    'predicted': predictions
})
predictions_bytes = predictions_df.to_csv(index=False).encode('utf-8')

# Create metrics output
metrics = {
    "accuracy": float(accuracy),
    "classification_report": report,
    "n_samples_train": len(train_df),
    "n_samples_test": len(test_df)
}
metrics_bytes = json.dumps(metrics, indent=2).encode('utf-8')

# Save all outputs to MinIO
utils.save_datasets(variables, resultMap, "ml_outputs",
                   [model_bytes, predictions_bytes, metrics_bytes],
                   ['model.pkl', 'predictions.csv', 'metrics.json'])

print("All artifacts saved to MinIO")
```

### Task with Large Dataset Processing

```python
import os
import sys
from eexp_engine_utils import utils
import pandas as pd
import numpy as np
from io import BytesIO

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

def process_chunk(chunk):
    """Process a chunk of data."""
    # Apply transformations
    chunk['processed'] = chunk['value'] * 2 + 10
    chunk['category'] = pd.cut(chunk['processed'], bins=5, labels=['A', 'B', 'C', 'D', 'E'])
    return chunk

# Load dataset
print("Loading large dataset...")
dataset_bytes = utils.load_dataset(variables, resultMap, "large_dataset")

# Process in chunks for memory efficiency
chunk_size = 10000
chunks = []

print("Processing data in chunks...")
for chunk in pd.read_csv(BytesIO(dataset_bytes), chunksize=chunk_size):
    processed_chunk = process_chunk(chunk)
    chunks.append(processed_chunk)

# Combine results
result_df = pd.concat(chunks, ignore_index=True)

print(f"Processed {len(result_df)} rows")

# Create summary statistics
summary = {
    "total_rows": len(result_df),
    "category_counts": result_df['category'].value_counts().to_dict(),
    "mean_processed": float(result_df['processed'].mean()),
    "std_processed": float(result_df['processed'].std())
}

# Save outputs
result_bytes = result_df.to_csv(index=False).encode('utf-8')
summary_bytes = json.dumps(summary, indent=2).encode('utf-8')

utils.save_datasets(variables, resultMap, "processing_outputs",
                   [result_bytes, summary_bytes],
                   ['processed_data.csv', 'summary.json'])

print("Processing complete")
```

## Pipeline Architecture

### Component Structure

Each task in a workflow becomes a Kubeflow Pipeline component with:

- **Container Image**: Python runtime with dependencies
- **Input Artifacts**: Datasets from MinIO or previous tasks
- **Output Artifacts**: Results uploaded to MinIO
- **Resource Limits**: Configurable CPU/memory limits
- **Environment Variables**: Workflow and task metadata

### Workflow Execution

1. **Pipeline Creation**: Workflow DSL → Kubeflow Pipeline specification
2. **Component Generation**: Each task → Kubernetes Pod
3. **Data Flow**: MinIO artifacts passed between components
4. **Monitoring**: Kubeflow UI tracks execution status
5. **Results Collection**: Exit handler aggregates outputs

### Resource Management

Configure resource limits in task specifications:

```dsl
task ModelTraining {
    implementation "ml/train_model";
    resources {
        cpu_limit "4";
        memory_limit "8Gi";
        cpu_request "2";
        memory_request "4Gi";
    }
}
```

## Integration with Workflow DSL

### Basic Workflow

```dsl
workflow DataPipelineWorkflow {
  START -> LoadData -> ProcessData -> SaveResults -> END;

  task LoadData {
    implementation "tasks/load_data";
    python_version "3.10";
  }

  task ProcessData {
    implementation "tasks/process_data";
    python_version "3.10";
  }

  task SaveResults {
    implementation "tasks/save_results";
    python_version "3.10";
  }

  define input data InputFile;
  define output data OutputFile;

  configure data InputFile {
    path "data/input.csv";
  }

  configure data OutputFile {
    path "results/output.csv";
  }

  InputFile --> LoadData.input_data;
  LoadData.loaded_data --> ProcessData.input_data;
  ProcessData.processed_data --> SaveResults.input_data;
  SaveResults.output_data --> OutputFile;
}
```

### ML Pipeline Workflow

```dsl
workflow MLPipelineWorkflow {
  START -> PrepareData -> TrainModel -> EvaluateModel -> END;

  task PrepareData {
    implementation "ml/prepare_data";
    python_version "3.10";
  }

  task TrainModel {
    implementation "ml/train_model";
    python_version "3.10";
  }

  task EvaluateModel {
    implementation "ml/evaluate_model";
    python_version "3.10";
  }

  define input data RawData;
  define output data ModelArtifacts;
  define output data EvaluationMetrics;

  configure data RawData {
    path "datasets/training_data.csv";
  }

  RawData --> PrepareData.raw_data;
  PrepareData.train_data --> TrainModel.training_data;
  PrepareData.test_data --> EvaluateModel.test_data;
  TrainModel.trained_model --> EvaluateModel.model;
  EvaluateModel.metrics --> EvaluationMetrics;
  TrainModel.model_file --> ModelArtifacts;
}
```
