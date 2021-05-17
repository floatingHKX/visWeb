from flask import Flask, render_template, request
from flask_sockets import Sockets
from utility.myDocker import ClientHandler, DockerStreamThread
from service.terminalService import TerminalService
from service.replayService import ReplayService
import conf
from flask_cors import *
from flask import jsonify
from utility.dataBase import DataBase
from service.manageService import ManageService
import os
from flask_apscheduler import APScheduler


class SchedulerConfig(object):
    JOBS = [
        {
            'id': 'flash_projects',
            'func': '__main__:flash_projects',
            'args': None,
            'trigger': 'interval',
            'seconds': 5
        }
    ]


def flash_projects():
    print('schedule task:xxx')


app = Flask(__name__)
CORS(app, supports_credentials=True)
sockets = Sockets(app)
app.config.from_object(SchedulerConfig())


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
    image_version = request.values.get('os')
    userId = request.values.get('userId')
    dockerCli = ClientHandler(base_url=conf.DOCKER_HOST)
    manageService = ManageService()

    container = dockerCli.createContainer(image_version, command=["/bin/sh", "-c", "while :; do sleep 1; done"])
    if container is None:
        return {'success': False}
    dockerCli.startContainer(container)
    result = {'containerId': container['Id'], 'success': True}
    manageService.add_container(userId, container['Id'])
    # result = {'Id': 55, 'Success': True}
    return jsonify(result)


'''
开始分析
'''
@app.route('/analysis', methods = ['POST','GET'])
def start_analysis():
    # 获得用户id
    userId = request.values.get('userId')
    # 漏洞重现的容器id
    containerId = request.values.get('containerId')
    # lib版本号
    libVersion = request.values.get('libVersion')
    # 分析启动队列
    analysisEnable = request.values.get('analysisEnable')
    # 二进制文件名
    binaryName = request.values.get('binaryName')
    # 任务名
    projectName = request.values.get('projectName')
    replayService = ReplayService()
    result = replayService.startReplayAnalysis(userId, containerId, binaryName, analysisEnable, libVersion, projectName)
    return jsonify(result)

'''
中断分析
'''
@app.route('/terminate', methods = ['POST','GET'])
def terminate_analysis():
    projectId = request.values.get('projectId')
    replayService = ReplayService()
    result = replayService.terminateAnalysis(projectId)
    return result

"""
删除任务
"""
@app.route('/deleteproject')
def delete_project():
    projectId = request.values.get('projectId')
    manageService = ManageService()
    return manageService.delete_project(projectId)

'''
删除容器
'''
@app.route('/container/delete',methods = ['POST','GET'])
def delete_container():
    containerId = request.values.get('containerId')
    manageService = ManageService()
    manageService.delete_container(containerId)
    return "OK"

"""
获得containerId
"""
@app.route('/container/getid')
def get_containerId_by_userId():
    userId = request.values.get('userId')
    manageService = ManageService()
    containerId = manageService.get_containerId(userId)
    if containerId is None:
        return jsonify({'success': False})
    return jsonify({'containerId': containerId, 'success': True})

@app.route('/projects')
def get_projectsInfoList():
    userId = request.values.get('userId')
    pageNo = int(request.values.get('pageNo'), 10)
    pageSize = int(request.values.get('pageSize'), 10)
    manageService = ManageService()
    results = manageService.get_projects(userId, pageNo, pageSize)
    return jsonify(results)

'''
生成websocket链接
'''
@sockets.route('/echo/<containerId>')
def echo_socket(ws, containerId):
    terminalService = TerminalService()
    execId, terminalStream = terminalService.creatTerminalExec(containerId)
    terminalService.terminalThreadCreate(ws, terminalStream._sock)

def init_filedir():
    if not os.access(conf.HOST_WOKR_PATH, os.F_OK):
        print("workplace %s do not exist." % conf.HOST_WOKR_PATH)
        os.system("mkdir %s" % conf.HOST_WOKR_PATH)
        print("workplace %s create now." % conf.HOST_WOKR_PATH)

if __name__ == '__main__':
    init_filedir()
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
