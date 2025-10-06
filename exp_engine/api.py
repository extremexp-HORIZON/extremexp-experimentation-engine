from flask import Flask, request
from flask_cors import CORS, cross_origin
from apiHandler import apiHandler
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/exp/run/<experimentname>', methods=["POST"])
@cross_origin()
def run(experimentname):
    return apiHandler.run_exp(experimentname)

@app.route("/exp/workflow/kill/<workflow_id>", methods=["GET"])
@cross_origin()
def kill_workflow(workflow_id):
    return apiHandler.kill_workflow(workflow_id)


@app.route("/exp/workflow/pause/<workflow_id>", methods=["GET"])
@cross_origin()
def pause_workflow(workflow_id):
    return apiHandler.pause_workflow(workflow_id)

@app.route("/exp/workflow/resume/<workflow_id>", methods=["GET"])
@cross_origin()
def resume_workflow(workflow_id):
    return apiHandler.resume_workflow(workflow_id)


@app.route("/exp/experiment/kill/<experiment_id>", methods=["GET"])
@cross_origin()
def kill_experiment(experiment_id):
    return apiHandler.kill_experiment(experiment_id)

@app.route("/exp/experiment/pause/<experiment_id>", methods=["GET"])
@cross_origin()
def pause_experiment(experiment_id):
    return apiHandler.pause_experiment(experiment_id)

@app.route("/exp/experiment/resume/<experiment_id>", methods=["GET"])
@cross_origin()
def resume_experiment(experiment_id):
    return apiHandler.resume_experiment(experiment_id)

@app.route("/exp/experiment/status/<experiment_id>", methods=["GET"])
@cross_origin()
def experiment_status(experiment_id):
    return apiHandler.get_experiment_status(experiment_id)
