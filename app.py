import requests
import json
from flask import Flask,render_template,Response,jsonify
import time

key = "9924d3911cf21a14cac79595f1a1b33e"
url = "https://api.nomics.com/v1/currencies/ticker?key="+key+"&interval=1d&convert=INR&per-page=100&page=1"
res = requests.get(url)
#print(json.loads(res.text))

app = Flask(__name__)

def get_message():
    '''this could be any function that blocks until data is ready'''
    time.sleep(20.0)
    s = time.ctime(time.time())
    js = res.json()
    return json.dumps(js)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def eventStream():
        while True:
            # wait for source data to be available, then push it
            yield 'data: {}\n\n'.format(get_message())
    return Response(eventStream(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(port=5000,debug=True)    