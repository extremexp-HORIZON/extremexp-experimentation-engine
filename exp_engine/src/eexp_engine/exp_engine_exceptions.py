class ImplementationFileNotFound(Exception):
    "Raised when an Implementation file is not found"
    pass

class InterfaceDoesNotMatch(Exception):
    "Raised when a task's interface (input or output data) does not match with its use in a workflow"
    pass
