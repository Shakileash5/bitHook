import os
import sys
import time
import json
import asyncio
import pyrebase
import requests
from mail import send_mail
from flask_cors import CORS
from datetime import datetime
from flask import Flask,render_template,Response,jsonify,request


key = "9924d3911cf21a14cac79595f1a1b33e"
alternateKey = "c36717396ec409c55b99f59637c4fb5b"
url = "https://api.nomics.com/v1/currencies/ticker" #?key="+key+"&interval=1h,1d&convert=INR&per-page=100&page=1"
params = {
    "key":key,
    "interval":"1h,1d",
    "convert" : "INR",
    "per-page" : 100,
    "page" : 1,
}
paramsUser = []
config = {
  "apiKey": "AIzaSyBREDzu1TkZWu3L1LBnIJnanDIUsSKlvTs",
  "authDomain": "bithook-default-rtdb.firebaseio.com/",
  "databaseURL": "https://bithook-default-rtdb.firebaseio.com/",
  "projectId": "bithook",
  "storageBucket": "https://bithook.appspot.com/",
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

#res = requests.get(url,params)
cryptoCoins = []
trackerRunning = 0

tempPercent = 0
coinDirection = 0
trackPeriod = 60
curveLength = {}

app = Flask(__name__)
CORS(app)

def getUserDetails(id):
    try:
        details = dict(db.child("User").child(str(id)).get().val())
        return details
    except:
        print("no such id")

def fetchFirebaseData():
    try:
        res = db.child("CoinData").get()
        keys = list(dict(res.val()).keys())
        val = dict(res.val())
        print(val)
        for user in keys:
            print(user)
            details = getUserDetails(user)
            mail = details["mail"]
            
            cryptoCoins.append({"userId":str(user),"mail":mail,"coinData":val[str(user)]})
            trackPeriod = details["trackPeriod"]
            
            curveLength[str(user)] = details["curveLength"]
            print("works",str(user))
            details = db.child("CoinData").child(str(user)).get().val()
            print(details,"userCoin")
            params["ids"] = ""
            print(cryptoCoins,"\n\n",cryptoCoins[0])
            paramsUser.append(params)
            for coin in details:
                if paramsUser[len(paramsUser)-1]["ids"] == "":
                    paramsUser[len(paramsUser)-1]["ids"] = coin["id"]
                        
                else:
                    paramsUser[len(paramsUser)-1]["ids"] += "," + coin["id"]
                    #if trackerRunning == 0:
                      #  asyncio.run(tracker())
            print(paramsUser,cryptoCoins)
        print("outOfloop")
        #asyncio.run(tracker())
    except Exception as e:
        print("someError",e)
    print(cryptoCoins,"val")
    return

def saveInFirebase(id,data):
    db.child("CoinData").child(str(id)).set(data)
    return

def hookHistoryFirebase(id,data,state):
    
    try:
        hookHistory = list(db.child("User").child(str(id)).child("hookHistory").get().val())
    except:
        hookHistory = []
    print("what is hook",hookHistory)
    if hookHistory == None:
        hookHistory = []
    if state == 1:
        fakeParams = params
        fakeParams["ids"] = str(data["id"])
        res = requests.get(url,fakeParams).json()
        print(res)
        hookHistory.append({"id":data["id"],"hookPrice":res[0]["price"],"hookDateTime":data["hookDateTime"],"maxPrice":data["maxPrice"],"type":"unHooked"})
    else:
        hookHistory.append({"id":data["id"],"hookPrice":data["hookPrice"],"hookDateTime":data["hookDateTime"],"type":"Hooked"})
    try:
        db.child("User").child(str(id)).child("hookHistory").set(hookHistory)
        print("Hooked sucessfully")
    except Exception as e:
        print("error in saving history",e)

async def tracker():
    trackerRunning = 1
    while True:
        
        print("tracker running")
        count = 0

        for user in cryptoCoins:
            if paramsUser[count]["ids"] == "":
                print("tracker stopped")
                trackerRunning = 0
            count+=1
        if trackerRunning == 0:
            break
        await asyncio.sleep(trackPeriod)
        
        global coinDirection
        try:    
            count = 0 
            for user in cryptoCoins:
                for coin in user["coinData"]:
                    res = requests.get(url,paramsUser[count]).json()
                    for i in res:
                        print(i["price"]," id ::",i["id"],params["ids"],"ui")
                        try:
                            coin["curve"] = coin["curve"]
                        except:
                            coin["curve"] = []
                        if coin["id"] == i["id"]:
                            if float(coin["maxPrice"]) < float(i["price"]):
                                coin["maxPrice"] = i["price"]
                                coin["highCurve"] = coin["completeCurve"] + 1
                            
                            tempPercent = (float(i["price"])*100)/float(coin["hookPrice"])
                            coin["count"] += 1
                            coin["curve"].append(tempPercent)
                            if coin["count"] == curveLength[str(user["userId"])]:
                                sum1 = 0
                                for k in range(curveLength[str(user["userId"])]):
                                    sum1 += coin["curve"].pop()
                                sum1 = sum1/curveLength[str(user["userId"])]
                                coin["count"] = 0
                                coin["curve"].append(sum1)
                                coin["completeCurve"] += 1
                                print("completecurve",coin["completeCurve"])
                                if coin["completeCurve"] > coin["highCurve"]:
                                    print("past limits")
                                    if coin["completeCurve"] > 3:
                                        print(coin["curve"][-2],"here")
                                        if coin["curve"][coin["highCurve"]] > coin["curve"][-2] and coin["curve"][-2] > coin["curve"][-1]:
                                            print("Pricing falling please sell the coin!!") 
                                            mail = getUserDetails(str(user["userId"]))["mail"]
                                            send_mail(mail,coin["id"])

                            tempPercent = (float(i["price"])*100)/float(coin["maxPrice"])

                            if tempPercent >= 100:
                                tempPercent -= 100
                                coinDirection = 1
                            else :
                                tempPercent = 100 - tempPercent

                            saveInFirebase(user["userId"],user["coinData"]) 
                            print(tempPercent,"percent ",coinDirection,"\n","curve",coin["curve"])    
                count+=1                  
        except Exception as e:
            print("some Error dont worry!!",e)


def setHook(data):
    flag = 0
    flagUser = -1
    print(data,cryptoCoins)
    for j in range(len(cryptoCoins)):
        if cryptoCoins[j]["userId"] == data["userId"]:
            flagUser = j
            for i in range(len(cryptoCoins[j]["coinData"])):
                if cryptoCoins[j]["coinData"][i]["id"] == data["coinId"]:
                    flag = 1
                    if data["track"] == False:
                        hookHistoryFirebase(data["userId"],cryptoCoins[j]["coinData"][i],1)
                        del cryptoCoins[j]["coinData"][i]
        
    if flag == 0:
        if flagUser == -1:
            mail = getUserDetails(str(data["userId"]))["mail"]
            cryptoCoins.append({"userId":str(data["userId"]),"mail":mail,"coinData":[]})
            paramsUser.append(params)
            flagUser = len(cryptoCoins) - 1
        paramsCoin = params
        paramsCoin["ids"] = str(data["coinId"])
        res = requests.get(url,paramsCoin).json()
        print(res[0]["price"],str(datetime.now()),"loaded")
        
        cryptoCoins[flagUser]["coinData"].append({"id":data["coinId"],"hookPrice":res[0]["price"],"hookDateTime":str(datetime.now()),"maxPrice":res[0]["price"],"count":0,"curve":[],"completeCurve":0,"highCurve":0})
        hookHistoryFirebase(data["userId"],cryptoCoins[flagUser]["coinData"][-1],0)

    #global params
    flag = 0
    params["ids"] = ""
    paramsUser[flagUser] = params
    print(cryptoCoins,"\n\n",cryptoCoins[0])
    for coin in cryptoCoins[flagUser]["coinData"]:

           if paramsUser[flagUser]["ids"] == "":
               paramsUser[flagUser]["ids"] = coin["id"]
               flag = 1
           else:
               paramsUser[flagUser]["ids"] += "," + coin["id"]
               if trackerRunning == 0:
                   #asyncio.run(tracker())
                   loop = asyncio.get_event_loop()
                   loop.run_until_complete(tracker())
    print(paramsUser[flagUser],cryptoCoins)   
    saveInFirebase(data["userId"],cryptoCoins[flagUser]["coinData"]) 
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

@app.route("/changeCurveLength",methods=["GET","POST"])
def changeCurveLength():
    if request.method == "POST":
        data = json.loads(request.data)
        print("data",data)
        if int(data["curveLength"])!=0:
            curveLength[str(data["userId"])] = int(data["curveLength"])
            return jsonify({'status':str(200)})
        else:
            return jsonify({'status':str(400)})    
    else:
        return jsonify({'status':str(400)}) 

@app.route("/stopTracker")
def stopTracker():
    trackerRunning = 0
    return jsonify({'status':str(200)})

@app.route("/changeTrackPeriod",methods=["GET","POST"])
def changeTrackPeriod():
    if request.method == "POST":
        data = json.loads(request.data)
        print("data",data)
        if int(data["trackPeriod"])!=0:
            trackPeriod = int(data["trackPeriod"])
            return jsonify({'status':str(200)})
        else:
            return jsonify({'status':str(400)})    
    else:
        return jsonify({'status':str(400)}) 




if __name__ == "__main__":
    fetchFirebaseData() 
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)),debug=True,use_reloader=True)    