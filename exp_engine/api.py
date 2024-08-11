from flask import Flask, request
from flask_cors import CORS, cross_origin
from apiHandler import apiHandler
import logging
logging.basicConfig(level=logging.INFO)
from translation import json2dsl
from data_abstraction_layer.data_abstraction_api import *
import pprint
import json

app = Flask(__name__)
cors = CORS(app) # cors is added in advance to allow cors requests
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/exp/run', methods=["POST"])
@cross_origin()
def run():
    if request.method == 'POST':
        posted_data = request.get_json() # get_data gets the body of post request
        json_data = posted_data['graphical_model']
        dsl_output = json2dsl.json_to_dsl(json_data)
        app.logger.info('Received request to run experiment with model: ')
        app.logger.info(dsl_output)

        with open("workflows/IDEKO_main.xxp", "w") as file:
            file.write(dsl_output)
        nodes = {node['id']: node for node in json_data['nodes']}
        dsl_lines = json2dsl.extract_and_save_composite_node_details(nodes)
        with open("workflows/IDEKO_DataPreprocessing.xxp", 'w') as file:
            file.write(dsl_lines)

        metadata = {
            'graphical_model': json.dumps(posted_data['graphical_model']),
            'dsl_model': json.dumps({
                'main': dsl_output,
                'secondary': [dsl_lines]
            })
        }
        new_exp = {
            'name': posted_data['name'],
            'model': str(dsl_output),
            'metadata': metadata
        }
        exp_id = create_experiment(new_exp)

        apiHandler.run_experiment(exp_id)
        return {"message": "experiment started"}, 201
