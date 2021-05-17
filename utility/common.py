
statusText = {
    0: "任务进行中",
    1: "任务完成",
    -1: "任务停止"
}

statusColor = {
    0: "processing",
    1: "success",
    -1: "warning"
}

def getTaskStatus(status):
    return statusText[status]

def getTaskStatusColor(status):
    return statusColor[status]