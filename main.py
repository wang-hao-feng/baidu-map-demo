import eel
import json
import os
import time

sleep_time = 0

class API():
    def __init__(self):
        self.location = None
        self.introduce = None
        self.cut_list = []
        self.counter = 0
        return
    
    def Introduce(self, location):
        self.location = location
        #调用api获得介绍文本
        self.introduce = time.sleep(sleep_time)
        return "introduce"
    
    def Cut(self):
        self.counter = 0
        #调用api获得空的位置
        self.cut_list = time.sleep(sleep_time)
        return "cut"
    
    def Next(self):
        if self.counter >= 2:
            return "next_finished", True
        self.counter += 1
        return "next" + str(self.counter), False
    
    #根据列表和计数器挖空
    def Dig(self):
        string = self.introduce
        for i in range(self.counter, len(self.cut_list), 1):
            [head, tail] = self.cut_list[i]
            string = string[:head] + '__' * (tail - head) + string[tail:]
        return string
    
    def Suggest(self):
        #调用api获得旅行建议
        time.sleep(sleep_time)
        return "suggest"

api = None

@eel.expose
def Introduce(location):
    introduce = api.Introduce(location)
    eel.getJSON({"introduce":introduce})

@eel.expose
def Cut():
    cut = api.Cut()
    eel.getJSON({"cut":cut})

@eel.expose
def Next():
    next, flag = api.Next()
    eel.getJSON({"next":next, "finished": flag})

@eel.expose
def Suggest():
    suggest = api.Suggest()
    eel.getJSON({"suggest":suggest})

if __name__ == "__main__":
    api = API()
    eel.init(os.getcwd())
    eel.start("index.html", mode="edge")