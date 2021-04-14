#!/usr/bin/env python
# coding: utf-8

import docker
import threading
import shutil
from io import BytesIO
import tarfile
import os


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
        return self.dockerClient.exec_start(execId, socket=socket, stream=stream, tty=True)

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
                if image_version == image['RepoTags'][0]:
                    return True
            return False

        if is_exist(image_version) is False:
            return None
        container = self.dockerClient.create_container(image=image_version, **kwargs)
        return container

    def startContainer(self, containerId):
        '''
        让一个关闭状态的容器运行
        docker start containerId
        '''
        self.dockerClient.start(container=containerId)

    def copyFromContainer(self,containerId, src, dst):
        '''
        复制文件
        '''
        stream, stat = self.dockerClient.get_archive(containerId, src)
        with open(dst, "wb") as f:
            for d in stream:
                f.write(d)
        unpacked_path = "%s@" % dst
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
        results = self.containerExecCmd(containerId, execCommand, stream=True, **execOptions)
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
    def __init__(self, terminalStream):
        super(AnalysisStreamThread, self).__init__()
        self.terminalStream = terminalStream

    def run(self):
        for b in self.terminalStream:
            print(str(b))
