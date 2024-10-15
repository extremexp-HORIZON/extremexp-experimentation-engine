import os
import json
[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
from classes import preprocessing_functions
import proactive_helper as ph

X_pad, Y_pad_json = ph.load_datasets(variables, "X_pad", "Y_pad_json")
Y_pad = json.loads(Y_pad_json)

# Split data into training set and test set

X_train, X_test, y_train, y_test = preprocessing_functions.split_data(X_pad, Y_pad)

n_timestamps = X_train.shape[1]
n_features = X_train.shape[2]

ph.save_datasets(variables, ("n_timestamps", n_timestamps), ("n_features", n_features))
ph.save_datasets(variables, ("X_train", X_train), ("X_test", X_test))
ph.save_datasets(variables, ("y_train", y_train), ("y_test", y_test))
ph.save_datasets(variables, ("X_pad", X_pad), ("Y_pad", Y_pad))
