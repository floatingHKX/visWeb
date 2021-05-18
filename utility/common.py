
TASK_PROCESSING = 2
TASK_FINISH = 3
TASK_STOP = -1

statusText = {
    2: "任务进行中",
    3: "任务完成",
    -1: "任务停止"
}

statusColor = {
    2: "processing",
    3: "success",
    -1: "warning"
}

def getTaskStatus(status):
    return statusText[status]

def getTaskStatusColor(status):
    return statusColor[status]