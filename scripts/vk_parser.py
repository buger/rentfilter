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

urls = [
        ("msk", "http://vkontakte.ru/al_search.php?c[section]=ads&c[category]=30&c[city]=1&c[country]=1&c[q]=%D1%81%D0%B4%D0%B0%D0%BC%20%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B8%D1%80%D1%83&c[Bsection]=ads&c[type]=3&al=1"),
        ("spb", "http://vkontakte.ru/al_search.php?c[section]=ads&c[category]=30&c[city]=2&c[country]=1&c[q]=%D1%81%D0%B4%D0%B0%D0%BC%20%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B8%D1%80%D1%83&c[Bsection]=ads&c[type]=3&al=1")
]

import time
import datetime

def get_list(url, region, page = 1):
    links = adsparser.ads_list(url, page).parse()

    parse_next_page = True

    ads = []

    for link in links:
        if Ad.get_by_key_name(link) is None:
            try:
                parser = adsparser.parse(link, region)
            except:
                continue

            if parser.date:
                created_at = parser.date
                created_at = datetime.datetime.combine(parser.date.date(), datetime.datetime.now().time())
            else:
                created_at = datetime.datetime.now()

            ad = Ad(key_name = link,
                    title = parser.title,
                    source = parser.get_name(),
                    md5 = parser.md5,
                    contact = parser.contact,
                    phone = parser.phone,
                    price = parser.price,
                    parent_url = url,
                    created_at = created_at,
                    region = parser.region
                    )

            if parser.address_id:
                ad.address_id = parser.address_id[0]

            if parser.agent:
                ad.rating = 0

            print ad.created_at

            ads.append(ad)

            time.sleep(1)
        else:
            print "ad already found"
            parse_next_page = False

    print "saving ads: %d" % len(ads)
    db.put(ads)

    for ad in ads:
        taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.key().name() })

    if parse_next_page or len(ads) > 36:
        print "parsing page %d" % (page+1)
        get_list(url, region, page+1)

while True:
    for url in urls:
        get_list(url[1], url[0])

    time.sleep(60*30)
