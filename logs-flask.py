import os
from time import sleep
from flask import Flask, render_template, request
from _configs import *

template_dir = os.path.dirname(os.path.realpath(__file__)) + "/html"

app = Flask(__name__, template_folder='html')


@app.route('/logs')
def logs():
    log = request.args.get('log')
    return render_template('logs.html', log=log)

@app.route('/stream')

def stream():
    log = request.args.get('log')
    def generate():
        if log == "web":
            thelog = LOG_FILE_WEB
        else:
            thelog = LOG_FILE

        print(thelog)
        with open(thelog) as f:
            while True:
                yield f.read()
                sleep(1)

    return app.response_class(generate(), mimetype='text/plain')

app.run(debug=True, port=5000, host='0.0.0.0')