import os
from time import sleep
import eel
import ssl
from ERNIE_API import ERNIE_API

ssl._create_default_https_context = ssl._create_unverified_context  

KEYS = {
    'introduce_key':{
        'API_KEY':'X6CNT7VlkVOWQA5KvOld1GN7', 
        'SECRET_KEY':'30K9GYZpDwMSE4Vm0uPPBW9deUNrcDGU'
    },
    'suggest_key':{
        #'API_KEY':'9GtCALtidmTe1ryMkXeInfHZ', 
        #'SECRET_KEY':'eg3l1raYvtqsoo1qNTsDGvFV3eRskGGS'
        'API_KEY':'X6CNT7VlkVOWQA5KvOld1GN7', 
        'SECRET_KEY':'30K9GYZpDwMSE4Vm0uPPBW9deUNrcDGU'
    }, 
    'vilg_key':{
        'API_KEY':'GKN0nu7vzKhAii9VDQI8vUiUAC0ElO4W', 
        'SECRET_KEY':'XR8Zia0YLTQcBSYqHD00kNTUyjoWtGdr'
    }
}

api = None

@eel.expose
def Introduce(location):
    introduce = api.Introduce(location)
    eel.getJSON({'introduce':introduce['introduce'], 'error':introduce['error']})

@eel.expose
def NewIntroduce():
    introduce = api.Introduce(api.location)
    eel.getJSON({'introduce':introduce['introduce'], 'error':introduce['error']})

@eel.expose
def Cut():
    api.Cut()
    eel.getJSON({"cut":api.holeResult})

@eel.expose
def Next():
    flag = api.Next()
    eel.getJSON({"next":api.holeResult, "finished": flag})

@eel.expose
def Suggest():
    suggest = ''
    while(1):
        suggest = api.Suggest()
        if not suggest['error'] and len(suggest['suggest']) >= 5:
            break
        sleep(1)
    eel.getJSON({"suggest":suggest['suggest'], 'error':suggest['error']})

@eel.expose
def Text2Image(location):
    image_url = api.Text2Image(location)
    eel.getJSON({'image_url':"url(" + image_url + ")"})

if __name__ == "__main__":
    api = ERNIE_API(KEYS)
    eel.init(os.getcwd())
    eel.start("index.html", mode="edge")