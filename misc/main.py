from flask import (
    Flask, 
    request, 
    render_template
)

from utilities import (
    tests
)

app = Flask(__name__)


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


@app.route('/tests/<test>', methods=['GET'])
def test(test):
    res = getattr(tests, test)(request.args)
    return res, 200
