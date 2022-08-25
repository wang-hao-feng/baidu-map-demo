import ssl
import json
from time import sleep
from LAC import LAC
from urllib3 import PoolManager
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ssl._create_default_https_context = ssl._create_unverified_context  

#请求access_token的url
VILG_TOKEN_URL = 'https://wenxin.baidu.com/younger/portal/api/oauth/token'
EASYDL_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'

#模型url
INTRODUCTION_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/intros_gen"
SUGGEST_URL = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/tripSug'
""" SUGGEST_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/Travel_tips" """
VILG_URL = 'https://wenxin.baidu.com/younger/portal/api/rest/1.0/ernievilg/v1/txt2img'
BACKGROUND_URL = 'https://wenxin.baidu.com/younger/portal/api/rest/1.0/ernievilg/v1/getImg'

#标点符号集
PUNCTUATION = set([ '.', '。', '?', '？', '!', ';', '；'])
#挖空所使用的命名实体类别
HOLE_LABEL = ['PER', 'LOC', 'ORG', 'TIME', 'nz', 'nw']

class ERNIE_API():
    def __init__(self, keys:dict):
        self.location = None            #缓存当前查询的地点
        self.introduce = None           #缓存景点介绍，用于后续挖空生成题目
        self.holeLoc = []               #填空题答案
        self.counter = 0                #空的数量
        self.lac = LAC(mode = 'lac')
        self.http = PoolManager()

        #调用模型所需的access_token
        self.introduce_token = self.__fetch_token(keys['introduce_key'], token_kind='EASYDL')
        self.suggest_token = self.__fetch_token(keys['suggest_key'], token_kind='EASYDL')
        self.vilg_token = self.__fetch_token(keys['vilg_key'], token_kind='VILG')
    
    def __request(self, url:str, data:dict, fetch_token:bool=False) -> str:
        """向url发送数据

        Args:
            url (str): 目标url
            data (dict): 需要发送的数据
            fetch_token (bool, optional): 标记是否申请token，默认为False

        Returns:
            str: 返回的报文
        """
        #请求access_token与向模型发送参数所需的数据编码方式不同
        data = urlencode(data) if fetch_token else json.dumps(data)
        request = Request(url, data.encode('utf-8'))
        response = urlopen(request)
        response = response.read().decode()
        return response

    def __fetch_token(self, key:dict, token_kind:str='EASYDL') -> str:
        """请求调用模型所需的access_token

        Args:
            key (dict): 请求access_token所需的api key
            token_kind (str, optional): 请求access_token的类别，默认为'EASYDL'.

        Returns:
            str: access_token
        """
        data = {
            'grant_type': 'client_credentials',
            'client_id': key['API_KEY'],
            'client_secret': key['SECRET_KEY']
        }
        if token_kind.upper() == 'EASYDL':
            response = json.loads(self.__request(EASYDL_TOKEN_URL, data, fetch_token=True))
            return response['access_token']
            
        elif token_kind.upper() == 'VILG':
            response = json.loads(self.__request(VILG_TOKEN_URL, data, fetch_token=True))
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
        """调用模型生成景点介绍

        Args:
            location (str): 景点名

        Returns:
            str: 模型生成的景点介绍
        """
        self.location = location

        url = INTRODUCTION_URL + '?access_token=' + self.introduce_token
        data = {
            'text': '地点：' + location + ' 介绍：',
            'max_gen_len': 128
        }

        response = self.__request(url, data)

        err = 0
        if 'result' in json.loads(response):
            content = json.loads(response)['result']['content']
            result_content = self.__cut(content)
        else:
            result_content = ''
            err = json.loads(response)['error_code']
        self.introduce = result_content

        return {'introduce':result_content, 'error':err}
    
    def Cut(self):
        """根据景点介绍生成填空题
        """
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

    def Next(self) -> bool:
        """向填空题中填入一个答案

        Returns:
            bool: 表示是否填完所有空
        """
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
        """调用模型生成旅行建议

        Returns:
            str: 模型生成的旅行建议
        """
        url = SUGGEST_URL + '?access_token=' + self.suggest_token
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
        """调用模型生成水彩背景 

        Args:
            location (str): 景点名

        Returns:
            str: 模型生成的图片的url
        """
        #请求图像
        data = {
            'access_token': self.vilg_token,
            'text': location,
            'style': '水彩'
        }

        response = self.http.request('POST', VILG_URL, data, timeout=30)
        print(json.loads(response.data)['msg'])
        taskId = json.loads(response.data)['data']['taskId']

        #等待请求结果
        while(1):
            data = {
                'access_token': self.vilg_token, 
                'taskId': taskId
            }

            response = json.loads(self.http.request('POST', BACKGROUND_URL, data).data)
            #print(response)
            if response['data']['img'] != '':
                return response['data']['img']
            else:
                sleep(30)