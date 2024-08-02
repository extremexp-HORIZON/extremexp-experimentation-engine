from flask import Flask, request
from flask_cors import CORS, cross_origin
from apiHandler import apiHandler
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
cors = CORS(app) # cors is added in advance to allow cors requests
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/exp/run', methods=["POST"])
@cross_origin()
def run():
    if request.method == 'POST':
        posted_data = request.get_json() # get_data gets the body of post request
        app.logger.info('testing info log')
        app.logger.info(posted_data)
        apiHandler.run_experiment()
        return {"message": "experiment started"}, 201
