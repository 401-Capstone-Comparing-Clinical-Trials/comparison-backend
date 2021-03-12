import flask
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return '''
    <h1>Comparison Backend</h1>
    '''

# Sort Trials By Criteria Route
@app.route('/api/sortTrialsByCriteria', methods=['GET'])
def api_sortTrialsByCriteria():
    return jsonify(
        status=True,
        message="Successfully sorted trials",
        data="No data"
    )

app.run()