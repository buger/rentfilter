# encoding: utf-8

from handlers.base import *
from google.appengine.api import taskqueue
from dateutil.relativedelta import relativedelta
import logging
import urllib2
import adsparser

REGIONS = {
  'spb': {
      'avito': 'http://www.avito.ru/catalog/kvartiry-24/sankt-peterburg-653240/params.201_1060?user=1',
      'slando': 'http://nedvizhimost.slando.spb.ru/sankt-peterburg/1572_1.html',
      'slando_agent': 'http://nedvizhimost.slando.spb.ru/sankt-peterburg/1573_1.html',
      'olx': "http://saintpetersburg.olx.ru/cat-363",
      'irr': "http://saint-petersburg.irr.ru/real-estate/rent/search/offertype=сдам/sourcefrom=1/page1/"
  }
}

ACTIVE_REGIONS = ['spb']

MAX_PAGES = 100

class AdsList(AppHandler):
    def post(self):
        url = self.request.get('url')
        force_next_page = self.request.get('force_next_page')

        logging.info("Gettings ads list: %s" % url)

        try:
            page = int(self.request.get('page'))
        except:
            page = 1

        links = adsparser.ads_list(unicode(url).encode('utf-8'), page).parse()

        parse_next_page = True

        for link in links:
            if Ad.get_by_key_name(link) is None:
                taskqueue.add(queue_name = adsparser.parser_name(url), url="/ad", params = {'url': link, 'parent_url': url})
            else:
                if not force_next_page:
                    parse_next_page = False

        if parse_next_page and page < MAX_PAGES:
            taskqueue.add(url="/ads", params = {'url': url, 'page': page+1, 'force_next_page': force_next_page})

    def get(self):
        self.post()

route('/ads', AdsList)


class ProcessAd(AppHandler):
    def post(self):
        url = self.request.get('url')

        logging.info("Processing ad: %s" % url)

        try:
            parser = adsparser.parse(url)
        except urllib2.HTTPError:
            parser = None

        if parser:
            if parser.get_name() == 'emls':
                key_name = parser.phone or url

                if Ad.get_by_key_name(key_name):
                    return True
            else:
                key_name = url

            ad = Ad(key_name = key_name,
                    title = parser.title,
                    source = parser.get_name(),
                    md5 = parser.md5,
                    contact = parser.contact,
                    phone = parser.phone,
                    parent_url = self.request.get('parent_url'),
                    created_at = parser.date)

            if parser.agent:
                ad.rating = 0

            ad.put()

            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': url})

    def get(self):
        url = self.request.get('url')
        parser = adsparser.parse(url)

        self.response.out.write(parser)

route('/ad', ProcessAd)


class CheckAd(AppHandler):
    def post(self):
        def descrise_rating(ads, amount = 20):
            for a in ads:
                a.rating -= amount

                if a.rating < 0:
                    a.rating = 0

            return ads

        key = self.request.get('key')
        ad = Ad.get_by_key_name(key)

        if ad is None or ad.created_at is None:
            return True

        if Ad.all().filter("phone =", ad.phone).get().rating < 80:
            ad.rating = 0
            ad.put()

        if ad.rating == 0:
            ads = Ad.all().order('-created_at').filter("phone =", ad.phone).fetch(50)
            ads = descrise_rating(ads, 100)
        else:
            ads = Ad.all().order('-created_at').filter('created_at >', datetime.datetime.now()-relativedelta(months = 3)).filter("phone =", ad.phone).fetch(50)


        if len(ads) > 10:
            ad.rating = 0
            ad.put()

        if len(ads) > 4:
            ads = descrise_rating(ads)

        db.put(ads)

route('/ad/check', CheckAd)


class DeleteAD(AppHandler):
    def get(self, key):
        key = db.Key(key)
        db.delete(key)

        self.redirect("/")

route('/admin/ad/delete/:key', DeleteAD)

class MarkAD(AppHandler):
    def get(self, key):
        key = db.Key(key)
        ad = Ad.get(key)
        ad.rating = 0
        ad.put()

        taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.key().name()})

        self.redirect("/")


route('/admin/ad/mark/:key', MarkAD)

class ReCheckAds(AppHandler):
    def get(self):
        ads = Ad.all(keys_only = True).order("-created_at").filter("rating =", 100).fetch(500)

        for ad in ads:
            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.name()})

route('/cron/recheck_ads', ReCheckAds)


class DeleteAds(AppHandler):
    def get(self):
        ads = Ad.all(keys_only = True).order("-added_at").filter("added_at >", datetime.datetime.now()-datetime.timedelta(days=1)).fetch(2000)
        db.delete(ads)

route('/admin/delete_ads', DeleteAds)


class AdsCron(AppHandler):
    def get(self):
        for region in ACTIVE_REGIONS:
            for item in REGIONS[region].items():
                taskqueue.add(url="/ads", params = {'url': item[1], 'force_next_page': self.request.get('force_next_page')})

route('/cron/ads', AdsCron)


class ElmsParser(AppHandler):
    def get(self):
        urls = adsparser.EmlsMainParser("http://www.emls.ru/agencys/").parse()

        for url in urls:
            taskqueue.add(url="/ads", params = {'url': url})

route('/admin/elms_parser', ElmsParser)


import datetime

class AgentPhones(AppHandler):
    def post(self):
        phones = self.request.get('phones').rsplit(" ")

        for_put = []

        source = self.request.get('source') or 'form'

        for phone in phones:
            if phone.strip():
                for_put.append(Ad(key_name=phone, phone=phone, created_at = datetime.datetime.now(), source=source, rating=0))

        db.put(for_put)

        for phone in phones:
            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': phone})

        self.redirect("/")


route('/admin/agent_phones', AgentPhones)


class FillDates(AppHandler):
    def get(self):
        for_put = []

        ads = Ad.all().order('-created_at').filter("rating =", 100).fetch(300)

        for ad in ads:
            ad.added_at = ad.created_at
            for_put.append(ad)

        db.put(for_put)

route('/admin/fill_dates', FillDates)

