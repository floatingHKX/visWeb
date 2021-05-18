from utility.dataBase import DataBase
from utility.myDocker import ClientHandler
import conf
import os
import time
from utility.common import getTaskStatus, getTaskStatusColor

class ManageService(object):
    def __init__(self):
        self.database = DataBase()
        self.clientHandle = ClientHandler(base_url=conf.DOCKER_HOST)

    def add_container(self, userId, containerId):
        self.database.insert_containers(userId, containerId)

    def delete_container(self, containerId):
        self.clientHandle.deleteContainer(containerId)
        self.database.delete_containers(containerId)

    def get_projects(self, userId, pageNo, pageSize):
        result = self.database.get_projects_by_userid(userId)
        totalCount = len(result)//pageSize+1
        lastPage = result[(totalCount-1)*pageSize:]
        results = {}
        results['data'] = result[(pageNo-1)*pageSize: pageNo*pageSize]
        results['pageSize'] = pageSize
        results['pageNo'] = pageNo
        results['totalPage'] = lastPage
        results['totalCount'] = totalCount
        for row in results['data']:
            row['color'] = getTaskStatusColor(row['status'])
            row['status_txt'] = getTaskStatus(row['status'])
        for row in results['totalPage']:
            if 'color' in row.keys():
                continue
            row['status_txt'] = getTaskStatus(row['status_txt'])
        return results

    def get_project_detail(self, projectId):
        result = self.database.get_projects_by_projectId(projectId)[0]
        result['color'] = getTaskStatusColor(result['status'])
        result['status_txt'] = getTaskStatus(result['status'])
        result['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return result
        

    def delete_project(self, projectId, userId):
        self.database.delete_projects_by_projectId(projectId)
        projectPath = "%s/%s_%s_unpacked" % (conf.HOST_WOKR_PATH, userId, projectId)
        os.system("rm -rf %s" % projectPath)


    def get_containerId(self, userId):
        result = self.database.get_containers_by_userid(userId)
        for row in result:
            if int(userId, 10) == row[0]:
                return row[1]
        return None