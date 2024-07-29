import os
import numpy as np
[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
from classes.binary_models import NeuralNetwork
import proactive_helper as ph

# NeuralNetwork:
# enabled: True
# model_parameters:
# activation_function: relu
# units:
# - 100
# - 100
# - 100
# training_parameters:
# epochs: 2
# batch_size: 64
# name_parameters:
# folder_name: NeuralNetwork
# model_name: model_nn.h5

# Model name
folder_name = "NeuralNetwork"

# TODO note: changed .h5 to .keras
model_name = "model_nn.keras"

# Path to store the model
working_dir = os.getcwd()
output_path = os.path.join(working_dir, "output")
output_path_nn = os.path.join(output_path, folder_name)
os.makedirs(output_path_nn, exist_ok = True)

# TODO note: creating directory to save the trained model
model_path = ph.create_dir(variables, 'trained_model')
# Parameters defining the architecture of the model

# Activation function
activation_function = "relu"

# The length of the list is the number of layers and each element indicates the number of neurons in each layer.
units =[100, 100, 100]

# Number of epochs y batch_size
epochs = int(variables.get("epochs"))
batch_size = int(variables.get("batch_size"))

n_timestamps, n_features = ph.load_datasets(variables, "n_timestamps", "n_features")
X_train, y_train = ph.load_datasets(variables, "X_train", "y_train")
X_test, y_test = ph.load_datasets(variables, "X_test", "y_test")
X_pad, Y_pad = ph.load_datasets(variables, "X_pad", "Y_pad")


print(f"n_timestamps in train_nn task: {n_timestamps}")
print(f"n_features in train_nn task: {n_features}")

# Initialise the model class
model_nn = NeuralNetwork(n_timestamps, n_features, activation_function, units)

# Create the model (according to the architecture defined)
model_nn.create_model()

# Define callbacks
early_stopping = model_nn.early_stopping_callback()
model_checkpoint = model_nn.model_checkpoint_callback(model_path = os.path.join(output_path_nn, model_name))
callback_list = [early_stopping, model_checkpoint]

# Model configuration and model training
model_nn.model_compilation(model_nn.model)

y_train = np.asarray(y_train)
y_test = np.asarray(y_test)
history_nn = model_nn.model_fitting(model_nn.model, X_train, y_train, X_test, y_test, callback_list, epochs, batch_size)

# Plot history of the model
# preprocessing_functions.plot_model_history(history_nn, output_path_nn)


# TODO note: added following lines to save trained model
model = model_nn.model
model_path = os.path.join(model_path, model_name)
model.save(model_path)

# TODO note: added following lines to save intermediate data for the next task
ph.save_datasets(variables, ("model_path", model_path))
ph.save_datasets(variables, ("X_test", X_test))
ph.save_datasets(variables, ("y_test", y_test))
ph.save_datasets(variables, ("X_pad", X_pad), ("Y_pad", Y_pad))

