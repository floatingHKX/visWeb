#!/usr/bin/env python
# coding: utf-8

import docker
import threading
import os
import subprocess
import conf
from utility.dataBase import DataBase
import utility.common

class ClientHandler(object):

    def __init__(self, **kwargs):
        self.dockerClient = docker.APIClient(**kwargs)

    def containerExecCmd(self, containerId,  execCommand, socket=False, stream=False, **execOptions):
        '''
        运行的容器执行命令
        '''
        # Sets up an exec instance in a running container.
        execId = self.dockerClient.exec_create(containerId, execCommand, **execOptions)

        # Start a previously set up exec instance.
        return execId, self.dockerClient.exec_start(execId, socket=socket, stream=stream, tty=True)

    def listImages(self):
        '''
        列举所有镜像信息
        docker images
        '''
        images = self.dockerClient.images()
        return images

    def listContainers(self):
        '''
        列举所有容器信息
        docker container ls -a
        '''
        containers = self.dockerClient.containers(all=True)
        return containers

    def createContainer(self, image_version, **kwargs):
        '''
        创建容器，跟据镜像版本
        新建容器处于一直运行的状态
        docker run -it imageVersion bash
        '''
        def is_exist(image_version):
            images = self.listImages()
            for image in images:
                if image_version in image['RepoTags'][0]:
                    return image['RepoTags'][0]
            return False

        imageName = is_exist(image_version)
        if imageName is False:
            return None
        container = self.dockerClient.create_container(image=imageName, **kwargs)
        return container

    def startContainer(self, containerId):
        '''
        让一个关闭状态的容器运行
        docker start containerId
        '''
        self.dockerClient.start(container=containerId)

    def stopContainer(self, containerId):
        '''
        关闭一个容器
        '''
        try:
            self.dockerClient.stop(container=containerId)
        except docker.errors.APIError as e:
            print("error: %s" % e)
            return False
        else:
            return True

    def copyFromContainer(self,containerId, src, dst):
        '''
        复制文件
        '''
        stream, stat = self.dockerClient.get_archive(containerId, src)
        with open(dst, "wb") as f:
            for d in stream:
                f.write(d)
        unpacked_path = "%s_unpacked" % dst
        os.system("rm -r %s" % unpacked_path)
        os.system("mkdir %s" % unpacked_path)
        os.system("tar xvf %s -C %s" % (dst, unpacked_path))
        os.system("rm %s" % dst)
        return unpacked_path

    def isFileExist(self, containerId, path):
        '''
        判断docker中文件是否存在
        '''
        execCommand = [
            "/bin/sh",
            "-c",
            "test -d %s && echo 'It Exists'" % path]
        execOptions = {
            "tty": True,
            "stdin": True
        }
        execID, results = self.containerExecCmd(containerId, execCommand, stream=True, **execOptions)
        for output in results:
            if b"It Exists" in output:
                return True
        return False

    def deleteFile(self, containerId, path):
        """
        删除docker中的文件
        """
        execCommand = [
            "/bin/rm",
            "-r",
            path
        ]
        execOptions = {
            "tty": True,
            "stdin": True
        }
        self.containerExecCmd(containerId, execCommand, **execOptions)

    def execDockerCmd(self, dockerCmd):
        """
        通过命令行执行docker命令
        """
        p = subprocess.Popen(dockerCmd, stdout=subprocess.PIPE, shell=True)
        # p.wait()
        return p

    def deleteContainer(self, containerId):
        """
        删除容器
        """
        try:
            self.dockerClient.stop(containerId)
            self.dockerClient.remove_container(containerId)
        except BaseException as e:
            print(e)



class DockerStreamThread(threading.Thread):
    def __init__(self, ws, terminalStream):
        super(DockerStreamThread, self).__init__()
        self.ws = ws
        self.terminalStream = terminalStream

    def run(self):
        while not self.ws.closed:
            try:
                dockerStreamStdout = self.terminalStream.recv(2048)
                if dockerStreamStdout is not None:
                    self.ws.send(str(dockerStreamStdout, encoding='utf-8'))
                else:
                    print("docker daemon socket is close")
                    self.ws.close()
            except Exception as e:
                print("docker daemon socket err: %s" % e)
                self.ws.close()
                break


class AnalysisStreamThread(threading.Thread):
    def __init__(self, outputs, containerId, logPath, projectId):
        super(AnalysisStreamThread, self).__init__()
        self.outputs = outputs
        self.containerId = containerId
        self.logPath = logPath
        self.projectId = projectId

    def run(self):
        with open(self.logPath+'/analysis_output', 'w') as f:
            for output in self.outputs:
                print(output.decode('utf-8'), end='')
                f.write(output.decode('utf-8'))
                f.flush()
            f.close()
        print('analysis over')
        clientHandle = ClientHandler(base_url=conf.DOCKER_HOST)
        clientHandle.stopContainer(self.containerId)
        dataBase = DataBase()
        if os.access(self.logPath+'/html', os.F_OK):
            compress_path = "%s/report.tar.gz" % self.logPath
            report_path = "%s/html" % self.logPath
            os.system("tar -zcvf %s %s" % (compress_path, report_path))
            dataBase.update_projects_status_by_projectId(utility.common.TASK_FINISH, self.projectId)
        else:
            dataBase.update_projects_status_by_projectId(utility.common.TASK_STOP, self.projectId)
        dataBase.update_projects_over_by_projectId(1, self.projectId)
        print('delete analysis container')
        # print(self.outputs.read())
