import numpy as np
import os
import json
sys.path.append(os.path.join(os.getcwd(), "tasks/IDEKO/src"))
from classes import preprocessing_functions
import proactive_helper as ph
from helpers.logger import LoggerHelper, logging

LoggerHelper.init_logger()
logger = logging.getLogger(__name__)

X, Y, indicator_list = ph.load_datasets(variables, "X", "Y", "indicator_list")

X_pad = preprocessing_functions.add_padding(X, indicator_list)
Y_pad = np.array(Y)

logger.info("SHAPE X (%d, %d, %d)" %(np.shape(X_pad)))

logger.info("Number of timeseries %d" %np.shape(X_pad)[0])
logger.info("Number of points %d" %np.shape(X_pad)[1])
logger.info("Number of features %d" %np.shape(X_pad)[2])

logger.info("SHAPE Y %s" %np.shape(Y_pad))

ph.save_datasets(variables, ("X_pad", X_pad), ("Y_pad_json", json.dumps(Y_pad,cls=ph.NumpyEncoder)))
