from utility.myDocker import ClientHandler
import conf
from utility.myDocker import AnalysisStreamThread
from utility.dataBase import DataBase

class ReplayService(object):

    def __init__(self):
        self.clientHandle = ClientHandler(base_url=conf.DOCKER_HOST)
        self.dataBase = DataBase()

    def createReplayContainer(self, projectId):
        '''
        创建重放的容器
        '''
        container = self.clientHandle\
            .createContainer(conf.REPLAY_CONTAINER_IMAGE, \
                          command=["/bin/sh", "-c", "while :; do sleep 1; done"], \
                          name="%s-%s" % (conf.REPLAY_CONTAINER_NAME, projectId) , \
                          # environment=["PATH=%s:$PATH" % conf.REPLAY_CONTAINER_PYPY_PATH], \
                          volumes=[conf.REPLAY_CONTAINER_WORK_PATH], \
                          host_config=self.clientHandle.dockerClient.create_host_config(
                              auto_remove=True,
                              binds={
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
            if conf.REPLAY_CONTAINER_NAME in contain['Names'][0][1:]:
                return True
        return False

    def getReplayContainerId(self, projectId):
        '''
        获取重放容器的id
        '''
        if self.isReplayContainerExist() is False:
            return None
        contains = self.clientHandle.listContainers()
        for contain in contains:
            if contain['Names'][0][1:] == "%s-%s" % (conf.REPLAY_CONTAINER_NAME, projectId):
                return contain['Id']
        return None

    def createProjectId(self):
        """
        获得最大的projectId
        """
        result = self.dataBase.get_projects_maxId()
        if result[0][0] is None:
            return 1
        else:
            return result[0][0] + 1

    def startReplayAnalysis(self, userId, containerId, binaryName, analysisEnable, libVersion, projectName):
        '''
        开始重放分析
        1 将重放容器中记录的信息，复制到复现容器的 路经中去
        2 创建运行脚本，复制到复现容器的 路径中去
        '''
        # 生成项目id
        projectId = self.createProjectId()
        # 重放容器 映射路径
        dst = "%s/%s_%s" % (conf.HOST_WOKR_PATH, userId, projectId)
        # 复现容器 打包文件 路径
        src = "%s/record_packed" % conf.EXPLOIT_CONTAINER_PACKED_PATH
        # 判断打包文件 是否存在
        if self.clientHandle.isFileExist(containerId, src) is False:
            return {'success': False, 'recordExist': False}
        # 解压文件路径
        unpacked_path = self.clientHandle.copyFromContainer(containerId, src, dst)
        # 生成分析脚本文件
        scriptPath = self.generateRunScript(unpacked_path+"/record_packed", binaryName, analysisEnable, libVersion)
        # 生成重放容器
        replayContainerId = self.createReplayContainer(projectId)

        self.dataBase.insert_projects(projectId, userId, projectName, binaryName, 0, analysisEnable, "start analysis...")
        execId = self.execAnalysisScript(replayContainerId, scriptPath, projectId)

        # workPath = scriptPath.replace(conf.HOST_WOKR_PATH, conf.REPLAY_CONTAINER_WORK_PATH)
        # dockerScript = "docker run --rm -v %s:%s " % (conf.HOST_WOKR_PATH, conf.REPLAY_CONTAINER_WORK_PATH) + \
        #     "-t -w %s %s " % (workPath, conf.REPLAY_CONTAINER_IMAGE)  + \
        #                "%s/pypy3 init.py" % conf.REPLAY_CONTAINER_PYPY_PATH
        # p = self.clientHandle.execDockerCmd(dockerScript)
        return execId

    def generateRunScript(self, scriptPath, binaryName, analysisEnable, libVersion):
        """
        生成分析脚本文件
        """
        script = conf.RUN_SCRIPT % (binaryName, "syscalls.record", "maps", libVersion, analysisEnable)
        with open(scriptPath+"/init.py", "w") as f:
            f.write(script)
            f.close()
        script = conf.RUN_SH % ("%s/pypy3" % conf.REPLAY_CONTAINER_PYPY_PATH, "init.py")
        with open(scriptPath+"/run.sh", "w") as f:
            f.write(script)
            f.close()
        print("生成分析脚本文件")
        return scriptPath

    def execAnalysisScript(self, containerId, path, projectId):
        """
        执行 分析脚本
        """
        analysis_output_path = path
        path = path.replace(conf.HOST_WOKR_PATH, conf.REPLAY_CONTAINER_WORK_PATH)
        execCommand = [
            "%s/pypy3" % conf.REPLAY_CONTAINER_PYPY_PATH,
            "init.py"
            # "/bin/sh",
            # "run.sh"
        ]
        execOptions = {
            "tty": True,
            "workdir": path
            # "environment": ["PATH=%s:$PATH" % conf.REPLAY_CONTAINER_PYPY_PATH]
        }
        print("执行分析脚本")
        execId, stream = self.clientHandle.containerExecCmd(containerId, execCommand, stream=True, **execOptions)
        print("over")
        analysisStreamThread = AnalysisStreamThread(stream, containerId, analysis_output_path, projectId)
        analysisStreamThread.start()
        return execId

    def terminateAnalysis(self, projectId):
        """
        中断分析
        """
        containerId = self.getReplayContainerId(projectId)
        return self.clientHandle.stopContainer(containerId)

    def deleteContainer(self, containerId):
        """
        删除容器
        """
        return self.clientHandle.stopContainer(containerId)






