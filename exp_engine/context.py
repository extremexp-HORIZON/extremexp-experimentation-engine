from dataclasses import dataclass

@dataclass
class ExperimentContext:
    wf_id: str
    exp_id: str
    mapping: dict