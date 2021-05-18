#!/usr/bin/env python
# coding: utf-8

import sqlite3
from flask import g
import os

class DataBase(object):
    def __init__(self):
        db_path = os.path.join(os.getcwd(), './db/exploitDB.db')
        self.conn = sqlite3.connect(db_path)

    def dictFactory(self, cursor, row):
        """将sql查询结果整理成字典形式"""
        d={}
        for index, col in enumerate(cursor.description):
            d[col[0]]=row[index]
        return d

    def delete_containers(self, contiainerId):
        """
        删除container
        """
        c = self.conn.cursor()
        c.execute('''DELETE FROM CONTAINERS WHERE containerid = ?; 
        ''', (contiainerId, ))
        self.conn.commit()

    def insert_containers(self, userId, containerId):
        """
        插入containers表
        """
        c = self.conn.cursor()
        c.execute('''INSERT INTO CONTAINERS (userid, containerid) \
        VALUES (?, ?);
        ''' , (userId, containerId))
        self.conn.commit()

    def get_containers_by_userid(self, userId):
        """
        获取一个用户的containerid
        """
        c = self.conn.cursor()
        c.execute('''SELECT * FROM CONTAINERS \
            WHERE userid = ?;''', (userId,))
        results = c.fetchall()
        return results

    def get_projects_maxId(self):
        """
        获得最大的projectId
        """
        c = self.conn.cursor()
        c.execute('''SELECT MAX(projectid) FROM PROJECTS
            ''')
        results = c.fetchall()
        return results

    def delete_projects_by_projectId(self, projectId):
        """
        删除任务
        """
        c = self.conn.cursor()
        c.execute('''DELETE FROM PROJECTS WHERE projectid = ?; 
        ''', (projectId, ))
        self.conn.commit()

    def get_projects_by_projectId(self, projectId):
        """
        获得任务细节信息
        """
        self.conn.row_factory = self.dictFactory
        c = self.conn.cursor()
        c.execute('''SELECT * FROM PROJECTS WHERE projectid = ?;''', (projectId, ))
        results = c.fetchall()
        return results

    def get_projects(self):
        """
        获得所有任务
        """
        self.conn.row_factory = self.dictFactory
        c = self.conn.cursor()
        c.execute('''SELECT * FROM PROJECTS''')
        results = c.fetchall()
        return results

    def insert_projects(self, projectId, userId, projectName, binaryName, status, analysis, output):
        """
        插入新任务
        """
        c = self.conn.cursor()
        c.execute('''INSERT INTO PROJECTS \
        (projectid, userid, projectname, binaryname, status, analysis, output, over, createdate) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, DateTime('now'));
        ''', (projectId, userId, projectName, binaryName, status, analysis, output, 0))
        self.conn.commit()

    def update_projects_over_by_projectId(self, over, projectId):
        """
        更新任务的更新标签
        """
        c = self.conn.cursor()
        c.execute('''UPDATE PROJECTS \
                        SET over = ?
                        WHERE projectid = ?;
                        ''', (over, projectId))
        self.conn.commit()

    def update_projects_output_by_projectId(self, output, projectId):
        """
        更新任务输出
        """
        c = self.conn.cursor()
        c.execute('''UPDATE PROJECTS \
                SET output = ?
                WHERE projectid = ?;
                ''', (output, projectId))
        self.conn.commit()

    def update_projects_status_by_projectId(self, status, projectId):
        """
        更新任务状态
        """
        c = self.conn.cursor()
        c.execute('''UPDATE PROJECTS \
                SET status = ?
                WHERE projectid = ?;
                ''', (status, projectId))
        self.conn.commit()

    def get_projects_by_userid(self, userId):
        """
        获得某用户的所有任务
        """
        self.conn.row_factory = self.dictFactory
        c = self.conn.cursor()
        c.execute('''SELECT * FROM PROJECTS \
            WHERE userid = ?;''', (userId, ))
        results = c.fetchall()
        return results

    def remove_projects_by_projectid(self, projectId):
        """
        删除project 通过projectid
        """
        c = self.conn.cursor()
        c.execute('''DELETE FROM PROJECTS WHERE projectid = ?; 
        ''', (projectId, ))
        self.conn.commit()