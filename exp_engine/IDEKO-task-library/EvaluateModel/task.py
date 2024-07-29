import os
import numpy as np
[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
from classes.binary_models import NeuralNetwork
import proactive_helper as ph
from classes import model_configuration
from classes import preprocessing_functions
import tensorflow.keras as keras
from tensorflow.keras.models import load_model

# Model name
folder_name = "NeuralNetwork"

model_name = "model_nn.keras"

activation_function = "relu"
units =[100, 100, 100]
n_timestamps, n_features = ph.load_datasets(variables, "n_timestamps", "n_features")

X_test, y_test = ph.load_datasets(variables, "X_test", "y_test")
X_pad, Y_pad = ph.load_datasets(variables, "X_pad", "Y_pad")
model_path = ph.load_datasets(variables, "model_path")
model_path = model_path[0]

model_nn = NeuralNetwork(n_timestamps, n_features, activation_function, units)

model_nn.model = keras.models.load_model(model_path)

y_test = np.asarray(y_test)
Y_pad = np.asarray(Y_pad)
resultMap = model_nn.model_evaluation(model_nn.model , X_pad, Y_pad, X_test, y_test, variables, resultMap)
