from __future__ import print_function
import plistlib
import requests
from functools import wraps
from bs4 import BeautifulSoup


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


class AppChecker(object):

    def __init__(self):
        self.appDic = {'Alfred 3':
                       {'Name': 'Alfred 3',
                        'URL': ('https://www.macupdate.com/app'
                                '/mac/34344/alfred'),
                        'Version': '3.4.1'},
                       'SizeUp':
                       {'Name': 'SizeUp',
                        'URL': ('https://www.macupdate.com/app'
                                '/mac/30721/sizeup'),
                        'Version': '1.7.2'}}

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
        print('%-10s | %-10s | %-10s |' %
              ('App', 'CurVer', 'NewVer'))
        print('---------- | ---------- | ---------- |')
        for app in self.appDic:
            appName = self.appDic[app]['Name']
            appURL = self.appDic[app]['URL']
            appVer = self.appDic[app]['Version']

            appCurrentVer = self.get_current_version(appName)
            appOnlineVer = self.extract_online_version(appURL)

            if appVer != appCurrentVer:
                appVer = appCurrentVer

            print('%-10s | %-10s | %-10s |' %
                  (appName, appCurrentVer, appOnlineVer))


def main():
    appChecker = AppChecker()
    appChecker.check_ver()


if __name__ == '__main__':
    main()
