from socket import timeout
import ssl
import json
from time import sleep
from LAC import LAC
from urllib3 import PoolManager
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ssl._create_default_https_context = ssl._create_unverified_context  

VILG_TOKEN_URL = 'https://wenxin.baidu.com/younger/portal/api/oauth/token'
EASYDL_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
SUGGEST_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/Travel_tips"
VILG_URL = 'https://wenxin.baidu.com/younger/portal/api/rest/1.0/ernievilg/v1/txt2img'
BACKGROUND_URL = 'https://wenxin.baidu.com/younger/portal/api/rest/1.0/ernievilg/v1/getImg'

INTRODUCTION_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/Introduction"

PUNCTUATION = set([ '.', '。', '?', '？', '!', ';', '；'])
HOLE_LABEL = ['PER', 'LOC', 'ORG', 'TIME', 'nz', 'nw']

class ERNIE_API():
    def __init__(self, easydl_key:dict, vilg_key:dict):
        self.location = None
        self.introduce = None
        self.holeLoc = []
        self.hole_result = '填空：'
        self.counter = 0
        self.lac = LAC(mode = 'lac')
        self.http = PoolManager()

        self.easydl_token = self.__fetch_token(easydl_key, token_kind='EASYDL')
        self.vilg_token = self.__fetch_token(vilg_key, token_kind='VILG')
    
    def __request(self, url:str, data:dict):
        data = urlencode(data) if url == EASYDL_TOKEN_URL or url == VILG_TOKEN_URL else json.dumps(data)
        request = Request(url, data.encode('utf-8'))
        response = urlopen(request)
        response = response.read().decode()
        return response

    def __fetch_token(self, key:dict, token_kind:str='EASYDL') -> str:
        data = {
            'grant_type': 'client_credentials',
            'client_id': key['API_KEY'],
            'client_secret': key['SECRET_KEY']
        }
        if token_kind.upper() == 'EASYDL':
            response = json.loads(self.__request(EASYDL_TOKEN_URL, data))
            return response['access_token']
            
        elif token_kind.upper() == 'VILG':
            response = json.loads(self.__request(VILG_TOKEN_URL, data))
            return response['data']
        
        raise Exception

    def __cut(self, content):
        length = len(content)
        count = 0
        for i in range(length):
            if content[i] in PUNCTUATION:
                count = i
        result_content = content[:count+1]
        return result_content
    
    def Introduce(self, location:str) -> str:
        self.location = location

        url = INTRODUCTION_URL + '?access_token=' + self.easydl_token
        data = {
            'text': '地点：' + location + ' 介绍：',
            'max_gen_len': 128
        }

        response = self.__request(url, data)

        content = json.loads(response)['result']['content']
        result_content = self.__cut(content)
        self.introduce = result_content

        return result_content
    
    def Cut(self):
        self.counter = 0
        self.holeResult = '填空：'
        self.holeLoc = []
        lac_result = self.lac.run(self.introduce)
        i,sumLength = 0,0
        for label in lac_result[1]:
            length = len(lac_result[0][i])
            if label in HOLE_LABEL:
                self.holeResult = self.holeResult + '__' * (length + 1)
                self.holeLoc.append([sumLength, sumLength + length])
            else:
                self.holeResult = self.holeResult + lac_result[0][i]
            sumLength += length
            i += 1

    def Next(self):
        if self.counter >= len(self.holeLoc):
            return True
        x = self.holeLoc[self.counter][0]
        y = self.holeLoc[self.counter][1]
        self.holeResult = self.holeResult[:x + 4 + 2 * self.counter] + self.introduce[x:y] + self.holeResult[x + 4 + 2 * (y - x + self.counter):]
        self.counter += 1
        if self.counter >= len(self.holeLoc):
            return True
        return False

    def Suggest(self) -> str:
        url = SUGGEST_URL + '?access_token=' + self.easydl_token
        data = {
            'text': '问题：去' + self.location +'旅行有什么建议 回答：',
            'max_gen_len': 128
        }

        response = self.__request(url, data)

        err = False
        if "result" in json.loads(response):
            content = json.loads(response)['result']['content']
            result_content = self.__cut(content)
        else:
            result_content = ""
            err = json.loads(response)['error_code'] != 0
        return {"suggest":result_content,"error":err}

    def Text2Image(self, location:str) -> str:
        #请求图像
        data = {
            'access_token': self.vilg_token,
            'text': location,
            'style': '中国画'
        }

        response = self.http.request('POST', VILG_URL, data, timeout=30)
        taskId = json.loads(response.data)['data']['taskId']

        #等待请求结果
        while(1):
            data = {
                'access_token': self.vilg_token, 
                'taskId': taskId
            }

            response = json.loads(self.http.request('POST', BACKGROUND_URL, data).data)
            print(response)
            if response['data']['img'] != '':
                return response['data']['img']
            else:
                sleep(10)