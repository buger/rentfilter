# encoding: utf-8

from handlers.base import *
import logging
import datetime
import re
import adsparser

class GetByPhone(AppHandler):
    def get(self):
        phone = self.request.get('phone')
        phone = adsparser.format_phone(phone)

        ads = Ad.all().filter("phone =", phone).filter("rating =", 0)

        if ads.count() > 0:
            self.render_json({'agent': True})
        else:
            self.render_json({'agent': False})

    def post(self):
        self.get()


route("/api/check_phone", GetByPhone)


class GetByUrl(AppHandler):
    def get(self):
        url = self.request.get('url')

        ad = Ad.get_by_key_name(url)

        if ad and ad.rating < 100:
            self.render_json({'agent': True})
        else:
            self.render_json({'agent': False})

    def post(self):
        self.get()

route("/api/check_url", GetByUrl)

#a3fb4a5c77348746e58b923b83713b8a -> 1gs.ru


class CheckUrls(AppHandler):
    def get(self):
        urls = self.request.get_all('u[]')
        host = self.request.get('host')

        response = []

        if host:
            urls = ["http://%s%s" % (host, url) for url in urls]

        keys = [db.Key.from_path('Ad', url) for url in urls]

        ads = db.get(keys)

        for idx, url in enumerate(urls):
            if ads[idx] and ads[idx].rating < 100:
                response.append({'agent': True, 'url':url})
            else:
                response.append({'agent': False, 'url':url})

        self.render_json(response)

route("/api/check_urls", CheckUrls)
