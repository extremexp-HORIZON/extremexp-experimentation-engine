# ExpEngine Service

The **ExpEngine Service** provides a RESTful API interface for managing experiments and workflows remotely. This service allows you to run, control, and monitor the execution proccess of experiments through HTTP requests, making it ideal for integration with web applications, CI/CD pipelines, or remote experiment management.

## Overview

The ExpEngine Service runs as a FastAPI-based web service that exposes endpoints for:

- **Starting experiments** asynchronously with queuing support
- **Managing experiment lifecycle** (status, pause, resume, kill)
- **Managing workflow lifecycle** (pause, resume, kill)
- **Monitoring experiment queue** and execution status
- **Retrieving error logs** for failed experiments
- **Cross-origin resource sharing (CORS)** support for web applications
- **User-scoped workspaces** for multi-tenant deployments

## Key Features

### Asynchronous Execution
Experiments are submitted to a queue and executed in the background, allowing multiple concurrent experiments with configurable limits.

### User Isolation
Each user can have their own workspace with isolated experiment libraries, task definitions, and dataset storage.

### Queue Management
- Configurable maximum concurrent experiments (default: 4)
- Automatic queuing when capacity is reached
- Queue position tracking
- Graceful experiment cancellation

### Error Logging
Failed experiments persist error logs with stack traces for debugging, with automatic cleanup after 15 minutes.

## API Documentation

!!swagger openapi.yaml!!

## Service Configuration

### Prerequisites

- Python >= 3.10
- FastAPI and Uvicorn
- ExpEngine package installed (`pip install eexp_engine`)
- Properly configured `eexp_config.py` file

### Configuration Requirements

The service requires the following configuration to be set in `eexp_config.py` as well:

```python
# Required: Base workspace directory for user-scoped files
WORKSPACE_ROOT = '/path/to/workspace'

# Optional: Experiment queue settings
MAX_EXPERIMENTS_IN_PARALLEL = 4  # Default: 4
```

!!! info "WORKSPACE_ROOT Configuration"
    When running as a service, `WORKSPACE_ROOT` defines the base directory where user-specific subdirectories will be created:
    ```
    WORKSPACE_ROOT/
    ├── user1/
    │   ├── experiments/
    │   ├── tasks/
    │   ├── datasets/
    │   └── dependencies/
    └── user2/
        ├── experiments/
        ├── tasks/
        ├── datasets/
        └── dependencies/
    ```

### Starting the Service

The service runs on `http://localhost:5556` by default with Uvicorn.

```bash
# Direct execution
python api.py

# Or with custom host/port
python api.py --host 0.0.0.0 --port 8000
```

### Docker Deployment

The recommended way to deploy the service is using Docker:

```bash
# Using docker-compose
docker-compose up -d

# Or using the pre-built image
docker pull ghcr.io/extremexp-horizon/exp-engine:latest
docker run -d -p 5556:5556 \
  -v $(pwd)/eexp_config.py:/app/eexp_config.py \
  -v $(pwd)/workspace:/workspace \
  ghcr.io/extremexp-horizon/exp-engine:latest
```

## Error Handling

The API returns standardized error responses in JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "exp_name": "ExperimentName",
    "details": {}
  }
}
```

**Error Codes:**

- `NOT_FOUND` - Experiment or workflow not found
- `SPEC_NOT_FOUND` - Experiment specification file not found in user's workspace
- `INTERNAL_ERROR` - Server-side error during execution
- `BAD_REQUEST` - Invalid request parameters

For failed experiments, the status endpoint includes error logs with stack traces for debugging (logs are retained for 15 minutes).