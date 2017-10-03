# coding=utf-8
from __future__ import print_function
import plistlib
import requests
import os
import sys
import ConfigParser
import pymongo
from functools import wraps
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf-8')


def log(debug=True):
    if debug:
        def _log(func):
            @wraps(func)
            def wrapped_function(*args, **kwargs):
                log_string = args[0] + 'was loaded in ' + func.__name__
                print(log_string)
                return func(*args, **kwargs)
            return wrapped_function
    else:
        def _log(func):
            return func
    return _log


class MongoDB(object):

    def __init__(self, confPath=None, collectionName=None):
        ''' Read MongoDB Configuration from MongoDB.conf '''

        cf = ConfigParser.ConfigParser()
        if confPath is None:
            currPath = os.getcwd()
            cf.read(currPath + '/MongoDB.conf')
        else:
            cf.read(confPath)

        self.db_host = cf.get('MongoDB', 'db_host')
        self.db_port = cf.getint('MongoDB', 'db_port')
        self.db_name = cf.get('MongoDB', 'db_name')
        self.db = None
        self.collectionName = collectionName

    def connect_db(self):
        ''' Connect to MongoDB using configuration '''

        self.client = pymongo.MongoClient(host=self.db_host, port=self.db_port)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collectionName]

    def get_all_docs(self, sortAttri=None):
        ''' Return all documents in the collection sorting with sortAttri'''

        try:
            all_docs = self.collection.find({}, {'_id': 0})
            if sortAttri is not None:
                all_docs_sort = all_docs.sort(sortAttri, pymongo.ASCENDING)
            else:
                all_docs_sort = all_docs
            docsList = []
            for item in all_docs_sort:
                docsList.append(item)
        except AttributeError as e:
            print('ERROR 0x001: Please connect MongoDB first!\n')
            raise e

        return docsList

    def insert_one_doc(self):
        ''' Insert one documents in the collection '''

        return 0

    def __del__(self):
        if self.db is not None:
            self.db.logout()


class AppChecker(object):

    def __init__(self, appList):
        self.appList = appList

    @log(False)
    def load_page_html(self, url):
        ''' Obtain the page's HTML content '''

        return requests.get(url).content

    def extract_online_version(self, url):
        ''' Extract the APP Version from MacUpdate '''

        html_content = self.load_page_html(url)
        soup = BeautifulSoup(html_content, 'lxml')
        appVersion = soup.select('div#app-info-version-data > h4 > a')
        appVersionStr = str(appVersion[0].get_text()).strip()
        return appVersionStr

    def get_current_version(self, appName=None):
        ''' Extract the APP Current Version from its plist file '''

        appPlistInfo = plistlib.readPlist(
            '/Applications/{}.app/Contents/Info.plist'.format(appName))

        return appPlistInfo['CFBundleShortVersionString']

    def check_ver(self):
        ''' Check APP Version and Print '''

        print('%-10s | %-10s | %-10s | %-10s |' %
              ('App', 'CurVer', 'NewVer', 'Status'))
        print('---------- | ---------- | ---------- | ---------- |')
        for app in self.appList:
            appName = app['Name']
            appURL = app['URL']
            appVer = app['Version']

            appCurrentVer = self.get_current_version(appName)
            appOnlineVer = self.extract_online_version(appURL)

            if appVer != appCurrentVer:
                appVer = appCurrentVer

            if appCurrentVer >= appOnlineVer:
                print('%-10s | %-10s | %-10s | %-10s |' %
                      (appName, appCurrentVer, appOnlineVer, '✔'))
            else:
                print('%-10s | %-10s | %-10s |            |' %
                      (appName, appCurrentVer, appOnlineVer))


def main():
    db_appInfo = MongoDB(collectionName='AppInfo')
    db_appInfo.connect_db()
    appInfo = db_appInfo.get_all_docs('Name')
    appChecker = AppChecker(appInfo)
    appChecker.check_ver()


if __name__ == '__main__':
    main()
