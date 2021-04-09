from utility.myDocker import ClientHandler, DockerStreamThread
import conf

class TerminalService(object):

    def __init__(self):
        self.clientHandle = ClientHandler(base_url=conf.DOCKER_HOST, timeout=1000)

    def creatTerminalExec(self, containerId):
        execCommand = [
            "/bin/sh",
            "-c",
            'TERM=xterm-256color; export TERM; [ -x /bin/bash ] && ([ -x /usr/bin/script ] && /usr/bin/script -q -c "/bin/bash" /dev/null || exec /bin/bash) || exec /bin/sh']
        execOptions = {
            "tty": True,
            "stdin": True
        }
        return self.clientHandle.containerExecCmd(containerId, execCommand, **execOptions)

    def terminalThreadCreate(self, ws, terminalStream):
        terminalThread = DockerStreamThread(ws, terminalStream)
        terminalThread.start()

        while not ws.closed:
            message = ws.receive()
            if message is not None:
                terminalStream.send(bytes(message, encoding='utf-8'))