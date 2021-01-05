import requests
import json
from flask import Flask,render_template,Response,jsonify,request
from flask_cors import CORS
import time
from datetime import datetime
import pyrebase

key = "9924d3911cf21a14cac79595f1a1b33e"
url = "https://api.nomics.com/v1/currencies/ticker" #?key="+key+"&interval=1h,1d&convert=INR&per-page=100&page=1"
params = {
    "key":key,
    "interval":"1h,1d",
    "convert" : "INR",
    "per-page" : 100,
    "page" : 1,
}
config = {
  "apiKey": "AIzaSyBREDzu1TkZWu3L1LBnIJnanDIUsSKlvTs",
  "authDomain": "bithook-default-rtdb.firebaseio.com/",
  "databaseURL": "https://bithook-default-rtdb.firebaseio.com/",
  "projectId": "bithook",
  "storageBucket": "https://bithook.appspot.com/",
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

res = requests.get(url,params)
cryptoCoins = []


app = Flask(__name__)
CORS(app)


def saveInFirebase(id,data):
    db.child("CoinData").child(str(id)).set(data)
    return

def setHook(data):
    flag = 0
    print(data,cryptoCoins)
    for i in range(len(cryptoCoins)):
        if cryptoCoins[i]["id"] == data["coinId"]:
            flag = 1
            if data["track"] == False:
                del cryptoCoins[i]
    
    if flag == 0:
        paramsCoin = params
        paramsCoin["ids"] = str(data["coinId"])
        res = requests.get(url,paramsCoin).json()
        print(res[0]["price"],str(datetime.now()),"loaded")
        cryptoCoins.append({"id":data["coinId"],"hookPrice":res[0]["price"],"hookDateTime":str(datetime.now()),"maxPrice":res[0]["price"]})

    params["ids"] = ""
    for coin in cryptoCoins:
           if params["ids"] == "":
               params["ids"] = coin["id"]
           else:
               params["ids"] += "," + coin["id"]
    print(params,cryptoCoins)   
    saveInFirebase(data["userId"],cryptoCoins)    
    return  
    #response = requests.get(url,params)
    #print("\n\n response\n",response.json()) 


def get_message():
    '''this could be any function that blocks until data is ready'''
    time.sleep(5.0)
    s = time.ctime(time.time())
    res = requests.get(url,params)
    js = res.json()
    return json.dumps(js)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/trackCoins',methods=['GET','POST'])
def trackCoins():
    if request.method == "POST":
        data = json.loads(request.data)
        print("data",data)
        if len(data["coinId"])!=0:
            setHook(data)
            return jsonify({'status':str(200)})
        else:
            return jsonify({'status':str(400)})    
    else:
        return jsonify({'status':str(400)}) 

@app.route('/stream')
def stream():
    def eventStream():
        while True:
            # wait for source data to be available, then push it
            yield 'data: {}\n\n'.format(get_message())
    return Response(eventStream(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(port=5000,debug=True)    