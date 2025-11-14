# Proactive ExecutionWare

Proactive ExecutionWare provides a distributed execution environment for workflows running on cloud infrastructure and computing clusters. It supports both local file storage and distributed data management through DDM (Distributed Data Management).

## Overview

Proactive ExecutionWare is designed for production deployments and large-scale experiments. It provides robust data management, distributed storage capabilities, and integration with cloud platforms. The system can handle both traditional file-based workflows and modern distributed data scenarios.

## Configuration

Proactive ExecutionWare internally uses runtime configuration files that contain execution metadata and data management settings.

### Data Management Modes

#### LOCAL Mode

- Uses local filesystem for data storage
- Similar to Local ExecutionWare but with Proactive infrastructure
- Set `DATASET_MANAGEMENT: "LOCAL"`

#### DDM Mode

- Uses distributed data management
- Supports cloud storage and distributed computing
- Set `DATASET_MANAGEMENT: "DDM"`

## Helper Functions

Import the proactive helper module in your tasks:
```python
import proactive_helper as ph
```

### Data Loading Functions

#### load_dataset()
Load a single dataset:
```python
dataset = ph.load_dataset(variables, resultMap, "input_key")
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
datasets = ph.load_datasets(variables, resultMap, "input_key")
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
ph.save_dataset(variables, resultMap, "output_key", data)
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping for tracking data flow
- `key`: Data key for saving
- `value`: Data to save

#### save_datasets()
Save multiple datasets with optional filenames:
```python
ph.save_datasets(variables, resultMap, "output_key", 
                [data1, data2], 
                ['file1.csv', 'file2.csv'])
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping for tracking data flow
- `key`: Data key for saving
- `values`: List of data to save
- `file_names`: Optional list of filenames

### Directory Management

#### create_dir()
Create a directory for intermediate files:
```python
folder_path = ph.create_dir(variables, "subfolder_name")
```

#### get_file_path()
Get a file path within a configured directory:
```python
file_path = ph.get_file_path(variables, "data_folder_key", "filename.csv")
```

### Utility Functions

#### get_experiment_results()
Load experiment results from previous runs:
```python
results = ph.get_experiment_results()
```

#### load_dataset_by_path()
Load data directly from a file path:
```python
data = ph.load_dataset_by_path("/path/to/file.csv")
```

### File Upload and Download

#### Upload Process

1. Data is converted to bytes
2. Metadata is created with task and workflow information
3. Files are uploaded to DDM storage
4. File URLs and metadata are stored in resultMap

#### Download Process

1. File catalog is searched based on project and filename
2. Files are downloaded from DDM storage
3. Content is returned as bytes
4. Metadata is tracked in resultMap

## Task Implementation Examples

### Basic Data Processing Task
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import proactive_helper as ph
import pandas as pd

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

# Load input data
print("Loading dataset...")
dataset_bytes = ph.load_dataset(variables, resultMap, "dataset")

# Convert bytes to DataFrame
dataset = pd.read_csv(BytesIO(dataset_bytes))

# Process the data
processed_data = dataset.dropna()

# Convert back to bytes
output_bytes = processed_data.to_csv(index=False).encode('utf-8')

# Save output data
ph.save_dataset(variables, resultMap, "processed_data", output_bytes)

print("Task completed successfully!")
```

### Advanced ML Task with Multiple Outputs
```python
import os
import sys
import proactive_helper as ph
import pandas as pd
import pickle
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

# Load training data
train_data_bytes = ph.load_dataset(variables, resultMap, "train_data")
test_data_bytes = ph.load_dataset(variables, resultMap, "test_data")

# Convert to DataFrames
train_df = pd.read_csv(BytesIO(train_data_bytes))
test_df = pd.read_csv(BytesIO(test_data_bytes))

# Prepare features and labels
X_train = train_df.drop('label', axis=1)
y_train = train_df['label']
X_test = test_df.drop('label', axis=1)
y_test = test_df['label']

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

# Prepare outputs
model_bytes = pickle.dumps(model)
predictions_df = pd.DataFrame(predictions, columns=['predictions'])
predictions_bytes = predictions_df.to_csv(index=False).encode('utf-8')

# Create results metadata
results = {
    "accuracy": accuracy,
    "n_estimators": 100,
    "test_size": len(test_df)
}
results_bytes = json.dumps(results).encode('utf-8')

# Save multiple outputs
ph.save_datasets(variables, resultMap, "ml_outputs", 
                [model_bytes, predictions_bytes, results_bytes],
                ['model.pkl', 'predictions.csv', 'results.json'])

print(f"Model trained with accuracy: {accuracy:.4f}")
```

### Task with DDM
```python
import os
import sys
import proactive_helper as ph
import pandas as pd
import json
from io import BytesIO

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

def format_bytes(bytes_size):
    """Convert bytes to human readable format."""
    for unit in ['bytes', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def df_to_csv_bytes(df):
    """Convert DataFrame to CSV bytes."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    size_str = format_bytes(len(csv_bytes))
    print(f"DataFrame converted to CSV: {size_str}")
    return csv_bytes

# Load model and data
print("Loading model and test data...")
model_data = ph.load_dataset(variables, resultMap, "trained_model")
test_data = ph.load_dataset(variables, resultMap, "test_data")

# Deserialize model
model = pickle.loads(model_data)

# Convert test data to DataFrame
test_df = pd.read_csv(BytesIO(test_data))

# Prepare data
test_labels = test_df[['label']]
test_features = test_df.drop(['label'], axis=1)

# Make predictions
predictions = model.predict(test_features)
predictions_df = pd.DataFrame(predictions, columns=['predictions'])

# Calculate probabilities for ROC analysis
probabilities = model.predict_proba(test_features)
from sklearn.metrics import roc_curve, roc_auc_score

fpr, tpr, thresholds = roc_curve(test_labels, probabilities[:, 1])
auc = roc_auc_score(test_labels, probabilities[:, 1])

# Create ROC data
roc_data = {
    "fpr": [round(x, 4) for x in fpr.tolist()],
    "tpr": [round(x, 4) for x in tpr.tolist()],
    "thresholds": [round(x, 4) for x in thresholds.tolist()],
    "auc": round(auc, 4)
}

# Prepare outputs for DDM
outputs = [
    df_to_csv_bytes(test_features),
    df_to_csv_bytes(test_labels),
    df_to_csv_bytes(predictions_df),
    json.dumps(roc_data).encode('utf-8'),
    pickle.dumps(model)
]

filenames = [
    'X_test.csv',
    'y_test.csv',
    'predictions.csv',
    'roc_data.json',
    'model.pkl'
]

print("Uploading results to DDM...")
ph.save_datasets(variables, resultMap, "analysis_results", outputs, filenames)

print(f"Analysis complete. AUC: {auc:.4f}")
```

## Integration with Workflow DSL

### Traditional File-based Workflows
```dsl
workflow DataProcessingWorkflow {
  START -> ReadData -> ProcessData -> SaveResults -> END;
  
  task ReadData {
    implementation "tasks/read_data";
  }
  
  task ProcessData {
    implementation "tasks/process_data";
  }
  
  task SaveResults {
    implementation "tasks/save_results";
  }
  
  define input data InputFile;
  define output data OutputFile;
  
  configure data InputFile {
    path "data/input.csv";
  }
  
  configure data OutputFile {
    path "results/output.csv";
  }
  
  InputFile --> ReadData.input_data;
  ReadData.processed_data --> ProcessData.input_data;
  ProcessData.final_data --> SaveResults.input_data;
  SaveResults.output_data --> OutputFile;
}
```

### DDM Workflows
```dsl
workflow DDMDataProcessingWorkflow {
  START -> ReadData -> ProcessData -> SaveResults -> END;
  
  task ReadData {
    implementation "tasks/read_data";
  }
  
  task ProcessData {
    implementation "tasks/process_data";
  }
  
  task SaveResults {
    implementation "tasks/save_results";
  }
  
  define input data InputFile;
  define output data OutputFile;
  
  configure data InputFile {
    name "input_dataset.csv";
    project "ml_experiment_project";
  }
  
  configure data OutputFile {
    project "ml_experiment_results";
  }
  
  InputFile --> ReadData.input_data;
  ReadData.processed_data --> ProcessData.input_data;
  ProcessData.final_data --> SaveResults.input_data;
  SaveResults.output_data --> OutputFile;
}
```

???+ info

    When using DDM, the workflow DSL configuration changes:
    
    ### Single File Input
    ```dsl
    define input data InputFile;
    configure data InputFile {
      name "titanic.json";
      project "demo_project";
    }
    ```
    
    ### Directory Input
    ```dsl
    define input data InputFile;
    configure data InputFile {
      project "demo_project";
    }
    ```

Proactive ExecutionWare provides the flexibility to handle both traditional file-based workflows and modern distributed data management scenarios, making it suitable for a wide range of computational experiments and production deployments.