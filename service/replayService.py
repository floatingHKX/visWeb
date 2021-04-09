from utility.myDocker import ClientHandler
import conf
import os

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

    def startReplayAnalysis(self, containerId):
        '''
        开始重放分析
        1
        '''
        # 重放容器 映射路径
        dst = "%s/%s" % (conf.HOST_WOKR_PATH, containerId)
        # 复现容器 打包文件 路径
        src = "%s/record_packed" % conf.EXPLOIT_CONTAINER_PACKED_PATH
        self.clientHandle.copyFromContainer(containerId, src, dst)


