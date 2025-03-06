[sys.path.append(os.path.join(os.getcwd(), folder)) for folder in variables.get("dependent_modules_folders").split(",")]
import proactive_helper as ph

print("I'm ExpInteraction1")
results = ph.get_experiment_results()
print(f"and here the results so far: {results}")

import threading
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    global df
    # Render a simple HTML page to display and edit the dataframe
    html_template = '''
    <h1>Experiment interaction test</h1>
    <form method="POST" action="/update">
        <button type="submit" formaction="/continue">Continue</button>
    </form>
    '''
    return render_template_string(html_template)

@app.route('/continue', methods=['POST'])
def continue_pipeline():
    global df
    try:
        print("Continue clicked.")
        # Display confirmation and the updated dataframe
        html_response = f'''
        <h1>Continue clicked.</h1>
        '''
        return html_response, 200
    except Exception as e:
        print("Error in continue_pipeline:", e)
        return f"Error in continue_pipeline: {e}", 400

# Flask shutdown utility
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()

@app.after_request
def shutdown_if_requested(response):
    if request.endpoint in ['continue_pipeline', 'stop_pipeline']:
        shutdown_server()
    return response

# Start Flask app in a separate thread
def run_flask_app():
    app.run(host='0.0.0.0', port=5000)


print("Starting Flask application...")
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()
