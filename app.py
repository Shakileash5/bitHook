import requests
import json
from flask import Flask,render_template,Response,jsonify,request
from flask_cors import CORS
import time
import asyncio
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
trackerRunning = 0

app = Flask(__name__)
CORS(app)

tempPercent = 0
coinDirection = 0

def saveInFirebase(id,data):
    db.child("CoinData").child(str(id)).set(data)
    return

async def tracker():
    trackerRunning = 1
    while True:
        
        print("tracker running")
        if params["ids"] == "":
            print("tracker stopped")
            trackerRunning = 0
            break
        
        time.sleep(5)
        res = requests.get(url,params).json()
        global coinDirection
        for i in res:
            print(i["price"]," id ::",i["id"],params["ids"])
            for coin in cryptoCoins:
                if coin["id"] == i["id"]:
                    if float(coin["maxPrice"]) < float(i["price"]):
                        coin["maxPrice"] = i["price"]
                        coin["highCurve"] = coin["completeCurve"] + 1
                    
                    tempPercent = (float(i["price"])*100)/float(coin["hookPrice"])
                    coin["count"] += 1
                    coin["curve"].append(tempPercent)
                    if coin["count"] == 3:
                        one,two,three = 0,0,0
                        one = coin["curve"].pop()
                        two = coin["curve"].pop()
                        three = coin["curve"].pop()
                        temp = 0
                        temp = (one + two + three)/3
                        coin["count"] = 0
                        coin["curve"].append(temp)
                        coin["completeCurve"] += 1
                        print("completecurve",coin["completeCurve"])
                        if coin["completeCurve"] > coin["highCurve"]:
                            print("past limits")
                            if coin["completeCurve"] > 3:
                                print(coin["curve"][-2],"here")
                                if coin["curve"][coin["highCurve"]] > coin["curve"][-2] and coin["curve"][-2] > coin["curve"][-1]:
                                    print("Pricing falling please sell the coin!!") 

                    tempPercent = (float(i["price"])*100)/float(coin["maxPrice"])

                    if tempPercent >= 100:
                        tempPercent -= 100
                        coinDirection = 1
                    else :
                        tempPercent = 100 - tempPercent

                    print(tempPercent,"percent ",coinDirection,"\n","curve",coin["curve"])

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
        cryptoCoins.append({"id":data["coinId"],"hookPrice":res[0]["price"],"hookDateTime":str(datetime.now()),"maxPrice":res[0]["price"],"count":0,"curve":[],"completeCurve":0,"highCurve":0})
    #global params
    flag = 0
    params["ids"] = ""
    for coin in cryptoCoins:
           if params["ids"] == "":
               params["ids"] = coin["id"]
               flag = 1
           else:
               params["ids"] += "," + coin["id"]
               if trackerRunning == 0:
                   asyncio.run(tracker())
    print(params,cryptoCoins)   
    saveInFirebase(data["userId"],cryptoCoins) 
    if flag == 1 and data["track"]:
        if trackerRunning == 0:
            asyncio.run(tracker())
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