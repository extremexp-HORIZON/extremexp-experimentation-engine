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
    "Raised when a proactive variable in a task's source code is not part of its signature (inputs/outputs/params)"
    pass


class SourceCodeAttemptsToLoadDatasetNotInTaskSignature(Exception):
    "Raised when attempting to load a dataset as an input of a task, without this being part of its signature"
    pass


class SourceCodeAttemptsToSaveDatasetNotInTaskSignature(Exception):
    "Raised when attempting to save a dataset as an output of a task, without this being part of its signature"
    pass


class InputDataInSubWorkflowDoesNotMatchOutputDataOfParentWorkflow(Exception):
    "Raised when a subworkflow's input does not much the output of its previous task in the parent workflow"
    pass


class OutputDataInSubWorkflowDoesNotMatchInputDataOfParentWorkflow(Exception):
    "Raised when a subworkflow's output does not much the input of its next task in the parent workflow"
    pass


class InteractionTaskDoesNotHaveInteractiveType(Exception):
    "Raised when an interaction of an experiment is not implemented via a task whose type is interactive"
    pass


class DatasetManagementNotSet(Exception):
    "Raised when the DATASET_MANAGEMENT variable in config.py is not set "
    pass


class DatasetManagementSetToDDMButNoURLProvided(Exception):
    "Raised when the DATASET_MANAGEMENT variable in config.py is set to DDM but the DATASET_MANAGEMENT_URL is not set"
    pass


class DatasetManagementSetToDDMButNoPortalUserOrPasswordProvided(Exception):
    "Raised when the DATASET_MANAGEMENT variable in config.py is set to DDM but the PORTAL_USERNAME or the PORTAL_PASSWORD is not set"
    pass


class PortalUserDoesNotExist(Exception):
    "Raised when the PORTAL_USERNAME variable in config.py is set to a user that does not exist"
    pass


class PortalPasswordDoesNotMatch(Exception):
    "Raised when the PORTAL_PASSWORD variable in config.py does not much the user in the PORTAL_USERNAME variable"
    pass