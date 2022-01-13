from email.mime import image
from http import client
import re
import os
import socket
from multiprocessing import Process
from urllib import request

SERVER_PORT = 8080
ROOT = '/var/www/html/demo'

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

        request_data = client_socket.recv(1024)
        print(request_data)
        print('--------------------------------------------------------')
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

        #构造响应数据
        response = bytes(response_start_line + response_headers + '\r\n', 'utf-8') + response_body

        client_socket.send(response)

        client_socket.close()

if __name__ == '__main__':
    http_server = HTTPServer()
    http_server.bind(SERVER_PORT)
    http_server.start()
