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
    try:
        exp_id = apiHandler.run_exp(experimentname, True)
        body = {
            "experiment": {
                "id": exp_id,
                "name": experimentname,
                "status": "scheduled"
            },
            "message": "experiment started."
        }
        # Location header (existing endpoints for experiment actions use this pattern)
        return body, 201
    except FileNotFoundError as e:
        return {"error": {"code": "SPEC_NOT_FOUND", "exp_name": experimentname, "message": str(e)}}, 404
    except Exception as e:
        # Avoid leaking internal details; still include basic message
        return {"error": {"code": "INTERNAL_ERROR", "message": str(e)}}, 500

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
