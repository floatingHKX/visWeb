DOCKER_HOST = "tcp://127.0.0.1:2375"

REPLAY_CONTAINER_IMAGE = "floatingdocker/angr_replay:replay"
REPLAY_CONTAINER_NAME = "angr_replay"

# 漏洞复现镜像，打包结果保存路径
EXPLOIT_CONTAINER_PACKED_PATH = "/tmp/work"
# 重放容器重放分析运行的路径
REPLAY_CONTAINER_WORK_PATH= "/opt/visualization/work"
# 宿主机器映射重放容器的路径
HOST_WOKR_PATH = "/tmp/work"

