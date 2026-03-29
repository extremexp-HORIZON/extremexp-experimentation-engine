from eexp_engine_utils import utils
import threading
import ctypes
from flask import Flask, request, render_template_string

print("I'm ExpInteraction1")
results = ph.get_experiment_results(variables)
print(f"and here the results so far: {results}")

class StoppableThread(threading.Thread):
    def get_id(self):  # pylint: disable=R1710
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for thread_id, thread in threading._active.items():  # pylint: disable=W0212
            if thread is self:
                return thread_id

    def kill(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(SystemExit)
        )
        if res == 0:
            raise ValueError(f"Invalid thread id: {thread_id}")
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), None)
            raise SystemExit("Stopping thread failure")

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

def shutdown_server():
    flask_thread.kill()
    flask_thread.join()

@app.after_request
def shutdown_if_requested(response):
    if request.endpoint in ['continue_pipeline', 'stop_pipeline']:
        shutdown_server()
    return response

# Start Flask app in a separate thread
def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

print("Starting Flask application...")
flask_thread = StoppableThread(target=run_flask_app)
flask_thread.start()
