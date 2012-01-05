
from google.appengine.ext import webapp
from google.appengine.ext import db

import os

from spb_metro import *
from msk_metro import *

register = webapp.template.create_template_register()

@register.filter
def metro(address_id, region = 'spb'):
    try:
        return METRO_LIST[region][address_id.split('@')[0]][1]
    except:
        return address_id

import re

phone_formats = [
    "7%s%s%s%s%s%s%s%s%s%s",
    "8%s%s%s%s%s%s%s%s%s%s",
    "8-%s%s%s-%s%s%s-%s%s-%s%s",
    "7-%s%s%s-%s%s%s-%s%s-%s%s",
    "%s%s%s-%s%s%s-%s%s-%s%s",
    "%s%s%s-%s%s-%s%s-%s%s%s",
    "8%s%s%s-%s%s%s-%s%s-%s%s",
    "7%s%s%s-%s%s-%s%s-%s%s%s",
    "8%s%s%s-%s%s%s%s%s%s%s"]

import urllib

@register.filter
def format_phone(phone):
    try:
        query = []

        for p_format in phone_formats:
            f_phone = p_format % tuple(phone)
            query.append('"%s"' % f_phone)

        return urllib.quote(" OR ".join(query))
    except:
        return phone
