from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from apiHandler import apiHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ExtremeXP Experimentation Engine API",
    description="API for running and managing experiments",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class RunExperimentRequest(BaseModel):
    exp_name: str
    username: str


class ExperimentResponse(BaseModel):
    id: str
    name: str
    status: str
    user: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    exp_name: Optional[str] = None


# ============================================================================
# Experiment Execution Endpoints
# ============================================================================

@app.post("/exp/run")
async def run_experiment(request: RunExperimentRequest):
    """
    Run a new experiment asynchronously.

    Args:
        request: Contains exp_name and username

    Returns:
        202 Accepted with experiment details and Location header
    """
    return apiHandler.run_exp(request.username, request.exp_name)

# ============================================================================
# Workflow Control Endpoints
# ============================================================================

@app.get("/exp/workflow/kill/{workflow_id}")
async def kill_workflow(workflow_id: str):
    """Kill a running or scheduled workflow."""
    return apiHandler.kill_workflow(workflow_id)


@app.get("/exp/workflow/pause/{workflow_id}")
async def pause_workflow(workflow_id: str):
    """Pause a running workflow."""
    return apiHandler.pause_workflow(workflow_id)


@app.get("/exp/workflow/resume/{workflow_id}")
async def resume_workflow(workflow_id: str):
    """Resume a paused workflow."""
    return apiHandler.resume_workflow(workflow_id)

# ============================================================================
# Experiment Control Endpoints
# ============================================================================

@app.get("/exp/experiment/kill/{experiment_id}")
async def kill_experiment(experiment_id: str):
    """Kill a running or scheduled experiment and all its workflows."""
    return apiHandler.kill_experiment(experiment_id)


@app.get("/exp/experiment/pause/{experiment_id}")
async def pause_experiment(experiment_id: str):
    """Pause all running workflows in an experiment."""
    return apiHandler.pause_experiment(experiment_id)


@app.get("/exp/experiment/resume/{experiment_id}")
async def resume_experiment(experiment_id: str):
    """Resume all paused workflows in an experiment."""
    return apiHandler.resume_experiment(experiment_id)

# ============================================================================
# Experiment Queue Status Endpoint
# ============================================================================

@app.get("/exp/queue/status")
async def get_queue_status():
    """Get the current status of the experiment execution queue."""
    return apiHandler.get_queue_status()

@app.get("/exp/experiment/status/{experiment_id}")
async def get_experiment_status(experiment_id: str):
    """
    Get the status of an experiment.

    Returns experiment status, queue position (if applicable), and error logs (if failed).
    """
    return apiHandler.get_experiment_status(experiment_id)

@app.post("/exp/experiments/query")
async def query_experiments(username: str):
    """
    Query experiments based on creator, intent, or metadata.

    Query Parameters:
        username: The username who owns the experiment

    Returns:
        List of experiments matching the query
    """
    return apiHandler.query_experiments(username=username)

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "eexp-engine-api"}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
