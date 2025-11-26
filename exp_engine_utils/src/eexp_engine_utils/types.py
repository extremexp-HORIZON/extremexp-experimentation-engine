from typing import Any, Dict, TypedDict, Optional


class Variables(TypedDict, total=False):
    """
    Variables dictionary passed to tasks by the execution engine.
    Contains task-specific configuration and runtime parameters.
    """
    task_name: str
    wf_id: str
    data_abstraction_base_url: Optional[str]
    data_abstraction_access_token: Optional[str]


class ResultMap(Dict[str, Any]):
    """
    Result map dictionary for passing data between tasks and capture metrics.
    """
    pass


def get_runtime_context() -> tuple[Variables, ResultMap]:
    """
    Helper function to get typed references to runtime variables.

    This is just for IDE type hints - at runtime, the actual variables
    and resultMap are provided by the execution engine.

    Returns:
        tuple: (variables, resultMap) with proper type hints
    """
    raise RuntimeError("This function is for type hints only and should never be called at runtime")
