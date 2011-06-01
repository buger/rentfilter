# encoding: utf-8

from handlers.base import *
import logging
from lib import PyRSS2Gen
import datetime

class Rss(AppHandler):
    def get(self):
        today = datetime.datetime.now()

        ads = Ad.all().order("-added_at").filter("rating =", 100)
        ads = ads.filter("added_at <", today-datetime.timedelta(minutes = 60))
        ads = ads.fetch(30)

        items = []

        for ad in ads:
            item = PyRSS2Gen.RSSItem(
                 title = ad.title,
                 link = ad.key().name(),
                 guid = PyRSS2Gen.Guid(ad.key().name()),
                 pubDate = ad.added_at)

            items.append(item);

        rss = PyRSS2Gen.RSS2(
            title = "СПБ - Аренда квартир от хозяев",
            link = "http://www.rentfilter.ru",
            description = "RentFilter поможет снять квартиру без посредников. Наши роботы фильтруют объявления об аренде помещений и оставляют только те, которые подают сами хозяева квартир.",

            lastBuildDate = datetime.datetime.utcnow(),

            items = items)


        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(rss.to_xml('utf-8'))

route('/rss/spb', Rss)

