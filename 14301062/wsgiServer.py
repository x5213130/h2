from __future__ import unicode_literals
import socket
import StringIO
import sys
import datetime
import os

class wsgiServer(object):
    socket_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 10

    def __init__(self, address):
        self.socket = socket.socket(self.socket_family, self.socket_type)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(address)
        self.socket.listen(self.request_queue_size)
        host, port = self.socket.getsockname()[:2]
        self.host = host
        self.port = port


    def setApplication(self, application):
        self.application = application

    def beginServer(self):
        print "开始监听:"
        while 1:
            self.connection, client_address = self.socket.accept()
            self.sendRequest()

    def sendRequest(self):
        self.request_data = self.connection.recv(1024)
        self.request_lines = self.request_data.splitlines()
        try:
            self.getUrl()
            env = self.getEnvironment()

            print env['PATH_INFO'][1:]

            if env['PATH_INFO'][1:].endswith(".html"):
                application = 'app1'
            else:
                application = 'app2'

            application = getattr(module, application)
            httpd.setApplication(application)

            app_data = self.application(env, self.startResponse)
            self.finishResponse(app_data)
            print '[{0}] "{1}" {2}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                           self.request_lines[0], self.status)
        except Exception, e:
            pass

    def getUrl(self):
        self.request_dict = {'Path': self.request_lines[0]}
        for itm in self.request_lines[1:]:
            if ':' in itm:
                self.request_dict[itm.split(':')[0]] = itm.split(':')[1]
        self.request_method, self.path, self.request_version = self.request_dict.get('Path').split()

    def getEnvironment(self):
        env = {
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': StringIO.StringIO(self.request_data),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'REQUEST_METHOD': self.request_method,
            'PATH_INFO': self.path,
            'SERVER_NAME': self.host,
            'SERVER_PORT': self.port,
            'USER_AGENT': self.request_dict.get('User-Agent')
        }
        return env


    def startResponse(self, status, response_headers):
        headers = [
            ('Date', datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')),
            ('Server', 'RAPOWSGI0.1'),
        ]
        self.headers = response_headers + headers
        self.status = status

    def finishResponse(self, app_data):
        try:
            response = 'HTTP/1.1 {status}\r\n'.format(status=self.status)
            for header in self.headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in app_data:
                response += data
            self.connection.sendall(response)
        finally:
            self.connection.close()

def app1(environ, start_response):

    filename = environ['PATH_INFO'][1:]

    if os.path.exists(filename):
        f = open(filename, "r")
        line = f.readline()
        message = line
        while line:
            line = f.readline()
            message = message + line

        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [message]
    else:
        status = '404 NOT FOUND'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return ['Can not find the file!']

def app2(environ, start_response):

    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)

    return ['Hello ', environ['PATH_INFO'][1:]]


if __name__ == '__main__':

    httpd = wsgiServer(('', int(8888)))

    print "服务器已启动."

    module = 'wsgiServer'
    module = __import__(module)

    httpd.beginServer()
