import eel
import os
import time
import sys
import json
import ssl

from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus
from LAC import LAC

ssl._create_default_https_context = ssl._create_unverified_context
API_KEY_1 = 'NSUVdo3wzXSOUfGammwAaXzy'
SECRET_KEY_1 = 'UMC3KS7x3SMkYP09LTiPUXcVXyEav7i2'
EASYDL_TEXT_CLASSIFY_URL_1 = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/intro_1"
API_KEY_2 = ''
SECRET_KEY_2 = ''
EASYDL_TEXT_CLASSIFY_URL_2 = ''
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
PUNCTUATION_LIST = [',', '，', '.', '。', '?', '？', '!', ';', '；']
HOLE_LABEL_LIST = ['PER', 'LOC', 'ORG', 'TIME', 'nz', 'nw']

class API():
    def __init__(self):
        self.location = None
        self.introduce = None
        self.holeLoc = []
        self.holeResult = '填空：' #填空文本以及出现填空的文本
        self.counter = 0
        self.lac = LAC(mode = 'lac')
    
    def Introduce(self, location):
        self.location = location
        params = {'grant_type': 'client_credentials',
                  'client_id': API_KEY_1,
                  'client_secret': SECRET_KEY_1}
        # 获取access token
        token = self.fetch_token(params)

        # 拼接url
        url = EASYDL_TEXT_CLASSIFY_URL_1 + "?access_token=" + token
        text = '地点：' + location +' 介绍：'

        # 请求接口
        # 测试
        response = self.request(url,
                           {
                               'text': text,
                               'max_gen_len': 128
                           })

        content = json.loads(response)['result']['content']
        result_content = self.cut(content)
        self.introduce = result_content

        return result_content
    
    def Cut(self):
        self.counter = 0
        self.holeResult = '填空：'
        lac_result = self.lac.run(self.introduce)
        i,sumLength = 0,0
        for label in lac_result[1]:
            length = len(lac_result[0][i])
            if label in HOLE_LABEL_LIST:
                self.holeResult = self.holeResult + '__' * length
                self.holeLoc.append([sumLength, sumLength + length])
            else:
                self.holeResult = self.holeResult + lac_result[0][i]
            sumLength += length
            i += 1
    
    def Next(self):
        x = self.holeLoc[self.counter][0]
        y = self.holeLoc[self.counter][1]
        self.holeResult = self.holeResult[:x + 3] + self.introduce[x:y] + self.holeResult[x + 3 + 2 * (y - x):]
        self.counter += 1
        if self.counter >= len(self.holeLoc):
            return True
        return False
    
    #根据列表和计数器挖空
    
    def Suggest(self, location):
        params = {'grant_type': 'client_credentials',
                  'client_id': API_KEY_2,
                  'client_secret': SECRET_KEY_2}

        # 获取access token
        token = self.fetch_token(params)

        # 拼接url
        url = EASYDL_TEXT_CLASSIFY_URL_2 + "?access_token=" + token
        text = '问题：去' + location +'旅行有什么建议 回答：'

        # 请求接口
        # 测试
        response = self.request(url,
                           {
                               'text': text,
                               'max_gen_len': 128
                           })

        content = json.loads(response)['result']['content']
        result_content = self.cut(content)

        return result_content

    def fetch_token(self,params):
        post_data = urlencode(params)
        post_data = post_data.encode('utf-8')
        req = Request(TOKEN_URL, post_data)
        try:
            f = urlopen(req, timeout=5)
            result_str = f.read()
        except URLError as err:
            print(err)
        result_str = result_str.decode()

        result = json.loads(result_str)

        if ('access_token' in result.keys() and 'scope' in result.keys()):
            if not 'brain_all_scope' in result['scope'].split(' '):
                print('please ensure has check the  ability')
                exit()
            return result['access_token']
        else:
            print('please overwrite the correct API_KEY and SECRET_KEY')
            exit()

    def request(self, url, data):
        req =Request(url, json.dumps(data).encode('utf-8'))

        has_error = False
        try:
            f = urlopen(req)
            result_str = f.read()
            result_str = result_str.decode()
            return result_str
        except URLError as err:
            print(err)

    def cut(self, content):
        length = len(content)
        for i in range(length):
            if content[i] in PUNCTUATION_LIST:
                count = i
        result_content = content[:count+1]
        return result_content

api = None

@eel.expose
def Introduce(location):
    introduce = api.Introduce(location)
    eel.getJSON({"introduce":introduce})

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
    suggest = api.Suggest()
    eel.getJSON({"suggest":suggest})

if __name__ == "__main__":
    api = API()
    eel.init(os.getcwd())
    eel.start("label.html", mode="edge")