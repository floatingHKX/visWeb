from flask import Flask, render_template, request
from flask_sockets import Sockets
from utility.myDocker import ClientHandler, DockerStreamThread
import conf

app = Flask(__name__)
sockets = Sockets(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images')
def get_images():
    dockerCli = ClientHandler(base_url=conf.DOCKER_HOST)
    images = dockerCli.listImages()
    print(images)


@app.route('/newcontainer', methods=["GET"])
def get_new_container():
    image_version = request.values.get('imageVersion')
    dockerCli = ClientHandler(base_url=conf.DOCKER_HOST)

    container = dockerCli.createContainer(image_version)
    if container is None:
        return "None"
    dockerCli.startContainer(container)
    return container['Id']

@app.route('/analysis')
def start_analysis():
    pass


@sockets.route('/echo')
def echo_socket(ws):
    dockerCli = ClientHandler(base_url=conf.DOCKER_HOST, timeout=1000)
    container_id = input()
    # terminalExecId = dockerCli.creatTerminalExec(conf.CONTAINER_ID)
    terminalExecId = dockerCli.creatTerminalExec(container_id)
    terminalStream = dockerCli.startTerminalExec(terminalExecId)._sock

    terminalThread = DockerStreamThread(ws, terminalStream)
    terminalThread.start()

    while not ws.closed:
        message = ws.receive()
        if message is not None:
            terminalStream.send(bytes(message, encoding='utf-8'))


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
