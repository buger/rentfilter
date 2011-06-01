# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.ext import blobstore
from google.appengine.api import users

import simplejson as json

class JsonProperty(db.Property):
    def get_value_for_datastore(self, model_instance):
        value = getattr(model_instance, self.name, None)
        return json.dumps(value)
    def make_value_from_datastore(self, value):
        return json.loads(value)


class i18nEntry(db.Model):
    msg_id = db.StringProperty()
    language = db.StringProperty()
    data = db.TextProperty()

class FileEntry(db.Model):
    url = db.StringProperty()

class Ad(db.Expando):
    title = db.StringProperty()
    source = db.StringProperty()
    parent_url = db.StringProperty()
    md5 = db.StringProperty()
    contact = db.StringProperty()
    phone = db.StringProperty()
    created_at = db.DateTimeProperty()

    added_at = db.DateTimeProperty(auto_now_add = True)

    rating = db.IntegerProperty(default = 100)

    region = db.StringProperty(default = 'spb')

    deleted = db.BooleanProperty(default = False)

    def count_by_phone(self):
        return Ad.all().filter("phone =", self.phone).count()

    def count_by_contact(self):
        return Ad.all().filter("contact =", self.contact).count()

    def icon(self):
        if self.source == 'avito':
            return 'http://www.avito.ru/favicon.ico'
        elif self.source == 'olx':
            return 'http://olx.ru/favicon.ico'
        elif self.source == 'slando':
            return 'http://slando.ru/favicon.ico'

import datetime
import time

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

def model_to_json(model):
    output = {}

    for key, prop in model.properties().iteritems():
        value = getattr(model, key)

        if value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, datetime.date):
            # Convert date/datetime to ms-since-epoch ("new Date()").
            ms = time.mktime(value.utctimetuple()) * 1000
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, db.GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, db.Model):
            output[key] = ''#model_to_json(value)
        else:
            raise ValueError('cannot encode ' + repr(prop))

    try:
        output['key'] = str(model.key())
    except:
        pass

    return output
