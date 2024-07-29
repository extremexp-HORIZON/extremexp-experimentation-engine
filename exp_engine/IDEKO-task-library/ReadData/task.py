
import os, sys
import pandas as pd
sys.path.append(os.path.join(os.getcwd(), "tasks/IDEKO/src"))
from classes import preprocessing_functions
from helpers.logger import LoggerHelper, logging
import proactive_helper as ph

LoggerHelper.init_logger()
logger = logging.getLogger(__name__)

# input_data_folder = "datasets/ideko"
input_data_folder = "datasets/ideko-subset"

indicator_list = ["f3"]
X, Y = preprocessing_functions.read_data(input_data_folder, indicator_list)
logger.info("Summary of timeseries length %s" %pd.Series([len(x) for x in X]).describe())

ph.save_datasets(variables, ("X", X), ("Y", Y), ("indicator_list", indicator_list))
