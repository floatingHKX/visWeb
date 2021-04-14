from flask import Flask, render_template, request
from flask_sockets import Sockets
from utility.myDocker import ClientHandler, DockerStreamThread
from service.terminalService import TerminalService
from service.replayService import ReplayService
import conf
import os

app = Flask(__name__)
sockets = Sockets(app)


@app.route('/container/<containerId>')
def index(containerId):
    # containerId = request.values.get('containerId')
    return render_template('index.html', containerId=containerId)


@app.route('/images')
def get_images():
    dockerCli = ClientHandler(base_url=conf.DOCKER_HOST)
    images = dockerCli.listImages()
    print(images)


'''
申请新容器
'''
@app.route('/newcontainer')
def get_new_container():
    image_version = request.values.get('imageVersion')
    dockerCli = ClientHandler(base_url=conf.DOCKER_HOST)

    container = dockerCli.createContainer(image_version, command=["/bin/sh", "-c", "while :; do sleep 1; done"])
    # containers = dockerCli.listContainers()
    # container = containers[0]
    if container is None:
        return "None"
    dockerCli.startContainer(container)
    return container['Id']


'''
开始分析
'''
@app.route('/analysis')
def start_analysis():
    # 漏洞重现的容器id
    containerId = request.values.get('containerId')
    # lib版本号
    libVersion = request.values.get('libVersion')
    # 分析启动队列
    analysisEnable = request.values.get('analysisEnable')
    # 二进制文件名
    binaryName = request.values.get('binaryName')
    replayService = ReplayService()
    if replayService.isReplayContainerExist() == False:
        replayService.createReplayContainer()

    replayService.startReplayAnalysis(containerId, binaryName, analysisEnable, libVersion)
    return "OK"


'''
生成websocket链接
'''
@sockets.route('/echo/<containerId>')
def echo_socket(ws, containerId):
    terminalService = TerminalService()
    terminalStream = terminalService.creatTerminalExec(containerId)._sock
    terminalService.terminalThreadCreate(ws, terminalStream)


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
