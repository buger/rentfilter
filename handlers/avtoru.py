# encoding: utf-8

from handlers.base import *
import logging
import datetime
import re
import avtoru_parser
from google.appengine.api import taskqueue


class AvtoruCron(AppHandler):
    def get(self):
        try:
            page = int(self.request.get('page'))
        except:
            page = 1


        settings = avtoru_parser.AvtoSettings().all().get()

        if settings is None:
            settings = avtoru_parser.AvtoSettings()
            settings.put()

        url = avtoru_parser.avtoru_url
        url = re.sub('@price_start@', str(settings.price_start), url)
        url = re.sub('@price_end@', str(settings.price_end), url)

        links = avtoru_parser.AvtoruParser(avtoru_parser.avtoru_url, page).get_list()

        for link in links:
            taskqueue.add(queue_name = 'avtoru', url="/avto/ad", params = {'url': link})

        if len(links) > 40:
            taskqueue.add(queue_name = 'avtoru', url="/avto/ads", params = {'page': page+1})

    def post(self):
        self.get()

route("/avto/ads", AvtoruCron)


import time
import logging
from datetime import timedelta

class ProcessAd(AppHandler):
    def post(self):
        url = self.request.get('url')

        logging.info("Processing ad: %s" % url)

        parser = avtoru_parser.AvtoruAdParser(url).parse()

        if avtoru_parser.AvtoAd.get_by_key_name(url) is None:
            start_from = date.today() - timedelta(days = 30)

            if avtoru_parser.AvtoAd().all().filter("phone =", parser.phone).filter("created_at >", start_from).get() is None:
                logging.info("Processing avto ad: %s, %s" % (url, parser.phone))
                logging.info(parser.date)

                ad = avtoru_parser.AvtoAd(key_name = "%s_%d" % (url, time.time()),
                                          phone = parser.phone,
                                          created_at = parser.date)

                ad.put()
            else:
                logging.info("Phone found: %s" % parser.phone)
        else:
            logging.info("Ad found: %s" % url)

route("/avto/ad", ProcessAd)


from datetime import date
from datetime import datetime

def query_counter(q, cursor=None, limit=1000):
    if cursor:
        q.with_cursor(cursor)
    count = q.count(limit=limit)
    if count == limit:
        return count + query_counter(q, q.cursor(), limit=limit)
    return count

class AvtoList(AppHandler):
    def get(self):
        ads = avtoru_parser.AvtoAd.all().order('-created_at')

        today_date = (datetime.now()+timedelta(hours=4)).date()

        today = query_counter(avtoru_parser.AvtoAd.all().order('-created_at').filter('created_at =', today_date))

        yesterday = query_counter(avtoru_parser.AvtoAd.all().order('-created_at').filter('created_at =', today_date-timedelta(1)))

        settings = avtoru_parser.AvtoSettings().all().get()

        url = avtoru_parser.avtoru_url
        url = re.sub('@price_start@', str(settings.price_start), url)
        url = re.sub('@price_end@', str(settings.price_end), url)

        self.render_template("avto_ads.html", { 'ads': ads.fetch(50), 'today':today, 'yesterday':yesterday, 'settings':settings, 'url':url })

route("/avto", AvtoList)


from dateutil import parser

class AvtoDownload(AppHandler):
    def get(self):
        if self.request.get('date') == 'today':
            _date = date.today()
        elif self.request.get('date') == 'yesterday':
            _date = date.today()-timedelta(1);
        else:
            _date = parser.parse(self.request.get('date'))

        ads = avtoru_parser.AvtoAd.all().order('-created_at').filter('created_at =', _date).fetch(3000)

        phones = [ad.phone for ad in ads]

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("\n".join(phones))

route("/avto/download", AvtoDownload)


class AvtoSettings(AppHandler):
    def post(self):
        settings = avtoru_parser.AvtoSettings().all().get()

        settings.price_start = int(self.request.get('price_start'))
        settings.price_end = int(self.request.get('price_end'))

        settings.put()

route("/avto/settings", AvtoSettings)
