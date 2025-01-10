import os
import threading
import pandas as pd
from flask import Flask, request, render_template_string

# Load the dataframe passed from Task 1
dataframe_json = variables.get("dataframe_json")
df = pd.read_json(dataframe_json)

# Flask application
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    global df
    # Render a simple HTML page to display and edit the dataframe
    html_template = '''
    <h1>Dataframe Viewer and Editor</h1>
    <form method="POST" action="/update">
        <textarea name="dataframe" rows="10" cols="50">{{ dataframe }}</textarea><br>
        <button type="submit" formaction="/continue">Continue</button>
        <button type="submit" formaction="/stop">Stop</button>
    </form>
    '''
    return render_template_string(html_template, dataframe=df.to_json())

@app.route('/update', methods=['POST'])
def update():
    global df
    try:
        # Retrieve the updated dataframe JSON from the form
        updated_data = request.form['dataframe']
        # Parse the updated JSON and update the dataframe
        df = pd.read_json(updated_data)
        print("Dataframe successfully updated:", df)
        # Reload the page to display the updated dataframe
        return index()
    except Exception as e:
        print("Error updating dataframe:", e)
        return f"Error updating dataframe: {e}", 400

@app.route('/continue', methods=['POST'])
def continue_pipeline():
    global df
    try:
        # Retrieve the updated JSON from the form
        updated_data = request.form['dataframe']
        # Parse the updated JSON and update the dataframe
        df = pd.read_json(updated_data)
        print("Updated dataframe reloaded in Task 2:")
        print(df)
        # Save the updated dataframe to ProActive variables
        variables.put("dataframe_json", df.to_json())
        print("Updated dataframe passed to Task 3.")
        print("ILIAS1")
        # Display confirmation and the updated dataframe
        html_response = f'''
        <h1>Data saved and pipeline will continue.</h1>
        <h2>Updated Dataframe:</h2>
        <pre>{df.to_string(index=False)}</pre>
        '''
        print("ILIAS2")
        return html_response, 200
    except Exception as e:
        print("Error in continue_pipeline:", e)
        return f"Error in continue_pipeline: {e}", 400

@app.route('/stop', methods=['POST'])
def stop_pipeline():
    print("User clicked Stop. Terminating pipeline.")
    # Send a response before shutting down
    return "Pipeline terminated. You can close this page now.", 200

# Flask shutdown utility
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()

@app.after_request
def shutdown_if_requested(response):
    print("request42")
    if request.endpoint in ['continue_pipeline', 'stop_pipeline']:
        shutdown_server()
    return response

# Start Flask app in a separate thread
def run_flask_app():
    app.run(host='0.0.0.0', port=5000)


print("Starting Flask application...")
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()
