class ImplementationFileNotFound(Exception):
    "Raised when an Implementation file is not found"
    pass

class InputDataInWorkflowDoesNotMatchSignature(Exception):
    "Raised when a task's input signature does not match with its use in a workflow"
    pass

class OutputDataInWorkflowDoesNotMatchSignature(Exception):
    "Raised when a task's output signature does not match with its use in a workflow"
    pass

class SourceCodeAttemptsToReadVariableNotInTaskSignature(Exception):
    "Raised when a task's input signature does not match with its source code"
    pass

class OutputDataInSourceDoesNotMatchSignature(Exception):
    "Raised when a task's output signature does not match with its source code"
    pass
