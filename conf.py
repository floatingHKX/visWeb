DOCKER_HOST = "tcp://127.0.0.1:2375"

REPLAY_CONTAINER_IMAGE = "floatingdocker/angr_replay:replay"
REPLAY_CONTAINER_NAME = "angr_replay"

# 漏洞复现镜像，打包结果保存路径
EXPLOIT_CONTAINER_PACKED_PATH = "/tmp/work"
# 重放容器angr分析工具路径
REPLAY_CONTAINER_TOOL_PATH = "/opt/visualization"
# 重放容器重放分析运行的路径
REPLAY_CONTAINER_WORK_PATH = "/opt/visualization/work"
# 重放容器中pypy路径
REPLAY_CONTAINER_PYPY_PATH = "/usr/lib/pypy3.7-v7.3.3-linux64/bin"
# 宿主机器映射重放容器的路径
HOST_WOKR_PATH = "/home/hkx/repaly_work"

# 分析脚本内容
RUN_SCRIPT = '''import sys
sys.path.append("''' + REPLAY_CONTAINER_TOOL_PATH + \
'''/source")
from replayer import Replayer

rr = Replayer("%s", "%s", "%s", "%s", new_syscall=True)
rr.enable_analysis(%s)
rr.do_analysis()
rr.generate_report()

'''

# 分析启动脚本
RUN_SH = '''#/bin/sh
%s %s |& tee analysis_output
'''
