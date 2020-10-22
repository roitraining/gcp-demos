from flask import (
    Flask, 
    request, 
    render_template,
    jsonify
)

from flask_cors import CORS

from utilities import (
    tests,
    dlp
)

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

def show_message_page(headline, message_text, title):
    message = {
        "headline": headline,
        "text": message_text,
        "title": title
    }
    return render_template('message.html',
        message_text=message_text,
        headline=headline,
        title=title
    )


@app.errorhandler(404)
def not_found(e):
    return show_message_page(
        "404",
        "Well, that didn't do anything",
        "Oops!"
    )


@app.route('/dlp_results', methods=['POST'])
def dlp_results():
    text = request.get_json()['text']
    action = request.get_json()['action']
    if action == "inspect":
        result = dlp.inspect(text)
    else:
        result = dlp.deidentify(text, action)
    return result, 200


@app.route('/dlp_demo', methods=['GET'])
def dlp_demo():
    return render_template('dlp-demo.html',
        title="DLP Demo"
    ), 200

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)