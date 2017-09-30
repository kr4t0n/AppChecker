from __future__ import print_function
import plistlib

appPlistInfo = plistlib.readPlist(
    '/Applications/Alfred 3.app/Contents/Info.plist')

# print out the short version of App
print(appPlistInfo['CFBundleShortVersionString'])
