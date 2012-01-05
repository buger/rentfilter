#!/usr/bin/env python
import os
import sys

# Hardwire in appengine modules to PYTHONPATH
# or use wrapper to do it more elegantly
DIR_PATH = '/home/buger/work/google_appengine'

EXTRA_PATHS = [
  DIR_PATH,
  os.path.join(DIR_PATH, 'lib', 'antlr3'),
  os.path.join(DIR_PATH, 'lib', 'django_0_96'),
  os.path.join(DIR_PATH, 'lib', 'fancy_urllib'),
  os.path.join(DIR_PATH, 'lib', 'ipaddr'),

  os.path.join(DIR_PATH, 'lib', 'webob'),
  os.path.join(DIR_PATH, 'lib', 'yaml', 'lib'),
  os.path.join(DIR_PATH, 'lib', 'simplejson'),
  os.path.join(DIR_PATH, 'lib', 'graphy'),
]

def fix_sys_path():
  """Fix the sys.path to include our extra paths."""
  sys.path = EXTRA_PATHS + sys.path

fix_sys_path()

# Add your models to path
my_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, my_root_dir)

from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.ext.remote_api import remote_api_stub
import getpass

from lib.models import *

APP_NAME = 'russiaflatrent'
os.environ['AUTH_DOMAIN'] = 'gmail.com'
os.environ['USER_EMAIL'] = 'leonsbox@gmail.com'

def auth_func():
    return ("leonsbox@gmail.com", "calestoffs4ic")
    # return (raw_input('Username:'), getpass.getpass('Password:'))

# Use local dev server by passing in as parameter:
# servername='localhost:8080'
# Otherwise, remote_api assumes you are targeting APP_NAME.appspot.com
remote_api_stub.ConfigureRemoteDatastore(APP_NAME,
 '/remote_api', auth_func)

# Do stuff like your code was running on App Engine

import adsparser
import time
import datetime

counter = 0

def get_list(cursor = None):
    global counter

    print counter

    ads = Ad.all()

    if cursor:
        ads.with_cursor(cursor)

    for_put = []

    for ad in ads.fetch(100):
        ad.offer_type = 1
        for_put.append(ad)

    db.put(for_put)

    counter += 1

    if len(for_put) == 100:
        get_list(ads.cursor())
    else:
        print "The end"

get_list()
