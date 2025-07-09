from flask import Flask, request
from flask_cors import CORS, cross_origin
from apiHandler import apiHandler
import logging
logging.basicConfig(level=logging.INFO)
from translation import json2dsl
from src.eexp_engine.data_abstraction_layer.data_abstraction_api import *
import pprint
import json
import os

app = Flask(__name__)
cors = CORS(app) # cors is added in advance to allow cors requests
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/exp/run/<experimentname>', methods=["GET"])
@cross_origin()
def run(experimentname):
    try:
        print("Running new experiment")
        exp_id = apiHandler.run_exp(experimentname)
        return {"message": f"experiment finished with id {exp_id}"}, 200
    except Exception as e:
        print(f"Exception: {e}", flush=True)
        return {"message": f"exception: {e}"}, 500

# @app.route('/exp/run', methods=["POST"])
# @cross_origin()
# def run():
#     if request.method == 'POST':
#         posted_data = request.get_json() # get_data gets the body of post request
#         json_data = posted_data['graphical_model']
#         dsl_output = json2dsl.json_to_dsl(json_data)
#         app.logger.info('Received request to run experiment with model: ')
#         app.logger.info(dsl_output)
#
#         with open("workflows/IDEKO_main.xxp", "w") as file:
#             file.write(dsl_output)
#         nodes = {node['id']: node for node in json_data['nodes']}
#         dsl_lines = json2dsl.extract_and_save_composite_node_details(nodes)
#         with open("workflows/IDEKO_DataPreprocessing.xxp", 'w') as file:
#             file.write(dsl_lines)
#
#         metadata = {
#             'graphical_model': json.dumps(posted_data['graphical_model']),
#             'dsl_model': json.dumps({
#                 'main': dsl_output,
#                 'secondary': [dsl_lines]
#             })
#         }
#         new_exp = {
#             'name': posted_data['name'],
#             'model': str(dsl_output),
#             'metadata': metadata
#         }
#         exp_id = create_experiment(new_exp, "dummy_user")
#
#         apiHandler.run_experiment(exp_id)
#         return {"message": "experiment started"}, 201

@app.route("/exp/workflow/kill/<workflow_id>", methods=["GET"])
@cross_origin()
def kill_workflow(workflow_id):
    apiHandler.kill_workflow(workflow_id)
    return {"message": f"workflow with id {workflow_id} is killed"}, 204


@app.route("/exp/workflow/pause/<workflow_id>", methods=["GET"])
@cross_origin()
def pause_workflow(workflow_id):
    apiHandler.pause_workflow(workflow_id)
    return {"message": f"workflow with id {workflow_id} is paused"}, 204


@app.route("/exp/workflow/resume/<workflow_id>", methods=["GET"])
@cross_origin()
def resume_workflow(workflow_id):
    apiHandler.resume_workflow(workflow_id)
    return {"message": f"workflow with id {workflow_id} is resumed"}, 204


@app.route("/exp/experiment/kill/<experiment_id>", methods=["GET"])
@cross_origin()
def kill_experiment(experiment_id):
    apiHandler.kill_experiment(experiment_id)
    return {"message": f"experiment with id {experiment_id} is killed"}, 204

@app.route("/exp/experiment/pause/<experiment_id>", methods=["GET"])
@cross_origin()
def pause_experiment(experiment_id):
    apiHandler.pause_experiment(experiment_id)
    return {"message": f"experiment with id {experiment_id} is paused"}, 204

@app.route("/exp/experiment/resume/<experiment_id>", methods=["GET"])
@cross_origin()
def resume_experiment(experiment_id):
    apiHandler.resume_experiment(experiment_id)
    return {"message": f"experiment with id {experiment_id} is resumed"}, 204
