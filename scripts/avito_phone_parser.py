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

import subprocess

command = "convert -resize 500x40 -negate -threshold 20% -negate -despeckle -monochrome __url__ numbers.tif && tesseract numbers.tif result  -l eng > /dev/null 2>&1 "


def clone_entity(e, **extra_args):
  """Clones an entity, adding or overriding constructor attributes.

  The cloned entity will have exactly the same property values as the original
  entity, except where overridden. By default it will have no parent entity or
  key name, unless supplied.

  Args:
    e: The entity to clone
    extra_args: Keyword arguments to override from the cloned entity and pass
      to the constructor.
  Returns:
    A cloned, possibly modified, copy of entity e.
  """
  klass = e.__class__
  props = dict((k, v.__get__(e, klass)) for k, v in klass.properties().iteritems())
  props.update(extra_args)
  return klass(**props)

import urllib2

def get_ads(cursor = None, count = 0):
    print "getting ads %d" % count

    ads = Ad.all().filter("source =", "avito").order("-created_at")

    print ads[0].created_at

    if cursor:
        ads = ads.with_cursor(cursor)

    ads_for_put = []
    ads_for_delete = []

    for ad in ads.fetch(10):
        try:
            parser = adsparser.parse(ad.key().name(), 'spb')
        except StandardError as e:
            msg = e.__str__()
            if msg == 'HTTP Error 404: Not found':
                print "deleting"
                ad.deleted = True

                ads_for_put.append(ad)

            continue

        if parser.phone_key is None:
            continue

        phone_url = "%s?pkey=%s" % (ad.key().name().replace('items/', 'items/phone/'), parser.phone_key)
        phone_cmd = command.replace("__url__", phone_url)

        print ad.key().name()

        fin, fout = os.popen4(phone_cmd)
        phone = fout.read()

        time.sleep(2)

        f = open("result.txt", "r")
        phone = adsparser.format_phone(f.read())
        f.close()

        if parser.is_real_agent:
            ad.rating = 0
        else:
            if ad.phone is None or ad.phone == '':
                ad.rating = 100

        if ad.phone is not None and ad.phone != '' and ad.phone != phone:
            new_ad = clone_entity(ad, key_name = "%s?v2" % ad.key().name(), parent = ad)
            new_ad.phone = phone
            new_ad.created_at = datetime.datetime.now()

            ads_for_put.append(new_ad)

        if ad.phone is None or ad.phone == '':
            ad.phone = phone
            ad.created_at = datetime.datetime.combine(ad.created_at.date(), datetime.datetime.now().time())

        ads_for_put.append(ad)

    print "saving ads"
    db.put(ads_for_put)
    print "ads saved"

    for ad in ads_for_put:
        try:
            print "adding task"
            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.key().name() })
        except:
            pass

    print "tasks added"

    get_ads(ads.cursor(), count + 10)


ads = Ad.all().filter("source =", "avito").order("-created_at")
ads.fetch(230)
get_ads(ads.cursor(), 230)

