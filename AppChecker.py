# coding=utf-8
from __future__ import print_function
from distutils.version import LooseVersion
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
        except Exception as e:
            raise e

        return docsList

    def insert_one_doc(self, insertDoc=None):
        ''' Insert one document in the collection '''

        try:
            insertDocID = self.collection.insert(insertDoc)
        except AttributeError as e:
            print('ERROR 0x001: Please connect MongoDB first!\n')
            raise e
        except Exception as e:
            raise e

        return insertDocID

    def isnert_multi_docs(self, insertDocs=None):
        ''' Insert multiple documents in the collection '''

        try:
            insertDocsID = self.collection.insert(insertDocs)
        except AttributeError as e:
            print('ERROR 0x001: Please connect MongoDB first!\n')
            raise e
        except Exception as e:
            raise e

        return insertDocsID

    def update_one_doc(self, updateCond=None, updateDoc=None):
        ''' Update one document in the collection
            If cannot find the existed one
            the method will insert a new document
            Returning the after-method documents'''

        try:
            afterDoc = self.collection.find_one_and_update(
                updateCond,
                updateDoc,
                projection={'_id': False},
                upsert=True,
                return_document=pymongo.ReturnDocument.AFTER)
        except AttributeError as e:
            print('ERROR 0x001: Please connect MongoDB first!\n')
            raise e
        except Exception as e:
            raise e

        return afterDoc

    def __del__(self):
        if self.db is not None:
            self.db.logout()


class AppChecker(object):

    def __init__(self, collectionName=None):
        self.db_appInfo = MongoDB(collectionName='AppInfo')
        self.db_appInfo.connect_db()
        self.appList = self.db_appInfo.get_all_docs(sortAttri='Name')

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

        try:
            appPlistInfo = plistlib.readPlist(
                '/Applications/{}.app/Contents/Info.plist'.format(appName))
            return appPlistInfo['CFBundleShortVersionString']
        except Exception as e:
            print('/Applications/{}.app/Contents/Info.plist'.format(appName))
            print(e)
            CFBundleShortVersionString = '0.0'
            return CFBundleShortVersionString

    def update_ver(self):
        ''' Update current APP Version in MAC '''

        appNames = os.listdir('/Applications')
        appNameList = []

        # Check the filename with app extension
        for item in appNames:
            if '.app' in item:
                appNameList.append(item[:-4])

        # Check the app version corresponding the appName in the list
        for appName in appNameList:
            appCurrentVer = self.get_current_version(appName)
            self.db_appInfo.update_one_doc(
                {'Name': appName}, {'$set': {'Version': appCurrentVer}})

        return 0

    def check_ver(self):
        ''' Check APP Version and Print '''

        print('%-18s | %-18s | %-18s | %-10s |' %
              ('App', 'CurVer', 'NewVer', 'Status'))
        print(('------------------ | ------------------ |'
               ' ------------------ | ---------- |'))
        for app in self.appList:
            appName = app['Name']
            appURL = app['URL']
            appVer = app['Version']

            if appURL == '':
                continue

            appCurrentVer = self.get_current_version(appName)
            appOnlineVer = self.extract_online_version(appURL)

            lsappCurrentVer = LooseVersion(appCurrentVer)
            lsappOnlineVer = LooseVersion(appOnlineVer)

            if appVer != appCurrentVer:
                appVer = appCurrentVer
                self.db_appInfo.update_one_doc(
                    {'Name': appName}, {'$set': {'Version': str(appVer)}})

            if cmp(lsappCurrentVer, lsappOnlineVer) != -1:
                print('%-18s | %-18s | %-18s | %-10s |' %
                      (appName, appCurrentVer, appOnlineVer, '✔'))
            else:
                print('%-18s | %-18s | %-18s |            |' %
                      (appName, appCurrentVer, appOnlineVer))

        return 0


def main():
    appChecker = AppChecker()
    # appChecker.update_ver()
    appChecker.check_ver()


if __name__ == '__main__':
    main()
