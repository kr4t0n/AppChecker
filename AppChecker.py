from __future__ import print_function
import plistlib
import requests
from functools import wraps
from bs4 import BeautifulSoup

app = ['Alfred 3']


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


@log(False)
def load_page_html(url):
    ''' Obtain the page's HTML content '''
    return requests.get(url).content


def extract_online_version(url):
    ''' Extract the APP Version from MacUpdate '''
    html_content = load_page_html(url)
    soup = BeautifulSoup(html_content, 'lxml')
    appVersion = soup.select('div#app-info-version-data > h4 > a')
    appVersionStr = str(appVersion[0].get_text()).strip()
    return appVersionStr


def get_current_version(appName=None):
    appPlistInfo = plistlib.readPlist(
        '/Applications/Alfred 3.app/Contents/Info.plist')

    return appPlistInfo['CFBundleShortVersionString']

appCurrentVer = get_current_version()
appOnlineVer = extract_online_version(
    'https://www.macupdate.com/app/mac/34344/alfred')

print('---------- | ---------- | ---------- |')
print('%-10s | %-10s | %-10s |' % ('Alfred', appCurrentVer, appOnlineVer))
