import sys
import json
import ssl

class API():
    def __init__(self):
        self.IS_PY3 = sys.version_info.major == 3
        if self.IS_PY3:
            from urllib.request import urlopen
            from urllib.request import Request
            from urllib.error import URLError
            from urllib.parse import urlencode
            from urllib.parse import quote_plus
            from LAC import LAC
            self.urlopen = urlopen
            self.Request = Request
            self.URLError = URLError
            self.urlencode = urlencode
            self.quote_plus = quote_plus
            self.lac = LAC(mode = 'lac')
        
        ssl._create_default_https_context = ssl._create_unverified_context
        self.API_KEY = 'NSUVdo3wzXSOUfGammwAaXzy'
        self.SECRET_KEY = 'UMC3KS7x3SMkYP09LTiPUXcVXyEav7i2'
        self.EASYDL_TEXT_CLASSIFY_URL_1 = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/intros_gen"
        self.EASYDL_TEXT_CLASSIFY_URL_2 = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/tripSug"
        self.TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
        self.punctuation_list = [ '.', '。', '?', '？', '!', ';', '；']
        self.text_1 = ""#介绍性文本
        self.text_2 = ""#旅行性文本
        self.holeLabellist = ['PER', 'LOC', 'ORG', 'TIME', 'nz', 'nw']
        self.holeLoc = []
        self.holeResult = '填空：' #填空文本以及出现填空的文本
        self.count = 0
    
    def fetch_token(self,params):
        params = {'grant_type': 'client_credentials',
                  'client_id': self.API_KEY,
                  'client_secret': self.SECRET_KEY}
        post_data = self.urlencode(params)
        if (self.IS_PY3):
            post_data = post_data.encode('utf-8')
        req = self.Request(self.TOKEN_URL, post_data)
        try:
            f = self.urlopen(req, timeout=5)
            result_str = f.read()
            #print('success')
        except self.URLError as err:
            print(err)
        if (self.IS_PY3):
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
        if self.IS_PY3:
            req =self. Request(url, json.dumps(data).encode('utf-8'))
        else:
            req = self.Request(url, json.dumps(data))

        has_error = False
        try:
            f = self.urlopen(req)
            result_str = f.read()
            if (self.IS_PY3):
                result_str = result_str.decode()
            return result_str
        except self.URLError as err:
            print(err)

    def cut(self, content):
        length = len(content)
        for i in range(length):
            if content[i] in self.punctuation_list:
                count = i
        result_content = content[:count+1]
        return result_content

    def Introduce(self, location):
        # 获取access token
        token = self.fetch_token()

        # 拼接url
        url = self.EASYDL_TEXT_CLASSIFY_URL_1 + "?access_token=" + token
        text = '地点：' + location +' 介绍：'

        # 请求接口
        # 测试
        response = self.request(url,
                           {
                               'text': text,
                               'max_gen_len': 128
                           })
        err = 0
        if "result" in json.loads(response):
            content = json.loads(response)['result']['content']
            result_content = self.cut(content)
            self.introduce = result_content
        else:
            result_content = ""
            err = json.loads(response)['error_code']
        return {"Introduce":result_content,"error":err}


    def hole(self):
        self.count = 0
        lac_result = self.lac.run(self.text_1)
        i,sumLength = 0,0
        for label in lac_result[1]:
            length = len(lac_result[0][i])
            if label in self.holeLabellist:
                self.holeResult = self.holeResult + '__' * (length + 1)
                self.holeLoc.append([sumLength, sumLength + length])
            else:
                self.holeResult = self.holeResult + lac_result[0][i]
            sumLength += length
            i += 1

    def fix(self):
        x = self.holeLoc[self.count][0]
        y = self.holeLoc[self.count][1]
        self.holeResult = self.holeResult[:x + 4 + 2 * self.count] + self.text_1[x:y] + self.holeResult[x + 4 + 2 * (y - x + self.count):]
        self.count += 1
        if self.count == len(self.holeLoc):
            return 1
        return 0

    def Suggest(self, location):
        # 获取access token
        token = self.fetch_token()

        # 拼接url
        url = self.EASYDL_TEXT_CLASSIFY_URL_2 + "?access_token=" + token
        text = '问题：去' + location +'旅行有什么建议 回答：'

        # 请求接口
        # 测试
        response = self.request(url,
                           {
                               'text': text,
                               'max_gen_len': 128
                           })
        err = 0
        if "result" in json.loads(response):
            content = json.loads(response)['result']['content']
            result_content = self.cut(content)
        else:
            result_content = ""
            err = json.loads(response)['error_code']
        return {"Suggest":result_content,"error":err}
