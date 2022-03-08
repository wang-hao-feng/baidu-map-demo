import ssl
import json
import socket

from multiprocessing import Process
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from LAC import LAC

SERVER_PORT = 8080
ROOT = '/var/www/html/demo'
ssl._create_default_https_context = ssl._create_unverified_context
API_KEY = 'NSUVdo3wzXSOUfGammwAaXzy'
SECRET_KEY = 'UMC3KS7x3SMkYP09LTiPUXcVXyEav7i2'
EASYDL_TEXT_CLASSIFY_URL_1 = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/intros_gen"
EASYDL_TEXT_CLASSIFY_URL_2 = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/text_gen/tripSug"
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
PUNCTUATION_LIST = [ '.', '。', '?', '？', '!', ';', '；']
HOLE_LABEL_LIST = ['PER', 'LOC', 'ORG', 'TIME', 'nz', 'nw']

api = None

class API():
    def __init__(self):
        self.lac = LAC(mode = 'lac')
    
    def Introduce(self, location):
        # 获取access token
        token = self.fetch_token()

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

        err = 0
        if 'result' in json.loads(response):
            content = json.loads(response)['result']['content']
            result_content = self.cut(content)
        else:
            result_content = ''
            err = json.loads(response)['error_code']

        return {'introduce':result_content, 'error':err}
    
    def BeginTest(self, introduce):
        test = '填空：'
        loc = []
        lac_result = self.lac.run(introduce)
        i,sumLength = 0,0
        for label in lac_result[1]:
            length = len(lac_result[0][i])
            if label in HOLE_LABEL_LIST:
                test = test + '__' * (length + 1)
                loc.append([sumLength, sumLength + length])
            else:
                test = test + lac_result[0][i]
            sumLength += length
            i += 1
        return {'test':test, 'loc':loc}
    
    def Next(self, introduce, counter, test, loc):
        loc = loc.split(',')
        counter = int(counter)
        counter += 1
        for i in range(counter):
            x = int(loc[2 * i])
            y = int(loc[2 * i + 1])
            test = test[:x + 4 + 2 * i] + introduce[x:y] + test[x + 4 + 2 * (y - x + i):]
        finished = counter * 2 >= len(loc)
        
        return {'counter':counter, 'test':test, 'finished':finished}
    
    #根据列表和计数器挖空
    
    def Suggest(self, location):
        # 获取access token
        token = self.fetch_token()

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

        err = 0
        if "result" in json.loads(response):
            content = json.loads(response)['result']['content']
            result_content = self.cut(content)
        else:
            result_content = ""
            err = json.loads(response)['error_code']
        return {"suggest":result_content,"error":err}

    def fetch_token(self):
        params = {'grant_type': 'client_credentials',
                  'client_id': API_KEY,
                  'client_secret': SECRET_KEY}
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

        try:
            f = urlopen(req)
            result_str = f.read()
            result_str = result_str.decode()
            return result_str
        except URLError as err:
            print(err)

    def cut(self, content):
        length = len(content)
        count = 0
        for i in range(length):
            if content[i] in PUNCTUATION_LIST:
                count = i
        result_content = content[:count+1]
        return result_content

class HTTPServer():
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.listen(128)
        while True:
            client_socket, _ = self.server_socket.accept()
            handle_client_procress = Process(target=self.handle_client, args=(client_socket,))
            handle_client_procress.start()
            client_socket.close()

    def bind(self, port):
        self.server_socket.bind(('', port))

    def handle_client(self, client_socket):
        response_start_line = 'HTTP/1.1 200 OK \r\n'
        response_headers = "Server: 180.76.120.243\r\n"
        response_body = bytes("", 'utf-8')

        request_data = client_socket.recv(10240)
        request_lines = request_data.decode().splitlines()

        #解析报文
        request_start_line = request_lines[0].split(' ')
        method = request_start_line[0]

        if method == 'GET':
            file_name = request_start_line[1]
            file_name = '/index.html' if file_name == '/' else file_name
            try:
                with open(ROOT + file_name, 'rb') as file:
                    file_data = file.read()
                    response_body = file_data
            except IOError:
                response_start_line = "HTTP/1.1 404 Not Found\r\n"
        elif method == 'POST':
            message = json.loads(request_lines[-1])
            args = message['args']
            if message['method'] == 'Introduce':
                introduce = api.Introduce(args['location'])
                response_body = bytes(json.dumps(introduce), 'utf-8')
            elif message['method'] == 'BeginTest':
                test = api.BeginTest(args['introduce'])
                response_body = bytes(json.dumps(test), 'utf-8')
            elif message['method'] == 'Next':
                next = api.Next(args['introduce'], args['counter'], args['test'], args['loc'])
                response_body = bytes(json.dumps(next), 'utf-8')    
            elif message['method'] == 'Suggest':
                suggest = api.Suggest(args['location'])
                response_body = bytes(json.dumps(suggest), 'utf-8')

        #构造响应数据
        response = bytes(response_start_line + response_headers + '\r\n', 'utf-8') + response_body

        client_socket.send(response)

        client_socket.close()

if __name__ == '__main__':
    api = API()
    http_server = HTTPServer()
    http_server.bind(SERVER_PORT)
    http_server.start()
