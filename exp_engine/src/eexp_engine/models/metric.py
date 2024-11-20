import logging
logger = logging.getLogger(__name__)


class Metric:

    def __init__(self, name, semantic_type, kind, data_type):
        self.name = name
        self.semantic_type = semantic_type
        self.kind = kind
        self.data_type = data_type

    def print(self, tab=""):
        logger.debug(f"{tab}\twith metric name : {self.name}")
        logger.debug(f"{tab}\twith metric semantic type : {self.semantic_type}")
        logger.debug(f"{tab}\twith metric kind : {self.kind}")
        logger.debug(f"{tab}\twith metric data_type : {self.data_type}")

    def clone(self):
        new_m = Metric(self.name, self.semantic_type, self.kind, self.data_type)
        return new_m
