from utility.dataBase import DataBase
import conf
import os

def schedule_task():
    dataBase = DataBase()
    projects = dataBase.get_projects()
    for project in projects:
        if project['over'] == 2:
            continue
        if project['over'] == 1:
            dataBase.update_projects_over_by_projectId(2, project['projectid'])
        projectOutputPath = "%s/%s_%s_unpacked/record_packed/analysis_output" % \
                      (conf.HOST_WOKR_PATH, project['userid'], project['projectid'])
        if not os.access(projectOutputPath, os.F_OK):
            continue
        content = ""
        with open(projectOutputPath, "r") as f:
            content = f.read()
            f.close()
        dataBase.update_projects_output_by_projectId(content, project['projectid'])