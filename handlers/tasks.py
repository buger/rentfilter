# encoding: utf-8

from handlers.base import *
from google.appengine.api import taskqueue
from dateutil.relativedelta import relativedelta
import logging
import urllib2
import datetime

import adsparser

REGIONS = {
  'spb': {
      #sdam
      'avito': 'http://www.avito.ru/catalog/kvartiry-24/sankt-peterburg-653240/params.201_1060?user=1',
      'slando': 'http://nedvizhimost.slando.spb.ru/sankt-peterburg/1572_1.html',
      'slando_agent': 'http://nedvizhimost.slando.spb.ru/sankt-peterburg/1573_1.html',
      'olx': "http://saintpetersburg.olx.ru/cat-363",
      'irr': "http://saint-petersburg.irr.ru/real-estate/rent/search/sourcefrom=1/page1/",
      'irr_2': "http://saint-petersburg.irr.ru/real-estate/rent/search/sourcefrom=0/currency=RUR/",
      '1gs': "http://spb.1gs.ru/arenda-kvartiry.1gs",
      'novoebenevo': "http://www.novoebenevo.ru/sdam/area_2",
      'egent': "http://spb.egent.ru/index.html?sd=1&sn=0&r1=0&r2=0&r3=0&r4=0&opt1=0&opt2=0&opt3=0&price_ot=&price_do=",
      'vkontakte': "http://vkontakte.ru/search?c[section]=ads&c[category]=30&c[city]=1&c[country]=1&c[q]=%D1%81%D0%B4%D0%B0%D0%BC%20%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B8%D1%80%D1%83&c[Bsection]=ads&c[type]=3&al=1",

      #snimu
      'slando_snimu': "http://nedvizhimost.slando.spb.ru/sankt-peterburg/194_T2_1.html",
      'avito_snimu': "http://www.avito.ru/catalog/kvartiry-24/sankt-peterburg-653240/params.201_1061?user=1"
  },

  'msk': {
      #sdam
      'slando': "http://nedvizhimost.slando.ru/moskva/1377_1.html",
      'slando_agent': "http://nedvizhimost.slando.ru/moskva/11_1.html",
      'avito': 'http://www.avito.ru/catalog/kvartiry-24/moskva-637640/params.201_1060?user=1',
      'olx': "http://moscow.olx.ru/cat-363",
      'irr_1': "http://irr.ru/real-estate/rent/search/sourcefrom=0/currency=RUR/",
      'irr_2': "http://irr.ru/real-estate/rent/search/sourcefrom=1/currency=RUR/",
      '1gs': "http://msk.1gs.ru/arenda-kvartiry.1gs",
      'novoebenevo': "http://www.novoebenevo.ru/sdam/area_3",
      'egent': "http://www.egent.ru/index.html?sd=1&sn=0&r1=0&r2=0&r3=0&r4=0&opt1=0&opt2=0&opt3=0&price_ot=&price_do=",
      'vkontakte': "http://vkontakte.ru/search?c[section]=ads&c[category]=30&c[city]=2&c[country]=1&c[q]=%D1%81%D0%B4%D0%B0%D0%BC%20%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B8%D1%80%D1%83&c[Bsection]=ads&c[type]=3&al=1",

      #snimu
      'slando_snimu': "http://nedvizhimost.slando.ru/moskva/1376_T2_1.html",
      'avito_snumu': "http://www.avito.ru/catalog/kvartiry-24/moskva-637640/params.201_1061?user=1"
  }
}

ACTIVE_REGIONS = ['msk', 'spb']

MAX_PAGES = 100

class SiteList(AppHandler):
    def get(self):
        for region in ACTIVE_REGIONS:
            self.response.out.write(region)
            self.response.out.write("<br/>")
            self.response.out.write("<br/>")

            for item in REGIONS[region].items():
                self.response.out.write("<a href='/site/test?url=%s'>%s</a>" % (item[1], item[0]))
                self.response.out.write("<br/>")

route('/site/list', SiteList)


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
                taskqueue.add(queue_name = adsparser.parser_name(url), url="/ad", params = {'url': link, 'parent_url': url, 'region': self.request.get('region')})
            else:
                if not force_next_page:
                    parse_next_page = False

        if parse_next_page and page < MAX_PAGES:
            taskqueue.add(url="/ads", params = {'url': url, 'page': page+1, 'force_next_page': force_next_page, 'region': self.request.get('region')})

    def get(self):
        self.post()

route('/ads', AdsList)


class ProcessAd(AppHandler):
    def post(self):
        url = self.request.get('url')

        logging.info("Processing ad: %s" % url)

        try:
            parser = adsparser.parse(url, self.request.get('region'))
        except urllib2.HTTPError:
            parser = None

        if parser:
            if parser.get_name() == 'emls':
                key_name = parser.phone or url

                if Ad.get_by_key_name(key_name):
                    return True
            else:
                key_name = url

            if parser.date:
                created_at = parser.date
                created_at = datetime.datetime.combine(parser.date.date(), datetime.datetime.now().time())
            else:
                created_at = datetime.datetime.now()

            ad = Ad(key_name = key_name,
                    title = parser.title,
                    source = parser.get_name(),
                    md5 = parser.md5,
                    contact = parser.contact,
                    phone = parser.phone,
                    price = parser.price,
                    parent_url = self.request.get('parent_url'),
                    created_at = created_at,
                    offer_type = parser.offer_type,
                    region = parser.region
                    )

            if parser.image:
                ad.image = parser.image
                ad.has_image = True

            if parser.address_id:
                ad.address_id = parser.address_id[0]

                if len(parser.address_id) > 1:
                    ad.needs_moderation = True
                    ad.moderation_type = 1

                ad.addresses = parser.address_id

            if parser.agent:
                ad.rating = 0

            if parser.phone is None:
                ad.moderation_type = 4

            ad.put()

            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': url})

    def get(self):
        url = self.request.get('url')
        parser = adsparser.parse(url, self.request.get('region'))

        self.response.out.write(parser)

route('/ad', ProcessAd)


class CheckAd(AppHandler):
    def post(self):
        def descrise_rating(ads, amount = 20):
            for a in ads:
                a.rating = 0

            return ads

        ad = Ad.get_by_key_name(self.request.get('key'))

        if ad is None:
            return True

        same_ads = Ad.all().filter("phone =", ad.phone).filter('region =', ad.region).fetch(10)
        same_ads = filter(lambda a: a.rating < 100, same_ads)

        if len(same_ads) > 0:
            ad.rating = 0
            ad.put()

        ads = Ad.all().filter("phone =", ad.phone).filter("region =", ad.region).fetch(50)

        if ad.rating == 0:
            ads = descrise_rating(ads, 100)

        if ad.offer_type == 1:
            ads_with_address = filter(lambda a: a.address_id is not None, ads)

            if ad.address_id and len(ads_with_address) > 1:
                if len(filter(lambda a: a.address_id != ad.address_id, ads)) > 0:
                    ads = descrise_rating(ads, 100)
                    ad.rating = 0
                    ad.moderation_type = 2
                    ad.put()

        connected_ads = []

        parent = ad.parent()

        if parent and parent.rating < 100:
            ad.rating = 0
            ad.put()

        if ad.rating < 100:
            if parent:
                parent.rating = 0
                parent.put()

            children = Ad.all().ancestor(ad).fetch(50)

            if len(children) > 1:
                for child in children:
                    if ad.key() == child.key():
                        continue

                    child.rating = 0
                    connected_ads.append(child)


        db.put(connected_ads)
        db.put(ads)

        for ad in connected_ads:
            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.key().name() })

    def get(self):
        self.post()

route('/ad/check', CheckAd)


class DeleteAD(AppHandler):
    def get(self, key):
        ad = Ad.get(db.Key(key))
        ad.deleted = True
        ad.put()

        memcache.delete("main_page_%s" % ad.region)

        self.redirect("/")

route('/admin/ad/delete/:key', DeleteAD)

class UnMarkAD(AppHandler):
    def get(self, phone):
        ads = Ad.all().filter("phone =", phone)
        ads = ads.fetch(1000)

        for ad in ads:
            ad.rating = 100

        db.put(ads)

        memcache.delete("main_page_%s" % ads[0].region)

        self.redirect("/")

route('/admin/ad/unmark/:phone', UnMarkAD)

class MarkAD(AppHandler):
    def get(self, key):
        key = db.Key(key)
        ad = Ad.get(key)
        ad.rating = 0
        ad.put()

        taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.key().name()})

        memcache.delete("main_page_%s" % ad.region)

        self.redirect("/")

route('/admin/ad/mark/:key', MarkAD)


class ReprocessAD(AppHandler):
    def get(self, key):
        key = db.Key(key)
        ad = Ad.get(key)

        taskqueue.add(queue_name = ad.source, url = '/ad', params = {'url': ad.key().name(), 'region': ad.region, 'parent_url': ad.parent_url})

        memcache.delete("main_page_%s" % ad.region)

        self.redirect("/")

route('/admin/ad/reprocess/:key', ReprocessAD)

class RecheckAD(AppHandler):
    def get(self, key):
        key = db.Key(key)
        ad = Ad.get(key)

        taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.key().name()})

        memcache.delete("main_page_%s" % ad.region)

        self.redirect("/")

route('/admin/ad/recheck/:key', RecheckAD)


class SendAbuseAD(AppHandler):
    def get(self, key):
        key = db.Key(key)
        ad = Ad.get(key)

        count = Ad.all().filter("phone =", ad.phone).count()

        url = ad.key().name()

        if ad.source == 'slando':
            posting_id = re.search("(\d+).html", url).group(1)

            import urllib
            from google.appengine.api import urlfetch

            form_fields = {
              "posting_id": posting_id,
              "reason": "REPORT_TO_MODERATOR_AGENCY",
              "comment": u"Найдено %d похожих объявлений отмеченных как агентские: http://www.rentfilter.ru?phone=%s\n\nRentFilter.ru hello@rentfilter.ru" % (count, ad.phone)
            }

            form_fields['comment'] = form_fields['comment'].encode('utf-8', 'ignore')

            form_data = urllib.urlencode(form_fields)

            url = u"http://nedvizhimost.slando.spb.ru/sankt-peterburg/content/report.html?nrk=%s&posting_id=%s" % ("RU-LEN-sankt-peterburg", posting_id)

            result = urlfetch.fetch(url=url,
                                    payload=form_data,
                                    method=urlfetch.POST,
                                    headers={'Content-Type': 'application/x-www-form-urlencoded'})

        self.redirect("/")

route('/admin/ad/abuse/:key', SendAbuseAD)


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
                taskqueue.add(url="/ads", params = {'url': item[1], 'force_next_page': self.request.get('force_next_page'), 'region':region})

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
        region = self.request.get('region')

        for phone in phones:
            if phone.strip():
                phone = adsparser.format_phone(phone)

                try:
                    for_put.append(Ad(key_name=phone, phone=phone, created_at = datetime.datetime.now(), source=source, rating=0, region=region))
                except:
                    continue

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


from dateutil.relativedelta import relativedelta

class FixAvito(AppHandler):
    def get(self):
        ads = Ad.all().order("-added_at").filter("source =", 'avito').fetch(2000)
        for ad in ads:
            ad.created_at = ad.created_at + relativedelta(days=2)

        db.put(ads)

route('/admin/fix_avito', FixAvito)


class FixVkontakte(AppHandler):
    def get(self):
        ads = Ad.all(keys_only = True).order("-added_at").filter("source =", 'vkontakte').fetch(4000)
        for ad in ads:
            taskqueue.add(queue_name = 'quick', url = '/ad/check', params = {'key': ad.name()})

        self.redirect("/")

route('/admin/fix_vkontakte', FixVkontakte)



class FixOneGSDates(AppHandler):
    def get(self):
        ads = Ad.all(keys_only = True).filter('source =', '1gs')

        for ad in ads:
            taskqueue.add(queue_name = '1gs', url = '/ad', params = {'url': ad.name()})

route('/admin/fix_1gs_dates', FixOneGSDates)


class FixMetroModeration(AppHandler):
    def get(self):
        ads = Ad.all().filter('moderation_type =', 1)
        ads = ads.fetch(500)

        for ad in ads:
            ad.address_id = ad.address_id.split('@')[0]
            ad.moderation_type = 0

        db.put(ads)

route('/admin/fix_metro_moderation', FixMetroModeration)


class FixOneGsParentUrls(AppHandler):
    def get(self):
        ads = Ad.all().filter('source =', '1gs')

        if self.request.get('cursor'):
            ads = ads.with_cursor(self.request.get('cursor'))

        for_put = []

        for ad in ads.fetch(100):
            ad.parent_url = 'http://spb.1gs.ru/arenda-kvartiry.1gs'
            for_put.append(ad)

        db.put(for_put)

        if len(for_put) == 100:
            taskqueue.add(queue_name = 'quick', url = '/admin/fix_1gs_parent_urls', params = {'cursor': ads.cursor()})

    def post(self):
        self.get()

route('/admin/fix_1gs_parent_urls', FixOneGsParentUrls)



