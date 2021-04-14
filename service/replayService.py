from utility.myDocker import ClientHandler
import conf
import os
import json
from utility.myDocker import AnalysisStreamThread

class ReplayService(object):

    def __init__(self):
        self.clientHandle = ClientHandler(base_url=conf.DOCKER_HOST)

    def createReplayContainer(self):
        '''
        创建重放的容器
        '''
        container = self.clientHandle\
            .createContainer(conf.REPLAY_CONTAINER_IMAGE, \
                          command=["/bin/sh", "-c", "while :; do sleep 1; done"], \
                          name=conf.REPLAY_CONTAINER_NAME, \
                          # environment={"PATH":"%s:$PATH" % conf.REPLAY_CONTAINER_PYPY_PATH}, \
                          volumes=[conf.REPLAY_CONTAINER_WORK_PATH], \
                          host_config=self.clientHandle.dockerClient.create_host_config(binds={
                              conf.HOST_WOKR_PATH:{
                                  "bind": conf.REPLAY_CONTAINER_WORK_PATH,
                                  "mode": "rw",
                              }
                          }))
        if container is None:
            return None
        self.clientHandle.startContainer(container)
        return container['Id']

    def isReplayContainerExist(self):
        '''
        判断容器是否存在
        '''
        contains = self.clientHandle.listContainers()
        for contain in contains:
            if contain['Names'][0][1:] == conf.REPLAY_CONTAINER_NAME:
                return True
        return False

    def getReplayContainerId(self):
        '''
        获取重放容器的id
        '''
        if self.isReplayContainerExist() is False:
            return None
        contains = self.clientHandle.listContainers()
        for contain in contains:
            if contain['Names'][0][1:] == conf.REPLAY_CONTAINER_NAME:
                return contain['Id']
        return None

    def startReplayAnalysis(self, containerId, binaryName, analysisEnable, libVersion):
        '''
        开始重放分析
        1 将重放容器中记录的信息，复制到复现容器的 路经中去
        2 创建运行脚本，复制到复现容器的 路径中去
        '''
        # 重放容器 映射路径
        dst = "%s/%s" % (conf.HOST_WOKR_PATH, containerId)
        # 复现容器 打包文件 路径
        src = "%s/record_packed" % conf.EXPLOIT_CONTAINER_PACKED_PATH
        # 判断打包文件 是否存在
        if self.clientHandle.isFileExist(containerId, src) is False:
            return "record_packed do not exist"
        unpacked_path = self.clientHandle.copyFromContainer(containerId, src, dst)
        scriptPath = self.generateRunScript(unpacked_path+"/record_packed", binaryName, analysisEnable, libVersion)
        replayContainerId = self.getReplayContainerId()
        self.execAnalysisScript(replayContainerId, scriptPath)

    def generateRunScript(self, scriptPath, binaryName, analysisEnable, libVersion):
        """
        生成分析脚本文件
        """
        script = conf.RUN_SCRIPT % (binaryName, "syscalls.record", "maps", libVersion, analysisEnable)
        with open(scriptPath+"/init.py", "w") as f:
            f.write(script)
            f.close()
        print("生成分析脚本文件")
        return scriptPath

    def execAnalysisScript(self, containerId, path):
        """
        执行 分析脚本
        """
        path = path.replace(conf.HOST_WOKR_PATH, conf.REPLAY_CONTAINER_WORK_PATH)
        execCommand = [
            "%s/pypy3" % conf.REPLAY_CONTAINER_PYPY_PATH,
            "init.py"]
        execOptions = {
            "workdir": path
        }
        print("执行分析脚本")
        analysisStream = self.clientHandle.containerExecCmd(containerId, execCommand, stream=True, **execOptions)
        print("over")
        analysisStreamThread = AnalysisStreamThread(analysisStream)
        analysisStreamThread.start()

        # for output in results:
        #     print(output)






